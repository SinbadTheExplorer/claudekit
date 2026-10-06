import io
import os
import shutil
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime, timezone

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fetch_bullion_news import (
    parse_rss_items,
    filter_recent,
    filter_listicles,
    tag_sentiment,
    classify_category,
    image_filename_for_url,
    resize_thumbnail_bytes,
    sync_news_images,
    prune_dangling_images,
    build_news_envelope,
    _fetch_image_bytes,
    CATEGORY_LABELS,
)


def _tiny_image_bytes(size=(10, 10), mode="RGB", color=(200, 30, 30), fmt="PNG"):
    """A minimal real, decodable image for tests that exercise the actual
    download -> decode -> resize -> re-encode pipeline -- fixtures for this
    code can't just be arbitrary placeholder bytes like b"fake-jpeg-bytes"
    now that sync_news_images() genuinely decodes what it downloads.
    """
    im = Image.new(mode, size, color)
    out = io.BytesIO()
    im.save(out, format=fmt)
    return out.getvalue()

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>Yahoo Finance</title>
<item>
<title>Stocks rally as Fed signals rate cut</title>
<link>https://finance.yahoo.com/news/stocks-rally-1.html</link>
<pubDate>2026-09-01T16:50:13Z</pubDate>
</item>
<item>
<title>Dow, S&amp;P 500, Nasdaq drop as bond yields weigh on stocks</title>
<link>https://finance.yahoo.com/news/stocks-drop-2.html</link>
<pubDate>2026-09-01T08:06:17Z</pubDate>
</item>
<item>
<title>Best Wells Fargo credit cards (2026)</title>
<link>https://finance.yahoo.com/news/best-cards.html</link>
<pubDate>2026-06-01T16:43:10Z</pubDate>
</item>
</channel></rss>
"""

# Real RSS 2.0 spec mandates RFC822 pubDates; Yahoo's actual feed uses ISO
# 8601 instead (confirmed against the live feed 2026-09-01). Support both
# rather than assume the spec-compliant format is what ships in practice.
RFC822_ITEM_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<item>
<title>Gold gains as dollar weakens</title>
<link>https://example.com/gold-gains.html</link>
<pubDate>Tue, 01 Sep 2026 16:50:13 +0000</pubDate>
</item>
</channel></rss>
"""


RSS_WITH_MEDIA = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:media="http://search.yahoo.com/mrss/" version="2.0"><channel>
<item>
<title>Diesel prices hit an all-time high</title>
<link>https://finance.yahoo.com/news/diesel-1.html</link>
<pubDate>2026-09-04T16:01:35Z</pubDate>
<media:content height="86" url="https://media.zenfs.com/en/24_7_wall_st__718/2353c1676228b59ba3205fd31ecddd52.jpg" width="130"/>
<media:credit role="publishing company"/>
</item>
<item>
<title>No thumbnail on this one</title>
<link>https://finance.yahoo.com/news/no-thumb.html</link>
<pubDate>2026-09-04T16:02:00Z</pubDate>
</item>
</channel></rss>
"""


class TestParseRssItems(unittest.TestCase):
    def test_extracts_title_link_and_pubdate(self):
        items = parse_rss_items(SAMPLE_RSS)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["title"], "Stocks rally as Fed signals rate cut")
        self.assertEqual(items[0]["link"], "https://finance.yahoo.com/news/stocks-rally-1.html")
        self.assertEqual(items[0]["published"],
                          datetime(2026, 9, 1, 16, 50, 13, tzinfo=timezone.utc))

    def test_unescapes_html_entities_in_title(self):
        items = parse_rss_items(SAMPLE_RSS)
        self.assertEqual(items[1]["title"],
                          "Dow, S&P 500, Nasdaq drop as bond yields weigh on stocks")

    def test_drops_items_whose_link_is_not_http(self):
        rss = "<rss><channel>" + "".join(
            f"<item><title>T{n}</title><link>{link}</link>"
            f"<pubDate>2026-09-01T16:50:13Z</pubDate></item>"
            for n, link in enumerate([
                "javascript:alert(1)",
                " JavaScript:alert(1)",
                "data:text/html,<script>alert(1)</script>",
                "//evil.example/x",
                "HTTPS://www.cnbc.com/ok.html",
            ])
        ) + "</channel></rss>"
        items = parse_rss_items(rss)
        self.assertEqual([i["link"] for i in items], ["HTTPS://www.cnbc.com/ok.html"])

    def test_image_fetch_refuses_non_http_schemes(self):
        for url in ("file:///etc/passwd", "ftp://example.com/a.jpg", "data:image/png;base64,AA"):
            with self.assertRaises(urllib.error.URLError):
                _fetch_image_bytes(url, timeout=1)

    def test_no_items_returns_empty_list(self):
        self.assertEqual(parse_rss_items("<rss><channel></channel></rss>"), [])

    def test_parses_rfc822_pubdate_too(self):
        # RSS 2.0's own spec format — a different feed than Yahoo's might use it.
        items = parse_rss_items(RFC822_ITEM_RSS)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["published"],
                          datetime(2026, 9, 1, 16, 50, 13, tzinfo=timezone.utc))

    def test_extracts_media_content_image_url(self):
        items = parse_rss_items(RSS_WITH_MEDIA)
        self.assertEqual(
            items[0]["image_url"],
            "https://media.zenfs.com/en/24_7_wall_st__718/2353c1676228b59ba3205fd31ecddd52.jpg",
        )

    def test_image_url_is_none_when_no_media_content_tag(self):
        items = parse_rss_items(RSS_WITH_MEDIA)
        self.assertIsNone(items[1]["image_url"])

    def test_image_url_is_none_for_feeds_with_no_media_namespace_at_all(self):
        # SAMPLE_RSS (existing fixture) has no media:content anywhere.
        items = parse_rss_items(SAMPLE_RSS)
        self.assertTrue(all(i["image_url"] is None for i in items))


class TestFilterRecent(unittest.TestCase):
    NOW = datetime(2026, 9, 1, 18, 0, 0, tzinfo=timezone.utc)

    def test_keeps_items_published_within_window(self):
        items = parse_rss_items(SAMPLE_RSS)
        recent = filter_recent(items, self.NOW, max_age_hours=48)
        titles = {i["title"] for i in recent}
        self.assertIn("Stocks rally as Fed signals rate cut", titles)

    def test_drops_stale_evergreen_items(self):
        # The credit-card listicle is months old — this is the exact noise
        # the real Yahoo Finance feed mixes into its "latest" items.
        items = parse_rss_items(SAMPLE_RSS)
        recent = filter_recent(items, self.NOW, max_age_hours=48)
        titles = {i["title"] for i in recent}
        self.assertNotIn("Best Wells Fargo credit cards (2026)", titles)

    def test_empty_input_returns_empty_list(self):
        self.assertEqual(filter_recent([], self.NOW, max_age_hours=48), [])


class TestFilterListicles(unittest.TestCase):
    def test_drops_leading_digit_listicle_titles(self):
        items = [{"title": "5 Easy Side Gigs to Quickly Eliminate Credit Card Debt"}]
        self.assertEqual(filter_listicles(items), [])

    def test_keeps_titles_that_merely_start_with_a_numbered_fact(self):
        # "161-year-old ..." starts with digits but isn't a numbered listicle
        # (no space right after the digits) -- must not be filtered.
        items = [{"title": "161-year-old kids clothing giant closes 29 more stores"}]
        self.assertEqual(filter_listicles(items), items)

    def test_keeps_normal_market_headlines(self):
        items = [{"title": "Stocks rally as Fed signals rate cut"}]
        self.assertEqual(filter_listicles(items), items)


class TestTagSentiment(unittest.TestCase):
    def test_bullish_keyword_tags_bullish(self):
        self.assertEqual(tag_sentiment("Stocks rally as Fed signals rate cut"), "bullish")

    def test_bearish_keyword_tags_bearish(self):
        self.assertEqual(tag_sentiment("Dow drops as recession fears mount"), "bearish")

    def test_no_keyword_tags_neutral(self):
        self.assertEqual(tag_sentiment("FDA approval marks a turning point for BeOne"), "neutral")

    def test_mixed_keywords_tags_neutral(self):
        # One bullish, one bearish signal in the same headline — no clear lean.
        self.assertEqual(tag_sentiment("Stocks rally even as recession fears mount"), "neutral")

    def test_case_insensitive(self):
        self.assertEqual(tag_sentiment("SELLOFF hits tech stocks"), "bearish")


class TestClassifyCategory(unittest.TestCase):
    def test_federal_policy_keyword(self):
        self.assertEqual(classify_category("Fed signals rate cut as inflation cools"), "federal")

    def test_technology_keyword(self):
        self.assertEqual(classify_category("Nvidia chip demand fuels AI data center boom"), "tech")

    def test_healthcare_keyword(self):
        self.assertEqual(classify_category("FDA approval marks a turning point for BeOne"), "healthcare")

    def test_energy_keyword(self):
        self.assertEqual(classify_category("Oil prices rise as OPEC weighs supply cuts"), "energy")

    def test_financials_keyword(self):
        self.assertEqual(classify_category("Goldman Sachs hedge fund unit sees record inflows"), "financials")

    def test_consumer_retail_keyword(self):
        self.assertEqual(classify_category("Walmart retailer sales beat as holiday shopping starts early"), "consumer")

    def test_industrials_keyword(self):
        self.assertEqual(classify_category("Boeing factory output ramps up amid supply chain fixes"), "industrials")

    def test_real_estate_keyword(self):
        self.assertEqual(classify_category("Mortgage rates fall as home sales pick up"), "realestate")

    def test_crypto_keyword(self):
        self.assertEqual(classify_category("Bitcoin and ethereum rally as crypto ETF inflows surge"), "crypto")

    def test_international_keyword(self):
        self.assertEqual(classify_category("China sanctions escalate trade war with Europe"), "international")

    def test_no_keyword_match_falls_back_to_other(self):
        self.assertEqual(classify_category("Is Linde Stock Underperforming the Dow?"), "other")

    def test_case_insensitive(self):
        self.assertEqual(classify_category("BITCOIN SURGES past new record high"), "crypto")

    def test_every_label_key_has_a_keyword_list_or_is_the_fallback(self):
        # Every category the classifier can return must resolve to a display
        # label; "other" is the one deliberate exception with no keyword list.
        from fetch_bullion_news import CATEGORY_KEYWORDS
        self.assertEqual(set(CATEGORY_KEYWORDS) | {"other"}, set(CATEGORY_LABELS))


class TestImageFilenameForUrl(unittest.TestCase):
    def test_same_url_always_produces_the_same_filename(self):
        url = "https://media.zenfs.com/en/reuters.com/89fed01bb8c2422ea700c6db81a37382.jpg"
        self.assertEqual(image_filename_for_url(url), image_filename_for_url(url))

    def test_different_urls_produce_different_filenames(self):
        a = image_filename_for_url("https://media.zenfs.com/en/a.jpg")
        b = image_filename_for_url("https://media.zenfs.com/en/b.jpg")
        self.assertNotEqual(a, b)

    def test_always_ends_in_jpg_regardless_of_source_extension(self):
        # Every cached file is re-encoded as JPEG by resize_thumbnail_bytes()
        # regardless of the source format, so the filename never reflects
        # the source URL's own extension -- .png, .jpeg, no-extension-at-all
        # sources all still cache as .jpg.
        for url in (
            "https://media.zenfs.com/en/24_7_wall_st__718/2353c1676228b59ba3205fd31ecddd52.jpg",
            "https://example.com/thumb.png",
            "https://example.com/thumb.jpeg",
            "https://s.yimg.com/uu/api/res/1.2/abc~B/no-extension-here",
        ):
            self.assertTrue(image_filename_for_url(url).endswith(".jpg"))

    def test_filename_has_no_path_separators_or_query_junk(self):
        url = "https://media.zenfs.com/en/reuters.com/89fed01bb8c2422ea700c6db81a37382.jpg?foo=bar"
        name = image_filename_for_url(url)
        self.assertNotIn("/", name)
        self.assertNotIn("?", name)


class TestSyncNewsImages(unittest.TestCase):
    def _tmp_images_dir(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        return d

    def test_downloads_and_sets_relative_image_path(self):
        images_dir = self._tmp_images_dir()
        calls = []

        def fake_fetch(url, timeout):
            calls.append(url)
            return _tiny_image_bytes()

        items = [{"title": "t", "link": "l", "image_url": "https://example.com/a.jpg"}]
        sync_news_images(items, images_dir, fetch=fake_fetch)

        self.assertEqual(calls, ["https://example.com/a.jpg"])
        expected_name = image_filename_for_url("https://example.com/a.jpg")
        self.assertEqual(items[0]["image"], f"news-images/{expected_name}")
        # The cached file is the resized/re-encoded output, not the raw
        # downloaded bytes verbatim -- confirm it's a valid, small JPEG.
        with Image.open(os.path.join(images_dir, expected_name)) as cached:
            self.assertEqual(cached.format, "JPEG")
            self.assertEqual(cached.size, (10, 10))

    def test_does_not_redownload_an_already_cached_image(self):
        images_dir = self._tmp_images_dir()
        url = "https://example.com/b.jpg"
        name = image_filename_for_url(url)
        with open(os.path.join(images_dir, name), "wb") as f:
            f.write(b"already-here")

        def fake_fetch(url, timeout):
            raise AssertionError("should not re-download a cached image")

        items = [{"title": "t", "link": "l", "image_url": url}]
        sync_news_images(items, images_dir, fetch=fake_fetch)

        self.assertEqual(items[0]["image"], f"news-images/{name}")
        with open(os.path.join(images_dir, name), "rb") as f:
            self.assertEqual(f.read(), b"already-here")

    def test_item_with_no_image_url_gets_none(self):
        images_dir = self._tmp_images_dir()
        items = [{"title": "t", "link": "l", "image_url": None}]
        sync_news_images(items, images_dir, fetch=lambda u, t: b"x")
        self.assertIsNone(items[0]["image"])

    def test_a_failed_download_sets_none_and_does_not_block_other_items(self):
        images_dir = self._tmp_images_dir()

        def flaky_fetch(url, timeout):
            if "bad" in url:
                raise urllib.error.URLError("boom")
            return _tiny_image_bytes()

        items = [
            {"title": "fails", "link": "l1", "image_url": "https://example.com/bad.jpg"},
            {"title": "works", "link": "l2", "image_url": "https://example.com/good.jpg"},
        ]
        sync_news_images(items, images_dir, fetch=flaky_fetch)

        self.assertIsNone(items[0]["image"])
        self.assertIsNotNone(items[1]["image"])

    def test_undecodable_bytes_sets_none_and_does_not_block_other_items(self):
        # A URL that "succeeds" at the HTTP level but doesn't return a real
        # image (an HTML error page, a truncated download, etc.) must not
        # crash the run -- confirmed via Pillow's own decode failure, not a
        # hand-picked exception type (see the broad except in sync_news_images).
        images_dir = self._tmp_images_dir()

        def fetch(url, timeout):
            if "notanimage" in url:
                return b"<html>this is not an image</html>"
            return _tiny_image_bytes()

        items = [
            {"title": "bad", "link": "l1", "image_url": "https://example.com/notanimage.jpg"},
            {"title": "good", "link": "l2", "image_url": "https://example.com/real.jpg"},
        ]
        sync_news_images(items, images_dir, fetch=fetch)

        self.assertIsNone(items[0]["image"])
        self.assertIsNotNone(items[1]["image"])

    def test_oversized_source_image_is_downsized_to_max_dimension(self):
        # Reproduces the real bug this feature was built to fix: Yahoo's
        # RSS media:content width/height attributes (130x86) describe the
        # embed display size, not the actual served file -- real files can
        # be several thousand pixels per side. A cached file must never
        # exceed IMAGE_MAX_DIMENSION on its longer side.
        images_dir = self._tmp_images_dir()
        oversized = _tiny_image_bytes(size=(4000, 3000))

        items = [{"title": "t", "link": "l", "image_url": "https://example.com/huge.jpg"}]
        sync_news_images(items, images_dir, fetch=lambda u, t: oversized)

        name = image_filename_for_url("https://example.com/huge.jpg")
        with Image.open(os.path.join(images_dir, name)) as cached:
            self.assertLessEqual(max(cached.size), 200)

    def test_creates_images_dir_if_missing(self):
        parent = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, parent, ignore_errors=True)
        images_dir = os.path.join(parent, "does", "not", "exist", "yet")
        items = [{"title": "t", "link": "l", "image_url": "https://example.com/c.jpg"}]
        sync_news_images(items, images_dir, fetch=lambda u, t: b"x")
        self.assertTrue(os.path.isdir(images_dir))


class TestResizeThumbnailBytes(unittest.TestCase):
    def test_downsizes_when_larger_than_max_dimension(self):
        data = _tiny_image_bytes(size=(4000, 2000))
        out = resize_thumbnail_bytes(data, max_dimension=200)
        with Image.open(io.BytesIO(out)) as im:
            self.assertEqual(im.format, "JPEG")
            self.assertEqual(im.size, (200, 100))  # aspect ratio preserved

    def test_does_not_upscale_smaller_images(self):
        data = _tiny_image_bytes(size=(10, 10))
        out = resize_thumbnail_bytes(data, max_dimension=200)
        with Image.open(io.BytesIO(out)) as im:
            self.assertEqual(im.size, (10, 10))

    def test_always_outputs_jpeg_even_from_a_png_source(self):
        data = _tiny_image_bytes(fmt="PNG")
        out = resize_thumbnail_bytes(data)
        with Image.open(io.BytesIO(out)) as im:
            self.assertEqual(im.format, "JPEG")

    def test_flattens_transparency_onto_white_instead_of_black(self):
        rgba = Image.new("RGBA", (10, 10), (0, 0, 0, 0))  # fully transparent
        buf = io.BytesIO()
        rgba.save(buf, format="PNG")
        out = resize_thumbnail_bytes(buf.getvalue())
        with Image.open(io.BytesIO(out)) as im:
            self.assertEqual(im.convert("RGB").getpixel((5, 5)), (255, 255, 255))

    def test_undecodable_bytes_raises_instead_of_returning_garbage(self):
        with self.assertRaises(Exception):
            resize_thumbnail_bytes(b"not an image at all")

    def test_extreme_aspect_ratio_clamps_to_1px_instead_of_raising(self):
        # A naive int(w*scale)/int(h*scale) can round the short side down
        # to 0, which Image.resize() rejects with a ValueError -- this
        # must clamp to 1px and still produce a valid thumbnail instead of
        # silently dropping an otherwise-valid image.
        data = _tiny_image_bytes(size=(5000, 1))
        out = resize_thumbnail_bytes(data, max_dimension=200)
        with Image.open(io.BytesIO(out)) as im:
            self.assertEqual(im.format, "JPEG")
            self.assertEqual(im.size, (200, 1))


class TestPruneDanglingImages(unittest.TestCase):
    def _tmp_images_dir(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        return d

    def test_deletes_unreferenced_files_keeps_referenced_ones(self):
        images_dir = self._tmp_images_dir()
        for name in ("keep.jpg", "drop.jpg"):
            with open(os.path.join(images_dir, name), "wb") as f:
                f.write(b"x")

        deleted = prune_dangling_images(images_dir, {"keep.jpg"})

        self.assertEqual(deleted, ["drop.jpg"])
        self.assertTrue(os.path.exists(os.path.join(images_dir, "keep.jpg")))
        self.assertFalse(os.path.exists(os.path.join(images_dir, "drop.jpg")))

    def test_missing_directory_returns_empty_list(self):
        self.assertEqual(prune_dangling_images("/no/such/dir", {"a.jpg"}), [])

    def test_empty_referenced_set_deletes_everything(self):
        images_dir = self._tmp_images_dir()
        with open(os.path.join(images_dir, "orphan.jpg"), "wb") as f:
            f.write(b"x")
        deleted = prune_dangling_images(images_dir, set())
        self.assertEqual(deleted, ["orphan.jpg"])


class TestBuildNewsEnvelope(unittest.TestCase):
    def test_envelope_shape(self):
        items = [{
            "title": "Stocks rally as Fed signals rate cut",
            "link": "https://finance.yahoo.com/news/stocks-rally-1.html",
            "published": datetime(2026, 9, 1, 16, 50, 13, tzinfo=timezone.utc),
        }]
        env = build_news_envelope(items, "2026-09-01T18:00:00Z")
        self.assertEqual(env["generated_at"], "2026-09-01T18:00:00Z")
        self.assertEqual(len(env["headlines"]), 1)
        h = env["headlines"][0]
        self.assertEqual(h["headline"], "Stocks rally as Fed signals rate cut")
        self.assertEqual(h["link"], "https://finance.yahoo.com/news/stocks-rally-1.html")
        self.assertEqual(h["published"], "2026-09-01T16:50:13Z")
        self.assertEqual(h["sentiment"], "bullish")
        self.assertEqual(h["category"], "federal")

    def test_envelope_includes_image_when_present(self):
        items = [{
            "title": "Stocks rally as Fed signals rate cut",
            "link": "https://finance.yahoo.com/news/stocks-rally-1.html",
            "published": datetime(2026, 9, 1, 16, 50, 13, tzinfo=timezone.utc),
            "image": "news-images/abc123.jpg",
        }]
        env = build_news_envelope(items, "2026-09-01T18:00:00Z")
        self.assertEqual(env["headlines"][0]["image"], "news-images/abc123.jpg")

    def test_envelope_image_is_none_when_absent(self):
        items = [{
            "title": "Stocks rally as Fed signals rate cut",
            "link": "https://finance.yahoo.com/news/stocks-rally-1.html",
            "published": datetime(2026, 9, 1, 16, 50, 13, tzinfo=timezone.utc),
        }]
        env = build_news_envelope(items, "2026-09-01T18:00:00Z")
        self.assertIsNone(env["headlines"][0]["image"])


class TestPathsAreFileRelative(unittest.TestCase):
    """Regression test for a real bug: NEWS_OUT_PATH used to be the bare
    string "news.json", which resolves relative to the *caller's* CWD. In
    GitHub Actions that CWD is the repo root, not bullion-live-map/, so the
    daily workflow was silently writing to the wrong location for 3+ days
    (confirmed via git log showing zero daily-bot commits to news.json
    while data.json, whose script resolves paths the correct way, updated
    every day). Both path constants must be anchored to the script's own
    file location, not whatever process invokes it.
    """
    def test_news_out_path_resolves_next_to_the_script_not_cwd(self):
        import fetch_bullion_news as mod
        expected_dir = os.path.dirname(os.path.abspath(mod.__file__))
        self.assertEqual(os.path.dirname(mod.NEWS_OUT_PATH), expected_dir)

    def test_images_dir_resolves_next_to_the_script_not_cwd(self):
        import fetch_bullion_news as mod
        expected_dir = os.path.dirname(os.path.abspath(mod.__file__))
        self.assertEqual(os.path.dirname(mod.IMAGES_DIR), expected_dir)


if __name__ == "__main__":
    unittest.main()

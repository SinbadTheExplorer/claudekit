#!/usr/bin/env python3
"""Daily news-headline fetch for the Bullion news bar.

Pulls Yahoo Finance's general RSS feed (free, no key) and writes news.json:
a list of recent headlines, each tagged with a sentiment and a topic
category, rendered by the Markets tab as a categorized list (not a
scrolling ticker). Deliberately does NOT call any LLM/paid API — both
sentiment and category are local keyword scans, same spirit as the map's
existing runLocalAnalysis JS fallback, just done once here in Python so
there is one wordlist per signal, not copies that can drift apart.

The raw feed mixes today's real market news with evergreen listicles
("best credit cards of 2026") that carry stale pubDates — filter_recent()
is what separates them; it is not optional polish.
"""
import hashlib
import html
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from PIL import Image
from email.utils import parsedate_to_datetime

NEWS_RSS_URL = "https://finance.yahoo.com/news/rssindex"
# Anchored to the script's own directory, not the caller's CWD -- GitHub
# Actions `run:` steps default CWD to the repo root, so a bare relative
# path here silently wrote to the wrong location for 3+ days (see the
# plan doc this fix came from). fetch_bullion_data.py already gets this
# right; mirror its OUT_DIR pattern instead of inventing a new one.
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_OUT_PATH = os.path.join(OUT_DIR, "news.json")
IMAGES_DIR_NAME = "news-images"
IMAGES_DIR = os.path.join(OUT_DIR, IMAGES_DIR_NAME)
MAX_AGE_HOURS = 48
# Raised from 20 (the old scrolling-ticker cap) now that headlines render as
# a categorized list, not a single marquee row -- more items means fuller
# category sections instead of most sections showing 0-1 headlines.
MAX_HEADLINES = 40

# A deliberately small, literal keyword scan -- not NLP, not weighted, just
# enough to separate "clearly up" from "clearly down" headlines. Ties (or no
# match) fall back to neutral rather than guessing.
BULLISH_WORDS = [
    "rally", "rallies", "surge", "surges", "soar", "soars", "jump", "jumps",
    "rate cut", "gains", "gain", "record high", "upgrade", "upgrades",
    "beat", "beats", "breakout", "rebound", "rebounds",
]
BEARISH_WORDS = [
    "recession", "selloff", "sell-off", "plunge", "plunges", "slump",
    "slumps", "downgrade", "downgrades", "miss", "misses", "crash",
    "crashes", "tumble", "tumbles", "drop", "drops", "falls", "fall",
    "weigh", "weighs",
]

# Category taxonomy for the news list, agreed with the user during the
# redesign brainstorm: 10 topic buckets + a catch-all "other". Same spirit
# as BULLISH_WORDS/BEARISH_WORDS above -- a literal keyword scan, not NLP;
# no LLM call, per the original cost constraint. Order matters only as a
# tie-break (first category reaching the highest keyword-hit count wins);
# a headline that hits nothing lands in "other" rather than being guessed.
CATEGORY_LABELS = {
    "federal": "Federal Reserve & Policy",
    "tech": "Technology",
    "healthcare": "Healthcare",
    "energy": "Energy",
    "financials": "Financials & Banking",
    "consumer": "Consumer & Retail",
    "industrials": "Industrials",
    "realestate": "Real Estate",
    "crypto": "Crypto",
    "international": "International & Geopolitics",
    "other": "Other",
}
CATEGORY_KEYWORDS = {
    "federal": [
        "federal reserve", "fomc", "interest rate", "rate cut", "rate hike",
        "treasury", "inflation", "cpi", "jobs report", "unemployment",
        "gdp", "powell", "central bank", "fiscal", "congress",
        "white house", "tariff", "trade war", "government shutdown",
        "debt ceiling", "social security",
    ],
    "tech": [
        "tech ", "technology", "apple", "microsoft", "google", "alphabet",
        "meta", "nvidia", " ai ", "ai-driven", "artificial intelligence",
        "chip", "semiconductor", "software", "app store",
        "cloud computing", "iphone", "silicon valley", "data center",
        "cyber",
    ],
    "healthcare": [
        "health", "fda", "drug", "pharma", "biotech", "vaccine",
        "hospital", "insurer", "medicare", "medicaid", "clinical trial",
    ],
    "energy": [
        "oil", "gas prices", "crude", "opec", "energy", "solar",
        "wind power", "pipeline", "natural gas", "refinery", "refin",
        "barrel", "lithium", "battery", "mining",
    ],
    "financials": [
        "bank", "banking", "bancorp", "wall street", "hedge fund",
        "private equity", "jpmorgan", "goldman sachs", "morgan stanley",
        "wells fargo", "citigroup", "lender", "loan", "credit union",
        "insurance company", "visa", "mastercard", "payments",
    ],
    "consumer": [
        "retail", "retailer", "store", "consumer spending", "walmart",
        "target", "amazon", "e-commerce", "holiday shopping", "restaurant",
        "airline", "travel", "hotel", "clothing",
    ],
    "industrials": [
        "manufacturing", "factory", "industrial", "boeing", "aerospace",
        "shipping", "logistics", "supply chain", "steel", "automaker",
        "auto industry", "tesla",
    ],
    "realestate": [
        "housing", "home sales", "mortgage", "real estate", "homebuilder",
        "rent", "commercial property", "reit",
    ],
    "crypto": [
        "bitcoin", "crypto", "ethereum", "blockchain", "coinbase",
        "stablecoin", "nft",
    ],
    "international": [
        "china", "europe", "eu ", "japan", "russia", "ukraine",
        "geopolitic", "sanctions", "trade deal", "global market",
        "emerging market", "world bank", "imf", "iran", "middle east",
        "war ",
    ],
}


def _parse_pub_date(raw):
    """Yahoo's real feed ships ISO 8601 (`2026-08-31T15:33:00Z`), not the
    RFC822 the RSS 2.0 spec mandates (confirmed against the live feed
    2026-09-01) -- try both rather than assume the spec-compliant format.
    """
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        try:
            dt = parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_rss_items(xml_text):
    """Extract title/link/pubDate from an RSS 2.0 <item> list.

    Regex, not an XML parser -- this project already parses SDMX/JSON via
    stdlib only elsewhere; Yahoo's feed is small and consistently shaped, so
    a targeted regex avoids pulling in a new dependency for one feed.
    """
    items = []
    for block in re.findall(r"<item>(.*?)</item>", xml_text, re.S):
        title_m = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", block, re.S)
        link_m = re.search(r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", block, re.S)
        pub_m = re.search(r"<pubDate>(.*?)</pubDate>", block, re.S)
        if not (title_m and link_m and pub_m):
            continue
        published = _parse_pub_date(pub_m.group(1).strip())
        if published is None:
            continue
        image_m = re.search(r'<media:content[^>]*\burl="([^"]*)"', block)
        items.append({
            "title": html.unescape(title_m.group(1).strip()),
            "link": link_m.group(1).strip(),
            "published": published,
            "image_url": image_m.group(1).strip() if image_m else None,
        })
    return items


def filter_recent(items, now, max_age_hours=MAX_AGE_HOURS):
    cutoff = now - timedelta(hours=max_age_hours)
    return [i for i in items if i["published"] >= cutoff]


_LISTICLE_TITLE = re.compile(r"^\d+\s")


def filter_listicles(items):
    """Drop generic personal-finance listicles ("5 Easy Side Gigs...").

    The 48h recency filter doesn't catch these -- they're freshly published,
    just not market news. They're also the dominant noise in Yahoo's general
    feed (confirmed against the live feed 2026-09-01): about half of a
    same-day pull is this shape. A leading "<digits><space>" title is a
    cheap, reliable tell; a real headline like "161-year-old kids clothing
    giant closes 29 more stores" has no space right after its digits, so it
    survives.
    """
    return [i for i in items if not _LISTICLE_TITLE.match(i["title"])]


def tag_sentiment(title):
    lower = title.lower()
    bull = sum(1 for w in BULLISH_WORDS if w in lower)
    bear = sum(1 for w in BEARISH_WORDS if w in lower)
    if bull > bear:
        return "bullish"
    if bear > bull:
        return "bearish"
    return "neutral"


def classify_category(title):
    lower = " " + title.lower() + " "
    best_cat, best_count = "other", 0
    for cat, words in CATEGORY_KEYWORDS.items():
        count = sum(1 for w in words if w in lower)
        if count > best_count:
            best_cat, best_count = cat, count
    return best_cat


def image_filename_for_url(url):
    """Content-addressed filename for a thumbnail URL: a stable hash of
    the URL, so the same source image always maps to the same cached
    file. This is what makes a headline that survives several hourly
    runs (inside the 48h window) dedupe for free -- the file already
    exists on disk, nothing is re-downloaded or re-committed. Always
    .jpg -- every cached image is re-encoded as JPEG by
    resize_thumbnail_bytes() regardless of the source format (Yahoo's
    RSS media:content width/height attributes describe its own embed
    display size, not the actual served file -- the real files run up
    to several MB / several thousand px per side, so re-encoding down to
    a real thumbnail is load-bearing, not cosmetic), so there's no
    source extension worth preserving.
    """
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    return f"{digest}.jpg"


IMAGE_TIMEOUT = 10
IMAGE_MAX_DIMENSION = 200
IMAGE_QUALITY = 80


def resize_thumbnail_bytes(data, max_dimension=IMAGE_MAX_DIMENSION, quality=IMAGE_QUALITY):
    """Decode arbitrary downloaded image bytes and re-encode as a small
    JPEG thumbnail, longer side capped at max_dimension (never upscaled).
    Always outputs JPEG regardless of source format, flattening any
    transparency onto a white background first (JPEG has no alpha
    channel; a naive RGB convert on a transparent image can produce a
    black background instead). Raises Pillow's own exception if `data`
    isn't a decodable image -- the caller decides how to handle that,
    this function doesn't swallow it.
    """
    with Image.open(io.BytesIO(data)) as im:
        w, h = im.size
        if max(w, h) > max_dimension:
            scale = max_dimension / max(w, h)
            # max(1, ...): an extreme aspect ratio (e.g. 5000x1) can scale
            # the short side down to 0px, which Image.resize() rejects
            # with a ValueError -- clamp to 1px instead of dropping an
            # otherwise-valid image.
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            im = im.resize((new_w, new_h), Image.LANCZOS)

        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            rgba = im.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[3])
            im = background
        else:
            im = im.convert("RGB")

        out = io.BytesIO()
        im.save(out, format="JPEG", quality=quality)
        return out.getvalue()


def _fetch_image_bytes(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def sync_news_images(items, images_dir, fetch=None):
    """Download each item's thumbnail into images_dir under a
    content-addressed filename, mutating each item with an `image` key
    (a relative "news-images/<hash>.jpg" path, or None if the item has
    no image_url, the download fails, or the downloaded bytes aren't a
    decodable image). A URL already cached on disk is never
    re-downloaded. One failed image never raises -- it just leaves that
    item's `image` as None, matching this whole feature's
    quality-of-life-not-load-bearing philosophy.

    `fetch` is an injectable (url, timeout) -> bytes callable, defaulting
    to a real HTTP GET; tests pass a fake to avoid real network calls.
    """
    fetch = fetch or _fetch_image_bytes
    os.makedirs(images_dir, exist_ok=True)
    for item in items:
        url = item.get("image_url")
        if not url:
            item["image"] = None
            continue
        filename = image_filename_for_url(url)
        dest = os.path.join(images_dir, filename)
        if not os.path.exists(dest):
            try:
                raw = fetch(url, IMAGE_TIMEOUT)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                print(f"Image fetch failed for {url} ({e}); skipping thumbnail.",
                      file=sys.stderr)
                item["image"] = None
                continue
            try:
                data = resize_thumbnail_bytes(raw)
            except Exception as e:
                # Untrusted bytes from an arbitrary external URL -- Pillow's
                # failure surface for "this isn't a valid/decodable image"
                # isn't a small fixed set of exception types, so this is
                # deliberately broad. One bad image must never block the
                # other headlines in this run.
                print(f"Image resize failed for {url} ({e}); skipping thumbnail.",
                      file=sys.stderr)
                item["image"] = None
                continue
            with open(dest, "wb") as f:
                f.write(data)
        item["image"] = f"{IMAGES_DIR_NAME}/{filename}"
    return items


def prune_dangling_images(images_dir, referenced_filenames):
    """Delete files under images_dir that aren't referenced by the
    envelope just built. Without this, news-images/ grows without bound
    -- every hourly run would leave behind thumbnails for headlines that
    have since rotated out of the 48h window.

    Returns the list of filenames actually deleted (for logging/tests).
    """
    if not os.path.isdir(images_dir):
        return []
    deleted = []
    for name in sorted(os.listdir(images_dir)):
        if name not in referenced_filenames:
            os.remove(os.path.join(images_dir, name))
            deleted.append(name)
    return deleted


def build_news_envelope(items, generated_at, source_item_count=None,
                        newest_item_published=None):
    """Build news.json.

    `source_item_count` and `newest_item_published` describe the feed as it
    arrived, BEFORE any filtering, and exist so a zero-headline run can be
    diagnosed without re-fetching. They are what separates the two failure
    modes that otherwise look identical from outside:

      - source_item_count == 0  -> the feed returned nothing; fetching broke.
      - source_item_count > 0 and headlines == []  -> the feed returned items
        but every one of them is older than MAX_AGE_HOURS; the SOURCE has gone
        stale, and no amount of re-running fixes it.

    The second case is what happened on 2026-09-25: 49 items arrived and all
    49 were older than 48h, because Yahoo's rssindex stopped publishing on
    2026-09-23. See docs/superpowers/bullion-r2-ui-punch-list.md.
    """
    headlines = []
    for i in items:
        headlines.append({
            "headline": i["title"],
            "link": i["link"],
            "published": i["published"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sentiment": tag_sentiment(i["title"]),
            "category": classify_category(i["title"]),
            "image": i.get("image"),
        })
    return {
        "generated_at": generated_at,
        "headlines": headlines,
        "source_item_count": source_item_count,
        "newest_item_published": newest_item_published,
    }


def fetch_news_rss(url=NEWS_RSS_URL, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main():
    now = datetime.now(timezone.utc)
    try:
        xml_text = fetch_news_rss()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        # Same philosophy as fetch_bullion_data.py: a failed fetch leaves
        # yesterday's news.json in place rather than writing an empty or
        # truncated ticker. This is a quality-of-life feature, not
        # load-bearing data -- it is not worth failing the whole daily cron
        # over, but it must not go silently stale either, so this prints
        # loudly to stderr for the workflow log to catch.
        print(f"News fetch failed ({e}); leaving existing {NEWS_OUT_PATH} untouched.",
              file=sys.stderr)
        sys.exit(1)

    all_items = parse_rss_items(xml_text)
    # Captured before filtering: the newest thing the SOURCE is publishing,
    # which is the number that actually diagnoses a zero-headline run.
    newest_published = max((i["published"] for i in all_items), default=None)

    items = filter_recent(all_items, now)
    items = filter_listicles(items)
    items = items[:MAX_HEADLINES]

    sync_news_images(items, IMAGES_DIR)

    generated_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    envelope = build_news_envelope(
        items,
        generated_at,
        source_item_count=len(all_items),
        newest_item_published=(
            newest_published.strftime("%Y-%m-%dT%H:%M:%SZ")
            if newest_published else None
        ),
    )

    referenced = {
        h["image"].split("/", 1)[1] for h in envelope["headlines"] if h.get("image")
    }
    deleted = prune_dangling_images(IMAGES_DIR, referenced)
    if deleted:
        print(f"Pruned {len(deleted)} dangling image(s) from {IMAGES_DIR_NAME}/.")

    with open(NEWS_OUT_PATH, "w") as f:
        json.dump(envelope, f, indent=2, sort_keys=True)
        f.write("\n")

    kept = len(envelope["headlines"])
    print(f"Wrote {NEWS_OUT_PATH} with {kept} headlines "
          f"(of {len(all_items)} fetched, filtered to last {MAX_AGE_HOURS}h).")

    # A zero-headline run is not an error -- refusing to present four-day-old
    # items as current news is the 48h filter doing its job, and overwriting
    # them would be worse than showing nothing. But it must never pass
    # quietly: on 2026-09-25 this exact state persisted for days behind a
    # green cron because the only thing anyone checked was generated_at,
    # which this script rewrites on every run regardless. Say it loudly here,
    # and let the workflow's freshness gate turn it into an alarm.
    if kept == 0:
        if not all_items:
            print("WARNING: the feed returned no items at all -- fetching is "
                  "broken, not merely stale.", file=sys.stderr)
        else:
            age = ""
            if newest_published:
                hours = (now - newest_published).total_seconds() / 3600
                age = (f" Newest item is {newest_published:%Y-%m-%dT%H:%M:%SZ}"
                       f" ({hours:.0f}h old).")
            print(f"WARNING: all {len(all_items)} items from the feed are older "
                  f"than {MAX_AGE_HOURS}h, so news.json is now empty. The "
                  f"SOURCE has gone stale, not this fetcher.{age}",
                  file=sys.stderr)


if __name__ == "__main__":
    main()

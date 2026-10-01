# Bullion Mk Ultra News Images Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-headline thumbnail images to the Markets tab's categorized news list, sourced from the RSS feed's own `<media:content>` tag, self-hosted as content-addressed local files (no CSP change, honors the project's vendoring principle), refreshed hourly during market hours instead of once a day.

**Architecture:** `fetch_bullion_news.py` gains an image-download step that runs after headline filtering: each headline's thumbnail URL (already present in Yahoo's feed, currently parsed but discarded) is hashed into a stable filename, downloaded once into `bullion-live-map/news-images/` if not already cached, and referenced from `news.json` by relative path. A prune step removes cached images no longer referenced once headlines age out. News fetching moves off the once-daily `daily-data.yml` workflow into its own hourly-during-market-hours workflow, decoupled from the once-daily FRED macro-data fetch. `bullion_mkultra.html`'s existing per-headline row renderer gains an `<img>` element when a headline has an image.

**Tech Stack:** Python 3.12 stdlib only (`urllib`, `hashlib`, `os`, `re` — no new dependency, matching the rest of `fetch_bullion_news.py`), vanilla JS/CSS in the existing single-file `bullion_mkultra.html`, GitHub Actions.

**Spec:** No separate spec file — this is a bounded addition scoped directly in chat (brainstorming session, 2026-09-04); the approved design is captured in this plan's Goal/Architecture above and the task list below.

## Global Constraints

- CSP stays `img-src 'self' data:` — every image reference must be a same-origin relative path. Never introduce an external host.
- Vendoring principle: no runtime dependency on a third-party CDN staying up (mirrors how Three.js is vendored, not loaded from jsDelivr).
- `fetch_bullion_news.py` is explicitly "quality-of-life... not load-bearing" (its own docstring) — no failure in this pipeline (RSS fetch, a single image download, a prune pass) may raise past `main()` in a way that fails the GitHub Actions job or trips the `pipeline-alarm` mechanism in `daily-data.yml`. One bad image must never block the other 39.
- `fetch_bullion_data.py` (FRED macro data) and its once-daily cadence in `daily-data.yml` are untouched by this plan — only `fetch_bullion_news.py`'s invocation moves.
- Follow the existing path-resolution pattern from `fetch_bullion_data.py` (`OUT_DIR = os.path.dirname(os.path.abspath(__file__))`) for every new/fixed path constant in `fetch_bullion_news.py` — see Task 1, this is fixing a real bug, not style preference.
- Test file conventions: `unittest`, one `TestCase` subclass per function under test, `sys.path.insert(0, ...)` shim already at the top of `tests/test_fetch_bullion_news.py` — follow it, don't introduce pytest-only syntax.
- Every task's diff must be explained in plain language (what changed, why) before being accepted — this is a standing rule for all work in this environment, not specific to this plan.

---

## Pre-existing bug discovered during planning (fixed by Task 1)

`fetch_bullion_news.py` currently defines `NEWS_OUT_PATH = "news.json"` — a bare relative path. `fetch_bullion_data.py`, by contrast, resolves its output path relative to its own file location (`OUT_DIR = os.path.dirname(os.path.abspath(__file__))`). GitHub Actions `run:` steps default their working directory to the repo root, not the script's own directory. Evidence this is live and biting right now:

- `git log --oneline -- bullion-live-map/news.json` shows only 2 commits ever: `8921f57` (the feature's initial add) and `269c58e` (the category redesign) — the same day, 2026-09-01. Zero daily-bot commits since.
- `git log --oneline -- bullion-live-map/data.json` over the same window shows a commit every single day (`73b274c`, `71e1297`, `c3e676b`, ...) — the sibling script that resolves its path correctly has been updating fine.
- The GitHub Actions run history for `daily-data.yml` shows the "Fetch news headlines for the Markets tab" step completing with `conclusion: success` on every run from 2026-09-01 through 2026-09-04 (checked via the public Actions API) — the script isn't crashing, it's silently writing to the wrong location (`$GITHUB_WORKSPACE/news.json` at the repo root) inside the ephemeral runner, which is discarded when the job container is torn down, so nothing is ever there to commit.

Net effect: the live news bar has shown the same 2026-09-01 headlines for 3+ days, invisible because `continue-on-error: true` keeps the job green. Task 1 fixes this as part of the same path-resolution change the new `IMAGES_DIR` constant needs anyway — it is not a separate, optional cleanup.

---

### Task 1: Fix path resolution (bug fix) and add image-path constants

**Files:**
- Modify: `bullion-live-map/fetch_bullion_news.py` (top-of-file constants, ~lines 16-31)
- Test: `bullion-live-map/tests/test_fetch_bullion_news.py`

**Interfaces:**
- Produces: `OUT_DIR` (str, absolute), `NEWS_OUT_PATH` (str, absolute), `IMAGES_DIR_NAME` (str, `"news-images"`), `IMAGES_DIR` (str, absolute) — later tasks import/use these names exactly.

- [ ] **Step 1: Write the failing regression test**

Add to `tests/test_fetch_bullion_news.py` (new class, after the existing imports — also add `import os` if not already imported at module level; it already is, via the `sys.path.insert` line's use of `os.path`):

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd bullion-live-map && python3 -m unittest tests.test_fetch_bullion_news.TestPathsAreFileRelative -v`
Expected: FAIL — `AttributeError: module 'fetch_bullion_news' has no attribute 'IMAGES_DIR'` (and `NEWS_OUT_PATH` is currently just `"news.json"`, so `os.path.dirname(...)` is `""`, not `expected_dir`).

- [ ] **Step 3: Fix the constants**

In `fetch_bullion_news.py`, replace:

```python
NEWS_RSS_URL = "https://finance.yahoo.com/news/rssindex"
NEWS_OUT_PATH = "news.json"
MAX_AGE_HOURS = 48
```

with:

```python
NEWS_RSS_URL = "https://finance.yahoo.com/news/rssindex"
# Anchored to the script's own directory, not the caller's CWD -- GitHub
# Actions `run:` steps default CWD to the repo root, so a bare relative
# path here silently wrote to the wrong location for 3+ days (see the
# plan doc this task came from). fetch_bullion_data.py already gets this
# right; mirror its OUT_DIR pattern instead of inventing a new one.
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_OUT_PATH = os.path.join(OUT_DIR, "news.json")
IMAGES_DIR_NAME = "news-images"
IMAGES_DIR = os.path.join(OUT_DIR, IMAGES_DIR_NAME)
MAX_AGE_HOURS = 48
```

Add `import os` to the import block at the top of the file (alongside the existing `import html`, `import json`, `import re`, `import sys`).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd bullion-live-map && python3 -m unittest tests.test_fetch_bullion_news.TestPathsAreFileRelative -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Run the full existing suite to confirm nothing else broke**

Run: `cd bullion-live-map && python3 -m unittest discover -s tests -v 2>&1 | tail -20`
Expected: all previously-passing tests still pass (156 as of the last handoff, now +2 for this task = 158).

- [ ] **Step 6: Commit**

```bash
git add bullion-live-map/fetch_bullion_news.py bullion-live-map/tests/test_fetch_bullion_news.py
git commit -m "Fix fetch_bullion_news.py output paths to resolve relative to the script, not CWD"
```

---

### Task 2: Parse the image URL out of the RSS feed's `<media:content>` tag

**Files:**
- Modify: `bullion-live-map/fetch_bullion_news.py` (`parse_rss_items`, ~line 141)
- Test: `bullion-live-map/tests/test_fetch_bullion_news.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: each dict `parse_rss_items()` returns now has an `"image_url"` key (str or `None`) alongside the existing `"title"`, `"link"`, `"published"`.

- [ ] **Step 1: Write the failing test**

Add a new sample RSS fixture and tests near the existing `SAMPLE_RSS`/`TestParseRssItems` in `tests/test_fetch_bullion_news.py`:

```python
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
```

```python
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
```

(Add these as methods on the existing `TestParseRssItems` class.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd bullion-live-map && python3 -m unittest tests.test_fetch_bullion_news.TestParseRssItems -v`
Expected: FAIL — `KeyError: 'image_url'`

- [ ] **Step 3: Implement**

In `parse_rss_items`, change the item-building block from:

```python
        items.append({
            "title": html.unescape(title_m.group(1).strip()),
            "link": link_m.group(1).strip(),
            "published": published,
        })
```

to:

```python
        image_m = re.search(r'<media:content[^>]*\burl="([^"]*)"', block)
        items.append({
            "title": html.unescape(title_m.group(1).strip()),
            "link": link_m.group(1).strip(),
            "published": published,
            "image_url": image_m.group(1).strip() if image_m else None,
        })
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd bullion-live-map && python3 -m unittest tests.test_fetch_bullion_news.TestParseRssItems -v`
Expected: PASS (all tests in the class, existing + 3 new)

- [ ] **Step 5: Run the full suite**

Run: `cd bullion-live-map && python3 -m unittest discover -s tests -v 2>&1 | tail -20`
Expected: all pass, no regressions in `filter_listicles`/`filter_recent` tests (they build their own minimal dicts without `image_url` and never read that key, so they're unaffected).

- [ ] **Step 6: Commit**

```bash
git add bullion-live-map/fetch_bullion_news.py bullion-live-map/tests/test_fetch_bullion_news.py
git commit -m "Parse media:content thumbnail URL from the RSS feed"
```

---

### Task 3: Content-addressed filename for an image URL

**Files:**
- Modify: `bullion-live-map/fetch_bullion_news.py`
- Test: `bullion-live-map/tests/test_fetch_bullion_news.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `image_filename_for_url(url: str) -> str` — later tasks (4, 6) call this exactly.

- [ ] **Step 1: Write the failing test**

```python
class TestImageFilenameForUrl(unittest.TestCase):
    def test_same_url_always_produces_the_same_filename(self):
        url = "https://media.zenfs.com/en/reuters.com/89fed01bb8c2422ea700c6db81a37382.jpg"
        self.assertEqual(image_filename_for_url(url), image_filename_for_url(url))

    def test_different_urls_produce_different_filenames(self):
        a = image_filename_for_url("https://media.zenfs.com/en/a.jpg")
        b = image_filename_for_url("https://media.zenfs.com/en/b.jpg")
        self.assertNotEqual(a, b)

    def test_preserves_jpg_extension(self):
        url = "https://media.zenfs.com/en/24_7_wall_st__718/2353c1676228b59ba3205fd31ecddd52.jpg"
        self.assertTrue(image_filename_for_url(url).endswith(".jpg"))

    def test_preserves_png_extension(self):
        url = "https://example.com/thumb.png"
        self.assertTrue(image_filename_for_url(url).endswith(".png"))

    def test_normalizes_jpeg_to_jpg(self):
        url = "https://example.com/thumb.jpeg"
        self.assertTrue(image_filename_for_url(url).endswith(".jpg"))
        self.assertFalse(image_filename_for_url(url).endswith(".jpeg"))

    def test_defaults_to_jpg_when_extension_is_unrecognized(self):
        url = "https://s.yimg.com/uu/api/res/1.2/abc~B/no-extension-here"
        self.assertTrue(image_filename_for_url(url).endswith(".jpg"))

    def test_filename_has_no_path_separators_or_query_junk(self):
        url = "https://media.zenfs.com/en/reuters.com/89fed01bb8c2422ea700c6db81a37382.jpg?foo=bar"
        name = image_filename_for_url(url)
        self.assertNotIn("/", name)
        self.assertNotIn("?", name)
```

Add `image_filename_for_url` to the import block at the top of the test file (alongside `parse_rss_items`, `filter_recent`, etc.).

- [ ] **Step 2: Run test to verify it fails**

Run: `cd bullion-live-map && python3 -m unittest tests.test_fetch_bullion_news.TestImageFilenameForUrl -v`
Expected: FAIL — `ImportError: cannot import name 'image_filename_for_url'`

- [ ] **Step 3: Implement**

Add `import hashlib` to the import block at the top of `fetch_bullion_news.py`. Add this function (near `classify_category`, before `build_news_envelope`):

```python
_IMAGE_EXT_RE = re.compile(r"\.(jpe?g|png|gif|webp)(?:$|[?&])", re.I)


def image_filename_for_url(url):
    """Content-addressed filename for a thumbnail URL: a stable hash of
    the URL plus its real extension, so the same source image always maps
    to the same file. This is what makes a headline that survives several
    hourly runs (inside the 48h window) dedupe for free -- the file
    already exists on disk, nothing is re-downloaded or re-committed.
    """
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    match = _IMAGE_EXT_RE.search(url.lower())
    ext = match.group(1) if match else "jpg"
    if ext == "jpeg":
        ext = "jpg"
    return f"{digest}.{ext}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd bullion-live-map && python3 -m unittest tests.test_fetch_bullion_news.TestImageFilenameForUrl -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Run the full suite**

Run: `cd bullion-live-map && python3 -m unittest discover -s tests -v 2>&1 | tail -20`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add bullion-live-map/fetch_bullion_news.py bullion-live-map/tests/test_fetch_bullion_news.py
git commit -m "Add content-addressed filename helper for news thumbnails"
```

---

### Task 4: Download and cache images, with dedup and per-image failure isolation

**Files:**
- Modify: `bullion-live-map/fetch_bullion_news.py`
- Test: `bullion-live-map/tests/test_fetch_bullion_news.py`

**Interfaces:**
- Consumes: `image_filename_for_url(url) -> str` (Task 3).
- Produces: `sync_news_images(items, images_dir, fetch=None) -> list` — mutates each item in `items` to add an `"image"` key (`"news-images/<hash>.<ext>"` relative-path string, or `None`), and returns the same list. `fetch` is an injectable `(url: str, timeout: int) -> bytes` callable (defaults to a real HTTP GET via `_fetch_image_bytes`); Task 6/9 rely on this signature to fake network calls in tests.

- [ ] **Step 1: Write the failing tests**

```python
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
            return b"fake-jpeg-bytes"

        items = [{"title": "t", "link": "l", "image_url": "https://example.com/a.jpg"}]
        sync_news_images(items, images_dir, fetch=fake_fetch)

        self.assertEqual(calls, ["https://example.com/a.jpg"])
        expected_name = image_filename_for_url("https://example.com/a.jpg")
        self.assertEqual(items[0]["image"], f"news-images/{expected_name}")
        with open(os.path.join(images_dir, expected_name), "rb") as f:
            self.assertEqual(f.read(), b"fake-jpeg-bytes")

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
            return b"good-bytes"

        items = [
            {"title": "fails", "link": "l1", "image_url": "https://example.com/bad.jpg"},
            {"title": "works", "link": "l2", "image_url": "https://example.com/good.jpg"},
        ]
        sync_news_images(items, images_dir, fetch=flaky_fetch)

        self.assertIsNone(items[0]["image"])
        self.assertIsNotNone(items[1]["image"])

    def test_creates_images_dir_if_missing(self):
        parent = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, parent, ignore_errors=True)
        images_dir = os.path.join(parent, "does", "not", "exist", "yet")
        items = [{"title": "t", "link": "l", "image_url": "https://example.com/c.jpg"}]
        sync_news_images(items, images_dir, fetch=lambda u, t: b"x")
        self.assertTrue(os.path.isdir(images_dir))
```

Add `import tempfile`, `import shutil`, `import urllib.error` (the last is likely already imported at module level — confirm) and `sync_news_images`, `image_filename_for_url` to the test file's import block.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd bullion-live-map && python3 -m unittest tests.test_fetch_bullion_news.TestSyncNewsImages -v`
Expected: FAIL — `ImportError: cannot import name 'sync_news_images'`

- [ ] **Step 3: Implement**

Add near `image_filename_for_url` in `fetch_bullion_news.py`:

```python
IMAGE_TIMEOUT = 10


def _fetch_image_bytes(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def sync_news_images(items, images_dir, fetch=None):
    """Download each item's thumbnail into images_dir under a
    content-addressed filename, mutating each item with an `image` key
    (a relative "news-images/<hash>.<ext>" path, or None if the item has
    no image_url or the download fails). A URL already cached on disk is
    never re-downloaded. One failed image never raises -- it just leaves
    that item's `image` as None, matching this whole feature's
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
                data = fetch(url, IMAGE_TIMEOUT)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                print(f"Image fetch failed for {url} ({e}); skipping thumbnail.",
                      file=sys.stderr)
                item["image"] = None
                continue
            with open(dest, "wb") as f:
                f.write(data)
        item["image"] = f"{IMAGES_DIR_NAME}/{filename}"
    return items
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd bullion-live-map && python3 -m unittest tests.test_fetch_bullion_news.TestSyncNewsImages -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Run the full suite**

Run: `cd bullion-live-map && python3 -m unittest discover -s tests -v 2>&1 | tail -20`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add bullion-live-map/fetch_bullion_news.py bullion-live-map/tests/test_fetch_bullion_news.py
git commit -m "Download and cache news thumbnails with dedup and per-image failure isolation"
```

---

### Task 5: Prune dangling cached images

**Files:**
- Modify: `bullion-live-map/fetch_bullion_news.py`
- Test: `bullion-live-map/tests/test_fetch_bullion_news.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `prune_dangling_images(images_dir, referenced_filenames) -> list` — returns the filenames it deleted; Task 6 calls this after building the envelope.

- [ ] **Step 1: Write the failing tests**

```python
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
```

Add `prune_dangling_images` to the test file's import block.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd bullion-live-map && python3 -m unittest tests.test_fetch_bullion_news.TestPruneDanglingImages -v`
Expected: FAIL — `ImportError: cannot import name 'prune_dangling_images'`

- [ ] **Step 3: Implement**

Add to `fetch_bullion_news.py`, near `sync_news_images`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd bullion-live-map && python3 -m unittest tests.test_fetch_bullion_news.TestPruneDanglingImages -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Run the full suite**

Run: `cd bullion-live-map && python3 -m unittest discover -s tests -v 2>&1 | tail -20`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add bullion-live-map/fetch_bullion_news.py bullion-live-map/tests/test_fetch_bullion_news.py
git commit -m "Prune cached news thumbnails no longer referenced by news.json"
```

---

### Task 6: Wire `image` into the envelope, and wire the whole pipeline together in `main()`

**Files:**
- Modify: `bullion-live-map/fetch_bullion_news.py` (`build_news_envelope`, ~line 209; `main`, ~line 228)
- Test: `bullion-live-map/tests/test_fetch_bullion_news.py`

**Interfaces:**
- Consumes: `sync_news_images` (Task 4), `prune_dangling_images` (Task 5).
- Produces: each headline dict from `build_news_envelope()` now has an `"image"` key (str or `None`).

- [ ] **Step 1: Write the failing tests**

Add to the existing `TestBuildNewsEnvelope` class (do not modify `test_envelope_shape`, which must keep passing unchanged — it builds items with no `"image"` key at all, proving the field is optional):

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd bullion-live-map && python3 -m unittest tests.test_fetch_bullion_news.TestBuildNewsEnvelope -v`
Expected: FAIL — `KeyError: 'image'`

- [ ] **Step 3: Implement — `build_news_envelope`**

Change:

```python
        headlines.append({
            "headline": i["title"],
            "link": i["link"],
            "published": i["published"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sentiment": tag_sentiment(i["title"]),
            "category": classify_category(i["title"]),
        })
```

to:

```python
        headlines.append({
            "headline": i["title"],
            "link": i["link"],
            "published": i["published"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sentiment": tag_sentiment(i["title"]),
            "category": classify_category(i["title"]),
            "image": i.get("image"),
        })
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd bullion-live-map && python3 -m unittest tests.test_fetch_bullion_news.TestBuildNewsEnvelope -v`
Expected: PASS (all tests in the class, existing `test_envelope_shape` unchanged + 2 new)

- [ ] **Step 5: Wire `sync_news_images`/`prune_dangling_images` into `main()`**

In `main()`, change:

```python
    items = parse_rss_items(xml_text)
    items = filter_recent(items, now)
    items = filter_listicles(items)
    items = items[:MAX_HEADLINES]

    generated_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    envelope = build_news_envelope(items, generated_at)

    with open(NEWS_OUT_PATH, "w") as f:
```

to:

```python
    items = parse_rss_items(xml_text)
    items = filter_recent(items, now)
    items = filter_listicles(items)
    items = items[:MAX_HEADLINES]

    sync_news_images(items, IMAGES_DIR)

    generated_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    envelope = build_news_envelope(items, generated_at)

    referenced = {
        h["image"].split("/", 1)[1] for h in envelope["headlines"] if h.get("image")
    }
    deleted = prune_dangling_images(IMAGES_DIR, referenced)
    if deleted:
        print(f"Pruned {len(deleted)} dangling image(s) from {IMAGES_DIR_NAME}/.")

    with open(NEWS_OUT_PATH, "w") as f:
```

This is not independently unit-testable (it performs real network I/O via `main()`, same as the rest of `main()` today, which has no direct unit test either — only its sub-functions do). It is verified end-to-end in Task 9.

- [ ] **Step 6: Run the full suite**

Run: `cd bullion-live-map && python3 -m unittest discover -s tests -v 2>&1 | tail -20`
Expected: all pass (158 + 2 from Task 6 = 160; running total after Tasks 2-5 add their own: verify the printed count matches sum of all new tests added so far — Task 1: +2, Task 2: +3, Task 3: +7, Task 4: +5, Task 5: +3, Task 6: +2 → 156 + 22 = 178).

- [ ] **Step 7: Commit**

```bash
git add bullion-live-map/fetch_bullion_news.py bullion-live-map/tests/test_fetch_bullion_news.py
git commit -m "Wire image download/prune into the news envelope and main() pipeline"
```

---

### Task 7: Split news fetching into its own hourly-during-market-hours workflow

**Files:**
- Create: `.github/workflows/news-hourly.yml`
- Modify: `.github/workflows/daily-data.yml` (remove the news-fetch step and its `news.json` git-add entry)

**Interfaces:**
- Consumes: `bullion-live-map/fetch_bullion_news.py` as a subprocess (Task 6's output).
- Produces: nothing consumed by later tasks — this is a leaf change.

- [ ] **Step 1: Create the new workflow file**

```yaml
name: Hourly News Update

# fetch_bullion_news.py needs a much tighter cadence than the once-daily
# macro-data fetch: Yahoo's RSS feed churns real headlines every 2-8
# minutes during market hours and only holds a rolling recent window, so
# the old once-daily pull was silently missing most of a day's real news
# (confirmed empirically 2026-09-04 -- see
# docs/superpowers/plans/2026-09-04-bullion-mkultra-news-images.md).
# Kept as its own workflow, separate from daily-data.yml, so the FRED
# macro-data fetch (which genuinely doesn't change hourly) isn't dragged
# along for the ride, and so the two workflows never race each other's
# git push on the same files.
#
# Market hours only, weekdays: 13:00-21:00 UTC covers the NYSE session
# (9:30am-4pm ET) with margin on both ends across DST; polling overnight
# or on weekends would just re-fetch the same recycled feed items.
# Minute offset off :00 for the same reason daily-data.yml's cron is
# offset -- GitHub delays jobs scheduled on the hour under load.
on:
  schedule:
    - cron: "11 13-21 * * 1-5"
  workflow_dispatch:

permissions:
  contents: write
  issues: write

jobs:
  update-news:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Fetch news headlines for the Markets tab
        # Quality-of-life only, not load-bearing market data -- must not
        # fail this job. A failed RSS fetch leaves the existing news.json
        # and news-images/ untouched; a failed individual image download
        # is caught inside sync_news_images and never aborts the run.
        continue-on-error: true
        run: python3 bullion-live-map/fetch_bullion_news.py

      - name: Commit and push if news changed
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add -A -- bullion-live-map/news.json bullion-live-map/news-images/
          if git diff --cached --quiet; then
            echo "No news changes this run; nothing to commit."
          else
            git commit -m "Update news headlines for $(date -u +%FT%H:%MZ)"
            git push
          fi

      - name: Check news.json freshness
        # Checks the *content* of news.json, not the fetch step's exit
        # code -- exit-code-0-while-writing-to-the-wrong-place is exactly
        # how the pre-existing bug this plan fixes (see Task 1) went
        # unnoticed for 3+ days. Threshold is 6h: generous enough that a
        # couple of missed/flaky hourly runs don't false-alarm, tight
        # enough to catch a real break same business day. Because this
        # step runs after this run's own fetch attempt, a normal
        # overnight/weekend gap never trips it -- if this run's fetch
        # succeeded, generated_at is seconds old regardless of how long
        # the previous gap was; it's only stale if fetching has actually
        # been failing.
        id: freshness
        run: |
          python3 - <<'PY' >> "$GITHUB_OUTPUT"
          import json
          from datetime import datetime, timezone

          STALE_AFTER_HOURS = 6
          try:
              with open("bullion-live-map/news.json") as f:
                  generated_at_raw = json.load(f)["generated_at"]
              generated_at = datetime.strptime(
                  generated_at_raw, "%Y-%m-%dT%H:%M:%SZ"
              ).replace(tzinfo=timezone.utc)
              age_hours = (datetime.now(timezone.utc) - generated_at).total_seconds() / 3600
              stale = age_hours > STALE_AFTER_HOURS
              print(f"stale={'true' if stale else 'false'}")
              print(f"age_hours={age_hours:.1f}")
          except Exception as e:
              # Missing file, unparseable JSON, missing/malformed
              # generated_at -- any of these mean the pipeline is broken,
              # not just slow.
              print("stale=true")
              print(f"age_hours=unknown ({e})")
          PY

      - name: Ensure the news-pipeline-stale label exists
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            try {
              await github.rest.issues.createLabel({
                owner: context.repo.owner,
                repo: context.repo.repo,
                name: 'news-pipeline-stale',
                color: 'd93f0b',
                description: 'Hourly news fetch has not produced fresh data recently',
              });
            } catch (err) {
              if (err.status !== 422) throw err; // 422 = label already exists
            }

      - name: Report staleness to the alarm issue
        if: steps.freshness.outputs.stale == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            const runUrl = `${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`;
            const ageHours = '${{ steps.freshness.outputs.age_hours }}';
            const now = new Date().toISOString();
            const body = `**${now}** — news.json is stale (age: ${ageHours}h, threshold: 6h).\nRun: ${runUrl}`;

            const { data: issues } = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              state: 'open',
              labels: 'news-pipeline-stale',
            });

            if (issues.length === 0) {
              await github.rest.issues.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: 'News pipeline has gone stale',
                body,
                labels: ['news-pipeline-stale'],
                assignees: [context.repo.owner],
              });
            } else {
              // Each stale run comments rather than opening a duplicate,
              // same pattern as daily-data.yml's own alarm.
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issues[0].number,
                body,
              });
            }

      - name: Close the news-pipeline-stale issue on recovery
        if: steps.freshness.outputs.stale == 'false'
        uses: actions/github-script@v7
        with:
          script: |
            const { data: issues } = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              state: 'open',
              labels: 'news-pipeline-stale',
            });
            const now = new Date().toISOString();
            for (const issue of issues) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                body: `Recovered — news.json is fresh again as of ${now}.`,
              });
              await github.rest.issues.update({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                state: 'closed',
              });
            }
```

**Interfaces note:** the freshness check's `stale`/`age_hours` step outputs are consumed only by the two steps immediately below it in this same file — nothing outside `news-hourly.yml` depends on them.

- [ ] **Step 2: Trim `daily-data.yml`**

Remove this step entirely:

```yaml
      - name: Fetch news headlines for the Markets tab
        # Quality-of-life only, not load-bearing market data -- must not
        # trip the pipeline-alarm below or block the data.json commit. A
        # failed run leaves the existing news.json in place.
        continue-on-error: true
        run: python3 bullion-live-map/fetch_bullion_news.py
```

And change the commit step's `git add` line from:

```yaml
          git add bullion-live-map/data.json bullion-live-map/news.json
```

to:

```yaml
          git add bullion-live-map/data.json
```

Leave every other step in `daily-data.yml` (FRED key provisioning, `fetch_bullion_data.py`, the pipeline-alarm label/report/close steps) untouched — this workflow still owns `data.json` and the alarm mechanism exactly as before.

- [ ] **Step 3: Validate YAML syntax**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/news-hourly.yml'))" && python3 -c "import yaml; yaml.safe_load(open('.github/workflows/daily-data.yml'))"`
Expected: no output, exit code 0 (both files parse). If `yaml` isn't installed, run `pip install pyyaml` first or use `python3 -c "import json,sys; sys.path.insert(0,'.'); import ruamel.yaml"` as a fallback — either way, confirm both files parse before moving on.

- [ ] **Step 4: Locally simulate the freshness-check logic against both a fresh and a stale fixture**

The freshness check is inline YAML Python, outside the unittest suite's reach — exercise the exact same logic locally against two fixtures before trusting it in CI:

```bash
mkdir -p /tmp/freshness-check-sim/bullion-live-map
cd /tmp/freshness-check-sim

# Fresh fixture: generated_at = now.
python3 -c "
import json
from datetime import datetime, timezone
json.dump(
    {'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'headlines': []},
    open('bullion-live-map/news.json', 'w'),
)
"
python3 - <<'PY'
import json
from datetime import datetime, timezone

STALE_AFTER_HOURS = 6
with open("bullion-live-map/news.json") as f:
    generated_at_raw = json.load(f)["generated_at"]
generated_at = datetime.strptime(generated_at_raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
age_hours = (datetime.now(timezone.utc) - generated_at).total_seconds() / 3600
stale = age_hours > STALE_AFTER_HOURS
print(f"fresh-fixture -> stale={'true' if stale else 'false'} age_hours={age_hours:.2f}")
PY

# Stale fixture: generated_at = 30 hours ago.
python3 -c "
import json
from datetime import datetime, timezone, timedelta
old = datetime.now(timezone.utc) - timedelta(hours=30)
json.dump({'generated_at': old.strftime('%Y-%m-%dT%H:%M:%SZ'), 'headlines': []}, open('bullion-live-map/news.json', 'w'))
"
python3 - <<'PY'
import json
from datetime import datetime, timezone

STALE_AFTER_HOURS = 6
with open("bullion-live-map/news.json") as f:
    generated_at_raw = json.load(f)["generated_at"]
generated_at = datetime.strptime(generated_at_raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
age_hours = (datetime.now(timezone.utc) - generated_at).total_seconds() / 3600
stale = age_hours > STALE_AFTER_HOURS
print(f"stale-fixture -> stale={'true' if stale else 'false'} age_hours={age_hours:.2f}")
PY

# Missing-file case.
rm bullion-live-map/news.json
python3 - <<'PY'
import json
try:
    with open("bullion-live-map/news.json") as f:
        json.load(f)["generated_at"]
    print("missing-file -> did not raise (unexpected)")
except Exception as e:
    print(f"missing-file -> correctly raised: {e}")
PY

cd - && rm -rf /tmp/freshness-check-sim
```

Expected: `fresh-fixture -> stale=false age_hours=0.00`, `stale-fixture -> stale=true age_hours=30.00`, `missing-file -> correctly raised: ...`. This confirms the three branches (fresh, genuinely stale, broken/missing) all resolve the way the workflow step expects before it ever runs for real in CI.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/news-hourly.yml .github/workflows/daily-data.yml
git commit -m "Split news fetching into its own hourly-during-market-hours workflow with a staleness alarm"
```

---

### Task 8: Render thumbnails in the Markets tab news list

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` (CSS ~line 232-245, `buildNewsItem` ~line 3478)

**Interfaces:**
- Consumes: `h.image` (str or `null`) from `news.json`, produced by Task 6.

- [ ] **Step 1: Add CSS for the thumbnail**

Near the existing `.news-item` rules (~line 240), add:

```css
  .news-item { align-items: center; }
  .news-item-thumb {
    flex: 0 0 auto; width: 48px; height: 32px; border-radius: 4px;
    object-fit: cover; background: var(--bg-panel2);
  }
```

Note this changes `.news-item`'s existing `align-items: baseline` to `center` (it currently reads `.news-item { display: flex; align-items: baseline; ... }` — change that declaration in place rather than adding a second rule) so rows with a thumbnail don't look misaligned against the text baseline; this applies to every row, including ones without an image, and is a deliberate small visual change, not a bug. Confirm it still looks right for image-less rows in Task 9's visual check.

- [ ] **Step 2: Render the `<img>` in `buildNewsItem`**

Change:

```js
function buildNewsItem(h) {
  const a = document.createElement('a');
  a.className = 'news-item sentiment-' + (h.sentiment || 'neutral');
  a.href = h.link;
  a.target = '_blank';
  a.rel = 'noopener noreferrer';

  const time = document.createElement('span');
```

to:

```js
function buildNewsItem(h) {
  const a = document.createElement('a');
  a.className = 'news-item sentiment-' + (h.sentiment || 'neutral');
  a.href = h.link;
  a.target = '_blank';
  a.rel = 'noopener noreferrer';

  if (h.image) {
    const thumb = document.createElement('img');
    thumb.className = 'news-item-thumb';
    thumb.src = h.image;
    thumb.alt = '';
    thumb.loading = 'lazy';
    thumb.onerror = function () { thumb.remove(); };
    a.appendChild(thumb);
  }

  const time = document.createElement('span');
```

The `onerror` handler is defensive (matches `loadNewsList`'s own catch-and-degrade-gracefully pattern for the whole feed): if a referenced image file is ever missing, the row still renders cleanly without a broken-image icon rather than failing the whole list.

- [ ] **Step 3: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "Render news thumbnails in the Markets tab headline list"
```

(No automated test for this step — it's verified visually in Task 9 via the project's existing headless-Chrome idiom.)

---

### Task 9: End-to-end verification

**Files:** none (verification only).

- [ ] **Step 1: Full test suite**

Run: `cd bullion-live-map && python3 -m unittest discover -s tests -v 2>&1 | tail -5`
Expected: all pass, count matches the running total from Task 6, Step 6 (178, assuming no other test files changed in this plan).

- [ ] **Step 2: Real end-to-end run of the fetch script, from the repo root (this is what actually exercises the Task 1 bug fix)**

```bash
cd ~/claude-projects/claudekit
python3 bullion-live-map/fetch_bullion_news.py
ls -la bullion-live-map/news-images/ | head -20
python3 -c "import json; d=json.load(open('bullion-live-map/news.json')); print(len(d['headlines']), 'headlines'); print(sum(1 for h in d['headlines'] if h['image']), 'with images'); print(d['headlines'][0])"
```

Expected: `bullion-live-map/news.json` and `bullion-live-map/news-images/*.jpg` are both written **relative to the repo root invocation** (proving Task 1's fix works under the same CWD GitHub Actions uses), most headlines have a non-null `image` pointing to a file that actually exists in `news-images/`.

- [ ] **Step 3: Confirm dedup by running it again immediately**

```bash
ls bullion-live-map/news-images/ | wc -l
python3 bullion-live-map/fetch_bullion_news.py
ls bullion-live-map/news-images/ | wc -l
```

Expected: the file count barely changes (only genuinely new headlines since the last run add new files) — not roughly doubled, which would indicate dedup isn't working.

- [ ] **Step 4: Visual verification in headless Chrome**

Follow the exact idiom from `docs/superpowers/bullion-mkultra-news-categories-shipped-handoff.md`'s "Verification idioms" section: serve via `python3 -m http.server <port>` from `bullion-live-map/` (never `file://`), drive real headless Chrome via `~/.claude/skills/headless-chrome-verification/templates/cdp_probe.mjs` with `--use-gl=angle --use-angle=swiftshader --user-data-dir=/tmp/<unique>` and real wall-clock `sleep()` (not `--virtual-time-budget`). Confirm:
- Thumbnails render at the expected size/position in each news row
- Rows with `image: null` still render cleanly (no broken-image icon, no layout shift)
- Zero console errors
- Take a screenshot and visually inspect it

- [ ] **Step 5: Clean up local scratch state**

The end-to-end run in Step 2 wrote real files into the working tree (`bullion-live-map/news.json`, `bullion-live-map/news-images/`). Decide with the user whether to commit this real snapshot as the first live data (recommended — it's genuine, verified-correct output, the same way the daily bot's own commits work) or discard it (`git checkout -- bullion-live-map/news.json && git clean -fd bullion-live-map/news-images/`) if a fresher one should come from the actual scheduled workflow instead. Do not leave it as uncommitted, undiscarded working-tree state.

- [ ] **Step 6: Confirm the workflow actually runs on schedule, and watch the staleness alarm for real**

This can only be verified after the plan is merged to `main` — GitHub only runs the `schedule:` trigger for workflows on the default branch:

1. After merging, either wait for the next `11 13-21 * * 1-5` window or trigger it manually: `workflow_dispatch` via the GitHub UI, or `curl -X POST -H "Authorization: token $TOKEN" .../actions/workflows/news-hourly.yml/dispatches -d '{"ref":"main"}'` (do not type a real token into this session — same rule as every other credential in this project; run any authenticated call yourself outside Claude Code, or use the UI button).
2. Poll `https://api.github.com/repos/SinbadTheExplorer/claudekit/actions/workflows/news-hourly.yml/runs?per_page=3` for `conclusion: success`, then confirm via the jobs API (same idiom used to diagnose the original bug in this plan's "Pre-existing bug" section) that the "Check news.json freshness" step's output was `stale=false`.
3. Leave it running for a few real days, then spot-check: has `bullion-live-map/news.json`'s `generated_at` actually been advancing hour over hour during market hours (`git log --oneline -- bullion-live-map/news.json` should now show a commit roughly every hour on weekdays, not the "2 commits total, ever" pattern that motivated Task 1)? This is the real proof the original bug is fixed, not just the local simulation in Task 7.
4. Do not synthetically force a real `news-pipeline-stale` GitHub issue to test the alarm end-to-end (e.g. by temporarily breaking the script in production) — that's a disproportionate way to test a safety net. Task 7's local simulation already proves the alarm's decision logic is correct; trust it, and let the alarm prove itself the only time it matters, which is if a real future regression happens.

---

## Execution note

Per the user's standing instruction for this environment: **explain each task's diff in plain language — what changed and why — before it's accepted**, whether a task is executed via `delegate` or directly. This applies task-by-task, not just at the end.

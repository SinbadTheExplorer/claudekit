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

# ─── NEWS SOURCES ──────────────────────────────────────────────────────────
# Four feeds across four independent vendors. That count is the point, not a
# nice-to-have: this file ran on ONE feed until 2026-09-28, and when
# https://finance.yahoo.com/news/rssindex quietly stopped being regenerated on
# 2026-09-24 the Markets tab simply emptied and stayed empty. Nothing was
# broken here -- the 48h filter correctly refused to present four-day-old
# items as current news -- but a single source means one vendor's neglect is
# indistinguishable from the feature being switched off.
#
# The dead endpoint is deliberately NOT in this list. Evidence it is
# abandoned rather than briefly down, gathered 2026-09-28: it still returns
# HTTP 200 and 49 items, but its `last-modified` header and its own channel
# `pubDate` agree on 2026-09-24T12:21 GMT and have not moved since, while
# `age: 439` against `cache-control: max-age=600` shows the CDN re-fetching
# from origin every 10 minutes and getting the same frozen document back. It
# also still declares `ttl: 5`, asking to be polled every five minutes, and
# carries stray items from 2024-11 and 2025-01. Yahoo's RSS infrastructure is
# fine -- the per-ticker endpoint below is live and current -- so this is one
# abandoned endpoint, not a vendor exit.
#
# Each entry is (key, label, url). `key` is stable and appears in news.json's
# per-source diagnostics, so renaming one breaks continuity of the alarm --
# add and remove whole entries rather than renaming keys.
#
# Sources were chosen on measured on-topic rate, not on reputation alone.
# Method: pull each feed's fresh-48h items, run classify_category over them,
# and count how many land somewhere other than the "other" catch-all. Run
# 2026-09-28:
#
#   Yahoo ^DJI      17 fresh   88% on-topic
#   MW Bulletins     5 fresh   80%
#   CNBC Top News   26 fresh   69%
#   MW Top Stories  10 fresh   40%   <- the only source carrying images
#   Yahoo ^GSPC     16 fresh   44%
#   BBC Business    19 fresh   21%   <- rejected
#
# BBC Business was tried first and dropped: at 21% it was filling the tab with
# UK domestic stories (Welsh tourism tax, rail nationalisation) that have
# nothing to do with a map of the US financial system. MW Top Stories is kept
# despite 40% because it is the only feed of the set that ships thumbnails,
# and its share is capped like every other source.
#
# Google News search feeds scored better than all of these (82% on-topic, 99
# fresh) and were still rejected: their links are opaque news.google.com
# redirects rather than publisher URLs, and the results mix wire copy with
# marketing blogs, which fails the "reputable sources" bar in criterion 2.
#
# MarketWatch appears twice, so a Dow Jones outage costs two of four sources.
# That is a known weakness, accepted because the per-source alarm below makes
# it loud rather than silent; swapping one for another vendor is a two-line
# change here.
NEWS_SOURCES = [
    ("cnbc",         "CNBC",          "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("yahoo_dji",    "Yahoo Finance", "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^DJI&region=US&lang=en-US"),
    ("marketwatch",  "MarketWatch",   "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("mw_bulletins", "MW Bulletins",  "https://feeds.content.dowjones.io/public/rss/mw_bulletins"),
]
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


_DEDUPE_STRIP = re.compile(r"[^a-z0-9 ]+")


def _dedupe_key(item):
    """Normalised title, used to spot the same story arriving twice.

    Title rather than link, because a syndicated story reaches two vendors
    under two URLs but near-identical wording. Punctuation and case are
    stripped so "Fed holds rates steady" and "Fed holds rates steady." are
    one story.
    """
    t = _DEDUPE_STRIP.sub("", item["title"].lower())
    return " ".join(t.split())


def dedupe_items(items):
    """Keep the first occurrence of each story, and of each link.

    Order matters: callers pass items in NEWS_SOURCES order, so an earlier
    source wins a tie. That keeps the choice of which vendor's wording to
    show deterministic instead of depending on which fetch finished first.
    """
    seen_titles, seen_links, out = set(), set(), []
    for i in items:
        tk, lk = _dedupe_key(i), i["link"]
        if tk in seen_titles or lk in seen_links:
            continue
        seen_titles.add(tk)
        seen_links.add(lk)
        out.append(i)
    return out


def select_headlines(by_source, max_headlines=MAX_HEADLINES):
    """Blend per-source lists into one recency-ordered set.

    Takes an even slice of each contributing source first, then backfills
    from whatever is left over, then sorts the result by recency.

    The two-pass shape is what makes a dead source harmless. A plain
    recency sort would let the highest-volume feed crowd the others out, so
    losing that feed would change the mix drastically. A fixed per-source cap
    with no backfill has the opposite failure: when a source dies its slots go
    unfilled and the tab quietly ships fewer headlines than it could. Taking
    an even share and then topping up from the remainder keeps the mix broad
    when every source is healthy and still fills the page when one is not.
    """
    live = [k for k, items in by_source.items() if items]
    if not live:
        return []

    share = max(1, -(-max_headlines // len(live)))   # ceil
    picked, leftovers = [], []
    for key in by_source:
        items = sorted(by_source[key], key=lambda i: i["published"], reverse=True)
        picked.extend(items[:share])
        leftovers.extend(items[share:])

    if len(picked) < max_headlines:
        leftovers.sort(key=lambda i: i["published"], reverse=True)
        picked.extend(leftovers[:max_headlines - len(picked)])

    picked.sort(key=lambda i: i["published"], reverse=True)
    return picked[:max_headlines]


def collect_sources(now, sources=NEWS_SOURCES):
    """Fetch every source, and report on each one individually.

    Returns (by_source, stats). A source that raises is recorded and skipped;
    one vendor being down must never cost us the other three.

    `stats` is what makes a single dead source detectable. Aggregate counts
    cannot do it: once there are four feeds, one freezing leaves the total
    healthy and the failure is invisible again -- the exact bug this whole
    change exists to stop, one level up. Per-source `fresh` is the signal,
    because a frozen feed keeps returning items (Yahoo's returned 49) and
    only the timestamps give it away.
    """
    by_source, stats = {}, {}
    for key, label, url in sources:
        entry = {"label": label, "ok": False, "fetched": 0, "fresh": 0,
                 "contributed": 0, "newest": None, "error": None}
        try:
            xml_text = fetch_news_rss(url)
        except Exception as e:                      # noqa: BLE001 - any failure is just "this source is down"
            entry["error"] = f"{type(e).__name__}: {e}"
            stats[key] = entry
            by_source[key] = []
            print(f"  {label}: FETCH FAILED -- {entry['error']}", file=sys.stderr)
            continue

        parsed = parse_rss_items(xml_text)
        entry["ok"] = True
        entry["fetched"] = len(parsed)
        if parsed:
            newest = max(i["published"] for i in parsed)
            entry["newest"] = newest.strftime("%Y-%m-%dT%H:%M:%SZ")

        recent = filter_listicles(filter_recent(parsed, now))
        # Tag each item with where it came from, so counting a source's
        # contribution later is a field lookup rather than an identity test
        # against the original lists.
        for i in recent:
            i["source"] = key
        entry["fresh"] = len(recent)
        by_source[key] = recent
        stats[key] = entry

        note = "" if recent else "  <-- nothing inside the freshness window"
        print(f"  {label}: {len(parsed)} fetched, {len(recent)} fresh{note}")
    return by_source, stats


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
                        newest_item_published=None, sources=None):
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
        # Per-source health. The aggregates above cannot see one feed dying
        # behind three healthy ones; this can. Consumed by news-hourly.yml.
        "sources": sources if sources is not None else {},
    }


def fetch_news_rss(url, timeout=15):
    """Fetch one feed. `url` is required -- there is no default source any
    more, and a default would quietly reintroduce the single point of failure
    this module was restructured to remove."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main():
    now = datetime.now(timezone.utc)

    print(f"Fetching {len(NEWS_SOURCES)} news sources:")
    by_source, stats = collect_sources(now)

    if not any(s["ok"] for s in stats.values()):
        # Every vendor unreachable at once is almost always us, not them --
        # no network in the runner, or DNS. Same philosophy as
        # fetch_bullion_data.py: leave the existing news.json alone rather
        # than overwrite good data with nothing, and exit non-zero so the
        # step is visibly unhappy.
        print(f"All {len(NEWS_SOURCES)} sources failed to fetch; leaving existing "
              f"{NEWS_OUT_PATH} untouched.", file=sys.stderr)
        sys.exit(1)

    # Dedupe across sources before selecting, so a story syndicated to three
    # vendors does not take three of the slots. NEWS_SOURCES order breaks
    # ties, which keeps the winner deterministic run to run.
    merged = dedupe_items([i for key in by_source for i in by_source[key]])
    kept_by_source = {key: [] for key in by_source}
    for i in merged:
        kept_by_source[i["source"]].append(i)

    items = select_headlines(kept_by_source)
    for key in stats:
        stats[key]["contributed"] = sum(1 for i in items if i.get("source") == key)

    sync_news_images(items, IMAGES_DIR)

    all_fetched = sum(s["fetched"] for s in stats.values())
    newest_overall = max(
        (s["newest"] for s in stats.values() if s["newest"]), default=None)

    generated_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    envelope = build_news_envelope(
        items,
        generated_at,
        source_item_count=all_fetched,
        newest_item_published=newest_overall,
        sources=stats,
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
    mix = ", ".join(f"{s['label']} {s['contributed']}" for s in stats.values())
    print(f"Wrote {NEWS_OUT_PATH} with {kept} headlines "
          f"(of {all_fetched} fetched across {len(NEWS_SOURCES)} sources, "
          f"filtered to last {MAX_AGE_HOURS}h) -- {mix}.")

    # Neither of the warnings below is an error. Refusing to present
    # four-day-old items as current news is the 48h filter doing its job, and
    # one vendor going quiet is not worth failing a run that still has three.
    # But neither may pass silently: on 2026-09-25 exactly this state ran for
    # days behind a green cron, because the only thing anyone checked was
    # generated_at, which this script rewrites every run regardless. Say it
    # here, and let the workflow's freshness gate raise it.
    for s in stats.values():
        if not s["ok"]:
            print(f"WARNING: {s['label']} could not be fetched ({s['error']}).",
                  file=sys.stderr)
        elif s["fetched"] == 0:
            print(f"WARNING: {s['label']} returned no parseable items -- its "
                  f"feed format may have changed.", file=sys.stderr)
        elif s["fresh"] == 0:
            age = ""
            if s["newest"]:
                newest = datetime.strptime(s["newest"], "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=timezone.utc)
                age = (f" Its newest item is {s['newest']} "
                       f"({(now - newest).total_seconds() / 3600:.0f}h old).")
            print(f"WARNING: {s['label']} returned {s['fetched']} items but none "
                  f"inside the {MAX_AGE_HOURS}h window -- this source looks "
                  f"FROZEN, the way Yahoo's rssindex did.{age}", file=sys.stderr)

    if kept == 0:
        print(f"WARNING: news.json is now EMPTY -- no source produced anything "
              f"inside the {MAX_AGE_HOURS}h window.", file=sys.stderr)


if __name__ == "__main__":
    main()

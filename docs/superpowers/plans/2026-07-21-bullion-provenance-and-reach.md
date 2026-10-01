# Bullion Mk11 Provenance & Reach Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every number on the Bullion Mk11 map declare where it came from and how fresh it is, and give the shared link a preview card worth tapping.

**Architecture:** `fetch_bullion_data.py` grows a schema-v2 envelope carrying per-field provenance (class, cadence, source, reference date, publication date). The HTML reads that envelope, branches on schema version for backward compatibility, and renders provenance on three surfaces: metric sub-lines, a provenance strip, and persistent markers on simulated values. A single pure `freshnessVerdict` function, mirrored in Python and JS, decides fresh vs. flagged.

**Tech Stack:** Python 3 standard library only. Vanilla JS inline in a single HTML file with D3 v7 bundled. Tests via `unittest` (stdlib) and a headless-Chrome HTML runner. No build step, no package manager, no new dependencies.

**Spec:** `docs/superpowers/specs/2026-07-20-bullion-provenance-and-reach-design.md`

## Global Constraints

- **No build step.** `bullion_mk11_constellation.html` must stay a single self-contained file, openable from `file://` with no server.
- **No new runtime dependencies.** `fetch_bullion_data.py` uses only the Python standard library.
- **Neither `pytest` nor `node` is installed.** Python tests use stdlib `unittest`; JS tests use a headless-Chrome HTML runner. Do not add install steps.
- **Chrome path:** `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- **Deployment URL:** `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/`
- **Freshness is judged on `published`, never `ref_date`.**
- **Tolerances:** `daily` 7 days, `monthly` 45 days, `fomc` none. Per-field override: `wti_px` 10 days.
- **Palette (from the map's own CSS):** `--bg-deep #05060a`, `--gold #d4b869`, `--text-dim #8891a6`, `--amber #e0b15a`.
- **Working directory for all commands:** `~/claude-projects/claudekit/`
- Commit after every task. Do not push — pushing requires the user's terminal.

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `bullion-live-map/preview-card.svg` | Create | Source for the social preview card |
| `bullion-live-map/preview-card.png` | Create | 1200×630 rasterised card, referenced by `og:image` |
| `bullion-live-map/fetch_bullion_data.py` | Modify | Add freshness logic, publication dates, schema-v2 envelope |
| `bullion-live-map/tests/test_fetch_bullion_data.py` | Create | unittest suite for the fetcher's pure logic |
| `bullion-live-map/tests/freshness_test.html` | Create | Headless-Chrome runner for the JS verdict function |
| `bullion_mk11_constellation.html` | Modify | OG tags, schema branching, provenance rendering |

Tasks 1–6 complete Tier 1. Tasks 7–8 complete Tier 2.

---

### Task 1: Social preview card and Open Graph tags

Standalone and zero-risk — touches only `<head>` and adds two new files. Nothing else in the plan depends on it.

**Files:**
- Create: `bullion-live-map/preview-card.svg`
- Create: `bullion-live-map/preview-card.png`
- Modify: `bullion_mk11_constellation.html` (inside `<head>`, after the `<title>` on line 6)

**Interfaces:**
- Consumes: nothing
- Produces: `preview-card.png` at a path the `og:image` tag hardcodes

- [ ] **Step 1: Write the card SVG**

Create `bullion-live-map/preview-card.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="#05060a"/>
  <g stroke="#1e2436" stroke-width="1.5" fill="none">
    <path d="M170 175 L330 120 L470 210 L330 300 Z"/>
    <path d="M330 120 L520 95 L470 210"/>
    <path d="M170 175 L240 330 L330 300"/>
    <path d="M470 210 L610 265 L520 95"/>
    <path d="M240 330 L400 430 L470 210"/>
  </g>
  <g fill="#d4b869">
    <circle cx="330" cy="120" r="8"/>
    <circle cx="470" cy="210" r="6"/>
    <circle cx="170" cy="175" r="5"/>
  </g>
  <g fill="#8891a6">
    <circle cx="330" cy="300" r="4.5"/>
    <circle cx="520" cy="95" r="4"/>
    <circle cx="240" cy="330" r="4"/>
    <circle cx="610" cy="265" r="3.5"/>
    <circle cx="400" cy="430" r="3.5"/>
  </g>
  <text x="700" y="255" font-family="Georgia, 'Times New Roman', serif" font-size="72" fill="#d4b869">Bullion Mk11</text>
  <text x="702" y="315" font-family="Helvetica, Arial, sans-serif" font-size="27" fill="#d8dce6">How the US financial system</text>
  <text x="702" y="352" font-family="Helvetica, Arial, sans-serif" font-size="27" fill="#d8dce6">actually connects</text>
  <text x="702" y="415" font-family="Helvetica, Arial, sans-serif" font-size="19" fill="#8891a6">Live yields, inflation, gold and volatility —</text>
  <text x="702" y="443" font-family="Helvetica, Arial, sans-serif" font-size="19" fill="#8891a6">every causal link explained in plain English.</text>
  <rect x="702" y="480" width="54" height="3" fill="#d4b869"/>
</svg>
```

- [ ] **Step 2: Rasterise to PNG and verify dimensions**

Run:

```bash
cd ~/claude-projects/claudekit/bullion-live-map && \
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --screenshot=preview-card.png \
  --window-size=1200,630 --default-background-color=00000000 \
  preview-card.svg 2>/dev/null && \
python3 -c "
import struct
d=open('preview-card.png','rb').read()
w,h=struct.unpack('>II', d[16:24])
print(f'{w}x{h}  {len(d)//1024}KB')
assert (w,h)==(1200,630), f'wrong size: {w}x{h}'
print('OK')
"
```

Expected: `1200x630  <size>KB` then `OK`.

If Chrome produces the wrong size, fall back to:
`qlmanage -t -s 1200 -o . preview-card.svg && mv preview-card.svg.png preview-card.png`
then re-run the dimension check.

- [ ] **Step 3: View the card and confirm it does not look broken**

Open `preview-card.png` with the Read tool and confirm: dark background, gold "Bullion Mk11" heading legible, subtitle text not overlapping the constellation motif, no clipped text at the right edge.

If text overlaps the motif, reduce the motif `<path>`/`<circle>` x-coordinates or shift the text block right, then re-run Step 2.

- [ ] **Step 4: Add the meta tags**

In `bullion_mk11_constellation.html`, immediately after the `<title>` line (line 6), insert:

```html
<meta name="description" content="An interactive map of how the US financial system actually connects — live Treasury yields, inflation, gold and volatility, with every causal link explained in plain English.">
<meta property="og:type" content="website">
<meta property="og:title" content="Bullion Mk11 — US Financial System Constellation">
<meta property="og:description" content="An interactive map of how the US financial system actually connects — live Treasury yields, inflation, gold and volatility, with every causal link explained in plain English.">
<meta property="og:url" content="https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mk11_constellation.html">
<meta property="og:image" content="https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/preview-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
```

- [ ] **Step 5: Verify the tags parse and the map still loads**

Run:

```bash
cd ~/claude-projects/claudekit/bullion-live-map && \
python3 -c "
import re
h=open('bullion_mk11_constellation.html',encoding='utf-8').read()
head=h[:h.index('<style>')]
for p in ['og:type','og:title','og:description','og:url','og:image','og:image:width','og:image:height','twitter:card']:
    assert p in head, 'MISSING '+p
print('all 8 OG tags present in <head>')
assert head.count('<title>')==1, 'title count changed'
# NB: check `head`, not `h` — a JS string literal near line 2911 builds the
# Audit Log popup and legitimately contains a second <title>.
print('OK')
"
```

Expected: `all 8 OG tags present in <head>` then `OK`.

Then open the map in Chrome and confirm it renders as before:

```bash
open -a "Google Chrome" ~/claude-projects/claudekit/bullion-live-map/bullion_mk11_constellation.html
```

Confirm the constellation draws and no console errors appear.

- [ ] **Step 6: Commit**

```bash
cd ~/claude-projects/claudekit && \
git add bullion-live-map/preview-card.svg bullion-live-map/preview-card.png bullion-live-map/bullion_mk11_constellation.html && \
git commit -m "Add social preview card and Open Graph tags

The shared link previously rendered as a bare URL with no title, image
or description. Adds a designed 1200x630 card in the map's own palette
plus the meta tags that reference it."
```

---

### Task 2: Freshness verdict in Python

The single rule that decides fresh vs. flagged. Pure function, no I/O, no network.

**Files:**
- Modify: `bullion-live-map/fetch_bullion_data.py`
- Create: `bullion-live-map/tests/test_fetch_bullion_data.py`

**Interfaces:**
- Consumes: nothing
- Produces: `freshness_verdict(cadence, published, today, override_days=None) -> (state, age_days)` where `state` is one of `'fresh'`, `'flagged'`, `'unknown'` and `age_days` is an `int` or `None`. Also `CADENCE_TOLERANCE_DAYS` and `FIELD_TOLERANCE_OVERRIDE` dicts, consumed by Task 3.

- [ ] **Step 1: Write the failing test**

Create `bullion-live-map/tests/test_fetch_bullion_data.py`:

```python
import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fetch_bullion_data import (
    freshness_verdict,
    CADENCE_TOLERANCE_DAYS,
    FIELD_TOLERANCE_OVERRIDE,
)

TODAY = date(2026, 7, 20)


class TestFreshnessVerdict(unittest.TestCase):
    def test_daily_within_tolerance_is_fresh(self):
        state, age = freshness_verdict("daily", date(2026, 7, 14), TODAY)
        self.assertEqual(state, "fresh")
        self.assertEqual(age, 6)

    def test_daily_exactly_at_tolerance_is_fresh(self):
        state, age = freshness_verdict("daily", date(2026, 7, 13), TODAY)
        self.assertEqual(state, "fresh")
        self.assertEqual(age, 7)

    def test_daily_past_tolerance_is_flagged(self):
        state, age = freshness_verdict("daily", date(2026, 7, 12), TODAY)
        self.assertEqual(state, "flagged")
        self.assertEqual(age, 8)

    def test_wti_override_keeps_eight_days_fresh(self):
        # 8 days would be flagged under the 7-day daily default; wti_px
        # publishes on a structurally longer lag and gets 10.
        state, age = freshness_verdict(
            "daily", date(2026, 7, 12), TODAY,
            override_days=FIELD_TOLERANCE_OVERRIDE["wti_px"])
        self.assertEqual(state, "fresh")
        self.assertEqual(age, 8)

    def test_wti_override_still_flags_at_eleven_days(self):
        state, age = freshness_verdict(
            "daily", date(2026, 7, 9), TODAY,
            override_days=FIELD_TOLERANCE_OVERRIDE["wti_px"])
        self.assertEqual(state, "flagged")
        self.assertEqual(age, 11)

    def test_monthly_within_tolerance_is_fresh(self):
        state, age = freshness_verdict("monthly", date(2026, 6, 6), TODAY)
        self.assertEqual(state, "fresh")
        self.assertEqual(age, 44)

    def test_monthly_past_tolerance_is_flagged(self):
        state, age = freshness_verdict("monthly", date(2026, 6, 4), TODAY)
        self.assertEqual(state, "flagged")
        self.assertEqual(age, 46)

    def test_real_world_cpi_is_fresh_despite_old_reference_period(self):
        # June CPI references 2026-06-01 (49 days old) but published
        # 2026-07-14 (6 days old). Judged on publication it is healthy.
        state, age = freshness_verdict("monthly", date(2026, 7, 14), TODAY)
        self.assertEqual(state, "fresh")
        self.assertEqual(age, 6)

    def test_fomc_cadence_is_unknown(self):
        state, age = freshness_verdict("fomc", date(2026, 7, 14), TODAY)
        self.assertEqual(state, "unknown")
        self.assertIsNone(age)

    def test_missing_published_date_is_unknown(self):
        state, age = freshness_verdict("daily", None, TODAY)
        self.assertEqual(state, "unknown")
        self.assertIsNone(age)

    def test_unrecognised_cadence_is_unknown(self):
        state, age = freshness_verdict("hourly", date(2026, 7, 19), TODAY)
        self.assertEqual(state, "unknown")
        self.assertIsNone(age)

    def test_tolerance_table_matches_spec(self):
        self.assertEqual(CADENCE_TOLERANCE_DAYS["daily"], 7)
        self.assertEqual(CADENCE_TOLERANCE_DAYS["monthly"], 45)
        self.assertIsNone(CADENCE_TOLERANCE_DAYS["fomc"])
        self.assertEqual(FIELD_TOLERANCE_OVERRIDE["wti_px"], 10)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
cd ~/claude-projects/claudekit && \
python3 -m unittest discover -s bullion-live-map/tests -v
```

Expected: `ImportError: cannot import name 'freshness_verdict'`

- [ ] **Step 3: Write the implementation**

In `bullion-live-map/fetch_bullion_data.py`, after the `YAHOO_SYMBOLS` block (currently ending line 43), add:

```python
# Cadence tolerances, in days, applied to a field's PUBLICATION date — never
# its reference date. June CPI references 2026-06-01 but publishes 2026-07-14;
# judged on reference date it looks broken, judged on publication it is on
# time. Calibrated 2026-07-20 against observed publication lags: daily FRED
# series ran 3-4 days, wti_px 5, CPI 6, PAYEMS 18.
CADENCE_TOLERANCE_DAYS = {
    "daily":   7,    # observed 3-4d; absorbs a three-day weekend plus a holiday
    "monthly": 45,   # observed 6d and 18d; silent for 45d means genuinely broken
    "fomc":    None, # simulated, never judged
}

# wti_px publishes on a structurally longer lag than the other dailies — it sat
# at 5 days while perfectly healthy, so the 7-day default would have produced a
# false alarm immediately.
FIELD_TOLERANCE_OVERRIDE = {
    "wti_px": 10,
}


def freshness_verdict(cadence, published, today, override_days=None):
    """Decide whether a field's latest value is fresh, judged on publication.

    Returns (state, age_days) where state is 'fresh', 'flagged' or 'unknown'.
    'unknown' means the question does not apply (simulated data) or cannot be
    answered (no publication date, unrecognised cadence) — callers must render
    nothing rather than guess.
    """
    if published is None or cadence == "fomc":
        return ("unknown", None)
    tolerance = override_days if override_days is not None else CADENCE_TOLERANCE_DAYS.get(cadence)
    if tolerance is None:
        return ("unknown", None)
    age_days = (today - published).days
    return ("flagged" if age_days > tolerance else "fresh", age_days)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
cd ~/claude-projects/claudekit && \
python3 -m unittest discover -s bullion-live-map/tests -v
```

Expected: `Ran 12 tests` and `OK`.

- [ ] **Step 5: Commit**

```bash
cd ~/claude-projects/claudekit && \
git add bullion-live-map/fetch_bullion_data.py bullion-live-map/tests/test_fetch_bullion_data.py && \
git commit -m "Add freshness verdict judged on publication date

Tolerances calibrated against measured FRED publication lags. wti_px
gets a 10-day override because it publishes on a longer lag than the
other daily series and would false-alarm under the 7-day default."
```

---

### Task 3: Capture publication dates from FRED

FRED exposes publication dates via `realtime_start` when realtime parameters are supplied. This changes `fetch_fred_series`'s return shape.

**Files:**
- Modify: `bullion-live-map/fetch_bullion_data.py:77-112` (`fetch_fred_series`) and `:115-149` (`fetch_yahoo_symbol`)
- Modify: `bullion-live-map/tests/test_fetch_bullion_data.py`

**Interfaces:**
- Consumes: `freshness_verdict` from Task 2
- Produces: both fetchers return `(latest_value, ref_date, published, history)` — `ref_date` and `published` are `str` in `YYYY-MM-DD` form or `None`. Consumed by Task 4.

- [ ] **Step 1: Write the failing test**

Append to `bullion-live-map/tests/test_fetch_bullion_data.py`, before the `if __name__` block:

```python
from fetch_bullion_data import parse_fred_observations, parse_yahoo_chart


class TestParseFredObservations(unittest.TestCase):
    PAYLOAD = {
        "observations": [
            {"realtime_start": "2026-05-12", "realtime_end": "9999-12-31",
             "date": "2026-04-01", "value": "335.423"},
            {"realtime_start": "2026-06-10", "realtime_end": "9999-12-31",
             "date": "2026-05-01", "value": "336.121"},
            {"realtime_start": "2026-07-14", "realtime_end": "9999-12-31",
             "date": "2026-06-01", "value": "336.065"},
        ]
    }

    def test_returns_latest_value_reference_and_publication_dates(self):
        value, ref, pub, hist = parse_fred_observations(self.PAYLOAD, decimals=1)
        self.assertEqual(value, 336.1)
        self.assertEqual(ref, "2026-06-01")
        self.assertEqual(pub, "2026-07-14")

    def test_builds_full_history_keyed_by_reference_date(self):
        _, _, _, hist = parse_fred_observations(self.PAYLOAD, decimals=1)
        self.assertEqual(len(hist), 3)
        self.assertEqual(hist["2026-04-01"], 335.4)

    def test_skips_missing_value_sentinel(self):
        payload = {"observations": [
            {"realtime_start": "2026-07-16", "date": "2026-07-15", "value": "."},
            {"realtime_start": "2026-07-17", "date": "2026-07-16", "value": "4.21"},
        ]}
        value, ref, pub, hist = parse_fred_observations(payload, decimals=2)
        self.assertEqual(value, 4.21)
        self.assertEqual(ref, "2026-07-16")
        self.assertEqual(len(hist), 1)

    def test_empty_payload_returns_all_none(self):
        value, ref, pub, hist = parse_fred_observations({"observations": []}, decimals=2)
        self.assertIsNone(value)
        self.assertIsNone(ref)
        self.assertIsNone(pub)
        self.assertEqual(hist, {})

    def test_missing_realtime_start_yields_none_publication(self):
        payload = {"observations": [
            {"date": "2026-07-16", "value": "4.21"},
        ]}
        value, ref, pub, hist = parse_fred_observations(payload, decimals=2)
        self.assertEqual(value, 4.21)
        self.assertEqual(ref, "2026-07-16")
        self.assertIsNone(pub)


class TestParseYahooChart(unittest.TestCase):
    PAYLOAD = {
        "chart": {"result": [{
            "timestamp": [1784332800, 1784419200],
            "indicators": {"quote": [{"close": [4001.5, 4018.84]}]},
            "meta": {"regularMarketPrice": 4018.84},
        }]}
    }

    def test_reference_and_publication_dates_are_equal(self):
        value, ref, pub, hist = parse_yahoo_chart(self.PAYLOAD, decimals=2)
        self.assertEqual(value, 4018.84)
        self.assertEqual(ref, pub,
                         "a daily close is both the reference period and the "
                         "moment it exists")

    def test_unexpected_shape_returns_all_none(self):
        value, ref, pub, hist = parse_yahoo_chart({"chart": {"result": []}}, decimals=2)
        self.assertIsNone(value)
        self.assertIsNone(ref)
        self.assertIsNone(pub)
        self.assertEqual(hist, {})
```

- [ ] **Step 2: Run to verify it fails**

Run:

```bash
cd ~/claude-projects/claudekit && \
python3 -m unittest discover -s bullion-live-map/tests -v
```

Expected: `ImportError: cannot import name 'parse_fred_observations'`

- [ ] **Step 3: Extract the parsers as pure functions**

Replace the body of `fetch_fred_series` (lines 77-112) with a thin network wrapper plus a pure parser:

```python
def parse_fred_observations(data, decimals):
    """Pure parse of a FRED observations payload.

    Returns (latest_value, ref_date, published, history). `published` comes
    from the observation's realtime_start, which is the date the reading
    became available — this is what freshness is judged on.
    """
    history = {}
    published_by_ref = {}
    for obs in data.get("observations", []):
        val = obs.get("value")
        if val is None or val == ".":
            continue
        try:
            history[obs["date"]] = round(float(val), decimals)
        except (ValueError, KeyError):
            continue
        published_by_ref[obs["date"]] = obs.get("realtime_start")

    if not history:
        return (None, None, None, {})
    latest_ref = max(history)
    return (history[latest_ref], latest_ref, published_by_ref.get(latest_ref), history)


def fetch_fred_series(series_id, key, units, decimals, start, end):
    """Network wrapper around parse_fred_observations."""
    params = {
        "series_id": series_id,
        "api_key": key,
        "file_type": "json",
        "sort_order": "asc",
        "observation_start": start,
        "observation_end": end,
        # realtime_end far in the future makes FRED return each observation's
        # realtime_start, i.e. its publication date.
        "realtime_start": start,
        "realtime_end": "9999-12-31",
    }
    if units:
        params["units"] = units
    url = "https://api.stlouisfed.org/fred/series/observations?" + "&".join(
        f"{k}={urllib.request.quote(str(v))}" for k, v in params.items()
    )
    try:
        data = http_get_json(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  FRED {series_id}: fetch failed ({e})", file=sys.stderr)
        return (None, None, None, {})

    value, ref, pub, hist = parse_fred_observations(data, decimals)
    if value is None:
        print(f"  FRED {series_id}: no usable observations in range", file=sys.stderr)
    return (value, ref, pub, hist)
```

Then replace `fetch_yahoo_symbol` (lines 115-149) similarly:

```python
def parse_yahoo_chart(data, decimals):
    """Pure parse of a Yahoo chart payload.

    Returns (latest_value, ref_date, published, history). For a daily close the
    reference date and publication date are the same day — the close IS the
    moment the number exists.
    """
    try:
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
        latest = result["meta"].get("regularMarketPrice")
    except (KeyError, IndexError, TypeError):
        return (None, None, None, {})

    history = {}
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        history[date_str] = round(float(close), decimals)

    if not history:
        return (None, None, None, {})
    latest_ref = max(history)
    latest = round(float(latest), decimals) if latest is not None else history[latest_ref]
    return (latest, latest_ref, latest_ref, history)


def fetch_yahoo_symbol(symbol, decimals, range_="1y"):
    """Network wrapper around parse_yahoo_chart."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(symbol)}"
           f"?range={range_}&interval=1d")
    try:
        data = http_get_json(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  Yahoo {symbol}: fetch failed ({e})", file=sys.stderr)
        return (None, None, None, {})

    value, ref, pub, hist = parse_yahoo_chart(data, decimals)
    if value is None:
        print(f"  Yahoo {symbol}: unexpected response shape or no usable data", file=sys.stderr)
    return (value, ref, pub, hist)
```

- [ ] **Step 4: Update `main()` for the new return shape**

In `main()`, replace the two fetch loops (currently lines 161-173) with:

```python
    for series_id, (field, units, decimals) in FRED_SERIES.items():
        value, ref, pub, hist = fetch_fred_series(series_id, key, units, decimals, start, end)
        if value is not None:
            latest_out[field] = {"value": value, "ref_date": ref, "published": pub}
        for date_str, val in hist.items():
            history_by_date.setdefault(date_str, {})[field] = val

    for symbol, (field, decimals) in YAHOO_SYMBOLS.items():
        value, ref, pub, hist = fetch_yahoo_symbol(symbol, decimals)
        if value is not None:
            latest_out[field] = {"value": value, "ref_date": ref, "published": pub}
        for date_str, val in hist.items():
            history_by_date.setdefault(date_str, {})[field] = val
```

- [ ] **Step 5: Run the tests to verify they pass**

Run:

```bash
cd ~/claude-projects/claudekit && \
python3 -m unittest discover -s bullion-live-map/tests -v
```

Expected: `Ran 19 tests` and `OK`.

- [ ] **Step 6: Run the fetcher against the live API**

Run:

```bash
cd ~/claude-projects/claudekit/bullion-live-map && python3 fetch_bullion_data.py
```

Expected: `Wrote .../data.json with ~366 dated entries.` and no tracebacks. The file's shape has not changed yet — that is Task 4.

- [ ] **Step 7: Commit**

```bash
cd ~/claude-projects/claudekit && \
git add bullion-live-map/fetch_bullion_data.py bullion-live-map/tests/test_fetch_bullion_data.py && \
git commit -m "Capture FRED publication dates and extract pure parsers

FRED returns each observation's realtime_start (its publication date)
when realtime parameters are supplied. Splitting parsing from network
I/O makes both parsers testable without mocking HTTP."
```

---

### Task 4: Write the schema v2 envelope

**Files:**
- Modify: `bullion-live-map/fetch_bullion_data.py` (`main`, and a new `build_envelope`)
- Modify: `bullion-live-map/tests/test_fetch_bullion_data.py`

**Interfaces:**
- Consumes: `freshness_verdict` (Task 2), the `{"value", "ref_date", "published"}` per-field dicts (Task 3)
- Produces: `build_envelope(latest_out, history_by_date, generated_at) -> dict` with keys `schema`, `generated_at`, `fields`, `history`. Consumed by Task 5.

- [ ] **Step 1: Write the failing test**

Append to `bullion-live-map/tests/test_fetch_bullion_data.py`, before the `if __name__` block:

```python
from fetch_bullion_data import build_envelope, FIELD_META


class TestBuildEnvelope(unittest.TestCase):
    LATEST = {
        "cpi_yoy": {"value": 2.6, "ref_date": "2026-06-01", "published": "2026-07-14"},
        "gold_px": {"value": 4018.8, "ref_date": "2026-07-17", "published": "2026-07-17"},
    }
    HISTORY = {
        "2026-07-17": {"gold_px": 4018.8},
        "2026-06-01": {"cpi_yoy": 2.6},
    }

    def build(self):
        return build_envelope(self.LATEST, self.HISTORY, "2026-07-20T10:07:14Z")

    def test_declares_schema_two(self):
        self.assertEqual(self.build()["schema"], 2)

    def test_history_passes_through_unchanged(self):
        # The date picker reads this block; its shape must not drift.
        self.assertEqual(self.build()["history"], self.HISTORY)

    def test_field_carries_full_provenance(self):
        f = self.build()["fields"]["cpi_yoy"]
        self.assertEqual(f["class"], "measured")
        self.assertEqual(f["cadence"], "monthly")
        self.assertEqual(f["source"], "FRED CPILFESL")
        self.assertEqual(f["ref_date"], "2026-06-01")
        self.assertEqual(f["published"], "2026-07-14")
        self.assertEqual(f["value"], 2.6)

    def test_yahoo_field_is_daily_and_measured(self):
        f = self.build()["fields"]["gold_px"]
        self.assertEqual(f["cadence"], "daily")
        self.assertEqual(f["source"], "Yahoo GC=F")

    def test_omits_fields_that_failed_to_fetch(self):
        env = build_envelope({"gold_px": self.LATEST["gold_px"]}, self.HISTORY,
                             "2026-07-20T10:07:14Z")
        self.assertIn("gold_px", env["fields"])
        self.assertNotIn("cpi_yoy", env["fields"])

    def test_every_known_field_has_metadata(self):
        # A field fetched but absent from FIELD_META would ship with no
        # provenance, which is the bug this whole change exists to prevent.
        expected = {"us2y", "us10y", "vix", "ffr", "wti_px", "cpi_yoy",
                    "nfp_mom", "gold_px", "dxy", "spx"}
        self.assertEqual(set(FIELD_META), expected)
        for name, meta in FIELD_META.items():
            self.assertIn(meta["cadence"], {"daily", "monthly", "fomc"})
            self.assertTrue(meta["source"])
```

- [ ] **Step 2: Run to verify it fails**

Run:

```bash
cd ~/claude-projects/claudekit && \
python3 -m unittest discover -s bullion-live-map/tests -v
```

Expected: `ImportError: cannot import name 'build_envelope'`

- [ ] **Step 3: Write the implementation**

In `bullion-live-map/fetch_bullion_data.py`, after `FIELD_TOLERANCE_OVERRIDE`, add:

```python
SCHEMA_VERSION = 2

# Provenance metadata per field. Every field written to data.json must appear
# here or it ships without provenance — which is the exact defect this schema
# exists to remove, so build_envelope raises rather than emitting a bare value.
FIELD_META = {
    "us2y":    {"class": "measured", "cadence": "daily",   "source": "FRED DGS2"},
    "us10y":   {"class": "measured", "cadence": "daily",   "source": "FRED DGS10"},
    "vix":     {"class": "measured", "cadence": "daily",   "source": "FRED VIXCLS"},
    "ffr":     {"class": "measured", "cadence": "daily",   "source": "FRED DFF"},
    "wti_px":  {"class": "measured", "cadence": "daily",   "source": "FRED DCOILWTICO"},
    "cpi_yoy": {"class": "measured", "cadence": "monthly", "source": "FRED CPILFESL"},
    "nfp_mom": {"class": "measured", "cadence": "monthly", "source": "FRED PAYEMS"},
    "gold_px": {"class": "measured", "cadence": "daily",   "source": "Yahoo GC=F"},
    "dxy":     {"class": "measured", "cadence": "daily",   "source": "Yahoo DX-Y.NYB"},
    "spx":     {"class": "measured", "cadence": "daily",   "source": "Yahoo ^GSPC"},
}


def build_envelope(latest_out, history_by_date, generated_at):
    """Assemble the schema v2 data.json envelope.

    `history` passes through untouched — the map's date picker reads it and its
    shape must not drift.
    """
    fields = {}
    for name, rec in latest_out.items():
        meta = FIELD_META.get(name)
        if meta is None:
            raise KeyError(
                f"field {name!r} has no FIELD_META entry; add one rather than "
                f"shipping a value with no provenance")
        fields[name] = {
            "class":     meta["class"],
            "cadence":   meta["cadence"],
            "source":    meta["source"],
            "ref_date":  rec["ref_date"],
            "published": rec["published"],
            "value":     rec["value"],
        }
    return {
        "schema": SCHEMA_VERSION,
        "generated_at": generated_at,
        "fields": fields,
        "history": history_by_date,
    }
```

- [ ] **Step 4: Wire it into `main()` and log publication ages**

Replace the write block and summary in `main()` (currently lines 179-192) with:

```python
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    envelope = build_envelope(latest_out, history_by_date, generated_at)

    with open(DATA_OUT_PATH, "w") as f:
        json.dump(envelope, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Wrote {DATA_OUT_PATH} (schema {SCHEMA_VERSION}) with "
          f"{len(history_by_date)} dated entries and {len(envelope['fields'])} fields.")

    # Log every field's publication age so the tolerances above can be revised
    # against observed behaviour instead of re-guessed.
    today = datetime.now(timezone.utc).date()
    print("\nPublication ages (freshness is judged on these, not ref_date):")
    for name in sorted(envelope["fields"]):
        fld = envelope["fields"][name]
        pub = fld["published"]
        pub_date = datetime.strptime(pub, "%Y-%m-%d").date() if pub else None
        state, age = freshness_verdict(
            fld["cadence"], pub_date, today,
            override_days=FIELD_TOLERANCE_OVERRIDE.get(name))
        marker = "  FLAGGED" if state == "flagged" else ""
        age_str = f"{age}d" if age is not None else "n/a"
        print(f"  {name:10s} ref={fld['ref_date']} pub={pub} age={age_str:>5s} {state}{marker}")

    missing = [f for f in FIELD_META if f not in envelope["fields"]]
    if missing:
        print(f"\nFailed to fetch (map falls back to simulated baseline): {', '.join(missing)}")
    print()
    print(SOURCE_NOTE)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run:

```bash
cd ~/claude-projects/claudekit && \
python3 -m unittest discover -s bullion-live-map/tests -v
```

Expected: `Ran 25 tests` and `OK`.

- [ ] **Step 6: Generate real v2 data and inspect it**

Run:

```bash
cd ~/claude-projects/claudekit/bullion-live-map && \
python3 fetch_bullion_data.py && \
python3 -c "
import json
d=json.load(open('data.json'))
assert d['schema']==2
assert len(d['fields'])==10, f\"expected 10 fields, got {len(d['fields'])}\"
assert d['history'], 'history must not be empty'
print('schema', d['schema'], '| fields', len(d['fields']), '| history dates', len(d['history']))
print('OK')
"
```

Expected: the publication-age table printed with all fields `fresh`, then `schema 2 | fields 10 | history dates ~366` and `OK`.

If any field reports `FLAGGED` on this first real run, stop and investigate before continuing — either that source is genuinely failing or the tolerance is wrong, and both need resolving before the UI starts showing warnings.

- [ ] **Step 7: Commit**

```bash
cd ~/claude-projects/claudekit && \
git add bullion-live-map/fetch_bullion_data.py bullion-live-map/tests/test_fetch_bullion_data.py bullion-live-map/data.json && \
git commit -m "Write schema v2 envelope with per-field provenance

data.json now carries class, cadence, source, reference date and
publication date per field. The history block passes through unchanged
so the map's date picker is unaffected. Every run logs publication ages
so the freshness tolerances can be calibrated against real behaviour."
```

---

### Task 5: JS freshness verdict and its test harness

Mirrors Task 2's rule in the browser. Lives inline between marker comments; the test extracts it from the shipped file so the two cannot drift.

**Files:**
- Modify: `bullion_mk11_constellation.html` (add function before the `fetch('data.json')` block at line 3246)
- Create: `bullion-live-map/tests/freshness_test.html`

**Interfaces:**
- Consumes: nothing
- Produces: `freshnessVerdict(cadence, published, today, overrideDays) -> {state, ageDays}`, `CADENCE_TOLERANCE_DAYS`, `FIELD_TOLERANCE_OVERRIDE`. Consumed by Tasks 6, 7, 8.

- [ ] **Step 1: Write the failing test runner**

Create `bullion-live-map/tests/freshness_test.html`:

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>freshness tests</title></head>
<body>
<pre id="out">running…</pre>
<script>
const results = [];
function check(name, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  results.push((ok ? 'PASS  ' : 'FAIL  ') + name +
    (ok ? '' : `\n        expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`));
}

fetch('../bullion_mk11_constellation.html')
  .then(r => r.text())
  .then(html => {
    const m = html.match(/FRESHNESS-VERDICT-START([\s\S]*?)FRESHNESS-VERDICT-END/);
    if (!m) throw new Error('marker comments not found in bullion_mk11_constellation.html');
    // Strip the trailing "// ───" of the opening marker line.
    const src = m[1].replace(/^[^\n]*\n/, '');
    (0, eval)(src + '; window.freshnessVerdict = freshnessVerdict;'
                  + ' window.CADENCE_TOLERANCE_DAYS = CADENCE_TOLERANCE_DAYS;'
                  + ' window.FIELD_TOLERANCE_OVERRIDE = FIELD_TOLERANCE_OVERRIDE;');

    const TODAY = '2026-07-20';
    const WTI = window.FIELD_TOLERANCE_OVERRIDE.wti_px;

    check('daily within tolerance is fresh',
      freshnessVerdict('daily', '2026-07-14', TODAY), {state:'fresh', ageDays:6});
    check('daily exactly at tolerance is fresh',
      freshnessVerdict('daily', '2026-07-13', TODAY), {state:'fresh', ageDays:7});
    check('daily past tolerance is flagged',
      freshnessVerdict('daily', '2026-07-12', TODAY), {state:'flagged', ageDays:8});
    check('wti override keeps 8 days fresh',
      freshnessVerdict('daily', '2026-07-12', TODAY, WTI), {state:'fresh', ageDays:8});
    check('wti override still flags at 11 days',
      freshnessVerdict('daily', '2026-07-09', TODAY, WTI), {state:'flagged', ageDays:11});
    check('monthly within tolerance is fresh',
      freshnessVerdict('monthly', '2026-06-06', TODAY), {state:'fresh', ageDays:44});
    check('monthly past tolerance is flagged',
      freshnessVerdict('monthly', '2026-06-04', TODAY), {state:'flagged', ageDays:46});
    check('real-world CPI is fresh despite old reference period',
      freshnessVerdict('monthly', '2026-07-14', TODAY), {state:'fresh', ageDays:6});
    check('fomc cadence is unknown',
      freshnessVerdict('fomc', '2026-07-14', TODAY), {state:'unknown', ageDays:null});
    check('missing published date is unknown',
      freshnessVerdict('daily', null, TODAY), {state:'unknown', ageDays:null});
    check('unrecognised cadence is unknown',
      freshnessVerdict('hourly', '2026-07-19', TODAY), {state:'unknown', ageDays:null});
    check('tolerance table matches spec',
      [window.CADENCE_TOLERANCE_DAYS.daily, window.CADENCE_TOLERANCE_DAYS.monthly,
       window.CADENCE_TOLERANCE_DAYS.fomc, WTI], [7, 45, null, 10]);
  })
  .catch(e => results.push('FAIL  harness error: ' + e.message))
  .finally(() => {
    const failed = results.filter(r => r.startsWith('FAIL')).length;
    document.getElementById('out').textContent =
      results.join('\n') + `\n\n${results.length - failed}/${results.length} passed` +
      (failed ? '\nRESULT: FAIL' : '\nRESULT: PASS');
  });
</script>
</body>
</html>
```

- [ ] **Step 2: Run it to verify it fails**

The runner `fetch`es a sibling file, which `file://` blocks, so serve the directory:

```bash
cd ~/claude-projects/claudekit/bullion-live-map && \
python3 -m http.server 8899 >/dev/null 2>&1 &
sleep 1 && \
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --dump-dom --virtual-time-budget=5000 \
  http://localhost:8899/tests/freshness_test.html 2>/dev/null \
  | python3 -c "
import sys,re,html
dom=sys.stdin.read()
m=re.search(r'<pre id=\"out\">(.*?)</pre>', dom, re.S)
print(html.unescape(m.group(1)) if m else 'NO OUTPUT FOUND')
"
kill %1
```

Expected: `FAIL  harness error: marker comments not found in bullion_mk11_constellation.html`

- [ ] **Step 3: Add the function to the map**

In `bullion_mk11_constellation.html`, immediately before the `fetch('data.json')` comment block at line 3244, insert:

```js
// ─── FRESHNESS-VERDICT-START ────────────────────────────────────────────────
// Mirrors freshness_verdict() in fetch_bullion_data.py. Judged on a field's
// PUBLICATION date, never its reference date: June CPI references 2026-06-01
// but publishes 2026-07-14, so by reference it looks broken and by publication
// it is on time. tests/freshness_test.html extracts this block by its marker
// comments and asserts the same cases as the Python suite — renaming or
// removing the markers breaks that test, which is intended.
const CADENCE_TOLERANCE_DAYS = { daily: 7, monthly: 45, fomc: null };
const FIELD_TOLERANCE_OVERRIDE = { wti_px: 10 };

function freshnessVerdict(cadence, published, today, overrideDays) {
  if (!published || cadence === 'fomc') return { state: 'unknown', ageDays: null };
  const tolerance = (overrideDays != null) ? overrideDays : CADENCE_TOLERANCE_DAYS[cadence];
  if (tolerance == null) return { state: 'unknown', ageDays: null };
  // Parse as UTC midnight so DST never shifts a day boundary.
  const ms = Date.parse(today + 'T00:00:00Z') - Date.parse(published + 'T00:00:00Z');
  if (Number.isNaN(ms)) return { state: 'unknown', ageDays: null };
  const ageDays = Math.round(ms / 86400000);
  return { state: ageDays > tolerance ? 'flagged' : 'fresh', ageDays: ageDays };
}
// ─── FRESHNESS-VERDICT-END ──────────────────────────────────────────────────
```

- [ ] **Step 4: Run the test to verify it passes**

Run the same command as Step 2.

Expected: 14 `PASS` lines, then `14/14 passed` and `RESULT: PASS`.

- [ ] **Step 5: Confirm the map still loads**

```bash
open -a "Google Chrome" ~/claude-projects/claudekit/bullion-live-map/bullion_mk11_constellation.html
```

Confirm the constellation renders and the console shows no errors.

- [ ] **Step 6: Commit**

```bash
cd ~/claude-projects/claudekit && \
git add bullion-live-map/bullion_mk11_constellation.html bullion-live-map/tests/freshness_test.html && \
git commit -m "Mirror the freshness verdict in JS with a Chrome test harness

The map must stay a single self-contained file, so the function lives
inline between marker comments and the test extracts it from the shipped
HTML rather than duplicating it. Runs under headless Chrome since node
is not installed."
```

---

### Task 6: Load schema v2 and branch on version

Completes Tier 1's data path.

**IMPORTANT — existing machinery this task must NOT duplicate.** The map already
renders provenance status in two places, added by an earlier plan:

- `renderLiveProvenance(s)` (line ~2662) writes `#live-provenance`:
  `Live as of {date}: US2Y, Core CPI, … Still simulated: FOMC hike/cut odds.`
  On a failed fetch it already writes `All metrics are simulated — data.json
  not found or failed to load.`
- `renderLiveBadge(s)` (line ~2684) writes a condensed version to `#live-badge`
  in the header.
- `LIVE_FIELD_LABEL` maps field name → display name; `ALWAYS_SIMULATED_LABEL`
  already names FOMC odds as simulated.

**A visible failure state therefore already exists.** Do not add a parallel one.
This task supplies the per-field provenance those functions will consume in
Tasks 7 and 8; it changes no rendering.

**Files:**
- Modify: `bullion_mk11_constellation.html:3246-3283` (the `fetch('data.json')` block)

**Interfaces:**
- Consumes: `freshnessVerdict` (Task 5), the v2 envelope (Task 4)
- Produces: `normaliseEnvelope(raw, todayISO)` and `window.BULLION_PROVENANCE` — `{schema, generatedAt, fields, history, ok, error}` where `fields` maps field name to `{class, cadence, source, refDate, published, value, state, ageDays}`. Consumed by Tasks 7 and 8.
- **Preserves:** `window.BULLION_LIVE_HISTORY` and `window.BULLION_LIVE_DATA` keep their current shapes, including `fetched_at` as a bare `YYYY-MM-DD` string — `renderLiveProvenance` does `new Date(s.fetched_at + 'T00:00')`, which produces an Invalid Date if handed a full ISO timestamp.

- [ ] **Step 1: Write the failing test**

Append to `bullion-live-map/tests/freshness_test.html`, inside the `.then(html => {…})` block after the existing checks:

```js
    // ── normaliseEnvelope: schema branching ──
    const m2 = html.match(/NORMALISE-ENVELOPE-START([\s\S]*?)NORMALISE-ENVELOPE-END/);
    if (!m2) { check('normaliseEnvelope present', false, true); }
    else {
      // The leading '\n' is REQUIRED: the captured source ends inside the closing
      // marker line's '// ───' comment, so appended code without a newline is
      // silently swallowed by it.
      (0, eval)(m2[1].replace(/^[^\n]*\n/, '') + '\n; window.normaliseEnvelope = normaliseEnvelope;');

      const v2 = { schema: 2, generated_at: '2026-07-20T10:07:14Z',
        fields: { cpi_yoy: { class:'measured', cadence:'monthly', source:'FRED CPILFESL',
                             ref_date:'2026-06-01', published:'2026-07-14', value:2.6 } },
        history: { '2026-06-01': { cpi_yoy: 2.6 } } };
      const n2 = normaliseEnvelope(v2, '2026-07-20');
      check('v2 is recognised', n2.schema, 2);
      check('v2 field carries a freshness state', n2.fields.cpi_yoy.state, 'fresh');
      check('v2 field carries an age', n2.fields.cpi_yoy.ageDays, 6);

      const v1 = { '2026-06-01': { cpi_yoy: 2.6 }, '2026-07-17': { gold_px: 4018.8 } };
      const n1 = normaliseEnvelope(v1, '2026-07-20');
      check('v1 is detected', n1.schema, 1);
      check('v1 suppresses freshness rather than guessing',
        n1.fields.gold_px.state, 'unknown');
      check('v1 still exposes values', n1.fields.gold_px.value, 4018.8);
      check('v1 history is reconstructed', Object.keys(n1.history).length, 2);

      const nFail = normaliseEnvelope(null, '2026-07-20');
      check('null envelope reports not-ok', nFail.ok, false);
      check('null envelope has no fields', Object.keys(nFail.fields).length, 0);
    }
```

- [ ] **Step 2: Run to verify it fails**

Run the Step 2 command from Task 5.

Expected: `FAIL  normaliseEnvelope present`, and `RESULT: FAIL`.

- [ ] **Step 3: Write `normaliseEnvelope`**

In `bullion_mk11_constellation.html`, immediately after the `FRESHNESS-VERDICT-END` marker, insert:

```js
// ─── NORMALISE-ENVELOPE-START ───────────────────────────────────────────────
// Turns whatever data.json contained into one shape the rest of the map can
// rely on. GitHub Pages caches aggressively, so a new HTML will meet an old
// data.json and vice versa — hence the schema branch. A v1 file has no
// publication dates, so its freshness is reported 'unknown' and the UI shows
// nothing, rather than inventing dates the file never carried.
function normaliseEnvelope(raw, todayISO) {
  const out = { schema: 0, generatedAt: null, fields: {}, history: {}, ok: false, error: null };

  if (!raw || typeof raw !== 'object') {
    out.error = 'no data';
    return out;
  }

  if (raw.schema === 2) {
    out.schema = 2;
    out.generatedAt = raw.generated_at || null;
    out.history = raw.history || {};
    out.ok = true;
    for (const [name, f] of Object.entries(raw.fields || {})) {
      const verdict = freshnessVerdict(
        f.cadence, f.published, todayISO, FIELD_TOLERANCE_OVERRIDE[name]);
      out.fields[name] = {
        class: f.class, cadence: f.cadence, source: f.source,
        refDate: f.ref_date, published: f.published, value: f.value,
        state: verdict.state, ageDays: verdict.ageDays,
      };
    }
    return out;
  }

  if (raw.schema != null && raw.schema > 2) {
    console.warn('data.json schema', raw.schema, 'is newer than this page understands; reading as v1');
  }

  // v1: a bare {date: {field: value}} map. Reconstruct per-field latest by
  // walking dates ascending, exactly as the pre-provenance loader did.
  out.schema = 1;
  out.history = raw;
  out.ok = true;
  const snapshot = {};
  for (const dt of Object.keys(raw).sort()) {
    const row = raw[dt];
    if (row && typeof row === 'object') {
      for (const [k, v] of Object.entries(row)) snapshot[k] = { value: v, refDate: dt };
    }
  }
  for (const [name, rec] of Object.entries(snapshot)) {
    out.fields[name] = {
      class: 'measured', cadence: 'unknown', source: null,
      refDate: rec.refDate, published: null, value: rec.value,
      state: 'unknown', ageDays: null,
    };
  }
  return out;
}
// ─── NORMALISE-ENVELOPE-END ─────────────────────────────────────────────────
```

- [ ] **Step 4: Rewrite the loader to use it**

Replace the entire `fetch('data.json')` chain (lines 3246-3283) with:

```js
// Live data loads asynchronously after the first paint, so the page is
// usable immediately on the simulated baseline, then upgrades in place.
fetch('data.json')
  .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
  .then(json => {
    const todayISO = new Date().toISOString().slice(0, 10);
    const prov = normaliseEnvelope(json, todayISO);
    window.BULLION_PROVENANCE = prov;
    window.BULLION_LIVE_HISTORY = prov.history;

    // Sources publish on different lags, so no single date has every field.
    // The snapshot takes each field's latest value; provenance now records
    // which date each one actually came from instead of stamping them all
    // with one misleading date.
    const snapshot = {};
    for (const [name, f] of Object.entries(prov.fields)) snapshot[name] = f.value;
    if (Object.keys(snapshot).length) {
      // Must stay a bare YYYY-MM-DD: renderLiveProvenance does
      // `new Date(s.fetched_at + 'T00:00')`, which yields an Invalid Date if
      // handed the full ISO timestamp that generated_at carries.
      snapshot.fetched_at = prov.generatedAt ? prov.generatedAt.slice(0, 10) : null;
      window.BULLION_LIVE_DATA = snapshot;
    }
  })
  .catch(err => {
    console.warn('data.json fetch failed, falling back to simulated baseline:', err);
    window.BULLION_PROVENANCE = {
      schema: 0, generatedAt: null, fields: {}, history: {},
      ok: false, error: err.message,
    };
  })
  .finally(() => {
    setupHistoryDatePicker();
    // refreshDriverBases() moves each d.base to the live value, so the manual
    // driver rows (first built with simulated bases, before this fetch
    // resolved) must be rebuilt or their sliders and baseline labels would
    // disagree with the live model.
    refreshDriverBases();
    buildManualRows();
    syncManualUI();
    state = buildBaseState();
    updateMetrics();
  });
```

- [ ] **Step 5: Confirm the existing failure state still works**

No new failure UI is added — `renderLiveProvenance` already handles it. This step
verifies the existing behaviour survived the loader rewrite.

```bash
cd ~/claude-projects/claudekit/bullion-live-map && \
python3 -m http.server 8899 >/dev/null 2>&1 &
sleep 1 && mv data.json /tmp/data-hidden.json && \
open -a "Google Chrome" http://localhost:8899/bullion_mk11_constellation.html
```

Confirm `#live-provenance` reads *"All metrics are simulated — data.json not
found or failed to load. Run fetch_bullion_data.py to pull live data."* and the
header badge shows its simulated state. Then restore:
`mv /tmp/data-hidden.json data.json`

- [ ] **Step 6: Run the tests to verify they pass**

Run the Step 2 command from Task 5.

Expected: 23 `PASS` lines, `23/23 passed`, `RESULT: PASS`.

- [ ] **Step 7: Verify all three fixtures in the browser**

Fixture 1 — v2 data (the real `data.json` from Task 4):

```bash
cd ~/claude-projects/claudekit/bullion-live-map && \
python3 -m http.server 8899 >/dev/null 2>&1 &
sleep 1 && open -a "Google Chrome" http://localhost:8899/bullion_mk11_constellation.html
```

In the console, run `BULLION_PROVENANCE.schema` — expect `2`. Run
`Object.values(BULLION_PROVENANCE.fields).map(f => f.state)` — expect all `"fresh"`.
Confirm the Live Data button still reads "Live Data".

Fixture 2 — v1 data:

```bash
cd ~/claude-projects/claudekit/bullion-live-map && \
# NB: locate the last v1 commit by content, not by a fixed HEAD~N offset —
# review-fix commits shift history. `aad4067^` was correct as of 2026-07-21.
git show "$(git log --format=%H -- bullion-live-map/data.json | sed -n 2p)":bullion-live-map/data.json > /tmp/v1-data.json && \
python3 -c "import json,sys; d=json.load(open('/tmp/v1-data.json')); assert 'schema' not in d, 'not a v1 file'; print('confirmed schema v1')" && \
cp data.json /tmp/v2-data.json && cp /tmp/v1-data.json data.json && \
open -a "Google Chrome" http://localhost:8899/bullion_mk11_constellation.html
```

Confirm: map renders, `BULLION_PROVENANCE.schema` is `1`, all field states are
`"unknown"`, no console errors. Then restore: `cp /tmp/v2-data.json data.json`

Fixture 3 — missing data:

```bash
cd ~/claude-projects/claudekit/bullion-live-map && \
mv data.json /tmp/data-hidden.json && \
open -a "Google Chrome" http://localhost:8899/bullion_mk11_constellation.html
```

Confirm `#live-provenance` reads **"All metrics are simulated — data.json not
found or failed to load…"** (the pre-existing failure message, which this task
must not have broken) and `BULLION_PROVENANCE.ok` is `false`. Then restore:
`mv /tmp/data-hidden.json data.json` and `kill %1`.

Repeat fixture 1 at the 640px breakpoint using Chrome's device toolbar.

- [ ] **Step 8: Commit**

```bash
cd ~/claude-projects/claudekit && \
git add bullion-live-map/bullion_mk11_constellation.html bullion-live-map/tests/freshness_test.html && \
git commit -m "Read schema v2 provenance and make fetch failure visible

Replaces the single misleading fetched_at stamp with per-field
provenance. Old v1 files still load, with freshness suppressed rather
than guessed. A failed fetch now says so on the Live Data button instead
of silently showing simulated numbers as live."
```

---

### Task 7: Metric sub-lines and flagged-field markers

**Files:**
- Modify: `bullion_mk11_constellation.html` (metric rendering in `updateMetrics`, and the CSS block near line 159)

**Interfaces:**
- Consumes: `window.BULLION_PROVENANCE` (Task 6)
- Produces: `provenanceSublineFor(field) -> string | null`, where `field` is one entry from `BULLION_PROVENANCE.fields`. Also `PROV_MON_ABBR` (consumed by Task 8) and CSS classes `.prov-sub`, `.prov-flag`, `.prov-dot`.

- [ ] **Step 1: Write the failing test**

Append to `bullion-live-map/tests/freshness_test.html`, after the Task 6 checks:

```js
    // ── provenanceSubline: what appears under a metric ──
    const m3 = html.match(/PROVENANCE-SUBLINE-START([\s\S]*?)PROVENANCE-SUBLINE-END/);
    if (!m3) { check('provenanceSubline present', false, true); }
    else {
      // PROV_MON_ABBR must reach the global object too: it is declared `const`
      // in this block, and Task 8's strip block references it from a separate
      // eval where block-scoped consts are not visible.
      // The leading '\n' is REQUIRED — see the note in the Task 6 checks.
      (0, eval)(m3[1].replace(/^[^\n]*\n/, '')
        + '\n; window.provenanceSublineFor = provenanceSublineFor;'
        + '  window.PROV_MON_ABBR = PROV_MON_ABBR;'
        + '  window.PROV_MONTHS = PROV_MONTHS;');

      check('fresh daily field shows nothing',
        provenanceSublineFor({class:'measured', cadence:'daily', refDate:'2026-07-17',
                              published:'2026-07-17', state:'fresh', ageDays:0}), null);
      check('monthly field shows period and publication date',
        provenanceSublineFor({class:'measured', cadence:'monthly', refDate:'2026-06-01',
                              published:'2026-07-14', state:'fresh', ageDays:6}),
        'June · published Jul 14 · monthly');
      check('simulated field says so',
        provenanceSublineFor({class:'simulated', cadence:'fomc', refDate:null,
                              published:null, state:'unknown', ageDays:null}),
        'model estimate · not market data');
      check('flagged field explains the fault',
        provenanceSublineFor({class:'measured', cadence:'daily', refDate:'2026-07-08',
                              published:'2026-07-08', state:'flagged', ageDays:12}),
        'Expected daily, last published 12 days ago — the source may be failing.');
      check('unknown cadence shows nothing',
        provenanceSublineFor({class:'measured', cadence:'unknown', refDate:'2026-07-17',
                              published:null, state:'unknown', ageDays:null}), null);
    }
```

- [ ] **Step 2: Run to verify it fails**

Run the Step 2 command from Task 5. Expected: `FAIL  provenanceSubline present`.

- [ ] **Step 3: Write the implementation**

After the `NORMALISE-ENVELOPE-END` marker, insert:

```js
// ─── PROVENANCE-SUBLINE-START ───────────────────────────────────────────────
// What appears under a metric's value. Fresh daily fields return null and show
// nothing: appending "as of today" to eight daily fields would be noise that
// trains the reader to ignore the line, defeating it on the one field where it
// matters.
const PROV_MONTHS = ['January','February','March','April','May','June','July',
                     'August','September','October','November','December'];
const PROV_MON_ABBR = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function provenanceSublineFor(field) {
  if (!field) return null;
  if (field.class === 'simulated') return 'model estimate · not market data';
  if (field.state === 'flagged') {
    return 'Expected ' + field.cadence + ', last published ' + field.ageDays
         + ' days ago — the source may be failing.';
  }
  if (field.state === 'unknown') return null;
  if (field.cadence === 'daily') return null;   // fresh and daily: silence
  if (field.cadence === 'monthly') {
    const ref = field.refDate ? new Date(field.refDate + 'T00:00:00Z') : null;
    const pub = field.published ? new Date(field.published + 'T00:00:00Z') : null;
    if (!ref || !pub) return null;
    return PROV_MONTHS[ref.getUTCMonth()] + ' · published '
         + PROV_MON_ABBR[pub.getUTCMonth()] + ' ' + pub.getUTCDate() + ' · monthly';
  }
  return null;
}
// ─── PROVENANCE-SUBLINE-END ─────────────────────────────────────────────────
```

- [ ] **Step 4: Add the CSS**

In the `<style>` block, after the `.mg-read` rule, add:

```css
  .prov-sub { display:block; font-size:9.5px; color:var(--text-dim);
              line-height:1.4; margin-top:2px; letter-spacing:0.02em; }
  .prov-flag { color:var(--amber); }
  .prov-dot  { display:inline-block; width:6px; height:6px; border-radius:50%;
               background:var(--amber); margin-left:5px; vertical-align:middle; }
```

Amber rather than red deliberately: this warns about the data pipeline, and red on a finance dashboard reads as "markets are falling".

- [ ] **Step 5: Render the sub-line in the metrics panel**

The metrics grid is **static markup with fixed ids**, not constructed rows. Each
cell (lines 451-459) has this shape:

```html
<div class="metric-cell">
  <div class="metric-label">Core CPI</div>
  <div class="metric-val" id="m-cpi">&mdash;</div>
  <div class="metric-sub">YoY %</div>
</div>
```

Add an empty provenance line to each of the nine cells, after its
`.metric-sub` div. Use the id pattern `p-<same suffix as m->`:

```html
<div class="prov-sub" id="p-cpi"></div>
```

The nine ids: `p-us2y`, `p-us10y`, `p-spread`, `p-vix`, `p-spx`, `p-cpi`,
`p-gold`, `p-dxy`, `p-wti`.

Then add the id → field mapping and the render pass. Insert next to
`LIVE_FIELD_LABEL` (line ~2649):

```js
// Metric cell id suffix -> data.json field name. `spread` is absent because it
// is computed from us10y and us2y rather than fetched — it is class 'derived'
// and carries no publication date of its own. `ffr` and `nfp_mom` are fetched
// but have no cell in the metrics grid.
const METRIC_CELL_FIELD = {
  'us2y': 'us2y', 'us10y': 'us10y', 'vix': 'vix', 'spx': 'spx',
  'cpi': 'cpi_yoy', 'gold': 'gold_px', 'dxy': 'dxy', 'wti': 'wti_px',
};

function renderMetricProvenance() {
  const prov = window.BULLION_PROVENANCE;
  for (const [suffix, fieldName] of Object.entries(METRIC_CELL_FIELD)) {
    const el = document.getElementById('p-' + suffix);
    if (!el) continue;
    const field = (prov && prov.fields) ? prov.fields[fieldName] : null;
    const text = provenanceSublineFor(field);
    el.textContent = text || '';
    el.className = 'prov-sub' + (field && field.state === 'flagged' ? ' prov-flag' : '');
  }
  // The spread is derived, so it states that rather than a publication date.
  const spreadEl = document.getElementById('p-spread');
  if (spreadEl) {
    spreadEl.textContent = (prov && prov.schema === 2) ? 'derived from 10Y and 2Y' : '';
    spreadEl.className = 'prov-sub';
  }
}
```

Call `renderMetricProvenance()` from `updateMetrics()`, immediately after the
existing `renderLiveProvenance(s);` call (line ~2636).

- [ ] **Step 6: Run the tests to verify they pass**

Run the Step 2 command from Task 5. Expected: `34/34 passed`, `RESULT: PASS`.

- [ ] **Step 7: Verify in the browser**

Serve and open as in Task 6 Step 7. Confirm:
- Core CPI shows `June · published Jul 14 · monthly`
- Gold, DXY, SPX, US2Y, US10Y, VIX show **no** sub-line
- No layout shift or text clipping in the metrics panel, at desktop and at 640px

To confirm the flagged path renders, temporarily edit `data.json` to set
`fields.vix.published` to a date 20 days old, reload, confirm the amber dot and
warning text appear, then restore the file with `git checkout bullion-live-map/data.json`.

- [ ] **Step 8: Commit**

```bash
cd ~/claude-projects/claudekit && \
git add bullion-live-map/bullion_mk11_constellation.html bullion-live-map/tests/freshness_test.html && \
git commit -m "Show reference period and publication date on lagging metrics

Core CPI now states the month it describes and the date it was
published, so a seven-week-old reference period reads as the normal
monthly cadence it is rather than as stale data. Fresh daily fields stay
silent. Fields breaching their own tolerance get an amber marker."
```

---

### Task 8: Per-field provenance summary and simulated-value markers

Completes Tier 2. Lands last and alone because it touches `STATS_VARS`, which
feeds the scenario stats panel.

**IMPORTANT — extend, do not duplicate.** `renderLiveProvenance()` (line ~2662)
and `renderLiveBadge()` (line ~2684) already exist and already say which fields
are live and that FOMC odds are simulated. This task replaces their single
`Live as of {fetched_at}` date — the misleading stamp this whole plan exists to
remove — with per-field freshness, and marks FOMC where its number is displayed
rather than only in the status line. Do not add a new strip element.

**Files:**
- Modify: `bullion_mk11_constellation.html` — `renderLiveProvenance` (~2662), `STATS_VARS` (~2570), `renderStats` (~2582), CSS

**Interfaces:**
- Consumes: `window.BULLION_PROVENANCE` (Task 6), `provenanceSublineFor` and `PROV_MON_ABBR` (Task 7)
- Produces: `provenanceSummaryText(prov)` — one sentence describing field freshness. No other exports; UI only.

- [ ] **Step 1: Write the failing test**

Append to `bullion-live-map/tests/freshness_test.html`, after the Task 7 checks:

```js
    // ── provenanceSummaryText ──
    const m4 = html.match(/PROVENANCE-SUMMARY-START([\s\S]*?)PROVENANCE-SUMMARY-END/);
    if (!m4) { check('provenanceSummaryText present', false, true); }
    else {
      // The leading '\n' is REQUIRED — see the note in the Task 6 checks.
      (0, eval)(m4[1].replace(/^[^\n]*\n/, '') + '\n; window.provenanceSummaryText = provenanceSummaryText;');

      check('all fresh states the newest publication date',
        provenanceSummaryText({ok:true, schema:2, fields:{
          a:{class:'measured', state:'fresh', published:'2026-07-17'},
          b:{class:'measured', state:'fresh', published:'2026-07-14'}}}),
        'All 2 measured fields are current — most recent publication Jul 17.');
      check('flagged fields are named',
        provenanceSummaryText({ok:true, schema:2, fields:{
          a:{class:'measured', state:'fresh', published:'2026-07-17'},
          vix:{class:'measured', state:'flagged', published:'2026-07-01', ageDays:19}}}),
        '1 of 2 measured fields may be failing: vix. Most recent publication Jul 17.');
      check('v1 file says freshness is unknown',
        provenanceSummaryText({ok:true, schema:1, fields:{
          a:{class:'measured', state:'unknown', published:null}}}),
        'Publication dates unavailable in this data file — freshness unknown.');
      check('failed load says so',
        provenanceSummaryText({ok:false, fields:{}}),
        'Live data unavailable — every number shown is simulated.');
    }
```

- [ ] **Step 2: Run to verify it fails**

Run the Step 2 command from Task 5. Expected: `FAIL  provenanceSummaryText present`.

- [ ] **Step 3: Write the summary function**

After the `PROVENANCE-SUBLINE-END` marker, insert:

```js
// ─── PROVENANCE-SUMMARY-START ───────────────────────────────────────────────
// One sentence replacing the old `Live as of {fetched_at}` stamp. That stamp
// applied a single date to ten fields published on ten different schedules,
// which is the misrepresentation this plan exists to remove.
function provenanceSummaryText(prov) {
  if (!prov || !prov.ok) return 'Live data unavailable — every number shown is simulated.';
  const entries = Object.entries(prov.fields || {})
                        .filter(([, f]) => f.class === 'measured');
  if (!entries.length) return 'Live data unavailable — every number shown is simulated.';
  if (entries.every(([, f]) => f.state === 'unknown')) {
    return 'Publication dates unavailable in this data file — freshness unknown.';
  }
  const published = entries.map(([, f]) => f.published).filter(Boolean).sort();
  const newest = published.length ? published[published.length - 1] : null;
  const newestTxt = newest
    ? ' Most recent publication ' + PROV_MON_ABBR[Number(newest.slice(5, 7)) - 1]
      + ' ' + Number(newest.slice(8, 10)) + '.'
    : '';
  const flagged = entries.filter(([, f]) => f.state === 'flagged').map(([n]) => n);
  if (flagged.length) {
    return flagged.length + ' of ' + entries.length + ' measured fields may be failing: '
         + flagged.join(', ') + '.' + newestTxt;
  }
  return 'All ' + entries.length + ' measured fields are current — most recent publication '
       + PROV_MON_ABBR[Number(newest.slice(5, 7)) - 1] + ' ' + Number(newest.slice(8, 10)) + '.';
}
// ─── PROVENANCE-SUMMARY-END ─────────────────────────────────────────────────
```

- [ ] **Step 4: Use it in `renderLiveProvenance`**

In `renderLiveProvenance` (line ~2662), replace the final two lines — the ones
building `when` from `s.fetched_at` and assigning `el.textContent` — with:

```js
  const prov = window.BULLION_PROVENANCE;
  el.textContent = `Live: ${liveNames.join(', ')}. Still simulated: ${ALWAYS_SIMULATED_LABEL}. `
                 + provenanceSummaryText(prov);
```

Leave the `selectedHistoryDate` and empty-`liveNames` branches above it
untouched — they already behave correctly and Task 6 verified them.

Delete the now-unused `when` local. `s.fetched_at` stays on the state object
(other code reads it); it simply no longer drives this sentence.

- [ ] **Step 5: Mark FOMC where its number is displayed**

`fomc_prob_hike` appears in `STATS_VARS` (line ~2578) as `FOMC Hike Prob`, which
`renderStats` renders in the scenario stats panel. Add a `sim` flag:

```js
  { key:'fomc_prob_hike', label:'FOMC Hike Prob', unit:'probability', sim:true },
```

In `renderStats`, where the row label is built:

```js
      + '<div class="stat-label">' + d.label + '<small>' + d.unit + '</small></div>'
```

replace with:

```js
      + '<div class="stat-label">' + d.label + (d.sim ? '<span class="sim-mark" title="Model estimate, not market data — FOMC odds have no free live source">~</span>' : '')
      + '<small>' + d.unit + (d.sim ? ' · model estimate' : '') + '</small></div>'
```

**Display only.** Do not change how `fomc_prob_hike` is computed or how it feeds
node colouring — the model is unchanged, only its presentation gains the marker.

- [ ] **Step 6: Add the marker CSS**

After the `.prov-dot` rule:

```css
  .sim-mark { color:var(--amber); font-weight:600; margin-left:3px; cursor:help; }
```

- [ ] **Step 7: Run the tests to verify they pass**

Run the Step 2 command from Task 5. Expected: `38/38 passed`, `RESULT: PASS`.

- [ ] **Step 8: Verify in the browser, including a scenario run**

Serve and open as in Task 6. Confirm:

- `#live-provenance` ends with `All 10 measured fields are current — most recent publication <date>.`
- It no longer contains the words `Live as of`
- **Run the Rate Hike scenario.** Confirm node colours change as before, and the
  stats panel shows `FOMC Hike Prob ~` with `probability · model estimate`
- Click 3-4 nodes; detail panels unaffected
- Repeat at the 640px breakpoint

Then re-run the missing-`data.json` fixture and confirm `#live-provenance` still
shows the pre-existing all-simulated message.

- [ ] **Step 9: Run the full test suite**

```bash
cd ~/claude-projects/claudekit && \
python3 -m unittest discover -s bullion-live-map/tests -v
```

Expected: `Ran 33 tests`, `OK`. Then re-run the Chrome runner: `44/44 passed`.

- [ ] **Step 10: Commit**

```bash
cd ~/claude-projects/claudekit && \
git add bullion-live-map/bullion_mk11_constellation.html bullion-live-map/tests/freshness_test.html && \
git commit -m "Replace the single fetched_at stamp with per-field freshness

The status line said 'Live as of <one date>' for ten fields published on
ten different schedules. It now summarises actual per-field freshness and
names any field breaching its own cadence. FOMC odds gain a marker where
their number is displayed, not only in the status line. Display only --
the values feeding node colouring and scenarios are unchanged."
```


## Done criteria

- `python3 -m unittest discover -s bullion-live-map/tests -v` → 33 tests, OK
- The Chrome runner → `44/44 passed`, `RESULT: PASS`
- All three fixtures verified at desktop and 640px
- Rate Hike scenario still colours nodes correctly after Task 8
- `preview-card.png` is 1200×630 and the eight OG tags are in `<head>`
- NO live code path emits the string `Live as of` — this means BOTH `#live-provenance`
  AND the header badge `#live-badge`. An earlier draft named only the former, which
  left the single-date claim standing in the more visible of the two.
- Branch `bullion-provenance` unpushed and not yet merged to `main`

## Follow-ups (not in this plan)

- **Push.** All commits are local; pushing needs the user's terminal.
- **Validate the preview card** against a real scraper once pushed — paste the URL into WhatsApp and confirm the card renders.
- **Tier 3, the guided tour** — specced only after watching real beginners use this build.
- **Confirm the daily Actions push path.** No `github-actions[bot]` commit exists after `e321844`; still unproven.
- **Revisit tolerances** once a few weeks of publication-age logs exist.
</content>

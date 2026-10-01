# Bullion Mk11 — Provenance & Reach Design

**Date:** 2026-07-20
**Status:** Approved for implementation (Tier 1 + Tier 2)
**Supersedes nothing.** Builds on `2026-07-19-bullion-live-data-pipeline-design.md`.

---

## Goal

Make the Bullion Mk11 constellation map honest about where every number on it
comes from, and make its shared link worth tapping.

Two problems drive this work:

1. **The map misrepresents data freshness.** It assembles a "current
   conditions" snapshot from each field's most recent value, then stamps the
   whole snapshot with a single date (`snapshot.fetched_at`,
   `bullion_mk11_constellation.html:3266`). On 2026-07-20 that snapshot mixes
   gold from Jul 17 with Core CPI referencing June — under a button reading
   "Live Data", with nothing on screen distinguishing them.
2. **The shared link has no preview.** The page has zero Open Graph tags.
   Pasted into WhatsApp or iMessage it renders as a bare
   `github.io/claudekit/bullion-live-map/bullion_mk11_constellation.html`
   with no title card, image, or description.

A third problem — FOMC hike/cut probabilities are fully simulated but render
identically to measured values — is folded into (1), since both are provenance
questions and a single mechanism answers them.

## Scope

**In scope (this spec):**

- Tier 1: Open Graph tags + designed preview card; per-field date lines; loud
  fetch-failure state.
- Tier 2: provenance strip; simulated-value markers.
- The `data.json` schema v2 envelope that both tiers depend on.

**Explicitly out of scope (deferred to 2026-07-21):**

- **Tier 3, the guided narrated tour.** Deferred deliberately, not for cost.
  Its design rests on an untested assumption about what confuses beginners —
  that they are blocked on the map's visual grammar (drivers vs. derived,
  arrows as causation). That assumption should be checked by watching two or
  three real beginners use the Tier 1+2 build before any tour is specced.
- A test framework for the HTML file. See "Testing constraints" below.
- Any new live data series (real yields `DFII10`, credit spreads
  `BAMLH0A0HYM2`). Discussed and wanted; separate work.
- Reducing page weight. The 480KB page is ~450KB inlined D3. Inlining is what
  makes the file self-contained and emailable; that tradeoff stands.

## Global constraints

- **No build step.** `bullion_mk11_constellation.html` is a single
  self-contained file with inline CSS and JS. It must remain openable from
  `file://` with no server, no bundler, no npm install.
- **No new runtime dependencies.** `fetch_bullion_data.py` uses only the Python
  standard library. Keep it that way.
- **Graceful degradation is mandatory.** The map must stay usable when
  `data.json` is missing, malformed, or an older schema. It currently falls
  back to a simulated baseline; that behaviour is preserved and made visible.
- **Deployment URL:** `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/`

---

## Section 1 — Provenance data model

### Value classes

Every value the map displays carries one of three classes, and the class
travels with the value from fetcher to pixel:

| Class | Meaning | Fields |
|---|---|---|
| `measured` | Real observation from a real source | `us2y`, `us10y`, `vix`, `ffr`, `wti_px`, `cpi_yoy`, `nfp_mom`, `gold_px`, `dxy`, `spx` |
| `simulated` | Invented by the map's own model | FOMC hike / hold / cut odds |
| `derived` | Computed from other displayed values | 10Y−2Y spread |

### `data.json` schema v2

The current file is a bare `{date: {field: value}}` map. Schema v2 wraps it in
an envelope. The `history` block keeps its exact current shape, so the date
picker (`setupHistoryDatePicker`, line 3209) needs no changes.

```json
{
  "schema": 2,
  "generated_at": "2026-07-20T10:07:14Z",
  "fields": {
    "cpi_yoy": {
      "class": "measured",
      "cadence": "monthly",
      "source": "FRED CPILFESL",
      "ref_date": "2026-06-01",
      "published": "2026-07-14",
      "value": 2.6
    },
    "gold_px": {
      "class": "measured",
      "cadence": "daily",
      "source": "Yahoo GC=F",
      "ref_date": "2026-07-17",
      "published": "2026-07-17",
      "value": 4018.8
    }
  },
  "history": {
    "2026-07-17": { "gold_px": 4018.8, "dxy": 100.75, "spx": 7457.69 }
  }
}
```

Field-level keys:

- `class` — one of `measured`, `simulated`, `derived`.
- `cadence` — one of `daily`, `monthly`, `fomc`.
- `source` — human-readable attribution, shown in the audit log.
- `ref_date` — the period the reading describes. For June CPI this is
  `2026-06-01`.
- `published` — when the reading became available. For June CPI,
  `2026-07-14`.
- `value` — the latest value, already rounded as today.

For Yahoo fields `ref_date` and `published` are equal: the daily close is both
the reference period and the moment it exists. This is correct, not a
placeholder.

### Obtaining publication dates

FRED exposes publication dates through the `realtime_start` field when
`realtime_start`/`realtime_end` are passed on the observations endpoint.
Verified 2026-07-20 against `CPILFESL`: the June observation carries
`realtime_start: 2026-07-14`, matching the release-dates endpoint for
release 10. No new dependency and no extra API call — the existing
`fetch_fred_series` request gains two query parameters.

### Freshness rule

**Freshness is judged on `published`, never on `ref_date`.** June CPI is 49
days past its reference date but 6 days past publication. Judged on reference
date it looks broken; judged on publication it is healthy and on time. This
distinction is the entire point of the feature: a monthly series arriving in
arrears is *correct behaviour*, and the map should teach that rather than
flag it as a fault.

Tolerances are calibrated against publication lags measured 2026-07-20
(a Monday, with markets last trading Thu 16 / Fri 17):

| Series | ref age | pub age |
|---|---|---|
| DGS2, DGS10, DFF | 4d | 3d |
| VIXCLS | 4d | 4d |
| DCOILWTICO | 7d | 5d |
| CPILFESL | 49d | 6d |
| PAYEMS | 49d | 18d |

Resulting thresholds — a field is flagged only when its **publication age**
exceeds its own tolerance:

| Cadence | Default tolerance | Rationale |
|---|---|---|
| `daily` | 7 days | Observed healthy range is 3–4d; 7 absorbs a three-day weekend plus a holiday |
| `monthly` | 45 days | Observed 6d (CPI) and 18d (PAYEMS); a monthly series silent for 45 days is genuinely broken |
| `fomc` | n/a | Simulated; never flagged for staleness |

Per-field overrides:

| Field | Tolerance | Rationale |
|---|---|---|
| `wti_px` | 10 days | Structurally laggier than other dailies — observed at 5d publication age while healthy. A 7-day rule would have produced a false alarm on day one. |

These thresholds are calibration, not physics. The fetcher logs each field's
publication age on every run so they can be revised against observed data
rather than re-guessed.

### Schema tolerance

GitHub Pages caches aggressively, so a new HTML will meet an old `data.json`
and vice versa. The loader branches on the `schema` key:

- `schema === 2` — full provenance UI.
- **key absent** — treat as v1. Wrap the bare date map into the v2 envelope in
  memory, mark every field `measured` with `cadence: "unknown"`, and **suppress
  all freshness UI**. Showing dates derived from a guess would reintroduce the
  exact dishonesty this work removes.
- `schema > 2` — treat as v1 for safety, log a console warning.

### Failure visibility — already handled

**Corrected 2026-07-21.** An earlier draft of this spec claimed the fetch
failure path was a silent `console.warn` leaving the user with no indication.
That was wrong, and the claim was made without reading far enough into the file.

`renderLiveProvenance()` (line ~2662) already writes *"All metrics are
simulated — data.json not found or failed to load. Run fetch_bullion_data.py
to pull live data."* to `#live-provenance`, and `renderLiveBadge()` mirrors a
condensed form into the header. The `console.warn` is a developer aid alongside
that UI, not instead of it.

No new failure UI is therefore in scope. The implementation must **preserve**
this behaviour — the loader rewrite is the risk, not the absence of a message.

Two related surfaces already exist and must be extended rather than duplicated:

- `ALWAYS_SIMULATED_LABEL` already names FOMC odds as simulated in the status
  line. What is missing is a marker where the FOMC number is actually
  displayed, in the scenario stats panel.
- `LIVE_FIELD_LABEL` already maps field names to display names and should be
  reused rather than re-declared.

What remains genuinely broken is the date: `renderLiveProvenance` renders
`Live as of {s.fetched_at}` — one date applied to ten fields published on ten
different schedules. That sentence is what this work replaces.

---

## Section 2 — Rendering surfaces

Three surfaces, in descending order of attention received.

### Metric rows

Each metric row gains a provenance sub-line in the existing `--text-dim`
style:

```
Core CPI        2.9%
                June · published Jul 14 · monthly
```

**Fresh daily fields render no sub-line.** Silence means current. Appending
"as of today" to eight daily fields would be noise that trains readers to
ignore the line entirely — which would defeat it on the one field where it
matters.

### Simulated values

Simulated values get a persistent marker rather than a footnote. A `~` prefix
plus the dim treatment:

```
FOMC hold odds  ~72%
                model estimate · not market data
```

This is the largest code change in the spec, because FOMC odds feed node
colouring and scenario output rather than living only in the metrics panel.
The `METRIC_GUIDE` entry for FOMC Probabilities already discloses this in prose
("a hardcoded snapshot, not live"); that prose stays, and the marker makes the
same fact visible where the number is actually read.

### Provenance summary line

**Revised 2026-07-21** — an earlier draft proposed a new strip element near the
Live Data button. That would have sat beside `#live-provenance`, which already
carries exactly this information. The existing element is extended instead.

`renderLiveProvenance` currently ends with:

```
Live as of {fetched_at}: US2Y, Core CPI, Gold… Still simulated: FOMC hike/cut odds.
```

The single `fetched_at` date is the misrepresentation. It becomes:

```
Live: US2Y, Core CPI, Gold… Still simulated: FOMC hike/cut odds.
All 10 measured fields are current — most recent publication Jul 17.
```

and, when a field breaches its cadence:

```
1 of 10 measured fields may be failing: wti_px. Most recent publication Jul 17.
```

### Flagged fields

When a field breaches its own tolerance it gets an amber dot and a hover
reason:

> Expected daily, last published 9 days ago — the source may be failing.

Amber (`--amber: #e0b15a`), not red: this warns about the data pipeline, not
about market conditions. Red on a finance dashboard reads as "markets are
falling", which would be a new piece of misinformation.

---

## Section 3 — Social preview

### Open Graph tags

Added to `<head>`. **URLs must be absolute** — relative OG URLs are unreliable
across scrapers — so the deployment URL is hardcoded:

```html
<meta property="og:type" content="website">
<meta property="og:title" content="Bullion Mk11 — US Financial System Constellation">
<meta property="og:description" content="An interactive map of how the US financial system actually connects — live Treasury yields, inflation, gold and volatility, with every causal link explained in plain English.">
<meta property="og:url" content="https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mk11_constellation.html">
<meta property="og:image" content="https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/preview-card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="description" content="An interactive map of how the US financial system actually connects — live Treasury yields, inflation, gold and volatility, with every causal link explained in plain English.">
```

The hardcoded absolute URL is a known wart: the file no longer renders a
correct preview if moved. Accepted, because relative OG URLs do not work.

### The card

A designed card, not a screenshot — a screenshot goes stale silently every time
the map changes and nobody remembers to retake it.

- `preview-card.svg` — source, committed.
- `preview-card.png` — 1200×630, committed. Generated once from the SVG.
- Palette taken from the map's own CSS custom properties: `--bg-deep #05060a`
  background, `--gold #d4b869` title, `--text-dim #8891a6` subtitle.
- Content: title "Bullion Mk11", subtitle "How the US financial system
  actually connects", and a small constellation motif echoing the map's node
  layout.
- No live values on the card. Baking numbers into a static image recreates the
  staleness problem in the one place it cannot be fixed.

---

## Testing

### What is properly testable

`fetch_bullion_data.py` holds the logic that can actually be wrong — schema
assembly and the freshness verdict — and it is pure Python. Tests live in
`bullion-live-map/tests/test_fetch_bullion_data.py`.

**Tooling constraint, verified 2026-07-21: neither `pytest` nor `node` is
installed on this machine.** Rather than add install steps to a project whose
defining constraint is zero dependencies, both test suites use what is already
present:

- **Python: `unittest` from the standard library.** Run with
  `python3 -m unittest discover -s bullion-live-map/tests -v`. No install.
- **JavaScript: a self-contained HTML runner driven by headless Chrome**,
  which is confirmed present at
  `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`. No install.

Cases:

- Schema v2 envelope assembly from mocked FRED and Yahoo responses.
- `published` extraction from FRED `realtime_start`.
- Yahoo fields get `ref_date == published`.
- Freshness verdict boundaries: daily at 6d (fresh) vs 8d (flagged); `wti_px`
  at 8d (fresh, override applies) vs 11d (flagged); monthly at 44d vs 46d.
- A field that fails to fetch is omitted, and the run still writes a valid
  envelope for the fields that succeeded.
- Total fetch failure leaves the existing `data.json` untouched (current
  behaviour, `fetch_bullion_data.py:175-177` — must not regress).

### The freshness verdict is shared logic

The same rule runs in Python (for logging) and JavaScript (for display). To
avoid the two drifting, the JS implementation is a single pure function:

```js
function freshnessVerdict(cadence, published, today, overrideDays)
// → { state: 'fresh' | 'flagged' | 'unknown', ageDays: number }
```

It takes no DOM and no globals. Because the map must remain a single
self-contained file, the function lives inline in the HTML between the marker
comments `FRESHNESS-VERDICT-START` / `FRESHNESS-VERDICT-END`. The test runner
`bullion-live-map/tests/freshness_test.html` reads the HTML, extracts the
source between those markers, evaluates it, and asserts the same boundary cases
as the Python suite — so a change to one surfaces as a failure in the other.

Extracting from the shipped file rather than duplicating the function is what
keeps the two from drifting. The cost is that renaming or removing the marker
comments breaks the test, which is the intended failure mode.

### Testing constraints — stated plainly

`bullion_mk11_constellation.html` is a single 3288-line file with inline JS, no
build step, no module boundaries, and no test runner. **Nothing in it is
unit-testable today**, and this spec does not fix that — doing so is a larger
project than this work, and pretending a handful of DOM assertions constitutes
coverage would be worse than admitting the gap.

Rendering is therefore verified manually in a browser, against three fixtures:

1. **Schema v2 data** — sub-lines, provenance strip, and simulated markers all
   render; fresh daily fields show no sub-line.
2. **Schema v1 data** (today's `data.json`) — map works, freshness UI fully
   suppressed, no console errors.
3. **404 on `data.json`** — Live Data button reads "Simulated — live data
   unavailable", provenance strip explains, map still usable.

Each fixture is checked at desktop width and at the 640px mobile breakpoint.

---

## Risks

| Risk | Mitigation |
|---|---|
| Simulated-value markers touch node colouring and scenario output — the riskiest edit in the file | Land it as its own task, after Tier 1 is verified working. Fixture 1 explicitly re-runs a scenario. |
| Thresholds are calibrated on a single day's observation | Fetcher logs publication age every run; thresholds revisited once a few weeks of logs exist |
| Hardcoded OG URL breaks if the page moves | Documented above; single line to change |
| Cached HTML meets new `data.json` or vice versa | Schema branching, with v1 suppressing freshness UI rather than guessing |

## Open threads (not blocking)

- The daily GitHub Actions push path remains unproven — no
  `github-actions[bot]` commit exists after `e321844`. Worth confirming
  separately.
</content>
</invoke>

# Bullion Mk Ultra — R2 UI Pass: The Punch List

**Written:** 2026-09-26 · **Authority for scope:** `docs/superpowers/bullion-done-criteria.md` §R2.
**Status:** **LIST CLOSED 2026-09-26** — all 8 items fixed and re-verified in headless Chrome at
both widths. Uncommitted; see "Verification after the fixes" at the end.

**Scope note, recorded because it overrides the authority doc.** R2 as written is "one pass, one
punch list." The owner declared on 2026-09-26 that this pass may also carry a *bolder visual pass*
— a deliberate scope change, not scope creep. One fix below (P1-2) goes past pure defect repair on
that authority, and P2-6 exists only because of it. Everything else is bounded defect repair and
the brutalist identity is unchanged.

Per R2: *"One pass, one punch list. Walk the app at phone width and desktop width, write every
visual defect found into a single list, fix that list, stop."* This is that list. Once it is
closed, a defect found later goes on the someday list unless it is a genuine bug.

**R2's hard bar, measured up front:** no horizontal scroll on any of the three tabs at 390px or
1280px. **Already passing** — `documentElement.scrollWidth` never exceeded the viewport on any of
the 7 surfaces probed at either width. What follows is the rest of the walk.

## How this was walked

Headless Chrome over `python3 -m http.server 8934`, per the project's verification idioms
(`--user-data-dir` isolated; `#start-screen-cta` clicked; `#coach` hidden). Two viewports —
**390×844** and **1280×900** — across seven surfaces each: start screen, Causal Link map, node
detail panel (`openDetail('fed')`), Market tab, Analysis pre-run, Analysis post-run, and Analysis
under an active scenario. Each surface got a screenshot that was actually looked at, plus an
in-page geometry scan (viewport overflow, self-clipping text, touch-target size, line length).

Probes and screenshots: `/private/tmp/claude-501/.../scratchpad/` (`ui_probe*.mjs`, `shots*/`).
Test baseline before any change: **126 passed, 1 failed** — the known pre-existing
`test_every_known_field_has_metadata`. Anything else afterward is a regression.

---

## The list

### P1-1 · Analysis panel prose runs 3× the readable line length at 1280px

**Location:** `#analysis-view`, twelve distinct classes. Measured widths at 1280px:

| Element | Width | Font | ≈chars/line |
|---|---|---|---|
| `#narrative-box.narrative-box` | 1248px | 12px | ~208 |
| `.dim-scale` | 1248px | 10.5px | ~238 |
| `.dim-shock-note` | 1248px | 10.5px | ~238 |
| `.dim-why.dim-gap`, `span.dim-flag` | 1227px | 11px | ~223 |
| `.chain-hop-why` | 1224px | 11px | ~223 |
| `.sim-note`, `#live-provenance`, `#history-note`, `.stats-foot`, `.impacts-note`, `#scenario-explain` | 1248px | 12px | ~208 |

The house standard is **65–75 characters**. This is the known candidate the done-criteria doc
flagged going in, and it is worse than "the dimension rows are 1248px wide" — it is every prose
run in the tab.

**The fix is a constraint, not a redesign, and the app already proves it:** at 390px the exact
same dimension rows render at ~55 chars/line and read beautifully, and the node detail panel at
1280px is constrained to ~360px and is the best-reading surface in the app. One `max-width` on the
analysis content column reproduces on desktop what mobile already does right.

⚠️ `#narrative-box` has `max-width: none` explicitly.

### P1-2 · Composite score and its label sit ~1100px apart

**Location:** `.health-score-row` — `display:flex; justify-content:space-between`, width 1248px.
Measured: the `58` (`.hero-stat`) starts at x=16 and occupies 1183px; `#health-label`
("Moderate stress") starts at x=1199. The number and the words that say what it means are on
opposite sides of the screen with nothing between them, so they don't read as one statement.

⚠️ **Do not fix by removing `flex: 1 1 auto` from `.health-score-row .hero-stat`.** The comment at
line ~707 records that it is deliberate: the wrapper shrink-to-fitting its 2-digit number clipped
the 96px `.hero-stat-ghost` glyph via `overflow:hidden`. A fix must keep the ghost unclipped.

### P1-3 · Impact rows lose label↔value association across 1248px

**Location:** `#impacts-list .impact-item` — each row is a 1248px block with the node name at the
left edge and its `Δ%` at the right. "Tech Equities" at x=16, "Δ-14%" ending at x=1250, a hairline
rule between. Eleven rows of this. The eye cannot reliably carry a label to its value across
1200px of empty space; this is the classic too-wide `space-between` failure.

### P1-4 · Persona orb overlays and obscures live content

**Location:** `#persona-orb` — `position:fixed; z-index:15`, 52×67px, `right:18px; bottom:18px`.
No container reserves space for it, so it sits on top of whatever scrolls underneath.

- **1280px, Analysis:** covers the right-hand `Δ%` values of the impact rows — the **Gold** row's
  value is entirely hidden behind it, and USD's is partly behind it. Data obscured, not just
  decoration overlapped.
- **390px, Analysis:** the orb plus its speech bubble covers the Credit dimension row and, on the
  pre-run view, the whole `#live-provenance` line.

**Fix direction:** reserve bottom padding on the scrolling panels equal to the orb's footprint.

### P2-5 · Empty bordered cell in the Live Metrics grid

**Location:** the metrics grid in `#analysis-view` — **9 cells in a 2-column grid**, so the last
row has WTI OIL on the left and a fully-bordered empty cell on the right. Visible at both 390px
and 1280px.

This is the exact quirk recorded in the brutalist-nav memory: it was invisible while `--border`
was near-black and became glaring when the token went to pure white. It has simply never been
fixed. Either span the last cell across both columns or fill it.

### P2-6 · Every interactive control is under the touch-target minimum at 390px

**Location:** `.btn` and friends, measured at 390px:

| Control | Size |
|---|---|
| `#tab-causal-link` / `#tab-market` / `#tab-analysis` | 102×**22** / 70×**22** / 78×**22** |
| `#expand-all-btn`, `#collapse-all-btn`, `#reset-view-btn`, `#audit-log-btn`, `#copy-link-btn` | ×**24** |
| `#detail-close` | **24×24** |
| `#disclaimer-close` | **21×22** |
| `.drawer-tag` (`show`, `what do these mean?`) | ×**17** |

WCAG 2.5.5 and both platform HIGs want **44×44**. Everything here is 17–29px tall. The two close
buttons are the worst: a 21×22px tap target on a phone is a genuine miss-and-mis-tap generator.

**Bounded fix that preserves the brutalist density:** raise the minimum inside
`@media (pointer: coarse)` only, so desktop spacing is untouched pixel-for-pixel.

### P2-7 · Node label clipped at the left viewport edge at 390px

**Location:** Causal Link map, first render at 390px. "Commercial Banks" renders as
"**…ercial Banks**", running off the left edge. The scene is orbitable so it is recoverable by
dragging, but the default framing at phone width ships a cut-off label.

### P3-8 · "NOTE" badge collides with the node label

**Location:** Causal Link map — renders as "Oil Price (WTI)NOTE" with no gap or separation at both
widths. Needs spacing, or to be a visually distinct chip.

---

## Out of R2 scope — but a genuine bug, so it is not a someday item

### BUG-A · Headlines are empty on the live site; the cron reports success

**Not a UI defect — a data-pipeline regression, and it breaks a criterion already marked MET.**

Live `news.json` right now:

```json
{ "generated_at": "2026-09-25T21:30:31Z", "headlines": [] }
```

Headline counts by commit:

| Run | Headlines |
|---|---|
| 2026-09-25T21:30Z (latest, live) | **0** |
| 2026-09-25T17:55Z | **0** |
| 2026-09-24T21:27Z | 40 |
| 2026-09-24T17:50Z | 40 |
| 2026-09-23T21:27Z | 38 |
| 2026-09-22T21:13Z | 40 |

`gh run list --workflow=news-hourly.yml` reports **`completed success`** for both zero-headline
runs.

**Root cause — diagnosed, and it is not Bullion's code.** The workflow log says it outright:

```
Wrote news.json with 0 headlines (of 49 fetched, filtered to last 48h).
```

The fetch succeeds and returns 49 items. Every one of them is then dropped by the `MAX_AGE_HOURS
= 48` recency filter, because **the upstream feed itself has stopped publishing.**
`https://finance.yahoo.com/news/rssindex` was pulled directly on 2026-09-26T18:43Z: 49 items, and
the **newest is 2026-09-23T06:00:41Z — 85 hours old.** (It also carries junk as old as
2024-11-20.) Replaying the real feed against the real cutoff reproduces the observed history
exactly:

| Run | Cutoff | Items surviving |
|---|---|---|
| 2026-09-24T21:27Z (last good) | 09-22 21:27Z | **45** of 49 → capped to `MAX_HEADLINES` 40 ✓ |
| 2026-09-25T17:55Z | 09-23 17:55Z | **0** ✓ |
| 2026-09-25T21:30Z | 09-23 21:30Z | **0** ✓ |
| now (09-26T18:43Z) | 09-24 18:43Z | **0** ✓ |

So `fetch_bullion_news.py` is behaving exactly as designed. The 48h filter is correctly refusing
to present 4-day-old headlines as current. **The bug is that it fails invisibly.**

**Why no alarm fired.** `news-hourly.yml`'s freshness gate (`id: freshness`) reads **only
`generated_at`**, which this job rewrites on every run whether or not any headline survived:

```python
generated_at = ... json.load(f)["generated_at"]
stale = age_hours > STALE_AFTER_HOURS   # 6
```

`generated_at` is always seconds old, so `stale` is always `false` and the `news-pipeline-stale`
issue is never opened. The guard's own comment states the assumption — *"if this run's fetch
succeeded, generated_at is seconds old"* — and the assumption is wrong: the fetch can succeed and
still yield nothing. **No issue has ever been opened on this label; the only alarm issues in the
repo are three closed `pipeline-alarm` ones from the daily-data job.**

This is the `ci-verify-scheduled-runs-actually-succeed` pattern (green cron, dead output) and
exactly what `silent-failure-and-vendor-independence` warns about. **Criterion 4 is recorded as
MET in the done-criteria doc but is currently false on the live site.**

**Two separable fixes, neither of them R2:**

1. ✅ **The guard — DONE 2026-09-28 (`b3603d0`).** The freshness step now alarms on
   `len(headlines) == 0`, not just `generated_at` age, and distinguishes *fetch broken* (feed
   returned nothing) from *source stale* (feed returned items, all past the 48h window) — because
   those need different responses and look identical from outside. `fetch_bullion_news.py` records
   `source_item_count` and `newest_item_published` to make that call possible, and prints a loud
   stderr warning on any zero-headline run. Both new keys are read defensively; pre-2026-09-28
   files still alarm, with a less specific reason.

   Verified by extracting the guard from the YAML and replaying the **real** historical payloads
   from git (empty file alarms; with diagnostics it names the source; feed-returns-nothing names
   the fetcher; the 40-headline file is quiet; that file aged past 6h alarms; missing file alarms),
   then running the real fetcher against the live feed and feeding its output to the guard.

   ⚠️ **The earlier proposal to "refuse to commit an empty array over a populated one" was
   deliberately NOT implemented.** Keeping the old file would leave `generated_at` ageing, so the
   6h check would eventually fire — but the page would meanwhile present five-day-old items as
   current news. That contradicts the project's own honesty bar. The empty state is *correct*
   behaviour; the bug was only ever the silence. Fixed the silence.

   Side effect worth knowing: `tests/test_fetch_bullion_news.py` (56 tests) had never run on this
   machine — Pillow was missing, so it was uncollectable. With Pillow installed it collects and
   **all 56 pass**. Suite is now 182 passed / 1 pre-existing failure.

2. ✅ **The source — FIXED 2026-09-28 (`0eab97e`).** Yahoo's `rssindex` is abandoned, not briefly
   down: it returns HTTP 200 and 49 items, but its `last-modified` header and its own channel
   `pubDate` both read `2026-09-24T12:21 GMT` and have not moved, while `age: 439` against
   `cache-control: max-age=600` shows the CDN re-fetching every 10 minutes and getting the same
   frozen document. It still declares `ttl: 5`. Yahoo's RSS estate is fine — the per-ticker
   endpoint is live — so this is one dead endpoint, not a vendor exit.

   It is replaced by **four feeds across three vendors**, fetched independently; one failing is
   recorded and skipped, never fatal. Sources were chosen on *measured* on-topic rate (each feed's
   fresh items scored through `classify_category`), not reputation:

   | Feed | Fresh 48h | On-topic | Verdict |
   |---|---|---|---|
   | Yahoo Finance `^DJI` | 17 | **88%** | in |
   | MarketWatch Bulletins | 5 | **80%** | in |
   | CNBC Top News | 26 | **69%** | in |
   | MarketWatch Top Stories | 10 | 40% | in — the only source with thumbnails |
   | BBC Business | 19 | **21%** | **rejected** |
   | Google News search | 99 | 82% | **rejected** |

   BBC was in the first cut and pulled: at 21% it filled the tab with Welsh tourism tax and rail
   nationalisation. Google News scored best on paper and was rejected anyway — opaque
   `news.google.com` redirect links rather than publisher URLs, and results mixing wire copy with
   marketing blogs, which fails criterion 2's "reputable sources".

   **The alarm now asserts per source, which is the real fix.** A total-only guard is useless with
   four feeds: one freezing leaves the total healthy and hides behind the others — the original bug
   one level up. `news.json` carries `ok`/`fetched`/`fresh`/`contributed`/`newest` per source, and
   the workflow alarms on any one being **down**, **unparseable**, or **frozen** (returning items
   but none inside the 48h window — exactly Yahoo's shape). Verified: *one frozen source among
   three healthy, 40 headlines shipped → `stale=true`.*

   Live result: 40 headlines from 69 fetched, balanced CNBC 15 / Yahoo 11 / MarketWatch 10 /
   Bulletins 4, **62% on-topic vs the old mix's 52%**, thumbnails intact, rendered and checked in a
   browser. `news.json` and `news-images/` are committed so the site recovers on merge rather than
   waiting for the cron.

   ⚠️ **Criterion 4 is not MET until this is merged to `main` and one unattended cron run
   succeeds.** The code is verified; "refreshes unattended" is a claim about the deployed cron, and
   nothing here proves that yet.

The user-visible symptom in the Market tab is `#news-list-empty` → "No recent headlines."

---

## Deliberately NOT on this list

These were considered and rejected as R2 work. Recording them so they are not rediscovered as
"new" later:

- **The ghost `Δ` watermark** (`.hero-stat-ghost`) — a 96px, `opacity: 0.07`, `aria-hidden`
  decorative glyph. It reads as a stray artifact in a screenshot but it is deliberate design.
  **Not a defect.** Nearly reported as one.
- **Dead vertical space in the 3D map at 390px** — inherent to an orbit camera view.
- **Legend hidden at 390px** — a deliberate media-query decision, not a break.
- **Anything that would restyle the nav, the score, or the visual direction.** The done-criteria
  doc forecloses it: *"Not a mandate to restart the composite health score, redesign the nav
  again, or add features not listed above."*

## Discoverability — raised by the owner mid-pass, and it is an R1 item, not a missing feature

The owner asked on 2026-09-26 to "bring back" the ability to change individual numbers (VIX etc.)
and see how the map responds. **It was never removed.** It is live, wired, and working:

- `#manual-toggle` ("Set your own numbers · show") → `#manual-box` → `buildManualRows()`.
- Built from `DRIVERS` (line ~4810): `ffr`, `vix`, `cpi_yoy`, `dxy`, `wti_px` — five entries, each
  with a range slider **and** a number input, min/max/step, and per-driver help text.
- Baselines are patched from live data, not hardcoded.

Verified end to end in headless Chrome: the drawer opens with 5 rows, VIX pre-filled at its live
**14.2**; setting it to **62** syncs the slider and reads "+47.8 vs baseline"; re-running the
analysis moves the composite **58 → 28**, "Moderate stress" → **"Elevated stress"**, and flips the
Volatility dimension to **+3.00** tagged *Hypothetical* with "VIX at 62.0 is 3.0 standard
deviations…". It integrates correctly with the per-dimension panel shipped in `60aa26a`.

**So the defect is that a first-time user cannot find it.** It is collapsed by default behind a
`.drawer-tag` that measured **47×17px** before this pass. That is precisely R1's job — *"extend
the existing first-run coach to cover what it currently does not"* — and the same is true of
`#metricguide-box`, `#trends-box` and `#glossary-box`, which are all live behind the same tiny
tag pattern. **Recommend R1 add a coach step for this drawer specifically**; it is arguably the
single most teaching-relevant control in the app for criterion 1.

## Positive findings (keep these, don't "fix" them)

- **No horizontal scroll anywhere**, either width, all three tabs, including the scenario state.
- **The node detail panel at 1280px is the best-reading surface in the app** — constrained width,
  clear hierarchy, honest evidence badges. It is the model P1-1 should copy.
- **The mobile Analysis layout is already correct.** The 2-column metric grid holds, the dimension
  rows read at ~55 chars/line. Desktop is the broken one, which is unusual and worth saying.
- The dimension rows ship real epistemics — baseline-window caveats, "1 causal link into this
  dimension is unverified and excluded", "no verified causal links into volatility". Visible
  without clicking, exactly per the render contract.

## Verification after the fixes

All fixes are CSS plus one JS clamp, in `bullion-live-map/bullion_mkultra.html`. The CSS is a
single labelled block at the end of the stylesheet — revertible in one cut.

| Check | Before | After |
|---|---|---|
| Prose elements over ~90ch at 1280px | 12 | **0** |
| `#dimension-rows` width | 1248px | **900px** |
| `.health-score-row` height | 104px | **58px** |
| Score ↔ its label | x=190 vs x=1199 (~1010px apart) | **x=190 vs x=312**, baselines aligned |
| `.impact-item` label ↔ value | ~1200px apart | **460px row** |
| Off-screen node labels at 390px, 3 fresh loads | "Commercial Banks" at `left:-35px` every load | **0, 0, 0** |
| Empty bordered metric cell | present at both widths | **removed**; WTI spans the row |
| Horizontal scroll, 3 tabs × 2 widths | none | **none** (unchanged) |
| `python3 -m pytest …` | 126 passed, 1 failed | **126 passed, 1 failed** (same pre-existing) |
| `node --check` on the largest inline `<script>` | ok | **ok** |

**P2-6 was verified indirectly and that limit is worth recording.** `Emulation.setEmulatedMedia`
could not make this Chrome report `(pointer: coarse)` — `matchMedia` kept returning false — so the
rule could not be exercised through its own media query. It was verified two other ways instead:
the rule parses into the CSSOM with condition `(pointer: coarse)` and all five declarations
intact, and applying the identical declarations with the media query stripped moves every target
(tabs 22→36px, `#detail-close` 24×24→**40×40**, `#disclaimer-close` 21×22→**40×40**, drawer tags
17→30px, `#run-ai-btn` 38→44px). What is *not* proven here is the media query firing on real
touch hardware. **Worth one look on an actual phone.**

### A latent bug found while fixing P1-2, worth carrying forward

`.hero-stat-ghost` declares `position: absolute` (line ~222) but `.hero-stat > *` declares
`position: relative` (line ~226). Same specificity, later rule wins — so the decorative 96px Δ was
**never out of flow.** It was a 64×109px block inflating `.hero-stat` to 104px tall, pushing the
score out of line with its own label and putting a large empty wedge above the Market tab's
Fed-odds headline. The `z-index: 0` on the ghost and `z-index: 1` on its siblings only make sense
if it sits behind them, so the intent is clear and has now been restored.

This also explains the `flex: 1 1 auto` workaround that the 2026-09-25 session added to this row
and warned about: it was widening the box so an in-flow glyph would not be clipped. That workaround
is gone; the warning it carried no longer applies.

## Closing condition

**Met.** P1-1 … P3-8 are fixed, and the re-probe shows no horizontal scroll and no overlapping
text at 390px and 1280px on all three tabs, in every state walked.

BUG-A is tracked here but is **not** R2 — it does not gate this list. It gates *release*, via
criterion 4, and needs an owner decision on the news source. The done-criteria doc still records
criterion 4 as MET; that cell is now wrong and should be corrected when BUG-A is resolved.

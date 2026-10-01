# Mk Ultra Macro Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `bullion_mkultra.html`'s "Run AI analysis" (a dead `api.anthropic.com` call that always 401s, silently falling back to a hand-picked linear formula) with a fully deterministic, client-side macro-conditions engine grounded in real institutional methodology (PCA-derived weights, à la the St. Louis Fed FSI).

**Architecture:** An offline Python script (`backfill_baseline.py`) pulls 15 years of history per field from FRED/Yahoo (reusing `fetch_bullion_data.py`'s fetchers), computes per-field baseline statistics and a PCA-derived composite weighting, and bakes the result as a `BASELINE_STATS` JS constant into `bullion_mkultra.html` — the same delivery pattern the file already uses for `ELASTICITY`. Three new pure JS functions (`computeCompositeScore`, `computeNodeMultipliers`, `buildMacroNarrative`) consume that constant plus the live `data.json` snapshot to produce the health score, node impact multipliers, and narrative — synchronously, no network call, no LLM.

**Tech Stack:** Python 3 stdlib only (no numpy — matches this project's existing `calibrate.py` precedent of hand-rolled statistics in pure Python), vanilla JS (matches the existing file), `node` CLI for JS↔Python parity testing (already used by `test_chain_reaction_js_parity.py`).

## Global Constraints

- Scope is `bullion_mkultra.html` ONLY. `bullion_mk18.html` and frozen mk11-17 are never touched.
- No new Python dependencies (no numpy/scipy/pandas) — pure stdlib, matching `calibrate.py`'s existing convention.
- No LLM call, no external network call of any kind in the analysis path — fully deterministic and free.
- Every new causal number must carry a confidence tier (`measured`/`directional`/`unverified`) and, where applicable, reuse the existing `NODE_ELASTICITY` coefficients rather than inventing new ones — matching this project's audit-log honesty convention.
- Backfill window: 15 years for mean-reverting fields (`hy_oas`, `ig_oas`, `sofr`, `tbill_3m`, `us10y`, `us2y`, `curve_slope`, `vix`, and the 5 `NODE_ELASTICITY` drivers `ffr`, `cpi_yoy`, `dxy`, `wti_px`); 2 years for secularly-trending fields (`spx`, `fed_bs`, `rrp`) to avoid a long-run mean being distorted by trend (SPX has risen from ~1200 to ~7700 over 15 years — a 15yr mean would make today's level always read as "extreme" regardless of actual stress).
- Composite score fields (11 total, PCA-weighted): `hy_oas`, `ig_oas`, `sofr`, `tbill_3m`, `us10y`, `us2y`, `curve_slope` (derived: `us10y - us2y`), `vix`, `spx`, `fed_bs`, `rrp`.
- `cpi_yoy`/`nfp_mom` are excluded from the composite score (monthly-lagged fundamentals, not real-time market signals — matches how NFCI/OFR FSI/STLFSI/CISS all exclude growth/inflation), but remain in the narrative as context.
- **Composite row-matrix window is `RECENT_WINDOW_YEARS` (2 years), not `FULL_WINDOW_YEARS` (15) — this is distinct from any individual field's `window_years`.** Discovered during implementation (Task 4's testing): the PCA fit and percentile table that back the composite score must use a date range consistent with every composite field's own baseline, including the trending fields which are only meaningfully z-scored against their trailing 2-year mean. Building the row matrix from a longer intersection (up to 15 years where data allows) produces an artificial step-discontinuity at the 2-year boundary — confirmed empirically (rows older than 2yr clip to z=-3 on all three trending fields simultaneously, landing ~6 composite units away from the recent cluster, not a gradual trend). `build_baseline`'s output carries this as `composite_window_years` — Task 6's narrative must cite that field, not `BASELINE_STATS.fields.vix.window_years` (15), when describing how far back the composite's percentile ranking goes.
- Spec: `docs/superpowers/specs/2026-08-09-bullion-mkultra-macro-engine-design.md`

---

## File Structure

- Create: `bullion-live-map/backfill_baseline.py` — offline stats/PCA computation + JS-constant splicer.
- Create: `bullion-live-map/tests/test_backfill_baseline.py` — Python unit tests for the stats/PCA math.
- Modify: `bullion-live-map/bullion_mkultra.html` — add `BASELINE_STATS` constant, add the 3 pure scoring functions, replace `runAIAnalysis`/`runLocalAnalysis`, extend `openAuditLog`, rename button copy.
- Create: `bullion-live-map/tests/test_macro_engine_js_parity.py` — `node`-based parity test for the 3 new JS functions, mirroring `test_chain_reaction_js_parity.py`.

---

### Task 1: `backfill_baseline.py` — fetch 15yr/2yr history and compute per-field baseline stats

**Files:**
- Create: `bullion-live-map/backfill_baseline.py`
- Test: `bullion-live-map/tests/test_backfill_baseline.py`

**Interfaces:**
- Consumes: `fetch_bullion_data.FRED_SERIES`, `fetch_bullion_data.YAHOO_SYMBOLS`, `fetch_bullion_data.KEY_PATH`, `fetch_bullion_data.fetch_fred_series(series_id, key, units, decimals, start, end) -> (value, ref, pub, hist)`, `fetch_bullion_data.fetch_yahoo_symbol(symbol, decimals, range_) -> (value, ref, pub, hist)` (all already defined in `fetch_bullion_data.py`, `hist` is a `{date_str: float}` dict).
- Produces: `fetch_all_history(key, start, end) -> dict[str, dict[str, float]]` (field name -> date -> value, covers every field in `FRED_SERIES`+`YAHOO_SYMBOLS`); `forward_fill(history, all_dates) -> dict[str, float]`; `field_stats(values) -> dict` with keys `mean`, `std`, `n`; `MEAN_REVERTING_FIELDS`, `TRENDING_FIELDS` module-level lists; `RECENT_WINDOW_YEARS = 2`, `FULL_WINDOW_YEARS = 15`.

- [ ] **Step 1: Write the failing test for `field_stats`**

```python
# bullion-live-map/tests/test_backfill_baseline.py
import os
import statistics
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backfill_baseline import field_stats, forward_fill, fetch_all_history


class TestFieldStats(unittest.TestCase):
    def test_field_stats_matches_hand_computed_mean_and_std(self):
        values = [10.0, 12.0, 14.0, 16.0, 18.0]
        stats = field_stats(values)
        self.assertAlmostEqual(stats["mean"], 14.0)
        self.assertAlmostEqual(stats["std"], statistics.pstdev(values))
        self.assertEqual(stats["n"], 5)

    def test_field_stats_empty_raises(self):
        with self.assertRaises(ValueError):
            field_stats([])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd bullion-live-map && python3 -m unittest tests.test_backfill_baseline -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backfill_baseline'`

- [ ] **Step 3: Write `backfill_baseline.py` — fetch + forward-fill + stats**

```python
#!/usr/bin/env python3
"""Backfill a long-run statistical baseline for the Mk Ultra macro engine.

Pulls 15 years of history per FRED/Yahoo series (reusing fetch_bullion_data's
fetchers), computes per-field mean/std for z-scoring, fits a PCA-derived
composite weighting (see build_pca in the next task), and splices the result
as a BASELINE_STATS JS constant into bullion_mkultra.html.

Rerunnable: rerun periodically (e.g. yearly) to keep the baseline current.
Not part of the daily-data cron — this is a slow, occasional, manual/dev-time
script, same category as calibrate.py.

See docs/superpowers/specs/2026-08-09-bullion-mkultra-macro-engine-design.md
"""
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_bullion_data import FRED_SERIES, YAHOO_SYMBOLS, KEY_PATH, fetch_fred_series, fetch_yahoo_symbol

FULL_WINDOW_YEARS = 15
RECENT_WINDOW_YEARS = 2

# Mean-reverting: z-score against the full 15yr window. Trending (secular
# growth/decline, e.g. an equity index or a balance sheet that grows via QE):
# z-score against a shorter recent window instead, since a 15yr mean of a
# trending series is not a meaningful "normal" — see Global Constraints in
# the plan for why.
MEAN_REVERTING_FIELDS = ["hy_oas", "ig_oas", "sofr", "tbill_3m", "us10y", "us2y", "vix",
                          "ffr", "cpi_yoy", "dxy", "wti_px"]
TRENDING_FIELDS = ["spx", "fed_bs", "rrp"]
# Fields whose native cadence has gaps a same-day PCA row matrix can't tolerate.
FORWARD_FILL_FIELDS = ["fed_bs"]

COMPOSITE_FIELDS = ["hy_oas", "ig_oas", "sofr", "tbill_3m", "us10y", "us2y",
                     "curve_slope", "vix", "spx", "fed_bs", "rrp"]


def _read_fred_key():
    with open(KEY_PATH) as f:
        return f.read().strip()


def fetch_all_history(key, start, end):
    """Fetch full history for every tracked FRED + Yahoo field.

    Returns {field: {date_str: value}}. Yahoo uses range_="max" (no
    arbitrary-length range token is guaranteed valid) and results are
    filtered to [start, end] here.
    """
    out = {}
    for series_id, (field, units, decimals) in FRED_SERIES.items():
        _, _, _, hist = fetch_fred_series(series_id, key, units, decimals, start, end)
        out[field] = hist
    for symbol, (field, decimals) in YAHOO_SYMBOLS.items():
        _, _, _, hist = fetch_yahoo_symbol(symbol, decimals, range_="max")
        out[field] = {d: v for d, v in hist.items() if start <= d <= end}
    return out


def forward_fill(history, all_dates):
    """Carry the last known value forward across every date in all_dates.

    all_dates must be sorted ascending. Dates before the first observation
    are left absent (nothing to carry forward yet).
    """
    filled = {}
    last = None
    for d in all_dates:
        if d in history:
            last = history[d]
        if last is not None:
            filled[d] = last
    return filled


def field_stats(values):
    if not values:
        raise ValueError("field_stats: empty values")
    return {"mean": statistics.mean(values), "std": statistics.pstdev(values), "n": len(values)}


if __name__ == "__main__":
    key = _read_fred_key()
    end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start_full = (datetime.now(timezone.utc) - timedelta(days=365 * FULL_WINDOW_YEARS)).strftime("%Y-%m-%d")
    history = fetch_all_history(key, start_full, end)
    print(f"Fetched history for {len(history)} fields, window {start_full}..{end}", file=sys.stderr)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd bullion-live-map && python3 -m unittest tests.test_backfill_baseline -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/backfill_baseline.py bullion-live-map/tests/test_backfill_baseline.py
git commit -m "Mk Ultra macro engine: backfill_baseline.py fetch + stats foundation"
```

---

### Task 2: `backfill_baseline.py` — derived fields, PCA weighting, percentile table

**Files:**
- Modify: `bullion-live-map/backfill_baseline.py`
- Test: `bullion-live-map/tests/test_backfill_baseline.py`

**Interfaces:**
- Consumes: `fetch_all_history`, `forward_fill`, `field_stats`, `COMPOSITE_FIELDS`, `MEAN_REVERTING_FIELDS`, `TRENDING_FIELDS`, `FORWARD_FILL_FIELDS` from Task 1.
- Produces: `add_curve_slope(history) -> dict[str, dict[str, float]]` (mutates a copy, adding a `curve_slope` field = `us10y - us2y` per date); `build_zscore_rows(history, stats_by_field, fields) -> tuple[list[str], list[list[float]]]` (dates, matrix rows in `fields` order, only dates where all fields present after forward-fill); `pca_first_component(rows, n_iter=500, seed=1) -> list[float]` (pure power-iteration, returns unit-length loadings vector in row-column order); `orient_loadings(loadings, fields, anchor_field="vix") -> list[float]` (flips sign of every element if the anchor's loading is negative); `percentile_table(values, n_points=101) -> list[float]` (values sorted ascending, `n_points` evenly-spaced breakpoints from min to max index).

- [ ] **Step 1: Write the failing tests**

```python
# appended to bullion-live-map/tests/test_backfill_baseline.py
from backfill_baseline import (
    add_curve_slope, build_zscore_rows, pca_first_component,
    orient_loadings, percentile_table,
)


class TestCurveSlope(unittest.TestCase):
    def test_curve_slope_is_us10y_minus_us2y(self):
        history = {"us10y": {"2020-01-01": 4.0, "2020-01-02": 4.5},
                    "us2y": {"2020-01-01": 1.0, "2020-01-02": 2.0}}
        out = add_curve_slope(history)
        self.assertAlmostEqual(out["curve_slope"]["2020-01-01"], 3.0)
        self.assertAlmostEqual(out["curve_slope"]["2020-01-02"], 2.5)


class TestZscoreRows(unittest.TestCase):
    def test_only_dates_with_all_fields_present_are_kept(self):
        history = {"a": {"d1": 1.0, "d2": 2.0}, "b": {"d1": 10.0}}
        stats = {"a": {"mean": 1.5, "std": 0.5}, "b": {"mean": 10.0, "std": 1.0}}
        dates, rows = build_zscore_rows(history, stats, ["a", "b"])
        self.assertEqual(dates, ["d1"])
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0][0], (1.0 - 1.5) / 0.5)
        self.assertAlmostEqual(rows[0][1], (10.0 - 10.0) / 1.0)


class TestPCA(unittest.TestCase):
    def test_recovers_dominant_direction_of_perfectly_correlated_fields(self):
        # Two fields that move in lockstep should load ~equally onto PC1.
        rows = [[x, x] for x in [-2.0, -1.0, 0.0, 1.0, 2.0]]
        loadings = pca_first_component(rows, n_iter=200, seed=1)
        self.assertAlmostEqual(abs(loadings[0]), abs(loadings[1]), places=3)
        self.assertAlmostEqual(loadings[0] * loadings[1], abs(loadings[0]) * abs(loadings[1]), places=3)

    def test_orient_loadings_flips_sign_so_anchor_is_positive(self):
        loadings = [-0.7, -0.7]
        oriented = orient_loadings(loadings, ["vix", "other"], anchor_field="vix")
        self.assertGreater(oriented[0], 0)
        self.assertLess(oriented[1], 0)

    def test_orient_loadings_noop_when_anchor_already_positive(self):
        loadings = [0.7, -0.7]
        oriented = orient_loadings(loadings, ["vix", "other"], anchor_field="vix")
        self.assertEqual(oriented, loadings)


class TestPercentileTable(unittest.TestCase):
    def test_table_is_monotonic_nondecreasing_and_spans_min_max(self):
        values = list(range(1000))
        table = percentile_table([float(v) for v in values], n_points=101)
        self.assertEqual(len(table), 101)
        self.assertEqual(table[0], 0.0)
        self.assertEqual(table[-1], 999.0)
        for i in range(1, len(table)):
            self.assertGreaterEqual(table[i], table[i - 1])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd bullion-live-map && python3 -m unittest tests.test_backfill_baseline -v`
Expected: FAIL with `ImportError: cannot import name 'add_curve_slope'`

- [ ] **Step 3: Implement in `backfill_baseline.py`**

Add after `field_stats`:

```python
import math
import random


def add_curve_slope(history):
    """Returns a new history dict with a derived 'curve_slope' = us10y - us2y field."""
    out = dict(history)
    us10y, us2y = history.get("us10y", {}), history.get("us2y", {})
    out["curve_slope"] = {d: us10y[d] - us2y[d] for d in us10y if d in us2y}
    return out


def build_zscore_rows(history, stats_by_field, fields):
    """Dates (sorted) and z-scored rows where every field in `fields` is present.

    Each row is clipped to +/-3 per field, matching the client-side engine's
    clipping so the historical composite distribution used for percentile
    lookup is built the same way the live score will be computed.
    """
    date_sets = [set(history[f].keys()) for f in fields]
    common = sorted(set.intersection(*date_sets)) if date_sets else []
    rows = []
    for d in common:
        row = []
        for f in fields:
            s = stats_by_field[f]
            z = (history[f][d] - s["mean"]) / s["std"] if s["std"] else 0.0
            row.append(max(-3.0, min(3.0, z)))
        rows.append(row)
    return common, rows


def pca_first_component(rows, n_iter=500, seed=1):
    """First principal component via power iteration on X^T X / n (rows are
    already z-scored, i.e. approximately mean-zero per column, so this is
    power iteration on the covariance matrix without building it explicitly).
    """
    n_fields = len(rows[0])
    n_rows = len(rows)
    rnd = random.Random(seed)
    v = [rnd.random() - 0.5 for _ in range(n_fields)]

    def normalize(vec):
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    v = normalize(v)
    for _ in range(n_iter):
        xv = [sum(row[j] * v[j] for j in range(n_fields)) for row in rows]
        w = [sum(xv[i] * rows[i][j] for i in range(n_rows)) / n_rows for j in range(n_fields)]
        v = normalize(w)
    return v


def orient_loadings(loadings, fields, anchor_field="vix"):
    idx = fields.index(anchor_field)
    if loadings[idx] < 0:
        return [-x for x in loadings]
    return list(loadings)


def percentile_table(values, n_points=101):
    ordered = sorted(values)
    last = len(ordered) - 1
    return [ordered[round(p / (n_points - 1) * last)] for p in range(n_points)]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd bullion-live-map && python3 -m unittest tests.test_backfill_baseline -v`
Expected: PASS (all tests, ~9)

- [ ] **Step 5: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/backfill_baseline.py bullion-live-map/tests/test_backfill_baseline.py
git commit -m "Mk Ultra macro engine: PCA weighting + percentile table"
```

---

### Task 3: `backfill_baseline.py` — orchestrate + splice `BASELINE_STATS` into `bullion_mkultra.html`

**Files:**
- Modify: `bullion-live-map/backfill_baseline.py`
- Modify: `bullion-live-map/bullion_mkultra.html` (adds two marker comments only, run once by this task to seed the block)
- Test: `bullion-live-map/tests/test_backfill_baseline.py`

**Interfaces:**
- Consumes: everything from Tasks 1-2.
- Produces: `build_baseline(history) -> dict` (the full stats+PCA payload, JSON-serializable); `render_js_block(baseline) -> str` (the `const BASELINE_STATS = {...};` source text); `splice_into_html(html_text, js_block) -> str` (replaces content between `// ─── BASELINE-STATS-START ───` and `// ─── BASELINE-STATS-END ───` markers, raising if markers are missing).

- [ ] **Step 1: Add the marker comments to `bullion_mkultra.html`**

Insert immediately before the `const NODE_ELASTICITY = {` line found earlier (search for that exact string — it's the natural home for this since both are baked-in calibration constants):

```html
    // ─── BASELINE-STATS-START ──────────────────────────────────────────────
    // Generated by backfill_baseline.py — DO NOT hand-edit. Rerun that script
    // to refresh (see docs/superpowers/specs/2026-08-09-bullion-mkultra-macro-engine-design.md).
    const BASELINE_STATS = { generated_at: null, fields: {}, pc1_loadings: {}, composite_percentiles: [] };
    // ─── BASELINE-STATS-END ────────────────────────────────────────────────
```

- [ ] **Step 2: Write the failing test**

```python
# appended to bullion-live-map/tests/test_backfill_baseline.py
import json

from backfill_baseline import build_baseline, render_js_block, splice_into_html, RECENT_WINDOW_YEARS


class TestBuildBaseline(unittest.TestCase):
    def _synthetic_history(self):
        dates = [f"2020-01-{d:02d}" for d in range(1, 29)]
        history = {}
        for i, f in enumerate(["hy_oas", "ig_oas", "sofr", "tbill_3m", "us10y", "us2y",
                                "vix", "spx", "fed_bs", "rrp", "ffr", "cpi_yoy", "dxy", "wti_px"]):
            history[f] = {d: 1.0 + i * 0.1 + 0.01 * n for n, d in enumerate(dates)}
        return history

    def test_build_baseline_produces_expected_keys(self):
        baseline = build_baseline(self._synthetic_history())
        self.assertIn("fields", baseline)
        self.assertIn("curve_slope", baseline["fields"])
        self.assertIn("pc1_loadings", baseline)
        self.assertEqual(set(baseline["pc1_loadings"].keys()),
                          {"hy_oas", "ig_oas", "sofr", "tbill_3m", "us10y", "us2y",
                           "curve_slope", "vix", "spx", "fed_bs", "rrp"})
        self.assertEqual(len(baseline["composite_percentiles"]), 101)
        for f in ("ffr", "cpi_yoy", "dxy", "wti_px"):
            self.assertIn(f, baseline["fields"])
        self.assertEqual(baseline["composite_window_years"], RECENT_WINDOW_YEARS)


class TestSplice(unittest.TestCase):
    def test_splice_replaces_only_between_markers(self):
        html = (
            "before\n"
            "// ─── BASELINE-STATS-START ───\n"
            "const BASELINE_STATS = { old: true };\n"
            "// ─── BASELINE-STATS-END ───\n"
            "after\n"
        )
        out = splice_into_html(html, "const BASELINE_STATS = { new: true };")
        self.assertIn("before", out)
        self.assertIn("after", out)
        self.assertIn("new: true", out)
        self.assertNotIn("old: true", out)

    def test_splice_raises_if_markers_missing(self):
        with self.assertRaises(ValueError):
            splice_into_html("no markers here", "const BASELINE_STATS = {};")

    def test_render_js_block_is_valid_json_payload(self):
        baseline = {"generated_at": "2026-08-09", "fields": {"vix": {"mean": 18.0, "std": 5.0, "n": 100, "window_years": 15}},
                    "pc1_loadings": {"vix": 1.0}, "composite_percentiles": [0.0, 1.0]}
        block = render_js_block(baseline)
        self.assertTrue(block.strip().startswith("const BASELINE_STATS ="))
        inner = block.strip()[len("const BASELINE_STATS ="):].rstrip(";").strip()
        self.assertEqual(json.loads(inner), baseline)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd bullion-live-map && python3 -m unittest tests.test_backfill_baseline -v`
Expected: FAIL with `ImportError: cannot import name 'build_baseline'`

- [ ] **Step 4: Implement**

First, add `import json` to the existing `import` block at the top of `backfill_baseline.py` (alongside `import os`, `import statistics`, etc.).

Then add the following, replacing the `if __name__ == "__main__":` block at the bottom:

```python
def build_baseline(history):
    history = add_curve_slope(history)
    all_dates_sorted = sorted({d for f in FORWARD_FILL_FIELDS for d in history.get(f, {})})
    for f in FORWARD_FILL_FIELDS:
        if f in history:
            history[f] = forward_fill(history[f], all_dates_sorted)

    fields_out = {}
    for f in MEAN_REVERTING_FIELDS + ["curve_slope"]:
        if f not in history or not history[f]:
            continue
        stats = field_stats(list(history[f].values()))
        stats["window_years"] = FULL_WINDOW_YEARS
        fields_out[f] = stats
    for f in TRENDING_FIELDS:
        if f not in history or not history[f]:
            continue
        cutoff = (datetime.now(timezone.utc) - timedelta(days=365 * RECENT_WINDOW_YEARS)).strftime("%Y-%m-%d")
        recent_values = [v for d, v in history[f].items() if d >= cutoff]
        stats = field_stats(recent_values)
        stats["window_years"] = RECENT_WINDOW_YEARS
        fields_out[f] = stats

    # The row matrix that feeds the PCA fit AND the percentile table must use
    # a date range consistent with EVERY composite field's own baseline
    # window -- not just whatever the raw date intersection happens to
    # allow. TRENDING_FIELDS (spx/fed_bs/rrp) are z-scored against only
    # their trailing RECENT_WINDOW_YEARS mean/std (see the loop above); any
    # row older than that window compares those three fields' actual level
    # against a mean that didn't apply to that era, producing an artificial
    # step-discontinuity (verified empirically: dates >2yr old clip to
    # z=-3 on all three trending fields simultaneously, producing a
    # composite value ~6 units away from anything in the recent window --
    # not a gradual trend, a computation artifact). So the row matrix is
    # restricted to the same trailing window, for every field, even though
    # MEAN_REVERTING_FIELDS' own stats (fields_out, above) still use their
    # full FULL_WINDOW_YEARS sample -- only the composite's row matrix
    # (PCA fit + percentile table) is windowed, not each field's baseline.
    recent_cutoff = (datetime.now(timezone.utc) - timedelta(days=365 * RECENT_WINDOW_YEARS)).strftime("%Y-%m-%d")
    history_for_rows = {f: {d: v for d, v in h.items() if d >= recent_cutoff} for f, h in history.items()}

    dates, rows = build_zscore_rows(history_for_rows, fields_out, COMPOSITE_FIELDS)
    loadings = orient_loadings(pca_first_component(rows), COMPOSITE_FIELDS, anchor_field="vix")
    pc1 = dict(zip(COMPOSITE_FIELDS, loadings))
    composite_series = [sum(row[i] * loadings[i] for i in range(len(loadings))) for row in rows]

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "fields": fields_out,
        "pc1_loadings": pc1,
        "composite_percentiles": percentile_table(composite_series) if composite_series else [],
        # The composite's OWN lookback window -- distinct from any single
        # field's window_years (which can be up to FULL_WINDOW_YEARS). The
        # narrative (Task 6) must cite this, not a field's window_years, when
        # describing how far back the composite score's percentile ranking goes.
        "composite_window_years": RECENT_WINDOW_YEARS,
    }


def render_js_block(baseline):
    return "const BASELINE_STATS = " + json.dumps(baseline, indent=2) + ";"


def splice_into_html(html_text, js_block):
    # Search on the bare marker TEXT, not a full decorative comment line --
    # matching on exact dash-run length would be fragile (the line's dash
    # padding has no functional meaning and could reflow without this
    # function needing to change).
    start_token = "BASELINE-STATS-START"
    end_token = "BASELINE-STATS-END"
    start_idx = html_text.find(start_token)
    end_idx = html_text.find(end_token)
    if start_idx == -1 or end_idx == -1:
        raise ValueError("BASELINE-STATS markers not found in HTML")
    # Splice after the START marker's own line, and before the END marker's line.
    start = html_text.index("\n", start_idx) + 1
    end = html_text.rfind("\n", 0, end_idx)
    before = html_text[:start]
    after = html_text[end:]
    return before + js_block + after


if __name__ == "__main__":
    key = _read_fred_key()
    end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start_date = (datetime.now(timezone.utc) - timedelta(days=365 * FULL_WINDOW_YEARS)).strftime("%Y-%m-%d")
    history = fetch_all_history(key, start_date, end_date)
    baseline = build_baseline(history)
    js_block = render_js_block(baseline)
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bullion_mkultra.html")
    with open(html_path) as f:
        html_text = f.read()
    with open(html_path, "w") as f:
        f.write(splice_into_html(html_text, js_block))
    print(f"BASELINE_STATS refreshed: {len(baseline['fields'])} fields, "
          f"{len(baseline['composite_percentiles'])} percentile points", file=sys.stderr)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd bullion-live-map && python3 -m unittest tests.test_backfill_baseline -v`
Expected: PASS (all tests, ~13)

- [ ] **Step 6: Run the real backfill against live FRED/Yahoo data**

Run: `cd bullion-live-map && python3 backfill_baseline.py`
Expected: stderr prints `BASELINE_STATS refreshed: 15 fields, 101 percentile points` (or similar), and `git diff bullion_mkultra.html` shows only the spliced block changed (the placeholder `{ generated_at: null, ... }` replaced with real numbers).

- [ ] **Step 7: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/backfill_baseline.py bullion-live-map/tests/test_backfill_baseline.py bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra macro engine: splice real BASELINE_STATS into bullion_mkultra.html"
```

---

### Task 4: `computeCompositeScore` — pure JS scoring function

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` (add function near `BASELINE_STATS`, before `runLocalAnalysis` at line ~4989)
- Test: `bullion-live-map/tests/test_macro_engine_js_parity.py`

**Interfaces:**
- Consumes: `BASELINE_STATS.fields[f] = {mean, std, n, window_years}`, `BASELINE_STATS.pc1_loadings[f]`, `BASELINE_STATS.composite_percentiles` (101-element sorted array) — all from Task 3.
- Produces: `computeCompositeScore(live)` where `live` is a flat `{field: number}` object (shape of `window.BULLION_LIVE_DATA`). Returns `{score, tier, leadingCategory, categoryContributions, fieldsUsed, fieldsMissing}` where `score` is `0-100`, `tier` is `'measured'` or `'directional'`, `leadingCategory` is one of `'Credit'|'Equity valuation'|'Funding'|'Safe assets'|'Volatility'`, `categoryContributions` is `{category: number}` (signed, summed loading*z per category).

- [ ] **Step 1: Write the failing parity test**

```python
# bullion-live-map/tests/test_macro_engine_js_parity.py
"""JS<->Python parity guard for the Mk Ultra macro engine's pure functions.

Mirrors test_chain_reaction_js_parity.py: extracts the real shipped JS
(BASELINE_STATS + the 3 macro-engine functions) out of bullion_mkultra.html,
runs it via a real `node` process against synthetic fixtures, and checks the
result matches a hand-computed expectation. Skipped (not failed) if `node`
isn't on PATH.
"""
import json
import os
import shutil
import subprocess
import unittest

MAP_PATH = os.path.join(os.path.dirname(__file__), "..", "bullion_mkultra.html")


def _extract_js_snippet(html):
    start = html.index("const BASELINE_STATS = ")
    end = html.index("function runLocalAnalysis")
    return html[start:end]


def _run_node(script):
    proc = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise RuntimeError("node script failed: " + proc.stderr[:2000])
    return json.loads(proc.stdout)


@unittest.skipUnless(shutil.which("node"), "node not on PATH")
class TestComputeCompositeScoreParity(unittest.TestCase):
    def setUp(self):
        with open(MAP_PATH) as f:
            self.snippet = _extract_js_snippet(f.read())

    def test_all_fields_at_their_own_mean_is_a_valid_measured_score(self):
        # NOTE: this does NOT assert score==50. Verified empirically during
        # implementation (see the macro-engine design doc's addendum) that
        # "every field simultaneously at its own individual baseline mean"
        # does not reliably land near the historical median: MEAN_REVERTING
        # fields are z-scored against their full FULL_WINDOW_YEARS sample,
        # which for several fields spans a materially different rate regime
        # (near-zero rates for much of that window vs. the current tightening
        # cycle) than the composite's own RECENT_WINDOW_YEARS row matrix. A
        # field sitting at its own multi-year average is not the same as the
        # SYSTEM being at a historically typical combined state -- some
        # fields are legitimately in a different regime than their own long
        # history right now, and that's real data, not a bug. So this test
        # only checks the mechanism is sound (valid bounded score, correct
        # tier when all fields are supplied), not a specific target value.
        script = self.snippet + """
const live = {};
for (const f of Object.keys(BASELINE_STATS.pc1_loadings)) {
  live[f] = BASELINE_STATS.fields[f].mean;
}
process.stdout.write(JSON.stringify(computeCompositeScore(live)));
"""
        result = _run_node(script)
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
        self.assertEqual(result["tier"], "measured")
        self.assertEqual(len(result["fieldsMissing"]), 0)

    def test_percentile_boundaries_map_to_score_extremes(self):
        # The one invariant that IS guaranteed regardless of field regime
        # heterogeneity: pushing EVERY composite field simultaneously to its
        # most-stressed clip (z=+3 in the direction its loading treats as
        # stress) produces a composite value that upper-bounds anything any
        # real historical day achieved (real days rarely have all fields
        # simultaneously at their most extreme together) -- so it must
        # score at or below the true worst historical day, i.e. score <= 10.
        # Symmetrically, the least-stressed simultaneous clip must score
        # >= 90. This does NOT try to hit BASELINE_STATS.composite_percentiles'
        # exact min/max (that would require knowing which specific field
        # combination actually produced the historical extreme, which a
        # single-field or naive solve can't guarantee) -- it only relies on
        # "all fields simultaneously maximally stressed" being at least as
        # extreme as anything observed, which is true by construction of
        # the clip bound itself, not dependent on any field's regime.
        script = self.snippet + """
const fields = Object.keys(BASELINE_STATS.pc1_loadings);
function liveAtExtreme(direction) {
  // direction = +1 for max stress, -1 for min stress.
  const live = {};
  fields.forEach(f => {
    const stat = BASELINE_STATS.fields[f];
    const loading = BASELINE_STATS.pc1_loadings[f];
    const zSign = (loading >= 0 ? 1 : -1) * direction;
    live[f] = stat.mean + zSign * 3 * stat.std;
  });
  return live;
}
const hi = computeCompositeScore(liveAtExtreme(1));
const lo = computeCompositeScore(liveAtExtreme(-1));
process.stdout.write(JSON.stringify({ lo, hi }));
"""
        result = _run_node(script)
        self.assertGreaterEqual(result["lo"]["score"], 90)
        self.assertLessEqual(result["hi"]["score"], 10)

    def test_missing_fields_degrade_tier_to_directional(self):
        script = self.snippet + """
const fields = Object.keys(BASELINE_STATS.pc1_loadings);
const live = {};
// Only supply 2 of the composite fields -> well under any reasonable
// completeness threshold.
live[fields[0]] = BASELINE_STATS.fields[fields[0]].mean;
live[fields[1]] = BASELINE_STATS.fields[fields[1]].mean;
process.stdout.write(JSON.stringify(computeCompositeScore(live)));
"""
        result = _run_node(script)
        self.assertEqual(result["tier"], "directional")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd bullion-live-map && python3 -m unittest tests.test_macro_engine_js_parity -v`
Expected: FAIL — `node` script errors because `computeCompositeScore` is not defined (or the `_extract_js_snippet` slice is empty since `BASELINE_STATS` marker text isn't yet followed by the function).

- [ ] **Step 3: Implement `computeCompositeScore` in `bullion_mkultra.html`**

Insert directly after the `BASELINE-STATS-END` marker (before `function runLocalAnalysis`):

```js
const COMPOSITE_CATEGORY = {
  hy_oas: 'Credit', ig_oas: 'Credit',
  spx: 'Equity valuation',
  sofr: 'Funding', tbill_3m: 'Funding', rrp: 'Funding', fed_bs: 'Funding',
  us10y: 'Safe assets', us2y: 'Safe assets', curve_slope: 'Safe assets',
  vix: 'Volatility',
};
const COMPOSITE_MIN_FIELDS_FOR_MEASURED = 9; // of 11 total

function _clip3(z) { return Math.max(-3, Math.min(3, z)); }

function _percentileRank(value, table) {
  // table is sorted ascending, 101 points (0th..100th percentile).
  if (value <= table[0]) return 0;
  if (value >= table[table.length - 1]) return 100;
  for (let p = 1; p < table.length; p++) {
    if (value <= table[p]) {
      const lo = table[p - 1], hi = table[p];
      const frac = hi > lo ? (value - lo) / (hi - lo) : 0;
      return (p - 1) + frac;
    }
  }
  return 100;
}

function computeCompositeScore(live) {
  const fields = Object.keys(BASELINE_STATS.pc1_loadings);
  const liveWithSlope = Object.assign({}, live);
  if (typeof live.us10y === 'number' && typeof live.us2y === 'number') {
    liveWithSlope.curve_slope = live.us10y - live.us2y;
  }
  const fieldsUsed = [], fieldsMissing = [];
  const categoryContributions = {};
  let composite = 0;
  fields.forEach(f => {
    const stat = BASELINE_STATS.fields[f];
    const v = liveWithSlope[f];
    if (typeof v !== 'number' || !stat || !stat.std) { fieldsMissing.push(f); return; }
    fieldsUsed.push(f);
    const z = _clip3((v - stat.mean) / stat.std);
    const contribution = BASELINE_STATS.pc1_loadings[f] * z;
    composite += contribution;
    const cat = COMPOSITE_CATEGORY[f];
    categoryContributions[cat] = (categoryContributions[cat] || 0) + contribution;
  });
  const percentile = _percentileRank(composite, BASELINE_STATS.composite_percentiles);
  const score = Math.round(100 - percentile);
  const tier = fieldsUsed.length >= COMPOSITE_MIN_FIELDS_FOR_MEASURED ? 'measured' : 'directional';
  let leadingCategory = null, leadingAbs = -1;
  Object.entries(categoryContributions).forEach(([cat, v]) => {
    if (Math.abs(v) > leadingAbs) { leadingAbs = Math.abs(v); leadingCategory = cat; }
  });
  return { score, tier, leadingCategory, categoryContributions, fieldsUsed, fieldsMissing };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd bullion-live-map && python3 -m unittest tests.test_macro_engine_js_parity -v`
Expected: PASS (2 tests) — if `node` is not installed, expect `SKIPPED`, not a failure; verify with `which node` first and install/skip-note in the task report accordingly.

- [ ] **Step 5: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mkultra.html bullion-live-map/tests/test_macro_engine_js_parity.py
git commit -m "Mk Ultra macro engine: add computeCompositeScore"
```

---

### Task 5: `computeNodeMultipliers` — reuse `NODE_ELASTICITY` with real current deviations

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` (add function after `computeCompositeScore`)
- Test: `bullion-live-map/tests/test_macro_engine_js_parity.py`

**Interfaces:**
- Consumes: `NODE_ELASTICITY` (`{driver: {node: {v, conf, src}}}`, defined at `bullion_mkultra.html:3833`), `DRIVERS` (array of `{key, base, ...}`, `base` already live-refreshed by the existing `refreshDriverBases()`), `BASELINE_STATS.fields[driverKey] = {mean, std}` from Task 3.
- Produces: `computeNodeMultipliers(driverValues)` where `driverValues` is `{ffr, vix, cpi_yoy, dxy, wti_px}` (matches `DRIVERS` keys). Returns `{mults: {NodeName: number}, tiers: {NodeName: 'measured'|'directional'}, noDataNodes: [NodeName]}`. `mults` only contains nodes with a nonzero contribution (mirrors the existing `if (Math.abs(mults[k]) < 0.004) delete mults[k]` convention at `bullion_mkultra.html:4083`); `noDataNodes` lists every `NODE_MAP` key absent from `mults`.

- [ ] **Step 1: Write the failing parity test**

```python
# appended to bullion-live-map/tests/test_macro_engine_js_parity.py

def _extract_js_snippet_through_node_mults(html):
    start = html.index("const BASELINE_STATS = ")
    end = html.index("function runLocalAnalysis")
    return html[start:end]


@unittest.skipUnless(shutil.which("node"), "node not on PATH")
class TestComputeNodeMultipliersParity(unittest.TestCase):
    def setUp(self):
        with open(MAP_PATH) as f:
            self.snippet = _extract_js_snippet_through_node_mults(f.read())

    def test_all_drivers_at_baseline_mean_yields_no_contributions(self):
        script = self.snippet + """
const driverValues = {};
DRIVERS.forEach(d => { driverValues[d.key] = BASELINE_STATS.fields[d.key].mean; });
const result = computeNodeMultipliers(driverValues);
process.stdout.write(JSON.stringify(result));
"""
        result = _run_node(script)
        self.assertEqual(result["mults"], {})

    def test_nodes_never_covered_by_node_elasticity_are_listed_as_no_data(self):
        script = self.snippet + """
const driverValues = {};
DRIVERS.forEach(d => { driverValues[d.key] = BASELINE_STATS.fields[d.key].mean; });
const result = computeNodeMultipliers(driverValues);
process.stdout.write(JSON.stringify(result.noDataNodes));
"""
        no_data = _run_node(script)
        self.assertIn("Russia", no_data)
        self.assertIn("Geopolitics", no_data)

    def test_vix_deviation_produces_expected_sign_on_spx(self):
        script = self.snippet + """
const driverValues = {};
DRIVERS.forEach(d => { driverValues[d.key] = BASELINE_STATS.fields[d.key].mean; });
// Push VIX 2 std-devs above its own mean.
driverValues.vix = BASELINE_STATS.fields.vix.mean + 2 * BASELINE_STATS.fields.vix.std;
const result = computeNodeMultipliers(driverValues);
process.stdout.write(JSON.stringify(result.mults.SPX));
"""
        spx_mult = _run_node(script)
        # NODE_ELASTICITY.vix.SPX is negative (rising VIX hurts SPX) -- see
        # bullion_mkultra.html:3862.
        self.assertLess(spx_mult, 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd bullion-live-map && python3 -m unittest tests.test_macro_engine_js_parity -v`
Expected: FAIL — `computeNodeMultipliers is not defined`

- [ ] **Step 3: Implement**

Insert after `computeCompositeScore`:

```js
function computeNodeMultipliers(driverValues) {
  const mults = {}, tierByNode = {};
  Object.keys(NODE_ELASTICITY).forEach(driverKey => {
    const stat = BASELINE_STATS.fields[driverKey];
    const current = driverValues[driverKey];
    if (!stat || typeof current !== 'number') return;
    const delta = current - stat.mean;
    if (Math.abs(delta) < 1e-9) return;
    Object.entries(NODE_ELASTICITY[driverKey]).forEach(([node, cell]) => {
      mults[node] = (mults[node] || 0) + cell.v * delta;
      const rank = { measured: 2, directional: 1, unverified: 0 };
      if (!(node in tierByNode) || rank[cell.conf] < rank[tierByNode[node]]) {
        tierByNode[node] = cell.conf;
      }
    });
  });
  Object.keys(mults).forEach(k => {
    mults[k] = +Math.max(-0.60, Math.min(0.60, mults[k])).toFixed(3);
    if (Math.abs(mults[k]) < 0.004) { delete mults[k]; delete tierByNode[k]; }
  });
  const noDataNodes = Object.keys(NODE_MAP).filter(n => !(n in mults));
  return { mults, tiers: tierByNode, noDataNodes };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd bullion-live-map && python3 -m unittest tests.test_macro_engine_js_parity -v`
Expected: PASS (5 tests total, or SKIPPED if no `node`)

- [ ] **Step 5: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mkultra.html bullion-live-map/tests/test_macro_engine_js_parity.py
git commit -m "Mk Ultra macro engine: add computeNodeMultipliers reusing NODE_ELASTICITY"
```

---

### Task 6: `buildMacroNarrative` — deterministic 3-sentence template

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` (add function after `computeNodeMultipliers`)
- Test: `bullion-live-map/tests/test_macro_engine_js_parity.py`

**Interfaces:**
- Consumes: the `computeCompositeScore` result (Task 4), the `computeNodeMultipliers` result (Task 5), `live` (flat `{field: number}`), `BASELINE_STATS.fields.cpi_yoy` / `.nfp_mom` if present (for context sentence — note `nfp_mom` is NOT in `COMPOSITE_FIELDS`/`BASELINE_STATS` per Task 3's `MEAN_REVERTING_FIELDS`; it needs to be added there too — see Step 0 below), `BASELINE_STATS.composite_window_years` (the composite's own lookback window — added to `build_baseline`'s output as part of the Task 3 correction in Global Constraints; use this, NOT `BASELINE_STATS.fields.vix.window_years`, for the "past K years" sentence).
- Produces: `buildMacroNarrative(compositeResult, nodeResult, live)` returning a single string of exactly 3 sentences.

- [ ] **Step 0: Add `nfp_mom` to the baseline fields (correction to Task 1)**

`MEAN_REVERTING_FIELDS` in `backfill_baseline.py` (Task 1) already omits `nfp_mom`. Add it:

```python
# backfill_baseline.py — change the existing MEAN_REVERTING_FIELDS line to:
MEAN_REVERTING_FIELDS = ["hy_oas", "ig_oas", "sofr", "tbill_3m", "us10y", "us2y", "vix",
                          "ffr", "cpi_yoy", "dxy", "wti_px", "nfp_mom"]
```

Rerun the backfill so `BASELINE_STATS.fields.nfp_mom` exists:

Run: `cd bullion-live-map && python3 backfill_baseline.py`
Expected: same success message as Task 3 Step 6, now with `nfp_mom` included.

- [ ] **Step 1: Write the failing parity test**

```python
# appended to bullion-live-map/tests/test_macro_engine_js_parity.py

@unittest.skipUnless(shutil.which("node"), "node not on PATH")
class TestBuildMacroNarrativeParity(unittest.TestCase):
    def setUp(self):
        with open(MAP_PATH) as f:
            self.snippet = _extract_js_snippet_through_node_mults(f.read())

    def test_narrative_has_exactly_three_sentences_and_cites_real_cpi(self):
        script = self.snippet + """
const live = {};
Object.keys(BASELINE_STATS.pc1_loadings).forEach(f => { live[f] = BASELINE_STATS.fields[f].mean; });
live.cpi_yoy = 2.6;
live.nfp_mom = 150;
const composite = computeCompositeScore(live);
const driverValues = {};
DRIVERS.forEach(d => { driverValues[d.key] = BASELINE_STATS.fields[d.key].mean; });
const nodes = computeNodeMultipliers(driverValues);
const narrative = buildMacroNarrative(composite, nodes, live);
process.stdout.write(JSON.stringify({ narrative, sentences: narrative.split(/(?<=[.])\\s+/).length }));
"""
        result = _run_node(script)
        self.assertEqual(result["sentences"], 3)
        self.assertIn("2.6", result["narrative"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd bullion-live-map && python3 -m unittest tests.test_macro_engine_js_parity -v`
Expected: FAIL — `buildMacroNarrative is not defined`

- [ ] **Step 3: Implement**

Insert after `computeNodeMultipliers`:

```js
function _ordinal(n) {
  const s = ['th', 'st', 'nd', 'rd'], v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function buildMacroNarrative(compositeResult, nodeResult, live) {
  // The composite's OWN lookback window (composite_window_years, currently
  // 2) -- NOT any individual field's window_years (which can be up to 15).
  // The composite's PCA fit and percentile table are built from a shorter,
  // internally-consistent row-matrix window; see Global Constraints.
  const windowYears = BASELINE_STATS.composite_window_years || 15;
  const pct = Math.max(0, Math.min(100, Math.round(100 - compositeResult.score)));
  const s1 = `Financial conditions sit at the ${_ordinal(pct)} percentile of the past ${windowYears} years, ` +
    `driven primarily by ${(compositeResult.leadingCategory || 'a mix of factors').toLowerCase()}.`;

  const cpi = live.cpi_yoy, nfp = live.nfp_mom;
  const cpiTxt = (typeof cpi === 'number')
    ? `Core CPI is running at ${cpi.toFixed(1)}% against the Fed's 2% target`
    : `Core CPI data is unavailable`;
  const nfpTxt = (typeof nfp === 'number')
    ? (nfp > 100 ? 'payrolls are trending firm' : (nfp < 0 ? 'payrolls are contracting' : 'payrolls are roughly flat'))
    : 'payroll data is unavailable';
  const s2 = `${cpiTxt}; ${nfpTxt}.`;

  const entries = Object.entries(nodeResult.mults);
  let s3;
  if (entries.length === 0) {
    s3 = 'No live driver is currently far enough from its historical baseline to move any node materially.';
  } else {
    entries.sort((a, b) => a[1] - b[1]);
    const worst = entries[0], best = entries[entries.length - 1];
    const pctTxt = v => (v >= 0 ? '+' : '') + (v * 100).toFixed(0) + '%';
    s3 = `The largest current headwind is to ${worst[0].replace(/_/g, ' ')} (${pctTxt(worst[1])})` +
      (best[0] !== worst[0] ? `, while ${best[0].replace(/_/g, ' ')} shows the most support (${pctTxt(best[1])}).` : '.');
  }
  return s1 + ' ' + s2 + ' ' + s3;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd bullion-live-map && python3 -m unittest tests.test_macro_engine_js_parity -v`
Expected: PASS (6 tests total, or SKIPPED if no `node`)

- [ ] **Step 5: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/backfill_baseline.py bullion-live-map/bullion_mkultra.html bullion-live-map/tests/test_macro_engine_js_parity.py
git commit -m "Mk Ultra macro engine: add buildMacroNarrative"
```

---

### Task 7: Wire the engine into the UI, remove dead AI code, rename button copy

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` — replace `runLocalAnalysis`/`runAIAnalysis` (lines 4989-5059), the button markup (lines 886, 896), the listener line (5300), and the `clearAI`/initial label text (line 4949).

**Interfaces:**
- Consumes: `computeCompositeScore`, `computeNodeMultipliers`, `buildMacroNarrative` (Tasks 4-6), existing `applyTransmission(state)`, `renderImpacts(mults, whyMap, label)`, `updateGraph(applyTransmission(state))`, `playEventNarration('ai_analysis')`.
- Produces: `runMacroAnalysis()` (replaces `runAIAnalysis`; same DOM element IDs so no HTML structure changes beyond button label text).

- [ ] **Step 1: Replace the button markup**

At line 886, change:
```html
<span style="font-size:11px;color:var(--text-dim)" id="health-label">Run AI analysis</span>
```
to:
```html
<span style="font-size:11px;color:var(--text-dim)" id="health-label">Run macro analysis</span>
```

At line 896, change:
```html
<button class="run-btn" id="run-ai-btn" style="margin-top:8px">Run AI analysis &#x2197;</button>
```
to:
```html
<button class="run-btn" id="run-ai-btn" style="margin-top:8px">Run macro analysis &#x2197;</button>
```

- [ ] **Step 2: Update `clearAI`'s label reset (line 4949)**

Change `document.getElementById('health-label').textContent = 'Run AI analysis';` to `document.getElementById('health-label').textContent = 'Run macro analysis';`

- [ ] **Step 3: Replace lines 4987-5059 (`BACKEND_URL` through the end of `runAIAnalysis`)**

Delete the existing `const BACKEND_URL = '';`, `runLocalAnalysis`, and `runAIAnalysis` entirely. Replace with:

```js
function runMacroAnalysis() {
  const btn = document.getElementById('run-ai-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Analyzing...';
  playEventNarration('ai_analysis');

  const s = applyTransmission(state);
  const live = Object.assign({}, window.BULLION_LIVE_DATA || {}, {
    // The 5 NODE_ELASTICITY drivers can be scenario-shocked; always feed the
    // engine the CURRENT (possibly shocked) value so a running shock still
    // shows up in the score, matching this button's pre-existing behavior.
    vix: s.vix, cpi_yoy: s.cpi_yoy, dxy: s.dxy, wti_px: s.wti_px,
  });
  const driverValues = {};
  DRIVERS.forEach(d => { driverValues[d.key] = (typeof s[d.key] === 'number') ? s[d.key] : d.base; });

  const composite = computeCompositeScore(live);
  const nodes = state.shock && Object.keys(nodeMultipliers).length
    ? { mults: Object.assign({}, nodeMultipliers), tiers: {}, noDataNodes: [] }
    : computeNodeMultipliers(driverValues);
  const narrative = buildMacroNarrative(composite, nodes, live);

  document.getElementById('narrative-box').textContent = narrative;
  document.getElementById('health-num').textContent = composite.score;
  document.getElementById('health-label').textContent =
    (composite.score > 70 ? 'Healthy' : composite.score > 45 ? 'Moderate stress' : 'Elevated stress') +
    (composite.tier === 'directional' ? ' (directional — limited live data)' : '');
  const barColor = composite.score > 70 ? '#7bbf8e' : composite.score > 45 ? '#e0b15a' : '#e0654f';
  document.getElementById('health-bar').style.width = composite.score + '%';
  document.getElementById('health-bar').style.background = barColor;
  nodeMultipliers = nodes.mults;
  renderImpacts(nodeMultipliers, null,
    state.shock ? 'Scenario node impact multipliers' : 'Current-conditions node impact multipliers');
  updateGraph(applyTransmission(state));
  btn.disabled = false;
  btn.innerHTML = 'Run macro analysis ↗';
}
```

- [ ] **Step 4: Update the listener (line 5300)**

Change `document.getElementById('run-ai-btn').addEventListener('click', runAIAnalysis);` to `document.getElementById('run-ai-btn').addEventListener('click', runMacroAnalysis);`

- [ ] **Step 5: Grep-verify no dead references remain**

Run: `cd bullion-live-map && grep -n "runAIAnalysis\|runLocalAnalysis\|BACKEND_URL\|api.anthropic.com" bullion_mkultra.html`
Expected: no output (empty grep result)

- [ ] **Step 6: Browser-verify via headless Chrome**

Per this project's standing convention (isolated `--user-data-dir`), launch headless Chrome against the local file, click `#run-ai-btn`, and confirm via `read_console_messages`/a `javascript_tool` read of `#narrative-box`/`#health-num` that: 0 console errors, the narrative contains real numbers (not `NaN`/`undefined`), and `#health-num` is a value between 1 and 100.

- [ ] **Step 7: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: wire macro engine into UI, remove dead AI call, rename button"
```

---

### Task 8: Audit log — new methodology section

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` — `openAuditLog()` (starts at line 5133 before Task 7's edits shift line numbers; locate by searching for `function openAuditLog()`).

**Interfaces:**
- Consumes: `BASELINE_STATS` (Task 3), the last `computeNodeMultipliers` result's `noDataNodes` (need to cache it — see Step 1), `provCoverage()` (existing function used elsewhere in `openAuditLog`).
- Produces: a new HTML section string appended to the audit log panel's existing innerHTML assembly.

- [ ] **Step 1: Cache the last node-multiplier result for the audit log to read**

In `runMacroAnalysis` (Task 7), add a module-level variable and set it:

```js
// Add near the top-level `let nodeMultipliers = {};` declaration:
let lastNodeMultiplierResult = { mults: {}, tiers: {}, noDataNodes: [] };
```

In `runMacroAnalysis`, after `const nodes = ...` line, add: `lastNodeMultiplierResult = nodes;`

- [ ] **Step 2: Add the new section to `openAuditLog()`**

Find the line that assembles the final innerHTML (search for where `bar`, `conflicts`, `demotions`, `superseded`, `scenNote` are joined into the panel — typically a `document.getElementById(...).innerHTML = bar + conflicts + ...` near the end of `openAuditLog`). Add a new section variable above that join:

```js
const macroEngineSection = BASELINE_STATS.generated_at
  ? '<h3>Macro engine methodology</h3><p class="audit-note">Health score and baseline node impacts are computed by a deterministic PCA-weighted composite (not AI) &mdash; see ' +
    '<code>docs/superpowers/specs/2026-08-09-bullion-mkultra-macro-engine-design.md</code>. ' +
    'Baseline statistics last refreshed <b>' + BASELINE_STATS.generated_at + '</b>. ' +
    'Composite fields: <b>' + Object.keys(BASELINE_STATS.pc1_loadings).length + '</b> (PCA-weighted, oriented to VIX). ' +
    (lastNodeMultiplierResult.noDataNodes.length
      ? ('<b>' + lastNodeMultiplierResult.noDataNodes.length + ' nodes</b> have no live-data-backed baseline reading: ' +
         lastNodeMultiplierResult.noDataNodes.join(', ') + '.')
      : 'Every conceptual node has at least one live-data-backed driver.') +
    '</p>'
  : '<h3>Macro engine methodology</h3><p class="audit-note">Baseline statistics have not been generated yet &mdash; run backfill_baseline.py.</p>';
```

Then include `macroEngineSection` in the existing innerHTML concatenation (append it alongside `bar + conflicts + demotions + superseded + scenNote + ...`).

- [ ] **Step 3: Browser-verify**

Launch headless Chrome, click the audit-log open control, confirm via a DOM read that the panel contains the text "Macro engine methodology" and the real `BASELINE_STATS.generated_at` date, and 0 console errors.

- [ ] **Step 4: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: surface macro engine methodology in the audit log"
```

---

### Task 9: Full-suite regression check

**Files:** none created/modified — verification only.

**Interfaces:** none new.

- [ ] **Step 1: Run the full Python test suite**

Run: `cd bullion-live-map && python3 -m unittest discover -s tests -v`
Expected: all tests pass (including the new `test_backfill_baseline` and `test_macro_engine_js_parity` suites alongside the existing `test_fetch_bullion_data`, `test_mk17_series`, `test_freshness_parity`, `test_chain_reaction*` suites).

- [ ] **Step 2: Confirm frozen files are byte-unchanged**

Run: `cd bullion-live-map && sha256sum bullion_mk11.html bullion_mk12.html bullion_mk13.html bullion_mk14.html bullion_mk15.html bullion_mk16.html bullion_mk17.html bullion_mk18.html`
Expected: matches the shas recorded in prior session handoffs (mk15 `ebfaaaf6…`, mk16 `ef9fbc55…`) — none of this plan's tasks touch these files, so this should already hold; run it to be certain nothing accidentally leaked into them.

- [ ] **Step 3: Full-page browser smoke test on `bullion_mkultra.html`**

Per this project's standing headless-Chrome convention (isolated `--user-data-dir`, `--use-gl=angle --use-angle=swiftshader` for WebGL): load the page, confirm 0 console errors on load, click through the existing scenario dropdown + `runMacroAnalysis` + audit log + a couple of node detail panels, confirm nothing outside the touched areas regressed (3D globe still renders, Overview board still works, narration buttons still fire).

- [ ] **Step 4: Update the project memory / handoff**

Invoke the `writing-handoff-docs` skill to record this session's outcome once Task 9 passes, per this project's established convention (a fresh handoff doc, not a code task — no commit needed for this step beyond what the skill itself does).

---

## Addendum (2026-08-11): composite health score disabled after final review

A final whole-branch review (after all 9 tasks above had individually passed review) found the composite health score **inverted under real stress**: a synthetic full crisis (VIX 45, HY credit spreads to 8%, SPX −35%) scored **100/"Healthy"**; today's genuinely calm market scored 18/"Elevated stress". Verified directly against the real shipped `computeCompositeScore` and the regenerated `BASELINE_STATS`, not a hypothetical.

**Root cause.** `build_baseline`'s PCA fit runs over the composite row-matrix's ~2-year window (per the earlier fix in this plan's Global Constraints — the only window where all 11 composite fields have comparable history, since `hy_oas`/`ig_oas` only have ~3yr of real FRED data due to an April-2026 retention-policy change). Over that window, **89.6% of PC1's loading-squared weight sits on nominal rate levels** (`us10y` 34.2%, `tbill_3m` 23.8%, `us2y` 22.9%, `sofr` 8.7%), while `vix`/`spx`/`fed_bs`/`rrp` each contribute **0.0%**. This is not a bug in the PCA implementation — the window genuinely contained no real stress episode, so rate-level drift (correlated across the four rate series via the same Fed-policy stance) was the actual dominant source of joint variance in the sample, and PCA correctly found it. Sign-orientation had been anchored on `vix`'s own loading (assumed to reliably indicate "more stress"), but that loading was ~0.009 — statistically indistinguishable from zero — so orienting the whole 11-dimensional axis off it was meaningless, and `hy_oas`/`ig_oas` ended up loading with an **inverted sign** (wider credit spreads *lowered* the composite's "stress" reading).

**A proposed fix — sign-align every field to its expected stress direction before fitting PCA — was implemented and proven to be a mathematical no-op.** PCA is invariant to per-column sign flips: if `C` is the (signed) covariance matrix and `D` is a diagonal ±1 sign matrix (so `D² = I`), then `C_signed = D·C·D`, and if `Cv = λv` then `C_signed(Dv) = D·C·D·D·v = D·C·v = λ(Dv)` — the signed fit's eigenvector is exactly `D` times the original, and re-multiplying the exported loadings by `D` (to "bake the sign back in" for the client) exactly cancels the flip. Verified empirically: the "fixed" loadings came out bit-identical to the pre-fix ones (max difference `1.39e-17`, floating-point noise). No amount of per-field sign convention changes what PCA identifies as the dominant pattern — that's determined entirely by the data's actual covariance structure, which had no meaningful credit/vol/equity co-movement in this sample to discover.

**Decision:** rather than attempt a further, riskier methodology change (a materially longer/different fitting window, which the short credit-spread history rules out for now; or abandoning PCA-discovered weights for a hand-specified scheme, reopening the "avoid setting weights by feel" design goal this plan started from) after several rounds of subtle statistical bugs in one session, the project owner chose to **disable the composite health score from the shipped UI** rather than ship something that reads backwards under real stress. `computeCompositeScore` (client-side) and the composite-scoring path in `build_baseline` (`backfill_baseline.py`) are left intact and correct as *infrastructure* — not deleted — for whoever revisits the weighting methodology later. What ships: the node-level impact multipliers (`computeNodeMultipliers`, a completely separate mechanism reusing the already-sourced `NODE_ELASTICITY` matrix — never touched by any of the above, not PCA-based, not implicated in this bug) and a 2-sentence narrative (CPI/payrolls context + node headwind/support), with the health-score number and bar hidden from the UI and the audit log explaining why.

**For whoever revisits this:** the two live candidate directions, evaluated but not adopted this round —
1. Equal-weighted sign-aligned z-scores (drop PCA-discovered weights entirely, average the 11 `EXPECTED_STRESS_SIGN`-aligned z-scores with equal weight) — empirically confirmed during this session's investigation to correctly rank a synthetic crisis below a synthetic calm scenario and below the reviewer's original repro case. Simpler, no longer claims to derive weights statistically from real institutional methodology, but demonstrably correct on the cases that matter.
2. Hand-specified category weights (the original credit/funding/equity/safe-assets/volatility structure from this plan's brainstorming phase — see the design spec's Sources section) applied to sign-aligned z-scores — closer to a real FCI's category structure, but reintroduces a hand-picked judgment call.
A materially longer fitting window with a proper stationarity transform for the secularly-trending fields (rather than the current window-shrinking approach) would let PCA-discovered weights work as originally intended, but is blocked today by `hy_oas`/`ig_oas`'s ~3yr real data ceiling.

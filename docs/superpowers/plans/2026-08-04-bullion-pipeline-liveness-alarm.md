# Bullion Pipeline-Liveness Alarm Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a stale or dead `bullion-live-map` data pipeline impossible to miss, via two independent layers — a map banner that reads the data file's own heartbeat, and a GitHub-issue alarm that fires the same day a scheduled run fails.

**Architecture:** Layer 1 adds a pure `pipelineLiveness()` function (mirroring the existing `freshnessVerdict()`) plus a DOM-rendering wrapper, wired into the same `renderLiveBadge` call path that already updates on every metrics refresh, in both live map files (`bullion_mk18.html`, `bullion_mkultra.html`). Layer 2 adds `issues: write` permission and three `actions/github-script` steps to `.github/workflows/daily-data.yml` that open/comment/close a labelled issue assigned to the repo owner, using only the built-in `GITHUB_TOKEN`.

**Tech Stack:** Vanilla JS (no framework) inside static HTML files, Python `unittest`, a browser-based marker-extraction test harness (`tests/freshness_test.html`), GitHub Actions YAML, `actions/github-script@v7`.

## Global Constraints

- **Tolerance: 3 days** for `pipelineLiveness` — copied verbatim from the spec (`docs/superpowers/specs/2026-08-04-bullion-pipeline-liveness-alarm-design.md`).
- **`unknown` must show the banner.** Never fail open into silence — this is the direct lesson from the `weekly`-cadence bug documented in the outage handoff.
- **Applies only to `bullion_mk18.html` and `bullion_mkultra.html`.** `bullion_mk11.html`–`bullion_mk17.html` are frozen byte-for-byte; never edit them.
- **No new secrets.** Layer 2 uses only `secrets.GITHUB_TOKEN`. SMTP/email was explicitly rejected in the spec.
- **`#pipeline-alarm[hidden]{display:none}` must ship from the start** — an id-selector `display` rule otherwise beats the UA `[hidden]` rule (exact bug the `#board-view` element shipped once already).
- **Repo:** `SinbadTheExplorer/claudekit` on GitHub, work happens directly on `main` (no feature branch, by standing project convention).
- **`gh` CLI and `pyyaml` are NOT installed in this environment.** Any GitHub API call in this plan uses `curl` with a token pulled via `git credential fill`, never `gh`. YAML syntax is validated by the live `workflow_dispatch` run in Task 4, not a static linter.

---

## Task 1: Pure liveness logic — `pipelineLiveness`, `pipelineAlarmMessage`, `renderPipelineAlarm`

**Files:**
- Modify: `bullion-live-map/bullion_mk18.html` (insert after the `FRESHNESS-VERDICT-END` marker, currently line 4715)
- Modify: `bullion-live-map/bullion_mkultra.html` (insert after the `FRESHNESS-VERDICT-END` marker, currently line 5425 — same surrounding text as mk18, confirmed byte-identical by diff)
- Modify: `bullion-live-map/tests/freshness_test.html` (new extraction block + checks)
- Modify: `bullion-live-map/tests/test_freshness_parity.py` (new parity check)

**Interfaces:**
- Produces: `PIPELINE_TOLERANCE_DAYS` (number, `3`), `pipelineLiveness(generatedAt, nowISO, toleranceDays) -> {state: 'fresh'|'stale'|'unknown', ageDays: number|null}`, `pipelineAlarmMessage(liveness, generatedAt) -> string`, `renderPipelineAlarm(bar, isLive, prov, nowISO) -> void` (sets `bar.hidden` and `bar.textContent`; `prov` is any object shaped `{generatedAt}` or `null`). Task 2 calls `renderPipelineAlarm` from the `updateMetrics` call site and reads `PIPELINE_TOLERANCE_DAYS` nowhere else (it's private to this block).
- Consumes: nothing from other tasks.

Both `bullion_mk18.html` and `bullion_mkultra.html` have byte-identical text around every anchor point used below (verified). Every step below is applied to **both** files unless noted.

- [ ] **Step 1: Add the new test block to `tests/freshness_test.html`**

Find this exact tail of the file (the end of the `provenanceSummaryText` block, right before the `.catch`):

```js
        '9 of 10 measured fields are missing from this data file: us2y, us10y, vix, ffr, wti_px, cpi_yoy, nfp_mom, dxy, spx.');
    }
  })
  .catch(e => results.push('FAIL  harness error: ' + e.message))
```

Replace it with (inserting the new block between the closing `}` of the summary block and the `})`):

```js
        '9 of 10 measured fields are missing from this data file: us2y, us10y, vix, ffr, wti_px, cpi_yoy, nfp_mom, dxy, spx.');
    }

    // ── pipelineLiveness / renderPipelineAlarm: the stale-pipeline banner ──
    const m6 = html.match(/PIPELINE-LIVENESS-START([\s\S]*?)PIPELINE-LIVENESS-END/);
    if (!m6) { check('pipelineLiveness present', false, true); }
    else {
      // The leading '\n' is REQUIRED — see the note on the freshnessVerdict
      // block above: the captured source ends inside the closing marker
      // line's '// ───' comment, so appended code without a newline first
      // is silently swallowed by it.
      (0, eval)(m6[1].replace(/^[^\n]*\n/, '')
        + '\n; window.pipelineLiveness = pipelineLiveness;'
        + '  window.pipelineAlarmMessage = pipelineAlarmMessage;'
        + '  window.renderPipelineAlarm = renderPipelineAlarm;'
        + '  window.PIPELINE_TOLERANCE_DAYS = PIPELINE_TOLERANCE_DAYS;');

      const PTODAY = '2026-08-04';
      check('pipeline tolerance is 3 days',
        window.PIPELINE_TOLERANCE_DAYS, 3);
      check('generated today is fresh',
        pipelineLiveness('2026-08-04T09:41:38Z', PTODAY, 3), {state:'fresh', ageDays:0});
      check('exactly at tolerance is fresh',
        pipelineLiveness('2026-08-01T00:00:00Z', PTODAY, 3), {state:'fresh', ageDays:3});
      check('one day past tolerance is stale',
        pipelineLiveness('2026-07-31T00:00:00Z', PTODAY, 3), {state:'stale', ageDays:4});
      check('long-dead pipeline is stale',
        pipelineLiveness('2026-07-20T09:41:38Z', PTODAY, 3), {state:'stale', ageDays:15});
      check('missing timestamp is unknown',
        pipelineLiveness(null, PTODAY, 3), {state:'unknown', ageDays:null});
      check('unparseable timestamp is unknown',
        pipelineLiveness('not-a-real-timestamp', PTODAY, 3), {state:'unknown', ageDays:null});

      check('stale and unknown use distinct wording',
        pipelineAlarmMessage({state:'stale', ageDays:15}, '2026-07-20T09:41:38Z')
          !== pipelineAlarmMessage({state:'unknown', ageDays:null}, null),
        true);

      // renderPipelineAlarm DOM assertions — a detached element is enough;
      // the function only ever touches .hidden/.textContent on what it's given.
      const staleProv   = {generatedAt: '2026-07-20T09:41:38Z'};
      const freshProv   = {generatedAt: '2026-08-04T09:41:38Z'};
      const unknownProv = {generatedAt: null};

      let bar = document.createElement('div');
      renderPipelineAlarm(bar, true, staleProv, PTODAY);
      check('bar shown for a stale envelope', bar.hidden, false);

      bar = document.createElement('div');
      renderPipelineAlarm(bar, true, freshProv, PTODAY);
      check('bar hidden for a fresh envelope', bar.hidden, true);

      bar = document.createElement('div');
      renderPipelineAlarm(bar, false, staleProv, PTODAY);
      check('bar hidden when live data is toggled off, even if stale', bar.hidden, true);

      bar = document.createElement('div');
      renderPipelineAlarm(bar, true, unknownProv, PTODAY);
      check('bar shown for an envelope with no generated_at', bar.hidden, false);
    }
  })
  .catch(e => results.push('FAIL  harness error: ' + e.message))
```

- [ ] **Step 2: Run the browser test and confirm it currently fails**

```bash
cd bullion-live-map && python3 -m http.server 8901 &
```

Then, using the `headless-chrome-verification` skill's `cdp_probe.mjs` template (copy it to a scratch path, point it at `http://localhost:8901/tests/freshness_test.html`, poll `#out`'s `textContent` until it stops reading `running…`):

Expected: `pipelineLiveness present` reads `FAIL` (marker not found yet) — everything else in the file still passes. This confirms the test actually exercises new code before any implementation exists.

- [ ] **Step 3: Implement the block in `bullion_mk18.html`**

Find (the end of the existing freshness-verdict block):

```
function freshnessVerdict(cadence, published, today, overrideDays) {
  if (published == null || cadence === 'fomc') return { state: 'unknown', ageDays: null };
  const tolerance = (overrideDays != null) ? overrideDays : CADENCE_TOLERANCE_DAYS[cadence];
  if (tolerance == null) return { state: 'unknown', ageDays: null };
  // Parse as UTC midnight so DST never shifts a day boundary.
  const ms = Date.parse(today + 'T00:00:00Z') - Date.parse(published + 'T00:00:00Z');
  if (Number.isNaN(ms)) return { state: 'unknown', ageDays: null };
  const ageDays = Math.round(ms / 86400000);
  return { state: ageDays > tolerance ? 'flagged' : 'fresh', ageDays: ageDays };
}
// ─── FRESHNESS-VERDICT-END ──────────────────────────────────────────────────

// ─── NORMALISE-ENVELOPE-START ───────────────────────────────────────────────
```

Replace with (inserting the new block between the two, keeping both existing markers exactly as they are):

```
function freshnessVerdict(cadence, published, today, overrideDays) {
  if (published == null || cadence === 'fomc') return { state: 'unknown', ageDays: null };
  const tolerance = (overrideDays != null) ? overrideDays : CADENCE_TOLERANCE_DAYS[cadence];
  if (tolerance == null) return { state: 'unknown', ageDays: null };
  // Parse as UTC midnight so DST never shifts a day boundary.
  const ms = Date.parse(today + 'T00:00:00Z') - Date.parse(published + 'T00:00:00Z');
  if (Number.isNaN(ms)) return { state: 'unknown', ageDays: null };
  const ageDays = Math.round(ms / 86400000);
  return { state: ageDays > tolerance ? 'flagged' : 'fresh', ageDays: ageDays };
}
// ─── FRESHNESS-VERDICT-END ──────────────────────────────────────────────────

// ─── PIPELINE-LIVENESS-START ────────────────────────────────────────────────
// Distinguishes "the fetcher ran and had nothing new to report" from "the
// fetcher has been dead for days" — generated_at is a timestamp, so data.json
// changes (and commits) on every successful run even when no market figure
// moved, making it a true daily heartbeat. A missing/unparseable timestamp is
// a fault, not a reason to stay quiet — it must show the banner, not hide it,
// exactly the failure mode that let the 'weekly' cadence bug hide for days.
// See docs/superpowers/specs/2026-08-04-bullion-pipeline-liveness-alarm-design.md.
// tests/freshness_test.html extracts this block by its marker comments —
// renaming or removing them breaks that test, which is intended.
const PIPELINE_TOLERANCE_DAYS = 3;

function pipelineLiveness(generatedAt, nowISO, toleranceDays) {
  if (generatedAt == null) return { state: 'unknown', ageDays: null };
  const ms = Date.parse(nowISO + 'T00:00:00Z') -
             Date.parse(String(generatedAt).slice(0, 10) + 'T00:00:00Z');
  if (Number.isNaN(ms)) return { state: 'unknown', ageDays: null };
  const ageDays = Math.round(ms / 86400000);
  return { state: ageDays > toleranceDays ? 'stale' : 'fresh', ageDays: ageDays };
}

// Wording is deliberately distinct between 'stale' (we know when it last ran)
// and 'unknown' (we don't even have a timestamp to judge) — the second is
// the more alarming case and must never read like a milder version of the
// first.
function pipelineAlarmMessage(liveness, generatedAt) {
  if (liveness.state === 'unknown') {
    return 'Pipeline status unknown — data.json has no readable timestamp. '
         + 'The numbers below could be stale without any warning.';
  }
  const dateStr = generatedAt ? String(generatedAt).slice(0, 10) : 'an unknown date';
  const days = liveness.ageDays === 1 ? '1 day' : liveness.ageDays + ' days';
  return `Live data pipeline hasn't run in ${days} (last update ${dateStr}). `
       + 'Numbers below may be stale.';
}

// bar: the #pipeline-alarm element. isLive: the live-data toggle state (the
// bar must stay hidden in simulated mode — nothing on screen came from
// data.json, so a staleness claim about it would be false). prov: an object
// carrying at least {generatedAt}, normally window.BULLION_PROVENANCE.
// Deliberately takes no history-date-picker input: a dead pipeline is a fact
// about the file, not about which date is being viewed, so this must show
// regardless of that selection.
function renderPipelineAlarm(bar, isLive, prov, nowISO) {
  if (!bar) return;
  if (!isLive) { bar.hidden = true; return; }
  const generatedAt = prov ? prov.generatedAt : null;
  const liveness = pipelineLiveness(generatedAt, nowISO, PIPELINE_TOLERANCE_DAYS);
  if (liveness.state === 'fresh') { bar.hidden = true; return; }
  bar.hidden = false;
  bar.textContent = '⚠ ' + pipelineAlarmMessage(liveness, generatedAt);
}
// ─── PIPELINE-LIVENESS-END ──────────────────────────────────────────────────

// ─── NORMALISE-ENVELOPE-START ───────────────────────────────────────────────
```

- [ ] **Step 4: Implement the identical block in `bullion_mkultra.html`**

Same find/replace as Step 3 — the surrounding text is byte-identical in `bullion_mkultra.html` (confirmed by diff).

- [ ] **Step 5: Re-run the browser test and confirm it passes**

Repeat Step 2's server+probe. Expected: every check in the new block reads `PASS`, and the file's final line reads `RESULT: PASS`.

- [ ] **Step 6: Add a JS↔JS parity check to `tests/test_freshness_parity.py`**

This guards against `bullion_mk18.html` and `bullion_mkultra.html` drifting from each other on `PIPELINE_TOLERANCE_DAYS` — the same class of silent drift that let `weekly` diverge between Python and the maps.

Find:

```python
    def test_live_maps_match_python_field_overrides(self):
        for name in LIVE_MAPS:
            with self.subTest(map=name):
                with open(os.path.join(MAP_DIR, name)) as f:
                    html = f.read()
                self.assertEqual(
                    _parse_js_object(html, "FIELD_TOLERANCE_OVERRIDE"),
                    _normalise(FIELD_TOLERANCE_OVERRIDE),
                    f"{name}'s FIELD_TOLERANCE_OVERRIDE has drifted from "
                    f"fetch_bullion_data.py.",
                )
```

Replace with (adding a new test method right after it):

```python
    def test_live_maps_match_python_field_overrides(self):
        for name in LIVE_MAPS:
            with self.subTest(map=name):
                with open(os.path.join(MAP_DIR, name)) as f:
                    html = f.read()
                self.assertEqual(
                    _parse_js_object(html, "FIELD_TOLERANCE_OVERRIDE"),
                    _normalise(FIELD_TOLERANCE_OVERRIDE),
                    f"{name}'s FIELD_TOLERANCE_OVERRIDE has drifted from "
                    f"fetch_bullion_data.py.",
                )

    def test_live_maps_agree_on_pipeline_tolerance(self):
        """PIPELINE_TOLERANCE_DAYS has no Python source of truth (it's a
        UI-only banner threshold), so the two live maps are each other's only
        guard against silently drifting apart."""
        values = {}
        for name in LIVE_MAPS:
            with open(os.path.join(MAP_DIR, name)) as f:
                html = f.read()
            m = re.search(r"const\s+PIPELINE_TOLERANCE_DAYS\s*=\s*(\d+)", html)
            self.assertIsNotNone(m, f"PIPELINE_TOLERANCE_DAYS not found in {name}")
            values[name] = int(m.group(1))
        self.assertEqual(
            len(set(values.values())), 1,
            f"PIPELINE_TOLERANCE_DAYS has drifted between live maps: {values}",
        )
```

- [ ] **Step 7: Run the Python suite**

```bash
cd bullion-live-map && python3 -m unittest discover -s tests
```

Expected: PASS, one more test than before (44 → 45, per the outage-fix handoff's count).

- [ ] **Step 8: Commit**

```bash
git add bullion-live-map/bullion_mk18.html bullion-live-map/bullion_mkultra.html \
        bullion-live-map/tests/freshness_test.html bullion-live-map/tests/test_freshness_parity.py
git commit -m "Add pipelineLiveness banner logic (Layer 1 of the pipeline-liveness alarm)"
```

---

## Task 2: Wire the banner into the page — HTML, CSS, layout, and the live-status render path

**Files:**
- Modify: `bullion-live-map/bullion_mk18.html` (HTML `<body>` opening, CSS near `#app`, `fitAppToViewport()`, `updateMetrics()`'s `renderLiveBadge` call site)
- Modify: `bullion-live-map/bullion_mkultra.html` (same four spots — byte-identical surrounding text, confirmed by diff)

**Interfaces:**
- Consumes: `renderPipelineAlarm(bar, isLive, prov, nowISO)` from Task 1 (already present in both files by this point).
- Produces: a live `#pipeline-alarm` element and a working `fitAppToViewport()` that accounts for it. Nothing later depends on new names from this task.

- [ ] **Step 1: Add the bar as the first child of `<body>`, in both files**

Find:

```
<body>
<div id="starfield"></div>
```

Replace with:

```
<body>
<div id="pipeline-alarm" role="status" hidden></div>
<div id="starfield"></div>
```

- [ ] **Step 2: Add its CSS, in both files**

Find:

```
  #app { position: relative; z-index: 1; height: 100%; width: 100%; display: flex; flex-direction: column; }

  #header {
```

Replace with:

```
  #app { position: relative; z-index: 1; height: 100%; width: 100%; display: flex; flex-direction: column; }

  /* First child of <body>, above #app entirely, so a dead pipeline is
     impossible to miss regardless of which view/tab is open underneath it. */
  #pipeline-alarm {
    flex: none; display: flex; align-items: center; justify-content: center;
    gap: 8px; padding: 7px 16px; font-size: 12px; font-weight: 600;
    text-align: center; line-height: 1.4;
    background: rgba(224,177,90,0.16); color: var(--warn);
    border-bottom: 1px solid rgba(224,177,90,0.4);
  }
  /* Same id-specificity-beats-[hidden] fix as #board-view[hidden] below in
     this stylesheet: hidden alone will not hide a flex-displayed element. */
  #pipeline-alarm[hidden] { display: none; }

  #header {
```

- [ ] **Step 3: Make `fitAppToViewport()` account for the bar's height, in both files**

Find:

```js
function fitAppToViewport() {
  const vv = window.visualViewport;
  const vh = (vv && vv.height) || window.innerHeight || document.documentElement.clientHeight;
  const app = document.getElementById('app');
  if (app && vh) app.style.height = Math.round(vh) + 'px';
}
```

Replace with:

```js
function fitAppToViewport() {
  const vv = window.visualViewport;
  const vh = (vv && vv.height) || window.innerHeight || document.documentElement.clientHeight;
  const app = document.getElementById('app');
  const alarmBar = document.getElementById('pipeline-alarm');
  // #app's height is set here in JS, not by CSS, so it must be told to give
  // up the alarm bar's own height — otherwise the bar pushes the bottom of
  // the map off screen instead of the map shrinking to make room for it.
  const alarmH = (alarmBar && !alarmBar.hidden) ? alarmBar.offsetHeight : 0;
  if (app && vh) app.style.height = Math.max(0, Math.round(vh) - alarmH) + 'px';
}
```

- [ ] **Step 4: Call `renderPipelineAlarm` from the `updateMetrics` call site, in both files**

Find:

```js
  renderLiveBadge(s);
  renderStats(s);
```

Replace with:

```js
  renderLiveBadge(s);
  {
    const alarmBar = document.getElementById('pipeline-alarm');
    const wasHidden = !alarmBar || alarmBar.hidden;
    renderPipelineAlarm(alarmBar, useLiveData, window.BULLION_PROVENANCE,
      new Date().toISOString().slice(0, 10));
    // Only re-measure the viewport on an actual visibility flip —
    // updateMetrics fires on every shock-slider drag frame, and reading
    // offsetHeight forces a synchronous reflow, so re-fitting unconditionally
    // here would thrash layout during dragging.
    if (alarmBar && wasHidden !== alarmBar.hidden) fitAppToViewport();
  }
  renderStats(s);
```

- [ ] **Step 5: Live-verify the banner in `bullion_mk18.html` via headless Chrome**

```bash
cd bullion-live-map && python3 -m http.server 8901 &
```

Using the `headless-chrome-verification` skill's `cdp_probe.mjs` template against `http://localhost:8901/bullion_mk18.html`, run this sequence via `evalJS`:

1. Wait for initial load, then: `document.getElementById('pipeline-alarm').hidden` — expect `true` (the committed `data.json` was generated 2026-08-04, so with `nowISO` also today it is fresh).
2. Force a stale envelope and re-render:
   ```js
   window.BULLION_PROVENANCE = {schema: 2, generatedAt: '2026-07-20T09:41:38Z', fields: {}, history: {}, ok: true};
   updateMetrics();
   [document.getElementById('pipeline-alarm').hidden,
    getComputedStyle(document.getElementById('pipeline-alarm')).display,
    document.getElementById('pipeline-alarm').textContent]
   ```
   Expect `[false, 'flex', <a string mentioning "15 days">]`. The `getComputedStyle` check is the one that would have caught the `#board-view[hidden]` bug class if the CSS override were missing.
3. Toggle live data off and re-check: `document.getElementById('live-toggle-btn').click(); document.getElementById('pipeline-alarm').hidden` — expect `true` (still using the same stale `window.BULLION_PROVENANCE` set in step 2, proving the toggle suppression works independent of staleness).
4. Toggle live data back on: `document.getElementById('live-toggle-btn').click(); document.getElementById('pipeline-alarm').hidden` — expect `false` again.
5. Check no clipping: with the bar visible (from step 4), `document.getElementById('app').getBoundingClientRect().bottom <= window.innerHeight` — expect `true`.

- [ ] **Step 6: Fix any failures from Step 5, then re-run until all five checks pass**

- [ ] **Step 7: Regression-check the existing suites**

```bash
cd bullion-live-map && python3 -m unittest discover -s tests && python3 -m unittest test_calibrate
```

Expected: both fully green (45/45 and 33/33). Also re-run the Task 1 Step 2 browser-test probe against `tests/freshness_test.html` — expected: still `RESULT: PASS`.

- [ ] **Step 8: Commit**

```bash
git add bullion-live-map/bullion_mk18.html bullion-live-map/bullion_mkultra.html
git commit -m "Wire the pipeline-liveness banner into the map's live-status render path"
```

- [ ] **Step 9: Push to `main`**

This is a live, public-facing change (GitHub Pages serves these files directly). **Confirm with the user before pushing.**

```bash
git push
```

Then confirm via `git show origin/main:bullion-live-map/bullion_mk18.html | grep -c pipeline-alarm` (expect a non-zero count) — do not rely on `curl -sI` against the Pages URL immediately after (the CDN caches ~5 min and a failed build leaves the old header in place indefinitely, per the outage handoff's documented idiom). Check the Actions run list for the Pages deployment instead.

---

## Task 3: Layer 2 — the workflow alarm job

**Files:**
- Modify: `.github/workflows/daily-data.yml`

**Interfaces:**
- Produces: three new steps in the `update-data` job, gated on `pipeline-alarm`-labelled issues. Task 4 depends on this being pushed to `main` before it can be live-tested (`workflow_dispatch` runs off the committed workflow file on the target ref).
- Consumes: nothing from earlier tasks (independent of Layer 1).

- [ ] **Step 1: Extend `permissions:` and add the three steps**

Find:

```yaml
# Lets the built-in GITHUB_TOKEN push the data.json commit back to main.
permissions:
  contents: write
```

Replace with:

```yaml
# Lets the built-in GITHUB_TOKEN push the data.json commit back to main and
# manage the pipeline-alarm issue below. No new secret — see the design doc:
# SMTP was rejected because it would need credentials in a repo secret,
# reintroducing the exact silent-bad-secret failure class this workflow
# already caused once (docs/superpowers/bullion-live-data-pipeline-outage-handoff.md).
permissions:
  contents: write
  issues: write
```

Find:

```yaml
      - name: Commit and push if data changed
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add bullion-live-map/data.json
          if git diff --cached --quiet; then
            echo "No data changes today; nothing to commit."
          else
            git commit -m "Update live financial data for $(date -u +%F)"
            git push
          fi
```

Replace with (same content, plus three new steps appended after it):

```yaml
      - name: Commit and push if data changed
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add bullion-live-map/data.json
          if git diff --cached --quiet; then
            echo "No data changes today; nothing to commit."
          else
            git commit -m "Update live financial data for $(date -u +%F)"
            git push
          fi

      - name: Ensure the pipeline-alarm label exists
        # always() so this still runs even if an earlier step in this job
        # failed — the failure-report step below depends on the label
        # already existing to filter its issue search correctly.
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            try {
              await github.rest.issues.createLabel({
                owner: context.repo.owner,
                repo: context.repo.repo,
                name: 'pipeline-alarm',
                color: 'd93f0b',
                description: 'Daily data fetch workflow is failing',
              });
            } catch (err) {
              if (err.status !== 422) throw err; // 422 = label already exists
            }

      - name: Report failure to the alarm issue
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            const runUrl = `${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`;
            const { data: jobs } = await github.rest.actions.listJobsForWorkflowRun({
              owner: context.repo.owner,
              repo: context.repo.repo,
              run_id: context.runId,
            });
            const failedStep = jobs
              .flatMap(j => j.steps || [])
              .find(s => s.conclusion === 'failure');
            const stepName = failedStep ? failedStep.name : 'unknown step';
            const today = new Date().toISOString().slice(0, 10);
            const body = `**${today}** — failing step: **${stepName}**\nRun: ${runUrl}`;

            const { data: issues } = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              state: 'open',
              labels: 'pipeline-alarm',
            });

            if (issues.length === 0) {
              await github.rest.issues.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                title: 'Daily data fetch is failing',
                body,
                labels: ['pipeline-alarm'],
                assignees: [context.repo.owner],
              });
            } else {
              // Each failure comments rather than opening a duplicate, so a
              // pipeline that stays broken emails once per day it stays broken.
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issues[0].number,
                body,
              });
            }

      - name: Close the alarm issue on success
        if: success()
        uses: actions/github-script@v7
        with:
          script: |
            const { data: issues } = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              state: 'open',
              labels: 'pipeline-alarm',
            });
            const today = new Date().toISOString().slice(0, 10);
            for (const issue of issues) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                body: `Recovered — the **${today}** run succeeded.`,
              });
              await github.rest.issues.update({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                state: 'closed',
              });
            }
```

- [ ] **Step 2: Sanity-check indentation by eye against the rest of the file**

There is no YAML linter available in this environment (`pyyaml` is not installed, `actionlint` is not on `PATH`, `gh` is not on `PATH`). Match the existing file's convention exactly: 6 spaces before every `- name:`, 8 spaces for the keys under it. The real syntax check is the live `workflow_dispatch` run in Task 4 — a malformed workflow file fails immediately and visibly there (GitHub reports "invalid workflow file" rather than running anything).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/daily-data.yml
git commit -m "Add the pipeline-alarm GitHub issue workflow (Layer 2 of the pipeline-liveness alarm)"
```

- [ ] **Step 4: Push to `main`**

Layer 2 cannot be tested at all until this file is on `main` — `workflow_dispatch` and `schedule` both run off the committed workflow on the target ref, not local changes. **Confirm with the user before pushing**, same as Task 2 Step 9.

```bash
git push
```

---

## Task 4: Live-fire verification of the workflow alarm

**This task creates real, publicly visible artifacts on `SinbadTheExplorer/claudekit`: a GitHub Actions run, a GitHub issue (assigned to the repo owner), and a deliberate temporary breakage of the production data-fetch step on `main`. Do not run any step in this task without the user's explicit go-ahead first — this is exactly the class of action the project's own instructions call out as needing confirmation (visible to others, modifies CI/CD, temporarily degrades a shared/production path).**

**Files:**
- Modify then revert: `.github/workflows/daily-data.yml` (one line, temporarily)

**Interfaces:**
- Consumes: the three steps from Task 3, already on `main`.
- Produces: nothing further code-side; this task is pure verification.

- [ ] **Step 0: Get explicit user confirmation before doing anything else in this task.** State plainly what will happen: a workflow run will be dispatched twice against a deliberately broken step, a real issue will be created and assigned to the repo owner, then the breakage will be reverted and a third clean run dispatched to confirm the issue closes itself.

- [ ] **Step 1: Set up the API token idiom used throughout this project**

```bash
TOKEN=$(printf 'protocol=https\nhost=github.com\n' | git credential fill 2>/dev/null | sed -n 's/^password=//p')
```

(Never `echo`/print `$TOKEN`. `unset TOKEN` at the end of this task.)

- [ ] **Step 2: Deliberately break the fetch step**

Find, in `.github/workflows/daily-data.yml`:

```yaml
      - name: Fetch live financial data
        run: python3 bullion-live-map/fetch_bullion_data.py
```

Temporarily replace with:

```yaml
      - name: Fetch live financial data
        run: exit 1 # TEMPORARY — deliberate failure for pipeline-alarm live-fire test, reverted in the same session
```

Commit and push this on its own:

```bash
git add .github/workflows/daily-data.yml
git commit -m "TEMPORARY: deliberately break daily-data.yml for pipeline-alarm live-fire test"
git push
```

- [ ] **Step 3: Dispatch the first broken run**

```bash
curl -s -X POST -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/SinbadTheExplorer/claudekit/actions/workflows/daily-data.yml/dispatches \
  -d '{"ref":"main"}'
```

Poll `https://api.github.com/repos/SinbadTheExplorer/claudekit/actions/workflows/daily-data.yml/runs` (same auth header) until the newest run's `status` is `completed` and `conclusion` is `failure`.

- [ ] **Step 4: Confirm an issue was created and assigned**

```bash
curl -s -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/SinbadTheExplorer/claudekit/issues?labels=pipeline-alarm&state=open"
```

Expected: exactly one issue, titled `Daily data fetch is failing`, with `assignees` containing `SinbadTheExplorer`, and a body naming the failing step (`Fetch live financial data`) and a run URL.

- [ ] **Step 5: Dispatch a second broken run and confirm it comments rather than duplicating**

Repeat Step 3, wait for `conclusion: failure` again, then repeat Step 4's query. Expected: still exactly **one** open issue (not two) — check its comment count increased instead:

```bash
curl -s -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/SinbadTheExplorer/claudekit/issues/<issue_number>/comments"
```

Expected: one comment, dated today, naming the failing step again.

- [ ] **Step 6: Revert the deliberate breakage**

```bash
git revert HEAD~2 --no-edit  # or: manually restore the original "Fetch live financial data" step and commit
```

Confirm the restored step reads exactly `run: python3 bullion-live-map/fetch_bullion_data.py` before pushing:

```bash
git push
```

- [ ] **Step 7: Dispatch a clean run and confirm the issue closes itself**

Repeat Step 3's dispatch, wait for `conclusion: success`, then repeat Step 4's query.

Expected: zero open issues with the `pipeline-alarm` label. Then confirm the previously-open issue now shows `state: closed` and carries a final "Recovered" comment:

```bash
curl -s -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/SinbadTheExplorer/claudekit/issues/<issue_number>"
```

- [ ] **Step 8: Clean up**

```bash
unset TOKEN
```

Confirm the workflow's run history now ends on a clean green `success` (Step 7's run) so nothing is left in a broken-looking state.

---

## Task 5: House-keeping — watch the repo, freeze-check, final regression, ship

**Files:** none changed by this task except verification output.

**Interfaces:** none — this task only verifies and finalizes prior tasks' work.

- [ ] **Step 1: Set the user as watching the repo**

This was already approved as part of the design (per the outage handoff: "the repo owner is not watching the repo — `/subscription` → 404 — which is why 15 failure emails made no noise"). Low blast radius (a personal notification-preference change, not visible to others), but confirm briefly with the user before making the API call since it changes account state outside this repo's files.

```bash
TOKEN=$(printf 'protocol=https\nhost=github.com\n' | git credential fill 2>/dev/null | sed -n 's/^password=//p')
curl -s -X PUT -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/SinbadTheExplorer/claudekit/subscription \
  -d '{"subscribed": true}'
unset TOKEN
```

Confirm with a GET on the same URL: `"subscribed": true`.

- [ ] **Step 2: Freeze-check the frozen map versions**

```bash
cd bullion-live-map && git diff --stat -- bullion_mk1[1-7].html
```

Expected: empty output. If anything appears, STOP — a frozen file was accidentally touched; revert it before proceeding.

- [ ] **Step 3: Run the full three-suite regression**

```bash
cd bullion-live-map
python3 -m unittest discover -s tests
python3 -m unittest test_calibrate
```

Expected: 45/45 and 33/33 (the +1 over the outage-fix handoff's 44 comes from Task 1's new parity test). Then re-run the `freshness_test.html` browser probe (Task 1 Step 2's method) one final time against the pushed state — expected: `RESULT: PASS`.

- [ ] **Step 4: Verify live on GitHub Pages**

```bash
git show origin/main:bullion-live-map/bullion_mk18.html | grep -c 'pipeline-alarm'
git show origin/main:.github/workflows/daily-data.yml | grep -c 'pipeline-alarm'
```

Both non-zero. Then check the Actions run list (not `curl -sI` against the live URL — the Pages CDN caches ~5 min and a failed build leaves the old header in place indefinitely) for a recent successful Pages deployment:

```bash
TOKEN=$(printf 'protocol=https\nhost=github.com\n' | git credential fill 2>/dev/null | sed -n 's/^password=//p')
curl -s -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/SinbadTheExplorer/claudekit/actions/workflows/daily-data.yml/runs?per_page=1"
unset TOKEN
```

- [ ] **Step 5: Report completion**

Summarize for the user: both layers live, all suites green, live-fire verification of Layer 2 passed (issue created/assigned/commented/closed correctly), user now watching the repo. Point at this plan's checked-off boxes as the record.

---

## Self-review notes (for whoever executes this plan)

- **Spec coverage:** Layer 1 banner (state/hidden logic, tolerance, unknown-shows, both suppression rules, both files) — Tasks 1–2. Layer 2 issue alarm (create/assign, comment-not-duplicate, close-on-success, no new secret) — Task 3. Testing section's six `pipelineLiveness` cases and four DOM assertions — Task 1 Step 1. `workflow_dispatch` live-fire verification — Task 4. Out-of-scope items (replacing the per-field badge, SMTP, backporting to mk11–mk17) are correctly untouched by every task above.
- **Why two files:** `bullion_mkultra.html` is a persona/orb variant of `bullion_mk18.html` with identical surrounding text at every anchor point used in this plan (diffed and confirmed in the investigation that produced this plan) — it is not yet linked from `index.html` (which still points at `bullion_mk18.html`), but the outage-fix commit already treated both as "live" (actively edited) rather than frozen, and `test_freshness_parity.py`'s `LIVE_MAPS` list already includes both. This plan follows that existing convention rather than inventing a new one.

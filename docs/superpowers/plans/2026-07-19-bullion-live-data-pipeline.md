# Bullion Mk11 Live Data Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the Bullion Mk11 financial map and its live-data fetch script into the `claudekit` repo, replace the two `<script src>` JS-global files with a single fetched `data.json`, and prepare it to be served on GitHub Pages and refreshed daily by a cloud-scheduled routine.

**Architecture:** `fetch_bullion_data.py` (FRED + Yahoo Finance, unchanged fetch logic) writes one date-keyed `data.json` instead of two `window.X = ...` JS files. `bullion_mk11_constellation.html` fetches that JSON at page load instead of loading it via `<script src>`, then re-populates the same `window.BULLION_LIVE_DATA` / `window.BULLION_LIVE_HISTORY` globals the existing `currentLiveSource()` / `refreshDriverBases()` / `setupHistoryDatePicker()` logic already reads — so none of that downstream logic changes. `run_daily_update.sh` wraps fetch → commit-if-changed → push for the (separately configured) cloud routine to call daily.

**Tech Stack:** Python 3 stdlib (`urllib`, `json`), vanilla JS (`fetch`), bash, git.

## Global Constraints

- FOMC hike/hold/cut odds have no free data source and stay simulated — do not attempt to source them live.
- `data.json` is date-keyed, one object per calendar day, last 365 days — see Task 2 for exact shape.
- Do not modify the transmission/shock rules, node set, elasticities, provenance tiers, or AI-narrative feature of the map — out of scope.
- Do not touch `financial-map.html` or the finance-planner/finance-builder/finance-tester agent pipeline in this repo — unrelated project.
- The cloud scheduled routine (set up in Task 9) runs daily at 6:00am America/New_York.
- Spec: `docs/superpowers/specs/2026-07-19-bullion-live-data-pipeline-design.md`.

---

### Task 1: Move files into the repo

**Files:**
- Create: `bullion-live-map/` (new directory in the `claudekit` repo root)
- Move: `~/Downloads/bullion_mk11_constellation.html` → `bullion-live-map/bullion_mk11_constellation.html`
- Move: `~/Downloads/fetch_bullion_data.py` → `bullion-live-map/fetch_bullion_data.py`

**Interfaces:**
- Produces: the two files at their new repo-relative paths, used by every later task.

- [ ] **Step 1: Create the directory and move both files**

```bash
cd "~/claude-projects/claudekit"
mkdir -p bullion-live-map
mv ~/Downloads/bullion_mk11_constellation.html bullion-live-map/bullion_mk11_constellation.html
mv ~/Downloads/fetch_bullion_data.py bullion-live-map/fetch_bullion_data.py
```

- [ ] **Step 2: Verify the move**

Run: `ls bullion-live-map/`
Expected:
```
bullion_mk11_constellation.html
fetch_bullion_data.py
```

Run: `ls ~/Downloads/bullion_mk11_constellation.html ~/Downloads/fetch_bullion_data.py 2>&1`
Expected: both report `No such file or directory` (confirms they were moved, not copied).

---

### Task 2: Rewrite `fetch_bullion_data.py` to write `data.json`

**Files:**
- Modify: `bullion-live-map/fetch_bullion_data.py`

**Interfaces:**
- Consumes: nothing new — same `FRED_SERIES`, `YAHOO_SYMBOLS`, `fetch_fred_series()`, `fetch_yahoo_symbol()` as before.
- Produces: `bullion-live-map/data.json`, shape `{ "YYYY-MM-DD": { "<field>": <number>, ... }, ... }` for every date any series returned data (last `HISTORY_DAYS` days). No `fetched_at`/`source_note` keys inside — those are derived client-side in Task 4 from the max date key.

- [ ] **Step 1: Replace the output path constants**

In `bullion-live-map/fetch_bullion_data.py`, find:

```python
KEY_PATH = os.path.expanduser("~/.config/bullion/fred_api_key")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
LATEST_OUT_PATH = os.path.join(OUT_DIR, "bullion_live_data.js")
HISTORY_OUT_PATH = os.path.join(OUT_DIR, "bullion_live_history.js")
HISTORY_DAYS = 365
```

Replace with:

```python
KEY_PATH = os.path.expanduser("~/.config/bullion/fred_api_key")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_OUT_PATH = os.path.join(OUT_DIR, "data.json")
HISTORY_DAYS = 365
```

- [ ] **Step 2: Replace the output-writing tail of `main()`**

Find:

```python
    if not latest_out:
        print("No fields fetched successfully; leaving existing output files untouched.", file=sys.stderr)
        sys.exit(1)

    fetched_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    latest_out["fetched_at"] = fetched_at
    latest_out["source_note"] = SOURCE_NOTE
    with open(LATEST_OUT_PATH, "w") as f:
        f.write("window.BULLION_LIVE_DATA = " + json.dumps(latest_out, indent=2) + ";\n")

    with open(HISTORY_OUT_PATH, "w") as f:
        f.write("window.BULLION_LIVE_HISTORY = " + json.dumps(history_by_date, indent=2, sort_keys=True) + ";\n")

    all_fields = [f for _, (f, _, _) in FRED_SERIES.items()] + [f for _, (f, _) in YAHOO_SYMBOLS.items()]
    missing = [f for f in all_fields if f not in latest_out]
    print(f"Wrote {LATEST_OUT_PATH} with {len(latest_out) - 2} of {len(all_fields)} fields.")
    print(f"Wrote {HISTORY_OUT_PATH} with {len(history_by_date)} dated entries.")
    if missing:
        print(f"Missing from latest (will fall back to simulated baseline): {', '.join(missing)}")
```

Replace with:

```python
    if not history_by_date:
        print("No fields fetched successfully; leaving existing data.json untouched.", file=sys.stderr)
        sys.exit(1)

    with open(DATA_OUT_PATH, "w") as f:
        json.dump(history_by_date, f, indent=2, sort_keys=True)
        f.write("\n")

    all_fields = [f for _, (f, _, _) in FRED_SERIES.items()] + [f for _, (f, _) in YAHOO_SYMBOLS.items()]
    latest_date = max(history_by_date)
    latest_fields = history_by_date[latest_date]
    missing = [f for f in all_fields if f not in latest_fields]
    print(f"Wrote {DATA_OUT_PATH} with {len(history_by_date)} dated entries.")
    print(f"Latest date {latest_date} has {len(latest_fields)} of {len(all_fields)} fields.")
    if missing:
        print(f"Missing from {latest_date} (map will fall back to simulated baseline for these): {', '.join(missing)}")
    print()
    print(SOURCE_NOTE)
```

Note: `latest_out` (the dict that used to accumulate a single "current" snapshot across both the FRED and Yahoo loops) is no longer read anywhere after this change, but leave its accumulation loops (`for series_id, ... latest_out[field] = latest` etc.) exactly as they are — they're harmless dead writes and removing them is out of scope for this task (don't touch the fetch loops).

- [ ] **Step 3: Confirm the module still parses**

Run: `python3 -m py_compile bullion-live-map/fetch_bullion_data.py`
Expected: no output, exit code 0.

---

### Task 3: Run the script for real and verify `data.json`

**Files:**
- Read: `bullion-live-map/data.json` (generated by this task, not created by hand)

**Interfaces:**
- Consumes: `bullion-live-map/fetch_bullion_data.py` from Task 2, the FRED key already saved at `~/.config/bullion/fred_api_key`.
- Produces: a real `bullion-live-map/data.json` used by Task 4's browser test and Task 6/7.

- [ ] **Step 1: Run it**

```bash
cd "~/claude-projects/claudekit/bullion-live-map"
python3 fetch_bullion_data.py
```

Expected: stdout ends with lines like:
```
Wrote .../bullion-live-map/data.json with <N> dated entries.
Latest date <YYYY-MM-DD> has <M> of 10 fields.
```
No `FRED ... fetch failed` or `Yahoo ... fetch failed` lines (a couple of missing fields is tolerable — see Task 2's `missing` message — but if every field is missing, stop and debug before continuing; likely causes are a bad/missing FRED key or no network).

- [ ] **Step 2: Verify the shape**

```bash
python3 -c "
import json
d = json.load(open('data.json'))
assert isinstance(d, dict) and len(d) > 0, 'data.json is empty or not an object'
latest = max(d)
print('dates:', len(d), 'latest:', latest)
print('latest fields:', sorted(d[latest].keys()))
for date, fields in d.items():
    assert isinstance(fields, dict)
    for k, v in fields.items():
        assert isinstance(v, (int, float)), f'{date}.{k} is not numeric: {v!r}'
print('OK')
"
```

Expected: prints `dates: <N> latest: <today or last trading day>`, a field list drawn from `{us2y, us10y, cpi_yoy, vix, ffr, wti_px, nfp_mom, gold_px, dxy, spx}`, and `OK` with no assertion errors.

---

### Task 4: Convert the HTML to fetch `data.json`

**Files:**
- Modify: `bullion-live-map/bullion_mk11_constellation.html`

**Interfaces:**
- Consumes: `data.json` (same directory, fetched via relative URL `fetch('data.json')`).
- Produces: `window.BULLION_LIVE_HISTORY` (full parsed object) and `window.BULLION_LIVE_DATA` (a per-field-latest snapshot — each field at its most recent available value across all dates — plus a `fetched_at` key set to the newest date that had any data) — the exact same two globals `currentLiveSource()` (already defined, untouched) already expects, so no changes are needed anywhere else in the file's ~3200 lines of state/graph logic.

**IMPORTANT — why per-field-latest, not a single date row (discovered during Task 3):** FRED daily series, Yahoo daily series, and FRED *monthly* series (cpi_yoy, nfp_mom) all publish on different lags, so **no single date in `data.json` has all 10 fields** — the newest date typically has only the 3 Yahoo fields. Building the "current conditions" snapshot from one date's row would therefore show most metrics as simulated. Instead, reconstruct the snapshot by taking each field's most recent available value (walk dates ascending, let later dates overwrite each field) — this reproduces exactly what the retired `bullion_live_data.js` per-field snapshot provided. The date picker (`BULLION_LIVE_HISTORY`) still reads raw per-date rows and correctly falls back per-field for dates missing a field, so it needs no such reconstruction.

- [ ] **Step 1: Remove the two `<script src>` tags**

Find (exact lines, near the top of the file):

```html
<script src="bullion_live_data.js"></script>
<script src="bullion_live_history.js"></script>
```

Delete both lines entirely.

- [ ] **Step 2: Update the "no live data" messages to mention `data.json`**

Find:

```js
      ? 'All metrics are simulated — no bullion_live_data.js found. Run fetch_bullion_data.py to pull live data.'
```

Replace with:

```js
      ? 'All metrics are simulated — data.json not found or failed to load. Run fetch_bullion_data.py to pull live data.'
```

Find:

```js
    input.title = 'No bullion_live_history.js found — run fetch_bullion_data.py to enable this.';
    if (note) note.textContent = 'Past dates are disabled because bullion_live_history.js was not found next to this file. Run fetch_bullion_data.py once to generate it, then reload.';
```

Replace with:

```js
    input.title = 'No data.json found — run fetch_bullion_data.py to enable this.';
    if (note) note.textContent = 'Past dates are disabled because data.json was not found (or failed to load) next to this file. Run fetch_bullion_data.py once to generate it, then reload.';
```

- [ ] **Step 3: Update the comment above the date picker**

Find:

```js
// ── Historical date picker ───────────────────────────────────────────────
// Reads from BULLION_LIVE_HISTORY (see fetch_bullion_data.py), a static,
// pre-fetched trailing-year table rather than a live fetch — so date changes
// stay instant and this still works when the HTML is opened via file://.
// A picked date overrides the sim/live toggle entirely (see currentLiveSource),
// so the toggle button is disabled while a date is active.
(function setupHistoryDatePicker() {
```

Replace with:

```js
// ── Historical date picker ───────────────────────────────────────────────
// Reads from BULLION_LIVE_HISTORY, populated by a fetch('data.json') below
// once it resolves — so date changes stay instant after load, but the picker
// is disabled until that fetch completes (or falls back if it fails/the page
// was opened via file://, where relative fetch() doesn't work).
// A picked date overrides the sim/live toggle entirely (see currentLiveSource),
// so the toggle button is disabled while a date is active.
function setupHistoryDatePicker() {
```

(Note: the function declaration changes from an auto-invoking `(function setupHistoryDatePicker() {` to a plain `function setupHistoryDatePicker() {` — it's called explicitly in Step 4 instead of invoking itself immediately.)

- [ ] **Step 4: Un-self-invoke the picker function and add the `data.json` loader**

Find (the end of the picker IIFE, followed by the initial render calls):

```js
  input.addEventListener('change', () => applyDate(input.value));
  clearBtn.addEventListener('click', () => { input.value = ''; applyDate(null); });
})();

buildGraph();
buildLegend();
updateMetrics();
```

Replace with:

```js
  input.addEventListener('change', () => applyDate(input.value));
  clearBtn.addEventListener('click', () => { input.value = ''; applyDate(null); });
}

buildGraph();
buildLegend();
updateMetrics();

// Live data loads asynchronously after the first paint, so the page is
// usable immediately on the simulated baseline, then upgrades in place.
fetch('data.json')
  .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
  .then(json => {
    window.BULLION_LIVE_HISTORY = json;
    // Sources publish on different lags (daily FRED/Yahoo vs monthly CPI/NFP),
    // so no single date has every field. Build the "current conditions"
    // snapshot from each field's most recent value: walk dates ascending and
    // let later dates overwrite each field, so every field ends at its latest
    // available reading. This reproduces the retired bullion_live_data.js.
    const snapshot = {};
    let latestDateWithData = null;
    for (const dt of Object.keys(json).sort()) {
      const row = json[dt];
      if (Object.keys(row).length) {
        Object.assign(snapshot, row);
        latestDateWithData = dt;
      }
    }
    if (latestDateWithData) {
      snapshot.fetched_at = latestDateWithData;
      window.BULLION_LIVE_DATA = snapshot;
    }
  })
  .catch(err => {
    console.warn('data.json fetch failed, falling back to simulated baseline:', err);
  })
  .finally(() => {
    setupHistoryDatePicker();
    refreshDriverBases();
    state = buildBaseState();
    updateMetrics();
  });
```

- [ ] **Step 5: Confirm the file is still well-formed**

Run: `python3 -c "import re; s = open('bullion-live-map/bullion_mk11_constellation.html').read(); assert s.count('<script') == s.count('</script>') + s.count('/>'); print('script tag count OK, length', len(s))"`

Run from the repo root (`cd "~/claude-projects/claudekit"` first if not already there).

Expected: `script tag count OK, length <some number close to the original ~486KB>` — no Python exception.

---

### Task 5: Functional browser test

**Files:**
- Read-only: `bullion-live-map/bullion_mk11_constellation.html`, `bullion-live-map/data.json`

**Interfaces:**
- Consumes: both files from Tasks 2–4, served over `http://` (not `file://`, since `fetch()` of a local file is blocked by Chrome's CORS rules on `file://` URLs).

- [ ] **Step 1: Serve the folder locally**

```bash
cd "~/claude-projects/claudekit/bullion-live-map"
python3 -m http.server 8899
```

Run this with `run_in_background: true` (it never exits on its own).

- [ ] **Step 2: Open it in Chrome and check the live metrics**

Use `mcp__claude-in-chrome__navigate` to open `http://localhost:8899/bullion_mk11_constellation.html`, then `mcp__claude-in-chrome__read_console_messages` to confirm there is no `data.json fetch failed` warning logged, then `mcp__claude-in-chrome__get_page_text` or `read_page` to confirm the metric cells (`#m-spx`, `#m-cpi`, `#m-gold`, `#m-dxy`, `#m-wti`) show numbers, not `—`.

Expected: no console warning about the fetch failing; metric cells show non-placeholder numeric values matching `data.json`'s latest date.

- [ ] **Step 3: Exercise the date picker**

Pick any date string that exists as a key in `bullion-live-map/data.json` other than the latest one (read a few keys with `python3 -c "import json; print(sorted(json.load(open('data.json')))[:5])"` if needed). Use `mcp__claude-in-chrome__form_input` (or `computer`) to set `#history-date-input` to that date and confirm `#history-note` updates and the metric cells change to that date's values instead of the latest date's. Then click `#history-date-clear-btn` and confirm the metrics revert to the latest date's values.

Expected: metrics visibly change when a historical date is picked, and revert on "Today".

- [ ] **Step 4: Stop the local server**

Stop the background `python3 -m http.server 8899` process (find its PID with `lsof -ti:8899` and `kill` it, or stop the backgrounded Bash shell directly).

---

### Task 6: `run_daily_update.sh`

**Files:**
- Create: `bullion-live-map/run_daily_update.sh`

**Interfaces:**
- Consumes: `fetch_bullion_data.py` (Task 2) and the repo's git state.
- Produces: the entrypoint the Task 9 cloud routine calls daily.

- [ ] **Step 1: Write the script**

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

python3 fetch_bullion_data.py

git add data.json
if git diff --cached --quiet; then
  echo "No data changes; skipping commit."
else
  git commit -m "Update live financial data for $(date -u +%F)"
  git push origin main
fi
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x "~/claude-projects/claudekit/bullion-live-map/run_daily_update.sh"
```

- [ ] **Step 3: Test the no-op branch (safe — does not push)**

This must run *after* Task 7 has committed today's `data.json`, so that re-running the fetch produces no diff. Run it now only if Task 7 is already done; otherwise do this step immediately after Task 7 instead, before Task 8.

```bash
cd "~/claude-projects/claudekit/bullion-live-map"
./run_daily_update.sh
```

Expected: `No data changes; skipping commit.` (confirms the guard works and, critically, that it does *not* attempt a `git push` when nothing changed — important since push access isn't fixed yet as of this plan).

Do not run this script on a day `data.json`'s latest date is stale relative to today and expect a no-op — a genuine new trading day's data will produce a real diff, hit the `git commit` + `git push` branch, and fail on the push (expected, until Task 9's prerequisite is met). If that happens, that's not a bug in this script — stop and don't retry-loop it.

---

### Task 7: Commit to git

**Files:**
- Stage: `bullion-live-map/bullion_mk11_constellation.html`, `bullion-live-map/fetch_bullion_data.py`, `bullion-live-map/data.json`, `bullion-live-map/run_daily_update.sh`

- [ ] **Step 1: Stage exactly these four files (not the repo's other pre-existing untracked files)**

```bash
cd "~/claude-projects/claudekit"
git add bullion-live-map/bullion_mk11_constellation.html bullion-live-map/fetch_bullion_data.py bullion-live-map/data.json bullion-live-map/run_daily_update.sh
git status
```

Expected: `git status` shows exactly those four files staged under "Changes to be committed", and `.claude/`, `CLAUDE.md`, `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `financial-map.html` still listed as untracked (pre-existing, unrelated — leave them alone).

- [ ] **Step 2: Commit**

```bash
git commit -m "$(cat <<'EOF'
Move Bullion Mk11 into the repo with a fetch()-based data.json pipeline

Replaces the two bullion_live_data.js/bullion_live_history.js globals
with a single date-keyed data.json fetched at runtime, so the map can
be served (and kept current) from GitHub Pages instead of only
working when opened as a local file.
EOF
)"
git log --oneline -3
```

Expected: commit succeeds, `git log` shows the new commit on top of `edd1b22` (the spec commit from brainstorming).

---

### Task 8: Disable the obsolete LaunchAgent

**Files:**
- Modify (rename, not delete): `~/Library/LaunchAgents/com.bullion.livedata.plist`

- [ ] **Step 1: Unload it**

```bash
launchctl unload ~/Library/LaunchAgents/com.bullion.livedata.plist 2>&1
```

Expected: no error, or (if it wasn't currently loaded) a message that can be ignored.

- [ ] **Step 2: Rename it so it can't be accidentally reloaded, but is still recoverable**

```bash
mv ~/Library/LaunchAgents/com.bullion.livedata.plist ~/Library/LaunchAgents/com.bullion.livedata.plist.disabled
```

- [ ] **Step 3: Verify it's gone from launchctl's list**

```bash
launchctl list | grep -i bullion
```

Expected: no output (empty grep result — the job is no longer registered).

---

### Task 9: Push, enable Pages, set up the cloud routine

**Files:** none (infra/config only)

This task is gated on a prerequisite outside this plan's control: push access to `SinbadTheExplorer/claudekit` from this Mac. As of the design phase, the cached GitHub credentials belonged to a different account (`tamphuc0503-nrc`) with no write access. The user was going to fix this via `gh auth login` as `SinbadTheExplorer`.

- [ ] **Step 1: Check whether push access is fixed**

```bash
cd "~/claude-projects/claudekit"
git push --dry-run origin main 2>&1
```

Expected if fixed: no `Permission ... denied` / `403` line (may print `To https://github.com/...` and a `main -> main` line, or nothing if already up to date).
Expected if not fixed: the same `Permission to SinbadTheExplorer/claudekit.git denied to <account>` / `403` error as before.

If not fixed: **stop this task here** and tell the user push access still isn't working — don't proceed to Steps 2–4 or attempt any workaround (e.g. force-pushing, switching remotes) without asking them first.

- [ ] **Step 2: Push**

```bash
git push origin main
```

Expected: succeeds, prints the new commit range pushed to `main`.

- [ ] **Step 3: Enable GitHub Pages**

Go to `https://github.com/SinbadTheExplorer/claudekit/settings/pages` (via browser automation if the user is signed into that account in Chrome, otherwise ask the user to do it) and set Source = "Deploy from a branch", Branch = `main`, folder = `/ (root)`. Note for the user: this makes everything at the repo root — including `financial-map.html`, `CLAUDE.md`, and the PDF — publicly reachable via the Pages URL, not just `bullion-live-map/`. Confirm that's acceptable before enabling (it likely already is, if `claudekit` is a public GitHub repo, but worth a one-line confirmation since Pages makes it a browsable website rather than just a git history).

Expected: after a minute or two, `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mk11_constellation.html` loads the map and its metrics populate (same check as Task 5 Step 2, but against the live Pages URL instead of `localhost:8899`).

- [ ] **Step 4: Set up the cloud scheduled routine**

Invoke the `schedule` skill to create a daily 6:00am America/New_York cloud routine against the `SinbadTheExplorer/claudekit` repo that runs `bullion-live-map/run_daily_update.sh`, with the FRED API key (currently at `~/.config/bullion/fred_api_key` locally — read its value, don't just reference the path, since the cloud routine can't read this Mac's filesystem) stored as whatever secret mechanism the `schedule` skill provides. Follow that skill's own instructions for the exact setup flow — it determines the repo-access and secret-storage mechanics, which weren't prescribed in the design.

Expected: the `schedule` skill confirms the routine is created and reports its next scheduled run time.

---

## Self-review notes

- Spec coverage: file layout (Task 1), `data.json` shape (Task 2/3), HTML fetch-based loading (Task 4), serving check (Task 5, then Task 9 Step 3), scheduler (Task 9 Step 4), `run_daily_update.sh` (Task 6), LaunchAgent cleanup (Task 8), out-of-scope items (Global Constraints) — all covered.
- Local git identity and `gh auth login` are prerequisites the user already completed for local commits (Task 7 needs `user.name`/`user.email`, already set) — push access (Task 9) is the one still open, called out explicitly rather than assumed.
- Task 6 Step 3 and Task 7 have an ordering dependency (test the no-op branch only after `data.json` is already committed) — called out inline since plan tasks are otherwise meant to be readable/executable independently.

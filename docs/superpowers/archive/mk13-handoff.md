# Bullion Mk12 (shipped) → Mk13 — Session Handoff

**Written:** 2026-07-23 · **For:** a fresh session resuming the Bullion map — either starting Mk13 from the backlog or just maintaining the now-live Mk12.

## Goal

Mk12 "Calibrate & Backtest" is **DONE and LIVE on `main`**, and a permanent
versioned-URL scheme is in place so future versions can ship without breaking the
shared link. There is **no in-progress work** — this hands off the finished state
plus the Mk13 backlog. The forward goal (when you pick it up) is Mk13, whose
headline item is aligning the JS backtest's day-pairing with the Python fit.

- Plan (Mk12, executed): `docs/superpowers/plans/2026-07-22-bullion-mk12-calibrate-backtest.md`
- Spec (Mk12): `docs/superpowers/specs/2026-07-22-bullion-mk12-calibrate-backtest-design.md`
- Progress ledger + full Mk13 backlog (recovery map): `.superpowers/sdd/progress.md`
- Prior handoff (mid-Mk12, now historical): `docs/superpowers/mk12-handoff.md`

## How to resume (do this first)

1. Confirm the clean shipped state: `git rev-parse --abbrev-ref HEAD` (expect `main`),
   and `git rev-parse --short main origin/main` — both should be **`ba7c874`** (local ==
   origin, everything pushed). `git log --oneline 2e2d7cd..HEAD` shows the 10 Mk12 commits
   + the versioning commit.
2. Read `.superpowers/sdd/progress.md` — it is the authority. All 9 Mk12 tasks are marked
   complete with commit SHAs; trust the ledger + `git log` over any recollection.
3. If starting Mk13: write a fresh Mk13 spec+plan (`superpowers:brainstorming` →
   `writing-plans`), then run `superpowers:subagent-driven-development` on a NEW feature
   branch off `main`. Do NOT reuse the Mk12 briefs in `.superpowers/sdd/` (they are Mk12).
4. **Immediate next action:** nothing is blocked or half-done. If continuing, the first
   Mk13 task is the day-pairing alignment (see "What's next" #1). If not, no action needed —
   the site is live and self-maintaining via the daily data pipeline.

## Current state (active files)

**Branch:** `main`, at `ba7c874`, fully pushed to `origin/main`. Working tree clean
(the only untracked items — `.claude/`, `CLAUDE.md`, `financial-map.html`,
`docs/chrome-mcp-setup.md`, `docs/project-overview.md` — are pre-existing and NOT part
of this work; leave them).

**The live map + versioning scheme** (all in `bullion-live-map/`):
- `index.html` — permanent front door; redirects to the current version. **The public
  share URL is the folder:** `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/`
- `bullion_mk12.html` — the current Mk12 map (the real deliverable).
- `bullion_mk11.html` — genuine Mk11 restored from `2e2d7cd`, a browsable archive.
- `bullion_mk11_constellation.html` — now a REDIRECT STUB (→ `./index.html`) so
  already-shared links still work. Do NOT delete it or put map content back in it.
- `release.sh <N>` — one-command version bump (copy current → `bullion_mk<N>.html`, bump
  only title/og:title/h1, repoint `index.html`). Verified: leaves historical "Mk9/Mk10"
  prose refs intact, rejects stale/invalid numbers.
- `calibrate.py` + `test_calibrate.py` (offline, stdlib, 6/6) + `calibration_report.txt`.
- `data.json` — daily live data (FRED/Yahoo); the GitHub Actions cron updates only this.

**Scratch workspace** (`.superpowers/sdd/`, git-ignored):
- `progress.md` — the Mk12 ledger + Mk13 backlog. Current.
- `task-1..9-brief.md` / `task-*-report.md` — these are now the **Mk12** artifacts
  (regenerated during the run). ⚠️ For Mk13, generate fresh briefs from a Mk13 plan;
  do not reuse these.

## What has changed (this effort)

- **Mk12 shipped** (10 commits `2e2d7cd..ddd6151`, fast-forward merged to `main`, pushed):
  offline calibration (`calibrate.py`), coefficient adoption into `ELASTICITY`
  (human-in-the-loop), a client-side self-grading backtest (`backtestModel()`) rendered
  as a "Model accuracy" panel in the Audit Log, plus three fixes (runManual boot bug,
  relative `nodeCutoff()`, weak-scenario relabels), and the Mk11→Mk12 version bump.
  Executed via `subagent-driven-development` with a per-task review gate + a final Opus
  whole-branch review (verdict: Ready to merge, Yes).
- **A latent bug was found + fixed (Task 6):** `validateProvenance()` only ran on slider
  moves, never at page load — so the audit log's "no sign contradictions" guarantee was
  not enforced at load. Now runs once at boot (proven `callsAtBoot:1`, 0 conflicts / 0
  demotions), so provenance is genuinely enforced.
- **Versioning scheme added** (commit `ba7c874`): the URL fix above, so the Mk-number can
  climb every release without breaking shared links.

## What has failed / risks / caveats

- **Nothing is failing.** No blocked tasks, no failing tests, tree clean, site live.
- **One deferred finding (accepted as Mk13, user-approved):** the JS backtest and the
  Python fit pair up days differently across weekends. `data.json` has ~102 weekend keys
  holding only `ffr`; `fit_cell` (Python) filters to present days then diffs consecutively
  (BRIDGES weekends, ~250 spx diffs), while `backtestModel()` (JS) walks all calendar dates
  and skips missing (DROPS weekend-straddling changes + Mondays, ~196 spx diffs). It does
  NOT break the out-of-sample property and **no displayed number is false** — it's just not
  a perfect apples-to-apples day-sample. This reproduces the plan's own JS snippet, so it's
  a plan-level follow-up, not an implementer defect.
- **Verification gotcha:** any headless check that needs the live data (backtest, or the
  provenance validator which now runs at boot) requires the Chrome flag
  `--allow-file-access-from-files`. Without it the `file://` fetch of `data.json` is blocked,
  `window.BULLION_LIVE_HISTORY` stays null, and `backtestModel()` returns null / PROV arrays
  stay empty. The earlier handoff's PROV command omitted this flag.
- **Do NOT rename `index.html`** and do NOT resurrect map content into the legacy stub —
  those two rules are what keep every shared link unbreakable.
- Old unrelated feature branches (`bullion-beginner-mode`, `bullion-provenance`,
  `bullion-provenance-audit`) exist locally — not part of this work, ignore them.

## What's next (ordered) — the Mk13 backlog

1. **[Important, plan-level] Align the JS backtest day-pairing to the Python fit.** In
   `backtestModel()` (in `bullion_mk12.html`), build the present-date list per field first
   (`dates.filter(d => field in H[d])`) and diff consecutive PRESENT days, mirroring
   `fit_cell`. Expect the displayed hit-rates/R² to shift slightly; re-verify with the
   backtest harness. Makes the "graded on the same sample it was fit on" claim exact.
2. **[Minor] `verdict()` NaN guard** in `calibrate.py`: add `math.isnan(t)` (unreachable on
   real data; hardening only).
3. **[Minor/UX] Add a one-line "structural, not a bug" note** to the Model-accuracy panel
   for low-hit-rate ffr-driven fields (us2y ~5%) so a lay viewer doesn't read it as broken.
   (The T5 caveat already frames it as same-day co-movement, not a forecast.)
4. **[Minor/pedagogy] Consider restoring 1-line causal intuition** to the Task-3 adopted
   `src` strings (e.g. dxy→spx "~40% of S&P revenue earned abroad") alongside the fit stats.
5. **[Cosmetic] Normalize "train split" phrasing** across the adopted `src` strings.

To ship any of these: do the work in `bullion_mk12.html` for small fixes (stays Mk12), or
run `./release.sh 13` to cut Mk13 first if it's a milestone. Then commit + `git push origin main`.

## Verification idioms used in this project (for the resuming session)

- **Python:** `cd bullion-live-map && python3 -m unittest test_calibrate -v` (expect 6/6).
- **Calibration report:** `cd bullion-live-map && python3 calibrate.py` → prints 14 cell
  lines + writes `calibration_report.txt`.
- **Headless map checks** (copy the html + `data.json` to a temp dir, append a probe after
  `load`, and USE THE FLAG):
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --allow-file-access-from-files --virtual-time-budget=5000 --enable-logging=stderr --v=0 file://<copy>.html`
  Probe examples: `backtestModel()` (per-field hit-rate/R²); `PROV_CONFLICTS.length` /
  `PROV_DEMOTIONS.length` (now populated at boot — expect 0/0); `nodeCutoff()` +
  `triggerShock(scenario)` for threshold checks.
- **Redirect checks:** copy the whole versioned set + `data.json` to a temp dir, load
  `index.html` / the legacy stub headless, and assert `location.pathname` lands on the
  current `bullion_mk<N>.html`.
- **Confirm a push landed:** `git show origin/main:<path>` — the Pages CDN caches ~5 min,
  so a stale live URL right after a push is normal, not a failure.

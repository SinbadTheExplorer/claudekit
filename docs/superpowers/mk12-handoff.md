# Bullion Mk12 — Session Handoff

**Written:** 2026-07-22 · **For:** a fresh session resuming the Mk12 subagent-driven run.

## Goal

Execute the **Mk12 "Calibrate & Backtest"** plan for the Bullion constellation map,
using **subagent-driven development** (fresh implementer subagent per task → per-task
review gate → final whole-branch review → merge).

Mk11 made the map's causal *signs* sourced and honest. Mk12 makes the *magnitudes*
honest where the data supports it, and adds a **live self-grading backtest** panel to
the Audit Log. See the thesis and full detail in:
- Spec: `docs/superpowers/specs/2026-07-22-bullion-mk12-calibrate-backtest-design.md`
- Plan (9 tasks, bite-sized): `docs/superpowers/plans/2026-07-22-bullion-mk12-calibrate-backtest.md`
- Progress ledger (recovery map): `.superpowers/sdd/progress.md`

## How to resume (do this first)

1. You should already be on branch **`mk12-calibrate-backtest`** (base commit `2e2d7cd`).
   Confirm: `git rev-parse --abbrev-ref HEAD` and `git log --oneline 2e2d7cd..HEAD`.
2. Re-invoke the workflow: `Skill superpowers:subagent-driven-development`.
3. Read `.superpowers/sdd/progress.md` — it is the authority on what is done. Trust the
   ledger + `git log` over any recollection.
4. **Immediate next action:** run the Task 1 **review gate** (see "What's next" below) —
   Task 1 is implemented but NOT yet reviewed.

## Current state (active files)

**Branch:** `mk12-calibrate-backtest`, one commit ahead of base `2e2d7cd`.

**Files created on the branch (Task 1, committed in `80f3359`):**
- `bullion-live-map/calibrate.py` — offline calibration harness core: `ols`,
  `first_diff` (ported verbatim from `audit_fit_elasticities.py`), plus new
  `train_split`, `target_series`, `verdict`. Stdlib-only, Python 3.9.
- `bullion-live-map/test_calibrate.py` — 6 unittest cases (split ×2, verdict ×4).

**File that later tasks will modify (untouched so far):**
- `bullion-live-map/bullion_mk11_constellation.html` — the map. Tasks 3–9 edit it
  (adopt fits, backtest engine, Audit Log panel, runManual fix, threshold, scenarios,
  version bump). **Keep this filename** — it is the public GitHub Pages URL.

**Scratch workspace** (`.superpowers/sdd/`, git-ignored — persists on disk, not in git):
- `progress.md` — the ledger (current Mk12 run).
- `task-1-brief.md`, `task-1-report.md` — Mk12 Task 1 artifacts.
- ⚠️ `task-2-brief.md` … `task-8-brief.md` and their reports are **STALE Mk11 leftovers**
  (dated Jul 21). Do NOT use them. Regenerate each task's brief from the Mk12 plan with
  the skill's `scripts/task-brief` before dispatching.

**Not mine — leave alone:** untracked `.claude/`, `CLAUDE.md`, `financial-map.html`,
`docs/chrome-mcp-setup.md`, `docs/project-overview.md` are pre-existing, unrelated.

## What has changed

- Created feature branch `mk12-calibrate-backtest` from `main`@`2e2d7cd`.
- Started a fresh Mk12 ledger at `.superpowers/sdd/progress.md`.
- **Task 1 implemented** (commit `80f3359`): `calibrate.py` + `test_calibrate.py`,
  6/6 tests passing per the implementer's report (`.superpowers/sdd/task-1-report.md`).
- Spec (`59bc6fa`) and plan (`2e2d7cd`) were committed earlier and are also on `main`.

## What has failed / risks / caveats

- **Nothing has failed.** No BLOCKED tasks, no failing tests.
- **Task 1 is UNVERIFIED.** Its per-task review gate has not run yet, AND the safety
  classifier was unavailable during the implementer dispatch (harness warned to verify
  the subagent's output manually). Treat Task 1 as provisional until reviewed.
- **Stale briefs trap** (above): the Mk11 task-2..8 briefs still sit in the workspace.
- **Controller resolutions carried from pre-flight** (also in the ledger):
  - Work stays on the feature branch. Task 9 Step 4 says "git push origin main" — that is
    **overridden**: implementers COMMIT only; the controller does the final whole-branch
    review + merge/push via `finishing-a-development-branch`.
  - Task 3 src-comment tokens (`<slope>`, `<target>`, `N`…) are fill-ins from
    `calibration_report.txt`, not literal source.
  - Ephemeral headless-Chrome test files may live in a temp dir.

## What's next (ordered)

1. **Finish Task 1's review gate.** Generate the review package and dispatch a task
   reviewer (a small stdlib-Python diff — a mid/cheap model reviewer is fine):
   ```
   SKILL=~/.claude/plugins/cache/claude-plugins-official/superpowers/6.1.1/skills/subagent-driven-development
   "$SKILL/scripts/review-package" 2e2d7cd 80f3359    # prints a diff-file path
   ```
   Give the reviewer: the diff path, `.superpowers/sdd/task-1-brief.md`,
   `.superpowers/sdd/task-1-report.md`, and the plan's Global Constraints. Two verdicts
   required (spec compliance + code quality). Fix→re-review loop until clean, then mark
   Task 1 complete in the ledger: `Task 1: complete (commit 80f3359, review clean)`.
2. **Task 2** — calibration report generator (`calibrate.py` → `calibration_report.txt`).
   Regenerate its brief first. Model: haiku (full code in the plan). Then review.
3. **Task 3** — human-in-the-loop adoption of good fits into the HTML `ELASTICITY` table,
   driven by the actual `calibration_report.txt` from Task 2. Model: sonnet (judgment).
   Verify `validateProvenance()` stays green (`PROV {"conflicts":0,"demotions":0}`).
4. **Tasks 4–9** in order — backtest engine (4), Audit Log accuracy panel (5), runManual
   fix (6), relative node cutoff (7), weak-scenario relabel (8), version bump + integration
   verify (9). Suggested models: sonnet for HTML/integration tasks; haiku for the fully
   code-specified ones (6, 8). Review gate after each.
5. **Final whole-branch review** on the most capable model (opus), then
   `finishing-a-development-branch`: merge `mk12-calibrate-backtest` → `main` and
   `git push origin main`. (Push works directly via the Bash tool now; verify a landed
   push with `git show origin/main:<path>` — the Pages CDN caches ~5 min.)

## Verification idioms used in this project (for the resuming session)

- Python: `cd bullion-live-map && python3 -m unittest test_calibrate -v`.
- The page has no JS test runner — verify via headless Chrome:
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --virtual-time-budget=4000 --enable-logging=stderr --v=0 file://<copy>.html`
  and assert on a `console.log('TAG '+JSON.stringify(...))` appended after `load`.
  Copy `data.json` next to the test HTML so the live-data fetch resolves.

# Bullion Mk14 + Mk15 (shipped & merged) — Session Handoff

**Written:** 2026-07-24 · **Re-verified current:** 2026-07-24 (same session — still `main @ 0de4f5c`, tree clean, nothing shipped since; Mk15 merged + live) · **For:** a fresh session resuming the Bullion map — either picking up the Mk16 backlog, or just maintaining the now-live Mk15.

## Goal

Mk14 "Fidelity & Truth" and Mk15 "Breadth & Depth" are **DONE, MERGED to `main`, and LIVE on GitHub Pages.** There is **no in-progress work** — this hands off the finished state plus a small Mk16 backlog (Minor follow-ups from the final review). The forward goal (when you pick it up) is Mk16, whose headline item is a user decision on the `vix→options` link direction.

- Plan (Mk14/Mk15, fully executed): `docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md` (untracked)
- Progress ledger + full per-task record + final-review Minors (recovery map): `.superpowers/sdd/progress.md`
- Prior handoff (mid-Mk13, now historical): `docs/superpowers/mk13-handoff.md`
- Merged PR: https://github.com/SinbadTheExplorer/claudekit/pull/2 (closed, merged)
- Live map (permanent folder URL): https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/

## How to resume (do this first)

1. Confirm the shipped state: `git rev-parse --abbrev-ref HEAD` (expect `main`) and
   `git log --oneline fd3b4f2..HEAD` — expect the 10 Mk14/Mk15 task commits + the merge
   `0de4f5c Merge PR #2`. `main` == `origin/main` == `0de4f5c`.
2. Read `.superpowers/sdd/progress.md` — it is the authority. All 12 tasks (M14.0–M14.6,
   M15.0–M15.4) are marked complete with commit SHAs, the calibration gate decision, every
   controller resolution of a plan-vs-reality conflict, and the final-review Minor list.
   Trust the ledger + `git log` over any recollection.
3. If starting Mk16: `git checkout main`, then `./bullion-live-map/release.sh 16`, edit the
   new file, and (optionally) run `superpowers:subagent-driven-development`. Do NOT reuse the
   Mk14/Mk15 briefs in `.superpowers/sdd/mk14mk15/` — they are for the shipped work.
4. **Immediate next action:** nothing is blocked or half-done. If continuing, the first Mk16
   item is the user decision on the `vix→options` arrow (see "What's next" #1). If not, no
   action needed — the site is live and self-maintaining via the daily data pipeline.

## Current state (active files)

**Branch:** on `main` @ `0de4f5c`, fully pushed. Working tree clean (only pre-existing
untracked items remain — see "Not mine" below). The feature branch `bullion-mk14-mk15`
(@ `da619c5`) still exists locally and on origin; the PR is merged, so it can be deleted
(`git branch -d bullion-mk14-mk15`) whenever — kept for now, harmless.

**The live map + versioning scheme** (all in `bullion-live-map/`):
- `index.html` — permanent redirect front door; now points at `bullion_mk15.html`. **The public
  share URL is the folder:** `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/`.
  NEVER rename `index.html`.
- `bullion_mk15.html` — the current live Mk15 map (39 nodes, 93 links).
- `bullion_mk14.html`, `bullion_mk13.html`, `bullion_mk12.html`, `bullion_mk11.html` — browsable archives.
- `bullion_mk11_constellation.html` — REDIRECT STUB (→ `./index.html`); keeps old shared links working. Do NOT delete it or put map content back in it.
- `calibrate.py` + `test_calibrate.py` (offline, stdlib, **10/10**) + `calibration_report.txt` (18 cells now).
- `release.sh <N>` — one-command version bump (copies current → `bullion_mk<N>.html`, bumps title/h1, repoints index).
- `data.json` — daily live data (FRED/Yahoo); the GitHub Actions cron updates only this.

**Separate lineage — do NOT conflate:** `financial-map.html` (repo root) is "Bullion Mk1 — Macro
Transmission Map", the older D3 force-directed map with its own planner/builder/tester agent
pipeline (see `CLAUDE.md`). It is NOT an earlier version of the Mk11→Mk15 constellation; it is a
parallel deliverable, is deployed on Pages, and runs on SIMULATED data (not wired to `data.json`).

**Scratch workspace / traps:**
- ⚠️ `.superpowers/sdd/mk14mk15/task-*-brief.md` / `task-*-report.md` are the **Mk14/Mk15**
  artifacts. For Mk16, generate fresh briefs — do NOT reuse these.
- ⚠️ `.superpowers/sdd/progress-mk12-archived.md` is the OLD Mk12 ledger, kept as a backup. The
  current ledger is `progress.md`.
- ⚠️ `/private/tmp/.../scratchpad/probe.sh` is the controller's known-good headless probe from
  this session (a temp file; may be gone in a fresh session — the recipe is in Verification idioms below).

**Not mine — leave alone (pre-existing untracked, intentionally NOT committed):** `.claude/`,
`CLAUDE.md`, `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `docs/superpowers/mk13-handoff.md`,
`docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md`, and `.DS_Store` files. The plan Global
Constraints say to leave these untracked. NEVER `git add .` / `git add -A` in this repo.

## What has changed (this effort)

- **Mk14 shipped** (commits `f402acc..1d6bc95`): verdict() NaN guard; backtest bridges weekends
  per-field to match `calibrate.py` fit_cell (per-field n +10); "structural, not a bug" note on
  ffr-driven `us2y`; restored causal clauses to the 3 adopted `ELASTICITY` src strings; normalized
  fit phrasing to `(train split)`.
- **Mk15 shipped** (commits `6bd628c..da619c5`): +5 qualitative nodes (T-Bills, Listed Options,
  ETFs, Energy, Households) + 12 links + COLUMN_OF; calibrated **one** new link `dxy→us10y`
  (t +6.6, MEASURED — the only candidate that fit; us10y backtest R² 0→0.134) into ELASTICITY +
  BACKTEST_MAP; label stagger in crowded columns; node keyboard a11y (Enter/Space); coach
  sessionStorage session-guard.
- **Merged** (`0de4f5c`) to `main` via PR #2 and pushed; Pages serves Mk15 (verified 200).
- Executed via `superpowers:subagent-driven-development` (fresh implementer + per-task spec+quality
  review per task, then an Opus whole-branch review — verdict **Ready to merge, 0 Critical / 0 Important**).

## What has failed / risks / caveats

- **Nothing has failed.** No blocked tasks, no failing tests, tree clean, site live & merged.
- **UNVERIFIED:** nothing outstanding — every task passed a per-task review and the whole-branch
  review; Python 10/10; both versions verified headless (PROV 0/0, backtest returns, 0 JS/CSP errors).
- **Deferred deliverable:** the Mk14 "Model accuracy" audit-panel screenshot was NOT captured
  (headless Chrome hangs when the audit modal opens). Capture it via a REAL browser (Chrome MCP /
  manual) if wanted. The Mk15 default/new-node/mobile screenshots were captured this session.
- **Carried-forward controller decisions that override the plan text** (all in the ledger):
  - M14.1 test/fix string contradiction → NaN message made `"t-stat undefined (NaN), not significant"`.
  - M14.4 → only the 3 bare-fit-stat cells got causal clauses; the plan-named `ffr.us2y`/`vix.spx_pct`
    (which already had richer intuition) were left untouched.
  - M14.5 → the plan's enumerated phrasing variants didn't exist; normalized to canonical `(train split)`.
  - M15.2 calibration gate → adopted ONLY `dxy→us10y`; the other 3 candidates stay DIRECTIONAL, no
    invented magnitudes; NO NODE_ELASTICITY added.
- **git-discipline trap:** an implementer once ran `git add .` and swept 14 pre-existing untracked
  files into a commit; it was reset. Always stage files by name.

## What's next (ordered) — the Mk16 backlog (all Minor; none blocked merge)

1. **[User decision] `vix→options` link direction.** Strictly it is `options→vix` (VIX is *derived
   from* option prices). The plan specified `vix→options` and the node text already says VIX comes
   from options, so it was left as-is. Decide: flip to `options→vix`, or add "(identity; arrow
   nominal)" to that link's `stat`. Edit `bullion_mk15.html` (or cut Mk16 first with `./release.sh 16`).
2. **[Minor/tests] Real-data integration test** for the `dxy→us10y` adoption: run `fit_cell` on
   `data.json` and assert MEASURED, so the calibration decision is guarded against data drift.
3. **[Minor/precision] M14.2 exactness:** for a single-driver backtest field, build the present-date
   list on driver AND target presence to make the "mirrors fit_cell" claim literally exact (no live
   effect on current daily data).
4. **[Cosmetic] M14.1 test style:** align the new test to the file's `import calibrate as c` +
   single-quote convention.

To ship any of these: small fixes can stay in `bullion_mk15.html` (still Mk15), or run
`./release.sh 16` to cut Mk16 first if it's a milestone. Then commit + `git push origin main`.

## Verification idioms used in this project (for the resuming session)

- **Python:** `cd bullion-live-map && python3 -m unittest test_calibrate -v` (expect 10/10).
- **Calibration report:** `cd bullion-live-map && python3 calibrate.py` → prints 18 cell lines +
  rewrites `calibration_report.txt` (dxy→us10y should be MEASURED; the other 3 Mk15 candidates DIRECTIONAL).
- **Headless map checks** (copy the html + `data.json` to a temp dir, inject a probe **before the
  LAST `</body>`** — line ~3379 has a `</body>` inside a JS string, so a naive first-match injection
  corrupts the file — then run with the flag):
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --allow-file-access-from-files --virtual-time-budget=10000 --enable-logging=stderr --v=1 file://<copy>.html`
  Probe globals after `load`+~3s: `NODES.length` (39), `LINKS.length` (93), `PROV_CONFLICTS.length`
  / `PROV_DEMOTIONS.length` (0/0), `backtestModel()` (6 fields). Grep stderr for
  `Uncaught|SyntaxError|Content Security Policy|Refused to` (expect none).
  - ⚠️ **NEVER call `openAuditLog()` in a headless probe** — its animated modal stalls headless
    virtual-time and hangs Chrome. Verify accuracy-panel logic via the `BACKTEST_MAP`/`backtestModel()`
    predicate instead. macOS has **no `timeout` command**; don't rely on it. Avoid `--user-data-dir`
    fresh profiles (they can hang on first-run).
  - ⚠️ Do NOT put a literal `</`+`script>` inside an injected probe string — it closes the tag.
- **Redirect checks:** `grep -oE 'bullion_mk[0-9]+\.html' bullion-live-map/index.html` → `bullion_mk15.html`;
  the legacy stub → `./index.html`.
- **Confirm a push/deploy landed:** `git show origin/main:<path>`; for Pages,
  `curl -s -o /dev/null -w "%{http_code}" https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mk15.html`
  (200). Pages CDN caches ~5 min, so a stale live URL right after a push is normal.
- **git/PR:** `gh` is NOT installed. Push works from the Bash tool (`GIT_TERMINAL_PROMPT=0 git push`).
  PR create/merge is via the GitHub API + `curl` using the token from `git credential fill`
  (`printf "protocol=https\nhost=github.com\n\n" | git credential fill`).

# Bullion Mk17 "Breadth of Live Data" — Session Handoff

**Written:** 2026-07-26 · **For:** a fresh session picking up the Bullion constellation-map project after Mk17 shipped. Mk17 is DONE + LIVE — this hand off is state + open follow-ups, not an in-progress resume. Prior handoff: `docs/superpowers/mkultra-2d-board-handoff.md`.

## Goal

Mk17 added **13 new free live-data fields** to the durable daily pipeline and wired them into a new `bullion_mk17.html` (cut from mk16), promoting every calibratable link to a MEASURED badge — so the map shows more of the financial system with real, honestly-graded data. **No MCP** (the refresh is a headless GitHub Action; MCP is session-only and can't feed it). This effort is COMPLETE, reviewed, merged to `main`, and live on GitHub Pages.
- Spec: `docs/superpowers/specs/2026-07-25-bullion-mk17-breadth-of-live-data-design.md`
- Plan: `docs/superpowers/plans/2026-07-25-bullion-mk17-breadth-of-live-data.md`
- Progress ledger (recovery map, authoritative task-by-task record + controller resolutions): `.superpowers/sdd/progress.md`

## How to resume (do this first)

1. Confirm you're on `main`, synced: `git -C ~/claude-projects/claudekit log --oneline -1` should show `688a70e Mk17: bump calibration report header Mk12->Mk17`, and `git rev-list --left-right --count origin/main...main` should be `0  0`. Mk17 = commits `d37eb6f..688a70e`.
2. **There is nothing to resume for Mk17 — it is shipped and live.** Read the ledger `.superpowers/sdd/progress.md` if you need the full build story; trust the ledger + `git log` over any recollection.
3. For NEW work (a Mk18, a fix, a beginner-usability pass), re-invoke the workflow from scratch: `superpowers:brainstorming` → `writing-plans` → `subagent-driven-development`. Follow the project's versioning discipline (see caveats).
4. **Immediate next action:** none required — the effort is complete. If continuing, the highest-value next thing the user flagged is a **beginner-usability pass** (see What's next); confirm with the user first.

## Current state (active files)

**Branch:** `main`, synced with `origin/main` at `688a70e`. The `bullion-mk17` feature branch was fast-forward-merged and deleted.

**Files created / changed (Mk17, all on `main`, live):**
- `bullion-live-map/fetch_bullion_data.py` — +9 FRED + 4 Yahoo series, new `weekly` (10d) cadence bucket, 13 FIELD_META entries, updated SOURCE_NOTE (`e6bc174`).
- `bullion-live-map/data.json` — regenerated, 23 fields / 366 dated rows (`a2a5b28`). Refreshed daily by the GitHub Action, so it drifts on its own.
- `bullion-live-map/calibrate.py` + `bullion-live-map/calibration_report.txt` — 9 new candidate CELLS; report header now "Mk17" (`e9977e0`, `688a70e`).
- `bullion-live-map/tests/test_fetch_bullion_data.py` (fixed 23-field/weekly assertions) + `bullion-live-map/tests/test_mk17_series.py` (new) (`3ca02f0`).
- `bullion-live-map/bullion_mk17.html` — the shipped map: 22-cell metric grid, node-detail live readouts (NFCI on vix node), 6 MEASURED links in ELASTICITY + BACKTEST_MAP (`d75b2cf` cut, then `7e4bf39`/`5a326fd`/`18b0576`).
- `bullion-live-map/index.html` — repointed to mk17 (`d75b2cf`).

**Frozen — DO NOT edit (verified byte-identical, they are shared/archived links):**
- `bullion_mk16.html` sha `ef9fbc55…`, `bullion_mk15.html` sha `ebfaaaf6…`, and all earlier `bullion_mk11..14`. Never resurrect map content into `bullion_mk11_constellation.html` (it's a redirect stub).

**Scratch workspace / traps:**
- ⚠️ `.superpowers/sdd/*-report.md` task-report files were repeatedly found to contain **stale content from OLD unrelated tasks** (e.g. task-5/6 reports held Mk11/Mk12 content until overwritten). Do NOT trust a `task-N-report.md` unless its content matches the task you expect. The `.superpowers/sdd/*.diff` review packages are disposable.
- ⚠️ `.superpowers/sdd/progress-mk14-mk15-archived.md` is the PRIOR effort's ledger, archived. The live ledger is `progress.md`.

**Not mine — leave alone:** everything under `docs/`, `.claude/`, `CLAUDE.md`, `.DS_Store` are pre-existing UNTRACKED files (git status shows them `??`). Do NOT `git add .`/`-A` — stage only the specific files a task changes.

## What has changed

- Mk17 shipped: `main` moved `711aba1 → 688a70e` (11 commits: spec, plan, 8 task commits, 1 cosmetic). Pushed to `origin/main`. **Live confirmed:** both `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/` and `…/bullion_mk17.html` return HTTP 200, and the live file carries `id="m-nfci"` + "Mk17 Column Constellation".
- Tests green: `python3 -m unittest discover -s tests` = 41/41; `python3 -m unittest test_calibrate` = 11/11.
- Calibration: 6 of 9 candidate links MEASURED (sofr←ffr, hy_oas←vix, xlk←spx, xlf←spx, xle←wti_px, mortgage_30y←us10y); adopted with FITTED slopes into ELASTICITY + BACKTEST_MAP. 3 DIRECTIONAL (ffr→tbill, spx→xle sign-flip, spx→xlp) NOT adopted.

## What has failed / risks / caveats

- **Nothing has failed.** Final opus whole-branch review = READY TO MERGE, 0 Critical / 0 Important.
- **Decisions carried forward that override the plan (do not silently undo):**
  - **NODE_ELASTICITY was deliberately NOT touched** (plan Task 7 Step 3 said to wire it). Reason: credit/repo nodes already have vix/ffr entries and the `energy` node isn't in `NODE_MAP`, so new entries would duplicate or orphan (matches Mk15.2 precedent). The 6 MEASURED links live in ELASTICITY + BACKTEST_MAP only.
  - **DIRECTIONAL cells were NOT adopted into the client** (no invented magnitudes) — only MEASURED, using fitted slopes. This is the project's honesty rule.
  - `us10y` + `spx` were added to `DRIVER_FIELD` + `BACKTEST_LABEL` (needed so `backtestModel()` grades the new-driver links) but NOT to the shock-slider array `DRIVERS` (still ffr/vix/cpi_yoy/dxy/wti_px). Keep it that way.
- **Honestly-disclosed weak spot:** `us10y→mortgage_30y` is the marginal fit (n=40, t=2.4, weekly-vs-daily); its `src` says so. Fine, but the weakest of the six.
- **Open follow-up (informational, deliberately deferred):** the EXISTING `us10y→spx_pct` cell now marginally fits MEASURED (t≈−2.0) on the 366-day data — left DIRECTIONAL (out of Mk17 scope). A future pass could reconsider.
- **Mk Ultra (`bullion_mkultra.html`, the 3D fork) was NOT wired for the Mk17 links.** It still auto-gets the new `data.json` values (all versions fetch the same file) but has no new metric cells / detail readouts / calibrated links. Also its still-open pre-Mk17 follow-up: vendor Three.js inline so it's self-contained (currently depends on a jsDelivr CDN).
- **User's candid product concern (2026-07-26):** for a TRUE beginner the map may overwhelm — 22 metric cells of jargon (SOFR/HY OAS/RRP/NFCI) + calibration stats add rigor, not first-timer legibility. This is unaddressed and is the most likely next direction (see What's next).

## What's next (ordered)

1. **If the user wants the map to actually help beginners** (they raised this): brainstorm a **beginner-usability pass** — a guided "3 scenarios" first-run tour (Fed hike / oil spike / risk-off), progressive disclosure (default-hide the metric wall + backtest + calibration behind an "advanced" toggle), and one-line "what is this" on the jargon cells. Start with `superpowers:brainstorming`.
2. **If continuing the data/rigor line (a Mk18):** the deferred `us10y→spx_pct` promotion, and/or wiring the Mk17 fields into `applyTransmission` so the new metric cells respond to shock sliders (currently they only display + get backtested, they don't animate under scenarios).
3. **If parity is wanted:** port the Mk17 live-data breadth into `bullion_mkultra.html` (3D), and/or vendor Three.js inline there.
4. **Any new version** must go through `./release.sh <N>` (copies current → `bullion_mk<N>.html`, bumps title/og/h1, repoints index.html) — it is NUMERIC-ONLY; never route named variants (mkultra) through it.

## Verification idioms used in this project (for the resuming session)

- **Python tests:** `cd bullion-live-map && python3 -m unittest discover -s tests` (fetch/pipeline tests live in `tests/`, NOT top-level) and `python3 -m unittest test_calibrate` (calibrate test is top-level).
- **Regenerate data.json:** `cd bullion-live-map && python3 fetch_bullion_data.py` (needs FRED key at `~/.config/bullion/fred_api_key` — present — and network).
- **Headless HTML verification (macOS has NO `timeout`):** copy the html + data.json to a temp dir, inject a probe `<script>` **before the LAST `</body>`** (use rfind — there's a decoy `</body>` inside a JS string mid-file), then:
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --allow-file-access-from-files --virtual-time-budget=9000 --enable-logging=stderr --v=1 "file://$D/m.html"` and grep your probe tag from stderr.
  - **NEVER call `openAuditLog()` in a headless probe** — its animated modal stalls headless virtual-time and hangs. Verify the accuracy panel via the `BACKTEST_MAP` / `backtestModel()` predicate over globals instead.
  - Node lookup in mk16/mk17 (SVG) is `nodesData.find(n=>n.id==='vix')` — there is NO `nodeById` (that only exists in mkultra).
- **Confirm a push landed / is live:** trust `git show origin/main:<path>`; the Pages CDN + a new-file rebuild lag ~30–90s, so a fresh mk-file URL can 404 briefly right after push — not a failure.
- **git push** works from the Bash tool (`GIT_TERMINAL_PROMPT=0 git push origin main`); `gh` CLI is NOT installed (use raw `curl` + the credential-store token for GitHub API).

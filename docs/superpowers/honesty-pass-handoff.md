# Bullion "Honesty Pass" (Spec 1 of 2) — Session Handoff

**Written:** 2026-07-27 (refreshed at `f7a90e6`, end of session) · **For:** a fresh session picking up the Bullion map after the honesty pass shipped. Spec 1 is DONE, pushed and live — this is state + the queued Spec 2, not an in-progress resume. Prior handoff: `docs/superpowers/mk17-handoff.md`.

## Goal

The map graded its own trustworthiness in the Audit Log via `provCoverage()`, which counts
`l.conf || CONF.UNVERIFIED` — and **48 of the 93 runtime links carried no `conf` at all**, so two
thirds of the graph was reported as "set by feel; the sign may be wrong" despite every link carrying
a `stat:` citation. Since Mk17 `data.json` holds 23 fields over 366 days, so 37 link pairs could be
*fitted* rather than asserted. This pass made every causal claim carry a tier it earned, caught
wrong-signed arrows nothing was checking, and stopped the teaching copy asserting undated figures.

- Spec: `docs/superpowers/specs/2026-07-27-bullion-honesty-pass-design.md`
- Plan: `docs/superpowers/plans/2026-07-27-bullion-honesty-pass.md` (mirrors `~/.claude/plans/unified-scribbling-acorn.md`)
- No SDD ledger this time — the work ran inline, so **`git log 688a70e..HEAD` is the authority.**

## How to resume (do this first)

1. Confirm you are on `main`, synced: `git -C ~/claude-projects/claudekit log --oneline -1` should show `f7a90e6 Add the honesty-pass session handoff`, and `git rev-list --left-right --count origin/main...main` should be `0  0`. This effort is `a3f26bb..f7a90e6` — **11 commits** on top of Mk17's `688a70e`, working tree clean of tracked changes.
2. **There is nothing to resume for Spec 1 — it is shipped and live.** `index.html` → `bullion_mk18.html`, both HTTP 200 on Pages.
3. For Spec 2 (the queued work), start from scratch with `superpowers:brainstorming` → `writing-plans`. The four approved decisions are already recorded in "What's next" below — do not re-litigate them.
4. **Immediate next action:** none required. If continuing, brainstorm **Spec 2, the Mk Ultra experience pass** (beginner legibility + visual elevation + motion + WebGL fallback), whose scope the user already chose.

## Current state (active files)

**Branch:** `main`, 11 commits ahead of base `688a70e`, synced with `origin/main`. No tracked file
is modified — everything below is committed and pushed.

**Files created / changed:**
- `bullion-live-map/bullion_mk18.html` — **the new shared map** (`ed18751`), cut from mk17 via `./release.sh 18`. Carries the full honesty pass + 2D tier encoding.
- `bullion-live-map/bullion_mkultra.html` — the 3D fork, same data + 3D tier encoding (`733dc63`, `fed1c0d`, `2ecf9a5`, `e88e802`).
- `bullion-live-map/calibrate.py` — new link-fitting pass: `NODE_FIELD`, `PCT_FIELDS`, `field_kind`, `_array_rows`, `_row_fields`, `parse_links`, `link_candidates`, `link_verdict`, `link_report`, `MIN_LINK_N` (`85ff624`, `93e5b1c`).
- `bullion-live-map/test_calibrate.py` — 11 → **33 tests** (`93e5b1c`).
- `bullion-live-map/calibration_report.txt` — now has `=== ELASTICITY CELLS ===` + `=== LINKS ===` sections. **This file is the record of every tier, flip and conflict — read it, don't re-derive.**
- `bullion-live-map/index.html` — repointed to mk18.
- `docs/superpowers/specs/2026-07-27-bullion-honesty-pass-design.md` — marked COMPLETE (`4db09d5`).
- `docs/superpowers/honesty-pass-handoff.md` — this file (`f7a90e6`). Unlike most handoffs here it
  **is** tracked, so don't archive or move it; git preserves it.

**Frozen — DO NOT edit (verified byte-identical after this work):**
`bullion_mk17.html` `9989bee3…`, `bullion_mk16.html` `ef9fbc55…`, `bullion_mk15.html` `ebfaaaf6…`, and all earlier `mk11..14`. Never resurrect map content into `bullion_mk11_constellation.html` (a redirect stub).

**Scratch workspace / traps:**
- ⚠️ **The causal graph is TWO arrays, not one.** `LINKS` (86 rows) and `PLUMBING_LINKS` (16 rows) are merged at load — 9 plumbing rows *supersede* the same-`(s,t)` `LINKS` row, 7 are *appended* → **93 runtime links**. Reading `LINKS` alone grades 9 rows that never render. This produced two wrong counts before being caught and flipped one result (`fed→repo`). `calibrate.py:parse_links()` performs the merge and is the reference. Sanity check: `grep -c "^  {s:'"` over the file (102) exceeds the `LINKS` row count (86) whenever a second array exists.
- ⚠️ The one-off rewrite script lives at `/private/tmp/claude-501/.../scratchpad/tier_links.py` — **temp dir, will vanish.** Its rules are documented in the spec; nothing depends on it now.
- ⚠️ `bullion-live-map/__pycache__/` and `tests/__pycache__/` are untracked build noise.

**Not mine — leave alone:** `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `CLAUDE.md`, `.DS_Store`, `docs/superpowers/archive/`, and the older handoffs — all pre-existing and untracked. **Never `git add .`/`-A`**; stage only the files a task changes.

## What has changed

- **Link tiers: 21/24/48 → 16 measured / 74 directional / 3 unverified, 0 untiered** across 93 links. Verified in-browser in both files; `provCoverage()` segments sum to its total.
- **4 arrows flipped to match the data**, each stating its old hand sign in `stat:`: `credit→equit` (+1→−1, t=12.5 — wider HY spreads do not lift stocks), `usd→oil` (−1→+1, t=4.7, window caveat recorded), `mortgage→credit` (−1→+1, t=2.0), `vix→defn` (+1→−1, t=2.0). 10 weaker contradictions logged as conflicts, not acted on.
- **All 39 nodes now carry a `Source:` line** (was 31). Every hardcoded figure is as-of-dated, and the 6 genuinely unattributed claims either name a source or say they have none.
- **Live readings in the detail panel**: 19 of 39 nodes (Mk Ultra had none before; mk17 had 16 and one was broken).
- **Evidence is now a visual channel**: colour = sign, width = strength, opacity + dash = evidence. Only the 3 genuinely unverified links are dashed (was 6 `aud:false` links whose signs are now settled). Legend gained an EVIDENCE block; relationship rows gained tier badges.
- **Tests:** `tests/` 41/41, `test_calibrate` 33/33 (was 11). Re-confirmed green at `f7a90e6`.
- **Live confirmed:** folder URL and `bullion_mk18.html` both HTTP 200; the live mk18 carries `tier-badge` and the evidence legend.

## What has failed / risks / caveats

- **Nothing has failed.** All items shipped and were verified in a browser, not just reasoned about.
- **UNVERIFIED:** no independent code review has run on these 11 commits (previous efforts in this project ended with an opus whole-branch review; this one did not). Run `/code-review` before building on it — that is the single biggest gap in this effort.
- **Untracked housekeeping never done** (deliberately, to keep `git add` surgical): `bullion-live-map/__pycache__/`, `tests/__pycache__/` and three `.DS_Store` files will clutter every `git status`. There is no `.gitignore` covering them. Also undecided: whether the five never-tracked handoffs in `docs/superpowers/archive/` should start being tracked.
- **Two counting errors happened mid-effort and are already corrected in git** (`1ffc320`, `93e5b1c`). If any doc or comment still says "86 links" or "57 untiered", it is stale — the truth is **93 / 48**.
- **Decisions carried forward that override the plan (do not silently undo):**
  - **Sign flips are applied mechanically** at |t| > 2, by user instruction. I argued `fed→repo` looked like a shared-trend artefact; it turned out moot once the plumbing merge was fixed. Do not add per-link judgment without asking.
  - **`MIN_LINK_N = 30`** blocks promotion on monthly series (3–9 usable daily diffs). Not in the original plan; added because it was promoting `cpi→fomc` on n=8.
  - **Same-field pairs are excluded** from fitting (`fomc→ffr`, `tsy→yield`, `usd→dxy_fx`) — self-regression always "fits".
  - **An insignificant fit is NOT evidence a relationship is false** — it stays `directional` with an honest note. Most of these claims are structural and have no daily-frequency signal.
  - **Definitional links** (`fomc→ffr`, `banks→fins`) read as `directional` and say so in prose; no 4th tier was added.
  - **Fields shown from the data.json snapshot rather than scenario state are marked** "* as published; not moved by scenarios". Don't drop the marker.
- **`usd→oil` now draws POSITIVE**, contradicting the textbook dollar-pricing channel. This is the fitted sign over the training window with the caveat stated in `note:`/`stat:`. Expect a question about it; it is deliberate, not a bug.
- **Mk Ultra still depends on the jsDelivr Three.js CDN** and renders a **silent black void** where WebGL is unavailable. Folded into Spec 2.

## What's next (ordered)

1. **Spec 2 — the Mk Ultra experience pass.** Scope the user already approved: **(a)** beginner legibility (progressive disclosure of the metric wall, plain-English tooltips on jargon, guided first-run tour of 3 scenarios); **(b)** visual elevation using the installed `impeccable` / `frontend-design` / `ui-ux-pro-max` skills; **(c)** motion + micro-interaction polish; **(d)** the WebGL/CDN fallback to the existing 2D Overview board instead of a blank page. Start with `superpowers:brainstorming`.
   Observed problems to design against (from a live screenshot): only 3 of 39 nodes carry a visible label so a beginner sees anonymous dots; composition is bottom-right heavy with an empty top-left; every panel hides behind one "⚙ Tools" button so none of the 23 live fields is visible on load; the 12-swatch legend has near-indistinguishable purples; no affordance shows the globe is drag-to-spin.
2. **Optional before (1):** `/code-review` this branch — 9 commits, no review yet.
3. **Deferred, informational:** port Mk17's 6 calibrated ELASTICITY links + 22-cell metric grid into Mk Ultra (its scenario `state` still carries only the 12 Mk15 fields); vendor Three.js inline; reconsider `us10y→spx_pct`.
4. **Any new version** goes through `./release.sh <N>` — numeric-only; never route `mkultra` through it.

## Verification idioms used in this project (for the resuming session)

- **Python:** `cd bullion-live-map && python3 -m unittest discover -s tests` (41/41) and `python3 -m unittest test_calibrate` (33/33 — top-level, not in `tests/`).
- **Re-run the calibration:** `python3 calibrate.py data.json bullion_mkultra.html` — second arg is the map to parse; writes `calibration_report.txt`.
- **Headless probe (the workhorse here):** copy the html + `data.json` to a temp dir, inject a `<script>` before the **last** `</body>` (use `rfind` — there is a decoy `</body>` inside a JS string), then run Chrome with `--headless=new --allow-file-access-from-files --virtual-time-budget=15000 --enable-logging=stderr --v=1` and grep your `PROBE_` tags from stderr. macOS has no `timeout`.
  - **Mk Ultra needs software WebGL:** add `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`, or the globe renders blank. mk18 (2D/SVG) needs only `--disable-gpu`.
  - **NEVER call `openAuditLog()`** in a probe — its animated modal stalls headless virtual-time and hangs.
  - `linkObjs` is **inside the renderer closure** and not reachable from a probe. To inspect it, patch the *copy* to add `window.__getLinks = () => linkObjs;` just before `function buildLinkObjects() {`. `NODES` is likewise unreachable — use `nodesData`.
- **Freeze check:** `shasum -a 256 bullion_mk15.html bullion_mk16.html bullion_mk17.html` before and after any change.
- **Confirm a push landed:** trust `git show origin/main:<path>`. A brand-new `mk<N>.html` URL can 404 for ~30–90s while Pages rebuilds — not a failure.
- **git push** works from the Bash tool (`GIT_TERMINAL_PROMPT=0 git push origin main`); `gh` is NOT installed (use raw `curl` + the credential-store token for API calls).

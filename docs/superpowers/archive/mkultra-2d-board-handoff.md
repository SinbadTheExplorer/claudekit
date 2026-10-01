# Bullion "Mk Ultra" — Classification-in-node + 2D Overview board — Session Handoff

**Written:** 2026-07-25 · **For:** a fresh session resuming the Mk Ultra work. Two things are DONE this session and pushed live (four 3D UX fixes); the next job is **executing the approved implementation plan** for (1) moving the classification stage off the globe into each node's detail header, and (2) a new 2D "Overview" kanban tab. No code for that plan has been written yet.

## Goal

Make Mk Ultra (the 3D Three.js version, `bullion_mkultra.html`) easier to read: take the 7 floating classification-stage labels off the rotating globe and show each node's stage in its detail-panel header instead (`Group · Stage`), and add a calm 2D **Overview** tab — a 7-column kanban (one column per causal stage, left→right) of node cards that open the same detail panel. Why: a 3D sphere is a hard first read for a beginner; the board is a plain-English on-ramp, and the floating labels drift over the orbs as clutter.

- Spec: `docs/superpowers/specs/2026-07-25-mkultra-2d-overview-board-design.md` (committed `b5885b7`)
- Plan: `docs/superpowers/plans/2026-07-25-mkultra-2d-overview-board.md` (committed `7d1d343`) — **the authority; two tasks, exact edits + code + Chrome-MCP verification.**
- Prior handoff (the 4 shipped fixes + full Mk Ultra build context): `docs/superpowers/mkultra-handoff.md`
- Project memory: `project-bullion-live-map.md` (live URLs + pipeline).

## How to resume (do this first)

1. Confirm state: `git rev-parse --abbrev-ref HEAD` (expect `main`); `git log --oneline -4` — expect `7d1d343` (plan) → `b5885b7` (spec) → `d34eb27` (4 fixes) → `2577c2b` (Mk Ultra). **`main` is 2 commits AHEAD of `origin/main` (`d34eb27`)** — the spec + plan are local-only docs, not pushed; that's fine, no code to deploy in them.
2. This is UI work with an **approved plan mid-flight**. Re-invoke `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to run the plan task-by-task. Trust the plan file + `git log` over recollection.
3. **The plan was written and approved; the user chose to pause before picking an execution mode.** When resuming, either ask "subagent vs inline?" or just start Task 1 (it's only 2 tasks in one file — inline is the leaner choice, my recommendation stands).
4. **Immediate next action:** execute **Task 1** of `docs/superpowers/plans/2026-07-25-mkultra-2d-overview-board.md` (classification off the globe → into the detail header). Then checkpoint, then Task 2 (the board).

## Current state (active files)

**Branch:** `main`, 2 commits ahead of `origin/main` (`d34eb27`). `d34eb27` is pushed + live on Pages; `b5885b7` + `7d1d343` are local docs only.

**Files created / changed this session:**
- `bullion-live-map/bullion_mkultra.html` — **changed + committed in `d34eb27`, pushed, LIVE.** The 4 fixes: click-to-highlight (emissive + 1.35× scale on the selected node), translucent orbs (`NODE_BASE_OPACITY = 0.4`, `depthWrite:false`), gold-pill stage labels, and `focusCameraOn()` camera redirect on related-node clicks. This is the file **both plan tasks edit next.**
- `docs/superpowers/specs/2026-07-25-mkultra-2d-overview-board-design.md` — NEW, committed `b5885b7`.
- `docs/superpowers/plans/2026-07-25-mkultra-2d-overview-board.md` — NEW, committed `7d1d343`.

**Files the PLAN will modify (untouched by the plan so far):**
- `bullion-live-map/bullion_mkultra.html` — the only file both tasks touch. Task 1 edits `openDetail` (~2492) + deletes `buildStageLabels`/`updateStageLabels`/`stageLabelEls`. Task 2 adds header tabs, a `#board-view` container, board CSS, and `buildBoard()`/`showView()`. **Line numbers in the plan are `~approximate`** — grep for the anchor strings, don't trust exact line numbers (Task 1's deletions shift everything below).

**Traps / leave alone:**
- ⚠️ **`bullion_mkultra.html` must stay the ONLY edited file.** `bullion_mk15.html` must remain byte-identical: `shasum -a 256` == `ebfaaaf60a63d573…` (verified this session). `index.html`/`release.sh`/`data.json` untouched. Task 2 Step 9 re-checks this.
- ⚠️ **No new dependencies** — the board is pure DOM/CSS; do NOT add a treemap/D3/Three import for it.
- ⚠️ `d.col` is guaranteed present (`buildGraph()` defaults it to `5`/Markets); `COLUMN_TITLES` has exactly 7 entries. Both the detail header AND the board column are driven by the same `d.col`, so they can't disagree.
- ⚠️ `release.sh` is numeric-only (`mk<N>`) and **cannot** cut a named "ultra" variant — never run it expecting that. Mk Ultra is hand-maintained.
- **Not mine — leave alone:** untracked pre-existing files in `git status` (`.DS_Store`×N, `.claude/`, `CLAUDE.md`, `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md`, the other handoff `.md`s). Do not commit them.

## What has changed

- `d34eb27` **Mk Ultra: highlight clicked nodes, translucent orbs, readable band labels, camera redirect.** All 4 verified in Chrome MCP (0 console errors) + confirmed LIVE on Pages (grepped `focusCameraOn` from the deployed URL). Pushed.
- `b5885b7` **Spec** for the classification-in-node + 2D board. Local only.
- `7d1d343` **Plan** (2 tasks) for same. Local only. **Approved by the user; not yet executed.**

## What has failed / risks / caveats

- **Nothing has failed.**
- **UNVERIFIED / NOT STARTED:** the classification-in-node change and the 2D Overview board are **designed + planned but not implemented.** Zero code exists for them yet.
- **UNVERIFIED ON A REAL DEVICE:** as with all prior Mk Ultra work, everything is desktop-Chrome only. The new board's phone reflow (Task 2 Step 8, horizontal scroll) is planned but should ideally get a real-phone check.
- **Decision carried forward (overrides nothing in the plan, but note it):** v1 board is deliberately **static** — it does NOT recolor on scenario runs and does NOT animate (YAGNI; deferred in the spec). Don't add those without asking.
- **Mk Ultra is not self-contained** (loads Three.js r160 from a pinned jsDelivr CDN via importmap). Unrelated to this plan, but a locked-down browser could block the globe; the board (pure DOM) would still render.

## What's next (ordered)

1. **Execute Task 1** of the plan: serve first (`cd bullion-live-map && python3 -m http.server 8755`). Edit `openDetail` to render `Group · Stage`, add `.detail-stage` CSS, delete the 3 stage-label functions/refs, `grep` to confirm no orphan `stageLabelEls`/`buildStageLabels`/`updateStageLabels`, verify in Chrome MCP (no floating pills; header shows e.g. "Central Bank · Policy & Fiscal"; 4 prior fixes still work), commit.
2. **Checkpoint** (if subagent-driven, two-stage review here), then **execute Task 2**: header tabs + `#board-view` + board CSS + `buildBoard()`/`showView()` + call `buildBoard()` at the tail of `buildGraph()`. Verify 7 columns / 39 cards / click→detail / tab switching / narrow-viewport horizontal scroll / mk15 sha unchanged. Commit.
3. **Ask before pushing.** Deploy flow: commits go directly to `main`; `git push origin main` (this also pushes the still-unpushed `b5885b7`+`7d1d343` docs); GitHub Pages rebuilds ~30–60s. Only push when the user asks.

## Verification idioms used in this project (for the resuming session)

- **Serve:** `cd bullion-live-map && python3 -m http.server 8755` → `http://localhost:8755/bullion_mkultra.html?cb=$RANDOM` (http only; `file://` is blocked by the Chrome extension). Backgrounded `http.server` here has died with exit 144; a `nohup … & disown` survives.
- **Drive via Chrome MCP:** load the core browser tools in ONE `ToolSearch` (`select:mcp__claude-in-chrome__tabs_context_mcp,…navigate,…computer,…read_console_messages,…javascript_tool`). Page internals (`Renderer`, `openDetail`, `nodesDataIndex`) ARE reachable from the page console via `javascript_tool` (e.g. `openDetail(nodesDataIndex['fed'])`, `[...document.querySelectorAll('.board-card')].length`). Always `read_console_messages` with `onlyErrors:true` after interactions — target is 0 errors.
- **Regression after ANY Mk Ultra edit:** `shasum -a 256 bullion_mk15.html` must equal `ebfaaaf6…`; `git status` must show only `bullion_mkultra.html` changed under `bullion-live-map/`.
- **Confirm live deploy after a push:** poll `curl -s "<pages-url>?cb=$RANDOM" | grep -c "<distinctive-new-string>"` until >0 (e.g. `board-view` or `buildBoard` once Task 2 ships). Pages URL: `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mkultra.html`.
- **Deploy:** commits go directly to `main` (no PR); push only when asked; `gh` not installed — use `git`/`curl`.

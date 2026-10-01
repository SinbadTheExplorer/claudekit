# Bullion "Mk Ultra" (3D) + Mk15 phone fix — Session Handoff

**Written:** 2026-07-25 · **For:** a fresh session resuming the Bullion map. Two things shipped live this session: (1) a Mk15 phone-layout bug fix, (2) the new **Mk Ultra** 3D orbital-sphere version. Most likely next job: respond to the user's real-phone re-test of either, or the optional follow-ups below.

## Goal

Two efforts, both **shipped to `main` and confirmed live on GitHub Pages**:
1. **Mk15 phone fix** (commit `accfde1`) — on short mobile viewports (Instagram in-app browser) node bubbles/labels rode over the row titles, and the green Equity/Credit "Markets" nodes overlapped. Root cause: portrait bands were spaced across the *measured* height; short webviews compressed them. Fixed by laying portrait out at a fixed minimum virtual height and letting the SVG viewBox scale it to fit + desktop crowded-column radius clamp + diverging label stagger.
2. **Mk Ultra** (commit `2577c2b`) — a **separate experimental version** (`bullion_mkultra.html`) that renders the same graph as an interactive **3D orbital sphere** in Three.js, with **full feature parity** to Mk15. Sibling to Mk15, not a replacement.

Authorities:
- Plan (Mk Ultra): `~/.claude/plans/create-a-seperate-version-mossy-tower.md`
- Map-build authority (the Mk14/Mk15 build itself): `docs/superpowers/archive/mk15-handoff.md`
- Prior handoff (Mk15 phone fixes, links further back): `docs/superpowers/mk15-phone-fixes-handoff.md`
- Project memory: `project-bullion-live-map.md` (has both updates + the live URLs)

## How to resume (do this first)

1. Confirm state: `git rev-parse --abbrev-ref HEAD` (expect `main`); `git log --oneline -3` — expect `2577c2b` (Mk Ultra) on top of `accfde1` (Mk15 phone fix). `main == origin/main == 2577c2b`, both pushed & live.
2. This is UI/visual work — **no active SDD plan/skill loop is running.** Trust `git log` + this doc over recollection.
3. To view: `cd bullion-live-map && python3 -m http.server 8755` → `http://localhost:8755/bullion_mkultra.html` (or `bullion_mk15.html`). `file://` is blocked by the Chrome extension; use http. Cache-bust with `?cb=$RANDOM`.
4. **Immediate next action:** ask the user for / respond to a **real-phone re-test** of both changes (esp. the Instagram in-app browser). All verification so far is desktop-Chrome emulation, NOT a real device.

## Current state (active files)

**Branch:** `main`, 2 commits ahead of `0de4f5c` (both pushed; `main == origin/main == 2577c2b`).

**Files created / changed:**
- `bullion-live-map/bullion_mkultra.html` — **NEW, committed in `2577c2b`.** The 3D version. Live at `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mkultra.html`. All changes are in its inline `<script>`/`<style>` + an ESM importmap in `<head>`.
- `bullion-live-map/bullion_mk15.html` — **changed in `accfde1`** (phone fix). SHA-256 now `ebfaaaf60a63d5732e7363c758a8cee43f75bfbdbc95f2838063e590546eb55f`. Mk Ultra was seeded from this exact file, then verified to keep it byte-identical.

**Files later work will modify (untouched so far):**
- `bullion-live-map/index.html` — front door, **still redirects to `bullion_mk15.html`** (Mk15 is the shared link). Mk Ultra is deliberately NOT the index target. Do not repoint unless the user asks.
- `bullion-live-map/release.sh` — cuts numeric versions only. Untouched.

**Not mine — leave alone:** pre-existing untracked files show in `git status` but aren't this work: `.DS_Store` (×3), `.claude/`, `CLAUDE.md`, `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md`. Do not commit them.

## What has changed

- `accfde1` **Mk15: fix phone title/node overlap + green Markets overlap.** Portrait floors to a min virtual height (7×92) and viewBox scales to fit; desktop crowded-column radius clamp + diverging label stagger. Verified 0 title/node clashes at 314px & 737px stages; green pair now 16px gap. Pushed + live.
- `2577c2b` **Mk Ultra: 3D orbital-sphere version (Three.js).** Nodes on a sphere (latitude = causal `col` 0→6 pole-to-pole, color by group), links as radial-bulge arcs (color by sign, dashed=unaudited, cone arrowheads), OrbitControls spin/zoom + idle auto-rotate, projected HTML labels w/ back-hemisphere declutter + latitude stage titles, ported animations (hub pulse, reveal-burst tween, focus dim, 450ms shock recolor). **Full parity:** the 2D SVG render layer was refactored behind a `Renderer` adapter (`build/redraw/setVisibility/focus/clearFocus/setLayerFilter/recolor/nodeById/nodes` + `onNodeActivate/Hover/Leave/BackgroundClick`); scenarios→recolor, audit log, backtest, AI, live-data picker, legend filter, glossary, coach all verified working in-browser. Built by a **claude-fable-5** subagent over 4 checkpoints, each verified via Chrome MCP; 0 console errors throughout. Pushed + live.

## What has failed / risks / caveats

- **Nothing has failed.** But note:
- **UNVERIFIED ON A REAL DEVICE.** Both changes were verified only in desktop-Chrome emulation (incl. a forced narrow/short viewport by setting `#app` width/height + dispatching `resize`). The real Instagram in-app browser behavior is inferred. **Get the user's real-phone result before changing anything;** a "still broken" report is often just stale cache (in-app browsers cache hard — have them open outside Instagram / clean-reload).
- **Mk Ultra is NOT self-contained.** It loads Three.js r160 + OrbitControls from a **pinned jsDelivr CDN** (`three@0.160.0`) via an ESM importmap; its CSP meta allow-lists that one host. A locked-down in-app browser could block the CDN and the globe wouldn't render. **Open follow-up the user may want: vendor Three.js inline** (like the existing d3 blob) to make it fully self-contained.
- **Traps for a resuming session:**
  - `release.sh` is numeric-only (`bullion_mk<N>.html`, digit-guard + monotonic-guard) and its `grep`/`sed` are hardcoded to `mk<N>`. It **cannot** cut a named variant — Mk Ultra was hand-created. Never run `release.sh` expecting it to handle "ultra".
  - `index.html` must keep pointing at Mk15; don't repoint to Ultra unless asked.
  - Keep `bullion_mk15.html` byte-identical (`ebfaaaf6…`) — Mk Ultra work proved this and any Ultra edit must not touch mk15.
  - The `Renderer` adapter + all 3D code live **only in `bullion_mkultra.html`**, not mk15. mk15 is still pure 2D SVG/d3.
  - The map has **39 nodes** (not the "~113" some older notes estimated).
  - `openAuditLog()` opens an `about:blank` popup window — Chrome MCP can't screenshot it (it sets the tab title, which is enough to confirm it ran). Also historically stalls headless virtual-time; don't call it from a headless probe.

## What's next (ordered)

1. **Get the user's real-phone re-test** of `accfde1` (Mk15 phone fix) and `2577c2b` (Mk Ultra). If good: done. If bad: get a fresh screenshot + which browser before editing; reproduce with a forced short/narrow viewport first.
2. **(Optional) Vendor Three.js inline** in `bullion_mkultra.html` so it has zero external deps. Then re-verify in Chrome and re-push.
3. **(Optional) Discoverability:** add an "Ultra" link somewhere (e.g. a small version switcher) so people can find the 3D version — currently only reachable by its direct URL.

## Verification idioms used in this project (for the resuming session)

- **Serve:** `cd bullion-live-map && python3 -m http.server 8755` → `http://localhost:8755/bullion_mkultra.html` (http only; cache-bust `?cb=$RANDOM`). Note: backgrounded `http.server` processes here have been dying (~exit 144) — a detached `nohup python3 -m http.server 8755 & disown` survived longer.
- **Reproduce the PHONE bug (2D Mk15):** narrow alone isn't enough — force a *short* stage. Set `#app` `width:390px; height:437px`, override `fitAppToViewport` to pin that height, dispatch `resize`; measure title↔node/label bbox overlaps in the console.
- **Verify Mk Ultra 3D:** drive via Chrome MCP. Inspect placement with `Renderer.nodes()` (check x/y/z, latitude-by-col). Force a phone viewport by setting `#app` width + dispatching resize (3D is viewport-independent, resize is camera-only — expand state should persist). Confirm 0 console errors after each interaction. Test click→detail, hover→dim, run a scenario→recolor, legend filter (drive `applyLayerFilter()` and check a node's a11y button `disabled`/`aria-hidden` flip).
- **Regression after any Ultra edit:** `shasum -a 256 bullion_mk15.html` must equal `ebfaaaf6…`; `git status` must show `index.html`/`release.sh`/`data.json` unchanged.
- **Confirm live deploy after push:** poll `curl -s "<pages-url>?cb=$RANDOM" | grep -c "Mk Ultra"` until >0 (Pages rebuild ~30–60s; a fresh file 404s until the build lands).
- **Deploy flow:** commits go **directly to `main`** (no PR); GitHub Pages serves `main`. Push only when the user asks. `gh` not installed — use `git`/`curl`.

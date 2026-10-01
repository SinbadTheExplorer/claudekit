# Bullion Mk15 — Phone/Mobile Layout Fixes — Session Handoff

**Written:** 2026-07-24 · **For:** a fresh session resuming the Bullion map after a round of **phone-presentation fixes to the already-live Mk15**. Either (a) respond to the user's real-device re-test of these fixes, or (b) pick up the pre-existing Mk16 backlog.

## Goal

Make the **live Mk15 map look good and behave correctly on phones.** The map was built and shipped (see prior handoff) but rendered badly on mobile: column titles printed on top of the node bubbles, nodes overlapping, the whole layout stretched vertically off the screen, and the page scrolling "into the void." This session fixed all of that. **No new Mk version was cut** — these are edits to the existing `bullion_mk15.html`.

- Prior handoff (the Mk14/Mk15 build — still the authority on the map itself): `docs/superpowers/mk15-handoff.md`
- Progress ledger for the build (recovery map): `.superpowers/sdd/progress.md`
- Live map (permanent folder URL): https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/
- Direct Mk15 URL: https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mk15.html

## How to resume (do this first)

1. Confirm state: `git rev-parse --abbrev-ref HEAD` (expect `main`) and `git log --oneline 0de4f5c..HEAD` — expect exactly two commits: `cd4614b` then `efc7cfc`. `main` == `origin/main` == `efc7cfc` (both pushed & live).
2. This is a UI/visual task, not the SDD build workflow. There is **no active plan/skill loop running**. Trust `git log` + this doc over any recollection.
3. To see the map: `cd bullion-live-map && python3 -m http.server 8731`, then open `http://localhost:8731/bullion_mk15.html`. To test the **phone** path you must force a narrow, *tall* viewport (see "Verification idioms" — a normal-height narrow window does NOT reproduce the bug).
4. **Immediate next action:** wait for / ask the user for a **real-phone re-test result** of commit `efc7cfc`. The fix is verified only in desktop-Chrome emulation, NOT yet confirmed on a real device (esp. the Instagram in-app browser the user uses). If they report it's still wrong, get a fresh screenshot before changing anything.

## Current state (active files)

**Branch:** `main`, 2 commits ahead of base `0de4f5c` (both pushed; `main == origin/main`).

**Files created / changed (committed in `cd4614b` + `efc7cfc`):**
- `bullion-live-map/bullion_mk15.html` — **the only changed file.** It IS the live map (`bullion-live-map/index.html` redirects to it; `release.sh` currently targets `bullion_mk15.html`). All changes are in the inline `<script>` / `<style>`. Key additions/edits:
  - `PORTRAIT_BAND` const (now includes `maxBand: 118`) + new `portraitBandGeom()` helper — shared, capped, vertically-centered band geometry used by BOTH the node layout and the row titles (keeps them in sync; caps row height so tall viewports can't stretch the rows).
  - `layoutColumns()` portrait branch — uses `portraitBandGeom()`; adds a per-row **radius clamp** (`maxR = slot/2 - 3`) so bubbles in a crowded band (e.g. Markets = 10 slots) can never intersect.
  - `buildGraph()` — portrait-only **smaller hub radius**; a **fit-to-frame** initial transform (portrait only, frames the visible hubs centered); and a **`translateExtent`** on the d3 zoom (both orientations) that bounds panning to the map content (kills the "scroll into void").
  - Column-title drawing (portrait branch) — uses `portraitBandGeom()` so titles sit in each band's header strip, never under the bubbles.
  - `fitAppToViewport()` (new) — pins `#app` height to the real visible height (`window.visualViewport.height`, fallback `innerHeight`). Called at init (before first `buildGraph`), inside `recenterGraph()`, and on `resize`/`orientationchange`/`visualViewport` resize+scroll. This is the actual fix for the mobile webview "balloon."

**Files later work will modify (untouched so far):**
- `bullion-live-map/index.html` — the permanent front door; redirects to the current mk file. Do not rename it. Only `release.sh <N>` should repoint it (only relevant if cutting Mk16).
- `bullion-live-map/release.sh` — cuts a new version + repoints index. Not needed for these fixes.

**Not mine — leave alone (pre-existing untracked, unrelated to this work):**
- `.DS_Store`, `docs/.DS_Store`, `docs/superpowers/.DS_Store`, `.claude/`, `CLAUDE.md`, `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md`. These show as untracked in `git status` but are not part of this session's work. Do not commit them.

## What has changed

- `cd4614b` **Mk15: fix phone layout — clear column titles, frame on open, bound pan.** Portrait titles moved into per-band header strips; smaller hubs + per-row radius clamp (no circle overlap); auto-fit-to-frame on open; `translateExtent` pan bound. Verified in Chrome MCP at ~390px width.
- `efc7cfc` **Mk15: stop phone layout stretching in tall/in-app-browser viewports.** Root cause: mobile webviews (Instagram/FB in-app browsers; some Safari/Chrome states) ignore `height:100dvh`/`position:fixed`, so `#stage` ballooned far past the screen — the portrait row spacing scales with stage height `H`, so rows stretched off-screen and the page scrolled into void. Fix: `fitAppToViewport()` clamps the stage to the visible viewport; `portraitBandGeom()` caps + centers the row stack as a backstop. **Both commits pushed; live site confirmed serving the new code** (grep for `fitAppToViewport`/`portraitBandGeom` on the live URL matched).

## What has failed / risks / caveats

- **Nothing has failed** in testing. But note the following.
- **UNVERIFIED ON A REAL DEVICE.** All verification was desktop-Chrome emulation: narrow `#app` width, plus a *forced tall* `#app` height to reproduce the webview balloon, plus forcing `#app` to 1600px to prove `fitAppToViewport()` overrides it. The real Instagram-in-app-browser behavior is **inferred**, not user-confirmed. The load-bearing assumption is that `window.visualViewport.height` returns the true visible height in that webview. If a specific webview misreports it, the balloon fix may not fully hold and a different container-sizing approach would be needed. **Wait for the user's real-phone result.**
- **Pre-existing, NOT fixed (not a regression):** on **desktop** (landscape) the Markets column stacks `Equity Markets` + `Credit Markets` so their circles overlap vertically. The radius clamp is **portrait-only** by design; desktop hub sizes/layout were intentionally left unchanged. Only touch this if the user asks.
- **Caching trap:** mobile browsers — especially in-app browsers — cache aggressively. The user repeatedly saw the old version until hard-refresh. When they re-test, they must fully close the tab / open outside the in-app browser. A "still broken" report may just be a stale cache — confirm they did a clean load before debugging.
- **Wrong-version trap:** the user's phone earlier showed **Mk11** (an old bookmark). Ensure any test opens `bullion_mk15.html` (or the front-door folder URL), not a stale Mk11 link.
- **Design decision carried forward:** the user chose "fit & center the current column/band layout" over "revert to the old Mk11 organic force-directed layout." Do not reintroduce force layout without asking.

## What's next (ordered)

1. **Get the user's real-phone re-test of `efc7cfc`.** If good: done — offer to note it and stop. If bad: obtain a fresh screenshot + which browser/app, then reproduce (tall narrow viewport) before editing.
2. If the webview balloon persists despite `fitAppToViewport()`: investigate sizing the map from `visualViewport` more directly, or setting explicit px height on `html`/`body` too, not just `#app`.
3. (Independent, optional) Pre-existing **Mk16 backlog** from `docs/superpowers/mk15-handoff.md` — headline item is a user decision on the `vix→options` link direction. To cut Mk16: `./bullion-live-map/release.sh 16`. Unrelated to these phone fixes.

## Verification idioms used in this project (for the resuming session)

- **Serve locally:** `cd bullion-live-map && python3 -m http.server 8731` → `http://localhost:8731/bullion_mk15.html` (file:// is blocked by the Chrome extension; must use http).
- **Reproduce the PHONE bug:** a narrow window alone is NOT enough — you must force a *tall* stage. In the page console: set `#app` to e.g. `width:390px; height:1500px` and dispatch a `resize` event, then observe the rows stretch. With the fix in place, `fitAppToViewport()` (fired on resize) clamps height back to the visible viewport and the map renders compact/framed. Landscape (desktop, width ≥ 560px) uses the column layout and is unaffected.
- **Confirm live deploy after a push:** `curl -s "https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mk15.html?cb=$RANDOM" | grep -c "fitAppToViewport"` — poll until > 0 (GitHub Pages rebuild takes ~30–60s).
- **Deploy flow:** this project commits **directly to `main`** (no PR) with `Mk15:`-prefixed messages; GitHub Pages serves `main`. Push only when the user asks.

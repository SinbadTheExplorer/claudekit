# Mk18/MkUltra UI Fixes + Voice Narration Phase 1 — Session Handoff

**Written:** 2026-07-30 · **For:** any future session resuming two in-flight brainstorms on
`bullion_mk18.html` / `bullion_mkultra.html`: (1) two UI bug reports the user gave in an
earlier, context-exhausted session, and (2) expanding the voice-narration pilot (shipped
this session, see prior handoff) to full node coverage. **Neither effort has a written spec
yet** — everything below is a design that was verbally presented and partially confirmed in
conversation, never committed to a file. This handoff IS the only record of it.

## Goal

Two separate, still-undesigned-on-paper efforts:
1. Fix two UI complaints on the live map: the "Set your own numbers" show/hide toggle, and
   the fact that no scenario control shows which scenario is currently active.
2. Expand voice narration from the 6-node/2-link pilot to full 39-node coverage (Phase 1),
   with link/relationship-row narration explicitly deferred to a separate Phase 2 effort.

- Spec: **none written yet** for either effort — this is the gap to close first.
- Plan: none — `writing-plans` hasn't been invoked for either.
- Progress ledger: none — neither effort has reached SDD.
- Prior handoff (voice-narration pilot, DONE + shipped): `mkultra-voice-narration-spec-handoff.md`
  — still present alongside this file, read it if you need the pilot's own design detail
  (architecture, error handling, testing approach for the 8-clip pilot that's now live).
- The pilot's own spec: `docs/superpowers/specs/2026-07-30-bullion-voice-narration-design.md`
  (committed, shipped, unrelated to what's below except as the pattern Phase 1 extends).

## How to resume (do this first)

1. Confirm nothing has drifted: `git -C ~/claude-projects/claudekit log --oneline -1`
   should show `e3fff8e` at HEAD on `main`. `git rev-list --left-right --count origin/main...main`
   should read `0  0` — everything through the voice-narration pilot is pushed and live.
2. Re-read this whole file — it is the only record of both designs below. There is no spec
   file to fall back on.
3. **Immediate next action:** re-ask the user the two open questions listed under "What's
   next" (item 1 and 2) — neither design is approved yet. Do NOT write a spec or touch code
   until both are resolved (brainstorming's hard gate: no implementation before explicit
   design approval).

## Current state (active files)

**Branch:** `main`, 0 ahead / 0 behind `origin/main`. Nothing from this session's UI-fix or
voice-Phase-1 discussion has touched any file — it is 100% conversational state.

**Files created/changed by this session so far:** none, for either effort. (The voice
narration *pilot* — 6 nodes/2 links — was built and shipped earlier in this same session;
see the prior handoff for that.)

**Files these efforts will eventually touch (untouched so far):**
- `bullion-live-map/bullion_mk18.html` — both efforts touch this.
- `bullion-live-map/bullion_mkultra.html` — both efforts touch this (same duplicated-file
  pattern as the pilot: separate standalone apps, no shared module).
- `bullion-live-map/scripts/generate_narration.py` — Phase 1 only; gains an HTML-extraction
  step (see below), replacing its current hardcoded `NARRATIONS` dict.
- `bullion-live-map/audio/narration/*.mp3` — Phase 1 adds ~33 new node clips; open question
  on whether the 6 existing pilot clips also get regenerated (see "What's next" item 2).

**Scratch workspace / traps:**
- ⚠️ A local dev server may still be running from this session: `python3 -m http.server 8791`
  in `bullion-live-map/`, log at `/tmp/bullion-http-server.log`. Check with
  `lsof -i :8791` before starting another; `file://` URLs do NOT work with the
  claude-in-chrome browser tool ("Can't interact with browser-internal or unparseable
  URLs") — always serve locally and navigate to `http://localhost:<port>/bullion_mk18.html`.
- ⚠️ Freeze-check baseline for `mk11.html`–`mk17.html` was written to
  `/tmp/bullion-freeze-baseline.txt` this session (Task 4 Step 0 of the pilot plan) — may not
  survive a reboot. Regenerate with `shasum -a 256 bullion_mk{11..17}.html` and compare
  against `git show <known-good-sha>:bullion-live-map/bullion_mk<N>.html | shasum -a 256` if
  the temp file is gone.
- ⚠️ **Nothing below is committed anywhere else.** Don't trust a future `git log` to
  corroborate any of this — it won't, because none of it has been written to disk yet.

**Not mine — leave alone:** same pre-existing untracked noise as always —
`docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`, `.codex/`,
`AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple), `bullion-live-map/__pycache__/`,
`bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`,
`docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md`. **Never `git add .`/`-A`.**

## What has changed

Nothing on disk. What happened this session, in conversation only:

**Investigation of the two UI bug reports:**
- The user reported (from the earlier, context-exhausted session) that the manual-drivers
  show/hide toggle "responds but nothing happened, no feedback," and that scenarios don't
  show which one is currently selected.
- **Root-caused the toggle complaint:** before commit `d225580` (already shipped this
  session as part of the voice-narration pilot push), `#manual-box.hidden { display: none }`
  didn't exist, so the box was ALWAYS visible regardless of the `hidden` class — clicking
  "show" flipped a class with zero visual effect. That's exactly "responds, no feedback."
  Verified live via real mouse clicks (not just JS) in both `mk18.html` and `mkultra.html`
  post-fix: toggle now correctly shows/hides the five driver sliders. **This item likely
  needs no further work** — asked the user to reload the live page and confirm; no
  confirmation received yet as of this handoff.
- **Confirmed the highlighting complaint is real:** read `triggerShock()` and the click
  wiring directly (`bullion_mk18.html` ~lines 3527–3549 for `triggerShock`/`resetState`,
  ~3902–3918 for the 5 preset-button + dropdown/Run-button click handlers, ~4074–4099 for
  `runManual()`). None of these touch button/select styling. `.btn.active` CSS already
  exists (line 96) and is used elsewhere (e.g. `#mode-toggle-btn`) but was never wired to
  scenario selection.

**Design proposed for scenario highlighting (NOT approved yet):**
- One new function, `setActiveScenario(type)`: clears `.active` from all 5 `[data-shock]`
  buttons and from `#scenario-select`, then marks whichever one matches `type` (or nothing,
  if `type` is `null`).
- Three call sites, no new event listeners: inside `triggerShock(type)` (covers both preset
  buttons and dropdown+Run, since both already funnel through it), inside `resetState()`
  (passes `null` — **user confirmed** Reset should clear highlight), inside `runManual()`
  when `manualIsDirty()` (passes `null` — **user confirmed** manual mode should clear any
  preset/dropdown highlight).
- Needs a new CSS rule giving `#scenario-select` an `.active` look, since `<select>` styling
  differs from `<button>` — proposed mirroring `.btn.active`'s existing gold-highlight look.
- Same change in both `mk18.html` and `mkultra.html`.
- **This design was presented in full but the user pivoted to voice narration before
  answering the one open styling question** (see "What's next" item 1) — treat as
  unapproved.

**Design proposed for voice-narration Phase 1 (full 39-node coverage, NOT approved yet):**
- User confirmed via explicit choice: full ~39-node coverage (not narrower), UI fixes take
  priority in sequencing (though in practice both got brainstormed the same session — no
  code written for either).
- Confirmed live via JS (`NODES.length` etc. in the browser): `mk18.html` has 39 nodes, 93
  `LINKS`, 16 `PLUMBING_LINKS` (109 links total). `mkultra.html`'s `NODES` array is
  **byte-identical** to `mk18.html`'s (diffed the raw array text) — node text hasn't
  drifted since the honesty pass, so Phase 1 audio only needs generating ONCE; both files'
  manifests can point at the same physical files (they already share
  `bullion-live-map/audio/narration/`).
- Node shape confirmed: `{id, label, group, beginner: [sentence, sentence, ...], expert:
  [...]}`. The pilot's hardcoded text for e.g. `fed` is exactly `beginner.join(' ')` —
  extraction will reproduce identical wording for the 6 already-piloted nodes.
- **User confirmed (via explicit choice):** extract text from the HTML at generation time
  rather than keep hardcoding it — `generate_narration.py` should launch headless Chrome
  (isolated `--user-data-dir`, this project's standard idiom) against `bullion_mk18.html`,
  evaluate `JSON.stringify(NODES.map(n => ({id: n.id, text: n.beginner.join(' ')})))`, and
  use that as the source of truth for all 39 texts, replacing the pilot's hardcoded
  `NARRATIONS` dict. Extracting from `mk18.html` alone is sufficient.
- **User confirmed (via explicit choice):** link/relationship-row narration is wanted, but
  explicitly split into a separate Phase 2 with its own design pass — NOT part of Phase 1.
  Reason surfaced during brainstorming: the pilot's 🔊 button only ever appears on 2 rare,
  visually-distinct italic field-note blocks; a typical node's relationship list runs
  6–11 rows (Credit Markets showed 11 in a screenshot this session), so a 🔊 on every row is
  a real crowding/layout question the pilot never tested. Phase 2 starts from scratch
  design-wise — nothing about it is decided (no call sites, no manifest-key scheme, no
  button placement).
- Manifest/wiring: `NARRATION_MANIFEST` expands from 6 to 39 entries in both files; **no new
  front-end code** — `openDetail()`'s existing `NARRATION_MANIFEST[d.id]` lookup already
  generalizes to any id present.
- New completeness check proposed (not yet built): assert every `NODES` id has a manifest
  entry, since this is meant to be complete coverage now, not a deliberately partial pilot.
- Testing proposed: same headless-probe idiom as the pilot, but sweeping all 39 (no more
  allowlist of 6). For the manual listen-through, proposed spot-checking ~6–8 clips across
  different node groups rather than exhaustively listening to all 39, backed by the
  programmatic duration/non-empty/decodability check (same as pilot Task 3 Step 3) for full
  coverage.

## What has failed / risks / caveats

- **Nothing has failed** — no code has been written for either effort this session.
- **UNVERIFIED / unconfirmed:**
  - Whether the manual-box toggle fix actually resolves the user's experience — verified by
    me via automation, not yet confirmed by the user on the live site.
  - The scenario-highlighting design's one open styling question (below).
  - Whether to regenerate the 6 existing pilot node clips as part of Phase 1, or leave them
    untouched (below) — flagged that Chatterbox likely isn't fully deterministic, so
    regenerating could produce audibly different output for those 6 even with identical
    text/voice/model, which the user may or may not want.
  - Whether `mkultra.html`'s `LINKS`/`PLUMBING_LINKS` text is identical to `mk18.html`'s the
    same way `NODES` is — never checked (only matters once Phase 2 starts).
  - Whether Chatterbox's actual generation time scales sanely to 39 clips — the pilot's
    8-clip runtime is the only data point so far.
- **Nothing overrides a prior plan** — no plan exists yet for either effort.

## What's next (ordered)

1. **Resolve the scenario-highlighting open question:** ask the user — "Does the design
   match what you had in mind, or should the 'active' treatment differ from `.btn.active`'s
   look (e.g. different color/border for the dropdown vs the buttons)?" This was asked once
   already but never answered (user redirected to voice narration instead).
2. **Resolve the Phase-1 open question:** regenerate all 39 node clips (including the 6
   piloted ones, for one consistent extraction+denoise pipeline) vs. leave the 6 existing
   ones untouched and only generate the 33 new ones. Recommend regenerate-all for
   consistency, but the user hasn't confirmed.
3. Once both are resolved, write each as its own spec under `docs/superpowers/specs/` (UI
   fixes and voice Phase 1 are unrelated enough to warrant separate spec files), commit,
   self-review per the brainstorming skill's spec-review checklist, then invoke
   `writing-plans` for each. Likely executed via `subagent-driven-development` per this
   project's established pattern for multi-task efforts.
4. Confirm with the user whether the manual-box toggle fix is actually resolved for them on
   the live site (low-cost, can happen any time — doesn't block 1–3).
5. Phase 2 (link/relationship-row narration) brainstorming starts only after Phase 1 ships —
   nothing about it is designed yet; begin from scratch with the brainstorming skill.

## Verification idioms used in this project (for the resuming session)

- Headless Chrome probes: always an isolated `--user-data-dir=/tmp/<unique>`; inject probe
  script before the LAST `</body>` via `str.rfind` (there's a decoy `</body>` inside a JS
  string mid-file); NEVER call `openAuditLog()` in a probe (its animated modal stalls
  headless virtual-time → hang).
- `file://` URLs don't work with the claude-in-chrome browser tool — serve locally instead:
  `cd bullion-live-map && python3 -m http.server <port>`, navigate to
  `http://localhost:<port>/bullion_mk18.html`.
- claude-in-chrome automated tabs report `document.visibilityState: "hidden"` — Chrome
  throttles the actual audio byte-fetch even though `Audio.play()` resolves without error. A
  resolved `.play()` promise + zero `securitypolicyviolation` events proves CSP isn't
  blocking playback, but does NOT prove audible sound — that always needs the user in a
  real, focused tab.
- Pixel-coordinate clicks near `mkultra.html`'s 3D WebGL globe are unreliable for automation
  (something — likely OrbitControls — hooks global mouse listeners that can deselect/close a
  panel even on a coordinate click that visually lands on a legitimate DOM button). Fix: one
  real coordinate click anywhere safe to establish user-activation, then
  `document.querySelector(...).click()` via the JS tool for the actual target element —
  hits the same production `onclick` path without fighting the canvas.
- Freeze-check: `shasum -a 256 bullion_mk11.html … bullion_mk17.html`, must stay
  byte-identical to their pre-effort state.
- Python suite: `cd bullion-live-map && python3 -m unittest discover -s tests &&
  python3 -m unittest test_calibrate` → 41/41 + 33/33 as of this session.
- `git push origin main` works directly via Bash (`GIT_TERMINAL_PROMPT=0 git push origin
  main`); no `gh` CLI installed.

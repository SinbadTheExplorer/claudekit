# Bullion Narration — User Review Fixes (4 of 8 done) — Session Handoff

**Written:** 2026-08-02 · **For:** any future session resuming this work — continues
directly from `bullion-johnny-full-39-nodes-handoff.md` (that handoff shipped Johnny on
all 39 nodes + `JOHNNY_TEMPO=0.9`, fully committed/pushed at `5224605`, "nothing
blocking"). This session worked through an 8-item visual/sound review list the user
wrote after actually using the map. **4 of 8 are done and committed; 4 are not started.**

## Goal

The user tested the live map (both `bullion_mk18.html` 2D and `bullion_mkultra.html` 3D)
and reported 8 concrete bugs/feedback items, split "Visual" and "Sound". This session
fixed the 4 that were pure code changes (no audio regeneration needed) and investigated
but did not implement the remaining 4, which all require either new content or a full
narration-audio regeneration pass. No spec/plan doc was written — handled as direct
review-feedback fixing, same "small work stays inline" posture as every prior ad-hoc
tuning session in this project.

- Prior handoff (Johnny expanded to 39 nodes, tempo retune mechanism):
  `docs/superpowers/bullion-johnny-full-39-nodes-handoff.md`
- Older handoff (Johnny's TTS-direct mechanism, why VC-blend was dropped for him):
  `docs/superpowers/bullion-johnny-tts-actor-handoff.md` — this session moved it to
  `docs/superpowers/archive/` (see "Current state" below); its content is still valid
  background, just no longer in the top-2-most-recent slot.
- No spec/plan/SDD ledger for this session's work.

## How to resume (do this first)

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline
   5224605..HEAD` should show exactly **1 commit, `a4b2838`**, on `main`. `git status
   --short` should be clean except the standing "Not mine" untracked noise (list below).
2. **This commit is NOT pushed** — `git log --oneline origin/main..HEAD` shows `a4b2838`;
   `HEAD..origin/main` is empty. Confirm with the user before pushing (they only asked
   for a commit this session, not a push).
3. Read this handoff in full, then the original 8-item list is reproduced verbatim under
   "The original review list" below so you don't have to go hunting for it.
4. **Immediate next action:** pick up item #4 (2D board dimming) — it's the only
   remaining item that's pure code, no audio pipeline involved. See "What's next".

## The original review list (verbatim, numbered for reference)

**Visual:**
1. The first sentence on any node ("This raises … when it …") might be redundant since
   the symbols already work for it — might need to remove it.
2. The caption is shown inside the node panel but disappears if the user clicks out of
   the node. Move the caption to the middle-bottom, matching where the tutorial guide is
   shown. Highlight it yellow with a cyberpunk font/color when Johnny is speaking, blue
   when Alfred speaks.
3. The Johnny/Alfred bubble's opacity should match the nodes', residing right in the
   center of the star system, like the Solar system. Not connected to any node. Should
   be 3D.
4. The 2D board should function the same as the map — dimming whatever isn't relevant to
   the clicked node.

**Sound:**
5. Johnny isn't speaking loud enough compared to Alfred — raise it so they match.
6. Voice lines overlay each other when switching nodes before the previous one finishes
   — stop the previous node's voice completely before the new one plays.
7. Alfred is speaking too fast — deduct 5 from his speed. Johnny is speaking too slow —
   raise his by 1.
8. Add more voice lines — e.g. when the user picks a preset scenario, or clicks AI
   analysis.

## Current state (active files)

**Branch:** `main`, 1 commit ahead of base `5224605` (`a4b2838`), **not pushed**, clean
tree (modulo standing untracked noise).

**Committed in `a4b2838`** (both `bullion_mk18.html` and `bullion_mkultra.html` edited in
parallel — the app-level JS/CSS between the two files is kept byte-identical by
convention, see the prior handoffs):

- **Item 1 (redundant sentence):** removed the `const effect = ...` / `const lead = ...`
  block and its `<span class="rel-lead">` render line from `buildRelationships()` in both
  files. The colored `word` badge (Amplifies/Dampens/Conditional) and the arrow glyphs
  stay — only the plain-English restatement sentence is gone.
- **Item 2 (persistent caption):** `#detail-caption` (which lived inside `#detail-panel`
  and vanished on close) is gone; replaced by `#narration-caption`, a new fixed
  bottom-center bar that is a body-level sibling (`#legend-box`'s sibling), independent
  of the detail panel's open/closed state. `closeDetail()` no longer calls
  `clearCaption()` — the caption now only clears when a **new** line starts
  (`playNarration()`'s own `clearCaption()` call) or the **current** one finishes
  naturally (the `'ended'` handler now calls `clearCaption()` instead of just
  `setOrbNarrating(false)`). Styling: `.persona-alfred` = blue (`var(--blue)` label,
  `#cfe0f5` text); `.persona-johnny` = yellow-gold (`#ffe45c`) with a monospace font
  stack and a neon `text-shadow` glow, no external font loaded (stays a fully
  self-contained static HTML file — see note below). Mobile media query in both files
  repositions the bar above the bottom detail-sheet via
  `#app.panel-open #narration-caption { bottom: calc(62vh + 12px); }`.
- **Item 3 (3D orb, `bullion_mkultra.html` ONLY — mk18 is 2D/SVG and has no "star
  system" concept, so its orb was deliberately left untouched):** `#persona-orb` moved
  from a `position:fixed` body-level sibling into a child of `#stage`, CSS-centered via
  `left:50%;top:50%;transform:translate(-50%,-50%)`. This lines up with the WebGL scene's
  world origin because `controls.enablePan = false` (confirmed in the Renderer's
  `build()`) — the camera always orbits around `(0,0,0)`, so that point projects to dead
  center of the canvas at every zoom/rotation. A **real Three.js mesh** (`sunMesh`, a
  small `SphereGeometry` + `MeshStandardMaterial`) plus a corona `Sprite` (`sunGlow`,
  reusing the existing `makeGlowTexture()` hub-glow pattern) were added at the origin
  inside `Renderer`'s `build()`. Both are deliberately **excluded from `meshList`** so
  they're never raycast-picked, never touched by `focus()`/`clearFocusImpl()`'s dimming
  loops, and never counted as a node by anything that iterates `meshList` — i.e.
  structurally guaranteed "not connected to any node." A new `updateSunPulse(time)`
  (mirrors the DOM orb's own `orbBreathe` CSS keyframe timing/values) runs every frame
  from `renderLoop()`. `Renderer.setOrbState(persona, active)` is the new public write
  surface (added to the returned API object); the app layer calls it from both
  `setOrbNarrating()` and `applyPersonaToggle()` so the WebGL sphere's color/opacity
  never drifts from what the DOM label/icon show. **Trap avoided, not present:** the
  Overview/board tab sets `#stage` to `display:none`, which would have taken the orb down
  with it since it's now `#stage`'s child — `showView()` was updated to **reparent** the
  orb to `<body>` and toggle a new `.orb-docked` class (restores the original
  fixed-bottom-right corner treatment, including the panel-dodge transform rule, which
  was re-added scoped to `.orb-docked` specifically) whenever the board tab is active.
  Confirmed this reparent logic is written correctly by re-reading it; **not yet
  confirmed by actually clicking the Overview tab in a browser** — see caveats.
- **Item 6 (audio overlap):** both files' `playNarration()` now track a module-level
  `currentNarrationAudio`. Before creating a new `Audio()`, it `.pause()`s the previous
  one, resets `.currentTime = 0`, and clears `.src`. The `'ended'` handler only clears
  `currentNarrationAudio` (and the caption) if it's still the same audio object that
  fired the event, so a stale `'ended'` from an already-superseded clip can't wipe state
  for the new one.

**Files later work will touch (untouched this session):**

- `bullion-live-map/scripts/generate_narration.py` — `ALFRED_RATE = 218` and
  `JOHNNY_TEMPO = 0.9` are both still at the prior session's values. Item 7 needs these
  edited; item 5's `loudnorm` fix (see below) also lands here.
- `bullion-live-map/bullion_mk18.html`'s `buildBoard()` / `.board-card` — item 4's
  target, completely unedited this session.
- All `bullion-live-map/audio/narration/*.mp3` — none regenerated this session (items 5
  and 7 both need a regen pass; see "What's next").
- Whatever handles the scenario-preset buttons and the AI-analysis drawer in both HTML
  files — item 8's target, not yet located. Search for `data-shock` (scenario buttons,
  seen once already at `<button class="btn" data-shock="rate_hike" ...>` in the control
  drawer) and whatever fires the AI-analysis request as starting points.

**Scratch workspace / traps:**

- ⚠️ **Nothing in this session was verified in a live browser.** All 4 completed items
  are code-reviewed-by-re-reading only. Before trusting any of them, actually load both
  HTML files (e.g. `python3 -m http.server` from `bullion-live-map/`) and check: caption
  survives clicking off a node and is styled correctly per persona; the 3D orb visually
  sits at the sphere's center and switches correctly between docked/centered when
  toggling the Overview tab; rapid node-switching no longer overlaps two voice clips.
- ⚠️ `bullion-live-map/audio/narration/.johnny_tempo90_done.txt` — untracked, inert
  leftover marker file from the *prior* session's resumable Johnny-generation driver.
  Not touched this session. Safe to delete or ignore; do not treat its contents as
  authoritative for anything.
- ⚠️ This session archived `docs/superpowers/bullion-johnny-tts-actor-handoff.md` to
  `docs/superpowers/archive/` (it was untracked and had fallen out of the top-2-most-recent
  slot per this project's handoff convention — see the `handoff-doc-conventions` memory).
  Its content (why Johnny moved off VC-blend to direct ChatterboxTTS) is still accurate
  background if you need it; it's just no longer top-level.
- **Not mine — leave alone** (same as every prior handoff in this project):
  `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`,
  `.codex/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple),
  `bullion-live-map/__pycache__/`, `bullion-live-map/scripts/__pycache__/`,
  `bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`, `.superpowers/`,
  and the other tracked handoffs still sitting in `docs/superpowers/` (`honesty-pass-`,
  `mk12-`, `mkultra-spec2-brainstorm-`, `mkultra-spec2-plan-handoff.md` — all tracked,
  intentionally left in place per the archiving rule). **Never `git add .`/`-A`** — this
  session staged only the two HTML files explicitly by name.

## What has changed

- Items 1, 2, 3, 6 from the review list implemented in both `bullion_mk18.html` and
  `bullion_mkultra.html` (item 3 is mkultra-only, see above). **Committed** in `a4b2838`
  on the user's explicit "commit everything that has been finished" instruction. **Not
  pushed** — push was never requested.
- No test suite exists for these two HTML files' JS/CSS (the project's `unittest` suite
  covers `generate_narration.py` and `calibrate.py` only) — there is nothing to run here
  beyond manual/browser verification.

## What has failed / risks / caveats

- **Nothing has failed** — no fix was attempted and abandoned.
- **UNVERIFIED (real risk, not just formality):** none of the 4 completed items have
  been exercised in an actual browser this session. The 3D orb reparenting logic (item 3)
  in particular is new, non-trivial DOM-manipulation-plus-CSS-class-toggling that has
  never been visually confirmed — a live check of the Overview-tab dock/undock is the
  single highest-value next step before trusting item 3.
- Items 4, 5, 7, 8 are **not started** — investigated only (see "What's next" for exactly
  what was found for each). Do not assume any code changes exist for them.
- **Item 7's exact target values are an interpretation, not a spec.** "Deduct 5" from
  Alfred's rate maps cleanly onto `ALFRED_RATE` (218 → 213, a macOS `say` words-per-minute
  value). "Raise Johnny by 1" does **not** map cleanly onto `JOHNNY_TEMPO` (a 0.9 ffmpeg
  `atempo` multiplier) — this session's working interpretation was "raise by one 0.1
  tuning notch" (0.9 → 1.0), matching the increment size the project has used for this
  constant historically. Confirm with the user before generating 39×2 clips off an
  interpretation, or at minimum flag it when reporting the regen as done.
- **Items 5 and 7 both require the SAME expensive regeneration pass** (all 39 nodes ×
  2 personas through the real TTS/VC pipeline). Do not regenerate twice — fold the
  `loudnorm` filter change (item 5) and the rate/tempo constant changes (item 7) into one
  script edit, then run generation once. Re-read
  `docs/superpowers/bullion-johnny-full-39-nodes-handoff.md`'s "Scratch workspace /
  traps" section first — that session's runs were killed mid-batch at least twice and
  the resumable per-node marker-file driver pattern (not the full `main()` batch) is
  what made that safe; the same caution applies here for double the volume (Alfred's
  `say`+ChatterboxVC path is also expensive per-clip, not just Johnny's).

## What's next (ordered)

1. **Verify items 1/2/3/6 in a real browser first**, before adding more surface area on
   top of unverified work — `python3 -m http.server` from `bullion-live-map/`, open both
   `bullion_mk18.html` and `bullion_mkultra.html`, click through captions, persona
   toggle, node-switching mid-narration, and (mkultra only) the Overview tab dock/undock.
2. **Item 4 — 2D board dimming (`bullion_mk18.html` only, no audio, do this next):** the
   SVG map's existing pattern is `focusNode(id)`/`clearFocus()` (~line 1917-1930 as of
   this session, will drift), which toggle a `'dimmed'` class via
   `window._mk5Node.classed('dimmed', d => !keep.has(d.id))` /
   `window._mk5Link.classed('dimmed', ...)`, backed by CSS `.node-g.dimmed { opacity:
   0.12; }`. `buildBoard()`'s cards (`.board-card`, built in `buildBoard()`, click handler
   just calls `openDetail(n)`) have no equivalent. Plan: give `.board-card` a `.dimmed`
   CSS rule (mirror `.node-g.dimmed`'s opacity), call `focusNode(d.id)` from the board
   card's click handler (it already operates on the persisted `window._mk5Node`/
   `window._mk5Link` D3 selections regardless of which tab is showing, since the SVG
   persists through `display:none`), and add a small analogous
   `document.querySelectorAll('.board-card').forEach(c => c.classList.toggle('dimmed',
   ...))` step — either inside `focusNode()`/`clearFocus()` themselves (simplest, keeps
   one source of truth) or via a small wrapper. Also need a background-click-to-clear
   handler for `#board-view` itself, mirroring the SVG's `svg.on('click', ...)` deselect
   behavior.
3. **Item 5 + item 7 together — one regeneration pass:**
   a. Edit `generate_narration.py`: `ALFRED_RATE = 218` → `213`; `JOHNNY_TEMPO = 0.9` →
      `1.0` (confirm the "+1" interpretation with the user first if possible).
   b. Add `loudnorm=I=-20:TP=-2:LRA=7` to `synthesize()`'s final ffmpeg encode step
      (currently `-codec:a libmp3lame -qscale:a 2`, needs `-filter:a
      loudnorm=I=-20:TP=-2:LRA=7` added) and to `synthesize_johnny()`'s existing
      `-filter:a atempo={JOHNNY_TEMPO}` (chain it: `atempo={JOHNNY_TEMPO},loudnorm=I=-20:
      TP=-2:LRA=7`). These target values came from measuring 3 sample node pairs this
      session (`node-fed/johnny-fed`, `node-gold/johnny-gold`, `node-vix/johnny-vix`) via
      `ffmpeg -i <file> -af loudnorm=print_format=json -f null /dev/null` — Alfred
      averaged **-20.17 LUFS** integrated, Johnny averaged **-32.07 LUFS**, both around
      **-2 to -3 dBTP** true peak. A single fixed runtime gain multiplier was
      **deliberately rejected** — per-clip peak headroom varies enough (Johnny's
      `max_volume` ranged -10.2 to -13.8 dB across just 3 samples) that a gain large
      enough to close the full loudness gap on `fed` would clip on `gold`/`vix`.
      `loudnorm` handles this correctly by design (it's a true loudness normalizer with
      peak limiting, not a fixed multiply).
   c. Regenerate all 39×2 clips using the resumable per-node driver pattern from the
      prior handoff (not the full `main()` batch — expect the run to get killed and need
      resuming, per that handoff's documented experience).
   d. Spot-check by ear (`afplay`) — this project's stated convention is that audio
      correctness is **never** inferred from clean exit codes alone.
   e. Commit the regenerated `.mp3` files + the script + the (currently blank, needs no
      test changes since node coverage isn't changing) test suite, run the full existing
      test suite (see "Verification idioms" below) before committing.
4. **Item 8 — new voice lines:** not started. First locate the actual trigger points —
   grep both HTML files for `data-shock` (scenario preset buttons, one instance already
   spotted: `<button class="btn" data-shock="rate_hike" ...>` inside `#control-drawer`)
   and whatever function handles the AI-analysis button/drawer. Then: draft short
   Alfred + Johnny lines per scenario (and for the AI-analysis trigger), following the
   existing tone conventions (Alfred = factual butler register from on-page copy; Johnny
   = embittered chrome-punk rocker, `choom`-flavored, per `JOHNNY_SCRIPTS` in
   `generate_narration.py`), add manifest entries, generate the audio (can likely be
   folded into the same regeneration pass as item 3 above if timed right — check with the
   user), and wire `playNarration()` calls into the relevant button handlers.

## Verification idioms used in this project (for the resuming session)

- Test suite (unrelated to items 1/2/3/6, but needed before committing any item 5/7/8
  audio work): `cd bullion-live-map && python3 -m unittest discover -s tests &&
  python3 -m unittest test_calibrate && python3 -m unittest scripts.test_generate_narration
  -v` (plain `python3`, no heavy deps) **and separately** `.venv-narration/bin/python3 -m
  unittest scripts.test_voice_blend -v` (needs torch/librosa/chatterbox). 103/103 green as
  of the prior handoff (`5224605`); this session made no code changes that suite covers.
- Real generation: `.venv-narration/bin/python3 scripts/generate_narration.py` runs the
  full batch but **expect it to get killed on long runs** — drive Johnny (and now
  potentially Alfred too, since item 7 touches both) node-by-node with a small
  done-marker-file-checking driver script, never the full `main()` batch.
- **Audible correctness is never automatable in this project** — every voice/script/
  tempo/volume change ends in a real human listening pass (`afplay` or the live browser),
  never inferred from clean test runs or exit codes.
- Required macOS voice: `Jamie (Premium)` (`en_GB`), needed for Alfred only. Confirmed
  present in this environment (`which say` succeeded).
- `ffmpeg` and `.venv-narration` both confirmed present and working in this environment
  this session (`which ffmpeg` → `/opt/homebrew/bin/ffmpeg`; `.venv-narration/bin`
  exists with a populated venv).
- GitHub Pages deploy verification: no `gh` CLI on this machine — use `curl -s
  "https://api.github.com/repos/SinbadTheExplorer/claudekit/actions/runs?per_page=5"`
  (public API, works unauthenticated) and check the run for the relevant commit shows
  `completed`/`success`. Not needed this session since nothing was pushed.

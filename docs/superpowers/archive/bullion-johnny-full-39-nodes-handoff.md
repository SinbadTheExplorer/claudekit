# Bullion Narration — Johnny Expanded to All 39 Nodes + Tempo Retune — Session Handoff

**Written:** 2026-08-02 · **For:** any future session resuming this work — this continues
directly from `bullion-johnny-tts-actor-handoff.md` (that handoff shipped Johnny's
direct-ChatterboxTTS mechanism at `c900ad3`, fully committed, clean tree, "nothing
blocking"). This session's work is **now fully shipped and pushed** — read "Current
state" below, but there is no open blocker to resume.

## Goal

The prior handoff shipped Johnny (the rocker persona) on only 6 pilot nodes
(fed/gold/vix/sec/repo/yield), same as the original Alfred+Johnny pilot. This session
wrote hand-written Johnny scripts for the remaining 33 nodes so Johnny now covers **all
39 nodes**, same parity as Alfred, and separately retuned playback speed down via a new
`JOHNNY_TEMPO=0.9` ffmpeg time-stretch (confirmed by ear against the "banks" sample).
No spec/plan doc was written — handled fully inline, same "small work stays inline"
posture as every prior ad-hoc tuning session in this project.

- Prior handoff (Johnny's TTS-direct mechanism, why VC-blend was dropped):
  `docs/superpowers/bullion-johnny-tts-actor-handoff.md`
- Older handoff (VC-blend history, meanness-pitch saga — mechanism has since changed,
  Tasks 1-3 history still accurate): `docs/superpowers/archive/bullion-johnny-actor-voice-handoff.md`
- No spec/plan/SDD ledger for this session's work.

## How to resume (do this first)

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline
   c900ad3..HEAD` should show exactly **1 commit, `5224605`**, on `main`. `git status
   --short` should be clean except the standing "Not mine" untracked noise (list
   below) plus one new marker file, `audio/narration/.johnny_tempo90_done.txt`
   (untracked, harmless — see traps). `git log origin/main..HEAD` /
   `git log HEAD..origin/main` should both be empty — confirmed pushed, in sync.
2. Read this handoff in full. The prior handoff is only needed for older mechanism
   history (VC-blend math, why the meanness pitch-shift was rejected) — none of that
   applies to this session's changes.
3. **Immediate next action: none blocking.** This work is fully shipped, pushed, and
   the GitHub Pages deploy for `5224605` was confirmed `completed`/`success`. The only
   open item is a soft one — see "What's next."

## Current state (active files)

**Branch:** `main`, 1 commit ahead of base `c900ad3` (`5224605`), fully pushed, clean
tree (modulo standing untracked noise).

**Committed in `5224605`:**

- `bullion-live-map/scripts/generate_narration.py` —
  - Module docstring updated: Johnny is now "all 39 nodes" (was "6 pilot nodes").
  - New `JOHNNY_TEMPO = 0.9` constant (ffmpeg `atempo` factor — ChatterboxTTS has no
    native rate control).
  - `JOHNNY_SCRIPTS` dict grew from 6 entries to 39 — all 33 new entries are original
    hand-written "Johnny" (embittered rocker/chrome-punk voice, `choom`-flavored slang)
    flavor text, **deliberately not** the factual on-page copy (per the persona-toggle
    design spec's original rule, unchanged this session).
  - `synthesize_johnny()` now pipes its output through `ffmpeg -filter:a
    atempo={JOHNNY_TEMPO}` before the mp3 encode (pitch-preserved time-stretch, not a
    pitch-shift).
- `bullion-live-map/scripts/test_generate_narration.py` — updated to check all 39
  Johnny entries (`test_johnny_scripts_cover_every_node`,
  `test_mk18_johnny_manifest_matches_johnny_scripts_keys`,
  `test_mkultra_johnny_manifest_matches_johnny_scripts_keys`, etc.) instead of the old
  6-node pilot set.
- `bullion-live-map/scripts/test_voice_blend.py` — minor updates, unrelated to the
  6→39 expansion (carried over from the prior session's actor-TTS work).
- `bullion-live-map/bullion_mk18.html` + `bullion-live-map/bullion_mkultra.html` —
  `JOHNNY_MANIFEST` and `JOHNNY_SCRIPTS` both expanded from 6 to 39 entries, mirrored
  byte-for-byte from `generate_narration.py` (parity enforced by
  `test_generate_narration.py`'s manifest tests). **Public URLs, both now serving the
  full 39-node Johnny set:**
  - `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/` (redirects
    to the current 2D version, Mk18)
  - `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mkultra.html`
    (3D Mk Ultra fork — separate permanent URL, updated in the same commit)
- **All 39** `bullion-live-map/audio/narration/johnny-*.mp3` — regenerated fresh at
  `JOHNNY_TEMPO=0.9` and committed (the original 6 pilot clips are also regenerated at
  the new tempo, not just the 33 new ones).

**Files later work might touch (untouched this session):**

- Same reference clips as always: `bullion-live-map/audio/voice_sample/{user_voice.wav,
  jamie_sample.wav, actor_sample.wav}` — untouched.
- `link-credit-equit.mp3` / `link-usd-oil.mp3` — still on the old pre-blend `say`-only
  voice, a pre-existing gap noted in every prior handoff, not touched here either.

**Scratch workspace / traps:**

- ⚠️ `bullion-live-map/audio/narration/.johnny_tempo90_done.txt` — untracked,
  deliberately **not committed**. It's an append-only ledger (one node ID per line)
  written by the throwaway per-node generation driver used this session to survive
  repeated process kills on long ChatterboxTTS runs (same known infra limitation
  documented in the prior handoff). It's now stale/inert since all 39 clips are
  already shipped — safe to delete if it's in the way, or ignore it. If Johnny content
  is ever regenerated again, recreate a similar marker-file-driven script rather than
  hunting for this one (it may not survive to a future session's filesystem).
- ⚠️ **This session's generation was killed and resumed at least twice mid-run**
  (confirmed via chat history and the marker file's incremental writes) — the
  resumable-per-node pattern is what made that safe. If regenerating Johnny again,
  keep driving it one line at a time rather than the full `main()` batch.
- ⚠️ The 6 originally-shipped Johnny clips (fed/gold/repo/sec/vix/yield) were
  **regenerated this session too** — they now reflect `JOHNNY_TEMPO=0.9`, not
  whatever tempo (or lack of one) they shipped at in `c900ad3`. Don't assume the
  "pilot 6" are historically untouched.
- **Not mine — leave alone** (same as every prior handoff in this project):
  `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`,
  `.codex/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple),
  `bullion-live-map/__pycache__/`, `bullion-live-map/scripts/__pycache__/`,
  `bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`, `.superpowers/`
  (pre-existing SDD/brainstorm scratch state, confirmed unrelated), and several older
  untracked plan/spec docs from unrelated prior work. **Never `git add .`/`-A`.**

## What has changed

- Wrote 33 new hand-authored Johnny scripts (one per non-pilot node), matching the
  existing 6 pilots' voice/length/tone (~2-4 sentences, embittered chrome-punk
  register, `choom` as the recurring address term).
- Added `JOHNNY_TEMPO=0.9` and wired it into `synthesize_johnny()`'s ffmpeg encode
  step as a pitch-preserved slowdown.
- Regenerated **all 39** Johnny clips (not just the 33 new ones) so every clip reflects
  the same tempo.
- Mirrored `JOHNNY_MANIFEST`/`JOHNNY_SCRIPTS` into both `bullion_mk18.html` and
  `bullion_mkultra.html`, keeping the two files' Johnny content identical.
- Updated the test suite to check 39-node coverage instead of 6.
- **All tests green:** `python3 -m unittest discover -s tests` (33), `python3 -m
  unittest test_calibrate` (unrelated, unaffected), `python3 -m unittest
  scripts.test_generate_narration -v` (22) — **41+33+22 = 96** — plus
  `.venv-narration/bin/python3 -m unittest scripts.test_voice_blend -v` (7) —
  **103/103 total, all green**.
- **Committed** (`5224605`, 44 files: 39 `johnny-*.mp3` + `generate_narration.py` +
  both test files + both HTML files) on the user's explicit "commit" instruction.
  **Pushed** to `origin/main`. **GitHub Pages deploy confirmed** `completed`/`success`
  for `5224605` via the public Actions API (`gh` not installed on this machine).

## What has failed / risks / caveats

- **Nothing has failed.** All 103 tests pass, commit and push succeeded, deploy
  confirmed live.
- **Soft caveat, not a blocker:** the user's "commit" instruction came without a full
  by-ear listening pass across all 33 new scripts or the retuned 0.9x tempo on the
  full set — only the single "banks" sample (used earlier to pick 0.9) had been
  confirmed by ear before this session's commit. This was a deliberate, explicit
  user call (they said "commit" directly when asked whether they wanted to listen
  first), not an oversight — but if the user later flags any of the 33 new scripts'
  tone/content or the tempo as off, that's the first place to look, not a regression.
- Same pre-existing, unrelated gap noted in every prior handoff: `link-credit-equit.mp3`
  / `link-usd-oil.mp3` are still on the old pre-blend `say`-only voice.

## What's next (ordered)

1. **Nothing blocking.** If the user later wants to revisit any of the 33 new Johnny
   scripts' tone or the 0.9x tempo after actually listening, treat it as further
   tuning — regenerate only the affected node(s) via `synthesize_johnny()`, not the
   full 39-clip batch (same done-marker-resumable driver pattern used this session).
2. If Alfred ever needs a similar tempo retune, note `ALFRED_RATE=218` (macOS `say`
   rate) is a separate, already-tuned mechanism from Johnny's ffmpeg `atempo` — not
   touched or evaluated this session.

## Verification idioms used in this project (for the resuming session)

- Test suite: `cd bullion-live-map && python3 -m unittest discover -s tests && python3
  -m unittest test_calibrate && python3 -m unittest scripts.test_generate_narration -v`
  (plain `python3`, no heavy deps — `41 + 33 + 22`) **and separately**
  `.venv-narration/bin/python3 -m unittest scripts.test_voice_blend -v` (needs
  torch/librosa/chatterbox — `7` tests). All 103 confirmed green as of this handoff.
- Real generation: `.venv-narration/bin/python3 scripts/generate_narration.py` runs the
  full batch (Alfred + Johnny) but **expect it to get killed on long runs** — for
  Johnny specifically, drive it node-by-node with a small script that checks/appends
  to a done-marker file, never the full `main()` batch, so a kill only costs one clip.
- **Audible correctness is never automatable in this project** — every voice/script/
  tempo change ends in a real human listening pass (`afplay` or the live browser),
  never inferred from clean test runs or exit codes.
- Required macOS voice: `Jamie (Premium)` (`en_GB`), needed for Alfred only.
- Reference clips: `bullion-live-map/audio/voice_sample/{user_voice.wav,
  jamie_sample.wav, actor_sample.wav}` — all pre-existing, untouched this session.
- GitHub Pages deploy verification: no `gh` CLI on this machine — use `curl -s
  "https://api.github.com/repos/SinbadTheExplorer/claudekit/actions/runs?per_page=5"`
  (public API, works unauthenticated) and check the run for the relevant commit shows
  `completed`/`success`. Confirmed working this session for `5224605`.

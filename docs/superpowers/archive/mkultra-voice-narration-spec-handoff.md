# Bullion Voice Narration — Spec Session Handoff

**Written:** 2026-07-30 · **For:** any future session resuming the "add voice narration
to `bullion_mk18.html` and `bullion_mkultra.html`" effort — this session took the prior
brainstorm from "approach not yet confirmed" to "design fully presented, approved, and
committed as a spec." No code, audio directory, or generation script exist yet.

## Goal

Add narration, read in the user's own cloned voice, to a small pilot set of node
explanations and field notes in `bullion-live-map/bullion_mk18.html` and
`bullion-live-map/bullion_mkultra.html`, proving the pipeline end-to-end before ever
considering full ~39-node coverage.

- Spec: `docs/superpowers/specs/2026-07-30-bullion-voice-narration-design.md` (committed,
  full design — read this for every detail; this handoff only summarizes it)
- Plan: none yet — not written. This effort has not reached `writing-plans` yet.
- Progress ledger: none yet — this effort hasn't reached SDD.
- Prior handoff (superseded by this one): `mkultra-voice-narration-brainstorm-handoff.md`
  — still present alongside this file (see "Scratch workspace" below for what to do with
  it).
- Related prior effort (DONE, unrelated code, same target files): `mkultra-spec2-shipped-handoff.md`.

## How to resume (do this first)

1. Confirm nothing has drifted: `git -C ~/claude-projects/claudekit log --oneline -1` should show `201b89b` at HEAD on `main`. `git rev-list --left-right --count origin/main...main` should read `0  1` — the spec commit exists locally but has **not been pushed**.
2. Read the committed spec in full: `docs/superpowers/specs/2026-07-30-bullion-voice-narration-design.md`. It is the authority on every design decision — architecture, file naming, error handling, testing — trust it over this summary.
3. **Immediate next action:** the brainstorming skill's flow is at the "user reviews written spec" gate — ask the user to review the committed spec file and confirm they're happy with it (they approved the design conversationally already, but have not yet explicitly reviewed the committed file). Once they confirm, invoke `writing-plans` to produce the implementation plan. Do not invoke any other skill first.

## Current state (active files)

**Branch:** `main`, 1 commit ahead of `origin/main` (`201b89b`, unpushed), 0 behind.

**Files created/changed by this effort so far (all in commit `201b89b`):**
- `docs/superpowers/specs/2026-07-30-bullion-voice-narration-design.md` — the full,
  approved, self-reviewed design. This is new since the last handoff.

**Files this effort will eventually touch (untouched so far):**
- `bullion-live-map/bullion_mk18.html` — gets `NARRATION_MANIFEST`, a 🔊 button in
  `#detail-header` wired into `openDetail()` (currently at `bullion_mk18.html:1942`).
- `bullion-live-map/bullion_mkultra.html` — same node-side changes, plus a second
  manifest (`NARRATION_LINKS`) and inline 🔊 buttons wherever `.rel-field-note` renders
  (currently `bullion_mkultra.html:2546`).
- New, not yet created: `bullion-live-map/scripts/generate_narration.py` (one-time
  generation script, 8 narration texts hardcoded in it) and
  `bullion-live-map/audio/narration/*.mp3` (8 output files — see spec for exact names).

**Scratch workspace / traps:**
- ⚠️ **The prior handoff, `mkultra-voice-narration-brainstorm-handoff.md`, is now
  superseded but per this project's 2-most-recent-handoffs convention it should stay in
  place** (this handoff + that one = exactly 2 in the directory; nothing needs archiving
  yet). If a *third* voice-narration handoff is written later, archive that one then
  (check `git ls-files --error-unmatch` first — it's currently untracked, so it would
  move to `archive/`, not get deleted).
- ⚠️ **Don't confuse this with the DONE Spec 2 effort.** `mkultra-spec2-shipped-handoff.md`
  documents finished, unrelated work (typography/palette/wordmark/cursor/field-notes/
  WebGL-fallback) on the same files. This voice-narration effort is separate.
- ⚠️ **Freeze-check scope differs from the Spec 2 convention.** Freeze-check
  `bullion_mk11.html`–`mk17.html` only; `mk18` is this effort's intentional target, not a
  frozen archive.
- ⚠️ No audio files, generation scripts, voice sample, or Chatterbox install exist yet —
  all of that is still ahead in "What's next."
- ⚠️ The spec commit (`201b89b`) has **not been pushed** to `origin/main`. Nobody asked
  for a push this session — don't push without being asked.

**Not mine — leave alone:** same pre-existing untracked noise as always —
`docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`, `.codex/`,
`AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple), `bullion-live-map/__pycache__/`,
`bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`,
`docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md`. **Never `git add .`/`-A`.**

## What has changed

Since the last handoff, entirely in conversation plus one commit:

- **Approach 1 confirmed by the user** (previously only proposed): static MP3s per
  node/field-note, generated once by a local script, played via a small 🔊 button and a
  plain `Audio()` object. The two alternatives (single master track; Web-Speech-API
  hybrid) remain rejected.
- **Pilot node list chosen:** `fed`, `gold`, `vix`, `sec`, `repo`, `yield` — one node each
  from monetary/commodity/sentiment/regulator/shadow-banking/capital-markets, a
  deliberate spread across layers rather than a themed cluster. Plus the 2 pre-existing
  field notes (`credit→equit`, `usd→oil`) — the only two links carrying a `fieldNote`
  field today.
- **Full design presented section-by-section and approved:** content/naming convention
  (`node-<id>.mp3`, `link-<s>-<t>.mp3` under `bullion-live-map/audio/narration/`),
  generation-script approach (texts hardcoded in the script, not extracted from the live
  HTML), front-end wiring for nodes and for field notes, error handling (no manifest
  entry → no button, ever; playback failure is caught and silent, no fallback), and
  testing approach (real-Chrome manual audio check + headless DOM probe + freeze-check +
  existing Python suite).
- **Spec written, self-reviewed (no placeholders/contradictions found), and committed**
  as `201b89b`.

## What has failed / risks / caveats

- **Nothing has failed** — no code has been written yet.
- **UNVERIFIED (carried forward from the brainstorm, still unresolved):** whether
  Chatterbox (or GPT-SoVITS) actually installs and runs cleanly on this Mac. Untested.
- **UNVERIFIED (carried forward):** CSP impact of local audio playback.
  `bullion_mk18.html`'s CSP has no explicit `media-src`, so same-origin audio should fall
  through to `default-src 'self'` — an assumption, not yet confirmed against a real
  browser load.
- **UNVERIFIED (new this session):** the user has approved the design conversationally
  but has not yet explicitly reviewed the *committed spec file itself* — that review gate
  is still open (see "Immediate next action" above).
- **Nothing overrides a prior plan** — no plan exists yet for this effort.

## What's next (ordered)

1. Ask the user to review the committed spec file
   (`docs/superpowers/specs/2026-07-30-bullion-voice-narration-design.md`) and confirm no
   changes are needed.
2. Invoke `writing-plans` to produce the implementation plan. It needs to cover, at
   minimum: recording the voice sample, installing/running Chatterbox (or chosen
   alternative), generating the 8 pilot MP3s via `generate_narration.py`, and the
   front-end wiring in both target HTML files per the spec's exact manifests/markup.
3. During implementation, resolve the two carried-forward UNVERIFIED risks early
   (Chatterbox install; CSP/audio playback) since they gate everything downstream.
4. After implementation, run the full testing section from the spec (manual real-Chrome
   audio check, headless DOM probe with isolated `--user-data-dir`, freeze-check
   `mk11`–`mk17`, Python unittest suite) before considering this pilot done.

## Verification idioms used in this project (for the resuming session)

No narration-specific verification exists yet (no code to verify). Reuse this project's
established idioms once implementation starts — documented in full in
`mkultra-spec2-shipped-handoff.md`:
- Real headless-Chrome DOM probes, always with an isolated `--user-data-dir` (never run
  headless Chrome against these files without one).
- Freeze-check via `shasum -a 256` — for this effort, check `bullion_mk11.html`–
  `mk17.html` only (not `mk18.html`, which this effort intentionally edits).
- Python suite: `cd bullion-live-map && python3 -m unittest discover -s tests &&
  python3 -m unittest test_calibrate` — sanity check after any change, unrelated to this
  JS/audio work but cheap to re-run.
- `git push` works directly via Bash (`GIT_TERMINAL_PROMPT=0 git push origin main`); no
  `gh` installed.

# Bullion Voice Narration — Brainstorm Session Handoff

**Written:** 2026-07-29 · **For:** any future session resuming the "add voice narration to
`bullion_mkultra.html` and `bullion_mk18.html`" effort — this is a brainstorming-in-progress
handoff, not a completion record. No spec, plan, or code exists yet; this file exists so a
fresh session can pick the conversation back up without re-litigating decisions already made.

## Goal

Add narration, read in the user's own cloned voice, to the node explanations and field notes
in `bullion-live-map/bullion_mk18.html` and `bullion-live-map/bullion_mkultra.html`. The whole
brainstorming conversation happened in chat — there is no spec/plan file yet because the
design wasn't finished being presented before the user asked for this handoff instead.

- Spec: none yet — not written.
- Plan: none yet — not written.
- Progress ledger: none yet — this effort hasn't reached `writing-plans`/SDD.
- Related prior effort (DONE, unrelated code but same target file): `docs/superpowers/mkultra-spec2-shipped-handoff.md` — confirms the Mk Ultra "editorial identity pass" (Spec 2) is fully shipped and live; this voice-narration effort is a brand-new, separate effort on the same file, not a continuation of Spec 2.

## How to resume (do this first)

1. Confirm nothing has changed: `git -C ~/claude-projects/claudekit log --oneline -1` should still show `ec47e64` at HEAD on `main` (this brainstorm session made zero code changes — pure conversation). `git rev-list --left-right --count origin/main...main` should read `0  0`.
2. Re-invoke `superpowers:brainstorming` to continue — do NOT restart from scratch. Every decision in "What has changed" below is locked in and should not be re-asked.
3. Read the "What has changed" section below — it's the authority on what's already settled.
4. **Immediate next action:** ask the user to confirm **Approach 1** (see below) — it was proposed and recommended but the conversation paused before the user explicitly said yes/no. Once confirmed, finish the brainstorming skill's "Present design" step in full (architecture, data flow, error handling), write the spec doc to `docs/superpowers/specs/2026-07-29-bullion-voice-narration-design.md` (adjust date if resumed later), get user sign-off, then invoke `writing-plans`.

## Current state (active files)

**Branch:** `main`, 0 commits ahead/behind `origin/main` — fully synced, nothing new pushed.

**Files created/changed by this effort so far:** none. No code, no audio directory, no spec.
Only this handoff file is new (untracked, same pattern as the previous handoff in this repo).

**Files this effort will eventually touch (untouched so far):**
- `bullion-live-map/bullion_mk18.html` — ~39 nodes (counted via `grep -c "beginner:\[" `), has `#detail-panel` with per-node beginner/expert text and a separate AI-generated `#narrative-box`.
- `bullion-live-map/bullion_mkultra.html` — same ~39-node structure (it's a 3D fork seeded from `bullion_mk15.html`), plus 2 first-person field notes on links (`.rel-field-note` CSS class) added by the now-shipped Spec 2 effort.

**Scratch workspace / traps:**
- ⚠️ **Don't confuse this with the DONE Spec 2 effort.** `mkultra-spec2-shipped-handoff.md` documents finished, unrelated work (typography/palette/wordmark/cursor/field-notes/WebGL-fallback) on the same file. This voice-narration effort is new and separate.
- ⚠️ **Freeze-check scope differs from the Spec 2 convention.** The project convention freeze-checks `bullion_mk11.html` through `bullion_mk18.html` as untouched archives during Mk Ultra work. **This effort explicitly intends to edit `bullion_mk18.html`** — when it starts, freeze-check `mk11`–`mk17` only; `mk18` is an intentional target, not a frozen archive, for this specific effort.
- ⚠️ No audio files, generation scripts, or pilot node list exist yet — none of that has been decided down to specifics (see "What's next").

**Not mine — leave alone:** same pre-existing untracked noise as always — `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`, `.codex/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple), `bullion-live-map/__pycache__/`, `bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`. **Never `git add .`/`-A`.**

## What has changed

Nothing on disk. All progress below is decisions reached in conversation — trust this list
over any vaguer recollection:

- **Content scope:** narrate node **beginner**-mode text only (not expert) + mkultra's 2
  first-person field notes. The AI-generated market narrative (`#narrative-box`, calls
  `api.anthropic.com`) is explicitly **out of scope** — it's different text every time "Run AI
  analysis" is clicked, so it can't be pre-generated as a static file.
- **Voice:** the user's own voice, cloned via a **free, self-hosted, open-source** model —
  Chatterbox was identified via web research as the current (2026) best open-source
  quality/ease-of-setup match (reportedly beat ElevenLabs in blind listening tests); GPT-SoVITS
  and Kokoro were mentioned as alternatives. **Not** a paid cloud API.
- **ElevenLabs was researched and explicitly rejected.** Its Free tier has no voice cloning at
  all; cheapest cloning tier is Starter at $6/mo (Instant Voice Cloning, 30k credits/mo). The
  user chose the free self-hosted path instead ("we have to make sacrifices" — meaning: drop
  the AI-narrative narration, which only the live-API path could have covered).
- **A Cloudflare Worker + client-side API-key-storage design was discussed and then abandoned.**
  It was the right answer *for the paid-cloud-API path* (hide the ElevenLabs key server-side,
  since this repo's HTML files are committed straight to a public repo and served as-is on
  public GitHub Pages — nothing can be hardcoded in source). Once the user picked the free
  self-hosted route, that entire concern became moot: pre-generated static files need no live
  API call, no key, no proxy. **Do not resurrect the Worker/key-storage design** unless the user
  later asks for live synthesis instead of static files.
- **Delivery mechanism:** generate audio files once, offline, on the user's own machine (this
  session's Bash tool operates directly on the user's real Mac — `darwin`, home dir
  `~` — not a sandboxed cloud VM, so a future session can plausibly run the
  actual model install + generation via Bash). Expect real setup cost: Python env, a multi-GB
  model download, and slow-ish CPU-only inference (no GPU assumed) — this was flagged to the
  user as a risk, not yet tested.
- **Initial rollout scope: PILOT, not full coverage.** A small subset of ~5–8 nodes (not all
  ~39) plus the 2 field notes, to prove the pipeline end-to-end before scaling up node-by-node.
  This was the user's explicit choice over "beginner text, all nodes" and "beginner + expert,
  all nodes."
- **Target files:** both `bullion_mk18.html` and `bullion_mkultra.html`.
- **Approach proposed and recommended (NOT yet confirmed by the user):** "Approach 1" — a local
  generation script produces static MP3s under `bullion-live-map/audio/narration/`; each
  narrated node/field-note gets a small 🔊 button in `#detail-panel` (or next to the field note)
  that plays the matching file via a plain `Audio()` object; nodes with no generated clip simply
  don't show a button (no errors, clean pilot-then-expand path). Two alternatives were presented
  and **not** chosen: a single concatenated "narrate this page" master track (rejected — doesn't
  match the click-a-node-to-read-it interaction model), and a Web-Speech-API-fallback hybrid
  (rejected — adds a second code path and a jarring mixed-voice experience, which cuts against
  the "small pilot, prove it works first" scope just chosen).

## What has failed / risks / caveats

- **Nothing has failed** — no code has been written yet, so nothing has broken.
- **UNVERIFIED:** whether Chatterbox (or GPT-SoVITS) actually installs and runs cleanly on this
  specific Mac. Completely untested — treat as a real one-time setup risk, not a solved step.
- **UNVERIFIED:** CSP impact of adding local audio playback. `bullion_mk18.html`'s CSP
  (`default-src 'self'; script-src 'self' 'unsafe-inline'; ...`) has no explicit `media-src`
  directive, so same-origin audio should fall through to `default-src 'self'` and just work —
  but this is an assumption, confirm with a real browser load before treating it as settled.
- **Nothing overrides a prior plan** — there is no prior plan for this effort; this is the first
  and only design conversation so far.

## What's next (ordered)

1. Resume `superpowers:brainstorming`. Ask the user to confirm or reject **Approach 1** (they
   had not yet answered when this handoff was requested).
2. Once confirmed, finish presenting the design in full per the brainstorming skill: exact audio
   file naming/path convention, exact pilot node-ID list (not yet chosen — "~5–8 nodes" was
   illustrative, not decided), exact button markup/placement in `#detail-panel`, error handling
   for missing/failed audio, and how mkultra's field notes (stored in the merged
   `LINKS`+`PLUMBING_LINKS` structure — see `[[bullion-two-link-arrays]]` memory) get their audio
   hooked in.
3. Write the spec to `docs/superpowers/specs/2026-07-29-bullion-voice-narration-design.md` (or
   today's real date if resumed later), run the spec self-review checklist, commit it.
4. Get the user's sign-off on the written spec.
5. Invoke `writing-plans` to produce the implementation plan — it will need to cover: recording
   the voice sample, installing/running the local cloning tool, generating the pilot's audio
   files, and the front-end wiring in both target files.

## Verification idioms used in this project (for the resuming session)

No narration-specific verification exists yet (no code to verify). Reuse this project's
established idioms once implementation starts — documented in full in
`mkultra-spec2-shipped-handoff.md`:
- Real headless-Chrome DOM probes, always with an isolated `--user-data-dir` (never run
  headless Chrome against these files without one — it has twice closed the user's real Chrome
  window when run without isolation).
- Freeze-check via `shasum -a 256` — for this effort, check `bullion_mk11.html`–`mk17.html`
  only (not `mk18.html`, which this effort intentionally edits).
- Python suite: `cd bullion-live-map && python3 -m unittest discover -s tests && python3 -m
  unittest test_calibrate` — sanity check after any change, unrelated to this JS/audio work but
  cheap to re-run.
- `git push` works directly via Bash (`GIT_TERMINAL_PROMPT=0 git push origin main`); no `gh`
  installed.

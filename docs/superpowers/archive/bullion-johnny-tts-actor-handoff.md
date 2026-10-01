# Bullion Narration — Johnny Voice Switched to Direct Actor TTS — Session Handoff

**Written:** 2026-08-02 · **For:** any future session resuming this work — this continues
directly from `bullion-johnny-actor-voice-handoff.md` (that handoff's blocker — explicit
sign-off on rate 218 + the actor-90% VC blend — was resolved and committed as `b4c8e0b`
earlier the same day, before this session's own visible context began). This session
**replaced that VC-blend mechanism for Johnny entirely** — read "Current state" below
before assuming anything about Johnny's pipeline from the prior handoff still applies.

## Goal

Capture more liveliness, bitterness, and humaneness in Johnny's voice. The user rejected
the `b4c8e0b` result on first listen. Root-caused it to a structural ceiling: Johnny's
pipeline was `say` (flat, robotic TTS) piped through ChatterboxVC (timbre recoloring
only) — VC cannot invent emotional performance the source audio's prosody never had.
Fixed by switching Johnny to ChatterboxTTS's **native text-to-speech** mode, generating
directly from the hired actor's recording with no `say` scaffold and no blend.

- Prior handoff (VC-blend history, the meanness-pitch saga, Tom's original role — all now
  superseded for Johnny's mechanism, but the SDD Tasks 1-3 history is still accurate):
  `docs/superpowers/bullion-johnny-actor-voice-handoff.md`
- No spec/plan doc for this session — handled fully inline, same "small work stays inline"
  posture as every prior ad-hoc tuning session in this project. No SDD ledger entry.

## How to resume (do this first)

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline
   b4c8e0b..HEAD` should show exactly 1 commit, `c900ad3`, on `main`. `git status --short`
   should be clean except the standing "Not mine" untracked noise (list below). Confirmed
   fully pushed (`+0 -0` vs `origin/main`) and the GitHub Pages deploy for `c900ad3`
   completed/success (checked via the API method below — `gh` is not installed on this
   machine).
2. Read this handoff in full. The prior handoff is only needed for older history (VC-blend
   mechanics, why the meanness pitch-shift was rejected, Tom's original purpose) — none of
   that applies to Johnny's current mechanism anymore.
3. **Immediate next action: none blocking.** This work is fully shipped and confirmed by
   the user. The only open item is a quality ceiling, not a bug — see "What's next."

## Current state (active files)

**Branch:** `main`, 1 commit ahead of base `b4c8e0b` (`c900ad3`), fully pushed, clean tree.

**Committed in `c900ad3`:**

- `bullion-live-map/scripts/generate_narration.py` — Johnny is now synthesized by a new
  `synthesize_johnny()` that calls `ChatterboxTTS.generate()` directly
  (`audio_prompt_path=ACTOR_SAMPLE_PATH`, `exaggeration=JOHNNY_EXAGGERATION` (0.8),
  `cfg_weight=JOHNNY_CFG_WEIGHT` (0.3)) — confirmed-by-ear settings, don't change without a
  fresh A/B. Added `load_tts_model()`. Removed entirely: `johnny_ref_dict()`,
  `JOHNNY_ACTOR_WEIGHTS`, `JOHNNY_RATE`, `TOM_VOICE`, `TOM_SAMPLE_PATH`. Also removed the
  now-unused `weights` param from `build_blended_ref_dict()` (only Alfred calls it now, a
  plain 2-way mean). **Alfred's pipeline (`say` + ChatterboxVC blend of Jamie+user) is
  completely untouched.**
- `bullion-live-map/scripts/test_voice_blend.py` — dropped the Tom/weighted-blend-specific
  tests (`test_weighted_average_matches_johnny_actor_blend` deleted;
  `test_three_way_average_matches_johnny_blend_shape` renamed to
  `test_averages_embedding_across_three_clips` since it was actually generic, not
  Johnny-specific); fixed `test_synthesizes_missing_tom_and_jamie_clips` →
  `test_synthesizes_missing_jamie_clip` (call_count 1, not 2); added
  `TestSynthesizeJohnny.test_generates_from_actor_sample_with_confirmed_settings`, which
  locks in the actor path + exaggeration/cfg_weight values as a regression guard.
- `bullion-live-map/audio/voice_sample/tom_sample.wav` — deleted (Tom is unused anywhere
  in the pipeline now).
- `bullion-live-map/scripts/spike_voice_blend.py`,
  `bullion-live-map/scripts/spike_johnny_actor_blend.py` — deleted. Both only exercised the
  now-removed Johnny blend mechanism; this was an explicit "keep or delete" question open
  across two prior handoffs, resolved here since the change made them dead code (not just
  unused).
- All 45 `bullion-live-map/audio/narration/*.mp3` regenerated. The 39 `node-*.mp3` (Alfred)
  changed only due to ChatterboxVC's inherent generation non-determinism — no logic change
  touched Alfred's path. The 6 `johnny-*.mp3` are the real deliverable.

**Files later work might touch (untouched this session):**

- `bullion-live-map/audio/voice_sample/actor_sample.wav` — unchanged; still the `[0–10s]`
  window of the actor's raw recording. Now the **sole** voice source for Johnny (was 90% of
  a blend before). The other two "clean" segments of the actor's original 66s recording
  (`[14–42]`, `[47–end]`) remain untested as alternate references — still parked, not
  solved.

**Scratch workspace / traps:**

- ⚠️ `~/Downloads/Nhà Hàng Phương Nam.m4a` — the actor's original raw recording. Its
  filename reads as Vietnamese; the user explicitly said not to weight that ("don't pay too
  much attention to the vietnamese... it is what it is"). Noted here so a resuming session
  doesn't reopen that question.
- ⚠️ **This session hit repeated background-process kills on long ChatterboxTTS runs** — a
  known, recurring infra limitation in this project (see the archived accent-debug
  handoff, `docs/superpowers/archive/voice-narration-accent-debug-handoff.md`, for the same
  pattern hitting a different Chatterbox run). The full 45-clip batch regen died mid-Johnny
  (only `johnny-fed.mp3` finished before the kill). **Resumed by generating one Johnny line
  per process invocation** instead of one big batch call — a kill then only costs the
  one in-flight line. Two of five remaining lines still needed a retry after being killed
  again on the first attempt (immediately, mid-fast-progress — not a stall, likely a
  harness-level constraint on background process duration/count). If regenerating Johnny
  again, prefer the per-line pattern over calling `main()`'s full batch for Johnny's part.
- ⚠️ `caffeinate -w <pid>` was used repeatedly to prevent system sleep from stalling
  generation — one very long stall (~75 minutes stuck on a single autoregressive sampling
  step) was traced to the system sleeping mid-run. Must be pinned to the actual generation
  process's PID **each time it's (re)started** — it exits when that PID exits, so it does
  not carry over between invocations.
- ⚠️ `afplay` intermittently failed for about an hour this session (`AudioQueueStart`
  errors, then hangs with no error) — self-resolved by morning with no explicit fix
  applied. If it recurs, don't loop retries past 2-3 attempts; it's likely a CoreAudio/sleep
  state issue outside this script's control — ask the user to check locally or just wait.
- **Not mine — leave alone** (same as every prior handoff in this project, plus one
  addition): `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`,
  `.agents/`, `.codex/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple), `.superpowers/`
  (pre-existing SDD/brainstorm scratch state from unrelated prior work — confirmed this
  session, not something this work created despite briefly looking newly-untracked),
  `bullion-live-map/__pycache__/`, `bullion-live-map/scripts/__pycache__/`,
  `bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`, and older untracked
  plan/spec docs from unrelated prior work. **Never `git add .`/`-A`.**

## What has changed

- Diagnosed why liveliness/bitterness were missing even after `b4c8e0b`'s actor-dominant
  blend: `say` (flat, robotic TTS) piped through ChatterboxVC (timbre recoloring only)
  caps emotional performance at whatever `say` produced — VC can't invent character the
  source audio's prosody never had.
- Tried and rejected: stronger `say` embedded prosody markup (`[[slnc]]`, `[[pbas]]` —
  confirmed via direct measurement that `[[pbas]]` has a real, large effect (>1 octave
  swing) while `[[emph +/-]]` has **zero** measurable effect on the "Jamie (Premium)"
  voice). User's verdict on the strongest version tried: "no to both."
- Tried and confirmed: ChatterboxTTS native TTS mode, generating directly from the actor's
  recording alone, `exaggeration=0.8`/`cfg_weight=0.3`. User: "i like the second version I
  heard" — confirmed again on a second, different script line before treating it as
  validated (single-sample confirmation is weak evidence, per this project's own prior
  debugging convention).
- Implemented in production, regenerated all 45 clips (via the per-line resume pattern
  above, due to repeated kills), all 4 test suites green (41+33+22+7), committed
  `c900ad3`, pushed, GitHub Pages deploy for `c900ad3` confirmed `completed`/`success`.
- **Final user verdict on the shipped clips** (after listening to all 6 directly):
  *"good enough for AI but not seem 1:1 with the voice actor I hired, we can feel a bit
  robotic undertone but it's alright enough for now."* Shipped as-is on that basis.

## What has failed / risks / caveats

- **Nothing has failed in the final shipped state** — all tests green, deploy confirmed
  success, user explicitly signed off before commit and push.
- **Known, accepted limitation:** user-flagged "robotic undertone," not 1:1 with the real
  actor's delivery. This was shipped anyway as "good enough for now," not silently
  accepted as a non-issue — a resuming session should not assume this is fully solved.
- If revisited, candidate next levers **not yet tried this session:** the other two clean
  segments of the actor's raw recording as alternate `audio_prompt_path` references;
  `exaggeration`/`cfg_weight` values other than 0.8/0.3; ChatterboxTTS's other generation
  params (`repetition_penalty`, `temperature`, `min_p`, `top_p`) — none explored.
- `actor_sample.wav`'s gitignore negation (the "third-party voice actor's recording
  published to a public GitHub Pages repo" privacy tradeoff flagged in the prior handoff)
  was already resolved **before** this session started (negation added in `b4c8e0b`) — not
  reopened here, just confirming it's settled and still in place.

## What's next (ordered)

1. **Nothing blocking.** If the user wants to push Johnny's voice quality further (closer
   to the actor's real delivery, less "robotic undertone"), start from the untried levers
   listed above — get a quick A/B on one line before touching all 6 production clips again.
2. If Alfred ever needs similar treatment, note Alfred's pipeline (`say` + ChatterboxVC
   blend of Jamie+user) is completely unchanged and still uses the old mechanism — a
   parallel TTS-direct approach has not been evaluated for Alfred.

## Verification idioms used in this project (for the resuming session)

- Test suite: `cd bullion-live-map && python3 -m unittest discover -s tests && python3 -m
  unittest test_calibrate && python3 -m unittest scripts.test_generate_narration -v` (plain
  `python3`, no heavy deps — `41 + 33 + 22`) **and separately** `.venv-narration/bin/python3
  -m unittest scripts.test_voice_blend -v` (needs torch/librosa/chatterbox — `7` tests).
- Real generation: `.venv-narration/bin/python3 scripts/generate_narration.py` for the full
  batch — **expect it may get killed on long runs** (see trap above). For Johnny
  specifically, prefer generating one line at a time rather than the full `main()` batch,
  since a kill then only costs one line.
- **Audible correctness is never automatable in this project** — every voice change ends in
  a real human listening pass (`afplay` or local playback), never inferred from clean test
  runs or exit codes.
- Required macOS voice: `Jamie (Premium)` (`en_GB`), needed for Alfred only. `Tom
  (Enhanced)` is **no longer required** by this pipeline at all.
- Reference clips: `bullion-live-map/audio/voice_sample/{user_voice.wav, jamie_sample.wav,
  actor_sample.wav}` — `tom_sample.wav` is gone, no longer needed.
- GitHub Pages deploy verification: **no `gh` CLI installed on this machine** (confirmed
  this session, contradicting a stale note in an older handoff). Use `curl -s
  "https://api.github.com/repos/SinbadTheExplorer/claudekit/actions/runs?per_page=5"`
  (public API, works unauthenticated for this public repo) and check the run for the
  relevant commit shows `completed`/`success`. Don't trust `curl -sI <pages-url>`/
  `last-modified` header timing alone.

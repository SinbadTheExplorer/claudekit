# Bullion Narration Voice-Conversion Blend ("Thamie") — Session Handoff

**Written:** 2026-08-01 · **For:** any future session resuming this work — the core
voice-blend feature is built, reviewed, and committed through `635d053`, but there is
**uncommitted follow-up work on top of that** (rate + Johnny voice changes) still awaiting
the user's listening confirmation. Do not push, and do not assume `635d053` reflects the
current pipeline behavior — read "Current state" below first.

## Goal

Fix the reported "robotic/synthetic" quality of Bullion's `say`-CLI narration (both
personas, Alfred and Johnny) by adding a `ChatterboxVC` voice-conversion pass that blends
in the user's own voice plus other `say` voices, instead of replacing the TTS engine
outright. Resolves the deferred `bullion-thamie-voice-blend-idea` project memory.

- Spec: `docs/superpowers/specs/2026-08-01-bullion-thamie-voice-blend-design.md`
- Plan: `docs/superpowers/plans/2026-08-01-bullion-thamie-voice-blend.md` (4 tasks)
- Progress ledger (recovery map for Tasks 1-3 + the final whole-branch review — **trust
  this over this handoff's prose for that history**):
  `.superpowers/sdd/2026-08-01-bullion-thamie-voice-blend/progress.md`

## How to resume (do this first)

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline
   06332ba..HEAD` should show 8 commits ending at `635d053`, on `main`. Then run `git
   status --short` — it will show **~47 modified/uncommitted files** (45 `.mp3`s +
   `generate_narration.py` + `test_voice_blend.py`). This uncommitted state is real,
   intentional, in-progress work from this session — not stray noise. See "Current state"
   below for exactly what it is.
2. Read the ledger in full — it's the authority on Tasks 1-3 and the final whole-branch
   review's findings/fix wave, all of which are already committed and done. **But note:**
   the ledger's prose still refers to `pitch_shift_semitones` / `apply_meanness` /
   `JOHNNY_MEANNESS_PITCH_SHIFT_SEMITONES` as if live — those were removed from the code in
   the uncommitted follow-up (see below). Trust the actual current file content over the
   ledger's naming for anything related to Johnny's pitch/meanness.
3. **Immediate next action:** get the user's explicit listening confirmation on the
   uncommitted regeneration (rate 233 for both personas, Johnny reverted to a plain
   3-way blend with no pitch processing). They had only heard 2 of the 45 regenerated
   clips (Alfred/"gold", Johnny/"gold") before this handoff was requested mid-listening-pass
   — resume by playing a few more (paths under "Verification idioms" below), not by
   assuming the 2 already heard constitute a full pass.

## Current state (active files)

**Branch:** `main`, 8 commits ahead of base `06332ba` (`0c9e702`..`635d053`), **plus
uncommitted local changes on top of `635d053`.**

**Committed through `635d053`:** the full voice-blend pipeline (`generate_narration.py`'s
blend-embedding helpers, `synthesize()`/`main()` wiring), `test_voice_blend.py`, the
throwaway `scripts/spike_voice_blend.py`, the design spec + implementation plan (with a
mid-project correction commit each), and the first real regeneration of all 45 clips.
Also includes the final review's fix wave: `user_voice.wav`/`tom_sample.wav`/
`jamie_sample.wav` committed (gitignore corrected via `audio/voice_sample/*` +
per-file negations — a deliberate privacy tradeoff the user explicitly approved, see
ledger), a `TestSynthesizePitchGating` test class, and a `pitch_shift_semitones` →
`apply_meanness` rename.

**Uncommitted, on top of `635d053` (this session, not yet confirmed by ear):**
- `bullion-live-map/scripts/generate_narration.py` — `ALFRED_RATE`/`JOHNNY_RATE` both
  changed from `240`/`225` to `233`. **Johnny's meanness pitch-shift was fully removed**,
  not just disabled: `JOHNNY_MEANNESS_PITCH_SHIFT_SEMITONES` constant, the
  `apply_johnny_meanness()` function, and `synthesize()`'s `apply_meanness` parameter are
  all gone — `synthesize()` is back to its original 5-arg signature
  `(text, rate, output_mp3_path, vc, ref_dict)`. Johnny now uses the plain 3-way blend
  (Tom + user + Jamie) with zero pitch processing, same as Alfred gets zero pitch
  processing. Module docstring also fixed (was stale, said Chatterbox was "dropped" —
  ledger's Task 3 minor #7, done opportunistically while in the file).
- `bullion-live-map/scripts/test_voice_blend.py` — `TestApplyJohnnyMeanness` and
  `TestSynthesizePitchGating` classes deleted (they tested code that no longer exists).
  Current suite: 5 tests (`TestBuildBlendedRefDict` ×3, `TestEnsureReferenceClips` ×2), all
  passing.
- 45 `bullion-live-map/audio/narration/*.mp3` files — regenerated a **second** time this
  session (rate 233, Johnny's plain blend, no pitch-shift). Generation completed cleanly
  (exit 0, all 45 `wrote ...` lines present). Both test suites re-run clean after
  regeneration: `41 + 33 + 22` (plain `python3`) `+ 5` (`.venv-narration`, was 7 before the
  2 test-class deletions above).

**Scratch workspace / traps:**
- ⚠️ `bullion-live-map/audio/voice_sample/spike_output/` contains several throwaway
  listening-test files from this session (`alfred_blend_spike.wav`,
  `johnny_blend_spike.wav`, `johnny_blend_spike_meaner.wav`, `johnny_mild_a.wav`,
  `johnny_mild_b.wav` — -1.5, then -0.5 and -0.8 semitone candidates, all superseded).
  Untracked, gitignored (matched by `audio/voice_sample/*`, not one of the 3 negated
  files). Safe to ignore or delete; not a deliverable.
- ⚠️ `bullion-live-map/scripts/spike_voice_blend.py` is **committed** (from Task 1) but was
  meant to be throwaway — the final whole-branch review already flagged it as duplicating
  production logic (ledger minor #8), and it's now *further* stale: it still contains its
  own local `apply_johnny_meanness(src, dst)` helper for a mechanism the production code no
  longer has at all as of the uncommitted changes. Not deleted yet — open item, see "What's
  next".
- ⚠️ The "menacing" Johnny voice (3-way blend + -1.5 semitone pitch-down) that got removed
  from production this session is **not yet written up anywhere as a spec** — the user
  asked for it to be saved as a documented idea for a possible future third
  persona/preset, explicitly NOT built now. This was promised but not started — see "What's
  next" #4.

**Not mine — leave alone (pre-existing untracked noise, same as every prior handoff in
this project):** `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`,
`.agents/`, `.codex/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple),
`bullion-live-map/__pycache__/`, `bullion-live-map/scripts/__pycache__/`,
`bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`, and several older
untracked plan/spec docs from unrelated prior work. **Never `git add .`/`-A`.**

## What has changed

- Full feature built via `superpowers:brainstorming` → `superpowers:writing-plans` →
  `superpowers:subagent-driven-development` (Tasks 1-3, each individually
  task-reviewed clean) → a final whole-branch review (opus) that found 4 Important
  findings, all resolved in one fix wave, scoped re-review clean. Full history in the
  ledger. All committed through `635d053`.
- **Mid-Task-4 (the listening pass), the user asked for 3 changes not in the original
  plan**, handled inline (not via SDD, per the project's own "small work stays inline"
  convention):
  1. Both personas' speaking rate → 233 wpm (was Alfred 240, Johnny 225 — the pre-project
     by-ear tuning).
  2. Johnny's -1.5 semitone meanness pitch-down (added earlier in this same session, see
     ledger) was reported as "quite menacing" — the user first wanted it kept as a real,
     usable preset for a *different* future persona, then explicitly reversed that to
     "just write a spec for later, don't build it now."
  3. Two milder pitch-down candidates for Johnny (-0.5, -0.8 semitones) were spiked and
     played, but the user rejected pitch-shift as a mechanism entirely ("semitone ain't
     it") — final call: Johnny reverts to the **plain** 3-way blend, no pitch processing
     of any kind. (A different, non-pitch lever — e.g. formant/EQ shaping — was explicitly
     parked for a possible future session, not pursued now.)
- All 3 changes implemented directly by the controller (small, well-scoped constant/code
  changes on top of already-reviewed working code — not re-run through the full SDD
  task+review loop). Regenerated all 45 clips a second time; both suites re-run clean.
  **Not yet committed** — awaiting listening confirmation.

## What has failed / risks / caveats

- **Nothing has failed technically.** All tests pass, both regeneration runs completed
  with exit 0, no errors in either run's output.
- **UNVERIFIED — this is the actual blocker:** the user has not yet confirmed by ear that
  rate 233 + Johnny's reverted plain blend actually sound right. They heard exactly 2 of
  the 45 regenerated clips (Alfred/"gold", Johnny/"gold") before asking for this handoff
  instead of confirming. Do not commit, push, or consider Task 4 done until they explicitly
  say so.
- The deferred "third voice" spec (documenting the -1.5 semitone Tom+user+Jamie blend as
  prior art for a possible future persona, confirmed "quite menacing" by ear) **has not
  been written** — promised, not started.
- The 2 "field note" link clips (`link-credit-equit.mp3`, `link-usd-oil.mp3`) are still on
  the **old**, pre-blend `say`-only voice — confirmed pre-existing (never wired into any
  version of `main()`'s generation loop, not a regression from this feature). The user
  heard the contrast directly (played `link-usd-oil.mp3` back-to-back with blended clips)
  and explicitly chose to defer fixing this rather than expand this session's scope. Known,
  accepted gap — not a bug.
- Task 4 Step 1 (automated browser/console-error check via Claude-in-Chrome) was
  **explicitly skipped** — the extension wasn't connected this session and the user chose
  to skip rather than reconnect, on the reasoning that the real acceptance gate is the
  audio listening pass anyway.
- **Push has not happened.** Task 4's Step 3 (fresh push decision) and Step 4 (confirm
  GitHub Pages deploy via Actions, not just `curl`/`last-modified` timing) are both still
  pending, blocked on the listening confirmation above.
- The SDD workspace (`.superpowers/sdd/2026-08-01-bullion-thamie-voice-blend/`) was
  deliberately **kept, not deleted**, specifically so this handoff could cite its full
  ledger — normal convention is to delete it once the final review is clean, but the
  controller judged the deferred-minors record would otherwise only exist in chat history.
  Delete once this handoff's "what's next" list is done.

## What's next (ordered)

1. Resume the listening pass: play a few more of the 45 regenerated clips (not just the 2
   already heard) — see paths under "Verification idioms" below — and get the user's
   explicit yes/no before anything else.
2. **If confirmed:** review `git status --short` (same "Not mine" caution as always), then
   commit the 45 mp3s + `generate_narration.py` + `test_voice_blend.py` in one commit.
   Suggested message theme: "Change both personas' rate to 233wpm, drop Johnny's meanness
   pitch-shift (reverted to plain blend after further listening rejected pitch-shift as the
   right lever)."
3. **If NOT confirmed:** treat as new tuning work — small experiment, listen, iterate
   (same discipline as Task 1's spike) — do not regenerate all 45 clips again until a
   specific new configuration is confirmed on a small sample first.
4. Write the deferred "third voice" spec to `docs/superpowers/specs/` — capture: 3-way
   blend (Tom (Enhanced) + user's own voice + Jamie (Premium)) via the same
   embedding-averaging mechanism as Johnny's current blend, plus a -1.5 semitone
   post-conversion pitch-down, confirmed "quite menacing" by ear on 2026-08-01, deemed not
   suited to Johnny's actual character. Explicitly prior art / not-yet-built, not a
   foregone conclusion for whatever eventually uses it (a new persona? an easter egg?
   genuinely open).
5. Finish Task 4: ask a **fresh** push decision (never reuse a prior "yes"/"hold" — this
   project's standing convention, honored in every prior handoff), push if yes, then
   confirm the GitHub Actions "pages build and deployment" run for that commit shows
   `completed`/`success` (don't trust `curl -sI`/`last-modified` alone — a failed build
   leaves stale content indefinitely, per this project's own hard-won lesson from the orb
   feature's Pages outage).
6. Once Task 4 is fully done and this handoff's content is durable elsewhere (this file, or
   a future memory), delete the SDD workspace
   (`.superpowers/sdd/2026-08-01-bullion-thamie-voice-blend/`).
7. Open item: whether to finally delete `scripts/spike_voice_blend.py` (committed but
   throwaway-in-intent, now further stale — ledger minor #8). Not urgent, the user's call.

## Verification idioms used in this project (for the resuming session)

- Test suite: `cd bullion-live-map && python3 -m unittest discover -s tests && python3 -m
  unittest test_calibrate && python3 -m unittest scripts.test_generate_narration -v`
  (plain `python3`, no heavy deps needed — 41 + 33 + 22) **and separately**
  `.venv-narration/bin/python3 -m unittest scripts.test_voice_blend -v` (needs
  torch/librosa/chatterbox — 5 tests as of the uncommitted changes).
- Real generation: `.venv-narration/bin/python3 scripts/generate_narration.py` — **never**
  plain `python3` (the pipeline needs `torch`/`chatterbox`, only installed in the venv).
  Takes roughly 10 minutes for all 45 clips (model load ~15s, then ~10s embedding + ~20s
  conversion per clip). Some clips to spot-check by ear after any future regeneration:
  `audio/narration/node-gold.mp3` (Alfred), `audio/narration/johnny-gold.mp3` (Johnny),
  plus `johnny-vix.mp3`/`node-sec.mp3` for a second data point per persona.
- Audible correctness is **never automatable** in this project — every voice change ends in
  a real human listening pass (`afplay` or the live browser), never inferred from test
  passes or console cleanliness alone. This is the standing rule, reconfirmed multiple
  times across this session.
- Required macOS voices (System Settings → Accessibility → Spoken Content → Manage
  Voices): `Jamie (Premium)` (`en_GB`) and `Tom (Enhanced)` (`en_US`) — both confirmed
  installed this session via `say -v '?'`, not guaranteed present on a fresh machine.
- Reference clips: `bullion-live-map/audio/voice_sample/{user_voice.wav, tom_sample.wav,
  jamie_sample.wav}` — all 3 now committed to git (as of `635d053`, via a corrected
  `.gitignore`: `audio/voice_sample/*` plus 3 per-file negations) — a deliberate privacy
  tradeoff the user explicitly approved (the user's raw voice recording is now public on
  the GitHub Pages repo, not just processed narration output).
- GitHub Pages deploy verification: `gh run list --repo SinbadTheExplorer/claudekit
  --limit 3` and check the run for the relevant commit shows `completed`/`success` — don't
  trust `curl -sI <pages-url>`/`last-modified` header timing alone, confirmed unreliable in
  a prior session (see `bullion-persona-orb-shipped-handoff.md`).

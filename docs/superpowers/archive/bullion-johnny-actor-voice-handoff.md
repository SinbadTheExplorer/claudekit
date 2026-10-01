# Bullion Narration — Johnny Actor-Voice Blend & Rate Tuning — Session Handoff

**Written:** 2026-08-01 · **For:** any future session resuming this work — this continues
directly from `bullion-thamie-voice-blend-handoff.md` (that handoff's blocker is now
resolved and committed at `0b9fa7f`). This session's own work is **entirely uncommitted**
and has its own, different blocker — read "Current state" below before doing anything.

## Goal

Make Johnny's blended voice draw mainly from a real recording by a professional voice
actor the user hired (`~/Downloads/Nhà Hàng Phương Nam.m4a`), instead of the equal-weight
Tom+user+Jamie blend from the prior session, and re-tune both personas' speaking rate
down from 233wpm. No new spec/plan doc was written for this — it was handled inline per
this project's "small work stays inline" convention (same posture the prior session used
for its rate/meanness tweaks).

- Prior handoff (deeper history — SDD Tasks 1-3, the meanness-pitch saga): `docs/superpowers/bullion-thamie-voice-blend-handoff.md`
- Progress ledger (still the authority for Tasks 1-3 + the whole-branch review, **not** for anything in this handoff): `.superpowers/sdd/2026-08-01-bullion-thamie-voice-blend/progress.md`
- No spec exists for this session's actor-blend weighting decision — this handoff plus chat history is the only record. Consider writing one if this becomes a recurring pattern (e.g. more third-party reference voices later).

## How to resume (do this first)

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline 06332ba..HEAD` should show 9 commits ending at `0b9fa7f`, on `main`. Then run `git status --short` — it will show **45 modified `.mp3`s + `generate_narration.py` + `test_voice_blend.py` modified, plus `scripts/spike_johnny_actor_blend.py` untracked**. This is real, intentional, in-progress work from this session — not stray noise.
2. Read this handoff in full before touching anything. The prior handoff is only needed for older history (Tasks 1-3, the removed meanness pitch-shift) — this handoff supersedes it for anything about Johnny's blend composition or the personas' speaking rate.
3. **Immediate next action:** get the user's **explicit** listening confirmation on rate 218 (both personas) and Johnny's new actor-dominant blend. They replayed `johnny-gold.mp3` twice at rate 218 this session but never said an explicit "yes"/"sounds good"/"ship it" before this handoff was requested — do not commit, and do not assume the replays constitute sign-off.

## Current state (active files)

**Branch:** `main`, 9 commits ahead of base `06332ba` (ending `0b9fa7f`), **plus uncommitted
local changes on top of `0b9fa7f`.**

**Committed through `0b9fa7f`:** everything from the prior handoff — the full voice-blend
pipeline, both personas at 233wpm, Johnny's meanness pitch-shift fully removed (plain
3-way Tom+user+Jamie blend). That baseline is what this session's uncommitted diff sits on
top of.

**Uncommitted, on top of `0b9fa7f` (this session):**

- `bullion-live-map/scripts/generate_narration.py` —
  - Added `ACTOR_SAMPLE_PATH` constant and `JOHNNY_ACTOR_WEIGHTS = [0.90, 0.10/3, 0.10/3, 0.10/3]`.
  - `build_blended_ref_dict()` gained an optional `weights` param (defaults to `None` → plain mean, so all 3 pre-existing tests still pass unchanged).
  - `johnny_ref_dict()` now does a **4-way weighted blend**: the actor's clip at 90% of the embedding, Tom+user+Jamie splitting the remaining 10% — and the actor's clip is also the **sole acoustic-prompt source** (`prompt_clip_path=ACTOR_SAMPLE_PATH`), so his delivery texture/prosody carries through, not just his tone color. Alfred's blend (Jamie+user) is untouched.
  - `ensure_reference_clips()` now also raises if `ACTOR_SAMPLE_PATH` is missing — same posture as `user_voice.wav` (a real recording, not something this script can generate).
  - `ALFRED_RATE`/`JOHNNY_RATE`: two iterations this session, `233` → `225`/`224` → **`218`/`218`** (final). Only the 218 version is reflected in the file and in the current `audio/narration/*.mp3` files on disk; the 225/224 intermediate was fully overwritten by the second regen.
- `bullion-live-map/scripts/test_voice_blend.py` — added `test_weighted_average_matches_johnny_actor_blend` (locks in the weighted-mean formula against Johnny's actual production weights) and `test_raises_if_actor_sample_missing`; updated `test_synthesizes_missing_tom_and_jamie_clips` to also patch `ACTOR_SAMPLE_PATH` to the real path. Suite is now 7/7 (was 5).
- 45 `bullion-live-map/audio/narration/*.mp3` — regenerated **twice** this session (first at rate 225/224 with the actor blend, then again at rate 218/218, same blend). Both runs completed cleanly (exit 0, all 45 `wrote ...` lines present each time). Current files on disk reflect only the final 218/218 pass.

**New, untracked files this session:**

- `bullion-live-map/scripts/spike_johnny_actor_blend.py` — throwaway spike (mirrors `spike_voice_blend.py`'s pattern) used to A/B the actor sample before wiring it into production. Produces `johnny_actor_4way_spike.wav` (equal-weight 4-way, superseded) and `johnny_actor_90pct_spike.wav` (the 90/10 weighting that got confirmed and shipped) under `audio/voice_sample/spike_output/`. Same open question as the prior handoff's item #7 for `spike_voice_blend.py`: keep or delete once this work is committed — consider resolving both together.
- `bullion-live-map/audio/voice_sample/actor_sample.wav` — converted from the user's `~/Downloads/Nhà Hàng Phương Nam.m4a` (a recording by a professional voice actor the user hired) via `ffmpeg -ac 1 -ar 22050 -c:a pcm_s16le`, matching the existing sample format. **⚠️ Currently gitignored** — `bullion-live-map/.gitignore`'s `audio/voice_sample/*` pattern has per-file negations for `user_voice.wav`/`tom_sample.wav`/`jamie_sample.wav` only. `actor_sample.wav` has **no negation yet**, so it will never be picked up by `git add`/show up as stageable, even though `generate_narration.py` now hard-requires it to exist. Until this is resolved, the narration pipeline is only reproducible on this one machine.

**Scratch workspace / traps:**

- ⚠️ `bullion-live-map/audio/voice_sample/spike_output/` now also has this session's `johnny_actor_4way_spike.wav` and `johnny_actor_90pct_spike.wav` alongside the prior session's `alfred_blend_spike.wav`/`johnny_blend_spike*.wav`/`johnny_mild_*.wav`. All gitignored, all superseded/throwaway, safe to ignore or delete — not deliverables.
- ⚠️ **The `actor_sample.wav` gitignore gap (above) is the biggest open decision.** The prior session already made a "deliberate privacy tradeoff" to publish the user's *own* voice (`user_voice.wav`, negated + committed in `635d053`) to a public GitHub Pages repo. **Do not assume the same answer extends to `actor_sample.wav`** — it's a third party's (the hired actor's) recording, a different consent/exposure question. Ask fresh.
- ⚠️ `bullion-live-map/scripts/spike_voice_blend.py` is still sitting there, committed-but-stale, from the prior handoff's unresolved item #7 — untouched this session, still open.
- **Not mine — leave alone** (same as every prior handoff in this project): `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`, `.codex/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple), `bullion-live-map/__pycache__/`, `bullion-live-map/scripts/__pycache__/`, `bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`, and several older untracked plan/spec docs from unrelated prior work. **Never `git add .`/`-A`.**

## What has changed

- Fully inline this session (no SDD, no spec/plan doc):
  1. Converted the user's uploaded `m4a` to `actor_sample.wav`.
  2. Spiked an **equal-weight 4-way** blend (Tom+user+Jamie+actor) — user liked the direction but wanted the actor to dominate.
  3. Spiked a **90/10 weighted** blend (actor 90%, actor also as the prompt clip) — user confirmed this by ear ("sounds good").
  4. Wired the 90/10 blend into production `johnny_ref_dict()`, added `weights` support to `build_blended_ref_dict()`, regenerated all 45 clips at the then-current rates (Alfred 225 / Johnny 224).
  5. User found it "fast," asked for rate 218 for both personas. Regenerated all 45 clips again at 218/218.
  6. User asked to replay `johnny-gold.mp3`; it was replayed twice. No explicit final verdict was given before this handoff was requested.
- Also discussed and deliberately deferred: whether to use more than the first 10 seconds of the actor's 66-second recording. `ChatterboxVC`'s `DEC_COND_LEN` caps the model's read at the first 10s of whichever file is loaded, regardless of how much audio the file contains. The user confirmed `[0s–10s]` of `actor_sample.wav` is already one of their three identified "clean" segments (`[0–10]`, `[14–42]`, `[47–end]`), so no re-trim was performed — this is not a workaround, it's the actual constraint. The other two clean windows are currently unused; revisit only if the reference-window logic ever changes.

## What has failed / risks / caveats

- **Nothing has failed technically.** Both regeneration runs exited 0 with all 45 `wrote ...` lines present. All test suites are green: `41 + 33 + 22` (plain `python3`) `+ 7` (`.venv-narration`, up from 5 — 2 new tests added this session).
- **UNVERIFIED — this is the actual blocker:** rate 218 (both personas) and Johnny's actor-dominant blend have **not** received an explicit sign-off. Two separate `afplay` replays of `johnny-gold.mp3` happened, but the user never said a clear "yes." Do not commit, push, or consider this done until they explicitly confirm.
- `actor_sample.wav`'s gitignore status (above) is an **unresolved decision**, not a bug — get an explicit answer before any commit that would include (or should include) it.
- The deferred second/third clean-segment question (`14–42s`, `47s–end` of the actor recording) is parked, not solved.
- Same pre-existing, unrelated gap the prior handoff noted: `link-credit-equit.mp3` / `link-usd-oil.mp3` are still on the old pre-blend `say`-only voice — not touched, not a regression from this session.
- **Nothing has been pushed or committed this session** — there is no pending "fresh push decision" yet; that only becomes relevant after a commit happens.

## What's next (ordered)

1. Get the user's **explicit** sign-off on rate 218 + Johnny's actor-90% blend. Ask directly — do not infer approval from "do johnny again" or any replay alone.
2. Resolve the `actor_sample.wav` gitignore gap: either add `!audio/voice_sample/actor_sample.wav` to `bullion-live-map/.gitignore` (ask the user first — third party's recording, same public-Pages-exposure question as before but for someone else's voice), or explicitly decide to keep it local-only and flag that the pipeline becomes non-reproducible from a fresh clone as a result.
3. **If confirmed:** review `git status --short` (same "Not mine" caution as always), then commit the 45 mp3s + `generate_narration.py` + `test_voice_blend.py` (+ `actor_sample.wav` if step 2 says yes) in one commit. Suggested message theme: "Blend Johnny's voice 90% from a hired voice actor's reference recording, drop both personas' rate to 218wpm."
4. Decide the fate of `scripts/spike_johnny_actor_blend.py` — same open question as `spike_voice_blend.py` (prior handoff's item #7, still unresolved). Consider resolving both together.
5. **If NOT confirmed at step 1:** treat as further tuning — do not regenerate all 45 clips again until a new specific configuration (rate and/or blend weights) is confirmed on a small sample first (same discipline used every time this session).
6. Once committed, ask a **fresh** push decision (never reuse a prior "yes"/"hold" — standing project convention), push if yes, then confirm the GitHub Actions "pages build and deployment" run for that commit shows `completed`/`success` (don't trust `curl -sI`/`last-modified` alone — confirmed unreliable in a prior session).

## Verification idioms used in this project (for the resuming session)

- Test suite: `cd bullion-live-map && python3 -m unittest discover -s tests && python3 -m unittest test_calibrate && python3 -m unittest scripts.test_generate_narration -v` (plain `python3`, no heavy deps — `41 + 33 + 22`) **and separately** `.venv-narration/bin/python3 -m unittest scripts.test_voice_blend -v` (needs torch/librosa/chatterbox — `7` tests, up from 5 this session).
- Real generation: `.venv-narration/bin/python3 scripts/generate_narration.py` — **never** plain `python3`. Takes roughly 10 minutes for all 45 clips.
- Spike/comparison only (does not touch production): `.venv-narration/bin/python3 scripts/spike_johnny_actor_blend.py` — writes `johnny_actor_4way_spike.wav` and `johnny_actor_90pct_spike.wav` under `audio/voice_sample/spike_output/` for A/B listening against production `johnny-fed.mp3`.
- **Audible correctness is never automatable in this project** — every voice/rate change ends in a real human listening pass (`afplay` or the live browser), never inferred from clean test runs or exit codes. Reconfirmed repeatedly this session across two rate iterations and two blend-weight iterations.
- Required macOS voices: `Jamie (Premium)` (`en_GB`) and `Tom (Enhanced)` (`en_US`) — unchanged this session, see prior handoff for install path.
- Reference clips: `bullion-live-map/audio/voice_sample/{user_voice.wav, tom_sample.wav, jamie_sample.wav, actor_sample.wav}` — first 3 committed (`635d053`); `actor_sample.wav` **not yet committed or negated** (see traps above).
- GitHub Pages deploy verification: `gh run list --repo SinbadTheExplorer/claudekit --limit 3`, check the run for the relevant commit shows `completed`/`success` — don't trust `curl -sI <pages-url>`/`last-modified` header timing alone.

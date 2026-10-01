# Bullion Narration Regen Complete + Caption/Map Overlap Fix — Session Handoff

**Written:** 2026-08-02 · **For:** any future session resuming this work — continues
directly from `bullion-review-fixes-audio-regen-handoff.md` (that session left the audio
regen at 54/100 clips and handed off with an explicit "resume the regen" instruction). This
session resumed and finished that regen (100/100), added a raw-WAV cache for Johnny to
speed up future tempo-only regens, shifted `bullion_mkultra.html`'s map + persona orb up to
reduce overlap with the narration caption bar, and pushed all of it on the user's explicit
override (no listening pass, no confirmed screenshot).

## Goal

Same broad effort as the prior two handoffs: ad-hoc review-driven polish of
`bullion_mkultra.html`'s narration system (Alfred/Johnny personas, captions, event-triggered
lines) — no spec/plan/SDD ledger exists for this thread of work, it's handled as direct
fixing, same posture as the sessions before it.

- Prior handoff (regen resumed from, 54/100 → this session): `bullion-review-fixes-audio-regen-handoff.md`
- Older handoff (items 1/2/3/6 of the original 8-item review list): `bullion-narration-ui-review-fixes-handoff.md`
  — this session archived it to `docs/superpowers/archive/` (see "Current state" below);
  still valid background, just no longer top-2-most-recent.
- No spec/plan/SDD ledger for this session's work either.

## How to resume (do this first)

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline
   a3a58e7..HEAD` should show exactly **2 commits, `f470c74` then `cfbe7fc`**, on `main`,
   already **pushed** (`git log --oneline origin/main..HEAD` empty). `git status --short`
   clean except the standing "Not mine" untracked noise (list below).
2. Read this handoff in full — it's self-contained. No ledger to cross-check against.
3. **Immediate next action:** get a real listening pass on the 46 clips this session
   generated/re-encoded (34 re-encoded `johnny-*.mp3` node clips + 11 new
   `johnny-event-*.mp3` clips) — this was explicitly skipped when pushing (see "What has
   failed / risks / caveats"). Second priority: confirm the caption-bar/map clearance fix
   actually works in a real browser (headless Chrome was unreliable all session — see below).

## Current state (active files)

**Branch:** `main`, HEAD at `cfbe7fc`, 2 commits ahead of the prior handoff's base
`a3a58e7` (`f470c74`, `cfbe7fc`), **already pushed**, clean tree (modulo standing untracked
noise below).

**Committed and pushed:**

- **`f470c74`** — `bullion-live-map/scripts/generate_narration.py` + `.gitignore`.
  `synthesize_johnny()` now persists the pre-atempo diffusion output to
  `audio/narration/raw_cache_johnny/<clip-stem>.wav` before the `ffmpeg atempo`+loudnorm
  encode. A cache hit skips `tts.generate()` (the expensive diffusion step) entirely. **Cache
  is keyed by output filename only, not content-hashed** — if a script's wording changes for
  an existing node/event id, the cache will silently serve the OLD audio at the new tempo
  unless you manually delete that id's cached `.wav`. `.gitignore` excludes the new cache
  dir (large, regeneratable, not shipped audio).
- **`cfbe7fc`** — three things in one commit:
  1. Finished the audio regen: 34 `johnny-*.mp3` node clips re-encoded + 11 new
     `johnny-event-*.mp3` clips generated, all at `ALFRED_RATE=213` / `JOHNNY_TEMPO=0.95` /
     `loudnorm=I=-20:TP=-2:LRA=7` (completing what `a3a58e7` left at 54/100). Alfred's side
     was already 100% done before this session.
  2. `bullion-live-map/bullion_mkultra.html`: `#stage` gained `margin-bottom: 112px`
     (started at 84px, bumped after a probe showed 84px left a 1px overlap — see caveats).
     Since `#persona-orb` is CSS-centered on `#stage` (`left:50%;top:50%`) and the Three.js
     renderer sizes off `stageEl.clientHeight` (which includes padding but not margin), this
     shrinks the render box and moves both the constellation sphere and the orb up together,
     without touching any JS.
  3. `bullion-live-map/scripts/regen_narration_v2.py` — committed for the first time (was
     untracked scratch driver in the prior two handoffs; the prior handoff explicitly left
     "should this be committed" as an open question — this session said yes, since it's
     proven useful twice and is the correct way to resume any future regen).

**Files later work will touch:**

- `bullion-live-map/audio/narration/raw_cache_johnny/` — does **not exist yet**. The regen
  that finished this session ran on the pre-`f470c74` code (started before the caching
  change landed), so the cache has never actually been exercised. The next session that runs
  any Johnny generation (via `generate_narration.py` or `regen_narration_v2.py`) will be the
  first real test of the caching behavior.

**Scratch workspace / traps:**

- ⚠️ **No listening pass happened on any of the 46 new/re-encoded clips.** Pushed on the
  user's explicit, informed "push all now" — the same one-time-override pattern the prior
  session used once already (this is the second time this project has done this). This is
  genuinely unverified audio in production right now.
- ⚠️ **The `112px` `#stage` margin is not confirmed by a screenshot or real measurement.**
  Headless Chrome was unreliable the entire session on this machine: repeated
  `SingletonLock` conflicts from leaked prior processes, apparent first-run/component-update
  network overhead on fresh `--user-data-dir` profiles, and — most importantly — **Chrome did
  not reliably exit on `--virtual-time-budget` while the WebGL `requestAnimationFrame` loop
  was active under `--headless=new`**, several probe invocations just hung indefinitely and
  had to be `pkill`ed. The `112px` number is a reasoned extrapolation from exactly ONE clean
  data point: an 84px margin left a **1px overlap** (`captionTop: 728` vs `stageBottom: 729`)
  for a synthetic ~120-char/2-line caption. `112px` = 84 + a 28px buffer, not a verified fit.
  Real caption text length varies widely (76 chars for `ai_analysis` up to 436 chars for the
  longest node script, `johnny-mortgage` — see `JOHNNY_SCRIPTS["mortgage"]` in
  `generate_narration.py`); the caption bar accumulates the FULL text by the end of playback
  (`startCaption()`'s `shown +=` logic in `bullion_mkultra.html`, don't assume only a
  partial/truncated line is ever visible), so the longest scripts could still brush the
  caption bar near the end of narration. **Not checked in a real browser.**
- ⚠️ If you retry the headless-Chrome probe idiom from
  `docs/superpowers/plans/2026-07-28-bullion-mkultra-experience.md`'s "Verification Harness":
  `pkill -f <your --user-data-dir path>` before each run (stale locks bit this session
  twice), and remember **macOS has no `timeout` command** — use the Bash tool's own
  `timeout` parameter, not a shell `timeout ...` wrapper (that silently no-ops as `command
  not found` and the whole invocation fails instantly with a 1-line log).
- Marker files `.regen_2026-08-02_v2_done.txt` (100/100 lines — the regen this session
  finished) and the older `.johnny_tempo90_done.txt` (from an even earlier session) are both
  untracked, both now inert/stale bookkeeping. Don't confuse either with an active driver or
  re-run anything based on their presence — the regen is genuinely done (see "What has
  changed").
- **Not mine — leave alone** (same standing list as every prior handoff, plus a few new
  untracked files spotted this session with unknown provenance — not created or touched by
  this session, just noting them so they're not mistaken for active work):
  `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`, `.codex/`,
  `.superpowers/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple),
  `bullion-live-map/__pycache__/`, `bullion-live-map/scripts/__pycache__/`,
  `bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`, the other tracked
  handoffs in `docs/superpowers/` (`honesty-pass-`, `mk12-`, `mkultra-spec2-brainstorm-`,
  `mkultra-spec2-plan-handoff.md`), and (new this session, untracked, not investigated):
  `docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md`,
  `docs/superpowers/plans/2026-07-30-bullion-ui-fixes.md`,
  `docs/superpowers/plans/2026-07-30-bullion-voice-narration-phase1.md`,
  `docs/superpowers/plans/2026-08-01-bullion-orb-translucency.md`,
  `docs/superpowers/plans/2026-08-01-bullion-persona-orb.md`,
  `docs/superpowers/specs/2026-08-01-bullion-persona-orb-design.md`. **Never `git add
  .`/`-A`** — this session staged only specific files/globs by name.

## What has changed

- Audio regen fully complete: 100/100 clips (78 node + 22 event, × Alfred/Johnny) at the
  corrected rate/tempo/loudnorm. `python3 -m unittest discover -s tests` → 41/41.
  `python3 -m unittest test_calibrate` → 33/33. `python3 -m unittest
  scripts.test_generate_narration -v` → **34/34** (the `test_every_event_johnny_clip_exists_and_nonempty`
  test that was an expected failure in the prior handoff now passes for real).
  `regen_narration_v2.py`'s own completion line printed: `"All 78 node clips + 22 event
  clips present."`
- Added Johnny raw-WAV caching (`f470c74`) so a future tempo-only change is cheap — see
  caveats above for its filename-keyed limitation.
- Shifted `#stage` (map + orb) up in `bullion_mkultra.html` to reduce caption-bar overlap —
  see caveats above for the unverified margin value.
- Committed the previously-untracked `regen_narration_v2.py` driver.
- Both commits pushed to `origin/main` (`cfbe7fc` is the current tip).

## What has failed / risks / caveats

- **Nothing has failed outright** — no fix was attempted and abandoned.
- **UNVERIFIED: the 46 new/re-encoded audio clips.** No listening pass. See "Scratch
  workspace / traps" above for the override context.
- **UNVERIFIED: the caption/map clearance fix.** No screenshot or real-browser confirmation.
  See "Scratch workspace / traps" above for why (headless Chrome instability this session).
- **Headless-Chrome verification is currently unreliable on this machine for this project**
  — budget real time/attempts for it, or investigate a more robust invocation (e.g. trying
  `--headless=old` instead of `--headless=new`, or an explicit process-group kill after a
  fixed wall-clock deadline) before trusting the existing plan-file idiom blindly. This is a
  new finding this session, not something noted in earlier handoffs.
- **Deploy status not checked** — no `curl` against the GitHub Actions API was run this
  session to confirm `cfbe7fc` actually deployed to Pages.

## What's next (ordered)

1. **Listening pass on the 46 new/re-encoded clips** — `cd bullion-live-map/audio/narration
   && afplay johnny-event-ai_analysis.mp3` (and the other 10 `johnny-event-*.mp3` files,
   plus spot-check a few of the 34 re-encoded `johnny-*.mp3` node clips). This is the single
   most important open item — audible correctness is never automatable in this project.
2. **Confirm the `#stage` margin-bottom:112px actually clears the caption bar for real** —
   open `bullion_mkultra.html` in an actual browser (not headless), click the "mortgage"
   node (longest Johnny script, 436 chars — the worst case), let narration play to the end,
   and watch whether the caption bar visually touches the sphere/orb. Adjust the margin
   value if it doesn't; it was never confirmed this session.
3. If a headless-Chrome recheck is preferred instead: `pkill -f <profile-dir>` first to
   clear any leaked lock, and don't wrap the Chrome invocation in a shell `timeout ...`
   command (macOS doesn't have one) — use the Bash tool's own timeout parameter.
4. **Deploy check** — `curl -s
   "https://api.github.com/repos/SinbadTheExplorer/claudekit/actions/runs?per_page=5"`
   and confirm the run for `cfbe7fc` shows `completed`/`success`.
5. Open follow-up idea (discussed, not started, not blocking): make the raw-WAV cache
   content-hash-keyed instead of filename-keyed, so an edited script auto-invalidates its
   own cache entry instead of silently going stale.

## Verification idioms used in this project (for the resuming session)

- Test suite: `cd bullion-live-map && python3 -m unittest discover -s tests &&
  python3 -m unittest test_calibrate && python3 -m unittest scripts.test_generate_narration
  -v` (plain `python3`).
- Real generation: `.venv-narration/bin/python3 bullion-live-map/scripts/regen_narration_v2.py`
  — resumable, marker-file-driven (`audio/narration/.regen_2026-08-02_v2_done.txt` — now
  complete/stale, a fresh regen for a NEW change would need a new marker file or that one
  cleared of the relevant entries), safe to kill and re-run at any point.
- Audible correctness is never automatable in this project — `afplay` or the live browser,
  never inferred from clean exit codes. This session's push was again a one-time, explicit,
  informed override, not a new standing practice — the default rule still applies next time.
- `git push` works directly from the Bash tool (`GIT_TERMINAL_PROMPT=0 git push origin
  main`); `gh` is NOT installed.
- Headless-Chrome DOM-probe recipe: see
  `docs/superpowers/plans/2026-07-28-bullion-mkultra-experience.md`'s "Verification Harness"
  section for the full reusable script. Treat it as unreliable on this machine right now
  (see caveats) rather than a guaranteed-to-work idiom.

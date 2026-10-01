# Bullion UI Fixes + Voice Narration Phase 1 — Execution Handoff

**Written:** 2026-07-31 (updated same day, after Task 2 finished) · **For:** any future
session resuming execution of two already-*approved* specs/plans: (1) scenario-highlighting
UI fix — **fully shipped and pushed, nothing left to do** — and (2) voice-narration Phase 1
(39-node coverage) — **Tasks 1 and 2 done, reviewed, and pushed; Task 3 (completeness
regression test, browser verification, final whole-plan review, final push) not started.**

## Goal

Execute (via `superpowers:subagent-driven-development`, direct-to-`main`, no
worktrees/branches — this project's established pattern, confirmed with the user) two specs
the prior handoff had designed but not built:
- Spec: `docs/superpowers/specs/2026-07-30-bullion-ui-fixes-design.md`
- Spec: `docs/superpowers/specs/2026-07-30-bullion-voice-narration-phase1-design.md`
- Plan: `docs/superpowers/plans/2026-07-30-bullion-ui-fixes.md` (all steps checked off, done)
- Plan: `docs/superpowers/plans/2026-07-30-bullion-voice-narration-phase1.md` (Tasks 1-2 done,
  checkboxes NOT yet marked `[x]` — do that once Task 3 finishes, matching the UI-fixes plan's
  convention)
- Progress ledger (voice narration Phase 1, **the authority on what's done — read this
  first**): `.superpowers/sdd/2026-07-30-bullion-voice-narration-phase1/progress.md`
- UI-fixes plan's SDD workspace was already deleted per the skill's finish step (plan fully
  done, git is the record) — don't look for it.
- Prior handoff (design/brainstorm phase — read only for design rationale, NOT execution
  state, which is entirely in this file):
  `docs/superpowers/mk18-ui-fixes-voice-phase1-handoff.md`

## How to resume (do this first)

1. Confirm branch/head: `git -C ~/claude-projects/claudekit log --oneline -5`
   should show `ceeb353` (voice Task 2) at HEAD on `main`, with `34f2dda`/`48dd496` (Task 1)
   and `c87b972` (UI-fixes plan, fully done) below it.
   `git rev-list --left-right --count origin/main...main` should read `0 0` — **everything
   through Task 2 is pushed and live, no uncommitted work, no background processes running.**
2. Read the ledger: `.superpowers/sdd/2026-07-30-bullion-voice-narration-phase1/progress.md`
   — it ends with an explicit "STOPPED HERE PER USER REQUEST" line; that's exactly where to
   pick up.
3. **Immediate next action:** start Task 3 of
   `docs/superpowers/plans/2026-07-30-bullion-voice-narration-phase1.md` — completeness
   regression test, browser verification of the 🔊 button across all 39 nodes in both HTML
   files, freeze-check, Python suite, then the plan's final whole-plan review (same pattern
   used for the UI-fixes plan — dispatch on the most capable model, point it at the ledger's
   deferred Minor items), then push and clean up the SDD workspace.

## Current state (active files)

**Branch:** `main`, working directly on it (no worktree/branch). Clean working tree — no
modified/staged tracked files (confirmed via `git status --short`, only the same pre-existing
untracked noise remains, see below). No `generate_narration.py` / `resume_narration.py`
processes running (confirmed via `ps aux`) — that whole saga (see "What has changed") is
finished and irrelevant now.

**Committed and pushed (UI-fixes plan, 100% done, nothing left):**
- `bullion-live-map/bullion_mk18.html`, `bullion-live-map/bullion_mkultra.html` — scenario
  highlighting. Commits `6d4bf33`, `3f5f939`, `c87b972`.

**Committed and pushed (voice-narration Phase 1, Tasks 1-2 done):**
- `bullion-live-map/scripts/generate_narration.py` +
  `bullion-live-map/scripts/test_generate_narration.py` — Task 1, commits `48dd496` +
  `34f2dda` (fix round: HTML-entity-unescaping bug). 6/6 tests pass.
- `bullion-live-map/audio/narration/node-*.mp3` — **all 39 present**, commit `ceeb353`.
  6 pilot clips (`fed`, `gold`, `repo`, `sec`, `vix`, `yield`) regenerated through the new
  pipeline, 33 new ones added. Verified: no duplicates, no empty files, uniform valid MP3
  encoding, manifest keys match filenames exactly in both HTML files (39/39, zero diff either
  direction — checked with a real JS parse of both files' `NODES` and `NARRATION_MANIFEST`,
  not regex).
- `bullion-live-map/bullion_mk18.html` / `bullion_mkultra.html` — `NARRATION_MANIFEST`
  expanded 6 → 39 entries in each (independently, same as the scenario-highlighting mirror
  pattern), same commit `ceeb353`.

**Not started (voice-narration Phase 1, Task 3):**
- Completeness regression test (assert every `NODES` id has a manifest entry, in both files)
  — not yet written.
- Browser verification of the 🔊 button across all 39 nodes in both files — not yet done for
  the full 39 (only spot-checked during Task 2's review via static/file-level checks, not a
  real browser pass).
- Manual listen-through spot-check (~6-8 clips) — **not done at all yet.** Per the Task 2
  reviewer's specific recommendation, prioritize at least one clip from each generation
  segment: `node-cftc` (from the original, uninterrupted run) and `node-mortgage` (from the
  resumed run) — the resumed clips' input text is attested only by a now-deleted scratch
  script, not by `generate_narration.py` itself under test, so this pairing is the cheapest
  check that would catch a resume-specific bug if one exists.
- Freeze-check (`mk11`-`mk17` byte-identical) and Python suite re-run — not yet re-run since
  Task 2 landed (should still be clean, nothing in Task 2 touches those files, but re-verify
  per the plan rather than assuming).
- Final whole-plan review for this plan (UI-fixes plan already got one, in `c87b972`'s
  history) — not started.
- Final push of Task 3's work, and SDD workspace cleanup
  (`.superpowers/sdd/2026-07-30-bullion-voice-narration-phase1/`) — not done.

**Not mine — leave alone:** same pre-existing untracked noise as always —
`docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`, `.codex/`,
`AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple), `bullion-live-map/__pycache__/`,
`bullion-live-map/scripts/__pycache__/`, `bullion-live-map/tests/__pycache__/`,
`docs/superpowers/archive/`, `docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md`.
**Never `git add .`/`-A`.**

**Scratch workspace / traps:**
- Several unrelated `python -m http.server` processes were found running on this machine
  during this session (ports 8765, 8888, 8899, 8912) with start times ranging from
  "Tue 12PM" to "21Jul26" — **none of these are from this session's work** (this session used
  port 8791, which is NOT currently running — already cleaned up). Don't assume any running
  `http.server` process is yours; check the port number and start time before touching one.
- The scratch resume driver from Task 2 (`resume_narration.py`, `gen.log`, `resume.log`, and
  related files under a session-specific `/private/tmp/claude-501/.../scratchpad/` path) is
  **fully done and no longer relevant** — the process exited cleanly (`RESUME_DONE` in its
  log), all 39 files are committed. No need to look for or trust anything under that
  scratchpad path anymore; it may not even still exist.
- If a fresh session ever needs to regenerate audio again (e.g., node text changes in a
  future edit), remember the two real infrastructure lessons from this effort: (1) any
  headless-Chrome probe must use stream-to-file + poll-for-marker + kill-the-process, NOT
  `subprocess.run(..., capture_output=True)` with `--dump-dom` (the latter hangs indefinitely
  on this machine's Chrome version, confirmed even on `about:blank`); (2) a long-running
  background TTS generation process may get killed by the harness partway through for reasons
  unrelated to the script itself — write any future generation driver to skip node ids whose
  output file already exists, so a resume is always cheap.

## What has changed

- **UI-fixes plan: 100% complete**, pushed. See prior version of this handoff or git log
  (`6d4bf33`, `3f5f939`, `c87b972`) for detail — nothing new to add here.
- **Voice-narration Phase 1, Task 1: complete, reviewed clean, pushed** (`48dd496`,
  `34f2dda`). `generate_narration.py` rewritten with `extract_node_texts`. Two real bugs
  found and fixed during implementation/review: the headless-Chrome `--dump-dom` hang (fixed
  with stream-to-file+poll+kill), and an HTML-entity-escaping bug in the `<title>` transport
  channel that could silently corrupt narration text containing `&`/`<`/`>`/nbsp (fixed with
  `html.unescape`, latent today since no current node text contains those characters).
- **Voice-narration Phase 1, Task 2: complete, reviewed clean, pushed** (`ceeb353`). Both
  manifests expanded to 39 entries; all 39 node MP3s generated. The generation run itself was
  killed mid-way by the harness at 22/39 clips (infrastructure limitation, not a script bug)
  and resumed via a scratch driver for the remaining 17 — the task reviewer independently
  corroborated via file-mtime ordering (strictly monotonic, exactly matching the interruption
  point, no gaps/duplicates) and audio-size-vs-source-text-length ratios (no truncation
  detected) that the result is indistinguishable from a clean single run. The implementer
  subagent never produced its own final report due to the repeated interruptions; the
  controller wrote the report and did final verification/commit directly — disclosed
  transparently to the reviewer, who treated it with the same "verify, don't trust" rigor as
  any other report and found nothing wrong.

## What has failed / risks / caveats

- **Nothing is currently broken or unverified for Tasks 1-2** — both fully reviewed clean,
  both pushed.
- **UNVERIFIED, carried into Task 3:** audible correctness of any individual narration clip.
  No one has listened to any of the 39 clips yet — Task 3's manual listen-through step is the
  first time this gets checked by ear, and per the Task 2 reviewer's recommendation, should
  prioritize one clip from each generation segment (`node-cftc`, `node-mortgage`) since the
  resumed segment's correctness rests on indirect evidence (timestamps, size ratios) rather
  than a script-under-test.
- **UNVERIFIED, carried into Task 3:** whether Chatterbox's known non-determinism produced
  audibly different output for the 6 regenerated pilot clips vs. their original pilot-era
  audio. The user already accepted this risk during brainstorming (chose "regenerate all 39"
  over "leave the 6 pilot clips untouched"), so this is not a blocker — just something a
  fresh session shouldn't be surprised by if the `fed`/`gold`/`repo`/`sec`/`vix`/`yield` clips
  sound slightly different from what shipped in the original pilot.
- Two Minor findings deferred from Task 2's review, neither blocking: untracked
  `__pycache__` byproducts under `bullion-live-map/` and `bullion-live-map/scripts/` (correctly
  not staged, could use a `.gitignore` entry eventually); a comment-wrapping nit at
  `bullion_mk18.html:3319-3321`.
- Several Minor findings deferred from Task 1's review (file-handle leak on a rare
  early-exception path in `generate_narration.py`, decoy-`</html>`-ordering fragility in the
  fast-fail check, missing regression test coverage for the `RuntimeError` paths themselves,
  exception-chaining omission) — all still open, all still Minor, carry them to this plan's
  final whole-plan review same as the UI-fixes plan's final review triaged its own deferred
  list.

## What's next (ordered)

1. Read `docs/superpowers/plans/2026-07-30-bullion-voice-narration-phase1.md`, Task 3, in
   full — it specifies the completeness test code, the browser verification approach, and the
   exact freeze-check/Python-suite commands.
2. Dispatch Task 3 via `subagent-driven-development` (fresh implementer, model per this
   session's established choice of `opus`) — same pattern as every prior task this session.
   BASE for the review package is `ceeb353` (Task 2's head).
3. Task reviewer, then push once clean.
4. Dispatch this plan's final whole-plan review (most capable model), pointing it at the
   deferred Minor list above (from both Task 1 and Task 2) so it can triage what — if
   anything — needs fixing before considering the plan done, same as the UI-fixes plan's
   final review found and fixed one Important issue (dropdown contrast) via exactly this
   mechanism.
5. Once the final review is clean (after at most one fix wave + one scoped re-review, per the
   skill), push, then delete
   `.superpowers/sdd/2026-07-30-bullion-voice-narration-phase1/` (git is the record after
   that) and mark all of the plan's checkboxes `[x]`
   (`sed -i '' 's/- \[ \]/- [x]/g' docs/superpowers/plans/2026-07-30-bullion-voice-narration-phase1.md`),
   matching what was done for the UI-fixes plan.
6. Only after this plan is fully done: Phase 2 (link/relationship-row narration) starts from
   scratch design-wise, per the Phase 1 spec's explicit note — begin with the brainstorming
   skill, nothing about Phase 2 is decided yet (no call sites, no manifest-key scheme, no
   button placement).

## Verification idioms used in this project (for the resuming session)

- Headless Chrome probes: **stream-to-file + poll-for-marker + kill-the-process**, NOT
  `subprocess.run(..., capture_output=True)` with `--dump-dom` (hangs indefinitely on this
  machine regardless of page content — see `generate_narration.py`'s `extract_node_texts` for
  the working pattern). Always an isolated `--user-data-dir`; inject probe script before the
  LAST `</body>` via `str.rfind` (decoy `</body>` inside a JS string mid-file); NEVER call
  `openAuditLog()` in a probe (stalls headless virtual-time → hang).
- `file://` URLs don't work with the claude-in-chrome browser tool — serve locally:
  `cd bullion-live-map && python3 -m http.server <port>`, navigate to
  `http://localhost:<port>/bullion_mk18.html`. Check `lsof -i :<port>` before starting a
  second server, and check the process's actual start time/args before assuming any running
  `http.server` is yours — this machine accumulates long-lived stray ones from other sessions.
- Pixel-coordinate clicks near `mkultra.html`'s 3D WebGL globe are unreliable — one real
  coordinate click anywhere safe first to establish user-activation, then
  `document.querySelector(...).click()` via the JS tool for the actual target.
- Freeze-check: `shasum -a 256 bullion_mk11.html … bullion_mk17.html`, compare against
  `git show ceeb353:bullion-live-map/bullion_mk<N>.html | shasum -a 256`.
- Python suite: `cd bullion-live-map && python3 -m unittest discover -s tests &&
  python3 -m unittest test_calibrate` → 41/41 + 33/33 as of last check. Narration script's own
  tests: `source .venv-narration/bin/activate && python3 -m unittest
  scripts.test_generate_narration -v` → 6/6 as of `34f2dda`.
- Manifest/node-id cross-checks are more reliable done via a real JS parse (`node -e` or
  headless-Chrome eval of the actual `NODES`/`NARRATION_MANIFEST` objects) than via regex —
  regex-based line extraction produced false mismatches during this session's own
  verification due to whitespace/formatting assumptions that didn't hold.
- `git push origin main` works directly via Bash (`GIT_TERMINAL_PROMPT=0 git push origin
  main`); no `gh` CLI installed.
- This session's SDD execution used `subagent-driven-development` throughout, dispatching
  fresh implementer/reviewer subagents per task on the `opus` model (user explicitly
  authorized Opus). Continue that pattern for Task 3 unless told otherwise.

# Bullion Voice Narration — Persona Toggle Implementation — Session Handoff

**Written:** 2026-08-01 · **For:** any future session resuming this plan — Tasks 1-5 are
done, merged, and pushed; Tasks 6-7 remain. Supersedes the previous version of this same
file (Tasks 1-3 only, mid-fix-loop) — that content is now stale, everything it describes
is finished and merged.

## Goal

Ship the `say`-CLI British-voice engine swap together with a two-persona narration
system — "Alfred" (butler, factual text, all 39 nodes) and "Johnny" (rocker, hand-written
text, 6 pilot nodes) — plus a global toggle, synced captions, and session-scoped
autoplay, on the Bullion financial map (`bullion-live-map/bullion_mk18.html` and
`bullion_mkultra.html`).

- Spec: `docs/superpowers/specs/2026-07-31-bullion-voice-persona-toggle-design.md`
- Plan: `docs/superpowers/plans/2026-07-31-bullion-voice-persona-toggle.md` (7 tasks)
- Progress ledger (recovery map — **trust this over this handoff's prose if they ever
  disagree**): `.superpowers/sdd/2026-07-31-bullion-voice-persona-toggle/progress.md`
  in the main checkout. **A second, separate ledger exists** at the same relative path
  inside the worktree (see "Current state" below) — read both if resuming
  mid-parallel-work; only the main checkout's ledger is authoritative once everything is
  merged.
- Prior handoffs (read only for history — brainstorming session that produced the spec,
  and this file's own prior revision covering only Tasks 1-3 mid-flight): archived or
  superseded, not needed to resume — everything relevant is in this file and the ledger.

## How to resume (do this first)

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline -5`
   should show `21cc1ea` (merge commit) at HEAD on `main`. `git rev-list --left-right
   --count origin/main...main` should read `0 0` — **fully pushed, nothing local-only.**
   `git status --short` should show only the usual pre-existing untracked noise (see
   "Not mine" below).
2. Read the main checkout's ledger in full — it's the authoritative record of Tasks
   1-3 and the merge.
3. **Check whether a second Claude Code session is still active** in the worktree at
   `~/claude-projects/claudekit/.claude/worktrees/bullion-persona-toggle-frontend`
   (branch `worktree-bullion-persona-toggle-frontend`) — it may still be working on Task
   6. If that session is gone/idle, this session should pick up Task 6 itself (either in
   that same worktree, or directly on `main` — worktree isolation no longer matters much
   now that Tasks 1-3 are merged and Task 6 is HTML-only, same as before).
4. Re-invoke `superpowers:subagent-driven-development` to continue.
5. **Immediate next action:** dispatch Task 6 (session-scoped autoplay) — read the brief
   with `scripts/task-brief docs/superpowers/plans/2026-07-31-bullion-voice-persona-toggle.md 6`
   from the subagent-driven-development skill directory, either from the worktree (if
   continuing there) or `main` directly (simpler now — no other stream to isolate from).

## Current state (active files)

**Branch:** `main`, at `21cc1ea`, fully pushed (`origin/main` matches exactly).

**This was executed as two parallel streams that have now merged:**
- **Stream A** (this session, main checkout): Tasks 1 (engine swap to `say`), 2 (Johnny
  generation), 3 (Johnny/JS-Python sync tests). All complete, reviewed clean, merged
  as part of normal linear history on `main`.
- **Stream B** (a separate concurrent Claude Code session, in the worktree at
  `.claude/worktrees/bullion-persona-toggle-frontend`): Tasks 4 (persona toggle +
  `JOHNNY_MANIFEST`/`JOHNNY_SCRIPTS`), 5 (captions). Both complete, reviewed clean
  (1 fix round on Task 5), merged into `main` via merge commit `21cc1ea`.
- **Task 6 (autoplay)** was NOT done by either stream as of this handoff — it belongs to
  Stream B's scope but hadn't been dispatched yet.
- **Task 7 (final regression + push decision)** not started — needs Task 6 done first.

**Files created / changed (all committed and merged):**
- `bullion-live-map/scripts/generate_narration.py` — Chatterbox fully replaced by
  `say -v "Jamie (Premium)"` + ffmpeg. `ALFRED_RATE = 240`, `JOHNNY_RATE = 225` (both
  human-confirmed by ear — **differ from the plan document's original placeholder
  values of 200 and 170**; the plan text itself was never updated, treat the shipped
  code as authoritative on these two numbers). `_voice_installed()` gates `main()`
  before any generation (fail-loud if the voice is missing). `JOHNNY_SCRIPTS` dict (6
  pilot scripts, Cyberpunk Johnny Silverhand register).
- `bullion-live-map/scripts/test_generate_narration.py` — `TestVoiceInstallationCheck`
  (5 tests) and `TestJohnnyPersona` (7 tests, including cross-checking the JS-embedded
  copies of `JOHNNY_MANIFEST`/`JOHNNY_SCRIPTS` in both HTML files against the Python
  dict). **All 22 tests pass as of `21cc1ea`** (they were briefly, correctly red for the
  4 cross-file checks between Task 3 landing and Task 4 merging — that's resolved now).
- `bullion-live-map/audio/narration/node-*.mp3` (39) and `johnny-*.mp3` (6) — all
  regenerated via `say`, present and non-empty.
- `bullion-live-map/bullion_mk18.html` / `bullion_mkultra.html` — both now have:
  persona-toggle button (`#persona-toggle-btn`, `localStorage`-persisted), `JOHNNY_MANIFEST`
  + `JOHNNY_SCRIPTS` (JS copies, byte-identical to Python's — tested), `resolveNarration`/
  `playCurrentNarration` (persona resolution + Alfred-fallback for the 33 non-piloted
  nodes), caption box (`#detail-caption`) with character-count-proportional word timing,
  `clearCaption()` wired into both `openDetail()` (fixes a mid-playback leak found in
  Task 5's review) and implicitly via `playNarration`'s own guard.
- **NOT yet present in either HTML file:** autoplay-on-first-open (`sessionStorage`
  tracking) — this is Task 6, still to do.

**Scratch workspace / traps:**
- ⚠️ **Rate values in the plan document are stale.** `docs/superpowers/plans/2026-07-31-bullion-voice-persona-toggle.md`
  still says `ALFRED_RATE = 200` and `JOHNNY_RATE = 170` in its prose — the actual
  shipped values are 240 and 225 respectively, confirmed by ear across several rounds of
  A/B testing. Don't "fix" the code to match the plan; the plan's prose was simply never
  updated after the fact.
- ⚠️ **A "Thamie" voice-blend idea was raised and explicitly deferred, not started** —
  blending the user's own cloned reference voice with the `say`-CLI Jamie voice into a
  new persona. Separate future project, not part of this plan. Full context in memory:
  `bullion-thamie-voice-blend-idea.md`.
- ⚠️ **An early, since-reverted merge incident happened during Task 4.** Its implementer
  subagent worked from the main checkout instead of its assigned worktree and committed
  directly onto `main` (`ef12334`); Stream B's session recovered by cherry-picking the
  same content onto its own branch (`a29b4b9`) and reverting the stray commit on `main`
  (`891d25c`) with the user's approval. Fully resolved — `main`'s history has an
  add-then-revert pair for this reason, which is harmless but may look odd in `git log`.
  Full account in the worktree's ledger (see below).
- ⚠️ **Two separate SDD ledgers exist** (main checkout's and the worktree's) because
  `.superpowers/` is untracked and per-working-directory — they were never meant to be
  the same file. The worktree's ledger at
  `.claude/worktrees/bullion-persona-toggle-frontend/.superpowers/sdd/2026-07-31-bullion-voice-persona-toggle/progress.md`
  has the full Task 4/5 review history and a post-merge browser-verification note (Chrome
  MCP confirmed 0 console errors, correct persona resolution, and correct Alfred fallback
  in both files — but could NOT confirm real-time audio playback/caption sync because
  automated browser tabs report `document.visibilityState:"hidden"`, which throttles
  actual audio loading; this needs a real user with a focused tab, same limitation as
  every prior audio-quality check in this project).
- ⚠️ **Deferred Minor findings, not yet fixed, for the eventual Task 7 / final
  whole-branch review to triage:** (1) unused `sys` import in `generate_narration.py`,
  (2) the `ffmpeg` subprocess call isn't wrapped to raise `RuntimeError` the way `say` is
  (still fails loudly via `CalledProcessError`, just an inconsistent exception type), (3)
  `_voice_installed()`'s docstring claims it raises `RuntimeError` on query failure but
  the `say -v '?'` call isn't wrapped either (same class of issue as #2), (4) missing
  inline comment on `JOHNNY_RATE` explaining how 225 was chosen, (5) one extra blank line
  near `main()`. None of these block anything; none have been fixed.

**Not mine — leave alone:** the standing pre-existing untracked noise —
`docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/` (note: now also
contains the live worktree under `.claude/worktrees/`, which IS meaningful, unlike the
rest of `.claude/` — don't delete it if Task 6 is still in flight there), `.agents/`,
`.codex/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple), `bullion-live-map/__pycache__/`,
`bullion-live-map/scripts/__pycache__/`, `bullion-live-map/tests/__pycache__/`,
`docs/superpowers/archive/`, `docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md`,
`docs/superpowers/plans/2026-07-30-bullion-ui-fixes.md`,
`docs/superpowers/plans/2026-07-30-bullion-voice-narration-phase1.md`. **Never
`git add .`/`-A`.**

## What has changed

- Tasks 1-5 fully implemented, reviewed (2 fix rounds total, both resolved clean), merged
  into `main` (`21cc1ea`), and pushed to `origin/main`.
- Full Python suite green: 41 (tests/) + 33 (test_calibrate) + 22 (scripts.test_generate_narration).
- Front-end manually spot-checked via Chrome MCP (console-clean, correct persona
  resolution/fallback logic) but NOT yet audibly/visually confirmed by a real human for
  Tasks 4-5's UI (captions, toggle) — worth a real click-through before calling the whole
  feature done, even though the code-level checks all passed.

## What has failed / risks / caveats

- **Nothing has failed as shipped code.** The Task 4 stray-commit incident was caught and
  cleanly reverted, not a lingering defect.
- **UNVERIFIED by a real human:** does the caption timing actually look right, does the
  persona toggle feel good in real use, does Johnny's audio actually sound like the
  intended rocker delivery in context (only isolated clips were confirmed by ear, not the
  full in-page experience with captions). Automation confirmed the mechanics (correct
  file resolution, no console errors) but not the "does this feel right" audible/visual
  judgment this project always defers to a human for.
- Task 6 is unstarted; Task 7 (full regression pass) is unstarted — its "push decision"
  half is moot for the Task 1-5 merge specifically (see below) but still applies to
  whatever Task 6 produces.
- **The Task 1-5 merge (`21cc1ea`) has been pushed to origin, with the user's explicit
  go-ahead.** Sequence, for the record: Stream B's session first asked the user "push to
  main?" and got a scoped answer (push only what was on `main` at the time — Stream A's
  Tasks 1-3, not yet including the Stream B merge); separately asked before merging
  Stream A + Stream B together ("merge both sessions?"); then, once merged, explicitly
  asked "push this merge?" and the user said yes in so many words. All three asks and
  answers are in that session's transcript. Nothing here needs re-confirming — it's
  fully authorized and done. Task 6's eventual commits will still need their own,
  separate push decision.

## What's next (ordered)

1. Determine whether Stream B's session is still active (check for recent worktree
   activity / ask the user). If active, let it continue Task 6. If not, pick up Task 6
   yourself — brief at `scripts/task-brief <plan> 6`.
2. Task 6: session-scoped autoplay (`sessionStorage`-tracked, first-open-per-session),
   both HTML files. Standard implement → review → fix-loop-if-needed → complete.
3. Once Task 6 is merged/complete, do Task 7: full Python suite run, full manual
   click-through in real Chrome for BOTH files (this is the point to finally get a real
   human's audible/visual confirmation on captions and Johnny's in-context delivery, not
   just isolated clips), then ask the user about pushing (even though the Task 1-5 merge
   is already pushed, Task 6's commits will need their own push decision).
4. Before or during Task 7, triage the 5 deferred Minor findings listed above — fix
   what's cheap, consciously leave the rest.
5. Once Task 7 passes, this plan is done. Consider cleaning up the worktree
   (`ExitWorktree` with `action: "remove"` if the other session is finished with it) and
   deleting the SDD workspace directories per the skill's normal "Finish" step.

## Verification idioms used in this project (for the resuming session)

- Test suite: `cd bullion-live-map && python3 -m unittest scripts.test_generate_narration -v`
  (currently 22/22). Full project suite:
  `python3 -m unittest discover -s tests && python3 -m unittest test_calibrate` (41 + 33).
  **Watch for transient headless-Chrome flakiness** (`extract_node_texts` occasionally
  gets SIGKILL'd — exit code -9 — under system load, especially if multiple subagents
  are running concurrently). A single test failing with "Probe script never ran... chrome
  exit code: -9" is very likely transient — re-run before treating it as a real
  regression (confirmed this pattern directly this session: the same test flipped
  pass/fail across 3 consecutive runs with no code changes in between).
- Audible correctness and now also caption-sync/toggle-feel **cannot be automated** —
  every such check is an explicit controller-driven step using `afplay <path>` plus
  asking the actual human, or acknowledging Chrome MCP's real limitation (throttled
  audio in non-focused automated tabs) rather than pretending it verified something it
  didn't.
- SDD process idioms: this plan's ledger(s) are the recovery map — trust them and
  `git log` over any session's memory. Task briefs/reports/review-packages live in
  `.superpowers/sdd/2026-07-31-bullion-voice-persona-toggle/` (per working directory —
  main checkout and worktree each have their own copy).

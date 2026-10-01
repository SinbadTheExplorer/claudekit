# Bullion Voice Narration — Persona Toggle (Tasks 6-7) + Persona Orb Redesign — Session Handoff

**Written:** 2026-08-01 · **For:** any future session resuming this work — Task 6 of the
persona-toggle plan is done (unpushed); Task 7 is blocked on a real voice-quality complaint,
not a checklist item; and a brand-new, unrelated-in-scope "persona orb" UI redesign was
brainstormed mid-session but not yet spec'd. Supersedes
`bullion-voice-persona-toggle-implementation-handoff.md` (Tasks 1-5 only) — that content is
now stale/complete; read this file instead. That prior file is kept as the second-most-recent
handoff; read it only if you need the Tasks 1-5 merge history in detail.

## Goal

Two goals, now tangled together (see "Sequencing" below):

1. **Ship the original 7-task plan**: `say`-CLI voice engine + Alfred/Johnny persona toggle +
   captions + autoplay on the Bullion financial map (`bullion-live-map/bullion_mk18.html` and
   `bullion_mkultra.html`). Tasks 1-6 are code-complete; Task 7 (final regression + push) is
   blocked on the user's own listening test.
   - Plan: `docs/superpowers/plans/2026-07-31-bullion-voice-persona-toggle.md` (7 tasks)
   - Progress ledger (recovery map — **trust this over this handoff's prose if they ever
     disagree**): `.superpowers/sdd/2026-07-31-bullion-voice-persona-toggle/progress.md`
2. **New, mid-session follow-on**: replace the small header persona-toggle button with a
   persistent "persona orb" (bottom-right corner, both files) that idle-breathes and
   pulses per spoken word during narration. This has NOT been written to a spec file yet —
   no `docs/superpowers/specs/...` file exists for it. All decisions below live only in this
   handoff and the visual-companion mockup files until a spec is written.

## How to resume (do this first)

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline -3`
   should show `bd4012d` (Task 6) at HEAD on `main`, one commit past `21cc1ea` (the Tasks
   1-5 merge). `git rev-list --left-right --count origin/main...main` should read `0 1` —
   **one commit ahead of origin, not yet pushed** (deliberate — user said hold). `git status
   --short` should show only the usual pre-existing untracked noise (see "Not mine" below).
2. Read the ledger in full: `.superpowers/sdd/2026-07-31-bullion-voice-persona-toggle/progress.md`
   — it has the complete Task 1-6 history plus Task 7's partial results appended at the end.
3. **Immediate next action:** this session is blocked on a real product question, not a
   mechanical one — see "What has failed" below. Do NOT just re-tune TTS rates again or
   re-run the regression pass; the user's complaint is about the `say`-CLI approach itself.
   Bring up superpowers:brainstorming with the user to figure out what to do about voice
   quality BEFORE touching Task 7 further, and separately ask them whether to resume the
   orb design work (not yet spec'd) independently of that, or wait — see "Sequencing" note.

## Current state (active files)

**Branch:** `main`, 1 commit ahead of `origin/main` (`bd4012d`), not pushed.

**Files created/changed, committed in `bd4012d` (Task 6):**
- `bullion-live-map/bullion_mk18.html` — added `maybeAutoplayNarration(d)` + one-line call
  in `openDetail()`.
- `bullion-live-map/bullion_mkultra.html` — identical change.
- (Tasks 1-5's files — `generate_narration.py`, `test_generate_narration.py`, both HTML
  files' earlier edits, all `audio/narration/*.mp3` — were already committed in `21cc1ea`
  and pushed; unchanged this session.)

**Files the orb redesign will touch (untouched so far — no code written yet):**
- `bullion-live-map/bullion_mk18.html` / `bullion_mkultra.html` — will remove
  `persona-toggle-btn` from the header, add a new `#persona-orb` element + CSS + JS hooks
  into `startCaption()`/`clearCaption()`. See "Orb design decisions" below for the exact
  shape these edits should take once a spec exists.

**Scratch workspace / traps:**
- ⚠️ **Visual-companion server may still be running.** Started this session at
  `.superpowers/brainstorm/66555-1785520603/` (project-dir mode), port `63035`. Check
  `.superpowers/brainstorm/66555-1785520603/state/server-info` exists and no
  `server-stopped` marker sits beside it — if it's still up and you don't need it, stop it
  with `scripts/stop-server.sh .superpowers/brainstorm/66555-1785520603` (path from the
  `superpowers:brainstorming` skill dir) rather than leaving it orphaned. If you DO need it
  (resuming the orb brainstorm), it reuses the same port on restart, so the user's old tab
  reconnects — no new URL needed. Mockup screens already on disk under
  `.../66555-1785520603/content/`: `orb-style.html` (idle/active pulse + color direction,
  approved), `orb-icons.html` (Johnny=👹 vs Alfred icon options, approved), plus two
  `waiting*.html` filler screens. These are historical record, not living code.
- ⚠️ **The worktree at `.claude/worktrees/bullion-persona-toggle-frontend` (branch
  `worktree-bullion-persona-toggle-frontend`) is stale and unused this session** — still
  sitting at `2fd6a32` (its state as of the Tasks 1-5 merge). Task 6 was done directly on
  `main` per the prior handoff's own suggestion once Tasks 1-5 were merged, so this worktree
  was never touched. Probably safe to remove (`ExitWorktree` / `git worktree remove`) once
  the user confirms they're done with it, but that's their call — don't delete unilaterally.
- ⚠️ **One self-inflicted test artifact from this session, already resolved, don't
  rediscover it as a mystery:** while mechanically verifying Task 6 via claude-in-chrome, an
  instrumented `playCurrentNarration` wrapper was re-wrapped on top of itself across two REPL
  calls without an intervening page reload, causing a false "called twice" reading. Re-ran
  with a single fresh wrap after reloading and confirmed exactly one call — not a real
  product bug, just a test-harness mistake.
- ⚠️ **Two untracked handoff files existed before this one** —
  `bullion-voice-persona-toggle-implementation-handoff.md` (kept, this file supersedes it)
  and `bullion-voice-persona-toggle-brainstorm-handoff.md` (older, now moved to
  `docs/superpowers/archive/` per the write-skill's 2-most-recent rule — it was untracked,
  so archiving instead of deleting was safe).

**Not mine — leave alone:** the standing pre-existing untracked noise —
`docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/` (still also contains the
stale worktree under `.claude/worktrees/`, see above), `.agents/`, `.codex/`, `AGENTS.md`,
`CLAUDE.md`, `.DS_Store` (multiple), `bullion-live-map/__pycache__/`,
`bullion-live-map/scripts/__pycache__/`, `bullion-live-map/tests/__pycache__/`,
`docs/superpowers/archive/`, `docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md`,
`docs/superpowers/plans/2026-07-30-bullion-ui-fixes.md`,
`docs/superpowers/plans/2026-07-30-bullion-voice-narration-phase1.md`. **Never
`git add .`/`-A`.**

## What has changed

- **Task 6 (session-scoped autoplay): complete.** Implemented by a haiku implementer per
  `superpowers:subagent-driven-development`, reviewed clean (0 Critical/Important; 2 Minor
  deferred — an unguarded `sessionStorage.setItem` matching the pattern of adjacent
  newer code, and autoplay "seen" tracking being persona-agnostic by design per the brief).
  Committed as `bd4012d`. Full ledger entry has the details.
- **Task 7, Step 1 (full Python suite): done, green.** 96/96 — 41 (`tests/`) + 33
  (`test_calibrate`) + 22 (`scripts.test_generate_narration`), including every
  `TestJohnnyPersona` cross-file test.
- **Task 7, Step 2, mechanical portion: done** (controller-verified via claude-in-chrome
  against a local server on both HTML files): 0 console errors on fresh load in both;
  autoplay fires exactly once per node per session and the "seen" list survives a reload;
  persona toggle flips label/highlight and persists via `localStorage` across reload
  (screenshot-confirmed); `resolveNarration` correctly resolves Johnny's clip for a piloted
  node and falls back to Alfred for a non-piloted one (e.g. `cftc`).
- **New orb design: brainstormed through 8 sections, 4 explicitly approved by the user in
  the terminal, the remaining 4 presented but not yet confirmed** (see "Orb design
  decisions" below — treat as directionally solid but not signed off).

## What has failed / risks / caveats

- **Task 7, Step 2's real audible check FAILED — this is the actual blocker, not a
  checklist gap.** The user explicitly said: *"I am not yet satisfied with the voice
  really."* Asked to narrow it down (Alfred specifically / Johnny specifically / the whole
  approach), they said **"Both / the whole say-CLI approach"** — the underlying macOS `say`
  TTS engine sounds too robotic/synthetic for either persona. This is NOT a rate-tuning
  complaint (Tasks 1-2 already did careful by-ear A/B rate selection: Alfred settled at 240,
  Johnny at 225) — it's a complaint about the engine choice itself.
  - **Do not respond to this by re-tuning rates again.** That was already tried and isn't
    the issue.
  - **Relevant prior context, already in project memory** (`bullion-thamie-voice-blend-idea.md`):
    a "Thamie" voice-blend idea — blending the user's own cloned reference voice with
    `say`-CLI's Jamie voice into a new persona — was raised earlier this project and
    explicitly deferred as a separate future project, not started. This complaint may be
    the trigger to revisit that, or some other TTS approach entirely.
  - **Going back to the original engine isn't a free win either**: the very first engine
    (Chatterbox voice cloning) was replaced specifically because the user found it had "the
    wrong accent" (see the project memory's Task 1 history). Both prior engines have now
    drawn a real complaint — this needs a genuine design conversation
    (`superpowers:brainstorming`), not a mechanical fix.
- **Task 7, Step 3 (push decision): user said HOLD.** `bd4012d` stays local-only until they
  say otherwise. Do not push without a fresh, explicit yes — a prior "yes" for the Tasks 1-5
  merge does not carry forward to this commit.
- **UNVERIFIED, carried forward unchanged from the prior handoff:** whether captions read
  naturally in sync with real speech and whether Johnny's in-context delivery lands right —
  moot in one sense now (the user has already found the voice itself unsatisfying at a more
  fundamental level), but worth re-checking against whatever engine is eventually chosen.
- **Nothing about Task 6's own code has failed** — the autoplay logic itself is sound and
  reviewed clean. The complaint is about voice quality, unrelated to Task 6's actual
  deliverable.

## Orb design decisions (brainstormed, NOT yet spec'd — treat as a strong draft)

This is new scope, not in the original 7-task plan. The user asked mid-session for a more
noticeable persona indicator, which grew into a full redesign via `superpowers:brainstorming`
and the visual companion. **Sections 1-4 below were each individually confirmed by the user
in the terminal ("yep" / "good"). Sections 5-8 were presented together in one message but the
user redirected to this handoff before confirming that batch — re-surface them before writing
the spec.**

1. **Overview (confirmed):** replace the small header `persona-toggle-btn` with a persistent
   floating orb, bottom-right corner, present identically in both `bullion_mk18.html` and
   `bullion_mkultra.html`. Always visible; shows the active persona's name/icon/color; breathes
   gently at rest; pulses strongly per spoken word during narration; click toggles persona.
   Default persona stays Alfred (unchanged — reconfirmed mid-brainstorm despite Johnny's new
   visual prominence, because Alfred covers all 39 nodes and Johnny only 6).
2. **Orb component (confirmed):** static markup near `#legend-box`:
   ```html
   <div id="persona-orb" title="Switch narration voice">
     <div class="orb-core"></div>
     <div class="orb-label">Alfred</div>
   </div>
   ```
   Two CSS states: `.idle` (slow ~3.6s breathing glow, always running, matching the existing
   `hubPulse` animation's visual language — not a new animation idiom) and `.active` (a sharp
   pulse triggered once per revealed word, NOT a fixed-interval loop).
3. **Icons/colors (confirmed):** Johnny = 👹 (Japanese Oni emoji) on a red gradient (reuses
   the existing `--red: #e0654f` token). Alfred = 🎩 (top hat emoji) on a **new** blue
   gradient not yet in the palette (mockup used roughly `#9fc6f5`/`#4d7fb8`/`#24425e` — add a
   `--blue` token to the existing `:root` palette alongside `--gold`/`--red`/`--green`,
   following the same naming convention). A hand-drawn custom-SVG "simplified butler face"
   (monocle + mustache) alternative was mocked and shown but explicitly NOT chosen — the
   user picked the plain top-hat emoji, keeping this project's existing plain-Unicode-glyph
   icon convention (matches 🎤/⚙/◉ used elsewhere) rather than introducing hand-drawn icon art.
4. **Placement & panel-open repositioning (confirmed):** `#persona-orb` is `position: fixed;
   right: 18px; bottom: 18px; z-index: 15` (above the map/legend, below the detail panel's
   `z-index: 20`). **Real conflict found and resolved during brainstorming:** the detail
   panel is `position: fixed; right: 0; height: 100%; width: min(380px, 92vw)` when open, which
   would otherwise sit directly on top of the orb's corner — precisely when narration is
   playing. Fix: when `#app.panel-open` is active, a CSS rule shifts the orb left by the
   panel's width (`min(380px, 92vw)`), the same value the existing `#stage` shift-left rule
   already uses for the identical reason. Slides back on close. Applies identically in both
   files.
5. **Interaction & narration sync (presented, NOT yet confirmed):** click toggles
   `narrationPersona` (same state/`localStorage` key Task 4 already established) — swaps
   icon/color/label, no effect on idle/active motion. Narration sync reuses Task 5's
   *existing* per-word `setTimeout` schedule inside `startCaption()` rather than building a
   second timer system — add one line per word to trigger a pulse (add a `.pulse` class,
   force reflow, remove it — standard CSS retrigger). Orb enters `.active` when
   `startCaption()` begins, returns to `.idle` exactly when `clearCaption()` fires (panel
   close, new narration starting, or natural end) — one single source of truth for "is
   anything narrating," not a parallel state machine.
6. **First-visit nudge (presented, NOT yet confirmed):** user said yes to this. A one-time
   ring-pulse reusing the existing `toolsPulse` keyframe pattern verbatim, plus a small
   tooltip ("Tap to switch narrator voice"), gated by a `sessionStorage` flag matching the
   existing `mode-toggle-btn.tools-ready` progressive-disclosure convention, dismissed on
   first orb click or first narration (whichever comes first).
7. **Removal & files touched (presented, NOT yet confirmed):** `persona-toggle-btn` and its
   click handler removed from the header in both files; `applyPersonaToggle()` repurposed to
   update the orb instead of the old button. Same two files as every prior task in this
   plan. No Python/backend changes — pure front-end.
8. **Testing (presented, NOT yet confirmed):** no new automated tests (same category as
   Tasks 4-6 — pure UI/CSS/animation). Verification follows the Task 6 pattern: mechanical
   checks via Chrome (console-clean, click toggles state, pulse-trigger fires once per word,
   panel-open repositioning happens, nudge shows once then never again), but whether the
   pulse *feels* good in sync with real audio needs the user, same standing limitation as
   every audio/motion check in this project — and is now doubly true given the open voice-
   quality question above.

## Sequencing note (important, not yet resolved with the user)

**The orb work and the Task 7 voice-quality blocker are now tangled.** The orb's whole
purpose is to pulse in sync with narration, but the narration engine itself just drew a real
quality complaint. Two real options, and the user has not yet said which they want:
- Proceed with the orb UI work independently — it's real regardless of which engine
  eventually produces the audio, and the per-word sync hook works the same either way.
- Have the voice-quality conversation first, since it might reshape assumptions the orb
  design leans on (e.g. if the fix involves per-persona audio characteristics beyond just an
  MP3 file, that could touch the sync mechanism).

**Ask the user directly which they want before picking either back up.** Don't assume.

## What's next (ordered)

1. Ask the user: voice-quality conversation first, or resume/finish the orb brainstorm
   first? (See "Sequencing note" above — genuinely open, don't guess.)
2. **If voice quality first:** start a fresh `superpowers:brainstorming` session scoped to
   "what should the Bullion narration TTS approach be, given `say`-CLI hasn't satisfied the
   user for either persona." Bring in the deferred "Thamie" idea and the Chatterbox history
   as prior art/context, not as a foregone conclusion.
3. **If orb work first (or once voice quality is resolved):** re-present sections 5-8 above
   for explicit confirmation (they were shown but not signed off), then write the design to
   `docs/superpowers/specs/2026-08-01-bullion-persona-orb-design.md`, run the spec self-review,
   get the user's sign-off on the written file, then invoke `superpowers:writing-plans`.
4. Once Task 7's real blocker (voice quality) is actually resolved — not just re-verified —
   close out Task 7 for real: re-run the full Python suite, do a genuine human audible pass
   against whatever engine is chosen, then ask again about pushing (a fresh yes/no, not
   reusing "hold" from this session).
5. Consider cleaning up the stale worktree at
   `.claude/worktrees/bullion-persona-toggle-frontend` once the user confirms they're done
   with it (not this session's call to make unilaterally).

## Verification idioms used in this project (for the resuming session)

- Test suite: `cd bullion-live-map && python3 -m unittest discover -s tests && python3 -m
  unittest test_calibrate && python3 -m unittest scripts.test_generate_narration -v`
  (currently 96/96: 41 + 33 + 22).
- Audible correctness, caption-sync feel, and now also "does this voice sound good at all"
  **cannot be automated** — every such check is an explicit human-in-a-focused-tab step,
  never inferred from `.play()` resolving or console cleanliness alone. This project's
  standing limitation: automated/background browser tabs report
  `document.visibilityState: "hidden"`, which throttles real audio loading — a
  `readyState`/`duration` check from automation proves the JS logic ran, never that a human
  actually heard anything.
- Mechanical front-end checks (state transitions, call counts, `sessionStorage`/
  `localStorage` persistence) can be verified via claude-in-chrome by instrumenting the
  relevant function (e.g. wrapping `playCurrentNarration` to count calls) — but reload the
  page between instrumentation attempts; re-wrapping an already-wrapped function across
  calls without a reload double-counts (see the caveat above).
- SDD process idioms: `.superpowers/sdd/2026-07-31-bullion-voice-persona-toggle/progress.md`
  is the ledger and recovery map — trust it and `git log` over this handoff's own prose if
  they ever disagree.

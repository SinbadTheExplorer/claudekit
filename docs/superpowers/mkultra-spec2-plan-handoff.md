# Bullion Mk Ultra — Spec 2 Plan Ready — Session Handoff

**Written:** 2026-07-28 · **For:** a fresh session resuming right before implementation starts.
The design brainstorm and the implementation plan are both done and committed — nothing has
been built yet. The only open question is which execution method to use. Prior handoff:
`docs/superpowers/mkultra-spec2-brainstorm-handoff.md` (written mid-brainstorm, before the spec
or plan existed — now superseded by this one, but left in place since it's git-tracked).

## Goal

Same effort as the prior handoff: the **Mk Ultra editorial identity pass** (Spec 2) —
typography, color palette, a "Bullion" wordmark/monogram, two field-note annotations, a
signature cursor, and a WebGL/CDN fallback card — on `bullion_mkultra.html` only. Since the
prior handoff, the brainstorm finished, the user approved the design, and a full 6-task
implementation plan was written, self-reviewed, and committed.

- Spec (approved): `docs/superpowers/specs/2026-07-28-bullion-mkultra-experience-design.md`
- **Plan (the authority for implementation): `docs/superpowers/plans/2026-07-28-bullion-mkultra-experience.md`**
  — 6 tasks, each with exact file/line anchors, real code (not placeholders), and a headless-
  Chrome-probe + Chrome-MCP-screenshot verification step.
- No SDD progress ledger exists yet — implementation hasn't started. If
  `superpowers:subagent-driven-development` is the chosen execution path, it will create one.

## How to resume (do this first)

1. Confirm branch state: `git -C ~/claude-projects/claudekit log --oneline -3`
   should show `f3627b7` at HEAD on `main`. `git rev-list --left-right --count
   origin/main...main` should read `0  2` — **local `main` is 2 commits ahead of
   `origin/main`** (`e61b428`, `f3627b7`), not yet pushed. This is expected, not a problem to
   fix reflexively.
2. **Do not re-run brainstorming or writing-plans.** Both are finished and approved. Read the
   plan file above — it is self-contained and has everything needed to implement.
3. There is no ledger to read yet (nothing built). Trust the plan file + `git log` over any
   recollection of what "should" be done.
4. **Immediate next action:** the user was asked to choose an execution approach and the answer
   may not have been captured before this handoff was written — **ask again rather than assume**:
   - **Subagent-Driven (recommended)** — invoke `superpowers:subagent-driven-development`
     against the plan file. Fresh subagent per task, two-stage review between tasks.
   - **Inline Execution** — invoke `superpowers:executing-plans` against the same plan file.
     Batch execution in-session with checkpoints.

## Current state (active files)

**Branch:** `main`, 2 commits ahead of `origin/main` (local-only: `e61b428`, `f3627b7`), 0
commits ahead in terms of implementation — **zero lines of `bullion_mkultra.html` have been
touched yet.** This is still fully pre-implementation.

**Files created / changed (all committed):**
- `docs/superpowers/specs/2026-07-28-bullion-mkultra-experience-design.md` (`e61b428`) — the
  approved 6-section design (typography, palette, header/mark, personal-touch details, WebGL
  fallback, testing approach).
- `docs/superpowers/mkultra-spec2-brainstorm-handoff.md` (`e61b428`) — the prior handoff;
  tracked, so left in place per this project's archiving convention even though it's no longer
  in the "2 most recent" window.
- `docs/superpowers/plans/2026-07-28-bullion-mkultra-experience.md` (`f3627b7`) — the 6-task
  implementation plan. Self-reviewed (spec coverage / placeholder scan / type-consistency all
  passed cleanly — see the plan's own header for exact anchors used).

**Files later work will modify (untouched so far):**
- `bullion-live-map/bullion_mkultra.html` — the sole implementation target for all 6 tasks.
  Line numbers cited in the plan were captured live from this file on 2026-07-28; the plan
  already instructs each task to locate code via anchor text/selectors rather than trust line
  numbers blindly, since numbers will drift task-to-task as edits land — re-emphasize this if
  resuming long after the plan was written.

**Scratch workspace / traps:**
- ⚠️ **`e61b428` and `f3627b7` are local-only, not pushed.** Don't assume `git show
  origin/main:<path>` reflects the spec or plan — it won't until a push happens. Confirm with
  the user before pushing (this project's/this assistant's standing practice).
- ⚠️ **Task 2's palette hex values are an unverified first draft**, explicitly flagged as such
  in the plan's own "Global Constraints" section — hand-reasoned for hue/lightness separation,
  never actually rendered and checked in a browser before being written into the plan. Task 2's
  Step 5 mandates a screenshot check with explicit permission (expectation, even) to adjust
  values that don't read as distinguishable. Do not skip that step or treat the draft hex values
  as final just because they're typed into the plan.
- ⚠️ **Task 5's field-note copy is a draft**, not signed off word-for-word by the user — they
  approved the concept (first-person annotations on the `usd→oil` and `credit→equit` links) and
  saw this exact draft text during brainstorming, but explicitly said they may want to rewrite
  it themselves since it's meant to be their own voice.
- ⚠️ This handoff exists at a clean checkpoint, not because anything is broken — everything
  through plan-writing is done and approved; only the execution-method choice is open.

**Not mine — leave alone (pre-existing untracked noise, confirmed via `git status`):**
`docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`, `.codex/`,
`AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple), `bullion-live-map/__pycache__/`,
`bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`, `docs/superpowers/
mk12-handoff.md` and `docs/superpowers/honesty-pass-handoff.md` (both older tracked handoffs,
correctly left in place). **Never `git add .`/`-A`.**

## What has changed

- Brainstorm finished; design approved section-by-section by the user (`e61b428`).
- Full implementation plan written and committed (`f3627b7`), self-reviewed with no gaps found.
- **Zero implementation.** No task in the plan has been started.

## What has failed / risks / caveats

- **Nothing has failed.** No code has been touched yet.
- **UNVERIFIED:** N/A — nothing built to verify.
- **Nothing overrides the plan.** All decisions from the brainstorm (scope = visual identity +
  personal touch + WebGL fallback only; Times New Roman for all headers/titles; Approach A;
  warm/tactile direction) are already baked into the spec and plan — no need to re-derive them,
  just follow the plan file.

## What's next (ordered)

1. **Get the user's execution-approach choice** (Subagent-Driven vs Inline — see "How to
   resume" #4). Do not guess; ask.
2. Run the plan task-by-task via whichever skill was chosen, in the order the plan lists them
   (Typography → Palette → Header/mark → Cursor → Field notes → WebGL fallback) — later tasks
   don't strictly depend on earlier ones code-wise, but Task 3 references `--font-display` from
   Task 1, so keep that ordering.
3. After Task 6: run `cd bullion-live-map && python3 -m unittest discover -s tests && python3
   -m unittest test_calibrate` as a sanity check (this pass shouldn't affect those, but confirm).
4. Confirm with the user, then `git push origin main` (carries the 2 pending local commits plus
   whatever implementation produced).
5. Confirm the live Pages URL serves the update within ~30-90s:
   `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mkultra.html`

## Verification idioms used in this project (for the resuming session)

- **The plan file has its own fully-spelled-out "Verification Harness" section** — a reusable
  headless-Chrome-probe bash recipe (copy html+data.json to a temp dir, inject a probe script
  before the last `</body>`, run headless Chrome, grep `PROBE_` output) that every task
  substitutes a different probe script into. That's the authoritative, most-detailed version of
  this idiom for this specific effort — prefer it over reconstructing the pattern from memory.
- **Mk Ultra needs software WebGL** for the normal 3D path in headless Chrome: `--use-gl=angle
  --use-angle=swiftshader --enable-unsafe-swiftshader`. Task 6 deliberately runs once *without*
  those flags to exercise the no-WebGL fallback path for real, not via a mock.
- **NEVER call `openAuditLog()`** in a probe — its animated modal stalls headless virtual-time
  and hangs. macOS has no `timeout` command.
- **Freeze check:** `shasum -a 256 bullion_mk15.html bullion_mk16.html bullion_mk17.html
  bullion_mk18.html` before Task 1 and after Task 6 — all four hashes must match both times;
  Task 6 in the plan has this as an explicit step.
- **git push** works directly from the Bash tool (`GIT_TERMINAL_PROMPT=0 git push origin
  main`); `gh` is NOT installed.

# Bullion Mk Ultra — Identity-Pass Polish (P1s) — Session Handoff

**Written:** 2026-08-06 · **For:** a fresh session picking up the two deferred P2 findings from
this same critique, or continuing further Mk Ultra polish work. The three P1 fixes below are
**done, verified, and live** — nothing here is blocking or half-finished.

## Goal

Ran `/impeccable critique` (dual-agent audit) against `bullion_mkultra.html`'s Spec 2 editorial
identity pass (wordmark, palette, cursor, field notes, WebGL fallback — all of which had
actually shipped already, contrary to a stale earlier handoff that thought it hadn't). The
critique scored it 27/40 and found 5 priority issues (3 P1, 2 P2). The user chose to fix the 3
P1s in this pass and explicitly defer the 2 P2s. All 3 P1s are now fixed, verified, committed,
and pushed.

- Critique snapshot (full findings, all 5 issues, heuristic scores): `.impeccable/critique/2026-08-06T12-49-55Z__bullion-live-map-bullion-mkultra-html.md`
- Spec (approved): `docs/superpowers/specs/2026-08-06-bullion-mkultra-identity-polish-design.md`
- Plan (executed in full): `docs/superpowers/plans/2026-08-06-bullion-mkultra-identity-polish.md`
- No SDD progress ledger — this ran via `superpowers:executing-plans` (inline), not
  subagent-driven, so the plan file's own checkboxes are the closest thing to a ledger (not
  ticked off during execution — trust `git log` over them).

## How to resume (do this first)

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline -6` should
   show `de39d4d` at `HEAD` on `main`. `git rev-list --left-right --count origin/main...main`
   should read `0  0` — **fully pushed, nothing pending.**
2. **Do not re-run the critique or brainstorming for the P1 work** — it's done. If you want to
   verify rather than trust this doc, the critique snapshot above lists all 5 original issues;
   compare against the "What has changed" section below.
3. If resuming the **deferred P2s**, read the critique snapshot's "Priority Issues" section for
   the two P2 write-ups in full (WebGL-fallback/orb overlap, field-note discoverability) — this
   handoff only summarizes them.
4. **Immediate next action:** this is a clean stopping point, not a blocked one. Ask the user
   what they want next — pick up a P2, run a fresh critique, or work on something unrelated.
   If picking up a P2: **invoke `superpowers:brainstorming` first**, same as this session did —
   don't jump straight to editing, per this project's standing skill-priority convention.

## Current state (active files)

**Branch:** `main` (no feature branch — this project works directly on `main` by standing
choice, confirmed again this session), fully in sync with `origin/main`.

**Files changed (all committed and pushed):**
- `bullion-live-map/bullion_mkultra.html` — all 3 fixes landed in this one file across 3
  commits: `f58211d` (cursor), `64ccffb` (text sizes), `de39d4d` (palette). See "What has
  changed" below for exact commit contents.
- `docs/superpowers/specs/2026-08-06-bullion-mkultra-identity-polish-design.md` (untracked, per
  this project's `docs/superpowers/` convention) — the approved spec, including the split
  reading-content/control/micro-label font-size taxonomy and the deuteranopia re-hue method.
- `docs/superpowers/plans/2026-08-06-bullion-mkultra-identity-polish.md` (untracked) — the
  4-task implementation plan, with exact selector tables and the search methodology for the new
  hex values. Worth reading if doing similar polish work again — the ΔE search technique and the
  font-size bucketing logic are reusable.
- `.impeccable/critique/2026-08-06T12-49-55Z__bullion-live-map-bullion-mkultra-html.md` — the
  full critique snapshot (first run for this target, no trend yet).

**Files later work will modify (untouched so far, if picking up the P2s):**
- `bullion-live-map/bullion_mkultra.html` again — `showRenderFallback()` (search for that
  function name; was around line 1791 before this session's edits shifted things) needs to hide
  `#persona-orb` so the WebGL-fallback reassurance message isn't covered by the orb. Field-note
  discoverability has no concrete implementation plan yet — needs a design decision (marker on
  the flagged links? onboarding mention?) before it's a coding task.

**Scratch workspace / traps:**
- ⚠️ **Two same-day automated bot commits landed on `origin/main` mid-session**
  (`e70749f`/`23970ef`, "Update live financial data for 2026-08-05/06") and rejected the first
  push attempt. Confirmed via `git show --stat <sha>` that **both touch `data.json` only, never
  `bullion_mkultra.html`** — so a plain `git rebase origin/main` was safe and conflict-free. This
  will keep happening (daily cron) — expect a rejected push occasionally, verify the bot commits
  are data-only before rebasing, don't assume a conflict.
- ⚠️ **Line numbers in the plan/spec above will have drifted** — Task 1 inserted ~13 new lines
  into the JS section (~line 1782 onward). CSS-block and `GROUP_COLOR` line numbers (everything
  before ~line 912) are unaffected since those edits were same-line value swaps, not insertions.
  Locate by selector/function name, not line number, same as this project's standing convention.
- ⚠️ **The `.impeccable/` directory is new this session** (first critique run in this project) —
  it's untracked; leave it that way unless the user says otherwise, consistent with the
  `docs/superpowers/` convention.

**Not mine — leave alone (pre-existing untracked noise, confirmed via `git status`):**
`docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`, `.codex/`,
`.superpowers/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple), `bullion-live-map/__pycache__/`,
`bullion-live-map/tests/__pycache__/`, `bullion-live-map/scripts/__pycache__/`,
`bullion-live-map/audio/narration/.*_done.txt`, `docs/superpowers/archive/`,
`docs/superpowers/mk12-handoff.md`, `docs/superpowers/honesty-pass-handoff.md`,
`docs/superpowers/mkultra-spec2-brainstorm-handoff.md`,
`docs/superpowers/mkultra-spec2-plan-handoff.md` (all four of these older handoffs are
git-tracked — correctly left in place, not superseded-and-archived). **Never `git add .`/`-A`.**

## What has changed

- **`f58211d`** — fixed the dead compass-rose cursor: added `isDragging` state, `CURSOR_GRAB`/
  `CURSOR_GRABBING` constants (copied from the existing CSS data-URIs), an `applyCursor()`
  helper, wired into `onPointerMove`/`onPointerDown`/`onPointerUp`/`onPointerCancel`. Root cause
  was an inline `canvas.style.cursor = 'grab'/'pointer'` beating the CSS rule that already had
  the correct SVG cursor.
- **`64ccffb`** — raised 27 undersized CSS rules: 15 reading-content rules to 12px, 1
  width-constrained tooltip (`.orb-nudge-tip`) to 11px, 2 interactive control labels (`.btn`
  mobile, `.disclaimer-link`) to 11px, 9 uppercase micro-label/badge rules bumped +1px (staying
  below the reading-content floor by design — not a bug if you see e.g. `.drawer-label` still at
  10px, that's intentional).
- **`de39d4d`** — re-hued `sovereign`/`monetary` and `sectors`/`indicator` in `GROUP_COLOR`
  (line ~912) for deuteranopia safety. New values found via a randomized search (120k+ trials)
  maximizing minimum ΔE across the full 12×12 matrix, hue-constrained to ±20° of each original to
  preserve the palette's hue families. Two pre-existing near-misses among the *unchanged* 8
  colors (`capmkt`/`fx`, `regulator`/`fx`) were confirmed untouched by this fix — out of scope,
  not a regression.
- **Rebased** past the 2 bot commits, **pushed** to `origin/main` (`de39d4d`), **confirmed
  building** on GitHub Pages for that exact commit SHA at push time.
- **Tests:** `python3 -m unittest test_calibrate` 33/33; the `discover` suite exits 0 (its final
  test prints a freshness table instead of the usual `Ran N tests` line — expected, not a bug in
  this session's work). Freeze-check on `bullion_mk11.html`–`bullion_mk18.html` clean before and
  after every commit.

## What has failed / risks / caveats

- **Nothing has failed.** All three fixes were verified live (headless-Chrome probe + real
  Chrome-MCP mouse interaction + 0 console errors) before each commit, not just claimed.
- **UNVERIFIED:** nothing from the shipped work. Everything committed was rendered and checked,
  not left as an on-paper claim.
- **Two P2 findings from the same critique are deferred, not fixed:**
  1. WebGL-fallback card gets covered by `#persona-orb` (both center-positioned in `#stage`,
     orb's `z-index:8` beats the fallback's `z-index:5`; `showRenderFallback()` never hides the
     orb). Low frequency (only triggers on actual WebGL failure) but real when it happens.
  2. Field notes — the most human content in the file — are undiscoverable: only 2 of 250+ links
     carry one, no signifier anywhere in the graph or Overview board.
- **Decision carried forward, overriding nothing but worth restating:** this project pushes
  directly to `main`, no PRs, no feature branches — confirmed again this session via the
  finishing-a-development-branch skill's menu, adapted since the standard merge/PR options don't
  apply to a no-branch workflow.

## What's next (ordered)

1. Ask the user what's next — this is a clean stop, not a blocker. Options: pick up a P2 (start
   with `superpowers:brainstorming`), run a fresh `/impeccable critique` on a different area,
   or something unrelated entirely.
2. If picking up a P2, read the critique snapshot's full write-up for that issue first — this
   handoff only has the summary.

## Verification idioms used in this project (for the resuming session)

- **Headless-Chrome probe harness:** copy `bullion_mkultra.html` + `data.json` to a temp dir,
  inject a probe script before the last `</body>` (use `html.rfind('</body>')` — there's a decoy
  `</body>` inside a JS string earlier in the file), run headless Chrome with
  `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader` (real software WebGL,
  required for anything touching the 3D scene/raycaster), grep `PROBE_` from the log. **The
  canvas element (`#mkultra-canvas`) doesn't exist until the async WebGL init completes** — poll
  for it (`setTimeout` retry loop) rather than assuming it's present on script injection, or
  you'll get `Cannot read properties of null (reading 'dispatchEvent')`.
- **Chrome-MCP visual checks:** the extension **cannot navigate to `file://` URLs** (blocked as
  "browser-internal or unparseable") — serve the folder locally first
  (`python3 -m http.server 8901` from `bullion-live-map/`) and navigate to `localhost`.
- **Synthetic `PointerEvent` dispatch and `OrbitControls.js`:** dispatching a synthetic
  `PointerEvent('pointerdown', ...)` — even via the Chrome-MCP `computer` tool's real
  click-and-drag, not just page-context JS — throws `NotFoundError: Failed to execute
  'setPointerCapture'` inside the vendored `OrbitControls.js`. This is a known automation-tooling
  artifact (no OS-level "active" pointer for `setPointerCapture` to find), confirmed unrelated to
  any app code by testing the identical pre-fix file. Don't chase it; it doesn't happen with a
  real physical mouse.
- **Deuteranopia simulation in-browser** (new technique this session, reusable): inject an SVG
  `<filter>` with a `feColorMatrix` using the Machado et al. (2009) deuteranopia coefficients,
  apply via `document.documentElement.style.filter = 'url(#deuteranopia-sim)'`, screenshot, then
  clear the filter. Matches the same matrix used for the offline Python ΔE search, so the visual
  check and the math agree by construction.
- **GitHub API checks** (Pages build status, workflow runs): `TOKEN=$(printf
  "protocol=https\nhost=github.com\n" | git credential fill 2>/dev/null | sed -n
  's/^password=//p')`, then `curl -H "Authorization: token $TOKEN" ...`, then `unset TOKEN`.
  Anonymous calls 403 even on this public repo. `gh` is NOT installed.
- **Python tests:** `cd bullion-live-map && python3 -m unittest discover -s tests` and
  `python3 -m unittest test_calibrate`.
- **Freeze-check:** `git diff --stat -- bullion-live-map/bullion_mk1[1-8].html` must be empty.
- **git push:** works directly from the Bash tool (`GIT_TERMINAL_PROMPT=0 git push origin
  main`). A rejection means the remote moved — `git fetch origin main` and inspect with `git show
  --stat <sha>` before rebasing; don't force-push.

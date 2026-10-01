# Bullion Mk Ultra — Field-Note Discoverability — Session Handoff

**Written:** 2026-08-07 · **For:** a fresh session picking up further Mk Ultra polish work, or
verifying this pass independently. This work is **done, verified, pushed, and live** — nothing
here is blocking or half-finished. Also relevant: read
`bullion-mkultra-identity-polish-handoff.md` (in this same directory) only if you need the P1
polish pass that immediately preceded this one — this handoff doesn't depend on it.

## Goal

Fixed the second of two P2 findings deferred from the 2026-08-06 `/impeccable critique` of
`bullion_mkultra.html`: only 2 of 250+ causal links carry a first-person "field note" (the
creator's own marginalia on a surprising finding), and nothing in the graph, the Overview board,
or the relationship panel signaled which links had one. Added a small ✎ marker on the two
affected links' nodes/rows, plus one onboarding sentence. **Deliberately out of scope:** writing
more field notes or lowering the authoring bar — this pass only makes the existing 2 discoverable.

- Spec: `docs/superpowers/specs/2026-08-06-bullion-mkultra-fieldnote-discoverability-design.md`
- Plan: `docs/superpowers/plans/2026-08-06-bullion-mkultra-fieldnote-discoverability.md`
- Progress ledger: **deleted** — the plan's SDD workspace
  (`.superpowers/sdd/2026-08-06-bullion-mkultra-fieldnote-discoverability/`) was removed after
  the final review came back clean, per this project's standing SDD convention ("final review
  clean: delete this plan's workspace — the git history is the record now"). `git log` below is
  the authority now, not a ledger file.

## How to resume (do this first)

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline -9` should show
   `cf3a6a3` at `HEAD` on `main`. `git rev-list --left-right --count origin/main...main` should
   read `0  0` — **fully pushed, nothing pending, confirmed live on GitHub Pages at this SHA.**
2. **Do not re-run brainstorming, planning, or the critique for this work** — it's done and
   independently re-verified (see "What has changed" below). The other P2 from the same critique
   (WebGL-fallback card getting covered by `#persona-orb`) was fixed in the *prior* session, not
   this one — check `bullion-mkultra-identity-polish-handoff.md` if you need that history, but
   both P2s from the original critique are now resolved.
3. This is a clean stopping point, not a blocked one. Ask the user what they want next.

## Current state (active files)

**Branch:** `main` (no feature branch — this project works directly on `main` by standing
choice, reconfirmed again this session via `superpowers:using-git-worktrees` and
`superpowers:finishing-a-development-branch`, both adapted for a no-branch workflow), fully in
sync with `origin/main` at `cf3a6a3`.

**Files changed (all committed and pushed, 8 commits from `de39d4d` to `cf3a6a3`):**
- `bullion-live-map/bullion_mkultra.html` — every commit touched only this file. In order:
  `80662e7` (foundation: `FIELDNOTE_NODE_IDS` set + `.fieldnote-badge` CSS), `80a4f3a` + fix
  `b1069c6` (board-card badge), `6fb6d5a` (3D node-label badge), `8b880b3` + fix `8245cd9`
  (relationship-row badge), `6aa54b3` (onboarding sentence), `cf3a6a3` (final-review hardening:
  extracted the badge's title string into a shared `FIELDNOTE_TITLE` constant). See "What has
  changed" for why two of these needed fix commits.
- `docs/superpowers/specs/2026-08-06-bullion-mkultra-fieldnote-discoverability-design.md`
  (untracked, per this project's `docs/superpowers/` convention) — approved spec.
- `docs/superpowers/plans/2026-08-06-bullion-mkultra-fieldnote-discoverability.md` (untracked) —
  the 6-task implementation plan, executed via `superpowers:subagent-driven-development`
  (fresh subagent per task, full review loop, final whole-branch review). Worth reading if doing
  similar micro-polish work again — the probe-driven verification pattern (write probe → confirm
  it fails → implement → confirm it passes) is reusable, and the exact headless-Chrome harness
  command is documented there.

**Files later work will modify (untouched so far):**
- None specific to this effort — it's complete. The other deferred item from the original
  critique (whether the field-note authoring bar should be lower, and writing more notes) was
  explicitly scoped *out* of this pass by user decision; if picked up later it's a fresh
  brainstorm, not a continuation of this plan.

**Scratch workspace / traps:**
- ⚠️ **The SDD workspace for this plan no longer exists** — deleted after the final review
  passed, per convention. Don't go looking for `task-N-report.md` files; `git log` on the 8
  commits above is the record.
- ⚠️ **`FIELDNOTE_TITLE` is a new top-level `const`** (search for it, don't trust a line number —
  it sits right after `FIELDNOTE_NODE_IDS`, itself right after the `PLUMBING_LINKS.forEach` merge
  block). It's the single source of truth for the badge's tooltip text now; the three consuming
  sites (board card, 3D label, relationship row) all reference it rather than hand-typing the
  string. If you ever touch this area again, keep it that way — see the trap below for why.
- ⚠️ **Two same-day automated bot commits could land on `origin/main` mid-session, same as every
  prior session** (daily cron updating `data.json`) — none did this time (`git fetch` showed 0
  behind right before push), but if a push is rejected next time, `git show --stat <sha>` to
  confirm it's data-only before rebasing, per this project's standing idiom.

**Not mine — leave alone (pre-existing untracked noise, confirmed via `git status`):**
`docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`, `.codex/`,
`.superpowers/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple), `bullion-live-map/__pycache__/`,
`bullion-live-map/scripts/__pycache__/`, `bullion-live-map/tests/__pycache__/`,
`bullion-live-map/audio/narration/.*_done.txt`, `docs/superpowers/archive/`, and the other
pre-existing handoff/plan/spec files in `docs/superpowers/` (all correctly left in place, not
superseded). **Never `git add .`/`-A`.**

## What has changed

- **`80662e7`** — added `FIELDNOTE_NODE_IDS` (a `Set` of node ids with ≥1 field-noted link,
  derived from the already-merged `LINKS` array — see the trap below on why that merge order
  matters in this file) and the shared `.fieldnote-badge` CSS class.
- **`80a4f3a` → fixed by `b1069c6`** — board-card badge. First attempt substituted an ASCII
  hyphen and escaped straight apostrophe for the required em dash/curly apostrophe in the badge's
  `title` text, on the (wrong) theory that the real characters would cause a syntax error. Task
  review caught it; fix round confirmed the real Unicode characters at the byte level.
- **`6fb6d5a`** — 3D node-label badge (inside the `Renderer` IIFE's `buildLabels()`). Landed
  clean on the first review — the implementer had the prior task's mistake explained to it in the
  dispatch and got the exact characters right immediately.
- **`8b880b3` → fixed by `8245cd9`** — relationship-row badge. Same class of mistake as the board
  card, but this time it wasn't cosmetic: the title string is built via JS string concatenation,
  and a bare ASCII apostrophe inside a single-quoted JS string literal terminated the string
  early, producing `Uncaught SyntaxError: Unexpected identifier 's'` in a classic (non-module)
  top-level `<script>` tag that contains the *entire app* — meaning the whole page would have
  gone dark. The implementer's own self-reported byte-check claimed the correct character was
  present; it wasn't. **The controller independently ran the actual headless-Chrome harness
  rather than trusting that report, and that's what caught it** — worth remembering next time an
  implementer says static/byte-level verification when the harness is available and "worked
  before."
- **`6aa54b3`** — one sentence appended to the onboarding coach's second step, mentioning the
  pencil icon. Landed clean.
- **`cf3a6a3`** — final whole-branch review (dispatched on the most capable model) flagged that
  the badge's title string had been hand-retyped three times and was the site of both bugs above;
  recommended extracting it into a shared constant so the failure class can't recur. Fixed,
  independently byte-verified and probe-verified by the controller (the implementer that wrote it
  was cut off mid-task by a session API limit before it could commit — the controller verified
  the already-correct diff and committed it directly, then a scoped re-review confirmed it clean).
- **Pushed** to `origin/main` (`cf3a6a3`) after explicit user confirmation, **confirmed built** on
  GitHub Pages for that exact commit SHA via the GitHub API.
- **Tests:** `python3 -m unittest test_calibrate` 33/33; `discover` suite exits 0 (freshness-table
  tail, not a `Ran N tests` line — expected, matches this project's known-normal output). Freeze-
  check on `bullion_mk11.html`–`bullion_mk18.html` clean throughout.

## What has failed / risks / caveats

- **Nothing has failed in the shipped result.** Two implementation attempts had a real bug each
  (see above), but both were caught by review before merge, fixed, and independently
  re-verified — nothing broken landed on `main`.
- **UNVERIFIED:** nothing. Every commit was rendered and functionally probed (headless Chrome +
  live Chrome-MCP visual pass covering all four surfaces: board card, 3D label, relationship row,
  onboarding coach), not left as an on-paper claim.
- **4 Minor findings from the final review, logged but explicitly not fixed (non-blocking, by
  design — Minor findings don't enter the SDD fix loop):**
  1. The 3D-label badge's `title` tooltip can never fire — `#mkultra-labels`'s container has
     `pointer-events: none`, which the badge inherits. The *visual* signal (the glyph itself)
     works fine; only the hover tooltip on that one surface is inert.
  2. The shared title text says "...on **this link**", which is accurate on the relationship row
     but imprecise on the board card / 3D label (those mark a *node* that has a field note
     *somewhere among its links*, not necessarily on that specific card/label). This is
     plan-mandated (byte-identical string was an explicit requirement, precisely because of the
     bugs above) — a copy fix would trade the identical-everywhere property for accuracy, a real
     trade-off, not a free win.
  3. `.fieldnote-badge`'s `margin-left: 3px` plus the relationship row's `flex; gap: 7px` gives it
     slightly more space before it than after — cosmetically negligible, confirmed in a rendered
     screenshot. Also missing `flex-shrink: 0` unlike its row siblings (harmless given a
     single-glyph item's `min-width: auto`, just an inconsistency).
  4. The onboarding coach styles the glyph with an inline `style="color:var(--gold-dim)"` instead
     of reusing `.fieldnote-badge` — plan-specified (the class's `font-size`/`margin-left` would
     look wrong inside prose), but it's a fourth unshared styling of the same mark.
  5. (Not a defect, noted as a known limit) The discoverability win is sighted-only — the board
     badge is excluded from the accessible name via `aria-label`, and 3D labels aren't reachable
     by assistive tech at all. Correct call for a decorative, non-interactive marker; a
     screen-reader user gets no signal a field note exists.
- **Decision carried forward, overriding nothing but worth restating:** this project pushes
  directly to `main`, no PRs, no feature branches, no worktrees — reconfirmed *twice* this
  session (once before starting implementation, once at finish) via the adapted
  `using-git-worktrees` / `finishing-a-development-branch` menus.

## What's next (ordered)

1. Ask the user what's next — this is a clean stop, not a blocker. Both P2s from the original
   2026-08-06 critique are now resolved (WebGL-fallback/orb overlap in the prior session, field-
   note discoverability in this one). Natural options: run a fresh `/impeccable critique` on a
   different area, revisit the "should the field-note authoring bar be lower" question as its own
   brainstorm (explicitly deferred, not started), or something unrelated.
2. If picking up any of the above, **invoke `superpowers:brainstorming` first** — don't jump
   straight to editing, per this project's standing skill-priority convention (reconfirmed again
   this session).

## Verification idioms used in this project (for the resuming session)

- **Headless-Chrome probe harness:** copy `bullion_mkultra.html` + `data.json` to a temp dir,
  inject a probe script before the last `</body>` (use `html.rfind('</body>')` — there's a decoy
  `</body>` inside a JS string earlier in the file), run headless Chrome with `--use-gl=angle
  --use-angle=swiftshader --enable-unsafe-swiftshader` (real software WebGL). **Poll for
  `#mkultra-canvas` and/or the specific DOM you need (`.board-card`, `#mkultra-labels > div`)
  rather than assuming readiness** — the 3D scene (`Renderer`, an IIFE) initializes
  asynchronously, and its internal state (e.g. `labelEls`) is private to that closure, not
  reachable from an injected probe — query the real DOM it produces instead.
- **`--virtual-time-budget=15000` can leave the Chrome process lingering past the shell command's
  own timeout** even though the probe's console output lands in the log well before that — check
  the log directly (`grep PROBE_ chrome.log`) rather than waiting on the process to exit, and
  `kill -9` the lingering PID once you have your answer.
- **Do not trust an implementer's self-reported byte/character verification** on anything
  involving non-ASCII punctuation in this file — independently re-run the actual functional
  harness. This bit twice in one session; the second time was a real `SyntaxError`, not a
  cosmetic mismatch.
- **Chrome-MCP visual checks:** the extension **cannot navigate to `file://` URLs** — serve the
  folder locally first (`python3 -m http.server 8901` from `bullion-live-map/`) and navigate to
  `localhost`.
- **GitHub API checks** (Pages build status): `TOKEN=$(printf "protocol=https\nhost=github.com\n"
  | git credential fill 2>/dev/null | sed -n 's/^password=//p')`, then `curl -H "Authorization:
  token $TOKEN" ...`, then `unset TOKEN`. Anonymous calls 403 even on this public repo. `gh` is
  NOT installed.
- **Python tests:** `cd bullion-live-map && python3 -m unittest discover -s tests` and
  `python3 -m unittest test_calibrate`.
- **Freeze-check:** `git diff --stat -- bullion-live-map/bullion_mk1[1-8].html` must be empty.
- **git push:** works directly from the Bash tool (`GIT_TERMINAL_PROMPT=0 git push origin
  main`), but only after explicit user confirmation — this project's standing practice, honored
  via the adapted `finishing-a-development-branch` menu (push now vs. keep local, not
  merge/PR). `git fetch origin main` first to check for the daily bot before pushing.

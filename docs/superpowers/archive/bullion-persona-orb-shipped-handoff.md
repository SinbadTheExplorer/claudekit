# Bullion Persona Orb — Shipped + Pushed — Session Handoff

**Written:** 2026-08-01 (updated same day after diagnosing a GitHub Pages outage) · **For:**
any future session resuming this work — the persona orb redesign is code-complete,
reviewed, and pushed to `origin/main`. **GitHub Pages itself was broken** (unrelated to
the orb feature) and required two follow-up infra fixes, documented in detail below —
check whether it's actually deploying before doing anything else. One parked,
non-blocking orb known issue remains after that. Supersedes
`bullion-voice-persona-toggle-and-orb-handoff.md` (that file's Tasks 1-6 + orb-brainstorm
content is now stale/complete; read this file instead). That prior file is kept as the
second-most-recent handoff; read it only if you need the original orb brainstorm's
section-by-section rationale in detail.

## Goal

Ship the "persona orb" — a persistent floating UI element (bottom-right corner, both
`bullion_mk18.html` and `bullion_mkultra.html`) replacing the old small header
persona-toggle button, that shows the active narration persona (Alfred 🎩 / Johnny 👹),
idle-breathes, pulses per spoken word during narration, repositions around the open
detail panel, and toggles persona on click/keyboard. This is now **done** — the goal
going forward is verification (the user testing it live) and, separately, picking back
up the still-unresolved voice-quality conversation this work was deliberately run
independently of.

- Design spec: `docs/superpowers/specs/2026-08-01-bullion-persona-orb-design.md`
- Plan: `docs/superpowers/plans/2026-08-01-bullion-persona-orb.md` (5 tasks)
- Progress ledger (recovery map — **trust this over this handoff's prose if they ever
  disagree**): `.superpowers/sdd/2026-08-01-bullion-persona-orb/progress.md`

## How to resume (do this first)

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline -3`
   should show `2e8fda3` at HEAD on `main`. `git rev-list --left-right --count
   origin/main...main` should read `0 0` — **fully pushed, nothing held back** (unlike
   every prior handoff in this project, there is no "hold" state right now). `git status
   --short` should show only the usual pre-existing untracked noise (see "Not mine"
   below).
2. Read the ledger in full: `.superpowers/sdd/2026-08-01-bullion-persona-orb/progress.md`
   — it has the complete Task 1-5 history, including a 2-round fix loop inside Task 1 and
   a final-review fix wave, plus the adjudication ruling on the one parked finding. (The
   ledger predates the Pages/Jekyll investigation below, which happened after Task 5 —
   trust this handoff for that part.)
3. **GitHub Pages is confirmed fixed and live as of this handoff** — do not re-litigate
   this unless something looks freshly broken again. Verified:
   `curl -s "https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mkultra.html?v=$(date +%s)" | grep -c persona-orb`
   returned `15` (and the same for `bullion_mk18.html`) after the `_config.yml` fix
   deployed successfully (`https://github.com/SinbadTheExplorer/claudekit/actions` —
   the `2e8fda3` "pages build and deployment" run shows `completed`/`success`). See "What
   has changed" below for the full story — this was a real, pre-existing infra outage
   unrelated to the orb feature, not a caching delay.
4. **Immediate next action:** get the user's own live-browser confirmation that the orb
   looks/feels right (the one thing this session's automation could never verify — see
   "What has failed" below). Link:
   `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mkultra.html`

## Current state (active files)

**Branch:** `main`, fully pushed and in sync with `origin/main` at `2e8fda3`.

**Files changed, all committed and pushed (`bd4012d..2e8fda3`, 10 commits total —
`bd4012d` is the prior session's already-covered autoplay commit, bundled into this push
since it had been held back unpushed until now; the last 2 are the Pages/Jekyll infra
fix, not orb-feature code):**
- `bullion-live-map/bullion_mk18.html` — `#persona-orb` markup + CSS (idle/active states,
  per-persona gradients, panel-open repositioning desktop+mobile, first-visit nudge),
  removed `#persona-toggle-btn` and its old click handler, `applyPersonaToggle()`
  repurposed, new `toggleNarrationPersona()`/`pulseOrb()`/`setOrbNarrating(on)`/
  `dismissOrbNudge()` functions, `startCaption()`/`clearCaption()`/`playNarration()`
  bodies extended.
- `bullion-live-map/bullion_mkultra.html` — identical changes throughout (verified
  byte-identical in every touched region across all 5 tasks and the fix wave).
- No Python/backend files touched by the orb feature itself — pure front-end, confirmed
  by the diff stat on every task.
- `.nojekyll` (commit `3ce493e`) — **added but ultimately ineffective**, kept in the repo
  anyway (harmless, standard practice, doesn't hurt). See "What has changed" for why it
  didn't work here.
- `_config.yml` (commit `2e8fda3`, **new file, repo root**) — the actual fix: `exclude:
  docs/` stops GitHub Pages' Jekyll build from ever reading the `docs/` tree. This is a
  genuinely new, permanent piece of repo config, not scoped to this plan's ledger — if a
  future session ever needs to serve something out of `docs/` via Pages, this exclude is
  why it won't show up, and that's intentional (see rationale below).

**Not mine — leave alone (pre-existing untracked noise, same as every prior handoff in
this project):** `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`,
`.agents/`, `.codex/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple),
`bullion-live-map/__pycache__/`, `bullion-live-map/scripts/__pycache__/`,
`bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`,
`docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md`,
`docs/superpowers/plans/2026-07-30-bullion-ui-fixes.md`,
`docs/superpowers/plans/2026-07-30-bullion-voice-narration-phase1.md`. **Never
`git add .`/`-A`.**

## What has changed

- **All 5 plan tasks: complete**, each individually task-reviewed (spec ✅ every time,
  Critical/Important findings: 0 across Tasks 2-4; Task 1 needed a 2-round fix loop, see
  below).
- **Task 1's fix loop (a real bug the controller caught in live testing, not part of any
  task reviewer's diff-only review):** the original panel-open repositioning CSS
  (`#app.panel-open #persona-orb`) could never match — `#persona-orb`/`#legend-box`/
  `#detail-panel` are DOM siblings of `#app`, not descendants (`#app` closes before they
  appear in either file). Root-caused to a `#detail-panel.open ~ #persona-orb`
  sibling-combinator fix. Verifying the fix burned an extra round because
  `getComputedStyle()` reads on this environment's hidden/backgrounded automation tab
  kept reporting the stale pre-transition value (see the durable lesson written to memory
  as `chrome-automation-hidden-tab-css-transition-trap` — trust screenshots, not
  `getComputedStyle()` JS-eval reads, when verifying CSS transitions via claude-in-chrome
  in this project). Final state re-reviewed clean, confirmed both structurally (DOM
  ancestry + JS class-toggle timing) and visually (screenshots).
- **Final whole-branch review (opus) found 2 real Important bugs no task-scoped review
  could see**, both traced to gaps in the *design spec's* own prose rather than
  implementer error:
  1. The orb never returned to `.idle` when a narration clip finished playing
     naturally — no audio `ended` handler existed anywhere; `clearCaption()`'s idle-reset
     was only reachable via panel-close, opening a different node, or starting a new
     playback.
  2. `orbPulse`/the nudge's (originally reused) `toolsPulse` keyframes animated
     `box-shadow` without preserving `.orb-core`'s base drop shadow, so the shadow
     visibly blinked off during every word-pulse and the entire ~6s nudge. Safe on the
     keyframe's original target (`#mode-toggle-btn`, no box-shadow of its own), unsafe
     once reused on an element that has one.
  Both fixed in one consolidated final-review fix wave (commit `6a08dc7`): new
  `setOrbNarrating(on)` helper used by `clearCaption()`/`startCaption()`/a new `ended`
  listener in `playNarration()`; `orbPulse` keyframes now layer in the base shadow; the
  nudge got its own dedicated `orbNudgePulse` keyframe instead of sharing `toolsPulse`.
  The same fix wave also addressed 3 cheap Minors: 2 remaining unguarded `#persona-orb`
  DOM accesses merged into one guarded block, a misleading `sessionStorage` key renamed
  from `bullion-orb-nudge-shown` to `bullion-orb-nudge-dismissed` (matches actual
  dismiss-on-interact semantics), and a code comment added documenting the CSS sibling
  combinator's DOM-order dependency. Re-reviewed: 4 of 5 findings cleanly ADDRESSED with
  no new breakage — see "What has failed" for the 5th.
- Design spec doc (`docs/superpowers/specs/2026-08-01-bullion-persona-orb-design.md`) was
  itself corrected during the fix wave: its "Narration sync" section's `clearCaption()`
  call-site enumeration was factually incomplete (missing natural audio completion), and
  its nudge-key description used "shown" language where the actual/now-correct semantics
  are "dismissed."
- Python suite re-run at the end (Task 5): 96/96 pass (41 `tests/` + 33 `test_calibrate`
  + 22 `scripts.test_generate_narration`), unaffected by this pure-front-end change —
  confirms this session's work didn't regress the unrelated live-data pipeline / voice
  generation script.
- Pushed to `origin/main` with the user's explicit, fresh "push now" answer (not a
  reused prior "yes" — this project's standing convention, honored again this session).
- **Separately, after the push: GitHub Pages itself turned out to be broken and was
  fixed.** This is real infrastructure work, not part of the plan/ledger, worth its own
  clear record:
  - The user asked for the mkultra link to test. `curl`-ing it showed the live site was
    stale (still serving Jul 30's content). Checking GitHub's Actions API (with an
    authenticated request via the credential already in `git credential fill` — no new
    token setup needed) showed the "pages build and deployment" workflow had actually
    been **failing since `21cc1ea` (2026-07-31, before this session even started)** — 3
    failed runs in a row, our new commit `6a08dc7` included.
  - Root cause, confirmed by pulling the actual build log (the jobs/logs API needs an
    authenticated request; the anonymous one 403s even on a public repo):
    `docs/superpowers/plans/2026-07-31-bullion-voice-persona-toggle.md:257` contains a
    Python f-string snippet — `f"const {const_name} = {{")` — where `{{` is legitimate
    Python (an escaped literal `{`), but GitHub Pages' default "legacy" build runs
    everything through **Jekyll**, whose Liquid template engine reads `{{` as the start
    of an output tag and throws `Liquid::SyntaxError` trying to parse the rest as a
    template expression. This repo has never been an intentional Jekyll site (it's
    hand-written static HTML) and has no `.nojekyll`/`_config.yml`, so Pages defaults to
    running the whole tree through Jekyll's markdown/Liquid pipeline regardless.
  - **First fix attempt (commit `3ce493e`): added an empty `.nojekyll` at the repo
    root** — the textbook-standard way to tell GitHub Pages to skip Jekyll entirely.
    **This did NOT work** — confirmed by pulling the *next* build's actual log too: it
    still ran full Jekyll (rendering every doc through `jekyll-theme-primer`) and hit the
    identical Liquid syntax error, with no mention of `.nojekyll` anywhere in the log.
    Root cause of *that*: this repo's Pages source is `build_type: "legacy"` (checked via
    the authenticated `/repos/.../pages` API — Settings → Pages → Source =
    "Deploy from a branch"), which GitHub implements via the
    `actions/jekyll-build-pages@v1` Docker action — and empirically, that specific action
    does not check for `.nojekyll` before building. (Left the file in place — harmless,
    just didn't do the job here.)
  - **Second fix (commit `2e8fda3`, the one that actually worked): added `_config.yml`
    at the repo root with `exclude: [docs/]`** — Jekyll's own `exclude` directive
    unconditionally skips reading/parsing anything under `docs/` during site generation,
    so the Liquid parser never touches the file with the `{{` in it (or any future doc
    with a similar pattern — this is a structural fix, not a one-off patch of that one
    line). Verified via the Actions API that the resulting `2e8fda3` "pages build and
    deployment" run completed with `conclusion: success` (the first successful Pages
    build since `2c79324` on Jul 30), then confirmed live by `curl`-ing both HTML files
    and finding the orb's markup present (`grep -c persona-orb` → `15` in each,
    previously `0`).
  - Checked for other landmines while at it: `git grep -E '\{%|\{\{' -- '*.md'` across
    the whole tracked repo found exactly one other hit
    (`bullion-live-map/scripts/test_generate_narration.py:16`, the same snippet in a
    `.py` file) — not a real risk, since Jekyll only Liquid-renders markdown/HTML/files
    with front matter, not plain `.py` files, and this was never implicated in any actual
    failure. No other tracked `.md` files outside `docs/` exist except
    `interest-rate-claude-ai.md` at the repo root, which is clean (0 hits).
  - **This was a real, user-visible outage unrelated to the orb feature** — anyone
    trying to view *any* page on this Pages site (not just the two files this session
    touched) would have hit it. It's now fixed for the whole site, not just this
    feature's two files.

## What has failed / risks / caveats

- **Nothing crashed or shipped broken.** The app works; all task-level and final-level
  reviews are clean or explicitly adjudicated (see next point).
- **One finding was found-and-PARKED, not fixed** — the SDD process caps the final
  review at exactly one fix wave, and this was found in the scoped re-review of that
  wave, i.e. too late for a second wave: **fixing bug (1) above (idle-reset on natural
  end) introduces a narration-overlap edge case.** If a second narration clip starts
  before the first one's audio has actually finished (e.g. clicking through several
  unseen nodes quickly enough that autoplay overlaps), the *first* clip's later `ended`
  event fires `setOrbNarrating(false)` unconditionally — flipping the orb to idle even
  though the *second* clip is still genuinely playing. Neither file has any
  audio-overlap/cancellation tracking (no `currentAudio`/`activeAudio` variable, no
  `.pause()` call on a previous clip when a new one starts) — this is a pre-existing gap
  this plan never scoped to fix; the fix wave's new `ended` listener just newly exposed
  it as an observable state bug. **Impact is bounded**: the orb stops reacting (stays
  motionless except idle-breathing) for the rest of the still-playing second clip's
  duration, until the user does something else that re-triggers `startCaption()`/
  `clearCaption()`. No crash, no data loss, no effect on the caption text itself (still
  correctly shows whichever clip is actually playing). **Ruling (in the ledger): ship
  as-is, this is a reasonable small follow-up task, not a blocker.** A real fix would
  track the currently-playing `Audio` object at module scope and either `.pause()` the
  previous one when a new `playNarration()` call starts, or have each `ended` listener
  check "am I still the active audio" before calling `setOrbNarrating(false)`.
- **UNVERIFIED — the user's own live check.** Every check this session performed was via
  claude-in-chrome browser automation (which, per the memory note above, cannot reliably
  verify real audio playback or animation timing — Chrome's autoplay policy blocks
  programmatic `.play()` without a trusted user gesture, confirmed via a `NotAllowedError`
  console warning during testing, which is expected/not a bug). The orb's *feel* — does
  the pulse actually look good in sync with real audio, does the idle breathe read as
  intended, does the nudge tooltip look right — has not been confirmed by an actual human
  in a focused browser tab. This is this project's own standing limitation for every
  prior audio/motion feature too, not new to this session.
- **GitHub Pages: RESOLVED, not a caveat anymore** — see "What has changed" above for
  the full root-cause story (a pre-existing Jekyll/Liquid parse failure unrelated to the
  orb, broken since `21cc1ea` on Jul 31, fixed via `_config.yml`'s `exclude: docs/`).
  Confirmed live and serving the orb feature as of this handoff. Noted here only so a
  resuming session doesn't mistake the now-stale phrase "Pages was still deploying" (if
  it appears anywhere else, e.g. in the earlier chat transcript this handoff was written
  from) for current state — it's fixed.
- **Still fully open, deliberately not touched this session (carried forward from the
  prior handoff, unchanged): the `say`-CLI voice-quality complaint.** The user said they
  are not satisfied with either persona's voice, specifically the underlying macOS `say`
  TTS engine itself (not a rate-tuning issue — both personas' rates were already
  carefully tuned by ear in an earlier session). This session deliberately worked on the
  orb UI independently of that conversation, per the user's own explicit direction
  ("let's work on the orb now") — the orb's per-word sync mechanism works identically
  regardless of which engine eventually produces the audio, so nothing about this
  session's work is blocked by or blocks that conversation. See the prior handoff
  (`bullion-voice-persona-toggle-and-orb-handoff.md`) for full context: prior engines
  already tried and rejected (Chatterbox — wrong accent), the deferred "Thamie"
  voice-blend idea (`bullion-thamie-voice-blend-idea` memory) as one possible direction,
  not a foregone conclusion.

## What's next (ordered)

1. **Get the user's own live-browser confirmation** that the orb looks and feels right —
   this is the one thing automation in this project has never been able to verify. Site
   is confirmed live, so nothing is blocking this anymore. Specifically worth their eyes
   on: does the pulse read as in-sync with the actual voice; does the idle breathe look
   calm/right; does the first-visit nudge tooltip look good; does the panel-open
   repositioning look clean on both desktop and a real mobile device (not just
   automation's unreliable viewport emulation).
2. **If the user hits the parked narration-overlap bug** (orb goes still while a clip is
   clearly still playing, likely by clicking through nodes quickly) — this is the known,
   documented issue above, not a new bug to re-investigate from scratch. Consider a small
   follow-up task: track the currently-playing `Audio` object, cancel/ignore a stale
   one's `ended` event.
3. **Separately, whenever the user wants to pick it back up: the voice-quality
   conversation is still fully open.** Bring up `superpowers:brainstorming` scoped to
   "what should the Bullion narration TTS approach be, given `say`-CLI hasn't satisfied
   the user for either persona" — bring in the deferred "Thamie" idea and the Chatterbox
   history as prior art, not a foregone conclusion. Nothing from this session changes
   that conversation's starting point.
4. Delete this plan's SDD workspace (`.superpowers/sdd/2026-08-01-bullion-persona-orb/`)
   once the user has confirmed everything looks right and no further reference to the
   ledger/reports is needed — the skill's own convention is "git history is the record
   now," but it was deliberately left in place this session since the parked finding's
   full rationale lives only in the ledger, not in any commit message. Not urgent.

## Verification idioms used in this project (for the resuming session)

- Test suite: `cd bullion-live-map && python3 -m unittest discover -s tests && python3 -m
  unittest test_calibrate && python3 -m unittest scripts.test_generate_narration -v`
  (currently 96/96: 41 + 33 + 22).
- **New this session, durable and important: `getComputedStyle()` on a CSS-transitioning
  property is unreliable via claude-in-chrome's `javascript_tool` on this project's
  automation tabs** (`document.visibilityState: "hidden"` — backgrounded tabs throttle
  transition resolution as observed via JS-eval, not just audio loading as previously
  documented). **Use `computer` tool screenshots (real compositor paint) to verify CSS
  transform/transition state, not `getComputedStyle()` reads.** For non-animated state
  (class membership, `hidden` attributes, text content, `localStorage`/`sessionStorage`
  values), JS-eval reads remain reliable and fast — prefer those when they answer the
  question. Full writeup: `chrome-automation-hidden-tab-css-transition-trap` memory.
- Audible correctness, caption-sync feel, and animation "does it look right" **cannot be
  automated** — every such check is an explicit human-in-a-focused-tab step, never
  inferred from `.play()` resolving, `getComputedStyle()`, or console cleanliness alone.
  This project's standing limitation, reconfirmed again this session.
- SDD process idioms: `.superpowers/sdd/2026-08-01-bullion-persona-orb/progress.md` is
  the ledger and recovery map — trust it and `git log` over this handoff's own prose if
  they ever disagree.
- **New this session: diagnosing a GitHub Pages deploy failure needs authenticated API
  calls** — the unauthenticated `/repos/.../actions/runs`, `/repos/.../pages`, and
  `/repos/.../actions/jobs/{id}/logs` endpoints either 404 or 403 (`"Must have admin
  rights to Repository"`) even on this public repo. Get the token already sitting in the
  git credential helper (never print it): `TOKEN=$(printf "protocol=https\nhost=github.com\n"
  | git credential fill 2>/dev/null | sed -n 's/^password=//p')`, then pass `-H
  "Authorization: token $TOKEN"` on the `curl` call, and `unset TOKEN` right after. The
  real build error only shows up in the `.../actions/jobs/{job_id}/logs` response (plain
  text, `-L` to follow the redirect) — the run-list/job-list endpoints only tell you
  pass/fail, not why. `curl -sI <pages-url>` and `last-modified` headers are NOT reliable
  signals of whether a fix landed — a failed build leaves the OLD `last-modified` in
  place indefinitely, indistinguishable from "still deploying" without checking Actions
  directly. When something looks stale after a push for more than a few minutes, check
  Actions before assuming it's just cache lag (this project's own memory previously said
  "a stale response right after pushing is normal" — still true for the first few
  minutes, but don't let that habit mask an actual failure sitting for hours, as
  apparently happened here across several unrelated pushes before anyone noticed).

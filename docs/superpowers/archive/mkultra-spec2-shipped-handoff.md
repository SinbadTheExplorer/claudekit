# Bullion Mk Ultra — Spec 2 Shipped — Session Handoff

**Written:** 2026-07-28 · **For:** any future session touching `bullion_mkultra.html` — this
effort is DONE, not in progress; this handoff exists so a fresh session doesn't waste time
re-deriving what happened or, worse, re-doing it.

## Goal

The Mk Ultra "editorial identity pass" (Spec 2) — Times New Roman typography, a re-spaced
color palette, a "Bullion" wordmark/monogram, a signature drag cursor, two first-person field
notes, and a real WebGL/CDN fallback card — is **fully implemented, reviewed, pushed, and
confirmed live.** There is no open work on this specific effort.

- Spec: `docs/superpowers/specs/2026-07-28-bullion-mkultra-experience-design.md`
- Plan (all 6 tasks, exact code, verification harness): `docs/superpowers/plans/2026-07-28-bullion-mkultra-experience.md`
- Progress ledger: **deleted** — the SDD workspace (`.superpowers/sdd/2026-07-28-bullion-mkultra-experience/`)
  was removed after the final review went clean, per the subagent-driven-development skill's
  "Finish" step (git history is the record now). Do not look for it; it's gone by design, not
  by accident.
- Prior handoffs in this same effort (both git-tracked, left in place, read only if you need
  deeper history than this file gives): `docs/superpowers/mkultra-spec2-plan-handoff.md`
  (written right before implementation started) and `docs/superpowers/mkultra-spec2-brainstorm-handoff.md`
  (written mid-brainstorm, before the spec/plan existed).

## How to resume (do this first)

There is nothing to resume — this is a completion record, not a mid-work handoff. If you were
pointed here expecting unfinished work, re-check what the user actually wants; it's likely a
NEW effort on this file, not a continuation of Spec 2.

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline -1` should
   show `ec47e64` (or later, if more work has landed since) at HEAD on `main`. `git rev-list
   --left-right --count origin/main...main` should read `0  0` — **fully pushed, nothing
   local-only.**
2. Confirm live: `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mkultra.html`
   should serve the current file (was verified live within ~45s of push at the time this was
   written).
3. **Immediate next action:** none for this effort. If the user wants MORE done to Mk Ultra,
   treat it as a new effort — brainstorm it fresh rather than assuming it extends this plan.

## Current state (active files)

**Branch:** `main`, 0 commits ahead/behind `origin/main` — fully synced.

**Files changed by this effort (all committed, all pushed):**
- `bullion-live-map/bullion_mkultra.html` — the sole implementation target. 9 commits total
  across the effort: `0784f6b` (typography) → `cf43c4d` (palette) → `89d29d6` (wordmark) →
  `9bd5a42` (cursor) → `9bd4f0f` + `ea2f1ae` (field notes + a mid-task syntax-error fix, see
  below) → `4ed7174` (WebGL/CDN fallback) → `ec47e64` (final-review fix: fallback button width
  + coach-overlay suppression). Full range: `e23c955..ec47e64`.
- `docs/superpowers/mkultra-spec2-shipped-handoff.md` — this file (new, untracked as of
  writing).

**Files this effort deliberately did NOT touch (freeze-checked clean throughout, verify with
`shasum -a 256` if you ever suspect drift):** `bullion_mk11.html` through `bullion_mk18.html`.
These are frozen archives of past versions; `bullion_mkultra.html` is a separate experimental
3D fork seeded from `bullion_mk15.html` — see `[[project-bullion-live-map]]` memory for the
full versioning scheme if this is unfamiliar.

**Scratch workspace / traps:**
- ⚠️ The SDD workspace for this plan (`.superpowers/sdd/2026-07-28-bullion-mkultra-experience/`)
  is gone — deleted on purpose after a clean final review, per project convention. Don't be
  alarmed if you go looking for the task briefs/reports/ledger; they never existed outside that
  now-deleted directory, and their content (what was built, why, and every review verdict) is
  summarized in this handoff and in commit messages.
- ⚠️ **During this effort, headless-Chrome verification commands twice closed the user's actual
  Chrome browser window** when run without an isolated `--user-data-dir`. If you run headless
  Chrome against this file for any reason, always pass a dedicated
  `--user-data-dir=/tmp/<unique>` — see `[[sdd-dont-trust-implementer-verification-claims]]`
  memory for the full writeup.
- ⚠️ **A real bug shipped mid-effort and was caught/fixed within the same session**: commit
  `9bd4f0f` briefly broke the entire app (JS syntax error from straightened apostrophes inside
  single-quoted string literals — the plan's copy text used curly quotes `’` deliberately for
  exactly this reason). Fixed in `ea2f1ae`. If you ever `git bisect` into the range
  `9bd4f0f..ea2f1ae` (exclusive of `ea2f1ae`), expect the app to be broken at those specific
  commits — that's expected, not a sign your checkout is corrupt.

**Not mine — leave alone (pre-existing untracked noise, confirmed via `git status`):**
`docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`, `.codex/`,
`AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple), `bullion-live-map/__pycache__/`,
`bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`,
`docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md`. **Never `git add .`/`-A`.**

## What has changed

- All 6 planned tasks implemented, each passing an individual task-scoped review
  (spec-compliance + code quality) via `superpowers:subagent-driven-development`.
- One real bug (see above) caught and fixed within a task's fix loop before that task was
  marked complete.
- A final whole-branch review (dispatched on Opus) found 2 Important, 0 Critical issues — both
  cosmetic, both confined to the WebGL-unavailable fallback path added in the last task, both
  inherited from the plan's own spec rather than being implementer errors:
  1. The fallback card's "Open the Overview board" button inherited `.run-btn { width: 100% }`
     and spanned the entire stage instead of reading as a composed card.
  2. The beginner "coach" tutorial overlay ("Click any glowing dot...") stayed visible on top
     of the fallback card, instructing users to do something that's impossible on that screen.
  Both fixed in one follow-up commit (`ec47e64`): a scoped `#render-fallback .run-btn { width:
  auto; ... }` CSS override, and a `dismissCoach()` call inside `showRenderFallback()`. A scoped
  re-review confirmed both addressed with no new breakage.
- Pushed to `origin/main`, confirmed live on GitHub Pages.
- Python test suite re-run as a sanity check post-implementation: `discover -s tests` = 41/41,
  `test_calibrate` = 33/33 — both unaffected, as expected for a pure HTML/CSS/JS change.

## What has failed / risks / caveats

- **Nothing is currently failing.** The one thing that failed mid-session (the syntax error in
  `9bd4f0f`) was caught and fixed before the task was marked complete; the shipped state has no
  known defects.
- **UNVERIFIED / deliberately deferred (Minor, not blocking, logged for future reference):**
  - `shadow` vs `fx` remains the tightest pair in the re-spaced palette (ΔE76 ≈ 13.6 — above the
    ~10 "confusable" floor but below the ~20 comfort margin for small swatches). The plan
    pre-flagged this exact pair as a watch item; it was visually confirmed distinguishable but
    is the one to revisit first if palette complaints ever surface.
  - `hasWebGLSupport()` (in the `Renderer` IIFE) creates a throwaway canvas + WebGL context to
    probe support and never releases it. Currently harmless — `build()` has exactly one call
    site in the whole app — but would leak a context if `build()` ever became re-entrant.
  - `#brand-eyebrow` hardcodes the sans-serif font stack as a duplicate magic string instead of
    a `--font-ui` token (the pairing itself — serif wordmark, sans eyebrow — is intentional and
    correct; only the lack of a shared token is the nit).
  - `#render-fallback` has no `aria-live`/`role="status"` — a screen-reader user gets no
    announcement when it's injected asynchronously after a failed load.
- **Nothing overrides the plan.** All brainstorm decisions (scope, Times New Roman, Approach A,
  warm/tactile direction) shipped as specified; the field-note copy was implemented as the
  user's approved draft (they may still want to hand-edit the wording themselves — that was
  always expected, see the spec/plan for the "draft, not precious" framing).

## What's next (ordered)

Nothing is queued. If the user asks for more work on this file:
1. Treat it as a new effort — use `superpowers:brainstorming` first rather than assuming it's a
   continuation of this plan.
2. If it turns out to be small polish on the Minor/deferred list above, it's fine to skip
   brainstorming and just fix directly with the user's go-ahead — but confirm with them which
   item(s) they mean rather than batch-fixing the whole list unprompted.

## Verification idioms used in this project (for the resuming session)

- **Real headless-Chrome DOM probes, always with an isolated `--user-data-dir`:**
  ```bash
  rm -rf /tmp/<probe-dir> && mkdir -p /tmp/<probe-dir>
  cp bullion-live-map/bullion_mkultra.html bullion-live-map/data.json /tmp/<probe-dir>/
  # inject a <script> before the LAST </body> — Python str.rfind('</body>'), not find();
  # there's a decoy </body> earlier in a JS string.
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --headless=new --allow-file-access-from-files --virtual-time-budget=15000 \
    --enable-logging=stderr --v=1 \
    --user-data-dir=/tmp/<unique-profile-dir> \
    [--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader   # only for the WebGL-available path
     | --disable-gpu]                                                     # for the no-WebGL path
    "file:///tmp/<probe-dir>/bullion_mkultra.html" 2>chrome.log
  grep "PROBE_\|SyntaxError\|Uncaught\|ReferenceError" chrome.log
  ```
- **Do not trust an implementer/agent report that substitutes grep/regex/static-analysis for
  this real probe** — see `[[sdd-dont-trust-implementer-verification-claims]]` memory. This is
  the single most important lesson from this effort.
- **NEVER call `openAuditLog()`** in a probe — its animated modal stalls headless virtual-time
  and hangs the run. macOS has no `timeout` command; use a background PID + `sleep N && kill`
  pattern instead if a run might hang.
- **Freeze check:** `shasum -a 256 bullion_mk15.html bullion_mk16.html bullion_mk17.html
  bullion_mk18.html` before and after any work on `bullion_mkultra.html` — all four hashes must
  match both times.
- **Python suite:** `cd bullion-live-map && python3 -m unittest discover -s tests && python3 -m
  unittest test_calibrate` — unrelated to this HTML file's JS but worth a sanity run after any
  change, since both live in the same directory.
- **git push** works directly from the Bash tool (`GIT_TERMINAL_PROMPT=0 git push origin
  main`); `gh` is NOT installed, use raw `curl` + credential-store token if a GitHub API call is
  ever needed.

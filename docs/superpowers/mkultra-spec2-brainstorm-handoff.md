# Bullion Mk Ultra — Spec 2 Brainstorm — Session Handoff

**Written:** 2026-07-27 · **For:** a fresh session resuming the Spec 2 ("Mk Ultra experience
pass") design brainstorm mid-flight. Nothing has been implemented or written to a spec file yet —
this handoff **is** the record of what was decided in conversation. Prior handoff:
`docs/superpowers/honesty-pass-handoff.md` (defines Spec 2's original 4-part scope in its
"What's next" section).

## Goal

Spec 1 (the "honesty pass") shipped as `bullion_mk18.html` and is live. Spec 2 is the **Mk Ultra
experience pass** — visual/UX work on the 3D fork (`bullion_mkultra.html`) only. The user's ask
that started this session: integrate the `impeccable`/`frontend-design`/`ui-ux-pro-max` skills so
Mk Ultra stops feeling like a generic AI-generated dark-fintech-dashboard template and instead
feels intentionally designed, with a personal touch. We are running this through
`superpowers:brainstorming` per the project's process convention.

- Prior handoff (defines original 4-part Spec 2 scope: legibility / visual elevation / motion /
  WebGL fallback): `docs/superpowers/honesty-pass-handoff.md`
- **No spec file exists yet.** The brainstorming skill's "present design in sections" step is
  in progress (Section 1 of 6 approved) — nothing has been written to
  `docs/superpowers/specs/` yet.
- No SDD progress ledger for this effort (nothing has been built).

## How to resume (do this first)

1. Confirm branch state: `git -C ~/claude-projects/claudekit log --oneline -3`
   should show `3bfc9e5` (or later) at HEAD on `main`; `git rev-list --left-right --count
   origin/main...main` should read `0  0`.
2. **Do not re-run `superpowers:brainstorming`'s clarifying-questions step** — all the
   decisions it would ask for are already locked below. Resume directly at "present design
   in sections," starting from Section 2.
3. Re-read the "Decisions locked" list below before saying anything — it overrides re-asking.
4. **Immediate next action:** present **Section 2 — Color palette** of the design (see "What's
   next" #1) to the user, get approval, then continue through Sections 3–6 in order.

## Current state (active files)

**Branch:** `main`, 0 commits ahead/behind `origin/main`. No tracked file has been modified by
this effort — it is pure conversation so far.

**Files created / changed:** none yet, other than this handoff itself (once committed).

**Files later work will modify (untouched so far):**
- `bullion-live-map/bullion_mkultra.html` — the sole implementation target. Spec 2 is scoped to
  Mk Ultra ONLY — do not touch `bullion_mk18.html` or any frozen `mk11..17` file.
- `bullion-live-map/fonts/` (does not exist yet) — planned location for a self-hosted Fraunces
  `.woff2` subset (see decisions below).

**Scratch workspace / traps:**
- ⚠️ **No spec document exists for this effort yet.** Do not search for
  `docs/superpowers/specs/*mkultra-experience*` — it hasn't been written. This handoff file is
  the only durable record of the brainstorm until the spec is written (What's next #6).
- ⚠️ Early in this session the user asked about "Anthropic design" thinking it might be a skill
  name — **no such skill exists** (closest matches: `frontend-design`, `impeccable`, the
  `ui-ux-pro-max` family). This was resolved as a misunderstanding and explicitly dropped from
  the design direction — don't reintroduce a literal "Anthropic branding" reading.
- ⚠️ The `GROUP_COLOR` hex values cited under "Decisions locked" were read live from
  `bullion_mkultra.html:697-710` on 2026-07-27. Re-verify with `grep -n "GROUP_COLOR" -A14
  bullion_mkultra.html` if resuming much later in case the file changed underneath this handoff.

**Not mine — leave alone (pre-existing untracked noise, confirmed via `git status`):**
`docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`, `.codex/`,
`AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple), `bullion-live-map/__pycache__/`,
`bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`, and `docs/superpowers/
mk12-handoff.md` (older handoff, tracked — see step 4 below). **Never `git add .`/`-A`.**

## What has changed

Nothing has shipped. This is a pre-implementation design brainstorm; the only output so far is
this handoff and the decisions recorded in it.

## What has failed / risks / caveats

- **Nothing has failed.** No code has been touched.
- **UNVERIFIED:** N/A — nothing implemented yet to verify.
- **Decisions locked this session (do not silently re-ask or override):**
  - **Scope = visual elevation + personal touch + the WebGL/CDN fallback bug fix only.**
    Explicitly **excludes** (a) beginner legibility and (c) motion/micro-interaction polish from
    the original 4-part Spec 2 scope — both deferred to a separate follow-up spec.
  - **Approach chosen: "A — Editorial identity pass"** (of three proposed: A editorial identity,
    B component-by-component craft pass, C full masthead rebrand). B and C were declined.
  - **Visual direction: "Warm, tactile, hand-finished"** (chosen over "calm, editorial,
    restrained" and "precision instrument / terminal").
  - **"Personal touch" defined as:** signature visual details + reflecting the user's own
    learning journey. Explicitly **not primarily** about copy/voice tone (that option was
    offered and not selected, though incidental copy touches are fine).
  - **Typography (Section 1, approved):** self-host **Fraunces** (variable-weight display serif)
    for the `<h1>` wordmark, node-detail titles, and coach-card headings — extends the
    Georgia-serif feel already used in `preview-card.png`. Keep the existing system sans
    (`-apple-system, Segoe UI, Roboto`) for dense UI/live-data numbers. Ship as same-origin
    `.woff2` file(s) under `bullion-live-map/fonts/` — CSP already allows `font-src 'self'`, so
    **no CSP change needed**; deliberately avoided an external font CDN so Mk Ultra doesn't pick
    up a second CDN dependency on top of the existing Three.js/jsDelivr one. Subset to the
    glyphs actually used (headings only) to keep the file small.
  - **Palette problem to fix in Section 2** (grounded, not yet designed): `GROUP_COLOR` in
    `bullion_mkultra.html:697-710` has `monetary:#b79be0`, `commercial:#8f9ee0`,
    `shadow:#b586c8` — three purples within a few degrees of hue/lightness of each other — plus
    `sovereign:#7fb4e0` and `fx:#8fb0c8` crowding the same blue-purple band. This is the concrete
    input for the still-pending Section 2 proposal.

## What's next (ordered)

1. **Present Section 2 — Color palette.** Propose a refined palette that separates the 12
   `GROUP_COLOR` swatches (fixing the purple/blue crowding above) while staying inside the
   "warm, tactile" direction — get user approval.
2. **Section 3 — Header / brand mark.** Small custom monogram/wordmark treatment, reusing
   `preview-card.png`'s Georgia-serif "Bullion" as the seed identity.
3. **Section 4 — Signature personal-touch details.** 2–3 hand-written "field note" annotations
   on nodes the user personally found surprising while building this, plus one signature
   interaction detail (e.g. a custom hover/cursor state on the 3D globe).
4. **Section 5 — WebGL/CDN fallback.** Replace the current silent black void (when WebGL is
   unavailable) with an explanatory card that drops to the existing 2D Overview board.
5. **Section 6 — Testing / verification approach.** Reuse this project's headless-Chrome probe
   idiom (see below) — note Mk Ultra specifically needs the software-WebGL flags.
6. **Write the design doc** to `docs/superpowers/specs/2026-07-27-bullion-mkultra-experience-
   design.md` (or later date if resumed on a different day), commit it, run the brainstorming
   skill's spec self-review (placeholders / contradictions / scope / ambiguity), then ask the
   user to review the written spec file.
7. **On user approval, invoke `superpowers:writing-plans`.** Do not invoke `frontend-design`,
   `impeccable`, or any other implementation skill directly — writing-plans is the mandated next
   step per the brainstorming skill's terminal state.

## Verification idioms used in this project (for the resuming session)

- **Python tests:** `cd bullion-live-map && python3 -m unittest discover -s tests` (41/41 as of
  the honesty pass) and `python3 -m unittest test_calibrate` (33/33, top-level not in `tests/`).
- **Headless probe (the workhorse here):** copy the html + `data.json` to a temp dir, inject a
  `<script>` before the **last** `</body>` (use `rfind` — there's a decoy `</body>` inside a JS
  string), run Chrome with `--headless=new --allow-file-access-from-files
  --virtual-time-budget=15000 --enable-logging=stderr --v=1`, grep `PROBE_` tags from stderr.
  macOS has no `timeout`. **NEVER call `openAuditLog()`** in a probe — its animated modal stalls
  headless virtual-time and hangs.
  - **Mk Ultra specifically needs software WebGL:** add `--use-gl=angle
    --use-angle=swiftshader --enable-unsafe-swiftshader`, or the globe renders blank — this
    matters even more for this effort since Section 5 is directly about the no-WebGL path.
- **Freeze check:** `shasum -a 256 bullion_mk15.html bullion_mk16.html bullion_mk17.html
  bullion_mk18.html` before and after any change — Spec 2 must not touch these.
- **Confirm a push landed:** trust `git show origin/main:<path>`; a brand-new URL can 404 for
  ~30–90s while Pages rebuilds.
- **git push** works directly from the Bash tool (`GIT_TERMINAL_PROMPT=0 git push origin main`);
  `gh` is NOT installed — use raw `curl` + the credential-store token for any GitHub API calls.

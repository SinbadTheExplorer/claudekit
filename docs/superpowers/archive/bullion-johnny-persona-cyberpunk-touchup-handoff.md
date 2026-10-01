# Bullion Narration — Johnny Persona Skill + Cyberpunk-Researched Script Rewrite — Session Handoff

**Written:** 2026-08-03 · **For:** any future session resuming this work — this is a new
thread of work, not a direct continuation of the narration-audio-quality thread the prior
two handoffs covered, though it touches the same files. Nothing is blocking; this is a
"here's what changed and what to spot-check" handoff.

## Goal

The user asked for a reusable, general-purpose (personal, cross-project) skill capturing
Johnny's voice/persona, then asked for that skill to be deepened with real Cyberpunk 2077
research, then asked to apply the improved voice back into this project's actual Johnny
narration scripts and regenerate the audio at a new tempo. No spec/plan/SDD ledger exists
for this thread — handled fully inline, same "small work stays inline" posture as every
prior ad-hoc narration/tuning session in this project.

- Prior handoff (audio-quality/regen-mechanics thread, unrelated content but same files):
  `docs/superpowers/bullion-narration-regen-complete-caption-fix-handoff.md` — still valid
  background on the regen pipeline itself, not superseded by this session.
- Older handoff (this session archived it — see "Current state"):
  `docs/superpowers/archive/bullion-review-fixes-audio-regen-handoff.md`
- **New personal skill (NOT part of this git repo):**
  `~/.claude/skills/johnny-persona/SKILL.md` — the actual deliverable of the first half of
  this session. Cross-project, available in any future Claude Code session on this machine.
  A resuming session should **read this file directly** for the full voice-writing
  guidelines; it is the source of truth for Johnny's voice, not this handoff.

## How to resume (do this first)

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline
   cfbe7fc..HEAD` should show exactly **2 commits**, `f0b3ada` (not from this session — the
   user committed the pre-existing `narration-regen-workflow` skill directly) then `62a83eb`
   (this session's work), on `main`, **pushed** (`git log --oneline origin/main..HEAD`
   empty), GitHub Pages deploy for `62a83eb` **confirmed** `completed`/`success` via the
   public Actions API. `git status --short` clean except the standing "Not mine" untracked
   noise (list below) plus two marker files from this session's regen (also below).
2. Read this handoff in full — it's self-contained, no ledger to cross-check.
3. Read `~/.claude/skills/johnny-persona/SKILL.md` if you're about to write MORE Johnny
   lines — don't re-derive voice rules from the examples in this handoff alone.
4. **Immediate next action: none blocking.** The one open item worth doing is a real-browser
   check of the new disclaimer UI (never visually confirmed this session — see "What has
   failed / risks / caveats").

## Current state (active files)

**Branch:** `main`, HEAD at `62a83eb`, 2 commits ahead of `cfbe7fc`, **pushed**, deploy
**confirmed** `completed`/`success`, clean tree (modulo standing untracked noise below).

**Committed and pushed (`62a83eb`, 53 files):**

- **`bullion-live-map/scripts/generate_narration.py`** —
  - All 39 `JOHNNY_SCRIPTS` entries and all 11 `EVENT_JOHNNY_SCRIPTS` entries rewritten to
    use a wider Cyberpunk-2077-researched vocabulary (see skill file for the full trait
    list): `eddies` (money), `gonk` (idiot), `zero`/`zeroed` (kill/wipe out), `ganic`
    chrome (organic vs. synthetic contrast, used on the `gold` node), `screamsheet`
    (newspaper/headlines), `edgerunner` (used for private-credit funds). Every real
    number/fact from the original scripts was preserved exactly — only the framing/flavor
    language changed.
  - Per the user's explicit feedback partway through: **removed `delta`** (2 occurrences,
    in `dxy_fx` and the `usd_shock` event — user found it too deep-cut/unclear) and
    **reduced `choom` from 16 occurrences to 8** (kept the strongest placements: `fed`,
    `repo`, `gse`, `gold`, `house`, `vix`, `ai_analysis` event, `rate_hike` event).
  - `JOHNNY_TEMPO` changed `0.95` → `0.92`, sampled first via the documented monkey-patch
    convention (`~/.claude/skills/narration-regen-workflow/SKILL.md`'s "Sample before you
    commit" section) against the `"banks"` reference node, confirmed by ear by the user
    ("sounds good") before the tracked constant was actually edited.
- **`bullion-live-map/bullion_mk18.html` + `bullion-live-map/bullion_mkultra.html`** —
  - `JOHNNY_SCRIPTS`/`EVENT_JOHNNY_SCRIPTS` JS consts mirrored byte-for-byte from the
    Python source (generated programmatically from the Python dicts, not hand-copied, to
    guarantee the parity tests pass).
  - **New feature:** a one-time Cyberpunk-2077 attribution disclaimer near `#persona-orb`.
    New CSS class `.orb-johnny-disclaimer` (same positioning pattern as the existing
    `.orb-nudge-tip`, but wraps text instead of `nowrap`, `width: 220px`). New HTML element
    `<div class="orb-johnny-disclaimer" hidden>...</div>` inside `#persona-orb`, sibling of
    the existing `.orb-nudge-tip`. New JS function `maybeShowJohnnyDisclaimer()`, called
    from `toggleNarrationPersona()` only when switching **to** Johnny, gated by
    `localStorage.getItem('bullion-johnny-disclaimer-seen')` (persistent, not
    `sessionStorage` — shows **once ever per browser**, not once per session), auto-hides
    itself after 9 seconds via `setTimeout`. Text: *"Johnny's voice/attitude is a nod to
    Cyberpunk 2077's Johnny Silverhand — cynical, rough language. Tap the orb anytime to
    switch back to Alfred."*
- **All 50 `bullion-live-map/audio/narration/johnny-*.mp3`** (39 node + 11 event) —
  regenerated fresh at `JOHNNY_TEMPO=0.92` against the rewritten scripts.

**New personal skill (uncommitted, outside this repo, not tracked by this project's git):**

- `~/.claude/skills/johnny-persona/SKILL.md` — created this session, then revised once
  after Cyberpunk 2077 research (genre Wikipedia page + Johnny Silverhand Wikipedia page +
  a Night City slang glossary + a Silverhand-quotes roundup, all via WebFetch/WebSearch).
  Tested RED→GREEN with fresh subagents both times (baseline drift without the skill vs.
  compliant output with it) — both verification runs are described in this handoff's chat
  history, not re-summarized here. This is a **personal** skill (lives in
  `~/.claude/skills/`, not `bullion-live-map/.claude/skills/` or this repo), so it's
  available to any future project on this machine, not just `claudekit`.

**Scratch workspace / traps:**

- ⚠️ `bullion-live-map/audio/narration/raw_cache_johnny/` now has all **50** entries (one
  raw pre-atempo `.wav` per Johnny clip, from this session's regen). Same trap as always:
  **keyed by output filename only, not content-hashed.** If any Johnny script's TEXT is
  edited again in a future session without a corresponding tempo/rate change, the cache
  will silently serve THIS session's audio at whatever new tempo is set — delete the
  specific `raw_cache_johnny/<id>.wav` first. All 50 are gitignored, not shipped.
- ⚠️ `bullion-live-map/audio/narration/.regen_2026-08-02_v2_done.txt` — untracked marker
  file, now has all **100** entries again (39+11 Alfred, 39+11 Johnny — Alfred untouched
  this session, Johnny fully redone). Fully done/stale as of this handoff. A future
  Johnny-only change needs this file's `johnny-*`/`event-johnny-*` lines stripped first (see
  `~/.claude/skills/narration-regen-workflow/SKILL.md`'s "Full regen" section) or nothing
  will regenerate.
- ⚠️ `bullion-live-map/audio/narration/.johnny_tempo90_done.txt` — older, unrelated,
  pre-existing stale marker from an earlier session (noted in a prior handoff too). Still
  inert, still untouched this session, still safe to ignore.
- ⚠️ **This session's regen hit heavy, repeated memory-pressure stalls** — 5 separate
  kill/pkill-and-resume cycles were needed across two regen passes (the initial full
  39+11-clip batch, then a smaller 10-clip targeted re-regen after the choom/delta wording
  fix landed). Root cause identified via `top -o mem`: a long-running, unrelated
  `open-webui serve` process (PID varies, ~1.7GB+ resident, running 3+ days uninterrupted)
  plus normal browser memory usage were already eating into this 8GB machine's headroom
  before ChatterboxTTS ever loaded — **not** a bug in `regen_narration_v2.py` or a new
  leak. The existing `narration-regen-workflow` skill documents this class of stall as
  something that's happened once before; this session hit it five times in a row on the
  same run. The kill-and-resume procedure it documents (`pkill -f
  "scripts/regen_narration_v2.py"`, wait, re-run — safe because of the marker file) worked
  every time, just needed repeating. **Not fixed, not investigated further** — the user was
  asked once whether to keep auto-retrying, close other apps, or pause, and chose
  auto-retry; that's what happened.
- **Not mine — leave alone** (same standing list as every prior handoff, unchanged):
  `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`, `.codex/`,
  `.superpowers/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple),
  `bullion-live-map/__pycache__/`, `bullion-live-map/scripts/__pycache__/`,
  `bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`, the other tracked
  handoffs in `docs/superpowers/` (`honesty-pass-`, `mk12-`, `mkultra-spec2-brainstorm-`,
  `mkultra-spec2-plan-handoff.md`), and the untracked plan/spec docs under
  `docs/superpowers/plans/` and `docs/superpowers/specs/` noted in the prior handoff.
  **Never `git add .`/`-A`** — this session staged only the specific 53 changed files by
  glob (`generate_narration.py`, both HTML files, `johnny-*.mp3`).

## What has changed

- Created `~/.claude/skills/johnny-persona/SKILL.md` (personal skill), verified with a
  baseline (no-skill) subagent run and a with-skill subagent run showing clear improvement.
- Researched Cyberpunk 2077 (genre Wikipedia, Johnny Silverhand Wikipedia, a Night City
  slang glossary, a Silverhand-quotes roundup) and folded findings into the skill: genre
  grounding ("high tech, low life," noir, alienated-antihero-vs-megacorp), a "design not
  accident" cynicism-framing trait, humor-plus-anger balance, and an explicit
  do-not-copy-Silverhand's-actual-lines note. Re-verified with a third subagent run.
- Rewrote all 39 node + 11 event Johnny scripts in `generate_narration.py` using the
  researched vocabulary, preserving every original fact/number.
- Per user feedback: removed `delta` entirely, cut `choom` roughly in half, added the
  one-time Cyberpunk-2077 disclaimer UI to both HTML files.
- Retuned `JOHNNY_TEMPO` 0.95 → 0.92 (sampled and confirmed by ear first).
- Regenerated all 50 Johnny clips at the new tempo/scripts (two passes: the full 50, then a
  targeted 10-clip re-regen after the delta/choom wording fix invalidated those 10 clips'
  cached audio).
- All tests green throughout: `python3 -m unittest discover -s tests` (41),
  `python3 -m unittest test_calibrate` (33), `python3 -m unittest
  scripts.test_generate_narration -v` (34) — **108/108**, checked after every content
  change in this session, not just once at the end.
- Listening passes: all 11 event clips + 9 spot-checked node clips after the first full
  regen (user: "sounds good"), then all 10 wording-fix-affected clips after the second
  targeted regen (user: "good" — moved straight to commit).
- Committed `62a83eb` (53 files: 50 mp3 + `generate_narration.py` + both HTML files),
  pushed to `origin/main`, GitHub Pages deploy confirmed `completed`/`success`.
- Archived `bullion-review-fixes-audio-regen-handoff.md` to `docs/superpowers/archive/`
  (untracked, dropped out of the top-2-most-recent by writing this handoff).

## What has failed / risks / caveats

- **Nothing has failed in the final shipped state.** All 108 tests pass, commit and push
  succeeded, deploy confirmed live.
- **UNVERIFIED: the new Cyberpunk-2077 disclaimer UI was never visually confirmed in a real
  browser.** It was code-reviewed (CSS/HTML/JS added by hand, positioning modeled on the
  existing `.orb-nudge-tip` pattern) but no headless-Chrome probe or `claude-in-chrome`
  check ran this session. This project's own docs flag headless Chrome as unreliable on
  this machine right now — a live/manual browser check is the recommended next step, not a
  headless one (see "What's next").
- **UNVERIFIED (partial): not literally all 39 node clips got an individual human listening
  pass.** All 39 got fresh audio and all pass the nonempty/exists tests, but the listening
  passes covered 11 events + ~19 distinct node clips across both rounds (some overlap
  between the two rounds' spot-checks), not a full 39-clip pass. The user confirmed both
  rounds as sufficient ("sounds good" / "good") rather than asking for more coverage.
- **Repeated memory-pressure stalls during regen** — see "Scratch workspace / traps" above.
  Not a code bug; flagged as a machine-level condition (an unrelated long-running
  `open-webui serve` process) that will likely recur on future narration regens on this
  same machine until that process is closed or the machine gets more RAM. Nobody asked for
  that process to be touched, so it wasn't.

## What's next (ordered)

1. **Open `bullion_mkultra.html` (and/or `bullion_mk18.html`) in a real, non-headless
   browser.** If `bullion-johnny-disclaimer-seen` is already set in this machine's browser
   profile from earlier testing, clear it first (`localStorage.removeItem
   ('bullion-johnny-disclaimer-seen')` in DevTools console, or a fresh profile) so the
   one-time disclaimer actually fires. Switch to Johnny for the first time and confirm: the
   disclaimer tooltip renders above the orb, text wraps legibly within ~220px, it doesn't
   clip off-screen in either the centered-orb state or the `orb-docked` fallback state (only
   relevant in `bullion_mkultra.html`), and it auto-hides after ~9 seconds.
2. Optional, low priority: a broader listening pass on the ~20 node clips not individually
   spot-checked this session, if the user wants full-coverage confidence rather than the
   sampled confirmation already given.
3. If a future narration regen on this machine hits the same repeated memory-pressure
   stalls, consider updating `~/.claude/skills/narration-regen-workflow/SKILL.md`'s
   "Memory-safety / timing expectations" section with this session's finding (the
   `open-webui` process, the `top -o mem` diagnostic command, and the "may take several
   kill/resume cycles, not just one" reality) — not done this session, just an open idea.
4. No other blocking work.

## Verification idioms used in this project (for the resuming session)

- Test suite: `cd bullion-live-map && python3 -m unittest discover -s tests &&
  python3 -m unittest test_calibrate && python3 -m unittest scripts.test_generate_narration
  -v` (plain `python3`) — **41 + 33 + 34 = 108**, all green as of this handoff.
- Real generation / regen mechanics: see `~/.claude/skills/narration-regen-workflow/SKILL.md`
  (sample-before-commit monkey-patch pattern, marker-file resume mechanics, raw-WAV cache
  staleness trap) — this session followed it throughout, including the "ask the user before
  skipping the mandatory listening-pass gate" rule (never invoked; the gate was honored both
  rounds).
- **New idiom this session — diagnosing a stalled regen:** `sysctl vm.swapusage` (swap
  pinned near its total = likely stall) and `top -l 1 -o mem -n 8` (shows top memory
  consumers system-wide, not just this project's own processes) — this is how the
  `open-webui` finding was made. `ps aux | grep regen_narration_v2` process state `U`
  (uninterruptible sleep) with an unchanging CPU-time delta across 2+ checks a few minutes
  apart is the practical "it's actually stuck, not just slow" signal; state `R` with
  growing CPU time means it's still working even if the visible iteration count looks slow.
- Johnny voice/persona writing: invoke the **`johnny-persona`** skill via the Skill tool
  (personal skill, works in any project) rather than re-deriving voice rules — it has the
  full trait list, do/don't table, and Cyberpunk 2077 sourcing this handoff only
  summarizes.
- `afplay <path>` for listening passes — this machine plays audio directly through the
  Bash tool since it's the user's own local session.
- `git push` works directly from the Bash tool (`GIT_TERMINAL_PROMPT=0 git push origin
  main`); `gh` is NOT installed — deploy verification uses the public Actions API:
  `curl -s "https://api.github.com/repos/SinbadTheExplorer/claudekit/actions/runs?per_page=5"`.

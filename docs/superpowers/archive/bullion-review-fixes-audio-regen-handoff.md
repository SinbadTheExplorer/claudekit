# Bullion Narration Review Fixes — Board Dimming, Event Narration, Audio Regen — Session Handoff

**Written:** 2026-08-02 · **For:** any future session resuming this work — continues
directly from `bullion-narration-ui-review-fixes-handoff.md` (that session shipped items
1/2/3/6 of the user's 8-item review list, committed at `a4b2838`, NOT pushed, and flagged
items 4/5/7/8 as not started). This session finished items 4 and 8, made the code-side
edits for items 5/7, kicked off the (large, slow) audio regeneration those two items
require, committed and pushed everything, and is handing off with the regen **only
54/100 clips done**.

## Goal

The user tested the live map and gave an 8-item visual/sound review list (reproduced
verbatim in the prior handoff, `docs/superpowers/bullion-narration-ui-review-fixes-handoff.md`,
under "The original review list"). This session's job was to pick up items 4, 5, 7, 8
where the prior session left off. No spec/plan/SDD doc exists for this work — handled as
direct review-feedback fixing, same posture as prior ad-hoc tuning sessions in this project.

- Prior handoff (items 1/2/3/6 shipped, items 4/5/7/8 scoped): `bullion-narration-ui-review-fixes-handoff.md`
- Older handoff (Johnny expanded to 39 nodes, tempo mechanism): `bullion-johnny-full-39-nodes-handoff.md`
  — this session archived it to `docs/superpowers/archive/` (see "Current state" below);
  still valid background, just no longer top-2-most-recent.
- No spec/plan/SDD ledger for this session's work either.

## How to resume (do this first)

1. Confirm state: `git -C ~/claude-projects/claudekit log --oneline
   a4b2838..HEAD` should show exactly **1 commit, `a3a58e7`**, on `main`, already **pushed**
   (`git log --oneline origin/main..HEAD` empty). `git status --short` clean except the
   standing "Not mine" untracked noise (list below) plus two NEW untracked files this
   session added on purpose (also below).
2. Read this handoff in full. The original 8-item review list lives in the prior handoff
   (`bullion-narration-ui-review-fixes-handoff.md`, "The original review list" section) —
   re-read it there rather than duplicating it here.
3. **Immediate next action:** resume the audio regen. Marker file
   `bullion-live-map/audio/narration/.regen_2026-08-02_v2_done.txt` currently has **54
   entries**; the resumable driver script is at
   `bullion-live-map/scripts/regen_narration_v2.py` (untracked — copied there THIS session
   specifically so it wouldn't be lost like the prior session's scratchpad-only driver was;
   see "Scratch workspace / traps"). Run:
   `cd bullion-live-map && .venv-narration/bin/python3 scripts/regen_narration_v2.py`
   It picks up from the marker file automatically — safe to just re-run.

## Current state (active files)

**Branch:** `main`, 1 commit ahead of the prior handoff's base `a4b2838` (`a3a58e7`),
**already pushed**, clean tree (modulo standing untracked noise + 2 new untracked files
below).

**Committed and pushed in `a3a58e7`:**

- **Item 4 (2D board dimming) — done in BOTH `bullion_mk18.html` AND
  `bullion_mkultra.html`** (the user explicitly asked for mkultra too, mid-session, after
  I'd only done mk18 per the prior handoff's scoping — mkultra also has an Overview board
  and had the identical gap). `.board-card.dimmed { opacity: 0.12 }` mirrors
  `.node-g.dimmed`. mk18: `focusNode(id)`/`clearFocus()` (the existing D3-`.classed()`
  functions) now also toggle `.board-card` dimmed state via a `keep` set built from
  `neighborsOf`. mkultra: same, but `focusNode(id)`/`clearFocus()` wrap `Renderer.focus()`/
  `Renderer.clearFocus()` (WebGL mesh opacity) which don't expose their internal `keep` set,
  so the outer function independently computes its own `keep = new Set([id,
  ...(neighborsOf[id]||[])])` to drive the board-card classing. Both files: board cards now
  get `card.dataset.id = n.id`, click handlers `stopPropagation()` + set `stickyFocusId` +
  call `focusNode()` before `openDetail()`, and a new `#board-view` click listener (fires
  only when a click reaches the view itself, since card clicks stop propagation) mirrors
  each file's existing background-click deselect (`svg.on('click',...)` in mk18,
  `handleBackgroundClick()` in mkultra).
- **Item 8 (new voice lines) — scripted + wired, NOT fully generated yet.** All 10
  scenario/dropdown triggers (`rate_hike`, `vix_spike`, `cpi_rise`, `usd_shock`,
  `bank_stress`, `fiscal_stimulus`, `fiscal_tightening`, `geo_conflict`, `trade_war`,
  `deregulation` — all 10, not just the 5 quick-shock buttons, since all 10 route through
  the same `triggerShock(type)`) plus the AI-analysis button got short Alfred (factual
  butler) + Johnny (chrome-punk) flavor lines. New in `generate_narration.py`: `EVENT_IDS`,
  `EVENT_ALFRED_SCRIPTS`, `EVENT_JOHNNY_SCRIPTS` (11 entries each). New in both HTML files
  (byte-identical block inserted right after `JOHNNY_SCRIPTS`/`NARRATION_LINKS`):
  `EVENT_NARRATION_MANIFEST`, `EVENT_ALFRED_SCRIPTS`, `EVENT_JOHNNY_MANIFEST`,
  `EVENT_JOHNNY_SCRIPTS`, `resolveEventNarration(eventId)`, `playEventNarration(eventId)`.
  Wired: `triggerShock(type)` calls `playEventNarration(type)` right after `updateMetrics()`;
  `runAIAnalysis()` calls `playEventNarration('ai_analysis')` as its first line (fires
  immediately on click, not gated on the network round-trip). Deliberately generic/
  non-data-dependent lines (no static audio file could vary by numeric result).
  **AI content is NOT data-dependent — always the same clip regardless of the analysis
  outcome.**
- **Items 5+7 (loudness + rate/tempo) — code done, is what's driving the regen.** In
  `generate_narration.py`: `ALFRED_RATE` 218→213 ("Alfred too fast"), `JOHNNY_TEMPO` 0.9→0.95
  (user gave this exact value directly, not the 0.9→1.0 the prior handoff had guessed —
  **0.95 is confirmed correct, not an interpretation**). `LOUDNORM_FILTER =
  "loudnorm=I=-20:TP=-2:LRA=7"` added to `synthesize()`'s final ffmpeg encode and chained
  after `atempo={JOHNNY_TEMPO}` in `synthesize_johnny()`'s. These target values are
  unchanged from the prior handoff's own measurement (Alfred ~-20 LUFS, Johnny ~-32 LUFS on
  3 sample pairs).
- `test_generate_narration.py`: new `TestEventNarration` class (10 tests) guarding the new
  event-narration structures the same way `TestManifestCompleteness`/`TestJohnnyPersona`
  guard the per-node ones — ID-set completeness, Python/JS text parity (both HTML files),
  and per-clip file-existence. Also added a generic `_double_quoted_dict_from_html()` helper
  (parallel to the existing `_johnny_scripts_from_html()`, parametrized by const name).
- 43 audio clips regenerated at the new rate/tempo/loudnorm: **all 39 Alfred node clips**
  (`node-*.mp3`) + 4 Johnny node clips (`sec`, `cftc`, `fdic`, `tsy`) + **all 11 new Alfred
  event clips** (`event-*.mp3`). **Alfred's entire persona is done** (50/50: 39 node + 11
  event). Johnny is NOT done: 4/39 node clips, 0/11 event clips.

**NEW untracked files this session (not "leave alone" noise — active, deliberate):**

- `bullion-live-map/scripts/regen_narration_v2.py` — the resumable driver, see "How to
  resume" and "Scratch workspace / traps". Untracked on purpose (ad-hoc driver, not part
  of the shipped product), but copied into the real project tree (not a session scratchpad)
  specifically so a fresh session can find and re-run it.
- `bullion-live-map/audio/narration/.regen_2026-08-02_v2_done.txt` — the marker file the
  driver reads/appends. Currently 54 lines. **This is the actual source of truth for what's
  done** — trust it over any narrative (including this one) about progress.

**Files later work will touch:**

- `bullion-live-map/audio/narration/johnny-*.mp3` for the 35 nodes NOT yet in the marker
  file (everything except `sec`/`cftc`/`fdic`/`tsy`) — still contain the OLD tempo (0.9,
  not 0.95) and no loudnorm. Not broken, just stale/quieter/slower than the fixed version.
- `bullion-live-map/audio/narration/johnny-event-*.mp3` (11 files) — **do not exist at
  all yet.** `EVENT_JOHNNY_MANIFEST` already references them in shipped, pushed code.
  Playing Johnny's narration for any of the 10 scenarios or the AI-analysis button right
  now fails silently (404 → `audio.play().catch()` → `console.warn`), same failure mode as
  any missing manifest entry, not a crash. This is a live, known, temporary gap in
  production until the regen finishes.

**Scratch workspace / traps:**

- ⚠️ **This machine has only 8GB unified memory (Apple M2, confirmed via `sysctl
  hw.memsize`).** The regen was extremely slow and unpredictable this session — fast for
  ~15-20 diffusion-sampling steps, then a cliff to 10-50+ seconds/step on some clips. Root
  cause investigation this session: NOT thermal (`pmset -g therm` showed no recorded
  warning). Two real contributors found: (1) the driver originally loaded BOTH ChatterboxVC
  and ChatterboxTTS resident simultaneously for the whole run — fixed by restructuring
  `regen_narration_v2.py` to do the entire Alfred pass first (only VC resident), fully
  release it (`del` + `gc.collect()` + `torch.mps.empty_cache()`), then load TTS for the
  entire Johnny pass. This measurably helped (Alfred's 50-clip pass ran end-to-end with
  zero slowdowns after the fix). (2) Steam was running with an active GPU helper process
  during the first two attempts; the user quit it before the successful 3rd attempt, though
  this wasn't isolated from fix (1) so its independent contribution is unconfirmed. **Even
  after both fixes, a slowdown recurred later in Johnny's `tsy` clip** (stalled ~10-15s/step
  around step 600/1000, `vm.swapusage` showed 13GB/13GB swap in use, ~59MB physical RAM
  free) — this now looks like a **per-generation memory-growth ceiling** (longer text →
  longer diffusion sampling → growing attention/KV buffer that eventually exceeds what fits
  in 8GB regardless of what else is loaded), not something further code restructuring can
  fix. `tsy` still finished eventually (just slow). **Expect Johnny's remaining 35 node +
  11 event clips to be similarly unpredictable — some fast, some very slow — budget real
  wall-clock time, not compute-time.** Consider: running unattended/overnight, or shortening
  Johnny's longer scripts if this becomes intolerable (not attempted this session).
- ⚠️ **The regen was NEVER run to completion this session** — it was manually stopped
  twice (once to restructure the driver, once at the user's explicit request to stop and
  write this handoff) and manually resumed twice. The marker file is the only reliable
  record of what's actually done; don't trust log tail snippets from this conversation, the
  process is not currently running.
- **At the time of the commit/push, NOTHING from this session's audio had been listened to**
  — the commit/push happened on the user's **explicit, informed override** ("Commit + push
  everything now" — chosen after being told the regen was only 54% done and unheard). **The
  user has since listened to the 54 clips and confirmed they're fine** (see the UPDATE
  bullet below and "What has failed / risks / caveats"). This project's standing rule
  (never infer audio correctness from clean exit codes) held for this override in spirit —
  the listen just happened after the push instead of before. The next session still needs a
  listening pass on whatever the resumed regen adds, and should get one before any FUTURE
  audio commit.
- **UPDATE, same session, after the above was written: items 1/2/3/6 are now CONFIRMED**,
  not just code-reviewed. The Claude-in-Chrome extension never reconnected all session, so
  instead a small headless-Chrome + DevTools-Protocol driver was built ad hoc (no new deps —
  Node 21+'s built-in `fetch`/`WebSocket`; script discarded after use, not saved to the
  project) to drive both files through their real code paths (dispatching real click events
  on the D3-bound node `<g>` elements, calling the actual `showView()`/`closeDetail()`).
  Launched with `--use-gl=angle --use-angle=swiftshader` (NOT `--disable-gpu`, which was
  tried first and only produced mkultra's WebGL-unavailable fallback card instead of the
  real 3D scene) + an isolated `--user-data-dir` per this project's standing rule. Results:
  item 1 — rendered relationships HTML no longer contains the old lead sentence; item 2 —
  caption confirmed visible both while the panel is open AND after `closeDetail()` runs
  (panel-closed state independently confirmed too); item 3 — `#persona-orb`'s
  `getBoundingClientRect()` center exactly equals `#stage`'s center (both (700,492)) while
  parented inside `#stage`, reparents to `<body>` + gains `.orb-docked` on
  `showView('board')`, and reparents back + loses the class on `showView('map')` — both
  directions checked, plus a real WebGL screenshot (SwiftShader) showing the orb visually
  centered in the rendered constellation and correctly docked bottom-right on the board tab;
  item 6 — after starting a second clip, the first `Audio` object is a different reference
  from `currentNarrationAudio` and is left `.paused`. Zero console errors/exceptions in
  either file. **This closes out the single largest open risk from the prior handoff.**
- ⚠️ The prior handoff's own untracked-vs-tracked marker file
  (`.johnny_tempo90_done.txt`, 39 lines, from the PRIOR session's Johnny-only regen) is
  still sitting in `audio/narration/`, untouched, inert, unrelated to this session's
  `.regen_2026-08-02_v2_done.txt`. Don't confuse the two or treat the old one as current.
- **Not mine — leave alone** (same as every prior handoff in this project):
  `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`, `.agents/`, `.codex/`,
  `.superpowers/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple),
  `bullion-live-map/__pycache__/`, `bullion-live-map/scripts/__pycache__/`,
  `bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`, and the other tracked
  handoffs still sitting in `docs/superpowers/` (`honesty-pass-`, `mk12-`,
  `mkultra-spec2-brainstorm-`, `mkultra-spec2-plan-handoff.md` — all tracked, intentionally
  left in place per the archiving rule). **Never `git add .`/`-A`** — this session staged
  only specific files by name (2 HTML files, 2 Python files, the modified/new `.mp3`s).

## What has changed

- Items 4 and 8 fully implemented and shipped (code-complete; item 4 has zero audio
  dependency and is otherwise done; item 8's Alfred half is fully generated, Johnny half is
  not).
- Items 5 and 7's code changes shipped; the audio regen they require is 54% done (see
  above).
- `python3 -m unittest discover -s tests` → 41/41 still green (unaffected — pure HTML/JS +
  narration-script changes, this suite doesn't touch either).
- `python3 -m unittest scripts.test_generate_narration` → **33/34 green, 1 expected
  failure**: `test_every_event_johnny_clip_exists_and_nonempty` (11 files genuinely don't
  exist yet). This is the correct/expected state right now, not a regression — it'll go
  green once the Johnny event clips are generated.
- Commit `a3a58e7` on `main`, **pushed** to `origin/main`.

## What has failed / risks / caveats

- **Nothing has failed outright** — no fix was attempted and abandoned.
- **The remaining open risk is the incomplete audio regen** (54/100 clips), detailed at
  length above. Practically: Johnny's voice will sound inconsistent (some clips
  louder/faster-fixed, most still old) and Johnny's scenario/AI narration will silently
  no-op, until the regen finishes. **The user has listened to the clips generated so far
  and confirmed they're fine** — the "needs a listening pass" risk from earlier in this
  same session is resolved for what's been generated; it still applies to whatever the
  regen produces next.
- **Items 1/2/3/6 are now CONFIRMED** (see "What has changed" above and the detailed update
  under "Current state") via a headless-Chrome+CDP driver exercising the real code paths,
  not just code review. This was the single largest open risk carried in from the prior
  handoff — it's closed.

## What's next (ordered)

1. **Resume the audio regen** — `cd bullion-live-map && .venv-narration/bin/python3
   scripts/regen_narration_v2.py`. Expect it to be slow and uneven (see the memory-ceiling
   trap above); consider running it unattended/overnight. It will print
   `"All 78 node clips + 22 event clips present."` when genuinely done — don't infer
   completion from a quiet terminal or a stopped process; check the marker file has all
   100 entries (39×2 node + 11×2 event).
2. **Get a real human listening pass on whatever this regen run produces** — the clips
   already generated this session (54) have been listened to and confirmed fine; anything
   the resumed run adds still needs the same check before being fully trusted.
3. Items 1/2/3/4/6 are ALL now confirmed via headless-CDP this session (see "Current
   state" for the full item-3 writeup; item 4 confirmed separately in both files:
   clicking a board card dims all but the clicked node + its neighbors — exact counts
   checked, e.g. clicking "fed" left 7 of 39 cards undimmed, matching its neighbor set —
   and a board-background click clears all dimming + closes the panel). Nothing from the
   8-item review list needs further browser verification at this point.
4. Once the regen is fully done and heard, run
   `python3 -m unittest scripts.test_generate_narration` — should be 34/34 green — and
   commit the remaining ~46 `.mp3` files (all still named `johnny-*.mp3`/
   `johnny-event-*.mp3`, no new manifest/code changes needed, they're already wired).
5. Consider whether `bullion-live-map/scripts/regen_narration_v2.py` (currently untracked)
   should be committed now that it's proven useful twice — up to the user; not done this
   session since only asked to commit the review-fix work itself.

## Verification idioms used in this project (for the resuming session)

- Test suite: `cd bullion-live-map && python3 -m unittest discover -s tests &&
  python3 -m unittest test_calibrate && python3 -m unittest scripts.test_generate_narration
  -v` (plain `python3`) **and separately** `.venv-narration/bin/python3 -m unittest
  scripts.test_voice_blend -v` (needs torch/librosa/chatterbox).
- JS syntax check without a browser (used this session in place of live verification):
  extract `<script>` blocks with a regex that skips the one false-positive match inside an
  HTML comment (`<!-- ... <script>/<style> ... -->` near the top of both files), concatenate,
  `node --check`. Catches syntax errors only, not runtime/logic bugs — the headless-CDP
  approach (see the item-1/2/3/6 and item-4 confirmations above) is what actually replaced
  live-browser verification this session.
- Real generation: `.venv-narration/bin/python3 bullion-live-map/scripts/regen_narration_v2.py`
  — resumable, marker-file-driven, safe to kill and re-run at any point (loses at most the
  one clip in flight). Do NOT use `generate_narration.py`'s own `main()` for real runs — it
  has no resume capability and this project's runs get killed/stopped often enough that
  matters.
- Memory/thermal diagnosis on this machine: `pmset -g therm` (thermal warnings — showed
  none this session, ruling out heat as the cause), `sysctl vm.swapusage` +
  `vm_stat | head -4` (swap/free-page pressure — this is what actually correlated with the
  slowdowns this session), `sysctl hw.memsize` (confirms the 8GB ceiling).
- Audible correctness is never automatable in this project — `afplay` or the live browser,
  never inferred from clean test runs or exit codes. (This session's push was an explicit,
  informed, one-time exception — see the caveats section.)
- GitHub Pages deploy verification: no `gh` CLI on this machine — use `curl -s
  "https://api.github.com/repos/SinbadTheExplorer/claudekit/actions/runs?per_page=5"`
  and check the run for commit `a3a58e7` shows `completed`/`success`. Not checked this
  session (focus was code + regen, not deploy).

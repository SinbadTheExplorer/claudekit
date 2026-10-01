# Bullion Mk Ultra — Chain-Reaction Feature Shipped + Audit-Followup Closeout — Session Handoff

**Written:** 2026-08-09 · **For:** whoever resumes this project next. This handoff covers an
entire session's worth of shipped, deployed, and independently-reviewed work — there is
**no unfinished task to pick up mid-flight**. Everything below is closed out and live. Read
this for orientation on what changed and what's still genuinely open for a *future* session,
not to continue in-progress work.

## Goal

Three separate pieces of work landed this session, in order: (1) closing the last open item
from a prior link-sourcing audit, (2) applying all 20 outstanding findings from that same
audit plus fixing 5 stale figures that had leaked into Johnny's narration scripts, and (3)
designing, building, and QC-hardening a brand-new feature — "chain reaction hypothesis,"
which lets a user pick two nodes in `bullion_mkultra.html`'s causal graph and see every real,
already-verified path (≤3 hops) connecting them, honestly labeled forward/backward, with a
net-effect sign shown only when a path is consistently one direction.

- Spec (chain-reaction): `docs/superpowers/specs/2026-08-08-bullion-mkultra-chain-reaction-hypothesis-design.md`
- Plan (chain-reaction): `docs/superpowers/plans/2026-08-08-bullion-mkultra-chain-reaction-hypothesis.md`
- Spec (audit-followup): `docs/superpowers/specs/2026-08-08-bullion-mkultra-audit-followup-design.md`
- Prior handoff (read only if you need the equit/etf citation-fix backstory —
  not required to understand anything below): `docs/superpowers/bullion-mkultra-link-sourcing-audit-resolved-handoff.md`
- No active progress ledger exists — the chain-reaction plan's SDD workspace was deleted
  after its final review went clean, per this project's normal cleanup convention. `git log`
  is the only ground truth now.

## How to resume (do this first)

1. Confirm branch: `main`, up to date with `origin/main`. Run `git log --oneline
   cf3a6a3..HEAD` — you should see exactly the 9 commits listed under "What has changed"
   below (10 including the automated bot commit `b50c435`, which is unrelated — GitHub
   Actions' daily FRED/Yahoo data refresh, not this session's work).
2. Run `git status` — should be clean except for this project's long-standing list of
   untracked "not mine" files (`.DS_Store`, `__pycache__/`, `docs/superpowers/*` other than
   this handoff, etc.) — see "Not mine" below for the full list pattern.
3. There is no in-progress task. If you were told to "continue" this session's work, there
   is nothing queued — ask what's actually wanted, or see "What's next" below for genuinely
   open threads.

## Current state (active files)

**Branch:** `main`, clean, 9 commits ahead of session-start `cf3a6a3` (10 including the
unrelated automated `b50c435`), all pushed and deployed (verified via authenticated GitHub
Actions API — "pages build and deployment" shows `completed`/`success` for the final commit
`05872c1`, not just a fast `git push`).

**Files changed this session (all committed, all pushed):**
- `bullion-live-map/bullion_mkultra.html` — the only HTML file touched. Node/link citation
  fixes (audit-followup), 5 Johnny narration script corrections, and the entire new
  chain-reaction feature (traversal logic + UI).
- `bullion-live-map/bullion_mk18.html` — touched **only** for the same 5 narration-script
  text fixes (kept in sync because `generate_narration.py`'s test suite enforces a 3-way
  match across `bullion_mkultra.html`/`bullion_mk18.html`/Python). Nothing else in mk18 was
  touched — its stale Alfred `etf` citation text (see "What's next" below) is still there,
  deliberately.
- `bullion-live-map/scripts/generate_narration.py` — same 5 narration text fixes.
- `bullion-live-map/audio/narration/johnny-{dxy_fx,energy,geo,mbs,privcredit}.mp3` —
  regenerated, listened to and confirmed by the user before commit.
- `bullion-live-map/tests/test_chain_reaction.py` — new. Independent Python re-implementation
  of the chain-reaction traversal algorithm, used as a regression guard (this repo has no
  browser-based JS test runner).
- `bullion-live-map/tests/test_chain_reaction_js_parity.py` — new. Shells out to a real
  `node` process, runs the actual shipped JS across every ordered node pair (1,368 connected
  pairs, 6,076 paths), and diffs against the Python mirror exhaustively. Mutation-tested
  during this session: confirmed it fails if the direction-shadowing bug (see below) or the
  reversed-net-sign logic regresses. Skips (not fails) if `node` isn't on `PATH`.

**Files intentionally NOT changed:** `bullion_mk16.html`, `bullion_mk17.html` — frozen, per
this project's versioning convention. `bullion_mk18.html` beyond the narration-text sync
described above.

**Untracked, not committed anywhere (per this project's standing convention that
`docs/superpowers/` stays untracked for recent work):**
- `docs/superpowers/specs/2026-08-08-bullion-mkultra-audit-followup-design.md`
- `docs/superpowers/specs/2026-08-08-bullion-mkultra-chain-reaction-hypothesis-design.md`
- `docs/superpowers/plans/2026-08-08-bullion-mkultra-chain-reaction-hypothesis.md`
- `docs/superpowers/reports/2026-08-07-bullion-mkultra-link-sourcing-audit.md` — updated in
  place this session (all 20 previously-open rows now show `Suggested action: none`).

**⚠️ Traps:**
- **`bullion_mk18.html`'s `etf` node still has stale Alfred citation text** ("Source: ICI,
  Fed Financial Stability Report") — this was explicitly left un-synced per the user's
  direction in a prior session ("mk18 there's no need to touch anymore"), and this session's
  narration fixes did NOT change that stance — only the 5 unrelated Johnny-script figures
  got synced into mk18, nothing else. Don't assume mk18 is now fully current with mkultra.
- **Two node pairs in the graph store BOTH directions as separate, distinctly-cited edges**:
  `banks↔fdic` and `equit↔etf`. This tripped up the chain-reaction feature's first shipped
  version (a `.find()` with an either-direction match silently showed the wrong edge's
  mechanism/sign for these two pairs) — fixed in commit `e98ffe6`, and now permanently
  guarded by `test_chain_reaction_js_parity.py`. If you ever add a third such reverse-pair to
  the graph, that test will exercise it automatically (it's exhaustive over all pairs, not
  fixture-based) — no action needed, just know why it might newly fail.
- **The chain-reaction feature's net-sign semantics changed mid-session**, after a QC review.
  Originally: net sign shown only for all-forward paths. Now: shown for all-forward **or**
  all-backward paths (an all-backward path is a legitimate chain, just read end-to-start —
  labeled `(reverse)` in the UI so it's never mistaken for the forward answer). The design
  spec has been updated to match; if you find prose elsewhere describing the old forward-only
  rule, it's stale and should be corrected to match `bullion_mkultra.html`, not the reverse.

**Not mine — leave alone:** the long-standing untracked pile (`.DS_Store` files,
`__pycache__/`, `.claude/`, `.agents/`, `.codex/`, `.impeccable/`, `AGENTS.md`, `CLAUDE.md`,
`docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `docs/superpowers/archive/`, and every
other untracked `docs/superpowers/plans|specs/*.md` from earlier sessions) — same convention
every prior handoff in this project has documented. Also **`.claude/worktrees/`** may contain
`bullion-persona-toggle-frontend`, an unrelated prior session's worktree — not mine, don't
touch it.

## What has changed

1. **`b4e80cc`** — Closed the link-sourcing audit's last open item: verified the 57% equity-fund
   index-share figure from a primary ICI source, replaced a mismatched FEDS citation.
2. **`d7f4db4`** — Applied all 20 remaining findings from the same audit (wrong dealer counts,
   stale dollar figures, mismatched papers, etc.) directly to link `stat`/`why`/`note` fields,
   plus added the `oil→equit` field note the fieldnote-bar spec had identified. Updated the
   audit report so all 93 rows now read `none`.
3. **`ddc8f91`** — Found and fixed 5 places where Johnny's narration scripts had baked in the
   *old* versions of figures just corrected in step 2 (e.g. "a point and a half off their
   GDP" vs. the corrected 1.9%). Regenerated those 5 audio clips, listened to and confirmed
   by the user before commit.
4. **`53ff4d9`, `a715d0c`, `12282d9`** — Chain-reaction feature built via
   subagent-driven-development (3 tasks: independent Python test, JS traversal core, UI),
   each individually task-reviewed clean.
5. **`e98ffe6`** — Whole-branch review (the first review to span all 3 tasks together) found
   a real bug invisible to any single task: the direction-shadowing issue on `banks/fdic` and
   `equit/etf` described above. Fixed, plus routed hop text through this file's existing
   `enrichText()` convention (acronym hover-defs, source links) which the UI task had
   bypassed.
6. **`585f2e3`** — A user-requested independent QC review (fresh reviewer, no context from
   the SDD process) found: a real CSS layout bug (the node pickers overflowed the sidebar,
   making the whole drawer scroll horizontally), and that the JS/Python parity check from
   planning had only ever been run by hand, never committed as a permanent test. Both fixed,
   plus 3 UX polish items (bad default node pair, no result count, stale results after
   changing a dropdown) and the all-backward-paths net-sign change described above.
7. **`05872c1`** — A second independent re-review of that fix batch found 2 more Important
   items: the design spec still described the old net-sign rule (now corrected), and the
   `(reverse)` UI label had no test coverage (added, mutation-tested to confirm it actually
   catches the label being deleted).

Every commit's Pages deploy was verified via the authenticated GitHub Actions API (not just a
successful `git push`) before moving on — this project has a documented history of pushes
that silently failed to deploy due to Jekyll build breakage, so this check is load-bearing,
not paranoia.

## What has failed / risks / caveats

- **Nothing has failed.** All 120 tests pass (`tests/` 53, `test_calibrate` 33,
  `scripts.test_generate_narration` 34) as of the final commit.
- **Two independent code reviews, at two different stages, both explicitly found real bugs**
  that earlier review passes missed (the direction-shadowing bug at the whole-branch-review
  stage; the CSS overflow and missing permanent test at the standalone-QC stage). Neither
  gap was a process failure exactly — each review was scoped correctly for its stage — but it
  demonstrates that for this file's scale and density, a single review pass is not
  sufficient. If this feature gets extended, budget for at least one whole-branch review plus
  one independent fresh-eyes QC pass, not just per-task review.
- **Deferred, not forgotten — Minor findings from both QC rounds** (not blocking, both
  reviewers explicitly said fine to ship without): a tooltip on the `(reverse)` badge
  explaining what it means; the "N paths found" count line scrolls out of view in the
  240px-capped results box instead of staying pinned; no `aria-live` announcement when
  changing a dropdown updates results; `.chain-sign-zero`'s color literal duplicates the
  existing `--amber` CSS variable instead of referencing it; a couple of defensive/DRY nits
  in the traversal code (linear-scan lookup, off-by-one-safe-but-inelegant hop-cap check).
  None of these are correctness bugs.

## What's next (ordered)

Nothing is required. These are the genuinely open threads if a future session wants them,
none urgent:

1. **D3/3D canvas highlighting for a traced chain-reaction path** — explicitly out of scope
   for v1 (noted in the spec as a fast-follow). Would need to translate a found path into the
   renderer's existing focus/dim/highlight machinery.
2. **The Minor findings listed above**, if you're in the file anyway for something else —
   cheap to bundle, not worth a dedicated session.
3. **`bullion_mk18.html`'s stale `etf` Alfred citation text** — still deliberately un-synced.
   Confirm the user still wants it left alone before touching.
4. **The "third voice" narration spec** (a menacing-Johnny variant, 3-way blend + pitch-down,
   confirmed "quite menacing" by ear in an earlier session) — promised as a write-up, never
   delivered. Small, well-specified, still open. Not touched this session.
5. **Broader source-reinforcement research** (validating causal links against government
   sources/textbooks/Wikipedia beyond what the existing audit covered) — explicitly out of
   scope for everything done this session, would need its own brainstorm if picked up.

## Verification idioms used in this project (for the resuming session)

- Test suite: `cd bullion-live-map && python3 -m unittest discover -s tests && python3 -m
  unittest test_calibrate && python3 -m unittest scripts.test_generate_narration -v`
  (plain `python3`, no venv needed — 53 + 33 + 34 as of this handoff).
- Narration regeneration needs the venv: `.venv-narration/bin/python3
  scripts/regen_narration_v2.py` — never plain `python3`. See the `narration-regen-workflow`
  skill for the marker-file resume mechanics and the mandatory human listening-pass gate
  before any commit.
- Sanity-checking a hand-edited JS snippet in `bullion_mkultra.html` without a browser:
  extract the relevant lines with `node -e` and `eval()` them in isolation — a naive
  full-file parse false-positives on this file. If your snippet declares `const`/`let` you
  need in a later check, keep the whole thing in **one** `eval()` call — direct eval's
  block-scoped bindings don't leak to the outer scope across separate calls (this bit a
  verification script during this session; fixed by concatenating into one string before
  `eval`).
- UI verification: the `headless-chrome-verification` skill, with an isolated
  `--user-data-dir` per this project's standing rule.
- Push verification: a successful `git push` is **not** proof of a successful deploy. Check
  the authenticated Actions API: `TOKEN=$(printf "protocol=https\nhost=github.com\n" | git
  credential fill 2>/dev/null | sed -n 's/^password=//p')`, then `curl -H "Authorization:
  token $TOKEN" https://api.github.com/repos/SinbadTheExplorer/claudekit/actions/runs`
  and confirm the "pages build and deployment" run for your commit SHA shows
  `completed`/`success`.
- Mutation-testing a new regression guard: before trusting a new test, deliberately break the
  thing it's supposed to catch (in a scratch copy, never the real file) and confirm the test
  actually fails. Used twice this session (the JS-parity test against the direction-shadowing
  bug and the reversed-net-sign logic; the reverse-label guard against the label being
  deleted) — both confirmed to genuinely catch their target regression, not just look
  plausible.

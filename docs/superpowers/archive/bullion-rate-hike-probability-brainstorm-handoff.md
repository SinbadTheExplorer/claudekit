# Bullion — Rate-Hike/Cut Probability Feature — Brainstorm Handoff

**Written:** 2026-09-08 · **For:** a fresh session that will implement the rate-hike/cut probability capability for Bullion (Mk Ultra front door)

## Goal

Give Bullion a way to show what the market currently thinks about the next Fed rate
decision — timed to real-world relevance (Warsh Fed-chair talk, Trump rate-hike
commentary) — without turning the UI into a wall of basis points, and without
overclaiming what the correlation to gold actually supports.

No spec file or plan doc exists yet — this was a **brainstorming conversation only**
(bounded-path classification; no `docs/superpowers/specs/...` file was written because
the flow being extended already exists in the repo). This handoff **is** the design
record. Nothing has been implemented.

- Design authority: this document (below), from a 2026-09-08 brainstorming session.
- No plan doc yet — writing-plans has not been invoked for this feature.
- No progress ledger — implementation hasn't started.

## How to resume (do this first)

1. Confirm you're on `main` in `~/claude-projects/claudekit`, working subdir `bullion-live-map/`.
2. Read the **Design** section below in full — it's the only record of what was decided and why.
3. Do NOT re-brainstorm from scratch. The design was presented to the user in chat and approved ("good, write a hand off we implement later"). Treat it as approved; only revisit a point if you hit a blocker the design didn't anticipate (see Open Questions).
4. **Immediate next action:** verify whether Kalshi's public markets-read endpoint needs an API key/account signup or is truly anonymous-read. This was ambiguous from a web search during brainstorming and blocks writing the fetch function. Check `https://help.kalshi.com` / their API docs directly, or just try an unauthenticated `GET` against a known market endpoint.

## Current state (active files)

**Branch:** `main`, 0 commits ahead — this session made no commits. Repo `HEAD` at brainstorm time: `095efb5` (Add first verified news.json + news-images/ snapshot).

**Files created / changed:** none. This was pure research + conversation. Files **read** during brainstorming (for context, not modified):
- `bullion-live-map/calibration_report.txt` — OLS elasticity fit report, see Design below
- `bullion-live-map/audit_fit_elasticities.py` — the hand-rolled OLS fitter that produced it
- `bullion-live-map/fetch_bullion_data.py` — existing fetch pattern (FRED, Yahoo unofficial, IMF) to follow for the two new fetchers
- `.github/workflows/daily-data.yml` — the cron this feature should piggyback on
- `bullion-live-map/bullion_mkultra.html` — grepped for `ffr`, `ELASTICITY`, `DRIVERS`, `NODE_ELASTICITY`, tab structure, and the existing `data-shock="rate_hike"` button

**Files future work will touch:**
- `bullion-live-map/fetch_bullion_data.py` — add two new fetch functions
- `bullion-live-map/data.json` — two new fields in `fields`/`schema`, populated into `history`
- `bullion-live-map/bullion_mkultra.html` — new Markets-tab card; possible wiring into the existing `rate_hike` shock button
- `.github/workflows/daily-data.yml` — likely just needs the new fetch calls added to the existing `fetch_bullion_data.py` invocation; probably no workflow-file changes needed since it's piggybacking, not a new cadence

**Scratch workspace / traps:**
- ⚠️ `docs/superpowers/bullion-mkultra-markets-tab-handoff.md` (untracked, Sep 1) covers a **different, already-shipped** Markets-tab feature (index dashboard + news ticker). It is NOT about this rate-probability feature — don't confuse the two. It's being moved to `archive/` as part of writing this handoff (see below), per the "keep only the 2 most recent handoffs" rule — but it's still readable there if you want that history.
- ⚠️ `calibration_report.txt` reflects a specific historical training window (first 80% of a 366-day span, ending before 2026-09-08). Its `ffr -> gold_pct` "not significant" finding is the honesty anchor for this feature's forecast framing (see Design) — don't treat the *specific numbers* as current without re-running `audit_fit_elasticities.py` against fresh `data.json`, but the *qualitative* finding (direct ffr→gold link is weak; ffr→dxy→gold is the stronger indirect path) is unlikely to have flipped in a week.

**Not mine — leave alone:** everything else in `bullion-live-map/` (news pipeline, 3D map, mk11–mk18 prototype files) — untouched, unrelated to this feature.

## What has changed

Nothing shipped. This session was 100% design/discovery, conversationally approved, now being written down.

## What has failed / risks / caveats

**Nothing has failed** — nothing was attempted yet. Caveats and carried-forward decisions:

- **UNVERIFIED:** Kalshi's auth requirement for reading public market prices (see "How to resume" step 4). This is the single blocking unknown for implementation.
- **UNVERIFIED:** exact Kalshi market ticker / series and Polymarket market slug for "next FOMC rate decision" — these rotate per meeting and were not looked up during brainstorming. Must be confirmed against each platform's live market listings before writing the fetch calls.
- **Decision not finalized, flagged for implementation time:** whether the new probability card scales the existing hardcoded `+50bps` `rate_hike` shock scenario (replacing the fixed assumption with the real market-implied move), or stays a separate factual card next to that scenario button. Both were discussed; neither was picked. Default recommendation if not revisited: keep them **separate** — a sourced fact (probability) and a what-if simulation (the button) are different epistemic categories, and conflating them risks the exact overclaiming the honesty constraint below is meant to prevent.
- **Open tension, not resolved, flagged explicitly:** Mk Ultra's live front door (`bullion_mkultra.html`) has a standing **no-LLM-calls** design principle. This feature's "plain-English headline" (e.g. "Markets price in a 78% chance of a cut") must be **template-generated**, not an LLM call, to stay consistent with that principle. This was raised early in the conversation as a real tension and never explicitly overridden by the user — default to template-based (simple string interpolation off the fetched probability number + a small set of hand-written phrase buckets, same spirit as the existing hand-written `why`/`stat` link descriptions in `LINKS`) unless the user says otherwise when implementation starts.
- **Forecast-honesty constraint (hard requirement — ties to the project's existing "verify, don't assume" citation discipline):** the probability number itself is stated as fact, sourced + timestamped ("Kalshi, as of [time]" / "Polymarket, as of [time]"). Any "what this means for gold" propagation must reuse the existing `measured` / `directional` / `unverified` confidence tiers already in `ELASTICITY` — it must not imply more certainty than the underlying correlation supports. Concretely: `calibration_report.txt` already shows `ffr -> gold_pct` is **not statistically significant** (`|t|=0.3`) in this project's own data — so a literal "rate move → gold forecast" claim needs heavy hedging or should lean on the indirect, actually-measured path instead: `dxy -> gold_pct` is `MEASURED` at `|t|=4.4`.

## What's next (ordered)

1. Verify Kalshi's public-read auth requirement (see "How to resume" step 4).
2. Look up the live Kalshi market ticker and Polymarket market slug for the next FOMC decision.
3. Add two fetch functions to `bullion-live-map/fetch_bullion_data.py`, following the existing `fetch_yahoo_symbol`/`fetch_fred_series` pattern — same per-field failure isolation (one source failing must not kill the day's commit).
4. Add two new fields (`fed_cut_prob_kalshi`, `fed_cut_prob_polymarket` or similar — names not finalized) to `data.json`'s `fields`/`schema`, populated daily into `history` via the existing `daily-data.yml` cron (no new workflow needed).
5. Build the Markets-tab card in `bullion_mkultra.html`: plain-English headline (template-generated, no LLM call), both numbers shown if Kalshi/Polymarket diverge meaningfully, bps/elasticity detail collapsed underneath reusing the existing confidence-tier labels.
6. Decide (or accept the default above) on whether the card feeds into the existing `rate_hike` shock button or stays separate.
7. Before calling this done, re-skim `calibration_report.txt` (or re-run `audit_fit_elasticities.py` if `data.json` has moved on meaningfully) to make sure the "what this means for gold" framing still matches the actual fitted relationships.

## Verification idioms used in this project (for the resuming session)

- `python3 bullion-live-map/fetch_bullion_data.py` — run the fetch script directly to test new fetchers before relying on the cron; it prints per-field fetch failures rather than dying silently.
- `python3 bullion-live-map/audit_fit_elasticities.py [path/to/data.json]` — re-run the OLS elasticity audit against current data if you need fresh significance numbers for the honesty framing.
- Workflow can be tested by hand via `workflow_dispatch` on `daily-data.yml` in GitHub Actions (see the "CI: verify scheduled runs actually succeed" project memory — check the Actions run history, don't assume a scheduled run succeeded just because the workflow file looks right).

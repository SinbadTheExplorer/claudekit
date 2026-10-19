# Bullion v1.1: Onboarding (first-time tutorials)

**Written:** 2026-10-19 · **Status:** planned, not started. Start only after the Diesel case
competition is submitted (due 2026-10-23).

## Why

Bullion v1.0 was released on 2026-10-19. The owner and some of their family and friends then
tried it, and the main reaction was **"too complicated."** It works like a deep game: there's a
gem inside, but you have to be very motivated to dig it out. The whole map shows up at once, and
most features come with no explanation.

What's there today: a 3-step coach (`COACH` in `bullion_mkultra.html`: "Start here," "That card
is the point," "Reading the lines"). It only covers the map, and it stores its "done" state in
`sessionStorage`, so it shows up again in every new tab.

## Scope

1. **First visit: a 60-second guided story** instead of the full map at once. Use a real recent
   event: "Inflation came in hot (Oct 14). Watch what happened." Light up 3-4 nodes in order:
   inflation → rate-hike odds → tech stocks → fear (VIX). End with a "See the full map" button.
2. **A first-open tip for each feature.** It is 1-3 steps long and can be skipped after step 1.
   It appears the first time that feature is opened and never again. Remember who has seen it
   with `localStorage`, not `sessionStorage`. Features to cover:
   - **Market tab**: index dashboard and news ticker
   - **Analysis tab**: what "Run macro analysis" does, how to read the health score, and how to
     read the five dimensions (positive = more stress than usual)
   - **Scenario picker** (`scenario-select`): what a shock is and what to watch for
   - **"Set your own numbers"** (`manual-section`): live, but effectively undiscoverable today
   - **History date picker**: lets you see the map on a past date
   - **Narrator toggle**: Alfred vs Johnny
3. **Fix the existing coach** so it uses `localStorage`.

## Out of scope

- The "You're the Fed" game mode goes on the someday list. It could become the guided story
  later, but it is not part of v1.1.
- No new data, no prediction work, no "super database."

## Done when (checkable by someone else)

1. **Someone who has never used Bullion can explain one chain reaction without help** (e.g.
   "hot inflation → rates up → tech falls") after about 60 seconds. Test it on the same family
   and friends who found v1.0 too complicated, with at least 3 people.
2. **Every feature listed above shows its tip exactly once** on a fresh browser profile, and
   doesn't show it again after a reload or in a new tab.
3. **Nothing appears on a phone that can't be skipped.** Check at 390px width.

**Time budget:** about 2 short sessions to build, plus 1 afternoon of watching people use it.
Then tag `bullion-v1.1` and add a changelog entry.

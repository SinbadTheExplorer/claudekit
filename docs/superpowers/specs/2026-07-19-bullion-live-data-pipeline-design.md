# Bullion Mk11 Live Data Pipeline — Design

Date: 2026-07-19

## Purpose

Turn `bullion_mk11_constellation.html` (currently a Downloads-folder scratch
file with a broken, Mac-only 9am data job) into a maintained part of the
`claudekit` repo: a daily-refreshed, date-browsable financial map that
non-Mac users (phones, other browsers) can view live over the web.

## Background / current state

- `~/Downloads/bullion_mk11_constellation.html` already has a working date
  selector (`#history-date-input`) and reads history from a global JS
  variable (`window.BULLION_LIVE_HISTORY`) loaded via `<script src>`.
- `~/Downloads/fetch_bullion_data.py` already pulls live data (FRED for
  us2y/us10y/cpi_yoy/vix/ffr/wti_px/nfp_mom; Yahoo Finance chart API for
  gold_px/dxy/spx) and writes `bullion_live_data.js` (latest) +
  `bullion_live_history.js` (date-keyed, 365 days). FOMC hike/hold/cut odds
  have no free data source and stay simulated.
- A FRED API key is already saved locally at `~/.config/bullion/fred_api_key`.
- An existing LaunchAgent (`~/Library/LaunchAgents/com.bullion.livedata.plist`)
  runs this at 9am daily but is broken: macOS blocks a bare launchd-invoked
  `python3` from reading `~/Downloads` ("Operation not permitted").
- `~/Downloads` is not a git repo. The only repo with a real GitHub remote
  is `claudekit` (`origin` → `github.com/SinbadTheExplorer/claudekit`,
  tracks `main`), which currently holds an unrelated map (`financial-map.html`).
- The keychain-cached GitHub credentials on this Mac belong to a different
  account (`tamphuc0503-nrc`) with no write access to this repo.

## Decisions

1. **Location**: move the mk11 lineage into its own subfolder inside
   `claudekit`, kept separate from the unrelated `financial-map.html`
   project: `claudekit/bullion-live-map/`.
2. **Data format**: replace `bullion_live_data.js` / `bullion_live_history.js`
   with a single `data.json`, fetched at runtime via `fetch('data.json')`
   rather than loaded as a `<script src>` global. This matches the request
   literally, at the cost of requiring the page be served over HTTP(S)
   rather than opened as a local `file://` — which GitHub Pages provides.
3. **Serving**: enable GitHub Pages on `claudekit` (branch `main`). This
   gives any device — phone, tablet, desktop, any browser — a stable HTTPS
   URL that always reflects the latest pushed `data.json`. This was the
   deciding factor for point 4 below: once other people depend on the page,
   a scheduler that silently no-ops when a laptop is asleep is a liability.
4. **Scheduler**: a Claude Code cloud scheduled routine (via the `schedule`
   skill), running daily at **6:00am America/New_York**, independent of
   whether the Mac is on. Supersedes the local LaunchAgent, which becomes
   obsolete and should be unloaded to stop it failing silently at 9am.
5. **Git identity / local push credentials**: not required for the
   automation itself once it runs in the cloud. Local `gh auth login` /
   `git config user.*` are only needed if the user wants to push manually.

## File layout (after implementation)

```
claudekit/
└── bullion-live-map/
    ├── bullion_mk11_constellation.html   (moved from Downloads, fetch()-based)
    ├── fetch_bullion_data.py             (moved from Downloads, writes data.json)
    ├── data.json                         (generated daily, git-tracked)
    └── run_daily_update.sh               (fetch → commit-if-changed → push)
```

## `data.json` shape

Flat, date-keyed object, one entry per trading day, last 365 days:

```json
{
  "2026-07-19": {
    "us2y": 4.42, "us10y": 4.28, "cpi_yoy": 2.4, "vix": 16.8,
    "ffr": 4.33, "wti_px": 68.2, "nfp_mom": 186,
    "gold_px": 2385.4, "dxy": 104.1, "spx": 5540.2
  },
  "2026-07-18": { "...": "..." }
}
```

Same fields, sources, and rounding as today's `fetch_bullion_data.py`. FOMC
odds remain simulated (documented in-script, unchanged).

## Component changes

**`fetch_bullion_data.py`**: replace the two `window.X = ...` JS-file
writers with a single `json.dump()` to `data.json`. FRED/Yahoo fetch logic,
error handling, and graceful-degradation-on-partial-failure are unchanged.

**`bullion_mk11_constellation.html`**: replace the two
`<script src="bullion_live_...">` tags with a `fetch('data.json')` at page
load; cache the parsed object; wire the existing `#history-date-input`
date-lookup logic to read from the fetched object instead of
`window.BULLION_LIVE_HISTORY`. Falls back to the existing simulated
baseline if the fetch fails (e.g. someone opens the file locally instead of
via the Pages URL) — same degrade-gracefully behavior it has today.

**`run_daily_update.sh`** (new): runs `fetch_bullion_data.py`, then
`git add data.json && git diff --cached --quiet || (git commit -m "Update live financial data for $(date +%F)" && git push origin main)`.
The `git diff --cached --quiet ||` guard prevents empty commits on days the
data didn't change.

**Cloud scheduled routine**: set up via the `schedule` skill at
implementation time — exact repo-access and FRED-key-as-secret mechanics
are determined then, not prescribed here.

## Cleanup

- Unload/remove `~/Library/LaunchAgents/com.bullion.livedata.plist` (or
  repoint it at nothing) so it stops attempting — and failing — at 9am.
- Leave `~/Downloads/bullion_mk*.html` and older mk versions alone; only
  mk11 and its live-data companions move.

## Out of scope

- Changing the transmission/shock rules, node set, or AI-narrative feature
  of the map.
- The separate `financial-map.html` project and its finance-planner /
  finance-builder / finance-tester agent pipeline — unrelated lineage, not
  touched by this work.
- FOMC probability live-sourcing (no free API found; stays simulated).

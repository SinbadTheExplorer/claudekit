# Bullion Mk Ultra Security, Legal Footer & First-Open Tips — Session Handoff

**Written:** 2026-10-07 · **For:** the next session (terminal or cloud) that picks up Bullion. Four commits are **pushed to a branch but NOT merged** — nothing below is live on GitHub Pages until `security/news-link-scheme` lands on `main`. Read "How to resume" first.

## Goal

The user asked for, in order:

1. A security review of everything that could put Bullion at risk ("as a security team"), and fixes for what turned up.
2. Fixes prompted by two TikTok videos on "vibe-coded" sites: working buttons, a visible legal footer, an accurate privacy policy, a COPPA line. The videos' login/back-end tests don't apply: Bullion has no login and no user data.
3. Game-style tutorials: one short tip the first time each menu or tool is opened.

All three are implemented, browser-verified, committed and pushed to the branch.

## How to resume (do this first)

1. `git fetch origin && git log --oneline -1 origin/security/news-link-scheme`. It should be at or after `a48df83` (the commit that added this handoff; code changes end at `0aa59c3`).
2. Has it been merged? Check with `git branch -r --contains 0aa59c3`, or look for a PR from `security/news-link-scheme`.
   - **Not merged:** the user still has to merge it (or ask for a PR). As of writing it merges cleanly into `origin/main` (`git merge-tree --write-tree origin/security/news-link-scheme origin/main` exits 0); `main` had only moved by bot data commits. **Don't open a PR unless the user asks.**
   - **Merged:** start any new work from fresh `main`, not from this branch.
3. **Next action:** fix the stale test (see "What's next" #1). It's a 2-line change, and it's the only red test in the suite.

## Current state

**Branch:** `security/news-link-scheme`, 4 commits on top of `877ce61`:

| Commit | What |
|---|---|
| `5284e84` | Only allow http(s) links on news headlines |
| `6d05404` | Survive blocked browser storage; restrict news image downloads |
| `def87fc` | Put the disclaimer on the start screen; complete the privacy notice |
| `0aa59c3` | Add first-open tips to each menu and tool |

**Files changed:**
- `bullion-live-map/bullion_mkultra.html`: the live version. Every UI change is here.
- `bullion-live-map/fetch_bullion_news.py`: link scheme check (in `parse_rss_items`), and an image-download scheme check plus size cap (`_fetch_image_bytes`, `IMAGE_MAX_BYTES = 5 MB`).
- `bullion-live-map/tests/test_fetch_bullion_news.py`: two new tests (`test_drops_items_whose_link_is_not_http`, `test_image_fetch_refuses_non_http_schemes`).

**Not touched / leave alone:** `bullion_mk11`–`mk18.html` (frozen; their AI call has `BACKEND_URL = ''` and no key, so it just fails), the Mk1 `financial-map.html` at the repo root (bring-your-own key in `sessionStorage`, sent only to `api.anthropic.com`; judged acceptable), `fetch_bullion_data.py`, and `data.json`/`news.json` (bot-managed).

## What has changed (and why)

### Security
- **Headline link XSS (medium).** `buildNewsItem` assigned the feed's `h.link` straight to `<a href>`. A `javascript:` link would run on click, and the page CSP's `'unsafe-inline'` does **not** block `javascript:` URLs. It's now blocked in two places: the fetcher drops non-http(s) items, and the page refuses to set the href.
- **Blocked-storage crash (medium; reliability, not security).** `localStorage.getItem` ran at top level (narration persona). Where a browser blocks site data, that throws `SecurityError` and **halts the rest of the script**: 0 headlines and no later panels. Reproduced in Playwright by making the `localStorage` getter throw. All storage now goes through `storageGet`/`storageSet` (try/catch helpers defined next to `narrationPersona`). **Use these helpers for any new storage access, never `localStorage` directly.**
- **Image fetch (low).** `urlopen` also accepts `file://` and `ftp://`, and `resp.read()` was unbounded. Now: http(s) only, capped at 5 MB. Both failures raise `URLError`, so the existing skip-thumbnail handler covers them.

### Legal / privacy
- The only "Disclaimer & privacy" link was buried in a collapsed Analysis drawer, and it was a `<span>`, so keyboard users couldn't reach it. Now the start-screen footer (`.version-label`) reads: *Mk Ultra · Educational use only — not financial advice · Disclaimer & privacy · © 2026 SinbadTheExplorer*. Both links are `<button class="disclaimer-link">`, wired with `querySelectorAll`. The dialog focuses its close button on open and returns focus on close.
- The privacy notice said nothing was stored. It now discloses the local-storage settings (narrator voice, seen tips and notices), says the site is **not directed to children under 13**, and adds a contact route (GitHub Issues, deliberately not an email address) and a copyright line matching `LICENSE`.

### First-open tips
- One `#tip-card` plus an engine in the **last `<script>` block** of `bullion_mkultra.html`. `TIPS` holds 12 entries: market, analysis, board, live, expand, scenario, manual, history, macro, trends, customize, chain. Each has an `anchor` selector, a `title` and a static HTML `body`.
- Triggers are wired with `on(id, key, when)` *after* each element's own handler, so `when()` sees the opened state. A tip is **not** marked seen if it's blocked (start screen, coach card or disclaimer visible), so it shows next time instead.
- Storage keys: `bullion-tip-<key>`, `bullion-tips-off`, `bullion-coach-done`. "Turn off tips" sets `tips-off`. **"Show tips again"** (`#tips-replay`, next to the drawer disclaimer link) clears all of them and re-shows the coach.
- The coach ("Start here") moved from `sessionStorage` to `localStorage`, so it's shown once ever, not once per visit.
- Deliberately **no tip** for the node card (coach step 2 covers it), the narrator orb (has its own nudge and Johnny notice) or the Audit Log (opens in a new window via `window.open`, with its own explanation).
- **Every tip describes UI behavior only, checked against its handler. None makes a causal or financial claim.** If you add one, keep it that way: causal wording falls under the `bullion-descriptions` skill's standard.
- **Trap fixed during testing:** `blocked()` first used `coach.offsetParent !== null`. `offsetParent` is **always null for `position: fixed`** elements, so the coach never registered as visible and tips could stack on it. It's now `coach.getClientRects().length > 0`. Use that pattern for any fixed-position visibility check.

### Copy fix
- The scenario section's note said *"Baseline is a simulated mid-2024 snapshot, not a live feed."* That's false by default: `useLiveData = true`, and `buildBaseState()` overlays live values. It now reads: *"Scenarios start from today's live numbers, or from a fixed mid-2024 snapshot if you switch the map to Simulated."*

## Verification that was done

All in headless Chromium (`executablePath: '/opt/pw-browsers/chromium'`, args `--use-gl=swiftshader --enable-webgl`) against `python3 -m http.server` run from `bullion-live-map/`:
- **News:** all 40 headlines render with http(s) hrefs, and 0 page errors.
- **Storage blocked** (getter throws `SecurityError`): 40 headlines and 0 errors after the fix; 0 headlines and an error before it.
- **Every button**, each on a fresh page load with the coach dismissed: 24/24 ordinary buttons, 9/9 off-screen keyboard node buttons (`#mkultra-a11y-nodes button`, Enter key), a mouse click on a 3D dot, and both × buttons once their panel is open.
  - Harness gotchas: the coach card covers part of the toolbar; `#board-view`'s `.board-col` buttons share node names with the a11y buttons; and a picked history date deliberately **disables** `#live-toggle-btn` until **Today** is pressed.
- **Tips:** all 12 appear on first trigger and none on a second trigger or after a reload. Turn-off and replay both work. No tip while the coach is up. Checked at desktop (1440×900, placed by its anchor) and phone (390×844, docked along the bottom) sizes.
- **Unit tests:** `python3 -m unittest discover -s tests` from `bullion-live-map/`. All pass except the one pre-existing failure below.

The Playwright scripts lived in the session scratchpad and are gone. Rebuild from the notes above if needed.

## What has failed / risks / caveats

- **Pre-existing red test (not caused by this branch; fails identically on `877ce61`):** `test_fetch_bullion_data.TestBuildEnvelope.test_every_known_field_has_metadata`. The **test** is stale, not the code: `FIELD_META` correctly contains `fed_decision_kalshi` and `fed_decision_polymarket` (added with the Fed-odds feature), but the test's hard-coded `expected` set was never updated.
- **Known cosmetic issue:** on desktop the scenario tip briefly covers the scenario's one-line description until dismissed. Left as is.
- **`'unsafe-inline'` stays in the CSP** on purpose. Removing it means moving about 750 KB of inline JS into external files, which carries high breakage risk for little gain now that the link hole is closed. Revisit only if user logins or user-submitted content are ever added.
- **Old Mk11 and Mk12 have no CSP.** They're safe because they load only same-origin `data.json`, but they're public, show older unaudited claims and are indexable.

## User-only actions (account settings; the session can't do these)

Raised with the user. Not confirmed done as of writing:
1. **Turn on GitHub 2FA.** They are the sole admin of a public repo.
2. **Fix the repo's "About → Website" field.** It points to `nguyenminhthanh0403-hub.github.io/claudekit/bullion-live-map/bullion_mk15.html`, a **different username** and an old Mk. If that username is free, someone could claim it and host a look-alike. It couldn't be checked from the sandbox (proxy blocked it).
3. **Hide commit email:** Settings → Emails → "Keep my email addresses private" and "Block command line pushes that expose my email". The author email appears in about 328 public commits; history wasn't rewritten.
4. **Protect `main`** with a ruleset that blocks force-push and deletion. That doesn't block the bots' normal pushes.
5. **Merge this branch.**

## What's next (optional, in rough priority)

1. Fix the stale test: add `"fed_decision_kalshi", "fed_decision_polymarket"` to `expected` in `tests/test_fetch_bullion_data.py` (around line 325). Then the whole suite should be green.
2. Consider deleting the old Mk11–Mk18 pages, or marking them `noindex`.
3. Copyright exposure: `fetch_bullion_news.py` re-hosts MarketWatch thumbnails in `news-images/`. That's low risk for a student project; drop the thumbnails before any promotion push.
4. Analytics, if wanted later: GoatCounter (cookie-less). It needs a CSP `connect-src`/`script-src` allowance **and** a same-day update to the privacy notice, which currently says "uses no analytics".
5. SEO groundwork discussed earlier but not built: `robots.txt` and `sitemap.xml`, Google Search Console, a plain-text About section, and a `canonical` pointing at the clean URL instead of `bullion_mkultra.html`.

## Security review coverage (for reference)

Already checked and found clean, so no need to redo it: full-history secret scan (430 commits: no keys, tokens or private keys); docs contain no personal details beyond "business student"; all `innerHTML` sinks in `bullion_mkultra.html` take static content or escaped values (`escapeHTML`), and feed and `data.json` strings reach the page via `textContent`; the three workflows are `schedule`/`workflow_dispatch` only (no PR triggers), pass outside text through `env`, not `${{ }}` interpolation, and read the FRED key from Secrets; `Pillow==12.3.0` is pinned; the live page contains no API key and has `connect-src 'self'`; the sole collaborator is the owner.

# Handoff: Bullion analytics (deploy + switch on)

**Branch:** `bullion-analytics` (commit `be2a215`, pushed). Not merged to `main`.
**Status:** Code done and tested in a cloud session. The tracker is **off**
(`ANALYTICS_URL = ''`) until the Worker is deployed. Deployment needs
`wrangler login` on the Mac, which a cloud session can't do.

## Prompt to paste into the terminal session

> Read `docs/superpowers/bullion-analytics-handoff.md` on branch
> `bullion-analytics` in claudekit and do the "Next steps". Stop and ask me
> before any step that needs a secret. I type secrets myself.

## What was built

| Piece | File | Notes |
|---|---|---|
| Worker (backend) | `analytics-worker/src/index.js` | `POST /e` collect, `GET /stats` (Bearer `STATS_TOKEN`), `GET /dashboard` owner page |
| DB schema | `analytics-worker/schema.sql` | D1: `agg(day,kind,key,hits,ms)` + `seen(day,h)` for today's visitor hashes only |
| Config | `analytics-worker/wrangler.toml` | `database_id` is a placeholder. `ALLOWED_ORIGIN = https://sinbadtheexplorer.github.io` |
| User guide | `analytics-worker/README.md` | Setup commands, privacy rationale, limits |
| Tracker | `bullion-live-map/bullion_mkultra.html` (last `<script>` before `</body>`) | Polls `openDetailNode` + active tab every 1s. Wraps `triggerShock`. `sendBeacon` on hide/pagehide |
| Privacy note | same file, start screen `.privacy-note` | "Anonymous, cookie-free usage counts only" |
| Pages exclude | `_config.yml` | `analytics-worker/` excluded from the Jekyll build |

**Metrics:** daily unique visitors, page views, visible time per tab/node
(the clock pauses after 2 min idle or when the tab is hidden), opens per
node/tab, and shock scenarios run.

**Privacy design (do not weaken without telling the user):** no cookies or
localStorage. IP+UA are hashed with `SALT_SECRET`+date and then dropped.
`seen` rows from earlier days are deleted on every write. DNT/GPC are
honored on the client and the server. The dashboard token lives in memory only.

## Verified (cloud session, headless Chromium + node:sqlite mock of D1)
- The beacon carried the correct visit/tab/node/shock events (`sec` node 3.8s, `rate_hike` shock).
- Wrong token on `/stats` returned 401. A foreign `Origin` on `/e` returned 403.
- `/stats` aggregates were correct, and `seen` held only one hash with no IP.
- No page errors. The dashboard renders at 390px width.
- Not verified: real Cloudflare deploy and real D1. The mock D1 may differ slightly (e.g. `meta.changes`).

## Next steps (Mac terminal)
1. `git fetch origin && git checkout bullion-analytics`
2. **Check for the user's earlier local tracking work.** They said they built
   tracking on a branch that was never pushed. Run `git status`, `git branch`
   and `git stash list` in the Mac's claudekit. If it exists, show the user
   both versions and let them pick. Don't merge them blindly.
3. `cd analytics-worker && npx wrangler login`
4. `npx wrangler d1 create bullion-analytics`, then put the printed `database_id` into `wrangler.toml`.
5. `npx wrangler d1 execute bullion-analytics --remote --file=schema.sql`
6. `npx wrangler secret put STATS_TOKEN` and `npx wrangler secret put SALT_SECRET`. **The user types these values.** Never echo, log or commit them.
7. `npx wrangler deploy`, then note the `*.workers.dev` URL.
8. Switch the tracker on. Set `ANALYTICS_URL` to that URL **and** add the URL to the
   CSP `connect-src` in `bullion_mkultra.html` (the README has the sed one-liner;
   `connect-src 'self'` occurs exactly once). Commit both changes.
9. Smoke test: `curl -i "$URL/stats"` should return 401. Open the live map locally or after merging,
   click a node, switch tabs, close the tab, then open `$URL/dashboard` and check the numbers.
   Also check that `wrangler d1 execute ... "select * from seen"` shows only hashes.
10. Merge `bullion-analytics` into `main` (or open a PR), push, and confirm that GitHub Pages redeploys.

## Gotchas
- Only `bullion_mkultra.html` is instrumented. `release.sh` copies the live file, so future Mk versions inherit the tracker.
- My quick parse check flags a `</script>` inside a string in mkultra (the audit-log popup around line 6639). That issue was already on `main` and isn't a bug.
- If the user moves the site off `sinbadtheexplorer.github.io`, update `ALLOWED_ORIGIN` or every beacon will get a 403.
- `/e` can be spammed by anyone who forges the `Origin` header. Inputs are capped, but the numbers are directional. Cloudflare rate limiting is a possible follow-up.
- Secrets scan (all 5 repos, full history) was clean on 2026-10-12. The only hits were fake test keys in graywind.

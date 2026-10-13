# Bullion analytics

Usage stats for the Bullion map, from two counters that answer different
questions. Both are aggregate-only and cookieless, both are switched off by
Do Not Track / Global Privacy Control, and both are disclosed on the page.

| Counter | Answers | Where you read it |
|---|---|---|
| **Cloudflare Web Analytics** (Cloudflare's script) | How many people came, **which site sent them** (e.g. reddit.com), country, device, page speed | Cloudflare dashboard → Analytics & Logs → Web Analytics |
| **This Worker** (our own code, in this folder) | **What they did**: time on each tab and node, which nodes get opened, which shock scenarios get run, daily unique visitors | `https://bullion-analytics.<you>.workers.dev/dashboard` |

## Privacy design (do not weaken without updating the page's Privacy text)

| Not collected | How |
|---|---|
| Cookies / localStorage | Neither counter writes to the visitor's device, so no cookie banner is needed under the EU ePrivacy rules. |
| IP address, user agent | The Worker reads them once to compute `HMAC(dayKey, IP + UA)`, where `dayKey = HMAC(SALT_SECRET, date)`, so the hashing key changes every day. Only the hash is kept, and the daily cron deletes the previous day's hashes at 00:05 UTC whether or not anyone visits. The raw IP never reaches the database or the rate limiter. |
| Free text | The Worker only stores keys from a fixed allowlist (`src/allowlist.js`: the 39 node ids, 10 scenarios, 4 tabs). Anything else is dropped, so nothing typed on the page and nothing a forger sends can land in the database. |
| Visitors with DNT / GPC | Neither counter loads in the browser, and the Worker also drops the request server-side. |

Aggregate totals are kept for 400 days, then deleted by the same cron.

The page's start-screen note and its **Disclaimer & privacy → Privacy** section
describe exactly this. If you change what is collected, change that text in the
same commit. This is not legal advice; for a free, non-commercial page with
aggregate counts and this disclosure, it is low-risk under GDPR and CCPA. Get a
real review if Bullion ever becomes a business.

## Security model

- **`/e` (collect) is public by necessity.** Defences: exact `Origin` check
  (stops casual abuse, not curl), allowlisted keys, per-item caps on hits and
  time, duplicates merged per batch, an 8 KB body cap enforced while streaming,
  and rate limits (20/min per visitor hash, 600/min site-wide to protect the D1
  write quota). No `Content-Type` check on purpose: `navigator.sendBeacon`
  sends `text/plain`, and anything needing a CORS preflight would be dropped.
- **`/stats` fails closed.** It refuses everyone unless `STATS_TOKEN` is set
  and at least 32 characters. The comparison is constant-time (HMACs under a
  random key), only `Authorization: Bearer` is accepted, failed attempts are
  rate limited (10/min), and there are **no CORS headers**, so no other website
  can read the stats from a visitor's browser.
- **`/dashboard`** has a hash-based CSP (no `'unsafe-inline'`), builds every
  cell with `textContent` (no `innerHTML`), denies framing, sends no referrer,
  and keeps the token in memory only (never in storage or the URL).
- **Every response** carries `nosniff`, `no-referrer`, `no-store`, `noindex` and
  HSTS. Errors return a bare 500; details go to `wrangler tail` only.
- **Secrets** live only in Cloudflare (`wrangler secret put`). `.dev.vars` and
  `.env*` are gitignored. Never paste them into chat, commits or docs.

### Accepted risks (known, deliberate)

1. **Cloudflare's script is third-party code running on the page.** Cloudflare
   serves it from a URL whose contents it updates, so Subresource Integrity
   isn't practical (a pinned hash would break silently on their next update). The
   page's CSP limits it to `static.cloudflareinsights.com` (script) and
   `cloudflareinsights.com` (data), and the page holds no logins, secrets or
   personal data for it to reach. If you'd rather not run any third-party
   code, the Worker could record referring site and country itself
   (`Referer` header, `request.cf.country`) and the Cloudflare script could go.
2. **Forged events.** Anyone can replay the beacon with a fake `Origin`. The
   allowlist and caps bound what they can write; treat the numbers as
   directional, not audited.
3. **Quota exhaustion.** D1's free tier allows 100,000 row writes/day. The
   site-wide rate limit makes it hard but not impossible to burn through; if
   that happens the counter pauses until the next UTC day. The map itself is
   unaffected.
4. **Rate limits are approximate.** Cloudflare counts per location and
   eventually consistent, by design. Whether the binding is available on the
   Workers Free plan wasn't documented when this was written; if the account
   lacks it, `wrangler deploy` will say so and the code treats a missing
   binding as "no limit" rather than breaking.

## One-time setup (about 10 minutes, on your Mac)

Generate the two secrets with `openssl rand -base64 32` and type or paste them
at the prompts yourself. Keep `STATS_TOKEN` in your password manager.

```bash
cd analytics-worker
npx wrangler login
npx wrangler d1 create bullion-analytics      # copy the database_id it prints into wrangler.toml
npx wrangler d1 execute bullion-analytics --remote --file=schema.sql
npx wrangler secret put STATS_TOKEN           # 32+ chars, your dashboard login
npx wrangler secret put SALT_SECRET           # 32+ chars, never needed again
npx wrangler deploy                           # prints https://bullion-analytics.<you>.workers.dev
```

Cloudflare Web Analytics: Cloudflare dashboard → Analytics & Logs → Web
Analytics → Add a site → `sinbadtheexplorer.github.io` → copy the token from the
snippet (skip "automatic setup"; that only works for sites proxied through
Cloudflare).

## Going live: one commit

Turn everything on in a **single** commit so the page's behaviour, its CSP and
its privacy text always change together. In `bullion-live-map/bullion_mkultra.html`:

```bash
URL=https://bullion-analytics.YOURNAME.workers.dev
TOKEN=the_cloudflare_web_analytics_token
sed -i '' "s#var ANALYTICS_URL = '';#var ANALYTICS_URL = '$URL';#; \
           s#var CF_BEACON_TOKEN = '';#var CF_BEACON_TOKEN = '$TOKEN';#; \
           s#connect-src 'self'#connect-src 'self' $URL#" bullion-live-map/bullion_mkultra.html
```

The CF token is public by design (it ships in every visitor's page), so it is
safe to commit. Then check: `curl -i $URL/stats` returns 401, visit the live
map, click a node, close the tab, and the numbers appear on `/dashboard` and,
within a few minutes, in Cloudflare.

## Verify locally (no login needed)

```bash
cd analytics-worker
npm test                                                          # unit tests, node:sqlite stand-in for D1
npx wrangler d1 execute bullion-analytics --local --file=schema.sql
printf 'STATS_TOKEN=%s\nSALT_SECRET=%s\n' "$(openssl rand -hex 24)" "$(openssl rand -hex 24)" > .dev.vars
npx wrangler dev --local --test-scheduled                         # real workerd + real local D1
```

`/__scheduled?cron=5+0+*+*+*` fires the daily purge by hand.

## Limits to know

- **Visitors are counted once per day.** Someone who comes back on 3 days
  counts as 3 "visitor-days". Telling returning people apart would need a
  cookie, and that would need a consent banner.
- **Time stops after 2 minutes of no input**, so a tab left open overnight
  doesn't inflate the numbers.
- **Adding a node or scenario to the map?** Add its id to `src/allowlist.js`
  in the same commit. `npm test` fails if the two drift, and until it's added
  the Worker silently ignores that node.
- **Only the live version (`bullion_mkultra.html`) is instrumented.**
  `release.sh` copies it, so new Mk versions inherit the tracker automatically.

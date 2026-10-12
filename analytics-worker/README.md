# Bullion analytics

Private usage stats for the Bullion map. Only you can read them (the dashboard
needs a token only you set). It records three things:

1. **How many people visit**: daily unique visitors and page views.
2. **Where they stay longest**: visible time per tab and per node.
3. **What gets the most engagement**: node opens, tab switches, shock scenarios run.

## What it does NOT collect (and why that matters legally)

| Not collected | How |
|---|---|
| Cookies / localStorage | Nothing is written to the visitor's device, so no cookie banner is needed under the EU ePrivacy rules. |
| IP address, user agent | Read once to compute `sha256(secret + date + IP + UA)`, then thrown away. Only that hash is kept, only for the current UTC day. The salt changes daily, so one person can't be tracked across days. This is the same approach Plausible and Fathom use. |
| Anything typed or clicked outside the map's own tabs/nodes/scenarios | Only fixed IDs like `sec` or `rate_hike` are accepted. |
| Visitors with Do Not Track / Global Privacy Control on | Skipped in the browser *and* on the server. |

The start screen tells visitors: "Anonymous, cookie-free usage counts only."
That matches what the code does. If you ever add fingerprinting, identity,
or third-party scripts, update that line and re-check the law first.
This is not legal advice. For a student project with aggregate counts it is
low-risk under GDPR and CCPA, but get a real review if Bullion becomes a
business.

## One-time setup (about 10 minutes, on your Mac)

```bash
cd analytics-worker
npx wrangler login
npx wrangler d1 create bullion-analytics      # copy the database_id it prints into wrangler.toml
npx wrangler d1 execute bullion-analytics --remote --file=schema.sql
npx wrangler secret put STATS_TOKEN           # type a long password: this is your dashboard login
npx wrangler secret put SALT_SECRET           # type any long random string; you never need it again
npx wrangler deploy                           # prints https://bullion-analytics.<you>.workers.dev
```

Then switch the map on. Put your Worker URL in both places in
`bullion-live-map/bullion_mkultra.html`:

```bash
URL=https://bullion-analytics.YOURNAME.workers.dev
sed -i '' "s#var ANALYTICS_URL = '';#var ANALYTICS_URL = '$URL';#; s#connect-src 'self'#connect-src 'self' $URL#" bullion-live-map/bullion_mkultra.html
```

(The first replaces the URL constant. The second allows it in the page's
Content-Security-Policy, which otherwise blocks the request.) Commit and push.

**Read your stats:** open `https://bullion-analytics.<you>.workers.dev/dashboard`
and enter your `STATS_TOKEN`.

Free-tier cost: $0. Workers allow 100k requests/day and D1 allows 5 GB, far
more than this needs.

## Limits to know

- **Visitors are counted once per day.** Someone who comes back on 3 days
  counts as 3 "visitor-days". Telling returning people apart would need a
  cookie, and that would need a consent banner.
- **Time stops after 2 minutes of no input**, so a tab left open overnight
  doesn't inflate the numbers.
- **Anyone can send fake events with a forged `Origin` header.** Inputs are
  validated and capped, but treat the numbers as directional, not audited.
- **Only the live version (`bullion_mkultra.html`) is instrumented.**
  `release.sh` copies it, so new Mk versions inherit the tracker automatically.

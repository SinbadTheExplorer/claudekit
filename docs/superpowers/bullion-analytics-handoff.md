# Handoff: Bullion analytics (combined, hardened, ready to deploy)

**Written:** 2026-10-13 · **Branch:** `bullion-analytics` (not merged to `main`).
**Supersedes** the cloud session's version of this file (commit `6cc33fd`).

## Goal

See how many people use Bullion and what they do, legally and ethically. Two
versions were built in parallel: Cloudflare Web Analytics (Mac session) and a
custom Worker + D1 (phone/cloud session). The owner asked for both to be
combined and brought up to a high security standard. That is done; only
deployment remains.

- Design, security model, accepted risks, setup: `analytics-worker/README.md`
  (the authority, so trust it over this file)
- Page code: the `Usage analytics` script just before `</body>` in
  `bullion-live-map/bullion_mkultra.html`, plus the CSP `<meta>` near the top,
  the start-screen `.privacy-note`, and the Privacy section of `#disclaimer-modal`

## How to resume (do this first)

1. `git fetch origin && git log --oneline origin/main..origin/bullion-analytics`
2. `cd analytics-worker && npm test` → expect **18 passed**.
3. **Immediate next action:** the owner runs the setup in README "One-time
   setup" with the `!` prefix (auto mode can't run `wrangler login`/`deploy`).
   They type both secrets themselves. Never echo, log or commit them. They also
   create the Cloudflare Web Analytics site and paste its (public) token.
4. Then do README "Going live: one commit" on this branch (token + Worker URL +
   CSP in one commit), get the owner's yes, merge to `main`, push, and confirm the
   GitHub Pages deploy and a real visit on both dashboards.

## Current state

**Off by default.** `CF_BEACON_TOKEN` and `ANALYTICS_URL` are both `''`, so the
live page loads neither counter. Verified in headless Chrome: zero analytics
requests. ⚠️ The Privacy text on this branch already describes the counters,
so **don't merge to `main` until the go-live commit**, or the page describes
analytics it doesn't run.

**Changed vs the cloud session's version:**
- Worker: allowlisted keys (was regex-only, so a forger could create unlimited
  rows and inject text); HMAC with a per-day key (the old wording "salt rotates
  daily" was inaccurate because the secret was fixed); daily cron purge (old
  hashes outlived the day on quiet days); body cap enforced while streaming;
  rate limits; `/stats` fails closed under 32 chars, only accepts `Bearer`, and is
  rate limited; dashboard has a hash CSP and no `innerHTML`; security headers on
  every response; errors don't leak; `.dev.vars` gitignored; 400-day retention.
- Page: one script runs both counters, both gated on DNT/GPC and on their
  setting being filled in. The Cloudflare script is injected only then. The CSP
  allows exactly Cloudflare's two hosts (plus the Worker URL at go-live).
- Privacy text: the old paragraph still said "uses no analytics" (it would
  have contradicted the start-screen note). It is rewritten to match the code
  sentence by sentence.

## What has failed / risks / caveats

- **Nothing failed.** See README "Accepted risks": third-party CF script without
  SRI, forgeable events, D1 quota, approximate rate limits.
- **UNVERIFIED:** whether the Rate Limiting binding exists on the Workers Free
  plan (docs silent). `wrangler deploy` will tell; the code treats a missing
  binding as "no limit".
- **UNVERIFIED:** the CF beacon actually recording a visit. Locally it loaded,
  read the token and POSTed, but Cloudflare rejected `localhost` with a fake
  token (expected). The first real visit after go-live settles it.
- Out of scope, untouched: the page-wide CSP still allows `'unsafe-inline'`
  scripts (the whole app is inline), and the unmerged `security/news-link-scheme`
  branch from 2026-10-07.

## Verification idioms

- `npm test` in `analytics-worker/` (node:sqlite stand-in for D1, includes an
  allowlist ↔ page parity test). Mutation-checked: each security check, when
  removed, fails a test (the Content-Length precheck is backed up by the
  streaming cap, so removing only it is not caught).
- Real runtime: README "Verify locally" (`wrangler dev --local` + local D1).
  Proved dedupe (`meta.changes`), 429 after 20 beacons/min and after 10 bad
  `/stats` attempts, cron purge, dashboard headers.
- Page: serve over HTTP, patch a scratch copy with a local Worker URL, drive it
  with the `headless-chrome-verification` probe; inject
  `Navigator.prototype.globalPrivacyControl` / `doNotTrack` to prove both opt-outs
  send nothing.
- Python suite with Pillow: 182 passed, 1 pre-existing failure
  (`test_every_known_field_has_metadata`).

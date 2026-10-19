# Bullion — Changelog

## v1.0 — Released 2026-10-19

Live at https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/

The owner declared Bullion finished on 2026-10-19. From here on, fixing a broken data feed
counts as maintenance. It does not reopen the project.

### What it does

- **Interactive 3D map of the US financial system (Mk Ultra).** It has 39 nodes connected by
  causal links. Each node comes with beginner-level explanations, and chain-reaction paths show
  how a shock spreads from one node to the next.
- **Market health read.** It gives one overall score, then breaks it into five dimensions
  (Credit, Volatility, Equity valuation, Funding, Safe assets). Each dimension reads tight or
  loose and explains what is driving it.
- **Live data, updated daily, with no one running it.** A scheduled GitHub Actions job pulls
  FRED and Yahoo data into `data.json`.
- **Markets tab.** It shows an index dashboard and a financial news ticker built from 4 feeds
  across 3 vendors, with an alarm for each source if its feed goes stale.
- **"Set your own numbers."** You can enter your own values and see what the map does with them.
- **A backtest that grades itself in the page**, plus an offline calibration harness.
- **Privacy-respecting analytics**: Cloudflare Web Analytics plus its own Worker counter.

### What it does not do

- **No daily report gets pushed to you.** Original criterion 3b was never built. You have to
  open the site to see the analysis.
- **Nobody outside the owner has tested it as a teaching tool.** The 3-question feedback panel
  was never run, and the one Reddit post got no engagement.
- **News is "updated daily," not hourly.** GitHub only fires about 2 of the 9 scheduled news
  runs each day.
- **Not every link is verified.** 72 links are `directional`, not fitted measurements. 17 items
  are still unverified or have no source, including `china→tsy`, `geo→credit` and
  `hf→privcredit`. Each one shows its not-verified marker on the map.
- **Expert mode is hidden.** Beginner mode is always on, so the expert bullets can't be reached.
- **It is not investment advice.** It's a teaching map, and its causal claims are
  simplifications.

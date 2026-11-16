# Bullion constellation map

`bullion_mk10_constellation.html` is a self-contained financial "map" (a
node-and-edge graph of how Fed policy transmits through markets), built with
d3. Open it directly in a browser — no build step, no server required.

## Live data

The map ships with a static, hand-set simulated baseline (rates, VIX, CPI,
etc. as of roughly mid-2024) so it's always usable out of the box. It shows
a `⚪ Simulated` badge whenever no live data is loaded.

To pull real numbers in, run the fetcher next to the HTML file:

```bash
export FRED_API_KEY=your_key_here   # free key: https://fred.stlouisfed.org/docs/api/api_key.html
python3 fetch_bullion_data.py
```

This writes two files into the same directory:

- `bullion_live_data.js` — latest snapshot of each field
- `bullion_live_history.js` — trailing-year history, for the date picker

Reload the HTML (or refresh the page) and the badge switches to
`🟢 Live as of <timestamp>`. Re-run the script (e.g. from cron) to refresh.

Both generated files are gitignored — they're a live snapshot, not
something to commit, and go stale the moment they're written.

### Where each field comes from

| Field      | Source                                            |
|------------|----------------------------------------------------|
| `us2y`     | FRED `DGS2` — 2Y Treasury yield                     |
| `us10y`    | FRED `DGS10` — 10Y Treasury yield                   |
| `vix`      | FRED `VIXCLS` — CBOE VIX                            |
| `cpi_yoy`  | FRED `CPILFESL` — Core CPI index, YoY % computed locally |
| `wti_px`   | FRED `DCOILWTICO` — WTI crude spot                  |
| `nfp_mom`  | FRED `PAYEMS` — nonfarm payrolls level, MoM diff computed locally |
| `dxy`      | FRED `DTWEXBGS` — trade-weighted dollar index (closest free proxy for ICE DXY; not identical) |
| `spx`      | FRED `SP500`                                        |
| `ffr`      | FRED `DFF` — effective fed funds rate               |
| `gold_px`  | Stooq `XAUUSD` daily close (FRED has no maintained live gold series) |

`fomc_prob_hike/hold/cut` (FOMC odds) has no free live source and always
stays simulated — the map is explicit about this in its live-status text.

If a given series fails to fetch (network hiccup, FRED outage, bad key),
the script skips just that field and still writes the rest — partial data
beats no data, and the map already tracks liveness per field.

## Why it wasn't showing live data before

The HTML file expected `bullion_live_data.js` / `bullion_live_history.js`
to already exist next to it (loaded as plain `<script src>` tags, not
`fetch()`, so the page still works when opened via `file://`). Those two
files — and the script that generates them — didn't exist yet. A missing
file there fails silently by design, so the map fell back to its
simulated baseline instead of erroring. `fetch_bullion_data.py` is that
missing piece.

#!/usr/bin/env python3
"""
Pulls live macro data for the Bullion constellation map and writes
bullion_live_data.js / bullion_live_history.js next to the HTML file.

Sources:
  - FRED (https://fred.stlouisfed.org) for rates, CPI, payrolls, oil, the
    dollar index, the S&P 500, and the Fed funds rate. Needs a free API key:
    https://fred.stlouisfed.org/docs/api/api_key.html
  - Stooq (https://stooq.com) for spot gold (XAUUSD), which FRED does not
    carry as a live series. No key required.

Usage:
    export FRED_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    python3 fetch_bullion_data.py

Re-run it (e.g. from cron) to refresh the map's "live" data. Missing or
failed series are skipped rather than aborting the whole run -- the map
only treats a field as live if it got a number for it.
"""
import argparse
import csv
import io
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
STOOQ_GOLD_URL = "https://stooq.com/q/d/l/?s=xauusd&i=d"

# series_id -> (field name, transform)
#   "level"      value used as-is
#   "yoy_pct"    year-over-year percent change of the raw index (Core CPI)
#   "mom_diff"   month-over-month difference of the raw level (payrolls, in thousands)
FRED_SERIES = {
    "DGS2":     ("us2y",    "level"),
    "DGS10":    ("us10y",   "level"),
    "VIXCLS":   ("vix",     "level"),
    "DCOILWTICO": ("wti_px", "level"),
    "DTWEXBGS": ("dxy",     "level"),   # Trade-Weighted Dollar Index (Broad) -- closest free FRED proxy for ICE DXY
    "SP500":    ("spx",     "level"),
    "DFF":      ("ffr",     "level"),
    "CPILFESL": ("cpi_yoy", "yoy_pct"), # Core CPI index -> YoY %
    "PAYEMS":   ("nfp_mom", "mom_diff"),# Nonfarm payrolls level (thousands) -> MoM change
}


def fetch_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "bullion-map/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_fred_observations(series_id, api_key, start_date):
    url = (
        f"{FRED_BASE}?series_id={series_id}&api_key={api_key}"
        f"&file_type=json&observation_start={start_date}"
    )
    data = fetch_json(url)
    out = []
    for obs in data.get("observations", []):
        v = obs.get("value")
        if v is None or v == ".":
            continue
        try:
            out.append((obs["date"], float(v)))
        except ValueError:
            continue
    return out


def to_level_series(raw):
    return dict(raw)


def to_yoy_pct_series(raw):
    """YoY % change of a monthly index series, keyed by the later date."""
    by_date = dict(raw)
    dates = sorted(by_date)
    out = {}
    for d in dates:
        d_dt = datetime.strptime(d, "%Y-%m-%d")
        target = f"{d_dt.year - 1:04d}-{d_dt.month:02d}"
        prior = next((by_date[p] for p in dates if p.startswith(target)), None)
        if prior:
            out[d] = round((by_date[d] / prior - 1.0) * 100.0, 2)
    return out


def to_mom_diff_series(raw):
    """Month-over-month difference of a monthly level series."""
    dates = sorted(raw)
    out = {}
    for i in range(1, len(dates)):
        out[dates[i]] = round(raw[dates[i]] - raw[dates[i - 1]], 1)
    return out


def fetch_gold_series(days):
    req = urllib.request.Request(STOOQ_GOLD_URL, headers={"User-Agent": "bullion-map/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        text = resp.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    out = {}
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    for row in reader:
        d = row.get("Date")
        close = row.get("Close")
        if not d or not close or d < cutoff:
            continue
        try:
            out[d] = float(close)
        except ValueError:
            continue
    return out


def merge_forward_fill(field_series):
    """field_series: {field_name: {date: value}} -> sorted-date-forward-filled history."""
    all_dates = sorted({d for series in field_series.values() for d in series})
    history = {}
    last = {}
    for d in all_dates:
        for field, series in field_series.items():
            if d in series:
                last[field] = series[d]
        if last:
            history[d] = dict(last)
    return history


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api-key", default=os.environ.get("FRED_API_KEY"),
                         help="FRED API key (defaults to $FRED_API_KEY)")
    parser.add_argument("--days", type=int, default=400,
                         help="trailing window of history to fetch, in days (default 400)")
    parser.add_argument("--out-dir", default=os.path.dirname(os.path.abspath(__file__)),
                         help="directory to write bullion_live_data.js / bullion_live_history.js into")
    args = parser.parse_args()

    if not args.api_key:
        print(
            "No FRED API key found. Get a free one at "
            "https://fred.stlouisfed.org/docs/api/api_key.html then either:\n"
            "  export FRED_API_KEY=your_key_here\n"
            "  python3 fetch_bullion_data.py\n"
            "or pass --api-key your_key_here.",
            file=sys.stderr,
        )
        sys.exit(1)

    start_date = (datetime.now(timezone.utc) - timedelta(days=args.days)).strftime("%Y-%m-%d")
    field_series = {}
    failed = []

    for series_id, (field, transform) in FRED_SERIES.items():
        try:
            raw = fetch_fred_observations(series_id, args.api_key, start_date)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            failed.append((series_id, str(e)))
            continue
        if not raw:
            failed.append((series_id, "no observations returned"))
            continue
        raw_dict = dict(raw)
        if transform == "level":
            field_series[field] = to_level_series(raw)
        elif transform == "yoy_pct":
            field_series[field] = to_yoy_pct_series(raw_dict)
        elif transform == "mom_diff":
            field_series[field] = to_mom_diff_series(raw_dict)

    try:
        field_series["gold_px"] = fetch_gold_series(args.days)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        failed.append(("stooq:xauusd", str(e)))

    if not field_series:
        print("All sources failed -- nothing to write. Errors:", file=sys.stderr)
        for name, err in failed:
            print(f"  {name}: {err}", file=sys.stderr)
        sys.exit(1)

    history = merge_forward_fill(field_series)
    if not history:
        print("No history could be assembled.", file=sys.stderr)
        sys.exit(1)

    fetched_at = datetime.now(timezone.utc).isoformat()
    latest_date = sorted(history)[-1]
    latest = dict(history[latest_date])
    latest["fetched_at"] = fetched_at

    os.makedirs(args.out_dir, exist_ok=True)
    data_path = os.path.join(args.out_dir, "bullion_live_data.js")
    history_path = os.path.join(args.out_dir, "bullion_live_history.js")

    with open(data_path, "w") as f:
        f.write("window.BULLION_LIVE_DATA = ")
        json.dump(latest, f, indent=2)
        f.write(";\n")

    with open(history_path, "w") as f:
        f.write("window.BULLION_LIVE_HISTORY = ")
        json.dump(history, f, indent=2, sort_keys=True)
        f.write(";\n")

    print(f"Wrote {data_path} (as of {latest_date}, fields: {', '.join(sorted(latest.keys() - {'fetched_at'}))})")
    print(f"Wrote {history_path} ({len(history)} dates from {sorted(history)[0]} to {latest_date})")
    if failed:
        print("\nSome series failed and were skipped (their fields stay simulated in the map):", file=sys.stderr)
        for name, err in failed:
            print(f"  {name}: {err}", file=sys.stderr)


if __name__ == "__main__":
    main()

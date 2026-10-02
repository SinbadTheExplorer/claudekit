#!/usr/bin/env python3
"""Fetch live market data for Bullion Mk11 and write a date-keyed data.json.

FRED (official, requires a free key) covers us2y, us10y, cpi_yoy, vix, ffr,
wti_px, nfp_mom. Yahoo Finance's chart API (unofficial, undocumented, no key
needed) covers gold_px, dxy, spx. If every field fetches, data.json is
overwritten with the full set. If even one field fails to fetch, main()
refuses to write anything and exits non-zero instead, leaving the previous
(complete) data.json in place — a partial file, once written, is
indistinguishable from a healthy one to the fields that did come through.

fed_decision_kalshi/fed_decision_polymarket are the one exception to that
all-or-nothing rule: market-implied FOMC odds from Kalshi and Polymarket,
fetched best-effort in their own isolated try/except in main() so a hiccup
on either (unofficial, no key, no uptime guarantee) never blocks every other
field above from publishing.

Get a free FRED key at https://fred.stlouisfed.org/docs/api/api_key.html
then save it with:
  mkdir -p ~/.config/bullion && echo YOUR_KEY_HERE > ~/.config/bullion/fred_api_key
"""
import calendar
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

KEY_PATH = os.path.expanduser("~/.config/bullion/fred_api_key")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_OUT_PATH = os.path.join(OUT_DIR, "data.json")
HISTORY_DAYS = 365

# FRED series -> (output field, optional FRED `units` transform, decimals to round to)
FRED_SERIES = {
    "DGS2":       ("us2y",    None,  2),
    "DGS10":      ("us10y",   None,  2),
    "CPILFESL":   ("cpi_yoy", "pc1", 1),
    "VIXCLS":     ("vix",     None,  1),
    "DFF":        ("ffr",     None,  2),
    "DCOILWTICO": ("wti_px",  None,  2),
    "PAYEMS":     ("nfp_mom", "chg", 0),
    # Mk17 breadth
    "NFCI":         ("nfci",         None, 2),
    "M2SL":         ("m2",           None, 1),
    "MORTGAGE30US": ("mortgage_30y", None, 2),
    "BAMLH0A0HYM2": ("hy_oas",       None, 2),
    "BAMLC0A0CM":   ("ig_oas",       None, 2),
    "SOFR":         ("sofr",         None, 2),
    "DTB3":         ("tbill_3m",     None, 2),
    "WALCL":        ("fed_bs",       None, 1),
    "RRPONTSYD":    ("rrp",          None, 1),
}

# Yahoo Finance chart API. Unofficial/undocumented — no key, but could change
# or rate-limit without notice, unlike FRED's supported public API.
YAHOO_SYMBOLS = {
    "GC=F":      ("gold_px", 2),
    "DX-Y.NYB":  ("dxy",     2),
    "^GSPC":     ("spx",     2),
    "^IXIC":     ("nasdaq",  2),
    "^DJI":      ("dow",     2),
    # Mk17 sector ETFs
    "XLK":       ("xlk", 2),
    "XLF":       ("xlf", 2),
    "XLE":       ("xle", 2),
    "XLP":       ("xlp", 2),
}

# IMF SDMX 3.0 IRFCL dataflow has no world-aggregate entity for gold
# reserves (COUNTRY=G001 returns zero series for this indicator, confirmed
# against the live API 2026-08-11) -- this basket of the largest verified
# public holders is the closest available approximation to a global total.
# IRFCLDT1_IRFCL56V_FTO is "Official reserve assets, gold volume" in troy
# ounces; S1XS1311 ("Monetary Authorities and Central Government excl.
# Social Security") is the sector code with data for every country below --
# the narrower S1X ("Monetary authorities" alone) misses the USA, whose
# gold is held by the Treasury rather than the Fed.
IMF_GOLD_BASE_URL = "https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.STA/IRFCL/12.0.0"
IMF_GOLD_INDICATOR = "IRFCLDT1_IRFCL56V_FTO"
IMF_GOLD_SECTOR = "S1XS1311"
IMF_GOLD_COUNTRIES = ["USA", "DEU", "ITA", "FRA", "CHN", "RUS", "CHE", "IND", "JPN", "TUR", "NLD"]
TROY_OZ_PER_TONNE = 32150.7466

# IMF COFER (Currency Composition of Official Foreign Exchange Reserves).
# Unlike IRFCL gold reserves, IMF DOES publish a genuine COUNTRY=G001
# ("World") series for COFER (confirmed against the live API 2026-08-12),
# so this is a single fetch, not a per-country basket. AFXRA = "Allocated
# foreign exchange reserves"; CI_USD = "Claims in US dollar";
# SHRO_PT = "Shares" -- already a plain percentage (e.g. 58.38, not
# 0.5838), no unit conversion needed.
IMF_COFER_BASE_URL = "https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.STA/COFER/7.0.1"
IMF_COFER_INDICATOR = "AFXRA"
IMF_COFER_CURRENCY = "CI_USD"
IMF_COFER_TRANSFORM = "SHRO_PT"

# Cadence tolerances, in days, applied to a field's PUBLICATION date — never
# its reference date. June CPI references 2026-06-01 but publishes 2026-07-14;
# judged on reference date it looks broken, judged on publication it is on
# time. Calibrated 2026-07-20 against observed publication lags: daily FRED
# series ran 3-4 days, wti_px 5, CPI 6, PAYEMS 18.
CADENCE_TOLERANCE_DAYS = {
    "daily":   7,    # observed 3-4d; absorbs a three-day weekend plus a holiday
    "weekly":  10,   # NFCI (Wed), WALCL/H.4.1 (Thu), Freddie PMMS (Thu) post ~7d
                     # apart; 10 = 7 + slack for a holiday or a one-week slip.
    "monthly": 45,   # observed 6d and 18d; silent for 45d means genuinely broken
    # COFER's `published` is set equal to `ref_date` (no separate
    # publication date), so its reported age grows every day from a
    # quarter's end until the NEXT quarter's data replaces it -- it never
    # resets shortly after release the way FRED's `published` dates do.
    # Worst case, right before the next release: IMF's publication lag
    # after a quarter's own end, PLUS a full ~91-day quarter (we must wait
    # for the entire next quarter to complete before it can be released).
    # 180 was calibrated from a single mid-cycle snapshot (2026-08-11: 134
    # days) and undershoots that structural worst case; 210 covers it with
    # slack. Revisit once more release cycles have been observed in
    # production, the same way monthly's 45d was calibrated from multiple
    # fields over time.
    "quarterly": 210,
    # fed_decision_kalshi/fed_decision_polymarket use this cadence. Neither
    # "freshness" (there is no publication lag to judge, only a live snapshot)
    # nor "completeness" (see the `missing` gate in main()) apply to them the
    # way they do to a published economic statistic -- both checks below key
    # off this same cadence value.
    "fomc":    None,
}

# wti_px publishes on a structurally longer lag than the other dailies — it sat
# at 5 days while perfectly healthy, so the 7-day default would have produced a
# false alarm immediately.
#
# cb_gold_reserves sums 11 countries with independent national reporting
# lags. Observed 2026-08-11: the slowest of the 11 sat at 43 days (still
# on end-of-June data, fetched mid-August) while every country was
# reporting normally -- the 45-day monthly default would false-alarm on a
# single day's routine slip. 60 gives roughly the same cushion ratio
# wti_px's override gives over ITS observed lag.
# Raised to 75 on 2026-10-01: the USA alone sat on end-of-July data at
# 62 days while the other ten had August, so the basket (which is only as
# fresh as its slowest reporter) false-alarmed. One country a month behind is
# a routine reporting slip; a second missed month would still flag.
FIELD_TOLERANCE_OVERRIDE = {
    "wti_px": 10,
    "cb_gold_reserves": 75,
}

SCHEMA_VERSION = 2

# Provenance metadata per field. Every field written to data.json must appear
# here or it ships without provenance — which is the exact defect this schema
# exists to remove, so build_envelope raises rather than emitting a bare value.
FIELD_META = {
    "us2y":    {"class": "measured", "cadence": "daily",   "source": "FRED DGS2"},
    "us10y":   {"class": "measured", "cadence": "daily",   "source": "FRED DGS10"},
    "vix":     {"class": "measured", "cadence": "daily",   "source": "FRED VIXCLS"},
    "ffr":     {"class": "measured", "cadence": "daily",   "source": "FRED DFF"},
    "wti_px":  {"class": "measured", "cadence": "daily",   "source": "FRED DCOILWTICO"},
    "cpi_yoy": {"class": "measured", "cadence": "monthly", "source": "FRED CPILFESL"},
    "nfp_mom": {"class": "measured", "cadence": "monthly", "source": "FRED PAYEMS"},
    "gold_px": {"class": "measured", "cadence": "daily",   "source": "Yahoo GC=F"},
    "dxy":     {"class": "measured", "cadence": "daily",   "source": "Yahoo DX-Y.NYB"},
    "spx":     {"class": "measured", "cadence": "daily",   "source": "Yahoo ^GSPC"},
    "nasdaq":  {"class": "measured", "cadence": "daily",   "source": "Yahoo ^IXIC"},
    "dow":     {"class": "measured", "cadence": "daily",   "source": "Yahoo ^DJI"},
    # Mk17 breadth
    "nfci":         {"class": "measured", "cadence": "weekly",  "source": "FRED NFCI"},
    "m2":           {"class": "measured", "cadence": "monthly", "source": "FRED M2SL"},
    "mortgage_30y": {"class": "measured", "cadence": "weekly",  "source": "FRED MORTGAGE30US"},
    "hy_oas":       {"class": "measured", "cadence": "daily",   "source": "FRED BAMLH0A0HYM2"},
    "ig_oas":       {"class": "measured", "cadence": "daily",   "source": "FRED BAMLC0A0CM"},
    "sofr":         {"class": "measured", "cadence": "daily",   "source": "FRED SOFR"},
    "tbill_3m":     {"class": "measured", "cadence": "daily",   "source": "FRED DTB3"},
    "fed_bs":       {"class": "measured", "cadence": "weekly",  "source": "FRED WALCL"},
    "rrp":          {"class": "measured", "cadence": "daily",   "source": "FRED RRPONTSYD"},
    "xlk":          {"class": "measured", "cadence": "daily",   "source": "Yahoo XLK"},
    "xlf":          {"class": "measured", "cadence": "daily",   "source": "Yahoo XLF"},
    "xle":          {"class": "measured", "cadence": "daily",   "source": "Yahoo XLE"},
    "xlp":          {"class": "measured", "cadence": "daily",   "source": "Yahoo XLP"},
    "cb_gold_reserves": {"class": "measured", "cadence": "monthly",
                          "source": "IMF IRFCL (top-11 public holders, summed)"},
    "usd_reserve_share": {"class": "measured", "cadence": "quarterly",
                           "source": "IMF COFER (allocated reserves, USD share)"},
    "fed_decision_kalshi": {"class": "measured", "cadence": "fomc",
                             "source": "Kalshi KXFED ladder, bucketed against FRED DFEDTARU"},
    "fed_decision_polymarket": {"class": "measured", "cadence": "fomc",
                                 "source": "Polymarket 'Fed Decision' event"},
}


def build_envelope(latest_out, history_by_date, generated_at):
    """Assemble the schema v2 data.json envelope.

    `history` passes through untouched — the map's date picker reads it and its
    shape must not drift.
    """
    fields = {}
    for name, rec in latest_out.items():
        meta = FIELD_META.get(name)
        if meta is None:
            raise KeyError(
                f"field {name!r} has no FIELD_META entry; add one rather than "
                f"shipping a value with no provenance")
        fields[name] = {
            "class":     meta["class"],
            "cadence":   meta["cadence"],
            "source":    meta["source"],
            "ref_date":  rec["ref_date"],
            "published": rec["published"],
            "value":     rec["value"],
        }
    return {
        "schema": SCHEMA_VERSION,
        "generated_at": generated_at,
        "fields": fields,
        "history": history_by_date,
    }


def freshness_verdict(cadence, published, today, override_days=None):
    """Decide whether a field's latest value is fresh, judged on publication.

    Returns (state, age_days) where state is 'fresh', 'flagged' or 'unknown'.
    'unknown' means the question does not apply (simulated data) or cannot be
    answered (no publication date, unrecognised cadence) — callers must render
    nothing rather than guess.
    """
    if published is None or cadence == "fomc":
        return ("unknown", None)
    tolerance = override_days if override_days is not None else CADENCE_TOLERANCE_DAYS.get(cadence)
    if tolerance is None:
        return ("unknown", None)
    age_days = (today - published).days
    return ("flagged" if age_days > tolerance else "fresh", age_days)

SOURCE_NOTE = (
    "us2y/us10y/vix/ffr/wti_px: FRED daily series (DGS2, DGS10, VIXCLS, DFF, "
    "DCOILWTICO), official supported API. cpi_yoy: FRED CPILFESL, percent "
    "change from year ago. nfp_mom: FRED PAYEMS, month-over-month change "
    "(thousands). Mk17 adds FRED NFCI (financial conditions, weekly), M2SL "
    "(money supply, monthly), MORTGAGE30US (30Y mortgage, weekly), "
    "BAMLH0A0HYM2/BAMLC0A0CM (HY/IG credit OAS), SOFR, DTB3 (3M bill), WALCL "
    "(Fed balance sheet, weekly) and RRPONTSYD (overnight RRP). "
    "gold_px/dxy/spx and the Mk17 sector ETFs XLK/XLF/XLE/XLP: Yahoo Finance "
    "chart API — unofficial and undocumented, unlike FRED; could change or "
    "rate-limit without notice. "
    "fed_decision_kalshi/fed_decision_polymarket: market-implied odds for the "
    "next FOMC decision, from Kalshi's KXFED threshold ladder and "
    "Polymarket's 'Fed Decision' bracket event respectively -- both "
    "unofficial prediction markets, fetched best-effort and isolated from "
    "every other field (see main()): a failure here never blocks the rest "
    "of data.json from updating. "
    "cb_gold_reserves: IMF IRFCL (International Reserves and Foreign "
    "Currency Liquidity), summed across the 11 largest public holders "
    "(USA, Germany, Italy, France, China, Russia, Switzerland, India, "
    "Japan, Turkiye, Netherlands) -- IMF publishes no single world-"
    "aggregate entity for this indicator, so this is the largest holders, "
    "not a true global total. "
    "usd_reserve_share: IMF COFER (Currency Composition of Official "
    "Foreign Exchange Reserves), share of allocated reserves held in USD, "
    "world aggregate."
)


def load_key():
    try:
        with open(KEY_PATH, "r") as f:
            key = f.read().strip()
    except FileNotFoundError:
        print(f"No FRED API key found at {KEY_PATH}.", file=sys.stderr)
        print("Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html", file=sys.stderr)
        print(f"then run: mkdir -p {os.path.dirname(KEY_PATH)} && echo YOUR_KEY > {KEY_PATH}", file=sys.stderr)
        sys.exit(1)
    if not key:
        print(f"{KEY_PATH} is empty.", file=sys.stderr)
        sys.exit(1)
    return key


def http_get_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def parse_fred_observations(data, decimals):
    """Pure parse of a FRED observations payload.

    Returns (latest_value, ref_date, published, history). `published` comes
    from the observation's realtime_start, which is the date the reading
    became available — this is what freshness is judged on.

    A realtime RANGE request (see fetch_fred_series) makes FRED return one
    row PER VINTAGE per observation date, in undocumented server-side order.
    For each observation date we keep the row with the greatest
    realtime_start — the current, most-revised value — regardless of the
    order rows arrive in. A row with no realtime_start sorts as oldest, so
    any row that HAS one always wins over one that doesn't for the same date.
    """
    best_realtime_start_by_ref = {}
    history = {}
    published_by_ref = {}
    for obs in data.get("observations", []):
        val = obs.get("value")
        if val is None or val == ".":
            continue
        ref_date = obs.get("date")
        try:
            parsed_val = round(float(val), decimals)
        except (ValueError, TypeError):
            continue
        if ref_date is None:
            continue

        realtime_start = obs.get("realtime_start") or ""
        current_best = best_realtime_start_by_ref.get(ref_date)
        if current_best is not None and realtime_start <= current_best:
            continue  # an earlier (or equal) vintage than the one we already kept

        best_realtime_start_by_ref[ref_date] = realtime_start
        history[ref_date] = parsed_val
        published_by_ref[ref_date] = obs.get("realtime_start")

    if not history:
        return (None, None, None, {})
    latest_ref = max(history)
    return (history[latest_ref], latest_ref, published_by_ref.get(latest_ref), history)


def fred_url(params):
    return "https://api.stlouisfed.org/fred/series/observations?" + "&".join(
        f"{k}={urllib.request.quote(str(v))}" for k, v in params.items()
    )


def fred_observation_params(series_id, key, units, start, end):
    """Pure construction of the params dict for a values request.

    FRED returns HTTP 400 when a realtime RANGE (realtime_start/realtime_end)
    is combined with any `units` transform other than 'lin' — see
    fetch_fred_publication_date's docstring. So: `units` set means NO
    realtime keys; `units` unset means BOTH realtime keys, no `units` key.
    """
    params = {
        "series_id": series_id,
        "api_key": key,
        "file_type": "json",
        "sort_order": "asc",
        "observation_start": start,
        "observation_end": end,
    }
    if units:
        params["units"] = units
    else:
        # Safe only without a units transform — see fetch_fred_publication_date.
        params["realtime_start"] = start
        params["realtime_end"] = "9999-12-31"
    return params


def fetch_fred_publication_date(series_id, key, start, end):
    """Publication date of a series' latest observation, as its own request.

    Verified against the live API 2026-07-21: FRED rejects a realtime RANGE
    combined with any `units` transform other than 'lin' —

      400: "If output_type is '1' and units is not 'lin', then realtime_start
            must equal realtime_end..."

    CPILFESL uses units=pc1 and PAYEMS uses units=chg, so the two monthly
    series this whole feature exists for cannot carry realtime parameters on
    their values request. Publication date is a property of the observation and
    not of the transform, so the untransformed series answers the question and
    the observation dates join exactly.

    Note the trap: omitting realtime parameters entirely does NOT work either.
    FRED then returns realtime_start = today (a current-vintage marker), which
    would silently read as "published today" for every series.

    Returns (ref_date, published), or (None, None) if unavailable.
    """
    params = {
        "series_id": series_id,
        "api_key": key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
        "observation_start": start,
        "observation_end": end,
        "realtime_start": start,
        "realtime_end": "9999-12-31",
    }
    try:
        data = http_get_json(fred_url(params))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  FRED {series_id}: publication-date lookup failed ({e})", file=sys.stderr)
        return (None, None)
    obs = data.get("observations") or []
    if not obs:
        return (None, None)
    return (obs[0].get("date"), obs[0].get("realtime_start"))


def fetch_fred_series(series_id, key, units, decimals, start, end):
    """Network wrapper around parse_fred_observations."""
    params = fred_observation_params(series_id, key, units, start, end)

    try:
        data = http_get_json(fred_url(params))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  FRED {series_id}: fetch failed ({e})", file=sys.stderr)
        return (None, None, None, {})

    value, ref, pub, hist = parse_fred_observations(data, decimals)
    if value is None:
        print(f"  FRED {series_id}: no usable observations in range", file=sys.stderr)
        return (None, None, None, {})

    if units:
        # The values request could not carry realtime parameters, so the
        # publication date comes from a second, untransformed lookup.
        pub_ref, pub = fetch_fred_publication_date(series_id, key, start, end)
        if pub_ref and pub_ref != ref:
            print(f"  FRED {series_id}: publication lookup returned {pub_ref}, "
                  f"values latest is {ref}; leaving published unset", file=sys.stderr)
            pub = None

    return (value, ref, pub, hist)


def parse_yahoo_chart(data, decimals):
    """Pure parse of a Yahoo chart payload.

    Returns (latest_value, ref_date, published, history). For a daily close the
    reference date and publication date are the same day — the close IS the
    moment the number exists.
    """
    try:
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
        latest = result["meta"].get("regularMarketPrice")
    except (KeyError, IndexError, TypeError):
        return (None, None, None, {})

    history = {}
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        history[date_str] = round(float(close), decimals)

    if not history:
        return (None, None, None, {})
    latest_ref = max(history)
    latest = round(float(latest), decimals) if latest is not None else history[latest_ref]
    return (latest, latest_ref, latest_ref, history)


def fetch_yahoo_symbol(symbol, decimals, range_="1y"):
    """Network wrapper around parse_yahoo_chart."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(symbol)}"
           f"?range={range_}&interval=1d")
    try:
        data = http_get_json(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  Yahoo {symbol}: fetch failed ({e})", file=sys.stderr)
        return (None, None, None, {})

    value, ref, pub, hist = parse_yahoo_chart(data, decimals)
    if value is None:
        print(f"  Yahoo {symbol}: unexpected response shape or no usable data", file=sys.stderr)
    return (value, ref, pub, hist)


def imf_period_to_end_date(period):
    """Convert an SDMX 'YYYY-Mmm' or 'YYYY-Qn' period to its ISO period-end date.

    Handles both monthly (IRFCL gold reserves) and quarterly (COFER)
    periods -- the rest of the SDMX response shape is otherwise identical
    between these two IMF dataflows (confirmed against the live API
    2026-08-12), so a single period converter lets parse_imf_sdmx serve
    both rather than forking a near-duplicate parser. Returns None for
    anything not in one of these two exact shapes.
    """
    if len(period) == 8 and period[4] == "-" and period[5] == "M":
        try:
            year = int(period[:4])
            month = int(period[6:8])
        except ValueError:
            return None
        if not 1 <= month <= 12:
            return None
        last_day = calendar.monthrange(year, month)[1]
        return f"{year:04d}-{month:02d}-{last_day:02d}"
    if len(period) == 7 and period[4] == "-" and period[5] == "Q":
        try:
            year = int(period[:4])
            quarter = int(period[6])
        except ValueError:
            return None
        if not 1 <= quarter <= 4:
            return None
        month = quarter * 3
        last_day = calendar.monthrange(year, month)[1]
        return f"{year:04d}-{month:02d}-{last_day:02d}"
    return None


def parse_imf_sdmx(data):
    """Pure parse of an IMF SDMX 3.0 response's single data series into
    {date_iso: raw_numeric_value}.

    Shared by both the per-country IRFCL gold-reserves fetcher and the
    COFER world-aggregate fetcher -- the numeric unit (troy ounces vs.
    percent) and whether the series represents one country or a world
    aggregate are the caller's concern, not this parser's.

    date_iso is keyed by the LAST day of each reported period (a stock
    figure is naturally "as of period end"); returns {} for any
    missing/unrecognised shape or null value -- mirrors
    parse_fred_observations/parse_yahoo_chart's pure-parse-returns-empty-
    on-failure convention. No exception is raised here.
    """
    try:
        structures = data["data"]["structures"][0]
        period_values = structures["dimensions"]["observation"][0]["values"]
        series = data["data"]["dataSets"][0].get("series")
    except (KeyError, IndexError, TypeError):
        return {}
    if not series:
        return {}

    history = {}
    for s in series.values():
        for idx, obs in s.get("observations", {}).items():
            if not obs or obs[0] is None:
                continue
            try:
                oz = float(obs[0])
                period = period_values[int(idx)]["value"]
            except (KeyError, IndexError, TypeError, ValueError):
                continue
            date_iso = imf_period_to_end_date(period)
            if date_iso is not None:
                history[date_iso] = oz
    return history


def fetch_imf_country_series(country, start, end):
    """Network wrapper: one country's monthly gold-reserves history, in troy oz.

    Returns {date_iso: troy_oz}, or {} on any HTTP error or unparseable
    response -- same non-raising convention as fetch_fred_series/
    fetch_yahoo_symbol, so one bad country fails the basket closed (see
    fetch_imf_gold_reserves_basket) instead of crashing the whole run.

    Uses the SDMX 3.0 `c[TIME_PERIOD]=ge:...` filter, not the `startPeriod`
    query param the SDMX docs describe -- verified against the live API
    2026-08-11 that this dataflow silently ignores `startPeriod` entirely
    (always returns the full history back to 2000 regardless of its value)
    while `c[TIME_PERIOD]` correctly bounds the response.
    """
    start_period = start[:7]  # "YYYY-MM-DD" -> "YYYY-MM"
    url = (f"{IMF_GOLD_BASE_URL}/{country}.{IMF_GOLD_INDICATOR}.{IMF_GOLD_SECTOR}.M"
           f"?c%5BTIME_PERIOD%5D=ge:{start_period}")
    try:
        data = http_get_json(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  IMF {country}: fetch failed ({e})", file=sys.stderr)
        return {}
    hist = parse_imf_sdmx(data)
    if not hist:
        print(f"  IMF {country}: unexpected response shape or no usable data", file=sys.stderr)
    return hist


def fetch_imf_gold_reserves_basket(start, end):
    """Sum central-bank gold reserves (tonnes) across IMF_GOLD_COUNTRIES.

    IMF's IRFCL dataflow has no world-aggregate entity for gold reserves
    (confirmed against the live API 2026-08-11) -- this basket of the
    largest public holders is the closest available approximation to a
    global total. Any single country's fetch failing fails the whole
    field closed (returns the all-None tuple) rather than silently
    shipping an under-counted sum with no indication a holder is missing.

    Returns (latest_tonnes, ref_date, published, history) in the same
    shape fetch_fred_series/fetch_yahoo_symbol produce. ref_date and
    published are identical -- IMF's SDMX response carries no separate
    publication/vintage date, only a reference period, the same situation
    parse_yahoo_chart documents for a daily close -- and are set to the
    LATEST month every basket country has reported through: summing past
    that point would mix a stale country's old figure into an otherwise-
    current total.
    """
    per_country = {}
    for country in IMF_GOLD_COUNTRIES:
        hist = fetch_imf_country_series(country, start, end)
        if not hist:
            print(f"  IMF gold-reserves basket: {country} missing, "
                  f"failing the whole field", file=sys.stderr)
            return (None, None, None, {})
        per_country[country] = hist

    common_dates = set.intersection(*(set(h) for h in per_country.values()))
    if not common_dates:
        print("  IMF gold-reserves basket: no common reporting date across "
              "all countries", file=sys.stderr)
        return (None, None, None, {})

    history = {}
    for date_iso in common_dates:
        total_oz = sum(per_country[c][date_iso] for c in IMF_GOLD_COUNTRIES)
        history[date_iso] = round(total_oz / TROY_OZ_PER_TONNE, 1)

    latest_ref = max(history)
    return (history[latest_ref], latest_ref, latest_ref, history)


def fetch_usd_reserve_share(start, end):
    """Network wrapper: USD share of allocated global FX reserves, in percent.

    Reuses parse_imf_sdmx directly -- COFER's SDMX response shape is
    identical to IRFCL's (confirmed against the live API 2026-08-12), and
    IMF publishes a genuine COUNTRY=G001 ("World") series for COFER, unlike
    IRFCL gold reserves, so no per-country basket/sum is needed here.

    Returns (latest_value, ref_date, published, history) in the same shape
    every other fetcher produces, or (None, None, None, {}) on any HTTP
    error or unparseable response -- same non-raising convention as the
    rest of this file. ref_date and published are identical: COFER exposes
    no separate publication/vintage date, same situation as IRFCL.
    """
    # Snap to the start of the quarter containing `start`'s month: a plain
    # "YYYY-MM" truncation (as fetch_imf_country_series uses for its monthly
    # dataflow) can silently drop the earliest in-range quarter here, since
    # this dataflow is quarterly -- e.g. ge:2025-08 returns only
    # ['2025-Q4','2026-Q1'], skipping 2025-Q3 (July-September), which is
    # legitimately within an August-starting window.
    start_year, start_month = int(start[:4]), int(start[5:7])
    quarter_start_month = ((start_month - 1) // 3) * 3 + 1
    start_period = f"{start_year:04d}-{quarter_start_month:02d}"
    url = (f"{IMF_COFER_BASE_URL}/G001.{IMF_COFER_INDICATOR}.{IMF_COFER_CURRENCY}."
           f"{IMF_COFER_TRANSFORM}.Q?c%5BTIME_PERIOD%5D=ge:{start_period}")
    try:
        data = http_get_json(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  IMF COFER: fetch failed ({e})", file=sys.stderr)
        return (None, None, None, {})
    hist = parse_imf_sdmx(data)
    if not hist:
        print("  IMF COFER: unexpected response shape or no usable data", file=sys.stderr)
        return (None, None, None, {})
    rounded = {d: round(v, 1) for d, v in hist.items()}
    latest_ref = max(rounded)
    return (rounded[latest_ref], latest_ref, latest_ref, rounded)


# ─── FOMC rate-decision odds (Kalshi + Polymarket) ──────────────────────────
# Isolated from every fetcher above: those are official/stable enough that
# one failing should abort the whole run (see main()'s docstring). Kalshi and
# Polymarket are unofficial prediction markets with no uptime guarantee, so a
# failure here must never block gold_px/dxy/etc. from updating -- both
# fetchers are called inside their own try/except in main() and their
# FIELD_META cadence ("fomc") is exempt from the completeness gate.
KALSHI_API_BASE = "https://api.elections.kalshi.com/trade-api/v2"
KALSHI_FED_SERIES = "KXFED"
KALSHI_LADDER_STEP = 0.25  # observed rung spacing (verified against the live API 2026-09-08)
FRED_TARGET_UPPER_SERIES = "DFEDTARU"  # current target-range upper bound -- the baseline the Kalshi ladder is diffed against
POLYMARKET_GAMMA_BASE = "https://gamma-api.polymarket.com"
POLYMARKET_GROUP_TO_BUCKET = {
    "50+ bps decrease": "cut50plus",
    "25 bps decrease": "cut25",
    "No change": "hold",
    "25 bps increase": "hike25",
    "50+ bps increase": "hike50plus",
}


def kalshi_market_prob(market):
    """Yes-probability for one Kalshi market: midpoint of bid/ask, falling
    back to last trade price when the book is one-sided or empty (thin,
    far-dated FOMC rungs often have no resting bid)."""
    def to_float(x):
        try:
            return float(x) if x is not None else None
        except (TypeError, ValueError):
            return None

    bid, ask = to_float(market.get("yes_bid_dollars")), to_float(market.get("yes_ask_dollars"))
    if bid is not None and ask is not None and (bid > 0 or ask > 0):
        return (bid + ask) / 2
    return to_float(market.get("last_price_dollars"))


def parse_kalshi_ladder(markets, current_upper):
    """Pure parse: one FOMC event's Kalshi threshold markets, plus the
    current target-upper-bound baseline, -> cut/hold/hike buckets.

    Kalshi has no single "will the Fed cut" market for a meeting -- KXFED is
    a ladder of binary "will the upper bound end up above $K" contracts, one
    rung per quarter-point. Each resolves Yes iff the post-meeting rate is
    strictly above its floor_strike, so consecutive rungs (STEP apart) give
    P(rate == K) = P(rate > K-STEP) - P(rate > K). The ladder observed in
    practice already spans far enough that the two open ends carry ~0-1%
    mass, so they're folded into the outermost bucket rather than tracked
    separately. Returns None if fewer than 2 usable rungs survive.
    """
    rungs = sorted(
        (float(m["floor_strike"]), kalshi_market_prob(m))
        for m in markets
        if m.get("floor_strike") is not None and kalshi_market_prob(m) is not None
    )
    if len(rungs) < 2:
        return None
    strikes = [r[0] for r in rungs]
    prob_above = [r[1] for r in rungs]

    def bucket_for(level):
        delta = round((level - current_upper) / KALSHI_LADDER_STEP)
        if delta <= -2: return "cut50plus"
        if delta == -1: return "cut25"
        if delta == 0:  return "hold"
        if delta == 1:  return "hike25"
        return "hike50plus"

    buckets = {"cut50plus": 0.0, "cut25": 0.0, "hold": 0.0, "hike25": 0.0, "hike50plus": 0.0}
    # Below the lowest rung: P(rate <= strikes[0]).
    buckets[bucket_for(strikes[0])] += max(1.0 - prob_above[0], 0.0)
    # Each interior rung: P(rate == strikes[i]) = prob_above[i-1] - prob_above[i].
    for i in range(1, len(rungs)):
        buckets[bucket_for(strikes[i])] += max(prob_above[i - 1] - prob_above[i], 0.0)
    # Above the highest rung: P(rate > strikes[-1]).
    buckets[bucket_for(strikes[-1] + KALSHI_LADDER_STEP)] += max(prob_above[-1], 0.0)
    return {k: round(v, 4) for k, v in buckets.items()}


def fetch_kalshi_fed_decision(current_upper):
    """Network wrapper: resolve the next open KXFED event dynamically, fetch
    its ladder, and bucket it via parse_kalshi_ladder.

    Several KXFED events are open simultaneously (this meeting's ladder plus
    the next several) -- the event is picked by earliest close_time still in
    the future rather than a hardcoded ticker like "KXFED-26SEP", which
    would silently go stale within weeks of shipping (each meeting's ladder
    closes ~6 weeks after the last one). No API key needed -- Kalshi's
    markets-read endpoint is anonymous (verified against the live API
    2026-09-08). Returns None on any failure.
    """
    url = f"{KALSHI_API_BASE}/markets?series_ticker={KALSHI_FED_SERIES}&status=open&limit=1000"
    try:
        data = http_get_json(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  Kalshi {KALSHI_FED_SERIES}: fetch failed ({e})", file=sys.stderr)
        return None

    by_event = {}
    for m in data.get("markets", []):
        et = m.get("event_ticker")
        if et and m.get("close_time"):
            by_event.setdefault(et, []).append(m)
    if not by_event:
        print(f"  Kalshi {KALSHI_FED_SERIES}: no open markets returned", file=sys.stderr)
        return None

    now = datetime.now(timezone.utc)
    def close_dt(et):
        try:
            return datetime.strptime(by_event[et][0]["close_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    future = [(close_dt(et), et) for et in by_event]
    future = [(c, et) for c, et in future if c and c > now]
    if not future:
        print(f"  Kalshi {KALSHI_FED_SERIES}: no future event found", file=sys.stderr)
        return None
    close, next_event = min(future, key=lambda ce: ce[0])

    buckets = parse_kalshi_ladder(by_event[next_event], current_upper)
    if buckets is None:
        print(f"  Kalshi {next_event}: fewer than 2 usable ladder rungs", file=sys.stderr)
        return None
    return {"event": next_event, "meeting_close": close.strftime("%Y-%m-%d"),
            "current_upper": current_upper, "buckets": buckets}


def parse_polymarket_fed_event(event):
    """Pure parse: one Polymarket 'Fed Decision' event -> bucket probabilities.

    Unlike Kalshi's threshold ladder, Polymarket structures this event as
    five directly-labelled brackets (POLYMARKET_GROUP_TO_BUCKET) with a
    first-class Yes price per bracket -- no threshold math needed. The Yes
    price of an "X happens" market IS its market-implied probability.
    Returns None if fewer than 3 of the 5 expected brackets parse.
    """
    buckets = {}
    for m in event.get("markets", []):
        bucket = POLYMARKET_GROUP_TO_BUCKET.get(m.get("groupItemTitle"))
        if bucket is None:
            continue
        try:
            prices = json.loads(m.get("outcomePrices", "[]"))
            buckets[bucket] = round(float(prices[0]), 4)
        except (ValueError, IndexError, TypeError, json.JSONDecodeError):
            continue
    return buckets if len(buckets) >= 3 else None


def fetch_polymarket_fed_decision():
    """Network wrapper: find the next open 'Fed Decision in <Month>' event
    and parse its bracket probabilities via parse_polymarket_fed_event.

    Resolved dynamically the same way as the Kalshi event (earliest endDate
    still in the future) -- Polymarket also runs one of these events per
    FOMC meeting under a rotating slug (fed-decision-in-september-762,
    fed-decision-in-october-..., ...), so a hardcoded slug would go stale
    the same way a hardcoded Kalshi ticker would. No API key needed --
    Polymarket's gamma-api is a public read endpoint. Returns None on any
    failure.
    """
    url = f"{POLYMARKET_GAMMA_BASE}/events?tag_slug=fed&closed=false&limit=100"
    try:
        events = http_get_json(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  Polymarket fed events: fetch failed ({e})", file=sys.stderr)
        return None

    now = datetime.now(timezone.utc)
    candidates = []
    for e in events:
        if not e.get("title", "").startswith("Fed Decision in "):
            continue
        end = e.get("endDate")
        if not end:
            continue
        try:
            end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if end_dt > now:
            candidates.append((end_dt, e))
    if not candidates:
        print("  Polymarket fed events: no future 'Fed Decision' event found", file=sys.stderr)
        return None
    end_dt, event = min(candidates, key=lambda c: c[0])

    buckets = parse_polymarket_fed_event(event)
    if buckets is None:
        print(f"  Polymarket {event.get('slug')}: fewer than 3 usable brackets", file=sys.stderr)
        return None
    return {"event": event.get("slug"), "meeting_close": end_dt.strftime("%Y-%m-%d"), "buckets": buckets}
# ─── end FOMC rate-decision odds ─────────────────────────────────────────────


def main():
    key = load_key()
    today = datetime.now(timezone.utc).date()
    start = (today - timedelta(days=HISTORY_DAYS)).isoformat()
    end = today.isoformat()

    latest_out = {}
    history_by_date = {}  # date_str -> {field: value}

    for series_id, (field, units, decimals) in FRED_SERIES.items():
        value, ref, pub, hist = fetch_fred_series(series_id, key, units, decimals, start, end)
        if value is not None:
            latest_out[field] = {"value": value, "ref_date": ref, "published": pub}
        for date_str, val in hist.items():
            history_by_date.setdefault(date_str, {})[field] = val

    for symbol, (field, decimals) in YAHOO_SYMBOLS.items():
        value, ref, pub, hist = fetch_yahoo_symbol(symbol, decimals)
        if value is not None:
            latest_out[field] = {"value": value, "ref_date": ref, "published": pub}
        for date_str, val in hist.items():
            history_by_date.setdefault(date_str, {})[field] = val

    imf_value, imf_ref, imf_pub, imf_hist = fetch_imf_gold_reserves_basket(start, end)
    if imf_value is not None:
        latest_out["cb_gold_reserves"] = {"value": imf_value, "ref_date": imf_ref, "published": imf_pub}
    for date_str, val in imf_hist.items():
        history_by_date.setdefault(date_str, {})["cb_gold_reserves"] = val

    cofer_value, cofer_ref, cofer_pub, cofer_hist = fetch_usd_reserve_share(start, end)
    if cofer_value is not None:
        latest_out["usd_reserve_share"] = {"value": cofer_value, "ref_date": cofer_ref, "published": cofer_pub}
    for date_str, val in cofer_hist.items():
        history_by_date.setdefault(date_str, {})["usd_reserve_share"] = val

    # Isolated best-effort block: neither fetcher's failure may raise past
    # here or touch history_by_date/the completeness gate below (see the
    # cadence="fomc" exemption in FIELD_META and CADENCE_TOLERANCE_DAYS).
    try:
        current_upper, _, _, _ = fetch_fred_series(FRED_TARGET_UPPER_SERIES, key, None, 2, start, end)
        kalshi = fetch_kalshi_fed_decision(current_upper) if current_upper is not None else None
        if kalshi is not None:
            latest_out["fed_decision_kalshi"] = {
                "value": kalshi, "ref_date": today.isoformat(), "published": today.isoformat()}
    except Exception as e:
        print(f"  Kalshi FOMC fetch failed, skipping (isolated from the rest of the run): {e}", file=sys.stderr)

    try:
        polymarket = fetch_polymarket_fed_decision()
        if polymarket is not None:
            latest_out["fed_decision_polymarket"] = {
                "value": polymarket, "ref_date": today.isoformat(), "published": today.isoformat()}
    except Exception as e:
        print(f"  Polymarket FOMC fetch failed, skipping (isolated from the rest of the run): {e}", file=sys.stderr)

    if not history_by_date:
        print("No fields fetched successfully; leaving existing data.json untouched.", file=sys.stderr)
        sys.exit(1)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    envelope = build_envelope(latest_out, history_by_date, generated_at)

    # Log every field's publication age so the tolerances above can be revised
    # against observed behaviour instead of re-guessed. Printed before the
    # completeness gate below so an operator can see exactly which field(s)
    # are missing even on a run that aborts without writing.
    today = datetime.now(timezone.utc).date()
    print("\nPublication ages (freshness is judged on these, not ref_date):")
    for name in sorted(envelope["fields"]):
        fld = envelope["fields"][name]
        pub = fld["published"]
        pub_date = datetime.strptime(pub, "%Y-%m-%d").date() if pub else None
        state, age = freshness_verdict(
            fld["cadence"], pub_date, today,
            override_days=FIELD_TOLERANCE_OVERRIDE.get(name))
        marker = "  FLAGGED" if state == "flagged" else ""
        age_str = f"{age}d" if age is not None else "n/a"
        print(f"  {name:10s} ref={fld['ref_date']} pub={pub} age={age_str:>5s} {state}{marker}")

    # A partial fetch must never publish a truncated data.json: the daily
    # cron commits whatever this writes, so a flaky minute at FRED would
    # otherwise ship nine real fields and one silently-simulated one behind
    # a green CI check. Yesterday's complete file, left untouched, is
    # strictly better than today's truncated one — every run rebuilds the
    # full rolling year from scratch anyway, so skipping a day loses nothing.
    # fomc-cadence fields (fed_decision_kalshi/fed_decision_polymarket) are
    # exempt: they're fetched best-effort in their own isolated try/except
    # above specifically so a Kalshi/Polymarket hiccup never blocks the
    # official FRED/Yahoo/IMF fields below from publishing.
    missing = [f for f in FIELD_META
               if f not in envelope["fields"] and FIELD_META[f]["cadence"] != "fomc"]
    if missing:
        print(f"\nFailed to fetch: {', '.join(missing)}", file=sys.stderr)
        print("Refusing to write a truncated data.json; leaving the existing "
              "file untouched.", file=sys.stderr)
        sys.exit(1)

    with open(DATA_OUT_PATH, "w") as f:
        json.dump(envelope, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"\nWrote {DATA_OUT_PATH} (schema {SCHEMA_VERSION}) with "
          f"{len(history_by_date)} dated entries and {len(envelope['fields'])} fields.")
    print()
    print(SOURCE_NOTE)


if __name__ == "__main__":
    main()

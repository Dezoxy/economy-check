#!/usr/bin/env python3
"""As-of cache backfill for step-F backtests.

  python3 shared/fetchers/backfill.py --date 2026-07-05 [--sources a,b,c] [--force]

Writes data/cache/<date>/<source>.json exactly as a run on that day would have
seen the world — historical API endpoints only, no today-values. Every record
carries "backfill": true. Sources whose history is unreachable are SKIPPED
(they show up as degraded/missing in --verify, which is the honest state).

Lookahead discipline: everything here slices at end-of-day <date> UTC.
"""
import argparse
import re
import sys
import time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import base  # noqa: E402
import indicators as ind  # noqa: E402
from binance_klines import MIRRORS, _cols  # noqa: E402
from etf_flows import _parse_table  # noqa: E402
from fred import SERIES  # noqa: E402


def _day_end_ms(d):
    dt = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int((dt + timedelta(days=1)).timestamp() * 1000) - 1


def _klines_asof(symbol, interval, limit, end_ms):
    last_err = None
    for root in MIRRORS:
        url = ("%s/klines?symbol=%s&interval=%s&limit=%d&endTime=%d"
               % (root, symbol, interval, limit, end_ms))
        try:
            raw = base.http_get_json(url)
            if isinstance(raw, list) and raw:
                return raw, url
        except base.FetchError as e:
            last_err = e
    raise base.FetchError("mirrors failed for %s: %s" % (symbol, last_err))


def bf_binance_klines(d, cfg):
    end_ms = _day_end_ms(d)

    def daily(symbol):
        raw, url = _klines_asof(symbol, "1d", 1000, end_ms)
        older, _ = _klines_asof(symbol, "1d", 1000, int(raw[0][0]) - 1)
        if older and older[-1][0] < raw[0][0]:
            raw = older + raw
        live = float(raw[-1][4])
        raw = raw[:-1]  # the as-of day's candle was still open at post time
        highs, lows, closes, vols = _cols(raw)
        rsi = ind.rsi_wilder_series(closes)
        rsi_clean = [r for r in rsi if r is not None]
        mid, up, lo = ind.bollinger(closes)
        anchor = ind.cycle_low_index(lows, lookback=len(lows))
        poc, shelves = ind.volume_profile_poc(closes, vols)
        return {
            "close": closes[-1], "price_live": live, "prev_close": closes[-2],
            "week_high": max(highs[-7:]), "week_low": min(lows[-7:]),
            "ma50d": ind.sma(closes, 50), "ma100d": ind.sma(closes, 100),
            "ma150d": ind.sma(closes, 150), "ma200d": ind.sma(closes, 200),
            "boll_mid": mid, "boll_upper": up, "boll_lower": lo,
            "rsi14d": rsi[-1], "rsi14d_ma14": ind.sma(rsi_clean, 14),
            "vwap_cycle_low": ind.anchored_vwap(highs, lows, closes, vols, anchor),
            "vwap_anchor_date": datetime.fromtimestamp(
                raw[anchor][0] / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
            "poc_180d": poc, "volume_shelves_180d": shelves,
        }, url

    def weekly(symbol):
        raw, _ = _klines_asof(symbol, "1w", 520, end_ms)
        raw = raw[:-1]
        _, _, closes, _ = _cols(raw)
        rsi = ind.rsi_wilder_series(closes)
        rsi_clean = [r for r in rsi if r is not None]
        return {"close_w": closes[-1], "ma200w": ind.sma(closes, 200),
                "ma100w": ind.sma(closes, 100), "rsi14w": rsi[-1],
                "rsi14w_ma14": ind.sma(rsi_clean, 14)}

    data = {}
    btc_d, url = daily("BTCUSDT")
    for prefix, block in (("btc", btc_d), ("btc", weekly("BTCUSDT")),
                          ("eth", daily("ETHUSDT")[0]), ("eth", weekly("ETHUSDT"))):
        for k, v in block.items():
            data["%s_%s" % (prefix, k)] = round(v, 2) if isinstance(v, float) else v
    return data, url


def bf_feargreed(d, cfg):
    url = "https://api.alternative.me/fng/?limit=0"
    rows = base.http_get_json(url).get("data") or []
    end_ts = _day_end_ms(d) / 1000
    hist = [r for r in rows if float(r["timestamp"]) <= end_ts][:30]
    if not hist:
        raise base.FetchError("no F&G history at %s" % d)
    now, week = hist[0], hist[7] if len(hist) > 7 else hist[-1]
    return {"value": int(now["value"]), "classification": now["value_classification"],
            "week_ago_value": int(week["value"]),
            "week_ago_classification": week["value_classification"],
            "month_min": min(int(r["value"]) for r in hist),
            "month_max": max(int(r["value"]) for r in hist),
            "history_30d": [int(r["value"]) for r in hist]}, url


def bf_defillama(d, cfg):
    end_ts = _day_end_ms(d) / 1000

    def series_at(rows, key_path, ts_key="date"):
        vals = [(float(r[ts_key]), r) for r in rows if float(r[ts_key]) <= end_ts]
        if not vals:
            raise base.FetchError("defillama history empty at %s" % d)
        vals.sort()
        cur = vals[-1][1]
        week = next((r for t, r in reversed(vals) if t <= end_ts - 7 * 86400), cur)
        def dig(r):
            for k in key_path:
                r = r[k]
            return float(r)
        return dig(cur), dig(week)

    tvl_rows = base.http_get_json("https://api.llama.fi/v2/historicalChainTvl")
    tvl_now, _ = series_at(tvl_rows, ["tvl"])
    tot = base.http_get_json("https://stablecoins.llama.fi/stablecoincharts/all")
    st_now, st_week = series_at(tot, ["totalCirculating", "peggedUSD"])
    time.sleep(1)
    usdt = base.http_get_json("https://stablecoins.llama.fi/stablecoincharts/all?stablecoin=1")
    t_now, t_week = series_at(usdt, ["totalCirculating", "peggedUSD"])
    usdc = base.http_get_json("https://stablecoins.llama.fi/stablecoincharts/all?stablecoin=2")
    c_now, c_week = series_at(usdc, ["totalCirculating", "peggedUSD"])
    return {
        "tvl_total_usd": round(tvl_now, 0), "tvl_top_chains": None,
        "stablecoin_total_musd": round(st_now / 1e6, 1),
        "stablecoin_week_delta_musd": round((st_now - st_week) / 1e6, 1),
        "usdt_mcap_musd": round(t_now / 1e6, 1),
        "usdt_week_delta_musd": round((t_now - t_week) / 1e6, 1),
        "usdc_mcap_musd": round(c_now / 1e6, 1),
        "usdc_week_delta_musd": round((c_now - c_week) / 1e6, 1),
    }, "llama.fi historical + stablecoincharts"


def bf_fx_rates(d, cfg):
    usd = base.http_get_json("https://api.frankfurter.dev/v1/%s?base=USD&symbols=HUF,EUR" % d)
    eur = base.http_get_json("https://api.frankfurter.dev/v1/%s?base=EUR&symbols=HUF" % d)
    return {"usd_huf": round(float(usd["rates"]["HUF"]), 2),
            "usd_eur": round(float(usd["rates"]["EUR"]), 4),
            "eur_huf": round(float(eur["rates"]["HUF"]), 2),
            "rate_date": usd["date"]}, "frankfurter.dev historical"


def bf_fred(d, cfg, env):
    key = env.get("FRED_API_KEY")
    if not key:
        raise base.FetchError("FRED_API_KEY missing")
    series = {}
    for name, (sid, units) in SERIES.items():
        url = ("https://api.stlouisfed.org/fred/series/observations?series_id=%s"
               "&api_key=%s&file_type=json&sort_order=desc&limit=8&units=%s"
               "&realtime_start=%s&realtime_end=%s&observation_end=%s"
               % (sid, key, units, d, d, d))
        try:
            obs = [o for o in base.http_get_json(url).get("observations") or []
                   if o.get("value") not in (".", None)]
        except base.FetchError:
            obs = []
        series[name] = None if not obs else {
            "value": float(obs[0]["value"]), "date": obs[0]["date"],
            "prior": float(obs[1]["value"]) if len(obs) > 1 else None,
            "prior_date": obs[1]["date"] if len(obs) > 1 else None}
        time.sleep(0.4)
    if all(v is None for v in series.values()):
        raise base.FetchError("no vintage observations at %s" % d)
    return {"series": series, "vintage": d}, "FRED/ALFRED realtime=%s" % d


def bf_etf_flows(d, cfg):
    # the /btc/ front page shows only the recent window; the all-data pages hold
    # the complete daily history back to the 2024 launches
    root = "https://farside.co.uk"
    out = {}
    btc = [r for r in _parse_table(
        base.http_get(root + "/bitcoin-etf-flow-all-data/"), "btc",
        keep_all=True) if r["date"] <= d]
    if not btc:
        raise base.FetchError("no farside rows at or before %s" % d)
    btc = btc[-10:]
    out["btc_daily_flows_musd"] = btc
    out["btc_week_total_musd"] = round(sum(r["total_musd"] for r in btc[-5:]), 1)
    out["btc_latest_flow_date"] = btc[-1]["date"]
    try:
        eth = [r for r in _parse_table(
            base.http_get(root + "/ethereum-etf-flow-all-data/"), "eth",
            keep_all=True) if r["date"] <= d][-10:]
        out["eth_daily_flows_musd"] = eth
        out["eth_week_total_musd"] = round(sum(r["total_musd"] for r in eth[-5:]), 1)
    except base.FetchError:
        out["eth_daily_flows_musd"] = None
    return out, root + "/*-all-data/ (rows <= %s)" % d


def bf_binance_funding(d, cfg):
    end_ms = _day_end_ms(d)
    data = {}
    for sym, p in (("BTCUSDT", "btc"), ("ETHUSDT", "eth")):
        hist = base.http_get_json(
            "https://fapi.binance.com/fapi/v1/fundingRate?symbol=%s&limit=21&endTime=%d"
            % (sym, end_ms))
        if not hist:
            raise base.FetchError("no funding history at %s" % d)
        rates = [float(h["fundingRate"]) for h in hist]
        data[p + "_funding_pct"] = round(rates[-1] * 100, 4)
        data[p + "_funding_week_avg_pct"] = round(sum(rates) / len(rates) * 100, 4)
        oi = base.http_get_json(
            "https://fapi.binance.com/futures/data/openInterestHist?symbol=%s"
            "&period=1d&limit=30" % sym)
        rows = [r for r in oi if int(r["timestamp"]) <= end_ms]
        if rows:  # only exists ~30 days back — absent for older backtests
            data[p + "_oi_coins"] = round(float(rows[-1]["sumOpenInterest"]), 1)
            data[p + "_oi_usd"] = round(float(rows[-1]["sumOpenInterestValue"]), 0)
        else:
            data[p + "_oi_coins"] = None
            data[p + "_oi_usd"] = None
    return data, "fapi.binance.com fundingRate+openInterestHist (asof)"


def bf_fed_calendar(d, cfg):
    import fed_calendar as fc
    html = base.http_get(cfg["base_url"])
    meetings = []
    for ym in re.finditer(r"(20\d\d) FOMC Meetings(.*?)(?=20\d\d FOMC Meetings|$)",
                          html, re.S):
        year = int(ym.group(1))
        for mm in re.finditer(
                r"(January|February|March|April|May|June|July|August|September|"
                r"October|November|December)(?:/(?:[A-Z][a-z]+))?\s*(?:<[^>]+>|\s)*"
                r"(\d{1,2})\s*[-–]\s*(\d{1,2})", ym.group(2)):
            month, d1, d2 = fc.MONTHS[mm.group(1)], int(mm.group(2)), int(mm.group(3))
            end_month = month if d2 > d1 else month + 1
            try:
                from datetime import date as _date
                end = _date(year, end_month, d2).isoformat()
            except ValueError:
                continue
            meetings.append({"start": "%04d-%02d-%02d" % (year, month, d1), "end": end})
    upcoming = sorted([m for m in meetings if m["end"] >= d], key=lambda m: m["start"])
    if not upcoming:
        raise base.FetchError("no FOMC meeting after %s parsed" % d)
    return {"next_fomc_date": upcoming[0]["start"], "next_fomc_end": upcoming[0]["end"],
            "upcoming": upcoming[:6], "all_parsed": len(meetings)}, cfg["base_url"]


def bf_econ_calendar(d, cfg, env):
    key = env.get("FRED_API_KEY")
    if not key:
        raise base.FetchError("FRED_API_KEY missing")
    from econ_calendar import RELEASES
    # ALFRED holds no vintage for *scheduled* dates. Release calendars are
    # pre-announced ~a year ahead and immutable, so the current schedule filtered
    # to dates >= d is lookahead-safe (a run on d knew these dates).
    upcoming = []
    for rid, name in RELEASES.items():
        url = ("https://api.stlouisfed.org/fred/release/dates?release_id=%d&api_key=%s"
               "&file_type=json&include_release_dates_with_no_data=true"
               "&realtime_start=%s&sort_order=asc&limit=10" % (rid, key, d))
        try:
            for row in base.http_get_json(url).get("release_dates") or []:
                if row.get("date", "") >= d:
                    upcoming.append({"release": name, "date": row["date"]})
        except base.FetchError:
            continue
        time.sleep(0.3)
    if not upcoming:
        raise base.FetchError("no as-of release calendar at %s" % d)
    upcoming.sort(key=lambda r: r["date"])
    return {"upcoming": upcoming[:15],
            "note": "pre-announced schedule (immutable), filtered to >= %s" % d}, \
        "FRED release/dates (pre-announced, filtered)"


BACKFILLS = ["binance_klines", "feargreed", "defillama", "fx_rates", "fred",
             "etf_flows", "binance_funding", "fed_calendar", "econ_calendar"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--sources", default=",".join(BACKFILLS))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    d = args.date
    cfg = base.load_sources()
    env = base.load_env()
    wanted = [s.strip() for s in args.sources.split(",") if s.strip()]
    for sid in wanted:
        scfg = cfg["sources"].get(sid) or {}
        try:
            if sid == "binance_klines":
                data, url = bf_binance_klines(d, scfg)
            elif sid == "feargreed":
                data, url = bf_feargreed(d, scfg)
            elif sid == "defillama":
                data, url = bf_defillama(d, scfg)
            elif sid == "fx_rates":
                data, url = bf_fx_rates(d, scfg)
            elif sid == "fred":
                data, url = bf_fred(d, scfg, env)
            elif sid == "etf_flows":
                data, url = bf_etf_flows(d, scfg)
            elif sid == "binance_funding":
                data, url = bf_binance_funding(d, scfg)
            elif sid == "fed_calendar":
                data, url = bf_fed_calendar(d, scfg)
            elif sid == "econ_calendar":
                data, url = bf_econ_calendar(d, scfg, env)
            else:
                print("%-16s SKIP (no backfill implemented)" % sid)
                continue
            data["backfill"] = True
            path, wrote = base.write_cache(sid, d, data, url=url, force=args.force)
            print("%-16s ok       %s%s" % (sid, path, "" if wrote else " (existing kept)"))
        except base.FetchError as e:
            print("%-16s FAIL     %s" % (sid, str(e)[:110]))
        except Exception as e:
            print("%-16s CRASH    %s: %s" % (sid, type(e).__name__, str(e)[:110]))


if __name__ == "__main__":
    main()

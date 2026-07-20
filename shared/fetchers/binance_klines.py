#!/usr/bin/env python3
"""Binance klines + computed indicators — the TA backbone of the weekly report.

Emits everything crypto-analyst narrates (three-plane rule: ALL math here):
MA 50/100/150/200 daily + 200 weekly, Bollinger(20,2), RSI(14) daily+weekly with
their own SMA(14), anchored VWAP from the cycle low, volume-profile POC/shelves.

Indicators use CLOSED candles only — the running daily/weekly candle is excluded
(a Sunday-evening run must not compute a 200d MA on a half-day candle); the live
(incomplete) close is emitted separately as *_price_live.
"""
import base
import indicators as ind

MIRRORS = [
    "https://api.binance.com/api/v3",
    "https://data-api.binance.vision/api/v3",
]


def _klines(symbol, interval, limit, end_time=None):
    last_err = None
    for root in MIRRORS:
        url = "%s/klines?symbol=%s&interval=%s&limit=%d" % (root, symbol, interval, limit)
        if end_time is not None:
            url += "&endTime=%d" % end_time
        try:
            raw = base.http_get_json(url)
            if isinstance(raw, list) and raw:
                return raw, url
        except base.FetchError as e:
            last_err = e
    raise base.FetchError("all Binance mirrors failed for %s %s: %s"
                          % (symbol, interval, last_err))


def _klines_paged(symbol, interval, pages=2):
    """Up to pages*1000 candles (oldest→newest). Two daily pages ≈ 5.5 years —
    enough for the cycle-low VWAP anchor to find the true 2022 trough instead of
    a sliding window edge."""
    raw, url = _klines(symbol, interval, 1000)
    for _ in range(pages - 1):
        older, _ = _klines(symbol, interval, 1000, end_time=int(raw[0][0]) - 1)
        if not older or older[-1][0] >= raw[0][0]:
            break
        raw = older + raw
    return raw, url


def _cols(raw):
    """kline row: [openTime, open, high, low, close, volume, closeTime, ...]"""
    highs = [float(r[2]) for r in raw]
    lows = [float(r[3]) for r in raw]
    closes = [float(r[4]) for r in raw]
    vols = [float(r[5]) for r in raw]
    return highs, lows, closes, vols


def _daily_block(symbol):
    raw, url = _klines_paged(symbol, "1d", pages=2)
    live_close = float(raw[-1][4])
    raw = raw[:-1]  # drop the running (incomplete) candle
    highs, lows, closes, vols = _cols(raw)
    rsi = ind.rsi_wilder_series(closes)
    rsi_clean = [r for r in rsi if r is not None]
    boll_mid, boll_up, boll_lo = ind.bollinger(closes)
    anchor = ind.cycle_low_index(lows, lookback=len(lows))
    poc, shelves = ind.volume_profile_poc(closes, vols)
    block = {
        "close": closes[-1],
        "price_live": live_close,
        "prev_close": closes[-2],
        "week_high": max(highs[-7:]),
        "week_low": min(lows[-7:]),
        "ma50d": ind.sma(closes, 50),
        "ma100d": ind.sma(closes, 100),
        "ma150d": ind.sma(closes, 150),
        "ma200d": ind.sma(closes, 200),
        "boll_mid": boll_mid, "boll_upper": boll_up, "boll_lower": boll_lo,
        "rsi14d": rsi[-1],
        "rsi14d_ma14": ind.sma(rsi_clean, 14),
        "vwap_cycle_low": ind.anchored_vwap(highs, lows, closes, vols, anchor),
        "vwap_anchor_date": raw[anchor][0],
        "poc_180d": poc,
        "volume_shelves_180d": shelves,
    }
    return block, url


def _weekly_block(symbol):
    raw, _ = _klines(symbol, "1w", 520)
    raw = raw[:-1]  # drop the running week
    _, _, closes, _ = _cols(raw)
    rsi = ind.rsi_wilder_series(closes)
    rsi_clean = [r for r in rsi if r is not None]
    return {
        "close_w": closes[-1],
        "ma200w": ind.sma(closes, 200),
        "ma100w": ind.sma(closes, 100),
        "rsi14w": rsi[-1],
        "rsi14w_ma14": ind.sma(rsi_clean, 14),
    }


def fetch(cfg, env):
    btc_d, url = _daily_block("BTCUSDT")
    btc_w = _weekly_block("BTCUSDT")
    eth_d, _ = _daily_block("ETHUSDT")
    eth_w = _weekly_block("ETHUSDT")

    def r2(x):
        return round(x, 2) if isinstance(x, float) else x

    data = {}
    for prefix, block in (("btc", btc_d), ("btc", btc_w), ("eth", eth_d), ("eth", eth_w)):
        for key, val in block.items():
            data["%s_%s" % (prefix, key)] = r2(val)
    # convert VWAP anchor open-time (ms) to a date string
    for coin in ("btc", "eth"):
        ms = data.get(coin + "_vwap_anchor_date")
        if isinstance(ms, (int, float)):
            from datetime import datetime, timezone
            data[coin + "_vwap_anchor_date"] = datetime.fromtimestamp(
                ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    return data, url

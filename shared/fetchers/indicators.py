#!/usr/bin/env python3
"""Pure indicator math for the data plane. Stdlib only, no side effects.

Every function takes plain lists of floats and returns floats/lists. This module
is the single place TA arithmetic happens (three-plane rule: the reasoning plane
narrates these numbers, never computes them). Tested by test_indicators.py.
"""


def sma(values, period):
    """Simple moving average of the LAST `period` values; None if not enough data."""
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def sma_series(values, period):
    """SMA at each index (None until warm); same length as input."""
    out = [None] * len(values)
    running = 0.0
    for i, v in enumerate(values):
        running += v
        if i >= period:
            running -= values[i - period]
        if i >= period - 1:
            out[i] = running / period
    return out


def rsi_wilder_series(closes, period=14):
    """Wilder-smoothed RSI series; None until warm. Matches TradingView RSI."""
    n = len(closes)
    out = [None] * n
    if n <= period:
        return out
    gains, losses = 0.0, 0.0
    for i in range(1, period + 1):
        delta = closes[i] - closes[i - 1]
        if delta >= 0:
            gains += delta
        else:
            losses -= delta
    avg_gain, avg_loss = gains / period, losses / period
    out[period] = _rsi_from(avg_gain, avg_loss)
    for i in range(period + 1, n):
        delta = closes[i] - closes[i - 1]
        gain = delta if delta > 0 else 0.0
        loss = -delta if delta < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        out[i] = _rsi_from(avg_gain, avg_loss)
    return out


def _rsi_from(avg_gain, avg_loss):
    if avg_loss == 0:
        return 100.0
    return 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)


def bollinger(closes, period=20, mult=2.0):
    """(mid, upper, lower) on the last `period` closes; population stddev."""
    if len(closes) < period:
        return None, None, None
    window = closes[-period:]
    mid = sum(window) / period
    var = sum((c - mid) ** 2 for c in window) / period
    sd = var ** 0.5
    return mid, mid + mult * sd, mid - mult * sd


def anchored_vwap(highs, lows, closes, volumes, anchor_idx):
    """Volume-weighted average of typical price from anchor_idx to the end."""
    num, den = 0.0, 0.0
    for i in range(anchor_idx, len(closes)):
        typical = (highs[i] + lows[i] + closes[i]) / 3.0
        num += typical * volumes[i]
        den += volumes[i]
    return num / den if den else None


def volume_profile_poc(closes, volumes, lookback=180, bins=50):
    """Point of control + top shelves over the last `lookback` candles.

    Buckets close prices into `bins` equal bands, sums volume per band, returns
    (poc_price, [(price, volume_share), ...top3]) with band-center prices."""
    closes, volumes = closes[-lookback:], volumes[-lookback:]
    if not closes:
        return None, []
    lo, hi = min(closes), max(closes)
    if hi <= lo:
        return closes[-1], []
    width = (hi - lo) / bins
    buckets = [0.0] * bins
    for c, v in zip(closes, volumes):
        idx = min(int((c - lo) / width), bins - 1)
        buckets[idx] += v
    total = sum(buckets) or 1.0
    ranked = sorted(range(bins), key=lambda i: buckets[i], reverse=True)
    centers = [lo + width * (i + 0.5) for i in range(bins)]
    top = [(round(centers[i], 2), round(buckets[i] / total, 4)) for i in ranked[:3]]
    return top[0][0], top


def cycle_low_index(lows, lookback=1000):
    """Index of the lowest low in the last `lookback` candles (VWAP anchor)."""
    window = lows[-lookback:]
    offset = len(lows) - len(window)
    return offset + min(range(len(window)), key=lambda i: window[i])

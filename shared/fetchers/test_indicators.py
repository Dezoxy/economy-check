#!/usr/bin/env python3
"""Sanity tests for indicators.py — run: python3 shared/fetchers/test_indicators.py
The reasoning plane narrates these numbers blindly; this file is the proof they
are right. Keep it green before every step-D/E change."""
import sys

import indicators as ind


def approx(a, b, tol=1e-6):
    assert a is not None and abs(a - b) < tol, "expected %s got %s" % (b, a)


def main():
    # SMA: arithmetic series 1..10, SMA5 of last 5 = (6+7+8+9+10)/5 = 8
    approx(ind.sma(list(map(float, range(1, 11))), 5), 8.0)
    assert ind.sma([1.0, 2.0], 5) is None

    # SMA series alignment: index period-1 is the first defined value
    s = ind.sma_series([2.0, 4.0, 6.0, 8.0], 2)
    assert s[0] is None
    approx(s[1], 3.0)
    approx(s[3], 7.0)

    # RSI: monotonic rise -> 100; monotonic fall -> 0; flat after warmup stays put
    up = list(map(float, range(1, 40)))
    approx(ind.rsi_wilder_series(up)[-1], 100.0)
    down = list(map(float, range(40, 1, -1)))
    approx(ind.rsi_wilder_series(down)[-1], 0.0)
    # alternating +1/-1 deltas -> RSI ~50
    alt = [100.0 + (i % 2) for i in range(200)]
    rsi = ind.rsi_wilder_series(alt)[-1]
    assert 45.0 < rsi < 55.0, rsi

    # Bollinger: constant series -> bands collapse onto mid
    mid, upb, lob = ind.bollinger([5.0] * 25)
    approx(mid, 5.0); approx(upb, 5.0); approx(lob, 5.0)
    # known case: [1..20], mid=10.5, population sd of 1..20 = 5.766281
    mid, upb, lob = ind.bollinger(list(map(float, range(1, 21))))
    approx(mid, 10.5)
    approx(upb - mid, 2 * 5.766281297335398, 1e-9)

    # anchored VWAP: equal volumes -> mean of typical prices from anchor
    h, l, c, v = [10.0, 20.0], [8.0, 16.0], [9.0, 18.0], [1.0, 1.0]
    approx(ind.anchored_vwap(h, l, c, v, 0), ((10 + 8 + 9) / 3 + (20 + 16 + 18) / 3) / 2)
    # volume weighting: all volume on candle 2 -> VWAP = candle 2 typical
    approx(ind.anchored_vwap(h, l, c, [0.0, 5.0], 0), (20 + 16 + 18) / 3)

    # POC: volume concentrated at one price level wins
    closes = [10.0] * 50 + [20.0] * 5
    vols = [100.0] * 50 + [1.0] * 5
    poc, shelves = ind.volume_profile_poc(closes, vols, lookback=55, bins=10)
    assert abs(poc - 10.0) < 1.0, poc
    assert shelves[0][1] > 0.9  # >90% of volume in the winning shelf

    # cycle low: index of the minimum low
    lows = [5.0, 3.0, 4.0, 1.0, 2.0]
    assert ind.cycle_low_index(lows) == 3
    assert ind.cycle_low_index(lows, lookback=1) == 4

    print("indicators: ALL TESTS PASS")


if __name__ == "__main__":
    sys.exit(main())

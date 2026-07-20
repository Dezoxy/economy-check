#!/usr/bin/env python3
"""Binance futures: funding rates + open interest for BTC/ETH (leverage regime)."""
import base


def fetch(cfg, env):
    root = cfg["base_url"]
    data = {}
    for sym, prefix in (("BTCUSDT", "btc"), ("ETHUSDT", "eth")):
        prem = base.http_get_json("%s/fapi/v1/premiumIndex?symbol=%s" % (root, sym))
        oi = base.http_get_json("%s/fapi/v1/openInterest?symbol=%s" % (root, sym))
        mark = float(prem["markPrice"])
        oi_coins = float(oi["openInterest"])
        # last 7 funding settlements (8h each) for the weekly read
        hist = base.http_get_json(
            "%s/fapi/v1/fundingRate?symbol=%s&limit=21" % (root, sym))
        rates = [float(h["fundingRate"]) for h in hist]
        data.update({
            prefix + "_funding_pct": round(float(prem["lastFundingRate"]) * 100, 4),
            prefix + "_funding_week_avg_pct": round(sum(rates[-21:]) / max(1, len(rates)) * 100, 4),
            prefix + "_mark_price": round(mark, 2),
            prefix + "_oi_coins": round(oi_coins, 1),
            prefix + "_oi_usd": round(oi_coins * mark, 0),
        })
    return data, root + "/fapi/v1/{premiumIndex,openInterest,fundingRate}"

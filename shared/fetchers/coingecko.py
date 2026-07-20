#!/usr/bin/env python3
"""CoinGecko fetcher — reference implementation for the framework (step D pattern).

Emits exactly what downstream prose needs, pre-computed: the reasoning plane never
does arithmetic, so TOTAL3 (alt breadth) is derived HERE, in deterministic code.
"""
import time

import base


def fetch(cfg, env):
    headers = {}
    key = env.get(cfg.get("auth") or "")
    if key:
        headers["x-cg-demo-api-key"] = key
    burl = cfg["base_url"]

    prices = base.http_get_json(
        burl + "/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
               "&include_market_cap=true&include_24hr_change=true", headers=headers)
    time.sleep(2)  # free tier is ~10 req/min; be a polite client
    glob = base.http_get_json(burl + "/global", headers=headers)

    g = glob["data"]
    total = g["total_market_cap"]["usd"]
    btc_mcap = prices["bitcoin"].get("usd_market_cap")
    eth_mcap = prices["ethereum"].get("usd_market_cap")
    total3 = total - (btc_mcap or 0) - (eth_mcap or 0) if btc_mcap and eth_mcap else None

    data = {
        "btc_usd": prices["bitcoin"]["usd"],
        "eth_usd": prices["ethereum"]["usd"],
        "btc_24h_change_pct": prices["bitcoin"].get("usd_24h_change"),
        "eth_24h_change_pct": prices["ethereum"].get("usd_24h_change"),
        "btc_mcap_usd": btc_mcap,
        "eth_mcap_usd": eth_mcap,
        "total_mcap_usd": total,
        "total3_usd": total3,
        "btc_dominance_pct": g["market_cap_percentage"].get("btc"),
        "eth_dominance_pct": g["market_cap_percentage"].get("eth"),
        "mcap_24h_change_pct": g.get("market_cap_change_percentage_24h_usd"),
    }
    return data, burl + "/simple/price + /global"

#!/usr/bin/env python3
"""DefiLlama: total TVL + stablecoin supply with w/w deltas (fiat-flow signal)."""
import base


def fetch(cfg, env):
    chains = base.http_get_json("https://api.llama.fi/v2/chains")
    tvl_total = sum(c.get("tvl") or 0 for c in chains)
    top_chains = sorted(chains, key=lambda c: c.get("tvl") or 0, reverse=True)[:8]

    st = base.http_get_json("https://stablecoins.llama.fi/stablecoins?includePrices=true")
    assets = st.get("peggedAssets") or []

    def circ(a, key="circulating"):
        v = a.get(key) or {}
        return float(v.get("peggedUSD") or 0)

    total_now = sum(circ(a) for a in assets)
    total_week = sum(circ(a, "circulatingPrevWeek") for a in assets)
    by_symbol = {a.get("symbol"): a for a in assets}
    usdt, usdc = by_symbol.get("USDT"), by_symbol.get("USDC")
    if usdt is None or usdc is None:
        raise base.FetchError("USDT/USDC missing from stablecoins response")

    data = {
        "tvl_total_usd": round(tvl_total, 0),
        "tvl_top_chains": [{"name": c["name"], "tvl_usd": round(c["tvl"], 0)}
                           for c in top_chains],
        "stablecoin_total_musd": round(total_now / 1e6, 1),
        "stablecoin_week_delta_musd": round((total_now - total_week) / 1e6, 1),
        "usdt_mcap_musd": round(circ(usdt) / 1e6, 1),
        "usdt_week_delta_musd": round((circ(usdt) - circ(usdt, "circulatingPrevWeek")) / 1e6, 1),
        "usdc_mcap_musd": round(circ(usdc) / 1e6, 1),
        "usdc_week_delta_musd": round((circ(usdc) - circ(usdc, "circulatingPrevWeek")) / 1e6, 1),
    }
    return data, "api.llama.fi/v2/chains + stablecoins.llama.fi/stablecoins"

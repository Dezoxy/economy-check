#!/usr/bin/env python3
"""CoinPaprika — keyless fallback for coingecko (spot prices + mcaps only)."""
import base


def fetch(cfg, env):
    root = cfg["base_url"]
    btc = base.http_get_json(root + "/tickers/btc-bitcoin")
    eth = base.http_get_json(root + "/tickers/eth-ethereum")
    q_btc, q_eth = btc["quotes"]["USD"], eth["quotes"]["USD"]
    data = {
        "btc_usd": q_btc["price"],
        "eth_usd": q_eth["price"],
        "btc_mcap_usd": q_btc.get("market_cap"),
        "eth_mcap_usd": q_eth.get("market_cap"),
        "btc_24h_change_pct": q_btc.get("percent_change_24h"),
        "eth_24h_change_pct": q_eth.get("percent_change_24h"),
        # coingecko-schema keys this source CANNOT provide are absent on purpose:
        # fallback duty fails coingecko's schema check -> correct hard failure.
    }
    return data, root + "/tickers"

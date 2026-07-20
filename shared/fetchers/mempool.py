#!/usr/bin/env python3
"""mempool.space: BTC network health — fees, hashrate, difficulty."""
import base


def fetch(cfg, env):
    root = cfg["base_url"]
    fees = base.http_get_json(root + "/v1/fees/recommended")
    hashrate = base.http_get_json(root + "/v1/mining/hashrate/1m")
    diff = base.http_get_json(root + "/v1/difficulty-adjustment")
    cur = float(hashrate.get("currentHashrate") or 0)
    data = {
        "fee_fast_satvb": fees.get("fastestFee"),
        "fee_medium_satvb": fees.get("halfHourFee"),
        "hashrate_ehs": round(cur / 1e18, 1),
        "difficulty_change_pct": round(float(diff.get("difficultyChange") or 0), 2),
        "blocks_to_retarget": diff.get("remainingBlocks"),
    }
    if not data["hashrate_ehs"]:
        raise base.FetchError("mempool hashrate empty")
    return data, root + "/v1/{fees,mining/hashrate,difficulty-adjustment}"

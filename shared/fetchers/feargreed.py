#!/usr/bin/env python3
"""alternative.me Fear & Greed index — now, a week ago, and a short history."""
import base


def fetch(cfg, env):
    url = cfg["base_url"] + "/fng/?limit=30"
    out = base.http_get_json(url)
    rows = out.get("data") or []
    if not rows:
        raise base.FetchError("empty fng response")
    now = rows[0]
    week_ago = rows[7] if len(rows) > 7 else rows[-1]
    data = {
        "value": int(now["value"]),
        "classification": now["value_classification"],
        "week_ago_value": int(week_ago["value"]),
        "week_ago_classification": week_ago["value_classification"],
        "month_min": min(int(r["value"]) for r in rows),
        "month_max": max(int(r["value"]) for r in rows),
        "history_30d": [int(r["value"]) for r in rows],
    }
    return data, url

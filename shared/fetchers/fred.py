#!/usr/bin/env python3
"""FRED macro series: latest + prior + revision context for the MAKRÓ section.
Requires FRED_API_KEY in .env (free key: https://fred.stlouisfed.org)."""
import base

SERIES = {
    "cpi_yoy": ("CPIAUCSL", "pc1"),        # CPI, % change from year ago
    "core_cpi_yoy": ("CPILFESL", "pc1"),
    "pce_yoy": ("PCEPI", "pc1"),
    "core_pce_yoy": ("PCEPILFE", "pc1"),
    "unemployment_pct": ("UNRATE", "lin"),
    "payrolls_k": ("PAYEMS", "chg"),       # monthly change, thousands
    "ust2y_pct": ("DGS2", "lin"),
    "ust10y_pct": ("DGS10", "lin"),
    "dxy_broad": ("DTWEXBGS", "lin"),
    "fedfunds_pct": ("DFEDTARU", "lin"),   # target range upper bound
}


def fetch(cfg, env):
    key = env.get(cfg.get("auth") or "FRED_API_KEY")
    if not key:
        raise base.FetchError("FRED_API_KEY missing from .env (free key at "
                              "https://fred.stlouisfed.org — required source)")
    root = cfg["base_url"]
    series = {}
    for name, (sid, units) in SERIES.items():
        url = ("%s/series/observations?series_id=%s&api_key=%s&file_type=json"
               "&sort_order=desc&limit=8&units=%s" % (root, sid, key, units))
        out = base.http_get_json(url)
        obs = [o for o in out.get("observations") or [] if o.get("value") not in (".", None)]
        if not obs:
            series[name] = None
            continue
        series[name] = {
            "value": float(obs[0]["value"]),
            "date": obs[0]["date"],
            "prior": float(obs[1]["value"]) if len(obs) > 1 else None,
            "prior_date": obs[1]["date"] if len(obs) > 1 else None,
        }
    if all(v is None for v in series.values()):
        raise base.FetchError("FRED returned no observations (bad key?)")
    return {"series": series}, root + "/series/observations"

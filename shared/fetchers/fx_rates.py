#!/usr/bin/env python3
"""ECB reference FX rates via frankfurter (no key). Basis for the one permitted
derived figure in prose: approximate HUF conversions tagged [src:fx_rates/date]."""
import base


def fetch(cfg, env):
    usd = base.http_get_json(cfg["base_url"] + "/latest?base=USD&symbols=HUF,EUR")
    eur = base.http_get_json(cfg["base_url"] + "/latest?base=EUR&symbols=HUF")
    data = {
        "usd_huf": round(float(usd["rates"]["HUF"]), 2),
        "usd_eur": round(float(usd["rates"]["EUR"]), 4),
        "eur_huf": round(float(eur["rates"]["HUF"]), 2),
        "rate_date": usd["date"],  # ECB fix date — weekend runs carry Friday's
    }
    return data, cfg["base_url"] + "/latest"

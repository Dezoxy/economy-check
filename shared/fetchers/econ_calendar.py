#!/usr/bin/env python3
"""Upcoming macro release dates via the FRED releases API (bls.gov blocks bots;
FRED mirrors the schedule authoritatively). Uses the same FRED_API_KEY."""
from datetime import date

import base

# FRED release ids: name shown in reports
RELEASES = {
    10: "Consumer Price Index (CPI)",
    50: "Employment Situation (NFP)",
    46: "Producer Price Index (PPI)",
    53: "Gross Domestic Product (GDP)",
    54: "Personal Income and Outlays (PCE)",
}


def fetch(cfg, env):
    key = env.get("FRED_API_KEY")
    if not key:
        raise base.FetchError("FRED_API_KEY missing from .env (econ_calendar uses "
                              "the FRED releases API; bls.gov blocks unattended fetches)")
    today = date.today().isoformat()
    upcoming = []
    for rid, name in RELEASES.items():
        url = ("https://api.stlouisfed.org/fred/release/dates?release_id=%d"
               "&api_key=%s&file_type=json&include_release_dates_with_no_data=true"
               "&realtime_start=%s&sort_order=asc&limit=3" % (rid, key, today))
        out = base.http_get_json(url)
        for d in out.get("release_dates") or []:
            if d.get("date", "") >= today:
                upcoming.append({"release": name, "date": d["date"]})
    if not upcoming:
        raise base.FetchError("FRED release calendar returned nothing upcoming")
    upcoming.sort(key=lambda r: r["date"])
    return {"upcoming": upcoming[:15]}, "api.stlouisfed.org/fred/release/dates"

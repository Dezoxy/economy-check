#!/usr/bin/env python3
"""Federal Reserve FOMC meeting calendar scrape → upcoming meeting dates."""
import re
from datetime import date

import base

MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}


def fetch(cfg, env):
    url = cfg["base_url"]
    html = base.http_get(url)
    meetings = []
    # year sections: "2026 FOMC Meetings" followed by month/day panels like
    # "January</strong> 27-28" or "April/May</strong> 28-29" (HTML tags between)
    for ym in re.finditer(r"(20\d\d) FOMC Meetings(.*?)(?=20\d\d FOMC Meetings|$)",
                          html, re.S):
        year = int(ym.group(1))
        for mm in re.finditer(
                r"(January|February|March|April|May|June|July|August|September|"
                r"October|November|December)(?:/(?:[A-Z][a-z]+))?\s*(?:<[^>]+>|\s)*"
                r"(\d{1,2})\s*[-–]\s*(\d{1,2})", ym.group(2)):
            month, d1, d2 = MONTHS[mm.group(1)], int(mm.group(2)), int(mm.group(3))
            end_month = month if d2 > d1 else month + 1  # Apr 28 – May 1 style wrap
            try:
                end = date(year, end_month, d2)
            except ValueError:
                continue
            meetings.append({"start": "%04d-%02d-%02d" % (year, month, d1),
                             "end": end.isoformat()})
    if not meetings:
        raise base.FetchError("FOMC calendar layout changed — no meetings parsed")
    meetings.sort(key=lambda m: m["start"])
    today = date.today().isoformat()
    upcoming = [m for m in meetings if m["end"] >= today]
    if not upcoming:
        raise base.FetchError("no upcoming FOMC meeting found (calendar stale?)")
    return {"next_fomc_date": upcoming[0]["start"],
            "next_fomc_end": upcoming[0]["end"],
            "upcoming": upcoming[:6],
            "all_parsed": len(meetings)}, url

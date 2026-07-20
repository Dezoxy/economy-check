#!/usr/bin/env python3
"""Atlanta Fed GDPNow. The tool page renders the number via JS, but the official
RSS feed carries it in the entry title:
  'GDPNow estimate for real GDP growth (SAAR) in Q3 2026 is 2.4 percent on July 17'
"""
import re

import base

RSS_URL = "https://www.atlantafed.org/rss/GDPNow"


def fetch(cfg, env):
    xml_text = base.http_get(RSS_URL, headers={"Accept": "application/rss+xml"})
    # newest item first; the estimate sits in <description>:
    # "...estimate for real GDP growth (...) in the second quarter of 2026 is
    #  1.2 percent on July 1, down from 2.5 percent on June 25. ..."
    for m in re.finditer(r"<description>(.*?)</description>", xml_text, re.S):
        desc = m.group(1)
        val = re.search(
            r"in the (\w+ quarter of 20\d\d) is (-?\d+(?:\.\d+)?)\s*percent"
            r"\s*on\s+([A-Z][a-z]+ \d{1,2})", desc)
        if not val:
            continue
        prev = re.search(r"(?:up|down) from (-?\d+(?:\.\d+)?)\s*percent"
                         r"\s*on\s+([A-Z][a-z]+ \d{1,2})", desc)
        data = {
            "estimate_pct": float(val.group(2)),
            "quarter": val.group(1),
            "as_of_date": val.group(3),
            "prev_estimate_pct": float(prev.group(1)) if prev else None,
            "prev_date": prev.group(2) if prev else None,
            "component_note": re.sub(r"\s+", " ", desc)[:400],
        }
        return data, RSS_URL
    raise base.FetchError("GDPNow RSS carried no parseable estimate "
                          "(feed layout changed?)")

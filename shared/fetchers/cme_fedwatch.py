#!/usr/bin/env python3
"""CME FedWatch — best-effort. The tool page is JS-rendered; the underlying API
sits behind bot protection, so an unattended scrape usually fails. Policy
(sources.yaml): on failure the REPORT cites FedWatch odds via a dated news
source and marks them relayed — never invented."""
import re

import base


def fetch(cfg, env):
    html = base.http_get(cfg["base_url"], timeout=20)
    # If the page ever server-renders the headline probability, catch it.
    m = re.search(r"(\d{1,3}(?:\.\d)?)\s?%\s*(?:probability|chance)", html, re.I)
    if m:
        return {"next_meeting_odds": {"headline_pct": float(m.group(1)),
                                      "note": "server-rendered headline only"}}, \
            cfg["base_url"]
    raise base.FetchError(
        "FedWatch page is JS-rendered (expected). Report policy: cite the odds "
        "via a dated news source ('a CME FedWatch szerint, Reuters nyomán'), "
        "tag the news domain, mark relayed.")

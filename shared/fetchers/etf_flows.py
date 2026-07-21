#!/usr/bin/env python3
"""Farside US spot ETF flow tables (BTC + ETH). T+1 data by nature — the report
must state the flow date. HTML table scrape; fallback source is sosovalue."""
import re

import base


def _parse_table(html, label, keep_all=False):
    """Farside daily-flow tables: rows '<td>12 Jul 2026</td> ... <td>Total</td>'.
    We take date + the LAST numeric cell of each row (the Total column).
    keep_all=True returns every parsed row (backfill slices by as-of date)."""
    text = html.replace("&minus;", "-").replace("−", "-")
    rows = []
    for tr in re.finditer(r"<tr[^>]*>(.*?)</tr>", text, re.S | re.I):
        cells = [re.sub(r"<[^>]+>", "", c).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr.group(1),
                                     re.S | re.I)]
        if len(cells) < 3:
            continue
        m = re.match(r"(\d{1,2}) ([A-Z][a-z]{2}) (20\d\d)$", cells[0])
        if not m:
            continue
        # last cell that parses as a number = Total (M USD)
        total = None
        for c in reversed(cells[1:]):
            v = c.replace(",", "").replace("(", "-").replace(")", "")
            try:
                total = float(v)
                break
            except ValueError:
                continue
        if total is None:
            continue
        months = {m_: i + 1 for i, m_ in enumerate(
            ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
             "Oct", "Nov", "Dec"])}
        iso = "%s-%02d-%02d" % (m.group(3), months[m.group(2)], int(m.group(1)))
        rows.append({"date": iso, "total_musd": total})
    if not rows:
        raise base.FetchError("farside %s table layout changed — no rows parsed"
                              % label)
    rows.sort(key=lambda r: r["date"])
    return rows if keep_all else rows[-10:]


def fetch(cfg, env):
    from datetime import date
    root = cfg["base_url"]

    def settled(rows):
        # today's row shows 0.0 until T+1 data lands — a placeholder, not a flow
        if rows and rows[-1]["total_musd"] == 0.0 \
                and rows[-1]["date"] >= date.today().isoformat():
            return rows[:-1]
        return rows

    btc = settled(_parse_table(base.http_get(root + "/btc/"), "btc"))
    data = {
        "btc_daily_flows_musd": btc,
        "btc_week_total_musd": round(sum(r["total_musd"] for r in btc[-5:]), 1),
        "btc_latest_flow_date": btc[-1]["date"],
    }
    try:
        eth = settled(_parse_table(base.http_get(root + "/eth/"), "eth"))
        data["eth_daily_flows_musd"] = eth
        data["eth_week_total_musd"] = round(sum(r["total_musd"] for r in eth[-5:]), 1)
    except base.FetchError:
        data["eth_daily_flows_musd"] = None
        data["eth_note"] = "eth table unavailable this run"
    return data, root + "/btc/ + /eth/"

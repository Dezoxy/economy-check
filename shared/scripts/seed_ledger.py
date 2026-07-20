#!/usr/bin/env python3
"""Seed crypto-analyst/ledger.jsonl from the graded benchmark table in
templates/prediction-ledger.md. Idempotent: rebuilds the benchmark series only,
preserving any non-benchmark lines already in the ledger."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "crypto-analyst", "templates", "prediction-ledger.md")
DST = os.path.join(ROOT, "crypto-analyst", "ledger.jsonl")

YEAR = 2026  # benchmark grading window per prediction-ledger.md (Jan–Jul 2026)

TYPE_MAP = {
    "level": "level-range", "level-range": "level-range",
    "direction": "direction",
    "cond-scenario": "conditional-scenario", "scenario": "conditional-scenario",
    "event": "event-timeline", "event-timeline": "event-timeline",
    "data-reint": "data-reinterpretation",
    "risk-flag": "risk-flag",
    "position": "position",
}
OUTCOME_MAP = {"✅": "hit", "➖": "partial", "❌": "miss", "?": "unresolved"}


def parse_rows(text):
    m = re.search(r"## Seed entries.*?\n(\|.*)", text, re.S)
    if not m:
        raise SystemExit("seed table not found in prediction-ledger.md")
    rows = []
    for line in m.group(1).splitlines():
        if not line.startswith("|") or set(line.strip()) <= {"|", "-", " "}:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 6 or cells[0] in ("date", ""):
            continue
        rows.append(cells)
    return rows


def main():
    text = open(SRC, encoding="utf-8").read()
    rows = parse_rows(text)
    per_date = {}
    out = []
    for date_md, topic, claim, ctype, outcome_sym, evidence in rows:
        mm, dd = date_md.split("-")
        pdate = "%d-%02d-%02d" % (YEAR, int(mm), int(dd))
        per_date[pdate] = per_date.get(pdate, 0) + 1
        ctype_norm = TYPE_MAP.get(ctype.strip().lower())
        outcome = OUTCOME_MAP.get(outcome_sym.strip())
        if ctype_norm is None or outcome is None:
            raise SystemExit("unmapped type/outcome in row: %s" % [date_md, ctype,
                                                                   outcome_sym])
        relayed = "relayed" in claim.lower()
        out.append({
            "call_id": "kv-%s-%02d" % (pdate, per_date[pdate]),
            "series": "benchmark",
            "publish_date": pdate,
            "source_post": None,
            "asset_topic": topic,
            "call_type": ctype_norm,
            "claim_verbatim": None,
            "claim_normalized": claim,
            "levels": None,
            "trigger_condition": None,
            "invalidation_level": None,
            "deadline": None,
            "own_vs_relayed": "relayed" if relayed else "own",
            "stated_confidence": None,
            "position_taken": ctype_norm == "position",
            "resolution_criteria": None,
            "outcome": outcome,
            "outcome_evidence": evidence,
            "graded_on": "2026-07-20",
            # benchmark pattern: hits credited in posts, misses never acknowledged
            "self_review": outcome == "hit",
            "band_definition": None,
        })

    kept = []
    if os.path.exists(DST):
        for line in open(DST, encoding="utf-8"):
            if line.strip() and json.loads(line).get("series") != "benchmark":
                kept.append(line.rstrip("\n"))

    with open(DST, "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        for line in kept:
            f.write(line + "\n")

    tally = {}
    for r in out:
        tally[r["outcome"]] = tally.get(r["outcome"], 0) + 1
    print("wrote %d benchmark calls (+%d preserved own calls) -> %s"
          % (len(out), len(kept), os.path.relpath(DST, ROOT)))
    print("outcomes:", json.dumps(tally, ensure_ascii=False))


if __name__ == "__main__":
    main()

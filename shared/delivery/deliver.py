#!/usr/bin/env python3
"""Delivery orchestrator — the ONLY way reports leave the repo.

  python3 shared/delivery/deliver.py --report crypto-analyst/reports/2026/x.md
        [--channels telegram,email] [--dry-run] [--force]
  python3 shared/delivery/deliver.py --alert "fetcher fred failed 2x"   # ops alerts

Defense in depth: delivery independently re-checks the quality gate (sidecar
<report>.score.json with total >= threshold) — a report that dodged the Stop hook
still cannot ship. --force overrides with a loud [GATE OVERRIDE] tag in the caption.
"""
import argparse
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_HERE, "..", "fetchers"))
sys.path.insert(0, os.path.join(_ROOT, ".claude", "hooks"))
import base  # noqa: E402
import telegram  # noqa: E402  (sibling module; _HERE is on sys.path as script dir)
import emailer  # noqa: E402
from quality_gate import check_score_sidecar  # noqa: E402  single gate definition


def gate_check(report_path):
    """Returns (ok, message). Delegates to the SAME check the Stop hook runs
    (total >= 80, no category < 60% of weight, arithmetic recomputed) — delivery
    must never be weaker than the gate it backstops."""
    problems = check_score_sidecar(report_path)
    if problems:
        return False, "; ".join(problems)
    sidecar = re.sub(r"\.md$", "", report_path) + ".score.json"
    with open(sidecar, encoding="utf-8") as f:
        total = json.load(f)["total"]
    return True, "score %s/100" % total


def report_title(report_path):
    with open(report_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                return line[2:].strip()
    return os.path.basename(report_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report")
    ap.add_argument("--alert")
    ap.add_argument("--channels", default="telegram,email")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    env = base.load_env()
    channels = [c.strip() for c in args.channels.split(",") if c.strip()]

    if args.alert:
        text = "⚠️ economy-check alert: %s" % args.alert
        if args.dry_run:
            print("[dry-run] telegram alert: %s" % text)
            return
        telegram.send_message(env, text)
        print("alert sent")
        return

    if not args.report:
        ap.print_help()
        sys.exit(2)
    path = os.path.abspath(args.report)
    if not os.path.exists(path):
        print("no such report: %s" % path, file=sys.stderr)
        sys.exit(2)

    ok, msg = gate_check(path)
    caption = report_title(path)
    if not ok:
        if not args.force:
            print("REFUSED: quality gate not passed — %s" % msg, file=sys.stderr)
            print("(use --force to override; the override is tagged in the caption)",
                  file=sys.stderr)
            sys.exit(1)
        caption = "[GATE OVERRIDE: %s] %s" % (msg, caption)

    if args.dry_run:
        print("[dry-run] would deliver %s via %s — %s" %
              (os.path.basename(path), "+".join(channels), msg))
        return

    failures = []
    if "telegram" in channels:
        try:
            telegram.send_document(env, path, caption=caption)
            print("telegram: delivered")
        except Exception as e:
            failures.append("telegram: %s" % e)
    if "email" in channels:
        try:
            with open(path, encoding="utf-8") as f:
                body = f.read()
            emailer.send_report(env, caption, body, attachments=[path])
            print("email: delivered")
        except Exception as e:
            failures.append("email: %s" % e)

    if failures:
        print("delivery failures: " + "; ".join(failures), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

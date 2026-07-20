#!/usr/bin/env python3
"""Fetcher runner CLI — the data plane's entry point.

  python3 shared/fetchers/run.py --source coingecko [--date YYYY-MM-DD] [--force]
  python3 shared/fetchers/run.py --manifest weekly-market-update [--date D] [--force]
  python3 shared/fetchers/run.py --verify weekly-market-update [--date D]
  python3 shared/fetchers/run.py --health [--date D]
  python3 shared/fetchers/run.py --check          # registry sanity (parse + modules)

Exit codes: 0 ok · 1 required source failed/stale (verify/manifest) · 2 usage/config error.

A fetcher module is shared/fetchers/<source_id>.py exposing fetch(cfg, env) -> (data, url).
Missing module => status "not_implemented" (fine during step C; step D fills them in).
"""
import argparse
import importlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base  # noqa: E402


def run_source(source_id, cfg, env, date, force=False, serve_as=None):
    """Fetch via <source_id>'s module. When serve_as is set (fallback duty), the
    data is schema-checked against SERVE_AS's contract and cached under SERVE_AS's
    id — a fallback that can't provide what the requested source promises is a
    failure, not a silent substitution."""
    target = serve_as or source_id
    src = cfg["sources"].get(source_id)
    target_cfg = cfg["sources"].get(target)
    if src is None or target_cfg is None:
        return {"source": target, "status": "unknown_source"}
    t0 = time.time()
    result = {"source": target, "date": date}
    if serve_as:
        result["served_by"] = source_id
    # Retry-friendly: a valid, fresh same-day cache short-circuits the network hit
    # (an evening re-run must not 429 sources that already succeeded at 18:00).
    if not force:
        cached = base.read_cache(target, date)
        age = base.cache_age_hours(target, date)
        if (cached is not None and age is not None
                and age <= target_cfg.get("freshness_hours", 24)
                and not base.check_schema(target_cfg, cached.get("data") or {})):
            result.update(status="ok", cached=os.path.relpath(
                base.cache_path(target, date), base.ROOT), cache_hit=True,
                ms=int((time.time() - t0) * 1000))
            base.health_append(**result)
            return result
    try:
        mod = importlib.import_module(source_id)
    except ImportError:
        result["status"] = "not_implemented"
        base.health_append(**result)
        return result
    try:
        data, url = mod.fetch(src, env)
        problems = base.check_schema(target_cfg, data)
        if problems:
            result.update(status="schema_fail", problems=problems)
        else:
            path, wrote = base.write_cache(target, date, data, url=url, force=force)
            result.update(status="ok", cached=os.path.relpath(path, base.ROOT),
                          fresh_write=wrote)
    except base.FetchError as e:
        result.update(status="fetch_fail", error=str(e)[:300])
    except Exception as e:  # a broken fetcher must never kill the whole run
        result.update(status="crash", error="%s: %s" % (type(e).__name__, str(e)[:300]))
    result["ms"] = int((time.time() - t0) * 1000)
    base.health_append(**result)
    return result


def run_with_fallbacks(source_id, cfg, env, date, force=False):
    chain = [source_id]
    for fb in (cfg["sources"].get(source_id) or {}).get("fallbacks") or []:
        if fb not in chain:
            chain.append(fb)
    res = {"source": source_id, "status": "unknown_source"}
    for sid in chain:
        res = run_source(sid, cfg, env, date, force=force,
                         serve_as=None if sid == source_id else source_id)
        if res.get("status") == "ok":
            return res
    return res


def verify_manifest(report_type, cfg, date, quiet=False):
    """Cache completeness/freshness check for a report run. Returns (ok, rows)."""
    man = cfg["manifests"].get(report_type)
    if man is None:
        print("unknown manifest: %s" % report_type, file=sys.stderr)
        sys.exit(2)
    ok = True
    rows = []
    for tier in ("required", "degraded_ok"):
        for sid in man.get(tier) or []:
            src = cfg["sources"].get(sid) or {}
            age = base.cache_age_hours(sid, date)
            rec = base.read_cache(sid, date)
            problems = base.check_schema(src, rec["data"]) if rec else ["no cache file"]
            max_age = src.get("freshness_hours", 24)
            stale = age is None or age > max_age
            good = not problems and not stale
            if tier == "required" and not good:
                ok = False
            rows.append({
                "source": sid, "tier": tier, "ok": good,
                "age_h": round(age, 1) if age is not None else None,
                "max_age_h": max_age, "problems": problems,
            })
    if not quiet:
        for r in rows:
            mark = "OK " if r["ok"] else ("MISS" if r["tier"] == "required" else "degr")
            print("%-5s %-16s %-12s age=%s/%sh %s" % (
                mark, r["source"], r["tier"], r["age_h"], r["max_age_h"],
                "; ".join(r["problems"]) if r["problems"] else ""))
        print("verify %s @ %s: %s" % (report_type, date, "PASS" if ok else "FAIL"))
    return ok, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source")
    ap.add_argument("--manifest")
    ap.add_argument("--verify")
    ap.add_argument("--health", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--date", default=base.today())
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cfg = base.load_sources()
    env = base.load_env()

    if args.check:
        n_impl = sum(1 for s in cfg["sources"]
                     if os.path.exists(os.path.join(os.path.dirname(__file__), s + ".py")))
        print("sources.yaml OK: %d sources, %d manifests, %d fetchers implemented"
              % (len(cfg["sources"]), len(cfg["manifests"]), n_impl))
        return

    if args.source:
        res = run_with_fallbacks(args.source, cfg, env, args.date, force=args.force)
        print(json.dumps(res, ensure_ascii=False, indent=1))
        sys.exit(0 if res.get("status") == "ok" else 1)

    if args.manifest:
        man = cfg["manifests"].get(args.manifest)
        if man is None:
            print("unknown manifest: %s" % args.manifest, file=sys.stderr)
            sys.exit(2)
        hard_fail = False
        for tier in ("required", "degraded_ok"):
            for sid in man.get(tier) or []:
                res = run_with_fallbacks(sid, cfg, env, args.date, force=args.force)
                status = res.get("status")
                print("%-16s %-16s %s" % (sid, status,
                      res.get("error", "") or res.get("cached", "")))
                if tier == "required" and status != "ok":
                    hard_fail = True
        sys.exit(1 if hard_fail else 0)

    if args.verify:
        ok, rows = verify_manifest(args.verify, cfg, args.date, quiet=args.json)
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        sys.exit(0 if ok else 1)

    if args.health:
        if not os.path.exists(base.HEALTH_PATH):
            print("no health log yet")
            return
        recs = [json.loads(l) for l in open(base.HEALTH_PATH, encoding="utf-8")]
        recs = [r for r in recs if r.get("date") == args.date] or recs[-20:]
        for r in recs:
            print("%-20s %-16s %-16s %sms %s" % (r.get("ts", ""), r.get("source", ""),
                  r.get("status", ""), r.get("ms", "-"), r.get("error", "")[:80]))
        return

    ap.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()

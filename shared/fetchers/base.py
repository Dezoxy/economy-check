#!/usr/bin/env python3
"""Fetcher framework: source registry, dated immutable cache, schema check, health log.

Design contract (PLAN.md, three-plane architecture):
  - Fetchers are the ONLY component that touches the network for report data.
  - Every pull lands in data/cache/<YYYY-MM-DD>/<source>.json, immutable once written.
  - Cache files self-describe: {"source", "fetched_at", "url", "data": {...}}.
  - The reasoning plane reads cache files and never computes or invents numbers.

Stdlib-only on purpose: must run on a bare macOS/Linux python3 (launchd, cron, Cowork).
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCES_PATH = os.path.join(ROOT, "data", "sources.yaml")
CACHE_ROOT = os.path.join(ROOT, "data", "cache")
HEALTH_PATH = os.path.join(CACHE_ROOT, "health.jsonl")
USER_AGENT = "economy-check/0.1 (personal research pipeline)"


class FetchError(Exception):
    pass


# --------------------------------------------------------------------------
# Strict-subset YAML parser. sources.yaml documents the allowed subset:
# 2-space indents, maps, block/inline lists, scalars, comments. No PyYAML dep.
# --------------------------------------------------------------------------
def _scalar(s):
    if " #" in s:
        s = s.split(" #", 1)[0].rstrip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [] if not inner else [_scalar(x.strip()) for x in inner.split(",")]
    if s in ("null", "~", ""):
        return None
    if s == "true":
        return True
    if s == "false":
        return False
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    for cast in (int, float):
        try:
            return cast(s)
        except ValueError:
            pass
    return s


def parse_simple_yaml(text):
    root = {}
    # stack entries: (indent, container, parent_container, key_in_parent)
    stack = [(-2, root, None, None)]
    for lineno, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw:
            raise ValueError("sources.yaml:%d: tabs not allowed" % lineno)
        indent = len(raw) - len(raw.lstrip(" "))
        content = raw.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        top_indent, container, parent, pkey = stack[-1]
        if content.startswith("- "):
            if isinstance(container, dict):
                if container or parent is None:
                    raise ValueError("sources.yaml:%d: unexpected list item" % lineno)
                container = []
                parent[pkey] = container
                stack[-1] = (top_indent, container, parent, pkey)
            container.append(_scalar(content[2:]))
        else:
            if not isinstance(container, dict):
                raise ValueError("sources.yaml:%d: expected '- item'" % lineno)
            key, sep, rest = content.partition(":")
            if not sep:
                raise ValueError("sources.yaml:%d: expected 'key:'" % lineno)
            key, rest = key.strip(), rest.strip()
            if rest == "":
                child = {}
                container[key] = child
                stack.append((indent, child, container, key))
            else:
                container[key] = _scalar(rest)
    return root


def load_sources():
    with open(SOURCES_PATH, encoding="utf-8") as f:
        cfg = parse_simple_yaml(f.read())
    for section in ("sources", "manifests"):
        if section not in cfg:
            raise FetchError("sources.yaml missing '%s' section" % section)
    return cfg


# --------------------------------------------------------------------------
# .env loading — secrets stay in .env (gitignored), never in code or YAML.
# --------------------------------------------------------------------------
def load_env():
    env = {}
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            key, sep, val = line.partition("=")
            if sep:
                env[key.strip()] = val.strip().strip("\"'")
    merged = dict(os.environ)
    merged.update(env)
    return merged


# --------------------------------------------------------------------------
# HTTP helpers
# --------------------------------------------------------------------------
def http_get(url, headers=None, timeout=30, retries=2):
    hdrs = {"User-Agent": USER_AGENT}
    hdrs.update(headers or {})
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise FetchError("GET %s failed after %d tries: %s" % (url, retries + 1, last_err))


def http_get_json(url, headers=None, timeout=30):
    body = http_get(url, headers=headers, timeout=timeout)
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise FetchError("GET %s returned non-JSON (%s): %.120s" % (url, e, body))


# --------------------------------------------------------------------------
# Cache: immutable dated pulls
# --------------------------------------------------------------------------
def today():
    return datetime.now().strftime("%Y-%m-%d")


def cache_path(source_id, date):
    return os.path.join(CACHE_ROOT, date, source_id + ".json")


def write_cache(source_id, date, data, url="", force=False):
    path = cache_path(source_id, date)
    if os.path.exists(path) and not force:
        return path, False  # immutability: same-day re-run keeps the first pull
    os.makedirs(os.path.dirname(path), exist_ok=True)
    record = {
        "source": source_id,
        "date": date,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "url": url,
        "data": data,
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return path, True


def read_cache(source_id, date):
    path = cache_path(source_id, date)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_schema(source_cfg, data):
    """Required keys present and non-null. Returns list of problems (empty = ok)."""
    problems = []
    required = (source_cfg.get("schema") or {}).get("required") or []
    for key in required:
        if key not in data:
            problems.append("missing required key: %s" % key)
        elif data[key] is None:
            problems.append("required key is null: %s" % key)
    return problems


def cache_age_hours(source_id, date):
    rec = read_cache(source_id, date)
    if rec is None:
        return None
    try:
        fetched = datetime.fromisoformat(rec["fetched_at"])
    except (KeyError, ValueError):
        return None
    return (datetime.now(timezone.utc) - fetched).total_seconds() / 3600.0


def health_append(**fields):
    os.makedirs(CACHE_ROOT, exist_ok=True)
    fields.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    with open(HEALTH_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(fields, ensure_ascii=False) + "\n")

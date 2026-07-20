#!/usr/bin/env python3
"""PreToolUse hook: network egress allowlist for the reasoning plane.

Every domain listed anywhere in data/sources.yaml (plus BUILTIN below) is allowed;
any other host in a WebFetch url or a Bash command's URLs is denied with a reason.
Bash commands with no URL pass through untouched.

Fail-closed: if sources.yaml can't be read and the call carries a URL, deny.
Adding a source domain = editing sources.yaml (one registry, three planes).
"""
import json
import os
import re
import sys

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
SOURCES = os.path.join(ROOT, "data", "sources.yaml")

# Infrastructure the pipeline itself needs, independent of data sources.
BUILTIN = {
    "api.telegram.org",       # delivery
    "localhost", "127.0.0.1",
    "docs.claude.com", "code.claude.com",  # tooling docs during maintenance
    "github.com", "api.github.com", "raw.githubusercontent.com",
}

DOMAIN_RE = re.compile(r"^\s*-?\s*([a-z0-9][a-z0-9.-]*\.[a-z]{2,})\s*,?\s*$")
INLINE_LIST_RE = re.compile(r"domains:\s*\[([^\]]*)\]")
# Capture the FULL authority (userinfo included) — host_allowed() strips userinfo,
# so `https://api.coingecko.com@evil.com/` is judged by evil.com, not the decoy.
URL_RE = re.compile(r"https?://([^/\s\"'<>]+)", re.I)
# bare-host usage in curl/wget invocations, e.g. `curl api.example.com/x`.
# Flag skipper handles attached and separate (incl. quoted) flag arguments.
# Best-effort by design: exotic shell quoting can evade this — the real fetch
# path is shared/fetchers/, and WebFetch is covered exactly by URL_RE above.
CURL_BARE_RE = re.compile(
    r"\b(?:curl|wget|http|https)\s+"
    r"(?:-{1,2}[\w-]+(?:[= ](?:'[^']*'|\"[^\"]*\"|[^-\s'\"]\S*))?\s+)*"
    r"['\"]?([a-z0-9][a-z0-9.-]*\.[a-z]{2,})",
    re.I)


def allowed_domains():
    domains = set(BUILTIN)
    try:
        text = open(SOURCES, encoding="utf-8").read()
    except OSError:
        return None
    for m in INLINE_LIST_RE.finditer(text):
        for d in m.group(1).split(","):
            d = d.strip()
            if "." in d:
                domains.add(d.lower())
    for line in text.splitlines():
        line = line.split("#", 1)[0]
        m = DOMAIN_RE.match(line)
        if m:
            domains.add(m.group(1).lower())
    return domains


def host_allowed(host, domains):
    host = host.lower().split("@")[-1]        # drop userinfo decoys (user:pass@)
    host = host.rstrip(".").split(":", 1)[0]  # drop port
    if not host:
        return False
    if host in domains:
        return True
    return any(host.endswith("." + d) for d in domains)


def extract_hosts(tool_name, tool_input):
    hosts = set()
    if tool_name == "WebFetch":
        url = tool_input.get("url") or ""
        m = URL_RE.match(url) or URL_RE.search(url)
        if m:
            hosts.add(m.group(1))
        elif url:
            # WebFetch always targets a URL; unparseable => treat host as unknown
            hosts.add(url.split("/", 1)[0])
    elif tool_name == "Bash":
        cmd = tool_input.get("command") or ""
        for m in URL_RE.finditer(cmd):
            hosts.add(m.group(1))
        for m in CURL_BARE_RE.finditer(cmd):
            hosts.add(m.group(1))
    return hosts


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # nothing to inspect
    hosts = extract_hosts(payload.get("tool_name", ""),
                          payload.get("tool_input") or {})
    if not hosts:
        sys.exit(0)  # no network use detected — allow
    domains = allowed_domains()
    if domains is None:
        deny("net allowlist: data/sources.yaml unreadable — network calls are "
             "fail-closed. Fix the registry first.")
    bad = sorted(h for h in hosts if not host_allowed(h, domains))
    if bad:
        deny("Domain(s) not in data/sources.yaml allowlist: %s. "
             "If this source is legitimate, add its domain to sources.yaml "
             "(with schema + fallbacks) instead of fetching ad hoc." % ", ".join(bad))
    sys.exit(0)


if __name__ == "__main__":
    main()

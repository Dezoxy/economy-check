#!/usr/bin/env python3
"""PostToolUse hook (Write|Edit): deterministic report lint.

Enforces the mechanical half of the rubric the moment a report file is written:
  - no naked numbers (every significant figure needs a [src:provider/date] tag
    in its paragraph),
  - required sections present + KOCKÁZATI KERET + disclaimer (once the draft is
    long enough to plausibly be complete),
  - stale source-tag warning (>7 days old).

quality_gate.py imports lint_report() from here so Stop re-checks the same rules.
"""
import json
import os
import re
import sys
from datetime import date, datetime

MIN_CHARS_FOR_STRUCTURE = 2500  # incremental drafts: only number-lint below this

REPORT_PATH_RE = re.compile(r"/(?:[^/]+)/reports/.*\.md$")

SECTION_REQUIREMENTS = {
    # report-type keyword in filename -> list of (label, regex on ## headers or body)
    "heti-piaci-update": [
        ("VILÁG/GEOPOLITIKA section", r"(?im)^##.*\b(VIL[ÁA]G|GEOPOLITIK)"),
        ("MAKRÓ section", r"(?im)^##.*MAKR[ÓO]"),
        ("KRIPTO section", r"(?im)^##.*KRIPTO"),
        ("BITCOIN section", r"(?im)^##.*BITCOIN"),
        ("ÖSSZESSÉGÉBEN synthesis", r"(?im)^(##.*\bössze|összességében)"),
        ("KOCKÁZATI KERET box", r"(?i)KOCK[ÁA]ZATI\s+KERET"),
        ("JÖVŐ HÉT calendar", r"(?im)^##.*J[ÖO]V[ŐO]\s+H[ÉE]T"),
        ("invalidation trigger (veszélyzóna)", r"(?i)veszélyz[óo]na"),
        ("disclaimer", r"(?i)nem\s+min[őo]s[üu]l\s+befektet[ée]si\s+tan[áa]csad[áa]s"),
    ],
    # event-note: only Type A (FOMC) mandates HATÁSOK; Types B/C/D close differently
    # (A MOTORHÁZTETŐ ALATT / SZEMÉLYES KOMMENTÁR / PREDIKCIÓK) — see event-note.md.
    "event-note": [
        ("closing section (KOMMENTÁR/SZEMÉLYES/ÖSSZE/HATÁSOK)",
         r"(?im)^##.*(KOMMENT[ÁA]R|SZEM[ÉE]LYES|[ÖO]SSZE|HAT[ÁA]SOK|PREDIKCI[ÓO])"),
        ("disclaimer", r"(?i)nem\s+min[őo]s[üu]l\s+befektet[ée]si\s+tan[áa]csad[áa]s"),
    ],
    "fomc": [
        ("HATÁSOK section", r"(?im)^##.*HAT[ÁA]SOK"),
        ("SAJTÓTÁJÉKOZTATÓ section", r"(?im)^##.*SAJT[ÓO]"),
        ("closing kommentár", r"(?im)^##.*(KOMMENT[ÁA]R|SZEM[ÉE]LYES|[ÖO]SSZE)"),
        ("disclaimer", r"(?i)nem\s+min[őo]s[üu]l\s+befektet[ée]si\s+tan[áa]csad[áa]s"),
    ],
    "onchain-review": [
        ("what-to-watch close", r"(?i)(mit\s+figyel|tripwire|figyel[őo]pont)"),
        ("disclaimer", r"(?i)nem\s+min[őo]s[üu]l\s+befektet[ée]si\s+tan[áa]csad[áa]s"),
    ],
    "altcoin-screen": [
        ("Kockázatok section", r"(?im)^##.*Kock[áa]zat"),
        ("Lehetőségek section", r"(?im)^##.*Lehet[őo]s[ée]g"),
        ("Források section", r"(?im)^##.*forr[áa]s"),
        ("disclaimer", r"(?i)nem\s+min[őo]s[üu]l\s+befektet[ée]si\s+tan[áa]csad[áa]s"),
    ],
}

SRC_TAG_RE = re.compile(r"\[src:([a-z0-9_.-]+)/(\d{4}-\d{2}-\d{2})\]")

# Stripped before naked-number scanning (structural numbers, not data points).
# ORDER MATTERS: specific multi-token patterns first, general ones (bare years) last.
WHITELIST_RES = [
    re.compile(r"\[src:[^\]]+\]"),                     # the tags themselves
    re.compile(r"\(EU\)\s*\d{4}/\d+"),                 # EU regulation refs (MiCA…)
    re.compile(r"\b\d{4}\.\s*évi\b", re.I),            # HU law refs (2007. évi CXXXVIII.)
    re.compile(r"\d{4}-\d{2}-\d{2}"),                 # ISO dates
    re.compile(r"\b\d{1,2}:\d{2}\b"),                  # clock times
    re.compile(r"\b\d{1,3}\s*(?:napos|napi|hetes|heti|[óo]r[áa]s)\b", re.I),  # MA periods
    # MA color-legend vocabulary: "piros 50 / kék 100 / zöld 150 / fekete 200 napi"
    re.compile(r"\b(?:piros|k[ée]k|z[öo]ld|fekete|lila)\s+\d{1,3}\b", re.I),
    re.compile(r"\b\d{1,3}(?:\s*/\s*\d{1,3})+\b"),     # slash-separated period lists
    re.compile(r"\b(?:MA|EMA|SMA|RSI|VWAP)\s?\(?\d{1,3}(?:,\s?\d)?\)?", re.I),
    re.compile(r"\bT\+\d\b"),
    re.compile(r"\bTOTAL3?\b", re.I),
    re.compile(r"\bS&P\s?500\b|\bRussell\s?2000\b|\b13F\b", re.I),
    # bare years — LAST, and only when NOT followed by a currency/unit word
    # ("2026-ban" strips; "az ETH 2050 dollár" stays a naked number)
    re.compile(r"\b(19|20)\d\d\b"
               r"(?!\s?(?:doll[áa]r|USD|\$|forint|HUF|Ft|pont|eur[óo]?|EUR|BTC|ETH|"
               r"ezer|milli[óo]|milli[áa]rd|MRD|bp)\b)", re.I),
]

# Significant figures: currency, percent, 3+ digit numbers, decimals, and small
# numbers with a magnitude/unit word ("45 millió", "16 MRD HUF", "25 bp").
NUMBER_RE = re.compile(
    r"[$€£]\s?\d|\d\s?%|\d{3,}|\d+[.,]\d+|"
    r"(?i:\d+\s?(?:bp|ezer|milli[óo]|milli[áa]rd|mrd|billi[óo])\b)")


def paragraphs(text):
    """Lintable units: blank-line paragraphs, but headings and dash bullets each
    stand alone — a tag on one bullet must not exempt its neighbours, and prose
    glued directly under a '#' heading must still be scanned."""
    buf, out, fence = [], [], False

    def flush():
        if buf:
            out.append("\n".join(buf))
            del buf[:]

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if not stripped:
            flush()
        elif stripped.startswith("#") or re.match(r"^[-*]\s", stripped):
            flush()
            out.append(line)
        else:
            buf.append(line)
    flush()
    return out


def report_type(path):
    name = os.path.basename(path)
    if "fomc" in name:
        return "fomc"
    for key in SECTION_REQUIREMENTS:
        if key in name:
            return key
    if re.search(r"cpi|pce|jobs|geo", name):
        return "event-note"
    return None


def lint_report(path, text):
    """Returns (violations, warnings) — lists of strings."""
    violations, warnings = [], []
    rtype = report_type(path)

    # 1. naked numbers (always, even on partial drafts)
    for para in paragraphs(text):
        if para.lstrip().startswith("#"):
            continue  # heading LINES only — glued prose is its own unit now
        stripped = para
        for wre in WHITELIST_RES:
            stripped = wre.sub(" ", stripped)
        has_valid_tag = SRC_TAG_RE.search(para) is not None
        if "[src:" in para and not has_valid_tag:
            excerpt = re.sub(r"\s+", " ", para)[:110]
            violations.append("malformed source tag (must be "
                              "[src:provider/YYYY-MM-DD]): \"%s…\"" % excerpt)
        elif NUMBER_RE.search(stripped) and not has_valid_tag:
            excerpt = re.sub(r"\s+", " ", para)[:110]
            violations.append("naked number (no [src:provider/date] in paragraph): "
                              "\"%s…\"" % excerpt)

    # 2. structure — only when the draft is plausibly complete
    if rtype and len(text) >= MIN_CHARS_FOR_STRUCTURE:
        for label, pattern in SECTION_REQUIREMENTS[rtype]:
            if not re.search(pattern, text):
                violations.append("missing %s (template: %s.md)" % (label, rtype))

    # 3. source-tag freshness (warning only — some sources are legitimately older)
    m = re.match(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
    ref = date.today()
    if m:
        try:
            ref = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            pass  # digit-shaped but invalid filename date — fall back to today
    for provider, dstr in SRC_TAG_RE.findall(text):
        try:
            age = (ref - datetime.strptime(dstr, "%Y-%m-%d").date()).days
        except ValueError:
            continue
        if age > 7:
            warnings.append("stale tag [src:%s/%s] — %dd old at publish; verify or "
                            "label the staleness in prose" % (provider, dstr, age))
        if age < 0:
            violations.append("future-dated tag [src:%s/%s]" % (provider, dstr))

    return violations, warnings


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not REPORT_PATH_RE.search(path.replace(os.sep, "/")):
        sys.exit(0)
    if not os.path.exists(path):
        sys.exit(0)
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        sys.exit(0)

    violations, warnings = lint_report(path, text)
    if violations:
        lines = ["report_lint: %d violation(s) in %s:" % (len(violations),
                 os.path.basename(path))]
        lines += ["  - " + v for v in violations[:20]]
        if len(violations) > 20:
            lines.append("  … and %d more" % (len(violations) - 20))
        lines += ["  (warnings: %s)" % "; ".join(warnings[:5])] if warnings else []
        lines.append("Fix these in the report file. Every figure needs its "
                     "[src:provider/date] tag from data/cache/.")
        print(json.dumps({"decision": "block", "reason": "\n".join(lines)}))
        sys.exit(0)
    if warnings:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "report_lint warnings: " + "; ".join(warnings[:10]),
        }}))
    sys.exit(0)


if __name__ == "__main__":
    main()

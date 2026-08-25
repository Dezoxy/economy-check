#!/usr/bin/env python3
"""Stop hook: the rubric gate. A session that wrote a report may not finish until
every written report (a) passes the full lint and (b) has a passing editor score
sidecar (<report>.score.json: total >= 80, no category below 60% of its weight).

Scope guard: engages ONLY when this session's transcript contains a Write/Edit to
*/reports/*.md — ordinary coding sessions in this repo stop normally.

Loop cap: after MAX_ATTEMPTS blocked stops per report we allow the stop (logged);
delivery still refuses unscored/failing reports, so allowing a stop never ships one.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_lint import lint_report, MIN_CHARS_FOR_STRUCTURE  # noqa: E402

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
STATE_PATH = os.path.join(ROOT, "data", ".gate_state.json")
MAX_ATTEMPTS = 3
GATE_TOTAL = 80
CATEGORY_FLOOR = 0.60

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
REPORT_MD_RE = re.compile(r"/reports/.*\.md$")


def _walk_tool_uses(obj):
    """Yield (tool_name, input_dict) for every tool_use block in a transcript entry."""
    if isinstance(obj, dict):
        if obj.get("type") == "tool_use" and isinstance(obj.get("input"), dict):
            yield obj.get("name"), obj["input"]
        for v in obj.values():
            yield from _walk_tool_uses(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_tool_uses(v)


def reports_written(transcript_path):
    """Report files this session actually WROTE (Write/Edit tools only — a session
    that merely reads an old report must not trip the gate)."""
    paths = set()
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                if "/reports/" not in line or "file_path" not in line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                for name, tin in _walk_tool_uses(entry):
                    p = tin.get("file_path") or ""
                    if (name in WRITE_TOOLS
                            and REPORT_MD_RE.search(p.replace(os.sep, "/"))
                            and not p.endswith(".score.json")
                            and os.path.exists(p)):
                        paths.add(os.path.abspath(p))
    except OSError:
        pass
    return sorted(paths)


def check_score_sidecar(report_path):
    problems = []
    sidecar = re.sub(r"\.md$", "", report_path) + ".score.json"
    if not os.path.exists(sidecar):
        return ["no editor score yet: run the editor agent, write %s "
                "(schema: rubric.md scoring protocol)" % os.path.basename(sidecar)]
    try:
        score = json.load(open(sidecar, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return ["unreadable score sidecar: %s" % e]
    if not isinstance(score, dict):
        return ["score sidecar must be a JSON object (rubric.md scoring protocol)"]
    cats = score.get("categories")
    if not isinstance(cats, dict) or not cats:
        return ["score sidecar needs a 'categories' OBJECT keyed by category name "
                "(each {\"score\": n, \"max\": m}) — editor must itemize"]
    recomputed = 0
    for name, cat in cats.items():
        try:
            pts, mx = float(cat["score"]), float(cat["max"])
        except (KeyError, TypeError, ValueError):
            problems.append("category %s: malformed (needs score+max)" % name)
            continue
        recomputed += pts
        if mx > 0 and pts < CATEGORY_FLOOR * mx:
            problems.append("category %s below floor: %.1f/%.0f (< %d%%)"
                            % (name, pts, mx, int(CATEGORY_FLOOR * 100)))
    total = score.get("total")
    if not isinstance(total, (int, float)):
        problems.append("score sidecar: numeric 'total' missing")
    else:
        if abs(recomputed - total) > 0.51:
            problems.append("score arithmetic mismatch: total=%s but categories "
                            "sum to %.1f — editor must fix the itemization"
                            % (total, recomputed))
        if total < GATE_TOTAL:
            problems.append("total %.0f < publish gate %d — apply the editor's "
                            "fix list, then re-score" % (total, GATE_TOTAL))
    return problems


def load_state():
    try:
        return json.load(open(STATE_PATH, encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1)


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if payload.get("stop_hook_active"):
        # we already blocked once in this stop cycle; rely on attempt cap below
        pass
    transcript = payload.get("transcript_path") or ""
    session = payload.get("session_id") or "unknown"
    reports = reports_written(transcript)
    if not reports:
        sys.exit(0)

    all_problems = {}
    for rp in reports:
        problems = []
        try:
            text = open(rp, encoding="utf-8").read()
        except OSError as e:
            all_problems[rp] = ["unreadable: %s" % e]
            continue
        if len(text) < MIN_CHARS_FOR_STRUCTURE:
            problems.append("report is only %d chars — below any template band; "
                            "finish the draft" % len(text))
        violations, _ = lint_report(rp, text)
        problems += violations
        problems += check_score_sidecar(rp)
        if problems:
            all_problems[rp] = problems

    if not all_problems:
        sys.exit(0)

    state = load_state()
    skey = session
    state.setdefault(skey, {})
    blocking = {}
    for rp, problems in all_problems.items():
        attempts = state[skey].get(rp, 0)
        if attempts >= MAX_ATTEMPTS:
            continue  # cap reached: allow stop, delivery gate still protects
        state[skey][rp] = attempts + 1
        blocking[rp] = problems
    save_state(state)

    if not blocking:
        print("quality_gate: attempt cap reached; allowing stop. Reports still "
              "FAIL the gate and cannot be delivered.", file=sys.stderr)
        sys.exit(0)

    lines = ["quality_gate: the session wrote report(s) that do not pass the "
             "publish gate. Fix before finishing:"]
    for rp, problems in blocking.items():
        lines.append("• %s" % os.path.relpath(rp, ROOT))
        lines += ["    - " + p for p in problems[:15]]
        if len(problems) > 15:
            lines.append("    … and %d more" % (len(problems) - 15))
    lines.append("Protocol: fix content → fact-checker → editor re-score "
                 "(sidecar .score.json) → stop. See crypto-analyst/templates/rubric.md.")
    print(json.dumps({"decision": "block", "reason": "\n".join(lines)}))
    sys.exit(0)


if __name__ == "__main__":
    main()

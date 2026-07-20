#!/bin/bash
# run_job.sh — headless pipeline entry point (launchd/cron on the Mac, or Cowork).
#
#   shared/scripts/run_job.sh <job> <report-type> [date]
#   e.g. shared/scripts/run_job.sh crypto-analyst weekly-market-update
#
# Steps: fetch manifest -> verify cache -> claude -p "/<report-type-skill>" ->
# assert artifacts. Delivery happens INSIDE the skill (quality gate wraps it);
# every failure path here sends an ops alert — an unattended run must never
# die silently.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
JOB="${1:?usage: run_job.sh <job> <report-type> [date]}"
REPORT_TYPE="${2:?usage: run_job.sh <job> <report-type> [date]}"
RUN_DATE="${3:-$(date +%F)}"
LOG_DIR="$ROOT/data/logs"
LOG="$LOG_DIR/${RUN_DATE}_${JOB}_${REPORT_TYPE}.log"
CLAUDE_TIMEOUT="${CLAUDE_TIMEOUT:-5400}"   # wall-clock cap for the LLM plane (s)
mkdir -p "$LOG_DIR"

# launchd/cron run with PATH=/usr/bin:/bin — resolve the claude CLI explicitly.
CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude || echo "$HOME/.local/bin/claude")}"

alert() {
    echo "ALERT: $1" | tee -a "$LOG" >&2
    python3 "$ROOT/shared/delivery/deliver.py" --alert "$1" >>"$LOG" 2>&1 || true
}

echo "=== economy-check run: $JOB/$REPORT_TYPE @ $RUN_DATE ===" | tee -a "$LOG"

if [ ! -x "$CLAUDE_BIN" ]; then
    alert "run_job $JOB/$REPORT_TYPE $RUN_DATE: claude CLI not found (CLAUDE_BIN=$CLAUDE_BIN)"
    exit 1
fi

# 1. Data plane: pull the job's manifest into the dated cache (fallbacks inside).
if ! python3 "$ROOT/shared/fetchers/run.py" --manifest "$REPORT_TYPE" \
        --date "$RUN_DATE" >>"$LOG" 2>&1; then
    alert "run_job $JOB/$REPORT_TYPE $RUN_DATE: required fetcher failed (see $LOG)"
    exit 1
fi

# 2. Freshness/schema verification (the skill re-checks this too).
if ! python3 "$ROOT/shared/fetchers/run.py" --verify "$REPORT_TYPE" \
        --date "$RUN_DATE" >>"$LOG" 2>&1; then
    alert "run_job $JOB/$REPORT_TYPE $RUN_DATE: cache verify FAILED (see $LOG)"
    exit 1
fi

# 3. Reasoning plane: run the skill headless, wall-clock-capped (macOS has no GNU
#    timeout by default; perl alarm is portable). Hooks enforce net allowlist +
#    lint + quality gate; permissions come from .claude/settings.json.
cd "$ROOT"
if ! perl -e 'alarm shift; exec @ARGV' "$CLAUDE_TIMEOUT" \
        "$CLAUDE_BIN" -p "/$REPORT_TYPE $RUN_DATE" \
        --permission-mode acceptEdits \
        --max-turns 120 \
        >>"$LOG" 2>&1; then
    alert "run_job $JOB/$REPORT_TYPE $RUN_DATE: claude run failed or timed out (see $LOG)"
    exit 1
fi

# 4. Artifact assertion: a zero exit from claude is not proof of a report — the
#    skill may have stopped gracefully (missing data, gate cap). Verify the output.
RPT="$ROOT/$JOB/reports/${RUN_DATE%%-*}/${RUN_DATE}-heti-piaci-update.md"
if [ "$REPORT_TYPE" != "weekly-market-update" ]; then
    RPT="$ROOT/$JOB/reports/${RUN_DATE%%-*}/${RUN_DATE}-${REPORT_TYPE}.md"
fi
if ! python3 - "$RPT" >>"$LOG" 2>&1 <<'PYEOF'
import json, re, sys, os
rpt = sys.argv[1]
sidecar = re.sub(r"\.md$", "", rpt) + ".score.json"
assert os.path.exists(rpt), "report missing: %s" % rpt
score = json.load(open(sidecar))
assert isinstance(score.get("total"), (int, float)) and score["total"] >= 80, \
    "gate not passed: %s" % score.get("total")
print("artifacts OK: %s (score %s)" % (os.path.basename(rpt), score["total"]))
PYEOF
then
    alert "run_job $JOB/$REPORT_TYPE $RUN_DATE: run ended without a gate-passing report (see $LOG)"
    exit 1
fi

echo "=== done: $JOB/$REPORT_TYPE @ $RUN_DATE ===" | tee -a "$LOG"

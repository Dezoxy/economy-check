# economy-check

Self-hosted, agent-driven market & economy analysis. A deterministic Python data plane
feeds LLM analysts that write a Hungarian weekly market report; a deterministic quality
plane refuses to publish it if it doesn't score well enough.

The bar is explicit and measured, not felt: **at least KriptoVadász parity**, scored with
`crypto-analyst/templates/rubric.md` against a 132-post benchmark corpus. Voice is
*konstruktív, de őszinte* — constructive framing, risks never minimized, misses graded as
loudly as hits.

Private repo. The corpus is paid content (patterns quoted, never republished), and the
reports are personal-use education — **not investment advice**.

## Status

Phase 1 (`crypto-analyst`) has cleared steps A–F: corpus, templates, doctrine, skill,
16 registered sources, a live report (95.5/100) and a 3-week backtest that beat the benchmark on the
honest parity metric (category C: 17.0 vs 14.0 average). Step G — scheduling, live
delivery, monitoring — is what's left. Phases 2–4 (macro-analyst, portfolio-review,
daily-pulse) are planned.

Live delivery is the one thing not yet proven end-to-end: `TELEGRAM_*` and `SMTP_*` are
still blank in `.env`, so only `deliver.py --dry-run` has been exercised.

**[PLAN.md](PLAN.md) is the live status board, phase detail and backlog — read it there,
not here.**

## Quick start

```bash
# 1. Secrets — copy the template and fill in at minimum FRED_API_KEY
cp .env.example .env

# 2. Pull today's data into the immutable dated cache, then verify the manifest
python3 shared/fetchers/run.py --manifest weekly-market-update --date "$(date +%F)"
python3 shared/fetchers/run.py --verify   weekly-market-update --date "$(date +%F)"

# 3. Produce the report (inside Claude Code)
#    /weekly-market-update              -> live run for today
#    /weekly-market-update dry-run      -> acceptance check, writes nothing
#    /weekly-market-update backtest 2026-05-17  -> historical parity run

# 4. Or run the whole thing headless (launchd/cron)
shared/scripts/run_job.sh crypto-analyst weekly-market-update
```

Useful one-offs:

```bash
python3 shared/fetchers/run.py --health                    # per-source health log
python3 shared/fetchers/backfill.py --date 2026-05-17      # as-of cache for a backtest
python3 shared/delivery/render_pdf.py <report.md>          # regenerate the PDF
python3 shared/delivery/deliver.py --report <report.md> --dry-run
```

## How a report gets made

```
data plane            reasoning plane                  quality plane
(Python, exact)       (LLM, prose only)                (hooks, deterministic)

sources.yaml          4 analyst subagents, parallel    net_allowlist  (PreToolUse)
   -> fetchers            -> sourced briefs            report_lint    (PostToolUse)
   -> data/cache/     compose per template             fact-checker   (adversarial)
      <date>/*.json   grade + append ledger calls      editor -> .score.json
                                                       quality_gate   (Stop)
                                                       render_pdf -> deliver.py
```

The load-bearing rule: **the model never invents or computes a number.** All arithmetic —
indicators, deltas, TOTAL3 — happens in `shared/fetchers/`, and every figure in a report
carries a `[src:provider/YYYY-MM-DD]` tag traceable to that day's cache. The lint blocks
naked numbers; the fact-checker re-derives them; the editor scores the result; the Stop
gate refuses to finish below 80/100 or with any category under 60% of its weight.
Generator ≠ verifier throughout — the session that writes a report never scores it.

## Layout

| Path | What |
|---|---|
| `AGENTS.md` | the constitution — hard rules for every agent. Read first. |
| `PLAN.md` | living roadmap: phases, status board, backlog, changelog |
| `CLAUDE.md` | Claude Code specifics (hooks, skill invocations, mirrors) |
| `data/sources.yaml` | source registry — domains double as the network allowlist |
| `shared/fetchers/` | the data plane: one module per source, plus indicators + backfill |
| `shared/delivery/` | `deliver.py`, `render_pdf.py`, Telegram + SMTP transports |
| `.claude/` | skills, subagents, hooks, permissions |
| `.codex/`, `.agents/` | mirrors of `.claude/` for other runtimes — keep in sync |
| `crypto-analyst/` | Phase 1 job: corpus, templates, ledger, reports |

Gitignored and local-only: `examples/`, `data/cache/`, `data/logs/`, `.env`, and the
derived `.pdf`/`.html` under `*/reports/`.

## Working on this repo

Read [AGENTS.md](AGENTS.md) before touching anything — it is normative, this file is not.
Two rules worth repeating here:

1. **Never fix a failing gate by weakening the rubric, the lint, or the hooks.** Raise the
   report instead. Quality-plane changes are engineering decisions made deliberately,
   outside report runs.
2. **`.codex/` and `.agents/` are mirrors, not forks.** Edit `.claude/` first, then re-copy
   the changed file into every mirror in the same commit.

Python is stdlib-only by design (bare `python3` on Mac and in Cowork). The two exceptions
are matplotlib for charts and headless Chrome — a system tool, not a package — for PDF
rendering.

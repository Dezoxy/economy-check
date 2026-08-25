# AGENTS.md — economy-check constitution

Source of truth for every agent working in this repo — Claude Code, Cowork, Codex, subagents.
Read this before doing anything. The roadmap lives in [PLAN.md](PLAN.md) — read that second,
update it as you complete work. [README.md](README.md) is the human entry point; it is a
summary of this file, never a second source of truth.

**Runtime mirrors.** The canonical agent config lives in `.claude/`. `.codex/` (TOML agents +
`hooks.json` + hook copies) and `.agents/skills/` (portable skill copy) are *mirrors* of it for
other runtimes. They are plain copies, not symlinks: **change `.claude/` first, then re-copy the
changed file into every mirror in the same commit.** A hook that exists in three versions is a
quality plane with three different opinions.

## Mission

Self-hosted, agent-driven market & economy analysis. Output quality bar: at least
KriptoVadász parity, measured by `crypto-analyst/templates/rubric.md`, never felt.
Voice: **konstruktív, de őszinte** — constructive framing, risks never minimized.

## The three planes (hard architectural rule)

1. **Data plane (deterministic).** `shared/fetchers/` pull from the registry
   `data/sources.yaml` into immutable dated caches `data/cache/<YYYY-MM-DD>/<source>.json`.
   All arithmetic (indicators, deltas, TOTAL3) happens HERE, in code.
2. **Reasoning plane (LLM).** Skills + subagents read cache files and write prose.
   **The model never invents or computes a number.** Every figure in a report traces to
   a cache file or a cited fetch: `[src:provider/YYYY-MM-DD]`.
3. **Quality plane (deterministic).** Hooks enforce: network egress allowlist
   (`net_allowlist.py`), report lint (`report_lint.py`), publish gate
   (`quality_gate.py`, Stop). Delivery (`shared/delivery/deliver.py`) independently
   re-checks the gate. Generator ≠ verifier: fact-checker and editor agents review
   every report; the editor's score sidecar (`<report>.score.json`) is the gate input.

## Hard rules (any agent, any run)

- **No naked numbers.** Every figure carries `[src:provider/date]`. Lint-enforced.
  Provider is a sources.yaml source id (= cache filename, e.g. `binance_klines`)
  or a bare domain for cited in-run fetches (e.g. `reuters.com`). The one permitted
  derived figure: approximate HUF conversions against the cached `fx_rates` rate,
  tagged `[src:fx_rates/date]` (fact-checker recomputes, ±5% tolerance).
- **Balance by construction.** Every report: bear case, bull case, exact invalidation
  levels, KOCKÁZATI KERET (weekly) / anti-panic machinery (event notes). No advice
  framing, ever — watch-points and conditionals only; disclaimer block mandatory.
- **Accountability.** Every forward-looking statement → `crypto-analyst/ledger.jsonl`
  (schema: `crypto-analyst/templates/prediction-ledger.md`). Due calls are graded in
  the next report — misses named as loudly as hits.
- **Reproducibility.** Reports derive only from their dated cache; a run can be
  replayed from `data/cache/<date>/`.
- **Backtest discipline.** Historical parity runs (`backtest <date>`) build an as-of cache via
  `shared/fetchers/backfill.py`, write to `crypto-analyst/reports/backtests/`, and obey three
  rules: prices come from cache ONLY (a fetched archive page renders *today's* ticker widget,
  not the publication-date one), citations may not postdate the report date, and **nothing is
  written to the live ledger** — it records reality, not rehearsals.
- **Network discipline.** Only domains registered in `data/sources.yaml` (hook-enforced).
  New source = registry entry with schema + fallbacks, not an ad-hoc fetch.
- **Privacy & legal.** Repo private. `examples/`, `data/cache/`, `.env` are gitignored.
  Secrets only in `.env` — never in code, YAML, markdown, or logs. Corpus is paid
  content: quote patterns, never republish. Reports are personal-use education,
  not investment advice.
- **Language.** Reports in Hungarian per `crypto-analyst/templates/style-guide.md`;
  code, commits, and engineering docs in English.

## Repo map

| Path | What |
|---|---|
| `README.md` | human entry point (status, quick start) — summary of this file |
| `PLAN.md` | living roadmap — phases, checkboxes, changelog |
| `data/sources.yaml` | source registry: domains (allowlist), schemas, fallbacks, per-job manifests (16 sources / 5 manifests) |
| `data/cache/<date>/` | immutable dated pulls (gitignored); `health.jsonl` = per-fetch health log |
| `shared/fetchers/` | `run.py --manifest/--verify/--health/--check`; 15 source modules for the registry's 16 sources |
| `shared/fetchers/backfill.py` | as-of cache builder for backtests (`--date --sources`) |
| `shared/fetchers/indicators.py` | all indicator math, proven by `test_indicators.py` |
| `shared/delivery/` | `deliver.py --report/--alert` (gate-checked) + `telegram.py`, `emailer.py` |
| `shared/delivery/render_pdf.py` | md → house-styled HTML → PDF; the PDF is the delivery artifact |
| `shared/charting/style.py` | house chart style (MA colors match prose vocabulary) |
| `shared/scripts/run_job.sh` | headless entry: fetch → verify → `claude -p /skill` → assert artifacts |
| `shared/scripts/` | `ingest_examples.py` (corpus build), `seed_ledger.py` (benchmark calls) |
| `.claude/skills/` | one skill per report type (pipeline orchestration) — `weekly-market-update` |
| `.claude/agents/` | subagents: 4 analysts + fact-checker + editor |
| `.claude/hooks/` | the quality plane |
| `.codex/`, `.agents/` | mirrors of the above for other runtimes — keep in sync, never fork |
| `crypto-analyst/templates/` | report templates, rubric, style guide, ledger schema, doctrine |
| `crypto-analyst/templates/analytical-doctrine.md` | the reasoning playbook — loaded by every analyst |
| `crypto-analyst/corpus/corpus.jsonl` | 132-post benchmark corpus, 998K chars (private) |
| `crypto-analyst/ledger.jsonl` | machine prediction ledger (67 calls: 54 benchmark, 13 own) |
| `crypto-analyst/reports/<year>/` | output: `YYYY-MM-DD-<type>.md` + `.score.json` + `.pdf` |
| `crypto-analyst/reports/backtests/` | parity runs: our report + `kv-<date>.score.json` (benchmark) |
| `crypto-analyst/reports/scores.jsonl` | append-only score trend (gate + monitoring input) |

## Workflow index

| Task | Entry point |
|---|---|
| Weekly flagship report | skill `weekly-market-update` (skills own the full pipeline) |
| Skill acceptance check | `weekly-market-update dry-run` — pipeline outline, no report written |
| Historical parity run | `weekly-market-update backtest <YYYY-MM-DD>` (backtest rules above) |
| Data pull / cache check | `python3 shared/fetchers/run.py --manifest <type> --date <d>` then `--verify` |
| As-of cache for a backtest | `python3 shared/fetchers/backfill.py --date <YYYY-MM-DD>` |
| Source health / registry check | `run.py --health`, `run.py --check` |
| Render the delivery PDF | `python3 shared/delivery/render_pdf.py <report.md>` |
| Deliver / ops alert | `python3 shared/delivery/deliver.py --report <md> [--dry-run]` |
| Scheduled run | `shared/scripts/run_job.sh crypto-analyst weekly-market-update` |
| Grade predictions | ledger rules in `templates/prediction-ledger.md`; grade in-report |
| Score a report | editor agent → `<report>.score.json` (rubric protocol) |

## Report pipeline contract (what every report skill does)

1. Verify cache for the report type's manifest (`run.py --verify`); refuse on missing
   required sources; label degraded ones in-prose.
2. Spawn the job's analyst subagents in parallel; each returns a sourced brief.
3. Compose per the template; every number tagged; charts referenced with numbers
   restated in prose.
4. Update the ledger: grade due calls (symmetrically), append new calls.
5. Fact-checker pass (adversarial): every tag verified against cache; failures fixed.
6. Editor pass: rubric score → `<report>.score.json`; iterate until total ≥ 80 and
   no category < 60% of weight.
7. Render the PDF (`render_pdf.py`) — the delivery artifact. Chrome headless does the print;
   if Chrome is missing the HTML still lands and delivery falls back to the `.md`.
8. Deliver via `deliver.py` (skill asks first in interactive sessions; scheduled runs
   deliver automatically). Backtests stop at step 6: no PDF, no delivery, no ledger write.

Do not "fix" a failing gate by weakening the rubric, the lint, or the hooks — raise
the report instead. Changes to the quality plane are engineering decisions made with
tom, outside report runs.

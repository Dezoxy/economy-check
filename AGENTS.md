# AGENTS.md — economy-check constitution

Source of truth for every agent working in this repo (Claude Code, Cowork, subagents).
Read this before doing anything. The roadmap lives in [PLAN.md](PLAN.md) — read that second,
update it as you complete work.

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
| `PLAN.md` | living roadmap — phases, checkboxes, changelog |
| `data/sources.yaml` | source registry: domains (allowlist), schemas, fallbacks, per-job manifests |
| `data/cache/<date>/` | immutable dated pulls (gitignored) |
| `shared/fetchers/` | `run.py --manifest/--verify/--health`, one module per source |
| `shared/delivery/` | `deliver.py --report/--alert` (Telegram + email, gate-checked) |
| `shared/charting/style.py` | house chart style (MA colors match prose vocabulary) |
| `shared/scripts/run_job.sh` | headless entry: fetch → verify → `claude -p /skill` |
| `.claude/skills/` | one skill per report type (pipeline orchestration) |
| `.claude/agents/` | subagents: analysts + fact-checker + editor |
| `.claude/hooks/` | the quality plane |
| `crypto-analyst/templates/` | report templates, rubric, style guide, ledger schema |
| `crypto-analyst/corpus/corpus.jsonl` | 132-post benchmark corpus (private) |
| `crypto-analyst/ledger.jsonl` | machine prediction ledger |
| `crypto-analyst/reports/<year>/` | output: `YYYY-MM-DD-<type>.md` + `.score.json` |

## Workflow index

| Task | Entry point |
|---|---|
| Weekly flagship report | skill `weekly-market-update` (skills own the full pipeline) |
| Data pull / cache check | `python3 shared/fetchers/run.py --manifest <type> --date <d>` then `--verify` |
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
7. Deliver via `deliver.py` (skill asks first in interactive sessions; scheduled runs
   deliver automatically).

Do not "fix" a failing gate by weakening the rubric, the lint, or the hooks — raise
the report instead. Changes to the quality plane are engineering decisions made with
tom, outside report runs.

# economy-check — Master Plan

> Self-hosted, agent-driven market & economy analysis pipeline.
> Goal: produce analyses at **minimum KriptoVadász quality**, on our own schedule,
> constructive in tone but honest about risk ("konstruktív, de őszinte").
>
> This file is the living roadmap. Agents: read this first. Update checkboxes + changelog as you work.

---

## 1. Mission & non-negotiable principles

1. **Three-plane architecture.** Deterministic *data plane* (Python fetchers → dated cache) → LLM *reasoning plane* (specialist subagents) → deterministic *quality gate* (hooks + rubric). The model never invents a number: every figure traces to a cache file or cited source (`[src:coingecko/2026-07-19]`).
2. **Generator ≠ verifier.** Every report passes an adversarial fact-checker and an editor before delivery. A Stop-hook rubric gate can refuse to finish.
3. **Balanced by construction.** Constructive/opportunity-focused voice, but every report must contain: bear case, risk box, invalidation levels ("this view is wrong if X"). A feed that only says positive things is worse than no feed.
4. **Reproducibility.** Each run's inputs are cached immutably under `data/cache/<date>/`. A report can be re-derived from its cache.
5. **Accountability.** Every prediction/call goes into a prediction ledger; hit-rates are reviewed monthly (ours *and* the benchmark corpus's).
6. **Privacy & legal.** Repo is **private** (corpus = paid Patreon content, never republished). Raw `examples/` and caches are gitignored. Secrets live in `.env`, never in git or markdown. Reports are for personal use; not investment advice.
7. **Portability.** Everything is plain files (AGENTS.md, skills, agents, hooks, scripts). Runs via Claude Code on the Mac/homelab (cron/launchd) *and* in Cowork cloud sessions. No hidden state.

## 2. Target repo layout

```
economy-check/
├── AGENTS.md                  # constitution for all agents (source of truth)
├── CLAUDE.md                  # thin: imports AGENTS.md + Claude Code specifics
├── PLAN.md                    # ← this file
├── .claude/
│   ├── settings.json          # permissions + hook wiring
│   ├── agents/                # subagents: analysts, fact-checker, editor
│   ├── skills/                # one skill per report type (+ style, charting)
│   └── hooks/                 # net allowlist, report lint, quality gate
├── shared/
│   ├── scripts/               # ingest, run, utilities        [ingest_examples.py ✅]
│   ├── fetchers/              # one small script per data source
│   ├── delivery/              # telegram.py, email.py
│   └── charting/              # consistent chart look
├── data/
│   ├── sources.yaml           # source registry + fallbacks + health
│   └── cache/<YYYY-MM-DD>/    # immutable dated pulls (gitignored)
├── examples/                  # raw saved inputs (gitignored, local only)
├── crypto-analyst/            # Phase 1 job
│   ├── corpus/                # normalized benchmark corpus   [corpus.jsonl ✅ 132 posts]
│   ├── templates/             # report templates, rubric, style guide, ledger
│   └── reports/<YYYY>/        # generated output (markdown + html)
├── macro-analyst/             # Phase 2 job (placeholder)
├── portfolio-review/          # Phase 3 job (placeholder)
└── daily-pulse/               # Phase 4 job (placeholder)
```

## 3. The Job Blueprint (standard steps for ANY job subfolder)

Every `Phase N — <job>/` runs the same sequence; each phase section below only defines
what is **unique** to that job. Quality bar: a job is not "done" until step G passes.

| Step | What | Definition of done |
|---|---|---|
| **A. Corpus** | Collect + normalize reference material into `corpus/corpus.jsonl` | inventory stats printed; <5% extraction failures |
| **B. Derive** | From corpus: `templates/*.md` (per report type), `rubric.md` (scored checklist), `style-guide.md`, `prediction-ledger.md` seed | reviewed by tom; rubric has measurable criteria |
| **C. Wire** | Skill(s) in `.claude/skills/`, job-specific subagent prompts, data manifest (what step D must fetch) | dry-run of skill produces correct outline |
| **D. Data** | Fetchers + `sources.yaml` entries for the job's data manifest, with fallbacks | all fetchers pass schema check + health check |
| **E. First report** | Full pipeline run, manual trigger, human review | report delivered end-to-end, all numbers sourced |
| **F. Backtest** | Generate for 2–3 historical periods; side-by-side vs corpus originals; score both with rubric | avg score ≥ benchmark ("minimum this quality" is measured, not felt) |
| **G. Operate** | Schedule (launchd/cron + Cowork fallback), delivery (Telegram + email), monitoring (failure alerts, staleness, score trend, ledger) | 2 consecutive unattended successful runs |

---

## Phase 0 — Foundation (repo root + shared/)          `status: in progress`

Built once, used by every job. Steps:

- [x] Repo folder + `.gitignore` (examples/, data/cache/, .env)
- [x] `git init`, private GitHub repo `economy-check` (Dezoxy/economy-check), first push
      (2026-07-20, tom OK'd pushing the corpus to the private repo)
- [x] `AGENTS.md` (constitution: mission, hard rules, workflow index) + thin `CLAUDE.md`
- [x] `.claude/settings.json` + hooks: `net_allowlist.py` (PreToolUse: only sources.yaml domains, fail-closed, userinfo-bypass-proof), `report_lint.py` (PostToolUse: sections, no naked numbers incl. HU magnitude words, freshness), `quality_gate.py` (Stop: score sidecar ≥80 + category floors, 3-attempt cap, engages only when the session wrote a report)
- [x] Shared subagents: `fact-checker.md`, `editor.md` (job-agnostic, parameterized by job folder)
- [x] `shared/delivery/`: Telegram bot push + SMTP email via `deliver.py` (independently re-checks the full gate; `--dry-run`/`--alert` modes) — *live send untested until `.env` secrets exist*
- [x] `data/sources.yaml` (16 sources incl. fx_rates for HUF conversions, 4 manifests) + fetcher framework (strict schema check, dated immutable cache with same-day retry short-circuit, schema-validated fallbacks cached under the requested id, health.jsonl) — coingecko reference fetcher live-tested
- [x] `shared/charting/style.py` (MA colors match the prose vocabulary; matplotlib is the repo's only non-stdlib dep, charts land in step D/E)
- [x] Runner: `shared/scripts/run_job.sh` (resolves claude CLI for launchd PATH, wall-clock timeout, alerts on every failure path, post-run artifact assertion)

**DoD:** hooks + gate + delivery proven on a synthetic report (deterministic test suite,
2026-07-20); live delivery smoke test blocked on `.env` (FRED_API_KEY, TELEGRAM_*, SMTP_*).

## Phase 1 — crypto-analyst/                            `status: steps A+B done ✅`

The KriptoVadász replacement. Benchmark corpus: 132 posts (Jan 2025 + Dec 2025 → Jul 2026),
18 weekly updates + 11 weekly PDF deep-dives + FOMC notes + event notes + altcoin/onchain posts.

- [x] **A. Corpus** — `corpus.jsonl` built (743K chars, 1 junk file skipped)
- [x] **B. Derive** — done via 4-agent corpus analysis → `templates/`: heti-piaci-update.md, event-note.md (FOMC/macro/geo/thematic/institutional), onchain-review.md, altcoin-screen.md, rubric.md (/100, publish gate ≥80), style-guide.md, prediction-ledger.md (schema + 41 graded KV calls seeded; KV baseline: 49% hit / 37% partial / 15% miss, misses never self-acknowledged — our bar: beat it symmetrically)
- [x] **B2. Doctrine** — `templates/analytical-doctrine.md`: his reasoning playbook
      (28 canonical patterns from 144 mined instances, full corpus), outcome-weighted
      by the graded ledger (ADOPT his proven level-confluence/positioning/decomposition
      families; EXTRA SKEPTICISM on his miss clusters: event-timelines, relayed official
      forecasts, nowcast-vs-print). Loaded by all analysts + composer; patterns cited
      by name in briefs so the fact-checker audits reasoning provenance. This is the
      "clone the mind" artifact — and the reusable core for Phases 2–4 + /elemzes.
- [x] **C. Wire** — skill `weekly-market-update` (full pipeline: verify → 4 parallel analyst briefs → compose → ledger → fact-check loop → editor score → gated delivery; `dry-run` mode = acceptance check, passed headless 2026-07-20); subagents macro/crypto/onchain/sentiment-analyst wired to cache files + section assignments; data manifests in sources.yaml; `ledger.jsonl` seeded via `seed_ledger.py` (42 benchmark calls — note: templates table has 14 partials vs 15 claimed in its own baseline line, flagged to tom). Later skills (`event-note`, `onchain-review`, `altcoin-screen`) follow the same pattern after E/F prove it.
- [x] **D. Data** — 14 fetchers implemented + live-tested 2026-07-20 (11 green, all
      schema-checked): binance_klines with the full indicator contract (MA50/100/150/200d,
      200w, Bollinger, RSI+RSI-MA daily+weekly, VWAP anchored at the TRUE 2022 cycle
      trough via 2-page kline history, POC + volume shelves — math proven by
      `test_indicators.py`), coingecko(+coinpaprika fallback), defillama (TVL+stablecoin
      w/w deltas), feargreed, binance_funding (funding+OI), fx_rates (ECB/frankfurter),
      mempool, etf_flows (farside scrape, T+1 placeholder-aware), gdpnow (official RSS —
      tool page is JS), fed_calendar (FOMC scrape, 55 meetings parsed), rss_news
      (DTD-rejecting stdlib parse), econ_calendar (FRED releases API — bls.gov blocks
      bots), cme_fedwatch (graceful-fail by design → relayed-via-news policy).
      **Blocked on tom:** `FRED_API_KEY` in `.env` (see `.env.example`) — fred is a
      required source, verify FAILs until then. sosovalue fallback needs its key (optional).
      *Known limit: pro-tier onchain (Glassnode/CryptoQuant) paywalled → free proxies,
      confidence labeled.*
- [ ] **E. First report** — current week's *heti piaci update*, Hungarian, full gate pass
- [ ] **F. Backtest** — regenerate 2–3 past weeks (as-of data from cache/corpus dates), rubric-score vs the real KV weeklies, iterate skills until ≥ parity
- [ ] **G. Operate** — Sunday 18:00 weekly run; FOMC/CPI event-notes triggered from econ calendar; Telegram + email; score trend + ledger review monthly

**Report cadence target:** weekly flagship + event-driven notes; expansion after F passes.

## Phase 2 — macro-analyst/                             `status: planned`

The "economy check": global macro weekly (Fed/ECB path, inflation prints, growth, USD, yields,
positioning) with a HU angle (MNB, HUF, energy) that KV doesn't cover.
Corpus: macro sections of Phase 1 corpus + public sources (Fed/ECB/MNB statements, FRED).
Data adds: ECB/MNB calendars, Eurostat/KSH, DXY/yield curves. Blueprint A–G apply.

## Phase 3 — portfolio-review/                          `status: planned`

Private monthly review of tom's actual holdings vs the market view from Phases 1–2:
allocation drift, scenario exposure, invalidation levels hit, rebalancing *scenarios*
(never advice-framed). Inputs: manual holdings file (or exchange CSV export later).
Highest privacy: this folder's data never leaves the repo; delivery = repo file only by default.

## Phase 4 — daily-pulse/                               `status: planned`

Short daily snapshot (5 bullets: overnight moves, today's calendar, sentiment, one chart,
one thing to watch) reusing Phase 1 fetchers entirely. Cheap by design; only built once
weekly quality is proven, so the daily habit inherits a validated pipeline.

## Backlog / ideas (unscheduled)

- `/elemzes "<question>"` ad-hoc analysis skill — apply the doctrine + cached data +
  fact-check discipline to ANY question tom asks, independent of report formats
  (the "use his mentality for my own questions" endpoint; build after E proves the pipeline)
- AMERIKAI PIAC [EXT] section needs an owner (macro-analyst is natural) + an equity
  index source (stooq or FRED SP500) + earnings-calendar policy before first monthly
- Bash-level curl allowlisting is best-effort by design (exotic quoting can evade);
  real egress control = fetchers + WebFetch hook. Revisit only if it bites.
- Altcoin deep-dive series as its own cadence (KV "Altcoin sorozat" equivalent)
- Web dashboard on homelab (reports.toomhorvath.com) with score trends + ledger
- English executive summaries (language practice mode)
- Quarterly "big picture" report (K-shaped economy style structural pieces)

## Status board

| Phase | Job | Status |
|---|---|---|
| 0 | foundation | 🟢 built + tested (pending: .env secrets, GitHub push decision) |
| 1 | crypto-analyst | 🟡 A+B+B2+C+D ✅ — next: E (first report; needs FRED_API_KEY in .env) |
| 2 | macro-analyst | ⚪ planned |
| 3 | portfolio-review | ⚪ planned |
| 4 | daily-pulse | ⚪ planned |

## Changelog

- 2026-07-20 — Plan created. Phase 0 partially done (.gitignore, ingest script, folder layout). Phase 1 step A complete: 132-post corpus extracted on-device to `crypto-analyst/corpus/corpus.jsonl`.
- 2026-07-20 — Phase 1 step B complete (in Cowork): 4 parallel agents analyzed the full corpus (flagship weeklies+PDFs, 52 event notes, summaries/alt/onchain, predictions). 7 foundation artifacts written to `crypto-analyst/templates/`. Handoff: continue in Claude Code with Phase 0 scaffold + Phase 1 step C ("Read PLAN.md and continue with the current phase").
- 2026-07-20 — Phase 1 step D (fetchers): 14 modules + indicators.py (tested math)
  live-run against real APIs; 11/14 green, remaining 3 are key-gated (FRED ×2) or
  policy-fail (FedWatch JS). Cache for 2026-07-20 populated. Fixes en route: VWAP
  anchor paginated to the real 2022 trough; GDPNow moved to its RSS; econ_calendar
  moved to FRED releases API (BLS 403s bots); farside T+1 placeholder excluded from
  week totals. `.env.example` added — tom: fill FRED_API_KEY to unblock step E.
- 2026-07-20 — Phase 1 step B2 (doctrine): mined all 8 corpus slices for reasoning
  patterns (144 instances, 64 indicators, 64 discipline rules; 8-agent workflow),
  synthesized in-session into `analytical-doctrine.md` (28 canonical patterns +
  Súlyozás verdicts from the graded ledger + "Miénk, nem az övé" deltas), wired into
  all 4 analysts + skill context-load. `/elemzes` ad-hoc skill added to backlog as
  the generalization endpoint.
- 2026-07-20 — Phase 0 scaffold + Phase 1 step C complete (Claude Code). Built: AGENTS.md/CLAUDE.md, 3 hooks + settings, sources.yaml (16 sources/4 manifests) + fetcher framework (coingecko live-tested), delivery (gate-checked), run_job.sh, weekly-market-update skill + 6 subagents, ledger.jsonl (42 benchmark calls). Verified: deterministic hook/gate/delivery test suite + headless skill dry-run (passed) + adversarial multi-lens review (31 findings raised, ~25 confirmed & fixed — incl. allowlist @-bypass, Stop-gate read-only false positive, headless-delivery permission block, HU magnitude-word lint gaps, missing fx_rates source; 2 rejected; rubric-A4 & [EXT]-section items → backlog). Next: step D fetchers, .env secrets, GitHub push decision.

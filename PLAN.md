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
- [x] **E. First report** — `reports/2026/2026-07-21-heti-piaci-update.md`, full pipeline
      (4 parallel analyst briefs → compose → 13 own ledger calls + 1 benchmark call graded
      (Schwab ✅, externally verified) → fact-checker 2 passes (6+2 findings, all fixed —
      incl. a real weekday error and 3 ledger-integrity catches) → editor **95.5/100 PASS**
      (residue: length over band, missing Érdekesség/self-Q&A voice devices, hyphenation
      sweep — fixes queued in the score sidecar for issue #2). Delivery pending channel
      secrets (TELEGRAM_*/SMTP_ in .env).
- [x] **F. Backtest** — 3 of 3 weeks done. Full-rubric totals ours vs benchmark:
      07-05 **87.5**/47.0, 03-15 **84.5**/67.0, 05-17 **93.0**/35.5.
      **Parity metric (category C, the only section no benchmark-gap item touches):
      ours 17 / 17 / 17, theirs 14 / 20 / 8 — we win two of three, average 17.0 vs 14.0.**
      The verdict is "we clear the bar on average, and the benchmark is wildly
      non-uniform" — its C ranges 8 to 20 across three posts, so no single week
      supports a general claim in either direction. Our own C is flat at 17 all three
      weeks, and the blocker is the same every time: the ONCHAIN section has no onchain
      data (C2 = 3/6 in all three). **That single infrastructure gap is the whole
      remaining analytical delta** — see the coingecko/mempool/OI backlog item.
      Step F also paid for itself in bugs found: the corpus-truncation fix (07-05),
      five process findings (03-15), and a falsified rubric arithmetic claim (05-17).
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
- etf_flows fetcher: emit `prev_week_total_musd` (summed in code) so reports can cite
  the w/w comparison without reasoning-plane arithmetic (fact-checker F4, 2026-07-21)
- **Editorial rulings die with their sidecar → they regress.** The 03-15 backtest
  re-introduced three defects the 07-05 issue had settled (ASCII closing quotes,
  `Tripwire`, `relayed`), because those rulings were recorded only in a `.score.json`
  no later composing session reads. Action: a "settled terms & typography" section in
  `style-guide.md` that skill step 1 loads, so decisions bind future runs. Note the
  editor itself mislabeled `Tripwire` as a restored 07-05 ruling when 07-05 had
  actually resolved it by deletion — it self-corrected on challenge, but an unchecked
  "re-apply the precedent" instruction would have entered an invention into the house
  vocabulary. Found by step-F backtest 2026-03-15.
- **report_lint.py does not check Hungarian quote pairing.** F2 is a zero-tolerance
  rubric item, yet 20 opening `„` against 0 closing `”` survived compose + lint and was
  caught only by the editor grepping by hand — costing the gate a full cycle. A pair
  check is a few lines and would make the most mechanical F2 defect impossible to ship.
  **Add a second warn-level check in the same pass: nonstandard two-element hyphenation**
  (regex over lowercase-hyphen-lowercase tokens, excluding 3+ element compounds over six
  syllables and anything with a foreign or proper-noun element). The 03-15 run burned
  two full edit rounds on hand-sampled compound lists that were each presented as closed
  and each turned out to be a sample — ~25 sites still remained after nine fixes
  (`makró-ténye`, `dollár-alapú`, `évjárat-műtermék`, `konfluencia-távolságok`, …).
  A hand-sample is the wrong instrument for a zero-tolerance item; the lint is the right
  one. Found by step-F backtest 2026-03-15.
- **quality_gate.py sidecar parse errors are undiagnosable.** Blocked twice in one run
  with only `char 11702` / `char 14530`; the real cause both times was an editor evidence
  string quoting report prose whose `„…"` closer terminated the JSON value early. Two
  fixes, both cheap: have the gate print the offending line's `"id"` and surrounding
  text, and have the editor emit inner quotes as `„ ”` (or escaped) — the failure mode is
  structural, since the editor's job is to quote Hungarian into JSON. Found 2026-03-15.
- ~~**report_lint staleness warnings misfire in backtest mode.**~~ **FIXED** — verified
  2026-07-21 during the 05-17 backtest: `report_lint.py:163-169` now derives the freshness
  reference date from the report filename, falling back to today only when the filename
  carries no parseable date. Backtest staleness warnings are now correct and actionable
  (the 05-17 run's warnings were all genuine and were labeled in prose).
- **The compound-hyphenation sweep needs a capitalised first element.** The 05-17 run
  used `[a-z]{3,}-[a-z]{3,}` and reported clean; the editor then found two survivors
  (`Sávhatár-szabály`, `Motorháztető-elv`) that the regex *structurally could not see*
  because sentence position or bold markup capitalises the first element. This is the
  same failure mode as the 03-15 hand-sampling item one level up: an instrument that
  reports clean because it cannot see the defect class. When the F2 pair check goes into
  `report_lint.py`, the hyphenation half must allow `[A-ZÁÉÍÓÖŐÚÜŰ]?` on the first element.
- **Settled terms & typography (the style-guide section 03-15 asked for — seed it with
  these).** Rulings made and applied in the 05-17 run, currently recorded only in a
  sidecar and therefore at risk of regressing again: solid `motorháztetőelv`,
  `retorikadiszkont`, `sávhatárszabály`, `konfluenciaszabály` (AkH 139 — hyphen only
  *above* six syllables, so exactly-six compounds are solid); hyphen retained only for
  proper-noun (`Bollinger-középvonal`, AkH 168) and unassimilated foreign
  (`chokepoint-aritmetika`, AkH 138) elements. Use `adatközlés`, never `nyomtatás`, for
  a data release — the calque reads as physical printing in Hungarian. Open for tom:
  pick one house term for `bérpapír` vs `payroll` across the series.
- **Spurious subject–predicate comma appears in all three benchmark posts scored** and
  has crept into ours. Warrants a one-line house style rule rather than a per-run fix.
- **The "known benchmark gaps" item list does not sum to 34.5.** Both prior sidecars
  quote 34.5 pts for A1/A6/B3/D3/D4/E1–E3/F2; the 05-17 editor recomputed 30 and recorded
  the discrepancy rather than inheriting it. Since this number is the load-bearing caveat
  on every parity claim we make, resolve it with tom before the figure is quoted again.
- **B5 length is now structural, not stylistic.** The 05-17 report hit ~3,500 words
  against a 700–900 band even after deliberate tightening, and ~580 of those words are
  the prediction table alone, because machine-checkable resolution criteria are written
  as prose inside table cells. The benchmark clears this band at ~950 words. Either the
  template's band is wrong for a report carrying our accountability apparatus, or the
  apparatus needs a compact notation — a decision for tom, not another editor round.
- binance_klines / defillama fetchers: emit derived gap widths (level-to-level spans) and
  the stablecoin non-USDC/USDT residual, so confluence distances and share splits stop
  being reasoning-plane arithmetic carrying a bare cache tag (fact-checker F3/F4, 03-15)
- **Step B/B2 artifacts were derived from a truncated corpus.** The 07-05 backtest found
  and fixed the ingest bug (base64 images exhausted the 700K parse window): 58 of 132
  records recovered a combined 255K chars — mostly post TAILS (BITCOIN closings, polls,
  disclaimers, exactly the template-critical sections). Templates, rubric, and the
  doctrine were mined from the truncated text. Action (with tom): a delta-pass over the
  recovered text to check for missed patterns/ritual formulas before step F concludes.
- **net_allowlist.py does not gate WebSearch** — `extract_hosts()` handles WebFetch and
  Bash only, so analysts can cite any domain reached via search while the hook stays
  silent. Both the 07-21 live report (axios/cnn/cnbc/kslaw) and the 07-05 backtest
  (aljazeera/cnbc/cnn/fortune/worldoil) shipped tags for unregistered domains. Decide:
  extend the hook to WebSearch results, or register a small vetted news tier
  (reuters/apnews are registered but block the crawler — that is the reason analysts
  drift to unregistered outlets). Found by step-F backtest 2026-07-05.
- **Geopolitics has no usable registered source.** reuters.com and apnews.com are in
  `extra_allowed_domains` but refuse the fetcher (HTTP 400 / robots), so the
  VILÁG/GEOPOLITIKA section has no primary wire in any run. Needs either a working wire
  source or an explicit "geo runs on cache + declared gaps" policy.
- Oil/energy + chokepoint data has no registered source at all (no Brent/WTI level, no
  tanker-transit series) — doctrine patterns 26/27 cannot be run on sourced numbers.
  Candidate: EIA or a FRED oil series (DCOILBRENTEU) — cheap, registry-clean.
- **Backtest hazard: live ticker widgets.** Fetching an archived article returns
  price widgets rendered at fetch time, not publication time (07-05 run: a "$66,423"
  and a "$66,313.26" both leaked from 06-29/07-03 pages). Analysts caught these, but
  the rule belongs in the agent briefs: in backtests, prices come from cache ONLY.
- econ_calendar carries dates without release times, so the weekly calendar cannot
  give the rubric's "weekday + CET time" without inventing the clock (rubric B-4 point
  forfeited honestly in the 07-05 backtest). Add times to the fetcher.
- **rubric.md:68 is half-falsified.** "No alt depth (ETH had no dedicated TA) → we add
  an ETH block + TOTAL3" — the 2026-07-05 benchmark post carries genuine weekly TOTAL3
  TA (200w MA, February low, RSI, trend structure). The TOTAL3 half of that claim is
  false and should stop being advertised as our differentiator; the ETH half survives
  (ETH appears only as a stagnant reserve line). Rubric revision, made with tom.
- **Parity metric needs rethinking.** Rubric items A1/A6/B3/D3/D4/E1–E3/F2 total 34.5
  pts and ARE the six "known benchmark gaps we must BEAT" (rubric.md:63-69) — the rubric
  was written from this corpus. Scoring the benchmark with it grades them on an exam
  written from their own marked-up essay. Category C (depth/mechanism) is the only
  section no benchmark-gap item touches: ours 17 vs theirs 14. Treat C (or C+D1/D2) as
  the real analytical parity metric, the full total as a compliance metric.
- scores.jsonl has no way to distinguish our reports from benchmark scores, and no
  revision field — a benchmark row would pollute the 3-report-decline trend monitor,
  and a re-scored report either double-counts or loses its audit trail. Add a
  `kind`/`revision` discriminator before the parity series grows.
- Template gaps found by the 07-05 parity run: sector rotation is `[EXT]`-only but
  carried a weekly thesis in the benchmark (promote to weekly); no slot for a
  methodology-limits caveat ("rotation makes index TA unreliable"); MAKRÓ is US-only
  so Eurozone CPI/ECB has nowhere to go (real gap for an EU reader); earnings horizon
  is one week only; no standing commodity slot (oil only lives under geopolitics); no
  trading-calendar/holiday note slot.
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
| 1 | crypto-analyst | 🟢 A+B+B2+C+D+E+F ✅ (F 3/3: 87.5/47.0, 84.5/67.0, 93.0/35.5; **category C avg 17.0 vs 14.0 — bar cleared**) — next: step G (schedule + delivery + monitoring) |
| 2 | macro-analyst | ⚪ planned |
| 3 | portfolio-review | ⚪ planned |
| 4 | daily-pulse | ⚪ planned |

## Changelog

- 2026-07-21 — Phase 1 step F **complete**, backtest week 3 of 3 (2026-05-17, a grinding
  deterioration week: BTC rejected at a four-tool 81 782,66–82 981,80 confluence band and
  sitting on its 150-day MA, ETH's weekly close below its 200-week MA, CPI re-accelerating
  3,29→3,78% while payrolls halved 185k→115k, ~1 Mrd USD of BTC ETF outflow against flat
  funding). Ours **93.0** (A 22.5 / B 18.5 / C 17 / D 15 / E 10 / F 10) — our best of the
  three. Benchmark weekly update scored **35.5**. NO live-ledger writes (67 records
  unchanged), no PDF, no delivery — backtest rules held.
  **Category C, the honest parity metric: ours 17 vs theirs 8 — reversing the 03-15 loss
  and closing step F at 17.0 vs 14.0 on average across the three weeks.** The benchmark's
  C of 8 / 14 / 20 across three posts is the real headline: the corpus is non-uniform, and
  any single-week parity claim (in either direction) is noise. Ours is flat at 17 all
  three weeks, blocked every time by the same thing — C2 = 3/6, because the ONCHAIN
  section has no onchain data. That is now the entire remaining analytical gap.
  Two places the benchmark genuinely beat us, recorded without softening: it clears the
  700–900 word band at ~950 words where we ran ~3,500, and it ran four triangulation legs
  (whale cohorts, per-asset ETF reserves across BTC/ETH/SOL/XRP, a per-issuer Morgan
  Stanley line, macro) to our two. Both are data-plane gaps on our side, not writing.
  Pipeline notes: fact-checker took **seven rounds** to PASS (18 → 11 → 15 → 6 → 3 → 1 → 0
  findings), the most adversarial run of the series and the most valuable — it caught an
  inverted ETH VWAP relation, a Strategy cost-basis level described two contradictory ways
  in two sections, a load-bearing CPI-internals claim tagged to `bls.gov` that the registry
  itself says is unfetchable (an AGENTS.md reproducibility violation), a KOMMENTÁR argument
  resting on a yield move that postdated the print it claimed to explain, and a prediction
  row that survived **four** rewrites before it could actually fail. The editor then caught
  that our own compound sweep was structurally blind to capitalised first elements, and
  recomputed the long-quoted "34.5 pts of known-gap items" as 30. Six process findings
  added to backlog; one prior backlog item (backtest staleness warnings) verified fixed.
- 2026-07-20 — Plan created. Phase 0 partially done (.gitignore, ingest script, folder layout). Phase 1 step A complete: 132-post corpus extracted on-device to `crypto-analyst/corpus/corpus.jsonl`.
- 2026-07-20 — Phase 1 step B complete (in Cowork): 4 parallel agents analyzed the full corpus (flagship weeklies+PDFs, 52 event notes, summaries/alt/onchain, predictions). 7 foundation artifacts written to `crypto-analyst/templates/`. Handoff: continue in Claude Code with Phase 0 scaffold + Phase 1 step C ("Read PLAN.md and continue with the current phase").
- 2026-07-21 — Phase 1 step E: first real weekly report through the full gate, 95.5/100.
- 2026-07-21 — Phase 1 step F, backtest week 1 of 3 (2026-07-05). Report scored **87.5** (A 20.5 / B 16.5 / C 17 / D 15 / E 10 / F 8.5) after 4 adversarial fact-check rounds + 2 editor passes; benchmark post scored **47.0** with the same rubric. NO live-ledger writes (backtest rule held; ledger unchanged at 67 records). Honest caveat: 34.5 of the 40.5-pt gap sits in rubric items that ARE the enumerated "benchmark gaps we must beat" — category C (ours 17 vs 14) is the only uncontaminated analytical comparison. **Bug fixed mid-run:** `ingest_examples.py` fed the parser a fixed 700k-char window, so a single inline base64 image truncated the post body — 120 of 132 corpus records were at risk, and the 07-05 benchmark record was cut mid-BITCOIN-section. Base64 payloads are now stripped before the feed; both shards re-extracted, corpus re-merged (132 records, 998,256 chars). Corpus scoring before this fix would have been ~30 pts of artifact against the benchmark.
  Pipeline behaved as designed: lint blocked one naked number mid-compose; fact-checker
  failed the first pass (weekday error, ledger claim_verbatim integrity, derived-sum
  flag, 2 more) and passed the re-check; editor scored honestly with itemized evidence.
  Ledger: +13 own calls with deadlines (first due 2026-07-23), Schwab benchmark call
  graded ✅ hit (launched 05-13, verified externally). Delivery awaits TELEGRAM_*/SMTP_*.
- 2026-07-21 — Phase 1 step F, backtest week 2 of 3 (2026-03-15), resumed after an API
  drop mid-pipeline (draft existed, no sidecars; restarted at step 5). Report scored
  **84.5** (A 22.5 / B 15 / C 17 / D 15 / E 8 / F 7); benchmark PDF deep-dive scored
  **67.0**. NO live-ledger writes, no PDF, no delivery (backtest rules held).
  **The headline total is misleading and the sidecar says so:** our +17.5 is +12 in
  category A and +5 in E — the two categories the benchmark is not attempting and cannot
  structurally reach. On the four contested categories (B+C+D+F) it is 54.0 vs 53.5, a
  tie. **The benchmark WINS the parity metric, category C, 20 vs 17**, and also wins B
  (16.5-15). Why: it uses disanalogy as section architecture rather than disclosure,
  runs four genuine onchain legs (our ONCHAIN section has no onchain data — C2 3/6), and
  wires one mechanism (Hormuz → crude → inflation → rate curve → BTC) across four
  sections without repeating it. Two losses are on things we fully control: length
  (~6,500 words vs their ~1,800, B5 = 0) and calendar clock times (B2 2/4).
  **Rubric assumption falsified:** known-gap #2 (`rubric.md:63-69`, "benchmark never
  grades its misses") is wrong for this post — it grades its poll with checkable
  reasoning and carries a full Bszt + MiCA disclaimer. Do not generalize the gap list
  from 07-05. **Open rubric question for tom:** category C scored 20/20 with a real
  weakness present (peripheral index recital, an unchained "US sentiment feeds back into
  crypto" premise) — the C items don't discriminate at the top of the range. If C is the
  parity metric, it needs a harder top rung. Rubric untouched by the run, per AGENTS.md.
  Pipeline notes: fact-checker PASS in 2 rounds (0 block, as-of discipline clean —
  every citation ≤ 03-15, all 16 HIÁNYZÓ ADAT claims verified as genuinely missing);
  editor caught a 3-defect regression of rulings settled in 07-05; the Stop gate blocked
  twice on editor-written sidecars that were invalid JSON. 07-05 (87.5) vs 03-15 (84.5)
  is **not** a trend — two points, and the delta hides that 03-15 is the stronger
  sourcing performance (A 90%, A3 4 vs 2) and the weaker editorial one (B5 0 vs 1.5,
  E1 2 vs 4). Five process findings added to backlog.
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

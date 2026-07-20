# Prediction ledger

Purpose: every forward-looking statement — ours and the benchmark's — is logged, given a
deadline and resolution criteria, and graded. This is what makes "quality" honest.
Machine copy lives at `crypto-analyst/ledger.jsonl` (one JSON object per call, schema below);
this file holds the schema, grading rules, and the human-readable seed.

## Schema (per call)

| field | notes |
|---|---|
| call_id | `YYYY-MM-DD-nn` |
| publish_date / source_post | link back — enables "múlt heti anyag" continuity |
| asset_topic | BTC / ETH / S&P / macro-series / reg / geo … (instrument granularity!) |
| call_type | `level-range` \| `direction` \| `conditional-scenario` \| `event-timeline` \| `data-reinterpretation` \| `risk-flag` \| `position` |
| claim_verbatim + claim_normalized | HU quote + one-sentence EN |
| levels | exact numbers (what made benchmark calls gradeable) |
| trigger_condition / invalidation_level | separate fields; condition-unmet ≠ miss |
| deadline | HARD date. "a következő hetekben" is not a deadline. Vague = `expired-vague` at +30d |
| own_vs_relayed | relayed plans/consensus (Balchunas, Goldman, CME odds) graded separately |
| stated_confidence | low/med/high from hedge language + any cited odds (whose) |
| position_taken | bool + note — skin-in-the-game rows rank highest |
| resolution_criteria | pre-registered measurable test ("weekly close > 150d MA by DATE") |
| outcome | `hit` \| `miss` \| `partial` \| `condition-unmet` \| `unresolved` \| `expired-vague` |
| outcome_evidence + graded_on | data/post + date |
| self_review | did the report acknowledge the outcome? (enforces symmetry) |
| band_definition | for poll-range calls: the named anchors defining each band |

## Grading rules
1. Grade at deadline, in the next scheduled report — hits AND misses named in prose.
2. Conditional calls whose condition never fired → `condition-unmet` (not miss).
3. Relayed calls tally separately (they measure curation, not analysis).
4. Monthly recap: hit-rate by call_type, "Tévedtünk / Igazunk lett" section.
5. Target to beat (benchmark baseline below): >52% hit, <16% miss on own calls, AND
   0 silent misses (benchmark had many — every KV miss below vanished from his posts).

## Benchmark baseline (KriptoVadász, Jan–Jul 2026, N=50 graded)
**✅ 26 hits (52%) · ➖ 16 partial (32%) · ❌ 8 miss (16%)** (+3 unresolved, 1 in-table
expired-vague; outcome symbols: ✅ hit · ➖ partial · ❌ miss · ? unresolved · ⌛ expired-vague)
Pattern: level/roadmap calls near-flawless (65,500 support hit exactly; FVG-fill scenarios
played out); data-reinterpretations strong (GDP-import arithmetic, PCE peak); misses cluster
in event-timeline calls (Clarity Act ×2), relayed direction under geopolitics (oil
normalization), nowcast-vs-print and relayed official inflation/growth forecasts (Lutnick
>5% GDP, Bessent mid-year disinflation). He credits hits ("ahogy számoltunk vele") — the
audit confirmed explicit self-acknowledgment on several (06-16 Fed pair, 06-19 semis) —
but **all 8 misses vanished silently**; community poll graded only when right.

**Audit note (2026-07-20).** Full-corpus re-extraction (7 agents, month-sliced) reconciled
against the step B table: (1) the originally published 20/15/6 (N=41) line was arithmetically
right and the table had DROPPED one graded partial — the 02-03 Morgan Stanley approval-timing
call, restored below; (2) 12 further corpus-verified gradeable calls were absent (6 hit,
3 partial incl. the MS row, 2 miss, 1 unresolved) — all restored below with evidence;
(3) the 01-02 "post-down-year catch-up (vague)" row is regraded ➖→⌛ per this file's own
rule ("vague = expired-vague at +30d") and excluded from graded N.

## Seed entries (extracted from corpus)

| date | topic | call (EN, condensed) | type | outcome | evidence |
|---|---|---|---|---|---|
| 01-02 | BTC | Post-down-year catch-up plausible if macro cooperates (vague) | direction | ⌛ | regraded per vague-deadline rule (audit 07-20); was ➖ |
| 01-09 | BTC | Channel resistance (from Sunday analysis) caps price | level | ✅ | hit + ETF outflows 01-09 |
| 01-16 | BTC | Dip changes nothing — ascending channel intact | direction | ❌ | $1.8B liq cascade 02-06 |
| 01-16 | reg | Clarity Act revote in 2–3 weeks (relayed) | event | ❌ | stuck in Senate 07-05 |
| 01-20 | silver | Crowded silver longs + $125/oz option bets = correction risk (relayed) | risk-flag | ✅ | record early-Feb devaluation; −50% from peak by June |
| 01-21 | GDP | Lutnick (Davos): >5% US growth for Q1 (relayed) | level | ❌ | Q1 visible slowdown, Q4 revised to 0.7%; silently dropped |
| 01-23 | BTC | 100d MA reclaim easier "in coming weeks" | direction | ❌ | 02-06 crash instead |
| 01-28 | CPI | Powell: inflation eases in middle quarters, ~June (relayed) | event | ➖ | May war spike (PCE 4.1%) but June printed −0.4% m/m |
| 02-01 | BTC | Binance $1B BTC buy within 30d, stabilization program (relayed) | event | ➖ | tranches executed Feb (~$435M + 3rd); full $1B unconfirmed |
| 02-01 | JPY | If Takaichi majority Feb 8 → yen weakens anew (relayed Watanabe) | cond-scenario | ✅ | landslide 02-08; April intervention temporary; 40-yr low 07 |
| 02-03 | ETF | MS spot BTC ETF approval "as early as March", 75-day process (relayed) | event | ➖ | launched 04-08/12 — substance right, ~2 weeks late. *The dropped 15th partial* |
| 02-06 | BTC/ETH/SOL | **Position**: bought the 60–65k dip (200w MA, wRSI~30); overhead supply flagged | position | ➖ | >80k by 05-17; 58.2k undercut 07-05 |
| 02-17 | CPI | Bessent: marked inflation drop by mid-year (relayed, + Truflation gap) | event | ❌ | May PCE 4.1%, June CPI 3.5% vs 2.4% at call; silently dropped |
| 02-13 | BTC | At −50% (hist. max −75%), decline nearer end than beginning | direction | ➖ | Feb low held until marginal undercut |
| 02-20 | GDP | Weak Q4 GDP backward-looking/distorted | data-reint | ✅ | shutdown revision; Q2 GDPNow 3–4.3% |
| 02-25 | macro | Flat 10% tariff ≈ tax cut → disinflation + sector refuel | scenario | ➖ | PMI 4-yr highs ✅; war CPI spike ❌ |
| 03-13 | politics | War cost → sentiment/approval pressure to settle | scenario | ✅ | record-low Michigan; 04-12 diplomacy |
| 03-22 | BTC | Roadmap: 50d reclaim #1; if channel lost → 65,500 → 62,600 → 60,500 VWAP | cond-scenario | ✅ | fell exactly to 65,500 (03-29) |
| 03-27 | S&P | Pattern echo: bottom ~1–1.5w after failed 200d reclaim | direction | ✅ | ceasefire flip 04-08; ATH 04-24 |
| 03-27 | geo | Rubio "war over in 1–2 weeks" fits seasonality window | event | ➖ | 2-week ceasefire, then resumed |
| 03-29 | ETF | MS ETF launch ~2 weeks (relayed Balchunas) | event | ✅ | launched 04-08/12 |
| 03-29 | BTC | If weekly trend support lost → air down to ~60k (CBD zone) | cond-scenario | ✅ | triggered June → 58,189 (07-05) |
| 04-05 | GDP | GDP dip = import/statistical, optimistic path if AI capex lands | data-reint | ✅ | GDPNow 3→4.3% (05) |
| 04-05 | adoption | Schwab Crypto (spot BTC/ETH) launch before end-Q2 (relayed) | event | ? | deadline passed, corpus silent — verify externally |
| 04-05 | BTC | Coiling wedge + fading volume = breakout setup (no direction) | risk-flag | ➖ | upside break 04-12 |
| 04-12 | BTC | Strategy STRC raise (~9,173 BTC) = buy pressure if converted | cond-scenario | ✅ | rally into mid-May |
| 04-12 | ETF | MS ETH + SOL ETFs "soon" (relayed) | event | ➖ | SOL S-1 06-28; ETH no |
| 04-19 | BTC | Crowded shorts + negative funding often contra-signal | direction | ✅ | reclaimed 50/150d → 200d |
| 04-24 | Fed | Consensus "no cut to Dec" could be wrong IF Warsh + Mideast calm | cond-scenario | ➖ | condition failed (re-escalation) |
| 04-24 | equities | At ATH with broad beats — ride fundamentals over TA | direction | ✅ | 8w win streak, Dow ATH |
| 04-26 | Fed | Next FOMC = non-event (no SEP, hold priced) | event | ✅ | passed quietly 05-03 |
| 04-26 | BTC | Key: reclaim+hold 150d (hist. → sharp rises) else blue channel | cond-scenario | ✅ | reclaimed; 150d became support |
| 05-03 | CPI | Real-time measures → April inflation slowed | data-reint | ❌ | printed above consensus |
| 05-03 | BTC | Bearish divergence noted but subordinated to key levels | risk-flag | ➖ | June collapse vindicated it |
| 05-07 | geo/eq | Peace = booster short-term; durable deal → yields normalize | scenario | ➖ | headlines lifted ✅; no durable peace |
| 05-10 | reg | Clarity Act Senate vote possible June (relayed) | event | ❌ | still stuck 07-05 |
| 05-10 | BTC | STH-basis reclaim bullish BUT 200d MA = bull/bear divide | level | ➖ | 200d rejected exactly |
| 05-15 | equities | Hindenburg omen "often false alarm", K-divergence read | data-reint | ✅ | no crash; ATH streak |
| 05-22 | macro/AI | Sulfur scarcity = underrated input-inflation risk | risk-flag | ? | unresolved |
| 05-29 | equities | SpaceX IPO in ~2 weeks (relayed) | event | ✅ | IPO wk 06-12, +10% d1 |
| 05-31 | BTC | Channel support loss → FVG/air-pocket below gets filled | cond-scenario | ✅ | 06-07 filled; 200w briefly broken |
| 06-04 | BTC | Longs adding into decline (funding up) = cascade risk | risk-flag | ✅ | flush to 58,189 |
| 06-07 | Fed | Key risk: FOMC in 2w stricter than priced | scenario | ✅ | dot plot leaned to a hike 06-21 |
| 06-14 | geo | Peace framework signable this week; 60-day window = fragile | event | ➖ | signed 06-21; collapsed 07-12 |
| 06-16 | Fed | Tomorrow's FOMC revises the annual inflation forecast upward | direction | ✅ | SEP raised; self-acknowledged 06-17/06-19 |
| 06-16 | Fed | The ~10bp cut penciled in the March SEP gets dropped | direction | ✅ | dot plot leaned to a hike 06-21 |
| 06-18 | USD | SocGen (Groen): long USD on US resilience (relayed) | direction | ✅ | dollar strength held into July |
| 06-19 | semis | Record-crowded long-semis trade = correction risk (relayed) | risk-flag | ✅ | software/AI sell-off; self-acknowledged 07-08 |
| 06-21 | BTC | Map: hold rising support → sideways escape; danger = Feb low; proof = >67,500 POC | cond-scenario | ➖ | Feb low briefly lost, reclaimed; 67.5k not taken |
| 06-28 | PCE | PCE likely peaked (oil down since May) | data-reint | ✅ | June CPI −0.4% m/m (07-19) |
| 06-28 | GDP | GDPNow plunge statistical, not consumer collapse | data-reint | ✅ | components + rebound 07-19 |
| 07-05 | oil | OPEC+ increases → further oil normalization | direction | ❌ | WTI +13% to $81+ (07-19) |
| 07-08 | BTC | Trend health needs zone reclaim; RSI support intact | level | ➖ | weekly break ✅, daily resistances held |
| 07-19 | CPI | June relief may be one-off; July may show energy shock return | scenario | ? | beyond corpus |

*(3 further vague sentiment calls remain deliberately omitted as `expired-vague` — they
carry no testable content at all. The machine copy is `crypto-analyst/ledger.jsonl`,
regenerated from THIS table by `python3 shared/scripts/seed_ledger.py`; the script prints
the graded N and hit/partial/miss split, so table and ledger can never silently diverge
again. Table is the source of truth — edit here, then re-run the script.)*

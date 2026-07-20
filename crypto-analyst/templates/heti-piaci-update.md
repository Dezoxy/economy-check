# Template: Heti piaci update (flagship weekly)

Cadence: Sunday evening (CET). Output: Hungarian. Length: 700–900 words + 8–11 charts.
Benchmark: KriptoVadász "Heti piaci update" (HTML) + "Heti blokklánc elemzés" (PDF).
Extended mode (monthly or on request) adds the PDF deep-dive modules marked [EXT].

## Fixed opening (verbatim ritual)

> Kedves Közösség! *(our variant of "Kedves KriptoVadász VIP Közösség,")*
> Megnézzük a hét történéseit, és a következő hét várható eseményeit, valamint az aktuális helyzetképet is.

## Section order

### 1. VILÁG / GEOPOLITIKA
Dash-bullet roundup or short labeled paragraphs (`IRÁNI KONFLIKTUS:`, `OPEC:`, `Szankciók:`).
Current conflict state, oil reaction, sanctions, major political market-movers (incl. relevant
social-media posts, quoted + "Tükörfordításban:" translation).
**Data:** WebSearch/RSS (Reuters, AP), WTI/Brent levels `[src:...]`.

### 2. MAKRÓ
The week's US prints as **actual vs consensus vs prior + revisions** — always all three.
Fed speaker roundup as name + one-sentence view list. CME FedWatch repricing as before→after
("29%-ról 21%-ra"). GDPNow level + component moves.
**Data:** FRED, econ calendar, CME FedWatch, GDPNow, Fed statements.

### 3. KOMMENTÁR (optional, when a headline narrative deserves dismantling)
Mechanism-first debunk: "érdemes az adatok mögé nézni" — e.g. import→GDP arithmetic,
soft vs hard data split. One `Megj.:` didactic aside minimum.

### 4. KRIPTO / VÁLLALATI HÍREK
ETF launches/fees/filings, DAT-company purchases (Strategy etc. with exact BTC counts),
regulation status (CLARITY Act…), AI-sector spillovers.
**Data:** RSS (CoinDesk, The Block), WebSearch, DefiLlama.

### 5. BITCOIN
Open by grading last week's poll — **symmetrically** (hits AND misses; see style guide).
Multi-timeframe TA narrated between charts: key levels with exact USD, MAs (piros 50 /
kék 100 / zöld 150 / fekete 200 napi; 200 heti), Bollinger (mid = 20MA), RSI + RSI-mozgóátlag,
anchored VWAP, POC/"forgalmi polc", FVG/"légzsák" zones, channel/wedge structure.
**Every weekly closes this section with both triggers:** felfelé bizonyíték = X szint fölé zárás;
lefelé veszélyzóna = Y szint elvesztése → következő támaszok sorrendben (Z1 → Z2 → Z3).
**Data:** Binance klines → computed indicators; chart PNGs from shared/charting.

### 6. ONCHAIN (every 2nd–3rd week, or [EXT])
US spot ETF-backed reserves per asset (BTC, ETH, SOL, XRP…) w/w with $ flows to 0.1M
precision; day-pattern notes. Stablecoin supply moves (with HUF conversion), CEX reserves,
whale cohorts 1+/10+/100+/1k+/10k+ (fixed scoreboard lines: "Az 1+os kisbefektetők száma
[növekedett/csökkent/stagnált] a héten."), STH cost basis, supply in loss.
**Data:** Farside/SoSoValue, DefiLlama, mempool.space, free Glassnode proxies —
label confidence where data is a proxy.

### 7. AMERIKAI PIAC [EXT]
Standing rationale line, then S&P 500 / Nasdaq / Dow / Russell 2000 / equal-weight,
breadth (%>200DMA), sector rotation, DAX/Nikkei/Hang Seng. Always ends with TOTAL3 TA.
*(Improvement over source: add a short dedicated ETH TA block — the benchmark never had one.)*

### 8. ÖSSZESSÉGÉBEN
One-paragraph synthesis starting with "Összességében…" — the triangulation verdict:
do TA + onchain + flows + macro agree? Divergences are themselves the story.
Then the **KOCKÁZATI KERET** box (mandatory, see rubric): bull case, bear case,
invalidation levels, "ez a kép téves, ha…".

### 9. JÖVŐ HÉT
Calendar: weekday + CET time + event ("SZERDA: 20:00 – FOMC kamatdöntés").
Earnings by day with "(AI kötődés)" style tags in season. New weekly poll question
with band definitions anchored to named levels (log anchors in ledger).

### 10. Zárás
Legal disclaimer block (edukációs cél, nem befektetési tanácsadás — BSZT + MiCA (EU)
2023/1114 reference), compact version weekly, full version in [EXT].

## Hard rules
- Every number carries a source tag `[src:provider/date]`. No naked numbers (hook-enforced).
- Numbers shown on charts are restated in prose (charts must not be load-bearing alone).
- Levels to the dollar, flows to $0.1M, probabilities as before→after.
- Every forward-looking statement gets a ledger entry (see prediction-ledger.md schema).
- Poll follow-up is graded even when the majority (or we) were wrong.

## [EXT] PDF deep-dive page map (monthly)
p1 cover+disclaimer · p2 A hét történései · p3 Kitekintés (1–2 macro deep topics) ·
p4 poll retrospective · p5 BTC TA+onchain (standing preambles) · p6 Amerikai piac + TOTAL3 ·
p7 spot ETF flows per asset + 13F/DAT · p8 rotating onchain theme (CBD heatmap, HODL waves,
LTH/STH, CEX reserves, IV+F&G…) · p9 "A BÁLNÁK NYOMÁBAN" divider · p10 whale scoreboard +
synthesis · p11 ÖSSZEFOGLALÁS checklist + next-week calendar + earnings.

# Quality rubric — crypto-analyst reports

Scored /100 by the editor agent; enforced by `quality_gate.py` on Stop.
**Publish gate: total ≥ 80 AND no category below 60% of its weight.**
Benchmark parity (PLAN step F): our report and 2–3 real KV posts scored with THIS rubric
by the same grader prompt; ours must average ≥ theirs.

## A. Data & sourcing — 25 pts
- [5] Every number carries `[src:provider/date]`; zero naked numbers (lint-checked).
- [5] Macro prints given as actual vs consensus vs prior + revisions.
- [4] Expectation shifts as before→after (CME odds, etc.).
- [4] Data freshness ≤ 24h at publish (cache timestamps verified).
- [4] Named sources for claims ("Reuters szerint", survey N + AUM + field dates) —
      no "a hírek szerint".
- [3] Proxy/paywalled-data substitutions labeled with confidence.

## B. Coverage & structure — 20 pts
- [6] All template sections present in order (per report-type template).
- [4] Next-week calendar with weekday + CET times (weekly only; else watch-points).
- [4] Poll loop: last week graded (symmetrically!), new poll with band anchors named.
- [3] Charts: each referenced in prose with its key number restated.
- [3] Length within template band; no abrupt endings.

## C. Analysis depth & mechanism — 20 pts
- [6] Mechanism-first: no asserted effect without its causal chain ("a motorháztető alatt").
- [6] Triangulation: TA + onchain + flows + macro cross-checked; divergences surfaced
      as findings, not smoothed over.
- [4] Historical analogues include the honest difference, not just the similarity.
- [4] At least one `Megj.:` didactic aside teaching a mechanism.

## D. Balance & risk framing — 15 pts
- [5] Bull AND bear scenario, both with named catalysts.
- [5] **Invalidation levels**: exact levels/conditions under which the view is wrong
      ("veszélyzóna" + ordered next supports; upside proof level).
- [3] KOCKÁZATI KERET box present (weekly) / anti-panic machinery (event notes).
- [2] No advice framing; watch-points and conditionals only; disclaimer block present.

## E. Accountability — 10 pts
- [4] Every forward-looking statement logged to prediction-ledger with schema fields
      (incl. deadline + resolution criteria + own_vs_relayed).
- [3] Prior calls due for grading are graded this issue — **misses acknowledged explicitly**
      (the benchmark never did; we always do).
- [3] Promises kept: every "megnézzük hét közben" from prior issues either delivered
      or explicitly closed.

## F. Voice & language — 10 pts
- [3] Style-guide voice: hedging in potential mood, "Érdekesség/Összességében" rhythm,
      rhetorical self-Q&A, HUF conversions for big numbers.
- [3] Hungarian correctness: zero typos/agreement errors (the benchmark's weak spot).
- [2] Consistent `##` header vocabulary (no mixed ALL-CAPS/unlabeled drift).
- [2] Constructive-but-honest tone: opportunity framing present, doom deflated with
      base rates, but risks never minimized.

## Scoring protocol
1. Editor agent scores each checklist item 0 / half / full, cites evidence line for each.
2. `quality_gate.py` recomputes totals from the itemized JSON; blocks publish if gate fails,
   returning the failed items as concrete fix instructions.
3. Score + itemization appended to `reports/scores.jsonl` (trend monitored; 3-report
   decline triggers a review task).

## Known benchmark gaps we must BEAT (not merely match)
1. Implicit sourcing → we tag everything.
2. Silent misses → symmetric ledger grading.
3. Chart-dependent prose → numbers restated in text.
4. Typos → zero tolerance.
5. No alt depth (ETH had no dedicated TA) → we add an ETH block + TOTAL3.
6. Hedging density burying takeaways → one clear "Összességében" verdict per report.

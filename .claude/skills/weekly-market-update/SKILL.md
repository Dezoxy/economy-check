---
name: weekly-market-update
description: Produce the flagship Hungarian weekly market report (heti piaci update) end-to-end — cache verification, parallel analyst briefs, composition per template, ledger grading, fact-check, rubric scoring, delivery. Use for the Sunday weekly run or when tom asks for the weekly report. Argument: report date (defaults to today) or "dry-run".
argument-hint: "[YYYY-MM-DD | dry-run]"
---

# Weekly market update — pipeline skill

Read `AGENTS.md` first — its hard rules bind every step. This skill owns the full
pipeline for one report; do the steps in order and do not skip verification steps.

**Date resolution:** `$ARGUMENTS` is the run date (`YYYY-MM-DD`); empty → today.
`RPT = crypto-analyst/reports/<year>/<date>-heti-piaci-update.md`.

## Step 0 — Pre-flight (data plane)

```
python3 shared/fetchers/run.py --verify weekly-market-update --date <date>
```
- FAIL on a `required` source → run `python3 shared/fetchers/run.py --manifest
  weekly-market-update --date <date>` once, re-verify. Still failing → STOP and
  report which sources are missing; do not compose from partial required data.
  This includes required sources whose fetcher is not yet implemented (step D
  pending): a required source with no cache is a hard stop, never a workaround.
- Failing `degraded_ok` sources (fetch failure OR fetcher not yet implemented):
  continue, but list them now — the analysts may cover the gap via WebSearch/
  WebFetch (allowlisted, domain-tagged citations), and each degraded source must
  be labeled in the report ("közelítő adat", confidence tag).

## Dry-run mode (`$ARGUMENTS` = "dry-run")

Print, without composing or spawning agents:
1. the resolved date, report path, template in use;
2. the verify table from step 0 (available / degraded / missing per source);
3. the section outline from `crypto-analyst/templates/heti-piaci-update.md` with
   the assigned analyst per section and the cache files each will read;
4. ledger status: how many calls are due for grading this week
   (`crypto-analyst/ledger.jsonl`, deadline ≤ date, outcome unresolved).
Then stop. This is the step C acceptance check.

## Step 1 — Context load

Read: `crypto-analyst/templates/heti-piaci-update.md` (structure),
`style-guide.md` (voice), `analytical-doctrine.md` (the reasoning playbook —
compose with its patterns, respect its Súlyozás verdicts), `rubric.md` (what
gets scored), `prediction-ledger.md` (grading rules), `crypto-analyst/ledger.jsonl`
(due calls + last week's poll), and the previous report in
`crypto-analyst/reports/` if one exists (continuity: "ahogy a múlt heti anyagban…",
open promises to close).

## Step 2 — Analyst briefs (parallel, one message)

Spawn ALL FOUR as parallel Agent calls, each with: the run date, cache dir
`data/cache/<date>/`, degraded-source list, and their section assignment:

| Agent | Sections |
|---|---|
| `sentiment-analyst` | 1 VILÁG/GEOPOLITIKA (+ anti-panic inputs, watch-points) |
| `macro-analyst` | 2 MAKRÓ (+ 3 KOMMENTÁR candidates) |
| `crypto-analyst` | 4 KRIPTO/VÁLLALATI + 5 BITCOIN + ETH/TOTAL3 block |
| `onchain-analyst` | 6 ONCHAIN (skip only if this is an off-week AND no regime shift; say so) |

Briefs come back with `[src:]` tags and ledger-item lists. `HIÁNYZÓ ADAT` entries
propagate to the report as explicit gaps, never as filled-in guesses.

## Step 3 — Compose

Write `RPT` per the template, in Hungarian, style-guide voice:
- Fixed opening ritual; section order 1→10; ONE "Összességében" verdict; mandatory
  KOCKÁZATI KERET (bull + bear + exact invalidation levels); BITCOIN section closes
  with both triggers; JÖVŐ HÉT calendar (weekday + CET) + new poll with named band
  anchors; compact disclaimer block.
- Every number from a brief keeps its `[src:]` tag. Charts: not yet generated in
  step C — insert `<!-- chart: <what>, [src:...] -->` placeholders whose key numbers
  are ALREADY restated in prose (the prose must survive without images).
- Grade last week's poll and every due ledger call SYMMETRICALLY — misses named
  as plainly as hits ("Tévedtünk: …").
- The PostToolUse lint will block naked numbers immediately — fix, don't fight it.

## Step 4 — Ledger update

Append to `crypto-analyst/ledger.jsonl`: one JSON line per new forward-looking
statement (schema: `templates/prediction-ledger.md` — deadline and
resolution_criteria are mandatory fields, `own_vs_relayed` honest). Update graded
calls' `outcome`, `outcome_evidence`, `graded_on`, `self_review`.

## Step 5 — Fact-check (adversarial)

Spawn `fact-checker` with RPT + job folder (`crypto-analyst/`) + date. Fix every `block` finding in the report (and
ledger), then re-run the fact-checker. Repeat until PASS. Never argue a finding
away — if the checker is wrong, it will still be wrong after you verify against
the cache file, and only then may you note why.

## Step 6 — Editor score

Spawn `editor` with RPT + job folder. It writes `<RPT minus .md>.score.json` and
returns fixes. If gate fails (total < 80 or category < 60%): apply fixes, go back
to Step 5 (fact-check again after content changes), re-score. The Stop-hook
quality gate enforces this loop — you cannot finish with a failing report.

## Step 7 — Render PDF + deliver

First render the delivery artifact:
```
python3 shared/delivery/render_pdf.py RPT
```
(PDF lands next to the .md; if Chrome is unavailable the .md is delivered instead —
note it in the wrap-up, don't block.)

- Interactive session: show the score + a 3-line summary, then ASK whether to
  deliver. On yes: `python3 shared/delivery/deliver.py --report RPT`.
- Headless/scheduled run (invoked by run_job.sh): deliver without asking.
- Delivery re-checks the gate itself; a `REFUSED` from deliver.py means the score
  sidecar is missing/failing — go back to Step 6, never `--force`.

## Step 8 — Wrap up

Report in chat: score, ledger items added/graded, degraded sources used, open
promises for next week. If anything in the pipeline itself broke (fetcher, hook,
template gap), add it to PLAN.md backlog — never silently work around it twice.

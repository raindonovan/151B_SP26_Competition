# TODO.md — Wolfram Batch Queue

**Status: COMPUTABLE PASS COMPLETE (2026-05-29).**
All `computable=YES` items have been processed across batches B1–B29.

**Final: 477 DONE | 92 INCONCLUSIVE | 1 DISPUTED | 373 UNVERIFIED**

See `RESULTS_SUMMARY.md` for the full consolidated report.

## Nothing queued — error-finding is done
- All flagged buckets (P1, undercount, backsolve_disagree) verified → ~58 discrepancies found.
- All unflagged solvable items verified → confirmations only, 0 discrepancies.
- Remaining 373 UNVERIFIED are all flagged `MAYBE`: word-problems / competition items that
  Wolfram cannot adjudicate. They need **web/source search** (AoPS, textbook, WeBWorK), not Wolfram.

## Open actions for a human (from RESULTS_SUMMARY.md §5)
1. **F22 variance convention** — Kaggle probe: submit a known stats item with population vs sample
   variance to learn which the grader wants, before mass-applying variance corrections.
2. **F24 sheet-hygiene sweep** — grep `best_answer` across all 943 for "PLACEHOLDER", CoT text,
   or bare vocabulary words; all are unparsed/failed entries needing a value (e.g. 0611, 0498).
3. **373 MAYBE items** — route to the search agent (web/source) rather than Wolfram.

## Specific items flagged in SCRATCH (promoted here so they aren't lost)
- **Sheet answer SUSPECT — verify, likely sheet errors:**
  - 0016 — game theory, sheet/teacher = 501 (looks wrong)
  - 0488 — "Linetown", sheet/teacher = 4050 (suspect)
- **INCONCLUSIVE (Wolfram can't adjudicate) → route to web/source search:**
  - 0058, 0501, 0682 — functional-equation competition problems
  - 0255, 0647, 0675, 0772 — OEIS-pattern "compute a(n)" MCQs (Wolfram can't compute arbitrary OEIS sequences at given indices)
- Answer twin: 0017, 0606, 0211 all resolve to **181** (least odd prime of a_n = 4·a(n-1) − a(n-2)). Cross-check these three agree.

## Cross-reference — this data now feeds the v3 gold build
- `WOLF_RESULTS.csv` (309 HIGH + 161 MED) is the **Wolfram source for the v3 weighted-vote gold sheet** (weight: HIGH 3.0, MED 1.2). It REPLACES the tracker's stale 58-HIGH `wolfram_override` column — do not source Wolfram from the tracker.
- Join on `id` is **zero-padded** ('0000') here vs unpadded in the tracker — strip leading zeros (repeated trap).
- The **65 Wolfram-HIGH-vs-teacher disagreements** (≈56 confirmed sheet errors per the discrepancy pass) are the correction set: in the weighted vote, Wolfram HIGH (3.0) outweighs the correlated LLM bloc, so these resolve to the Wolfram answer automatically.
- The 373 MAYBE items are now being actively **web-searched (genuine-search-only: no computation, ≥90% exact-source match)** by the search agent — not Wolfram.

## Known dataset bugs (skipped throughout)
0011, 0317, 0570, 0585, 0622, 0858, 0894

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

## Known dataset bugs (skipped throughout)
0011, 0317, 0570, 0585, 0622, 0858, 0894

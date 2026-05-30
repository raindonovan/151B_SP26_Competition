# TODO.md — Wolfram Batch Queue

**Updated**: 2026-05-29
**Total DONE**: 308  |  **INCONCLUSIVE**: 57  |  **DISPUTED**: 1  |  **Unverified**: 577

## Batch history
- B1-B8 + WEBSEARCH: 66 (legacy)
- B9-B13 (P1): ~90 done, ~39 discrepancies, competition-heavy tail
- B14 (P2): 0 discrepancies (verification only)
- B15-B16 (P3 undercount-flagged): 17 discrepancies / 50
- B17 (P3 unflagged): 0 discrepancies (verification only)
- B18 (backsolve_disagree single-slot): 2 discrepancies / 25 (weak flag — see F23)

## Outcome vocabulary (per Rain): match / discrepancy / inconclusive. NOT "override".

## Priority (per Finding 23: undercount flag strong, backsolve_disagree weak)
- Remaining UNDERCOUNT-flagged computable: 0  ← highest discrepancy yield
- Remaining multi-slot computable (unflagged): 34  ← verification
- Remaining single-slot computable: 220  ← verification

## ▶ NEXT: batch21 (solvable leftovers pass)
IDs: 0279, 0282, 0283, 0284, 0286, 0290, 0292, 0295, 0304, 0305, 0321, 0324, 0331, 0337, 0340, 0348, 0351, 0355, 0356, 0365, 0366, 0377, 0381, 0384, 0394


## Known bugs
0011, 0317, 0570, 0585, 0622, 0858, 0894

## OPEN ACTIONS
- F22: resolve population-vs-sample variance convention via Kaggle probe.
- F24: sheet-hygiene sweep — grep best_answer for PLACEHOLDER / CoT text / bare words.

## Strategy (LOCKED)
- `undercount` flag = strong discrepancy signal (~30%). `backsolve_disagree` = weak (~8%).
- UNFLAGGED items = verification-only (~0% discrepancy).
- best=PLACEHOLDER/word/INVALID/CoT-text = sheet failure, supply value (F16/F21/F24).

# TODO.md — Wolfram Batch Queue

**Updated**: 2026-05-29
**Total DONE**: 346  |  **INCONCLUSIVE**: 69  |  **DISPUTED**: 1  |  **Unverified**: 527

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

## ▶ NEXT: batch23 (solvable leftovers pass)
IDs: 0507, 0511, 0512, 0513, 0514, 0517, 0524, 0526, 0532, 0533, 0534, 0536, 0544, 0545, 0547, 0549, 0551, 0552, 0554, 0556, 0560, 0561, 0567, 0569, 0574


## Known bugs
0011, 0317, 0570, 0585, 0622, 0858, 0894

## OPEN ACTIONS
- F22: resolve population-vs-sample variance convention via Kaggle probe.
- F24: sheet-hygiene sweep — grep best_answer for PLACEHOLDER / CoT text / bare words.

## Strategy (LOCKED)
- `undercount` flag = strong discrepancy signal (~30%). `backsolve_disagree` = weak (~8%).
- UNFLAGGED items = verification-only (~0% discrepancy).
- best=PLACEHOLDER/word/INVALID/CoT-text = sheet failure, supply value (F16/F21/F24).

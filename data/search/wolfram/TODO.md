# TODO.md — Wolfram Batch Queue

**Updated**: 2026-05-29 (end of session 2: B9-B17)
**Total DONE**: 259  |  **INCONCLUSIVE**: 31  |  **DISPUTED**: 1  |  **Unverified**: 652

## Batch history
- B1-B7: 38  B8: 25  WEBSEARCH: 5
- B9: 21H/1M/3I   B10: 22H/3I   B11: 17H/1M/7I   B12: 12H/1M/12I
- B13: 18H/1M/6I (P1 END)   B14: 12H/13M (P2, 0 discrepancies)
- B15: 14H/11M (P3 flagged, 10 discrepancies)   B16: 11H/14M (P3 flagged, 7 discrepancies)
- B17: 11H/14M (P3 UNFLAGGED, 0 discrepancies — verification only)

## ▶ NEXT: batch18 (FLAGGED single-slot — discrepancy candidates)
22 flagged single-slot computable items remain. Higher discrepancy yield than unflagged P3.
IDs: 0019, 0055, 0112, 0161, 0184, 0195, 0198, 0229, 0312, 0316, 0376, 0391, 0405, 0445, 0498, 0502, 0522, 0611, 0775, 0802, 0812, 0906, 0409, 0415, 0448

## After batch18
- Remaining UNFLAGGED P3 multi-slot (37 items): verification-only (~0% discrepancy per F20)
- P4 unflagged single-slot (~200): verification
- P5 other/MAYBE (~370): mostly competition/OEIS, expect high INCONCLUSIVE

## Known bugs
0011, 0317, 0570, 0585, 0622, 0858, 0894

## OPEN ACTION (Finding 22)
Resolve population-vs-sample variance convention via Kaggle probe before mass-applying variance corrections.

## Strategy (LOCKED)
- FLAGGED (undercount/disagree) items = discrepancy-rich (~30%). Prioritize these.
- UNFLAGGED items = verification-only (~0% discrepancy). Lower priority (F17, F20).
- best=word/"INVALID"/"answer" = inference failure, direct correction (F16, F21).
- Undercount mode = drop-earlier-subparts (F19).

# TODO.md — Wolfram Batch Queue

**Updated**: 2026-05-29
**Total DONE**: 234  |  **INCONCLUSIVE**: 31  |  **DISPUTED**: 1  |  **Unverified**: 677

## Batch history
- B1-B7: 38  B8: 25  WEBSEARCH: 5
- B9: 21H/1M/3I   B10: 22H/3I   B11: 17H/1M/7I   B12: 12H/1M/12I
- B13: 18H/1M/6I (P1 END)   B14: 12H/13M (P2, 0 overrides)
- B15: 14H/11M (P3, 10 overrides)   B16: 11H/14M (P3, 7 overrides)

## Priority distribution
P3 multi-slot remaining: 62 (flagged 0)

## ▶ NEXT: batch17 (P3 continued)
IDs: 0056, 0063, 0097, 0099, 0101, 0119, 0129, 0133, 0158, 0163, 0179, 0185, 0187, 0265, 0289, 0315, 0323, 0330, 0343, 0370, 0373, 0378, 0393, 0401, 0408

## batch18 (queued)
IDs: 0409, 0415, 0448, 0451, 0459, 0477, 0493, 0504, 0513, 0552, 0560, 0567, 0603, 0615, 0635, 0648, 0653, 0654, 0661, 0733, 0735, 0738, 0745, 0774, 0789

## Known bugs
0011, 0317, 0570, 0585, 0622, 0858, 0894

## OPEN ACTION (Finding 22)
Resolve population-vs-sample variance convention via Kaggle probe before mass-applying variance overrides.

## Strategy note
P3 override rate ~30% (B15:10, B16:7). MED items mostly correct-but-unverified.
Undercount = drop-earlier-subparts (F19). best=word/INVALID = inference failure (F16,F21).

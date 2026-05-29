# TODO.md — Wolfram Batch Queue

**Updated**: 2026-05-29
**Total DONE**: 184  |  **Total INCONCLUSIVE**: 31  |  **DISPUTED**: 1  |  **Unverified**: 727

## Batch history
- B1-B7: 38  B8: 25  WEBSEARCH: 5
- B9: 21 HIGH, 1 MED, 3 INCONCLUSIVE
- B10: 22 HIGH, 3 INCONCLUSIVE
- B11: 17 HIGH, 1 MED, 7 INCONCLUSIVE
- B12: 12 HIGH, 1 MED, 12 INCONCLUSIVE
- B13: 18 HIGH, 1 MED, 6 INCONCLUSIVE (P1 bucket END)
- B14: 12 HIGH, 13 MED, 0 INCONCLUSIVE (P2 bucket START — all teacher==best, verification only)

## Priority distribution (remaining unverified)
- P1: 0  P2: 27  P3: 108  P4: 219  P5: 372

## ▶ NEXT: batch15 (P2 continued)
IDs: 0440, 0473, 0483, 0502, 0504, 0507, 0544, 0549, 0551, 0554, 0560, 0614, 0691, 0703, 0713, 0722, 0754, 0759, 0760, 0774, 0779, 0802, 0808, 0838, 0865

## batch16 (queued)
IDs: 0906, 0918, 0015, 0021, 0027, 0035, 0043, 0046, 0050, 0056, 0063, 0082, 0097, 0099, 0101, 0119, 0129, 0133, 0157, 0158, 0163, 0179, 0185, 0187, 0194

## Known bugs
0011, 0317, 0570, 0585, 0622, 0858, 0894

## Strategy note
P2 items mostly have teacher==best already agreeing (zero overrides in B14). P2 is verification-anchoring,
not override-hunting. Consider whether P3 (multi-answer computable, 108 items) has higher override yield —
multi-slot undercount was the dominant failure in P1. P3 likely richer for actionable fixes.

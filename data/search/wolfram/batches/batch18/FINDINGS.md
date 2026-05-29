# Batch18 Findings — 2026-05-29

**Items**: FLAGGED single-slot (all `backsolve_disagree`-flagged) + 3 unflagged P3.
**Subject mix**: number_theory (10), algebra (6), trigonometry (4), statistics (4), geometry (2)

## Outcome distribution (match / discrepancy / inconclusive)
- **match** (verified answer agrees with sheet): 7
- **discrepancy** (sheet wrong): 2
- **inconclusive**: 12
- (3 MED items: multi-slot plausible, not each-slot verified)

By confidence: HIGH 10, MED 3, INCONCLUSIVE 12.

## Discrepancies (verified answer differs from sheet best)
| ID | Verified answer | Sheet best (wrong) | Issue |
|----|-----------------|--------------------|-------|
| 0611 | 1.356 | "PLACEHOLDER_0611" | SE=√(57/31); sheet has a literal placeholder string |
| 0775 | 6sin(x-7)-6 | 6sin(x-7)-36 | down-shift is -6, not -36 (looks like 6×6 error on the shift) |

## Matches (verified answer confirms the sheet → gold)
0055 (5x⁴), 0502 (period 8/11), 0522 (±0.472), 0802 (26/7), 0812 (512/sin⁶(2t)), 0906 (x=2,x=5), 0415 (s=√(A/6) + slots)

## Inconclusive (12 — competition / OEIS)
0112, 0161, 0184, 0198, 0229, 0312, 0316, 0376, 0391, 0405, 0445, 0498 — cross-section geometry, median-of-subsets, GF(2) tables, reducibility, game theory, gcd sums, partitions, etc. Not Wolfram-computable.

## Key finding

### Finding B18-1 — `backsolve_disagree` is a WEAK discrepancy signal (vs `undercount`)
This batch was all `backsolve_disagree`-flagged single-slot items. Result: only 2 discrepancies in 25 (8%), 7 matches, 12 inconclusive. Contrast with `undercount`-flagged P3 (B15-16: ~30% discrepancies). **Refines Findings 17/20:** the `undercount` flag is a strong discrepancy predictor; `backsolve_disagree` is weak — it fires on items where the back-solve posterior merely disagreed with the sheet, but the sheet (best) is usually already correct, and many such items are uncomputable competition problems. Future sweeps: prioritize `undercount` flag, deprioritize `backsolve_disagree`-only.

### Finding B18-2 — Sheet placeholder leakage (0611, 0498)
- 0611 best = literal "PLACEHOLDER_0611" (template never filled).
- 0498 best = leaked chain-of-thought rambling text (inference output not parsed to a final answer).
Both are sheet-construction failures, not math errors. Joins F16/F21 (best="INVALID"/"answer"/word). **Recommend a sheet-hygiene sweep:** grep best_answer for "PLACEHOLDER", multi-sentence text, or vocabulary words — all are unparsed/failed entries needing a value.

### Finding B18-3 — recurrence family now 4 instances
a_n=4a(n-1)-a(n-2) with least-odd-prime answer: 0017 (n=2015), 0211 (n=255), 0606 (n=25), now 0019 (n=155). All → 181. Strongly a dataset template; any future item with this recurrence → 181.

# Batch20 Findings — 2026-05-29

**Items**: solvable-leftovers pass (item 2 of the 254). Unflagged computable.
**Subject mix**: algebra (8), statistics (4), linear_algebra (2), calculus (2), trigonometry (2), number_theory (5), geometry (2)

## Outcome
- HIGH: 16 | MED: 2 | INCONCLUSIVE: 7
- **12 matches** (sheet confirmed correct), 0 discrepancies, + 4 MCQ values verified.

## Matches (sheet confirmed correct)
0166 (175(1/4)^n), 0172 (1320/3721), 0180 (m/2−7/2), 0189 (equation setup), 0206 (=4), 0216 (T=60), 0224 (2643), 0230 (−2.424), 0231 (regression line), 0234 (29x⁷+6x⁵), 0264 (256πt²), 0277 (38800).

## MCQ values verified (value computed; sheet stores a letter)
| ID | Verified value | Sheet letter |
|----|----------------|--------------|
| 0156 | eigenvalues −7, 2, 2 | H |
| 0178 | determinant = −4 | C |
| 0267 | k = −1/2 | C |
| 0272 | sec+tan = x + √(x²−1) | B |

## Inconclusive (7)
0162, 0175 (OEIS algorithm MCQs), 0199 (pentagon Fermat-point), 0200 (Brocard angle), 0212 (renewal process), 0220 (perfect-square count), 0235 (card subsets) — all competition/OEIS.

## Running observation (B19+B20 of the 254-pass)
Consistent with the prediction: the solvable-leftovers are **almost all matches** (24 matches across the two batches, 0 discrepancies). This pass is **verification/gold-anchoring**, not error-finding. Value confirmed for ~30 items so far; the ~14 inconclusive are all competition/OEIS that slipped into "computable=YES" via keyword classification but aren't actually Wolfram-solvable.

**Note for classifier:** several "computable=YES" items are really competition problems (0199, 0200, 0220, 0235). The subject keyword (geometry/number_theory) flagged them computable, but they're olympiad-style. Minor — doesn't change the workflow, just inflates the "solvable" estimate slightly.

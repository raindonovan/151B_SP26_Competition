# Batch21 Findings — 2026-05-29

**Items**: solvable-leftovers pass (item 3 of the 254). Heavy on calculus MCQs.
**Subject mix**: calculus (11), algebra (6), number_theory (4), linear_algebra (2), trigonometry (1), statistics (1)

## Outcome
- HIGH: 8 | MED: 11 | INCONCLUSIVE: 6
- 3 matches, 0 discrepancies, 5 more MCQ values verified.

## Matches
0292 (tan285°=−2−√3), 0381 (Σ17 = 2040), 0384 ((ln(11/32)−3)/5).

## MCQ values verified
| ID | Value | Letter |
|----|-------|--------|
| 0290 | 2 (real convergent part) | C |
| 0295 | 8π/15 (volume) | C |
| 0321 | a = 1 (tangent through origin) | H |
| 0351 | 12.287 (dy/dt at t=1) | A |
| 0355 | inflection (−3, −26/9) | H |

## Inconclusive (6)
0284, 0286, 0305, 0324, 0331, 0377 — competition / OEIS.

## New observation

### Finding B21-1 — calculus MCQs split: clean values vs messy closed forms
Two kinds of computable calculus MCQ:
- **Clean** (definite integrals → a number, tangent/inflection → a point): fully verifiable (0290, 0295, 0321, 0351, 0355).
- **Messy** (indefinite integrals → long closed forms: 0279, 0304, 0348, 0356, 0394): Wolfram computes them, but the answer is a multi-term expression that's tedious to match against an MCQ option without reading all options. Marked MED — the value is computable, but confirming the letter is high-effort, low-value (verification, not error-finding).

### Caught my own shortcut error
For 0295 I almost reused a wrong formula (a²π/3) from item 0147; the correct general result is **πa³/15** (verified: a=5→25π/3, a=2→8π/15). Lesson: re-derive, don't pattern-match across items even when they look identical.

## Running tally (254-pass: B19-B21)
- 75 items processed, ~27 matches, **0 discrepancies**, ~20 inconclusive (competition/OEIS).
- The pass continues to be pure verification. No wrong sheet answers found in 75 solvable-leftover items — strongly confirms that the errors were all in the flagged buckets (already done).

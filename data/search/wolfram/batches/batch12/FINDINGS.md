# Batch12 Findings — 2026-05-29

**Items**: 0610-0772 (25 P1 items)
**Subject mix**: number_theory (7), statistics (5), algebra (4), calculus (4), trigonometry (2), geometry (2), other (1)

## Confidence distribution
- HIGH: 12/25 (48%)
- MED: 1/25 (4%)
- INCONCLUSIVE: 12/25 (48%)

Note: INCONCLUSIVE rate climbed to 48% — this batch is heavily loaded with OEIS algorithms, competition problems, and conceptual MCQs that Wolfram cannot directly compute.

## Discrepancies (verified answer differs from sheet best)

| ID | Wolfram answer | Best (wrong) | Issue |
|----|---------------|--------------|-------|
| 0620 | 4/sqrt(7),16/7,2.167,B | B | 4-slot collapsed to 1 slot |
| 0655 | S=0.85L | 1 | completely wrong — trivial discount formula |
| 0679 | 11 | "answer" | completely wrong — silo radius |
| 0681 | 28900,170,135,205 | 135,205 | missing first 2 slots |
| 0684 | -1.55 | "answer" | completely wrong — critical z |
| 0716 | 19/33 | "answer" | completely wrong — R² formula |

**6 discrepancies**.

## Teacher/best equivalences
- 0642, 0704, 0723, 0762: teacher/best agree (notation differences only)
- 0696: best gives h-value (-8), teacher gives expression (x+8); effectively agree

## INCONCLUSIVE items (12)
Competition/OEIS heavy batch:
- 0610, 0646, 0647, 0675, 0682, 0695, 0700, 0720, 0727, 0751, 0772: competition or OEIS
- 0712: conceptual study design MCQ

## Key observations

### Pattern: OEIS algorithm MCQs are systematically INCONCLUSIVE
Items 0647, 0675, 0772 all follow the pattern: "given OEIS sequence a(n), compute y_list for input x_list, find MCQ letter". These require looking up or computing OEIS sequences for arbitrary indices. Wolfram Alpha cannot reliably do this (confirmed for: A-period-of-reciprocals, Hurwitz-Radon, bell-ringing).

### Pattern: items with best="answer" or best="INVALID" are ALL wrong
Items 0679, 0684, 0716 have best="answer" (literal string); items 0675, 0682, 0695, 0712, 0720, 0727 have best="INVALID". All these represent complete inference failures rather than format issues.

### 0690: log_π(400) = 5.2340
Value confirmed. Teacher=H, best=G. Clean computation: ln(400)/ln(π) = 5.2340.

### 0681: Artist revenue symmetric prices
Max revenue $28,900 at price $170. Symmetric prices $135 and $205 both yield revenue $27,675. These are the "equal-revenue partner prices" on each side of the optimum.

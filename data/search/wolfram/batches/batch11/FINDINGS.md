# Batch11 Findings — 2026-05-29

**Items**: 0438-0608 (25 P1 items)
**Subject mix**: algebra (7), statistics (5), number_theory (4), geometry (3), trigonometry (2), linear_algebra (1), other (1)

## Confidence distribution
- HIGH: 17/25 (68%)
- MED: 1/25 (4%)
- INCONCLUSIVE: 7/25 (28%)

Note: Higher INCONCLUSIVE rate due to competition problems in this batch (0443, 0450, 0488, 0501, 0540, 0583, 0598).

## Actionable overrides (Wolfram confirms teacher, best wrong)

| ID | Wolfram answer | Best (wrong) | Issue |
|----|---------------|--------------|-------|
| 0438 | 5,9,1,10,2,0,10,x^3y^7,1 | 1 | 9-slot polynomial info collapsed to 1 slot |
| 0444 | 113,35,112,61,148,43 | 43 | 6-slot division collapsed to 1 (last remainder only) |
| 0461 | 2, 302 | 3 | completely wrong — std=2 not 3, n=302 not 3 |
| 0503 | y=-43000x+833000, 446000, 2019 | 446000, 2019 | missing equation (slot 1) |
| 0505 | 1,3,6,-5,-4,2 | 2 | 6-slot Horner steps collapsed to last value only |
| 0539 | 4, 5 | 5 | undercount — lower bound 4 missing |
| 0557 | 5 | 6 | TRIVIAL WRONG: |5| = 5, not 6 |
| 0608 | B, A, A, 1981 | 1981 | 4-slot collapsed to last value |

**8 actionable overrides**.

## Teacher/best equivalences
- 0447, 0508, 0535, 0558, 0593, 0599, 0607: teacher/best agree (different notation)
- 0492: best gives value (81%) where teacher gives letter (A); effectively agree

## INCONCLUSIVE items (7)
- **0443**: Q(8) mod 1000 (competition)
- **0450**: Equiangular hexagon (competition)
- **0488**: Linetown line-orientation (competition — teacher=4050, best=2025!)
- **0501**: GCD sum over subsets (competition)
- **0540**: AR(1) MCQ (conceptual; slot 2 differs between teacher/best)
- **0583**: Rectangle cut competition (teacher=119, best=1)
- **0598**: Quadratic form standard form MCQ

## New findings

### Finding B11-1 — 0557 trivial error (|5|=6)
Qwen gave |5|=6 for a trivial absolute value computation. This type of error (integer arithmetic off by 1) is a new failure mode beyond the 7 established ones. May indicate specific tokenization or computation artifacts.

### Finding B11-2 — Competition problems cluster in P1 bucket
7/25 INCONCLUSIVE items are competition-level problems (game theory, combinatorics, functional equations). The P1 priority bucket (Qwen-vs-teacher disagreements) contains many such items where Qwen's wrong answer is simply garbage, not a format mismatch.

### Finding B11-3 — Horner evaluation pattern
Item 0505: Qwen reports only the final Horner value (2) for a 6-intermediate-step problem. This is the standard "last slot" undercount applied to Horner evaluation.

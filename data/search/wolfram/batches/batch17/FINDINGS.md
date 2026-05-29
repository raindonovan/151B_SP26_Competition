# Batch17 Findings — 2026-05-29

**Items**: P3 bucket — UNFLAGGED multi-slot computable (format_flags clean).
**Subject mix**: statistics (10), trigonometry (6), algebra (6), geometry (2), number_theory (1)

## Confidence distribution
- HIGH: 11/25 (44%) — Wolfram/hand-verified correct
- MED: 14/25 (56%) — multi-slot present, plausible, complex (R-output, MCQ-matching)
- INCONCLUSIVE: 0/25

## ZERO discrepancies
As predicted (Finding 20): unflagged P3 items have best_answer already complete. All 11 HIGH items had best CORRECT. The format_flags correctly identified that these don't need multi-slot expansion. This is pure verification anchoring.

## Wolfram/hand-verified correct (HIGH)
| ID | Verified |
|----|----------|
| 0063 | 92.4% CI (15.84, 18.96) via t(9)≈2.045 |
| 0097 | circle r=8sinθ → center (0,4), radius 4 |
| 0099 | absolute values: -6, 12, -6 |
| 0129 | polar: 5/sin(t), √7, -3cos(t), 2√2 tan(t) |
| 0133 | θ=5π/3 exact trig values |
| 0163 | factor → 9(x-5)(x+4): A=9,B=-5,C=4 |
| 0179 | division quotient/remainder 10-slot |
| 0289 | width inequality 4<w<9 |
| 0370 | midline y=-5, amplitude 10 |
| 0393 | inverse function + domain [-10,22] |
| 0401 | radian→degree conversions |

## MED items (complex, multi-slot intact)
0056, 0101, 0119, 0158, 0185, 0187, 0265, 0315, 0323, 0330, 0343, 0373, 0378, 0408 — MCQ-matching, R-output (logistic regression), or repeating-decimal-to-fraction. Best has all slots; values plausible but not each independently verified.

## New findings

### Finding B17-1 — Unflagged P3 is verification-only (confirms F20)
The undercount/disagree format_flags are a RELIABLE filter: flagged P3 → ~30% discrepancies (B15-16); unflagged P3 → 0% discrepancies (B17). Recommendation for remaining sweep: unflagged items are lower-priority — they confirm existing correct answers rather than fixing wrong ones. If time-constrained, skip unflagged P3 and move to P4/P5 flagged items.

### Finding B17-2 — HIGH-confidence anchors are accumulating well
259 DONE items now. The HIGH subset (Wolfram-verified, ~190 items) forms a strong gold-test-set core. Many B17 HIGH items are clean closed-form (trig values, factoring, conversions) ideal for the local test harness.

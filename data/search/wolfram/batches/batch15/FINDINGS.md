# Batch15 Findings — 2026-05-29

**Items**: P3 bucket — multi-slot (slots≥2) computable items, NO teacher consensus, flagged undercount/backsolve_disagree.
**Subject mix**: statistics (13), trigonometry (5), algebra (3), calculus (2), geometry (1)

## Confidence distribution
- HIGH: 14/25 (56%) — Wolfram-computed
- MED: 11/25 (44%) — multi-slot present & plausible, not each-slot independently verified
- INCONCLUSIVE: 0/25

## STRATEGY VALIDATION: P3 is the rich override bucket
**10 actionable undercount overrides** in this batch (vs 0 in P2/B14). Confirms Finding 17 prediction: P3 (multi-answer computable) has the highest override yield because multi-slot undercount is the dominant failure mode.

## Actionable undercount overrides (Wolfram full answer vs collapsed best)

| ID | Full Wolfram answer | Best (undercount) | Missing |
|----|---------------------|-------------------|---------|
| 0021 | 0.2915t+56.93, 67.43 | 67.43 | regression equation |
| 0027 | 1/3, 2/3, 7/6, 11/6 | 7/6, 11/6 | first equation's roots |
| 0082 | 1.309,1.677,?,No | 1.309,1.677,No | slot 3 (df/p-value) |
| 0239 | 35, 3.450 | 3.450 | mean=35 |
| 0262 | 850-50t, 1480-140t, 7 | 7 | both depreciation equations |
| 0318 | 8, 0.562 | 0.5625 | r=8 |
| 0320 | (approaches 1), 3.73 | 3.73 | part-b limit behavior |
| 0446 | 1.87, 0.972 | 0.9720 | standard error |
| 0468 | ?, 0.8816 | 0.8816 | slot 1 |
| 0470 | 1.96,2.201,2.326,2.718,2.576,3.106 | 2.576,3.106 | 95% & 98% CI z/t (4 of 6 slots!) |

## Wolfram-confirmed (best already correct — multi-slot intact)
- 0043: sin⁴(7x)=3/8-½cos(14x)+⅛cos(28x) (TrigReduce)
- 0157: spring x=-7cos(0.1t)+50sin(0.1t), x(13)=46.31
- 0210: tan(arcsin(4/7)+arccos(½))=-11.786
- 0273: -cos²x, 1, 2cos²x (trig simplify)
- 0281: odd-function values + product=-2.1655
- 0325: gas domain[0,280] range[0,14]

## MED items (multi-slot present, plausible, not each-slot verified)
0194, 0225, 0242, 0297, 0417, 0418, 0449, 0456, 0467 — complex ANOVA/t-test tables where best has all slots filled with plausible values. Recommend spot-check if these become high-leverage.

## New findings

### Finding B15-1 — 0470 is the worst undercount in P3 so far (4 of 6 slots)
Item 0470 asks for z AND t values across 95%/98%/99% CIs (6 slots). Qwen emitted only the 99% pair (2.576, 3.106). This is the same "last group only" pattern as the Horner/division undercounts — Qwen completes the LAST sub-part and drops earlier ones.

### Finding B15-2 — P3 undercount is "drop earlier sub-parts" not "drop within sub-part"
Pattern across 0027, 0262, 0470: multi-PART questions (a/b/c) where Qwen answers only the final part. Distinct from within-slot truncation. Post-processing lever: detect questions with N sub-part markers and verify N answers present.

### Finding B15-3 — recurrence-of-data: confirm best when multi-slot intact
6 items had best ALREADY correct with all slots (0043,0157,0210,0273,0281,0325). Even in the "undercount-flagged" P3 subset, ~24% were already complete. The format_flags are noisy — Wolfram verification still needed to separate true undercounts from false flags.

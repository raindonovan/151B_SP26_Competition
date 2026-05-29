# Batch16 Findings — 2026-05-29

**Items**: P3 bucket continued — multi-slot computable.
**Subject mix**: statistics (15), algebra (6), trigonometry (1), calculus (1)... mostly stats

## Confidence distribution
- HIGH: 11/25 (44%) — Wolfram-computed
- MED: 14/25 (56%) — multi-slot present & plausible
- INCONCLUSIVE: 0/25

## Undercount discrepancies (7)

| ID | Full answer | Best (undercount) | Missing |
|----|-------------|-------------------|---------|
| 0553 | 24, 1.6 | 1.600 | IQ difference 24 |
| 0666 | 76·1.532^t, 42.68 | 42.68 | exponential equation |
| 0718 | 65761800, 72704000, median | "median" | mean & median VALUES (best=word only!) |
| 0753 | ..., 16.56 | 16.56 | slots 1-3 |
| 0885 | 18, 139.875, 18, B | B | mode/mean/median values |
| 0914 | (0.190, 0.247) | 0.2474 | lower CI bound |
| 0923 | 93, 48, ... | 93, 48 | slot 3 |

## Wolfram-confirmed (best already correct — multi-slot intact)
- 0497: tan/arctan/cot of 48 (4-slot all correct)
- 0601: (3s-1)(2s+1)
- 0713: -3, not real (radicals)
- 0015: degree 8, NONE (polynomial test)
- 0035: down, ln(p) (log shift)
- 0050: 140A+150B=5930, 3A+4B=142 (system)

## Convention ambiguity flagged
- **0542**: range=285 confirmed, but variance/std depend on population vs sample convention. Wolfram sample: var=8388, std=91.59. Best used POPULATION: var=7457, std=86.35. Both defensible — Kaggle gold determines which. **Worth probing which convention the dataset uses for "variance"/"standard deviation" without "sample" qualifier.**

## New findings

### Finding B16-1 — 0718 "answer-as-label" failure (best = the word "median")
Item 0718 best_answer is literally the string "median" — Qwen output the NAME of the statistic instead of computing it. Combined with best="answer"/"INVALID" (Finding 16), this is a class of items where Qwen emits a placeholder/label token instead of a value. Pattern: best_answer is a non-numeric English word matching question vocabulary.

### Finding B16-2 — P3 stats convention question (population vs sample variance)
0542 surfaces a likely dataset-wide convention question: when a problem says "variance"/"standard deviation" without "sample", does gold use n or n-1 denominator? This affects MANY stats items. Recommend a targeted probe (submit both forms for one known item) to resolve globally.

### Finding B16-3 — P3 hit rate stabilizing at ~28-40% discrepancy
B15: 10/25 discrepancies. B16: 7/25 discrepancies. P3 discrepancy rate ~30%, consistently higher than P2 (0%). The MED items (multi-slot already filled) are mostly correct — the value is in the sheet, just unverified. P3's actionable yield is the undercount subset.

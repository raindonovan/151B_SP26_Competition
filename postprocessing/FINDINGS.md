# Post-Processing Findings

## F1 — Hendrycks is_equiv is the Kaggle grader
Confirmed via source-code review. 28pp gap with local judger.py explained.

## F2 — What Hendrycks auto-normalizes (DON'T fix)
dfrac→frac, \left/\right removed, whitespace stripped, \sqrt/\frac shorthand, x= prefix stripped.

## F3 — What Hendrycks does NOT normalize (our levers)
Multi-slot under-count (dominant). Fraction vs decimal. \text{A} vs A.

## F4 — Multi-slot under-count is 79% of failures
From Wolfram B1-7 audit. THE dominant failure mode.

## F5 — Trailing-zero strip is neutral
Day 3 ablation: 0.692 with strip = 0.692 without. No effect.

## F6 — ~310 items wrong despite \boxed{}
Ceiling from fixing WRONG answers >> fixing FORMAT or rescuing no-box.

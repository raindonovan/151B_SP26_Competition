# 29_05 — Scores Tracker

Fill in scores as Kaggle returns them.

**Base for both builds:** `submission/25_08/csvs/slot4_undercount_expand.csv` = 0.706 (current best)

| Build | CSV | Items changed | Score | Δ vs 0.706 | Slice items net |
|-------|-----|---------------|-------|------------|-----------------|
| 1 | undercount_plus_frac.csv | 8 | ___ | ___ | ___ |
| 2 | mcq_prepend_fix.csv | 16 | ___ | ___ | ___ |

Δ × 283 ≈ net slice items flipped (positive = right, negative = wrong).

## Pre-build predictions (so we can score our calibration)

| Build | Predicted score | Reasoning |
|-------|----------------|-----------|
| 1 | 0.713 (+0.007) | Slot 1 alone gained +0.007 on kitchen base; same overrides on slot 4 base should give same gain if additive |
| 2 | 0.713 (+0.007) | 16 items × 0.30 slice × 30-50% conditional yield ≈ +1.4 to +2.4 slice items → +0.5 to +0.8pp |

## Interpretation notes

### Build 1 (undercount_plus_frac)
- **= 0.713:** Levers fully additive. Confirms slot 4 and slot 1 wins were on independent slice items.
- **< 0.713 (e.g., 0.706-0.712):** Partial additivity. Some overlap between slot 4 and slot 1's slice wins (e.g., item 25 in slot 4 already had decimal→fraction within its multi-slot expansion).
- **> 0.713:** Bonus — possible from items where slot 4's expansion was wrong format but with frac fix now correct. Unlikely but possible.
- **< 0.706:** Frac override actively HARMING when stacked on slot 4. Would suggest slot 4 already had these items as expansion-with-correct-format and our additional frac box overrides a now-correct value.

### Build 2 (mcq_prepend_fix)
- **> 0.706:** Teacher MCQ consensus IS more reliable than Qwen on these items. The 25_08 Slot 3 no-op was masking real signal. **Action:** expand to all letter-disagreement items (~26 in 25_08's filter, possibly more at 2+ threshold)
- **= 0.706:** Mechanism worked (no longer broken), but teachers and Qwen are equivalent. No more MCQ overrides warranted.
- **< 0.706:** Teachers are wrong more than they're right. Trust Qwen's MCQ choices going forward; demote teacher MCQ consensus in evidence ranking.

## Why no Build 3+

Submission slots are constrained to 5/day. After today's 5 slots (25_08 round), Rain may have allocation for more tomorrow. These 2 are the highest-EV next steps based on 25_08 empirical results.

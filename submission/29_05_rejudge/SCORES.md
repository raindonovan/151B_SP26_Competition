# 29_05_rejudge — Post-Judge-Update Re-Submission Batch

**Date:** 2026-05-29 (Day 7) · **Status:** ⏳ AWAITING KAGGLE SCORES — fill in actuals below
**Trigger:** Piazza "Kaggle Competition Judge Updated" (Ruijia Niu) — judge made more adaptive on fraction/decimal mismatches; staff says *re-submit to get updated scores, daily limit raised to 5, expect overall increase as false-negatives are fixed.*

## Why this batch

Two goals, no new CSVs — we re-submit **existing** builds under the **updated judge**:
1. **Measure the judge-update lift** on our proven best (does 0.713 rise for free?).
2. **Decompose which post-processing levers still matter** under the new value-based judge, to decide what to keep vs retire in the normalizer (`postprocessing/scripts/normalizer.py`).

## What we know about the new judge (verified this session, local `judger.py`)

`judge_single_numerical_value` does **numeric-value comparison at ~1e-8 relative tolerance** with sympy/LaTeX parsing. Empirically:

| pred | gold | new judge |
|---|---|---|
| `4.000` | `4` | ✅ pass (trailing zeros dead as a concern) |
| `0.6000` | `3/5` | ✅ pass (**exact decimal ≡ fraction**) |
| `25.71` | `180/7` | ❌ fail (Qwen *rounded* — value differs) |
| `11.31` | `8√2` | ❌ fail (rounded) |

**Implication:** surface form (decimal vs fraction, trailing zeros) is no longer a lever when the value is exact. Live failure modes are now **precision/rounding** and **parseability**, plus the structural rules (MCQ first-box, multi-answer single-box-ordered, undercount).

## The 3 submissions

Reference base for diffs: `undercount_plus_frac.csv` (the 0.713 best).

| # | CSV | Prior score | vs ref | Items changed | Hypothesis tested | Prediction | **Actual** | Verdict |
|---|-----|-------------|--------|---------------|-------------------|------------|------------|---------|
| 1 | `submission/29_05/csvs/undercount_plus_frac.csv` | 0.713 (old judge) | — | — | Judge update lifts our best for free | rises vs 0.713 | _TBD_ | _TBD_ |
| 2 | `submission/28_05/csvs/slot4_undercount_expand.csv` | 0.706 (old judge) | differs only on 8 frac items | `135,207,529,716,784,817,919,936` | Is the numeric-format (frac) layer now redundant? | **ties #1** if new judge accepts the exact decimals; small gap remains only for rounded-decimal frac items | _TBD_ | _TBD_ |
| 3 | `submission/29_05/csvs/undercount_frac_mcq.csv` | ~0.710 expected (never scored) | adds 16 MCQ overrides | `18,117,403,443,457,501,518,589,670,675,682,695,720,727,786,935` | Do MCQ teacher-overrides help under the new judge? | ≈ or slightly below #1 (only 6 of 16 are real flips; historically net −1) | _TBD_ | _TBD_ |

## Decode logic — what each result tells the normalizer redesign

- **#1 − 0.713** = the free lift from the judge update. Large positive ⇒ much of our historical format-fixing was already done by the judge.
- **#1 vs #2** isolates the **frac/numeric lever**:
  - `#2 == #1` ⇒ numeric-surface layer is **dead** → retire `FRACTION_PROMOTED` + trailing-zero/aggressive numeric rules from the normalizer (keep them only as explicit per-item overrides).
  - `#2 < #1` by the old ~0.007 ⇒ frac still lives (rounded-decimal items where the sheet has the exact value) → keep frac-promotion but reframe it as an **override**, not a normalization.
- **#3 vs #1** isolates the **MCQ-override lever**:
  - `#3 > #1` ⇒ MCQ overrides are finally live under the new judge → wire MCQ teacher-override into the pipeline.
  - `#3 ≤ #1` ⇒ confirmed not worth it → drop blanket MCQ overrides (kitchen-sink fusion already absorbs teacher signal).

## Follow-ups once actuals are in (do not skip)

1. Fill the **Actual** + **Verdict** columns above.
2. Append the 3 rows to `submission/REGISTRY.md` (the master cross-round log), with `# 37/38/39`.
3. Update `strategy/SESSION_HANDOFF.md` TL;DR with the new best score.
4. Update `postprocessing/FORMAT_RULE_REGISTRY.csv`: promote/retire the frac (FR008) and trailing-zero (FR009) rules per the #1-vs-#2 result; resolve their `stale-risk` status with this evidence.
5. Apply the normalizer edits the result dictates (retire/gate numeric layer; restore pristine `judger.py`; swap `build_review_sheet.py` engine off strict-Hendrycks).

## Notes

- These CSVs were **not** produced by the merged normalizer — they come from the answer-sheet pipeline. This batch tests the *judge update's* effect on proven levers, which is the highest-EV use of an expiring submission window. The normalizer's own end-to-end value remains unmeasured against Kaggle.
- All 3 CSVs validated 2026-05-29: 943 rows, `id,response`, no duplicate IDs.

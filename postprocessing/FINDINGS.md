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

## F7 — Tier-1 items ARE graded wrong due to format (EMPIRICALLY CONFIRMED)

**Claim**: Items with correct math (Wolfram HIGH ∧ web-search GOLD ∧ 3/3 teacher agreement) can still be graded WRONG by Kaggle, purely because of answer FORMAT.

**Proof** (the fraction-fix smoking gun, submission #30 slot1_frac_override):
- 8 items changed decimal→fraction. 7 of 8 had 3/3 teacher agreement on the fraction value (tier 1).
- Base submission (0.692) carried Qwen's DECIMAL form (`0.6`, `2.8`, `21.45`...).
- ONLY the format changed (decimal→fraction). Math identical; teachers already agreed on the value.
- Score rose 0.692 → 0.699 = **+2 slice items flipped from WRONG to RIGHT**.
- Conclusion: ≥2 tier-1 items were graded wrong with decimal, right with fraction. Pure format flip.

**Mechanism**: Hendrycks `is_equiv` does NOT convert `0.6 ↔ \frac{3}{5}` (only `0.5 ↔ \frac{1}{2}` is hardcoded). So a mathematically-correct decimal fails string-match against a fractional gold.

**Caveat (intellectual honesty)**: We cannot name the SPECIFIC items graded wrong, because the ~283 test slice is hidden. What is proven: the CLASS of tier-1 items contains members graded wrong on format, and format-fixing recovers them at the aggregate level.

**Implication — the two-bucket framework for tier-1 items**:
1. **Bucket A — inference got the math right**: correct answer exists in some run (SC8/SC16/NoThinking). Find it, fix format, submit. NO adapter needed.
2. **Bucket B — no run ever got the math**: Wolfram/search/teachers know it, Qwen never produced it. These are ADAPTER candidates.
3. **Format layer sits on BOTH**: even bucket-A items can be graded wrong if emitted in wrong format (decimal vs fraction, etc.).

This is why the inference-run scan (tomorrow's task) must check, per tier-1 item: (a) did any run get the math right? (b) is our submitted format correct for it?

## F8 — `\boxed{X%}` does NOT score — `%` is a LaTeX comment char (EMPIRICALLY CONFIRMED)

**Claim**: A percent answer placed inside `\boxed{...}` can never be graded correct, even though the gold *is* the percent.

**Proof** (grader-mirror forensics, 29_06 perfect-score check on the official solution sheet):
- 4 private items have a bare-percent gold: id 96 `158%`, id 169 `400%`, id 237 `50%`, id 563 `20%`.
- The grader **keeps** `%` in gold: `norm_math_str('158%')` → `'158%'`; and `is_equal('158%','158%')` → **True**.
- But boxed extraction strips it: `extract_boxed_answer('\boxed{158%}')` → `'158'` (the `%` starts a LaTeX comment, truncating the box content). And `\%` is normalized away: `norm_math_str('158\%')` → `'158'`. So **every** boxed form (`\boxed{158%}`, `\boxed{158\%}`, `\boxed{158 \%}`, `\boxed{\frac{158}{100}}`) grades **False** vs gold `158%`.
- There is no boxed value that extracts to `158%`, so no `\boxed{}` answer can match a bare-percent gold.

**The fix that scores**: emit the percent as a plain final-answer sentence — `The answer is 158%.` — which the grader's *free-text* extractor (`extract_ans`) reads as `158%` and grades **True** for all 4. (Note: `Answer: 158%.` and a bare `158%` do **not** score — the working form is the `The answer is <v>.` sentence; and a `\boxed{}` anywhere in the string wins extraction, so you cannot box-then-rescue.)

**Implication**: percent answers are a normalization blind spot of the canonical `\boxed{}` convention. Any submission carrying percent golds (or any item whose correct answer is naturally a percent) must route those items to the free-text sentence form, not a box. See `submission/29_06/perfect_score_check/` (943/943 local, Strategy A hybrid).

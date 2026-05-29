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

# Format Conventions Research Summary

**Created**: 2026-05-28 Day 6
**Source**: Deep research on gold-answer formatting across math evaluation datasets

## TL;DR
The most likely Kaggle grader is Hendrycks-style "normalize-then-equal" on the last \boxed{}.
~80% of our errors are FORMAT mismatches, not math errors. Source-corpus identification enables per-item format routing.

## Key findings

1. **Hendrycks _strip_string** is the canonical math grader. It normalizes whitespace, dfrac→frac, \left/\right, but does NOT strip commas in numbers, does NOT normalize decimals to fractions (except 0.5→\frac{1}{2}).

2. **Source corpus identification is feasible** from problem text:
   - AIME: integer answers, "find remainder" phrasing
   - MATH: "Express your answer as...", LaTeX-heavy
   - WeBWorK: "Round to N decimals", multiple answer blanks
   - GSM8K: word problems, integer answers

3. **Multi-answer convention varies by corpus**:
   - MATH/NuminaMath: single \boxed{} with comma separation
   - OlympiadBench: multiple \boxed{} per answer
   - WeBWorK: semicolon-separated
   - Our grader wants: single \boxed{} with comma separation

4. **Math-Verify** (huggingface) is SymPy-based and format-tolerant. Our 80% format-loss confirms we are NOT using Math-Verify.

## Full report
See the deep research artifact from the Day 6 session (stored in Claude.ai conversation, not repo — too large for commit).

## Actionable format rules
- Emit LaTeX inside \boxed{} (not plain text)
- Use \frac{a}{b} not a/b for fractions
- No units inside the box
- No commas in large numbers (1000 not 1,000)
- Single \boxed{} per problem with comma-separated parts
- MCQ: just the letter in \boxed{}

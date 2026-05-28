# Post-Processing Techniques Inventory

**Updated**: 2026-05-28 Day 6

## Architecture

Post-processing is a **composable function chain**. Each item passes through a sequence of transformations. Each function is independently testable. Items can have custom routing (some only need unboxing, others need full normalization).

The adapter's job is mathematical correctness. Post-processing's job is format normalization. This separation is a locked strategic decision.

## Implemented (in postprocessing/scripts/)

| Technique | Script | Status | Effect |
|-----------|--------|--------|--------|
| Multi-answer reformat | (in splice scripts) | ACTIVE | Rewrite per-sub \boxed{a}\boxed{b} → single \boxed{a, b}. Confirmed +0.3pp |
| Trailing zero strip | (in splice scripts) | PROVEN NEUTRAL | 0.692 with = 0.692 without. No effect |
| Hendrycks dfrac→frac | format_review/ | ACTIVE | \dfrac → \frac (grader does this too, so redundant but safe) |
| \left/\right removal | format_review/ | ACTIVE | Strip \left and \right (grader normalizes these) |
| Whitespace collapse | format_review/ | ACTIVE | Remove all spaces inside \boxed{} |
| x= prefix strip | format_review/ | ACTIVE | Remove "x = " prefix when x ≤ 2 chars |
| No-box rescue | postprocessing/ | ACTIVE | Extract answer from responses lacking \boxed{} |

## Known but not yet implemented

| Technique | Source | Expected impact | Priority |
|-----------|--------|----------------|----------|
| **Comma-in-numbers strip** | Research report (Hendrycks _strip_string does NOT strip commas) | HIGH for items like 1,000 | HIGH |
| **Unit word removal** | Minerva word list (square, ways, integers, dollars, mph...) | MEDIUM | MEDIUM |
| **Decimal-to-fraction** | Only 0.5→\frac{1}{2} is hardcoded in Hendrycks. 0.25, 0.75 etc. are NOT | MEDIUM | MEDIUM |
| **a/b to \frac{a}{b}** | Hendrycks does this for integer a,b. Verify our pipeline does too | LOW (may already work) | LOW |
| **\text{} wrapper strip** | Hendrycks strips \text{ suffix} for units. What about \text{A} for MCQ? | MEDIUM for MCQ items | MEDIUM |
| **Trailing punctuation strip** | Remove trailing ., ,, ; inside \boxed{} | LOW | LOW |
| **Source-corpus routing** | Route AIME→integer, MATH→LaTeX, WeBWorK→decimal based on item style | HIGH (attacks 80% format-loss) | HIGH |
| **\sqrt shorthand fix** | \sqrt3 → \sqrt{3}. Hendrycks does this, but verify our outputs | LOW | LOW |
| **Negative sign normalization** | -\frac{2}{3} vs \frac{-2}{3} — _strip_string does NOT unify | MEDIUM | LOW |

## Grader behavior (verified)

See `grading/GRADER_SPEC.md` for full details. Summary:
- Extracts ONLY the LAST \boxed{} from response field
- String-matches after normalization (Hendrycks _strip_string)
- Order-sensitive within box: reversed = -17.6pp
- Per-slot \boxed{a}\boxed{b} costs -16.2pp vs single \boxed{a, b}
- Local judger.py is 28pp more lenient than Kaggle

## Research findings (from format conventions report, 2026-05-28)

Key normalization rules from actual grader source code:

**Hendrycks _strip_string** (likely our grader):
1. Strips all whitespace
2. dfrac/tfrac → frac
3. Removes \left, \right, \!, \$, \%
4. Removes degree symbols
5. Strips \text{ suffix} (units)
6. 0.5 → \frac{1}{2} (only this one decimal)
7. a/b → \frac{a}{b} (only integer a,b)
8. Does NOT strip commas in numbers
9. Does NOT normalize \mathrm{} or \mathbf{}
10. Does NOT convert other decimals to fractions

**Minerva variant** additionally:
- Strips unit words (square, dollars, mph, etc.)
- Strips commas in pure-digit numbers
- More aggressive on \text/\textbf wrappers

**Math-Verify** (huggingface):
- SymPy-based equivalence checking
- Format-tolerant by design
- Our 80% format-loss suggests we are NOT using Math-Verify

## Probe opportunities

To fingerprint grader behavior:
1. Submit \boxed{0.5} vs \boxed{\frac{1}{2}} on same item → delta reveals decimal-fraction handling
2. Submit \boxed{1,000} vs \boxed{1000} → delta reveals comma handling
3. Submit \boxed{5 \text{ m/s}} vs \boxed{5} → delta reveals unit handling

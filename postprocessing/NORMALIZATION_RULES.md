# Normalization Rules — Canonical Tiered List

**This file is the normalizer's decision framework.** Every rule is classified by evidence quality. The post-processor applies TIER 1 unconditionally, TIER 2 by default, and TIER 3 only when explicitly enabled.

**Updated**: 2026-05-28

---

## TIER 1 — CONFIRMED (empirically verified via Kaggle submissions)

Apply these unconditionally. Each has submission-pair evidence.

| # | Rule | Evidence | Effect |
|---|------|----------|--------|
| 1.1 | **Multi-slot consolidation**: collect ALL \boxed{} from response → single \boxed{a, b, c} | Slot 4 undercount: +1.4pp (0.692→0.706) | +4 slice items from 51 changes |
| 1.2 | **Decimal→fraction for known rationals**: convert decimal to \frac{a}{b} when teachers unanimously agree on fraction form | Slot 1 frac_override: +0.7pp (0.692→0.699) | +2 slice items from 8 changes |
| 1.3 | **NEVER use per-slot separate boxes**: \boxed{a}\boxed{b} → \boxed{a, b} | Probe #3 vs #4: -16.2pp | Catastrophic if violated |
| 1.4 | **NEVER reverse multi-answer order**: maintain placeholder order | Probe #4 vs #5: -17.6pp | Catastrophic if violated |

## TIER 2 — HIGH CONFIDENCE (source code + Piazza, not submission-tested)

Apply by default. Evidence from reading Hendrycks source code and instructor confirmations. These are things Hendrycks AUTO-NORMALIZES — applying them on our side is safe (redundant at worst).

| # | Rule | Evidence | Apply? |
|---|------|----------|--------|
| 2.1 | dfrac→frac, tfrac→frac | Hendrycks `_strip_string` line: `replace("tfrac","frac")` | YES (redundant but safe) |
| 2.2 | Strip \left, \right | Hendrycks source | YES (redundant but safe) |
| 2.3 | Strip ^\circ, ^{\circ} | Hendrycks source | YES (redundant but safe) |
| 2.4 | Strip \%, \$ | Hendrycks source | YES (redundant but safe) |
| 2.5 | Strip ALL whitespace | Hendrycks source: `replace(" ","")` | YES (redundant but safe) |
| 2.6 | Strip \text{ UNIT} suffix (with leading space before unit) | Hendrycks `_remove_right_units` | YES (redundant but safe) |
| 2.7 | Strip x= prefix when LHS ≤ 2 chars | Hendrycks source | YES (redundant but safe) |
| 2.8 | 0.5 → \frac{1}{2} (ONLY this exact string) | Hendrycks source hardcoded | YES (redundant but safe) |
| 2.9 | a/b → \frac{a}{b} for integer a,b | Hendrycks `_fix_a_slash_b` | YES (redundant but safe) |
| 2.10 | \frac12 → \frac{1}{2} (shorthand fix) | Hendrycks `_fix_fracs` | YES (redundant but safe) |
| 2.11 | \sqrt3 → \sqrt{3} (shorthand fix) | Hendrycks `_fix_sqrt` | YES (redundant but safe) |
| 2.12 | Strip \! (thin negative space) | Hendrycks source | YES (redundant but safe) |
| 2.13 | MCQ: extract FIRST \boxed{LETTER} | Starter notebook cells 11, 22 | YES (critical for MCQ overrides) |
| 2.14 | Free-form: extract LAST \boxed{} | Starter notebook + probes | YES (already standard) |
| 2.15 | No sympy equivalence on server | Piazza: Anthony Tong 2026-05-09 | N/A (informs what NOT to expect) |

## TIER 3 — BELIEVED (theoretical / research-based, NOT empirically tested)

Apply only when explicitly enabled OR when we have per-item evidence. These are things Hendrycks does NOT normalize — they represent potential levers but unverified.

| # | Rule | Evidence | Risk |
|---|------|----------|------|
| 3.1 | Other decimal→fraction (0.25→\frac{1}{4}, 0.75→\frac{3}{4}, etc.) | Hendrycks only converts "0.5". Piazza confirms no fraction/decimal normalization. Slot 1 frac_override confirms fractions can help. | MEDIUM — might convert TO wrong form if gold is decimal |
| 3.2 | Strip trailing zeros (9.0→9, 70.00→70) | Hendrycks code does NOT strip. 63 items have trailing zeros. | LOW — tested NEUTRAL (Slots 25/26). May interact differently with other fixes. |
| 3.3 | Strip commas in numbers (1,000→1000) | Hendrycks does NOT strip commas | LOW — no items identified with this issue yet |
| 3.4 | Strip \mathrm{}, \mathbf{} wrappers | Hendrycks does NOT strip these | LOW — rare in our outputs |
| 3.5 | Source-corpus routing (AIME→integer, MATH→LaTeX, WeBWorK→decimal) | Format conventions research. Theoretically attacks 80% format loss. | MEDIUM — no empirical test. Could help or hurt depending on classification accuracy. |
| 3.6 | No-box rescue (extract answer from non-boxed responses) | 4 items with 4/4 unanimous rescue. Already in overrides. | LOW — only 4-5 items affected |
| 3.7 | Strip \text{} wrapper on MCQ letters (\text{A}→A) | Wolfram Finding 10. Hendrycks strips \text{ X} only with LEADING SPACE. \text{A} (no space) may be preserved. | UNKNOWN — unverified |
| 3.8 | Negative sign placement: -\frac{2}{3} vs \frac{-2}{3} | Hendrycks does NOT unify these | UNKNOWN — never tested |
| 3.9 | Add missing prefix/label/unit (D=, Quadrant, ^\circ) | Wolfram failure mode 4. Per-item rule. | HIGH — requires knowing the gold format |

## TIER 4 — DISPROVED / DEAD (do NOT apply)

These have been tested and shown to be neutral or harmful.

| # | Rule | Evidence | Verdict |
|---|------|----------|---------|
| 4.1 | Trailing-zero strip (standalone) | Slots 25/26: 0.692 = 0.692 | NEUTRAL — don't waste time |
| 4.2 | Bulk search-gold overlay | Slot 2: -2.1pp (0.692→0.671) | HARMFUL — don't bulk-apply |
| 4.3 | MCQ override via append-to-end | Slot 3: 0.692 = 0.692 (no-op due to FIRST-box extraction) | BROKEN MECHANISM — use prepend/replace |
| 4.4 | dfrac→frac as a lever | Auto-normalized by Hendrycks. No delta possible. | DEAD — redundant |
| 4.5 | Whitespace in comma lists | Auto-normalized by Hendrycks. "a, b" = "a,b" | DEAD — redundant |

## How the normalizer uses this list

```python
def normalize(response, item_metadata, config):
    answer = extract_last_boxed(response)
    
    # TIER 1 — always apply
    answer = consolidate_multi_slot(response, item_metadata)  # 1.1
    answer = decimal_to_fraction_if_unanimous(answer, item_metadata)  # 1.2
    
    # TIER 2 — apply by default (redundant with grader, but safe)
    answer = dfrac_to_frac(answer)  # 2.1
    answer = strip_left_right(answer)  # 2.2
    answer = strip_degree_symbols(answer)  # 2.3
    answer = strip_percent_dollar(answer)  # 2.4
    answer = strip_whitespace(answer)  # 2.5
    answer = strip_text_units(answer)  # 2.6
    answer = strip_var_equals_prefix(answer)  # 2.7
    answer = fix_half(answer)  # 2.8
    answer = fix_slash_fractions(answer)  # 2.9
    answer = fix_frac_shorthand(answer)  # 2.10
    answer = fix_sqrt_shorthand(answer)  # 2.11
    
    # TIER 3 — only if enabled in config
    if config.get('broad_frac_conversion'):
        answer = broad_decimal_to_fraction(answer)  # 3.1
    if config.get('strip_trailing_zeros'):
        answer = strip_trailing_zeros(answer)  # 3.2
    if config.get('source_routing'):
        answer = route_by_source_corpus(answer, item_metadata)  # 3.5
    
    # TIER 4 — NEVER apply
    # (not even in code — these are dead)
    
    return f"\\boxed{{{answer}}}"
```

## Maintaining this list

When a new rule is proposed:
1. Check if it's already in this list
2. If new: add to TIER 3 (believed)
3. Design a submission probe to test it
4. If confirmed: promote to TIER 1
5. If disproved: demote to TIER 4

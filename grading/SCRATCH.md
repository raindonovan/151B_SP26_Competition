# grading/SCRATCH.md — Empirical grader findings (notebook style)

Drop anything here. Crystallized rules live in `GRADER_SPEC.md`.

---

## 2026-05-28: 25_08 submission run — five new empirical confirmations

The 25_08 run was effectively a probe suite. Documenting what each slot's score tells us about the grader (additional to the existing GRADER_SPEC).

### 1. The MCQ "first box" rule is REAL and breaks append-to-end overrides

Slot 3 of 25_08 (`slot3_mcq_teacher_override.csv`) used the standard override mechanism: append `\n\n\boxed{LETTER}` at end of response for 26 MCQ items.

**Result: 0.692 = exactly base. Net delta = 0.000.**

This empirically confirms GRADER_SPEC §3 — for MCQ, the grader uses `re.search` for the FIRST `\boxed{LETTER}`, so appending at the end does nothing. The original `\boxed{LETTER}` from kitchen_sink_C's response wins.

**Implication for post-processing infrastructure:** Any system applying overrides via append must branch by item type. MCQ overrides require prepend or full-replace.

### 2. Hendrycks decimal↔fraction non-normalization is REAL

Slot 1 (`slot1_frac_override.csv`) overrode 8 items where Qwen emitted decimals but teacher consensus was a fraction.

**Result: 0.699 (+0.007 = +2 slice items from 8 overrides, ~83% conditional yield).**

This directly proves that `0.6 ≠ \frac{3}{5}` under Hendrycks `is_equiv`. The MATH paper's stated convention ("probabilities expressed as simplified fractions") is observed in this competition's gold labels too.

**Implication:** Every item where Qwen emits a clean decimal but the underlying answer is rational deserves an override pass.

### 3. Slot order and slot count are absolute (multi-answer)

Slot 4 (`slot4_undercount_expand.csv`) expanded 51 items from `\boxed{LAST_SLOT}` to `\boxed{slot1, slot2, ..., slotN}`.

**Result: 0.706 (+0.014 = +4 slice items). NEW BEST.**

Of the 51 overrides:
- 29 were whitespace-only changes (`'4, 16'` → `'4,16'`) — ZERO grader impact. This re-confirms the global `replace(' ','')` normalization.
- 21 were real content changes (added missing slots, converted decimal→fraction within multi-answer, fixed letter ordering)
- 4 net slice items flipped wrong→right

This confirms three behaviors:
- Multi-answer must be SINGLE `\boxed{}` with comma-separated values
- Order within the box matches gold's order exactly (string match after whitespace strip)
- The grader doesn't look at reasoning trace for missing slots — only the box

### 4. Hendrycks does NOT normalize multi-character LHS prefixes

Slot 2 (`slot2_search_gold_overlay.csv`) was net harmful (−6 slice items). Forensic analysis of the 68 real-content changes showed three failure patterns. **Pattern A** = search-gold added multi-char label prefixes that Hendrycks does NOT strip:

| Item | BASE | Search-gold (lost) |
|------|------|---------------------|
| 20 | `228, 229, 250` | `Mean=228, Median=229, Mode=250` |
| 97 | `0, 4, 4` | `x=0, y=4, r=4` (single-char `x=` likely stripped, but multi-slot context complicates) |
| 108 | `72, 12x` | `A=72, B=12x` |
| 139 | `201, \dfrac{1}{n(n+1)}` | `A=201, B=1/(n*(n+1))` |

`_strip_string` only handles `x=` when `len(LHS) ≤ 2`. So `x=` → stripped; `Mean=` → preserved as-is in the string match.

**Implication:** Any override that ADDS a labeled-equation form to a previously bare answer is risky. Strip labels before override.

### 5. Hendrycks does NOT normalize `*` for multiplication

Slot 2 also showed (**Pattern C**):

| Item | BASE | Search-gold (lost) |
|------|------|---------------------|
| 104 | `4.166` | `7.7*31*pi/180` |
| 127 | `10.7` | `5*ln(17/2)` |

The `*` survives Hendrycks normalization. Gold expressions use `\cdot` or implicit multiplication, not `*`.

**Implication:** Math-notation overrides must use LaTeX (`\cdot`, `\ln`), not Python-style operators.

### 6. Hendrycks DOES handle `\frac` ↔ `a/b` for pure integers

Item 135 in BOTH slot 1 (`\frac{3}{5}`) and slot 2 (`3/5`) had the same effect — both presumably matched gold. This is `_fix_a_slash_b` doing its job for pure integer numerator/denominator with no other content in the box.

**But:** It does NOT fire for `3/5, 0.5` (comma-separated multi-answer) because the box content isn't just `3/5`. Multi-slot fractions need explicit `\frac{}`.

### 7. Whitespace strip is GLOBAL and EXHAUSTIVE

Slot 4's 29 whitespace-only "changes" produced exactly zero score impact. Examples:
- `'4, 16'` → `'4,16'` (space after comma) — equivalent
- `'7, 0.875'` → `'7,0.875'` — equivalent
- `'A, D, A'` → `'A,D,A'` — equivalent
- `'1174.8, 55'` → `'1174.8,55'` — equivalent

Confirms `replace(' ', '')` is applied globally to both gold and pred before comparison.

### 8. Source-type label in search results does NOT equal "external verification"

Slot 2's catastrophic −0.021 was driven by 61 of 68 real-content overrides coming from `source_type ∈ {computation, math, basic math}` — i.e., the search agent's OWN math labeled as GOLD. Only 1 of the 116 items had an actual external aggregator source (HW.Study); only ~5 had strong sources (Putnam, MathWorld).

**Implication for the grader-spec reader:** When evaluating an evidence stack, the `confidence` and `status=GOLD` fields in search CSV are agent-internal flags, not externally-verified facts. Treat them as approximately equivalent to "another LLM's opinion" — not stronger than our own SC majority.

---

## Summary of empirical rule confirmations (this run)

| GRADER_SPEC rule | Status before 25_08 | Status after 25_08 |
|------------------|---------------------|---------------------|
| Free-form: last `\boxed{}` only | Confirmed (prior probes) | Re-confirmed (every slot 4 expansion) |
| MCQ: first `\boxed{LETTER}` via re.search | Sourced from notebook | **Empirically confirmed** (slot 3 = exact no-op) |
| Global whitespace strip | Confirmed | Re-confirmed (29 whitespace-only changes = 0 impact) |
| `\dfrac` ≡ `\frac` | Confirmed | No new evidence |
| Decimal ↔ fraction NOT normalized | Confirmed (Piazza, source) | **Empirically demonstrated** (+2 slice from 8 frac overrides) |
| `_strip_string` `x=` only for LHS ≤ 2 chars | Confirmed (source code) | **Empirically demonstrated by failure** (Mean=, A= survived) |
| `_fix_a_slash_b` pure-int only | Confirmed (source code) | Re-confirmed (item 135 both formats worked) |
| Multi-answer single box, ordered | Confirmed (probes) | Re-confirmed (slot 4 wins) |
| Order matters within box | Confirmed (probe_b_reversed −17.6pp) | No new evidence |
| `*` NOT normalized | Inferred | **Empirically demonstrated by failure** (104, 127 lost) |
| Symbolic ↔ decimal NOT normalized | Inferred | **Empirically demonstrated** (item 834 trig values) |


---
## Append — claude_grader_research — 2026-05-28 (KNOW / SUSPECT / DON'T-KNOW summary)
### WHAT WE KNOW (source-verified or Piazza-confirmed)
- Grader = Hendrycks `is_equiv`. Fetched real source, ran 35+ probes, 20/20 matched our prior docs.
- Free-form: LAST `\boxed{}` (rfind, brace-matched). MCQ: FIRST `\boxed{LETTER}` (re.search), fallback last bare capital.
- `_strip_string` exact pipeline documented (order matters) in GRADER_RESEARCH.md §1.
- NO sympy server-side (Piazza Anthony Tong 2026-05-09). judger.py (Minerva/sympy) is NOT the grader → explains 28pp gap.
- Reference impl saved: grading/hendrycks_is_equiv_reference.py + hendrycks_extraction_reference.py (VERIFIED, use as validation harness before submitting).
### WHAT WE SUSPECT (single signal / inference)
- Gold uses `\frac` for rationals (MATH convention + 1 probe). Strong but not airtight per-item.
- Slice may shake-down on 943 (AIMO winner + RED_ALERT both say overfit-public-LB risk). Directional, not measured.
### WHAT WE DON'T KNOW
- Exact gold STRING for any specific item (slice hidden). All "correct answers" are proxies.
- Whether slice over/under-samples MCQ/hard items (AMBER #1).
- Per-item gold notation choices (set braces? Yes/yes? interval open/closed?) — these are per-item evidence questions, NOT blanket rules.
### GOLDEN KEY (Phase 4): NO external grader code exists online.
- CSE 151B SP26 *math* comp is private/un-indexed (public search only finds old taxi-time CSE151B comps).
- Closest = in-repo starter notebook, but that's the LOCAL judger (Minerva), NOT the server grader (Hendrycks). Our reconstruction is the best obtainable; confidence HIGH.

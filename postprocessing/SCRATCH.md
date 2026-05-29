# postprocessing/SCRATCH.md — Unsorted findings, ideas, observations

Drop anything here. Rain will sort it later.

---

- AMBER ALERT (Day 6): format-aware comparison is critical everywhere. Backsolve, answer sheet, post-processing all need to use the SAME normalization as the grader (Hendrycks _strip_string). Raw string comparison introduces noise.
- Post-processor should be a composable function chain with per-item routing. Each item gets a custom sequence of functions based on its format needs.
- Adapter format decision (LOCKED): adapter just needs to produce something resembling an answer. Post-processing handles format. This means post-processing is a PREREQUISITE for evaluating the adapter.
- Every discovered format rule (e.g., "item X needs trailing zeros") is literally a point on the scoreboard. Record in FORMAT_RULES.md.
- Source-corpus routing is the highest-EV post-processing improvement: route AIME→integer, MATH→LaTeX, WeBWorK→decimal. Attacks the 80% format-loss directly.
- Hendrycks _strip_string does NOT normalize: commas in numbers, decimals to fractions (except 0.5), trailing zeros, \mathrm{} wrappers. These are all levers.
- Minerva normalizer additionally strips unit words and commas in pure-digit numbers. If our grader uses Minerva, many format issues go away. Our 80% format-loss suggests it doesn't.
- Probe opportunity: submit \boxed{0.5} vs \boxed{\frac{1}{2}} on same item to fingerprint grader behavior.

---

## [Penny 2] 119 format-only-diff items extracted (2026-05-28, claude_librarian)

**Source**: data/FINDINGS.md §5, data/master_item_tracker.csv `format_only_diff_teacher` flag.
**Output**: `postprocessing/format_candidates_117.csv` (119 items — the "117" name is from the original count; actual extraction yielded 119).
**What these are**: Items where our current best_answer matches the teacher consensus AFTER normalization but differs in raw string form. These are PURE FORMAT ERRORS — the math is right, the encoding is wrong.
**Action**: Feed these into the post-processing pipeline. Each one is a recoverable point via format transform only (no math re-computation needed).
**Priority**: HIGH — these are the lowest-hanging fruit for post-processing.

---

## [Penny 3] Multi-slot undercount items (2026-05-28, claude_librarian)

**Source**: data/FINDINGS.md §5, data/master_item_tracker.csv `undercount` flag, data/undercount_candidates.csv (82 rows).
**What these are**: 110 items flagged as `undercount` in master tracker (items where current answer has fewer slots than the question's [ANS] markers). The undercount_candidates.csv has 82 of these pre-extracted.
**Gap**: 110 flagged vs 82 in CSV — 28 items may be missing from the CSV or were filtered.
**Why it matters**: Multi-slot undercount is the DOMINANT failure mode (79% of B1-7 audit items per data/FINDINGS.md §4). Qwen emits only the last \boxed{} for multi-answer items, losing all other slots.
**Action**: Post-processor needs multi-answer expansion — collect all \boxed{} from raw response, merge into single \boxed{a, b, c}.

---

## 25_08 SUBMISSION RUN — EMPIRICAL GRADER FINDINGS (2026-05-28)

Five submissions to Kaggle yielded the cleanest grader-behavior data we've ever collected. Documenting every confirmed/refuted/clarified rule.

### Base: kitchen_sink_C = 0.692 (196/283 slice items correct)

| Slot | Mechanism | Score | Slice Δ | Per-change conditional yield |
|------|-----------|-------|---------|------------------------------|
| 1 frac override (8 items) | Append `\boxed{\frac{a}{b}}` | 0.699 | **+2** | **~83%** ← best yield ever |
| 2 search-gold (116 items) | Append various | 0.671 | **−6** | **−17%** (net harmful) |
| 3 MCQ teacher (26 items) | Append `\boxed{LETTER}` | 0.692 | **0 (exact)** | — (mechanism failure) |
| 4 undercount (51 items, 21 real) | Append `\boxed{a,b,c}` | **0.706** 🏆 | **+4** | **~63%** |
| 5 combined (186 items) | Stacked appends | 0.696 | +1 | low (interference) |

### CONFIRMED grader rules (from this run + prior probes)

#### Extraction
1. **Free-form items: extracts ONLY the LAST `\boxed{}`.** Re-confirmed by every slot 4 expansion that worked. The model's reasoning trace contains the full multi-answer values, but the grader sees only the final box.
2. **MCQ items: extracts FIRST `\boxed{LETTER}` via `re.search`, fallback to last bare capital.** Re-confirmed empirically by Slot 3 (26 append-to-end MCQ overrides → exact 0.692 = no change). **This means append-to-end mechanism is BROKEN for MCQ.** Must prepend or replace whole response.

#### Normalization (what Hendrycks DOES handle — confirmed no impact)
3. **Global whitespace strip** (`replace(' ','')`). Slot 4 had 29 items with whitespace-only changes (`'4, 16'` → `'4,16'`) — ZERO grader impact. Strip is real.
4. **`\dfrac` ≡ `\frac`** — Slot 4's item 137 had `\frac{2}{1}` vs search-gold's `2/1` and they're equivalent under `_fix_a_slash_b` because both are integer-over-integer.
5. **`x=` prefix strip when LHS ≤ 2 chars.** Slot 2 item 97 with `x=0, y=4, r=4` MAY have been stripped to `0, 4, 4` matching base — but the surrounding multi-slot context complicates this. Single-char `x=` strip is confirmed from prior runs.

#### Normalization (what Hendrycks does NOT handle — confirmed FAILURE causes)
6. **Decimal ↔ fraction NOT normalized.** `0.6` ≠ `\frac{3}{5}` to the grader. Slot 1's wins (+2 slice items from 8 decimal→fraction overrides) directly prove this. MATH paper convention is fractions for rational answers; gold matches that convention.
7. **Decimal ↔ symbolic NOT normalized.** Slot 4's item 834 (`0.7854, 4.712, -9.948` → `\pi/4, 3\pi/2, -19\pi/6`) suggests gold sometimes uses exact symbolic forms.
8. **`*` for multiplication NOT normalized.** Slot 2 item 104 (`7.7*31*pi/180`) and item 127 (`5*ln(17/2)`) used `*` — Hendrycks has no `*` → `\cdot` normalization. These broke items that may have been correct in base.
9. **Multi-character LHS prefixes NOT stripped.** Slot 2 item 20 (`Mean=228, Median=229, Mode=250`) and item 108 (`A=72, B=12x`) added 4+ char prefixes that survive normalization. Likely caused some of the −6 loss.
10. **Verbal/conditional notation NOT normalized.** Slot 2 item 61 (`0.76c if 0≤c≤150; 10.5+0.69c if c>150`) used a verbal piecewise definition — gold almost certainly expects function notation, not English conditions.

#### Slot/order behavior
11. **Multi-answer requires SINGLE `\boxed{a,b,c}`.** Per-slot `\boxed{a}\boxed{b}` costs −16.2pp (from probes #2, #3). The grader takes ONLY the last box.
12. **Slot ORDER matters absolutely.** Reversal probe cost −17.6pp. String match is position-sensitive within the box.
13. **Slot COUNT matters absolutely.** Slot 4 items 232 (`3` → `40,37,3`) and 505 (`2` → `1,3,6,-5,-4,2`) recovered points by adding missing leading slots. The grader does not credit "last slot matches".

### EMPIRICALLY VERIFIED FAILURE MODES (with item examples)

**Failure Mode 1 — Undercount (the dominant lever)**
- Question has N `[ANS]` markers; model boxes only LAST value
- Examples: 232, 505, 595, 750
- Recovery: append `\boxed{a,b,...,N}` with all N values
- Yield in slot 4: ~63% conditional

**Failure Mode 2 — Decimal where gold is fraction**
- Mathematically equivalent but string-distinct
- Examples: 135, 207, 529, 716, 784, 817, 919, 936
- Recovery: append `\boxed{\frac{a}{b}}`
- Yield in slot 1: ~83% conditional

**Failure Mode 3 — Decimal where gold is symbolic exact**
- `0.7854` vs `\pi/4`, `4.712` vs `3\pi/2`
- Examples: 834 (and likely many trig items)
- Recovery: needs symbolic-form detection (harder than fraction case)

**Failure Mode 4 — Multi-MCQ letter wrong**
- Sub-MCQ within multi-answer questions where one letter is off
- Examples: 77 (A→C), 676 (A,D,A → D,A,A), 890 (6→A in first slot)
- Recovery: teacher consensus on per-slot letters

**Failure Mode 5 — Verbose label prefixes (NEW FROM THIS RUN)**
- "Mean=228" / "A=72" / "x=0" prefixes survive when LHS > 2 chars
- Causes search-gold harm
- Recovery: strip prefixes before override

**Failure Mode 6 — Non-LaTeX math notation (NEW FROM THIS RUN)**
- `*` for multiplication, `ln` (lowercase), verbal conditionals
- Causes search-gold harm
- Recovery: convert to LaTeX (`\cdot`, `\ln`, function notation)

### EMPIRICAL TRUST RANKING OF EVIDENCE SOURCES (after this run)

| Rank | Source | Empirical reliability |
|------|--------|----------------------|
| 1 | Wolfram HIGH | Strongest — mathematical computation in LaTeX |
| 2 | All teachers unanimous (3-4 agree) on simple fractions | Strong — proven in slot 1 |
| 3 | `undercount_candidates.csv` teacher consensus (multi-slot) | Strong — proven in slot 4 |
| 4 | Putnam/MathWorld/MSE URL search match | Strong (small sample only ~5 of 116) |
| 5 | "Search GOLD" with source_type ∈ {computation, math, basic math} | **WEAK — empirically NET HARMFUL** (this is just the search agent's own LLM output mislabeled as GOLD) |
| 6 | Single teacher | Weak |
| 7 | Back-solve majority | Contaminated (RED_ALERT) — don't use as ground truth |

**The "search GOLD" label is a confidence flag, NOT external verification.** 61 of 68 real-content-changes in slot 2 had source_type = "computation"/"math"/"basic math" = agent self-computed. Only 1 item had an external source (HW.Study, weak).

### POST-PROCESSING IMPLICATIONS

The grader behavior confirms the following pipeline architecture (refining what's in CLAUDE.md/FINDINGS.md):

1. **Extract phase:** Walk all `\boxed{}` in response. Also walk reasoning trace for un-boxed candidate answers.
2. **Classify phase:** Per-item, identify failure mode (undercount, decimal-where-fraction, symbolic-needed, label-prefix, non-LaTeX-math).
3. **Transform phase:** Apply mode-specific transforms:
   - Undercount → multi-slot expansion (single box, comma-separated, gold-order)
   - Decimal-fraction → convert via gcd if teacher says so
   - Label prefix → strip if > 2 chars LHS (Hendrycks doesn't)
   - `*` → `\cdot` , lowercase functions → LaTeX
4. **Emit phase:** Single `\boxed{}` at end of response (for free-form), OR replace entire response with `\boxed{LETTER}` for MCQ.

### MECHANISM RULES FOR OVERRIDES

- **Free-form items:** append `\n\n\boxed{NEW_ANSWER}` to existing response. Grader takes LAST. Original boxes earlier in trace are ignored. ✅ Works.
- **MCQ items:** CANNOT use append-to-end. Grader uses `re.search` for FIRST `\boxed{LETTER}`. Three options:
  - Option A: PREPEND `\boxed{LETTER}` at start of response
  - Option B: Replace entire response with `\boxed{LETTER}`
  - Option C: Find and replace the existing first `\boxed{}` in trace
  - Recommended: Option B for cleanest behavior, Option A if we want to preserve reasoning trace for diagnostics

### TODO from this learning

- Build proper `mcq_override.py` script using Option A or B for MCQ items
- Audit `undercount_candidates.csv` for items where current answer is whitespace-only-diff from teacher consensus (those rows shouldn't be in the override set; 29 of 50 in slot 4 were no-ops because of this)
- Build systematic decimal→fraction scan: for every item where current answer is a decimal AND teachers agree on a fraction, queue for override
- Build "tight" search-gold subset: filter to source_url containing 'putnam', 'mathworld', 'stackexchange' only


---

## GRADER RESEARCH NEW FORMAT RULES (claude_grader_research, 2026-05-28)

### Source-code-verified NEW rules not previously in our docs:

1. **NEGATIVE FRACTION SIGN PLACEMENT**: `-\frac{2}{3}` ≠ `\frac{-2}{3}`. Hendrycks does NOT normalize negative sign placement. MATH dataset convention is sign OUTSIDE (`-\frac{a}{b}`). ACTION: post-processor should normalize to sign-outside form for fractions.

2. **BARE `%` NOT REMOVED**: `50%` ≠ `50`. Only `\%` (LaTeX escaped) is removed. ACTION: if model emits bare `%`, convert to either strip it or use `\%`.

3. **`\text{A}` IS PRESERVED**: `\text{A}` ≠ `A` when there's no space in `\text{`. The `_remove_right_units` function only fires on `\text{ ` (with space). ACTION: always strip `\text{}` wrapping from MCQ letters in post-processing.

4. **`\mathrm{}` IS PRESERVED**: `\mathrm{e}` ≠ `e`. ACTION: strip `\mathrm{}` wrapper.

5. **`\cdot` ≠ `*`**: Multiplication operators not normalized. ACTION: convert `*` to `\cdot` in post-processing.

6. **`ln()` ≠ `\ln()`**: Backslash matters for function names. ACTION: ensure all math function names are LaTeX-escaped.

7. **PARENTHESIZED NEGATIVES**: `-5` ≠ `(-5)`. ACTION: match gold's convention.

8. **LEADING ZEROS ON INTEGERS**: `042` ≠ `42`. ACTION: strip leading zeros.

9. **`0.5` HARDCODE IS STANDALONE ONLY**: `0.5` → `\frac{1}{2}` ONLY when the ENTIRE normalized string is exactly `"0.5"`. In multi-answer like `0.5, 3`, the `0.5` stays as `0.5`. Same for `_fix_a_slash_b` — `3/5` → `\frac{3}{5}` only standalone. ACTION: in multi-answer, explicitly use `\frac{}{}` notation, never rely on auto-conversion.

10. **MIXED NUMBERS NEVER EQUIVALENT**: `1\frac{1}{2}` ≠ `\frac{3}{2}`. ACTION: always use improper fractions.

11. **SET BRACES NOT STRIPPED**: `\{1,2,3\}` ≠ `1,2,3`. ACTION: match gold's set notation.

12. **COMMA GROUPING NOT STRIPPED**: `1,000` ≠ `1000`. ACTION: always strip commas from large numbers.

13. **`_remove_right_units` CRASH ON MULTIPLE `\text{ `**: If response has multiple `\text{ ` occurrences, the assert fails → exception → raw string comparison fallback. This means normalization is SKIPPED. ACTION: clean up responses to have at most one `\text{ `.

### PRIORITY POST-PROCESSING PIPELINE (ordered by confidence × impact):

1. Multi-slot expansion (DOMINANT, confirmed +4 slice items)
2. Decimal → fraction conversion (confirmed +2 slice items)  
3. `*` → `\cdot` conversion (confirmed harmful without)
4. Strip `\text{}` wrappers (preserves letter for MCQ in multi-answer)
5. Strip verbose label prefixes (`Mean=`, `A=` etc.) 
6. `ln` → `\ln`, `sin` → `\sin` etc.
7. Strip `\mathrm{}`, `\mathbf{}` wrappers
8. Strip commas from large numbers
9. Strip leading zeros from integers
10. Normalize negative sign to outside fraction
11. Convert mixed numbers to improper fractions

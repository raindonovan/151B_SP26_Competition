# Grader Research Findings — 2026-05-28

**Agent**: claude_grader_research  
**Mission**: Reverse-engineer exact Kaggle grader format from source code + empirical data  
**Source code verified**: `hendrycks/math/modeling/math_equivalence.py` (SHA b5c066f)

---

## 1. VERIFIED SOURCE CODE — `_strip_string` processing order (17 steps)

1. `\n` → `""` (newlines)
2. `\!` → `""` (thin spaces)
3. `\\` → `\` (double backslash → single)
4. `tfrac`/`dfrac` → `frac` (plain substring replace)
5. `\left`/`\right` → `""` 
6. `^{\circ}`/`^\circ` → `""`
7. `\$` → `""`
8. `_remove_right_units` — strips `\text{ unit}` (space before content required)
9. `\%` → `""` (bare `%` is NOT removed)
10. Leading zero: `" ."→`" 0."`, `"{."→`"{0."`, string starts with `.` → prepend `0`
11. Equation prefix: if exactly ONE `=` and LHS ≤ 2 chars → strip LHS
12. `_fix_sqrt` — `\sqrt3` → `\sqrt{3}`
13. ALL SPACES removed globally
14. `_fix_fracs` — `\frac12` → `\frac{1}{2}`
15. HARDCODE: exactly `"0.5"` → `"\frac{1}{2}"` (standalone only)
16. `_fix_a_slash_b` — `3/5` → `\frac{3}{5}` (standalone integers only)
17. Return normalized string; `is_equiv` compares with `==`; exception → raw fallback

## 2. NEW FORMAT RULES (not previously documented)

### 2a. Confirmed via source + empirical testing (40+ test cases)

| # | Rule | Impact |
|---|------|--------|
| L1 | `-\frac{2}{3}` ≠ `\frac{-2}{3}` — negative sign placement not normalized | 1 item in sheet (id=113) |
| L2 | `0.5` hardcode is STANDALONE only — `0.5,3` stays as `0.5,3` | 15 items have 0.5 in multi-answer |
| L3 | `a/b→\frac` is STANDALONE only — `3/5,7` stays as `3/5,7` | 6 items have slash in multi-answer |
| L4 | Bare `%` NOT removed (only `\%` is) | 0 items in sheet |
| L5 | `\text{A}` preserved (no space = no strip) | 6 items including id=725 |
| L6 | `\cdot` ≠ `*` — multiplication operators | 0 items in sheet (7 in junk answers) |
| L7 | `\ln` ≠ `ln` — function backslash matters | 0 items in sheet |
| L8 | `-5` ≠ `(-5)` — parenthesized negatives | 7 items (mostly intervals, not errors) |
| L9 | `042` ≠ `42` — leading zeros on integers | 0 items in sheet |
| L10 | `1\frac{1}{2}` ≠ `\frac{3}{2}` — mixed numbers | 0 items in sheet |
| L11 | `\{1,2,3\}` ≠ `1,2,3` — set braces | 0 items in sheet |
| L12 | `1,000` ≠ `1000` — comma grouping | 0 genuine items in sheet |
| L13 | Multiple `\text{ ` crashes normalization → raw string fallback | Edge case |

### 2b. CRITICAL: WeBWorK items use `a/b` gold, NOT `\frac{a}{b}`

Items 137, 530, 833 have question text explicitly saying "enter as a/b". ALL teachers agree on slash format. The gold is almost certainly `a/b`. Converting to `\frac{}{}` would BREAK the match because `_fix_a_slash_b` doesn't fire in multi-answer.

**Affected items (DO NOT convert to \frac):**
- id=137: `2/13,2/1` — CORRECT as-is
- id=530: `8/9,7/9,5` — CORRECT as-is  
- id=833: `-19/3,3/4,48/6,40/3` — CORRECT as-is
- id=27: `1/3,2/3,7/6,11/6` — likely correct as-is (WeBWorK source)

### 2c. `\text{A}` in item 725 likely costs a point

Answer `41.30,13.28,\text{A}` — the MCQ letter is wrapped in `\text{}`. Hendrycks will NOT strip it. If gold has bare `A`, this is a free point to recover by stripping the wrapper.

## 3. EXTRACTION PIPELINE ASYMMETRY (MCQ vs free-form)

| Item type | Extraction | Override mechanism |
|-----------|------------|--------------------|
| MCQ | FIRST `\boxed{LETTER}` via `re.search` | Must PREPEND or REPLACE (append = no-op) |
| Free-form | LAST `\boxed{...}` via `rfind` | Append works |

Empirically confirmed: 25_08 Slot 3 (26 MCQ appends) = exact 0.692 = no change.

## 4. MATH-VERIFY vs HENDRYCKS DELTA

Math-Verify (HuggingFace) uses SymPy and handles fraction↔decimal, symbolic↔numeric, interval↔inequality, set comparison. Our 80% format-loss confirms we are NOT using Math-Verify.

## 5. AIMO WINNERS AVOIDED FORMAT ISSUES

Both AIMO PP1 (Numina) and PP2 (NemoSkills) used integer-only answers to dodge LaTeX equivalence entirely. CSE 151B's mixed format makes this impossible.

## 6. NORMALIZATION AUDIT OF 943 ANSWERS

- 83/943 changed by `_strip_string`
- 19 non-whitespace changes — ALL auto-handled (\\%, equation prefix, \\left/\\right, \\$, ^\\circ, standalone slash)
- 0 items with: bare %, \\mathrm{}, \\mathbf{}, bare ln, mixed numbers
- Format rules L4-L12 are theoretical risks confirmed absent from current answer sheet
- They matter for future post-processing of raw model outputs

## 7. PRIORITY POST-PROCESSING PIPELINE

1. Multi-slot expansion (DOMINANT, confirmed +4 slice items)
2. Decimal→fraction for MATH-sourced items (confirmed +2 slice items)
3. `\text{A}` → bare `A` in multi-answer MCQ slots
4. `*` → `\cdot` in raw model outputs
5. Strip verbose label prefixes (`Mean=`, `A=` etc.)
6. `ln` → `\ln`, `sin` → `\sin` in raw outputs
7. Strip `\mathrm{}`, `\mathbf{}` wrappers
8. Strip commas from large numbers
9. Strip leading zeros from integers
10. Normalize negative sign to outside fraction
11. Convert mixed numbers to improper fractions
12. MCQ overrides: use prepend/replace, NOT append

## 8. KNOW / SUSPECT / DON'T KNOW

### KNOW (source-code + empirically verified):
1-17: Full `_strip_string` behavior (see §1)  
18: MCQ = first box, free-form = last box  
19: All equivalences and non-equivalences in §2

### SUSPECT:
- Server-side grader = same Hendrycks code (Piazza + source align)
- Gold follows MATH dataset conventions (fractions for rationals, exact forms for symbolic)
- Gold negative fractions use sign-outside (`-\frac{a}{b}`)
- WeBWorK items use `a/b` gold format

### DON'T KNOW:
- Exact server-side source (could be a fork)
- Which items are in ~283 public LB slice
- Per-item gold labels
- Whether gold uses trailing zeros on WeBWorK items
- Per-item source corpus (AIME vs MATH vs WeBWorK vs custom)

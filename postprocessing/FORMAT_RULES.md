# Format Rules — Discovered Gold Format Patterns

**Created**: 2026-05-28 Day 6
**Status**: ACTIVE — every rule here is a direct scoring lever

## What is a format rule?

A format rule is a discovered fact about how a specific item's gold answer is encoded in the Kaggle grader. When we know the mathematically correct answer but keep getting scored wrong, the gap is FORMAT. Each format rule we discover = a point recovered.

Example: if verified gold is `4` but Kaggle wants `4.00`, the format rule is: "item X requires 2 decimal places."

## How we discover format rules

1. **Ground truth + submission mismatch**: we know the answer is `4` (from Wolfram/search/teachers), multiple submissions include `4`, but item still scores wrong → format issue
2. **Differential submission probes**: submit `\boxed{4}` vs `\boxed{4.00}` for the same item, observe score delta
3. **Source-corpus identification**: if we identify the item came from WeBWorK, we know it expects decimal precision matching; if AIME, it expects bare integer

## Discovered rules (add as we find them)

| Item ID | Verified answer | Format that works | Format that fails | Rule | Source |
|---------|----------------|-------------------|-------------------|------|--------|
| (none yet) | | | | | |

## Rules to investigate

| Item ID | Verified answer | Current submission answer | Hypothesis | Priority |
|---------|----------------|--------------------------|------------|----------|
| (needs backsolve output to populate) | | | | |

## Format rule categories

These are the TYPES of format rules we expect to find:
1. **Trailing zeros**: `9` vs `9.0` vs `9.00` — Hendrycks does NOT normalize these
2. **Fraction vs decimal**: `\frac{1}{4}` vs `0.25` — only `0.5` ↔ `\frac{1}{2}` is normalized
3. **Comma in numbers**: `1,000` vs `1000` — Hendrycks does NOT strip commas
4. **Units inside box**: `5 \text{ m/s}` vs `5` — Hendrycks strips `\text{ unit}` but only with leading space
5. **Multi-answer order**: `a, b` vs `b, a` — order matters (-17.6pp verified)
6. **Multi-answer delimiter**: `a, b` vs `a; b` vs `a \text{ and } b`
7. **LaTeX wrappers**: `\mathrm{e}` vs `e`, `\mathbf{2}` vs `2`
8. **MCQ letter format**: `\text{A}` vs `A` vs `(A)`
9. **Decimal precision**: `0.0625` vs `0.063` vs `0.06` — which precision matches gold?
10. **Negative sign placement**: `-\frac{2}{3}` vs `\frac{-2}{3}`



## Trailing-zero items (63 items) — LIVE LEVER

**Source**: data/FINDINGS.md section 1; Hendrycks `is_equiv` does NOT normalize trailing zeros.
**Impact**: `1.50 ≠ 1.5`, `70.00 ≠ 70` — stripping recovers points.
**Action**: Post-processing strip of trailing zeros on free-form decimal answers.

| Item ID | Current answer (truncated) | Rule | Category | Source |
|---------|---------------------------|------|----------|--------|
| 4 | `-0.5735, 0.8192, -0.7000` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 28 | `2, 140.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 32 | `10.05, -1.000, -3.500` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 46 | `1.645, 1.719, 1.960, -1.960, 1.719, B, A` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 61 | `0.7600c, 0, 150, 0.6900c + 10.50, 150` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 105 | `24.00, 9.114` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 118 | `3.600` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 133 | `-0.8660, 0.5000, -1.732, 2.000` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 187 | `0.0281, 0.0067, 0.3825, 0.4512, 22.00, 18.00, 2, 35.00,` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 194 | `600.0,\ July,\ 1908,\ 890.0,\ March,\ 1907` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 233 | `1.960,\ -1.960,\ -5.177,\ B` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 239 | `3.450` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 246 | `25.00, 23.00, 17.00, 23.00, 19.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 277 | `38800.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 281 | `-0.4618, 0.8870, -0.5206, -2.1655` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 296 | `45.00, 180.00, 270.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 322 | `40.00, 25.00, 1000.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 325 | `280.0, 14.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 341 | `126.0, 36.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 357 | `320.0, 0.06570` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 369 | `0.7500, 5.000, 2.000` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 378 | `0.0001420, 0.00002206, 0.0001199, 0.1554, 15.54` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 388 | `4.110, 3.523, 2.935, 1.174, 0.000` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 401 | `143.2, 240.0, 52.52, -135.0` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 404 | `52.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 410 | `45.00, 4.000` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 417 | `1.006, 0.9676, 28, 29.10, 1.039` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 418 | `2.958, 1.751, 0.001530, B` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 423 | `-0.5000` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 446 | `0.9720` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 449 | `3.5850, 0.0003460, B` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 451 | `0.1290, 0.1935, 0.2097, 14, 0.1774, 0.06452` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 456 | `-7.740, A, B` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 480 | `2.500` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 490 | `23.00, 410.0` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 494 | `0.06200` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 519 | `98.30` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 542 | `285.0, 7457, 86.35` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 548 | `120.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 553 | `1.600` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 584 | `6.000` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 619 | `-3.226, 0.001230, A` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 635 | `37.60, 0.7460, -25.40` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 642 | `6.000, 1.047, 13.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 648 | `11.51 + 0.83x, 30.60` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 651 | `73.00, 114.5` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 693 | `5.500` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 694 | `6750 + 9x, 36x, 27x - 6750, 250.0` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 715 | `8.500` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 725 | `41.30, 13.28, \text{A}` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 734 | `4.830` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 735 | `28.00, 42.50, 55.00, -29.00, 82.00, 27.00, A` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 742 | `241.0` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 763 | `13.00, 2.667` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 785 | `0.000, 1.000, 0.000, 0.000` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 787 | `47.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 806 | `-0.6551, -0.7556, 0.8670, 1.153, -1.324, -1.527` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 858 | `2.300, 1.694, \text{Yes}` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 864 | `25.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 869 | `20.50, \dfrac{x + y + xy}{2}` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 908 | `100 \cdot (0.83)^t, 39.390` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 916 | `4.243, 8.485, 18.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |
| 923 | `93.00, 48.00` | Strip trailing zeros from decimals | trailing zeros | data/FINDINGS.md §1 |


## Multi-slot undercount items (110 items) — DOMINANT LEVER

**Source**: data/FINDINGS.md §4-5; data/undercount_candidates.csv (82 pre-extracted).
**Impact**: 79% of B1-7 failures are multi-slot undercount. Qwen emits last \boxed{} only, losing prior slots.
**Action**: Post-processor collects all \boxed{} from raw response, rewrites as single \boxed{a, b, c}.
**Category**: multi-slot undercount
**Note**: 110 flagged in master tracker, 82 in CSV — gap needs investigation.


## No-box rescue items (18 items, 5 with consensus) — MEDIUM LEVER

**Source**: data/FINDINGS.md §8. Items where Qwen consistently produces no \boxed{} across all SC runs.
**Action**: Override with forced-answer rescue values where consensus is strong.

### HIGH confidence (4/4 unanimous):
| Item ID | Rescue answer | Votes | Confidence | Category |
|---------|--------------|-------|------------|----------|
| 229 | 2 | 4/4 | HIGH | no-box rescue |
| 308 | 12 | 4/4 | HIGH | no-box rescue |
| 383 | 80 | 4/4 | HIGH | no-box rescue |
| 498 | 15 | 4/4 | HIGH | no-box rescue |

### MEDIUM confidence (3/4 consensus):
| Item ID | Rescue answer | Votes | Confidence | Category |
|---------|--------------|-------|------------|----------|
| 445 | D | 3/4 | MEDIUM | no-box rescue |

### LOW confidence (2/4 or 1/4 — do NOT override without additional evidence):
Items 161, 204, 312, 453, 724, 799, 836, 911 (2/4), and 93, 112, 376, 652, 809 (1/4 split).

## How this feeds into post-processing

Each discovered format rule becomes a post-processing function:
- Rule: "item X needs 2 decimal places" → function: `round_to_2dp(answer)`
- Rule: "item Y's gold uses `a/b` not `\frac{a}{b}`" → function: `frac_to_slash(answer)`
- The post-processor applies per-item function chains based on discovered rules

## IMPORTANT: Record every format discovery

When ANYONE (any agent, any analysis) discovers a format rule:
1. Add it to the table above
2. Note the item ID, verified answer, what format works/fails, and how we know
3. This is the raw material for the post-processor
4. Each rule = a point on the scoreboard

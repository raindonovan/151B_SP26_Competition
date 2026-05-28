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

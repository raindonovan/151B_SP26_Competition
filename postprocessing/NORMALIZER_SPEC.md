# Canonical Normalizer Spec

This document defines the current post-inference normalizer implemented in `postprocessing/scripts/normalizer.py`.

## Goal

Target the competition grader we actually have, not the evaluator we wish we had.

The relevant stack is:

1. Extract the grader-visible answer.
2. Normalize using Hendrycks-style string cleanup.
3. Compare by exact post-normalization string equality.

That is stricter than `math-verify` and stricter than Minerva-style symbolic evaluation. External references reinforce the same conclusion:

- Hendrycks `math_equivalence.py` is a literal normalize-then-compare string matcher.
- Hugging Face `Math-Verify` is much more permissive and symbolic.
- LM Evaluation Harness `minerva_math` now delegates to `math_verify` for tolerant evaluation and is not an accurate model of the Kaggle grader.

Implication: the submission normalizer should imitate Hendrycks-visible behavior, while symbolic tools remain useful for research and offline diagnosis only.

## Why This Exists

Before this file, postprocessing logic was split across:

- `postprocessing/scripts/fix_submission_format.py`
- `postprocessing/scripts/post_filter.py`
- `postprocessing/scripts/apply_grader_normalization.py`

Those scripts covered isolated probes, but not a single auditable pipeline with explicit mode boundaries.

## Evidence Base

The current rule split is grounded in three sources.

### 1. Submission forensics

`submission/SUBMISSION_FORENSICS.md` and related submission analyses showed that grader-visible diffs matter more than raw response diffs, and that structural answer formatting can move leaderboard score even when underlying reasoning is unchanged.

### 2. Early inference runs

The V0 to V3 fixed-50 summaries show prompt wording helped only modestly:

- V0 baseline: 35/50
- V1 counting-top: 36/50
- V2 counting-bookend: 36/50
- V3 shape-filter: 36/50

That is consistent with a pipeline where prompt changes alone are not enough and deterministic postprocessing needs to recover visible-answer failures.

### 3. Repo-wide JSONL scan

A full scan over every stored `inference/results/**/*.jsonl` run sample produced these aggregate counts:

- `samples`: 42,293
- `multi_box`: 16,936
- `multi_boxes_enough_to_consolidate`: 8,417
- `trailing_zero`: 4,003
- `no_box`: 1,675
- `mcq_bare_letter_only`: 503
- `multi_undercount_single_box`: 168
- `comma_number`: 302
- `scientific`: 16

Selected runs show the same pattern:

- V0 fixed-50: 177 multi-box samples, 39 trailing-zero samples, 7 no-box samples
- V3 fixed-50: 202 multi-box samples, 39 trailing-zero samples, 6 no-box samples
- run14b private943: 4,108 multi-box samples, 829 trailing-zero samples, 218 no-box samples

Takeaway: the first-order lever is structural answer recovery, not broad algebraic rewriting.

## Modes

### `conservative`

Use only locked-in structure repair and safe grader-aligned cleanup.

Included:

- MCQ first-letter extraction and canonical `\boxed{LETTER}` rewrite when needed
- last-box extraction for free-form answers
- multi-box consolidation for multi-answer items
- Hendrycks-safe cleanup:
  - `\dfrac` and `\tfrac` to `\frac`
  - `\left` and `\right` stripping
  - thin-space and inverse-space stripping
  - `%`, degree, short `x=` / `k=` prefix cleanup
  - `\sqrt3 -> \sqrt{3}`
  - integer slash fraction cleanup like `3/5 -> \frac{3}{5}`
  - exact `0.5 -> \frac{1}{2}`
- per-item overrides from `postprocessing/per_item_overrides.csv`

Not included:

- blanket decimal-to-fraction promotion
- trailing-zero stripping
- scientific-notation expansion
- wrapper stripping like `\mathbf{}` / `\mathrm{}`
- multi-char prefix stripping like `Mean=`

Use this when the priority is minimizing accidental score loss.

### `default`

`default` includes everything in `conservative`, plus evidence-backed fraction promotion when metadata supports it.

The current implementation promotes a decimal answer to a fractional target only when answer-sheet metadata strongly suggests the item wants that exact fraction, for example:

- `sheet_best_answer` is fractional, and
- teacher metadata agrees, or the sheet tier/confidence is strong enough.

This is deliberately narrower than a blanket decimal-to-fraction rule.

### `aggressive`

`aggressive` includes `default`, plus medium-confidence formatting rewrites.

Included:

- trailing-zero stripping
- numeric thousands-comma stripping
- `\mathrm{}` / `\mathbf{}` wrapper stripping
- multi-char prefix stripping such as `Mean=228`
- scientific notation expansion
- source-routing heuristics from prompt text
- broad decimal-to-fraction conversion only when the prompt suggests a fractional target

The aggressive mode is intentionally heuristic. It is for targeted probes, ablations, or high-conviction final-sheet builds, not blind default deployment.

## Pipeline Shape

For a single response:

1. Extract the visible answer.
2. Classify the item as `MCQ`, `free_single`, or `free_multi`.
3. Apply universal cleanup.
4. Apply type-specific normalization.
5. Apply per-item overrides.
6. Re-emit a canonical final answer box.

## CLI

Main entry point:

```bash
python3 postprocessing/scripts/normalizer.py INPUT.csv OUTPUT.csv --mode default
```

Useful flags:

- `--items private.jsonl`
- `--master-answers data/MASTER_ANSWERS.csv`
- `--overrides postprocessing/per_item_overrides.csv`
- `--report postprocessing/results/normalizer_report.json`

The script expects an input CSV with at least `id,response` columns.

## Testing System

There are now three layers.

### 1. Unit tests

`tests/test_normalizer.py` checks:

- Hendrycks-local extraction behavior
- MCQ rescue and rewrite behavior
- multi-answer consolidation
- metadata-backed fraction promotion
- aggressive wrapper / prefix cleanup
- per-item override handling

### 2. Fixture harness

`postprocessing/scripts/evaluate_normalizer.py` runs the normalizer against `testing/tier1_ground_truth.csv` and reports:

- raw grader-visible matches
- normalized matches
- number of improved cases

Current seed fixture results:

- `conservative`: 4/6 normalized matches, +1 improvement over raw
- `default`: 4/6 normalized matches, +1 improvement over raw
- `aggressive`: 5/6 normalized matches, +2 improvements over raw

### 3. Real-pipeline reports

The CLI can emit a JSON report with per-row flags. That is intended for auditing any submission build before use.

## Overrides

`postprocessing/per_item_overrides.csv` is the explicit escape hatch for rare or high-conviction cases.

Supported override types today:

- `force_value`
- `force_fraction`
- `force_decimal_places`
- `force_units`
- `custom`

Overrides should only be added with evidence and a note in the `evidence` column.

## Current Limitations

- The fixture sheet is still small and should grow.
- The normalizer currently operates on submission CSVs, not directly on full SC JSONL runs.
- Source-routing heuristics are intentionally conservative and incomplete.
- The aggressive tier is implemented, but not yet justified for blanket final submission use.

## Recommended Current Use

- Use `conservative` when you want the lowest-risk cleanup.
- Use `default` for normal answer-sheet builds with sheet metadata available.
- Use `aggressive` only for targeted comparisons, not as an unquestioned final default.

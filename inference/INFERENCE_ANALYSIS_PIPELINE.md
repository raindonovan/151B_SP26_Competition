# Inference Analysis Pipeline

> **Grader (2026-05-30):** canonical grader = `grading/grader.py` (`Grader`) — value-equality, our Kaggle mirror. "judger" is legacy; the strict Hendrycks `kaggle_like_is_equiv` is DEPRECATED (mirrors the retired strict grader). See `grading/grader.py`.

This is the pipeline to use before manually reviewing a 943-item inference run for submission decisions.

It is designed for the real question you care about:

1. Did Qwen get the math right according to the strongest evidence we have?
2. After normalization, is the answer still sound and more Kaggle-safe?

It is not designed to pretend we have true private-set labels.

## What to do before starting the pass

### 1. Freeze the equivalence engine

Use `grading/judger.py` as the canonical local import surface.

Important role split:

- `Judger` is for local extraction/diagnostics and public-set style evaluation.
- `kaggle_like_is_equiv` is the grading-phase helper for Hendrycks-style string equivalence checks against surrogate gold.

Do not treat the local judger as proof of private-set correctness.

### 2. Freeze the post-inference normalizer mode

Use `postprocessing/scripts/normalizer.py` in `conservative` or `default` mode for the analysis pass.

Recommended default for review:

- `default` when you want metadata-backed fraction promotion
- `conservative` when you want only structural and clearly safe cleanup

Avoid leading with `aggressive` unless the item is already in manual review.

### 3. Freeze the surrogate-gold hierarchy

Use this source priority when deciding whether Qwen got the math right:

1. `wolfram_answer` with `HIGH` confidence
2. unanimous teacher agreement
3. high-confidence answer sheet (`sheet_tier` 1 or 2 and `sheet_confidence >= 80`)
4. high-confidence backsolve answer
5. low-confidence answer sheet fallback

If the chosen surrogate answer is clearly junk or explanation text, do not let it drive the item decision.

### 4. Sanity-check tracker metadata

Before trusting tracker-derived answers, remember:

- `master_item_tracker.csv` may contain dirty `best_answer` cells
- `undercount` flags are high-value
- `backsolve_disagree` is weaker
- unflagged items are usually lower-EV to review first

### 5. Decide the review order

High priority first:

1. `undercount`
2. `mcq_not_letter`
3. `no_box_item`
4. direct disagreement with strong surrogate gold

Medium priority:

1. `disagree_teacher`
2. `format_only_diff_teacher`

Low priority:

1. `backsolve_disagree` only
2. completely unflagged items with no strong conflicting evidence

## Per-run review flow

### A. Extract the run answer surface

For single-sample runs, use the raw `response`.

For SC runs:

- start with `voted_answer` as the analysis surface
- if an item becomes interesting, drill into the sample bundle for structural recovery and no-box review

### B. Normalize the answer

Run the chosen normalizer mode and record:

- extracted raw candidate
- normalized candidate
- item type
- normalizer flags

### C. Compare against surrogate gold

Use `grading.judger.kaggle_like_is_equiv` for free-form equivalence and exact letter comparison for MCQ.

Track both:

- raw answer vs surrogate gold
- normalized answer vs surrogate gold

### D. Bucket the item

Use these buckets:

- `SUBMIT_AS_IS`
- `SUBMIT_NORMALIZED`
- `SUBMIT_NORMALIZED_UNDERCOUNT`
- `MANUAL_UNDERCOUNT_REVIEW`
- `MANUAL_LOW_CONF_SURROGATE`
- `MANUAL_NO_SURROGATE`
- `HOLD`

### E. Only then do manual analysis

Manual effort should go to items where normalization or strong evidence actually changes the decision.

## Script

Use:

```bash
python3 inference/scripts/build_review_sheet.py \
  --run-jsonl inference/results/YOUR_RUN.jsonl \
  --output-csv inference/runs/review/YOUR_RUN.review.csv \
  --mode default
```

The script merges:

- `private.jsonl`
- `data/MASTER_ANSWERS.csv`
- `data/master_item_tracker.csv`
- the chosen run JSONL

and emits one review row per item with:

- raw candidate
- normalized candidate
- surrogate gold + source quality
- tracker flags
- raw/normalized equivalence outcomes
- recommended action

## Why this is the right flow

It avoids the two big mistakes that burned time earlier:

1. treating the local judger as private-set truth
2. reviewing raw Qwen answers without first separating math correctness from surface formatting

This pipeline keeps those questions separate:

- surrogate gold asks whether the math is believed correct
- normalization asks whether the answer is submit-safe

That is the right framing for endgame inference analysis.
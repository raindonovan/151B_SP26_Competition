# testing/backsolve/CLAUDE.md — Backsolve Oracle Mining Agent

> **FIRST: Ask Rain for the GitHub PAT.**

## Identity
You are a backsolve analysis agent for the CSE 151B Kaggle math competition. Your job: mine 29 past submissions and their Kaggle scores to infer (1) which ~283 items are in the Kaggle test subset, and (2) what the gold answers are for those items.

## The problem
Kaggle scores each submission on a FIXED UNKNOWN subset T of ~283 items (30% of 943). For submission i with score s_i: s_i = (1/|T|) * sum_{j in T} match(sub_i[j], gold_j). We have 29 such equations. Solve for T and gold.

## Data
- 29 submission CSVs: submission/csvs/*.csv
- 29 Kaggle scores: submission/REGISTRY.md
- MASTER_ANSWERS.csv: data/MASTER_ANSWERS.csv (all evidence per item)
- Verified gold: ~148 items (60 search + 66 Wolfram + 22 T1)
- private.jsonl: 943 items with metadata

## Three methods (do in order)

### Method 1: Verified-item triangulation
For items where we KNOW the gold (search/Wolfram/T1): check each submission against known gold, count matches, see how many of these known-correct items are consistent with each score. Bounds test set membership.

### Method 2: Pairwise differential
For each submission pair (i,k): find D = items that differ. Score delta * |T| = net flips in D intersect T. Small D + measurable delta = strong signal. Find pairs with few differences.

### Method 3: Per-item regression
For each item: group submissions by answer, compute avg score per group. Items in test set show correlation between answer quality and score. Solve as constrained binary regression.

## Output (write to testing/backsolve/)
- test_set_probabilities.csv: item_id, p_in_test_set, confidence
- gold_inferences.csv: item_id, inferred_gold, confidence, evidence
- pairwise_analysis.csv: sub_pair, n_diffs, delta, items_identified
- ANALYSIS.md: narrative findings

## Constraints
- |T| approx 283 (exact size unknown)
- Score resolution 0.001 (3 decimal places)
- 1/283 = 0.00354 per item
- Accuracy metric = discrete, less info than log-loss
- Hendrycks is_equiv for matching (see grading/GRADER_SPEC.md)

## Read first
- This file, submission/REGISTRY.md, data/MASTER_ANSWERS.csv
- submission/BACKSOLVE_RESEARCH.md, grading/GRADER_SPEC.md, root CLAUDE.md

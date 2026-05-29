# testing/backsolve/CLAUDE.md — Backsolve Oracle Mining Agent

> **FIRST**: if you need write access, see CREDENTIALS RULE in root `CLAUDE.md`. Chat-based Claudes ask Rain at session start; persistent runtimes use pre-configured `~/.git-credentials`.

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

## AMBER ALERT: Format-aware comparison (CRITICAL)

When building the 29×943 answer matrix, you MUST compare answers the same way the Kaggle grader does. This means applying Hendrycks _strip_string normalization BEFORE comparison.

**The problem**: submission 14 might have `\boxed{9.0}` and submission 2 might have `\boxed{9}`. If you compare raw strings, these look "different." But if the grader normalizes trailing zeros, they're IDENTICAL to Kaggle — and any score difference between submissions 14 and 2 has NOTHING to do with this item.

**What to do**:
1. Extract last `\boxed{}` content from each submission response
2. Apply Hendrycks normalization (strip whitespace, dfrac→frac, \left/\right removal, etc.)
3. THEN compare. Two answers are "same" only if their normalized forms match.
4. See `grading/GRADER_SPEC.md` Section 4 for exact normalization rules.

**But also flag format-suspects**: if the RAW answers differ but NORMALIZED answers match (e.g., `9.0` vs `9` both normalize to `9`), that's fine — they're the same to the grader. But if normalized answers match our verified gold BUT the item still scores wrong across submissions, FLAG IT — the gold format might differ from what we think (e.g., gold is actually `9.00` with trailing zeros).

These flags go to `postprocessing/FORMAT_RULES.md` as format rule candidates.

## Role & Relevance

**Role**: Mine past submission scores to infer which items are in the test set (~283 LB subset) and what the gold answers are.
**Relevance**: Each past submission is a query to an accuracy oracle. With 29 submissions, we have ~232 bits of information about the test set. Mining this data reveals per-item gold answers (direct scoring lever) and test set membership (enables local eval harness).
**Techniques**: Pairwise differential analysis (compare submission pairs that differ on few items), verified-item triangulation (use known gold to isolate membership), per-item regression (correlate answer variants with score changes), Bayesian posterior inference.
**Inputs**: 29 submission CSVs + Kaggle scores, MASTER_ANSWERS.csv, verified gold from search/Wolfram.
**Outputs**: test_set_probabilities.csv, gold_inferences.csv, pairwise_analysis.csv.
**Key lever**: Every inferred gold answer expands our gold set. Gold answers help on the FINAL test set (all 943), not just the LB subset.

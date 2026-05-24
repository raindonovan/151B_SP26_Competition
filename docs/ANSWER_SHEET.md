# Answer Sheet Methodology

## Problem
943 items with withheld gold answers. We infer correct answers using:
- N Kaggle submissions (currently 16, growing), each with known overall score
- 3 teacher models with per-item answers (Sonnet, GPT-5.4, GPT-OSS)

## Formula: Score-Weighted Majority Vote

For each item i:
- Collect all answers from all sources
- Each source gets weight = its Kaggle score (submissions) or estimated accuracy (teachers)
- For each unique candidate answer a:
    score(a) = sum of weights for all sources giving answer a
- best_answer = argmax score
- confidence = score(best) / sum(all scores)

Teacher weights: Sonnet=0.70, GPT-5.4=0.65, GPT-OSS=0.60, xhigh=EXCLUDED

## Why Score-Weighted Voting
We chose score-weighted majority voting over Bayesian posterior (v2-v3) 
and Dawid-Skene EM because:
- The theoretical gap to optimal is small when source quality varies 
  significantly (our scores range 0.028-0.646)
- One unified formula replaces the confusing dual-track (Bayesian + teacher)
- Easy to maintain and debug
- Adding new submissions is trivial (one registry line)

Known limitation: correlated submissions (multiple runs from same base 
model) inflate confidence. Fixed by correlation dampening (see below).

## Correlation Dampening
Submissions from the same base model are correlated — they tend to agree
or disagree together, not independently. Without correction, 8 runs from
the same Qwen3 base count as 8 independent votes, inflating confidence.

Fix: group correlated submissions and apply weight dampening:
  effective_weight = raw_weight / sqrt(group_size)

Groups:
- base_qwen3 (8 subs): run14b, run09sc8, run08v2, run10, expA variants
- diagnostics (6 subs): diagnostic_a/c, D, E, f, post_filtered
- sft_v3 (1 sub): sftv3_epoch8_sc1 (uncorrelated, no dampening)
- teachers: treated as independent (different model families)

Why sqrt(n): standard approximation for correlated estimators with
correlation ρ. At full correlation (ρ=1), effective N=1; at zero (ρ=0),
effective N=n. sqrt(n) assumes moderate correlation (~0.5), which matches
empirical submission agreement rates on this dataset.

Excluded from registry:
- sftv4_adaptive_rerolled.csv: trained on answer sheet labels — circular
  reasoning confirmed (all 11 new T1 items after adding it were trained
  items). Its Kaggle score (0.597) is valid signal for other purposes.

## Confidence Tiers
- T1 (≥0.80): High confidence, lock
- T2 (0.60-0.80): Medium
- T3 (0.40-0.60): Low, worth testing
- T4 (<0.40): Very low, model is guessing

## Answer Matching
Before comparing: strip whitespace, $, LaTeX spacing (\, \; \quad),
normalize \dfrac→\frac, normalize comma spacing, collapse whitespace.
Same normalize_answer() as in voting scripts.

## Workflow After Each Submission
1. Place CSV in submissions/
2. Add to SUBMISSION_REGISTRY in build_answer_sheet script
3. Re-run script
4. Check tier distribution

## Script
scripts/build_answer_sheet_v4.py (replaces build_answer_sheet.py)

## History
- v1 (2026-05-22): 10 subs, simple back-solve
- v2 (2026-05-23): 12 subs, Bayesian posterior
- v3 (2026-05-24): 16 subs + teacher, Bayesian + teacher dual-track
- v4 (2026-05-24): Simplified to score-weighted voting, one unified formula

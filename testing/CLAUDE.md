# testing/CLAUDE.md — Testing & Validation Agent

> **FIRST: Ask Rain for the GitHub PAT.**

## Identity
You are a testing and validation agent for the CSE 151B Kaggle math competition. You build and run the local test harness that validates pipeline outputs before Kaggle submission.

## Your task scope
- Maintain the local test/validation set (back-solved gold answers)
- Run pipeline outputs against the validation set
- Compare adapter outputs to gold
- Validate post-processing transformations
- Provide go/no-go signal before burning a submission slot

## Key insight
The ~283-item Kaggle test subset can be partially reconstructed via back-solve oracle.
These items become a **validation set** — NOT a training set.
- Train adapter on OTHER verified-wrong items
- Validate adapter on back-solved test items
- If adapter improves score on validation set → safe to submit to Kaggle

## Data in this folder
- `gold_validation_set.csv` — back-solved items with known gold answers (TO BUILD)
- `test_results/` — per-run validation results
- `validation_reports/` — comparison reports

## Read these first
- `submission/BACKSOLVE_RESEARCH.md` — how we extract gold from Kaggle scores
- `strategy/TEST_PIPELINE.md` — the north star pipeline
- `grading/GRADER_SPEC.md` — grader behavior
- Root `CLAUDE.md` — universal rules

## Validation workflow
1. Load gold validation set (back-solved items with known answers)
2. Run pipeline output through post-processing
3. Compare to gold using Hendrycks is_equiv normalization
4. Report: per-item pass/fail, aggregate accuracy, delta from previous run
5. Flag items where format-fix would rescue a correct answer

## Critical: adapter train/validation split
- **Training set**: items Qwen gets wrong, with verified gold from teachers/Wolfram/search (NOT from back-solve)
- **Validation set**: back-solved test subset items (these are what Kaggle actually scores)
- NEVER train on validation items — that would overfit to the test subset

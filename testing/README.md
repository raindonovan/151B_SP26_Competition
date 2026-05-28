# testing/ — Local Test Harness

This folder holds the local validation infrastructure that mirrors Kaggle scoring.

## Purpose
Before burning a submission slot, validate pipeline outputs locally against back-solved gold answers.

## Key files
- `CLAUDE.md` — agent operating doc for testing tasks
- `gold_validation_set.csv` — back-solved items with known gold (TO BUILD)
- `test_results/` — per-run validation outputs
- `validation_reports/` — comparison reports

## The split
- **Validation set** = back-solved Kaggle test subset items (what Kaggle scores on)
- **Training set** (for adapter) = other verified-wrong items (teachers/Wolfram/search gold)
- These sets must NOT overlap — training on validation items = overfitting to test subset

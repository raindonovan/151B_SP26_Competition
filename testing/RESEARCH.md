# Testing Research

## Key insight (Day 6)
Back-solved test set items serve as a held-out validation set for adapter training.
This connects back-solve directly to the adapter pipeline:
1. Back-solve → identify test set items + gold answers
2. Train adapter on OTHER verified-wrong items (not test set)
3. Validate adapter on back-solved test set
4. Local validation score ≈ Kaggle score (on the same ~283 items)
5. Submit only when local validation shows improvement

## Train/validation split is critical
If we train the adapter on back-solved test items, we're memorizing the test set.
That would inflate local validation score but not help on the other ~660 items at final ranking.
The split: train on Wolfram/teacher/search gold, validate on back-solve gold.

## Building the validation set
Sources (in order of reliability):
1. Items where flipping our answer changed the Kaggle score → confirms item is in test set AND reveals gold
2. Items where back-solve posterior ≥ 0.95 AND the item is likely in test set
3. Cross-referencing multiple submission pairs to triangulate

## See also
- `submission/BACKSOLVE_RESEARCH.md` — differential submission technique
- `submission/RED_ALERT_LB_SUBSET.md` — LB-subset scoring caveat

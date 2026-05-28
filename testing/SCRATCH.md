# testing/SCRATCH.md — Unsorted findings, ideas, observations

Drop anything here. Rain will sort it later.

---

- Back-solved test set items = VALIDATION set for adapter (not training). Train on Wolfram/teacher/search gold, validate on back-solve gold. Never overlap.
- If we can identify even 50 items in the test set with known gold, that's a local eval harness with ~18% coverage of what Kaggle tests.
- The backsolve matrix must use Hendrycks-normalized answers, not raw strings. Otherwise format noise corrupts the signal (AMBER ALERT Day 6).

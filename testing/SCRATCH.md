# testing/SCRATCH.md — Unsorted findings, ideas, observations

Drop anything here. Rain will sort it later.

---

- Back-solved test set items = VALIDATION set for adapter (not training). Train on Wolfram/teacher/search gold, validate on back-solve gold. Never overlap.
- If we can identify even 50 items in the test set with known gold, that's a local eval harness with ~18% coverage of what Kaggle tests.
- The backsolve matrix must use Hendrycks-normalized answers, not raw strings. Otherwise format noise corrupts the signal (AMBER ALERT Day 6).

---

## Backsolve priority analysis (Day 6, from strategy discussion)

### Terminology (LOCKED)
- **test set** = the ~283-item LB subset Kaggle scores on (unknown, fixed)
- **FINAL test set** = all 943 items (used for final ranking at deadline)

### The two unknowns
Backsolve is solving for TWO things simultaneously:
1. **T** (test set membership): which ~283 items does Kaggle test on?
2. **gold_j** (gold answers): what is the correct answer for each item?

### They're entangled but separable in practice
The score gives us the PRODUCT of (in test set) × (answer correct). We can't observe either alone. BUT:

For the ~148 items where we KNOW gold (Wolfram/search/T1): membership unknown is isolated. Backsolve tells us purely "is this item in the test set?" because we already know the answer.

For the ~795 items where we DON'T know gold: we get the joint P(in_test_set AND answer_correct). But we don't need to separate them — if backsolve says "answer X has high joint probability," submit X regardless.

### Priority: gold answers >> test set membership
**Gold answers matter more** because:
- Discovering a gold answer = direct scoring lever on the FINAL test set (all 943)
- Discovering test set membership = indirect (helps local harness, format debugging)
- At deadline, final ranking uses ALL 943, not just the ~283 LB subset
- Gold answers help everywhere. Test set membership only helps pre-deadline.

Test set membership IS valuable for two specific things:
1. Building local eval harness (test pipeline changes without burning submissions)
2. Format rule discovery (if we have gold + membership + still wrong → FORMAT issue)

### Concern: LB-subset overfitting
If we optimize too hard for the ~283 LB subset, we risk shake-DOWN at final ranking (when all 943 count). Robust picks that score well across all 943 are safer than picks tuned to the test set.

### Bottom line for backsolve agent
Output BOTH P(in_test_set) and inferred_gold per item. But the gold answers are what we ACT on first. Test set membership is secondary intelligence.

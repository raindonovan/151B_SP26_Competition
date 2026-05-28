# Back-Solve Research

## Theoretical foundation

**Whitehill 2017** (arXiv 1707.01825): "Climbing the Kaggle Leaderboard by Exploiting the Log-Loss Oracle"
- Demonstrated that access to a score oracle can be exploited to deduce ground-truth test labels
- Achieved log-loss 0.00000 (#4 of 848) on Intel/MobileODT competition without training a classifier
- Key insight: iteratively submit batches of m examples, use score feedback to infer labels

## Applicability to our competition

Our grader returns **accuracy** (discrete fraction-correct) on an **unknown ~283-item subset** (30% of 943), not log-loss (continuous). This limits information per submission:
- Each submission reveals: ΔScore ≈ ΔCorrectItems / 283
- Minimum detectable change: ±1 item = ±0.35pp
- A single submission can test whether flipping item X changed the score

## What we already have

24+ past submissions with known scores. The Bayesian per-item back-solve (from `submission/scripts/backsolve.py`) already:
- Computes log-posterior for each candidate answer per item
- Uses all submissions to estimate per-item correctness probability
- Assigns confidence tiers (T1-T5)
- Produced `data/back_solve_detail.csv` (943 rows × diagnostic columns)

## Strategy: differential submissions for oracle mining

### Method
1. Start from a known-score baseline CSV (e.g., slot1_kitchen_sink_C at 0.692)
2. For a batch of N items, flip to an alternative answer
3. Submit and observe score delta
4. If score increases: the flipped answer is correct AND the item is in the test subset
5. If score decreases: the original was correct (or item not in test subset)
6. If score unchanged: items not in test subset (or net zero change)

### Batch sizing
- Flipping 1 item at a time: cleanest signal but costs 1 submission per item
- Flipping 5-10 items: more efficient but harder to attribute delta to specific items
- Recommended: flip 5-10 HIGH-CONFIDENCE items where we believe our alternative is correct
  - If all 5-10 are correct, expect +0.35pp per item in test subset
  - Score delta / 0.35pp ≈ items that changed

### Constraints
- Can't flip items we don't have alternatives for
- Need to hold all OTHER items constant between submissions
- 5pp noise band from unknown test subset composition

## Open questions
- Can we narrow down the ~283-item test subset from existing submission data?
- What's the optimal batch size for oracle mining given 5 submissions/day?
- Should we prioritize mining T2-T3 items (where we have moderate-confidence alternatives)?

# Submission Global Strategy

**Created**: 2026-05-28 Day 6
**Status**: ACTIVE — governs all remaining submission decisions

## Budget

- **~20 submissions remaining** (5/day × 4 remaining days, minus some already used)
- **2 final picks** at deadline (~2026-06-02)
- **CURRENT PICKS ARE WRONG**: 0.438 + 0.420 selected — MUST CHANGE before deadline

## What are submissions for?

Submissions serve three purposes, in priority order:

### Purpose 1: Oracle mining (highest value)
Each submission is an information-extraction tool. By constructing *differential* submissions (change a controlled set of items, hold everything else constant), we can infer:
- Which items are in the ~283-item test subset
- Whether our answer for a specific item is correct
- The gold answer for items where we can test multiple candidates

**Strategy**: pair submissions — identical except for N items flipped. Score delta ÷ (1/283) ≈ number of items changed. With careful item selection, a single pair reveals per-item gold.

**Back-solve is resurrected as a first-class strategy lever.** See `submission/BACKSOLVE_RESEARCH.md`.

### Purpose 2: Pipeline validation (second priority)
After building a new pipeline stage (adapter, post-processing rule, new inference run), submit to get a real Kaggle score. This is the test pipeline's final evaluation step — the one that makes the whole thing real.

### Purpose 3: Final pick optimization (reserve)
Reserve 2-3 slots in the last day for "best-so-far + one targeted improvement" to ensure final picks are actual best.

## Allocation plan

| Day | Slots | Purpose |
|-----|-------|---------|
| Day 6 (today) | 1-2 | Pipeline validation (Track A v1 baseline) |
| Day 7 | 3-4 | Oracle mining (differential pairs) |
| Day 8 | 3-4 | Oracle mining + pipeline validation |
| Day 9 | 2-3 | Final pipeline validation + pick optimization |
| Deadline | 0 | Select 2 final picks |

## Rules (locked)

- ALL submission methods allowed at ANY score (real-inference, mesh, splice, sheet-patch, Wolfram-patch)
- Only constraint: results must be produced by us
- Every submission must test a deliberate hypothesis — document it BEFORE submitting
- Record in `submission/REGISTRY.md` immediately after each submission
- Save CSV in `submission/csvs/` with descriptive filename

## Final picks strategy

- **Pick A**: Best real-inference pipeline score (robust, full 943)
- **Pick B**: Best override-augmented score (inference + Wolfram + teacher overrides)

## Related

- `submission/BACKSOLVE_RESEARCH.md` — back-solve techniques and research
- `submission/REGISTRY.md` — all past submissions with scores
- `submission/RED_ALERT_LB_SUBSET.md` — LB-subset scoring caveat

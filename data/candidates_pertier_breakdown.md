# Per-tier control candidate breakdown

**Total: 200 unique IDs across 4 tier-stratified samples.**

- Random seed: `42`
- Source: `results/answer_sheet/unified_answer_sheet_v5_1.csv`
- Filter: tier ∈ {T1,T2,T3,T4} AND non-empty `best_answer` AND NOT in `data/candidates_sc16_weak_158.txt`
- Per-tier: `min(50, available)`, sampled via `random.Random(42).sample(sorted_pool, n)`

## Per-tier counts and samples
- **T1**: 50 sampled from 402 available
  - First 5 IDs: `[15, 48, 52, 56, 57]`
- **T2**: 50 sampled from 138 available
  - First 5 IDs: `[0, 10, 22, 26, 27]`
- **T3**: 50 sampled from 136 available
  - First 5 IDs: `[4, 17, 18, 25, 29]`
- **T4**: 50 sampled from 109 available
  - First 5 IDs: `[14, 35, 45, 46, 124]`

## Verification
- Overlap with weak_158: 0 (must be 0)
- Internal uniqueness: 200 == 200 -> True

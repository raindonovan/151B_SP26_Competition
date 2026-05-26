# 30 hardest items breakdown

**Source**: `results/hybrid/sc16_base_run.jsonl` (partial — 43 items) intersected with `data/candidates_sc16_weak_158.txt`.

**Selection method:**
1. For items ∈ (158-weak ∩ sc16_base_run): compute `share = votes / n_voting`
2. Sort ascending by share, ties broken by item_id ascending
3. Take bottom 30 by share
4. If <30 in intersection: fall back to filling from 158-weak items NOT in sc16_base_run, sorted by id ascending

| item_id | share | source |
|---|---|---|
| 2 | 0.750 | in_partial |
| 5 | 0.875 | in_partial |
| 7 | 0.500 | in_partial |
| 16 | 0.500 | in_partial |
| 19 | 0.500 | in_partial |
| 24 | 1.000 | in_partial |
| 30 | 1.000 | in_partial |
| 49 | 0.562 | in_partial |
| 54 | 0.500 | in_partial |
| 58 | 1.000 | in_partial |
| 61 | 0.636 | in_partial |
| 63 | 0.188 | in_partial |
| 64 | 0.188 | in_partial |
| 67 | 0.875 | in_partial |
| 68 | 0.875 | in_partial |
| 72 | 0.312 | in_partial |
| 74 | 0.188 | in_partial |
| 82 | 0.875 | in_partial |
| 95 | 0.500 | in_partial |
| 102 | 0.538 | in_partial |
| 115 | 0.938 | in_partial |
| 129 | 0.625 | in_partial |
| 151 | 0.625 | in_partial |
| 177 | 0.562 | in_partial |
| 187 | 0.250 | in_partial |
| 195 | 0.188 | in_partial |
| 196 | 0.875 | in_partial |
| 199 | 0.500 | in_partial |
| 210 | 0.875 | in_partial |
| 225 | 0.750 | in_partial |

## Companion file
- `data/candidates_sc16_weak_default_128.txt`: 128 items = 158_weak - hardest30
- Verified: hardest30 ∪ default_128 = 158_weak, hardest30 ∩ default_128 = ∅

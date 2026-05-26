# NoThinking probe candidate breakdown

**Total: 98 unique IDs across 3 disjoint categories.**

- Random seed used: `42`
- Source for weak_ab pool: `data/candidates_sc16_weak_158.txt`
- Source for t1_control pool: `results/answer_sheet/unified_answer_sheet_v5_1.csv` (tier=1, non-empty `best_answer`, minus any overlap with no_box or weak_ab)
- Source for no_box: hardcoded list of 18 IDs from `submissions/run14b_v3filtered.csv` (rows lacking `\boxed{}`)

## no_box (18 IDs) — rescue probe
Items where run14b emitted a degenerate non-boxed response. Testing whether NoThinking forces a clean answer.

`93, 112, 161, 204, 229, 308, 312, 376, 383, 445, 453, 498, 652, 724, 799, 809, 836, 911`

## weak_ab (50 IDs) — NoThinking-vs-Thinking A/B test
Random sample from the 158-item weak set (random.Random(42).sample(weak_158, 50)).

`5, 24, 30, 49, 54, 61, 63, 64, 67, 72, 116, 122, 145, 169, 196, 210, 225, 239, 240, 269, 273, 288, 297, 325, 329, 340, 341, 347, 363, 387, 393, 403, 422, 487, 489, 519, 584, 607, 619, 653, 705, 745, 751, 773, 812, 833, 857, 864, 923, 927`

## t1_control (30 IDs) — does NoThinking break items the model already gets right?
Random sample from tier-1, non-empty best_answer pool (excluding no_box and weak_ab to ensure disjoint).

`48, 52, 56, 57, 123, 128, 139, 148, 185, 249, 268, 272, 279, 290, 300, 332, 512, 515, 600, 645, 669, 709, 730, 771, 782, 821, 848, 861, 877, 879`

## Verification
- no_box ∩ weak_ab: [] (must be empty)
- no_box ∩ t1_control: [] (must be empty)
- weak_ab ∩ t1_control: [] (must be empty)
- Total union size: 98 (must equal 98)

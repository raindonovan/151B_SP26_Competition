# submission/03_06 — SCORES

Submissions unlimited — submit all built slots; fill scores in as Kaggle returns them.
Kaggle is authoritative. Local independent-gold scoring **not computed**: the
`cross_run_correctness_matrix.csv` carries per-run pass/fail flags but no regradable gold
*value* column, so the new slot-5 values can't be locally graded without the sympy grader
(known hang risk). Left to Kaggle.

| slot | description | layer added | kaggle_public | kaggle_private | local_indep_gold |
|---|---|---|---|---|---|
| slot1_baseline_R20 | R20 SC8/32K, pure Qwen | — (anchor) | TBD | TBD | n/a |
| slot2_nothinking_join | NoThinking∪R20 join | NT-join | 0.664 (confirmed) | TBD | n/a |
| slot3_join_undercount | **NOT BUILT** (no Qwen-only source) | — | — | — | — |
| slot4_join_undercount_frac | **NOT BUILT** (source mismatch) | — | — | — | — |
| slot5_max_inference_alone | consensus + Thinking rescues + expr-safety | 40 consensus + 4 thinking + 763 expr | TBD | TBD | n/a |

See README "Blocked slots" for why 3 and 4 are held.

# submission/03_06 — SCORES

Submissions unlimited — submit all built slots; fill scores in as Kaggle returns them.
Kaggle is authoritative. Local independent-gold scoring **not computed**: the
`cross_run_correctness_matrix.csv` carries per-run pass/fail flags but no regradable gold
*value* column, so the new slot-5 values can't be locally graded without the sympy grader
(known hang risk). Left to Kaggle.

## SOURCE CAMPAIGN R1 — s01–s15 + control (2026-06-03)

All 16 submitted via Kaggle API; all **COMPLETE** by 2026-06-03 ~22:39 UTC.
Post-deadline ablation/oracle overlays (teacher/Wolfram/search values in `response`) — not rule-#11 Qwen-only.

| slot | file | description | kaggle_public | kaggle_private | status |
|---|---|---|---|---|---|
| s05_xhigh | `s05_xhigh.csv` | full 940-row xhigh one-hot | **0.756** | 0.715 | COMPLETE |
| s10_v7_fusion | `s10_v7_fusion.csv` | v7 canonical fusion | **0.749** | 0.686 | COMPLETE |
| s15_v7_fusion_raw | `s15_v7_fusion_raw.csv` | v7 raw render (no canon) | **0.749** | 0.686 | COMPLETE |
| control | `30_05_slot4_aggressive_v2.csv` | Pick A floor (re-submit) | **0.745** | 0.684 | COMPLETE |
| s11_agree_k2 | `s11_agree_k2.csv` | 5LLM agree ≥2 | 0.734 | 0.672 | COMPLETE |
| s12_agree_k3 | `s12_agree_k3.csv` | 5LLM agree ≥3 | 0.713 | 0.642 | COMPLETE |
| s09_anchor316 | `s09_anchor316.csv` | anchor316 one-hot | 0.706 | 0.648 | COMPLETE |
| s03_gpt54 | `s03_gpt54.csv` | GPT-5.4 teacher one-hot | 0.696 | 0.600 | COMPLETE |
| s06_opus | `s06_opus.csv` | Opus teacher one-hot (316) | 0.692 | 0.624 | COMPLETE |
| s02_sonnet | `s02_sonnet.csv` | Sonnet teacher one-hot | 0.692 | 0.640 | COMPLETE |
| s13_agree_k4 | `s13_agree_k4.csv` | 5LLM agree ≥4 | 0.689 | 0.631 | COMPLETE |
| s08_search | `s08_search.csv` | search one-hot (47) | 0.681 | 0.598 | COMPLETE |
| s07_wolfram_HIGH | `s07_wolfram_HIGH.csv` | Wolfram HIGH (58) | 0.678 | 0.607 | COMPLETE |
| s04_gpt_oss | `s04_gpt_oss.csv` | gpt-oss teacher one-hot | 0.671 | 0.630 | COMPLETE |
| s14_agree_k5 | `s14_agree_k5.csv` | 5LLM unanimous (98) | 0.671 | 0.592 | COMPLETE |
| s01_qwen_control | `s01_qwen_control.csv` | R20 Qwen base (0 overrides) | 0.667 | 0.583 | COMPLETE |

**s10 vs s15:** public **0.000** delta (both 0.749); private **0.000** delta (both 0.686) — matches local `Grader.is_equal` prediction in `CAMPAIGN_R1_LOCAL_CHECKS.md`.

**Control:** `30_05_slot4_aggressive_v2` re-submit **0.745** public / **0.684** private — unchanged from prior runs.

---

## Qwen-only ladder (separate campaign — README)

| slot | description | layer added | kaggle_public | kaggle_private | local_indep_gold |
|---|---|---|---|---|---|
| slot1_baseline_R20 | R20 SC8/32K, pure Qwen | — (anchor) | 0.667 | 0.583 | n/a |
| slot_adapter_rescue | `03_06_R20_plus_adapter11.csv` | adapter (11) | 0.667 | 0.587 | n/a |
| slot2_nothinking_join | NoThinking∪R20 join | NT-join | 0.664 (confirmed) | TBD | n/a |
| slot3_join_undercount | **NOT BUILT** (no Qwen-only source) | — | — | — | — |
| slot4_join_undercount_frac | **NOT BUILT** (source mismatch) | — | — | — | — |
| slot5_max_inference_alone | consensus + Thinking rescues + expr-safety | 40 consensus + 4 thinking + 763 expr | TBD | TBD | n/a |

**slot1_baseline_R20:** COMPLETE (submitted 2026-06-03 ~23:24 UTC). Public ties **s01_qwen_control** (0.667); private matches s01 (0.583).

**slot_adapter_rescue:** COMPLETE. Public ties baseline (0.667); private **+0.004** vs slot1_baseline_R20 (0.587 vs 0.583).

See README "Blocked slots" for why 3 and 4 are held.

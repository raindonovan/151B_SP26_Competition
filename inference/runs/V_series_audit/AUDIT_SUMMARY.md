# V-Series Audit (R15-R19) — Day 9 (2026-05-31)

Auditor: claude_strategy
Audit type: T1-shallow per Rain's plan (research-grade, post-deadline writeup material)
Verdict: **CLOSED, no incremental juice for competition tonight**

## Files
- Per-run candidate CSVs: `V0_baseline_candidates.csv`, `V1_counting_top_candidates.csv`, `V2_counting_bookend_candidates.csv`, `V3_shape_filter_candidates.csv`
- Merged tagged: `V0_to_V3_merged_candidates.csv` (47 items with category tags)
- V4: insufficient data (5/50 items in final jsonl, no summary)

## Headline numbers

| Run | Variant | Overall | MCQ | Free | n_unanimous | n_voted_changed | p25 agree | Oracle@8 | OracleGain |
|---|---|---|---|---|---|---|---|---|---|
| V0 | baseline (v1-prompt) | 0.700 (35/50) | 0.882 | 0.606 | 28 | 7 | 0.625 | 36 | +1 |
| V1 | counting-top (v2) | 0.720 (36/50) | 0.882 | 0.636 | 27 | 10 | 0.750 | 36 | 0 |
| V2 | counting-bookend (v2) | 0.720 (36/50) | 0.824 | 0.667 | 26 | 7 | 0.750 | 36 | 0 |
| V3 | shape_filter (v2) | 0.720 (36/50) | 0.882 | 0.636 | 22 | 7 | 0.500 | 37 | +1 |
| V4 | temp_diversification | INSUFFICIENT | — | — | — | — | — | — | — |

## Vote-lost items (Oracle@8 > Voted=R)

Union across V0-V3 = 4 items (public-set IDs 48, 56, 332, 599):

- **id 48** (all 4 runs): gold='I', voted='E'. **DATASET BUG per JUDGER_AND_PUBLIC_SET.md** (gold I=(4/3)ln3 ≡ option E=(2/3)ln9 — both correct, gold picks one). Not a real rescue.
- **id 56** (V0 only): gold=['A','C'], voted='C'. Multi-select MCQ undercount.
- **id 332** (V2 only): gold='C', voted='N'. Low agreement (0.38) → legit fragmentation.
- **id 599** (V3 only): gold='25/343, 11 4/7', voted='\frac{25}{343}, 11 \frac{4}{7}'. **Value-equal on private grader, lost only under strict-Hendrycks.** Not vote-lost on Kaggle.

Net legitimate oracle gain: 1-2 items across 4 runs × 50 items.

## Per-run lever interpretation

- **V0**: reference; vote-aggregation upside small on this slice.
- **V1 (counting-top)**: prompt-engineering moves vote winners without unlocking new capability.
- **V2 (counting-bookend)**: bookend redistributes errors MCQ↔Free, no net gain. cutoffs_per_sample 8→16 — token cap pressure noise.
- **V3 (shape_filter)**: lowest unanimity (22) and p50 agreement (0.875). Creates fragility, doesn't create rescues — fragmented samples are correlated-wrong, not "1 right hidden among 7."
- **V4**: ABORTED, 5/50 final items. Insufficient data to evaluate temp diversification.

## Normalization-linked extraction

| Category | Count | Public-set IDs |
|---|---|---|
| multi_box_pattern | 47 | (normal reasoning trace; not actionable alone) |
| multi_slot_undercount | 3 | 29, 56, 759 |
| no_box_rescue_candidate | 1 | 332 |
| vote_fragmentation | 2 | 332, 599 |
| revote_candidate_any | 4 | 48, 56, 332, 599 |

## Marginal IDs vs current Pick B workstreams

**CRITICAL**: V-series uses PUBLIC-SET IDs (data/public.jsonl, 1126 items). These are DISJOINT from PRIVATE-SET IDs (data/private.jsonl, 943 items) used by the Kaggle leaderboard and the cross_run_correctness_matrix / NT-13 / Tier-1 normalizer scope.

- Diff vs NT-13 (private IDs): N/A (different ID space)
- Diff vs Tier-1 normalizer planned coverage: CATEGORY signal aligns (multi-slot, no-box rescue, vote-fragmentation are all in normalizer scope), but specific IDs don't apply
- Diff vs value-equality re-vote (private SC runs): N/A (different ID space)

The V-series CATEGORY findings generalize and confirm the normalizer's chosen scope. The SPECIFIC IDs are not actionable for tonight's Pick B construction.

## Recommendation

Mark V-series audit **CLOSED for competition tonight**. No new inference experiments. The two active levers (Tier-1 normalizer + value-equality re-vote) cover the same failure-mode categories the V-series exposed. Document this audit in the research write-up post-deadline.

## V4 follow-up (post-deadline only)
- Restart V4 with full 50-item budget if useful for research write-up
- Diagnose cause of truncation (8 PARTIAL → 5 FINAL — re-tagging step lost 3 items)

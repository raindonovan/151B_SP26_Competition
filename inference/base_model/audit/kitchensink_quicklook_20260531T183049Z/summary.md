# Kitchen-sink quicklook summary — 2026-05-31

**Run dir:** inference/base_model/kitchensink_20260531T135417Z (rung 1 partial, 6/27 items)
**Rungs completed:** 1 of 3 (rung1_stable only so far, run in progress)

## Key findings
1. All 6 completed items fall in <60% SC agreement — these are genuinely hard residual items with high diversity of extracted answers.
2. ID 376 is the hardest: 1/16 agreement (16 distinct answers), voted=10850 — model has almost no consensus.
3. ID 724 is the strongest at 56% agreement (voted=2, 9/16 samples agree) — borderline candidate.
4. sample_extracted field used correctly; schema confirmed: id, sample_extracted, voted_answer, n_voting, wall_seconds.
5. No gold comparison done here — gold field in kitchensink_target_set.csv may contain placeholders per external LLM flag; formal rescore pending separately.

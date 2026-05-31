# R20b_eval_v1_sc8_p943_t32k_v3filt

**Original name:** `run14b_sc8_v1_private943_tok32k_pp1_v3filtered`
**R-number:** R20b (derivative of R20)
**Run date:** 2026-05-22 (derived from R20's samples; no separate summary.json)
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method `vllm-sc` · n_samples 8 · max_new_tokens 32768 · temperature 0.6 · top_p 0.95 · top_k 20 · prompt `v1-baseline` · **+ v3 shape-filter applied to samples before SC voting** (per-sample `shape_rejected`; row-level `v3_samples_kept`/`v3_samples_rejected`)

**Purpose:** Isolates the **sample-filter effect** at fixed inference — same 8 samples per item as R20, but a v3 shape-filter rejects off-shape samples before voting, changing which votes win. The only Pick-B-relevant cohort lever that costs no GPU (pure post-processing). **Finding: the filter is a vote-cleanup, not a correctness lever — filter dividend = 0 on gold-scored items, Kaggle flat at 0.646 (== R20). Dropped from morning planning.** Fifth and FINAL deep audit; completes the 5-run p943 cohort and the CROSS_RUN_MATRIX.

Deep audit (T2): `analysis/` holds analyzer v3-final-final outputs (`analysis.csv`, `analysis.jsonl`, `analysis_samples.jsonl` — 7544 rows). Findings (filter effect vs R20, 5-way intersection, **locked 11-item adapter seed**) in `findings.md`. Derived submission stays in `submission/csvs/`: `run14b_v3filtered.csv` (REGISTRY #14, **0.646**). The run `.jsonl` (155MB), `analysis.jsonl`, `analysis_samples.jsonl` are git-LFS-tracked.

# R08_eval_v1_single_p943_t16k

**Original name:** `run08v2_v1_private943_tok16384`
**R-number:** R08
**Run date:** 2026-05-04 05:49 → 09:47 UTC (≈4h, RTX 4090)
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method `vllm` (single-sample) · n_samples 1 · max_new_tokens 16384 (max_model_len 20480) · temperature 0.6 · top_p 0.95 · n_items 943 (300 MCQ / 643 free) · prompt `v1-baseline`

**Purpose:** First time the base model ran the **full 943-item private test set** — the naïve single-sample 16K floor that every later run (SC, longer tokens, prompt variants, adapters) was built on top of. Contributes the baseline column to `CROSS_RUN_MATRIX` (Pick-B-relevant p943 cohort: R08, R09, R10, R20, R20b).

Deep audit (T2): `analysis/` holds the analyzer v3-final-final outputs (`analysis.csv`, `analysis.jsonl`; no `analysis_samples.jsonl` — single-sample run). Findings in `findings.md`. Derived submissions stay in `submission/csvs/`: `run08v2_v1_private943.csv` (REGISTRY #1, **0.586**, first submission) and `expA_run08_perslot_perturbed.csv` (REGISTRY #3, 0.420). The run `.jsonl` (17MB) is git-LFS-tracked.

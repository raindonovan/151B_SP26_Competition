# R10_eval_v3perslot_single_p943_t16k

**Original name:** `run10_v3perslot_private943_tok16384`
**R-number:** R10
**Run date:** 2026-05-05 (git-log fallback; summary.json has no timestamps)
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method `vllm` (single-sample) · n_samples 1 · max_new_tokens 16384 · temperature 0.6 · top_p 0.95 · n_items 943 (300 MCQ / 643 free) · prompt `v3-perslot`

**Purpose:** Isolates the **prompt-variant effect** — v3-perslot vs R08's v1-baseline, both single-sample at 16K. The third deep p943 run; contributes the v3-perslot column to `CROSS_RUN_MATRIX`. Finding: v3-perslot is net-negative (−11 vs R08) and decisively beaten by SC (R09); the dev arc correctly abandoned it after this run.

Deep audit (T2): `analysis/` holds analyzer v3-final-final outputs (`analysis.csv`, `analysis.jsonl`; no `analysis_samples.jsonl` — single-sample). Findings (cross-run vs R08/R09 + three-way B∩B∩B core) in `findings.md`. Derived submission stays in `submission/csvs/`: `run10_v3perslot_private943.csv` (REGISTRY #2, **0.424**, worst p943 submission). The run `.jsonl` (16MB) is git-LFS-tracked. R10b (`expA_run08_perslot_perturbed`) ran alongside but is a shallow ablation — not cataloged here.

# R09_eval_v1_sc8_p943_t16k

**Original name:** `run09sc8_v1_private943_tok16384`
**R-number:** R09
**Run date:** 2026-05-04 17:32 → 2026-05-05 22:24 UTC (long SC run)
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method `vllm-sc` · **n_samples 8** · max_new_tokens 16384 · temperature 0.6 · top_p 0.95 · n_items 943 (300 MCQ / 643 free) · prompt `v1-baseline`

**Purpose:** First self-consistency run on the full 943-item private set, and the **SC twin of R08** — same model, token budget, prompt, and day, differing ONLY by SC@8. Isolates the pure SC effect at fixed tokens/prompt. Pick-B-relevant p943 cohort member; contributes the first SC column (plus the first real A_lucky_sample distribution) to `CROSS_RUN_MATRIX`.

Deep audit (T2): `analysis/` holds analyzer v3-final-final outputs (`analysis.csv`, `analysis.jsonl`, `analysis_samples.jsonl` — 7544 rows). Findings (incl. cross-run R08↔R09 transitions + DeepConf/SC@32 candidate lists) in `findings.md`. Derived submissions stay in `submission/csvs/` and cross-link here: `run09sc8_v1_private943.csv` (REGISTRY #4, **0.614**, SC=8 baseline), `run09sc8_format_fixed.csv` (#6, 0.611), `run09sc8_probe_b_reversed.csv` (#5, 0.438). The run `.jsonl` (130MB) and `analysis.jsonl` are git-LFS-tracked.

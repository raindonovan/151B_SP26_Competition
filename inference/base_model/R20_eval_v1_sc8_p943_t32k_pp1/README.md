# R20_eval_v1_sc8_p943_t32k_pp1

**Original name:** `run14b_sc8_v1_private943_tok32k_pp1`
**R-number:** R20 (locked chronology; ran 2026-05-22, the latest p943 run — the `run14b` filename and the May-27 commit are post-hoc)
**Run date:** 2026-05-22 13:56 UTC
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method `vllm-sc` · **n_samples 8** · **max_new_tokens 32768** · temperature 0.6 · top_p 0.95 · top_k 20 · presence_penalty 1.0 · repetition_penalty 1.0 · n_items 943 (300 MCQ / 643 free) · prompt `v1-baseline`

**Purpose:** THE 0.646 best-inference baseline — the floor the locked **0.745 Pick A** was built on via teacher/anchor/Opus overrides. Isolates the **token-budget effect**: R09's structural sibling (both SC@8 + v1) at 32K vs 16K. Pick-B-relevant p943 cohort; the 4th deep audit completes the 4-way (single/SC × v1/v3perslot × 16K/32K) cross-run matrix and the final adapter-target seed.

Deep audit (T2): `analysis/` holds analyzer v3-final-final outputs (`analysis.csv`, `analysis.jsonl`, `analysis_samples.jsonl` — 7544 rows). Findings (token-effect vs R09, 4-way intersection, final 11-item adapter seed) in `findings.md`. The run `.jsonl` (150MB), `analysis.jsonl`, `analysis_samples.jsonl` are git-LFS-tracked; the run `.log` (from `infrastructure/logs/`) is co-located here. Derived submissions stay in `submission/csvs/` (`run14b_sc8_v1.csv`, `run14b_v3filtered.csv`=R20b, `slot3_run14b_nobox_patched.csv`, `slot1_adapter_v5_plus_run14b_*.csv`) and the entire 30_05 slot sweep / 0.745 stack trace back here.

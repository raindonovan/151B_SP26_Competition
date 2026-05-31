# R07_eval_v1_sc8_f50_t16k

**Original name:** `run07_sc8_v1_50_tok16384`
**R-number:** R07
**Run date:** 2026-05-03 19:23 UTC
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method vllm-sc · n_samples 8 · max_new_tokens 16384 · temperature 0.6 · n_items 50 · prompt `v1-baseline`

**Purpose:** First self-consistency run (SC@8) — 50 items, 8 samples each, v1-baseline prompt at 16K tokens. The decoding method that later scaled to the p943 SC8 runs.

Shallow dev/smoke/parity run — identity-preservation catalog only (T1). Does NOT feed CROSS_RUN_MATRIX or Pick B (those are the p943 cohort: R08, R09, R10, R20, R20b). Artifacts (`.jsonl` + `.summary.json`) live in this folder; no analyzer artifacts (shallow runs don't get `analyze_run.py`).

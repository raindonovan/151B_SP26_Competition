# R04_parity_v1_single_f20_t8k

**Original name:** `run04_vllm_parity_20_tok8192`
**R-number:** R04
**Run date:** 2026-05-03 02:31 UTC
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method vllm · n_samples n/a (single-sample) · max_new_tokens 8192 · temperature 0.6 · n_items 20 · prompt `v1-baseline`

**Purpose:** 20-item vLLM parity check — verifies the vLLM path matches the reference decoding on the same 20 items as R00, at 8K tokens, temp 0.6.

Shallow dev/smoke/parity run — identity-preservation catalog only (T1). Does NOT feed CROSS_RUN_MATRIX or Pick B (those are the p943 cohort: R08, R09, R10, R20, R20b). Artifacts (`.jsonl` + `.summary.json`) live in this folder; no analyzer artifacts (shallow runs don't get `analyze_run.py`).

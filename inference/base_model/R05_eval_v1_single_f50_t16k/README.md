# R05_eval_v1_single_f50_t16k

**Original name:** `run05_v1_50_tok16384`
**R-number:** R05
**Run date:** 2026-05-03 16:53 UTC
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method vllm · n_samples n/a (single-sample) · max_new_tokens 16384 · temperature 0.6 · n_items 50 · prompt `v1-baseline`

**Purpose:** First 50-item eval — the first run at the 16K token budget that became the dev-era default, on the v1-baseline prompt.

Shallow dev/smoke/parity run — identity-preservation catalog only (T1). Does NOT feed CROSS_RUN_MATRIX or Pick B (those are the p943 cohort: R08, R09, R10, R20, R20b). Artifacts (`.jsonl` + `.summary.json`) live in this folder; no analyzer artifacts (shallow runs don't get `analyze_run.py`).

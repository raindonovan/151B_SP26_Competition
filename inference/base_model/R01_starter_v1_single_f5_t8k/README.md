# R01_starter_v1_single_f5_t8k

**Original name:** `starter_results`
**R-number:** R01
**Run date:** 2026-05-01 21:25 UTC
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method vllm (single-sample) · n_samples n/a (single-sample) · max_new_tokens unlogged (8K era) · temperature unlogged (0.6 era default) · n_items 5 · prompt `v1-baseline (inferred)`

**Purpose:** Initial scaffold output (~3 min after R00) — a 5-item smoke that produced the first results.jsonl shape. Minimal row schema (correct/gold/id/is_mcq/response); no token/temperature logging yet, so tokens default to the 8K era setting.

Shallow dev/smoke/parity run — identity-preservation catalog only (T1). Does NOT feed CROSS_RUN_MATRIX or Pick B (those are the p943 cohort: R08, R09, R10, R20, R20b). Artifacts (`.jsonl`) live in this folder; no analyzer artifacts (shallow runs don't get `analyze_run.py`).

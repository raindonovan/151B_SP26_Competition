# R00_eval_v1_single_f20_t8k

**Original name:** `run03_tok8192_20`
**R-number:** R00
**Run date:** 2026-05-01 21:22 UTC
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method vllm (single-sample) · n_samples n/a (single-sample) · max_new_tokens 8192 · temperature 0.6 · n_items 20 · prompt `v1-baseline (inferred)`

**Purpose:** Earliest run on record — a 20-item @ 8K-token eval used to sanity-check the base model end-to-end. No summary.json; date and config from the locked chronology + row-0 schema (correct/gold/gen_tokens/response).

Shallow dev/smoke/parity run — identity-preservation catalog only (T1). Does NOT feed CROSS_RUN_MATRIX or Pick B (those are the p943 cohort: R08, R09, R10, R20, R20b). Artifacts (`.jsonl`) live in this folder; no analyzer artifacts (shallow runs don't get `analyze_run.py`).

# R06_eval_v2mcq_single_f50_t16k

**Original name:** `run06_v2mcq_50_tok16384`
**R-number:** R06
**Run date:** 2026-05-03 17:16 UTC
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method vllm · n_samples n/a (single-sample) · max_new_tokens 16384 · temperature 0.6 · n_items 50 · prompt `v2-mcq-commit`

**Purpose:** 50-item eval on the v2-mcq-commit prompt variant — tests an MCQ-specific prompt change against the same 50 items as R05.

Shallow dev/smoke/parity run — identity-preservation catalog only (T1). Does NOT feed CROSS_RUN_MATRIX or Pick B (those are the p943 cohort: R08, R09, R10, R20, R20b). Artifacts (`.jsonl` + `.summary.json`) live in this folder; no analyzer artifacts (shallow runs don't get `analyze_run.py`).

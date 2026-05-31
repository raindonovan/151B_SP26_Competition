# R02_smoke_v1_single_f5_t2k

**Original name:** `run_vllm_smoke_5_tok2048`
**R-number:** R02
**Run date:** 2026-05-03 02:17 UTC
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method vllm (single-sample) · n_samples n/a (single-sample) · max_new_tokens 2048 · temperature unlogged (0.6 era default) · n_items 5 · prompt `v1-baseline (inferred)`

**Purpose:** 5-item vLLM smoke at 2K tokens (same commit as R03) — a deliberately tight token budget to confirm truncation/hit_token_cap handling. Row schema adds has_boxed_answer + hit_token_cap.

Shallow dev/smoke/parity run — identity-preservation catalog only (T1). Does NOT feed CROSS_RUN_MATRIX or Pick B (those are the p943 cohort: R08, R09, R10, R20, R20b). Artifacts (`.jsonl`) live in this folder; no analyzer artifacts (shallow runs don't get `analyze_run.py`).

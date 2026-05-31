# NT_eval_nothinking_sc8_p943_t8k

**Original name:** `nothinking_full_943_20260527T000129Z` (from `inference/results/hybrid/tnr-B/`)
**R-number:** NT (NOT R-series — orthogonal NoThinking mode, distinct from the chronological R-loop)
**Run date:** 2026-05-27 00:01 UTC (on disk untouched ~3 days until this T1.5 audit)
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method `vllm-sc` in **NoThinking mode** (prefill `"Okay, I think I have finished thinking.\n</think>\n\n"` bypass, per memory #20 — NOT `enable_thinking=False`) · n_samples 8 · token cap 8192 · n_items 943 · `mode: base`. No summary.json (provenance from the run jsonl).

**Purpose:** Out-of-cohort T1.5 audit testing whether NoThinking outputs are **orthogonal** to R20's Thinking-mode outputs — i.e. whether "NoThinking ∪ R20 consensus" is a zero-GPU Pick-B candidate. **VERDICT: ELEVATE** — 15 unique-correct items vs R20 (≥10 threshold), 4/5 orthogonal failure modes, 67.3% agreement (32.7% ensemble headroom). See `findings.md`.

Audit artifacts: `analysis/` holds analyzer v3-final-final outputs (run on the adapted file). **Two run jsonls in this folder:** `nothinking_full_943_20260527T000129Z.jsonl` (raw, original schema — string-samples + parallel arrays) and `nothinking_full_943_ADAPTED.jsonl` (restructured to the analyzer's SC schema by `inference/scripts/prep_nothinking_for_analyzer.py`; the analyzer ran on this one). The analyzer was NOT modified. Both jsonls + analysis.jsonl + analysis_samples.jsonl are git-LFS-tracked. The 98-item probe + targeted_rescue variants in the original `hybrid/tnr-B/` dir are NOT cataloged here (deferred).

# NT_probe98_eval_nothinking_sc8_f98_t8k

**Original name:** `nothinking_probe98_20260526T065456Z` (from `inference/results/hybrid/tnr-B/`)
**R-number:** NT-probe98 (NOT R-series — precursor NoThinking slice used for T2 variance work, not part of the chronological R-loop)
**Run date:** 2026-05-26 06:58 UTC
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · method `vllm-sc` in **NoThinking mode** (prefill `"Okay, I think I have finished thinking.\n</think>\n\n"` bypass, not `enable_thinking=False`) · n_samples 8 · token cap 8192 · n_items 98 · `mode: base`. No summary.json; provenance is from the raw run jsonl.

**Purpose:** T2 audit of the early 98-item NoThinking probe against the later full 943-item NoThinking run. This is a variance / determinism check, not a Pick-B candidate by itself. **VERDICT: YELLOW** — lineage is confirmed, but probe98 is too noisy to serve as a stable mirror of NT-943 (`28/98` exact voted-answer matches; scored-set accuracy drops from `37/44` on NT-943 to `27/44` here).

Audit artifacts: `analysis/` holds analyzer v3-final-final outputs run on `nothinking_probe98_ADAPTED.jsonl`, produced by `inference/scripts/prep_nothinking_for_analyzer.py --run-id NT_probe98_eval_nothinking_sc8_f98_t8k`. The raw probe jsonl remains at `inference/results/hybrid/tnr-B/nothinking_probe98_20260526T065456Z.jsonl`; this folder stores the adapted copy plus audit outputs to avoid duplicating the raw artifact.
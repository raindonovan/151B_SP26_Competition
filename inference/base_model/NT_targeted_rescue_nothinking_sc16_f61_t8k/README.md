# NT_targeted_rescue_nothinking_sc16_f61_t8k

**Original name:** `targeted_rescue_nothinking_20260526T230849Z` (from `inference/results/hybrid/tnr-B/`)
**R-number:** NT-targeted_rescue (NOT R-series — NoThinking curated-subset experiment)
**Run date:** 2026-05-26 23:12 UTC
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · **NoThinking mode** (prefill `</think>` bypass; mean 1389 output tok) · **SC@16** · token cap 8192 · **61 curated hard items** (R20-failure-weighted: 42/61 R20-wrong, 43/61 T5). `mode: base`. No summary.json.

**Purpose:** T2 audit testing whether NoThinking applied to a *curated hard subset* (at SC@16) produces rescues beyond the full NT-943 join. **Verdict: NO** — 1 new unique rescue (id=232) but 6 regressions vs NT-943 → **net −5, do not stack**. Capability-vs-sampling signal = stochastic variance (texas-oil/probe98 saturation pattern), not capability. **0 intersection with the 17-still-truncated set** → says nothing about the "NoThinking high-budget on truncated" morning candidate. Research-only. Full analysis in `findings.md`.

**Paired with** a Thinking-mode twin `targeted_rescue_20260526T201046Z` (same 61 ids, mean 6102 tok) — left in `hybrid/tnr-B/`, separate audit if needed. Artifacts: `analysis/` (analyzer v3-final-final on the adapted file), raw `targeted_rescue_nothinking_20260526T230849Z.jsonl` (string-sample schema, 4.5MB), `targeted_rescue_nothinking_ADAPTED.jsonl` (SC-schema via `prep_nothinking_for_analyzer.py`). All <10MB → committed raw. Analyzer NOT modified.

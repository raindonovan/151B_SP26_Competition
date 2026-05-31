# TH_targeted_rescue_thinking_sc16_f61

**Original name:** `targeted_rescue_20260526T201046Z` (from `inference/results/hybrid/tnr-B/`)
**R-number:** TH-targeted_rescue (Thinking-mode twin of `NT_targeted_rescue_nothinking_sc16_f61_t8k`)
**Run date:** 2026-05-26 20:13 UTC
**Config:** model `Qwen/Qwen3-4B-Thinking-2507` · **Thinking mode** (full reasoning; mean 6102 output tok, max 22617 → thinking_budget ~24576) · **SC@16** · same **61 curated hard items** as the NoThinking twin (R20-failure-weighted, 43/61 T5).

**Purpose:** Slot-composition follow-up — does high-budget Thinking on hard items rescue what R20 ∪ NT-943 miss? **Verdict: YES — real slot-7/8 lever.** NEW-RESCUE COUNT = **4** (items 9, 435, 479, 638; the 5th candidate, 499, was R20-already-correct), **all on independent gold**, all FRESH (0 ∩ 17-truncated, 0 ∩ 8-item adapter seed). THINK beats NoThinking-twin 20/61 vs 13/61 on the identical hard set. Rescues a distinct multi-slot/precision class via long generation (not truncation). Full analysis in `findings.md`.

Artifacts: `analysis/` (analyzer v3-final-final on the adapted file), raw `targeted_rescue_20260526T201046Z.jsonl` (string-sample schema, 19MB, git-LFS-tracked), `targeted_rescue_thinking_ADAPTED.jsonl` (SC-schema via `prep_nothinking_for_analyzer.py --budget 24576`; analyzer ran on this). Analyzer NOT modified. Tomorrow-impact: justifies a high-budget Thinking SC morning run on R20-wrong multi-slot/precision items (complementary to the NT-943 join).

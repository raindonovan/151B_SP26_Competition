# inference/base_model/FINDINGS.md — Cross-run findings for base-model inference

> **Scope**: patterns and discoveries that cut across multiple base-model inference runs.
> Single-run findings live in the per-run `findings.md`. Promote here when a finding holds across runs.
> Top-level cross-cutting (e.g. things that hold for adapter AND base model) → `inference/FINDINGS.md`.

## Seeded from `inference/RESEARCH.md` (pre-Day-7 carryover, to be validated/expanded as we catalog each run)

### Best base-model configuration (LOCKED)
- Model: `Qwen3-4B-Thinking-2507`
- Sampling: `temperature=0.6, top_p=0.95, top_k=20, min_p=0`, `presence_penalty` preferred (not `repetition_penalty`)
- Token budget: `max_tokens=49152, thinking_budget=24576` (hardest items: `81920/65536`)
- Greedy decoding contraindicated for thinking mode (per official Qwen guidance)
- Best inference score: **0.646** (`run14b_sc8_v1_private943_tok32k_pp1_v3filtered`, soon to be renamed)

### Self-consistency (SC@N)
- SC gains plateau around N=16-32 for AIME-level problems (Wang et al. 2023).
- Temperature diversification across SC samples: +7.3pp on Qwen3-4B (Sun et al.) — UNTRIED on our data.
- All-disagreement items degenerate to pass@1 (SC doesn't help when no two samples agree).

### NoThinking
- `enable_thinking=False` is a NO-OP on this model — silently ignored.
- Must use prefill: `"Okay, I think I have finished thinking.\n</think>\n\n"`.
- Full 943-item NoThinking results exist but have NEVER been scored on Kaggle.

### DeepConf (untried, candidate)
- Fu et al. arxiv 2508.15260: logprob-weighted SC voting.
- 99.9% at 512 traces on AIME 2025 (vs 97.0% plain majority vote).
- Needs `output_scores=True` plumbed through the sampler.
- At SC@8 the confidence signal is noisier than at SC@32+.

### Multi-agent prompt dive (May 9 research)
- Top AIMO teams use minimal prompts (1-2 sentences). Elaborate system prompts hurt more than help on math reasoning.
- DeepSeek-R1 recommends NO system prompt at all.
- Qwen3-Thinking vendor recommendations match our locked config (T=0.6, TopP=0.95, TopK=20).

## Token budget / thinking-length / truncation (CONFIRMED, R08–R20 matrix + high-budget probes)

- **16K**: truncation dominant failure mode (`inference/SCRATCH.md` L247: 119 truncated on R08; L284: tokens remain ceiling even with SC@8).
- **32K (R20)**: trunc=17 vs R08 119 / R09 93; **72/89** items always truncated at 16K rescued at 32K (`inference/SCRATCH.md` L338). Token dividend +7 scored vs SC +33 at fixed v1 (L342–L343) — SC first, tokens second-order but material on long derivations.
- **High thinking budget (81920/65536)**: thinking_probe runs 0 truncations on targeted slices (`inference/SCRATCH.md` L479–L498); on hard multi-slot items, long Thinking beats NoThinking twin (L37–L39 in `inference/base_model/SCRATCH.md`).
- **NoThinking full-943**: trunc=9 vs R20 trunc=17 (`inference/SCRATCH.md` L421); Kaggle join lever 0.664 (`submission/REGISTRY.md` L9) — orthogonal to Pick A win path, not a contradiction of win-forward lock.

---
## [Rain] 2026-06-04 — External validation (truncation + thinking-length axes)

**GOLD:** Field independently confirmed truncation + thinking-length as core failure axes and inference-time scaling > SFT on this model — aligns with R08–R20 token matrix above and `inference/FINDINGS.md` (2026-06-04 entry).

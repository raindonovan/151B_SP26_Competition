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

## To-add (will populate as we catalog each base-model run)

_Empty._

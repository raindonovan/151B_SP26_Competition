# Inference Research

## Key findings

### Sampling configuration (LOCKED)
- Model: Qwen3-4B-Thinking-2507
- Sampling: temperature=0.6, top_p=0.95, top_k=20, min_p=0, presence_penalty (not repetition_penalty)
- Greedy decoding contraindicated for thinking mode (official Qwen guidance)
- Token budget: max_tokens=49152, thinking_budget=24576; hard items at 81920/65536

### NoThinking
- enable_thinking=False is a NO-OP on this model
- Must use prefill: "Okay, I think I have finished thinking.\n</think>\n\n"
- Results exist (full 943), NEVER analyzed or scored on Kaggle

### Self-consistency
- SC gains plateau around N=16-32 for AIME-level (Wang et al. 2023)
- Temperature diversification across SC samples: +7.3pp on Qwen3-4B (Sun et al.)
- All-disagreement items degenerate to pass@1

### SFT adapters
- v5 near break-even with base. Regression ~7 semantic items. 87% T1-easy training is structural issue.
- Repetition collapse at greedy/default traced to decoding config, not weight-space collapse
- repetition_penalty=1.1 partially recovers
- WiSE-FT for LoRA = scale lora_alpha by δ (δ=0.5 prior, no retraining)

### DeepConf (untried)
- Fu et al. arxiv 2508.15260: logprob-weighted SC voting
- 99.9% at 512 traces on AIME 2025 (vs 97.0% plain majority vote)
- Needs output_scores=True plumbed through sampler
- At SC@8 the confidence signal is noisier than at SC@32+

## See also
- `strategy/INFERENCE_TECHNIQUES.md` — full tried-vs-untried inventory

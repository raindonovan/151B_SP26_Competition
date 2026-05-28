# inference/SCRATCH.md — Unsorted findings, ideas, observations

Drop anything here. Rain will sort it later.

---

- Qwen3-4B official recommended sampling: temperature=0.6, top_p=0.95, top_k=20, min_p=0, presence_penalty (not repetition_penalty). Greedy contraindicated for thinking mode.
- NoThinking = prefill only. enable_thinking=False is a no-op on this model.
- Repetition collapse at greedy traced to decoding config, not weight-space collapse. repetition_penalty=1.1 partially recovers.
- Sun et al. showed +7.3pp from multi-temperature voting on Qwen3-4B size class. Never tried.
- WiSE-FT for LoRA = scale lora_alpha by delta (delta=0.5 prior). No retraining needed. Could recover v5 adapter.
- SFT v5 regression was ~7 semantic items, not format. 87% T1-easy in training set is structural issue.

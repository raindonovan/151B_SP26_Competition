# OpenR1 v2 16K Adapter — Untracked

This adapter exists on DSMLP local disk only. Not git-tracked.

## Location
DSMLP: `~/private/151B_SP26_Competition/training/checkpoints/openr1_v2_16k/final_adapter/`

## Files
- `adapter_model.safetensors` (253MB) — LoRA adapter weights
- `adapter_config.json` — LoRA config
- `tokenizer.json` (11MB) + `tokenizer_config.json` — tokenizer files
- `chat_template.jinja` — chat template

## Why untracked
This is from the SFT v1 era (2026-05-06 catastrophe). OpenR1-Math-220k traces truncated at max_seq_length=4096 — model learned to ramble without producing \boxed{}. Superseded by v3/v4/v5. Preserved on disk for historical reference only.

## What this was
QLoRA adapter on Qwen3-4B-Thinking-2507, trained on 1K OpenR1-Math-220k traces. Part of the 3-arm SFT v1 experiment that all failed. See `inference/adapters/sft_v1_postmortem/` and `archive/session_logs/SESSION_LOG.md` (2026-05-06 entry).

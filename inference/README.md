# inference/ — Stage 2: Model Inference

Running Qwen3-4B-Thinking-2507 on private.jsonl to generate candidate answers.

## Contents
- `scripts/` — inference runners (run_vllm_sc.py is the main one)
- `runs/` — per-run analysis folders with findings
- `results/` — raw inference JSONL outputs from all runs
- `adapters/` — SFT adapter configs, training scripts, logs

## Key facts
- Model: Qwen/Qwen3-4B-Thinking-2507 (fixed by rules)
- Best config: SC=8, 32K tokens, T=0.6, top_p=0.95, top_k=20
- Best inference score: 0.646 (run14b_v3filtered)
- 12+ runs in results/ (~720MB total)
- Production entry point: scripts/run_inference.py (for Gradescope)

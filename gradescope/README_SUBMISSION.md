# CSE 151B SP26 Competition — Submission

## Quick Start

```bash
python3 scripts/run_inference.py
```

This produces `submission.csv` — the final Kaggle-format output.

## Entry Point

`run_inference()` in `scripts/run_inference.py` is the single entry point:
1. Loads Qwen3-4B-Thinking-2507 via vLLM
2. Runs inference on all 943 items from `private.jsonl` (SC=8, shape-filtered majority vote)
3. Applies post-processing: multi-answer shape fix, minimal LaTeX normalizer, Wolfram overrides
4. Outputs `submission.csv` (id, response)

## Hardware

- **GPU**: 2× NVIDIA A100 80GB (tensor parallel)
- **Inference time**: ~3-4 hours for full 943 items at SC=8
- **Memory**: ~40GB VRAM used (bfloat16, prefix caching enabled)

## Model

- **Base**: `Qwen/Qwen3-4B-Thinking-2507` from HuggingFace
- **No adapter** used in final submission (adapter v5 was near-break-even, not beneficial)
- **Sampling**: temperature=0.6, top_p=0.95, top_k=20, max_tokens=49152, thinking_budget=24576

## Post-Processing Pipeline

Applied in order after inference:
1. **Multi-answer shape fix**: Consolidates separate `\boxed{}` entries into single `\boxed{a, b, c}` format (+0.3pp)
2. **Minimal LaTeX normalizer**: Strips thin-space macros (`\,`, `\;`, `\!`, `\:`) and `\left`/`\right` from last `\boxed{}` content (+0.4pp)
3. **Wolfram overrides**: 58 HIGH-confidence answers from Wolfram Alpha verification, applied as static last-`\boxed{}` replacements from `results/wolfram_overrides.csv` (+0.7pp est.)

## Key Files

| File | Purpose |
|------|---------|
| `scripts/run_inference.py` | Entry point — `run_inference()` |
| `private.jsonl` | 943 competition items (questions) |
| `results/wolfram_overrides.csv` | Static Wolfram-verified answer overrides |
| `submission.csv` | Output — Kaggle submission format |
| `results/inference_run.jsonl` | Full inference log with all SC samples |

## Inference Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| SC (self-consistency) | 8 | Diminishing returns past 8 on this model size |
| max_tokens | 49152 | Captures long reasoning chains |
| thinking_budget | 24576 | Balances depth vs speed |
| temperature | 0.6 | Official Qwen3-Thinking recommendation |
| Shape filter | ON | Rejects no-box and multi-box samples before vote |

## Score History

Best real-inference: **0.653** (slot1_wolfram_full_overrides.csv)
Best diagnostic: **0.671** (info_4_t1lock_sheet_rest.csv)

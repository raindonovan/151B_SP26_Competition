# RUN: SFT v5

**Type**: Supervised fine-tuning + adapter inference
**Date**: 2026-05-25 training, real Kaggle inference ~2026-05-25
**Owner**: Thunder (training), claude_strategy (memo test analysis)
**Status**: Memo test analyzed (misleading). Held-out validation NOT done. Real Kaggle near break-even with base.

## What this was

LoRA adapter training on Qwen3-4B-Thinking-2507.
- Dataset: 391 items, 14 trace fixes (5 MCQ replacements + 9 format fixes)
- Training: 16 epochs, 28 min on H100, bs=4/ga=1, linear LR, dropout=0, r=64, α=128
- 4 checkpoints saved at epochs 8, 12, 14, 16
- Memo test (memo_test_v5.py) selected checkpoint-1176 (epoch 12) as winner with 20/20 consistent
- Decision at the time: keep as LoRA adapter, no merge

## Artifacts

- `checkpoints/sft_v5/checkpoint-1176/` (505MB, LFS) — the chosen adapter
- `results/sft_v5_checkpoint_comparison.json` — memo test results
- `scripts/memo_test_v5.py` — the memorization test script
- `scripts/eval_adapter.py` — adapter evaluation script
- `sft/v5/` — training config, logs

## Real Kaggle scores

- v5 adapter on real inference: near base (~0.646 range, NOT improved over base)
- v5 + answer sheet T3+T4 swap (info_4 diagnostic): 0.671

## See also

- `findings.md` — the memorization paradox + Rain's targeted-memorization insight

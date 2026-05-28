# SFT v5 — Untracked Checkpoint Files

## Tracked (safe)
- `checkpoints/sft_v5/checkpoint-1176/adapter_model.safetensors` — TRACKED via git LFS. Selected as best checkpoint (20/20 memorization test, epoch 12).

## Untracked (Thunder tnr-0 disk only)
Location: `~/151B_SP26_Competition/checkpoints/sft_v5/`
- `checkpoint-*/optimizer.pt` (~1GB each) — optimizer state, resume only
- Other `checkpoint-*/adapter_model.safetensors` — non-selected epoch checkpoints

## Why untracked
v5 scored ~0.646 (break-even with base). The winning checkpoint (1176) is tracked. Other checkpoints are intermediate. Optimizer states only for resume (not planned).

## What this was
391-item dataset, 16 epochs, QLoRA r=64 alpha=128. Memorization confirmed but generalization failed. See `findings.md` in `inference/runs/adapters/sft_v5/`.

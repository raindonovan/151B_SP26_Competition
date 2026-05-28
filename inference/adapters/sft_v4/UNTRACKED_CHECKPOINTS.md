# SFT v4 — Untracked Checkpoint Files

## Tracked (safe)
- `checkpoints/sft_v4/checkpoint-588/adapter_model.safetensors` — TRACKED via git LFS. This is the selected best checkpoint.

## Untracked (Thunder tnr-0 disk only)
Location: `~/151B_SP26_Competition/checkpoints/sft_v4/`
- `checkpoint-*/optimizer.pt` (~1GB each) — optimizer state, resume only
- Other `checkpoint-*/adapter_model.safetensors` — non-selected epoch checkpoints

## Why untracked
SFT v4 scored 0.597. The winning checkpoint (588) is tracked. Other checkpoints are intermediate — preserved on disk but not worth LFS. Optimizer states only needed for resume (not planned).

## What this was
391-item clean dataset, QLoRA r=64 alpha=128, 8 epochs, wd=0. See `scripts/train_sft_v4.py`.

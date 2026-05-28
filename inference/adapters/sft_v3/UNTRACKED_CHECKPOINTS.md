# SFT v3 — Untracked Checkpoint Files

These files exist on Thunder tnr-0 local disk only. Not git-tracked (too large, not needed for inference).

## Location
Thunder tnr-0: `~/151B_SP26_Competition/checkpoints/sft_v3/`

## Files
- `checkpoint-*/optimizer.pt` (~1GB each) — optimizer state for training resume only
- `checkpoint-*/adapter_model.safetensors` (~505MB each) — LoRA adapter weights per epoch

## Why untracked
SFT v3 scored 0.452 on Kaggle — worst performing adapter. Weights preserved on disk for postmortem analysis but not worth LFS storage. Only useful if revisiting v3's failure mode.

## What this was
QLoRA adapter trained on teacher-consensus traces. 8 epochs on H100. Failed due to training on wrong-answer items without proper weighting. See `SFT_V3_TRAINING_LOG.md` in this folder.

# SFT v3 Training Log — CSE 151B SP26 Competition

**Status:** Complete — all 8 epochs trained, all smoke tests passed  
**Date:** 2026-05-22  
**Agent:** claude_thunder (Thunder Compute instance)  
**Authored by:** Rain + claude_thunder

---

## 1. Objective

Train a LoRA adapter on `Qwen/Qwen3-4B-Thinking-2507` using SFT on 594 teacher-labeled competition items. Goal: teach the model to reproduce the `<think>...</think>\n\n\boxed{}` format with high-quality reasoning traces, then hand the merged model to claude_vscode on DSMLP for full 943-item inference.

This is **Phase 3, SFT v3** — the third attempt at SFT. v1 failed catastrophically (max_seq_length=4096 truncated 50%+ of traces; models learned to ramble without boxing). v2 was not attempted. v3 is the first successful run.

---

## 2. Hardware & Environment

| Field | Value |
|---|---|
| GPU | NVIDIA A100-SXM4-80GB (80 GB VRAM) |
| CUDA | 13.0 |
| Driver | 580.126.20 |
| Instance | Thunder Compute (persistent disk: `~/`, ephemeral NVMe wiped on stop) |
| Python | 3.12.13 |
| OS | Ubuntu 22.04 |

### Package Versions

| Package | Version |
|---|---|
| torch | 2.11.0+cu130 |
| transformers | 5.9.0 |
| trl | 0.24.0 |
| peft | 0.19.1 |
| unsloth | 2026.5.5 (Xformers fallback — Flash Attention 2 broken) |
| bitsandbytes | 0.49.2 |
| datasets | (current) |

**Known conflict:** unsloth-zoo wants transformers≤5.5.0 but vllm needs 5.9.0. Did not cause issues in practice.

### Runtime Fixes Required (for reproducibility)

Two environment issues hit before training could start:

1. **`/ephemeral` missing after instance stop/start** — NVMe wiped as expected. HF cache moved to `~/hf_cache` on persistent disk (80 GB free).
   ```bash
   export HF_HOME=~/hf_cache
   ```

2. **`libnvJitLink.so.13` not in `LD_LIBRARY_PATH`** — bitsandbytes crashed on import. Library exists at `/usr/local/cuda/targets/x86_64-linux/lib/`. Fix:
   ```bash
   export LD_LIBRARY_PATH=/usr/local/cuda/targets/x86_64-linux/lib:$LD_LIBRARY_PATH
   ```

Full launch command for reproducibility:
```bash
source ~/venv/bin/activate
export HF_HOME=~/hf_cache
export LD_LIBRARY_PATH=/usr/local/cuda/targets/x86_64-linux/lib:$LD_LIBRARY_PATH
cd ~/151B_SP26_Competition
python scripts/train_sft_v3.py 2>&1 | tee sft_v3_train.log
```

---

## 3. Dataset

| Field | Value |
|---|---|
| File | `sft_v3_dataset_final.jsonl` |
| SHA256 | `901b86dca5be94e486d811672a3d4d8cdfd5d424ad93c7b2e57facb227b0605f` |
| Total items | 594 |
| Storage | Git LFS (file is a pointer in repo; `git lfs pull` required) |
| Produced by | claude_dataApp |

### Tier Breakdown

| Tier | Count | Description |
|---|---|---|
| R1/R2 | 392 (66%) | Model got right — reinforce correct traces |
| W2 | 154 (26%) | Model got wrong, strong teacher signal available |
| W1 | 48 (8%) | Model got wrong, weaker teacher signal |

### Format Verification

- Items with `</think>` tag: **594/594 (100%)**
- Items with `\boxed{}`: **594/594 (100%)**
- Format: `[system, user, assistant]` messages, 3 messages per item

### Token Length Profile (assistant responses, word-level proxy)

| Percentile | Words |
|---|---|
| p50 | 71 |
| p90 | 215 |
| p99 | 400 |
| max | 475 |

`max_seq_length=4096` covers all items with no truncation (unlike v1 where 4096 tokens truncated ~50% of traces — those were much longer R1-distill outputs).

---

## 4. Model Configuration

### Base Model

| Field | Value |
|---|---|
| Model ID | `Qwen/Qwen3-4B-Thinking-2507` |
| Architecture | Qwen3 4B, thinking-mode variant |
| Parameters | 4.15B total |
| dtype | bfloat16 |
| Loading | `device_map="auto"`, no quantization |

### LoRA Configuration

| Parameter | Value | Rationale |
|---|---|---|
| r | 64 | Aggressive — intentional overfitting to 594 items |
| lora_alpha | 128 | 2× r (standard scaling) |
| lora_dropout | 0.05 | Light regularization |
| target_modules | q, k, v, o, gate, up, down proj | All attention + MLP = full expressivity |
| bias | none | Standard |
| Trainable params | 132,120,576 (3.18%) | |
| Total params | 4,154,588,672 | |

### Training Hyperparameters

| Parameter | Value | Rationale |
|---|---|---|
| num_train_epochs | 8 | Heavy memorization intended |
| per_device_train_batch_size | 2 | A100 80GB constraint |
| gradient_accumulation_steps | 8 | Effective batch = 16 |
| learning_rate | 2e-4 | Research consensus for LoRA SFT |
| lr_scheduler_type | cosine | Standard decay |
| warmup_ratio | 0.05 | ~15 warmup steps |
| weight_decay | 0.01 | Light L2 |
| bf16 | True | |
| optim | adamw_torch | Standard; no bitsandbytes paged optimizer needed |
| max_seq_length | 4096 | Covers p99 of trace lengths |
| packing | False | CRITICAL — packing breaks `<think>` attention spans |
| save_strategy | epoch | All 8 checkpoints saved |
| logging_steps | 5 | |

### Loss Masking

`DataCollatorForCompletionOnlyLM` was removed in trl 0.24.0. Replaced with custom `AssistantOnlyCollator` in `scripts/train_sft_v3.py`. This collator:
1. Finds the last occurrence of `<|im_start|>assistant` token IDs `[151644, 77091]` in each sequence
2. Sets `labels = -100` for all tokens up to and including the template
3. Computes loss **only on the assistant's response** (thinking trace + final answer)

This correctly prevents the model from being penalized for predicting system/user tokens.

---

## 5. trl 0.24.0 API Changes (Breaking — Fixed in Script)

The original `scripts/train_sft_v3.py` from claude_strategy was written for an earlier trl version. Three breaking changes required fixes:

| Old API | New API (trl 0.24.0) | Fix |
|---|---|---|
| `from trl import DataCollatorForCompletionOnlyLM` | Removed entirely | Custom `AssistantOnlyCollator` class |
| `TrainingArguments` from transformers | `SFTConfig` from trl | Import + replace |
| `SFTTrainer(tokenizer=...)` | `SFTTrainer(processing_class=...)` | Rename param |
| `SFTTrainer(max_seq_length=...)` | `SFTConfig(max_length=...)` | Move to config |
| `SFTConfig(assistant_only_loss=True)` | Requires `{% generation %}` in chat template | Replaced with custom collator |

`Qwen3-4B-Thinking-2507`'s chat template does not include `{% generation %}` markers, so `assistant_only_loss=True` in SFTConfig raised a RuntimeError. The custom collator sidesteps this entirely.

---

## 6. Dry Run

**Purpose:** Verify model loads, forward pass works, loss is finite before committing to full training.

**Config:** `max_steps=2` added to TRAINING_CONFIG temporarily.

| Metric | Value |
|---|---|
| Steps | 2 |
| train_loss | **0.9486** (finite ✓, not NaN ✓) |
| mean_token_accuracy | 0.8446 |
| entropy | 0.461 |
| Duration | 52.49s |
| Result | PASS |

Dry run log: `sft_v3_dryrun.log`

---

## 7. Full Training Run

**Date:** 2026-05-22  
**Duration:** 2149s (~35.8 minutes)  
**Total steps:** 304 (38 steps/epoch × 8 epochs; 594 items ÷ batch 16 = 37.125 → 38 rounded up)

### Loss Curve by Epoch

| Epoch | Checkpoint | Loss (at boundary) | Mean Token Acc | LR |
|---|---|---|---|---|
| 1 | checkpoint-38 | 0.3288 | ~0.939 | 1.97e-4 |
| 2 | checkpoint-76 | 0.1925 | ~0.940 | 1.81e-4 |
| 3 | checkpoint-114 | 0.0910 | ~0.980 | 1.48e-4 |
| 4 | checkpoint-152 | 0.0422 | ~0.990 | 1.12e-4 |
| 5 | checkpoint-190 | 0.0177 | ~0.994 | 6.89e-5 |
| 6 | checkpoint-228 | 0.0160 | ~0.997 | 3.16e-5 |
| 7 | checkpoint-266 | 0.0027 | ~0.9995 | 9.37e-6 |
| 8 | checkpoint-304 | 0.0020 | ~0.9994 | 1.49e-7 |

**Final aggregate train_loss:** 0.1148 (mean over all steps)  
**Total tokens processed:** 1.854M  
**Throughput:** 2.211 samples/sec, 0.141 steps/sec

### Loss Curve Interpretation

- Epoch 1→2: Fast initial descent (0.59 → 0.33), model learning format
- Epoch 2→4: Continued descent into memorization territory (0.19 → 0.04)
- Epoch 5→8: Deep memorization (<0.02), near-perfect token prediction
- No loss spikes or instability throughout; grad norms stable (0.02–0.5 range)
- One anomalous grad_norm spike at epoch 5.0 (1.613) — single step, did not affect training

Training log: `sft_v3_train.log`

---

## 8. Checkpoint Inventory

All checkpoints on Thunder persistent disk at `~/151B_SP26_Competition/checkpoints/sft_v3/`. **Not in git** (13 GB total). Smoke test JSONs archived to `results/sft_v3_smoke/`.

| Directory | Epoch | Steps | Loss at Save |
|---|---|---|---|
| `checkpoint-38` | 1 | 38 | ~0.33 |
| `checkpoint-76` | 2 | 76 | ~0.19 |
| `checkpoint-114` | 3 | 114 | ~0.09 |
| `checkpoint-152` | 4 | 152 | ~0.04 |
| `checkpoint-190` | 5 | 190 | ~0.018 |
| `checkpoint-228` | 6 | 228 | ~0.016 |
| `checkpoint-266` | 7 | 266 | ~0.003 |
| `checkpoint-304` | 8 | 304 | ~0.002 |
| `final/` | 8 | 304 | same as checkpoint-304 |

---

## 9. Smoke Tests

**Script:** `scripts/smoke_test.py`  
**Method:** Load base model + LoRA adapter, generate on 10 random items from training set (seed=42), check format compliance.  
**Items tested:** Same 10 items across all 3 checkpoints (fixed seed)

### Format Compliance Gates
- No-box rate > 10% → FAIL (stop, investigate)
- Missing `</think>` rate > 10% → FAIL (stop, investigate)

### Results

#### Epoch 1 — checkpoint-38

| Metric | Value |
|---|---|
| No-box rate | **0% (0/10)** ✅ |
| Missing `</think>` | **0% (0/10)** ✅ |
| Wrong order (`</think>` after `\boxed{}`) | 0/10 ✅ |
| Degenerate outputs | 0/10 ✅ |
| Gate | **PASS** |

Results file: `results/sft_v3_smoke/epoch1_checkpoint38.json`

#### Epoch 4 — checkpoint-152

| Metric | Value |
|---|---|
| No-box rate | **0% (0/10)** ✅ |
| Missing `</think>` | **0% (0/10)** ✅ |
| Wrong order | 0/10 ✅ |
| Degenerate outputs | 0/10 ✅ |
| Gate | **PASS** |

Results file: `results/sft_v3_smoke/epoch4_checkpoint152.json`

#### Epoch 8 — checkpoint-304

| Metric | Value |
|---|---|
| No-box rate | **0% (0/10)** ✅ |
| Missing `</think>` | **0% (0/10)** ✅ |
| Wrong order | 0/10 ✅ |
| Degenerate outputs | 0/10 ✅ |
| Gate | **PASS** |

Results file: `results/sft_v3_smoke/epoch8_checkpoint304.json`

---

## 10. Memorization Check (Epoch 4)

**Method:** For each of the 10 smoke test items, compare the model's `\boxed{}` output against the teacher answer from the training dataset. Tests whether SFT successfully imprinted teacher answers.

| Item ID | Tier | Teacher Answer | Model Answer | Result |
|---|---|---|---|---|
| 0185 | R1/R2 | T,F,T,F,T | T,F,T,F,T | MATCH |
| 0040 | R1/R2 | D = 800 - 50d | D = 800 - 50d | MATCH |
| 0433 | R1/R2 | C | C | MATCH |
| 0385 | R1/R2 | A,A,A | A,A,A | MATCH |
| 0352 | R1/R2 | 68 | 68 | MATCH |
| 0219 | R1/R2 | 27 | 27 | MATCH |
| 0171 | R1/R2 | 20 | 20 | MATCH |
| 0890 | R1/R2 | A,A,C,6 | A,A,C,6 | MATCH |
| 0142 | R1/R2 | 7, 8, 9, 10, 11 | 7, 8, 9, 10, 11 | MATCH |
| 0698 | R1/R2 | -50.92 | -50.92 | MATCH |

**Memorization rate: 10/10 (100%)** at epoch 4.

Note: these 10 items are all R1/R2 tier (model originally got them right — they were in the training set to reinforce format). Memorization on W1/W2 items (where model was originally wrong) has not been tested and is the key question for Kaggle inference.

---

## 11. Bugs & Incidents

### Incident 1: Dataset LFS pointer
- **Symptom:** `sft_v3_dataset_final.jsonl` showed 3 lines, wrong SHA — it was a Git LFS pointer, not the actual data.
- **Cause:** `git-lfs` not installed on Thunder instance.
- **Fix:** `sudo apt-get install git-lfs && git lfs install && git lfs pull`
- **Time lost:** ~10 min

### Incident 2: `/ephemeral` missing
- **Symptom:** `PermissionError: /ephemeral` when model tried to download to HF cache.
- **Cause:** Instance was stopped for billing; ephemeral NVMe is wiped on stop (expected behavior per CLAUDE_THUNDER.md).
- **Fix:** `export HF_HOME=~/hf_cache` (persistent disk, 80 GB free).
- **Time lost:** ~5 min

### Incident 3: bitsandbytes `libnvJitLink.so.13` not found
- **Symptom:** `OSError: libnvJitLink.so.13: cannot open shared object file` — process crashed.
- **Cause:** Library exists at `/usr/local/cuda/targets/x86_64-linux/lib/` but not in `LD_LIBRARY_PATH`.
- **Fix:** `export LD_LIBRARY_PATH=/usr/local/cuda/targets/x86_64-linux/lib:$LD_LIBRARY_PATH`
- **Time lost:** ~10 min

### Incident 4: trl 0.24.0 breaking API changes (3 sub-issues)
- **Symptom 1:** `ImportError: cannot import name 'DataCollatorForCompletionOnlyLM' from 'trl'`
- **Symptom 2:** `RuntimeError: assistant_only_loss=True` requires `{% generation %}` in chat template — Qwen3 template doesn't have it.
- **Symptom 3:** `KeyError: 'attention_mask'` in custom collator — trl 0.24.0 SFTTrainer omits `attention_mask` from dataset features.
- **Root cause:** trl 0.24.0 significantly restructured SFT API. Script was written for older version.
- **Fix:** Custom `AssistantOnlyCollator` class replacing the old collator; `SFTConfig` replacing `TrainingArguments`; `processing_class` replacing `tokenizer` param; generating `attention_mask` from `input_ids` in collator when absent.
- **Time lost:** ~30 min across 4 failed dry runs

### Incident 5: tmux not installed
- **Symptom:** `tmux: command not found`
- **Fix:** `sudo apt-get install -y tmux`
- **Time lost:** 1 min

---

## 12. What's Next

1. **Checkpoint selection:** `scripts/select_checkpoint.py` exists in repo. Awaiting claude_strategy decision on which epoch(s) to merge. Candidates:
   - **Epoch 4** (checkpoint-152): loss=0.04, high memorization, less overfit — likely best generalization
   - **Epoch 8** (checkpoint-304): maximum memorization — best if competition items overlap training distribution

2. **Merge:** `python training/merge_adapter.py --adapter checkpoints/sft_v3/<chosen> --output training/merged/sft_v3_merged_bf16`

3. **Handoff:** Merged BF16 model → claude_vscode on DSMLP for full 943-item inference → Kaggle submission.

---

## 13. Files

| File | Location | Description |
|---|---|---|
| Training script | `scripts/train_sft_v3.py` | Fixed for trl 0.24.0 |
| Smoke test script | `scripts/smoke_test.py` | 10-item format compliance check |
| Checkpoint selector | `scripts/select_checkpoint.py` | Automated checkpoint ranking |
| Dry run log | `sft_v3_dryrun.log` | 2-step test run output |
| Full training log | `sft_v3_train.log` | Complete 304-step log with loss curve |
| Smoke test log | `smoke_results.log` | All 3 checkpoint smoke test outputs |
| Smoke JSONs | `results/sft_v3_smoke/` | Per-item results for ep1, ep4, ep8 |
| Dataset | `sft_v3_dataset_final.jsonl` | 594-item training set (Git LFS) |
| Checkpoints | `checkpoints/sft_v3/` | 13 GB, on Thunder persistent disk only |
| This document | `SFT_V3_TRAINING_LOG.md` | You are here |

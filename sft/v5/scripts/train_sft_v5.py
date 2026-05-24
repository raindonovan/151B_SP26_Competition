#!/usr/bin/env python3
"""
SFT v5 Training Script - Locked Configuration
Qwen3-4B-Thinking adapter on 391-item v5 dataset (lettered MCQs + teacher-consensus fixes).

Differences from v4:
  - DATASET_PATH:    data/sft_v5_dataset.jsonl (lettered MCQ user msgs, 14 fixed traces)
  - OUTPUT_DIR:      ./checkpoints/sft_v5
  - num_train_epochs:    16 (was 8)
  - lr_scheduler_type:   "linear" (was "cosine")
  - lora_dropout:        0.0 (was 0.05; zero dropout for max memorization)
  - save_strategy:       "steps" + save_steps=196 (every ~2 epochs)
                          replaces the v4 SelectiveEpochSaveCallback
  - per_device_train_batch_size: 1 -> 4 (H100 80GB has headroom)
  - gradient_accumulation_steps: 4 -> 1 (effective batch unchanged at 4)
  - Auto-resume from latest checkpoint in OUTPUT_DIR via get_last_checkpoint.
"""

import os
import json
from dataclasses import dataclass
from typing import Any
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
)
from transformers.trainer_utils import get_last_checkpoint
from trl import SFTTrainer, SFTConfig
from peft import LoraConfig, get_peft_model
import torch


@dataclass
class AssistantOnlyCollator:
    """Replaces DataCollatorForCompletionOnlyLM (removed in trl 0.24.0).
    Masks loss on all tokens before and including the assistant response template."""
    tokenizer: Any
    response_template: str = "<|im_start|>assistant"

    def __post_init__(self):
        self.template_ids = self.tokenizer.encode(
            self.response_template, add_special_tokens=False
        )

    def __call__(self, features):
        # trl 0.24.0 SFTTrainer may not include attention_mask in features
        has_attn_mask = "attention_mask" in features[0]
        pad_input = {"input_ids": [f["input_ids"] for f in features]}
        if has_attn_mask:
            pad_input["attention_mask"] = [f["attention_mask"] for f in features]

        padded = self.tokenizer.pad(pad_input, return_tensors="pt", padding=True)

        if "attention_mask" not in padded:
            padded["attention_mask"] = (padded["input_ids"] != self.tokenizer.pad_token_id).long()
        labels = padded["input_ids"].clone()
        tlen = len(self.template_ids)

        for i in range(labels.shape[0]):
            ids = padded["input_ids"][i].tolist()
            last_pos = -1
            for j in range(len(ids) - tlen + 1):
                if ids[j : j + tlen] == self.template_ids:
                    last_pos = j
            if last_pos == -1:
                labels[i] = torch.full_like(labels[i], -100)
            else:
                labels[i, : last_pos + tlen] = -100
            labels[i][padded["input_ids"][i] == self.tokenizer.pad_token_id] = -100

        padded["labels"] = labels
        return padded


# ============================================================================
# LOCKED PARAMETERS - DO NOT MODIFY WITHOUT RESEARCH JUSTIFICATION
# ============================================================================

MODEL_ID = "Qwen/Qwen3-4B-Thinking-2507"
DATASET_PATH = "data/sft_v5_dataset.jsonl"  # 391 items, lettered MCQs, teacher-consensus fixes
OUTPUT_DIR = "./checkpoints/sft_v5"
MAX_SEQ_LENGTH = 5500  # v5 max=3594, p99=2476; keep v4 setting for headroom

# Training hyperparameters
# v5 changes from v4: 16 epochs, linear LR, dropout=0 (max memorization),
# native step-based saving every 2 epochs.
TRAINING_CONFIG = {
    "num_train_epochs": 16,
    "per_device_train_batch_size": 4,
    "gradient_accumulation_steps": 1,
    "learning_rate": 2.0e-4,
    "lr_scheduler_type": "linear",
    "weight_decay": 0.0,
    "warmup_ratio": 0.05,
    "bf16": True,
    "logging_steps": 5,
    "save_strategy": "steps",   # 391/(1*4) = ~98 steps/epoch -> save_steps=196 ~ every 2 epochs
    "save_steps": 196,
    "save_total_limit": 8,      # 8 checkpoints across 16 epochs
    "optim": "adamw_torch",
    "report_to": "none",
}

# LoRA configuration (aggressive overfitting setup, dropout=0 for v5)
LORA_CONFIG = {
    "r": 64,
    "lora_alpha": 128,
    "lora_dropout": 0.0,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "bias": "none",
    "task_type": "CAUSAL_LM",
}

# ============================================================================
# DATASET LOADING
# ============================================================================

def load_dataset_from_jsonl(path):
    """Load dataset with messages format (system + user + assistant)"""
    with open(path) as f:
        data = [json.loads(line) for line in f]

    print(f"Loaded {len(data)} training examples from {path}")

    # Verify format
    assert all("messages" in item for item in data), "All items must have 'messages' field"
    assert all(len(item["messages"]) == 3 for item in data), "All items must have 3 messages"
    assert all(item["messages"][0]["role"] == "system" for item in data), "First message must be system"

    # Check for </think> tags
    has_think_close = sum(1 for item in data if "</think>" in item["messages"][2]["content"])
    print(f"Items with </think> tag: {has_think_close}/{len(data)}")
    if has_think_close < len(data):
        print("WARNING: Some items missing </think> tag!")

    # Check for \boxed{}
    has_boxed = sum(1 for item in data if "\\boxed{" in item["messages"][2]["content"])
    print(f"Items with \\boxed{{}} tag: {has_boxed}/{len(data)}")
    if has_boxed < len(data):
        print("WARNING: Some items missing \\boxed{} tag!")

    return Dataset.from_list(data)

# ============================================================================
# MODEL & TOKENIZER
# ============================================================================

def load_model_and_tokenizer():
    """Load base model and tokenizer with LoRA adapter"""
    print(f"Loading model: {MODEL_ID}")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        trust_remote_code=True,
        padding_side="right",  # Required for training
    )

    # Qwen models may not have pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )

    # Apply LoRA
    lora_config = LoraConfig(**LORA_CONFIG)
    model = get_peft_model(model, lora_config)

    print("\n=== LoRA Configuration ===")
    model.print_trainable_parameters()

    return model, tokenizer

# ============================================================================
# TRAINING
# ============================================================================

def main():
    print("=" * 80)
    print("SFT v5 Training - Qwen3-4B-Thinking")
    print("=" * 80)

    # Load dataset
    dataset = load_dataset_from_jsonl(DATASET_PATH)
    print(f"\nDataset size: {len(dataset)}")

    # Load model
    model, tokenizer = load_model_and_tokenizer()

    # Training arguments (SFTConfig replaces TrainingArguments in trl 0.24.0)
    training_args = SFTConfig(
        output_dir=OUTPUT_DIR,
        max_length=MAX_SEQ_LENGTH,
        packing=False,          # CRITICAL: packing breaks <think> attention spans
        **TRAINING_CONFIG,
    )

    print("\n=== Training Configuration ===")
    print(f"Epochs: {TRAINING_CONFIG['num_train_epochs']}")
    print(f"Batch size: {TRAINING_CONFIG['per_device_train_batch_size']}")
    print(f"Gradient accumulation: {TRAINING_CONFIG['gradient_accumulation_steps']}")
    print(f"Effective batch size: {TRAINING_CONFIG['per_device_train_batch_size'] * TRAINING_CONFIG['gradient_accumulation_steps']}")
    print(f"Learning rate: {TRAINING_CONFIG['learning_rate']}")
    print(f"Warmup ratio: {TRAINING_CONFIG['warmup_ratio']}")
    print(f"Weight decay: {TRAINING_CONFIG['weight_decay']}")
    print(f"Max sequence length: {MAX_SEQ_LENGTH}")
    print(f"Save strategy: {TRAINING_CONFIG['save_strategy']} every {TRAINING_CONFIG['save_steps']} steps")

    collator = AssistantOnlyCollator(tokenizer=tokenizer)
    print(f"\n=== Loss Configuration ===")
    print(f"Using AssistantOnlyCollator (response_template: '{collator.response_template}')")
    print(f"Template token IDs: {collator.template_ids}")
    print(f"Loss computed on assistant tokens only")

    # Initialize trainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
        data_collator=collator,
    )

    print(f"\n=== Starting Training ===")
    print(f"Total training steps: {len(dataset) // (TRAINING_CONFIG['per_device_train_batch_size'] * TRAINING_CONFIG['gradient_accumulation_steps']) * TRAINING_CONFIG['num_train_epochs']}")
    print(f"Warmup steps: ~{int(len(dataset) // (TRAINING_CONFIG['per_device_train_batch_size'] * TRAINING_CONFIG['gradient_accumulation_steps']) * TRAINING_CONFIG['num_train_epochs'] * TRAINING_CONFIG['warmup_ratio'])}")
    print(f"Checkpoints will be saved every {TRAINING_CONFIG['save_steps']} steps to: {OUTPUT_DIR}")
    print()

    # Auto-resume from latest checkpoint if OUTPUT_DIR exists with a checkpoint.
    last_ckpt = None
    if os.path.isdir(OUTPUT_DIR):
        last_ckpt = get_last_checkpoint(OUTPUT_DIR)
        if last_ckpt:
            print(f"[resume] Found checkpoint at {last_ckpt} -- resuming.")
    trainer.train(resume_from_checkpoint=last_ckpt)

    # Save final model
    trainer.save_model(f"{OUTPUT_DIR}/final")
    print(f"\nTraining complete! Final model saved to {OUTPUT_DIR}/final")
    print("\n=== NEXT STEPS ===")
    print("1. Run smoke test on epoch-4 checkpoint")
    print("2. Generate on R1/R2 items for each checkpoint")
    print("3. Select best checkpoint by no-box rate + teacher agreement")
    print("4. Merge adapter and run full inference")

if __name__ == "__main__":
    main()

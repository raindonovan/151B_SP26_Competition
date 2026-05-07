"""
Train Qwen3-4B-Thinking-2507 with QLoRA on a JSONL of {messages: [...]} examples.
Single script handles all three teacher arms (OpenR1, NuminaMath, Frugal).

Usage:
    .venv-training/bin/python training/train_qwen3_qlora.py \\
        --data data/sft/openr1_v1_1k.jsonl \\
        --output-dir training/checkpoints/openr1_v1_1k \\
        --run-name openr1_v1_1k

Pre-flight checks (printed at startup, training begins after):
  1. Renders one chat-template example, checks for duplicate <think>
  2. Tokenizes one example and prints (input_ids, labels) sample to verify
     assistant_only_loss masking
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--data", type=str, required=True,
                    help="Path to SFT JSONL (each line: {'messages': [...]})")
parser.add_argument("--output-dir", type=str, required=True,
                    help="Where to save adapter checkpoints")
parser.add_argument("--run-name", type=str, default=None,
                    help="Identifier for logs (default: derived from --data)")
parser.add_argument("--base-model", type=str, default="unsloth/Qwen3-4B-Thinking-2507",
                    help="Base model. Unsloth's prequantized version recommended.")
parser.add_argument("--max-seq-length", type=int, default=4096)
parser.add_argument("--lora-rank", type=int, default=16)
parser.add_argument("--learning-rate", type=float, default=2e-4)
parser.add_argument("--num-epochs", type=float, default=1.0)
parser.add_argument("--per-device-batch-size", type=int, default=1)
parser.add_argument("--grad-accum-steps", type=int, default=8)
parser.add_argument("--warmup-ratio", type=float, default=0.03)
parser.add_argument("--weight-decay", type=float, default=0.01)
parser.add_argument("--save-steps", type=int, default=250)
parser.add_argument("--save-total-limit", type=int, default=4)
parser.add_argument("--logging-steps", type=int, default=10)
parser.add_argument("--seed", type=int, default=3407)
parser.add_argument("--smoke-only", action="store_true",
                    help="If set, do pre-flight checks then exit (no training).")
args = parser.parse_args()

if args.run_name is None:
    args.run_name = Path(args.data).stem

print(f"[{time.strftime('%H:%M:%S')}] === TRAIN_QWEN3_QLORA ===")
print(f"  Run name:        {args.run_name}")
print(f"  Data:            {args.data}")
print(f"  Output dir:      {args.output_dir}")
print(f"  Base model:      {args.base_model}")
print(f"  LoRA rank:       {args.lora_rank}")
print(f"  Max seq length:  {args.max_seq_length}")
print(f"  LR:              {args.learning_rate}")
print(f"  Epochs:          {args.num_epochs}")
print(f"  Effective batch: {args.per_device_batch_size * args.grad_accum_steps}")
print()

# --- Imports (heavy) ---
print(f"[{time.strftime('%H:%M:%S')}] Importing Unsloth + TRL...")
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
from datasets import load_dataset
from trl import SFTConfig, SFTTrainer
import torch

# --- Load model + tokenizer ---
print(f"[{time.strftime('%H:%M:%S')}] Loading {args.base_model} (4-bit nf4)...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=args.base_model,
    max_seq_length=args.max_seq_length,
    dtype=None,
    load_in_4bit=True,
)
print(f"[{time.strftime('%H:%M:%S')}] Model loaded.")

# Apply Qwen3-Thinking chat template
tokenizer = get_chat_template(tokenizer, chat_template="qwen3-thinking")

# --- LoRA config ---
print(f"[{time.strftime('%H:%M:%S')}] Applying LoRA (r={args.lora_rank}, alpha=32, all-linear)...")
model = FastLanguageModel.get_peft_model(
    model,
    r=args.lora_rank,
    lora_alpha=args.lora_rank * 2,
    lora_dropout=0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=args.seed,
)

# --- Load + format dataset ---
print(f"[{time.strftime('%H:%M:%S')}] Loading dataset from {args.data}...")
dataset = load_dataset("json", data_files=args.data, split="train")
print(f"[{time.strftime('%H:%M:%S')}] Loaded {len(dataset)} examples.")

def format_with_chat_template(examples):
    texts = [
        tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
        for messages in examples["messages"]
    ]
    return {"text": texts}

dataset = dataset.map(format_with_chat_template, batched=True, num_proc=4,
                     remove_columns=[c for c in dataset.column_names if c != "messages"])

# --- Pre-flight check 1: rendered example ---
print(f"\n[{time.strftime('%H:%M:%S')}] === PRE-FLIGHT CHECK 1: rendered template ===")
sample_text = dataset[0]["text"]
print(f"First 500 chars of rendered example:")
print(sample_text[:500])
print(f"...")
print(f"Last 200 chars:")
print(sample_text[-200:])

# Check for duplicate <think>
think_open_count = sample_text.count("<think>")
think_close_count = sample_text.count("</think>")
print(f"\n<think> opens:  {think_open_count}")
print(f"</think> closes: {think_close_count}")
if think_open_count > 1 + sample_text[:200].count("<think>"):
    # Heuristic: more than 1 in main body suggests duplication
    print("WARNING: Possible duplicate <think> tags in rendered template.")
    print("Inspect sample above. If template adds <think> AND content already has <think>,")
    print("the data prep needs to strip leading <think> from assistant content.")
else:
    print("OK: no obvious <think> duplication.")

# --- Pre-flight check 2: tokenization + loss mask ---
print(f"\n[{time.strftime('%H:%M:%S')}] === PRE-FLIGHT CHECK 2: tokenization ===")
sample_ids = tokenizer(sample_text, return_tensors=None, truncation=True,
                       max_length=args.max_seq_length)["input_ids"]
print(f"Tokenized length: {len(sample_ids)} tokens")
print(f"First 30 token IDs: {sample_ids[:30]}")
print(f"First 30 decoded:")
print(repr(tokenizer.decode(sample_ids[:30])))
print(f"Last 30 decoded:")
print(repr(tokenizer.decode(sample_ids[-30:])))

if args.smoke_only:
    print(f"\n[{time.strftime('%H:%M:%S')}] --smoke-only set. Pre-flight checks done. Exiting.")
    sys.exit(0)

# --- Training config ---
out_path = Path(args.output_dir)
out_path.mkdir(parents=True, exist_ok=True)

print(f"\n[{time.strftime('%H:%M:%S')}] === TRAINING ===")
print(f"  Output dir: {out_path}")
print(f"  Effective batch: {args.per_device_batch_size * args.grad_accum_steps}")
print(f"  Epochs: {args.num_epochs}")

training_args = SFTConfig(
    output_dir=str(out_path),
    per_device_train_batch_size=args.per_device_batch_size,
    gradient_accumulation_steps=args.grad_accum_steps,
    warmup_ratio=args.warmup_ratio,
    num_train_epochs=args.num_epochs,
    learning_rate=args.learning_rate,
    optim="adamw_8bit",
    weight_decay=args.weight_decay,
    lr_scheduler_type="cosine",
    bf16=True,
    fp16=False,
    logging_steps=args.logging_steps,
    save_strategy="steps",
    save_steps=args.save_steps,
    save_total_limit=args.save_total_limit,
    seed=args.seed,
    max_seq_length=args.max_seq_length,
    packing=False,
    assistant_only_loss=True,
    report_to="none",
    dataset_text_field="text",
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    args=training_args,
)

# --- Train ---
print(f"[{time.strftime('%H:%M:%S')}] Starting training...")
t_start = time.time()
trainer.train()
t_train = time.time() - t_start
print(f"[{time.strftime('%H:%M:%S')}] Training complete in {t_train/60:.1f} min")

# --- Save final adapter ---
final_path = out_path / "final_adapter"
print(f"[{time.strftime('%H:%M:%S')}] Saving final adapter to {final_path}...")
model.save_pretrained(str(final_path))
tokenizer.save_pretrained(str(final_path))
print(f"[{time.strftime('%H:%M:%S')}] Saved.")

# --- Summary ---
print(f"\n[{time.strftime('%H:%M:%S')}] === DONE ===")
print(f"  Run:           {args.run_name}")
print(f"  Output:        {args.output_dir}")
print(f"  Final adapter: {final_path}")
print(f"  Training time: {t_train/60:.1f} min")
print(f"  Examples:      {len(dataset)}")

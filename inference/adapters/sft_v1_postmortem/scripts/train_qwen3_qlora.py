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
  2. Tokenizes one example and prints the token sequence
  3. Computes assistant-only eval-loss against the (untrained-LoRA) model on
     an 8-row held-out batch; aborts if the value is non-finite or outside
     [0.5, 5.0] nats. Catches mask-construction bugs before any training
     compute is committed.
"""
import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("WANDB_PROJECT", "cse151b-sft")

parser = argparse.ArgumentParser()
parser.add_argument("--data", type=str, required=True,
                    help="Path to SFT JSONL (each line: {'messages': [...]})")
parser.add_argument("--output-dir", type=str, required=True,
                    help="Where to save adapter checkpoints")
parser.add_argument("--run-name", type=str, default=None,
                    help="Identifier for logs (default: derived from --data)")
parser.add_argument("--base-model", type=str, default="unsloth/Qwen3-4B-Thinking-2507",
                    help="Base model. Unsloth's prequantized version recommended.")
parser.add_argument("--max-seq-length", type=int, default=8192)
parser.add_argument("--lora-rank", type=int, default=16)
parser.add_argument("--lora-alpha", type=int, default=32,
                    help="default 32 matches v1 behavior at rank=16 (16*2). "
                         "For v2 (rank=32, Schulman default alpha==rank), pass --lora-alpha 32 explicitly.")
parser.add_argument("--learning-rate", type=float, default=2e-4)
parser.add_argument("--num-epochs", type=float, default=1.0)
parser.add_argument("--per-device-batch-size", type=int, default=2)
parser.add_argument("--grad-accum-steps", type=int, default=4)
parser.add_argument("--warmup-ratio", type=float, default=0.03)
parser.add_argument("--weight-decay", type=float, default=0.01)
parser.add_argument("--save-steps", type=int, default=250)
parser.add_argument("--save-total-limit", type=int, default=4)
parser.add_argument("--logging-steps", type=int, default=10)
parser.add_argument("--seed", type=int, default=3407)
parser.add_argument("--smoke-only", action="store_true",
                    help="If set, do pre-flight checks then exit (no training).")
parser.add_argument("--max-steps", type=int, default=-1,
                    help="If >0, override num_train_epochs (for smoke/throughput tests).")
parser.add_argument("--no-padding-free", action="store_true",
                    help="Explicitly pass padding_free=False to SFTConfig (disables Unsloth's auto-enable, "
                         "for throughput experiments). Default behavior unchanged when flag is absent.")
parser.add_argument("--dataloader-num-workers", type=int, default=0,
                    help="Number of dataloader workers. Default 0 (inline; main thread blocks on data prep). "
                         "Try 4 for I/O-bound pipelines.")
parser.add_argument("--dataloader-prefetch-factor", type=int, default=None,
                    help="Per-worker prefetch factor. Auto-set to 2 when --dataloader-num-workers > 0.")
parser.add_argument("--no-dataloader-pin-memory", action="store_true",
                    help="Disable dataloader pin_memory (default: pin_memory=True).")
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
from transformers import TrainerCallback
import torch
import torch.nn.functional as F


class AssistantOnlyEvalLossCallback(TrainerCallback):
    """Logs cross-entropy restricted to the assistant span on a fixed held-out batch.

    Diagnostic for full-sequence training (v2 default per the 2026-05-08 reframe).
    The standard `train/loss` mixes easy-to-memorize prompt tokens with assistant
    content; this metric reports loss on the assistant span alone so genuine
    learning progress is observable. Fires at every save_steps boundary via
    `on_save`. See DESIGN.md §7 > Diagnostic: assistant-only eval-loss metric.
    """
    METRIC_NAME = "eval/assistant_only_loss"

    def __init__(self, input_ids_list, labels_list):
        self.input_ids_list = [torch.tensor(ids, dtype=torch.long) for ids in input_ids_list]
        self.labels_list = [torch.tensor(lbl, dtype=torch.long) for lbl in labels_list]

    @torch.no_grad()
    def compute(self, model) -> float:
        device = next(model.parameters()).device
        was_training = model.training
        model.eval()
        total_loss_sum = 0.0
        total_token_count = 0
        try:
            for ids, labels in zip(self.input_ids_list, self.labels_list):
                ids_b = ids.unsqueeze(0).to(device)
                labels_b = labels.unsqueeze(0).to(device)
                attn_b = torch.ones_like(ids_b)
                outputs = model(input_ids=ids_b, attention_mask=attn_b, use_cache=False)
                shift_logits = outputs.logits[:, :-1, :].contiguous()
                shift_labels = labels_b[:, 1:].contiguous()
                graded = shift_labels != -100
                n_graded = int(graded.sum().item())
                if n_graded == 0:
                    continue
                loss_sum = F.cross_entropy(
                    shift_logits.reshape(-1, shift_logits.size(-1)),
                    shift_labels.reshape(-1),
                    ignore_index=-100,
                    reduction="sum",
                )
                total_loss_sum += float(loss_sum.item())
                total_token_count += n_graded
        finally:
            if was_training:
                model.train()
        if total_token_count == 0:
            raise RuntimeError(
                "AssistantOnlyEvalLoss: zero graded tokens across eval batch. "
                "Mask construction is broken — inspect the eval batch."
            )
        return total_loss_sum / total_token_count

    def on_save(self, args, state, control, model=None, **kwargs):
        if model is None:
            return
        try:
            value = self.compute(model)
        except Exception as exc:
            print(f"[AssistantOnlyEvalLoss] compute failed at step {state.global_step}: {exc}")
            return
        print(f"[{time.strftime('%H:%M:%S')}] {self.METRIC_NAME} @ step {state.global_step}: {value:.4f}")
        try:
            import wandb
            if wandb.run is not None:
                wandb.log({self.METRIC_NAME: value}, step=state.global_step)
        except Exception:
            pass


def find_last_subseq(seq, sub):
    """Return the start index of the last occurrence of `sub` in `seq`, or -1."""
    n, m = len(seq), len(sub)
    for i in range(n - m, -1, -1):
        if seq[i:i + m] == sub:
            return i
    return -1


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
    lora_alpha=args.lora_alpha,
    lora_dropout=0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    bias="none",
    # use_gradient_checkpointing="unsloth": re-enabled 2026-05-09 for memory
    # headroom on v2 OpenR1's longer reasoning traces (max_seq_length=11000+).
    # The 2026-05-08 throughput investigation that disabled this is moot —
    # activation checkpointing's memory savings are required to fit the longer
    # sequences. SFTConfig's gradient_checkpointing=True below is the matching
    # trainer-side flag.
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

# --- Hold out the last 8 rows for the eval/assistant_only_loss metric ---
HOLDOUT_N = 8
total_n = len(dataset)
if total_n <= HOLDOUT_N:
    raise RuntimeError(
        f"Dataset has {total_n} rows; need > {HOLDOUT_N} for the eval/assistant_only_loss metric."
    )
eval_holdout = dataset.select(range(total_n - HOLDOUT_N, total_n))
dataset = dataset.select(range(total_n - HOLDOUT_N))
print(f"[{time.strftime('%H:%M:%S')}] Eval holdout: last {HOLDOUT_N} rows. "
      f"Training set: {len(dataset)} rows.")

# Build the eval batch for AssistantOnlyEvalLossCallback. Mask construction
# uses last-occurrence token-id matching of "<|im_start|>assistant\n" rather
# than apply_chat_template(return_assistant_tokens_mask=True), since unsloth's
# qwen3-thinking template lacks {% generation %} markers (per experiments.md
# > External Review Insights > 2026-05-08 entry).
ASSISTANT_MARKER_TEXT = "<|im_start|>assistant\n"
marker_ids = tokenizer.encode(ASSISTANT_MARKER_TEXT, add_special_tokens=False)
if not marker_ids:
    raise RuntimeError(f"Could not encode {ASSISTANT_MARKER_TEXT!r} into tokens.")

eval_input_ids_list = []
eval_labels_list = []
for row in eval_holdout:
    ids = tokenizer(row["text"], truncation=True, max_length=args.max_seq_length,
                    return_tensors=None)["input_ids"]
    marker_pos = find_last_subseq(ids, marker_ids)
    if marker_pos < 0:
        raise RuntimeError(
            f"Eval batch construction: could not find {ASSISTANT_MARKER_TEXT!r} marker tokens "
            f"{marker_ids} in tokenized eval row of length {len(ids)}. "
            f"Last 30 token ids: {ids[-30:]}."
        )
    span_start = marker_pos + len(marker_ids)
    if span_start >= len(ids):
        raise RuntimeError(
            f"Eval batch construction: assistant span starts at or beyond end of input "
            f"(span_start={span_start}, len={len(ids)}). Truncation likely cut off all "
            f"assistant content — increase --max-seq-length or hold out shorter rows."
        )
    labels = [-100] * len(ids)
    for i in range(span_start, len(ids)):
        labels[i] = ids[i]
    eval_input_ids_list.append(ids)
    eval_labels_list.append(labels)

eval_callback = AssistantOnlyEvalLossCallback(eval_input_ids_list, eval_labels_list)

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

# --- Pre-flight check 2: tokenization ---
print(f"\n[{time.strftime('%H:%M:%S')}] === PRE-FLIGHT CHECK 2: tokenization ===")
sample_ids = tokenizer(sample_text, return_tensors=None, truncation=True,
                       max_length=args.max_seq_length)["input_ids"]
print(f"Tokenized length: {len(sample_ids)} tokens")
print(f"First 30 token IDs: {sample_ids[:30]}")
print(f"First 30 decoded:")
print(repr(tokenizer.decode(sample_ids[:30])))
print(f"Last 30 decoded:")
print(repr(tokenizer.decode(sample_ids[-30:])))

# --- Pre-flight check 3: assistant-only eval-loss base-model gate ---
# Verifies (1) the assistant-mask boundary lands where expected and (2) the
# computed metric is finite and in a sane range against the untrained-LoRA
# model. Aborts before any training compute if either fails.
print(f"\n[{time.strftime('%H:%M:%S')}] === PRE-FLIGHT CHECK 3: assistant-only eval-loss ===")

ids0 = eval_input_ids_list[0]
labels0 = eval_labels_list[0]
graded_indices = [i for i, l in enumerate(labels0) if l != -100]
if not graded_indices:
    raise RuntimeError("PRE-FLIGHT 3 FAILED: eval example 0 has no graded tokens.")
span0 = graded_indices[0]
print(f"Eval example 0: {len(ids0)} tokens total, "
      f"{span0} masked (system+user+separator), "
      f"{len(ids0) - span0} graded (assistant content).")
masked_text = tokenizer.decode(ids0[:span0])
graded_text = tokenizer.decode(ids0[span0:])
print(f"Last 80 chars of MASKED region: ...{masked_text[-80:]!r}")
print(f"First 80 chars of GRADED region: {graded_text[:80]!r}...")

base_loss = eval_callback.compute(model)
print(f"Base-model {AssistantOnlyEvalLossCallback.METRIC_NAME} = {base_loss:.4f} nats "
      f"over {HOLDOUT_N} held-out examples.")
if not math.isfinite(base_loss):
    raise RuntimeError(
        f"PRE-FLIGHT 3 FAILED: Base-model {AssistantOnlyEvalLossCallback.METRIC_NAME}={base_loss} "
        f"is not finite. The metric implementation is broken. Inspect the masked-decode "
        f"output above and the eval batch construction."
    )
if not (0.5 <= base_loss <= 5.0):
    raise RuntimeError(
        f"PRE-FLIGHT 3 FAILED: Base-model {AssistantOnlyEvalLossCallback.METRIC_NAME}={base_loss:.4f} "
        f"nats, outside expected sanity range [0.5, 5.0]. Probable causes: "
        f"(1) assistant-mask construction is wrong (graded tokens include system/user content); "
        f"(2) the base model is unexpectedly far from in-distribution on math reasoning; "
        f"(3) the eval batch contains malformed rows. Inspect the masked-decode output above."
    )
print("PRE-FLIGHT 3 PASSED.")

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

_sft_kwargs = dict(
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
    # gradient_checkpointing=True: re-enabled 2026-05-09 for memory headroom on
    # v2 OpenR1's longer reasoning traces (max_seq_length=11000+). Matches
    # use_gradient_checkpointing="unsloth" at the LoRA-attach call above. The
    # 2026-05-08 throughput investigation that disabled this is moot — memory
    # savings outweigh throughput cost at these sequence lengths.
    gradient_checkpointing=True,
    packing=False,
    # assistant_only_loss=False per 2026-05-08 v1 post-mortem reframe (Unsloth
    # silently ignored True; full-sequence loss is what we actually train under).
    # See experiments.md > External Review Insights > 2026-05-08 entry for the
    # full investigation trace; DESIGN.md §7 > Loss target paragraph for the
    # rationale (Huerta-Enochian & Lee 2024 + Sky-T1 / NovaSky 2025).
    assistant_only_loss=False,
    report_to="wandb",
    run_name=args.run_name,
    dataset_text_field="text",
)
if args.max_steps > 0:
    _sft_kwargs["max_steps"] = args.max_steps
if args.no_padding_free:
    _sft_kwargs["padding_free"] = False
if args.dataloader_num_workers > 0:
    _sft_kwargs["dataloader_num_workers"] = args.dataloader_num_workers
    _sft_kwargs["dataloader_prefetch_factor"] = (
        args.dataloader_prefetch_factor if args.dataloader_prefetch_factor is not None else 2
    )
if args.no_dataloader_pin_memory:
    _sft_kwargs["dataloader_pin_memory"] = False
training_args = SFTConfig(**_sft_kwargs)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    args=training_args,
    callbacks=[eval_callback],
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

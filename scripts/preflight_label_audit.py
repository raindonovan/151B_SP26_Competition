"""
One-shot pre-flight label audit (NOT part of the training pipeline).

Renders the first 5 rows of data/sft/numina_concise_v2_8k.jsonl through the
exact tokenization path used by training/train_qwen3_qlora.py, then
constructs labels as DataCollatorForLanguageModeling does under v2's
full-sequence loss config (assistant_only_loss=False), and decodes the
positions where labels != -100 to confirm what gradient signal flows
through training.

Discardable after run.
"""
import json
import sys
import time
from pathlib import Path

DATA_PATH = "data/sft/numina_concise_v2_8k.jsonl"
BASE_MODEL = "unsloth/Qwen3-4B-Thinking-2507"
MAX_SEQ_LENGTH = 8192
N_ROWS = 5

print(f"[{time.strftime('%H:%M:%S')}] Importing Unsloth + tokenizer...")
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template

print(f"[{time.strftime('%H:%M:%S')}] Loading {BASE_MODEL} (4-bit nf4)...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,
    load_in_4bit=True,
)
print(f"[{time.strftime('%H:%M:%S')}] Model + tokenizer loaded.")

# Apply same chat template as training
tokenizer = get_chat_template(tokenizer, chat_template="qwen3-thinking")
print(f"[{time.strftime('%H:%M:%S')}] Chat template 'qwen3-thinking' applied.")
print(f"  pad_token: {tokenizer.pad_token!r} (id={tokenizer.pad_token_id})")
print(f"  eos_token: {tokenizer.eos_token!r}")

# Load first N rows
print(f"\n[{time.strftime('%H:%M:%S')}] Loading first {N_ROWS} rows from {DATA_PATH}...")
rows = []
with open(DATA_PATH) as f:
    for i, line in enumerate(f):
        if i >= N_ROWS:
            break
        rows.append(json.loads(line))
print(f"Loaded {len(rows)} rows.")

REQUIRED_MARKERS = [
    "<|im_start|>system",
    "<|im_start|>user",
    "<|im_start|>assistant",
    "<think>",
    "</think>",
    "\\boxed{",
]

per_row_stats = []

for ridx, row in enumerate(rows):
    print(f"\n{'='*80}")
    print(f"ROW {ridx}")
    print(f"{'='*80}")

    msgs = row["messages"]
    user_msg = next((m["content"] for m in msgs if m["role"] == "user"), "")
    print(f"Source user-msg (first 80 chars): {user_msg[:80]!r}")

    # Render via training-path apply_chat_template
    rendered = tokenizer.apply_chat_template(
        msgs, tokenize=False, add_generation_prompt=False
    )

    # Tokenize via training-path tokenizer call (no padding for individual rows)
    enc = tokenizer(rendered, truncation=True, max_length=MAX_SEQ_LENGTH, padding=False)
    input_ids = list(enc["input_ids"])

    # Construct labels exactly as DataCollatorForLanguageModeling does:
    # labels = input_ids.clone(); labels[labels == pad_token_id] = -100.
    # No padding here since each example is processed individually; included
    # for faithfulness to the training collator path.
    labels = list(input_ids)
    pad_id = tokenizer.pad_token_id
    if pad_id is not None:
        for i, t in enumerate(labels):
            if t == pad_id:
                labels[i] = -100

    n_total = len(input_ids)
    n_masked = sum(1 for l in labels if l == -100)
    n_graded = n_total - n_masked

    print(f"Token count:      {n_total}")
    print(f"-100 positions:   {n_masked}")
    print(f"Graded positions: {n_graded}")

    print(f"\n--- DECODED RENDERED TEXT (full) ---")
    print(rendered)

    print(f"\n--- DECODED TEXT FROM GRADED POSITIONS (full) ---")
    graded_ids = [t for t, l in zip(input_ids, labels) if l != -100]
    graded_text = tokenizer.decode(graded_ids)
    print(graded_text)

    markers_present = {m: m in rendered for m in REQUIRED_MARKERS}

    per_row_stats.append({
        "ridx": ridx,
        "n_total": n_total,
        "n_graded": n_graded,
        "markers": markers_present,
    })

# --- Summary ---
print(f"\n\n{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")

print(f"\nPer-row stats:")
print(f"  {'row':>4} {'tokens':>8} {'graded':>8}  markers all present")
for st in per_row_stats:
    all_markers = all(st["markers"].values())
    missing = [m for m, p in st["markers"].items() if not p]
    suffix = "" if all_markers else f"  (missing: {missing})"
    print(f"  {st['ridx']:>4} {st['n_total']:>8} {st['n_graded']:>8}  {all_markers}{suffix}")

all_pass = True

# Check 1: graded > 0 every row
check1 = all(st["n_graded"] > 0 for st in per_row_stats)
print(f"\nCheck 1 (graded tokens > 0 for every row): {'PASS' if check1 else 'FAIL'}")
all_pass = all_pass and check1

# Check 2: structural markers present every row
check2_failures = [
    (st["ridx"], [m for m, p in st["markers"].items() if not p])
    for st in per_row_stats
    if not all(st["markers"].values())
]
check2 = len(check2_failures) == 0
print(f"Check 2 (structural markers present in every row): {'PASS' if check2 else 'FAIL'}")
for ridx, missing in check2_failures:
    print(f"    Row {ridx} missing: {missing}")
all_pass = all_pass and check2

# Check 3: token counts in [50, 4000]
check3_failures = [
    (st["ridx"], st["n_total"])
    for st in per_row_stats
    if st["n_total"] < 50 or st["n_total"] > 4000
]
check3 = len(check3_failures) == 0
print(f"Check 3 (token count in [50, 4000]): {'PASS' if check3 else 'FAIL'}")
for ridx, count in check3_failures:
    print(f"    Row {ridx}: {count} tokens (out of range)")
all_pass = all_pass and check3

print(f"\nOVERALL: {'ALL PASS' if all_pass else 'FAIL'}")
sys.exit(0 if all_pass else 1)

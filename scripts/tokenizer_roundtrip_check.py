"""
One-shot tokenizer round-trip check (NOT part of the training pipeline).

Runs the same chat-template rendering and tokenization in whichever venv
this script is invoked from. Saves token-id sequences, SHA256 hashes of
both the rendered strings and the token-id sequences, and tokenizer-state
metadata (pad_token, eos_token, chat_template hash) for cross-venv comparison.

Run twice:
  .venv-training/bin/python scripts/tokenizer_roundtrip_check.py
  .venv/bin/python scripts/tokenizer_roundtrip_check.py

Then:
  diff /tmp/tokenizer_roundtrip_training.json /tmp/tokenizer_roundtrip_inference.json

Discardable after run.
"""
import hashlib
import json
import sys
from pathlib import Path

DATA_PATH = "data/sft/numina_concise_v2_8k.jsonl"
BASE_MODEL = "unsloth/Qwen3-4B-Thinking-2507"
MAX_SEQ_LENGTH = 8192
N_ROWS = 5

import transformers
TF_VERSION = transformers.__version__
print(f"transformers: {TF_VERSION}")
print(f"executable:   {sys.executable}")

unsloth_available = False
try:
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import get_chat_template
    unsloth_available = True
except ImportError:
    pass
print(f"unsloth available: {unsloth_available}")

# Tokenizer load — Unsloth path matches training; fallback uses AutoTokenizer
# with whatever chat_template is bundled in the model repo's tokenizer_config.
if unsloth_available:
    print("Loading via Unsloth FastLanguageModel + get_chat_template('qwen3-thinking')...")
    _, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=True,
    )
    tokenizer = get_chat_template(tokenizer, chat_template="qwen3-thinking")
    template_path = "unsloth/get_chat_template('qwen3-thinking')"
else:
    print("Unsloth unavailable; loading via AutoTokenizer with bundled chat_template.")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    template_path = "AutoTokenizer/bundled"

template_str = tokenizer.chat_template or ""
template_sha = hashlib.sha256(template_str.encode()).hexdigest()
print(f"\nTemplate path: {template_path}")
print(f"Template SHA256:    {template_sha}")
print(f"Template length:    {len(template_str)} chars")
print(f"pad_token:          {tokenizer.pad_token!r} (id={tokenizer.pad_token_id})")
print(f"eos_token:          {tokenizer.eos_token!r}")
print(f"vocab_size:         {tokenizer.vocab_size}")
print(f"len(tokenizer):     {len(tokenizer)}")

print(f"\nLoading first {N_ROWS} rows from {DATA_PATH}...")
rows = []
with open(DATA_PATH) as f:
    for i, line in enumerate(f):
        if i >= N_ROWS:
            break
        rows.append(json.loads(line))

per_row = {}
for ridx, row in enumerate(rows):
    rendered = tokenizer.apply_chat_template(
        row["messages"], tokenize=False, add_generation_prompt=False
    )
    enc = tokenizer(rendered, truncation=True, max_length=MAX_SEQ_LENGTH, padding=False)
    ids = list(enc["input_ids"])

    rendered_sha = hashlib.sha256(rendered.encode()).hexdigest()
    ids_str = ",".join(str(i) for i in ids)
    ids_sha = hashlib.sha256(ids_str.encode()).hexdigest()

    per_row[str(ridx)] = {
        "token_count": len(ids),
        "first_20": ids[:20],
        "last_20": ids[-20:],
        "sha256_tokens": ids_sha,
        "sha256_rendered": rendered_sha,
        "rendered_first_120": rendered[:120],
        "rendered_last_120": rendered[-120:],
    }
    print(f"\nRow {ridx}: {len(ids)} tokens")
    print(f"  rendered-sha: {rendered_sha[:32]}...")
    print(f"  tokens-sha:   {ids_sha[:32]}...")
    print(f"  first 20: {ids[:20]}")
    print(f"  last 20:  {ids[-20:]}")

# Pick output filename based on which venv we're in.
exec_path = sys.executable
if "venv-training" in exec_path:
    out_name = "training"
else:
    out_name = "inference"
out_path = f"/tmp/tokenizer_roundtrip_{out_name}.json"

output = {
    "_meta": {
        "transformers_version": TF_VERSION,
        "unsloth_available": unsloth_available,
        "template_path": template_path,
        "chat_template_sha256": template_sha,
        "chat_template_len": len(template_str),
        "pad_token": tokenizer.pad_token,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token": tokenizer.eos_token,
        "vocab_size": tokenizer.vocab_size,
        "len_tokenizer": len(tokenizer),
        "executable": exec_path,
    },
    "rows": per_row,
}
with open(out_path, "w") as f:
    json.dump(output, f, indent=2, sort_keys=True)
print(f"\nSaved {out_path}")

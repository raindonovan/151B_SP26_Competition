"""
Prepare OpenR1-Math-220k SFT training data.
Filters by correctness flag, length range (1000-6000 tokens), single-answer,
parseable boxed answer. Writes Qwen3-Thinking chat-format JSONL.
"""
import argparse
import json
import re
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--target-rows", type=int, default=1000)
parser.add_argument("--output", type=str, default="data/sft/openr1_v1_1k.jsonl")
parser.add_argument("--min-tokens", type=int, default=1000)
parser.add_argument("--max-tokens", type=int, default=6000)
parser.add_argument("--seed", type=int, default=42)
args = parser.parse_args()

from datasets import load_dataset
from transformers import AutoTokenizer

print(f"[{time.strftime('%H:%M:%S')}] Loading tokenizer + OpenR1-Math-220k...")
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-4B-Thinking-2507")
ds = load_dataset("open-r1/OpenR1-Math-220k", "default", split="train")
print(f"[{time.strftime('%H:%M:%S')}] Loaded {len(ds)} rows")

MULTI_PART_RE = re.compile(r"\(a\)|\(b\)|\(i\)|\(ii\)|Part\s+[12]|prove that", re.IGNORECASE)
BOXED_RE = re.compile(r"\\boxed\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}")

def normalize_for_match(s):
    if s is None:
        return ""
    s = str(s).strip()
    s = s.replace(" ", "").replace("\\!", "").replace("\\,", "")
    s = s.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    s = s.replace("\\left", "").replace("\\right", "")
    s = re.sub(r"\\text\{[^}]*\}", "", s)
    return s

def get_first_verified_generation(row):
    correctness = row.get("correctness_math_verify") or []
    if not any(correctness):
        return None
    idx = correctness.index(True)
    gens = row.get("generations") or []
    if idx >= len(gens) or gens[idx] is None:
        return None
    return gens[idx], idx

print(f"[{time.strftime('%H:%M:%S')}] Filtering and tokenizing (this may take 5-10 min)...")
print(f"[{time.strftime('%H:%M:%S')}] Filter: verified single-answer, {args.min_tokens}-{args.max_tokens} tokens, parseable boxed")

ds_shuffled = ds.shuffle(seed=args.seed)

n_attempted = 0
n_no_verified = 0
n_multi_part = 0
n_too_short = 0
n_too_long = 0
n_no_boxed = 0
n_answer_mismatch = 0
n_written = 0

out_dir = Path(args.output).parent
out_dir.mkdir(parents=True, exist_ok=True)

with open(args.output, "w") as out_f:
    for row in ds_shuffled:
        if n_written >= args.target_rows:
            break
        n_attempted += 1
        if n_attempted % 1000 == 0:
            print(f"  [{time.strftime('%H:%M:%S')}] attempted {n_attempted}, written {n_written}...")

        result = get_first_verified_generation(row)
        if result is None:
            n_no_verified += 1
            continue
        gen_text, gen_idx = result

        problem = row.get("problem", "")
        if MULTI_PART_RE.search(problem):
            n_multi_part += 1
            continue

        gen_tokens = len(tok(gen_text, add_special_tokens=False)["input_ids"])
        if gen_tokens < args.min_tokens:
            n_too_short += 1
            continue
        if gen_tokens > args.max_tokens:
            n_too_long += 1
            continue

        boxed_matches = BOXED_RE.findall(gen_text)
        if not boxed_matches:
            n_no_boxed += 1
            continue
        extracted = boxed_matches[-1].strip()

        gold = row.get("answer", "")
        if normalize_for_match(extracted) != normalize_for_match(gold):
            try:
                from math_verify import parse, verify
                e_parsed = parse(f"\\boxed{{{extracted}}}")
                g_parsed = parse(f"\\boxed{{{gold}}}")
                if not bool(verify(g_parsed, e_parsed)):
                    n_answer_mismatch += 1
                    continue
            except Exception:
                n_answer_mismatch += 1
                continue

        sft_record = {
            "messages": [
                {"role": "user", "content": problem},
                {"role": "assistant", "content": gen_text},
            ],
            "metadata": {
                "source_dataset": "openr1_math_220k",
                "openr1_uuid": row.get("uuid", ""),
                "openr1_source": row.get("source", ""),
                "problem_type": row.get("problem_type", ""),
                "gold_answer": gold,
                "gen_tokens": gen_tokens,
                "gen_index": gen_idx,
            },
        }
        out_f.write(json.dumps(sft_record) + "\n")
        n_written += 1

print(f"\n[{time.strftime('%H:%M:%S')}] === DONE ===")
print(f"  Attempted:               {n_attempted}")
print(f"  Dropped (no verified):   {n_no_verified}")
print(f"  Dropped (multi-part):    {n_multi_part}")
print(f"  Dropped (too short):     {n_too_short}")
print(f"  Dropped (too long):      {n_too_long}")
print(f"  Dropped (no boxed):      {n_no_boxed}")
print(f"  Dropped (answer wrong):  {n_answer_mismatch}")
print(f"  Written:                 {n_written}")
print(f"  Output:                  {args.output}")

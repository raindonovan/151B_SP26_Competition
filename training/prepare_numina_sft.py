"""
Prepare NuminaMath-1.5 SFT training data.
Filters: answer != 'proof', validity flags Yes, synthetic == False, 
         source NOT in {cn_k12} (drops 60% Chinese K-12 below competition difficulty),
         solution length 200-2000 tokens.
Format: assistant content = NuminaMath solution + '\n\nThe answer is \\boxed{<gold>}.'
        (concise-solution arm; we wrap with explicit boxed answer for SFT consistency)
"""
import argparse
import json
import re
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--target-rows", type=int, default=1000)
parser.add_argument("--output", type=str, default="data/sft/numina_concise_v1_1k.jsonl")
parser.add_argument("--min-tokens", type=int, default=200)
parser.add_argument("--max-tokens", type=int, default=2000)
parser.add_argument("--seed", type=int, default=42)
args = parser.parse_args()

from datasets import load_dataset
from transformers import AutoTokenizer

print(f"[{time.strftime('%H:%M:%S')}] Loading tokenizer + NuminaMath-1.5...")
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-4B-Thinking-2507")
ds = load_dataset("AI-MO/NuminaMath-1.5", split="train")
print(f"[{time.strftime('%H:%M:%S')}] Loaded {len(ds)} rows")

KEEP_SOURCES = {"olympiads", "aops_forum", "cn_contest", "amc_aime",
                "olympiads_ref", "inequalities", "number_theory"}

def numina_keep(row):
    if row.get("answer") == "proof":
        return False
    if row.get("problem_is_valid") != "Yes":
        return False
    if row.get("solution_is_valid") != "Yes":
        return False
    if row.get("synthetic") is True:
        return False
    if row.get("source") not in KEEP_SOURCES:
        return False
    sol = row.get("solution")
    prob = row.get("problem")
    if sol is None or not sol.strip() or prob is None or not prob.strip():
        return False
    ans = row.get("answer")
    if ans is None or not str(ans).strip():
        return False
    return True

print(f"[{time.strftime('%H:%M:%S')}] Filtering NuminaMath...")
filtered = ds.filter(numina_keep)
print(f"[{time.strftime('%H:%M:%S')}] After filter: {len(filtered)} rows ({len(filtered)/len(ds)*100:.1f}% retained)")

print(f"[{time.strftime('%H:%M:%S')}] Tokenizing and length-filtering (target {args.target_rows} rows)...")
print(f"[{time.strftime('%H:%M:%S')}] Length filter: {args.min_tokens}-{args.max_tokens} tokens")

# Already has correctness from NuminaMath's curation; no R1-style verification needed
filtered_shuffled = filtered.shuffle(seed=args.seed)

n_attempted = 0
n_too_short = 0
n_too_long = 0
n_written = 0

out_dir = Path(args.output).parent
out_dir.mkdir(parents=True, exist_ok=True)

with open(args.output, "w") as out_f:
    for row in filtered_shuffled:
        if n_written >= args.target_rows:
            break
        n_attempted += 1
        if n_attempted % 1000 == 0:
            print(f"  [{time.strftime('%H:%M:%S')}] attempted {n_attempted}, written {n_written}...")

        sol = row["solution"]
        sol_tokens = len(tok(sol, add_special_tokens=False)["input_ids"])
        if sol_tokens < args.min_tokens:
            n_too_short += 1
            continue
        if sol_tokens > args.max_tokens:
            n_too_long += 1
            continue

        problem = row["problem"]
        gold = str(row["answer"]).strip()

        # Wrap NuminaMath solution with an explicit boxed answer at the end
        # to match SFT format expectation. NuminaMath solutions usually conclude
        # with the answer inline; we append a boxed wrapper for consistency.
        # If solution already contains \boxed{<gold>}, don't double-wrap.
        if f"\\boxed{{{gold}}}" not in sol and "\\boxed{" not in sol:
            assistant_content = f"{sol}\n\nThe answer is $\\boxed{{{gold}}}$."
        else:
            assistant_content = sol

        sft_record = {
            "messages": [
                {"role": "user", "content": problem},
                {"role": "assistant", "content": assistant_content},
            ],
            "metadata": {
                "source_dataset": "numina_math_1.5",
                "numina_source": row.get("source", ""),
                "problem_type": row.get("problem_type", ""),
                "gold_answer": gold,
                "sol_tokens": sol_tokens,
                "boxed_was_present": "\\boxed{" in sol,
            },
        }
        out_f.write(json.dumps(sft_record) + "\n")
        n_written += 1

print(f"\n[{time.strftime('%H:%M:%S')}] === DONE ===")
print(f"  Attempted:               {n_attempted}")
print(f"  Dropped (too short):     {n_too_short}")
print(f"  Dropped (too long):      {n_too_long}")
print(f"  Written:                 {n_written}")
print(f"  Output:                  {args.output}")

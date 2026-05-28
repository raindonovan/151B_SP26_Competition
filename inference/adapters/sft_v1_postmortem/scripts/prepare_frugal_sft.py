"""
Generate SFT traces by running Frugal-Thinking-4B inference on filtered NuminaMath problems.
Filters traces by correctness (sympy-verified against gold) and writes Qwen3-Thinking
chat-format JSONL for downstream SFT training.

Usage:
    .venv/bin/python training/prepare_frugal_sft.py \\
        --target-rows 1000 \\
        --sample-budget 1500 \\
        --output data/sft/frugal_traces_v1_1k.jsonl
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

# --- Args ---
parser = argparse.ArgumentParser()
parser.add_argument("--target-rows", type=int, default=1000,
                    help="Stop generation when this many valid traces are written.")
parser.add_argument("--sample-budget", type=int, default=1500,
                    help="Maximum NuminaMath problems to attempt (cap on inference cost).")
parser.add_argument("--output", type=str, default="data/sft/frugal_traces_v1_1k.jsonl")
parser.add_argument("--raw-output", type=str, default="data/sft/frugal_traces_v1_1k.raw.jsonl",
                    help="Raw Frugal generations + correctness flags (pre-filter).")
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--max-tokens", type=int, default=16384)
parser.add_argument("--frugal-model", type=str, default="MBZUAI-Paris/Frugal-Thinking-4B")
args = parser.parse_args()

# --- NuminaMath load + filter (matches DESIGN.md §7 spec) ---
from datasets import load_dataset

print(f"[{time.strftime('%H:%M:%S')}] Loading NuminaMath-1.5...")
ds = load_dataset("AI-MO/NuminaMath-1.5", split="train")
print(f"[{time.strftime('%H:%M:%S')}] Loaded {len(ds)} rows total.")

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

# Shuffle and take sample budget
print(f"[{time.strftime('%H:%M:%S')}] Sampling {args.sample_budget} problems with seed={args.seed}...")
sampled = filtered.shuffle(seed=args.seed).select(range(min(args.sample_budget, len(filtered))))

# --- Load Frugal via vLLM ---
print(f"[{time.strftime('%H:%M:%S')}] Loading Frugal-Thinking-4B via vLLM (BF16, ~5min first time)...")
from vllm import LLM, SamplingParams

llm = LLM(
    model=args.frugal_model,
    dtype="bfloat16",
    max_model_len=20480,        # 16k generation + ~500 prompt + headroom
    gpu_memory_utilization=0.85, # leave room
    enforce_eager=False,
)
tokenizer = llm.get_tokenizer()

sampling_params = SamplingParams(
    temperature=0.6,
    top_p=0.95,
    top_k=20,
    min_p=0.0,
    max_tokens=args.max_tokens,
    seed=args.seed,
)

# --- Build prompts ---
# Use Frugal's chat template (same as Qwen3-Thinking-2507 base)
print(f"[{time.strftime('%H:%M:%S')}] Building chat-formatted prompts...")
prompts = []
for row in sampled:
    messages = [{"role": "user", "content": row["problem"]}]
    prompt_text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    prompts.append(prompt_text)

print(f"[{time.strftime('%H:%M:%S')}] First prompt sample (truncated):")
print(prompts[0][:300] + "...")

# --- Generate ---
# vLLM batch-generates; submit all and let it parallelize internally
print(f"[{time.strftime('%H:%M:%S')}] Starting Frugal inference on {len(prompts)} problems...")
t_start = time.time()
outputs = llm.generate(prompts, sampling_params)
t_gen = time.time() - t_start
print(f"[{time.strftime('%H:%M:%S')}] Generation complete: {t_gen/60:.1f} min wall time")

# --- Extract + verify ---
BOXED_RE = re.compile(r"\\boxed\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}")

def extract_last_boxed(text):
    matches = BOXED_RE.findall(text)
    if not matches:
        return None
    return matches[-1].strip()

def normalize_for_match(s):
    if s is None:
        return ""
    s = str(s).strip()
    s = s.replace(" ", "").replace("\\!", "").replace("\\,", "")
    s = s.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    s = s.replace("\\left", "").replace("\\right", "")
    s = re.sub(r"\\text\{[^}]*\}", "", s)
    return s

def verify_correct(extracted, gold):
    if extracted is None or gold is None:
        return False
    e_norm = normalize_for_match(extracted)
    g_norm = normalize_for_match(gold)
    if e_norm == g_norm:
        return True
    # Sympy fallback via math_verify (already a dep for SFT eval)
    try:
        from math_verify import parse, verify
        e_parsed = parse(f"\\boxed{{{extracted}}}")
        g_parsed = parse(f"\\boxed{{{gold}}}")
        return bool(verify(g_parsed, e_parsed))
    except Exception:
        return False

# --- Process outputs ---
print(f"[{time.strftime('%H:%M:%S')}] Processing outputs and filtering for correctness...")

raw_dir = Path(args.raw_output).parent
raw_dir.mkdir(parents=True, exist_ok=True)
out_dir = Path(args.output).parent
out_dir.mkdir(parents=True, exist_ok=True)

n_raw = 0
n_extracted = 0
n_correct = 0
n_written = 0

with open(args.raw_output, "w") as raw_f, open(args.output, "w") as out_f:
    for row, output in zip(sampled, outputs):
        gen_text = output.outputs[0].text
        gen_tokens = len(output.outputs[0].token_ids)
        prob = row["problem"]
        gold = row["answer"]
        source = row.get("source", "unknown")

        extracted = extract_last_boxed(gen_text)
        is_correct = verify_correct(extracted, gold)
        n_raw += 1
        if extracted is not None:
            n_extracted += 1
        if is_correct:
            n_correct += 1

        raw_record = {
            "problem": prob,
            "gold_answer": gold,
            "source": source,
            "frugal_output": gen_text,
            "extracted_answer": extracted,
            "correct": is_correct,
            "gen_tokens": gen_tokens,
        }
        raw_f.write(json.dumps(raw_record) + "\n")

        if is_correct and n_written < args.target_rows:
            sft_record = {
                "messages": [
                    {"role": "user", "content": prob},
                    {"role": "assistant", "content": gen_text},
                ],
                "metadata": {
                    "source_dataset": "frugal_traces_v1",
                    "numina_source": source,
                    "gold_answer": gold,
                    "gen_tokens": gen_tokens,
                },
            }
            out_f.write(json.dumps(sft_record) + "\n")
            n_written += 1

print(f"\n[{time.strftime('%H:%M:%S')}] === DONE ===")
print(f"  Total problems attempted: {n_raw}")
print(f"  Extracted boxed answer:   {n_extracted} ({n_extracted/n_raw*100:.1f}%)")
print(f"  Correct (sympy-verified): {n_correct} ({n_correct/n_raw*100:.1f}%)")
print(f"  Written to SFT JSONL:     {n_written}")
print(f"  Generation wall time:     {t_gen/60:.1f} min")
print(f"  Raw outputs:              {args.raw_output}")
print(f"  SFT JSONL:                {args.output}")

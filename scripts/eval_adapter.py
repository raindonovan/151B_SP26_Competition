"""
Eval a merged adapter checkpoint against a JSONL slice.

Loads merged BF16 model via vLLM, runs N=1 inference with Qwen3-Thinking sampling defaults,
scores each item with both Judger and math_verify, logs Tier 1 metrics.

Usage:
    .venv/bin/python scripts/eval_adapter.py \\
        --model training/checkpoints/openr1_v1_1k/merged \\
        --slice data/slices/fixed_200_v1.jsonl \\
        --output results/eval_openr1_v1_1k_fixed_200.jsonl \\
        --summary results/eval_openr1_v1_1k_fixed_200.summary.json \\
        --label openr1_v1_1k

For baseline (untrained Qwen3 base) comparison:
    --model Qwen/Qwen3-4B-Thinking-2507  --label baseline_v1
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, required=True,
                    help="Path to merged model OR HF model ID for baseline")
parser.add_argument("--slice", type=str, default="data/slices/fixed_200_v1.jsonl")
parser.add_argument("--output", type=str, required=True,
                    help="Per-item JSONL output")
parser.add_argument("--summary", type=str, required=True,
                    help="Per-run aggregate summary JSON")
parser.add_argument("--label", type=str, required=True,
                    help="Run identifier")
parser.add_argument("--max-tokens", type=int, default=16384)
parser.add_argument("--temperature", type=float, default=0.6)
parser.add_argument("--top-p", type=float, default=0.95)
parser.add_argument("--top-k", type=int, default=20)
parser.add_argument("--seed", type=int, default=42)
args = parser.parse_args()

print(f"[{time.strftime('%H:%M:%S')}] === EVAL_ADAPTER ===")
print(f"  Label:    {args.label}")
print(f"  Model:    {args.model}")
print(f"  Slice:    {args.slice}")
print(f"  Output:   {args.output}")
print(f"  Summary:  {args.summary}")
print()

# --- Load slice ---
print(f"[{time.strftime('%H:%M:%S')}] Loading slice...")
with open(args.slice) as f:
    items = [json.loads(l) for l in f]
print(f"  {len(items)} items")

# --- Load Judger ---
print(f"[{time.strftime('%H:%M:%S')}] Loading judger.py...")
sys.path.insert(0, "/workspace/151B_SP26_Competition")
from judger import Judger
judger = Judger()

# --- Load math_verify ---
from math_verify import parse, verify

# --- Load model via vLLM ---
print(f"[{time.strftime('%H:%M:%S')}] Loading model {args.model} via vLLM...")
from vllm import LLM, SamplingParams

llm = LLM(
    model=args.model,
    dtype="bfloat16",
    max_model_len=20480,
    gpu_memory_utilization=0.85,
    enforce_eager=False,
)
tokenizer = llm.get_tokenizer()

sampling = SamplingParams(
    temperature=args.temperature,
    top_p=args.top_p,
    top_k=args.top_k,
    min_p=0.0,
    max_tokens=args.max_tokens,
    seed=args.seed,
)

# --- Build prompts (matches scripts/run_vllm_experiment.py format) ---
SYSTEM_PROMPT = (
    "You are an expert mathematician. Solve the problem step-by-step. "
    "Put your final answer inside \\boxed{}. If the problem has multiple sub-answers, "
    "separate them by commas inside a single \\boxed{}, e.g. \\boxed{3, 7}. "
    "Give numerical answers to at least 4 significant figures, "
    "unless the problem specifies a different precision."
)

def build_user_content(item):
    user = item["question"]
    if item.get("is_mcq"):
        opts = item.get("options", [])
        opt_text = "\n".join([f"{chr(65+i)}. {o}" for i, o in enumerate(opts)])
        user = f"{user}\n\nOptions:\n{opt_text}"
    return user

prompts = []
for item in items:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_content(item)},
    ]
    prompt_text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    prompts.append(prompt_text)

print(f"[{time.strftime('%H:%M:%S')}] First prompt sample (truncated):")
print(prompts[0][:300])
print("...")

# --- Generate ---
print(f"[{time.strftime('%H:%M:%S')}] Generating {len(prompts)} responses...")
t_start = time.time()
outputs = llm.generate(prompts, sampling)
t_gen = time.time() - t_start
print(f"[{time.strftime('%H:%M:%S')}] Generation complete in {t_gen/60:.1f} min")

# --- Score each item ---
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

def extract_last_boxed(text):
    matches = BOXED_RE.findall(text)
    if not matches:
        return None
    return matches[-1].strip()

def kaggle_approx_correct(extracted, gold):
    if extracted is None or gold is None:
        return False
    if normalize_for_match(extracted) == normalize_for_match(gold):
        return True
    try:
        e_parsed = parse(f"\\boxed{{{extracted}}}")
        g_parsed = parse(f"\\boxed{{{gold}}}")
        return bool(verify(g_parsed, e_parsed))
    except Exception:
        return False

print(f"[{time.strftime('%H:%M:%S')}] Scoring items...")

results = []
for item, output in zip(items, outputs):
    gen_text = output.outputs[0].text
    gen_tokens = len(output.outputs[0].token_ids)
    hit_token_cap = gen_tokens >= args.max_tokens

    extracted = extract_last_boxed(gen_text)
    gold = item.get("gold")  # may be empty string for private set

    # Judger correctness
    correct_judger = bool(judger.is_correct(gen_text, item)) if gold else False

    # Kaggle approx correctness
    correct_kaggle = kaggle_approx_correct(extracted, gold) if gold else False

    sympy_disagreement = (correct_judger != correct_kaggle) if gold else False

    # <think> structure
    has_think_open = "<think>" in gen_text
    has_think_close = "</think>" in gen_text
    if has_think_open and has_think_close:
        think_block = gen_text.split("<think>", 1)[1].split("</think>", 1)[0]
        post_think = gen_text.split("</think>", 1)[1] if has_think_close else ""
        think_tokens = len(tokenizer(think_block, add_special_tokens=False)["input_ids"])
        post_think_tokens = len(tokenizer(post_think, add_special_tokens=False)["input_ids"])
    else:
        think_tokens = 0
        post_think_tokens = gen_tokens

    # boxed_at_end: is the last \boxed{} within last 100 tokens?
    if extracted is not None:
        last_boxed_pos = gen_text.rfind("\\boxed{")
        chars_after = len(gen_text) - last_boxed_pos
        # rough heuristic: 100 tokens ≈ 400 chars
        boxed_at_end = chars_after < 400
    else:
        boxed_at_end = False

    record = {
        "id": item.get("id"),
        "is_mcq": item.get("is_mcq", False),
        "gen_tokens": gen_tokens,
        "hit_token_cap": hit_token_cap,
        "extracted_answer": extracted,
        "gold": gold,
        "correct_judger": correct_judger,
        "correct_kaggle_approx": correct_kaggle,
        "sympy_disagreement": sympy_disagreement,
        "has_think_open": has_think_open,
        "has_think_close": has_think_close,
        "think_tokens": think_tokens,
        "post_think_tokens": post_think_tokens,
        "boxed_at_end": boxed_at_end,
        "response": gen_text,
    }
    results.append(record)

# --- Write per-item JSONL ---
out_dir = Path(args.output).parent
out_dir.mkdir(parents=True, exist_ok=True)
with open(args.output, "w") as f:
    for r in results:
        f.write(json.dumps(r) + "\n")
print(f"[{time.strftime('%H:%M:%S')}] Per-item results: {args.output}")

# --- Aggregate summary ---
import numpy as np

n = len(results)
n_with_gold = sum(1 for r in results if r["gold"])
correct_judger_count = sum(1 for r in results if r["correct_judger"])
correct_kaggle_count = sum(1 for r in results if r["correct_kaggle_approx"])
disagreement_count = sum(1 for r in results if r["sympy_disagreement"])

malformed_think = sum(1 for r in results if r["has_think_open"] != r["has_think_close"])
boxed_rate = sum(1 for r in results if r["extracted_answer"] is not None) / n
hit_cap = sum(1 for r in results if r["hit_token_cap"])

gen_tokens = np.array([r["gen_tokens"] for r in results])

# Length-by-correctness buckets
correct_tokens = np.array([r["gen_tokens"] for r in results if r["correct_judger"]])
wrong_tokens = np.array([r["gen_tokens"] for r in results if not r["correct_judger"]])

summary = {
    "label": args.label,
    "model": args.model,
    "slice": args.slice,
    "n_items": n,
    "n_with_gold": n_with_gold,
    "generation_minutes": round(t_gen / 60, 2),
    # Accuracy
    "correct_judger_count": correct_judger_count,
    "correct_judger_rate": correct_judger_count / max(n_with_gold, 1),
    "correct_kaggle_approx_count": correct_kaggle_count,
    "correct_kaggle_approx_rate": correct_kaggle_count / max(n_with_gold, 1),
    "judger_kaggle_approx_agreement_rate": (n - disagreement_count) / max(n, 1),
    "sympy_disagreement_count": disagreement_count,
    # Format compliance
    "boxed_rate": boxed_rate,
    "malformed_think_count": malformed_think,
    "malformed_think_rate": malformed_think / n,
    # Length statistics
    "avg_gen_tokens": float(gen_tokens.mean()),
    "median_gen_tokens": float(np.median(gen_tokens)),
    "p25_gen_tokens": float(np.percentile(gen_tokens, 25)),
    "p75_gen_tokens": float(np.percentile(gen_tokens, 75)),
    "p95_gen_tokens": float(np.percentile(gen_tokens, 95)),
    # Cutoff
    "cutoff_count": hit_cap,
    "cutoff_rate": hit_cap / n,
    # Length-by-correctness
    "avg_tokens_correct": float(correct_tokens.mean()) if len(correct_tokens) else None,
    "avg_tokens_wrong": float(wrong_tokens.mean()) if len(wrong_tokens) else None,
}

with open(args.summary, "w") as f:
    json.dump(summary, f, indent=2)

print(f"\n[{time.strftime('%H:%M:%S')}] === SUMMARY ===")
print(f"  Label:                    {args.label}")
print(f"  Items with gold:          {n_with_gold}/{n}")
print(f"  correct_judger_rate:      {summary['correct_judger_rate']:.3f}")
print(f"  correct_kaggle_rate:      {summary['correct_kaggle_approx_rate']:.3f}")
print(f"  agreement_rate:           {summary['judger_kaggle_approx_agreement_rate']:.3f}")
print(f"  boxed_rate:               {summary['boxed_rate']:.3f}")
print(f"  malformed_think_rate:     {summary['malformed_think_rate']:.3f}")
print(f"  avg_gen_tokens:           {summary['avg_gen_tokens']:.0f}")
print(f"  median_gen_tokens:        {summary['median_gen_tokens']:.0f}")
print(f"  cutoff_rate:              {summary['cutoff_rate']:.3f}")
print(f"  avg_tokens_correct:       {summary['avg_tokens_correct']}")
print(f"  avg_tokens_wrong:         {summary['avg_tokens_wrong']}")
print(f"  Summary saved: {args.summary}")

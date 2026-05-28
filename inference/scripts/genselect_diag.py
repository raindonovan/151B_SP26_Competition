"""Diagnostic: measure endpoint speed at different (workers, max_tokens) combos.

Runs N calls on a single Tier-5 item under each config and reports avg time.
Helps decide if today's slowdown is due to concurrency contention,
KV-cache pre-allocation on max_tokens, or general endpoint degradation.
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI

API_BASE = "https://tritonai-api.ucsd.edu/v1"
API_KEY  = os.environ.get("TRITONAI_API_KEY", "")  # was hardcoded; rotated 2026-05-28
MODEL    = "api-test-qwen-3-4b"

SYS_FREE = (
    "You are an expert mathematician. Solve the problem step-by-step. "
    "Put your final answer inside \\boxed{}. "
    "If the problem has multiple sub-answers, separate them by commas inside a single \\boxed{}, "
    "e.g. \\boxed{3, 7}. "
    "Give numerical answers to at least 4 significant figures, unless the problem specifies a different precision."
)

# Load 1 Tier-5 item from private.jsonl (item 51 was being processed when slow)
print("Loading test item...")
with open("private.jsonl") as f:
    items = {int(json.loads(l)["id"]): json.loads(l) for l in f}
item = items[51]  # known Tier-4 hard item
user = item["question"]
print(f"  item_id=51, question len={len(user)} chars\n")

client = OpenAI(base_url=API_BASE, api_key=API_KEY)

def one_call(idx, max_tokens):
    t0 = time.time()
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYS_FREE},
                {"role": "user",   "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.6,
            top_p=0.95,
        )
        elapsed = time.time() - t0
        tok = r.usage.completion_tokens if r.usage else 0
        print(f"  [{idx}] {elapsed:6.1f}s  {tok:5d}tok", flush=True)
        return elapsed, tok, None
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  [{idx}] {elapsed:6.1f}s  ERR: {str(e)[:80]}", flush=True)
        return elapsed, 0, str(e)

def run_config(workers, max_tokens, n_calls):
    print(f"=== workers={workers}, max_tokens={max_tokens}, n_calls={n_calls} ===")
    t0 = time.time()
    if workers == 1:
        results = [one_call(i, max_tokens) for i in range(n_calls)]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda i: one_call(i, max_tokens), range(n_calls)))
    wall = time.time() - t0
    ok = [r for r in results if r[2] is None]
    if ok:
        avg = sum(r[0] for r in ok) / len(ok)
        avg_tok = sum(r[1] for r in ok) / len(ok)
        print(f"  WALL={wall:.0f}s  ok={len(ok)}/{n_calls}  avg_call={avg:.0f}s  avg_tok={avg_tok:.0f}  thrput={len(ok)/wall*60:.2f}/min")
    print()
    return wall, ok

# Run configs in sequence
print("Test 1: serial baseline (workers=1, max_tokens=32768, n=3)")
run_config(1, 32768, 3)

print("Test 2: 60K tokens serial (workers=1, max_tokens=60000, n=3)")
run_config(1, 60000, 3)

print("Test 3: 4-way concurrent at 32K (workers=4, max_tokens=32768, n=4)")
run_config(4, 32768, 4)

print("Test 4: 4-way concurrent at 60K (workers=4, max_tokens=60000, n=4)")
run_config(4, 60000, 4)

print("Test 5: 4-way concurrent at 16K (workers=4, max_tokens=16384, n=4)")
run_config(4, 16384, 4)

print("Done.")

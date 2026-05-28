"""
Build a 200-question stratified sample from data/private.jsonl for SFT eval ranking.

Strategy: simple random sample with fixed seed 42 (no stratification by topic/difficulty
since private.jsonl doesn't have those labels). Could be upgraded later if we add
topic/difficulty labels via LLM augmentation.

Output: data/slices/fixed_200_v1.jsonl (200 rows, same schema as private.jsonl)
"""
import json
import random
from pathlib import Path

INPUT = "data/private.jsonl"
OUTPUT = "data/slices/fixed_200_v1.jsonl"
N_TARGET = 200
SEED = 42

print(f"Reading {INPUT}...")
with open(INPUT) as f:
    rows = [json.loads(l) for l in f]
print(f"Total rows: {len(rows)}")

random.seed(SEED)
sampled = random.sample(rows, N_TARGET)
print(f"Sampled {len(sampled)} rows with seed={SEED}")

# Distribution check
mcq_count = sum(1 for r in sampled if r.get("is_mcq"))
print(f"  MCQ: {mcq_count} ({mcq_count/N_TARGET*100:.1f}%)")
print(f"  Free-response: {N_TARGET - mcq_count}")

out_path = Path(OUTPUT)
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, "w") as f:
    for r in sampled:
        f.write(json.dumps(r) + "\n")
print(f"Wrote {OUTPUT}")

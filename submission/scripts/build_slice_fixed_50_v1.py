"""Build a fixed, reproducible 50-question slice for the prompt sweep.

Stratifies 17 MCQ + 33 free-form from data/public.jsonl with two seeded
RNG instances (one per pool) and writes data/slices/fixed_50_v1.json.
Refuses to overwrite an existing slice file — slices are immutable per
experiments.md rules.

Two RNGs (not one shared instance) so the per-pool draws are independent
of each other's order: swapping or inserting an rng consumer between them
cannot silently change either pool's selection.

Usage:
    python scripts/build_slice_fixed_50_v1.py
"""

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "data" / "public.jsonl"
OUTPUT_PATH = REPO_ROOT / "data" / "slices" / "fixed_50_v1.json"

SLICE_ID = "fixed_50_v1"
# Convention: MCQ pool uses SEED, free-form pool uses SEED + 1.
SEED = 42
MCQ_SEED = SEED
FREE_SEED = SEED + 1
N_MCQ = 17
N_FREE = 33
EXPECTED_MIN_MCQ = 375
EXPECTED_MIN_FREE = 751


def is_mcq(row: dict) -> bool:
    return isinstance(row.get("options"), list) and len(row["options"]) > 0


def main() -> int:
    if OUTPUT_PATH.exists():
        sys.stderr.write(
            f"ERROR: {OUTPUT_PATH} already exists. Slices are immutable.\n"
            "Delete it manually if you intend to regenerate (and document why).\n"
        )
        return 1

    if not DATA_PATH.exists():
        sys.stderr.write(f"ERROR: dataset not found at {DATA_PATH}\n")
        return 1

    with open(DATA_PATH) as f:
        rows = [json.loads(line) for line in f if line.strip()]

    mcq_ids = [r["id"] for r in rows if is_mcq(r)]
    free_ids = [r["id"] for r in rows if not is_mcq(r)]

    if len(mcq_ids) < EXPECTED_MIN_MCQ:
        sys.stderr.write(
            f"ERROR: expected >= {EXPECTED_MIN_MCQ} MCQ rows, found {len(mcq_ids)}.\n"
            "Dataset may be wrong or filtered. Aborting.\n"
        )
        return 1
    if len(free_ids) < EXPECTED_MIN_FREE:
        sys.stderr.write(
            f"ERROR: expected >= {EXPECTED_MIN_FREE} free-form rows, found {len(free_ids)}.\n"
            "Dataset may be wrong or filtered. Aborting.\n"
        )
        return 1

    mcq_rng = random.Random(MCQ_SEED)
    free_rng = random.Random(FREE_SEED)
    sampled_mcq = mcq_rng.sample(mcq_ids, N_MCQ)
    sampled_free = free_rng.sample(free_ids, N_FREE)
    sampled = sorted(sampled_mcq + sampled_free)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slice_id": SLICE_ID,
        "seed": SEED,
        "n_mcq": N_MCQ,
        "n_free": N_FREE,
        "ids": sampled,
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

    print(f"Wrote {OUTPUT_PATH}")
    print(f"  slice_id : {SLICE_ID}")
    print(f"  seed     : {SEED}  (MCQ uses seed, free uses seed+1)")
    print(f"  total    : {len(sampled)}  (mcq={N_MCQ}, free={N_FREE})")
    print(f"  pool     : {len(mcq_ids)} MCQ / {len(free_ids)} free in dataset")
    print(f"  first 5  : {sampled[:5]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

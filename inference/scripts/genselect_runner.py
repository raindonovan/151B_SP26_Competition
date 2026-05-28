"""GenSelect SC runner against TritonAI API.

Features:
- Incremental JSONL saves (one line per call, append mode)
- Resume: skips already-completed (item_id, sc_index) pairs
- Concurrent workers (--workers, default 4)
- Live progress: calls/min, ETA, per-call timing

Usage:
  python scripts/genselect_runner.py --tiers 4 5 --workers 4
  python scripts/genselect_runner.py --tiers 4 5 --workers 1   # serial
  python scripts/genselect_runner.py --item-ids 4 28 40         # specific items
"""

import argparse
import csv
import json
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE  = "https://tritonai-api.ucsd.edu/v1"
API_KEY   = os.environ.get("TRITONAI_API_KEY", "")  # was hardcoded; rotated 2026-05-28
MODEL     = "api-test-qwen-3-4b"
N_SAMPLES = 16
MAX_TOKENS = 32768
TEMPERATURE = 0.6
TOP_P = 0.95
OUTPUT_FILE = "results/genselect_runner.jsonl"

# v1-baseline prompts (verbatim from scripts/prompts.py)
SYS_MCQ = (
    "You are an expert mathematician. "
    "Read the problem and the answer choices below, then select the single best answer. "
    "Output ONLY the letter of your chosen option inside \\boxed{}, e.g. \\boxed{C}."
)
SYS_FREE = (
    "You are an expert mathematician. Solve the problem step-by-step. "
    "Put your final answer inside \\boxed{}. "
    "If the problem has multiple sub-answers, separate them by commas inside a single \\boxed{}, "
    "e.g. \\boxed{3, 7}. "
    "Give numerical answers to at least 4 significant figures, unless the problem specifies a different precision."
)

# ── Thread-safe write lock ────────────────────────────────────────────────────
_write_lock = threading.Lock()
_progress_lock = threading.Lock()
_completed = 0
_failed = 0
_timings = []
_start_time = None
_total_calls = 0

def write_result(result: dict):
    with _write_lock:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

def update_progress(elapsed: float, success: bool, item_id, sc_index, comp_tokens):
    global _completed, _failed
    with _progress_lock:
        if success:
            _completed += 1
            _timings.append(elapsed)
        else:
            _failed += 1

        done = _completed + _failed
        pct = 100 * done / _total_calls
        avg = sum(_timings) / len(_timings) if _timings else 0
        calls_per_min = 60 / avg if avg > 0 else 0
        remaining = _total_calls - done
        eta_h = (remaining * avg) / 3600 if avg > 0 else 0
        wall = time.time() - _start_time
        status = "OK" if success else "ERR"
        print(
            f"[{done:>4}/{_total_calls}] {pct:5.1f}%  "
            f"item={item_id} sc={sc_index:02d}  "
            f"{elapsed:5.1f}s  {comp_tokens:5d}tok  "
            f"avg={avg:.0f}s  {calls_per_min:.2f}calls/min  "
            f"ETA={eta_h:.1f}h  wall={wall/3600:.2f}h  [{status}]",
            flush=True
        )

# ── Single API call ───────────────────────────────────────────────────────────
def run_one(client, item_id, sc_index, system, user):
    t0 = time.time()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        elapsed = time.time() - t0
        content = response.choices[0].message.content or ""
        reasoning = ""
        psf = getattr(response.choices[0].message, "provider_specific_fields", None)
        if psf:
            reasoning = psf.get("reasoning_content", "")
        usage = response.usage
        comp_tokens = usage.completion_tokens if usage else 0
        prompt_tokens = usage.prompt_tokens if usage else 0

        result = {
            "item_id": item_id,
            "sc_index": sc_index,
            "content": content,
            "reasoning_content": reasoning,
            "completion_tokens": comp_tokens,
            "prompt_tokens": prompt_tokens,
            "elapsed_sec": round(elapsed, 2),
            "error": None,
        }
        write_result(result)
        update_progress(elapsed, True, item_id, sc_index, comp_tokens)
        return result

    except Exception as e:
        elapsed = time.time() - t0
        result = {
            "item_id": item_id,
            "sc_index": sc_index,
            "content": "",
            "reasoning_content": "",
            "completion_tokens": 0,
            "prompt_tokens": 0,
            "elapsed_sec": round(elapsed, 2),
            "error": str(e),
        }
        write_result(result)
        update_progress(elapsed, False, item_id, sc_index, 0)
        return result

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global _start_time, _total_calls

    parser = argparse.ArgumentParser()
    parser.add_argument("--tiers", nargs="+", type=int, default=[4, 5],
                        help="Tiers to include (default: 4 5)")
    parser.add_argument("--item-ids", nargs="+", type=int, default=None,
                        help="Override: run specific item IDs only")
    parser.add_argument("--workers", type=int, default=4,
                        help="Concurrent API workers (default: 4)")
    parser.add_argument("--n-samples", type=int, default=N_SAMPLES,
                        help=f"SC samples per item (default: {N_SAMPLES})")
    parser.add_argument("--output", default=OUTPUT_FILE,
                        help=f"Output JSONL file (default: {OUTPUT_FILE})")
    args = parser.parse_args()

    output_file = args.output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Load private items
    print("Loading private.jsonl...")
    items = {}
    with open("private.jsonl") as f:
        for line in f:
            item = json.loads(line)
            items[int(item["id"])] = item
    print(f"  {len(items)} items")

    # Load answer sheet
    print("Loading unified_answer_sheet.csv...")
    tier_map = {}
    with open("results/unified_answer_sheet.csv") as f:
        for row in csv.DictReader(f):
            tier_map[int(row["item_id"])] = int(row["tier"])

    # Determine target item IDs
    if args.item_ids:
        target_ids = args.item_ids
        print(f"  Mode: specific items {target_ids}")
    else:
        target_ids = sorted(iid for iid, t in tier_map.items() if t in args.tiers)
        print(f"  Mode: tiers {args.tiers} → {len(target_ids)} items")

    # Load already-completed (item_id, sc_index) from output file
    done_set = set()
    if os.path.exists(output_file):
        with open(output_file, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    if r.get("error") is None:  # only count successful calls
                        done_set.add((int(r["item_id"]), int(r["sc_index"])))
                except Exception:
                    pass
        print(f"  Resuming: {len(done_set)} calls already done, skipping them")

    # Build work queue
    work = []
    for iid in target_ids:
        for sc in range(args.n_samples):
            if (iid, sc) not in done_set:
                work.append((iid, sc))

    _total_calls = len(work)
    total_expected = len(target_ids) * args.n_samples
    print(f"\n  Target:    {len(target_ids)} items × {args.n_samples} samples = {total_expected} calls")
    print(f"  Skipping:  {len(done_set)} already done")
    print(f"  To run:    {_total_calls} calls")
    print(f"  Workers:   {args.workers}")
    pilot_avg = 107.0  # seconds from throughput pilot
    eta_h = _total_calls * pilot_avg / args.workers / 3600
    print(f"  ETA (est): {eta_h:.1f}h at {pilot_avg:.0f}s/call × {args.workers} workers")
    print(f"  Output:    {output_file}")
    print()

    if _total_calls == 0:
        print("Nothing to do — all calls already completed.")
        return

    client = OpenAI(base_url=API_BASE, api_key=API_KEY)
    _start_time = time.time()

    def make_task(iid, sc):
        item = items[iid]
        is_mcq = bool(item.get("options"))
        if is_mcq:
            system = SYS_MCQ
            opts_text = "\n".join(item["options"])
            user = f"{item['question']}\n\nOptions:\n{opts_text}"
        else:
            system = SYS_FREE
            user = item["question"]
        return iid, sc, system, user

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(run_one, client, iid, sc, sys_p, usr_p): (iid, sc)
            for iid, sc, sys_p, usr_p in (make_task(iid, sc) for iid, sc in work)
        }
        for _ in as_completed(futures):
            pass  # progress printed inside run_one

    wall = time.time() - _start_time
    valid = [t for t in _timings if t > 0]
    print(f"\n{'='*70}")
    print(f"DONE")
    print(f"  Completed: {_completed}/{_total_calls}")
    print(f"  Failed:    {_failed}")
    print(f"  Wall time: {wall/3600:.2f}h")
    if valid:
        print(f"  Avg call:  {sum(valid)/len(valid):.1f}s")
    print(f"  Output:    {output_file}")

if __name__ == "__main__":
    main()

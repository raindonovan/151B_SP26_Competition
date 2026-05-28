"""GenSelect Phase 2: LLM-as-selector over SC=16 samples.

For each item:
  - Load all 16 generated solutions from genselect_runner.jsonl
  - Run 8 permutations of randomized solution ordering
  - Each permutation: ask the model to select the best solution
  - Aggregate via majority vote across permutations

Gate: requires results/genselect_runner.jsonl to have 4032 successful lines
      (252 items × 16 samples). Use --force to skip gate check.

Usage:
  python scripts/genselect_phase2.py                  # full run
  python scripts/genselect_phase2.py --smoke          # 1 item, 1 perm (smoke test)
  python scripts/genselect_phase2.py --item-ids 2 49  # specific items
  python scripts/genselect_phase2.py --force          # skip gate check
"""

import argparse
import csv
import json
import os
import random
import re
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE    = "https://tritonai-api.ucsd.edu/v1"
API_KEY     = os.environ.get("TRITONAI_API_KEY", "")  # was hardcoded; rotated 2026-05-28
MODEL       = "api-test-qwen-3-4b"
N_PERMS     = 8
MAX_TOKENS  = 2048
TEMPERATURE = 0.1   # low temp for selection (deterministic-ish)
TOP_P       = 0.95

GEN_FILE    = "results/genselect_runner.jsonl"
SEL_FILE    = "results/genselect_phase2_selections.jsonl"
FINAL_FILE  = "results/genselect_final_answers.csv"

EXPECTED_ITEMS   = 252
EXPECTED_SAMPLES = 16
EXPECTED_TOTAL   = EXPECTED_ITEMS * EXPECTED_SAMPLES  # 4032

# ── Prompts ───────────────────────────────────────────────────────────────────
SYS_SELECT = (
    "You are an expert mathematician and careful evaluator. "
    "You will be shown several solutions to a math problem. "
    "Your task is to select the single best solution — the one most likely to be correct. "
    "Output ONLY the solution number (e.g. '3') with no other text."
)

def make_select_prompt(question: str, summaries: list[tuple[int, str, str]]) -> str:
    """Build the selector user prompt.

    summaries: list of (display_number, answer, reasoning_snippet)
    """
    lines = [f"PROBLEM:\n{question}\n\nSOLUTIONS:"]
    for num, answer, reasoning in summaries:
        lines.append(
            f"\n--- Solution {num} ---\n"
            f"Answer: {answer}\n"
            f"Key reasoning:\n{reasoning}"
        )
    lines.append(
        "\nWhich solution number is most likely correct? "
        "Output ONLY the number."
    )
    return "\n".join(lines)

# ── Answer + reasoning extraction ────────────────────────────────────────────
def extract_summary(content: str) -> tuple[str, str]:
    """Extract (answer, reasoning_snippet) from a generated solution."""
    # Extract \boxed{} answer — take last match (final answer)
    matches = re.findall(r'\\boxed\{([^}]+)\}', content)
    answer = matches[-1].strip() if matches else "NO_ANSWER"

    # Reasoning: 400 chars immediately before the last \boxed{}
    boxed_pos = content.rfind('\\boxed')
    if boxed_pos > 0:
        window = content[max(0, boxed_pos - 500):boxed_pos]
        reasoning = window.strip()[-400:]
    else:
        reasoning = content[-400:].strip()

    return answer, reasoning

# ── Thread-safe write + progress ──────────────────────────────────────────────
_write_lock    = threading.Lock()
_progress_lock = threading.Lock()
_completed = 0
_failed    = 0
_timings   = []
_start_time = None
_total_calls = 0

def write_selection(result: dict):
    with _write_lock:
        with open(SEL_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

def update_progress(elapsed: float, success: bool, item_id, perm_idx):
    global _completed, _failed
    with _progress_lock:
        if success:
            _completed += 1
            _timings.append(elapsed)
        else:
            _failed += 1
        done = _completed + _failed
        pct  = 100 * done / _total_calls
        avg  = sum(_timings) / len(_timings) if _timings else 0
        eta_h = (_total_calls - done) * avg / 3600 if avg > 0 else 0
        wall  = time.time() - _start_time
        status = "OK" if success else "ERR"
        print(
            f"[{done:>4}/{_total_calls}] {pct:5.1f}%  "
            f"item={item_id} perm={perm_idx}  "
            f"{elapsed:5.1f}s  avg={avg:.0f}s  ETA={eta_h:.1f}h  "
            f"wall={wall/3600:.2f}h  [{status}]",
            flush=True,
        )

# ── Single selection call ─────────────────────────────────────────────────────
def run_selection(client, item_id, perm_idx, question, samples_for_item, rng):
    """Run one permutation selection call."""
    t0 = time.time()

    # Randomize order
    indices = list(range(len(samples_for_item)))
    rng.shuffle(indices)
    shuffled = [samples_for_item[i] for i in indices]

    # Build summaries with display numbers 1..N
    summaries = []
    for display_num, sample in enumerate(shuffled, start=1):
        answer, reasoning = extract_summary(sample["content"])
        summaries.append((display_num, answer, reasoning))

    user_prompt = make_select_prompt(question, summaries)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYS_SELECT},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        elapsed = time.time() - t0
        raw = response.choices[0].message.content or ""

        # Parse selected number
        m = re.search(r'\d+', raw.strip())
        selected_display = int(m.group()) if m else -1

        # Map display number back to original sc_index
        if 1 <= selected_display <= len(shuffled):
            selected_orig_idx = indices[selected_display - 1]
            selected_sample   = shuffled[selected_display - 1]
            selected_answer, _ = extract_summary(selected_sample["content"])
            selected_sc_index  = selected_sample["sc_index"]
        else:
            selected_orig_idx  = -1
            selected_answer    = "PARSE_ERROR"
            selected_sc_index  = -1

        result = {
            "item_id":         item_id,
            "permutation":     perm_idx,
            "solutions_order": [samples_for_item[i]["sc_index"] for i in indices],
            "selected_index":  selected_sc_index,
            "selected_answer": selected_answer,
            "raw_response":    raw,
            "elapsed_sec":     round(elapsed, 2),
            "error":           None,
        }
        write_selection(result)
        update_progress(elapsed, True, item_id, perm_idx)
        return result

    except Exception as e:
        elapsed = time.time() - t0
        result = {
            "item_id":         item_id,
            "permutation":     perm_idx,
            "solutions_order": [],
            "selected_index":  -1,
            "selected_answer": "",
            "raw_response":    "",
            "elapsed_sec":     round(elapsed, 2),
            "error":           str(e),
        }
        write_selection(result)
        update_progress(elapsed, False, item_id, perm_idx)
        return result

# ── Aggregation ───────────────────────────────────────────────────────────────
def aggregate_selections():
    """Majority-vote across permutations per item → final CSV."""
    votes = defaultdict(list)  # item_id → [answer, ...]
    with open(SEL_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
                if r.get("error") is None and r["selected_answer"] not in ("", "PARSE_ERROR", "NO_ANSWER"):
                    votes[r["item_id"]].append(r["selected_answer"])
            except Exception:
                pass

    rows = []
    for item_id, answers in sorted(votes.items(), key=lambda x: int(x[0])):
        counter = Counter(answers)
        best_answer, vote_count = counter.most_common(1)[0]
        agreement = vote_count / len(answers)
        rows.append({
            "item_id":        item_id,
            "genselect_answer": best_answer,
            "vote_count":     vote_count,
            "total_perms":    len(answers),
            "agreement_rate": round(agreement, 4),
        })

    with open(FINAL_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["item_id", "genselect_answer", "vote_count", "total_perms", "agreement_rate"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nAggregated {len(rows)} items → {FINAL_FILE}")
    agree_counts = Counter(1 if r["agreement_rate"] == 1.0 else 0 for r in rows)
    print(f"  Perfect agreement (8/8): {agree_counts[1]}")
    print(f"  Partial agreement:       {agree_counts[0]}")
    return rows

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global _start_time, _total_calls

    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke",    action="store_true", help="1 item, 1 perm smoke test")
    parser.add_argument("--item-ids", nargs="+", type=int,  help="Run specific item IDs only")
    parser.add_argument("--workers",  type=int, default=4,  help="Concurrent workers (default 4)")
    parser.add_argument("--force",    action="store_true",  help="Skip 4032-line gate check")
    parser.add_argument("--aggregate-only", action="store_true", help="Skip selection, just aggregate existing SEL_FILE")
    args = parser.parse_args()

    if args.aggregate_only:
        aggregate_selections()
        return

    # Load generation results
    print(f"Loading {GEN_FILE}...")
    samples_by_item = defaultdict(list)
    with open(GEN_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
                if r.get("error") is None:
                    samples_by_item[r["item_id"]].append(r)
            except Exception:
                pass

    total_successful = sum(len(v) for v in samples_by_item.values())
    print(f"  {len(samples_by_item)} items, {total_successful} successful samples")

    # Gate check
    if not args.force and not args.smoke and not args.item_ids:
        if total_successful < EXPECTED_TOTAL:
            print(f"\nGATE FAILED: only {total_successful}/{EXPECTED_TOTAL} successful samples.")
            print("Run genselect_runner.py to completion first, or use --force to override.")
            return
        items_complete = sum(1 for v in samples_by_item.values() if len(v) >= EXPECTED_SAMPLES)
        if items_complete < EXPECTED_ITEMS:
            print(f"\nGATE FAILED: only {items_complete}/{EXPECTED_ITEMS} items have 16 samples.")
            return
        print(f"  Gate passed: {total_successful} samples across {len(samples_by_item)} items.")

    # Load questions
    print("Loading private.jsonl...")
    questions = {}
    with open("private.jsonl") as f:
        for line in f:
            item = json.loads(line)
            iid = int(item["id"])
            is_mcq = bool(item.get("options"))
            if is_mcq:
                opts_text = "\n".join(item["options"])
                questions[iid] = f"{item['question']}\n\nOptions:\n{opts_text}"
            else:
                questions[iid] = item["question"]
    print(f"  {len(questions)} questions loaded")

    # Determine target items
    if args.smoke:
        target_ids = [next(iter(samples_by_item))]
        n_perms = 1
        print(f"  SMOKE: item={target_ids[0]}, 1 perm")
    elif args.item_ids:
        target_ids = args.item_ids
        n_perms = N_PERMS
    else:
        target_ids = sorted(samples_by_item.keys(), key=int)
        n_perms = N_PERMS

    # Load already-done (item_id, perm) from SEL_FILE
    done_set = set()
    if os.path.exists(SEL_FILE):
        with open(SEL_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    if r.get("error") is None:
                        done_set.add((int(r["item_id"]), int(r["permutation"])))
                except Exception:
                    pass
        print(f"  Resuming: {len(done_set)} selections already done")

    # Build work queue
    work = []
    for iid in target_ids:
        if iid not in samples_by_item:
            print(f"  WARNING: item {iid} has no samples, skipping")
            continue
        for perm in range(n_perms):
            if (iid, perm) not in done_set:
                work.append((iid, perm))

    _total_calls = len(work)
    os.makedirs(os.path.dirname(SEL_FILE), exist_ok=True)
    print(f"\n  Items:    {len(target_ids)}")
    print(f"  Perms:    {n_perms}")
    print(f"  Skip:     {len(done_set)}")
    print(f"  To run:   {_total_calls}")
    print(f"  Workers:  {args.workers}")
    print(f"  Output:   {SEL_FILE}")
    print()

    if _total_calls == 0:
        print("Nothing to do.")
        aggregate_selections()
        return

    client = OpenAI(base_url=API_BASE, api_key=API_KEY)
    _start_time = time.time()

    # One RNG per (item, perm) for reproducibility
    def make_rng(iid, perm):
        return random.Random(iid * 1000 + perm)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                run_selection,
                client, iid, perm,
                questions[iid],
                samples_by_item[iid],
                make_rng(iid, perm),
            ): (iid, perm)
            for iid, perm in work
        }
        for _ in as_completed(futures):
            pass

    wall = time.time() - _start_time
    print(f"\n{'='*70}")
    print(f"DONE  completed={_completed}  failed={_failed}  wall={wall/3600:.2f}h")

    aggregate_selections()

if __name__ == "__main__":
    main()

"""Adaptive SC inference for SFT v4: trained items vs untrained items.

Trained items (391, listed in data/sft_v4_dataset.jsonl):
    n=3 samples @ temperature=0.6, max_tokens=4096.
Untrained items (552):
    SC=16  (8 @ T=0.6 + 8 @ T=1.0), max_tokens=16384.
    Shape filter applied before majority vote.

Voted answer per item is the most-frequent extracted boxed string among
shape-accepted samples (multi-answer questions use top-level box count).
The CSV `response` field is the full trace of the sample whose extracted
answer == voted answer (fallback: samples[0]).

Outputs under results/sft_v4_adaptive/:
    submission.csv        -- (id, response) per private item
    samples.jsonl         -- per-item: all samples + vote + shape flags
    run_meta.json         -- config snapshot

Run from repo root:
    python3 scripts/run_adaptive_sc.py sft_v4_epoch6_merged

SECURITY: this is read-only over private.jsonl and writes only to
results/sft_v4_adaptive/. No code execution.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

# Must be set before `import vllm`.
os.environ["VLLM_USE_V1"] = "0"

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import torch  # noqa: E402
import vllm  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402
from vllm import LLM, SamplingParams  # noqa: E402


SYSTEM = "Please reason step by step and put your final answer within \\boxed{}."

# Engine config (mirrors scripts/run_vllm_sc.py)
DTYPE = "bfloat16"
GPU_MEMORY_UTILIZATION = 0.85
MAX_MODEL_LEN = 20480

# Per-pool sampling
TRAINED_N = 3
TRAINED_TEMP = 0.6
TRAINED_TOP_P = 0.95
TRAINED_MAX_TOKENS = 4096

UNTRAINED_N_PER_TEMP = 8
UNTRAINED_TEMPS = [0.6, 1.0]
UNTRAINED_TOP_P = 0.95
UNTRAINED_MAX_TOKENS = 16384


# ---- Helpers ----

def count_top_level_boxes(text: str) -> int:
    """Count \\boxed{} occurrences not nested inside another \\boxed{}."""
    count = 0
    depth = 0
    i = 0
    while i < len(text):
        if text[i:i + 7] == "\\boxed{":
            if depth == 0:
                count += 1
            depth += 1
            i += 7
        elif text[i] == "{" and depth > 0:
            depth += 1
            i += 1
        elif text[i] == "}" and depth > 0:
            depth -= 1
            i += 1
        else:
            i += 1
    return count


def extract_last_boxed(text: str) -> str:
    """Return the contents of the last \\boxed{...} or ''."""
    positions = []
    i = 0
    while i < len(text):
        pos = text.find("\\boxed{", i)
        if pos == -1:
            break
        positions.append(pos)
        i = pos + 7
    if not positions:
        return ""
    start = positions[-1] + 7
    depth, j = 1, start
    while j < len(text) and depth > 0:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    return text[start:j - 1].strip() if depth == 0 else ""


def count_ans_placeholders(question: str) -> int:
    """Number of [ANS] placeholders. 0 means a single-answer question (treat as 1)."""
    n = question.count("[ANS]")
    return max(n, 1)


def build_user(item) -> str:
    """User prompt: question + bare options (no letter labels) if MCQ."""
    q = item.get("question", "")
    opts = item.get("options", [])
    if opts:
        return f"{q}\n\nOptions:\n" + "\n".join(opts)
    return q


def normalize_answer(s: str) -> str:
    """Light normalization for vote bucketing."""
    if not s:
        return ""
    s = s.strip()
    if s.startswith("$") and s.endswith("$") and len(s) >= 2:
        s = s[1:-1].strip()
    s = s.replace("\\,", " ").replace("\\;", " ").replace("\\ ", " ").replace("\\quad", " ").replace("\\!", "")
    s = s.replace("\\dfrac", "\\frac")
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def apply_shape_filter(samples, is_multi_answer):
    """Tag each sample with shape_rejected in-place. Returns (fallback_used, n_dropped).

    Rejects:
      - 0 top-level \\boxed{} (no answer)
      - >1 top-level \\boxed{} on a multi-answer item (per-slot format expected)
    If every sample is rejected, clear all flags (fallback) and return True.
    """
    n_dropped = 0
    for s in samples:
        n_boxes = count_top_level_boxes(s["response"])
        rejected = n_boxes == 0 or (is_multi_answer and n_boxes > 1)
        s["shape_rejected"] = rejected
        if rejected:
            n_dropped += 1
    if all(s["shape_rejected"] for s in samples):
        for s in samples:
            s["shape_rejected"] = False
        return True, n_dropped
    return False, n_dropped


def majority_vote(samples):
    """Majority over non-rejected samples. Returns (voted, count, n_voting)."""
    bucket = Counter()
    raw_for = {}  # normalized -> first raw seen
    for s in samples:
        if s.get("shape_rejected"):
            continue
        ans = s.get("extracted_answer", "")
        if not ans:
            continue
        n = normalize_answer(ans)
        if not n:
            continue
        bucket[n] += 1
        raw_for.setdefault(n, ans)
    if not bucket:
        return "", 0, 0
    winner_norm, count = bucket.most_common(1)[0]
    return raw_for[winner_norm], count, sum(bucket.values())


def pick_response(samples, voted_raw):
    """Pick the full response whose extracted answer matches voted_raw.
    Fallback: first non-rejected sample, then samples[0]."""
    voted_norm = normalize_answer(voted_raw)
    for s in samples:
        if s.get("shape_rejected"):
            continue
        if normalize_answer(s.get("extracted_answer", "")) == voted_norm:
            return s["response"]
    for s in samples:
        if not s.get("shape_rejected"):
            return s["response"]
    return samples[0]["response"] if samples else ""


# ---- Main ----

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("model", nargs="?", default="sft_v4_epoch6_merged")
    p.add_argument("--max-model-len", type=int, default=MAX_MODEL_LEN)
    p.add_argument("--output-dir", default="results/sft_v4_adaptive")
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = REPO_ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    submission_path = out_dir / "submission.csv"
    samples_path = out_dir / "samples.jsonl"
    meta_path = out_dir / "run_meta.json"

    # ---- Load data ----
    with open(REPO_ROOT / "private.jsonl") as f:
        items = [json.loads(l) for l in f]
    items_by_id = {it["id"]: it for it in items}

    trained_ids = set()
    with open(REPO_ROOT / "data" / "sft_v4_dataset.jsonl") as f:
        for line in f:
            trained_ids.add(int(json.loads(line)["item_id"]))

    all_ids = sorted(items_by_id.keys())
    trained = sorted(i for i in all_ids if i in trained_ids)
    untrained = sorted(i for i in all_ids if i not in trained_ids)

    print(f"Items: total={len(all_ids)}  trained={len(trained)}  untrained={len(untrained)}")
    print(f"Trained pool: n={TRAINED_N} @ T={TRAINED_TEMP}, max_tokens={TRAINED_MAX_TOKENS}")
    print(f"Untrained pool: n={UNTRAINED_N_PER_TEMP}x2 @ T={UNTRAINED_TEMPS}, max_tokens={UNTRAINED_MAX_TOKENS}")
    print(f"Output dir: {out_dir}")

    # ---- Write run_meta.json up front ----
    meta = {
        "model": args.model,
        "max_model_len": args.max_model_len,
        "trained": {"n": TRAINED_N, "temperature": TRAINED_TEMP,
                    "top_p": TRAINED_TOP_P, "max_tokens": TRAINED_MAX_TOKENS,
                    "n_items": len(trained)},
        "untrained": {"n_per_temp": UNTRAINED_N_PER_TEMP, "temperatures": UNTRAINED_TEMPS,
                      "top_p": UNTRAINED_TOP_P, "max_tokens": UNTRAINED_MAX_TOKENS,
                      "n_items": len(untrained), "shape_filter": True},
        "system_prompt": SYSTEM,
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    # ---- Load model ----
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    llm = LLM(
        model=args.model,
        dtype=DTYPE,
        trust_remote_code=True,
        gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
        max_model_len=args.max_model_len,
        enable_prefix_caching=True,
        reasoning_parser="deepseek_r1",
    )

    def render(item):
        return tokenizer.apply_chat_template(
            [{"role": "system", "content": SYSTEM},
             {"role": "user", "content": build_user(item)}],
            tokenize=False, add_generation_prompt=True,
        )

    per_item_results = {}  # iid -> dict for samples.jsonl

    # ---- TRAINED pool ----
    t0 = time.perf_counter()
    print(f"\n=== TRAINED ({len(trained)} items, n={TRAINED_N} @ T={TRAINED_TEMP}) ===")
    trained_prompts = [render(items_by_id[iid]) for iid in trained]
    trained_sp = SamplingParams(
        n=TRAINED_N,
        temperature=TRAINED_TEMP,
        top_p=TRAINED_TOP_P,
        max_tokens=TRAINED_MAX_TOKENS,
    )
    trained_out = llm.generate(trained_prompts, trained_sp)
    print(f"  trained generate took {time.perf_counter() - t0:.1f}s")

    for idx, iid in enumerate(trained):
        ro = trained_out[idx]
        item = items_by_id[iid]
        n_ans = count_ans_placeholders(item.get("question", ""))
        samples = []
        for comp in ro.outputs:
            text = comp.text
            samples.append({
                "response": text,
                "gen_tokens": len(comp.token_ids),
                "hit_token_cap": len(comp.token_ids) >= TRAINED_MAX_TOKENS,
                "extracted_answer": extract_last_boxed(text),
                "shape_rejected": False,
                "temperature": TRAINED_TEMP,
            })
        # No shape filter on trained pool.
        voted, votes, n_voting = majority_vote(samples)
        response_for_csv = pick_response(samples, voted)
        per_item_results[iid] = {
            "id": iid,
            "pool": "trained",
            "n_ans_placeholders": n_ans,
            "voted_answer": voted,
            "votes": votes,
            "n_voting": n_voting,
            "shape_fallback": False,
            "n_dropped_shape": 0,
            "samples": samples,
            "response": response_for_csv,
        }

    # ---- UNTRAINED pool (8 + 8 ladder) ----
    t1 = time.perf_counter()
    print(f"\n=== UNTRAINED ({len(untrained)} items, n={UNTRAINED_N_PER_TEMP}x{len(UNTRAINED_TEMPS)} @ T={UNTRAINED_TEMPS}) ===")
    untrained_prompts = [render(items_by_id[iid]) for iid in untrained]

    rung_outs = []  # list of (temp, list[RequestOutput])
    for temp in UNTRAINED_TEMPS:
        rung_t0 = time.perf_counter()
        print(f"  Rung T={temp}: generating {UNTRAINED_N_PER_TEMP} per prompt...")
        rung_sp = SamplingParams(
            n=UNTRAINED_N_PER_TEMP,
            temperature=temp,
            top_p=UNTRAINED_TOP_P,
            max_tokens=UNTRAINED_MAX_TOKENS,
        )
        rung_out = llm.generate(untrained_prompts, rung_sp)
        rung_outs.append((temp, rung_out))
        print(f"    rung took {time.perf_counter() - rung_t0:.1f}s")

    for idx, iid in enumerate(untrained):
        item = items_by_id[iid]
        n_ans = count_ans_placeholders(item.get("question", ""))
        is_multi_answer = n_ans > 1
        samples = []
        for temp, rung_out in rung_outs:
            for comp in rung_out[idx].outputs:
                text = comp.text
                samples.append({
                    "response": text,
                    "gen_tokens": len(comp.token_ids),
                    "hit_token_cap": len(comp.token_ids) >= UNTRAINED_MAX_TOKENS,
                    "extracted_answer": extract_last_boxed(text),
                    "shape_rejected": False,
                    "temperature": temp,
                })
        # Apply shape filter
        shape_fallback, n_dropped = apply_shape_filter(samples, is_multi_answer)
        voted, votes, n_voting = majority_vote(samples)
        response_for_csv = pick_response(samples, voted)
        per_item_results[iid] = {
            "id": iid,
            "pool": "untrained",
            "n_ans_placeholders": n_ans,
            "is_multi_answer": is_multi_answer,
            "voted_answer": voted,
            "votes": votes,
            "n_voting": n_voting,
            "shape_fallback": shape_fallback,
            "n_dropped_shape": n_dropped,
            "samples": samples,
            "response": response_for_csv,
        }

    print(f"\nUntrained generate total: {time.perf_counter() - t1:.1f}s")
    print(f"Overall: {time.perf_counter() - t0:.1f}s")

    # ---- Persist samples.jsonl ----
    with open(samples_path, "w") as f:
        for iid in all_ids:
            r = per_item_results[iid]
            # samples.jsonl row (slim version of response not included to keep file modest;
            # full responses are in r["samples"][i]["response"])
            row = {k: v for k, v in r.items() if k != "response"}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {samples_path}")

    # ---- Build submission.csv ----
    with open(submission_path, "w", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["id", "response"])
        for iid in all_ids:
            writer.writerow([iid, per_item_results[iid]["response"]])
    print(f"Wrote {submission_path}")

    # ---- Stats ----
    truncated = sum(1 for iid in all_ids
                    for s in per_item_results[iid]["samples"]
                    if s["hit_token_cap"])
    no_answer = sum(1 for iid in all_ids if not per_item_results[iid]["voted_answer"])
    shape_fallback_count = sum(1 for iid in untrained if per_item_results[iid].get("shape_fallback"))

    print("\n=== SUMMARY ===")
    print(f"  Items written: {len(all_ids)}")
    print(f"  Items with no voted answer: {no_answer}")
    print(f"  Truncated samples (hit token cap): {truncated}")
    print(f"  Untrained items where shape filter fell back (all rejected): {shape_fallback_count}")

    meta["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    meta["stats"] = {
        "n_items": len(all_ids),
        "no_voted_answer": no_answer,
        "truncated_samples": truncated,
        "shape_fallback_items": shape_fallback_count,
        "wall_seconds": time.perf_counter() - t0,
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)


if __name__ == "__main__":
    main()

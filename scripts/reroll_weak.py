"""Re-roll a small set of weak items at higher max_tokens.

Loads vLLM at max_model_len=36864, regenerates samples for the listed
weak IDs (each split into trained vs untrained pool), then PATCHES IN
PLACE:
  - results/sft_v4_adaptive/submission.csv  (row replaced)
  - results/sft_v4_adaptive/samples.jsonl   (line replaced)

Originals are backed up to *.before_reroll.

Run from repo root:
    python3 scripts/reroll_weak.py sft_v4_epoch6_merged
"""

import argparse
import csv
import json
import os
import shutil
import sys
import time
from pathlib import Path

# Must be set before `import vllm`.
os.environ["VLLM_USE_V1"] = "0"

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import torch  # noqa: E402
import vllm  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402
from vllm import LLM, SamplingParams  # noqa: E402

# Reuse the canonical helpers from run_adaptive_sc.py.
from scripts.run_adaptive_sc import (  # noqa: E402
    SYSTEM,
    DTYPE,
    GPU_MEMORY_UTILIZATION,
    apply_shape_filter,
    build_user,
    count_ans_placeholders,
    extract_last_boxed,
    majority_vote,
    pick_response,
)


# === The reroll targets ===
TRAINED_REROLL = {
    336: {"pool": "trained", "n": 3, "temps": [0.6], "max_tokens": 8192},
}
UNTRAINED_REROLL = {
    19:  {"pool": "untrained", "n_per_temp": 8, "temps": [0.6, 1.0], "max_tokens": 32768},
    652: {"pool": "untrained", "n_per_temp": 8, "temps": [0.6, 1.0], "max_tokens": 32768},
    751: {"pool": "untrained", "n_per_temp": 8, "temps": [0.6, 1.0], "max_tokens": 32768},
    823: {"pool": "untrained", "n_per_temp": 8, "temps": [0.6, 1.0], "max_tokens": 32768},
}

# vLLM context budget must hold prompt + max_tokens. Untrained uses 32768.
MAX_MODEL_LEN = 36864

OUT_DIR = REPO_ROOT / "results" / "sft_v4_adaptive"
CSV_PATH = OUT_DIR / "submission.csv"
JSONL_PATH = OUT_DIR / "samples.jsonl"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("model", nargs="?", default="sft_v4_epoch6_merged")
    p.add_argument("--max-model-len", type=int, default=MAX_MODEL_LEN)
    return p.parse_args()


def render(item, tokenizer):
    return tokenizer.apply_chat_template(
        [{"role": "system", "content": SYSTEM},
         {"role": "user", "content": build_user(item)}],
        tokenize=False, add_generation_prompt=True,
    )


def main():
    args = parse_args()

    # 1. Load private items
    with open(REPO_ROOT / "private.jsonl") as f:
        items_by_id = {json.loads(l)["id"]: json.loads(l) for l in f}

    targets = {**TRAINED_REROLL, **UNTRAINED_REROLL}
    print(f"Reroll targets ({len(targets)}): {sorted(targets)}")
    print(f"max_model_len = {args.max_model_len}")

    # 2. Backup originals
    for p in (CSV_PATH, JSONL_PATH):
        bk = p.with_suffix(p.suffix + ".before_reroll")
        if not bk.exists():
            shutil.copyfile(p, bk)
            print(f"  backed up {p.name} -> {bk.name}")

    # 3. Load model
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

    # 4. Generate new results per item
    new_results = {}  # iid -> patched samples.jsonl row + chosen response

    for iid, cfg in TRAINED_REROLL.items():
        item = items_by_id[iid]
        n_ans = count_ans_placeholders(item.get("question", ""))
        prompt = render(item, tokenizer)
        print(f"\n[TRAINED] ID {iid}: n={cfg['n']} @ T={cfg['temps'][0]} max_tokens={cfg['max_tokens']}")
        sp = SamplingParams(n=cfg["n"], temperature=cfg["temps"][0], top_p=0.95,
                            max_tokens=cfg["max_tokens"])
        t0 = time.perf_counter()
        out = llm.generate([prompt], sp)
        print(f"  generate took {time.perf_counter() - t0:.1f}s")
        samples = []
        for comp in out[0].outputs:
            text = comp.text
            samples.append({
                "response": text,
                "gen_tokens": len(comp.token_ids),
                "hit_token_cap": len(comp.token_ids) >= cfg["max_tokens"],
                "extracted_answer": extract_last_boxed(text),
                "shape_rejected": False,
                "temperature": cfg["temps"][0],
            })
        voted, votes, n_voting = majority_vote(samples)
        response_csv = pick_response(samples, voted)
        new_results[iid] = {
            "id": iid,
            "pool": "trained",
            "n_ans_placeholders": n_ans,
            "voted_answer": voted,
            "votes": votes,
            "n_voting": n_voting,
            "shape_fallback": False,
            "n_dropped_shape": 0,
            "samples": samples,
            "_response_for_csv": response_csv,
            "_rerolled": True,
            "_reroll_max_tokens": cfg["max_tokens"],
        }
        truncated = sum(1 for s in samples if s["hit_token_cap"])
        print(f"  voted='{voted[:40]}' votes={votes}/{n_voting} truncated={truncated}/{len(samples)}")

    for iid, cfg in UNTRAINED_REROLL.items():
        item = items_by_id[iid]
        n_ans = count_ans_placeholders(item.get("question", ""))
        is_multi = n_ans > 1
        prompt = render(item, tokenizer)
        print(f"\n[UNTRAINED] ID {iid}: n=8x{len(cfg['temps'])} @ T={cfg['temps']} max_tokens={cfg['max_tokens']}")
        samples = []
        for temp in cfg["temps"]:
            sp = SamplingParams(n=cfg["n_per_temp"], temperature=temp, top_p=0.95,
                                max_tokens=cfg["max_tokens"])
            t0 = time.perf_counter()
            out = llm.generate([prompt], sp)
            print(f"  rung T={temp} took {time.perf_counter() - t0:.1f}s")
            for comp in out[0].outputs:
                text = comp.text
                samples.append({
                    "response": text,
                    "gen_tokens": len(comp.token_ids),
                    "hit_token_cap": len(comp.token_ids) >= cfg["max_tokens"],
                    "extracted_answer": extract_last_boxed(text),
                    "shape_rejected": False,
                    "temperature": temp,
                })
        shape_fallback, n_dropped = apply_shape_filter(samples, is_multi)
        voted, votes, n_voting = majority_vote(samples)
        response_csv = pick_response(samples, voted)
        new_results[iid] = {
            "id": iid,
            "pool": "untrained",
            "n_ans_placeholders": n_ans,
            "is_multi_answer": is_multi,
            "voted_answer": voted,
            "votes": votes,
            "n_voting": n_voting,
            "shape_fallback": shape_fallback,
            "n_dropped_shape": n_dropped,
            "samples": samples,
            "_response_for_csv": response_csv,
            "_rerolled": True,
            "_reroll_max_tokens": cfg["max_tokens"],
        }
        truncated = sum(1 for s in samples if s["hit_token_cap"])
        print(f"  voted='{voted[:40]}' votes={votes}/{n_voting} truncated={truncated}/{len(samples)}  shape_dropped={n_dropped} fallback={shape_fallback}")

    # 5. Patch samples.jsonl in place
    new_jsonl_rows = []
    with open(JSONL_PATH) as f:
        for line in f:
            d = json.loads(line)
            iid = d["id"]
            if iid in new_results:
                # rebuild the row from new_results, drop helper keys
                r = new_results[iid]
                row = {k: v for k, v in r.items() if not k.startswith("_")}
                # add reroll provenance to the row
                row["rerolled"] = True
                row["reroll_max_tokens"] = r["_reroll_max_tokens"]
                new_jsonl_rows.append(row)
            else:
                new_jsonl_rows.append(d)
    with open(JSONL_PATH, "w") as f:
        for row in new_jsonl_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"\nPatched {JSONL_PATH}")

    # 6. Patch submission.csv in place
    new_csv_rows = []
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            iid = int(row["id"])
            if iid in new_results:
                new_csv_rows.append((iid, new_results[iid]["_response_for_csv"]))
            else:
                new_csv_rows.append((iid, row["response"]))
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["id", "response"])
        for iid, resp in new_csv_rows:
            writer.writerow([iid, resp])
    print(f"Patched {CSV_PATH}")

    # 7. Summary table
    print("\n=== RE-ROLL SUMMARY ===")
    for iid in sorted(new_results):
        r = new_results[iid]
        truncated = sum(1 for s in r["samples"] if s["hit_token_cap"])
        print(f"  ID {iid} [{r['pool']}]: voted='{r['voted_answer'][:40]}' "
              f"votes={r['votes']}/{r['n_voting']}  truncated={truncated}/{len(r['samples'])}")


if __name__ == "__main__":
    main()

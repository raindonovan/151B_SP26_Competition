"""SFT v5 checkpoint memorization test.

Tests 4 checkpoints (epochs 8/12/14/16) on 20 trained items
(10 MCQ + 10 FREE, first 10 of each by item_id). For each item:
  - Generate SC=3 at T=0.6, max_tokens=4096
  - Extract \\boxed{...} from each sample
  - "3/3 consistent" = all 3 extractions match the training label
    (compared via the same normalize() used elsewhere)

Reports per checkpoint:
  Epoch X (step Y): N/20 items 3/3 consistent
    MCQ: M/10 | Free: F/10
    Failed IDs: [...]

Picks highest N (ties broken by latest epoch).
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

os.environ["VLLM_USE_V1"] = "0"

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import torch  # noqa: E402
import vllm  # noqa: E402
from vllm import LLM, SamplingParams  # noqa: E402
from vllm.lora.request import LoRARequest  # noqa: E402

# Reuse canonical helpers from run_hybrid_inference
from scripts.run_hybrid_inference import SYSTEM_PROMPT, build_user_msg  # noqa: E402


BASE_MODEL = "Qwen/Qwen3-4B-Thinking-2507"
CHECKPOINTS = [
    (8, "checkpoints/sft_v5/checkpoint-784"),
    (12, "checkpoints/sft_v5/checkpoint-1176"),
    (14, "checkpoints/sft_v5/checkpoint-1372"),
    (16, "checkpoints/sft_v5/checkpoint-1568"),
]


def extract_last_boxed(text):
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


def normalize(s):
    if not s:
        return ""
    s = str(s).strip()
    if s.startswith("$") and s.endswith("$") and len(s) >= 2:
        s = s[1:-1].strip()
    for esc in ["\\,", "\\;", "\\ ", "\\quad", "\\!"]:
        s = s.replace(esc, " " if esc != "\\!" else "")
    s = s.replace("\\dfrac", "\\frac")
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--base-model", default=BASE_MODEL)
    p.add_argument("--mcq-format", default="letters")
    p.add_argument("--sc", type=int, default=3)
    p.add_argument("--temperature", type=float, default=0.6)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("--gpu-util", type=float, default=0.85)
    return p.parse_args()


def main():
    args = parse_args()

    # 1. Load private (needed for build_user_msg)
    with open(REPO_ROOT / "private.jsonl") as f:
        priv = {int(json.loads(l)["id"]): json.loads(l) for l in f}

    # 2. Load training labels from v5 dataset; pick test items.
    train_items = []
    with open(REPO_ROOT / "data" / "sft_v5_dataset.jsonl") as f:
        for line in f:
            train_items.append(json.loads(line))

    train_label = {}  # iid -> last boxed in trace
    for it in train_items:
        iid = int(it["item_id"])
        train_label[iid] = extract_last_boxed(it["messages"][2]["content"])

    # First 10 MCQ + first 10 FREE by item_id
    sorted_train = sorted(train_label.keys())
    mcq_ids = [iid for iid in sorted_train if priv[iid].get("options")][:10]
    free_ids = [iid for iid in sorted_train if not priv[iid].get("options")][:10]
    test_ids = mcq_ids + free_ids
    print(f"Test items: 10 MCQ + 10 FREE")
    print(f"  MCQ IDs:  {mcq_ids}")
    print(f"  FREE IDs: {free_ids}")

    # 3. Boot vLLM ONCE with enable_lora; swap adapters via LoRARequest.
    llm = LLM(
        model=args.base_model,
        gpu_memory_utilization=args.gpu_util,
        enable_prefix_caching=True,
        max_model_len=args.max_tokens + 4096,
        reasoning_parser="deepseek_r1",
        trust_remote_code=True,
        dtype="bfloat16",
        enable_lora=True,
        max_lora_rank=64,
    )
    tokenizer = llm.get_tokenizer()

    # 4. Build prompts once (same set across checkpoints).
    prompts = []
    for iid in test_ids:
        item = priv[iid]
        user_msg = build_user_msg(item, args.mcq_format)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ]
        prompts.append(tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        ))

    sampling = SamplingParams(
        n=args.sc,
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
    )

    # 5. For each checkpoint: load adapter -> generate -> score.
    results = []
    for ckpt_idx, (epoch, adapter_path) in enumerate(CHECKPOINTS):
        if not os.path.isdir(adapter_path):
            print(f"\nSKIP epoch {epoch}: {adapter_path} does not exist")
            continue
        lora_req = LoRARequest(f"sft_v5_ep{epoch}", ckpt_idx + 1, adapter_path)
        print(f"\n{'=' * 60}")
        print(f"Epoch {epoch} (step {adapter_path.split('-')[-1]})")
        print(f"  Adapter: {adapter_path}")
        print("=" * 60)

        outputs = llm.generate(prompts, sampling, lora_request=lora_req)

        consistent = 0
        mcq_consistent = 0
        free_consistent = 0
        failed = []

        for idx, iid in enumerate(test_ids):
            label = normalize(train_label[iid])
            samples = [normalize(extract_last_boxed(c.text)) for c in outputs[idx].outputs]
            is_mcq = priv[iid].get("options") is not None and len(priv[iid].get("options", [])) > 0

            # "3/3 consistent" = all 3 samples match the training label
            match = sum(1 for s in samples if s == label and s != "")
            ok = match == args.sc
            if ok:
                consistent += 1
                if is_mcq:
                    mcq_consistent += 1
                else:
                    free_consistent += 1
            else:
                failed.append((iid, label[:30], samples))

        print(f"  Result: {consistent}/{len(test_ids)} items {args.sc}/{args.sc} consistent")
        print(f"    MCQ:  {mcq_consistent}/{len(mcq_ids)} consistent")
        print(f"    FREE: {free_consistent}/{len(free_ids)} consistent")
        if failed:
            print(f"    Failed IDs: {[f[0] for f in failed]}")
            # Show details for first 5 failures
            for iid, label, samples in failed[:5]:
                print(f"      ID {iid} label='{label}' got={samples}")
        results.append({
            "epoch": epoch,
            "adapter": adapter_path,
            "consistent": consistent,
            "mcq_consistent": mcq_consistent,
            "free_consistent": free_consistent,
            "failed": [f[0] for f in failed],
        })

    # 6. Pick best: highest N, ties -> latest epoch.
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"  Epoch {r['epoch']:>2}: {r['consistent']}/{len(test_ids)} "
              f"(MCQ {r['mcq_consistent']}/{len(mcq_ids)}, "
              f"FREE {r['free_consistent']}/{len(free_ids)})")

    if results:
        # results is in epoch order ascending; latest epoch with max N wins.
        best_n = max(r["consistent"] for r in results)
        best = [r for r in results if r["consistent"] == best_n][-1]
        print(f"\nWINNER: Epoch {best['epoch']} ({best['adapter']})")
        print(f"  Score: {best['consistent']}/{len(test_ids)}")
        print(f"  No merge -- keep as LoRA adapter.")


if __name__ == "__main__":
    main()

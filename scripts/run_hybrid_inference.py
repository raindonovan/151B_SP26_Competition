"""Hybrid inference: base model SC or adapter SC with resume + live feedback.

TWO MODES:
  --mode base    : Base model, 943 items, SC=8, 32K tokens
  --mode adapter : SFT adapter via LoRARequest, subset of items, SC=3, 4K tokens

Usage:
  # Base run (DSMLP A30):
  python3 scripts/run_hybrid_inference.py \
    --mode base \
    --model Qwen/Qwen3-4B-Thinking-2507 \
    --output results/hybrid/base_run.jsonl \
    --max-tokens 32768 --sc 8 --temperature 0.6

  # Adapter run:
  python3 scripts/run_hybrid_inference.py \
    --mode adapter \
    --model Qwen/Qwen3-4B-Thinking-2507 \
    --adapter-path checkpoints/sft_v4/checkpoint-588 \
    --item-ids results/hybrid/adapter_pass_set.txt \
    --output results/hybrid/adapter_run.jsonl \
    --max-tokens 4096 --sc 3 --temperature 0.6
"""

import os
os.environ["VLLM_USE_V1"] = "0"

import argparse
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone

SYSTEM_PROMPT = (
    "Please reason step by step and put your final answer within \\boxed{}."
)
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# ── Answer utilities (mirrors build_answer_sheet_v4.py) ───────────────────────
def normalize_answer(ans: str) -> str:
    if not ans:
        return ""
    s = ans.strip().strip("$")
    s = re.sub(r"\\dfrac", r"\\frac", s)
    s = re.sub(r"\\,|\\;|\\!", "", s)
    s = re.sub(r"\s*,\s*", ",", s)
    return s.strip()

def extract_last_boxed(text: str) -> str:
    matches = list(re.finditer(r"\\boxed\{", text))
    if not matches:
        return ""
    start = matches[-1].end()
    depth, i = 1, start
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return normalize_answer(text[start : i - 1])

# V3 shape filter: reject implausible answers on untrained items
_SHAPE_PATTERNS = [
    re.compile(r"^\d{6,}$"),           # very long raw integers
    re.compile(r"^[A-Z]{5,}$"),        # long uppercase strings
    re.compile(r"^\s*$"),              # empty
]

def shape_filter(ans: str) -> bool:
    """Returns True if answer passes (looks plausible)."""
    for pat in _SHAPE_PATTERNS:
        if pat.match(ans):
            return False
    return True

def majority_vote(
    samples: list[str], apply_shape_filter: bool = True
) -> tuple[str, int, int]:
    """Returns (voted_answer, votes_for_winner, n_voting)."""
    answers = [extract_last_boxed(s) for s in samples]
    valid = [a for a in answers if a]
    if apply_shape_filter:
        valid = [a for a in valid if shape_filter(a)]
    if not valid:
        return ("", 0, 0)
    counts = Counter(valid)
    winner, votes = counts.most_common(1)[0]
    return winner, votes, len(valid)

def pick_response(samples: list[str], voted_answer: str) -> str:
    """Return full trace of first sample whose boxed answer matches voted."""
    for s in samples:
        if extract_last_boxed(s) == voted_answer:
            return s
    return samples[0] if samples else ""

# ── Prompt construction ───────────────────────────────────────────────────────
def build_user_msg(item: dict) -> str:
    question = item["question"]
    options = item.get("options")
    if options:
        opts_text = "\n".join(
            f"{LETTERS[i]}. {opt}" for i, opt in enumerate(options)
        )
        return f"{question}\n\nOptions:\n{opts_text}"
    return question

# ── Load private items ────────────────────────────────────────────────────────
def load_items(item_ids: list[int] | None = None) -> list[dict]:
    items = {}
    with open("private.jsonl") as f:
        for line in f:
            it = json.loads(line)
            items[int(it["id"])] = it
    if item_ids is not None:
        return [items[i] for i in item_ids if i in items]
    return [items[i] for i in sorted(items)]

# ── Resume: load already-completed IDs ───────────────────────────────────────
def load_done(output_path: str) -> set[int]:
    done = set()
    if not os.path.exists(output_path):
        return done
    with open(output_path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
                done.add(int(r["id"]))
            except Exception:
                pass
    return done

# ── Write one result ──────────────────────────────────────────────────────────
def write_result(path: str, result: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

# ── Live feedback ─────────────────────────────────────────────────────────────
def print_progress(
    idx: int,
    total: int,
    item_id: int,
    is_mcq: bool,
    voted: str,
    votes: int,
    n_voting: int,
    wall: float,
    timings: list[float],
    slow_threshold: float = 5.0,
) -> None:
    avg = sum(timings) / len(timings) if timings else wall
    remaining = total - idx
    eta_s = remaining * avg
    eta_str = (
        f"{eta_s/3600:.1f}h" if eta_s >= 3600
        else f"{eta_s/60:.0f}m" if eta_s >= 60
        else f"{eta_s:.0f}s"
    )
    kind = "MCQ" if is_mcq else "FRE"
    slow = wall > slow_threshold * avg and len(timings) > 3
    prefix = "⚠️ " if slow else "   "
    slow_tag = f" SLOW: {wall:.1f}s (avg {avg:.1f}s)" if slow else ""
    print(
        f"{prefix}[{idx:>4}/{total}] ID {item_id:>4} [{kind}] "
        f"voted={voted!r:10s} ({votes}/{n_voting}) "
        f"{wall:.1f}s{slow_tag} | done={idx} avg={avg:.1f}s ETA={eta_str}",
        flush=True,
    )

# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["base", "adapter"], required=True)
    parser.add_argument("--model", required=True, help="HF model path or name")
    parser.add_argument("--adapter-path", default=None,
                        help="LoRA adapter path (adapter mode only)")
    parser.add_argument("--item-ids", default=None,
                        help="Path to text file with one item ID per line (adapter mode)")
    parser.add_argument("--output", required=True, help="Output JSONL path")
    parser.add_argument("--max-tokens", type=int, default=32768)
    parser.add_argument("--sc", type=int, default=8, help="SC samples per item")
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--gpu-util", type=float, default=0.85)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    # Determine item IDs to run
    if args.item_ids:
        with open(args.item_ids) as f:
            target_ids = [int(l.strip()) for l in f if l.strip()]
    else:
        target_ids = None  # all 943

    # Resume
    done = load_done(args.output)
    print(f"Resuming: found {len(done)} completed items, skipping")

    # Load items
    all_items = load_items(target_ids)
    items = [it for it in all_items if int(it["id"]) not in done]
    total = len(all_items)
    print(f"Target: {total} items | To run: {len(items)} | SC={args.sc} | max_tokens={args.max_tokens}")

    if not items:
        print("Nothing to do.")
        return

    # Build vLLM engine
    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest

    llm_kwargs = dict(
        model=args.model,
        gpu_memory_utilization=args.gpu_util,
        enable_prefix_caching=True,
        max_model_len=args.max_tokens + 4096,
        reasoning_parser="deepseek_r1",
    )
    if args.mode == "adapter":
        if not args.adapter_path:
            raise ValueError("--adapter-path required for adapter mode")
        llm_kwargs["enable_lora"] = True
        llm_kwargs["max_lora_rank"] = 64

    llm = LLM(**llm_kwargs)

    sampling = SamplingParams(
        n=args.sc,
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
    )

    lora_req = None
    if args.mode == "adapter":
        lora_req = LoRARequest("sft_adapter", 1, args.adapter_path)

    timings: list[float] = []
    idx = len(done)

    for item in items:
        iid = int(item["id"])
        is_mcq = bool(item.get("options"))
        user_msg = build_user_msg(item)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ]

        t0 = time.time()
        kwargs = {"lora_request": lora_req} if lora_req else {}
        outputs = llm.chat(messages, sampling_params=sampling, **kwargs)
        wall = time.time() - t0

        samples = [c.text for c in outputs[0].outputs]
        apply_filter = args.mode == "base"
        voted, votes, n_voting = majority_vote(samples, apply_shape_filter=apply_filter)
        response = pick_response(samples, voted)

        result = {
            "id": iid,
            "mode": args.mode,
            "voted_answer": voted,
            "votes": votes,
            "n_voting": n_voting,
            "response": response,
            "samples": samples,
            "wall_seconds": round(wall, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        write_result(args.output, result)

        idx += 1
        timings.append(wall)
        print_progress(idx, total, iid, is_mcq, voted, votes, n_voting, wall, timings)

    print(f"\nDone. {idx} items written to {args.output}")


if __name__ == "__main__":
    main()

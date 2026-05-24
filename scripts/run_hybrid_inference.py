"""Hybrid inference: base model SC or adapter SC with resume + live feedback.

TWO MODES:
  --mode base    : Base model, 943 items, SC=8, 32K tokens
  --mode adapter : SFT adapter via LoRARequest, subset of items, SC=3, 4K tokens

Usage:
  # Base run (DSMLP A30):
  VLLM_USE_V1=0 python3 scripts/run_hybrid_inference.py \
    --mode base \
    --model Qwen/Qwen3-4B-Thinking-2507 \
    --output results/hybrid/base_run.jsonl \
    --max-tokens 32768 --sc 8 --temperature 0.6

  # Adapter run (v5 adapter, letter-labelled MCQ):
  VLLM_USE_V1=0 python3 scripts/run_hybrid_inference.py \
    --mode adapter \
    --model Qwen/Qwen3-4B-Thinking-2507 \
    --adapter-path checkpoints/sft_v4/checkpoint-588 \
    --item-ids results/hybrid/adapter_pass_set.txt \
    --output results/hybrid/adapter_run.jsonl \
    --max-tokens 4096 --sc 3 --temperature 0.6

  # Adapter run (v4 adapter, bare MCQ options):
  VLLM_USE_V1=0 python3 scripts/run_hybrid_inference.py \
    --mode adapter --mcq-format bare ...
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

# ── Answer utilities (mirrors run_adaptive_sc.py) ─────────────────────────────
def normalize_answer(s: str) -> str:
    if not s:
        return ""
    s = s.strip()
    if s.startswith("$") and s.endswith("$") and len(s) >= 2:
        s = s[1:-1].strip()
    s = s.replace("\\,", " ").replace("\\;", " ").replace("\\ ", " ")
    s = s.replace("\\quad", " ").replace("\\!", "")
    s = s.replace("\\dfrac", "\\frac")
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

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
    return text[start : j - 1].strip() if depth == 0 else ""

def count_ans_placeholders(question: str) -> int:
    n = question.count("[ANS]")
    return max(n, 1)

def apply_shape_filter(
    sample_texts: list[str], is_multi_answer: bool
) -> tuple[list[bool], bool]:
    """Returns (rejected_flags, fallback_used).

    Rejects samples with:
      - 0 top-level \\boxed{} (no answer given)
      - >1 top-level \\boxed{} on a multi-answer item
    Falls back to all-accepted if every sample is rejected.
    """
    rejected = []
    for text in sample_texts:
        n_boxes = count_top_level_boxes(text)
        rejected.append(n_boxes == 0 or (is_multi_answer and n_boxes > 1))
    if all(rejected):
        return [False] * len(sample_texts), True  # fallback
    return rejected, False

def majority_vote_filtered(
    sample_texts: list[str], rejected: list[bool]
) -> tuple[str, int, int]:
    """Majority over non-rejected samples. Returns (voted_raw, votes, n_voting)."""
    bucket: Counter = Counter()
    raw_for: dict[str, str] = {}
    for text, rej in zip(sample_texts, rejected):
        if rej:
            continue
        ans = extract_last_boxed(text)
        if not ans:
            continue
        norm = normalize_answer(ans)
        if not norm:
            continue
        bucket[norm] += 1
        raw_for.setdefault(norm, ans)
    if not bucket:
        return "", 0, 0
    winner_norm, votes = bucket.most_common(1)[0]
    return raw_for[winner_norm], votes, sum(bucket.values())

def pick_response(
    sample_texts: list[str], rejected: list[bool], voted_raw: str
) -> str:
    """Full trace of first non-rejected sample matching voted_raw."""
    voted_norm = normalize_answer(voted_raw)
    for text, rej in zip(sample_texts, rejected):
        if rej:
            continue
        if normalize_answer(extract_last_boxed(text)) == voted_norm:
            return text
    for text, rej in zip(sample_texts, rejected):
        if not rej:
            return text
    return sample_texts[0] if sample_texts else ""

# ── Prompt construction ───────────────────────────────────────────────────────
def build_user_msg(item: dict, mcq_format: str = "letters") -> str:
    question = item["question"]
    options = item.get("options")
    if options:
        if mcq_format == "letters":
            opts_text = "\n".join(
                f"{LETTERS[i]}. {opt}" for i, opt in enumerate(options)
            )
        else:  # bare — v4 adapter format
            opts_text = "\n".join(options)
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

# ── Resume ────────────────────────────────────────────────────────────────────
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
                        help="Text file with one item ID per line")
    parser.add_argument("--output", required=True, help="Output JSONL path")
    parser.add_argument("--max-tokens", type=int, default=32768)
    parser.add_argument("--sc", type=int, default=8, help="SC samples per item")
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--gpu-util", type=float, default=0.85)
    parser.add_argument("--mcq-format", choices=["letters", "bare"], default="letters",
                        help="letters=A. B. C. (v5/base), bare=no labels (v4 adapter)")
    parser.add_argument("--thinking-budget", type=int, default=None,
                        help="Max thinking tokens before forcing </think>. None = unlimited.")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    if args.item_ids:
        with open(args.item_ids) as f:
            target_ids = [int(l.strip()) for l in f if l.strip()]
    else:
        target_ids = None

    done = load_done(args.output)
    print(f"Resuming: found {len(done)} completed items, skipping")

    all_items = load_items(target_ids)
    items = [it for it in all_items if int(it["id"]) not in done]
    total = len(all_items)
    print(f"Target: {total} items | To run: {len(items)} | SC={args.sc} | "
          f"max_tokens={args.max_tokens} | mcq_format={args.mcq_format}")

    if not items:
        print("Nothing to do.")
        return

    from vllm import LLM, SamplingParams
    from vllm.lora.request import LoRARequest

    llm_kwargs = dict(
        model=args.model,
        gpu_memory_utilization=args.gpu_util,
        enable_prefix_caching=True,
        max_model_len=args.max_tokens + 4096,
        reasoning_parser="deepseek_r1",
        trust_remote_code=True,
        dtype="bfloat16",
    )
    if args.mode == "adapter":
        if not args.adapter_path:
            raise ValueError("--adapter-path required for adapter mode")
        llm_kwargs["enable_lora"] = True
        llm_kwargs["max_lora_rank"] = 64

    llm = LLM(**llm_kwargs)

    # Use tokenizer to apply chat template manually (consistent with run_adaptive_sc.py)
    tokenizer = llm.get_tokenizer()

    sp_kwargs = dict(
        n=args.sc,
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
    )
    if args.thinking_budget is not None:
        sp_kwargs["thinking_token_budget"] = args.thinking_budget
    sampling = SamplingParams(**sp_kwargs)

    lora_req = None
    if args.mode == "adapter":
        lora_req = LoRARequest("sft_adapter", 1, args.adapter_path)

    timings: list[float] = []
    idx = len(done)

    for item in items:
        iid = int(item["id"])
        is_mcq = bool(item.get("options"))
        is_multi = count_ans_placeholders(item.get("question", "")) > 1
        user_msg = build_user_msg(item, args.mcq_format)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        t0 = time.time()
        gen_kwargs = {"lora_request": lora_req} if lora_req else {}
        outputs = llm.generate(prompt, sampling_params=sampling, **gen_kwargs)
        wall = time.time() - t0

        sample_texts = [o.text for o in outputs[0].outputs]

        apply_filter = args.mode == "base"
        if apply_filter:
            rejected, fallback = apply_shape_filter(sample_texts, is_multi)
        else:
            rejected = [False] * len(sample_texts)
            fallback = False

        voted, votes, n_voting = majority_vote_filtered(sample_texts, rejected)
        response = pick_response(sample_texts, rejected, voted)

        result = {
            "id": iid,
            "mode": args.mode,
            "voted_answer": voted,
            "votes": votes,
            "n_voting": n_voting,
            "shape_fallback": fallback,
            "response": response,
            "samples": sample_texts,
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

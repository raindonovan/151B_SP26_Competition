"""Run a vLLM inference experiment on the CSE151B competition data.

Mirrors the v1 baseline prompt policy from starter_code_cse151b_comp.ipynb
and uses the existing judger.py for scoring. Writes one JSONL row per
question and prints a summary at the end.

This script is intended for the vLLM environment on this pod. vLLM v1 is
disabled here (VLLM_USE_V1=0) because it is the only mode currently working
on this setup.
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Must be set before `import vllm` — required by current pod setup.
os.environ["VLLM_USE_V1"] = "0"

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import torch  # noqa: E402
import transformers  # noqa: E402
import vllm  # noqa: E402
from judger import Judger  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402
from vllm import LLM, SamplingParams  # noqa: E402

MODEL_ID = "Qwen/Qwen3-4B-Thinking-2507"
METHOD = "vllm"
PROMPT_VERSION = "v1-baseline"

# Engine config — referenced by both LLM(...) and the summary.
DTYPE = "bfloat16"
QUANTIZATION = "none"
GPU_MEMORY_UTILIZATION = 0.85
VLLM_USE_V1 = "0"  # see env var set above

# Single source of truth for sampling — referenced by SamplingParams, per-row
# fields, and the summary file so they cannot drift apart.
SAMPLING = {
    "temperature": 0.6,
    "top_p": 0.95,
    "top_k": 20,
    "repetition_penalty": 1.0,
}

SYSTEM_PROMPT_MATH = (
    "You are an expert mathematician. Solve the problem step-by-step. "
    "Put your final answer inside \\boxed{}. "
    "If the problem has multiple sub-answers, separate them by commas inside a single \\boxed{}, "
    "e.g. \\boxed{3, 7}."
)

SYSTEM_PROMPT_MCQ = (
    "You are an expert mathematician. "
    "Read the problem and the answer choices below, then select the single best answer. "
    "Output ONLY the letter of your chosen option inside \\boxed{}, e.g. \\boxed{C}."
)


def build_prompt(question: str, options: Optional[list]) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for a question — v1 baseline."""
    if options:
        labels = [chr(65 + i) for i in range(len(options))]
        opts_text = "\n".join(f"{lbl}. {opt.strip()}" for lbl, opt in zip(labels, options))
        return SYSTEM_PROMPT_MCQ, f"{question}\n\nOptions:\n{opts_text}"
    return SYSTEM_PROMPT_MATH, question


def extract_letter(text: str) -> str:
    m = re.search(r"\\boxed\{([A-Za-z])\}", text)
    if m:
        return m.group(1).upper()
    matches = re.findall(r"\b([A-Z])\b", text.upper())
    return matches[-1] if matches else ""


def score_mcq(response: str, gold_letter: str) -> bool:
    return extract_letter(response) == gold_letter.strip().upper()


def has_boxed(response: str) -> bool:
    """True if a closed \\boxed{...} appears after the last </think> (or anywhere if no think tag)."""
    end = response.rfind("</think>")
    tail = response[end + len("</think>"):] if end >= 0 else response
    idx = tail.find("\\boxed{")
    if idx < 0:
        return False
    depth = 1
    i = idx + len("\\boxed{")
    while i < len(tail) and depth > 0:
        if tail[i] == "{":
            depth += 1
        elif tail[i] == "}":
            depth -= 1
        i += 1
    return depth == 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument("--data-start", type=int, default=0)
    p.add_argument("--data-end", type=int, required=True)
    p.add_argument("--max-new-tokens", type=int, required=True)
    p.add_argument("--output", required=True)
    # Default 16384 matches Pod A's input-truncation cap and gives a full
    # 8192-token generation budget regardless of prompt length. vLLM caps
    # prompt + generation combined at this value — setting it equal to
    # max_new_tokens silently shrinks effective gen budget on any non-empty
    # prompt. Override (e.g. 24576) when running with max_new_tokens > 8192.
    p.add_argument("--max-model-len", type=int, default=16384)
    p.add_argument("--data-path", default=str(REPO_ROOT / "data" / "public.jsonl"))
    return p.parse_args()


def load_data(path: str, start: int, end: int) -> list[dict]:
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items[start:end]


def main() -> None:
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    args = parse_args()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    items = load_data(args.data_path, args.data_start, args.data_end)
    print(f"Loaded {len(items)} questions [{args.data_start}:{args.data_end}] from {args.data_path}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)

    prompts = []
    for item in items:
        system, user = build_prompt(item["question"], item.get("options"))
        prompt_text = tokenizer.apply_chat_template(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            tokenize=False,
            add_generation_prompt=True,
        )
        prompts.append(prompt_text)

    llm = LLM(
        model=MODEL_ID,
        dtype=DTYPE,
        trust_remote_code=True,
        gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
        max_model_len=args.max_model_len,
    )

    sampling_params = SamplingParams(
        max_tokens=args.max_new_tokens,
        **SAMPLING,
    )

    print(f"Generating {len(prompts)} responses (max_new_tokens={args.max_new_tokens})...")
    t0 = time.perf_counter()
    outputs = llm.generate(prompts, sampling_params=sampling_params)
    runtime = time.perf_counter() - t0

    # vLLM does not guarantee output order matches input order — match by request_id index.
    # `llm.generate` returns outputs in the same order as the input prompts list.
    judger = Judger(strict_extract=False)

    rows = []
    for item, out in zip(items, outputs):
        completion = out.outputs[0]
        response = completion.text
        gen_tokens = len(completion.token_ids)
        hit_cap = gen_tokens >= args.max_new_tokens
        boxed = has_boxed(response)

        is_mcq = isinstance(item.get("options"), list) and len(item["options"]) > 0
        gold = item["answer"]

        if is_mcq:
            correct = score_mcq(response, str(gold))
            gold_field = gold
        else:
            gold_list = gold if isinstance(gold, list) else [gold]
            try:
                correct = judger.auto_judge(
                    pred=response,
                    gold=gold_list,
                    options=[[]] * len(gold_list),
                )
            except Exception:
                correct = False
            gold_field = gold_list

        rows.append({
            "run_id": args.run_id,
            "id": item.get("id"),
            "is_mcq": is_mcq,
            "question": item["question"],
            "options": item.get("options"),
            "gold": gold_field,
            "response": response,
            "correct": bool(correct),
            "gen_tokens": gen_tokens,
            "hit_token_cap": hit_cap,
            "has_boxed_answer": boxed,
            "method": METHOD,
            "prompt_version": PROMPT_VERSION,
            "model": MODEL_ID,
            "max_new_tokens": args.max_new_tokens,
            **SAMPLING,
        })

    with open(out_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    n = len(rows)
    n_mcq = sum(1 for r in rows if r["is_mcq"])
    n_free = n - n_mcq
    n_correct = sum(1 for r in rows if r["correct"])
    n_mcq_correct = sum(1 for r in rows if r["is_mcq"] and r["correct"])
    n_free_correct = sum(1 for r in rows if (not r["is_mcq"]) and r["correct"])
    cutoffs = sum(1 for r in rows if r["hit_token_cap"])
    cutoffs_mcq = sum(1 for r in rows if r["is_mcq"] and r["hit_token_cap"])
    cutoffs_free = sum(1 for r in rows if (not r["is_mcq"]) and r["hit_token_cap"])
    missing_boxed = sum(1 for r in rows if not r["has_boxed_answer"])
    missing_boxed_mcq = sum(1 for r in rows if r["is_mcq"] and not r["has_boxed_answer"])
    missing_boxed_free = sum(1 for r in rows if (not r["is_mcq"]) and not r["has_boxed_answer"])
    tokens = [r["gen_tokens"] for r in rows]
    total_tokens = sum(tokens)
    avg_tokens = total_tokens / max(n, 1)

    def safe_div(num, den):
        return (num / den) if den else None

    def pct_at(values: list[int], p: int) -> Optional[int]:
        # Nearest-rank percentile, matching the notebook's _pct() so numbers
        # stay comparable to Run 03's recorded p50/p95/max.
        if not values:
            return None
        s = sorted(values)
        return s[min(int(len(s) * p / 100), len(s) - 1)]

    gpu_name = (
        torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    )

    finished_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    summary = {
        "run_id": args.run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "model": MODEL_ID,
        "method": METHOD,
        "prompt_version": PROMPT_VERSION,
        "vllm_version": vllm.__version__,
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "torch_cuda_version": torch.version.cuda,
        "gpu_name": gpu_name,
        "dtype": DTYPE,
        "quantization": QUANTIZATION,
        "gpu_memory_utilization": GPU_MEMORY_UTILIZATION,
        "vllm_use_v1": VLLM_USE_V1,
        "data_path": args.data_path,
        "data_start": args.data_start,
        "data_end": args.data_end,
        "n": n,
        "n_mcq": n_mcq,
        "n_free": n_free,
        "max_new_tokens": args.max_new_tokens,
        "max_model_len": args.max_model_len,
        **SAMPLING,
        "overall_correct": n_correct,
        "overall_accuracy": safe_div(n_correct, n),
        "mcq_correct": n_mcq_correct,
        "mcq_accuracy": safe_div(n_mcq_correct, n_mcq),
        "free_correct": n_free_correct,
        "free_accuracy": safe_div(n_free_correct, n_free),
        "runtime_seconds": runtime,
        "seconds_per_question": safe_div(runtime, n),
        "avg_gen_tokens": avg_tokens,
        "total_gen_tokens": total_tokens,
        "gen_tokens_min": min(tokens) if tokens else None,
        "gen_tokens_p50": pct_at(tokens, 50),
        "gen_tokens_p95": pct_at(tokens, 95),
        "gen_tokens_max": max(tokens) if tokens else None,
        "cutoffs": cutoffs,
        "cutoffs_mcq": cutoffs_mcq,
        "cutoffs_free": cutoffs_free,
        "missing_boxed": missing_boxed,
        "missing_boxed_mcq": missing_boxed_mcq,
        "missing_boxed_free": missing_boxed_free,
        "output_file": str(out_path),
    }

    if out_path.suffix == ".jsonl":
        summary_path = out_path.with_suffix(".summary.json")
    else:
        summary_path = out_path.with_name(out_path.name + ".summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    def pct(num, den):
        return f"{(num / den * 100):.1f}%" if den else "n/a"

    print("\n" + "─" * 60)
    print(f"Run ID            : {args.run_id}")
    print(f"Output            : {out_path}")
    print(f"Summary           : {summary_path}")
    print(f"Questions         : {n}  (mcq={n_mcq}, free={n_free})")
    print(f"Overall accuracy  : {pct(n_correct, n)}  ({n_correct}/{n})")
    print(f"MCQ accuracy      : {pct(n_mcq_correct, n_mcq)}  ({n_mcq_correct}/{n_mcq})")
    print(f"Free accuracy     : {pct(n_free_correct, n_free)}  ({n_free_correct}/{n_free})")
    print(f"Runtime           : {runtime:.1f} s  ({runtime / max(n, 1):.1f} s/q)")
    print(f"Avg gen tokens    : {avg_tokens:.0f}  (cap={args.max_new_tokens})")
    print(f"Cutoffs (hit cap) : {cutoffs}/{n}")
    print(f"Missing \\boxed{{}} : {missing_boxed}/{n}")
    print("─" * 60)


if __name__ == "__main__":
    main()

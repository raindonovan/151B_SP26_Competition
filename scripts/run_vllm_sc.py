"""Self-consistency runner: N samples per prompt, majority vote.

Builds on scripts/run_vllm_experiment.py — imports PROMPTS, SAMPLING,
prompt building, slice loading, and scoring helpers from there to keep
the prompt registry and extraction paths as a single source of truth.

Differences from the deterministic runner:
- SamplingParams(n=N, ...) — vLLM batches the N samples per prompt natively.
- Vote on the EXTRACTED ANSWER STRING per sample, take majority.
  - Empty extractions (no \\boxed{} found) excluded from the voting pool.
  - Tie-break: lexicographically smallest. Deterministic.
  - Two mathematically-equivalent forms vote SEPARATELY. Run 06 id=48
    is the canonical example: gold I = (4/3)ln3 and E = (2/3)ln9 are
    identical math but distinct strings — they would not combine even
    if 5 samples produce I and 3 produce E. Symbolic-equivalence-aware
    voting would require running sympy inside the vote loop (~9x cost
    per item) AND would change scoring semantics mid-sweep. Out of scope.
- Score voted_answer once via the existing single-sample path:
  wrap in \\boxed{...} and pass through score_mcq / Judger.auto_judge.
  Per-sample correctness is NOT computed — would burn ~9 sympy parses
  per sample on free-form, multiplying cost by N.
"""

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from tqdm import tqdm

# Must be set before `import vllm` — required by current pod setup.
os.environ["VLLM_USE_V1"] = "0"

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import torch  # noqa: E402
import transformers  # noqa: E402
import vllm  # noqa: E402
from judger import Judger  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402
from vllm import LLM, SamplingParams  # noqa: E402

# Re-use everything stable from the deterministic runner so the prompt
# registry and extraction paths can never drift between runners.
from run_vllm_experiment import (  # noqa: E402
    PROMPTS,
    SAMPLING,
    DTYPE,
    QUANTIZATION,
    GPU_MEMORY_UTILIZATION,
    VLLM_USE_V1,
    MODEL_ID,
    build_prompt,
    extract_letter,
    score_mcq,
    load_data,
    load_slice,
    load_data_by_ids,
)
from variants import resolve_variant  # noqa: E402

METHOD = "vllm-sc"


def extract_for_voting(text: str, is_mcq: bool, judger: Judger) -> str:
    """Extract the answer string for majority voting.

    Matches the extraction path the deterministic runner uses to score
    a single response, so SC results are comparable to single-sample
    runs item-by-item.

    Returns "" if no answer can be extracted; "" is excluded from the
    voting pool in vote().
    """
    if is_mcq:
        return extract_letter(text)
    return judger.extract_ans(text) or ""


def vote(extracted: list[str]) -> tuple[str, int, bool]:
    """Majority-vote among extracted answer strings.

    Empty extractions are excluded from the voting pool. Tie-break is
    lexicographically smallest (deterministic).

    Returns (winning_answer, vote_count, tie_broken):
      - winning_answer: "" if all extractions were empty
      - vote_count:     0 if all empty, else max count among non-empty
      - tie_broken:     True iff multiple candidates tied for max
    """
    candidates = [a for a in extracted if a]
    if not candidates:
        return "", 0, False
    counts = Counter(candidates)
    max_count = max(counts.values())
    winners = sorted(a for a, c in counts.items() if c == max_count)
    return winners[0], max_count, len(winners) > 1


def count_top_level_boxes(text: str) -> int:
    """Count \\boxed{} occurrences not nested inside another \\boxed{}."""
    count = 0
    depth = 0
    i = 0
    while i < len(text):
        if text[i : i + 7] == "\\boxed{":
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


def apply_shape_filter(samples: list[dict], is_multi_answer: bool) -> bool:
    """Tag each sample dict with shape_rejected in-place. Returns fallback_used.

    Rejects a sample if:
    - it has 0 top-level \\boxed{} (no answer extracted)
    - it has >1 top-level \\boxed{} on a multi-answer question (per-slot format)

    If every sample is rejected, clears all flags (fallback to unfiltered) and
    returns True. Caller uses shape_rejected=False samples for voting.
    """
    for s in samples:
        n_boxes = count_top_level_boxes(s["response"])
        s["shape_rejected"] = n_boxes == 0 or (is_multi_answer and n_boxes > 1)

    if all(s["shape_rejected"] for s in samples):
        for s in samples:
            s["shape_rejected"] = False
        return True  # fallback: vote on unfiltered set
    return False


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", required=True)
    p.add_argument(
        "--variant",
        default=None,
        help=(
            "Variant name from scripts/variants.py (e.g. V0_baseline). "
            "When set, overrides --prompt-version, --n-samples, --max-new-tokens, "
            "and all sampling params with values from resolve_variant(name)."
        ),
    )
    p.add_argument(
        "--prompt-version",
        default="v1-baseline",
        choices=list(PROMPTS.keys()),
        help="Which prompt policy from the PROMPTS registry to use.",
    )
    p.add_argument(
        "--slice",
        default=None,
        help="Path to a slice JSON. Mutually exclusive with --data-end.",
    )
    p.add_argument("--data-start", type=int, default=0)
    p.add_argument("--data-end", type=int, default=None)
    p.add_argument(
        "--max-new-tokens",
        type=int,
        default=None,  # None → use variant value if --variant set, else 32768
        help="Max tokens per sample. When --variant is set, variant value is used unless this flag is explicitly provided.",
    )
    p.add_argument("--output", required=True)
    # §7.1: max_model_len = max_new_tokens + 4096 headroom (32768 + 4096 = 36864)
    p.add_argument("--max-model-len", type=int, default=36864)
    p.add_argument("--data-path", default=str(REPO_ROOT / "data" / "public.jsonl"))
    p.add_argument(
        "--n-samples",
        type=int,
        default=8,
        help="Number of samples per question for self-consistency vote. Overridden by --variant.",
    )
    args = p.parse_args()
    if args.slice is not None and args.data_end is not None:
        p.error("--slice and --data-end are mutually exclusive")
    if args.slice is None and args.data_end is None:
        p.error("either --slice or --data-end must be provided")
    if args.n_samples < 1:
        p.error("--n-samples must be >= 1")
    return args


def percentile(values: list[float], p: int) -> Optional[float]:
    """Nearest-rank percentile."""
    if not values:
        return None
    s = sorted(values)
    return s[min(int(len(s) * p / 100), len(s) - 1)]


def _write_summary_from_file(
    out_path: Path,
    args,
    slice_info,
    slice_id_value,
    slice_path_value,
    variant_name,
    sp_kwargs: dict,
    started_at: str,
    runtime_new_questions: float = 0.0,
) -> None:
    """Load all rows from out_path and write the .summary.json file.

    Called both at normal completion and when all questions were already done
    (resume with nothing left to generate). runtime_new_questions covers only
    the generation time for this session; prior sessions' time is not tracked.
    """
    rows = []
    with open(out_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass

    policy = PROMPTS[args.prompt_version]

    n = len(rows)
    n_mcq = sum(1 for r in rows if r["is_mcq"])
    n_free = n - n_mcq
    n_correct = sum(1 for r in rows if r["correct"])
    n_mcq_correct = sum(1 for r in rows if r["is_mcq"] and r["correct"])
    n_free_correct = sum(1 for r in rows if (not r["is_mcq"]) and r["correct"])
    agreement_rates = [r["agreement_rate"] for r in rows]
    n_unanimous = sum(1 for r in rows if r["agreement_rate"] == 1.0)
    n_tie_broken = sum(1 for r in rows if r["tie_broken"])
    n_voted_changed_call = sum(1 for r in rows if r["voted_diff_from_sample1"])

    all_tokens = [s["gen_tokens"] for r in rows for s in r["samples"]]
    cutoffs_per_sample = sum(
        1 for r in rows for s in r["samples"] if s["hit_token_cap"]
    )

    def safe_div(num, den):
        return (num / den) if den else None

    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    finished_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    summary = {
        "run_id": args.run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "model": MODEL_ID,
        "method": METHOD,
        "prompt_version": args.prompt_version,
        "system_prompt_mcq": policy["mcq"],
        "system_prompt_free": policy["free"],
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
        "slice_id": slice_id_value,
        "slice_path": slice_path_value,
        "slice_n": len(slice_info["ids"]) if slice_info else None,
        "variant": variant_name,
        "n": n,
        "n_mcq": n_mcq,
        "n_free": n_free,
        "n_samples": args.n_samples,
        "max_new_tokens": args.max_new_tokens,
        "max_model_len": args.max_model_len,
        **sp_kwargs,
        "overall_correct": n_correct,
        "overall_accuracy": safe_div(n_correct, n),
        "mcq_correct": n_mcq_correct,
        "mcq_accuracy": safe_div(n_mcq_correct, n_mcq),
        "free_correct": n_free_correct,
        "free_accuracy": safe_div(n_free_correct, n_free),
        "runtime_seconds": runtime_new_questions,
        "seconds_per_question": safe_div(runtime_new_questions, n),
        "agreement_rate_p25": percentile(agreement_rates, 25),
        "agreement_rate_p50": percentile(agreement_rates, 50),
        "agreement_rate_p75": percentile(agreement_rates, 75),
        "n_unanimous": n_unanimous,
        "n_tie_broken": n_tie_broken,
        "n_voted_changed_call": n_voted_changed_call,
        "total_gen_tokens_all_samples": sum(all_tokens),
        "avg_gen_tokens_per_sample": safe_div(sum(all_tokens), len(all_tokens)),
        "cutoffs_per_sample": cutoffs_per_sample,
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
    if slice_info:
        print(f"Slice             : {slice_info['slice_id']}  ({args.slice})")
    print(f"Prompt            : {args.prompt_version}")
    print(f"N samples         : {args.n_samples}")
    print(f"Output            : {out_path}")
    print(f"Summary           : {summary_path}")
    print(f"Questions         : {n}  (mcq={n_mcq}, free={n_free})")
    print(f"Overall accuracy  : {pct(n_correct, n)}  ({n_correct}/{n})")
    print(f"MCQ accuracy      : {pct(n_mcq_correct, n_mcq)}  ({n_mcq_correct}/{n_mcq})")
    print(f"Free accuracy     : {pct(n_free_correct, n_free)}  ({n_free_correct}/{n_free})")
    if runtime_new_questions > 0:
        print(f"Runtime (session) : {runtime_new_questions:.1f} s")
    print(f"Unanimous         : {n_unanimous}/{n}")
    print(f"Tie-broken        : {n_tie_broken}/{n}")
    print(f"Vote != sample 1  : {n_voted_changed_call}/{n}  (how often SC changed the call)")
    if all(v is not None for v in (
        summary["agreement_rate_p25"],
        summary["agreement_rate_p50"],
        summary["agreement_rate_p75"],
    )):
        print(
            f"Agreement-rate p25/50/75 : "
            f"{summary['agreement_rate_p25']:.3f} / "
            f"{summary['agreement_rate_p50']:.3f} / "
            f"{summary['agreement_rate_p75']:.3f}"
        )
    print("─" * 60)


def main() -> None:
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    args = parse_args()

    # --- Variant config resolution ---
    variant_name = args.variant
    if variant_name is not None:
        vcfg = resolve_variant(variant_name)
        args.prompt_version = vcfg["prompt_version"]
        args.n_samples = vcfg["n_samples"]
        # Explicit --max-new-tokens on CLI wins over variant; None means use variant.
        if args.max_new_tokens is None:
            args.max_new_tokens = vcfg["max_new_tokens"]
        sp_kwargs = {
            "temperature": vcfg["temperature"],
            "top_p": vcfg["top_p"],
            "top_k": vcfg["top_k"],
            "min_p": vcfg["min_p"],
            "presence_penalty": vcfg["presence_penalty"],
            "repetition_penalty": vcfg["repetition_penalty"],
        }
        shape_filter_enabled = vcfg.get("shape_filter", False)
        temperature_ladder = vcfg.get("temperature_ladder", None)
        print(f"Variant '{variant_name}' applied: {vcfg}")
    else:
        if args.max_new_tokens is None:
            args.max_new_tokens = 32768
        sp_kwargs = {**SAMPLING, "presence_penalty": 1.0}
        shape_filter_enabled = False
        temperature_ladder = None

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # --- Resume: read already-completed question IDs from existing output ---
    completed_ids: set = set()
    if out_path.exists():
        with open(out_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        completed_ids.add(json.loads(line)["id"])
                    except Exception:
                        pass
        print(f"Resume: {len(completed_ids)} completed questions found in {out_path}")

    if args.slice:
        slice_info = load_slice(args.slice)
        items = load_data_by_ids(args.data_path, slice_info["ids"])
        print(
            f"Loaded {len(items)} questions from slice "
            f"{slice_info.get('slice_id')!r} ({args.slice}) over {args.data_path}"
        )
    else:
        slice_info = None
        items = load_data(args.data_path, args.data_start, args.data_end)
        print(
            f"Loaded {len(items)} questions [{args.data_start}:{args.data_end}] "
            f"from {args.data_path}"
        )

    slice_id_value = slice_info["slice_id"] if slice_info else None
    slice_path_value = str(args.slice) if args.slice else None
    policy = PROMPTS[args.prompt_version]

    # Filter to only questions not yet completed
    items_todo = [item for item in items if item.get("id") not in completed_ids]
    n_skipped = len(items) - len(items_todo)
    if n_skipped:
        print(f"Skipping {n_skipped} already-completed; {len(items_todo)} remaining")
    if not items_todo:
        print("All questions already completed — writing summary and exiting.")
        _write_summary_from_file(
            out_path, args, slice_info, slice_id_value, slice_path_value,
            variant_name, sp_kwargs, started_at,
        )
        return

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)

    # Build prompts for remaining items only
    prompts_todo = []
    for item in items_todo:
        system, user = build_prompt(item["question"], item.get("options"), policy)
        prompt_text = tokenizer.apply_chat_template(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            tokenize=False,
            add_generation_prompt=True,
        )
        prompts_todo.append(prompt_text)

    # §7.1: enable_prefix_caching, reasoning_parser=deepseek_r1 (vLLM Issue #22507)
    llm = LLM(
        model=MODEL_ID,
        dtype=DTYPE,
        trust_remote_code=True,
        gpu_memory_utilization=GPU_MEMORY_UTILIZATION,
        max_model_len=args.max_model_len,
        enable_prefix_caching=True,
        reasoning_parser="deepseek_r1",
    )

    if temperature_ladder is None:
        sampling_params = SamplingParams(
            n=args.n_samples,
            max_tokens=args.max_new_tokens,
            **sp_kwargs,
        )

    if temperature_ladder is not None:
        print(
            f"Generating {args.n_samples} samples × {len(items_todo)} prompts "
            f"(ladder={temperature_ladder}, {len(temperature_ladder)} generate() calls per question)..."
        )
    else:
        print(
            f"Generating {args.n_samples} samples × {len(items_todo)} prompts "
            f"(max_new_tokens={args.max_new_tokens}, one generate() call per question)..."
        )

    judger = Judger(strict_extract=False)
    t0 = time.perf_counter()

    # Open in append mode so resumed runs add to existing rows.
    with open(out_path, "a") as out_f:
        pbar = tqdm(
            zip(items_todo, prompts_todo),
            total=len(items_todo),
            initial=0,
            desc=f"{variant_name or args.run_id}",
            unit="q",
            dynamic_ncols=True,
            file=sys.stdout,
        )
        for i, (item, prompt) in enumerate(pbar):
            q_t0 = time.perf_counter()

            is_mcq = isinstance(item.get("options"), list) and len(item["options"]) > 0
            gold = item["answer"]

            # --- Generate samples (single-temp or ladder) ---
            if temperature_ladder is not None:
                n_per_rung = args.n_samples // len(temperature_ladder)
                remainder = args.n_samples % len(temperature_ladder)
                all_completions = []
                for rung_i, temp in enumerate(temperature_ladder):
                    n_this = n_per_rung + (1 if rung_i < remainder else 0)
                    if n_this == 0:
                        continue
                    rung_params = SamplingParams(
                        n=n_this,
                        max_tokens=args.max_new_tokens,
                        **{**sp_kwargs, "temperature": temp},
                    )
                    rung_out = llm.generate([prompt], sampling_params=rung_params)
                    all_completions.extend(rung_out[0].outputs)
                completions = all_completions
            else:
                outputs = llm.generate([prompt], sampling_params=sampling_params)
                completions = outputs[0].outputs

            q_elapsed = time.perf_counter() - q_t0

            samples = []
            for completion in completions:
                response = completion.text
                extracted = extract_for_voting(response, is_mcq, judger)
                samples.append({
                    "response": response,
                    "gen_tokens": len(completion.token_ids),
                    "hit_token_cap": len(completion.token_ids) >= args.max_new_tokens,
                    "extracted_answer": extracted,
                    "shape_rejected": False,
                })

            # --- Shape filter (V3+) ---
            shape_fallback = False
            if shape_filter_enabled:
                is_multi_answer = isinstance(gold, list) and len(gold) > 1
                shape_fallback = apply_shape_filter(samples, is_multi_answer)
                vote_inputs = [s["extracted_answer"] for s in samples if not s["shape_rejected"]]
            else:
                vote_inputs = [s["extracted_answer"] for s in samples]

            voted_answer, vote_count, tie_broken = vote(vote_inputs)
            agreement_rate = vote_count / args.n_samples
            sample1_answer = samples[0]["extracted_answer"] if samples else ""
            voted_diff_from_sample1 = voted_answer != sample1_answer

            if voted_answer:
                voted_response = f"\\boxed{{{voted_answer}}}"
                if is_mcq:
                    correct = score_mcq(voted_response, str(gold))
                    gold_field = gold
                else:
                    gold_list = gold if isinstance(gold, list) else [gold]
                    try:
                        correct = judger.auto_judge(
                            pred=voted_response,
                            gold=gold_list,
                            options=[[]] * len(gold_list),
                        )
                    except Exception:
                        correct = False
                    gold_field = gold_list
            else:
                correct = False
                gold_field = gold if is_mcq else (
                    gold if isinstance(gold, list) else [gold]
                )

            row = {
                "run_id": args.run_id,
                "id": item.get("id"),
                "is_mcq": is_mcq,
                "question": item["question"],
                "options": item.get("options"),
                "gold": gold_field,
                "samples": samples,
                "voted_answer": voted_answer,
                "agreement_rate": agreement_rate,
                "tie_broken": tie_broken,
                "voted_diff_from_sample1": voted_diff_from_sample1,
                "shape_filter_fallback": shape_fallback,
                "correct": bool(correct),
                "method": METHOD,
                "prompt_version": args.prompt_version,
                "variant": variant_name,
                "model": MODEL_ID,
                "max_new_tokens": args.max_new_tokens,
                "n_samples": args.n_samples,
                "slice_id": slice_id_value,
                "slice_path": slice_path_value,
                **sp_kwargs,
            }
            out_f.write(json.dumps(row, ensure_ascii=False) + "\n")
            out_f.flush()

            n_done = n_skipped + i + 1
            n_total = len(items)
            pbar.set_postfix(
                id=item.get("id"),
                ok=bool(correct),
                agree=f"{agreement_rate:.2f}",
                voted=voted_answer[:12] if voted_answer else "",
                s=f"{q_elapsed:.0f}",
                refresh=True,
            )
            print(
                f"  [{n_done}/{n_total}] id={item.get('id')}  "
                f"correct={bool(correct)}  agree={agreement_rate:.2f}  "
                f"voted={voted_answer!r}  {q_elapsed:.0f}s",
                flush=True,
            )

    runtime = time.perf_counter() - t0

    _write_summary_from_file(
        out_path, args, slice_info, slice_id_value, slice_path_value,
        variant_name, sp_kwargs, started_at, runtime_new_questions=runtime,
    )


if __name__ == "__main__":
    main()

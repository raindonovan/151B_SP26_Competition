"""No-box rescue (Track A, post-A2): forced-answer base inference on items
that run10 emitted no \\boxed{} for AND that slot1_reformat could not
recover downstream.

Per claude_strategy spec (memory #5 + Day-2 plan):
- Base model Qwen3-4B-Thinking-2507, no adapter.
- SC=4, T=0.6 / top_p=0.95 / top_k=20 / repetition_penalty=1.0.
- max_new_tokens=81920, thinking_budget=65536 (hardest-item defaults).
- Forced-answer suffix on each user prompt to push a \\boxed{}.

Output:
  results/no_box_rescue_<TS>.jsonl       full audit JSONL (one row per item;
                                          per-sample texts + extracted boxes
                                          preserved verbatim)
  results/no_box_rescue.candidates.csv   id, voted_answer, n_votes,
                                          n_samples_with_box, teacher_agreement,
                                          current_value_in_slot1_reformat

Vote: majority on per-sample extracted box (post-normalize).
Tie-break: prefer answer matching any teacher in
results/unified_answer_sheet.csv (best_answer column); else first
extraction by sample index.

Does NOT splice into any submission.
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

# Must precede vllm import so the in-tree V1 engine is disabled (matches
# every other inference script we run on this box).
os.environ.setdefault("VLLM_USE_V1", "0")
os.environ.setdefault("HF_HOME", os.path.expanduser("~/hf_cache"))

REPO_ROOT = Path(__file__).resolve().parent.parent

SYSTEM_PROMPT = "Please reason step by step and put your final answer within \\boxed{}."
FORCED_SUFFIX = (
    "\n\nProvide your final answer in the form \\boxed{your answer}. "
    "Do not write any text after the boxed answer."
)


# ── Inline balanced-brace boxed extractor (per claude_strategy spec d) ───────
def extract_boxed_all(text: str) -> list[str]:
    """Return contents of every top-level \\boxed{...} in `text`, in order.

    Handles nested braces inside the boxed content (e.g. \\boxed{\\frac{a}{b}}).
    Skips a \\boxed{ whose content is unterminated.
    """
    out = []
    i = 0
    while True:
        pos = text.find("\\boxed{", i)
        if pos == -1:
            break
        start = pos + len("\\boxed{")
        depth = 1
        j = start
        while j < len(text):
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    out.append(text[start:j])
                    break
            j += 1
        # advance i past this \\boxed{ so we find the next one
        i = j + 1 if depth == 0 else pos + 1
    return out


def extract_last_boxed(text: str) -> str:
    """Last top-level \\boxed{...} content, or empty string."""
    boxes = extract_boxed_all(text)
    return boxes[-1].strip() if boxes else ""


# ── Light normalization (matches scripts/run_hybrid_inference.py) ────────────
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


def smoke_test_extractor() -> None:
    """Three known cases per claude_strategy spec (d)."""
    cases = [
        # single box
        ("The answer is \\boxed{42}.", ["42"]),
        # multi-box with nested fractions
        (
            "First box: \\boxed{\\frac{1}{2}}. Then: \\boxed{\\frac{a+b}{\\frac{c}{d}}}.",
            ["\\frac{1}{2}", "\\frac{a+b}{\\frac{c}{d}}"],
        ),
        # embedded parens (no braces but content includes them)
        (
            "Hence \\boxed{(x+1)(x-1)} and earlier \\boxed{\\sin(\\theta)}.",
            ["(x+1)(x-1)", "\\sin(\\theta)"],
        ),
    ]
    for i, (text, expected) in enumerate(cases, 1):
        got = extract_boxed_all(text)
        ok = got == expected
        flag = "OK" if ok else "FAIL"
        print(f"  smoke {i} {flag}: expected={expected!r} got={got!r}")
        if not ok:
            raise SystemExit(f"extractor smoke test {i} failed")


# ── Data loading ─────────────────────────────────────────────────────────────
def load_private() -> dict[int, dict]:
    items = {}
    with open(REPO_ROOT / "private.jsonl") as f:
        for line in f:
            d = json.loads(line)
            items[int(d["id"])] = d
    return items


def load_target_ids(path: Path) -> list[int]:
    ids = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if s:
                ids.append(int(s))
    return ids


def load_teacher_answers() -> dict[int, str]:
    """Best-answer per id from results/unified_answer_sheet.csv."""
    path = REPO_ROOT / "results" / "unified_answer_sheet.csv"
    out: dict[int, str] = {}
    if not path.exists():
        return out
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                iid = int(row["item_id"])
            except (KeyError, ValueError, TypeError):
                continue
            ans = (row.get("best_answer") or "").strip()
            if ans:
                out[iid] = ans
    return out


def load_slot1_reformat() -> dict[int, str]:
    """Current value in slot1_reformat for each rescue id (entire response cell)."""
    path = REPO_ROOT / "submissions" / "slot1_reformat.csv"
    out: dict[int, str] = {}
    if not path.exists():
        return out
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                iid = int(row["id"])
            except (KeyError, ValueError, TypeError):
                continue
            out[iid] = (row.get("response") or row.get("answer") or "").strip()
    return out


# ── Prompt builder ───────────────────────────────────────────────────────────
def build_user_msg(item: dict) -> str:
    """Match run_hybrid_inference's letters format for MCQs; append forced suffix."""
    q = item.get("question", "")
    opts = item.get("options") or []
    if opts:
        # Match the runner's 'letters' format
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        lines = [q, "", "Options:"]
        for letter, opt in zip(letters, opts):
            lines.append(f"{letter}. {opt}")
        user = "\n".join(lines)
    else:
        user = q
    return user + FORCED_SUFFIX


# ── Vote + tie-break ─────────────────────────────────────────────────────────
def vote(samples: list[dict], teacher_set: set[str]) -> tuple[str, int, int]:
    """Return (voted_answer_raw, n_votes_for_winner, n_samples_with_box).

    samples: list of {"text": str, "extracted": str} dicts (extracted = raw, pre-normalize)
    Returns the RAW form of the winning answer (matching its highest-vote bucket's first entry).
    """
    # Bucket by normalized answer
    buckets: dict[str, list[tuple[int, str]]] = {}  # norm -> [(sample_idx, raw), ...]
    for i, s in enumerate(samples):
        raw = s.get("extracted") or ""
        if not raw:
            continue
        norm = normalize_answer(raw)
        if not norm:
            continue
        buckets.setdefault(norm, []).append((i, raw))

    n_with_box = sum(1 for s in samples if (s.get("extracted") or "").strip())
    if not buckets:
        return "", 0, n_with_box

    # Find max vote count
    max_count = max(len(v) for v in buckets.values())
    candidates = [norm for norm, v in buckets.items() if len(v) == max_count]

    if len(candidates) == 1:
        winner_norm = candidates[0]
    else:
        # Tie-break: prefer any candidate that matches a teacher answer
        teacher_match = [c for c in candidates if c in teacher_set]
        if teacher_match:
            winner_norm = teacher_match[0]
        else:
            # else: prefer the candidate whose first-occurring sample_idx is smallest
            winner_norm = min(candidates, key=lambda c: buckets[c][0][0])

    # Return RAW form of the winner's first-occurring sample
    raw_winner = buckets[winner_norm][0][1]
    return raw_winner, max_count, n_with_box


# ── Main ─────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--target-ids", default="data/no_box_rescue_targets.txt")
    p.add_argument("--model", default="Qwen/Qwen3-4B-Thinking-2507")
    p.add_argument("--tensor-parallel-size", type=int, default=2)
    p.add_argument("--sc", type=int, default=4)
    p.add_argument("--max-tokens", type=int, default=81920)
    p.add_argument("--thinking-budget", type=int, default=65536)
    p.add_argument("--temperature", type=float, default=0.6)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--top-k", type=int, default=20)
    p.add_argument("--repetition-penalty", type=float, default=1.0)
    p.add_argument("--gpu-util", type=float, default=0.85)
    p.add_argument("--output-jsonl", default=None,
                   help="Default: results/no_box_rescue_<TS>.jsonl")
    p.add_argument("--candidates-csv", default="results/no_box_rescue.candidates.csv")
    p.add_argument("--smoke-only", action="store_true",
                   help="Run extractor smoke tests then exit without launching vLLM")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 70)
    print(" no-box rescue v1")
    print("=" * 70)
    print("[step 1] smoke-testing inline boxed extractor")
    smoke_test_extractor()
    print("  extractor OK")
    if args.smoke_only:
        return

    # Inputs
    ids = load_target_ids(Path(args.target_ids))
    print(f"[step 2] loaded {len(ids)} rescue targets from {args.target_ids}")
    items = load_private()
    teacher_map = load_teacher_answers()
    teacher_set_norm = {normalize_answer(v) for v in teacher_map.values() if v}
    print(f"  teacher answer sheet: {len(teacher_map)} ids, "
          f"{len(teacher_set_norm)} normalized unique")
    slot1 = load_slot1_reformat()
    print(f"  slot1_reformat: {len(slot1)} ids loaded")

    # Build prompts (later applied via the tokenizer's chat template)
    prompts: list[tuple[int, list[dict]]] = []
    for iid in ids:
        item = items[iid]
        msgs = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": build_user_msg(item)},
        ]
        prompts.append((iid, msgs))

    # Output paths
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_jsonl = args.output_jsonl or f"results/no_box_rescue_{ts}.jsonl"
    out_jsonl_path = REPO_ROOT / out_jsonl
    out_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    cand_csv_path = REPO_ROOT / args.candidates_csv
    cand_csv_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[step 3] output_jsonl   = {out_jsonl_path}")
    print(f"         candidates_csv = {cand_csv_path}")

    # ── vLLM init ───────────────────────────────────────────────────────────
    print("[step 4] loading vLLM + model")
    from vllm import LLM, SamplingParams  # noqa: E402

    llm = LLM(
        model=args.model,
        tensor_parallel_size=args.tensor_parallel_size,
        gpu_memory_utilization=args.gpu_util,
        max_model_len=args.max_tokens + 4096,
        trust_remote_code=True,
        dtype="bfloat16",
        enable_prefix_caching=True,
        reasoning_parser="deepseek_r1",
    )
    tokenizer = llm.get_tokenizer()

    sampling = SamplingParams(
        n=args.sc,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        repetition_penalty=args.repetition_penalty,
        max_tokens=args.max_tokens,
    )
    if args.thinking_budget and args.thinking_budget > 0:
        # vLLM exposes thinking budget via extra kwargs on Qwen3-Thinking.
        # Setting reasoning_max_tokens in the SamplingParams via the deepseek_r1
        # reasoning parser is the documented path on 0.20.2.
        try:
            sampling.reasoning_max_tokens = args.thinking_budget
        except Exception:
            print(f"  (warn) failed to set reasoning_max_tokens={args.thinking_budget}; ignoring")

    # ── Inference ──────────────────────────────────────────────────────────
    print(f"[step 5] generating SC={args.sc} for {len(prompts)} items "
          f"(max_tokens={args.max_tokens}, thinking_budget={args.thinking_budget})")
    rendered_prompts = []
    for iid, msgs in prompts:
        rendered = tokenizer.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=True,
        )
        rendered_prompts.append((iid, rendered))

    audit_rows: list[dict] = []
    candidate_rows: list[dict] = []

    with open(out_jsonl_path, "w") as out_f:
        for idx, (iid, prompt) in enumerate(rendered_prompts, 1):
            t0 = time.time()
            outputs = llm.generate([prompt], sampling, use_tqdm=False)
            wall = time.time() - t0
            assert len(outputs) == 1, f"expected 1 RequestOutput, got {len(outputs)}"
            req = outputs[0]

            samples = []
            for s_idx, comp in enumerate(req.outputs):
                text = comp.text
                extracted = extract_last_boxed(text)
                samples.append({
                    "sample_idx": s_idx,
                    "finish_reason": comp.finish_reason,
                    "gen_tokens": len(comp.token_ids),
                    "text": text,
                    "extracted": extracted,
                })

            voted_raw, n_votes, n_with_box = vote(samples, teacher_set_norm)
            voted_norm = normalize_answer(voted_raw)
            t_match = voted_norm in teacher_set_norm if voted_norm else False
            teacher_agreement = "TRUE" if t_match else ("FALSE" if voted_norm else "NONE")
            slot1_cell = slot1.get(iid, "")

            audit = {
                "id": iid,
                "voted_answer": voted_raw,
                "voted_normalized": voted_norm,
                "n_votes": n_votes,
                "n_samples_with_box": n_with_box,
                "n_samples_total": len(samples),
                "teacher_agreement": teacher_agreement,
                "wall_seconds": round(wall, 1),
                "samples": samples,
            }
            audit_rows.append(audit)
            out_f.write(json.dumps(audit, ensure_ascii=False) + "\n")
            out_f.flush()

            candidate_rows.append({
                "id": iid,
                "voted_answer": voted_raw,
                "n_votes": n_votes,
                "n_samples_with_box": n_with_box,
                "teacher_agreement": teacher_agreement,
                "current_value_in_slot1_reformat": slot1_cell,
            })

            print(f"  [{idx:>2}/{len(prompts)}] id={iid:>4} "
                  f"voted={voted_raw[:30]!r} votes={n_votes}/{args.sc} "
                  f"box={n_with_box}/{args.sc} t={teacher_agreement} "
                  f"wall={wall:.1f}s", flush=True)

    # ── Candidates CSV ─────────────────────────────────────────────────────
    with open(cand_csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id", "voted_answer", "n_votes", "n_samples_with_box",
                "teacher_agreement", "current_value_in_slot1_reformat",
            ],
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        writer.writerows(candidate_rows)

    # ── Validation summary ─────────────────────────────────────────────────
    n = len(audit_rows)
    rescued = sum(1 for r in audit_rows if r["voted_answer"])
    uncoverable = sum(1 for r in audit_rows if r["n_samples_with_box"] == 0)
    split = sum(1 for r in audit_rows
                if r["voted_answer"] and r["n_votes"] < (args.sc // 2 + 1))
    teacher_agree = sum(1 for r in audit_rows if r["teacher_agreement"] == "TRUE")

    print("")
    print("=" * 70)
    print(" SUMMARY")
    print("=" * 70)
    print(f"  inputs:    {n}")
    print(f"  outputs:   {len(candidate_rows)} (must match: {n == len(candidate_rows)})")
    print(f"  rescued (majority found): {rescued}/{n}")
    print(f"  split (no majority):       {n - rescued - uncoverable}/{n}")
    print(f"  uncoverable (0/SC boxed):  {uncoverable}/{n}")
    print(f"  teacher-agreeing:          {teacher_agree}/{n}")
    print("")
    print("  spot-checks (first 3):")
    for r in audit_rows[:3]:
        item = items[r["id"]]
        q = (item.get("question") or "")[:300].replace("\n", " ")
        print(f"  ─ id={r['id']} q={q!r}")
        for s in r["samples"]:
            print(f"    sample {s['sample_idx']} extracted={s['extracted'][:60]!r}")
        print(f"    voted={r['voted_answer'][:60]!r} votes={r['n_votes']}/{args.sc} "
              f"teacher={r['teacher_agreement']}")
    print("")
    print(f"audit JSONL: {out_jsonl_path}")
    print(f"candidates CSV: {cand_csv_path}")


if __name__ == "__main__":
    main()

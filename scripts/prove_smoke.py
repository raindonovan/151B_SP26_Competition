"""PROVE-style verification smoke test — 20-item expanded eval.

Three groups (20 items total):

  CALIBRATION_IDS (5, TRAINED): we have the gold label from the SFT v4
    dataset. PROVE's program output is compared to the KNOWN training
    answer. This calibrates whether the PROVE pipeline can produce a
    correct answer at all on items the model has seen.

  GOOD_IDS (10, UNTRAINED, numeric): the real PROVE evaluation. We get
    a majority vote with SC=8 then ask the model to write an independent
    Python program (the proposed answer is NOT shown). Program output is
    compared to the SC=8 majority answer. We ALSO print the unified
    answer-sheet best_answer for manual triangulation.

  EDGE_IDS (5, UNTRAINED, hard): symbolic, multi-answer, or MCQ items
    where PROVE is expected to fail gracefully. Outcomes are reported
    per item without a pass/fail count — these test robustness.

Run from repo root:
    python3 scripts/prove_smoke.py [model_path]

Default model path: sft_v4_epoch6_merged

SECURITY NOTE: this script EXECUTES model-generated Python with no sandbox.
Trust your model.
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from fractions import Fraction
from pathlib import Path

# Must be set before `import vllm`.
os.environ["VLLM_USE_V1"] = "0"

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import torch  # noqa: E402
import vllm  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402
from vllm import LLM, SamplingParams  # noqa: E402


CALIBRATION_IDS = [31, 39, 52, 59, 62]              # TRAINED, known labels
GOOD_IDS = [0, 6, 7, 8, 11, 16, 20, 24, 28, 30]    # UNTRAINED, numeric, PROVE targets
EDGE_IDS = [4, 9, 2, 5, 17]                         # UNTRAINED, hard / multi-answer / MCQ

SYSTEM = "Please reason step by step and put your final answer within \\boxed{}."
PROVE_SYSTEM = (
    "Write a Python program to solve the following math problem. "
    "The program must compute the answer from scratch using arithmetic, "
    "sympy, or numpy as needed. Print ONLY the final numerical answer "
    "(no labels, no extra text). If the problem cannot be solved "
    "computationally, print 'SKIP'."
)

# Engine config (mirrors scripts/run_vllm_sc.py)
DTYPE = "bfloat16"
GPU_MEMORY_UTILIZATION = 0.85
MAX_MODEL_LEN = 20480
PROG_TIMEOUT = 10


# ---- Boxed extraction ----

def extract_boxed(text):
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


# ---- Code extraction + execution ----

def extract_python(text):
    """Extract Python code block from model output."""
    m = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    if "print(" in text and ("import" in text or "=" in text):
        return text.strip()
    return None


def run_python(code, timeout=PROG_TIMEOUT):
    """Execute Python code, return (status, stdout_or_error)."""
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            tmpname = f.name
        try:
            result = subprocess.run(
                ["python3", tmpname],
                capture_output=True, text=True, timeout=timeout,
            )
        finally:
            os.unlink(tmpname)
        if result.returncode == 0:
            return ("ok", result.stdout.strip())
        return ("error", result.stderr.strip()[:300])
    except subprocess.TimeoutExpired:
        return ("timeout", f"exceeded {timeout}s")
    except Exception as e:
        return ("exception", str(e)[:300])


# ---- Answer comparison ----

_LATEX_FRAC = re.compile(r"\\d?frac\s*\{(-?[^{}]+)\}\s*\{(-?[^{}]+)\}")
_SIMPLE_FRAC = re.compile(r"^\s*(-?\d+)\s*/\s*(-?\d+)\s*$")


def to_number(s):
    if s is None:
        return None
    s = str(s).strip()
    s = s.replace("$", "").replace("\\,", "").replace("\\;", "").replace(",", "")
    m = _LATEX_FRAC.search(s)
    if m:
        try:
            num = float(m.group(1))
            den = float(m.group(2))
            if den != 0:
                return num / den
        except (ValueError, ZeroDivisionError):
            pass
    m = _SIMPLE_FRAC.match(s)
    if m:
        try:
            return float(m.group(1)) / float(m.group(2))
        except (ValueError, ZeroDivisionError):
            pass
    try:
        return float(s)
    except ValueError:
        return None


def answers_equal(expected, program_out, rtol=1e-3, atol=1e-4):
    e = (expected or "").strip()
    p = (program_out or "").strip()
    if not e or not p:
        return False
    if e == p:
        return True
    p_tail = p.split()[-1] if p.split() else p
    if e == p_tail:
        return True
    e_num = to_number(e)
    p_num = to_number(p_tail)
    if e_num is not None and p_num is not None:
        if abs(e_num - p_num) <= atol + rtol * max(abs(e_num), abs(p_num)):
            return True
    return False


# ---- Data loading ----

def load_training_answers():
    """Map item_id -> last \\boxed{} answer from the v4 training set."""
    answers = {}
    with open("data/sft_v4_dataset.jsonl") as f:
        for line in f:
            d = json.loads(line)
            iid = int(d["item_id"])
            trace = d["messages"][2]["content"]
            answers[iid] = extract_boxed(trace)
    return answers


def load_answer_sheet():
    """Map item_id -> best_answer from results/answer_sheet/unified_answer_sheet.csv."""
    sheet_path = REPO_ROOT / "results" / "answer_sheet" / "unified_answer_sheet.csv"
    sheet = {}
    if not sheet_path.exists():
        return sheet
    with open(sheet_path, newline="") as f:
        for row in csv.DictReader(f):
            try:
                iid = int(row["item_id"])
            except (KeyError, ValueError, TypeError):
                continue
            sheet[iid] = row.get("best_answer", "")
    return sheet


# ---- Main ----

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("model", nargs="?", default="sft_v4_epoch6_merged")
    p.add_argument("--max-model-len", type=int, default=MAX_MODEL_LEN)
    return p.parse_args()


def build_solve_prompt(item, tokenizer):
    q = item.get("question", "")
    opts = item.get("options", [])
    if opts:
        user = f"{q}\n\nOptions:\n" + "\n".join(opts)
    else:
        user = q
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
    return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def build_prove_prompt(item, tokenizer):
    msgs = [
        {"role": "system", "content": PROVE_SYSTEM},
        {"role": "user", "content": item.get("question", "")},
    ]
    return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def majority_vote(outputs):
    """outputs: list of vllm output objects with .outputs[].text
       Returns (winner, count, n_nonempty)."""
    answers = [extract_boxed(o.text) for o in outputs]
    non_empty = [a for a in answers if a]
    if not non_empty:
        return "", 0, 0
    vote = Counter(non_empty)
    winner, count = vote.most_common(1)[0]
    return winner, count, len(non_empty)


def main():
    args = parse_args()

    with open("private.jsonl") as f:
        items = {json.loads(l)["id"]: json.loads(l) for l in f}

    train_answers = load_training_answers()
    answer_sheet = load_answer_sheet()

    # Bucket validity checks
    for iid in CALIBRATION_IDS:
        if iid not in train_answers or not train_answers[iid]:
            print(f"WARNING: CALIBRATION item {iid} not in training data or has no boxed answer")
    for iid in GOOD_IDS + EDGE_IDS:
        if iid in train_answers:
            print(f"WARNING: {iid} is in training data but listed as untrained")

    all_ids = CALIBRATION_IDS + GOOD_IDS + EDGE_IDS
    print(f"\nGroups: CALIBRATION={CALIBRATION_IDS}  GOOD={GOOD_IDS}  EDGE={EDGE_IDS}")
    print(f"Total: {len(all_ids)} items")

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

    # ----- STEP 1: SC=8 solve on ALL items (used for majority vote on GOOD/EDGE)
    # CALIBRATION doesn't need a vote (we have the gold label) but generating it
    # is cheap and useful for sanity (does the model agree with its training?)
    print("\n" + "=" * 60)
    print("STEP 1: SC=8 @ T=0.6 (majority vote)")
    print("=" * 60)

    solve_prompts = [build_solve_prompt(items[iid], tokenizer) for iid in all_ids]
    solve_out = llm.generate(solve_prompts, SamplingParams(
        temperature=0.6, max_tokens=16384, top_p=0.95, n=8))

    majority = {}  # iid -> (winner, count, n_nonempty)
    for idx, iid in enumerate(all_ids):
        majority[iid] = majority_vote(solve_out[idx])
        w, c, n = majority[iid]
        print(f"  ID {iid:>3}: majority='{w[:60]}' votes={c}/{n}")

    # ----- STEP 2: Generate PROVE Python programs for ALL items (no proposed answer)
    print("\n" + "=" * 60)
    print("STEP 2: Generate PROVE programs (independent, no proposed answer)")
    print("=" * 60)

    prove_prompts = [build_prove_prompt(items[iid], tokenizer) for iid in all_ids]
    prove_out = llm.generate(prove_prompts, SamplingParams(
        temperature=0.0, max_tokens=4096))

    prove_responses = {iid: prove_out[idx].outputs[0].text
                       for idx, iid in enumerate(all_ids)}

    # ----- STEP 3: Execute and compare per group
    print("\n" + "=" * 60)
    print("STEP 3: Execute and evaluate")
    print("=" * 60)

    def evaluate(iid, compare_to, compare_label):
        """Run the PROVE program for iid and compare to `compare_to`.
        Returns one of: 'correct', 'mismatch', 'no_code', 'error', 'skip', 'timeout'.
        """
        response = prove_responses[iid]
        code = extract_python(response)

        print(f"\n  ID {iid}:")
        print(f"    {compare_label}: '{(compare_to or '')[:60]}'")

        if not code:
            print(f"    NO CODE extracted. Response head: {response[:200]!r}")
            return "no_code"

        status, out = run_python(code)

        if status != "ok":
            print(f"    EXECUTION {status.upper()}: {out[:200]}")
            print(f"    Code ({len(code)} chars): {code[:200]}")
            return status

        if out.strip() == "SKIP":
            print(f"    Program said SKIP")
            return "skip"

        match = answers_equal(compare_to, out)
        print(f"    Program output: '{out[:60]}'  -> {'CORRECT' if match else 'MISMATCH'}")
        if not match:
            print(f"    Code ({len(code)} chars): {code[:200]}")
        return "correct" if match else "mismatch"

    # CALIBRATION: compare PROVE output to KNOWN training answer
    print("\n--- CALIBRATION (compare to known training label) ---")
    calib_correct = calib_other = 0
    calib_outcomes = {}
    for iid in CALIBRATION_IDS:
        known = train_answers.get(iid, "")
        w, c, n = majority[iid]
        print(f"\n  ID {iid}:  KNOWN='{known[:60]}'  SC8-majority='{w[:60]}' ({c}/{n})")
        outcome = evaluate(iid, known, "KNOWN ANSWER")
        calib_outcomes[iid] = outcome
        if outcome == "correct":
            calib_correct += 1
        else:
            calib_other += 1

    # GOOD: compare PROVE output to SC=8 majority; also show answer sheet
    print("\n--- GOOD (compare to SC=8 majority; answer-sheet for reference) ---")
    good_correct = good_mismatch = good_error = good_no_code = good_skip = 0
    good_outcomes = {}
    for iid in GOOD_IDS:
        w, c, n = majority[iid]
        sheet_best = answer_sheet.get(iid, "")
        print(f"\n  ID {iid}:  SC8-majority='{w[:60]}' ({c}/{n})  answer-sheet='{sheet_best[:60]}'")
        outcome = evaluate(iid, w, "SC8 MAJORITY")
        good_outcomes[iid] = outcome
        if outcome == "correct":
            good_correct += 1
        elif outcome == "mismatch":
            good_mismatch += 1
        elif outcome == "no_code":
            good_no_code += 1
        elif outcome == "skip":
            good_skip += 1
        else:
            good_error += 1

    # EDGE: report each item individually
    print("\n--- EDGE (report-only; expected to fail gracefully) ---")
    edge_outcomes = {}
    for iid in EDGE_IDS:
        item = items[iid]
        is_mcq = bool(item.get("options"))
        w, c, n = majority[iid]
        sheet_best = answer_sheet.get(iid, "")
        tag = "MCQ" if is_mcq else "FREE"
        print(f"\n  ID {iid} [{tag}]:  SC8-majority='{w[:60]}' ({c}/{n})  answer-sheet='{sheet_best[:60]}'")
        outcome = evaluate(iid, w, "SC8 MAJORITY")
        edge_outcomes[iid] = (tag, outcome)

    # ----- FINAL SUMMARY -----
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"\nCALIBRATION (PROVE vs KNOWN training label):")
    print(f"  {calib_correct}/{len(CALIBRATION_IDS)} correct")
    for iid in CALIBRATION_IDS:
        print(f"    ID {iid}: {calib_outcomes[iid]}")

    print(f"\nGOOD (PROVE vs SC=8 majority):")
    print(f"  Correct:  {good_correct}/{len(GOOD_IDS)}")
    print(f"  Mismatch: {good_mismatch}/{len(GOOD_IDS)}")
    print(f"  No code:  {good_no_code}/{len(GOOD_IDS)}")
    print(f"  Skip:     {good_skip}/{len(GOOD_IDS)}")
    print(f"  Errors:   {good_error}/{len(GOOD_IDS)}")
    for iid in GOOD_IDS:
        print(f"    ID {iid}: {good_outcomes[iid]}")

    print(f"\nEDGE (report-only):")
    for iid in EDGE_IDS:
        tag, outcome = edge_outcomes[iid]
        print(f"    ID {iid} [{tag}]: {outcome}")


if __name__ == "__main__":
    main()

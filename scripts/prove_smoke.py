"""PROVE-style verification smoke test.

For each FREE-form item (skips MCQ):
  1. Generate SC=8 solutions (T=0.6) to get a majority vote answer.
  2. Ask model to write a Python program that INDEPENDENTLY solves the
     problem -- without ever seeing the proposed answer.
  3. Execute the program (subprocess, 10s timeout).
  4. Compare program output to majority vote answer (handles
     fraction/decimal/whitespace differences).

Run from repo root:
    python3 scripts/prove_smoke.py [model_path]

Default model path: sft_v4_epoch6_merged

SECURITY NOTE: this script EXECUTES model-generated Python with no sandbox.
Trust your model.
"""

import argparse
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


TEST_IDS = [17, 22, 18, 19, 25, 30, 2, 4, 6, 7, 11, 16]
SYSTEM = "Please reason step by step and put your final answer within \\boxed{}."
PROVE_SYSTEM = (
    "Write a Python program to solve the following math problem. "
    "The program must compute the answer from scratch using arithmetic, "
    "sympy, or numpy as needed. Print ONLY the final numerical answer "
    "(no labels, no extra text). If the problem cannot be solved "
    "computationally, print 'SKIP'."
)

# Engine config
DTYPE = "bfloat16"
GPU_MEMORY_UTILIZATION = 0.85
MAX_MODEL_LEN = 20480
PROG_TIMEOUT = 10


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


def extract_python(text):
    """Extract Python code block from model output."""
    m = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # No fenced block: if text contains imports/prints, treat whole text as code
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


# ---- Answer comparison helpers ----

_LATEX_FRAC = re.compile(r"\\d?frac\s*\{(-?[^{}]+)\}\s*\{(-?[^{}]+)\}")
_SIMPLE_FRAC = re.compile(r"^\s*(-?\d+)\s*/\s*(-?\d+)\s*$")


def to_number(s):
    """Try to parse s as a real number (int, float, fraction, latex frac).
    Returns float or None."""
    if s is None:
        return None
    s = str(s).strip()
    s = s.replace("$", "").replace("\\,", "").replace("\\;", "").replace(",", "")
    # latex frac
    m = _LATEX_FRAC.search(s)
    if m:
        try:
            num = float(m.group(1))
            den = float(m.group(2))
            if den != 0:
                return num / den
        except (ValueError, ZeroDivisionError):
            pass
    # simple a/b
    m = _SIMPLE_FRAC.match(s)
    if m:
        try:
            return float(m.group(1)) / float(m.group(2))
        except (ValueError, ZeroDivisionError):
            pass
    # plain float
    try:
        return float(s)
    except ValueError:
        return None


def answers_equal(majority, program_out, rtol=1e-3, atol=1e-4):
    """True if `program_out` matches `majority` answer."""
    m = (majority or "").strip()
    p = (program_out or "").strip()
    if not m or not p:
        return False
    if m == p:
        return True
    # Last whitespace-separated token from program output (in case it prints extras)
    p_tail = p.split()[-1] if p.split() else p
    if m == p_tail:
        return True
    # Numeric comparison
    m_num = to_number(m)
    p_num = to_number(p_tail)
    if m_num is not None and p_num is not None:
        if abs(m_num - p_num) <= atol + rtol * max(abs(m_num), abs(p_num)):
            return True
    return False


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("model", nargs="?", default="sft_v4_epoch6_merged")
    p.add_argument("--max-model-len", type=int, default=MAX_MODEL_LEN)
    return p.parse_args()


def main():
    args = parse_args()

    with open("private.jsonl") as f:
        items = {json.loads(l)["id"]: json.loads(l) for l in f}

    free_ids = [iid for iid in TEST_IDS if not items[iid].get("options")]
    mcq_ids = [iid for iid in TEST_IDS if items[iid].get("options")]
    print(f"Free-form items to PROVE: {free_ids}")
    print(f"MCQ items skipped: {mcq_ids}")

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

    # STEP 1: SC=8 solutions on the FREE items to derive majority answers
    print("\n" + "=" * 60)
    print("STEP 1: Majority vote (SC=8 @ T=0.6)")
    print("=" * 60)

    solve_prompts = []
    for iid in free_ids:
        item = items[iid]
        msgs = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": item.get("question", "")},
        ]
        solve_prompts.append(tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))

    solve_out = llm.generate(solve_prompts, SamplingParams(
        temperature=0.6, max_tokens=16384, top_p=0.95, n=8))

    majorities = {}  # iid -> (winner, votes, n_nonempty)
    for idx, iid in enumerate(free_ids):
        answers = [extract_boxed(o.text) for o in solve_out[idx].outputs]
        non_empty = [a for a in answers if a]
        vote = Counter(non_empty)
        if vote:
            winner, count = vote.most_common(1)[0]
        else:
            winner, count = "", 0
        majorities[iid] = (winner, count, len(non_empty))
        print(f"  ID {iid}: majority='{winner[:60]}' votes={count}/{len(non_empty)}")

    # STEP 2: Generate PROVE Python programs (NO proposed answer in prompt)
    print("\n" + "=" * 60)
    print("STEP 2: Generate Python programs (independent)")
    print("=" * 60)

    prove_prompts = []
    prove_ids = []
    for iid in free_ids:
        winner, count, _ = majorities[iid]
        if not winner:
            print(f"  ID {iid}: SKIP -- majority vote produced no answer")
            continue
        user_msg = items[iid].get("question", "")
        msgs = [
            {"role": "system", "content": PROVE_SYSTEM},
            {"role": "user", "content": user_msg},
        ]
        prove_prompts.append(tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True))
        prove_ids.append(iid)

    if not prove_prompts:
        print("\nNo items eligible for PROVE.")
        return

    prove_out = llm.generate(prove_prompts, SamplingParams(
        temperature=0.0, max_tokens=4096))

    # STEP 3: Execute programs and compare
    print("\n" + "=" * 60)
    print("STEP 3: Execute and compare to majority")
    print("=" * 60)

    n_verified = n_mismatch = n_no_code = n_run_err = n_skip = 0

    for i, iid in enumerate(prove_ids):
        response = prove_out[i].outputs[0].text
        code = extract_python(response)
        majority = majorities[iid][0]

        print(f"\n  ID {iid}:")
        print(f"    Majority: '{majority[:60]}'")

        if not code:
            print(f"    NO CODE extracted. Response head: {response[:200]!r}")
            n_no_code += 1
            continue

        status, out = run_python(code)

        if status != "ok":
            print(f"    EXECUTION {status.upper()}: {out[:200]}")
            print(f"    Code ({len(code)} chars): {code[:200]}")
            n_run_err += 1
            continue

        if out.strip() == "SKIP":
            print(f"    Program said SKIP (not computable)")
            n_skip += 1
            continue

        match = answers_equal(majority, out)
        verdict = "VERIFIED" if match else "MISMATCH"
        if match:
            n_verified += 1
        else:
            n_mismatch += 1
        print(f"    Program output: '{out[:60]}'  -> {verdict}")
        if not match:
            print(f"    Code ({len(code)} chars): {code[:200]}")

    print("\n" + "=" * 60)
    print("PROVE SUMMARY")
    print("=" * 60)
    print(f"  Verified (program agrees):    {n_verified}")
    print(f"  Mismatch (program disagrees): {n_mismatch}")
    print(f"  No code extracted:            {n_no_code}")
    print(f"  Runtime errors:               {n_run_err}")
    print(f"  Model said SKIP:              {n_skip}")
    print(f"  MCQ items skipped (n/a):      {len(mcq_ids)}")
    print(f"\n  VERDICT: {'PROVE flags potential corrections' if n_mismatch > 0 else 'PROVE confirms majority (no flips)'}")


if __name__ == "__main__":
    main()

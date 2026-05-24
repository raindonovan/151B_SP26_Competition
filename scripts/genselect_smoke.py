"""GenSelect smoke test: SC=16 vote analysis + verification on split items.

Test 12 untrained items at 8xT=0.6 + 8xT=1.0, then for items where the
runner-up has >=4 votes, run a verification prompt that asks the model to
pick the correct answer (outputting the actual answer string, NOT "A"/"B").

Logs which candidate was presented first (for position bias analysis).

Run from repo root:
    python3 scripts/genselect_smoke.py [model_path]

Default model path: sft_v4_epoch6_merged
"""

import argparse
import json
import os
import random
import re
import sys
from collections import Counter
from pathlib import Path

# Must be set before `import vllm` -- required by current pod setup.
os.environ["VLLM_USE_V1"] = "0"

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import torch  # noqa: E402
import vllm  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402
from vllm import LLM, SamplingParams  # noqa: E402


TEST_IDS = [17, 22, 18, 19, 25, 30, 2, 4, 6, 7, 11, 16]
SYSTEM = "Please reason step by step and put your final answer within \\boxed{}."
VERIFY_SYSTEM = (
    "You are an expert mathematician. Two candidate answers are proposed for a "
    "math problem. Analyze both, then output the correct full answer inside "
    "\\boxed{}. Do NOT output a label like 'A' or 'B' -- output the actual "
    "mathematical expression or numerical value."
)

# Engine config (mirrors scripts/run_vllm_sc.py)
DTYPE = "bfloat16"
GPU_MEMORY_UTILIZATION = 0.85
MAX_MODEL_LEN = 20480
PRINT_WIDTH = 60  # answer string width when printing


def normalize(s):
    """Normalize an answer string for comparison.
    Strips outer whitespace and $...$, collapses runs of whitespace,
    normalizes 'a,b' vs 'a, b' to 'a, b', removes LaTeX spacing macros."""
    if s is None:
        return ""
    s = str(s).strip()
    # Strip wrapping $...$ math delimiters (one pair)
    if s.startswith("$") and s.endswith("$") and len(s) >= 2:
        s = s[1:-1].strip()
    # Drop LaTeX spacing macros
    s = s.replace("\\,", " ").replace("\\;", " ").replace("\\ ", " ").replace("\\quad", " ").replace("\\!", "")
    # \dfrac vs \frac
    s = s.replace("\\dfrac", "\\frac")
    # Normalize comma spacing: 'a,b' or 'a , b' -> 'a, b'
    s = re.sub(r"\s*,\s*", ", ", s)
    # Collapse all internal whitespace runs to one space
    s = re.sub(r"\s+", " ", s).strip()
    return s


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


def build_prompt(iid, items, tokenizer):
    item = items[iid]
    q = item.get("question", "")
    opts = item.get("options", [])
    if opts:
        user = f"{q}\n\nOptions:\n" + "\n".join(opts)
    else:
        user = q
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
    return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def build_verify_prompt(iid, ans_a, ans_b, items, tokenizer):
    """Build a verification prompt. Returns (prompt, orientation) where
    orientation is "majority_first" (the passed ans_a is shown as Candidate A)
    or "minority_first" (passed ans_a is shown as Candidate B).
    """
    item = items[iid]
    q = item.get("question", "")
    opts = item.get("options", [])
    if opts:
        q += "\n\nOptions:\n" + "\n".join(opts)
    if random.random() > 0.5:
        cand_a, cand_b = ans_b, ans_a
        orientation = "minority_first"
    else:
        cand_a, cand_b = ans_a, ans_b
        orientation = "majority_first"
    user = (
        f"{q}\n\nCandidate A: {cand_a}\nCandidate B: {cand_b}\n\n"
        f"Analyze both candidates and output the correct answer inside "
        f"\\boxed{{}}. Output the actual answer, not a letter."
    )
    msgs = [{"role": "system", "content": VERIFY_SYSTEM}, {"role": "user", "content": user}]
    return tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True), orientation


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("model", nargs="?", default="sft_v4_epoch6_merged",
                   help="path or HF id of the merged model")
    p.add_argument("--max-model-len", type=int, default=MAX_MODEL_LEN)
    p.add_argument("--seed", type=int, default=0,
                   help="RNG seed for position-bias randomization")
    return p.parse_args()


def main():
    args = parse_args()
    random.seed(args.seed)

    with open("private.jsonl") as f:
        items = {json.loads(l)["id"]: json.loads(l) for l in f}

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

    # PHASE 1: SC=16 generation
    print("=" * 60)
    print("PHASE 1: SC=16 (8xT=0.6 + 8xT=1.0)")
    print("=" * 60)
    prompts = [build_prompt(iid, items, tokenizer) for iid in TEST_IDS]

    print("Generating 8 samples at T=0.6...")
    out_low = llm.generate(prompts, SamplingParams(temperature=0.6, max_tokens=16384, top_p=0.95, n=8))
    print("Generating 8 samples at T=1.0...")
    out_high = llm.generate(prompts, SamplingParams(temperature=1.0, max_tokens=16384, top_p=0.95, n=8))

    # PHASE 2: Vote analysis
    print(f"\n{'=' * 60}")
    print("PHASE 2: VOTE ANALYSIS")
    print("=" * 60)

    split_items = []
    results = {}

    for idx, iid in enumerate(TEST_IDS):
        answers_low = [extract_boxed(o.text) for o in out_low[idx].outputs]
        answers_high = [extract_boxed(o.text) for o in out_high[idx].outputs]
        all_answers = answers_low + answers_high
        non_empty = [a for a in all_answers if a]
        vote = Counter(non_empty)

        winner, count = vote.most_common(1)[0] if vote else ("", 0)
        # Agreement RELATIVE TO non-empty responses (not /16)
        agreement = count / len(non_empty) if non_empty else 0

        low_vote = Counter(a for a in answers_low if a)
        high_vote = Counter(a for a in answers_high if a)
        low_winner = low_vote.most_common(1)[0][0] if low_vote else ""
        high_winner = high_vote.most_common(1)[0][0] if high_vote else ""

        truncated = sum(1 for o in out_low[idx].outputs + out_high[idx].outputs
                        if o.finish_reason == "length")
        no_box = 16 - len(non_empty)

        qt = "MCQ" if items[iid].get("options") else "FREE"
        print(f"\nID {iid:>3} [{qt}] winner='{winner[:PRINT_WIDTH]}' votes={count}/{len(non_empty)} ({agreement:.0%}) trunc={truncated} nobox={no_box}")
        print(f"  Low-T:  {dict(low_vote.most_common(3))}")
        print(f"  High-T: {dict(high_vote.most_common(3))}")

        if low_winner != high_winner:
            print(f"  TEMP DISAGREE: low='{low_winner[:PRINT_WIDTH]}' high='{high_winner[:PRINT_WIDTH]}'")

        top2 = vote.most_common(2)
        needs_verify = False
        if len(top2) >= 2 and top2[1][1] >= 4:
            print(f"  MINORITY CHALLENGE: '{top2[1][0][:PRINT_WIDTH]}' has {top2[1][1]} votes")
            needs_verify = True
        if agreement < 0.5 and len(top2) >= 2:
            print(f"  DEEP SPLIT: no answer above 50%")
            needs_verify = True

        results[iid] = {"winner": winner, "agreement": agreement, "vote": dict(vote.most_common())}

        if needs_verify and len(top2) >= 2:
            split_items.append((iid, top2[0][0], top2[1][0], qt))

    # PHASE 3: GenSelect verification on splits
    print(f"\n{'=' * 60}")
    print(f"PHASE 3: GENSELECT VERIFICATION ({len(split_items)} items)")
    print("=" * 60)

    if not split_items:
        print("No splits detected. GenA (simple majority) is sufficient.")
    else:
        verify_data = []  # (iid, ans_a_majority, ans_b_minority, qt, orientation)
        verify_prompts = []
        for iid, ans_a, ans_b, qt in split_items:
            prompt, orient = build_verify_prompt(iid, ans_a, ans_b, items, tokenizer)
            verify_prompts.append(prompt)
            verify_data.append((iid, ans_a, ans_b, qt, orient))

        print(f"Running greedy verification on {len(split_items)} items...")
        verify_out = llm.generate(verify_prompts, SamplingParams(temperature=0.0, max_tokens=4096))

        verify_agrees_majority = 0
        verify_flips_minority = 0
        verify_third = 0
        verify_empty = 0

        for i, (iid, ans_a, ans_b, qt, orient) in enumerate(verify_data):
            verified_raw = extract_boxed(verify_out[i].outputs[0].text)
            n_verified = normalize(verified_raw)
            n_a = normalize(ans_a)
            n_b = normalize(ans_b)

            if not verified_raw:
                verdict = "EMPTY (no box)"
                verify_empty += 1
            elif n_verified == n_a:
                verdict = "AGREES with majority"
                verify_agrees_majority += 1
            elif n_verified == n_b:
                verdict = "FLIPS to minority"
                verify_flips_minority += 1
            else:
                verdict = f"THIRD ANSWER"
                verify_third += 1

            print(f"\n  ID {iid} [{qt}]:")
            print(f"    Orientation:  {orient}  (majority shown as {'A' if orient == 'majority_first' else 'B'})")
            print(f"    Majority:     '{ans_a[:PRINT_WIDTH]}' ({results[iid]['vote'].get(ans_a, 0)} votes)")
            print(f"    Minority:     '{ans_b[:PRINT_WIDTH]}' ({results[iid]['vote'].get(ans_b, 0)} votes)")
            print(f"    Verified:     '{verified_raw[:PRINT_WIDTH]}'")
            print(f"    Verdict:      {verdict}")
            print(f"    Trace preview: {verify_out[i].outputs[0].text[:200]}...")

        print(f"\n  Verification summary:")
        print(f"    Agrees with majority: {verify_agrees_majority}")
        print(f"    Flips to minority:    {verify_flips_minority}")
        print(f"    Third answer:         {verify_third}")
        print(f"    Empty (no box):       {verify_empty}")
        helpful = verify_flips_minority + verify_third
        print(f"    Verdict: {'FullGen adds value' if helpful > 0 else 'GenA is sufficient'}")

    # FINAL SUMMARY
    print(f"\n{'=' * 60}")
    print("FINAL SUMMARY")
    print("=" * 60)
    clear = sum(1 for r in results.values() if r['agreement'] >= 0.75)
    medium = sum(1 for r in results.values() if 0.5 <= r['agreement'] < 0.75)
    split = sum(1 for r in results.values() if r['agreement'] < 0.5)
    print(f"  Clear majority (>=75%): {clear}/12")
    print(f"  Medium agreement (50-75%): {medium}/12")
    print(f"  Split (<50%): {split}/12")
    print(f"  GenSelect candidates (minority >=4): {len(split_items)}/12")
    print(f"\n  RECOMMENDATION:")
    if len(split_items) == 0:
        print(f"  -> Use GenA (simple majority). No splits to verify.")
    elif len(split_items) <= 2:
        print(f"  -> Use GenA + verify only on the {len(split_items)} split items.")
    else:
        print(f"  -> Use FullGen. {len(split_items)} items benefit from verification.")


if __name__ == "__main__":
    main()

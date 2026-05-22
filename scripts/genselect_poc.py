#!/usr/bin/env python3
"""
GenSelect Proof-of-Concept — Round 2
Fixes: enable_thinking=False, max_tokens=16384, system prompt added.
"""

import json
import re
import pickle
import sys
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

MODEL_ID = "Qwen/Qwen3-4B-Thinking-2507"
CANDIDATES_PATH = "/tmp/genselect_final.pkl"

SYSTEM_PROMPT = (
    "Do not solve the problem yourself. "
    "Only analyze the given solutions and select the best one."
)

USER_TEMPLATE = """\
You will be given a math problem followed by {n} candidate solutions. \
Your task is to carefully analyze each solution for errors and select the best one.

Problem:
{question}

{solutions}

Analyze each solution step by step. Identify any computational errors or logical mistakes. \
Then select the best solution.

End your response with exactly: Judgment [{idx_range}]"""

def extract_judgment(text):
    """Extract the selected index from 'Judgment [N]'"""
    m = re.search(r'Judgment\s*\[(\d+)\]', text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # Fallback: last number in brackets
    all_m = re.findall(r'\[(\d+)\]', text)
    if all_m:
        return int(all_m[-1])
    return None

def extract_boxed(text):
    if not text:
        return None
    for m in re.finditer(r'\\boxed\{', text):
        start = m.end(); depth = 1; end = start
        while end < len(text) and depth:
            if text[end] == '{': depth += 1
            elif text[end] == '}': depth -= 1
            end += 1
        if depth == 0:
            return text[start:end-1]
    return None

def build_messages(candidate):
    q = candidate['question']
    samples = candidate['samples']
    n = len(samples)

    solutions_text = ""
    for idx, s in enumerate(samples):
        resp = s['response']
        if len(resp) > 3000:
            resp = resp[:2800] + "\n...[truncated]"
        solutions_text += f"Solution {idx}:\n{resp}\n\n"

    user_content = USER_TEMPLATE.format(
        n=n,
        question=q,
        solutions=solutions_text.strip(),
        idx_range=f"0-{n-1}",
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_content},
    ]

def main():
    print("=" * 70)
    print("GenSelect Proof-of-Concept")
    print("=" * 70)

    # Load candidates
    candidates = pickle.load(open(CANDIDATES_PATH, 'rb'))
    print(f"Loaded {len(candidates)} candidates\n")

    # Build prompts — use tokenizer chat template with enable_thinking=False
    # This inserts an empty <think></think> block, forcing the model to skip
    # the reasoning trace and follow the selection instruction directly.
    print(f"Loading tokenizer for chat template formatting...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)

    all_messages = [build_messages(c) for c in candidates]
    prompts = [
        tokenizer.apply_chat_template(
            msgs,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        for msgs in all_messages
    ]
    print(f"Built {len(prompts)} prompts")
    print(f"Longest prompt: {max(len(p) for p in prompts):,} chars")

    # Load model
    print(f"\nLoading model: {MODEL_ID}")
    llm = LLM(
        model=MODEL_ID,
        max_model_len=36864,
        gpu_memory_utilization=0.90,
        enable_prefix_caching=True,
        dtype="bfloat16",
    )

    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=16384,
        top_p=1.0,
    )

    # Run inference
    print(f"\nRunning inference on {len(prompts)} items...")
    outputs = llm.generate(prompts, sampling_params)

    # Evaluate
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    n_correct = 0
    results = []

    for i, (c, output) in enumerate(zip(candidates, outputs)):
        response = output.outputs[0].text
        selected_idx = extract_judgment(response)

        if selected_idx is not None and 0 <= selected_idx < 8:
            selected_ans = extract_boxed(c['samples'][selected_idx]['response'])
        else:
            selected_ans = None

        # Normalize for comparison
        def norm(x):
            if x is None: return None
            return x.strip().replace(', ', ',').replace(' ,', ',')

        picked_correct = (selected_idx in c['correct_sample_idxs']) if selected_idx is not None else False
        if picked_correct:
            n_correct += 1

        status = "✓ CORRECT" if picked_correct else "✗ WRONG"
        print(f"\n[{i+1:02d}] id={c['item_id']} MCQ={c['is_mcq']}")
        print(f"  Majority vote:   '{c['voted']}' (WRONG)")
        print(f"  Gold answer:     '{c['gold']}'")
        print(f"  Correct samples: {c['correct_sample_idxs']}")
        print(f"  Model selected:  Solution {selected_idx} → '{selected_ans}'")
        print(f"  Result:          {status}")

        results.append({
            'item_id': c['item_id'],
            'voted': c['voted'],
            'gold': c['gold'],
            'correct_sample_idxs': c['correct_sample_idxs'],
            'selected_idx': selected_idx,
            'selected_ans': selected_ans,
            'picked_correct': picked_correct,
            'response': response,
        })

    # Summary
    total = len(candidates)
    print(f"\n{'='*70}")
    print(f"SUMMARY: GenSelect picked correct solution {n_correct}/{total} times ({n_correct/total:.0%})")
    print(f"Majority vote baseline: 0/{total} (0%) — all items were wrong votes by definition")

    # Baseline: random pick from 8 samples
    avg_correct_per_item = sum(c['n_correct'] for c in candidates) / (total * 8)
    print(f"Random-pick baseline: ~{avg_correct_per_item:.0%} (avg correct samples / 8)")
    print(f"{'='*70}")

    # Save results
    out_path = "results/genselect_poc_r2_results.json"
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {out_path}")

if __name__ == "__main__":
    main()

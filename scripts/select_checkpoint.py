#!/usr/bin/env python3
"""
Checkpoint Selection for SFT v3
Evaluate all checkpoints and select best by no-box rate + teacher agreement
"""

import os
import sys
import json
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
from collections import defaultdict

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_MODEL_ID = "Qwen/Qwen2.5-Math-RM-4B-Thinking"
CHECKPOINTS_DIR = "./checkpoints/sft_v3"
DATASET_PATH = "sft_v3_dataset_final.jsonl"

# Only evaluate on R1/R2 items (we have teacher answers for these)
EVAL_TIERS = ["R1/R2"]

# ============================================================================
# LOAD DATASET
# ============================================================================

def load_eval_items():
    """Load R1/R2 items with teacher answers"""
    with open(DATASET_PATH) as f:
        all_items = [json.loads(line) for line in f]

    # Filter to R1/R2
    eval_items = [item for item in all_items if item.get("tier") in EVAL_TIERS]

    print(f"Loaded {len(eval_items)} R1/R2 items for evaluation")
    return eval_items

# ============================================================================
# GENERATE
# ============================================================================

def generate_response(model, tokenizer, question, max_tokens=2048, temperature=0.7):
    """Generate response for a question"""

    messages = [
        {"role": "system", "content": "Please reason step by step and put your final answer within \\boxed{}."},
        {"role": "user", "content": question}
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
        )

    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return response

# ============================================================================
# EXTRACT ANSWER
# ============================================================================

def extract_boxed_answer(text):
    """Extract answer from \\boxed{}"""
    import re

    # Find last \boxed{...}
    matches = list(re.finditer(r'\\boxed\{([^}]*)\}', text))
    if not matches:
        return None

    answer = matches[-1].group(1).strip()
    return answer

# ============================================================================
# EVALUATE CHECKPOINT
# ============================================================================

def evaluate_checkpoint(checkpoint_path, eval_items):
    """Evaluate single checkpoint on eval set"""

    print(f"\nEvaluating: {checkpoint_path}")

    # Load model
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(base_model, checkpoint_path)
    model.eval()

    results = []
    no_box_count = 0
    agreement_count = 0
    total_tokens = 0

    for i, item in enumerate(eval_items):
        question = item["messages"][1]["content"]
        teacher_response = item["messages"][2]["content"]
        teacher_answer = extract_boxed_answer(teacher_response)

        # Generate
        model_response = generate_response(model, tokenizer, question)
        model_answer = extract_boxed_answer(model_response)

        # Check format
        has_boxed = "\\boxed{" in model_response
        has_think_close = "</think>" in model_response

        if not has_boxed:
            no_box_count += 1

        # Check agreement
        agrees = (model_answer == teacher_answer) if (model_answer and teacher_answer) else False
        if agrees:
            agreement_count += 1

        total_tokens += len(model_response)

        results.append({
            "item_id": item.get("item_id"),
            "has_boxed": has_boxed,
            "has_think_close": has_think_close,
            "model_answer": model_answer,
            "teacher_answer": teacher_answer,
            "agrees": agrees,
            "response_length": len(model_response),
        })

        # Progress
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{len(eval_items)}")

    # Compute metrics
    total = len(eval_items)
    no_box_rate = no_box_count / total
    agreement_rate = agreement_count / total
    avg_tokens = total_tokens / total

    metrics = {
        "checkpoint": checkpoint_path,
        "no_box_rate": no_box_rate,
        "agreement_rate": agreement_rate,
        "avg_tokens": avg_tokens,
        "total_items": total,
    }

    print(f"  No-box rate: {no_box_rate:.1%}")
    print(f"  Teacher agreement: {agreement_rate:.1%}")
    print(f"  Avg tokens: {avg_tokens:.0f}")

    # Cleanup
    del model
    del base_model
    torch.cuda.empty_cache()

    return metrics, results

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("Checkpoint Selection - SFT v3")
    print("=" * 80)

    # Find all checkpoints
    checkpoint_dirs = sorted([
        d for d in Path(CHECKPOINTS_DIR).iterdir()
        if d.is_dir() and d.name.startswith("checkpoint-")
    ])

    print(f"\nFound {len(checkpoint_dirs)} checkpoints:")
    for cp in checkpoint_dirs:
        print(f"  - {cp.name}")

    # Load eval items
    eval_items = load_eval_items()

    # Evaluate each checkpoint
    all_metrics = []

    for checkpoint_dir in checkpoint_dirs:
        metrics, results = evaluate_checkpoint(str(checkpoint_dir), eval_items)
        all_metrics.append(metrics)

        # Save individual results
        result_path = f"{checkpoint_dir}_eval_results.json"
        with open(result_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"  Results saved to: {result_path}")

    # Rank checkpoints
    print("\n" + "=" * 80)
    print("CHECKPOINT RANKING")
    print("=" * 80)

    # Combined score: 70% agreement + 30% format compliance
    for m in all_metrics:
        m["score"] = (m["agreement_rate"] * 0.7) + ((1 - m["no_box_rate"]) * 0.3)

    ranked = sorted(all_metrics, key=lambda x: x["score"], reverse=True)

    print(f"\n{'Rank':<6} {'Checkpoint':<30} {'Score':<8} {'Agreement':<12} {'No-box':<10} {'Tokens':<8}")
    print("-" * 90)

    for i, m in enumerate(ranked):
        checkpoint_name = Path(m["checkpoint"]).name
        print(f"{i+1:<6} {checkpoint_name:<30} {m['score']:.3f}    {m['agreement_rate']:.1%}        {m['no_box_rate']:.1%}      {m['avg_tokens']:.0f}")

    # Recommendation
    best = ranked[0]
    best_checkpoint = Path(best["checkpoint"]).name

    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print(f"Best checkpoint: {best_checkpoint}")
    print(f"Score: {best['score']:.3f}")
    print(f"Teacher agreement: {best['agreement_rate']:.1%}")
    print(f"No-box rate: {best['no_box_rate']:.1%}")
    print()
    print(f"Next steps:")
    print(f"1. Manually inspect 10 samples from {best_checkpoint}")
    print(f"2. Merge adapter: python merge_adapter.py --checkpoint {best['checkpoint']}")
    print(f"3. Run full inference on 943 items")
    print(f"4. Submit to Kaggle")

    # Save summary
    summary_path = f"{CHECKPOINTS_DIR}/checkpoint_comparison.json"
    with open(summary_path, "w") as f:
        json.dump(ranked, f, indent=2)
    print(f"\nComparison saved to: {summary_path}")

if __name__ == "__main__":
    main()

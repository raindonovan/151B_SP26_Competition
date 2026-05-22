#!/usr/bin/env python3
"""
Smoke Test for SFT v3 Checkpoints
Run after epoch 1 to verify format compliance before continuing training
"""

import os
import sys
import json
import random
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_MODEL_ID = "Qwen/Qwen2.5-Math-RM-4B-Thinking"
CHECKPOINT_DIR = sys.argv[1] if len(sys.argv) > 1 else "./checkpoints/sft_v3/checkpoint-epoch-1"
N_SAMPLES = 10  # Number of items to test
SEED = 42

# Test items (mix of tiers)
TEST_ITEMS_PATH = "sft_v3_dataset_final.jsonl"

# ============================================================================
# LOAD MODEL
# ============================================================================

def load_checkpoint(checkpoint_dir):
    """Load checkpoint with adapter"""
    print(f"Loading checkpoint: {checkpoint_dir}")

    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL_ID,
        trust_remote_code=True,
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )

    model = PeftModel.from_pretrained(base_model, checkpoint_dir)
    model.eval()

    return model, tokenizer

# ============================================================================
# GENERATE
# ============================================================================

def generate_response(model, tokenizer, question, max_tokens=2048):
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
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
        )

    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return response

# ============================================================================
# VALIDATION CHECKS
# ============================================================================

def check_format(response):
    """Check if response has correct format"""
    checks = {
        "has_think_close": "</think>" in response,
        "has_boxed": "\\boxed{" in response,
        "think_before_boxed": "</think>" in response and "\\boxed{" in response and
                              response.index("</think>") < response.index("\\boxed{"),
        "no_degenerate_repetition": not any(token * 10 in response for token in ["1", "than", "the", " "]),
        "reasonable_length": 100 < len(response) < 3000,
    }
    return checks

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("SFT v3 Smoke Test")
    print("=" * 80)

    # Load model
    model, tokenizer = load_checkpoint(CHECKPOINT_DIR)

    # Load test items
    with open(TEST_ITEMS_PATH) as f:
        all_items = [json.loads(line) for line in f]

    # Sample test items (stratified by tier if possible)
    random.seed(SEED)
    test_items = random.sample(all_items, min(N_SAMPLES, len(all_items)))

    print(f"\nTesting on {len(test_items)} random items")
    print()

    results = []

    for i, item in enumerate(test_items):
        question = item["messages"][1]["content"]
        item_id = item.get("item_id", f"unknown_{i}")
        tier = item.get("tier", "unknown")

        print(f"[{i+1}/{len(test_items)}] Item {item_id} ({tier})")

        # Generate
        response = generate_response(model, tokenizer, question)

        # Check format
        checks = check_format(response)

        # Print result
        status = "✅ PASS" if all(checks.values()) else "❌ FAIL"
        print(f"  {status}")
        print(f"  - </think> present: {checks['has_think_close']}")
        print(f"  - \\boxed{{}} present: {checks['has_boxed']}")
        print(f"  - </think> before \\boxed: {checks['think_before_boxed']}")
        print(f"  - No repetition: {checks['no_degenerate_repetition']}")
        print(f"  - Reasonable length: {checks['reasonable_length']} ({len(response)} chars)")

        # Show snippet
        snippet = response[:200] + "..." if len(response) > 200 else response
        print(f"  Response: {snippet}")
        print()

        results.append({
            "item_id": item_id,
            "tier": tier,
            "checks": checks,
            "response": response,
        })

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    no_box_count = sum(1 for r in results if not r["checks"]["has_boxed"])
    no_think_close_count = sum(1 for r in results if not r["checks"]["has_think_close"])
    bad_order_count = sum(1 for r in results if not r["checks"]["think_before_boxed"])
    degenerate_count = sum(1 for r in results if not r["checks"]["no_degenerate_repetition"])

    no_box_rate = no_box_count / total
    no_think_close_rate = no_think_close_count / total

    print(f"No-box rate: {no_box_rate:.1%} ({no_box_count}/{total})")
    print(f"Missing </think>: {no_think_close_rate:.1%} ({no_think_close_count}/{total})")
    print(f"Wrong order: {bad_order_count}/{total}")
    print(f"Degenerate outputs: {degenerate_count}/{total}")
    print()

    # Gates
    print("GATES:")
    if no_box_rate > 0.10:
        print(f"❌ FAIL: No-box rate {no_box_rate:.1%} > 10% threshold")
        print("   ACTION: Stop training, investigate format collapse")
    else:
        print(f"✅ PASS: No-box rate {no_box_rate:.1%} < 10% threshold")

    if no_think_close_rate > 0.10:
        print(f"❌ FAIL: Missing </think> rate {no_think_close_rate:.1%} > 10%")
        print("   ACTION: Stop training, investigate format collapse")
    else:
        print(f"✅ PASS: Missing </think> rate {no_think_close_rate:.1%} < 10%")

    if degenerate_count > 0:
        print(f"⚠️  WARNING: {degenerate_count} degenerate outputs detected")
        print("   ACTION: Monitor in next checkpoint")

    print()

    # Save results
    output_path = f"{CHECKPOINT_DIR}_smoke_test.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Detailed results saved to: {output_path}")

if __name__ == "__main__":
    main()

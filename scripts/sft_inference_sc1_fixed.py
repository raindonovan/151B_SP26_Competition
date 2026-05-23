import json
import os
import sys
import time
import subprocess
from datetime import datetime

os.environ['VLLM_USE_V1'] = '0'

from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from vllm import LLM, SamplingParams
from transformers import AutoTokenizer
from utils import last_boxed_only_string, remove_boxed

def get_gpu_memory():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=2
        )
        return int(result.stdout.strip())
    except:
        return -1

def log_progress(msg, log_file="results/sft_inference.log"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(log_file, "a") as f:
        f.write(line + "\n")

def main():
    output_file = "results/sftv3_epoch8_sc1_greedy.jsonl"
    log_file = "results/sft_inference.log"
    os.makedirs("results", exist_ok=True)

    log_progress("=== SFT INFERENCE (FIXED: chat template + training prompt) ===")
    log_progress(f"GPU memory at start: {get_gpu_memory()} MB")

    # Check for resume
    completed_ids = set()
    if os.path.exists(output_file):
        with open(output_file) as f:
            for line in f:
                if line.strip():
                    completed_ids.add(json.loads(line)["item_id"])
        log_progress(f"Resuming: {len(completed_ids)} items already completed")

    # Load tokenizer for chat template
    log_progress("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("./sft_v3_epoch8_merged")

    # Load all items
    with open("private.jsonl") as f:
        all_items = [json.loads(line) for line in f]

    pending_items = [item for item in all_items if item["id"] not in completed_ids]

    if not pending_items:
        log_progress("All items already completed!")
        return

    log_progress(f"Total items: {len(all_items)}, pending: {len(pending_items)}")

    # EXACT system prompt from training data
    SYSTEM_PROMPT = "Please reason step by step and put your final answer within \\boxed{}."

    def build_chat_prompt(item):
        question = item["question"]

        if "options" in item and item.get("options"):
            opts = "\n".join(item["options"])
            user_content = f"{question}\n\nOptions:\n{opts}"
        else:
            user_content = question

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        return prompt

    # Load model
    log_progress("Loading merged SFT model into vLLM...")
    model_start = time.time()
    llm = LLM(
        model="./sft_v3_epoch8_merged",
        tensor_parallel_size=1,
        max_model_len=12288,
        gpu_memory_utilization=0.9,
        
    )
    log_progress(f"Model loaded in {time.time() - model_start:.1f}s")
    log_progress(f"GPU memory after model load: {get_gpu_memory()} MB")

    # Greedy sampling — 8192 max (training max was 4096, this gives 2x headroom)
    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=8192,
        top_p=1.0
    )

    log_progress("Starting inference...")
    run_start = time.time()

    # Log first prompt to verify format
    first_prompt = build_chat_prompt(pending_items[0])
    log_progress(f"First prompt preview:")
    log_progress(f"  {first_prompt[:500]}")

    # Process in batches of 50
    batch_size = 50
    total_tokens = 0

    for batch_start in range(0, len(pending_items), batch_size):
        batch_end = min(batch_start + batch_size, len(pending_items))
        batch_items = pending_items[batch_start:batch_end]

        batch_prompts = [build_chat_prompt(item) for item in batch_items]
        batch_ids = [item["id"] for item in batch_items]

        batch_num = batch_start // batch_size + 1
        log_progress(f"Batch {batch_num}: items {batch_start+1}-{batch_end}/{len(pending_items)}")

        batch_gen_start = time.time()
        batch_outputs = llm.generate(batch_prompts, sampling_params)
        batch_gen_time = time.time() - batch_gen_start

        batch_tokens = 0
        for item_id, output in zip(batch_ids, batch_outputs):
            tokens = len(output.outputs[0].token_ids)
            batch_tokens += tokens
            total_tokens += tokens

            result = {
                "item_id": item_id,
                "response": output.outputs[0].text,
                "tokens": tokens
            }

            with open(output_file, "a") as f:
                f.write(json.dumps(result) + "\n")

            if tokens > 7000:
                log_progress(f"  ⚠ Item {item_id}: {tokens} tokens (near 8K cap)")

        avg_batch_tokens = batch_tokens / len(batch_items)
        tok_per_sec = batch_tokens / batch_gen_time if batch_gen_time > 0 else 0
        items_done = len(completed_ids) + batch_end
        items_left = len(all_items) - items_done
        elapsed = time.time() - run_start
        eta = (elapsed / (batch_end)) * items_left / 60 if batch_end > 0 else 0

        log_progress(f"  ✓ Batch {batch_num} in {batch_gen_time:.1f}s | {avg_batch_tokens:.0f} tok/item | {tok_per_sec:.0f} tok/s | ETA: {eta:.1f} min")
        log_progress(f"    GPU mem: {get_gpu_memory()} MB")

    run_time = time.time() - run_start

    # Final stats
    with open(output_file) as f:
        all_results = [json.loads(line) for line in f if line.strip()]

    no_box = sum(1 for r in all_results if not last_boxed_only_string(r["response"]))

    log_progress("=== INFERENCE COMPLETE ===")
    log_progress(f"Runtime: {run_time/60:.1f} minutes")
    log_progress(f"Items: {len(all_results)}/943")
    log_progress(f"Total tokens: {total_tokens}")
    log_progress(f"Avg tokens/item: {total_tokens/len(pending_items):.0f}")
    log_progress(f"No-box items: {no_box}/{len(all_results)}")
    log_progress(f"GPU memory: {get_gpu_memory()} MB")

if __name__ == '__main__':
    main()

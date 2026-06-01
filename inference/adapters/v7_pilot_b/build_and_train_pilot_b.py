#!/usr/bin/env python3
"""
Phase 1 Pilot B: build dataset + train LoRA adapter.
Qwen3-4B-Thinking-2507, r=64, alpha=128, 4ep, LR=2e-4, BF16.
Single N=40 resample if N=30 fails gate. Hard fail if N=40 fails.
"""
import csv, hashlib, json, os, random, re, sys
from pathlib import Path

# Must run from repo root
REPO = Path(__file__).parent.parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO / "inference/scripts"))

from phase1_pilot_lib import (
    extract_boxed, qc_match, has_sonnet_trace,
    BoundaryAssistantCollator, preflight_supervised_tokens, FailFastCallback,
)

SYSTEM_MSG = "Please reason step by step and put your final answer within \\boxed{}."
OUT_DIR = REPO / "inference/adapters/v7_pilot_b"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODULE_SHA = hashlib.sha256(
    (REPO / "inference/scripts/phase1_pilot_lib.py").read_bytes()
).hexdigest()
print(f"phase1_pilot_lib.py sha256: {MODULE_SHA}")


# ── load source lists ──────────────────────────────────────────────────────────
def load_candidates():
    ids = []
    with open(REPO / "data/v7_train_candidates.csv") as f:
        for row in csv.DictReader(f):
            ids.append(int(row["item_id"]))
    return ids

def load_anchors():
    ids = []
    with open(REPO / "data/search/teachers/anchor_set_FINAL.csv") as f:
        for row in csv.DictReader(f):
            raw = row["id"].lstrip("0") or "0"
            try:
                ids.append(int(raw))
            except ValueError:
                pass
    return ids

def load_gold():
    gold = {}
    with open(REPO / "archive/pre_audit_reset_20260530/answer_sheet/unified_answer_sheet_v6.csv") as f:
        for row in csv.DictReader(f):
            gold[int(row["item_id"])] = row["best_answer"].strip()
    return gold


# ── sonnet trace loader ────────────────────────────────────────────────────────
def load_sonnet_trace(item_id):
    padded = str(item_id).zfill(4)
    path = REPO / f"data/search/teachers/sonnet/item_{padded}.md"
    if not path.exists():
        return None
    text = path.read_text()
    prompt_match = re.search(r'## Prompt\n```\n(.*?)```', text, re.DOTALL)
    if not prompt_match:
        return None
    prompt = prompt_match.group(1).strip()
    # extract_boxed handles section search internally
    boxed = extract_boxed(text)
    # also return full response text for wrapping
    resp_match = re.search(r'## Reasoning \+ Response\n(.*?)(?=\n## |\Z)', text, re.DOTALL)
    response = resp_match.group(1).strip() if resp_match else None
    return prompt, response, boxed


# ── dataset builder for a given (n_wrong, n_anchor, seed) ─────────────────────
def build_dataset(candidates, anchors, gold, n_wrong, n_anchor, seed):
    # filter to trace-exists before sampling
    cands_with_trace = [i for i in candidates if has_sonnet_trace(i)]
    ancs_with_trace  = [i for i in anchors    if has_sonnet_trace(i)]
    print(f"  cands with trace: {len(cands_with_trace)}, anchors with trace: {len(ancs_with_trace)}")

    random.seed(seed)
    sampled_wrong  = random.sample(cands_with_trace, min(n_wrong,  len(cands_with_trace)))
    sampled_anchor = random.sample(ancs_with_trace,  min(n_anchor, len(ancs_with_trace)))
    all_items = [("wrong", i) for i in sampled_wrong] + [("anchor", i) for i in sampled_anchor]
    print(f"  sampled: {len(sampled_wrong)} wrong + {len(sampled_anchor)} anchor = {len(all_items)} total")

    dataset, drops = [], []
    drop_reasons = {}

    for source, item_id in all_items:
        trace = load_sonnet_trace(item_id)
        if trace is None:
            reason = "no_sonnet_trace"
            drops.append({"item_id": item_id, "reason": reason})
            drop_reasons[reason] = drop_reasons.get(reason, 0) + 1
            print(f"  DROP {item_id}: {reason}")
            continue

        prompt, response, boxed = trace

        if boxed is None:
            reason = "no_boxed_in_trace"
            drops.append({"item_id": item_id, "reason": reason})
            drop_reasons[reason] = drop_reasons.get(reason, 0) + 1
            print(f"  DROP {item_id}: {reason}")
            continue

        if response is None:
            reason = "no_response_section"
            drops.append({"item_id": item_id, "reason": reason})
            drop_reasons[reason] = drop_reasons.get(reason, 0) + 1
            print(f"  DROP {item_id}: {reason}")
            continue

        gold_ans = gold.get(item_id, "")
        if gold_ans and "This is a complex" not in gold_ans and gold_ans.strip():
            gold_slots = [s.strip() for s in gold_ans.split(',')]
            match = qc_match(boxed, gold_ans) or any(qc_match(boxed, g) for g in gold_slots)
            if not match:
                reason = f"sonnet_wrong: boxed={boxed!r} gold={gold_ans!r}"
                drops.append({"item_id": item_id, "reason": reason})
                drop_reasons["sonnet_wrong"] = drop_reasons.get("sonnet_wrong", 0) + 1
                print(f"  DROP {item_id}: sonnet wrong (boxed={boxed!r}, gold={gold_ans!r})")
                continue
        else:
            print(f"  WARN {item_id}: no verifiable gold — keeping")

        # wrap in <think>...</think> if not present
        if "<think>" not in response and "</think>" not in response:
            boxed_idx = response.rfind("\\boxed{")
            if boxed_idx > 0:
                thinking = response[:boxed_idx].rstrip()
                answer_part = response[boxed_idx:]
                response = f"<think>\n{thinking}\n</think>\n\n{answer_part}"

        record = {
            "messages": [
                {"role": "system",    "content": SYSTEM_MSG},
                {"role": "user",      "content": prompt},
                {"role": "assistant", "content": response},
            ],
            "item_id": item_id,
            "weight": 1,
            "source": f"sonnet_v7_pilot_b_{source}",
        }
        dataset.append(record)
        print(f"  PASS {item_id} ({source})")

    return dataset, drops, drop_reasons, len(all_items)


# ── main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Phase 1 Pilot B — dataset build + train")
    print("=" * 60)

    candidates = load_candidates()
    anchors    = load_anchors()
    gold       = load_gold()
    print(f"Candidates: {len(candidates)}, Anchors: {len(anchors)}, Gold entries: {len(gold)}")

    # ── STEP 3: N=30 attempt ──────────────────────────────────────────────────
    print("\n--- STEP 3: N=30 (28 wrong + 2 anchor, seed=43) ---")
    dataset, drops, drop_reasons, n_in = build_dataset(candidates, anchors, gold, 28, 2, 43)
    n_pass = len(dataset)
    drop_rate = (n_in - n_pass) / n_in if n_in else 1.0
    resample_used = False
    resample_N = 30

    gate_ok = (n_pass >= 20) and (drop_rate <= 0.25)
    print(f"\nN=30 gate: dataset_size={n_pass}, drop_rate={drop_rate:.2%} → {'PASS' if gate_ok else 'FAIL'}")

    if not gate_ok:
        # ── N=40 resample ─────────────────────────────────────────────────────
        print("\n--- STEP 3 RESAMPLE: N=40 (36 wrong + 4 anchor, seed=43) ---")
        dataset, drops, drop_reasons, n_in = build_dataset(candidates, anchors, gold, 36, 4, 43)
        n_pass = len(dataset)
        drop_rate = (n_in - n_pass) / n_in if n_in else 1.0
        resample_used = True
        resample_N = 40

        gate_ok = (n_pass >= 20) and (drop_rate <= 0.25)
        print(f"\nN=40 gate: dataset_size={n_pass}, drop_rate={drop_rate:.2%} → {'PASS' if gate_ok else 'FAIL'}")

        if not gate_ok:
            qc_report = {
                "status": "FAIL",
                "resample_used": resample_used,
                "resample_N": resample_N,
                "dataset_size": n_pass,
                "drop_rate": round(drop_rate, 4),
                "drop_reasons_histogram": drop_reasons,
                "qc_chain": ["exact", "norm_string", "numeric", "math_verify"],
                "module_sha256": MODULE_SHA,
                "dropped": drops,
            }
            with open(OUT_DIR / "qc_report.json", "w") as f:
                json.dump(qc_report, f, indent=2)
            print("\nHARD FAIL: N=40 resample also failed gate. Phase 1 halted.")
            sys.exit(1)

    # ── write dataset ─────────────────────────────────────────────────────────
    out_path = OUT_DIR / "dataset.jsonl"
    with open(out_path, "w") as f:
        for r in dataset:
            f.write(json.dumps(r) + "\n")
    print(f"\nDataset written: {n_pass} items → {out_path}")

    # ── STEP 3.5: preflight ───────────────────────────────────────────────────
    print("\n--- STEP 3.5: preflight supervised tokens ---")
    from datasets import Dataset as HFDataset
    from transformers import AutoTokenizer

    MODEL_ID = "Qwen/Qwen3-4B-Thinking-2507"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True, padding_side="right")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    hf_dataset = HFDataset.from_list(dataset)
    pf = preflight_supervised_tokens(hf_dataset, tokenizer)
    print(f"Preflight OK: min_supervised={pf['min_supervised']}, max_supervised={pf['max_supervised']}")

    # ── write qc_report ───────────────────────────────────────────────────────
    qc_report = {
        "status": "PASS",
        "resample_used": resample_used,
        "resample_N": resample_N,
        "dataset_size": n_pass,
        "drop_rate": round(drop_rate, 4),
        "drop_reasons_histogram": drop_reasons,
        "qc_chain": ["exact", "norm_string", "numeric", "math_verify"],
        "module_sha256": MODULE_SHA,
        "preflight_min_supervised": pf["min_supervised"],
        "preflight_max_supervised": pf["max_supervised"],
        "passed_ids": [r["item_id"] for r in dataset],
        "dropped": drops,
    }
    with open(OUT_DIR / "qc_report.json", "w") as f:
        json.dump(qc_report, f, indent=2)
    print(f"qc_report.json written.")

    # ── STEP 4: training ──────────────────────────────────────────────────────
    print("\n--- STEP 4: training ---")
    import torch
    from transformers import AutoModelForCausalLM, Trainer, TrainingArguments
    from transformers.trainer_utils import get_last_checkpoint
    from peft import LoraConfig, get_peft_model

    OUTPUT_DIR = str(OUT_DIR / "adapter")

    LORA_CONFIG = {
        "r": 64,
        "lora_alpha": 128,
        "lora_dropout": 0.0,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        "bias": "none",
        "task_type": "CAUSAL_LM",
    }

    print(f"Loading model: {MODEL_ID}")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.bfloat16, device_map="auto", trust_remote_code=True
    )
    model = get_peft_model(model, LoraConfig(**LORA_CONFIG))
    model.print_trainable_parameters()

    # Pre-tokenize with BoundaryAssistantCollator; use base Trainer which never rewrites labels.
    collator = BoundaryAssistantCollator(tokenizer=tokenizer)
    tokenized_data = collator(list(hf_dataset))
    from datasets import Dataset as _DS
    tok_dataset = _DS.from_dict({k: v.tolist() for k, v in tokenized_data.items()})

    # Verify labels are non-trivial before training
    total_sup = sum(sum(1 for x in row if x != -100) for row in tok_dataset["labels"])
    assert total_sup > 0, f"All labels are -100 after tokenization — abort"
    print(f"Total supervised tokens across dataset: {total_sup}")

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=4,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=1.0e-4,
        lr_scheduler_type="linear",
        weight_decay=0.0,
        warmup_ratio=0.10,
        bf16=True,
        bf16_full_eval=False,
        max_grad_norm=1.0,
        logging_steps=1,
        save_strategy="epoch",
        save_total_limit=4,
        optim="adamw_torch",
        report_to="none",
        remove_unused_columns=False,
    )

    # Simple stack collator — dataset is already padded to uniform length by BoundaryAssistantCollator.
    # DataCollatorForSeq2Seq must NOT be used: it re-pads and may corrupt labels.
    def stack_collator(features):
        import torch
        return {k: torch.tensor([f[k] for f in features]) for k in features[0]}

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tok_dataset,
        data_collator=stack_collator,
        callbacks=[FailFastCallback()],
    )

    last_ckpt = get_last_checkpoint(OUTPUT_DIR) if os.path.isdir(OUTPUT_DIR) else None
    if last_ckpt:
        print(f"Resuming from {last_ckpt}")
    trainer.train(resume_from_checkpoint=last_ckpt)
    trainer.save_model(f"{OUTPUT_DIR}/final")
    print(f"\nTraining complete. Adapter saved to {OUTPUT_DIR}/final")


if __name__ == "__main__":
    main()

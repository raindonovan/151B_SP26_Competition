#!/usr/bin/env python3
"""Stream B v2 (LAST attempt): research-stabilized fp32 LoRA.
Changes from v1:
  - LR: 2e-4 → 5e-5 (4x lower)
  - warmup_ratio: 0 → 0.15 (cosine; eliminates step-1 full force)
  - max_grad_norm: 0.5 → 0.3
  - adam_epsilon: 1e-8 → 1e-6 (limits over-shrinkage)
  - grad_accum: 1 → 4 (smooths grad)
  - LoRA alpha: 128 → 64 (scale 2.0 → 1.0; halves grad magnitude)
  - max_length: 8192 → 4096
HARD STOP: any non-finite loss/grad in steps 1-3 → kill.
"""
import sys, os, json, hashlib
REPO = os.path.expanduser("~/151B_SP26_Competition")
sys.path.insert(0, REPO); os.chdir(REPO)

from inference.scripts.phase1_pilot_lib import (
    BoundaryAssistantCollator, preflight_supervised_tokens, FailFastCallback,
)
import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainerCallback
from trl import SFTTrainer, SFTConfig
from peft import LoraConfig, get_peft_model

OUT_DIR     = f"{REPO}/inference/adapters/v7_pilot_a"
DATASET_FP  = f"{OUT_DIR}/dataset.jsonl"
QC_FP       = f"{OUT_DIR}/qc_report.json"
ADAPTER_OUT = f"{OUT_DIR}/adapter"
TRAIN_CKPT  = f"{OUT_DIR}/training_ckpt"
MODEL_ID    = "Qwen/Qwen3-4B-Thinking-2507"
MAX_SEQ     = 4096
LIB_FP = f"{REPO}/inference/scripts/phase1_pilot_lib.py"
MODULE_SHA256 = hashlib.sha256(open(LIB_FP, "rb").read()).hexdigest()


class HardStopFirst3(TrainerCallback):
    """Belt-and-suspenders on top of FailFastCallback for steps 1-3."""
    def on_log(self, args, state, control, logs=None, **kwargs):
        if state.global_step > 3 or logs is None: return
        loss, gn = logs.get("loss"), logs.get("grad_norm")
        if loss is not None and not torch.isfinite(torch.tensor(loss)):
            raise RuntimeError(f"HardStop step {state.global_step}: loss={loss} (non-finite)")
        if gn is not None and not torch.isfinite(torch.tensor(gn)):
            raise RuntimeError(f"HardStop step {state.global_step}: grad_norm={gn} (non-finite)")


def main():
    data = [json.loads(l) for l in open(DATASET_FP)]
    print(f"Loaded {len(data)} pilot items (post-precheck)")

    tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True, padding_side="right")
    if tok.pad_token is None: tok.pad_token = tok.eos_token

    print("\n=== fp32 + eager model load ===")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float32,
        attn_implementation="eager",
        device_map="auto",
        trust_remote_code=True,
    )

    # Forward-pass preflight on all 27 (already proven finite in v1 fp32 run; cheap re-verify)
    print("\n=== Forward-pass preflight (re-verify) ===")
    bad = []
    model.eval()
    with torch.no_grad():
        for i, ex in enumerate(data):
            text = tok.apply_chat_template(ex['messages'], tokenize=False, add_generation_prompt=False)
            ids = tok(text, return_tensors='pt', truncation=True, max_length=MAX_SEQ).to(model.device)
            out = model(**ids)
            if not torch.isfinite(out.logits).all():
                bad.append({'idx': i, 'item_id': ex.get('item_id')})
                print(f"  item {i} (id={ex.get('item_id')}): NON-FINITE")
            elif i % 5 == 0:
                print(f"  item {i} (id={ex.get('item_id')}): ok", flush=True)
    model.train()
    if bad:
        print(f"FAIL: preflight non-finite {bad}")
        sys.exit(2)
    print(f"All {len(data)} items: finite logits ✓")

    # Apply LoRA: r=64, alpha=64 (NEW: was 128)
    print("\n=== Apply LoRA r=64 alpha=64 dropout=0 ===")
    model = get_peft_model(model, LoraConfig(
        r=64, lora_alpha=64, lora_dropout=0.0,
        bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    ))
    model.print_trainable_parameters()

    # Supervised tokens preflight (boundary collator)
    ds = Dataset.from_list([dict(d, input_ids=[0]) for d in data])
    pre = preflight_supervised_tokens(ds, tok, n_check=min(64, len(data)))
    print(f"supervised: min={pre['min_supervised']} max={pre['max_supervised']}")

    print("\n=== Train (fp32, 1 epoch, batch=1, accum=4, LR=5e-5, warmup=0.15, cosine, clip=0.3, eps=1e-6, alpha=64) ===")
    args = SFTConfig(
        output_dir=TRAIN_CKPT,
        max_length=MAX_SEQ,
        packing=False,
        bf16=False, fp16=False,
        num_train_epochs=1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=5e-5,
        warmup_ratio=0.15,
        lr_scheduler_type="cosine",
        max_grad_norm=0.3,
        adam_epsilon=1e-6,
        weight_decay=0.0,
        remove_unused_columns=False,
        dataset_kwargs={"skip_prepare_dataset": True},
        save_strategy="no",
        logging_steps=1,
        optim="adamw_torch",
        report_to="none",
    )
    collator = BoundaryAssistantCollator(tokenizer=tok)
    trainer = SFTTrainer(
        model=model, args=args, train_dataset=ds, processing_class=tok,
        data_collator=collator,
        callbacks=[HardStopFirst3(), FailFastCallback()],
    )
    trainer.train()
    trainer.save_model(ADAPTER_OUT)
    print(f"\nSaved adapter to {ADAPTER_OUT}")

    # Write qc_report (training complete; promotion gate next)
    qc_existing = json.load(open(QC_FP)) if os.path.exists(QC_FP) else {}
    qc_existing.update({
        "phase": "STEP4_TRAINED_v2",
        "module_sha256": MODULE_SHA256,
        "dataset_size_after_precheck": len(data),
        "stream": "B_fp32_v2",
        "fp32": True, "attn_implementation": "eager",
        "config": {
            "lr": 5e-5, "warmup_ratio": 0.15, "scheduler": "cosine",
            "max_grad_norm": 0.3, "adam_epsilon": 1e-6,
            "grad_accum": 4, "batch_size": 1,
            "lora_alpha": 64, "lora_r": 64,
            "max_length": MAX_SEQ,
        },
        "preflight_min_supervised": pre["min_supervised"],
        "preflight_max_supervised": pre["max_supervised"],
        "preflight_finite_logits_v2": "pass",
    })
    json.dump(qc_existing, open(QC_FP, "w"), indent=2)
    print("BUILD+TRAIN DONE")

if __name__ == "__main__":
    main()

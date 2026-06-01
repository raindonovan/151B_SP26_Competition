#!/usr/bin/env python3
"""Stream B v3 (FINAL): Cursor-arbitrated stabilized fp32 LoRA.
Changes from v2:
  - LR: 5e-5 → 1e-5 (5x lower)
  - warmup_ratio: 0.15 → 0.25
  - max_grad_norm: 0.3 → 0.1
  - adam_epsilon: 1e-6 → 1e-5
  - grad_accum: 4 → 8
  - max_length: 4096 → 2048
  - LoRA: r=32 alpha=16, attention-only target_modules (no MLP)
HARD STOP: non-finite OR >10x ratio in any optimizer step 1-10 → kill.
"""
import sys, os, json, hashlib
REPO = os.path.expanduser("~/151B_SP26_Competition")
sys.path.insert(0, REPO); os.chdir(REPO)

from inference.scripts.phase1_pilot_lib import (
    BoundaryAssistantCollator, preflight_supervised_tokens,
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
MAX_SEQ     = 2048
LIB_FP      = f"{REPO}/inference/scripts/phase1_pilot_lib.py"
MODULE_SHA256 = hashlib.sha256(open(LIB_FP, "rb").read()).hexdigest()


class HardStopV3(TrainerCallback):
    """KILL if any non-finite OR any >10x grad ratio in optimizer steps 1-10."""
    def __init__(self):
        self.prev_gn = None
        self.history = []
    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is None: return
        loss, gn = logs.get("loss"), logs.get("grad_norm")
        if loss is None and gn is None: return
        step = state.global_step
        finite_loss = loss is None or torch.isfinite(torch.tensor(loss))
        finite_gn = gn is None or torch.isfinite(torch.tensor(gn))
        self.history.append({"step": step, "loss": loss, "grad_norm": gn})
        if step <= 10:
            if not finite_loss:
                raise RuntimeError(f"HardStopV3 step {step}: loss={loss} (non-finite)")
            if not finite_gn:
                raise RuntimeError(f"HardStopV3 step {step}: grad_norm={gn} (non-finite)")
            if self.prev_gn is not None and gn is not None and self.prev_gn > 0:
                ratio = float(gn) / float(self.prev_gn)
                if ratio > 10:
                    raise RuntimeError(f"HardStopV3 step {step}: >10x ratio ({self.prev_gn:.4g} → {gn:.4g}, ratio={ratio:.2f})")
        if gn is not None:
            self.prev_gn = float(gn)


def main():
    data = [json.loads(l) for l in open(DATASET_FP)]
    print(f"Loaded {len(data)} pilot items (post-precheck v3, max_length=2048)")

    tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True, padding_side="right")
    if tok.pad_token is None: tok.pad_token = tok.eos_token

    print("\n=== fp32 + eager model load ===")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.float32, attn_implementation="eager",
        device_map="auto", trust_remote_code=True,
    )

    # Forward-pass preflight
    print("\n=== Forward-pass preflight ===")
    bad = []
    model.eval()
    with torch.no_grad():
        for i, ex in enumerate(data):
            text = tok.apply_chat_template(ex['messages'], tokenize=False, add_generation_prompt=False)
            ids = tok(text, return_tensors='pt', truncation=True, max_length=MAX_SEQ).to(model.device)
            out = model(**ids)
            if not torch.isfinite(out.logits).all():
                bad.append({'idx': i, 'item_id': ex.get('item_id')})
    model.train()
    if bad:
        print(f"FAIL preflight: {bad}")
        sys.exit(2)
    print(f"All {len(data)} items: finite logits ✓")

    # LoRA v3: r=32, alpha=16, attention-only
    print("\n=== Apply LoRA r=32 alpha=16 attention-only ===")
    model = get_peft_model(model, LoraConfig(
        r=32, lora_alpha=16, lora_dropout=0.0,
        bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj","k_proj","v_proj","o_proj"],
        use_rslora=False,
    ))
    model.print_trainable_parameters()

    ds = Dataset.from_list([dict(d, input_ids=[0]) for d in data])
    pre = preflight_supervised_tokens(ds, tok, n_check=min(64, len(data)))
    print(f"supervised: min={pre['min_supervised']} max={pre['max_supervised']}")

    print("\n=== Train v3 (fp32, 1 epoch, batch=1, accum=8, LR=1e-5, warmup=0.25, cosine, clip=0.1, eps=1e-5, attn-only LoRA) ===")
    args = SFTConfig(
        output_dir=TRAIN_CKPT, max_length=MAX_SEQ, packing=False,
        bf16=False, fp16=False,
        num_train_epochs=1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=1e-5,
        warmup_ratio=0.25,
        lr_scheduler_type="cosine",
        max_grad_norm=0.1,
        adam_epsilon=1e-5,
        weight_decay=0.0,
        remove_unused_columns=False,
        dataset_kwargs={"skip_prepare_dataset": True},
        save_strategy="no",
        logging_steps=1,
        optim="adamw_torch",
        report_to="none",
    )
    collator = BoundaryAssistantCollator(tokenizer=tok)
    hard_stop = HardStopV3()
    trainer = SFTTrainer(
        model=model, args=args, train_dataset=ds, processing_class=tok,
        data_collator=collator,
        callbacks=[hard_stop],
    )
    trainer.train()
    trainer.save_model(ADAPTER_OUT)
    print(f"\nSaved adapter to {ADAPTER_OUT}")

    # Promotion gate (a): check post-step-10 history for >10x jumps
    history = hard_stop.history
    jumps_over_10x = []
    for i in range(1, len(history)):
        prev = history[i-1].get("grad_norm")
        curr = history[i].get("grad_norm")
        if prev and curr and prev > 0:
            r = float(curr) / float(prev)
            if r > 10 or (1/r if r > 0 else 0) > 10:
                jumps_over_10x.append({"step": history[i]["step"], "prev": prev, "curr": curr, "ratio": r})
    all_finite_loss = all(h.get("loss") is None or torch.isfinite(torch.tensor(h["loss"])) for h in history)
    all_finite_gn = all(h.get("grad_norm") is None or torch.isfinite(torch.tensor(h["grad_norm"])) for h in history)
    gate_a_pass = all_finite_loss and all_finite_gn and not jumps_over_10x

    qc = {
        "phase": "v3_TRAIN_COMPLETE" if gate_a_pass else "v3_FAIL_gate_a_post_hard_stop",
        "module_sha256": MODULE_SHA256,
        "stream": "B_fp32_v3",
        "dataset_size": len(data),
        "config_v3": {
            "lr": 1e-5, "warmup_ratio": 0.25, "scheduler": "cosine",
            "max_grad_norm": 0.1, "adam_epsilon": 1e-5,
            "grad_accum": 8, "batch_size": 1,
            "lora_alpha": 16, "lora_r": 32,
            "target_modules": ["q_proj","k_proj","v_proj","o_proj"],
            "max_length": MAX_SEQ, "fp32": True, "attn": "eager",
        },
        "step_history": history,
        "jumps_over_10x_post_hard_stop": jumps_over_10x,
        "all_finite_loss": bool(all_finite_loss),
        "all_finite_grad_norm": bool(all_finite_gn),
        "gate_a_pass": gate_a_pass,
        "preflight_min_supervised": pre["min_supervised"],
        "preflight_max_supervised": pre["max_supervised"],
    }
    json.dump(qc, open(QC_FP, "w"), indent=2)
    print(f"Wrote {QC_FP} (gate_a_pass={gate_a_pass})")
    if not gate_a_pass:
        print(f"FAIL gate_a post-hard-stop: {len(jumps_over_10x)} jumps over 10x")
        sys.exit(3)
    print("TRAIN+GATE_A DONE")

if __name__ == "__main__":
    main()

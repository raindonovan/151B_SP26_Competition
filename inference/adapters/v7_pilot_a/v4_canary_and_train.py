#!/usr/bin/env python3
"""Stream B v4: toxic-sample canary + clean retrain.
Gates: G1 canary report, G2 ≥17 clean, G3 smoke non-regression, G4 first-10 finite.
Branches:
  toxic == 0   → PREFLIGHT_DISPROVES_HYPOTHESIS (exit clean)
  toxic > 10   → PREFLIGHT_FUNDAMENTAL_INCOMPAT (exit clean)
  1 ≤ toxic ≤ 10 → train on remaining with EXACT v3 config
"""
import sys, os, json, hashlib, subprocess
REPO = os.path.expanduser("~/151B_SP26_Competition")
sys.path.insert(0, REPO); os.chdir(REPO)

from inference.scripts.phase1_pilot_lib import BoundaryAssistantCollator, preflight_supervised_tokens
import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainerCallback
from trl import SFTTrainer, SFTConfig
from peft import LoraConfig, get_peft_model

OUT_DIR    = f"{REPO}/inference/adapters/v7_pilot_a"
DATASET_FP = f"{OUT_DIR}/dataset.jsonl"
CANARY_FP  = f"{OUT_DIR}/toxic_canary_v4.json"
QC_FP      = f"{OUT_DIR}/qc_report.json"
ADAPTER_OUT = f"{OUT_DIR}/adapter"
TRAIN_CKPT = f"{OUT_DIR}/training_ckpt"
MODEL_ID   = "Qwen/Qwen3-4B-Thinking-2507"
MAX_SEQ    = 2048
LIB_FP     = f"{REPO}/inference/scripts/phase1_pilot_lib.py"
MODULE_SHA256 = hashlib.sha256(open(LIB_FP, "rb").read()).hexdigest()


class HardStopV4(TrainerCallback):
    """G4: any non-finite in first 10 optimizer steps → FAIL."""
    def __init__(self):
        self.history = []
    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is None: return
        step = state.global_step
        loss, gn = logs.get("loss"), logs.get("grad_norm")
        self.history.append({"step": step, "loss": loss, "grad_norm": gn})
        if step <= 10:
            if loss is not None and not torch.isfinite(torch.tensor(loss)):
                raise RuntimeError(f"HardStopV4 step {step}: loss={loss} (non-finite)")
            if gn is not None and not torch.isfinite(torch.tensor(gn)):
                raise RuntimeError(f"HardStopV4 step {step}: grad_norm={gn} (non-finite)")


def main():
    data = [json.loads(l) for l in open(DATASET_FP)]
    print(f"Loaded {len(data)} items from v3-validated dataset")

    tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True, padding_side="right")
    if tok.pad_token is None: tok.pad_token = tok.eos_token

    print("\n=== STEP 2: Load model fp32 + eager + apply v3 LoRA (for canary) ===")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.float32, attn_implementation="eager",
        device_map="auto", trust_remote_code=True,
    )
    model = get_peft_model(model, LoraConfig(
        r=32, lora_alpha=16, lora_dropout=0.0,
        bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj","k_proj","v_proj","o_proj"],
        use_rslora=False,
    ))
    model.print_trainable_parameters()
    collator = BoundaryAssistantCollator(tokenizer=tok)
    model.train()

    # ============ STEP 3: Toxic-sample canary (per-sample forward+backward) ============
    print("\n=== STEP 3: Toxic-sample canary (per-item fwd+bwd) ===")
    toxic, healthy = [], []
    for i, ex in enumerate(data):
        model.zero_grad()
        iid = ex.get("item_id", "?")
        try:
            batch = collator([ex])
            batch = {k: v.to(model.device) if torch.is_tensor(v) else v for k, v in batch.items()}
            out = model(**batch)
            if not torch.isfinite(out.loss).all():
                toxic.append({
                    "dataset_idx": i, "item_id": iid,
                    "failure_mode": "nonfinite_loss",
                    "loss": str(out.loss.item()),
                    "first_nonfinite_param": None,
                })
                print(f"  [{i:>2}] item {iid}: TOXIC (nonfinite_loss={out.loss.item()})", flush=True)
                model.zero_grad()
                continue
            out.loss.backward()
            nonfinite_params = [
                n for n, p in model.named_parameters()
                if p.requires_grad and p.grad is not None and not torch.isfinite(p.grad).all()
            ]
            if nonfinite_params:
                toxic.append({
                    "dataset_idx": i, "item_id": iid,
                    "failure_mode": "nonfinite_grad",
                    "loss": float(out.loss.item()),
                    "first_nonfinite_param": nonfinite_params[0],
                    "total_nonfinite_params": len(nonfinite_params),
                })
                print(f"  [{i:>2}] item {iid}: TOXIC (nonfinite_grad, {len(nonfinite_params)} params, first={nonfinite_params[0]}, loss={out.loss.item():.3f})", flush=True)
            else:
                gn = (sum(p.grad.norm().item()**2 for p in model.parameters() if p.requires_grad and p.grad is not None)) ** 0.5
                healthy.append({"dataset_idx": i, "item_id": iid, "grad_norm": gn, "loss": float(out.loss.item())})
                print(f"  [{i:>2}] item {iid}: ok (loss={out.loss.item():.3f}, grad_norm={gn:.2f})", flush=True)
        except Exception as e:
            toxic.append({
                "dataset_idx": i, "item_id": iid,
                "failure_mode": f"exception:{type(e).__name__}",
                "loss": None, "first_nonfinite_param": None,
                "exception_msg": str(e)[:200],
            })
            print(f"  [{i:>2}] item {iid}: TOXIC (exception={type(e).__name__}: {str(e)[:80]})", flush=True)
        model.zero_grad()

    report = {
        "module_sha256": MODULE_SHA256,
        "n_toxic": len(toxic), "n_healthy": len(healthy),
        "toxic": toxic, "healthy": healthy,
    }
    json.dump(report, open(CANARY_FP, "w"), indent=2)
    print(f"\n[v4-canary] toxic={len(toxic)} healthy={len(healthy)}")
    if healthy:
        grads = sorted(h["grad_norm"] for h in healthy)
        print(f"[v4-canary] healthy grad_norm: min={grads[0]:.1f} median={grads[len(grads)//2]:.1f} max={grads[-1]:.1f}")
    print(f"[v4-canary] toxic item_ids: {[(t['dataset_idx'], t['item_id'], t['failure_mode']) for t in toxic]}")

    # ============ STEP 4: Branch on canary ============
    if len(toxic) == 0:
        qc = {"phase": "PREFLIGHT_DISPROVES_HYPOTHESIS",
              "module_sha256": MODULE_SHA256,
              "n_toxic": 0, "n_healthy": len(healthy)}
        json.dump(qc, open(QC_FP, "w"), indent=2)
        print("\n[v4] PREFLIGHT_DISPROVES_HYPOTHESIS — exiting clean (no train)")
        sys.exit(0)

    if len(toxic) > 10:
        qc = {"phase": "PREFLIGHT_FUNDAMENTAL_INCOMPAT",
              "module_sha256": MODULE_SHA256,
              "n_toxic": len(toxic), "n_healthy": len(healthy),
              "toxic_item_ids": [t["item_id"] for t in toxic]}
        json.dump(qc, open(QC_FP, "w"), indent=2)
        print(f"\n[v4] PREFLIGHT_FUNDAMENTAL_INCOMPAT toxic={len(toxic)} — exiting clean (no train)")
        sys.exit(0)

    # 1 ≤ toxic ≤ 10 → filter and train
    toxic_idxs = {t["dataset_idx"] for t in toxic}
    clean = [ex for i, ex in enumerate(data) if i not in toxic_idxs]
    print(f"\n[v4-clean] training on {len(clean)} items ({len(toxic)} excluded)")
    assert len(clean) >= 17, f"G2 FAIL: clean dataset {len(clean)} < 17"

    # Free model memory before reloading (LoRA state polluted by canary)
    del model
    torch.cuda.empty_cache()

    # ============ STEP 5: Train on clean with EXACT v3 hyperparams ============
    print("\n=== STEP 5: Train on clean (v3 hyperparams) ===")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.float32, attn_implementation="eager",
        device_map="auto", trust_remote_code=True,
    )
    model = get_peft_model(model, LoraConfig(
        r=32, lora_alpha=16, lora_dropout=0.0,
        bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj","k_proj","v_proj","o_proj"],
        use_rslora=False,
    ))
    model.print_trainable_parameters()

    ds = Dataset.from_list([dict(d, input_ids=[0]) for d in clean])
    pre = preflight_supervised_tokens(ds, tok, n_check=min(64, len(clean)))
    print(f"supervised: min={pre['min_supervised']} max={pre['max_supervised']}")

    args = SFTConfig(
        output_dir=TRAIN_CKPT, max_length=MAX_SEQ, packing=False,
        bf16=False, fp16=False,
        num_train_epochs=1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=1e-5, warmup_ratio=0.25, lr_scheduler_type="cosine",
        max_grad_norm=0.1, adam_epsilon=1e-5, weight_decay=0.0,
        remove_unused_columns=False,
        dataset_kwargs={"skip_prepare_dataset": True},
        save_strategy="no",
        logging_steps=1,
        optim="adamw_torch",
        report_to="none",
    )
    hard_stop = HardStopV4()
    trainer = SFTTrainer(
        model=model, args=args, train_dataset=ds, processing_class=tok,
        data_collator=BoundaryAssistantCollator(tokenizer=tok),
        callbacks=[hard_stop],
    )
    trainer.train()
    trainer.save_model(ADAPTER_OUT)
    print(f"\nSaved adapter to {ADAPTER_OUT}")

    # gate (a) check
    history = hard_stop.history
    jumps = []
    for i in range(1, len(history)):
        p, c = history[i-1].get("grad_norm"), history[i].get("grad_norm")
        if p and c and p > 0:
            r = float(c) / float(p)
            if r > 10 or (r > 0 and 1/r > 10): jumps.append({"step": history[i]["step"], "prev": p, "curr": c, "ratio": r})
    all_finite_loss = all(h.get("loss") is None or torch.isfinite(torch.tensor(h["loss"])) for h in history)
    all_finite_gn   = all(h.get("grad_norm") is None or torch.isfinite(torch.tensor(h["grad_norm"])) for h in history)
    gate_a = all_finite_loss and all_finite_gn and not jumps

    qc = {
        "phase": "TRAIN_COMPLETE_v4" if gate_a else "FAIL_gate_a_v4",
        "module_sha256": MODULE_SHA256,
        "stream": "B_fp32_v4_canary_filtered",
        "n_toxic_excluded": len(toxic),
        "toxic_excluded_item_ids": [t["item_id"] for t in toxic],
        "clean_dataset_size": len(clean),
        "config": {
            "lr": 1e-5, "warmup_ratio": 0.25, "scheduler": "cosine",
            "max_grad_norm": 0.1, "adam_epsilon": 1e-5,
            "grad_accum": 8, "batch_size": 1,
            "lora_alpha": 16, "lora_r": 32,
            "target_modules": ["q_proj","k_proj","v_proj","o_proj"],
            "max_length": MAX_SEQ, "fp32": True, "attn": "eager",
        },
        "step_history": history,
        "jumps_over_10x": jumps,
        "all_finite_loss": bool(all_finite_loss),
        "all_finite_grad_norm": bool(all_finite_gn),
        "gate_a_pass": gate_a,
        "preflight_min_supervised": pre["min_supervised"],
        "preflight_max_supervised": pre["max_supervised"],
    }
    json.dump(qc, open(QC_FP, "w"), indent=2)
    if not gate_a:
        print(f"FAIL gate_a (jumps={len(jumps)})")
        sys.exit(3)
    print("TRAIN COMPLETE — proceed to smoke (next step in separate command for time)")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Stream B: ONE bounded fp32 adapter attempt. 90-min HARD CAP.
- Reuse N=30 sample (seed=42), patched QC, verify ≥27 kept
- fp32 + eager attention (the FIX)
- preflight_finite_logits HARD GATE on all items
- 1 epoch, batch=1, max_grad_norm=0.5
- Promotion gate: training-loss finiteness + smoke non-regression
"""
import sys, os, json, csv, random, hashlib
REPO = os.path.expanduser("~/151B_SP26_Competition")
sys.path.insert(0, REPO); os.chdir(REPO)

from inference.scripts.phase1_pilot_lib import (
    extract_boxed, qc_match, qc_match_with_rung, has_sonnet_trace,
    BoundaryAssistantCollator, preflight_supervised_tokens, FailFastCallback,
)
import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer, SFTConfig
from peft import LoraConfig, get_peft_model

# --- config ---
OUT_DIR     = f"{REPO}/inference/adapters/v7_pilot_a"
DATASET_FP  = f"{OUT_DIR}/dataset.jsonl"
QC_FP       = f"{OUT_DIR}/qc_report.json"
ADAPTER_OUT = f"{OUT_DIR}/adapter"
TRAIN_CKPT  = f"{OUT_DIR}/training_ckpt"
MODEL_ID    = "Qwen/Qwen3-4B-Thinking-2507"
SEED        = 42
N_WRONG     = 24
N_ANCHOR    = 6
MAX_SEQ_LENGTH = 8192
SYS_MSG = "Please reason step by step and put your final answer within \\boxed{}."

LIB_FP = f"{REPO}/inference/scripts/phase1_pilot_lib.py"
MODULE_SHA256 = hashlib.sha256(open(LIB_FP, "rb").read()).hexdigest()

# --- loaders (unchanged from prior) ---
def load_master():
    m = {}
    with open(f"{REPO}/data/MASTER_ANSWERS.csv") as f:
        for r in csv.DictReader(f):
            try: iid = int(r["item_id"])
            except: continue
            m[iid] = {"best": r.get("sheet_best_answer","").strip(),
                      "tier": r.get("sheet_tier","").strip(),
                      "cat":  r.get("category","").strip()}
    return m

def load_v7_wrong():
    rows = []
    with open(f"{REPO}/data/v7_train_candidates.csv") as f:
        for r in csv.DictReader(f):
            r["item_id"] = int(r["item_id"])
            if has_sonnet_trace(r["item_id"]):
                rows.append(r)
    return rows

def load_anchors():
    rows = []
    with open(f"{REPO}/data/search/teachers/anchor_set_FINAL.csv") as f:
        for r in csv.DictReader(f):
            try: iid = int(r["id"])
            except: continue
            if has_sonnet_trace(iid):
                r["id"] = iid
                rows.append(r)
    return rows

def parse_sonnet_prompt(item_id):
    p = f"{REPO}/data/search/teachers/sonnet/item_{item_id:04d}.md"
    if not os.path.exists(p): return None
    txt = open(p).read()
    import re
    m_prompt = re.search(r"## Prompt\s*\n```\n(.*?)\n```", txt, re.S)
    m_resp = re.search(r"## Reasoning \+ Response\s*\n(.*?)(?=\n## Metadata|\Z)", txt, re.S)
    if not (m_prompt and m_resp): return None
    return m_prompt.group(1).strip(), m_resp.group(1).strip(), txt

def wrap_assistant(response_text, last_box):
    import re
    marker = "\\boxed{" + last_box + "}"
    idx = response_text.rfind(marker)
    if idx == -1:
        body = re.sub(r"\n*\\boxed\{[^}]*\}\s*$", "", response_text).rstrip()
    else:
        body = response_text[:idx].rstrip()
    return f"<think>\n{body}\n</think>\n\n\\boxed{{{last_box}}}"

def build(master, wrong_pool, anchor_pool, n_wrong, n_anchor, seed):
    rnd_w = random.Random(seed); rnd_a = random.Random(seed)
    wrong_pick  = rnd_w.sample(wrong_pool,  n_wrong)
    anchor_pick = rnd_a.sample(anchor_pool, n_anchor)
    dataset, drops = [], []
    rungs = {}
    def proc(item_id, source):
        s = parse_sonnet_prompt(item_id)
        if s is None:
            drops.append({"item_id": item_id, "source": source, "reason": "sonnet_parse_failed"}); return
        prompt, response, full_md = s
        last_box = extract_boxed(full_md)
        if not last_box:
            drops.append({"item_id": item_id, "source": source, "reason": "extract_boxed_none"}); return
        gold = master.get(item_id, {}).get("best", "")
        if not gold:
            drops.append({"item_id": item_id, "source": source, "reason": "no_master_gold"}); return
        matched, rung = qc_match_with_rung(last_box, gold)
        rungs[rung] = rungs.get(rung, 0) + 1
        if not matched:
            drops.append({"item_id": item_id, "source": source, "reason": f"qc_disagrees:{rung}", "sonnet": last_box[:80], "gold": gold[:80]}); return
        dataset.append({
            "messages": [
                {"role":"system","content":SYS_MSG},
                {"role":"user","content":prompt},
                {"role":"assistant","content":wrap_assistant(response, last_box)},
            ],
            "item_id": item_id, "weight": 1, "source": source,
        })
    for w in wrong_pick: proc(w["item_id"], "v7_wrong_residual")
    for a in anchor_pick: proc(a["id"], "anchor_set_FINAL")
    return dataset, drops, rungs

# --- preflight_finite_logits ---
def preflight_finite_logits(model, dataset_list, tokenizer):
    model.eval(); bad = []
    with torch.no_grad():
        for i, ex in enumerate(dataset_list):
            text = tokenizer.apply_chat_template(ex['messages'], tokenize=False, add_generation_prompt=False)
            ids = tokenizer(text, return_tensors='pt', truncation=True, max_length=MAX_SEQ_LENGTH).to(model.device)
            out = model(**ids)
            if not torch.isfinite(out.logits).all():
                bad.append({'idx': i, 'item_id': ex.get('item_id', '?')})
                print(f"  preflight item {i} (id={ex.get('item_id')}): NON-FINITE LOGITS", flush=True)
            else:
                lo, hi = out.logits.min().item(), out.logits.max().item()
                print(f"  preflight item {i} (id={ex.get('item_id')}): ok logits=[{lo:.2f},{hi:.2f}]", flush=True)
    model.train()
    return bad

def write_qc(status, payload):
    json.dump(payload, open(QC_FP, "w"), indent=2)
    print(f"Wrote {QC_FP} (status={status})")

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    master = load_master()
    wrong_pool = load_v7_wrong()
    anchor_pool = load_anchors()
    print(f"Pools: wrong={len(wrong_pool)} anchor={len(anchor_pool)}")

    # --- STEP 2: rebuild + verify ≥27 kept ---
    dataset, drops, rungs = build(master, wrong_pool, anchor_pool, N_WRONG, N_ANCHOR, SEED)
    n_in = N_WRONG + N_ANCHOR
    drop_rate = len(drops) / n_in
    print(f"\nBuild: N={n_in} dropped={len(drops)} ({drop_rate:.1%}) kept={len(dataset)} rungs={rungs}")
    if len(dataset) < 27:
        write_qc("FAIL_STEP2_QC", {
            "phase": "FAIL_STEP2_QC", "module_sha256": MODULE_SHA256,
            "dataset_size": len(dataset), "drop_rate": drop_rate,
            "drop_reasons_histogram": {d['reason']: 0 for d in drops},
            "qc_rungs": rungs, "seed_used": SEED,
        })
        print(f"FAIL: kept={len(dataset)} < 27")
        sys.exit(2)

    with open(DATASET_FP, "w") as f:
        for r in dataset: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(dataset)} items")

    # --- STEP 3: fp32 model + eager attn ---
    print("\n=== STEP 3: fp32 + eager attention model load ===")
    tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True, padding_side="right")
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float32,
        attn_implementation="eager",
        device_map="auto",
        trust_remote_code=True,
    )

    # --- STEP 3.5a: preflight_finite_logits HARD GATE ---
    print("\n=== STEP 3.5a: preflight_finite_logits (HARD GATE) ===")
    bad = preflight_finite_logits(model, dataset, tok)
    if bad:
        print(f"FAIL: fp32 preflight non-finite on {len(bad)} items: {[b['item_id'] for b in bad]}")
        write_qc("FAIL_STEP3.5a", {
            "phase": "FAIL_STEP3.5a", "module_sha256": MODULE_SHA256,
            "non_finite_count": len(bad), "non_finite_items": bad,
            "dataset_size": len(dataset), "qc_rungs": rungs, "seed_used": SEED,
        })
        sys.exit(2)
    print("ALL items produce finite logits (fp32 fix confirmed)")

    # --- STEP 3.5b: preflight_supervised_tokens ---
    print("\n=== STEP 3.5b: preflight_supervised_tokens ===")
    ds = Dataset.from_list([dict(d, input_ids=[0]) for d in dataset])
    pre = preflight_supervised_tokens(ds, tok, n_check=min(64, len(dataset)))
    print(f"supervised: min={pre['min_supervised']} max={pre['max_supervised']}")

    # --- STEP 4: train ---
    print("\n=== STEP 4: train (fp32, 1 epoch, batch=1) ===")
    model = get_peft_model(model, LoraConfig(
        r=64, lora_alpha=128, lora_dropout=0.0, bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    ))
    model.print_trainable_parameters()

    args = SFTConfig(
        output_dir=TRAIN_CKPT,
        max_length=MAX_SEQ_LENGTH,
        packing=False,
        bf16=False, fp16=False,
        num_train_epochs=1,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=1,
        learning_rate=2e-4,
        max_grad_norm=0.5,
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
        data_collator=collator, callbacks=[FailFastCallback()],
    )
    trainer.train()
    trainer.save_model(ADAPTER_OUT)
    print(f"\nSaved adapter to {ADAPTER_OUT}")

    # --- Write qc_report (training succeeded) ---
    write_qc("STEP4_TRAINED", {
        "phase": "STEP4_TRAINED",
        "module_sha256": MODULE_SHA256,
        "dataset_size": len(dataset),
        "drop_rate": drop_rate,
        "qc_rungs": rungs,
        "preflight_min_supervised": pre["min_supervised"],
        "preflight_max_supervised": pre["max_supervised"],
        "preflight_finite_logits": "pass",
        "fp32": True,
        "attn_implementation": "eager",
        "n_epochs": 1,
        "max_grad_norm": 0.5,
        "seed_used": SEED,
        "qc_chain": ["exact","norm_string","numeric","tuple","mv_raw","mv_boxed","mv_dollar","mv_dfrac_sub"],
        "dropped_detail": drops,
    })
    print("BUILD+TRAIN DONE")

if __name__ == "__main__":
    main()

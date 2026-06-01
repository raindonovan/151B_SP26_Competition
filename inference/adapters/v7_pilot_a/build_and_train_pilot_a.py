#!/usr/bin/env python3
"""Phase 1 Pilot A — build + preflight + train. Uses shared phase1_pilot_lib.
80/20: 24 wrong-residual + 6 anchors (or 32+8 on resample). seed=42.
"""
import sys, os, json, csv, random, hashlib
REPO = os.path.expanduser("~/151B_SP26_Competition")
sys.path.insert(0, REPO)
os.chdir(REPO)

from inference.scripts.phase1_pilot_lib import (
    extract_boxed, qc_match, has_sonnet_trace,
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
N_WRONG_INITIAL  = 24
N_ANCHOR_INITIAL = 6
N_WRONG_RESAMPLE  = 32
N_ANCHOR_RESAMPLE = 8
MAX_SEQ_LENGTH = 5500
SYS_MSG = "Please reason step by step and put your final answer within \\boxed{}."

LIB_FP = f"{REPO}/inference/scripts/phase1_pilot_lib.py"
MODULE_SHA256 = hashlib.sha256(open(LIB_FP, "rb").read()).hexdigest()

# --- loaders ---
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

# --- build one pass ---
def build_one(master, wrong_pool, anchor_pool, n_wrong, n_anchor, seed):
    rnd_w = random.Random(seed)
    rnd_a = random.Random(seed)
    wrong_pick  = rnd_w.sample(wrong_pool,  min(n_wrong,  len(wrong_pool)))
    anchor_pick = rnd_a.sample(anchor_pool, min(n_anchor, len(anchor_pool)))
    dataset, drops = [], []
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
        if not qc_match(last_box, gold):
            drops.append({"item_id": item_id, "source": source, "reason": "qc_disagrees", "sonnet": last_box[:120], "gold": gold[:120]}); return
        assistant = wrap_assistant(response, last_box)
        dataset.append({
            "messages": [
                {"role":"system","content":SYS_MSG},
                {"role":"user","content":prompt},
                {"role":"assistant","content":assistant},
            ],
            "item_id": item_id, "weight": 1, "source": source,
        })
    for w in wrong_pick: proc(w["item_id"], "v7_wrong_residual")
    for a in anchor_pick: proc(a["id"], "anchor_set_FINAL")
    return dataset, drops

def drop_histogram(drops):
    h = {}
    for d in drops: h[d["reason"]] = h.get(d["reason"], 0) + 1
    return h

# --- main ---
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    master = load_master()
    wrong_pool  = load_v7_wrong()
    anchor_pool = load_anchors()
    print(f"Pools: wrong={len(wrong_pool)} (w/ sonnet) anchor={len(anchor_pool)} (w/ sonnet)")

    # initial 30
    dataset, drops = build_one(master, wrong_pool, anchor_pool, N_WRONG_INITIAL, N_ANCHOR_INITIAL, SEED)
    n_in = N_WRONG_INITIAL + N_ANCHOR_INITIAL
    drop_rate = len(drops) / n_in
    print(f"N=30 pass: in={n_in} dropped={len(drops)} ({drop_rate:.1%}) kept={len(dataset)}")
    resample_used, resample_N = False, 30

    if not (len(dataset) >= 20 and drop_rate <= 0.25):
        print("Gate failed — retry N=40")
        dataset, drops = build_one(master, wrong_pool, anchor_pool, N_WRONG_RESAMPLE, N_ANCHOR_RESAMPLE, SEED)
        n_in = N_WRONG_RESAMPLE + N_ANCHOR_RESAMPLE
        drop_rate = len(drops) / n_in
        resample_used, resample_N = True, 40
        print(f"N=40 pass: in={n_in} dropped={len(drops)} ({drop_rate:.1%}) kept={len(dataset)}")
        if not (len(dataset) >= 20 and drop_rate <= 0.25):
            print("Gate STILL failed — writing FAIL qc_report and exiting non-zero")
            qc = {
                "phase": "FAIL_STEP3",
                "module_sha256": MODULE_SHA256,
                "dataset_size": len(dataset),
                "drop_rate": drop_rate,
                "drop_reasons_histogram": drop_histogram(drops),
                "resample_used": True, "resample_N": 40,
                "seed_used": SEED,
                "qc_chain": ["exact","norm_string","numeric","math_verify"],
            }
            json.dump(qc, open(QC_FP, "w"), indent=2)
            sys.exit(2)

    # Write dataset
    with open(DATASET_FP, "w") as f:
        for r in dataset: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(dataset)} items to {DATASET_FP}")

    # --- STEP 3.5 preflight ---
    print("\n=== STEP 3.5: preflight_supervised_tokens ===")
    tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True, padding_side="right")
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    # Add dummy input_ids so SFTTrainer treats dataset as pre-processed and skips
    # its tokenizer pipeline (which would strip `messages` before the collator runs).
    # BoundaryAssistantCollator ignores this field and tokenizes from `messages` itself.
    ds_with_dummy = [dict(d, input_ids=[0]) for d in dataset]
    ds = Dataset.from_list(ds_with_dummy)
    pre = preflight_supervised_tokens(ds, tok, n_check=min(64, len(dataset)))
    print(f"min_supervised={pre['min_supervised']}  max_supervised={pre['max_supervised']}")

    # --- STEP 4 train ---
    print("\n=== STEP 4: train ===")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.bfloat16, device_map="auto", trust_remote_code=True
    )
    model = get_peft_model(model, LoraConfig(
        r=64, lora_alpha=128, lora_dropout=0.0, bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    ))
    model.print_trainable_parameters()

    args = SFTConfig(
        output_dir=TRAIN_CKPT,
        max_length=MAX_SEQ_LENGTH,
        packing=False,
        remove_unused_columns=False,  # preserve `messages` for the collator
        dataset_kwargs={"skip_prepare_dataset": True},  # don't tokenize ourselves
        num_train_epochs=4,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=1,
        learning_rate=2e-4,
        lr_scheduler_type="linear",
        weight_decay=0.0,
        warmup_ratio=0.05,
        bf16=True,
        logging_steps=1,
        save_strategy="no",
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
    print(f"Saved adapter to {ADAPTER_OUT}")

    # --- Write qc_report ---
    qc = {
        "phase": "PASS_STEP4",
        "module_sha256": MODULE_SHA256,
        "dataset_size": len(dataset),
        "drop_rate": drop_rate,
        "drop_reasons_histogram": drop_histogram(drops),
        "resample_used": resample_used,
        "resample_N": resample_N,
        "seed_used": SEED,
        "preflight_min_supervised": pre["min_supervised"],
        "preflight_max_supervised": pre["max_supervised"],
        "qc_chain": ["exact","norm_string","numeric","math_verify"],
        "dropped_detail": drops,
    }
    json.dump(qc, open(QC_FP, "w"), indent=2)
    print(f"Wrote {QC_FP}")
    print("BUILD+TRAIN DONE")

if __name__ == "__main__":
    main()

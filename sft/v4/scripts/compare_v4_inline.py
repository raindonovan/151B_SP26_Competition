import json, re, sys, os, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE = "Qwen/Qwen3-4B-Thinking-2507"
CKPT_DIR = "checkpoints/sft_v4"
SYSTEM = "Please reason step by step and put your final answer within \\boxed{}."

with open("data/sft_v4_dataset.jsonl") as f:
    train_data = {int(json.loads(l)['item_id']): json.loads(l) for l in f}

with open("private.jsonl") as f:
    items = {json.loads(l)['id']: json.loads(l) for l in f}

mcq_ids = [iid for iid in sorted(train_data) if items.get(iid,{}).get('options')][:5]
free_ids = [iid for iid in sorted(train_data) if not items.get(iid,{}).get('options')][:5]
test_ids = mcq_ids + free_ids

def extract_boxed(text):
    positions = []
    i = 0
    while i < len(text):
        pos = text.find("\\boxed{", i)
        if pos == -1: break
        positions.append(pos)
        i = pos + 7
    if not positions: return ""
    start = positions[-1] + 7
    depth, j = 1, start
    while j < len(text) and depth > 0:
        if text[j] == "{": depth += 1
        elif text[j] == "}": depth -= 1
        j += 1
    return text[start:j-1].strip() if depth == 0 else ""

tokenizer = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)

ckpts = sorted([d for d in os.listdir(CKPT_DIR) if d.startswith("checkpoint")])
print(f"Checkpoints: {ckpts}")
print(f"Test items: MCQ={mcq_ids} FREE={free_ids}")

for ckpt_name in ckpts:
    ckpt_path = f"{CKPT_DIR}/{ckpt_name}"
    print(f"\n{'='*60}")
    print(f"TESTING: {ckpt_name}")
    print(f"{'='*60}")

    base = AutoModelForCausalLM.from_pretrained(
        BASE, torch_dtype=torch.bfloat16, device_map="auto", trust_remote_code=True)
    model = PeftModel.from_pretrained(base, ckpt_path)
    model.eval()

    match_mcq = match_free = format_ok = 0

    for iid in test_ids:
        item = items[iid]
        q = item.get("question","")
        opts = item.get("options",[])
        user = f"{q}\n\nOptions:\n" + "\n".join(opts) if opts else q

        msgs = [{"role":"system","content":SYSTEM},{"role":"user","content":user}]
        prompt = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=2048, do_sample=False)

        response = tokenizer.decode(out[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        sft_ans = extract_boxed(response)
        train_ans = extract_boxed(train_data[iid]['messages'][2]['content'])

        is_mcq = bool(opts)
        match = (re.sub(r'\s+','',sft_ans) == re.sub(r'\s+','',train_ans))

        if is_mcq and match: match_mcq += 1
        if not is_mcq and match: match_free += 1

        fmt = '<think>' in response and '</think>' in response and '\\boxed' in response
        if fmt: format_ok += 1

        status = "✓" if match else "✗"
        qt = "MCQ" if is_mcq else "FREE"
        print(f"  {status} ID {iid:>4} [{qt}] sft='{sft_ans[:30]}' train='{train_ans[:30]}' fmt={'OK' if fmt else 'BAD'}")

    print(f"\n  RESULT: MCQ={match_mcq}/5 FREE={match_free}/5 FORMAT={format_ok}/10")

    del model, base
    torch.cuda.empty_cache()

print("\n=== PICK EARLIEST EPOCH WITH MCQ >= 4/5 ===")

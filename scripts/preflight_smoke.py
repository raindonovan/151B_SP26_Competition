"""Pre-flight smoke test — run before EVERY GPU job.

Usage:
  python3 scripts/preflight_smoke.py \
    --mode base --model Qwen/Qwen3-4B-Thinking-2507

  python3 scripts/preflight_smoke.py \
    --mode adapter --model Qwen/Qwen3-4B-Thinking-2507 \
    --adapter-path checkpoints/sft_v4/checkpoint-588 --mcq-format bare
"""

import os
os.environ["VLLM_USE_V1"] = "0"

import argparse
import csv
import json
import re
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

# ── Imports from run_hybrid_inference (shared logic) ─────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from run_hybrid_inference import (
    build_user_msg,
    apply_shape_filter,
    count_ans_placeholders,
    extract_last_boxed,
    normalize_answer,
    load_done,
    SYSTEM_PROMPT,
    LETTERS,
)

# ── Result tracking ───────────────────────────────────────────────────────────
_results: list[tuple[str, str, str]] = []   # (status, name, detail)

def record(status: str, name: str, detail: str = "") -> bool:
    _results.append((status, name, detail))
    icon = "✓" if status == "PASS" else ("–" if status == "SKIP" else "✗")
    print(f"  [{icon}] {name}" + (f": {detail}" if detail else ""), flush=True)
    return status == "PASS"

# ── Load private items ────────────────────────────────────────────────────────
def load_private() -> dict[int, dict]:
    items = {}
    with open("private.jsonl") as f:
        for line in f:
            it = json.loads(line)
            items[int(it["id"])] = it
    return items

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 1 — Prompt format (no GPU)
# ══════════════════════════════════════════════════════════════════════════════
def check_prompt_format(items: dict[int, dict], mcq_format: str) -> bool:
    print("\n[1] PROMPT FORMAT")
    ok = True

    mcq_items  = [it for it in items.values() if it.get("options")][:5]
    free_items = [it for it in items.values() if not it.get("options")][:5]
    multi_items = [it for it in items.values()
                   if count_ans_placeholders(it.get("question","")) > 1][:3]

    failures = []

    for it in mcq_items:
        msg = build_user_msg(it, mcq_format)
        if "Options:" not in msg:
            failures.append(f"ID {it['id']}: MCQ missing Options: section")
            continue
        if mcq_format == "letters":
            if "A." not in msg or "B." not in msg:
                failures.append(f"ID {it['id']}: letters format but no A./B. labels")
        else:
            # bare: check that "A." is NOT present as a label prefix
            opts_block = msg.split("Options:\n", 1)[1] if "Options:\n" in msg else ""
            first_line = next((l for l in opts_block.splitlines() if l.strip()), "")
            if re.match(r"^[A-Z]\.\s", first_line):
                failures.append(f"ID {it['id']}: bare format but found letter labels")

    for it in free_items:
        msg = build_user_msg(it, mcq_format)
        if "Options:" in msg:
            failures.append(f"ID {it['id']}: free-form item has Options: section")

    for it in multi_items:
        n = count_ans_placeholders(it.get("question", ""))
        if n <= 1:
            failures.append(f"ID {it['id']}: expected multi-answer, got {n} placeholders")

    if failures:
        for f in failures:
            print(f"    ✗ {f}")
        ok = record("FAIL", "Prompt format", f"{len(failures)} failures")
    else:
        record("PASS", "Prompt format",
               f"{len(mcq_items)} MCQ, {len(free_items)} free, {len(multi_items)} multi OK")

    # Visual inspection — first 200 chars of each type
    print("  Sample prompts (first 200 chars):")
    for label, group in [("MCQ", mcq_items[:2]), ("Free", free_items[:2])]:
        for it in group:
            msg = build_user_msg(it, mcq_format)
            print(f"    [{label} ID {it['id']}] {repr(msg[:200])}")

    return ok


# ══════════════════════════════════════════════════════════════════════════════
# CHECK 2 — Model load (GPU)
# ══════════════════════════════════════════════════════════════════════════════
def check_model_load(model: str, adapter_path: str | None, mode: str):
    print("\n[2] MODEL LOAD")
    try:
        from vllm import LLM
        llm_kwargs = dict(
            model=model,
            gpu_memory_utilization=0.85,
            enable_prefix_caching=True,
            max_model_len=8192 + 4096,
            reasoning_parser="deepseek_r1",
            trust_remote_code=True,
            dtype="bfloat16",
        )
        if mode == "adapter":
            if not adapter_path:
                record("FAIL", "Model load", "--adapter-path required for adapter mode")
                return None, None
            llm_kwargs["enable_lora"] = True
            llm_kwargs["max_lora_rank"] = 64

        t0 = time.time()
        llm = LLM(**llm_kwargs)
        tokenizer = llm.get_tokenizer()
        elapsed = time.time() - t0

        try:
            import torch
            allocated = torch.cuda.memory_allocated() / 1e9
            reserved  = torch.cuda.memory_reserved()  / 1e9
            mem_str = f"GPU mem allocated={allocated:.1f}GB reserved={reserved:.1f}GB"
        except Exception:
            mem_str = "GPU mem: unavailable"

        record("PASS", "Model load", f"{elapsed:.1f}s | {mem_str}")
        return llm, tokenizer

    except Exception as e:
        record("FAIL", "Model load", str(e))
        return None, None


# ══════════════════════════════════════════════════════════════════════════════
# CHECK 3 — Generation smoke (GPU, 5 items)
# ══════════════════════════════════════════════════════════════════════════════
def check_generation(
    llm, tokenizer, items: dict[int, dict],
    adapter_path: str | None, mode: str, mcq_format: str
) -> bool:
    print("\n[3] GENERATION SMOKE")
    if llm is None:
        record("SKIP", "Generation smoke", "model not loaded")
        return False

    from vllm import SamplingParams
    from vllm.lora.request import LoRARequest

    mcq_items  = [it for it in items.values() if it.get("options")][:3]
    free_items = [it for it in items.values() if not it.get("options")][:2]
    test_items = mcq_items + free_items

    lora_req = (LoRARequest("sft_adapter", 1, adapter_path)
                if mode == "adapter" and adapter_path else None)

    sampling = SamplingParams(n=2, temperature=0.6, top_p=0.95, max_tokens=8192)

    n_pass = 0
    failures = []

    for it in test_items:
        iid = int(it["id"])
        is_mcq = bool(it.get("options"))
        user_msg = build_user_msg(it, mcq_format)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        try:
            t0 = time.time()
            gen_kwargs = {"lora_request": lora_req} if lora_req else {}
            outputs = llm.generate(prompt, sampling_params=sampling, **gen_kwargs)
            elapsed = time.time() - t0

            texts = [o.text for o in outputs[0].outputs]
            answers = [extract_last_boxed(t) for t in texts]
            has_box = any(a for a in answers)

            if not any(t.strip() for t in texts):
                failures.append(f"ID {iid}: empty output")
            elif not has_box:
                failures.append(f"ID {iid}: no \\boxed{{}} in any sample")
            else:
                n_pass += 1

            kind = "MCQ" if is_mcq else "FRE"
            ans_str = " | ".join(repr(a) for a in answers if a) or "NONE"
            print(f"    ID {iid} [{kind}] {elapsed:.1f}s → {ans_str}")

        except Exception as e:
            failures.append(f"ID {iid}: exception {e}")

    if failures:
        for f in failures:
            print(f"    ✗ {f}")
        return record("FAIL", "Generation smoke",
                      f"{n_pass}/{len(test_items)} items produced \\boxed{{}}")
    return record("PASS", "Generation smoke",
                  f"{n_pass}/{len(test_items)} items produced \\boxed{{}}")


# ══════════════════════════════════════════════════════════════════════════════
# CHECK 4 — Shape filter (no GPU)
# ══════════════════════════════════════════════════════════════════════════════
def check_shape_filter() -> bool:
    print("\n[4] SHAPE FILTER")
    failures = []

    # a) 1 box → PASS (not rejected)
    texts_a = [r"The answer is \boxed{42}"]
    rej_a, fb_a = apply_shape_filter(texts_a, is_multi_answer=False)
    if rej_a[0]:
        failures.append("case a: 1 box single-answer should NOT be rejected")
    else:
        print("    [✓] case a: 1 box → accepted")

    # b) 0 boxes → REJECTED (then fallback since all rejected)
    texts_b = ["The answer is 42"]
    rej_b, fb_b = apply_shape_filter(texts_b, is_multi_answer=False)
    if not fb_b:
        failures.append("case b: 0 boxes should trigger fallback")
    else:
        print("    [✓] case b: 0 boxes → fallback activated")

    # c) multi-answer item with 2 boxes → REJECTED (pair: one good, one bad)
    # Use 2 samples so fallback doesn't fire (fallback only fires if ALL are rejected)
    texts_c = [
        r"First: \boxed{3}, second: \boxed{7}",  # 2 boxes → should be rejected
        r"The answer is \boxed{42}",              # 1 box → accepted (prevents fallback)
    ]
    rej_c, fb_c = apply_shape_filter(texts_c, is_multi_answer=True)
    if not rej_c[0] or rej_c[1]:
        failures.append("case c: 2-box multi-answer rejected=[True,False] expected")
    else:
        print("    [✓] case c: 2 boxes on multi-answer → rejected")

    # d) all rejected → fallback clears flags
    texts_d = ["no box here", "also no box"]
    rej_d, fb_d = apply_shape_filter(texts_d, is_multi_answer=False)
    if not fb_d or any(rej_d):
        failures.append("case d: all-rejected fallback should clear all flags")
    else:
        print("    [✓] case d: all rejected → fallback clears flags")

    if failures:
        for f in failures:
            print(f"    ✗ {f}")
        return record("FAIL", "Shape filter", "; ".join(failures))
    return record("PASS", "Shape filter", "4/4 synthetic cases correct")


# ══════════════════════════════════════════════════════════════════════════════
# CHECK 5 — Resume (no GPU)
# ══════════════════════════════════════════════════════════════════════════════
def check_resume() -> bool:
    print("\n[5] RESUME")
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as tmp:
            tmp_path = tmp.name
            for iid in [1, 42, 99]:
                tmp.write(json.dumps({"id": iid, "voted_answer": "A"}) + "\n")

        done = load_done(tmp_path)
        os.unlink(tmp_path)

        if done == {1, 42, 99}:
            return record("PASS", "Resume", "load_done returned {1, 42, 99}")
        else:
            return record("FAIL", "Resume", f"expected {{1,42,99}}, got {done}")
    except Exception as e:
        return record("FAIL", "Resume", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# CHECK 6 — Adapter consistency (adapter mode only, GPU, 5 MCQ items)
# ══════════════════════════════════════════════════════════════════════════════
def check_adapter_consistency(
    llm, tokenizer, items: dict[int, dict],
    adapter_path: str | None, mode: str, mcq_format: str
) -> bool:
    print("\n[6] ADAPTER CONSISTENCY")
    if mode != "adapter":
        return record("SKIP", "Adapter consistency", "base mode")
    if llm is None:
        return record("SKIP", "Adapter consistency", "model not loaded")

    # Load trained IDs
    train_ids: set[int] = set()
    try:
        with open("data/sft_v5_dataset.jsonl") as f:
            for line in f:
                train_ids.add(int(json.loads(line)["item_id"]))
    except FileNotFoundError:
        return record("SKIP", "Adapter consistency", "sft_v5_dataset.jsonl not found")

    mcq_trained = [it for it in items.values()
                   if it.get("options") and int(it["id"]) in train_ids][:5]
    if not mcq_trained:
        return record("SKIP", "Adapter consistency", "no trained MCQ items found")

    from vllm import SamplingParams
    from vllm.lora.request import LoRARequest

    lora_req = LoRARequest("sft_adapter", 1, adapter_path) if adapter_path else None
    sampling = SamplingParams(n=3, temperature=0.6, top_p=0.95, max_tokens=8192)

    n_consistent = 0
    for it in mcq_trained:
        iid = int(it["id"])
        user_msg = build_user_msg(it, mcq_format)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        try:
            gen_kwargs = {"lora_request": lora_req} if lora_req else {}
            outputs = llm.generate(prompt, sampling_params=sampling, **gen_kwargs)
            texts = [o.text for o in outputs[0].outputs]
            answers = [normalize_answer(extract_last_boxed(t)) for t in texts]
            unique = set(a for a in answers if a)
            if len(unique) == 1:
                n_consistent += 1
                print(f"    ID {iid}: 3/3 match → {repr(list(unique)[0])}")
            else:
                ans_str = " | ".join(repr(a) for a in answers)
                print(f"    ID {iid}: INCONSISTENT: {ans_str}")
        except Exception as e:
            print(f"    ID {iid}: exception {e}")

    if n_consistent == len(mcq_trained):
        return record("PASS", "Adapter consistency",
                      f"{n_consistent}/{len(mcq_trained)} items 3/3 match")
    else:
        return record("FAIL", "Adapter consistency",
                      f"{n_consistent}/{len(mcq_trained)} consistent "
                      f"({len(mcq_trained)-n_consistent} inconsistent)")


# ══════════════════════════════════════════════════════════════════════════════
# CHECK 7 — Output format / splice (no GPU)
# ══════════════════════════════════════════════════════════════════════════════
def check_output_format() -> bool:
    print("\n[7] OUTPUT FORMAT / SPLICE")
    try:
        import subprocess

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path    = os.path.join(tmpdir, "base.jsonl")
            adapter_path = os.path.join(tmpdir, "adapter.jsonl")
            out_dir      = os.path.join(tmpdir, "out")
            os.makedirs(out_dir)

            # Write mock base (10 items)
            with open(base_path, "w") as f:
                for iid in range(10):
                    f.write(json.dumps({
                        "id": iid, "mode": "base",
                        "voted_answer": "A",
                        "votes": 6, "n_voting": 8,
                        "response": f"The answer is \\boxed{{A}} (item {iid})",
                        "samples": [], "wall_seconds": 1.0,
                    }) + "\n")

            # Write mock adapter (3 items — IDs 0, 3, 7 override base)
            with open(adapter_path, "w") as f:
                for iid in [0, 3, 7]:
                    f.write(json.dumps({
                        "id": iid, "mode": "adapter",
                        "voted_answer": "B",
                        "votes": 3, "n_voting": 3,
                        "response": f"Adapter answer \\boxed{{B}} (item {iid})",
                        "samples": [], "wall_seconds": 0.5,
                    }) + "\n")

            result = subprocess.run(
                [sys.executable, "scripts/splice_submission.py",
                 "--base", base_path,
                 "--adapter", adapter_path,
                 "--output-dir", out_dir],
                capture_output=True, text=True, cwd="."
            )

            sub_path = os.path.join(out_dir, "submission.csv")
            manifest_path = os.path.join(out_dir, "routing_manifest.csv")

            if result.returncode != 0:
                return record("FAIL", "Output format",
                              f"splice_submission.py exited {result.returncode}: {result.stderr[:200]}")

            if not os.path.exists(sub_path):
                return record("FAIL", "Output format", "submission.csv not created")

            with open(sub_path) as f:
                sub_rows = list(csv.DictReader(f))
            with open(manifest_path) as f:
                manifest_rows = list(csv.DictReader(f))

            # Verify: 943 rows (script fills 943 - only 10 have data → 933 empty)
            # Actually mock only has 10 items → expect 943 rows with 933 MISSING
            # Just check row count and routing
            adapter_rows = [r for r in manifest_rows if r["source"] == "adapter"]
            base_rows    = [r for r in manifest_rows if r["source"] == "base"]

            if len(adapter_rows) != 3:
                return record("FAIL", "Output format",
                              f"expected 3 adapter rows, got {len(adapter_rows)}")
            if len(base_rows) != 7:
                return record("FAIL", "Output format",
                              f"expected 7 base rows, got {len(base_rows)}")

            print(f"    submission.csv: {len(sub_rows)} rows")
            print(f"    manifest: {len(adapter_rows)} adapter | {len(base_rows)} base | "
                  f"{len(manifest_rows)-len(adapter_rows)-len(base_rows)} MISSING")
            return record("PASS", "Output format",
                          f"routing correct: 3 adapter, 7 base")

    except Exception as e:
        return record("FAIL", "Output format", str(e))


# ══════════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════════
def print_summary() -> int:
    n_pass = sum(1 for s, _, _ in _results if s == "PASS")
    n_fail = sum(1 for s, _, _ in _results if s == "FAIL")
    n_skip = sum(1 for s, _, _ in _results if s == "SKIP")

    print("\nPREFLIGHT RESULTS:")
    labels = [
        "1. Prompt format",
        "2. Model load",
        "3. Generation smoke",
        "4. Shape filter",
        "5. Resume",
        "6. Adapter consistency",
        "7. Output format",
    ]
    for i, (status, name, detail) in enumerate(_results):
        label = labels[i] if i < len(labels) else name
        icon = "✓" if status == "PASS" else ("–" if status == "SKIP" else "✗")
        suffix = f" ({detail})" if detail and status != "PASS" else ""
        print(f"  [{icon}] {label}: {status}{suffix}")

    print()
    if n_fail:
        print(f"  ⚠️  FAILURES DETECTED ({n_fail}) — do NOT launch until fixed.")
    else:
        print(f"  ALL CHECKS PASSED — ready to launch.")
    print(f"  ({n_pass} passed, {n_fail} failed, {n_skip} skipped)")
    return n_fail


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["base", "adapter"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter-path", default=None)
    parser.add_argument("--mcq-format", choices=["letters", "bare"], default="letters")
    parser.add_argument("--skip-gpu", action="store_true",
                        help="Skip GPU checks (2, 3, 6) for fast offline validation")
    args = parser.parse_args()

    print(f"Pre-flight smoke test")
    print(f"  mode={args.mode} model={args.model} mcq_format={args.mcq_format}")
    if args.adapter_path:
        print(f"  adapter={args.adapter_path}")
    print()

    items = load_private()

    # No-GPU checks first
    check_prompt_format(items, args.mcq_format)
    check_shape_filter()
    check_resume()
    check_output_format()

    # GPU checks
    if args.skip_gpu:
        print("\n[2] MODEL LOAD")
        record("SKIP", "Model load", "--skip-gpu")
        print("\n[3] GENERATION SMOKE")
        record("SKIP", "Generation smoke", "--skip-gpu")
        print("\n[6] ADAPTER CONSISTENCY")
        record("SKIP", "Adapter consistency", "--skip-gpu")
    else:
        llm, tokenizer = check_model_load(args.model, args.adapter_path, args.mode)
        check_generation(llm, tokenizer, items, args.adapter_path, args.mode, args.mcq_format)
        check_adapter_consistency(llm, tokenizer, items, args.adapter_path, args.mode, args.mcq_format)

    n_fail = print_summary()
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()

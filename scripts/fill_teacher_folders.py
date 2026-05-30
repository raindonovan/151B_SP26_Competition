#!/usr/bin/env python3
"""
Copy raw teacher responses from DataApp clone into competition repo per-LLM folders,
then re-extract answers into answers.csv per teacher.

Source: /tmp/dataapp/dataapp_outputs/
Dest:   data/search/teachers/{sonnet,gpt4,oss,xhigh}/item_XXXX.md

Extraction rules:
  - Last \\boxed{...} content (handles nested braces)
  - If no \\boxed, look for explicit "final answer: X" line
  - Hard-reject template placeholders -> blank + log
  - answers.csv columns: id,answer  (id UNPADDED 0..942)
"""

import csv
import json
import os
import re
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATAAPP = "/tmp/dataapp/dataapp_outputs"
TEACHERS_DIR = os.path.join(REPO_ROOT, "data", "search", "teachers")
NUM_ITEMS = 943

TEMPLATE_PLACEHOLDERS = {
    "answer", "letter", "value1,value2,value3", "value1", "value2", "value3",
    "option", "choice", "your answer", "final answer", "insert answer",
    "placeholder", "x", "y", "z",
}

PROTECTED_FILES = {"README.md", "FINDINGS.md", "SCRATCH.md"}


def extract_last_boxed(text):
    """Return content of last \\boxed{...}, handling nested braces."""
    matches = list(re.finditer(r'\\boxed\{', text))
    if not matches:
        return None
    start = matches[-1].end()
    depth = 1
    pos = start
    while pos < len(text) and depth > 0:
        if text[pos] == '{':
            depth += 1
        elif text[pos] == '}':
            depth -= 1
        pos += 1
    return text[start:pos - 1].strip()


def extract_final_answer_line(text):
    """Fallback: look for 'final answer: X' or 'answer: X' pattern."""
    m = re.search(
        r'(?:final\s+answer|answer)\s*[:=]\s*([^\n]{1,100})',
        text, re.IGNORECASE
    )
    if m:
        return m.group(1).strip()
    return None


def is_placeholder(val):
    if val is None:
        return False
    return val.lower().strip() in TEMPLATE_PLACEHOLDERS


def extract_answer(text):
    """Extract answer from response text. Returns (answer_or_empty, method, rejected)."""
    ans = extract_last_boxed(text)
    method = "boxed"
    if ans is None:
        ans = extract_final_answer_line(text)
        method = "final_answer_line"
    if ans is None:
        return "", "none", False
    if is_placeholder(ans):
        return "", method, True  # hard-rejected
    return ans, method, False


def copy_and_extract(llm_name, src_files_fn, rerun_overlay=None):
    """
    llm_name: folder name under data/search/teachers/
    src_files_fn: callable(item_idx) -> path to source .md file (or None)
    rerun_overlay: dict {item_idx: answer_str} for pre-recovered answers
    """
    dest_dir = os.path.join(TEACHERS_DIR, llm_name)
    os.makedirs(dest_dir, exist_ok=True)

    rows = []           # (id_str, answer)
    blanks = []         # item ids with no answer
    rejected = []       # item ids where placeholder was hard-rejected
    missing_src = []    # item ids where source file not found

    for idx in range(NUM_ITEMS):
        padded = f"{idx:04d}"
        dest_file = os.path.join(dest_dir, f"item_{padded}.md")
        key_str = str(idx)  # unpadded

        # Copy source file
        src = src_files_fn(idx)
        if src and os.path.exists(src):
            shutil.copy2(src, dest_file)
        else:
            missing_src.append(idx)
            # Write a stub so the file exists
            with open(dest_file, "w") as f:
                f.write(f"# item_{padded}\n\nSource file not found: {src}\n")

        # Check rerun overlay first (pre-recovered answer, skip extraction)
        if rerun_overlay and key_str in rerun_overlay:
            rows.append((key_str, rerun_overlay[key_str]))
            continue

        # Extract from copied file
        if os.path.exists(dest_file):
            with open(dest_file) as f:
                content = f.read()
            # Skip stub files
            if content.startswith("# item_") and "Source file not found" in content:
                rows.append((key_str, ""))
                blanks.append(idx)
                continue
            ans, method, was_rejected = extract_answer(content)
            if was_rejected:
                rejected.append(idx)
                rows.append((key_str, ""))
            elif not ans:
                blanks.append(idx)
                rows.append((key_str, ""))
            else:
                rows.append((key_str, ans))
        else:
            rows.append((key_str, ""))
            blanks.append(idx)

    # Write answers.csv
    csv_path = os.path.join(dest_dir, "answers.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "answer"])
        writer.writerows(rows)

    print(f"\n=== {llm_name} ===")
    print(f"  Files copied: {NUM_ITEMS - len(missing_src)}/{NUM_ITEMS}")
    if missing_src:
        print(f"  Missing source: {len(missing_src)} items: {missing_src[:10]}")
    print(f"  answers.csv rows: {len(rows)}")
    filled = sum(1 for _, a in rows if a)
    print(f"  Filled: {filled}  Blank: {len(rows) - filled}")
    if rejected:
        print(f"  Hard-rejected (placeholder): {len(rejected)} items: {rejected}")
    if blanks:
        print(f"  Blank items ({len(blanks)}): {sorted(blanks)[:20]}{'...' if len(blanks)>20 else ''}")

    return rows, blanks, rejected, missing_src


def main():
    # Load xhigh refusal recovery
    refusal_file = "/tmp/dataapp/data/xhigh_refusal_recovery.json"
    with open(refusal_file) as f:
        rec = json.load(f)
    xhigh_integrate = rec.get("integrate", {})   # {str_id: answer}
    xhigh_excluded = set(rec.get("excluded_with_reason", {}).keys())  # str ids

    print(f"xhigh recovery: {len(xhigh_integrate)} integrate, {len(xhigh_excluded)} excluded")

    # --- sonnet ---
    def sonnet_src(idx):
        return f"{DATAAPP}/item_{idx:04d}/sonnet_response.md"

    copy_and_extract("sonnet", sonnet_src)

    # --- gpt4 ---
    def gpt4_src(idx):
        return f"{DATAAPP}/item_{idx:04d}/gpt5_4_response.md"

    copy_and_extract("gpt4", gpt4_src)

    # --- oss ---
    def oss_src(idx):
        return f"{DATAAPP}/item_{idx:04d}/gpt_oss_response.md"

    copy_and_extract("oss", oss_src)

    # --- xhigh ---
    # Primary source: gpt55_full/item_XXXX_gpt5_5_response.md
    # Overlay for recovered items: use rerun md if exists, else the integrate answer directly
    # For excluded items: blank
    xhigh_rerun_dir = f"{DATAAPP}/gpt55_rerun_refusals"

    def xhigh_src(idx):
        padded = f"{idx:04d}"
        str_idx = str(idx)
        # Use rerun file if it exists for this item
        rerun_file = f"{xhigh_rerun_dir}/item_{padded}_gpt5_5_rerun.md"
        if os.path.exists(rerun_file):
            return rerun_file
        return f"{DATAAPP}/gpt55_full/item_{padded}_gpt5_5_response.md"

    # For excluded items, pass them as blanks via overlay
    xhigh_overlay = dict(xhigh_integrate)  # str_id -> answer (already extracted)
    for excl_id in xhigh_excluded:
        xhigh_overlay[excl_id] = ""  # force blank, skip extraction

    copy_and_extract("xhigh", xhigh_src, rerun_overlay=xhigh_overlay)

    # Spot-check: verify no answers.csv value is a placeholder
    print("\n=== Placeholder audit ===")
    for llm in ["sonnet", "gpt4", "oss", "xhigh"]:
        csv_path = os.path.join(TEACHERS_DIR, llm, "answers.csv")
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            hits = [(r["id"], r["answer"]) for r in reader if is_placeholder(r["answer"])]
        if hits:
            print(f"  {llm} PLACEHOLDER HITS: {hits[:5]}")
        else:
            print(f"  {llm}: clean (0 placeholders)")

    # gpt4 items 267-449 diagnostic
    print("\n=== gpt4 items 267-449 diagnostic ===")
    csv_path = os.path.join(TEACHERS_DIR, "gpt4", "answers.csv")
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows_267_449 = [(int(r["id"]), r["answer"]) for r in reader
                        if 267 <= int(r["id"]) <= 449]
    blank_in_range = [(i, a) for i, a in rows_267_449 if not a]
    filled_in_range = [(i, a) for i, a in rows_267_449 if a]
    print(f"  Items 267-449: {len(rows_267_449)} total")
    print(f"  Filled: {len(filled_in_range)}  Blank: {len(blank_in_range)}")
    print(f"  Blank items: {[i for i,_ in blank_in_range][:20]}")

    # Spot-check 5 items across teachers
    print("\n=== Spot-checks (item 0, 1, 100, 500, 942) ===")
    spot_ids = [0, 1, 100, 500, 942]
    for llm in ["sonnet", "gpt4", "oss", "xhigh"]:
        csv_path = os.path.join(TEACHERS_DIR, llm, "answers.csv")
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            rows_map = {int(r["id"]): r["answer"] for r in reader}
        vals = [repr(rows_map.get(i, "MISSING")[:30]) for i in spot_ids]
        print(f"  {llm}: {vals}")

    print("\nDone.")


if __name__ == "__main__":
    main()

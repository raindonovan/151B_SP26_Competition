#!/usr/bin/env python3
"""build_master_tracker_v2.py — Fill per-run columns into master_item_tracker.csv.
Run on tnr-0 where local JSONL files exist.

Usage:
    cd /home/ubuntu/151B_SP26_Competition
    python3 scripts/build_master_tracker_v2.py
"""
import csv, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path("/home/ubuntu/151B_SP26_Competition")

def extract_last_boxed(text):
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

def normalize_answer(s):
    if not s: return ""
    s = str(s).strip()
    if s.startswith("$") and s.endswith("$") and len(s) >= 2: s = s[1:-1].strip()
    s = s.replace("\\dfrac","\\frac").replace("\\left","").replace("\\right","")
    s = re.sub(r"\\[,;!]"," ",s)
    s = re.sub(r"\s+"," ",s).strip()
    return s

def process_jsonl(path):
    results = {}
    if not path.exists():
        print(f"  SKIP (not found): {path}")
        return results
    with open(path) as f:
        for line in f:
            if not line.strip(): continue
            item = json.loads(line)
            iid = item.get("id", item.get("item_id"))
            if "voted_normalized" in item:
                results[iid] = {
                    "voted": item["voted_normalized"],
                    "vote_frac": f"{item['n_votes']}/{item['n_samples_total']}",
                    "truncated": sum(1 for s in item.get("samples",[]) if len(s)>40000),
                }
            elif "samples" in item:
                samples = item["samples"]
                boxed = [normalize_answer(extract_last_boxed(s)) for s in samples]
                nonempty = [b for b in boxed if b]
                if nonempty:
                    votes = Counter(nonempty)
                    top_ans, top_cnt = votes.most_common(1)[0]
                    results[iid] = {"voted":top_ans, "vote_frac":f"{top_cnt}/{len(samples)}",
                                    "truncated":sum(1 for s in samples if len(s)>40000)}
                else:
                    results[iid] = {"voted":"", "vote_frac":f"0/{len(samples)}", "truncated":0}
            else:
                resp = item.get("response", item.get("text",""))
                ans = normalize_answer(extract_last_boxed(resp))
                results[iid] = {"voted":ans, "vote_frac":"1/1", "truncated":0}
    print(f"  {path.name}: {len(results)} items")
    return results

def read_submission(path):
    results = {}
    if not path.exists(): return results
    with open(path) as f:
        first = f.readline()
        if first.startswith("version https://git-lfs"):
            print(f"  SKIP LFS: {path.name}")
            return results
        f.seek(0)
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            if len(row) >= 2:
                try: results[int(row[0])] = row[1]
                except: pass
    return results

def main():
    print("=== Master Item Tracker V2 ===\n")
    tracker = ROOT / "results" / "master_item_tracker.csv"
    if not tracker.exists():
        print(f"ERROR: {tracker} not found. Run git pull first.")
        sys.exit(1)

    with open(tracker) as f:
        reader = csv.DictReader(f)
        v1_cols = list(reader.fieldnames)
        items = {}
        for row in reader:
            iid = int(row["id"])
            items[iid] = dict(row)
    print(f"V1: {len(items)} items, {len(v1_cols)} cols")

    # Run10
    print("\nrun10:")
    run10 = process_jsonl(ROOT/"results"/"run10_v3perslot_private943_tok16384.jsonl")
    for iid, d in run10.items():
        if iid in items:
            items[iid]["run10_voted"] = d["voted"]
            items[iid]["run10_vote_frac"] = d["vote_frac"]
            items[iid]["run10_truncated"] = str(d["truncated"])

    # NoThinking
    print("nothinking:")
    nothink = process_jsonl(ROOT/"results"/"hybrid"/"tnr-B"/"nothinking_full_943_20260527T000129Z.jsonl")
    for iid, d in nothink.items():
        if iid in items:
            items[iid]["nothink_voted"] = d["voted"]
            items[iid]["nothink_vote_frac"] = d["vote_frac"]
            items[iid]["nothink_truncated"] = str(d["truncated"])

    # Hardest-30 runs (if exist)
    for label, pattern in [
        ("a2_h30", "results/hybrid/tnr-A/a2_serial_sc16_hardest30_*.jsonl"),
        ("j2_h30", "results/hybrid/tnr-A/sc16_hardest30_*.jsonl"),
    ]:
        matches = sorted(ROOT.glob(pattern))
        if matches:
            print(f"{label}:")
            data = process_jsonl(matches[-1])
            for iid, d in data.items():
                if iid in items:
                    items[iid][f"{label}_voted"] = d["voted"]
                    items[iid][f"{label}_vote_frac"] = d["vote_frac"]

    # Submissions
    print("\nsubmissions:")
    sub_dir = ROOT / "submissions"
    for name in sorted(sub_dir.glob("*.csv")) if sub_dir.exists() else []:
        data = read_submission(name)
        if data:
            col = f"sub_{name.stem}"
            for iid, ans in data.items():
                if iid in items: items[iid][col] = ans
            print(f"  {name.name}: {len(data)} items")

    # Rescue JSONL (if committed)
    rescue_files = sorted(ROOT.glob("results/no_box_rescue_*.jsonl"))
    if rescue_files:
        print(f"\nrescue:")
        rdata = process_jsonl(rescue_files[-1])
        for iid, d in rdata.items():
            if iid in items:
                items[iid]["rescue_voted_v2"] = d["voted"]
                items[iid]["rescue_vote_frac_v2"] = d["vote_frac"]

    # Compute action_needed flag
    for iid, item in items.items():
        flags = []
        if item.get("no_box_item") == "True" and not item.get("rescue_answer"):
            flags.append("no_box_unrescued")
        if item.get("run10_truncated","0") not in ("0",""):
            try:
                if int(item["run10_truncated"]) >= 3: flags.append("heavy_truncation")
            except: pass
        if item.get("wolfram_confidence") == "DISPUTED":
            flags.append("disputed_override")
        if item.get("teacher_agree_count","0") in ("0","1") and not item.get("wolfram_override"):
            flags.append("low_teacher_agree")
        items[iid]["action_flags"] = "|".join(flags) if flags else ""

    # Collect all columns
    all_cols = set()
    for item in items.values():
        all_cols.update(item.keys())
    # Order: V1 cols first, then new cols sorted
    new_cols = sorted(all_cols - set(v1_cols))
    v2_cols = v1_cols + new_cols

    with open(tracker, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=v2_cols, extrasaction="ignore")
        w.writeheader()
        for iid in sorted(items.keys()):
            w.writerow(items[iid])

    print(f"\nV2 written: {len(items)} rows, {len(v2_cols)} cols")
    print(f"New columns ({len(new_cols)}): {new_cols}")

    # Coverage stats
    for col in ["run10_voted","nothink_voted"]:
        cnt = sum(1 for i in items.values() if i.get(col))
        print(f"  {col}: {cnt}/943")

if __name__ == "__main__":
    main()

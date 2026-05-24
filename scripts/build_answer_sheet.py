#!/usr/bin/env python3
"""
build_answer_sheet.py — Unified Answer Sheet Builder

THE SINGLE MOST IMPORTANT SCRIPT IN THE COMPETITION.

Takes all Kaggle submission CSVs + teacher consensus, and produces:
1. answer_matrix.json — per-item × per-submission extracted answers (raw data)
2. unified_answer_sheet.csv — final best answer per item with 5-tier confidence
3. validation_report.txt — sanity checks against known Kaggle scores

Methodology:

"""

import argparse
import csv
import json
import math
import os
import re
import sys
from collections import defaultdict, Counter
from pathlib import Path

SUBMISSION_REGISTRY = [
    ("run14b_v3filtered.csv",           0.646, "Base V0 SC=8 32K V3-filter — BEST"),
    ("run14b_sc8_v1.csv",               0.639, "Base V0 SC=8 32K no filter"),
    ("run09sc8_v1_private943.csv",      0.614, "Base V1 SC=8 16K — ANCHOR"),
    ("run09sc8_format_fixed.csv",       0.611, "Run09 + format fix"),
    ("run08v2_v1_private943.csv",       0.586, "Base V1 SC=8"),
    ("diagnostic_sub_a.csv",            0.505, "DiagA: teacher on R1+R2"),
    ("sftv3_epoch8_sc1_final.csv",      0.452, "SFT v3 epoch8 SC=1 greedy"),
    ("run09sc8_probe_b_reversed.csv",   0.438, "Run09 reversed multi-answer order"),
    ("run10_v3perslot_private943.csv",  0.424, "V3 per-slot format"),
    ("expA_run08_perslot_perturbed.csv",0.420, "Per-slot format experiment"),
    ("D_05_07_numina_d.csv",            0.310, "DiagD"),
    ("diagnostic_sub_c.csv",            0.222, "DiagC"),
    ("post_filtered_b.csv",             0.151, "DiagB"),
    ("f_today_F.csv",                   0.137, "DiagF"),
    ("E_05_13_h100run_e.csv",           0.028, "DiagE: all-placeholder baseline"),
    ("g_epoch8_lora_G.csv",             0.017, "Broken lora diagnostic"),
]

def extract_last_boxed(text):
    positions = []
    i = 0
    while i < len(text):
        pos = text.find("\\boxed{", i)
        if pos == -1:
            break
        positions.append(pos)
        i = pos + 7
    if not positions:
        return None
    start = positions[-1] + 7
    depth = 1
    j = start
    while j < len(text) and depth > 0:
        if text[j] == "{": depth += 1
        elif text[j] == "}": depth -= 1
        j += 1
    if depth == 0:
        return text[start:j-1].strip()
    return text[start:].strip() if text[start:].strip() else None

def extract_answer_from_response(response):
    if not response or not response.strip():
        return ""
    response = response.strip()
    boxed = extract_last_boxed(response)
    if boxed:
        return boxed
    if "PLACEHOLDER" in response: return ""
    if response == "INVALID": return ""
    if response == "77777777.77777": return ""
    if response == "W": return ""
    if len(response) < 500:
        return response.strip()
    return ""

def load_submission_csv(filepath):
    answers = {}
    with open(filepath, newline='', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        if 'response' in columns: ans_col = 'response'
        elif 'answer' in columns: ans_col = 'answer'
        elif 'prediction' in columns: ans_col = 'prediction'
        else:
            print(f"  WARNING: Unknown columns {columns} in {filepath}", file=sys.stderr)
            return answers
        for row in reader:
            try: item_id = int(row['id'])
            except (ValueError, KeyError): continue
            raw = row.get(ans_col, "")
            answers[item_id] = extract_answer_from_response(raw)
    return answers

def normalize_answer(answer, item_type="unknown"):
    if not answer: return ""
    s = answer.strip()
    if s.startswith("$") and s.endswith("$"): s = s[1:-1].strip()
    s = s.replace("\\,", " ").replace("\\;", " ").replace("\\ ", " ").replace("\\quad", " ")
    s = re.sub(r'\\text\s*\{[^}]{1,30}\}\s*$', '', s).strip()
    s = s.replace("\\dfrac", "\\frac")
    s = re.sub(r'\s*,\s*', ', ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def answers_equivalent(a, b):
    if a == b: return True
    try:
        va, vb = float(a), float(b)
        if abs(va - vb) < 1e-6: return True
    except (ValueError, OverflowError): pass
    def eval_frac(s):
        m = re.match(r'\\frac\{(\-?\d+)\}\{(\-?\d+)\}', s)
        if m: return float(m.group(1)) / float(m.group(2))
        m = re.match(r'(\-?\d+)/(\-?\d+)$', s)
        if m: return float(m.group(1)) / float(m.group(2))
        return None
    fa, fb = eval_frac(a), eval_frac(b)
    if fa is not None and fb is not None and abs(fa - fb) < 1e-6: return True
    if fa is not None:
        try:
            if abs(fa - float(b)) < 1e-6: return True
        except (ValueError, OverflowError): pass
    if fb is not None:
        try:
            if abs(float(a) - fb) < 1e-6: return True
        except (ValueError, OverflowError): pass
    return False

def group_equivalent_answers(candidates):
    groups = []
    for norm_ans, sub_name, score in candidates:
        if not norm_ans: continue
        matched = False
        for i, (canonical, members) in enumerate(groups):
            if answers_equivalent(norm_ans, canonical):
                members.append((sub_name, score))
                if score > max(s for _, s in members[:-1]):
                    groups[i] = (norm_ans, members)
                matched = True
                break
        if not matched:
            groups.append((norm_ans, [(sub_name, score)]))
    return {canonical: members for canonical, members in groups}

def bayesian_vote(item_id, submission_answers, submission_scores, item_type="unknown"):
    candidates = []
    for sub_name, raw_ans in submission_answers.items():
        norm_ans = normalize_answer(raw_ans, item_type)
        if norm_ans:
            score = submission_scores.get(sub_name, 0.5)
            candidates.append((norm_ans, sub_name, score))
    if not candidates: return "", 0.0, {}
    groups = group_equivalent_answers(candidates)
    if not groups: return "", 0.0, {}
    active_subs = {sub_name for sub_name, raw_ans in submission_answers.items()
                   if normalize_answer(raw_ans, item_type)}
    log_posteriors = {}
    for candidate_X, supporters in groups.items():
        supporter_names = {name for name, _ in supporters}
        log_p = 0.0
        for sub_name in active_subs:
            score = max(0.01, min(0.99, submission_scores.get(sub_name, 0.5)))
            if sub_name in supporter_names:
                log_p += math.log(score)
            else:
                log_p += math.log(1 - score)
        log_posteriors[candidate_X] = log_p
    if not log_posteriors: return "", 0.0, {}
    max_log = max(log_posteriors.values())
    probs = {X: math.exp(lp - max_log) for X, lp in log_posteriors.items()}
    total = sum(probs.values())
    if total == 0: return "", 0.0, {}
    probs = {X: p / total for X, p in probs.items()}
    best_X = max(probs, key=probs.get)
    return best_X, probs[best_X], probs

def assign_tier(confidence):
    if confidence >= 0.90: return 1
    elif confidence >= 0.80: return 2
    elif confidence >= 0.60: return 3
    elif confidence >= 0.40: return 4
    else: return 5

def load_teacher_consensus(manifest_path):
    teachers = {}
    with open(manifest_path) as f:
        for line in f:
            item = json.loads(line)
            item_id = int(item.get("id", -1))
            answers = {}
            for key, name in [("sonnet_answer_raw","sonnet"),("gpt5_4_answer_raw","gpt5_4"),("gpt_oss_answer_raw","gpt_oss")]:
                ans = item.get(key, "").strip()
                if ans: answers[name] = ans
            if not answers:
                teachers[item_id] = {"consensus": "", "agreement": 0.0, "answers": {}}
                continue
            norm_answers = {name: normalize_answer(ans) for name, ans in answers.items()}
            vote_counts = Counter(norm_answers.values())
            best_ans = vote_counts.most_common(1)[0][0]
            agreement = vote_counts.most_common(1)[0][1] / len(norm_answers)
            raw_consensus = ""
            for name in ["sonnet", "gpt5_4", "gpt_oss"]:
                if name in norm_answers and norm_answers[name] == best_ans:
                    raw_consensus = answers[name]
                    break
            teachers[item_id] = {"consensus": raw_consensus, "agreement": agreement, "answers": answers}
    return teachers

def validate_against_kaggle(answer_sheet, submission_answers, submission_scores):
    report = ["=== VALIDATION: Answer Sheet vs Kaggle Scores ===", ""]
    for sub_name in sorted(submission_scores, key=submission_scores.get, reverse=True):
        actual_score = submission_scores[sub_name]
        sub_ans = submission_answers.get(sub_name, {})
        agree, total_comparable = 0, 0
        for item_id in range(943):
            our_ans = normalize_answer(answer_sheet.get(item_id, ""))
            their_ans = normalize_answer(sub_ans.get(item_id, ""))
            if our_ans and their_ans:
                total_comparable += 1
                if answers_equivalent(our_ans, their_ans): agree += 1
        predicted_score = agree / 943 if total_comparable > 0 else 0
        delta = predicted_score - actual_score
        status = "PASS" if abs(delta) < 0.05 else "WARN" if abs(delta) < 0.10 else "FAIL"
        report.append(f"  {status} {sub_name:<42} Kaggle={actual_score:.3f} Agree={agree}/{total_comparable} Predicted={predicted_score:.3f} D={delta:+.3f}")
    return report

def main():
    p = argparse.ArgumentParser(description="Build Unified Answer Sheet")
    p.add_argument("--submissions-dir", required=True)
    p.add_argument("--manifest", default=None)
    p.add_argument("--data", default=None)
    p.add_argument("--output-dir", default="results/answer_sheet")
    args = p.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("STEP 1: Loading all submission CSVs")
    print("=" * 70)
    submission_answers = {}
    submission_scores = {}
    for filename, score, notes in SUBMISSION_REGISTRY:
        filepath = os.path.join(args.submissions_dir, filename)
        if not os.path.exists(filepath):
            print(f"  X MISSING: {filename}")
            continue
        print(f"  Loading {filename} (score={score:.3f})...", end="")
        answers = load_submission_csv(filepath)
        n_answers = sum(1 for a in answers.values() if a)
        print(f" {n_answers}/943 items with answers")
        sub_name = filename.replace(".csv", "")
        submission_answers[sub_name] = answers
        submission_scores[sub_name] = score
    print(f"\nTotal submissions loaded: {len(submission_answers)}")

    print("\n" + "=" * 70)
    print("STEP 2: Loading teacher consensus (xhigh EXCLUDED)")
    print("=" * 70)
    teachers = {}
    if args.manifest and os.path.exists(args.manifest):
        teachers = load_teacher_consensus(args.manifest)
        print(f"  Loaded teacher data for {len(teachers)} items")
    else:
        print("  No manifest — teacher consensus not available")

    print("\n" + "=" * 70)
    print("STEP 3: Loading question types")
    print("=" * 70)
    item_types = {}
    if args.data and os.path.exists(args.data):
        with open(args.data) as f:
            for line in f:
                item = json.loads(line)
                item_types[item["id"]] = {"type": "mcq" if item.get("options") else "free"}
        print(f"  Loaded types for {len(item_types)} items")

    print("\n" + "=" * 70)
    print(f"STEP 4: Building answer matrix (943 x {len(submission_answers)})")
    print("=" * 70)
    answer_matrix = {}
    for item_id in range(943):
        item_answers = {}
        for sub_name, answers in submission_answers.items():
            raw = answers.get(item_id, "")
            norm = normalize_answer(raw)
            if norm: item_answers[sub_name] = norm
        answer_matrix[item_id] = item_answers
    matrix_path = output_dir / "answer_matrix.json"
    with open(matrix_path, "w") as f:
        json.dump({str(k): v for k, v in answer_matrix.items()}, f, indent=1)
    print(f"  Saved: {matrix_path}")

    print("\n" + "=" * 70)
    print("STEP 5: Score-weighted Bayesian voting")
    print("=" * 70)
    results = []
    for item_id in range(943):
        item_sub_answers = {}
        for sub_name, answers in submission_answers.items():
            raw = answers.get(item_id, "")
            if raw: item_sub_answers[sub_name] = raw
        item_type = item_types.get(item_id, {}).get("type", "unknown")
        best_answer, confidence, posteriors = bayesian_vote(item_id, item_sub_answers, submission_scores, item_type)
        tier = assign_tier(confidence)
        teacher_data = teachers.get(item_id, {})
        teacher_ans = normalize_answer(teacher_data.get("consensus", ""))
        teacher_agrees = answers_equivalent(normalize_answer(best_answer), teacher_ans) if teacher_ans and best_answer else None
        adjusted_confidence = confidence
        if teacher_agrees is True:
            adjusted_confidence = min(0.99, confidence + 0.05)
        elif teacher_agrees is False and teacher_data.get("agreement", 0) >= 1.0:
            adjusted_confidence = max(0.10, confidence - 0.10)
        adjusted_tier = assign_tier(adjusted_confidence)
        runner_up, runner_up_conf = "", 0.0
        if len(posteriors) > 1:
            sorted_post = sorted(posteriors.items(), key=lambda x: -x[1])
            if len(sorted_post) > 1:
                runner_up = sorted_post[1][0]
                runner_up_conf = sorted_post[1][1]
        n_supporting, n_with_answer = 0, 0
        for sub_name, raw_ans in item_sub_answers.items():
            norm = normalize_answer(raw_ans, item_type)
            if norm:
                n_with_answer += 1
                if answers_equivalent(norm, normalize_answer(best_answer)): n_supporting += 1
        results.append({
            "item_id": item_id, "best_answer": best_answer,
            "raw_confidence": round(confidence, 4),
            "adjusted_confidence": round(adjusted_confidence, 4),
            "tier": adjusted_tier,
            "runner_up": runner_up, "runner_up_conf": round(runner_up_conf, 4),
            "n_supporting": n_supporting, "n_with_answer": n_with_answer,
            "teacher_consensus": teacher_data.get("consensus", ""),
            "teacher_agrees": str(teacher_agrees) if teacher_agrees is not None else "N/A",
            "teacher_agreement": round(teacher_data.get("agreement", 0), 2),
        })

    print("\n" + "=" * 70)
    print("STEP 6: Saving unified answer sheet")
    print("=" * 70)
    sheet_path = output_dir / "unified_answer_sheet.csv"
    with open(sheet_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "item_id","best_answer","raw_confidence","adjusted_confidence",
            "tier","runner_up","runner_up_conf","n_supporting","n_with_answer",
            "teacher_consensus","teacher_agrees","teacher_agreement"])
        writer.writeheader()
        writer.writerows(results)
    print(f"  Saved: {sheet_path}")
    adjusted_tier_counts = Counter(r["tier"] for r in results)
    labels = {1:"LOCK ZONE",2:"High conf",3:"Medium",4:"Low conf",5:"INVESTIGATION"}
    print(f"\n  Tier distribution:")
    for tier in range(1, 6):
        count = adjusted_tier_counts[tier]
        print(f"    Tier {tier} ({labels[tier]:>13}): {count:>4} items ({count/943*100:.1f}%)")

    print("\n" + "=" * 70)
    print("STEP 7: Validation against Kaggle scores")
    print("=" * 70)
    answer_sheet = {r["item_id"]: r["best_answer"] for r in results}
    validation = validate_against_kaggle(answer_sheet, submission_answers, submission_scores)
    for line in validation: print(line)
    report_path = output_dir / "validation_report.txt"
    with open(report_path, "w") as f:
        f.write("\n".join(validation))
        f.write(f"\n\nTier distribution:\n")
        for tier in range(1, 6):
            f.write(f"  Tier {tier}: {adjusted_tier_counts[tier]} items ({adjusted_tier_counts[tier]/943*100:.1f}%)\n")
    print(f"\n  Saved: {report_path}")
    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

if __name__ == "__main__":
    main()
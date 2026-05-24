#!/usr/bin/env python3
"""
build_answer_sheet.py — Unified Answer Sheet Builder v2

10 submissions (diagnostics B-F excluded due to format mismatch noise).
Score-weighted Bayesian + teacher consensus (xhigh excluded).
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
    # EXCLUDED: DiagB(0.151), DiagC(0.222), DiagD(0.310), DiagE(0.028),
    # DiagF(0.137), lora_G(0.017) — format mismatch causes noise
]


def extract_last_boxed(text):
    positions = []
    i = 0
    while i < len(text):
        pos = text.find("\\boxed{", i)
        if pos == -1: break
        positions.append(pos)
        i = pos + 7
    if not positions: return None
    start = positions[-1] + 7
    depth = 1
    j = start
    while j < len(text) and depth > 0:
        if text[j] == "{": depth += 1
        elif text[j] == "}": depth -= 1
        j += 1
    if depth == 0: return text[start:j-1].strip()
    return text[start:].strip() if text[start:].strip() else None


def extract_answer_from_response(response):
    if not response or not response.strip(): return ""
    response = response.strip()
    boxed = extract_last_boxed(response)
    if boxed: return boxed
    if "PLACEHOLDER" in response: return ""
    if response == "INVALID": return ""
    if response == "77777777.77777": return ""
    if response == "W": return ""
    if len(response) < 500: return response.strip()
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
            print(f"  WARNING: Unknown columns {columns}", file=sys.stderr)
            return answers
        for row in reader:
            try: item_id = int(row['id'])
            except (ValueError, KeyError): continue
            answers[item_id] = extract_answer_from_response(row.get(ans_col, ""))
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
    return {c: m for c, m in groups}


def bayesian_vote(item_id, submission_answers, submission_scores, item_type="unknown"):
    candidates = []
    for sub_name, raw_ans in submission_answers.items():
        norm_ans = normalize_answer(raw_ans, item_type)
        if norm_ans:
            candidates.append((norm_ans, sub_name, submission_scores.get(sub_name, 0.5)))
    if not candidates: return "", 0.0, {}
    groups = group_equivalent_answers(candidates)
    if not groups: return "", 0.0, {}
    active_subs = {sn for sn, ra in submission_answers.items() if normalize_answer(ra, item_type)}
    log_posteriors = {}
    for candidate_X, supporters in groups.items():
        supporter_names = {name for name, _ in supporters}
        log_p = 0.0
        for sub_name in active_subs:
            score = max(0.01, min(0.99, submission_scores.get(sub_name, 0.5)))
            log_p += math.log(score) if sub_name in supporter_names else math.log(1 - score)
        log_posteriors[candidate_X] = log_p
    if not log_posteriors: return "", 0.0, {}
    max_log = max(log_posteriors.values())
    probs = {X: math.exp(lp - max_log) for X, lp in log_posteriors.items()}
    total = sum(probs.values())
    if total == 0: return "", 0.0, {}
    probs = {X: p / total for X, p in probs.items()}
    best_X = max(probs, key=probs.get)
    return best_X, probs[best_X], probs


def assign_tier(c):
    if c >= 0.90: return 1
    if c >= 0.80: return 2
    if c >= 0.60: return 3
    if c >= 0.40: return 4
    return 5


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
                teachers[item_id] = {"consensus":"","agreement":0.0,"answers":{}}
                continue
            norm_answers = {n: normalize_answer(a) for n, a in answers.items()}
            vote_counts = Counter(norm_answers.values())
            best_ans = vote_counts.most_common(1)[0][0]
            agreement = vote_counts.most_common(1)[0][1] / len(norm_answers)
            raw_consensus = ""
            for n in ["sonnet","gpt5_4","gpt_oss"]:
                if n in norm_answers and norm_answers[n] == best_ans:
                    raw_consensus = answers[n]; break
            teachers[item_id] = {"consensus":raw_consensus,"agreement":agreement,"answers":answers}
    return teachers


def validate_against_kaggle(answer_sheet, submission_answers, submission_scores):
    report = ["=== VALIDATION: Answer Sheet vs Kaggle Scores ===",""]
    for sub_name in sorted(submission_scores, key=submission_scores.get, reverse=True):
        actual = submission_scores[sub_name]
        sub_ans = submission_answers.get(sub_name, {})
        agree = total = 0
        for iid in range(943):
            ours = normalize_answer(answer_sheet.get(iid, ""))
            theirs = normalize_answer(sub_ans.get(iid, ""))
            if ours and theirs:
                total += 1
                if answers_equivalent(ours, theirs): agree += 1
        pred = agree / 943 if total > 0 else 0
        d = pred - actual
        s = "PASS" if abs(d)<0.05 else "WARN" if abs(d)<0.10 else "FAIL"
        report.append(f"  {s} {sub_name:<42} Kaggle={actual:.3f} Agree={agree}/{total} Pred={pred:.3f} D={d:+.3f}")
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--submissions-dir", required=True)
    p.add_argument("--manifest", default=None)
    p.add_argument("--data", default=None)
    p.add_argument("--output-dir", default="results/answer_sheet")
    args = p.parse_args()
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)

    print("="*70); print("STEP 1: Loading submissions"); print("="*70)
    sub_answers, sub_scores = {}, {}
    for fn, score, notes in SUBMISSION_REGISTRY:
        fp = os.path.join(args.submissions_dir, fn)
        if not os.path.exists(fp):
            print(f"  X MISSING: {fn}"); continue
        print(f"  Loading {fn} ({score:.3f})...", end="")
        ans = load_submission_csv(fp)
        n = sum(1 for a in ans.values() if a)
        print(f" {n}/943 answers")
        sn = fn.replace(".csv","")
        sub_answers[sn] = ans; sub_scores[sn] = score
    print(f"\nLoaded: {len(sub_answers)} submissions")

    print("\n"+"="*70); print("STEP 2: Teacher consensus (xhigh EXCLUDED)"); print("="*70)
    teachers = {}
    manifest_found = False
    if args.manifest and os.path.exists(args.manifest):
        teachers = load_teacher_consensus(args.manifest)
        manifest_found = True
        n3 = sum(1 for t in teachers.values() if t["agreement"] >= 1.0)
        print(f"  Loaded {len(teachers)} items, {n3} with 3/3 agreement")
    else:
        print(f"  MANIFEST NOT FOUND at: {args.manifest}")
        # Try fallback paths
        for fallback in ["data/dataset_manifest.jsonl",
                         "../DataApp/dataapp_outputs/dataset_manifest.jsonl",
                         os.path.expanduser("~/DataApp/dataapp_outputs/dataset_manifest.jsonl")]:
            if os.path.exists(fallback):
                print(f"  FOUND FALLBACK: {fallback}")
                teachers = load_teacher_consensus(fallback)
                manifest_found = True
                n3 = sum(1 for t in teachers.values() if t["agreement"] >= 1.0)
                print(f"  Loaded {len(teachers)} items, {n3} with 3/3 agreement")
                break
        if not manifest_found:
            print("  NO MANIFEST FOUND — teacher consensus unavailable")

    print("\n"+"="*70); print("STEP 3: Question types"); print("="*70)
    item_types = {}
    if args.data and os.path.exists(args.data):
        with open(args.data) as f:
            for line in f:
                item = json.loads(line)
                item_types[item["id"]] = {"type":"mcq" if item.get("options") else "free"}
        print(f"  {len(item_types)} items")

    print("\n"+"="*70)
    print(f"STEP 4: Answer matrix (943 x {len(sub_answers)})"); print("="*70)
    answer_matrix = {}
    for iid in range(943):
        ia = {}
        for sn, ans in sub_answers.items():
            norm = normalize_answer(ans.get(iid,""))
            if norm: ia[sn] = norm
        answer_matrix[iid] = ia
    mp = out/"answer_matrix.json"
    with open(mp,"w") as f:
        json.dump({str(k):v for k,v in answer_matrix.items()}, f, indent=1)
    print(f"  Saved: {mp}")

    print("\n"+"="*70); print("STEP 5: Bayesian voting"); print("="*70)
    results = []
    for iid in range(943):
        isa = {sn: ans.get(iid,"") for sn, ans in sub_answers.items() if ans.get(iid,"")}
        it = item_types.get(iid,{}).get("type","unknown")
        best, conf, posts = bayesian_vote(iid, isa, sub_scores, it)
        tier = assign_tier(conf)
        td = teachers.get(iid, {})
        ta = normalize_answer(td.get("consensus",""))
        tagree = answers_equivalent(normalize_answer(best), ta) if ta and best else None
        adj = conf
        if tagree is True: adj = min(0.99, conf+0.05)
        elif tagree is False and td.get("agreement",0) >= 1.0: adj = max(0.10, conf-0.10)
        atier = assign_tier(adj)
        ru, ruc = "", 0.0
        if len(posts)>1:
            sp = sorted(posts.items(), key=lambda x:-x[1])
            ru, ruc = sp[1][0], sp[1][1]
        ns = nw = 0
        for sn, ra in isa.items():
            norm = normalize_answer(ra, it)
            if norm:
                nw += 1
                if answers_equivalent(norm, normalize_answer(best)): ns += 1
        results.append({
            "item_id":iid,"best_answer":best,
            "raw_confidence":round(conf,4),"adjusted_confidence":round(adj,4),
            "tier":atier,"runner_up":ru,"runner_up_conf":round(ruc,4),
            "n_supporting":ns,"n_with_answer":nw,
            "teacher_consensus":td.get("consensus",""),
            "teacher_agrees":str(tagree) if tagree is not None else "N/A",
            "teacher_agreement":round(td.get("agreement",0),2)})

    print("\n"+"="*70); print("STEP 6: Save answer sheet"); print("="*70)
    sp = out/"unified_answer_sheet.csv"
    with open(sp,"w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "item_id","best_answer","raw_confidence","adjusted_confidence",
            "tier","runner_up","runner_up_conf","n_supporting","n_with_answer",
            "teacher_consensus","teacher_agrees","teacher_agreement"])
        w.writeheader(); w.writerows(results)
    print(f"  Saved: {sp}")
    tc = Counter(r["tier"] for r in results)
    labels = {1:"LOCK",2:"High",3:"Med",4:"Low",5:"INVEST"}
    print("\n  Tiers:")
    for t in range(1,6):
        print(f"    T{t} ({labels[t]:>6}): {tc[t]:>4} ({tc[t]/943*100:.1f}%)")

    # Teacher stats
    ta_counts = Counter(r["teacher_agrees"] for r in results)
    print(f"\n  Teacher agreement: {dict(ta_counts)}")

    print("\n"+"="*70); print("STEP 7: Validation"); print("="*70)
    sheet = {r["item_id"]:r["best_answer"] for r in results}
    val = validate_against_kaggle(sheet, sub_answers, sub_scores)
    for line in val: print(line)
    rp = out/"validation_report.txt"
    with open(rp,"w") as f:
        f.write("\n".join(val))
        f.write(f"\n\nTiers:\n")
        for t in range(1,6): f.write(f"  T{t}: {tc[t]} ({tc[t]/943*100:.1f}%)\n")
        f.write(f"\nTeacher agreement: {dict(ta_counts)}\n")
    print(f"\n  Saved: {rp}")
    print("\n"+"="*70); print("DONE"); print("="*70)


if __name__ == "__main__":
    main()

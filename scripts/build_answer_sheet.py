#!/usr/bin/env python3
"""
build_answer_sheet.py — Unified Answer Sheet Builder

THE SINGLE MOST IMPORTANT SCRIPT IN THE COMPETITION.

Takes all Kaggle submission CSVs + teacher consensus, and produces:
1. answer_matrix.json — per-item × per-submission extracted answers (raw data)
2. unified_answer_sheet.csv — final best answer per item with 5-tier confidence
import csv
import json
import math
import os
import re
import sys
from collections import Counter
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
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    if depth == 0:
        return text[start:j - 1].strip()
    return text[start:].strip() if text[start:].strip() else None


def extract_answer_from_response(response):
    if not response or not response.strip():
        return ""
    response = response.strip()
    boxed = extract_last_boxed(response)
    if boxed:
        return boxed
    if "PLACEHOLDER" in response:
        return ""
    if response in ("INVALID", "77777777.77777", "W"):
        return ""
    if len(response) < 500:
        return response.strip()
    return ""


def load_submission_csv(filepath):
    answers = {}
    with open(filepath, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        def main():
            p = argparse.ArgumentParser()
            p.add_argument("--submissions-dir", required=True)
            p.add_argument("--manifest", default=None)
            p.add_argument("--data", default=None)
            p.add_argument("--output-dir", default="results/answer_sheet")
            args = p.parse_args()
            out = Path(args.output_dir)
            out.mkdir(parents=True, exist_ok=True)

            print("=" * 70)
            print("STEP 1: Loading submissions")
            print("=" * 70)
            sub_answers, sub_scores = {}, {}
            for fn, score, notes in SUBMISSION_REGISTRY:
                fp = os.path.join(args.submissions_dir, fn)
                if not os.path.exists(fp):
                    print(f"  X MISSING: {fn}")
                    continue
                print(f"  Loading {fn} ({score:.3f})...", end="")
                ans = load_submission_csv(fp)
                n = sum(1 for a in ans.values() if a)
                print(f" {n}/943 answers")
                sn = fn.replace(".csv", "")
                sub_answers[sn] = ans
                sub_scores[sn] = score
            print(f"\nLoaded: {len(sub_answers)} submissions")

            print("\n" + "=" * 70)
            print("STEP 2: Teacher consensus (xhigh EXCLUDED)")
            print("=" * 70)
            teachers = {}
            manifest_found = False
            if args.manifest and os.path.exists(args.manifest):
                teachers = load_teacher_consensus(args.manifest)
                manifest_found = True
                n3 = sum(1 for t in teachers.values() if t["agreement"] >= 1.0)
                print(f"  Loaded {len(teachers)} items, {n3} with 3/3 agreement")
            else:
                print(f"  MANIFEST NOT FOUND at: {args.manifest}")
                for fallback in [
                    "data/dataset_manifest.jsonl",
                    "../DataApp/dataapp_outputs/dataset_manifest.jsonl",
                    os.path.expanduser("~/DataApp/dataapp_outputs/dataset_manifest.jsonl"),
                ]:
                    if os.path.exists(fallback):
                        print(f"  FOUND FALLBACK: {fallback}")
                        teachers = load_teacher_consensus(fallback)
                        manifest_found = True
                        n3 = sum(1 for t in teachers.values() if t["agreement"] >= 1.0)
                        print(f"  Loaded {len(teachers)} items, {n3} with 3/3 agreement")
                        break
                if not manifest_found:
                    print("  NO MANIFEST FOUND — teacher consensus unavailable")

            print("\n" + "=" * 70)
            print("STEP 3: Question types")
            print("=" * 70)
            item_types = {}
            if args.data and os.path.exists(args.data):
                with open(args.data) as f:
                    for line in f:
                        item = json.loads(line)
                        item_types[item["id"]] = {"type": "mcq" if item.get("options") else "free"}
                print(f"  {len(item_types)} items")

            print("\n" + "=" * 70)
            print(f"STEP 4: Answer matrix (943 x {len(sub_answers)})")
            print("=" * 70)
            answer_matrix = {}
            for iid in range(943):
                ia = {}
                for sn, ans in sub_answers.items():
                    norm = normalize_answer(ans.get(iid, ""))
                    if norm:
                        ia[sn] = norm
                answer_matrix[iid] = ia
            mp = out / "answer_matrix.json"
            with open(mp, "w") as f:
                json.dump({str(k): v for k, v in answer_matrix.items()}, f, indent=1)
            print(f"  Saved: {mp}")

            print("\n" + "=" * 70)
            print("STEP 5: Bayesian voting")
            print("=" * 70)
            results = []
            for iid in range(943):
                isa = {sn: ans.get(iid, "") for sn, ans in sub_answers.items() if ans.get(iid, "")}
                it = item_types.get(iid, {}).get("type", "unknown")
                best, conf, posts = bayesian_vote(iid, isa, sub_scores, it)
                tier = assign_tier(conf)
                td = teachers.get(iid, {})
                ta = normalize_answer(td.get("consensus", ""))
                tagree = answers_equivalent(normalize_answer(best), ta) if ta and best else None
                adj = conf
                if tagree is True:
                    adj = min(0.99, conf + 0.05)
                elif tagree is False and td.get("agreement", 0) >= 1.0:
                    adj = max(0.10, conf - 0.10)
                atier = assign_tier(adj)
                ru, ruc = "", 0.0
                if len(posts) > 1:
                    sp = sorted(posts.items(), key=lambda x: -x[1])
                    ru, ruc = sp[1][0], sp[1][1]
                ns = nw = 0
                for sn, ra in isa.items():
                    norm = normalize_answer(ra, it)
                    if norm:
                        nw += 1
                        if answers_equivalent(norm, normalize_answer(best)):
                            ns += 1
                results.append(
                    {
                        "item_id": iid,
                        "best_answer": best,
                        "raw_confidence": round(conf, 4),
                        "adjusted_confidence": round(adj, 4),
                        "tier": atier,
                        "runner_up": ru,
                        "runner_up_conf": round(ruc, 4),
                        "n_supporting": ns,
                        "n_with_answer": nw,
                        "teacher_consensus": td.get("consensus", ""),
                        "teacher_agrees": str(tagree) if tagree is not None else "N/A",
                        "teacher_agreement": round(td.get("agreement", 0), 2),
                    }
                )

            print("\n" + "=" * 70)
            print("STEP 6: Save answer sheet")
            print("=" * 70)
            sp = out / "unified_answer_sheet.csv"
            with open(sp, "w", newline="") as f:
                w = csv.DictWriter(
                    f,
                    fieldnames=[
                        "item_id",
                        "best_answer",
                        "raw_confidence",
                        "adjusted_confidence",
                        "tier",
                        "runner_up",
                        "runner_up_conf",
                        "n_supporting",
                        "n_with_answer",
                        "teacher_consensus",
                        "teacher_agrees",
                        "teacher_agreement",
                    ],
                )
                w.writeheader()
                w.writerows(results)
            print(f"  Saved: {sp}")
            tc = Counter(r["tier"] for r in results)
            labels = {1: "LOCK", 2: "High", 3: "Med", 4: "Low", 5: "INVEST"}
            print("\n  Tiers:")
            for t in range(1, 6):
                print(f"    T{t} ({labels[t]:>6}): {tc[t]:>4} ({tc[t]/943*100:.1f}%)")

            ta_counts = Counter(r["teacher_agrees"] for r in results)
            print(f"\n  Teacher agreement: {dict(ta_counts)}")

            print("\n" + "=" * 70)
            print("STEP 7: Validation")
            print("=" * 70)
            sheet = {r["item_id"]: r["best_answer"] for r in results}
            val = validate_against_kaggle(sheet, sub_answers, sub_scores)
            for line in val:
                print(line)
            rp = out / "validation_report.txt"
            with open(rp, "w") as f:
                f.write("\n".join(val))
                f.write(f"\n\nTiers:\n")
                for t in range(1, 6):
                    f.write(f"  T{t}: {tc[t]} ({tc[t]/943*100:.1f}%)\n")
                f.write(f"\nTeacher agreement: {dict(ta_counts)}\n")
            print(f"\n  Saved: {rp}")
            print("\n" + "=" * 70)
            print("DONE")
            print("=" * 70)


        if __name__ == "__main__":
            main()
                ans = item.get(key, "").strip()
                if ans:
                    answers[name] = ans
            if not answers:
                teachers[item_id] = {"consensus": "", "agreement": 0.0, "answers": {}}
                continue
            norm_answers = {n: normalize_answer(a) for n, a in answers.items()}
            vote_counts = Counter(norm_answers.values())
            best_ans = vote_counts.most_common(1)[0][0]
            agreement = vote_counts.most_common(1)[0][1] / len(norm_answers)
            raw_consensus = ""
            for n in ["sonnet", "gpt5_4", "gpt_oss"]:
                if n in norm_answers and norm_answers[n] == best_ans:
                    raw_consensus = answers[n]
                    break
            teachers[item_id] = {"consensus": raw_consensus, "agreement": agreement, "answers": answers}
    return teachers


def validate_against_kaggle(answer_sheet, submission_answers, submission_scores):
    report = ["=== VALIDATION: Answer Sheet vs Kaggle Scores ===", ""]
    for sub_name in sorted(submission_scores, key=submission_scores.get, reverse=True):
        actual = submission_scores[sub_name]
        sub_ans = submission_answers.get(sub_name, {})
        agree = total = 0
        for iid in range(943):
            ours = normalize_answer(answer_sheet.get(iid, ""))
            theirs = normalize_answer(sub_ans.get(iid, ""))
            if ours and theirs:
                total += 1
                if answers_equivalent(ours, theirs):
                    agree += 1
        pred = agree / 943 if total > 0 else 0
        d = pred - actual
        s = "PASS" if abs(d) < 0.05 else "WARN" if abs(d) < 0.10 else "FAIL"
        report.append(f"  {s} {sub_name:<42} Kaggle={actual:.3f} Agree={agree}/{total} Pred={pred:.3f} D={d:+.3f}")
    return report
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
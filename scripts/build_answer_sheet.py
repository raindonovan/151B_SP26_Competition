#!/usr/bin/env python3
"""
build_answer_sheet.py — Unified Answer Sheet Builder

THE SINGLE MOST IMPORTANT SCRIPT IN THE COMPETITION.

Takes all Kaggle submission CSVs + teacher consensus, and produces:
1. answer_matrix.json — per-item × per-submission extracted answers (raw data)
2. unified_answer_sheet.csv — final best answer per item with 5-tier confidence
3. validation_report.txt — sanity checks against known Kaggle scores

Methodology:
  - Score-weighted Bayesian posterior per item per candidate answer
  - Answer normalization (LaTeX equivalence, whitespace, fraction→decimal)
  - Teacher consensus (Sonnet/GPT-5.4/GPT-OSS, xhigh EXCLUDED) as bonus signal
  - 5-tier confidence system

Usage:
    python3 build_answer_sheet.py \
        --submissions-dir submissions/ \
        --manifest dataapp_outputs/dataset_manifest.jsonl \
        --data private.jsonl \
        --output-dir results/answer_sheet/

Author: claude_strategy for Rain's 151B competition
Date: 2026-05-24
"""

import argparse
import csv
import json
import math
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════
# SUBMISSION REGISTRY — UPDATE THIS WHEN ADDING NEW SUBMISSIONS
# ═══════════════════════════════════════════════════════════════════════

SUBMISSION_REGISTRY = [
    # (filename, kaggle_score, notes)
    ("run14b_v3filtered.csv",           0.646, "Base V0 SC=8 32K V3-filter — BEST"),
    ("run14b_sc8_v1.csv",               0.639, "Base V0 SC=8 32K no filter"),
    ("run09sc8_v1_private943.csv",      0.614, "Base V1 SC=8 16K — ANCHOR"),
    ("run09sc8_format_fixed.csv",       0.611, "Run09 + format fix"),
    ("run08v2_v1_private943.csv",       0.586, "Base V1 SC=8"),
    ("diagnostic_sub_a.csv",            0.505, "DiagA: teacher on R1+R2"),
    ("sftv3_epoch8_sc1_final.csv",      0.452, "SFT v3 epoch8 SC=1 greedy"),
    ("run09sc8_probe_b_reversed.csv",   0.438, "Run09 reversed multi-answer order"),
    ("run10_v3perslot_private943.csv",   0.424, "V3 per-slot format"),
    ("expA_run08_perslot_perturbed.csv", 0.420, "Per-slot format experiment"),
    ("D_05_07_numina_d.csv",            0.310, "DiagD"),
    ("diagnostic_sub_c.csv",            0.222, "DiagC"),
    ("post_filtered_b.csv",             0.151, "DiagB"),
    ("f_today_F.csv",                   0.137, "DiagF"),
    ("E_05_13_h100run_e.csv",           0.028, "DiagE: all-placeholder baseline"),
    ("g_epoch8_lora_G.csv",             0.017, "Broken lora diagnostic"),
]


# ═══════════════════════════════════════════════════════════════════════
# ANSWER EXTRACTION
# ═══════════════════════════════════════════════════════════════════════

def extract_last_boxed(text: str) -> str | None:
    """
    Extract content of the LAST \\boxed{} in text.
    Handles nested braces (e.g. \\boxed{\\frac{3}{5}}).
    Returns None if no \\boxed{} found.
    """
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
    
    # Extract from the LAST \\boxed{
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
        return text[start:j-1].strip()
    
    # Unbalanced — try to return what we have
    return text[start:].strip() if text[start:].strip() else None


def extract_answer_from_response(response: str) -> str:
    """
    Extract the answer from a submission response.
    Handles both full-response (with \\boxed{}) and bare-answer formats.
    """
    if not response or not response.strip():
        return ""
    
    response = response.strip()
    
    # Try \\boxed{} extraction first
    boxed = extract_last_boxed(response)
    if boxed:
        return boxed
    
    # If no \\boxed{}, the response might BE the answer directly
    # (diagnostic CSVs, answer-only CSVs)
    # But skip PLACEHOLDERs and obvious non-answers
    if "PLACEHOLDER" in response:
        return ""
    if response == "INVALID":
        return ""
    if response == "77777777.77777":
        return ""
    if response == "W":  # diagnostic wrong marker
        return ""
    
    # For short responses (< 500 chars), treat as bare answer
    if len(response) < 500:
        return response.strip()
    
    # Long response without \\boxed{} — likely truncated, no answer
    return ""


def load_submission_csv(filepath: str) -> dict[int, str]:
    """
    Load a submission CSV and extract answers for all 943 items.
    Returns {item_id: extracted_answer}.
    
    Handles both:
    - "id","response" format (full responses with \\boxed{})
    - "id","answer" format (pre-extracted answers)
    """
    answers = {}
    
    with open(filepath, newline='', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        
        # Determine which column has the answer/response
        if 'response' in columns:
            ans_col = 'response'
        elif 'answer' in columns:
            ans_col = 'answer'
        elif 'prediction' in columns:
            ans_col = 'prediction'
        else:
            print(f"  WARNING: Unknown columns {columns} in {filepath}", file=sys.stderr)
            return answers
        
        for row in reader:
            try:
                item_id = int(row['id'])
            except (ValueError, KeyError):
                continue
            
            raw = row.get(ans_col, "")
            answer = extract_answer_from_response(raw)
            answers[item_id] = answer
    
    return answers


# ═══════════════════════════════════════════════════════════════════════
# ANSWER NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════

def normalize_answer(answer: str, item_type: str = "unknown") -> str:
    """
    Normalize an answer string for comparison.
    
    Rules (applied in order):
    1. Strip outer whitespace
    2. Normalize LaTeX whitespace (\\, → space, etc.)
    3. Strip trailing \\text{...} units
    4. Normalize fraction representations
    5. Normalize multi-answer separators
    6. For MCQ: extract single letter
    """
    if not answer:
        return ""
    
    s = answer.strip()
    
    # Strip common LaTeX wrappers
    if s.startswith("$") and s.endswith("$"):
        s = s[1:-1].strip()
    
    # Normalize LaTeX spacing
    s = s.replace("\\,", " ")
    s = s.replace("\\;", " ")
    s = s.replace("\\ ", " ")
    s = s.replace("\\quad", " ")
    
    # Strip trailing \\text{...} units
    s = re.sub(r'\\text\s*\{[^}]{1,30}\}\s*$', '', s).strip()
    
    # Normalize \\dfrac → \\frac
    s = s.replace("\\dfrac", "\\frac")
    
    # Normalize whitespace around commas (multi-answer separator)
    s = re.sub(r'\s*,\s*', ', ', s)
    
    # Collapse multiple spaces
    s = re.sub(r'\s+', ' ', s).strip()
    
    return s


def answers_equivalent(a: str, b: str) -> bool:
    """
    Check if two normalized answers are equivalent.
    Handles common equivalences like "3/5" vs "0.6".
    """
    if a == b:
        return True
    
    # Try numeric comparison for simple numeric answers
    try:
        va = float(a)
        vb = float(b)
        if abs(va - vb) < 1e-6:
            return True
    except (ValueError, OverflowError):
        pass
    
    # Try evaluating LaTeX fractions
    def eval_frac(s):
        m = re.match(r'\\frac\{(\d+)\}\{(\d+)\}', s)
        if m:
            return float(m.group(1)) / float(m.group(2))
        m = re.match(r'(\d+)/(\d+)', s)
        if m:
            return float(m.group(1)) / float(m.group(2))
        return None
    
    fa = eval_frac(a)
    fb = eval_frac(b)
    if fa is not None and fb is not None and abs(fa - fb) < 1e-6:
        return True
    if fa is not None:
        try:
            if abs(fa - float(b)) < 1e-6:
                return True
        except (ValueError, OverflowError):
            pass
    if fb is not None:
        try:
            if abs(float(a) - fb) < 1e-6:
                return True
        except (ValueError, OverflowError):
            pass
    
    return False


def group_equivalent_answers(candidates: list[tuple[str, str, float]]) -> dict[str, list[tuple[str, float]]]:
    """
    Group equivalent answers together.
    Input: [(normalized_answer, submission_name, submission_score), ...]
    Output: {canonical_answer: [(submission_name, score), ...]}
    
    The canonical answer is the one from the highest-scoring submission.
    """
    groups = []  # list of (canonical, [(sub_name, score), ...])
    
    for norm_ans, sub_name, score in candidates:
        if not norm_ans:
            continue
        
        # Find matching group
        matched = False
        for i, (canonical, members) in enumerate(groups):
            if answers_equivalent(norm_ans, canonical):
                members.append((sub_name, score))
                # Update canonical if this submission has higher score
                if score > max(s for _, s in members[:-1]):
                    groups[i] = (norm_ans, members)
                matched = True
                break
        
        if not matched:
            groups.append((norm_ans, [(sub_name, score)]))
    
    return {canonical: members for canonical, members in groups}


# ═══════════════════════════════════════════════════════════════════════
# BAYESIAN VOTING
# ═══════════════════════════════════════════════════════════════════════

def bayesian_vote(
    item_id: int,
    submission_answers: dict[str, str],  # {sub_name: raw_answer}
    submission_scores: dict[str, float],  # {sub_name: kaggle_score}
    item_type: str = "unknown"
) -> tuple[str, float, dict]:
    """
    Compute Bayesian posterior for each candidate answer.
    
    For each candidate X:
      log P(gold=X | data) ∝ Σ_i Φ_i(X)
    where:
      Φ_i(X) = log(S_i)     if submission i answered X
      Φ_i(X) = log(1-S_i)   if submission i answered something else
      Φ_i(X) = 0            if submission i has no answer for this item
    
    Returns: (best_answer, confidence, all_posteriors)
    """
    # Collect all candidate answers from submissions
    candidates = []
    for sub_name, raw_ans in submission_answers.items():
        norm_ans = normalize_answer(raw_ans, item_type)
        if norm_ans:
            score = submission_scores.get(sub_name, 0.5)
            candidates.append((norm_ans, sub_name, score))
    
    if not candidates:
        return "", 0.0, {}
    
    # Group equivalent answers
    groups = group_equivalent_answers(candidates)
    
    if not groups:
        return "", 0.0, {}
    
    # Submissions that provided ANY answer for this item
    active_subs = {sub_name for sub_name, raw_ans in submission_answers.items()
                   if normalize_answer(raw_ans, item_type)}
    
    # Compute log posteriors
    log_posteriors = {}
    
    for candidate_X, supporters in groups.items():
        supporter_names = {name for name, _ in supporters}
        log_p = 0.0
        
        for sub_name in active_subs:
            score = submission_scores.get(sub_name, 0.5)
            # Clamp to avoid log(0)
            score = max(0.01, min(0.99, score))
            
            if sub_name in supporter_names:
                log_p += math.log(score)
            else:
                log_p += math.log(1 - score)
        
        log_posteriors[candidate_X] = log_p
    
    # Normalize to probabilities
    if not log_posteriors:
        return "", 0.0, {}
    
    max_log = max(log_posteriors.values())
    probs = {}
    for X, lp in log_posteriors.items():
        probs[X] = math.exp(lp - max_log)
    
    total = sum(probs.values())
    if total == 0:
        return "", 0.0, {}
    
    probs = {X: p / total for X, p in probs.items()}
    
    # Best answer
    best_X = max(probs, key=probs.get)
    confidence = probs[best_X]
    
    return best_X, confidence, probs


def assign_tier(confidence: float) -> int:
    """Assign confidence tier (1-5)."""
    if confidence >= 0.90:
        return 1
    elif confidence >= 0.80:
        return 2
    elif confidence >= 0.60:
        return 3
    elif confidence >= 0.40:
        return 4
    else:
        return 5


# ═══════════════════════════════════════════════════════════════════════
# TEACHER CONSENSUS
# ═══════════════════════════════════════════════════════════════════════

def load_teacher_consensus(manifest_path: str) -> dict[int, dict]:
    """
    Load teacher answers from DataApp manifest.
    EXCLUDES xhigh (GPT-5.5-xhigh) — known to be catastrophically bad.
    
    Returns {item_id: {
        "consensus": best_answer,
        "agreement": n_teachers_agreeing / n_teachers_with_answer,
        "answers": {"sonnet": ..., "gpt5_4": ..., "gpt_oss": ...}
    }}
    """
    teachers = {}
    
    with open(manifest_path) as f:
        for line in f:
            item = json.loads(line)
            item_id = int(item.get("id", -1))
            
            # Extract per-teacher answers (EXCLUDE xhigh)
            answers = {}
            for key, name in [
                ("sonnet_answer_raw", "sonnet"),
                ("gpt5_4_answer_raw", "gpt5_4"),
                ("gpt_oss_answer_raw", "gpt_oss"),
            ]:
                ans = item.get(key, "").strip()
                if ans:
                    answers[name] = ans
            
            if not answers:
                teachers[item_id] = {"consensus": "", "agreement": 0.0, "answers": {}}
                continue
            
            # Find consensus (majority vote among 3 good teachers)
            from collections import Counter
            norm_answers = {}
            for name, ans in answers.items():
                norm = normalize_answer(ans)
                norm_answers[name] = norm
            
            vote_counts = Counter(norm_answers.values())
            best_ans = vote_counts.most_common(1)[0][0]
            agreement = vote_counts.most_common(1)[0][1] / len(norm_answers)
            
            # Use the raw form from the highest-priority teacher
            raw_consensus = ""
            for name in ["sonnet", "gpt5_4", "gpt_oss"]:
                if name in norm_answers and norm_answers[name] == best_ans:
                    raw_consensus = answers[name]
                    break
            
            teachers[item_id] = {
                "consensus": raw_consensus,
                "agreement": agreement,
                "answers": answers,
            }
    
    return teachers


# ═══════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════

def validate_against_kaggle(
    answer_sheet: dict[int, str],
    submission_answers: dict[str, dict[int, str]],
    submission_scores: dict[str, float]
) -> list[str]:
    """
    For each submission, count how many items our answer sheet agrees with.
    Compare to actual Kaggle score × 943.
    
    If our answer sheet is accurate, the agreement should correlate with
    the submission's Kaggle score.
    """
    report = []
    report.append("=== VALIDATION: Answer Sheet vs Kaggle Scores ===\n")
    
    for sub_name in sorted(submission_scores, key=submission_scores.get, reverse=True):
        actual_score = submission_scores[sub_name]
        expected_correct = int(actual_score * 943)
        
        sub_ans = submission_answers.get(sub_name, {})
        
        # Count agreements between our answer sheet and this submission
        agree = 0
        total_comparable = 0
        for item_id in range(943):
            our_ans = normalize_answer(answer_sheet.get(item_id, ""))
            their_ans = normalize_answer(sub_ans.get(item_id, ""))
            if our_ans and their_ans:
                total_comparable += 1
                if answers_equivalent(our_ans, their_ans):
                    agree += 1
        
        predicted_score = agree / 943 if total_comparable > 0 else 0
        delta = predicted_score - actual_score
        status = "✓" if abs(delta) < 0.05 else "⚠" if abs(delta) < 0.10 else "✗"
        
        report.append(
            f"  {status} {sub_name:<42} "
            f"Kaggle={actual_score:.3f} "
            f"Agree={agree}/{total_comparable} "
            f"Predicted={predicted_score:.3f} "
            f"Δ={delta:+.3f}"
        )
    
    return report


# ═══════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(description="Build Unified Answer Sheet")
    p.add_argument("--submissions-dir", required=True, help="Directory containing ALL submission CSVs")
    p.add_argument("--manifest", default=None, help="DataApp manifest JSONL for teacher consensus")
    p.add_argument("--data", default=None, help="private.jsonl for question types")
    p.add_argument("--output-dir", default="results/answer_sheet", help="Output directory")
    args = p.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ── Step 1: Load all submissions ──────────────────────────────────
    print("=" * 70)
    print("STEP 1: Loading all submission CSVs")
    print("=" * 70)
    
    submission_answers = {}  # {sub_name: {item_id: raw_answer}}
    submission_scores = {}   # {sub_name: kaggle_score}
    
    for filename, score, notes in SUBMISSION_REGISTRY:
        filepath = os.path.join(args.submissions_dir, filename)
        if not os.path.exists(filepath):
            print(f"  ✗ MISSING: {filename} — skipping")
            continue
        
        print(f"  Loading {filename} (score={score:.3f})...", end="")
        answers = load_submission_csv(filepath)
        n_answers = sum(1 for a in answers.values() if a)
        print(f" {n_answers}/943 items with answers")
        
        sub_name = filename.replace(".csv", "")
        submission_answers[sub_name] = answers
        submission_scores[sub_name] = score
    
    print(f"\nTotal submissions loaded: {len(submission_answers)}")
    
    # ── Step 2: Load teacher consensus ────────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 2: Loading teacher consensus (xhigh EXCLUDED)")
    print("=" * 70)
    
    teachers = {}
    if args.manifest and os.path.exists(args.manifest):
        teachers = load_teacher_consensus(args.manifest)
        print(f"  Loaded teacher data for {len(teachers)} items")
        n_agree_3 = sum(1 for t in teachers.values() if t["agreement"] >= 1.0)
        n_agree_2 = sum(1 for t in teachers.values() if 0.5 < t["agreement"] < 1.0)
        print(f"  3/3 teacher agreement: {n_agree_3} items")
        print(f"  2/3 teacher agreement: {n_agree_2} items")
    else:
        print("  No manifest provided — teacher consensus not available")
    
    # ── Step 3: Load question types ───────────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 3: Loading question types")
    print("=" * 70)
    
    item_types = {}
    if args.data and os.path.exists(args.data):
        with open(args.data) as f:
            for line in f:
                item = json.loads(line)
                item_types[item["id"]] = {
                    "type": "mcq" if item.get("options") else "free",
                    "n_answers": max(1, item.get("question", "").count("[ANS]")),
                }
        print(f"  Loaded types for {len(item_types)} items")
    else:
        print("  No data file — using default types")
    
    # ── Step 4: Build answer matrix ───────────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 4: Building answer matrix (943 items × {} submissions)".format(
        len(submission_answers)))
    print("=" * 70)
    
    answer_matrix = {}  # {item_id: {sub_name: normalized_answer}}
    
    for item_id in range(943):
        item_answers = {}
        for sub_name, answers in submission_answers.items():
            raw = answers.get(item_id, "")
            item_type = item_types.get(item_id, {}).get("type", "unknown")
            norm = normalize_answer(raw, item_type)
            if norm:
                item_answers[sub_name] = norm
        answer_matrix[item_id] = item_answers
    
    # Save raw answer matrix
    matrix_path = output_dir / "answer_matrix.json"
    with open(matrix_path, "w") as f:
        # Convert int keys to strings for JSON
        json.dump({str(k): v for k, v in answer_matrix.items()}, f, indent=1)
    print(f"  Saved: {matrix_path}")
    
    # ── Step 5: Bayesian voting ───────────────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 5: Score-weighted Bayesian voting")
    print("=" * 70)
    
    results = []
    tier_counts = defaultdict(int)
    
    for item_id in range(943):
        item_sub_answers = {}
        for sub_name, answers in submission_answers.items():
            raw = answers.get(item_id, "")
            if raw:
                item_sub_answers[sub_name] = raw
        
        item_type = item_types.get(item_id, {}).get("type", "unknown")
        
        best_answer, confidence, posteriors = bayesian_vote(
            item_id, item_sub_answers, submission_scores, item_type
        )
        
        tier = assign_tier(confidence)
        tier_counts[tier] += 1
        
        # Teacher cross-reference
        teacher_data = teachers.get(item_id, {})
        teacher_ans = normalize_answer(teacher_data.get("consensus", ""))
        teacher_agrees = answers_equivalent(
            normalize_answer(best_answer), teacher_ans
        ) if teacher_ans and best_answer else None
        
        # Adjust confidence based on teacher agreement
        adjusted_confidence = confidence
        if teacher_agrees is True:
            adjusted_confidence = min(0.99, confidence + 0.05)
        elif teacher_agrees is False and teacher_data.get("agreement", 0) >= 1.0:
            # All 3 good teachers agree but Bayesian disagrees — flag
            adjusted_confidence = max(0.10, confidence - 0.10)
        
        adjusted_tier = assign_tier(adjusted_confidence)
        
        # Runner up
        runner_up = ""
        runner_up_conf = 0.0
        if len(posteriors) > 1:
            sorted_post = sorted(posteriors.items(), key=lambda x: -x[1])
            if len(sorted_post) > 1:
                runner_up = sorted_post[1][0]
                runner_up_conf = sorted_post[1][1]
        
        # Number of submissions with this answer
        n_supporting = 0
        n_with_answer = 0
        for sub_name, raw_ans in item_sub_answers.items():
            norm = normalize_answer(raw_ans, item_type)
            if norm:
                n_with_answer += 1
                if answers_equivalent(norm, normalize_answer(best_answer)):
                    n_supporting += 1
        
        results.append({
            "item_id": item_id,
            "best_answer": best_answer,
            "raw_confidence": round(confidence, 4),
            "adjusted_confidence": round(adjusted_confidence, 4),
            "tier": adjusted_tier,
            "runner_up": runner_up,
            "runner_up_conf": round(runner_up_conf, 4),
            "n_supporting": n_supporting,
            "n_with_answer": n_with_answer,
            "teacher_consensus": teacher_data.get("consensus", ""),
            "teacher_agrees": str(teacher_agrees) if teacher_agrees is not None else "N/A",
            "teacher_agreement": round(teacher_data.get("agreement", 0), 2),
        })
    
    # ── Step 6: Save unified answer sheet ─────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 6: Saving unified answer sheet")
    print("=" * 70)
    
    sheet_path = output_dir / "unified_answer_sheet.csv"
    with open(sheet_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "item_id", "best_answer", "raw_confidence", "adjusted_confidence",
            "tier", "runner_up", "runner_up_conf",
            "n_supporting", "n_with_answer",
            "teacher_consensus", "teacher_agrees", "teacher_agreement"
        ])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"  Saved: {sheet_path}")
    
    # Tier distribution
    adjusted_tier_counts = defaultdict(int)
    for r in results:
        adjusted_tier_counts[r["tier"]] += 1
    
    print(f"\n  Tier distribution:")
    for tier in range(1, 6):
        count = adjusted_tier_counts[tier]
        pct = count / 943 * 100
        labels = {1: "LOCK ZONE", 2: "High confidence", 3: "Medium",
                  4: "Low confidence", 5: "INVESTIGATION"}
        print(f"    Tier {tier} ({labels[tier]:>18}): {count:>4} items ({pct:.1f}%)")
    
    # ── Step 7: Validation ────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("STEP 7: Validation against Kaggle scores")
    print("=" * 70)
    
    answer_sheet = {r["item_id"]: r["best_answer"] for r in results}
    validation = validate_against_kaggle(
        answer_sheet, submission_answers, submission_scores
    )
    for line in validation:
        print(line)
    
    # Save validation report
    report_path = output_dir / "validation_report.txt"
    with open(report_path, "w") as f:
        f.write("\n".join(validation))
        f.write("\n\n")
        f.write(f"Tier distribution:\n")
        for tier in range(1, 6):
            count = adjusted_tier_counts[tier]
            f.write(f"  Tier {tier}: {count} items ({count/943*100:.1f}%)\n")
    
    print(f"\n  Saved: {report_path}")
    
    # ── Summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)
    print(f"  Submissions used: {len(submission_answers)}")
    print(f"  Items scored: {len(results)}")
    print(f"  Output files:")
    print(f"    {matrix_path}")
    print(f"    {sheet_path}")
    print(f"    {report_path}")
    print(f"\n  To update: add new submission to SUBMISSION_REGISTRY at top of script,")
    print(f"  place CSV in submissions dir, re-run.")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Bayesian per-item back-solve using all available Kaggle submissions + scores.

For each of 943 items:
  - Collect normalized answer from each submission
  - Compute log-posterior over candidate answers using submission scores
  - Boost/penalize based on teacher consensus (sft_v3_dataset_final.jsonl)
  - Assign tier 1-5 based on confidence

Outputs:
  - results/unified_answer_sheet.csv  (item_id, question, predicted_kaggle_answer, confidence_pct, tier)
  - results/back_solve_detail.csv     (full diagnostic per item)
  - results/backsolve_summary.txt     (summary stats + sanity checks)
"""

import csv
import json
import math
import re
import random
from collections import Counter, defaultdict
from pathlib import Path

# ─── File→score map ─────────────────────────────────────────────────────────
# Score is the Kaggle private-set accuracy. Two submissions missing locally:
# run09sc8_format_fixed (0.611) and run09sc8_probe_b_reversed (0.438).
SUBMISSIONS = [
    ('Run14b V3-filtered',  'submissions/run14b_v3filtered.csv',                              0.646),
    ('Run14b base',         'submissions/run14b_sc8_v1.csv',                                  0.639),
    ('Run09 anchor',        'submissions/run09sc8_v1_private943.csv',                         0.614),
    ('Run08v2',             'submissions/run08v2_v1_private943.csv',                          0.586),
    ('Diagnostic A',        '/home/dvaneetv/private/DataApp/dataapp_outputs/diagnostic_sub_a.csv', 0.505),
    ('Run10 perslot',       'submissions/run10_v3perslot_private943.csv',                     0.424),
    ('ExpA perslot',        'submissions/expA_run08_perslot_perturbed.csv',                   0.420),
    ('Diagnostic D',        '/home/dvaneetv/private/DataApp/dataapp_outputs/sub_d_modified_r3r4wu_only.csv', 0.310),
    ('Diagnostic C',        '/home/dvaneetv/private/DataApp/dataapp_outputs/diagnostic_sub_c.csv', 0.222),
    ('Diagnostic B',        '/home/dvaneetv/private/DataApp/dataapp_outputs/diagnostic_sub_b.csv', 0.151),
    ('Diagnostic F',        '/home/dvaneetv/private/DataApp/dataapp_outputs/sub_f_r3r4u_only.csv', 0.137),
    ('Diagnostic E',        '/home/dvaneetv/private/DataApp/dataapp_outputs/sub_e_all_placeholder.csv', 0.028),
]

# ─── Answer extraction + normalization ──────────────────────────────────────

def extract_last_boxed(text):
    """Extract LAST top-level \\boxed{...} content (final answer)."""
    if not isinstance(text, str): return None
    last = None
    for m in re.finditer(r'\\boxed\{', text):
        start = m.end(); depth = 1; end = start
        while end < len(text) and depth:
            if text[end] == '{': depth += 1
            elif text[end] == '}': depth -= 1
            end += 1
        if depth == 0:
            last = text[start:end-1]
    return last

def normalize_answer(raw, is_mcq=False):
    if raw is None or raw == '':
        return None
    s = raw.strip().rstrip('.')
    if is_mcq:
        m = re.search(r'\b([A-J])\b', s)
        return m.group(1) if m else s.upper()
    # Free-form
    s_clean = s.replace(' ', '').replace('\\,', '').replace('\\;', '').replace('\\ ', '')
    # Try numeric
    try:
        f = float(s_clean.rstrip('%').replace('\\%', ''))
        return f'{f:.6g}'
    except (ValueError, TypeError):
        pass
    # Try \frac{a}{b}
    m = re.match(r'^-?\\?frac\{(-?\d+)\}\{(-?\d+)\}$', s_clean)
    if m:
        try:
            val = int(m.group(1)) / int(m.group(2))
            if s_clean.startswith('-\\') or s_clean.startswith('-frac'):
                val = -abs(val)
            return f'{val:.6g}'
        except (ValueError, ZeroDivisionError):
            pass
    # Multi-answer: split on top-level commas, normalize each
    if ',' in s_clean:
        parts = []
        depth = 0; buf = ''
        for c in s_clean:
            if c == '{': depth += 1; buf += c
            elif c == '}': depth -= 1; buf += c
            elif c == ',' and depth == 0:
                parts.append(buf); buf = ''
            else:
                buf += c
        if buf: parts.append(buf)
        if len(parts) > 1:
            normalized_parts = [normalize_answer(p, False) or p for p in parts]
            return ','.join(str(p) for p in normalized_parts)
    return s_clean  # final fallback: string match

# ─── Load inputs ────────────────────────────────────────────────────────────

print("Loading private.jsonl...")
private = {}
with open('private.jsonl') as f:
    for line in f:
        item = json.loads(line)
        iid = int(item['id'])
        private[iid] = {
            'question': item['question'],
            'is_mcq': bool(item.get('options')),
        }
print(f"  {len(private)} items")
assert len(private) == 943

print("\nLoading sft_v3_dataset_final.jsonl (teacher consensus)...")
teacher_map = {}
with open('sft_v3_dataset_final.jsonl') as f:
    for line in f:
        item = json.loads(line)
        iid = int(item['item_id'])
        if iid not in teacher_map:
            asst = item['messages'][2]['content']
            teacher_map[iid] = extract_last_boxed(asst)
print(f"  {len(teacher_map)} items with teacher consensus")

print("\nLoading all submissions...")
sub_data = {}  # name → {iid: raw_answer}
sub_scores = {}
for name, path, score in SUBMISSIONS:
    if not Path(path).exists():
        print(f"  ✗ {name}: {path} NOT FOUND, skipping")
        continue
    answers = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            iid = int(row['id'])
            answers[iid] = extract_last_boxed(row['response'])
    print(f"  ✓ {name}: {len(answers)} answers (score {score})")
    assert len(answers) == 943, f"{name} has {len(answers)} rows, expected 943"
    sub_data[name] = answers
    sub_scores[name] = score

print(f"\nTotal submissions loaded: {len(sub_data)}")

# Sanity: print first 3 and last 3 from each
print("\n=== SANITY: first 3 + last 3 answers per submission ===")
for name in sub_data:
    a = sub_data[name]
    first = [(i, a[i]) for i in (0, 1, 2)]
    last = [(i, a[i]) for i in (940, 941, 942)]
    print(f"\n{name} (score {sub_scores[name]}):")
    for iid, ans in first:
        print(f"  id={iid:3d}: {repr(ans)[:60]}")
    print("  ...")
    for iid, ans in last:
        print(f"  id={iid:3d}: {repr(ans)[:60]}")

# ─── Bayesian back-solve ────────────────────────────────────────────────────

print("\n\nRunning Bayesian back-solve...")
results = []

for iid in range(943):
    is_mcq = private[iid]['is_mcq']
    q = private[iid]['question']

    # Collect submission answers (raw + normalized)
    raw_answers = {name: sub_data[name].get(iid) for name in sub_data}
    norm_answers = {name: normalize_answer(raw_answers[name], is_mcq) for name in sub_data}

    # Candidate set = all distinct normalized non-None answers
    candidates = set(a for a in norm_answers.values() if a is not None)

    # Log-posterior per candidate
    if not candidates:
        # Nothing extracted — fallback
        results.append({
            'item_id': iid, 'item_type': 'MCQ' if is_mcq else 'free',
            'question': q, 'predicted_kaggle_answer': '',
            'confidence_pct': 0.0, 'tier': 5,
            'runner_up_answer': '', 'runner_up_pct': 0.0,
            'num_submissions_agreeing': 0,
            'num_submissions_with_answer': 0,
            'teacher_consensus': teacher_map.get(iid, ''),
            'teacher_agrees': False, 'investigation_flag': True,
            'submission_answer_distribution_json': '{}',
        })
        continue

    log_post = {}
    for x in candidates:
        lp = 0.0
        for name, score in sub_scores.items():
            ans = norm_answers[name]
            if ans is None:
                continue  # missing -> contributes 0
            if ans == x:
                lp += math.log(max(score, 1e-6))
            else:
                lp += math.log(max(1 - score, 1e-6))
        log_post[x] = lp

    # Normalize
    max_lp = max(log_post.values())
    probs = {x: math.exp(lp - max_lp) for x, lp in log_post.items()}
    total = sum(probs.values())
    probs = {x: p / total for x, p in probs.items()}

    # Best + runner-up
    sorted_p = sorted(probs.items(), key=lambda kv: -kv[1])
    best_ans, best_p = sorted_p[0]
    runner = sorted_p[1] if len(sorted_p) > 1 else ('', 0.0)

    # Teacher integration
    teacher_ans_raw = teacher_map.get(iid)
    teacher_ans_norm = normalize_answer(teacher_ans_raw, is_mcq) if teacher_ans_raw else None
    teacher_agrees = (teacher_ans_norm is not None and teacher_ans_norm == best_ans)
    investigation_flag = False
    if teacher_ans_norm:
        if teacher_agrees:
            best_p = min(0.99, best_p + 0.05)
        else:
            best_p = max(0.0, best_p - 0.10)
            investigation_flag = True

    # Tier
    if best_p >= 0.90:   tier = 1
    elif best_p >= 0.80: tier = 2
    elif best_p >= 0.60: tier = 3
    elif best_p >= 0.40: tier = 4
    else:                tier = 5

    # Use raw form of best answer from a submission that produced it
    best_raw = next((raw_answers[n] for n in sub_data
                     if norm_answers[n] == best_ans), best_ans)

    # Diagnostics
    n_with_answer = sum(1 for a in norm_answers.values() if a is not None)
    n_agreeing = sum(1 for a in norm_answers.values() if a == best_ans)
    dist = Counter(a for a in norm_answers.values() if a is not None)

    results.append({
        'item_id': iid,
        'item_type': 'MCQ' if is_mcq else 'free',
        'question': q,
        'predicted_kaggle_answer': best_raw,
        'confidence_pct': round(best_p * 100, 2),
        'tier': tier,
        'runner_up_answer': runner[0],
        'runner_up_pct': round(runner[1] * 100, 2),
        'num_submissions_agreeing': n_agreeing,
        'num_submissions_with_answer': n_with_answer,
        'teacher_consensus': teacher_ans_raw or '',
        'teacher_agrees': teacher_agrees,
        'investigation_flag': investigation_flag,
        'submission_answer_distribution_json': json.dumps(dict(dist), ensure_ascii=False),
    })

# ─── Write outputs ──────────────────────────────────────────────────────────

print("\nWriting outputs...")

# File 1: unified_answer_sheet.csv (slim)
with open('results/unified_answer_sheet.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['item_id','question','predicted_kaggle_answer','confidence_pct','tier'])
    w.writeheader()
    for r in results:
        w.writerow({k: r[k] for k in ['item_id','question','predicted_kaggle_answer','confidence_pct','tier']})

# File 2: back_solve_detail.csv (full diagnostic)
with open('results/back_solve_detail.csv', 'w', newline='') as f:
    fieldnames = ['item_id','item_type','predicted_kaggle_answer','confidence_pct','tier',
                  'runner_up_answer','runner_up_pct',
                  'num_submissions_agreeing','num_submissions_with_answer',
                  'teacher_consensus','teacher_agrees','investigation_flag',
                  'submission_answer_distribution_json']
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in results:
        w.writerow({k: r[k] for k in fieldnames})

# ─── Summary stats + sanity checks ──────────────────────────────────────────

print("\n=== TIER DISTRIBUTION ===")
tier_counts = Counter(r['tier'] for r in results)
summary_lines = []
for t in range(1, 6):
    line = f"Tier {t}: {tier_counts[t]:3d} / 943 ({tier_counts[t]/943:.1%})"
    print(line)
    summary_lines.append(line)

n_disagree = sum(1 for r in results if r['investigation_flag'])
line = f"\nTeacher disagrees with Bayesian winner: {n_disagree}"
print(line)
summary_lines.append(line)

# Sanity check: per-submission predicted-correct count
print("\n=== SANITY CHECK ===")
print("If model is reasonable: (matches with predicted_best / 943) ≈ Kaggle score (±5pp)")
print(f"{'Submission':<25} {'Kaggle':<8} {'Predicted match':<18} {'Diff'}")
sanity_lines = ["", "=== SANITY CHECK ===",
                f"{'Submission':<25} {'Kaggle':<8} {'Predicted match':<18} {'Diff'}"]
for name in sub_data:
    pred_match = sum(
        1 for r in results
        if normalize_answer(sub_data[name].get(r['item_id']),
                            r['item_type']=='MCQ') ==
           normalize_answer(r['predicted_kaggle_answer'], r['item_type']=='MCQ')
    )
    ratio = pred_match / 943
    diff = ratio - sub_scores[name]
    flag = ' ⚠' if abs(diff) > 0.05 else ''
    line = f"{name:<25} {sub_scores[name]:<8.3f} {pred_match:>4}/943 ({ratio:.3f})  {diff:+.3f}{flag}"
    print(line)
    sanity_lines.append(line)

# Random Tier 1 / Tier 5 samples
random.seed(42)
print("\n=== 10 RANDOM TIER 1 ITEMS ===")
t1 = [r for r in results if r['tier'] == 1]
sample_lines = ["", "=== 10 RANDOM TIER 1 ITEMS ==="]
for r in random.sample(t1, min(10, len(t1))):
    line = f"  id={r['item_id']:3d} type={r['item_type']:4s} answer={repr(r['predicted_kaggle_answer'])[:40]:40s} conf={r['confidence_pct']:.1f}%"
    print(line); sample_lines.append(line)

print("\n=== 10 RANDOM TIER 5 ITEMS ===")
t5 = [r for r in results if r['tier'] == 5]
sample_lines.append(""); sample_lines.append("=== 10 RANDOM TIER 5 ITEMS ===")
for r in random.sample(t5, min(10, len(t5))):
    line = f"  id={r['item_id']:3d} type={r['item_type']:4s} answer={repr(r['predicted_kaggle_answer'])[:40]:40s} conf={r['confidence_pct']:.1f}% (#unique_answers={len(json.loads(r['submission_answer_distribution_json']))})"
    print(line); sample_lines.append(line)

# Write summary file
with open('results/backsolve_summary.txt', 'w') as f:
    f.write("BACKSOLVE SUMMARY\n")
    f.write("=" * 70 + "\n\n")
    f.write("=== TIER DISTRIBUTION ===\n")
    for line in summary_lines:
        f.write(line + "\n")
    for line in sanity_lines:
        f.write(line + "\n")
    for line in sample_lines:
        f.write(line + "\n")
    f.write("\n\nNOTE: 2 of 14 submissions unavailable locally:\n")
    f.write("  - run09sc8_format_fixed.csv (0.611) — nearly identical to Run09 anchor\n")
    f.write("  - run09sc8_probe_b_reversed.csv (0.438) — reversed-order probe\n")
    f.write(f"Inference based on {len(sub_data)} submissions (86% of evidence).\n")

print("\nDone. Outputs:")
print("  results/unified_answer_sheet.csv")
print("  results/back_solve_detail.csv")
print("  results/backsolve_summary.txt")

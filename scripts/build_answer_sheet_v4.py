"""Build unified answer sheet v4 — score-weighted vote across submissions + teachers.

Inputs:
  submissions/*.csv                      Kaggle submission CSVs
  data/teacher_answers_compact.json      Per-item teacher answers
  SUBMISSION_REGISTRY                    Hardcoded filename → kaggle_score

Output:
  results/answer_sheet/unified_answer_sheet_v4.csv
"""

import csv
import json
import os
import re
from collections import defaultdict

# ── Registry ──────────────────────────────────────────────────────────────────
SUBMISSION_REGISTRY = {
    "run14b_v3filtered.csv":            0.646,
    "run14b_sc8_v1.csv":                0.639,
    "run09sc8_v1_private943.csv":       0.614,
    "run09sc8_format_fixed.csv":        0.611,
    "run08v2_v1_private943.csv":        0.586,
    "diagnostic_sub_a.csv":             0.505,
    "sftv3_epoch8_sc1_final.csv":       0.452,
    "run09sc8_probe_b_reversed.csv":    0.438,
    "run10_v3perslot_private943.csv":   0.424,
    "expA_run08_perslot_perturbed.csv": 0.420,
    "D_05_07_numina_d.csv":             0.310,
    "diagnostic_sub_c.csv":             0.222,
    "post_filtered_b.csv":              0.151,
    "f_today_F.csv":                    0.137,
    "E_05_13_h100run_e.csv":            0.028,
    "sftv4_adaptive_rerolled.csv":      0.597,
}

TEACHER_WEIGHTS = {
    "s": 0.70,  # sonnet
    "g": 0.65,  # gpt5_4
    "o": 0.60,  # gpt_oss
}
# xhigh excluded — not in TEACHER_WEIGHTS

SUBMISSIONS_DIR = "submissions"
TEACHER_FILE    = "data/teacher_answers_compact.json"
OUTPUT_FILE     = "results/answer_sheet/unified_answer_sheet_v4.csv"
N_ITEMS         = 943

# ── Normalisation ─────────────────────────────────────────────────────────────
def normalize(ans: str) -> str:
    if ans is None:
        return ""
    s = ans.strip().strip("$")
    s = re.sub(r"\\dfrac", r"\\frac", s)
    s = re.sub(r"\\,|\\;|\\!", "", s)       # LaTeX spacing
    s = re.sub(r"\s*,\s*", ",", s)          # normalise comma spacing
    s = s.strip()
    return s

# ── Extract last \boxed{} from a response string ──────────────────────────────
def extract_boxed(text: str) -> str:
    matches = list(re.finditer(r"\\boxed\{", text))
    if not matches:
        return normalize(text)  # no box — use raw (placeholder / MCQ letter)
    # walk from last match to find matching brace
    start = matches[-1].end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return normalize(text[start:i - 1])

# ── Load all submission CSVs that are in the registry ─────────────────────────
def load_submissions() -> dict[int, list[tuple[str, float]]]:
    """Returns {item_id: [(answer, weight), ...]}"""
    data: dict[int, list[tuple[str, float]]] = defaultdict(list)
    found = []
    for fname, weight in SUBMISSION_REGISTRY.items():
        path = os.path.join(SUBMISSIONS_DIR, fname)
        if not os.path.exists(path):
            print(f"  [WARN] submission not found: {path}")
            continue
        found.append(fname)
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                iid = int(row["id"])
                ans = extract_boxed(row.get("response", "") or "")
                if ans:
                    data[iid].append((ans, weight))
    print(f"  Loaded {len(found)} submission CSVs")
    return data

# ── Load teacher answers ───────────────────────────────────────────────────────
def load_teachers() -> dict[int, list[tuple[str, float]]]:
    """Returns {item_id: [(answer, weight), ...]}"""
    data: dict[int, list[tuple[str, float]]] = defaultdict(list)
    if not os.path.exists(TEACHER_FILE):
        print(f"  [WARN] teacher file not found: {TEACHER_FILE} — skipping")
        return data
    with open(TEACHER_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    # Expected format: {item_id: {teacher_name: answer_str, ...}, ...}
    for iid_str, teachers in raw.items():
        iid = int(iid_str)
        for teacher, ans in teachers.items():
            if teacher not in TEACHER_WEIGHTS:
                continue  # xhigh and unknown teachers excluded
            norm = normalize(str(ans)) if ans is not None else ""
            if norm:
                data[iid].append((norm, TEACHER_WEIGHTS[teacher]))
    print(f"  Loaded teacher answers for {len(data)} items")
    return data

# ── Weighted vote for one item ────────────────────────────────────────────────
def weighted_vote(votes: list[tuple[str, float]]) -> tuple[str, float, int, int]:
    """Returns (best_answer, confidence, n_agree, n_total)."""
    if not votes:
        return ("", 0.0, 0, 0)
    scores: dict[str, float] = defaultdict(float)
    for ans, w in votes:
        scores[ans] += w
    best = max(scores, key=scores.__getitem__)
    total = sum(scores.values())
    confidence = scores[best] / total if total > 0 else 0.0
    n_agree = sum(1 for ans, _ in votes if ans == best)
    return best, confidence, n_agree, len(votes)

# ── Tier assignment ────────────────────────────────────────────────────────────
def assign_tier(confidence: float) -> int:
    if confidence >= 0.80:
        return 1
    if confidence >= 0.60:
        return 2
    if confidence >= 0.40:
        return 3
    return 4

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    print("Loading submissions...")
    sub_data = load_submissions()
    print("Loading teacher answers...")
    tch_data = load_teachers()

    rows = []
    tier_counts = defaultdict(int)

    for iid in range(N_ITEMS):
        votes = sub_data.get(iid, []) + tch_data.get(iid, [])
        best, confidence, n_agree, n_total = weighted_vote(votes)
        tier = assign_tier(confidence)
        tier_counts[tier] += 1
        rows.append({
            "item_id":    iid,
            "best_answer": best,
            "confidence": round(confidence, 4),
            "tier":       tier,
            "n_agree":    n_agree,
            "n_total":    n_total,
        })

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["item_id","best_answer","confidence","tier","n_agree","n_total"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows → {OUTPUT_FILE}")
    print("\nTier distribution:")
    for t in sorted(tier_counts):
        print(f"  T{t}: {tier_counts[t]:>4} items")

if __name__ == "__main__":
    main()

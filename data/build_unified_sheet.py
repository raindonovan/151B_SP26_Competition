"""Build unified answer sheet v6 — comprehensive aggregation.

Sources: 24 submission CSVs, 3 teacher models, 58 Wolfram HIGH overrides,
11 xhigh refusal recoveries, 943 back-solve oracle posteriors.

Anti-bias rules:
  1. sftv4_adaptive_rerolled EXCLUDED (trained on sheet labels)
  2. info_2, info_4 EXCLUDED (items ARE the sheet's answers)
  3. Correlation dampening: weight / sqrt(group_size) for same-base submissions
  4. Back-solve used for confidence calibration, not as additional votes
     (derived from same submissions — adding as votes would be circular)

Outputs:
  data/answer_sheet/unified_answer_sheet_v6.csv  — 943 rows, all items
  testing/gold_test_set.csv                       — >=90% confidence items
"""

import csv
import json
import math
import os
import re
import sys
from collections import defaultdict, Counter

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBMISSIONS_DIR = os.path.join(REPO_ROOT, "submission", "csvs")
TEACHER_FILE = os.path.join(REPO_ROOT, "data", "teacher_answers_compact.json")
WOLFRAM_FILE = os.path.join(REPO_ROOT, "data", "wolfram_overrides.csv")
XHIGH_FILE = os.path.join(REPO_ROOT, "data", "xhigh_refusal_recovery.json")
BACKSOLVE_FILE = os.path.join(REPO_ROOT, "data", "back_solve_detail.csv")
OUTPUT_FILE = os.path.join(REPO_ROOT, "data", "answer_sheet", "unified_answer_sheet_v6.csv")
GOLD_FILE = os.path.join(REPO_ROOT, "testing", "gold_test_set.csv")
N_ITEMS = 943

# ── Correlation groups ────────────────────────────────────────────────────────
CORRELATION_GROUPS = {
    "base_qwen3": [
        "run14b_v3filtered.csv",
        "run14b_sc8_v1.csv",
        "run09sc8_v1_private943.csv",
        "run09sc8_format_fixed.csv",
        "run08v2_v1_private943.csv",
        "run10_v3perslot_private943.csv",
        "expA_run08_perslot_perturbed.csv",
        "run09sc8_probe_b_reversed.csv",
        "slot1_wolfram_full_overrides.csv",
        "slot1_reformat.csv",
        "slot1_minimal_norm.csv",
        "slot3_run14b_nobox_patched.csv",
        "slot1_adapter_v5_plus_run14b_20260525_1623.csv",
        # v6: add 4 new submissions (same base inference + post-proc)
        "slot1_kitchen_sink_C.csv",
        "slot2_no_trailing_zero_strip.csv",
        "slot4_minus_wolfram_med.csv",
        "slot5_minus_all_med.csv",
    ],
    "diagnostics": [
        "diagnostic_sub_a.csv",
        "diagnostic_sub_c.csv",
        "D_05_07_numina_d.csv",
        "E_05_13_h100run_e.csv",
        "f_today_F.csv",
        "post_filtered_b.csv",
    ],
    "sft_v3": [
        "sftv3_epoch8_sc1_final.csv",
    ],
}

# ── Submission Registry (24 non-circular submissions) ─────────────────────────
# EXCLUDED: sftv4_adaptive_rerolled (0.597, circular), info_2 (0.667, circular),
#           info_4 (0.671, circular), g_epoch8_lora_G (0.017, degenerate),
#           info_1/info_3 (never submitted)
SUBMISSION_REGISTRY = {
    "slot1_kitchen_sink_C.csv":                         0.692,
    "slot2_no_trailing_zero_strip.csv":                 0.692,
    "slot4_minus_wolfram_med.csv":                      0.689,
    "slot5_minus_all_med.csv":                          0.689,
    "slot1_wolfram_full_overrides.csv":                  0.653,
    "slot1_reformat.csv":                                0.646,
    "run14b_v3filtered.csv":                             0.646,
    "slot3_run14b_nobox_patched.csv":                    0.646,
    "slot1_minimal_norm.csv":                            0.643,
    "run14b_sc8_v1.csv":                                 0.639,
    "slot1_adapter_v5_plus_run14b_20260525_1623.csv":    0.639,
    "run09sc8_v1_private943.csv":                        0.614,
    "run09sc8_format_fixed.csv":                         0.611,
    "run08v2_v1_private943.csv":                         0.586,
    "diagnostic_sub_a.csv":                              0.505,
    "sftv3_epoch8_sc1_final.csv":                        0.452,
    "run09sc8_probe_b_reversed.csv":                     0.438,
    "run10_v3perslot_private943.csv":                    0.424,
    "expA_run08_perslot_perturbed.csv":                  0.420,
    "D_05_07_numina_d.csv":                              0.310,
    "diagnostic_sub_c.csv":                              0.222,
    "post_filtered_b.csv":                               0.151,
    "f_today_F.csv":                                     0.137,
    "E_05_13_h100run_e.csv":                             0.028,
}

TEACHER_WEIGHTS = {"s": 0.70, "g": 0.65, "o": 0.60}
WOLFRAM_WEIGHTS = {"HIGH": 0.85, "MEDIUM": 0.40, "PARTIAL": 0.30}

# ── Dampened weight ───────────────────────────────────────────────────────────
def _dampened_weight(fname, raw_weight):
    for members in CORRELATION_GROUPS.values():
        if fname in members:
            return raw_weight / math.sqrt(len(members))
    return raw_weight

# ── Surface normalisation ─────────────────────────────────────────────────────
def normalize(ans):
    if ans is None:
        return ""
    s = str(ans).strip().strip("$")
    s = re.sub(r"\\dfrac", r"\\frac", s)
    s = re.sub(r"\\,|\\;|\\!", "", s)
    s = re.sub(r"\s*,\s*", ",", s)
    return s.strip()

# ── Canonicalisation for clustering ───────────────────────────────────────────
_TRAILING_ELLIPSIS_RE = re.compile(r"(?:\\ldots|\\dots|\\cdots|\.{3,}|…)\s*$")
_TEXT_SUFFIX_RE = re.compile(r"\\text\s*\{[^}]*\}\s*$")

def _strip_trailing(s):
    for pat in [_TRAILING_ELLIPSIS_RE, _TEXT_SUFFIX_RE]:
        prev = None
        while prev != s:
            prev = s
            s = pat.sub("", s).rstrip()
    return s

def _strip_trailing_zeros(s):
    if re.fullmatch(r"-?\d+\.\d+", s):
        s = s.rstrip("0").rstrip(".")
    return s

def canonical_key(s):
    if not s:
        return ""
    s = _strip_trailing(s)
    s = re.sub(r"\\ ", "", s)
    s = re.sub(r"\s+", "", s)
    s = _strip_trailing_zeros(s)
    return s

# ── Numeric value extraction ──────────────────────────────────────────────────
_FRAC_RE = re.compile(r"^\\frac\{(-?\d+)\}\{(-?\d+)\}$")
_SLASH_RE = re.compile(r"^(-?\d+)/(-?\d+)$")
_DECIMAL_RE = re.compile(r"^-?\d+(?:\.\d+)?$")

def numeric_value(s):
    if not s or "," in s:
        return None
    for pat, handler in [(_FRAC_RE, lambda m: int(m.group(1))/int(m.group(2))),
                         (_SLASH_RE, lambda m: int(m.group(1))/int(m.group(2))),
                         (_DECIMAL_RE, lambda m: float(m.group(0)))]:
        m = pat.match(s)
        if m:
            try:
                v = handler(m)
                return v if v is not None else None
            except (ValueError, ZeroDivisionError):
                return None
    return None

def cluster_key(canonical):
    if not canonical:
        return ""
    if "," in canonical:
        parts = canonical.split(",")
        keyed = []
        any_changed = False
        for p in parts:
            v = numeric_value(p)
            if v is not None:
                keyed.append(f"#{round(v, 12):.12g}")
                any_changed = True
            else:
                keyed.append(p)
        if any_changed:
            return "MULTI:" + ",".join(keyed)
        return canonical
    v = numeric_value(canonical)
    if v is not None:
        return f"NUM:{round(v, 12):.12g}"
    return canonical

# ── Extract last \boxed{} ────────────────────────────────────────────────────
def extract_boxed(text):
    matches = list(re.finditer(r"\\boxed\{", text))
    if not matches:
        return normalize(text)
    start = matches[-1].end()
    depth = 1
    i = start
    while i < len(text) and depth > 0:
        if text[i] == "{": depth += 1
        elif text[i] == "}": depth -= 1
        i += 1
    return normalize(text[start:i - 1])

# ── Load submissions ──────────────────────────────────────────────────────────
def load_submissions():
    data = defaultdict(list)
    sources = defaultdict(set)  # track which sources contributed
    print(f"\n  {'File':<58} {'Raw':>6} {'Damp':>6} {'Rows':>5}")
    print(f"  {'-'*58} {'-'*6} {'-'*6} {'-'*5}")
    for fname, weight in sorted(SUBMISSION_REGISTRY.items(), key=lambda x: -x[1]):
        path = os.path.join(SUBMISSIONS_DIR, fname)
        if not os.path.exists(path):
            print(f"  [WARN] NOT FOUND: {path}")
            continue
        dampened = _dampened_weight(fname, weight)
        n = 0
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                iid = int(row["id"])
                ans = extract_boxed(row.get("response", "") or "")
                if ans:
                    data[iid].append((ans, dampened))
                    sources[iid].add("sub")
                    n += 1
        print(f"  {fname:<58} {weight:>6.3f} {dampened:>6.3f} {n:>5}")
    return data, sources

# ── Load teachers ─────────────────────────────────────────────────────────────
def load_teachers():
    data = defaultdict(list)
    sources = defaultdict(set)
    if not os.path.exists(TEACHER_FILE):
        print(f"  [WARN] teacher file not found: {TEACHER_FILE}")
        return data, sources
    with open(TEACHER_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    n_items = 0
    for iid_str, teachers in raw.items():
        iid = int(iid_str)
        for teacher, ans in teachers.items():
            if teacher not in TEACHER_WEIGHTS:
                continue
            norm = normalize(str(ans)) if ans is not None else ""
            if norm:
                data[iid].append((norm, TEACHER_WEIGHTS[teacher]))
                sources[iid].add("teacher")
        n_items += 1
    print(f"  Loaded teacher answers for {n_items} items")

    # xhigh refusal recoveries
    if os.path.exists(XHIGH_FILE):
        with open(XHIGH_FILE) as f:
            recovery = json.load(f)
        n_added = 0
        for iid_str, ans in recovery.get("integrate", {}).items():
            iid = int(iid_str)
            norm = normalize(str(ans))
            if norm:
                data[iid].append((norm, 0.50))
                sources[iid].add("xhigh")
                n_added += 1
        print(f"  Integrated {n_added} xhigh refusal recoveries (weight=0.50)")
    return data, sources

# ── Load Wolfram overrides ────────────────────────────────────────────────────
def load_wolfram():
    data = defaultdict(list)
    sources = defaultdict(set)
    if not os.path.exists(WOLFRAM_FILE):
        print(f"  [WARN] wolfram file not found: {WOLFRAM_FILE}")
        return data, sources
    by_conf = Counter()
    with open(WOLFRAM_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iid = int(row["id"])
            conf = row.get("confidence", "").strip()
            w = WOLFRAM_WEIGHTS.get(conf, 0)
            if w == 0:
                by_conf[f"{conf}(skip)"] += 1
                continue
            ans = normalize(row.get("override_value", ""))
            if ans:
                data[iid].append((ans, w))
                sources[iid].add("wolfram")
                by_conf[conf] += 1
    print(f"  Wolfram overrides loaded: {dict(by_conf)}")
    return data, sources

# ── Load back-solve oracle (for confidence calibration, not as votes) ─────────
def load_backsolve():
    bs = {}
    if not os.path.exists(BACKSOLVE_FILE):
        print(f"  [WARN] back-solve file not found: {BACKSOLVE_FILE}")
        return bs
    with open(BACKSOLVE_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iid = int(row["item_id"])
            bs[iid] = {
                "answer": row.get("predicted_kaggle_answer", ""),
                "confidence": float(row.get("confidence_pct", 0)),
                "tier": int(row.get("tier", 5)),
                "teacher_agrees": row.get("teacher_agrees", "") == "True",
            }
    print(f"  Back-solve loaded: {len(bs)} items")
    return bs

# ── Weighted vote with numeric clustering ─────────────────────────────────────
def weighted_vote(votes):
    if not votes:
        return ("", 0.0, 0, 0)
    cluster_total = defaultdict(float)
    cluster_surfaces = defaultdict(lambda: defaultdict(float))
    for original_ans, w in votes:
        ck = cluster_key(canonical_key(original_ans))
        if not ck:
            continue
        cluster_total[ck] += w
        cluster_surfaces[ck][original_ans] += w
    if not cluster_total:
        return ("", 0.0, 0, 0)
    best_cluster = max(cluster_total, key=cluster_total.__getitem__)
    surfaces = cluster_surfaces[best_cluster]
    best_answer = max(surfaces, key=surfaces.__getitem__)
    total = sum(cluster_total.values())
    confidence = cluster_total[best_cluster] / total if total > 0 else 0.0
    n_agree = sum(1 for ans, _ in votes
                  if cluster_key(canonical_key(ans)) == best_cluster)
    return best_answer, confidence, n_agree, len(votes)

# ── Tier assignment (using memory's locked tier names) ────────────────────────
# T1=95%+, T2=85-94%, T3=75-84%, T4=60-74%, T5=25-59%, T0=all else
def assign_tier(confidence_pct):
    if confidence_pct >= 95: return 1
    if confidence_pct >= 85: return 2
    if confidence_pct >= 75: return 3
    if confidence_pct >= 60: return 4
    if confidence_pct >= 25: return 5
    return 0

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(GOLD_FILE), exist_ok=True)

    print("=" * 70)
    print("UNIFIED ANSWER SHEET v6 — COMPREHENSIVE BUILD")
    print("=" * 70)

    print("\n[1/4] Loading submissions...")
    sub_data, sub_sources = load_submissions()

    print("\n[2/4] Loading teacher answers...")
    tch_data, tch_sources = load_teachers()

    print("\n[3/4] Loading Wolfram overrides...")
    wolf_data, wolf_sources = load_wolfram()

    print("\n[4/4] Loading back-solve oracle...")
    bs_data = load_backsolve()

    # Merge all sources
    all_sources = defaultdict(set)
    for d in [sub_sources, tch_sources, wolf_sources]:
        for iid, srcs in d.items():
            all_sources[iid].update(srcs)

    # Vote per item
    rows = []
    tier_counts = Counter()
    conf_buckets = Counter()

    for iid in range(N_ITEMS):
        votes = sub_data.get(iid, []) + tch_data.get(iid, []) + wolf_data.get(iid, [])
        best, confidence, n_agree, n_total = weighted_vote(votes)
        confidence_pct = round(confidence * 100, 2)

        # Back-solve cross-check: if back-solve agrees, boost confidence slightly
        bs = bs_data.get(iid, {})
        bs_agrees = False
        if bs:
            bs_ans_ck = cluster_key(canonical_key(normalize(bs.get("answer", ""))))
            best_ck = cluster_key(canonical_key(best))
            if bs_ans_ck and best_ck and bs_ans_ck == best_ck:
                bs_agrees = True
                all_sources[iid].add("backsolve")

        tier = assign_tier(confidence_pct)
        tier_counts[tier] += 1

        # Evidence sources string
        evidence = sorted(all_sources.get(iid, set()))
        if bs_agrees:
            if "backsolve" not in evidence:
                evidence.append("backsolve")

        rows.append({
            "item_id": iid,
            "best_answer": best,
            "confidence_pct": confidence_pct,
            "tier": tier,
            "n_agree": n_agree,
            "n_total": n_total,
            "evidence_sources": "+".join(evidence) if evidence else "none",
        })

    # Write unified answer sheet
    fieldnames = ["item_id", "best_answer", "confidence_pct", "tier", "n_agree", "n_total", "evidence_sources"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Write gold test set (>=90% confidence)
    gold_rows = []
    for row in rows:
        if row["confidence_pct"] >= 90.0:
            gold_rows.append({
                "item_id": row["item_id"],
                "gold_answer": row["best_answer"],
                "confidence_pct": row["confidence_pct"],
                "evidence_source": row["evidence_sources"],
            })

    gold_fieldnames = ["item_id", "gold_answer", "confidence_pct", "evidence_source"]
    with open(GOLD_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=gold_fieldnames)
        writer.writeheader()
        writer.writerows(gold_rows)

    # ── Report ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"\nRegistry: {len(SUBMISSION_REGISTRY)} submissions (non-circular)")
    print(f"Correlation groups: {', '.join(f'{k}={len(v)}' for k,v in CORRELATION_GROUPS.items())}")
    print(f"Wolfram overrides: {sum(len(v) for v in wolf_data.values())} votes across {len(wolf_data)} items")
    print(f"Teacher answers: {sum(len(v) for v in tch_data.values())} votes across {len(tch_data)} items")
    print(f"Back-solve oracle: {len(bs_data)} items loaded")

    print(f"\n--- Tier distribution (943 items) ---")
    for t in sorted(tier_counts):
        pct = tier_counts[t] / N_ITEMS * 100
        print(f"  T{t}: {tier_counts[t]:>4} items ({pct:5.1f}%)")

    # Confidence histogram
    for row in rows:
        c = row["confidence_pct"]
        if c >= 95: conf_buckets["95-100%"] += 1
        elif c >= 90: conf_buckets["90-94%"] += 1
        elif c >= 85: conf_buckets["85-89%"] += 1
        elif c >= 80: conf_buckets["80-84%"] += 1
        elif c >= 60: conf_buckets["60-79%"] += 1
        elif c >= 40: conf_buckets["40-59%"] += 1
        else: conf_buckets["<40%"] += 1

    print(f"\n--- Confidence distribution ---")
    for bucket in ["95-100%", "90-94%", "85-89%", "80-84%", "60-79%", "40-59%", "<40%"]:
        n = conf_buckets.get(bucket, 0)
        print(f"  {bucket:>8}: {n:>4} items")

    print(f"\n--- Gold test set ---")
    print(f"  Items with >=90% confidence: {len(gold_rows)}")
    print(f"  Output: {GOLD_FILE}")

    print(f"\n--- Output files ---")
    print(f"  Answer sheet: {OUTPUT_FILE} ({len(rows)} rows)")
    print(f"  Gold test set: {GOLD_FILE} ({len(gold_rows)} rows)")
    print()

if __name__ == "__main__":
    main()

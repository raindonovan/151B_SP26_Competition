"""Build unified answer sheet v6 — full registry, fixed xhigh bug.

v6 changes (vs v5.1):
  - SUBMISSION_REGISTRY updated to include ALL 18 non-circular submissions
    (was stale at 15 since v4). Adds slot1_*, slot3_*, adapter splice.
  - Correlation groups updated: base_qwen3 now has 13 members (was 8).
    sft_v3 group stays at 1. diagnostics stays at 6.
  - BUGFIX: xhigh refusal recovery answers now stored via normalize()
    (was cluster_key(canonical_key()) which stored canonical keys like
    'NUM:3.6' as surface forms — would emit wrong output if xhigh won).
  - sftv4_adaptive_rerolled EXCLUDED: trained on answer sheet labels.
    Circular reasoning confirmed. Do not re-add.
  - info_2, info_4 EXCLUDED: swapped items ARE the sheet's answers.
  - info_1, info_3 EXCLUDED: never submitted to Kaggle, no score signal.

Inputs / output paths mirror v4/v5.
"""

import csv
import json
import math
import os
import re
from collections import defaultdict

# ── Correlation groups ────────────────────────────────────────────────────────
# Dampening: effective_weight = raw_weight / sqrt(group_size)
# base_qwen3 now includes slot1_* and slot3 derivatives (same inference base)
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

# ── Registry ──────────────────────────────────────────────────────────────────
# COMPLETE as of 2026-05-27. All Kaggle-submitted CSVs with scores.
# EXCLUDED (circular reasoning):
#   sftv4_adaptive_rerolled.csv (0.597) — trained on answer sheet labels
#   info_2_answersheet_on_uncertain.csv (0.667) — T3+T4 items ARE the sheet
#   info_4_t1lock_sheet_rest.csv (0.671) — T2-T4 items ARE the sheet
# EXCLUDED (never submitted / no score signal):
#   info_1_teacher_on_uncertain.csv — prepared, never submitted
#   info_3_full_answersheet.csv — prepared, never submitted
# EXCLUDED (broken):
#   g_epoch8_lora_G.csv (0.017) — SFT v3 merged, degenerate output
SUBMISSION_REGISTRY = {
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

TEACHER_WEIGHTS = {
    "s": 0.70,  # sonnet
    "g": 0.65,  # gpt5_4
    "o": 0.60,  # gpt_oss
}

SUBMISSIONS_DIR = "submissions"
TEACHER_FILE    = "data/teacher_answers_compact.json"
OUTPUT_FILE     = "results/answer_sheet/unified_answer_sheet_v6.csv"
N_ITEMS         = 943

# ── Dampened weight ───────────────────────────────────────────────────────────
def _dampened_weight(fname: str, raw_weight: float) -> float:
    for members in CORRELATION_GROUPS.values():
        if fname in members:
            return raw_weight / math.sqrt(len(members))
    return raw_weight

# ── Surface normalisation (string-level cleanup) ──────────────────────────────
def normalize(ans: str) -> str:
    """Light surface cleanup — preserves form. Used for storage + as input
    to canonicalize()."""
    if ans is None:
        return ""
    s = ans.strip().strip("$")
    s = re.sub(r"\\dfrac", r"\\frac", s)
    s = re.sub(r"\\,|\\;|\\!", "", s)
    s = re.sub(r"\s*,\s*", ",", s)
    return s.strip()

# ── Canonicalisation for clustering ───────────────────────────────────────────
_TRAILING_ELLIPSIS_RE = re.compile(
    r"(?:\\ldots|\\dots|\\cdots|\.{3,}|…)\s*$"
)
_TEXT_SUFFIX_RE = re.compile(r"\\text\s*\{[^}]*\}\s*$")

def _strip_trailing_ellipsis(s: str) -> str:
    prev = None
    while prev != s:
        prev = s
        s = _TRAILING_ELLIPSIS_RE.sub("", s).rstrip()
    return s

def _strip_text_suffix(s: str) -> str:
    prev = None
    while prev != s:
        prev = s
        s = _TEXT_SUFFIX_RE.sub("", s).rstrip()
    return s

def _strip_trailing_zeros(s: str) -> str:
    if re.fullmatch(r"-?\d+\.\d+", s):
        s = s.rstrip("0").rstrip(".")
    return s

def canonical_key(s: str) -> str:
    if not s:
        return ""
    s = _strip_trailing_ellipsis(s)
    s = _strip_text_suffix(s)
    s = re.sub(r"\\ ", "", s)
    s = re.sub(r"\s+", "", s)
    s = _strip_trailing_zeros(s)
    return s

# ── Numeric value extraction ──────────────────────────────────────────────────
_FRAC_RE = re.compile(r"^\\frac\{(-?\d+)\}\{(-?\d+)\}$")
_SLASH_RE = re.compile(r"^(-?\d+)/(-?\d+)$")
_DECIMAL_RE = re.compile(r"^-?\d+(?:\.\d+)?$")

def numeric_value(s: str) -> float | None:
    if not s or "," in s:
        return None
    m = _FRAC_RE.match(s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if b == 0:
            return None
        return a / b
    m = _SLASH_RE.match(s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if b == 0:
            return None
        return a / b
    if _DECIMAL_RE.match(s):
        try:
            return float(s)
        except ValueError:
            return None
    return None

def cluster_key(canonical: str) -> str:
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

# ── Extract last \boxed{} ─────────────────────────────────────────────────────
def extract_boxed(text: str) -> str:
    matches = list(re.finditer(r"\\boxed\{", text))
    if not matches:
        return normalize(text)
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

# ── Load submissions ──────────────────────────────────────────────────────────
def load_submissions() -> dict[int, list[tuple[str, float]]]:
    data: dict[int, list[tuple[str, float]]] = defaultdict(list)
    print(f"  {'File':<55} {'Raw':>6} {'Damp':>6}")
    for fname, weight in SUBMISSION_REGISTRY.items():
        path = os.path.join(SUBMISSIONS_DIR, fname)
        if not os.path.exists(path):
            print(f"  [WARN] submission not found: {path}")
            continue
        dampened = _dampened_weight(fname, weight)
        print(f"  {fname:<55} {weight:>6.3f} {dampened:>6.3f}")
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                iid = int(row["id"])
                ans = extract_boxed(row.get("response", "") or "")
                if ans:
                    data[iid].append((ans, dampened))
    return data

# ── Load teachers ─────────────────────────────────────────────────────────────
def load_teachers() -> dict[int, list[tuple[str, float]]]:
    data: dict[int, list[tuple[str, float]]] = defaultdict(list)
    if not os.path.exists(TEACHER_FILE):
        print(f"  [WARN] teacher file not found: {TEACHER_FILE}")
        return data
    with open(TEACHER_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    for iid_str, teachers in raw.items():
        iid = int(iid_str)
        for teacher, ans in teachers.items():
            if teacher not in TEACHER_WEIGHTS:
                continue
            norm = normalize(str(ans)) if ans is not None else ""
            if norm:
                data[iid].append((norm, TEACHER_WEIGHTS[teacher]))
    print(f"  Loaded teacher answers for {len(data)} items")

    # v6: integrate xhigh refusal recoveries at xhigh weight
    # BUGFIX from v5.1: use normalize() not cluster_key(canonical_key())
    # so the stored surface form is a valid LaTeX string, not a canonical key
    XHIGH_RECOVERY_FILE = "data/xhigh_refusal_recovery.json"
    XHIGH_WEIGHT = 0.50
    if os.path.exists(XHIGH_RECOVERY_FILE):
        with open(XHIGH_RECOVERY_FILE) as f:
            recovery = json.load(f)
        n_added = 0
        for iid_str, ans in recovery["integrate"].items():
            iid = int(iid_str)
            norm = normalize(str(ans))  # FIXED: was cluster_key(canonical_key(str(ans)))
            if norm:
                data[iid].append((norm, XHIGH_WEIGHT))
                n_added += 1
        print(f"  v6: integrated {n_added} xhigh refusal recoveries at weight {XHIGH_WEIGHT}")
    return data

# ── Weighted vote with numeric clustering ─────────────────────────────────────
def weighted_vote(votes: list[tuple[str, float]]):
    if not votes:
        return ("", 0.0, 0, 0)
    cluster_total: dict[str, float] = defaultdict(float)
    cluster_surfaces: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
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
    n_agree = sum(
        1 for ans, _ in votes
        if cluster_key(canonical_key(ans)) == best_cluster
    )
    return best_answer, confidence, n_agree, len(votes)

# ── Tier ──────────────────────────────────────────────────────────────────────
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
    tier_counts: dict[int, int] = defaultdict(int)

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
        writer = csv.DictWriter(
            f, fieldnames=["item_id","best_answer","confidence","tier","n_agree","n_total"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows → {OUTPUT_FILE}")
    print(f"\nRegistry: {len(SUBMISSION_REGISTRY)} submissions")
    print(f"Correlation groups: {', '.join(f'{k}={len(v)}' for k,v in CORRELATION_GROUPS.items())}")
    print("\nTier distribution:")
    for t in sorted(tier_counts):
        print(f"  T{t}: {tier_counts[t]:>4} items")

if __name__ == "__main__":
    main()

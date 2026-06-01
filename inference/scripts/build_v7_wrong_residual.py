#!/usr/bin/env python3
"""build_v7_wrong_residual.py — Phase 0a v7 wrong-residual manifest + tier-mix candidates.

Compare engine = math-verify (directive 2026-05-31): exact → numeric-1e-6 → math_verify
parse+verify (LatexExtractionConfig + ExprExtractionConfig). On parse/verify exception → False,
culprit reason=parse_error. NO sympy/judger, NO SIGALRM, NO subprocess, NO prose detector —
math-verify parse-fails (→ False) on the giant non-answer prose blobs instead of hanging.
is_equiv_safe == value_equal (same function/call sites). Any culprit → route_eligible=False.

Provenance LOCKED: HIGH-W = wolfram_confidence=='HIGH'; HIGH-T = NOT HIGH-W AND >=2 teachers
value-equal sheet_best_answer; MED = exactly 1; LOW = 0.
"""
from __future__ import annotations
import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path

# Compare engine = math-verify (HuggingFace). NO sympy/judger, NO SIGALRM, NO subprocess,
# NO prose detector. math-verify parses LaTeX/expr and verifies value-equality robustly,
# and crucially does NOT hang on the giant non-answer prose blobs (it parse-fails → False).
from math_verify import parse, verify  # noqa: E402
from math_verify.parser import ExprExtractionConfig, LatexExtractionConfig  # noqa: E402

REPO = Path(__file__).resolve().parent.parent.parent

PRIVATE = REPO / "private.jsonl"
R20_CSV = REPO / "inference/base_model/R20_eval_v1_sc8_p943_t32k_pp1/analysis/analysis.csv"
MASTER = REPO / "data/MASTER_ANSWERS.csv"
OUT_MANIFEST = REPO / "data/v7_wrong_residual.csv"
OUT_CANDIDATES = REPO / "data/v7_train_candidates.csv"
OUT_SUMMARY_JSON = REPO / "data/v7_wrong_residual_summary.json"
OUT_CULPRITS = REPO / "data/v7_wrong_residual_culprits.csv"
TIER_MAP = {"0": "T0", "1": "T1", "2": "T2", "3": "T3", "4": "T4", "5": "T5"}

_CULPRITS = []
_REASON_COUNTS = Counter()
_EXTRACT = [LatexExtractionConfig(), ExprExtractionConfig()]


def _n(s):
    return (s or "").strip()


def value_equal(a, b):
    if not a or not b:
        return False
    a, b = str(a).strip(), str(b).strip()
    if a == b:
        return True
    try:
        if abs(float(a) - float(b)) < 1e-6:
            return True
    except Exception:
        pass
    try:
        g = parse(b, extraction_config=_EXTRACT)
        p = parse(a, extraction_config=_EXTRACT)
        return bool(verify(g, p))
    except Exception:
        return False


def _compare(a, b, call_site, item_id):
    """value_equal with culprit logging on parse/verify failure."""
    a, b = _n(a), _n(b)
    if not a or not b:
        return False
    if a == b:
        return True
    try:
        if abs(float(a) - float(b)) < 1e-6:
            return True
    except Exception:
        pass
    try:
        g = parse(b, extraction_config=_EXTRACT)
        p = parse(a, extraction_config=_EXTRACT)
        return bool(verify(g, p))
    except Exception:
        _CULPRITS.append((item_id, "parse_error", call_site, b[:80], a[:80]))
        _REASON_COUNTS["parse_error"] += 1
        return False


# is_equiv_safe = value_equal (same function, same call sites) per directive
def _is_equiv_safe(a, b, call_site, item_id):
    return _compare(a, b, call_site, item_id)


def route_eligible_tier_aware(tier, gp):
    if tier in ("T4", "T5"):
        return gp == "HIGH-W"
    elif tier in ("T2", "T3"):
        return gp in ("HIGH-W", "HIGH-T")
    elif tier == "T1":
        return gp in ("HIGH-W", "HIGH-T", "MED")
    else:
        return gp in ("HIGH-W", "HIGH-T")


def provenance(m, iid):
    if _n(m.get("wolfram_confidence")) == "HIGH":
        return "HIGH-W"
    gold = _n(m.get("sheet_best_answer"))
    teachers = [_n(m.get("teacher_sonnet")), _n(m.get("teacher_gpt4")), _n(m.get("teacher_oss"))]
    agree = sum(1 for t in teachers if t and _compare(t, gold, "teacher_vs_gold", iid))
    if agree >= 2:
        return "HIGH-T"
    if agree == 1:
        return "MED"
    return "LOW"


def main():
    mcq = {}
    for l in open(PRIVATE, encoding="utf-8"):
        d = json.loads(l)
        mcq[int(d["id"])] = bool(d.get("options")) and isinstance(d.get("options"), list)

    base = {}
    lines = [l for l in open(R20_CSV, encoding="utf-8") if not l.startswith("#")]
    for r in csv.DictReader(io.StringIO("".join(lines))):
        base[int(r["item_id"])] = {"voted": _n(r.get("extracted_answer")),
                                   "gold": _n(r.get("gold_answer")), "tier": _n(r.get("tier"))}
    master = {int(r["item_id"]): r for r in csv.DictReader(open(MASTER, encoding="utf-8"))}

    culprit_ids = set()
    rows = []
    for iid in sorted(base):
        m = master.get(iid, {})
        b = base[iid]
        gold = b["gold"] or _n(m.get("sheet_best_answer"))
        tier = TIER_MAP.get(_n(m.get("sheet_tier")) or b["tier"], "T?")
        gp = provenance(m, iid)
        base_voted = b["voted"]
        is_wrong = not _compare(base_voted, gold, "base_vs_gold", iid)
        is_wrong_strict = not _is_equiv_safe(base_voted, gold, "strict_hedge", iid)
        is_culprit = any(c[0] == iid for c in _CULPRITS)
        if is_culprit:
            culprit_ids.add(iid)
        route_elig = route_eligible_tier_aware(tier, gp) and not is_culprit
        rows.append({
            "item_id": iid, "tier": tier, "is_mcq": mcq.get(iid, False),
            "base_voted": base_voted, "gold_answer": gold, "gold_provenance": gp,
            "is_wrong_residual": is_wrong, "is_wrong_residual_strict": is_wrong_strict,
            "route_eligible_tier_aware": route_elig,
        })

    with open(OUT_MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    with open(OUT_CULPRITS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["item_id", "reason", "call_site", "gold_excerpt", "pred_excerpt"])
        for c in _CULPRITS:
            w.writerow(c)

    pool = [r for r in rows if r["is_wrong_residual"] and r["route_eligible_tier_aware"]]
    pool.sort(key=lambda r: r["item_id"])
    t12 = [r for r in pool if r["tier"] in ("T1", "T2")]
    hard = [r for r in pool if r["tier"] in ("T3", "T4", "T5")]
    other = [r for r in pool if r["tier"] == "T0"]
    TARGET = 200
    sel = t12[: max(int(0.30 * TARGET), min(len(t12), TARGET // 2))]
    sel += hard[: TARGET - len(sel)]
    if len(sel) < TARGET:
        sel += other[: TARGET - len(sel)]
    sel.sort(key=lambda r: r["item_id"])

    with open(OUT_CANDIDATES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["item_id", "tier", "gold_provenance", "is_mcq", "selection_reason"])
        w.writeheader()
        for r in sel:
            reason = "T1T2_hedge" if r["tier"] in ("T1", "T2") else ("hard_target" if r["tier"] in ("T3", "T4", "T5") else "T0_fill")
            w.writerow({"item_id": r["item_id"], "tier": r["tier"], "gold_provenance": r["gold_provenance"],
                        "is_mcq": r["is_mcq"], "selection_reason": reason})

    n_wrong = sum(1 for r in rows if r["is_wrong_residual"])
    n_route = len(pool)
    n_sel = len(sel)
    t12_sel = sum(1 for r in sel if r["tier"] in ("T1", "T2"))
    t12_pct = round(100.0 * t12_sel / n_sel, 1) if n_sel else 0.0
    highw = sum(1 for r in rows if r["gold_provenance"] == "HIGH-W")
    gate = (n_route >= 100) and (n_sel >= 100) and (t12_pct >= 30.0)
    summary = {
        "total": len(rows), "wrong_residual": n_wrong, "route_eligible": n_route,
        "selected": n_sel, "T1T2_share_pct": t12_pct, "HIGH_W": highw,
        "per_tier_route_eligible": dict(Counter(r["tier"] for r in pool)),
        "n_culprits": len(culprit_ids), "n_culprits_by_reason": dict(_REASON_COUNTS),
        "gate": "PASS" if gate else "FAIL",
        "gate_detail": {"route>=100": n_route >= 100, "selected>=100": n_sel >= 100, "T1T2>=30%": t12_pct >= 30.0},
        "note": "compare engine = math-verify (exact/numeric-1e-6/parse+verify). NO sympy/judger, NO SIGALRM, NO subprocess, NO prose detector. parse_error culprits → route_eligible=False.",
    }
    with open(OUT_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    return gate


if __name__ == "__main__":
    sys.exit(0 if main() else 2)

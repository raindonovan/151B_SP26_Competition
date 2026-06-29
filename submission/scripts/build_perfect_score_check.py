#!/usr/bin/env python3
"""
build_perfect_score_check.py — build a *perfect-score sanity* submission.

Purpose: take the OFFICIAL Kaggle solution sheet (post-competition) and box every
answer back into a submission CSV, then locally grade all 943 with the exact grader
mirror used in `inference/scripts/analyze_run.py` (`auto_judge` over comma-split gold
slots + per-slot options). If the grader + format are understood correctly, this
should score 1.0 on Kaggle. It is a *validation harness*, not a leaderboard play —
it answers "do our grader-mirror and response format actually agree with Kaggle?".

Response format (Strategy A — hybrid):
  - Canonical `\\boxed{<value>}` for every answer. Multi-value (JSON-list) golds are
    comma-joined inside one box ("4, 16"); single values / intervals / letters verbatim.
  - EXCEPTION — percent answers ("158%", ...): `\\boxed{158%}` does NOT score, because
    `%` is a LaTeX comment char and the grader's boxed extractor truncates at it
    (-> "158"), while `\\%` is normalized away (-> "158"). The grader keeps the `%`
    in gold, so no boxed form can match. These 4 items instead use the plain
    final-answer sentence "The answer is 158%." which the grader's free-text
    extractor reads as "158%" and scores. (See postprocessing/FINDINGS.md.)

Source of truth: data/raw/_original/solution.csv  (the official grading sheet:
  columns id, answer, options, Usage, is_matharena; answer is a JSON string —
  a JSON list for multi-value items, else a bare value).

Output: submission/29_06/perfect_score_check/29_06_perfect_score_check.csv
  (id zero-padded to 4 digits to match the 0.745 winning reference; response column).
"""
import csv, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from grading.grader import Grader

SOLUTION = os.path.join(REPO, "data/raw/_original/solution.csv")
OUT_DIR = os.path.join(REPO, "submission/29_06/perfect_score_check")
OUT_CSV = os.path.join(OUT_DIR, "29_06_perfect_score_check.csv")

g = Grader()


def joined_value(raw_answer: str) -> str:
    """Official answer -> the value string to grade/box.
    JSON list -> comma-joined ("4, 16"); else verbatim (incl. intervals, letters)."""
    a = (raw_answer or "").strip()
    if a.startswith("["):
        try:
            return ", ".join(str(v) for v in json.loads(a))
        except Exception:
            pass
    return a


def build_response(value: str) -> str:
    """Strategy A: boxed canonical, percent -> plain final-answer sentence."""
    if "%" in value:
        return f"The answer is {value}."
    return "\\boxed{" + value + "}"


def grade(response: str, value: str, options) -> bool:
    """Mirror inference/scripts/analyze_run.py:judge_math exactly."""
    gold_slots = [s for s in g.split_by_comma(value)]
    if not gold_slots:
        return False
    opts = options if isinstance(options, list) and options else None
    opt_list = [opts] if (opts and len(gold_slots) == 1) else [None] * len(gold_slots)
    try:
        return bool(g.auto_judge(response, gold_slots, opt_list))
    except Exception:
        return False


def main():
    rows = sorted(csv.DictReader(open(SOLUTION)), key=lambda r: int(r["id"]))
    assert len(rows) == 943, f"expected 943 solution rows, got {len(rows)}"

    out_rows, npass, fails = [], 0, []
    for r in rows:
        iid = int(r["id"])
        value = joined_value(r["answer"])
        response = build_response(value)
        try:
            options = json.loads(r.get("options") or "[]")
        except Exception:
            options = []
        if grade(response, value, options):
            npass += 1
        else:
            fails.append((iid, r["answer"], value, response))
        out_rows.append({"id": f"{iid:04d}", "response": response})

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "response"])
        w.writeheader()
        w.writerows(out_rows)

    print(f"LOCAL GRADE (grader mirror): {npass}/943 pass ({100*npass/943:.2f}%)")
    print(f"wrote {len(out_rows)} rows -> {os.path.relpath(OUT_CSV, REPO)}")
    if fails:
        print(f"!! {len(fails)} items did NOT score locally — NOT submission-ready:")
        for x in fails[:20]:
            print("   FAIL", x)
        sys.exit(1)
    print("ALL 943 score locally — submission-ready (expect 1.0 if Kaggle grader == mirror).")


if __name__ == "__main__":
    main()

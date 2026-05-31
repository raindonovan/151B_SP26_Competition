"""Executable fixture harness for normalizer modes.

This checks raw grader-visible answers vs normalized outputs against a small
fixture sheet of high-confidence formatting cases.
"""

from __future__ import annotations

import argparse
import csv
import os as _os
import sys as _sys
from pathlib import Path

from hendrycks_local import extract_last_boxed_content, extract_mcq_letter, is_equiv
from normalizer import Normalizer

# ACTION 7 (Cursor #6): value-equality scorer alongside the existing strict (Hendrycks) one.
# value-match is the PRIMARY gating truth (mirrors the updated Kaggle grader); strict is the
# divergence/hedge signal. Import Grader via repo-root sys.path workaround (per ACTION 3).
_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)
from grading.grader import Grader  # noqa: E402

_GRADER = Grader()


def _value_equal(pred: str, gold: str) -> bool:
    try:
        return bool(_GRADER.is_equal(str(pred), str(gold), options=[]))
    except Exception:
        return False


def infer_item(row: dict[str, str]) -> dict:
    category = row.get("category", "free_single")
    question = row.get("question", "")
    item = {"id": int(row["id"]), "question": question}
    if category == "MCQ":
        item["options"] = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    return item


def raw_candidate(row: dict[str, str], item: dict) -> str:
    response = row["response"]
    if item.get("options"):
        return extract_mcq_letter(response)
    content = extract_last_boxed_content(response)
    return content or response


def evaluate(fixtures_path: str, mode: str) -> dict[str, int]:
    normalizer = Normalizer(mode=mode)
    totals = {
        "rows": 0,
        # strict (Hendrycks) — divergence/hedge signal
        "raw_strict_match": 0, "normalized_strict_match": 0, "improved_strict": 0,
        # value-equality — PRIMARY gating truth
        "raw_value_match": 0, "normalized_value_match": 0, "improved_value": 0,
    }
    with open(fixtures_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item = infer_item(row)
            raw = raw_candidate(row, item)
            normalized = normalizer.normalize_with_report(row["response"], item).candidate
            gold = row["gold_answer"]
            raw_strict = is_equiv(raw, gold)
            norm_strict = is_equiv(normalized, gold)
            raw_value = _value_equal(raw, gold)
            norm_value = _value_equal(normalized, gold)
            totals["rows"] += 1
            totals["raw_strict_match"] += int(raw_strict)
            totals["normalized_strict_match"] += int(norm_strict)
            totals["improved_strict"] += int((not raw_strict) and norm_strict)
            totals["raw_value_match"] += int(raw_value)
            totals["normalized_value_match"] += int(norm_value)
            totals["improved_value"] += int((not raw_value) and norm_value)
    return totals


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate normalizer modes on fixture CSV")
    parser.add_argument(
        "--fixtures",
        default=str(Path("testing") / "tier1_ground_truth.csv"),
        help="Fixture CSV path",
    )
    parser.add_argument(
        "--mode",
        choices=["conservative", "default", "aggressive"],
        default="default",
        help="Normalization mode",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    totals = evaluate(args.fixtures, args.mode)
    print(totals)


if __name__ == "__main__":
    main()
"""Executable fixture harness for normalizer modes.

This checks raw grader-visible answers vs normalized outputs against a small
fixture sheet of high-confidence formatting cases.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from hendrycks_local import extract_last_boxed_content, extract_mcq_letter, is_equiv
from normalizer import Normalizer


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
    totals = {"rows": 0, "raw_match": 0, "normalized_match": 0, "improved": 0}
    with open(fixtures_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item = infer_item(row)
            raw = raw_candidate(row, item)
            normalized = normalizer.normalize_with_report(row["response"], item).candidate
            gold = row["gold_answer"]
            raw_ok = is_equiv(raw, gold)
            normalized_ok = is_equiv(normalized, gold)
            totals["rows"] += 1
            totals["raw_match"] += int(raw_ok)
            totals["normalized_match"] += int(normalized_ok)
            totals["improved"] += int((not raw_ok) and normalized_ok)
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
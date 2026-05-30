"""Build a surrogate-gold review sheet for an inference run.

This is for manual inference analysis on private-set runs. It does NOT claim
true Kaggle accuracy. Instead it answers two review questions per item:

1. Does the run answer agree with our best available surrogate gold?
2. If we normalize the run answer, does it become more submit-safe?
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "postprocessing" / "scripts"))

from grading.judger import kaggle_like_is_equiv, math_correct_is_equiv  # noqa: E402
from normalizer import (  # noqa: E402
    Normalizer,
    load_items,
    load_master_answer_metadata,
    merge_item_metadata,
)


DIRTY_ANSWER_MARKERS = (
    "therefore",
    "hence",
    "because",
    "answer is",
    "we get",
    "we have",
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-jsonl", required=True, help="Inference run JSONL to review")
    parser.add_argument("--output-csv", required=True, help="Review CSV to write")
    parser.add_argument(
        "--mode",
        default="default",
        choices=["conservative", "default", "aggressive"],
        help="Normalizer mode to evaluate",
    )
    parser.add_argument(
        "--items-path",
        default=str(REPO_ROOT / "private.jsonl"),
        help="Base item metadata JSONL",
    )
    parser.add_argument(
        "--master-answers-path",
        default=str(REPO_ROOT / "data" / "MASTER_ANSWERS.csv"),
        help="Surrogate-gold metadata table",
    )
    parser.add_argument(
        "--tracker-path",
        default=str(REPO_ROOT / "data" / "master_item_tracker.csv"),
        help="Master tracker with flags such as undercount/backsolve_disagree",
    )
    return parser


def load_tracker_metadata(csv_path: str) -> dict[int, dict[str, Any]]:
    metadata: dict[int, dict[str, Any]] = {}
    path = Path(csv_path)
    if not path.exists():
        return metadata
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item_id = row.get("id")
            if not item_id:
                continue
            metadata[int(item_id)] = row
    return metadata


def looks_dirty_answer(answer: str) -> bool:
    text = (answer or "").strip()
    if not text:
        return False
    if "\n" in text or len(text) > 160:
        return True
    lowered = text.lower()
    if any(marker in lowered for marker in DIRTY_ANSWER_MARKERS):
        return True
    if lowered.count(". ") >= 1:
        return True
    return False


def choose_surrogate_gold(item: dict[str, Any]) -> tuple[str, str, str]:
    wolfram = (item.get("wolfram_answer") or "").strip()
    wolfram_conf = str(item.get("wolfram_confidence") or "").upper()
    if wolfram and wolfram_conf == "HIGH" and not looks_dirty_answer(wolfram):
        return wolfram, "wolfram_high", "high"

    teacher_values = [
        (item.get("teacher_sonnet") or "").strip(),
        (item.get("teacher_gpt4") or "").strip(),
        (item.get("teacher_oss") or "").strip(),
    ]
    teacher_values = [value for value in teacher_values if value]
    if teacher_values and len(set(teacher_values)) == 1 and not looks_dirty_answer(teacher_values[0]):
        return teacher_values[0], "teacher_unanimous", "high"

    sheet_best = (item.get("sheet_best_answer") or "").strip()
    sheet_conf = item.get("sheet_confidence") or 0
    sheet_tier = item.get("sheet_tier")
    if (
        sheet_best
        and not looks_dirty_answer(sheet_best)
        and sheet_tier in {1, 2, "1", "2", "T1", "T2"}
        and float(sheet_conf) >= 80
    ):
        return sheet_best, "sheet_high_conf", "medium"

    backsolve = (item.get("backsolve_answer") or "").strip()
    backsolve_conf = item.get("backsolve_confidence") or 0
    if backsolve and not looks_dirty_answer(backsolve) and float(backsolve_conf) >= 80:
        return backsolve, "backsolve_high_conf", "medium"

    if sheet_best and not looks_dirty_answer(sheet_best):
        return sheet_best, "sheet_fallback", "low"
    return "", "", ""


def run_surface(row: dict[str, Any]) -> tuple[str, str]:
    response = (row.get("response") or "").strip()
    if response:
        return response, "response"

    voted = (row.get("voted_answer") or "").strip()
    if voted:
        return f"\\boxed{{{voted}}}", "voted_answer"

    samples = row.get("samples") or []
    if isinstance(samples, list) and samples:
        first = samples[0]
        first_response = (first.get("response") or "").strip()
        if first_response:
            return first_response, "sample0_response"
        extracted = (first.get("extracted_answer") or "").strip()
        if extracted:
            return f"\\boxed{{{extracted}}}", "sample0_extracted"
    return "", "missing"


def kaggle_like_match(candidate: str, surrogate: str, item_type: str) -> bool:
    candidate = (candidate or "").strip()
    surrogate = (surrogate or "").strip()
    if not candidate or not surrogate:
        return False
    if item_type == "MCQ":
        return candidate.upper() == surrogate.upper()
    return bool(kaggle_like_is_equiv(candidate, surrogate))


def math_correct_match(candidate: str, surrogate: str, item_type: str) -> str:
    verdict = math_correct_is_equiv(candidate, surrogate, item_type=item_type)
    if verdict is None:
        return "UNKNOWN"
    return "TRUE" if verdict else "FALSE"


def recommended_action(
    *,
    raw_candidate: str,
    normalized_candidate: str,
    surrogate_gold: str,
    surrogate_quality: str,
    raw_match: bool,
    normalized_match: bool,
    flags: list[str],
    tracker_flags: str,
) -> str:
    if not raw_candidate and not normalized_candidate:
        return "NO_ANSWER"
    if not surrogate_gold:
        return "MANUAL_NO_SURROGATE"
    if surrogate_quality == "low":
        return "MANUAL_LOW_CONF_SURROGATE"
    if normalized_match and not raw_match:
        if any(flag.startswith("UNDERCOUNT_") for flag in flags):
            return "SUBMIT_NORMALIZED_UNDERCOUNT"
        return "SUBMIT_NORMALIZED"
    if raw_match:
        return "SUBMIT_AS_IS"
    if "undercount" in tracker_flags:
        return "MANUAL_UNDERCOUNT_REVIEW"
    if "backsolve_disagree" in tracker_flags:
        return "LOW_PRIORITY_BACKSOLVE_CHECK"
    return "HOLD"


def main() -> int:
    args = build_arg_parser().parse_args()
    base_items = load_items(args.items_path)
    master_answers = load_master_answer_metadata(args.master_answers_path)
    tracker = load_tracker_metadata(args.tracker_path)
    items = merge_item_metadata(base_items, master_answers)
    normalizer = Normalizer(mode=args.mode)

    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "id",
        "run_surface",
        "item_type",
        "question_preview",
        "raw_candidate",
        "normalized_candidate",
        "normalizer_flags",
        "surrogate_gold",
        "surrogate_source",
        "surrogate_quality",
        "surrogate_dirty",
        "raw_matches_surrogate",
        "normalized_matches_surrogate",
        "raw_math_correct",
        "normalized_math_correct",
        "tracker_best_answer",
        "tracker_flags",
        "tracker_action",
        "agreement_rate",
        "recommended_action",
    ]

    action_counts: Counter[str] = Counter()
    with open(args.run_jsonl, encoding="utf-8") as in_handle, output_path.open(
        "w", newline="", encoding="utf-8"
    ) as out_handle:
        writer = csv.DictWriter(out_handle, fieldnames=fieldnames)
        writer.writeheader()

        for line in in_handle:
            record = json.loads(line)
            item_id = int(record["id"])
            item = dict(items.get(item_id, {"id": item_id}))
            tracker_row = tracker.get(item_id, {})
            if tracker_row:
                item.update({f"tracker_{k}": v for k, v in tracker_row.items() if v not in {None, ""}})

            surface, surface_kind = run_surface(record)
            extraction = normalizer.extract_answer(surface, item) if surface else None
            raw_candidate = (extraction.candidate if extraction else "").strip()
            normalized = normalizer.normalize_with_report(surface, item) if surface else None
            normalized_candidate = normalized.candidate if normalized else ""
            item_type = normalized.item_type if normalized else normalizer.classify_type(item)
            flags = normalized.flags if normalized else []

            surrogate_gold, surrogate_source, surrogate_quality = choose_surrogate_gold(item)
            surrogate_dirty = looks_dirty_answer(surrogate_gold)
            raw_match = kaggle_like_match(raw_candidate, surrogate_gold, item_type)
            normalized_match = kaggle_like_match(normalized_candidate, surrogate_gold, item_type)
            raw_math_correct = math_correct_match(raw_candidate, surrogate_gold, item_type)
            normalized_math_correct = math_correct_match(normalized_candidate, surrogate_gold, item_type)
            tracker_flags = tracker_row.get("format_flags", "")
            action = recommended_action(
                raw_candidate=raw_candidate,
                normalized_candidate=normalized_candidate,
                surrogate_gold=surrogate_gold,
                surrogate_quality=surrogate_quality,
                raw_match=raw_match,
                normalized_match=normalized_match,
                flags=flags,
                tracker_flags=tracker_flags,
            )
            action_counts[action] += 1

            writer.writerow(
                {
                    "id": item_id,
                    "run_surface": surface_kind,
                    "item_type": item_type,
                    "question_preview": (item.get("question") or "")[:120].replace("\n", " "),
                    "raw_candidate": raw_candidate,
                    "normalized_candidate": normalized_candidate,
                    "normalizer_flags": "|".join(flags),
                    "surrogate_gold": surrogate_gold,
                    "surrogate_source": surrogate_source,
                    "surrogate_quality": surrogate_quality,
                    "surrogate_dirty": surrogate_dirty,
                    "raw_matches_surrogate": raw_match,
                    "normalized_matches_surrogate": normalized_match,
                    "raw_math_correct": raw_math_correct,
                    "normalized_math_correct": normalized_math_correct,
                    "tracker_best_answer": tracker_row.get("best_answer", ""),
                    "tracker_flags": tracker_flags,
                    "tracker_action": tracker_row.get("action", ""),
                    "agreement_rate": record.get("agreement_rate", ""),
                    "recommended_action": action,
                }
            )

    print(f"wrote review sheet: {output_path}")
    for action, count in sorted(action_counts.items()):
        print(f"{action}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
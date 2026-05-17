#!/usr/bin/env python3
"""Post-inference shape filter: apply retroactively to SC JSONL files.

Reads JSONL with samples, applies shape_filter to reject malformed samples,
re-votes on filtered samples, and outputs modified JSONL + diff report.
"""

import json
import argparse
import sys
from collections import Counter
from pathlib import Path


def count_top_level_boxes(text: str) -> int:
    """Count \\boxed{} occurrences not nested inside another \\boxed{}."""
    count = 0
    depth = 0
    i = 0
    while i < len(text):
        if text[i : i + 7] == "\\boxed{":
            if depth == 0:
                count += 1
            depth += 1
            i += 7
        elif text[i] == "{" and depth > 0:
            depth += 1
            i += 1
        elif text[i] == "}" and depth > 0:
            depth -= 1
            i += 1
        else:
            i += 1
    return count


def apply_shape_filter(samples: list[dict], is_multi_answer: bool) -> tuple[bool, int]:
    """Apply shape filter to samples. Returns (fallback_used, n_dropped)."""
    n_dropped = 0
    for s in samples:
        n_boxes = count_top_level_boxes(s.get("response", ""))
        s["shape_rejected"] = n_boxes == 0 or (is_multi_answer and n_boxes > 1)
        if s["shape_rejected"]:
            n_dropped += 1

    # If all samples rejected, fall back to unfiltered
    if all(s.get("shape_rejected", False) for s in samples):
        for s in samples:
            s["shape_rejected"] = False
        return True, 0  # fallback used, report 0 dropped

    return False, n_dropped


def vote(candidates: list[str]) -> tuple[str, int, bool]:
    """Vote on candidate answers. Returns (winner, vote_count, tie_broken)."""
    if not candidates or all(c is None or c == "" for c in candidates):
        return "", 0, False
    candidates = [c for c in candidates if c]  # filter empty
    counts = Counter(candidates)
    max_count = max(counts.values())
    winners = sorted(a for a, c in counts.items() if c == max_count)
    tie_broken = len(winners) > 1
    return winners[0], max_count, tie_broken


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Input JSONL path")
    p.add_argument("--output-jsonl", required=True, help="Output JSONL path")
    p.add_argument("--output-csv", required=True, help="Output CSV (Kaggle format)")
    p.add_argument("--output-report", required=True, help="Output diff report")
    args = p.parse_args()

    input_path = Path(args.input)
    output_jsonl_path = Path(args.output_jsonl)
    output_csv_path = Path(args.output_csv)
    report_path = Path(args.output_report)

    # Create output directories
    output_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Statistics
    n_total = 0
    n_vote_changed = 0
    n_no_filter = 0
    n_fallback = 0
    diffs = []

    # Process JSONL
    rows = []
    with open(input_path) as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"ERROR: line {line_no}: {e}", file=sys.stderr)
                continue

            n_total += 1
            item_id = row.get("id")
            original_vote = row.get("voted_answer", "")
            gold = row.get("gold")
            samples = row.get("samples", [])
            is_mcq = row.get("is_mcq", False)
            is_multi_answer = isinstance(gold, list) and len(gold) > 1

            # Apply shape filter
            fallback_used, n_dropped = apply_shape_filter(samples, is_multi_answer)

            # Re-vote on filtered samples
            if n_dropped > 0 or fallback_used:
                vote_inputs = [s.get("extracted_answer", "") for s in samples
                               if not s.get("shape_rejected", False)]
                filtered_vote, vote_count, tie_broken = vote(vote_inputs)
                agreement_rate = vote_count / len(samples) if samples else 0
            else:
                filtered_vote = original_vote
                vote_count = row.get("agreement_rate", 0) * len(samples) if samples else 0
                agreement_rate = row.get("agreement_rate", 0)
                tie_broken = row.get("tie_broken", False)
                n_no_filter += 1

            if fallback_used:
                n_fallback += 1

            # Check if vote changed
            vote_changed = filtered_vote != original_vote
            if vote_changed:
                n_vote_changed += 1
                diffs.append({
                    "id": item_id,
                    "original": original_vote,
                    "filtered": filtered_vote,
                    "n_dropped": n_dropped,
                    "fallback": fallback_used,
                })

            # Update row with filtered vote
            row["voted_answer"] = filtered_vote
            row["agreement_rate"] = agreement_rate
            row["tie_broken"] = tie_broken
            row["shape_filter_applied"] = n_dropped > 0 or fallback_used
            row["shape_filter_n_dropped"] = n_dropped
            row["shape_filter_fallback"] = fallback_used

            rows.append(row)

    # Write output JSONL
    with open(output_jsonl_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Write output CSV (Kaggle format: id,prediction)
    with open(output_csv_path, "w") as f:
        f.write("id,prediction\n")
        for row in rows:
            item_id = row.get("id")
            pred = row.get("voted_answer", "")
            f.write(f"{item_id},{pred}\n")

    # Write report
    with open(report_path, "w") as f:
        f.write(f"Shape Filter Post-Inference Report\n")
        f.write(f"===================================\n\n")
        f.write(f"Input: {input_path}\n")
        f.write(f"Items processed: {n_total}\n")
        f.write(f"Items with no filtering: {n_no_filter}\n")
        f.write(f"Items with filtering applied: {n_total - n_no_filter}\n")
        f.write(f"Items with filter fallback: {n_fallback}\n")
        f.write(f"Items with vote changed: {n_vote_changed}\n\n")

        if diffs:
            f.write(f"Vote Changes ({len(diffs)} items):\n")
            f.write(f"id   | original_vote | filtered_vote | n_dropped | fallback\n")
            f.write(f"---  | ------------- | ------------- | --------- | --------\n")
            for diff in diffs:
                f.write(f"{diff['id']:4d} | {str(diff['original'])[:13]:13s} | {str(diff['filtered'])[:13]:13s} | {diff['n_dropped']:9d} | {str(diff['fallback']):8s}\n")
        else:
            f.write("No vote changes.\n")

    print(f"✓ Output JSONL: {output_jsonl_path}")
    print(f"✓ Output CSV: {output_csv_path}")
    print(f"✓ Report: {report_path}")
    print(f"\nSummary:")
    print(f"  Total items: {n_total}")
    print(f"  Vote changes: {n_vote_changed}")
    print(f"  Filter applied: {n_total - n_no_filter} items")
    print(f"  Filter fallback: {n_fallback} items")


if __name__ == "__main__":
    main()

"""Format post-processor for multi-answer free-form items.

Problem: For multi-answer questions, the model sometimes produces multiple
separate \\boxed{} entries (one per sub-answer) instead of the required single
\\boxed{v1, v2, ...} format. Items where the LAST \\boxed{} has no commas but
the response has multiple boxes are "fixable": we can consolidate the last N
unique boxed values into one comma-separated box.

Usage:
    python3 scripts/fix_submission_format.py \
        --input submissions/run09sc8_v1_private943.csv \
        --data  data/private.jsonl \
        --output submissions/run09sc8_v1_private943_fixed.csv \
        [--dry-run]   # print stats + examples, do not write CSV

Requires: data file (private.jsonl or public.jsonl) with 'options',
          'question', and 'answer' fields for the same IDs as the CSV.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path


def extract_all_boxed(text: str) -> list[str]:
    """Nested-brace-aware extractor for \\boxed{...} content."""
    results = []
    i = 0
    while i < len(text):
        pos = text.find("\\boxed{", i)
        if pos == -1:
            break
        depth = 1
        j = pos + 7
        while j < len(text) and depth > 0:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
            j += 1
        if depth == 0:
            results.append(text[pos + 7 : j - 1])
        i = pos + 7
    return results


def replace_last_boxed(text: str, new_content: str) -> str:
    """Replace the last \\boxed{...} in text with \\boxed{new_content}."""
    # Find last occurrence
    last_pos = -1
    i = 0
    while i < len(text):
        pos = text.find("\\boxed{", i)
        if pos == -1:
            break
        last_pos = pos
        i = pos + 7
    if last_pos == -1:
        return text + f" \\boxed{{{new_content}}}"
    # Find matching close brace
    depth = 1
    j = last_pos + 7
    while j < len(text) and depth > 0:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    return text[: last_pos] + f"\\boxed{{{new_content}}}" + text[j:]


def n_ans_placeholders(question: str) -> int:
    return question.count("[ANS]")


def is_mcq(item: dict) -> bool:
    return isinstance(item.get("options"), list) and bool(item["options"])


def is_multi_answer(item: dict) -> bool:
    if is_mcq(item):
        return False
    a = item.get("answer")
    if isinstance(a, list) and len(a) >= 2:
        return True
    # Fallback: [ANS] placeholder count
    return n_ans_placeholders(item.get("question", "")) >= 2


def expected_n_answers(item: dict) -> int:
    """Number of sub-answers expected for this item."""
    a = item.get("answer")
    if isinstance(a, list):
        return len(a)
    return max(1, n_ans_placeholders(item.get("question", "")))


def fix_response(response: str, n: int) -> tuple[str, str]:
    """
    For multi-answer items where the last \\boxed{} has no commas but there
    are multiple boxes: take the last N unique boxed values and consolidate
    into a single \\boxed{v1, v2, ...}.

    Returns (fixed_response, action) where action describes what was done.
    """
    boxes = extract_all_boxed(response)

    if not boxes:
        return response, "no_box"

    last = boxes[-1]
    if "," in last:
        return response, "already_comma"  # correct format, no change

    if len(boxes) == 1:
        return response, "single_no_comma"  # fixable but only one box, nothing to consolidate

    # Multiple boxes, last has no comma — take last N unique non-empty values
    unique_vals = []
    seen = set()
    for b in reversed(boxes):
        b_stripped = b.strip()
        if b_stripped and b_stripped not in seen:
            seen.add(b_stripped)
            unique_vals.insert(0, b_stripped)
        if len(unique_vals) == n:
            break

    if len(unique_vals) < n:
        # Not enough unique boxes — use what we have
        consolidated = ", ".join(unique_vals)
        action = f"partial_consolidate_{len(unique_vals)}_of_{n}"
    else:
        consolidated = ", ".join(unique_vals)
        action = f"consolidated_{n}"

    fixed = replace_last_boxed(response, consolidated)
    return fixed, action


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Input submission CSV (id, response)")
    p.add_argument("--data", required=True, help="Data JSONL (private.jsonl or public.jsonl)")
    p.add_argument("--output", required=True, help="Output fixed CSV")
    p.add_argument("--dry-run", action="store_true", help="Print stats/examples, do not write CSV")
    args = p.parse_args()

    # Load data
    data_path = Path(args.data)
    if not data_path.exists():
        # Fallback to public.jsonl
        fallback = Path(__file__).parent.parent / "data" / "public.jsonl"
        print(f"WARNING: {args.data} not found. Falling back to {fallback}", file=sys.stderr)
        data_path = fallback

    items = {}
    with open(data_path) as f:
        for line in f:
            d = json.loads(line)
            items[d["id"]] = d

    # Load submission CSV
    rows = []
    with open(args.input, newline="") as f:
        rows = list(csv.DictReader(f))

    # Process
    actions = {}
    fixed_rows = []
    examples = []

    for row in rows:
        rid = row["id"]
        try:
            item = items[int(rid)]
        except (KeyError, ValueError):
            fixed_rows.append(row)
            actions["id_not_found"] = actions.get("id_not_found", 0) + 1
            continue

        resp = row["response"]

        if not is_multi_answer(item):
            fixed_rows.append(row)
            actions["not_multi"] = actions.get("not_multi", 0) + 1
            continue

        n = expected_n_answers(item)
        fixed_resp, action = fix_response(resp, n)
        actions[action] = actions.get(action, 0) + 1

        fixed_rows.append({"id": rid, "response": fixed_resp})

        if action.startswith("consolidated") and len(examples) < 5:
            orig_boxes = extract_all_boxed(resp)
            new_boxes = extract_all_boxed(fixed_resp)
            examples.append({
                "id": rid,
                "n_expected": n,
                "orig_last_box": orig_boxes[-1] if orig_boxes else "",
                "orig_n_boxes": len(orig_boxes),
                "new_last_box": new_boxes[-1] if new_boxes else "",
            })

    # Report
    multi_count = sum(1 for row in rows
                      if int(row["id"]) in items and is_multi_answer(items[int(row["id"])]))
    fixable = actions.get("consolidated_2", 0) + sum(
        v for k, v in actions.items() if k.startswith("consolidated_")
    )

    print(f"\nInput: {args.input}")
    print(f"Data:  {data_path} ({len(items)} items loaded)")
    print(f"Total rows: {len(rows)}, multi-answer: {multi_count}")
    print(f"\nAction breakdown:")
    for k, v in sorted(actions.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print(f"\nRows fixed (consolidated): {fixable}")
    print(f"Rows unchanged: {len(rows) - fixable}")

    print(f"\n--- 5 example fixes ---")
    for e in examples:
        print(f"  id={e['id']} | n_expected={e['n_expected']} | orig_boxes={e['orig_n_boxes']} "
              f"| orig_last={e['orig_last_box']!r:.40} | new_last={e['new_last_box']!r:.40}")

    if args.dry_run:
        print("\n[DRY RUN] No output written.")
        return

    # Verify byte-identical for non-multi rows
    non_multi_orig = {r["id"]: r["response"] for r in rows
                      if int(r["id"]) in items and not is_multi_answer(items[int(r["id"])])}
    non_multi_fixed = {r["id"]: r["response"] for r in fixed_rows
                       if r["id"] in non_multi_orig}
    mismatches = sum(1 for k in non_multi_orig if non_multi_orig[k] != non_multi_fixed.get(k))
    if mismatches:
        print(f"ERROR: {mismatches} non-multi rows differ between input and output!", file=sys.stderr)
        sys.exit(1)
    print(f"\nVerified: all {len(non_multi_orig)} non-multi rows are byte-identical.")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "response"],
                                quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(fixed_rows)

    print(f"Written: {args.output} ({len(fixed_rows)} rows)")


if __name__ == "__main__":
    main()

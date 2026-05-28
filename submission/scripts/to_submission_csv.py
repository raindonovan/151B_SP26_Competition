"""Convert a model-output JSONL to a Kaggle submission CSV.

Two input schemas supported:
  - Deterministic runner (run_vllm_experiment.py): each row has
    `id` and `response` fields plus per-run metadata.
  - Self-consistency runner (run_vllm_sc.py): each row has `id`,
    `samples` (list of N completion objects), and `voted_answer`
    plus per-run metadata. For SC, we emit the full response text
    of the sample whose `extracted_answer` matches `voted_answer`.
    If no sample matches voted_answer (shouldn't happen — vote
    pulls from extracted_answers, so at least one sample is
    guaranteed to match), falls back to samples[0].response.

Output CSV: exactly two columns (id, response), header row,
RFC 4180 with QUOTE_ALL. Inner double quotes escaped as "".
Newlines, commas, backslashes inside response preserved verbatim.
Uses Python's csv module — no hand-rolled escaping.

Validation: input must contain exactly the set of IDs in the
--expected-ids file (no missing, no extras, no duplicates).
Aborts with first 5 missing + first 5 extras if any mismatch.

--expected-ids accepts either format:
  - Slice JSON ({"slice_id": ..., "ids": [...]})
  - Kaggle-style JSONL (one object per line with "id" field)
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


def load_expected_ids(path: str) -> set:
    """Load expected IDs from either slice JSON or Kaggle-style JSONL.

    Auto-detects: tries to parse the entire file as JSON first; if it
    parses to a dict with an "ids" key, uses that. Otherwise treats it
    as JSONL (one JSON object per line, each with an "id" field).
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"expected-ids file not found: {path}")
    text = p.read_text()
    if not text.strip():
        raise ValueError(f"{path}: empty file")

    # Try slice-JSON format first
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "ids" in obj:
            return set(obj["ids"])
    except json.JSONDecodeError:
        pass  # Not a single JSON document; try JSONL

    # Fall back to JSONL
    ids = set()
    for line_num, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path}:{line_num}: not valid JSON: {e}") from e
        if "id" not in obj:
            raise ValueError(f"{path}:{line_num}: missing 'id' field")
        ids.add(obj["id"])
    if not ids:
        raise ValueError(f"{path}: no IDs found")
    return ids


def detect_runner_type(rows: list) -> str:
    """Auto-detect runner type from the first row's schema."""
    if not rows:
        return "deterministic"  # arbitrary; will fail validation downstream
    first = rows[0]
    if "samples" in first and "voted_answer" in first:
        return "sc"
    return "deterministic"


def extract_response_for_sc(row: dict) -> str:
    """Return the full response text of the sample whose extracted_answer
    matches voted_answer. Falls back to samples[0].response if no match
    (defensive — shouldn't happen since vote() picks from extracted answers).
    """
    voted = row.get("voted_answer", "")
    samples = row.get("samples", [])
    if not samples:
        return ""
    for s in samples:
        if s.get("extracted_answer", "") == voted:
            return s.get("response", "")
    return samples[0].get("response", "")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Path to model-output JSONL.")
    p.add_argument("--output", required=True, help="Path to write the submission CSV.")
    p.add_argument(
        "--expected-ids",
        required=True,
        help="Path to expected-IDs file (slice JSON or Kaggle-style JSONL).",
    )
    p.add_argument(
        "--runner-type",
        default="auto",
        choices=["auto", "deterministic", "sc"],
        help="Schema of the input JSONL. 'auto' detects from the first row.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Load input rows
    in_path = Path(args.input)
    if not in_path.exists():
        sys.stderr.write(f"ERROR: input file not found: {in_path}\n")
        return 1
    rows = []
    with open(in_path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                sys.stderr.write(f"ERROR: {in_path}:{line_num}: not valid JSON: {e}\n")
                return 1
            if "id" not in row:
                sys.stderr.write(f"ERROR: {in_path}:{line_num}: missing 'id' field\n")
                return 1
            rows.append(row)

    runner_type = args.runner_type
    if runner_type == "auto":
        runner_type = detect_runner_type(rows)
        print(f"Detected runner type: {runner_type}")
    else:
        print(f"Runner type (explicit): {runner_type}")

    # Load expected IDs
    try:
        expected = load_expected_ids(args.expected_ids)
    except (FileNotFoundError, ValueError) as e:
        sys.stderr.write(f"ERROR: {e}\n")
        return 1
    print(f"Expected IDs: {len(expected)} (from {args.expected_ids})")

    # Validate the ID set
    input_id_counts = Counter(r["id"] for r in rows)
    duplicates = sorted(i for i, c in input_id_counts.items() if c > 1)
    input_ids = set(input_id_counts.keys())
    missing = sorted(expected - input_ids)
    extras = sorted(input_ids - expected)

    errors = []
    if duplicates:
        errors.append(
            f"duplicate IDs in input ({len(duplicates)}): "
            f"{duplicates[:5]}{'...' if len(duplicates) > 5 else ''}"
        )
    if missing:
        errors.append(
            f"missing IDs ({len(missing)}): "
            f"{missing[:5]}{'...' if len(missing) > 5 else ''}"
        )
    if extras:
        errors.append(
            f"unexpected IDs in input ({len(extras)}): "
            f"{extras[:5]}{'...' if len(extras) > 5 else ''}"
        )

    if errors:
        sys.stderr.write("ERROR: ID validation failed:\n")
        for e in errors:
            sys.stderr.write(f"  - {e}\n")
        return 1

    # Sort rows by id for stable, reproducible output
    rows.sort(key=lambda r: r["id"])

    # Write CSV (RFC 4180 via Python's csv module)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["id", "response"])
        for row in rows:
            qid = row["id"]
            if runner_type == "sc":
                response = extract_response_for_sc(row)
            else:
                response = row.get("response", "")
            writer.writerow([qid, response])

    print(f"Wrote {len(rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

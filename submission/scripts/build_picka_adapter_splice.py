#!/usr/bin/env python3
"""
Build Pick A adapter splice CSV:
  - base: submission/30_05/slot4_aggressive/30_05_slot4_aggressive_v2.csv
  - overrides: submission/v5_part_tnr0.csv, submission/v5_part_tnr1.csv,
               submission/v5_part_tnr02.csv, submission/v5_part_tnr3.csv

Rule:
  For each id in base, use adapter response if present in any part CSV;
  otherwise keep base response.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import Dict, List, Tuple


def read_csv_rows(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalize_id(raw: str) -> int:
    # Handles "0000" and "0" consistently.
    return int(str(raw).strip())


def validate_schema(path: str, rows: List[Dict[str, str]]) -> None:
    if not rows:
        raise ValueError(f"{path}: empty CSV")
    keys = set(rows[0].keys())
    if keys != {"id", "response"}:
        raise ValueError(f"{path}: expected columns {{id,response}}, got {keys}")


def load_overrides(paths: List[str]) -> Tuple[Dict[int, str], List[int]]:
    merged: Dict[int, str] = {}
    collisions: List[int] = []
    for path in paths:
        rows = read_csv_rows(path)
        validate_schema(path, rows)
        for r in rows:
            iid = normalize_id(r["id"])
            resp = (r.get("response") or "").strip()
            if not resp:
                continue
            if iid in merged and merged[iid] != resp:
                collisions.append(iid)
            merged[iid] = r["response"]
    return merged, sorted(set(collisions))


def boxed_ratio(rows: List[Dict[str, str]]) -> float:
    if not rows:
        return 0.0
    n_boxed = sum(1 for r in rows if "\\boxed" in (r.get("response") or ""))
    return n_boxed / len(rows)


def parse_exclude_ids(raw: str) -> set[int]:
    out: set[int] = set()
    if not raw.strip():
        return out
    for tok in raw.split(","):
        tok = tok.strip()
        if not tok:
            continue
        out.add(int(tok))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base",
        default="submission/30_05/slot4_aggressive/30_05_slot4_aggressive_v2.csv",
    )
    parser.add_argument(
        "--parts",
        nargs="+",
        default=[
            "submission/v5_part_tnr0.csv",
            "submission/v5_part_tnr1.csv",
            "submission/v5_part_tnr02.csv",
            "submission/v5_part_tnr3.csv",
        ],
    )
    parser.add_argument(
        "--out",
        default="submission/30_05/slot4_aggressive/30_05_slot4_aggressive_v5splice.csv",
    )
    parser.add_argument(
        "--exclude-ids",
        default="",
        help="Comma-separated ids that must never be overridden by adapter.",
    )
    args = parser.parse_args()

    if not os.path.exists(args.base):
        raise FileNotFoundError(f"Missing base CSV: {args.base}")
    for p in args.parts:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Missing part CSV: {p}")

    base_rows = read_csv_rows(args.base)
    validate_schema(args.base, base_rows)
    if len(base_rows) != 943:
        raise ValueError(f"Base must have 943 rows, got {len(base_rows)}")
    base_ids = {normalize_id(r["id"]) for r in base_rows}
    if base_ids != set(range(943)):
        raise ValueError("Base ids must be exactly integers 0..942")

    overrides, collisions = load_overrides(args.parts)
    if collisions:
        raise ValueError(
            f"Conflicting adapter responses for ids across part CSVs: {collisions[:20]}"
        )

    exclude_ids = parse_exclude_ids(args.exclude_ids)

    out_rows: List[Dict[str, str]] = []
    changed = 0
    excluded_hits = 0
    seen_ids = set()
    for r in base_rows:
        iid = normalize_id(r["id"])
        if iid in seen_ids:
            raise ValueError(f"Duplicate id in base CSV: {iid}")
        seen_ids.add(iid)
        if iid in exclude_ids:
            out_resp = r["response"]
            if iid in overrides:
                excluded_hits += 1
        else:
            out_resp = overrides.get(iid, r["response"])
        if out_resp != r["response"]:
            changed += 1
        out_rows.append({"id": str(iid), "response": out_resp})

    if len(out_rows) != 943:
        raise ValueError(f"Output rows != 943: {len(out_rows)}")
    if len({normalize_id(r["id"]) for r in out_rows}) != 943:
        raise ValueError("Output ids are not unique")
    out_ids = {normalize_id(r["id"]) for r in out_rows}
    if out_ids != set(range(943)):
        raise ValueError("Output ids must be exactly integers 0..942")
    if any(not (r["response"] or "").strip() for r in out_rows):
        raise ValueError("Output has empty responses")

    ratio = boxed_ratio(out_rows)
    if ratio <= 0.5:
        raise ValueError(f"Boxed ratio <= 50% ({ratio:.2%})")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "response"])
        w.writeheader()
        w.writerows(out_rows)

    print(f"OK wrote: {args.out}")
    overrides_in_base = sum(1 for iid in overrides if iid in base_ids)
    overrides_outside = sum(1 for iid in overrides if iid not in base_ids)
    print(
        "rows=943 "
        f"changed_from_base={changed} "
        f"overrides_seen={len(overrides)} "
        f"overrides_in_base={overrides_in_base} "
        f"overrides_outside_base={overrides_outside} "
        f"exclude_ids_count={len(exclude_ids)} "
        f"exclude_ids_present_in_overrides={excluded_hits}"
    )
    print(f"boxed_ratio={ratio:.2%}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        raise

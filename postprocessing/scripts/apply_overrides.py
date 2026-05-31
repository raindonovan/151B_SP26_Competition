"""apply_overrides.py — per-item answer override onto a submission CSV.

Reuses the PROVEN Day-8 override mechanism (scripts/build_slots_1_4.py apply_override,
which produced the 0.745 submission):
  - MCQ (override value is a single uppercase letter A-Z): FULL-REPLACE the response
    with `\\boxed{LETTER}` — the grader takes the FIRST \\boxed{LETTER} for MCQ.
  - Free-form (everything else): APPEND `\n\n\\boxed{value}` — the grader takes the
    LAST \\boxed{} for free-form, so the appended box wins (last-box-wins).

Source CSV is read, overridden rows are replaced, all other rows pass through BYTE-FOR-BYTE.
Row order and schema (id,response) are preserved.

Usage:
  python3 postprocessing/scripts/apply_overrides.py \
    --source <submission.csv> --overrides <overrides.csv> --output <out.csv>

overrides.csv must have columns: id, override_value [, evidence (ignored)].
"""
from __future__ import annotations
import argparse, csv, re, sys

_MCQ_LETTER = re.compile(r"^[A-Z]$")


def apply_override(resp: str, value: str, is_mcq_letter: bool) -> str:
    """FULL-REPLACE the response with a single `\\boxed{value}`.

    We deliberately do NOT append: the grader's free-form extractor takes the LAST
    CONTIGUOUS GROUP of `\\boxed{}` (judger.extract_all_boxed), so appending
    `\n\n\\boxed{NEW}` after a response that already ends in a `$$\\boxed{...}$$`
    block MERGES the two box-groups (e.g. old `a,b` + new `c,d` → graded as `a,b,c,d`,
    wrong slot count). Verified empirically on ids 5/345/763 (10/10 multi-slot
    overrides graded FALSE under append). Full-replace guarantees the grader sees
    exactly the override value — correct for both MCQ (first-box) and free (last-box),
    and we are asserting NoThinking's answer IS the answer for these T3-verified items.
    """
    value = str(value).strip()
    return "\\boxed{" + value + "}"                # full-replace for ALL overrides
    # (is_mcq_letter retained in signature for callers; behaviour identical now)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--overrides", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()

    # load overrides {id -> value}
    ov: dict[str, str] = {}
    with open(args.overrides, newline="") as f:
        for r in csv.DictReader(f):
            ov[str(r["id"]).strip()] = r["override_value"]

    # stream source, replace matching ids
    with open(args.source, newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        if fields != ["id", "response"]:
            print(f"WARN: unexpected source schema {fields}", file=sys.stderr)
        rows = list(reader)

    applied = 0
    for row in rows:
        iid = str(row["id"]).strip()
        if iid in ov:
            val = ov[iid]
            is_letter = bool(_MCQ_LETTER.match(val.strip()))
            row["response"] = apply_override(row["response"], val, is_letter)
            applied += 1

    with open(args.output, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)

    print(f"source={args.source} rows={len(rows)} overrides_in={len(ov)} applied={applied} -> {args.output}")
    if applied != len(ov):
        print(f"WARN: {len(ov)-applied} override ids not found in source!", file=sys.stderr)


if __name__ == "__main__":
    main()

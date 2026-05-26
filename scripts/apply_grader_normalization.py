"""Grader-targeted submission normalizer.

Applies normalization ONLY to the content of the last \\boxed{...} in each
row's response/answer field. Everything else (reasoning prose, intermediate
boxes) is left untouched.

Two modes:
  dfrac_only — substitute \\dfrac→\\frac and \\tfrac→\\frac (DIAGNOSTIC PROBE
               ONLY — Kaggle sample_submission shows \\dfrac is canonical;
               this mode would CONVERT TO WRONG FORMAT. Kept for evidence.)
  minimal    — safe rules only: strip thin-space macros (\\, \\; \\! \\:)
               and strip \\left/\\right. Pure typography removal, never
               carries math meaning. SAFE for submission.

Column auto-detection: prefers "response" (actual submission schema), falls
back to "answer" (spec wording).
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import re
from collections import Counter
from typing import Optional

# ── Box extraction ────────────────────────────────────────────────────────────
def find_last_box(text: str) -> Optional[tuple[int, int, str]]:
    """Return (start, end, inner) for the last \\boxed{...} in text, with
    correct brace matching. start = index of first char of \\boxed, end = index
    just past closing brace. inner = content between braces (exclusive).
    Returns None if no boxed expression is found."""
    if not isinstance(text, str):
        return None
    matches = list(re.finditer(r"\\boxed\{", text))
    if not matches:
        return None
    m = matches[-1]
    open_brace_idx = m.end() - 1  # index of the '{'
    depth = 1
    i = m.end()
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    if depth != 0:
        return None  # unbalanced — leave row alone
    inner = text[m.end():i - 1]
    return (m.start(), i, inner)

# ── Per-rule normalizers ──────────────────────────────────────────────────────
_DFRAC_RE = re.compile(r"\\(?:dfrac|tfrac)\b")
_THIN_SPACE_RE = re.compile(r"\\[,;!:]")
_LEFT_RIGHT_RE = re.compile(r"\\(?:left|right)\b")
_COMMA_SP_RE = re.compile(r",\s+")

def apply_rules(inner: str, mode: str) -> tuple[str, dict[str, bool]]:
    """Apply the requested rule set to box-inner content.
    Returns (new_inner, fired_rules) where fired_rules is a dict of
    rule_name -> bool indicating which rules actually changed the string."""
    fired: dict[str, bool] = {}
    out = inner

    if mode == "dfrac_only":
        after = _DFRAC_RE.sub(r"\\frac", out)
        fired["dfrac_or_tfrac"] = after != out
        out = after
    elif mode == "minimal":
        after = _THIN_SPACE_RE.sub("", out)
        fired["thin_space"] = after != out
        out = after

        after = _LEFT_RIGHT_RE.sub("", out)
        fired["left_right"] = after != out
        out = after
    else:
        raise ValueError(f"unknown mode: {mode}")

    return out, fired

# ── Row processing ────────────────────────────────────────────────────────────
def normalize_row(text: str, mode: str) -> tuple[str, Optional[dict[str, bool]]]:
    """Return (new_text, fired_rules_or_None).
    fired_rules is None if the row was not modified at all (no box, NaN,
    unbalanced braces, or all rules no-ops)."""
    if not isinstance(text, str):
        return text, None
    box = find_last_box(text)
    if box is None:
        return text, None
    start, end, inner = box
    new_inner, fired = apply_rules(inner, mode)
    if new_inner == inner:
        return text, None
    new_text = text[:start] + "\\boxed{" + new_inner + "}" + text[end:]
    return new_text, fired

# ── Report generation ─────────────────────────────────────────────────────────
def write_report(
    report_path: str,
    *,
    mode: str,
    input_path: str,
    output_path: str,
    total_rows: int,
    rows_with_box: int,
    modified_examples: list[tuple[int, str, str]],
    unmodified_examples: list[tuple[int, str]],
    rule_counts: Counter,
) -> None:
    n_mod = len(modified_examples_full := modified_examples) and modified_examples  # placate linter
    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    lines = []
    lines.append(f"# Grader normalization report")
    lines.append("")
    lines.append(f"- Mode: `{mode}`")
    lines.append(f"- Input:  `{input_path}`")
    lines.append(f"- Output: `{output_path}`")
    lines.append("")
    lines.append(f"## Summary")
    lines.append(f"- Total rows: **{total_rows}**")
    lines.append(f"- Rows with at least one `\\boxed{{}}`: **{rows_with_box}**")
    n_modified = sum(rule_counts.values()) and len(modified_examples_full)
    # n_modified above is wrong (sum across rules ≠ row count). Use the real count:
    real_modified_count = rule_counts.get("__rows_modified__", 0)
    pct = (100.0 * real_modified_count / total_rows) if total_rows else 0.0
    lines.append(f"- Rows modified: **{real_modified_count}** ({pct:.2f}%)")
    lines.append("")
    lines.append(f"## Per-rule trigger counts (rows where rule fired)")
    rule_keys = [k for k in rule_counts.keys() if not k.startswith("__")]
    if rule_keys:
        for k in sorted(rule_keys):
            lines.append(f"- `{k}`: {rule_counts[k]}")
    else:
        lines.append("- (no rules fired on any row)")
    lines.append("")
    lines.append(f"## Sample modified rows (up to 10)")
    if modified_examples:
        for iid, before, after in modified_examples[:10]:
            lines.append(f"- **id={iid}**")
            lines.append(f"  - before: `{before}`")
            lines.append(f"  - after:  `{after}`")
    else:
        lines.append("- (no rows were modified)")
    lines.append("")
    lines.append(f"## Sample unmodified rows (5 random)")
    for iid, last_box in unmodified_examples:
        lines.append(f"- **id={iid}** last-box: `{last_box}`")
    lines.append("")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

# ── Main ──────────────────────────────────────────────────────────────────────
def process(input_path: str, output_path: str, mode: str, report_path: str) -> None:
    with open(input_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    # Auto-detect content column: prefer "response", fall back to "answer".
    content_col = "response" if "response" in fieldnames else (
        "answer" if "answer" in fieldnames else None
    )
    if content_col is None:
        raise ValueError(
            f"Input {input_path}: expected 'response' or 'answer' column, "
            f"got fieldnames={fieldnames}"
        )

    rule_counts: Counter = Counter()
    modified_examples: list[tuple[int, str, str]] = []
    unmodified_rows: list[tuple[int, str]] = []
    rows_with_box = 0

    for row in rows:
        raw_id = row.get("id", "")
        try:
            iid = int(raw_id)
        except (TypeError, ValueError):
            iid = raw_id  # type: ignore[assignment]
        original = row[content_col]

        # Track whether row contained at least one box (for sanity).
        if isinstance(original, str) and "\\boxed{" in original:
            rows_with_box += 1

        new_text, fired = normalize_row(original, mode)
        if fired is not None:
            row[content_col] = new_text
            rule_counts["__rows_modified__"] += 1
            for rule_name, did_fire in fired.items():
                if did_fire:
                    rule_counts[rule_name] += 1
            # Capture before/after of last box for the report
            before_box = find_last_box(original)
            after_box = find_last_box(new_text)
            if before_box and after_box and len(modified_examples) < 10:
                modified_examples.append((iid, before_box[2], after_box[2]))
        else:
            box = find_last_box(original) if isinstance(original, str) else None
            if box is not None:
                unmodified_rows.append((iid, box[2]))

    # 5 random unmodified samples (deterministic seed for reproducibility)
    rng = random.Random(42)
    if len(unmodified_rows) > 5:
        unmodified_sample = rng.sample(unmodified_rows, 5)
    else:
        unmodified_sample = unmodified_rows[:]

    # Write output CSV (preserve column order & quoting)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    write_report(
        report_path,
        mode=mode,
        input_path=input_path,
        output_path=output_path,
        total_rows=len(rows),
        rows_with_box=rows_with_box,
        modified_examples=modified_examples,
        unmodified_examples=unmodified_sample,
        rule_counts=rule_counts,
    )

    print(f"Mode: {mode}")
    print(f"  Total rows:       {len(rows)}")
    print(f"  Rows with box:    {rows_with_box}")
    print(f"  Rows modified:    {rule_counts.get('__rows_modified__', 0)}")
    for k in sorted(k for k in rule_counts if not k.startswith('__')):
        print(f"    rule {k}: {rule_counts[k]}")
    print(f"  Wrote: {output_path}")
    print(f"  Report: {report_path}")

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--mode", choices=["dfrac_only", "minimal"], required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    process(args.input, args.output, args.mode, args.report)

if __name__ == "__main__":
    main()

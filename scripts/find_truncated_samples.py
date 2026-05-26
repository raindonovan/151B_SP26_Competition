"""Classify samples in a hybrid-inference samples.jsonl as truncated, no-box, or ok.

Schema expected per JSONL row (mirrors run_hybrid_inference.py output):
  {"id": <int>, "samples": [<str>, ...], ...}

Token counting uses Qwen3-4B-Thinking-2507 tokenizer if available; otherwise
falls back to a whitespace-split heuristic (still useful for detecting
truncation, since the threshold is len ≥ max_tokens - 5).

Use --no-tokenizer to force the heuristic (faster, no model load).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from typing import Callable, Optional

BOXED_RE = re.compile(r"\\boxed\{")


def classify_sample(
    text: str,
    max_tokens: int,
    count_tokens: Callable[[str], int],
) -> str:
    """Return one of: 'truncated_max_tokens', 'no_boxed_answer', 'ok'."""
    if not isinstance(text, str):
        return "no_boxed_answer"
    if count_tokens(text) >= max_tokens - 5:
        return "truncated_max_tokens"
    if not BOXED_RE.search(text):
        return "no_boxed_answer"
    return "ok"


def make_token_counter(no_tokenizer: bool, model: Optional[str]) -> Callable[[str], int]:
    if no_tokenizer:
        return lambda s: len(s.split())
    try:
        from transformers import AutoTokenizer  # type: ignore
        m = model or "Qwen/Qwen3-4B-Thinking-2507"
        tok = AutoTokenizer.from_pretrained(m, trust_remote_code=True)
        return lambda s: len(tok.encode(s))
    except Exception as e:
        print(f"[warn] tokenizer load failed ({e}); falling back to whitespace heuristic",
              file=sys.stderr)
        return lambda s: len(s.split())


def process(
    input_path: str,
    max_tokens: int,
    output_path: str,
    report_path: str,
    count_tokens: Callable[[str], int],
) -> None:
    rows = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    total_samples = 0
    reason_counts: Counter = Counter()
    per_item_truncs: Counter = Counter()
    nonok: list[tuple[int, int, str]] = []

    for row in rows:
        iid = row.get("id")
        samples = row.get("samples", []) or []
        for sidx, s in enumerate(samples):
            total_samples += 1
            r = classify_sample(s, max_tokens, count_tokens)
            reason_counts[r] += 1
            if r != "ok":
                nonok.append((iid, sidx, r))
                if r == "truncated_max_tokens":
                    per_item_truncs[iid] += 1

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["item_id", "sample_idx", "reason"])
        for iid, sidx, reason in nonok:
            w.writerow([iid, sidx, reason])

    md = []
    md.append(f"# Truncation report")
    md.append("")
    md.append(f"- Input: `{input_path}`")
    md.append(f"- max_tokens used for threshold: **{max_tokens}**")
    md.append(f"- Total samples: **{total_samples}**")
    md.append(f"- Total rows (items): **{len(rows)}**")
    md.append("")
    md.append("## Counts by reason")
    for reason in ("ok", "truncated_max_tokens", "no_boxed_answer"):
        md.append(f"- `{reason}`: {reason_counts.get(reason, 0)}")
    md.append("")
    md.append("## Top 10 items by truncation count")
    top = per_item_truncs.most_common(10)
    if top:
        md.append("| item_id | truncated_samples |")
        md.append("|---|---|")
        for iid, n in top:
            md.append(f"| {iid} | {n} |")
    else:
        md.append("- (no items had any truncated samples)")
    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    print(f"Total samples: {total_samples}")
    print(f"  ok:                   {reason_counts.get('ok', 0)}")
    print(f"  truncated_max_tokens: {reason_counts.get('truncated_max_tokens', 0)}")
    print(f"  no_boxed_answer:      {reason_counts.get('no_boxed_answer', 0)}")
    print(f"Wrote: {output_path}")
    print(f"Wrote: {report_path}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--max-tokens", type=int, required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--no-tokenizer", action="store_true",
                   help="Skip HF tokenizer load; use whitespace-split heuristic.")
    p.add_argument("--model", default=None,
                   help="HF model name for tokenizer (default Qwen3-4B-Thinking-2507).")
    args = p.parse_args()

    counter = make_token_counter(args.no_tokenizer, args.model)
    process(args.input, args.max_tokens, args.output, args.report, counter)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""compute_r20_vote_dist.py — per-item SC vote distribution from raw R20 SC@8 samples.

Cursor amendment (a): the kitchen-sink close_vote criterion needs a true vote_margin
(top - second), which is NOT in the R20 analysis.csv. This reads the raw R20 SC@8 samples
(LFS file, hydrated on DSMLP) and computes, per item:
  top_vote_count, second_vote_count, vote_margin = top - second, n_unique_answers

Votes are grouped by the per-sample `extracted_answer` exact string (the same surface key
the SC vote itself used — this is a vote-distribution measurement, NOT a value-equality
re-vote). Empty/blank extracted answers are excluded from the distribution (and counted).

Output: inference/base_model/R20_eval_v1_sc8_p943_t32k_pp1/analysis/r20_vote_dist.csv
Columns: item_id, top_vote_count, second_vote_count, vote_margin, n_unique_answers
"""
from __future__ import annotations
import csv
import json
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
R20_SAMPLES = REPO / "inference/base_model/R20_eval_v1_sc8_p943_t32k_pp1/run14b_sc8_v1_private943_tok32k_pp1.jsonl"
OUT = REPO / "inference/base_model/R20_eval_v1_sc8_p943_t32k_pp1/analysis/r20_vote_dist.csv"


def main():
    rows = []
    margin_hist = Counter()
    with open(R20_SAMPLES, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            iid = rec["id"]
            samples = rec.get("samples", [])
            # vote key = per-sample extracted_answer exact string (matches SC vote semantics)
            answers = [str(s.get("extracted_answer", "")).strip() for s in samples]
            nonempty = [a for a in answers if a]
            counts = Counter(nonempty)
            ordered = counts.most_common()
            top = ordered[0][1] if ordered else 0
            second = ordered[1][1] if len(ordered) > 1 else 0
            margin = top - second
            n_unique = len(counts)
            rows.append({
                "item_id": iid,
                "top_vote_count": top,
                "second_vote_count": second,
                "vote_margin": margin,
                "n_unique_answers": n_unique,
            })
            margin_hist[margin] += 1

    rows.sort(key=lambda r: r["item_id"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["item_id", "top_vote_count", "second_vote_count",
                                          "vote_margin", "n_unique_answers"])
        w.writeheader()
        w.writerows(rows)

    # distribution stats
    m1 = margin_hist.get(1, 0)
    m2 = margin_hist.get(2, 0)
    m3 = margin_hist.get(3, 0)
    m4plus = sum(v for k, v in margin_hist.items() if k >= 4)
    m0 = margin_hist.get(0, 0)
    print(f"wrote {OUT} ({len(rows)} items)")
    print(f"vote_margin distribution: margin=0 (all-tie/no-clear): {m0}, "
          f"=1: {m1}, =2: {m2}, =3: {m3}, >=4: {m4plus}")
    print(f"  close (margin<=2): {m0 + m1 + m2}  |  decisive (margin>=4): {m4plus}")


if __name__ == "__main__":
    main()

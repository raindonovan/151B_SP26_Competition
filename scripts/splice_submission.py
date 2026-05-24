"""Splice base + adapter inference results into a single Kaggle submission.

For each of 943 items:
  - If ID appears in adapter JSONL → use adapter answer
  - Else → use base answer

Outputs:
  results/hybrid/submission.csv        (id, response)
  results/hybrid/routing_manifest.csv  (id, source, answer, votes)

Usage:
  python3 scripts/splice_submission.py \
    --base   results/hybrid/base_run.jsonl \
    --adapter results/hybrid/adapter_run.jsonl \
    --output-dir results/hybrid
"""

import argparse
import csv
import json
import os

N_ITEMS = 943


def load_jsonl(path: str) -> dict[int, dict]:
    results = {}
    if not os.path.exists(path):
        return results
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
                results[int(r["id"])] = r
            except Exception:
                pass
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="Base run JSONL")
    parser.add_argument("--adapter", default=None, help="Adapter run JSONL (optional)")
    parser.add_argument("--output-dir", default="results/hybrid")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    base = load_jsonl(args.base)
    adapter = load_jsonl(args.adapter) if args.adapter else {}

    print(f"Base results:    {len(base)} items")
    print(f"Adapter results: {len(adapter)} items")

    sub_rows = []
    manifest_rows = []
    missing = []

    for iid in range(N_ITEMS):
        if iid in adapter:
            r = adapter[iid]
            source = "adapter"
        elif iid in base:
            r = base[iid]
            source = "base"
        else:
            missing.append(iid)
            sub_rows.append({"id": iid, "response": ""})
            manifest_rows.append({
                "id": iid, "source": "MISSING",
                "answer": "", "votes": 0,
            })
            continue

        answer = r.get("voted_answer", "")
        response = r.get("response", "")
        votes = r.get("votes", 0)

        sub_rows.append({"id": iid, "response": response})
        manifest_rows.append({
            "id": iid,
            "source": source,
            "answer": answer,
            "votes": votes,
        })

    sub_path = os.path.join(args.output_dir, "submission.csv")
    with open(sub_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "response"])
        writer.writeheader()
        writer.writerows(sub_rows)

    manifest_path = os.path.join(args.output_dir, "routing_manifest.csv")
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "source", "answer", "votes"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    adapter_count = sum(1 for r in manifest_rows if r["source"] == "adapter")
    base_count = sum(1 for r in manifest_rows if r["source"] == "base")

    print(f"\nRouting: {adapter_count} adapter | {base_count} base | {len(missing)} MISSING")
    if missing:
        print(f"  Missing IDs: {missing[:10]}{'...' if len(missing) > 10 else ''}")
    print(f"Submission → {sub_path}")
    print(f"Manifest   → {manifest_path}")


if __name__ == "__main__":
    main()

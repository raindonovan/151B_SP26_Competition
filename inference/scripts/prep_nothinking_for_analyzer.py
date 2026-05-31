"""prep_nothinking_for_analyzer.py — one-off schema adapter for the NoThinking-943 run.

The NoThinking SC jsonl uses a DIFFERENT schema than the R-series SC runs:
  - `samples` is a list of raw response STRINGS (not dicts)
  - per-sample data lives in parallel arrays: `sample_extracted`, `sample_n_output_tokens`
  - no `is_mcq` / `options` / `max_new_tokens` / per-sample `hit_token_cap`

analyze_run.py (LOCKED, do NOT modify) expects each `samples[i]` to be a dict with
`response` / `extracted_answer` / `gen_tokens` / `hit_token_cap` / `temperature`, plus
row-level `voted_answer` / `max_new_tokens` / `n_samples` / `options` / `is_mcq`.

This script rewrites the NoThinking jsonl into that expected shape WITHOUT changing any
content — pure structural transform. Truncation is synthesized from
`sample_n_output_tokens >= BUDGET - 10` (BUDGET inferred = 8192, the observed hard cap).
is_mcq/options are backfilled from MASTER_ANSWERS category where possible (options stay
None — auto_judge handles None via is_equal, as the single-sample R08/R10 audits did).

Usage:
  python3 inference/scripts/prep_nothinking_for_analyzer.py \
        --in  <nothinking.jsonl> --out <adapted.jsonl> [--budget 8192] \
        [--run-id NT_eval_nothinking_sc8_p943_t8k]
"""
from __future__ import annotations
import argparse, csv, json, os, sys

BUDGET_DEFAULT = 8192  # observed hard token cap in the NoThinking run


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--budget", type=int, default=BUDGET_DEFAULT)
    p.add_argument("--run-id", default="NT_eval_nothinking_sc8_p943_t8k")
    p.add_argument("--master-answers", default="data/MASTER_ANSWERS.csv")
    args = p.parse_args()

    cat = {}
    if os.path.exists(args.master_answers):
        for r in csv.DictReader(open(args.master_answers)):
            try:
                cat[int(r["item_id"])] = (r.get("category") or "").strip()
            except (KeyError, ValueError):
                pass

    n = 0
    with open(args.inp) as f, open(args.out, "w") as out:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            iid = d["id"]
            samples = d.get("samples", [])
            extracted = d.get("sample_extracted", [])
            toks = d.get("sample_n_output_tokens", [])
            new_samples = []
            for i, resp in enumerate(samples):
                gen = toks[i] if i < len(toks) else 0
                new_samples.append({
                    "response": resp if isinstance(resp, str) else "",
                    "extracted_answer": extracted[i] if i < len(extracted) else "",
                    "gen_tokens": gen,
                    "hit_token_cap": bool(isinstance(gen, int) and gen >= args.budget - 10),
                    "temperature": d.get("temperature"),
                })
            is_mcq = (cat.get(iid) == "MCQ")
            out.write(json.dumps({
                "run_id": args.run_id,
                "id": iid,
                "is_mcq": is_mcq,
                "options": None,            # NoThinking row has none; auto_judge handles None
                "samples": new_samples,
                "voted_answer": d.get("voted_answer", ""),
                "method": "vllm-sc-nothinking",
                "model": "Qwen/Qwen3-4B-Thinking-2507",
                "max_new_tokens": args.budget,
                "n_samples": len(new_samples),
                "temperature": d.get("temperature"),
                "top_p": d.get("top_p"),
                # carry NoThinking-specific provenance through (analyzer ignores extras)
                "mode": d.get("mode"),
                "votes": d.get("votes"),
                "n_voting": d.get("n_voting"),
                "shape_fallback": d.get("shape_fallback"),
                "timestamp": d.get("timestamp"),
            }, ensure_ascii=False) + "\n")
            n += 1
    print(f"adapted {n} rows -> {args.out} (budget={args.budget})")


if __name__ == "__main__":
    main()

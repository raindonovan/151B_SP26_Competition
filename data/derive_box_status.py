#!/usr/bin/env python3
"""
derive_box_status.py — add the derived answer-status columns to data/samples/.

Refines the no-answer story that `finish_reason` (stop/length/null) only half-tells:
`finish_reason` describes the *generation* (a length-truncated sample can still carry
a `\\boxed{}`), so it is kept as-is. These columns describe the *answer*:

  has_box              bool   — grader can extract a `\\boxed{}` answer from `response`
  box_status           str    — boxed | cut | no_emit
                                 boxed   : has_box (an answer is present)
                                 cut     : no box, generation ran out of tokens first
                                 no_emit : no box, generation finished but never boxed
  box_status_inferred  bool   — True where cut/no_emit was inferred (the run did not log
                                 finish_reason), False where read from a logged signal
                                 or where has_box (boxed is always objective)

Classification (only 3 of 14 runs logged finish_reason, hence the inference):
  has_box                                              -> boxed       (inferred=False)
  finish_reason == length                              -> cut         (inferred=False)
  finish_reason == stop                                -> no_emit     (inferred=False)
  null finish · thinking · `<think>` never closed      -> cut         (inferred=True)
  null finish · thinking · `</think>` closed, no box   -> no_emit     (inferred=True)
  null finish · nothinking · est_tokens >= 90% budget  -> cut         (inferred=True)
  null finish · nothinking · est_tokens <  90% budget  -> no_emit     (inferred=True)
NoThinking uses a closed-`<think>` prefill, so `</think>` is not a truncation signal there,
and the sentence-ending heuristic is unreliable (NoThinking math output rarely ends on
punctuation even when it stopped naturally). Instead we test token-budget proximity:
est_tokens = len(response) / chars_per_token (calibrated from rows with gen_tokens, ~2.7),
cut iff within 10% of the run's token budget. (Cross-checked against `NT_probe98`, the one
NoThinking run that *did* log finish_reason: its no-box samples are short and all natural-stop
= no_emit, consistent with this rule.)

Idempotent. Rewrites samples.parquet (zstd, existing columns preserved) + samples.jsonl.
Run from repo root:  python3 data/derive_box_status.py
"""
import json, os, sys
import pyarrow as pa
import pyarrow.parquet as pq

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
from grading.grader import Grader

PARQUET = os.path.join(HERE, "samples", "samples.parquet")
JSONL = os.path.join(HERE, "samples", "samples.jsonl")
NEW_COLS = ["has_box", "box_status", "box_status_inferred"]

g = Grader()
CUT_FRAC = 0.90  # NoThinking null rows: cut iff est. tokens within 10% of the token budget


def has_box(resp: str) -> bool:
    if "\\boxed{" not in resp:
        return False
    try:
        return len(g.extract_all_boxed(resp)) > 0
    except Exception:
        return False


def classify(resp, finish_reason, think_mode, boxed, resp_len, budget, cpt):
    """-> (box_status, inferred)."""
    if boxed:
        return "boxed", False
    if finish_reason == "length":
        return "cut", False
    if finish_reason == "stop":
        return "no_emit", False
    # null finish_reason -> infer
    if think_mode == "thinking":
        # an unclosed <think> means generation stopped mid-reasoning -> truncated
        return ("no_emit", True) if "</think>" in resp else ("cut", True)
    # nothinking: token-budget proximity (</think> is a prefill; ending is unreliable)
    if budget and budget == budget:  # budget not NaN
        return ("cut", True) if (resp_len / cpt) >= CUT_FRAC * budget else ("no_emit", True)
    # last resort (no budget recorded): treat as finished-without-box
    return ("no_emit", True)


def main():
    t = pq.read_table(PARQUET)
    # drop prior derived cols so the script is idempotent
    keep = [c for c in t.column_names if c not in NEW_COLS]
    t = t.select(keep)

    resp = t.column("response").to_pylist()
    fr = t.column("finish_reason").to_pylist()
    run_id = t.column("run_id").to_pylist()
    tm = t.column("think_mode").to_pylist()
    gen_tok = t.column("gen_tokens").to_pylist()
    resp_len = [len(r) for r in resp]

    # calibrate chars-per-token from rows that recorded gen_tokens
    pairs = [(L, gt) for L, gt in zip(resp_len, gen_tok) if gt]
    cpt = sorted(L / gt for L, gt in pairs)[len(pairs) // 2] if pairs else 2.71
    # per-run token budget (for the NoThinking proximity test)
    runs = pq.read_table(os.path.join(HERE, "samples", "runs.parquet")).to_pandas().set_index("run_id")
    budget = {rid: runs.loc[rid, "token_budget"] for rid in runs.index}

    boxed = [has_box(r) for r in resp]
    status, inferred = [], []
    for r, f, m, b, L, rid in zip(resp, fr, tm, boxed, resp_len, run_id):
        s, inf = classify(r, f, m, b, L, budget.get(rid), cpt)
        status.append(s); inferred.append(inf)
    print(f"calibrated chars/token = {cpt:.2f} | NoThinking cut threshold = {CUT_FRAC:.0%} of budget")

    t = t.append_column("has_box", pa.array(boxed, pa.bool_()))
    t = t.append_column("box_status", pa.array(status, pa.string()))
    t = t.append_column("box_status_inferred", pa.array(inferred, pa.bool_()))
    pq.write_table(t, PARQUET, compression="zstd")

    # JSONL export — preserve key order + null handling (NaN/NA -> None)
    df = t.to_pandas()
    cols = list(df.columns)
    def clean(v):
        if v is None:
            return None
        try:
            import math
            if isinstance(v, float) and math.isnan(v):
                return None
        except Exception:
            pass
        if hasattr(v, "item"):
            v = v.item()
        return v
    with open(JSONL, "w") as out:
        for rec in df.to_dict(orient="records"):
            out.write(json.dumps({k: clean(rec[k]) for k in cols}, ensure_ascii=False) + "\n")

    # report
    from collections import Counter
    c = Counter(status)
    nb = c["cut"] + c["no_emit"]
    inf_nb = sum(1 for s, i in zip(status, inferred) if i and s != "boxed")
    print(f"rows: {t.num_rows:,} | columns now: {t.num_columns} (+{len(NEW_COLS)})")
    print(f"  boxed   {c['boxed']:,}")
    print(f"  no-box  {nb:,}  ->  cut {c['cut']:,} ({100*c['cut']/nb:.0f}%) | "
          f"no_emit {c['no_emit']:,} ({100*c['no_emit']/nb:.0f}%)")
    print(f"  of no-box, {inf_nb:,} labels inferred (null finish_reason), {nb-inf_nb:,} from a logged signal")
    print(f"wrote {os.path.relpath(PARQUET, REPO)} + {os.path.relpath(JSONL, REPO)}")


if __name__ == "__main__":
    main()

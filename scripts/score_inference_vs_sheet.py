"""Reusable per-item scoring: inference (or a slot sheet) vs an answer sheet.

Comparison uses gold_equiv (semantic value-equality) from scripts/gold_equiv.py.
Extraction mirrors inference/scripts/build_review_sheet.py: RAW last-boxed for
free-form, first-boxed letter for MCQ — NO normalization.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Literal, Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gold_equiv import gold_equiv  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
csv.field_size_limit(sys.maxsize)


def load_qtypes() -> dict[int, str]:
    """qtype per item for gold_equiv: 'MCQ' | 'free_multi' | 'free_single'."""
    qt: dict[int, str] = {}
    with open(REPO / "private.jsonl") as f:
        for line in f:
            r = json.loads(line)
            iid = int(r["id"])
            q = r.get("question", "") or ""
            if r.get("options"):
                qt[iid] = "MCQ"
            elif q.count("[ANS]") > 1:
                qt[iid] = "free_multi"
            else:
                qt[iid] = "free_single"
    return qt


def last_boxed(text: str) -> str:
    i = text.rfind("\\boxed{")
    if i < 0:
        return ""
    j = i + 7
    depth = 1
    while j < len(text) and depth > 0:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    return text[i + 7 : j - 1] if depth == 0 else ""


def first_letter(text: str) -> str:
    m = re.search(r"\\boxed\{([A-Za-z])\}", text)
    return m.group(1).upper() if m else ""


def extract_raw(response: str, qtype: str) -> str:
    response = response or ""
    if qtype == "MCQ":
        return first_letter(response)
    return last_boxed(response)


def _surface_from_inference_record(rec: dict) -> str:
    """Match build_review_sheet.py run_surface: response > \\boxed{voted} > sample0."""
    resp = (rec.get("response") or "").strip()
    if resp:
        return resp
    voted = (rec.get("voted_answer") or "").strip()
    if voted:
        return "\\boxed{" + voted + "}"
    samples = rec.get("samples") or []
    if samples:
        return samples[0].get("response", "") or ""
    return ""


def _load_response_source(path: str, qt: dict[int, str]) -> dict[int, str]:
    """Extract raw answer per item from a .jsonl inference run or an id,response CSV."""
    out: dict[int, str] = {}
    p = Path(path)
    if p.suffix == ".jsonl":
        with open(p) as f:
            for line in f:
                rec = json.loads(line)
                iid = int(rec["id"])
                out[iid] = extract_raw(_surface_from_inference_record(rec), qt.get(iid, "free_single"))
    else:  # CSV with id,response
        with open(p, newline="") as f:
            for row in csv.DictReader(f):
                iid = int(row["id"])
                out[iid] = extract_raw(row.get("response", ""), qt.get(iid, "free_single"))
    return out


def score_inference_vs_sheet(
    inference_jsonl_path: str,
    answer_sheet_csv_path: Optional[str],
    extractor_kind: Literal["raw", "normalized"] = "raw",
) -> pd.DataFrame:
    """Per-item scoring DataFrame.

    Columns: id, inference_raw, sheet_answer, sheet_source, agree (bool|None),
             confidence_tier, comparison_note.
    `answer_sheet_csv_path=None` → sheet_answer/agree are None (inference-only view).
    `extractor_kind` is "raw" (current behavior); "normalized" reserved for future.
    """
    qt = load_qtypes()
    inf = _load_response_source(inference_jsonl_path, qt)

    sheet: dict[int, str] = {}
    src: dict[int, str] = {}
    tier: dict[int, str] = {}
    if answer_sheet_csv_path:
        with open(answer_sheet_csv_path, newline="") as f:
            for row in csv.DictReader(f):
                iid = int(row["id"])
                sheet[iid] = row.get("answer", "") or row.get("response", "")
                src[iid] = row.get("source", "") or row.get("sheet_source", "") or row.get("source_quality", "")
                tier[iid] = row.get("tier", "") or row.get("confidence_tier", "")

    rows = []
    for iid in sorted(inf):
        qtype = qt.get(iid, "free_single")
        inf_raw = inf[iid]
        if answer_sheet_csv_path and iid in sheet:
            sa = sheet[iid]
            eq = gold_equiv(inf_raw, sa, qtype)
            note = "match" if eq is True else ("mismatch" if eq is False else "incomparable")
            rows.append(
                dict(id=iid, inference_raw=inf_raw, sheet_answer=sa, sheet_source=src.get(iid, ""),
                     agree=(eq is True), confidence_tier=tier.get(iid, ""), comparison_note=note)
            )
        else:
            note = "no-sheet-row" if answer_sheet_csv_path else "no-sheet"
            rows.append(
                dict(id=iid, inference_raw=inf_raw, sheet_answer=None, sheet_source=None,
                     agree=None, confidence_tier=None, comparison_note=note)
            )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    inf = str(REPO / "inference/results/run14b_sc8_v1_private943_tok32k_pp1_v3filtered.jsonl")
    anchor = str(REPO / "data/search/teachers/anchor_set_FINAL.csv")
    df = score_inference_vs_sheet(inf, anchor, extractor_kind="raw")
    total = len(df)
    scored = df[df["comparison_note"].isin(["match", "mismatch", "incomparable"])]
    print(f"total items        : {total}")
    print(f"with sheet row     : {len(scored)}")
    print(f"  agree (match)    : {int((df['agree'] == True).sum())}")
    print(f"  disagree         : {int((df['comparison_note'] == 'mismatch').sum())}")
    print(f"  incomparable     : {int((df['comparison_note'] == 'incomparable').sum())}")
    print(f"no-sheet-row       : {int((df['comparison_note'] == 'no-sheet-row').sum())}")

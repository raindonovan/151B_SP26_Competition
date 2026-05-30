"""Build slots 1-4 candidate sheets (30_05) + per-slot summaries.

Slot 1: undercount_plus_frac.csv (0.713 stack output) verbatim.
Slot 2: + anchor_set_FINAL.csv overlay (316 items).
Slot 3: + 4/4 teacher consensus on non-anchor items.
Slot 4: + 3/4-with-xhigh consensus on non-anchor, MCQ_single items.

Override mechanism (proven, per submission/29_05/RUN_REPORT.md):
  MCQ  -> full-replace response with \\boxed{LETTER}  (grader takes FIRST box)
  free -> append "\\n\\n\\boxed{value}"                (grader takes LAST box)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
csv.field_size_limit(sys.maxsize)

from score_inference_vs_sheet import load_qtypes, score_inference_vs_sheet  # noqa: E402

BASE = REPO / "submission/csvs/undercount_plus_frac.csv"  # canonical 0.713 stack output (943 rows)
ANCHOR = REPO / "data/search/teachers/anchor_set_FINAL.csv"
BREAKDOWN = REPO / "data/search/teachers/teacher_agreement_breakdown.csv"
RUN14B = REPO / "inference/results/run14b_sc8_v1_private943_tok32k_pp1_v3filtered.jsonl"
OUT = REPO / "submission/30_05"

SLOT_DIRS = {1: "slot1_control", 2: "slot2_anchor", 3: "slot3_bloc", 4: "slot4_aggressive"}


def load_csv_responses(p):
    with open(p, newline="") as f:
        return {int(r["id"]): r["response"] for r in csv.DictReader(f)}


def apply_override(resp, value, is_mcq):
    value = str(value).strip()
    if is_mcq:
        return "\\boxed{" + value + "}"
    return (resp.rstrip() if resp else "") + "\n\n\\boxed{" + value + "}"


def write_sheet(slot_n, responses):
    d = OUT / SLOT_DIRS[slot_n]
    d.mkdir(parents=True, exist_ok=True)
    path = d / "sheet.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "response"])
        for iid in sorted(responses):
            w.writerow([iid, responses[iid]])
    return path


def main():
    qt = load_qtypes()
    base = load_csv_responses(BASE)
    assert len(base) == 943, f"base not 943: {len(base)}"

    # MCQ_single (derived: has options AND <=1 [ANS] — documented; A8 range guards it)
    mcq_single = set()
    for line in open(REPO / "private.jsonl"):
        r = json.loads(line)
        iid = int(r["id"])
        q = r.get("question", "") or ""
        if r.get("options") and q.count("[ANS]") <= 1:
            mcq_single.add(iid)

    # anchor
    anchor, anchor_cat = {}, {}
    for row in csv.DictReader(open(ANCHOR)):
        iid = int(row["id"])
        anchor[iid] = row["answer"]
        anchor_cat[iid] = row.get("category", "")
    anchor_ids = set(anchor)

    # teacher answers
    T = {}
    for t in ["sonnet", "gpt4", "oss", "xhigh"]:
        T[t] = {int(r["id"]): (r["answer"] or "").strip()
                for r in csv.DictReader(open(REPO / f"data/search/teachers/{t}/answers.csv"))}

    # clusters
    clusters = {}
    for row in csv.DictReader(open(BREAKDOWN)):
        clusters[int(row["id"])] = (row["cluster_pattern"], json.loads(row["cluster_membership_json"]))

    is_mcq = lambda iid: qt.get(iid) == "MCQ"  # noqa: E731

    # SLOT 1
    slot1 = dict(base)

    # SLOT 2 (+anchor)
    slot2 = dict(slot1)
    for iid in anchor_ids:
        if iid in slot2:
            mcq = anchor_cat.get(iid, "").upper() == "MCQ" or is_mcq(iid)
            slot2[iid] = apply_override(slot2[iid], anchor[iid], mcq)

    # SLOT 3 (+4/4 non-anchor)
    slot3 = dict(slot2)
    s3 = []
    for iid in slot3:
        if iid in anchor_ids:
            continue
        pat, _ = clusters.get(iid, ("", []))
        if pat == "4":
            val = next((T[t].get(iid, "") for t in ["sonnet", "gpt4", "oss", "xhigh"] if T[t].get(iid, "")), "")
            if val:
                slot3[iid] = apply_override(slot3[iid], val, is_mcq(iid))
                s3.append(iid)

    # SLOT 4 (+3/4-with-xhigh, MCQ_single, non-anchor)
    slot4 = dict(slot3)
    s4 = []
    for iid in slot4:
        if iid in anchor_ids or iid not in mcq_single:
            continue
        pat, mem = clusters.get(iid, ("", []))
        if pat == "3+1":
            three = [c for c in mem if len(c) == 3]
            if three and "xhigh" in three[0]:
                val = T["xhigh"].get(iid, "") or next((T[t].get(iid, "") for t in three[0] if T[t].get(iid, "")), "")
                if val:
                    slot4[iid] = apply_override(slot4[iid], val, True)
                    s4.append(iid)

    slots = {1: slot1, 2: slot2, 3: slot3, 4: slot4}
    over_counts = {1: 0, 2: len(anchor_ids), 3: len(s3), 4: len(s4)}

    # write sheets + summaries
    raw_df = score_inference_vs_sheet(str(RUN14B), None)  # inference-only, for raw disagreement
    raw = dict(zip(raw_df["id"], raw_df["inference_raw"]))
    from score_inference_vs_sheet import extract_raw

    for n, resp in slots.items():
        path = write_sheet(n, resp)
        rows = sum(1 for _ in open(path)) - 1
        # local score vs anchor
        ldf = score_inference_vs_sheet(str(path), str(ANCHOR))
        ldf.to_csv(OUT / SLOT_DIRS[n] / "local_score_vs_anchor.csv", index=False)
        agree_anchor = int((ldf["agree"] == True).sum())
        # disagreement with raw inference
        slot_extract = {iid: extract_raw(resp[iid], qt.get(iid, "free_single")) for iid in resp}
        disagree_raw = sum(1 for iid in resp if (slot_extract[iid] or "") != (raw.get(iid, "") or ""))
        summary = {
            "slot": n, "dir": SLOT_DIRS[n], "rows": rows,
            "overrides_applied": over_counts[n],
            "override_source": {"anchor": len(anchor_ids) if n >= 2 else 0,
                                 "4/4_bloc": len(s3) if n >= 3 else 0,
                                 "3/4_xhigh_mcq": len(s4) if n >= 4 else 0},
            "agreement_with_anchor": agree_anchor,
            "disagreement_with_raw_inference": disagree_raw,
        }
        with open(OUT / SLOT_DIRS[n] / "score_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        print(f"slot{n}: rows={rows} overrides={over_counts[n]} anchor_agree={agree_anchor} disagree_raw={disagree_raw}")

    # sanity gates
    print("\n=== SANITY GATES ===")
    print(f"A6 slot2 anchor-agreement >=310 : {json.load(open(OUT/SLOT_DIRS[2]/'score_summary.json'))['agreement_with_anchor']}")
    print(f"A7 slot3 4/4 overrides (~150-250): {len(s3)}")
    print(f"A8 slot4 3/4-xhigh-mcq (~30-100) : {len(s4)}")
    print(f"all slots 943 rows: {all((sum(1 for _ in open(OUT/SLOT_DIRS[n]/'sheet.csv'))-1)==943 for n in slots)}")


if __name__ == "__main__":
    main()

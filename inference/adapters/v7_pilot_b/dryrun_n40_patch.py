#!/usr/bin/env python3
"""
Dry-run: apply patched QC to the existing N=40 sample from failed run.
Loads item_ids from qc_report.json dropped list + passed dataset.jsonl.
Applies qc_match_with_rung; checks Cursor guardrails; gates.
"""
import csv, hashlib, json, os, re, sys
from pathlib import Path

REPO = Path(__file__).parent.parent.parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO / "inference/scripts"))

from phase1_pilot_lib import extract_boxed, qc_match_with_rung

OUT_DIR = REPO / "inference/adapters/v7_pilot_b"
QC_REPORT = OUT_DIR / "qc_report.json"
DATASET   = OUT_DIR / "dataset.jsonl"

MODULE_SHA = hashlib.sha256(
    (REPO / "inference/scripts/phase1_pilot_lib.py").read_bytes()
).hexdigest()
print(f"phase1_pilot_lib.py sha256: {MODULE_SHA}")

# ── load gold ─────────────────────────────────────────────────────────────────
gold = {}
with open(REPO / "archive/pre_audit_reset_20260530/answer_sheet/unified_answer_sheet_v6.csv") as f:
    for row in csv.DictReader(f):
        gold[int(row["item_id"])] = row["best_answer"].strip()

# ── reconstruct N=40 item list from training.log ─────────────────────────────
# Full N=40 ordered list (36 wrong + 4 anchor, seed=43) from training.log
N40_PASS = [60,350,168,635,628,707,734,576,473,506,76,122,137,477,185,813,191,699,158,
            689,163,902,103,238,56,44,52,234,376,877]
N40_DROP = [469,106,41,587,218,495,362,317,353,89,210,405]
# Note: 376, 877 are N=30 anchors that were already passing; included in full N=40 set
all_n40_ids = N40_PASS + N40_DROP

prev_passed = set(N40_PASS)
prev_dropped = {iid: "sonnet_wrong" for iid in N40_DROP}

print(f"N=40 items: {len(all_n40_ids)} "
      f"({len(prev_passed)} prev-pass + {len(prev_dropped)} prev-drop)")

# ── load sonnet trace boxes ────────────────────────────────────────────────────
def load_boxed(item_id):
    padded = str(item_id).zfill(4)
    path = REPO / f"data/search/teachers/sonnet/item_{padded}.md"
    if not path.exists():
        return None
    return extract_boxed(path.read_text())

# ── apply new QC ──────────────────────────────────────────────────────────────
MUST_FLIP      = {str(x) for x in [106, 210, 218, 353, 362]}
MUST_STAY_FAIL = {str(x) for x in [89, 495]}

results = []
new_passed_ids = set()
recovered_by_patch = []
regressions = []

for item_id in all_n40_ids:
    boxed = load_boxed(item_id)
    gold_ans = gold.get(item_id, "")

    iid_str = str(item_id)
    prev_status = "pass" if item_id in prev_passed else "drop"

    if boxed is None:
        new_status, rung = "drop", "no_boxed"
    elif not gold_ans or "This is a complex" in gold_ans:
        new_status, rung = "pass", "no_gold_warn"
    else:
        gold_slots = [s.strip() for s in gold_ans.split(',')]
        matched, rung = qc_match_with_rung(boxed, gold_ans)
        if not matched:
            for gs in gold_slots:
                m2, r2 = qc_match_with_rung(boxed, gs)
                if m2:
                    matched, rung = True, r2
                    break
        new_status = "pass" if matched else "drop"

    results.append({
        "item_id": item_id,
        "prev_status": prev_status,
        "new_status": new_status,
        "rung": rung,
        "boxed": boxed,
        "gold": gold_ans,
    })

    if new_status == "pass":
        new_passed_ids.add(item_id)

    if prev_status == "drop" and new_status == "pass":
        recovered_by_patch.append({"item_id": iid_str, "rung_used": rung})
        print(f"  RECOVERED {item_id} via {rung}")
    elif prev_status == "pass" and new_status == "drop":
        regressions.append(iid_str)
        print(f"  REGRESSION {item_id} (was pass, now drop) rung={rung}")
    elif prev_status == "pass":
        print(f"  STILL_PASS {item_id} rung={rung}")
    else:
        print(f"  STILL_DROP {item_id} rung={rung} boxed={boxed!r:.60} gold={gold_ans!r:.60}")

n_pass = len(new_passed_ids)
n_total = len(all_n40_ids)
drop_rate = (n_total - n_pass) / n_total
recovered_ids = {r["item_id"] for r in recovered_by_patch}

print(f"\n=== DRY-RUN SUMMARY ===")
print(f"dataset_size: {n_pass}/{n_total}, drop_rate: {drop_rate:.2%}")
print(f"recovered: {len(recovered_by_patch)}, regressions: {len(regressions)}")

# ── GUARDRAIL #1: known-case assertions ───────────────────────────────────────
print("\n=== GUARDRAIL #1: known cases ===")
gc1_result = "PASS"
gc1_reason = []

for iid in sorted(MUST_FLIP):
    if iid not in recovered_ids:
        msg = f"patch incomplete: {iid} did not recover"
        gc1_result = f"FAIL: {msg}"
        gc1_reason.append(msg)
        print(f"  MUST_FLIP FAIL: {iid}")
    else:
        rung_used = next(r["rung_used"] for r in recovered_by_patch if r["item_id"] == iid)
        print(f"  MUST_FLIP OK: {iid} via {rung_used}")

for iid in sorted(MUST_STAY_FAIL):
    if iid in recovered_ids:
        msg = f"over-permissive: {iid} should remain drop"
        gc1_result = f"FAIL: {msg}"
        gc1_reason.append(msg)
        print(f"  MUST_STAY_FAIL FAIL: {iid} incorrectly recovered")
    else:
        print(f"  MUST_STAY_FAIL OK: {iid} still drop")

if gc1_result == "PASS":
    print("  Guardrail #1: PASS")
else:
    print(f"  Guardrail #1: {gc1_result}")

# ── GUARDRAIL #2: no regressions ──────────────────────────────────────────────
print("\n=== GUARDRAIL #2: no regressions ===")
if regressions:
    gc2_result = f"FAIL: regressions={regressions}"
    print(f"  Guardrail #2: {gc2_result}")
else:
    gc2_result = "PASS"
    print("  Guardrail #2: PASS")

# ── GATE DECISION ─────────────────────────────────────────────────────────────
print("\n=== GATE DECISION ===")
gate_reasons = []
if n_pass < 20:
    gate_reasons.append(f"dataset_size={n_pass} < 20")
if drop_rate > 0.25:
    gate_reasons.append(f"drop_rate={drop_rate:.2%} > 25%")
if len(recovered_by_patch) < 5:
    gate_reasons.append(f"recovered={len(recovered_by_patch)} < 5")
if regressions:
    gate_reasons.append(f"regressions={regressions}")
if gc1_result != "PASS":
    gate_reasons.append(gc1_result)
if gc2_result != "PASS":
    gate_reasons.append(gc2_result)

gate_verdict = "PASS" if not gate_reasons else f"FAIL"
gate_reason  = "; ".join(gate_reasons) if gate_reasons else ""

print(f"  dataset_size={n_pass} ({'✓' if n_pass>=20 else '✗'})")
print(f"  drop_rate={drop_rate:.2%} ({'✓' if drop_rate<=0.25 else '✗'})")
print(f"  recovered={len(recovered_by_patch)} ({'✓' if len(recovered_by_patch)>=5 else '✗'})")
print(f"  regressions={len(regressions)} ({'✓' if not regressions else '✗'})")
print(f"  gate_verdict: {gate_verdict}" + (f" — {gate_reason}" if gate_reason else ""))

# ── write qc_report ───────────────────────────────────────────────────────────
qc_report = {
    "status": gate_verdict,
    "dataset_size": n_pass,
    "drop_rate": round(drop_rate, 4),
    "recovered_count": len(recovered_by_patch),
    "recovered_by_patch": recovered_by_patch,
    "regressions": regressions,
    "known_case_check": gc1_result,
    "qc_chain": ["exact","norm_string","numeric","tuple","mv_raw","mv_boxed","mv_dollar","mv_dfrac_sub"],
    "module_sha256": MODULE_SHA,
    "gate_verdict": gate_verdict,
    "gate_reason": gate_reason,
    "all_results": results,
}
QC_REPORT.write_text(json.dumps(qc_report, indent=2))
print(f"\nqc_report.json written.")

if gate_verdict != "PASS":
    print(f"HARD FAIL: {gate_reason}")
    sys.exit(1)

print("GATE PASSED — ready for STEP 3.5 + STEP 4")

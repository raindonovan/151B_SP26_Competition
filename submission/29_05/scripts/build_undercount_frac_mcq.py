"""
Build undercount_frac_mcq.csv (Day 7)

Recipe: undercount_plus_frac.csv (Pick A, 0.713)
      + 16 MCQ-prepend-fix overrides from mcq_prepend_fix.csv
      → undercount_frac_mcq.csv (the three-lever stack — a Pick B candidate)

The 16 MCQ items are disjoint from the 8 frac items, so the merge is a clean union
(verified: no item appears in both override sets).

Empirical caveat (file in submission/29_05/SCORES.md):
  29_05 Build 2 (mcq_prepend_fix alone on slot4 base): 0.706 → 0.703 (-1 slice item, net).
  Of 16 attempted overrides, only 6 actually flipped letter (the other 10 already
  matched the teacher consensus letter in slot4). Net effect of the 6 real flips
  was -1 slice item.

Expected score for undercount_frac_mcq.csv (assuming additivity, which has held for
frac on slot4): 0.713 + (-0.003) = ~0.710. Likely NOT a Pick-B improvement over
the pure 0.713 frac stack — needs a submission probe to confirm whether the MCQ
prepend lever is net-positive on top of frac before we commit it to Pick B.
"""
import csv
import sys
from pathlib import Path

csv.field_size_limit(sys.maxsize)
REPO = Path("/home/claude/repo")

BASE = REPO / "submission/29_05/csvs/undercount_plus_frac.csv"
MCQ = REPO / "submission/29_05/csvs/mcq_prepend_fix.csv"
SLOT4 = REPO / "submission/25_08/csvs/slot4_undercount_expand.csv"
OUT = REPO / "submission/29_05/csvs/undercount_frac_mcq.csv"


def load(path):
    with open(path) as f:
        return {r["id"]: r["response"] for r in csv.DictReader(f)}


print("Loading base + override CSVs...")
slot4 = load(SLOT4)
mcq = load(MCQ)
base = load(BASE)
print(f"  slot4_undercount_expand: {len(slot4)} rows")
print(f"  mcq_prepend_fix:         {len(mcq)} rows")
print(f"  undercount_plus_frac:    {len(base)} rows")

# Compute the 16 MCQ-touched IDs (vs slot4 base)
mcq_ids = sorted([k for k in mcq if mcq[k] != slot4.get(k)], key=int)
print(f"MCQ-touched IDs ({len(mcq_ids)}): {mcq_ids}")

# Verify disjointness vs frac touches (sanity-check before merge)
frac_ids = sorted([k for k in base if base[k] != slot4.get(k)], key=int)
print(f"Frac-touched IDs ({len(frac_ids)}): {frac_ids}")
overlap = set(mcq_ids) & set(frac_ids)
assert not overlap, f"OVERLAP DETECTED — merge unsafe: {overlap}"
print("Disjoint — merge is a clean union.")

# Build the merged response set: start from base (undercount + frac),
# overlay MCQ responses for the 16 MCQ-touched IDs.
out = dict(base)
overlay_count = 0
for iid in mcq_ids:
    if mcq[iid] != base[iid]:
        out[iid] = mcq[iid]
        overlay_count += 1
print(f"Overlaid {overlay_count} MCQ responses onto base.")

# Sanity: total changed rows vs slot4 = 8 frac + 16 mcq = 24
changed = sum(1 for k in out if out[k] != slot4.get(k))
print(f"undercount_frac_mcq differs from slot4 on {changed} IDs (expect 24).")
assert changed == 24, f"Expected 24 changed rows, got {changed}"

# Preserve the original sort order (numerical 0..942)
out_ids = sorted(out.keys(), key=int)

print(f"Writing {OUT}...")
with open(OUT, "w", newline="") as f:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    w.writerow(["id", "response"])
    for iid in out_ids:
        w.writerow([iid, out[iid]])
print("Done.")

# Submission Audit Session — Normalizer-Only Diagnostic Slot

**Status**: DRAFT — Stage 1 (Locked Plan). Awaiting Rain stage-2 review.
**Author**: claude_strategy
**Date**: 2026-05-31 (Day 9 final day)
**Time budget**: deadline Sun 23:59 PT, ~12h remaining
**Slot allocation**: proposed `slot3_normalizer_only` (Rain to confirm/relabel)
**Slot budget burned today so far**: UNKNOWN — Rain to populate

---

## Hypothesis being tested

**Q**: What does the Tier-1 normalizer contribute on the Kaggle private slice (~283 items)?

The normalizer landed an audit-cleared GREEN verdict (commit 59c6861) with local diagnostics: +2 on the 547-item independent-gold subset, larger expected wins on the unmeasurable T4/T5 sheet_dependent subset. Local cannot tell us what those unmeasurable wins are worth on Kaggle. This slot is purely diagnostic to size the lever before stacking with Thunder rescues / NT-13 / overrides for downstream Pick B candidates.

**Expected Kaggle outcome**: 0.655–0.678 (per claude_vscode projection vs R20 raw ~0.646 baseline). Pick A locked at 0.745 for reference (not this slot's purpose).

**Decision this slot informs**: how to compose Pick B downstream — if normalizer delivers strongly on Kaggle, weight it heavily; if marginal, prioritize Thunder rescues + NT-13 stack.

---

## Inputs (locked)

| Field | Value |
|---|---|
| Source CSV | `submission/csvs/run14b_sc8_v1.csv` (R20 raw, 943 rows) |
| Normalizer commit | `59c6861` (HEAD) |
| Normalizer mode | `single` (default) |
| Overrides applied | `postprocessing/per_item_overrides.csv` (4 entries: 229=2, 308=12, 383=80, 498=15; all Qwen-derived, Rule #11 compliant) |
| Items metadata | `private.jsonl` |
| Output destination | `submission/30_05/slot3_normalizer_only/normalizer_only_v1.csv` |
| Diagnostic JSON | `submission/30_05/slot3_normalizer_only/normalizer_only_v1_report.json` |

NO other lever stacked: no NT-13 join, no Thunder rescues, no texas-oil, no Wolfram, no teacher overlays. Clean attribution.

---

## Stage 2 — Pre-flight checklist (Rain reviews before Stage 3 fires)

- [ ] Repo at HEAD 59c6861 (`git rev-parse --short HEAD`)
- [ ] Source CSV exists and is 943 rows: `wc -l submission/csvs/run14b_sc8_v1.csv` returns 944 (header + 943)
- [ ] Per-item overrides CSV has EXACTLY 4 entries: `wc -l postprocessing/per_item_overrides.csv` returns 5
- [ ] Override entries verified: 229/308/383/498, all `force_value`, all Qwen-derived per evidence column
- [ ] private.jsonl present and parseable
- [ ] Output directory does NOT exist yet (will be created at Stage 3); avoid clobbering a prior slot accidentally
- [ ] Disk avail >= 8GB (`df -h .`)
- [ ] 15/15 tests pass on current HEAD: pre-flight regression sanity (~10s)
- [ ] Slot label and budget confirmed: this slot is slot N of 5 today; remaining slots = 5 - N (Rain confirms before fire)

---

## Stage 3 — CSV construction (after Stage 2 sign-off)

Mechanical, one-shot construction. No improvisation.

```bash
cd /home/claude/repo

# Verify pre-flight one more time
git rev-parse --short HEAD  # expect 59c6861 or descendant
wc -l submission/csvs/run14b_sc8_v1.csv  # expect 944
wc -l postprocessing/per_item_overrides.csv  # expect 5

# Create output directory
mkdir -p submission/30_05/slot3_normalizer_only

# Run normalizer (same params used in build smoke + audit)
python3 postprocessing/scripts/normalizer.py \
  submission/csvs/run14b_sc8_v1.csv \
  submission/30_05/slot3_normalizer_only/normalizer_only_v1.csv \
  --items private.jsonl \
  --report submission/30_05/slot3_normalizer_only/normalizer_only_v1_report.json

# Verify output exists and row count matches
wc -l submission/30_05/slot3_normalizer_only/normalizer_only_v1.csv  # expect 944 (header + 943)
```

Stage 3 success criteria:
- Exit code 0
- 0 exceptions reported in stdout
- Output CSV has 944 lines (header + 943 rows)
- Report JSON parses cleanly

---

## Stage 4 — Self-verification (claude_strategy runs immediately after Stage 3)

Re-run the anchor checks from the build audit on the SUBMITTED CSV (not the smoke output):

```python
import csv, json
import sys; sys.path.insert(0,'postprocessing/scripts')
from normalizer import Normalizer
n = Normalizer(mode='single')
out = {r['id']: r['response'] for r in csv.DictReader(open('submission/30_05/slot3_normalizer_only/normalizer_only_v1.csv'))}
def lastbox(s):
    b = n.extract_all_boxed(s); return b[-1] if b else None

# REQUIRED anchors (all must pass before Stage 5):
assert lastbox(out['15']) == '8, NONE', f"item 15 anchor FAIL: {lastbox(out['15'])!r}"
assert lastbox(out['229']) == '2', f"item 229 override FAIL: {lastbox(out['229'])!r}"
assert lastbox(out['308']) == '12', f"item 308 override FAIL"
assert lastbox(out['383']) == '80', f"item 383 override FAIL"
assert lastbox(out['498']) == '15', f"item 498 override FAIL"
assert lastbox(out['302']) == 'H', f"item 302 anchor FAIL"
assert lastbox(out['839']) == 'G', f"item 839 anchor FAIL"

rep = json.load(open('submission/30_05/slot3_normalizer_only/normalizer_only_v1_report.json'))
fc = rep['flag_counts']
assert fc.get('OVERRIDE_FORCE_VALUE') == 4, f"OVERRIDE_FORCE_VALUE count FAIL"
assert len(rep['rows']) == 943, f"row count FAIL"

print("All Stage 4 anchors PASS. Ready for Cursor cross-check.")
```

If any anchor fails: STAGE 3 OUTPUT IS REJECTED. Investigation required before retry.

---

## Stage 5 — Cursor cross-check (paste-ready prompt)

After Stage 4 passes locally, paste this to Cursor:

```
@CURSOR
FROM: CLAUDE_STRATEGY
SUBJECT: Submission audit — normalizer-only diagnostic slot CSV cross-check
PRIORITY: HIGH — gates Kaggle submission

CONTEXT: Audit session per submission/30_05/AUDIT_SESSION_normalizer_only.md.
Build at HEAD 59c6861 was audited GREEN by you. This is the SUBMISSION-SPECIFIC verification:
the CSV that will be uploaded must match the build's expected behavior exactly.

VERIFY (each row PASS/FAIL):

1. CSV exists at submission/30_05/slot3_normalizer_only/normalizer_only_v1.csv
2. Row count = 944 (header + 943 data rows)
3. Column structure matches Kaggle template: id, response (verify against any prior submitted CSV)
4. Anchor values match build expectations:
   - item 15 last \boxed{} content == "8, NONE"
   - item 229 last \boxed{} content == "2"
   - item 308 last \boxed{} content == "12"
   - item 383 last \boxed{} content == "80"
   - item 498 last \boxed{} content == "15"
   - item 302 last \boxed{} content == "H"
   - item 839 last \boxed{} content == "G"
5. Flag counts in companion JSON match build report:
   - OVERRIDE_FORCE_VALUE == 4
   - LAST_BOX_KEPT == 239
   - CONSOLIDATED_* sum == 91
   - MULTI_RESCUE_ONLY == 7
   - INVALID_MCQ == 1
6. Rule #11 compliance: NO teacher overrides in submission_answer (verify per_item_overrides.csv has only Qwen-derived entries — check evidence column doesn't contain "wolfram", "teacher", "consensus" or similar)
7. No row missing data: every id has a non-empty response
8. No id duplicates

VERDICT FORMAT (<=200 words):
- GREEN: submission ready to fire
- YELLOW: specific issues with concrete fixes
- RED: do not submit; what's wrong

DO NOT
- Re-audit the build (already GREEN at 59c6861)
- Re-litigate the convergence plan
- Suggest stacking other levers (this is a clean-attribution diagnostic)
```

---

## Stage 6 — Rain final approval gate

After Cursor's GREEN/YELLOW verdict, Rain explicitly approves the fire with one of:
- "fire it"
- "kill it"
- "fix X first"

No fire without explicit Rain approval.

---

## Stage 7 — Submission fire

Rain manually uploads `submission/30_05/slot3_normalizer_only/normalizer_only_v1.csv` to the Kaggle submission page (per past pattern; claude_strategy does not interact with Kaggle directly).

Slot label on Kaggle: `D9_S3_NORMALIZER_ONLY_v1` (or Rain's preferred label).

---

## Stage 8 — Post-result signoff

When Kaggle score comes back:
- claude_strategy appends to `submission/REGISTRY.md` with:
  - slot label
  - Kaggle score
  - delta vs R20 raw baseline
  - delta vs expected (0.655-0.678)
  - rung/lever attribution: normalizer-only
- claude_strategy signoff to `strategy/SCRATCH.md` with: Kaggle result, diagnostic learning, implication for Pick B composition
- Cursor cross-check on the diagnostic interpretation if magnitude is surprising
- Result feeds into Pick B candidate construction (next audit session)

---

## Risk register (surface before fire)

1. **Unmeasurable Kaggle regression risk**: 4 no-box overrides + multi-slot fixes land disproportionately on sheet_dependent (unmeasurable) gold. Local +2 on independent-gold confirms no measurable regression, but unmeasurable Kaggle could be net negative if (e.g.) the override values are wrong on items NOT in independent-gold. Pre-mitigation: SC voting on the 4 HIGH items was 4/4 unanimous; very low probability of all 4 being wrong.

2. **Kaggle extractor behavior**: judger.extract_all_boxed takes last contiguous group. Normalizer's rebox safety comment documents that "Final answer: \boxed{...}" prefix breaks contiguity. Risk: if Kaggle uses a different extractor than our local judger, results could diverge. Mitigation: we have R20 raw as Kaggle anchor (~0.646 expected); if normalized comes in WAY lower than R20 raw, it signals extractor divergence not normalizer regression.

3. **Slot opportunity cost**: this slot uses 1 of 5 remaining. If kitchen-sink fires (conditional on Thunder), and Pick B Final fires, we have 3 slots between this and Pick B. Worth it to isolate normalizer signal.

---

## Kill conditions (any stage)

- Stage 2 pre-flight fails: investigate before retry
- Stage 3 exit code != 0 or row count mismatch: investigate
- Stage 4 anchor fails: REJECT the output CSV; do not advance
- Stage 5 Cursor RED: do not submit
- Stage 6 Rain says "kill it": don't submit
- Any stage takes > 60min without progress: escalate to Rain

---

## Expected total time

- Stage 2 review (Rain): ~5 min
- Stage 3 construction: ~5 min
- Stage 4 self-verification: ~5 min
- Stage 5 Cursor cross-check + verdict: ~10 min
- Stage 6 Rain approval: ~2 min
- Stage 7 fire: ~2 min
- Stage 8 signoff (post-result): ~10 min after Kaggle score returns

Total wall-clock from green-light to fire: ~30 min. Kaggle scoring: minutes-to-hours per past pattern.

---

## Notes

- This is the FIRST submission audit session of Day 9. Pattern locks discipline for downstream Pick B slots.
- Doc lives at `submission/30_05/AUDIT_SESSION_normalizer_only.md` for posterity (lifecycle artifact, not Kaggle artifact).
- Future audit sessions (Thunder-stacked slot, Pick B final, etc.) follow the same 8-stage structure with content adjusted.

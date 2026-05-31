# Pick B FINAL — pre-fire audit checklist

**Owner**: claude_strategy
**Date**: 2026-05-31 (Day 9 evening)
**Trigger**: predecessor flagged `build_pickb.py` smoke as "validated layered constructor on small input" but explicitly NOT covering the live-kitchen-sink edge cases. This document is the pre-fire audit checklist that closes those gaps.

## Non-kitchen-sink path: VERIFIED

`python3 submission/scripts/build_pickb.py --variant intermediate --thunder-stance intermediate --out-dir <out>` runs end-to-end on real inputs and produces 943-row CSV with 20 thunder + 13 NT-13 overlays = 33 overrides, 910 baseline-unchanged, no cross-layer conflicts. This path is safe.

## Kitchen-sink path: SILENT-EMPTY FAILURE MODE confirmed

Empirical verification of two failure modes for `--include-kitchensink`:

### Risk A — empty/missing rung dir
Script writes `WARN: no rung*.jsonl files found in <dir>` to stderr and reports `Kitchen-sink layer: 0 items`. Pipeline continues and produces output IDENTICAL to a no-kitchen-sink run (i.e., effectively variant=intermediate masquerading as variant=final).

### Risk B — schema drift
If `rung*.jsonl` exists but `sample_extracted` field is renamed/missing (e.g., field is now `samples_extracted` or `sample_answers`), script produces NO warning, reports `Kitchen-sink layer: 0 items`, and silently produces the intermediate-equivalent output.

### Hardcoded threshold (Risk D)
The strong-majority threshold `top_count >= 20` in `build_kitchensink_layer()` is hardcoded for "3 rungs × 16 SC = 48 samples." If actual sample-count-per-item differs (e.g., 2 rungs × 16 = 32, or 3 rungs × 8 = 24), threshold of 20 may be either too strict (drops good items) or impossible (no items overridden).

## Pre-fire checklist (DO BEFORE EVERY KITCHEN-SINK PICK B FINAL FIRE)

### 1. Verify kitchen-sink output existence
```bash
ls inference/base_model/kitchensink_<RUN_TAG>/rung*.jsonl
# Expected: at least 1 file, ideally 3 (rung1.jsonl, rung2.jsonl, rung3.jsonl per dispatch plan)
# If zero files: kitchen-sink crashed or never ran. STOP. Do not fire Pick B FINAL.
```

### 2. Verify schema match (CRITICAL)
```bash
head -1 inference/base_model/kitchensink_<RUN_TAG>/rung1.jsonl | python3 -m json.tool | head -20
# Verify the JSON includes fields:
#   - "id" (item id, int or string)
#   - "sample_extracted" (list of extracted answers)
# If field name is different: STOP. Either rename field or edit build_pickb.py before running.
```

### 3. Verify per-item sample count
```bash
python3 -c "
import json
from collections import Counter
counts = Counter()
for rf in sorted(__import__('pathlib').Path('inference/base_model/kitchensink_<RUN_TAG>').glob('rung*.jsonl')):
    for line in open(rf):
        r = json.loads(line)
        counts[r['id']] += len(r.get('sample_extracted', []))
print('items:', len(counts))
print('min/median/max samples per item:', min(counts.values()), sorted(counts.values())[len(counts)//2], max(counts.values()))
print('items with <20 samples (threshold-blocked):', sum(1 for v in counts.values() if v < 20))
"
# If median != 48, threshold may not align. Consider editing build_pickb.py threshold.
# If many items have <20 samples, kitchen-sink incomplete or threshold too strict.
```

### 4. Apply stop rule externally
The script does NOT enforce the stop rule. Operator MUST:
- Compute kitchen-sink layer overrides (using #3 above or running build_pickb.py with `--include-kitchensink` and inspecting the layer)
- Compare against indep-gold subset (items where we have HIGH-confidence external label)
- Count: +N correct overrides, M regressions
- Pass criteria: +N ≥ 1 AND M = 0 (per the locked stop rule)
- If fail: pass `--kitchensink-stop-rule-pass=False` to build_pickb.py to skip the layer

### 5. Run with explicit kitchen-sink flag
```bash
python3 submission/scripts/build_pickb.py \
  --variant final \
  --thunder-stance intermediate \
  --include-kitchensink \
  --kitchensink-run-dir inference/base_model/kitchensink_<RUN_TAG> \
  --out-dir submission/30_05/pickb_final
```

### 6. POST-RUN MANDATORY CHECK
Look at stdout for the line:
```
Kitchen-sink layer: N items (from <dir>)
```
If `N == 0`, the kitchen-sink layer is empty. THIS IS THE SILENT FAILURE.

If N == 0 was UNEXPECTED → stop. Diagnose schema, threshold, or stop-rule before re-running.
If N == 0 was EXPECTED (kitchen-sink failed stop rule) → the output is functionally Pick B intermediate; rename or label accordingly to avoid confusion.

### 7. Byte-level diff against intermediate
```bash
diff submission/30_05/pickb_final/pickb_final_v1.csv submission/30_05/pickb_intermediate/pickb_intermediate_v1.csv | head -50
```
If diff is empty → kitchen-sink contributed nothing. Identical to intermediate.
If diff shows N items × 2 lines (id+response) → kitchen-sink contributed N items. Verify count matches step 6.

### 8. Manifest review
```bash
grep '^.*,kitchensink,' submission/30_05/pickb_final/pickb_final_v1_manifest.csv | wc -l
```
Should equal N from step 6. If not, something else is wrong.

### 9. Eye-check at least 3 kitchen-sink overrides
Pick 3 items at random from the kitchen-sink layer. For each:
- Look at the original baseline answer
- Look at the kitchen-sink override value
- Verify the override is a plausible Qwen-derived answer (matches one of the 48 samples by majority)
- Verify the override survives `\boxed{}` formatting (no stray quotes, no LaTeX corruption)

## Anti-foot-guns

- **DO NOT** assume `--variant final` ALWAYS produces a different CSV than `--variant intermediate` just because the variant name is different. The variant name only affects output filename; the actual layer composition depends on flags + data presence.
- **DO NOT** trust that the script will alert you to schema drift. Silent-empty is the failure mode.
- **DO NOT** trust the stop-rule flag default of True. Always set it explicitly to match your external audit.
- **DO NOT** fire a kitchen-sink Pick B FINAL just because the build script exited cleanly. Clean exit + 0 kitchen-sink items = misleading filename.

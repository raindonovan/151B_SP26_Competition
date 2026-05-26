# DAY 2 SUBMISSION QUEUE -- 2026-05-27

Last updated: 2026-05-26 evening, migrated to repo 2026-05-27 ~01:30.
Status: planning ahead of Thunder completion.

> **Migration note**: Written before tonight's SIGKILL recovery on tnr-0. See `docs/IMMEDIATE_CONTEXT.md` for current restart status.

## Reference points

- Best real-inference: slot1_minimal_norm = 0.643
- Best diagnostic (sheet patches): info_4 = 0.671
- Tomorrow's 3 Kaggle slots available

## Submission queue (priority order)

### Slot 1 (morning) -- 3-PART HYBRID SPLICE
**Source**: Thunder A1 (SC=16 on 158 weak at 49K/24K) + adapter v5 on 391 trained + run14b_v3filtered on remaining 394.

**Build steps**:
1. Pull `inference/tnr-0-<TS>` once A1 completes
2. Extract SC=16 voted-answer CSV for 158 weak ids
3. Run `splice_csvs.py` (3-source priority splice)
4. Apply minimal normalizer
5. Submit to Kaggle

**Expected**: 0.65-0.68 range. Best case: SC=16 catches +5-10 weak items vs run14b's SC=8.

### Slot 2 (morning) -- NOTHINKING SUBMISSION (CONDITIONAL)
**Trigger**: B2 ran AND coverage reasonable.

**Source**: B2 v2 NoThinking inference (8192 max_tokens, batched, IF tnr-1 restarted).

**Expected**: 0.55-0.65 range. Provides voting diversity.

**SKIP CRITERIA**:
- B2 v1 skipped (B1 found <3/18 boxed) -- defunct
- tnr-1 not restarted (B2 stayed serial with 5K cap + 17% truncation) -- coverage ~50-66%, weak slot, consider skipping

### Slot 3 (afternoon) -- OVERRIDE RESOLUTION
**Source**: `slot1_minimal_norm_setC_5flip.csv`.

**Overrides** (5 MCQ items, sheet-vs-slot1 disagreements):
- id=184: E -> J
- id=317: D -> H
- id=772: J -> H
- id=831: C -> E (strongest sheet endorsement)
- id=887: C -> I

**Expected**: 0.643 + 0.005*k. Range 0.643-0.648.

## v7 GO/NO-GO decision (evening of Day 2)

**Threshold**: 0.68 on Day 2 best real-inference.

| Day 2 best | Action |
|---|---|
| >= 0.68 | **v7 NO-GO**. Pivot to GenSelect + Sheet v6 + extended PACE |
| 0.65-0.68 | **v7 GO-CONDITIONAL** |
| < 0.65 | **v7 GO**. Train v7 multi-teacher on Thunder |

## Risk mitigations

1. Thunder fails: Slot 1 fallback = `slot1_minimal_norm_setC_5flip.csv` (0.643 + 5 flips)
2. Truncation: re-run at 82K/64K (~10 min)
3. CSV format issues: minimal normalizer + pre-submission audit
4. Override hypothesis wrong: -0.005pp downside on Slot 3

## Pre-submission checklist (ALL slots)

- [ ] Row count == 943
- [ ] All ids 0..942 present, no duplicates
- [ ] Header is exactly `id,response`
- [ ] No `\left` / `\right` / `\,` in LAST `\boxed{}`
- [ ] No truncated responses

## Deliverables built tonight (5/26 eve)

In /tmp/override_test/ and /home/claude/:
- `splice_csvs.py` (generic K-source priority splice)
- `apply_overrides.py` (per-id last-boxed override)
- `slot1_minimal_norm_setC_5flip.csv` (RECOMMENDED Slot 3)
- `MCQ_OVERRIDE_CANDIDATES.md`
- `pace_report_session1.md`

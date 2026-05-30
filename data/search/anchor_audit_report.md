# Anchor Audit Report — Round-3 Wolfram + web_search

**Date:** 2026-05-30
**Audited commit:** efcd55c (round-3 landing)
**Output:** `data/search/teachers/anchor_set_FINAL.csv` (316 rows)
**Auditors:** claude_strategy (Pass A/B/C/D + Wolfram-Alpha tool) + ChatGPT (cross-audit)

## Summary

Both round-3 sheets are mechanically clean (schema, provenance, mapper logic all reproduce from raw source). But the union of the two sheets is **not** a clean anchor without three corrections, identified by cross-audit and confirmed via independent Wolfram|Alpha computation.

**Corrections applied to anchor_set_FINAL.csv:**

| id | action | detail |
|---|---|---|
| 0285 | quarantine + replace | Wolfram `147` is wrong (confirmed via Wolfram|Alpha: N mod 1000 = **735**). Anchor uses web_search `735`. |
| 0097 | promote to A+ | Wolfram `0, 4, 4` and web_search `x=0, y=4, r=4` are the same answer in different notations. Both correct. |
| 0252 | recover from residual | web_search FREE→`free_unrecognized_form` due to inline-option-MCQ-as-FREE schema mismatch. Stored answer `"C. independent samples..."` → letter `C` extracted into anchor. |

**Wolfram tool usage:** 3 queries (cap ~30):
- 0285: independent computation confirmed web_search value
- 0263: independent verification of weak-source Gauthmath value (passed)
- 0041: attempted lookup, not indexed; 2-source agreement (Wolfram + web_search IMO solution GOLD) stands

---

## Pass A — Structural sanity

| Check | Wolfram (276 rows) | Web_search (47 rows) |
|---|---|---|
| Schema valid | ✓ | ✓ |
| Unique ids | ✓ | ✓ |
| 4-digit zero-pad | ✓ | ✓ |
| CRLF preserved | ✓ | ✓ |
| promotion_class enum closed | ✓ | ✓ |
| MCQ letter format | 15/15 | 40/40 |

## Pass B — Provenance trace-back

- All 276 Wolfram rows trace to `WOLF_RESULTS.csv` status=DONE
- All 47 web_search rows trace to `search_results.csv` status=GOLD
- All 15 `mcq_letter_mapped_numeric` mappings re-verified under value-equality
- All 35 `mcq_exact_option_match` string-equalities re-verified

## Pass C — Cross-source agreement

- Unique anchor universe: **315 items** (within [250, 400] envelope)
- 268 Wolfram-only, 39 web_search-only, **8 overlap**
- Overlap: 6 genuine A+ agreement (0017, 0041, 0125, 0263, 0274, 0440), 1 cosmetic A+ (0097), **1 real conflict (0285)**

## Pass D — Targeted content review

Independent Wolfram|Alpha computations + hand verification on the highest-stakes items:

| Item | Source 1 | Source 2 | Independent verification | Verdict |
|---|---|---|---|---|
| 0285 | Wolfram: 147 | web_search: 735 (AIME_2025) | Wolfram\|Alpha N=885,735 → mod 1000 = 735 | **Wolfram value wrong** |
| 0097 | Wolfram: `0, 4, 4` | web_search: `x=0, y=4, r=4` | r=8sinθ → x²+(y−4)²=16, center (0,4) r=4 | **Same answer, both correct, promote to A+** |
| 0041 | Wolfram: 2112 | web_search: 2112 (imo_solution) | Wolfram\|Alpha didn't have it; 2 independent non-LLM sources agree against 3-way teacher disagreement (3542/3986/4048) | **2-source agreement stands** |
| 0263 | Wolfram: E | web_search: E (Gauthmath weak-src) | Wolfram\|Alpha: tan(arcsin(3/5)+arccos(5/13)) = −63/16 → letter E | **Weak source confirmed correct** |
| 0778 | (Wolfram-absent) | web_search: I (vaia weak-src) | Hand: 1−(0.9)(0.7)(0.5)=0.685=option I | **Weak source confirmed correct** |

8-row random sample of Wolfram clean_value rows (0582, 0099, 0015, 0684, 0216, 0189, 0176, 0108) all correct or plausible-correct on inspection.

## ChatGPT cross-audit findings (converged + additions)

ChatGPT independently caught the same 0285 issue and surfaced two further items:

**0252 (medium) — recall miss.** web_search GOLD `"C. independent samples..."` got bounced to `free_unrecognized_form` because the FREE Phase 1C path doesn't handle inline-option-MCQs (questions with `A./B./C.` options listed inline but no structured `options` field in `private.jsonl`). Recovered into anchor as letter `C`.

**0851 (low) — inline-option leak.** Wolfram sheet promotes 0851 as `free_single` with answer `"B, C"` — actually inline-option MCQ. Sweep extended this finding: **12 such inline-option leaks in the Wolfram sheet** (0056, 0101, 0119, 0158, 0185, 0227, 0315, 0343, 0385, 0492, 0676, 0851).

**Disposition for the 12:** no anchor change. Downstream Phase 2 (teacher_analysis.py) classifies by answer form, not category field — letter-set answers automatically route to MCQ_set subtype. Functionally self-correcting.

**FINDINGS.md staleness (process).** Updated: appended Finding 26 (round-2/3 build state) + Finding 27 (0285 quarantine).

## Generalizable risk

The round-2 fail-closed pipeline correctly extracts what Wolfram itself stored, but does not detect upstream wrong values when no cross-source exists. 0285 was caught only because web_search disagreed; 268 Wolfram-only rows have no equivalent independent check. The 3% spot-check sample (8 rows) found no additional bad entries, but that's a sample, not a guarantee.

## Anchor envelope (final)

| Tier | Source | Count |
|---|---|---|
| A+ | wolfram + web_search agree | 7 (6 confirmed + 0097 cosmetic) |
| A | wolfram only | 268 |
| A | web_search only | 41 (39 native + 0285 replacement + 0252 recovery) |
| **Total** | | **316** |

Consumed downstream by `teacher_analysis.py` (teacher v3 work-unit) as the measuring rod for all 4 teachers.

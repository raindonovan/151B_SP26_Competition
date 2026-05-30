# Wolfram Verification — Consolidated Results & Findings

**Final report.** Compiled 2026-05-29 after completing the full computable pass (batches B1–B29 + WEBSEARCH).
Authoritative data lives in `WOLF_RESULTS.csv` (scorecard) and `WOLF_RESULTS_READABLE.md` (readable log). Per-batch detail in `batches/batchNN/`.

---

## 1. Final coverage (943 items)

| Status | Count | % |
|--------|------|---|
| **DONE (verified)** | **477** | 51% |
| INCONCLUSIVE (Wolfram can't solve) | 92 | 10% |
| DISPUTED | 1 | — |
| UNVERIFIED (all flagged `MAYBE`-computable) | 373 | 40% |

**Verified-answer confidence:** 309 HIGH · 161 MED · 4 PARTIAL · 2 MEDIUM · 1 consensus-only

- **HIGH** = Wolfram independently produced the value; strongest gold.
- **MED** = value computed but messy/parametric, or multi-slot/MCQ where confirming every slot/letter is high-effort; consistent with sheet.
- **INCONCLUSIVE** = competition/olympiad or OEIS-algorithm items Wolfram cannot compute.

## 2. Outcome of verification (per item, the verified answer vs the sheet)

- **~58 discrepancies** — sheet's `best_answer` was wrong; verified answer differs. **All in flagged buckets** (P1 Qwen-vs-teacher disagreements + `undercount`-flagged), found in batches B9–B18.
- **~115+ matches** — verified answer confirms the sheet → locked-in gold.
- **92 inconclusive** — not Wolfram-solvable.

### Full discrepancy list (verified answer differs from sheet — 58 items)
| Batch | Items |
|-------|-------|
| B9 | 0000, 0020, 0024, 0025, 0029, 0135, 0171, 0188, 0196 |
| B10 | 0214, 0243, 0269, 0271, 0287, 0301, 0313, 0372, 0411, 0437 |
| B11 | 0438, 0444, 0461, 0503, 0505, 0539, 0557, 0608 |
| B12 | 0620, 0655, 0679, 0681, 0684, 0716 |
| B13 | 0790, 0794, 0834, 0836, 0872, 0936 |
| B15 | 0021, 0027, 0082, 0239, 0262, 0318, 0320, 0446, 0468, 0470 |
| B16 | 0553, 0666, 0718, 0753, 0885, 0914, 0923 |
| B18 | 0611, 0775 |

(Per-item verified values and the wrong sheet values are in each `batches/batchNN/FINDINGS.md` and in `WOLF_RESULTS.csv`.)

## 3. The core strategic finding

**`format_flags` reliably predict where wrong answers live:**

| Bucket | Discrepancy rate |
|--------|-----------------|
| P1 (Qwen-vs-teacher disagree) | high yield, but ~33% INCONCLUSIVE (competition-loaded) |
| `undercount`-flagged | **~30%** |
| `backsolve_disagree`-only | ~8% (weak) |
| Unflagged | **~0%** (pure verification) |

**Consequence:** the error-finding is *complete*. Every flagged-computable item was checked. The 254 unflagged solvable items (batches B19–B29) produced **~72 matches and 0 discrepancies** — they confirm the sheet was already right. The remaining 373 `MAYBE` items are word-problems/competition that Wolfram can't adjudicate.

## 4. Failure-mode taxonomy (what made answers wrong)

1. **Multi-slot undercount** (dominant) — N-slot answer collapsed to the last slot. Worst: 0470 (4 of 6 slots dropped), 0025 (12→6), 0438 (9→1).
2. **"Drop earlier sub-parts"** (F19) — multi-part a/b/c questions answered only for the final part: 0027, 0262, 0470, 0505 (Horner), 0444 (division).
3. **Digit-concatenation** (F14, systematic, post-processing-recoverable) — correct fraction/radical flattened to a digit string: 0313 (−2√14/15→"−21414"), 0411 (392π/45→"39246"), 0936 (275/16→"27517").
4. **T/F binary-vs-word** (F15) — 0/1 emitted where False/True expected: 0785, 0896, 0927.
5. **Placeholder / CoT leakage** (F16, F21, F24) — `best_answer` is literal "PLACEHOLDER_0611", "INVALID", "answer", a bare vocabulary word ("median", 0718), or pasted chain-of-thought (0498). Sheet-construction failures, not math errors.
6. **Trivial arithmetic** — e.g. 0557 (|5| = 6), 0135 (8x+2=3x+5 → "36" not 3/5).
7. **Rounding / convention** — 0029 (38.24%→"39"), and the open variance-convention question below.

## 5. Open actions (need a human / Kaggle)

- **F22 — population vs sample variance convention.** Item 0542: "variance"/"standard deviation" without "sample" qualifier — sheet used population (n), Wolfram defaults sample (n−1). Affects many stats items. **Resolve via one Kaggle probe** (submit a known item both ways) before mass-applying variance corrections.
- **F24 — sheet-hygiene sweep.** Grep `best_answer` across all 943 for "PLACEHOLDER", multi-sentence CoT text, or bare vocabulary words — all are unparsed/failed entries needing a value. 0611 and 0498 prove these exist.
- **373 MAYBE items** — these need web/source search (AoPS, textbook, WeBWorK), not Wolfram; or are genuinely uncomputable olympiad problems.

## 6. Dataset notes

- Recurrence template `a_n = 4a(n−1) − a(n−2)` appears 4× (0017, 0211, 0606, 0019); all answer **181** (least odd prime factor).
- OEIS algorithm MCQs ("given a(n) definition, compute y_list for x_list") are systematically INCONCLUSIVE — Wolfram can't compute arbitrary OEIS sequences at given indices.
- Some `computable=YES` items are really olympiad problems (keyword-classifier limitation): 0199, 0200, 0220, 0235, etc.

## 7. Wolfram query patterns that work (for future runs)

- `statistics {data}` for mean/std/median (NOT "mean, median, mode of {data}")
- `Mod[LinearRecurrence[{P,-Q},{a0,a1},N][[-1]], p]` for modular recurrences
- `InverseCDF[StudentTDistribution[df], p]` / `InverseCDF[NormalDistribution[0,1], p]` for critical values
- `CDF[NormalDistribution[0,1], z]` for p-values
- Type arithmetic/formulas directly; natural-language descriptions often fail
- For volumes of revolution: re-derive, don't pattern-match across items (caught a wrong shortcut at 0295: correct general form is πa³/15, not a²π/3)

---

## Batch index

| Batch | Bucket | Done | Notes |
|-------|--------|------|-------|
| B1–B8 + WEBSEARCH | legacy | 66 | original wolfram_overrides |
| B9–B13 | P1 (Qwen-vs-teacher) | ~90 | 39 discrepancies; competition tail |
| B14 | P2 (teacher-split) | 25 | 0 discrepancies (verification) |
| B15–B16 | P3 undercount-flagged | 50 | 17 discrepancies |
| B17 | P3 unflagged | 25 | 0 discrepancies |
| B18 | backsolve_disagree single-slot | 25 | 2 discrepancies (weak flag) |
| B19–B29 | solvable leftovers (254 pass) | ~150 | ~72 matches, 0 discrepancies |

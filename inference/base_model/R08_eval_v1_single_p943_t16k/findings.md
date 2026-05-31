# R08_eval_v1_single_p943_t16k — findings (deep audit)

**Run:** `run08v2_v1_private943_tok16384` · first full p943 eval · single-sample · 16K tokens · v1-baseline · 2026-05-04
**Analyzer:** v3-final-final (761f903), single-sample auto-detect path (`is_sc=False`) — first deep audit to exercise it.
**Kaggle:** submitted as `submission/csvs/run08v2_v1_private943.csv` = REGISTRY #1, **0.586** (first submission). Analyzer NOT re-run with `--kaggle-score` because the CSV is a post-processed derivative, not the raw run; 0.586 is the post-processed score, recorded here for reference.

## a. Headline
- **Bucket:** A=407 · A_lucky_sample=0 · B=91 · unknown=445
- **Scored set** (bucket≠unknown): n=498, math_correct=407, **acc=0.8173**
- (Audit score is NOT a Kaggle mirror — see CATALOG C6 reframe. The 0.82 here is on the easy independent-gold subset; Kaggle post-processed was 0.586.)

## b. hard_independent_CLEAN (the gate set — wolfram_HIGH + search_GOLD @ T1/T2/T3)
- **n=16, correct=10, acc=0.6250** — PASSES gate [0.60, 0.95] (at the low edge).
- Per-source: wolfram_HIGH 3/7 · search_GOLD 7/9.
- (c-info) hard_independent_DIRTY (wolfram/search @ T4/T5): n=78, acc=0.2051 — the structural-normalizer gap, same as R20; not a Qwen-ability signal.

## c. unanimous_teachers (report-only)
- **n=403, correct=381, acc=0.9454.** Below R20's 0.988 — expected: R08 is single-sample at half the token budget, so it agrees with teacher consensus less often. Still ≥0.90, so the run is healthy (no analyzer/data alarm).

## d. A_lucky_sample — EMPTY (confirmed)
- **A_lucky_sample = 0**, as required for a single-sample run (no vote to lose).
- Explicitly verified: `n_samples_math_correct ∈ {0, 1}` for ALL 943 rows (domain check passed). The analyzer's single-sample path sets n_samples_math_correct = 1 iff math_correct else 0.

## e. B items (n=91) — format-recoverability
Visual classification of all 91 B response bodies:

| Category | Count | Recoverable? |
|---|---|---|
| likely true math miss | 28 | no |
| multi-slot (per-box mismatch) | 19 | yes (structural) |
| fraction-form (e.g. `\frac{L-8x}{6F}` vs `L-8x, 6F`) | 16 | yes (structural/gold-split) |
| MCQ-letter vs value (boxed `I`/`F` vs `232`/`28`) | 14 | yes (extraction) |
| multi-slot undercount (last-box only) | 14 | yes (structural) |

**~63/91 (69%) are format-recoverable**, matching the R20 ~72% observation. **22 of the 91 B items are ALSO truncated** (math cut off mid-derivation, not a format issue — fixable by tokens, see §f).

Top B examples (clean-gold tiers first): id=12 `2c+4p=70, 11` boxes both parts but order/extraction mismatches; id=26 body computes `232` (correct) but final box is option letter `I`; id=9 `\frac{L-8x}{6F}` vs mis-split gold `L-8x, 6F` (Qwen arguably more correct); id=41 `2112` — genuine miss (response rambles, never converges). Full per-item list in `analysis/analysis.csv` (filter `bucket_b_review_needed=True`).

## f. Truncated items (hit_token_cap=True) — n=119
- **119 truncated vs R20's 17** — exactly the half-token-budget (16K vs 32K) prediction. By tier: T5=70, T4=21, T3=12, T2=8, T0=8.
- **118 of 119 are math-wrong** — truncation is a dominant failure mode at 16K. 22 of these are in Bucket B (the rest fall in `unknown`/T4-T5).
- These are **high-budget re-run targets** (81920/65536 per memory #20), NOT format fixes.
- Full id list (119): 7,16,17,19,21,41,54,58,66,83,93,95,102,112,117,120,124,125,141,161,164,170,173,194,198,199,204,211,222,229,248,250,266,275,285,308,312,316,341,347,373,376,377,383,386,391,409,419,422,443,445,450,453,457,458,471,475,488,498,501,503,508,510,517,518,519,523,525,552,562,571,583,586,589,597,606,614,620,629,636,644,646,649,652,653,668,673,682,688,700,703,722,724,727,744,749,751,786,788,797,799,801,809,810,814,823,836,840,856,868,874,894,907,911,919,920,925,930,935

## g. Cross-run implications
- **First p943 deep audit — nothing to compare yet.** Cross-run flips (watchlist §3), all-p943-wrong items (§4), and consensus-fragility analysis populate after R09 (next deep run) and complete at R20b.
- R08's role in CROSS_RUN_MATRIX: the **naïve single-sample 16K floor**. Where later SC / longer-token / prompt-variant runs beat R08 tells us what those levers bought; where R08 is uniquely right flags consensus-fragility candidates. Both deferred until ≥2 p943 runs are cataloged.

## Notes / surprises
- **Analyzer single-sample path is clean** — the key risk this audit was meant to exercise (R20 was SC-only). All gates a/c/d/f/g + verification triple pass. No single-sample bug; downstream p943 deep audits are unblocked.
- **extracted_empty=1** (one item with no extractable answer at all) — vs 0 on R20. Single-sample + truncation occasionally yields a response with no box and no fallback-able number.
- Truncation (119) dwarfs every other failure mode at 16K — the single biggest "free" lever for this run would be tokens, not prompt or SC.

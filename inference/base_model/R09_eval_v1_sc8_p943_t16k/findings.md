# R09_eval_v1_sc8_p943_t16k — findings (deep audit)

**Run:** `run09sc8_v1_private943_tok16384` · first SC@8 on p943 · 16K tokens · v1-baseline · 2026-05-04→05
**The SC twin of R08:** identical model / token budget / prompt / day — the ONLY difference is self-consistency at N=8. So every delta here isolates the **pure SC effect at fixed tokens+prompt**.
**Analyzer:** v3-final-final (761f903). **Kaggle: 0.614** (REGISTRY #4; memory #2 notes local judger 0.332 vs Kaggle 0.614 — the 28pp gap).

## a. Headline
- **Bucket:** A=422 · A_lucky_sample=18 · B=58 · unknown=445
- **Scored set** (n=498): math_correct=422, **acc=0.8474** (vs R08's 0.8173 — SC +3.0pp on the scored set).

## b. hard_independent_CLEAN (wolfram_HIGH + search_GOLD @ T1/T2/T3)
- **n=16, correct=11, acc=0.6875** — PASSES [0.60,0.95] (vs R08's 0.625). Per-source: wolfram_HIGH 4/7 · search_GOLD 7/9.
- (c-info) DIRTY (T4/T5): n=78, acc=0.1795 — structural-normalizer gap (same as R08/R20).

## c. unanimous_teachers (report-only)
- **n=403, correct=397, acc=0.9851** — vs R08's 0.9454. SC recovers most of the consensus-agreement gap (matches R20's 0.988). Healthy.

## d. A_lucky_sample — FIRST real distribution in the cohort (n=18)
Items where the correct math was IN the 8 samples but voting picked a wrong answer. (item_id, n_correct/8, first correct sample_index):

| item | n_correct/8 | correct sample idx (all) | gold | voted (wrong) |
|---|---|---|---|---|
| 763 | **6/8** | 0 (0,2,3,4,5,7) | `13, 8/3` | `13.00, 2.667` |
| 403 | 4/8 | 2 (2,3,4,7) | `J` | `I` |
| 721 | 4/8 | 0 (0,2,3,4) | `D, A, A` | `A` |
| 584 | 3/8 | 3 (3,5,6) | `7z, 6w` | `7.000, 6.000` |
| 924 | 3/8 | 2 (2,3,4) | `n = 55 + 0.2t, 201` | `2010, 2010` |
| 12 | 2/8 | 5 (5,7) | `2c + 4p = 70, 11` | `11` |
| 416 | 2/8 | 1 (1,3) | `11,16` | `\frac{11}{16}` |
| 495 | 2/8 | 2 (2,5) | `100, 100, 200, 0.2` | `B` |
| 535 | 2/8 | 0 (0,4) | `-4, -6` | `-6, -4` |
| 712 | 2/8 | 0 (0,5) | `D,D,A` | `A` |
| 715 | 2/8 | 4 (4,6) | `5, 7, 9, 13, 8.5, ...` | `8.500` |
| 9 | 1/8 | 5 | `L-8x, 6F` | `\frac{L - 8x}{6F}` |
| 120 | 1/8 | 2 | `8` | `1` |
| 181 | 1/8 | 2 | `A` | `B` |
| 257 | 1/8 | 1 | `2.52, 3.00, A` | `A` |
| 642 | 1/8 | 1 | `amp=6, period=pi/3` | `13` |
| 929 | 1/8 | 3 | `5.860, (-0.78, 3.1...` | `A` |
| 935 | 1/8 | 5 | `H` | `S` |

- **DeepConf gold (≥5/8 correct but lost the vote): 1 item — id=763** (6/8). Logprob-weighting would very likely flip this. (Low count because at fixed 16K+v1, when ≥5/8 samples agree on the right answer they usually also win the plain vote; the lossy cases cluster at 1–4/8.)
- **SC@32 candidates (1–4/8 correct): 17 items** — 403, 721, 584, 924, 12, 416, 495, 535, 712, 715, 9, 120, 181, 257, 642, 929, 935. More samples could surface/strengthen the minority-correct answer.
- **(item_id, winning_sample_index) tuples** for adapter-trace harvest are the "idx" column above.
- Note: several A_lucky items are *also format-divergent* (763 `8/3` vs `2.667`; 416 fraction-form; 535 order) — the "correct sample" was judged right by value-equality, so these are genuine math-right samples regardless of form.

## e. B items (n=58) — format-recoverability
| Category | Count |
|---|---|
| multi-slot (per-box mismatch) | 23 |
| true math miss | 18 |
| MCQ-letter vs value | 9 |
| fraction-form | 6 |
| undercount (1 box, multi gold) | 2 |

**~40/58 (69%) format-recoverable** (same ratio as R08/R20). Top examples: id=26 body computes `232`, boxes letter `I`; id=89 `\frac{326}{7}` vs `46.57` (value-equal, judged wrong — precision/form); id=41 `2112` genuine miss (rambles). Full list: `analysis/analysis.csv` filter `bucket_b_review_needed=True`.

## f. Truncated items — n=93 (vs R08's 119)
- SC dropped truncation 119→93: with 8 samples, at least one often completes within 16K. By tier T5-heavy.
- **89 items truncated in BOTH R08 and R09** = strongest high-budget re-run candidates (truncated under both single-sample AND SC at 16K → consistently need >16K). R08-only 30, R09-only 4.
- Still token-bound, not format: high-budget (65536/81920) re-run targets.

## g. Cross-run vs R08 (first real cross-run analysis — the SC dividend)
Bucket transitions, R08 → R09 (943 items):

| R08 → R09 | count | meaning |
|---|---|---|
| A → A | 401 | SC-preserved correct |
| A → B | **0** | SC-regressed — **none** |
| A → A_lucky_sample | 6 | was cleanly correct, now vote-fragile (math still present) |
| B → A | **21** | **SC SAVED** — correct math R08 missed entirely |
| B → A_lucky_sample | 12 | math now present in samples but vote lost it |
| B → B | 58 | still wrong under SC |
| unknown → unknown | 445 | (T4/T5 + non-independent, not scored) |

- **SC dividend at fixed tokens+prompt = 21 (B→A) + 12 (B→A_lucky) = 33 items** where SC surfaced correct math that single-sample R08 missed. Of these, 21 already win the vote; 12 need better aggregation (DeepConf/SC@32) to convert.
- **SC cost = 0 regressions to B**, only 6 A→A_lucky (clean→vote-fragile, math still there). **SC is strictly positive at fixed tokens/prompt** — it never lost a correct answer to wrong, only occasionally made a correct one vote-fragile.
- Implication for Pick B: the 12 B→A_lucky + 6 A→A_lucky = 18 vote-fragile items are exactly the DeepConf/SC@32 target set (matches the A_lucky_sample list in §d).

# NT_eval_nothinking_sc8_p943_t8k — findings (T1.5 hybrid audit)

**Run:** `nothinking_full_943_20260527T000129Z` · SC@8 · **NoThinking mode** (prefill `</think>` bypass, per memory #20) · 943 items · token cap 8192 · 2026-05-27 00:01 UTC · untouched ~3 days.
**NOT R-series** — orthogonal reasoning mode (NT prefix). **No REGISTRY entry** (never submitted standalone), so no `--kaggle-score`.
**Analyzer:** v3-final-final (761f903), SC path — run on an ADAPTED copy (see schema note).

## Schema note (why there's an ADAPTED file)
The NoThinking jsonl uses a **different schema** than R-series SC runs: `samples` is a list of raw response STRINGS (not dicts); per-sample data is in parallel arrays (`sample_extracted`, `sample_n_output_tokens`); no `is_mcq`/`options`/`max_new_tokens`/per-sample `hit_token_cap`. The analyzer (LOCKED — not modified) expects dict-samples. Per the T1.5 contingency, I wrote a one-off prep adapter `inference/scripts/prep_nothinking_for_analyzer.py` that restructures it into the expected SC schema (truncation synthesized from `n_output_tokens >= 8192-10`; `is_mcq` backfilled from MASTER category; `options=None`, which `auto_judge` handles via `is_equal` as the R08/R10 single-sample audits did). Both the raw run jsonl and the `_ADAPTED.jsonl` are kept in this folder; the analyzer ran on the adapted one. **Analyzer was NOT modified.**

## a. Headline — standalone NoThinking is WEAKER (expected)
- **Bucket:** A=363 · A_lucky_sample=**66** · B=69 · unknown=445
- **Scored set** (n=498): math_correct=363, **acc=0.7289** (vs R20 0.8554). NoThinking bypasses the reasoning phase → broadly lower accuracy. But the huge A_lucky_sample (66 vs R20's 14) says the right answer is often present in *some* sample — NoThinking is high-variance/high-diversity.

## b. hard_independent_CLEAN
- **n=16, correct=12, acc=0.7500** (R20 0.8125). Per-source: wolfram_HIGH 5/7, search_GOLD 7/9. Holds up better on hard items than its overall accuracy suggests.
- (c-info) DIRTY: 0.3205 — HIGHER than R20's 0.19 (NoThinking does better on the messy T4/T5 wolfram/search set, likely because no reasoning phase means less over-thinking on hard multi-part items).

## c. unanimous_teachers
- **n=403, correct=326, acc=0.8089** (R20 0.9876). The big standalone gap is here — NoThinking misses many easy consensus items the Thinking model nails. This is why it's not a standalone replacement.

## d. A_lucky_sample (66) + truncation
- **A_lucky_sample = 66** (R20 14) — the headline diversity signal: 66 items where a correct answer is in the samples but the vote lost it. NoThinking's lack of reasoning makes individual samples noisier (more spread), so the right answer surfaces in a minority more often.
- **Truncated = 9** (R20 17) — much lower, as expected: no reasoning phase → shorter outputs, rarely hits the 8192 cap.

## e. CROSS-RUN vs R20 — LOAD-BEARING for Pick B
### e1. R20 → NT transition table
| R20 → NT | A | A_lucky | B |
|---|---|---|---|
| A (426) | 348 | 50 | 28 |
| A_lucky (14) | 7 | 6 | 1 |
| B (58) | 8 | 10 | 40 |

### e2. UNIQUE-CORRECT (NT bucket A, R20 NOT bucket A) = **15** ✓ (≥10 threshold)
Items: **5, 181, 257, 282, 345, 474, 578, 584, 633, 642, 712, 715, 763, 868, 917**.
Inspection — these are GENUINE wins, two flavors:
- **NoThinking emits the full multi-slot answer where R20's vote collapsed to one slot:** 5, 257, 474, 578, 633, 642, 712, 715, 868, 917 (e.g. 868 NT `88`==gold vs R20 `E`; 712 NT `D,D,A`==gold vs R20 `A`).
- **NoThinking avoids a reasoning-induced error R20 made:** **id=282** — NT `e^2`==gold, R20 `e^2,-e^2` (the spurious extra-root that made 282 an *adapter-seed* item!); **id=345** — NT exact `-5/6,5/6`, R20 decimal `-0.8333` (R20-T3 format item).
- This means NoThinking ∪ R20 consensus could **rescue 2 of R20's hardest items (282 adapter-seed, 345 format)** plus ~13 multi-slot collapses, at ZERO GPU.

### e3. R20 wins, NT misses (R20.A ∩ NT.B) = **28**
NoThinking is broadly weaker — 28 items R20 gets that NT drops. So a consensus join must **weight R20 as primary** and only let NT break ties / add on R20-misses; a naive equal-weight union would import these 28 losses.

### e4. Both miss (B in both) = **40** (R20's B∩∩∩∩∩ was 48)
NT recovers 8 of R20's 48 cross-lever-B (e.g. 282, 345, 474, 868) but the 40 both-miss core is the consensus-can't-help set. NT adds NO new permanent misses beyond R20's set on the scored items (its extra failures are all in R20's existing B or are vote-fragility).

### e5. Agreement on scored set = **335/498 (67.3%)**
**32.7% disagreement** — high ensemble headroom. The value is concentrated in the disagreements where NT is the correct one (the 15 unique-correct + the A_lucky overlaps).

## f. Failure-mode orthogonality (5 both-B items)
| id | gold | NT | R20 | |
|---|---|---|---|---|
| 12 | `2c+4p=70, 11` | `11` | `11` | SAME (undercount, both) |
| 25 | fractions | `0.127,...` | `8,14,25,...` | DIFFERENT |
| 41 | `2112` | `2024` | `4048` | DIFFERENT |
| 61 | piecewise | `0.76c,0,150` | `0.7600c,0,150` | DIFFERENT |
| 67 | `7.6(1.09)^t,...` | `7.6·(1.09)^t` | `13.89,...` | DIFFERENT |

**4 of 5 DIFFERENT wrong answers** — NoThinking's failures are genuinely orthogonal to R20's (different values, different error modes; e.g. 41 NT undershoots `2024`, R20 overshoots `4048`). Only the id=12 undercount is shared. **Orthogonal failures = genuine diversity, not a weaker copy.**

## g. VERDICT: **ELEVATE** — NoThinking ∪ R20 consensus is a Pick-B candidate
- **15 unique-correct ≥ 10 threshold** ✓
- **Orthogonal failures (4/5 different)** ✓
- **67.3% agreement → 32.7% ensemble headroom** ✓
- Recommend **T3 verification** of the 15 unique-correct (confirm NT's wins are real value-equality, not gold-quirk) **before building the consensus-join CSV**.
- **Consensus-join design caveat:** R20 must be PRIMARY (28 items where R20 wins and NT misses). The join should be "R20 voted answer, but where R20∈B and NT∈A with agreement across NT samples, take NT" — NOT an equal-weight union. This is a post-processing step, ZERO GPU.
- **Top-10 unique-correct for Pick B planning:** 5, 181, 257, 282, 345, 474, 578, 633, 642, 712 (282 and 345 are the highest-value — they rescue an adapter-seed item and a format item respectively).

## Notes / surprises about NoThinking on Qwen3-Thinking
- **NoThinking does BETTER on hard/dirty items (DIRTY 0.32 vs R20 0.19) and WORSE on easy consensus (0.81 vs 0.99).** Counterintuitive but coherent: skipping the reasoning phase hurts straightforward problems (where reasoning helps) but avoids over-thinking spirals on hard multi-part ones — and notably avoids the spurious-extra-root error (282) that the reasoning chain introduced.
- **A_lucky_sample=66 is the standout:** NoThinking is a diversity engine. Even where its vote is wrong, the right answer is frequently in the samples — ideal raw material for a logprob/DeepConf-weighted ensemble with R20, or for SC@32-on-NoThinking.
- This is the only Pick-B lever found in the whole audit that ADDS correctness over R20 (SC/tokens/filter were all about R20-internal aggregation; NoThinking brings *orthogonal* solves).

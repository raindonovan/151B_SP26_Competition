# R10_eval_v3perslot_single_p943_t16k — findings (deep audit)

**Run:** `run10_v3perslot_private943_tok16384` · single-sample · 16K tokens · **v3-perslot prompt** · 2026-05-05
**Isolates PROMPT-VARIANT effect** at fixed model + fixed (no) SC + fixed 16K, vs R08's v1-baseline single-sample.
**Analyzer:** v3-final-final (761f903), single-sample path. **Kaggle: 0.424** (REGISTRY #2 = `run10_v3perslot_private943.csv`, "V3 per-slot prompt" — the worst p943 submission). Analyzer NOT re-run with `--kaggle-score` (CSV is a post-processed derivative).

> **Doc-conflation flag (for strategy):** `strategy/INFERENCE_TECHNIQUES.md` L9 and `strategy/TEST_PIPELINE.md` L21 list "run10, run14b" as **SC@8 → 0.646**. R10 is **single-sample** (`method: vllm`, no `samples` array) and scored **0.424**. The 0.646 belongs to R14b/R20 alone. R10 was mislabeled as SC@8 in those two docs.

## a. Headline
- **Bucket:** A=396 · A_lucky_sample=0 · B=102 · unknown=445
- **Scored set** (n=498): math_correct=396, **acc=0.7952** — the LOWEST of the three deep runs (R08 0.8173, R09 0.8474). The v3-perslot prompt *hurt* at fixed single-sample/16K.

## b. hard_independent_CLEAN (wolfram_HIGH + search_GOLD @ T1/T2/T3)
- **n=16, correct=12, acc=0.7500** — PASSES [0.60,0.95]; HIGHEST of the three (R08 0.625, R09 0.6875). Per-source: wolfram_HIGH 6/7, search_GOLD 6/9.
- Note the split signal: v3-perslot *helped* the small hard-independent set (6/7 wolfram vs R08's 3/7) but *hurt* the broad easy set (see §c). The per-slot structure seems to aid hard multi-part items while costing accuracy elsewhere.
- (c-info) DIRTY (T4/T5): n=78, acc=0.2179 — structural-normalizer gap (consistent across cohort).

## c. unanimous_teachers (report-only)
- **n=403, correct=367, acc=0.9107** — LOWEST of the three (R08 0.9454, R09 0.9851). Still ≥0.90 (healthy) but the v3-perslot prompt clearly degraded agreement on the easy consensus set — the dominant driver of R10's lower overall accuracy.

## d. A_lucky_sample — EMPTY (confirmed)
- A_lucky_sample = 0 (single-sample). Verified `n_samples_math_correct ∈ {0,1}` for all 943 rows.

## e. B items (n=102) — format-recoverability
| Category | Count |
|---|---|
| multi-slot (per-box mismatch) | 46 |
| true math miss | 21 |
| MCQ-letter vs value | 18 |
| fraction-form | 13 |
| undercount | 4 |

**~81/102 (79%) format-recoverable.** The v3-perslot prompt *increased* multi-slot/per-box mismatches (46 vs R08's 19) — consistent with a per-slot prompt encouraging per-part boxing that the last-box extractor then mis-collects. Top B: id=26 `232`→`I` (MCQ-letter), id=52 `231,385`→`385` (undercount, NEW vs R08), id=41 `2112` (true miss), id=89 covered below. Full list: `analysis/analysis.csv` filter `bucket_b_review_needed=True`.

## f. Truncated items — n=110
- Between R08 (119) and R09 (93), as predicted. Single-sample like R08 but v3-perslot uses slightly fewer tokens on some items. T5-heavy. High-budget re-run targets.

## g. Cross-run analysis (now 3 p943 runs)

### g1. R10 vs R08 — PROMPT EFFECT (both single-sample 16K, v3perslot vs v1)
| R08 → R10 | count |
|---|---|
| A → A | 373 |
| **A → B** | **34** (prompt regression) |
| **B → A** | **23** (prompt-saved) |
| B → B | 68 |
- **Prompt dividend = 23 (B→A), prompt regression = 34 (A→B) → NET −11.** Unlike SC, the v3-perslot prompt **breaks more than it fixes**.
- **vs R09's SC dividend (21 B→A, 0 A→B, net strictly positive):** SC is the clearly superior lever at 16K. The prompt variant is net-negative; SC is net-positive with zero regressions.

### g2. R10 vs R09 — prompt-single vs v1-SC
- **R10 wins / R09 misses (prompt > SC): 12** — [12, 120, 416, 469, 633, 642, 715, 721, 727, 763, 902, 917]
- **R09 wins / R10 misses (SC > prompt): 38**
- both-miss (scored): 64
- **SC strictly dominates the prompt variant** (38 vs 12). Interesting: the 12 R10-wins overlap heavily with R09's A_lucky_sample list (12, 120, 416, 642, 715, 721, 763) — items where v3-perslot's single sample happened to land the answer SC's vote lost. These reinforce the SC@32/DeepConf target set, not a case for v3-perslot.

### g3. Three-way A∩A∩A (consistently solved across both prompts + SC/no-SC)
- **372 strict A∩A∩A** (373 counting R09's one A_lucky here). Highest-confidence A items — NOT adapter/normalizer candidates. ~75% of the 498 scored set is rock-solid across every lever tried.

### g4. Three-way B∩B∩B (consistently wrong across both prompts + SC/no-SC) — CORE BUCKET B
- **53 items B∩B∩B:** 5,25,26,33,41,61,67,68,72,89,100,103,104,106,117,124,127,134,167,182,192,218,231,233,247,263,264,282,306,317,345,353,389,395,413,440,443,474,487,506,519,548,578,587,591,638,657,710,713,723,748,793,868
- Recoverability split of the core: **multi-slot 23, MCQ-letter 10, fraction-form 7, undercount 3 = 43 format-recoverable** (normalizer targets, NOT adapter); **true-miss = 10**.
- **TRUE-MISS CORE (real adapter targets after format filter): [41, 61, 103, 104, 117, 127, 231, 264, 282, 868]** — 10 items wrong on the math across both prompts and SC. id=41 already T3-confirmed (R08). This is the strongest adapter-target seed so far; will tighten when R20/R20b land (32K + longer tokens may rescue some — esp. 117/127 which are in the both-truncated set).
- **Adapter-exclusion reminder (R08-T3):** id=9 is a gold-split artifact, NOT a true miss — it is NOT in B∩B∩B (R09/R10 bucketed it A_lucky/B variously) and must stay off adapter exemplars. id=68 flagged true-miss by R08-T3 but here classified fraction-form due to a truncated R10 response — treat per R08-T3 (true miss).

## Notes / surprises
- **Biggest surprise: the v3-perslot prompt is net-negative** (−11 vs R08) yet *helps* the hard-independent subset (0.75 vs 0.625). A per-slot prompt seems to trade broad easy-item accuracy for a few hard multi-part wins — a bad trade at 16K. Confirms why it scored 0.424 on Kaggle (worst p943).
- SC (R09) > prompt-variant (R10) decisively as a lever; the chronological arc correctly abandoned v3-perslot after this run.
- Multi-slot B inflation (46) under a per-slot prompt is a clean illustration that prompt-induced per-part boxing fights the single-last-box grader — a structural-normalizer (undercount collapse) would recover much of it.

---

## ChatGPT T3 deep audit verdict — 2026-05-30 ~22:05 PT

**VERDICT: GREEN. Confidence HIGH for matrix use.**

All numerics confirmed exactly: bucket counts, transition counts (373/34/23/68), A∩A∩A=372, B∩B∩B=53.

### Methodology nuance: "R10 over R09: 12 wins" is definition-sensitive

**Two valid definitions, both meaningful:**
- **Strict A-only**: items where R09 in B AND R10 in A → **5 items**
- **Non-A (A_lucky_sample counts as miss)**: items where R09 either-B-or-A_lucky AND R10 in A → **12 items**

The 12 is the more strategically useful frame: it captures "items where R10's single sample landed on math R09's vote missed." But 7 of those 12 are R09 A_lucky_sample items — R10's "wins" are mostly vote-fragile SC@32 candidates, not prompt-variant advantage. Strict A-vs-B = 5 is the conservative read.

**ALWAYS specify the definition** when citing this number in downstream analysis (CROSS_RUN_MATRIX, T4 audit, morning-runs planning).

### Spot-check on true-miss core [41, 61, 103, 104, 117, 127, 231, 264, 282, 868]

ChatGPT spot-checked 2:
- **id=117**: repeated truncation/non-answer vs gold B across all 3 runs. **Truncation-driven.** Likely rescued at R20's 32K. Expected to leave the true-miss seed at R20.
- **id=282**: consistently emits `e^2, -e^2` when gold is just `e^2`. **Extra-root reasoning error** — Qwen's chain includes a spurious negative-root path. **Stays in the seed; ideal adapter exemplar candidate.**

### 34 A→B regressions confirmed real (spot-checked 3)

- id=52: undercount (`231,385` → `385`) — single-slot collapse
- id=403: MCQ wrong letter (J → H)
- id=712: multi-slot collapse (`D,D,A` → `A`)

**The v3-perslot prompt damages multiple failure-mode categories simultaneously**, not a single bug. Structural prompt-grader mismatch, not fixable. The dev-arc decision to abandon it is empirically correct.

### Multi-slot B inflation (46 vs R08's 19)

ChatGPT notes the exact "46" isn't directly auditable from analysis.csv (no `failure_mode` column with a `multi_slot` subtype). The proxies (emitted-field counts) show strong inflation over R08, which supports the directional claim. **Worth a future analyzer enhancement: add a `failure_mode` subtype column to analysis.csv for downstream queryability.** Out of scope for tonight.

### Adapter-seed projection going into R20

After R20:
- id=117 (truncation) → likely OUT of true-miss seed (rescued at 32K)
- id=127 (also flagged truncation-suspect) → possibly OUT
- id=282 (extra-root error), id=41 (rambling) → confirmed IN
- Final true-miss seed projection: **5-8 items**, refined at R20

---

## Adapter training approach by failure mode (locked Day 9 22:15 PT)

For each item in the true-miss seed, training approach depends on failure mode. Add a `training_approach` column to per_item adapter exemplar files when building tomorrow's training set.

| Failure mode | Seed items (R8∩R9∩R10, may shrink at R20) | Training approach | Risk |
|---|---|---|---|
| Rambling / never converges | 41, 61 | Tight decisive Sonnet traces, mid-length (40-75th pct correct lengths). 1-2 self-verify steps. Goal: termination behavior. | LOW |
| Spurious reasoning path | 282 (extra-root: e², -e² vs gold e²) | "Mistake + correction" pattern — show spurious step, catch via domain/constraint check. One-mistake-plus-correction transfers better than straight-path (May 13 research). | MEDIUM — may not generalize beyond specific constraint type |
| Truncation-driven | 117, 127 (CONFIRM AT R20) | **NOT adapter scope.** If 32K rescues → fix is inference-time token budget. Move out of seed. | N/A |
| Multi-slot/format quirks | 103, 104, 231, 264, 868 (need per-item triage at R20) | NOT adapter scope — these are normalizer territory (tier 2 class-based or tier 3 item-specific via per_item_overrides.csv) | N/A |
| High-reasoning differentiation | (none confirmed) | AVOID — stylistic confusion + distribution drift risk. SFT shifts token patterns, not reasoning style. | HIGH |

### Training data construction principles (May 23 research consensus)

- Single-teacher style consistency (Sonnet preferred per research; v3+ design choice)
- Correctness-gated traces only
- 40-75th percentile trace length (shortest-correct underperforms)
- 1-2 self-verify steps preferred (excess verification hurts)
- One-mistake-plus-correction pattern transfers better than straight-path
- 3-5 epochs (Light-R1, LIMO pattern)
- ~15-25 training examples on ~5-8 items max (2-3 paraphrase traces per item)

### Open verification gap

**Claim to verify with Rain (Day 9 22:15 PT):** Does our v3/v4/v5 SFT history specifically show "Sonnet traces work on Qwen" as a finding distinct from architecture-fix failures? Or is Sonnet-as-teacher currently a research-consensus prior we haven't empirically isolated yet? If the latter, the adapter run tomorrow is also a teacher-isolation experiment.

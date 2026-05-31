# strategy/MORNING_RUNS_WATCHLIST.md — Signals from chronological audit → Sunday morning inference

> **Built Day 9, 2026-05-30 ~20:00 PT.** Pre-staged for the 02:00 → 05:00 Sun checkpoint where claude_strategy decides what (if any) GPU runs fire in the 05:00 → 09:30 Sun adapter / inference window. Survives session boundaries — read this at wake-up.

## Decision time: ~05:00 Sun May 31 PT

At wake-up post-sleep, claude_strategy reads:
- `inference/runs/CROSS_RUN_MATRIX.csv` (built by end of deep audits ~02:00 Sun)
- Per-run `findings.md` for R08, R09, R10, R20, R20b
- This watchlist

…then picks 0–3 morning inference runs to fire on Thunder A100s in parallel with adapter training (3+ GPUs available, no GPU budget).

## Watchlist — signals to capture in per-run findings.md (deep audits ONLY)

For each p943 run (R08, R09, R10, R20, R20b), the deep findings.md MUST surface:

### 1. A_lucky_sample items with n_samples_math_correct distribution
(Items where Qwen knew but voting lost it — Rain's "highest lever" candidate set)
- Sort by `n_samples_math_correct`, high → low
- Items at **5/8, 6/8, 7/8 correct that lost the vote** = DeepConf gold (logprob weighting would likely flip these)
- Items at **1/8, 2/8 correct** = SC@32 candidates (more samples might surface the right answer)
- **Capture the (item_id, winning_sample_index) tuples** — these are also the adapter-trace-harvest input per Rain's idea

### 2. Truncated items
(`hit_token_cap=True`; math may have been cut off mid-derivation)
- Item IDs + token-cap value
- Higher-token-budget re-run targets (81920 / 65536 per memory #20 for hardest items)

### 3. Cross-run flips (populated incrementally)
After ≥2 p943 runs cataloged:
- Items where this run differs from another p943 run on `math_correct`
- Inter-run instability marks → candidates for tiebreaker inference (NoThinking, alt-prompt)

### 4. All-p943-wrong items (populated by R20b finish)
- Items wrong across all of R08, R09, R10, R20, R20b
- True Bucket B = adapter training targets
- ALSO candidates for NoThinking-mode 943 re-run (orthogonal sampling regime)

### 5. Format-recoverable B items
(B items where math is right in the response body but boxed extraction failed)
- Note failure mode: multi-slot undercount / precision / MCQ-first-box / etc.
- These feed the structural-normalizer probe list — **NOT new inference runs**
- Sized roughly at vscode's R20 observation: ~72% of hard-wrong items
- **NEW (Day 9 ~00:30 Sun, ChatGPT pre-submission audit finding):** R20's raw CSV contains **19 rows with NO `\boxed{}` wrapper at all** — these fail Kaggle grader extraction unconditionally. Tier-1 universal normalizer rule to add: "if response has no `\boxed{}`, detect most-likely answer in response body and wrap it." Conservatively ~6 rescues on slice (19 × 30%). Free lever, higher EV than DeepConf at this point. Build BEFORE other normalizer tiers since it touches the most fundamental extraction failure.

## Morning-run candidates (specs gated on watchlist evidence)

All candidates Qwen-only → Pick-B eligible under rule #11.

| Run | Threshold signal | GPU cost | Code cost |
|---|---|---|---|
| **DeepConf SC@16 + `logprobs=20`** on contested slice | ≥20 A_lucky_sample items with n_samples_math_correct ≥ 5/8 | ~60 min A100 | ~30 min vLLM source mod (R1 from strategy/INFERENCE_TECHNIQUES.md) |
| **Plain SC@32** on contested slice | ≥30 A_lucky_sample items with n_samples_math_correct 1–4/8 | ~45 min A100 | none (use existing run_vllm_sc.py) |
| **NoThinking 943 audit + consensus join** — full 943 NoThinking-SC results already exist on disk (`inference/results/hybrid/tnr-B/nothinking_full_943_20260527T000129Z.jsonl`, May 27 untouched). T1-shallow audit + cross-run join vs R20. **ZERO GPU cost** for the audit; the value is consensus with R20. Threshold: ≥10 unique-correct items vs R20 → Pick B candidate (NoThinking ∪ R20 consensus). | ≥10 unique-correct vs R20 | ~0 (audit) / +60 min A100 if fresh re-run wanted | minor (T1 catalog + cross-join script) |
| **GenSelect re-test (fix candidate-window bug)** — POC failed due to candidate inputs truncated to ~500 chars (per inference/runs/selection/genselect_poc/findings.md). The "Qwen bad at self-verification" conclusion was unvalidated — the bug masked the test. Fix candidate window, smoke-test 5 items per discipline rule, then 943 if smoke passes. | smoke shows Qwen-as-judge produces sensible outputs on full-length candidates | ~60 min A100 | ~30 min code (increase candidate-window budget + smoke-test wrapper) |
| **High-budget re-run on truncated** (target: 17 R20-still-truncated items at 81920/65536 tokens) | already-known 17 items: [93,112,161,204,229,275,308,312,376,383,445,498,586,652,724,799,809] | ~30 min A100 | none |
| **Multi-temp SC sweep** on contested (Sun et al. Qwen3-4B +7.3pp) | If single-temp SC shows consistent same-failures across all p943 runs | ~60 min A100 | minor (multi-temp wrapper) |
| **Adapter eval (SFT v5 ckpt-1176)** | Default-include for cross-run diversity even if standalone is at break-even; per memory entry SFT v5 trained QLoRA ckpt-1176 (ep12) 505MB LFS, never tested vs R20 baseline | ~60 min A100 | none |

## Decision algorithm at 05:00 Sun

1. Read `CROSS_RUN_MATRIX.csv`; count items per threshold above.
2. **Check param-lever evidence** if V-series (R15–R19) or R14 (run13_rp110) shallow batch has been cataloged: scan their READMEs for which sampling params helped/hurt. Multi-temp SC candidate gets stronger evidence base if V4_temp_diversification showed gains; rep-penalty tweaks get evidence base from R14. **If V-series not yet cataloged at 05:00, the multi-temp candidate is evaluated on Qwen3-4B research priors alone** (Sun et al. +7.3pp), no V-series boost.
3. Rank candidates by `(items_addressable / GPU_minutes)`.
4. Pick top 2–3 that fit the 05:00 → 09:30 Sun window (4.5 hr).
5. Fire on 3 Thunder A100s **in parallel** (one run per GPU; no GPU-budget constraint).
6. Adapter training on a 4th Thunder if separable; otherwise queue after morning runs finish (~10:30 Sun).

## Hard skip rule

If watchlist signals are weak across the cohort:
- Few A_lucky_sample with high n_samples_math_correct (< 10 items)
- Few truncated items (< 5)
- Low cross-run divergence (most items agree across p943 cohort)

…then **skip morning inference entirely**. All GPU time goes to adapter training + structural normalizer build. Submitting more variants of the same Qwen output won't help; the lever is post-processing.

## Out of scope for morning runs

- Few-shot exemplar prompting (cross-item transfer per Rain's earlier idea — high-craft, harder to verify under deadline pressure than the mechanical options above)
- GenSelect (PoC had truncation issues — not enough time to debug)
- Fresh SFT training beyond v5 (only if Bucket B is clearly large AND adapter v5 eval shows regression)
- Teacher-model anything (rule #11)

## Submission slot reservations for morning-run outputs

Per `strategy/SESSION_HANDOFF.md` + ChatGPT submission-strategy view:
- Morning-run Kaggle validation: **1 slot max** per run, only after offline analyzer confirms positive direction
- If a morning run flips ≥10 items math-wrong → math-right on the analyzer's CLEAN gold subset → it earns a slot
- Otherwise the output stays in the cross-run matrix as input to consensus, no slot burn

## Post-hoc

If morning runs surface new findings, they go to `inference/FINDINGS.md` (cross-cutting) or per-run findings within their own R-folder if cataloged. The watchlist itself becomes archive once decisions are made.

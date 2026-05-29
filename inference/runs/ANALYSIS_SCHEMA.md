# inference/runs/ANALYSIS_SCHEMA.md — Per-run analysis spec

> **Status (Day 7, 2026-05-29)**: schema AGREED with Rain. Implementation NOT started. One decision pending (see "Open decision" at bottom) before building the analyzer.

## Purpose

For every inference run, produce a consistent analysis that answers: where did this run fail, what's recoverable by post-processing (format fix), and what's a real math miss (adapter candidate). The end goal is the **Bucket A / Bucket B** label per item (the F7 operational unlock).

## Artifacts per run

Stored in the run's own folder (`inference/{adapter|base_model}/R{NN}_.../`):

1. **`analysis.csv`** — human-readable, ~943 rows, no reasoning traces. Columns:
   ```
   item_id, category, tier, gold_answer, gold_source, gold_uncertain_flag,
   extracted_answer, extracted_empty_flag, truncated_flag,
   format_correct, math_correct, format_failure_subtype, bucket,
   n_tokens_total, n_tokens_thinking,
   sc_vote_size, sc_total_samples,
   response_preview, notes
   ```
2. **`analysis.jsonl`** — full data, ~943 entries, includes `full_response`, `full_reasoning_trace`, `all_boxed_extracted`. Version-controlled (LFS if >10MB).
3. **`analysis_samples.jsonl`** — SC runs ONLY. One entry per sample (943 × N). Columns:
   ```
   item_id, sample_index, sample_extracted, sample_correct,
   sample_truncated, sample_temperature, sample_top_p, sample_seed, sample_n_tokens
   ```

Cross-run:
4. **`inference/runs/CROSS_RUN_MATRIX.csv`** — 943 rows × N runs. Marks each item right/wrong/truncated/math-right per run. Collapses to a `bucket` column per item once all runs are cataloged. THIS is the operational endpoint.

Reasoning traces stay in the original raw `samples.jsonl`; analysis files reference by `(item_id, sample_index)` — never duplicate the trace into CSV.

## Column definitions (the 9 agreed additions, + Rain's original 5)

**Rain's original schema**: per-item row, `format_correct`, `math_correct`, full answer + reasoning trace, `notes`. For SC: a samples sheet + a voted sheet.

**Agreed additions (1-9, all locked):**
1. `gold_answer` + `gold_source` — from MASTER_ANSWERS; tier of evidence (3/3 teachers / wolfram_HIGH / search_GOLD / ...). T4/T5 items → `gold_uncertain_flag=true`, don't pretend to score.
2. `extracted_answer` (= last `\boxed{}` the grader sees) + `extracted_empty_flag` (no box at all → no_box_rescue category). Distinct from `full_response`.
3. `truncated_flag` — response hit `max_tokens`. Distinct failure mode from wrong-math. Detect via `n_tokens >= max_tokens - 10`.
4. Item metadata join — `category` (MCQ/free), `tier` (T1-T5), `n_slots_expected` (from `[ANS]` markers). From MASTER_ANSWERS + private.jsonl.
5. `sc_vote_size` / `sc_total_samples` — voted sheet: "5/8 agreement" vs "8/8" vs "all-disagree → pass@1 fallback". All-disagree flagged separately.
6. Per-sample SC columns (in `analysis_samples.jsonl`): `sample_index`, `sample_extracted`, `sample_temperature`. Shows WHICH samples were right when the vote was wrong.
7. Run-level header — config (model/decoding/tokens/items), date, Kaggle score, artifact path. Self-describing.
8. `format_failure_subtype` — which Tier-1/2/3/4 rule from `postprocessing/NORMALIZATION_RULES.md` was violated (trailing-zero, fraction-vs-decimal, multi-answer-slot, MCQ-letter-mismatch, missing-box, etc.).
9. `math_right_in_response_body` — DEFERRED (expensive, needs LLM-as-judge on prose). Only populate during an explicit Bucket-A hunt. The simple `extracted_answer` check captures ~95% of value.

**Derived:**
- `bucket` ∈ `{A, B, unknown}`: A = math right in this (or any) run, format-fix needed → no adapter. B = math never right → adapter candidate. unknown = gold uncertain.

## Scoring methodology (decided)

- **Format check**: automated via Hendrycks normalizer (the grader's actual logic — `postprocessing/scripts/apply_grader_normalization.py` or equivalent). Deterministic.
- **Math check (numeric)**: automated, numeric tolerance after extraction.
- **Math check (symbolic/multi-answer)**: automated where possible (sympy / normalized string match), flagged for review where not.
- **`math_right_in_response_body`**: deferred unless explicit Bucket-A hunt.

## Salvaged design ideas (from the 2026-05-29 normalization dump — good instincts, fold in)

The dump described an uncommitted parallel stack (see "Open decision"). Regardless of whether we recover its code, these design ideas are sound and we adopt them:

- **Surrogate-gold hierarchy** (use for `gold_source` priority): Wolfram HIGH → unanimous teachers → high-confidence answer sheet → high-confidence backsolve → sheet fallback.
- **Action bucketing** (richer than A/B for the review pass): `SUBMIT_AS_IS`, `SUBMIT_NORMALIZED`, `SUBMIT_NORMALIZED_UNDERCOUNT`, `MANUAL_UNDERCOUNT_REVIEW`, `HOLD`.
- **Review priority order**: undercount → mcq_not_letter → no_box_item → direct disagreement with strong surrogate gold → (weaker) backsolve_disagree.
- **Metadata hygiene caveat**: don't blindly trust tracker `best_answer` if it looks dirty/rambling — sanitize surrogate gold separately from output normalization.

## Implementation path (decided)

1. **Build `inference/scripts/analyze_run.py` ONCE.** Input: a run jsonl + MASTER_ANSWERS + private.jsonl. Output: the 3 artifacts above for that run.
2. **Run it on R14 first** (our best, 0.646, most-mined). Pressure-test the schema against real data with Rain.
3. **Refine schema if wrong** — cheap at run-1, expensive at run-15.
4. **Batch across all ~30 runs** once the analyzer is trusted.
5. Per-session catalog work then = `analyze_run.py R{NN}` + read output + write prose `findings.md` + escalate cross-cutting → ~30-60 min/run.

## OPEN DECISION (blocks build — Rain to decide)

The 2026-05-29 normalization dump described a full parallel stack (`normalizer.py`, `build_review_sheet.py`, `INFERENCE_ANALYSIS_PIPELINE.md`, a judger move into a `grading/` package, etc.). **VERIFIED 2026-05-29: none of it is on `main` or any remote branch. `judger.py` is still at root. The work is uncommitted/phantom.**

What IS on main (the real stack): `judger.py` (root, 28pp Kaggle gap, degenerate-detection only), `postprocessing/STRICT_NORMALIZER_SPEC.md`, `postprocessing/scripts/apply_grader_normalization.py`, `postprocessing/NORMALIZATION_RULES.md`, `postprocessing/FORMAT_RULES.md`, `tests/test_grader_normalization.py`.

**Decision needed:**
- **(A) Recover the phantom work** — find which runtime it's on, push, verify, adopt. Saves rebuild IF it's real and good. Risk: may not exist / may be buggy / may conflict with the existing stack (two normalizers, two judger homes).
- **(B) Build fresh on the existing stack** — use `apply_grader_normalization.py` + `judger.py` already on main, write `analyze_run.py` to this schema. Borrow the salvaged design ideas above. No dependency on code we can't see.

**claude_strategy recommendation: (B), salvage the design.** Don't depend on phantom code with the deadline this close.

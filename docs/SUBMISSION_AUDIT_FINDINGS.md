# Submission & Answer Sheet Audit — 2026-05-27 (Day 3)

**Auditor:** claude_strategy (submissions agent)
**Scope:** Full read of every submission CSV, answer sheet script, post-processing script, and documentation file across the repo.
**Repo:** beepbeeepimajeep/151B_SP26_Competition

---

## EXECUTIVE SUMMARY

The submission and answer sheet infrastructure has grown organically across 22 days of competition. The core pipeline is solid (well-designed v5.1 weighted voting with numeric clustering and correlation dampening), but **the script registries are stale** — all three answer sheet builder scripts (v4, v5, v5.1) contain identical 15-entry registries missing 8+ submissions with known Kaggle scores. Additionally, documentation is fragmented across 4+ locations (2 deprecated), 3 files referenced in docs are missing from the repo, and 5 files in the repo have no documented Kaggle score anywhere.

---

## 1. SUBMISSION INVENTORY

### 1.1 Files in `submissions/` folder (26 total)

| # | File | Script Registry | Doc Registry Score | Status |
|---|------|:---:|---|---|
| 1 | run14b_v3filtered.csv | ✅ 0.646 | 0.646 | OK |
| 2 | run14b_sc8_v1.csv | ✅ 0.639 | 0.639 | OK |
| 3 | run09sc8_v1_private943.csv | ✅ 0.614 | 0.614 | OK |
| 4 | run09sc8_format_fixed.csv | ✅ 0.611 | 0.611 | OK |
| 5 | run08v2_v1_private943.csv | ✅ 0.586 | 0.586 | OK |
| 6 | diagnostic_sub_a.csv | ✅ 0.505 | 0.505 | OK |
| 7 | sftv3_epoch8_sc1_final.csv | ✅ 0.452 | 0.452 | OK |
| 8 | run09sc8_probe_b_reversed.csv | ✅ 0.438 | 0.438 | OK |
| 9 | run10_v3perslot_private943.csv | ✅ 0.424 | 0.424 | OK |
| 10 | expA_run08_perslot_perturbed.csv | ✅ 0.420 | 0.420 | OK |
| 11 | D_05_07_numina_d.csv | ✅ 0.310 | 0.310 | OK |
| 12 | diagnostic_sub_c.csv | ✅ 0.222 | 0.222 | OK |
| 13 | post_filtered_b.csv | ✅ 0.151 | 0.151 | OK |
| 14 | f_today_F.csv | ✅ 0.137 | 0.137 | OK |
| 15 | E_05_13_h100run_e.csv | ✅ 0.028 | 0.028 | OK |
| 16 | info_4_t1lock_sheet_rest.csv | ❌ | 0.671 | **BEST DIAG** — excluded (circular) |
| 17 | info_2_answersheet_on_uncertain.csv | ❌ | 0.667 | excluded (circular) |
| 18 | slot1_reformat.csv | ❌ | 0.646 | **⚠ SHOULD ADD to registry?** |
| 19 | slot3_run14b_nobox_patched.csv | ❌ | 0.646 | **⚠ SHOULD ADD to registry?** |
| 20 | slot1_minimal_norm.csv | ❌ | 0.643 | **⚠ SHOULD ADD to registry?** |
| 21 | slot1_adapter_v5_plus_run14b_20260525_1623.csv | ❌ | ~0.639 | **⚠ Score in doc as different filename** |
| 22 | sftv4_adaptive_rerolled.csv | ❌ | 0.597 | Correctly excluded (circular) |
| 23 | info_1_teacher_on_uncertain.csv | ❌ | **NONE** | **🔴 NO SCORE DOCUMENTED** |
| 24 | info_3_full_answersheet.csv | ❌ | **NONE** | **🔴 NO SCORE DOCUMENTED** |
| 25 | slot1_reformat_plus_b2_plus_sheet.csv | ❌ | N/A (skipped) | Not submitted to Kaggle |
| 26 | slotA_slot1_dfrac_only.csv | ❌ | N/A (skipped) | Not submitted to Kaggle |

### 1.2 Files referenced in docs but MISSING from `submissions/` folder

| File | Doc Score | Notes |
|------|-----------|-------|
| g_epoch8_lora_G.csv | 0.017 | In SUBMISSION_REGISTRY.md but not in repo |
| slot1_wolfram_full_overrides.csv | 0.653 | **BEST REAL** — not in repo! |
| slot1_adapter_v5_plus_run14b_20260525.csv | 0.639 | In docs with slightly different filename than repo version |

### 1.3 Critical finding: BEST REAL submission (0.653) is not in the repo

`slot1_wolfram_full_overrides.csv` scored 0.653 (best real inference submission) but does not exist in `submissions/`. This file needs to be recovered from wherever it was generated (likely tnr-0/tnr-1 or vscode agent) and committed.

---

## 2. ANSWER SHEET SCRIPT AUDIT

### 2.1 Script versions

| Script | Output | Key difference |
|--------|--------|---------------|
| `build_answer_sheet.py` (v1) | `results/answer_sheet/unified_answer_sheet.csv` (79KB) | Original, unclear methodology |
| `build_answer_sheet_v4.py` | `results/answer_sheet/unified_answer_sheet_v4.csv` (29KB) | Score-weighted voting, correlation dampening |
| `build_answer_sheet_v5.py` | `results/answer_sheet/unified_answer_sheet_v5.csv` (29KB) | + numeric clustering (frac/decimal equivalence) |
| `build_answer_sheet_v5_1.py` | `results/answer_sheet/unified_answer_sheet_v5_1.csv` (29KB) | + xhigh refusal recovery (11 items) |
| `backsolve.py` | `results/unified_answer_sheet.csv`, etc. | **DEPRECATED** — header says so |

### 2.2 ALL THREE ACTIVE SCRIPTS HAVE IDENTICAL STALE REGISTRIES

`build_answer_sheet_v4.py`, `build_answer_sheet_v5.py`, and `build_answer_sheet_v5_1.py` all contain the **exact same 15-entry SUBMISSION_REGISTRY**. This means:

- **8 submissions with known Kaggle scores are absent** from the voting pool
- The answer sheet has been computed from a subset of available signal
- Submissions scoring 0.643–0.653 (slot1_minimal_norm, slot1_reformat, slot1_wolfram, slot3_nobox) are NOT contributing to the answer sheet despite being the strongest real-inference results

### 2.3 Which missing submissions SHOULD be added?

**Should ADD (independent signal, not circular):**
- `slot1_minimal_norm.csv` (0.643) — yes, BUT highly correlated with run14b (same inference, post-processing only)
- `slot1_reformat.csv` (0.646) — same caveat, derivative of run14b
- `slot3_run14b_nobox_patched.csv` (0.646) — same caveat
- `slot1_adapter_v5_plus_run14b_20260525_1623.csv` (0.639) — hybrid, some independent signal

**Should NOT add (circular reasoning):**
- `info_2_answersheet_on_uncertain.csv` (0.667) — T3+T4 items ARE from the answer sheet
- `info_4_t1lock_sheet_rest.csv` (0.671) — T2-T4 items ARE from the answer sheet
- `sftv4_adaptive_rerolled.csv` (0.597) — trained on answer sheet labels (already documented)
- `info_1_teacher_on_uncertain.csv` — likely uses teacher answers (circular)
- `info_3_full_answersheet.csv` — literally IS the answer sheet

**Assessment:** The slot1_* submissions are essentially run14b with post-processing, so adding them provides minimal new signal. They'd all go into the `base_qwen3` correlation group and get dampened by sqrt(11) instead of sqrt(8). The marginal information gain is small. However, the higher scores (0.643–0.653) would upweight whatever post-processing differences exist, which IS legitimate signal about formatting correctness.

### 2.4 v5 vs v5.1 output comparison

Both `unified_answer_sheet_v5.csv` and `unified_answer_sheet_v5_1.csv` are 29419 bytes. The v5.1 addition (11 xhigh refusal recoveries at weight 0.50) either had zero effect on the final vote outcomes, or the differences are limited to items where xhigh was the tiebreaker. Given xhigh's low weight (0.50 vs 0.60-0.70 for other teachers), the impact is likely negligible.

### 2.5 Bug in v5.1: canonicalized xhigh answers stored as surface forms

In `build_answer_sheet_v5_1.py` line 262:
```python
norm = cluster_key(canonical_key(str(ans)))
```

xhigh recovery answers are being canonicalized BEFORE being stored as the surface form. This means the xhigh vote contributes a canonical key (e.g., `NUM:3.6`) as the "answer" rather than the original surface form. If the xhigh cluster wins, the emitted best_answer would be the canonical key string, not a valid LaTeX expression. This is a latent bug (likely hasn't triggered because xhigh weight is too low to swing any votes, which explains the identical file sizes).

---

## 3. POST-PROCESSING SCRIPT AUDIT

### 3.1 Script inventory and roles

| Script | Purpose | Status |
|--------|---------|--------|
| `to_submission_csv.py` | JSONL → Kaggle CSV converter | ✅ Active, well-tested |
| `fix_submission_format.py` | Multi-answer box consolidator | ✅ Active, +0.3pp proven |
| `apply_grader_normalization.py` | LaTeX normalizer (dfrac_only / minimal) | ✅ Active, +0.4pp proven |
| `splice_submission.py` | Base + adapter merger | ✅ Active |
| `post_filter.py` | Shape filter on SC JSONL | ✅ Active, +0.7pp proven |
| `no_box_rescue.py` | Re-prompt no-box items | ⚠️ Results: 0/18 scored on Kaggle |
| `backsolve.py` | Bayesian answer back-solver | ❌ DEPRECATED |

### 3.2 Post-processing pipeline dependencies

The proven post-processing stack (in order) is:
1. `post_filter.py` (shape filter on SC samples) → +0.7pp
2. `to_submission_csv.py` (JSONL → CSV)
3. `apply_grader_normalization.py --mode minimal` → +0.4pp
4. `fix_submission_format.py` (multi-answer consolidation) → +0.3pp
5. Optional: Wolfram last-box overrides → +0.7pp (but format-mismatch on 32/38 items)

Total stacked: ~+2.1pp from post-processing alone.

### 3.3 Normalizer gotcha: dfrac_only mode is ANTI-helpful

`apply_grader_normalization.py` documents that `dfrac_only` mode converts `\dfrac` → `\frac`, but Kaggle's sample_submission actually uses `\dfrac` as canonical. The dfrac_only mode was a diagnostic probe that SHOULD NOT be used for real submissions. The `slotA_slot1_dfrac_only.csv` in the folder was correctly flagged as confounded and skipped.

---

## 4. DOCUMENTATION AUDIT

### 4.1 Fragmentation

Submission documentation exists in **6 locations**, only 2 of which are current:

| Location | Status | Notes |
|----------|--------|-------|
| `docs/SUBMISSION_REGISTRY.md` | **CURRENT** | Best single source of truth |
| `docs/ANSWER_SHEET.md` | **CURRENT** | Methodology doc (references wrong script version) |
| `docs/SUBMISSION_PLAN.md` | DEPRECATED | Pointer to Drive |
| `docs/DAY_2_SUBMISSION_QUEUE.md` | DEPRECATED | Pointer to Drive |
| `experiments.md` | PARTIAL | Has analysis for subs 1-4 only (first 4 submissions) |
| Memory (claude_strategy) | PARTIAL | References `build_answer_sheet_v4.py` as canonical |

### 4.2 docs/ANSWER_SHEET.md references wrong script

The doc says "Script: scripts/build_answer_sheet_v4.py" but the latest version is v5.1. The v4 doc history section stops at "v4 (2026-05-24)" — v5 and v5.1 are undocumented in this file.

### 4.3 Memory references wrong script

Memory says "Answer sheet workflow: After each Kaggle submission — add to SUBMISSION_REGISTRY in `scripts/build_answer_sheet_v4.py`" but the canonical script is v5.1. This means any agent following memory instructions would update the wrong file.

---

## 5. RESULTS DIRECTORY AUDIT

### 5.1 Answer sheet outputs

| File | Size | Producer | Status |
|------|------|----------|--------|
| `results/answer_sheet/unified_answer_sheet.csv` | 79KB | build_answer_sheet.py (v1) | STALE |
| `results/answer_sheet/unified_answer_sheet_v4.csv` | 29KB | build_answer_sheet_v4.py | STALE |
| `results/answer_sheet/unified_answer_sheet_v5.csv` | 29KB | build_answer_sheet_v5.py | CURRENT |
| `results/answer_sheet/unified_answer_sheet_v5_1.csv` | 29KB | build_answer_sheet_v5_1.py | CURRENT |
| `results/answer_sheet/answer_matrix.json` | 555KB | Unknown (v1 era?) | STALE |
| `results/answer_sheet/validation_report.txt` | 1KB | Unknown | STALE? |
| `results/unified_answer_sheet.csv` | 348KB | backsolve.py (DEPRECATED) | STALE |

Multiple stale answer sheet files could cause confusion if an agent or script references the wrong one.

### 5.2 Empty file alert

`results/no_box_rescue_20260527T152423Z.jsonl` is **0 bytes** — the no-box rescue run appears to have produced no output.

---

## 6. PATTERN ANALYSIS & KEY INSIGHTS

### 6.1 Score trajectory

Plotting all real-inference submissions chronologically:
- 2026-05-06: 0.586 (run08v2, first sub)
- 2026-05-06: 0.424, 0.420 (format experiments, regression)
- 2026-05-13: 0.614 (run09 SC=8, +2.8pp)
- 2026-05-23: 0.646, 0.639 (run14b 32K, +3.2pp)
- 2026-05-25: 0.646 (nobox patch, +0.0pp)
- 2026-05-26: 0.643 (minimal norm, baseline reset)
- 2026-05-26: 0.646 (reformat, +0.3pp)
- 2026-05-26: **0.653** (Wolfram overrides, +0.7pp, BEST REAL)

Total gain: +6.7pp over 20 days (0.586 → 0.653).

### 6.2 Diagnostic submissions (not real inference)

The info_4 submission (0.671) uses the answer sheet itself for T2-T4 items — it's a ceiling estimate of what "perfect post-processing + real T1" could achieve. The gap between best real (0.653) and best diagnostic (0.671) is **1.8pp** — this is the remaining answer-sheet uplift available.

### 6.3 Wolfram underperformance

Wolfram overrides scored only ~6/38 items correctly despite Wolfram being a symbolic engine. The SUBMISSION_REGISTRY.md identifies "format-mismatch (parens, commas, infty vs \infty, LaTeX wrapping)" as the bottleneck. This suggests the remaining Wolfram uplift is largely a formatting problem, not a correctness problem.

### 6.4 Locked levers (validated via Kaggle)

| Lever | Delta | Method |
|-------|-------|--------|
| 32K vs 16K token budget | +2.5pp | run14b vs run09 |
| V3 shape filter | +0.7pp | run14b_v3filtered vs run14b_sc8 |
| Minimal LaTeX normalizer | +0.4pp | slot1_minimal_norm vs slot1 |
| Reformat post-processor | +0.3pp | slot1_reformat vs slot1_minimal_norm |
| Wolfram canonical overrides | +0.7pp | slot1_wolfram vs slot1_reformat |
| Per-slot \boxed{} format | −16.2pp | run10 vs run08v2 (DO NOT USE) |
| Answer order reversal | −17.6pp | probe_b_reversed vs run09 (DO NOT USE) |

### 6.5 Correlated submissions dominate

8 of 15 registry entries are from the same base Qwen3 model. The correlation dampening (÷√8 ≈ ÷2.83) is critical. Without it, the answer sheet would be 53% base_qwen3 signal by vote weight, drowning out teacher diversity.

---

## 7. RECOMMENDATIONS FOR DAY 3 (today)

### 7.1 CRITICAL: Recover slot1_wolfram_full_overrides.csv

The BEST REAL submission (0.653) is not in the repo. It must be recovered from wherever it was built and committed to `submissions/`.

### 7.2 Update memory: correct script reference

Memory says `build_answer_sheet_v4.py` — should say `build_answer_sheet_v5_1.py`.

### 7.3 Consider updating the script registry

Adding the slot1_* and slot3 submissions to the registry would provide marginal signal (they're all derivatives of run14b so heavily dampened), but at 0.643-0.653 their scores are higher than run14b_v3filtered (0.646) and would slightly upweight post-processing correctness signal. The cost is low (3 lines of code), the risk is near-zero.

Suggested additions (all go into `base_qwen3` correlation group):
```python
"slot1_minimal_norm.csv":        0.643,
"slot1_reformat.csv":            0.646,
"slot3_run14b_nobox_patched.csv": 0.646,
```

Do NOT add: info_*, sftv4, or slot1_wolfram (all contain circular or oracle-derived answers).

### 7.4 Find scores for undocumented submissions

`info_1_teacher_on_uncertain.csv` and `info_3_full_answersheet.csv` have no Kaggle scores documented anywhere. If they were submitted, the scores should be recorded. If they weren't submitted, they should be removed from the folder to avoid confusion.

### 7.5 Fix v5.1 xhigh bug

Line 262 of `build_answer_sheet_v5_1.py` applies `cluster_key(canonical_key())` to xhigh answers before storing them. This should be just `normalize()` to match how all other answers are stored, with clustering happening downstream in `weighted_vote()`.

---

## 8. FILE MANIFEST

All submission-related files in the repo, organized by category:

### Submission CSVs (26 files in `submissions/`)
(see inventory table in §1.1)

### Answer Sheet Scripts (5 files in `scripts/`)
- `build_answer_sheet.py` — v1, original
- `build_answer_sheet_v4.py` — v4, score-weighted voting
- `build_answer_sheet_v5.py` — v5, + numeric clustering
- `build_answer_sheet_v5_1.py` — **v5.1, CURRENT** (+ xhigh recovery)
- `backsolve.py` — DEPRECATED

### Post-Processing Scripts (6 files in `scripts/`)
- `to_submission_csv.py` — JSONL → CSV
- `fix_submission_format.py` — multi-answer consolidation
- `apply_grader_normalization.py` — LaTeX normalization
- `splice_submission.py` — base/adapter merger
- `post_filter.py` — shape filter
- `no_box_rescue.py` — re-prompt no-box items

### Answer Sheet Data Inputs (2 files in `data/`)
- `teacher_answers_compact.json` — 3-teacher per-item answers
- `xhigh_refusal_recovery.json` — 11 xhigh recovery items

### Answer Sheet Outputs (7 files in `results/answer_sheet/`)
(see table in §5.1)

### Documentation (6+ files)
(see table in §4.1)

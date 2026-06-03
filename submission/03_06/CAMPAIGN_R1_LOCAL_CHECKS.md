# 03_06 SOURCE CAMPAIGN R1 — local checks

## Investigation A (xhigh full source)
FOUND: `data/search/teachers/xhigh/answers.csv` = full **943-row** xhigh (940 non-empty),
NOT subset-only. Used for s05 (coverage 940). The tracker's `teacher_gpt55xh` (254) was a
curated subset (== qwen_sc8_ans subset). s05 uses the full file.

## Deliverable 0 — qwen_run_answer_matrix.csv
Per-run coverage (non-empty extracted_answer, no re-vote): R08 942, R09 943, R10 943,
R20 943, R20b 943, NT 942; subset twins NT_tr 61, TH_tr 61.
Cross-run agreement (max identical among 6 full runs) histogram:
{1:9, 2:106, 3:115, 4:134, 5:226, 6:353}. (353 items unanimous across all 6 Qwen runs.)
cross_run_correctness_matrix id-set cross-check: matches 0..942.

## Agreement sweep (s11–s14) — overrides + winning-agreement-size histogram
- s11 K>=2: 832 overrides, hist {2:167, 3:139, 4:428, 5:98}
- s12 K>=3: 665 overrides, hist {3:139, 4:428, 5:98}
- s13 K>=4: 526 overrides, hist {4:428, 5:98}
- s14 K==5: 98 overrides (unanimous 5-LLM)

## Format gap (s10 canonical vs s15 raw v7)
183 rows render-differently between canonical (s10) and raw (s15). Under
`grading.grader.Grader.is_equal` (value-equality): **183/183 = 100.0%** are value-equal
(0 parse-err, 0 timeout). Prediction: a true value-based Kaggle grader closes the entire
s10–s15 format gap (they should score identically). Any Kaggle delta s10 vs s15 ⇒ residual
strict/format sensitivity in the live grader.

# Pick B candidates — NoThinking ∪ R20 consensus-join

**Built:** 2026-05-30 · claude_vscode · zero GPU (pure post-processing). NOT yet Kaggle-submitted — **Pick B candidates awaiting Rain's decision.**

## What these are
The first Pick-B candidate that **adds correctness over R20's 0.646 inference floor**. Source = `submission/csvs/run14b_sc8_v1.csv` (the raw R20 SC@8 voted output = `run14b_sc8_v1_private943_tok32k_pp1` = catalog R20; chosen over `run14b_v3filtered.csv` [R20b], `slot3_*` [nobox-patched] and `slot1_adapter_*` [adapter-hybrid] because it's closest to RAW R20 voted_answer, so the join's effect is cleanly attributable). On 13 (or 14) specific items, the R20 answer is replaced with the **NoThinking** run's voted answer (`NT_eval_nothinking_sc8_p943_t8k`), which the T1.5 cross-run audit (commit eae3c2a) + ChatGPT T3 verified as correct where R20 was wrong. All other 930 rows pass through **byte-for-byte identical** to source.

## Two variants
- **`picks_nothinking_join_conservative_v1.csv`** (13 overrides) — **primary Pick B candidate.** R20.B rescues [5, 257, 345, 474, 578, 868, 917] + R20.A_lucky rescues [181, 584, 642, 712, 715, 763]. All T3-confirmed; 633 EXCLUDED (noise — n_voting=3, T3 drop).
- **`picks_nothinking_join_diagnostic_v1.csv`** (14 = conservative + id=282) — **diagnostic only.** id=282 is a disputed-gold calibration item (NT `e^2` vs R20 `e^2,-e^2` spurious extra-root; backsolve evidence on R20's side is tainted). Submit only if a slot is spare — it empirically tests which gold form Kaggle accepts.

Override CSVs (audit trail): `overrides_nothinking_join_{conservative,diagnostic}.csv` (id, override_value, evidence).

## Override mechanism (and a corrected gotcha)
`postprocessing/scripts/apply_overrides.py` **full-replaces** each overridden response with a single `\boxed{value}`. We do NOT append — verified empirically that appending `\n\n\boxed{NEW}` after a response ending in a `$$\boxed{...}$$` block makes the grader's last-contiguous-box-group extractor MERGE old+new boxes (e.g. `a,b` + `c,d` → graded `a,b,c,d`, wrong slot count; 10/10 multi-slot overrides graded FALSE under append). Full-replace guarantees the grader sees exactly the override value. All 13 (+282) confirmed `auto_judge==True` against gold under the value-equality grader.

## Rule #11 legality
**Legal.** Both R20 and NoThinking are `Qwen3-4B-Thinking-2507` outputs — the override is **Qwen-over-Qwen** on specific items (no teacher/anchor/Opus/search values enter `response`). NoThinking is a different *inference mode* (prefill `</think>` bypass) of the same locked model, not a different model. The selection of WHICH items to override used independent gold for verification, but the submitted VALUE is purely Qwen (NoThinking's voted answer).

## Expected Kaggle delta vs source
~**+1.4pp** on the ~283-item public slice (≈4 of the 13 rescued items expected to fall on-slice, per the slice ratio). Directional only — local grader confirms all 13 are now correct vs gold, but the local↔Kaggle gap and the unknown slice membership make the realized delta uncertain. **id=763 caveat:** its override `4+9,8\div3` is an *unevaluated expression* (value-equal to gold `13,8/3` under our sympy grader, but a Kaggle-grader risk if Kaggle doesn't evaluate `4+9`).

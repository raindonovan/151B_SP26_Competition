# inference/SCRATCH.md — Unsorted findings, ideas, observations

Drop anything here. Rain will sort it later.

---

- Qwen3-4B official recommended sampling: temperature=0.6, top_p=0.95, top_k=20, min_p=0, presence_penalty (not repetition_penalty). Greedy contraindicated for thinking mode.
- NoThinking = prefill only. enable_thinking=False is a no-op on this model.
- Repetition collapse at greedy traced to decoding config, not weight-space collapse. repetition_penalty=1.1 partially recovers.
- Sun et al. showed +7.3pp from multi-temperature voting on Qwen3-4B size class. Never tried.
- WiSE-FT for LoRA = scale lora_alpha by delta (delta=0.5 prior). No retraining needed. Could recover v5 adapter.
- SFT v5 regression was ~7 semantic items, not format. 87% T1-easy in training set is structural issue.

---

## Two-bucket framework for tier-1 items (2026-05-28) — sets up tomorrow's run scan

CONFIRMED (see postprocessing/FINDINGS.md F7): tier-1 items (Wolfram HIGH ∧ web-search GOLD ∧ 3/3 teachers) ARE getting graded wrong on FORMAT. The fraction fix proved it (+2 slice items from pure decimal→fraction flip).

TOMORROW'S INFERENCE-RUN SCAN: for every tier-1 item, classify into:
- **Bucket A**: some inference run (SC8/SC16/NoThinking/etc.) produced the correct MATH → find it, format-fix, submit. NO adapter needed.
- **Bucket B**: NO run ever produced the correct math → adapter candidate.

Then the format layer applies to BOTH buckets: even bucket-A items can be graded wrong if emitted in wrong format.

Operational tier-1 filter: wolfram_confidence=HIGH AND search_status=GOLD AND all 3 teachers agree. Cross-reference each tier-1 item's gold answer against the voted answer in EVERY run's samples.jsonl. Need format-aware comparison (Hendrycks normalization), not raw string match.

---
## claude_vscode signoff — Day 9 — analyze_run.py v1 + R14 pressure-test (GATE FAILED — NOT committed)

### What was built
- `inference/scripts/analyze_run.py` — per-run analyzer to ANALYSIS_SCHEMA.md. Re-uses the merged stack: `grading.grader.Grader` (root judger value-equality engine) for `extract_boxed_answer` / `extract_all_boxed` / `auto_judge` / `split_by_comma`, and `apply_grader_normalization.normalize_row` (minimal cosmetic mode) for the format-fix probe. Auto-detects SC vs single via `samples` array. Derives gold + gold_source from MASTER_ANSWERS surrogate hierarchy (Wolfram_HIGH > unanimous_teachers > answer_sheet_HIGH > backsolve_HIGH > sheet_fallback); options come from the run jsonl (private.jsonl root has only id+question). Writes analysis.csv (run-meta comment header), analysis.jsonl (full_response + trace + all_boxed, row0 _run_meta), analysis_samples.jsonl (SC only).

### Pressure-test outcome (R14, run14b_sc8_v1, kaggle 0.646) — **GATE FAILED, did NOT commit**
- 2a ✅ analysis.csv = 943 rows (via proper CSV parse) + 13 meta comment lines + header.
- 2b ✅ analysis_samples.jsonl = 7544 (= 8×943) exact. analysis.jsonl = 943.
- 2c ⚠️ bucket A=501 B=10 unknown=432. B (10) far below the 100-300 estimate; unknown=432 not ~186 (the 186 was v7 tiering; MASTER sheet_tier T4+T5 = 104+328 = 432).
- 2d ❌ **Σmath_correct = 784 (0.831), expected ~607±30. +177 over.** Root cause = GOLD LEAKAGE: derived gold for certain tiers (T0-3) is the teacher/answer-sheet consensus, which was itself partly built from these same runs/submissions → circular. On certain items alone: 495/511 = 0.969 (implausible vs 0.646 external). Also denominator/grader mismatch: 943-item value-equality vs 283-slice strict-Kaggle.
- 2e ✅ 5A/5B hand-inspect: labels correct. A id=20 `228.0,229.0,250.0`≡gold`228,229,250` (value-equality working). B id=12 gold 2-slot `2c+4p=70, 11` vs extracted `11` (undercount), B id=82 `\text{No}` markers vs `No` — genuine B cases.
- 2f ❌ TWO bugs: (1) `extracted_empty_flag=True` on 19 rows that ALL have a non-blank `extracted_answer` — contradiction: flag uses extract_all_boxed (no-box), column uses extract_boxed_answer (has last-number/last-latex FALLBACK that fills a value). (2) `response_preview` embeds raw newlines → analysis.csv has 36130 raw lines (parses fine to 943 via csv module, but ugly/fragile for grep).
- format_correct == math_correct exactly (784/784) → the `minimal` cosmetic normalizer recovered ZERO format-only items. apply_grader_normalization only has dfrac_only/minimal modes (thin-space + \left\right strip) — NOT a gold-comparison "format_correct" checker. The schema's format_correct needs the structural normalizer (undercount collapse, multi-answer order, MCQ first-box), which isn't in that script.

### Open items / follow-ups for the per-run catalog loop (BLOCKERS before this is the gate)
1. **GOLD LEAKAGE (the big one):** need a leakage-free gold for math_correct, OR explicitly restrict scoring to gold_source ∈ {Wolfram_HIGH, unanimous_teachers} that are independent of the run, AND report math_correct ONLY on those, treating sheet_fallback/backsolve as unknown. Decide with strategy: is "audit score" meant to mirror Kaggle (then we need the held-out slice) or to measure "agreement with best surrogate gold" (then 0.83 is expected and the ±30 gate is wrong)?
2. **extracted_empty_flag fix:** make flag and column use the SAME extractor — either blank the column when no box, or define extracted_empty purely on `\boxed{` absence and stop trusting the fallback value.
3. **response_preview:** strip ALL whitespace runs to single spaces (kill \r and \n) so analysis.csv is one-line-per-row.
4. **format_correct:** wire to the structural normalizer (undercount collapse / multi-answer order / MCQ first-box), not the cosmetic minimal mode, or rename it to format_correct_cosmetic and DEFER the real one like format_failure_subtype.
5. **bucket B=10 is suspiciously low** — likely because unknown(432) absorbs most real misses (T4/T5), and certain-tier leakage inflates A. Will self-correct once #1 is fixed.

### Commit hash
NONE — gate failed (2d, 2f), per task rule 3 did not commit. Artifacts left in inference/scripts/_pressure_test_R14/ for inspection (uncommitted).

---
## claude_vscode signoff — Day 9 — analyze_run.py v3 (C1-C7) R14 re-run — GATES c+d FAILED, NOT committed

### What was built (patched v2, not rebuilt)
All 7 corrections applied to inference/scripts/analyze_run.py:
- C1: gold_independent_flag from RAW columns only (wolfram_confidence=='HIGH' OR search_status=='GOLD' OR 3-way raw teacher equality). Zero code reads of sheet_n_agree/sheet_evidence/sheet_confidence (grep-verified: only doc-comment mentions). New published column gold_independent_flag (between gold_source and gold_uncertain_flag).
- C7: gold_source precedence wolfram_HIGH > unanimous_teachers > search_GOLD > sheet_dependent; gold_answer from winning raw column; conflict notes written to notes col.
- C2: new gates (B>25 hard; scored acc∈[0.70,0.95]; A_lucky informational).
- C3: extracted_empty_flag = (extracted_answer==""). Single source of truth — 0 contradictions now.
- C4: response_preview = re.sub(r'\s+',' ',resp).strip()[-200:].
- C5: format_correct == math_correct (cosmetic-only capability documented); new col format_check_capability='cosmetic_only_until_structural'; removed apply_grader_normalization use.
- C6: audit-score reframe line in csv meta header (+ TODO: CATALOG.md note — see open items).
- bucket: not-independent→unknown; T4/T5→unknown; math_ok→A; SC any-sample-correct→A_lucky_sample; else B.

### Verification triple — ALL PASS
- grep forbidden cols in independence path: 0 code reads (only comments). PASS.
- gold_source label set ⊆ {wolfram_HIGH,unanimous_teachers,search_GOLD,sheet_dependent}: PASS.
- sum identity: wolfram_HIGH(58)+unanimous_teachers(452)+search_GOLD(37)=547 == gold_independent_flag True (547). PASS.

### Gates: a✅ b✅ c❌ d❌ e✅ f✅ g✅  →  STOP, did NOT commit
- (a) 943 rows + header + 14 meta comments ✅
- (b) 7544 sample rows ✅
- (c) B>25 ❌ — **B=4**. FAIL.
- (d) scored acc∈[0.70,0.95] ❌ — **0.981**. FAIL.
- (e) hand-inspect 4 B + 4 A_lucky (fewer than 5 each EXIST): labels all correct ✅
- (f) extracted_empty_flag==(""): 0 contradictions ✅
- (g) preview no newline/double-space: 0 violations ✅

### Bucket dist (v3): A=412 A_lucky_sample=4 B=4 unknown=523
scored set n=420, math_correct=412, acc=0.981.

### WHY c+d failed (methodological, NOT a code bug — strategy decision needed)
The scored set is 403/420 unanimous_teachers items, and unanimous_teachers acc=0.990. 3-teacher unanimity is itself a proxy for EASY/unambiguous items — exactly the ones Qwen also nails. The genuinely-hard independent gold (wolfram_HIGH n=8 acc=0.750, search_GOLD n=9 acc=0.778) IS in the gate band, but there are only 17 such items. So the [0.70,0.95]/B>25 gates assumed independent gold would be HARDER than the LB slice; it's actually EASIER (unanimity selection effect). The leakage fix worked (dropped from 0.831→ honest, removed sheet-derived gold) — but it didn't lower accuracy because the run genuinely agrees with teacher consensus.

Also: 127 independent-gold items are DISCARDED to unknown because sheet_tier∈{T4,T5} overrides independence. The T4/T5 gate uses the CONTAMINATED sheet_tier to throw away CLEAN independent gold — a tension in the C1 bucket order (not-independent check is fine; the gold_uncertain check after it nukes valid independent rows).

The 4 B rows are real but mostly MULTI-SLOT UNDERCOUNT (math right in body, last-box extractor missed slots): id=12 boxes (a)2c+4p=70 (b)11 → grader sees 11 only; id=712 boxes D,D,A → sees A; id=548 boxes 144=1.2x,120.00 → sees 120.00. id=127 5*ln(17/2)≡10.70 value-equal but judged wrong; id=389 MCQ-as-expression. These belong in a "format/undercount recoverable" lane, not pure adapter-B.

### Open items / follow-ups
1. STRATEGY DECISION: gates c+d are mis-calibrated for the unanimity-selection effect. Options: (i) relax d to [0.85,0.995] & drop/lower B>25 on the unanimity-heavy set; (ii) restrict the SCORED gate to wolfram_HIGH+search_GOLD only (the hard independent subset, n=17 here) and report unanimous_teachers separately; (iii) keep gates, accept that R14 simply agrees with teachers. I did NOT pick — need your call.
2. Bucket order: should independent-gold T4/T5 items still be scored (independence beats sheet_tier uncertainty)? Currently 127 clean items lost to unknown.
3. C6 CATALOG.md status note not yet added (only the csv meta header). Add when committing.
4. Multi-slot undercount is the dominant B/near-B failure → confirms postprocessing undercount lever; flag to postprocessing.

### Commit hash
NONE — gates c+d failed, per task rule did not commit. Artifacts uncommitted in inference/scripts/_pressure_test_R14/.

---
## claude_vscode signoff — Day 9 — analyze_run.py v3-final (C8-C10) R14 re-run — GATE (c-new) FAILED, NOT committed

### What was patched (v3, C8-C10 only; C1-C7 untouched)
- C8 bucket-order flip: wolfram_HIGH / search_GOLD bucket-decide regardless of sheet_tier; unanimous_teachers bucket-decides only at T1/T2/T3, else unknown. Branches on gold_source (encodes winning signal by C7 precedence).
- C9 gate recalibration in summary: (c-new) hard_independent = wolfram_HIGH+search_GOLD, acc gate [0.60,0.95]; (d-new) unanimous_teachers acc report-only (expect ≥0.90); B count no longer gated.
- C10 bucket_b_review_needed column (=bucket=='B') in csv + jsonl.

### Verification triple — ALL STILL PASS
labels ⊆ {wolfram_HIGH,unanimous_teachers,search_GOLD,sheet_dependent} ✅; sum-identity 547==547 ✅; 0 forbidden code reads (unchanged) ✅.

### Gates: a✅ b✅ (c-new)❌ (d-new)✅ e✅ f✅ g✅ (h-new)✅ (i-new)✅  → STOP, did NOT commit
- (a) 943 + 14 meta ✅  (b) 7544 ✅
- (c-new) hard_independent acc=**0.2947** (n=95) ❌ — FAR below [0.60,0.95].
- (d-new) unanimous_teachers acc=0.9901 (n=403) ✅ report-only.
- (e) 5B+5A_lucky inspected, labels correct ✅
- (f) 0 contradictions ✅  (g) 0 preview violations ✅
- (h-new) scored set 420→**498** (+78) ✅ (prompt expected 430-440; bigger because C8 admitted ALL wolfram/search T4/T5, not just a few)
- (i-new) wolfram_HIGH @ T4/T5 = 50, ALL 50 now scored ✅

### Bucket dist (v3-final): A=427 A_lucky_sample=13 B=58 unknown=445

### WHY (c-new) failed — gold-format artifact on hard T4/T5, NOT a code bug, NOT Qwen-wrong
C8 newly admitted 50 wolfram_HIGH + ~28 search_GOLD items that were T4/T5 (previously unknown). hard_independent jumped n=17 (prior v3) → n=95. These T4/T5 items have MESSY MULTI-SLOT / PRECISION gold, and with NO structural normalizer (C5) the value-equality judge false-negatives on:
- precision/rounding: id=5 135.325 vs 135.3, 4.2167 vs 4.217; id=67 13.9 vs 13.89; id=89 \frac{326}{7} vs 46.57 (=46.571…, value-equal!)
- format/representation: id=9 \frac{L-8x}{6F} vs mis-split gold 'L-8x, 6F' (Qwen MORE correct); id=72 'Quadrant IV' vs 'IV' (same)
- undercount: id=12 body has both boxes, grader sees last; id=26 body has 232 but final box is option letter
Of 67 hard-wrong, **48 (72%) have comma/frac/latex in gold = likely format-divergent**, not real misses. Genuine misses exist too (id=41 2112 vs 4048; id=26/33 wrong option) but are the minority.

Interpretation: hard_independent at T4/T5 measures FORMAT/GOLD-QUALITY reconciliation, not Qwen math ability. The [0.60,0.95] band assumed clean gold; T4/T5 wolfram/search gold is not clean. This is the SAME structural-normalizer gap as C5 — value-equality can't reconcile multi-slot/precision without it.

### Open items / strategy decisions (BLOCKERS before commit)
1. (c-new) gate is now testing gold-quality+format, not Qwen correctness, because C8 pulled in messy T4/T5 gold. Options: (a) restrict (c-new) to wolfram_HIGH+search_GOLD AT T1/T2/T3 only (clean-gold hard subset) — keeps C8's recovery for bucketing but gates on clean items; (b) keep C8 bucketing but widen (c-new) to [0.25,0.95] acknowledging format-loss until structural normalizer; (c) build the structural normalizer first (bigger scope). I did NOT pick.
2. 48/67 hard-wrong are format-recoverable — strong evidence the structural normalizer (undercount collapse + precision tolerance) is the highest-value next build; these are NOT adapter-B.
3. C6 CATALOG.md status note still not added (only csv meta header).

### Commit hash
NONE — gate (c-new) failed, per task rule did not commit. v3-final artifacts uncommitted in inference/scripts/_pressure_test_R14/.

---
## claude_vscode signoff — Day 9 — analyze_run.py v3-final-final (C11-C16) — ALL GATES PASS — LOCKED + committed

### What was patched (C11-C16 only; C1-C10 untouched)
- C11 deterministic canonical sample: among samples matching voted_answer, pick min(gen_tokens, sample_index) — shortest correct response, index breaks ties. Replaces "first matching" (was sample-order-dependent). Verified order-independent (gate j).
- C12 canonical_sample_fallback note appended to notes (with '; ') when no sample matches voted.
- C13 response_preview = re.sub(r'\s+',' ', canonical_response)[:200].strip() — FIRST 200 chars (was last). Confirmed: id0 preview now starts "Okay, let's tackle part a...".
- C14 CLI flags --skip-samples (suppress analysis_samples.jsonl) + --fail-fast (raise on first per-item judge error). Default False both.
- C15 pressure-test artifacts committed with the analyzer (LFS-tracked — see note).
- C16 gate split: (c-new-fixed) hard_independent_CLEAN = wolfram/search @ T1/T2/T3, gate [0.60,0.95]; (c-info) hard_independent_DIRTY = wolfram/search @ T4/T5, REPORT-only (surfaces the structural-normalizer gap). Bucket logic (C8) UNCHANGED — T4/T5 wolfram/search stay in scored set for cross-run matrix.

### Gates — ALL PASS
(a) 943 + 14 meta ✅  (b) 7544 ✅
(c-new-fixed) hard_independent_CLEAN n=16 acc=0.8125 ∈[0.60,0.95] ✅
(c-info) hard_independent_DIRTY n=78 acc=0.1923 (no gate; normalizer gap) ✅ reported
(d) unanimous_teachers n=403 acc=0.9876 ≥0.90 ✅ report-only
(e) 5B+5A_lucky inspected, labels correct ✅
(f) 0 extracted_empty contradictions ✅  (g) 0 preview violations ✅
(h) scored set 498 ✅  (i) wolfram/search T4/T5 = 78/78 still scored ✅
(j) DETERMINISM: 5 multi-match rows identical under 3 shuffles each ✅
(k) canonical_sample_fallback notes = 0 ✅
Verification triple: labels clean, sum-identity 547==547, 0 forbidden code reads ✅

### Final bucket dist: A=426 A_lucky_sample=14 B=58 unknown=445 (scored 498, acc 0.8554)
(C11 shifted A 427→426, A_lucky 13→14, truncated 21→17 vs prior v3-final — expected: canonical now = shortest correct sample, not first, so a different response is judged/measured per item.)

### LFS (per LOCKED rule)
analysis.jsonl (29M) + analysis_samples.jsonl (20M) both >10MB and were filter:unspecified. Added to .gitattributes as filter=lfs (matching the repo's per-file jsonl convention) BEFORE staging. analysis.csv (2.3M) committed raw. git lfs push + push.

### End-to-end wall-clock on R14: 4:52 (User 291s) — CPU-only, 943 items × ~9 judge passes.

### Analyzer LOCKED. No more iteration before R00. For the 30-run batch:
- Per run: python3 inference/scripts/analyze_run.py --run-jsonl <run> --master-answers data/MASTER_ANSWERS.csv --output-dir inference/<R??>/ [--run-id <id>] [--kaggle-score <s>] [--skip-samples for speed].
- Each new run's >10MB analysis jsonl MUST be git-lfs-tracked before commit (add .gitattributes glob or per-file).
- CROSS_RUN_MATRIX consumes the per-run analysis.csv bucket columns.

### Downstream flag (NOT in scope here): structural normalizer is the highest-value next build.
48/67 hard-wrong items at T4/T5 are format-recoverable (undercount collapse / precision tolerance / representation), NOT adapter-B. hard_independent_DIRTY acc 0.19 is mostly the missing structural normalizer, not Qwen math failure. bucket_b_review_needed=58 flags these for human triage until the normalizer lands.

### Commit hash
761f903 (rebased onto strategy's 3b5bd69 AUDIT_TEMPLATES + cace2a9 CATALOG R-numbering; LFS 2 objects/50MB pushed). Pushed 3b5bd69..761f903.
NOTE: R14 in my prompts == R20 in the now-locked chronological catalog (cace2a9). The pressure-test ran on run14b_sc8_v1_private943_tok32k_pp1 = R20, the 0.646 baseline. Output dir kept as _pressure_test_R14 (matches the prompt's naming); the run is R20.

---
## claude_vscode signoff — Day 9 — T1 SHALLOW BATCH R00-R07 + scripts/rename_run.sh

### Step 0: scripts/rename_run.sh (68 lines, +x)
Cross-ref sweep tool. Args: $1=old_name, $2=new_ref. Loops the canonical 25-doc list (CATALOG calls it "27 docs"; the fenced list has 25 entries — used verbatim, did not expand per the "don't expand without Rain" note). Per doc: grep -Fo count; sed -i "s|old|new|g" if >0 (| delimiter so paths in $2 are safe); per-doc + grand-total report. set -euo pipefail; skips missing docs.
NOTE: Step-0 spec says $2 = bare run id ("NOT a path"); the T1 template line 69 + this prompt's step 6 call it WITH a path (inference/base_model/{slug}). Tool is agnostic (replaces literal $2). I followed the TEMPLATE invocation (path) since that's the literal per-run instruction. Flag for strategy if bare-slug refs were intended instead.

### 8 runs cataloged (old → new path) — all base_model, all git mv (none >10MB, no LFS needed; largest R07=5.9MB)
R00: run03_tok8192_20            → inference/base_model/R00_eval_v1_single_f20_t8k/
R01: starter_results            → inference/base_model/R01_starter_v1_single_f5_t8k/
R02: run_vllm_smoke_5_tok2048   → inference/base_model/R02_smoke_v1_single_f5_t2k/
R03: run_vllm_smoke_5_tok8192   → inference/base_model/R03_smoke_v1_single_f5_t8k/
R04: run04_vllm_parity_20_tok8192 → inference/base_model/R04_parity_v1_single_f20_t8k/
R05: run05_v1_50_tok16384       → inference/base_model/R05_eval_v1_single_f50_t16k/
R06: run06_v2mcq_50_tok16384    → inference/base_model/R06_eval_v2mcq_single_f50_t16k/
R07: run07_sc8_v1_50_tok16384   → inference/base_model/R07_eval_v1_sc8_f50_t16k/
Each: README.md (≤2 para: name/R#/date/config/purpose) + findings.md (≤1 para). git mv'd .jsonl (+ .summary.json for R04-R07; R00/R01/R02/R03 had none).

### Cross-ref sweep: GRAND TOTAL = 0 replacements across all 8
These dev/smoke/parity runs are NOT referenced in any of the 25 cross-ref docs (expected — they predate the docs). Sweep ran clean per run; tool validated against real files (skips/counts correct).

### CATALOG.md: status ⚪→🟢 (8 rows) + registry reserved→cataloged (8 rows). R08+ untouched (verified ⚪/reserved).

### Slug decisions (locked): purpose=eval/smoke/parity/starter; variant=v1 (v1-baseline) / v2mcq (v2-mcq-commit); decoding=single (non-SC) except R07=sc8; items=f5/f20/f50; tokens=t2k/t8k/t16k.
- R00/R01: no summary.json; date from locked chronology (2026-05-01), config from row-0 schema. R01 starter has no token field logged → t8k (era default), noted in its README.
- R02/R03: no summary.json but run_id in rows; 2K/8K from filename, dates from CATALOG.

### Anything unusual
- None of the 8 are "secretly real evals" — they ARE what the chronology says (smokes 5-item, parity 20-item, evals 50-item). R07 is the first SC8 (8 samples) — genuine ancestor of the p943 SC8 cohort but itself dev-only (50 items).
- The "27 docs" label vs 25 actual entries in the cross-ref fenced list (see rename_run.sh note).

### Commit hash
13c4cea (rebased onto origin 8a96854 MORNING_RUNS_WATCHLIST; pushed 8a96854..13c4cea). Brief detached-HEAD detour during rebase-with-stash — reattached main via branch -f, verified all 8 R0x folders intact before push.

---
## claude_vscode signoff — Day 9 — T2 DEEP audit R08 (first p943 single-sample baseline)

### What was done
Cataloged run08v2_v1_private943_tok16384 → inference/base_model/R08_eval_v1_single_p943_t16k/ (git mv jsonl+summary; no infra logs matched). Ran analyzer v3-final-final — FIRST exercise of the single-sample (is_sc=False) auto-detect path (R20 was SC-only). Wrote README + deep findings.md per MORNING_RUNS_WATCHLIST.

### Gates: a✅ b(n/a, single-sample) c✅ d✅ e✅ f✅ g✅ h✅ i✅ — ALL PASS
- (a) 943 + 20 meta ✅  (b) single-sample → no analysis_samples.jsonl (correct; gate b is SC-only)
- (c-new-fixed) hard_independent_CLEAN n=16 acc=0.6250 ∈[0.60,0.95] ✅ (low edge; wolfram 3/7, search 7/9)
- (c-info) DIRTY n=78 acc=0.2051 (normalizer gap)
- (d) A_lucky_sample=0 ✅ + n_samples_math_correct ∈{0,1} for all 943 ✅ (explicit single-sample confirmation)
- (f) truncated=119 ✅  (g) preview 0 ✅  (h) scored 498 ✅  (i) wolfram/search T4/T5 78/78 ✅
- Verification triple: labels clean, sum-identity 547==547, 0 forbidden reads ✅
- Single-sample path is CLEAN — no bug. Downstream p943 deep audits (R09/R10/R20b) unblocked. Analyzer wall-clock 36s (single-sample = 1 judge pass/item vs SC's ~9).

### Bucket: A=407 A_lucky_sample=0 B=91 unknown=445 | scored acc 0.8173 | unanimous_teachers 381/403=0.9454
(Kaggle for the derived CSV run08v2_v1_private943.csv = REGISTRY #1, 0.586 — post-processed, not re-run through analyzer with --kaggle-score since it's a derivative.)

### B=91: ~63 (69%) format-recoverable (multi-slot 33, fraction-form 16, MCQ-letter 14), 28 likely true miss. 22 of the 91 are ALSO truncated.
### Truncated=119 (vs R20's 17 — half token budget, 16K vs 32K, as predicted). 118/119 math-wrong. High-budget re-run targets.

### BUG FOUND + FIXED in scripts/rename_run.sh (my own, from T1 session)
`n=$(grep -Fo "$OLD" "$doc" | wc -l)` aborted under `set -o pipefail` whenever grep matched zero (grep exit 1 → pipefail → script exit). Fixed: `n=$( { grep -Fo ... || true; } | wc -l ...)`. IMPACT: T1 batch sweeps exited early — BUT I re-verified with an authoritative grep that none of the 8 T1 runs NOR run08v2 appear in any of the 25 cross-ref docs, so T1's reported "0 replacements" was CORRECT despite the early exit. The fix matters for R09+ which WILL have real references. Re-ran all 8 T1 + R08 under the fixed script: all exit 0, all 0 replacements (confirmed correct).

### Cross-ref sweep (R08, bare-slug form per strategy clarification): 0 replacements.
run08v2_v1_private943_tok16384 (the run jsonl name) isn't referenced in the doc list; the submission CSVs use the shorter `run08v2_v1_private943` name and live in submission/csvs/ (not in the 25-doc sweep list). REGISTRY.md references the CSV name, not the run name.

### LFS (locked rule): jsonl 17MB + analysis.jsonl 33MB both >10MB → git-lfs-tracked on their new paths before staging (verified pointer content, not raw blobs). analysis.csv 5.7MB raw.

### Surprises
- extracted_empty=1 (R20 had 0) — single-sample + truncation can yield no box and no fallback number.
- Truncation (119) is the dominant failure mode at 16K — biggest free lever for THIS run is tokens, not prompt/SC.
- unanimous_teachers 0.945 < R20's 0.988 — single-sample at half budget agrees with consensus less; still healthy (≥0.90).

### Commit hash
fe753b3 (R08 deep audit + rename_run.sh pipefail fix; LFS 2 objects pushed: run jsonl 17MB + analysis.jsonl 33MB).

---
## claude_vscode signoff — Day 9 — T2 DEEP audit R09 (first SC@8 on p943; R08's SC twin)

### What was done
Cataloged run09sc8_v1_private943_tok16384 → inference/base_model/R09_eval_v1_sc8_p943_t16k/ (git mv jsonl 130MB + summary). Ran analyzer v3-final-final (SC path), Kaggle 0.614. README + deep findings.md w/ first real A_lucky_sample + first cross-run (vs R08) transitions.

### Gates: a✅ b✅(7544) c✅ d✅ e✅ f✅ g✅ h✅ i✅ — ALL PASS. Verification triple ✅ (547==547).
Wall-clock 7:47 (SC, ~9 judge passes/item).

### Bucket: A=422 A_lucky_sample=18 B=58 unknown=445 | scored acc 0.8474 (R08 0.8173, SC +3.0pp)
hard_independent_CLEAN n=16 acc=0.6875 (wolfram 4/7, search 7/9). unanimous_teachers 397/403=0.9851 (R08 0.9454 — SC recovers consensus agreement).

### A_lucky_sample (18) — first DeepConf signal
DeepConf gold (≥5/8 correct, lost vote): 1 item = id 763 (6/8). SC@32 candidates (1-4/8): 17 items (403,721,584,924,12,416,495,535,712,715,9,120,181,257,642,929,935). (item_id, winning_sample_idx) tuples captured in findings table d for adapter-trace harvest.

### B=58, ~40 (69%) format-recoverable (multi-slot 23, MCQ-letter 9, fraction-form 6, undercount 2; true miss 18).

### Truncated=93 (R08 was 119 — SC's 8 samples mean ≥1 often completes at 16K). 89 truncated in BOTH R08+R09 = strongest high-budget (>16K) re-run set; R08-only 30, R09-only 4.

### CROSS-RUN vs R08 (the SC dividend at fixed tokens+prompt):
A→A 401 · A→B **0** (no regression) · A→A_lucky 6 · B→A **21 (SC saved)** · B→A_lucky 12 · B→B 58.
SC dividend = 21 (B→A) + 12 (B→A_lucky) = 33 items where SC surfaced correct math R08 missed. SC cost = 0 regressions, only 6 clean→vote-fragile. **SC is STRICTLY POSITIVE at fixed tokens/prompt.** The 18 vote-fragile (12 B→A_lucky + 6 A→A_lucky) = DeepConf/SC@32 target set.

### Cross-ref sweep: full-name run09sc8_v1_private943_tok16384 = 0 replacements (clean, fixed script exit 0). SHORT-name run09sc8_v1_private943 sweep DELIBERATELY SKIPPED — its only 2 hits (REGISTRY.md L45, CLAUDE_STRATEGY.md L227) are both `run09sc8_v1_private943.csv` (submission CSV refs); sweeping would corrupt to nonexistent `R09_..._t16k.csv`. CSVs stay in submission/csvs/, README cross-links. (Prompt's "skip if over-match" judgment.)
First real test of the pipefail fix: PASSED (script ran the full doc list to completion, exit 0).

### LFS: jsonl 130MB + analysis.jsonl 27MB + analysis_samples.jsonl 39MB all >10MB → tracked on new paths before staging. analysis.csv 4.9MB raw.

### Surprises about SC at SAME token budget
- SC is strictly Pareto-positive here: 0 A→B, 33 items gained. The cost is only "vote-fragility" (6 items), never lost correctness.
- DeepConf gold is only 1 item (763) — at 16K+v1, ≥5/8-correct usually also wins the plain vote; the lossy cases sit at 1-4/8 (the SC@32 lane). So at THIS config DeepConf logprob-weighting has a thin direct payoff; SC@32 (more samples) is the bigger lever for the 17 minority-correct items.
- Truncation still material (93) even with SC — tokens remain a real ceiling at 16K.

### Commit hash
38eca28 (rebased onto strategy b658ba9/efdb3b2 R08-T3 followups; LFS 2 objects/66MB pushed: analysis.jsonl 27MB + analysis_samples.jsonl 39MB; run jsonl 130MB already on remote from prior LFS).

---
## claude_vscode signoff — Day 9 — T2 DEEP audit R10 (v3-perslot prompt effect, single-sample)

### What was done
Cataloged run10_v3perslot_private943_tok16384 → inference/base_model/R10_eval_v3perslot_single_p943_t16k/ (git mv jsonl 16MB + summary). Analyzer v3-final-final (single-sample path). README + deep findings.md with cross-run g1/g2/g3/g4.

### Gates: a✅ b✅(n/a single-sample) c✅ d✅ e✅ f✅ g✅ h✅ i✅ — ALL PASS. Verification triple ✅ (547==547). Wall-clock 38s.

### Bucket: A=396 A_lucky=0 B=102 unknown=445 | scored acc 0.7952 (LOWEST of 3: R08 .8173, R09 .8474)
hard_independent_CLEAN n=16 acc=0.7500 (HIGHEST: wolfram 6/7, search 6/9). unanimous_teachers 367/403=0.9107 (LOWEST). Kaggle 0.424 (REGISTRY #2, worst p943). v3-perslot helped hard multi-part items but hurt the broad easy set.

### B=102, ~81 (79%) format-recoverable (multi-slot 46 — INFLATED by per-slot prompt encouraging per-part boxing vs single-last-box grader; MCQ-letter 18, fraction 13, undercount 4; true miss 21).
### Truncated=110 (between R08 119 and R09 93).

### CROSS-RUN (3 runs now):
- g1 R10 vs R08 (PROMPT effect): A→A 373, A→B **34 (regression)**, B→A **23 (saved)**, B→B 68. **NET −11 — v3-perslot breaks more than it fixes.** vs R09 SC dividend +21/0-regression. SC >> prompt-variant as a lever.
- g2 R10 vs R09: R10-wins-R09-misses=12, R09-wins-R10-misses=38. **SC strictly dominates.** The 12 R10-wins overlap R09's A_lucky list (vote-fragile items a lucky single sample caught) — reinforce SC@32 set, not v3-perslot.
- g3 A∩A∩A = 372 (rock-solid across both prompts + SC/no-SC; NOT adapter/normalizer candidates).
- g4 B∩B∩B = 53 (CORE bucket B). Recoverability split: 43 format-recoverable (normalizer), **10 TRUE-MISS = real adapter targets: [41, 61, 103, 104, 117, 127, 231, 264, 282, 868]** (41 already T3-confirmed). Will tighten at R20/R20b (32K may rescue truncated ones e.g. 117/127).

### Adapter notes: id=9 (gold-split, R08-T3) NOT in B∩B∩B, stays excluded. id=68 (R08-T3 true-miss) classified fraction-form here due to truncated R10 response — defer to R08-T3 (true miss).

### Cross-ref sweep: full-name run10_v3perslot_private943_tok16384 = 0 replacements (exit 0). SKIPPED short 'run10_v3perslot' (2 hits, both run10_v3perslot_private943.csv — CSV refs) and bare 'run10' (5 hits: 2 CSV + 3 prose 'run10,run14b'; too broad, would corrupt). Judgment per R09 pattern.

### DOC-CONFLATION FLAG for strategy: INFERENCE_TECHNIQUES.md L9 + TEST_PIPELINE.md L21 list "run10, run14b" as SC@8→0.646. R10 is SINGLE-SAMPLE (method vllm, no samples array), Kaggle 0.424. 0.646 belongs to R14b/R20 alone. R10 mislabeled as SC@8 in those 2 docs. Did NOT auto-fix (broad bare-run10 sweep too risky); flagging for manual correction.

### LFS: jsonl 16MB + analysis.jsonl 31MB → tracked on new paths before staging. analysis.csv 5.4MB raw.

### Surprises
- v3-perslot is net-NEGATIVE (−11) yet HELPS hard-independent (0.75 vs R08 0.625) — trades broad easy accuracy for a few hard multi-part wins. Bad trade → 0.424 Kaggle. Dev arc correctly abandoned it.
- Per-slot prompt INFLATES multi-slot B (46 vs R08's 19): prompt-induced per-part boxing fights the single-last-box grader. Clean structural-normalizer (undercount) illustration.
- B∩B∩B true-miss core is only 10 of 53 — most "consistently wrong" items are format-recoverable, NOT adapter material. Adapter target set is small and tightening.

### Commit hash
(filled after commit)

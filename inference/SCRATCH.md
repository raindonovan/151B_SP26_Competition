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
304517e (R10 deep audit; LFS 2 objects/49MB: run jsonl 16MB + analysis.jsonl 31MB pushed). Pushed 51c6117..304517e.

---
## claude_vscode signoff — Day 9 — T2 DEEP audit R20 (the 0.646 best-inference baseline; SC@8 32K; completes 4-way matrix)

### What was done
Cataloged run14b_sc8_v1_private943_tok32k_pp1 → inference/base_model/R20_eval_v1_sc8_p943_t32k_pp1/ (git mv jsonl 150MB + summary + exact-match infra log). Analyzer v3-final-final, Kaggle 0.646. Numbers match my lock-session pressure-test exactly (deterministic). README + deep findings.md (token-effect vs R09, 4-way intersection, final adapter seed).

### Gates: a✅ b✅(7544) c✅ d✅ e✅ f✅ g✅ h✅ i✅ — ALL PASS. Verification triple ✅ (547==547). Wall-clock 4:41.

### Bucket: A=426 A_lucky=14 B=58 unknown=445 | scored acc 0.8554 (HIGHEST: R08 .8173 R09 .8474 R10 .7952)
hard_independent_CLEAN n=16 acc=0.8125 (HIGHEST; wolfram 6/7 search 7/9; trend .625→.6875→.75→.8125). unanimous_teachers 398/403=0.9876 (HIGHEST).

### (d) A_lucky=14, DeepConf territory GREW: ≥5/8 = 3 items (296 5/8, 839 6/8, 302 7/8) vs R09's 1. SC@32 (1-4/8)=11. (302/839 voted==gold by value, format-adjacent; 296 clean multi-slot-order.) DeepConf slightly stronger morning lever at 32K, pool still small.

### (f) TRUNCATION — the token headline: R20 trunc=17 (R08 119, R09 93). 32K RESCUED 72 of the 89 always-truncated-at-16K. Only 17 still truncate → want >32K (65536): [93,112,161,204,229,275,308,312,376,383,445,498,586,652,724,799,809]. Prediction check: id=117 RESCUED at 32K (now A correct) ✓; id=127 NOT rescued (true miss).

### B=58, ~46 (79%) format-recoverable. id=41 now converges to wrong number 4048 (was rambling non-answer at 16K) — clearer true-miss.

### (g) CROSS-RUN R09→R20 (TOKEN effect, fixed SC/v1): A→A 417, A→B 1, B→A 5, B→A_lucky 2, B→B 51, A_lucky→B 6. Token dividend = 7. LEVER RANKING at fixed v1: SC +33 ≫ tokens +7 ≫ prompt-variant −11.

### (h) 4-WAY R08∩R09∩R10∩R20:
- A∩A∩A∩A = 371 strict (rock-solid, NOT adapter/normalizer candidates; ~75% of scored set).
- B∩B∩B∩B = 48 (was 53 triple-core; 117 rescued at 32K + a few →A_lucky).
- 9 of 10 R8∩R9∩R10 true-miss seed survive R20; id=117 rescued (predicted).
- B∩B∩B∩B recoverability: 37 format-recoverable (normalizer), **11 true-miss = FINAL ADAPTER TARGET SEED: [41, 61, 103, 104, 127, 167, 231, 264, 282, 345, 591]**. Heuristic-classified — recommend T3 confirm before adapter training (esp. 167/345/591, newly added vs R10 seed). id=9 correctly excluded (gold-split, R08-T3).

### Cross-ref sweep: full-name run14b_sc8_v1_private943_tok32k_pp1 = 0 replacements (exit 0). Bare 'run14b' SKIPPED — ~40 hits across 18 docs (CSV names, R20b v3filtered, the 0.745-feeder refs); sweeping would corrupt critical references. Per prompt's explicit warning.

### Artifact moves: jsonl+summary git mv; ALSO moved infrastructure/logs/run14b_sc8_v1_private943_tok32k_pp1.log into the R20 folder (per CATALOG absorb-list; updated that list entry to 'MOVED ... done'). Left run14b_launcher.sh / _smoke / _autorestart / _20260518 logs in infrastructure/ (tooling/other-run, not this run's artifact).

### LFS: jsonl 150MB + analysis.jsonl 30MB + analysis_samples.jsonl 20MB → tracked on new paths before staging. analysis.csv 2.3MB raw.

### Surprises about the 0.646 baseline
- Tokens are SECOND-ORDER: 16K→32K bought only +7 SCORED items vs SC's +33. R20's edge over R09 (0.646 vs 0.614 Kaggle) comes mostly from the 72 truncation-rescues landing on the FULL set (many in unknown/T4-T5, off the hard-gate), i.e. 32K saves long-derivation items 16K cut off.
- The 0.745 Pick A sits on a baseline with 0.8554 independent-gold scored accuracy — strong clean floor; overlays add teacher-corroborated items on top.
- Final adapter seed is only ~11 items — the "wrong-on-math across EVERY lever (single/SC × v1/v3perslot × 16K/32K)" set is tiny. Most failures are format (normalizer) or token (high-budget), not capability.

### Housekeeping note (NOT acted on, out of scope): inference/scripts/_pressure_test_R14/ (the lock-session pressure-test on this same run, committed at 761f903) is now redundant with R20's canonical analysis/. Candidate for cleanup post-deadline — flagging, not removing.

### Commit hash
b3901c4 (R20 deep audit; rebased onto strategy 43e14bd/2f50042 R10-T3 followups — which PREDICTED id=117 rescued at R20 32K; my R20 audit CONFIRMS it ✓). LFS run jsonl 150MB already remote + analysis.jsonl 30MB + samples 20MB pushed. Pushed 43e14bd..b3901c4.

---
## claude_vscode signoff — Day 9 — T2 DEEP audit R20b (v3 sample-filter; FINAL of 5; cohort COMPLETE)

### What was done
Cataloged run14b_sc8_v1_private943_tok32k_pp1_v3filtered → inference/base_model/R20b_eval_v1_sc8_p943_t32k_v3filt/ (git mv jsonl 155MB; no summary.json). Schema was raw-SC-compatible (full samples array + voted_answer + per-sample shape_rejected + v3_samples_kept/rejected) → analyzer SC path ran directly, NO prep step needed. Kaggle 0.646 (REGISTRY #14).

### Gates: a✅ b✅(7544) c✅ d✅ e✅ f✅(flagged) g✅ h✅ i✅ — ALL PASS. Verification triple ✅ (547==547). 4:42.

### Bucket: A=430 A_lucky=10 B=58 unknown=445 | scored acc 0.8635 (highest LOCAL; R20 .8554)
hard_independent_CLEAN n=16 acc=0.8125 (IDENTICAL to R20; filter didn't touch hard set). unanimous_teachers 401/403=0.9950 (highest — where the filter's local gain lands).

### Filter does real work: rejected ≥1 sample on 142 items, changed voted_answer on 55 vs R20. NOT a no-op.

### (f) truncated=16 vs R20's 17 — FLAGGED: filter swapped one item's canonical sample (rejected the truncated one R20 voted; non-truncated won). Trivial.

### (g) CROSS-RUN R20→R20b (FILTER effect) — LOAD-BEARING:
A→A 426, **A_lucky→A 4**, A_lucky→A_lucky 10, B→B 58. **B→A=0, B→A_lucky=0, A→B=0, A_lucky→B=0.**
**FILTER DIVIDEND = 0.** Filter's ONLY gold-scored effect is A_lucky→A (cleans 4 already-correct vote-fragile items). Moves NOTHING wrong→right. Local +0.8pp is pure vote-cleanup; **Kaggle FLAT 0.646==R20**. 
**VERDICT: v3 shape-filter is NOT a Pick-B improvement. DROP from morning planning.** Cleanest possible "dead lever" signal — can't help Kaggle because it changes no item's correctness.

### (h) 5-WAY R08∩R09∩R10∩R20∩R20b — COHORT COMPLETE:
- A∩∩∩∩∩ = 371 strict (373 w/ lucky) — definitive rock-solid; NOT adapter/normalizer.
- B∩∩∩∩∩ = 48 — identical to R20's 4-way B∩ (filter changed nothing in wrong set).
- ALL 11 R20 true-miss seed survive R20b, INCLUDING heuristic-newcomers 167/345/591 (all still B∩∩∩∩∩).
- **LOCKED FINAL ADAPTER TARGET SEED (true-miss in B∩∩∩∩∩): [41, 61, 103, 104, 127, 167, 231, 264, 282, 345, 591]** (11). Other 37 of 48 = format-recoverable (normalizer, NOT adapter). Recommend T3 confirm the 11 (41/282 already T3-done; verify newcomers 167/345/591). id=9 correctly excluded; id=117 correctly removed at R20 (32K rescue).

### FINAL LEVER RANKING (at fixed v1, full cohort): SC +33 ≫ tokens +7 ≫ filter 0 ≫ prompt-variant −11.
SC is the dominant Pick-B lever. Tokens second. v3 shape-filter and v3-perslot prompt are both non-levers (0 / negative).

### Cross-ref sweep: full-name run14b_sc8_v1_private943_tok32k_pp1_v3filtered = 0 replacements (exit 0). SKIPPED 'run14b_v3filtered'/'v3filtered' (7 hits across 5 docs, all the CSV name run14b_v3filtered.csv — would corrupt). Per R20 pattern.

### LFS: jsonl 155MB + analysis.jsonl 30MB + analysis_samples.jsonl 20MB → tracked before staging. analysis.csv 2.2MB raw.

### ALL 5 DEEP-COHORT RUNS NOW CATALOGED (R08 R09 R10 R20 R20b 🟢). CROSS_RUN_MATRIX inputs complete. Strategy can build the matrix + finalize Pick B / adapter seed.

### Surprises
- The filter is the cleanest "dead lever" in the cohort: 55 voted-answer changes, but every gold-scored one is A_lucky→A (already correct). Zero correctness change → Kaggle flat by construction.
- Cohort plateaued: hard_clean 0.8125 (R20=R20b), B∩=48, adapter seed=11, rock-solid=371 — all LOCKED. No remaining p943 lever in this cohort moves them; the morning levers (DeepConf/SC@32/NoThinking/high-budget) are the only untried ones.

### Commit hash
59cd151 (R20b deep audit; rebased onto strategy 904c818 R20-T3 YELLOW + 2d17481 morning candidates). LFS run jsonl 155MB already remote + analysis.jsonl 31MB + samples 20MB pushed. Pushed 904c818..59cd151.

### POST-PUSH CORRECTION (R20-T3 landed during my session): adapter seed 11→8. ChatGPT R20-T3 reclassified 167 (option-mapping, like id=9), 345 (precision/exact-form, like id=89), 591 (undercount, like id=12) as FORMAT-RECOVERABLE not true-miss — exactly the newcomers I flagged for T3 to verify. **LOCKED FINAL ADAPTER SEED = 8: [41, 61, 103, 104, 127, 231, 264, 282].** Also 302/839 are duplicate-option overcounts, not clean DeepConf. Applied the correction to R20b findings.md (appended CORRECTION section). B∩∩∩∩∩=48 and A∩∩∩∩∩=371 unchanged; only the true-miss split (11→8) within the 48 shifts. Filter-dividend=0 and lever ranking unaffected.

---
## claude_vscode signoff — Day 9 — T1.5 HYBRID audit NoThinking-943 (NT, out-of-cohort) — VERDICT: ELEVATE

### What was done
Cataloged nothinking_full_943_20260527T000129Z (NoThinking SC@8 943, prefill bypass, May 27, untouched 3 days) → inference/base_model/NT_eval_nothinking_sc8_p943_t8k/. NOT R-series (NT prefix). git mv from hybrid/tnr-B/. Analyzer v3-final-final + focused cross-run vs R20.

### SCHEMA MISMATCH → prep adapter (analyzer NOT modified, per instruction)
NoThinking jsonl schema differs: `samples`=list of STRINGS (not dicts), per-sample data in parallel arrays (sample_extracted, sample_n_output_tokens), no is_mcq/options/max_new_tokens/hit_token_cap. Analyzer crashed at line 267 (`s.get` on str) — CONFIRMED, reported, did NOT touch analyzer. Wrote one-off `inference/scripts/prep_nothinking_for_analyzer.py` restructuring → expected SC schema (truncation synth from n_tokens>=8192-10; is_mcq from MASTER; options=None handled by auto_judge.is_equal as in R08/R10). Analyzer ran on the _ADAPTED.jsonl. Both raw+adapted kept in folder.

### Gates: a✅ b✅(7544) c✅ d✅ e✅ f✅ g✅ h✅ i✅ — ALL PASS (on adapted). Verification triple ✅ (547==547). 6:25.

### Standalone NoThinking is WEAKER (expected): A=363 A_lucky=66 B=69 unknown=445, scored acc 0.7289 (R20 0.8554). unanimous_teachers 0.8089 (R20 0.988) — the gap is easy-consensus items. hard_clean 0.75 (wolfram 5/7, search 7/9). DIRTY 0.32 (HIGHER than R20 0.19 — NoThinking better on messy T4/T5). Truncated=9 (R20 17, no reasoning phase). A_lucky=66 (R20 14) — diversity engine.

### CROSS-RUN vs R20 (LOAD-BEARING):
- e1 R20→NT: A→A 348, A→A_lucky 50, A→B 28; A_lucky→A 7; B→A 8, B→A_lucky 10, B→B 40.
- e2 UNIQUE-CORRECT (NT.A, R20 not-A) = **15** ≥10 ✓: [5,181,257,282,345,474,578,584,633,642,712,715,763,868,917]. Genuine: ~13 multi-slot wins where R20's vote collapsed to one slot, PLUS id=282 (NT e^2==gold, R20 e^2,-e^2 — NoThinking AVOIDED the spurious extra-root that made 282 an adapter-seed item!) + id=345 (NT exact -5/6,5/6 vs R20 decimal).
- e3 R20 wins NT misses (R20.A∩NT.B) = 28 — NT broadly weaker; consensus join must weight R20 PRIMARY.
- e4 both-B = 40 (NT recovers 8 of R20's 48 cross-lever-B incl 282/345/474/868; adds no new permanent misses).
- e5 agreement = 335/498 = 67.3% → 32.7% ensemble headroom.

### f orthogonality (5 both-B): 4/5 DIFFERENT wrong answers (only id=12 undercount shared). 41: NT 2024 vs R20 4048 (both wrong, opposite directions). GENUINELY ORTHOGONAL, not a weaker copy.

### VERDICT: **ELEVATE** — NoThinking ∪ R20 consensus = Pick-B candidate (ZERO GPU).
15 unique-correct ≥10 + orthogonal failures + 67% agreement. Recommend T3 verify the 15 before building the join CSV. JOIN DESIGN: R20 primary; take NT only where R20∈B AND NT∈A with NT sample agreement (NOT equal-weight union — would import the 28 R20-wins-NT-misses). It's the ONLY Pick-B lever in the whole audit that ADDS correctness over R20 (SC/tokens/filter were R20-internal aggregation; NoThinking brings orthogonal solves). Top picks for join: 282 (rescues adapter-seed), 345 (format), + 13 multi-slot.

### Surprises: NoThinking does BETTER on hard/dirty (0.32 vs 0.19) + WORSE on easy (0.81 vs 0.99) — skipping reasoning hurts straightforward items but avoids over-thinking spirals (incl the 282 extra-root). A_lucky=66 = ideal raw material for DeepConf/SC@32-on-NoThinking ensemble.

### LFS: raw jsonl 45MB + adapted 39MB → LFS. analysis.jsonl 4.7MB + samples 9.7MB are <10MB (NoThinking = no traces = small) → committed RAW. analysis.csv 0.97MB raw.

### Cross-ref sweep: full timestamp name = 0 (exit 0). Bare 'nothinking'/'nothinking_full_943' SKIPPED (appears in data/candidates_nothinking_breakdown.md as analysis prose; too broad; the candidates file is a different artifact). 98-probe + targeted_rescue variants left in hybrid/tnr-B/ (deferred per instruction).

### Commit hash
c4d07b6 (NT T1.5 audit + prep_nothinking_for_analyzer.py; rebased onto strategy 2c7089d R20b-T3 GREEN). LFS 2 run jsonls/86MB pushed; analysis.jsonl+samples committed RAW (<10MB, no traces). Pushed 2c7089d..c4d07b6.

---
## claude_vscode signoff — Day 9 — T2 NoThinking probe98 audit — VERDICT: YELLOW

### What I tried
- Located the deferred probe artifacts outside `inference/base_model/` by following the NT-943 README back to `inference/results/hybrid/tnr-B/`.
- Reused the existing NoThinking adapter/analyzer path instead of hand-scoring the probe.
- Compared probe98 directly against NT-943 on the exact same 98 ids, then split by `no_box`, `weak_ab`, and `t1_control`.

### What I did
- Verified `inference/results/hybrid/tnr-B/nothinking_probe98_20260526T065456Z.jsonl` matches `data/candidates_nothinking_98.txt` exactly (98/98 ids, no extras).
- Fixed `inference/scripts/prep_nothinking_for_analyzer.py` so `--run-id` is configurable; validated it on probe98.
- Generated `inference/base_model/NT_probe98_eval_nothinking_sc8_f98_t8k/nothinking_probe98_ADAPTED.jsonl` plus analyzer artifacts in that folder.
- Wrote README/findings for the new catalog folder and updated `inference/runs/CATALOG.md` to identify the probe as the source of the 98-id candidate files.

### What worked
- Provenance is now locked: the 98-id candidate files are analysis of `nothinking_probe98_20260526T065456Z`.
- The old NoThinking adapter path is reusable after the run-id fix; analyzer ran cleanly on the probe with no schema edits to the analyzer.
- The audit cleanly distinguishes lineage from stability: probe98 is same family/config path, but behaviorally noisy.

### What didn't work
- probe98 is NOT a stable mirror of NT-943: only `28/98` exact voted-answer matches, `14/98` exact sample-extracted multiset matches.
- On the scored subset, NT-943 is `37/44` voted-correct while probe98 is only `27/44`.
- The probe overlaps only 2 of the 15 NT rescue ids (`5`, `584`) and fails both, so it cannot validate the rescue lever.

### What's left
- Commit and push this catalog/audit work.
- If anyone wants a stronger early-phase NT stability read, the next useful slice is NOT this probe; it would need either the targeted_rescue NT run or another shared-id comparison with meaningful hard-clean coverage.

### Key discoveries
- `data/candidates_nothinking_breakdown.md` and `data/candidates_nothinking_98.txt` are definitively tied to `nothinking_probe98_20260526T065456Z`.
- `shape_fallback` is the dominant failure mode in probe98 (`46/98`), not truncation (`0`) or missing boxes (`0`).
- The probe's apparent all-rows bucket agreement with NT-943 (`85/98`) is misleading because `54/54` `unknown -> unknown` rows dominate it; on the real scored slice the agreement is much worse (`31/44` buckets, `32/44` math correctness).

## claude_thunder_tnr1 signoff — 2026-05-31 — Thinking-probe inference
- Tried: SC@16 Thinking-mode on 59 R20-wrong multi-slot/precision items (slice 59-117 of thinking_probe_target_set)
- Did: Full run inference/base_model/thinking_probe_tnr1_20260531T065534Z/, 59 items, SC@16, max-tokens 81920, thinking-budget 65536, TP=2, 2×A100 80GB
- Worked: 59/59 items completed, 0 truncations, 0 empty samples, ~19/59 rescued by slot-aware gold match (~32%), wall time ~4.0h avg 245s/item. 16MB samples.jsonl pushed via LFS commit ecc7adf.
- Didn't: Exact-string rescue count is 0 (multi-slot gold format mismatch) — slot-aware needed for real count. Several near-misses due to formatting differences (e.g. ID 736 sqrt formatting, ID 705 True/False formatting).
- Left: inference/base_model/thinking_probe_tnr1_20260531T065534Z/samples.jsonl + inference.log + summary.txt on main. Cross-run analysis with tnr-0 pending.
- Discoveries: One outlier item (ID 453, 2982s) drove early ETA inflation — rest were 18-694s. avg settled at 245s. Budget 81920/65536 produced 0 truncations vs prior runs at 49152/24576.

---
## claude_thunder_tnr0 signoff — 2026-05-31 — Thinking-probe inference
### What I tried
- SC@16 Thinking-mode inference on items 0-58 (lowest 59 IDs sorted ascending) of `submission/csvs/picks/thinking_probe_target_set.csv` (118 items total; tnr-1 took the upper 59).
- Initial config (49152 / 24576) → smoke OK; bumped per claude_strategy patch to high-tier budget (81920 / 65536) before full run.
### What I did
- State fix: preserved 371 commits of pre-reorg local main as `tnr-local-main-may27-preserve` branch on origin before hard-reset to origin/main.
- Pre-flight 7-step (incl. extraction fix — CSV has embedded newlines in LaTeX fields, shell `cut/sort` silently produced 59 empty lines; switched to Python `csv` parser).
- Smoke (5 items) → pass; full run launched in `tmux` with `RUN_DIR` env-exported per claude_strategy's blocker fix.
- Full run: 5.17 hr wall time, 0 truncations, 0 empties, 944 samples total.
- Push: LFS budget initially exhausted; surfaced per LFS rule; budget bumped externally; retried; merge conflict in `.gitattributes` resolved by keeping both tnr-0 and tnr-1 LFS patterns; commit `fad3fc4` pushed.
### What worked
- Smoke: 5/5 items, majority boxed (gate ≥ 4/5).
- Full run health: 0/944 truncation despite 28138-token max seen. Budget headroom 3×.
- Vote concentration: 53/59 items at n_voting ≥ 10 (strong consensus).
### What didn't work
- 2 items had n_voting=1 (IDs 9, 416); 4 items at n_voting 2-9 (IDs 25, others). Mostly multi-slot/multi-form LaTeX where extractor or aggregator failed to converge — model reasoning was correct in raw samples (per ID 9 / 25 diagnostic dump).
- Shape fallback fired on 43/59 items (73%) — normal for multi-slot/precision-tier items but worth noting in cross-run analysis.
- One outlier: ID 194 took ~1150s (~19 min) wall; cumulative-frequency-style problem.
### What's left
- claude_strategy: cross-run analysis with tnr-1 (`inference/base_model/thinking_probe_tnr1_20260531T065534Z/`) for the rescue audit. My loose-norm rough audit showed ≥5-7 rescues + 2 surface-level regressions, but all "regressions" are multi-slot artifacts not true wrong answers; canonical per-slot scoring needed.
### Key discoveries
- **CSV with embedded newlines + shell `cut`/`sort` silently produces empty output.** This affects the spawn-prompt boilerplate; future probes should use Python CSV parser for ID extraction. Filed under "discipline win" for spawn-prompt patches.
- **Multi-`\boxed{}` answers (multi-slot `[ANS] [ANS]` questions) confuse the SC aggregator.** ID 9: all 16 samples correctly wrote `\boxed{L-8x}` and `\boxed{6F}`, but n_voting=1 because each sample's extracted form was just `6F` (last box) yet voted_answer reconstructs the joined fraction. Worth instrumenting.
- **shape_fallback at 73% on this slice suggests the multi-slot/precision target set is exactly the bucket where SC consensus is hardest** — the bumped token budget didn't help that, only helped per-sample reasoning depth.
- State-fix discipline win: rather than hard-resetting and losing 12 local commits, preserved as feature branch first.

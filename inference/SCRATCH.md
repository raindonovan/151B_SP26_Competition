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
(filled below after commit)

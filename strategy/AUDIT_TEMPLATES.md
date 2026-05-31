# strategy/AUDIT_TEMPLATES.md — Reusable spawn-prompt templates

> **Status (Day 9 2026-05-30, locked)**: built during the inference-audit
> 6-hr push. Templates are paste-fill, not re-draft. Saves draft time per
> session and prevents discipline drift under deadline pressure.
>
> **Identity-addressing rule** (memory #9): every prompt MUST start with
> `TO: {AGENT}` / `FROM: CLAUDE_STRATEGY` headers. Guardrail against wrong
> agent reading wrong prompt.
>
> **Placeholders** are in `{ALL_CAPS_BRACES}`. claude_strategy fills these
> in per session.

## Template index

| Template | When to use | Per-session cadence |
|---|---|---|
| **T1 — Shallow batch catalog** | Dev/smoke/ablation runs (R00–R07, R10b, R11–R19) | Multiple runs per session (4–6 in a batch) |
| **T2 — Deep audit (p943)** | Pick-B-relevant runs (R08, R09, R10, R20, R20b) | ONE run per session, full discipline |
| **T3 — ChatGPT DEEP per-run audit** | After every T2 deep audit (mandatory, one per p943 run) | One per deep run, 15–20 min |
| **T4 — ChatGPT FINAL cross-run sanity** | Once after CROSS_RUN_MATRIX.csv is built (~02:00 Sun) | Once total, 20–25 min |

---

## T1 — Shallow batch catalog (vscode)

```
TO: CLAUDE_VSCODE
FROM: CLAUDE_STRATEGY
SUBJECT: SHALLOW catalog batch — {RUN_LIST} ({R_NUMS}); rename + brief
         docs + cross-ref sweep, one commit at end

ROLE & RELEVANCE
Role: Mechanical catalog of {N} shallow dev/smoke/ablation runs in ONE
batch session. Renames + 2-paragraph README + 1-paragraph findings per
run + cross-ref sweep across 27 docs.
Relevance: Identity preservation only. These runs predate the p943 cohort
and DO NOT feed CROSS_RUN_MATRIX or Pick B. We're keeping the history
clean for the final report and the post-deadline backlog. NOT analysis
work.

SETUP (once for the batch)
cd /home/raindonovan/151B_SP26_Competition
git fetch origin && git pull --ff-only origin main
cat inference/runs/CATALOG.md | sed -n '30,75p'      # status table
ls scripts/rename_run.sh || echo "MISSING — flag to claude_strategy"

PER-RUN LOOP (for each run in batch):
  Batch list:
    {R_NUM_1}: {OLD_NAME_1} → inference/base_model/{R_NUM_1}_{SLUG_1}/
    {R_NUM_2}: {OLD_NAME_2} → inference/base_model/{R_NUM_2}_{SLUG_2}/
    {... continue per batch}

  1. Read run head + summary.json (or git-log first commit if no summary).
  2. Create folder: inference/base_model/{R_NUM}_{SLUG}/
  3. git mv run artifacts in:
     - .jsonl + .summary.json
     - Matching infrastructure/logs/ entries (if any)
     - Submission CSVs derived from this run STAY in submission/csvs/
       but reference back to the run folder in README
  4. Write README.md (≤2 paragraphs). Required fields:
     - Original name + R#
     - Run date (UTC, from summary.json.started_at or git first-commit)
     - Config: model, method, n_samples, max_new_tokens, temperature,
       n_items
     - Purpose: one sentence on why this run existed in dev arc
  5. Write findings.md (≤1 paragraph). Either the headline result OR
     "No findings beyond development iteration" if it was scaffolding.
  6. Run cross-ref sweep:
       ./scripts/rename_run.sh {OLD_NAME} inference/base_model/{R_NUM}_{SLUG}
     Verify it produced sensible diff (head of output).
  7. Update inference/runs/CATALOG.md: ⚪ → 🟢 for this row; in
     R-number registry, change "reserved" → "cataloged".
  8. Move to next run in batch — SAME vscode session.

BATCH COMMIT (once all {N} runs done):
  git add inference/base_model/{R_NUMS}_*/ inference/runs/CATALOG.md
  git add {cross-ref doc changes from rename_run.sh — git status to see}
  git commit -m "inference/runs: catalog shallow batch {R_NUMS} —
    renames + brief docs + cross-ref sweep ({N} runs)"
  git push

REPORT BACK to claude_strategy (one short message, addressed):
  - {N} runs cataloged this batch
  - Per-run: R{NN}: {old} → {new_path}
  - Cross-ref sweep total replacements (summed across runs)
  - Anything unusual found (e.g. a "smoke" that was actually a real eval)
  - Commit hash

SIGNOFF
Append batch entry to inference/SCRATCH.md.

DO NOT in this session:
  - Run analyze_run.py on any of these (they're shallow)
  - Fire any ChatGPT audit
  - Spend more than 2 paragraphs on README, 1 on findings
  - Investigate "interesting" findings beyond logging the bare fact
  - Open any deep-audit work (separate sessions, T2 template)
  - Modify analyze_run.py
```

---

## T2 — Deep audit per p943 run (vscode)

```
TO: CLAUDE_VSCODE
FROM: CLAUDE_STRATEGY
SUBJECT: DEEP audit — R{NN} {OLD_NAME} (Pick-B-relevant p943 cohort)

ROLE & RELEVANCE
Role: Full audit of ONE p943 run that feeds CROSS_RUN_MATRIX and Pick B.
Includes analyze_run.py run, line-by-line review of contested rows
(A_lucky_sample + B-review-needed), findings prose, then claude_strategy
dispatches a ChatGPT per-run audit (T3) afterward.
Relevance: This run contributes Bucket A/A_lucky_sample/B labels to the
cross-run consensus that produces tonight's Pick B candidate. Quality
here directly affects the deadline submission.

SETUP
cd /home/raindonovan/151B_SP26_Competition
git fetch origin && git pull --ff-only origin main
cat inference/scripts/analyze_run.py | head -60
cat inference/runs/CATALOG.md | grep -B1 -A1 "R{NN}"

TASK (single run, single commit)
1. Create folder: inference/base_model/R{NN}_{SLUG}/
2. git mv run artifacts in:
   - .jsonl + .summary.json
   - Related infrastructure/logs/ entries
   - Submission CSVs STAY in submission/csvs/, README cross-links
3. Run analyzer:
     python3 inference/scripts/analyze_run.py \
       --run-jsonl inference/base_model/R{NN}_{SLUG}/{JSONL_BASENAME} \
       --output-dir inference/base_model/R{NN}_{SLUG}/analysis/ \
       --run-id R{NN}_{SLUG} \
       --kaggle-score {KAGGLE_SCORE_OR_OMIT}
4. Verify analyzer output passes acceptance gates a-i (v3-final spec).
   If any fail → STOP, report. Don't commit.
5. Build findings.md (long form OK — these matter):
   a. Headline: bucket distribution + scored-set accuracy
   b. hard_independent accuracy (n + per-source: wolfram_HIGH,
      search_GOLD)
   c. unanimous_teachers accuracy
   d. A_lucky_sample item list with (item_id, sample_index) of the
      correct sample — this is the adapter-trace-harvest input
   e. B item list + which look format-recoverable on inspection
   f. Cross-run implications: items where this run differs from other
      p943 runs already cataloged
6. Cross-ref sweep:
     ./scripts/rename_run.sh {OLD_NAME} inference/base_model/R{NN}_{SLUG}
7. Update inference/runs/CATALOG.md: ⚪ → 🟢, registry "reserved" →
   "cataloged".
8. Commit + push:
     "inference/runs: catalog R{NN} {OLD_NAME} → R{NN}_{SLUG} (deep
      audit + analyzer artifacts + findings)"

REPORT BACK:
  - Pass/Fail on gates a-i
  - Bucket distribution: A, A_lucky_sample, B, unknown
  - hard_independent accuracy (n + acc)
  - unanimous_teachers accuracy (n + acc)
  - A_lucky_sample list: top 10 by n_samples_math_correct
  - B item list with format-recoverable flag (inspection)
  - Commit hash
  - Anything diverging from previous deep-audit findings

SIGNOFF
Per-run entry to inference/SCRATCH.md.

DO NOT in this session:
  - Move on to another run (ONE deep run per session)
  - Modify analyze_run.py
  - Fire ChatGPT audit yourself — claude_strategy dispatches T3 next
```

---

## T3 — ChatGPT per-run audit (after every T2)

```
TO: CHATGPT_AUDIT
FROM: CLAUDE_STRATEGY
SUBJECT: DEEP per-run audit on R{NN} {OLD_NAME} findings + analyzer
         artifacts — p943 deep cohort

WALL TIME:
  - Now: {TIME_PT}
  - Hard deadline: Sun May 31 23:59 PT
  - Audit budget for YOU: 15-20 min. This is a DEEP per-run pass.
    Analyzer code is locked at commit 761f903 (or whatever the v3-
    final-final hash is — verify in repo); you're auditing the
    FINDINGS PROSE plus the ANALYSIS ARTIFACTS for this specific run.
  - Output cap: 400 words.

CONTEXT
R{NN} is one of the 5 p943 deep-cohort runs (R08, R09, R10, R20, R20b).
These 5 are the ONLY runs that feed CROSS_RUN_MATRIX, which decides:
Pick B candidate selection, adapter target set (true Bucket B),
structural-normalizer probe list (format-recoverable items), and
morning-run pickups. Every deep run gets a deep audit because a single
miscategorized B item could mean a wrong adapter target or a missed
format probe.

ARTIFACTS
Repo: beepbeeepimajeep/151B_SP26_Competition
Commit: {COMMIT_HASH}

Read fully:
  inference/base_model/R{NN}_{SLUG}/findings.md
  inference/base_model/R{NN}_{SLUG}/README.md
  inference/base_model/R{NN}_{SLUG}/analysis/analysis.csv
  inference/base_model/R{NN}_{SLUG}/analysis/analysis.jsonl  (spot-check)
  inference/base_model/R{NN}_{SLUG}/analysis/analysis_samples.jsonl  (SC only)

For cross-run context (skip for R08, first in cohort):
  Prior R-folders' analysis.csv to compare bucket patterns

AUDIT DIMENSIONS:

1. NUMERICAL CONSISTENCY (findings.md ↔ analysis.csv):
   - Bucket counts (A, A_lucky_sample, B, unknown) match exactly
   - hard_independent_CLEAN n + acc match
   - unanimous_teachers n + acc match
   - All counts in findings derivable from the artifacts

2. A_lucky_sample VALIDITY (SC runs only — skip for R08 single-sample):
   - Each cited (item_id, sample_index) pair exists in
     analysis_samples.jsonl with sample_correct=True
   - Sort order matches findings' claimed sort (n_samples_math_correct
     high → low)
   - Spot-check 3 traces in analysis.jsonl: confirm math reasoning
     actually leads to gold answer

3. B-ITEM CLASSIFICATION (LOAD-BEARING):
   - For each B item findings flags format-recoverable: read response
     trace; confirm the math IS right in the body
   - For each B item findings flags true_B: confirm Qwen genuinely
     didn't solve
   - Misclassifications corrupt adapter target set AND normalizer
     probe list. This is the highest-value check.

4. TRUNCATED ITEMS:
   - Count matches findings
   - Spot-check 2: did math get cut off, or did model just stop
     reasoning? Different failure modes; both worth flagging.

5. CROSS-RUN PATTERNS (R09+ only):
   - Items this run gets right that prior cohort runs got wrong: do
     they look genuinely flippable (longer tokens / different prompt
     / SC helped), or noise?
   - Items this run gets wrong that prior runs got right: regression
     pattern — what's the common feature?

6. UNEXPECTED FINDINGS:
   - Anything in the data findings.md MISSED?
   - Specifically: items at unusual buckets (e.g., A_lucky_sample
     with n=8/8 correct but voted wrong — implies analyzer voting
     bug OR shape filter issue)
   - Output-format failure modes not yet catalogued

OUTPUT FORMAT (exactly this, ≤400 words):

VERDICT: GREEN (matrix-ready) / YELLOW (N fixes) / RED (re-do)
NUMERICAL CONSISTENCY: [pass / list discrepancies]
A_lucky_sample VALIDITY: [confirmed / N invalid; specifics]
B-ITEM CLASSIFICATION ACCURACY: [N/M correct / misses listed]
TRUNCATION SPOT-CHECK: [pattern observed]
CROSS-RUN PATTERN (n/a for R08): [insight or none]
UNEXPECTED FINDING: [single most important; or "none"]
CONFIDENCE this run is matrix-ready: low / med / high

DO NOT:
  - Re-litigate analyzer methodology (locked)
  - Suggest schema changes
  - Comment on chronology or other runs' R-numbers
  - Style review
```

---

## T4 — ChatGPT FINAL cross-run matrix sanity audit (once, after all 5 deep audits)

Fire ONCE, after CROSS_RUN_MATRIX.csv is built (~02:00 Sun expected).
This is the LAST audit before we use the matrix to decide Pick B
candidates, adapter targets, structural-normalizer probes, and
morning-run pickups. Mistakes here propagate to all four downstream
workstreams.

```
TO: CHATGPT_AUDIT
FROM: CLAUDE_STRATEGY
SUBJECT: FINAL SANITY — CROSS_RUN_MATRIX.csv + 5-run p943 cohort
         synthesis (last audit before downstream decisions)

WALL TIME:
  - Now: {TIME_PT} (~02:00 Sun expected)
  - Hard deadline: Sun May 31 23:59 PT (~21 hr from this audit)
  - Audit budget for YOU: 20-25 min.
  - Output cap: 500 words.

CONTEXT
You've audited all 5 p943 runs (R08, R09, R10, R20, R20b) at deep T3
level — each individually cleared. Now their bucket columns are
stitched into CROSS_RUN_MATRIX.csv (943 rows × 5 runs). The matrix
feeds:
  - Pick B candidate selection (cross-run consensus on math_correct)
  - Adapter target set (items wrong across ALL p943 runs = true B)
  - Structural-normalizer probe list (format-recoverable B items)
  - Morning-run candidates (per strategy/MORNING_RUNS_WATCHLIST.md
    thresholds)

ARTIFACTS
Repo: beepbeeepimajeep/151B_SP26_Competition
Commit: {COMMIT_HASH}

Read fully:
  inference/runs/CROSS_RUN_MATRIX.csv
  inference/base_model/R08_*/findings.md (and R09, R10, R20, R20b)
  strategy/MORNING_RUNS_WATCHLIST.md
  Any cross-run synthesis doc claude_strategy committed

AUDIT DIMENSIONS:

1. MATRIX INTERNAL CONSISTENCY:
   - Every row has 5 bucket entries (one per run)
   - item_id alignment correct (no off-by-one)
   - Bucket label set clean ({A, A_lucky_sample, B, unknown})
   - No NA / empty cells

2. ADAPTER TARGET SET (B-or-A_lucky in ALL 5 runs):
   - Count seems sane (Rain estimated 25-50 true B items)
   - Spot-check 3: do they look genuinely hard, or
     format-recoverable that all 5 runs failed identically?

3. PICK B CANDIDATE (consensus on math_correct):
   - Items A in ≥3 of 5 runs = trustworthy consensus A
   - Compare consensus count to individual-run A counts; should
     overlap significantly with R20's A set (R20 = best run)
   - Items where consensus says A but R20 says B: A_lucky_sample-
     recovered items, candidates for Pick B uplift

4. FORMAT-RECOVERABLE SET (structural-normalizer probes):
   - Across all 5 deep audits, how many distinct items flagged
     format-recoverable?
   - Distinct failure modes (multi-slot / MCQ-first-box / precision)?
   - Distribution suggests probe priority for the 3 normalizer slots

5. MORNING-RUN SIGNAL CHECK
   (vs strategy/MORNING_RUNS_WATCHLIST.md thresholds):
   - Count A_lucky_sample with n_samples_math_correct ≥ 5/8 across
     R09/R10/R20/R20b (R08 single-sample exempt)
   - Count truncated items at 16K (R08/R09/R10) vs 32K (R20)
   - Count all-p943-wrong items

6. RED FLAGS:
   - Any run with vastly different bucket distribution? (Suggests
     analyzer bug or run pathology — block matrix use until resolved.)
   - Any item with all 5 buckets='unknown'? (Sanity: ~445 unknowns
     per run if alignment correct.)
   - Any cell that looks like a copy-paste error from the wrong run?

OUTPUT FORMAT (exactly this, ≤500 words):

VERDICT: GREEN (matrix ready for ALL 4 downstream uses) /
         YELLOW (N issues block specific uses — list which) /
         RED (matrix not usable)
INTERNAL CONSISTENCY: [pass / issues listed]
ADAPTER TARGET COUNT: [N items + qualitative assessment]
PICK B CONSENSUS COUNT: [N items A in ≥3/5 + delta vs R20-alone]
STRUCTURAL NORMALIZER PROBE LIST SIZE: [N + top failure modes]
MORNING-RUN SIGNAL: [GO if thresholds met / NO-GO if signals weak]
RED FLAGS: [list or "none"]
ONE THING TO INVESTIGATE BEFORE USING MATRIX: [single item or "none"]
DOWNSTREAM READINESS (mark each):
  - Pick B build: ready / blocked
  - Adapter targeting: ready / blocked
  - Normalizer probes: ready / blocked
  - Morning runs: ready / blocked

DO NOT:
  - Re-audit individual runs (already T3-cleared)
  - Comment on analyzer methodology
  - Suggest new submission strategies
```

---

## Pre-flight checklist for claude_strategy before firing any template

1. **Identity header populated**: `TO:` is the correct agent, `FROM: CLAUDE_STRATEGY`
2. **All `{PLACEHOLDERS}` filled**: zero `{...}` strings remain in the final fenced block
3. **Wall-time updated** on T3/T4 audits (current PT)
4. **Commit hash filled** on T3/T4 (otherwise ChatGPT can't read the artifacts)
5. **Batch size sanity** on T1: 4–6 shallow runs max per batch (more = context bloat for vscode)
6. **One run only** on T2 (the per-session discipline for deep)
7. **R# matches CATALOG.md** for the run being cataloged (no surprises)
8. **T3 fires AFTER every T2** (mandatory; not optional now per Day-9 discipline)
9. **T4 fires ONCE after CROSS_RUN_MATRIX exists** (final gate before downstream decisions)

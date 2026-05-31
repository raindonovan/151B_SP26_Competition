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
| **T3 — ChatGPT per-run audit** | After every T2 deep audit only | One per deep run, ≤10 min |

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
SUBJECT: Per-run audit on R{NN} {OLD_NAME} findings — p943 deep cohort

WALL TIME:
  - Now: {TIME_PT}
  - Hard deadline: Sun May 31 23:59 PT
  - Audit budget for YOU: 5-10 min. Light per-run pass. Analyzer was
    full-audited at commit {V3_FINAL_HASH}; this is per-run sanity, not
    analyzer methodology review.
  - Output cap: 200 words.

CONTEXT
R{NN} is one of the Pick-B-relevant p943 cohort (R08, R09, R10, R20,
R20b). Analyzer v3-final is locked. You're checking the findings prose
against the analyzer artifacts for THIS specific run only.

ARTIFACTS
Repo: beepbeeepimajeep/151B_SP26_Competition
Commit: {COMMIT_HASH}

Read:
  inference/base_model/R{NN}_{SLUG}/findings.md
  inference/base_model/R{NN}_{SLUG}/analysis/analysis.csv
  inference/base_model/R{NN}_{SLUG}/analysis/analysis_samples.jsonl (skim)
  inference/base_model/R{NN}_{SLUG}/analysis/analysis.jsonl (spot-check)

CHECK ONLY:
1. Do findings.md headline numbers match analysis.csv (bucket counts,
   accuracies)?
2. Do cited (item_id, sample_index) pairs in the A_lucky_sample list
   exist in analysis_samples.jsonl with sample_correct=True?
3. Do the B items flagged "format-recoverable" actually show math-right
   in the response trace from analysis.jsonl?
4. ONE THING the findings missed about this run that cross-run analysis
   will need? Or "none".

OUTPUT (exactly, ≤200 words):
VERDICT: GREEN / YELLOW / RED
DISCREPANCIES (findings vs artifacts): [list or "none"]
A_lucky_sample VALIDITY: [confirmed / N invalid]
B-ITEM CLASSIFICATION: [accurate / N misclassified]
ONE MISSING THING: [single item or "none"]

DO NOT:
  - Re-litigate analyzer methodology (locked)
  - Suggest schema changes
  - Comment on chronology
  - Style review
```

---

## Pre-flight checklist for claude_strategy before firing any template

1. **Identity header populated**: `TO:` is the correct agent, `FROM: CLAUDE_STRATEGY`
2. **All `{PLACEHOLDERS}` filled**: zero `{...}` strings remain in the final fenced block
3. **Wall-time updated** on T3 audits (current PT)
4. **Commit hash filled** on T3 (otherwise ChatGPT can't read the artifacts)
5. **Batch size sanity** on T1: 4–6 shallow runs max per batch (more = context bloat for vscode)
6. **One run only** on T2 (the per-session discipline for deep)
7. **R# matches CATALOG.md** for the run being cataloged (no surprises)

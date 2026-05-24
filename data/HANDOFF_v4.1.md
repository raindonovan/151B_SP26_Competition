# HANDOFF — claude_strategy session continuity

**Version:** 4.1
**Last updated:** 2026-05-24 (~09:00 UTC)
**Supersedes:** HANDOFF v3.0 (2026-05-23 evening)
**Owner:** Rain (dvaneetv@ucsd.edu)
**Project:** CSE 151B (UCSD) Kaggle math reasoning competition

---

## CRITICAL SESSION STATE (2026-05-24)

- **BEST KAGGLE: 0.646** — `run14b_v3filtered.csv` (base model, SC=8, 32K, V3 shape filter)
- **SFT v3 SC=1: 0.452** — tested, root cause identified (MCQ format mismatch). All free-form items memorized 100%. MCQ failed at 41.5% due to missing options in training data.
- **SFT v4: TRAINED + MERGED.** Epoch 6 (checkpoint-588) selected empirically. Merged model at `sft_v4_epoch6_merged` on Thunder. 391 items, clean traces (`<think>` tags, no markdown artifacts), all SFT v3 bugs fixed.
- **GenSelect smoke: COMPLETE.** SC=16 voting works (3 clear, 4 medium, 5 split out of 12 test items). NL verification unreliable on 4B (3/6 returned labels instead of answers). Skip NL verification.
- **PROVE smoke: IN PROGRESS.** 35-item expanded test running on Thunder. Testing post-hoc Python code verification on numeric answers.
- **Total Kaggle submissions: 16** (see §4)
- **Days remaining: ~8**
- **Thunder status: RUNNING** (PROVE smoke test). Stop when idle.

---

## 0. BOOT SEQUENCE

You are claude_strategy. Context resets between sessions.

1. Read this HANDOFF top to bottom
2. Read CLAUDE_STRATEGY.md from repo root: https://github.com/beepbeeepimajeep/151B_SP26_Competition
3. Read both repos (Competition + DataApp) via bash+curl raw.githubusercontent.com
4. Check Google Drive folder "151B Competition" (ID: `14ntQe56m_ufIPyDk_Cs-sPjSESQ1NRZ8`)
5. Search past chats: `conversation_search("SFT v4 PROVE genselect")`, `conversation_search("answer sheet adaptive inference")`
6. Check memory (~27 entries). Key: current best 0.646, SFT v4 training fixes, answer sheet workflow, testing principle, ADHD support.
7. Verify tools: bash_tool, web_search, Google Drive MCP, conversation_search, memory_user_edits
8. Respond

---

## 1. FOUR-AGENT SETUP

| Agent | Where | Job |
|-------|-------|-----|
| **claude_strategy** (you) | Claude.ai | Plan, audit, research, direct |
| **claude_vscode** | DSMLP pod | Execute on Competition repo |
| **claude_dataApp** | DSMLP pod (separate) | Execute on DataApp repo |
| **claude_thunder** | Thunder (laptop SSH) | SFT training + inference |

**Workflow:** claude_strategy gives specs → execution agents implement → claude_strategy audits from repo (raw.githubusercontent.com) → approves launch. Never write full scripts — spec what needs to happen.

**Communication:** Execution agents prefix `[FROM CLAUDE_VSCODE/DATAAPP/THUNDER]`. Your prompts = single code block, no preamble. One prompt at a time for dataApp.

**File transfer:** Via the repo ONLY (commit + push + pull). Not Google Drive.

---

## 2. THUNDER COMPUTE

**Instance:** ID 0, RTX A6000, SSH host `tnr-0`
**Key paths:**
- SFT v4 merged model: `~/sft_v4_epoch6_merged` (~8GB)
- SFT v4 checkpoints: `~/151B_SP26_Competition/checkpoints/sft_v4/` (epochs 4, 6, 8)
- SFT v3 merged: `~/sft_v3_epoch4_merged` (historical)
- Smoke scripts: `scripts/genselect_smoke.py`, `scripts/prove_smoke.py`

**BILLING:** `tnr stop 0` when idle. Costs $/hr.

---

## 3. TRITONAI API ENDPOINT

UCSD LiteLLM gateway. Base Qwen3-4B-Thinking (no adapter).
```
URL: https://tritonai-api.ucsd.edu/v1
Key: sk-rT2cq501v0ydXxdpnMF4Hw
Model: api-test-qwen-3-4b
```
LoRA NOT enabled. Contact: Dominic Feliton.

---

## 4. KAGGLE SUBMISSIONS (16 total)

**BEST: 0.646** (run14b_v3filtered.csv)

| # | File | Score | Notes |
|---|---|---|---|
| 1 | run14b_v3filtered.csv | 0.646 | BEST — base SC=8 32K V3 filter |
| 2 | run14b_sc8_v1.csv | 0.639 | Base SC=8 32K |
| 3 | run09sc8_v1_private943.csv | 0.614 | Base SC=8 16K |
| 4 | run09sc8_format_fixed.csv | 0.611 | Format fix |
| 5 | run08v2_v1_private943.csv | 0.586 | Base SC=8 |
| 6 | diagnostic_sub_a.csv | 0.505 | DiagA |
| 7 | sftv3_epoch8_sc1_final.csv | 0.452 | SFT v3 SC=1 |
| 8 | run09sc8_probe_b_reversed.csv | 0.438 | Order probe |
| 9 | run10_v3perslot_private943.csv | 0.424 | Per-slot |
| 10 | expA_run08_perslot_perturbed.csv | 0.420 | Per-slot |
| 11-16 | diagnostics D/C/B/F/E/G | 0.017-0.310 | Various diagnostics |

**Format:** CSV with `"id","response"` columns. Response = FULL model output with traces + `\boxed{}`. Grader extracts last `\boxed{}`.

---

## 5. UNIFIED ANSWER SHEET v3

**Script:** `scripts/build_answer_sheet.py`
**Data:** 16 submissions + teacher consensus (Sonnet/GPT-5.4/GPT-OSS, xhigh EXCLUDED)

**Tiers:** T1=256(27.1%), T2=214(22.7%), T3=171(18.1%), T4=145(15.4%), T5=157(16.6%)
**Teacher:** agrees=412, disagrees=486 genuine + 45 normalization
**Validation:** 6/9 PASS, 3 WARN, 0 FAIL

**Workflow:** After each submission: add to SUBMISSION_REGISTRY → re-run script → update answer sheet.

---

## 6. SFT STATUS

### 6.1 SFT v3 Postmortem (0.452)
- Free-form: 100% memorization (293/293)
- MCQ: 41.5% memorization (83/200) — ALL failures were MCQ
- Root cause: training had 0/200 MCQ items with options in user message
- Also: xhigh contamination (~29 items), 101 duplicates

### 6.2 SFT v4 (TRAINED + MERGED)
- **391 items** (T1+T2 teacher agrees): 202 MCQ, 112 single_free, 77 multi_free
- All Sonnet traces, xhigh excluded, 0 duplicates
- Traces cleaned: `<think>...</think>\n\n\boxed{answer}` format, no markdown headers
- MCQ options in user message (bare, no letter labels)
- **Epoch 6 selected empirically** (5/5 MCQ, 5/5 free, FORMAT=0/10 is decode artifact)
- Config: r=64, α=128, wd=0, bs=2×8, max_seq=5500, cosine LR 2e-4, 8 epochs

### 6.3 SFT Training Protocol (LOCKED)
Compare ALL checkpoints empirically. Test 5 MCQ + 5 free-form per checkpoint using PEFT direct loading. Pick earliest epoch with MCQ ≥ 4/5. Never assume epoch 4 is best.

---

## 7. INFERENCE STRATEGY

### 7.1 Adaptive SC (planned)
- Trained items (391): SC=3, max_tokens=4096
- Untrained items (552): SC=16 (8×T=0.6 + 8×T=1.0), max_tokens=16384
- Run on Thunder (model already there, no transfer needed)
- Rerun truncated items at 32K if needed

### 7.2 GenSelect Smoke Results
- 12 items tested: 3 clear (≥75%), 4 medium (50-75%), 5 deep split (<50%)
- NL verification unreliable: 3/6 returned labels ("A"/"B") despite instructions
- NL verification verdict: SKIP for 4B model

### 7.3 PROVE (Programs as Verifiers) — IN PROGRESS
- Post-hoc: model writes Python to independently solve problem, we execute and compare
- Works on numeric free-form items (~159 GOOD, ~178 MAYBE out of 552 untrained)
- Doesn't work on: MCQ (letter answer), symbolic LaTeX, proof-based problems
- 35-item expanded test: 5 calibration + 25 GOOD + 5 edge cases
- Testing principle: calibrate against items where we KNOW the answer

---

## 8. RESEARCH FINDINGS (for inference optimization)

1. **SC-TIR won AIMO** — code execution DURING reasoning. Needs TIR-trained model (we don't have).
2. **PROVE works on small models** — 0.5B to 7B showed gains (PROVE paper, 2024).
3. **NL verification unreliable below 13B** — confirmed by Zhang et al. 2024 + our smoke test.
4. **Calculator-mode PROVE** — ask for one-line Python expression instead of full program. Simpler, fewer bugs.
5. **Self-healing** — if code errors, feed error back for one retry.
6. **Element-wise multi-answer verification** — verify each sub-answer separately.
7. **Prompt matching is critical** — AIMO winners emphasized using exact training prompts.
8. **Functional Majority Voting (FMV)** — vote on program outputs not answer strings.
9. **GenSelect works for large models** (QwQ-32B, DeepSeek-R1) but needs RL training for small models.

---

## 9. LOCKED FINDINGS (don't relitigate)

1. V3 shape filter = +0.7pp. Apply to ALL runs.
2. 32K tokens = +2.5pp over 16K.
3. Per-slot `\boxed{}` costs −16.2pp. Use single `\boxed{a, b, c}`.
4. Training on private.jsonl: ALLOWED.
5. Submission format: `"id","response"` with FULL traces.
6. xhigh is catastrophically bad (40.5% on T1). EXCLUDE from everything.
7. MCQ options MUST be in user message for SFT training.
8. Inference prompt MUST EXACTLY match training format.
9. Submission slots NOT scarce (3/day).

---

## 10. KEY SCRIPTS IN REPO

| Script | Purpose | Branch |
|---|---|---|
| `scripts/build_answer_sheet.py` | Answer sheet builder (16 subs + teacher) | sync |
| `scripts/genselect_smoke.py` | SC=16 + NL verification smoke test | sync |
| `scripts/prove_smoke.py` | PROVE code verification smoke test | sync |
| `scripts/run_vllm_sc.py` | SC inference runner (⚠️ adds letter labels to MCQ — DO NOT USE with SFT adapter) | main |
| `scripts/post_filter.py` | V3 shape filter | main |
| `sft/v4/scripts/train_sft_v4.py` | SFT v4 training | sync |
| `sft/v3/scripts/merge_adapter.py` | LoRA merge (argparse) | main |

**⚠️ Branch divergence:** Thunder is on `sync/submissions_from_origin_20260524`. DSMLP vscode is on `main`. Need merge.

---

## 11. TO-DO LIST

### IN PROGRESS
1. PROVE smoke test running on Thunder (35 items)

### AFTER PROVE RESULTS
2. Decide: include PROVE in full run (if ≥15/25 GOOD items work) or skip
3. Run full adaptive inference on Thunder (SC=3 trained + SC=16 untrained + optional PROVE)
4. Build submission CSV → submit to Kaggle
5. Update answer sheet with new submission

### IF TIME ALLOWS
6. SFT v5 with expanded training set (based on updated answer sheet)
7. PROVE with self-healing retry (if smoke test shows code errors are the main failure mode)
8. Merge sync branch to main

### CLEANUP
9. Stop Thunder when done
10. Update Drive docs
11. DataApp repo cleanup (PAT rotation)

---

## 12. ABOUT RAIN

- Undergrad CS at UCSD, learning ML/SWE through this competition
- Has ADHD (diagnosed). When Rain drifts to tangents: acknowledge briefly, offer to add to todo, redirect to current task.
- Direct, no theater. Lowercase. Calls out BS.
- Wants the WHY. Teaching moments valued.
- Makes execution decisions (where to run, what GPU). Don't override.
- File transfer via repo ONLY, not Drive.
- claude_strategy specs, agents implement, strategy audits from repo.

---

## 13. FAILURE MODES TO AVOID

1. Wrong submission format (`"id","answer"` instead of `"id","response"` with full traces)
2. Including xhigh in anything
3. Mismatched train/inference prompts (MCQ options format)
4. Using `run_vllm_sc.py` with SFT adapter (adds letter labels that break format)
5. Google Drive as file transfer (use repo)
6. Writing implementation code instead of specs (strategy role)
7. Following Rain's tangents without redirecting (ADHD support)
8. Guessing script args without reading the actual script
9. Overconfident answer sheet (correlated submissions inflate Bayesian confidence)

---

**v4.1 (2026-05-24 ~09:00 UTC):** Full rewrite. SFT v3→v4 transition complete. Answer sheet v3 built. GenSelect smoke done (NL verification fails, skip). PROVE testing in progress. Research findings documented. Inference strategy planned. Branch divergence flagged.

**End of HANDOFF v4.1.**

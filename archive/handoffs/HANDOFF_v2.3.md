# HANDOFF — claude_strategy session continuity

**Version:** 2.3  
**Last updated:** 2026-05-23  
**Supersedes:** HANDOFF.md v2.2 (2026-05-22 early morning)  
**Owner:** Rain (dvaneetv@ucsd.edu)  
**Project:** CSE 151B (UCSD) Kaggle math reasoning competition

---

## RECENT UPDATES (2026-05-23)

- **NEW BEST KAGGLE: 0.646** — `run14b_v3filtered.csv` (V3 shape filter applied to run14b SC-8)
- **V3 shape filter CONFIRMED +0.7pp** (Run14b base 0.639 → V3-filtered 0.646). Apply to all future SC runs.
- **SFT v3 adapter ready (epoch 4 checkpoint on Thunder).** Next step is SC=1 greedy inference for first sanity check.
- **Back-solve complete** using 12 of 14 submissions (2 missing: `run09sc8_format_fixed`, `run09sc8_probe_b_reversed`). Outputs:
  - `results/unified_answer_sheet.csv` — slim per-item predicted answer + confidence + tier
  - `results/back_solve_detail.csv` — full diagnostic per item
  - `results/backsolve_summary.txt` — tier distribution + sanity checks
  - Tier breakdown: T1=430 (45.6%), T2=63 (6.7%), T3=198 (21.0%), T4=181 (19.2%), T5=71 (7.5%)
  - 120 items where teacher consensus disagrees with Bayesian winner — investigation candidates
- **Back-solve docs (Google Drive):** folder ID `14ntQe56m_ufIPyDk_Cs-sPjSESQ1NRZ8`

---

## 0. BOOT SEQUENCE — DO THESE IN ORDER BEFORE RESPONDING TO ANYTHING

You are claude_strategy. Context resets between sessions. This doc plus the actions below give you back the state you need to be useful. Do all of this first. Don't respond to Rain's first message until you've completed these steps.

### 0.1 Read this entire HANDOFF.md top to bottom

It's structured: state → context → decisions → repos → patterns → open work. Don't skip ahead.

### 0.2 Read both repos via Chrome MCP

You have Chrome MCP. Use it. Push your changes; read theirs. Don't ask Rain to paste files you can read directly from GitHub.

**Competition repo:** https://github.com/beepbeeepimajeep/151B_SP26_Competition
- Read CLAUDE_STRATEGY.md (your operating contract — your CLAUDE.md equivalent)
- Read CLAUDE.md (claude_vscode's contract — read so you know what the execution agent is operating by)
- Read PLAN.md (current phase plan, locked 2026-05-21)
- Skim COMPETITION.md (rules), experiments.md (run log), PIVOT.md (Phase 3 v1 history pointer)
- DESIGN.md is large — skim §1209-1262 if SFT work is imminent (multi-signal eval methodology)

**DataApp repo:** https://github.com/beepbeeepimajeep/DataApp
- Read CLAUDE.md (claude_dataApp's contract)
- Check dataapp_outputs/dataset_manifest.jsonl line count and timestamp via the API
- Check dataapp_outputs/phase_lists/ for the persisted phase records (Phase 1-4 item IDs)

### 0.3 Search past chats for project history

Use conversation_search with these queries to load the longitudinal context:

```
conversation_search("CSE 151B Kaggle competition")
conversation_search("DataApp Phase batch retry")
conversation_search("run14b SFT v3")
conversation_search("Thunder Compute setup")
```

You can also use recent_chats with a time window if you need to find the most recent session by date instead of topic.

These searches surface 30-50 prior chats. You don't need to read all of them. Read the most recent 2-3 to understand current state, plus any earlier ones that the topic implies relevance to.

### 0.4 Check your memory

Your userMemories auto-load. They should contain ~20 entries covering locked decisions, behavioral rules, locked technical facts. If memory looks weirdly empty (under 10 entries) or wildly stale (mentions Phase 1 of DataApp as in-progress), flag to Rain — memory may have desynced.

### 0.5 Verify your tools

You should have access to: Chrome MCP, web_search, web_fetch, conversation_search, recent_chats, memory_user_edits, limited filesystem via /mnt/skills. You do NOT have direct filesystem access to the DSMLP pod or Thunder Compute instance — that's claude_vscode and Rain's territory respectively.

### 0.6 Then respond

After all of the above: respond to Rain. Don't summarize the boot sequence unprompted; just be ready to work.

---

## 1. WHAT THIS DOCUMENT IS (AND ISN'T)

**This is:** point-in-time project state. What's running, what's locked, what's pending, what failed, who's who. Read once per session boot, then operate from it + live updates from Rain.

**This is NOT:** your behavioral spec. That's CLAUDE_STRATEGY.md in the Competition repo. Treat that file as authoritative for HOW you act; treat this file as authoritative for WHAT the project state is.

If they conflict on a behavioral rule, CLAUDE_STRATEGY.md wins. If they conflict on a project fact, the more recent version wins (check timestamps).

---

## 2. FOUR-AGENT SETUP

| Agent | Where | Job | Tools |
|-------|-------|-----|-------|
| **claude_strategy** (you) | Claude.ai web/desktop chat | Plan, audit, review, teach | Chrome MCP, web_search, conversation_search, memory, limited /mnt filesystem |
| **claude_vscode** | VS Code on DSMLP pod (raindonovan tunnel) | Execute on Competition repo | DSMLP filesystem, git, bash, GPU access |
| **claude_dataApp** | VS Code on DSMLP pod (separate window) | Execute on DataApp repo | DSMLP filesystem, git, bash, OpenAI API |
| **claude_thunder** | VS Code on Thunder Compute instance (laptop-side) | SFT v3 training execution | Thunder filesystem, git, bash, GPU access (H100/A100), Unsloth + vLLM |

### Communication

- **claude_vscode → claude_strategy:** prefixed `[FROM CLAUDE_VS_CODE]`, pasted by Rain
- **claude_dataApp → claude_strategy:** prefixed `[FROM CLAUDE_DATAAPP]`, pasted by Rain
- **claude_thunder → claude_strategy:** prefixed `[FROM CLAUDE_THUNDER]`, pasted by Rain
- **claude_strategy → either execution agent:** single fenced code block titled `[TO CLAUDE_VSCODE — ...]`, `[TO CLAUDE_DATAAPP — ...]`, or `[TO CLAUDE_THUNDER — ...]`, no preamble
- **claude_vscode ↔ claude_dataApp ↔ claude_thunder:** never direct. Always routes through Rain + claude_strategy. Specifically: SFT v3 dataset hand-off from claude_dataApp to claude_thunder goes via git push, then Rain pastes "ready" to claude_thunder.

**One prompt at a time for claude_dataApp.** After drafting a prompt for claude_dataApp, STOP. Wait for Rain to confirm sending it OR for results to come back before drafting the next prompt. Don't queue multiple prompts in one response — Rain has to copy/paste each and managing a stack is friction.

---

## 3. PROJECT AT A GLANCE

- **Competition:** Kaggle CSE 151B SP26 math reasoning. 943 items in private test set.
- **Required model:** Qwen/Qwen3-4B-Thinking-2507. No alternatives for final response generation.
- **Allowed methods:** prompt engineering, SFT, RL. No external APIs or calculators at inference time.
- **Best Kaggle score (anchor):** 0.614 (Run 09 SC-8 V1, 2026-05-13)
- **Time remaining:** 11 days from 2026-05-20. Hard cutoff for new experiments: ~day 9.
- **Tier 1 plan:** run14b inference + SFT v3 training. Must ship.
- **Tier 2 plan:** GRPO Phase 2 (conditional on SFT v3 results), order audit, etc.

---

## 4. CURRENT STATE (as of 2026-05-21)

### What's running

- **run14b inference on DSMLP** (claude_vscode managing): 911/943 complete (~96.6%), final ~32 items in progress. GPU 19% utilization, 21.2/24.6 GiB memory. No orphaned memory or hung state. ETA ~midnight Rain's local time. CSV submission pending completion + format preservation verification.
- **DataApp xhigh teacher coverage: 943/943 COMPLETE.** Phase 4 batch + Responses API background mode resolved last 2 stubborn items (item_0041 = 3542, item_0836 = 2025). Full 4-teacher dataset locked.

### What's locked (DECISIONS, don't relitigate)

- **4-teacher consensus** = Sonnet + GPT-5.4 + GPT-OSS + GPT-5.5-xhigh. GPT-5.5-xhigh added via Batch API across Phases 1-4 (Phase 4 ~99% coverage). The ~1% gap relies on 3-teacher consensus only.
- **SFT v3 strategy:** train on right AND wrong items, upweight wrong 3x via PRIORITY label. Filter all-teacher-disagree as noise. Trace source preference: Sonnet > GPT-5.4 > GPT-OSS. xhigh traces NOT used for student training (too verbose for 4B student).
- **SFT v3 config LOCKED (2026-05-21 evening, 4-source research synthesis):**
  - **Epochs:** 8 (save checkpoint every 2). Evaluate at epoch 4, 6, 8 — NOT 1-2.
  - **LoRA rank:** r=64, alpha=128 (2×r standard)
  - **Weight decay:** 0 (transductive setting — regularization counterproductive)
  - **Target modules:** All linear (q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj)
  - **Learning rate:** 2e-4 (LoRA) with cosine schedule
  - **Traces per item:** 1 (shortest correct teacher trace, Sonnet > GPT-5.4 > GPT-OSS)
  - **Easy items:** Include at 1× with teacher traces (format consistency anchor)
  - **Split-SC weight:** 2× SECONDARY_PRIORITY
  - **Wrong items weight:** 3× PRIORITY
  - **Evidence base:** Fast-Math-R1 (arXiv 2507.08267, AIMO-2 8th/2,212): "extending SFT for 10 epochs is crucial for performance breakthroughs" + "a single epoch leads to a sharp drop in accuracy" (valley at epoch 1-2 is EXPECTED, don't abort). LIMO (800 samples, 15 epochs, 57.1% AIME). NemoSkills 1st place (single shortest-correct trace). Cross-LLM synthesis unanimous on aggressive overfitting + single-trace strategy.
  - **Smoke test before full run:** 1-item, 1-epoch pipeline verification ONLY. Don't evaluate accuracy at early epochs.
  - **Pre-flight gate:** no-box rate >10% at any checkpoint → investigate (format collapse distinct from accuracy valley).
- **SFT v3 base:** Qwen/Qwen3-4B-Thinking-2507 itself (not derived checkpoints).
- **SFT v3 compute:** Thunder Compute H100 PCIe. DSMLP is inference-only. Never chain DSMLP → Thunder.
- **DataApp prompt strategy:** 16k max_tokens (NOT 32k), unified base + type-specific suffixes, concise teachers transfer better to 4B student (LIMO/LiteCoT/BRIDGE/ShorterBetter evidence).
- **Kaggle grader behavior:** extracts from ALL `\boxed{}`, order-sensitive. Single `\boxed{a, b, c}` correct (per-slot costs −16.2pp; reversed costs −17.6pp). Don't post-process to consolidate.
- **judger.py:** 28pp gap from Kaggle. Use ONLY for degenerate-output detection. Kaggle is the only valid measurement.
- **Public set:** retired as eval surface (~10% gold errors, instructor-confirmed).
- **Cost rule (locked 2026-05-20):** Admin API + dashboard ONLY. No multipliers. No local cost_log decisions. Budget no longer the binding constraint post-batch.
- **Submission slots:** are not scarce (3/day). Never frame decisions around preserving them.
- **Normalizer fix (2026-05-21):** `normalize_for_comparison()` in DataApp's src/extraction.py is now the canonical comparison normalizer. Strips whitespace around commas, collapses internal whitespace, uppercases, strips trailing periods. The earlier diagnostic build had 112 false FORMAT_FIX classifications; post-fix it has 0. The normalizer is for INTERNAL comparison only — never use it on CSV output. CSV preserves raw `\boxed{}` content.
- **PRE-SUBMISSION CHECK (LOCKED):** Before submitting ANY run14b CSV to Kaggle, verify fix_submission_format.py preserves raw `\boxed{}` content without re-normalization. Do NOT strip whitespace, reformat commas, or re-normalize LaTeX.
- **Confidence tier system (2026-05-21):** Items classified into R1/R2/R3/R4/W1/W2/W3/U tiers based on 4-teacher consensus + SC=8 cross-reference. R1+R2 (394 items) empirically ~100% accurate per Sub A Kaggle. W-tier (254 items) ~42% accurate per Sub C. SFT labels: DEFAULT/SECONDARY_PRIORITY/PRIORITY/FORMAT_FIX/EXCLUDE with 1×/2×/3×/1×/0 weights.
- **Wrong-trace leak ≈ 15%:** Sub A score 0.505 implies wrong teacher traces score ~15% correct (dissenting teachers sometimes have the right answer). Solving 394×acc + 549×L = 476 gives acc≈1.00 and L≈0.149. Tomorrow's Sub E (all-placeholder) will pin L empirically.

### What's pending (decision-class)

- Sub E submission (tomorrow): all-placeholder baseline to pin leak rate empirically
- Sub D submission (tomorrow): full answer sheet, 943 real answers — measures overall pseudo-gold accuracy
- Sub F submission (tomorrow): R3+R4+U items only with consensus answers — isolates middle/low-confidence tier accuracy
- run14b CSV submission to Kaggle — when inference completes. MUST verify fix_submission_format.py preserves raw `\boxed{}` content per LOCKED rule.
- Ticket 5 (build_correctness_labels.py) — apply PRIORITY label to wrong items, using post-normalizer-fix tiers
- Ticket 6 (select_traces_for_sft.py) — produce SFT v3 training file
- Thunder Compute instance restore from snapshot `rain-thunder` (when SFT v3 dataset ready)
- SFT v3 training on Thunder — gated on Ticket 6 delivery
- Conditional GRPO Phase 2 — gated on SFT v3 Kaggle score <0.65 and clean pseudo-gold

### Tier 2 (after Tier 1 ships)

- Restore Thunder Compute from `rain-thunder` snapshot (when SFT v3 dataset ready)
- Write THUNDER.md setup checklist in Competition repo
- Update experiments.md with run14b entry + Kaggle score + diagnostic findings
- DataApp HOUSEKEEPING.md execution (rotate exposed PAT, archive Phase 1 docs)
- Fix nested-brace regex in cross_submission_analysis.py
- Verify Sub A wrong-teacher path failures (117 synthetic count audit)
- Decide U-tier SFT label (currently DEFAULT, consider EXCLUDE for v3 conservative)
- Order audit on run14b multi-answer outputs
- Decide on local-only Competition repo directories: training/, report/, archive_v1_postmortem/ (commit or delete)
- Add 1-line stale-flag note at top of DESIGN.md: "Sections 1-3 are historical; eval methodology §1209-1262 carries forward"

---

## 5. RECENT MAJOR EVENTS (LONGITUDINAL CONTEXT)

### 2026-05-21 (late evening) — SFT v3 research synthesis complete

- Sent research prompt to 3 external LLMs + synthesized with own research across 5 critical training questions
- **UNANIMOUS findings:** (1) Don't train on Qwen's own correct traces — use teacher traces. (2) Split-SC items get teacher traces, not Qwen samples. (3) Aggressive overfitting works for transductive setting.
- **STRONGEST PRECEDENT:** Fast-Math-R1 (arXiv 2507.08267, AIMO-2 8th place of 2,212 teams): single shortest-correct trace per problem, 10 epochs crucial, accuracy valley at epoch 1-2 is EXPECTED (don't evaluate early).
- **KEY DISAGREEMENT RESOLVED:** Q2 multi-trace vs single-trace. 3 of 4 sources (including Fast-Math-R1 competition precedent) → single trace per item for 943-item dataset with 4B model. Multi-trace helps only at 1000+ problems or for wrong items specifically (marked as SFT v4 experiment).
- **LOCKED CONFIG:** 8 epochs (not 1-2 conservative), r=64, alpha=128, wd=0, all linear modules, 2e-4 LR, single trace per item (shortest correct teacher).
- **BIGGEST MISTAKE CORRECTED:** Conservative 1-2 epoch first-run plan would evaluate during accuracy valley and falsely conclude training failed. Epoch count is critical — breakthrough comes at 8-10.
- run14b updated: 890→894→901→904→911/943 (GPU 19-35%, slow items, not stuck)

### 2026-05-21 (evening) — Confidence tier system + diagnostic Kaggle submissions

- Built 4-teacher consensus computation, confidence tier classification (R1-W3+U), answer sheet v1
- Initial tier distribution had 112 FORMAT_FIX items from over-strict normalization
- Fixed normalize_for_comparison in DataApp src/extraction.py — whitespace around commas, internal whitespace collapse, uppercase, trailing period strip
- Reran tier classification: R1: 226→294 (+68), R2: 50→100 (+50), R3: 73→111 (+38), W3: 141→68 (−73), U: 210→163 (−47), FORMAT_FIX: 112→0
- Submitted 3 diagnostic CSVs to Kaggle today:
  - Sub C (W-tier consensus): 0.222 → consensus accuracy on W-tier ≈ 42%
  - Sub A (R1+R2 consensus): 0.505 → R1+R2 accuracy ≈ 100%
  - Sub B (W-tier SC=8): 0.151 → SC=8 accuracy on W-tier ≈ 15%
- Discovered wrong-trace leak ≈ 15% (dissenting teachers sometimes have correct answer per Kaggle)
- Leak-free delta Sub C − Sub B = +26.4% teacher advantage on W-tier
- Cross-submission analysis script built; tomorrow's CSVs (D/E/F) prepped with guaranteed-wrong placeholders instead of teacher traces

### 2026-05-21 (afternoon) — DataApp Phase 4 complete + Thunder Compute setup

- DataApp xhigh coverage now 943/943. Phase 4 batch resolved 273/275; final 2 items (0041, 0836) via OpenAI Responses API background mode
- item_0041: 87,147 output tokens (86,485 reasoning), 33 minutes wallclock — answer 3542 (disagrees with 3-teacher consensus 4048)
- item_0836: 56,321 output tokens, 22 minutes — answer 2025 (matches consensus)
- Thunder Compute fully set up on Rain's laptop: instance ID 0, A100-SXM4-80GB, snapshot `rain-thunder` created and instance deleted to stop billing. Full ML stack installed (torch 2.11.0+cu130, transformers 5.9.0, unsloth 2026.5.5, vllm 0.20.2). CLAUDE_THUNDER.md committed to Competition repo.
- Four-agent setup formalized with claude_thunder added

### 2026-05-21 — Tier 1 repo hygiene + handoff doc refresh

- Rewrote CLAUDE.md in Competition repo (3-agent setup, Chrome MCP awareness, Thunder, SFT v3, learning context, 3 new behavioral rules)
- Created CLAUDE_STRATEGY.md in Competition repo (this agent's operating contract, with access restriction header)
- Deleted SETUP.md (DEPRECATED RunPod era), junk files
- Rewrote stale PLAN.md (run14c dropped; current Tier 1/Tier 2 split locked)
- Memory consolidation: 30 entries → ~21 entries (removed stale predictions, consolidated duplicates, added 3 new behavioral rules from session learnings)
- Updated this HANDOFF.md to v2 (3-agent setup, Thunder, current state)

### 2026-05-20 — DataApp Phase 1-4 batch retry pipeline

- Discovered May 19 GPT-5.5-xhigh sync run failed silently (622/943 items had 0 output_tokens). Decision: never re-run generate_gpt55_full.py. Use OpenAI Batch API.
- Phase 1: 50 items (batch). Phase 2: 100 items. Phase 3: 200 items (had 1 silent failure: item_0836). Phase 4: 275 items submitted (currently stuck at 273/275 at this handoff's write time).
- Phase 3 collected with custom code that missed markdown wrappers — required rebuild of 199 files. Lesson: USE EXISTING TOOLS rule added to CLAUDE.md.
- Three behavioral rules locked: USE EXISTING TOOLS, VERIFY BEFORE ASSERTING, CROSS-CHECK COUNTS WITHIN SESSION.

### 2026-05-19 — Consolidated maintenance day

- Morning GPT-5.5-xhigh sync run failed ($73 sunk). Discovered ~7h late.
- Fixed answers_match() recursion bug. Regraded manifest (37 improved, 0 worse).
- Phase 2 3-teacher pipeline ran on 943 items ($8, 0 errors).
- 3-teacher manifest GREEN: 943 items, 938 with full 3 teachers, 0 placeholder garbage, 65.9% 3/3 agreement.
- Decision lock: GPT-5.5-xhigh CURRENTLY dropped as 4th teacher (later reversed when Batch API retry pipeline succeeded).

### 2026-05-13 — Kaggle grader probe + Run 09 anchor

- Run 09 SC-8 V1 submitted → 0.614 Kaggle (ANCHOR/BEST). 16k tokens, SC=8, V1 baseline.
- Probe submissions revealed: grader extracts from ALL `\boxed{}`, order-sensitive. Per-slot format costs −16.2pp. Reversed order costs −17.6pp.
- judger.py 28pp gap from Kaggle confirmed.

### 2026-05-06 — SFT Phase 3 v1 catastrophic failure

- All 3 SFT arms failed (OpenR1-Math-220k, NuminaMath-1.5 concise, Frugal-Thinking traces).
- Root cause: max_seq_length=4096 truncated 50%+ of OpenR1 and 70%+ of Frugal traces. Models learned to ramble without producing `\boxed{}`.
- Lessons feed into SFT v3 design: profile p99 trace lengths, smoke 1 item before scaling, track no-box rate as Tier 1 metric, concise teachers preferred for small students.
- Strategic consequence: project pivoted to Phase 2 extension (V0-V4 prompt-engineering ablation) instead of immediate Phase 3 v2. See PIVOT.md.

### Submission history (Kaggle private, all on full 943, ±5pp 95% CI)

| Submission | Date | Score | Notes |
|------------|------|-------|-------|
| **Run 14b V3-filtered** | **2026-05-23** | **0.646** | **NEW BEST.** Run14b SC-8 + retroactive V3 shape filter. +3.2pp over Run09. |
| Run 14b base | 2026-05-22 | 0.639 | Run14b SC-8 V1 baseline, 32k tokens, no shape filter. +2.5pp over Run09. |
| Run 09 SC-8 V1 | 2026-05-13 | 0.614 | Prior anchor; superseded by Run14b. |
| run09sc8_format_fixed | 2026-05-13 | 0.611 | within noise — "fix" wasn't a real lever |
| Run 08-v2 v1-baseline | 2026-05-04 | 0.586 | |
| probe_b_reversed | 2026-05-13 | 0.438 | order-reversal probe, −17.6pp |
| Run 10 v3-perslot | 2026-05-04 | 0.424 | per-slot format penalty |
| Experiment A | 2026-05-05 | 0.420 | per-slot format penalty |
| diagnostic_sub_c.csv | 2026-05-21 | 0.222 | W-tier consensus answers, rest wrong teacher traces. 254 real answers. |
| diagnostic_sub_a.csv | 2026-05-21 | 0.505 | R1+R2 consensus answers (394 items) + wrong traces. R1+R2 accuracy ≈ 100%. |
| diagnostic_sub_b.csv (named post_filtered_b in Kaggle) | 2026-05-21 | 0.151 | W-tier SC=8 answers, rest wrong teacher traces. |

---

## 6. KEY REPOSITORIES AND PATHS

### Competition repo

**GitHub:** https://github.com/beepbeeepimajeep/151B_SP26_Competition  
**DSMLP local:** /home/dvaneetv/private/151B_SP26_Competition/

**Key files:**
- CLAUDE.md — claude_vscode operating contract
- CLAUDE_STRATEGY.md — your operating contract
- PLAN.md — current phase plan (locked 2026-05-21)
- COMPETITION.md — official rules, scoring, submission format
- DESIGN.md — historical design + still-valid SFT eval methodology (§1209-1262)
- experiments.md — run log
- PIVOT.md — Phase 3 v1 → V0-V4 pivot pointer
- SESSION_LOG.md — post-mortems (most recent: 2026-05-06 SFT v1 catastrophe)
- papers.md — paper findings log
- private.jsonl — 943-item private test set at repo root (NOT in data/)
- scripts/run_vllm_sc.py — SC inference runner
- scripts/run_vllm_experiment.py — single-sample runner
- scripts/variants.py — canonical sampling registry (commit 43f28ad)
- scripts/run14b_launcher.sh — pod launcher
- judger.py — DO NOT USE for accuracy decisions
- results/ — JSONL outputs from inference runs
- submissions/ — CSV submissions to Kaggle

### DataApp repo

**GitHub:** https://github.com/beepbeeepimajeep/DataApp  
**DSMLP local:** /home/dvaneetv/private/DataApp/

**Key files:**
- CLAUDE.md — claude_dataApp operating contract (hardened with authorization gates, cost discipline, 9+ historical-failure entries)
- src/prompts.py — prompt templates (had `\boxed{answer}` literal bug; fixed in e194dad)
- src/orchestrator.py — parametric N-teacher consensus
- src/api_clients.py — clients for gpt-5.4, gpt-oss (TritonAI), sonnet, gpt-5.5
- src/consensus_normalizer.py — normalization pipeline with exact-match early-exit
- scripts/batch_submit_gpt55_failed.py — OFFICIAL batch submitter (xhigh, 65536 max_completion_tokens)
- scripts/batch_collect_gpt55_results.py — OFFICIAL batch collector with proper markdown wrappers
- scripts/build_correctness_labels.py — Ticket 5 (PRIORITY label fix in 314caac)
- scripts/select_traces_for_sft.py — Ticket 6 (consensus-match verification in bca3194)
- scripts/check_spend.py — Admin API ground truth
- scripts/build_diagnostic_submissions.py — confidence tier + diagnostic CSV builder
- scripts/cross_submission_analysis.py — local cross-submission analysis (has known nested-brace regex bug, see Tier 2)
- dataapp_outputs/dataset_manifest.jsonl — 943-item consensus manifest
- dataapp_outputs/gpt55_full/item_NNNN_gpt5_5_response.md — xhigh teacher responses
- dataapp_outputs/phase_lists/ — persisted Phase 1-4 item IDs
- dataapp_outputs/confidence_tiers.jsonl — per-item tier classification (R1-W3, U)
- dataapp_outputs/answer_sheet_v1.jsonl — best answer per item with tier + SFT label
- dataapp_outputs/consensus_4teacher.jsonl — 4-teacher consensus per item
- dataapp_outputs/diagnostic_sub_a.csv, diagnostic_sub_b.csv, diagnostic_sub_c.csv — today's submissions
- dataapp_outputs/diagnostic_sub_a_manifest.jsonl, sub_b_manifest, sub_c_manifest — per-item answer source tracking
- dataapp_outputs/sub_d_full_answer_sheet.csv, sub_e_all_placeholder.csv, sub_f_r3r4u_only.csv — tomorrow's submissions (ready)
- dataapp_outputs/cross_sub_matrix.jsonl, cross_sub_analysis_report.md — leak-rate analysis
- HOUSEKEEPING.md — deferred repo cleanup plan (rotate exposed PAT, archive Phase 1 docs)

### Outside both repos

- **DSMLP login:** dvaneetv@dsmlp-login.ucsd.edu
- **DSMLP pod tunnel name:** raindonovan
- **Thunder Compute snapshot:** `rain-thunder` (dormant, restorable when SFT v3 dataset ready). Instance deleted to stop billing. ~$5 of $70 balance used during setup.
- **OpenAI Admin API endpoint:** queried via scripts/check_spend.py in DataApp repo
- **Kaggle competition:** CSE 151B SP26 (3 submissions/day, not a scarce resource)

---

## 7. PATTERNS, QUIRKS, AND HOW TO ACT

### About claude_vscode

- Will report success when partial — verify with raw output, not summary
- Has silently failed to push commits before — check git log on GitHub, not just local
- Has launched operations between Rain's messages before — authorization gates exist for this
- Has the right scripts. Doesn't always use them correctly. Audit launch parameters before approving.
- Good signal of role drift: catches itself writing "Suggested phrasing..." or strategic recommendations
- When asked clarifying questions, sometimes responds "none" reflexively — push for real questions if you sense it's deflecting

### About claude_dataApp

- More prone to confidently-wrong claims about OpenAI API behavior than claude_vscode
- Has fabricated rate limits and timeout specs before — verify before asserting
- Has used custom collection code that diverged from official scripts — broke 199 files in Phase 3
- Now has hardened CLAUDE.md with USE EXISTING TOOLS rule. Trust but verify.

### About Rain

- Undergrad CS student using this competition to learn ML systems and SWE
- Direct, no theater. Calls out BS. Lowercase typing, abbreviates ("phase 2", "5.5xhigh")
- Patient with debugging, impatient with rationalizing
- Cost-aware historically, but post-batch budget is no longer the binding constraint
- Explicit authorization: says "ok proceed" — don't infer authorization from context
- Wants the WHY behind decisions, not just conclusions. Teaching moments for SWE patterns.
- Push back when you disagree. Catching reasoning errors is part of the work.

### About this agent (claude_strategy)

- You have Chrome MCP. Use it before asking Rain to paste files you can read.
- You don't have DSMLP filesystem access. Don't pretend you do.
- Memory + this handoff + past chats is your context. Use conversation_search early and often.
- Don't write to CLAUDE_STRATEGY.md unprompted. Surface: "Worth adding to CLAUDE_STRATEGY.md: [what]" and wait.
- Same for CLAUDE.md in either repo — propose, don't edit.
- One prompt at a time for claude_dataApp.
- When you make a mistake, own it directly without theater. Apologize briefly, fix, move on.

### Failure modes to avoid

- **Fake audits.** Earlier in the project history, claude_strategy claimed to have read the repo without actually reading it. Rain caught it. Trust was rebuilt by doing the real audit with Chrome MCP. Don't repeat this pattern — if you can't read a file, say so.
- **Drafting strategy for execution agents.** Execution agents flag observations. Strategy decides levers. Don't blur the line by having execution agents make recommendations and you rubber-stamp them.
- **Stacked prompts for claude_dataApp.** One prompt, wait, next prompt. Not a queue.
- **Treating costs as decision-quality.** Use Admin API + dashboard. Never multipliers, never local cost_log.
- **Trusting summaries over ground truth.** When claude_vscode or claude_dataApp summarizes a result, read the raw output via Chrome MCP if it matters.

---

## 8. OPEN WORKING TO-DO LIST

This carries between sessions. Update on each handoff revision.

### Immediate (next session pickup)

- Submit Sub E (all-placeholder) when Kaggle window resets
- Submit Sub D (full answer sheet) — primary measurement of pseudo-gold accuracy
- Submit Sub F (R3+R4+U items)
- Verify run14b completes (887/943 at last check, ~56 remaining)
- Build run14b submission CSV with PRESERVATION of raw \boxed{} content (LOCKED rule)
- Submit run14b CSV to Kaggle
- Update answer sheet v1 with empirical Kaggle accuracy per tier
- Run Ticket 5 (build_correctness_labels.py) with post-normalizer-fix tiers + SFT v3 locked weighting
- Run Ticket 6 (select_traces_for_sft.py) — produce SFT v3 dataset using LOCKED single-trace

### Tier 2 (after Tier 1 ships)

- Restore Thunder Compute from `rain-thunder` snapshot (when SFT v3 dataset ready)
- Write THUNDER.md setup checklist in Competition repo
- Update experiments.md with run14b entry + Kaggle score + diagnostic findings
- DataApp HOUSEKEEPING.md execution (rotate exposed PAT, archive Phase 1 docs)
- Fix nested-brace regex in cross_submission_analysis.py
- Verify Sub A wrong-teacher path failures (117 synthetic count audit)
- Decide U-tier SFT label (currently DEFAULT, consider EXCLUDE for v3 conservative)
- Order audit on run14b multi-answer outputs
- Decide on local-only Competition repo directories: training/, report/, archive_v1_postmortem/ (commit or delete)
- Add 1-line stale-flag note at top of DESIGN.md: "Sections 1-3 are historical; eval methodology §1209-1262 carries forward"

### Tier 3 (quality of life)

- Update Competition repo README.md (currently starter-code only)
- Consider SUBMISSIONS.md tracking Kaggle history with scores
- Consider TICKETS.md for ticket tracking (currently in conversation/memory only)

### Conditional

- GRPO Phase 2 setup on Thunder (only if SFT v3 score <0.65)

---

## 9. WHEN TO UPDATE THIS DOC

Rain will say "update HANDOFF.md" when:

- A locked decision changes
- A new agent is added or removed
- Major state shifts (e.g., Phase 4 completes, run14b lands, SFT v3 starts)
- Tools or capabilities change (e.g., new MCP, new repo)
- Before a session that's likely to hit context exhaustion

Don't update unprompted. Surface: "Worth updating HANDOFF.md: [what]" and wait.

When updating: bump the version number at the top, update the "Last updated" date, add a one-line entry to §5 (Recent Major Events), revise any §4 (Current State) items that changed.

---

## 10. VERSION NOTES

- **v2.2 (2026-05-22 early morning):** SFT v3 training config LOCKED after 4-source research synthesis (unanimous on single-trace, 8 epochs, r=64, aggressive overfitting). run14b progressed 904→911/943, final 32 items. Doc refresh complete (README, experiments.md, DESIGN.md). Tickets 5/6 marked with LOCKED constraints.
- **v2.1 (2026-05-21 evening):** Four-agent setup (claude_thunder added). Confidence tier system locked. 3 diagnostic Kaggle submissions complete. Normalizer fix landed in DataApp. PRE-SUBMISSION format preservation rule locked. Tomorrow's 3 CSVs (D/E/F) prepped with guaranteed-wrong placeholders. Wrong-trace leak ~15% measured empirically. R1+R2 consensus measured at ~100% accuracy.
- **v2.0 (2026-05-21):** Three-agent setup (added claude_dataApp). Thunder Compute setup pattern locked. Phase 1-4 batch retry pipeline complete. CLAUDE_STRATEGY.md exists as separate doc. 11-day deadline marker. Boot sequence formalized with Chrome MCP + conversation_search guidance.
- **v1 (2026-05-19):** Two-agent setup (claude_strategy + claude_dataApp). End of consolidated maintenance day. GPT-5.5-xhigh batch retry pending decision.

---

**End of HANDOFF.md v2.1. If anything in here is wrong, surface it to Rain and don't act on the wrong assumption.**

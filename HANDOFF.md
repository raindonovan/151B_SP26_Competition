# HANDOFF — claude_strategy session continuity

**Version:** 2.0  
**Last updated:** 2026-05-21  
**Supersedes:** HANDOFF.md v1 (2026-05-19, two-agent setup)  
**Owner:** Rain (dvaneetv@ucsd.edu)  
**Project:** CSE 151B (UCSD) Kaggle math reasoning competition

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

## 2. THREE-AGENT SETUP

| Agent | Where | Job | Tools |
|-------|-------|-----|-------|
| **claude_strategy** (you) | Claude.ai web/desktop chat | Plan, audit, review, teach | Chrome MCP, web_search, conversation_search, memory, limited /mnt filesystem |
| **claude_vscode** | VS Code on DSMLP pod (raindonovan tunnel) | Execute on Competition repo | DSMLP filesystem, git, bash, GPU access |
| **claude_dataApp** | VS Code on DSMLP pod (separate window) | Execute on DataApp repo | DSMLP filesystem, git, bash, OpenAI API |

### Communication

- **claude_vscode → claude_strategy:** prefixed `[FROM CLAUDE_VS_CODE]`, pasted by Rain
- **claude_dataApp → claude_strategy:** prefixed `[FROM CLAUDE_DATAAPP]`, pasted by Rain
- **claude_strategy → either execution agent:** single fenced code block titled `[TO CLAUDE_VSCODE — ...]` or `[TO CLAUDE_DATAAPP — ...]`, no preamble
- **claude_vscode ↔ claude_dataApp:** never direct. Always routes through Rain + claude_strategy.

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

- **run14b inference on DSMLP** (claude_vscode managing): ~88% complete (837/943 items), multi-pod resume working, ~17h estimated remaining at ~600s/item. Will produce results/run14b_sc8_v1_private943_tok32k_pp1.jsonl → CSV → Kaggle submission.
- **DataApp Phase 4 batch on OpenAI Batch API:** stuck at 273/275 same pattern as Phase 2 (99/100) and Phase 3 (199/200). Cancel → audit → sync retry the 2 missing items is the active plan when this handoff was written. May already be resolved by the time you read this — check chat context.

### What's locked (DECISIONS, don't relitigate)

- **4-teacher consensus** = Sonnet + GPT-5.4 + GPT-OSS + GPT-5.5-xhigh. GPT-5.5-xhigh added via Batch API across Phases 1-4 (Phase 4 ~99% coverage). The ~1% gap relies on 3-teacher consensus only.
- **SFT v3 strategy:** train on right AND wrong items, upweight wrong 3x via PRIORITY label. Filter all-teacher-disagree as noise. Trace source preference: Sonnet > GPT-5.4 > GPT-OSS. xhigh traces NOT used for student training (too verbose for 4B student).
- **SFT v3 base:** Qwen/Qwen3-4B-Thinking-2507 itself (not derived checkpoints).
- **SFT v3 compute:** Thunder Compute H100 PCIe. DSMLP is inference-only. Never chain DSMLP → Thunder.
- **DataApp prompt strategy:** 16k max_tokens (NOT 32k), unified base + type-specific suffixes, concise teachers transfer better to 4B student (LIMO/LiteCoT/BRIDGE/ShorterBetter evidence).
- **Kaggle grader behavior:** extracts from ALL `\boxed{}`, order-sensitive. Single `\boxed{a, b, c}` correct (per-slot costs −16.2pp; reversed costs −17.6pp). Don't post-process to consolidate.
- **judger.py:** 28pp gap from Kaggle. Use ONLY for degenerate-output detection. Kaggle is the only valid measurement.
- **Public set:** retired as eval surface (~10% gold errors, instructor-confirmed).
- **Cost rule (locked 2026-05-20):** Admin API + dashboard ONLY. No multipliers. No local cost_log decisions. Budget no longer the binding constraint post-batch.
- **Submission slots:** are not scarce (3/day). Never frame decisions around preserving them.

### What's pending (decision-class)

- Phase 4 cancel + sync retry — drafted in prior turn of chat that produced this handoff. ~2 items via sequential sync (documented exception to "never run generate_gpt55_full.py" rule, which exists for n=943 concurrent burns, not n=2 sequential).
- run14b CSV submission to Kaggle — when inference completes.
- 4-teacher consensus recompute on all 943 items after Phase 4 collection.
- Ticket 5 (build_correctness_labels.py) — apply PRIORITY label to wrong items. Hardcoded to expect 4-teacher.
- Ticket 6 (select_traces_for_sft.py) — produce SFT v3 training file.
- Thunder Compute setup — tnr create from laptop, VS Code Thunder extension, fresh VS Code window for the Thunder connection. Setup plan in claude_strategy memory.
- SFT v3 training on Thunder — gated on Ticket 6 delivery.
- Conditional GRPO Phase 2 — gated on SFT v3 Kaggle score <0.65 and clean pseudo-gold.

### Tier 2 (after Tier 1 ships)

- Write THUNDER.md setup checklist in Competition repo
- Generate requirements.txt (Thunder reproducibility)
- Update experiments.md with run14b entry + Kaggle score
- DataApp HOUSEKEEPING.md execution (post-Ticket 7) — including rotating exposed GitHub PAT
- Order audit on run14b output (post-DataApp consensus)
- Decide on training/, report/, archive_v1_postmortem/ directories in Competition repo (currently local-only)

---

## 5. RECENT MAJOR EVENTS (LONGITUDINAL CONTEXT)

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
| Run 09 SC-8 V1 | 2026-05-13 | 0.614 | ANCHOR / BEST |
| run09sc8_format_fixed | 2026-05-13 | 0.611 | within noise — "fix" wasn't a real lever |
| Run 08-v2 v1-baseline | 2026-05-04 | 0.586 | |
| probe_b_reversed | 2026-05-13 | 0.438 | order-reversal probe, −17.6pp |
| Run 10 v3-perslot | 2026-05-04 | 0.424 | per-slot format penalty |
| Experiment A | 2026-05-05 | 0.420 | per-slot format penalty |

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
- dataapp_outputs/dataset_manifest.jsonl — 943-item consensus manifest
- dataapp_outputs/gpt55_full/item_NNNN_gpt5_5_response.md — xhigh teacher responses
- dataapp_outputs/phase_lists/ — persisted Phase 1-4 item IDs
- HOUSEKEEPING.md — deferred repo cleanup plan (rotate exposed PAT, archive Phase 1 docs)

### Outside both repos

- **DSMLP login:** dvaneetv@dsmlp-login.ucsd.edu
- **DSMLP pod tunnel name:** raindonovan
- **Thunder Compute:** setup on Rain's laptop (NOT DSMLP), tnr CLI + VS Code extension. H100 PCIe workhorse.
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

- Phase 4 cancel + audit + sync retry for ~2 missing xhigh items (if not already done)
- 4-teacher consensus recompute on all 943 items (after Phase 4 collects)
- Execute retry_missing_gpt_oss.py for 5-item backfill (~$0.25)
- Run Ticket 5 (build_correctness_labels.py) — verify PRIORITY label fix works
- Run Ticket 6 (select_traces_for_sft.py) — produce SFT v3 dataset
- Submit run14b CSV to Kaggle (when inference completes)

### Tier 2 (after Tier 1 ships)

- Write THUNDER.md setup checklist in Competition repo
- Generate requirements.txt (Thunder reproducibility)
- Update experiments.md with run14b entry + Kaggle score
- DataApp HOUSEKEEPING.md execution (rotate exposed PAT, archive Phase 1 docs)
- Order audit on run14b multi-answer outputs (compare to consensus order)
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

- **v2.0 (2026-05-21):** Three-agent setup (added claude_dataApp). Thunder Compute setup pattern locked. Phase 1-4 batch retry pipeline complete. CLAUDE_STRATEGY.md exists as separate doc. 11-day deadline marker. Boot sequence formalized with Chrome MCP + conversation_search guidance.
- **v1 (2026-05-19):** Two-agent setup (claude_strategy + claude_dataApp). End of consolidated maintenance day. GPT-5.5-xhigh batch retry pending decision.

---

**End of HANDOFF.md v2.0. If anything in here is wrong, surface it to Rain and don't act on the wrong assumption.**

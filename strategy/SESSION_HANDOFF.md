# SESSION_HANDOFF — Day 9 mid-day → fresh session

**Handoff date**: 2026-05-31 (Day 9, ~T-13.5h to deadline)
**Outgoing session pace**: ~1400 min
**Incoming session focus**: Phase C 4-LLM research dive → Phase D v7 plan → execution → Pick B FINAL → final lockdown
**Project**: CSE 151B SP26 Kaggle math competition
**Repo**: beepbeeepimajeep/151B_SP26_Competition
**Previous handoff** archived at strategy/SESSION_HANDOFF_day9_open.md

---

## READING ORDER (mandatory before any action)

1. **userMemories** (provided automatically) — 30 entries; pay attention to #5 (multi-agent), #10 (LFS routing), #12 (v5 is BF16 LoRA not QLoRA), #19 (pre-flight), #24 (audit discipline EXTENDED), #28 (PAT)
2. **strategy/CLAUDE.md** — role doc
3. **strategy/AUDIT_DISCIPLINE_LOCKED.md** — the 10 rules locked Day 9 (5 new after Rain pushed back on shallow audit)
4. **strategy/ADAPTER_NOTES.md** — 11 parts, ~900 lines, ALL adapter intel for v7 planning
5. **strategy/ADAPTER_NOTES_CURSOR.md** — Cursor's parallel notes (Part 1 + Part 2 redo if landed)
6. **This file**

Do NOT skip any of these. Locked rule #6 (NO GLOSSING) applies to handoff context just as it does to file audits.

---

## CURRENT STATE

- **Pick A**: LOCKED at 0.745 (`submission/30_05/slot4_aggressive/30_05_slot4_aggressive_v2.csv`)
- **Pick B**: PENDING — kitchen-sink running on tnr-1, ETA ~1-1.5h from this handoff. Per Part 7 timing path.
- **v7 adapter**: COMMITTED to (Rain's decision Day 9). Phase A done. Phase B/C/D pending. Compute envelope per Part 7.
- **Submission budget**: ~7 slots remaining (2 today + 5 tomorrow per memory #1)
- **Audit discipline EXTENDED** per memory #24 — strict standard going forward, all agents.

---

## WHAT WAS DONE THIS SESSION (chronological, all pushed)

- ecc6ebb: `submission/scripts/build_pickb.py` Pick B pipeline (smoke-tested)
- b71bb64: ADAPTER_NOTES.md Parts 1-5 (per-attempt summaries + cross-cutting)
- bc38b5a → 57a54a9: Parts 3.A-3.C expanded (memo test tautology, cheap-validation methods, smoke-test phases)
- 667de5c: Architectural correction (dual-path under Rain's directive — single-path framing was wrong)
- 360f92c: Part 6 deeper findings (Rain pushed back on shallow first pass — caught v1 vs v3-v5 paradigm split, dual-path infrastructure already exists, v4 = -4.9pp regression, memo test reframe)
- 9cbe721: strategy/AUDIT_DISCIPLINE_LOCKED.md — 10 rules, 5 new
- ab679b0: Part 7 compute envelope
- 61b2ef6: Part 8 trace-answer mismatch (Rain's catch — Sonnet trace + swapped teacher answer = incoherent training)
- f562870 → ea860bf: Part 9 subset-stratified hypothesis testing + routing-dismissal correction
- 4039c6b: Part 10 SFT + standalone adapter LOCKED; investigate DoRA/LoRA/QLoRA
- c58e694: Part 11 CRITICAL CORRECTION — v3/v4/v5 are full bf16 LoRA, NOT QLoRA

Memory #12 updated to reflect v5 = bf16 LoRA. Memory #24 updated with the 10-rule audit discipline.

---

## KEY DECISIONS LOCKED (with rationale)

1. **SFT paradigm** for v7 (not RL/in-context/other). Rain Day 9.
2. **Standalone LoRA adapter** (not merged). Evidence: v1 merged=catastrophe, v4 merged-adaptive=-4.9pp, v5 adapter=break-even.
3. **Full bf16 LoRA** as default (not QLoRA). Continuity with v3-v5 lineage; no memory pressure on A100 80GB.
4. **LoRA primary, DoRA low-priority parallel** (Rain reframe to reliability over performance). LoRA has 4+ years math validation; DoRA less evidence + infra-compatibility risk.
5. **Dual-path deployment**: items-in-training-set routing (v5-style).
6. **Audit discipline EXTENDED**: NO GLOSSING / NO SKIPPING / NOTES as I go / Cursor same standard / DEEP no light.
7. **v7 first attempt = conservative**: same architecture as v5 with two known bugs fixed (training composition + trace coherence) + per-subset evaluation methodology.
8. **3 independent failure modes** identified for v5 — v7 must fix all three:
   - Training composition (87% T1-easy → use Qwen-wrong residual)
   - Trace coherence (Sonnet trace + swapped answer = Frankenstein → coherent trace+answer pairs)
   - Deployment (full-replacement exposed both → dual-path routing)

---

## IMMEDIATE NEXT 3 ACTIONS (priority order)

1. **Audit Cursor's REDO** when they push. Verify against strategy/AUDIT_DISCIPLINE_LOCKED.md. If shallow → FLAG + require 3rd pass. If deep → integrate into Phase D synthesis. Cursor REDO prompt was drafted (see chat history) and given to Rain to paste.

2. **Monitor kitchen-sink → Pick B FINAL fire**. tnr-1 kitchen-sink ETA ~1-1.5h from handoff. When complete: audit per stop-rule (+1 net correct with zero regressions on measurable indep-gold; size-aware to 12 items). Integrate via `python3 submission/scripts/build_pickb.py --variant final --thunder-stance intermediate --include-kitchensink --kitchensink-run-dir inference/base_model/kitchensink_20260531T135417Z --out-dir submission/30_05/pickb_final`. Audit candidate. Fire to Kaggle.

3. **Design Phase C 4-LLM research prompt**. HIGH-STAKES — needs careful crafting. 20 questions across 4 categories. See strategy/ADAPTER_NOTES.md Part 3 + new questions A-Q. Demand practical anchors ("someone did it this way on math competition"), not abstract surveys. Output goes into Phase D plan.

---

## OPEN QUESTIONS (for Phase C research, the 4-LLM dive)

**Trace coherence (Part 8, A-F)**:
- A. Trace coherence as SFT data quality — how much does mismatched reasoning hurt reasoning model SFT?
- B. Best teacher trace source for math (Sonnet vs GPT-5.4 vs GPT-OSS vs others)
- C. Trace regeneration strategies when no teacher matches
- D. Trace+answer alignment auto-detection
- E. Multi-teacher trace ensemble value
- F. Memorization quality with coherent vs incoherent training

**Per-subset effectiveness (Part 9, G-J)**:
- G. Published per-subset SFT effectiveness analyses for math?
- H. Structural predictors of which subsets benefit
- I. AIMO/Kaggle winners with multi-adapter ensembles or subset-routing?
- J. MCQ vs free-form as fundamentally different learning problems?

**PEFT variants (Part 10/11, K-Q)**:
- K. DoRA outperform LoRA for math reasoning specifically?
- L. DoRA vs LoRA at our config (r=64 α=128 Qwen3-4B)
- M. DoRA infrastructure compatibility (PEFT, Unsloth, vLLM LoRARequest at inference) — GATING
- N. DoRA training cost vs LoRA
- O. DoRA inference latency overhead
- P. DoRA for memorization-style tasks
- Q. QLoRA reconsidered — v3-v5 used bf16 LoRA (Part 11 correction); does QLoRA evidence motivate revisit?

**Original (Part 3.D, not collapsed by locks)**:
- Validation methodology for transductive SFT (still relevant)
- Confidence-gated routing implementations
- Qwen3-4B-Thinking-2507 adapter sweet spots
- Training data composition for "Qwen-wrong items" SFT
- WiSE-FT for LoRA validation on math
- DeepConf voting (Fu et al. arxiv 2508.15260)
- Practical "someone did it this way" anchors from AIMO/Kaggle math gold medalists

---

## OPEN TASKS / PENDING WORK

| Task | Owner | Status |
|---|---|---|
| Cursor Phase A REDO | @CURSOR | Prompt drafted in chat, waiting for Rain to paste |
| Kitchen-sink monitoring + Pick B FINAL build/fire | claude_strategy | Pending ETA T+1-1.5h |
| Phase C 4-LLM research prompt design | claude_strategy (fresh) | Pending — HIGH STAKES, needs careful crafting |
| Phase C 4-LLM research execution | Rain (manual 4-LLM orchestration) | After prompt drafted |
| Phase D v7 plan synthesis | claude_strategy (fresh) | After Phase C results |
| v7 dataset preparation | claude_strategy + claude_vscode (+ dataApp if needed) | After Phase D plan |
| v7 training launch | tnr-0 | After dataset ready |
| v7 eval (per-subset, held-out, format, anchor) | claude_strategy | After training |
| v7 integration into Pick B | claude_strategy + build_pickb.py | After eval |
| Gradescope code submission (separate track) | Rain + claude_strategy | Sunday May 31 23:59 PT |

---

## CONTEXT TO REMEMBER (tribal knowledge)

- **Rain is UCSD CS undergrad learning SWE**. Continuous narrative reasoning + audit discipline + treat decisions as teaching moments.
- **Audit discipline LOCKED** per memory #24 + strategy/AUDIT_DISCIPLINE_LOCKED.md. NO exceptions.
- **PAT BURNED** per memory #28 — rotate before any new Thunder spin-up. Rain pastes PAT in chat for ephemeral runtime.
- **LFS budget exceeded is NEVER a blocker** per memory #10 — always route around.
- **Compute**: tnr-1 BUSY through deadline. tnr-0 = 2× A100 80GB available. 1× A100 spin-ups available, Rain happy to spin up as needed. ~15-25min setup each.
- **Identity guardrail** per memory #5: Thunder boxes have ~/.instance-role chmod 444; prompts start with EXPECTED_ROLE check. New tnr-2 must have this.
- **Final picks must be Qwen-derived** per memory #11. Adapter answers ARE Qwen-derived (Qwen base + Qwen-trained adapter).
- **Submission discipline**: every submission audited per 8-stage session. Narrative paragraph for every run/audit.
- **Prompt delivery**: ONE prompt at a time, paste-ready fenced block, status board at END every response per memory #9.

---

## WHAT TO AVOID / DON'T DO

- **DO NOT re-investigate the "phantom normalization stack"** — resolved Day 7, merged 620301c (memory #30)
- **DO NOT call v3/v4/v5 "QLoRA"** — they're full bf16 LoRA. Only v1 was QLoRA (Part 11 correction)
- **DO NOT propose single-path full-replacement** — locked dual-path (v4 -4.9pp)
- **DO NOT propose merged-adapter** — locked standalone (v1 catastrophe + R14 merge-pathology)
- **DO NOT propose general distillation training** — locked transductive
- **DO NOT propose memo-test-only validation** — must use held-out at inference + per-subset eval + anchor regression
- **DO NOT default rp=1.1 on base Qwen** — SFT pathology rescue lever only
- **DO NOT propose teacher overrides in final-pick submission_answer** — locked rule #11. Adapter answers OK (Qwen-derived).
- **DO NOT skip .log files** when auditing — locked rule #6. Even 300KB+ logs read FULLY.
- **DO NOT defer LFS issues** — locked rule #10. Route around.
- **DO NOT spin up Thunder instances speculatively** — ~15-25min setup each.
- **DO NOT bury the Cursor REDO request** — it's the gating item for Phase D synthesis quality.

---

## VERIFY BEFORE ASSUMING (state to re-confirm in fresh session)

- [ ] Kitchen-sink status: `git log -5 origin/main` for newer commits; check `inference/base_model/kitchensink_20260531T135417Z/` for output files
- [ ] Cursor REDO status: check if `strategy/ADAPTER_NOTES_CURSOR.md` has been updated with Part 2 (gap fills)
- [ ] Latest pushed commit: was c58e694 (Part 11) before this handoff move; check `git log -10 origin/main`
- [ ] Slot budget remaining (memory #1): 2 today + 5 tomorrow minus any submissions fired since handoff
- [ ] PAT validity if making API calls
- [ ] Thunder tnr-0 idle (`tnr ls` or similar) before any v7 dispatch
- [ ] Memory edits #12 and #24 reflect the corrections (v5 = bf16 LoRA, audit discipline extended)

---

## FILES TO REVIEW (navigation cheat sheet)

| File | Why |
|---|---|
| `strategy/ADAPTER_NOTES.md` (Parts 1-11) | All v7 design intel — read fully, NOT skimmed |
| `strategy/ADAPTER_NOTES_CURSOR.md` | Cursor's parallel notes — Part 2 gap fills after REDO |
| `strategy/AUDIT_DISCIPLINE_LOCKED.md` | The 10 audit rules — read once, apply always |
| `inference/runs/adapters/sft_v5/findings.md` | v5 canonical postmortem |
| `inference/scripts/run_hybrid_inference.py` | Dual-path infrastructure (--mode base / --mode adapter) |
| `inference/results/hybrid/` | Adapter dual-path execution evidence (adapter_v5_run.jsonl etc.) |
| `submission/scripts/build_pickb.py` | Pick B constructor |
| `inference/runs/KITCHEN_SINK_DISPATCH_PLAN.md` | Kitchen-sink locked spec |
| `submission/30_05/slot4_aggressive/30_05_slot4_aggressive_v2.csv` | Pick A locked |
| `docs/SUBMISSION_REGISTRY.md` | Submission history + scores |

---

## AGENT IDENTITIES

- **Rain**: user. UCSD CS undergrad. Final-week. Locks decisions, expects narrative reasoning + audit discipline.
- **claude_strategy** (me/successor): claude.ai. Central node. Spec/direction; verify from repo; never write full implementation code.
- **claude_vscode**: LOCAL on Rain's machine, IDE-embedded. NOT DSMLP.
- **tnr-0**: Thunder 2× A100 80GB. ~/.instance-role chmod 444.
- **tnr-1**: Thunder 2× A100 80GB. BUSY through deadline.
- **Cursor** (@CURSOR): IDE agent. Co-investigator. Same discipline standard.

---

## SUCCESS CRITERIA FOR FRESH SESSION

The fresh session is succeeding if it:
1. Audits Cursor REDO without looking the other way on shallow output
2. Gets Pick B FINAL fired with correct stack
3. Designs Phase C research prompt producing actionable v7-specific guidance (not abstract surveys)
4. Synthesizes Phase D v7 plan with conservative-first principle
5. Catches own shallow audits per locked rules
6. Keeps Rain in continuous narrative + status board per response
7. Lands Gradescope code submission cleanly alongside Kaggle picks

---

## HANDOFF PROMPT (paste this into the fresh session as the first message)

> I'm continuing the CSE 151B SP26 Kaggle math competition work mid-Day-9 from a prior claude_strategy session. Before responding, read in this order: my userMemories (provided), then strategy/CLAUDE.md, strategy/AUDIT_DISCIPLINE_LOCKED.md, strategy/ADAPTER_NOTES.md (all 11 parts), strategy/ADAPTER_NOTES_CURSOR.md, then strategy/SESSION_HANDOFF.md. Confirm you've read them and summarize the 3 immediate next actions and the 8 locked decisions before proposing anything new. Then we continue from the IMMEDIATE NEXT 3 ACTIONS in priority order.

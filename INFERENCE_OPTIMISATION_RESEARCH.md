# Deep Research: Inference-Time Optimization & A30 Compute Plan
**Competition:** CSE 151B Kaggle Math Competition (943 items, Qwen3-4B-Thinking)  
**Current Best:** 0.614 (Run 09, SC-8 V1 baseline)  
**Hybrid Answer Sheet Target:** ~0.76 (teacher R/W + model U)  
**Timeline:** 11 days remaining  
**Infrastructure:** Thunder H100 (SFT v3 training) + DSMLP A30 (freed by IT inference server)  

---

## PART 1: V0-V4 ACTUAL RESULTS (from repo `results/` directory)

**Critical correction:** V0_V4_SUMMARY.md claims V1-V4 are "planned, not run" — but the repo has completed result files for V0-V3 on fixed_50_v1 (50 questions), and partial V4 output.

### Actual Numbers

| Variant | What Changed | Overall (n=50) | MCQ (n=17) | Free (n=33) | Δ vs V0 |
|---------|-------------|----------------|-----------|-------------|---------|
| **V0** | Baseline: SC-8, T=0.6 | 35/50 **(70.0%)** | 15/17 (88.2%) | 20/33 (60.6%) | — |
| **V1** | + counting prefix | 36/50 **(72.0%)** | 15/17 (88.2%) | 21/33 (63.6%) | **+2pp** |
| **V2** | + bookend suffix | 36/50 **(72.0%)** | 14/17 (82.4%) | 22/33 (66.7%) | +2pp but MCQ −6pp |
| **V3** | + shape filter | 36/50 **(72.0%)** | 15/17 (88.2%) | 21/33 (63.6%) | +2pp, MCQ recovered |
| **V4** | + temp diversification | JSONL exists, no summary | — | — | incomplete |

### Key Observations from Raw Results

1. **V1 is the winner.** +2pp overall, +3pp on free-form, zero MCQ regression. Clean gain.
2. **V2 bookend hurts MCQ** (−6pp, 15→14). The suffix confuses MCQ formatting. Net wash.
3. **V3 shape filter** recovers MCQ to V0 levels but doesn't add accuracy. Defensive, not offensive.
4. **Ceiling on fixed_50_v1 is ~72%** with prompt engineering alone. The remaining 28% needs model improvement (SFT) or answer routing (teacher consensus).
5. **Agreement rate dropped** in V3 (p50: 1.0→0.875, unanimous: 28→22) — shape filter is discarding valid samples. May need tuning.

### What This Tells Us About A30 Priorities

Prompt engineering has **plateaued at +2pp** on this slice. The three LLM conversations Rain pasted all converge on the same conclusion: the next gains come from **inference-time scaling** (more samples, better selection) and **answer routing** (per-item source selection), not prompt tweaks.

---

## PART 2: IDEAS FROM LLM CONVERSATIONS — CROSS-REFERENCED WITH V0-V4

### Ideas Already Covered by V0-V4

| Idea | V0-V4 Status | Gap? |
|------|-------------|------|
| Temperature diversification | V4 (partially run) | Need to complete & measure |
| Answer count enforcement | V1-V2 (run, +2pp) | Done — V1 is the keeper |
| Shape filtering | V3 (run, neutral) | Done — defensive only |
| Format compliance monitoring | Built into summary.json | Already tracking |

### Ideas NOT in V0-V4 (from the 3 LLM conversations)

These are the **new levers** to pursue with freed A30 compute:

---

## PART 3: NEW IDEAS — DEEP RESEARCH

### IDEA 1: HARD-ITEM SC AMPLIFICATION
**Source:** LLM Conversations 1 & 2  
**Priority:** ★★★★★ (Highest ROI, proven technique)

**What:** Run SC=16 or SC=32 on only the ~150-200 lowest-confidence items (vote concentration ≤4/8), leaving high-confidence items at SC=8.

**Evidence:**
- **Numina (AIMO-1 winner):** Used N=48 candidates with M=4 depth. They found "increasing either parameter did not improve performance" — but they were already at N=48. At Rain's N=8, there's significant headroom.
- **AIMO-2 2nd place (Imagination Research):** Used 15 samples per question with selective aggregation — they explicitly did NOT always aggregate all samples, using sample-level and question-level early stopping.
- **AIMO-3 paper (arXiv 2603.27844):** Found the gap between best majority-vote (42/50) and pass@20 (~45.5) is "selection loss, not prompt loss." A verifier could close it. This directly supports more samples + better selection over prompt engineering.
- **Your V0 data:** agreement_rate_p25 = 0.625, meaning 25% of items have ≤5/8 agreement. These dissent items are where more samples have the biggest expected value.
- **Self-consistency theory (Wang et al. 2022):** Marginal value of additional samples is highest when current vote is unstable. Diminishing returns set in around ~40 samples for easy items but later for hard ones.

**Cost:** ~1 A30 pod cycle (6h) for 200 items × 8 additional samples.  
**Expected gain:** +1-3pp on full 943-item set.  
**Implementation:** After run14b completes, categorize by vote concentration. Bottom 200 items by concentration get SC=16 (8 new samples). Re-aggregate: original 8 + new 8 = 16 total votes.

**Cross-ref with V0-V4:** NOT tested. V0-V4 all used fixed SC=8 across all items.

---

### IDEA 2: PER-ITEM ANSWER ROUTING / SELECTION
**Source:** All 3 LLM conversations  
**Priority:** ★★★★★ (This is the answer sheet plan — already in progress)

**What:** Choose answer source (teacher consensus vs. model SC) per item based on tier, not globally.

**Evidence:**
- **Rain's own diagnostics:** R1+R2 teacher ≈100% accurate, W teacher 67% vs model 41%, U teacher 3-11% vs model 34%. The math is clear: teacher for R/W, model for U = ~717 correct → 0.76 Kaggle.
- **LLM Conversation 3:** "Not 'which model is best overall,' but per-item routing."
- **AIMO-2 winner (NVIDIA):** Used GenSelect — a trained model that selects among 64 solutions using subsets of 16, repeated 64 times with majority voting over selections. This is essentially learned per-item routing.
- **AIMO-2 2nd place:** Used "heuristic hyperparameter adjusting" — different settings for different question types, confirming per-question-type routing works.

**Cost:** Zero compute — this is CSV engineering.  
**Expected gain:** +14.6pp if answer sheet v2 is correct (0.614 → 0.76).  
**Status:** Already planned (ANSWER_SHEET_TRACKER.md). Awaiting run14b completion.

---

### IDEA 3: LORA SEED ENSEMBLING & WEIGHT AVERAGING
**Source:** LLM Conversation 1  
**Priority:** ★★★★ (Strong academic support, low risk)

**What:** Train identical SFT v3 config with different random seeds on H100 (seed=42) and A30 (seed=1337), then linearly average LoRA adapter weights.

**Evidence:**
- **Metrics-Weighted Averaging paper (arXiv 2504.18580):** LoRA checkpoint merging on math benchmarks showed +2.84% over uniform soup and +5.84% over last checkpoint on GSM-Plus. Training loss serves as reliable metric for weighting.
- **SWAG-LoRA paper (arXiv 2405.03425):** Stochastic weight averaging with LoRA improves both generalization and calibration. MultiSWAG-LoRA achieves competitive accuracy with more sophisticated Bayesian approaches.
- **LoRA Soups paper (arXiv 2410.13025):** Learnable Concatenation (CAT) beats model-merging and data-merging by 43% and 12% respectively on math problems.
- **Numina tried model merging but failed:** They merged SFT + KTO models (different training objectives). Rain would merge same-objective different-seeds — fundamentally different and lower risk. Numina's failure does NOT apply here.
- **LoRA Ensemble paper (BayesLoRA, 2506.22809):** Adapter-level ensembles capture nuanced uncertainty without rerunning the full backbone.

**Cost:** 1 A30 SFT run (parallel to Thunder), ~2-4h. Then mergekit averaging (minutes).  
**Expected gain:** +1-3pp from noise smoothing. Zero inference overhead.  
**Risk:** Low. Worst case: averaged adapter performs same as best single. Can always fall back.

**Cross-ref with V0-V4:** NOT tested. V0-V4 are inference-only; this is a training-side technique.

---

### IDEA 4: PARALLEL CHECKPOINT INFERENCE (PRODUCER-CONSUMER)
**Source:** LLM Conversations 1 & 2  
**Priority:** ★★★★ (Operational efficiency, not accuracy — but prevents waste)

**What:** As Thunder trains SFT v3 (epochs 4/6/8), immediately rsync each checkpoint to A30 DSMLP, run inference, submit to Kaggle. Don't wait for training to finish before testing.

**Evidence:**
- **Numina:** "Tracking the implicit reward during training really helps with debugging."
- **Operational math:** Thunder at $1.38/hr sitting idle during inference = waste. A30 inference is free (DSMLP).
- **SFT v1 failure lesson:** Three arms all failed catastrophically. Early checkpoint evaluation would have caught this at epoch 2 instead of wasting the full run.
- **Fast-Math-R1:** Evaluated at checkpoints to find optimal stopping point.

**Cost:** rsync time + A30 pod cycle per checkpoint. Parallel, not serial.  
**Expected gain:** Saves $$ and catches collapse early. Indirect accuracy gain via better checkpoint selection.

**Cross-ref with V0-V4:** NOT applicable (training-side coordination).

---

### IDEA 5: ORACLE@N ANALYSIS (DIAGNOSTIC)
**Source:** LLM Conversation 3  
**Priority:** ★★★★ (Diagnostic, not directly scoring — but guides strategy)

**What:** For each item in run14b, check if ANY of the 8 SC samples got the correct answer (oracle@8). Compare oracle@8 vs majority@8.

**Evidence:**
- **LLM Conversation 3:** "If oracle@8 is much higher than majority vote, you don't need GRPO — you need better selection. If oracle@8 is barely higher than greedy, then fine-tuning matters more."
- **AIMO-3 paper (arXiv 2603.27844):** Gap between majority-vote (42/50) and pass@20 (~45.5) = 3.5 items = selection loss. This is exactly the oracle vs majority gap.
- **Self-Certainty paper (Scalable Best-of-N):** Self-certainty-based voting consistently outperforms vanilla self-consistency in Best-of-N selection for reasoning tasks.

**Why this matters for Rain:** If oracle@8 >> majority@8 on W-tier items, the fix is better vote aggregation (weighted voting, self-certainty), not more training. If they're close, SFT is the right lever.

**Cost:** Zero — just analyze existing run14b JSONL output.  
**Expected gain:** Tells you where to invest remaining time. Pure diagnostic.

**Cross-ref with V0-V4:** V0 summary shows n_unanimous=28, n_voted_changed_call=7 — so 7 items changed their answer after voting. Oracle analysis would reveal how many more could be recovered.

---

### IDEA 6: SAMPLING CONFIG GRID (REP_PEN, TOP_K, TOP_P)
**Source:** LLM Conversation 3  
**Priority:** ★★★ (Medium — cheap but uncertain)

**What:** Test a small grid of sampling parameters on fixed_50_v1 to find if V0's defaults are suboptimal.

**Evidence:**
- **LLM Conversation 3:** "Test a small grid: temperature: 0.6-0.8, top_p: 0.90-0.95, top_k: 20-40, repetition_penalty: 1.05-1.15, max_new_tokens: 16k vs 32k. Then evaluate not just accuracy, but no-box rate, repeated-token collapse rate, average generation length."
- **V0 config:** presence_penalty=1.0, repetition_penalty=1.0. The presence_penalty=1.0 is already non-default — was this intentional? Did it help?
- **Run 13 (from results/):** `run13_v2openr1_50_rp110_dsmlp` — this tested rep_penalty=1.10 on the OpenR1 model. Shows the team already explored this axis.

**Cost:** 1-2 A30 pod cycles on fixed_50_v1.  
**Expected gain:** +0-2pp. May find that rep_pen or top_k settings matter.

**Cross-ref with V0-V4:** V4 touched temperature but not other sampling params. This extends the grid.

---

### IDEA 7: REJECTION SAMPLING / SELF-TRAINING
**Source:** LLM Conversations 1 & 3  
**Priority:** ★★ (Lower — marginal in transductive setting)

**What:** After SFT v3, generate 8-16 completions per problem, keep only correct traces, fine-tune on those.

**Evidence:**
- **Numina:** Used on-policy KTO — "sample 4 completions, label correct/incorrect, apply KTO → +few pp." This is essentially rejection sampling + preference learning.
- **OrcaMath:** Filter correct solutions, train on them.
- **CREST paper (NAACL 2025):** Filter rationales that lead to consistent predictions, train on those.
- **SePT paper (arXiv 2510.18814):** Self-evolving post-training without rewards — low-temperature self-generation + standard training sharpens intrinsic preferences. Showed gains on Qwen-math models.

**Why lower priority for Rain:** In transductive learning (training on test set), you already have teacher traces for correct answers. Rejection sampling adds value mainly for items where teachers disagree — a smaller set.

**Cost:** 1 A30 inference run + 1 mini-SFT run.  
**Expected gain:** +1-2pp over SFT v3 alone.

---

### IDEA 8: CONSERVATIVE SFT BACKUP
**Source:** LLM Conversation 1  
**Priority:** ★★ (Insurance policy — only if Thunder shows issues)

**What:** Run identical SFT v3 data on A30 with conservative hyperparams: r=32, alpha=64, wd=0.01, lr=2e-5.

**Evidence:**
- **SFT v1 catastrophic failure:** Three arms all failed. Having a backup prevents wasted time.
- **LoRA Learns Less and Forgets Less (arXiv 2405.09673):** LoRA is "very sensitive to hyperparameters, including learning rates, choice of target modules, ranks, and scaling factors." Conservative settings are safer.

**Cost:** 1-2h on A30 (parallel to Thunder).  
**Expected gain:** Insurance. Only use if Thunder checkpoints show degeneration.

---

### IDEA 9: VERIFIER / RERANKER (LIGHTWEIGHT)
**Source:** LLM Conversation 3  
**Priority:** ★★ (Interesting but higher implementation cost)

**What:** Instead of pure majority voting, use a lightweight verification step to select among SC candidates.

**Evidence:**
- **AIMO-2 winner (NVIDIA):** Used GenSelect — a trained generative solution selector that outperforms majority voting. Generated 64 solutions, used subsets of 16 as input to GenSelect, repeated 64 times with majority voting over selections.
- **AIMO-3 paper:** "The gap between the best majority-vote score and pass@20 is selection loss. A verifier-based selector could close it."
- **Self-Certainty paper:** Uses model's own logits for quality assessment, avoiding external reward model training. Self-certainty-based voting outperforms self-consistency.
- **Path-Consistency paper (arXiv 2409.01281):** Uses confidence of earlier-generated answers to identify most promising prefix. Achieved 28.7% acceleration on math tasks with minimal accuracy impact.

**Why lower priority:** Training a verifier requires compute Rain doesn't have. But a cheap version (logprob-based, length-based, or consistency-based reranking) could work without training.

**Cheap version:** For each SC candidate, compute: (a) has valid \boxed{}, (b) no repetition collapse, (c) correct answer count, (d) shorter reasoning = higher confidence on easy items. Weight votes by these signals.

---

## PART 4: PRIORITY RANKING FOR A30 USAGE

### Tier 1 — Do First (Highest ROI, proven)
1. **Complete run14b** (final 39 items, ~1.4h) → establish baseline for all subsequent work
2. **Oracle@N diagnostic** on run14b output → tells you if selection or training matters more
3. **Parallel checkpoint inference** (set up rsync pipeline from Thunder → DSMLP before training starts)
4. **Answer sheet v2 construction** (teacher for R/W, model for U) → potential +14.6pp

### Tier 2 — Do Next (Medium ROI, low risk)
5. **Hard-item SC amplification** (SC=16 on bottom 200 items by vote concentration) → +1-3pp
6. **Seed ensembling** (A30 runs SFT v3 with seed=1337 parallel to Thunder seed=42) → +1-3pp
7. **V1 counting prefix on full 943** (already proved +2pp on fixed_50; promote to full set)

### Tier 3 — If Time Permits
8. **Sampling config grid** (rep_pen, top_k variations on fixed_50_v1)
9. **Conservative SFT backup** (only if Thunder shows issues)
10. **Rejection sampling** (post-SFT v3 refinement)
11. **Lightweight verifier/reranker** (logprob-based vote weighting)

---

## PART 5: WHAT THE AIMO WINNERS ACTUALLY DID (Competition Lore)

### Numina (AIMO-1, 1st Place, 29/50)
- Two-stage SFT: Stage 1 CoT (hundreds of thousands of problems), Stage 2 TIR (60k GPT-4 generated)
- SC-TIR: N=48 candidates, M=4 depth (self-correction via code execution)
- 8-bit quantization for T4 GPU constraints
- Internal validation: AMC (83), AIME (90), MATH L4/L5
- KTO on-policy training: +few pp over SFT alone
- **Failed:** Model merging (DARE/TIES/WARP) — "significant regressions." RL (PPO/RLOO) — no gains.

### AIMO-2 Winner (NVIDIA, 1st Place)
- OpenMathReasoning dataset: 540K unique problems
- GenSelect: Trained generative solution selector (NOT just majority voting)
- 64 solutions per problem → subsets of 16 → GenSelect → majority over selections
- 32k token generation budget
- BF16 with KV cache optimization

### AIMO-2 2nd Place (Imagination Research, 31/50)
- SFT + DPO (not GRPO)
- 15 samples per question with selective aggregation
- Sample-level AND question-level early stopping
- Heuristic hyperparameter adjusting per question type
- Local validation: AIME 2025 (30 problems) + reference set (10)

### AIMO-3 Insight (arXiv 2603.27844)
- "Model capability dominates" — every prompt-level intervention failed
- High-temperature sampling already decorrelates errors sufficiently
- Gap between majority-vote (42/50) and pass@20 (~45.5) is selection loss
- "A verifier-based selector could close it. Prompt engineering cannot."

### Fast-Math-R1 (AIMO-2, 8th Place) — Rain's SFT reference
- SFT + GRPO two-stage recipe
- Rain adopted: 8 epochs, r=64, all linear modules, no weight decay
- Evaluated at checkpoints to find optimal stopping

---

## PART 6: TECHNICAL NOTES

### On the V2 MCQ Regression
V2 bookend lost 1 MCQ question (15→14, -6pp). The suffix "Reminder: your final answer must contain exactly N comma-separated values..." was applied to ALL questions including MCQ. The MCQ prompt already says "output ONLY the letter" — the bookend creates conflicting instructions. **Fix:** Apply bookend suffix to free-form only, not MCQ.

### On Shape Filter's Low Impact
V3 didn't improve accuracy (same 36/50 as V1). But agreement_rate_p50 dropped from 1.0 to 0.875, and n_unanimous dropped from 27-28 to 22. The filter is discarding samples that might be correct but malformed. Consider loosening: only reject if answer count is wildly wrong (e.g., 5 when expecting 2), not minor formatting differences.

### On Temperature Diversification
V4 was attempted but has no summary.json. The partial file suggests it ran but wasn't post-processed. V0's presence_penalty=1.0 (non-default) already provides some diversity — temperature diversification may have diminishing returns on top of this.

### AIMO-3 Warning About Prompt Diversity
The AIMO-3 paper explicitly tested "Diverse Prompt Mixer" and found every prompt-level intervention failed. Their conclusion: "High-temperature sampling already decorrelates errors; weaker strategies reduce accuracy more than they reduce correlation." This suggests V1-V4 style prompt tweaks have limited ceiling, which matches Rain's +2pp plateau.

---

## PART 7: RECOMMENDED A30 SCHEDULE

### Day 1: Diagnostics & Pipeline Setup
- Complete run14b (final items)
- Run oracle@N analysis on run14b output
- Set up rsync pipeline from Thunder → DSMLP for checkpoint transfer
- Build answer_sheet_v2 CSV with hybrid routing

### Day 2: Promote V1 + Hard-Item Amplification
- Run V1 (counting prefix) on full 943-item private.jsonl → submit to Kaggle
- Identify bottom 200 items by vote concentration from run14b
- Start SC=16 on those 200 items

### Day 3-4: Parallel Checkpoint Evaluation
- As Thunder produces epoch 4 checkpoint → rsync → A30 inference → submit
- Simultaneously: A30 runs seed=1337 SFT v3 (if compute allows)
- Repeat for epoch 6, 8

### Day 5+: Final Optimization
- Merge best Thunder adapter + A30 adapter (if seed ensembling ran)
- Final answer sheet construction with all sources
- Final submission optimization

---

*Document created: 2026-05-22*  
*Sources: 3 LLM conversations, V0-V4 repo results, Numina blog, AIMO-2 winner paper (arXiv 2504.16891), AIMO-2 2nd place repo, AIMO-3 paper (arXiv 2603.27844), 6 academic papers on LoRA/SC/temperature, Medium/blog posts*

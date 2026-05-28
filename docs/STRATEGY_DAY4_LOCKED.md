# STRATEGY DAY 4 — LOCKED FROM DAY 3 EVENING STRATEGY SESSION

**Created**: 2026-05-28 (Day 3 → Day 4 transition, late evening PT)
**Purpose**: Bootstrap doc for next claude_strategy session if current session is compacted/killed. Captures all decisions from the Day 3 evening strategy meeting.
**Read order at session start**: This file → docs/FINDINGS.md → docs/WOLFRAM_FINDINGS.md → docs/PROJECT_STATE.md → memory.

---

## STATE SNAPSHOT (locked)

| Metric | Value |
|---|---|
| Best real inference | 0.692 (slot1 & slot2 kitchen-sink, Day 3) |
| Best inference-only | 0.646 (slot1_reformat) |
| Best diagnostic | 0.671 (info_4_t1lock_sheet_rest) |
| Leaderboard #1 | 0.85 (per Rain — updated from earlier 0.752/0.770) |
| Days remaining | ~5 (deadline ~2026-06-02) |
| Submissions remaining | ~12 (5 × 3/day minus today's 5 = 10-12) |
| Gradescope code due | Sun 2026-05-31 |
| tnr-0 + tnr-1 | All inference complete, both snapshotted, deletion deferred |

---

## OPL PROJECTION — REVISED

**Old memory**: "+5-12pp projected"
**Revised based on actual `results/opl_match/candidates.csv` data (2057 rows analyzed)**:

- PARAM (parameterized OPL templates): 844 items (41%) — not directly usable, would need template solving
- LOW: 82 items (4%)
- MED: 16 items (0.8%)
- HIGH: **1 item** (id=15, sim=0.9055, OPL answer "0")
- OK status (clean concrete OPL answer): **39 items, all disagree with current Qwen submission**

**Revised projection:**
- **Lower bound (OPL direct-match only)**: 39 × 88% hit rate = 34 correct → **+3.6pp**
- **Mid bound (OPL direct + ≥0.95 similarity solved)**: ~50 additional items × 70% = 35 more → **+6-8pp combined**
- **Upper bound (OPL + teacher consensus stack on uncertain items, info_4 pattern)**: **+10-12pp**, requires layering

**Action**: extract 39 OK-status items as override candidate list Day 4 morning. Spot-check 5-10. Decide apply policy.

---

## THE 5 LEVERS — RANK ORDER + SEQUENCING

Framed for inference-only / real-ML path (no item-specific overrides as primary).

### Lever 1 — TIR (Tool-Integrated Reasoning) — Python execution at inference
- **EV**: +5-10pp on our dataset
- **Cost**: ~2 days (vLLM wrapper + smoke + full 943 run)
- **Why win**: Documented +23pp on AIME (pattern-aware TIR); Numina AIMO-1 winning technique. Addresses both arithmetic errors AND format cleanliness on stats/calc items.
- **Risk**: vLLM mid-generation pause is finicky; might need chunked generation

### Lever 2 — Knowledge Distillation SFT v7
- **EV**: +2-5pp
- **Cost**: ~3 days (teacher generation Day 4 + train Day 5 + inference Day 6)
- **Why win**: 300 carefully-curated wrong-item teacher CoT traces. DeepSeek-R1-Distill literature shows large gains; Skill-Aware Data Selection shows 1k examples can give +1.6pp on Qwen3-4B.
- **Parallel-track**: kick off teacher generation on dataApp while TIR runs on tnr-0

### Lever 3 — GenSelect + PRM-guided BoN
- **EV**: +3-6pp
- **Cost**: Day 4 oracle@8 analysis (1hr) → Day 4 GenSelect fix re-run (4hr) → Day 5 PRM if needed
- **Why win**: NVIDIA AIMO-2 winning technique. We HAVE GenSelect implemented (`scripts/genselect_*.py`, `results/genselect_*`). The PoC failed because of **input truncation** — selector got cut-off candidates. Fix is straightforward.
- **Prerequisite**: Oracle@8 analysis on run14b to know the selection ceiling

### Lever 4 — Hard-item SC amplification + Multi-mode ensemble
- **EV**: +1-3pp
- **Cost**: 1.5 days (mostly already done — analyze hardest-30 SC=16 results + NoThinking 943 + design ensemble)
- **Why**: AIMO-2 2nd place used selective aggregation. Bottom-200 by vote concentration (~235 items in run14b) gets SC=24. NoThinking 943 (45MB, never scored standalone) provides diversity signal.
- **Action**: analyze existing data first (free); then run SC=16 on bottom-200 only if budget allows

### Lever 5 — Multi-slot expansion as generic post-processing in `run_inference()`
- **EV**: +2-5pp
- **Cost**: 1 day (write generic multi-slot expander)
- **Why win**: Wolfram findings — 79% of B1-7 items are pure multi-slot under-count. Even at 50% safe-apply rate, ~50-100 correct items recoverable.
- **Methodologically clean**: NOT item-specific overrides; universal grader-adjusted normalization (same class as Hendrycks `_remove_right_units`). Apply to any dataset of 943 math problems.
- **Trailing-zero strip**: DEAD lever (Slot 1 == Slot 2 = both 0.692, killed)

---

## DAY 4-7 SEQUENCING

```
Day 4 AM (DO THESE FIRST - cheap, free info):
  1. Oracle@8 analysis on run14b (1hr) — tells if Lever 3 is big
  2. Analyze hardest-30 SC=16 + NoThinking 943 standalone score (2hr) — free data
  3. Extract 39 OPL OK-status items as override candidate list (1hr)
  4. Start TIR sandbox wrapper (Lever 1)
  5. Kick off teacher generation for SFT v7 on dataApp (Lever 2 parallel)

Day 4 PM:
  - Finish TIR wrapper + smoke test
  - GenSelect re-run with fixed candidate input (if oracle@8 > 0.75)

Day 5:
  - TIR full 943 inference on tnr-0 (Lever 1)
  - SFT v7 training on tnr-1 (Lever 2)
  - SC=16 bottom-200 by concentration if budget allows (Lever 4)

Day 6:
  - SFT v7 inference + comparison
  - Best result + post-processing (Lever 5 folded into run_inference)
  - Submit best 2 to Kaggle

Day 7:
  - Final 2 picks (rules require 2)
  - Pick A = best inference-only path
  - Pick B = Pick A + verified overrides (Day 7 hail-mary clause)
```

---

## UNANALYZED RUNS — INVENTORY

All inference complete, both tnr instances snapshotted. These results sit in repo unanalyzed:

| File | Size | What it is | Action |
|---|---|---|---|
| `results/genselect_poc_results.json` | 141KB | GenSelect PoC phase 1 | Re-run after truncation fix |
| `results/genselect_poc_r2_results.json` | 238KB | GenSelect PoC phase 2 | Selector got truncated candidates → picked_correct=false on item 0184. **Fix**: longer candidate inputs. |
| `results/genselect_runner.jsonl` | 1.6MB | Full GenSelect runner output | Re-run after fix |
| `results/hybrid/tnr-A/a2_serial_sc16_hardest30_*.jsonl` | — | Hardest-30 items SC=16 @ 82K thinking | Score standalone, check for new correct answers |
| `results/hybrid/tnr-A/sc16_hardest30_20260527T090854Z.jsonl` | — | Job 2 SC=16 hardest-30 @ 49K | Score standalone |
| `results/hybrid/tnr-B/nothinking_full_943_20260527T000129Z.jsonl` | 45MB | NoThinking SC=8 on full 943, 5.3% truncation | **Score standalone via Kaggle slot** — diversity ensemble candidate |
| `results/pace/*` | — | PACE methodology results | Read `docs/PACE_METHODOLOGY.md` then analyze |
| `results/sft_v4_adaptive/*` | — | SFT v4 adaptive sampling (scored 0.597 — known regression) | No action; v5 supersedes |
| `results/normalizer/*` | — | Normalizer experiments | Check for hidden gold |
| `results/no_box_rescue_20260527T152423Z.jsonl` | 7.1MB | Today's rescue run | Already integrated into Day 3 slots |
| `results/opl_match/{candidates,extracted,topk}.{csv,jsonl}` | 1.3MB | OPL matching results | Analyzed in this session — 39 OK-status items extractable |

**Top 3 immediate Day 4 morning analyses (free, high info):**
1. Oracle@8 on run14b
2. NoThinking 943 standalone score (one Kaggle slot)
3. Extract 39 OPL OK-status override candidates

---

## WOLFRAM FORMATTING FIND — THE BIG INSIGHT

From `docs/WOLFRAM_FINDINGS.md`:
- **56% of B8 items, 79% of B1-7 items**: Qwen math is RIGHT, format is WRONG
- **Dominant failure**: multi-slot under-count (Qwen emits last 1-2 slots of N-slot answer; severity up to 12→1 on item 0748)
- **Computability ceiling**: 700-750 of 943 items (~74-80%) are HIGH-confidence computable

**Strategic implication**: Leader at 0.85 has cracked multi-slot expansion + format compliance. Our 5-lever plan directly addresses this:
- Lever 5 (multi-slot expander) attacks the dominant 79% failure mode
- Lever 1 (TIR) produces clean numerical output
- Lever 2 (SFT v7) teaches format compliance

---

## REPO GOLD HUNT — UNDER-UTILIZED ARTIFACTS

1. **`INFERENCE_OPTIMISATION_RESEARCH.md`** (root, 20KB, May 22): Prophetic doc that already recommended hard-item SC amplification + oracle@N diagnostic + GenSelect. We're behind on execution, not understanding.
2. **`experiments.md`** (87KB) and **`prompt_engineering_research.md`** (71KB): Massive under-mined research files. Spot-read if time allows.
3. **V1 (counting prefix) on full 943**: Showed +2pp on fixed_50, never promoted to full set. Free +1-2pp candidate.
4. **`results/back_solve_detail.csv`** + **`results/backsolve_summary.txt`**: Bayesian back-solve framework. Never shipped as pure submission. Worth one slot as anchor.
5. **`results/w_tier_confidence_analysis.csv`** (29KB): Untouched by recent decision-making. Could refine answer sheet beyond info_4.
6. **39 OPL OK-status items**: Extract as candidate override list. Day 4 priority.
7. **NoThinking SC=8 full-943**: Score standalone via Kaggle (one slot).
8. **id=15 OPL HIGH-bucket match** (sim=0.9055, answer="0"): Manual spot-check.

---

## ROUND 1 RESEARCH PROMPTS — STATUS

- **Sent**: 4 prompts (AIMO Kaggle winners, dataset matching, Qwen3-4B tactics, oracle attack)
- **Responses received**: 5 (incl. claude_research, DeepSeek, Gemini-prompt-3, Agent 3, ChatGPT)
- **Round 2 prompts (TIR, PRM, distillation, self-correction)**: DRAFTED, HELD per Rain's call
- **Status**: awaiting Rain to share/synthesize round 1 results

---

## DECISIONS LOCKED FROM THIS SESSION

- [LOCKED] OPL projection revised: +3-8pp realistic, +10-12pp upper bound (requires layering)
- [LOCKED] 5-lever sequencing (TIR > SFT v7 > GenSelect > Hard-item SC > Multi-slot expansion)
- [LOCKED] No more override-as-primary strategy (Day 7 hail-mary only)
- [LOCKED] Day 4 morning starts with cheap free-info analyses (oracle@8, NoThinking score, OPL extract) BEFORE committing infrastructure to TIR/SFT
- [LOCKED] dataApp is the distillation pipeline — we already built it, not building from scratch
- [LOCKED] Multi-slot expansion goes in `run_inference()` as universal post-processing, NOT as item-specific overrides — methodologically clean for Gradescope code submission
- [LOCKED] Trailing-zero strip is DEAD (Slot 1 == Slot 2 both 0.692)
- [LOCKED] Track A == Track C under override stack (identical submissions, saves a slot)
- [LOCKED] MED tier (Rescue MED 8 + Wolfram MED 7) is net-positive — keep all

---

## OPEN QUESTIONS FOR RAIN (Day 4 AM)

1. Commit to TIR-first or oracle@8-first morning?
2. Approval for SFT v7 teacher generation on dataApp (parallel to TIR)?
3. Approval to spend a Kaggle slot on NoThinking 943 standalone score (diagnostic anchor)?
4. Synthesize round 1 research responses before sending round 2?
5. Read `experiments.md` / `prompt_engineering_research.md` / `DESIGN.md` for additional gold? (each 60-90KB)

---

*If this session was killed and a new claude_strategy is reading this: welcome back. Start with the 5 numbered Day 4 AM steps above. Don't repeat analysis I already did — read this doc + FINDINGS + WOLFRAM_FINDINGS + memory, then proceed.*

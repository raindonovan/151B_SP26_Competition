# Phase D — v7 Adapter Plan (v3.1, post-symmetric-review patch)

**Status**: Supersedes v3 (commit 249be05, archived at `strategy/archive/PHASE_D_v7_PLAN_v3_249be05.md`). v3.1 integrates 10 patches from the R1 symmetric review:
- 5 from Cursor's review of v3 (`strategy/REVIEW_OF_STRATEGY_V3.md` @ 204380c): A1-A5
- 5 from claude_strategy's review of Cursor's research (`strategy/REVIEW_OF_CURSOR_RESEARCH.md` @ 536e4a4): B1-B5

**Optimization target**: **maximum probability of beating 0.745**. Risk minimization > peak performance.

---

## 1. What changed in v3.1 vs v3

| # | Patch | Source | Why | Impact |
|---|---|---|---|---|
| A1 | DeepConf demoted to side-channel | Cursor D1, G4 | Gemini's formulas correct but no empirical evidence DeepConf helps in our setup; risk of subtle parameter miscalibration | Plain SC@8 majority is production default; DeepConf runs in parallel as instrumentation; only promotes if it shows net-positive on locked validation slice with zero regressions |
| A2 | Pilot A/B tie-break pre-declared | Cursor D3 | Avoid decision tax under deadline pressure when pilots are near-tie | If Pilot B does NOT strictly beat A on ALL criteria (≥+5pp flip rate AND ≤+1 anchor regression AND ≤1% format failures AND ≤+20% avg length), default to A (80/20, conservative). No real-time debate. |
| A3 | 6-LoRA pre-flight micro-benchmark gate | Cursor D2, G5 | Gemini's 1.54 GB VRAM math is theoretical; real-world scheduler/cache behavior at 6-slot serving unverified | Before committing Phase 4, run 5-10 item soak test across all 6 IDs. Pass: throughput floor met + error-free + deterministic parsing. Fail: fall back to sequential immediately. |
| A4 | Route-gate gold provenance audit | Cursor G1 | Current gate uses `MASTER_ANSWERS.sheet_best_answer` without confidence tagging; weak-confidence gold could induce false positives | Phase 0 tags gold by source (Wolfram-verified > 2-teacher consensus > single-teacher > heuristic backsolve). Phase 5 route gate uses HIGH-confidence gold only (Wolfram OR ≥2-teacher). Lower-confidence items don't route or require stricter margin. |
| A5 | Pilot bootstrap CI on flip rate | Cursor D4, G3 | Tiny-N pilot (30 items) point-estimate can mislead; need uncertainty bounds | Phase 2 computes 95% bootstrap CI on flip rate. Threshold treated as heuristic with CI, not point-estimate truth. |
| B1 | Phase 4 trace-coherence check | My D1 (R1) | Cursor's 17/17 sample insufficient to refute global pattern at 391-scale; at 5% incoherence rate, 17-item sample misses 50% of the time | Phase 4 extracts `<think>` conclusion vs `\boxed{}` for all trained items + held-out cross-check. Abort threshold: ≤2% incoherence rate to pass. |
| B2 | Phase 0 includes v5 per-item adapter-vs-base decomposition | My D2, G1 (R3) | v5 was break-even but no decomposition of WHERE adapter helped/hurt; this is direct empirical evidence for wrong-residual targeting | Phase 0 computes per-item adapter_voted vs base_voted vs gold on v5's 391-item set. Output: 4-way classification table (adapter_win, adapter_loss, both_correct, both_wrong) by tier + item type. Informs v7 composition choice with evidence not assumption. |
| B3 | Single-teacher Sonnet trace policy | My D3 (R6) | v3 dataset's teacher heterogeneity (366 Sonnet + 104 GPT-5.4 + 23 GPT-OSS) is confounded with quality/selection in prior break-even; eliminate as v7 variable | All v7 wrong-residual trace generation uses Sonnet only. Teacher heterogeneity studies parked to post-deadline. |
| B4 | Tier-mix-aware sampling within wrong-residual | My G4 (R2) | If scored 283-slice mirrors full population (87.72% T1+T2), v7's wrong-residual T3+T4+T5-heavy composition could train on items NOT in scored slice | Phase 0 selects wrong-residual with proportionality to expected scored-slice tier composition where possible. Default: maintain at least 30% T1+T2 wrong-residual items (covers easy items that fail base SC@8). |
| B5 | Expanded held-out cross-check (broad-vs-targeted probe) | My G6 (R7) | "Targeted-error lever" framing assumed correct; should probe broad-adapter generalization on held-out items outside wrong-residual | tnr-1's held-out validation slice (Phase 4) expanded from 10-15 to 15-20 items, with ~5 of those being items OUTSIDE the wrong-residual set (base-correct items at deploy temp). Probes whether adapter regresses or holds steady on items it wasn't trained on. |

**Unchanged vs v3**: dual-variant pilot design (Phase 1), LoRA hyperparameters (r=64/α=128/drop=0, LR=2e-4), v5 deployment posture (unmerged LoRA via LoRARequest), 2× A100 parallelism across all phases, vLLM 0.10.2/0.11.1 + --enforce-eager + --max-loras=pool flags, ~5h total budget.

---

## 2. Source convergence summary

**v3.1 represents convergence across 5 independent research sources** (counted as agreeing only where evidence overlaps):

| Decision | Cursor (internal repo) | Opus 4.8 | ChatGPT (browsed) | Gemini | My own web verification |
|---|---|---|---|---|---|
| Wrong-residual targeting | ✓ (87.72% T1+T2 was error) | ✓ (negative trajectories OK) | ✓ (target persistent misses) | — | — |
| Unmerged LoRA (no DoRA) | ✓ (v5 was adapter, others merged) | ✓ (Pattern A > Pattern B) | — | ✓ (DoRA blocked in PEFTHelper) | ✓ (PR #11003) |
| Held-out validation as selection gate | ✓ (memo_test was anti-signal) | ✓ (pilot ≠ accuracy gate) | ✓ (deploy-like eval) | — | — |
| Per-item route gate | ✓ (v5 dual-path routing precedent) | ✓ (Pattern A routing) | ✓ (no global replacement) | — | — |
| LoRA bf16, NOT QLoRA | ✓ (v5 script direct read) | — | — | — | ✓ (v5 adapter_config.json) |
| Dual-variant pilot (80/20 vs 95/5) | — | — | ✓ (explicit "run both") | ✓ (VRAM cost ≈ 0) | — |
| 6-LoRA simultaneous serving | — | — | — | ✓ (1.54 GB math) | ✓ (docs.vllm.ai) |
| Token budget headroom (81920/65536) | ✓ (v1 truncation cautionary) | — | — | — | — |
| Qwen3-4B is dense | — | — | — | ✓ (MoE FlashInfer N/A) | ✓ (Qwen blog) |
| Plain SC majority as production default | — | — | — | — | (Cursor + my synthesis) |

The strongest decisions have 3+ independent source convergence. v3.1 is the integration of all converged decisions.

---

## 3. The plan with 2× A100 utilization (per phase)

### Phase 0 — Wrong-residual manifest build + v5 decomposition (60 min) — **both GPUs busy**

- **claude_vscode** (~45 min): build wrong-residual manifest with gold provenance tagging (A4), tier-mix-aware sampling (B4), and v5 per-item decomposition (B2):
  - Join `R20_eval_v1_sc8_p943_t32k_pp1.jsonl` (base SC@8) with `MASTER_ANSWERS.csv`.
  - Tag each gold by source: HIGH (Wolfram OR ≥2-teacher), MED (single-teacher), LOW (heuristic backsolve).
  - For v7 training set: select wrong-residual items (base SC@8 majority ≠ HIGH/MED gold) with tier-mix-aware sampling — maintain at least 30% T1+T2 within wrong-residual set, 70% T3+T4+T5 (B4).
  - **NEW B2**: also compute per-item adapter_v5 vs base_R20 vs gold for v5's 391 trained items. Output 4-way classification by tier + MCQ/free-form. Save to `data/v5_per_item_decomp.csv`.
  - Output: `data/v7_wrong_residual.csv` with columns `item_id`, `tier`, `gold_provenance`, `is_mcq`, `route_eligible` (true if HIGH-confidence gold).
- **tnr-0** (60 min): base SC@16 on items 0-471 at deploy temp (0.6/0.95/16). vLLM launch: `--enforce-eager --enable-lora --max-loras=2 --max-lora-rank=64`.
- **tnr-1** (60 min): base SC@16 on items 472-942 at same params.

**Phase 0 pass criteria** (hard):
- ≥100 wrong-residual candidates with HIGH-confidence gold (A4 gate)
- B2 decomposition completed (no failure of compute path)
- Both base SC@16 runs completed across full 943

If <100 HIGH-confidence wrong-residual → fall back to Option B (skip v7).

### Phase 1 — Dual pilot training (45 min) — **both GPUs busy**
Unchanged from v3 except item composition reflects tier-mix-aware sampling (B4) and is gold-provenance filtered (A4).

- **tnr-0**: Pilot A — 30 items (24 wrong-residual + 6 anchors = 80/20), 4 epochs, single Sonnet teacher (B3).
- **tnr-1**: Pilot B — 30 items (28 wrong-residual + 2 anchors = ~95/5), 4 epochs, single Sonnet teacher (B3).

### Phase 2 — Pilot eval + A/B select (40 min) — **both GPUs busy**

- **tnr-0**: paired base-vs-adapter SC@8 on Pilot A's 30 items + 10 anchors.
- **tnr-1**: paired base-vs-adapter SC@8 on Pilot B's 30 items + 10 anchors.
- **NEW A5**: each pilot eval includes 95% bootstrap CI computation on flip rate (5 lines of resampling code).

**Pilot evaluation rubric** (per ChatGPT's calibration + A5 CI):

| Metric | Plumbing check | Directional gate |
|---|---|---|
| Loss descends across 4 epochs | Required | — |
| Adapter loads cleanly via LoRARequest | Required | — |
| Format compliance (parseable last `\boxed{}`) | ≥95% | ≥98% for green |
| Base-wrong residual flips correct under SC@8 | — | ≥30% point estimate AND CI lower bound ≥20% = ship; 20-30% point estimate gray; <20% abort |
| Anchor regression (base-correct → adapter-wrong) | ≤2/10 | ≤1/10 for green |
| Net residual gain (flips − regressions) | — | ≥+20% of pilot |

**A/B winner selection rule** (A2, deterministic, no real-time debate):
```
if (pilot_B.flip_rate >= pilot_A.flip_rate + 5pp
    AND pilot_B.anchor_regressions <= pilot_A.anchor_regressions + 1
    AND pilot_B.format_failure_rate <= 1%
    AND pilot_B.avg_length <= pilot_A.avg_length * 1.20):
    winner = "B (95/5, aggressive)"
else:
    winner = "A (80/20, conservative)"   # default

if both fail plumbing OR both CI-lower-bound <20%:
    ABORT v7, ship Pick B intermediate
```

### Phase 3 — Full v7 train of winner (90 min) — **both GPUs busy**
Unchanged from v3 except trace generation uses single Sonnet teacher (B3).

- **tnr-0**: train full v7 on 180-200 items (≥80% wrong-residual + ≤20% anchors per winning composition), 12 epochs, checkpoint every 2 epochs, single Sonnet teacher.
- **tnr-1**: 
  - First 60 min: write + smoke-test offline DeepConf script (LGC over 512-token windows, per Gemini's formulas). NOTE per A1: this is now SIDE-CHANNEL, not production default.
  - Last 30 min: prepare expanded held-out validation slice (B5): 15-20 items including ~5 base-correct items outside wrong-residual scope.

### Phase 4 — Multi-LoRA checkpoint eval with pre-flight + trace coherence (45 min) — **both GPUs busy**

**NEW A3 pre-flight (10 min)**:
- **tnr-0**: launch vLLM with `--max-loras=6 --max-lora-rank=64`. Load all 6 v7 checkpoints (ep2/4/6/8/10/12). Run 5-item soak test dispatching SC@8 across all 6 IDs in parallel.
- Pass: zero errors + throughput ≥0.5 sample/sec/checkpoint + parsing deterministic (all 6 produce `\boxed{}`-compliant outputs).
- Fail: kill vLLM, restart with `--max-loras=1`, fall back to sequential checkpoint eval (Phase 4 takes 90 min instead of 35).

**Main multi-LoRA eval (30 min if pre-flight pass)**:
- **tnr-0**: dispatch parallel SC@8 across all 6 checkpoints for each item in trained set. SGMV kernel batches.
- **tnr-1**: same multi-LoRA eval on **expanded held-out cross-check** (B5) — 15-20 items, ~5 outside wrong-residual.

**NEW B1 trace-coherence check (5 min, in parallel)**:
- For all trained items + held-out items on selected best checkpoint, extract `<think>` conclusion vs `\boxed{}` and flag mismatches.
- Abort threshold: ≤2% incoherence rate to pass.

**Checkpoint selection rule** (unchanged from v3):
```
best_ckpt = argmax over ckpts of (
    items_where_adapter_wins - 2 × items_where_adapter_regresses
), subject to:
    format_compliance >= 98%
    trace_coherence_rate >= 98% (NEW B1)
    train_token_accuracy plateaued (delta vs prev ckpt < 1pp)
```

### Phase 5 — Per-item routing + plain SC majority as production default (45 min) — **both GPUs busy**

**A1 change**: production answer selection defaults to plain SC@8 majority on the best checkpoint's adapter outputs. DeepConf runs in parallel as instrumentation; only promotes to production if it shows net-positive on locked validation slice with zero regressions.

- **tnr-0**: for each item in `route_to_adapter=True` set per A4-revised gate (HIGH-confidence gold only), run adapter SC@8 at deploy temp. Save trajectories with `logprobs=True, top_logprobs=20`.
- **tnr-1**: compute both (a) plain SC@8 majority [production] and (b) offline DeepConf weighted aggregation [instrumentation]. Compare:
  - If DeepConf > plain SC on net-correct-flips AND zero regressions on held-out slice → promote DeepConf to production.
  - Otherwise → ship plain SC majority. DeepConf stays as side-channel data.

**Per-item routing rule** (A4-revised):
```python
def route_to_adapter(item_id, paired_eval, gold_meta):
    if gold_meta[item_id]["provenance"] not in ("WOLFRAM", "TWO_PLUS_TEACHER"):
        return False  # NEW A4: only HIGH-confidence gold can route
    a_correct = paired_eval[item_id]["adapter_majority"] == gold[item_id]
    b_correct = paired_eval[item_id]["base_majority"] == gold[item_id]
    a_margin = paired_eval[item_id]["adapter_vote_margin"]
    b_margin = paired_eval[item_id]["base_vote_margin"]
    if a_correct and not b_correct:
        return True   # clear win on HIGH-confidence item
    if a_correct and b_correct and a_margin >= b_margin + 1:
        return True   # safe tie with margin on HIGH-confidence item
    return False     # default to base
```

### Phase 6 — Fire + Gradescope (20 min)
Apply `PICKB_FINAL_PREFIRE_CHECKLIST`. Submit Pick B FINAL to Kaggle. Submit code to Gradescope.

**Total wall time**: 60 + 45 + 40 + 90 + 45 + 45 + 20 = **345 min (~5h45m)**.
**Buffer to deadline**: ~4h. Tighter than v3 but still generous.

---

## 4. v7 PRE-DEPLOY GO/NO-GO checklist (binding, expanded for v3.1)

| # | Criterion | Threshold | Fallback if fails |
|---|---|---|---|
| 1 | Phase 0: ≥100 wrong-residual candidates with HIGH-confidence gold (A4) | hard | ABORT v7, ship Pick B intermediate |
| 2 | Phase 0: v5 per-item decomposition (B2) completed | soft (warning) | Proceed with reduced confidence in composition |
| 3 | Phase 0: both base SC@16 splits (0-471, 472-942) completed | hard | Delay Phase 1 until complete |
| 4 | Phase 1: at least one pilot loads and trains without error | hard | ABORT, ship Pick B intermediate |
| 5 | Phase 2: at least one pilot has CI lower bound ≥20% flip rate AND anchor regression ≤2/10 AND format ≥95% | hard | ABORT, ship Pick B intermediate |
| 6 | Phase 3: full train completes 12 epochs, all 6 ckpts saved | hard | Use whatever ckpts saved; pick best per route-sim |
| 7 | Phase 4: 6-LoRA pre-flight passes (A3) | soft | Fall back to sequential checkpoint eval |
| 8 | Phase 4: selected ckpt has items_won - 2 × items_regressed ≥ 10 | hard | Lower threshold to ≥5 OR ABORT |
| 9 | Phase 4: selected ckpt has format compliance ≥98% | hard | Pick later/earlier ckpt |
| 10 | Phase 4: selected ckpt has trace coherence ≥98% (B1) | hard | Pick later/earlier ckpt or ABORT |
| 11 | Phase 4: held-out cross-check shows adapter wins on ≥30% of held-out wrong-residual items AND ≤1 regression on outside-residual items (B5) | soft | Reduce confidence in routing aggressiveness |
| 12 | Phase 5: route_to_adapter manifest contains only HIGH-confidence gold items (A4) | hard | Fix and re-verify |
| 13 | Phase 5: plain SC majority computed for each routed item | hard | Cannot ship without |
| 14 | Phase 5: DeepConf side-channel computed; promote only if net-positive zero-regression (A1) | soft | Ship plain SC majority |
| 15 | Phase 6: ≥1h budget remaining at Phase 5 entry | hard | Stop and ship Pick B intermediate |

---

## 5. Probability estimates (v3.1 revised, with overlap uncertainty acknowledged)

| Path | P(beats 0.745) | Notes |
|---|---|---|
| A — Full train v7 now, skip pilot | 35-45% | v5 failed similar attempt |
| B — Skip v7, ship Pick B intermediate | 50-55% | Floor (no v7 downside, no v7 upside) |
| **C — v3.1 with all 10 patches** | **63-72%** | Conditional on roughly uniform overlap of trained items with scored 283-slice. If overlap concentrates in items adapter helps: ceiling ~75%. If overlap concentrates in items adapter doesn't help: floor remains Pick B intermediate ~50-55%. Per-item gate (A4) and trace-coherence abort (B1) protect floor. |

Best-case ceiling: routed wins land in scored 283-slice → ~0.74-0.79.
Floor: per-item routing prevents regressions → floor ≈ Pick B intermediate.

---

## 6. Pre-mortem (most-likely failure modes, v3.1)

**A — Proxy mismatch** (highest): training items don't overlap heavily with scored 283-slice. **Mitigation**: A4 (provenance gate) + per-item routing means no regressions; floor ≈ Pick B. B4 tier-mix-aware sampling reduces this risk.

**B — Trace incoherence at full-train scale**: Cursor's 17/17 sample insufficient. **Mitigation**: B1 trace-coherence check in Phase 4 with abort threshold ≤2%.

**C — Time overrun**: pilot reveals slow learning; multiple hidden serials. **Mitigation**: hard ≥1h buffer at Phase 5 entry. v3.1 wall time 5h45m vs 5h v3 — buffer reduced from 5h to 4h, still generous.

**D — 6-LoRA serving edge case**: Gemini's math is theoretical. **Mitigation**: A3 pre-flight micro-benchmark gate. Sequential fallback adds ~50 min, still fits.

**E — Pilot A/B near-tie + decision tax**: **Mitigation**: A2 deterministic default-to-A rule, no real-time debate.

**F — Gold label corruption**: **Mitigation**: A4 HIGH-confidence-only routing. Lower-confidence items don't route.

**G — DeepConf parameter miscalibration**: **Mitigation**: A1 side-channel posture, plain SC majority is production default.

---

## 7. Closure protocol for Cursor's 5 open questions (per G5)

From `ADAPTER_NOTES_CURSOR.md` "Open questions / unknowns to resolve before proposing v7":

| Cursor question | v3.1 status |
|---|---|
| Which item set defines targeted memorization scope? | CLOSED — Phase 0 wrong-residual manifest with A4 gold provenance gate + B4 tier-mix-aware sampling |
| What held-out protocol best predicts Kaggle improvement? | CLOSED — Phase 4 multi-LoRA paired eval on trained items + tnr-1 cross-check on held-out (B5) |
| Should deployment use route-by-item or confidence agreement? | CLOSED — per-item route-sim with A4 high-confidence gold gate |
| How much of prior underperformance is data curation vs decoding stack? | PARKED — addressed indirectly by B2 v5 decomposition; full causal analysis post-deadline |
| Is teacher-source consistency materially causal? | CLOSED (by design) — B3 locks single Sonnet teacher; heterogeneity studies post-deadline |

---

## 8. Explicit NOT in v7 round 1

Unchanged from v3 (DoRA, vLLM source patching, WiSE-FT, confidence-gated routing via logits, weight-merging adapters, two full-train adapters by default, kitchen-sink, spectral geometry, Numina-style external benchmarks, trace regeneration).

**NEW in v3.1**: DeepConf-as-production-default (demoted to side-channel per A1).

---

## 9. Operational notes for execution agents

Unchanged from v3. vLLM 0.10.2 or 0.11.1, `--enforce-eager`, `--max-loras` = pool size per phase, `logprobs=True top_logprobs=20`, temperature=0.6/top_p=0.95/top_k=20.

**NEW for v3.1**: 
- Phase 0 outputs include `data/v5_per_item_decomp.csv` (B2) and `data/v7_wrong_residual.csv` with `gold_provenance` column (A4).
- Phase 4 pre-flight: 5-item soak test before committing all 6 IDs (A3).
- Phase 4 trace-coherence check on selected ckpt outputs (B1).
- Phase 5 production answer = plain SC@8 majority (A1).

# v3.2 Patch Notes — Post-R5-LLM-Sanity-Check

**Status**: Patches v3.1 (commit d84de5b) with 4 deltas from R5 LLM sanity check responses (ChatGPT browsed, Gemini, Opus 4.8). Delta document rather than full plan rewrite for time efficiency. The 4 patches are enforced at execution-prompt level when those phases begin. v3.1 plan at d84de5b remains canonical structure.

---

## C1 — SPLICE rule for Pick B FINAL CSV assembly (BINDING)

**Source**: Opus 4.8 Q2, biggest unpriced risk.

**Problem**: v3.1 didn't lock how Pick B FINAL CSV is assembled. If `run_inference()` regenerates all 943 items fresh, the ~211 non-routed scored items become a NEW sampling draw with ~±2.6pp SE per item. Two-sided noise on 211 non-routed items swamps the small one-sided routed gain — turns the structured ~65% bet into a coin flip plus thin edge.

**Patch (Phase 6 BINDING)**: Pick B FINAL = (Pick A frozen) ⊕ (adapter overrides on routed IDs only). Non-routed rows byte-identical to Pick A. No regenerate.

**Implementation** (new build script `submission/scripts/build_pickb_final_splice.py`):

```python
import pandas as pd

pick_a = pd.read_csv("submission/csvs/pick_a.csv")
assert len(pick_a) == 943

routing = pd.read_csv("data/v7_routing_manifest.csv")
routed_ids = set(routing[routing["route_to_adapter"]]["item_id"])

adapter_outputs = pd.read_csv("data/v7_adapter_voted_answers.csv")

pickb_final = pick_a.copy()
for idx, row in pickb_final.iterrows():
    if row["id"] in routed_ids:
        ans = adapter_outputs.loc[
            adapter_outputs["item_id"] == row["id"], "adapter_voted_answer"
        ].values
        if len(ans) == 1 and not pd.isna(ans[0]):
            pickb_final.at[idx, "answer"] = ans[0]

# HARD GATE: diff_count must equal len(routed_ids) exactly
diff_count = (pickb_final["answer"] != pick_a["answer"]).sum()
assert diff_count == len(routed_ids), \
    f"SPLICE VIOLATION: diff_count={diff_count}, routed={len(routed_ids)}"

pickb_final.to_csv("submission/csvs/pickb_final.csv", index=False)
```

**New GO/NO-GO gate #15**: hard. Diff count assertion. If violated, fix or abort.

---

## C2 — PagedAttention stress items in pre-flight (Gemini Q2)

**Problem**: A3's 5-item soak test passes easily but doesn't detect KV-cache exhaustion under parallel SC@8 with max-thinking traces. Qwen3-4B thinking traces dynamically expand to ~24k tokens; under 6-adapter concurrent SC@8 the PagedAttention block allocator saturates → silent preemption or OOM.

**Patch (Phase 4 pre-flight)**: 5 normal items + 2 xhigh-difficulty items (T4/T5 known hardest from MASTER_ANSWERS, forced max_tokens=81920, thinking_budget=65536), all dispatched in parallel across 6 adapter IDs.

**Pass criteria additions**:
- No PagedAttention preemption events
- No OOM crashes
- xhigh items don't slowdown >2× vs normal
- All 6 IDs produce parseable \boxed{} on xhigh items

**Fail action**: kill vLLM, restart --max-loras=1, sequential fallback (adds ~50 min).

---

## C3 — Tier-aware gold provenance gate (Opus Q1)

**Problem**: v3.1's A4 treats all HIGH-confidence gold the same. T4/T5 items have least reliable teacher consensus. Mislabeled routed item flips +1 to −1. Expected delta scales with (2·p_label − 1) → net-negative below p_label ~0.5.

**Patch** (Phase 0 manifest + Phase 5 routing):

```python
def route_eligible_tier_aware(item_id, tier, gold_provenance):
    if tier in ("T4", "T5"):
        return gold_provenance == "HIGH-W"   # Wolfram-verified ONLY
    elif tier in ("T2", "T3"):
        return gold_provenance in ("HIGH-W", "HIGH-T")   # Wolfram or 2+ teacher
    elif tier == "T1":
        return gold_provenance in ("HIGH-W", "HIGH-T", "MED")   # easy items OK
    else:  # T0
        return gold_provenance in ("HIGH-W", "HIGH-T")
```

**Phase 0 manifest tagging**: HIGH-W (Wolfram-verified), HIGH-T (2+ teacher consensus, no Wolfram), MED (single-teacher), LOW (heuristic backsolve).

**GO/NO-GO gate #1 updated**: ≥100 wrong-residual candidates with route_eligible_tier_aware=True.

---

## C4 — Probability re-anchored + convergence-bias acknowledged

**Q1 finding (Opus)**: v3.1's 63-72% conditioned on coverage uniformity. Load-bearing variable is verified-label precision on residual set. Hardest items (T3-T5) are exactly where teacher consensus is weakest.

**Q3 finding (Opus)**: All 5 research sources (Cursor, Opus, ChatGPT, Gemini, my own web verification) approved v3.1 because asked to refine, not falsify. Local base rate 0/4: v1/v3/v4/v5 went 0.14/0.452/0.597/0.646 — every prior version failed to beat base. Each had a "this time we fixed the real problem" narrative.

**B2 partial counter-evidence (NEW, from 308310e)**: v5 per-item decomposition showed NET +7 adapter on hard items (T3/T4/T5) — 8 real-capability wins / 1 loss under value-equality grading. Caveats: memorization confound (v5 was trained on those items, so wins may not generalize) and is_equiv overstatement (the grader is more lenient than Hendrycks). Direction is supportive of v7's wrong-residual T3+T4+T5-heavy targeting, magnitude is uncertain.

**Patch (probability re-anchored)**:

| Path | P(beats 0.745) | Conditioning |
|---|---|---|
| A — Skip pilot, full train v7 | 25-35% | Was 35-45%; convergence-bias adjustment |
| B — Skip v7, ship Pick A unchanged | ~50% (Pick A IS 0.745) | Floor by definition |
| **C — v3.2 with all 14 patches** | **50-65%** | Conditional on p_label ≥0.85, SPLICE (C1) enforced, 0/4 base rate adjustment, B2 +7 directional signal |

**Sources of probability**:
- +15-20% if pilot passes + ckpt eval shows ≥30% routed wins with high vote margin
- +5-10% if held-out cross-check generalizes
- +5pp if DeepConf promotes (zero-regression net-positive on locked validation)
- +5pp from B2 directional evidence (counter to convergence-bias adjustment)
- −5-10% from convergence-bias (sources couldn't falsify SFT-residual paradigm)
- −5-10% from p_label uncertainty even with HIGH-confidence gate
- −5-10% from B2 caveats (memorization confound, grader leniency)
- −10pp if SPLICE rule (C1) breaks — must be hard gate

**Pre-mortem additions**:

**H — SPLICE rule violation (NEW)**: regenerate vs splice would inject ±2.6pp SE on ~211 non-routed scored items. Mitigation: C1 binding + hard gate #15 + diff_count assertion.

**I — Convergence bias (acknowledged)**: 5 sources approved v3.1 because asked to refine, not falsify. Local base rate 0/4. Composition diagnosis is most mechanistic fix yet but agreement ≠ evidence the fix works. B2 +7 finding is partial counter-evidence but with memorization confound. Mitigation: probability honestly re-anchored; SPLICE preserves Pick A floor.

---

## Enforcement at execution-prompt level

| Patch | Enforcement point |
|---|---|
| C1 SPLICE | Phase 6 build prompt — references build_pickb_final_splice.py with diff_count assertion |
| C2 stress items | Phase 4 pre-flight prompt — 2 xhigh items at forced max budget |
| C3 tier-aware | Phase 0 manifest prompt — route_eligible_tier_aware logic |
| C4 probability | Documentation only — this doc |

---

## Acknowledgment of remaining unknowns (Opus through-line)

All 3 R5 findings are the same failure shape: unexamined assumptions inherited rather than tested. We fixed the most impactful (C1 SPLICE) and most actionable (C3 tier-aware). C4 honestly documents the structural risks.

What we cannot fix in remaining time:
- Local base rate 0/4 prior version failures (real prior; B2 +7 provides partial counter-evidence but with memorization confound)
- Convergence across 5 sources is methodological consistency, not validation
- Hidden 283-item scored slice composition remains unknown
- B2 grading leniency (is_equiv vs Hendrycks) may overstate adapter capability

These are explicit known unknowns. Floor protected by SPLICE (C1) preserving Pick A at 0.745.

---

## References

- v3.1 plan (canonical structure): `strategy/PHASE_D_v7_PLAN.md` @ commit d84de5b
- v3.1 R1 reviews: `strategy/REVIEW_OF_STRATEGY_V3.md` @ 204380c + `strategy/REVIEW_OF_CURSOR_RESEARCH.md` @ 536e4a4
- B2 results: `data/v5_per_item_decomp.csv` + `data/v5_decomp_summary.md` @ 308310e
- Session handoff: `strategy/SESSION_HANDOFF.md` @ 1ae010e
- Research phase flow: `strategy/RESEARCH_PHASE_FLOW.md` @ cd2161d

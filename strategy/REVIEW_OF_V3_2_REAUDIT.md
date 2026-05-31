# Review of v3.2 Part A re-audit (C1-C4 only)

Reviewer: Cursor  
Target: `strategy/V3_2_PATCH_NOTES.md` + `submission/scripts/build_pickb_final_splice.py` @ `27e7a5f`  
Time spent: ~10 minutes (hard cap)

This re-audit is scoped to Part A only, per request. Prior Part B (B2 @ `308310e`) and Part C (v3.1 integration @ `d84de5b`) conclusions are reused from `strategy/REVIEW_OF_V3_2_AND_B2.md`.

---

## Section 1: Steelman

- **C1 (SPLICE) is implemented in code and is fail-safe by default.** `build_pickb_final_splice.py` loads frozen Pick A, overlays only routed IDs with usable adapter answers, preserves non-routed rows by construction, and exits non-zero on assertion failure. This enforces the "no full regenerate" intent from patch notes.
- **C1 invariant direction is correct.** Using `diff_count == overrides_applied` is materially better than `diff_count == len(routed_ids)` because routed IDs can legally include silent fallback rows (missing/empty adapter answer), which should remain Pick A unchanged.
- **C1 silent fallback handling is correctly safe.** Routed items with missing/empty adapter outputs are explicitly left as Pick A with warning-only logging, preventing accidental blank or malformed output rows.
- **C1 structural checks are aligned with shipping risk.** Fixed row count (943), row-order identity check on `id`, and exact column-list match are the right anti-corruption checks for final CSV assembly.
- **C2 stress patch is directionally strong for allocator risk.** The 5 normal + 2 xhigh pattern, forced high token budgets, and parallel dispatch across 6 LoRA IDs directly pressure the PagedAttention/KV path that A3 alone under-tested.
- **C2 pass criteria cover the main operational failures.** No preemption, no OOM, bounded slowdown on xhigh, and parseable `\boxed{}` across all 6 IDs collectively catch both hard crashes and soft degradation that would invalidate multi-LoRA production assumptions.
- **C3 tier-aware provenance logic is coherent and risk-aware.** T4/T5 restriction to HIGH-W protects the highest-risk label regime; T2/T3 allow HIGH-T; T1 allowance for MED is a pragmatic coverage unlock where consensus is naturally stronger.
- **C3 manifest tag schema is implementation-ready.** HIGH-W / HIGH-T / MED / LOW is explicit enough to support deterministic Phase 0 filtering and downstream route gating.
- **C4 probability re-anchor is materially more honest than v3.1.** It explicitly includes 0/4 historical base rate, convergence-bias risk, and B2 caveats (memorization confound, lenient equivalence), while conditioning upside on SPLICE and label precision.

---

## Section 2: Red-team

- **C1 docstring/comment inconsistency can mislead operators.** The file header says "diff_count must equal len(routed_ids) exactly," while executable logic asserts `diff_count == overrides_applied`. Runtime is correct; prose is stale and should be corrected to avoid human error during execution.
- **C1 invariant has one edge-case false-stop.** `overrides_applied` increments when a routed item has a usable adapter answer even if that answer equals Pick A's existing answer; then `diff_count` does not increase and the hard gate trips. This is safe (fail-stop, not bad ship) but can cause avoidable aborts.
- **C1 does not assert routed coverage sanity.** There is no explicit check that all routed IDs exist in Pick A and no duplicate `item_id` conflicts in adapter outputs. Current behavior is conservative (duplicates become fallback), but diagnostics are weaker than they could be.
- **C2 remains a pre-flight sample, not full-load proof.** The 7-item stress set is good for early allocator failure detection but cannot guarantee absence of rare long-run fragmentation events across full production traffic.
- **C2 preemption detection needs explicit observability wiring.** Patch notes require "no preemption events," but success depends on log parsing/metrics being reliably captured during the stress run; that instrumentation is assumed, not codified here.
- **C3 T1+MED still carries non-zero label-noise risk.** It is probably acceptable given easy-item consensus, but if MED labeling process drifts, T1 admits a leakage path; this should be watched in Phase 0 manifests.
- **C4 range could still be optimistic if label precision underperforms.** 50-65% is defensible only under stated conditions (`p_label >= 0.85`, SPLICE enforced, adjusted priors). If `p_label` quality degrades, this interval should be revised downward immediately.

---

## Section 3: AGREE & LOCK

1. **Lock C1 SPLICE as binding**: build final Pick B by splice-only on routed IDs; no full 943 regeneration.
2. **Lock C1 hard-fail behavior**: assertion violations must abort shipping; never "best-effort" through integrity mismatch.
3. **Lock C2 stress gate**: include xhigh forced-budget parallel stress before trusting 6-LoRA concurrent serving.
4. **Lock C3 tier-aware provenance gate**: keep T4/T5 at HIGH-W only; retain stricter provenance for harder tiers.
5. **Lock C4 framing**: treat 50-65% as conditional decision range, not unconditional performance claim.

---

## Section 4: DISAGREE / DIVERGE

- **Claim**: C1 script comments currently reflect final invariant semantics.  
  **Counter-position**: Not fully true; comments still mention `len(routed_ids)` while code enforces `overrides_applied`.  
  **Resolution evidence**: one-line doc/comment correction in `build_pickb_final_splice.py` to match executable invariant.

- **Claim**: `diff_count == overrides_applied` is universally valid as implemented.  
  **Counter-position**: Not universal because equal-to-Pick-A overrides can trigger false-stop.  
  **Resolution evidence**: either (a) count override only when value actually changes, or (b) maintain current conservative fail-stop and explicitly document this abort condition as intentional.

No divergence found that blocks Phase 0 authorization under the current risk posture.

---

## Section 5: GAPS

1. **C2 observability artifact gap**: retain and review one concrete stress-run log showing preemption/OOM checks before final launch.
2. **C1 operator clarity gap**: update stale invariant wording in script header/comments to prevent accidental procedural drift.
3. **C3 MED drift gap**: monitor T1 MED-labeled routed items count in Phase 0 output; if unexpectedly large, tighten gate.
4. **C4 conditioning audit gap**: ensure explicit `p_label` estimate is written at run time, not only assumed in planning docs.

---

VERDICT: ACCEPT — execute

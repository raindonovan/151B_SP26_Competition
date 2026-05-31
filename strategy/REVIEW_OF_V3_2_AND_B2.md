# Review of v3.2 + B2 combined artifacts

Reviewer: Cursor  
Target set:
- Part A: `strategy/V3_2_PATCH_NOTES.md` + `submission/scripts/build_pickb_final_splice.py` (claimed, not present in current `main`)
- Part B: `data/v5_per_item_decomp.csv`, `data/v5_decomp_summary.md`, `inference/scripts/compute_v5_decomp.py` (`308310e`)
- Part C: `strategy/PHASE_D_v7_PLAN.md` (`d84de5b`)
Time spent: ~30 min (hard cap)

---

## Section 1: Steelman

- The B2 implementation is methodologically careful: it computes both value-equality (`grading.grader.Grader.is_equal`) and strict (`hendrycks_local.is_equiv`) and explicitly treats strict as hedge, not primary.
- Internal accounting for B2 is clean and reproducible: 391 rows; class totals sum exactly; all class-by-tier/type/provenance subtotals reconcile.
- The top-line B2 conclusion is directionally coherent with v7 targeting: net adapter value concentrates on hard tiers (T3/T4/T5 net +7), with zero net on T1/T2.
- v3.1 still preserves the A1-A5 safety posture (DeepConf side-channel default, deterministic A/B tie-break, pre-flight 6-LoRA gate, high-confidence route gate, pilot CI).
- v3.1 also preserves B1-B5 additions in a way that generally strengthens reliability rather than increasing execution risk.

---

## Section 2: Red-team

### Part A (v3.2 patches C1-C4): **blocked by missing artifacts**

- `strategy/V3_2_PATCH_NOTES.md` is not present in the checked-out `main`.
- `submission/scripts/build_pickb_final_splice.py` is not present either.
- Latest relevant commits available locally and on origin are `308310e` and `8a7049a`; neither includes C1-C4 artifacts.

Impact:
- I cannot verify C1 SPLICE assertions, C2 PagedAttention stress design, C3 tier-aware provenance refinement, or C4 probability re-anchor language from source.
- Any ACCEPT verdict would be unsafe because the claimed patch surface is not auditable in this repo state.

### Part B (B2 decomposition): specific risks/anomalies

- B2 is robust internally, but evidence strength is still bounded: this is trained-set decomposition (memorization-influenced), not held-out causal proof.
- `gold_provenance` currently marks `search_GOLD` as HIGH in code; if later C3 introduces tier-aware provenance overrides, that logic must be audited for consistency with A4 route-gate spirit.
- Strict-vs-primary discrepancy count is 10 items (not 6) in raw comparison; summary correctly focuses on six strict-only "wins," but downstream readers should avoid over-generalizing strict as capability signal.

### Part C (v3.1 integrity under claimed v3.2): cannot fully certify

- Since C1-C4 code/docs are absent, I cannot verify whether they regress A1-A5 or B1-B5 in the actual v3.2 state.
- I can only confirm the current visible state (`d84de5b` + `308310e`) is consistent and non-regressive.

---

## Section 3: AGREE & LOCK

Lockable now from available evidence:

1. **B2 data pipeline quality**: methodology and arithmetic consistency pass.
2. **B2 interpretation for v7 composition**: hard-tier concentration signal (net +7 on T3/T4/T5; net 0 on T1/T2) is real in available data.
3. **v3.1 A1-A5 preservation**: still intact in `d84de5b`.
4. **v3.1 B1-B5 preservation**: still intact in `d84de5b`.

---

## Section 4: DISAGREE / DIVERGE

### D1) Claimed "three things in one push" is not reflected in repo state
- Specific claim: v5 decomp + v3.2 patch notes + session handoff replacement committed together.
- Observed state: only v5 decomp artifacts are committed (`308310e`) plus SCRATCH marker (`8a7049a`).
- Resolution path:
  1. Push the missing artifacts (or provide commit SHA containing them), then
  2. Re-run a short delta audit on C1-C4 immediately.

### D2) Execution authorization based on unseen C1-C4 is not defensible
- Counter-position: no execution decision should depend on patch notes/scripts absent from audited tree.
- Resolution path: either (a) treat C1-C4 as not integrated and proceed on audited v3.1+B2 only, or (b) pause for missing commit and re-audit.

---

## Section 5: GAPS

1. **Missing v3.2 patch document** (`strategy/V3_2_PATCH_NOTES.md`)  
   - Closure: commit/push file or provide exact SHA/path.

2. **Missing C1 implementation file** (`submission/scripts/build_pickb_final_splice.py`)  
   - Closure: commit/push file, then run targeted script audit.

3. **No auditable C2 stress evidence** (inputs/results/criteria)  
   - Closure: include stress-run artifact and explicit pass metrics in patch notes.

4. **Unverifiable C3/C4 wording changes**  
   - Closure: include those deltas in patch notes commit and re-run 10-min verification.

---

**VERDICT: REPLAN — issues require v3.3 (or at minimum a missing-artifacts push + immediate re-audit before execution authorization).**

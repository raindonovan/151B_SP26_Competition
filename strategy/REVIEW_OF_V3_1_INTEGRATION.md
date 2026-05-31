# Review of v3.1 integration (`strategy/PHASE_D_v7_PLAN.md` @ `d84de5b`)

## INTEGRATION CONFIRMED

A1-A5 integration check against `strategy/REVIEW_OF_STRATEGY_V3.md`:

1. **A1 (DeepConf demoted, plain SC default)**: **CONFIRMED**  
   - Integrated in change table (A1), Phase 5 default path, and GO/NO-GO #13/#14 split.
2. **A2 (A/B tie-break default-to-A)**: **CONFIRMED**  
   - Deterministic rule is explicit in Phase 2 (`else -> A`) with no gray-zone arbitration branch.
3. **A3 (6-LoRA pre-flight micro-benchmark gate)**: **CONFIRMED**  
   - Added pre-flight soak test (5 items), explicit pass criteria, explicit sequential fallback.
4. **A4 (route-gate gold provenance audit, HIGH-confidence only)**: **CONFIRMED**  
   - Added provenance tagging in Phase 0, routing predicate hard-gated to high-confidence sources, GO/NO-GO #1/#12 enforce it.
5. **A5 (pilot bootstrap CI on flip rate)**: **CONFIRMED**  
   - Added Phase 2 bootstrap CI and CI-based threshold logic (lower bound gating).

No A1-A5 integration errors found.

## NO REGRESSION

B1-B5 interaction check vs A1-A5:

- **B1 (trace-coherence check) vs A3 (6-LoRA pre-flight)**: **NO CONFLICT**  
  - A3 is serving stability gate; B1 is output-quality gate after eval. They are orthogonal and correctly sequenced.

- **B4 (tier-mix-aware sampling) vs A4 (HIGH-confidence provenance gate)**: **NO REGRESSION**  
  - B4 changes composition mix inside wrong-residual selection; A4 still controls route eligibility by confidence provenance.  
  - v3.1 explicitly keeps A4 hard gate in routing logic and GO/NO-GO.

- **B2, B3, B5 vs A1-A5**: **NO REGRESSION DETECTED**  
  - B2 decomposition augments Phase 0 evidence; does not weaken A1-A5.  
  - B3 teacher standardization removes a confound; no adverse effect on A1-A5.  
  - B5 expanded held-out slice strengthens, not weakens, A1/A4 decisions.

## CARRYOVER PRESERVED

Core v3 design points checked for accidental drop:

- Dual-variant pilot architecture: **PRESERVED**
- LoRA hyperparameters and unmerged LoRARequest posture: **PRESERVED**
- Per-item routing strategy (adapter subset + base fallback): **PRESERVED**
- Checkpoint selection by deploy-like paired evaluation: **PRESERVED** (with added B1 quality constraint)
- 2xA100 parallelism structure: **PRESERVED** (with added pre-flight and side-channel tasks)
- Runtime discipline (vLLM pin + serving flags): **PRESERVED**
- Hard abort/fallback posture: **PRESERVED**

Net: v3.1 is a faithful patch integration of R1 feedback with no detected regression against A1-A5 and no accidental drop of core v3 design intent.

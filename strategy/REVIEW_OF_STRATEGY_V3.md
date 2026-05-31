# Review of `strategy/PHASE_D_v7_PLAN.md`

Reviewer: Cursor
Target: `strategy/PHASE_D_v7_PLAN.md` @ commit `249be05`
Time spent: 29 minutes

## Section 1: Steelman

### 1) Dual-variant pilot (80/20 vs 95/5) is rational under 2x A100 constraints
- What would have to be true: pilot overhead is mostly fixed plumbing/eval cost, not a second full train cost.
- Evidence supporting it: v3 keeps both pilots to 30 items and 4 epochs and runs them truly in parallel on separate A100s; it does not double full-train cost.
- Insight worth integrating: this is not "two bets for same price" in pure wall-clock terms, but it is close in this setup because the expensive path (Phase 3 full train) remains single-winner only.

### 2) Reframing pilot as plumbing + directional screen (not final predictive gate) is correct
- What would have to be true: 30-item pilot behavior is too noisy to forecast full-train absolute gain, but still useful to detect obvious non-viability and implementation breakage.
- Evidence supporting it: v3 explicitly separates pilot directional thresholds from Phase 4/5 per-item route-sim gating on full-train checkpoints.
- Insight worth integrating: this avoids repeating v5's "wrong metric at wrong level" failure by moving the decisive gate to deploy-like paired evaluation.

### 3) Per-item route-sim gate is the strongest risk reducer in the document
- What would have to be true: routed overrides are only used where adapter has item-level evidence of superiority under deploy-like decoding.
- Evidence supporting it: v3 gate requires adapter correctness and either base wrongness or margin superiority; default path is base.
- Insight worth integrating: this is exactly aligned with "maximize success probability" and "single-shot slot" risk posture, because it structurally avoids global adapter replacement.

### 4) 6-checkpoint simultaneous multi-LoRA eval is strategically high leverage if stable
- What would have to be true: vLLM in pinned versions can run 6 LoRAs without pathological scheduler/eviction behavior.
- Evidence supporting it: v3 cites concrete `max_loras=6` serving assumptions, pins versions, and includes sequential fallback in pre-mortem.
- Insight worth integrating: collapsing checkpoint eval variance (single serve process, same runtime conditions) improves comparison quality, not just speed.

### 5) Time budget optimism is partially controlled by explicit abort points
- What would have to be true: hard aborts are actually enforced and not softened under deadline pressure.
- Evidence supporting it: v3 has hard gates in Section 4 (Phase 0 candidate floor, pilot fail abort, buffer gate at Phase 5 entry).
- Insight worth integrating: this is one of the few plans in this repo history that explicitly encodes stop conditions early enough to preserve a fallback submission.

### 6) DeepConf is correctly treated as additive, not foundational
- What would have to be true: base SC majority remains available as a fallback and DeepConf can be disabled with no pipeline break.
- Evidence supporting it: v3 pre-mortem calls DeepConf bug risk directly and states plain SC fallback.
- Insight worth integrating: the plan does not make success contingent on novel confidence machinery, which is the right reliability posture this late.

### 7) Version pinning and serving flags show good operational maturity
- What would have to be true: known vLLM regressions are version-sensitive and can be avoided by pinning + launch discipline.
- Evidence supporting it: v3 explicitly locks to 0.10.2/0.11.1 and includes `--enforce-eager`, `--max-loras`, `--max-lora-rank`.
- Insight worth integrating: this is a practical anti-regression layer many strategy docs miss.

## Section 2: Red-team

### 1) Dual-variant pilot is not free; hidden cost is decision noise and operator bandwidth
- Failure mode: near-tie pilot outputs (for example 3-5pp swing, mixed anchor regressions) create arbitration delay and human overfitting to noisy differences.
- Why this matters: under one-slot risk, cognitive load and indecision can burn more time than nominal parallelism saves.
- Concrete risk: v3 uses an A/B winner rule with multiple conditions; if both are "gray," team may spend 20-40 minutes re-litigating instead of moving to full train or abort.

### 2) Per-item route gate may leak optimistic bias unless gold provenance is strictly partitioned
- Failure mode: gate uses `gold` comparisons from the same curated answer sheet used for training target selection; if confidence labels are wrong or selection is correlated, false positives can enter routing.
- Specific concern: gate expression
  `(a_correct AND NOT b_correct) OR (a_correct AND b_correct AND a_margin >= b_margin+1)`
  is conservative only if `a_correct`/`b_correct` are reliable and computed on items not implicitly overfit by data curation artifacts.
- Regression scenario: answer-sheet errors or normalization mismatches mark adapter as "correct" where both are actually wrong, producing harmful overrides in scored slice.

### 3) 30-item pilot can still be dangerously optimistic even as plumbing test
- Failure mode: small-sample pilot is dominated by easy-to-flip residuals and overstates true deploy leverage; "plumbing framing" does not fully neutralize this if thresholds are interpreted as directional efficacy evidence.
- Specific risk in v3: it still uses flip-rate thresholds (`>=30% green`) that can induce false confidence from tiny N and composition luck.
- Consequence: passing pilot may greenlight a full train that fails to produce robust route wins beyond curation artifacts.

### 4) Phase 4 six-LoRA collapse has real-world failure modes beyond VRAM math
- Failure mode class A: scheduler fairness and latency spikes with mixed LoRA IDs can cause timeout/retry asymmetry and inconsistent sample quality.
- Failure mode class B: LoRA cache churn or rank/kernel path edge behavior under sustained multi-ID SC loops causes silent throughput collapse.
- Failure mode class C: if one loaded checkpoint has malformed metadata/tokenizer coupling assumptions, batched comparisons become contaminated by non-comparable failures.
- v3 mitigation is present (sequential fallback), but the fallback adds a major serial tail and may break the 4h50m budget in practice.

### 5) ChatGPT-derived `>=30%` flip threshold is likely population-mismatched
- Failure mode: threshold calibrated from AIMO-style validation priors does not transfer cleanly to this private-943 / hidden-283 regime with different error distribution and overlap uncertainty.
- Risk impact: false gate confidence (both false positives and false negatives) at Phase 2.
- Better framing: treat threshold as heuristic trigger, not decision truth; require uncertainty bounds or minimum effective sample constraints.

### 6) Time budget is likely optimistic due to hidden serial dependencies
- Hidden serials:
  - manifest quality debugging and schema mismatches before Phase 0 pass
  - logprob capture integrity checks before DeepConf can run
  - reruns on malformed/no-box outliers in paired eval
  - route manifest audit + PickB integration QA before fire
- If any one occurs, nominal ~5h buffer can compress fast, especially with human arbitration in pilot A/B ties.

### 7) DeepConf placement still introduces unnecessary production-path fragility
- Failure mode: parameter defaults (`alpha=1`, `beta=1`, window 512) subtly degrade route quality on long reasoning traces, but no pre-registered acceptance test distinguishes "helpful weighting" from "confidence hallucination."
- Risk-minimizing posture suggests DeepConf should be side-channel scoring only, with production answer selection defaulting to plain SC majority unless DeepConf demonstrates monotonic gain on a locked validation slice.

### 8) Section 5 probability table is overconfident given unresolved overlap uncertainty
- The stated C path `60-70%` appears stronger than evidence supports because the major uncertainty term is overlap between routed wins and hidden scored-283.
- This is the dominant unknown and remains weakly constrained; safer expression is scenario-bounded with explicit low/median/high assumptions on overlap.

## Section 3: AGREE & LOCK

These should be locked for execution unless Rain explicitly overrides:

1. **Keep DoRA out of v7 round 1** (blocker and integration risk remain too high).
2. **Keep v5 LoRA hyperparameter family as baseline**; do not burn time searching rank/alpha/dropout now.
3. **Use wrong-residual targeting as primary composition lever** with anchor cap.
4. **Use per-item routing (adapter subset + base fallback)**; avoid global replacement.
5. **Select checkpoint by deploy-like paired evaluation**, not train loss or memo behavior.
6. **Pin vLLM version + launch flags** as specified; treat runtime discipline as part of model quality.
7. **Retain hard abort gates and buffer gate**; fallback to intermediate is mandatory if breached.

## Section 4: DISAGREE / DIVERGE

### D1) Claim: DeepConf should be integrated into production route answer selection in Phase 5
- Counter-position: DeepConf should be default-off for production in this round; run it in parallel and only promote if it wins on a locked validation subset with zero regressions.
- Evidence to resolve:
  - direct A/B on the same routed set: plain SC vs DeepConf
  - require `net gain > 0` and `regressions = 0` on locked validation IDs.

### D2) Claim: 6-LoRA collapse is a default execution path
- Counter-position: keep 6-LoRA path as "fast path," but plan should declare a pre-flight micro-benchmark gate (5-10 items across 6 IDs) before committing full Phase 4.
- Evidence to resolve:
  - measured throughput, failure count, and consistency on a fixed micro-slice under 6-ID load
  - go to sequential immediately if instability observed.

### D3) Claim: Pilot A/B can be decided reliably with current rule
- Counter-position: include an explicit tie/gray policy to avoid indecision tax:
  - if delta <5pp and anchor diff <=1, pick conservative A by default.
- Evidence to resolve:
  - run historical replay on prior artifacts or simulated pilot results to show rule determinism and decision latency.

### D4) Claim: `>=30%` flip threshold is an actionable gate as written
- Counter-position: keep it as directional heuristic only; require confidence interval or minimum denominator quality to avoid overreacting to tiny unstable slices.
- Evidence to resolve:
  - bootstrap interval on pilot flip rate and anchor regression
  - check sensitivity to 2-3 item label perturbations.

### D5) Claim: Probability band `60-70%` for path C
- Counter-position: reduce confidence or make dependence explicit on scored-slice overlap parameter; current band is likely too tight.
- Evidence to resolve:
  - scenario analysis with overlap assumptions (low/mid/high) and route-win leakage rate.

## Section 5: GAPS

1. **No explicit leakage audit for route gate gold labels**  
   Need: provenance tagging of each `gold` used for gate decision (Wolfram vs teacher-consensus vs weak confidence), with auto-exclusion of low-confidence entries.

2. **No pre-registered tie-break protocol for pilot A/B gray outcomes**  
   Need: deterministic fallback policy to avoid real-time debate under clock pressure.

3. **No explicit uncertainty quantification on pilot metrics**  
   Need: simple bootstrap CI for flip-rate and regression-rate before passing Phase 2.

4. **No explicit DeepConf promotion test**  
   Need: lock criterion for enabling DeepConf in production (`net positive`, `no regressions`, same routed set).

5. **No explicit 6-LoRA micro-benchmark gate before full Phase 4**  
   Need: short soak test with pass/fail thresholds (throughput floor, error-free runs, deterministic parsing rate).

6. **No scored-slice overlap stress test in probability section**  
   Need: probability table conditional on overlap assumptions, not single unconditional band.

# Review of `strategy/ADAPTER_NOTES_CURSOR.md`

Reviewer: claude_strategy
Target: `strategy/ADAPTER_NOTES_CURSOR.md` @ blob SHA `fe441b683ab9fc85dec1359591500587084aa82d` (commit `204380c`)
Time spent: 28 minutes

---

## Section 1: Steelman

### S1) Per-attempt failure-mode taxonomy is methodologically sharp
- **What would have to be true**: each version's break-even/regression had a specific, attributable cause; lessons must be inherited as constraints not vibes.
- **Evidence supporting it**: Cursor extracts concrete root causes per version — v1: trace truncation pathology, v3: in-training-only memorization proxy, v4: training-ID-aware routing optimism, v5: memo-test as selection gate. Each backed by direct file references (`memo_test.log`, `training.log`, `run_meta.json`).
- **Insight worth integrating**: the "one thing to change next attempt" line per version is essentially a binding constraint set for v7. v3 already absorbs all four (held-out gate, scoped target set, ban training-ID-aware selection, route-sim not memorization).

### S2) v5 87.72% T1+T2 tier verification corrects a long-running ambiguity
- **What would have to be true**: prior assertions about "easy-heavy" v5 composition needed concrete tier-level confirmation against `MASTER_ANSWERS`.
- **Evidence supporting it**: Cursor joins `sft_v5_dataset.jsonl` against `MASTER_ANSWERS.csv` and reports exact tier breakdown — T1: 0.51%, T2: 87.21%, T3: 7.93%, T4: 1.79%, T5: 2.56%, 391/391 mapped, missing=0.
- **Insight worth integrating**: locks the precise mismatch — v5 was not just "easy-heavy" colloquially; it was 87.72% T1+T2 by hard count. v7's wrong-residual targeting inverts this directly. This is the single most actionable finding in the research for v7 composition.

### S3) Merge-vs-adapter per-version table resolves a deployment-mode question
- **What would have to be true**: each prior version's deployment mode (merged vs adapter) needed unambiguous evidence-trace tying training-time artifact to inference-time loading path.
- **Evidence supporting it**: Cursor gives the table with both training-artifact evidence (merge scripts in v1/v3, `run_meta.json` showing `sft_v4_epoch6_merged` in v4) and inference-loading-path evidence (`LoRARequest` in v5 hybrid). v5 is the only true unmerged adapter deployment.
- **Insight worth integrating**: v3.1 inherits v5's deployment posture exactly (unmerged LoRA via `LoRARequest`). Confirmed-correct path.

### S4) Quantization table corrects my own memory
- **What would have to be true**: prior memory claims about v5 = "LoRA BF16 not QLoRA" needed direct script verification.
- **Evidence supporting it**: Cursor reads `train_sft_v5.py` and confirms `AutoModelForCausalLM.from_pretrained(..., torch_dtype=torch.bfloat16)`, no `BitsAndBytesConfig`, optimizer `adamw_torch`. Only v1 used 4-bit loading + Unsloth + `adamw_8bit`.
- **Insight worth integrating**: my session memory already reflected this correction but Cursor's direct script-level evidence makes it bulletproof. v7 builds on bf16 LoRA, no quantization.

### S5) memo_test_v5 reconciliation is the cleanest causal story for v5 break-even
- **What would have to be true**: memo_test scored 20/20 at epoch 12, yet v5 was break-even (~0.646). The reconciliation must explain both.
- **Evidence supporting it**: Cursor's three-factor reconciliation — gate-mismatch (test measured exactly what training optimized, not what Kaggle scores), composition-mismatch (87.72% T1+T2 biases toward easy-pattern reinforcement), dual-path context (391 trained + 552 base partition). All three are concrete and mutually-reinforcing.
- **Insight worth integrating**: v7 must avoid all three. v3 does: pilot is plumbing-only (not selection gate), wrong-residual composition (inverts the T1+T2 bias), per-item route gate replaces blanket trained-ID routing.

### S6) Trace-coherence audit (17/17) was a real audit, not vibes
- **What would have to be true**: Part 8's structural-incoherence hypothesis had to be testable on v5 dataset directly.
- **Evidence supporting it**: Cursor sampled 17 items stratified across T2/T3/T4/T5, parsed `<think>` blocks, compared trace conclusion to `\boxed{}` label, found 17/17 coherent. Also reports caveats — small sample, MCQ-heavy (12/17), branching traces don't count as incoherent.
- **Insight worth integrating**: Part 8's hypothesis is at least partially refuted at this sample size; v7 should treat trace-coherence as a watch-item, not a closed problem. (Caveat noted in Red-team R1.)

### S7) Hybrid routing artifact characterization clarifies the v5 deployment surface
- **What would have to be true**: dual-path 391-adapter + 552-base routing had to be evidence-tied to actual production submission artifacts.
- **Evidence supporting it**: Cursor reads `slot1/routing_manifest.csv` (943 rows, adapter=391, base=552 exact partition), `adapter_v5_run.jsonl` (391 items, 388 with 3/3 votes, 3 with 2/3), `sc16_base_run.jsonl` (43 rows base). Set-relations confirmed disjoint between adapter and sc16 targets.
- **Insight worth integrating**: confirms v5's deployment topology directly. v7 follows similar topology but with per-item route gate replacing the static 391-ID partition.

---

## Section 2: Red-team

### R1) Trace coherence 17/17 sample is too small to refute a global pattern
- **Failure mode**: Cursor reports 17 items audited, 0 mismatches, then writes "structural coherence risk remains a valid hypothesis to test at larger scale, but it was not evidenced in this sample window." This is the right epistemic caveat, but the bottom-line "Part 14.E refuted Part 8" interpretation downstream in our session memory may have over-collapsed this.
- **Concrete risk**: at 391-item scale, ~5% structural incoherence rate (which would still be 20/391 affected items) would not surface in a 17-item sample with 95% probability. v7's larger trained set (180-200 items) could surface 9-10 incoherent traces if the rate is even modestly nonzero.
- **Mitigation needed**: v3.1 should add a trace-coherence check to the full-train output as part of Phase 4 evaluation (cheap to compute — extract `<think>` conclusion vs `\boxed{}` and flag mismatches). Default: ≤2% incoherence rate to pass.

### R2) "Easy-heavy" interpretation of 87.72% T1+T2 doesn't account for scored-slice composition
- **Failure mode**: Cursor frames v5's T1+T2 dominance as the root composition error. But the SCORED 283-item slice composition is unknown. If the scored slice is also heavily T1+T2 (mirroring the full 943 distribution), then v5's mix was at least partially correct in target selection — the failure was methodological (proxy metric), not compositional (wrong tier mix).
- **Concrete risk**: v7's wrong-residual targeting inverts to T3/T4/T5-heavy. If the scored slice is heavily T1+T2 like the full population, v7 trains on items NOT in the scored slice. Per-item route gate catches this (no regressions even on missed items) but ceiling is capped.
- **Mitigation needed**: explicit acknowledgment in v3.1 that tier composition of trained items needs MATCHING to expected scored-slice tier composition where possible. Wrong-residual targeting is correct; tier-mix-aware sampling within wrong-residual is an enhancement.

### R3) No per-item adapter-vs-base win/loss analysis on v5's 391-item trained set
- **Failure mode**: this is the missing meta-analysis. v5 was break-even (~0.646) on the full 943, deployed as adapter on 391 + base on 552. But Cursor's research never decomposes: of the 391 adapter-routed items, on how many did the adapter actually flip a base-wrong-to-correct, and on how many did it regress base-correct-to-wrong?
- **Concrete risk**: without this decomposition, v7's wrong-residual targeting assumes adapter HELPS on wrong-residual items. v5's experience could either confirm (adapter wins on hard items) or refute (adapter wins on easy items, regresses on hard) the assumption. We're flying blind on the directly-evidenced lesson.
- **Mitigation needed**: Phase 0 of v3.1 should include this decomposition as part of wrong-residual manifest build. Cheap — we have `adapter_v5_run.jsonl` and base inference, just need to compute per-item win/loss against `MASTER_ANSWERS`.

### R4) No MCQ vs free-form analysis of adapter behavior
- **Failure mode**: v4 dataset was ~206/391 MCQ-like; v5 dataset is similar. Different reasoning structures (MCQ option-elimination vs free-form derivation) likely benefit from adapter differently. Cursor's research never addresses this split.
- **Concrete risk**: v7 wrong-residual targeting may inadvertently bias toward one item type. If adapter helps MCQ more than free-form, and v7's wrong-residual set is free-form-heavy, we lose adapter leverage.
- **Mitigation needed**: track MCQ vs free-form ratio in v7 wrong-residual manifest. Pilot eval (Phase 2) should report flip rate stratified by item type. Not blocking, but a watch-item.

### R5) Internal-evidence-only methodology has zero external validation
- **Failure mode**: Cursor's research is exclusively repo-internal (training logs, scripts, artifacts). No external citations (AIMO winners, Numina, PEFT issues, vLLM behavior). This makes it bulletproof against fabrication but provides no cross-check on whether the failure-mode lessons are universal or repo-idiosyncratic.
- **Concrete risk**: a lesson like "memorization is anti-signal for deployment" — is it specifically a v5 phenomenon, or is it universal across math SFT? If the latter (which Opus 4.8 / ChatGPT browsed confirmed in follow-up), Cursor's research aligns. If the former, v7 might be over-correcting.
- **Mitigation needed**: cross-check Cursor's lessons against the Opus/ChatGPT/Gemini follow-up research from this session. AGREE & LOCK only items where both internal and external evidence converge.

### R6) Trace generator (teacher) heterogeneity left as open question, not analyzed
- **Failure mode**: v3 dataset had 366 Sonnet + 104 GPT-5.4 + 23 GPT-OSS — heterogeneous teacher mix. Cursor lists "Is teacher-source consistency (single-teacher vs mixed) materially causal here, or confounded with dataset quality/selection?" as an open question but doesn't analyze it.
- **Concrete risk**: v7 trace generation method (single Sonnet vs mixed) is not pinned. If teacher heterogeneity is materially negative, v7 should standardize on one teacher.
- **Mitigation needed**: v3.1 should declare a teacher policy for v7. Default: single teacher (Sonnet) for trace generation to eliminate heterogeneity as a confounder.

### R7) "Deployment scope" framing assumes targeted-error lever is correct without evidence
- **Failure mode**: Cursor concludes "adapter should be built and judged as a targeted-error lever, not a broad global-improvement lever." This is plausible but only weakly evidenced — v5 broad approach broke even, but the methodological errors (proxy metric, composition) are larger confounds than the broad-vs-targeted dimension.
- **Concrete risk**: v7 commits to targeted scope based on a hypothesis that broad doesn't work, when broad MIGHT work if methodology is fixed.
- **Mitigation needed**: Phase 4 cross-check on tnr-1 (held-out validation slice) should be EXPANDED to include some items from outside the wrong-residual set, as a probe for whether adapter generalizes broadly. If it does, v7's scoped framing is conservative-but-correct (no downside). If it does NOT, scoped framing is essential.

### R8) Open questions surfaced but no closure path declared
- **Failure mode**: Cursor lists 5 open questions in "Open questions / unknowns to resolve before proposing v7" but no closure protocol — which questions block v7, which are nice-to-have, which can be answered during v7 execution?
- **Concrete risk**: these questions might re-surface mid-execution and cause indecision.
- **Mitigation needed**: v3.1 should declare which Cursor open-questions are CLOSED by v7's design choices, which are PARKED as known unknowns, and which are ACTIVELY ANSWERED during v7 execution.

---

## Section 3: AGREE & LOCK

These should be locked for v7 execution unless Rain explicitly overrides:

1. **v5 was bf16 LoRA, NOT QLoRA** (only v1 was QLoRA). v7 builds on bf16 LoRA. Locked.
2. **v5's 87.72% T1+T2 composition was the structural compositional error**. v7's wrong-residual targeting inverts this. Locked.
3. **memo_test on training items is anti-signal for deployment**. v3 makes pilot plumbing-only; route-sim on full train is the real gate. Locked.
4. **Unmerged LoRA via `LoRARequest`** is the correct deployment posture (v5's confirmed approach). v3 inherits. Locked.
5. **v1 trace truncation pathology** is a cautionary precedent. v3 uses 81920/65536 token budget on T4/T5 items. Locked.
6. **Held-out validation slice** must be the only checkpoint selection gate (v3 Phase 4 already does this on tnr-0 trained ckpts; cross-check on tnr-1 held-out items). Locked.
7. **Targeted-error scope** (vs broad global improvement) is the v7 framing. Locked, but see R7 for cross-check addition.
8. **Per-version deployment-mode table** (v1/v3/v4 merged; v5 adapter) is the correct evidence base for "stay unmerged in v7". Locked.

---

## Section 4: DISAGREE / DIVERGE

### D1) Trace coherence is NOT a closed problem
- **Cursor's position** (implicit, via "not evidenced in this sample window"): 17/17 sample suggests Part 8 hypothesis is not surfaced, but acknowledges small sample.
- **My counter-position**: at 391-item scale, a 5% incoherence rate would still mean ~20 affected items, unlikely to surface in a 17-item sample. v3.1 should add trace-coherence check to Phase 4 output as a watch-item, with abort threshold (≤2% incoherence to pass).
- **Evidence to resolve**: run trace-coherence check on v5's actual 391-item adapter output (`adapter_v5_run.jsonl`). If <2% incoherent globally, hypothesis truly refuted. If ≥5%, hypothesis active and must be a v7 abort gate.

### D2) Per-item adapter win/loss decomposition on v5 should happen BEFORE v7 execution
- **Cursor's position**: research stops at "v5 was break-even on full 943" with hybrid-routing structure described.
- **My counter-position**: the per-item decomposition (adapter win, adapter loss, adapter tie vs base) on v5's 391-item set is the most direct evidence we have for "where adapter actually helps". It should be computed in Phase 0 of v3.1 and used to inform wrong-residual composition.
- **Evidence to resolve**: ~30 minutes of compute on existing `adapter_v5_run.jsonl` and base inference + `MASTER_ANSWERS`. Produces an adapter-vs-base per-item delta table.

### D3) Teacher heterogeneity policy needs explicit declaration in v7
- **Cursor's position**: left as open question.
- **My counter-position**: v3.1 should default to single-teacher Sonnet trace generation for v7's wrong-residual training set. Eliminates teacher-source confound as a variable. If we want to test teacher heterogeneity, run as a follow-up post-deadline.
- **Evidence to resolve**: not needed — this is a design decision, default to conservative.

---

## Section 5: GAPS

### G1) No per-item adapter performance decomposition on v5 (covered in D2)
- **Need**: Phase 0 of v3.1 must include this. Without it, v7's composition choice rests on assumption not evidence.
- **Candidate close**: ~30 min compute on existing artifacts.

### G2) No MCQ vs free-form adapter behavior stratification
- **Need**: should be tracked in v7 pilot (Phase 2) and full-train evals (Phase 4). Cheap to add.
- **Candidate close**: extend pilot eval to report flip rate stratified by item type. Negligible cost.

### G3) No external cross-check between Cursor's internal lessons and external practitioner evidence
- **Need**: cross-reference Cursor's lessons against Opus 4.8 / ChatGPT / Gemini research from this session. Where both converge → strongest signal. Where they diverge → flag for investigation.
- **Candidate close**: ~15 min synthesis exercise. Can be done as part of v3.1 patch writeup.

### G4) No tier composition matching of wrong-residual to expected scored-slice composition
- **Need**: per R2, if scored 283-slice is heavily T1+T2, v7 should ensure wrong-residual training set is not 100% T3+ stratified.
- **Candidate close**: add tier-mix-aware sampling within wrong-residual to Phase 0. Maintain proportionality to full-population distribution while still excluding base-correct items.

### G5) No declared closure protocol for Cursor's 5 open questions
- **Need**: explicit mapping of each Cursor open question to CLOSED / PARKED / ACTIVELY-ANSWERED-IN-V7 status.
- **Candidate close**: section in v3.1 mapping each.

### G6) No empirical confirmation that "targeted-error lever" outperforms "broad improvement" — only by exclusion of v5
- **Need**: addressed by R7 mitigation (expand Phase 4 cross-check to include some items outside wrong-residual).
- **Candidate close**: extend tnr-1's held-out validation slice to ~15-20 items, ~5 of which are outside wrong-residual scope.

---

## Final synthesis (informational, not part of mandatory format)

Cursor's research and my v3 plan converge significantly on the strategic direction. Disagreements are minor refinements (D1-D3) and gaps are tractable in <90 min total. The most actionable single addition to v3.1 from this review is **G1/D2: per-item adapter win/loss decomposition on v5** before v7 execution. Phase 0 should include this.

The most important AGREE & LOCK is **the precise tier mix verification (87.72% T1+T2)** — this is the single most actionable composition lesson for v7. Cursor's evidence-tied corroboration of my session memory makes this rock-solid.

R5's recommendation to AGREE & LOCK only items where Cursor's internal evidence converges with external (Opus/ChatGPT/Gemini) evidence is the right epistemic standard. Almost all of Cursor's findings pass this filter; the trace-coherence watch-item (R1/D1) is the one where I'd want sharper external evidence before fully closing.

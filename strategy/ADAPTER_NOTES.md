# ADAPTER_NOTES.md — claude_strategy Phase A repo read

**Owner**: claude_strategy
**Date**: 2026-05-31 (Day 9)
**Purpose**: Capture all adapter-related learnings from repo, oriented toward "what would we do DIFFERENTLY for v7?"
**Pair-read**: claude_vscode (Cursor) doing parallel into `ADAPTER_NOTES_CURSOR.md`

---

## PART 1 — Per-attempt summaries

### SFT v1 (2026-05-06) — CATASTROPHIC FAILURE

**Composition** (per `inference/adapters/sft_v1_postmortem/scripts/`):
- 3-arm dataset: NuminaMath + OpenR1 + Frugal
- prepare scripts for each arm exist in sft_v1_postmortem/

**Hyperparams**: train_qwen3_qlora.py exists but not deeply read here

**Outcome**: Catastrophic. Model learned to RAMBLE without ever emitting `\boxed{}`.

**Root cause (from v3 log retrospective + memory)**:
- `max_seq_length=4096` truncated **50%+ of training traces** (R1-distill outputs were much longer)
- Model learned to start reasoning but never converge to boxed answer (mid-trace cutoff was the dominant signal during training)
- Trained the wrong behavior

**What we'd do differently for v7**:
- Profile token length distribution FIRST (p50/p90/p99/max)
- Set max_seq_length ≥ p99 + safety margin (or filter dataset to fit)
- Verify: 0% trace truncation in dataset preprocessing

---

### SFT v2 — NOT ATTEMPTED

No artifacts. Per v3 log: "v2 was not attempted." Likely a planned redesign that got skipped in favor of v3.

---

### SFT v3 (2026-05-22) — First successful run, never used for picks

**Dataset**:
- File: `sft_v3_dataset_final.jsonl` (LFS)
- Items: **594** (tier mix: 392 R1/R2 reinforcement + 154 W2 + 48 W1)
- Source: teacher-labeled competition items
- Format: `[system, user, assistant]` 3-message structure, 100% had `</think>` + `\boxed{}`
- Token profile: p50=71 words, p90=215, p99=400, max=475 (all <4096 cap, no truncation)

**Hyperparams**:
- Model: `Qwen/Qwen3-4B-Thinking-2507` (bf16, no quantization)
- LoRA: r=64, alpha=128, dropout=0.05, target_modules=q,k,v,o,gate,up,down (all)
- Training: 8 epochs, bs=2, ga=8 (effective 16), lr=2e-4, cosine, warmup_ratio=0.05, wd=0.01
- max_seq_length=4096, packing=False (CRITICAL — packing breaks `<think>` attention)
- save_strategy=epoch (all 8 checkpoints saved)

**Loss curve**: 0.59 → 0.0020 over 8 epochs (deep memorization by ep5-8)

**Smoke tests** (10 items, fixed seed=42, all R1/R2 tier from training set):
- Epochs 1, 4, 8: all 0% no-box, 0% missing `</think>`, 100% MATCH against teacher answer

**CRITICAL FLAW**: Smoke test items ALL from training set → memorization tautology. No held-out validation. Memorization on W1/W2 (the actually-hard items) was never tested.

**What we'd do differently for v7**:
- Held-out validation set (50 items) DRAWN FROM W1/W2 ONLY
- Don't trust memorization on training items as success signal
- Pre-flight: verify loss ∈ [0.5, 5.0] on untrained held-out batch BEFORE committing to full run

---

### SFT v4 (2026-05-XX) — Outcome unclear, not used for picks

**Dataset**: `data/sft_v4_dataset.jsonl`, 391 items, "clean, MCQ options, xhigh excluded"

**Hyperparams** (from train_sft_v4.py):
- Model: same Qwen3-4B-Thinking-2507
- LoRA: r=64, alpha=128, dropout=0.05
- Training: 8 epochs, lr=2e-4 (other config not extracted in this pass)
- adapter_config: alpha=128, r=64, dropout=0.05 (matches v3)

**Variant**: `sft_v4_dirty` exists on Thunder tnr-0 disk only — experimental, not canonical, not needed for submission per UNTRACKED_V4_DIRTY.md

**Outcome**: Not extensively documented in what I read. Checkpoint-588 exists. Per memory #12: "v4 unclear."

**What we'd do differently for v7**: Carry forward v3's hyperparams + v5's memorization optimizations, but address the validation gap.

---

### SFT v5 (2026-05-25) — Memorization succeeded; generalization didn't (THE KEY POSTMORTEM)

**Dataset**:
- File: `data/sft_v5_dataset.jsonl`
- Items: **391** (lettered MCQ user msgs + 14 trace fixes: 5 MCQ replacements + 9 format fixes)
- Critical issue: **87% T1-easy items** (structural diet — low signal)

**Hyperparams** (DIFFERENCES from v4 — designed for max memorization):
- num_train_epochs: **16** (was 8)
- lr_scheduler_type: **linear** (was cosine)
- **lora_dropout=0.0** (was 0.05) — zero dropout for max memorization
- per_device_train_batch_size: 4 (was 1), gradient_accumulation_steps: 1 (was 4) — effective bs unchanged
- weight_decay=0.0 — no L2
- save_strategy=steps, save_steps=196 (every ~2 epochs), save_total_limit=8

**Result memo test** (`memo_test_v5.py`): **20/20** consistent → declared "winner" → kept as LoRA adapter (no merge)

**THE CRITICAL MISTAKE** (canonical postmortem at `inference/runs/adapters/sft_v5/findings.md`):
> The 20/20 memorization metric tested whether v5 could reproduce 20 items from its TRAINING SET. This is a **TAUTOLOGY**, not evidence. Any modestly-trained 14-epoch model WILL memorize 391 items it was trained on. The 20/20 score said nothing about test-set generalization.

**Reality check**: v5 adapter on real inference = ~0.646 (near base, NOT improved). +info_4 diagnostic (with answer-sheet swap) = 0.671 — but that was the swap, not the adapter.

**Locked discipline correction**:
> No metric is trustworthy until validated on items NOT in training set. Include a held-out validation set of 50 items scored against teacher consensus, separate from training. Decide viability on that, not memo tests.

**THE LEVER — Rain's targeted memorization insight (the v7 thesis)**:
1. Identify 200-300 items Qwen base gets WRONG (low SC agreement on private 943)
2. Get verified correct answers (multi-teacher consensus + Wolfram)
3. Train v7 adapter on those items + verified answers
4. At inference: run BOTH base Qwen AND v7-adapter. Use SFT-adapter answer ONLY for items it was trained on (or where base+adapter agree → high-confidence override).

Differences from v4/v5 mistakes:
- v1/v4/v5 trained for *general* improvement → failed
- v7-targeted: narrow scope = "items we know base gets wrong"
- No claim of generalization — only USE adapter where explicitly trained
- Held-out validation still required to confirm targeted memorization works WITHOUT degrading base

---

## PART 2 — Cross-cutting learnings

### A) Failure mode taxonomy across v1/v3/v4/v5

| Failure mode | v1 | v3 | v4 | v5 |
|---|---|---|---|---|
| Trace truncation in training data | ✗ FATAL | ✓ ok (p99=400 < 4096) | ✓ ok | ✓ ok |
| Wrong validation methodology | n/a | ✗ memo-only | ✗ memo-only | ✗ memo-only (canonical lesson) |
| Format-broken at inference | ✗ ramble | ✓ | ✓ | ✓ |
| Dataset bias (T1-easy %) | n/a | tier-mixed (66%R1/R2) | unclear | **✗ 87% T1-easy (structural)** |
| Held-out validation done | ✗ | ✗ | ✗ | ✗ |
| Real Kaggle improvement | ✗ | ✗ not used | ✗ not used | ✗ break-even |

### B) Hardware/compute constraints discovered

- **Thunder A100 80GB**: handles full QLoRA + 16-epoch r=64 training in ~28-35 min (v5 was 28min on H100; v3 was 35.8min on A100 80GB)
- **bitsandbytes import**: requires `LD_LIBRARY_PATH=/usr/local/cuda/targets/x86_64-linux/lib:$LD_LIBRARY_PATH` (libnvJitLink.so.13 needed)
- **HF cache**: must be on persistent disk `~/hf_cache` (ephemeral wiped on stop) → `HF_HOME=~/hf_cache`
- **LFS**: dataset files MUST be LFS-pulled before training, else 3-line pointer fails silently
- **tmux**: long-running training needs tmux (apt-get install -y tmux)
- **trl 0.24.0 breaking changes**: requires custom AssistantOnlyCollator (DataCollatorForCompletionOnlyLM removed), SFTConfig replaces TrainingArguments, processing_class replaces tokenizer param
- **Qwen3 chat template**: no `{% generation %}` markers → `SFTConfig(assistant_only_loss=True)` fails → must use custom collator
- **packing=False CRITICAL**: packing breaks `<think>` attention spans

### C) Data quality issues that limited results

- **v1**: trace truncation poisoned training (FATAL)
- **v5**: 87% T1-easy is structural — model learned the easy items, gained nothing on hard ones
- **All versions**: training items ARE test items (transductive task per Piazza-confirmed allowed). This is intentional but eliminates traditional generalization signal — must use held-out FROM THE SAME PRIVATE SET to validate.
- **Teacher labels**: only available for some items. Multi-teacher consensus + Wolfram needed for v7-quality labels on hard items.

### D) Evaluation methodology pitfalls

- **Memo test is tautology**: tested on training items only → memorization confirmed but generalization unknown. CANONICAL LESSON.
- **Local judger has 28pp gap from Kaggle** (memory #2): "use only for degenerate-output detection, never accuracy decisions"
- **Pseudo-gold from answer sheet** can be circular (gold leakage): items where derived gold = teacher/sheet consensus that was BUILT FROM prior runs
- **Kaggle is the only valid measurement** (memory #2)
- **sft_v5 eval pathology checklist** (per `inference/runs/adapters/sft_v5/findings.md` carry-forward):
  1. Log per-run: `missing_boxed`, `missing_boxed_mcq`, `missing_boxed_free`, `avg_gen_tokens`, `cutoffs`
  2. Trigger threshold: if `missing_boxed > ~10%`, rambling pathology likely active
  3. Fallback decode: run second eval with `rp=1.1`
  4. Decision rule: if fallback rp=1.1 rescues ≥50% no-box failures → SFT pathology, baseline rp=1.0 understates capability; if <20% rescue → real model gap
  5. **DO NOT default rp=1.1 on base Qwen** — only on observed pathology

### E) What we learned about Qwen3-4B-Thinking-2507 specifically

- **Recommended sampling** (LOCKED, memory #20): temperature=0.6, top_p=0.95, top_k=20, min_p=0, presence_penalty (not repetition_penalty)
- **Greedy contraindicated** for thinking mode (official Qwen guidance)
- **Token budget**: max_tokens=49152, thinking_budget=24576; hard items 81920/65536
- **NoThinking**: `enable_thinking=False` is a NO-OP on this model — must use prefill: `"Okay, I think I have finished thinking.\n</think>\n\n"`
- **Repetition collapse at default decoding** = decoding-config issue, NOT weight-space collapse; rp=1.1 partially recovers
- **SFT-merged variants** exhibit rambling pathology that rp=1.1 rescues (R14 audit lesson). Adapter form (not merged) avoids this — keep v7 as adapter.

### F) Inference-mode integration

- `inference/scripts/run_hybrid_inference.py` has `--mode adapter` and `--mode base` support
- `inference/scripts/eval_adapter.py` exists for adapter evaluation
- adapter loading: PEFT auto-loads adapter_config.json + adapter_model.safetensors
- 505MB LFS files (v5 size; v7 likely similar at r=64)

---

## PART 3 — Open questions for the 4-LLM research dive (Phase C)

### 3.A) Deployment architecture drives validation — corrected framing

**PRIOR DRAFT WAS WRONG. RAIN CORRECTED (2026-05-31)**:

An earlier version of this section said "what v5 should have measured: on the 552 items NOT in training, does adapter beat base?" That framing implicitly assumed single-path deployment (adapter replaces base across the full 943). Under DUAL-PATH deployment — adapter routes ONLY for items Qwen base gets wrong, base handles the rest — that statement is irrelevant. Adapter never sees the 552, so we don't care if it beats base on them.

**What the relevant validation actually is under dual-path**:

The only question: "On items adapter was trained on, does it produce the correct answer AT INFERENCE TIME (with real sampling, not teacher-forced training conditions)?"

If yes → dual-path deployment locks in adapter-right on those items. Base handles everything else. Net = strict improvement over base.

**The actual v5 failures (corrected)**:

1. **Training data composition was wrong target**: v5 trained on 87% T1-easy items = mostly items Qwen base already gets right. Under dual-path, these items route to base anyway → adapter memorizing them gains nothing. Training set should have been Qwen-WRONG items only.

2. **Deployment model didn't match training intent**: v5 was deployed single-path (adapter replaces base on full 943). On items NOT in training, adapter REGRESSED vs base. Net = break-even because gains on trained items were cancelled by losses on untrained items.

3. **Memo test would have been meaningful under dual-path** (if v5 had been deployed dual-path): asking "does adapter produce correct answer at inference for items we trained it on?" IS the deployment question if we route only those items to adapter. NOT a tautology under that architecture.

**The genuine concern with memo tests** (under dual-path, this is what we actually need to be careful about):

Training time = teacher-forced loss computation. Inference time = autoregressive sampling with real decoding params (temperature, top-p, etc). Memorization can fail to transfer. The memo test must mirror deployment conditions:
- Generate with sampling (temperature, top-p), not greedy/teacher-forced
- Multiple SC samples per item to check consistency
- Verify the model's generation patterns are stable enough that the memorized answer reliably emerges
- Verify generation doesn't catastrophically fail (no-box, ramble, missing `</think>`)

So memo test design under dual-path = "training items + inference conditions + multi-sample consistency check + format compliance check."

**Revised validation criteria under dual-path** (replacing my earlier 4-criterion rule, which was written for single-path):

1. **Same items as deployment**: test items = adapter's training items (because that's what adapter will see at inference)
2. **Same conditions as deployment**: inference time with real sampling, not teacher-forced training conditions
3. **Right comparison**: did "Qwen-wrong on this item" convert to "adapter-right on this item"? (Not "adapter beat base" in the abstract)
4. **Right metric**: correctness per verified gold (Wolfram_HIGH / unanimous_teachers), not just format presence

The previous "test items NOT in training" rule (which I wrote earlier) was correct ONLY for single-path full-replacement. For dual-path, it's the wrong rule.

### 3.A.1) Architecture options to consider (Rain's "keep minds open" directive)

PRIMARY (the v7 thesis from sft_v5 findings):
- **Dual-path with selective routing**: train adapter on Qwen-wrong items; at inference, route only those items to adapter. Base handles everything else. Clean attribution, low risk.

ALTERNATIVES to evaluate in Phase C research dive:
- **Single-path full-replacement (the v5 deployment that failed)**: might work if training data is dramatically better (Qwen-wrong items only, broader coverage). v5's failure doesn't mean this is dead; v5's specific training data was wrong.
- **Logit interpolation (WiSE-FT-style)**: at every decode step, blend base + adapter logits with some weight δ. Lets us "dial in" adapter influence. Per memory: "scale lora_alpha by delta (delta=0.5 prior, no retraining)". Untested for math.
- **Confidence-gated routing**: use adapter answer ONLY when adapter's top-logit confidence exceeds threshold; else fall back to base. Self-policing.
- **Multi-adapter ensemble**: multiple narrow specialists (one per category/tier), route per item characteristics.
- **In-context learning instead of SFT**: bake verified answers into prompts via retrieval; no training needed. Faster iteration.
- **GenSelect at inference**: have base + adapter both generate, use a third call (also Qwen, same model) to judge which is better. Memory #18 says GenSelect is allowed (same-model multi-pass).

The PRIMARY (dual-path) is the path we lean toward because it's cleanest and aligns most closely with v5 postmortem learning. But Phase C research must surface what OTHER teams actually did.

### 3.A.2) The deeper validation principle (restated under dual-path)

A validation test is meaningful only if it tests THE DEPLOYMENT QUESTION. For dual-path:
- The deployment question is "for items in adapter's training set, does adapter at INFERENCE TIME produce the verified correct answer reliably?"
- Inference time = autoregressive sampling with real decoding params (not teacher-forced)
- Reliably = multiple samples agree, not just one lucky generation
- Verified correct answer = the labeled gold (Wolfram_HIGH / unanimous_teachers), not the adapter's own training signal

For single-path full-replacement: would also need generalization to untrained items (the original framing). This is why dual-path is conceptually simpler.

For logit interpolation / confidence-gated / GenSelect: validation needs to test the BLEND, not the adapter alone. More complex.

### 3.A.3) Why this matters for v7 design

The deployment architecture choice changes EVERYTHING downstream:
- Training data selection (Qwen-wrong only for dual-path; broader for full-replacement)
- Training duration (more epochs = better memorization for dual-path; risk of overfit for full-replacement)
- Validation strategy (memo-at-inference for dual-path; held-out generalization for full-replacement)
- Integration into Pick B (routing logic for dual-path; full CSV replacement for full-replacement)
- run_inference() code complexity (dual-path needs routing logic in code; full-replacement is simpler)

Phase D MUST decide architecture FIRST, then design v7 accordingly.

### 3.B) Cheap validation methods to brainstorm + decide

**The constraint**: must validate adapter quality WITHOUT burning Kaggle slot, in <30 min, on commodity Thunder hardware. Brainstorm pool — pick best 2-3 for v7:

1. **Held-out subset accuracy** [primary candidate]
   - 30-50 items from wrong-Qwen pool, NOT in training
   - Run base + adapter, compare accuracy
   - Cost: ~5-10 min on A100
   - Quality: directly measures what we care about (correctness on unseen items from same distribution)

2. **Format compliance check** [primary candidate — catches v1-style failures]
   - Sample 10-20 outputs from adapter
   - Check `\boxed{}` presence, missing `</think>`, ramble patterns, missing-box rate
   - Cost: ~2-5 min
   - Quality: catches catastrophic failures fast; doesn't measure correctness

3. **Single-token-loss check** [quick, indirect]
   - Feed test item, measure cross-entropy loss on correct-answer position
   - Compare adapter loss vs base loss on same items
   - Adapter should have lower loss on training items (memorization) AND on similar held-out items (generalization)
   - Cost: ~1-2 min per item
   - Quality: indirect signal; reveals "model is more confident" but not "model is more correct"

4. **Logit comparison** [diagnostic]
   - For test item, look at top-5 logits from base vs adapter
   - Did adapter shift probability mass toward correct answer?
   - Does it still consider other answers plausible (good) or did it collapse to single answer (overfitting)?
   - Cost: ~1 min per item
   - Quality: helps interpret WHY adapter is doing what it does

5. **Anchor item regression test** [primary candidate — catastrophic-forgetting catch]
   - 5-10 items where base ALREADY gets right (R1/R2 items)
   - Adapter must ALSO get right on these
   - Cost: ~2-3 min
   - Quality: catches catastrophic forgetting (adapter learning hard items but breaking easy ones)

6. **Item-similarity test** [generalization probe]
   - Pick test items SIMILAR to training items (same category, same difficulty)
   - Adapter should beat base on these if it learned generalizable patterns
   - Cost: ~5-10 min
   - Quality: distinguishes "memorized specific items" from "learned category-level patterns"

7. **Held-out tier check** [stratified probe]
   - Train on T2/T3 items, hold out 10 from each tier
   - Measure adapter accuracy on held-out per-tier
   - Cost: ~5 min
   - Quality: shows whether adapter learns tier-level structure

8. **Catastrophic forgetting check** [variant of #5]
   - Adapter performance on items base Qwen excelled at
   - If much worse → forgetting is real
   - Cost: ~5 min
   - Quality: focuses specifically on the failure mode where adapter trades base ability for new ability

9. **NoThinking baseline** [interesting diagnostic]
   - Run adapter without thinking-mode prefill
   - If accuracy similar to with-thinking → model truly memorized (skip reasoning)
   - If accuracy drops a lot → model is doing some reasoning
   - Cost: ~5 min
   - Quality: helps characterize what adapter learned

10. **Confidence calibration** [advanced]
    - For items adapter is "confident" (high top-logit), is it more often right than base?
    - If confidence is meaningful → trust selective routing
    - If confidence is meaningless → routing is risky
    - Cost: ~10 min
    - Quality: validates routing strategy specifically

**Recommended cheap-test bundle for v7 (to be confirmed in Phase D)**:
- Pre-training: format pre-check on dataset + tokenizer round-trip + token length profile
- Post-training mandatory: (1) Held-out subset accuracy + (2) Anchor regression test + (3) Format compliance check
- Optional diagnostic: logit comparison on a few hand-picked items if results are surprising

### 3.C) Effective smoke tests by phase

**Pre-training smoke (before committing to full run, ~10 min total)**:

1. **Dataset preflight** (~1 min):
   - All items parseable as JSON
   - 100% have `</think>` and `\boxed{}`
   - Token-length distribution: max ≤ max_seq_length (no truncation)
   - No duplicate items
   - Labels present and non-empty

2. **Dry run** (~3 min): 
   - Train for 2 steps with full config
   - Verify loss is finite (not NaN)
   - Loss in plausible range (0.5-5.0 nats)
   - Gradient norms not exploding
   - Memory fits in GPU

3. **Tokenizer round-trip** (~1 min):
   - Encode then decode test items
   - Verify no info loss
   - Verify chat template correctly applied
   - Verify special tokens (`<|im_start|>`, `</think>`, etc.) present

4. **Forward-pass smoke** (~2 min):
   - Single forward pass on 3 items
   - Logits shape correct
   - No NaN/inf in logits
   - Top-5 logits reasonable (not all uniform)

5. **Pre-flight gate check** (memory #19, 1 min):
   - Disk free ≥8GB
   - GPU memory free as expected
   - Output paths writable
   - Model/adapter paths valid

**Mid-training smoke (during training, every N steps)**:

1. **Loss curve monitor**:
   - Smooth descent (no spikes after warmup)
   - Grad norms stable (0.02-0.5 range typical)
   - Mean token accuracy rising
   - Trigger pause if loss diverges or grad norms explode

2. **Optional periodic eval on held-out** (every 1-2 epochs):
   - Run adapter on 10-item held-out set
   - Track accuracy over epochs
   - Identify epoch where accuracy peaks (early stopping signal)

**Post-training smoke (before integration, ~15 min)**:

1. **Format compliance** (~3 min):
   - 10 items, check no-box rate, missing-think rate, ramble patterns
   - Threshold: <10% no-box rate (per memory #19 + v3 gate)

2. **Anchor regression** (~3 min):
   - 5 R1/R2 items base gets right
   - Adapter must also get right
   - Threshold: 100% pass (zero regression on base-easy items)

3. **Held-out subset accuracy** (~10 min):
   - 30-50 items from wrong-Qwen pool, NOT in training
   - Compute accuracy: adapter vs base
   - Threshold: adapter ≥ base + epsilon (else don't integrate)

4. **rp=1.1 pathology monitor** (per sft_v5 carry-forward):
   - If missing_boxed > 10% on held-out → fallback eval with rp=1.1
   - Decision rule per sft_v5 findings (≥50% rescue → SFT pathology)

**Integration smoke (before adding to Pick B, ~5 min)**:

1. **Per-item check on top-20 wrong-Qwen items**:
   - Adapter answers each item
   - Compare to Wolfram_HIGH / unanimous_teachers gold
   - Manual eye-check on top-5

2. **No-regression on Pick B baseline**:
   - Run Pick B candidate WITH and WITHOUT adapter overlay
   - On independent-gold subset: must not regress

### 3.D) Existing 7 research questions (unchanged)

1. **Validation methodology for transductive SFT on math competitions**:
   - When training items = test items (intentional), how do top teams validate adapter quality?
   - Held-out subset strategies that don't waste training data?
   - Kaggle-comp-winner playbook on this specifically?

2. **Selective routing at inference**:
   - How to architecturally combine base + adapter outputs?
   - Logit interpolation vs answer-level switching?
   - Confidence thresholds for routing decisions?

3. **Qwen3-4B-Thinking-2507 adapter sweet spots**:
   - Anyone published successful adapter on this exact model + math task?
   - Best LoRA r/α for this size class + dataset size?
   - Recent (2025-2026) papers on QLoRA for reasoning models?

4. **Training data composition for "items wrong" SFT**:
   - Multi-teacher consensus generation strategies that work?
   - When to use Wolfram trace vs reasoning trace?
   - Anchor item mix percentage?

5. **WiSE-FT for LoRA** (memory #scratch mention):
   - "scale lora_alpha by delta (delta=0.5 prior, no retraining)"
   - Has anyone validated this for math tasks?

6. **DeepConf** (untried, memory #scratch):
   - Fu et al. arxiv 2508.15260: logprob-weighted SC voting, 99.9% at 512 traces AIME 2025
   - Would adapter outputs benefit from this voting scheme?
   - Requires `output_scores=True` plumbing

7. **Practical "someone did it this way" anchors**:
   - AIMO competition winners + their adapter approaches
   - MATH/AIME reproductions with small (4B) models
   - Kaggle math comp gold medalists' write-ups

---

## PART 4 — Pragmatic constraints for v7 plan (Phase D)

**Timeline**: ~13-15h remaining post-research-dive (40min for research + 30min for plan + 8-11h training/eval/integration)

**Hardware**: Thunder A100 80GB (tnr-0 idle, tnr-1 running kitchen-sink ~5h)

**Conservative-first principle** (Rain's directive):
- v7 v1: small dataset (50-100 items), short train (3-5 epochs, NOT 16), held-out validation MANDATORY
- Smoke test BEFORE full run
- If first pass shows promise: iterate aggressive

**Selective routing principle**:
- Use adapter ONLY for items it was trained on
- Run base + adapter, compare
- If agree → high confidence override
- If disagree → use base (default to safer)

**Audit all actionable work**:
- Cursor cross-check on training prompt before launch
- Cursor cross-check on dataset prep before training
- Smoke test before full run
- Independent eval before integration into Pick B

**Adapter as redemption arc** (Rain's framing):
- Doesn't need to fix everything
- Goal: demonstrate the model LEARNED something + contribute SOME value
- Even +0.1-0.3pp Kaggle is a win

---

## PART 5 — Specific things I'd flag for v7 design discussion

1. **Dataset SIZE tradeoff**: v3=594 items (over-broad, never tested), v4/v5=391 items (T1-easy bias). What's the sweet spot for "items Qwen wrong"? Maybe 100-200 carefully selected.

2. **Verified labels SOURCE hierarchy**: Wolfram_HIGH > unanimous_teachers > search_GOLD. For v7, restrict training set to items where we have HIGH-confidence label.

3. **Held-out set**: 30-50 items, drawn from same wrong-Qwen pool, held back from training. Score adapter on these AFTER training. If <50% accuracy on held-out, NOT viable.

4. **Hyperparam reuse**: v5's hyperparams (16 epochs, dropout=0, linear LR) optimized for memorization. For TARGETED memorization on small set, this is probably right. Don't reinvent.

5. **Smoke test discipline**: 5-item smoke on real code path BEFORE 200-item training (memory #19 PRE-FLIGHT AUDIT).

6. **Integration test**: after training, run adapter on 20-item subset, compare to base. Verify no catastrophic degradation. ONLY THEN integrate into Pick B.

7. **Code submission impact**: if v7 adapter is in Pick B, must be in `run_inference()` for Gradescope. Add ~1h for HF Hub push + run_inference integration.

8. **rp=1.1 monitor**: per sft_v5 carry-forward, monitor missing_boxed during v7 eval. Have fallback rp=1.1 path ready.

---

---

## PART 6 — DEEPER FINDINGS (Rain pushed back on shallow first pass)

First pass missed critical distinctions. This part captures what I should have surfaced.

### 6.A) The v1 vs v3-v5 paradigm split

**v1 was a fundamentally different paradigm from v3/v4/v5.** I conflated them.

**v1 paradigm: General distillation + MERGED deployment**
- Training data: EXTERNAL (OpenR1-Math-220k, NuminaMath, Frugal) — NOT competition items
- 3 separate teacher arms, each trained separately on ~1k items, 1 epoch each
- LoRA: r=16, α=32 (small capacity), all-linear targets, dropout=0
- max_seq_length=8192 default, args allow 11000+ for long traces
- **Deployment: MERGED.** Adapter merged into base weights → produces new model file → loaded directly by vLLM as standalone model. No adapter at inference.
- Pre-flight checks (rendered chat-template, tokenized example, eval-loss on held-out 8-row batch must be in [0.5,5.0] nats). DISCIPLINE that v5 LOST.
- Outcome: smoke on openr1 5 items showed 3/5 MISSING `\boxed{}` (60% rambling rate). Catastrophe was rambling pathology at inference, NOT trace truncation alone.

**v3/v4/v5 paradigm: Transductive memorization + LoRA adapter (NOT merged)**
- Training data: 391-594 actual competition items + teacher-labeled answers
- LoRA: r=64, α=128 (large capacity)
- **Deployment: ADAPTER VIA vLLM LoRARequest.** Base weights stay clean; adapter loaded at runtime as a separate weight layer applied to base activations. Detachable.
- All trained on transductive premise (Piazza-confirmed: training-on-test is allowed)

**The merge-vs-adapter distinction matters because**:
- MERGED model is a single set of weights — adapter and base are fused. Behavioral changes from training are permanent and global.
- ADAPTER mode keeps base clean — at inference, vLLM applies the LoRA delta to base activations. Adapter can be detached, swapped, weighted, blended with multiple adapters.
- Merged models cannot do dual-path (one set of weights, can't selectively apply adapter on some items only).
- Adapter mode CAN do dual-path: run base on one set of items, run base+adapter on another set.
- R14 rambling pathology was on MERGED v2 OpenR1 model. v5 was kept as adapter — different deployment, different failure modes.

### 6.B) Dual-path infrastructure ALREADY EXISTS

`inference/scripts/run_hybrid_inference.py` is the dual-path infrastructure I missed first pass.

**Two modes, runnable independently**:
- `--mode base`: vLLM with base Qwen3-4B-Thinking-2507. Default 943 items, SC=8, 32K tokens.
- `--mode adapter`: vLLM with base + LoRARequest pointing at adapter checkpoint. Default subset via `--item-ids` file, SC=3, 4K tokens.

The script does NOT have routing logic itself — it generates two separate jsonl files. The routing/combining is downstream (the CSV merging into a single Kaggle submission).

This is exactly the architecture Rain wants for v7. We don't need to build it; we need to use it correctly.

**What we still need to build for v7 selective routing**:
- A merger script: takes base run jsonl + adapter run jsonl + routing rules → single CSV
- Routing rules logic: per-item decision of base-answer vs adapter-answer (precedence, confidence threshold, etc.)
- The smarter we make the merger, the more architecture options we unlock (logit interpolation harder, but answer-level routing easy)

### 6.C) The memo test was MORE NUANCED than I claimed

I framed memo test as "trivial" / "tautology." Actually `scripts/memo_test_v5.py` is well-designed:
- Tests 4 checkpoints: epoch 8/12/14/16
- 20 items stratified: 10 MCQ + 10 FREE
- **SC=3 at T=0.6, max_tokens=4096 — REAL inference-time sampling, not greedy/teacher-forced**
- Threshold: "3/3 consistent" = all 3 SC samples extract the training label after normalize()
- Picks best checkpoint by N items passing
- Reports MCQ vs Free breakdown separately

This DOES test inference-time stability of memorization. It IS NOT a teacher-forced loss check.

**Why it was still misleading**: it told us "adapter reliably produces correct answers on training items at inference time" — which is TRUE and IS the dual-path deployment question. But v5 was actually deployed via `slot1_adapter_v5_plus_run14b_20260525_1623.csv` — a COMBINED dual-path CSV — and the Kaggle result was still ~0.646 (near base, not improved).

**So why did v5 dual-path fail despite passing memo test?**

The v5 training set composition (per memory: 87% T1-easy):
- 87% of training items were items base Qwen ALREADY got right (T1 = high agreement, easy)
- Dual-path routing of those items to adapter gives the SAME ANSWER base would have given (correctly)
- Only ~13% of training items were items base was wrong on
- Maximum upside: 50 items (13% of 391) where adapter could ADD value
- But: were those 50 items LABELED CORRECTLY? Were they items where the labeled "correct" answer was genuinely correct on Kaggle?

So v5 dual-path failed not because memo test was wrong, but because **training set wasn't selected for residual coverage**. We routed Qwen-right items to adapter (no change), and Qwen-wrong items mostly weren't in training, so they routed to base unchanged.

The lesson for v7 isn't "redesign memo test" — it's "select training items as Qwen-WRONG residual."

### 6.D) v4 actual Kaggle outcome: 0.597 = REGRESSION

v4 was NOT break-even. Per `UNTRACKED_CHECKPOINTS.md`:
> "SFT v4 scored 0.597. The winning checkpoint (588) is tracked."

**0.597 vs base 0.646 = -4.9pp regression.**

v4 hyperparams (same as v5 except dropout=0.05 instead of 0, and 8 epochs instead of 16):
- r=64, α=128, dropout=0.05, lr=2e-4, 8 epochs, wd=0
- 391-item clean dataset, MCQ options, "xhigh excluded"

**Why v4 regressed and v5 didn't (per the evidence we have):**
- v4 was likely deployed single-path full-replacement (need to verify, but the regression magnitude suggests it)
- v5 was deployed dual-path (slot1_adapter_v5_plus_run14b) which got back to break-even
- So v5's dual-path DID prevent catastrophic regression vs v4's deployment, but failed to ADD value because training set composition was wrong

This is actually evidence FOR the dual-path architecture: it prevents the regression even when adapter doesn't help. Single-path is asymmetric risk (can regress catastrophically); dual-path is symmetric (worst case = base, upside = adapter additions).

### 6.E) Memorization is not binary — what kind matters

I treated memorization as yes/no. It's not. The adapter_v5_run.jsonl evidence shows several layers:

1. **Answer memorization** — does adapter produce the labeled answer? In v5 evidence: high (SC@3 unanimous on many items). YES.

2. **Reasoning-trace memorization** — does adapter produce the SAME reasoning steps it was trained on? Looking at adapter_v5_run.jsonl id=1 response: produces clean derivation `$\bar{x}' = \frac{9/10 \sum w_i x_i}{9/10 \sum w_i} = \bar{x}$`. This is NOT regurgitation — it's structured reasoning. So adapter learned the TYPE of solution, not just the answer string.

3. **Format memorization** — does adapter produce `<think>...</think>\n\n\boxed{ANSWER}`? Yes, consistently in evidence we have.

4. **Surface memorization vs structural learning** — adapter could be (a) literally memorizing the input→output mapping, OR (b) learning the underlying math reasoning. Both produce the same training-set accuracy. The relevant difference is generalization, which we don't measure under dual-path because we don't deploy there.

5. **Memorization robustness** — does memorization survive sampling? v5 memo test shows YES (SC@3 consistent). At T=0.6 the memorized answer dominates.

So for v7 design: we want answer + reasoning-trace + format memorization, all surviving sampling. The v5 memo test already screens for this.

### 6.F) What changed in my mental model after this deeper pass

| Topic | First pass framing | Corrected framing |
|---|---|---|
| Memo test | Tautology, says nothing | Multi-sample at inference conditions — IS the right test under dual-path |
| v5 failure | Bad validation | Bad training set composition (87% T1-easy = not residual) |
| v4 outcome | "Unclear" | -4.9pp REGRESSION (likely single-path deployment caused it) |
| v1 | Trace truncation killed it | External-distill paradigm + merged deployment + rambling pathology — different from v3-v5 entirely |
| Dual-path infrastructure | Need to build | EXISTS in run_hybrid_inference.py; need merger script downstream |
| Adapter vs merge | Conflated | Distinct deployment modes with different failure profiles |
| Memorization | Binary | Layered: answer/trace/format/robustness — each separately testable |
| Validation rule | "Items NOT in training" | Wrong for dual-path. Correct rule: "deployment conditions on items you'll actually route" |

### 6.G) Implications for v7 design (updated)

1. **Architecture default = dual-path with LoRA adapter (not merged)** — confirmed by the evidence. Single-path causes regression (v4); merged causes rambling (v1, R14).

2. **Training set composition = the actual lever** — v5 had right architecture (dual-path), wrong training set (T1-easy). v7's training set MUST be Qwen-wrong residual + verified labels.

3. **Memo test (v5 design) is the right validation** — keep multi-sample at inference conditions, stratified MCQ/Free, threshold N/20. Add per-item routing decision quality (does adapter actually help on each item vs base).

4. **Merger script is the missing piece** — combines base run + adapter run + routing rules → single CSV. Phase D should design this. Simple version: precedence (adapter answer wins if item in adapter target set). Advanced version: confidence-gated routing.

5. **Smoke discipline** — v5 lost the pre-flight gate that v1 had (eval-loss on held-out 8-row batch must be in [0.5,5.0] nats). v7 should restore this.

6. **Gradescope code impact** — `run_inference()` must execute the dual-path: invoke base run, invoke adapter run, invoke merger. Needs to be in the entry point.

---

## END OF PHASE A NOTES (with Part 6 deepening)

Synthesize with `ADAPTER_NOTES_CURSOR.md` in Phase D after both committed.

---

---

## PART 8 — TRACE-ANSWER MISMATCH (Rain's catch, 5/31) — CRITICAL v7 design constraint

**The mismatch (Rain's memory of v3/v4/v5 data construction):**

Training data construction used Sonnet for the REASONING TRACE on every item. But when Sonnet's final answer was WRONG for a question being trained, the team would swap in the correct answer from another teacher (GPT-5.4 or GPT-OSS). The reasoning trace was NOT regenerated to match — it stayed as Sonnet's (incorrect) chain of thought.

Result: training examples like
```
<think>
[Sonnet's trace concluding "...therefore the answer is B"]
</think>

\boxed{A}    ← swapped in from another teacher
```

The reasoning doesn't lead to the labeled answer. The model trains on incoherent examples.

**What the model would learn from this pattern:**

1. "Reasoning patterns are decorative" — the final box is what matters, the trace doesn't have to derive it
2. Pattern-match against trace shape (math-looking content) without doing actual derivation work
3. Trust labeled answers over self-derived ones — increases likelihood of producing answers from a "memorized lookup" rather than from reasoning

This is **directly consistent** with the adapter_v5_run.jsonl evidence (Part 6.E): adapter produces structured reasoning that LOOKS like derivation but might be pattern-matched against training data, with the answer arriving via memorized lookup, not via the displayed reasoning.

**Evidence trail to verify the mismatch claim:**

- v5 dataset (`data/sft_v5_dataset.jsonl`): I verified earlier that 391/391 items have `source='sonnet'` — every trace from Sonnet
- v3 dataset (per Cursor's read): "Sonnet 366, GPT-5.4 104, GPT-OSS 23" — most traces from Sonnet, some from others
- Need to verify: when source='sonnet' but final answer != Sonnet's actual answer, is the trace's conclusion misaligned with the boxed answer? Would need to either parse trace conclusions or check answer-history per item.

**For v7 design (this becomes a primary constraint):**

Training examples must have COHERENT trace+answer pairs:
- Reasoning trace must actually arrive at the labeled answer through valid math
- If teacher X got answer A and teacher Y got answer B, use trace from whichever teacher matches the verified-correct answer
- If NO teacher's natural trace matches the verified-correct answer, REGENERATE the trace (don't construct a Frankenstein)

**Fallback options for trace regeneration (Rain's note):**

1. **dataApp** has proven it can quickly generate responses — not ideal but available
2. **Wolfram step-by-step output** — for items where Wolfram has HIGH confidence, its derivation could become a trace template (would need formatting layer)
3. **Multi-teacher consensus trace** — pick the teacher whose answer matches verified-correct AND whose trace is coherent
4. **Self-derivation from Qwen at high SC** — for items where Qwen does converge on correct answer in some SC samples, harvest those traces

**Critical Phase C research questions added (these are now PRIMARY, not secondary):**

A. **Trace coherence as SFT data quality**: how much does trace+answer mismatch hurt SFT for reasoning models like Qwen3-Thinking? Is there published research on this specifically?

B. **Best teacher trace source**: does one teacher (Sonnet vs GPT-5.4 vs GPT-OSS vs others) produce systematically better reasoning traces for math? Are there benchmarks or comparisons?

C. **Trace regeneration strategies**: when no teacher's natural trace matches verified-correct answer, what's the best fallback? Wolfram-derived? LLM-regenerated? Hand-crafted? Hybrid?

D. **Trace+answer alignment auto-detection**: how to detect mismatch automatically? Parse trace conclusion, compare to labeled answer? Other approaches?

E. **Multi-teacher trace ensemble**: any value in showing multiple correct traces per item during training? Or does this confuse memorization?

F. **Memorization quality**: does coherent trace+answer pair training produce qualitatively different memorization vs incoherent? Specifically, does it produce a model that actually DERIVES the answer in trace at inference, vs one that pattern-matches and bypasses?

**Implication for v7 plan timing:**

If we determine via Phase C that trace regeneration is necessary for items where Sonnet got the answer wrong:
- Add ~1-2h to dataset prep phase (run dataApp or alternative to regenerate)
- Could pre-stage dataApp generation in parallel with claude_strategy doing other work
- Trade-off: better training data quality vs more time spent before training

**Implication for the v5 postmortem:**

v5's break-even outcome (not regression, but no gain) may be partially attributable to:
1. 87% T1-easy training (Qwen already gets these right)
2. Trace-answer mismatch on the items where Sonnet was wrong (poisoned training signal)
3. Single-path deployment that exposed both issues to the full 943

These are independent failure modes. v7 needs to address ALL THREE simultaneously:
- Train on Qwen-wrong residual (not T1-easy)
- COHERENT trace+answer pairs (no Frankenstein)
- Dual-path deployment (route only trained items to adapter)

This raises confidence that v7 is fixable. Each of these is concretely addressable.

---

## PART 7 — Compute envelope through deadline (locked 5/31)

**Available compute** (per Rain, Day 9 Hour ~T-15):
- **tnr-1**: BUSY until competition end (kitchen-sink + Pick B firing). OFF TABLE for v7.
- **tnr-0**: AVAILABLE — 2× A100 80GB. Primary v7 platform.
- **Additional spin-up**: +1× A100 currently available (theoretical max +2 more if needed).
- **Effective v7 envelope**: 2 baseline + 1 standby = 3 GPUs max.

**Implications**:
1. v7 training: 30-60 min on single A100 80GB (extrapolating from v3 35.8min on A100 80GB). Fits comfortably.
2. tnr-0's 2 GPUs enable PARALLEL work: GPU 0 trains v7, GPU 1 runs held-out base eval / pre-stages adapter inference.
3. Extra A100 = INSURANCE, not primary. Use for: kitchen-sink rerun if needed, v7 variant in parallel, held-out validation inference.
4. Setup overhead on tnr-2 (if spun up): 15-25min per v3 log. PAT BURNED per memory #28 — rotate before spawn. Identity guardrail (~/.instance-role chmod 444) MUST be set per memory #5.
5. **Conservative-first reinforced**: 2× A100 = enough for one solid v7 attempt + eval + integration. Not enough for 3-4 aggressive variants. First attempt MUST be well-designed.

**Refined v7 timing path** (~6-7h end-to-end):
- T+0 to T+1h: Phase C 4-LLM research (no GPU)
- T+1h to T+1.5h: Phase D planning (no GPU)
- T+1.5h to T+3h: Dataset prep (claude_strategy + claude_vscode, no GPU). PARALLEL: tnr-0 GPU 1 pre-stages held-out base eval.
- T+3h to T+4h: v7 training on tnr-0 GPU 0 (60min budget)
- T+4h to T+5h: Eval (held-out + memo at inference + smoke + format)
- T+5h to T+6h: Integration into Pick B + audit
- T+6h: Decision point — fire Pick B with v7

Leaves 7-8h remaining buffer at end for Pick B iteration, Gradescope code, final lockdown.

---

## PART 9 — Subset-stratified hypothesis testing + routing-dismissal correction (Rain's catch 5/31)

### 9.A) Subset-stratified hypothesis testing (PRIMARY v7 eval direction)

Rain's observation: transductive learning effectiveness may NOT be uniform across the 943. Could be effective on some subsets and useless or harmful on others. The right v7 question isn't "does adapter work" — it's **"for which subsets does adapter work, and where does it fail."**

**Subsets to define and test per-subset performance**:
- **Question format**: MCQ vs free-form
- **Answer cardinality**: single-slot vs multi-slot (2-slot, 3-slot, 5-slot, 10-slot)
- **Trace length**: short (<1000 tokens) vs medium (1000-4000) vs long (4000+)
- **Tier**: T1/T2/T3/T4/T5 (per memory #23)
- **Subject category**: algebra / geometry / calculus / statistics / number theory / combinatorics / ...
- **Difficulty proxies**: low base-SC agreement (≤4/16) vs medium (5-12) vs high (13-16)
- **Answer type**: numeric (integer/decimal/fraction) / algebraic expression / set / interval/range / textual (T/F or Yes/No)
- **Wolfram coverage**: items where Wolfram solved vs items where Wolfram failed

**Eval methodology change**: v7 evaluation must produce a PER-SUBSET breakdown table, not just aggregate. Example output:
```
Subset            Base    Adapter   Delta    Routing?
MCQ single        0.81    0.86     +5pp     ROUTE
Free single       0.62    0.65     +3pp     ROUTE
Multi-slot 2      0.43    0.41     -2pp     SKIP
Multi-slot 3+     0.35    0.30     -5pp     SKIP
T1 (easy)         0.94    0.94      0pp     SKIP (no upside)
T4 (hard)         0.28    0.42     +14pp    ROUTE
```

This output enables SELECTIVE deployment: route items in the subsets where adapter helps; pass-through items where it doesn't.

**Multi-adapter ensemble option** (opened up by per-subset analysis):
- Train narrow specialists per subset (e.g., MCQ adapter, single-slot free adapter, T4 adapter)
- Each adapter trained on its subset's residual (Qwen-wrong items in that subset)
- At inference, route per item characteristics to the right specialist
- More complex but potentially much higher upside than one general adapter

**Critical Phase C research questions added**:
- G. Has anyone published per-subset effectiveness analyses for LoRA SFT on math reasoning? Which subsets benefit most/least?
- H. Are there structural reasons (model architecture, training paradigm) that would predict which subsets benefit from SFT memorization?
- I. AIMO/Kaggle math winners: did any use multi-adapter ensembles or subset-routing?
- J. Are MCQ and free-form fundamentally different learning problems for SFT, or roughly equivalent?

### 9.B) Routing-dismissal correction

Earlier in this notes file I wrote: "v4 ALREADY attempted selective sampling diversity (trained items low-T tight, untrained items high-T diverse) — still regressed. So pure routing doesn't fix it."

**This was overstatement.** Rain pushed back: just because v4's specific routing implementation regressed doesn't mean the dual-path/selective-routing concept is dead.

**Corrected framing**:
- v4's specific implementation = MERGED model + temperature-differentiated sampling. That ONE configuration regressed -4.9pp.
- This is one data point on one routing strategy. It does NOT extend to all routing approaches.
- v5's deployment (LoRA adapter not merged + items-in-training-set routed to adapter) broke even — a different routing on a different architecture was at least neutral.
- Selective routing remains viable. The lesson is: v4's combination of merge + temperature was a bad combination, not that routing concept is wrong.

**Routing strategies still on the table for v7** (any of these could be the right answer):
1. **LoRA-adapter routing** (v5-like): adapter applied only to items in training set
2. **Subset-routing** (new): adapter applied to subsets where per-subset eval showed gain
3. **Confidence-gated routing**: adapter answer used only when adapter is confident (high top-logit)
4. **Multi-adapter ensemble**: multiple specialists, route per item characteristic
5. **Logit interpolation** (WiSE-FT-style): blend base + adapter logits at decode time
6. **GenSelect**: have base + adapter both generate, third Qwen call judges which is better
7. **Item-similarity routing**: train on items A,B,C; at inference, also route items similar to A,B,C (by embedding distance or other measure)

Phase C should examine evidence for/against each of these.

### 9.C) Implication for v7 plan structure

v7 plan now has TWO orthogonal axes (vs single axis I had before):

**Axis 1: training data composition**
- Mode 1.1: Qwen-wrong residual only (v5-thesis evolved)
- Mode 1.2: Stratified — proportional sample across subsets (in case adapter learns subset-specific patterns)
- Mode 1.3: Single-subset focus — train on just MCQ residual, or just T4-hard, etc.

**Axis 2: deployment / routing**
- Mode 2.1: Items-in-training-set routing (v5-like, dual-path)
- Mode 2.2: Subset-routing (per per-subset eval results)
- Mode 2.3: Confidence-gated
- Mode 2.4: Multi-adapter ensemble (if Axis 1 = 1.3)
- Mode 2.5: Logit interpolation
- Mode 2.6: GenSelect

Phase D must pick combinations conservatively. First v7 attempt should be ONE Axis-1 mode + ONE Axis-2 mode, well-validated. Iteration can vary either axis.

**Recommended first v7 attempt** (subject to Phase C/D refinement):
- Axis 1: Mode 1.1 (Qwen-wrong residual) + coherent trace+answer pairs (Part 8 fix)
- Axis 2: Mode 2.1 (items-in-training routing) + per-subset evaluation (so we LEARN which subsets to route in v7.2)
- This is conservative: same architecture as v5 with the two known bugs (training composition + trace coherence) fixed, plus stratified eval to guide future iterations

If first v7 attempt fails or breaks even: the per-subset eval results tell us WHICH subsets to focus on for v7.2 (e.g., maybe MCQ subset is +5pp but multi-slot is -3pp — v7.2 trains on MCQ residual only).

---

## PART 10 — Locked decisions + PEFT variant investigation (Rain's lock 5/31)

### 10.A) LOCKED decisions (skip investigation, save time)

1. **PARADIGM**: SFT. Not RL, not in-context learning, not other paradigms.
2. **DEPLOYMENT**: Standalone LoRA adapter (NOT merged). Evidence already strong:
   - v1 merged → catastrophic rambling pathology
   - v4 merged-adaptive → -4.9pp regression
   - v5 adapter (LoRARequest) → break-even
   - Merge-mode adds risk without offsetting benefit; adapter mode is reversible, supports dual-path, supports vLLM LoRARequest natively
3. **ARCHITECTURE FAMILY**: PEFT (parameter-efficient fine-tuning). NOT full fine-tuning, not soft prompts.

These locks COLLAPSE several Phase C research questions that are no longer needed:
- ~~Single-path vs dual-path deployment debate~~ — dual-path locked
- ~~Adapter vs merge deployment~~ — adapter locked
- ~~SFT vs RL vs in-context~~ — SFT locked
- ~~GenSelect as primary~~ — secondary at most (still mention as deployment-time option)

Phase C should focus only on questions that affect the locked path.

### 10.B) PEFT variant investigation — MUST DO in Phase C

Three variants to compare:

**LoRA** (Hu et al. 2021) — what v3/v4/v5 used:
- Decompose weight update as ΔW = BA (low-rank product, B ∈ R^{d×r}, A ∈ R^{r×k})
- Parameters: r (rank), α (scaling), target_modules, dropout
- v3-v5 used: r=64, α=128, target modules = q/k/v/o + gate/up/down

**QLoRA** (Dettmers et al. 2023) — also what v3-v5 used:
- LoRA + 4-bit base model quantization (NF4 dtype + double quantization)
- Reduces base model memory ~4× without performance loss on most tasks
- Allows training on smaller GPUs (consumer hardware feasibility)
- For our use case: 4B model on 80GB A100 — quantization not strictly needed, but doesn't hurt

**DoRA** (Liu et al. 2024) — NOT YET TRIED — the variant Rain wants us to investigate:
- Decompose pretrained weight W into magnitude vector m + direction matrix V (W = m * V/||V||)
- Apply LoRA only to the direction component V
- Magnitude m is learned separately as full vector (not low-rank)
- Reportedly outperforms LoRA at same rank on multiple benchmarks (per original paper)
- More expressive than LoRA at low ranks; closes the gap to full fine-tuning

**Research questions for Phase C** (PRIMARY now):

K. **Does DoRA outperform LoRA for math reasoning specifically?** Most DoRA benchmarks are NLU (GLUE, etc.). Need evidence on math.

L. **DoRA vs LoRA at our specific config (r=64, α=128, Qwen3-4B-class)** — what's the published delta?

M. **DoRA compatibility with our infrastructure**:
- PEFT library: supports DoRA since v0.10 (need to verify our pinned version)
- Unsloth: DoRA support status?
- vLLM LoRARequest: does it support DoRA adapters at inference, or only LoRA?
- If vLLM doesn't support DoRA at inference: dealbreaker (we lose the adapter deployment mechanism)

N. **DoRA training cost vs LoRA**: how much extra wall time? Memory footprint?

O. **DoRA inference cost vs LoRA**: latency overhead?

P. **DoRA for memorization-style tasks** (our specific use case = targeted memorization on Qwen-wrong items): does DoRA's higher expressivity help or hurt memorization-focused training?

Q. **QLoRA vs LoRA at our scale**: do we need 4-bit quantization for 4B model on 80GB A100? Or can we use full bf16 LoRA for cleaner training? Trade-off analysis.

**Why investigation is justified despite time pressure**:
- v3/v4/v5 ALL used QLoRA-with-LoRA. Same PEFT variant across 4 attempts. We've never tested DoRA.
- If DoRA-vs-LoRA delta is meaningful (e.g., +2-3pp on math), it's a free win on v7
- Verification time is small (~15min of research read) vs potential gain
- BUT must verify infrastructure compatibility first (M) — if vLLM doesn't support DoRA at inference, drop immediately

### 10.C) Implications for v7 plan

- Phase C research dive now includes 7 questions (K-Q) on PEFT variants — concrete + actionable
- Phase D v7 design needs explicit PEFT variant choice as an explicit decision (currently default = LoRA per v5 lineage; should we switch to DoRA?)
- v7 first attempt could explore DoRA IF infrastructure compatible:
  - Train one adapter with LoRA (familiar, low-risk)
  - Train one adapter with DoRA (if compatible, novel, potential gain)
  - Compare on per-subset eval
  - Use winner for Pick B
- This adds ~30-60min for parallel DoRA training on tnr-0 GPU 1 while LoRA trains on GPU 0 — fits in compute envelope

**Required pre-flight before any v7 training launches**:
- Verify PEFT version supports DoRA
- Verify vLLM LoRARequest supports DoRA at inference (or find alternative inference path for DoRA adapter)
- If verification fails: stay with LoRA, drop DoRA from v7

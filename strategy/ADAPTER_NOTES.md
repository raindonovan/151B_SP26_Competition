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

## END OF PHASE A NOTES

Synthesize with `ADAPTER_NOTES_CURSOR.md` in Phase D after both committed.

# Papers and Tooling Findings

Persistent log of academic papers and tooling-class findings that inform methodology decisions on this project. Each entry captures not just the source but our reading of it and how it shaped what we did.

## When to add an entry

- Cited a paper in a review packet, post-mortem, or methodology argument? Add it.
- Used a finding to make a compute-relevant decision? Add it.
- Discovered a tooling bug or silent-failure pattern that affects how we configure trainers/inference? Add it (even if it's not a single paper).

## Entry format

Each entry follows this structure:

### YYYY-MM-DD: Title (or short identifier)

- **Citation:** authors, venue, year
- **Link:** arXiv URL (preferred) or other canonical source
- **Encountered:** when and in what context
- **Core claim:** what does it argue, in 1-2 sentences
- **Relevance to us:** specifically how it bears on our work
- **What we took from it:** concrete updates to thinking or decisions
- **Caveats:** where its findings might not transfer to our setup
- **Used in:** which docs/decisions cite it

---

### 2026-05-08: Huerta-Enochian & Lee — Does Prompt Loss Matter?

- **Citation:** Huerta-Enochian, M. & Ko, S.Y. "Instruction Fine-Tuning: Does Prompt Loss Matter?" EMNLP 2024 (arXiv v2, Feb 2024; v4, Oct 2024).
- **Link:** https://arxiv.org/abs/2401.13586
- **Encountered:** External review packet for v2 SFT loss-target decision (2026-05-08). Cited by reviewers as empirical grounding for the assistant-only-vs-full-sequence question.
- **Core claim:** Controlled study across 60 training runs (10 PLW values × 2 PTLMs × 3 datasets) on LLaMA-1/2 7B. For long-completion data (R_g ≥ 1, where R_g = completion-length / prompt-length), prompt loss weight has no statistically significant effect on downstream performance (α=0.05, 13 benchmarks). For short-completion data (R_g < 1), they found a negative quadratic relationship with optimal PLW around 0.01-0.1.
- **Relevance to us:** v2 NuminaMath has assistant content ~658 median tokens against system + user ~200-400 tokens, so R_g ≈ 1.5-3.0. Squarely in the "long-completion" regime where their finding is null. Direct empirical evidence that loss-target choice (full-sequence vs assistant-only) should not materially affect v2 NuminaMath performance.
- **What we took from it:** Updated v2 SFT loss-target decision toward full-sequence (option F0/F3) on 2026-05-08. The "wasted gradient on prompt tokens" argument for assistant-only loss is theoretically reasonable but empirically doesn't show up in long-completion regimes per their controlled experiment. Combined with v1↔v2 parity considerations and infrastructure-complexity costs of bypassing Unsloth's prep path for genuine assistant-only loss, full-sequence is the simpler and equally-effective path.
- **Caveats:** Their data is Alpaca-style instruction following on LLaMA-1/2 7B, not thinking-model SFT on Qwen3-4B-Thinking-2507. The underlying mechanism (loss budget allocation across prompt vs completion tokens) is the same, but base architecture, data domain, and reasoning-trace structure all differ. Not a slam dunk; treat as strong but not conclusive prior.
- **Used in:** DESIGN.md §7 > Loss target paragraph (v2 SFT loss-target rationale).

---

### 2026-05-08: Li et al. — Sky-T1 / "Structure, not content"

- **Citation:** Li, D., Cao, S., Griggs, T., Liu, S., et al. "LLMs Can Easily Learn to Reason from Demonstrations: Structure, not content, is what matters!" arXiv preprint, Feb 2025 (NovaSky / UC Berkeley + Anyscale).
- **Link:** https://arxiv.org/abs/2502.07374
- **Encountered:** Web research for v2 SFT loss-target decision (2026-05-08). Surfaced as evidence about what thinking-model SFT actually learns from training traces.
- **Core claim:** Fine-tuning Qwen2.5-32B-Instruct on 17k DeepSeek-R1 reasoning traces takes AIME24 from 16.7% → 56.7% (competitive with o1-preview). Controlled perturbations show models are highly sensitive to *structural* perturbations of reasoning traces (shuffling, deleting, or inserting reasoning steps drops accuracy 10-15%) but remarkably *insensitive* to content perturbations (training on samples with wrong final answers: only 3.2% drop; 70% of digits randomly corrupted: only 4.3% drop; all reasoning keywords removed: only 3.3% drop).
- **Relevance to us:** Directly bears on the "what is loss target actually optimizing for" question. The intuition motivating assistant-only loss is "concentrate gradient signal on the tokens we want the model to produce." But Sky-T1 evidence suggests the model is learning structural patterns of long-CoT (reflection, backtracking, self-validation, sequencing of logical steps) rather than per-token gradient density. This pushes back against the "full-sequence wastes gradient capacity" argument: the model isn't learning from gradient density, it's learning from trace structure.
- **What we took from it:** (1) Reinforced confidence in the v2 SFT loss-target decision toward full-sequence — loss-target is a per-token gradient-density choice, and the evidence says structure-level patterns are what matter. (2) Reframes v1 NuminaMath post-mortem: Pattern B (empty think block, content post-think) is a *structural* corruption of the training distribution, which Sky-T1 evidence says is exactly the kind of thing that wrecks reasoning capability. Pattern A2 fix is load-bearing because it restores correct trace structure, not because of any loss-target consideration.
- **Caveats:** Their student model is Qwen2.5-32B-Instruct (not Qwen3-4B-Thinking) and they trained with 17k samples vs our 8k. They use a system prompt that explicitly instructs `<|begin_of_thought|>` / `<|end_of_thought|>` format (different from Qwen3's `<think>...</think>`). Their findings on structure-vs-content sensitivity generalize at the mechanism level but exact numbers are not directly transferable.
- **Used in:** experiments.md > External Review Insights > 2026-05-08 entry; v1 NuminaMath post-mortem reframe evidence.

---

### 2026-05-08: TRL silent-disable bug class (Liger / Unsloth / packing)

- **Citation:** Tooling-class finding, not a single paper. Documented across multiple HuggingFace TRL GitHub issues (linked below) and observed empirically in our own v1 SFT runs.
- **Link:** Primary sources:
  - TRL Issue #3781: assistant_only_loss silently discarded when use_liger_kernel=True (https://github.com/huggingface/trl/issues/3781)
  - TRL Issue #3927: assistant_only_loss fails silently when sequence > max_length (https://github.com/huggingface/trl/issues/3927)
  - TRL Issue #3484: completion_only_loss incompatible with use_liger_kernel — completion_mask dropped (https://github.com/huggingface/trl/issues/3484)
  - HuggingFace OpenR1-Distill-7B (https://huggingface.co/HuggingFaceTB/SmolLM3-3B and related repos): trains under accidental full-sequence loss (Liger Kernel silent-disable) and successfully replicates DeepSeek-R1-distill-Qwen-7B numbers.
- **Encountered:** Diagnostic 4.3 investigation (2026-05-07 / 2026-05-08). The "0 graded tokens" finding turned out to be a manifestation of the same bug-class: Unsloth's compiled cache ships its own _prepare_dataset that bypasses TRL's apply_chat_template(return_assistant_tokens_mask=True) path entirely, silently producing input_ids-only datasets that the data collator falls back to full-sequence loss on. Confirmed v1 trained under this regime despite assistant_only_loss=True being set.
- **Core claim:** Multiple major fine-tuning frameworks (TRL+Liger, TRL+packing, Unsloth) have shipped silent-disable bugs around assistant-only-loss for over a year. None of them produce visible warnings or errors. Successful published recipes (HuggingFace OpenR1-Distill-7B, possibly many others) train under accidental full-sequence loss without anyone noticing in output quality.
- **Relevance to us:** Two implications. First, the empirical fact that production thinking-model SFT recipes are silently full-sequence and still produce good results is independent evidence supporting our v2 SFT loss-target decision. Second, any future "set X=True and trust the config" decision should be diagnostically validated before committing compute — this bug-class generalizes (the same pattern could affect packing, padding-free, completion masks, etc.).
- **What we took from it:** (1) Strong evidence-of-life that full-sequence loss in thinking-model SFT works. (2) Process discipline: configs are claims about what *should* happen, not what *does* happen. Diagnostic 4.3-style label audits (decode actual graded positions) are mandatory before compute commits, regardless of what config says. Codified in CLAUDE.md > External Review Before Compute Commits and the pre-flight label audit step in DESIGN.md.
- **Caveats:** This is a tooling-stability snapshot as of 2026-05-08. TRL is actively patching these bugs. By the time anyone re-reads this entry, the specific bugs may be fixed — but the *pattern* of silent-disable on speed-optimization paths is durable.
- **Used in:** experiments.md > External Review Insights > 2026-05-08 Unsloth entry; CLAUDE.md > External Review Before Compute Commits (motivating example).

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

### 2026-06-04: Diniz et al. — Reasoning-optimised LLMs reach near-expert accuracy on board-style exams [PEER-REVIEWED, difficulty anchor]

- **Citation:** Diniz, P., Yokoe, T., Öttl, F.C., Pereira, H., Henriques, R., & Samuelsson, K. (2025). Knee Surgery, Sports Traumatology, Arthroscopy, 34(2), 752–762.
- **Link:** https://doi.org/10.1002/ksa.70222
- **Encountered:** Scholar Gateway peer-reviewed pass (2026-06-04).
- **Core claim:** Across 702 board-style MCQs, reasoning-optimised models scored ≥14pp above GPT-4 (o3 93.6%); accuracy declined with difficulty but the reasoning advantage PERSISTED in every difficulty stratum; reasoning models also better-calibrated (Opus 4 ECE 0.023), with large latency/cost spreads (0.9–15.9s; $0–$29.9/1000q).
- **Relevance to us:** Peer-reviewed support for the reframe — explicit reasoning's edge is difficulty-robust, it does NOT vanish on hard items. Counts against the "NoThinking solves what reasoning can't" hypothesis. The latency/cost spread also motivates the efficiency framing.
- **Caveats:** Medical MCQ across DIFFERENT models (o3/Claude/Gemini), not a same-model thinking/no-thinking toggle on free-form math. Contextual support, not a direct precedent.
- **Used in:** research_paper_no_thinking/FINDINGS.md, SYNTHESIS.md (reframe).

### 2026-06-04: Sprague et al. — To CoT or not to CoT? [when-does-thinking-help anchor]

- **Citation:** Sprague, Z., Yin, F., Rodriguez, J.D., Jiang, D., Wadhwa, M., Singhal, P., Zhao, X., Durrett, G., et al. "To CoT or not to CoT? Chain-of-thought helps mainly on math and symbolic reasoning." arXiv 2409.12183 (verify), 2024. ICLR 2025.
- **Link:** https://consensus.app/papers/details/88d9a6d5af175c35984bae4fc831c2a4/
- **Encountered:** Consensus arXiv sweep (2026-06-04). 300 citations.
- **Core claim:** Meta-analysis (100+ papers, 20 datasets, 14 models): CoT gives strong gains mainly on MATH/symbolic tasks, small gains elsewhere; on MMLU, direct-answer ≈ CoT unless an equals sign is present. CoT can be applied selectively to save cost.
- **Relevance to us:** The authoritative "when does thinking help" result. Our task IS math, so it predicts thinking should help → NoThinking's value is efficiency, not capability, on our domain. Justifies difficulty/type-gated routing.
- **Caveats:** Prompt-based CoT on general LLMs, not native thinking-model mode-toggling.
- **Used in:** research_paper_no_thinking/FINDINGS.md (Related work), SYNTHESIS.md.

### 2026-06-04: Zhao et al. — SABER: Switchable and Balanced Training for Efficient LLM Reasoning [closest graded-pipeline prior]

- **Citation:** Zhao, K., et al. "SABER: Switchable and Balanced Training for Efficient LLM Reasoning." arXiv preprint, 2025.
- **Link:** https://consensus.app/papers/details/865dbae7e7d35de9a011f72fec1e4df2/
- **Encountered:** Consensus arXiv sweep (2026-06-04).
- **Core claim:** RL framework for user-controllable, token-budgeted reasoning. Profiles each example's base thinking-token usage, assigns a budget tier, trains with length-aware rewards + no-think examples. Four inference modes — NoThink / FastThink / CoreThink / DeepThink. SABER-FastThink cuts reasoning length 65.4% with +3.6% accuracy on MATH.
- **Relevance to us:** The closest published version of our graded THINKING→NOTHINKING pipeline — a trained continuum of thinking depths, difficulty-routed. Our pipeline must be positioned against it.
- **What we took from it:** Don't claim a graded thinking-budget pipeline as novel. Our differentiator is the TRANSDUCTIVE answer-memorization terminal gate (force the known answer) vs SABER's RL length-control, plus the Qwen3-2507 demonstration.
- **Caveats:** RL training approach; modes are length-tiers, not an answer-injection gate.
- **Used in:** research_paper_no_thinking/SYNTHESIS.md (pipeline positioning).

### 2026-06-04: Chen et al. — Distilling Reasoning Ability with Adaptive Thinking [peer-reviewed answer-first routing prior]

- **Citation:** Chen, X., et al. "Distilling Reasoning Ability From Large Language Models With Adaptive Thinking." IEEE Transactions on Neural Networks and Learning Systems, 2024.
- **Link:** https://consensus.app/papers/details/2dc3eed2de835d939fa6d686e6fe0aea/
- **Encountered:** Consensus arXiv sweep (2026-06-04). Peer-reviewed (IEEE TNNLS).
- **Core claim:** Proposes POST-thinking (answer before rationale) vs the usual pre-thinking. Answer-first escapes rationale-sensitivity; the rationale acts as an "error amplifier" focusing learning on hard samples; better inference efficiency. A plug-and-play adaptive-thinking module routes answer-first vs think-first by question complexity.
- **Relevance to us:** Peer-reviewed, 2024 — predates AdaptThink — and is the closest prior to our adaptive answer-first gate AND to the id-282 "reasoning introduces errors" intuition (their "rationale as error amplifier"). Strong prior art for the routing idea.
- **What we took from it:** The "rationale as error amplifier" framing directly names our overthinking-error mechanism. Position our transductive gate as a competition-grounded, answer-injection instance of answer-first routing.
- **Caveats:** CoT-distillation into small models; adaptive module is soft-prompt-tuned, not memorization.
- **Used in:** research_paper_no_thinking/SYNTHESIS.md, FINDINGS.md.

### 2026-06-04: Li et al. — When Thinking Fails: Pitfalls of Reasoning for Instruction-Following [reasoning-induced-error anchor = id-282]

- **Citation:** Li, X., et al. "When Thinking Fails: The Pitfalls of Reasoning for Instruction-Following in LLMs." arXiv preprint, 2025.
- **Link:** https://consensus.app/papers/details/89bfec0361a756bcb07a500218400e37/
- **Encountered:** Consensus arXiv sweep (2026-06-04). 42 citations.
- **Core claim:** Explicit CoT can DEGRADE instruction-following (15 models, IFEval/ComplexBench). Reasoning helps with formatting/lexical precision but hurts by neglecting constraints or "introducing unnecessary content"; CoT diverts attention from instruction-relevant tokens. Selective / classifier-selective reasoning recovers the loss.
- **Relevance to us:** The generalized, named version of our id-282 (reasoning invents a spurious extra root) and our format/multi-slot failures. Direct evidence for "thinking hurts via overthinking, not capability," and its mitigation (selective reasoning) is our gating idea.
- **What we took from it:** Frame NoThinking's wins as overthinking-error avoidance (their mechanism), and our gating as selective reasoning. Strengthens the honest reframe.
- **Caveats:** Instruction-following constraints, not free-form math grading; mechanism transfers, benchmark differs.
- **Used in:** research_paper_no_thinking/FINDINGS.md, SYNTHESIS.md (reframe).

### 2026-06-04: He et al. — Reasoning Beyond CoT: A Latent Computational Mode [reliability/override caveat]

- **Citation:** He, Z., et al. "Reasoning Beyond Chain-of-Thought: A Latent Computational Mode in Large Language Models." arXiv preprint, 2026.
- **Link:** https://consensus.app/papers/details/42eaba95dc4f53b9a653d738aab5ce05/
- **Encountered:** Consensus arXiv sweep (2026-06-04).
- **Core claim:** Via sparse autoencoders, identifies latent reasoning features; steering one can match CoT accuracy without explicit CoT. Critically: the reasoning-oriented internal state is triggered EARLY and can OVERRIDE prompt-level instructions that discourage explicit reasoning.
- **Relevance to us:** Mechanistic complement to Zhu et al. (2505.15276) — explains WHY our `</think>` prefill may fail to suppress reasoning on an RL-trained model (the latent reasoning state overrides the instruction). Backs the Exp-1 NT/ET/IT reliability instrument.
- **Caveats:** SAE-steering analysis across model families; not a direct prefill-on-Qwen3 study.
- **Used in:** research_paper_no_thinking/EXPERIMENTS.md (Exp 1 reliability), FINDINGS.md.

### 2026-06-04: Efficient-reasoning landscape [grouped — token-compression / no-think family]

The broader efficient-reasoning field our work sits within (cite as a cluster; we occupy the up-front-NoThinking + transductive-gate corner):
- **NoWait** (C. Wang et al. 2025): suppress "Wait"/"Hmm" self-reflection tokens at inference → 27–51% shorter CoT, utility preserved. https://consensus.app/papers/details/30da75346fe8546bb8fabec89a93abc2/
- **Chain of Draft** (S. Xu et al. 2025): concise drafts, matches CoT at ~7.6% of tokens. https://consensus.app/papers/details/3b0d32cf2dfd58a7890cc44a99a2bdd3/
- **TokenSkip** (Xia et al. 2025): controllable CoT compression; Qwen2.5-14B −40% tokens, <0.4% drop. https://consensus.app/papers/details/019024f618ec516ea0a3bee995e85d1f/
- **Sketch-of-Thought** (Aytes et al. 2025): cognitive sketching, up to −84% tokens, sometimes +accuracy on math. https://consensus.app/papers/details/328853e8f4d85a6894e7063743caeeef/
- **Thought Manipulation** (Y. Liu et al. 2025): inject small-model CoT between think tokens; QwQ-32B −30% tokens; difficulty-aware fallbacks. https://consensus.app/papers/details/1e793a0868cf5f65806b3fd4bc93dbcd/
- **Self-Training Elicits Concise Reasoning** (Munkhbat et al. 2025): self-train on own concise correct traces, −30% tokens (= the comp's iterative-self-training "Clanker" lever). https://consensus.app/papers/details/4a48f9d2ceeb559eac05d7de15f7253f/
- **Confidence-Aware Self-Consistency** (Xiong et al. 2026): single-trajectory signal routes single vs multi-path SC, −80% tokens at parity (relevant to our format-gated voting + Exp-1 SC ladder). https://consensus.app/papers/details/25862f93f476520887aee9c400bb3422/
- Also: SoftCoT, TwT (thinking-without-tokens distillation), CoT-decoding (Wang 2024).
- **Relevance:** Establishes that "make reasoning cheaper" is a dense field; our angle is bypass-not-compress (up-front NoThinking) + transductive answer-injection + the Qwen3-2507 demonstration.
- **Used in:** research_paper_no_thinking/FINDINGS.md (Related work landscape).

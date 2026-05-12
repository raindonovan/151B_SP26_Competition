# Prompt Engineering Research Doc — CSE 151B SP26

Implementation notes for Path A (inference-time leverage). Living doc — each section covers what the evidence shows, the implementation plan, what to measure, and known risks. Update as experiments come in.

## Status

- **Active path:** Path A (inference-time leverage). Path B (SFT) deferred until A is exhausted.
- **Baseline to beat:** base Qwen3-4B-Thinking-2507 + SC-8 = **0.614** on Kaggle (Run 09).
- **Target failure mode:** multi-answer free-form, ~41% of private test. Base model: 13/20 on local 50-slice multi-answer items. Adapter (v2 OpenR1): 2/20 (catastrophic collapse).
- **Three independent levers** being layered (each separately justified by published work, all compose):
  1. Multi-answer counting prompt + few-shot multi-answer exemplars
  2. Shape filter (discard SC samples with wrong number of comma-separated entries in `\boxed{}`)
  3. Temperature diversification across SC samples

---

## 1. Temperature Diversification

### Evidence base

**Source:** Sun, Mirhoseini, Tambe — *"On the Role of Temperature Sampling in Test-Time Scaling"* — arxiv 2510.02611, Stanford, Oct 2025. Read in full.

Tested **directly on the Qwen3 family** (0.6B, 1.7B, **4B**, 8B) across AIME 2024/2025, MATH500, LiveCodeBench v6, Hi-ToM. Evaluated with vLLM at 1024 samples per temperature, 12 temperatures from 0.0 to 1.2 in 0.1 increments.

**Core finding (robust):** Different questions have different optimal sampling temperatures. Single-temperature scaling explores only a subset of the model's reasoning boundary. Mechanism is corroborated by entropy analysis (§3) and case studies (§3.2). A given problem may be solvable at T=0.7 but not T=0.9 because the high-T traces wander into approximate-guess reasoning instead of the exact reduction path.

**Headline number (caveat-heavy):** averaged across 4 model sizes and 5 benchmarks, "+T" beats "Base" by **+7.3 points**, where:
- *Base* = Pass@1024 at T=0.6 (1024 samples, single temperature)
- *+T* = Pass@All across 12 temperatures × 1024 samples each = **13,312 total samples**

For Qwen3-4B specifically (Table 1):

| Benchmark | Base | +T | Δ |
|---|---|---|---|
| AIME 2025 | 60.0 | 73.3 | +13.3 |
| AIME 2024 | 66.7 | 76.7 | +10.0 |
| MATH500 | 95.5 | 98.5 | +3.0 |
| LiveCodeBench v6 | 36.0 | 40.0 | +4.0 |
| Hi-ToM | 83.0 | 92.0 | +9.0 |

**Why the headline overstates what we get at SC-8:**

1. **Wrong metric.** Pass@K means "an oracle verifier picks any correct sample." Majority vote (what we do) cannot match Pass@K. The paper itself says: *"Avg@1,024 remains nearly identical across temperatures."* Avg@N is closer to what majority vote achieves than Pass@K is.
2. **Wrong regime.** From Figure 2c: *"When K is small, different temperatures yield similar Pass@K… As K grows, temperature-specific advantages emerge."* SC-8 is the small-K regime.
3. **Unequal compute.** The +7.3pp compares 13,312 vs 1024 samples. The equal-compute version (Figure 3c, K=13,312 at single-T vs 13,312 split across temperatures) gives ~6.67pp on AIME 2025.

**Realistic expectation for our SC-8/SC-16 majority vote: +0 to +3pp on the multi-answer slice.** Worth pulling because the lever is essentially free (one config change), but **not** the killer move. The counting prompt and shape filter are likely bigger contributors.

**Resolves a tension in the practitioner data:** Qwen's official model card recommends **T=0.6** for thinking mode (single-trace optimum). The AIMO-2 9th place team (Fast-Math-R1-14B, Yoshihara/Inoue/Yamaguchi, GitHub repo verified) ran SC at **T=1.0, top_p=0.90, min_p=0.05** — substantially hotter. These don't contradict; they answer different questions. T=0.6 maximizes single-trace accuracy. T≥1.0 maximizes ensemble diversity for SC. Our cross-temperature ladder (T ∈ {0.5, 0.7, 0.9, 1.1}) covers both regimes and is consistent with the diversity-tier practitioner consensus.

### Implementation plan

**Current code:** `run_vllm_sc.py` calls `llm.generate(prompts, SamplingParams(n=8, temperature=0.6, ...))`.

**Change:** vary temperature across the N samples per prompt. Recommended subset per paper §4.1 (excludes very low T = 0.1-0.3 which doesn't add coverage):

- **SC-8 variant:** 2 samples each at T ∈ {0.5, 0.7, 0.9, 1.1}
- **SC-16 variant:** 2 samples each at T ∈ {0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2}
- **SC-32 variant (if pursued):** 4 samples each at T ∈ {0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2}

vLLM accepts per-call `SamplingParams`. Cleanest implementation is to loop over temperatures and concatenate outputs per prompt before voting:

```python
def generate_with_temp_diversification(llm, prompts, temps, samples_per_temp, **kwargs):
    """Returns list of lists: per-prompt list of all generated outputs across temps."""
    all_outputs = [[] for _ in prompts]
    for t in temps:
        params = SamplingParams(n=samples_per_temp, temperature=t, **kwargs)
        outputs = llm.generate(prompts, params)
        for i, out in enumerate(outputs):
            all_outputs[i].extend(out.outputs)
    return all_outputs
```

**vLLM specifics (Kwon et al. arxiv 2309.06180):** within a single `generate()` call with `n>1`, the prefill KV cache is shared across all `n` samples by PagedAttention — this is core to why SC is cheap on vLLM. Across separate `generate()` calls with the same prompt (as in the loop above), prefix sharing requires `enable_prefix_caching=True` in the vLLM engine config. Set this. With prefix caching on, the per-temperature loop pays prefill once per question and reuses it for all subsequent temperatures. Without it, we pay prefill N times per question for N temperatures — still tractable since prompts are ~hundreds of tokens vs ~9K-token generations, but cleaner with caching on.

### Voting strategy: flat vs hierarchical

Paper §4.2 proposes hierarchical voting: intra-temperature majority first (σintra=0.8), then cross-temperature majority (σcross=1.0). This is designed for *early exit on easy questions*, not for boosting accuracy on hard ones.

For SC-8 with only 2 samples per T, intra-T voting is meaningless (no majority possible in 2 samples). For SC-16 still too thin. Hierarchical only becomes meaningful at 4+ samples per T.

**Plan:** flat majority vote across all samples. Reserve hierarchical for SC-32+ experiments if we get there.

### What to measure (on fixed_50_v1)

1. **Per-temperature contribution.** How often does each T uniquely solve a problem that other T's miss? Sanity check that the diversification is doing anything.
2. **Overall majority-vote accuracy** after shape filter applied.
3. **Accuracy by question type:** MCQ / single-free / multi-free. Multi-free is what we care about most.
4. **Shape filter rejection rate per T.** Expect higher rejection at T ≥ 1.0 due to format degradation.

### Risks

- **Repetition penalty interaction.** Run 09 baseline used some repetition_penalty setting; the 1.1 value was a band-aid for the broken adapter. For base model, recommend rep_penalty = 1.0 across all temperatures. Test 1.0 vs 1.05 in a small ablation if results are noisy.
- **Language drift at high T.** Qwen3 documentation flags that higher penalties can cause language mixing; high T may also. Shape filter catches most degenerate outputs; track rejection rate.
- **Logprob-weighted voting (DeepConf-style).** Defer. Paper §3.1 shows entropy/confidence signals are unreliable on hard problems (the ones we'd want them to help with). Implement only if base diversification result is positive and we want to squeeze out a marginal gain.

### Open questions

- Does hierarchical voting help at SC-32 with 4 samples per T? Untested at our compute scale.
- Does the gain interact with the counting prompt (do diverse temperatures help when the model already knows N answers are required)? Will fall out of joint experiments.
- Optimal subset of temperatures may be model- and dataset-specific; paper's recommendation is generic. May want to re-tune on fixed_50_v1.

---

## 2. Multi-Answer Counting Prompt

### Evidence base

**Source:** Fu, Gu, Li, Qu, Cheng — *"Scaling Reasoning, Losing Control: Evaluating Instruction Following in Large Reasoning Models"* — arxiv 2505.14810, May 2025. Read in full.

**What MathIF actually is** (important reframe — not what I expected): a benchmark that tests whether reasoning models can follow **secondary natural-language constraints** (length, lexical, format, affix) layered on top of math problems. 15 constraint types across 4 categories. Examples:
- *"Your answer must contain exactly 3 bullet points."*
- *"Finish your response with this exact phrase: Any other questions?"*
- *"In your entire response, refrain from the use of any commas."*
- *"First repeat the request word for word without change, then give your answer."*

420 samples: 140 single, 140 dual, 140 triple compositional constraints, drawn from GSM8K, MATH-500, Minerva, Olympiad, AIME. Evaluated 23 LRMs at T=1.0, top_p=0.95, max 16K tokens, via vLLM.

**Caveat on transfer:** MathIF tests *secondary* instructions ("solve the math AND end with phrase X"), not the *primary* answer-format instruction we're imposing ("output N comma-separated values in `\boxed{}`"). The "format" category does include things very close to what we want — *"Your answer must contain exactly N bullet points"* is structurally similar to *"your boxed answer must contain exactly N entries"* — so findings transfer, but not 1:1.

### Findings that change how we should build the counting prompt

**1. Qwen3-4B is the best ≤4B model for instruction-following.** HAcc 44.05% (fraction of examples satisfying *all* constraints), SAcc 61.43% (average fraction satisfied). Beats DeepSeek-R1-Distill-Llama-70B (HAcc 41.43%) which is 15× larger. We picked the right base model for this task — among small reasoning models, Qwen3-4B-Thinking-2507 has the strongest instruction-following prior.

**2. Long CoT hurts instruction-following — monotonically.** Figure 6 in the paper shows HAcc and SAcc decline with CoT length across all three tested models (Qwen3-0.6B, Qwen3-32B, DeepSeek-R1-Distill-Llama-8B). Figure 7: artificially extending CoT via "Wait" budget-forcing drops SAcc from ~60% at N=2 forces to ~35% at N=8 forces.

**Mechanism:** longer CoT widens the contextual distance between the user's format instruction (at the top of the prompt) and the model's final answer generation. The model loses track of the constraint.

This directly affects us: Qwen3-Thinking-2507 produces very long thinking traces. Run 09 SC-8 averaged ~9300 tokens per sample. The longest traces are the ones most likely to drop the format.

**3. The "repeat" intervention is the strongest empirical fix (Table 6).** They append "Wait" to extend CoT, *then reintroduce the original constraint immediately afterward*. The constraint appears **twice** — once at the start, once at the end of the CoT, shortening its distance from the final answer.

Results:
| Model | HAcc base → +repeat | SAcc base → +repeat | Correctness base → +repeat |
|---|---|---|---|
| DeepSeek-R1-Distill-Qwen-1.5B | 17.14 → 21.66 (+4.52) | 36.62 → 42.58 (+5.96) | 31.67 → 22.38 (-9.29) |
| Open-Reasoner-Zero-7B | 13.57 → 14.53 (+0.96) | 32.26 → 33.14 (+0.88) | 51.90 → 30.00 (-21.90) |
| **Qwen3-32B** | **43.81 → 59.29 (+15.48)** | **62.82 → 68.34 (+5.52)** | **70.00 → 63.81 (-6.19)** |

The Qwen3 family gets the biggest instruction-following boost. The correctness drop is modest for Qwen3-32B (-6.19pp) but severe for the other two models.

**4. Compositional load compounds the problem.** From Table 8, Qwen3-4B specifically:
- Single constraint: 53.57% HAcc
- Double constraint: 38.57% HAcc
- Triple constraint: 40.00% HAcc

For us: keep the format spec **unified and minimal**. Don't scatter "count N", "order matters", "comma-separated", "inside one box" as 4 distinct rules — fold them into one tight instruction.

**5. Explicit reasoning separation (`<think>...</think>`) helps.** Models that use these tokens generally do better at constraint-following. Qwen3-Thinking-2507 does this natively. ✓

### Implementation plan

**Prompt structure (apply the repeat trick):**

```
[FORMAT INSTRUCTION — appears once at top]

You will solve a math problem. The problem may contain one or more [ANS]
placeholders. Count them — call this number N. Your final answer must be
exactly N comma-separated values inside a single \boxed{}, in the same
order as the [ANS] placeholders appear in the problem.

If N=1: output \boxed{answer}.
If N>1: output \boxed{ans1, ans2, ..., ansN}.

[FEW-SHOT EXEMPLARS]

Example 1: [multi-answer worked example showing \boxed{a, b, c}]
Example 2: [single-answer worked example showing \boxed{x}]

[QUESTION]

{question_text}

[FORMAT INSTRUCTION — repeated at end, right before model takes over]

Remember: count the [ANS] placeholders. Output exactly that many
comma-separated values in your final \boxed{}, in placeholder order.
```

The repetition at the end is the MathIF-paper-derived addition. We're not artificially extending CoT (no "Wait" tokens) — we're just bookending the prompt so when the model emerges from `</think>` and produces its final boxed answer, the constraint is in recent context.

**On few-shot:** generic CoT literature (Wei et al. 2022) and the multi-agent convergence all support 2 exemplars showing the desired format. MathIF doesn't directly test few-shot for format-following but the prior is strong. Plan: 1 multi-answer example, 1 single-answer example, drawn from public.jsonl (so distribution-matched).

**Length:**
- `max_new_tokens` = 16384 minimum. Qwen3 docs allow up to 32768 for math; we may want 24576 as a middle ground to balance throughput vs traces hitting the cap.
- Track per-sample CoT length. Samples that approach the cap are likely format-degraded; the shape filter (Section 3) should catch these but we should also log the correlation.

### What to measure (on fixed_50_v1)

1. **Ablation grid:**
   - Baseline prompt (current v1)
   - + counting instruction at top only
   - + counting instruction repeated at end (MathIF repeat trick)
   - + few-shot exemplars (single + multi)
   - + all of the above

2. **By question type:** MCQ / single-free / multi-free. Watch for regressions on MCQ and single-free as we strengthen the multi-answer instruction — the MathIF correctness/obedience tradeoff predicts this.

3. **By CoT length bin:** are samples in the top length quartile format-degraded? (Sanity-check the MathIF mechanism on our distribution.)

4. **Shape-validity rate** (precursor to Section 3's filter): what fraction of samples produce the correct N comma-separated entries before any filtering?

### Risks

- **The correctness/obedience tradeoff is real and measured.** Stronger format pressure → slightly worse math reasoning. We could end up with more well-formatted wrong answers. Measure both axes.
- **Few-shot examples must match the distribution.** Bad examples (wrong answer, wrong format) will be copied. Curate from `public.jsonl` and verify each exemplar passes math_verify against its gold answer.
- **Over-engineering the prompt.** MathIF's compositional findings warn against piling on rules. If we add 5 different "Remember to do X" lines, HAcc will probably drop. Iterate on a minimal version first.
- **System prompt interaction.** Qwen3 docs recommend not adding extra system prompts to thinking models. Put everything in the user message.

### What MathIF does NOT tell us

- Whether few-shot multi-answer exemplars specifically help (not tested).
- Whether the repeat trick interacts with self-consistency voting (not tested).
- How shape filtering on top of imperfect instruction-following compounds (not in scope).
- Whether for our particular constraint (multi-answer comma-separated in `\boxed{}`), Qwen3-Thinking-2507 specifically does better or worse than its non-thinking base. The paper only evaluates Qwen3-4B (non-Thinking variant).

## 3. Reasoning Prompt Diversity

### Evidence base

**Source:** Hu, Lau, Diwen, Jizhuo, Ng, Low — *"Dipper: Diversity in Prompts for Producing Large Language Model Ensembles in Reasoning Tasks"* — arxiv 2412.15238, EMNLP 2025. Read in full.

**Core claim (clean settling of the multi-agent disagreement):** diverse-prompt ensembles beat single-prompt self-ensembles **at equal compute** on math reasoning. Tested on Qwen2-MATH-1.5B and LLaMA3.2-3B-it across MATH, GSM8K, MMLU-STEM.

Key numbers from Figure 4 (Qwen2-MATH-1.5B on MATH):
| Method | Ensemble size | Accuracy |
|---|---|---|
| Single model | 1 | ~50% |
| Self-ensemble (one prompt, diverse sampling) | 9 | ~56% |
| Dipper-FASV (diverse prompts) | 9 | ~60% |
| Qwen2-MATH-7B baseline | 1 | ~58% |

**Two clean comparisons:**
- Self-ensemble n=9 vs single model: **+6pp** (matches expected SC gain)
- Dipper n=9 vs self-ensemble n=9: **+4pp** (additional gain from prompt diversity at equal compute)
- Dipper n=3 of 1.5B model ≈ single 7B model (cheaper than scaling parameters)

**Mechanism (Figure 3):** at fixed ensemble size of 7, accuracy rises monotonically with number of unique prompts in the ensemble. Single prompt (×7 samples) is the worst; 7 unique prompts is the best. Variance also drops with more unique prompts.

**Stacking:** Dipper + Reflexion-style self-reflection: 57% → 65% (+8pp). The diverse-prompt mechanism is orthogonal to other prompting techniques.

### The critical generalization gap

Dipper tested on **non-thinking** models with 4/8/5-shot prompting at max 512 tokens. We're using Qwen3-4B-Thinking-2507 which has native `<think>...</think>` reasoning and runs ~9300 tokens per sample.

Dipper's "diverse prompts" are reasoning-style *framings*, not format instructions. Examples from their generated pool (Table 4):
- *"Let's think step-by-step to find the answer."*
- *"Apply Mathematical Logic: Use mathematical principles and logic to solve the problem."*
- *"Use Analogies: Relate the question to a familiar concept."*
- *"Consider Cause and Effect: Identify potential causes and their effects."*

**Two real concerns for our setting:**

1. **Redundancy with thinking mode.** Qwen3-Thinking already thinks step-by-step inside its `<think>` block. Adding "Let's think step-by-step" as a user-level hint may be ignored or have no effect. Some of the more specific reasoning styles ("Apply Mathematical Logic") might still steer the model in different directions, but the headline gain may shrink.

2. **Format risk.** The Dipper prompts are layered on top of an already-format-compliant model (Qwen2-MATH outputs `\boxed{}` cleanly). Adding reasoning-style prefixes to our setup, where we're *already* fighting format compliance per Section 2, could split the model's attention. MathIF directly warns that compositional constraints degrade instruction-following.

So the +4pp gain from Dipper is in a setting that's:
- Single-answer (we're often multi-answer)
- Non-thinking (we're thinking)
- Short generations (ours are 10-20× longer)
- Already format-stable (we're not)

The mechanism is real, but the magnitude that transfers to our setting is genuinely unknown.

### Implementation plan (deferred until first 3 levers are measured)

If we pursue this as a fourth lever, the natural shape:

**1. Build a small candidate pool** (10-15 prompts), hand-curated rather than GPT-4o-generated, that compose cleanly with our counting-prompt format instruction. Examples:
- Direct: *"Solve carefully and methodically."*
- Strategic: *"Identify the key relationships first, then compute."*
- Verification-focused: *"After solving, double-check your final answer matches what was asked."*
- Decomposition: *"Break the problem into sub-parts before solving."*

Each candidate is a short prefix that goes BEFORE the counting instruction in the user message. The counting instruction stays **constant** across all variants. Diversity is in reasoning approach, not format spec.

**2. Validate each on a small slice** (~10-15 items from fixed_50_v1). Compute per-prompt accuracy `u(w)` as Dipper's fidelity score.

**3. Skip the FASV optimization.** It assumes a candidate pool of 200 and selects via submodular optimization with sentence-bert embeddings. For 10-15 hand-curated prompts, just pick the top-K by validation accuracy where K matches our SC size, with a tiebreaker for surface-level diversity. The semantic-volume optimization is overkill at our scale.

**4. Run SC across the selected prompts**, with samples-per-prompt = SC_size / K. Vote on the boxed final answers with shape filter applied.

### What to measure (if/when we test this)

- Per-prompt validation accuracy (Dipper's fidelity check). Discard any prompt below baseline.
- SC accuracy with K=4 unique prompts vs K=1 unique prompt at fixed total samples (the clean apples-to-apples).
- Interaction with temperature diversification: does prompt diversity reduce the value of temperature diversification, or do they compose?

### Recommendation: defer

Given that:
- The +4pp Dipper number is in a non-thinking model, single-answer regime, far from ours.
- The MathIF compositional-constraint warning suggests piling on prompts may hurt our format compliance.
- **Direct contradicting practitioner evidence:** the AIMO-2 2nd place team (imagination-research, GitHub repo verified) explicitly tested and dropped system-prompt diversification. Their quote from the repo: *"We find diversifying the system prompt doesn't help for reasoning models."* They kept temperature diversification but not prompt diversification. This is an explicit empirical finding from a top-3 team on a comparable model class (DeepSeek-R1-Distill-Qwen-14B, R1-family thinking model — same lineage as ours).
- We have three independent levers from Sections 1, 2, and the shape filter (Section 4) that all have stronger evidence for our specific setting.
- Adding a fourth lever before measuring the first three confounds the experiment.

**Plan:** ship the counting prompt + shape filter + temperature diversification combo first. Measure on fixed_50_v1. Reasoning-prompt diversity stays deferred with stronger justification than before — the imagination-research finding gives us empirical reason to expect zero benefit, not just uncertainty.

## 4. Shape Filter

### Purpose

Discard SC samples whose final `\boxed{...}` doesn't match the expected output structure for the question, so malformed outputs don't pollute the vote. This is the safety net for the counting-prompt instruction in Section 2 — when the model drifts off-format despite the bookended instruction (especially on long CoT, per MathIF), we don't let that sample vote.

### Evidence base

Two foundational papers inform the design:

**Wang et al. (arxiv 2203.11171, ICLR 2023)** — the original Self-Consistency paper. Their Table 1 directly compares aggregation strategies on PaLM-540B / GSM8K:

| Strategy | Accuracy |
|---|---|
| Unweighted majority vote | 74.4 |
| Length-normalized log-prob weighted sum | 74.1 |
| Unnormalized log-prob weighted sum | 59.9 |
| Weighted average | 22–56 |

Empirically, **plain majority vote ≈ length-normalized logprob weighting**. Their footnote 2: LMs are not well-calibrated, so logprobs don't reliably distinguish correct from incorrect solutions. They also show (Figure 5) that **sample agreement rate is correlated with accuracy** — a free confidence signal that doesn't require logprob access.

**Math-Verify** (HuggingFace library) — handles whitespace and basic latex normalization for boxed content; supports mathematical equivalence checking *within* each entry. But the library's GitHub issue tracker (and the Claude research agent confirmation) flag that strict multi-part validation isn't its default behavior. For our use case, we should use math_verify only for *per-entry* equivalence checks, with our own logic for the outer shape (entry count, ordering).

### Implementation plan

**Four operations applied to each SC sample:**

1. **Count top-level `\boxed{...}` occurrences.** Walk the string with brace-depth tracking, counting only `\boxed{` openings at depth 0. **If the question is multi-answer (N>1) AND count > 1, reject the sample.** Justification: per OpenR1 dataset discussion #5 and Math-Verify CHANGELOG, R1-distilled and Qwen3-Thinking-lineage models routinely emit multiple `\boxed{}` blocks during self-doubt cycles ("`\boxed{999}`. Wait, this is wrong. Actually `\boxed{1}`"), and they also commonly emit one box per answer when given a multi-part problem ("speed of water is `\boxed{4}` km/h, speed of boat is `\boxed{10}` km/h"). For single-answer questions, the grader's last-box convention handles self-doubt cleanly. For multi-answer questions, multi-boxing means the model has broken the requested format and the sample should not vote.
2. **Extract the last `\boxed{...}`** from the generation, with brace-depth tracking to handle nested expressions like `\boxed{\frac{1}{2}}`.
3. **Parse the contents** by splitting on top-level commas only (depth-0 commas), so `\boxed{\frac{1}{2}, x^2 + y^2}` yields two entries, not five.
4. **Check entry count against expected N** for this question.

**Determining expected N:**
- MCQ: N = 1, and the entry must match a single capital letter (we know the choice set from the question).
- Single free-form: N = 1.
- Multi-answer free-form: N = count of `[ANS]` placeholders in the question text.

**Pseudocode:**

```python
def count_top_level_boxed(text: str) -> int:
    """Count \\boxed{ occurrences at brace-depth 0."""
    ...

def extract_last_boxed(text: str) -> str | None:
    """Return contents of last \\boxed{...} or None."""
    # Find all "\boxed{" occurrences, walk braces for the last one
    ...

def split_top_level_commas(s: str) -> list[str]:
    """Split on commas at brace-depth 0. Strip whitespace from entries."""
    ...

def expected_n(question: str, qtype: str) -> int:
    if qtype == "mcq" or qtype == "single_free":
        return 1
    return question.count("[ANS]")

def is_shape_valid(generation: str, expected: int) -> bool:
    # New: reject multi-boxed samples on multi-answer questions
    if expected > 1 and count_top_level_boxed(generation) > 1:
        return False
    boxed = extract_last_boxed(generation)
    if boxed is None:
        return False
    entries = split_top_level_commas(boxed)
    return len(entries) == expected

def shape_filtered_vote(generations: list[str], expected: int) -> str:
    valid = [g for g in generations if is_shape_valid(g, expected)]
    if not valid:
        return fallback_vote(generations, expected)  # degraded path
    boxes = [extract_last_boxed(g) for g in valid]
    canonicalized = [canonicalize(b) for b in boxes]  # whitespace, comma spacing
    return majority(canonicalized)
```

**Canonicalization before voting:** normalize whitespace inside the boxed content so `\boxed{1, 2, 3}` and `\boxed{1,2,3}` count as the same vote. Use `\boxed{a, b, c}` (comma + single space) as our output canonical form when we serialize the winner — this matches the math_verify normalization most likely to be applied by the Kaggle grader.

**Within-entry equivalence:** use math_verify only when two boxed strings differ only in mathematical-equivalent ways (e.g., `\frac{1}{2}` vs `0.5`). For the majority vote, group entries by canonicalized string equality first; only fall back to math_verify equivalence checks if there are tied groups. Why: math_verify is slow per call and we have N=8-16 samples to compare.

### Fallback when all samples are shape-invalid

This happens when the model fails the format on every SC sample for a question. Options in order of preference:

1. **Take the most common malformed answer.** If 7 of 8 samples produce `\boxed{5}` on a multi-answer question where N=3, the model has clearly converged on "5" being part of the answer but failed to enumerate the others. Submit the majority anyway — partial credit > random.
2. **Try the first valid extraction**, even if the count is wrong. Some samples may have the right count plus extras.
3. **Submit a deterministic guess** based on question type (empty answer, or "A" for MCQ as the modal correct choice in many datasets).

Track how often the fallback triggers per question type — if it's >5% on multi-free, something is wrong with the counting prompt and we need to iterate.

### Edge cases to handle

| Case | Handling |
|---|---|
| Numbers like `1,000` in answers | Train counting prompt to use `1000` (no thousand separators). If model insists, fall back to expecting N or N-extras and detect via expected N. |
| Nested LaTeX like `\frac{1}{2}` | Brace-depth tracking in the splitter handles this. |
| Multiple `\boxed{}` in one output on **single-answer** question | Take the LAST one — grader convention. Often a self-doubt cycle artifact (model wrote one answer, reconsidered, wrote another). The last box is the model's final answer. |
| Multiple `\boxed{}` in one output on **multi-answer** question | **Reject the sample.** Indicates the model emitted one box per answer instead of one box with N entries — broken format. Last-box-only would lose all but one answer. Documented R1-family failure mode (OpenR1 dataset discussion #5, Math-Verify CHANGELOG). |
| Empty boxed `\boxed{}` | Invalid. |
| Boxed with only whitespace `\boxed{ }` | Invalid. |
| Latex math mode markers `$\boxed{x}$` | Strip outer `$` before extraction. |
| Boxed contains another boxed (`\boxed{\boxed{x}}`) | Take innermost as the answer entry; uncommon but possible from reasoning models. |
| Ordering: comma-separated but in wrong order | Shape filter accepts it; if grader is order-sensitive (per MathIF caveat), we lose this sample regardless. Track separately. |

### What to measure (on fixed_50_v1)

1. **Shape-valid rate per prompt variant** — the fraction of SC samples passing the filter. Below baseline (no counting prompt) = the prompt change is hurting format compliance.
2. **Vote accuracy with vs without shape filter** at fixed SC size. Expected: filter helps, especially on multi-answer.
3. **Fallback trigger rate** by question type. Should be near-zero on MCQ/single-free, non-zero on multi-free.
4. **Sample agreement rate** as a confidence signal (per Wang et al. Figure 5). Log it per question; correlate with correctness on the fixed_50_v1 to validate it's actually a signal in our setting.

### Risks

- **Over-aggressive filtering with bad fallback.** If the counting prompt makes the model worse at format (the MathIF correctness/obedience tradeoff), filter rejects too many samples and fallback gets the wrong answer. Mitigation: tune the counting prompt strength, monitor shape-valid rate, keep fallback graceful.
- **Base model verbosity is structural.** Bounhar et al. (arxiv 2511.01937) show that standard RLVR training on Qwen3-4B-Thinking-2507 specifically produces a model that "conflates thinking longer with thinking better" — the long-CoT tendency we see in Run 09's ~9300-token average is a trained-in property, not random. Combined with MathIF's long-CoT → instruction-following degradation, this means the shape filter is essential infrastructure, not optional polish. Plan for the long-trace failure case and make sure the filter handles it cleanly.
- **Comma-in-answer collision.** Our shape check assumes comma = entry separator, but math answers can legitimately contain commas (e.g., coordinates `(1, 2)`). Mitigation: strip outermost parens before counting; instruct prompt to use semicolons or spaces inside coordinate-like answers; or accept this as a known failure mode for coordinate-heavy problems.
- **Math_verify ≠ Kaggle grader.** The grader's exact normalization rules are undocumented. Our local extractor uses our best guess of canonicalization; the grader may differ. Two probe submissions (per memory note: slots aren't scarce) can characterize this.
- **Math-Verify itself may be more lenient than our grader.** Per Math-Verify GitHub Issue #47 (verified): default `verify()` can return True when prediction is a subset of gold ([1331, 1728] gold + [1728] pred → True), because the comparison is permissive on multi-answer. Per HF Open LLM Leaderboard blog (Feb 14, 2025), switching from old grader to Math-Verify nearly tripled DeepSeek/Qwen scores on MATH-Hard — the eval choice swings results massively. **Implication:** if we use math_verify locally as a Kaggle-grader proxy, we may overestimate multi-free accuracy. Our local validator should be **literal string-equality on the canonicalized last `\boxed{}` content**, not sympy-aware. Use math_verify only as a tiebreaker or sanity check, not as the grader proxy.
- **The fallback path is a bandaid for a bug we're trying to prevent.** If fallback fires often, the prompt design is wrong, not the filter. Don't let fallback become the primary mechanism.

## 5. Combined Experiment Plan

The action document. Ties Sections 1, 2, and 4 into a concrete ablation on `fixed_50_v1`, with measurement rules and submission criteria. Section 3 (reasoning-prompt diversity) is held out for round 2.

### Phase 0: Establish fixed_50_v1 baseline for base + SC-8

Goal: nail down what the current "do nothing new" setup scores on the slice we're using to compare variants. Kaggle reported 0.614 for Run 09 on the 943-item private set, but `fixed_50_v1` is a 50-item slice and may not match exactly.

**Run:** existing `run_vllm_sc.py` with current v1-baseline prompt, SC-8, T=0.6, on `fixed_50_v1`. No prompt changes, no filter, no temperature diversification. Just re-run the existing setup against the slice.

**Output:** `runs/p0_baseline/summary.json` with overall accuracy, by-type breakdown (MCQ / single-free / multi-free), per-sample token lengths, and the raw boxed extractions for each question. This is the comparison reference point.

**Sanity check:** if this drops below ~0.58 or rises above ~0.66, the slice doesn't match the private distribution closely enough and we shouldn't trust local deltas as Kaggle predictors. Consider expanding to fixed_100 or running a second 50-slice for a noise estimate.

### Phase 1: Linear ablation grid

Five variants, each adds **one** lever to the previous. Run all five on `fixed_50_v1`, same SC budget (N=8), same seed for reproducibility.

| Variant | Lever added | Hypothesis | Section |
|---|---|---|---|
| **V0** | (baseline, Phase 0 result) | — | — |
| **V1** | Counting prompt at top of user message | +pp on multi-free, no regression elsewhere | §2 |
| **V2** | Counting prompt also at end (bookend) | +pp on long-CoT samples specifically | §2 (MathIF "repeat") |
| **V3** | Shape filter on votes | +pp from removing malformed votes | §4 |
| **V4** | Temperature diversification across 8 samples | small +pp from coverage of "hard at one T" cases | §1 |

**Order rationale:**
- Counting prompt first (V1, V2) because it's the lever most directly attacking the failure mode.
- Shape filter (V3) after the counting prompt because the prompt's job is to *produce* well-formed samples; the filter's job is to handle the ones that still drift.
- Temperature diversification last (V4) because its expected gain is smallest and we want to measure each preceding lever's contribution cleanly.

**Compute estimate:** Run 09 was 28.8hr for 943 × 8 samples. 50 × 8 = ~1.5hr per variant. 5 variants → 7-10hr local. Tractable in one session.

### Phase 2: Pick the variant to submit

**Primary criterion:** highest accuracy on the **multi-answer free-form slice** (the failure mode driving the project), without regressing more than 2pp on either MCQ or single-free.

**Tie-breaker:** highest overall accuracy.

**Veto condition:** if the chosen variant has shape-filter fallback rate >10% on multi-free, don't submit — the prompt isn't producing well-formed samples reliably enough. Iterate on the counting prompt phrasing instead.

**Submit one Kaggle submission** of the chosen variant. Compare to Run 09's 0.614.

### Phase 3: Grader probes (parallel, independent of Phase 1-2)

Two submissions to characterize the Kaggle grader's exact normalization. Submission slots are not scarce — these answer questions that can't be resolved locally.

**Probe A — Order sensitivity:**
Take a known-correct multi-answer prediction from the V3+ runs. Submit it once with answers in the [ANS]-placeholder order, then again with answers reordered. Compare scores.

- If equal: grader is order-insensitive — we have flexibility, and ordering errors aren't fatal
- If reordered scores lower: grader is order-sensitive — confirms our default assumption, no behavior change needed

**Probe B — Comma format:**
Same prediction set, but format as `\boxed{a, b, c}` (comma + space) in one submission and `\boxed{a,b,c}` (no space) in another. Compare scores.

- If equal: math_verify-style normalization is in play, our canonicalization is safe
- If different: pick the winning format as our canonical output

Each probe is cheap (one extra inference run if not already cached, plus one Kaggle submission slot). Run both before or in parallel with Phase 1.

### Phase 4 (conditional): Scale-up

Trigger: V4 from Phase 1 shows clear gain over V3 (≥1pp on multi-free, and the per-temperature contribution analysis confirms each T is solving things others aren't).

Then: rerun V4 with SC-16 (2 samples each at T ∈ {0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2}), measure on `fixed_50_v1`, decide whether to submit.

No trigger: don't bother scaling. SC-16 doubles compute for marginal expected gain.

### Measurement infrastructure (required for all phases)

Per-sample logging (one row per generated SC sample):
- variant_id, question_id, sample_index, temperature_used
- generation_length_tokens, generation_truncated_at_max
- last_boxed_raw, last_boxed_canonical, parsed_entry_count
- shape_valid (bool), shape_valid_reason
- vote_weight (1 if valid, 0 if filtered)

Per-question logging (one row per question):
- variant_id, question_id, qtype (mcq/single/multi), expected_n
- gold_answer, predicted_answer, correct (bool)
- num_samples_used (post-filter), agreement_rate (% of valid samples matching winner)
- fallback_triggered (bool)

Per-variant summary:
- overall_acc, mcq_acc, single_acc, multi_acc
- shape_valid_rate (by type), fallback_rate (by type)
- mean / p95 / p99 generation length
- mean agreement rate

The agreement rate is the Wang et al. Figure 5 confidence signal. Log it now so we can validate it as a predictor on our distribution.

### Decision rules — summary table

| Outcome | Action |
|---|---|
| V4 multi-free > V0 multi-free + 5pp, no MCQ/single regression | Submit V4 to Kaggle. Probably worth scaling to SC-16. |
| V4 wins but mainly via V1/V2 (counting prompt) — V3, V4 contribute <1pp each | Submit V2 or V3 (whichever is best) to save compute. Skip SC-16 scale-up. |
| V1-V4 each show no gain or regress on multi-free | Counting prompt isn't working as expected. Diagnose: read sample outputs, check whether the model is following the instruction at all. Iterate on phrasing. |
| MCQ or single-free regresses by >2pp on any V≥1 | Counting prompt is causing collateral damage. Variant that minimizes damage wins; consider per-question-type prompt routing as a future change. |
| Shape filter fallback rate >10% on multi-free | Don't submit. Counting prompt isn't producing well-formed samples; iterate. |

### Risks / circuit-breakers

- **fixed_50_v1 noise.** N=50 means each percentage point is ~0.5 questions. Small differences between variants may not be real. If the V1 → V2 → V3 deltas are all <2pp on multi-free, treat them as approximately equivalent and pick the simplest variant.
- **No baseline carries forward.** Phase 0 baseline must be re-run if any infrastructure changes (vLLM version, tokenizer behavior, etc.). Don't compare against Run 09's Kaggle number alone — it's the slice number that matters for variant comparison.
- **The Kaggle private set is bigger and may behave differently.** A variant that wins by 2pp on fixed_50_v1 may not win by 2pp on Kaggle. Submit, see the actual delta, calibrate expectations going forward.
- **One ablation step at a time.** Don't change the prompt phrasing in the middle of Phase 1 even if you see an obvious improvement. Get clean per-lever attribution first; iterate on phrasing in a follow-up phase.

### Open questions explicitly deferred to round 2

After Phase 1-4 ship and we have a Kaggle measurement of the best variant:

- Reasoning-prompt diversity (§3, Dipper) — add as a 5th lever only if Phase 2 result still has gap to close.
- DeepConf-style logprob-weighted voting — Wang et al. Table 1 suggests it's not worth implementing first, but if our shape-filter agreement rate is unreliable as a confidence signal on our distribution, revisit.
- Per-type prompt routing (different prompts for MCQ vs free-form) — adds complexity, defer until clear single-prompt ceiling is hit.
- Path B (SFT) — explicitly out of scope until Path A is exhausted *and* probe results inform what kind of training data would help.

---

## 6. Anecdotal / Non-Formal Research

Practitioner and informal sources researched May 11. Goal: capture lessons from competition writeups, model-discussion threads, and engineering posts that academic literature doesn't carry. Each finding has source URL, track-record signal where relevant, claim, and direct/partial/tangential relevance to our setup.

### 6.1 Kaggle math competition writeups

**Caveat on the Massaron article (added after multi-agent verification):** Luca Massaron's Medium article on AIMO-2 is explicitly **Gemini 2.5 Pro summarizing the underlying Kaggle writeups**, not a Massaron-written analysis. The title itself reads "Learning from Kaggle Competitions *using Gemini 2.5*." The underlying claims may be roughly correct (Gemini was reading real first-party writeups) but specific quotes, numbers, and attributions in the summary should be cross-verified against the primary sources before being cited. Below, where Massaron findings have been verified against primary GitHub repos or first-party blogs, the primary source is cited; where not, the claim is flagged.

**Primary source: https://github.com/imagination-research/aimo2** (AIMO-2 2nd place — Yichen You, Xuefei Ning, Zinan Lin; Tsinghua + Microsoft Research)
**Track-record signal:** Verifiable GitHub repo with code, configs, and prose writeup. 2nd place AIMO-2 (34/50 public, 31/50 private).

**Findings (verified from repo, not Massaron):**

- **Explicit empirical finding: "We find diversifying the system prompt doesn't help for reasoning models."** Tested and dropped. They kept temperature diversification but not prompt diversification. This is the strongest single piece of evidence that Section 3 (Dipper-style prompt diversity) doesn't transfer to our model class.
- **15 samples = 7 CoT prompts + 8 Code prompts** in their final submission. 32 samples beat 16 in local tests; budget forced 15 online.
- **Question-level early stopping: stop generation when 5 of 7 outputs agree.** Same family of heuristic as NemoSkills' "4 of first 5 agree."
- **Sample-level early stopping on first `\boxed{}` detected.** They observed: "the reasoning model will self-doubt a lot after obtaining the answer early, even if it usually gives out the same answer in the end. And in most cases, after giving the answer between `<think></think>`, the model will rewrite the solution again (at least twice)." Stopping on first box prevents this.
- **Post-SFT collapse precedent: 11 of 16 code prompts failed to elicit code after SFT on math-only data.** Their workaround was keeping both prompts in the SC pool so the un-collapsed mode could still vote. This is the closest documented analog to our OpenR1 single-answer collapse — same family of failure (SFT on narrow data → model loses access to behaviors it had before training).

**Relevance:** Direct, multiple high-confidence findings.

---

**Primary source: https://huggingface.co/blog/winning-aimo-progress-prize** (AIMO-1 winner — Lewis Tunstall, Ed Beeching, et al. — Numina + HuggingFace)
**Track-record signal:** First-party winning writeup. Tunstall is the TRL maintainer.

**Findings (verified):**
- **N=48 × M=4 SC-TIR plateau.** "Increasing either parameter did not improve performance."
- **SC variance: 1-3% across 5-10 seeds on internal validation.** Only practitioner-reported variance number we have for SC on competition math.
- **Quantization gotcha: "casting from bfloat16 to float16 leads to a degradation in model performance"** on T4s. They used 8-bit GPTQ instead.
- **Model merging (DARE, TIES, WARP via mergekit) caused "significant regressions on our internal evaluations."** Dropped entirely.

**Relevance:** Direct. The SC plateau number, variance estimate, and merging warning all transfer.

---

**Primary source: https://github.com/analokmaus/kaggle-aimo2-fast-math-r1** (AIMO-2 9th — Yoshihara, Inoue, Yamaguchi)
**Track-record signal:** Verified GitHub repo with code. Inoue is at Sakana AI.

**Findings (verified from README):**
- **Temperature = 1.0, top_p = 0.90, min_p = 0.05** for SC sampling on Fast-Math-R1-14B. Hotter than Qwen-official T=0.6.
- **GRPO format reward shaping:** `r"^.*?oxed{(.*?)}.*?</think>.*?$"` forces the answer before `</think>`.
- **Inference uses `stop='</think>'`** for early stopping after the answer commitment.
- **GRPO "catastrophic shifts"** confirmed from the README — reward optimized steadily up to a point, then collapsed; team used earlier checkpoints.

**Relevance:** Direct. The T=1.0 datapoint resolves the Section 1 single-trace-vs-SC-diversity tension.

---

**Primary source: NVIDIA blog https://blogs.nvidia.com/blog/reasoning-ai-math-olympiad/** (AIMO-2 1st — NemoSkills, Gitman, Hanley, et al.)
**Track-record signal:** NVIDIA-published first-party.

**Findings (verified):**
- **Vote-based question-level early stop: 4 of 12 same-answer convergence → cancel remaining.**
- **FP8 quantization via TensorRT-LLM: 1.5x speedup. ReDrafter speculative decoding: additional 1.8x.**
- **Solution generalized better on private than public.** "Got the magic in the end."

**Relevance:** Direct.

---

**Source:** https://aimoprize.com/updates/2025-11-19-third-progress-prize-launched
**Date:** Nov 19, 2025
**Findings:** AIMO Progress Prize 3 now uses **H100 GPUs** (2x compute of AIMO-2) and "advanced formats" — explicitly supports GPT-OSS-120B and Qwen3-Next. Up to 128 H100s available for select participants via Fields Institute partnership.

**Relevance:** Tangential. Tells us where competitive math is headed — bigger models, longer thinking. Not directly applicable to a 4B-thinking constraint.

---

### 6.2 Qwen3-4B-Thinking-2507 practitioner notes

**Source:** https://github.com/vllm-project/vllm/issues/22507
**Authors:** vLLM issue reporters; closed by maintainers
**Date:** August 8, 2025
**Track-record signal:** GitHub issue on the official vLLM repo, with reproduction steps and curl output.

**Finding:** **Qwen3-4B-Thinking-2507 does not output an opening `<think>` tag** when used with vLLM's `qwen3` reasoning parser. The reasoning content appears in the regular `content` field with a closing `</think>` tag visible mid-stream, but the parser fails because it expects the opening tag. The reasoning_content field is null.

**Relevance:** **Direct, mechanically important.** Our extraction code needs to handle the case where there's no opening `<think>` tag. Either strip `</think>` and treat everything before it as reasoning, or switch to the `deepseek_r1` parser per the Unsloth recommendation below.

---

**Source:** https://huggingface.co/unsloth/Qwen3-30B-A3B-Thinking-2507-GGUF/discussions/1
**Author:** Daniel Han (Unsloth co-founder, well-known LLM-finetuning engineer)
**Date:** July 30-31, 2025
**Track-record signal:** Unsloth is a widely-used LoRA fine-tuning library; Han is the lead maintainer.

**Finding:** **Confirms the missing `<think>` token issue is across the 2507 thinking family**, not just the 4B. Daniel Han: "We verified that removing the `<think>` is fine, since the model's probability of producing the think token seems to be nearly 100% anyways." Practical fix: delete the `<think>\n` injection from the chat template's `add_generation_prompt` block, OR use `--reasoning-format deepseek` (llama.cpp) / `--reasoning-parser deepseek_r1` (vLLM).

**Relevance:** Direct. Confirms the parser fix path, and the "model emits think anyway" finding means we don't need to *add* `<think>` — the model will produce reasoning regardless.

---

**Source:** https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507/discussions/2
**Author:** Anonymous practitioner running structured output tasks
**Date:** August 6, 2025
**Track-record signal:** Detailed reproduction across multiple quants (4q_K_M, others) with comparison to the previous Qwen3-4B baseline. Comment thread shows multiple confirmers, not a single complaint.

**Finding:** **"Terrible instruction following"** thread title. User reports Qwen3-4B-Thinking-2507 fails Pydantic-schema structured output tasks 50-70% of the time. Direct quote: *"I can see from the responses that it's like the model is clearly smarter, but it just doesn't understand what to do or how to follow instructions."* The previous Qwen3-4B (non-Thinking-2507) handled the same prompt perfectly. Multiple commenters confirm: "That happens in all versions — I tested each one and they all failed the same way."

**Relevance:** **Direct, and important corroboration.** This is the MathIF finding (long-CoT degrades instruction-following) showing up as a real-world practitioner complaint about our specific model. Our shape filter and bookended counting prompt aren't optional — the failure mode this user is hitting is exactly what we're guarding against.

---

**Source:** https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507 (official model card)
**Author:** Qwen team (Alibaba)

**Finding:** Qwen team's own recommendation: **"For highly challenging tasks (including PolyMATH and all reasoning and coding tasks), we use an output length of 81,920 tokens. For all other tasks, we set the output length to 32,768."** Native context is 262,144. Model only supports thinking mode (no `enable_thinking=False`).

**Relevance:** Direct. **We're running at 16K max output, well below the 32K-for-non-reasoning recommendation and 5x below the 81K-for-math recommendation.** This may explain some of our truncation-related format failures — if a long trace gets cut off before the model writes its `\boxed{}`, we get a malformed sample. Worth a controlled experiment: raise max_output to 32K and see if shape-valid rate improves.

---

### 6.3 SC in practice — practitioner takeaways

Most searches in this area returned academic results. Practitioner-level takeaways from the AIMO writeups already covered above:

- **N=48 plateaus on AIMO-1** (Numina, integer-output competition).
- **Vote-based early stopping is universal among top teams** at AIMO-2: 4-of-5 or 4-of-12 thresholds.
- **CISC (Confidence-Informed Self-Consistency)** is widely cited in informal posts: 8-sample CISC matches 30-sample plain SC on MATH (Gemma2-9B). This is academic but the practitioner Medium summary at https://medium.com/@ema.ilic9/confidence-improves-self-consistency-in-llms-313e80467168 reflects industry interest. Track-record signal weak — author is unfamiliar.

**Relevance:** Partial. The early-stop heuristic is the most directly applicable. CISC is in our deferred Section 3 / round-2 territory.

---

### 6.4 Multi-answer math format handling — gap

Searches for multi-answer comma-separated `\boxed{}` formats turned up nothing specifically matching our setup. AIMO competitions are integer-mod-1000, so the top-team writeups don't address multi-answer format. **We're on novel practitioner ground for the specific failure mode we're chasing.** This is part of why this competition is hard — the failure mode isn't well-documented because most public math benchmarks use single-value answers.

The closest practitioner content is the AIMO-2 universal prompt — `"You must put the final answer in \\boxed{}"` — which works for single-answer. Our bookended-counting variant in Section 2 is an unverified extension, not borrowed from a documented practice.

---

### 6.5 Math grader idiosyncrasies — gap, not researched

Did not search this topic in depth. Time-budgeted research focused on Kaggle writeups and Qwen3-Thinking notes since those had highest-density practitioner content. Worth a follow-up search if Probe A and Probe B (Section 5 Phase 3) don't conclusively characterize the grader.

---

### 6.6 Shape filtering / output validation patterns — gap, not researched

Did not search this topic in depth. The math_verify library (HuggingFace) is the de-facto open implementation and our Section 4 design references its canonicalization. Practitioner blog posts on extraction edge cases (LaTeX nesting, malformed boxes) likely exist but were not surveyed in this pass.

---

### 6.7 Burned-hours lessons (compiled across topics 1-2)

Patterns of "what doesn't work" repeatedly surfaced:

- **GRPO instability on small models** (~7B and under). 21st place Ash team (AIMO-2): "Did Not Work" with 7B. 2nd place imagination-research: "did not observe significant improvement on accuracy" after four GRPO runs. Fast-Math-R1-14B: catastrophic shifts after optimization point — had to use earlier checkpoints.
- **Model merging causes regressions.** Numina (AIMO-1 winner) tried DARE, TIES, WARP via mergekit — "significant regressions on our internal evaluations." Dropped entirely.
- **Quantization choice matters more than expected.** Numina noted casting bf16 to fp16 "leads to a degradation in model performance." Top AIMO-2 teams almost universally landed on 4-bit AWQ.
- **T4 GPU support issues** are a real time-sink: cryptic errors with model sharding + torch compilation. Numina had to work around this. (We're not on T4, but the principle — infra incompatibility consumes days — generalizes.)
- **Long-CoT instruction-following degradation** is the practitioner consensus on Qwen3-Thinking-2507 in the wild. The HF "terrible instruction following" thread captures it from a real-world structured-output use case.

**Relevance:** Direct for Path B planning. The GRPO warnings argue strongly against running our own GRPO if we revisit SFT — pick SFT-only or rank/DPO over GRPO. The merging warning means we shouldn't try to combine multiple adapters.

---

### Top 3 most actionable findings (updated after multi-agent cross-verification)

1. **Reject multi-`\boxed{}` samples on multi-answer questions, before voting.** OpenR1 dataset discussion #5 and the Math-Verify CHANGELOG document the failure mode: R1-distilled and Qwen3-Thinking lineage models routinely emit multiple boxes either via self-doubt cycles or by boxing each part of a multi-part answer separately ("speed is `\boxed{4}`... boat is `\boxed{10}`"). The last-`\boxed{}` grader convention destroys the latter case. Added to Section 4 shape filter as the first check.
2. **The vLLM `<think>` parser bug + the `deepseek_r1` parser fix.** vLLM Issue #22507: using `--reasoning-parser qwen3` with Qwen3-4B-Thinking-2507 silently fails because the model never emits an opening `<think>` tag. Maintainer fix: use `--reasoning-parser deepseek_r1`. Verify this is set before Phase 0 baseline runs — otherwise our extraction logic is operating on broken parsed output.
3. **Local validator must mimic Kaggle grader, not Math-Verify defaults.** Math-Verify Issue #47 (verified): default `verify()` treats subset answers as correct on multi-answer ([1331, 1728] gold + [1728] pred → True). If we use math_verify locally, we overestimate multi-free accuracy. Local validator should be literal string-equality on canonicalized last `\boxed{}` content. Math_verify only as a tiebreaker for clear equivalence cases.

### Surprises (updated)

- **AIMO-2 writeups make no mention of multi-answer comma format handling**, despite that being our central failure mode. The competition is integer-output, so top-team writeups don't help here. **We're solving a problem the practitioner literature hasn't documented well.** Continued search on this specific topic has low expected value; our own ablation is the most direct path.
- **The strongest contradiction to academic prompt-diversity literature** is the imagination-research (AIMO-2 2nd place) explicit finding: *"diversifying the system prompt doesn't help for reasoning models."* Tested empirically, dropped from their final pipeline. This is stronger than my original Section 3 "uncertain generalization" hedge — it's positive evidence the technique doesn't transfer to reasoning models in our class.
- **Reasoning models self-doubt after their first `\boxed{}` and rewrite the solution at least twice** (imagination-research observation, also visible in Open R1 outputs). This argues for sample-level early stopping at first box on single-answer questions but against it on multi-answer (which we ship without sample-level early stop). Question-level early stopping (4-of-5 or 5-of-7 majority) is still safe.
- **Numina found SC plateaued at N=48** on AIMO-1, not at N=8 or N=16. Variance was 1-3% across 5-10 seeds — important calibration: a 1-2pp difference between our variants on fixed_50_v1 may not survive the seed-variance floor on a larger test set.
- **Multiple top AIMO-2 teams used DPO or GRPO specifically to reduce output length**, not for accuracy. Unexpected use of preference optimization; Frugal-AI confirms this is a real structural problem on Qwen3-Thinking models.

### Verified-but-cant-strongly-attribute / gaps

- Math grader idiosyncrasies: not researched. Grader-probe submissions (Section 5 Phase 3) are the substitute.
- Shape filtering edge cases: not researched. math_verify source code is the authority.
- Qwen3-Thinking-2507 prompt-routing tricks (per-question-type prompts): no specific writeups found. Stays in round-2 deferrals.

---

## 7. Locked Implementation Plan

This section consolidates Sections 1-6 into the concrete spec to execute. All open questions in earlier sections resolve here. If anything in this section conflicts with an earlier section's hedge, **this section wins**.

### 7.1 Inference configuration (apply before any phase)

Apply these once, verify the model emits expected token sequences, then never change them during the ablation. Changes mid-ablation invalidate comparisons.

**Model:** `Qwen/Qwen3-4B-Thinking-2507` (stock weights, no adapter)

**vLLM engine config:**
- `--reasoning-parser deepseek_r1` (**not** `qwen3` — the qwen3 parser silently fails on this model per Issue #22507)
- `enable_prefix_caching=True` (KV-cache reuse across per-temperature `generate()` calls)
- `--max-model-len`: at least 36K (32K output + ~4K input context buffer)

**Sampling params (single-temperature baseline, V0-V3):**
- temperature = 0.6
- top_p = 0.95
- top_k = 20
- min_p = 0
- max_tokens = 32768 (Qwen's recommended floor for reasoning tasks; up from current 16K)
- presence_penalty = 1.0 (small Qwen3 models exhibit endless-repetition loops on long generations per multiple practitioner reports; this is the documented mitigation)

**Sampling params (temperature-diversification variant, V4):**
- Cross-temperature ladder: 2 samples each at T ∈ {0.5, 0.7, 0.9, 1.1}
- All other params identical to single-temp setting
- Per-T calls in a loop (not n=8 in one call) so each T gets its own SamplingParams

**Pre-Phase-0 verification step:**
1. Run a single example through the pipeline.
2. Confirm the parsed output has reasoning content separated from final content (deepseek_r1 parser working).
3. Confirm last `\boxed{}` is correctly extracted.
4. Confirm no opening `<think>` tag is expected or required.

If any of these fail, fix before running Phase 0. Measuring with broken extraction wastes the ablation.

### 7.2 Prompt structure (locked)

**Bookended multi-answer counting prompt.** Format spec at top AND end of user message — MathIF "repeat" trick.

```
SYSTEM: You are a careful mathematical reasoner. Solve the problem step by step.

USER:
You will solve a math problem. Read the format instructions carefully.

Format instructions:
- Your final answer must appear in a single \boxed{} at the end.
- If the question has multiple [ANS] placeholders, your \boxed{} must contain
  exactly that many values, separated by commas in a single box.
  Example: for 2 [ANS] placeholders, output \boxed{a, b}.
- Do not output multiple \boxed{} blocks.

Question:
{question_text}

Format reminder: provide exactly the number of values requested,
comma-separated, inside a single \boxed{}.
```

**No system-prompt diversification.** imagination-research (AIMO-2 2nd) tested and dropped it for reasoning models. Single prompt across all SC samples.

**No few-shot exemplars in V1-V4.** Adding exemplars is a separate change — keep ablation linear. If V4 wins and there's still a gap, exemplars become V5 in a round-2 experiment.

### 7.3 Self-Consistency setup (locked)

- **SC budget: N=8** for Phase 1 ablation.
- **No sample-level early stopping.** Per imagination-research, reasoning models self-doubt and rewrite after first `\boxed{}`. Stopping at first box risks capturing an interim guess.
- **No question-level early stopping during Phase 1 ablation** — clean per-variant comparison needs full N samples per question. Save question-level early stop for Phase 4 SC-16 scale-up.

### 7.4 Shape filter (locked rules)

Applied to each SC sample in order:

1. **Count top-level `\boxed{` occurrences** at brace-depth 0.
2. **If question is multi-answer (N>1) AND count > 1: REJECT sample.** Documented R1-family failure mode where model emits one box per answer.
3. **Extract last `\boxed{...}` content** with brace-depth tracking.
4. **Strip outer `$...$` if present** (LaTeX math-mode wrapper).
5. **Split contents on top-level commas** (depth-0 commas only — preserves `\frac{1}{2}` as one entry).
6. **Strip whitespace from each entry.** Strip any leading `x=`, `y=`, etc. variable assignments.
7. **Compare entry count to expected N.** Reject if mismatch.
8. **Canonicalize valid samples** to `\boxed{a, b, c}` (comma + single space) before voting.

### 7.5 Voting (locked)

- **Majority vote on canonicalized last-`\boxed{}` content among shape-valid samples.**
- **No logprob weighting.** Wang et al. Table 1: empirically equivalent. Not worth implementing.
- **Tiebreaker:** if two answers tied, use math_verify equivalence to merge groups (per-entry). If still tied, prefer the answer from the lower-temperature sample.
- **Fallback when all samples filtered out:** take most common malformed answer (partial credit > random). Log fallback trigger.

### 7.6 Local validator (locked)

For Phase 0 and Phase 1 measurement on `fixed_50_v1`:

- **Literal string equality** on the canonicalized last `\boxed{}` content vs gold answer.
- **NOT math_verify default behavior.** Per Math-Verify Issue #47, default `verify()` is permissive on multi-answer (treats subset answers as correct). Math_verify only as a sanity-check tiebreaker for clear equivalence cases.
- Per-question logging: gold, predicted, correct, all sample votes, agreement rate, fallback triggered.

### 7.7 Phase sequence (locked)

**Phase 0:** Run base + SC-8 with the locked config on `fixed_50_v1`. Establish baseline. Sanity check: ~0.58-0.66 expected.

**Phase 1:** Linear ablation, all on `fixed_50_v1`, same seed:

| Variant | Lever added |
|---|---|
| **V0** | Phase 0 baseline result (config fixes only — `deepseek_r1` parser, 32K max_tokens, presence_penalty) |
| **V1** | + multi-answer counting prompt at TOP of user message only |
| **V2** | V1 + counting prompt also at END (bookend) |
| **V3** | V2 + shape filter with multi-`\boxed{}` rejection |
| **V4** | V3 + temperature diversification (cross-T ladder) |

**Phase 2:** Pick variant by **multi-free accuracy with no >2pp regression on MCQ/single-free**. Veto if shape-filter fallback rate >10% on multi-free. Submit one Kaggle submission.

**Phase 3 (parallel):** Two grader probes:
- **Probe A:** Order-permuted multi-answer submission to test grader order-sensitivity.
- **Probe B:** Comma-space (`\boxed{a, b}`) vs comma-no-space (`\boxed{a,b}`) for whitespace normalization.

**Phase 4 (conditional):** Scale to SC-16 only if V4 beats V3 by ≥1pp on multi-free. Add question-level early stop (4-of-first-5 agreement → cancel remaining) to manage compute.

### 7.8 Logging (locked)

Per sample: `variant_id`, `question_id`, `sample_index`, `temperature`, `generation_length_tokens`, `generation_truncated_at_max`, `top_level_boxed_count`, `last_boxed_raw`, `last_boxed_canonical`, `parsed_entry_count`, `shape_valid`, `shape_invalid_reason`, `vote_weight`.

Per question: `qtype`, `expected_n`, `gold`, `predicted`, `correct`, `num_samples_used`, `agreement_rate`, `fallback_triggered`.

Per variant: `overall_acc`, `mcq_acc`, `single_acc`, `multi_acc`, `shape_valid_rate` by type, `fallback_rate` by type, `mean/p95/p99 generation_length`, `mean agreement_rate`.

### 7.9 What's NOT in this plan (deferred to round 2)

- Sample-level early stopping (risky for multi-answer)
- Question-level early stopping during Phase 1 ablation
- System-prompt diversification (imagination-research empirical evidence: doesn't help reasoning models)
- Few-shot exemplars in the prompt
- Logprob-weighted voting (not better than plain majority per Wang et al.)
- Per-question-type prompt routing
- Token scheduler / dynamic compute allocation
- Path B SFT

### 7.10 Pre-flight checklist (before Phase 0 runs)

- [ ] vLLM running with `--reasoning-parser deepseek_r1`
- [ ] `enable_prefix_caching=True` in engine config
- [ ] `max_tokens=32768` confirmed in sampling params
- [ ] `presence_penalty=1.0` set
- [ ] One-example smoke test passes (parsed reasoning content + extracted last `\boxed{}` correct)
- [ ] Local validator is literal string-equality, not math_verify-default
- [ ] Logging schema (§7.8) implemented and verified with one question
- [ ] `fixed_50_v1` reachable and same set of question_ids as before

When all 8 boxes are checked, run Phase 0. The plan is locked from there.

---

## Changelog
- 2026-05-11: Doc created. Section 1 (Temperature Diversification) complete based on Sun et al. 2510.02611 full read.
- 2026-05-11: Section 2 (Multi-Answer Counting Prompt) complete based on MathIF / Fu et al. 2505.14810 full read. Key derived design choice: bookend the format instruction at top and bottom of prompt (the "repeat" trick from Table 6).
- 2026-05-11: Section 3 (Reasoning Prompt Diversity) complete based on Dipper / Hu et al. 2412.15238 full read. Mechanism real (+4pp diverse vs self-ensemble at n=9 on Qwen2-MATH-1.5B), but generalization to thinking model + multi-answer setting is uncertain. Deferred to second-round experiment.
- 2026-05-11: Section 4 (Shape Filter) complete based on Wang et al. 2203.11171 (original Self-Consistency, ICLR 2023) Table 1 plus math_verify engineering knowledge. Key derived design choice: simple majority vote on shape-filtered samples — logprob weighting is empirically equivalent and not worth the implementation cost. Use sample agreement rate as a confidence signal.
- 2026-05-11: Section 4 Risks updated to incorporate Bounhar et al. 2511.01937 (Frugal-AI) — confirms verbosity is structurally trained into Qwen3-4B-Thinking-2507, reinforcing why shape filter is essential infrastructure.
- 2026-05-11: Section 5 (Combined Experiment Plan) complete. Linear ablation V0-V4 on fixed_50_v1, primary criterion is multi-free accuracy without regression elsewhere. Phase 3 grader probes run in parallel. Phase 4 scale-up to SC-16 conditional on V4 showing clear gain.
- 2026-05-11: Section 1 implementation note tightened to cite Kwon et al. 2309.06180 (vLLM/PagedAttention paper) and explicitly require `enable_prefix_caching=True` for the per-temperature loop to share prefill across temperatures.
- 2026-05-11: Read DeepSeekMath / Shao et al. 2402.03300. Confirmatory/contextual: GRPO (introduced here) is in the training lineage of our base model. Their SC scaling result (single-sample 51.7% → SC-64 60.9% on MATH, +9.2pp) serves as a rough upper bound for pure-SC-scale-up gains on math benchmarks. Most of our remaining headroom must come from the counting prompt and shape filter, not from doubling SC samples. No section change.
- 2026-05-11: Section 6 (Anecdotal / Non-Formal Research) added. Practitioner sources covered: Massaron AIMO-2 survey (22 top solutions), HuggingFace Numina AIMO-1 writeup, NVIDIA NemoSkills AIMO-2 win, vLLM Issue #22507 (missing `<think>` tag), Unsloth GGUF discussion, HF "terrible instruction following" thread, Qwen official 81K-token recommendation. Three top actionables: vote-based 4-of-5 early stopping for SC scale-up, the vLLM reasoning-parser fix (`deepseek_r1` instead of `qwen3`), and raising max output tokens from 16K to 32K. Honest gaps documented: math grader idiosyncrasies and shape-filter edge cases were not searched in depth.
- 2026-05-11: Multi-agent verification dive. Four other agents asked to do the same practitioner-research task. Critical correction: Massaron Medium article is Gemini-2.5-Pro-generated summary content, not Massaron-authored — downgraded all Massaron citations in Section 6 to "Gemini summary of [primary source]" and replaced where possible with direct GitHub repo citations (imagination-research/aimo2, analokmaus/kaggle-aimo2-fast-math-r1). Added imagination-research direct finding "system prompt diversification doesn't help for reasoning models" to Section 3 (strengthens deferral from "uncertain" to "positive empirical evidence against"). Added multi-`\boxed{}` rejection rule to Section 4 shape filter (R1-lineage models routinely emit one box per answer on multi-part questions; documented in OpenR1 discussion #5 and Math-Verify CHANGELOG). Added Math-Verify Issue #47 caveat to Section 4 risks (default verify() is permissive on multi-answer; local validator should be string-equality, not math_verify-default). Updated Section 6 top 3 actionable accordingly.
- 2026-05-11: Section 7 (Locked Implementation Plan) added. Consolidates Sections 1-6 into concrete spec: vLLM config (`--reasoning-parser deepseek_r1`, `enable_prefix_caching=True`, max_tokens=32K, presence_penalty=1.0), bookended counting prompt template, locked shape filter rules including multi-`\boxed{}` rejection, locked voting and fallback behavior, phase sequence with sanity checks, and 8-item pre-flight checklist.

## Doc status: locked and ready to execute

Seven sections written. **Section 7 is the executable spec.** Run the §7.10 pre-flight checklist, then Phase 0. The plan is locked — no design changes during the ablation; only after Phase 1 measurements come in do we consider deviations.

Open items deferred explicitly per §7.9: Dipper-style prompt diversity (round 2, weaker case now per imagination-research finding), logprob-weighted voting (only if agreement-rate signal fails), per-type prompt routing (round 2+), Path B SFT (only after Path A is exhausted).

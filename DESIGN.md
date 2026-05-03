# Design Notes

## 1. Prompt Engineering

### 1.1 Goal

The goal of this phase is to improve accuracy on the CSE151B competition task using prompt engineering only.

The target model remains:

```text
Qwen/Qwen3-4B-Thinking-2507
```

Prompt engineering should improve the model’s ability to solve both multiple-choice and free-response math problems while preserving clean answer extraction through `\boxed{}` formatting.

This phase comes before heavier methods such as supervised fine-tuning or reinforcement learning.

---

### 1.2 Current Repo Behavior

The current notebook already supports different prompt behavior for multiple-choice and free-response problems.

The dataset contains:

```text
question
answer
id
options
```

The key discriminator is the `options` field:

```text
options exists and is non-empty  -> multiple-choice problem
options missing or empty         -> free-response problem
```

There is no reliable `question_type`, `type`, `choices`, or `multiple_choice` field. Therefore, the correct heuristic is:

```python
is_mcq = isinstance(options, list) and len(options) > 0
```

The current prompt-construction function has this general form:

```python
def build_prompt(question: str, options: Optional[list]) -> tuple[str, str]:
    ...
    return system_prompt, user_prompt
```

This return structure should be preserved unless there is a strong reason to change the generation pipeline.

---

### 1.3 Prompt Architecture

We will use separate prompt templates for:

```text
multiple-choice questions
free-response questions
```

We should not use one large universal prompt unless question-type detection fails.

Reason:

Multiple-choice questions require the model to solve the problem and then map the result back to a lettered answer choice.

Free-response questions require the model to produce the exact mathematical answer directly.

Therefore, prompt behavior should branch as follows:

```text
MCQ:
- solve carefully
- compare result against choices
- final answer should be only the option letter inside \boxed{}

Free-response:
- solve carefully
- give exact answer unless approximation is requested
- final answer should be the mathematical answer inside \boxed{}
```

---

### 1.4 Controlled Variables

During prompt comparisons, the only thing that should change is the prompt policy.

The following should remain fixed:

```text
model
dataset slice
question order
temperature
top_p / top_k
max_new_tokens
seed, if used
answer parser
evaluation script
runtime environment
submission/output format
```

In particular, `max_new_tokens` must remain fixed during prompt comparisons.

Changing `max_new_tokens` at the same time as the prompt makes it unclear whether a result improved because of better wording or because the model had more room to reason.

Token-budget experiments should be run separately.

---

### 1.5 Baseline Plan

Previous runs used a 20-question slice. That is useful for smoke testing, but too small for serious prompt comparison.

A 20-question slice is good for checking:

```text
Does the code run?
Does the model generate?
Are answers boxed?
Does parsing work?
Is runtime acceptable?
```

For prompt engineering, we will first create a fixed 50-question validation slice.

The current baseline prompt should be rerun on this same 50-question slice before testing new prompt policies.

This gives a clean comparison:

```text
baseline prompt on fixed 50-question slice
vs.
new prompt policy on same fixed 50-question slice
```

We should not compare a baseline from a 20-question run against a new prompt from a 50-question run.

---

### 1.6 Validation Slice

The first prompt-engineering slice should contain 50 questions.

Ideally, the slice should roughly preserve the competition distribution:

```text
about 1/3 multiple-choice
about 2/3 free-response
```

Since the public data has 375 MCQ problems out of 1126 total, a 50-question slice could contain roughly:

```text
15-20 MCQ questions
30-35 free-response questions
```

The exact same 50-question slice should be reused for every first-round prompt trial.

---

### 1.7 Metrics to Record

For every run, record:

```text
overall accuracy
multiple-choice accuracy
free-response accuracy
number of parse failures
number of missing boxed answers
number of invalid MCQ answers
runtime
average output length, if easy to collect
max_new_tokens
temperature
prompt policy name
run ID
```

It is important to track MCQ and free-response accuracy separately.

A prompt may improve one category while hurting the other. If that happens, we may keep only the useful half of the prompt policy.

---

### 1.8 Prompt Policy Definition

A prompt policy is the full paired prompt strategy for both problem types.

Each policy includes:

```text
MCQ system prompt
MCQ user prompt format
free-response system prompt
free-response user prompt format
```

It is valid to change both the system prompt and user prompt together, as long as we treat the pair as one prompt policy.

The conclusion should be phrased as:

```text
Prompt Policy B beat Prompt Policy A.
```

Not:

```text
This exact sentence in the system prompt caused the improvement.
```

To make claims about individual prompt components, we need ablation testing.

---

### 1.9 First-Round Prompt Policies

> **Status (2026-05-03):** The original 5-policy plan has been substantially superseded by published evidence and our own findings. **Only v1-baseline (Policy 0, sig-figs patched) and v2-mcq-commit (a tightened revision of Policy 4) were actually run.** Policies 1, 2, 3 are formally dead (see status notes below). The verbatim text remains here for the historical record only.

#### Policy 0 → v1-baseline (sig-figs patched). RAN as Run 05.

Purpose: establish the baseline on `fixed_50_v1`.

Result: 70.0% / 82.4% MCQ / 63.6% free at 16k cap. Locked as the prompt-sweep anchor. See [`experiments.md`](experiments.md) > Run 05 + Prompt Versions > v1-baseline for the patched text and rationale.

---

#### Policy 1: Careful Reasoning. **DEAD.**

> **Status: dead.** Subsumed by Anti-Patterns in CLAUDE.md. "Reason step by step" / "check work" prompts are neutral or harmful on a thinking model — the model already does extensive `<think>` reasoning by default, and explicit reasoning instructions either drift into Policy 2/3 territory (length pressure) or just restate what the model is already doing. Not worth a run.

Original wording (for the historical record): solve accurately, reason step by step, check work, final answer inside `\boxed{}`.

---

#### Policy 2: Brief but Sufficient Reasoning. **DEAD.**

> **Status: dead.** "Be brief" / length-pressure prompts on thinking models are an Anti-Pattern in CLAUDE.md. Frugal Table 5 + general published evidence: forcing shorter reasoning on a thinking model degrades accuracy. Run 06's v2-mcq-commit ("Stop generating immediately after `\boxed{}`") *did* shrink the median MCQ response by 13% but converted **0 of 3** MCQ cutoffs to correct answers — the items hitting the cutoff cluster are reasoning-bound, not budget-bound (Insight 2). Brevity prompts attack the wrong axis.

Original wording: brief but sufficient reasoning, avoid unnecessary verbosity, final answer inside `\boxed{}`.

---

#### Policy 3: Anti-Error / Checking Prompt. **DEAD.**

> **Status: dead.** "Check your work" prompts on thinking models are an Anti-Pattern in CLAUDE.md. The model's default `<think>` block already performs verification; explicit "check arithmetic / units / edge cases" instructions are noise.

Original wording: check arithmetic, check units, check edge cases, check whether the problem asks for an exact value or choice.

---

#### Policy 4 → v2-mcq-commit. RAN as Run 06.

Original Policy 4 was "MCQ-elimination + exact free-response." It morphed into v2-mcq-commit, which keeps the question-type specialization spirit but replaces "compare and eliminate choices" (length-encouraging) with "stop immediately after `\boxed{LETTER}`" (commitment-targeted). Free-form prompt held byte-identical to v1 to keep the comparison clean.

Result: 66.0% overall (−2 q vs Run 05), MCQ 76.5% (−1 q), free 60.6% (−1 q). **Not promoted.** Both losses explainable by either ambiguous gold (id=48) or sampling noise (id=199). MCQ-cutoff cluster unaffected: 0 of Run 05's 3 MCQ cutoffs converted to correct under v2.

See [`experiments.md`](experiments.md) > Run 06 + Insight 2 + Insight 7 for the full analysis. The v2 wording lives in `scripts/run_vllm_experiment.py:PROMPTS["v2-mcq-commit"]`.

---

#### Conclusion of the prompt sweep

Two policies survived the literature filter and got tested. Neither beat baseline at n=50 within the +4 q promotion bar (DESIGN.md §1.11). The MCQ-cutoff cluster, hypothesized to be commitment-bound, turns out to be reasoning-bound (Insight 2). **Phase 1 (prompt engineering) has hit its ceiling at this model + slice + cap.** Move to Phase 2 (self-consistency); see §3.

---

### 1.10 First-Round Experiment Plan — Outcome

> **Updated 2026-05-03 to reflect actual runs.** Original plan was 5 policies × 50q. Three policies (1, 2, 3) became Anti-Patterns and were never run; Policy 0 → Run 05 and Policy 4 → Run 06 (as v2-mcq-commit). Reality:

| Planned | Actual | Run | Result on `fixed_50_v1` | Verdict |
|---|---|---|---|---|
| Policy 0 (baseline) | v1-baseline (sig-figs patched) | 05 | 70.0% / 82.4% MCQ / 63.6% free, 4 cutoffs | **Anchor.** Locked. |
| Policy 1 (careful) | — (dead) | — | — | Anti-Pattern; not run |
| Policy 2 (brief) | — (dead) | — | — | Anti-Pattern; not run |
| Policy 3 (checking) | — (dead) | — | — | Anti-Pattern; not run |
| Policy 4 (MCQ-elim) | v2-mcq-commit | 06 | 66.0% / 76.5% MCQ / 60.6% free, 3 cutoffs | Not promoted (within noise; MCQ-cutoff structural per Insight 2) |

Same-slice, same-engine, same-cap, same-sampling between Runs 05 and 06 — only the MCQ system prompt changed. Per-item agreement: 48/50 (the 2 flips were id=48 ambiguous gold and id=199 free-form sampling noise).

Phase 1 conclusion: the prompt-only lever has been exercised within the safe set; no winner exists at n=50 within the +4 q promotion bar. See §1.18 (Phase 1 Outcome) for the strategic summary and §3 for the Phase 2 plan.

---

### 1.11 Promotion Criteria

A 50-question run is still somewhat noisy.

On 50 questions:

```text
+1 correct answer = 2 percentage points
```

Therefore:

```text
A gain of 1 question out of 50 is not strong evidence.
A gain of 4-6 questions out of 50 is worth promoting to a larger run.
```

After first-round testing:

```text
Top 1-2 prompt policies should be promoted to a 100-question or 200-question run.
```

If runtime is expensive, start with 100. If runtime is acceptable, use 200.

A prompt should be promoted if:

```text
it improves overall accuracy meaningfully
or
it significantly improves MCQ without hurting free-response
or
it significantly improves free-response without hurting MCQ
or
it reduces parse failures / invalid outputs
```

If a policy improves only one question type, consider keeping only that branch of the prompt.

---

### 1.12 Ablation Testing Plan

Initial prompt trials compare whole prompt policies.

Ablation testing comes after identifying one or two promising policies.

The purpose of ablation testing is to determine which part of the prompt caused the improvement.

Possible ablations:

```text
baseline system prompt + new user prompt
new system prompt + baseline user prompt
new system prompt + new user prompt
MCQ prompt changed only
free-response prompt changed only
MCQ final-answer instruction changed only
free-response exact-answer instruction changed only
```

Example ablation matrix:

| Ablation | System Prompt | User Prompt | Purpose |
|---|---|---|---|
| A0 | baseline | baseline | control |
| A1 | baseline | new | test user prompt effect |
| A2 | new | baseline | test system prompt effect |
| A3 | new | new | test combined policy |
| A4 | new MCQ only | baseline long | isolate MCQ change |
| A5 | baseline MCQ | new long only | isolate long-form change |

Ablation testing should use the same fixed validation slice as the original comparison unless we are promoting to a larger confirmation run.

---

### 1.13 Failure Modes to Track

Prompt engineering should not only track accuracy. It should also track output-format failures.

Important failure modes:

```text
no boxed answer
multiple boxed answers
answer outside \boxed{}
MCQ outputs full solution instead of letter
MCQ outputs a letter not present in the options
MCQ outputs both letter and value inside \boxed{}
free-response gives decimal when exact answer is expected
free-response gives multiple answers when one is expected
reasoning gets cut off by max_new_tokens
parser extracts the wrong boxed expression
model refuses or gives non-math response
```

These failures should be logged separately when possible.

This helps distinguish:

```text
model reasoning failure
prompt-format failure
answer-parser failure
token-budget failure
```

---

### 1.14 Output and Run Logging

Each run should save outputs to a uniquely named file.

Do not overwrite baseline results.

Suggested directory:

```text
runs/
```

Suggested filename pattern:

```text
runs/prompt_v0_baseline_50.jsonl
runs/prompt_v1_careful_50.jsonl
runs/prompt_v2_brief_50.jsonl
runs/prompt_v3_checking_50.jsonl
runs/prompt_v4_specialized_50.jsonl
```

Each output row should ideally include:

```json
{
  "run_id": "prompt_v1_careful_50",
  "problem_id": "...",
  "question_type": "mcq",
  "question": "...",
  "options": ["...", "..."],
  "gold_answer": "...",
  "raw_output": "...",
  "extracted_answer": "...",
  "is_correct": true,
  "parse_failure": false
}
```

This makes later analysis easier.

---

### 1.15 Experiment Log Template

Use a table like this in the design doc or a separate experiment log.

| Run ID | Date | Prompt Policy | Questions | MCQ Count | Free Count | Accuracy | MCQ Acc. | Free Acc. | Parse Failures | max_new_tokens | Temp | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| prompt_v0_baseline_50 | TBD | Baseline | 50 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Current repo prompts |
| prompt_v1_careful_50 | TBD | Careful reasoning | 50 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |  |
| prompt_v2_brief_50 | TBD | Brief reasoning | 50 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |  |
| prompt_v3_checking_50 | TBD | Anti-error/checking | 50 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |  |
| prompt_v4_specialized_50 | TBD | MCQ/free specialized | 50 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |  |

---

### 1.16 What Not to Change During Prompt Trials

> **Removed.** Now lives in [`CLAUDE.md`](CLAUDE.md) > Inference Constraints + Experimentation Discipline (one-variable rule, locked sampling defaults, engine-as-variable, slice-immutability, `Don't change the prompt parser or scorer mid-sweep`). Original content also contained an obsolete vLLM-isolation rule that was superseded when both engines moved to the same `.venv` (see SETUP.md).

### 1.17 Notes for Coding Agents

> **Removed.** Now lives in [`CLAUDE.md`](CLAUDE.md) > Role + Experimentation Discipline (inspect before editing, minimal changes, no package installs without ask, no notebook edits unless asked, no overwriting previous run outputs). The `build_prompt(question, options) -> (system, user)` interface assertion was also superseded — current runner uses `build_prompt(question, options, policy)` to support the PROMPTS registry.

---

### 1.18 Phase 1 Outcome (was: Summary of Immediate Next Steps)

> Original §1.18 listed the 8-step plan to *start* Phase 1. All 8 are now done or superseded. Replaced with the Phase 1 outcome — what was concluded, why, and what comes next.

**Phase 1 conclusion: prompt engineering at this model + slice + cap has hit its ceiling.** Two policies survived the Anti-Patterns filter and got tested at n=50; neither beat the v1 anchor by the +4 q promotion bar. The cluster of items that drives most MCQ failures is reasoning-bound, not budget-bound or commitment-bound — and prompt instructions can't fix reasoning.

**Three load-bearing findings from Phase 1** (full write-ups in [`experiments.md`](experiments.md) > Insights):

1. **Token budget reduces cutoff rate but doesn't unlock reasoning depth on items that aren't already cap-bound.** 8k → 16k cap dropped cutoff rate 30% → 8% on `fixed_50_v1`, but avg gen tokens barely moved (4899 → 4871) and p50 was 3536 — most items don't use the extra budget. **16k locked as the operating point.** Chasing 32k would only matter if cutoffs > ~5/50; Frugal Table 5 shows diminishing returns past 16k for the base model. ([Insight 1](experiments.md))
2. **MCQ-cutoff cluster is structural, not prompt-engineerable at this cap.** Survives engine swap, cap doubling, AND a commitment-targeted prompt (v2). Run 06 converted 0 of Run 05's 3 MCQ cutoffs to correct answers — its reduced cutoff count (3→2) came from the model committing to wrong answers earlier, not from solving the items. **The items are reasoning-bound.** ([Insight 2](experiments.md))
3. **Combined noise floor on n=50 is ~3-5 q.** Sampling + engine variance contributes ±2 q (Insight 6: same-slice flips between Run 05 and Run 06); ambiguous-gold contributes ~2-3 q (Insight 7: id=48 case + instructor-confirmed dataset errors). **Any prompt-policy comparison under +4 q at n=50 is within combined noise.** Promotion bar in §1.11 stays right; the floor explains why Policy 4 (v2) at −2 q is non-evidence either way. ([Insight 6, 7](experiments.md))

**Strategic implication.** The prompt-engineering knob is exhausted *within the literature-safe set of policies*. Further work on the prompt axis would either (a) re-run Anti-Pattern policies hoping for a surprise, or (b) propose entirely new prompt strategies — both low-EV. The next high-leverage move is **sample-level (self-consistency, §3) or training-level (§4)**, not more prompt iteration.

**Carry-forward from Phase 1:**
- v1-baseline (sig-figs patched) is the locked prompt for all subsequent phases unless explicitly changed
- `fixed_50_v1` is the locked Phase-1/Phase-2 evaluation slice
- 16k token budget / 24576 max_model_len is the locked operating point on Pod B
- The Anti-Patterns list in CLAUDE.md is the persistent residue of Phase 1's literature filter — protects future work from re-trying dead policies

**Phase 2 entry point:** §3 (Self-Consistency).

---

## 2. Phase 1 → Phase 2 Transition

Phase 1 conclusion (§1.18): the prompt-engineering knob is exhausted within the literature-safe set; the items driving most failures are reasoning-bound, not budget- or commitment-bound. Phase 2's question: **can we get free accuracy by sampling the model multiple times and voting?**

**Hypothesis.** Self-consistency (Wang et al. 2022) reduces sampling noise on items where the model "knows" the answer but its single-sample output drifts. On our locked v1 + `fixed_50_v1` + 16k cap setup, this is the highest-leverage non-training move available.

**Why it should work on this distribution.**
- Run 06's two v1→v2 flips were one sampling-noise case (id=199) plus one ambiguous-gold case (id=48). SC kills the first directly (vote across N samples is noise-robust) and partially addresses the second (the vote reflects which equivalent form the model leans toward most often).
- The MCQ-cutoff cluster (Insight 2) is reasoning-bound — SC won't fix it, since no number of samples helps if every sample produces the same wrong reasoning. But it should improve the items where the model is on the boundary between confident-correct and lucky-wrong.

**Why it might not help much.**
- Locked sampling already uses temperature=0.6 (low-ish for a thinking model). Sample diversity may be limited; if all 8 samples produce nearly identical chains, SC degenerates to single-sample.
- High-agreement-wrong items (where 8/8 samples agree on a wrong answer) are unhelped by any voting scheme.

Decision rule for whether Phase 2 is worth the cost: §3.4.

---

## 3. Phase 2 — Self-Consistency

### 3.1 Method

Sample N completions per question with the locked sampling defaults (`temperature=0.6, top_p=0.95, top_k=20, repetition_penalty=1.0`). Extract `\boxed{...}` content from each completion. **Unweighted majority vote** on the extracted strings. Submit the winning vote as the final answer.

- N = 8 for the first run (see §3.4 cost table). Promote to N=16 only if N=8 shows positive returns and budget allows.
- **No beam search.** Plain stochastic sampling per locked defaults — beam search degenerates the diversity SC needs.
- **No weighted variants.** Wang et al. show unweighted majority beats weighted in most regimes; complexity isn't worth it.
- **Vote on the extracted answer string, not the full response.** Two responses with different reasoning that converge on the same `\boxed{42}` should both contribute to the "42" vote.
- **Tie-break:** if two answers tie in vote count, take the one that appeared first across the sample stream. Document the rule; ties should be rare with N=8 and a moderately-confident model.

### 3.2 Implementation

vLLM's `SamplingParams` supports `n=N` natively — no manual sampling loop required, the engine handles batched parallel sampling internally:

```python
SamplingParams(
    n=8,
    temperature=0.6, top_p=0.95, top_k=20, repetition_penalty=1.0,
    max_tokens=16384,
)
```

Each `RequestOutput.outputs` will contain N `CompletionOutput` objects. Loop over them, extract boxed, count votes, take argmax.

**Per-row JSONL schema additions:**
- `samples`: array of N objects, each `{response, gen_tokens, hit_token_cap, extracted_answer}`. Lets us audit individual samples post-hoc.
- `voted_answer`: the majority answer string.
- `agreement_rate`: `max_vote / N` (e.g. 0.625 if 5/8 agreed). Per-question confidence proxy.
- `tie_broken`: bool. Flag for the rare cases where the tie-break rule fired.

The deterministic-runner per-row fields (`prompt_version`, `slice_id`, etc.) all carry forward unchanged.

**Summary additions:** `n_samples`, `agreement_rate_p25 / p50 / p75`, `n_unanimous` (count of items where all N samples agreed), `n_tie_broken`.

### 3.3 New script

`scripts/run_vllm_sc.py` — separate file from `run_vllm_experiment.py`. Reasons:
- Different schema (samples array per row).
- Different cost profile (N× per question; needs distinct cost reporting).
- Same prompt registry, same slice loading, same chat-template path → import those from a shared module if both files start to overlap, but for now copy-and-adapt is fine.

Estimated effort: ~80 lines new, mostly the extraction + voting logic.

### 3.4 Cost and decision rule

| N | per-q cost | n=50 slice runtime | n=1126 full set |
|---|---|---|---|
| 1 (Run 05/06 baseline) | 13 s | 11 min, ~$0.13 | ~245 min, ~$2.80 |
| 8 | ~100 s* | ~85 min, ~$1.00 | ~32 hr, ~$22 |
| 16 | ~200 s* | ~170 min, ~$2.00 | ~64 hr, ~$45 |

*assumes near-linear N-scaling on Pod B; actual could be 0.6-0.9× depending on KV-cache pressure under N-way batching. Will measure on the n=50 run.

**Decision rule (Run 07-SC, N=8 on `fixed_50_v1`):**
- Overall accuracy ≥ Run 05 + 4 q (i.e. ≥ 78%) → **promote SC as part of submission pipeline.** Move to a confirmation run (n=100 or n=200), then full-set submission with SC.
- Overall ≥ Run 05 + 2 q AND agreement-rate distribution shows meaningful spread (p50 < 1.0) → **SC is helping but not enough at N=8.** Re-run at N=16 if budget allows. Otherwise treat as "modest improvement, accept" and move on.
- Overall < Run 05 + 2 q OR agreement-rate p50 = 1.0 (everything unanimous) → **SC isn't doing useful work on this distribution at locked sampling.** Don't promote; the next move is training (§4).

### 3.5 What to record per run

Standard metrics (Insights 1-7) plus:
- agreement-rate distribution
- breakdown of correct vs. incorrect items by agreement bucket (unanimous / strong / weak / split)
- per-item samples for any item that flipped vs. the v1 single-sample baseline (Run 05)

If N=8 reaches 75% on `fixed_50_v1` with median agreement 7/8, the model is "almost there" on most items and SC is the right last-mile lever. If N=8 lands at 71% with median 8/8 agreement, the floor is genuine model failure that no voting can fix → Phase 3 becomes urgent.

---

## 4. Phase 3 — Training

### 4.1 Reference recipe — Frugal-Thinking (Bounhar et al., MBZUAI-Paris, arXiv 2511.01937)

The cleanest published recipe targeting Qwen3-4B-Thinking-2507 specifically. Two-stage GRPO with binary verifiable reward on `\boxed{}` exact match:

| Hyperparameter | Frugal value |
|---|---|
| Algorithm | GRPO via veRL |
| Reward | binary on `\boxed{}` exact match |
| Group size G | 16 |
| Batch size | 128 |
| Learning rate | 1e-6 |
| Optimizer | AdamW |
| Warmup | 5% linear |
| Clip | asymmetric (0.8, 1.28) |
| Max completion | 16384 |
| Total compute (full scale) | ~250 H200-days |

**Key data point — Frugal Table 5 (AIME25 accuracy by token cap):**

| Model | 8k | 16k | 32k | 42k |
|---|---:|---:|---:|---:|
| Qwen3-4B-Thinking (base) | 13.33 | 46.67 | 73.33 | 73.33 |
| Frugal-Stage-2 | 53.33 | 70.00 | 70.00 | 70.00 |

Frugal-Stage-2 squeezes far more accuracy out of an 8k budget but plateaus earlier. For our setting at 16k on a CSE 151B distribution (easier than AIME25), both models are likely closer to saturation — the absolute gap matters less than the directional confirmation that GRPO on this base model produces real gains.

**Faithful replication is infeasible on a single 4090** (1-2 OOM under-resourced — 250 H200-days vs ~1 4090-day realistic budget).

### 4.2 Three realistic paths

**Path A — Heavy downscale.** G=4 or 8, QLoRA, possibly TRL or Unsloth instead of veRL. Keep the recipe shape (GRPO, binary boxed-match reward, locked sampling) but accept that we get a fraction of Frugal's training signal.
- **Pros:** straightforward; tooling exists (TRL, Unsloth).
- **Cons:** possibly under-trained; reward signal at G=4 is noisier than at G=16.

**Path B — Use Frugal-4B as init checkpoint.** Skip our own training entirely; fine-tune from `MBZUAI-Paris/Frugal-Thinking-4B` directly.
- **Pros:** highest expected accuracy ceiling — Frugal-Stage-2 hits 53% on AIME25 at 8k vs base Qwen3-4B-Thinking's 13%.
- **Cons:** **compliance question.** Competition rules require `Qwen/Qwen3-4B-Thinking-2507`; Frugal-4B is a fine-tuned derivative. Spirit-of-rule: base model + intrinsic methods. Letter-of-rule may exclude derivatives. **See §5.1 — Piazza question pending.**

**Path C — Distillation.** Use Frugal-4B as a teacher offline; generate reasoning traces on training problems; SFT our base Qwen3-4B-Thinking on those traces.
- **Pros:** gets some of Frugal's signal; less aggressive interpretation of the rules than Path B (we still ship the base model with our own training).
- **Cons:** SFT on R1-distill-style traces is a known trap if format isn't translated to Qwen3-Thinking's `<think>` convention (CLAUDE.md Anti-Patterns). Frugal-4B *is* a Qwen3-Thinking variant, so format should match — but verify.

### 4.3 Reward function — load-bearing detail

Per CLAUDE.md > Scoring (Judger): **any reward function calling `Judger.auto_judge` MUST construct `Judger(strict_extract=True)`.** Default `strict_extract=False` enables fallbacks (`"answer is X"`, `"C: explanation"`, last-number-in-text) that a policy will learn to farm — toxic as a training signal.

Other reward considerations:
- **Throughput:** `auto_judge` does ~9 sympy parses per item in the try-all `is_equal` loop. For G=16 × batch=128 = 2048 reward computations per step, that's ~18,000 sympy parses per step. **Route by question type** to skip the unnecessary methods (CLAUDE.md > Scoring); 5× speedup easily achievable.
- **Binary vs partial credit:** Frugal uses binary. Tempting to add partial-credit signals (e.g. correct boxed format but wrong value → small positive reward) but this opens new reward-hacking surfaces. Stay binary unless there's specific evidence partial credit helps for our regime.
- **Eval contamination:** training data sources matter. NuminaMath, MetaMathQA, and OpenMathInstruct include MATH train, which may overlap with the public/private competition split. **Prefer post-Aug 2025 sources** (Big-Math-RL-Verified, AIME/HMMT 2025) for the training set. Document the chosen source in the run log.

### 4.4 Data filtering

Per CLAUDE.md > Data & Analysis Discipline: the public dataset is LLM-synthesized and contains errors (questions 1, 8, 12.3 instructor-confirmed). Manipulating training data is explicitly allowed; **filtering bad examples counts as a method**.

For training data specifically:
- Drop questions where automated filters (e.g. checking gold against a strong solver) detect mismatches. Conservative threshold; over-filtering removes hard items the model needs to see.
- For RL: items where gold is genuinely wrong will reward the wrong answer; these are toxic for training. Worth a more aggressive filter pass than for evaluation.

### 4.5 Decision tree (depends on Phase 2 outcome)

| Phase 2 (SC) outcome | Phase 3 priority |
|---|---|
| SC promotes → ≥ 78% on n=50 | Optional. SC + v1 is the submission. Phase 3 only if budget permits another ~$50-100 of training experiments. |
| SC marginal → 72-77% on n=50 | Mid-priority. Try Path B first if Piazza answer permits; fall back to Path C. |
| SC flat or negative → ≤ 72% on n=50 | The next major lever. Path B (Frugal-4B init) is highest EV if compliance permits. |

### 4.6 What to record for a Phase 3 run

Beyond the standard run log: training step, loss curve, validation accuracy on `fixed_50_v1` at every Nth step (don't forget cost — checkpoint eval is its own compute), and a held-out check on a fresh `fixed_50_v2` slice at end-of-training to detect overfitting to `fixed_50_v1`.

---

## 5. Open Questions

### 5.1 Piazza compliance — Frugal-4B as init checkpoint

Competition requires `Qwen/Qwen3-4B-Thinking-2507`. `MBZUAI-Paris/Frugal-Thinking-4B` is a fine-tuned derivative of that exact model. **Question for course staff:** does fine-tuning *from* a public derivative checkpoint count as "using `Qwen/Qwen3-4B-Thinking-2507`" for the rules?

Two interpretations:
- **Spirit reading:** the rule is "no other architectures, no closed models" — derivatives of the same architecture trained with publicly described methods are in scope. Path B and Path C both OK.
- **Letter reading:** the rule names the exact model; only base weights or weights you trained yourself from base are allowed. Only Path A.

**Action:** post the question on Piazza before investing in Path B setup. Default-assume letter reading until staff answers; develop Path A in parallel as the safe fallback.

### 5.2 Eval contamination on training sources

Several popular open math datasets (NuminaMath, MetaMathQA, OpenMathInstruct) include MATH train, which may overlap with the competition's public/private split. Worth investigating overlap before Phase 3 commits to a training source.

### 5.3 CSV submission generator timing

Known Issue in `experiments.md`: no CSV submission generator exists yet. Not blocking the prompt sweep or Phase 2; **blocking before any private-set submission run.** Cheapest to write once, alongside whichever runner first crosses into private-set territory.

### 5.4 Per-item incremental save

Known Issue: the current vLLM runner writes per-row JSONL only after the full batch completes. Fine for n=50 (~11 min); risky for n=1126 (~245 min) — a mid-run crash loses everything. Schedule before any full-set run regardless of phase.

---

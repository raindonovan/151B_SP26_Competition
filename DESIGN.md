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

> **Updated 2026-05-06 per Piazza response from Ruijia Niu (May 5, 2026):** *"You can use any method to modify your model, as long as you start with the required Qwen3-4B-Thinking-2507 model."* This explicitly approves Path C (Qwen3-4B-Thinking-2507-derived teacher signal for distillation/SFT). Path A remains the primary plan; Path C is now an explicitly sanctioned alternative pursued in §7's v2 alternative-teacher experiment. Path B kept BLOCKED status pending its own decision (init-checkpoint-from-descendant is a stronger claim than data-source-from-descendant; revisit if needed). See §5.1 for the framing update.

**Path A — Heavy downscale (DEFAULT).** G=4 or 8, QLoRA, possibly TRL or Unsloth instead of veRL. Keep the recipe shape (GRPO, binary boxed-match reward, locked sampling) but accept that we get a fraction of Frugal's training signal.
- **Pros:** straightforward; tooling exists (TRL, Unsloth); compliance unambiguous (we train from base, no descendant checkpoints).
- **Cons:** possibly under-trained; reward signal at G=4 is noisier than at G=16.

**Path B — Use Frugal-4B as init checkpoint. (BLOCKED on Piazza compliance.)** Skip our own training entirely; fine-tune from `MBZUAI-Paris/Frugal-Thinking-4B` directly.
- **Pros:** highest expected accuracy ceiling — Frugal-Stage-2 hits 53% on AIME25 at 8k vs base Qwen3-4B-Thinking's 13%.
- **Cons:** **compliance.** Rules don't explicitly permit descendant init checkpoints. Operating under the conservative reading until clarified. Don't depend on this path being available. (The May 5 Piazza response in the §4.2 callout speaks to "modifying your model"; whether starting *from* a descendant counts as "starting with the required model" is a separate question that has not been asked. Path B remains BLOCKED until that clarification.)

**Path C — Distillation. APPROVED 2026-05-06 per Piazza (Ruijia Niu, May 5, 2026):** *"You can use any method to modify your model, as long as you start with the required Qwen3-4B-Thinking-2507 model."* Use a Qwen3-4B-Thinking-2507-derived teacher offline; generate reasoning traces on training problems; SFT our base Qwen3-4B-Thinking on those traces. Earlier "BLOCKED on Piazza compliance" framing is superseded.
- **Pros:** less aggressive than Path B (we still ship the base model with our own training); some teacher-derived signal.
- **Cons:** SFT on R1-distill-style traces is a known trap if format isn't translated to Qwen3-Thinking's `<think>` convention (CLAUDE.md Anti-Patterns). Note: Frugal-Thinking-4B is paper-only / not on HuggingFace as of 2026-05-06 — see §7 Open Questions for the verified Qwen3-4B-Thinking-2507-derivative shortlist used by the v2 alternative-teacher experiment.

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

### 5.1 Piazza compliance — descendant models as training inputs

**Updated 2026-05-06 per Piazza response from Ruijia Niu (May 5, 2026):** *"You can use any method to modify your model, as long as you start with the required Qwen3-4B-Thinking-2507 model."*

Resolution by path:

- **Path A (base + our own fine-tuning) — primary.** Always allowed; this is what §7 v1 (OpenR1 vs NuminaMath comparison) executes. Keep as the default plan; conservative framing preserved here.
- **Path C (Qwen3-Thinking-2507-derived teacher signal for distillation/SFT) — APPROVED.** Generating training data from a Qwen3-4B-Thinking-2507 descendant and SFT'ing our base on those traces is "modifying your model" while "starting with the required model." Pursued as the v2 alternative-teacher experiment in §7 Open Questions; deferred until v1 OpenR1/NuminaMath comparison establishes baseline.
- **Path B (init-from-descendant checkpoint) — STILL BLOCKED.** The May 5 response speaks to modification *of* the required model. Whether *starting from* a descendant satisfies "start with the required model" is a separate question that has not been asked. Don't depend on Path B being available without a follow-up Piazza clarification. Asymmetric upside if asked, but not on the critical path.

**Working assumption shift:** the prior "conservative reading adopted, Path A only" framing (2026-05-04) is partially superseded — Path C is now in scope. Path A remains primary because v1 establishes a baseline before any teacher signal enters the comparison; Path C joins the plan as a deliberately scoped v2 experiment, not as a replacement for Path A. The earlier two-readings framing (Conservative vs Liberal) is retired since the instructor response selected the relevant interpretation directly.

If a future Piazza response addresses Path B (init-from-descendant), revisit §4.2 Path B status and update.

### 5.2 Eval contamination on training sources

Several popular open math datasets (NuminaMath, MetaMathQA, OpenMathInstruct) include MATH train, which may overlap with the competition's public/private split. Worth investigating overlap before Phase 3 commits to a training source.

### 5.3 CSV submission generator timing

Known Issue in `experiments.md`: no CSV submission generator exists yet. Not blocking the prompt sweep or Phase 2; **blocking before any private-set submission run.** Cheapest to write once, alongside whichever runner first crosses into private-set territory.

### 5.4 Per-item incremental save

Known Issue: the current vLLM runner writes per-row JSONL only after the full batch completes. Fine for n=50 (~11 min); risky for n=1126 (~245 min) — a mid-run crash loses everything. Schedule before any full-set run regardless of phase.

---

## 6. Planned Work

### 6.1 Confidence-aware abstention / resampling on SC vote distribution

**Status:** Planned, dependent on Run 09-SC completion.

**Hypothesis:** SC's per-item agreement rate is a usable confidence signal. Items where 7-8/8 samples agree are likely correct; items where votes are scattered (1-2/8) are essentially the model guessing. We can use this signal to route items differently.

**Motivation:** Reflection/self-correction prompts have been shown to hurt thinking models (Huang et al. 2024, *"LLMs Cannot Self-Correct Reasoning Yet"*; −2 to +1 pp on math). Self-consistency vote distribution is the closest verification-style signal we can get without breaking the model's native thinking flow.

**Method:**

1. After Run 09-SC's JSONL is in, compute per-item agreement rate distribution.
2. Bucket items by agreement rate (e.g. 1.00, 0.875, 0.75, ..., 0.125).
3. Compute "if we had Kaggle gold for the public set, accuracy by bucket" — but since private is hidden, use a proxy: rerun on public set (1126 items) where we DO have gold.
4. Identify the agreement-rate cliff (point below which accuracy drops sharply).
5. For low-confidence items, try one of: (a) sample 8 more times, take majority of 16, (b) try a different prompt variant, (c) abstain (output an empty boxed which scores 0 — only useful if low-confidence items would have been wrong anyway).

**Cost:** ~$3 for one public-set SC eval to characterize the cliff. Ablations of the routing strategy add maybe $5-10.

**Success criterion:** Identify a routing rule that improves Kaggle public LB by ≥2 pp over plain v1+SC@N=8 (Run 09-SC's score, TBD).

**Open questions:**

- How does the cliff vary by question type? MCQ probably has a different shape than free-form.
- For low-confidence items, is "more samples" or "different prompt" the better resampling strategy? Probably needs A/B testing once we have agreement-rate data.
- Should we treat tie-broken items (multiple winners with same vote count) as low-confidence by default, regardless of vote count? The runner already logs `tie_broken: True` for these.

**Non-goal:** This is NOT reflection prompting (e.g. "now verify your work"). The thinking-model literature is clear that adding self-correction instructions to the prompt hurts accuracy. We use the vote distribution as a routing signal, not as feedback to the model.

---

## 7. QLoRA SFT Plan (NuminaMath, short-rationale)

### Goal

Train a QLoRA adapter on `Qwen/Qwen3-4B-Thinking-2507` that produces shorter, format-compliant
reasoning traces while preserving accuracy. Success criterion is Kaggle public LB score, not
token count alone.

Pass gate: Kaggle score within ±2 pp of Run 08-v2's 0.586 AND avg gen tokens drops by ≥30%.
Strong pass: Kaggle score ≥ 0.60 AND avg gen tokens drops by ≥50%.
Fail: Kaggle score drops > 3 pp OR cutoff rate increases.

Token reduction is a means, not an end. We're not against reasoning — there is no
score benefit to suppressing reasoning, only to preserving accuracy while reducing
wall-time and cutoff rate. Format choice and training data selection (next
subsections) reflect this hierarchy: Kaggle score is primary, token reduction is
secondary.

### Compliance frame

Required model is `Qwen/Qwen3-4B-Thinking-2507`. The competition allows training with public
data via SFT/QLoRA/RL but forbids "directly using open-source models or data without
modifications."

Two training corpora are used in a controlled comparison:

(1) **OpenR1-Math-220k** — verified subset of NuminaMath problems with reasoning traces
generated by DeepSeek-R1, where each row passed both Math-Verify and an LLM-judge against
ground truth. Apache-2.0 license. ~94k rows. Tests the "reasoning-trace imitation" hypothesis.

(2) **NuminaMath-1.5** — same underlying problem corpus, but using NuminaMath's native
concise-solution format ("Solution: ... therefore 42"). Tests the "concise-solution
imitation" hypothesis.

Both run at matched data size, matched QLoRA config, matched eval slice. The control
isolates whether Qwen3 benefits more from reasoning-trace teacher signal or from
concise-solution teacher signal. Both corpora require format transformation into our
competition-style prompt/answer schema before training, satisfying the no-direct-use clause.

Excluded by design:
- Frugal-Thinking-4B as teacher signal: instructor-approved per Piazza (Ruijia Niu,
  May 5, 2026: *"You can use any method to modify your model, as long as you start with
  the required Qwen3-4B-Thinking-2507 model."*) — see §4.2 Path C and §5.1. However,
  HuggingFace search confirms Frugal-Thinking-4B does NOT appear on Hub as of
  2026-05-06 — it may be a paper-only reference or use a different name. The
  "alternative teacher signal" v2 experiment substitutes a verified
  Qwen3-4B-Thinking-2507-derived candidate (see Open Questions for shortlist).
- Public-set training data: deferred until audit pass (~10% suspected gold error rate;
  instructor-confirmed the public set is LLM-synthesized with imperfect filtering).
  Private set is confirmed clean per Piazza response from Ruijia Niu, May 5, 2026
  (*"We did not synthesize the private dataset, as they are already carefully filtered
  and verified."*). For SFT v1, we use OpenR1 + NuminaMath as primary; public set may
  be incorporated as supplementary training data after audit.

### What SFT changes (and what it doesn't)

The Qwen3-4B-Thinking-2507 chat template auto-injects `<think>` regardless of training.
SFT cannot remove this template behavior. What SFT CAN change is the model's behavior
INSIDE the think block — making it produce shorter content, or even empty content
(immediate `</think>`), before committing to an answer.

This means "answer-only" SFT targets don't produce true 0-token responses; they produce
`<think></think>\boxed{X}` which is ~5-10 token overhead.

The training target length we choose (via filter and template wrapping) directly
determines what the model learns to produce. We're choosing preserved-reasoning targets
over the aggressive answer-only path because:

- Math accuracy depends on intermediate reasoning steps
- Patrick's "64 token" approach is unverified at competition-relevant accuracy
- A model with preserved reasoning is more robust to harder problems than one trained to
  skip reasoning entirely
- Token count doesn't directly affect Kaggle score; it affects wall time, compute cost,
  and cutoff rate (12.6% in Run 08-v2 baseline). The optimization target is "minimize
  cutoffs while preserving accuracy."

### Stage 1 — Pre-training measurement (mandatory)

Before any training data filter is finalized, characterize the actual length distributions
to choose informed thresholds:

1. **OpenR1 trace length distribution** — tokenize all OpenR1 verified single-answer rows
   with the Qwen3 tokenizer. Report mean, median, p25/p50/p75/p90/p95, max.

2. **Qwen baseline output length distribution** — extract `gen_tokens` from existing
   Run 09-SC outputs (943 items, 8 samples each). Same statistics.

3. **NuminaMath solution length distribution** — same statistics for filtered NuminaMath
   single-answer rows.

4. **Cross-distribution comparison** — if OpenR1 traces have median ≥ Qwen baseline
   median, the "shorter teacher" assumption is wrong and the filter must be tighter
   than "arbitrary 2000-12000." If OpenR1 median is meaningfully shorter, default
   candidate filter ranges (1000-6000 or 2000-8000) become viable; final choice from
   data.

Filter range selection happens after this measurement, not before. Document the chosen
range and why.

### Tooling

Primary: **Unsloth** + `trl.SFTTrainer`. Confirmed support for `unsloth/Qwen3-4B-Thinking-2507`
via official notebook. Key advantages: ~2× training speed, ~30% lower VRAM, supported
`qwen3-thinking` chat template, simple `save_pretrained_merged` for vLLM deployment.

Fallback: HF Transformers + PEFT + bitsandbytes if Unsloth's release breaks against our
pinned torch/transformers stack.

Avoided: Axolotl (adds YAML abstraction layer; not needed for fast iteration).

### Critical model behavior facts

Three Qwen3-4B-Thinking-2507-specific findings shape the implementation:

1. **Thinking-only mode.** This model supports only thinking mode. `enable_thinking=False`
   appears in some Unsloth notebooks but should not be used here — it would conflict with
   the model's required behavior. The default chat template auto-includes `<think>`, so
   outputs may begin with content and only later close with `</think>`. Any extraction logic
   that assumes a literal `<think>` opening tag is wrong.

2. **Long thinking traces are expected behavior, not a bug.** Qwen3-Thinking-2507's model card
   notes increased thinking length compared to predecessors. This is the source of our cutoff
   problem. SFT must teach concise reasoning, not eliminate reasoning.

3. **Sampling settings differ from Instruct.** For this thinking model:
   - `temperature = 0.6`, `top_p = 0.95`, `top_k = 20`, `min_p = 0.0`
   - These match what we already use in `scripts/run_vllm_experiment.py` SAMPLING dict.
   - Do not copy Instruct settings (`temp=0.7, top_p=0.8`).

### Code organization

New `training/` directory parallel to existing `scripts/`:

```
training/
prepare_openr1_sft.py          # OpenR1-Math-220k ingestion, filtering, format conversion
prepare_numina_sft.py          # NuminaMath-1.5 ingestion, filtering, format conversion
prepare_frugal_sft.py          # Frugal-Thinking-4B trace generation (inference + format)
train_qwen3_qlora.py           # SFT training loop (Unsloth + SFTTrainer)
merge_lora_adapter.py          # adapter -> merged BF16 checkpoint for vLLM
eval_adapter_public.py         # local public-set eval w/ Judger + Kaggle-approximation
checkpoints/                   # adapters + merged models (gitignored)
```

Training data lives under the existing top-level `data/` directory to match repo
convention (`data/public.jsonl`, `data/slices/...`):

```
data/sft/                      # generated SFT training datasets (gitignored)
  openr1_v1_1k.jsonl
  numina_concise_v1_1k.jsonl
  frugal_traces_v1_1k.jsonl
  ...
```

Inference uses existing `scripts/run_vllm_experiment.py` with `--model` pointing at the
merged checkpoint path.

### Training data: format and filtering

Output schema (each row, JSONL):

```json
{
  "messages": [
    {"role": "system", "content": "You are an expert mathematician..."},
    {"role": "user", "content": "<question text matching v1-baseline format>"},
    {"role": "assistant", "content": "<short reasoning>\n\\boxed{<answer>}"}
  ]
}
```

For OpenR1 (reasoning-trace arm):

1. Row has at least one `correctness_math_verify=True`
2. Pick the first such generation for the assistant content
3. Tokenize with the Qwen3 tokenizer; keep within the filter range chosen from Stage 1
   measurement (default candidates: 1000-6000 or 2000-8000)
4. Regex-drop multi-part prompts: `\(a\)`, `\(i\)`, "Part 1", "prove that" (single-answer
   only)
5. Sympy-parse the last `\boxed{}` from the generation; drop parse failures
6. Verify the parsed answer string-matches the row's `answer` field
7. English-only via fasttext lid.176
8. MinHash-LSH dedup against MATH-test, AIME 2024-2025, HMMT Feb 2025 (threshold 0.7)

For NuminaMath (concise-solution arm):

1. Single-answer problems only (drop multi-part)
2. Solution length appropriate for "concise solution" format — tokenize and select to
   match OpenR1 arm size at the same scale (1k v1, 8k scale)
3. Final boxed answer parseable
4. English-only
5. Same dedup pass as OpenR1
6. Drop `synthetic: True` rows. NuminaMath-1.5 contains LLM-generated problems; the
   competition's public set has the same provenance with confirmed errors. Training on
   synthetic data risks distilling toward the same hallucination patterns. Human-written
   olympiad problems only.

Both arms produce JSONL files with matched schema:
- `data/sft/openr1_v1_1k.jsonl`
- `data/sft/numina_concise_v1_1k.jsonl`
- (later) `data/sft/openr1_v1_8k.jsonl`, `data/sft/numina_concise_v1_8k.jsonl`

Multi-answer training data is a v2 problem deferred until single-answer training is validated.

### Training target format vs auto-injected `<think>` token

The `qwen3-thinking` chat template auto-injects `<think>` immediately after
`<|im_start|>assistant`. Verified empirically during environment setup; a
trivial input tokenizes to:

```
<|im_start|>user
What is 2+2?<|im_end|>
<|im_start|>assistant
<think>
```

The model is forced into thinking mode by the template itself, before any
assistant content is added. This shapes how SFT examples must format the
assistant turn.

Two candidate formats:

**Option 1 — Include `<think>...</think>` explicitly in training targets.**

Format: `<think>brief reasoning</think>\boxed{answer}`

Pro: model learns to close `<think>` quickly with concise content; full control
over reasoning structure.
Con: risk of double `<think>` tokens if SFTTrainer's text-field formatting
collides with the template's auto-injection.

**Option 2 — Rely on the template's auto-injected `<think>` opener.**

Format: `brief reasoning</think>\boxed{answer}` (assistant content starts after
the auto-injected opener)

Pro: no double-token risk; matches what the template produces by default.
Con: harder to verify what the model actually sees during training without
inspecting tokenized sequences directly.

**Resolution: Option 2 (rely on the template's auto-injected opener).** Validate before
training with this concrete check on one rendered example:

```python
print(tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False))
```

If the rendered output shows `<|im_start|>assistant\n<think>\n<think>\n...`, the assistant
content has a redundant leading `<think>`. Drop it. OpenR1 traces from R1 already contain
`<think>...</think>` — pass through unchanged unless the duplication appears.

This is a load-bearing pre-flight check, not optional. R1's chat template conventions are
similar but not identical to Qwen3-Thinking's, and template malformation would silently
corrupt training.

### Training data: format transformation choice

**Decision: preserved reasoning, NOT answer-only.** Justification:

1. **Inference distribution match.** Qwen3-Thinking's chat template auto-prepends
   `<think>` to the assistant prefix at inference time. SFT on answer-only targets
   creates a distribution mismatch — the template injects `<think>` but weights have
   learned to emit `\boxed{}` immediately, producing malformed traces.

2. **Unsloth's Qwen3 fine-tuning guidance: keep ≥75% reasoning in mixed datasets to
   avoid catastrophic loss of reasoning capability.**

3. **Frugal-Thinking-4B (verified at `MBZUAI-Paris/Frugal-Thinking-4B`; gated;
   Apache 2.0; Qwen3-4B-Thinking-2507 base) preserved the `<think>` block entirely.**
   Its token reduction came from data curation and reward shaping, not format collapse.

4. **Naive truncation of CoT degrades accuracy on math reasoning tasks (well-documented
   in CoT-pruning literature).** Entropy-aware or verification-aware pruning methods
   exist but are their own research projects, out of scope for v1.

The data filter (chosen from Stage 1) produces shorter outputs by trimming the long
tail. Format is preserved; length distribution shifts.

### Training hyperparameters

v2 (2026-05-07) values shown below; v1 used `r=16`, `alpha=32` (=2r), `warmup_ratio=0.03`, `save_steps=250`, `max_seq_length=4096`. The five changes target the v1 truncation post-mortem (max_seq_length), capacity headroom for 8x training data (r), Schulman's `alpha == r` convention (alpha comment only — value unchanged), more warmup steps over a ~1000-step run, and reduced disk thrash from frequent checkpointing.

QLoRA configuration:

```python
load_in_4bit=True
quantization: nf4
bf16 compute dtype
double quantization: enabled
```

LoRA configuration:

```python
r = 32                            # community default; r=32 if r=16 underfit
lora_alpha = 32                   # Schulman default: alpha == r
lora_dropout = 0                  # Unsloth-recommended
bias = "none"
target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                  "gate_proj", "up_proj", "down_proj"]
use_gradient_checkpointing = False        # 2026-05-08 throughput investigation: Unsloth's CPU-offload variant was the single-core-pinned / 5%-GPU-util bottleneck. Disabled. SFTConfig.gradient_checkpointing=False matches at the trainer layer.
random_state = 3407
```

Training arguments:

```python
per_device_train_batch_size = 2          # 2026-05-09 throughput investigation
gradient_accumulation_steps = 4          # effective batch 8 preserved
warmup_ratio = 0.05
num_train_epochs = 1                     # 1 epoch v1 (conservative — see note below)
learning_rate = 2e-4
optim = "adamw_8bit"
weight_decay = 0.01                      # PRESERVED — standard AdamW regularization
lr_scheduler_type = "cosine"
bf16 = True
gradient_checkpointing = False           # belt-and-suspenders against use_gradient_checkpointing=False at LoRA-attach
packing = False
save_strategy = "steps"
save_steps = 200
save_total_limit = 4                     # keep more checkpoints for sweep
seed = 3407
max_seq_length = 8192
assistant_only_loss = False              # 2026-05-08 reframe — Unsloth silently ignores True; v2 trains full-sequence (see "Loss target" paragraph below)
```

Rationale for batch=2 + grad_accum=4 (effective batch 8 preserved):
- v1 used batch=1 + grad_accum=8 with Unsloth's CPU-offload gradient checkpointing, ran at ~25 sec/step (5% GPU util, single-core pinned).
- 2026-05-09 throughput investigation found the offload-checkpointing was the dominant bottleneck. Disabling it dropped step time to ~16 sec/step.
- batch=4 + grad_accum=2 reached 87.8% peak VRAM in a 20-step smoke and OOM'd at step 11 of a 100-step extension when an adversarial batch (multiple long examples in one microbatch) pushed allocation past the 24 GiB ceiling.
- batch=2 + grad_accum=4 (current setting) held 81.5% peak VRAM with zero drift across both halves of a 100-step smoke; full-epoch v2 NuminaMath ran clean at 8.18 sec/step, 2h 16m wall-clock.
- See [`experiments.md`](experiments.md) > External Review Insights > 2026-05-09 entry for the full investigation.

1 epoch is the v1 default. Save adapters every 200 steps, evaluate each checkpoint on
the 200-question slice, and only commit to additional epochs if step-N+200 checkpoints
still show monotonic improvement at end of epoch 1. This is not domain adaptation —
we're shifting reasoning style — so overtraining risks imitating teacher-specific
verbosity tics at the expense of Qwen3's native thinking quality.

**Loss target — full-sequence (per 2026-05-08 reframe).** Setting `assistant_only_loss=True` on `SFTConfig` is silently ignored under Unsloth's compiled SFTTrainer override (`unsloth_compiled_cache/UnslothSFTTrainer.py:1041-1300` ships its own `_prepare_dataset` that bypasses TRL's `apply_chat_template(return_assistant_tokens_mask=True)` path; see [`experiments.md`](experiments.md) > External Review Insights > 2026-05-08 entry for the full investigation trace). v1 trained on full-sequence cross-entropy despite the flag being set to True; v2 sets the flag to `False` to align config with what actually happens. Full-sequence loss is supported as appropriate for our regime by Huerta-Enochian & Lee 2024 (no statistically significant effect of prompt loss weight on long-completion data, R_g ≥ 1; v2 NuminaMath has R_g ≈ 1.5-3.0) and Sky-T1 / NovaSky 2025 (reasoning-trace SFT is highly sensitive to *structural* perturbations of training traces and remarkably insensitive to content / per-token signal). See [`papers.md`](papers.md) for citations. v3 is pre-committed as the assistant-only ablation if v2 succeeds; achieving genuine assistant-only loss under Unsloth requires either bypassing `_prepare_dataset` via `dataset_kwargs={"skip_prepare_dataset": True}` plus pre-tokenizing the dataset with `apply_chat_template(return_assistant_tokens_mask=True)`, or switching off Unsloth entirely.

### Diagnostic: assistant-only eval-loss metric

Under full-sequence loss, the standard `train/loss` reported to wandb is computed over system + user + separator + assistant tokens. The system+user content is identical or near-identical across rows in our schema and trivially memorized — driving `train/loss` down without meaningful signal about assistant-content learning. To monitor genuine learning progress, [`training/train_qwen3_qlora.py`](training/train_qwen3_qlora.py) ships a custom `AssistantOnlyEvalLossCallback` that:

- Holds out the **last 8 rows** of the loaded JSONL as a deterministic eval batch (training rows: 8000 → 7992; below sampling noise).
- Constructs a per-token mask via last-occurrence token-id matching of `<|im_start|>assistant\n`, marking the assistant span (including the auto-injected `<think>\n` opener) as graded and everything before as `-100`. Token-id matching avoids reliance on `{% generation %}` markers which are absent from unsloth's `qwen3-thinking` template and is BPE-stable across Unicode/normalization edge cases.
- At every `save_steps` boundary (5 firings per arm at v2's `save_steps=200`, ~1000 total steps), runs a forward pass on the held-out batch under `torch.no_grad()` and `model.eval()`, computes token-weighted cross-entropy on the masked positions, and logs as `eval/assistant_only_loss` to wandb (and stdout if wandb isn't active).

A **hard pre-flight gate** (Pre-flight check 3 in `train_qwen3_qlora.py`) computes the metric against the untrained-LoRA model and aborts before any training compute if the value is not finite or falls outside the sanity range `[0.5, 5.0]` nats. This catches mask-construction bugs, tokenization edge cases, and base-model dtype mismatches at smoke-test time. The gate also prints a human-readable masked/graded boundary decode for one example so the span can be visually verified.

Interpretation: this metric is the diagnostic ceiling for "is the model actually learning the assistant-content distribution?" — distinct from `train/loss` which is dominated by easy prompt-prediction. Under healthy v2 training we expect both to descend, but `eval/assistant_only_loss` is the truer signal of reasoning-trace fit. The metric is held-out (rows excluded from training), so it doesn't trend monotonically with training loss the way an in-set metric would.

### Chat template and tokenization

Use Unsloth's `qwen3-thinking` chat template:

```python
from unsloth.chat_templates import get_chat_template
tokenizer = get_chat_template(tokenizer, chat_template="qwen3-thinking")
```

Apply via `tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)`
during training data preprocessing. Do NOT pass `enable_thinking=False`; this model is
thinking-only.

### Inference: merge over LoRA serving

vLLM 0.8.5 has LoRA support but is finicky for Qwen3 architecture. The competition pipeline
is too important to depend on a finicky adapter-serving path.

Decision: **train LoRA adapter, save it, then merge into a BF16 checkpoint** before vLLM
inference. Disk cost (~8 GB per merged model) is acceptable.

Save path:

```python
model.save_pretrained_merged(
    "qwen3-4b-thinking-merged",
    tokenizer,
    save_method="merged_16bit",  # NOT merged_4bit — vLLM can't load 4bit-saved natively
)
```

Verify presence in the merged directory: `config.json`, `generation_config.json`,
`tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`,
`model-0000X-of-0000Y.safetensors`, `model.safetensors.index.json`.

**Primary inference invocation (single-pod, in-process):** existing
`scripts/run_vllm_experiment.py` with `--model` argument pointing at the merged checkpoint
directory. All other vLLM defaults (sampling, `max_model_len`, etc.) remain unchanged. No
`--enable-lora` flag — the merged checkpoint is a self-contained model. No code changes
to the runner needed.

**Optional: separate inference pod via HF Hub.** Currently both training and inference
run on Pod B, so the merged model lives on local disk and the runner loads it directly.
If we later move inference to a separate pod (e.g., for cost reasons after training),
push to a private HF repo (~8 GB, ~70s on 1 Gbps via LFS):

```bash
hf auth login                     # paste write token
hf repo create your-org/qwen3-4b-thinking-ft --private
hf upload your-org/qwen3-4b-thinking-ft ./qwen3-4b-thinking-merged \
    --repo-type=model --commit-message "QLoRA merged 16bit"
```

Then either point `run_vllm_experiment.py --model your-org/qwen3-4b-thinking-ft` at the
Hub repo, or launch an HTTP server via `vllm serve` if HTTP-based serving is desired:

```bash
HF_TOKEN=hf_xxx vllm serve your-org/qwen3-4b-thinking-ft \
    --dtype bfloat16 \
    --max-model-len 24576 \
    --gpu-memory-utilization 0.92 \
    --enable-prefix-caching \
    --served-model-name qwen3-thinking-ft
```

vLLM 0.8.5 has known LoRA-serving issues with Qwen3 (vllm #28186, #18120, #38085).
Merging avoids all of these. If the merged path also fails, upgrading vLLM is the move,
not architectural workarounds.

### Evaluation

#### Evaluation slices

For checkpoint ranking we use a 200-question stratified slice (within difficulty/topic
buckets, fixed seed). Statistical motivation:

- 50-question slice CI at observed accuracy ~0.7: ±13pp — only detects Δ ≥ 18pp reliably
- 200-question slice CI at same accuracy: ±6pp — detects Δ ≥ 8pp

`data/slices/fixed_50_v1` stays as the prompt A/B slice (calibrated mental priors). New
slice `data/slices/fixed_200_v1` for checkpoint ranking. Full 1126 (cleaned) only for
the final 2-3 finalists.

#### Multi-signal eval

Local eval uses multiple correctness signals because no single grader matches Kaggle
perfectly:

1. **Existing local Judger** (`judger.py`) — the framework we've used since Run 03
2. **math_verify-based Kaggle approximation** — last-boxed string match with sympy fallback
3. **Boxed answer rate** — fraction of items with extractable final boxed
4. **Parse failure rate** — fraction where extraction failed entirely
5. **Cutoff rate** — fraction hitting `max_new_tokens`

If Judger and math_verify disagree, neither is automatically right. Inspect examples
manually. Kaggle submission is the ultimate arbiter — reserve for after local gates pass.

**Caveat:** math_verify is also used in OpenR1's filtering. Using it as both
training-data filter AND eval grader creates correlated blindspots. Track Judger ↔
math_verify agreement rate as a calibration signal; if they diverge sharply on
trained-vs-untrained outputs, that's diagnostic.

#### Per-item logged metrics (Tier 1, mandatory for SFT runs)

For every item in any SFT-related eval run, log:

- `correct_judger` (existing) — local Judger correctness
- `correct_kaggle_approx` (NEW) — math_verify-based grader correctness
- `sympy_disagreement` (NEW) — True if `correct_judger != correct_kaggle_approx`
- `has_think_open` (NEW) — True if `<think>` appears in response
- `has_think_close` (NEW) — True if `</think>` appears in response
- `think_tokens` (NEW) — token count between `<think>` and `</think>`, or 0 if missing
- `post_think_tokens` (NEW) — token count after `</think>`
- `boxed_at_end` (NEW) — True if last `\boxed{}` appears within final 100 tokens
- `gen_tokens` (existing) — total response tokens
- `hit_token_cap` (existing) — boolean cutoff flag

#### Per-run aggregate metrics (Tier 1, mandatory for SFT runs)

For every SFT eval run summary:

- `judger_kaggle_approx_agreement_rate` (NEW) — fraction where both graders agree
- `malformed_think_rate` (NEW) — fraction with open-without-close or close-without-open
- `avg_gen_tokens`, `median_gen_tokens`, `p25/p50/p75/p95` (was just `avg`)
- `cutoff_count`, `cutoff_rate` (existing)
- **Length-by-correctness buckets:**
  - `avg_tokens_correct` — average `gen_tokens` on items judged correct
  - `avg_tokens_wrong` — average `gen_tokens` on items judged wrong
  - `cutoff_rate_correct` vs `cutoff_rate_wrong`
  - `boxed_rate_correct` vs `boxed_rate_wrong`
- **Adapter metadata** (NEW):
  - `base_model`, `adapter_path`, `lora_rank`, `train_steps_completed`
  - `train_data_source` (openr1 / numina_concise / etc.), `train_data_size`,
    `train_epochs_completed`
  - `train_final_loss`, `train_eval_loss_per_epoch`

#### Checkpoint selection criterion

For comparing adapter checkpoints, the priority order is strict:

1. **Maximum Kaggle-approximated accuracy** on `fixed_200_v1`
2. Among checkpoints within 1pp of max accuracy: **minimum avg `gen_tokens`**
3. Among checkpoints with similar score+length: **lowest cutoff rate**

A 0.62 + 5000-token checkpoint beats a 0.61 + 1500-token checkpoint. Token reduction is
value-add only when accuracy is preserved.

#### Submission gate

Must all pass before burning a Kaggle slot:

- Public eval runs end-to-end without crashes
- CSV validates: 943 rows, IDs sequential 0-942, all responses non-empty
- Boxed answer rate ≥ 95%
- No catastrophic public-set regression (≥ 50% accuracy maintained)

### Open questions deferred to v2

- Multi-answer training data format (single-answer-only in v1)
- LoRA rank scaling (r=16 → r=32 if underfit)
- Different rationale-length targets (e.g., 200 vs 500 tokens)
- Combination with N=8 SC at inference (does SFT'd model benefit equally?)
- **Multi-epoch training** — extend to 2-3 epochs only if v1 1-epoch checkpoints show
  monotonic improvement at end of epoch 1. Track learning curve to detect overfitting
  (rising eval loss while train loss falls).
- **Multi-teacher signal blending (v2)** — once v1 establishes which teacher signal
  wins, explore mixing teachers (e.g., 50/50 OpenR1+Frugal traces). Defer until v1
  ranking is clear.
- **Public-set audit** — clean the public set's ~10% suspected gold errors via 3-LLM
  consensus + human review. Cleaned set becomes a richer eval slice. Doesn't gate v1
  SFT work.

### Risks and mitigations

- **Unsloth incompatibility with pinned stack:** fall back to HF PEFT.
- **NuminaMath filtering removes too many items:** start with stricter filter, relax if <5k
  examples remain after filtering.
- **Training loss doesn't decrease in smoke test:** check chat template, dataset format,
  learning rate before scaling up.
- **Trained model produces malformed outputs:** check whether the `<think>` block is being
  preserved vs removed during training; this model requires it.
- **Disk fills from merged checkpoint accumulation:** keep only the latest merged model on
  Pod B, archive prior ones to HF Hub if needed for comparison runs.

---

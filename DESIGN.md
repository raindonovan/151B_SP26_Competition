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

We will test 5 prompt pairs total, including the current baseline.

#### Policy 0: Current Baseline

Purpose:

```text
Establish the baseline on the fixed 50-question slice.
```

This uses the repo’s current MCQ and free-response prompts.

---

#### Policy 1: Careful Reasoning

Purpose:

```text
Encourage careful step-by-step reasoning and verification.
```

General idea:

```text
Solve accurately.
Reason step by step.
Check work.
Final answer inside \boxed{}.
```

MCQ version should emphasize comparing the solved result against the provided options.

Free-response version should emphasize giving the exact answer unless an approximation is requested.

---

#### Policy 2: Brief but Sufficient Reasoning

Purpose:

```text
Test whether shorter reasoning improves efficiency and possibly accuracy.
```

General idea:

```text
Use brief but sufficient reasoning.
Avoid unnecessary verbosity.
Still put final answer inside \boxed{}.
```

This is motivated by the possibility that very long reasoning can waste tokens, increase runtime, or introduce mistakes.

---

#### Policy 3: Anti-Error / Checking Prompt

Purpose:

```text
Reduce common math-model errors.
```

General idea:

```text
Check arithmetic.
Check units.
Check edge cases.
Check whether the problem asks for an exact value, expression, or choice.
```

For MCQ, the model should verify that the selected option matches the computed result.

For free-response, the model should avoid unnecessary decimal approximations.

---

#### Policy 4: MCQ-Elimination + Exact Free-Response

Purpose:

```text
Use more specialized guidance for each question type.
```

MCQ guidance:

```text
Solve the problem.
Compare choices.
Eliminate wrong choices if useful.
Return only the final option letter inside \boxed{}.
```

Free-response guidance:

```text
Solve the problem.
Give the exact mathematical answer.
Use \boxed{} for final answer.
```

This policy tests whether stronger question-type specialization improves performance.

---

### 1.10 First-Round Experiment Plan

The first round should use:

```text
5 prompt policies
50 fixed validation questions
same generation parameters for all runs
same answer parser for all runs
```

Run table:

| Run | Prompt Policy | Questions | Purpose |
|---|---:|---:|---|
| 0 | Current baseline | 50 | Establish baseline |
| 1 | Careful reasoning | 50 | Test careful verification |
| 2 | Brief reasoning | 50 | Test shorter reasoning |
| 3 | Anti-error/checking | 50 | Test explicit error prevention |
| 4 | MCQ-elimination + exact free-response | 50 | Test specialized wording |

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

During prompt comparisons, do not change:

```text
model
dataset slice
question order
generation parameters
max_new_tokens
answer parser
evaluation script
runtime environment
```

Also:

```text
Do not change the model away from Qwen/Qwen3-4B-Thinking-2507.
Do not rewrite the notebook architecture.
Do not modify model loading during prompt experiments.
Do not change the answer parser unless parser behavior is the explicit experiment.
vLLM is allowed but must run in the isolated Pod B environment — do not install or import
vLLM in Pod A's .venv. See SETUP.md for the two-environment strategy.
```

Prompt changes should be isolated to the prompt-construction cell/function whenever possible.

---

### 1.17 Notes for Coding Agents

Coding agents should follow these rules:

```text
inspect before editing
make minimal changes
report exact files/cells changed
do not install packages unless explicitly requested
do not use vLLM in Pod A (Transformers environment) — vLLM belongs in Pod B only
do not change the model
do not change generation parameters during prompt trials
do not overwrite previous run outputs
```

For prompt changes, the expected target is usually:

```text
starter_code_cse151b_comp.ipynb
prompt-construction cell/function
```

The function interface should remain:

```python
def build_prompt(question: str, options: Optional[list]) -> tuple[str, str]:
    ...
```

unless the generation code is intentionally updated.

---

### 1.18 Summary of Immediate Next Steps

1. Create or update `design.md` with this prompt-engineering plan.
2. Create a fixed 50-question validation slice.
3. Rerun the current baseline on that exact 50-question slice.
4. Save baseline outputs under a unique run ID.
5. Test 4 new prompt policies on the same 50-question slice.
6. Compare overall, MCQ, and free-response accuracy.
7. Promote the top 1-2 policies to a 100-question or 200-question run.
8. Run ablations only after identifying a promising policy.

---

## 2. Future Sections

These sections can be expanded later.

### 2.1 Inference Pipeline

To document:

```text
model loading
quantization
Transformers generation path
batching strategy
runtime constraints
GPU memory constraints
```

### 2.2 Evaluation and Answer Parsing

To document:

```text
boxed-answer extraction
normalization rules
MCQ answer handling
free-response answer handling
parse-failure handling
```

### 2.3 Runtime and Compute Constraints

To document:

```text
expected runtime per question
max_new_tokens tradeoffs
GPU availability
memory limits
cost of larger validation runs
```

### 2.4 Competition Rules

To document:

```text
required model
allowed techniques
disallowed techniques
submission format
fairness constraints
```

### 2.5 Future Methods

Possible later methods:

```text
supervised fine-tuning
reinforcement learning
self-consistency
answer re-ranking
tool-assisted verification, if allowed
```

# CSE 151B — Competition Reference

## Overview
Improve mathematical reasoning of `Qwen/Qwen3-4B-Thinking-2507` using only model-intrinsic methods. No external APIs or tool-augmented generation permitted at inference time.

Evaluated on **unified accuracy**: total correct / total questions, equally weighted across all benchmarks. Problems span high-school to graduate level math.

---

## Allowed Methods
1. **Prompt engineering** — chain-of-thought, few-shot, self-consistency, progressive-hint prompting, etc.
2. **Supervised fine-tuning** — LoRA, QLoRA, or full fine-tuning on any publicly available data
3. **Reinforcement learning** — GRPO, DPO, outcome-based reward modeling, etc.

**Not permitted:** external model calls, API access, code interpreters, calculators at inference time.

---

## Model Constraint
- **Required model:** `Qwen/Qwen3-4B-Thinking-2507`
- May be further trained with the above methods
- No alternative models allowed for final response generation

---

## Dataset Format
Problems are in JSONL format (one JSON object per line).

### Data Fields
| Field | Description |
|---|---|
| `id` | Unique integer identifier |
| `question` | Problem statement in LaTeX. Free-form uses `[ANS]` placeholders |
| `answer` | List of strings (free-form) or single capital letter (MCQ) |
| `options` | (MCQ only) List of candidate answer choices in LaTeX |

### Question Types

**Free-form (single answer):**
```json
{"question": "...$\\frac{1}{(-8)^{-3}}=$ [ANS]...", "answer": ["-512"], "id": 4}
```

**Free-form (multiple answers):**
```json
{"question": "...f(3)= [ANS]\\n(b) f(-3)= [ANS]...", "answer": ["41", "35", "16"], "id": 2}
```

**Multiple-choice:**
```json
{"question": "...", "options": ["...", "..."], "answer": "C", "id": 1}
```

### Data Splits
- **Public set:** Ground truth provided — use for development and validation
- **Private set:** No answers — used for leaderboard and final ranking (~30% revealed during competition)

---

## Scoring
- **Metric:** Unified accuracy = correct / total, equal weight per question
- **Free-form:** ALL sub-answers must be correct for a question to count
- **MCQ:** Selected letter must match ground truth exactly
- Final ranking uses full private test set revealed after deadline

---

## Submission Format
CSV file with predictions for every problem in `private.jsonl`.

```
id,response
0,"[full reasoning trace] ... The answer is \boxed{42}"
1,"[full reasoning trace] ... \boxed{580, 660, 80}"
```

### Rules
- `response` must be the **complete raw model output** including all chain-of-thought/thinking tokens
- Properly quote and escape the response field (standard CSV double-quoting, inner quotes as `""`)
- Every `id` in `private.jsonl` must have a row
- Final answer is extracted from the response trace during evaluation

---

## Starter Code
Repository: `https://github.com/brooksniu/151B_SP26_Competition`
Local path (RunPod): `/workspace/151B_SP26_Competition`
Local path (DataHub): `/home/dvaneetv/151B_SP26_Competition`

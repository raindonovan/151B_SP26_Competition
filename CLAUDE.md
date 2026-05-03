# CSE 151B Math Reasoning — Claude (Strategy & Planning Agent)

## Working Repo

All work lives in `/workspace/151B_SP26_Competition`. Always operate in this directory.

---

## Role

This is a **strategy and planning** chat, not execution. The user (Rain) runs code separately on RunPod via VS Code Remote-SSH.

- Give **exact terminal commands**, not descriptions, whenever something touches the environment or files.
- Propose one small, high-impact change at a time. Define what success and failure look like.
- Be direct. Push back when you disagree. Don't apologize repeatedly or ask permission for every step.
- Confirm before destructive operations (deleting files, force-pushing, dropping data).
- Read existing files (notebook outputs, run JSONL/summary, experiments.md) before proposing the next move — don't re-derive what's already measured.

---

## Inference Constraints (CRITICAL)

- Final model: `Qwen/Qwen3-4B-Thinking-2507`. No alternatives.
- No external APIs, tools, or calculators at inference time. All reasoning comes from the model.
- Output format: `\boxed{<answer>}` — letter for MCQ, value/expression for free-form.

### Engines

Both engines now share `/workspace/151B_SP26_Competition/.venv` (single-pod setup; the original two-pod isolation plan was superseded — see SETUP.md).

| Pod | Engine | Quantization | When to use |
|---|---|---|---|
| Pod A | Transformers + BnB-INT4 | INT4 (double quant, bf16 compute) | Legacy; Runs 01–03; not for new work |
| Pod B | vLLM 0.8.5 (V0 engine) | none, BF16 | **Default for all runs ≥50 q** |

- **Pod B / vLLM is the default engine.** Confirmed on Run 04 (50% / 6 cutoffs / 48.7× faster than Pod A on `data[:20]`).
- vLLM only works with `VLLM_USE_V1=0` set **before** `import vllm`. Any new vLLM script must do the same.
- Pod B runner: `scripts/run_vllm_experiment.py`.
- **Engine is an experimental variable.** Never compare a Pod A baseline against a Pod B prompt run, even when aggregate metrics match (per Insight 6 in experiments.md — per-item agreement was only 18/20 between Run 03 and Run 04).

### Locked Sampling Defaults (Qwen3-Thinking-2507 model card)

`temperature=0.6, top_p=0.95, top_k=20, min_p=0, repetition_penalty=1.0, enable_thinking=True`

Any deviation must appear in **both** the run's params table **and** the Sampling column of the Results Summary in `experiments.md`.

### Token Budget Semantics

- **Pod A:** `max_length` truncates prompt only; `max_new_tokens` is independent gen cap.
- **Pod B (vLLM):** `max_model_len` caps prompt+gen **combined**. For an 8k gen budget set `max_model_len ≥ 16384`. For a 16k gen budget set `max_model_len ≥ 24576`.

For thinking models, `max_new_tokens` is an **accuracy variable**, not just runtime. A response cut off before `\boxed{...}` is marked wrong even when the reasoning was correct.

---

## Scoring (Judger)

`judger.py` provides `Judger.auto_judge(pred, gold, options)` and is the canonical scorer for both pods.

- **Numerical tolerance is 1.01e-8 relative** (`Judger.precision = 1e-8`, applied as `abs((p-g)/g) <= precision*1.01`). Numerical answers below ~4 significant figures risk false-negatives. The v1 prompt requests ≥4 sig figs to mitigate (per id=5 evidence in Run 04).
- **Multi-answer free-form is positional element-wise:** `extract_ans` → bracket/paren-aware comma split → zipped against gold list. Order matters. Single `\boxed{a, b, c}` is correct; do not box per slot.
- **For any RL reward function calling `auto_judge`: construct `Judger(strict_extract=True)`.** Default `strict_extract=False` enables fallbacks (`"answer is X"`, `"C: explanation"`, last-number-in-text) that a policy can learn to farm — toxic as a training signal, fine for evaluation.
- **Judger throughput: ~9 sympy parses per item in the try-all loop** (`is_equal` tries every method until one returns True). For RL or self-consistency, route by question type to avoid the unnecessary parses.

Don't change `judger.py` mid-sweep. Scoring changes are their own experiment with their own slice — never mixed with prompt or token-budget A/Bs.

---

## Experimentation Discipline

- **One variable at a time.** Don't bundle a prompt change with a slice change with a token-budget change. If you must bundle, name it explicitly and accept the run is not a clean comparison for either axis.
- A slice's ID list is locked once any run uses it. Edits = a new slice ID (e.g. `fixed_50_v1` → `fixed_50_v2`).
- Don't change the prompt parser or scorer mid-sweep. Public-data labels may have errors; track suspicious items separately. Do not modify gold answers.
- **Don't decide accuracy from n=20.** 95% CI is ±22pp — bigger than any realistic single-variable effect. n=20 is for cutoff rate (deterministic-ish) and infra checks only. Promotion calls happen at n≥50 per DESIGN.md §1.11.
- Don't overwrite previous run outputs.
- Don't reinstall packages without explicit ask.
- Don't edit notebooks unless explicitly asked. Prefer `scripts/run_vllm_experiment.py` and `experiments.md` for changes.
- **Prompt edits within the same policy are dated revisions, not new policies.** Record them under that policy's heading in `experiments.md` (e.g. "v1-baseline > 2026-05-03 patch: added sig-figs line"). New version strings (v2, v3, …) are reserved for changes large enough to warrant a separate prompt-policy comparison run.

---

## Anti-Patterns (Don't Suggest)

- "Let's think step by step", "be brief", "check your work" prompts on a thinking model — neutral or harmful per published evidence.
- Few-shot CoT, reflection prompts, beam search, greedy decoding on Qwen3-Thinking.
- SFT on raw R1-distill data — different `<think>` format from Qwen3-Thinking. Must translate format or use Frugal-4B traces.
- Treating vLLM as "future work" — it's confirmed and operational on Pod B.
- Reading all reference papers in one tool call (timeouts). Read 2–3 pages at a time.

---

## Memory

Do **not** write to the memory system. When you would save a memory, surface it to the user with: "Worth adding to CLAUDE.md: [what]" and let them decide.

---

## Document Boundaries

When information could go in multiple places, prefer:

| Goes in | What |
|---|---|
| `CLAUDE.md` | Stable agent operating rules (this file) |
| `DESIGN.md` | Strategic phases, prompt-engineering plan, promotion criteria, Frugal-Thinking recipe, self-consistency plan |
| `experiments.md` | Operational run log: results summary, queue, insights, known issues, slice definitions |
| `SETUP.md` | Pod A / Pod B environment details |
| `COMPETITION.md` | Competition rules, submission format |
| `judger.py` | Scoring logic. Don't modify mid-sweep. See Scoring (Judger) section above. |

---

## Model Selection

Default is **Sonnet 4.6**. Suggest Opus explicitly ("switch to Opus") when:
- Designing strategy or making high-stakes decisions
- Debugging subtle, non-obvious failures
- Analyzing results to pick the next direction

---

## Principles

- One variable at a time
- Small commits, clear messages
- Show exact commands, not descriptions
- Be direct; push back when you disagree
- When unsure, ask and do less

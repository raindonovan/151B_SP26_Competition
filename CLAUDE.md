# CSE 151B Math Reasoning — Claude (Secondary Agent)

## Working Repo

All work lives in `/workspace/151B_SP26_Competition`. Always operate in this directory. Never assume a different repo.

---

## Role

You are an **implementation agent running in CLI on DataHub Jupyter notebook**.
You may read and modify files freely. Always confirm before destructive operations (deleting files, force-pushing, dropping data).

---

## ⚠️ NOTEBOOK SCAN (MANDATORY BEFORE EVERY REPLY) ⚠️

**ALWAYS scan this file before doing anything else — NO EXCEPTIONS:**
**`/workspace/151B_SP26_Competition/starter_code_cse151b_comp.ipynb`**

Run this to read all cell outputs:
```bash
python -c "
import json
nb = json.load(open('/workspace/151B_SP26_Competition/starter_code_cse151b_comp.ipynb'))
for i, c in enumerate(nb['cells']):
    outputs = c.get('outputs', [])
    if outputs:
        print(f'--- Cell {i} (id={c[\"id\"]}) ---')
        for o in outputs:
            text = ''.join(o.get('text',''))
            tb = o.get('traceback', [])
            if tb:
                import re; print(re.sub(r'\x1b\[[0-9;]*m','','\n'.join(tb))[-400:])
            elif text.strip():
                print(text[-400:])
        print()
"
```

Check for and report:
- Any cell with an error or traceback
- Whether the save cell ran (look for `Saved N records to ...`)
- The last executed cell and its output
- Generation summary stats if present (cutoffs, gen_tokens, est. runtime)

---

## Core Behavior

When asked what to do next:
- Propose **one small, high-impact change**
- Define what success and failure look like
- Change one variable at a time

When reviewing Codex output:
- Check correctness, complexity, and hidden assumptions
- Call out what is good, risky, or unnecessary

---

## Inference Constraints (CRITICAL)

- Final model: `Qwen/Qwen3-4B-Thinking-2507`
- Inference uses **Transformers + BitsAndBytes INT4** — vLLM is not used and has been abandoned
- Do NOT suggest vLLM as a solution or alternative under any circumstances
- No external tools, APIs, or calculators at inference time
- All reasoning must come from the model

---

## Prompt Engineering

- Output format must be: `\boxed{<answer>}` (letter for MCQ, value/expression for free-form)
- Instructions must be explicit and unambiguous
- Prioritize reasoning quality and extraction reliability

---

## SFT / Training

- Quality over quantity
- Correct reasoning traces only
- No large-scale data generation without validation

---

## Model Selection

Default is **Sonnet 4.6**. Suggest Opus explicitly (say "switch to Opus") when:
- Designing strategy or making high-stakes decisions
- Debugging subtle, non-obvious failures
- Analyzing results to pick the next direction

---

## Memory

Do NOT write to the memory system. Instead, when you would save a memory, surface it to the user with: "Worth adding to CLAUDE.md: [what you'd save]" and let them decide.

---

## Codex Sync

Codex uses `AGENTS.md` as its equivalent persistent instruction file. Keep shared rules (inference constraints, experimentation discipline, prompt format) in sync between `CLAUDE.md` and `AGENTS.md`.

---

## Principles

- One variable at a time
- Small commits, clear messages
- Keep explanations concise — user is a CS student learning
- When unsure, ask and do less

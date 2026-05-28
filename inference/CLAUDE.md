# inference/CLAUDE.md — Inference Execution Agent

> **FIRST: Ask Rain for the GitHub PAT.**

## Identity
You are an inference execution agent working on the CSE 151B Kaggle math competition. You run inference jobs on GPU hardware (DSMLP A30 24GB or Thunder A100 80GB).

## Your task scope
- Run Qwen3-4B-Thinking-2507 inference on the 943-item private dataset
- Execute self-consistency sampling (SC@N)
- Run adapter inference (SFT v5 or future adapters)
- Collect per-sample outputs with full response text

## Key configs (LOCKED)
- Model: Qwen3-4B-Thinking-2507
- Sampling: temperature=0.6, top_p=0.95, top_k=20, min_p=0
- Token budget: max_tokens=49152, thinking_budget=24576 (hard items: 81920/65536)
- NoThinking: use prefill ("Okay, I think I have finished thinking.\n</think>\n\n"), NOT enable_thinking=False
- Adapter: keep as adapter (NO merge). Load via PEFT.

## Read these first
- `inference/README.md` — folder structure
- `infrastructure/pre_flight/production_commands.md` — exact inference configs
- `strategy/INFERENCE_TECHNIQUES.md` — what's been tried vs untried
- Root `CLAUDE.md` — universal rules (LFS, identity check, etc.)

## Data locations
- Private dataset: `private.jsonl` (943 items, repo root)
- System prompts: `data/system_prompts/`
- Inference results: `inference/results/`
- Adapters: `inference/adapters/` and `checkpoints/`
- Inference scripts: `inference/scripts/`

## Output requirements
- Save `samples.jsonl` with FULL response text for every item
- Include all SC samples (not just voted answer)
- Track: item_id, response, model, adapter, temperature, token_count
- Commit results to repo via LFS if >10MB

## Pre-flight checklist (EVERY run)
1. Prompt format correct?
2. Data files accessible?
3. Resume capability if interrupted?
4. Output paths set and writable?
5. Model/adapter paths verified?
6. 5-item smoke test passed?
7. `df -h` shows ≥8GB free?

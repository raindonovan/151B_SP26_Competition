
## 2026-05-06 evening: v1 1k smoke training FAILED across all 3 arms

Root cause hypotheses (priority by reviewer consensus):
1. **TRUNCATION CATASTROPHE**: max_seq_length=4096 truncated 50%+ of OpenR1 
   (~4800 tok median) and 70%+ of Frugal (~5700 tok median) traces. Models 
   learned "ramble forever, never produce \boxed{}". Smoke test: avg gen 
   tokens 12,718 (vs baseline 6,602), 60% missing boxed answer, all 5 
   responses devolve into "1 1 1 1" / "than than than" repetition.

2. SYSTEM PROMPT MISMATCH: trained without, inference adds one.

3. TOKENIZER/CHAT-TEMPLATE SWAP: I replaced training-saved tokenizer files 
   with official Qwen3 ones post-merge (transformers version skew). 
   Reviewers said keep training-saved chat_template, not official.

4. WARMUP/LR: warmup_ratio=0.03 on 125 steps = ~4 warmup steps. With 
   lr=2e-4, weights jarred hard before warmup completes.

5. lora_dropout=0 + 125 steps = memorization recipe.

6. Frugal selection bias: kept only 45.2% Frugal-correct = biased toward 
   easier problems / low-entropy traces.

NO Kaggle submissions made. All adapters preserved on disk.

## Process lesson for next sessions

- Get third-party review (GPT + Gemini + Claude research) before any 
  major training/methodology decision. Tonight's reviewers caught issues 
  Claude missed (especially truncation).
- Image upload stopped working = signal that conversation context is 
  hitting limits. Start fresh window for v2 work tomorrow.
- Always cross-check (max_seq_length vs median trace length) before saying 
  "data prep looks good".

## v2 plan adopted (2026-05-07)

External review (ChatGPT + Gemini + fresh Claude research) consolidated the
post-mortem's guesses into the actual v2 plan. Five hyperparameter changes
from v1, plus three methodology changes.

### Hyperparameter changes (v1 → v2)

- `max_seq_length`: 4096 → **8192** (truncation fix; OpenR1 median ~4800,
  Frugal median ~5700 — v1's 4096 cut the final `\boxed{}` off labels)
- `r`: 16 → **32** (more capacity headroom for 8x training data)
- `lora_alpha`: 32 → **32** (value unchanged; comment swapped from "2x rank"
  to "Schulman default: alpha == r" — at r=32, alpha=32 satisfies alpha == r)
- `warmup_ratio`: 0.03 → **0.05** (~50 warmup steps over a ~1000-step run)
- `save_steps`: 250 → **200**

### Methodology changes

- **Train WITH inference system prompt.** `PROMPTS["v1-baseline"]["free"]`
  baked into SFT data via Path α: PROMPTS extracted to `scripts/prompts.py`,
  `prepare_numina_sft.py` prepends a system message to every record's messages
  array. Not injected at train time. Eliminates v1's reviewer-flagged
  prompt-mismatch contributor (verification still pending; truncation is the
  only verified v1 cause).
- **Preserve training-saved `chat_template.jinja` through merge.** Don't
  substitute the official Qwen template post-merge — v1 did this and it's
  one of the post-mortem suspects.
- **wandb tracking enabled** in `training/train_qwen3_qlora.py` (project
  `cse151b-sft`, `report_to="wandb"`, run_name forwarded from `--run-name`).
  Catches degenerate loss curves at step ~50, not after training finishes.

### Rejected from post-mortem guesses (with reasons)

- **LR = 1e-4** → kept at **2e-4**. Reviewers' consensus: 2e-4 is correct for
  Qwen3-Thinking short-run SFT (Schulman: 10× FullFT). 1e-4 was an
  over-correction with no specific evidence.
- **warmup_ratio = 0.1** → **0.05**. 0.1 is overkill at ~1000 steps; 0.05
  (~50 steps) gives the model enough ramp without stretching warmup over 10%
  of the run.
- **lora_dropout = 0.05** → kept at **0**. Short SFT runs use
  `weight_decay=0.01` as the regularizer; LoRA dropout at this scale adds
  noise without measurable benefit.

### Frugal v2 generation strategy (deferred)

k=4 samples per problem at temp 0.2–0.4, keep shortest correct. Locked but
rollout deferred until v2 NuminaMath kickoff results land. The v1
single-sample-temp-0.6 strategy biased toward easier problems / low-entropy
traces (post-mortem item 6).

### v2 NuminaMath kickoff command

Run inside `tmux new -s v2_numina`:

```bash
.venv-training/bin/python training/train_qwen3_qlora.py \
    --data data/sft/numina_concise_v2_8k.jsonl \
    --output-dir training/checkpoints/numina_concise_v2_8k \
    --run-name numina_concise_v2_8k \
    --max-seq-length 8192 \
    --lora-rank 32 \
    --lora-alpha 32 \
    --warmup-ratio 0.05 \
    --save-steps 200 \
    --num-epochs 1 \
    --learning-rate 2e-4
```

Verify after step ~50: training loop running, wandb run visible,
loss decreasing (not NaN, not stuck). v1 training-loss anchor for v2
comparison: **NuminaMath v1 final = 0.726**.

### Note: v2 NuminaMath SFT data on second regeneration tonight

v2 NuminaMath SFT data was regenerated **twice** during the pre-training
diagnostic session on 2026-05-07:

1. **First regen** added the inference system prompt to every record's
   messages array (Path α — `prepare_numina_sft.py` imports
   `PROMPTS["v1-baseline"]["free"]` from `scripts/prompts.py` and
   prepends a system message). Closed the v1 reviewer-flagged
   prompt-mismatch contributor.
2. **Second regen** added an explicit `</think>` to assistant content
   so the qwen3-thinking chat template lands the NuminaMath solution
   inside the auto-injected `<think>...</think>` block as reasoning
   trace, with the canonical `\boxed{<gold>}` post-think as answer
   commit (per DESIGN.md §7 Option 2). Caught by diagnostic 4.2's
   structural inspection — the binary `<think>` count was already
   passing, but the rendered template was Pattern B (empty think,
   answer-only) which §7 explicitly rejects.

Both regenerations preserved seed=42 determinism — same draw from
NuminaMath-1.5, same 8000 rows by problem identity, same length
filter. See [`experiments.md`](experiments.md) > External Review
Insights > 2026-05-07 entries for measurements.

## Recovery state

- 3 broken adapters at training/checkpoints/{openr1,numina_concise,frugal}_v1_1k/
- 3 merged BF16 models at .../merged/
- 3 SFT data files at data/sft/
- Working training/merge/inference scripts (modulo bugs)

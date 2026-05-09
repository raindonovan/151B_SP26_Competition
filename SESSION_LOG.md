
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

## Correction (2026-05-08): v1 was full-sequence, not assistant-only

Hypothesis 1 above (truncation catastrophe) is partially correct but materially incomplete. Investigation on 2026-05-08 (full trace in [`experiments.md`](experiments.md) > External Review Insights > 2026-05-08: Unsloth silently disables `assistant_only_loss=True`) found:

- The `assistant_only_loss=True` flag set on `SFTConfig` was silently ignored by Unsloth's compiled SFTTrainer override. Unsloth's `_prepare_dataset` bypasses TRL's `apply_chat_template(return_assistant_tokens_mask=True)` path and produces `input_ids`-only datasets. The default `DataCollatorForLanguageModeling` then constructed `labels = input_ids.clone()` (with `-100` only for pad tokens). v1 trained on **full-sequence cross-entropy**, not assistant-only.
- v1's reported final losses (NuminaMath 0.726, OpenR1 0.385, Frugal 0.190) measured next-token prediction across system + user + auto-injected `<think>\n\n</think>\n\n` + assistant content. They are real (loss curves descend, grad norms non-zero) but they are not "loss on assistant continuation given prompt." Cross-arm comparisons remain valid (same masking applied to all three).
- v1 NuminaMath specifically had 0/8000 truncations at `max_seq=4096` (measured on 2026-05-07), so the truncation hypothesis cannot explain its degenerate output. The Pattern B template structure (empty `<think>` block, full solution post-think — see 2026-05-07 assistant-content-structure entry) combined with full-sequence loss is the missing mechanism: v1 trained on a layout where think is empty, learned no distribution over think content, then at inference the chat template seeded `<think>\n` and the model rambled.
- Hypotheses 2-6 above are not directly affected. Hypothesis 3 (tokenizer/chat-template swap) remains a separate concern; this finding does not absolve it.

Implication for v2: F1/F2 fix candidates are inert under Unsloth; F0/F3 (full-sequence by design) and "skip Unsloth's prep + pre-tokenize ourselves" are the only live paths to assistant-only loss. Decision deferred to external review per [`CLAUDE.md`](CLAUDE.md) > External Review Before Compute Commits.

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

### Current state as of 2026-05-07 stop (third structural catch deferred)

Tonight's pre-training diagnostics caught **three** structural bugs:

1. v2 SFT system prompt absence (Path α regen) — **fixed and verified.**
2. Pattern B answer-only structure from missing explicit `</think>` —
   **fixed and verified** via diagnostic 4.2 + 4.1 re-runs on the
   Option-2-shaped data.
3. All-masked labels under `assistant_only_loss=True` (Unsloth #3383
   class — qwen3-thinking template lacks `{% generation %}` markers,
   transformers' fallback returns all-zeros mask, SFTTrainer writes
   `-100` to every label) — **deferred to next session for
   fresh-eyes fix-design decision.**

**Tomorrow's first action.** Investigate whether v1 training ran
under this same all-masked mask. Look at git history on
`training/train_qwen3_qlora.py` at the v1 SFT commit
(`b5454c2 v1 1k smoke training failed across 3 arms`) and any
earlier prepare/train script revisions. If v1 used the same
`get_chat_template("qwen3-thinking")` path, the v1 final losses
(NuminaMath 0.726, OpenR1 0.385, Frugal 0.190) couldn't have come
from gradient flow through the assistant span — would reframe the
truncation hypothesis. That investigation result informs the
F1/F2/F3 fix selection. See
[`experiments.md`](experiments.md) > 2026-05-07: v2 SFT
all-masked labels for the three options.

**Everything else ready for kickoff:**
- v2 NuminaMath SFT data regenerated and verified clean
  (diagnostics 4.1 PASS, 4.2 PASS, mid-think vs gold check PASS)
- `train_qwen3_qlora.py` edits done (`--lora-alpha` flag, wandb)
- wandb wired (project `cse151b-sft`, `run_name` forwarded)
- Diagnostic 4.4 (tokenizer round-trip across venvs) not yet run —
  depends on the chat-template choice from F1/F2/F3.

Only the masking-fix remains before kickoff.

## Recovery state

- 3 broken adapters at training/checkpoints/{openr1,numina_concise,frugal}_v1_1k/
- 3 merged BF16 models at .../merged/
- 3 SFT data files at data/sft/
- Working training/merge/inference scripts (modulo bugs)

## 2026-05-08 stop: v2 NuminaMath SFT training complete

First successful v2 SFT training. Run `numina_concise_v2_8k`, full epoch on 7992 rows, batch=2/grad_accum=4 (effective batch 8), 999 steps.

**Headline metrics.**
- Final running-average `train_loss`: **0.6092** (vs v1 NuminaMath final of 0.726, before the 2026-05-08 v1 reframe)
- Final `eval/assistant_only_loss` (held-out 8 rows): **0.5131 at checkpoint-800** (best by held-out eval), **0.5138 at checkpoint-999 / final_adapter** (+0.0007 from best — within noise)
- Wall-clock: **2h 16m** at 8.18 sec/step (vs ~7h baseline at 25 sec/step)
- Eval/assistant_only_loss trajectory: 0.9300 base → 0.5356 step 200 → 0.5243 step 400 → 0.5193 step 600 → 0.5131 step 800 → 0.5138 step 999. Monotonic improvement through step 800; tail uptick is noise on N=8.

**Throughput investigation completed.** Stacked-config smoke OOMed at 22.54/23.53 GiB; staged single-variable smokes isolated Unsloth's CPU-offload gradient checkpointing as the dominant bottleneck and the batch arithmetic restructure (1+8 → 2+4) as a secondary multiplier. Full investigation trace and four findings (two-layer config bug, OOM cliff, log-flush behavior, callback design held up) logged to [`experiments.md`](experiments.md) > External Review Insights > 2026-05-09 entry.

**Artifacts.**
- Final adapter: [`training/checkpoints/numina_concise_v2_8k/final_adapter`](training/checkpoints/numina_concise_v2_8k/final_adapter) (≡ checkpoint-999, no optimizer state)
- Best-eval checkpoint: [`training/checkpoints/numina_concise_v2_8k/checkpoint-800`](training/checkpoints/numina_concise_v2_8k/checkpoint-800)
- wandb run: `dvaneetv-university-of-california-san-diego/cse151b-sft/runs/prskijn1`
- Total disk: 1.8 GB (4 checkpoints retained per `save_total_limit=4`; checkpoint-200 deleted)

**Pending tomorrow.**
- Merge checkpoint-800 to BF16 via `model.save_pretrained_merged(...)` (per [`DESIGN.md`](DESIGN.md) §7 inference-merge plan)
- Run inference on `data/public.jsonl` via `scripts/run_vllm_experiment.py` against the merged model
- Kaggle submission (slot pending)
- Refresh "Recovery state" section above (now stale post-v2-success)
- Decide on v2 OpenR1 / Frugal arm kickoffs based on v2 NuminaMath leaderboard result

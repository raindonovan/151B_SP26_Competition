
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

## v2 fixes for tomorrow

- max_seq_length = 8192 (or 12288)
- Train WITH inference system prompt, OR remove system prompt at inference
- Don't replace training-saved chat_template.jinja
- LR = 1e-4 OR warmup_ratio = 0.1 (or both)
- lora_dropout = 0.05
- Frugal v2: k=4 samples per problem, temp=0.2-0.4, keep shortest correct
- Add multi-answer training data (37% of competition)
- Verify merge: weight diff base vs merged (q_proj, v_proj)
- Diagnostic FIRST: count truncated training examples per arm

## Recovery state

- 3 broken adapters at training/checkpoints/{openr1,numina_concise,frugal}_v1_1k/
- 3 merged BF16 models at .../merged/
- 3 SFT data files at data/sft/
- Working training/merge/inference scripts (modulo bugs)

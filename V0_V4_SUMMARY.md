# V0-V4 Variant Ablation Summary — CSE 151B SP26

**Status:** V0 = Executed (0.614 Kaggle). V1-V4 = Planned, not run. Document is a **research-to-execution bridge**.

---

## Quick Reference Table

| Variant | What Changed | Evidence Base | Expected Δ | Status | Notes |
|---------|-------------|---------------|-----------|--------|-------|
| **V0** | Baseline: v1-baseline prompt, SC-8, T=0.6 | Run 09 | **+0.614** Kaggle | ✓ Done | Achieved; anchor for all V1-V4 comparisons |
| **V1** | Prompt: add "exactly N answers" counting prefix to multi-answer Qs | Fu et al. 2505.14810 MathIF §3 | +1-3pp locally | Planned | Targets multi-free format errors; Qwen3 strong on instruction-following |
| **V2** | Prompt: V1 + counting reminder at END of prompt (bookend) | Fu et al. MathIF §4.2 repeat trick | +2-5pp locally | Planned | Strongest empirical fix in MathIF; models lose format instruction after long CoT |
| **V3** | Pipeline: V2 prompt + shape filter on SC voting pool | Custom inference logic | +1-3pp locally | Planned | Discard samples with wrong \# of comma-separated values in \boxed{}; catches format degradation |
| **V4** | Sampling: V3 + temperature diversification (T ∈ {0.5, 0.7, 0.9, 1.1}) | Sun et al. 2510.02611 temp diversity | +0-3pp locally | Planned | Covers ensemble diversity axis; cheap (one config change); measured on Qwen3-4B |

---

## Variant Details

### V0: Baseline (EXECUTED)

**What:** `v1-baseline` prompt + Self-Consistency N=8 + Single temperature T=0.6

**Config:** (from `scripts/variants.py`)
```python
{
    "prompt_version": "v1-baseline",
    "max_new_tokens": 32768,
    "presence_penalty": 1.0,
    "n_samples": 8,
    "temperature": 0.6,
    "top_p": 0.95,
    "top_k": 20,
    "min_p": 0.0,
    "repetition_penalty": 1.0,
    "temperature_ladder": None,
    "shape_filter": False,
}
```

**Prompt (free-form):**
```
You are an expert mathematician. Solve the problem step-by-step. 
Put your final answer inside \boxed{}. 
If the problem has multiple sub-answers, separate them by commas inside a single \boxed{}, 
e.g. \boxed{3, 7}. 
Give numerical answers to at least 4 significant figures, unless the problem specifies a different precision.
```

**Result:** Kaggle 0.614 on private 943-item set (Run 09).

**Status:** ✓ Executed, locked. This is the baseline for all V1-V4 deltas.

---

### V1: Counting Prefix

**What:** Add explicit "exactly N answers" prefix to free-form multi-answer questions.

**Delta from V0:**
```python
{
    "prompt_version": "v2-counting-top",  # NEW
}
```

**Prompt change (free-form multi-answer):**

**Before (V0):**
```
You are an expert mathematician. Solve the problem step-by-step. 
Put your final answer inside \boxed{}. 
If the problem has multiple sub-answers, separate them by commas inside a single \boxed{}, 
e.g. \boxed{3, 7}. 
```

**After (V1):**
```
This question requires exactly 2 answers. Your final answer must be a single \boxed{} containing exactly 2 values separated by commas. Example for 2: \boxed{value_1, value_2}.

You are an expert mathematician. Solve the problem step-by-step. 
Put your final answer inside \boxed{}. 
If the problem has multiple sub-answers, separate them by commas inside a single \boxed{}, 
e.g. \boxed{3, 7}. 
```

**Evidence:** Fu, Gu, Li, Qu, Cheng — "Scaling Reasoning, Losing Control" (arXiv 2505.14810, May 2025) — MathIF benchmark.

Key finding (Table 2): **Qwen3-4B has strongest instruction-following among ≤4B models** (HAcc 44.05%, beats DeepSeek-R1-Distill-70B at 41.43%).

**Why:** Explicit counting removes ambiguity on multi-answer format. Measurement strategy: count `[ANS]` placeholders in question, inject `exactly N` into prefix.

**Expected improvement:** +1-3pp on multi-free questions locally. (~13% of private set are multi-free; very loose upper bound on full set gain from format alone).

**Risk:** Potential slight regression on MCQ (format instruction adds noise for choice-picking), but MathIF shows instruction-following on Qwen3 is robust.

**Status:** Planned, not executed.

---

### V2: Counting Bookend (Repeat Trick)

**What:** V1 + add counting reminder at the END of the prompt (just before model generates answer).

**Delta from V1:**
```python
{
    "prompt_version": "v2-counting-bookend",  # CHANGED
}
```

**Prompt change (free-form multi-answer):**

**V1 structure:**
```
[PREFIX: "This question requires exactly N answers..."]

[System prompt + question text]
```

**V2 structure:**
```
[PREFIX: "This question requires exactly N answers..."]

[System prompt + question text]

[SUFFIX: "Reminder: your final answer must contain exactly N comma-separated values inside a single \boxed{}. Do not produce multiple \boxed{} blocks."]
```

**Evidence:** MathIF §4.2 (Table 6) — "repeat" intervention (reintroduce constraint at end, shortening distance to final answer).

**Result on Qwen3-32B:**
- HAcc: 43.81% → 59.29% (+15.48pp)
- SAcc: 62.82% → 68.34% (+5.52pp)
- Mechanism: Long CoT widens contextual distance from format instruction to answer generation. Re-introduction at end recovers ~60-68% instruction compliance.

**Why:** Qwen3-Thinking-2507 produces very long thinking traces (Run 09 averaged ~9300 tokens per sample). The longer the CoT, the more the model loses track of format constraints (MathIF Figure 6 shows monotonic HAcc decline with CoT length).

**Expected improvement:** +2-5pp on multi-free locally (stronger than V1 alone, as most v1 failures are format-related, not reasoning-related).

**Status:** Planned, not executed.

---

### V3: Shape Filter

**What:** V2 prompt + discard SC samples with wrong number of comma-separated entries in `\boxed{}`.

**Delta from V2:**
```python
{
    "shape_filter": True,  # NEW
}
```

**Implementation:** In SC voting pool, before majority-vote step:
1. Extract all values from `\boxed{...}` 
2. Split by commas, count non-empty entries
3. For multi-answer items: discard sample if count ≠ expected N
4. For single-answer items: discard if count > 1 (multiple boxes or comma-split values)
5. Proceed with majority-vote on remaining valid samples

**Why:** Temperature increases (V4) and long CoT cause format degradation:
- Some samples produce `\boxed{ans1, ans2, ans3}` when N=2 (extra value)
- Some produce multiple `\boxed{}` blocks instead of one (caught by extractor already, but shape filter catches malformed single-box cases)
- Some produce `\boxed{ans1 ans2}` (missing comma)

Shape filter rejects these *at voting time*, improving vote quality.

**Expected improvement:** +1-3pp (modest; most format errors are caught earlier, but this cleans up edge cases).

**Risk:** May reject some legitimately-correct samples where the model is unsure but still correct (e.g., `\boxed{(1, 2, 3)}` when N=1, answer is a tuple). Conservative: reject unless exact match on count.

**Status:** Planned, not executed.

---

### V4: Temperature Diversification

**What:** V3 prompt + sample across temperature ladder instead of single T=0.6.

**Delta from V3:**
```python
{
    "temperature_ladder": [0.5, 0.7, 0.9, 1.1],  # REPLACES temperature=0.6
}
```

**Implementation:** Instead of 8 samples at T=0.6, generate 2 samples each at T ∈ {0.5, 0.7, 0.9, 1.1}.

```python
# Pseudo-code
temps = [0.5, 0.7, 0.9, 1.1]
all_samples = []
for t in temps:
    samples = llm.generate(prompt, SamplingParams(n=2, temperature=t, ...))
    all_samples.extend(samples)
# all_samples now has 8 completions from 4 different temperatures
majority_vote(all_samples)
```

**Evidence:** Sun, Mirhoseini, Tambe — "On the Role of Temperature Sampling in Test-Time Scaling" (arXiv 2510.02611, Oct 2025).

**Key findings (direct Qwen3-4B tests):**
- Table 1 Pass@K: different Qs benefit from different temperatures. Single-T exploration misses subsets.
- Figure 2c: "When K is small [e.g., 8], different temperatures yield similar Pass@K."
- Figure 3c: Equal-compute version (13,312 samples across Ts vs single-T) gives ~6.67pp on AIME 2025.

**Reality check for our regime (SC-8 + majority vote, not Pass@K oracle):**
- Paper's +7.3pp headline is Pass@K (oracle picks any correct sample) not majority-vote.
- Majority vote is much more conservative: Avg@1024 remains nearly identical across Ts per paper.
- **Realistic expectation: +0 to +3pp on multi-free slice.**

**Temperature choice rationale:** Paper recommends excluding very low T (0.1-0.3, redundant). We cover diversity tier {0.5 low, 0.7 base, 0.9, 1.1 high}. AIMO-2 9th place team (Fast-Math-R1) ran SC at T=1.0, confirming our high-T choice.

**vLLM efficiency:** Use `enable_prefix_caching=True` in LLM config to share prefill KV cache across T calls. Without it, we pay prefill N times per question for N temperatures — tractable but less efficient.

**Expected improvement:** +0-3pp locally. Worth pulling because it's free (config change only), but not a killer move.

**Risk:** High T may degrade format compliance; shape filter (V3) should catch most degenerate outputs.

**Status:** Planned, not executed.

---

## Composition & Phasing

**Promotion path:**
1. Run V0 on fixed_50_v1 slice (already done at 0.614 Kaggle).
2. Run V1 on same slice. If +ε (even +1pp locally), keep V1. If ≤0, revert.
3. Run V2 (V1 + bookend). If +ε over V1, keep. Otherwise evaluate V1 vs revert baseline.
4. Run V3 (V2 + shape filter). Pipeline change only; should not harm.
5. Run V4 (V3 + temperature diversification). Config change; measure contribution.

**Variants are cumulative:** each δ is additive in expectation. Expected ceiling if all move: +0 to +3pp + +2 to +5pp + +1 to +3pp + +0 to +3pp = **+3 to +14pp locally** (very loose upper bound, not additive in practice).

**Realistic expectation:** +3 to +7pp locally → ~0.62-0.64 Kaggle (hard to move the anchor).

---

## Measurement Plan (per fixed_50_v1 slice)

### Metrics to log for each variant run:

1. **Overall accuracy** (% correct)
2. **By question type:**
   - MCQ accuracy (watch for regressions)
   - Single-free accuracy
   - Multi-free accuracy (primary target)
3. **Format compliance:**
   - % items with votable answer (≥1 sample has `\boxed{}`)
   - % multi-free items with exactly-N comma-separated values (pre-filter)
   - % samples rejected by shape filter (V3+)
4. **Per-temperature contribution (V4 only):**
   - How many items are uniquely solved by each T?
   - Agreement rate across Ts
5. **Edge case audit:**
   - Items with MCQ regression → inspect gold/format
   - Items with format failures → check CoT length

---

## Evidence Base Summary

### Sources read in full:

1. **Fu et al. 2505.14810** — MathIF: Scaling Reasoning, Losing Control
   - Multi-constraint instruction-following benchmark
   - Qwen3-4B strongest ≤4B model
   - Repeat trick (+15pp HAcc on Qwen3-32B)
   - Compositional load compounds (keep format unified)

2. **Sun et al. 2510.02611** — On the Role of Temperature Sampling
   - Temperature diversification on Qwen3 family (0.6B, 1.7B, 4B, 8B)
   - +7.3pp Pass@K (oracle); +0-3pp Avg@N (majority vote, our regime)
   - Different Qs need different Ts
   - Prefix caching reuses KV cache across temps

3. **Internal:** experiments.md, prompt_engineering_research.md
   - Run 09 anchor: 0.614 Kaggle
   - Baseline: 70% on fixed_50_v1 (10Q ceiling with v1-baseline)
   - Token budget: 16k minimum; 32k allows long CoT but not "more thinking"
   - Ambiguous gold floor: ~2-3Q on n=50 (not prompt-engineerable)

---

## Gaps: Ideas in prompt_engineering_research.md NOT yet in IDEAS.md

(Note: no IDEAS.md file exists in repo; creating one if needed).

### Locked ideas (in progress, code partially merged):

- [x] V0-V4 research path locked (variants_and_prompts.md + scripts/variants.py)
- [x] vLLM prefix caching rule (already in CLAUDE.md §Inference Rules)
- [x] Few-shot exemplars for V1-V2 (sketched in prompt_engineering_research.md §2, not implemented)
- [x] Shape filter logic (Section 3, code outline)

### Unlocked / deferred ideas:

- [ ] Logprob-weighted voting (DeepConf-style confidence scores) — deferred, paper says unreliable on hard problems
- [ ] Hierarchical voting (intra-T then cross-T) — only meaningful at 4+ samples per T; defer to SC-32+
- [ ] Re-tuning temperature subset on fixed_50_v1 — use paper's generic {0.5, 0.7, 0.9, 1.1} first
- [ ] Early exit on easy questions (Section 4.2 mechanism) — out of scope for SC-8 majority-vote
- [ ] Few-shot ablation grid (§2 Measurement) — listed but not yet run

---

## What Worked, What Didn't (Historical)

### Phase 1 (Concluded):
- ✓ V0 baseline locked, 70% on fixed_50_v1, 0.614 Kaggle
- ✗ Prompt engineering beyond V0 plateau'd at fixed_50_v1 (70% ceiling)

### Phase 2 (Active):
- ✓ Self-consistency SC-8 (+12pp over single-sample)
- ✓ V0-V4 path designed, evidence base locked
- ⏸ V1-V4 not yet executed (resource constraints)

### Phase 3 (Deferred):
- ✗ SFT v1 failed 2026-05-06 (three arms catastrophic failure: truncation @ 4096 + pattern B template + full-seq loss)
- ⏸ SFT v2 fixes sketched (SESSION_LOG.md 2026-05-06) but not scheduled

---

## Next Steps (for claude_vscode execution)

1. **Implement V1 variant:** Edit `scripts/prompts.py` to add `v2-counting-top`, update `build_prompt` in `run_vllm_experiment.py`.
2. **Smoke test V1:** Run on first 5 items, confirm prefix appears in user message.
3. **Run V1 on fixed_50_v1:** Log format compliance, MCQ/free breakdown.
4. **Iterate V2-V4:** Each variant adds one lever; measure cumulative delta.
5. **Promote to full private.jsonl:** If cumulative +ε locally, run on all 943 items, submit to Kaggle.

---

## Meta: Document Scope

**Created:** 2026-05-22 (research task from claude_vscode)
**Sources:** variants_and_prompts.md, scripts/variants.py, experiments.md, prompt_engineering_research.md, PIVOT.md, CLAUDE.md
**Audience:** Rain + claude_vscode execution coordination
**Format:** Research-to-execution bridge (evidence → variant spec → measurement plan)

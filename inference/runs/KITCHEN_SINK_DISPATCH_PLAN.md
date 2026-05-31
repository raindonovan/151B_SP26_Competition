# KITCHEN-SINK DISPATCH PLAN — FINAL LOCKED

**Status**: LOCKED — committed as canonical spec after Cursor final-lock pass
**Date**: 2026-05-31 (Day 9)
**Authors**: Cursor (initial draft) → claude_strategy (YELLOW corrections: rep_penalty/pp/cap) → Cursor (final pass: explicit min_p, size-aware stop rule) → claude_strategy (lock-in)
**Trigger**: post-Thunder land + target_set computation + Rain approval + explicit go
**Worker**: claude_vscode (or first free 2xA100 box once tnr-1 finishes)

## GOAL

Run ONE final bounded inference attempt on true residuals after tnr-0/tnr-1 land. No teacher traces. Qwen-only. If stop-rule fails, inference closes for tonight.

## LOCKED CONSTRAINTS (do not modify without re-audit)

- **rep_penalty = 1.0 on ALL rungs** (base Qwen discipline per R14 audit + Sun et al. priors)
- **presence_penalty = 1.0 on ALL rungs** (matches R20 pp1 baseline for attribution cleanness)
- **min_p = 0.0 explicit on ALL rungs** (Cursor final-lock: explicit > implicit, prevents vLLM default surprise)
- **target cap = 40 items** (wall-clock feasibility)
- **3 rungs only, param-only diversification** (Rung 1 stable / Rung 2 production-anchor / Rung 3 temperature-diversity)
- **No teacher-trace hints, no NoThinking rung, no prompt-logic changes, no cap expansion**

---

## A) 3-RUNG COMMAND BLOCK (Thinking, TP=2, max_tokens=81920, thinking_budget=65536, SC=16)

```bash
# Preconditions:
# - Residual target IDs file exists: submission/csvs/picks/kitchensink_target_ids.txt
# - One 2xA100 box is free (tnr-1 finished, freed)
# - Repo at main and clean
# - Section B residual computed AND Rain approved target_set
# - DO NOT start until all preconditions met (see Section E)

source ~/venv/bin/activate
export HF_HOME=~/hf_cache
export LD_LIBRARY_PATH=/usr/local/cuda/targets/x86_64-linux/lib:$LD_LIBRARY_PATH
cd ~/151B_SP26_Competition

RUN_TAG="kitchensink_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="inference/base_model/${RUN_TAG}"
mkdir -p "$OUT_DIR"

# Rung 1 — Stable exploit
HF_HOME=$HOME/hf_cache python3 -u inference/scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --tensor-parallel-size 2 \
  --item-ids submission/csvs/picks/kitchensink_target_ids.txt \
  --output "$OUT_DIR/rung1_stable.jsonl" \
  --mcq-format letters \
  --sc 16 \
  --max-tokens 81920 --thinking-budget 65536 \
  --temperature 0.55 --top-p 0.95 --top-k 20 --min-p 0.0 \
  --presence-penalty 1.0 \
  --repetition-penalty 1.0 \
  2>&1 | tee "$OUT_DIR/rung1_stable.log"

# Rung 2 — Production anchor (matches R20 baseline params)
HF_HOME=$HOME/hf_cache python3 -u inference/scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --tensor-parallel-size 2 \
  --item-ids submission/csvs/picks/kitchensink_target_ids.txt \
  --output "$OUT_DIR/rung2_prodlike.jsonl" \
  --mcq-format letters \
  --sc 16 \
  --max-tokens 81920 --thinking-budget 65536 \
  --temperature 0.60 --top-p 0.95 --top-k 20 --min-p 0.0 \
  --presence-penalty 1.0 \
  --repetition-penalty 1.0 \
  2>&1 | tee "$OUT_DIR/rung2_prodlike.log"

# Rung 3 — Controlled diversity (temperature-based)
HF_HOME=$HOME/hf_cache python3 -u inference/scripts/run_hybrid_inference.py \
  --mode base \
  --model Qwen/Qwen3-4B-Thinking-2507 \
  --tensor-parallel-size 2 \
  --item-ids submission/csvs/picks/kitchensink_target_ids.txt \
  --output "$OUT_DIR/rung3_diverse.jsonl" \
  --mcq-format letters \
  --sc 16 \
  --max-tokens 81920 --thinking-budget 65536 \
  --temperature 0.72 --top-p 0.90 --top-k 40 --min-p 0.0 \
  --presence-penalty 1.0 \
  --repetition-penalty 1.0 \
  2>&1 | tee "$OUT_DIR/rung3_diverse.log"
```

---

## B) RESIDUAL-ITEM SELECTION RULE

**Run immediately after Thunder lands. Inputs:**

1. R20 analysis: `inference/base_model/R20_eval_v1_sc8_p943_t32k_pp1/analysis/analysis.csv`
2. R20 samples: `inference/base_model/R20_eval_v1_sc8_p943_t32k_pp1/run14b_sc8_v1_private943_tok32k_pp1.jsonl`
3. Thunder outputs: tnr-0 + tnr-1 samples.jsonl (landed run dirs)
4. Thunder 118 set: `submission/csvs/picks/thinking_probe_target_set.csv`
5. NT-13 join set: `submission/csvs/picks/overrides_nothinking_join_conservative.csv`
6. Existing rescue accounting pool: `submission/csvs/picks/pickb_marginal_accounting.csv` (dedup sanity)

**Selection procedure:**

**Step 1**: Build base residual universe U
- Start with R20 rows where `math_correct == 'False'` (R20-wrong universe = 187 items)
  - **OPERATIONAL OVERRIDE** (approved Cursor final-lock + post-target-set audit): Original spec said "bucket == 'B' or bucket == 'A_lucky_sample'" (72 items). That filter is too narrow — it excludes items where `bucket == 'unknown'` (gold uncertain or sheet_dependent) which Thunder explicitly covered (62 of Thunder 118 are sheet_dependent). The bucket filter is artificially narrow vs Thunder's operational universe. Using `math_correct == 'False'` aligns the kitchen-sink universe with Thunder's. Stop rule's measurable-gold gate protects against false signal from the broader pool.
- Remove IDs already rescued by:
  - Thunder landed rescues (tnr-0/1 delta-positive vs R20)
  - NT-13 conservative join IDs
  - **HIGH-confidence per_item_overrides** (229/308/383/498) — already covered by Tier-1 normalizer's force_value step; budget-efficient to not waste kitchen-sink GPU on them
- Remove IDs present in Thunder 118 set (explicit requirement)

**Step 2**: Compute rescue-potential signal per remaining item

From R20 SC@8 samples compute:
- `top_vote_count`, `second_vote_count`, `vote_margin = top - second`

Operationalized criteria (concrete, per Cursor final pass):
- `close_vote = (top_vote_count <= 5) OR (vote_margin <= 2)`
- `multi_slot_precision_risk = ` ONE of:
  - `item.question.count("[ANS]") >= 2` (multi-slot template)
  - OR R20 analysis row has `UNDERCOUNT_*` or `OVERCOUNT_*` flag
  - OR `category == "free_multi"`

**Step 3**: Keep only candidates with rescue-potential
- keep if `close_vote == True OR multi_slot_precision_risk == True`

**Step 4**: HARD CAP = 40 items
- If >40, rank:
  1. smallest `vote_margin` first
  2. then `close_vote == True`
  3. then `multi_slot_precision_risk == True`
  4. then independent-gold source priority (wolfram_HIGH → search_GOLD → unanimous_teachers)
- Keep top 40
- If <40, backfill with next-best `close_vote` items (CONFIRMED: backfill source ALSO excludes Thunder118 + NT-13 + Thunder landed rescues)

**Step 5**: Write outputs
- `submission/csvs/picks/kitchensink_target_set.csv` with:
  `id, reason_close_vote, reason_multi_slot_precision, top_vote_count, second_vote_count, vote_margin, r20_bucket, gold_source, in_thunder118, in_nt13`
- `submission/csvs/picks/kitchensink_target_ids.txt` (id-only, one per line)

---

## C) STOP-RULE (pre-registered, strict)

**Primary gate**: On kitchen-sink target intersection with independent-gold (gold_source ∈ {wolfram_HIGH, search_GOLD, unanimous_teachers}):
- **If measurable subset >= 20 items**: best rung (or rung-ensemble winner) must deliver **>= +2 net correct vs R20 baseline**
- **If measurable subset < 20 items (size-aware amendment per Cursor final pass)**: best rung must deliver **+1 net correct AND zero regressions** vs R20 baseline

**Fail condition**: If gate not met → **STOP, declare inference closed for tonight, redirect to normalizer + submission sequencing + SFT gate**

**Optional early kill**: If Rung 1 + Rung 2 both show <=0 measurable net AND similar winners → skip Rung 3 and close inference immediately

---

## D) POLICY LOCKS

- ❌ **No teacher-trace hints** (Rule #11 compliance + attribution cleanness)
- ❌ **No teacher model outputs in prompts/exemplars**
- ❌ **No NoThinking rung** (NT_targeted_rescue showed NET -5 historically)
- ❌ **No prompt-logic changes** (cut for attribution; no self-critique, no few-shot)
- ❌ **No cap expansion beyond 40** (wall-clock)
- ✅ **Any specialization stays Qwen-only and explicitly declared**

---

## E) DISPATCH GATE

Do not fire until ALL of:

1. ✅ Thunder residual is computed (tnr-0 + tnr-1 landed, processed)
2. ✅ Section B selection rule has been run, producing `kitchensink_target_set.csv` + `kitchensink_target_ids.txt`
3. ✅ claude_strategy + Rain audit and approve target_set
4. ✅ Explicit "go" signal from Rain

---

## F) DELIVERABLES (post-run)

- `inference/base_model/${RUN_TAG}/rung1_stable.jsonl` + `.log`
- `inference/base_model/${RUN_TAG}/rung2_prodlike.jsonl` + `.log`
- `inference/base_model/${RUN_TAG}/rung3_diverse.jsonl` + `.log`
- `inference/base_model/${RUN_TAG}/findings.md` — claude_strategy authored post-run with:
  - Per-rung rescue analysis (which rung produced which rescues?)
  - Measurable-gold lift vs R20 baseline (gate check)
  - Cross-rung agreement signal
  - Kill-or-keep call per Section C

---

## G) AUDIT TRAIL

This spec was developed via 3 audit cycles:

1. **Cursor initial draft** (3-rung structure + selection + stop)
2. **claude_strategy YELLOW**: rep_penalty=1.1 bug (R14 audit conflict), presence_penalty inconsistency, cap 80→40
3. **Cursor corrected + final-lock pass**: explicit min_p=0.0, size-aware stop rule, optional min_p swap REJECTED in favor of temperature-based diversity

LOCKED at this state. Modifications require re-audit cycle.

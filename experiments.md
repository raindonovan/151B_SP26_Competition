# CSE 151B SP26 — Experiment Log

## See Also

- [`DESIGN.md`](DESIGN.md) — strategic phases, prompt-engineering plan, promotion criteria
- [`SETUP.md`](SETUP.md) — Pod A/Pod B environments, inference speed levers
- [`COMPETITION.md`](COMPETITION.md) — rules, submission format, allowed methods
- [`CLAUDE.md`](CLAUDE.md) — agent operating instructions (mirrored in `AGENTS.md` for Codex)

This doc owns the **operational** record (what was run, with what params, what came out). Strategic decisions (which prompt policies to test, what gates to use, what phase comes next) live in `DESIGN.md`.

---

## Environment

Two pods, same model, different inference stacks. See [`SETUP.md`](SETUP.md) for setup details and the rationale for the split. Per-run rows in the Results Summary identify which pod produced them via the Engine column.

**Shared**
- Model: `Qwen/Qwen3-4B-Thinking-2507`
- Compute: NVIDIA GeForce RTX 4090 (24 GB)

**Pod A — Transformers (current primary)**
- Engine: Transformers + BitsAndBytes
- Quantization: 4-bit BitsAndBytes (INT4, double quant, bf16 compute)
- Torch: 2.11.0+cu128 | CUDA: 12.8 | Transformers: 5.7.0
- Kernel: Python (cse151b)
- Used by: Runs 01–03

**Pod B — vLLM (working as of 2026-05-03)**
- Engine: vLLM 0.8.5 (V0 engine; `VLLM_USE_V1=0` required — see Known Issues)
- Quantization: none
- dtype: bfloat16
- gpu_memory_utilization: 0.85
- Torch: 2.6.0+cu124 | CUDA: 12.4 | Transformers: 4.51.3
- Runner: `scripts/run_vllm_experiment.py`
- Used by: `run_vllm_smoke_5_tok8192`, Runs 04–06

---

## Locked Defaults

Sampling defaults are **shared** across both pods and apply to every run unless explicitly overridden. Engine defaults are **per-pod** (Pod A = Transformers + BnB-INT4; Pod B = vLLM + BF16) — engine choice is recorded explicitly in each run, not as a deviation.

Per-run param tables write **"default"** for any sampling field below; only deviations get listed.

**Sampling (shared, both pods)**

| Param | Value | Source |
|---|---|---|
| temperature | 0.6 | Qwen3-Thinking-2507 model card |
| top_p | 0.95 | Qwen3-Thinking-2507 model card |
| top_k | 20 | Qwen3-Thinking-2507 model card |
| min_p | 0.0 | Qwen3-Thinking-2507 model card |
| repetition_penalty | 1.0 | Qwen3-Thinking-2507 model card |
| do_sample | True | required for sampling decoding (Pod A only — vLLM samples whenever `temperature > 0`) |
| enable_thinking | True | thinking-variant model |
| max_length (input truncation) | 16384 | Pod A |

**Engine (per-pod, recorded explicitly)**

| Pod | Engine | Quantization | dtype |
|---|---|---|---|
| Pod A | Transformers | BnB-INT4 (double quant) | bf16 compute |
| Pod B | vLLM 0.8.5 (V0) | none | bfloat16 |

**Token-budget semantics differ between pods — read this before setting `max_new_tokens` on Pod B.**

| Pod | How the budget works |
|---|---|
| Pod A (Transformers) | `max_length=16384` truncates the **prompt only**. `max_new_tokens` is an **independent** generation cap. Effective generation budget = `max_new_tokens` regardless of prompt length. |
| Pod B (vLLM) | `max_model_len` caps **prompt + generation combined**. Effective generation budget = `max_model_len − prompt_len`. To match Pod A's full 8192-token gen budget on the standard slice, use `max_model_len ≥ 16384` (script default is 16384). For an explicit 16k generation budget, set `max_model_len ≥ ~24576` (16384 + prompt headroom). |

When comparing a Pod A run to a Pod B run, confirm both effectively allowed the same generation budget, not just that they share the same `max_new_tokens` number.

If a run deviates from any sampling default, the deviation must appear in **both** that run's params table **and** the Sampling/Notes column of the Results Summary, so the diff is visible at a glance.

---

## Results Summary

| Run | Date | N | Slice | Prompt | Engine | tok | avg_tok | s/q | Cutoffs | MCQ | Free | Overall | Sampling | Results |
|-----|------------|---:|-------------|--------|--------------|-----:|--------:|------:|--------:|:-------------|:-------------|:--------------|----------|----------|
| 01  | 2026-05-01 |  5 | `data[:5]`  | v1     | Transformers | 2048 | —       | —     | ?       | 0/2 = 0.0%   | 2/3 = 66.7%  | 2/5 = 40.0%  | default  | [starter_results.jsonl](results/starter_results.jsonl) |
| 02  | 2026-05-01 | 20 | `data[:20]` | v1     | Transformers | 4096 | —       | —     | 9 (est.) | 3/9 = 33.3%  | 6/11 = 54.5% | 9/20 = 45.0% | default  | [run02_baseline_20_tok4096.jsonl](results/run02_baseline_20_tok4096.jsonl) |
| 03  | 2026-05-01 | 20 | `data[:20]` | v1     | Transformers | 8192 | 5466    | 395.7 | 6       | 4/9 = 44.4%  | 6/11 = 54.5% | 10/20 = 50.0% | default | [run03_tok8192_20.jsonl](results/run03_tok8192_20.jsonl) |
| smoke‑vLLM | 2026-05-03 | 5 | `data[:5]` | v1 | vLLM BF16 | 8192 | 4332 | 20.7 | 0 | 1/2 = 50.0% | 2/3 = 66.7% | 3/5 = 60.0% | default | [run_vllm_smoke_5_tok8192.jsonl](results/run_vllm_smoke_5_tok8192.jsonl) |
| 04  | 2026-05-03 | 20 | `data[:20]` | v1     | vLLM BF16    | 8192 | 4899    |   8.1 | 6       | 4/9 = 44.4%  | 6/11 = 54.5% | 10/20 = 50.0% | default; max_model_len=16384 | [run04_vllm_parity_20_tok8192.jsonl](results/run04_vllm_parity_20_tok8192.jsonl) |
| 05  | 2026-05-03 | 50 | `fixed_50_v1` | v1 (sig-figs patched) | vLLM BF16 | 16384 | 4871 | 13.0 | 4 | 14/17 = 82.4% | 21/33 = 63.6% | 35/50 = 70.0% | default; max_model_len=24576 | [run05_v1_50_tok16384.jsonl](results/run05_v1_50_tok16384.jsonl) |
| 06  | 2026-05-03 | 50 | `fixed_50_v1` | v2-mcq-commit | vLLM BF16 | 16384 | 4772 | 13.3 | 3 | 13/17 = 76.5% | 20/33 = 60.6% | 33/50 = 66.0% | default; max_model_len=24576 | [run06_v2mcq_50_tok16384.jsonl](results/run06_v2mcq_50_tok16384.jsonl) |

Runtime + cost: Run 03 = 131.9 min ≈ $1.52 (Pod A). Run 04 = 162 s ≈ $0.03 (Pod B). Run 05 = 650 s ≈ $0.13. Run 06 = 666 s ≈ $0.13. vLLM smoke = 103.3 s. Earlier Pod A runs untracked. Pod B at 13 s/q on n=50 / 16k cap extrapolates to ~245 min ≈ $2.80 for the full 1126-question set.

**`smoke‑vLLM` is an infrastructure-validation run, not a comparable experiment.** N=5 is too small for accuracy claims; its purpose was to confirm Pod B (vLLM 0.8.5, V0 engine) generates end-to-end with `\boxed{}` extraction working. It is excluded from cross-run accuracy comparisons. The first comparable Pod B run is planned Run 04.

---

## Insights

Cross-run lessons. Each cites the run(s) it came from. New insights belong here, not buried in a single run's Observations.

1. **Token budget reduces cutoff rate as expected; it does NOT unlock additional reasoning depth on items that aren't already cap-bound.** Runs 02→03 on Pod A (4k→8k) dropped cutoffs ~9→6 on n=20. Runs 04→05 effectively repeat this on Pod B at a larger scale (8k→16k, slice changed from `data[:20]` to `fixed_50_v1`): cutoff *rate* dropped 30%→8% (6/20 → 4/50), but **avg gen tokens barely moved (4899→4871) despite doubling the cap.** p50 on Run 05 was 3536 — most items don't use the extra budget. The extra cap is a binary safety net for the long-tail items, not "more thinking room" for the median. **16k locked as the operating point**; chasing 32k would only matter if cutoffs > ~5/50 and Frugal Table 5 indicates diminishing returns past 16k for the base model anyway.

2. **The MCQ-cutoff pattern is structural, not prompt-engineerable at this cap.** Pod A Run 03: 5/6 cutoffs MCQ. Pod B Run 04 at 8k: 4/6 cutoffs MCQ. Pod B Run 05 at 16k: 3/4 cutoffs MCQ (17.6% of MCQ items vs 3% of free items). Pod B Run 06 with v2-mcq-commit prompt at 16k: 2/3 cutoffs MCQ. **Pattern survives engine swap, cap doubling, AND a commitment-targeted prompt.** Most damningly, Run 06 converted *zero* of Run 05's 3 MCQ cutoffs to correct answers — its cutoff count dropped from 3 to 2 by causing the model to commit to a *wrong* answer instead of running out of tokens. Conclusion: at this model scale and cap, the items hitting the MCQ cutoff cluster are reasoning-bound, not budget- or commitment-bound. Further prompt iteration on the MCQ axis is a low-leverage move; the next high-leverage lever is sample-level (self-consistency) or training-level (RL/SFT).

3. **Pod A throughput is infeasible for full-set runs.** Run 03 measured ~14 tok/s through Transformers + BnB-INT4 → ~395 s/q → ~124 hr / ~$85 for the full 1126 questions. Anything past a 50–100 q validation slice needs Pod B (vLLM batching).

4. **The model self-terminates near `\boxed{}` already.** Simulated early-stopping on Run 03 saved ~1% of decoded chars on average — the model emits EOS shortly after the boxed answer in the success cases. Early-stop (now wired into the notebook) is a cheap safety net but **not** a meaningful speed lever for this model on this data. Real speed wins come from Pod B and from prompt changes that prevent runaway thinking.

5. **Pod B/vLLM is ~49× faster than Pod A at the n=20 / 8k operating point, confirmed.** Run 04 = **8.12 s/q** vs Run 03's 395.7 s/q on the same slice/prompt/cap = **48.7× speedup** measured (vs the 19× n=5 smoke estimate, which was a floor as expected — batching scales). Full-set extrapolation: 1126 questions ≈ 152 minutes ≈ $0.30 on this pod. Pod B is now the default engine for runs ≥50 q (decision applied per Run 04 pre-registered comparisons).

6. **Per-item variance is real even at fixed engine + slice + cap; ~2 q on n=50 is the noise floor.** Original evidence from Run 03 vs 04 (different engine): 18/20 per-item agreement despite identical aggregate metrics. Run 05 vs Run 06 (same engine, same slice, same cap, only MCQ system prompt changed; free-form prompt byte-identical): 48/50 agreement. The 2 v1→v2 losses were id=48 (ambiguous gold — see Insight 7) and id=199 (sampling variance on a free-form item where the prompt was byte-identical). **Implication:** at n=50, ±2 q is sampling + engine noise even with everything else held fixed. A prompt-policy comparison needs >+4 q delta to clear noise (matches DESIGN.md §1.11 promotion bar). The original engine-as-variable rule still holds: never compare Pod A baseline against Pod B prompt run, ever.

7. **Ambiguous-gold floor on n=50 is ~2-3 q.** id=48 (Run 06): gold `I` = `(4/3)ln3` and model's `E` = `(2/3)ln9` are mathematically identical (`ln 9 = 2 ln 3`). The question has two correct options; gold picks one and the Judger is brittle on the other. Combined with instructor-confirmed dataset errors (questions 1, 8, 12.3 — see CLAUDE.md > Data & Analysis Discipline), this means every reported accuracy on a 50-item slice carries ~2-3 q of irreducible error from gold mismatches alone, on top of the ±2 q sampling/engine noise from Insight 6. **Combined noise floor is ~3-5 q at n=50.** Self-consistency partially helps (vote across N samples reflects which equivalent form the model leans toward); the underlying scorer brittleness is unfixable without scorer changes (which don't happen mid-sweep). **Operational protocol:** see CLAUDE.md > Data & Analysis Discipline for the wrong-answer audit checklist (mathematical equivalence / gold wrong / genuine model error) before drawing behavioral conclusions from <5 items of evidence.

---

## External Review Insights

Failures caught — or that should have been caught — by external review of compute commits. Dated, tied to the run/decision they affected. New entries appended. See [`CLAUDE.md`](CLAUDE.md) > External Review Before Compute Commits for the rule.

### 2026-05-06: v1 SFT truncation (caught by 3 reviewers)

ChatGPT, Gemini, and fresh Claude research all flagged `max_seq_length=4096` as below the median trace length of OpenR1 (~4800 tokens) and Frugal (~5700 tokens), which silently truncated the final `\boxed{}` off training labels. v1 trained anyway; output degenerated across all three teacher arms (60% missing boxed answer, ~12,718 avg gen tokens vs baseline 6,602, repetition collapse). v2 raises `max_seq_length` to 8192. See [`SESSION_LOG.md`](SESSION_LOG.md) > 2026-05-06 evening.

### 2026-05-06: v1 merge verification gap (Gemini)

File size and structure of a merged BF16 model are not evidence that the LoRA delta was actually folded in. The authoritative check is logit-diff vs base on a fixed prompt set; a passing diff confirms the merge reached the weights. Required pre-submission, not optional. v1 skipped this; whether the merge ever applied correctly is unverified.

### 2026-05-06: tokenizer round-trip (Claude research)

`transformers 5.5.0` (training venv) vs `4.51.3` (inference venv) version skew can produce silent token-ID drift on the same input string under the same chat template. Diagnostic: tokenize identical input under both versions, compare ID sequences. Required before any claim of tokenizer/template equivalence between training and inference. Pending.

### 2026-05-07: v2 SFT system prompt absence (execution agent)

v2 SFT data was prepared by running the unmodified v1 `prepare_numina_sft.py` script, which constructs `messages = [user, assistant]` with no system message — would have repeated v1's prompt-mismatch failure mode silently. Caught during pre-training inspection at the start of the v2 prep step. Resolution: Path α — extract `PROMPTS` to `scripts/prompts.py` (no heavy imports), edit `prepare_numina_sft.py` to prepend `PROMPTS["v1-baseline"]["free"]` as a system message, regenerate `data/sft/numina_concise_v2_8k.jsonl` with seed=42 preserving user+assistant content byte-identical (only the prepended system message differs). Refactor verified via `from scripts.prompts import PROMPTS is from scripts.run_vllm_experiment import PROMPTS` → True.

### 2026-05-07: v2 SFT assistant-content structure bug (diagnostic 4.2)

Diagnostic 4.2 (`<think>` count == 1 per templated example) passed the binary count criterion (1 open, 1 close, 0/100 leakage) but structural inspection revealed the chat template was auto-injecting an empty `<think>\n\n</think>\n\n` block and placing **all** of our assistant content (NuminaMath solution + canonical boxed answer) as **post-think** material. Would have trained the model to skip thinking entirely — the answer-only failure mode that DESIGN.md §7 explicitly rejected. Same class of catch as the system prompt absence entry above: silent format corruption that the binary diagnostic alone wouldn't have caught, surfaced only by inspecting the rendered template structure.

**Resolution.** Single-branch unification of `prepare_numina_sft.py` to always append `"</think>\n\nThe answer is $\boxed{<gold>}$."` to assistant content. Verified Hypothesis A on a single-row test: unsloth's `qwen3-thinking` template detects an existing `</think>` in assistant content and elides its own auto-injected close. Result post-fix: NuminaMath solution body lands inside the auto-injected `<think>...</think>` block as reasoning trace; the explicit `\boxed{<gold>}` lands post-think as canonical answer commit. Matches DESIGN.md §7 Option 2 exactly. The old prep script's `if boxed_was_present: pass else: append` two-branch logic was correct *under the old contract* (don't double-wrap) but unnecessary under the new contract — mid-think `\boxed{}` is reasoning trace, post-think `\boxed{}` is canonical commit, and duplicating across the boundary is the *correct* behavior (matches Qwen3-Thinking's natural inference output).

**Mid-think vs post-think `\boxed{}` agreement measurement (post-fix data).** 1544/8000 (19.3%) of rows have at least one `\boxed{}` inside the think block. Of those, 1465/1544 (94.9%) match canonical gold under string-or-sympy equivalence. 78/79 disagreements are the same systematic pattern: `amc_aime` source rows where NuminaMath boxed the multiple-choice option label (`\textbf{(D) } 48`, `\mathrm{(C)}\ \frac{\sqrt{3}}{4}-\frac{1}{24}\pi`, or even bare `'C'` / `'D'` / `\text{D}`) while canonical gold stripped to the underlying numerical/symbolic value. Trains a *positive* normalization signal: verbose mid-think reasoning → clean canonical post-think commit, exactly the inference behavior we want. One genuine outlier at **0.0125% prevalence**: row 3205, source `number_theory`, mid-think `\boxed{38249}` vs gold being a prime factorization of 710352035484. Below noise threshold; left in the dataset for clean v1↔v2 row-count parity. **Flag for future investigation if v2 NuminaMath shows anomalous behavior on number-theory items specifically.**

### 2026-05-07: NuminaMath SFT data length distribution (diagnostic 4.1)

On `data/sft/numina_concise_v2_8k.jsonl` (post-`</think>` fix) after `qwen3-thinking` chat template application: p50=660, p75=945, p90=1252, p95=1451, max=2710 tokens; mean=762. 0/8000 exceeded `max_seq_length=8192`.

**Implication for the v1 truncation hypothesis.** v1's failure root-cause hypothesis from external review (max_seq_length=4096 truncating final `\boxed{}` from labels) was measured against OpenR1 (median ~4800) and Frugal (median ~5700). NuminaMath's true distribution is fundamentally different — solutions are concise (filtered to 200-2000 *solution* tokens; +system/user/template overhead lands at 330-2710 total). At v1's max_seq=4096, **0/8000 NuminaMath examples would have been truncated.** v1 NuminaMath's failure (final loss 0.726, degenerate output) was therefore NOT truncation-limited; the truncation hypothesis was over-generalized from the OpenR1/Frugal arms to all three. **Future v3 NuminaMath could safely run at `max_seq=3072` or even `2048`** (max example is 2710 tokens). v2 keeps `max_seq=8192` to avoid muddying the v1↔v2 comparison with an unnecessary sixth changed variable. Strategically, v2 NuminaMath becomes a cleaner isolation experiment than originally framed — the active variable for this arm is most likely the system-prompt fix (Path α) plus the assistant-content structure fix, not max_seq_length.

### 2026-05-07: v2 SFT all-masked labels (Unsloth #3383 class)

Diagnostic 4.3 caught silent corruption in the loss-masking machinery: **zero of 915 input tokens were graded** on the test example — all labels = `-100`, every position masked from cross-entropy loss. Training under this would compute loss over an entirely masked sequence, producing zero gradient signal across the assistant turn. The output checkpoint would be identical to the base model.

**Root cause.** The active chat template (unsloth's `qwen3-thinking`, configured via `get_chat_template(tok, "qwen3-thinking")` in `training/train_qwen3_qlora.py`) lacks the `{% generation %}...{% endgeneration %}` Jinja markers that `tokenizer.apply_chat_template(return_assistant_tokens_mask=True)` requires to identify the assistant span. Without those markers, transformers' fallback returns an all-zeros mask. `SFTTrainer` with `assistant_only_loss=True` then writes `-100` to every label position. Visible only via diagnostic-time decoding — the warning is emitted at startup but eclipsed by Unsloth's own startup output (`return_assistant_tokens_mask==True but chat template does not contain '{% generation %}' keyword.`).

**Relation to Unsloth bug #3383.** Same failure family, more severe symptom: #3383 reported markers *misplaced* on Qwen3-Instruct-2507 (`{% generation %}` in the wrong position, masking the wrong span). Here the markers are *entirely absent* from the qwen3-thinking template, so 100% of the assistant span is masked rather than the wrong subset.

**Fix decision deferred** to a fresh session. Three candidates, each with different methodology consequences:

- **F1.** Add `{% generation %}` markers to unsloth's `qwen3-thinking` template. Highest precision; modifies a vendor template; Jinja-edit risk under fatigue.
- **F2.** Drop the `get_chat_template(...)` call and use the official `Qwen/Qwen3-4B-Thinking-2507` tokenizer's default chat template. Test whether it contains the markers; if yes, use directly. Simplest; requires full re-run of diagnostics 4.1, 4.2, 4.3 to verify other rendering behavior didn't shift.
- **F3.** Disable `assistant_only_loss=True`; train on full-sequence loss (system + user + assistant). Wastes signal on conditioning-prediction; standard practice for many SFT setups; affects v1↔v2 comparability since v1 used `assistant_only_loss=True` per DESIGN.md §7.

**Open question that may reframe the v1 post-mortem.** Did v1 training run under this same all-masked mask? If so, v1's reported final losses (NuminaMath 0.726, OpenR1 0.385, Frugal 0.190) couldn't have come from gradient flow through the assistant span — they'd be measuring something else (system + user prediction, or batch-averaged across pad positions). v1's degenerate output across all three arms would then have a different root cause than the truncation hypothesis assumed: zero-signal training rather than corrupted-label training. Tomorrow's first investigation: git history on `training/train_qwen3_qlora.py` at the v1 SFT commit (and any earlier prepare/train script revisions) to confirm whether the same `get_chat_template("qwen3-thinking")` path was used, and whether the rendered v1 training data had the same all-masked behavior.

---

## Experiment Queue

What's planned. The "on deck" row is the single source of truth for what runs next; everything below it is provisional and will be re-evaluated after each completed run.

> **Rows here describe *planned* runs, not measured results.** "Hypothesis" and "Expected outcome" are predictions written *before* the run. Measured results live in the **Results Summary** table and the per-run subsection under **Run Details**. When a queued run completes, it moves out of this table.

| # | On deck? | Hypothesis | Variable changed | Held fixed | Expected outcome | Decision rule |
|---|---|---|---|---|---|---|
| 07-SC | **yes** | Self-consistency with N=8 samples per question on v1 (sig-figs patched) lifts overall accuracy via majority-vote noise reduction (Wang et al. 2022). Should also blunt the id=48-class ambiguous-gold issue (vote reflects which equivalent form the model leans toward most often). | single-sample → N=8 majority-vote | engine vLLM, slice `fixed_50_v1`, prompt v1, max_new_tokens 16384, sampling defaults | Overall +3-8 pp vs Run 05's 70.0% (i.e. 73-78%). Agreement-rate distribution informative: high-agreement-wrong items are calibration failures, low-agreement-correct items are where SC is doing real work. | Promote SC as part of submission pipeline if overall ≥ Run 05 + 4 q (per DESIGN.md §1.11). Cost is N× per question — at the full-set scale that's ~32 min × 8 ≈ 4 hr / ~$3 on Pod B; tractable. If SC underperforms or doesn't clear bar, the next move is training (SFT or RL), not more prompt work. |

**Dropped from queue post-Run-06:** Runs 07 (16k token-budget test), v3-concise, v4-checking. Reasoning: Run 05 already used 16k cap and Insight 1 confirmed the cap-vs-accuracy story (cutoffs drop, median item unaffected). v3 and v4 were planned negative controls *if v2 had been a winner*; without a winner to validate sweep methodology against, running them now is busywork at $0.10 + 20 min each. Can revisit if a future prompt experiment surprises us.

---

## Data Slices

A slice is the **deterministic** question set a run uses. Slices are first-class identifiers — comparing runs means comparing the same slice (or accepting cross-slice noise explicitly).

| Slice ID | N | Definition | Used by |
|---|---:|---|---|
| `data[:5]`     |  5 | First 5 rows of `data/public.jsonl`. | Run 01 |
| `data[:20]`    | 20 | First 20 rows. | Runs 02, 03, 04 |
| `fixed_50_v1`  | 50 | **Locked.** 17 MCQ + 33 free stratified from `data/public.jsonl`. RNG seeds: MCQ pool = 42, free pool = 43 (per-pool independence; see `scripts/build_slice_fixed_50_v1.py`). ID list at [`data/slices/fixed_50_v1.json`](data/slices/fixed_50_v1.json). MCQ ids: 48, 53, 54, 121, 129, 142, 154, 223, 332, 340, 364, 403, 634, 830, 891, 974, 1023. Free ids: 29, 56, 93, 156, 169, 195, 199, 218, 231, 243, 269, 446, 570, 577, 581, 599, 610, 668, 671, 701, 712, 759, 766, 782, 785, 844, 893, 922, 936, 960, 1040, 1078, 1081. | Runs 05, 06, planned 07-SC |
| `private_test` | TBD | Released on submission day. | Submission runs only. |

### Slice rules

- A slice's id list is locked once any run uses it. Edits = a new slice with a new ID (e.g. `fixed_50_v2`).
- All slice ID lists live under `data/slices/<id>.json` as an explicit list of question IDs (not Python ranges).
- Stratified slices store the seed alongside the id list so the draw is reproducible.
- Cross-slice comparisons need an uncertainty band, not an equality claim.

---

## Known Issues

Tracked here so they don't surface mid-run at the worst possible time. Address opportunistically before any run >50 q.

### Pod A — Notebook

- **Dead `MAX_TOKENS = 32768` knob in cell 7.** Generation actually uses `DEBUG_MAX_NEW_TOKENS` defined locally in cell 20 (currently 8192). Risk: someone changes `MAX_TOKENS` expecting it to take effect. Either delete the unused config or wire it through.
- **`tokenizer.padding_side = 'left'` not set.** Single-sequence inference is unaffected, but any future batched generation on Pod A will silently produce wrong outputs without left padding. (Pod B/vLLM handles padding internally — this is a Pod A-only concern.) Set this before the first Pod A batched run, not after.
- **No per-item incremental save.** Cell 26 writes results only after the full loop completes. A crash at question 800/1126 loses all 800 prior generations. Convert to per-item append-mode write before scaling past ~50 q on Pod A.
- **No CSV submission generator.** `COMPETITION.md` §Submission requires `id,response` CSV with proper double-quoting; current pipeline only writes JSONL. Needed before the first private-set run.
- **Stale display in cell 26 output** (`Saved … run02_baseline_20_tok4096.jsonl`) — `OUTPUT_PATH` in cell 7 is now `run03_tok8192_20.jsonl`; the saved file matches the new path, only the printed text is stale. Self-resolves on the next full run.

### Pod B — vLLM script

- **`VLLM_USE_V1=0` is required.** vLLM 0.8.5 on this pod fails to initialize under the V1 engine. `scripts/run_vllm_experiment.py` sets this env var before importing `vllm`; any new vLLM script must do the same. If this becomes a problem in a future vLLM upgrade, see [`SETUP.md`](SETUP.md) Pod B section.
- **No per-item incremental save.** `scripts/run_vllm_experiment.py` writes the full JSONL only after the entire batch completes (same shape as the Pod A notebook issue). vLLM's batched scheduling makes per-item streaming awkward, but a "stream completed requests as they finish" path is feasible via `LLM.generate(..., use_tqdm=False)` + the `RequestOutput.finished` flag. Implement before any vLLM run ≥100 q so a mid-batch crash doesn't lose hours of generation.
- **No CSV submission generator on Pod B path either.** Same gap as Pod A — currently no `id,response` CSV writer matching `COMPETITION.md` §Submission. Should land in one place that both pods can call.

### Instrumentation provenance

When comparing across runs, only Run 03+ numbers are *measured*. Earlier rows are estimates or floors.

| Run | cutoffs | gen_tokens | gen_secs | per-item save | Reliability |
|---|:-:|:-:|:-:|:-:|---|
| 01 | ✗ (not tracked) | ✗ | ✗ | ✗ | Smoke-test only; cutoff column is `?`. |
| 02 | est. (post-hoc by counting missing `\boxed{}`) | ✗ | ✗ | ✗ | Cutoff count is an estimate, not a measurement. |
| 03 | ✓ | ✓ | ✓ | ✗ | First run with reliable per-item stats. Lacks crash-safe save. |

---

## Submissions

Track every leaderboard submission here. Kaggle limits: 3/day, 2 final selections.

| # | Date | Run ID | Slice | Local accuracy | Leaderboard accuracy | Gap | Notes |
|---|------|--------|-------|----------------|----------------------|----:|-------|
| 1 | 2026-05-04 | run08v2_v1_private943 | full 943 | N/A (gold withheld) | 0.586 | N/A | v1-baseline (sig-figs patched), single sample, 16k tok; first Kaggle submission |
| 2 | 2026-05-04 / 2026-05-05 | run10_v3perslot_private943 | full 943 | N/A (gold withheld) | 0.424 | N/A | v3-perslot per-slot multi-answer format → −16.2 pp; format effect, model reasoning preserved |
| 3 | 2026-05-05 | expA_run08_perslot_perturbed | full 943 | N/A (gold withheld) | 0.420 | N/A | diagnostic: Run 08 responses with multi-answer reformatted per-slot → confirms format alone causes regression |

When the gap between local and leaderboard accuracy exceeds ~5pp, treat it as a **calibration problem first** (slice mismatch, scoring mismatch, parser mismatch, prompt-divergence between dev and submission run) — not a model problem. Investigate before spending another submission.

---

## Calibration vs Published Baselines

Run 03 = 50% overall on n=20 at 8k tokens. **Not directly comparable** to published Qwen3-4B-Thinking benchmarks:

- Different problem distribution (CSE 151B mix of high-school → graduate vs AIME25 / MATH / etc.)
- Different token budget (8k here vs typical 16k–32k in papers)
- Different sampling (matched to model card defaults, but per-paper choices vary)

The *Frugal Reasoning* paper (Table 5) reports base Qwen3-4B at 8k on AIME25 ≈ 13%. The CSE 151B mix is easier than AIME25, so 50% on 8k is unsurprising — but the same paper shows accuracy climbing substantially as the token cap rises through 16k–32k. **A jump in Run 04 (16k) should be expected from "unclamping a known ceiling" alone**, not attributed to other factors. Note this so a 16k overall accuracy jump doesn't get falsely credited to whatever else is changed alongside.

---

## Token Budget Notes

For thinking models, `max_new_tokens` is an **accuracy variable**, not only a runtime/cost variable. If generation is cut off before the final `\boxed{...}` appears, the scorer marks the response wrong even when the reasoning was correct.

**Cutoff** = generation hit `max_new_tokens` before a `\boxed{}` was found in the output.

When comparing token budgets, hold prompt, data slice, sampling params, and model fixed — change only `max_new_tokens`.

Decision rule after each run:
- Cutoffs > 0 → run same slice at 2× token budget before changing anything else
- Cutoffs = 0 → token budget is not the bottleneck; move to prompt or method experiments

---

## Run Details

### Run 01 — Smoke test

**Rationale:** First run ever. Goal was to verify the pipeline works end-to-end — model loads, prompt builds, generation runs, scorer doesn't crash. Used only 5 questions to keep it fast. Token cap of 2048 was a conservative placeholder; we knew it might be too short for a thinking model but didn't want to wait long on a smoke test.

- **Slice:** `data[:5]` — 2 MCQ, 3 free-form
- **Engine:** Transformers + TextStreamer

| param | value | note |
|-------|------:|------|
| max_new_tokens | 2048 | capped: `min(MAX_TOKENS=32768, 2048)` |
| sampling | default | per Locked Defaults |
- **Runtime / cost:** untracked
- **Results:** [starter_results.jsonl](results/starter_results.jsonl)

**Observations:**
- Pipeline works end-to-end.
- `max_new_tokens=2048` may cut off reasoning mid-thought.
- Cutoffs not tracked (added to summary table as `?`).
- Sample too small to judge quality.

---

### Run 02 — Baseline 20 questions

**Rationale:** Pipeline confirmed working. Scaled to 20 questions and doubled the token cap to 4096 to get a more meaningful baseline before touching the prompt. Post-run, 9/20 responses had no `\boxed{}` at all — strong signal the model is hitting the cap before finishing. This makes the 4096 baseline effectively a floor, not a real score.

- **Slice:** `data[:20]`
- **Engine:** Transformers + TextStreamer

| param | value | note |
|-------|------:|------|
| max_new_tokens | 4096 | |
| sampling | default | per Locked Defaults |
- **Runtime / cost:** untracked
- **Results:** [run02_baseline_20_tok4096.jsonl](results/run02_baseline_20_tok4096.jsonl)

**Observations:**
- MCQ 3/9 = 33.3% | Free 6/11 = 54.5% | Overall 9/20 = 45.0%
- 9/20 responses had no `\boxed{}` — all marked wrong.
- Likely many cutoffs at 4096 tokens before model finished thinking and wrote final answer.
- gen_tokens / gen_secs not tracked this run; cutoff count is an estimate.
- **Decision applied:** cutoffs > 0 → double budget → Run 03.

---

### Run 03 — Token budget test

**Rationale:** Run 02 had 9/20 missing `\boxed{}`. Inspection of the raw tails confirmed every single one was cut off mid-sentence — not a prompt failure, just running out of tokens. Per the decision rule (cutoffs > 0 → double budget), Run 03 doubles to 8192 with everything else held fixed.

- **Slice:** `data[:20]`
- **Engine:** Transformers + TextStreamer

| param | value | note |
|-------|------:|------|
| max_new_tokens | 8192 | 2× Run 02 |
| sampling | default | per Locked Defaults |
- **Runtime:** ~131.9 min for 20 questions (mean 395.7 s/q).
- **Cost est.:** ~$1.52 on the 4090 at $0.69/hr.
- **Results:** [run03_tok8192_20.jsonl](results/run03_tok8192_20.jsonl)

**Observations:**
- Overall 10/20 = 50.0% (up from 45.0%; +1 question correct = within noise on n=20, see Insight 1).
- MCQ 4/9 = 44.4% (up from 33.3%); one previously-cutoff question (id=4) now completed and correct.
- Free-form 6/11 = 54.5% (unchanged); two newly-completed free-form items were still wrong (reasoning errors, not cutoffs).
- gen_tokens: mean=5466, p50=5895, p95=8192, max=8192.
- 6 responses hit the 8192-token cap with no `\boxed{}` — **5 of 6 are MCQ** (Insight 2).
- Critical: at 395.7 s/q, a full 1126-question run takes ~124 hrs and costs ~$85. Pod B (vLLM) batching is required before any run >50 q (Insight 3).
- **Decision applied:** original plan was to double again to 16k. Superseded by Pod B coming online — 16k token-budget test is now optional Run 07, deferred until vLLM cutoff behavior is known. Next run is the vLLM parity comparison (Run 04).

---

### `run_vllm_smoke_5_tok8192` — Pod B infrastructure validation

**Rationale:** First end-to-end vLLM run on Pod B after the V0-engine workaround (`VLLM_USE_V1=0`) was identified. Goal: confirm `scripts/run_vllm_experiment.py` loads the model under vLLM, batches the 5 prompts, and produces `\boxed{}`-bearing outputs that the existing `Judger` can score. **This is an infrastructure check, not an accuracy experiment** — n=5 is too small for any cross-run comparison and the result is excluded from the Insights numbers.

- **Slice:** `data[:5]` — 2 MCQ, 3 free-form
- **Engine:** vLLM 0.8.5 (V0), BF16, no quantization, gpu_memory_utilization=0.85

| param | value | note |
|-------|------:|------|
| max_new_tokens | 8192 | matches Run 03 cap for later comparison |
| sampling | default | per Locked Defaults |
| `VLLM_USE_V1` | `"0"` | required on this pod (see Known Issues) |

- **Runtime:** 103.3 s wall-clock for batch of 5 (20.7 s/q amortized).
- **Results:** [run_vllm_smoke_5_tok8192.jsonl](results/run_vllm_smoke_5_tok8192.jsonl) + sidecar `.summary.json`.

**Observations:**
- Pipeline runs end-to-end: vLLM loads → batched generate → `\boxed{}` extraction → `Judger.auto_judge` → JSONL + summary written.
- Overall 3/5 = 60.0% (1/2 MCQ, 2/3 free-form). **Not comparable to Run 03** at n=5.
- Cutoffs 0/5 and missing `\boxed{}` 0/5 at 8k. avg_gen_tokens=4332 (vs Run 03's 5466). Both findings are interesting but unreliable at n=5 — see Insight 5 caveats.
- Wall-clock 20.7 s/q vs Run 03's 395.7 s/q ≈ 19× faster on this batch size. This is a *floor* on the speedup for batched runs; per-question time under vLLM is dominated by the slowest item in the batch, so the multiplier is not stable across batch sizes.
- **Decision applied:** Pod B is operational. Promote Run 04 (vLLM parity on `data[:20]` at 8k) to "on deck".

---

### Run 04 — vLLM parity vs Run 03

**Rationale:** First apples-to-apples Pod A↔B comparison. Same slice, prompt, sampling, and effective generation budget as Run 03; the only changes were the inference backend (Transformers → vLLM 0.8.5 V0) and quantization (BnB-INT4 → BF16/none). Goal: confirm vLLM is safe to adopt as the default engine for runs ≥50 q and learn whether the Run 03 MCQ-cutoff pattern persists under vLLM/BF16.

- **Slice:** `data[:20]` (9 MCQ + 11 free-form, identical to Runs 02–03)
- **Engine:** vLLM 0.8.5 (V0), BF16, no quantization, gpu_memory_utilization=0.85

| param | value | note |
|-------|------:|------|
| max_new_tokens | 8192 | matches Run 03 |
| max_model_len | 16384 | gives full 8192-token gen budget regardless of prompt length; matches Pod A's effective budget. See Locked Defaults / Token-budget semantics. |
| sampling | default | per Locked Defaults |
| `VLLM_USE_V1` | `"0"` | required on this pod |

- **Runtime:** 162.4 s for 20 questions (8.1 s/q). Started 02:31:58 UTC, finished 02:35:49 UTC. ≈ $0.03 on the 4090 at $0.69/hr.
- **Results:** [run04_vllm_parity_20_tok8192.jsonl](results/run04_vllm_parity_20_tok8192.jsonl) + [.summary.json](results/run04_vllm_parity_20_tok8192.summary.json)

**Pre-registered comparisons — all four passed:**

| # | Metric | Run 03 | Run 04 | Pass band | Result |
|---|---|---:|---:|---|:-:|
| 1 | Overall accuracy | 50.0% (10/20) | 50.0% (10/20) | ±5pp of 50% | ✅ exact |
| 2 | MCQ accuracy | 44.4% (4/9) | 44.4% (4/9) | ±5pp of 44.4% | ✅ exact |
| 3 | Cutoffs | 6/20 | 6/20 | ≤ 6 | ✅ exact |
| 4 | Throughput | 395.7 s/q | 8.1 s/q | ≥5× faster | ✅ 48.7× |

**Observations:**

- **Aggregate parity is exact**, but **per-item agreement is only 18/20 (90%)**:
  - id=14 (MCQ): Run 03 cut off at 8192 → wrong. Run 04 finished at 7803 → correct.
  - id=19 (MCQ): Run 03 finished at 4704 → correct. Run 04 ran into a new cutoff at 8192 → wrong.
  - The two flips cancel exactly, leaving 10/20 unchanged. This is partly chance (sampling at n=20 quantizes to 5pp steps) and partly real engine-induced variance — see Insight 6.
- **Cutoff count is identical (6) but composition shifted:** Pod A = 5 MCQ + 1 free; Pod B = 4 MCQ + 2 free. Pod B "fixed" id=14 (MCQ) and "broke" id=19 (MCQ) and id=16 (free, finished cleanly under Pod A but cut off under vLLM). MCQ-cutoff pattern survives the engine swap; Insight 2 holds.
- **Token usage is ~10% lower under vLLM/BF16:** avg_gen_tokens 4899 vs 5466. Distribution: min=1017, p50=4154, p95=8192, max=8192. Most items use noticeably fewer tokens (id=0: 2383→1750, id=5: 5834→3800, id=8: 6745→3624, id=17: 5895→2836); a few use more and tip into cutoffs. BF16 numerics produce somewhat shorter `<think>` blocks on average but with higher variance than INT4 — both for better and for worse.
- **Speed is the headline:** 48.7× faster than Pod A on this slice. Full-set extrapolation: 1126 q × 8.1 s/q ≈ 152 min ≈ $1.74 wall-clock cost (compute cost ≈ $0.30 — most of the difference is dominated by Pod A's cost when used; on Pod B at this throughput the full set is genuinely cheap). Pod B is cleared as the default engine for all runs ≥50 q.
- **Decision applied:** vLLM adopted as default engine. Run 04 row removed from Queue; Run 05 (vLLM 50-q baseline) promoted to "on deck". Insight 5 updated to record the measured 48.7× (replacing the n=5 floor estimate of 19×). New Insight 6 added on engine-induced per-item variance.

---

### Run 05 — Prompt-sweep anchor on `fixed_50_v1` at 16k

**Rationale:** Establish the n=50 anchor for the v1/v2 prompt sweep on the locked `fixed_50_v1` slice. Bundles **three changes vs Run 04** (slice `data[:20]` → `fixed_50_v1`, gen budget 8k → 16k, prompt v1-baseline → v1 with sig-figs patch). Bundling explicitly accepted: this run is *not* a clean A/B for any single axis. Token-budget choice (16k) was made on prior evidence (Frugal Table 5 + Run 04's unresolved 6/20 cutoffs at 8k); skipping a clean 8k→16k pre-check at n=20 is theater whose outcome wouldn't change the next action. Subsequent runs (06+) hold slice + cap fixed and vary only the prompt.

- **Slice:** `fixed_50_v1` (17 MCQ + 33 free, seed=42, locked)
- **Engine:** vLLM 0.8.5 (V0), BF16, no quantization, gpu_memory_utilization=0.85
- **Prompt:** v1-baseline with 2026-05-03 sig-figs revision (see Prompt Versions)

| param | value | note |
|-------|------:|------|
| max_new_tokens | 16384 | doubled from Run 04's 8192 |
| max_model_len | 24576 | gives full 16384-token gen budget regardless of prompt length |
| sampling | default | per Locked Defaults |
| `VLLM_USE_V1` | `"0"` | required on this pod |

- **Runtime:** 650.1 s = 10.8 min for 50 questions (13.0 s/q). Started 16:53:51 UTC, finished 17:06:24 UTC. ≈ $0.13 on the 4090.
- **Results:** [run05_v1_50_tok16384.jsonl](results/run05_v1_50_tok16384.jsonl) + [.summary.json](results/run05_v1_50_tok16384.summary.json)

**Observations:**

- Overall **70.0% (35/50)**. MCQ **82.4% (14/17)**. Free-form **63.6% (21/33)**.
- **Cutoff rate dropped 30%→8%** vs Run 04 (6/20 → 4/50). 16k locked as the operating point. Three of four remaining cutoffs are MCQ — Insight 2 reinforced, see Run 06 for the prompt-side test.
- Avg gen tokens **4871** (essentially flat from Run 04's 4899) despite doubling the cap. p50=3536, p95=16384, max=16384, min=522. **Most items don't use the extra budget**; only the long-tail items benefit. Insight 1 updated.
- One vLLM KV-cache preemption warning (sequence group 48, `PreemptionMode.RECOMPUTE`). Single occurrence; no correctness impact, only some wasted compute. Watch for pattern at larger n or longer caps.
- First end-to-end use of `--slice` and `--prompt-version` infrastructure (commits b7701cd, b777480). Schema additions in summary (`slice_id`, `slice_path`, `slice_n`, `system_prompt_mcq`, `system_prompt_free`) all populated correctly.
- Run 04's id=5 (the original sig-figs-patch motivation) is **not in `fixed_50_v1`**, so the patch's effect on the original failure case is untestable from this slice. Live with it; don't burn a slice draw to test a single item.
- **Bundling caveat reminder:** the +20pp overall vs Run 04 cannot be attributed to any single change. Run 06 is the first clean prompt A/B; comparisons against Run 05 should hold the bundling in mind.

- **Decision applied:** Run 05 locked as the prompt-sweep anchor. Run 06 (v2-mcq-commit, prompt-only change vs Run 05) promoted to "on deck". 16k cap held for all subsequent prompt-sweep runs. Insight 1 extended with the cap-doesn't-help-median finding; Insight 2 to be revisited after Run 06.

---

### Run 06 — v2-mcq-commit prompt A/B vs Run 05

**Rationale:** First clean prompt A/B in the sweep. Holds slice (`fixed_50_v1`), engine (vLLM/BF16), cap (16k), and sampling defaults fixed against Run 05 — the *only* change is the MCQ system prompt (free-form prompt is byte-identical to Run 05's). Tests whether the v2-mcq-commit instruction *"Stop generating immediately after `\boxed{}`"* reduces the engine-independent MCQ-cutoff pattern (Insight 2) by forcing earlier commitment.

- **Slice:** `fixed_50_v1` (identical to Run 05)
- **Engine:** vLLM 0.8.5 (V0), BF16

| param | value | note |
|-------|------:|------|
| max_new_tokens | 16384 | matches Run 05 |
| max_model_len | 24576 | matches Run 05 |
| prompt | v2-mcq-commit | only change vs Run 05 |
| sampling | default | per Locked Defaults |
| `VLLM_USE_V1` | `"0"` | required on this pod |

- **Runtime:** 666.0 s = 11.1 min (13.3 s/q). Started 17:16:59 UTC, finished 17:29:29 UTC. ≈ $0.13.
- **Results:** [run06_v2mcq_50_tok16384.jsonl](results/run06_v2mcq_50_tok16384.jsonl) + [.summary.json](results/run06_v2mcq_50_tok16384.summary.json)

**Pre-registered comparisons (vs Run 05) — neither passed:**

| # | Metric | Run 05 (v1) | Run 06 (v2) | Pass band | Result |
|---|---|---:|---:|---|:-:|
| 1 | MCQ accuracy | 14/17 = 82.4% | 13/17 = 76.5% | +4 q (DESIGN.md §1.11) | ❌ −1 q |
| 2 | Free-form accuracy | 21/33 = 63.6% | 20/33 = 60.6% | within ±2 q | ✅ −1 q |

**Observations:**

- Overall **66.0% (33/50)**: −2 q vs Run 05's 70%, well within the ~±5 q noise floor at n=50 (sampling + engine + ambiguous-gold; see Insight 6 + 7). v2-mcq-commit is **not promoted**.
- Same-slice per-item agreement vs Run 05: **48/50.** Only 2 flips, both v1-correct → v2-wrong:

  | id | type | v1 (Run 05) | v2 (Run 06) | v1_tok | v2_tok | Δtok | classification |
  |---|---|---|---|---:|---:|---:|---|
  | 48  | MCQ  | ✓ → I (gold) | ✗ → E         | 6162 | 1627 | −4535 | **ambiguous gold** (id=48 class — see below + Insight 7) |
  | 199 | free | ✓             | ✗             | 1005 | 921  | −84   | **sampling variance** — free-form prompt byte-identical between v1 and v2 |

- **id=48 is the high-leverage finding.** The integral evaluates to `(2/3) ln 9`. Options included **E** = `(2/3) ln 9` (exact form) and **I** = `(4/3) ln 3` (simplified via `ln 9 = 2 ln 3`). Both correct. Gold is I. v1 spent ~4500 extra tokens noticing the equivalence and meta-reasoning *"in most calculus problems they expect the logarithm to be simplified to its prime base"* — picked I, won. v2 sanity-checked the computation with two substitution methods, picked E (the form matching its computed result), lost. **This is question-design ambiguity, not a v2 prompt failure.** v2 didn't cause premature commitment; it just didn't do the test-author-intent meta-reasoning. Drives Insight 7.
- v2 **did** shift behavior as designed: p50 gen tokens dropped 3536 → 3075 (−13%); min dropped 522 → 379 (−27%). The "stop immediately after `\boxed{}`" instruction is being followed.
- But **0 of Run 05's 3 MCQ cutoffs were converted to correct answers under v2.** v2's MCQ cutoff count dropped 3 → 2 — but the item that "stopped cutting off" is still wrong (committed to a wrong answer instead of running out of tokens). v2 traded a cutoff-wrong for a commit-wrong on that item. **No structural progress on the MCQ-cutoff cluster.** Insight 2 updated to call the pattern "structural, not prompt-engineerable at this cap."
- Avg gen tokens 4772 (vs Run 05's 4871). Distribution: min=379, p50=3075, p95=16384, max=16384.
- Throughput +2.5% slower (13.3 vs 13.0 s/q) despite shorter individual responses — vLLM batching means saved tokens on individual MCQ items don't trade for runtime savings; the long-tail items still dominate the wall clock.

- **Decision applied:**
  - v2-mcq-commit not promoted; remains in the registry but won't be the default. The MCQ-cutoff pattern is not addressable via prompt at 16k cap; the next high-leverage move is sample-level (self-consistency) or training-level.
  - Drop v3-concise and v4-checking from the queue. They were planned negative controls *if v2 had been a winner*; without one, they're busywork.
  - Run 07-SC (self-consistency on v1, N=8, same slice) promoted to "on deck".
  - Insight 2 rewritten as "structural" finding. Insight 6 extended with the n=50 same-slice flip evidence (id=48, id=199). New Insight 7 added on the ambiguous-gold floor with id=48 as the canonical example.
  - **Process improvement applied:** wrong-answer audit before behavioral conclusions (CLAUDE.md > Data & Analysis Discipline). Skipping it on Run 06 cost ~5 min of misguided "Hypothesis A vs B" speculation about v2 causing premature commitment, before realizing id=48 was an ambiguous-gold case where v2's pick was mathematically equivalent to gold.

---

### Submission 1 Analysis (Run 08-v2 → Kaggle 0.586)

> **[Superseded 2026-05-05 by Submission 2 + Submission 3 Analysis below.]** This section's central thesis — that Run 08-v2's 0.586 was bottlenecked by multi-answer format failure against `judger.py`'s list-match scoring, and that ~10-15 pp could be reclaimed by per-slot boxing — was directly falsified by Run 10 (per-slot, scored 0.424) and Experiment A (format-only perturbation of Run 08-v2 → 0.420). Local `judger.py` does not model Kaggle's grader. Read on for the original analysis as written; the corrected rule lives in [`CLAUDE.md`](CLAUDE.md) > Scoring (Judger).

#### Result

- First Kaggle submission: Run 08-v2 (v1-baseline, single sample, 16k tok, full 943 private set)
- Public LB score: **0.586** (58.6% on ~30% sample of private set, n≈283, ±5pp 95% CI)
- Significantly below local `fixed_50_v1` estimate of 70%

#### Key data points from response analysis ([run08v2_v1_private943_tok16384.jsonl](results/run08v2_v1_private943_tok16384.jsonl))

**Cutoff rate:** 119/943 (12.6%) hit 16k token cap before producing `\boxed{}`

- MCQ: 52/300 (17.3%) — model over-thinks multiple choice
- Free-form: 67/643 (10.4%)

**Format failure rate:** 115/943 (12.2%) responses have no parseable boxed answer

- 100% of missing-boxed items ARE cutoffs (no items where model "finished but forgot to box")
- Format failure and cutoff are the same problem mechanically

**Token length distribution:**

- median: 4,863 tokens
- mean: 6,602 tokens
- p90: 16,384 (already at cap)
- p95: 16,384
- MCQ median: 7,618 tokens (vs free-form median: 3,423) — MCQ over-thinks
- 13.3% of items at 16k cap

**MCQ format quality:** 250/300 (83.3%) of MCQ items have clean single-letter boxed answer

- Upper bound on MCQ accuracy from format alone is ~83.3% (the rest are cutoffs)

**Multi-answer free-form items: 338/943 (35.8% of dataset)**

- These have multiple `[ANS]` placeholders and are pass/fail (all sub-answers must be correct)
- Distribution of slot counts: 142×2-slot, 76×3-slot, 58×4-slot, 23×5-slot, 17×6-slot, 5×7-slot, 8×8-slot, etc.
- Model behavior on multi-answer items is wildly inconsistent:
  - Some produce 1 box with comma-separated answers (e.g. id=448 slots=2 last_box=`'x^3-4x^2-6x+30, x^2-9x+20'`)
  - Some produce N boxes for N slots (e.g. id=87 slots=3 total_boxed=15)
  - Some produce N intermediate boxes through reasoning, ending on a fragment (e.g. id=129 slots=4 total_boxed=32 last_box=`'\dfrac{5'`)
  - Some produce a single-letter box for multi-slot questions (e.g. id=225 slots=4 total_boxed=8 last_box=`'A'`)

#### Judger behavior (verified by reading [`judger.py`](judger.py))

The Judger's `extract_all_boxed` returns the LAST CONTIGUOUS GROUP of `\boxed{...}` blocks. Two boxes are "contiguous" if separated only by whitespace, commas, punctuation, `$`, or common separators. Any non-whitespace text (e.g. mid-reasoning text) breaks the contiguous group.

For multi-answer items, gold is stored as a list of strings (e.g. id=12 gold=`['380','315','13','310']`). Judger expects N separate `\boxed{...}` blocks at the end matching N gold elements. A single `\boxed{a, b, c}` produces a length-1 list and FAILS the gold list match.

#### Local public-set diagnostic ([run05_v1_50_tok16384.jsonl](results/run05_v1_50_tok16384.jsonl))

Re-analyzed Run 05's 7 wrong multi-answer items on `fixed_50_v1`:

- 6 of 7 are FORMAT failures (single comma-sep box vs gold's list-of-strings, or intermediate boxes breaking contiguity)
- 1 of 7 is dataset gold formatting bug (id=701: gold=`['0','0','(2,3)','NONE']` has nested commas)
- 0 of 7 are pure reasoning errors

If format-only failures were fixed, Run 05 would have scored ~41/50 = 82% (vs measured 70%).

#### Implications

True model capability on the test distribution is likely **70-75%**, not 58.6%. Format engineering (per-slot boxed for multi-answer + no intermediate boxes during reasoning) is the largest available lever, not self-consistency or model training.

Estimated error decomposition for the 0.586:

- Multi-answer format failures: ~10-15 pp
- Cutoffs (auto-zero items): ~6-8 pp (subset includes MCQ over-thinking)
- Genuine model errors: ~15-20 pp

#### v1-baseline prompt instruction that's structurally incompatible with Judger

> "If the problem has multiple sub-answers, separate them by commas inside a single \boxed{}, e.g. \boxed{3, 7}"

This produces a length-1 boxed group, but Judger expects N elements for an N-slot gold list. This single instruction likely accounts for the bulk of multi-answer scoring losses.

---

### Submission 2 Analysis (Run 10 → Kaggle 0.424)

#### Result

- Second Kaggle submission: Run 10 (v3-perslot, single sample, 16k tok, full 943 private set)
- Public LB score: **0.424** (42.4% on ~30% sample of private set, n≈283, ±5pp 95% CI)
- **−16.2 pp regression** vs Run 08-v2's 0.586 on identical 943 questions
- Submission date: 2026-05-04

#### What v3-perslot changed vs v1-baseline

The free-form prompt was rewritten to make multi-answer outputs satisfy local `judger.py` extraction:

- ONE separate `\boxed{...}` per `[ANS]` slot, in question order
- Banned `\quad`, `\qquad`, `$`, `$$`, and any LaTeX command between consecutive boxes (these break `judger.py`'s contiguous-group regex — gap text containing letters disqualifies the group)
- No `\boxed{}` during reasoning — final answers only
- MCQ prompt unchanged from v1-baseline

Designed under the hypothesis (now falsified) that Run 08-v2's 0.586 was bottlenecked by multi-answer format failure against `judger.py`'s list-match scoring.

#### Head-to-head diagnostic (Run 08-v2 vs Run 10, 943 items each)

**Aggregate gen behavior:**

- Avg gen tokens: Run 08-v2 = 6,602 → Run 10 = 6,269 (−5%)
- Cutoffs at 16k cap: Run 08-v2 = 119 → Run 10 = 110 (slight improvement)

**Per-question extraction agreement:**

| Type | n | Same extracted_list | Reading |
|---|---:|---|---|
| MCQ | 300 | 253 (84.3%) | Reasoning stable — model not broken |
| Single-answer free | 305 | 233 (76.4%) | Reasoning stable |
| Multi-answer free | 338 | 48 (14.2%) | Format swung as designed |

The 86% disagreement on multi-answer items is structurally expected — v3-perslot was engineered to produce a different format. MCQ + single-answer agreement near 80% confirms the underlying model reasoning is stable across the two runs; the −16.2 pp swing is not a regression in capability.

**Multi-answer format flip:** 209 of 338 multi-answer items moved from a length-1 extracted_list (Run 08-v2, e.g. `["143, 2.33"]`) to a length-N extracted_list (Run 10, e.g. `["143", "2.33"]`).

#### Score-prediction test

Under the hypothesis that Kaggle's grader takes only the **last** `\boxed{...}` and string-matches against gold-as-string:

- Predicted Run 10 score: **0.438**
- Actual Run 10 score: **0.424**
- Gap: 1.4 pp, within the ±5pp 95% CI on n≈283

The hypothesis fits the data. Caveat: Kaggle's grader code is not directly visible — other extraction logic could also fit, but no simpler model has been proposed.

#### Conclusion

Local `judger.py` does NOT match Kaggle's actual grader. The "extract last contiguous group → list-match positionally" logic was treated as a faithful proxy for Kaggle scoring; Run 10 falsifies that assumption.

The v1-baseline format (one `\boxed{...}` containing comma-separated values matching the gold string) was already correct for Kaggle. v3-perslot moved away from a correct format toward a `judger.py`-compliant one and lost 16.2 pp.

#### Implications for forward strategy

- Run 08-v2 (0.586) remains the strongest single-sample submission. Discard the v3-perslot direction.
- Run 09-SC (Pod B, v1-baseline + N=8 self-consistency, in progress, expected to finish 2026-05-05 afternoon) is the next clean experiment — it uses v1-baseline format so its outcome is interpretable.
- Future prompt iterations should hold the v1-baseline single-box multi-answer format fixed and experiment on other axes.
- Don't trust local-judger reverse-engineering as a model of Kaggle's grader. Submit-and-measure when scoring assumptions matter.

---

### Submission 3 Analysis (Experiment A → Kaggle 0.420)

#### Result

- Third Kaggle submission: Experiment A (`expA_run08_perslot_perturbed`)
- Public LB score: **0.420** (42.0% on ~30% sample of private set, n≈283, ±5pp 95% CI)
- **−16.6 pp** vs Run 08-v2's 0.586; **+0.4 pp** vs Run 10's 0.424 (within noise)
- Submission date: 2026-05-05
- Cost: $0 (no GPU; pure CSV perturbation in Python)

#### Method — controlled format perturbation, no inference

Took Run 08-v2's exact JSONL response file. For each multi-answer item where the last `\boxed{...}`'s comma-split count matched the slot count, programmatically rewrote that last box from `\boxed{a, b, c}` into per-slot `\boxed{a} \boxed{b} \boxed{c}`.

- 242 of 338 multi-answer items reformatted (those with unambiguous comma split)
- 96 of 338 multi-answer items left **byte-identical** to Run 08-v2 (no clean comma split available)
- All 605 non-multi items (300 MCQ + 305 single-answer) left **byte-identical** to Run 08-v2

Reasoning traces, MCQ outputs, and single-answer outputs were unchanged at the byte level. The ONLY difference vs Run 08-v2: the multi-answer last-box format on 242 items.

#### Why this experiment

Run 10's regression (Submission 2 Analysis) was correlational — both prompt and outputs differed between Run 08-v2 and Run 10. The "Kaggle takes only the last `\boxed{}`" hypothesis fit Run 10's score within noise (predicted 0.438, actual 0.424), but the run also had different reasoning paths, different cutoffs, different generation behavior — any of which could partly explain the −16.2 pp.

Experiment A isolates format as the lone variable. If format is the entire causal mechanism, Experiment A should score very close to Run 10. If reasoning differences were partly responsible for Run 10's regression, Experiment A should score noticeably higher than Run 10 (closer to Run 08-v2).

#### Result confirms format alone

- Experiment A: **0.420**
- Run 10: **0.424**
- Difference: 0.4 pp, within ±5pp 95% CI on n≈283

The two scores are statistically indistinguishable. With reasoning content held byte-identical for 605 of 943 items and only multi-answer last-box format changed on 242 items, the score collapse from 0.586 → 0.420 is attributable **entirely** to the format change. Run 10's −16.2 pp regression was not partly explained by reasoning drift — it was the format change in full.

#### Conclusion

Strongest evidence yet that local `judger.py` does not model Kaggle's actual grader and that the v1-baseline single-comma-separated `\boxed{}` format is the right one for Kaggle. The "Kaggle takes only the last `\boxed{}` and string-matches against gold-as-string" hypothesis remains the simplest fit; no simpler model has been proposed and no evidence so far contradicts it.

Operational implication: do not use per-slot multi-answer formatting in any future submission. The v1-baseline format is the locked multi-answer format until a different scoring assumption is positively demonstrated.

---

## Prompt Versions

### v1-baseline

**Free-form:**
```
You are an expert mathematician. Solve the problem step-by-step. Put your final answer inside \boxed{}. If the problem has multiple sub-answers, separate them by commas inside a single \boxed{}, e.g. \boxed{3, 7}. Give numerical answers to at least 4 significant figures, unless the problem specifies a different precision.
```

**MCQ:**
```
You are an expert mathematician. Read the problem and the answer choices below, then select the single best answer. Output ONLY the letter of your chosen option inside \boxed{}, e.g. \boxed{C}.
```

**Revisions:**

- **2026-05-03 patch — sig-figs line for free-form.** Added to the free-form prompt: *"Give numerical answers to at least 4 significant figures, unless the problem specifies a different precision."* Motivated by Run 04 id=5 (model `62.78` vs gold `62.7778` failed). Investigation of `judger.py` (`Judger.judge_single_numerical_value`, lines 738–790) confirmed the failure is a true rounding mismatch under the Judger's 1.01e-8 relative tolerance, not a config issue. MCQ prompt unchanged. **Used by:** Run 05+. Runs 01–04 used the pre-patch prompt (without the sig-figs line).

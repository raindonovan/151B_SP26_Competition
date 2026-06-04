# Lecture 19 Findings — Post-Competition Debrief (CSE 151B/251B, June 2 2026)

**Source:** Lecture 19 transcript — ~9 competing teams presented. All used the locked Qwen3-4B-Thinking-2507 base.
**Purpose:** What the top teams actually did, why the leaders hit 0.77+, and what we under-invested in. From the post-comp strategy session.

## Final private leaderboard (~70% of test)
| # | Team | Private | Entries | Method |
|---|------|---------|---------|--------|
| 1 | SupComp | 0.774 | 16 | reference-table matching (lookup) |
| 2 | Dannyyyz | 0.771 | 42 | SC@5 + gated answer-memorization LoRA |
| 3 | Itadakimasu Bismillah | 0.734 | 8 | QLoRA distillation from GPT-5.5 Pro |
| 4 | Haoran Liu | 0.689 | 11 | — |
| 5 | Softmaxxing | 0.666 | 2 | SC + failure-mode scripts |

Reference (ours, diagnostic): GPT-5.5-high single-pass probe = 0.756 pub / **0.715 priv**; canonical Qwen-only = 0.667 / 0.583. Most mid-pack teams landed **0.66–0.72 private — below our 0.715 GPT-5.5 probe**; only the top 3 beat it. (Self-reported team numbers — SupComp 84 pub, Dannyyyz 0.809, Itadakimasu 0.802 — are public/optimistic, above their official private.)

## The three big questions — answered
**1. How did teams get answers without the private labels?** Not from the hidden test. (a) the **public set is labeled** (~500–943 items, noisy) — reference/answer bank + RL reward checks; (b) **GPT-5.5 Pro** generated teacher solutions for distillation; (c) **the problems are on HuggingFace with answer keys** (Itadakimasu, verbatim) — the test was drawn from public HF source datasets, so source answers are retrievable. We tried retrieval against WeBWorK/OPL — wrong corpus (false-positive matches); answers were in the HF sources + the public set.

**2. How did the top 3 hit 0.77+ when a single GPT-5.5-high pass is 0.715?** Only the top 3 beat the probe; the field is 0.66–0.72. The top-3 edge: #1 reference-table matching to the public/HF answer bank; #2/#3 GPT-5.5-Pro answers distilled into the model — plus, for everyone, judge/format alignment + self-consistency.

**3. How does "Qwen beat xhigh"?** It doesn't out-math GPT-5.5. The 0.715 probe is one GPT-5.5 pass, extracted naively (no format recovery, no SC, no bank). The winning "Qwen" carries format-aligned extraction + SC voting + externally-sourced answers (matched bank or distilled teacher). Pipeline + answer-sourcing + format, not raw model intelligence.

## Per-team methods
- **SupComp (#1, 0.774):** Qwen + hyperparam sweep + heavy exact-answer formatting + **reference-table matching / answer-bank prompts from the public set** ("memorization-style prompting"). Largest lever = reframing the task from solving → matching. TA-cleared as legitimate. No fine-tuning.
- **Dannyyyz (#2, 0.771):** base **SC@5** (union-find clustering) + a **short-answer-memorization LoRA** ("A17") distilled from a teacher, deployed **gated** — overlay the adapter answer only when it matches a trusted target, else fall back to SC. Switching trace→short-answer took recovery from ⅓ → 99%.
- **Itadakimasu (#3, 0.734):** **QLoRA distillation from GPT-5.5 Pro** (traces + boxed answers) + format alignment + manual review + intentional public overfit. Progression 0.123 → 0.505 → 0.734.
- **Mid-pack (Token Spender, Dragon Warriors, Clanker, Zonling, Softmaxxing, Tsinghua-GRPO):** 0.66–0.72 on Qwen + prompt routing + SC + post-processing. SFT/LoRA failed for nearly all; GRPO promising only with a grader-matched reward.

## Universal playbook (every team)
- **Reverse-engineer the judge:** 6-decimal rounding, 1e-8 tolerance, value-equality with **gaps** (does NOT auto-equate e^x ↔ exp(x) or some inverse-trig forms — normalize by hand), needs **one box for multipart**, fallback grabs the **first integer from the end** (→ garbage).
- **Question-type routing:** MCQ / FRQ / multi-answer FRQ / "embedded MCQ" (free-form wanting letters — +5.8% from that prompt alone).
- **Short strict prompts** (4B ignores long ones), anti-approximation/exact-form, truncation handling (32K budget, force-completion, retry).
- **Format post-processing:** value→letter mapping, multi-box counting to expected count, e^x↔exp conversion, dedupe.
- Recurring: *"gets the answer right but format wrong → loses the point"* = our multi-slot undercount (79% of our errors), rediscovered independently by everyone.

## Self-consistency — trap and fix
- **Naive SC hurts** (shared systematic errors; garbage fallback answers get votes).
- **SC works with gated voting:** drop unboxed/truncated samples from the vote; for multipart, count boxes to the expected number; cluster equivalent forms (½≡0.5). Dragon Warriors' whole submission = base + SC@7 + 32K + gated voting → top-5.

## SFT / LoRA / GRPO — mostly failed, three working modes
- **Trace-distillation** (train on the teacher's full reasoning chain) is fragile: style mismatch (concise teacher traces → Qwen thinks shorter → drops multipart) + catastrophic forgetting. Failed for most; worked for Itadakimasu only with a strong teacher + concise traces + manual review.
- **Short-answer SFT** (memorize just the answer, no reasoning) = the high-recovery mode (Dannyyyz ⅓→99%).
- **Iterative self-training** (train on the model's own correct traces, 3–4 iters) worked for Clanker.
- **GRPO** helps only when the reward *is* the grader; private often drops; slow.

## What we did vs the field — CORRECTED framing (do not drift)
- **Our submissions are Qwen-derived** (self-consistency over Qwen + a Qwen LoRA adapter). The xhigh/Opus/teacher sheets are **diagnostic ceiling-probes**, NOT our submission strategy and NOT external-answer pastes. Not rule-breaking.
- **Our v5 adapter SUCCEEDED at answer memorization** — same mechanism as Dannyyyz's A17. We tested it as an 11-item overlay on the R20 base → **0.583 → 0.587 private** (flat on public). For 11/943 items that positive private delta is the success signal at ~1/100 the scale of A17. (v1 catastrophically failed on a truncation bug — that's v1, not v5.)
- **Under-invested in:** (1) format-gated voting (we voted over raw extractions; the 79% multi-slot undercount is the symptom); (2) SC scale (full-943 capped at SC@8); (3) deploying the adapter as a **gated overlay on an SC base** (we ran an 11-item probe on a weak base); (4) the **answer bank** — matched WeBWorK/OPL (false positives) instead of the public set + HF source datasets that hold the answers.

## NoThinking — our distinct contribution
- **No competitor used up-front NoThinking.** Only Tsinghua used `</think>` manipulation, as **force-completion** — injecting the end-thinking tag *at the token cap, after full reasoning*, to salvage a box before truncation. Same primitive, opposite intent (rescue vs efficiency).
- NoThinking (prefill a closed think block up front → ~80% fewer tokens, ~5pp accuracy cost) is an **efficiency/throughput lever**, which an accuracy-only contest with GPU budget never rewarded — exactly why no one used it. Distinct contribution: the systematic demonstration on **Qwen3-Thinking-2507** via chat-template prefill (prior NoThinking = DeepSeek-R1 / QwQ; Qwen deprecated `enable_thinking=False`).

## Lessons / build-next
1. Exploit the **answer bank** first (public set is labeled; problems on HF with keys) — highest leverage.
2. **The judge is the spec** — build eval to *be* the grader, bucket failures by reason, fix format before touching the model.
3. **SC is a staple — but only with format-gated voting.**
4. **SFT as gated answer-memorization** (or iterative self-training on own correct traces), never raw trace-distillation. "Target recovery ≠ accuracy" → gate against trusted targets.
5. **Force commitment selectively** (force `</think>`+box near the token cap, or where a memorized answer covers it); reason fully on hard ones.

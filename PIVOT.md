# Strategic Pivot (2026-05-11)

**This is a high-level pointer.** Full context lives in `DESIGN.md`. Read DESIGN.md §3.6 (active work), §4 status callout (deferred work), and §7 status header (deferral rationale) for the in-context version.

## Summary

Phase 3 (training) v1 was attempted 2026-05-06 across three SFT arms (OpenR1-Math-220k, NuminaMath-1.5 concise, Frugal-Thinking traces). All three arms failed catastrophically — truncation catastrophe at `max_seq_length=4096` (see `SESSION_LOG.md` 2026-05-06 entry). Rather than committing to a Phase 3 v2 effort with the sketched fixes, the project pivoted to extend Phase 2 (self-consistency) with a focused V0-V4 prompt-engineering ablation.

## Status of project phases

- **Phase 1 (prompt engineering):** Concluded. Ceiling at 70% on `fixed_50_v1` with v1-baseline. See DESIGN §1.18.
- **Phase 2 (self-consistency):** Active, extended. Run 09-SC (N=8) scored 0.614 on Kaggle. V0-V4 ablation extends Phase 2 — see DESIGN §3.6.
- **Phase 3 (training / SFT):** Deferred. v1 failed 2026-05-06; v2 plan sketched but not scheduled. See DESIGN §4 status callout and §7 status header.

## Active design docs

- `prompt_engineering_research.md` — research basis and locked implementation plan (Section 7) for V0-V4.
- `variants_and_prompts.md` — concrete implementation spec for V0-V4.
- `DESIGN.md` §3.6 — V0-V4 framed in the context of DESIGN.md's broader plan.

## Phase 3 artifacts preserved (do not delete)

- `training/train_qwen3_qlora.py` — QLoRA training script.
- `training/prepare_openr1_sft.py`, `training/prepare_numina_sft.py`, `training/prepare_frugal_sft.py` — data prep for the three arms.
- `training/merge_adapter.py` — LoRA → BF16 merge for vLLM serving.
- `training/checkpoints/` — completed v1 adapters and merged models.
- `data/sft/` — generated training datasets.

## When Phase 3 might resume

DESIGN.md §4.5 has the decision tree. Phase 3 v2 becomes the next major move only if:

- The V0-V4 ablation plateaus below a useful Kaggle score, AND
- A v2 SFT recipe addressing truncation, system prompt mismatch, and chat template issues is drafted (see SESSION_LOG.md 2026-05-06 entry's "v2 fixes for tomorrow" list).

This pivot is a redirection, not a final answer on training.

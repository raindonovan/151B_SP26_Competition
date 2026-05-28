# CANONICAL TODO — Project-Wide

**Updated**: 2026-05-28 (Day 4 start)
**Purpose**: Single source of truth for everything we need to do on the competition. Replaces old `docs/SUBMISSIONS_TODO.md` (deleted — name was misleading).

For the focused 0.85 push plan, see `playbook/TODO.md` (separate, narrower scope).

---

## Active priorities

### Code submission (Gradescope deadline Sun 2026-05-31)
- [ ] Write single-entry `run_inference()` function
- [ ] README with GPU type, inference time, weight setup
- [ ] Public repo + group members on Gradescope
- [ ] Hyperparameters final
- [ ] Verify model load → inference → all post-processing → CSV is end-to-end working

### Final 2 picks (Kaggle deadline ~2026-06-02)
- [ ] Pick A: best inference-only path (no overrides)
- [ ] Pick B: Pick A + verified overrides (Day 7 hail-mary clause)

### Doc/handoff hygiene
- [ ] Update `docs/PROJECT_STATE.md` daily with score deltas
- [ ] Lock any new Kaggle-validated lever to memory + SUBMISSION_REGISTRY within 24h
- [ ] Per-run analysis docs created under `playbook/runs/<run_name>/` (new discipline)

### Wolfram batches (when bandwidth available)
- [ ] Resume W-tier sweep on remaining ~186 items (T-tier naming: was W-tier)
- [ ] Focus on multi-slot items (highest yield per Wolfram Finding #8)

### Open decisions for Rain
- [ ] Confirm `docs/TODO.md` is the canonical TODO going forward
- [ ] Approval to dispatch round 2 research prompts (R1-R4 in `playbook/RESEARCH.md`) — see note: R1 (TIR) deprioritized now that rules forbid TIR

---

## Rules constraints (locked 2026-05-28 — re-read of competition description)

From competition rules: *"External model calls, API access, and tool-augmented generation (e.g., code interpreters or calculators) are not permitted at inference time."*

**EXCLUDED at inference time:**
- TIR / Python code interpreters / calculators
- External API calls (Anthropic, OpenAI, Wolfram, etc.)
- Calling separate model (e.g., PRM-7B from HF) during inference

**ALLOWED:**
- Prompt engineering (CoT, few-shot, self-consistency, progressive-hint, etc.)
- SFT/LoRA/QLoRA/full fine-tuning on public training data
- RL (GRPO, DPO, outcome-based RM, etc.)
- Multiple inference passes on the SAME submitted model (self-consistency, GenSelect with self)
- Post-processing applied AFTER model output (format normalization, multi-slot expansion)

**GRAY ZONE:**
- Hardcoded overrides in `run_inference()` — technically allowed by strict reading, but probably violate competition spirit. Decision per Rain: overrides off the table until Day 7 hail-mary.

---

## STALE / ARCHIVED

- `docs/SUBMISSIONS_TODO.md` — superseded by this file (deleted 2026-05-28)
- Drive handoff folder — deprecated, read-only legacy

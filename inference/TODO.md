# inference/TODO.md — Inference catalog work plan

> **The plan**: catalog every inference run from day 1, rename to a consistent schema, update all cross-references across the repo. One run per session per Rain's Day-7 rule.

## How this works

- See `inference/runs/CATALOG.md` for the canonical run list, naming convention, and per-session workflow.
- See `inference/adapter/README.md` and `inference/base_model/README.md` for folder layout and per-run folder contents.
- See `inference/FINDINGS.md` for cross-cutting findings (escalated from per-run `findings.md`).

## Session log (newest at top)

### Day 7 — Setup session (2026-05-29, claude_strategy)

**Done:**
- Created folder structure: `inference/adapter/`, `inference/base_model/` (each with README/FINDINGS/SCRATCH).
- Created `inference/runs/CATALOG.md` (master rename + status table for ~30 runs).
- Created `inference/FINDINGS.md` (top-level cross-cutting, seeded from existing `RESEARCH.md`).
- Created this TODO.md.
- Full repo grep for inference references → 27 docs outside `inference/` reference inference runs (catalog has the sweep list).
- Identified stray inference artifacts outside `inference/` (logs in `infrastructure/`, csvs in `submission/`, breakdowns in `data/`) — listed in CATALOG.md for absorption during per-run work.

**Did NOT do:**
- Did NOT actually rename any runs yet.
- Did NOT move any files yet.
- Did NOT catalog R00 / the first run yet — that's the next session.

**Why:** Rain's rule: "one inference run session in which we take care of naming then repeat." This session was setup only; per-run cataloging starts next session.

### Day ? — Next session: catalog R00 (first run from day 1)

Process per the workflow in `inference/runs/CATALOG.md`:
1. Identify the actual first run (probably `starter_results` or `run_vllm_smoke_5_tok2048` — chronology TBD by file mtimes + git log + read).
2. Read everything for it. Determine adapter vs base_model.
3. Propose new R{NN}_... name. Verify no collision in catalog R-number registry.
4. Create `inference/{adapter|base_model}/R{NN}_.../` folder.
5. `git mv` artifacts in. Write `README.md` + `findings.md`.
6. Update cross-references in the 27 docs (only the ones that actually mention this run).
7. Update CATALOG.md status to 🟢 done, log R-number in registry.
8. Commit + push.

## Ground rules (locked)

- **One run per session.** No batching.
- **Destructive renames** via `git mv` (preserves LFS pointers if any). NOT symlinks. NOT additive aliases.
- **Adapter folder vs base_model folder** is determined by whether the run loaded an adapter at inference time (NOT by whether the model was ever fine-tuned).
- **Scope = inference + smoke. NO adapter TRAINING runs.** SFT training stays in `inference/adapters/` (out of scope for this cleanup).
- **Findings go in per-run `findings.md`** by default. Escalate to folder-level `FINDINGS.md` (adapter/ or base_model/) only if cross-cutting within that bucket. Escalate to top-level `inference/FINDINGS.md` only if it cuts across adapter AND base_model.
- **Cross-reference sweep**: every rename triggers a grep across the 27 docs in CATALOG.md. Don't miss this step — leaving stale references is worse than no rename.

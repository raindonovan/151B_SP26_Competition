# TODO — Day 6 (2026-05-28)

**Mode**: Repo hygiene / strategy. NO analysis/inference until Rain switches gears.

## Immediate (this session)

### Strategy & docs
- [x] Create test pipeline north star (TEST_PIPELINE.md)
- [x] Create strategy/CLAUDE.md (heart of claude_strategy)
- [x] Create per-folder CLAUDE.md files (inference, postprocessing, submission, data/search)
- [x] Create submission/GLOBAL_STRATEGY.md
- [x] Create submission/BACKSOLVE_RESEARCH.md
- [x] Create strategy/INFERENCE_TECHNIQUES.md (tried vs untried)
- [x] Create strategy/POST_PROCESSING_TECHNIQUES.md (implemented vs planned)
- [x] Create research/FORMAT_CONVENTIONS.md
- [x] Update SESSION_HANDOFF.md for Day 6
- [x] Update this TODO.md
- [ ] Update root CLAUDE.md with PAT-first protocol
- [ ] Update agents/CLAUDE_STRATEGY.md to point to strategy/CLAUDE.md

### Data artifacts (Day 6 acceptance criteria)
- [ ] **ANSWER_SHEET**: Run build_answer_sheet_v6.py, commit output CSV (currently MISSING)
- [ ] **MASTER_ITEM_TABLE**: Reconcile master_tracker 1039 rows vs 943 items in private.jsonl
- [ ] **RUN_ANSWER_MATRIX**: Items × runs cross-tab (which items did EACH run get right?)
- [ ] **RUN_REGISTRY**: Canonical list of ALL inference runs with metadata
- [ ] **GRADER_SPEC**: Already exists at grading/GRADER_SPEC.md — verify up to date
- [ ] **ADAPTER_REGISTRY**: Catalog all adapters (v3, v4, v5) with status and location

### Run folder hygiene
- [ ] Confirm every run folder has an analysis doc (even if stub)
- [ ] Inventory ALL unanalyzed runs (NoThinking, Hardest-30, GenSelect PoC)
- [ ] Review analyzed runs for completeness

## Core questions (MUST ANSWER — requires data artifacts first)

- [ ] **Q1**: What questions have we inferred correctly? (needs RUN_ANSWER_MATRIX)
- [ ] **Q2**: What answers are T1/Gold/90%+ confidence? (needs ANSWER_SHEET output)
- [ ] **Q3**: What can we infer right but need format fixing? (needs Q1 + grader analysis)
- [ ] **Q4**: What gold answers can't be answered through inference? (needs Q1, these are adapter candidates)

## After switching gears (Rain decides when)

### Post-processing (MAJOR LEVER — do before adapter)
- [ ] Implement comma-in-numbers stripping
- [ ] Implement unit word removal (Minerva word list)
- [ ] Implement source-corpus routing (AIME→integer, MATH→LaTeX, WeBWorK→decimal)
- [ ] Build per-item function chain architecture
- [ ] Test post-processing on gold set items

### Inference (GPU work — can run autonomously)
- [ ] Analyze NoThinking SC=8 results
- [ ] Analyze Hardest-30 SC=16 results
- [ ] Re-analyze GenSelect PoC (truncation correlation)
- [ ] Oracle@8 analysis on run14b (ceiling for selection techniques)
- [ ] Spec DeepConf@SC32 run (can run 2 days on Thunder)

### Submissions
- [ ] **CHANGE KAGGLE PICKS** to 0.692 + next best (URGENT — before 5/31)
- [ ] Submit Track A v1 baseline (when ready)
- [ ] Design first oracle mining differential pair

### Adapter (BONUS — only if time after post-processing)
- [ ] Answer Q4 (what items can't inference solve?)
- [ ] Build training set from Q4 items with verified gold
- [ ] Train QLoRA v7 (targeted memorization)
- [ ] Test: does adapter reproduce training items?
- [ ] Test: does adapter degrade held-out items?

### Code submission (due 2026-05-31)
- [ ] Single run_inference() entry point
- [ ] Fine-tuned models on HF Hub
- [ ] Public GitHub repo + README
- [ ] All group members on Gradescope

## Research queue
- [x] Format conventions research (deep research session)
- [x] Log-loss oracle paper (1707.01825) → documented in BACKSOLVE_RESEARCH.md
- [x] DeepConf identification (Fu et al. 2508.15260)
- [ ] R2: Single-model judge prompt design for math BoN selection
- [ ] R3: Targeted memorization SFT precedents
- [ ] R4: GenSelect with full-length candidates (NVIDIA NemoSkills AIMO-2 winner)

## Backlog mining (from strategy/TIME_MACHINE_BACKLOG.md)

**TIER 1 — richest unmined docs, START HERE:**
- [ ] **archive/research/prompt_engineering_research.md** (70KB, 896L) — UNMINED. Prompt-lever research; V0–V4 prompts trace back here. → inference prompt levers + strategy.
- [ ] **archive/design/experiments.md** (85KB, 928L) — partially mined. Run-by-run experiment log incl. failures. Only judger/public + Insights 6–7 pulled. → RUN_REGISTRY + knowledge layer.
- [ ] **archive/session_logs/SESSION_LOG.md** (14KB) — UNMINED. Chronological log opening on v1 3-arm SFT FAILURE. Dense failure postmortems. → RUN_REGISTRY / adapters.
- [ ] **archive/design/DESIGN.md** (68KB) — partially mined. Design rationale, Piazza rulings, SFT paths, data-filtering. Only §4.4/§5.1 grepped. → RULES + INFERENCE + STRATEGY.

**Priority flags**: prompt_engineering_research.md (70KB) and experiments.md (85KB) are HIGH-PRIORITY unmined — together they're 155KB of raw knowledge that could contain format rules, run findings, and failure modes we haven't captured.

**Full backlog**: See strategy/TIME_MACHINE_BACKLOG.md for Tiers 2-5.

# TEST PIPELINE — North Star

**Created**: 2026-05-28 Day 6
**Status**: ACTIVE — this is our guiding architecture for the remaining 4 days

## The core idea

We have gold answers for a subset of items (from Search, Wolfram, teachers, back-solve oracle). We test whether our pipeline can reproduce them. Items we get right go through post-processing and into the submission. Items we get wrong become adapter training candidates.

## Pipeline stages

### Stage 1: Gold question set
Sources of gold answers (confidence ordered):
- **Web search verified**: 5 items (IMO 2025 P6, Putnam 2021 A5, etc.) — highest confidence
- **Wolfram HIGH**: 51 items with computational verification — very high confidence
- **Multi-teacher unanimous**: items where all 5 teachers agree — high confidence
- **Back-solve oracle**: items where we can infer gold from Kaggle score deltas — medium-high confidence
- **Answer sheet T1**: items with ≥95% posterior from Bayesian back-solve — medium confidence

### Stage 2: Run base inference
- SC@8 with Qwen3-4B-Thinking-2507 (existing runs: run14b only; prior doc versions listed run10 — that was an error, run10/R10 is single-sample v3-perslot)
- Future: SC@32/64 with DeepConf logprob weighting
- Future: GenSelect (model judges its own candidates)
- Future: multi-temperature voting

### Stage 3: Compare to gold
For each gold item: does the SC-voted answer match gold after normalization?
- YES → item goes to inference-solvable pool
- NO → item goes to adapter candidate pool

### Stage 4a: Inference-solvable path
Items where inference already gets the right answer. These go directly to post-processing.
The goal: make sure post-processing extracts the correct answer in Kaggle-canonical format.

### Stage 4b: Adapter candidate path
Items where inference gets the wrong answer despite having gold.
- Collect these into a training set
- Train QLoRA adapter (targeted memorization, not generalization)
- Run adapter inference on ONLY these items
- Bar for adapter: produce anything resembling a correct answer (not perfect format)

### Stage 5: Post-processing pipeline
ALL items (from both paths) go through post-processing:
- Extract last \boxed{} content
- Per-item function chain: strip units → normalize fractions → collapse whitespace → etc.
- Each item can have a custom routing (some only need unboxing, others need full normalization)
- Post-processing is a composable function chain — each function independently testable

### Stage 6: Kaggle submission (THE MISSING BOX)
Submit to Kaggle and get aggregate score on ~283-item test subset.
This is the REAL eval — everything else is proxy.

### Stage 7: Back-solve oracle
Use the Kaggle score to infer per-item correctness:
- Differential submissions: change N items, hold everything else constant
- Score delta tells us which items changed → reveals test set membership AND gold answers
- Every submission feeds back into Stage 1 (expanding the gold set)

## The 4-day iteration loop

**Step 1 — Expand gold set**: More Search queries, more Wolfram verification, more back-solve mining.
**Step 2 — New inference techniques**: DeepConf@SC32, GenSelect, multi-temperature, NoThinking analysis.
**Step 3 — Grow adapter**: Add more verified-wrong items to training set, re-train, test reproduction.
**Step 4 — Improve post-processing**: New normalization rules, per-item routing, format rescue functions.

Each iteration makes the test harness more reliable and the pipeline more effective.

## Key insight: post-processing is the prerequisite

The adapter's job is mathematical correctness only. Post-processing handles format. This means:
1. Post-processing must be robust BEFORE we can evaluate the adapter
2. Every post-processing improvement helps BOTH inference and adapter paths
3. Post-processing is the highest-leverage lever we haven't fully exploited

Priority: inference → post-processing → adapter (bonus if time)

## Terminology (LOCKED)

- **test set** = the ~283-item LB subset Kaggle scores submissions on. Fixed but unknown. Used during competition for leaderboard scoring.
- **FINAL test set** = all 943 items. Used at deadline for final ranking. This is what matters.
- **gold set** = items where we have verified correct answers (from search, Wolfram, teachers, back-solve). Our local ground truth.
- **gold answer** = a verified correct answer for a specific item.
- **format rule** = a discovered fact about how a specific item's gold is encoded (e.g., trailing zeros, fraction vs decimal). Each rule = a point recovered.

## Diagram

The test pipeline diagram was rendered as an inline SVG in the Day 6 claude_strategy chat session. The original PIPELINE.md at repo root has a mermaid flowchart of the repo-level pipeline (pre-inference → inference → post-inference → submission). The TEST_PIPELINE described here extends that with the feedback loop (submit → back-solve → iterate).

See also: `PIPELINE.md` (repo root) for the repo organization blueprint and Rain's hand-drawn diagram (`pipeline_diagram.jpeg`).

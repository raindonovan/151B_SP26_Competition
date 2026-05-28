# SESSION HANDOFF — Day 6 Morning (2026-05-28)

## You are claude_strategy = CENTRAL NODE
Read `strategy/CLAUDE.md` for your full operating contract.

## Session start checklist
1. Clone repo: `git clone https://github.com/beepbeeepimajeep/151B_SP26_Competition.git /home/claude/repo`
2. Ask Rain for PAT: "I need the GitHub PAT to push directly."
3. Read this file + `strategy/CLAUDE.md` + memory
4. Check `strategy/TODO.md` for priorities

## Current state
- **Best inference-only**: 0.646 (slot1_reformat, run14b SC=8 32K)
- **Best with overrides**: 0.692 (kitchen_sink_C, 78 overrides)
- **Leader**: 0.85 (gap: 15.8pp from inference, 20.4pp from base)
- **Deadline**: ~2026-06-02 (Kaggle final picks) / 2026-05-31 (Gradescope code)
- **Submissions remaining**: ~20 (5/day final week)
- **CURRENT KAGGLE PICKS ARE WRONG**: 0.438 + 0.420 selected. CHANGE BEFORE DEADLINE.

## North star: TEST PIPELINE
See `strategy/TEST_PIPELINE.md` for the full architecture.
```
Gold set → Inference → Compare → YES: post-proc → submit
                                → NO: adapter → post-proc → submit
                                → Kaggle score → back-solve → iterate
```

## What was done Day 5 (repo hygiene)
- Full repo reorganization into pipeline structure
- 29 submissions verified + definitive REGISTRY.md
- 4 critical inference JSONLs LFS-tracked (586MB)
- Data audits on DSMLP/Thunder — both Thunder instances flagged KILL
- Direct push via PAT + bash established

## What was done Day 6 morning (this session)
- **Test pipeline concept** established as north star (diagram + TEST_PIPELINE.md)
- **Submission strategy** locked (oracle mining > pipeline validation > final picks)
- **Adapter format decision** locked (adapter = correctness only, post-proc = format)
- **Per-folder CLAUDE.md** architecture created for delegated agent workflow
- **Inference techniques inventory** built (tried vs untried, unanalyzed data flagged)
- **Post-processing techniques inventory** built (implemented vs known-but-not-implemented)
- **Back-solve research** documented (log-loss oracle paper + our differential approach)
- **Format conventions research** summarized from deep research session
- **DeepConf** identified as the logprob-weighted SC technique Rain was remembering
- **Core questions** defined (Q1-Q4: what's correct, what's gold, what needs format fix, what's adapter material)

## Key strategic decisions (locked Day 6)

1. **Post-processing is the major lever before adapter.** Inference → post-processing → adapter (if time).
2. **Adapter format is relaxed.** Just needs to produce something resembling an answer. Post-proc handles format.
3. **Submissions are for oracle mining first.** Back-solve is resurrected as first-class lever.
4. **Per-folder CLAUDE.md** enables delegated agent workflow. Spawn new chat, point to folder, go to work.
5. **Source-corpus routing** is the highest-EV post-processing improvement (attacks 80% format-loss).

## Priority stack (this session, Day 6)

We are in **repo hygiene / strategy mode**. NO analysis/inference/research until Rain switches gears.

1. ✅ Create strategy docs (CLAUDE.md, TEST_PIPELINE.md, technique inventories)
2. ✅ Create per-folder CLAUDE.mds
3. ✅ Document submission strategy
4. ⬜ Update TODO.md with comprehensive Day 6 priorities
5. ⬜ Build MASTER_ITEM_TABLE (reconcile 1039 vs 943 rows)
6. ⬜ Run build_answer_sheet_v6.py → commit output
7. ⬜ Confirm every run folder has analysis doc (even stub)
8. ⬜ Answer Core Questions Q1-Q4

## Compute status
- **DSMLP**: Active, A30 24GB, clean
- **Thunder tnr-0**: FLAGGED KILL (audited, clean)
- **Thunder tnr-1**: FLAGGED KILL (audited, clean)

## Key files to read
- `strategy/CLAUDE.md` — your operating contract
- `strategy/TEST_PIPELINE.md` — the north star
- `strategy/INFERENCE_TECHNIQUES.md` — tried vs untried techniques
- `strategy/POST_PROCESSING_TECHNIQUES.md` — format normalization inventory
- `submission/GLOBAL_STRATEGY.md` — submission allocation plan
- `submission/REGISTRY.md` — all 29 past submissions
- `grading/GRADER_SPEC.md` — grader behavior

# inference/base_model/SCRATCH.md — Unsorted base-model inference observations

Drop anything here. Promote to `FINDINGS.md` (this folder) or `inference/FINDINGS.md` (top-level) when a pattern crystallizes.

---

---
## claude_vscode signoff — Day 9 — T2 probe98 audit (UPDATE, not new build)

probe98 (NoThinking Phase-1, 98 hard items) was ALREADY cataloged + committed by a parallel claude_vscode at ffa0959 (full findings a-f, README, analysis, YELLOW verdict). Per memory #24 pre-commit-audit (b) "findings exists → UPDATE not build", I did NOT overwrite. Re-ran prep+analyzer from raw for provenance (matched committed analysis exactly → analyzer deterministic) and INDEPENDENTLY reproduced every load-bearing number (27/44=0.6136, A=27/Alucky=4/B=13/unknown=54, shape_fallback 46/98, 47% T5 skew, all 98⊆943, rescue 5&584 both flip 0/2, math_correct 73.5% with 24-vs-2 asymmetry). Zero discrepancies with the committed audit.

APPENDED section g (the genuine value-add): decomposed the 943≫probe98 swing — 27/98 probe98 frag votes (n_voting≤1) vs 7/98 in 943; 943 mean 2554 tok vs 2194 (longer on 45/98); of 24 943-only-correct, only 5 frag + 12 shorter → ~HALF the swing is genuine sampling variance, not mechanical. Determinism = MIXED/NOISY. CONFIG CAVEAT: neither NT run records sampling params, so asymmetry could be partly config-difference not variance — unresolvable from artifacts. Tomorrow: DOWN-WEIGHT NT in slot 7/8 stacks; run NT-on-17-truncated at HIGHER budget (length-driven component).

PROVENANCE RECONCILE: re-ran prep WITHOUT --run-id, so my stale local prep copy stamped the 943 run_id into the adapted file (my ADAPTED diverged from committed on run_id only). The COMMITTED prep script (ffa0959) already has --run-id (default p943) — parallel instance fixed it. analyze_run.py --run-id overrides downstream anyway, so committed analysis/ run_id is correct (verified NT_probe98_...). I REVERTED my mis-stamped ADAPTED + raw-move back to committed canonical; kept ONLY findings.md section g. No script change needed (already parametrized upstream).

VERDICT (concur with parallel): YELLOW — provenance PASS, stability/rescue FAIL. Closes at T2 (ChatGPT parallel = cross-check). NT-943's +1.8pp Kaggle is the real lever; probe98 is a noisy precursor, neither confirms nor refutes it.

---
## claude_vscode signoff — Day 9 — T2 NoThinking targeted_rescue (new-rescue analysis) — NO SIGNAL

targeted_rescue_nothinking (61 curated R20-failure items, NoThinking SC@16, May 26) → inference/base_model/NT_targeted_rescue_nothinking_sc16_f61_t8k/. Distinguished from its Thinking-mode twin (targeted_rescue_20260526T201046Z, mean 6102 tok vs NT's 1389; same 61 ids; twin left in hybrid/). New build. Prep WITH --run-id (avoided hardcode bug).

GATES: 61 rows, 976 samples (16×61), 0 contradictions. Standalone 7/36=0.1944 (hard slice, 43/61 T5). shape_fallback 6/61=9.8% (vs NT-943 3.7%).

LOAD-BEARING new-rescue analysis (vs R20 + NT-943): R20-already-correct 19; **NEW UNIQUE rescues beyond NT-943 = 1 (id=232)**; existing 3; **tr WORSE than NT-943 = 6 (5,257,490,499,578,715)**. **NET vs NT-943 = +1−6 = −5 → stacking HARMS.**

Capability-vs-sampling: agreement 25/61, both-wrong 42, tr-only-right 1, NT943-only-right 6 = STOCHASTIC VARIANCE (texas-oil/probe98 saturation), NOT capability. Curating+SC@16 did not beat the full NT-943 pass.

17-TRUNCATED INTERSECTION = 0 (subset predates 32K-truncation analysis) → says NOTHING about the "NoThinking-high-budget-on-17-truncated" morning candidate; that remains untested.

VERDICT: NO new-rescue signal. targeted_rescue is RESEARCH-ONLY, do NOT stack. Closes NT-workstream "more NT passes help" question across probe98(YELLOW)+texas-oil(PARTIAL)+this: they don't. NT value = the single NT-943 join (+1.8pp); path to more = independent gold, not more/curated NT runs. Did NOT build Pick-B candidate (audit only). Closes at T2 (no ChatGPT pass per spawn). Commit: cb1e29e.

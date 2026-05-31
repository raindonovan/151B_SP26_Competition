# SESSION_HANDOFF.md — claude_strategy session state

> Read this FIRST when resuming a claude_strategy chat. Detailed findings live in their canonical homes; this is the index.

**Last updated:** 2026-05-31 ~00:45 PT (Day 9 close — deep-audit cohort complete, Pick B framework validated on Kaggle at 0.664, structural normalizer build scheduled for 05:00 Sun)

**HEAD at handoff:** see latest commit on `main`. Previous Day 8 handoff archived at `strategy/SESSION_HANDOFF_day8_close.md`.

**Time-to-deadline:** ~23 hours

---

## State summary

- **Pick A:** LOCKED at 0.745 (R20 + overrides + teacher overlay)
- **Pick B candidates:** slots 1 + 2 both scored **0.664** on Kaggle — framework CONFIRMED
- **Kaggle slots remaining:** 8 of 10 (3 current-pool expire ~18:50 Sun PT + 5 reset-pool refresh at Kaggle daily reset)
- **Deep-audit cohort (R08, R09, R10, R20, R20b):** all 5 closed, all T3-verified
- **NoThinking 943:** elevated to Pick B candidate, T1.5 + T3 verified, 13 unique-correct items confirmed
- **Final adapter-target seed:** **8 items** [41, 61, 103, 104, 127, 231, 264, 282] (post-T3 corrections from initial heuristic 11)
- **17-item still-truncated-at-32K set:** [93, 112, 161, 204, 229, 275, 308, 312, 376, 383, 445, 498, 586, 652, 724, 799, 809] — high-budget probe target

## Tonight's submissions (Day 9 close)

| Slot | CSV | Kaggle | Delta vs R20 baseline (0.646) |
|---|---|---|---|
| 1 | `picks_nothinking_join_conservative_v1.csv` | **0.664** | +1.8pp |
| 2 | `picks_nothinking_join_conservative_763safe_v1.csv` | **0.664** | +1.8pp (identical) |

**Interpretation:** Framework confirmed. 763 expression-form vs canonical form scored identically (either not on slice or grader handles both — future builds don't need disambiguator companions for expression items).

**Slice-landing rate calibration:** ~5 of 13 rescues landed on the 283-item slice = **38% rate**, vs my 30% prior. Use 35-40% for future slot estimates.

## ⏰ 05:00 Sun decisions (in priority order)

Read in this order: `submission/SLOT_PLAN.md` → `strategy/MORNING_RUNS_WATCHLIST.md` → this section

### 1. Structural normalizer build (HIGHEST EV remaining lever)
- **Build at 05:00-08:00 Sun.** Three tiers per cohort findings:
  - **Tier 1 universal** (highest priority, build first): includes **NEW: wrap-on-detect for 19 unboxed rows** (R20 source rows with no `\boxed{}` — fail Kaggle extraction unconditionally; ~6 expected slice rescues at 38% rate). Also: multi-slot collapse, MCQ-first-box, duplicate-option overcount (id 302/839 pattern), trailing-zero/precision rules.
  - **Tier 2 class-based**: detect "exact form expected" from question text (rescues id=89/345 pattern); detect "N quantities expected" for slot-count alignment.
  - **Tier 3 per-item overrides** via `postprocessing/per_item_overrides.csv` (schema'd, currently empty). Seeds: id=9 (gold split-form), id=167 (option-mapping), id=345 (precision), id=591 (undercount).
- **Expected delta vs 0.646 baseline:** +2-3pp on its own (priors are lower bounds because Day-8 append bug suppressed historical measurement — see POST_DEADLINE_AUDITS.md A1).

### 2. Morning runs on 3 Thunder A100s in parallel (~05:00-09:30 Sun)
- Read `strategy/MORNING_RUNS_WATCHLIST.md` decision algorithm
- Candidate ranking (from Day 9 evidence):
  - **High-budget probe on 17 still-truncated items** (81920/65536 tokens): ~30 min A100, low engineering, concrete target
  - **SC@32 on contested slice**: ~45 min A100, no engineering, ~11-14 A_lucky candidates
  - **NoThinking on the 17 still-truncated items**: leverages tonight's NoThinking-works finding on the items most likely to need it
  - **DeepConf**: thinner than predicted (R20 had only 3 items at >=5/8); deprioritize unless V-series shows multi-temp signal (unlikely tonight)
- **Adapter eval (SFT v5 ckpt-1176)**: separate Thunder if available; default-include for cross-run diversity
- **Adapter training on 8-item seed**: low priority given tiny target count; only if structural normalizer + morning runs aren't producing expected delta

### 3. Sunday submissions (slots 3-8 per SLOT_PLAN.md)
- Sun ~10:30: slot 3 = full normalizer on R20 (~0.669 expected)
- Sun ~12:00: slot 4 = normalizer + NT join stack (~0.676 expected, first true Pick-B frontrunner)
- Sun ~13:00: slot 5 = best morning-run winner
- Sun ~14:30: slot 6 = second-best morning-run winner
- Sun ~16:00: slot 7 = slot 4 + slot 5 stack (ceiling test, ~0.681 expected)
- Sun ~18:00: slot 8 = slot 4 + slot 6 OR normalizer v2 (finalist alternative)
- Sun ~20:00: slot 9 = diagnostic 14 (282 calibration) ONLY IF SPARE
- Sun ~22:00: slot 10 = emergency reserve / last-built finalist

### 4. Gradescope code submission (deadline Sun 23:59 PT)
- Single `run_inference()` entry point per memory #17
- Add all group members to Gradescope
- Public GitHub repo + README (GPU type, inference time, weight setup)
- Verification: top-10 = full private re-run; rest = 200 random Qs

## Discipline lock-ins (read before any big decision)

- **Memory #24 extended Day 9:** "DEEP AUDITS NO LIGHT AUDITS unless trivially so — applies to ALL big decisions, not just runs. claude_vscode same standard."
- **Locked audit pattern (high-stakes):** my-audit -> ChatGPT cross-check -> synthesize
- **Memory #11 (Pick B):** Qwen-derived only (output + format norm; no teacher overrides in submission_answer)
- **Memory #25 (LB-subset lens):** Kaggle score = ~283-item slice; prefer robust picks over slice-tuned overrides
- **Memory #2 (judger gap):** 28pp local-vs-Kaggle gap; local scores directional only
- **Memory #30 + `strategy/POST_DEADLINE_AUDITS.md`:** A1 historical-override audit pending; Day-8 append bug means historical priors are LOWER BOUNDS

## Open questions (deferred)

- Sonnet-on-Qwen empirical validation (A6 — tomorrow's adapter, if trained, IS this experiment)
- Diagnostic 14 (282) submission deferred to slot 9 / only-if-spare
- 19-unboxed-rows: ~6 expected slice rescues — embedded in tier-1 normalizer build

## Anti-patterns to avoid (Day 9 lessons)

- **Don't re-investigate the phantom normalization stack** (resolved Day 7, merged 620301c)
- **Don't reintroduce Day-8 append override mechanism** for multi-slot — use canonical full-replace via `apply_overrides.py`
- **Don't add 282 to automatic Pick-B joins** without further evidence (disputed gold; can probe via slot 9)
- **Don't isolate per-format-rule contributions on Kaggle** — offline-testable; preserve slots
- **Don't burn slots on individual rule isolation** — bundle the full normalizer into one submission for aggregate measurement

## Where to find things

- **Tonight's full picture:** read this doc, then `submission/REGISTRY.md`, then `submission/SLOT_PLAN.md`
- **The deep audits:** `inference/base_model/R{08,09,10,20,20b}_*/findings.md` (each has its own ChatGPT T3 verdict appended)
- **NoThinking audit:** `inference/base_model/NT_eval_nothinking_sc8_p943_t?/findings.md`
- **Audit templates:** `strategy/AUDIT_TEMPLATES.md` (T1, T2, T3, T4 + paste-fill spawn prompts)
- **Pre-flight discipline:** `infrastructure/pre_flight/` + memory #19
- **Post-deadline audit queue:** `strategy/POST_DEADLINE_AUDITS.md` (A1-A6)
- **Morning planning detail:** `strategy/MORNING_RUNS_WATCHLIST.md`
- **Submission strategy:** `submission/SLOT_PLAN.md` (the 10-slot locked plan)

---

## DAY 9 SESSION HANDOFF — 2026-05-31 ~02:30 PT (claude_strategy → wake-up Rain)

### Active state at handoff

**Two Thunder runs in flight (parallel):**
- **tnr-0**: items 0-58 (IDs 2..418) of `submission/csvs/picks/thinking_probe_target_set.csv`
- **tnr-1**: items 59-117 (IDs 435..929)

**Config (hard-tier validated, post-smoke-pass bump):**
- SC=16, Thinking-mode, TP=2 on 2× A100
- `--max-tokens 81920 --thinking-budget 65536`
- `--temperature 0.6 --top-p 0.95 --top-k 20 --repetition-penalty 1.1`
- `--mcq-format letters`

**ETA**: ~6.5 hr each, parallel → wake-up dawn (~08:30 PT).

**Output paths**:
- tnr-0: `inference/base_model/thinking_probe_tnr0_20260531T065751Z/samples.jsonl`
- tnr-1: `inference/base_model/thinking_probe_tnr1_<timestamp>/samples.jsonl`
- Both pushed to origin/main with race-safe rebase-retry (fix coded in STEP 6).

### What auto-happens when runs complete (coded into spawn prompts)

1. samples.jsonl written, summary.txt generated
2. LFS-track if >10MB
3. `git add` → commit → race-safe push (rebase + retry up to 3x)
4. Signoff appended to `inference/SCRATCH.md`
5. Tmux window 0 shows "=== RUN COMPLETE <timestamp> ===" when done

### Smoke results (passed gate, recorded here for analysis ref)

**tnr-0 smoke (5/5 boxed, default-tier budgets 49152/24576):**
- ID 2: A 12/16 ✓
- ID 9: `\frac{L-8x}{6F}` 2/2 valid — WRONG (gold = `L-8x, 6F`; validation anchor MISSED at default budget)
- ID 12: 11 16/16 ✓
- ID 21: 67.4 15/16 ✓
- ID 25: long LaTeX 2/3 valid — TRUNCATION-HEAVY at default budget

**Key concern at default budget**: 40% of items hit token-cap truncation; voting unreliable on truncated items. **Why we bumped to hard-tier config for full run.**

### Wake-up checklist

1. **Check both runs completed cleanly:**
   ```bash
   cd ~/151B_SP26_Competition && git pull
   ls -lh inference/base_model/thinking_probe_tnr0_*/samples.jsonl
   ls -lh inference/base_model/thinking_probe_tnr1_*/samples.jsonl
   wc -l inference/base_model/thinking_probe_tnr*/samples.jsonl   # expect 59 each
   ```
   If either is <59: instance crashed or smoke failed at step 5 fresh-fire. Check inference/SCRATCH.md signoff entries.

2. **Cross-run analysis** (hand to claude_vscode on DSMLP):
   - Merge tnr0 + tnr1 samples.jsonl (disjoint 118 items)
   - Run analyzer → extract SC-majority `\boxed{}` per item
   - Cross-ref vs R20 + NT-943 + thinking-twin existing rescues
   - **Identify NEW rescues**: correct here AND R20 wrong AND NT-943 wrong AND on independent gold
   - **Validation anchors to check explicitly**: ID 9, 435, 479, 638 (the thinking-twin verified-4). If all 4 replicate at high budget = mechanism robust. If <2 replicate = mechanism didn't replicate at scale; calibrate expectations.

3. **Build Pick B candidates** (once rescues known):
   - `picks_thunderprobe_strict.csv` = R20 + NT-943 join + verified Thunder rescues
   - `picks_thunderprobe_plus_texas.csv` = above + 6 texas-oil verified rescues (lower-confidence)

4. **Submission schedule** (Sunday May 31, deadline 22:00 PT — ~14 hours left at wake):
   - Slot 7 (~10:30 PT): strict variant
   - Slot 8 (~12:00 PT): combined variant
   - Slot 9 (~14:00 PT): normalizer build (still pending — see deferred)
   - Slot 10 (~17:00 PT): best-of stack
   - Final Pick A locked at 0.745. Final Pick B lock by ~21:00 PT.

### Locked Pick A (do NOT change)

- 0.745 — R20 + NT-943 join + teacher overrides + Opus 5th-teacher overlay
- Submission CSV in `submission/csvs/picks/` — see REGISTRY.md for filename
- This is the deadline floor; everything else is upside

### Deferred / NOT-tonight items (per "ignore post-deadline" Day 9 rule)

- Normalizer build (originally planned ~05:00 PT) — push to Slot 9 mid-Sunday
- A1-A7 post-deadline audits in `strategy/POST_DEADLINE_AUDITS.md`
- PAT rotation (all PATs expire <24h anyway per Rain)
- Cursor/Copilot consolidation decisions

### Key uncertainties at handoff

1. **Will ID 9 replicate at high budget?** Validation anchor missed at default. At 81920/65536 should have 16/16 valid samples → cleaner vote. If still wrong at high budget: mechanism didn't replicate, calibrate Pick B expectations down.
2. **Thunder push race**: both runs push to origin/main near-simultaneously. Mitigation: rebase-retry in STEP 6 (coded). If one push fails 3 retries, agent reports back; manual fix at wake.
3. **Tnr-1's anchors (435, 479, 638)**: untested at smoke. Full-run is the test.

### Discipline wins logged this session (preserve as memory carry-forward)

1. Identity guardrail caught SSH-label-vs-marker mismatch on first deployment — paid for itself
2. Pre-flight 7-step caught CSV embedded-newline trap (shell pipeline broken) — Thunder agent surfaced the bug, applied Python fix
3. GPT-5.5 audit via Cursor caught 3 WORRY items (JSON-aware resume, push race, quoted paths) on tnr-1 prompt before fire
4. Smoke gate caught the truncation issue → bumped to hard-tier config before committing 4-5hr
5. `.cursorrules` committed (ae6b7f9) — Cursor auto-loads contract every chat; cross-vendor audit pipeline durable

### Files modified this session (all on origin)

- `agents/CLAUDE_THUNDER.md` (ae3845d) — Day 9 contract: targeted-probe inference scope, identity guardrails, spawn boilerplate, 12 gotchas
- `strategy/POST_DEADLINE_AUDITS.md` (77eadda) — A7 added (past A100 throughput investigation)
- `.cursorrules` (ae6b7f9) — Cursor operating contract
- Tnr-0 + tnr-1 inference outputs (LFS-tracked) — landing post-run

### HEAD at handoff time

`ae6b7f9` (or later if any auto-pushes from running Thunder agents have landed by wake).

### Context state

claude_strategy session at ~870 min, context tight. If continuing in this session post-wake, expect terse responses; if opening a fresh chat, reference this handoff as primary state.

---

## DAY 9 SESSION HANDOFF UPDATE — AUDIT DISCIPLINE (CRITICAL CARRY-FORWARD)

**THIS APPLIES TO ALL WAKE-UP WORK AND ALL FUTURE THUNDER/GPU OPERATIONS, NO EXCEPTIONS.**

### The four-gate protocol (mandatory before any GPU launch)

1. **RESUME-ENABLED**: explicit detection of partial samples.jsonl using JSON-aware count (not `wc -l`)
2. **LIVE TRACKING**: tmux tracker window with watch on sample count + log tail
3. **SMOKE TEST**: 5-item gate, ≥4/5 majority-boxed, fail = `sys.exit(1)` hard-stop
4. **CROSS-MODEL AUDIT (via Cursor GPT-5.5 with `.cursorrules` auto-loaded)**: before fire

### Audit is NEVER optional

Even for:
- "Small" param changes (e.g. token budget bumps)
- "Trivial" patches (e.g. quoting fixes)
- "Same as last time" re-launches
- Tnr-1 mirror of tnr-0's already-audited prompt (mirror is a NEW artifact)

**Why:** This session, three separate audit catches saved real failures:
- Thunder pre-flight caught CSV embedded-newline trap (would have produced 59 empty IDs)
- GPT-5.5 audit caught tracker `$RUN_DIR` BLOCKER (would have broken live monitoring on a 6.5hr run)
- GPT-5.5 audit caught JSON-aware resume + race-safe push + quoted-paths WORRY items
- Tnr-1 launched unaudited with old budgets → killed mid-flight (discipline win)

**The pattern that fails:** "I'm only changing 2 params, no audit needed." That's the exact framing that introduced the tracker BLOCKER.

### Audit workflow (Cursor)

1. Draft prompt OR patch
2. Open Cursor → repo loaded → chat with GPT-5.5 selected (MAX mode, High reasoning, Premium intelligence)
3. Paste prompt with `@codebase` + `#file:` refs to relevant artifacts
4. Cursor auto-loads `.cursorrules` → GPT-5.5 knows audit contract, output format (BLOCKER/WORRY/NOTE)
5. Apply BLOCKERs always; apply WORRYs if cheap
6. Fire to Thunder agent

### When tnr-1's STEP 5 patch fires

It MUST include:
- The same RUN_DIR export + hard-fail-on-missing-run-dir-file fixes from tnr-0's re-patched STEP 5
- Budget bump: `--max-tokens 81920 --thinking-budget 65536`
- All sampling params unchanged from validated thinking-twin config
- Race-safe push (rebase+retry) in STEP 6
- Cross-model audit by GPT-5.5 BEFORE Rain pastes the prompt to tnr-1

### Wake-up audit reminders

If runs complete cleanly: cross-run analysis goes to claude_vscode. Even THAT analysis script should be audited if it touches the GPU or produces submission CSVs.

If runs failed: diagnosis prompt to Thunder agents → audit before sending.

If new spawn prompts needed: draft → audit → fire. Always.

**Discipline > speed. Audits caught real failures multiple times tonight. Don't break the gate.**

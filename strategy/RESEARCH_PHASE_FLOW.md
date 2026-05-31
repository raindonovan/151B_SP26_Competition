# Research Phase Flow — Final-Window Protocol

**Purpose**: Lock in the workflow for the last research phase before v7 execution. Binding for `claude_strategy`, `Cursor`, and execution agents (`claude_vscode`, `tnr-0`, `tnr-1`) during research → review → execute transition.

**Why this exists**: Multiple agents producing research, one human (Rain) couriering LLM queries via dataapp. Without protocol we'll loop forever or work past each other. This time-boxes the loop and defines convergence.

---

## Phase R1 — Parallel adversarial review (30 minutes, hard cap)

Both reviewers work simultaneously, no sequential dependency.

### claude_strategy responsibilities
- Read Cursor's research report (path: TBD, Rain will paste or commit)
- Produce review at `strategy/REVIEW_OF_CURSOR_RESEARCH.md`
- Steelman BEFORE red-team
- Output: AGREE & LOCK / DISAGREE / GAPS

### Cursor responsibilities
- Read v3 plan at `strategy/PHASE_D_v7_PLAN.md` (commit 249be05)
- Optionally read v3 §1 verified citations + 3-LLM follow-up integration
- Produce review at `strategy/REVIEW_OF_STRATEGY_V3.md`
- Steelman BEFORE red-team
- Same output format

### Steelman → red-team protocol (mandatory ordering)

1. **Steelman first** (charitable interpretation). For each major claim/decision in the target doc, write the strongest possible defense. Ask: "What would this need to be true to be correct? What evidence would confirm it? What insight am I missing?" Protects against strawmanning.

2. **Red-team second** (adversarial attack). Only after steelmanning, attack. Ask: "What does this fail to address? Which citations are unverifiable? What failure modes does it create? What plausible scenarios make this plan ship a regression?" This is where you find bugs.

3. **Both rounds required.** Red-team only = anchors on weaknesses. Steelman only = no stress test.

### Mandatory output format (both reviewers)

```markdown
# Review of <target document>

Reviewer: <claude_strategy or Cursor>
Target: <path + commit SHA>
Time spent: <minutes>

## Section 1: Steelman
[For each major claim, strongest defense. Note insights worth integrating.]

## Section 2: Red-team
[For each major claim, attack. Note failure modes, unverifiable citations, gaps.]

## Section 3: AGREE & LOCK
[Items both reviewer and target document agree on after steelman survived
red-team. These are lockable for execution.]

## Section 4: DISAGREE / DIVERGE
[Items where reviewer disagrees. Each must include:
- The specific claim
- Reviewer's counter-position
- What evidence would resolve it (Rain arbitrates, or LLM tiebreak)]

## Section 5: GAPS
[Unanswered questions material to v7 outcome. Candidates for LLM tiebreak.]
```

---

## Phase R2 — Convergence check (Rain, ~10 minutes)

Rain reads both reviews and decides ONE of:

- **CONVERGED** → execute v7. AGREE & LOCK across both reviews becomes binding. DISAGREE parked as known uncertainties unless materially decision-changing. GAPS tolerated.
- **TIEBREAK NEEDED** → escalate ONE specific question to an LLM via Phase R3.
- **REPLAN** → significant flaw surfaced. Author revises (v3.1 patch). Smaller-scope re-review.

Default to CONVERGED unless evidence justifies otherwise.

---

## Phase R3 — Targeted LLM tiebreak (only if needed, ~15 minutes)

If Rain calls TIEBREAK NEEDED:

1. Agent needing answer drafts ONE paste-ready prompt addressed to ONE specific LLM.
2. Rain pastes via dataapp, returns response.
3. Either agent integrates answer into the AGREE/DISAGREE column it touches.
4. **Hard rule**: at most TWO sequential tiebreaks before Rain makes executive call. No infinite refinement.

---

## Phase R4 — Execute

v7 plan locked. Rain authorizes kickoff. Execution agents activated:
- `claude_vscode` → Phase 0 manifest build
- `tnr-0` + `tnr-1` → split base SC@16 (items 0-471 / 472-942)
- `claude_strategy` + `Cursor` standby for execution-time questions

---

## LLM query protocol (any agent can query any LLM at any time)

**Rule of access**: Any agent can request an LLM consultation at any time. Rain is the courier via dataapp.

**Protocol**:

1. **Authoring agent drafts the prompt**. Paste-ready in a fenced code block:
   - **Recipient by name** at top (e.g., `TO: GEMINI`, `TO: CHATGPT (browsed mode)`, `TO: OPUS 4.8`)
   - **The question** — sharp, specific, single-issue
   - **Context** — what context the LLM needs (cite specific repo files, prior LLM responses, v7 sections)
   - **Expected output format** — brief description
   - **Why this LLM** — one line: why this LLM specifically

2. **Rain is the courier**. Only Rain pastes into dataapp and returns the response. No agent assumes anything got fired without Rain confirming.

3. **Identity-address every prompt**. Match LLM to known strengths:
   - **Gemini**: vLLM internals, serving math, low-level technical confirmation (provides actual code references)
   - **ChatGPT (browsed)**: practitioner / Kaggle / AIMO evidence, citation verification (BROWSE STATUS markers)
   - **Opus 4.8**: synthesis across literature, theory framing, hyperparameter rationale
   - Avoid **DeepSeek/Grok** — admitted fabricated citations
   - **Copilot** — last-resort fallback, low credibility

4. **Track in chat, not in the repo**. LLM queries and responses live in conversation. Only the synthesis (decisions, integrations) gets committed.

5. **Max two queries in flight per agent**. Rain has finite bandwidth to relay. Don't pre-queue.

6. **Not for routine questions**. LLM queries are for non-obvious research / verification, not "what flag should I use" (already in docs).

---

## Decision authority matrix

| Decision type | Authority |
|---|---|
| Plan content / synthesis | claude_strategy proposes, Rain authorizes |
| Research interpretation | Cursor proposes, Rain authorizes |
| Conflict resolution | Rain (with LLM input optional via Phase R3) |
| Execution kickoff | Rain only |
| Mid-execution scope change | Rain only |
| LLM query fired | Rain only (couriered via dataapp) |
| Plan freeze | Rain only |
| Time-box override | Rain only |

---

## Exit criteria (research phase ends when ANY trigger)

- **Convergence**: `claude_strategy` + `Cursor` + Rain agree on all material decisions
- **Time pressure**: ≥6 hours before deadline (need ~5h execution + ~1h buffer)
- **Rain executive call**: "we're done researching, execute"
- **Two tiebreaks exhausted** without convergence (Rain makes final call regardless)

---

## Anti-patterns to avoid

- ❌ Steelman/red-team of the review itself (reviews of reviews → infinite loop)
- ❌ LLM queries without a sharp question ("any thoughts on v3?" → fishing)
- ❌ Cursor and claude_strategy both firing LLM queries on the same topic in parallel without coordination
- ❌ Plan revisions during execution phase
- ❌ Pasting raw LLM responses to the repo as canonical evidence (repo gets synthesis, not paste)
- ❌ Treating LLM consensus as proof (LLMs fabricate citations — verification still matters)
- ❌ Reading partial documents ("I'll just skim") — both reviewers commit to full reads
- ❌ Surfacing GAPS without proposing how to close them (every GAP → candidate LLM query or Rain decision)

---

## Where to find things

| Artifact | Location |
|---|---|
| v7 plan (canonical) | `strategy/PHASE_D_v7_PLAN.md` (commit 249be05) |
| v7 plan archive | `strategy/archive/PHASE_D_v7_PLAN_v1_286aaf9.md`, `_v2_49e8da6.md` |
| Cursor's research report (for claude_strategy review) | TBD — Rain pastes or commits to path Cursor specifies |
| claude_strategy's review of Cursor | `strategy/REVIEW_OF_CURSOR_RESEARCH.md` (to be written in R1) |
| Cursor's review of v3 plan | `strategy/REVIEW_OF_STRATEGY_V3.md` (to be written in R1) |
| Master answers / verified gold labels | `data/MASTER_ANSWERS.csv` |
| Latest base SC@8 inference run | `inference/base_model/R20_eval_v1_sc8_p943_t32k_pp1/` |
| Pick B builder | `submission/scripts/build_pickb.py` |
| Pre-fire checklist | `submission/PICKB_FINAL_PREFIRE_CHECKLIST.md` |
| Session handoff | `strategy/SESSION_HANDOFF.md` |
| This flow doc | `strategy/RESEARCH_PHASE_FLOW.md` |

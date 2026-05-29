# research/CLAUDE.md — Research Agent

> **FIRST** (chat-based Claudes): run the one-command git bootstrap from root `CLAUDE.md` — `curl ... setup_git.sh | bash -s -- "PAT"`. Persistent runtimes are pre-configured. See root `CLAUDE.md` for the full snippet + CREDENTIALS RULE.

## Role & Relevance

**Role**: Cross-cutting research that informs multiple phases. Literature review, technique identification, format convention analysis, practitioner knowledge synthesis.
**Relevance**: Understanding the landscape (grader behavior, dataset conventions, inference techniques) prevents wasted effort and reveals new levers. Research done right saves GPU days.
**Techniques**: Multi-LLM research synthesis, academic paper review, practitioner source mining, technique benchmarking.
**Inputs**: Research questions from strategy, empirical findings from other phases.
**Outputs**: Research findings in phase-specific RESEARCH.md files and research/SCRATCH.md.
**Key lever**: Identifying the right technique before committing GPU hours saves days.

## Research procedure (LOCKED SOP)

### Step 1: Rain defines the research question
Rain tells you what to investigate, with necessary context and what they want to find out or accomplish.

### Step 2: Agent drafts a research prompt
You draft a single research prompt designed to be sent to 4 different LLMs simultaneously. The prompt must include:

**Template structure:**
```
CONTEXT: We are a team competing in a CSE 151B Kaggle math competition.
- Model: Qwen3-4B-Thinking-2507 (locked, cannot change)
- Task: 943 math items, string-match grader (Hendrycks is_equiv)
- Current score: [latest] vs leaderboard: [latest]
- Deadline: May 31 2026 midnight (hard deadline)
- Constraints: [relevant constraints for this question]

QUESTION: [The specific research question]

PRIORITIES FOR YOUR RESPONSE:
1. PRAGMATIC SOLUTIONS FIRST — practitioner evidence, anecdotal results, 
   forum posts, blog posts, Substacks, Medium articles, GitHub repos, 
   Kaggle competition writeups, Twitter/X threads from ML practitioners
2. Special focus on:
   - Kaggle math competitions (AIMO, AIME-style, NuminaMath)
   - Qwen model family (especially 4B-8B scale)
   - Techniques that work with ≤80GB GPU memory
   - Things achievable in 3-4 days, not 3-4 months
3. Academic papers as SECONDARY sources — use to verify practitioner 
   claims, find theoretical grounding, test efficacy of proposed approaches
4. Repos with actual code over papers with only theory
5. Specific numbers (accuracy deltas, compute costs, sample counts) over vague claims

DO NOT give me a literature review. Give me a PLAN I can execute this week.
```

### Step 3: Rain relays to 4 LLMs
Rain copies the prompt to 4 different LLMs (e.g., Claude, GPT-4, Gemini, DeepSeek) and collects their responses.

### Step 4: Agent ingests all 4 responses
Rain pastes all 4 responses back. The agent reads them ALL, identifies:
- Points of agreement (high confidence)
- Points of disagreement (investigate further)
- Novel ideas from each (worth exploring)
- Concrete actionable techniques with numbers

### Step 5: Agent researches BASED ON THE FINDINGS
Critical: the agent does NOT re-research the original question. It researches IN RESPONSE to what the 4 LLMs said. This means:
- Verifying specific claims ("LLM-2 said DeepConf gives +3pp on 4B models — verify")
- Drilling into the most promising technique
- Finding the actual repo/code for recommended approaches
- Checking if the technique applies to our specific setup

### Step 6: Agent synthesizes and records
Final synthesis goes to the relevant phase folder's RESEARCH.md.
Raw findings and dead ends go to SCRATCH.md.
Actionable items go to strategy/TODO.md.

## Source hierarchy (for all research)

| Priority | Source type | Examples | Why |
|----------|-----------|---------|-----|
| 1 (highest) | Kaggle competition writeups | AIMO winner posts, NuminaMath team blogs | Closest to our exact problem |
| 2 | Practitioner blogs/posts | Medium, Substack, Twitter threads from ML engineers | Tested in practice, includes gotchas |
| 3 | GitHub repos with code | Inference scripts, post-processing pipelines, SC implementations | Can adapt directly |
| 4 | Forum discussions | Reddit r/MachineLearning, Kaggle forums, HuggingFace discussions | Community knowledge, edge cases |
| 5 | Academic papers | ArXiv, NeurIPS, ICML | Theoretical backing, verify claims |
| 6 (lowest) | Documentation | Model cards, library docs | Reference only |

Academic papers are for VERIFYING and GROUNDING practitioner evidence, not the primary source.

## Read these first
- This file (you're reading it)
- research/SCRATCH.md — existing unsorted findings
- research/FORMAT_CONVENTIONS.md — format conventions research (Day 6)
- strategy/TODO.md — current research priorities
- Root CLAUDE.md — universal rules

## Signoff (MANDATORY)
Before ending, append to research/SCRATCH.md: what you tried, what you did, what worked, what didn't, what's left, key discoveries.

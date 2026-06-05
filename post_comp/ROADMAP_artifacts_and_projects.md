# Post-Competition Roadmap — Artifacts & Projects
*The tangible outputs. Brainstorm texture/rationale lives in SESSION_ARC_2026-06-04.md (§11). 10 items: 4 artifacts + 6 projects.*

## ARTIFACTS (things we WRITE)
- **A1 — Research paper.** Course requirement. Topic OPEN (rare-trace pending diligence). Treated in isolation.
- **A2 — Systems / competition writeup.** The pragmatic "how I actually approached the competition" doc — the honest equivalent of a "how I won" post. Blog first, arXiv optional.
- **A3 — "What I learned executing this competition."** The lessons list (seed below). Standalone OR a section of A2.
- **A4 — Agentic workflow doc.** What the orchestration was, what broke ("butcher shop" friction — agents couldn't read/write paths, coordination overhead), what worked, how to do it better. Doubles as the design spec for P1.

### A3 seed — the "what I learned" list (do not let this slip)
- **Agentic / multi-agent orchestration** (strategy↔execution↔submission; delegate→verify-from-repo→approve; four-gate protocol) — the most market-hot, differentiating skill; "what made this all possible."
- Inference-time scaling: self-consistency, format-gated + confidence-weighted voting.
- Reasoning-model internals: NoThinking prefill, chat-template manipulation, budget forcing, the suppression spectrum.
- Fine-tuning with scar tissue: LoRA/QLoRA, SFT failure modes (truncation, catastrophic forgetting, drift), GRPO (sharpens not expands), transductive answer-memorization.
- Eval / grader engineering: reverse-engineering a value-equality grader, answer extraction/normalization, multi-slot/positional handling, the clean-benchmark-vs-real-grader gap.
- Infra: vLLM, DSMLP A30/A100, Thunder H100/A100, multi-GPU, resumable long runs, walltime management.
- Background differentiators: commercial pilot, EV-fleet founder, 2M-sub creator-strategist — a rare combo.

## PROJECTS (things we BUILD)
- **P1 — The orchestration harness "I wished I'd had."** Multi-agent ML-experiment framework: verified file I/O, four-gate protocol, strategy↔execution↔results loop. Start small (CLI coordinating 2–3 agents). Origin story sells it.
- **P2 — Research-diligence agent.** Point it at an idea → searches literature, finds prior art, drafts related-work + honest novelty verdict. Automates exactly what we did by hand. Hackathon-sized. Showcases agentic + research methodology.
- **P3 — Domain-crossed agentic build.** An agentic tool in a vertical Rain knows cold: aviation ops / small-fleet-EV logistics / creator-content strategy. Domain expertise × agentic skill = the real moat.
- **P4 — Visual demos.** Smaller pieces (grader-gap visualizer, thinking-budget/NoThinking tradeoff explorer). Largely folds into P6 + the website.
- **P5 — Personal website.** The home tying all artifacts + projects together. Built AFTER the artifacts exist.
- **P6 — Live Inference Visualizer** (the centerpiece). Spec below.

## P6 — Live Inference Visualizer (spec v0)
**What:** an interactive, animated diagram of the competition's inference pipeline — **EIB made tangible** — that an employer can click through. Centerpiece of the website (P5).
**Pipeline stages (data flows left→right):**
1. **Input** — problems/questions enter.
2. **EXTRACT** — the inference engine: self-consistency over the model (the agents / parallel sampling) → candidate answers → the "answer sheet."
3. **BYPASS** — the LoRA / answer-memorization adapter overlays known-hard items.
4. **NORMALIZE** — the grader-conformance layer (canonical render / multi-slot formatting).
5. **Output** — the final submission CSV.
**Interactivity:** every node clickable → reveals its parameters + a real sample flowing through it (e.g., click the adapter → see its config + an item being overridden).
**Data — REPLAY-FIRST:** pipe the real recorded runs + CSV outputs through the animation — always works, instant, free, demo-proof. "Run live on a GPU backend" = optional stretch button only (a 4B thinking model won't run in-browser; a live endpoint is what breaks in an interview). Replay of real data > fragile live run. (Rain's own seed: "use our old CSV output.")
**Tech (tentative):** static skeleton can be Mermaid-style; the flowing/clickable/animated layer wants React Flow or custom SVG/canvas. Lock the stack at build time.
**Why it lands:** portfolio eye-candy + teaching artifact + proof of end-to-end understanding. Most candidates show a repo; this shows a living pipeline.

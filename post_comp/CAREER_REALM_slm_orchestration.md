# Career Realm — SLM Orchestration / Efficient Inference
*Grounded via web research (NVIDIA SLM position paper; multiple 2026 hiring-data analyses). The realm the competition skills actually map onto. Hard constraint honored: fast-moving field = continuous learning is the job.*

## The realm (and why it's real)
- **"Small models, orchestrated well"** is a live, dominant bet in applied AI. NVIDIA's "Small Language Models are the Future of Agentic AI" (Belcak et al., 2025): most agentic work is repetitive/structured/scoped; SLMs are 10–30× cheaper; **"capability — not parameter count — is the binding constraint."**
- The bottleneck has shifted from **model capability → orchestration quality**, which is largely size-independent. "Teams that invest in fine-tuning/squeezing expertise dramatically out-perform; the last 30% requires skills that aren't widespread."
- Who wants a maxed-out small model: regulated/on-prem (healthcare, finance, defense), latency-sensitive inline UX, high-volume (>~11B tokens/mo self-hosting wins 4–10×), edge/on-device, cost-cutting agentic teams. (Rain's domains — aviation, fleet ops — are plausibly on-prem/regulated/edge verticals.)
- What questions: structured, high-frequency, format-constrained, input-determined (classification, extraction, routing, tool-calls, summarization) — same shape as "math question → boxed answer in required format."

## Skills map (competition → market)
STRONG / SCARCE (lead with these):
- **Eval discipline** — #1 hiring-gap complaint. = grader reverse-engineering + forensic error analysis. Also the key RAG sub-skill (retrieval evaluation / groundedness).
- **Inference & cost engineering** — vLLM, batching, KV cache, token budgets, "which model per request." = iso-compute + token-cost work.
- **Multi-agent orchestration** — planner-executor, tool routers, LangGraph-in-prod. = strategy/execution agent system. The differentiator.
- **Fine-tuning scar tissue** — LoRA/QLoRA, catastrophic forgetting "two weeks later," Unsloth/Axolotl. Rare depth; the scarce $200–450K role explicitly values it. BUT keep as differentiating flex, NOT primary positioning.

GAPS (close deliberately):
- **RAG / retrieval** — #1 baseline skill (40% of all AI-eng roles; 74% of LLM-focused). Competition had ZERO retrieval. Now baseline/table-stakes (premium migrated to the platform layer beneath: vector DBs, observability, MLOps, distributed systems — where Rain's skills already sit). Close it by reusing eval strength on retrieval-eval. Minor signal: RAG demand cooled ~4% recently (commoditizing as baseline).
- **Production ops at scale** — deploy/monitor/on-call, Docker/K8s, observability (Langfuse/Braintrust). Competition was experimental, not productionized.

## Positioning (decided)
- Target role: **Applied-LLM / AI Engineer (platform-leaning)** — NOT "fine-tuning specialist" (scarce demand, hard to break into cold as a new grad), NOT "prompt engineer" (collapsed).
- One-liner shape: "applied-LLM/inference engineer with unusual depth in evaluation, inference-economics, and orchestration — plus real fine-tuning scar tissue."
- On-ramp realities: remote-friendly + contract-to-hire heavy at senior end → friendlier entry without a big-name resume.

## Portfolio green-flags to engineer toward (from hiring data)
quantified results (cost/latency/accuracy deltas) · an eval framework · failure-mode handling · cost optimization w/ real savings · a public technical writeup on a specific failure mode · specialty depth ("the agent-infra person"). Anti-flags: only-notebooks, tutorial demos, fine-tuning as primary skill w/o broader eng, all-projects-in-last-6-months (career-switcher read).

## Next pass (TODO)
- Re-map the 6 PROJECTS (see ROADMAP_artifacts_and_projects.md) so each is explicitly aimed at a named green-flag, with **RAG slotted into at least one build** (paired with retrieval-eval). To be done in the dedicated projects discussion.

## DECISION: RAG build = next major build
- Locked. The next big build is a **small-model RAG system with a retrieval-eval harness as the centerpiece** (the eval layer is the differentiator, and reuses the competition's black-box-forensics skill). Artifacts wrapping up the competition + smaller demos are supporting work, not the headline.
- Enter it to DEMONSTRATE the scarce skill (build + evaluate reliable small-model RAG), NOT to find a novel trick.

## RESEARCH FINDING: 2026 RAG is also fully mapped — but the open lane is eval/reliability
- Direct translations of our 2025 tricks → RAG are all DONE, often 2026-datestamped: self-consistency/parallel scaling (SPARC-RAG, HypoSelectSimRAG), confidence/uncertainty-gating (CRAG, ReaLM-Retrieve, MultiRAG), adaptive reasoning depth (Cost-Aware Adaptive Depth, When-to-Retrieve), test-time adaptation = transductive (TTARAG), agentic+reasoning RAG (Search-o1, CoRAG), and our EXACT stack — small model + R1-distilled reasoning + RAG + on-prem — already published (Retrieval-augmented reasoning with lean LMs / NHS corpus).
- LESSON (permanent): **novelty-by-translation is itself a saturated strategy.** Porting a trick one field over is a treadmill, not an escape. Stop hunting unclaimed concepts.
- The OPEN lane (where the field's own surveys point): eval, reliability, faithfulness, **positional/permutation fragility** (Stable-RAG 2026 — rhymes with our multi-slot positional grader problem), failure attribution, on-prem deployment. These are MEASUREMENT problems = our lane.

## THE OPEN SEAM (best candidate for the 5-week research project)
- 2026 papers show the small-model RAG failure picture is unresolved AND metric-hidden:
  - "Can Small Language Models Use What They Retrieve?" — ≤7B models fail to extract the answer 85–100% even with ORACLE retrieval; context DESTROYS 42–100% of previously-known answers (distraction). Bottleneck = context UTILIZATION, not retrieval quality; naive RAG can be net-negative at this scale.
  - "When Small Models Are Right for Wrong Reasons" — 50–69% of CORRECT 7–9B answers have flawed reasoning (invisible to accuracy); RAG helps reasoning integrity, self-critique HURTS small models.
- Viable project shape: **a forensic characterization of WHERE/WHY a 4B model fails to use retrieved context (utilization vs retrieval vs negative-rejection vs right-for-wrong-reasons) on a real corpus, + a failure-attribution harness.** Empirical autopsy, not a new method. Doubles as the RAG build's eval layer.
- Trap check: the BROAD question ("do small models use retrieval well") is being actively claimed by the two 2026 papers above. Our defensible wedge = forensic attribution + specific real corpus + reusable harness. NEEDS one confirmatory diligence pass before committing.

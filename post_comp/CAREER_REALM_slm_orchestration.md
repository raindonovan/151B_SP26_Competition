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

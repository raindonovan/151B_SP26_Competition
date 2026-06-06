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

## BIG REVEAL: advisor = Prof. Sicun (Sean) Gao, UCSD CSE
- Renowned: CMU PhD under Edmund Clarke; built **dReal** (SMT solver for nonlinear reals; used by Toyota Research, NASA, a UK hospital). Associate Prof since 2023.
- His lane: automated reasoning, formal verification, **safe neural control** (neural Lyapunov/barrier functions, ReLU-net verification — SEEV NeurIPS'24), NP-hard search/optimization, and recently **RL theory** (ICML 2025: value estimation in policy gradients; max-entropy pitfalls). Self-described mission: "practical algorithms for NP-hard search and optimization… reliable yet aggressively optimized… needles in haystacks."
- His lane is NOT LLMs/RAG/NLP. ⇒ This RESHAPES the research half of the plan. A great advisor in HIS area > a mediocre fit to our pre-chosen RAG area.

## RESEARCH DIRECTION PIVOT (two independent minds converged)
- Both Claude and ChatGPT independently concluded: with Gao as a hard constraint, **small-model RAG context-utilization is second-best** (dragging NLP into a verification lab; "evaluation" is not enough glue).
- The surviving, advisor-shaped ABSTRACTION (this is the durable win): **a small LLM as a stochastic search/proposal policy INSIDE a verified system** — NOT "RAG." This is the honest abstraction of what we actually did well in the competition (search + selection + canonicalization + verifier-mismatch forensics), and the repo confirms it (fusion/overlay submissions beat the SFT/LoRA ones; LoRA was never the winning story).
- Competition→Gao skill map: SC sampler → proposal distribution; Kaggle grader → SMT/dReal checker; boxed-answer normalizer → parse/canonicalize to a formal object; "rare correct trace" → "valid certificate = needle in haystack" (literally Gao's mission).

## CERTSEARCH VERDICT (ChatGPT's proposal — pressure-tested, NOT locked)
- ChatGPT proposed "CertSearch": small model proposes Lyapunov/barrier/invariant certificates, dReal/SMT checks, counterexample-guided repair, failure forensics, budgeted search. Strong advisor-fit AND portfolio-fit.
- BUT its claim "near-frontier, not saturated in Gao's niche" FAILED diligence — same failure mode as every prior idea, one domain over:
  - **BarrierBench (2025)** is CertSearch's twin: LLM agentic framework for barrier-cert synthesis, 100 dynamical systems (lin/nonlin/discrete/cont), LLM template discovery + SMT verification + counterexample refinement, even tests RAG + agentic coordination; >90% valid. Benchmark + toolchain released.
  - **Global Lyapunov functions w/ symbolic transformers (Meta 2024)**: LMs discover Lyapunov functions, beat solvers on polynomial systems. "LLM finds Lyapunov" headline taken.
  - CEGIS-with-LLM loop is an established named pattern (Counterexample-Guided Inductive Synthesis + SAT/SMT, 2023); loop-invariant world saturated (LaM4Inv; reasoning-LLM+Z3 = 100% on Code2Inv 2025).
  - ⇒ CertSearch as pitched = "BarrierBench but smaller model + more forensics" = footnote on someone's flag, not open ground.
- PERMANENT LESSON reconfirmed (6th time): no obvious conceptual/translation wedge is open in this field. Novelty lives in EMPIRICS / a specific real-system measurement.

## THE SURVIVING SEAM (promising, HYPOTHESIS — needs its own diligence pass before building)
- The one corner BarrierBench did NOT center: **selection economics + confidence-signal forensics for verifier-guided small-model synthesis** — "which of a small model's many candidates deserves an expensive solver call, and where do naive confidence signals LIE?"
- Grounded by: **Grammars of Formal Uncertainty (2025)** — token-entropy fails to predict correctness of LLM formal artifacts; lightweight selective verification cuts errors 14–100%. **Neural Synthesis for SMT-Assisted Proof** — fine-tuned SMALL models (Phi-2) rival GPT-4 at far lower cost on verified synthesis.
- This is EXACTLY our competition machinery (self-consistency + selection + "when does the confidence signal mislead"), it's Gao-shaped (budgeted search under an exact checker), and less crowded than success-rate-maximizing cert synthesis.
- STATUS: Claude's hypothesis, NOT a verified-open finding. Run confirmatory diligence before committing as headline.

## TWO-TRACK FORK (decision pending; take to Gao)
- Track A (job-optimal, advisor-neutral): small-model RAG + eval-harness build. Strong portfolio, weak Gao-fit. Keep as BACKUP / portfolio, not the Gao project.
- Track B (advisor-optimal): small-LLM-as-search-policy inside a verified synthesis loop, in Gao's domain — pending Gao's read on WHICH specific sub-question is still open (the selection-economics seam is our best guess).
- KEY MOVE: take Track B to Gao as a DIRECTION, not a finished proposal — BarrierBench means the obvious version is taken, so his expertise must pick the open sub-question. Opener instinct: "small LLM as proposal policy inside a verified loop; BarrierBench/symbolic-Lyapunov did the obvious version; my competition instinct says the open part is selection economics — which candidates deserve expensive verification and why confidence misleads — but you'll know the real gap."

## VENUES (Gao-fit, mid/late 2026)
- HIGH signal: **FMCAD 2026 Student Forum** (student-specific, formal methods, ongoing-work reports, talk/poster, NOT archival so doesn't block later pub; abstract ~Jun 16, submission ~Jun 22 — VERIFY exact dates). **VSTTE 2026** WiP/short (co-located FMCAD; abstract ~Jul 10, paper ~Jul 17 — VERIFY).
- North star (deadlines passed for 2026): CAV (ML/autonomous-system verification scope). NeurIPS 2026 workshops possible later (neuro-symbolic / AI-for-theorem-proving / reliable-ML) if a relevant one appears.
- Prior RAG-track venue intel (if Track A ever revived): ACL/AACL Student Research Workshops (first-author-must-be-student = our edge; non-archival; pre-submission mentorship; AACL deadline ~Jul 26 2026 — VERIFY).

## URGENT REPO HYGIENE (before ANY employer or Gao sees the repo)
- Root README is placeholder text — fix.
- A leaked-API-key warning is visible in the repo — ROTATE the key + scrub. Non-negotiable; it's the first thing a viewer sees.

## FOUR-LLM SWEEP RESULTS (ChatGPT + Gemini build-ideas; DeepSeek + Opus4.8 + 1 more CertSearch critiques)

### Citation verification (Claude ran this — Rain's standing instruction)
- VERIFIED: "selection economics" is DEAD as a research contribution — preempted, not open. Real, published 2025–26: "When to Trust the Cheap Check: Weak and Strong Verification for Reasoning" (weak/strong policies, two-threshold, online algo SSV); a state-level selective-verification paper (gating + pre-verification ranking + adaptive verifier-call allocation; beats best-of-N w/ ~44% fewer calls); Singhi "When to Solve, When to Verify"; "Budget-aware Test-time Scaling via Discriminative Verification." ⇒ "which candidates deserve an expensive verifier call + where confidence misleads" is one of the most active corners of test-time-compute research. Occupied.
- Citation trust pattern (confirmed): DeepSeek cited BarrierBench as 2503.12311 — WRONG (real = 2511.09363); other DeepSeek cites unverifiable/likely fabricated. Opus4.8 citations clean. RULE: trust the critiques' reasoning (it converges); trust DeepSeek's specific citations not at all.

### Build sweep — STRONG convergence (two independent models, near-identical top 3)
- #1 (BOTH): eval / failure-forensics lab. ChatGPT "GraderScope" ≈ Gemini "Grader-Hacking Evals Lab" — open-source harness that finds where graders/judges/brittle checkers fail on stochastic LLM output, then patches w/ normalization + calibration + regression tests. Weaponizes Rain's standout skill. Maps onto residency/frontier hiring (Anthropic reward-models, OpenAI frontier-evals, Cursor eval). Highest feasibility. ← LIKELY THE BUILD.
- #2–3 (BOTH): aviation domain wedge — safety-report normalizer on public NASA ASRS + FAA SDR, tied to Part 135 SMS deadline 2027 "why now." FlightCheck ≈ Aviation SMS Event Normalizer. Pilot background as wedge, not trivia.
- #3 (BOTH): verifiable agent harness (orchestrator-worker-verifier, replay, trace diffing, regression gates).
- Gemini's best line — the HYBRID: aviation SMS tool as the PRODUCT story, grader-forensics machinery as the intellectual CORE. Hard to fake, easy to interview on.
- Universal hinge question (BOTH): "Can Rain get ~3 real users/design partners + data access in the first 2 weeks in a wedge domain (aviation/fleet/creator)?" YES → domain-wedge build; NO → eval/forensics lab.
- Avoid (unanimous): generic RAG chatbot, thin model-wrapper, sprawling platform, benchmark untied to a real workflow.

### Genuinely-new items the sweep surfaced
- Eval/forensics lab as the crisp #1 — wasn't our headline; now is.
- Aviation SMS wedge w/ real regulatory why-now (Part 135 SMS 2027) + public data.
- "Build ON Gao's existing code (SEEV / FOSSIL), not from scratch" — rescues a Gao project from the dReal-from-scratch trap.
- Cheap-verifier pivot (code / text-to-SQL): same skill ("selection under an expensive oracle"), free verifier (test execution), zero install pain, instant hiring legibility (Opus).

### Divergence — the Gao research pivot (only Gao resolves)
3-way split: DeepSeek → value-guided inference search for control / repair-selection. Opus → empirical study on SEEV/FOSSIL, or selection-economics reframed WITHOUT the LLM. 3rd → LLM-guided boundary-partitioning to accelerate SEEV. (Build models barely diverge — itself a signal.)

### SETTLED SHAPE (post-sweep)
- Job build decided in spirit: eval/failure-forensics lab, possibly w/ aviation SMS wedge as product skin. Serves residency + mid-market + AI-for-X.
- CertSearch dead. A Gao research project lives ONLY if it (a) builds on his existing code AND (b) he picks the open sub-question.
- One-artifact-vs-two leans TWO related tracks (eval/aviation build for job; SEEV/FOSSIL empirical study for Gao) — share a through-line (forensic eval + selection under a verifier). GAO CONFIRMS OR COLLAPSES THIS.
- Sweep DONE. No fifth model. Bottleneck = Gao conversation → start building.

### Resume-bullet language (reframe — do NOT lead with "I fine-tune LLMs")
- "Built an eval/failure-forensics harness for stochastic LLM outputs: normalization, failure taxonomy, self-consistency + confidence selection, regression gates."
- "Reduced unreliable generation to auditable proposal→check→repair loops, tracking parse/verifier failures, duplicates, latency, cost."
- Lead identity: "I build and evaluate reliable verified-generation / multi-agent systems on small models."

## MAX OUT THE STUDENT CARD (~3 months left at UCSD)
Organizing principle: rank by what EXPIRES at graduation. Clock-bound first.
- [ ] Student-only apps w/ deadlines (TOP — they vanish): student research workshops + travel grants (FMCAD Student Forum, AACL/ACL SRW); UCSD-internal fellowships/showcases; new-grad programs requiring current-enrollment/recent-grad status. VERIFY exact dates.
- [ ] People (access expires): Gao + his PhD students (reference network); 2–3 adjacent AI/ML/systems faculty (breadth + letters); CSE/HDSI career staff (employer pipelines); seminar speakers; UCSD alumni at target cos (LinkedIn warm-intro path).
- [ ] Events: CSE/HDSI seminars, career fairs, research expos/demo days, hackathons, reading groups.
- [ ] Resources: compute credits, paper access, .edu perks.

## APPLY-IN-PARALLEL (research lead time < application lead time)
- Apply WHILE research in progress; describe it in-progress (residencies accept this).
- Residencies/fellowships: Anthropic Fellows, OpenAI Residency — reference in-progress research + Gao. Verify cycles.
- Job pipeline NOW via referral/recruiter (cold apps convert terribly): UCSD network + alumni; AI-mature mid-market + AI-for-X + infra startups.
- Show finished research (~wk6–7+): FMCAD Student Forum / VSTTE WiP / AACL-ACL SRW + UCSD expos.

## DECISIONS
- NO second formal research program (dilutes). Informal breadth OK (reading groups, coffees). Gao = gold, depth > breadth.
- Current research program: keep ONLY for its instrumental value (Gao conduit? funding? letter? line?). Minimize time on hand-holding; extract the one thing it gives.

## GAO TIMING + WEEKEND REFRAME
- Gao takes meetings WEDNESDAY onward. Weekend = continued planning → transition into focused Gao meeting prep. Email still sends Sunday eve (waits in inbox Mon); meeting lands Wed+. No pressure to have anything "done" by Monday.

## POST-RESEARCH DREAM BOARD (residencies/fellowships — verify exact dates at apply-time, programs move)
- Anthropic Fellows (BEST-TIMED): 4mo, empirical→paper, $3,850/wk + ~$15k/mo compute, Berkeley/London/remote-in-country. Workstreams incl. RL Fellows (GRPO/RLVR/small-model fit) + ML Systems & Performance (vLLM/inference fit). Credentials-agnostic, bachelor's min. ROLLING, multiple cohorts/yr (May/Jul/late-Sept 2026+). Apply when build+Gao paper ready.
- OpenAI Safety Fellowship: Sep'26–Feb'27, priority incl. SAFETY EVALUATION + robustness (= build #2). Output paper/benchmark/dataset. Apps closed May 3 → WATCH next cycle.
- OpenAI Residency: 6mo, full salary, early-builders. CLOSED for 2026 → watch.
- MATS Autumn 2026: fully funded, ~$5k/mo+compute, housing/travel, J1 visa support, top mentors. Closes JUNE 7. AI-safety/alignment focus = stretch-fit on current profile. Multiple cohorts → target a future one with stronger materials.
- Cambridge ERA:AI: 10wk Cambridge, fully funded incl visa+travel, GLOBAL (SA-friendly). 2026 likely closed (Jul 6 start) → watch 2027.

## CRITICAL GATE: WORK AUTHORIZATION
- Anthropic Fellows + OpenAI require US/UK/Canada work auth, NO visa sponsorship. Rain's SA background → must confirm status. If uncertain → MATS (J1) + ERA (global) are the safer doors. CONFIRM RAIN'S WORK-AUTH STATUS — gates the list.

## AVIATION BUILD — INTERNATIONAL/ICAO REFRAME (build #2 framing)
- SA contacts (SACAA, not FAA) DON'T break build B — they bend framing. SMS is a GLOBAL ICAO mandate (Annex 19, in force 2013); FAA Part 135 2027 is the US instance; SA has SA-CAR Part 140 (SMS in law: accountable manager, safety manager, SRB/SAG, audits — from ICAO Annex 19 + Doc 9859); EASA its own. Internationally-harmonized 12-element framework.
- ⇒ Build is regulator-agnostic: public US ASRS data as corpus (regardless of validator nationality) + ICAO-harmonized taxonomy. SA safety officers are valid design partners; their judgment transfers. Cross-regime 121+135 + 1000hr = RICHER credential.
- Flags: time-zone (SA ~UTC+2 vs CA ~UTC-8 → async process); DO NOT request confidential/proprietary reports (POPIA/privacy) — public ASRS for data, contacts for judgment/validation ONLY.
- Net framing: build on ASRS, why-now = global SMS (ICAO; FAA 2027 + SA-CAR 140 as instances), validate with SA network. Strongest form of B.

## BUILD #2 — CHOSEN SHAPE + TIERS
- DECISION: Option B (aviation SMS normalizer) as product + Option A (grader/confidence forensics) as engine. Hybrid.
- Three tiers (better than binary): A = GraderScope, domain-agnostic, no users. B-minus = aviation on public ASRS alone, scored vs NASA coded fields (domain wedge + why-now, no partners). B-full = aviation + 3 real design partners + validated user story.
- Data is FREE (public ASRS CSV + NASA expert-coded fields as ground-truth anchor; FAA SDR for maintenance). Design partners are NOT for data — they're for: what "correct/dangerous" means operationally, the real-user story (the reason B>A), workflow realism. Rain's pilot network = partner pipeline.
- Decider A vs B: can Rain get ~3 partners + data in 2 weeks? Yes→B/hybrid, No→A. C (research judge-robustness benchmark) only if residency-first over mid-market.

## SWEEP FACT-CHECK (build #2 docs) — what's real
VERIFIED, citable:
- Judges gameable: "One Token to Fool LLM-as-a-Judge"; AdvJudge-Zero (arXiv 2512.17375, Dec'25 + PaloAlto Unit42) — >90% FPR on 22/24 cells (Unit42 blog says "99%").
- Agreeableness bias: Beyond Consensus (arXiv 2510.11822, NUS Oct'25) — TPR>96%/TNR<25%, minority-veto, regression→1.2% max error. SCOPE: one code-feedback task (366 buggy Python, ~7.5% invalid). Cite scoped, not as universal law.
- 12 judge biases (Justice or Prejudice, Ye 2024); pairwise flips ~35% vs 9% (Tripathi); VerifyBench/RewardBench "room for improvement."
- CertSearch anchors verified prior: BarrierBench 2511.09363, SEEV 2410.20326, Snell 2408.03314, Setlur 2502.12118.
- Eval incumbents real (LangSmith/Inspect/DeepEval/promptfoo/Braintrust/Langfuse/Galileo/Openlayer).

UNVERIFIED — do not quote w/o checking (recent-ID fabrication risk):
- RAG cluster doc#3: RAGVUE 2601.04196, Pandey 2603.11513, Stable-RAG 2601.02993, "Agentic AI" 2605.14675, RAGBench 2407.11005, Wallat 2412.18004. ODAR routing. Conformal coverage %s (97.1/98.6/91.4). N-Rep $0.039-vs-$0.46 (2505.14174).

FABRICATED — never cite (doc#4):
- "Flagship" platform comparison table (beats Braintrust/LangSmith/etc.) = aspirational spec presented as measured.
- ASRS table "Flagship MV Ensemble 89.5% precision" etc. = invented results for a system that doesn't exist.

STRATEGY:
- Docs #4/#5 = over-scoped fantasy (1 real paper [Beyond Consensus] + conformal/HDBSCAN/ODAR theater). Build doc #3's HONEST CORE: 2×2 production-grader vs oracle-grader → failure taxonomy → safe normalization → regression gate. Conformal/clustering = optional spice, not spine.
- AVIATION DEMOTED (per Rain): optional demo skin, not thesis. Lead domain-agnostic. Generate own measured numbers if aviation demo built; never reuse doc#4's fake ASRS stats.

# Transductive / inference-forward competition targets (June 2026)

> **Logged:** 2026-06-04 · Research for Rain (151B winner: hidden holdout + SC/thinking + oracle/format loop).  
> **Ratings (1–10):** H = hidden test + submit loop; I = inference-at-scale fit; O = legal test-time adaptation / ensemble exploit; W = field size / win probability for Rain.

## Best 3 to enter now (June 4, 2026)

1. **[ICML AI4Math Workshop challenges](https://ai4math2026.github.io/)** — **June 15, 2026** (Codabench). Pick Track 2 (Lean TCS) or Track 3 (SeePhys Pro) for closest 151B math→answer pipeline.
2. **[NVIDIA Nemotron Model Reasoning Challenge](https://www.kaggle.com/competitions/nvidia-nemotron-model-reasoning-challenge)** — **June 15, 2026** final submit. `\boxed{}` logic puzzles; GRPO/SFT + SC stack transfers; field is large (~3.9k teams).
3. **[Mega Agent-A-Thon](https://mega-agent-a-thon.devpost.com/)** — **June 4–14, 2026**, students only, tiny field. Package 151B agent/verification as a demo (not math LB mining).

**Start immediately (July payoff):** [CAR-bench @ IJCAI-ECAI 2026](https://car-bench.github.io/car-bench/) — final hidden eval **July 19**.

---

## Ranked opportunities (10)

| Rank | Opportunity | Link | Deadline | H | I | O | W | Composite |
|------|-------------|------|----------|---|---|---|---|-----------|
| 1 | ICML AI4Math (4 Codabench tracks) | [ai4math2026.github.io](https://ai4math2026.github.io/) | **Jun 15, 2026** | 7 | 9 | 6 | 8 | **7.5** |
| 2 | NVIDIA Nemotron Reasoning (Kaggle) | [kaggle.com/.../nvidia-nemotron-model-reasoning-challenge](https://www.kaggle.com/competitions/nvidia-nemotron-model-reasoning-challenge) | **Jun 15, 2026** | 9 | 9 | 5 | 5 | **7.0** |
| 3 | CAR-bench Challenge (IJCAI) | [car-bench.github.io](https://car-bench.github.io/car-bench/) | Hidden eval **Jul 19**; report **Jul 26** | 8 | 8 | 7 | 7 | **7.5** |
| 4 | Mega Agent-A-Thon (students) | [mega-agent-a-thon.devpost.com](https://mega-agent-a-thon.devpost.com/) | **Jun 14, 2026** | 5 | 7 | 4 | 9 | **6.3** |
| 5 | AIMO Progress Prize 4 (watch) | [aimoprize.com](https://aimoprize.com/) | TBD (PP3 closed Apr 2026) | 10 | 10 | 7* | 3 | **7.5*** |
| 6 | Google Cloud Rapid Agent Hackathon | [rapid-agent.devpost.com](https://rapid-agent.devpost.com/) | **Jun 11, 2026** | 4 | 6 | 3 | 6 | **4.8** |
| 7 | ARC Prize 2026 — AGI-2 (static) | [kaggle.com/.../arc-prize-2026-arc-agi-2](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2) | **Nov 2, 2026** | 8 | 6 | 4 | 4 | **5.5** |
| 8 | ARC Prize 2026 — AGI-3 (interactive) | [arcprize.org/competitions/2026/arc-agi-3](https://arcprize.org/competitions/2026/arc-agi-3) | Milestones Jun/Sep; final **Nov 2** | 7 | 5 | 5 | 4 | **5.3** |
| 9 | NeuroGolf Championship (ARC, minimal nets) | [kaggle.com/competitions/neurogolf-2026](https://www.kaggle.com/competitions/neurogolf-2026) | Entry **Jul 8, 2026** | 7 | 3 | 3 | 6 | **4.8** |
| 10 | USAII Global AI Hackathon (undergrad) | [usaii-global-ai-hackathon-2026.devpost.com](https://usaii-global-ai-hackathon-2026.devpost.com/) | **Jun 21, 2026** | 3 | 5 | 2 | 4 | **3.5** |

\*AIMO PP4: highest formula fit, lowest *current* win % (expect 4k+ teams, labs). *O* assumes only legal SC/ensembling—not 151B-style differential LB oracle mining on private items.

**Not ranked as enter-now comps:** LiveBench / LiveCodeBench (leaderboard hunts, no prize loop); FrontierMath (Epoch benchmark + problem workshops, not multi-submit Kaggle); MLSys 2026 Agent Track (closed Apr 24); Hackenza 2026 TTA (CV, ended); IOAI 2026 (human olympiad pipeline, not transductive ML).

---

## Per-opportunity notes (playbook sketches)

### 1. ICML AI4Math — Codabench (Tracks 1–4)

**Why formula applies:** Math/science tasks with hidden grading, iterative submissions May 1–Jun 15. Track 3 (SeePhys Pro) = multimodal physics with exact match + LLM judge—closest to 151B “generate → normalize → verify.” Track 2 = Lean proving with `leanprover/comparator` anti-cheat. Track 4 (ShadowBench) = NL→Lean autoformalization.

**Caveats:** Formal tracks punish “oracle” label use; no Kaggle-style unlimited daily submits. Track 1 (FormalRx) is evaluator/classification, not integer `\boxed{}`.

**Playbook:** Reuse gold-verify loop: multi-sample reasoning, majority on extracted answers (Track 3), or parallel proof attempts + compiler filter (Tracks 2/4). Document format rules per error taxonomy (Track 1). Ship short ICML-format tech report by Jun 15.

### 2. NVIDIA Nemotron Reasoning Challenge

**Why formula applies:** Hidden test, notebook constraints, Alice-in-Wonderland logic with `\boxed{}` answers—same extraction/normalization muscle as 151B. Community already running GRPO + vLLM + high-token inference.

**Caveats:** ~$106k pool but **Featured** Kaggle scale; midpoint (Apr 9) passed. Rules require open-source writeup; check submission cap/day. **O=5:** LB probing helps only within daily submit limits—not 943-item course-style unlimited ablation.

**Playbook:** Port thinking-twin SC@N + verifier pass (constraint check on puzzle text). SFT on public puzzle format, then GRPO if 2×GPU available. Treat each submit as lottery ticket only after smoke gate—same four-gate discipline.

### 3. CAR-bench @ IJCAI-ECAI 2026

**Why formula applies:** **Pass^3** on hidden 250 tasks = ensemble/consistency metric by design. Public dev leaderboard + two official hidden evaluations (Jul 10, Jul 19). Agent harness + tool policies match Rain’s verification/oracle-overlay mindset for *refusal* and *disambiguation* dimensions.

**Caveats:** Automotive voice domain, not math. **Illegal:** training on hidden task text, sharing hidden labels, API key leakage in PRs. Cerebras track caps 15 teams.

**Playbook:** Wrap 151B-style “teacher overlay” as harness rules: force clarify/refuse when tool missing; self-consistency across 3 trials; multi-pass Codex on Cerebras track within time budget. Register now; iterate on public 254 tasks.

### 4. Mega Agent-A-Thon

**Why formula applies:** Low-friction agent demo; students-only → **W=9**. Good for narrative + portfolio, not transductive math.

**Caveats:** Requires **2–3 person team**; “submissions open soon” on Devpost; companies excluded.

**Playbook:** Demo “verified math agent” or competition postmortem agent using your inference+gold pipeline as product story. 10-day sprint, no LB mining.

### 5. AIMO Progress Prize 4 (monitor)

**Why formula applies:** **Gold-standard** transfer: integer answers 0–99999, penalized accuracy, private rerun, H100 notebook, multi-submit lottery for variance (AIMO3 postmortem). Rain’s 151B stack is literally this game.

**Caveats:** PP3 closed Apr 15, 2026; PP4 unannounced. Expect 4k+ teams, Nemotron-class labs. **Oracle mining that worked on course LB (differential submits, back-solve) is largely ILLEGAL** on AIMO private set—see ethics below.

**Playbook:** Watch [aimoprize.com/participate](https://aimoprize.com/participate). Pre-build: Nemotron/Qwen SC notebooks, format rules doc, verifier voting (per AIMO3 open analysis). When PP4 drops, sprint with legal SC only.

### 6. Google Cloud Rapid Agent Hackathon

**Why formula applies:** Agent + Gemini/GCP; deadline **Jun 11** (7 days).

**Caveats:** General hackathon; subjective judging; crowded; not hidden-holdout math.

**Playbook:** Only if team already has GCP credits; thin slice of 151B as “verified reasoning agent” MVP.

### 7–8. ARC Prize 2026 (AGI-2 / AGI-3)

**Why formula applies:** Private eval, $2M pool, test-time search/program synthesis (AGI-2); interactive exploration (AGI-3). TTC angle.

**Caveats:** **No internet** on Kaggle eval—kills API teacher overlays. Open-source mandatory. AGI-2 top scores ~24–43%—different from math `\boxed{}`. Weak transductive oracle fit.

**Playbook:** Long summer project; hybrid DSL + small model (NVARC style), not 151B transductive loop. Milestone open-source Jun 30 / Sep 30 for AGI-3 cash.

### 9. NeuroGolf (IJCAI)

**Why formula applies:** ARC tasks, hidden test, $50k.

**Caveats:** **Minimize ONNX size**, not LLM inference at scale. Wrong core skill.

**Playbook:** Deprioritize unless pivoting to tiny net distillation research.

### 10. USAII Global AI Hackathon

**Why formula applies:** Student track, Jun 14–21 build window.

**Caveats:** Qualifier gate; large global field; product pitch not benchmark optimization.

**Playbook:** Only if productizing 151B learnings; else skip.

---

## Ethics / rules — legal vs illegal adaptation

| Tactic (151B-style) | Usually legal | Often illegal / disqualifying |
|---------------------|---------------|-------------------------------|
| Self-consistency, majority vote, high-temp multi-sample | Yes | — |
| Thinking / no-thinking twins, SC@N | Yes | — |
| Per-item format normalization (post-process rules) | Yes if no peeking at hidden labels | Using hidden gold to tune rules |
| Verifier re-rank (code exec, constraint check) | Yes | Fabricating tool outputs (CAR-bench anti-pattern) |
| Many submissions to estimate variance | Yes within daily caps | Sharing private test questions/answers |
| LB delta / differential submit “gold mining” | **Course comps only if allowed** | **AIMO/Kaggle private holdout** — test leakage |
| External data (Wolfram, web) on test items | No on closed notebook comps | Yes — rule violation |
| Teacher/oracle model on contested IDs | Yes on **public** dev set | Hidden-label oracle overlay |
| Back-solve from submission feedback | Rarely allowed on private LB | Treat as cheating unless rules explicit |

**Rule of thumb:** If the tactic requires knowing the answer on a hidden item, it does not transfer—only the *machinery* (ensemble, verify, normalize) transfers.

---

## Related doc

See also `post_comp/COMPETITION_TARGETS.md` (June 3 student-strategy snapshot).

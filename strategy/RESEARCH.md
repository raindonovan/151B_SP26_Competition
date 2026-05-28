# PLAYBOOK RESEARCH

**Updated**: 2026-05-28 (Day 4 start)
**Note**: Research notes specific to the 0.85 push. Earlier research lives at `INFERENCE_OPTIMISATION_RESEARCH.md` and `docs/RESEARCH.md`.

## Round 2 research prompts (HELD — Rain to approve dispatch)

### R1 — TIR + vLLM + Qwen3-4B-Thinking implementations

**Question**: Is there an existing tool, repo, blog post, or recipe for running Tool-Integrated Reasoning (TIR) with vLLM on Qwen3-4B-Thinking (or close substitute like Qwen2.5-Math-7B-Instruct)? Specifically:
1. Has any AIMO competitor, paper, or open-source project implemented mid-generation Python execution with vLLM as the inference engine?
2. What is the canonical pattern for pausing vLLM generation, executing a code block in a sandbox, and resuming with the result as a new system message?
3. Is there a wrapper library (Numina's repo, Hugging Face's `lighteval`, NeMo Skills, etc.) we can adopt directly vs build from scratch?
4. What's the engineering cost estimate from someone who's done this exact thing?
5. CRITICAL: confirm or deny that vLLM is a feasibility blocker for TIR. If it is, what's the alternative inference engine (e.g., transformers + custom loop, sglang, llama.cpp)?

### R2 — Process Reward Model (PRM) without external API

**Question**: Given we cannot make external API calls in run_inference(), can we use Qwen2.5-Math-PRM-7B (Hugging Face) locally to score reasoning traces?
1. Is the model small enough to fit alongside Qwen3-4B-Thinking on a single A100 80GB during inference?
2. What's the throughput cost of scoring N=8 candidates per item with PRM?
3. Are there lighter PRMs (smaller param count) with comparable performance on math reasoning?
4. Has any AIMO competitor used PRM-based BoN selection in their submitted solution?

### R3 — Distillation success cases on Qwen3-4B

**Question**: When does distilling DeepSeek-R1 / GPT / Claude / QwQ traces onto Qwen3-4B work, and when does it fail?
1. We tried 3-arm teacher SFT earlier and got regression (v4 scored 0.597 vs base 0.646). Why?
2. What's the right number of training items for a 4B model — 100, 1000, 10000?
3. Should we use chain-of-thought traces (full reasoning) or just final answers?
4. Does mixing teachers (Claude + GPT + R1) hurt or help vs single-teacher consistency?
5. What does the literature say about Qwen3-4B being "trace-style-sensitive" — does it reject styles unlike its own?

### R4 — GenSelect implementation gotchas

**Question**: NVIDIA's AIMO-2 winning GenSelect technique — what are the implementation traps we should know about?
1. Our PoC failed because the selector was given truncated candidates (only ~500 chars instead of full reasoning). Is there a canonical truncation budget per candidate?
2. Should the selector see thinking blocks or just final answers?
3. AIMO-2 winner used N=64 candidates with subsets of 16, repeated 64 times with majority over selections. Can a smaller version (N=8 from existing run14b) work?
4. What's the selector prompt structure?

## Earlier research (already done — don't repeat)

- **AIMO winners deep-dive**: see `INFERENCE_OPTIMISATION_RESEARCH.md`
- **Hendrycks grader source**: see `docs/FINDINGS.md` "THE HENDRYCKS GRADER FIND" section
- **Information-theoretic ceiling on back-solve**: see `docs/FINDINGS.md` Bshouty COLT 2009 reference
- **Wolfram failure-mode taxonomy**: see `docs/WOLFRAM_FINDINGS.md`

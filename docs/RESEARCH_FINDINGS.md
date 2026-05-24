# Research Findings for Inference Optimization

## SC-TIR (AIMO Winner — NuminaMath/NVIDIA)
- Code execution DURING reasoning, not post-hoc
- Won both AIMO-1 and AIMO-2
- Requires TIR-trained model (we don't have this)
- Key: model interleaves natural language + Python REPL

## PROVE (Programs as Verifiers)
- Post-hoc: generate N solutions, write Python verification, filter
- Works on small models (0.5B-7B, paper showed +5-7pp gains)
- Our result: SFT v4 model CANNOT write code (35/35 no_code)
- SFT prior overwhelms any code-generation prompt
- Viable only with BASE model (two-model pipeline, deferred)

## NL Verification
- Asking model "which answer is correct?" with two candidates
- Unreliable below 13B parameters (Zhang et al. 2024)
- Our result: 3/6 returned labels ("A"/"B") instead of actual answers
- Verdict: SKIP for 4B model

## Key Principles
- Prompt matching is critical (AIMO winner finding)
- SC=16 majority voting is our primary verification method
- Temperature diversification (T=0.6 + T=1.0) improves SC diversity
- V3 shape filter = +0.7pp (confirmed empirically)
- 32K tokens = +2.5pp over 16K (confirmed empirically)

## Ideas Not Yet Tested
- Calculator-mode PROVE (one-line expressions instead of full programs)
- Self-healing retry (feed error back for one retry)
- Element-wise multi-answer verification
- Functional Majority Voting (vote on program outputs not strings)
- PROVE with base model (two-model pipeline)

"""Prompt registry — single source of truth for inference and SFT data prep.

Imported by `scripts/run_vllm_experiment.py` (inference) and
`training/prepare_*_sft.py` (SFT data construction). Kept free of heavy
imports (no torch / transformers / vllm) so the SFT data-prep venv can
import it without the inference stack.
"""

# Prompt registry. Each policy's strings are stored verbatim — do NOT replace
# duplicate text across policies with shared variables or references. The
# redundancy is intentional: a reader auditing any single policy needs to see
# its exact text without cross-referencing other policies. Treat this as
# config, not code.
PROMPTS = {
    "v1-baseline": {
        "mcq": (
            "You are an expert mathematician. "
            "Read the problem and the answer choices below, then select the single best answer. "
            "Output ONLY the letter of your chosen option inside \\boxed{}, e.g. \\boxed{C}."
        ),
        "free": (
            "You are an expert mathematician. Solve the problem step-by-step. "
            "Put your final answer inside \\boxed{}. "
            "If the problem has multiple sub-answers, separate them by commas inside a single \\boxed{}, "
            "e.g. \\boxed{3, 7}. "
            "Give numerical answers to at least 4 significant figures, unless the problem specifies a different precision."
        ),
    },
    "v2-mcq-commit": {
        "mcq": (
            "You are an expert mathematician. Choose the single correct option from the choices below. "
            "After your reasoning, output exactly one final answer in the form \\boxed{LETTER}, where LETTER is one of A, B, C, etc. "
            "Stop generating immediately after \\boxed{}."
        ),
        "free": (
            # Identical to v1-baseline.free — copied verbatim for auditability.
            "You are an expert mathematician. Solve the problem step-by-step. "
            "Put your final answer inside \\boxed{}. "
            "If the problem has multiple sub-answers, separate them by commas inside a single \\boxed{}, "
            "e.g. \\boxed{3, 7}. "
            "Give numerical answers to at least 4 significant figures, unless the problem specifies a different precision."
        ),
    },
}

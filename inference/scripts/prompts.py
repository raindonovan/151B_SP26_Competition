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
    # V1 ablation: counting instruction at the top of the user message only.
    # System prompt kept verbatim from v1-baseline (option i) so the ablation
    # isolates the user-wrapper change, not a system-prompt change.
    "v2-counting-top": {
        "mcq": (
            # Identical to v1-baseline.mcq — copied verbatim for auditability.
            "You are an expert mathematician. "
            "Read the problem and the answer choices below, then select the single best answer. "
            "Output ONLY the letter of your chosen option inside \\boxed{}, e.g. \\boxed{C}."
        ),
        "free": (
            # Identical to v1-baseline.free — copied verbatim for auditability.
            "You are an expert mathematician. Solve the problem step-by-step. "
            "Put your final answer inside \\boxed{}. "
            "If the problem has multiple sub-answers, separate them by commas inside a single \\boxed{}, "
            "e.g. \\boxed{3, 7}. "
            "Give numerical answers to at least 4 significant figures, unless the problem specifies a different precision."
        ),
        "user_wrapper": "top_only",
    },
    # V2 ablation: counting instruction bookended — at top AND end of user message.
    # MathIF "repeat" trick: re-stating the format constraint immediately before
    # the model generates its final answer counteracts long-CoT context drift.
    "v2-counting-bookend": {
        "mcq": (
            # Identical to v1-baseline.mcq — copied verbatim for auditability.
            "You are an expert mathematician. "
            "Read the problem and the answer choices below, then select the single best answer. "
            "Output ONLY the letter of your chosen option inside \\boxed{}, e.g. \\boxed{C}."
        ),
        "free": (
            # Identical to v1-baseline.free — copied verbatim for auditability.
            "You are an expert mathematician. Solve the problem step-by-step. "
            "Put your final answer inside \\boxed{}. "
            "If the problem has multiple sub-answers, separate them by commas inside a single \\boxed{}, "
            "e.g. \\boxed{3, 7}. "
            "Give numerical answers to at least 4 significant figures, unless the problem specifies a different precision."
        ),
        "user_wrapper": "bookend",
    },
}

# ---- User-message wrapper templates (V1/V2 counting prompt) ----
# Applied in build_prompt() to free-form questions only. MCQ messages are
# never wrapped. Format strings use {n} for the expected answer count.

USER_PREFIX_MULTI = (
    "This question requires exactly {n} answers. "
    "Your final answer must be a single \\boxed{{}} containing exactly {n} values "
    "separated by commas (e.g. \\boxed{{ans_1, ans_2}} for N=2).\n\n"
)

USER_PREFIX_SINGLE = (
    "This question requires a single answer. "
    "Provide it inside a single \\boxed{}.\n\n"
)

# Bookend suffix — V2 only. Re-states the constraint after the question text
# so it is in recent context when the model generates its final boxed answer.
USER_SUFFIX_MULTI = (
    "\n\nReminder: your final answer must contain exactly {n} comma-separated "
    "values inside a single \\boxed{{}}. Do not produce multiple \\boxed{{}} blocks."
)

USER_SUFFIX_SINGLE = (
    "\n\nReminder: your final answer must be inside a single \\boxed{}."
)


def count_ans_placeholders(question: str) -> int:
    """Count [ANS] placeholders. Returns 1 if none found (single-answer question)."""
    n = question.count("[ANS]")
    return n if n > 0 else 1

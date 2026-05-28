# Variants and Prompts — Implementation Spec

Concrete spec for the V0-V4 ablation in §7 of the prompt engineering doc. Hand this to claude_vscode for execution. Two file changes plus one new file.

## Overview

V0 = baseline (config fixes only, no prompt change). V1-V2 are prompt changes. V3-V4 are pipeline changes (shape filter, temperature ladder). The actual *prompt strings* only change between V0 → V1 → V2. V3 and V4 reuse V2's prompt.

## File 1: `scripts/prompts.py` (additions)

Append two new entries to the `PROMPTS` dict and add the user-message wrapper constants and helpers. Existing entries (`v1-baseline`, `v2-mcq-commit`) stay unchanged.

```python
# ---- New constants for V1/V2 user-message wrappers ----

# Top prefix injected before the question text.
# For free-form multi-answer questions (n>1):
USER_PREFIX_MULTI = (
    "This question requires exactly {n} answers. "
    "Your final answer must be a single \\boxed{{}} containing exactly {n} values "
    "separated by commas. Example for {n}=2: \\boxed{{value_1, value_2}}.\n\n"
)

# For free-form single-answer questions (n=1):
USER_PREFIX_SINGLE = (
    "This question requires a single answer. "
    "Provide it inside a single \\boxed{{}}.\n\n"
)

# Bookend suffix appended after the question text. V2 only.
USER_SUFFIX_MULTI = (
    "\n\nReminder: your final answer must contain exactly {n} comma-separated "
    "values inside a single \\boxed{{}}. Do not produce multiple \\boxed{{}} blocks."
)

USER_SUFFIX_SINGLE = (
    "\n\nReminder: your final answer must be inside a single \\boxed{{}}."
)


# ---- New PROMPTS entries (append to existing dict) ----

PROMPTS["v2-counting-top"] = {
    "mcq": (
        # Identical to v1-baseline.mcq — kept verbatim per the file's convention.
        "You are an expert mathematician. "
        "Read the problem and the answer choices below, then select the single best answer. "
        "Output ONLY the letter of your chosen option inside \\boxed{}, e.g. \\boxed{C}."
    ),
    "free": (
        # Identical to v1-baseline.free.
        "You are an expert mathematician. Solve the problem step-by-step. "
        "Put your final answer inside \\boxed{}. "
        "If the problem has multiple sub-answers, separate them by commas inside a single \\boxed{}, "
        "e.g. \\boxed{3, 7}. "
        "Give numerical answers to at least 4 significant figures, unless the problem specifies a different precision."
    ),
    "user_wrapper": "top_only",   # signal to build_prompt
}

PROMPTS["v2-counting-bookend"] = {
    "mcq": (
        # Identical to v1-baseline.mcq.
        "You are an expert mathematician. "
        "Read the problem and the answer choices below, then select the single best answer. "
        "Output ONLY the letter of your chosen option inside \\boxed{}, e.g. \\boxed{C}."
    ),
    "free": (
        # Identical to v1-baseline.free.
        "You are an expert mathematician. Solve the problem step-by-step. "
        "Put your final answer inside \\boxed{}. "
        "If the problem has multiple sub-answers, separate them by commas inside a single \\boxed{}, "
        "e.g. \\boxed{3, 7}. "
        "Give numerical answers to at least 4 significant figures, unless the problem specifies a different precision."
    ),
    "user_wrapper": "bookend",    # signal to build_prompt
}


# ---- Helpers (additions) ----

def count_ans_placeholders(question: str) -> int:
    """Count [ANS] placeholders. Default to 1 if none found (single-answer)."""
    n = question.count("[ANS]")
    return n if n > 0 else 1
```

## File 2: `scripts/run_vllm_experiment.py` (modify `build_prompt`)

Replace the existing `build_prompt` with this one. It reads `user_wrapper` from the policy and applies the prefix/suffix accordingly. Backward compatible: policies without `user_wrapper` (v1-baseline, v2-mcq-commit) behave exactly as before.

```python
from scripts.prompts import (
    PROMPTS,
    USER_PREFIX_MULTI,
    USER_PREFIX_SINGLE,
    USER_SUFFIX_MULTI,
    USER_SUFFIX_SINGLE,
    count_ans_placeholders,
)

def build_prompt(question: str, options, policy: dict) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for a question under `policy`.

    If policy includes `user_wrapper`, the user message is wrapped with a
    counting prefix and (for "bookend") a closing reminder. Wrapper applies
    to free-form questions only — MCQ user messages are unchanged.
    """
    if options:
        labels = [chr(65 + i) for i in range(len(options))]
        opts_text = "\n".join(
            f"{lbl}. {opt.strip()}" for lbl, opt in zip(labels, options)
        )
        return policy["mcq"], f"{question}\n\nOptions:\n{opts_text}"

    # Free-form path
    wrapper = policy.get("user_wrapper")
    if wrapper is None:
        return policy["free"], question

    n = count_ans_placeholders(question)
    if n > 1:
        prefix = USER_PREFIX_MULTI.format(n=n)
        suffix = USER_SUFFIX_MULTI.format(n=n) if wrapper == "bookend" else ""
    else:
        prefix = USER_PREFIX_SINGLE
        suffix = USER_SUFFIX_SINGLE if wrapper == "bookend" else ""

    return policy["free"], f"{prefix}{question}{suffix}"
```

## File 3 (new): `scripts/variants.py`

The variant registry. Each variant is a *delta* on top of the previous variant. `resolve_variant("V3_shape_filter")` returns the full merged config.

```python
"""Variant registry for the V0-V4 prompt-engineering ablation.

Each variant is defined as the DIFF from the previous variant. To get the
full config for a variant, call resolve_variant(name) — it walks the
ordered list and merges left-to-right.

Usage:
    from scripts.variants import resolve_variant
    config = resolve_variant("V3_shape_filter")
    # config has all keys: prompt_version, max_new_tokens, presence_penalty,
    # n_samples, temperature, temperature_ladder, shape_filter
"""

# Variant deltas. Each dict contains ONLY the keys that change vs the
# previous variant in VARIANT_ORDER.
VARIANTS = {
    "V0_baseline": dict(
        prompt_version="v1-baseline",
        max_new_tokens=32768,
        presence_penalty=1.0,
        n_samples=8,
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        min_p=0.0,
        repetition_penalty=1.0,
        temperature_ladder=None,    # single-temp
        shape_filter=False,
    ),
    "V1_counting_top": dict(
        prompt_version="v2-counting-top",
    ),
    "V2_counting_bookend": dict(
        prompt_version="v2-counting-bookend",
    ),
    "V3_shape_filter": dict(
        shape_filter=True,
    ),
    "V4_temp_diversification": dict(
        temperature_ladder=[0.5, 0.7, 0.9, 1.1],
        # `temperature` becomes irrelevant when ladder is set;
        # SC runner reads ladder if present, else falls back to temperature.
    ),
}

# Order matters: each variant is the delta on top of the previous.
VARIANT_ORDER = [
    "V0_baseline",
    "V1_counting_top",
    "V2_counting_bookend",
    "V3_shape_filter",
    "V4_temp_diversification",
]


def resolve_variant(name: str) -> dict:
    """Merge deltas left-to-right up through `name`. Returns full config."""
    if name not in VARIANT_ORDER:
        raise KeyError(f"Unknown variant: {name!r}. Known: {VARIANT_ORDER}")
    config = {}
    for v in VARIANT_ORDER:
        config.update(VARIANTS[v])
        if v == name:
            break
    return config


def all_variants() -> list[str]:
    """Return the full ordered list of variant names."""
    return list(VARIANT_ORDER)
```

## How the prompt actually looks at runtime

For a hypothetical multi-answer question:

> Find the roots of the quadratic equation x² - 5x + 6 = 0. Provide the smaller root [ANS] and the larger root [ANS].

**V0** (existing v1-baseline) sends to the model:
- System: "You are an expert mathematician. Solve the problem step-by-step. Put your final answer inside \\boxed{}. If the problem has multiple sub-answers, separate them by commas inside a single \\boxed{}, e.g. \\boxed{3, 7}. Give numerical answers to at least 4 significant figures..."
- User: "Find the roots of the quadratic equation x² - 5x + 6 = 0. Provide the smaller root [ANS] and the larger root [ANS]."

**V1** (counting at top) sends:
- System: (same as V0)
- User: "This question requires exactly 2 answers. Your final answer must be a single \\boxed{} containing exactly 2 values separated by commas. Example for 2: \\boxed{value_1, value_2}.\n\nFind the roots of the quadratic equation x² - 5x + 6 = 0. Provide the smaller root [ANS] and the larger root [ANS]."

**V2** (bookend) sends:
- System: (same as V0)
- User: "This question requires exactly 2 answers. Your final answer must be a single \\boxed{} containing exactly 2 values separated by commas. Example for 2: \\boxed{value_1, value_2}.\n\nFind the roots of the quadratic equation x² - 5x + 6 = 0. Provide the smaller root [ANS] and the larger root [ANS].\n\nReminder: your final answer must contain exactly 2 comma-separated values inside a single \\boxed{}. Do not produce multiple \\boxed{} blocks."

**V3** is V2's prompt + shape filter applied to the voting pool (no prompt change).
**V4** is V3's prompt + temperature ladder across samples (no prompt change).

## What's NOT here

- **Shape filter implementation** (V3). That's part C of the elaboration plan — separate file.
- **SC runner modifications** to read `temperature_ladder` and loop. That's an edit to `run_vllm_sc.py`, also separate.
- **Smoke test script.** Part D of the elaboration plan.
- **Aggregator script.** Part E.

## Verification before running

Before kicking off Phase 1, verify with a single hand-built call:

1. `from scripts.variants import resolve_variant; resolve_variant("V2_counting_bookend")` returns the expected dict.
2. `from scripts.run_vllm_experiment import build_prompt; from scripts.prompts import PROMPTS` then call `build_prompt(question_with_two_ANS, None, PROMPTS["v2-counting-bookend"])` and inspect the user message. Confirm both prefix and suffix appear, with N=2 substituted.
3. Same call with a question that has NO `[ANS]` placeholders should produce a single-answer prefix (`"This question requires a single answer..."`).
4. Same call with `options=[...]` (MCQ) should produce the unchanged MCQ user message.

If all four pass, the prompt scaffolding is correct. Move on to C (shape filter code).

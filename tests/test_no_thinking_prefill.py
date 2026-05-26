"""Unit tests for the NoThinking-prefill helper in run_hybrid_inference.py.

Verifies that --no-thinking appends the NoThinking-paper transition sentence
to the rendered chat template, closing the auto-opened <think> block.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "scripts"))

from run_hybrid_inference import (  # noqa: E402
    NO_THINKING_PREFILL,
    maybe_apply_no_thinking_prefill,
)


def test_prefill_is_no_op_when_disabled():
    template_output = "<|im_start|>assistant\n<think>\n"
    out = maybe_apply_no_thinking_prefill(template_output, no_thinking=False)
    assert out == template_output


def test_prefill_appended_when_enabled():
    template_output = "<|im_start|>assistant\n<think>\n"
    out = maybe_apply_no_thinking_prefill(template_output, no_thinking=True)
    assert out == template_output + NO_THINKING_PREFILL


def test_prefill_text_matches_paper_exact():
    # Paper text from arxiv 2504.09858: "Okay, I think I have finished thinking."
    # followed by closing </think> and two newlines.
    assert NO_THINKING_PREFILL == "Okay, I think I have finished thinking.\n</think>\n\n"


def test_prefill_closes_think_block():
    # Combined with the chat template's auto-opened <think>\n, the full string
    # has a balanced <think>...</think> pair.
    template_output = "before\n<think>\n"
    full = maybe_apply_no_thinking_prefill(template_output, no_thinking=True)
    assert "<think>" in full and "</think>" in full
    # The </think> appears AFTER the <think>
    assert full.index("</think>") > full.index("<think>")


def test_prefill_empty_prompt():
    # Edge: empty prompt → still appends prefill when flag set
    out = maybe_apply_no_thinking_prefill("", no_thinking=True)
    assert out == NO_THINKING_PREFILL
    out2 = maybe_apply_no_thinking_prefill("", no_thinking=False)
    assert out2 == ""

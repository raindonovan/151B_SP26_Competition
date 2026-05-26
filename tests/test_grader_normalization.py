"""Unit tests for scripts/apply_grader_normalization.py.

Modes covered:
  dfrac_only — diagnostic probe (Kaggle canonical is \\dfrac; this mode is
               WRONG-DIRECTION but kept for forensic evidence)
  minimal    — safe submission rules: thin-space and \\left/\\right strip
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "scripts"))

from apply_grader_normalization import normalize_row, find_last_box  # noqa: E402


def _norm(text, mode):
    new_text, _ = normalize_row(text, mode)
    return new_text


# 1. dfrac_only: \boxed{\dfrac{1}{2}} → \boxed{\frac{1}{2}}
def test_dfrac_only_converts():
    assert _norm(r"\boxed{\dfrac{1}{2}}", "dfrac_only") == r"\boxed{\frac{1}{2}}"


# 1b. minimal: \dfrac left alone (Kaggle canonical)
def test_minimal_preserves_dfrac():
    assert _norm(r"\boxed{\dfrac{1}{2}}", "minimal") == r"\boxed{\dfrac{1}{2}}"


# 2. MCQ letter — no change in either mode
def test_mcq_letter_no_change():
    assert _norm(r"\boxed{A}", "dfrac_only") == r"\boxed{A}"
    assert _norm(r"\boxed{A}", "minimal") == r"\boxed{A}"


# 3. minimal: comma+space preserved (Kaggle canonical)
def test_minimal_preserves_comma_space():
    src = r"\boxed{7, -11, 4}"
    assert _norm(src, "minimal") == src
    assert _norm(src, "dfrac_only") == src


# 4. minimal: thin-space stripped
def test_minimal_thin_space_strip():
    assert _norm(r"\boxed{61\,62}", "minimal") == r"\boxed{6162}"
    # dfrac_only does NOT touch thin-space
    assert _norm(r"\boxed{61\,62}", "dfrac_only") == r"\boxed{61\,62}"


# 5. Multiple boxes — only LAST modified
def test_multiple_boxes_only_last():
    src = r"answer: \boxed{1} oh wait \boxed{\dfrac{2}{3}}"
    out = _norm(src, "dfrac_only")
    assert out == r"answer: \boxed{1} oh wait \boxed{\frac{2}{3}}"
    # earlier dfrac left alone in either mode
    src2 = r"first \boxed{\dfrac{1}{1}} then \boxed{2}"
    assert _norm(src2, "dfrac_only") == src2
    assert _norm(src2, "minimal") == src2


# 6. No box → unchanged
def test_no_box_unchanged():
    src = "just some prose with no answer"
    assert _norm(src, "dfrac_only") == src
    assert _norm(src, "minimal") == src


# 7. NaN / None / non-string → unchanged
def test_nan_unchanged():
    nan = math.nan
    out, fired = normalize_row(nan, "minimal")
    assert isinstance(out, float) and math.isnan(out)
    assert fired is None
    out2, fired2 = normalize_row(None, "minimal")
    assert out2 is None
    assert fired2 is None


# 8. minimal: \left and \right stripped
def test_minimal_left_right_strip():
    src = r"\boxed{\left(\frac{1}{2}\right)}"
    assert _norm(src, "minimal") == r"\boxed{(\frac{1}{2})}"
    # dfrac_only doesn't touch \left/\right
    assert _norm(src, "dfrac_only") == src


# 9. minimal: thin-space + left/right combo
def test_minimal_combo():
    src = r"\boxed{\left( a\,b\right)}"
    assert _norm(src, "minimal") == r"\boxed{( ab)}"


# 10. dfrac_only: nested deep no-dfrac box → unchanged
def test_dfrac_only_no_dfrac_unchanged():
    src = r"\boxed{\frac{a^{n+1}}{b^{m-1}}}"
    assert _norm(src, "dfrac_only") == src
    # minimal leaves it alone too (no thin-space, no left/right)
    assert _norm(src, "minimal") == src


# Sanity: find_last_box matches nested braces correctly
def test_find_last_box_nested():
    src = r"text \boxed{\frac{a}{b}} more"
    box = find_last_box(src)
    assert box is not None
    start, end, inner = box
    assert inner == r"\frac{a}{b}"
    assert src[start:end] == r"\boxed{\frac{a}{b}}"


def test_unbalanced_brace_safe():
    src = r"\boxed{\frac{1}{2}"
    assert find_last_box(src) is None
    assert _norm(src, "minimal") == src
    assert _norm(src, "dfrac_only") == src


# \tfrac handled like \dfrac in dfrac_only; preserved in minimal
def test_tfrac():
    assert _norm(r"\boxed{\tfrac{1}{2}}", "dfrac_only") == r"\boxed{\frac{1}{2}}"
    assert _norm(r"\boxed{\tfrac{1}{2}}", "minimal") == r"\boxed{\tfrac{1}{2}}"

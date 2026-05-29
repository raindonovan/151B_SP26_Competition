"""Focused tests for the canonical post-inference normalizer."""

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "postprocessing", "scripts"))

from hendrycks_local import extract_mcq_letter, extract_last_boxed_content, is_equiv, strip_string  # noqa: E402
from normalizer import Normalizer  # noqa: E402


def test_hendrycks_local_free_form_extraction():
    text = r"scratch \boxed{1} later \boxed{\frac{3}{5}}"
    assert extract_last_boxed_content(text) == r"\frac{3}{5}"


def test_hendrycks_local_mcq_extraction_first_box():
    text = r"reasoning \boxed{B} no wait \boxed{D}"
    assert extract_mcq_letter(text) == "B"


def test_conservative_mcq_preserves_valid_response():
    norm = Normalizer(mode="conservative")
    item = {"id": 3, "options": ["A", "B", "C"]}
    response = r"reasoning... therefore \boxed{B}"
    assert norm.normalize(response, item) == response


def test_mcq_replaces_when_rescue_needed():
    norm = Normalizer(mode="conservative")
    item = {"id": 3, "options": ["A", "B", "C"]}
    response = "Reasoning shows B is best"
    assert norm.normalize(response, item) == r"\boxed{B}"


def test_multi_answer_consolidates_all_boxes():
    norm = Normalizer(mode="conservative")
    item = {"id": 15, "question": "[ANS] [ANS]"}
    response = r"part a \boxed{8} part b \boxed{NONE}"
    out = norm.normalize(response, item)
    assert out.endswith(r"Final answer: \boxed{8, NONE}")


def test_default_promotes_fraction_when_metadata_supports_it():
    norm = Normalizer(mode="default")
    item = {
        "id": 135,
        "question": "Probability [ANS]",
        "sheet_best_answer": r"\frac{3}{5}",
        "sheet_tier": 1,
        "sheet_confidence": 90,
        "teacher_sonnet": r"\frac{3}{5}",
        "teacher_gpt4": r"\frac{3}{5}",
        "teacher_oss": r"\frac{3}{5}",
    }
    response = r"work... \boxed{0.6}"
    out = norm.normalize_with_report(response, item)
    assert out.candidate == r"\frac{3}{5}"
    assert out.response.endswith(r"Final answer: \boxed{\frac{3}{5}}")


def test_aggressive_strips_trailing_zero_and_wrappers():
    norm = Normalizer(mode="aggressive")
    item = {"id": 423, "question": "Value [ANS]"}
    response = r"work... \boxed{\mathbf{-0.5000}}"
    out = norm.normalize_with_report(response, item)
    assert out.candidate == "-0.5"
    assert "TRAILING_ZERO_STRIP" in out.flags
    assert "LATEX_WRAPPER_STRIP" in out.flags


def test_aggressive_strips_multi_char_prefix():
    norm = Normalizer(mode="aggressive")
    item = {"id": 20, "question": "Mean [ANS]"}
    response = r"work... \boxed{Mean=228}"
    out = norm.normalize_with_report(response, item)
    assert out.candidate == "228"
    assert "MULTI_CHAR_PREFIX_STRIP" in out.flags


def test_per_item_override_force_value():
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as handle:
        handle.write("id,override_type,value,evidence,added_by,date\n")
        handle.write('42,force_value,"No\\,Yes\\,A",test,unit,2026-05-28\n')
        path = handle.name
    try:
        norm = Normalizer(mode="conservative", overrides_path=path)
        item = {"id": 42, "question": "[ANS] [ANS] [ANS]"}
        response = r"scratch \boxed{No}"
        out = norm.normalize_with_report(response, item)
        assert out.candidate == r"No\,Yes\,A"
        assert "OVERRIDE_FORCE_VALUE" in out.flags
    finally:
        os.unlink(path)


def test_hendrycks_equivalence_helpers_match_expected_behavior():
    assert is_equiv(r"\dfrac{1}{2}", r"\frac{1}{2}")
    assert not is_equiv("0.6", r"\frac{3}{5}")
    assert strip_string("x = 5") == "5"
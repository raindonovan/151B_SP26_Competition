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


def test_mcq_multi_select_preserves_all_letters():
    """Multi-select MCQ must keep every letter, not collapse to the last one."""
    norm = Normalizer(mode="conservative")
    item = {"id": 193, "options": ["o"] * 10}
    assert norm.normalize_with_report(r"\boxed{A,\ C,\ D}", item).candidate == "A,C,D"
    assert norm.normalize_with_report(r"\boxed{A, B}", item).candidate == "A,B"
    # single-letter still works
    assert norm.normalize_with_report(r"\boxed{B}", item).candidate == "B"


def test_multi_answer_consolidates_all_boxes():
    norm = Normalizer(mode="conservative")
    item = {"id": 15, "question": "[ANS] [ANS]"}
    response = r"part a \boxed{8} part b \boxed{NONE}"
    out = norm.normalize(response, item)
    assert out.endswith(r"Final answer: \boxed{8, NONE}")


def test_single_mode_does_not_auto_promote_fraction():
    # Under the value-equality grader, decimal == fraction, so the normalizer
    # must NOT auto-convert 0.6 -> 3/5 (that was the old default-mode behavior).
    norm = Normalizer()
    item = {
        "id": 135,
        "question": "Probability [ANS]",
        "sheet_best_answer": r"\frac{3}{5}",
        "sheet_tier": 1,
        "sheet_confidence": 90,
        "teacher_sonnet": r"\frac{3}{5}",
    }
    out = norm.normalize_with_report(r"work... \boxed{0.6}", item)
    assert out.candidate == "0.6"
    assert "FRACTION_PROMOTED" not in out.flags


def test_single_mode_does_not_auto_strip_trailing_zero_or_prefix():
    # Old aggressive transforms are gone: no trailing-zero strip, no prefix strip.
    norm = Normalizer()
    out = norm.normalize_with_report(r"work... \boxed{-0.5000}", {"id": 423, "question": "Value [ANS]"})
    assert out.candidate == "-0.5000"
    assert "TRAILING_ZERO_STRIP" not in out.flags
    out2 = norm.normalize_with_report(r"work... \boxed{Mean=228}", {"id": 20, "question": "Mean [ANS]"})
    assert "MULTI_CHAR_PREFIX_STRIP" not in out2.flags


def test_legacy_mode_args_still_accepted():
    # Callers passing old mode strings must not crash; behavior is identical.
    for m in ("conservative", "default", "aggressive", "single"):
        assert Normalizer(mode=m).normalize_with_report(r"\boxed{B}", {"id": 1, "options": ["x"] * 3}).candidate == "B"


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


# ── ACTION 1 anchor tests (Tier-1 normalizer build; must FAIL on pre-build code) ──

def test_multi_answer_defect_intermediate_plus_final_comma():
    # item-15 pattern: a 2-slot free_multi where an intermediate \boxed{8} appears
    # mid-reasoning AND the final \boxed{8, NONE} already has the correct comma-split.
    # The fixed normalizer must KEEP the final comma'd box (= "8, NONE"), NOT splice
    # the intermediate box in to produce "8, 8,NONE" / "8, NONE" length-mismatch.
    norm = Normalizer(mode="single")
    item = {"id": 15, "question": "part a [ANS] part b [ANS]"}
    response = r"work \boxed{8} more reasoning, final answers \boxed{8, NONE}"
    out = norm.normalize_with_report(response, item)
    assert out.candidate == "8, NONE", out.candidate


def test_duplicate_option_collapse_mcq():
    # MCQ where the response box holds a duplicated option letter "H, H".
    # Must collapse to the single letter "H".
    norm = Normalizer(mode="single")
    item = {"id": 9001, "question": "pick one", "options": ["A"] * 8}  # H = index 7
    response = r"reasoning \boxed{H, H}"
    out = norm.normalize_with_report(response, item)
    assert out.candidate == "H", out.candidate


def test_high_confidence_no_box_overrides():
    # 4 Tier-1 HIGH no-box overrides (229, 308, 383, 498). Each response has NO \boxed{};
    # the per_item_overrides.csv force_value must drive the final candidate.
    expected = {"229": "2", "308": "12", "383": "80", "498": "15"}
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as handle:
        handle.write("id,override_type,value,evidence,added_by,date\n")
        for iid, val in expected.items():
            handle.write(f"{iid},force_value,{val},4/4 SC unanimous,unit,2026-05-31\n")
        path = handle.name
    try:
        norm = Normalizer(mode="single", overrides_path=path)
        for iid, val in expected.items():
            item = {"id": int(iid), "question": "[ANS]"}
            response = "long rambling reasoning with no boxed answer at all"
            out = norm.normalize_with_report(response, item)
            assert out.candidate == val, (iid, out.candidate)
            assert "OVERRIDE_FORCE_VALUE" in out.flags, (iid, out.flags)
            assert f"\\boxed{{{val}}}" in out.response, (iid, out.response[-40:])
    finally:
        os.unlink(path)


def test_mcq_value_to_letter_via_value_equality():
    # item-141 pattern: MCQ whose options are numeric-valued; the response boxes a
    # number "3.0" that is VALUE-equal (not string-equal) to the option "3".
    # Must map to that option's letter. (3 is option index 2 → "C".)
    norm = Normalizer(mode="single")
    item = {"id": 141, "question": "choose", "options": ["1", "2", "3", "4"]}
    response = r"after computing \boxed{3.0}"
    out = norm.normalize_with_report(response, item)
    assert out.candidate == "C", out.candidate
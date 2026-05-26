"""Unit tests for scripts/find_truncated_samples.py."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "scripts"))

from find_truncated_samples import classify_sample, process  # noqa: E402


def whitespace_counter(s: str) -> int:
    return len(s.split())


def test_classify_truncated():
    # 100 tokens, max=100 -> 100 >= 100-5 -> truncated
    text = " ".join(["w"] * 100)
    assert classify_sample(text, max_tokens=100, count_tokens=whitespace_counter) == "truncated_max_tokens"


def test_classify_just_under_truncation():
    # 90 tokens, max=100 -> 90 < 95 -> not truncated; but no box -> no_boxed_answer
    text = " ".join(["w"] * 90)
    assert classify_sample(text, max_tokens=100, count_tokens=whitespace_counter) == "no_boxed_answer"


def test_classify_ok_with_box():
    text = "Some prose \\boxed{42} done"
    assert classify_sample(text, max_tokens=100, count_tokens=whitespace_counter) == "ok"


def test_classify_no_box():
    text = "prose without an answer"
    assert classify_sample(text, max_tokens=100, count_tokens=whitespace_counter) == "no_boxed_answer"


def test_classify_truncated_with_box_still_truncated():
    # Truncation takes priority over box presence
    text = "\\boxed{x} " + " ".join(["w"] * 200)
    assert classify_sample(text, max_tokens=100, count_tokens=whitespace_counter) == "truncated_max_tokens"


def test_classify_non_string():
    assert classify_sample(None, max_tokens=100, count_tokens=whitespace_counter) == "no_boxed_answer"


def test_process_endtoend():
    with tempfile.TemporaryDirectory() as td:
        inp = os.path.join(td, "in.jsonl")
        out = os.path.join(td, "out.tsv")
        rep = os.path.join(td, "rep.md")

        # Three items, each with two samples — mix of ok / truncated / no-box
        rows = [
            {"id": 10, "samples": ["pre \\boxed{1} ok", "no answer here at all"]},
            {"id": 11, "samples": ["\\boxed{2}", " ".join(["w"] * 100)]},
            {"id": 12, "samples": ["\\boxed{3}", "\\boxed{4}"]},
        ]
        with open(inp, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

        process(inp, max_tokens=100, output_path=out, report_path=rep,
                count_tokens=whitespace_counter)

        with open(out) as f:
            lines = [l.rstrip("\n").split("\t") for l in f]
        assert lines[0] == ["item_id", "sample_idx", "reason"]
        # 6 samples total, expect 3 non-ok: (10,1,no_box), (11,1,truncated)
        # Item 12 both ok
        non_ok = lines[1:]
        # Use sets of tuples to compare independent of order
        observed = {(r[0], r[1], r[2]) for r in non_ok}
        assert ("10", "1", "no_boxed_answer") in observed
        assert ("11", "1", "truncated_max_tokens") in observed
        # Item 12 should NOT appear
        assert not any(r[0] == "12" for r in non_ok)

        with open(rep) as f:
            md = f.read()
        assert "Total samples: **6**" in md
        assert "truncated_max_tokens" in md

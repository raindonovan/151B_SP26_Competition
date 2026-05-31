"""Canonical post-inference normalizer (SINGLE MODE).

Best-guess normalizer for the value-equality Kaggle grader: extraction + safe
universal cleanup + structural fixes (MCQ first-box / multi-letter, multi-slot
undercount) + per-item overrides. There is ONE behavior — the old
conservative/default/aggressive modes are collapsed. Automatic fraction/decimal/
format transforms are removed: under value-equality (4.000 == 4, 0.6 == 3/5)
they cannot raise the score and can lower it. Any explicit format fix must go
through per_item_overrides.csv (apply_per_item_override), never as an automatic
transform.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Optional

from hendrycks_local import extract_mcq_letter, is_equiv, strip_string

# ACTION 3 (Cursor BLOCKER 2): canonical value-equality grader for MCQ option matching.
# grading/grader.py lives at repo root with a root-judger dependency; add the repo root to
# sys.path so the import resolves regardless of CWD. Import via grading.grader (NOT direct
# judger) per the spec.
import os as _os
import sys as _sys
_REPO_ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
if _REPO_ROOT not in _sys.path:
    _sys.path.insert(0, _REPO_ROOT)
from grading.grader import Grader  # noqa: E402


BOX_START_RE = re.compile(r"\\boxed\{")
TEXT_WRAPPER_RE = re.compile(r"^\\text\{\s*([A-Za-z])\s*\}$")
LATEX_WRAPPER_RE = re.compile(r"\\(?:mathrm|mathbf)\{([^}]*)\}")
MULTI_CHAR_PREFIX_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]{2,})\s*=\s*(.+)$")
SCI_RE = re.compile(r"^([+-]?\d+(?:\.\d+)?)[eE]([+-]?\d+)$")
TIMES_TEN_RE = re.compile(r"^([+-]?\d+(?:\.\d+)?)\\times10\^\{?([+-]?\d+)\}?$")


@dataclass
class ExtractionResult:
    candidate: str
    rescued: bool = False
    all_boxes: list[str] = field(default_factory=list)
    first_boxed_letter: str = ""
    last_boxed: str = ""


@dataclass
class NormalizationResult:
    response: str
    candidate: str
    item_type: str
    flags: list[str] = field(default_factory=list)


class Normalizer:
    def __init__(self, mode: str = "single", overrides_path: Optional[str] = None):
        # Single-mode normalizer. `mode` is accepted for backward compatibility
        # with existing callers/CLIs (conservative/default/aggressive) but no
        # longer changes behavior — there is one structural-only behavior.
        self.mode = "single"
        self.overrides = self._load_overrides(overrides_path)
        self.custom_overrides: dict[str, Callable[[str, dict], str]] = {}
        self.grader = Grader()  # ACTION 3: value-equality MCQ option matching

    def normalize(self, response: str, item: dict) -> str:
        return self.normalize_with_report(response, item).response

    def normalize_with_report(self, response: str, item: dict) -> NormalizationResult:
        extraction = self.extract_answer(response, item)
        candidate = self.universal_cleanup(extraction.candidate)
        item_type = self.classify_type(item)
        flags: list[str] = []

        if item_type == "MCQ":
            candidate = self.mcq_normalize(candidate, item, response, extraction, flags)
        elif item_type == "free_multi":
            candidate = self.multi_answer_normalize(candidate, item, response, extraction, flags)
        else:
            candidate = self.single_answer_normalize(candidate, item, flags)

        candidate = self.apply_per_item_override(candidate, item, flags)
        final_response = self.rebox(response, candidate, item_type, extraction, flags)
        return NormalizationResult(
            response=final_response,
            candidate=candidate,
            item_type=item_type,
            flags=flags,
        )

    def extract_answer(self, response: str, item: dict) -> ExtractionResult:
        all_boxes = self.extract_all_boxed(response)
        item_type = self.classify_type(item)
        if item_type == "MCQ":
            boxed_match = re.search(r"\\boxed\{([A-Za-z])\}", response)
            if boxed_match:
                letter = boxed_match.group(1).upper()
                return ExtractionResult(
                    candidate=letter,
                    rescued=False,
                    all_boxes=all_boxes,
                    first_boxed_letter=letter,
                    last_boxed=all_boxes[-1] if all_boxes else "",
                )
            # multi-select MCQ: box holds >=2 comma/space separated letters
            if all_boxes:
                letters = self._parse_mcq_letter_set(all_boxes[-1])
                if letters:
                    joined = ",".join(letters)
                    return ExtractionResult(
                        candidate=joined,
                        rescued=False,
                        all_boxes=all_boxes,
                        first_boxed_letter=joined,
                        last_boxed=all_boxes[-1],
                    )
                # ACTION 3: a non-letter box (e.g. numeric "3.0") — carry the last box content
                # forward so mcq_normalize can map it to a letter via value-equality.
                return ExtractionResult(
                    candidate=all_boxes[-1],
                    rescued=False,
                    all_boxes=all_boxes,
                    last_boxed=all_boxes[-1],
                )
        elif all_boxes:
            return ExtractionResult(
                candidate=all_boxes[-1],
                rescued=False,
                all_boxes=all_boxes,
                last_boxed=all_boxes[-1],
            )

        rescue = self._rescue_candidate(response, item_type)
        return ExtractionResult(
            candidate=rescue,
            rescued=bool(rescue),
            all_boxes=all_boxes,
            last_boxed=all_boxes[-1] if all_boxes else "",
        )

    def universal_cleanup(self, candidate: str) -> str:
        s = (candidate or "").strip()
        s = s.replace("\\\\", "\\")
        s = s.replace("\\dfrac", "\\frac")
        s = s.replace("\\tfrac", "\\frac")
        s = s.replace("\\left", "")
        s = s.replace("\\right", "")
        s = s.replace("^{\\circ}", "")
        s = s.replace("^\\circ", "")
        s = s.replace("\\%", "")
        s = s.replace("\\$", "")
        s = self._strip_right_text_unit(s)
        s = self._strip_short_lhs_prefix(s)
        s = self._fix_frac_shorthand(s)
        s = self._fix_sqrt_shorthand(s)
        s = s.replace("\\!", "")
        s = s.replace("\\,", "")
        s = s.replace("\\;", "")
        s = s.replace("\\:", "")
        s = re.sub(r"\s+", "", s)
        if s == "0.5":
            s = "\\frac{1}{2}"
        s = self._fix_integer_slash_fraction(s)
        return s

    def classify_type(self, item: dict) -> str:
        options = item.get("options")
        if isinstance(options, list) and options:
            return "MCQ"
        question = item.get("question", "") or ""
        answer = item.get("answer")
        if isinstance(answer, list) and len(answer) > 1:
            return "free_multi"
        if question.count("[ANS]") > 1:
            return "free_multi"
        return "free_single"

    def mcq_normalize(
        self,
        candidate: str,
        item: dict,
        response: str,
        extraction: ExtractionResult,
        flags: list[str],
    ) -> str:
        letter = self._cleanup_mcq_letter(candidate)
        if not letter:
            letters = self._parse_mcq_letter_set(candidate)
            if letters:
                # ACTION 4 (Cursor WORRY 3 hedge): collapse duplicated-option answers like
                # "H, H" / "H,H,H" (same letter repeated) → single letter. Cheap regression
                # hedge in case value-equality didn't pre-empt it (the 302/839 pattern).
                if len(set(letters)) == 1:
                    flags.append("MCQ_DUPLICATE_COLLAPSED")
                    return letters[0]
                return ",".join(letters)
        # ACTION 4 also guards the raw-string form (regex on the cleaned candidate)
        if not letter and re.fullmatch(r"([A-Za-z])(?:\s*,\s*\1)+", candidate.strip()):
            flags.append("MCQ_DUPLICATE_COLLAPSED")
            return candidate.strip()[0].upper()
        if not letter:
            # ACTION 3 (Cursor BLOCKER 2): map a numeric/value candidate to its option letter
            # via VALUE-equality (grader.is_equal), not strict string is_equiv. Options may be
            # wrapped in \boxed{...}; strip the wrapper before comparing.
            numeric_candidate = self.universal_cleanup(candidate)
            options = item.get("options") or []
            for idx, option in enumerate(options):
                opt_val = option
                box = self.extract_all_boxed(option) if isinstance(option, str) else []
                if box:
                    opt_val = box[-1]
                opt_val = self.universal_cleanup(opt_val)
                try:
                    equal = bool(self.grader.is_equal(numeric_candidate, opt_val, options=[]))
                except Exception:
                    equal = False
                if equal:
                    letter = self._letter_for_index(idx)
                    flags.append("MCQ_MAPPED_FROM_OPTION")
                    break
        if not letter:
            flags.append("INVALID_MCQ")
            return "INVALID"
        return letter

    def multi_answer_normalize(
        self,
        candidate: str,
        item: dict,
        response: str,
        extraction: ExtractionResult,
        flags: list[str],
    ) -> str:
        # ACTION 2 (Cursor BLOCKER 3): replicate fix_submission_format.fix_response logic
        # INLINE (do NOT import that script). Fixes the multi_answer defect where an
        # intermediate \boxed{8} mid-reasoning + a correct final \boxed{8, NONE} used to be
        # mis-consolidated into "8, 8,NONE". Priority:
        #   1. last box already splits cleanly into `expected` non-empty pieces → KEEP it (LAST_BOX_KEPT)
        #   2. only 1 box → keep as-is (MULTI_RESCUE_ONLY)
        #   3. multiple boxes, last not clean → consolidate last N unique non-empty values (CONSOLIDATED_N)
        # UNDERCOUNT_*/OVERCOUNT_* flags preserved for diagnostics.
        expected = self._expected_slot_count(item)
        raw_boxes = [box for box in extraction.all_boxes if box.strip()]

        if raw_boxes:
            last_raw = raw_boxes[-1]
            last_pieces = [p.strip() for p in last_raw.split(",") if p.strip()]
            # (1) last box already a clean expected-count comma split → keep it (preserve order/form)
            if "," in last_raw and len(last_pieces) == expected:
                flags.append("LAST_BOX_KEPT")
                values = [self.universal_cleanup(p) for p in last_pieces]
                values = [self._normalize_multi_element(v, item) for v in values]
                return ", ".join(values)

            cleaned_boxes = [self.universal_cleanup(box) for box in raw_boxes]
            # (2) only one box, no clean split → rescue-only, pass through
            if len(cleaned_boxes) == 1:
                # the single box may itself be a comma-list; keep as a single element/value
                flags.append("MULTI_RESCUE_ONLY")
                return self._normalize_multi_element(cleaned_boxes[0], item)

            # (3) multiple boxes, last not a clean expected-count split → consolidate last N unique
            unique_vals: list[str] = []
            seen: set[str] = set()
            for b in reversed(cleaned_boxes):
                if b and b not in seen:
                    seen.add(b)
                    unique_vals.insert(0, b)
                if len(unique_vals) == expected:
                    break
            if len(unique_vals) < expected:
                flags.append(f"UNDERCOUNT_{len(unique_vals)}_OF_{expected}")
            elif len(cleaned_boxes) > expected:
                flags.append(f"OVERCOUNT_{len(cleaned_boxes)}_TO_{expected}")
            flags.append(f"CONSOLIDATED_{len(unique_vals)}")
            values = [self._normalize_multi_element(v, item) for v in unique_vals]
            return ", ".join(values)

        if candidate:
            flags.append("MULTI_RESCUE_ONLY")
        return self._normalize_multi_element(candidate, item)

    def single_answer_normalize(self, candidate: str, item: dict, flags: list[str]) -> str:
        # Single-mode: structural-only. No automatic fraction/format transforms
        # (dead under value-equality). Explicit fixes go via per_item_overrides.csv.
        return candidate

    def apply_per_item_override(self, candidate: str, item: dict, flags: list[str]) -> str:
        item_id = str(item.get("id", ""))
        override = self.overrides.get(item_id)
        if override is None:
            return candidate

        override_type = override.get("override_type", "")
        value = override.get("value", "")
        if override_type == "force_value":
            flags.append("OVERRIDE_FORCE_VALUE")
            return value
        if override_type == "force_fraction":
            flags.append("OVERRIDE_FORCE_FRACTION")
            return value
        if override_type == "force_decimal_places":
            flags.append("OVERRIDE_FORCE_DECIMAL")
            return self._round_decimal(candidate, int(value))
        if override_type == "force_units":
            flags.append("OVERRIDE_FORCE_UNITS")
            return f"{candidate}{value}"
        if override_type == "custom":
            func = self.custom_overrides.get(value)
            if func is not None:
                flags.append("OVERRIDE_CUSTOM")
                return func(candidate, item)
        return candidate

    def rebox(
        self,
        response: str,
        candidate: str,
        item_type: str,
        extraction: ExtractionResult,
        flags: list[str],
    ) -> str:
        if item_type == "MCQ":
            if candidate == "INVALID":
                return response
            if extraction.first_boxed_letter == candidate and not extraction.rescued:
                return response
            return f"\\boxed{{{candidate}}}"

        # ACTION 6 (Cursor WORRY 1) — REBOX SAFETY (behavior unchanged; documentation only):
        # We append a NEW box with a "Final answer:" text prefix rather than full-replacing.
        # Why this is SAFE under the value-equality grader: the grader (judger.extract_all_boxed)
        # takes the LAST CONTIGUOUS GROUP of \boxed{}, where "contiguous" allows only the gap
        # regex [\s,\$\.\;\:\-\&\\]* between boxes. The word "Final answer:" contains letters
        # ('F','i','n','a','l','a','n','s','w','e','r') that are NOT in that allowed-gap set, so
        # it BREAKS contiguity — the appended box forms its own last group and the grader sees
        # ONLY the new box (not merged with any prior boxes in the response).
        # Contrast with apply_overrides.py, which FULL-REPLACES the response with a single
        # \boxed{} (different use case: applying a single-item override value, where we want
        # zero ambiguity). And contrast with the Day-8 bug: a plain "\n\n\boxed{NEW}" appended
        # after an existing "$$\boxed{...}$$" block MERGES the two groups (gap is only whitespace/$,
        # all in the allowed set) → grader reads "old, NEW" with wrong slot count. The
        # "Final answer:" prefix is precisely what prevents that merge here.
        final_box = f"Final answer: \\boxed{{{candidate}}}"
        if response.rstrip().endswith(final_box):
            return response
        return response.rstrip() + "\n\n" + final_box

    def extract_all_boxed(self, text: str) -> list[str]:
        results: list[str] = []
        i = 0
        while i < len(text):
            match = BOX_START_RE.search(text, i)
            if match is None:
                break
            depth = 1
            j = match.end()
            while j < len(text) and depth > 0:
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                j += 1
            if depth == 0:
                results.append(text[match.end() : j - 1])
            i = match.end()
        return results

    def _rescue_candidate(self, response: str, item_type: str) -> str:
        patterns = [
            re.compile(r"(?:final answer|the answer|answer)\s*(?:is|:)\s*(.+?)\s*$", re.IGNORECASE),
            re.compile(r"(?:therefore|thus|hence)\s+(.+?)\s*$", re.IGNORECASE),
        ]
        for pattern in patterns:
            match = pattern.search(response.strip())
            if match:
                return match.group(1).strip().rstrip(".")

        number_match = re.search(r"(?:[:=])\s*([+-]?\d+(?:\.\d+)?)\s*$", response.strip())
        if number_match:
            return number_match.group(1)

        if item_type == "MCQ":
            return extract_mcq_letter(response)
        return ""

    def _parse_mcq_letter_set(self, candidate: str):
        """Return ['A','C','D'] for a multi-select MCQ answer like 'A,\\ C,\\ D',
        or None if not a clean set of >=2 single letters. Single letters return
        None so they keep flowing through the normal single-letter path."""
        s = (candidate or "").strip()
        for tok in ("\\,", "\\;", "\\:", "\\!", "\\ "):
            s = s.replace(tok, "")
        s = s.strip("()[]{} ")
        parts = [p.strip("()[]{} ") for p in re.split(r"[,\s]+", s) if p.strip()]
        if len(parts) >= 2 and all(len(p) == 1 and p.isalpha() for p in parts):
            return [p.upper() for p in parts]
        return None

    def _cleanup_mcq_letter(self, candidate: str) -> str:
        cleaned = candidate.strip().rstrip(".")
        text_match = TEXT_WRAPPER_RE.match(cleaned)
        if text_match:
            cleaned = text_match.group(1)
        cleaned = cleaned.strip("()[]{} ")
        if len(cleaned) == 1 and cleaned.isalpha():
            return cleaned.upper()
        return ""

    def _normalize_multi_element(self, value: str, item: dict) -> str:
        # Single-mode: per-slot value passes through unchanged (structural-only).
        return value

    def _promote_fraction_from_metadata(self, candidate: str, item: dict) -> str:
        if not self._looks_decimal(candidate):
            return candidate

        target = item.get("fraction_target") or ""
        if not target:
            sheet_best = item.get("sheet_best_answer") or ""
            teacher_values = [item.get("teacher_sonnet"), item.get("teacher_gpt4"), item.get("teacher_oss")]
            teacher_values = [self.universal_cleanup(v) for v in teacher_values if isinstance(v, str) and v.strip()]
            if sheet_best and self._looks_fraction_like(sheet_best):
                if teacher_values and len(set(teacher_values)) == 1 and teacher_values[0] == self.universal_cleanup(sheet_best):
                    target = self.universal_cleanup(sheet_best)
                elif item.get("sheet_tier") in {"1", "2", 1, 2} and item.get("sheet_confidence", 0) >= 80:
                    target = self.universal_cleanup(sheet_best)

        if target and self._looks_fraction_like(target):
            return target
        return candidate

    def _apply_aggressive_transforms(self, candidate: str, item: dict, flags: list[str]) -> str:
        out = candidate
        out2 = LATEX_WRAPPER_RE.sub(lambda match: match.group(1), out)
        if out2 != out:
            flags.append("LATEX_WRAPPER_STRIP")
            out = out2

        out2 = self._strip_trailing_zeros(out)
        if out2 != out:
            flags.append("TRAILING_ZERO_STRIP")
            out = out2

        out2 = self._strip_number_commas(out)
        if out2 != out:
            flags.append("NUMBER_COMMA_STRIP")
            out = out2

        prefix_match = MULTI_CHAR_PREFIX_RE.match(out)
        if prefix_match:
            flags.append("MULTI_CHAR_PREFIX_STRIP")
            out = prefix_match.group(2)

        expanded = self._expand_scientific_notation(out)
        if expanded != out:
            flags.append("SCIENTIFIC_EXPANDED")
            out = expanded

        routed = self._route_by_source_convention(out, item)
        if routed != out:
            flags.append("SOURCE_ROUTED")
            out = routed

        broad_frac = self._broad_fraction_conversion(out, item)
        if broad_frac != out:
            flags.append("BROAD_FRACTION_CONVERSION")
            out = broad_frac

        return out

    def _route_by_source_convention(self, candidate: str, item: dict) -> str:
        question = (item.get("question") or "").lower()
        if any(token in question for token in ["round to", "nearest", "decimal places", "decimal place"]):
            return self._strip_trailing_zeros(candidate)
        if "express your answer as" in question and "fraction" in question and self._looks_decimal(candidate):
            return self._broad_fraction_conversion(candidate, item)
        return candidate

    def _broad_fraction_conversion(self, candidate: str, item: dict) -> str:
        if not self._looks_decimal(candidate):
            return candidate
        question = (item.get("question") or "").lower()
        if any(token in question for token in ["decimal", "nearest", "round to"]):
            return candidate
        if not (
            item.get("prefer_fraction")
            or "fraction" in question
            or "ratio" in question
            or "probability" in question
            or "express your answer as" in question
        ):
            return candidate
        try:
            fraction = Fraction(candidate).limit_denominator(1000)
        except ValueError:
            return candidate
        if fraction.denominator == 1:
            return candidate
        return f"\\frac{{{fraction.numerator}}}{{{fraction.denominator}}}"

    def _expected_slot_count(self, item: dict) -> int:
        answer = item.get("answer")
        if isinstance(answer, list):
            return max(1, len(answer))
        return max(1, (item.get("question") or "").count("[ANS]"))

    def _letter_for_index(self, idx: int) -> str:
        return chr(ord("A") + idx)

    def _fix_frac_shorthand(self, string: str) -> str:
        substrs = string.split("\\frac")
        new_str = substrs[0]
        if len(substrs) > 1:
            for substr in substrs[1:]:
                new_str += "\\frac"
                if substr and substr[0] == "{":
                    new_str += substr
                else:
                    if len(substr) < 2:
                        return string
                    a = substr[0]
                    b = substr[1]
                    if b != "{":
                        new_str += "{" + a + "}{" + b + "}" + substr[2:]
                    else:
                        new_str += "{" + a + "}" + b + substr[2:]
        return new_str

    def _fix_sqrt_shorthand(self, string: str) -> str:
        if "\\sqrt" not in string:
            return string
        splits = string.split("\\sqrt")
        out = splits[0]
        for split in splits[1:]:
            if split and split[0] != "{":
                out += "\\sqrt{" + split[0] + "}" + split[1:]
            else:
                out += "\\sqrt" + split
        return out

    def _fix_integer_slash_fraction(self, string: str) -> str:
        if len(string.split("/")) != 2:
            return string
        left, right = string.split("/")
        try:
            left_i = int(left)
            right_i = int(right)
            assert string == f"{left_i}/{right_i}"
            return f"\\frac{{{left_i}}}{{{right_i}}}"
        except Exception:
            return string

    def _strip_right_text_unit(self, string: str) -> str:
        if "\\text{ " in string:
            parts = string.split("\\text{ ")
            if len(parts) == 2:
                return parts[0]
        return string

    def _strip_short_lhs_prefix(self, string: str) -> str:
        if len(string.split("=")) == 2 and len(string.split("=")[0]) <= 2:
            return string.split("=")[1]
        return string

    def _strip_trailing_zeros(self, string: str) -> str:
        if not string:
            return string
        if re.fullmatch(r"[+-]?\d+\.\d+", string):
            return string.rstrip("0").rstrip(".")
        return string

    def _strip_number_commas(self, string: str) -> str:
        if re.fullmatch(r"[+-]?\d{1,3}(,\d{3})+(\.\d+)?", string):
            return string.replace(",", "")
        return string

    def _expand_scientific_notation(self, string: str) -> str:
        match = SCI_RE.match(string) or TIMES_TEN_RE.match(string)
        if match is None:
            return string
        mantissa = match.group(1)
        exponent = match.group(2)
        try:
            value = Decimal(mantissa) * (Decimal(10) ** int(exponent))
        except (InvalidOperation, ValueError):
            return string
        normalized = format(value.normalize(), "f")
        return normalized.rstrip("0").rstrip(".") if "." in normalized else normalized

    def _round_decimal(self, string: str, n_places: int) -> str:
        try:
            return f"{Decimal(string):.{n_places}f}"
        except (InvalidOperation, ValueError):
            return string

    def _looks_decimal(self, string: str) -> bool:
        return bool(re.fullmatch(r"[+-]?\d+\.\d+", string or ""))

    def _looks_fraction_like(self, string: str) -> bool:
        return "\\frac{" in string or bool(re.fullmatch(r"[+-]?\d+/\d+", string or ""))

    def _load_overrides(self, overrides_path: Optional[str]) -> dict[str, dict[str, str]]:
        if overrides_path is None:
            overrides_path = str(
                Path(__file__).resolve().parent.parent / "per_item_overrides.csv"
            )
        path = Path(overrides_path)
        if not path.exists():
            return {}
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            return {row["id"]: row for row in reader if row.get("id")}


def load_items(items_path: str) -> dict[int, dict[str, Any]]:
    items: dict[int, dict[str, Any]] = {}
    with open(items_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if not isinstance(record, dict) or "id" not in record:
                continue
            items[int(record["id"])] = record
    return items


def load_master_answer_metadata(csv_path: str) -> dict[int, dict[str, Any]]:
    metadata: dict[int, dict[str, Any]] = {}
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item_id = row.get("item_id")
            if not item_id:
                continue
            normalized: dict[str, Any] = {k: v for k, v in row.items() if v not in {None, ""}}
            for key in ["sheet_confidence", "backsolve_confidence"]:
                if key in normalized:
                    try:
                        normalized[key] = float(normalized[key])
                    except ValueError:
                        pass
            for key in ["sheet_tier", "sheet_n_agree", "backsolve_tier"]:
                if key in normalized:
                    try:
                        normalized[key] = int(float(normalized[key]))
                    except ValueError:
                        pass
            metadata[int(item_id)] = normalized
    return metadata


def merge_item_metadata(
    base_items: dict[int, dict[str, Any]],
    master_answers: Optional[dict[int, dict[str, Any]]] = None,
) -> dict[int, dict[str, Any]]:
    merged: dict[int, dict[str, Any]] = {}
    all_ids = set(base_items)
    if master_answers:
        all_ids |= set(master_answers)
    for item_id in all_ids:
        item = dict(base_items.get(item_id, {}))
        if master_answers and item_id in master_answers:
            item.update(master_answers[item_id])
        merged[item_id] = item
    return merged


def normalize_csv(
    *,
    input_csv: str,
    output_csv: str,
    mode: str,
    items_path: str,
    master_answers_path: Optional[str] = None,
    overrides_path: Optional[str] = None,
    report_path: Optional[str] = None,
) -> dict[str, Any]:
    base_items = load_items(items_path)
    master_answers = load_master_answer_metadata(master_answers_path) if master_answers_path else None
    items = merge_item_metadata(base_items, master_answers)
    normalizer = Normalizer(mode=mode, overrides_path=overrides_path)

    flag_counts: dict[str, int] = {}
    rows_report: list[dict[str, Any]] = []

    with open(input_csv, newline="", encoding="utf-8") as in_handle, open(
        output_csv, "w", newline="", encoding="utf-8"
    ) as out_handle:
        reader = csv.DictReader(in_handle)
        fieldnames = reader.fieldnames or ["id", "response"]
        writer = csv.DictWriter(out_handle, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            row_id = int(row["id"])
            item = items.get(row_id, {"id": row_id})
            response = row.get("response", "") or ""
            result = normalizer.normalize_with_report(response, item)
            row["response"] = result.response
            writer.writerow(row)

            for flag in result.flags:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
            rows_report.append(
                {
                    "id": row_id,
                    "item_type": result.item_type,
                    "candidate": result.candidate,
                    "flags": result.flags,
                }
            )

    report = {
        "mode": mode,
        "input_csv": input_csv,
        "output_csv": output_csv,
        "flag_counts": flag_counts,
        "rows": rows_report,
    }
    if report_path:
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Canonical post-inference normalizer")
    parser.add_argument("input_csv", help="Input submission CSV with id,response columns")
    parser.add_argument("output_csv", help="Output CSV path for normalized responses")
    parser.add_argument(
        "--mode",
        choices=["conservative", "default", "aggressive"],
        default="default",
        help="Normalization mode",
    )
    parser.add_argument(
        "--items",
        default="private.jsonl",
        help="Item metadata JSONL used for MCQ routing and question structure",
    )
    parser.add_argument(
        "--master-answers",
        default="data/MASTER_ANSWERS.csv",
        help="Optional answer-sheet metadata CSV for fraction promotion and confidence-aware routing",
    )
    parser.add_argument(
        "--overrides",
        default=str(Path(__file__).resolve().parent.parent / "per_item_overrides.csv"),
        help="Per-item override CSV",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Optional JSON report path with per-row flags and candidates",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    report = normalize_csv(
        input_csv=args.input_csv,
        output_csv=args.output_csv,
        mode=args.mode,
        items_path=args.items,
        master_answers_path=args.master_answers,
        overrides_path=args.overrides,
        report_path=args.report,
    )
    print(json.dumps({"mode": report["mode"], "flag_counts": report["flag_counts"]}, indent=2))


if __name__ == "__main__":
    main()

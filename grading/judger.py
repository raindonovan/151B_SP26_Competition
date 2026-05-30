"""Canonical local grading import surface.

Use this module for local judger access from repo code. The root-level
`judger.py` remains as a compatibility entrypoint for older scripts and the
starter notebook.
"""

from __future__ import annotations

from judger import Judger

from grading.hendrycks_is_equiv_reference import is_equiv as kaggle_like_is_equiv

try:
	from math_verify import parse, verify
except Exception:  # pragma: no cover - environment dependent
	parse = None
	verify = None


def math_correct_is_equiv(candidate: str, surrogate: str, item_type: str = "free") -> bool | None:
	candidate = (candidate or "").strip()
	surrogate = (surrogate or "").strip()
	if not candidate or not surrogate:
		return False
	if item_type == "MCQ":
		return candidate.upper() == surrogate.upper()
	if parse is None or verify is None:
		return None
	try:
		candidate_parsed = parse(f"\\boxed{{{candidate}}}")
		surrogate_parsed = parse(f"\\boxed{{{surrogate}}}")
		return bool(verify(surrogate_parsed, candidate_parsed))
	except Exception:
		return None


__all__ = ["Judger", "kaggle_like_is_equiv", "math_correct_is_equiv"]
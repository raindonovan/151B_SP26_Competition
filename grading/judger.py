"""Canonical local grading import surface.

Use this module for local judger access from repo code. The root-level
`judger.py` remains as a compatibility entrypoint for older scripts and the
starter notebook.
"""

from judger import Judger

from grading.hendrycks_is_equiv_reference import is_equiv as kaggle_like_is_equiv

__all__ = ["Judger", "kaggle_like_is_equiv"]
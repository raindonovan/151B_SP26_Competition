"""Canonical grading package exports.

`Grader` (grading.grader) is the canonical value-equality grader — use it.
`kaggle_like_is_equiv` is the DEPRECATED strict Hendrycks mirror (retired grader).
"""

from .grader import Grader
from .judger import Judger, kaggle_like_is_equiv

__all__ = ["Grader", "Judger", "kaggle_like_is_equiv"]
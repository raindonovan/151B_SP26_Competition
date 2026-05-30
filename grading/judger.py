"""DEPRECATED module name — use `grading.grader` (Grader) instead.

Kept for backward compatibility. Note:
- `Judger` here is the value-equality engine (same object as grading.grader.Grader).
- `kaggle_like_is_equiv` is the Hendrycks STRICT string-match mirror, which models
  the RETIRED strict Kaggle grader. Do NOT use it to predict the current
  (value-equality) grader — it is retained only for historical comparison.
"""

from judger import Judger

from grading.hendrycks_is_equiv_reference import is_equiv as kaggle_like_is_equiv

__all__ = ["Judger", "kaggle_like_is_equiv"]
"""Canonical GRADER — our value-equality Kaggle mirror.

Import the grader from here:  `from grading.grader import Grader`

WHAT IT IS
----------
`Grader` is the value-equality engine (numeric equality at ~1e-8 with sympy/LaTeX
parsing). It is our best mirror of the UPDATED Kaggle grader, which switched to
value-based comparison (4.000 == 4, 0.6 == 3/5) around 2026-05-27.
Status: believed-accurate, pending final Kaggle confirmation (see
submission/30_05/SCORES.md, the #1-vs-#2 rejudge comparison).

TRUST NOTE (read this — the historical docs are inverted)
---------------------------------------------------------
Older docs call the sympy "judger" untrustworthy / cite a ~28pp gap. That was the
PRE-update world: the sympy value-equality engine vs a STRICT (Hendrycks string-
match) Kaggle grader. After the judge update that gap is believed closed, so the
value-equality engine (this Grader) is now the one to trust, NOT the strict mirror.

DEPRECATED
----------
`grading.judger.kaggle_like_is_equiv` (Hendrycks strict string-match) mirrors the
RETIRED strict grader. Do NOT use it to predict the current grader. It is kept only
for historical comparison.

(The value-equality engine physically lives in root `judger.py` for now because it
has a root-level `from utils import *` dependency; relocating it is a post-deadline
cleanup. Always import via this module, not by file path.)
"""

from grading.judger import Judger as Grader  # value-equality engine

Judger = Grader  # backward-compat alias for older callers

__all__ = ["Grader", "Judger"]

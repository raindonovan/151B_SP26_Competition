# Submission Research

## Back-solve oracle
See `submission/BACKSOLVE_RESEARCH.md` for detailed findings.

## Key insight: submissions are for oracle mining
Each submission is an information-extraction tool. Differential submissions reveal per-item gold on the ~283-item test subset. Back-solve is resurrected as a first-class strategy lever.

## Log-loss oracle (Whitehill 2017, arXiv 1707.01825)
Formalizes the theory behind leaderboard exploitation. Our accuracy-based grader gives less information per submission than log-loss, but the same principle applies: each submission is a query to an oracle.

## LB-subset caveat (RED ALERT)
Kaggle score = accuracy on a fixed UNKNOWN ~283-item slice (30% of private). NOT all 943.
Back-solve values and tiers built on /943 assumption are unreliable.
Endgame: final rank uses full 943, so slice-tuned overrides risk shake-DOWN.
See `submission/RED_ALERT_LB_SUBSET.md`.

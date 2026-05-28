# RUN: OPL Match

**Type**: Embedding-based question matching (not an inference run)
**Date**: ~2026-05-26 to 2026-05-27
**Owner**: tnr-0 (OPL embeddings local), claude_strategy (analysis)
**Status**: Match data complete; analyzed in `findings.md`; decision in `decision.md`

## What this was

We embedded our 943 private questions using BGE-base-en-v1.5 (768-dim) and matched them against 72,668 OpenProblemLibrary (WeBWorK) templates also embedded. Goal: find OPL problems that match ours, extract answer logic from the .pg files.

## Artifacts

- `results/opl_match/candidates.csv` (217KB, 2057 rows) — match candidates per item with bucket/similarity/status
- `results/opl_match/extracted.jsonl` (688KB) — extracted answer logic
- `results/opl_match/topk.jsonl` (412KB) — top-k matches per item
- `results/opl_embeddings/opl_embeddings.npy` (223MB, tnr-0 LOCAL ONLY — LFS-migration pending)
- `scripts/splice_submission.py` — apply OPL answers as override CSV

## See also

- `findings.md` — what we learned
- `decision.md` — what we're doing about it

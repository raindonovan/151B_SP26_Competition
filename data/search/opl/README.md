# RUN: OPL Match

> ⚰️ **STATUS (Day 7, 2026-05-29): DEAD CHANNEL.** OPL bulk-override is empirically disconfirmed. The OK-bucket is mostly false-positive text matches against unrelated problems. See `findings.md` Day-7 headline and `decision.md` for the verdict. Infrastructure kept for spot-query reference; no further work planned.

**Type**: Embedding-based question matching (not an inference run)
**Date**: ~2026-05-26 to 2026-05-27 (matching); 2026-05-29 (join + disconfirmation)
**Owner**: tnr-0 (OPL embeddings local), claude_strategy (analysis, then bust verdict)
**Status**: DEAD — analyzed in `findings.md`, killed in `decision.md`

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

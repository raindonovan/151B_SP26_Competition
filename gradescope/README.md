# gradescope/ — Gradescope & Course Deliverables

Final code submission due: 2026-05-31 (Sunday)

## Requirements
- Single `run_inference()` entry point: model load → inference → post-processing → final CSV
- Fine-tuned models on HF Hub
- Public GitHub repo + README (GPU type, inference time, weight setup)
- All group members on Gradescope
- Verification: top-10 = full private re-run; rest = 200 random questions; >30pp gap flagged

## Files
- `milestone_report.pdf` — milestone report (submitted)
- `milestone_report.tex` — source for milestone report

## Role & Relevance

**Role**: Course deliverables — milestone reports, final code submission, Gradescope uploads.
**Relevance**: The code submission (due 2026-05-31) requires a single run_inference() entry point, fine-tuned models on HF Hub, and a public README. This is a hard deadline independent of Kaggle.
**Techniques**: N/A — this is packaging, not research.
**Inputs**: Final pipeline code, trained adapters, inference configs.
**Outputs**: Gradescope submission, HF Hub model upload, public repo README.

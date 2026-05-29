# inference/SCRATCH.md — Unsorted findings, ideas, observations

Drop anything here. Rain will sort it later.

---

- Qwen3-4B official recommended sampling: temperature=0.6, top_p=0.95, top_k=20, min_p=0, presence_penalty (not repetition_penalty). Greedy contraindicated for thinking mode.
- NoThinking = prefill only. enable_thinking=False is a no-op on this model.
- Repetition collapse at greedy traced to decoding config, not weight-space collapse. repetition_penalty=1.1 partially recovers.
- Sun et al. showed +7.3pp from multi-temperature voting on Qwen3-4B size class. Never tried.
- WiSE-FT for LoRA = scale lora_alpha by delta (delta=0.5 prior). No retraining needed. Could recover v5 adapter.
- SFT v5 regression was ~7 semantic items, not format. 87% T1-easy in training set is structural issue.

---

## Two-bucket framework for tier-1 items (2026-05-28) — sets up tomorrow's run scan

CONFIRMED (see postprocessing/FINDINGS.md F7): tier-1 items (Wolfram HIGH ∧ web-search GOLD ∧ 3/3 teachers) ARE getting graded wrong on FORMAT. The fraction fix proved it (+2 slice items from pure decimal→fraction flip).

TOMORROW'S INFERENCE-RUN SCAN: for every tier-1 item, classify into:
- **Bucket A**: some inference run (SC8/SC16/NoThinking/etc.) produced the correct MATH → find it, format-fix, submit. NO adapter needed.
- **Bucket B**: NO run ever produced the correct math → adapter candidate.

Then the format layer applies to BOTH buckets: even bucket-A items can be graded wrong if emitted in wrong format.

Operational tier-1 filter: wolfram_confidence=HIGH AND search_status=GOLD AND all 3 teachers agree. Cross-reference each tier-1 item's gold answer against the voted answer in EVERY run's samples.jsonl. Need format-aware comparison (Hendrycks normalization), not raw string match.

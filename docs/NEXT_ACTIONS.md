# NEXT ACTIONS

**Last updated**: 2026-05-27 ~17:30 PT (Day 3, mid-session)
**Update**: Edit in-place via GitHub API (PAT in Drive SECRETS doc)

## Right now (waiting)

1. **Tnr-0 no-box rescue**: 13/18 done, ~40 min ETA. Let run. Report expected ~18:30 PT.
2. **Tnr-1 snapshot**: In progress. Rain executes snapshot+delete on Thunder UI row 1 (UUID q6b81cqp) when complete.
3. **TritonAI endpoint test**: Rain running from PowerShell. Results pending.
4. **Dominic reply**: Await TritonAI results, then Rain picks variant (1=polite close-out / 2=lead with access question).

## When rescue completes (~18:30 PT)

5. **OPL v1 spec**: claude_strategy delivers Block 2 prompt to tnr-0. Matcher + extractor + audit triage. ~30-60 min, mostly CPU.
6. **Wolfram Drive cleanup**: move 3 duplicate 08a files + 1 old 0181 followup to delete_ignore folder (id `168kP6ivwSsUgwvwX81LvoxwlqJ6MK55A`).
7. **MASTER_SHEET 0181 update**: update verdict from inconclusive → override=A in Drive MASTER_SHEET.

## Day 3 evening / morning stock-take

8. **Update unified_answer_sheet.csv**: incorporate Wolfram B8 overrides (23 items) + web search GOLDs (5 items). Run `scripts/build_answer_sheet_v4.py` on tnr-0 or vscode. Push via PAT.
9. **Build Track B submission CSV**: apply Wolfram overrides + web search GOLDs to slot1_wolfram_full_overrides base. Submit as Day 4 Slot 2.
10. **Review no-box rescue candidates.csv**: which items have strong vote (≥3/4)? Those are splice candidates for Track A/B.
11. **OPL v1 audit**: HIGH-bucket FALSE-agreement count → determines if OPL is a real lever worth v2 investment.

## Day 4

12. **Day 4 Slot 1 (Track A)**: best clean-inference submission. Base: NoThinking SC=8 + tuple-voting reformat + no-box rescue spliced. Target: 0.66-0.68.
13. **Day 4 Slot 2 (Track B)**: Wolfram + web search overrides applied to Track A base. Target: 0.67-0.69.
14. **Tuple-voting on NoThinking samples**: desk task, no GPU. Refine multi-answer shape fix using sample-bearing JSONL.
15. **Truncation rescue triage**: aggregate run10 + NoThinking truncated items. Build 30-50 item target list for high-budget re-run.

## Day 4-5

16. **OPL v2 (conditional)**: formula eval + parameter substitution. Only if v1 HIGH-bucket FALSE-agreement count ≥ 30.
17. **SFT v7 (conditional)**: train on Qwen-wrong items (SC ≠ sheet), verified labels, epochs 3-5 + weight decay, multi-teacher. Only if Day 4 Track A < 0.67.
18. **LFS migration for tnr-0**: move `results/opl_embeddings/opl_embeddings.npy` to Git LFS before tnr-0 deletion. MUST happen before billing pause.
19. **GRPO (conditional)**: Day 5-6 only if conservative inference sum < 0.70.

## Day 7 (deadline ~2026-06-02)

20. **Final 2 picks**: Pick A (Track A best) + Pick B (Track B best with all overrides).
21. **run_inference()**: single entry-point function for Gradescope. Model load → inference on private 943 → ALL post-processing → final CSV. Hyperparams final. Fine-tuned model on HF Hub.
22. **Gradescope**: public repo + README (GPU type, inference time, weight setup, run call). Add all group members.

## Open decisions

- [ ] [RAIN] SC=20 hybrid + DeepSeek-R1 5th teacher green-light
- [ ] [RAIN] Wolfram Drive cleanup authorization (3 dupes + 1 old followup)
- [ ] [RAIN] MASTER_SHEET 0181 update (inconclusive → override=A)
- [ ] [TECH] LFS migration for OPL embeddings (before tnr-0 deletion)
- [ ] [STRATEGIC] Ask Dominic: grader normalization logic, OPL source %, external tools in run_inference()

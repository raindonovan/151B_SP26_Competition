# AUDIT DISCIPLINE — LOCKED RULES

**Status**: LOCKED 2026-05-31 (Day 9) after shallow first-pass adapter audit incident
**Authority**: Rain
**Scope**: All audits, all agents (claude_strategy, claude_vscode, Cursor, Thunder agents, ChatGPT cross-checks)
**Trigger for this lock**: claude_strategy's Phase A adapter repo read was shallow — skipped log files, conflated v1 (merged) with v3-v5 (adapter), missed dual-path infrastructure, didn't read result jsonls. Rain explicitly pushed back twice. This document codifies the standard so it doesn't repeat.

---

## The 10 locked rules

### Pre-existing (5/13 baseline)

1. **Grep call sites before production claim** — never claim a function is used unless you've grep'd it across the repo
2. **Check existing implementations** — before writing new code, search for what already exists
3. **Validate against ground truth, not self-equality** — never test "output matches output"
4. **Per-branch test matrix** — every code path tested
5. **Calibrate verdict to evidence** — verdict strength must match what evidence supports

### NEW (5/31 v2 lock — Rain's audit discipline directive)

6. **NO GLOSSING OVER FILES** — every relevant file is read FULLY. Includes:
   - .log files (training logs, smoke logs, inference logs) — even if 300KB+
   - Training scripts (every line of hyperparams, not just grep for keys)
   - Result jsonls (inspect actual outputs, not just file existence)
   - Adapter configs (every field, not just headline values)
   - Markdown docs (every section, not just headers)

7. **NO SKIPPING READS** because content "looks already known" or is long. The reason we skip is the reason we miss things. If a file is in scope, it gets read fully.

8. **NOTES OF ALL ANALYSIS captured in repo AS I GO** — not "after the audit." For smooth handover across sessions/agents:
   - Findings → write to ADAPTER_NOTES.md / strategy/*.md / per-folder FINDINGS.md immediately as discovered
   - Don't accumulate state in chat — chat is ephemeral, repo is durable
   - Every file read produces at least one note (even if "nothing new here")
   - Disagreements/corrections logged explicitly so future sessions don't re-make the same mistake

9. **CURSOR / ChatGPT SAME STANDARD** — when delegating audits to external LLMs:
   - The audit prompt must demand the same depth (see Phase A v2 enhanced Cursor prompt for the template)
   - If their audit is shallow / glosses files / misses scope → FLAG IMMEDIATELY in chat, do not proceed to synthesis
   - Require redo with explicit scope expansion
   - Never let a shallow external audit be the foundation for a downstream decision

10. **DEEP AUDITS NO LIGHT AUDITS** unless trivially so. Trivially so = "is this string equal to that string" type checks. Anything involving strategy / training data / inference / picks / overrides → deep audit, no exceptions.

### Workflow

- **High-stakes decisions** (submission strategy, normalizer, adapter targets, training composition, picks): my audit → ChatGPT cross-check → synthesize. Three independent passes minimum.
- **claude_vscode same standard** as claude_strategy
- **Tnr-0 / tnr-1 same standard** when doing audit work (not just execution)

### What "shallow" looks like (concrete failure modes from the 5/31 incident)

- ✗ Listing files via `find` / `ls`, claiming "scope mapped" without opening them
- ✗ Reading head/tail of files only (`head -100`, `tail -50`) when full file is short enough
- ✗ Treating training scripts as black boxes — extracting hyperparam names without reading what they do
- ✗ Conflating distinct entities (v1 vs v3 vs v4 vs v5; merged vs adapter; single-path vs dual-path)
- ✗ Citing memory snippets instead of opening the underlying file
- ✗ Skipping .log files because they're long
- ✗ Skipping result jsonls because "we already know what they contain"
- ✗ Generating high-level conceptual notes without grounding them in file evidence

### What "deep" looks like (the bar)

- ✓ Every file in scope opened and read fully (or large files paginated through completely)
- ✓ Training scripts: read every line; understand what each does
- ✓ Logs: read training trajectories, smoke outputs, error messages
- ✓ Result jsonls: inspect actual sample outputs, count items, check SC consistency, etc.
- ✓ Distinct entities kept distinct (v1 vs v5, merged vs adapter, etc.)
- ✓ Notes captured in repo with file paths + line references
- ✓ Disagreements with prior framings called out explicitly

### Enforcement

- Rain has authority to flag any audit as shallow and require redo
- Other agents (claude_vscode, Cursor, etc.) have authority to flag claude_strategy's audits as shallow
- claude_strategy has authority to flag Cursor/ChatGPT audits as shallow and require redo
- A shallow audit blocks downstream work until redone

---

## Why this matters

The 5/31 shallow first pass on adapter repo missed:
- v1 vs v3-v5 paradigm split (external-distill+merged vs transductive+adapter)
- Dual-path infrastructure already exists in `run_hybrid_inference.py`
- v4 was -4.9pp regression (not break-even as claimed from memory)
- memo_test_v5 was multi-sample at inference conditions (not the trivial test I framed)
- Training set composition was the real lever (not validation methodology)

Each of these required Rain to push back twice. In a 17-hour-to-deadline situation, that's expensive context burn. The discipline cost of "read everything fully the first time" is far smaller than the discipline cost of "audit / discover gap / redo / discover next gap / redo" cycles.

Going forward: read everything fully the first time. Cheaper than corrections.

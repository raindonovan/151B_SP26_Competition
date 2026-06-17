# ADR-0002 — Naming and ID standard

> Animating idea: every durable thing carries exactly one kind of ID, drawn from a
> standard primitive — so a reader never has to decode a bespoke code.

Date: 2026-06-17 | Status: Accepted | Author: claude_strategy_25 (with Rain)
Note: first record under the new name "ADR" (was "AgDR"); also sets the template the later records follow.

## Context
The rig accumulated ~7 overlapping, ad-hoc ID schemes that leaked into durable docs —
refinement-round labels (R3/R4/R5), decision letters (D-a/b/c), defense layers (L1–L4),
todo tiers (T1.1…), punch-list numbers, corrections numbers, and AgDR numbers. They were
unparseable to Rain (the primary reader) and collided with each other. The fix: stop
inventing per-session schemes; standardize on the primitives the industry already uses.
(Online research round, 2026-06-17 — see Evidence.)

## Decision
Three buckets, and nothing else carries a standing code:
1. Decisions → ADRs. One decision per file in `decisions/`, named `NNNN-short-title.md`
   (lowercase, dashes). A status line per record. An index at the top of the folder.
   Records are superseded, never deleted or renumbered. ("AgDR" → the universal "ADR".)
2. Tasks → GitHub Issues. Tracker-numbered (`#N`), with a small label set and a board.
   No markdown to-do list as the source of truth.
3. Corrections → a lessons ledger filed by failure mode. Each entry under a failure-mode
   heading, WRONG → RIGHT → LESSON. The failure mode is the key; the number is a back-reference.

Numbering: ADR IDs are sequential and immutable — assigned at creation, never renumbered
(links from commits/Issues depend on a stable ID). Importance and priority live in the
Issues backlog (`prio:now/next/later`) and the ADR index — never in the number. Numbers are
not reserved ahead of writing; the earlier reservation of `0002` for the hub (noted in
ADR-0001) is void — the hub takes the next free number when written. (This record takes `0002`.)

Shorthand: no bespoke standing codes. Any unavoidable shorthand is spelled out in brackets
on first use in a doc — e.g. "the boot-recovery layers [defense layers 1–4 in ADR-0001]".

Record template (set here): spirit line → `# ADR-NNNN — Title` → Date / Status / Author →
Context → Decision → Consequences → Evidence (links to shared research/decisions, not embedded).
Lean; one decision per record; don't over-produce records.

## Consequences
- `0001` is grandfathered as ADR-0001 (its "AgDR" header aligned in a later pass; ID unchanged).
- The old labels (R#/D-x/L#/T#/punch#) retire from durable docs; their content migrates
  into ADRs, Issues, or rules.
- Stable IDs make records linkable from commits and Issues.
- Where the decision log lives (rig-wide central vs repo-local), role-scoped access, and
  index ownership are recorded separately — see PLAN.md and the forthcoming hub record.

## Evidence
- Online research round, 2026-06-17: ADR conventions (sequential-immutable IDs, one decision
  per file, an index, supersede-not-delete, don't over-document); AGENTS.md as the cross-tool
  standard; ADR central-vs-local scope patterns. (To the research index when built — Phase 4/5.)
- PLAN.md; scratch/A1-dogfood-audit.md (the directive that prompted this).

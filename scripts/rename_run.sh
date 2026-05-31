#!/usr/bin/env bash
# rename_run.sh — cross-ref sweep tool for the 30-run inference catalog loop.
#
# Usage:  ./scripts/rename_run.sh <old_name> <new_run_ref>
#   $1 = old run name as it appears in prose (e.g. "run03_tok8192_20")
#   $2 = new reference string to replace it with (e.g. a slug
#        "R00_eval_v1_single_f20_t8k" or a path
#        "inference/base_model/R00_eval_v1_single_f20_t8k") — sed-replaces
#        the literal $1 with the literal $2 across the canonical cross-ref docs.
#
# Sweeps ONLY the canonical cross-ref doc list from inference/runs/CATALOG.md
# ("Cross-reference list"). Per doc: count matches, sed -i if >0, report.
# Prints a per-doc change count and a grand total.
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: $0 <old_name> <new_run_ref>" >&2
  exit 2
fi
OLD="$1"
NEW="$2"

# Canonical 27-doc cross-ref list (from inference/runs/CATALOG.md).
DOCS=(
  README.md
  agents/CLAUDE_STRATEGY.md
  agents/CLAUDE_VSCODE.md
  data/ANSWER_SHEET_SCHEMA.md
  data/FINDINGS.md
  data/candidates_nothinking_breakdown.md
  data/candidates_pertier_breakdown.md
  data/candidates_sc16_hardest30_breakdown.md
  data/search/README.md
  infrastructure/pre_flight/audit_report.md
  infrastructure/pre_flight/production_commands.md
  postprocessing/results/slot1_minimal_report.md
  postprocessing/results/slotA_report.md
  strategy/FINDINGS.md
  strategy/HOW_WE_KNOW_CORRECTNESS.md
  strategy/INFERENCE_TECHNIQUES.md
  strategy/LEVERS.md
  strategy/RESEARCH.md
  strategy/SESSION_HANDOFF.md
  strategy/TEST_PIPELINE.md
  strategy/TIME_MACHINE_BACKLOG.md
  strategy/TODO.md
  submission/AMBER_ALERT.md
  submission/RED_ALERT_LB_SUBSET.md
  submission/REGISTRY.md
)

echo "rename_run: '$OLD' -> '$NEW'"
total=0
for doc in "${DOCS[@]}"; do
  if [ ! -f "$doc" ]; then
    echo "  SKIP (missing): $doc"
    continue
  fi
  # count literal matches (grep -F, fixed string; -o for per-occurrence count)
  n=$(grep -Fo "$OLD" "$doc" | wc -l | tr -d ' ')
  if [ "$n" -gt 0 ]; then
    # use | as sed delimiter so paths in $NEW don't clash with /
    sed -i "s|$OLD|$NEW|g" "$doc"
    echo "  $doc: $n replaced"
    total=$((total + n))
  fi
done
echo "rename_run: total replacements = $total"

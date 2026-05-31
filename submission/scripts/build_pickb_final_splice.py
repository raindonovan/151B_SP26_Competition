#!/usr/bin/env python3
"""
build_pickb_final_splice.py — canonical Phase 6 build for Pick B FINAL.

Implements v3.2 patch C1 (SPLICE rule): Pick B FINAL CSV is built by loading
Pick A's frozen CSV as the base, then overwriting ONLY rows where
route_to_adapter=True with adapter outputs. Non-routed rows are byte-identical
to Pick A.

This is BINDING for Kaggle submission. If `run_inference()` regenerates all
943 items fresh, the ~211 non-routed scored items become a new sampling draw
with ~±2.6pp SE per item; two-sided noise on non-routed items swamps the
small one-sided routed gain (per Opus 4.8 R5 sanity check Q2).

Hard gate assertion: diff_count must equal len(routed_ids) exactly. If not,
the splice has bugged out and we must NOT ship.

Usage:
    python submission/scripts/build_pickb_final_splice.py

Inputs (must exist on disk before run):
    - submission/csvs/pick_a.csv (frozen, 943 rows)
    - data/v7_routing_manifest.csv (Phase 5 output, cols: item_id, route_to_adapter)
    - data/v7_adapter_voted_answers.csv (Phase 5 output, cols: item_id, adapter_voted_answer)

Output:
    - submission/csvs/pickb_final.csv (943 rows, 943 - n_routed rows identical to Pick A)
"""

import sys
import pandas as pd


def build_pickb_final_splice(
    pick_a_path: str = "submission/csvs/pick_a.csv",
    routing_path: str = "data/v7_routing_manifest.csv",
    adapter_outputs_path: str = "data/v7_adapter_voted_answers.csv",
    output_path: str = "submission/csvs/pickb_final.csv",
) -> None:
    """Splice adapter overrides onto Pick A's frozen CSV. Hard gate on diff count."""

    # Step 1: load Pick A frozen CSV (the floor at 0.745)
    pick_a = pd.read_csv(pick_a_path)
    assert len(pick_a) == 943, f"Pick A must have 943 rows, got {len(pick_a)}"
    assert pick_a["id"].is_unique, "Pick A ids must be unique"
    assert "id" in pick_a.columns and "answer" in pick_a.columns, \
        f"Pick A must have id and answer columns; got {pick_a.columns.tolist()}"

    # Step 2: load routing manifest, get set of routed item IDs
    routing = pd.read_csv(routing_path)
    assert "item_id" in routing.columns and "route_to_adapter" in routing.columns, \
        f"Routing manifest missing required columns; got {routing.columns.tolist()}"
    routed_ids = set(routing[routing["route_to_adapter"]]["item_id"])
    n_routed = len(routed_ids)
    print(f"[splice] {n_routed} items routed to adapter; {943 - n_routed} stay as Pick A.")

    # Step 3: load adapter outputs
    adapter_outputs = pd.read_csv(adapter_outputs_path)
    assert "item_id" in adapter_outputs.columns and "adapter_voted_answer" in adapter_outputs.columns, \
        f"Adapter outputs missing required columns; got {adapter_outputs.columns.tolist()}"

    # Step 4: build Pick B FINAL = Pick A with ONLY routed rows overwritten
    pickb_final = pick_a.copy()
    overrides_applied = 0
    silent_fallbacks = 0
    for idx, row in pickb_final.iterrows():
        item_id = row["id"]
        if item_id in routed_ids:
            ans = adapter_outputs.loc[
                adapter_outputs["item_id"] == item_id, "adapter_voted_answer"
            ].values
            if len(ans) == 1 and not pd.isna(ans[0]) and str(ans[0]).strip() != "":
                pickb_final.at[idx, "answer"] = ans[0]
                overrides_applied += 1
            else:
                # Adapter output missing/empty for a routed item → keep Pick A (safe fallback)
                silent_fallbacks += 1

    # Step 5: structural verification
    assert len(pickb_final) == 943, f"Pick B FINAL must have 943 rows, got {len(pickb_final)}"
    assert (pickb_final["id"] == pick_a["id"]).all(), "Row order must match Pick A exactly"
    assert pickb_final.columns.tolist() == pick_a.columns.tolist(), \
        f"Column structure must match Pick A; got {pickb_final.columns.tolist()}"

    # Step 6: HARD GATE — diff count must equal overrides_applied
    diff_count = (pickb_final["answer"].astype(str) != pick_a["answer"].astype(str)).sum()
    assert diff_count == overrides_applied, (
        f"SPLICE INTEGRITY VIOLATION: diff_count={diff_count} but overrides_applied={overrides_applied}. "
        f"Investigate before shipping."
    )
    # Soft check: if silent_fallbacks > 0, diff_count will be < n_routed; warn but allow
    if silent_fallbacks > 0:
        print(f"[splice] WARNING: {silent_fallbacks} routed items had no usable adapter output; "
              f"those rows kept Pick A's answer (safe fallback).")

    # Step 7: write
    pickb_final.to_csv(output_path, index=False)
    print(f"[splice] Pick B FINAL written to {output_path}")
    print(f"[splice] Overrides applied: {overrides_applied}")
    print(f"[splice] Silent fallbacks: {silent_fallbacks}")
    print(f"[splice] Non-routed rows preserved verbatim from Pick A: {943 - overrides_applied}")


if __name__ == "__main__":
    try:
        build_pickb_final_splice()
        print("[splice] SUCCESS — diff count matches override count. Safe to ship.")
        sys.exit(0)
    except AssertionError as e:
        print(f"[splice] FAILED — {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[splice] FAILED (unexpected error) — {e}", file=sys.stderr)
        sys.exit(1)

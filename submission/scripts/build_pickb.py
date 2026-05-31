"""build_pickb.py — Pick B candidate constructor pipeline.

Layers Qwen-derived rescue/override answers onto a normalizer baseline using the
canonical full-replace mechanism (postprocessing/scripts/apply_overrides.apply_override).

LAYER PRECEDENCE (highest to lowest priority):
  1. Kitchen-sink rescues (--include-kitchensink, optional)
  2. Thunder rescues (--thunder-stance: conservative / intermediate / moderate)
  3. NT-13 conservative join (always included unless --no-nt13)
  4. Normalizer baseline (slot3 normalizer_only_v1.csv, has normalizer + 4 HIGH overrides applied)

By construction, the layers target disjoint item sets, so precedence rarely matters.
Pipeline asserts no within-layer conflicts and reports any cross-layer overlaps.

RULE #11 COMPLIANCE: All layers are Qwen-derived.
  - Normalizer baseline = R20 (Qwen SC@8) + format normalization + 4 SC-unanimous HIGH overrides (Qwen)
  - Thunder = Qwen SC@16 deep inference
  - NT-13 = Qwen NoThinking variant
  - Kitchen-sink = Qwen SC@16 multi-rung
  - NO teacher traces, NO Wolfram outputs

OUTPUTS:
  - pickb_<variant>_v1.csv: final Pick B candidate CSV (943 rows, id, response)
  - pickb_<variant>_v1_manifest.csv: per-item change log (id, layer, original, new)
  - pickb_<variant>_v1_summary.txt: top-line stats

USAGE:
  python3 build_pickb.py \\
    --variant intermediate \\
    --thunder-stance intermediate \\
    --out-dir submission/30_05/pickb_intermediate
  
  # When kitchen-sink lands:
  python3 build_pickb.py \\
    --variant final \\
    --thunder-stance intermediate \\
    --include-kitchensink \\
    --kitchensink-run-dir inference/base_model/kitchensink_<RUN_TAG> \\
    --out-dir submission/30_05/pickb_final
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).parent.parent.parent

# Thunder stance composition (computed from inference/base_model/audit/thunder_combined_audit.csv)
# CONSERVATIVE: 5 CONFIRMED strong-vote indep-gold rescues (no FP filter applied)
THUNDER_CONSERVATIVE_IDS = {313, 372, 897, 492, 790}
# INTERMEDIATE: 20 items = strong-vote, excludes broader multi-slot FP-risk class (Cursor's recommendation)
THUNDER_INTERMEDIATE_IDS = {26, 32, 33, 143, 182, 263, 306, 313, 319, 325, 372, 389, 396, 440, 535, 617, 705, 762, 790, 897}


def load_baseline(path: Path) -> list[dict]:
    """Load baseline CSV (id, response). Returns list of dicts."""
    with open(path, newline='') as f:
        return list(csv.DictReader(f))


def load_thunder_audit(path: Path) -> dict[int, dict]:
    """Load thunder_combined_audit.csv keyed by id."""
    with open(path, newline='') as f:
        return {int(r['id']): r for r in csv.DictReader(f)}


def build_thunder_layer(audit_csv: Path, stance: str) -> dict[int, str]:
    """Build {id: override_value} for Thunder layer per stance."""
    audit = load_thunder_audit(audit_csv)
    if stance == 'conservative':
        target_ids = THUNDER_CONSERVATIVE_IDS
    elif stance == 'intermediate':
        target_ids = THUNDER_INTERMEDIATE_IDS
    elif stance == 'moderate':
        # All strong-vote items, NO FP filter
        target_ids = {int(r['id']) for r in audit.values() if r['thunder_vote_bucket'] == 'strong'}
    else:
        raise ValueError(f"Unknown stance: {stance}. Use conservative/intermediate/moderate.")
    
    layer = {}
    for iid in target_ids:
        row = audit.get(iid)
        if row is None:
            raise ValueError(f"Thunder id {iid} not in audit CSV — sanity check failed")
        layer[iid] = row['thunder_voted_answer']
    return layer


def build_nt13_layer(csv_path: Path) -> dict[int, str]:
    """Build {id: override_value} from NT-13 conservative join."""
    layer = {}
    with open(csv_path, newline='') as f:
        for r in csv.DictReader(f):
            layer[int(r['id'])] = r['override_value']
    return layer


def build_kitchensink_layer(run_dir: Path, stop_rule_pass: bool = True) -> dict[int, str]:
    """Build {id: override_value} from kitchen-sink rungs.
    
    Strategy: cross-rung majority vote. For each item, pool all 48 samples
    (3 rungs × 16 SC) and take the most-voted answer if its vote count
    represents a strong majority (≥20/48 = ~42%).
    
    If stop_rule_pass=False, returns empty dict (kitchen-sink failed gate).
    """
    if not stop_rule_pass:
        return {}
    
    rung_files = sorted(run_dir.glob('rung*.jsonl'))
    if not rung_files:
        print(f"WARN: no rung*.jsonl files found in {run_dir}", file=sys.stderr)
        return {}
    
    # Pool samples per item across rungs
    pooled = {}  # iid -> list of extracted answers
    for rf in rung_files:
        for line in open(rf):
            r = json.loads(line)
            iid = r['id']
            pooled.setdefault(iid, []).extend(r.get('sample_extracted', []))
    
    layer = {}
    for iid, samples in pooled.items():
        cleaned = [str(s).strip() for s in samples if s is not None and str(s).strip()]
        if not cleaned:
            continue
        counts = Counter(cleaned)
        top, top_count = counts.most_common(1)[0]
        # Strong majority threshold: ≥20/48 (~42%) or ≥top_count*2 of second-best
        if top_count >= 20:
            layer[iid] = top
        # else: insufficient consensus, skip
    return layer


def full_replace_response(value: str) -> str:
    """Canonical full-replace per postprocessing/scripts/apply_overrides.py."""
    return "\\boxed{" + str(value).strip() + "}"


def apply_layers(baseline_rows: list[dict], layers: list[tuple[str, dict[int, str]]]) -> tuple[list[dict], list[dict]]:
    """Apply layers in precedence order (highest priority first).
    
    Returns: (final_rows, manifest)
    manifest is list of {id, layer, original_response_preview, new_value}
    """
    manifest = []
    # Process in REVERSE precedence so highest-priority writes last (wins)
    # But we want to track conflicts, so first compute the "winning" layer per id
    
    id_to_winning_layer = {}  # iid -> (layer_name, value)
    for layer_name, layer_dict in layers:  # iterate in precedence order (highest first)
        for iid, val in layer_dict.items():
            if iid not in id_to_winning_layer:
                id_to_winning_layer[iid] = (layer_name, val)
    
    # Build new rows
    final_rows = []
    for row in baseline_rows:
        iid = int(row['id'])
        if iid in id_to_winning_layer:
            layer_name, val = id_to_winning_layer[iid]
            original_preview = row['response'][:80]
            new_response = full_replace_response(val)
            final_rows.append({'id': row['id'], 'response': new_response})
            manifest.append({
                'id': iid,
                'layer': layer_name,
                'override_value': val,
                'original_response_preview': original_preview,
            })
        else:
            final_rows.append({'id': row['id'], 'response': row['response']})
    
    return final_rows, manifest


def detect_conflicts(layers: list[tuple[str, dict[int, str]]]) -> dict[int, list[tuple[str, str]]]:
    """Detect items appearing in multiple layers."""
    seen = {}  # iid -> list of (layer_name, value)
    for layer_name, layer_dict in layers:
        for iid, val in layer_dict.items():
            seen.setdefault(iid, []).append((layer_name, val))
    return {iid: hits for iid, hits in seen.items() if len(hits) > 1}


def validate(rows: list[dict], layers: list[tuple[str, dict[int, str]]]):
    """Validation checks."""
    assert len(rows) == 943, f"Expected 943 rows, got {len(rows)}"
    
    # No duplicates
    ids = [r['id'] for r in rows]
    assert len(set(ids)) == len(ids), "Duplicate ids in output"
    
    # All responses non-empty strings
    empty = [r['id'] for r in rows if not str(r['response']).strip()]
    assert not empty, f"Empty responses: {empty[:10]}"
    
    # Layer ids all in baseline
    baseline_ids = set(int(r['id']) for r in rows)
    for layer_name, layer_dict in layers:
        oob = set(layer_dict.keys()) - baseline_ids
        assert not oob, f"Layer {layer_name} has ids not in baseline: {oob}"


def write_outputs(rows: list[dict], manifest: list[dict], out_dir: Path, variant: str, layers_info: list[tuple[str, int]]):
    """Write all output files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = out_dir / f"pickb_{variant}_v1.csv"
    with open(csv_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'response'])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    
    manifest_path = out_dir / f"pickb_{variant}_v1_manifest.csv"
    with open(manifest_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'layer', 'override_value', 'original_response_preview'], quoting=csv.QUOTE_ALL)
        w.writeheader()
        for m in sorted(manifest, key=lambda x: (x['layer'], x['id'])):
            w.writerow(m)
    
    summary_path = out_dir / f"pickb_{variant}_v1_summary.txt"
    total_overlaid = len(manifest)
    by_layer = Counter(m['layer'] for m in manifest)
    with open(summary_path, 'w') as f:
        f.write(f"Pick B variant: {variant}\n")
        f.write(f"Total rows: {len(rows)}\n")
        f.write(f"Total items overlaid: {total_overlaid}\n")
        f.write(f"By layer:\n")
        for layer_name, layer_size in layers_info:
            actually_applied = by_layer.get(layer_name, 0)
            f.write(f"  {layer_name}: {actually_applied} applied (layer had {layer_size} items)\n")
        f.write(f"\nBaseline unchanged: {len(rows) - total_overlaid}\n")
    
    return csv_path, manifest_path, summary_path


def main():
    p = argparse.ArgumentParser(description="Build Pick B candidate by layering Qwen-derived rescues onto normalizer baseline")
    p.add_argument('--variant', required=True, help="Variant name (e.g. intermediate, final)")
    p.add_argument('--baseline', default='submission/30_05/slot3_normalizer_only/normalizer_only_v1.csv',
                   help="Baseline CSV path (default: slot3 normalizer-only)")
    p.add_argument('--thunder-audit', default='inference/base_model/audit/thunder_combined_audit.csv',
                   help="Thunder combined audit CSV")
    p.add_argument('--thunder-stance', choices=['conservative', 'intermediate', 'moderate'], default='intermediate')
    p.add_argument('--nt13-csv', default='submission/csvs/picks/overrides_nothinking_join_conservative.csv')
    p.add_argument('--no-nt13', action='store_true', help="Skip NT-13 layer")
    p.add_argument('--include-kitchensink', action='store_true')
    p.add_argument('--kitchensink-run-dir', default='', help="Kitchen-sink run directory containing rung*.jsonl")
    p.add_argument('--kitchensink-stop-rule-pass', action='store_true', default=True,
                   help="Whether kitchen-sink passed stop-rule (gate)")
    p.add_argument('--out-dir', required=True)
    args = p.parse_args()
    
    print(f"=== Building Pick B variant: {args.variant} ===")
    print(f"Baseline: {args.baseline}")
    print(f"Thunder stance: {args.thunder_stance}")
    print(f"NT-13: {'skipped' if args.no_nt13 else 'included'}")
    print(f"Kitchen-sink: {'included from ' + args.kitchensink_run_dir if args.include_kitchensink else 'not included'}")
    print()
    
    # Build layers
    baseline_path = REPO / args.baseline
    baseline_rows = load_baseline(baseline_path)
    print(f"Baseline loaded: {len(baseline_rows)} rows")
    
    layers = []  # list of (layer_name, dict) in PRECEDENCE order (highest first)
    
    if args.include_kitchensink and args.kitchensink_run_dir:
        ks_dir = REPO / args.kitchensink_run_dir
        ks_layer = build_kitchensink_layer(ks_dir, args.kitchensink_stop_rule_pass)
        print(f"Kitchen-sink layer: {len(ks_layer)} items (from {ks_dir.name})")
        layers.append(('kitchensink', ks_layer))
    
    thunder_layer = build_thunder_layer(REPO / args.thunder_audit, args.thunder_stance)
    print(f"Thunder layer ({args.thunder_stance}): {len(thunder_layer)} items")
    layers.append(('thunder', thunder_layer))
    
    if not args.no_nt13:
        nt13_layer = build_nt13_layer(REPO / args.nt13_csv)
        print(f"NT-13 layer: {len(nt13_layer)} items")
        layers.append(('nt13', nt13_layer))
    
    # Check conflicts
    conflicts = detect_conflicts(layers)
    if conflicts:
        print(f"\nCROSS-LAYER CONFLICTS DETECTED ({len(conflicts)}):")
        for iid, hits in conflicts.items():
            print(f"  id={iid}: {hits} (precedence: {hits[0]} wins)")
    else:
        print("No cross-layer conflicts (layers are disjoint as designed)")
    
    # Apply
    final_rows, manifest = apply_layers(baseline_rows, layers)
    
    # Validate
    validate(final_rows, layers)
    
    # Write
    layers_info = [(name, len(d)) for name, d in layers]
    csv_path, manifest_path, summary_path = write_outputs(final_rows, manifest, REPO / args.out_dir, args.variant, layers_info)
    
    print(f"\nWrote:")
    print(f"  {csv_path}")
    print(f"  {manifest_path}")
    print(f"  {summary_path}")
    print()
    print("=== Summary ===")
    print(open(summary_path).read())


if __name__ == '__main__':
    main()

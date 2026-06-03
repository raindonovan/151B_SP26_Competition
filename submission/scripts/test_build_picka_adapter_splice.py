#!/usr/bin/env python3
"""
Focused tests for adapter override picker logic in build_picka_adapter_splice.py.
"""

from __future__ import annotations

import csv
import subprocess
import tempfile
from pathlib import Path


ROOT = Path("/home/raindonovan/151B_SP26_Competition")
SCRIPT = ROOT / "submission/scripts/build_picka_adapter_splice.py"


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "response"])
        w.writeheader()
        w.writerows(rows)


def mk_base(path: Path, boxed=True):
    rows = []
    for i in range(943):
        resp = f"trace \\boxed{{base_{i}}}" if boxed else f"trace base_{i}"
        rows.append({"id": str(i), "response": resp})
    write_csv(path, rows)


def run(base: Path, parts: list[Path], out: Path):
    cmd = [
        "python3",
        str(SCRIPT),
        "--base",
        str(base),
        "--parts",
        *(str(p) for p in parts),
        "--out",
        str(out),
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


def read_map(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        return {int(r["id"]): r["response"] for r in rd}


def require(cond: bool, msg: str):
    if not cond:
        raise AssertionError(msg)


def main():
    td = Path(tempfile.mkdtemp(prefix="adapter_picker_test_", dir=ROOT))
    base = td / "base.csv"
    p0 = td / "v5_part_tnr0.csv"
    p1 = td / "v5_part_tnr1.csv"
    p2 = td / "v5_part_tnr02.csv"
    p3 = td / "v5_part_tnr3.csv"
    out = td / "out.csv"

    # CASE 1: Happy path override application.
    mk_base(base, boxed=True)
    write_csv(p0, [{"id": "10", "response": "ovr \\boxed{a}"}])
    write_csv(p1, [{"id": "500", "response": "ovr \\boxed{b}"}])
    write_csv(p2, [{"id": "900", "response": "ovr \\boxed{c}"}])
    write_csv(p3, [{"id": "0", "response": "ovr \\boxed{d}"}])
    r = run(base, [p0, p1, p2, p3], out)
    require(r.returncode == 0, f"case1 failed: {r.stderr}")
    m = read_map(out)
    require(m[10] == "ovr \\boxed{a}", "case1 id10 override not applied")
    require(m[500] == "ovr \\boxed{b}", "case1 id500 override not applied")
    require(m[1].startswith("trace \\boxed{base_1}"), "case1 fallback changed unexpectedly")

    # CASE 2: Empty override should not replace base.
    write_csv(p0, [{"id": "20", "response": "   "}])
    write_csv(p1, [])
    write_csv(p2, [])
    write_csv(p3, [])
    r = run(base, [p0, p1, p2, p3], out)
    require(r.returncode == 1, "case2 expected failure because empty shards are invalid")
    # rebuild valid minimal shards to test empty row skip behavior
    write_csv(p0, [{"id": "20", "response": "   "}, {"id": "21", "response": "ovr \\boxed{x}"}])
    write_csv(p1, [{"id": "22", "response": "ovr \\boxed{y}"}])
    write_csv(p2, [{"id": "23", "response": "ovr \\boxed{z}"}])
    write_csv(p3, [{"id": "24", "response": "ovr \\boxed{w}"}])
    r = run(base, [p0, p1, p2, p3], out)
    require(r.returncode == 0, f"case2b failed: {r.stderr}")
    m = read_map(out)
    require(m[20].startswith("trace \\boxed{base_20}"), "case2 empty override incorrectly replaced base")
    require(m[21] == "ovr \\boxed{x}", "case2 override missing")

    # CASE 3: Same-id same-response across shards is acceptable.
    write_csv(p0, [{"id": "30", "response": "ovr \\boxed{same}"}])
    write_csv(p1, [{"id": "30", "response": "ovr \\boxed{same}"}])
    write_csv(p2, [{"id": "31", "response": "ovr \\boxed{ok}"}])
    write_csv(p3, [{"id": "32", "response": "ovr \\boxed{ok2}"}])
    r = run(base, [p0, p1, p2, p3], out)
    require(r.returncode == 0, f"case3 failed: {r.stderr}")

    # CASE 4: Same-id conflicting response must fail.
    write_csv(p0, [{"id": "40", "response": "ovr \\boxed{A}"}])
    write_csv(p1, [{"id": "40", "response": "ovr \\boxed{B}"}])
    write_csv(p2, [{"id": "41", "response": "ovr \\boxed{ok}"}])
    write_csv(p3, [{"id": "42", "response": "ovr \\boxed{ok2}"}])
    r = run(base, [p0, p1, p2, p3], out)
    require(r.returncode != 0, "case4 expected conflict failure")
    require("Conflicting adapter responses" in (r.stderr + r.stdout), "case4 wrong failure reason")

    # CASE 5: Boxed ratio gate must fail when <= 50%.
    mk_base(base, boxed=False)
    write_csv(p0, [{"id": "100", "response": "no_boxed"}])
    write_csv(p1, [{"id": "101", "response": "no_boxed"}])
    write_csv(p2, [{"id": "102", "response": "no_boxed"}])
    write_csv(p3, [{"id": "103", "response": "no_boxed"}])
    r = run(base, [p0, p1, p2, p3], out)
    require(r.returncode != 0, "case5 expected boxed ratio failure")
    require("Boxed ratio <= 50%" in (r.stderr + r.stdout), "case5 wrong failure reason")

    print("ALL_TESTS_PASS")


if __name__ == "__main__":
    main()

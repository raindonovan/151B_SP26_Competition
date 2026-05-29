"""
OPL × Teacher-Consensus Join (Day 7)

For each of the 39 OK-status items in data/search/opl/match/candidates.csv:
  1. Extract clean OPL answer from raw Perl/PG syntax (Compute("X"), Real(N), etc.)
  2. Look up 3 teacher answers from data/MASTER_ANSWERS.csv
  3. Determine teacher unanimity (3/3, 2/3, or split)
  4. Compare teacher consensus to OPL answer (normalized string + numeric tolerance)
  5. Classify per spec:
       T1-promoted   : 3/3 teachers agree AND consensus matches OPL
       OPL-disagrees : 3/3 teachers agree, OPL says something different
       Split-teacher : teachers not unanimous (OPL is tiebreaker candidate)

Outputs:
  data/search/opl/findings_join.csv
"""
import csv
import json
import re
from pathlib import Path

REPO = Path("/home/claude/repo")
CANDS = REPO / "data/search/opl/match/candidates.csv"
MASTER = REPO / "data/MASTER_ANSWERS.csv"
OUT = REPO / "data/search/opl/findings_join.csv"


def extract_opl_answer(raw: str) -> str:
    """Pull the literal answer out of OPL Perl/PG cmp syntax.
    Returns the extracted string, or the raw string if no pattern matched."""
    s = raw.strip()
    # Compute("X")->cmp(), Compute('X')->cmp()
    m = re.search(r'Compute\(\s*["\']([^"\']+)["\']\s*\)', s)
    if m: return m.group(1).strip()
    # Real(N), Real(N)->cmp (no quotes)
    m = re.search(r'Real\(\s*([^)]+?)\s*\)', s)
    if m: return m.group(1).strip()
    # Numeric(N), num_cmp(N)
    m = re.search(r'(?:Numeric|num_cmp)\(\s*([^)]+?)\s*\)', s)
    if m: return m.group(1).strip()
    # fun_cmp("expr", var=>...) — pull the first quoted string
    m = re.search(r'fun_cmp\(\s*["\']([^"\']+)["\']', s)
    if m: return m.group(1).strip()
    # str_cmp("X"), Formula("X")
    m = re.search(r'(?:str_cmp|Formula|String|Point|Vector|Interval|List)\(\s*["\']([^"\']+)["\']', s)
    if m: return m.group(1).strip()
    # ans_eval, $ans-style, raw with ->cmp
    m = re.search(r'^["\']([^"\']+)["\']', s)
    if m: return m.group(1).strip()
    return s  # fallback — let downstream see the raw form


def normalize_for_compare(s: str) -> str:
    """Cheap normalization for string equality testing — Hendrycks-flavored."""
    if s is None: return ""
    s = str(s).strip().lower()
    # Strip \boxed{...} wrappers (keep contents)
    s = re.sub(r'\\boxed\s*\{([^}]+)\}', r'\1', s)
    # Strip \text{...} wrappers (keep contents)
    s = re.sub(r'\\text\s*\{([^}]+)\}', r'\1', s)
    # Strip outer braces, dollar signs, backticks, whitespace
    s = s.strip('{}$` \t\n')
    # LaTeX fraction equivalents
    s = s.replace('\\dfrac', '\\frac').replace('\\tfrac', '\\frac')
    # Strip cosmetic LaTeX
    s = re.sub(r'\\displaystyle\b', '', s)
    s = re.sub(r'\\(?:left|right)\b', '', s)
    s = re.sub(r'\\[!,;: ]', '', s)  # thin/thick spaces, \!, \, etc.
    # Pi normalization: \pi -> pi (so 256\pi t^2 == 256 pi t^2)
    s = s.replace('\\pi', 'pi')
    # Strip "var=" or "y=" / "u=" prefix at start (e.g. "y=-6.2x..." -> "-6.2x...")
    s = re.sub(r'^[a-z]\s*=\s*', '', s)
    # Brace-stripped single-char exponents: ^{2} -> ^2
    s = re.sub(r'\^\{([^{}]+)\}', r'^\1', s)
    # Brace-stripped single-token subscripts/args: _{x} -> _x
    s = re.sub(r'_\{([^{}]+)\}', r'_\1', s)
    # Collapse all whitespace
    s = re.sub(r'\s+', '', s)
    return s


def try_numeric(s: str):
    """Return a float if s parses as a number, else None."""
    if s is None: return None
    s = str(s).strip().strip('{}$`')
    # Handle simple fractions a/b
    m = re.match(r'^(-?\d+(?:\.\d+)?)\s*/\s*(-?\d+(?:\.\d+)?)$', s)
    if m:
        try: return float(m.group(1)) / float(m.group(2))
        except ZeroDivisionError: return None
    try: return float(s)
    except (ValueError, TypeError): return None


def answers_match(a: str, b: str) -> bool:
    """Compare two answer strings — numeric tolerance OR normalized string equality."""
    if a is None or b is None or a == "" or b == "":
        return False
    na, nb = try_numeric(a), try_numeric(b)
    if na is not None and nb is not None:
        return abs(na - nb) < 1e-6
    return normalize_for_compare(a) == normalize_for_compare(b)


def teacher_consensus(t_sonnet: str, t_gpt4: str, t_oss: str):
    """Return (unanimous_answer_or_None, agreement_count_max).
    unanimous = all three exactly match after normalization."""
    teachers = [t_sonnet or "", t_gpt4 or "", t_oss or ""]
    normed = [normalize_for_compare(t) for t in teachers]
    # Count how many of the three pairs match
    if normed[0] == normed[1] == normed[2] and normed[0] != "":
        return (t_sonnet, 3)
    # Two of three
    if normed[0] == normed[1] != "":
        return (t_sonnet, 2)
    if normed[0] == normed[2] != "":
        return (t_sonnet, 2)
    if normed[1] == normed[2] != "":
        return (t_gpt4, 2)
    return (None, 1)


# ---- main ----
print("Loading candidates.csv...")
with open(CANDS) as f:
    rows = [r for r in csv.DictReader(f) if r["top_status"] == "OK"]
print(f"  {len(rows)} OK-status rows")

print("Loading MASTER_ANSWERS.csv...")
with open(MASTER) as f:
    master = {r["item_id"]: r for r in csv.DictReader(f)}
print(f"  {len(master)} items")

print("Joining + classifying...")
out_rows = []
counts = {"T1-promoted": 0, "OPL-disagrees": 0, "split-teacher": 0, "missing-teacher": 0}
for r in rows:
    iid = r["id"]
    raw_opl = r["opl_first_answer"]
    opl_ans = extract_opl_answer(raw_opl)
    sim = r["top_similarity"]
    opl_path = r["top_opl_path"]

    m = master.get(iid)
    if not m:
        cls = "missing-teacher"
        notes = f"item_id={iid} not in MASTER_ANSWERS.csv"
        out_rows.append({
            "id": iid, "opl_answer": opl_ans, "opl_raw": raw_opl,
            "teacher_sonnet": "", "teacher_gpt4": "", "teacher_oss": "",
            "teacher_consensus": "", "teacher_agree_count": 0,
            "similarity": sim, "opl_path": opl_path,
            "classification": cls, "notes": notes,
        })
        counts[cls] += 1
        continue

    t_s, t_g, t_o = m.get("teacher_sonnet", ""), m.get("teacher_gpt4", ""), m.get("teacher_oss", "")
    consensus, agree_count = teacher_consensus(t_s, t_g, t_o)

    if agree_count == 3:
        if answers_match(consensus, opl_ans):
            cls = "T1-promoted"
            notes = "3/3 teachers AND OPL agree — two independent evidence types"
        else:
            cls = "OPL-disagrees"
            notes = f"3/3 teachers agree on '{consensus}' but OPL says '{opl_ans}' — manual review"
    else:
        cls = "split-teacher"
        notes = f"Teachers split ({agree_count}/3 max); OPL='{opl_ans}' is tiebreaker candidate"

    counts[cls] += 1
    out_rows.append({
        "id": iid, "opl_answer": opl_ans, "opl_raw": raw_opl,
        "teacher_sonnet": t_s, "teacher_gpt4": t_g, "teacher_oss": t_o,
        "teacher_consensus": consensus if consensus else "",
        "teacher_agree_count": agree_count,
        "similarity": sim, "opl_path": opl_path,
        "classification": cls, "notes": notes,
    })

print(f"\nResults:")
for k, v in counts.items():
    print(f"  {k}: {v}")
print(f"  total: {sum(counts.values())}")

# Write output
print(f"\nWriting {OUT}...")
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="") as f:
    fieldnames = [
        "id", "classification", "opl_answer", "teacher_consensus", "teacher_agree_count",
        "teacher_sonnet", "teacher_gpt4", "teacher_oss",
        "opl_raw", "similarity", "opl_path", "notes",
    ]
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    # Sort by classification then id for readability
    cls_order = {"T1-promoted": 0, "OPL-disagrees": 1, "split-teacher": 2, "missing-teacher": 3}
    out_rows.sort(key=lambda r: (cls_order.get(r["classification"], 9), int(r["id"])))
    for row in out_rows:
        w.writerow(row)
print("Done.")

#!/usr/bin/env python3
"""
Issue #7 — how far can public-slice membership actually be pinned down?

Method (the repo's own, from submission/REGISTRY.md: "realized +1.8pp = ~5 items
on slice"): the public LB scores 283 of the 943.  For two submissions differing
on item set S,

    delta_public * 283  =  net correctness change among  S ∩ public

A pair with a small |S| and a measured delta is a constraint on membership.
A pair with |S| small and delta == 0 says: no item of S is in public, OR the
changes cancelled, OR they changed nothing the grader scores.

This script finds every such usable pair and reports what it constrains.
"""
import csv, os, re, itertools, collections

ROOT = '/home/raindonovan/151B-SP26-Competition'
N_PUBLIC = 283
ELEVEN = [89, 127, 182, 302, 317, 389, 429, 463, 762, 776, 839]
FIFTY  = [0,1,2,3,4,5,6,9,18,20,21,25,26,27,28,30,31,33,35,41,42,43,44,46,52,56,
          60,61,62,63,64,67,68,71,444,445,446,449,451,700,701,704,705,707,708,
          710,712,718,720,723]
TARGETS = set(ELEVEN) | set(FIFTY)

# ---- score table from REGISTRY (public LB) -------------------------------
scores = {}
for line in open(os.path.join(ROOT, 'submission/REGISTRY.md'), encoding='utf-8'):
    m = re.match(r'^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*\**([0-9.]+)\**\s*\|', line)
    if m:
        scores[m.group(2)] = float(m.group(3))

# ---- resolve each to a file on disk --------------------------------------
disk = {}
for dirpath, _, files in os.walk(os.path.join(ROOT, 'submission')):
    if '/scripts' in dirpath:
        continue
    for fn in files:
        if fn.endswith('.csv'):
            disk.setdefault(fn, []).append(os.path.join(dirpath, fn))

def resolve(relpath):
    p = os.path.join(ROOT, 'submission', relpath)
    if os.path.isfile(p):
        return p
    cands = disk.get(os.path.basename(relpath), [])
    return cands[0] if len(cands) == 1 else None

def load(path):
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None
    kid = 'id' if 'id' in rows[0] else list(rows[0])[0]
    krs = 'response' if 'response' in rows[0] else list(rows[0])[-1]
    try:
        return {int(r[kid]): (r[krs] or '').strip() for r in rows}
    except (ValueError, TypeError):
        return None

subs = {}
for rel, sc in scores.items():
    p = resolve(rel)
    if not p:
        continue
    d = load(p)
    if d and len(d) > 900:
        subs[rel] = (sc, d)

print(f'REGISTRY rows with a score : {len(scores)}')
print(f'resolved to a 943-row CSV  : {len(subs)}')
print()

BOX = re.compile(r'\\boxed\{')
def boxed(s):
    """last \\boxed{...} content, brace-balanced; else the whole cell."""
    last = None
    for m in BOX.finditer(s):
        i, depth = m.end(), 1
        while i < len(s) and depth:
            if s[i] == '{': depth += 1
            elif s[i] == '}': depth -= 1
            i += 1
        last = s[m.end():i-1]
    return (last if last is not None else s).strip()

# ---- pairwise diffs -------------------------------------------------------
pairs = []
names = sorted(subs)
for a, b in itertools.combinations(names, 2):
    sa, da = subs[a]; sb, db = subs[b]
    ids = set(da) & set(db)
    diff = sorted(i for i in ids if boxed(da[i]) != boxed(db[i]))
    if diff:
        pairs.append((len(diff), a, b, sa, sb, diff))
pairs.sort()

print('=' * 78)
print('USABLE PAIRS — small diff set with a measured public delta')
print('=' * 78)
usable = [p for p in pairs if p[0] <= 30]
if not usable:
    print('  none with |S| <= 30')
for n, a, b, sa, sb, diff in usable[:25]:
    d = sb - sa
    print(f'  |S|={n:<4} d_public={d:+.3f} = {d*N_PUBLIC:+5.1f} items')
    print(f'     {os.path.basename(a)}  ({sa})')
    print(f'     {os.path.basename(b)}  ({sb})')
    hit = sorted(set(diff) & TARGETS)
    print(f'     ids={diff[:18]}{" ..." if n > 18 else ""}')
    if hit:
        print(f'     *** touches {len(hit)} target items: {hit}')
    print()

# ---- coverage of our targets ---------------------------------------------
print('=' * 78)
print('TARGET COVERAGE — is any override item in a small enough diff to pin?')
print('=' * 78)
cover = collections.defaultdict(list)
for n, a, b, sa, sb, diff in pairs:
    if n > 30:
        continue
    for i in set(diff) & TARGETS:
        cover[i].append((n, abs(sb - sa) * N_PUBLIC))
for grp, ids in (('the 11', ELEVEN), ('the 50', FIFTY)):
    have = [i for i in ids if i in cover]
    print(f'  {grp}: {len(have)}/{len(ids)} appear in any pair with |S|<=30 -> {have}')

# =====================================================================
# THE DECISIVE CONSTRAINT — the 11-overlay has BOTH scores
# =====================================================================
print()
print('=' * 78)
print('THE 11-OVERLAY: public AND private measured on the SAME 11-cell change')
print('=' * 78)
base_pub, base_prv = 0.667, 0.583          # slot1_baseline_R20
adpt_pub, adpt_prv = 0.667, 0.587          # slot_adapter_rescue
N_PRIV = 943

d_pub, d_prv = adpt_pub - base_pub, adpt_prv - base_prv
print(f'  public  (283 items, a SUBSET of the 943): {base_pub} -> {adpt_pub}'
      f'   d={d_pub:+.3f} = {d_pub*N_PUBLIC:+.2f} items')
print(f'  private (the FULL 943)                  : {base_prv} -> {adpt_prv}'
      f'   d={d_prv:+.3f} = {d_prv*N_PRIV:+.2f} items')
print()
# 3dp rounding -> true delta lies in a band; convert the band to item counts
def band(d, n):
    return (round((d - 0.0005) * n, 2), round((d + 0.0005) * n, 2))
print(f'  rounding bands: public {band(d_pub, N_PUBLIC)} items,'
      f'  private {band(d_prv, N_PRIV)} items')
print()
print('  Every one of the 11 is scored in private (private IS the 943).')
print('  Only those that fall in the 283 are scored in public.')
print()
print('  => items in public contributed NET 0')
print(f'  => items NOT in public contributed NET +{round(d_prv*N_PRIV)}')
print()
print('  CONCLUSION: all ~4 net gains land OUTSIDE the public subset.')
print()
p_miss = 0.7 ** 6
print(f'  If the 283 were a uniform 30% draw, P(none of the 6 adapter_wins')
print(f'  lands in public) = 0.7^6 = {p_miss:.3f} ({p_miss*100:.0f}%).')
print('  Uncommon but not remarkable — and it is not the only explanation:')
print('  a win landing in public could be cancelled by 302/839 (`H, H`->`H`,')
print('  `G, G`->`G`) if Kaggle grades the multi-slot form differently than')
print('  our local is_equal does.  That alternative is testable and is the')
print('  reason #7 cannot be closed on arithmetic alone.')

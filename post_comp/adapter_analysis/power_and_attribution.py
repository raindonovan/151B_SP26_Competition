#!/usr/bin/env python3
"""
Issues #8 / #9: per-item attribution + what the observed deltas can mean.

Denominators, from COMPETITION.md:42-48 (this is the correction that matters):
  public  ~283 items, a ~30% SUBSET of the private set  -> 1 item = 0.3534 pp
  private the FULL 943                                  -> 1 item = 0.1060 pp
Every override is therefore in the private set by construction; only ~30% of
them land in public.  Any arithmetic that treats private as a ~660-item
complement of public is wrong.
"""
import csv, io, json, os, collections

ROOT = '/home/raindonovan/151B-SP26-Competition'
def rd(p):
    lines = [l for l in open(os.path.join(ROOT, p), encoding='utf-8') if not l.startswith('#')]
    return list(csv.DictReader(io.StringIO(''.join(lines))))

N_PRIVATE, N_PUBLIC = 943, 283
PP_PRIV, PP_PUB = 100.0 / N_PRIVATE, 100.0 / N_PUBLIC

r20    = {int(x['item_id']): x for x in rd('inference/base_model/R20_eval_v1_sc8_p943_t32k_pp1/analysis/analysis.csv')}
decomp = {int(x['item_id']): x for x in rd('data/v5_per_item_decomp.csv')}

ELEVEN = [89, 127, 182, 302, 317, 389, 429, 463, 762, 776, 839]
truthy = lambda v: str(v).strip().lower() in ('true', '1', 'yes')

print('=' * 74)
print('ISSUE #9 — RESOLUTION LIMITS')
print('=' * 74)
print(f'  private = {N_PRIVATE} items -> 1 item = {PP_PRIV:.4f} pp')
print(f'  public  = {N_PUBLIC} items -> 1 item = {PP_PUB:.4f} pp')
print()
for label, base, adpt, n, pp in [
    ('11-item overlay, PRIVATE', 0.583, 0.587, N_PRIVATE, PP_PRIV),
    ('11-item overlay, PUBLIC ', 0.667, 0.667, N_PUBLIC,  PP_PUB),
]:
    d = adpt - base
    print(f'  {label}: {base} -> {adpt}  delta {d:+.3f} = {d*n:+.2f} items')

print()
print('=' * 74)
print('ISSUE #8 — THE 11, ITEM BY ITEM')
print('=' * 74)
hdr = f"{'id':>4} {'cls':<13} {'tier':<4} {'gold_source':<19} {'ind':<5} {'base':<18} {'adapter':<18}"
print(hdr); print('-' * len(hdr))
cnt = collections.Counter()
for i in ELEVEN:
    d, a = decomp.get(i, {}), r20.get(i, {})
    ind = truthy(a.get('gold_independent_flag'))
    cls = d.get('classification', '?')
    cnt[cls] += 1
    print(f"{i:>4} {cls:<13} {d.get('tier',''):<4} {a.get('gold_source',''):<19} "
          f"{str(ind):<5} {(d.get('base_voted_answer','') or '')[:17]:<18} "
          f"{(d.get('adapter_voted_answer','') or '')[:17]:<18}")
print()
print('  classification:', dict(cnt))

wins = [i for i in ELEVEN if decomp.get(i, {}).get('classification') == 'adapter_win']
wins_ind = [i for i in wins if truthy(r20.get(i, {}).get('gold_independent_flag'))]
print(f'  adapter_win: {len(wins)} -> {wins}')
print(f'    of which independent gold: {len(wins_ind)} -> {wins_ind}')
print(f'    of which circular (sheet_dependent, and the item is in training): '
      f'{len(wins) - len(wins_ind)} -> {sorted(set(wins) - set(wins_ind))}')

print()
print('=' * 74)
print('THE BOUND')
print('=' * 74)
maxg = len(wins)
print(f'  The overlay replaced 11 cells.  By the repo\'s own decomposition only')
print(f'  {maxg} of them can possibly gain a point ({len(cnt)>0 and cnt["both_wrong"]} both_wrong and '
      f'{cnt["both_correct"]} both_correct contribute 0 by construction).')
print(f'  So the maximum achievable private delta is {maxg} items = {maxg*PP_PRIV/100:+.4f}')
print(f'  Observed: +0.004 = {0.004*N_PRIVATE:.2f} items.')
print(f'  => roughly {0.004*N_PRIVATE:.0f} of a possible {maxg} landed.  The measurement is')
print(f'     bounded above, which is worth more than the point estimate.')
print()
exp_pub = len(wins) * N_PUBLIC / N_PRIVATE
print(f'  PUBLIC tension: ~{11*N_PUBLIC/N_PRIVATE:.1f} of the 11 fall in public, carrying')
print(f'  ~{exp_pub:.1f} expected wins = {exp_pub*PP_PUB:+.2f} pp.  Observed 0.000.')
print(f'  Either the public draw missed the wins, or those "wins" are not wins on')
print(f'  Kaggle gold.  Issue #7 (slice membership) decides it.')

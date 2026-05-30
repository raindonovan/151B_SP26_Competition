"""gold_equiv — type-routed value-equality for cross-signal answer comparison.
Mirrors the Kaggle judger (root judger.py) as primary; sympy-numeric fallback only
fixes PARSE coverage (ascii<->LaTeX, symbolic), never adds leniency beyond value-equality.
Returns True (agree) / False (disagree) / None (incomparable: e.g. MCQ-letter vs numeric)."""
import re, sys
sys.path.insert(0, '.')
from judger import Judger
_J = Judger()
TOL = 1e-8

def _latex_to_ascii(s):
    s = s.replace('\\left', '').replace('\\right', '').replace('\\,', '').replace('\\!', '').replace('\\ ', ' ')
    s = s.replace('\\cdot', '*').replace('\\times', '*').replace('\\div', '/')
    s = re.sub(r'\\d?frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}', r'((\1)/(\2))', s)
    s = re.sub(r'\\sqrt\s*\{([^{}]+)\}', r'sqrt(\1)', s)
    s = re.sub(r'\\sqrt\s*(\w)', r'sqrt(\1)', s)
    s = s.replace('\\pi', 'pi').replace('\\ln', 'log').replace('\\log', 'log')
    s = s.replace('^', '**').replace('\\', '')
    return s

def _strip_wrap(s):
    s = s.strip()
    while len(s) >= 2 and s[0] in '([{' and s[-1] in ')]}':
        depth, ok = 0, True
        for i, ch in enumerate(s):
            if ch in '([{': depth += 1
            elif ch in ')]}': depth -= 1
            if depth == 0 and i < len(s) - 1: ok = False; break
        if ok: s = s[1:-1].strip()
        else: break
    return s

def _to_number(s):
    """Best-effort -> float, else None."""
    if not s: return None
    s = s.strip().lstrip('$').strip()
    s = re.sub(r'^[A-Za-z][\w\s]{0,12}=\s*', '', s)
    s = re.sub(r'\s*(mL|ml|cm|kg|g|units?|dollars?)\s*$', '', s)
    if not s or any(w in s.lower() for w in ('dne', 'not real', 'infinity', 'undefined', 'none')):
        return None
    from sympy import N
    from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                            implicit_multiplication_application)
    tr = standard_transformations + (implicit_multiplication_application,)
    candidates = []
    if '\\' in s:                      # real LaTeX parser handles nested braces
        try:
            from sympy.parsing.latex import parse_latex
            candidates.append(parse_latex(_strip_wrap(s)))
        except Exception:
            pass
    a = _strip_wrap(_latex_to_ascii(s))  # ascii fallback
    a = re.sub(r'\bln\b', 'log', a)
    try:
        candidates.append(parse_expr(a, transformations=tr, evaluate=True))
    except Exception:
        pass
    for expr in candidates:
        try:
            v = complex(N(expr))
            if abs(v.imag) < 1e-9:
                return v.real
        except Exception:
            continue
    return None

def _num_eq(a, b):
    na, nb = _to_number(a), _to_number(b)
    if na is None or nb is None: return None
    return abs(na - nb) <= TOL * max(1.0, abs(nb))

def _is_letter(x): return len(x.strip()) == 1 and x.strip().isalpha()

def _slots(s):
    s = _strip_wrap(s)
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch in '{[(': depth += 1
        elif ch in '}])': depth -= 1
        if ch == ',' and depth == 0: out.append(cur); cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur)
    return [x.strip() for x in out if x.strip()]

def _scalar_eq(a, b):
    """One slot. Judger primary (Kaggle-mirror); sympy numeric fixes parse gaps."""
    a, b = a.strip(), b.strip()
    if not a or not b: return None
    try:
        if '=' in a and '=' in b:
            if _J.judge_equation(a, b): return True
        elif _J.judge_single_numerical_value(a, b):
            return True
    except Exception:
        pass
    ne = _num_eq(a, b)               # parse-coverage fallback (same value-equality intent)
    if ne is True: return True
    if ne is False: return False
    return a == b or None            # non-numeric (set/word) -> exact or incomparable

def gold_equiv(pred, gold, qtype):
    pred, gold = (pred or '').strip(), (gold or '').strip()
    if not pred or not gold: return None
    if qtype == 'MCQ':
        if _is_letter(pred) and _is_letter(gold): return pred.upper() == gold.upper()
        return None                                   # letter vs numeric -> incomparable
    if qtype == 'free_single':
        r = _scalar_eq(pred, gold)
        return r
    # free_multi: order-insensitive set match (corroboration, not submission order)
    ps, gs = _slots(pred), _slots(gold)
    if not ps or not gs: return _scalar_eq(pred, gold)
    small, large = (ps, gs) if len(ps) <= len(gs) else (gs, ps)
    used, matched = set(), 0
    for a in small:
        for j, b in enumerate(large):
            if j in used: continue
            if _scalar_eq(a, b) is True: used.add(j); matched += 1; break
    if matched < len(small): return False
    return True if len(ps) == len(gs) else None       # subset = undercount/review

if __name__ == '__main__':
    tests = [
        ('eqn whitespace', 'free_single', '2c + 4p = 70', '2c+4p=70', True),
        ('ascii vs latex sqrt', 'free_single', '-sqrt(3)/2', '-\\frac{\\sqrt3}{2}', True),
        ('ascii vs latex frac', 'free_single', '(4*sqrt(78)-35)/72', '\\frac{4\\sqrt{78}-35}{72}', True),
        ('pi expr equal', 'free_single', '7.7*31*pi/180', '\\frac{2387\\pi}{1800}', True),
        ('paren tuple', 'free_multi', '76.37, 79.63', '(76.37, 79.63)', True),
        ('real rounding (10.66 vs 10.7)', 'free_single', '5*ln(17/2)', '10.7', False),
        ('real value diff', 'free_single', '2112', '4048', False),
        ('value diff multi', 'free_multi', '9, 6', '3,2', False),
        ('exact frac=dec', 'free_single', '3/5', '0.6', True),
        ('mcq letter vs num', 'MCQ', '232', 'I', None),
        ('mcq agree', 'MCQ', 'B', 'B', True),
        ('undercount review', 'free_multi', '4450', '4450,14', None),
    ]
    print(f"{'case':<32}{'got':<8}{'want':<8}ok")
    for name, t, a, b, want in tests:
        got = gold_equiv(a, b, t)
        print(f"{name:<32}{str(got):<8}{str(want):<8}{'OK' if got==want else 'XXXX'}")

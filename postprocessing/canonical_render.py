#!/usr/bin/env python3
"""canonical_render.py — canonical answer rendering for the 03_06 source campaign.

ONE function, applied identically to every sheet: render_canonical(raw_value, n_slots, is_mcq).

Spec (CANONICAL_RENDER.md). VALUE NEVER CHANGES — render only:
  - eval pure arithmetic: 4+9 -> 13 ; 8\\div3 -> \\frac{8}{3} (only when the whole slot is a
    pure numeric arithmetic expression; symbolic/text slots are left untouched).
  - "*" -> "\\cdot"
  - integer a/b -> \\frac{a}{b}
  - multi-slot: split into n_slots ordered values, emit ONE \\boxed{a, b, c}
  - MCQ: \\boxed{LETTER}
  - symbolic: clean LaTeX (whitespace-normalized), value preserved verbatim otherwise.

The output is always a single ``\\boxed{...}`` string (the response cell of the submission CSV).
Rendering is idempotent and never converts one value to a different value: arithmetic
evaluation is gated to exact rational results, so 4+9 -> 13 but 1/3 stays \\frac{1}{3}
(value-equal, not 0.333...).
"""
from __future__ import annotations

import re
from fractions import Fraction

# ── slot splitting ──────────────────────────────────────────────────────────
# Multi-slot values are comma-separated. We must NOT split commas inside braces
# (\\frac{a,b} never occurs, but tuples / intervals like (1, 2) and sets must be kept whole).
_TOPLEVEL_COMMA = re.compile(r",(?![^{(\[]*[})\]])")


def split_slots(value: str):
    """Split a raw answer into top-level comma-separated slots (brace/paren/bracket aware)."""
    s = value.strip()
    if not s:
        return []
    parts, depth, buf = [], 0, []
    for ch in s:
        if ch in "{([":
            depth += 1
        elif ch in "})]":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf).strip())
    return [p for p in parts if p != ""]


# ── per-slot canonicalization ─────────────────────────────────────────────────
_PURE_ARITH = re.compile(r"^[\d\s+\-*/().]+$")
_INT_FRAC = re.compile(r"^(-?\d+)\s*/\s*(\d+)$")
_DIV = re.compile(r"^(-?\d+)\s*\\div\s*(\d+)$")


def _canon_slot(slot: str) -> str:
    s = slot.strip()
    if s == "":
        return s

    # "*" -> "\cdot"  (multiplication dot; do this before arithmetic eval guard)
    # Only standalone * between operands, not "**" exponent.
    s_cdot = re.sub(r"(?<![*\\])\*(?!\*)", r" \\cdot ", s)

    # a\div b -> \frac{a}{b}  (integer operands)
    m = _DIV.match(s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return _frac(a, b)

    # integer a/b -> \frac{a}{b}
    m = _INT_FRAC.match(s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return _frac(a, b)

    # pure arithmetic (no \cdot inserted, original had no '*' meaning symbolic): eval to exact rational
    if _PURE_ARITH.match(s) and re.search(r"[+\-*/]", s.replace("**", "")) and "**" not in s:
        try:
            # safe eval over arithmetic only; use Fraction for exactness
            val = eval(s, {"__builtins__": {}}, {})  # noqa: S307 — gated by _PURE_ARITH
            fr = Fraction(val).limit_denominator(10**9)
            if fr.denominator == 1:
                return str(fr.numerator)
            return _frac(fr.numerator, fr.denominator)
        except Exception:
            pass

    # symbolic: return whitespace-cleaned, with * -> \cdot applied
    return re.sub(r"\s+", " ", s_cdot).strip()


def _frac(a: int, b: int) -> str:
    """integer a/b -> reduced \\frac{a}{b}; b==1 -> integer; sign on numerator."""
    fr = Fraction(a, b)
    if fr.denominator == 1:
        return str(fr.numerator)
    n, d = fr.numerator, fr.denominator
    if n < 0:
        return f"-\\frac{{{-n}}}{{{d}}}"
    return f"\\frac{{{n}}}{{{d}}}"


# ── top-level render ──────────────────────────────────────────────────────────
def render_canonical(raw_value: str, n_slots=None, is_mcq=False) -> str:
    """Return a single ``\\boxed{...}`` string. VALUE preserved; render only."""
    raw = (raw_value or "").strip()
    if raw == "":
        return "\\boxed{}"

    # MCQ: single letter (or letters) -> \boxed{LETTER}
    if is_mcq:
        slots = split_slots(raw)
        slots = [sl.strip() for sl in slots if sl.strip() != ""]
        return "\\boxed{" + ", ".join(slots) + "}"

    slots = split_slots(raw)
    canon = [_canon_slot(sl) for sl in slots]
    canon = [c for c in canon if c != ""]
    return "\\boxed{" + ", ".join(canon) + "}"


if __name__ == "__main__":
    # smoke
    tests = [
        ("4+9", None, False, "\\boxed{13}"),
        ("8\\div3", None, False, "\\boxed{\\frac{8}{3}}"),
        ("13, 8\\div3", None, False, "\\boxed{13, \\frac{8}{3}}"),
        ("3*x", None, False, "\\boxed{3 \\cdot x}"),
        ("1/3", None, False, "\\boxed{\\frac{1}{3}}"),
        ("A", None, True, "\\boxed{A}"),
        ("4, 16", None, False, "\\boxed{4, 16}"),
    ]
    for raw, n, mcq, exp in tests:
        got = render_canonical(raw, n, mcq)
        print(("OK " if got == exp else "XX ") + f"{raw!r} -> {got!r} (exp {exp!r})")

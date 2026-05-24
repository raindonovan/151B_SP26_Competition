#!/usr/bin/env python3
"""
post_inference_sc1.py — Comprehensive post-inference pipeline for SC=1 runs.

Applies all checks and fixes to a raw inference JSONL before building
the final Kaggle submission CSV. Designed to be the single standard
post-processing step for all SC=1 greedy runs.

Checks applied (in order):
  1. Truncation detection   — response ends without \boxed{} due to token cap
  2. Degenerate detection   — response stuck in repetition loop
  3. Multi-answer format    — multiple \boxed{} → single \boxed{a, b, c}
                              (incorporates fix_submission_format.py logic)
  4. LaTeX normalization    — strip \text{...} suffixes, clean whitespace
  5. Word-answer flagging   — flag "Unchanged", "None", "Cannot determine" etc.
  6. Fallback filling       — no-box items → teacher consensus (Sonnet > GPT-5.4 > GPT-OSS)
  7. Final sanity checks    — row count, IDs, column names, no empties

Usage:
    python3 scripts/post_inference_sc1.py \
        --input  results/sftv3_epoch8_sc1_greedy.jsonl \
        --data   private.jsonl \
        --output submissions/sftv3_epoch8_sc1_final.csv \
        [--manifest dataapp_outputs/dataset_manifest.jsonl]  # for teacher fallback
        [--dry-run]
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path


# ─── \boxed{} utilities (from fix_submission_format.py) ──────────────────────

def extract_all_boxed(text: str) -> list[str]:
    """Nested-brace-aware extractor for \\boxed{...} content.
    Handles multiline content and display-math-wrapped boxes.

    After extracting a candidate boxed content we perform lightweight
    checks for common truncation patterns (unbalanced parentheses,
    unmatched \left/\right pairs). If the boxed text appears to be
    missing a trailing \right... delimiter we attempt a short lookahead
    in the source text and append the delimiter to the extracted
    content so downstream checks don't treat it as truncated.
    """
    results = []
    i = 0
    L = len(text)
    while i < L:
        pos = text.find("\\boxed{", i)
        if pos == -1:
            break
        depth = 1
        j = pos + 7
        while j < L and depth > 0:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
            j += 1

        if depth == 0:
            content = text[pos + 7: j - 1].strip()

            # Quick imbalance check: parentheses, brackets and \left/\right
            def seems_unbalanced(s: str) -> bool:
                if s.count('(') != s.count(')'):
                    return True
                if s.count('[') != s.count(']'):
                    return True
                # braces inside boxed are handled by the extractor itself,
                # but unmatched \left / \right sequences are common in
                # piecewise / display-math situations.
                if s.count('\\left') > s.count('\\right'):
                    return True
                return False

            # If content seems unbalanced, try a short lookahead to capture
            # a trailing '\\right.' or similar delimiter that was placed
            # outside the box (common with \left...\right.). We only
            # extend up to 200 chars to avoid runaway scanning.
            if seems_unbalanced(content):
                lookahead = text[j:j+200]
                # Prefer an explicit \right token
                k = lookahead.find('\\right')
                if k != -1:
                    # capture the '\\right' token and following punctuation
                    k0 = j + k
                    k1 = k0 + len('\\right')
                    # include following punctuation characters like . ) ] }
                    while k1 < L and text[k1] in '.])}':
                        k1 += 1
                    # append the small suffix to the content (keeps original)
                    suffix = text[k0:k1]
                    content = (content + ' ' + suffix).strip()
                else:
                    # No explicit \right found — also accept a bare display
                    # math close '\\]' or ']' immediately after the box.
                    m = re.match(r"\s*(\\\\\]|\]|\\\\\))", lookahead)
                    if m:
                        suffix = m.group(1)
                        content = (content + ' ' + suffix).strip()

            # Skip empty boxes
            if content:
                results.append(content)

        i = pos + 7
    return results


def replace_last_boxed(text: str, new_content: str) -> str:
    """Replace the last \\boxed{...} in text with \\boxed{new_content}."""
    last_pos = -1
    i = 0
    while i < len(text):
        pos = text.find("\\boxed{", i)
        if pos == -1:
            break
        last_pos = pos
        i = pos + 7
    if last_pos == -1:
        return text + f" \\boxed{{{new_content}}}"
    depth = 1
    j = last_pos + 7
    while j < len(text) and depth > 0:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    return text[:last_pos] + f"\\boxed{{{new_content}}}" + text[j:]


def append_boxed(text: str, answer: str) -> str:
    """Append \\boxed{answer} to a response that has no boxed answer."""
    return text.rstrip() + f"\n\n\\boxed{{{answer}}}"


# ─── Item type helpers ────────────────────────────────────────────────────────

def n_ans_placeholders(question: str) -> int:
    return question.count("[ANS]")


def is_mcq(item: dict) -> bool:
    return isinstance(item.get("options"), list) and bool(item["options"])


def is_multi_answer(item: dict) -> bool:
    if is_mcq(item):
        return False
    a = item.get("answer")
    if isinstance(a, list) and len(a) >= 2:
        return True
    return n_ans_placeholders(item.get("question", "")) >= 2


def expected_n_answers(item: dict) -> int:
    a = item.get("answer")
    if isinstance(a, list):
        return len(a)
    return max(1, n_ans_placeholders(item.get("question", "")))


# ─── Check 1: Truncation detection ───────────────────────────────────────────

TRUNCATION_PATTERNS = [
    r"\.\.\.$",              # ends with ellipsis
    r"[a-zA-Z0-9]\s*$",     # ends mid-word/number (no punctuation)
    r"\\frac\{[^}]*$",      # unclosed \frac
    r"\([^)]*$",            # unclosed parenthesis
]

def is_truncated(response: str, token_count: int, max_tokens: int) -> bool:
    """Detect if response was truncated at token cap."""
    # Hit token cap and no \boxed{}
    if token_count >= max_tokens * 0.99 and not extract_all_boxed(response):
        return True
    # Has \boxed{} but token count very close to cap (might have cut off last boxed)
    if token_count >= max_tokens * 0.99:
        return True
    return False


# ─── Check 2: Degenerate loop detection ──────────────────────────────────────

def is_degenerate(response: str, window: int = 80, threshold: int = 4) -> bool:
    """Detect if response is stuck in a repetition loop.

    This is tuned to catch common generator loops including snippets
    like repeated '\\sqrt{2016}' fragments. Instead of looking for an
    exact repeated window we match a short prefix of the final window
    across a slightly longer tail and count occurrences.
    """
    if len(response) < window * threshold:
        return False
    tail = response[-window * (threshold + 2):]
    chunk = response[-window:]
    # use a short seed from the end to be robust to minor tokenization
    seed = chunk[:40]
    count = tail.count(seed)
    return count >= threshold


# ─── Check 3: Multi-answer format fix (from fix_submission_format.py) ────────

def fix_multi_answer(response: str, n: int) -> tuple[str, str]:
    """Consolidate multiple \\boxed{} into single \\boxed{v1, v2, ...}."""
    boxes = extract_all_boxed(response)

    if not boxes:
        return response, "no_box"

    last = boxes[-1]
    if "," in last:
        return response, "already_comma"

    if len(boxes) == 1:
        return response, "single_no_comma"

    # Take last N unique non-empty values
    unique_vals = []
    seen = set()
    for b in reversed(boxes):
        b_stripped = b.strip()
        if b_stripped and b_stripped not in seen:
            seen.add(b_stripped)
            unique_vals.insert(0, b_stripped)
        if len(unique_vals) == n:
            break

    consolidated = ", ".join(unique_vals)
    action = f"consolidated_{len(unique_vals)}_of_{n}"
    return replace_last_boxed(response, consolidated), action


# ─── Check 4: LaTeX normalization ────────────────────────────────────────────

# Patterns that add noise without changing the answer
LATEX_NOISE_PATTERNS = [
    (r'\\text\s*\{[^}]{1,30}\}$', ''),    # trailing \text{...} after last boxed content
    (r'\s+$', ''),                          # trailing whitespace
]

def normalize_boxed_content(content: str) -> str:
    """
    Normalize the content inside \\boxed{} to reduce grader mismatches.
    Conservative — only removes provably-redundant suffixes.
    """
    original = content

    # Strip trailing \text{...} units suffix (e.g. "\frac{180}{7}\text{ grams}" → "\frac{180}{7}")
    # Only if the \text{} is at the end and looks like a unit/label, not the answer itself
    stripped = re.sub(r'\\text\s*\{[^}]{1,20}\}\s*$', '', content).strip()
    if stripped and stripped != content:
        content = stripped

    # Strip trailing whitespace inside boxed
    content = content.strip()

    return content


def apply_latex_normalization(response: str) -> tuple[str, bool]:
    """Normalize the content of the last \\boxed{} in the response."""
    boxes = extract_all_boxed(response)
    if not boxes:
        return response, False

    last = boxes[-1]
    normalized = normalize_boxed_content(last)

    if normalized == last:
        return response, False

    return replace_last_boxed(response, normalized), True


# ─── Check 5: Word-answer detection ──────────────────────────────────────────

WORD_ANSWERS = {
    'unchanged', 'undefined', 'none', 'n/a', 'cannot', 'no solution',
    'does not exist', 'no answer', 'unknown', 'varies', 'impossible',
}

def is_word_answer(answer: str) -> bool:
    """Flag answers that are likely wrong because they're generic words."""
    if not answer:
        return False
    a = answer.lower().strip()
    return any(w in a for w in WORD_ANSWERS)


# ─── Check 6: Teacher fallback ───────────────────────────────────────────────

def load_teacher_fallbacks(manifest_path: str) -> dict[int, str]:
    """
    Load teacher answers from DataApp manifest.
    Priority: Sonnet → GPT-5.4 → GPT-OSS (exclude xhigh).
    """
    fallbacks = {}
    with open(manifest_path) as f:
        for line in f:
            item = json.loads(line)
            item_id = item.get("id")
            if item_id is None:
                continue

            for key in ["sonnet_answer_raw", "gpt5_4_answer_raw", "gpt_oss_answer_raw"]:
                ans = item.get(key, "").strip()
                # Reject obviously bad teacher answers
                if ans and len(ans) < 300 and "probably" not in ans.lower():
                    fallbacks[int(item_id)] = ans
                    break

    return fallbacks


# ─── Main pipeline ────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="SC=1 post-inference pipeline")
    p.add_argument("--input", required=True,
                   help="Raw inference JSONL (item_id, response, tokens)")
    p.add_argument("--data", required=True,
                   help="Competition data JSONL (private.jsonl)")
    p.add_argument("--output", required=True,
                   help="Output Kaggle submission CSV")
    p.add_argument("--manifest", default=None,
                   help="DataApp manifest JSONL for teacher fallback answers")
    p.add_argument("--max-tokens", type=int, default=8192,
                   help="Max tokens used during inference (for truncation detection)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print report only, do not write CSV")
    args = p.parse_args()

    # ── Load data ─────────────────────────────────────────────────────────────
    print(f"Loading competition data from {args.data}...")
    items = {}
    with open(args.data) as f:
        for line in f:
            d = json.loads(line)
            items[d["id"]] = d

    print(f"Loading inference results from {args.input}...")
    results = {}
    with open(args.input) as f:
        for line in f:
            r = json.loads(line)
            # Handle both int and string item_id keys
            item_id = int(r.get("item_id", r.get("id", -1)))
            results[item_id] = r

    teacher_fallbacks = {}
    if args.manifest and Path(args.manifest).exists():
        print(f"Loading teacher fallbacks from {args.manifest}...")
        teacher_fallbacks = load_teacher_fallbacks(args.manifest)
        print(f"  {len(teacher_fallbacks)} teacher answers loaded")
    else:
        if args.manifest:
            print(f"WARNING: manifest not found at {args.manifest} — no teacher fallback")

    # ── Process each item ─────────────────────────────────────────────────────
    report_items = []
    final_rows = []

    stats = Counter()

    for item_id in range(943):
        item = items.get(item_id, {})
        result = results.get(item_id)

        if result is None:
            stats["missing_inference"] += 1
            report_items.append({
                "id": item_id, "issue": "MISSING_INFERENCE",
                "action": "empty", "original": "", "final": ""
            })
            final_rows.append({"id": item_id, "response": ""})
            continue

        response = result.get("response", "")
        token_count = result.get("tokens", 0)
        issues = []
        actions = []

        # ── Check 1: Truncation ──────────────────────────────────────────────
        truncated = is_truncated(response, token_count, args.max_tokens)
        if truncated:
            issues.append("TRUNCATED")
            stats["truncated"] += 1

        # ── Check 2: Degenerate loop ─────────────────────────────────────────
        degenerate = is_degenerate(response)
        if degenerate:
            issues.append("DEGENERATE_LOOP")
            stats["degenerate"] += 1

        # ── Extract current boxes ────────────────────────────────────────────
        boxes = extract_all_boxed(response)
        has_boxed = len(boxes) > 0

        # ── Check 3: Multi-answer format fix ─────────────────────────────────
        if has_boxed and is_multi_answer(item) and not (truncated or degenerate):
            n = expected_n_answers(item)
            fixed_resp, action = fix_multi_answer(response, n)
            if action.startswith("consolidated"):
                response = fixed_resp
                actions.append(f"multi_fix:{action}")
                stats["multi_fixed"] += 1
                # Refresh boxes after fix
                boxes = extract_all_boxed(response)

        # ── Check 4: LaTeX normalization ─────────────────────────────────────
        if has_boxed and not (truncated or degenerate):
            norm_resp, was_normalized = apply_latex_normalization(response)
            if was_normalized:
                response = norm_resp
                actions.append("latex_normalized")
                stats["latex_normalized"] += 1
                boxes = extract_all_boxed(response)

        # ── Check 5: Word-answer detection ───────────────────────────────────
        current_answer = boxes[-1] if boxes else ""
        if current_answer and is_word_answer(current_answer):
            issues.append(f"WORD_ANSWER:{current_answer[:30]}")
            stats["word_answer"] += 1
            # Don't auto-replace — might be correct ("None" can be a valid answer)
            # Just flag it

        # ── Check 6: Fallback filling ─────────────────────────────────────────
        needs_fallback = (
            not has_boxed or  # no \boxed{} at all
            truncated or      # response was cut off
            degenerate        # stuck in loop
        )

        if needs_fallback:
            teacher_ans = teacher_fallbacks.get(item_id, "")
            if teacher_ans:
                # Append \boxed{teacher_ans} to the existing response
                response = append_boxed(response, teacher_ans)
                actions.append(f"fallback:teacher({teacher_ans[:40]})")
                stats["fallback_teacher"] += 1
            else:
                # No teacher answer available — leave as is, will score 0
                actions.append("fallback:none_available")
                stats["fallback_missing"] += 1

        # ── Build final row ───────────────────────────────────────────────────
        final_rows.append({"id": item_id, "response": response})

        if issues or actions:
            stats["items_modified"] += 1
            report_items.append({
                "id": item_id,
                "tokens": token_count,
                "issues": ", ".join(issues),
                "actions": ", ".join(actions),
                "original_answer": (extract_all_boxed(result.get("response", "")) or [""])[-1][:60],
                "final_answer": (extract_all_boxed(response) or [""])[-1][:60],
            })
        else:
            stats["clean"] += 1

    # ── Sanity checks ─────────────────────────────────────────────────────────
    print("\n=== SANITY CHECKS ===")
    assert len(final_rows) == 943, f"Expected 943 rows, got {len(final_rows)}"
    ids = [r["id"] for r in final_rows]
    assert ids == list(range(943)), "ID sequence is wrong"
    empties = sum(1 for r in final_rows if not r["response"].strip())
    final_boxed = sum(1 for r in final_rows if extract_all_boxed(r["response"]))

    print(f"  Total rows:          {len(final_rows)} ✓")
    print(f"  ID sequence 0-942:   ✓")
    print(f"  Empty responses:     {empties}")
    print(f"  Responses with \\boxed{{}}: {final_boxed}/943")

    # ── Report ────────────────────────────────────────────────────────────────
    print("\n=== POST-INFERENCE REPORT ===")
    print(f"  Clean items:         {stats['clean']}")
    print(f"  Items modified:      {stats['items_modified']}")
    print(f"  ├─ Truncated:        {stats['truncated']}")
    print(f"  ├─ Degenerate loops: {stats['degenerate']}")
    print(f"  ├─ Multi-fix:        {stats['multi_fixed']}")
    print(f"  ├─ LaTeX normalized: {stats['latex_normalized']}")
    print(f"  ├─ Word answers:     {stats['word_answer']} (flagged, not replaced)")
    print(f"  ├─ Fallback (teach): {stats['fallback_teacher']}")
    print(f"  └─ Fallback (none):  {stats['fallback_missing']}")

    if report_items:
        print(f"\n=== ITEM-LEVEL CHANGES ({len(report_items)} items) ===")
        for r in report_items:
            print(f"  ID {r['id']:4d} | {r.get('issues',''):<35} | {r.get('actions','')[:60]}")
            if r.get("original_answer") != r.get("final_answer"):
                print(f"         orig_ans: '{r.get('original_answer','')}'")
                print(f"         final_ans: '{r.get('final_answer','')}'")

    if args.dry_run:
        print("\n[DRY RUN] No output written.")
        return

    # ── Write output ──────────────────────────────────────────────────────────
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "response"],
                                quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(final_rows)

    print(f"\n✓ Written: {args.output} ({len(final_rows)} rows)")
    print(f"  Ready for Kaggle submission")


if __name__ == "__main__":
    main()
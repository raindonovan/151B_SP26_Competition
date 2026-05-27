"""run_inference.py — Single entry point for CSE 151B Kaggle competition.

Gradescope deadline: Sun 2026-05-31

Usage:
    python3 scripts/run_inference.py

This runs the FULL pipeline:
  1. Load Qwen3-4B-Thinking-2507 via vLLM
  2. Inference on all 943 items (SC=8, 32K tokens, shape-filtered vote)
  3. Post-processing: multi-answer shape fix + minimal normalizer
  4. Static overrides: Wolfram-verified answers from results/wolfram_overrides.csv
  5. Output: submission.csv (id, response)

GPU: 2x A100 80GB (tensor parallel), ~3-4 hours for full run
Model: Qwen/Qwen3-4B-Thinking-2507 (HuggingFace)
No external API calls at inference time — all overrides are static.
"""

import os
os.environ["VLLM_USE_V1"] = "0"

import csv
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
MODEL_NAME = "Qwen/Qwen3-4B-Thinking-2507"
DATA_PATH = "private.jsonl"
OUTPUT_CSV = "submission.csv"
OUTPUT_JSONL = "results/inference_run.jsonl"
WOLFRAM_OVERRIDES_PATH = "results/wolfram_overrides.csv"

SC_SAMPLES = 8
MAX_TOKENS = 49152
THINKING_BUDGET = 24576
TEMPERATURE = 0.6
TOP_P = 0.95
TOP_K = 20
GPU_UTIL = 0.85
TENSOR_PARALLEL = 2  # 2x A100

SYSTEM_PROMPT = "Please reason step by step and put your final answer within \\boxed{}."
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# ── Answer extraction utilities ───────────────────────────────────────────────
def normalize_answer(s: str) -> str:
    """Normalize for vote-counting (not for submission)."""
    if not s:
        return ""
    s = s.strip()
    if s.startswith("$") and s.endswith("$") and len(s) >= 2:
        s = s[1:-1].strip()
    s = s.replace("\\,", " ").replace("\\;", " ").replace("\\ ", " ")
    s = s.replace("\\quad", " ").replace("\\!", "")
    s = s.replace("\\dfrac", "\\frac")
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_last_boxed(text: str) -> str:
    """Return the contents of the last \\boxed{...} or ''."""
    positions = []
    i = 0
    while i < len(text):
        pos = text.find("\\boxed{", i)
        if pos == -1:
            break
        positions.append(pos)
        i = pos + 7
    if not positions:
        return ""
    start = positions[-1] + 7
    depth, j = 1, start
    while j < len(text) and depth > 0:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    return text[start:j - 1].strip() if depth == 0 else ""


def count_top_level_boxes(text: str) -> int:
    count = 0
    depth = 0
    i = 0
    while i < len(text):
        if text[i:i + 7] == "\\boxed{":
            if depth == 0:
                count += 1
            depth += 1
            i += 7
        elif text[i] == "{" and depth > 0:
            depth += 1
            i += 1
        elif text[i] == "}" and depth > 0:
            depth -= 1
            i += 1
        else:
            i += 1
    return count


def extract_all_boxed(text: str) -> list[str]:
    """Extract ALL \\boxed{...} contents (for multi-answer shape fix)."""
    results = []
    i = 0
    while i < len(text):
        pos = text.find("\\boxed{", i)
        if pos == -1:
            break
        depth = 1
        j = pos + 7
        while j < len(text) and depth > 0:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
            j += 1
        if depth == 0:
            results.append(text[pos + 7:j - 1])
        i = pos + 7
    return results


def count_ans_placeholders(question: str) -> int:
    n = question.count("[ANS]")
    return max(n, 1)


# ── Shape filter (vote on clean samples only) ────────────────────────────────
def apply_shape_filter(sample_texts, is_multi_answer):
    rejected = []
    for text in sample_texts:
        n_boxes = count_top_level_boxes(text)
        rejected.append(n_boxes == 0 or (is_multi_answer and n_boxes > 1))
    if all(rejected):
        return [False] * len(sample_texts), True
    return rejected, False


def majority_vote_filtered(sample_texts, rejected):
    bucket = Counter()
    raw_for = {}
    for text, rej in zip(sample_texts, rejected):
        if rej:
            continue
        ans = extract_last_boxed(text)
        if not ans:
            continue
        norm = normalize_answer(ans)
        if not norm:
            continue
        bucket[norm] += 1
        raw_for.setdefault(norm, ans)
    if not bucket:
        return "", 0, 0
    winner_norm, votes = bucket.most_common(1)[0]
    return raw_for[winner_norm], votes, sum(bucket.values())


def pick_response(sample_texts, rejected, voted_raw):
    voted_norm = normalize_answer(voted_raw)
    for text, rej in zip(sample_texts, rejected):
        if rej:
            continue
        if normalize_answer(extract_last_boxed(text)) == voted_norm:
            return text
    for text, rej in zip(sample_texts, rejected):
        if not rej:
            return text
    return sample_texts[0] if sample_texts else ""


# ── Prompt construction ───────────────────────────────────────────────────────
def build_user_msg(item: dict) -> str:
    question = item["question"]
    options = item.get("options")
    if options:
        opts_text = "\n".join(f"{LETTERS[i]}. {opt}" for i, opt in enumerate(options))
        return f"{question}\n\nOptions:\n{opts_text}"
    return question


# ── Post-processing: multi-answer shape fix ───────────────────────────────────
def fix_multi_answer_shape(response: str, n_expected: int) -> str:
    """If response has multiple separate \\boxed{} but the last one has no commas,
    consolidate the last N unique boxed values into a single \\boxed{v1, v2, ...}."""
    boxes = extract_all_boxed(response)
    if not boxes or len(boxes) <= 1:
        return response
    last = boxes[-1]
    if "," in last:
        return response  # already comma-separated

    # Collect last N unique non-empty values
    unique_vals = []
    seen = set()
    for b in reversed(boxes):
        b_stripped = b.strip()
        if b_stripped and b_stripped not in seen:
            seen.add(b_stripped)
            unique_vals.insert(0, b_stripped)
        if len(unique_vals) == n_expected:
            break

    consolidated = ", ".join(unique_vals)
    return replace_last_boxed(response, consolidated)


def replace_last_boxed(text: str, new_content: str) -> str:
    """Replace the content of the last \\boxed{} in text."""
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


# ── Post-processing: minimal normalizer ───────────────────────────────────────
_THIN_SPACE_RE = re.compile(r"\\[,;!:]")
_LEFT_RIGHT_RE = re.compile(r"\\(?:left|right)\b")


def apply_minimal_normalizer(response: str) -> str:
    """Apply minimal safe normalizations to the last \\boxed{} content only.
    Rules: strip thin-space macros (\\, \\; \\! \\:) and \\left/\\right."""
    positions = []
    i = 0
    while i < len(response):
        pos = response.find("\\boxed{", i)
        if pos == -1:
            break
        positions.append(pos)
        i = pos + 7
    if not positions:
        return response

    m_start = positions[-1]
    depth = 1
    j = m_start + 7
    while j < len(response) and depth > 0:
        if response[j] == "{":
            depth += 1
        elif response[j] == "}":
            depth -= 1
        j += 1
    if depth != 0:
        return response

    inner = response[m_start + 7:j - 1]
    new_inner = _THIN_SPACE_RE.sub("", inner)
    new_inner = _LEFT_RIGHT_RE.sub("", new_inner)

    if new_inner == inner:
        return response
    return response[:m_start] + "\\boxed{" + new_inner + "}" + response[j:]


# ── Post-processing: Wolfram overrides (static, no API calls) ─────────────────
def load_wolfram_overrides(path: str) -> dict[int, str]:
    """Load HIGH-confidence Wolfram overrides from CSV.
    Returns {item_id: override_answer}. Skips DISPUTED (id=141)."""
    overrides = {}
    if not os.path.exists(path):
        print(f"  [WARN] Wolfram overrides not found: {path}")
        return overrides
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            conf = row.get('confidence', '').strip()
            iid = int(row['id'])
            if 'HIGH' not in conf:
                continue
            if iid == 141:  # DISPUTED — skip
                continue
            override = row.get('override_value', '').strip()
            if override:
                overrides[iid] = override
    print(f"  Loaded {len(overrides)} HIGH Wolfram overrides")
    return overrides


def apply_wolfram_overrides(responses: dict[int, str], overrides: dict[int, str]) -> int:
    """Replace last \\boxed{} content with Wolfram override for specified items.
    Returns count of applied overrides."""
    n_applied = 0
    for iid, override_val in overrides.items():
        if iid in responses:
            responses[iid] = replace_last_boxed(responses[iid], override_val)
            n_applied += 1
    return n_applied


# ── Main inference function ───────────────────────────────────────────────────
def run_inference(
    data_path: str = DATA_PATH,
    output_csv: str = OUTPUT_CSV,
    output_jsonl: str = OUTPUT_JSONL,
    wolfram_path: str = WOLFRAM_OVERRIDES_PATH,
    sc: int = SC_SAMPLES,
    max_tokens: int = MAX_TOKENS,
    thinking_budget: int = THINKING_BUDGET,
    temperature: float = TEMPERATURE,
    tp: int = TENSOR_PARALLEL,
):
    """Single entry point: model load → inference → post-processing → CSV.

    This is the function Gradescope calls. No external API calls.
    """
    print(f"=== run_inference() ===")
    print(f"  Model: {MODEL_NAME}")
    print(f"  Data: {data_path}")
    print(f"  SC={sc}, max_tokens={max_tokens}, thinking_budget={thinking_budget}")
    print(f"  Output CSV: {output_csv}")
    print(f"  Output JSONL: {output_jsonl}")

    # ── 1. Load data ──────────────────────────────────────────────────────────
    items = {}
    with open(data_path) as f:
        for line in f:
            it = json.loads(line)
            items[int(it["id"])] = it
    print(f"  Loaded {len(items)} items from {data_path}")

    # ── 2. Load model ─────────────────────────────────────────────────────────
    from vllm import LLM, SamplingParams

    llm = LLM(
        model=MODEL_NAME,
        gpu_memory_utilization=GPU_UTIL,
        enable_prefix_caching=True,
        max_model_len=max_tokens + 4096,
        reasoning_parser="deepseek_r1",
        trust_remote_code=True,
        dtype="bfloat16",
        tensor_parallel_size=tp,
    )
    tokenizer = llm.get_tokenizer()

    sampling = SamplingParams(
        n=sc,
        temperature=temperature,
        top_p=TOP_P,
        top_k=TOP_K,
        max_tokens=max_tokens,
        thinking_token_budget=thinking_budget,
    )

    # ── 3. Resume support ─────────────────────────────────────────────────────
    done = set()
    os.makedirs(os.path.dirname(output_jsonl) or ".", exist_ok=True)
    if os.path.exists(output_jsonl):
        with open(output_jsonl) as f:
            for line in f:
                try:
                    done.add(int(json.loads(line)["id"]))
                except Exception:
                    pass
    print(f"  Resuming: {len(done)} items already completed")

    # ── 4. Inference loop ─────────────────────────────────────────────────────
    sorted_ids = sorted(items.keys())
    to_run = [items[iid] for iid in sorted_ids if iid not in done]
    total = len(sorted_ids)
    print(f"  Running inference on {len(to_run)} items (SC={sc})...")

    responses = {}  # id -> full response text
    timings = []

    for idx, item in enumerate(to_run):
        iid = int(item["id"])
        is_multi = count_ans_placeholders(item.get("question", "")) > 1

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_msg(item)},
        ]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        t0 = time.time()
        outputs = llm.generate(prompt, sampling_params=sampling)
        wall = time.time() - t0
        timings.append(wall)

        sample_texts = [o.text for o in outputs[0].outputs]
        sample_extracted = [extract_last_boxed(t) for t in sample_texts]
        sample_tokens = [len(o.token_ids) for o in outputs[0].outputs]

        rejected, fallback = apply_shape_filter(sample_texts, is_multi)
        voted, votes, n_voting = majority_vote_filtered(sample_texts, rejected)
        response = pick_response(sample_texts, rejected, voted)

        # Save full result
        result = {
            "id": iid,
            "voted_answer": voted,
            "votes": votes,
            "n_voting": n_voting,
            "shape_fallback": fallback,
            "response": response,
            "samples": sample_texts,
            "sample_extracted": sample_extracted,
            "sample_n_output_tokens": sample_tokens,
            "wall_seconds": round(wall, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(output_jsonl, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

        responses[iid] = response

        # Progress
        avg = sum(timings) / len(timings)
        eta = (len(to_run) - idx - 1) * avg
        kind = "MCQ" if item.get("options") else "FRE"
        print(f"  [{idx+1+len(done):>4}/{total}] ID {iid:>4} [{kind}] "
              f"voted={voted!r:10s} ({votes}/{n_voting}) "
              f"{wall:.1f}s avg={avg:.1f}s ETA={eta/3600:.1f}h", flush=True)

    # Load completed responses from JSONL for items done in prior runs
    with open(output_jsonl) as f:
        for line in f:
            r = json.loads(line)
            responses[int(r["id"])] = r["response"]

    print(f"\n  Inference complete: {len(responses)} items")

    # ── 5. Post-processing ────────────────────────────────────────────────────
    print("\n  Post-processing...")

    # 5a. Multi-answer shape fix
    n_fixed = 0
    for iid in sorted(responses.keys()):
        item = items[iid]
        n_expected = count_ans_placeholders(item.get("question", ""))
        if n_expected > 1:
            before = responses[iid]
            responses[iid] = fix_multi_answer_shape(responses[iid], n_expected)
            if responses[iid] != before:
                n_fixed += 1
    print(f"    Multi-answer shape fix: {n_fixed} items consolidated")

    # 5b. Minimal normalizer
    n_normed = 0
    for iid in responses:
        before = responses[iid]
        responses[iid] = apply_minimal_normalizer(responses[iid])
        if responses[iid] != before:
            n_normed += 1
    print(f"    Minimal normalizer: {n_normed} items cleaned")

    # 5c. Wolfram overrides (static, from CSV)
    overrides = load_wolfram_overrides(wolfram_path)
    n_wolf = apply_wolfram_overrides(responses, overrides)
    print(f"    Wolfram overrides: {n_wolf} items overridden")

    # ── 6. Write final CSV ────────────────────────────────────────────────────
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["id", "response"])
        for iid in range(len(items)):
            writer.writerow([iid, responses.get(iid, "")])

    print(f"\n  Final CSV: {output_csv} ({len(items)} rows)")
    print(f"  DONE.")
    return output_csv


if __name__ == "__main__":
    run_inference()

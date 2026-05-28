"""GenSelect Phase 0: Throughput pilot on TritonAI endpoint.

10 Tier-5 items × 16 samples = 160 API calls.
Uses exact v1-baseline system prompts from scripts/prompts.py.
"""

from openai import OpenAI
import json, time, csv, sys, os

client = OpenAI(
    base_url="https://tritonai-api.ucsd.edu/v1",
    api_key=os.environ.get("TRITONAI_API_KEY", "")  # was hardcoded; rotated 2026-05-28
)

# v1-baseline prompts (verbatim from scripts/prompts.py)
SYS_MCQ = (
    "You are an expert mathematician. "
    "Read the problem and the answer choices below, then select the single best answer. "
    "Output ONLY the letter of your chosen option inside \\boxed{}, e.g. \\boxed{C}."
)
SYS_FREE = (
    "You are an expert mathematician. Solve the problem step-by-step. "
    "Put your final answer inside \\boxed{}. "
    "If the problem has multiple sub-answers, separate them by commas inside a single \\boxed{}, "
    "e.g. \\boxed{3, 7}. "
    "Give numerical answers to at least 4 significant figures, unless the problem specifies a different precision."
)

# Load private items
print("Loading private.jsonl...")
items = {}
with open("private.jsonl") as f:
    for line in f:
        item = json.loads(line)
        items[item["id"]] = item
print(f"  {len(items)} items loaded")

# Load Tier 5 items from answer sheet
print("Loading Tier 5 items from unified_answer_sheet.csv...")
tier5_ids = []
with open("results/unified_answer_sheet.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get("tier") == "5":
            tier5_ids.append(row["item_id"])
print(f"  {len(tier5_ids)} Tier 5 items found")

pilot_ids = tier5_ids[:10]
print(f"  Pilot: {pilot_ids}\n")

results = []
timings = []
errors = []

for item_id in pilot_ids:
    item = items[int(item_id)]
    question = item["question"]
    is_mcq = bool(item.get("options"))

    if is_mcq:
        system = SYS_MCQ
        opts_text = "\n".join(item["options"])
        user = f"{question}\n\nOptions:\n{opts_text}"
    else:
        system = SYS_FREE
        user = question

    print(f"Item {item_id} ({'MCQ' if is_mcq else 'free'}):")

    for sc in range(16):
        t0 = time.time()
        try:
            response = client.chat.completions.create(
                model="api-test-qwen-3-4b",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=32768,
                temperature=0.6,
                top_p=0.95,
            )
            elapsed = time.time() - t0

            content = response.choices[0].message.content or ""
            reasoning = ""
            psf = getattr(response.choices[0].message, "provider_specific_fields", None)
            if psf:
                reasoning = psf.get("reasoning_content", "")

            usage = response.usage
            comp_tokens = usage.completion_tokens if usage else 0
            prompt_tokens = usage.prompt_tokens if usage else 0

            result = {
                "item_id": item_id,
                "sc_index": sc,
                "content": content,
                "reasoning_content": reasoning,
                "completion_tokens": comp_tokens,
                "prompt_tokens": prompt_tokens,
                "elapsed_sec": round(elapsed, 2),
            }
            results.append(result)
            timings.append(elapsed)

            reasoning_preview = reasoning[:60].replace("\n", " ") if reasoning else "(none)"
            print(f"  sc={sc:02d}: {elapsed:.1f}s  {comp_tokens} tok  reasoning={repr(reasoning_preview)}")
            sys.stdout.flush()

        except Exception as e:
            elapsed = time.time() - t0
            print(f"  sc={sc:02d}: ERROR after {elapsed:.1f}s — {e}")
            errors.append({"item_id": item_id, "sc_index": sc, "error": str(e)})
            timings.append(-1)
            sys.stdout.flush()

# Save results
with open("results/genselect_pilot.jsonl", "w") as f:
    for r in results:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# Report
valid = [t for t in timings if t > 0]
total = len(timings)
succeeded = len(valid)
failed = total - succeeded

print(f"\n{'='*60}")
print(f"=>>> PILOT RESULTS <<<=")
print(f"{'='*60}")
print(f"Total calls:   {total}")
print(f"Successful:    {succeeded}")
print(f"Failed:        {failed}")
if valid:
    avg = sum(valid) / len(valid)
    print(f"Avg time:      {avg:.1f}s")
    print(f"Min time:      {min(valid):.1f}s")
    print(f"Max time:      {max(valid):.1f}s")
    print(f"Total elapsed: {sum(valid)/60:.1f} min")
    print(f"\nEstimated full run (943 items × 16):")
    print(f"  Serial:       {943*16*avg/3600:.1f}h")
    print(f"  4x concurrent:{943*16*avg/3600/4:.1f}h")
    print(f"  8x concurrent:{943*16*avg/3600/8:.1f}h")
    print(f"\nEstimated Tier4+5 only (~252 items × 16):")
    print(f"  Serial:       {252*16*avg/3600:.1f}h")
    print(f"  4x concurrent:{252*16*avg/3600/4:.1f}h")
    print(f"  8x concurrent:{252*16*avg/3600/8:.1f}h")
if errors:
    print(f"\nErrors ({len(errors)}):")
    for e in errors:
        print(f"  item={e['item_id']} sc={e['sc_index']}: {e['error']}")

# Show first 2 successful responses for reasoning_content check
print(f"\n--- First 2 successful responses (reasoning_content check) ---")
for r in results[:2]:
    print(f"\nitem_id={r['item_id']} sc={r['sc_index']}")
    print(f"  content[:200]:   {repr(r['content'][:200])}")
    rc = r.get('reasoning_content', '')
    print(f"  reasoning[:200]: {repr(rc[:200]) if rc else '(EMPTY — provider_specific_fields not present)'}")

print(f"\nSaved {len(results)} results to results/genselect_pilot.jsonl")

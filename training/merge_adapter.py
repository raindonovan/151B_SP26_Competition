"""
Merge a LoRA adapter into the base model and save as a BF16 full checkpoint.
Output is a directory loadable by vLLM's standard --model flag.

Uses HuggingFace + PEFT directly to avoid Unsloth's 4-bit-merge issues.
Loads base in BF16 (not 4-bit) so merge produces a real full checkpoint.
"""
import argparse
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--adapter", type=str, required=True)
parser.add_argument("--output", type=str, required=True)
parser.add_argument("--base-model", type=str, default="Qwen/Qwen3-4B-Thinking-2507",
                    help="Base model — use the official Qwen path, not unsloth's 4-bit version")
args = parser.parse_args()

print(f"[{time.strftime('%H:%M:%S')}] === MERGE_ADAPTER (HF/PEFT path) ===")
print(f"  Adapter:    {args.adapter}")
print(f"  Output:     {args.output}")
print(f"  Base model: {args.base_model}")

print(f"\n[{time.strftime('%H:%M:%S')}] Importing transformers + peft...")
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

print(f"[{time.strftime('%H:%M:%S')}] Loading base model {args.base_model} in BF16 (~30-60 sec)...")
base = AutoModelForCausalLM.from_pretrained(
    args.base_model,
    torch_dtype=torch.bfloat16,
    device_map="cuda",
)
tokenizer = AutoTokenizer.from_pretrained(args.base_model)
print(f"[{time.strftime('%H:%M:%S')}] Base loaded. {sum(p.numel() for p in base.parameters())/1e9:.2f}B params")

print(f"[{time.strftime('%H:%M:%S')}] Loading adapter from {args.adapter}...")
peft_model = PeftModel.from_pretrained(base, args.adapter)
print(f"[{time.strftime('%H:%M:%S')}] Adapter loaded.")

print(f"[{time.strftime('%H:%M:%S')}] Merging adapter into base (merge_and_unload)...")
merged = peft_model.merge_and_unload()
print(f"[{time.strftime('%H:%M:%S')}] Merge complete.")

out_path = Path(args.output)
out_path.mkdir(parents=True, exist_ok=True)
print(f"[{time.strftime('%H:%M:%S')}] Saving merged BF16 to {args.output}...")
merged.save_pretrained(str(out_path), safe_serialization=True)
tokenizer.save_pretrained(str(out_path))
print(f"[{time.strftime('%H:%M:%S')}] Saved.")

print(f"\n[{time.strftime('%H:%M:%S')}] === DONE ===")
total_size = sum(f.stat().st_size for f in out_path.rglob("*") if f.is_file())
print(f"  Total size: {total_size/1e9:.2f} GB (expect ~8 GB for proper BF16 merge)")
print(f"  Files:")
for f in sorted(out_path.iterdir()):
    if f.is_file():
        print(f"    {f.name}: {f.stat().st_size/1e6:.1f} MB")

# Sanity: should NOT have adapter_config.json or adapter_model.safetensors
adapter_cfg = out_path / "adapter_config.json"
adapter_weights = out_path / "adapter_model.safetensors"
if adapter_cfg.exists() or adapter_weights.exists():
    print(f"\n  WARNING: output still contains adapter files — merge may have failed silently")
else:
    print(f"\n  OK: no adapter files in output (proper merge)")

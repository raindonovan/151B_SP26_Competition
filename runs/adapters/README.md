# Adapter Runs

All SFT / LoRA training runs. Naming: `sft_v<N>` or `sft_v<N>_<descriptor>`.

Key question across all adapter runs: **did training improve HELD-OUT performance, or just memorize training items?** (See sft_v5/findings.md — memorization ≠ generalization.)

Adapter run history: v1 (3-arm catastrophe, not submitted) → v3 (0.452) → v4 (0.597) → v5 (~0.646 break-even). No v2 (skipped), no v6. 'v7' is the PLANNED next adapter (naming skips v6 — investigate why).

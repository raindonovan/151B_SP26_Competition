# Inference Runs

Model inference runs (no training). Naming: `run<NN>_<descriptor>` or descriptive.

**Key fact**: run14b (SC=8, 32K tokens) = 0.646 is our BEST inference. The only inference lever that moved the needle was 16K→32K tokens (+2.5pp from run09 0.614). Everything after — prompts, normalizers, reformat, shape filters — gave ~0 on pure inference.

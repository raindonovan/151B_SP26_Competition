"""Variant registry for the V0-V4 prompt-engineering ablation.

Each variant is defined as the DIFF from the previous variant. To get the
full config for a variant, call resolve_variant(name) — it walks the ordered
list and merges left-to-right.

Usage:
    from scripts.variants import resolve_variant
    config = resolve_variant("V3_shape_filter")
    # config has all keys: prompt_version, max_new_tokens, presence_penalty,
    # n_samples, temperature, temperature_ladder, shape_filter, ...
"""

# Variant deltas. Each dict contains ONLY the keys that change vs the
# previous variant in VARIANT_ORDER.
VARIANTS = {
    "V0_baseline": dict(
        prompt_version="v1-baseline",
        max_new_tokens=32768,
        presence_penalty=1.0,
        n_samples=8,
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        min_p=0.0,
        repetition_penalty=1.0,
        temperature_ladder=None,  # single-temp; ladder overrides when set
        shape_filter=False,
    ),
    "V1_counting_top": dict(
        prompt_version="v2-counting-top",
    ),
    "V2_counting_bookend": dict(
        prompt_version="v2-counting-bookend",
    ),
    "V3_shape_filter": dict(
        shape_filter=True,
    ),
    "V4_temp_diversification": dict(
        # SC runner reads temperature_ladder when not None; falls back to
        # `temperature` for single-temp runs (V0-V3).
        temperature_ladder=[0.5, 0.7, 0.9, 1.1],
    ),
}

# Order matters: each variant is the delta on top of the previous.
VARIANT_ORDER = [
    "V0_baseline",
    "V1_counting_top",
    "V2_counting_bookend",
    "V3_shape_filter",
    "V4_temp_diversification",
]


def resolve_variant(name: str) -> dict:
    """Merge deltas left-to-right up through `name`. Returns full config."""
    if name not in VARIANT_ORDER:
        raise KeyError(f"Unknown variant: {name!r}. Known: {VARIANT_ORDER}")
    config = {}
    for v in VARIANT_ORDER:
        config.update(VARIANTS[v])
        if v == name:
            break
    return config


def all_variants() -> list[str]:
    """Return the full ordered list of variant names."""
    return list(VARIANT_ORDER)

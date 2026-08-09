"""Deterministic base templates used before any vision-derived parameter patch.

A reference analyzer is not allowed to invent a complete asset from scratch. It starts
from a known factory template and may propose bounded, evidence-backed parameter edits.
"""

from __future__ import annotations

import copy
from typing import Any

from compiler.spec import normalize_spec


_FACTORY_BASE_SPECS: dict[str, dict[str, Any]] = {
    "cliff_kitchen": {
        "version": 1,
        "factory": "cliff_kitchen",
        "seed": 0,
        "parameters": {
            "width": 7.2,
            "depth": 4.8,
            "wall_height": 2.7,
            "roof_pitch_deg": 31.0,
            "eave_overhang": 0.72,
            "platform_height": 0.9,
            "cliff_embed": 0.35,
            "stone_step_count": 9,
            "post_count_x": 4,
            "wood_age": 0.62,
            "tile_damage": 0.16,
            "moss": 0.18,
        },
        "style": {
            "palette": "paper_ink_old_wood",
            "roof": "dark_clay_tile",
            "wood": "aged_dark_timber",
        },
    },
    "cliff_ground_floor": {
        "version": 1,
        "factory": "cliff_ground_floor",
        "seed": 0,
        "parameters": {
            "width": 20.0,
            "depth": 5.2,
            "wall_height": 2.9,
            "platform_height": 0.85,
            "cliff_embed": 0.80,
            "stone_step_count": 12,
            "wood_age": 0.72,
            "moss": 0.20,
            "rooms": [
                {
                    "id": "gate",
                    "template": "sect_gate_room",
                    "width": 4.0,
                    "lantern_count": 3,
                    "occupancy": 2,
                    "clutter": 0.42,
                },
                {
                    "id": "infirmary",
                    "template": "infirmary_rest_room",
                    "width": 4.4,
                    "lantern_count": 1,
                    "occupancy": 2,
                    "clutter": 0.48,
                },
                {
                    "id": "kitchen",
                    "template": "kitchen_room",
                    "width": 5.0,
                    "lantern_count": 1,
                    "occupancy": 3,
                    "clutter": 0.72,
                },
                {
                    "id": "dining",
                    "template": "dining_room",
                    "width": 5.6,
                    "lantern_count": 2,
                    "occupancy": 6,
                    "clutter": 0.68,
                },
            ],
        },
        "style": {
            "palette": "paper_ink_old_wood",
            "roof": "dark_clay_tile",
            "wood": "aged_dark_timber",
        },
    },
}


def supported_templates() -> tuple[str, ...]:
    return tuple(sorted(_FACTORY_BASE_SPECS))


def make_base_spec(factory: str, *, seed: int = 0) -> dict[str, Any]:
    try:
        spec = copy.deepcopy(_FACTORY_BASE_SPECS[factory])
    except KeyError as exc:
        raise ValueError(f"No base template registered for factory {factory!r}") from exc
    spec["seed"] = seed
    return normalize_spec(spec)

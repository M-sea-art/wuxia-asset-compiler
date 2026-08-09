"""Pure-Python scene-spec validation and normalization.

This module intentionally has no Blender dependency. Vision/LLM output should pass
through this contract before any DCC tool is invoked.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


ROOT_KEYS = {"version", "factory", "seed", "parameters", "style"}
SUPPORTED_FACTORIES = {"cliff_kitchen"}

REQUIRED_PARAMETERS = {
    "width",
    "depth",
    "wall_height",
    "roof_pitch_deg",
    "eave_overhang",
    "platform_height",
    "cliff_embed",
    "stone_step_count",
}

OPTIONAL_DEFAULTS = {
    "post_count_x": 4,
    "wood_age": 0.5,
    "tile_damage": 0.0,
    "moss": 0.0,
}

PARAM_RANGES = {
    "width": (3.0, 20.0),
    "depth": (2.5, 14.0),
    "wall_height": (2.0, 6.0),
    "roof_pitch_deg": (15.0, 55.0),
    "eave_overhang": (0.2, 2.0),
    "platform_height": (0.2, 4.0),
    "cliff_embed": (0.0, 1.0),
    "stone_step_count": (3, 30),
    "post_count_x": (2, 12),
    "wood_age": (0.0, 1.0),
    "tile_damage": (0.0, 1.0),
    "moss": (0.0, 1.0),
}

INTEGER_PARAMETERS = {"stone_step_count", "post_count_x"}

STYLE_KEYS = {"palette", "roof", "wood"}
STYLE_ALLOWED = {
    "palette": {"paper_ink_old_wood"},
    "roof": {"dark_clay_tile"},
    "wood": {"aged_dark_timber"},
}


class SpecValidationError(ValueError):
    """Raised when a scene spec violates the compiler contract."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid scene spec:\n- " + "\n- ".join(errors))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_spec(spec: Any) -> dict[str, Any]:
    errors: list[str] = []

    if not isinstance(spec, dict):
        raise SpecValidationError(["root must be an object"])

    unknown_root = set(spec) - ROOT_KEYS
    missing_root = ROOT_KEYS - set(spec)
    if unknown_root:
        errors.append(f"unknown root keys: {sorted(unknown_root)}")
    if missing_root:
        errors.append(f"missing root keys: {sorted(missing_root)}")

    if spec.get("version") != 1:
        errors.append("version must be exactly 1")

    factory = spec.get("factory")
    if factory not in SUPPORTED_FACTORIES:
        errors.append(f"unsupported factory: {factory!r}")

    seed = spec.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= 2147483647:
        errors.append("seed must be an integer in [0, 2147483647]")

    parameters = spec.get("parameters")
    if not isinstance(parameters, dict):
        errors.append("parameters must be an object")
    else:
        allowed_parameters = set(PARAM_RANGES)
        unknown_parameters = set(parameters) - allowed_parameters
        missing_parameters = REQUIRED_PARAMETERS - set(parameters)
        if unknown_parameters:
            errors.append(f"unknown parameters: {sorted(unknown_parameters)}")
        if missing_parameters:
            errors.append(f"missing parameters: {sorted(missing_parameters)}")

        for key, value in parameters.items():
            if key not in PARAM_RANGES:
                continue
            if key in INTEGER_PARAMETERS:
                if not isinstance(value, int) or isinstance(value, bool):
                    errors.append(f"{key} must be an integer")
                    continue
            elif not _is_number(value):
                errors.append(f"{key} must be a number")
                continue

            lo, hi = PARAM_RANGES[key]
            if not lo <= value <= hi:
                errors.append(f"{key}={value!r} is outside [{lo}, {hi}]")

    style = spec.get("style")
    if not isinstance(style, dict):
        errors.append("style must be an object")
    else:
        unknown_style = set(style) - STYLE_KEYS
        missing_style = STYLE_KEYS - set(style)
        if unknown_style:
            errors.append(f"unknown style keys: {sorted(unknown_style)}")
        if missing_style:
            errors.append(f"missing style keys: {sorted(missing_style)}")
        for key, allowed in STYLE_ALLOWED.items():
            value = style.get(key)
            if value is not None and value not in allowed:
                errors.append(f"unsupported style {key}={value!r}")

    if errors:
        raise SpecValidationError(errors)
    return spec


def normalize_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Validate then return a copy with deterministic optional defaults filled."""
    validate_spec(spec)
    normalized = copy.deepcopy(spec)
    for key, value in OPTIONAL_DEFAULTS.items():
        normalized["parameters"].setdefault(key, value)
    return normalized


def load_spec(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return normalize_spec(data)

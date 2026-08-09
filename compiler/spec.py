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
SUPPORTED_FACTORIES = {"cliff_kitchen", "cliff_ground_floor"}

# Backward-compatible public constants for the original cliff_kitchen contract.
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
    "width": (3.0, 30.0),
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

GROUND_FLOOR_NUMERIC_PARAMETERS = {
    "width",
    "depth",
    "wall_height",
    "platform_height",
    "cliff_embed",
    "stone_step_count",
    "wood_age",
    "moss",
}
GROUND_FLOOR_REQUIRED_PARAMETERS = {
    "width",
    "depth",
    "wall_height",
    "platform_height",
    "cliff_embed",
    "stone_step_count",
    "rooms",
}
GROUND_FLOOR_ALLOWED_PARAMETERS = GROUND_FLOOR_NUMERIC_PARAMETERS | {"rooms"}
GROUND_FLOOR_OPTIONAL_DEFAULTS = {
    "wood_age": 0.68,
    "moss": 0.22,
}

ROOM_KEYS = {"id", "template", "width", "lantern_count", "occupancy", "clutter"}
ROOM_TEMPLATES = {
    "sect_gate_room",
    "infirmary_rest_room",
    "kitchen_room",
    "dining_room",
}
ROOM_REQUIRED_KEYS = {"id", "template", "width"}
ROOM_NUMERIC_RANGES = {
    "width": (2.5, 8.0),
    "lantern_count": (0, 6),
    "occupancy": (0, 12),
    "clutter": (0.0, 1.0),
}
ROOM_INTEGER_KEYS = {"lantern_count", "occupancy"}
ROOM_DEFAULTS = {
    "lantern_count": 1,
    "occupancy": 0,
    "clutter": 0.5,
}

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


def _validate_numeric_parameter(key: str, value: Any, errors: list[str]) -> None:
    if key in INTEGER_PARAMETERS:
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{key} must be an integer")
            return
    elif not _is_number(value):
        errors.append(f"{key} must be a number")
        return

    lo, hi = PARAM_RANGES[key]
    if not lo <= value <= hi:
        errors.append(f"{key}={value!r} is outside [{lo}, {hi}]")


def _validate_rooms(rooms: Any, overall_width: Any, errors: list[str]) -> None:
    if not isinstance(rooms, list) or not rooms:
        errors.append("rooms must be a non-empty array")
        return
    if not 2 <= len(rooms) <= 8:
        errors.append("rooms must contain between 2 and 8 room definitions")

    seen_ids: set[str] = set()
    total_width = 0.0
    for index, room in enumerate(rooms):
        prefix = f"rooms[{index}]"
        if not isinstance(room, dict):
            errors.append(f"{prefix} must be an object")
            continue
        unknown = set(room) - ROOM_KEYS
        missing = ROOM_REQUIRED_KEYS - set(room)
        if unknown:
            errors.append(f"{prefix} unknown keys: {sorted(unknown)}")
        if missing:
            errors.append(f"{prefix} missing keys: {sorted(missing)}")

        room_id = room.get("id")
        if not isinstance(room_id, str) or not room_id.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
        elif room_id in seen_ids:
            errors.append(f"duplicate room id: {room_id!r}")
        else:
            seen_ids.add(room_id)

        template = room.get("template")
        if template not in ROOM_TEMPLATES:
            errors.append(f"{prefix}.template unsupported: {template!r}")

        for key, (lo, hi) in ROOM_NUMERIC_RANGES.items():
            if key not in room:
                continue
            value = room[key]
            if key in ROOM_INTEGER_KEYS:
                if not isinstance(value, int) or isinstance(value, bool):
                    errors.append(f"{prefix}.{key} must be an integer")
                    continue
            elif not _is_number(value):
                errors.append(f"{prefix}.{key} must be a number")
                continue
            if not lo <= value <= hi:
                errors.append(f"{prefix}.{key}={value!r} is outside [{lo}, {hi}]")

        if _is_number(room.get("width")):
            total_width += float(room["width"])

    if _is_number(overall_width):
        slack = float(overall_width) - total_width
        if slack < -0.001:
            errors.append(
                f"room widths total {total_width:.2f}m, exceeding overall width {float(overall_width):.2f}m"
            )
        elif slack > max(3.0, float(overall_width) * 0.20):
            errors.append(
                f"room widths leave {slack:.2f}m unused; compact ground-floor layout allows at most 20% slack"
            )


def _validate_parameters(factory: str, parameters: Any, errors: list[str]) -> None:
    if not isinstance(parameters, dict):
        errors.append("parameters must be an object")
        return

    if factory == "cliff_ground_floor":
        allowed_parameters = GROUND_FLOOR_ALLOWED_PARAMETERS
        required_parameters = GROUND_FLOOR_REQUIRED_PARAMETERS
        numeric_parameters = GROUND_FLOOR_NUMERIC_PARAMETERS
    else:
        allowed_parameters = set(PARAM_RANGES)
        required_parameters = REQUIRED_PARAMETERS
        numeric_parameters = set(PARAM_RANGES)

    unknown_parameters = set(parameters) - allowed_parameters
    missing_parameters = required_parameters - set(parameters)
    if unknown_parameters:
        errors.append(f"unknown parameters: {sorted(unknown_parameters)}")
    if missing_parameters:
        errors.append(f"missing parameters: {sorted(missing_parameters)}")

    for key, value in parameters.items():
        if key not in numeric_parameters:
            continue
        _validate_numeric_parameter(key, value, errors)

    if factory == "cliff_ground_floor":
        _validate_rooms(parameters.get("rooms"), parameters.get("width"), errors)


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

    _validate_parameters(factory, spec.get("parameters"), errors)

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

    if normalized["factory"] == "cliff_ground_floor":
        for key, value in GROUND_FLOOR_OPTIONAL_DEFAULTS.items():
            normalized["parameters"].setdefault(key, value)
        for room in normalized["parameters"]["rooms"]:
            for key, value in ROOM_DEFAULTS.items():
                room.setdefault(key, value)
    else:
        for key, value in OPTIONAL_DEFAULTS.items():
            normalized["parameters"].setdefault(key, value)
    return normalized


def load_spec(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return normalize_spec(data)

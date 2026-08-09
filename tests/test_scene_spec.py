"""Zero-dependency smoke tests for the executable scene-spec contract."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from compiler.spec import (  # noqa: E402
    GROUND_FLOOR_REQUIRED_PARAMETERS,
    OPTIONAL_DEFAULTS,
    PARAM_RANGES,
    REQUIRED_PARAMETERS,
    ROOM_TEMPLATES,
    SUPPORTED_FACTORIES,
    SpecValidationError,
    load_spec,
    validate_spec,
)

KITCHEN_SPEC = ROOT / "examples" / "cliff_kitchen.scene_spec.json"
GROUND_SPEC = ROOT / "examples" / "cliff_ground_floor.scene_spec.json"
SCHEMA = ROOT / "schema" / "scene_spec.schema.json"


def test_kitchen_example_and_defaults() -> None:
    data = load_spec(KITCHEN_SPEC)
    assert data["version"] == 1
    assert data["factory"] == "cliff_kitchen"
    assert isinstance(data["seed"], int) and data["seed"] >= 0
    raw = json.loads(KITCHEN_SPEC.read_text(encoding="utf-8"))
    for key, default in OPTIONAL_DEFAULTS.items():
        assert key in data["parameters"]
        if key not in raw["parameters"]:
            assert data["parameters"][key] == default


def test_ground_floor_example_and_room_defaults() -> None:
    data = load_spec(GROUND_SPEC)
    assert data["factory"] == "cliff_ground_floor"
    rooms = data["parameters"]["rooms"]
    assert [room["template"] for room in rooms] == [
        "sect_gate_room",
        "infirmary_rest_room",
        "kitchen_room",
        "dining_room",
    ]
    assert sum(room["width"] for room in rooms) == 19.0
    assert all("lantern_count" in room for room in rooms)
    assert all("occupancy" in room for room in rooms)
    assert all("clutter" in room for room in rooms)


def test_invalid_parameter_rejected() -> None:
    data = load_spec(KITCHEN_SPEC)
    broken = copy.deepcopy(data)
    broken["parameters"]["width"] = 999.0
    try:
        validate_spec(broken)
    except SpecValidationError as exc:
        assert any("width" in error for error in exc.errors)
    else:
        raise AssertionError("invalid width should have been rejected")


def test_unknown_parameter_rejected() -> None:
    data = load_spec(KITCHEN_SPEC)
    broken = copy.deepcopy(data)
    broken["parameters"]["agent_invented_magic"] = 1
    try:
        validate_spec(broken)
    except SpecValidationError as exc:
        assert any("unknown parameters" in error for error in exc.errors)
    else:
        raise AssertionError("unknown parameters should have been rejected")


def test_unknown_room_template_rejected() -> None:
    data = load_spec(GROUND_SPEC)
    broken = copy.deepcopy(data)
    broken["parameters"]["rooms"][2]["template"] = "hallucinated_room"
    try:
        validate_spec(broken)
    except SpecValidationError as exc:
        assert any("template unsupported" in error for error in exc.errors)
    else:
        raise AssertionError("unknown room template should have been rejected")


def test_room_width_overflow_rejected() -> None:
    data = load_spec(GROUND_SPEC)
    broken = copy.deepcopy(data)
    broken["parameters"]["width"] = 18.0
    try:
        validate_spec(broken)
    except SpecValidationError as exc:
        assert any("exceeding overall width" in error for error in exc.errors)
    else:
        raise AssertionError("room width overflow should have been rejected")


def test_schema_and_runtime_contract_do_not_drift() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert set(schema["properties"]["factory"]["enum"]) == SUPPORTED_FACTORIES

    kitchen = schema["$defs"]["cliffKitchenParameters"]
    assert set(kitchen["required"]) == REQUIRED_PARAMETERS
    assert set(kitchen["properties"]) == set(PARAM_RANGES)
    for key, (lo, hi) in PARAM_RANGES.items():
        rule = kitchen["properties"][key]
        assert rule["minimum"] == lo
        assert rule["maximum"] == hi

    ground = schema["$defs"]["cliffGroundFloorParameters"]
    assert set(ground["required"]) == GROUND_FLOOR_REQUIRED_PARAMETERS
    room_enum = set(schema["$defs"]["room"]["properties"]["template"]["enum"])
    assert room_enum == ROOM_TEMPLATES


def main() -> None:
    test_kitchen_example_and_defaults()
    test_ground_floor_example_and_room_defaults()
    test_invalid_parameter_rejected()
    test_unknown_parameter_rejected()
    test_unknown_room_template_rejected()
    test_room_width_overflow_rejected()
    test_schema_and_runtime_contract_do_not_drift()
    print("scene_spec contract tests: PASS")


if __name__ == "__main__":
    main()

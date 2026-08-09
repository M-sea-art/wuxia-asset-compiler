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
    OPTIONAL_DEFAULTS,
    PARAM_RANGES,
    REQUIRED_PARAMETERS,
    SUPPORTED_FACTORIES,
    SpecValidationError,
    load_spec,
    validate_spec,
)

SPEC = ROOT / "examples" / "cliff_kitchen.scene_spec.json"
SCHEMA = ROOT / "schema" / "scene_spec.schema.json"


def test_example_and_defaults() -> None:
    data = load_spec(SPEC)
    assert data["version"] == 1
    assert data["factory"] == "cliff_kitchen"
    assert isinstance(data["seed"], int) and data["seed"] >= 0
    for key, default in OPTIONAL_DEFAULTS.items():
        assert key in data["parameters"]
        if key not in json.loads(SPEC.read_text(encoding="utf-8"))["parameters"]:
            assert data["parameters"][key] == default


def test_invalid_parameter_rejected() -> None:
    data = load_spec(SPEC)
    broken = copy.deepcopy(data)
    broken["parameters"]["width"] = 999.0
    try:
        validate_spec(broken)
    except SpecValidationError as exc:
        assert any("width" in error for error in exc.errors)
    else:
        raise AssertionError("invalid width should have been rejected")


def test_unknown_parameter_rejected() -> None:
    data = load_spec(SPEC)
    broken = copy.deepcopy(data)
    broken["parameters"]["agent_invented_magic"] = 1
    try:
        validate_spec(broken)
    except SpecValidationError as exc:
        assert any("unknown parameters" in error for error in exc.errors)
    else:
        raise AssertionError("unknown parameters should have been rejected")


def test_schema_and_runtime_contract_do_not_drift() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    properties = schema["properties"]
    parameter_schema = properties["parameters"]

    assert set(properties["factory"]["enum"]) == SUPPORTED_FACTORIES
    assert set(parameter_schema["required"]) == REQUIRED_PARAMETERS
    assert set(parameter_schema["properties"]) == set(PARAM_RANGES)

    for key, (lo, hi) in PARAM_RANGES.items():
        rule = parameter_schema["properties"][key]
        assert rule["minimum"] == lo
        assert rule["maximum"] == hi


def main() -> None:
    test_example_and_defaults()
    test_invalid_parameter_rejected()
    test_unknown_parameter_rejected()
    test_schema_and_runtime_contract_do_not_drift()
    print("scene_spec contract tests: PASS")


if __name__ == "__main__":
    main()

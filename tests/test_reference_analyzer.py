"""Zero-dependency tests for VLM reference-analysis resolution."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analyzer.reference import (  # noqa: E402
    ReferenceAnalysisError,
    resolve_reference_analysis,
    validate_reference_analysis,
)
from compiler.spec import normalize_spec  # noqa: E402
from compiler.templates import make_base_spec, supported_templates  # noqa: E402

KITCHEN_FIXTURE = ROOT / "examples" / "cliff_kitchen.reference_analysis.json"
GROUND_FLOOR_FIXTURE = ROOT / "examples" / "cliff_ground_floor.reference_analysis.json"
SCHEMA = ROOT / "schema" / "reference_analysis.schema.json"


def load_fixture(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_fixtures_validate() -> None:
    validate_reference_analysis(load_fixture(KITCHEN_FIXTURE))
    validate_reference_analysis(load_fixture(GROUND_FLOOR_FIXTURE))


def test_kitchen_resolution_accepts_confident_estimates_and_keeps_uncertain_defaults() -> None:
    analysis = load_fixture(KITCHEN_FIXTURE)
    spec, report = resolve_reference_analysis(analysis, seed=19, minimum_confidence=0.35)
    base = make_base_spec("cliff_kitchen", seed=19)

    assert spec["seed"] == 19
    assert spec["parameters"]["width"] == 7.8
    assert spec["parameters"]["depth"] == 4.6
    assert spec["parameters"]["roof_pitch_deg"] == 34.0
    assert spec["parameters"]["stone_step_count"] == 10
    assert spec["parameters"]["wood_age"] == 0.72

    assert spec["parameters"]["moss"] == base["parameters"]["moss"]
    moss_decision = next(item for item in report["decisions"] if item["parameter"] == "moss")
    assert moss_decision["accepted"] is False
    assert "below threshold" in moss_decision["reason"]
    assert report["room_decisions"] == []
    normalize_spec(spec)


def test_ground_floor_reference_resolves_global_and_room_estimates() -> None:
    analysis = load_fixture(GROUND_FLOOR_FIXTURE)
    spec, report = resolve_reference_analysis(analysis, seed=23, minimum_confidence=0.35)

    assert spec["factory"] == "cliff_ground_floor"
    assert spec["seed"] == 23
    assert spec["parameters"]["width"] == 21.2
    assert spec["parameters"]["depth"] == 5.4
    assert spec["parameters"]["wall_height"] == 3.05
    assert spec["parameters"]["wood_age"] == 0.82

    rooms = {room["id"]: room for room in spec["parameters"]["rooms"]}
    assert rooms["gate"]["width"] == 3.8
    assert rooms["gate"]["clutter"] == 0.72
    assert rooms["infirmary"]["width"] == 4.2
    assert rooms["infirmary"]["clutter"] == 0.82
    assert rooms["kitchen"]["width"] == 5.6
    assert rooms["kitchen"]["lantern_count"] == 2
    assert rooms["kitchen"]["clutter"] == 0.96
    assert rooms["dining"]["width"] == 6.0
    assert rooms["dining"]["occupancy"] == 7
    assert rooms["dining"]["clutter"] == 0.92

    assert [room["template"] for room in spec["parameters"]["rooms"]] == [
        "sect_gate_room",
        "infirmary_rest_room",
        "kitchen_room",
        "dining_room",
    ]
    assert len(report["room_decisions"]) == 16
    assert all(item["accepted"] for item in report["room_decisions"])

    roof_decision = next(
        item for item in report["decisions"] if item["parameter"] == "roof_pitch_deg"
    )
    assert roof_decision["accepted"] is False
    assert "does not own parameter" in roof_decision["reason"]
    assert roof_decision["resolved_value"] is None
    normalize_spec(spec)


def test_room_patch_for_unknown_room_is_rejected_without_mutating_template() -> None:
    analysis = load_fixture(GROUND_FLOOR_FIXTURE)
    analysis["room_estimates"].append(
        {
            "room_id": "invented_secret_room",
            "parameter_estimates": {
                "clutter": {
                    "value": 1.0,
                    "confidence": 0.99,
                    "evidence": "Test-only invented room.",
                }
            },
        }
    )
    spec, report = resolve_reference_analysis(analysis)
    assert all(room["id"] != "invented_secret_room" for room in spec["parameters"]["rooms"])
    decision = next(
        item for item in report["room_decisions"] if item["room_id"] == "invented_secret_room"
    )
    assert decision["accepted"] is False
    assert "no room id" in decision["reason"]


def test_out_of_range_estimate_is_rejected_not_clamped() -> None:
    analysis = load_fixture(KITCHEN_FIXTURE)
    analysis["parameter_estimates"]["roof_pitch_deg"] = {
        "value": 82.0,
        "confidence": 0.99,
        "evidence": "Test-only extreme proposal.",
    }
    spec, report = resolve_reference_analysis(analysis)
    base = make_base_spec("cliff_kitchen")

    assert spec["parameters"]["roof_pitch_deg"] == base["parameters"]["roof_pitch_deg"]
    decision = next(
        item for item in report["decisions"] if item["parameter"] == "roof_pitch_deg"
    )
    assert decision["accepted"] is False
    assert "outside" in decision["reason"]


def test_unknown_model_field_is_rejected() -> None:
    analysis = load_fixture(KITCHEN_FIXTURE)
    analysis["creative_blender_script"] = "bpy.ops.mesh.primitive_monkey_add()"
    try:
        validate_reference_analysis(analysis)
    except ReferenceAnalysisError as exc:
        assert any("unknown root keys" in error for error in exc.errors)
    else:
        raise AssertionError("unknown model fields must be rejected")


def test_schema_lists_same_factories_as_templates() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert set(schema["properties"]["factory_candidate"]["enum"]) == set(supported_templates())
    room_properties = schema["properties"]["room_estimates"]["items"]["properties"]
    assert set(room_properties["parameter_estimates"]["properties"]) == {
        "width",
        "lantern_count",
        "occupancy",
        "clutter",
    }


def main() -> None:
    test_fixtures_validate()
    test_kitchen_resolution_accepts_confident_estimates_and_keeps_uncertain_defaults()
    test_ground_floor_reference_resolves_global_and_room_estimates()
    test_room_patch_for_unknown_room_is_rejected_without_mutating_template()
    test_out_of_range_estimate_is_rejected_not_clamped()
    test_unknown_model_field_is_rejected()
    test_schema_lists_same_factories_as_templates()
    print("reference analyzer contract tests: PASS")


if __name__ == "__main__":
    main()

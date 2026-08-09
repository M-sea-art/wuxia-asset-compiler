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
from compiler.templates import make_base_spec  # noqa: E402

FIXTURE = ROOT / "examples" / "cliff_kitchen.reference_analysis.json"
SCHEMA = ROOT / "schema" / "reference_analysis.schema.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_validates() -> None:
    validate_reference_analysis(load_fixture())


def test_resolution_accepts_confident_estimates_and_keeps_uncertain_defaults() -> None:
    analysis = load_fixture()
    spec, report = resolve_reference_analysis(analysis, seed=19, minimum_confidence=0.35)
    base = make_base_spec("cliff_kitchen", seed=19)

    assert spec["seed"] == 19
    assert spec["parameters"]["width"] == 7.8
    assert spec["parameters"]["depth"] == 4.6
    assert spec["parameters"]["roof_pitch_deg"] == 34.0
    assert spec["parameters"]["stone_step_count"] == 10
    assert spec["parameters"]["wood_age"] == 0.72

    # Low-confidence vision estimate must not overwrite deterministic template state.
    assert spec["parameters"]["moss"] == base["parameters"]["moss"]
    moss_decision = next(item for item in report["decisions"] if item["parameter"] == "moss")
    assert moss_decision["accepted"] is False
    assert "below threshold" in moss_decision["reason"]

    # Output remains a valid compiler scene spec after resolution.
    normalize_spec(spec)


def test_out_of_range_estimate_is_rejected_not_clamped() -> None:
    analysis = load_fixture()
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
    analysis = load_fixture()
    analysis["creative_blender_script"] = "bpy.ops.mesh.primitive_monkey_add()"
    try:
        validate_reference_analysis(analysis)
    except ReferenceAnalysisError as exc:
        assert any("unknown root keys" in error for error in exc.errors)
    else:
        raise AssertionError("unknown model fields must be rejected")


def test_schema_lists_the_same_factory() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert schema["properties"]["factory_candidate"]["enum"] == ["cliff_kitchen"]


def main() -> None:
    test_fixture_validates()
    test_resolution_accepts_confident_estimates_and_keeps_uncertain_defaults()
    test_out_of_range_estimate_is_rejected_not_clamped()
    test_unknown_model_field_is_rejected()
    test_schema_lists_the_same_factory()
    print("reference analyzer contract tests: PASS")


if __name__ == "__main__":
    main()

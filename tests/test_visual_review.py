"""Zero-dependency tests for visual QA repair resolution."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analyzer.reference import resolve_reference_analysis  # noqa: E402
from qa.visual_review import (  # noqa: E402
    VisualReviewError,
    apply_visual_review,
    validate_visual_review,
)

ANALYSIS = ROOT / "examples" / "cliff_ground_floor.reference_analysis.json"
REVIEW = ROOT / "examples" / "cliff_ground_floor.visual_review.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def make_reference_spec():
    analysis = load(ANALYSIS)
    spec, _ = resolve_reference_analysis(analysis, seed=23, minimum_confidence=0.35)
    return spec


def test_review_validates() -> None:
    validate_visual_review(load(REVIEW))


def test_visual_review_applies_expressible_patches() -> None:
    spec = make_reference_spec()
    repaired, report = apply_visual_review(spec, load(REVIEW), minimum_confidence=0.40)
    rooms = {room["id"]: room for room in repaired["parameters"]["rooms"]}

    assert repaired["parameters"]["cliff_embed"] == 0.70
    assert repaired["parameters"]["platform_height"] == 0.72
    assert rooms["gate"]["lantern_count"] == 4
    assert rooms["gate"]["clutter"] == 0.82
    assert rooms["infirmary"]["clutter"] == 0.90
    assert rooms["kitchen"]["lantern_count"] == 3
    assert rooms["kitchen"]["clutter"] == 1.0
    assert rooms["dining"]["width"] == 6.2
    assert rooms["dining"]["occupancy"] == 8
    assert rooms["dining"]["clutter"] == 0.98

    assert all(item["accepted"] for item in report["decisions"])
    assert all(item["accepted"] for item in report["room_decisions"])
    assert sum(gap["severity"] >= 0.80 for gap in report["template_gaps"]) >= 4


def test_invalid_layout_patch_is_rejected_and_reverted() -> None:
    spec = make_reference_spec()
    review = load(REVIEW)
    broken = copy.deepcopy(review)
    dining = next(item for item in broken["room_patches"] if item["room_id"] == "dining")
    dining["parameter_patches"]["width"] = {
        "value": 8.0,
        "confidence": 0.99,
        "evidence": "Test-only width that should break the compact layout contract.",
    }
    repaired, report = apply_visual_review(spec, broken)
    dining_room = next(room for room in repaired["parameters"]["rooms"] if room["id"] == "dining")
    assert dining_room["width"] == 6.0
    decision = next(
        item
        for item in report["room_decisions"]
        if item["room_id"] == "dining" and item["parameter"] == "width"
    )
    assert decision["accepted"] is False
    assert "compiler contract rejected patch" in decision["reason"]


def test_review_cannot_invent_new_fields() -> None:
    review = load(REVIEW)
    review["execute_blender_python"] = "bpy.ops.mesh.primitive_monkey_add()"
    try:
        validate_visual_review(review)
    except VisualReviewError as exc:
        assert any("unknown root keys" in error for error in exc.errors)
    else:
        raise AssertionError("visual review must reject unknown execution fields")


def main() -> None:
    test_review_validates()
    test_visual_review_applies_expressible_patches()
    test_invalid_layout_patch_is_rejected_and_reverted()
    test_review_cannot_invent_new_fields()
    print("visual review contract tests: PASS")


if __name__ == "__main__":
    main()

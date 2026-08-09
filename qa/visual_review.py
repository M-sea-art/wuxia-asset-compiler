"""Validate a vision comparison review and apply only bounded compiler patches.

A visual reviewer compares a reference image with a rendered QA view. It may propose
numeric patches that the selected compiler template already knows how to express. Missing
capabilities are reported as template gaps rather than translated into ad-hoc Blender code.
"""

from __future__ import annotations

import copy
from typing import Any

from compiler.spec import (
    INTEGER_PARAMETERS,
    PARAM_RANGES,
    ROOM_INTEGER_KEYS,
    ROOM_NUMERIC_RANGES,
    SpecValidationError,
    normalize_spec,
)
from compiler.templates import supported_templates


ROOT_KEYS = {
    "review_version",
    "factory",
    "scores",
    "parameter_patches",
    "room_patches",
    "template_gaps",
    "summary",
}
SCORE_KEYS = {
    "composition",
    "room_identity",
    "semantic_density",
    "lighting",
    "material_style",
}
ESTIMATE_KEYS = {"value", "confidence", "evidence"}
ROOM_PATCH_KEYS = {"room_id", "parameter_patches"}
TEMPLATE_GAP_KEYS = {"scope", "capability", "severity", "evidence", "recommendation"}


class VisualReviewError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid visual review:\n- " + "\n- ".join(errors))


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _unit_interval(value: Any) -> bool:
    return _number(value) and 0.0 <= float(value) <= 1.0


def _validate_estimate(estimate: Any, path: str, errors: list[str]) -> None:
    if not isinstance(estimate, dict) or set(estimate) != ESTIMATE_KEYS:
        errors.append(f"{path} must contain exactly {sorted(ESTIMATE_KEYS)}")
        return
    if not _number(estimate.get("value")):
        errors.append(f"{path}.value must be a number")
    if not _unit_interval(estimate.get("confidence")):
        errors.append(f"{path}.confidence must be in [0, 1]")
    evidence = estimate.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        errors.append(f"{path}.evidence must be non-empty")


def validate_visual_review(review: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(review, dict):
        raise VisualReviewError(["root must be an object"])

    missing = ROOT_KEYS - set(review)
    unknown = set(review) - ROOT_KEYS
    if missing:
        errors.append(f"missing root keys: {sorted(missing)}")
    if unknown:
        errors.append(f"unknown root keys: {sorted(unknown)}")

    if review.get("review_version") != 1:
        errors.append("review_version must be exactly 1")
    if review.get("factory") not in supported_templates():
        errors.append(f"unsupported factory: {review.get('factory')!r}")

    scores = review.get("scores")
    if not isinstance(scores, dict) or set(scores) != SCORE_KEYS:
        errors.append(f"scores must contain exactly {sorted(SCORE_KEYS)}")
    else:
        for name, value in scores.items():
            if not _unit_interval(value):
                errors.append(f"scores.{name} must be in [0, 1]")

    patches = review.get("parameter_patches")
    if not isinstance(patches, dict):
        errors.append("parameter_patches must be an object")
    else:
        unknown_patches = set(patches) - set(PARAM_RANGES)
        if unknown_patches:
            errors.append(f"unknown parameter patches: {sorted(unknown_patches)}")
        for name, estimate in patches.items():
            if name in PARAM_RANGES:
                _validate_estimate(estimate, f"parameter_patches.{name}", errors)

    room_patches = review.get("room_patches")
    if not isinstance(room_patches, list):
        errors.append("room_patches must be an array")
    else:
        seen_rooms: set[str] = set()
        for index, room_patch in enumerate(room_patches):
            prefix = f"room_patches[{index}]"
            if not isinstance(room_patch, dict) or set(room_patch) != ROOM_PATCH_KEYS:
                errors.append(f"{prefix} must contain exactly {sorted(ROOM_PATCH_KEYS)}")
                continue
            room_id = room_patch.get("room_id")
            if not isinstance(room_id, str) or not room_id.strip():
                errors.append(f"{prefix}.room_id must be a non-empty string")
            elif room_id in seen_rooms:
                errors.append(f"duplicate room patch id: {room_id!r}")
            else:
                seen_rooms.add(room_id)
            room_values = room_patch.get("parameter_patches")
            if not isinstance(room_values, dict):
                errors.append(f"{prefix}.parameter_patches must be an object")
                continue
            unknown_room_values = set(room_values) - set(ROOM_NUMERIC_RANGES)
            if unknown_room_values:
                errors.append(f"{prefix} unknown room patches: {sorted(unknown_room_values)}")
            for name, estimate in room_values.items():
                if name in ROOM_NUMERIC_RANGES:
                    _validate_estimate(estimate, f"{prefix}.parameter_patches.{name}", errors)

    template_gaps = review.get("template_gaps")
    if not isinstance(template_gaps, list):
        errors.append("template_gaps must be an array")
    else:
        for index, gap in enumerate(template_gaps):
            prefix = f"template_gaps[{index}]"
            if not isinstance(gap, dict) or set(gap) != TEMPLATE_GAP_KEYS:
                errors.append(f"{prefix} must contain exactly {sorted(TEMPLATE_GAP_KEYS)}")
                continue
            for key in ("scope", "capability", "evidence", "recommendation"):
                if not isinstance(gap.get(key), str) or not gap[key].strip():
                    errors.append(f"{prefix}.{key} must be non-empty")
            if not _unit_interval(gap.get("severity")):
                errors.append(f"{prefix}.severity must be in [0, 1]")

    if not isinstance(review.get("summary"), str) or not review["summary"].strip():
        errors.append("summary must be a non-empty string")

    if errors:
        raise VisualReviewError(errors)
    return review


def _apply_global_patches(
    spec: dict[str, Any],
    patches: dict[str, Any],
    minimum_confidence: float,
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for name, patch in patches.items():
        proposed = patch["value"]
        confidence = float(patch["confidence"])
        base_value = spec["parameters"].get(name)
        lo, hi = PARAM_RANGES[name]
        accepted = True
        reason = "accepted"

        if name not in spec["parameters"]:
            accepted = False
            reason = f"selected scene spec does not own parameter {name!r}"
        elif confidence < minimum_confidence:
            accepted = False
            reason = f"confidence {confidence:.3f} below threshold {minimum_confidence:.3f}"
        elif not lo <= proposed <= hi:
            accepted = False
            reason = f"value {proposed!r} outside [{lo}, {hi}]"

        resolved = base_value
        if accepted:
            resolved = int(round(proposed)) if name in INTEGER_PARAMETERS else float(proposed)
            candidate = copy.deepcopy(spec)
            candidate["parameters"][name] = resolved
            try:
                candidate = normalize_spec(candidate)
            except SpecValidationError as exc:
                accepted = False
                resolved = base_value
                reason = "compiler contract rejected patch: " + "; ".join(exc.errors)
            else:
                spec.clear()
                spec.update(candidate)

        decisions.append(
            {
                "parameter": name,
                "base_value": base_value,
                "proposed_value": proposed,
                "resolved_value": resolved,
                "confidence": confidence,
                "accepted": accepted,
                "reason": reason,
                "evidence": patch["evidence"],
            }
        )
    return decisions


def _apply_room_patches(
    spec: dict[str, Any],
    room_patches: list[dict[str, Any]],
    minimum_confidence: float,
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for room_patch in room_patches:
        room_id = room_patch["room_id"]
        for name, patch in room_patch["parameter_patches"].items():
            rooms = spec.get("parameters", {}).get("rooms", [])
            room = next((item for item in rooms if item.get("id") == room_id), None)
            base_value = room.get(name) if room else None
            proposed = patch["value"]
            confidence = float(patch["confidence"])
            lo, hi = ROOM_NUMERIC_RANGES[name]
            accepted = True
            reason = "accepted"

            if room is None:
                accepted = False
                reason = f"selected scene spec has no room id {room_id!r}"
            elif confidence < minimum_confidence:
                accepted = False
                reason = f"confidence {confidence:.3f} below threshold {minimum_confidence:.3f}"
            elif not lo <= proposed <= hi:
                accepted = False
                reason = f"value {proposed!r} outside [{lo}, {hi}]"

            resolved = base_value
            if accepted:
                resolved = int(round(proposed)) if name in ROOM_INTEGER_KEYS else float(proposed)
                candidate = copy.deepcopy(spec)
                candidate_room = next(
                    item for item in candidate["parameters"]["rooms"] if item["id"] == room_id
                )
                candidate_room[name] = resolved
                try:
                    candidate = normalize_spec(candidate)
                except SpecValidationError as exc:
                    accepted = False
                    resolved = base_value
                    reason = "compiler contract rejected patch: " + "; ".join(exc.errors)
                else:
                    spec.clear()
                    spec.update(candidate)

            decisions.append(
                {
                    "room_id": room_id,
                    "parameter": name,
                    "base_value": base_value,
                    "proposed_value": proposed,
                    "resolved_value": resolved,
                    "confidence": confidence,
                    "accepted": accepted,
                    "reason": reason,
                    "evidence": patch["evidence"],
                }
            )
    return decisions


def apply_visual_review(
    scene_spec: dict[str, Any],
    review: dict[str, Any],
    *,
    minimum_confidence: float = 0.40,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply expressible visual corrections and preserve template-gap findings."""
    validate_visual_review(review)
    if not 0.0 <= minimum_confidence <= 1.0:
        raise ValueError("minimum_confidence must be in [0, 1]")

    spec = normalize_spec(copy.deepcopy(scene_spec))
    if spec["factory"] != review["factory"]:
        raise VisualReviewError(
            [f"review factory {review['factory']!r} does not match scene spec {spec['factory']!r}"]
        )

    decisions = _apply_global_patches(spec, review["parameter_patches"], minimum_confidence)
    room_decisions = _apply_room_patches(spec, review["room_patches"], minimum_confidence)
    spec = normalize_spec(spec)

    report = {
        "repair_version": 1,
        "factory": spec["factory"],
        "minimum_patch_confidence": minimum_confidence,
        "scores": copy.deepcopy(review["scores"]),
        "decisions": decisions,
        "room_decisions": room_decisions,
        "template_gaps": copy.deepcopy(review["template_gaps"]),
        "summary": review["summary"],
    }
    return spec, report

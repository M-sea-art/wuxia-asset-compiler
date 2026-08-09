"""Validate VLM reference analysis and resolve it into a bounded scene spec.

The vision model proposes observations and parameter estimates. Deterministic code
chooses what is accepted. This keeps the model in the interpretation layer instead of
letting it own geometry truth or Blender execution.
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
from compiler.templates import make_base_spec, supported_templates


REQUIRED_ROOT_KEYS = {
    "analysis_version",
    "factory_candidate",
    "factory_confidence",
    "camera",
    "parameter_estimates",
    "observations",
    "uncertainties",
}
ALLOWED_ROOT_KEYS = REQUIRED_ROOT_KEYS | {"room_estimates"}

CAMERA_KEYS = {"projection", "azimuth_deg", "elevation_deg", "confidence"}
PROJECTIONS = {"orthographic_like", "perspective", "unknown"}
ESTIMATE_KEYS = {"value", "confidence", "evidence"}
OBSERVATION_KEYS = {"subject", "statement", "confidence"}
ROOM_ESTIMATE_KEYS = {"room_id", "parameter_estimates"}


class ReferenceAnalysisError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid reference analysis:\n- " + "\n- ".join(errors))


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _confidence(value: Any) -> bool:
    return _number(value) and 0.0 <= float(value) <= 1.0


def _validate_estimate(estimate: Any, path: str, errors: list[str]) -> None:
    if not isinstance(estimate, dict) or set(estimate) != ESTIMATE_KEYS:
        errors.append(f"{path} must contain exactly {sorted(ESTIMATE_KEYS)}")
        return
    if not _number(estimate.get("value")):
        errors.append(f"{path}.value must be a number")
    if not _confidence(estimate.get("confidence")):
        errors.append(f"{path}.confidence must be in [0, 1]")
    evidence = estimate.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        errors.append(f"{path}.evidence must be non-empty")


def validate_reference_analysis(data: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(data, dict):
        raise ReferenceAnalysisError(["root must be an object"])

    missing = REQUIRED_ROOT_KEYS - set(data)
    unknown = set(data) - ALLOWED_ROOT_KEYS
    if missing:
        errors.append(f"missing root keys: {sorted(missing)}")
    if unknown:
        errors.append(f"unknown root keys: {sorted(unknown)}")

    if data.get("analysis_version") != 1:
        errors.append("analysis_version must be exactly 1")

    factory = data.get("factory_candidate")
    if factory not in supported_templates():
        errors.append(f"unsupported factory_candidate: {factory!r}")
    if not _confidence(data.get("factory_confidence")):
        errors.append("factory_confidence must be in [0, 1]")

    camera = data.get("camera")
    if not isinstance(camera, dict):
        errors.append("camera must be an object")
    else:
        if set(camera) != CAMERA_KEYS:
            errors.append(
                f"camera keys must be exactly {sorted(CAMERA_KEYS)}; got {sorted(camera)}"
            )
        if camera.get("projection") not in PROJECTIONS:
            errors.append(f"unsupported camera projection: {camera.get('projection')!r}")
        azimuth = camera.get("azimuth_deg")
        elevation = camera.get("elevation_deg")
        if not _number(azimuth) or not 0.0 <= float(azimuth) < 360.0:
            errors.append("camera.azimuth_deg must be in [0, 360)")
        if not _number(elevation) or not -10.0 <= float(elevation) <= 89.0:
            errors.append("camera.elevation_deg must be in [-10, 89]")
        if not _confidence(camera.get("confidence")):
            errors.append("camera.confidence must be in [0, 1]")

    estimates = data.get("parameter_estimates")
    if not isinstance(estimates, dict):
        errors.append("parameter_estimates must be an object")
    else:
        unknown_params = set(estimates) - set(PARAM_RANGES)
        if unknown_params:
            errors.append(f"unknown parameter estimates: {sorted(unknown_params)}")
        for name, estimate in estimates.items():
            if name in PARAM_RANGES:
                _validate_estimate(estimate, f"parameter_estimates.{name}", errors)

    room_estimates = data.get("room_estimates", [])
    if not isinstance(room_estimates, list):
        errors.append("room_estimates must be an array when provided")
    else:
        seen_rooms: set[str] = set()
        for index, room_estimate in enumerate(room_estimates):
            prefix = f"room_estimates[{index}]"
            if not isinstance(room_estimate, dict) or set(room_estimate) != ROOM_ESTIMATE_KEYS:
                errors.append(f"{prefix} must contain exactly {sorted(ROOM_ESTIMATE_KEYS)}")
                continue
            room_id = room_estimate.get("room_id")
            if not isinstance(room_id, str) or not room_id.strip():
                errors.append(f"{prefix}.room_id must be a non-empty string")
            elif room_id in seen_rooms:
                errors.append(f"duplicate room estimate id: {room_id!r}")
            else:
                seen_rooms.add(room_id)

            room_params = room_estimate.get("parameter_estimates")
            if not isinstance(room_params, dict):
                errors.append(f"{prefix}.parameter_estimates must be an object")
                continue
            unknown_room_params = set(room_params) - set(ROOM_NUMERIC_RANGES)
            if unknown_room_params:
                errors.append(
                    f"{prefix} unknown room parameter estimates: {sorted(unknown_room_params)}"
                )
            for name, estimate in room_params.items():
                if name in ROOM_NUMERIC_RANGES:
                    _validate_estimate(
                        estimate,
                        f"{prefix}.parameter_estimates.{name}",
                        errors,
                    )

    observations = data.get("observations")
    if not isinstance(observations, list):
        errors.append("observations must be an array")
    else:
        for index, observation in enumerate(observations):
            if not isinstance(observation, dict) or set(observation) != OBSERVATION_KEYS:
                errors.append(
                    f"observations[{index}] must contain exactly {sorted(OBSERVATION_KEYS)}"
                )
                continue
            if not isinstance(observation.get("subject"), str) or not observation["subject"].strip():
                errors.append(f"observations[{index}].subject must be non-empty")
            if not isinstance(observation.get("statement"), str) or not observation["statement"].strip():
                errors.append(f"observations[{index}].statement must be non-empty")
            if not _confidence(observation.get("confidence")):
                errors.append(f"observations[{index}].confidence must be in [0, 1]")

    uncertainties = data.get("uncertainties")
    if not isinstance(uncertainties, list) or not all(
        isinstance(item, str) and item.strip() for item in uncertainties
    ):
        errors.append("uncertainties must be an array of non-empty strings")

    if errors:
        raise ReferenceAnalysisError(errors)
    return data


def _resolve_scalar_estimates(
    spec: dict[str, Any],
    analysis: dict[str, Any],
    factory: str,
    minimum_confidence: float,
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for name, estimate in analysis["parameter_estimates"].items():
        proposed = estimate["value"]
        confidence = float(estimate["confidence"])
        owns_parameter = name in spec["parameters"]
        base_value = spec["parameters"].get(name)
        lo, hi = PARAM_RANGES[name]

        accepted = True
        reason = "accepted"
        if not owns_parameter:
            accepted = False
            reason = f"selected template {factory!r} does not own parameter {name!r}"
        elif confidence < minimum_confidence:
            accepted = False
            reason = f"confidence {confidence:.3f} below threshold {minimum_confidence:.3f}"
        elif not lo <= proposed <= hi:
            accepted = False
            reason = f"value {proposed!r} outside [{lo}, {hi}]"

        if accepted:
            resolved = int(round(proposed)) if name in INTEGER_PARAMETERS else float(proposed)
            if not lo <= resolved <= hi:
                accepted = False
                reason = f"rounded value {resolved!r} outside [{lo}, {hi}]"
            else:
                spec["parameters"][name] = resolved

        decisions.append(
            {
                "parameter": name,
                "base_value": base_value,
                "proposed_value": proposed,
                "resolved_value": spec["parameters"].get(name),
                "confidence": confidence,
                "accepted": accepted,
                "reason": reason,
                "evidence": estimate["evidence"],
            }
        )
    return decisions


def _resolve_room_estimates(
    spec: dict[str, Any],
    analysis: dict[str, Any],
    minimum_confidence: float,
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    rooms = spec.get("parameters", {}).get("rooms")
    room_map = {room["id"]: room for room in rooms} if isinstance(rooms, list) else {}

    for room_estimate in analysis.get("room_estimates", []):
        room_id = room_estimate["room_id"]
        for name, estimate in room_estimate["parameter_estimates"].items():
            proposed = estimate["value"]
            confidence = float(estimate["confidence"])
            room = room_map.get(room_id)
            base_value = room.get(name) if room else None
            lo, hi = ROOM_NUMERIC_RANGES[name]

            accepted = True
            reason = "accepted"
            if room is None:
                accepted = False
                reason = f"selected template has no room id {room_id!r}"
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
                    room_map = {item["id"]: item for item in spec["parameters"]["rooms"]}

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
                    "evidence": estimate["evidence"],
                }
            )
    return decisions


def resolve_reference_analysis(
    analysis: dict[str, Any],
    *,
    seed: int = 0,
    minimum_confidence: float = 0.35,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve vision estimates against a deterministic base template."""
    validate_reference_analysis(analysis)
    if not 0.0 <= minimum_confidence <= 1.0:
        raise ValueError("minimum_confidence must be in [0, 1]")

    factory = analysis["factory_candidate"]
    spec = make_base_spec(factory, seed=seed)
    decisions = _resolve_scalar_estimates(spec, analysis, factory, minimum_confidence)
    spec = normalize_spec(spec)
    room_decisions = _resolve_room_estimates(spec, analysis, minimum_confidence)
    spec = normalize_spec(spec)

    report = {
        "resolution_version": 1,
        "factory": factory,
        "factory_confidence": analysis["factory_confidence"],
        "minimum_parameter_confidence": minimum_confidence,
        "camera": copy.deepcopy(analysis["camera"]),
        "decisions": decisions,
        "room_decisions": room_decisions,
        "observations": copy.deepcopy(analysis["observations"]),
        "uncertainties": copy.deepcopy(analysis["uncertainties"]),
    }
    return spec, report

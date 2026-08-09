"""Compound factory for the open-front cliff ground-floor slice.

This is intentionally not roofed: in the mother reference it is the first floor of a
multi-storey sect compound, so the upper boundary is the next floor deck/beam system.
"""

from __future__ import annotations

from typing import Any

from factories import (
    _add_room_boundary_frame,
    _add_stone_steps,
    _make_material_pack,
    _room_centers,
)
from primitives import add_box, add_rock
from room_factories import ROOM_FACTORIES


def build_cliff_ground_floor(spec: dict[str, Any]):
    parameters = spec["parameters"]
    seed = int(spec.get("seed", 0))
    width = float(parameters["width"])
    depth = float(parameters["depth"])
    wall_height = float(parameters["wall_height"])
    platform_height = float(parameters["platform_height"])
    cliff_embed = float(parameters["cliff_embed"])
    step_count = int(parameters["stone_step_count"])
    rooms = list(parameters["rooms"])
    materials = _make_material_pack(
        float(parameters.get("wood_age", 0.68)),
        float(parameters.get("moss", 0.22)),
    )

    z0 = platform_height
    # The cliff is scenery/support behind the cutaway, not a foreground boulder.
    add_rock(
        "GroundFloorCliffMass",
        (-width * (0.30 + 0.15 * cliff_embed), -depth * 0.78, -1.05),
        (width * 0.66, depth * 0.62, max(3.0, platform_height + 2.2)),
        materials["stone"],
        seed=seed + 301,
    )
    add_box(
        "GroundFloorStonePlatform",
        (0.0, 0.0, z0 - 0.14),
        (width + 0.85, depth + 0.65, 0.28),
        materials["stone"],
    )
    add_box(
        "GroundFloorTimberDeck",
        (0.0, 0.0, z0),
        (width, depth, 0.18),
        materials["wood"],
    )
    add_box(
        "GroundFloorBackWall",
        (0.0, -depth / 2 + 0.18, z0 + wall_height * 0.48),
        (width - 0.45, 0.14, wall_height * 0.82),
        materials["plaster"],
    )

    centers = _room_centers(width, rooms)
    _add_room_boundary_frame(width, depth, wall_height, z0, centers, materials["wood"])

    # The next floor is represented as a thin timber deck with exposed beams,
    # matching the cutaway mother image instead of placing a roof on this slice.
    add_box(
        "UpperFloorDeck",
        (0.0, 0.0, z0 + wall_height + 0.05),
        (width + 0.18, depth + 0.12, 0.16),
        materials["wood"],
    )
    for center_x, room in centers:
        add_box(
            "UpperFloorCrossBeam",
            (center_x, 0.0, z0 + wall_height - 0.04),
            (0.18, depth - 0.25, 0.22),
            materials["wood"],
        )
        ROOM_FACTORIES[room["template"]](
            room,
            center_x,
            depth,
            z0,
            wall_height,
            materials,
        )

    _add_stone_steps(width, depth, z0, step_count, materials["stone"])

    return {
        "factory": "cliff_ground_floor",
        "room_count": len(rooms),
        "bounds_hint": [width, depth, z0 + wall_height + 0.25],
    }

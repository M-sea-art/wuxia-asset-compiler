"""Deterministic Blender factories for Wuxia Asset Compiler.

Keep this module boring and explicit. Agents choose bounded parameters;
these functions own mesh construction details.
"""

from __future__ import annotations

import math
from typing import Any

from primitives import add_box, add_rock, make_material
from room_factories import ROOM_FACTORIES


def _make_material_pack(wood_age: float, moss: float) -> dict[str, Any]:
    wood_luma = max(0.10, 0.27 - 0.08 * wood_age)
    wood_hex = "#%02x%02x%02x" % (
        int(255 * wood_luma),
        int(255 * wood_luma * 0.82),
        int(255 * wood_luma * 0.62),
    )
    stone_green = int(255 * min(0.30, 0.17 + moss * 0.10))
    stone_hex = f"#{int(255 * 0.26):02x}{stone_green:02x}{int(255 * 0.22):02x}"
    return {
        "wood": make_material("Wuxia_AgedWood", wood_hex, roughness=0.78),
        "roof": make_material("Wuxia_DarkTile", "#242426", roughness=0.84),
        "stone": make_material("Wuxia_Stone", stone_hex, roughness=0.93),
        "plaster": make_material("Wuxia_Plaster", "#afa891", roughness=0.90),
        "cloth": make_material("Wuxia_Cloth", "#6d6556", roughness=0.95),
        "metal": make_material("Wuxia_Iron", "#25282a", roughness=0.55, metallic=0.65),
        "lantern": make_material(
            "Wuxia_LanternGlow",
            "#e7a54d",
            roughness=0.65,
            emission_strength=1.6,
        ),
    }


def _add_timber_frame(
    width: float,
    depth: float,
    wall_height: float,
    z0: float,
    post_count_x: int,
    wood_mat,
):
    post = 0.18
    beam = 0.16
    margin = 0.38

    if post_count_x <= 2:
        xs = [-width / 2 + margin, width / 2 - margin]
    else:
        span = width - 2 * margin
        xs = [-width / 2 + margin + span * i / (post_count_x - 1) for i in range(post_count_x)]

    for x in xs:
        for y in (-depth / 2 + margin, depth / 2 - margin):
            add_box(
                "TimberPost",
                (x, y, z0 + wall_height / 2),
                (post, post, wall_height),
                wood_mat,
            )

    for y in (-depth / 2 + margin, depth / 2 - margin):
        add_box(
            "LongBeam",
            (0.0, y, z0 + wall_height - 0.12),
            (width - 2 * margin + post, beam, beam),
            wood_mat,
        )

    for x in (-width / 2 + margin, width / 2 - margin):
        add_box(
            "CrossBeam",
            (x, 0.0, z0 + wall_height - 0.12),
            (beam, depth - 2 * margin + post, beam),
            wood_mat,
        )


def _add_gabled_roof(
    width: float,
    depth: float,
    wall_top: float,
    pitch_deg: float,
    overhang: float,
    roof_mat,
):
    pitch = math.radians(pitch_deg)
    half_run = depth / 2 + overhang
    slope_len = half_run / max(math.cos(pitch), 1e-4)
    rise = half_run * math.tan(pitch)
    roof_width = width + 2 * overhang
    thickness = 0.12

    for sign in (-1, 1):
        y = sign * half_run / 2
        z = wall_top + rise / 2
        add_box(
            "RoofPanel",
            (0.0, y, z),
            (roof_width, slope_len, thickness),
            roof_mat,
            rotation=(sign * pitch, 0.0, 0.0),
        )

    add_box(
        "RoofRidge",
        (0.0, 0.0, wall_top + rise + 0.05),
        (roof_width + 0.12, 0.18, 0.18),
        roof_mat,
    )


def _add_stone_steps(width: float, depth: float, z0: float, count: int, stone_mat):
    step_w = min(1.6, width * 0.28)
    step_d = 0.42
    total_drop = max(z0, 0.4)
    for i in range(count):
        t = i / max(count - 1, 1)
        y = depth / 2 + 0.45 + i * step_d * 0.82
        z = z0 - t * total_drop - 0.10
        add_box(
            f"StoneStep_{i:02d}",
            (width * 0.22, y, z),
            (step_w, step_d, 0.20),
            stone_mat,
        )


def _add_kitchen_props(width: float, depth: float, z0: float, stone_mat, wood_mat):
    add_box(
        "StoneStove",
        (-width * 0.22, -depth * 0.18, z0 + 0.45),
        (1.15, 0.95, 0.9),
        stone_mat,
    )
    add_box(
        "PrepBenchTop",
        (width * 0.22, -depth * 0.12, z0 + 0.82),
        (1.75, 0.68, 0.10),
        wood_mat,
    )
    for x in (width * 0.22 - 0.68, width * 0.22 + 0.68):
        add_box(
            "PrepBenchLeg",
            (x, -depth * 0.12, z0 + 0.42),
            (0.12, 0.12, 0.8),
            wood_mat,
        )


def build_cliff_kitchen(spec: dict[str, Any]):
    p = spec["parameters"]
    seed = int(spec.get("seed", 0))

    width = float(p["width"])
    depth = float(p["depth"])
    wall_height = float(p["wall_height"])
    pitch = float(p["roof_pitch_deg"])
    overhang = float(p["eave_overhang"])
    platform_height = float(p["platform_height"])
    post_count_x = int(p.get("post_count_x", 4))
    step_count = int(p["stone_step_count"])
    wood_age = float(p.get("wood_age", 0.5))
    moss = float(p.get("moss", 0.0))
    materials = _make_material_pack(wood_age, moss)

    z0 = platform_height
    cliff_embed = float(p["cliff_embed"])
    add_rock(
        "CliffMass",
        (-width * (0.30 + 0.22 * cliff_embed), -depth * 0.08, -0.7),
        (width * 0.70, depth * 0.90, max(2.8, platform_height + 2.0)),
        materials["stone"],
        seed=seed + 101,
    )
    add_box(
        "StonePlatform",
        (0.0, 0.0, platform_height - 0.14),
        (width + 0.65, depth + 0.55, 0.28),
        materials["stone"],
    )

    add_box("TimberFloor", (0.0, 0.0, z0), (width, depth, 0.18), materials["wood"])
    add_box(
        "BackWall",
        (0.0, -depth / 2 + 0.18, z0 + wall_height * 0.48),
        (width - 0.7, 0.12, wall_height * 0.78),
        materials["plaster"],
    )

    _add_timber_frame(width, depth, wall_height, z0, post_count_x, materials["wood"])
    _add_gabled_roof(width, depth, z0 + wall_height, pitch, overhang, materials["roof"])
    _add_stone_steps(width, depth, z0, step_count, materials["stone"])
    _add_kitchen_props(width, depth, z0, materials["stone"], materials["wood"])

    return {
        "factory": "cliff_kitchen",
        "bounds_hint": [
            width + 2 * overhang,
            depth + 2 * overhang,
            z0 + wall_height + depth,
        ],
    }


def _room_centers(width: float, rooms: list[dict[str, Any]]) -> list[tuple[float, dict[str, Any]]]:
    total_room_width = sum(float(room["width"]) for room in rooms)
    gap_total = max(0.0, width - total_room_width)
    gap = gap_total / max(len(rooms) - 1, 1)
    cursor = -width / 2
    result: list[tuple[float, dict[str, Any]]] = []
    for room in rooms:
        room_width = float(room["width"])
        center_x = cursor + room_width / 2
        result.append((center_x, room))
        cursor += room_width + gap
    return result


def _add_room_boundary_frame(
    width: float,
    depth: float,
    wall_height: float,
    z0: float,
    centers: list[tuple[float, dict[str, Any]]],
    wood_mat,
):
    post_size = 0.20
    boundary_xs = [-width / 2]
    for center_x, room in centers:
        boundary_xs.append(center_x + float(room["width"]) / 2)
    for x in boundary_xs:
        for y in (-depth / 2 + 0.30, depth / 2 - 0.30):
            add_box(
                "GroundFloorPost",
                (x, y, z0 + wall_height / 2),
                (post_size, post_size, wall_height),
                wood_mat,
            )
    for y in (-depth / 2 + 0.30, depth / 2 - 0.30):
        add_box(
            "GroundFloorLongBeam",
            (0.0, y, z0 + wall_height - 0.12),
            (width + post_size, 0.18, 0.18),
            wood_mat,
        )


def build_cliff_ground_floor(spec: dict[str, Any]):
    """Build the first composable multi-room slice from the reference mother image."""
    p = spec["parameters"]
    seed = int(spec.get("seed", 0))
    width = float(p["width"])
    depth = float(p["depth"])
    wall_height = float(p["wall_height"])
    pitch = float(p["roof_pitch_deg"])
    overhang = float(p["eave_overhang"])
    platform_height = float(p["platform_height"])
    cliff_embed = float(p["cliff_embed"])
    step_count = int(p["stone_step_count"])
    rooms = list(p["rooms"])
    materials = _make_material_pack(float(p.get("wood_age", 0.68)), float(p.get("moss", 0.22)))

    z0 = platform_height
    add_rock(
        "GroundFloorCliffMass",
        (-width * (0.26 + 0.18 * cliff_embed), -depth * 0.18, -0.8),
        (width * 0.72, depth * 0.92, max(3.0, platform_height + 2.3)),
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
    _add_gabled_roof(width, depth, z0 + wall_height, pitch, overhang, materials["roof"])

    for center_x, room in centers:
        room_factory = ROOM_FACTORIES[room["template"]]
        room_factory(room, center_x, depth, z0, wall_height, materials)

    _add_stone_steps(width, depth, z0, step_count, materials["stone"])

    return {
        "factory": "cliff_ground_floor",
        "room_count": len(rooms),
        "bounds_hint": [
            width + 2 * overhang,
            depth + 2 * overhang,
            z0 + wall_height + depth,
        ],
    }

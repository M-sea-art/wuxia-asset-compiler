"""Deterministic Blender factories for Wuxia Asset Compiler.

Keep this module boring and explicit. Agents choose bounded parameters;
these functions own mesh construction details.
"""

from __future__ import annotations

import math
import random
from typing import Any

import bpy


def _hex_rgb(value: str) -> tuple[float, float, float, float]:
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected #RRGGBB color, got {value!r}")
    rgb = tuple(int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (*rgb, 1.0)


def make_material(name: str, color: str, roughness: float = 0.7, metallic: float = 0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = _hex_rgb(color)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_box(name: str, location, dimensions, material=None, rotation=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material is not None:
        obj.data.materials.append(material)
    return obj


def add_rock(name: str, location, scale, material, seed: int):
    rng = random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for vertex in obj.data.vertices:
        direction = vertex.co.normalized()
        jitter = 1.0 + rng.uniform(-0.16, 0.16)
        vertex.co = direction * vertex.co.length * jitter
    obj.data.materials.append(material)
    return obj


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

    wood_luma = max(0.10, 0.27 - 0.08 * wood_age)
    wood_hex = "#%02x%02x%02x" % (
        int(255 * wood_luma),
        int(255 * wood_luma * 0.82),
        int(255 * wood_luma * 0.62),
    )
    stone_green = int(255 * min(0.30, 0.17 + moss * 0.10))
    stone_hex = f"#{int(255 * 0.26):02x}{stone_green:02x}{int(255 * 0.22):02x}"

    wood_mat = make_material("Wuxia_AgedWood", wood_hex, roughness=0.78)
    roof_mat = make_material("Wuxia_DarkTile", "#242426", roughness=0.84)
    stone_mat = make_material("Wuxia_Stone", stone_hex, roughness=0.93)
    plaster_mat = make_material("Wuxia_Plaster", "#afa891", roughness=0.90)

    z0 = platform_height
    cliff_embed = float(p["cliff_embed"])
    add_rock(
        "CliffMass",
        (-width * (0.30 + 0.22 * cliff_embed), -depth * 0.08, -0.7),
        (width * 0.70, depth * 0.90, max(2.8, platform_height + 2.0)),
        stone_mat,
        seed=seed + 101,
    )
    add_box(
        "StonePlatform",
        (0.0, 0.0, platform_height - 0.14),
        (width + 0.65, depth + 0.55, 0.28),
        stone_mat,
    )

    add_box("TimberFloor", (0.0, 0.0, z0), (width, depth, 0.18), wood_mat)
    add_box(
        "BackWall",
        (0.0, -depth / 2 + 0.18, z0 + wall_height * 0.48),
        (width - 0.7, 0.12, wall_height * 0.78),
        plaster_mat,
    )

    _add_timber_frame(width, depth, wall_height, z0, post_count_x, wood_mat)
    _add_gabled_roof(width, depth, z0 + wall_height, pitch, overhang, roof_mat)
    _add_stone_steps(width, depth, z0, step_count, stone_mat)
    _add_kitchen_props(width, depth, z0, stone_mat, wood_mat)

    return {
        "factory": "cliff_kitchen",
        "bounds_hint": [
            width + 2 * overhang,
            depth + 2 * overhang,
            z0 + wall_height + depth,
        ],
    }

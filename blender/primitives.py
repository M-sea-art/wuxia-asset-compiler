"""Small deterministic Blender construction primitives.

Factories should build with these helpers instead of repeating raw bpy setup.
"""

from __future__ import annotations

import random

import bpy


def _hex_rgb(value: str) -> tuple[float, float, float, float]:
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected #RRGGBB color, got {value!r}")
    rgb = tuple(int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (*rgb, 1.0)


def make_material(
    name: str,
    color: str,
    roughness: float = 0.7,
    metallic: float = 0.0,
    emission_strength: float = 0.0,
):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = _hex_rgb(color)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission_strength > 0.0:
            emission_input = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
            if emission_input is not None:
                emission_input.default_value = _hex_rgb(color)
            strength_input = bsdf.inputs.get("Emission Strength")
            if strength_input is not None:
                strength_input.default_value = emission_strength
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


def add_cylinder(
    name: str,
    location,
    radius: float,
    depth: float,
    material=None,
    rotation=(0.0, 0.0, 0.0),
    vertices: int = 12,
):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    if material is not None:
        obj.data.materials.append(material)
    return obj


def add_cone(
    name: str,
    location,
    radius1: float,
    radius2: float,
    depth: float,
    material=None,
    rotation=(0.0, 0.0, 0.0),
    vertices: int = 10,
):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    if material is not None:
        obj.data.materials.append(material)
    return obj


def add_point_light(
    name: str,
    location,
    *,
    energy: float,
    color=(1.0, 0.45, 0.12),
    radius: float = 0.55,
):
    bpy.ops.object.light_add(type="POINT", location=location)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.color = color
    light.data.shadow_soft_size = radius
    return light


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

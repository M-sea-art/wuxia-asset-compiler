"""Deterministic Blender-side validation for generated assets."""

from __future__ import annotations

import json
import math
import os
from typing import Any

import bmesh
import bpy
from mathutils import Vector


DEFAULT_TRIANGLE_BUDGET = 50_000


def _world_bounds(mesh_objects) -> dict[str, list[float]] | None:
    points: list[Vector] = []
    for obj in mesh_objects:
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        return None
    minimum = [min(point[i] for point in points) for i in range(3)]
    maximum = [max(point[i] for point in points) for i in range(3)]
    dimensions = [maximum[i] - minimum[i] for i in range(3)]
    return {
        "min": [round(value, 6) for value in minimum],
        "max": [round(value, 6) for value in maximum],
        "dimensions": [round(value, 6) for value in dimensions],
    }


def _mesh_topology_metrics(obj) -> tuple[int, int]:
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        non_manifold_edges = sum(1 for edge in bm.edges if not edge.is_manifold)
        zero_area_faces = sum(1 for face in bm.faces if face.calc_area() <= 1e-10)
        return non_manifold_edges, zero_area_faces
    finally:
        bm.free()


def collect_scene_report(
    spec: dict[str, Any],
    triangle_budget: int = DEFAULT_TRIANGLE_BUDGET,
) -> dict[str, Any]:
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]

    total_vertices = 0
    total_polygons = 0
    total_triangles = 0
    non_manifold_edges = 0
    zero_area_faces = 0
    missing_materials: list[str] = []
    unapplied_scale: list[str] = []
    negative_scale: list[str] = []

    for obj in mesh_objects:
        mesh = obj.data
        total_vertices += len(mesh.vertices)
        total_polygons += len(mesh.polygons)
        mesh.calc_loop_triangles()
        total_triangles += len(mesh.loop_triangles)

        obj_non_manifold, obj_zero_area = _mesh_topology_metrics(obj)
        non_manifold_edges += obj_non_manifold
        zero_area_faces += obj_zero_area

        if not obj.material_slots:
            missing_materials.append(obj.name)

        scale = tuple(float(value) for value in obj.scale)
        if any(abs(abs(value) - 1.0) > 1e-5 for value in scale):
            unapplied_scale.append(obj.name)
        if math.prod(scale) < 0:
            negative_scale.append(obj.name)

    failures: list[str] = []
    warnings: list[str] = []

    if not mesh_objects:
        failures.append("scene contains no mesh objects")
    if non_manifold_edges:
        failures.append(f"non-manifold edge count is {non_manifold_edges}")
    if zero_area_faces:
        failures.append(f"zero-area face count is {zero_area_faces}")
    if negative_scale:
        failures.append(f"negative scale objects: {sorted(negative_scale)}")
    if missing_materials:
        warnings.append(f"mesh objects without material slots: {sorted(missing_materials)}")
    if unapplied_scale:
        warnings.append(f"mesh objects with unapplied scale: {sorted(unapplied_scale)}")
    if total_triangles > triangle_budget:
        warnings.append(
            f"triangle budget exceeded: {total_triangles} > {triangle_budget}"
        )

    return {
        "report_version": 1,
        "factory": spec.get("factory"),
        "seed": spec.get("seed"),
        "status": "fail" if failures else "pass",
        "metrics": {
            "mesh_objects": len(mesh_objects),
            "vertices": total_vertices,
            "polygons": total_polygons,
            "triangles": total_triangles,
            "non_manifold_edges": non_manifold_edges,
            "zero_area_faces": zero_area_faces,
            "world_bounds": _world_bounds(mesh_objects),
        },
        "failures": failures,
        "warnings": warnings,
    }


def write_report(path: str, report: dict[str, Any]) -> str:
    absolute = os.path.abspath(path)
    os.makedirs(os.path.dirname(absolute), exist_ok=True)
    with open(absolute, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return absolute

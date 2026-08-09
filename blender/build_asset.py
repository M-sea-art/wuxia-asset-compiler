"""CLI entry point for deterministic Wuxia Asset Compiler Blender builds."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from factories import build_cliff_kitchen  # noqa: E402


FACTORIES = {
    "cliff_kitchen": build_cliff_kitchen,
}


PARAM_RANGES = {
    "width": (3.0, 20.0),
    "depth": (2.5, 14.0),
    "wall_height": (2.0, 6.0),
    "roof_pitch_deg": (15.0, 55.0),
    "eave_overhang": (0.2, 2.0),
    "platform_height": (0.2, 4.0),
    "cliff_embed": (0.0, 1.0),
}


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--preview")
    return parser.parse_args(argv)


def validate_spec(spec: dict) -> None:
    if spec.get("version") != 1:
        raise ValueError("Only scene spec version 1 is supported")
    factory = spec.get("factory")
    if factory not in FACTORIES:
        raise ValueError(f"Unsupported factory: {factory!r}")
    if not isinstance(spec.get("seed"), int) or spec["seed"] < 0:
        raise ValueError("seed must be a non-negative integer")
    parameters = spec.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("parameters must be an object")
    for key, (lo, hi) in PARAM_RANGES.items():
        if key not in parameters:
            raise ValueError(f"Missing parameter: {key}")
        value = float(parameters[key])
        if not lo <= value <= hi:
            raise ValueError(f"{key}={value} is outside [{lo}, {hi}]")
    steps = parameters.get("stone_step_count")
    if not isinstance(steps, int) or not 3 <= steps <= 30:
        raise ValueError("stone_step_count must be an integer in [3, 30]")


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def aim_object_at(obj, target=(0.0, 0.0, 1.5)) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_camera_and_lighting(spec: dict) -> None:
    parameters = spec["parameters"]
    width = float(parameters["width"])
    depth = float(parameters["depth"])
    height = float(parameters["platform_height"]) + float(parameters["wall_height"])
    radius = max(width, depth) * 1.6

    bpy.ops.object.camera_add(location=(radius, radius, height + radius * 0.72))
    camera = bpy.context.object
    camera.name = "PreviewCamera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = max(width, depth) * 1.72
    aim_object_at(camera, (0.0, 0.0, height * 0.55))
    bpy.context.scene.camera = camera

    bpy.ops.object.light_add(type="SUN", location=(0.0, 0.0, height + 8.0))
    sun = bpy.context.object
    sun.name = "KeySun"
    sun.rotation_euler = (
        math.radians(28),
        math.radians(-20),
        math.radians(32),
    )
    sun.data.energy = 2.0

    bpy.ops.object.light_add(
        type="AREA",
        location=(-radius * 0.5, radius * 0.3, height + radius * 0.8),
    )
    area = bpy.context.object
    area.name = "SoftFill"
    area.data.energy = 650.0
    area.data.shape = "DISK"
    area.data.size = max(width, depth) * 0.9
    aim_object_at(area, (0.0, 0.0, height * 0.5))

    world = bpy.context.scene.world or bpy.data.worlds.new("WuxiaWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.055, 0.052, 0.047, 1.0)
        background.inputs["Strength"].default_value = 0.45


def configure_render() -> None:
    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        pass
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False


def ensure_parent(path: str) -> str:
    absolute = os.path.abspath(path)
    os.makedirs(os.path.dirname(absolute), exist_ok=True)
    return absolute


def main() -> None:
    args = parse_args()
    spec_path = os.path.abspath(args.spec)
    with open(spec_path, "r", encoding="utf-8") as handle:
        spec = json.load(handle)

    validate_spec(spec)
    clear_scene()
    configure_render()

    FACTORIES[spec["factory"]](spec)
    setup_camera_and_lighting(spec)

    if args.preview:
        preview_path = ensure_parent(args.preview)
        bpy.context.scene.render.filepath = preview_path
        bpy.ops.render.render(write_still=True)
        print(f"[WuxiaAssetCompiler] preview={preview_path}")

    out_path = ensure_parent(args.out)
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        export_apply=True,
        export_cameras=False,
        export_lights=False,
    )
    print(f"[WuxiaAssetCompiler] glb={out_path}")


if __name__ == "__main__":
    main()

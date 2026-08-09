"""CLI entry point for deterministic Wuxia Asset Compiler Blender builds."""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
for path in (REPO_ROOT, THIS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from compiler.spec import load_spec  # noqa: E402
from factories import build_cliff_kitchen  # noqa: E402
from ground_floor_factory import build_cliff_ground_floor  # noqa: E402
from validation import collect_scene_report, write_report  # noqa: E402


FACTORIES = {
    "cliff_kitchen": build_cliff_kitchen,
    "cliff_ground_floor": build_cliff_ground_floor,
}


VIEW_AZIMUTHS = (45, 135, 225, 315)
CANONICAL_AZIMUTH = 90


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--preview", help="Render one canonical front/cutaway preview")
    parser.add_argument(
        "--preview-dir",
        help="Render four fixed QA views at 45/135/225/315 degrees",
    )
    parser.add_argument("--report", help="Write deterministic validation JSON")
    parser.add_argument("--triangle-budget", type=int, default=50_000)
    return parser.parse_args(argv)


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


def aim_object_at(obj, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def position_camera(camera, target: Vector, radius: float, azimuth_deg: float) -> None:
    azimuth = math.radians(azimuth_deg)
    vertical_ratio = float(camera.get("wuxia_vertical_ratio", 0.45))
    camera.location = (
        target.x + math.cos(azimuth) * radius,
        target.y + math.sin(azimuth) * radius,
        target.z + radius * vertical_ratio,
    )
    aim_object_at(camera, target)


def setup_camera_and_lighting(spec: dict):
    parameters = spec["parameters"]
    width = float(parameters["width"])
    depth = float(parameters["depth"])
    height = float(parameters["platform_height"]) + float(parameters["wall_height"])
    is_compound_floor = spec["factory"] == "cliff_ground_floor"
    orbit_radius = max(width, depth) * (1.5 if is_compound_floor else 2.0)
    target = Vector((0.0, 0.0, height * (0.50 if is_compound_floor else 0.55)))

    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.name = "PreviewCamera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = max(width, depth) * (1.12 if is_compound_floor else 1.45)
    camera["wuxia_vertical_ratio"] = 0.18 if is_compound_floor else 0.45
    position_camera(camera, target, orbit_radius, CANONICAL_AZIMUTH)
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
        location=(-orbit_radius * 0.35, orbit_radius * 0.25, height + orbit_radius * 0.30),
    )
    area = bpy.context.object
    area.name = "SoftFill"
    area.data.energy = 650.0
    area.data.shape = "DISK"
    area.data.size = max(width, depth) * 0.9
    aim_object_at(area, target)

    world = bpy.context.scene.world or bpy.data.worlds.new("WuxiaWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background:
        background.inputs["Color"].default_value = (0.055, 0.052, 0.047, 1.0)
        background.inputs["Strength"].default_value = 0.45

    return camera, target, orbit_radius


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


def render_preview(path: str, camera, target: Vector, radius: float, azimuth: float) -> str:
    absolute = ensure_parent(path)
    position_camera(camera, target, radius, azimuth)
    bpy.context.scene.render.filepath = absolute
    bpy.ops.render.render(write_still=True)
    print(f"[WuxiaAssetCompiler] preview[{azimuth}]={absolute}")
    return absolute


def render_qa_views(directory: str, camera, target: Vector, radius: float) -> list[str]:
    absolute_dir = os.path.abspath(directory)
    os.makedirs(absolute_dir, exist_ok=True)
    outputs: list[str] = []
    for azimuth in VIEW_AZIMUTHS:
        output = os.path.join(absolute_dir, f"view_{azimuth:03d}.png")
        outputs.append(render_preview(output, camera, target, radius, azimuth))
    return outputs


def main() -> None:
    args = parse_args()
    spec = load_spec(os.path.abspath(args.spec))

    if spec["factory"] not in FACTORIES:
        raise RuntimeError(f"No Blender implementation registered for {spec['factory']!r}")

    clear_scene()
    configure_render()

    FACTORIES[spec["factory"]](spec)
    camera, target, orbit_radius = setup_camera_and_lighting(spec)

    if args.preview:
        render_preview(args.preview, camera, target, orbit_radius, CANONICAL_AZIMUTH)
    if args.preview_dir:
        render_qa_views(args.preview_dir, camera, target, orbit_radius)

    report = collect_scene_report(spec, triangle_budget=args.triangle_budget)
    if args.report:
        report_path = write_report(args.report, report)
        print(f"[WuxiaAssetCompiler] report={report_path}")

    print(
        "[WuxiaAssetCompiler] validation="
        f"{report['status']} triangles={report['metrics']['triangles']}"
    )
    if report["status"] != "pass":
        raise RuntimeError("Asset validation failed: " + "; ".join(report["failures"]))

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

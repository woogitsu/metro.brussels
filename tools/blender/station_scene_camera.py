"""Shaded review from the train cab and from the canonical mezzanine access."""

import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "track"))
import placement  # noqa: E402
import station_chamber as CH  # noqa: E402
import station_components as SC  # noqa: E402
import sweep as SW  # noqa: E402
from profiles import profile_points  # noqa: E402


def frame_at(points, distances, chainage_m):
    position, _index, _part = placement.frame_at(points, distances, chainage_m)
    before, _i, _t = placement.frame_at(points, distances, chainage_m - 1.0)
    after, _i, _t = placement.frame_at(points, distances, chainage_m + 1.0)
    forward = (Vector(after) - Vector(before)).normalized()
    right = forward.cross(Vector((0.0, 0.0, 1.0))).normalized()
    return Vector(position), forward, right


def neutral(name, rgb):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*rgb, 1.0)
    material.use_nodes = True
    node = material.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = (*rgb, 1.0)
    node.inputs["Roughness"].default_value = 0.85
    return material


def assign_review_materials():
    palette = {
        "tunnel": neutral("qa_tunnel", (0.39, 0.42, 0.45)),
        "platform": neutral("qa_platform", (0.56, 0.55, 0.52)),
        "edge": neutral("qa_edge", (0.80, 0.65, 0.22)),
        "stairs": neutral("qa_stairs", (0.65, 0.62, 0.57)),
        "lift": neutral("qa_lift", (0.38, 0.48, 0.52)),
        "mezzanine": neutral("qa_mezzanine", (0.54, 0.55, 0.52)),
        "corridor": neutral("qa_corridor", (0.47, 0.56, 0.59)),
        "portal": neutral("qa_portal", (0.46, 0.52, 0.55)),
    }
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        kind = next((key for key in palette if key in obj.name.lower()), "tunnel")
        obj.data.materials.clear()
        obj.data.materials.append(palette[kind])


def render_camera(name, eye, target, out, fov_deg=70.0):
    camera_data = bpy.data.cameras.new(name)
    camera = bpy.data.objects.new(name, camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = eye
    camera.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
    camera_data.angle_y = math.radians(fov_deg)
    camera_data.clip_end = 1000.0
    bpy.context.scene.camera = camera
    lamp_data = bpy.data.lights.new(name + "_lamp", type="POINT")
    lamp = bpy.data.objects.new(name + "_lamp", lamp_data)
    bpy.context.scene.collection.objects.link(lamp)
    lamp.location = eye
    lamp_data.energy = 4500.0
    lamp_data.shadow_soft_size = 2.0
    scene = bpy.context.scene
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(lamp, do_unlink=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    print(f"[KADR STACJI] {name}: {out}")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True)
    parser.add_argument("--axis", required=True)
    parser.add_argument("--layout", required=True)
    parser.add_argument("--station-index", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--cab-eye-height-m", type=float, required=True)
    parser.add_argument("--cab-eye-setback-m", type=float, required=True)
    parser.add_argument("--track-offset-m", type=float, required=True)
    parser.add_argument("--cab-fov-deg", type=float, required=True)
    args = parser.parse_args(argv)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=args.scene)
    assign_review_materials()
    with open(args.axis, encoding="utf-8") as handle:
        axis = json.load(handle)
    with open(args.layout, encoding="utf-8") as handle:
        layout = json.load(handle)
    platforms = layout["platforms"]
    platform = platforms[args.station_index]
    points = [tuple(point) for point in axis["points"]]
    distances = SW.chainages(points)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.world.color = (0.13, 0.15, 0.18)
    scene.view_settings.view_transform = "AgX"
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    cab_at = max(0.0, platform["station_chainage_m"] - 40.0 - args.cab_eye_setback_m)
    origin, forward, right = frame_at(points, distances, cab_at)
    cab_eye = origin + right * args.track_offset_m + Vector((0, 0, args.cab_eye_height_m))
    render_camera("cab", cab_eye, cab_eye + forward * 60.0,
                  args.out + "_cab.png", args.cab_fov_deg)

    windows = CH.access_windows([platform], profile_points("station"),
                                layout["platform_height_m"])
    if len(windows) != 1:
        raise SystemExit("BŁĄD: wybrany peron nie ma jednego wejścia korytarza")
    start, end, side = windows[0]
    origin, _forward, right = frame_at(points, distances, (start + end) / 2.0)
    wall_m = max(abs(y) for y, _z in profile_points("station"))
    floor_m = max(z for _y, z in profile_points("station")) + SC.DESIGN_SLAB_THICKNESS_M
    eye = origin + right * side * (wall_m - 3.0) + Vector((0, 0, floor_m + 1.3))
    target = origin + right * side * (wall_m + 12.0) + Vector((0, 0, floor_m + 1.3))
    render_camera("corridor", eye, target, args.out + "_corridor.png")


if __name__ == "__main__":
    main()

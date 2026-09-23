"""Render a cab-height preview of tunnel and track detail from the GLBs."""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(__file__))
import sweep as SW
from profiles import profile_points
from track_detail import frame_at
from tunnel_sweep import load_centerline


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--centerline", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--tunnel-dir", required=True)
    parser.add_argument("--detail-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--at", type=float, default=120.0)
    return parser.parse_args(argv)


def main():
    args = parse_args()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    with open(args.manifest, encoding="utf-8") as handle:
        manifest = json.load(handle)
    points, stations, _, _ = load_centerline(args.centerline)
    result = SW.sweep(points, profile_points("box_double"),
                      station_chainages=[s["chainage_m"] for s in stations])
    tunnel_mat = bpy.data.materials.new("Godot tunnel concrete")
    tunnel_mat.diffuse_color = (0.34, 0.38, 0.40, 1.0)
    tunnel_mat.use_nodes = True
    surface = tunnel_mat.node_tree.nodes.get("Principled BSDF")
    surface.inputs["Base Color"].default_value = (0.34, 0.38, 0.40, 1.0)
    surface.inputs["Roughness"].default_value = 0.95
    surface.inputs["Metallic"].default_value = 0.0

    for chunk in manifest["chunks"]:
        if chunk["end_m"] < args.at - 20 or chunk["start_m"] > args.at + 230:
            continue
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(args.tunnel_dir, chunk["file"]))
        for obj in set(bpy.data.objects) - before:
            if obj.type == "MESH":
                obj.data.materials.clear()
                obj.data.materials.append(tunnel_mat)
        bpy.ops.import_scene.gltf(filepath=os.path.join(
            args.detail_dir, chunk["id"] + "_detail.glb"))

    camera_frame = frame_at(result["frames"], result["station_m"], args.at)
    pos, forward, right, up = camera_frame
    eye = Vector(SW.add(pos, SW.add(SW.scale(right, 2.1), SW.scale(up, 2.2))))
    cam_data = bpy.data.cameras.new("Cab preview")
    cam = bpy.data.objects.new("Cab preview", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = eye
    cam.rotation_euler = Vector(forward).to_track_quat("-Z", "Y").to_euler()
    cam_data.type = "PERSP"
    cam_data.lens = 26
    bpy.context.scene.camera = cam

    # Fixtures in track_detail.py are at every 16 m, on both side walls.
    # The small inward offset keeps the point source clear of the wall mesh.
    for at in range(math.ceil((args.at - 20) / 16),
                    math.floor((args.at + 110) / 16) + 1):
        sample = frame_at(result["frames"], result["station_m"], at * 16.0)
        centre, _, side, vertical = sample
        for sign in (-1, 1):
            light_data = bpy.data.lights.new("wall practical", type="POINT")
            light_data.energy = 350
            light_data.color = (1.0, 0.86, 0.67)
            light_data.shadow_soft_size = 0.35
            light_data.use_custom_distance = True
            light_data.cutoff_distance = 14.0
            light = bpy.data.objects.new("wall practical", light_data)
            bpy.context.collection.objects.link(light)
            light.location = SW.add(centre, SW.add(SW.scale(side, sign * 4.25),
                                                  SW.scale(vertical, 3.35)))

    world = bpy.data.worlds.new("tunnel darkness")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.015, 0.02, 0.027, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = os.path.abspath(args.out)
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "AgX"
    bpy.ops.render.render(write_still=True)
    print("[PODGLĄD]", scene.render.filepath)


if __name__ == "__main__":
    main()

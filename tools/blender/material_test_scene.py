#!/usr/bin/env python3
"""T-902 deterministic neutral material test scene for Blender headless.

Usage:
  blender --background --python tools/blender/material_test_scene.py -- \
    --config data/design/visual-style.json \
    --out build/material-style.glb \
    --renders renders/material-style
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--renders", required=True)
    return p.parse_args(argv)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.materials, bpy.data.curves):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def principled_input(bsdf, *names):
    for name in names:
        if name in bsdf.inputs:
            return bsdf.inputs[name]
    return None


def make_material(spec):
    mat = bpy.data.materials.new(spec["id"])
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        raise SystemExit(f"BŁĄD: brak Principled BSDF dla {spec['id']}")

    base = principled_input(bsdf, "Base Color")
    metallic = principled_input(bsdf, "Metallic")
    roughness = principled_input(bsdf, "Roughness")
    alpha = principled_input(bsdf, "Alpha")
    transmission = principled_input(bsdf, "Transmission Weight", "Transmission")

    base.default_value = tuple(spec["base_color"])
    metallic.default_value = float(spec.get("metallic", 0.0))
    roughness.default_value = float(spec.get("roughness", 0.5))
    if alpha is not None:
        alpha.default_value = float(spec.get("alpha", 1.0))
    if transmission is not None:
        transmission.default_value = float(spec.get("transmission_weight", 0.0))

    if float(spec.get("alpha", 1.0)) < 1.0:
        if hasattr(mat, "surface_render_method"):
            try:
                mat.surface_render_method = "DITHERED"
            except Exception:
                pass
        elif hasattr(mat, "blend_method"):
            try:
                mat.blend_method = "BLEND"
            except Exception:
                pass
    return mat


def add_sample(spec, index, columns=5):
    row, col = divmod(index, columns)
    x = (col - (columns - 1) / 2.0) * 2.55
    y = -row * 2.55
    z = 0.95

    if spec["id"] == "glass":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(x, y, z))
        obj = bpy.context.active_object
        obj.scale = (0.82, 0.82, 0.82)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    else:
        bpy.ops.mesh.primitive_cube_add(size=1.65, location=(x, y, z))
        obj = bpy.context.active_object
        bevel = obj.modifiers.new("diagnostic_bevel", "BEVEL")
        bevel.width = 0.08
        bevel.segments = 3
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=bevel.name)

    obj.name = f"swatch_{index:02d}_{spec['id']}"
    mat = make_material(spec)
    obj.data.materials.append(mat)
    obj["material_id"] = spec["id"]
    obj["status"] = spec.get("status", "unknown")
    return obj


def add_floor(rows, columns):
    width = max(14.0, columns * 2.75)
    depth = max(8.0, rows * 2.75 + 2.0)
    bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0.0, -max(0.0, rows - 1) * 1.25, 0.0))
    floor = bpy.context.active_object
    floor.name = "diagnostic_floor"
    floor.scale = (width / 2.0, depth / 2.0, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mat = bpy.data.materials.new("diagnostic_floor_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    principled_input(bsdf, "Base Color").default_value = (0.11, 0.115, 0.12, 1.0)
    principled_input(bsdf, "Metallic").default_value = 0.0
    principled_input(bsdf, "Roughness").default_value = 0.78
    floor.data.materials.append(mat)


def scene_bounds():
    mins = Vector((1e9, 1e9, 1e9))
    maxs = Vector((-1e9, -1e9, -1e9))
    found = False
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        found = True
        for corner in obj.bound_box:
            p = obj.matrix_world @ Vector(corner)
            mins = Vector(tuple(min(mins[i], p[i]) for i in range(3)))
            maxs = Vector(tuple(max(maxs[i], p[i]) for i in range(3)))
    if not found:
        raise SystemExit("BŁĄD: scena materiałowa nie zawiera siatki")
    return mins, maxs


def set_render_engine(preferences):
    scene = bpy.context.scene
    errors = []
    for engine in preferences:
        try:
            scene.render.engine = engine
            return engine
        except Exception as exc:
            errors.append(f"{engine}: {exc}")
    raise SystemExit("BŁĄD: brak wspieranego renderera: " + " | ".join(errors))


def setup_world_and_lights(cfg):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("technical_world")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = tuple(cfg["background_rgba"])
    bg.inputs[1].default_value = float(cfg["fixed_world_strength"])
    scene.world = world

    def area(name, location, energy, size):
        data = bpy.data.lights.new(name, type="AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = location
        direction = (Vector((0.0, -2.0, 0.6)) - obj.location).normalized()
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        return obj

    area("key_area", (4.5, -1.5, 8.5), 950.0, 5.5)
    area("fill_area", (-5.0, -4.0, 5.5), 550.0, 4.0)


def add_camera(name, location, target, lens):
    data = bpy.data.cameras.new(name)
    data.lens = float(lens)
    cam = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(cam)
    cam.location = Vector(location)
    direction = (Vector(target) - cam.location).normalized()
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return cam


def render(cam, path, resolution):
    scene = bpy.context.scene
    scene.camera = cam
    scene.render.resolution_x = int(resolution[0])
    scene.render.resolution_y = int(resolution[1])
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if not os.path.isfile(path) or os.path.getsize(path) <= 1024:
        raise SystemExit(f"BŁĄD: render nie powstał lub jest podejrzanie mały: {path}")
    print(f"[RENDER] {path} {os.path.getsize(path)} B")


def average_location(objects):
    if not objects:
        raise SystemExit("BŁĄD: brak obiektów do wyznaczenia celu kamery close")
    total = Vector((0.0, 0.0, 0.0))
    for obj in objects:
        total += obj.location
    return total / len(objects)


def main():
    args = parse_args()
    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    materials = cfg.get("material_presets", [])
    if not materials:
        raise SystemExit("BŁĄD: material_presets jest puste")
    ids = [m.get("id") for m in materials]
    if len(ids) != len(set(ids)) or any(not x for x in ids):
        raise SystemExit("BŁĄD: material IDs muszą być niepuste i unikalne")

    clear_scene()
    columns = min(5, len(materials))
    rows = math.ceil(len(materials) / columns)
    sample_objects = {}
    for i, spec in enumerate(materials):
        sample_objects[spec["id"]] = add_sample(spec, i, columns)
    add_floor(rows, columns)

    render_cfg = cfg["render_baseline"]
    engine = set_render_engine(render_cfg["engine_preference"])
    setup_world_and_lights(render_cfg)
    mins, maxs = scene_bounds()
    center = (mins + maxs) / 2.0
    size = max((maxs - mins).x, (maxs - mins).y, 8.0)
    lens = render_cfg["camera_lens_mm"]

    out_dir = os.path.dirname(args.out) or "."
    render_dir = os.path.dirname(args.renders) or "."
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(render_dir, exist_ok=True)

    cam_iso = add_camera("cam_iso", center + Vector((size * 0.78, -size * 0.82, size * 0.62)), center + Vector((0, 0, 0.45)), lens)
    cam_side = add_camera("cam_side", center + Vector((0, -size * 1.18, size * 0.20)), center + Vector((0, 0, 0.55)), lens)

    close_ids = ("brushed_metal", "painted_metal", "glass")
    missing_close = [mid for mid in close_ids if mid not in sample_objects]
    if missing_close:
        raise SystemExit("BŁĄD: brak materiałów wymaganych przez kamerę close: " + ", ".join(missing_close))
    close_target = average_location([sample_objects[mid] for mid in close_ids])
    cam_close = add_camera("cam_close", close_target + Vector((0.0, -7.6, 3.2)), close_target + Vector((0.0, 0.0, 0.15)), 50)

    bpy.ops.export_scene.gltf(filepath=args.out, export_format="GLB")
    if not os.path.isfile(args.out) or os.path.getsize(args.out) <= 1024:
        raise SystemExit(f"BŁĄD: eksport GLB nie powstał: {args.out}")

    res = render_cfg["resolution"]
    render(cam_iso, f"{args.renders}_iso.png", res)
    render(cam_side, f"{args.renders}_side.png", res)
    render(cam_close, f"{args.renders}_close.png", res)

    mesh_count = sum(1 for o in bpy.context.scene.objects if o.type == "MESH")
    print(f"[RAPORT] engine={engine}")
    print(f"[RAPORT] material_presets={len(materials)} mesh_objects={mesh_count}")
    print(f"[RAPORT] close_materials={','.join(close_ids)}")
    print(f"[RAPORT] bbox_min=({mins.x:.2f},{mins.y:.2f},{mins.z:.2f}) bbox_max=({maxs.x:.2f},{maxs.y:.2f},{maxs.z:.2f})")
    print(f"[RAPORT] glb={args.out} bytes={os.path.getsize(args.out)}")
    print("[RAPORT] manual inspection still required for iso/side/close PNG files")


if __name__ == "__main__":
    main()

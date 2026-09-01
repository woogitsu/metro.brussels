"""Deterministyczny render kontrolny wg canonical manifestu kamer (T-012).

Uruchamianie:

    blender --background --python-exit-code 7 --python tools/visual/capture_blender.py -- \
        --in build/M7_shell.glb --set vehicle --prefix M7_shell --out renders

Świadomie korzysta z `tools/blender/render_check.py` (świat, materiał kontrolny,
overlay siatki, odczyt osi trasy), żeby nie mieć dwóch różnych definicji sceny
kontrolnej. Kadrowanie liczy `tools/visual/framing.py` — bez bpy, więc testowalne.
"""
import argparse
import hashlib
import json
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import framing  # noqa: E402
import render_check as rc  # noqa: E402


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Render kontrolny wg manifestu kamer")
    parser.add_argument("--in", dest="inp", required=True, help="wejściowy GLB")
    parser.add_argument("--set", dest="scene_set", required=True, help="zestaw kamer z manifestu")
    parser.add_argument("--prefix", required=True, help="przedrostek nazw plików wyjściowych")
    parser.add_argument("--out", default="renders", help="katalog wyjściowy")
    parser.add_argument("--manifest", default=os.path.join(HERE, "cameras.json"))
    parser.add_argument("--centerline", help="oś trasy — źródło kotwic inside_eye/inside_target")
    parser.add_argument("--anchor", action="append", default=[],
                        help="jawna kotwica, np. --anchor door=12.5,0,1.8")
    parser.add_argument("--commit", default=os.environ.get("GITHUB_SHA", "local"))
    parser.add_argument("--wire-cameras", default="inside,section",
                        help="kamery z overlayem siatki (kontrola normalnych)")
    parser.add_argument("--test-shift", help="TYLKO test pipeline'u: przesuń geometrię o X,Y,Z metrów")
    return parser.parse_args(argv)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def apply_render_settings(scene, render_cfg, resolution):
    engine = render_cfg.get("engine", "BLENDER_EEVEE_NEXT")
    try:
        scene.render.engine = engine
    except Exception:
        engine = render_cfg.get("engine_fallback", "BLENDER_EEVEE")
        scene.render.engine = engine
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = bool(render_cfg.get("film_transparent", False))
    scene.render.dither_intensity = 0.0
    scene.render.use_motion_blur = bool(render_cfg.get("use_motion_blur", False))
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = render_cfg.get("color_mode", "RGB")
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15
    try:
        scene.view_settings.view_transform = render_cfg.get("view_transform", "Standard")
        scene.view_settings.look = render_cfg.get("look", "None")
    except Exception as exc:
        print(f"[WARN] color management nieustawione: {exc}")
    samples = int(render_cfg.get("samples", 32))
    if hasattr(scene, "eevee"):
        for attr in ("taa_render_samples", "taa_samples"):
            if hasattr(scene.eevee, attr):
                setattr(scene.eevee, attr, samples)
    if hasattr(scene, "cycles"):
        scene.cycles.samples = samples
        scene.cycles.seed = 0
        scene.cycles.use_denoising = False
    print(f"[RENDER] engine={engine} samples={samples} res={resolution[0]}x{resolution[1]} dither=0.0")
    return engine


def build_camera(solved, name):
    data = bpy.data.cameras.new(name)
    data.clip_start = solved["clip_start"]
    data.clip_end = solved["clip_end"]
    if solved["projection"] == "ORTHO":
        data.type = "ORTHO"
        data.ortho_scale = solved["ortho_scale"]
    else:
        data.type = "PERSP"
        data.lens = solved["lens"]
        data.sensor_fit = "AUTO"
        data.sensor_width = framing.SENSOR_MM
    cam = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(cam)
    cam.location = Vector(solved["location"])
    right = Vector(solved["right"])
    up = Vector(solved["up"])
    back = -Vector(solved["direction"])
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = Matrix((right, up, back)).transposed().to_quaternion()
    return cam


def named_anchors_from_args(args, vertices, scene_size):
    anchors = {}
    for item in args.anchor:
        if "=" not in item:
            raise SystemExit(f"BŁĄD: zła kotwica {item!r}, oczekiwano nazwa=X,Y,Z")
        name, raw = item.split("=", 1)
        parts = [float(v) for v in raw.split(",")]
        if len(parts) != 3:
            raise SystemExit(f"BŁĄD: kotwica {name} musi mieć trzy współrzędne")
        anchors[name.strip()] = parts
    if args.centerline:
        points = rc.load_centerline(args.centerline)
        eye = rc.point_on_centerline(points, 0.05)
        target = rc.point_on_centerline(points, 0.055)
        eye.z = rc.local_vertical_mid(vertices, eye.x, scene_size)
        target.z = rc.local_vertical_mid(vertices, target.x, scene_size)
        anchors.setdefault("inside_eye", [eye.x, eye.y, eye.z])
        anchors.setdefault("inside_target", [target.x, target.y, target.z])
        cut = rc.point_on_centerline(points, 0.5)
        ahead = rc.point_on_centerline(points, 0.505)
        cut.z = rc.local_vertical_mid(vertices, cut.x, scene_size)
        ahead.z = rc.local_vertical_mid(vertices, ahead.x, scene_size)
        anchors.setdefault("section_eye", [cut.x, cut.y, cut.z])
        anchors.setdefault("section_target", [ahead.x, ahead.y, ahead.z])
    return anchors


def main():
    args = parse_args()
    with open(args.manifest, encoding="utf-8") as handle:
        manifest = json.load(handle)
    if args.scene_set not in manifest["scene_sets"]:
        raise SystemExit(f"BŁĄD: zestaw {args.scene_set} nie istnieje w manifeście")
    scene_set = manifest["scene_sets"][args.scene_set]
    if not os.path.isfile(args.inp):
        raise SystemExit(f"BŁĄD: brak pliku wejściowego {args.inp}")

    rc.clear_scene()
    bpy.ops.import_scene.gltf(filepath=args.inp)
    rc.setup_world()
    rc.setup_verification_material()
    scene = bpy.context.scene
    engine = apply_render_settings(scene, manifest["render"], scene_set["resolution"])

    vertices = rc.mesh_world_vertices()
    mins, maxs = rc.scene_bounds(vertices)
    bmin = (mins.x, mins.y, mins.z)
    bmax = (maxs.x, maxs.y, maxs.z)
    scene_size = max(maxs.x - mins.x, maxs.y - mins.y, maxs.z - mins.z, 1.0)
    points = [(v.x, v.y, v.z) for v in vertices]
    anchors = named_anchors_from_args(args, vertices, scene_size)
    solved, skipped = framing.solve_set(manifest, args.scene_set, bmin, bmax, anchors, points)
    for entry in skipped:
        print(f"[SKIP] kamera {entry['id']}: {entry['reason']}")

    shifted_bbox = None
    if args.test_shift:
        # Kamery są już policzone. Przesunięcie PO kadrowaniu symuluje realną regresję
        # geometrii przy niezmienionym baseline; przesunięcie przed kadrowaniem byłoby
        # niewidoczne, bo kamera kadruje się względem bboxa i pojechałaby razem z modelem.
        offset = Vector([float(v) for v in args.test_shift.split(",")])
        for obj in rc.mesh_objects():
            obj.location = obj.location + offset
        bpy.context.view_layer.update()
        shifted = rc.mesh_world_vertices()
        smins, smaxs = rc.scene_bounds(shifted)
        shifted_bbox = [[round(c, 6) for c in (smins.x, smins.y, smins.z)],
                        [round(c, 6) for c in (smaxs.x, smaxs.y, smaxs.z)]]
        print(f"[TEST-SHIFT] geometria przesunięta o {tuple(offset)} po ustaleniu kamer — test pipeline'u")

    wire_ids = {c.strip() for c in args.wire_cameras.split(",") if c.strip()}
    if wire_ids & {c["id"] for c in solved}:
        rc.add_inside_wire_overlay()
        wire_objects = [o for o in rc.mesh_objects() if o.name.endswith("_verification_wire")]
    else:
        wire_objects = []

    os.makedirs(args.out, exist_ok=True)
    meshes = [o for o in rc.mesh_objects() if not o.name.endswith("_verification_wire")]
    records = []
    for cam_solved in solved:
        camera_id = cam_solved["id"]
        for obj in wire_objects:
            obj.hide_render = camera_id not in wire_ids
        cam = build_camera(cam_solved, f"cam_{camera_id}")
        path = os.path.join(args.out, f"{args.prefix}_{camera_id}.png")
        scene.camera = cam
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        record = dict(cam_solved)
        record["file"] = path
        record["bytes"] = os.path.getsize(path)
        record["sha256"] = sha256(path)
        record["wire_overlay"] = camera_id in wire_ids
        record["corner_visibility"] = round(framing.corner_visibility(cam_solved, bmin, bmax), 4)
        records.append(record)
        print(f"[RENDER] {path} bytes={record['bytes']} corner_visibility={record['corner_visibility']}")

    metadata = {
        "tool": "tools/visual/capture_blender.py",
        "manifest_version": manifest.get("manifest_version"),
        "scene_set": args.scene_set,
        "prefix": args.prefix,
        "commit": args.commit,
        "blender_version": bpy.app.version_string,
        "engine": engine,
        "resolution": scene_set["resolution"],
        "source_glb": {"path": args.inp, "sha256": sha256(args.inp), "bytes": os.path.getsize(args.inp)},
        "scene": {
            "bbox_min": [round(c, 6) for c in bmin],
            "bbox_max": [round(c, 6) for c in bmax],
            "size_m": [round(bmax[i] - bmin[i], 6) for i in range(3)],
            "mesh_objects": len(meshes),
            "vertices": sum(len(o.data.vertices) for o in meshes),
            "faces": sum(len(o.data.polygons) for o in meshes),
        },
        "anchors": anchors,
        "test_shift": args.test_shift,
        "test_shift_bbox": shifted_bbox,
        "cameras": records,
        "skipped": skipped,
    }
    meta_path = os.path.join(args.out, f"{args.prefix}_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)
    print(f"[METADATA] {meta_path}")
    print(f"[RAPORT] kamery={len(records)} pominięte={len(skipped)} "
          f"bbox={metadata['scene']['size_m']} wierzchołki={metadata['scene']['vertices']}")
    if not records:
        raise SystemExit("BŁĄD: żadna kamera nie została wyrenderowana")


if __name__ == "__main__":
    main()

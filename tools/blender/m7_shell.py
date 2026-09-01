"""Proceduralna bryła zewnętrzna M7 (T-220). Uruchamianie headless w Blenderze.

    blender --background --python-exit-code 7 --python tools/blender/m7_shell.py -- \
        --out build/M7_shell.glb --envelope-out build/M7_envelope.glb \
        --report build/M7_shell.json

Model powstaje w 100 % ze skryptu. Zero modelowania ręcznego.

Wymiary `spec` pochodzą wyłącznie z `data/vehicle/m7-spec.json`; wszystko inne to
jawne `design_assumption` z `m7_layout.py`. Bryła jest **techniczną skorupą**, nie
finalnym assetem: bez kabiny, wnętrza, wózków, podwozia, szyb, materiałów
finalnych i bez czegokolwiek objętego `docs/03-legal.md` — żadnych logo STIB/MIVB,
liverii, map sieci, piktogramów ani wzorów tapicerki.
"""
import argparse
import json
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profiles  # noqa: E402
from m7_layout import DESIGN_ASSUMPTIONS, DESIGN_SHELL_THICKNESS_M, Layout  # noqa: E402

NOSE_STEP_M = 0.20
BODY_STEP_M = 1.00
TOLERANCE_M = 0.001
VERTEX_EPS = 1e-4


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Proceduralna bryła zewnętrzna M7")
    parser.add_argument("--out", default="build/M7_shell.glb")
    parser.add_argument("--envelope-out", default="build/M7_envelope.glb")
    parser.add_argument("--report", default="build/M7_shell.json")
    parser.add_argument("--spec", default=None, help="ścieżka do canonical registry M7")
    parser.add_argument("--skip-roundtrip", action="store_true",
                        help="pomiń kontrolny re-import GLB (tylko do debugowania)")
    return parser.parse_args(argv)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.objects):
        for item in list(block):
            if not item.users:
                block.remove(item)


def neutral_material():
    """Neutralny materiał techniczny. Bez liverii, logo i wzorów — docs/03-legal.md."""
    existing = bpy.data.materials.get("M7_neutral_shell")
    if existing:
        return existing
    material = bpy.data.materials.new("M7_neutral_shell")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.55, 0.57, 0.60, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.65
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
    return material


def x_stations(layout, start, end, taper_aware=True):
    """Punkty podziału wzdłuż X: gęściej tam, gdzie przekrój się zmienia."""
    stations = {round(start, 6), round(end, 6)}
    span = end - start
    steps = max(1, int(math.ceil(span / BODY_STEP_M)))
    for i in range(steps + 1):
        stations.add(round(start + span * i / steps, 6))
    if taper_aware:
        from m7_layout import DESIGN_NOSE_LENGTH_M
        for nose_end in (DESIGN_NOSE_LENGTH_M, layout.length - DESIGN_NOSE_LENGTH_M):
            if start - 1e-9 <= nose_end <= end + 1e-9:
                stations.add(round(nose_end, 6))
        nose_steps = int(math.ceil(DESIGN_NOSE_LENGTH_M / NOSE_STEP_M))
        for i in range(nose_steps + 1):
            for candidate in (DESIGN_NOSE_LENGTH_M * i / nose_steps,
                              layout.length - DESIGN_NOSE_LENGTH_M * i / nose_steps):
                if start - 1e-9 <= candidate <= end + 1e-9:
                    stations.add(round(candidate, 6))
    return sorted(stations)


def build_tube(name, layout, start, end, extra_inset=0.0, taper_aware=True):
    """Zamknięta skorupa zbudowana z pierścieni przekroju wzdłuż X."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    rings = []
    for x in x_stations(layout, start, end, taper_aware):
        section = layout.section(x, extra_inset)
        rings.append([bm.verts.new((x, y, z)) for y, z in section])
    bm.verts.ensure_lookup_table()

    count = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for i in range(count):
            j = (i + 1) % count
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.contextual_create(bm, geom=rings[0])
    bmesh.ops.contextual_create(bm, geom=rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(neutral_material())
    return obj


def solidify(obj, thickness=DESIGN_SHELL_THICKNESS_M):
    """Nadaje skorupie grubość do wewnątrz — inaczej otwór drzwiowy byłby wnęką."""
    bpy.context.view_layer.objects.active = obj
    modifier = obj.modifiers.new("shell", "SOLIDIFY")
    modifier.thickness = thickness
    modifier.offset = -1.0  # grubość narasta do wewnątrz; lico zewnętrzne = wymiar spec
    modifier.use_even_offset = True
    bpy.ops.object.modifier_apply(modifier="shell")
    return obj


def door_cutter(layout, doors, name):
    """Jedna siatka tnąca na człon: prostopadłościany dokładnie na otwory."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    margin = DESIGN_SHELL_THICKNESS_M + 0.05
    for door in doors:
        side = door["side"]
        y_outer = side * (layout.half_width + 0.05)
        y_inner = side * (layout.half_width - margin)
        y0, y1 = sorted((y_inner, y_outer))
        corners = [(door["x0"], y0, door["z0"]), (door["x1"], y0, door["z0"]),
                   (door["x1"], y1, door["z0"]), (door["x0"], y1, door["z0"]),
                   (door["x0"], y0, door["z1"]), (door["x1"], y0, door["z1"]),
                   (door["x1"], y1, door["z1"]), (door["x0"], y1, door["z1"])]
        verts = [bm.verts.new(c) for c in corners]
        faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        for face in faces:
            bm.faces.new([verts[i] for i in face])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return obj


def cut_doors(obj, cutter):
    bpy.context.view_layer.objects.active = obj
    modifier = obj.modifiers.new("doors", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.object = cutter
    if hasattr(modifier, "solver"):
        modifier.solver = "EXACT"
    bpy.ops.object.modifier_apply(modifier="doors")
    bpy.data.objects.remove(cutter, do_unlink=True)


def world_vertices(objects):
    out = []
    for obj in objects:
        matrix = obj.matrix_world
        out.extend(matrix @ v.co for v in obj.data.vertices)
    return out


def bounds(vertices):
    return ((min(v.x for v in vertices), min(v.y for v in vertices), min(v.z for v in vertices)),
            (max(v.x for v in vertices), max(v.y for v in vertices), max(v.z for v in vertices)))


def build_shell(layout):
    """Sześć członów + pięć przegubów, z wyciętymi otworami drzwiowymi."""
    doors = layout.all_doors()
    cars = []
    for index in range(layout.cars):
        start, end = layout.car_body_span(index)
        car = build_tube(f"M7_car_{index + 1}", layout, start, end)
        solidify(car)
        car_doors = [d for d in doors if d["car"] == index]
        if car_doors:
            cut_doors(car, door_cutter(layout, car_doors, f"cutter_{index + 1}"))
        cars.append(car)

    joints = []
    for index, (start, end) in enumerate(layout.articulation_spans()):
        from m7_layout import DESIGN_ARTICULATION_INSET_M
        joint = build_tube(f"M7_articulation_{index + 1}", layout, start, end,
                           extra_inset=DESIGN_ARTICULATION_INSET_M)
        solidify(joint)
        joints.append(joint)
    return cars, joints


def build_envelope(layout, name="M7_clearance_envelope"):
    """Uproszczona skrajnia pojazdu do testów kolizji — osobny plik, nie część bryły."""
    gauge = profiles.vehicle_gauge(clearance=0.0)
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    rings = []
    for x in (0.0, layout.length):
        rings.append([bm.verts.new((x, y, z)) for y, z in gauge])
    count = len(rings[0])
    for i in range(count):
        j = (i + 1) % count
        bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
    bmesh.ops.contextual_create(bm, geom=rings[0])
    bmesh.ops.contextual_create(bm, geom=rings[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(neutral_material())
    return obj


# --- weryfikacja --------------------------------------------------------------

def check_no_nan(vertices):
    for v in vertices:
        for component in (v.x, v.y, v.z):
            if math.isnan(component) or math.isinf(component):
                return False
    return True


def measure_openings(layout, objects):
    """Mierzy rzeczywistą szerokość otworów w wygenerowanej geometrii, nie w parametrach."""
    by_x = {}
    for obj in objects:
        matrix = obj.matrix_world
        for vertex in obj.data.vertices:
            point = matrix @ vertex.co
            if abs(abs(point.y) - layout.half_width) > VERTEX_EPS:
                continue
            key = (round(point.x, 4), 1 if point.y > 0 else -1)
            by_x.setdefault(key, []).append(round(point.z, 4))

    measured = []
    for door in layout.all_doors():
        side = door["side"]
        left = by_x.get((round(door["x0"], 4), side), [])
        right = by_x.get((round(door["x1"], 4), side), [])
        has_bottom = any(abs(z - door["z0"]) <= VERTEX_EPS for z in left + right)
        has_top = any(abs(z - door["z1"]) <= VERTEX_EPS for z in left + right)
        measured.append({
            "kind": door["kind"],
            "car": door["car"],
            "side": side,
            "center_x": door["center_x"],
            "edges_found": bool(left) and bool(right),
            "corners_found": has_bottom and has_top,
            "measured_width_m": round(door["x1"] - door["x0"], 6) if left and right else None,
            "measured_height_m": round(door["z1"] - door["z0"], 6) if has_bottom and has_top else None,
        })
    return measured


def verify(layout, cars, joints, report):
    problems = []
    body = cars + joints
    vertices = world_vertices(body)
    bmin, bmax = bounds(vertices)
    size = [bmax[i] - bmin[i] for i in range(3)]
    report["body"] = {
        "bbox_min": [round(c, 6) for c in bmin],
        "bbox_max": [round(c, 6) for c in bmax],
        "size_m": [round(c, 6) for c in size],
        "objects": len(body),
        "cars": len(cars),
        "articulations": len(joints),
        "vertices": sum(len(o.data.vertices) for o in body),
        "faces": sum(len(o.data.polygons) for o in body),
        "object_names": [o.name for o in body],
    }

    if abs(size[0] - layout.length) > TOLERANCE_M:
        problems.append(f"długość {size[0]:.6f} m != {layout.length} m")
    if abs(size[1] - layout.width) > TOLERANCE_M:
        problems.append(f"szerokość {size[1]:.6f} m != {layout.width} m")
    if abs(bmin[0]) > TOLERANCE_M or abs(bmax[0] - layout.length) > TOLERANCE_M:
        problems.append(f"origin/zasięg X = [{bmin[0]:.6f}, {bmax[0]:.6f}]")
    if abs(bmax[2] - layout.roof_z) > TOLERANCE_M:
        problems.append(f"wysokość dachu {bmax[2]:.6f} m != {layout.roof_z} m")
    if abs(bmin[2] - layout.body_bottom_z) > TOLERANCE_M:
        problems.append(f"spód pudła {bmin[2]:.6f} m != {layout.body_bottom_z} m")
    if len(cars) != layout.cars:
        problems.append(f"członów {len(cars)} != {layout.cars}")
    if not check_no_nan(vertices):
        problems.append("geometria zawiera NaN/Inf")
    if not 1000 < report["body"]["vertices"] < 500000:
        problems.append(f"podejrzana liczba wierzchołków: {report['body']['vertices']}")
    for obj in body:
        dims = obj.dimensions
        if max(dims) > layout.length + 1.0 or max(dims) <= 0.0:
            problems.append(f"absurdalna skala obiektu {obj.name}: {tuple(round(d, 3) for d in dims)}")

    openings = measure_openings(layout, body)
    report["openings"] = openings
    doubles = [o for o in openings if o["kind"] == "double"]
    cabs = [o for o in openings if o["kind"] == "cab"]
    report["opening_summary"] = {
        "double_total": len(doubles),
        "double_per_side": len(doubles) // 2,
        "cab_total": len(cabs),
        "double_edges_found": sum(1 for o in doubles if o["edges_found"]),
        "double_corners_found": sum(1 for o in doubles if o["corners_found"]),
        "cab_edges_found": sum(1 for o in cabs if o["edges_found"]),
    }
    if len(doubles) // 2 != layout.doors_per_side:
        problems.append(f"drzwi podwójnych na stronę {len(doubles) // 2} != {layout.doors_per_side}")
    if len(cabs) != layout.cab_doors:
        problems.append(f"drzwi kabinowych {len(cabs)} != {layout.cab_doors}")
    for opening in openings:
        if not opening["edges_found"] or not opening["corners_found"]:
            problems.append(f"otwór {opening['kind']} x={opening['center_x']} strona {opening['side']}"
                            " nie ma krawędzi w geometrii")
        elif opening["kind"] == "double" and abs(opening["measured_width_m"] - layout.door_width) > TOLERANCE_M:
            problems.append(f"otwór x={opening['center_x']}: zmierzone {opening['measured_width_m']} m")

    # Skład jest dwukierunkowy: bryła musi być niezmiennicza na obrót 180 stopni
    # wokół środka pojazdu. To łapie błędy generatora, których nie widać na renderze,
    # bo cieniowanie i tak jest asymetryczne.
    keys = {(round(v.x, 4), round(v.y, 4), round(v.z, 4)) for v in vertices}
    rotated = {(round(layout.length - x, 4), round(-y, 4), z) for x, y, z in keys}
    missing = keys - rotated
    report["rotational_symmetry"] = {
        "vertices": len(keys),
        "mismatched": len(missing),
        "ok": not missing,
        "rule": "(x, y, z) -> (94 - x, -y, z)",
    }
    if missing:
        problems.append(f"bryła nie jest symetryczna obrotowo: {len(missing)} z {len(keys)} wierzchołków")

    gauge_ok, gauge_message = layout.fits_vehicle_gauge()
    tunnel = layout.fits_tunnel_profiles()
    report["gauge"] = {"vehicle_gauge_ok": gauge_ok, "vehicle_gauge_message": gauge_message, "tunnel_profiles": tunnel}
    if not gauge_ok:
        problems.append(f"skrajnia pojazdu: {gauge_message}")
    for name, entry in tunnel.items():
        if not entry["ok"]:
            problems.append(f"profil {name}: {entry['message']}")
    return problems


def export(objects, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True)
    return {"path": path, "bytes": os.path.getsize(path)}


def roundtrip(path, expected_objects, expected_bbox):
    """Eksport i ponowny import muszą dać tę samą geometrię."""
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    vertices = world_vertices(meshes)
    bmin, bmax = bounds(vertices)
    deltas = [round(bmin[i] - expected_bbox[0][i], 6) for i in range(3)] + \
             [round(bmax[i] - expected_bbox[1][i], 6) for i in range(3)]
    result = {
        "objects": len(meshes),
        "expected_objects": expected_objects,
        "bbox_min": [round(c, 6) for c in bmin],
        "bbox_max": [round(c, 6) for c in bmax],
        "max_delta_m": max(abs(d) for d in deltas),
        "names": sorted(o.name for o in meshes),
    }
    result["ok"] = result["objects"] == expected_objects and result["max_delta_m"] <= TOLERANCE_M
    return result


def main():
    args = parse_args()
    layout = Layout(spec=None) if args.spec is None else Layout(spec=None)
    if args.spec:
        from m7_layout import load_spec
        layout = Layout(load_spec(args.spec))

    clear_scene()
    cars, joints = build_shell(layout)

    report = {
        "tool": "tools/blender/m7_shell.py",
        "blender_version": bpy.app.version_string,
        "spec_source": {"id": layout.spec["source_id"], "url": layout.spec["source_url"]},
        "spec_values": {k: v for k, v in layout.spec.items() if k not in ("source_id", "source_url")},
        "design_assumptions": {k: {"value": v[0], "reason": v[1]} for k, v in DESIGN_ASSUMPTIONS.items()},
        "layout": layout.summary(),
    }
    problems = verify(layout, cars, joints, report)

    body_bbox = (report["body"]["bbox_min"], report["body"]["bbox_max"])
    report["exports"] = {"shell": export(cars + joints, args.out)}

    envelope = build_envelope(layout)
    report["exports"]["envelope"] = export([envelope], args.envelope_out)
    envelope_vertices = world_vertices([envelope])
    emin, emax = bounds(envelope_vertices)
    report["envelope"] = {
        "bbox_min": [round(c, 6) for c in emin],
        "bbox_max": [round(c, 6) for c in emax],
        "size_m": [round(emax[i] - emin[i], 6) for i in range(3)],
        "source": "profiles.vehicle_gauge(clearance=0.0)",
    }
    for axis, label in ((1, "szerokość"), (2, "wysokość")):
        if emax[axis] + 1e-6 < body_bbox[1][axis] or emin[axis] - 1e-6 > body_bbox[0][axis]:
            problems.append(f"skrajnia nie obejmuje bryły w osi {label}")

    if not args.skip_roundtrip:
        report["roundtrip"] = roundtrip(args.out, len(cars) + len(joints), body_bbox)
        if not report["roundtrip"]["ok"]:
            problems.append(f"re-import GLB niezgodny: {report['roundtrip']}")

    report["problems"] = problems
    report["ok"] = not problems
    os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    body = report["body"]
    print(f"[RAPORT] plik={args.out} ({report['exports']['shell']['bytes']} B)")
    print(f"[RAPORT] skrajnia={args.envelope_out} ({report['exports']['envelope']['bytes']} B)")
    print(f"[RAPORT] wymiary_m: X={body['size_m'][0]:.6f} Y={body['size_m'][1]:.6f} Z={body['size_m'][2]:.6f}")
    print(f"[RAPORT] bbox_min={body['bbox_min']} bbox_max={body['bbox_max']}")
    print(f"[RAPORT] obiekty={body['objects']} (członów={body['cars']}, przegubów={body['articulations']})")
    print(f"[RAPORT] wierzcholki={body['vertices']} sciany={body['faces']}")
    print(f"[RAPORT] drzwi podwójne: {report['opening_summary']['double_per_side']}/stronę, "
          f"krawędzie zmierzone: {report['opening_summary']['double_edges_found']}/"
          f"{report['opening_summary']['double_total']}")
    print(f"[RAPORT] drzwi kabinowe: {report['opening_summary']['cab_total']}")
    print(f"[RAPORT] skrajnia pojazdu: {report['gauge']['vehicle_gauge_message']}")
    for name, entry in report["gauge"]["tunnel_profiles"].items():
        print(f"[RAPORT]   profil {name}: {'OK' if entry['ok'] else entry['message']} "
              f"luz_max={entry['min_clearance_m']:.2f} m")
    print(f"[RAPORT] symetria obrotowa 180°: {report['rotational_symmetry']['mismatched']} "
          f"niezgodnych z {report['rotational_symmetry']['vertices']} wierzchołków")
    if "roundtrip" in report:
        print(f"[RAPORT] re-import GLB: obiekty={report['roundtrip']['objects']} "
              f"max_delta={report['roundtrip']['max_delta_m']} m ok={report['roundtrip']['ok']}")
    print(f"[RAPORT] json={args.report}")

    if problems:
        for problem in problems:
            print(f"BŁĄD: {problem}", file=sys.stderr)
        raise SystemExit("BŁĄD: bryła nie przeszła własnej weryfikacji")
    print("[RAPORT] wszystkie kontrole geometryczne przeszły")


if __name__ == "__main__":
    main()

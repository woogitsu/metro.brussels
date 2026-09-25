"""Proceduralna bryła zewnętrzna M7 (T-220). Uruchamianie headless w Blenderze.

    blender --background --python-exit-code 7 --python tools/blender/m7_shell.py -- \
        --out build/M7_shell.glb --envelope-out build/M7_envelope.glb \
        --report build/M7_shell.json

Model powstaje w 100 % ze skryptu. Zero modelowania ręcznego.

Wymiary `spec` pochodzą wyłącznie z `data/vehicle/m7-spec.json`; wszystko inne to
jawne `design_assumption` z `m7_layout.py`. Bryła jest **techniczną skorupą**, nie
finalnym assetem: bez kabiny, wnętrza, wózków, podwozia, przezroczystych szyb i materiałów
finalnych i bez czegokolwiek objętego `docs/03-legal.md` — żadnych logo STIB/MIVB,
liverii, map sieci, piktogramów ani wzorów tapicerki.
"""
import argparse
import json
import os
import sys

import bpy
import bmesh
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profiles  # noqa: E402
import m7_report as RP  # noqa: E402
from m7_layout import (DESIGN_ASSUMPTIONS, DESIGN_SHELL_THICKNESS_M,
                       DESIGN_WINDOW_BAND_BOTTOM_M, DESIGN_WINDOW_BAND_TOP_M,
                       Layout)  # noqa: E402


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


def dark_panel_material():
    """Własny, neutralny panel końcowy i mieszek; bez znaków i tekstur."""
    existing = bpy.data.materials.get("M7_neutral_dark_panel")
    if existing:
        return existing
    material = bpy.data.materials.new("M7_neutral_dark_panel")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.115, 0.135, 0.155, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.75
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
    return material


def window_band_material():
    """Własny ciemny pas okienny; kryjący, bez grafiki i przezroczystości."""
    existing = bpy.data.materials.get("M7_neutral_window_band")
    if existing:
        return existing
    material = bpy.data.materials.new("M7_neutral_window_band")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.08, 0.15, 0.19, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.32
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
    return material


def end_cap_with_panel(bm, ring):
    """Wpuszczony neutralny panel czołowy, bez zmiany skrajni ani liczby brył."""
    cap = bmesh.ops.contextual_create(bm, geom=ring)["faces"][0]
    bmesh.ops.inset_region(bm, faces=[cap], thickness=0.18, depth=0.0)
    cap.material_index = 1


def build_tube(name, layout, start, end, extra_inset=0.0, taper_aware=True,
               dark_start=False, dark_end=False, dark_body=False,
               window_band=False, window_dividers=()):
    """Zamknięta skorupa zbudowana z pierścieni przekroju wzdłuż X."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    rings = []
    stations = set(RP.x_stations(layout, start, end, taper_aware))
    for x0, x1 in window_dividers:
        stations.update((x0, x1))
    for x in sorted(stations):
        section = layout.section(x, extra_inset)
        if window_band:
            # Rozbij tylko istniejące pionowe lica boków: materiał nie wystaje
            # poza podaną w specyfikacji szerokość ani nie dodaje nowej bryły.
            right, left = section[1], section[-1]
            section = [section[0], right,
                       (right[0], DESIGN_WINDOW_BAND_BOTTOM_M),
                       (right[0], DESIGN_WINDOW_BAND_TOP_M),
                       *section[2:-1], left,
                       (left[0], DESIGN_WINDOW_BAND_TOP_M),
                       (left[0], DESIGN_WINDOW_BAND_BOTTOM_M)]
        rings.append([bm.verts.new((x, y, z)) for y, z in section])
    bm.verts.ensure_lookup_table()

    count = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        mid_x = (a[0].co.x + b[0].co.x) / 2.0
        divider = any(x0 <= mid_x <= x1 for x0, x1 in window_dividers)
        for i in range(count):
            j = (i + 1) % count
            face = bm.faces.new((a[i], a[j], b[j], b[i]))
            if window_band and not divider and i in (2, 8):
                face.material_index = 2 if dark_start or dark_end else 1
    if dark_start:
        end_cap_with_panel(bm, rings[0])
    else:
        bmesh.ops.contextual_create(bm, geom=rings[0])
    if dark_end:
        end_cap_with_panel(bm, rings[-1])
    else:
        bmesh.ops.contextual_create(bm, geom=rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(dark_panel_material() if dark_body else neutral_material())
    if dark_start or dark_end:
        mesh.materials.append(dark_panel_material())
    if window_band:
        mesh.materials.append(window_band_material())
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


def mesh_records(objects):
    """Wszystko, czego pomiar i bramka potrzebują od Blendera — i nic ponadto.

    To jest CAŁA granica między bpy a `m7_report.py`. Wierzchołki idą dalej już
    w układzie świata, bo przemnożenie przez `matrix_world` jest jedyną rzeczą
    w tym kroku, której bez Blendera zrobić się nie da.
    """
    return [{"name": obj.name,
             "vertices": [tuple(obj.matrix_world @ v.co) for v in obj.data.vertices],
             "faces": len(obj.data.polygons),
             "dimensions": tuple(obj.dimensions)}
            for obj in objects]


def build_shell(layout):
    """Sześć członów + pięć przegubów, z wyciętymi otworami drzwiowymi."""
    doors = layout.all_doors()
    cars = []
    for index in range(layout.cars):
        start, end = layout.car_body_span(index)
        car = build_tube(f"M7_car_{index + 1}", layout, start, end,
                         dark_start=index == 0, dark_end=index == layout.cars - 1,
                         window_band=True,
                         window_dividers=layout.window_divider_spans(index))
        solidify(car)
        car_doors = [d for d in doors if d["car"] == index]
        if car_doors:
            cut_doors(car, door_cutter(layout, car_doors, f"cutter_{index + 1}"))
        cars.append(car)

    joints = []
    for index, (start, end) in enumerate(layout.articulation_spans()):
        from m7_layout import DESIGN_ARTICULATION_INSET_M
        joint = build_tube(f"M7_articulation_{index + 1}", layout, start, end,
                           extra_inset=DESIGN_ARTICULATION_INSET_M, dark_body=True)
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
    return RP.roundtrip_result(mesh_records(meshes), expected_objects, expected_bbox)


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
    problems = RP.verify(layout, mesh_records(cars), mesh_records(joints), report)

    body_bbox = (report["body"]["bbox_min"], report["body"]["bbox_max"])
    report["exports"] = {"shell": export(cars + joints, args.out)}

    envelope = build_envelope(layout)
    report["exports"]["envelope"] = export([envelope], args.envelope_out)
    emin, emax = RP.bounds(RP.all_points(mesh_records([envelope])))
    report["envelope"] = {
        "bbox_min": [round(c, 6) for c in emin],
        "bbox_max": [round(c, 6) for c in emax],
        "size_m": [round(emax[i] - emin[i], 6) for i in range(3)],
        "source": "profiles.vehicle_gauge(clearance=0.0)",
    }
    problems.extend(RP.envelope_problems((emin, emax), body_bbox))

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

"""Wczytuje wyeksportowany GLB z powrotem do Blendera i sprawdza, czy geometria ocalała.

    blender --background --python tools/blender/glb_roundtrip.py -- \
        --in build/L1_A.glb --expect-objects 12 --expect-metrics build/L1_A-metrics.json

„Eksport nie zgłosił błędu" nie jest dowodem, że plik da się wczytać: pusty mesh,
zerowa skala i utracone UV eksportują się bez ani jednego ostrzeżenia.
"""
import argparse
import json
import math
import os
import sys

import bpy

TOLERANCE_M = 0.01
COUNT_TOLERANCE = 0.10


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Kontrola round-trip GLB")
    parser.add_argument("--in", dest="inp", required=True)
    parser.add_argument("--expect-objects", type=int)
    parser.add_argument("--expect-metrics", help="metryki generatora do porównania bboxa")
    parser.add_argument("--out", help="ścieżka na wynik JSON")
    parser.add_argument("--allow-missing-uv", action="store_true",
                        help="nie wymagaj UV; tunel ich wymaga, skorupa M7 na tym etapie nie ma")
    return parser.parse_args(argv)


def main():
    args = parse_args()
    if not os.path.isfile(args.inp):
        raise SystemExit(f"BŁĄD: brak pliku {args.inp}")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=args.inp)

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit("BŁĄD: po ponownym imporcie nie ma ani jednego mesha")
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    vertices = faces = 0
    without_uv = []
    for obj in meshes:
        vertices += len(obj.data.vertices)
        faces += len(obj.data.polygons)
        if not obj.data.uv_layers:
            without_uv.append(obj.name)
        for corner in obj.bound_box:
            world = obj.matrix_world @ type(obj.location)(corner)
            for i in range(3):
                lo[i] = min(lo[i], world[i])
                hi[i] = max(hi[i], world[i])
    for value in lo + hi:
        if math.isnan(value) or math.isinf(value):
            raise SystemExit("BŁĄD: bbox po imporcie zawiera NaN/Inf")

    result = {
        "file": args.inp,
        "bytes": os.path.getsize(args.inp),
        "objects": len(meshes),
        "vertices": vertices,
        "faces": faces,
        "bbox_min_m": [round(v, 4) for v in lo],
        "bbox_max_m": [round(v, 4) for v in hi],
        "bbox_size_m": [round(hi[i] - lo[i], 4) for i in range(3)],
        "objects_without_uv": without_uv,
    }
    print(f"[ROUNDTRIP] obiekty={result['objects']} wierzcholki={vertices} sciany={faces}")
    print(f"[ROUNDTRIP] bbox_m: {result['bbox_size_m']}")

    problems = []
    if vertices == 0 or faces == 0:
        problems.append("geometria pusta po imporcie")
    if without_uv and not args.allow_missing_uv:
        problems.append(f"obiekty bez UV: {without_uv}")
    if args.expect_objects is not None and len(meshes) != args.expect_objects:
        problems.append(f"obiektów {len(meshes)}, oczekiwano {args.expect_objects}")
    if args.expect_metrics:
        with open(args.expect_metrics, encoding="utf-8") as handle:
            expected = json.load(handle)
        result["expected_bbox_size_m"] = expected["bbox_size_m"]
        for i, axis in enumerate("XYZ"):
            delta = abs(result["bbox_size_m"][i] - expected["bbox_size_m"][i])
            if delta > TOLERANCE_M:
                problems.append(f"bbox {axis} rozjazd {delta:.4f} m > {TOLERANCE_M} m")
        # eksport glTF rozszczepia wierzchołki na szwach UV — porównujemy rząd wielkości
        allowed = max(1.0, expected["vertices"] * (1.0 + COUNT_TOLERANCE))
        if vertices < expected["vertices"] or vertices > allowed * 4:
            problems.append(f"wierzchołków {vertices}, generator zgłosił {expected['vertices']}")
        if faces < expected["faces"]:
            problems.append(f"ścian {faces} < {expected['faces']} zgłoszonych przez generator")

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    if problems:
        raise SystemExit("BŁĄD: " + "; ".join(problems))
    print("[ROUNDTRIP] OK")


if __name__ == "__main__":
    main()

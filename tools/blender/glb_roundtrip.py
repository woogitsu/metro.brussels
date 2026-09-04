"""Wczytuje wyeksportowany GLB z powrotem do Blendera i sprawdza, czy geometria ocalała.

    blender --background --python tools/blender/glb_roundtrip.py -- \
        --in build/L1_A.glb --expect-objects 12 --expect-metrics build/L1_A-metrics.json

„Eksport nie zgłosił błędu" nie jest dowodem, że plik da się wczytać: pusty mesh,
zerowa skala i utracone UV eksportują się bez ani jednego ostrzeżenia.
"""
import argparse
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb_report as GR  # noqa: E402

# Progi i cały werdykt siedzą w `glb_report.py`, bo tamten moduł da się
# zaimportować bez Blendera, a ten nie. Tu zostaje wyłącznie to, co bez `bpy`
# nie ma sensu: czyszczenie sceny, import glTF i chodzenie po obiektach.


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
    vertices = faces = 0
    without_uv = []
    corner_groups = []
    for obj in meshes:
        vertices += len(obj.data.vertices)
        faces += len(obj.data.polygons)
        if not obj.data.uv_layers:
            without_uv.append(obj.name)
        corner_groups.append([obj.matrix_world @ type(obj.location)(corner)
                              for corner in obj.bound_box])
    lo, hi = GR.bbox_from_corners(corner_groups)
    if not GR.finite_bbox(lo, hi):
        raise SystemExit("BŁĄD: bbox po imporcie zawiera NaN/Inf")
    size_m = GR.bbox_size(lo, hi)

    result = {
        "file": args.inp,
        "bytes": os.path.getsize(args.inp),
        "objects": len(meshes),
        "vertices": vertices,
        "faces": faces,
        "bbox_min_m": [round(v, 4) for v in lo],
        "bbox_max_m": [round(v, 4) for v in hi],
        "bbox_size_m": [round(v, 4) for v in size_m],
        "objects_without_uv": without_uv,
    }
    print(f"[ROUNDTRIP] obiekty={result['objects']} wierzcholki={vertices} sciany={faces}")
    print(f"[ROUNDTRIP] bbox_m: {result['bbox_size_m']}")

    expected = None
    if args.expect_metrics:
        with open(args.expect_metrics, encoding="utf-8") as handle:
            expected = json.load(handle)
        result["expected_bbox_size_m"] = expected["bbox_size_m"]
    # Do bramki idą rozmiary ZAOKRĄGLONE, dokładnie jak przed wydzieleniem. Surowe
    # byłyby precyzyjniejsze i to jest ta sama rodzina, co znalezisko z #153
    # (porównywanie surowych odległości zamiast zaokrąglonych) — ale to decyzja
    # o zachowaniu bramki, a nie o jej rozmieszczeniu, i nie należy do tego zadania.
    problems = GR.roundtrip_problems(
        objects=len(meshes), vertices=vertices, faces=faces, without_uv=without_uv,
        size_m=result["bbox_size_m"], expect_objects=args.expect_objects,
        expected=expected, allow_missing_uv=args.allow_missing_uv)

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

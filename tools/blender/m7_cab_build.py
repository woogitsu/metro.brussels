"""Generator brył kabiny kanonicznej (6.D119). Uruchamianie headless w Blenderze.

    blender --background --python-exit-code 7 --python tools/blender/m7_cab_build.py -- \
        --out build/M7_cab.glb --report build/M7_cab.json

Model powstaje w 100 % ze skryptu. Zero modelowania ręcznego.

**Ten plik nie liczy ani jednego wymiaru.** Cała geometria przychodzi z `m7_cab.py`,
który nie importuje `bpy` i daje się sprawdzić bez Blendera — tak samo jak
`station_components.py` wobec `station_kit.py`. Tutaj zostaje zamiana pudełek na
siatki, eksport i zapis raportu.

Układ jest KANONICZNY i nie jest kabiną M7; zdanie o tym jedzie w raporcie obok
geometrii, a nie tylko w dokumentacji.
"""
import argparse
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m7_cab  # noqa: E402
import m7_layout  # noqa: E402

def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Bryły kabiny kanonicznej M7")
    parser.add_argument("--out", default="build/M7_cab.glb")
    parser.add_argument("--report", default="build/M7_cab.json")
    parser.add_argument("--end", type=int, choices=(0, 1),
                        help="zbuduj tylko tę kabinę; bez tego obie")
    return parser.parse_args(argv)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.objects):
        for item in list(block):
            block.remove(item)


def build_box(box):
    mesh = bpy.data.meshes.new(box["name"])
    mesh.from_pydata(m7_cab.verts(box), [], [list(f) for f in m7_cab.FACES])
    mesh.validate()
    obj = bpy.data.objects.new(box["name"], mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def export(objects, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True)
    return {"path": path, "bytes": os.path.getsize(path)}


def main():
    args = parse_args()
    layout = m7_layout.Layout()
    kabiny = m7_cab.both_cabs(layout)
    if args.end is not None:
        kabiny = [k for k in kabiny if k.end == args.end]

    clear_scene()
    bryly = [b for cab in kabiny for b in cab.solids()]
    objects = [build_box(b) for b in bryly]
    if not objects:
        print("[KABINA] BŁĄD: zero brył do zbudowania", file=sys.stderr)
        return 7

    wynik = export(objects, args.out)

    raport = m7_cab.report(layout)
    raport["built"] = {"objects": len(objects),
                       "ends": sorted(k.end for k in kabiny),
                       "glb": wynik}
    os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as handle:
        json.dump(raport, handle, ensure_ascii=False, indent=1)

    print(f"[KABINA] brył={len(objects)} otworów={len(raport['openings'])} "
          f"-> {wynik['path']} ({wynik['bytes']} B)")
    print(f"[KABINA] UKŁAD KANONICZNY, NIE kabina M7: {raport['not_modelled'][-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

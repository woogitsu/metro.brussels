#!/usr/bin/env python3
"""Generate one neutral, unit-width station name plate for runtime text markers.

    blender --background --python-exit-code 7 --python tools/blender/station_board.py -- \
        --out build/L1_A-station-board.glb

The runtime scales the plate across its width to fit the complete station name.
The material and wording are applied by Godot; this GLB contains only geometry.
"""
import argparse
import os
import sys

import bpy


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Neutral station name plate")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    # Blender is Z-up. glTF maps this to Godot's Y-up; the 4 cm depth becomes Z.
    verts = [(x, y, z) for z in (-0.5, 0.5) for y in (-0.02, 0.02)
             for x in (-0.5, 0.5)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
             (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    mesh = bpy.data.meshes.new("StationNamePlate")
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    obj = bpy.data.objects.new("StationNamePlate", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format="GLB")
    print(f"[STACJA] neutralna tablica: 8 wierzcholkow, 12 trojkatow -> {out}")


if __name__ == "__main__":
    main()

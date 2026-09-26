"""Combine procedural tunnel and station assets for a four-camera geometry review."""

import argparse
import os
import sys

import bpy


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--tunnel", required=True)
    parser.add_argument("--station", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for path in (args.tunnel, args.station):
        bpy.ops.import_scene.gltf(filepath=path)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise SystemExit("BŁĄD: po złożeniu scena nie zawiera siatki")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=args.out, use_selection=True, export_format="GLB")
    print(f"[SCENA STACJI] {len(meshes)} siatek -> {args.out}")


if __name__ == "__main__":
    main()

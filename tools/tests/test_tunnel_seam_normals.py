"""Run with Blender: blender -b --python tools/tests/test_tunnel_seam_normals.py."""
import json
import math
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "blender"))
import bpy
import lod as LD
import sweep as SW
import tunnel_sweep as TS
from profiles import profile_points


def end_normals(obj, row, walls):
    mesh = obj.data
    columns = walls + 1
    row_start = row * columns
    result = {}
    for polygon in mesh.polygons:
        wall = polygon.index % walls
        for loop in polygon.loop_indices:
            vertex = mesh.loops[loop].vertex_index
            if row_start <= vertex < row_start + columns:
                result.setdefault(wall, tuple(mesh.corner_normals[loop].vector))
    return result


with open(os.path.join(HERE, "..", "..", "data", "track", "L1_A.json"),
          encoding="utf-8") as handle:
    route = json.load(handle)
profile = profile_points("box_double")
result = SW.sweep(route["points"], profile,
                  station_chainages=[station["chainage_m"] for station in route["stations"]])
frames, chainages = result["frames"], result["station_m"]
material = bpy.data.materials.new("seam_test")
worst = 0.0
old_face_mismatch = 0.0
for previous, following in zip(result["chunks"], result["chunks"][1:]):
    # Before custom normals, the wall endpoint took only its own chunk's last
    # or first face normal. This is the measured negative control.
    old_before = SW.unit(SW.face_normal(previous["vertices"],
                                        previous["faces"][-len(profile) + 1]))
    old_after = SW.unit(SW.face_normal(following["vertices"],
                                       following["faces"][1]))
    old_face_mismatch = max(old_face_mismatch, math.degrees(math.acos(max(
        -1.0, min(1.0, SW.dot(old_before, old_after))))))
    for before_level in (0, 1, 2):
        for after_level in (0, 1, 2):
            before = (previous if before_level == 0 else
                      LD.lod_chunk(frames, chainages, profile,
                                   previous["first_ring"], previous["last_ring"], before_level))
            after = (following if after_level == 0 else
                     LD.lod_chunk(frames, chainages, profile,
                                  following["first_ring"], following["last_ring"], after_level))
            left = TS.build_object(before, 0, "before", material,
                                   frames=frames, profile=profile)
            right = TS.build_object(after, 0, "after", material,
                                    frames=frames, profile=profile)
            assert left.data.has_custom_normals and right.data.has_custom_normals
            a = end_normals(left, len(before["ring_indices"]) - 1, len(profile))
            b = end_normals(right, 0, len(profile))
            assert a.keys() == b.keys() == set(range(len(profile)))
            for wall in a:
                dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(a[wall], b[wall]))))
                worst = max(worst, math.degrees(math.acos(dot)))
            assert SW.chunk_gap_m(before, after, len(profile) + 1) < 1e-9
            bpy.data.objects.remove(left, do_unlink=True)
            bpy.data.objects.remove(right, do_unlink=True)

assert worst < 0.05, f"seam normals differ by {worst:.6f} degrees"
assert old_face_mismatch > 1.5, "negative control no longer exposes the seam crease"
print(f"SEAM NORMALS OK: {len(result['chunks']) - 1} seams, 9 LOD pairs, "
      f"maximum {worst:.6f} degrees (old faces {old_face_mismatch:.6f} degrees)")

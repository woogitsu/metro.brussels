#!/usr/bin/env python3
"""Rebuild the 300 m visual continuation beyond Merode from the pinned STIB shape.

The output is scenery only. Package A driving and station data still end at Merode.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from build_alignment import load_layers, pick_line, point_at, project_on_polyline

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "blender"))
import sweep as SW  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shapes", required=True)
    parser.add_argument("--axis", default="data/track/L1_A.json")
    parser.add_argument("--out", default="data/scenery/L1_A_visual_tail.json")
    args = parser.parse_args()

    axis = json.loads(Path(args.axis).read_text(encoding="utf-8"))
    shapes = Path(args.shapes)
    actual_hash = hashlib.sha256(shapes.read_bytes()).hexdigest()
    expected_hash = axis["source"]["content_sha256"]
    if actual_hash != expected_hash:
        raise SystemExit(f"source hash differs from L1_A: {actual_hash} != {expected_hash}")

    lines, _stops, _prj = load_layers(str(shapes))
    source = pick_line(lines, "001m", 1)["geometry"]["points"]
    origin = axis["origin_source_crs"]
    last = axis["points"][-1]
    world_end = (origin[0] + last[0], origin[1] + last[1])
    at, offset, _segment = project_on_polyline(source, world_end)
    if offset > 0.01:
        raise SystemExit(f"L1_A endpoint is {offset:.3f} m from the selected source")

    points = []
    for distance in range(0, 301, 15):
        source_point = point_at(source, at + distance)
        points.append([round(source_point[0] - origin[0], 3),
                       round(source_point[1] - origin[1], 3), 0.0])
    points[0] = last
    # The source polyline and the smoothed playable axis meet at the same point,
    # but their tangent differs by about 0.12 degrees. A one-metre guide point
    # uses the actual last rendered tangent, closing the profile and rail seam.
    rendered = SW.catmull_rom(axis["points"], SW.DEFAULT_RING_STEP_M)
    outgoing = SW.rmf_frames(rendered)[-1][1]
    guide = [round(last[0] + outgoing[0], 6),
             round(last[1] + outgoing[1], 6), 0.0]
    guide_world = (origin[0] + guide[0], origin[1] + guide[1])
    _guide_chainage, guide_offset, _ = project_on_polyline(source, guide_world)
    if guide_offset > 0.01:
        raise SystemExit(f"seam guide is {guide_offset:.3f} m from the selected source")
    points.insert(1, guide)
    length = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
    result = {
        "$comment": "Sceneria za Merode; nie wydłuża osi jazdy ani nie dodaje stacji.",
        "id": "L1_A_visual_tail",
        "length_m": round(length, 3),
        "points": points,
        "stations": [],
        "vertical": {"status": "not_modelled"},
        "source": {"source_id": "stib_shapefiles", "content_sha256": actual_hash,
                   "line_code": "001m", "variante": 1,
                   "source_chainage_start_m": round(at, 3),
                   "source_chainage_end_m": round(at + 300, 3),
                   "seam_guide_source_offset_m": round(guide_offset, 6),
                   "purpose": "visual_only"},
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
    print(f"[OGON] {len(points)} points, {length:.3f} m, source offset {offset:.6f} m")


if __name__ == "__main__":
    main()

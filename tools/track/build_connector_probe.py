#!/usr/bin/env python3
"""Generate an exploratory horizontal Merode–Montgomery connector outside data/.

This is a geometry probe, not a playable alignment: vertical profile, clearance,
signalling and infrastructure location have not been established.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from build_alignment import load_layers, pick_line, point_at, project_on_polyline

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "blender"))
import sweep  # noqa: E402


def canonical_json_sha256(path):
    """Hash parsed JSON so Windows and Linux checkout newlines give one identity."""
    content = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(content, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def unit(vector):
    length = math.hypot(vector[0], vector[1])
    return (vector[0] / length, vector[1] / length)


def angle_degrees(left, right):
    a, b = unit(left), unit(right)
    return math.degrees(math.acos(max(-1.0, min(1.0, a[0]*b[0] + a[1]*b[1]))))


def circumradius(a, b, c):
    ab = math.dist(a[:2], b[:2])
    bc = math.dist(b[:2], c[:2])
    ac = math.dist(a[:2], c[:2])
    cross = abs((b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0]))
    return ab*bc*ac/(2*cross) if cross > 1e-8 else math.inf


def generate(shapes, manifest, axis_a, axis_b):
    actual = hashlib.sha256(shapes.read_bytes()).hexdigest()
    expected = json.loads(manifest.read_text(encoding="utf-8"))["content_sha256"]
    if actual != expected:
        raise ValueError(f"STIB archive hash differs from manifest: {actual} != {expected}")
    a = json.loads(axis_a.read_text(encoding="utf-8"))
    b = json.loads(axis_b.read_text(encoding="utf-8"))
    if a["source"]["content_sha256"] != actual or b["source"]["content_sha256"] != actual:
        raise ValueError("package axis source differs from pinned STIB archive")
    if a["id"] != "L1_A" or b["id"] != "L1_B":
        raise ValueError("expected L1_A and L1_B package axes")

    lines, _stops, _projection = load_layers(str(shapes))
    source = pick_line(lines, "001m", 1)["geometry"]["points"]
    origin = a["origin_source_crs"]
    a_end = a["points"][-1]
    b_start = [b["origin_source_crs"][0] - origin[0],
               b["origin_source_crs"][1] - origin[1], 0.0]
    world_a = (a_end[0] + origin[0], a_end[1] + origin[1])
    world_b = (b_start[0] + origin[0], b_start[1] + origin[1])
    start, offset_a, _ = project_on_polyline(source, world_a)
    end, offset_b, _ = project_on_polyline(source, world_b)
    if not start < end or max(offset_a, offset_b) > 0.01:
        raise ValueError("package seam endpoints do not follow the selected source")
    gap = end - start
    if not 600 < gap < 800:
        raise ValueError(f"unexpected Merode–Montgomery source gap: {gap:.3f} m")

    # Follow official plan geometry until 100 m before Montgomery. The Hermite
    # transition is exploratory smoothing, not a claim about real rails.
    step = 15.0
    transition = 100.0
    source_points = [a_end]
    distance = start + step
    while distance < end - transition:
        x, y = point_at(source, distance)
        source_points.append([x - origin[0], y - origin[1], 0.0])
        distance += step
    join_distance = end - transition
    x, y = point_at(source, join_distance)
    join = [x - origin[0], y - origin[1], 0.0]
    x_next, y_next = point_at(source, join_distance + 1)
    join_tangent = unit((x_next - x, y_next - y))
    a_rendered = sweep.catmull_rom(a["points"], 5)
    a_tangent = unit((a_rendered[-1][0] - a_rendered[-2][0],
                      a_rendered[-1][1] - a_rendered[-2][1]))
    b_world = [[p[0] + b_start[0], p[1] + b_start[1], 0.0] for p in b["points"]]
    b_rendered = sweep.catmull_rom(b_world, 5)
    b_tangent = unit((b_rendered[1][0] - b_rendered[0][0],
                      b_rendered[1][1] - b_rendered[0][1]))
    points = [a_end, [a_end[0] + a_tangent[0], a_end[1] + a_tangent[1], 0.0]]
    points.extend(source_points[1:])
    points.append(join)
    for index in range(1, 11):
        t = index / 10
        h00 = 2*t**3 - 3*t**2 + 1
        h10 = t**3 - 2*t**2 + t
        h01 = -2*t**3 + 3*t**2
        h11 = t**3 - t**2
        points.append([h00*join[k] + h10*transition*join_tangent[k]
                       + h01*b_start[k] + h11*transition*b_tangent[k]
                       for k in range(2)] + [0.0])
    rendered = sweep.catmull_rom(points, 5)
    seam_a = angle_degrees((a_rendered[-1][0]-a_rendered[-2][0],
                            a_rendered[-1][1]-a_rendered[-2][1]),
                           (rendered[1][0]-rendered[0][0],
                            rendered[1][1]-rendered[0][1]))
    seam_b = angle_degrees((rendered[-1][0]-rendered[-2][0],
                            rendered[-1][1]-rendered[-2][1]),
                           (b_rendered[1][0]-b_rendered[0][0],
                            b_rendered[1][1]-b_rendered[0][1]))
    min_radius = min(circumradius(*rendered[i:i+3]) for i in range(len(rendered)-2))
    max_offset = max(project_on_polyline(source, (p[0]+origin[0], p[1]+origin[1]))[1]
                     for p in rendered)
    limits = {"max_seam_angle_deg": 0.2, "min_plan_radius_m": 100.0,
              "max_source_offset_m": 2.0}
    if max(seam_a, seam_b) > limits["max_seam_angle_deg"]:
        raise ValueError(f"connector seam angle exceeds probe limit: {seam_a:.3f}, {seam_b:.3f} deg")
    if min_radius < limits["min_plan_radius_m"]:
        raise ValueError(f"connector plan radius below probe limit: {min_radius:.3f} m")
    if max_offset > limits["max_source_offset_m"]:
        raise ValueError(f"connector departure from source exceeds probe limit: {max_offset:.3f} m")
    return {
        "$comment": "Research-only horizontal connector; not a playable or surveyed track axis.",
        "id": "L1_A_B_connector_PROBE",
        "length_m": round(sweep.polyline_length(rendered), 3),
        "points": [[round(value, 6) for value in point] for point in points],
        "stations": [],
        "vertical": {"status": "not_modelled", "z_values_are_placeholders": True},
        "plan_metrics": {"seam_a_angle_deg": round(seam_a, 6),
                         "seam_b_angle_deg": round(seam_b, 6),
                         "minimum_radius_m": round(min_radius, 3),
                         "maximum_source_offset_m": round(max_offset, 6),
                         "probe_limits": limits},
        "source": {"source_id": "stib_shapefiles", "content_sha256": actual,
                   "line_code": "001m", "variante": 1, "crs": "EPSG:31370",
                   "generator": "tools/track/build_connector_probe.py",
                   "generator_version": 1,
                   "input_sha256": {
                       "shapes": actual,
                   },
                   "input_json_sha256": {
                       "manifest": canonical_json_sha256(manifest),
                       "axis_a": canonical_json_sha256(axis_a),
                       "axis_b": canonical_json_sha256(axis_b),
                   },
                   "source_chainage_start_m": round(start, 6),
                   "source_chainage_end_m": round(end, 6),
                   "endpoint_offset_m": [round(offset_a, 6), round(offset_b, 6)],
                   "smoothing": "100 m Hermite at Montgomery; 1 m Merode tangent guide",
                   "purpose": "horizontal_geometry_probe"},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shapes", required=True, type=Path)
    parser.add_argument("--manifest", type=Path, default=Path("data/network/shapes-manifest.json"))
    parser.add_argument("--axis-a", type=Path, default=Path("data/track/L1_A.json"))
    parser.add_argument("--axis-b", type=Path, default=Path("data/track/L1_B.json"))
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.out.resolve().is_relative_to((Path(__file__).resolve().parents[2] / "data").resolve()):
        parser.error("probe output must stay outside tracked data/")
    result = generate(args.shapes, args.manifest, args.axis_a, args.axis_b)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    print(f"[PROBE] {result['length_m']:.3f} m; vertical and operational geometry unverified")


if __name__ == "__main__":
    main()

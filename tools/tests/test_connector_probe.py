#!/usr/bin/env python3
"""Offline checks for the research-only horizontal connector generator."""
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "track"))
import build_connector_probe as probe  # noqa: E402

ARTIFACT = ROOT / "data" / "design" / "geometry" / "merode-montgomery-horizontal-probe.json"


def test_connector_probe_provenance_and_vertical_unknown():
    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        shapes = temp / "shapes.zip"
        shapes.write_bytes(b"test archive")
        digest = hashlib.sha256(shapes.read_bytes()).hexdigest()
        manifest = temp / "manifest.json"
        manifest.write_text(json.dumps({"content_sha256": digest}), encoding="utf-8")
        a = temp / "A.json"
        b = temp / "B.json"
        a.write_text(json.dumps({"id": "L1_A", "origin_source_crs": [0, 0],
                                 "points": [[-15, 0, 0], [0, 0, 0]],
                                 "source": {"content_sha256": digest}}), encoding="utf-8")
        b.write_text(json.dumps({"id": "L1_B", "origin_source_crs": [700, 0],
                                 "points": [[0, 0, 0], [15, 0, 0]],
                                 "source": {"content_sha256": digest}}), encoding="utf-8")
        line = {"geometry": {"points": [[0, 0], [700, 0]]}}
        with patch.object(probe, "load_layers", return_value=([line], None, None)), \
             patch.object(probe, "pick_line", return_value=line):
            result = probe.generate(shapes, manifest, a, b)
            assert result["source"]["content_sha256"] == digest, result["source"]
            assert result["source"]["source_chainage_end_m"] == 700, result["source"]
            assert result["vertical"]["status"] == "not_modelled", result["vertical"]
            assert result["vertical"]["z_values_are_placeholders"] is True, result["vertical"]
            assert result["stations"] == [], result["stations"]
            assert result["points"][0] == [0, 0, 0], result["points"][0]
            assert result["points"][-1] == [700, 0, 0], result["points"][-1]
            metrics = result["plan_metrics"]
            assert max(metrics["seam_a_angle_deg"], metrics["seam_b_angle_deg"]) <= 0.2, metrics
            assert metrics["minimum_radius_m"] >= 100, metrics
            assert metrics["maximum_source_offset_m"] <= 2, metrics
            with patch.object(probe, "circumradius", return_value=50):
                try:
                    probe.generate(shapes, manifest, a, b)
                except ValueError as error:
                    assert "radius below probe limit" in str(error), str(error)
                else:
                    raise AssertionError("tight connector plan was accepted")
            manifest.write_text(json.dumps({"content_sha256": "0" * 64}), encoding="utf-8")
            try:
                probe.generate(shapes, manifest, a, b)
            except ValueError as error:
                assert "hash differs" in str(error), str(error)
            else:
                raise AssertionError("unpinned source archive was accepted")


def test_committed_connector_is_a_pinned_horizontal_probe():
    """Check input identities and measure geometry without treating it as a track axis."""
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    manifest_path = ROOT / "data" / "network" / "shapes-manifest.json"
    axis_a_path = ROOT / "data" / "track" / "L1_A.json"
    axis_b_path = ROOT / "data" / "track" / "L1_B.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    axis_a = json.loads(axis_a_path.read_text(encoding="utf-8"))
    axis_b = json.loads(axis_b_path.read_text(encoding="utf-8"))
    source = artifact["source"]
    assert ARTIFACT.parent != ROOT / "data" / "track", ARTIFACT
    assert artifact["id"] == "L1_A_B_connector_PROBE", artifact["id"]
    assert source["purpose"] == "horizontal_geometry_probe", source
    assert source["generator"] == "tools/track/build_connector_probe.py", source
    assert source["content_sha256"] == manifest["content_sha256"], source
    for name, path in (("manifest", manifest_path), ("axis_a", axis_a_path),
                       ("axis_b", axis_b_path)):
        measured = probe.canonical_json_sha256(path)
        assert source["input_json_sha256"][name] == measured, (name, measured)
    assert source["input_sha256"]["shapes"] == source["content_sha256"], source
    assert artifact["vertical"] == {
        "status": "not_modelled", "z_values_are_placeholders": True}, artifact["vertical"]
    assert artifact["stations"] == [], artifact["stations"]
    assert all(point[2] == 0 for point in artifact["points"]), artifact["points"]
    assert artifact["points"][0] == axis_a["points"][-1], artifact["points"][0]
    b_start = [axis_b["origin_source_crs"][0] - axis_a["origin_source_crs"][0],
               axis_b["origin_source_crs"][1] - axis_a["origin_source_crs"][1], 0]
    assert artifact["points"][-1] == b_start, artifact["points"][-1]
    rendered = probe.sweep.catmull_rom(artifact["points"], 5)
    assert math.isclose(probe.sweep.polyline_length(rendered), artifact["length_m"],
                        abs_tol=0.001), artifact["length_m"]
    minimum_radius = min(probe.circumradius(*rendered[i:i+3])
                         for i in range(len(rendered)-2))
    metrics = artifact["plan_metrics"]
    limits = metrics["probe_limits"]
    a_rendered = probe.sweep.catmull_rom(axis_a["points"], 5)
    b_world = [[point[0] + b_start[0], point[1] + b_start[1], 0]
               for point in axis_b["points"]]
    b_rendered = probe.sweep.catmull_rom(b_world, 5)
    seam_a = probe.angle_degrees(
        (a_rendered[-1][0] - a_rendered[-2][0],
         a_rendered[-1][1] - a_rendered[-2][1]),
        (rendered[1][0] - rendered[0][0], rendered[1][1] - rendered[0][1]))
    seam_b = probe.angle_degrees(
        (rendered[-1][0] - rendered[-2][0],
         rendered[-1][1] - rendered[-2][1]),
        (b_rendered[1][0] - b_rendered[0][0],
         b_rendered[1][1] - b_rendered[0][1]))
    assert math.isclose(seam_a, metrics["seam_a_angle_deg"], abs_tol=0.0001), seam_a
    assert math.isclose(seam_b, metrics["seam_b_angle_deg"], abs_tol=0.0001), seam_b
    assert math.isclose(minimum_radius, metrics["minimum_radius_m"],
                        abs_tol=0.002), (minimum_radius, metrics)
    assert minimum_radius >= limits["min_plan_radius_m"], minimum_radius
    assert max(metrics["seam_a_angle_deg"], metrics["seam_b_angle_deg"]) <= limits[
        "max_seam_angle_deg"], metrics
    assert metrics["maximum_source_offset_m"] <= limits[
        "max_source_offset_m"], metrics


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

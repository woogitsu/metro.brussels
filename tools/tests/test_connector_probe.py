#!/usr/bin/env python3
"""Offline checks for the research-only horizontal connector generator."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "track"))
import build_connector_probe as probe  # noqa: E402


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
            assert result["source"]["content_sha256"] == digest
            assert result["source"]["source_chainage_end_m"] == 700
            assert result["vertical"]["status"] == "not_modelled"
            assert result["vertical"]["z_values_are_placeholders"] is True
            assert result["stations"] == []
            assert result["points"][0] == [0, 0, 0]
            assert result["points"][-1] == [700, 0, 0]
            metrics = result["plan_metrics"]
            assert max(metrics["seam_a_angle_deg"], metrics["seam_b_angle_deg"]) <= 0.2
            assert metrics["minimum_radius_m"] >= 100
            assert metrics["maximum_source_offset_m"] <= 2
            with patch.object(probe, "circumradius", return_value=50):
                try:
                    probe.generate(shapes, manifest, a, b)
                except ValueError as error:
                    assert "radius below probe limit" in str(error)
                else:
                    raise AssertionError("tight connector plan was accepted")
            manifest.write_text(json.dumps({"content_sha256": "0" * 64}), encoding="utf-8")
            try:
                probe.generate(shapes, manifest, a, b)
            except ValueError as error:
                assert "hash differs" in str(error)
            else:
                raise AssertionError("unpinned source archive was accepted")

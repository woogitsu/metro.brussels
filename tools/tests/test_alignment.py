#!/usr/bin/env python3
"""Testy osi pakietu A i narzędzi geometrycznych (T-111). Bez sieci i bez pytest.

Czytnik shapefile'a i transformacja CRS są testowane na danych budowanych w locie,
więc testy nie zależą od 856 KB archiwum STIB ani od internetu. Gotowy artefakt
`data/track/L1_A.json` jest sprawdzany tylko wtedy, gdy jest obecny w repo.
"""
import json
import math
import os
import struct
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import build_alignment as B  # noqa: E402
import crs as CRS  # noqa: E402
import shapefile as S  # noqa: E402

ALIGNMENT = os.path.join(ROOT, "data", "track", "L1_A.json")
PROVENANCE = os.path.join(ROOT, "data", "track", "L1_A.provenance.json")

# Wartości odniesienia policzone przy pełnej precyzji parametrów EPSG:15929
# i porównane z PROJ 9 / pyproj 3.7; zgodność 0,25 mm przy identycznych parametrach.
CRS_REFERENCE = [
    (4.3517, 50.8466, 148799.079, 170688.565),
    (4.3200, 50.8500, 146566.821, 171067.752),
    (4.3900, 50.8400, 151496.611, 169954.478),
]
CRS_TOLERANCE_M = 0.005


def _shp(shapes, shape_type):
    body = b""
    for number, points in enumerate(shapes, start=1):
        if shape_type == S.TYPE_POINT:
            content = struct.pack("<i", shape_type) + struct.pack("<dd", *points[0])
        else:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            content = (struct.pack("<i", shape_type)
                       + struct.pack("<dddd", min(xs), min(ys), max(xs), max(ys))
                       + struct.pack("<ii", 1, len(points))
                       + struct.pack("<i", 0)
                       + b"".join(struct.pack("<dd", x, y) for x, y in points))
        body += struct.pack(">ii", number, len(content) // 2) + content
    header = struct.pack(">i", S.SHP_MAGIC) + b"\x00" * 20
    header += struct.pack(">i", (100 + len(body)) // 2) + struct.pack("<ii", 1000, shape_type)
    header += struct.pack("<dddd", 0, 0, 0, 0) + b"\x00" * 32
    return header + body


def _dbf(rows, fields):
    header_length = 32 + 32 * len(fields) + 1
    record_length = 1 + sum(f[2] for f in fields)
    out = bytearray(struct.pack("<B3B", 3, 26, 1, 1))
    out += struct.pack("<iHH", len(rows), header_length, record_length)
    out += b"\x00" * 20
    for name, kind, length in fields:
        out += name.encode("latin-1")[:11].ljust(11, b"\x00")
        out += kind.encode("latin-1")
        out += b"\x00" * 4 + bytes([length, 0]) + b"\x00" * 14
    out += b"\x0D"
    for row in rows:
        out += b" "
        for name, _kind, length in fields:
            out += str(row.get(name, "")).encode("utf-8")[:length].ljust(length, b" ")
    return bytes(out)


# --- czytnik shapefile --------------------------------------------------------

def test_alignment_shapefile_reads_polyline_and_attributes():
    shapes = [[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)], [(1.0, 1.0), (2.0, 2.0)]]
    fields = [("LineCode", "C", 8), ("Variante", "N", 4)]
    rows = [{"LineCode": "001m", "Variante": 1}, {"LineCode": "002m", "Variante": 2}]
    records = S.read_pair(_shp(shapes, S.TYPE_POLYLINE), _dbf(rows, fields))
    assert len(records) == 2
    assert records[0]["geometry"]["points"] == shapes[0]
    assert records[0]["attributes"]["LineCode"] == "001m"
    assert records[0]["attributes"]["Variante"] == 1


def test_alignment_shapefile_reads_points():
    records = S.read_pair(_shp([[(150000.0, 170000.0)]], S.TYPE_POINT),
                          _dbf([{"Stop_id": "8733"}], [("Stop_id", "C", 8)]))
    assert records[0]["geometry"]["points"] == [(150000.0, 170000.0)]
    assert records[0]["attributes"]["Stop_id"] == "8733"


def test_alignment_shapefile_rejects_bad_magic():
    try:
        S.read_shp(b"\x00" * 120)
    except S.ShapefileError as exc:
        assert "magic" in str(exc)
    else:
        raise AssertionError("zły magic powinien zostać odrzucony")


def test_alignment_shapefile_rejects_record_count_mismatch():
    try:
        S.read_pair(_shp([[(0.0, 0.0), (1.0, 1.0)]], S.TYPE_POLYLINE),
                    _dbf([{"A": "1"}, {"A": "2"}], [("A", "C", 2)]))
    except S.ShapefileError as exc:
        assert "niezgodna liczba rekordów" in str(exc)
    else:
        raise AssertionError("niezgodna liczba rekordów powinna zostać odrzucona")


def test_alignment_prj_parses_lambert72():
    text = ('PROJCS["Belge_Lambert_1972",PARAMETER["False_Easting",150000.013],'
            'PARAMETER["Central_Meridian",4.367486666666666]]')
    prj = S.read_prj(text)
    assert prj["name"] == "Belge_Lambert_1972"
    assert prj["parameters"]["False_Easting"] == 150000.013


# --- transformacja CRS --------------------------------------------------------

def test_alignment_crs_matches_reference_points():
    for lon, lat, x, y in CRS_REFERENCE:
        mx, my = CRS.wgs84_to_lambert72(lon, lat)
        assert math.dist((mx, my), (x, y)) < CRS_TOLERANCE_M, (lon, lat, mx, my)


def test_alignment_crs_roundtrip_is_stable():
    lon, lat = 4.3517, 50.8466
    blon, blat, _h = CRS.wgs84_to_bd72(lon, lat)
    assert abs(blon - lon) < 0.01 and abs(blat - lat) < 0.01
    first = CRS.wgs84_to_lambert72(lon, lat)
    second = CRS.wgs84_to_lambert72(lon, lat)
    assert first == second


# --- geometria osi ------------------------------------------------------------

def test_alignment_projection_finds_perpendicular_foot():
    line = [(0.0, 0.0), (100.0, 0.0)]
    chainage, offset, _segment = B.project_on_polyline(line, (30.0, 5.0))
    assert abs(chainage - 30.0) < 1e-9 and abs(offset - 5.0) < 1e-9


def test_alignment_slice_cuts_between_chainages():
    line = [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]
    sliced = [p for p, _ in B.slice_polyline(line, 50.0, 150.0)]
    assert abs(B.polyline_length(sliced) - 100.0) < 1e-9
    assert sliced[0] == (50.0, 0.0) and sliced[-1] == (150.0, 0.0)


def test_alignment_uniform_resample_keeps_anchors_and_limits_gap():
    line = [(0.0, 0.0), (1000.0, 0.0)]
    anchors = [0.0, 333.0, 1000.0]
    sampled = B.resample_uniform(line, 15.0, anchors)
    points = [p for p, _ in sampled]
    gaps = [math.dist(a, b) for a, b in zip(points, points[1:])]
    assert max(gaps) <= 15.0 * 1.5 + 1e-6, max(gaps)
    for anchor in anchors:
        assert any(abs(p[0] - anchor) < 1e-6 for p in points), anchor
    assert sum(1 for _p, tag in sampled if tag == "station_anchor") == len(anchors)


def test_alignment_resample_does_not_leave_source_polyline():
    line = [(0.0, 0.0), (100.0, 50.0), (200.0, 0.0)]
    sampled = [p for p, _ in B.resample_uniform(line, 10.0, [0.0])]
    assert B.max_deviation(sampled, line) < 1e-6


def test_alignment_radius_statistics_detect_digitisation_noise():
    dense = [(0.0, 0.0), (0.5, 0.02), (1.0, 0.0), (1.5, 0.02), (2.0, 0.0)]
    smooth = [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]
    assert B.radius_stats(dense)["min_m"] < 10.0
    assert B.radius_stats(smooth)["min_m"] is None or B.radius_stats(smooth)["min_m"] > 1000.0


def test_alignment_name_normalisation_ignores_accents_and_case():
    assert B.normalise("ETANGS NOIRS") == B.normalise("Étangs Noirs")
    assert B.normalise("DE BROUCKERE") == B.normalise("De Brouckère")
    assert B.normalise("ARTS-LOI") == B.normalise("Arts Loi")


# --- gotowy artefakt ----------------------------------------------------------

def test_alignment_committed_axis_matches_package_a():
    if not os.path.isfile(ALIGNMENT):
        return
    doc = json.load(open(ALIGNMENT, encoding="utf-8"))
    assert doc["id"] == "L1_A"
    assert doc["package"]["from"] == "Gare de l'Ouest" and doc["package"]["to"] == "Merode"
    assert len(doc["stations"]) == doc["package"]["declared_stations"] == 12
    chainages = [s["chainage_m"] for s in doc["stations"]]
    assert chainages == sorted(chainages)
    assert chainages[0] == 0.0
    assert abs(chainages[-1] - doc["length_m"]) < 1.0
    assert 6000 < doc["length_m"] < 7500, doc["length_m"]


def test_alignment_committed_axis_is_horizontal_only():
    if not os.path.isfile(ALIGNMENT):
        return
    doc = json.load(open(ALIGNMENT, encoding="utf-8"))
    assert doc["vertical"]["status"] == "not_modelled"
    assert all(point[2] == 0.0 for point in doc["points"])
    assert all(station["depth_m"] is None for station in doc["stations"])


def test_alignment_committed_axis_has_no_nan_and_sane_gaps():
    if not os.path.isfile(ALIGNMENT):
        return
    doc = json.load(open(ALIGNMENT, encoding="utf-8"))
    points = [(p[0], p[1]) for p in doc["points"]]
    for x, y in points:
        assert not math.isnan(x) and not math.isinf(x)
        assert not math.isnan(y) and not math.isinf(y)
    gaps = [math.dist(a, b) for a, b in zip(points, points[1:])]
    assert min(gaps) > 0.5, min(gaps)
    assert max(gaps) < 25.0, max(gaps)


def test_alignment_committed_provenance_marks_every_point_as_derived():
    if not os.path.isfile(PROVENANCE):
        return
    prov = json.load(open(PROVENANCE, encoding="utf-8"))
    doc = json.load(open(ALIGNMENT, encoding="utf-8"))
    assert len(prov["points"]) == len(doc["points"])
    assert {p["source_class"] for p in prov["points"]} == {"derived"}
    assert {p["derived_from"] for p in prov["points"]} == {"official_stib"}
    assert prov["source_crs"] == "EPSG:31370"
    steps = {t["step"] for t in prov["transformations"]}
    assert {"project_stations", "slice", "resample_uniform", "translate_origin"} <= steps
    assert prov["statistics"]["resample_max_deviation_m"] < 0.01
    assert any("profil pionowy" in item for item in prov["not_derived"])


def test_alignment_committed_crosscheck_reports_other_sources():
    if not os.path.isfile(PROVENANCE):
        return
    prov = json.load(open(PROVENANCE, encoding="utf-8"))
    codes = {(c["line_code"], c["variante"]) for c in prov["crosscheck"]}
    assert ("005m", 1) in codes
    for entry in prov["crosscheck"]:
        if entry["status"] == "ok":
            assert entry["deviation_median_m"] is not None

#!/usr/bin/env python3
"""Testy pomiaru szerokości tunelu z poligonów UrbIS. Bez sieci i bez pytest.

Geometria pomiaru jest sprawdzana na prostokątach i klinach budowanych w locie,
więc testy nie zależą od dostępności data.mobility.brussels.
"""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import tunnel_width as TW  # noqa: E402


def _box(half_width, length=600.0, y_centre=0.0):
    """Prostokątny „tunel" wzdłuż osi X o zadanej połowie szerokości."""
    return [(-10.0, y_centre - half_width), (length, y_centre - half_width),
            (length, y_centre + half_width), (-10.0, y_centre + half_width)]


def _axis(length=600.0, step=20.0):
    return [(x, 0.0, 0.0) for x in [i * step for i in range(int(length / step) + 1)]]


def test_tunnel_width_ray_finds_the_near_wall():
    ring = _box(4.7)
    assert abs(TW.ray_distance((100.0, 0.0), (0.0, 1.0), ring) - 4.7) < 1e-9
    assert abs(TW.ray_distance((100.0, 0.0), (0.0, -1.0), ring) - 4.7) < 1e-9
    assert abs(TW.ray_distance((100.0, 2.0), (0.0, 1.0), ring) - 2.7) < 1e-9


def test_tunnel_width_ray_misses_outside_the_range():
    ring = _box(4.7, length=50.0)
    assert TW.ray_distance((100.0, 0.0), (0.0, 1.0), ring, maximum=1.0) is None


def test_tunnel_width_point_in_ring_matches_the_rectangle():
    ring = _box(4.7)
    assert TW.point_in_ring((100.0, 0.0), ring) is True
    assert TW.point_in_ring((100.0, 9.0), ring) is False
    assert TW.point_in_ring((-50.0, 0.0), ring) is False


def test_tunnel_width_measures_a_known_rectangle():
    rows = TW.measure(_axis(), [], [({"name_fr": "test"}, _box(4.7))])
    assert rows, "brak próbek"
    widths = {r["width_m"] for r in rows}
    assert widths == {9.4}, widths
    assert all(abs(r["polygon_centre_offset_right_m"]) < 1e-9 for r in rows)


def test_tunnel_width_reports_offset_when_the_axis_is_not_centred():
    """Znak idzie wzdłuż wektora „prawo" ramki, czyli -Y dla osi biegnącej na +X."""
    rows = TW.measure(_axis(), [], [({"name_fr": "test"}, _box(4.7, y_centre=1.5))])
    assert rows
    assert all(abs(r["width_m"] - 9.4) < 1e-9 for r in rows)
    assert all(abs(r["polygon_centre_offset_right_m"] + 1.5) < 1e-9 for r in rows)


def test_tunnel_width_skips_the_station_halo():
    axis = _axis()
    total = 600.0
    everywhere = TW.measure(axis, [], [({"name_fr": "t"}, _box(4.7))])
    around_stations = TW.measure(axis, [0.0, total], [({"name_fr": "t"}, _box(4.7))],
                                 halo_m=120.0)
    assert len(around_stations) < len(everywhere)
    assert all(120.0 <= r["chainage_m"] <= total - 120.0 for r in around_stations)


def test_tunnel_width_ignores_points_covered_by_two_polygons():
    """Nakładka dwóch poligonów daje pomiar niejednoznaczny — ma zostać pominięta."""
    overlapping = [({"name_fr": "a"}, _box(4.7)), ({"name_fr": "b"}, _box(6.0))]
    assert TW.measure(_axis(), [], overlapping) == []


def test_tunnel_width_summary_splits_running_tunnel_from_chambers():
    rows = ([{"chainage_m": float(i), "width_m": 8.8, "polygon_centre_offset_right_m": 0.0,
              "polygon": "szlak"} for i in range(20)]
            + [{"chainage_m": 100.0, "width_m": 40.0, "polygon_centre_offset_right_m": 0.0,
                "polygon": "wezel"}])
    summary = TW.summarise(rows)
    assert summary["samples_all"] == 21 and summary["samples"] == 20
    assert summary["max_m"] == 8.8
    assert set(summary["per_polygon"]) == {"szlak"}


def test_tunnel_width_summary_is_explicit_when_nothing_qualifies():
    summary = TW.summarise([{"chainage_m": 0.0, "width_m": 40.0,
                             "polygon_centre_offset_right_m": 0.0, "polygon": "wezel"}])
    assert summary["status"] != "ok" and summary["samples"] == 0


def _rect(width, length):
    return [(0.0, -width / 2), (length, -width / 2), (length, width / 2), (0.0, width / 2)]


def _elbow(width, arm):
    """Korytarz zgięty pod kątem prostym — bbox go zawyża, 2A/P nie."""
    half = width / 2
    return [(-half, -half), (arm, -half), (arm, half + arm - width), (arm - width, half + arm - width),
            (arm - width, half), (-half, half)]


def test_survey_corridor_width_recovers_a_straight_rectangle():
    for width in (6.08, 8.8, 9.4):
        ring = _rect(width, 400.0)
        assert abs(TW.corridor_width(ring) - width) < 0.2, width
        assert abs(TW.bbox_min_width(ring) - width) < 1e-6, width


def test_survey_bbox_overestimates_a_bent_corridor_but_area_ratio_does_not():
    """Sedno wyboru estymatora: dla zgiętego korytarza bbox mierzy zasięg, nie szerokość."""
    ring = _elbow(9.0, 300.0)
    corridor = TW.corridor_width(ring)
    bbox = TW.bbox_min_width(ring)
    assert abs(corridor - 9.0) < 1.0, corridor
    assert bbox > 5 * corridor, (bbox, corridor)


def test_survey_area_and_perimeter_are_orientation_independent():
    ring = _rect(9.4, 200.0)
    turned = [(x * 0.6 - y * 0.8, x * 0.8 + y * 0.6) for x, y in ring]
    assert abs(TW.polygon_area(ring) - TW.polygon_area(turned)) < 1e-6
    assert abs(TW.polygon_perimeter(ring) - TW.polygon_perimeter(turned)) < 1e-6


def test_survey_sorts_by_corridor_width_and_reports_both_estimators():
    payload = {"features": [
        {"properties": {"type": "MT", "name_fr": "szeroki"},
         "geometry": {"type": "Polygon", "coordinates": [
             [list(CRSLESS(x, y)) for x, y in _rect(14.0, 300.0)]]}},
        {"properties": {"type": "MT", "name_fr": "waski"},
         "geometry": {"type": "Polygon", "coordinates": [
             [list(CRSLESS(x, y)) for x, y in _rect(6.2, 300.0)]]}},
    ]}
    result = TW.survey(payload)
    assert result["polygons"] == 2
    assert result["narrowest"][0]["name"] == "waski"
    assert result["narrowest"][0]["corridor_width_m"] < result["narrowest"][1]["corridor_width_m"]
    for row in result["narrowest"]:
        assert "bbox_min_width_m" in row and "area_m2" in row


def CRSLESS(x, y):
    """Punkty testowe podajemy w stopniach wokół Brukseli, żeby przeszły przez transformację."""
    return (4.35 + x / 70000.0, 50.85 + y / 111000.0)

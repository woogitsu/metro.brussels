#!/usr/bin/env python3
"""Testy klasyfikacji „w tunelu / poza tunelem". Bez sieci i bez pytest.

Wszystkie dane wejściowe są budowane w locie: OSM jako mały dokument XML, UrbIS jako
prostokąt. Test sprawdza logikę rozstrzygania, a nie dostępność serwisów.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import surface_sections as SS  # noqa: E402


def _osm(ways):
    """Dokument OSM z jednym węzłem na metr wzdłuż zadanych odcinków w WGS84."""
    nodes, body = [], []
    node_id = 1
    for way_id, coords, tags in ways:
        refs = []
        for lon, lat in coords:
            nodes.append(f'<node id="{node_id}" lon="{lon}" lat="{lat}"/>')
            refs.append(f'<nd ref="{node_id}"/>')
            node_id += 1
        tag_xml = "".join(f'<tag k="{k}" v="{v}"/>' for k, v in tags.items())
        body.append(f'<way id="{way_id}">{"".join(refs)}{tag_xml}</way>')
    return ("<osm version=\"0.6\">" + "".join(nodes) + "".join(body) + "</osm>").encode("utf-8")


# --- rozstrzyganie ------------------------------------------------------------

def test_surface_classify_agrees_when_both_sources_say_tunnel():
    verdict, urbis, osm = SS.classify({"niveau": "-"}, {"tunnel": "yes", "distance_m": 3.0})
    assert (verdict, urbis, osm) == ("zgodne", "tunel", "tunel")


def test_surface_classify_agrees_when_both_sources_say_surface():
    verdict, urbis, osm = SS.classify({"niveau": "0"}, {"tunnel": None, "distance_m": 3.0})
    assert (verdict, urbis, osm) == ("zgodne", "poza_tunelem", "poza_tunelem")


def test_surface_classify_reports_a_contradiction_instead_of_picking_a_side():
    """Rozbieżność jest wynikiem. Uśrednianie dwóch źródeł nie ma tu sensu."""
    verdict, urbis, osm = SS.classify({"niveau": "0"}, {"tunnel": "yes", "distance_m": 1.0})
    assert verdict == "sprzeczne" and urbis == "poza_tunelem" and osm == "tunel"


def test_surface_classify_ignores_an_osm_way_that_is_too_far():
    """Way sto metrów od osi opisuje inną linię, nie ten odcinek."""
    verdict, _urbis, osm = SS.classify({"niveau": "-"},
                                       {"tunnel": "yes", "distance_m": SS.NEAREST_MAX_M + 1.0})
    assert verdict == "jedno_zrodlo" and osm is None


def test_surface_classify_treats_covered_as_tunnel():
    _verdict, _urbis, osm = SS.classify(None, {"tunnel": "covered", "distance_m": 1.0})
    assert osm == "tunel"


def test_surface_classify_returns_unknown_when_neither_source_speaks():
    assert SS.classify(None, None)[0] == "nieznane"


# --- najbliższy way -----------------------------------------------------------

def test_surface_nearest_subway_picks_the_closest_way_not_the_first():
    """W węźle przesiadkowym w jednym kwadracie leży kilka linii na różnych poziomach."""
    import crs as CRS
    near = CRS.lambert72_to_wgs84(150000.0, 170000.0)
    far = CRS.lambert72_to_wgs84(150000.0, 170200.0)
    payload = _osm([
        ("far", [(far[0], far[1]), (far[0] + 0.002, far[1])],
         {"railway": "subway", "tunnel": "yes", "layer": "-3"}),
        ("near", [(near[0], near[1]), (near[0] + 0.002, near[1])],
         {"railway": "subway"}),
    ])
    best = SS.nearest_subway(payload, (150000.0, 170000.0))
    assert best["way_id"] == "near", best
    assert best["tunnel"] is None
    assert best["distance_m"] < 1.0


def test_surface_nearest_subway_ignores_other_railways():
    import crs as CRS
    lon, lat = CRS.lambert72_to_wgs84(150000.0, 170000.0)
    payload = _osm([("tram", [(lon, lat), (lon + 0.002, lat)], {"railway": "tram"})])
    assert SS.nearest_subway(payload, (150000.0, 170000.0)) is None


# --- rozmieszczenie sond ------------------------------------------------------

def test_surface_probe_chainages_always_hits_the_middle_of_every_range():
    """Regresja: bez tego wszystkie sondy przedziałów lądowały tuż za portalem."""
    chain = [float(i) for i in range(0, 3001, 10)]
    inside = [700.0 <= c <= 900.0 for c in chain]
    picks = SS.probe_chainages(chain, inside, 300.0, 800.0, [[700.0, 900.0]])
    assert any(abs(c - 800.0) < 1e-6 for c, _flag in picks), picks


def test_surface_probe_chainages_marks_portal_neighbourhood_separately():
    ranges = [[700.0, 900.0]]
    assert SS.range_position(800.0, ranges) == "srodek"
    assert SS.range_position(710.0, ranges) == "portal"
    assert SS.range_position(880.0, ranges) == "portal"
    assert SS.range_position(300.0, ranges) == "poza"


def test_surface_probe_chainages_are_sorted_and_unique():
    chain = [float(i) for i in range(0, 5001, 10)]
    inside = [1000.0 <= c <= 1400.0 for c in chain]
    picks = SS.probe_chainages(chain, inside, 300.0, 800.0, [[1000.0, 1400.0]])
    values = [c for c, _flag in picks]
    assert values == sorted(values)
    assert len(set(values)) == len(values)

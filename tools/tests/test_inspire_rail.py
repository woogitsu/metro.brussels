#!/usr/bin/env python3
"""Testy INSPIRE Rails i odwzorowania EPSG:3035 (T-111). Bez sieci i bez pytest.

Parser GML jest testowany na dokumencie budowanym w locie, więc testy nie zależą od
378 kB archiwum z portalu ani od internetu. Jedyne gniazdo, jakie tu powstaje, to
zamknięty port na 127.0.0.1 — po to, żeby sprawdzić, że niedostępne źródło jest
wynikiem, a nie wyjątkiem.
"""
import json
import math
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import crs as CRS  # noqa: E402
import inspire_rail as IR  # noqa: E402
import sweep as SW  # noqa: E402

# Przykład obliczeniowy z EPSG Guidance Note 7-2 dla metody 9820 (LAEA) w EPSG:3035.
# Wartości opublikowane są zaokrąglone do centymetra, stąd tolerancja 1 cm.
EPSG_EXAMPLE = (5.0, 50.0, 3962799.45, 2999718.85)
EPSG_TOLERANCE_M = 0.01
BRUSSELS = [(4.3517, 50.8466), (4.3200, 50.8500), (4.3900, 50.8400), (4.2500, 50.8900)]


# --- odwzorowanie EPSG:3035 ---------------------------------------------------

def test_inspire_laea_origin_maps_to_declared_centre():
    lon, lat = CRS.laea3035_to_wgs84(CRS.LAEA_FE, CRS.LAEA_FN)
    assert abs(lon - 10.0) < 1e-9 and abs(lat - 52.0) < 1e-9, (lon, lat)
    east, north = CRS.wgs84_to_laea3035(10.0, 52.0)
    assert abs(east - CRS.LAEA_FE) < 1e-6 and abs(north - CRS.LAEA_FN) < 1e-6


def test_inspire_laea_matches_epsg_worked_example():
    lon, lat, east, north = EPSG_EXAMPLE
    mx, my = CRS.wgs84_to_laea3035(lon, lat)
    assert math.dist((mx, my), (east, north)) < EPSG_TOLERANCE_M, (mx, my)


def test_inspire_laea_roundtrip_is_millimetre_stable():
    for lon, lat in BRUSSELS:
        east, north = CRS.wgs84_to_laea3035(lon, lat)
        back_lon, back_lat = CRS.laea3035_to_wgs84(east, north)
        # 1e-9 stopnia to poniżej 0,1 mm na tej szerokości
        assert abs(back_lon - lon) < 1e-9 and abs(back_lat - lat) < 1e-9, (lon, lat)


def test_inspire_laea_to_lambert72_lands_in_brussels():
    """Rzeczywisty wierzchołek z `TN.RailTransportNetwork.gml`, kolejność osi N,E."""
    east, north = 3927587.80980263, 3095760.75491994
    x, y = CRS.laea3035_to_lambert72(east, north)
    assert 140000 < x < 165000 and 160000 < y < 180000, (x, y)


def test_inspire_posbags_swap_axis_order():
    """EPSG:3035 ma kolejność osi northing,easting — zamiana wyrzuca punkt z Belgii."""
    points = IR.parse_posbags("3095760.75491994 3927587.80980263")
    assert points == [(3927587.80980263, 3095760.75491994)]
    lon, lat = CRS.laea3035_to_wgs84(*points[0])
    assert 4.0 < lon < 4.6 and 50.7 < lat < 51.0, (lon, lat)


# --- syntetyczny dokument GML -------------------------------------------------

def _line_string(points):
    flat = " ".join(f"{n:.6f} {e:.6f}" for e, n in points)
    return ('<net:centrelineGeometry><gml:LineString '
            'srsName="http://www.opengis.net/def/crs/EPSG/0/3035" srsDimension="2">'
            f'<gml:posList>{flat}</gml:posList></gml:LineString></net:centrelineGeometry>')


def _node(code, mode, station, point):
    return (f'<gml:featureMember><tn-ra:RailwayNode gml:id="node_56{code}">'
            f'<gml:description>{mode} stop {code} serving routes</gml:description>'
            f'<net:inNetwork xlink:href="rail" />'
            f'<gml:geometry><gml:Point><gml:pos>{point[1]:.6f} {point[0]:.6f}</gml:pos>'
            f'</gml:Point></gml:geometry>'
            f'<gn:GeographicalName><gn:spelling><gn:SpellingOfName>'
            f'<gn:text>{station}</gn:text></gn:SpellingOfName></gn:spelling>'
            f'</gn:GeographicalName>'
            f'<tn:validFrom>2026-03-02T00:00:00</tn:validFrom>'
            f'<tn:validTo>2026-06-28T00:00:00</tn:validTo>'
            f'</tn-ra:RailwayNode></gml:featureMember>')


def _link(code_a, code_b, points, valid_to="2026-06-28T00:00:00"):
    return (f'<gml:featureMember><tn-ra:RailwayLink gml:id="link_56{code_a}{code_b}">'
            f'<gml:description>Link between stops {code_a} and {code_b}</gml:description>'
            + _line_string(points)
            + f'<tn:validFrom>2026-03-02T00:00:00</tn:validFrom>'
            f'<tn:validTo>{valid_to}</tn:validTo>'
            f'</tn-ra:RailwayLink></gml:featureMember>')


def _line(code, description, sequence_id):
    return (f'<gml:featureMember><tn-ra:RailwayLine gml:id="line_{code}">'
            f'<gml:description>{description}</gml:description>'
            f'<net:link xlink:href="#{sequence_id}" />'
            f'<tn-ra:railwayLineCode>1</tn-ra:railwayLineCode>'
            f'</tn-ra:RailwayLine></gml:featureMember>')


def _sequence(sequence_id, hrefs):
    body = "".join(f'<net:link><net:DirectedLink><net:direction>+</net:direction>'
                   f'<net:link xlink:href="{h}" /></net:DirectedLink></net:link>'
                   for h in hrefs)
    return (f'<gml:featureMember><tn-ra:RailwayLinkSequence gml:id="{sequence_id}">'
            f'{body}</tn-ra:RailwayLinkSequence></gml:featureMember>')


def _document(body):
    return ('<?xml version="1.0" encoding="utf-8"?>'
            '<gml:FeatureCollection '
            'xmlns:gml="http://www.opengis.net/gml/3.2" '
            'xmlns:xlink="http://www.w3.org/1999/xlink" '
            'xmlns:net="http://inspire.ec.europa.eu/schemas/net/5.0" '
            'xmlns:gn="http://inspire.ec.europa.eu/schemas/gn/4.0" '
            'xmlns:tn="http://inspire.ec.europa.eu/schemas/tn/5.0" '
            'xmlns:tn-ra="http://inspire.ec.europa.eu/schemas/tn-ra/5.0">'
            + body + '</gml:FeatureCollection>').encode("utf-8")


# Prosty układ testowy w EPSG:3035: prosta oś wschód-zachód, tor przeciwny 3,5 m
# na północ od niej, plus para linków „linii 2/6" 11 m na południe, przez te same
# dwie stacje — czyli dokładnie ta pułapka, o którą chodzi w filtrze.
E0, N0 = 3923000.0, 3097000.0
STATIONS = [("8733", "Gare de l'Ouest"), ("8742", "Beekkant"), ("8292", "Étangs Noirs")]


def _fixture():
    body = ""
    for index, (code, station) in enumerate(STATIONS):
        body += _node(code, "Métro", station, (E0 + 200.0 * index, N0))
    reverse_codes = ["8731", "8741", "8291"]
    for index, code in enumerate(reverse_codes):
        body += _node(code, "Métro", STATIONS[index][1], (E0 + 200.0 * index, N0 + 3.5))
    for index, code in enumerate(["8382", "8744"]):
        body += _node(code, "Métro", STATIONS[index][1], (E0 + 200.0 * index, N0 - 11.0))
    body += _node("1961", "Tram", "Engeland", (E0 + 5000.0, N0))
    for index in range(len(STATIONS) - 1):
        body += _link(STATIONS[index][0], STATIONS[index + 1][0],
                      [(E0 + 200.0 * index, N0), (E0 + 200.0 * (index + 1), N0)])
        body += _link(reverse_codes[index + 1], reverse_codes[index],
                      [(E0 + 200.0 * (index + 1), N0 + 3.5), (E0 + 200.0 * index, N0 + 3.5)])
    body += _link("8382", "8744", [(E0, N0 - 11.0), (E0 + 200.0, N0 - 11.0)])
    body += _line("560011", "Métro line connecting GARE DE L'OUEST to STOCKEL", "seq_560011")
    body += _sequence("seq_560011", ["#link_560011", "#link_560011"])
    return _document(body)


def _fixture_alignment():
    """Oś w EPSG:31370 odpowiadająca torowi „w przód" dokumentu testowego."""
    points = [CRS.laea3035_to_lambert72(E0 + 20.0 * i, N0) for i in range(21)]
    origin = list(points[0])
    return {
        "id": "TEST_A",
        "source_crs": "EPSG:31370",
        "origin_source_crs": origin,
        "points": [[p[0] - origin[0], p[1] - origin[1], 0.0] for p in points],
        "stations": [{"stop_id": code, "name": name, "chainage_m": 200.0 * i}
                     for i, (code, name) in enumerate(STATIONS)],
    }


# --- parser -------------------------------------------------------------------

def test_inspire_parser_reads_nodes_links_lines_and_sequences():
    parsed = IR.parse_gml(_fixture())
    assert parsed["node_features"] == 9
    assert len(parsed["links"]) == 5
    assert len(parsed["lines"]) == 1
    assert len(parsed["sequences"]) == 1
    assert parsed["nodes"]["8733"]["mode"] == "Métro"
    assert parsed["nodes"]["8733"]["station"] == "Gare de l'Ouest"
    assert parsed["nodes"]["1961"]["mode"] == "Tram"
    assert parsed["lines"][0]["code"] == "1"
    assert parsed["lines"][0]["sequence_href"] == "#seq_560011"


def test_inspire_parser_keeps_metro_links_and_drops_tram():
    parsed = IR.parse_gml(_fixture())
    assert len(IR.metro_links(parsed)) == 5
    assert not any("1961" in (link["from"], link["to"]) for link in parsed["links"])
    parsed["nodes"]["8292"]["mode"] = "Tram"  # jedyny link dotykający 8292 to 8742->8292
    assert len(IR.metro_links(parsed)) == 4


def test_inspire_broken_link_sequence_references_are_counted_not_ignored():
    parsed = IR.parse_gml(_fixture())
    health = IR.topology_health(parsed)
    assert health["link_references"] == 2 and health["resolved"] == 0


def test_inspire_expired_validity_window_is_reported_not_fatal():
    parsed = IR.parse_gml(_fixture())
    expired = IR.validity_window(parsed, today="2026-09-01")
    assert expired["status"] == "wygasłe"
    assert expired["valid_from"] == "2026-03-02" and expired["valid_to"] == "2026-06-28"
    assert IR.validity_window(parsed, today="2026-05-01")["status"] == "aktualne"


def test_inspire_validity_window_survives_missing_declaration():
    parsed = IR.parse_gml(_fixture())
    for link in parsed["links"]:
        link["valid_from"] = link["valid_to"] = None
    assert IR.validity_window(parsed)["status"] == "brak deklaracji"


# --- filtr i klasyfikacja odsunięć --------------------------------------------

def test_inspire_station_walk_rejects_parallel_line_through_same_stations():
    parsed = IR.parse_gml(_fixture())
    chains = IR.package_chains(parsed, [code for code, _name in STATIONS])
    assert len(chains["forward"]) == 1 and len(chains["reverse"]) == 1
    assert [l["to"] for l in chains["forward"][0]] == ["8742", "8292"]
    assert [l["to"] for l in chains["reverse"][0]] == ["8741", "8731"]
    # link „linii 2/6" biegnie przez te same dwie stacje i musi zostać poza obiema ścieżkami
    used = {l["id"] for path in (chains["forward"][0], chains["reverse"][0]) for l in path}
    assert "link_5683828744" not in used


def test_inspire_signed_offsets_split_two_tracks_by_sign():
    document = _fixture_alignment()
    origin = document["origin_source_crs"]
    axis = [(p[0] + origin[0], p[1] + origin[1], 0.0) for p in document["points"]]
    frames = SW.rmf_frames(axis)
    parsed = IR.parse_gml(_fixture())
    chains = IR.package_chains(parsed, [code for code, _name in STATIONS])
    forward = IR.offsets_for(chains["forward"][0], axis, frames)
    reverse = IR.offsets_for(chains["reverse"][0], axis, frames)
    assert all(abs(r["offset_m"]) < 0.05 for r in IR.on_axis(forward))
    signs = {r["offset_m"] > 0 for r in IR.on_axis(reverse)}
    assert len(signs) == 1, "tor przeciwny musi leżeć w całości po jednej stronie osi"
    spacing = IR.measure_spacing(forward, reverse)
    assert spacing["status"] == "ok"
    assert abs(spacing["spacing_m"] - 3.5) < 0.05, spacing["spacing_m"]


def test_inspire_points_beyond_axis_end_are_flagged_not_measured():
    document = _fixture_alignment()
    origin = document["origin_source_crs"]
    axis = [(p[0] + origin[0], p[1] + origin[1], 0.0) for p in document["points"]]
    frames = SW.rmf_frames(axis)
    far = [{"id": "far", "points": [(E0 - 500.0, N0), (E0 - 480.0, N0)]}]
    rows = IR.offsets_for(far, axis, frames)
    assert all(row["beyond_axis"] for row in rows)
    assert IR.on_axis(rows) == []


def test_inspire_modes_count_separates_two_tracks_from_four():
    two = ([{"offset_m": 0.1} for _ in range(100)]
           + [{"offset_m": -3.3} for _ in range(100)])
    four = two + [{"offset_m": 10.5} for _ in range(30)] + [{"offset_m": -14.5} for _ in range(30)]
    assert len(IR.modes(two)) == 2
    assert len(IR.modes(four)) == 4


def test_inspire_modes_do_not_split_one_track_across_bin_edge():
    """Mod rozjeżdżony na dwa sąsiednie kosze to nadal jeden mod, nie dwa."""
    straddling = ([{"offset_m": -0.2} for _ in range(90)]
                  + [{"offset_m": 0.2} for _ in range(110)])
    assert len(IR.modes(straddling)) == 1


# --- zachowanie przy niedostępnym źródle --------------------------------------

def test_inspire_unavailable_source_is_a_result_not_a_crash():
    with tempfile.TemporaryDirectory() as directory:
        out = os.path.join(directory, "spacing.json")
        # port 9 to discard/TCP; nic tu nie nasłuchuje, więc połączenie pada od razu
        code = IR.main(["--url", "http://127.0.0.1:9/rail", "--out", out, "--timeout", "2"])
        assert code == 0
        report = json.load(open(out, encoding="utf-8"))
        assert report["status"] == "niedostępne"
        assert report["reason"]
        assert report["url"] == "http://127.0.0.1:9/rail"


def test_inspire_missing_download_url_is_a_result_not_a_crash():
    with tempfile.TemporaryDirectory() as directory:
        out = os.path.join(directory, "spacing.json")
        registry = os.path.join(directory, "sources.json")
        with open(registry, "w", encoding="utf-8") as handle:
            json.dump({"sources": [{"id": IR.SOURCE_ID, "download_url": None}]}, handle)
        original = IR.SOURCE_REGISTRY
        try:
            IR.SOURCE_REGISTRY = registry
            assert IR.download_url(registry) is None
            assert IR.main(["--out", out]) == 0
        finally:
            IR.SOURCE_REGISTRY = original
        assert json.load(open(out, encoding="utf-8"))["status"].startswith("brak download_url")


def test_inspire_source_registry_has_captured_download_url():
    registry = json.load(open(os.path.join(ROOT, "data", "network", "sources.json"),
                              encoding="utf-8"))
    row = {r["id"]: r for r in registry["sources"]}[IR.SOURCE_ID]
    assert row["download_url"].startswith("https://")
    assert row["crs"] == "EPSG:3035"
    assert row["license"] == "CC BY 4.0"
    assert row["attribution"] == "Source: STIB-MIVB - Open Data"
    for phrase in ("srsDimension=2", "RailwayLinkSequence", "validTo"):
        assert phrase in row["limitations"], phrase

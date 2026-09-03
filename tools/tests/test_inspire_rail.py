#!/usr/bin/env python3
"""Testy INSPIRE Rails i odwzorowania EPSG:3035 (T-111). Bez sieci i bez pytest.

Parser GML jest testowany na dokumencie budowanym w locie, więc testy nie zależą od
378 kB archiwum z portalu ani od internetu. Jedyne gniazdo, jakie tu powstaje, to
zamknięty port na 127.0.0.1 — po to, żeby sprawdzić, że niedostępne źródło jest
wynikiem, a nie wyjątkiem.
"""
import contextlib
import io
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


# --- granice progów i reguły klasyfikacji -------------------------------------
#
# Ta sekcja powstała z triażu przemiatania mutacyjnego (30 mutacji ocalałych z 41
# na `tools/track/inspire_rail.py`). Testy wyżej sprawdzały, że pomiar w ogóle
# wychodzi; te sprawdzają, gdzie dokładnie leżą jego progi, bo tylko wartość RÓWNA
# progowi odróżnia `<` od `<=`.
#
# Pułapka, którą trzeba tu obchodzić: `abs((6700.0 + 0.01) - 6700.0)` to
# 0,010000000000218, czyli już NAD progiem 0,01. Naiwne „wejście na granicę"
# przez dodawanie i odejmowanie dużych liczb nigdy granicy nie dotyka. Granica jest
# dokładna tylko wtedy, gdy jedna ze stron jest zerem, gdy próg jest potęgą dwójki,
# gdy porównywane są napisy albo gdy próg BIERZE SIĘ Z SAMEGO POMIARU. Każdy test
# poniżej mówi w docstringu, z której z tych czterech dróg korzysta.


def _axis_from_fixture():
    """Oś testowa w EPSG:31370, taka sama jak w testach pomiarowych wyżej."""
    document = _fixture_alignment()
    origin = document["origin_source_crs"]
    return [(p[0] + origin[0], p[1] + origin[1], 0.0) for p in document["points"]]


def _rows(offsets):
    """Wiersze odsunięć w postaci, jaką produkuje `offsets_for`, ale bez geometrii."""
    return [{"offset_m": value, "beyond_axis": False} for value in offsets]


class _IdentityCRS:
    """Przeliczenie tożsamościowe: pozwala podać `offsets_for` gotowy kilometraż.

    Bez tego nie da się dotknąć progu `1e-3` w `beyond_axis`: prawdziwe
    `laea3035_to_lambert72` daje współrzędne rzędu 1,5e5, a kilometraż liczony z ich
    różnic wypada 0,001 ± 1e-11 — nigdy dokładnie na progu.
    """

    @staticmethod
    def laea3035_to_lambert72(x, y):
        return (x, y)


def test_inspire_validity_window_is_current_on_its_last_declared_day():
    """Dzień równy `validTo` to jeszcze ważność, nie przeterminowanie.

    Po co: `latest_end < today` kontra `<=` różnią się WYŁĄCZNIE w dniu równym
    dacie końcowej. Testy wyżej pytają o 2026-05-01 i 2026-09-01, czyli mijają granicę
    z obu stron, nie dotykając jej. Granica jest tu dokładna, bo porównanie idzie na
    napisach ISO, a nie na liczbach zmiennoprzecinkowych.
    """
    parsed = IR.parse_gml(_fixture())
    assert IR.validity_window(parsed, today="2026-06-28")["status"] == "aktualne"
    # kontrola negatywna: doba dalej i ten sam plik jest już wygasły
    assert IR.validity_window(parsed, today="2026-06-29")["status"] == "wygasłe"


def test_inspire_station_walk_allows_a_hop_inside_one_station():
    """Przejście musi umieć zostać na tej samej stacji przez jeden link.

    Po co: na Schumanie kierunek przeciwny idzie 8071 -> 8065 -> 8061, czyli dwa linki
    pod jedną nazwą stacji. Dokument testowy wyżej takiego skoku nie ma, więc gałąź
    `elif station == station_names[index]` nie była wykonywana w ogóle i dowolna jej
    zmiana przechodziła niezauważona. Bez tej gałęzi pakiet A rozpada się na zero
    ścieżek, a skrypt kończy się na „niejednoznaczne przejście po stacjach".
    """
    nodes = {
        "8071": {"station": "Schuman", "mode": IR.METRO},
        "8065": {"station": "Schuman", "mode": IR.METRO},
        "8061": {"station": "Merode", "mode": IR.METRO},
        "8099": {"station": "Arts-Loi", "mode": IR.METRO},
    }
    links = [
        {"id": "wewnatrz", "from": "8071", "to": "8065"},
        {"id": "szlak", "from": "8065", "to": "8061"},
        # wabik: link do stacji, której w ogóle nie ma na liście przejścia
        {"id": "wabik", "from": "8071", "to": "8099"},
    ]
    paths = IR.walk_stations(links, nodes, ["Schuman", "Merode"], ["8071"])
    assert len(paths) == 1, [[l["id"] for l in p] for p in paths]
    assert [l["id"] for l in paths[0]] == ["wewnatrz", "szlak"]

    # kontrola negatywna: skok wolno zrobić tylko w obrębie stacji bieżącej. Gdy
    # wewnętrzny link prowadzi do obcej stacji, przejście nie ma czym dojść do Merode.
    nodes["8065"]["station"] = "Arts-Loi"
    assert IR.walk_stations(links, nodes, ["Schuman", "Merode"], ["8071"]) == []


def test_inspire_corridor_selection_keeps_a_link_exactly_on_its_radius():
    """Promień korytarza jest domknięty: link leżący dokładnie na nim jeszcze wpada.

    Po co: `<=` kontra `<` różni się tylko dla linku odległego o dokładnie `radius_m`.
    Granica jest tu dokładna, bo próg NIE jest wpisaną liczbą dziesiętną — jest tą samą
    wartością zmiennoprzecinkową, którą wyliczyła funkcja mierząca odległość. Kontrolna
    selekcja korytarzowa istnieje po to, żeby pokazać, ile linii 2/6 wciąga pomiar „po
    bliskości"; przesunięcie jej progu o jeden bit zmienia tę liczbę.
    """
    parsed = IR.parse_gml(_fixture())
    axis = _axis_from_fixture()
    parallel = [l for l in IR.metro_links(parsed) if l["id"] == "link_5683828744"][0]
    distance = min(SW.point_to_polyline((p[0], p[1], 0.0), axis)
                   for p in (CRS.laea3035_to_lambert72(x, y) for x, y in parallel["points"]))
    assert 10.0 < distance < 12.0, distance  # tor „linii 2/6" leży 11 m od osi

    on_radius = {l["id"] for l in IR.corridor_links(parsed, axis, radius_m=distance)}
    assert parallel["id"] in on_radius
    # kontrola negatywna: jeden bit ciaśniej i wypada dokładnie ten jeden link
    tighter = {l["id"] for l in IR.corridor_links(
        parsed, axis, radius_m=math.nextafter(distance, 0.0))}
    assert on_radius - tighter == {parallel["id"]}


def test_inspire_projection_skips_only_a_truly_zero_length_segment():
    """Zerowy segment osi jest pomijany, dwucentymetrowy — mierzony.

    Po co: próg `segment <= 0.0` broni przed dzieleniem przez zero i nie ma prawa być
    niczym innym niż zerem. Podniesienie go do 0,001 (czyli 3,2 cm długości) wycina
    z pomiaru krótkie segmenty, które są normalną osią, a nie zwyrodnieniem. Granica
    jest dokładna, bo jedna strona porównania to zero.
    """
    doubled = [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (128.0, 0.0, 0.0)]
    chainage, offset, distance = IR.project_signed(
        (64.0, -3.5), doubled, SW.rmf_frames(doubled))
    assert chainage == 64.0 and abs(abs(offset) - 3.5) < 1e-12 and abs(distance - 3.5) < 1e-12

    tiny = [(0.0, 0.0, 0.0), (0.02, 0.0, 0.0)]
    chainage, _offset, _distance = IR.project_signed((0.01, -3.5), tiny, SW.rmf_frames(tiny))
    assert chainage == 0.01, chainage


def test_inspire_projection_does_not_round_the_foot_to_the_segment_ends():
    """Spodek rzutu nie jest dociągany ani do początku, ani do końca segmentu.

    Po co: obcięcie `t` do przedziału [0, 1] jest po to, żeby punkt za końcem osi
    rzutował się na jej koniec. Przesunięcie któregokolwiek z tych dwóch progów o
    procent zamienia obcięcie w ciche zaokrąglenie: punkt 5 cm za początkiem osi
    dostaje kilometraż 0, a punkt metr za końcem — kilometraż o metr za duży, czyli
    pomiar poza osią udający pomiar na osi.
    """
    axis = [(0.0, 0.0, 0.0), (200.0, 0.0, 0.0)]
    frames = SW.rmf_frames(axis)

    near_start = IR.project_signed((0.05, -3.5), axis, frames)
    assert near_start[0] == 0.05, near_start

    past_end = IR.project_signed((201.0, -3.5), axis, frames)
    assert past_end[0] == 200.0, past_end
    assert abs(past_end[2] - math.dist((201.0, -3.5), (200.0, 0.0))) < 1e-12

    # kontrola negatywna: obcięcie MA działać — punkt przed początkiem osi
    # dostaje kilometraż 0 i odległość liczoną do pierwszego wierzchołka
    before_start = IR.project_signed((-1.0, -3.5), axis, frames)
    assert before_start[0] == 0.0
    assert abs(before_start[2] - math.dist((-1.0, -3.5), (0.0, 0.0))) < 1e-12


def test_inspire_projection_keeps_the_first_of_two_equidistant_segments():
    """Przy remisie odległości liczy się ramka segmentu WCZEŚNIEJSZEGO.

    Po co: dla punktu w zewnętrznym klinie załamania osi oba sąsiednie segmenty dają
    ten sam spodek — sam wierzchołek — więc `math.dist` zwraca dla obu identyczny bit
    w bit wynik. Remis jest tu dokładny bez żadnej sztuczki. Rozstrzyga go `<` kontra
    `<=`, a stawką nie jest odległość (ta sama), tylko znakowane odsunięcie: ramki obu
    segmentów mają inny wektor „w prawo", więc ta sama próbka raz ma odsunięcie 10 m,
    a raz 8,66 m. To jest liczba, którą raport porównuje z `track_offsets`.
    """
    corner = 100.0
    axis = [(0.0, 0.0, 0.0), (corner, 0.0, 0.0),
            (corner + 100.0 * math.cos(math.radians(60.0)),
             100.0 * math.sin(math.radians(60.0)), 0.0)]
    frames = SW.rmf_frames(axis)
    chainage, offset, distance = IR.project_signed((corner, -10.0), axis, frames)
    assert distance == 10.0 and chainage == corner
    assert abs(offset - 10.0) < 1e-12, offset

    # kontrola negatywna: bez remisu wygrywa segment naprawdę bliższy — punkt
    # przesunięty na drugi segment dostaje jego ramkę i odsunięcie o innej wartości
    second = IR.project_signed(
        (axis[2][0] * 0.5 + corner * 0.5, axis[2][1] * 0.5), axis, frames)
    assert second[0] > corner and abs(second[1]) < 1e-9


def test_inspire_beyond_axis_flag_is_exact_on_both_thresholds():
    """Punkt dokładnie na progu 1e-3 od któregokolwiek końca osi jest już „poza osią".

    Po co: flaga `beyond_axis` decyduje, które próbki w ogóle wchodzą do pomiaru
    rozstawu, a różnicy między `<=` a `<` nie widać nigdzie poza wartością równą progowi.
    Żeby ją dotknąć, oś ma długość 128 m — potęgę dwójki — i zaczyna się w zerze.
    Wtedy `t = px/128` i `t*128 = px` są dokładne, więc kilometraż punktu jest CO DO
    BITU równy jego współrzędnej i można go postawić na 1e-3 oraz na `128 - 1e-3`.
    Przeliczenie EPSG:3035 -> Lambert72 jest na czas testu tożsamościowe; z prawdziwym
    kilometraż wypada 0,001 ± 1e-11 i próg pozostaje nietykalny.
    """
    axis = [(0.0, 0.0, 0.0), (128.0, 0.0, 0.0)]
    frames = SW.rmf_frames(axis)
    total = SW.chainages(axis)[-1]
    assert total == 128.0
    link = [{"id": "L", "points": [(1e-3, 0.0), (0.001005, 0.0),
                                   (total - 1e-3, 0.0), (64.0, 0.0)]}]
    original = IR.CRS
    try:
        IR.CRS = _IdentityCRS
        rows = IR.offsets_for(link, axis, frames)
    finally:
        IR.CRS = original

    assert [r["chainage_m"] for r in rows] == [1e-3, 0.001005, total - 1e-3, 64.0]
    # na progu — poza osią; 5 mikrometrów za progiem — już na osi; w środku — na osi
    assert [r["beyond_axis"] for r in rows] == [True, False, True, False]
    assert [r["chainage_m"] for r in IR.on_axis(rows)] == [0.001005, 64.0]


def test_inspire_histogram_range_is_left_closed_and_right_open():
    """Zakres histogramu to [-20, 20): lewy koniec wpada, prawy nie.

    Po co: obcięcie do ±20 m jest jedynym powodem, dla którego histogram pokazuje mody
    zamiast setek jednoelementowych koszy — i jedynym miejscem, w którym próbka może
    zniknąć z raportu bez śladu. Granica jest dokładna, bo wartości są podane wprost,
    tą samą liczbą co domyślny próg, bez żadnej arytmetyki po drodze.
    """
    bins = IR.histogram(_rows([-20.0, 20.0, 19.999]))
    assert sum(b["count"] for b in bins) == 2, bins
    assert bins[0]["from_m"] == -20.0
    assert max(b["to_m"] for b in bins) == 20.0
    # kontrola negatywna: jedna próbka odsunięta o milimetr poza zakres i znika ona,
    # a nie którakolwiek inna
    outside = IR.histogram(_rows([-20.001, 20.0, 19.999]))
    assert sum(b["count"] for b in outside) == 1
    assert [b["from_m"] for b in outside] == [19.0]


def test_inspire_mode_share_threshold_is_inclusive():
    """Kosz niosący dokładnie `MODE_MIN_SHARE` próbek to jeszcze mod.

    Po co: liczba modów jest w tym skrypcie testem filtra topologicznego — dwa mody
    znaczą „dwa tory", cztery znaczą „wciągnęliśmy linie 2/6". Próg udziału decyduje,
    co jest modem, a `<` od `<=` odróżnia wyłącznie udział równy progowi.
    Granica jest tu dokładna przez dobór liczb: 3/200 to dokładnie ta sama liczba
    zmiennoprzecinkowa co literał 0.015, bo iloraz jest wymierny i obie drogi zaokrąglają
    się do tego samego bitu. Test to sprawdza wprost, zamiast na to liczyć.
    """
    assert 3 / 200 == IR.MODE_MIN_SHARE
    rows = _rows([0.5] * 197 + [10.5] * 3)
    assert len(IR.modes(rows)) == 2, IR.modes(rows)

    # kontrola negatywna: jedna próbka mniej w małym koszu (2/199) i zostaje jeden mod
    thinner = _rows([0.5] * 197 + [10.5] * 2)
    assert len(IR.modes(thinner)) == 1, IR.modes(thinner)


def test_inspire_modes_reject_a_bin_tied_with_its_neighbour():
    """Kosz równy sąsiadowi nie jest modem — mod musi być ŚCIŚLE większy.

    Po co: to jest cała obrona przed policzeniem jednego toru dwa razy. Test wyżej
    używa koszy 90 i 110, czyli mija remis; dopiero 100 i 100 pokazuje, że warunek jest
    ostry. Liczności są całkowite, więc remis jest dokładny.
    """
    tied = _rows([-0.5] * 100 + [0.5] * 100)
    assert IR.modes(tied) == []
    # kontrola negatywna: jedna próbka więcej po jednej stronie i mod jest dokładnie jeden
    broken_tie = _rows([-0.5] * 100 + [0.5] * 101)
    assert len(IR.modes(broken_tie)) == 1
    assert IR.modes(broken_tie)[0]["from_m"] == 0.0


def test_inspire_running_filter_keeps_a_sample_exactly_at_its_limit():
    """Odsunięcie równe `RUNNING_OFFSET_MAX_M` to jeszcze szlak, nie rozjazd.

    Po co: filtr 20 m odsiewa próbki z węzła Beekkant, żeby rozjazd nie wszedł do
    mediany międzytorza. Wartość równa progowi jest jedynym miejscem, w którym widać
    różnicę `<=` od `<`; podana jest wprost, więc granica jest dokładna.
    """
    axis_side = _rows([0.0, 0.0])
    at_limit = IR.measure_spacing(axis_side, _rows([-20.0, -3.5]))
    assert at_limit["opposite_track"]["samples"] == 2
    assert at_limit["opposite_track"]["median_m"] == -11.75
    assert at_limit["opposite_track"]["min_m"] == -20.0

    # kontrola negatywna: milimetr poza progiem i ta jedna próbka wypada z pomiaru
    over_limit = IR.measure_spacing(axis_side, _rows([-20.001, -3.5]))
    assert over_limit["opposite_track"]["samples"] == 1
    assert over_limit["opposite_track"]["median_m"] == -3.5


def test_inspire_zero_offset_sample_belongs_to_neither_track():
    """Próbka dokładnie na osi nie należy ani do lewego, ani do prawego toru.

    Po co: podział na strony jest po ostrym znaku i tylko dlatego mediana toru
    przeciwnego nie jest ciągnięta przez punkty leżące na samej osi. Cztery mutacje
    naraz mieszczą się w tym jednym rozstrzygnięciu: dopuszczenie zera do lewej strony,
    dopuszczenie go do prawej oraz przesunięcie któregokolwiek z dwóch zer na 0,001,
    co wciąga do klasyfikacji próbki milimetrowe. Granica jest dokładna, bo próg jest
    zerem.
    """
    axis_side = _rows([0.0])
    spacing = IR.measure_spacing(axis_side, _rows([-4.0, -3.0, 0.0, 0.0005]))
    assert spacing["opposite_track"]["samples"] == 2
    assert spacing["opposite_track"]["median_m"] == -3.5
    assert spacing["wrong_side_samples"] == 1

    # kontrola negatywna: ta sama próbka przesunięta o pół milimetra na lewo
    # dokłada się do toru przeciwnego i zmienia dokładnie te dwie liczby
    flipped = IR.measure_spacing(axis_side, _rows([-4.0, -3.0, -0.0005, 0.0005]))
    assert flipped["opposite_track"]["samples"] == 3
    assert flipped["opposite_track"]["median_m"] == -3.0
    assert flipped["wrong_side_samples"] == 1


def test_inspire_side_choice_on_a_tie_takes_the_negative_side():
    """Przy równej liczbie próbek po obu stronach torem przeciwnym jest strona ujemna.

    Po co: `len(left) >= len(right)` decyduje, którą chmurę raport nazwie „torem
    przeciwnym", a którą „próbkami po złej stronie". Remis liczności jest dokładny
    (to liczby całkowite) i tylko on odróżnia `>=` od `>`. Bez tego rozstrzygnięcia
    ten sam plik wejściowy dałby raz rozstaw 3,5 m, a raz 7 m.
    """
    axis_side = _rows([0.0])
    tie = IR.measure_spacing(axis_side, _rows([-3.5, -3.5, 7.0, 7.0]))
    assert tie["opposite_track"]["median_m"] == -3.5
    assert tie["spacing_m"] == 3.5
    assert tie["wrong_side_samples"] == 2

    # kontrola negatywna: jedna próbka więcej po stronie dodatniej i to ona
    # przejmuje rolę toru przeciwnego
    right_wins = IR.measure_spacing(axis_side, _rows([-3.5, -3.5, 7.0, 7.0, 7.0]))
    assert right_wins["opposite_track"]["median_m"] == 7.0
    assert right_wins["spacing_m"] == 7.0
    assert right_wins["wrong_side_samples"] == 2


def test_inspire_spacing_by_link_groups_rows_under_their_own_link():
    """Rozstaw odcinkami liczy się z próbek TEGO linku, nie wszystkich pozostałych.

    Po co: ta tabela istnieje po to, żeby jedna liczba na 6,7 km nie ukryła węzła
    Beekkant. Gdyby dopasowanie wiersza do linku poszło odwrotnie, tabela nadal miałaby
    tyle samo wierszy, sensowne nazwy odcinków i wiarygodne liczby — tylko przypisane
    do niewłaściwych odcinków. Żaden test dotąd tej funkcji nie wołał.
    """
    nodes = {"a": {"station": "Beekkant"}, "b": {"station": "Étangs Noirs"},
             "c": {"station": "Comte de Flandre"}}
    links = [{"id": "L1", "from": "a", "to": "b"}, {"id": "L2", "from": "b", "to": "c"}]
    rows = [{"link": "L1", "offset_m": -3.0}, {"link": "L1", "offset_m": -4.0},
            {"link": "L2", "offset_m": 9.0}]
    out = IR.spacing_by_link(rows, links, nodes)
    assert [r["link"] for r in out] == ["L1", "L2"]
    assert out[0]["section"] == "Beekkant -> Étangs Noirs"
    assert out[0]["samples"] == 2 and out[0]["median_offset_m"] == -3.5
    assert out[0]["min_offset_m"] == -4.0 and out[0]["max_offset_m"] == -3.0
    assert out[1]["samples"] == 1 and out[1]["median_offset_m"] == 9.0

    # kontrola negatywna: wiersz z linku spoza tabeli nie dokłada się do żadnego wiersza
    stray = IR.spacing_by_link(rows + [{"link": "L9", "offset_m": 100.0}], links, nodes)
    assert [r["samples"] for r in stray] == [2, 1]
    assert [r["max_offset_m"] for r in stray] == [-3.0, 9.0]


def _run_main(gml_bytes, alignment, directory):
    """Uruchamia CLI na lokalnym snapshotcie; zwraca raport i to, co poszło na stdout."""
    gml = os.path.join(directory, "rail.gml")
    with open(gml, "wb") as handle:
        handle.write(gml_bytes)
    axis_path = os.path.join(directory, "alignment.json")
    with open(axis_path, "w", encoding="utf-8") as handle:
        json.dump(alignment, handle, ensure_ascii=False)
    out = os.path.join(directory, "spacing.json")
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = IR.main(["--gml-file", gml, "--alignment", axis_path, "--out", out])
    assert code == 0
    return json.load(open(out, encoding="utf-8")), buffer.getvalue()


def test_inspire_main_measures_the_spacing_when_the_walk_is_unambiguous():
    """Jednoznaczne przejście po stacjach ma prowadzić do POMIARU, nie do komunikatu.

    Po co: bramka `len(forward) != 1 or len(reverse) != 1` przerywa skrypt przed
    pomiarem. Dopóki nikt nie uruchamiał `main` na snapshotcie, każda jej zmiana —
    odwrócenie warunku albo podniesienie oczekiwanej liczby ścieżek z 1 na 2 —
    przechodziła niezauważona, a skrypt zamiast rozstawu zwracał zdanie o
    niejednoznaczności i kod 0. Test sprawdza też, że podsumowanie z liczbą rozstawu
    naprawdę trafia na stdout: gałąź drukująca ma własny warunek na statusie.
    """
    with tempfile.TemporaryDirectory() as directory:
        report, printed = _run_main(_fixture(), _fixture_alignment(), directory)
    assert report["chains"]["forward_paths"] == 1
    assert report["chains"]["reverse_paths"] == 1
    assert report["status"] == "ok"
    assert abs(report["spacing"]["spacing_m"] - 3.5) < 0.05, report["spacing"]
    assert report["spacing"]["half_spacing_m"] == round(report["spacing"]["spacing_m"] / 2.0, 3)
    assert len(report["modes_filtered"]) == 2, report["modes_filtered"]
    assert "[ROZSTAW] rozstaw" in printed, printed


def test_inspire_main_stops_on_an_ambiguous_walk_instead_of_measuring():
    """Kontrola negatywna bramki: dwie ścieżki „w przód" mają zatrzymać pomiar.

    Drugi link między tą samą parą stacji to dokładnie ta sytuacja, dla której bramka
    powstała — nie wiadomo, który tor opisuje oś, więc rozstaw nie ma sensu.
    """
    doubled = _fixture().decode("utf-8").replace(
        "</gml:FeatureCollection>",
        _link(STATIONS[0][0], STATIONS[1][0], [(E0, N0), (E0 + 200.0, N0)])
        .replace("link_5687338742", "link_dublet") + "</gml:FeatureCollection>")
    with tempfile.TemporaryDirectory() as directory:
        report, printed = _run_main(doubled.encode("utf-8"), _fixture_alignment(), directory)
    assert report["chains"]["forward_paths"] == 2
    assert report["status"] == "niejednoznaczne przejście po stacjach"
    assert "spacing" not in report
    assert "niejednoznaczne" in printed

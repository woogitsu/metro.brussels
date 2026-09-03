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


# --- triaż ocalałych mutacji: geometria osi ----------------------------------
#
# Przemiatanie mutacyjne z 03.09.2026 dało dla `build_alignment.py` 69 mutacji
# i 57 ocalałych — największa pula w czystym Pythonie, jaka została. Testy powyżej
# sprawdzają, że funkcje LICZĄ dobrze na wejściu grzecznym. Nie sprawdzały,
# co robią NA GRANICY: przy zdublowanym wierzchołku, przy cięciu dokładnie
# w wierzchołku, przy rzucie wypadającym za segment. Tam mieszkały wszystkie
# ocalałe. Poniżej są testy właśnie tych miejsc.


def test_alignment_projection_skips_zero_length_segments():
    """Zdublowany wierzchołek w źródle STIB nie jest hipotezą — jest w danych.

    Bez pominięcia takiego segmentu rzut dzieli przez zero. Test przechodzi tylko
    wtedy, gdy pominięcie NAPRAWDĘ jest, bo inaczej leci ZeroDivisionError.
    """
    line = [(0.0, 0.0), (50.0, 0.0), (50.0, 0.0), (100.0, 0.0)]
    chainage, offset, _segment = B.project_on_polyline(line, (70.0, 3.0))
    assert abs(chainage - 70.0) < 1e-9, chainage
    assert abs(offset - 3.0) < 1e-9, offset


def test_alignment_projection_uses_segments_shorter_than_a_decimetre():
    """Pomijany ma być segment ZEROWY, nie po prostu krótki.

    Warunek stoi na kwadracie długości, więc próg podniesiony do 0.001 wycinałby
    wszystko poniżej 3,2 cm — a wtedy oś złożona z krótkich segmentów nie miałaby
    do czego się rzutować i wynik wracałby jako `inf`.
    """
    line = [(0.0, 0.0), (0.02, 0.0), (0.04, 0.0)]
    chainage, offset, _segment = B.project_on_polyline(line, (0.03, 0.0))
    assert math.isfinite(offset), offset
    assert abs(chainage - 0.03) < 1e-9, chainage


def test_alignment_projection_keeps_a_foot_just_past_the_start_of_a_segment():
    """Rzut 0,5 m za początek 1000-metrowego segmentu to t = 0,0005.

    Zaokrąglenie takiego t do zera przesunęłoby kotwicę stacji o pół metra
    i nie zostawiło po sobie żadnego śladu w metrykach.
    """
    line = [(0.0, 0.0), (1000.0, 0.0)]
    chainage, offset, _segment = B.project_on_polyline(line, (0.5, 1.0))
    assert abs(chainage - 0.5) < 1e-9, chainage
    assert abs(offset - 1.0) < 1e-9, offset


def test_alignment_projection_clamps_a_foot_past_the_end_of_the_polyline():
    """Cel 5 m za końcem osi ma dać rzut NA koniec, z odległością 5 m.

    Bez domknięcia t do 1 rzut wyjechałby poza polilinię: kilometraż 1005 m
    na osi, która ma 1000 m, i odległość 0 m zamiast 5 m.
    """
    line = [(0.0, 0.0), (1000.0, 0.0)]
    chainage, offset, _segment = B.project_on_polyline(line, (1005.0, 0.0))
    assert abs(chainage - 1000.0) < 1e-9, chainage
    assert abs(offset - 5.0) < 1e-9, offset


def test_alignment_projection_keeps_the_first_of_two_equally_close_feet():
    """Oś zawrócona sama na siebie daje dwa rzuty o identycznej odległości.

    Rozstrzygnięcie musi być deterministyczne i musi wskazywać MNIEJSZY kilometraż,
    bo inaczej kotwica stacji skakałaby na drugą stronę pętli przy tej samej
    geometrii wejściowej.
    """
    line = [(0.0, 0.0), (100.0, 0.0), (0.0, 0.0)]
    chainage, offset, _segment = B.project_on_polyline(line, (50.0, 10.0))
    assert abs(offset - 10.0) < 1e-9, offset
    assert abs(chainage - 50.0) < 1e-9, chainage


def test_alignment_slice_cuts_inside_a_segment_and_keeps_the_vertex_between():
    line = [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]
    sliced = [p for p, _ in B.slice_polyline(line, 50.0, 150.0)]
    assert sliced == [(50.0, 0.0), (100.0, 0.0), (150.0, 0.0)], sliced


def test_alignment_slice_starting_exactly_on_a_vertex_returns_it_once():
    line = [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]
    sliced = [p for p, _ in B.slice_polyline(line, 100.0, 150.0)]
    assert sliced == [(100.0, 0.0), (150.0, 0.0)], sliced


def test_alignment_slice_from_zero_keeps_the_first_vertex():
    line = [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]
    sliced = [p for p, _ in B.slice_polyline(line, 0.0, 150.0)]
    assert sliced == [(0.0, 0.0), (100.0, 0.0), (150.0, 0.0)], sliced


def test_alignment_slice_ending_exactly_on_a_vertex_keeps_it_once():
    line = [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]
    sliced = [p for p, _ in B.slice_polyline(line, 0.0, 100.0)]
    assert sliced == [(0.0, 0.0), (100.0, 0.0)], sliced


def test_alignment_slice_origin_tags_are_output_that_nobody_reads():
    """Etykieta pochodzenia z `slice_polyline` jest MARTWA i test to utrwala.

    Wszystkie cztery miejsca w `build_alignment.py`, które wołają tę funkcję,
    robią `[p for p, _ in slice_polyline(...)]` — etykieta jest odrzucana na
    wejściu. Do `data/track/*.json` nie trafia; plik osi nie ma w ogóle klucza
    `provenance` per punkt (ma go `resample_uniform`, i TA etykieta jest żywa).

    Test nie sprawdza więc, jaka etykieta jest — sprawdza, że każdy punkt jakąś
    ma i że jest napisem. Przypinanie konkretnych wartości znaczyłoby, że testy
    bronią czegoś, na czym nic nie stoi; wtedy zmiana etykiety wyglądałaby na
    regresję, a nie jest. Decyzja, czy etykietę uruchomić, czy usunąć, należy
    do właściciela — jest opisana w PR-ze, nie rozstrzygnięta tutaj.
    """
    line = [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]
    sliced = B.slice_polyline(line, 50.0, 150.0)
    assert len(sliced) == 3, sliced
    assert all(isinstance(tag, str) and tag for _p, tag in sliced), sliced


def test_alignment_slice_of_the_whole_polyline_reaches_the_last_vertex():
    """Regresja z pakietu D: bez domknięcia prawego końca ginęło 86,8 m osi."""
    line = [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]
    sliced = B.slice_polyline(line, 0.0, 200.0)
    assert [p for p, _ in sliced] == [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)], sliced
    assert abs(B.polyline_length([p for p, _ in sliced]) - 200.0) < 1e-9


def test_alignment_slice_dedup_threshold_is_a_micrometre_not_more():
    """Dwa punkty oddalone o 1,005 µm to nadal DWA punkty.

    Próg sklejania jest po to, żeby wyrzucić duplikat co do bitu, a nie żeby
    czyścić geometrię. Test stoi tuż nad progiem, bo tylko tam widać różnicę
    między „usuwam duplikat" a „upraszczam oś".
    """
    line = [(0.0, 0.0), (1.005e-6, 0.0), (100.0, 0.0)]
    sliced = B.slice_polyline(line, 0.0, 100.0)
    assert len(sliced) == 3, sliced


def test_alignment_slice_dedup_threshold_is_open_at_exactly_a_micrometre():
    line = [(0.0, 0.0), (1e-6, 0.0), (100.0, 0.0)]
    sliced = B.slice_polyline(line, 0.0, 100.0)
    assert len(sliced) == 3, sliced


def test_alignment_point_at_interpolates_inside_the_first_segment():
    """Kilometraż 0,5 m ma dać punkt 0,5 m od początku, nie sam początek."""
    line = [(0.0, 0.0), (100.0, 0.0)]
    assert B.point_at(line, 0.5) == (0.5, 0.0)
    assert B.point_at(line, 0.0) == (0.0, 0.0)


def test_alignment_point_at_survives_a_duplicated_vertex():
    """Segment zerowej długości nie może dzielić przez zero."""
    line = [(0.0, 0.0), (50.0, 0.0), (50.0, 0.0), (100.0, 0.0)]
    assert B.point_at(line, 50.0) == (50.0, 0.0)
    assert B.point_at(line, 75.0) == (75.0, 0.0)


def test_alignment_point_at_interpolates_inside_segments_shorter_than_a_metre():
    """Zabezpieczenie dotyczy segmentu ZEROWEGO, nie krótkiego.

    Oś STIB ma w łukach segmenty poniżej metra; podniesienie progu do 1 m
    zamieniłoby interpolację na skok do najbliższego wierzchołka.
    """
    line = [(0.0, 0.0), (0.5, 0.0), (1.0, 0.0)]
    assert B.point_at(line, 0.25) == (0.25, 0.0)
    assert B.point_at(line, 0.75) == (0.75, 0.0)


def test_alignment_point_at_clamps_outside_the_polyline():
    line = [(0.0, 0.0), (100.0, 0.0)]
    assert B.point_at(line, -5.0) == (0.0, 0.0)
    assert B.point_at(line, 100.0) == (100.0, 0.0)
    assert B.point_at(line, 500.0) == (100.0, 0.0)


def test_alignment_resample_drops_a_candidate_exactly_half_a_step_from_an_anchor():
    """Próbka dokładnie pół kroku od kotwicy ma ZNIKNĄĆ — kotwica ma pierwszeństwo.

    Warunek jest ostry (`>`), więc granica należy do kotwicy. Gdyby był
    nieostry, przy kotwicy 5 m i kroku 10 m zostałyby obok siebie punkty
    0, 5 i 10 — dwa razy gęściej, niż mówi krok, i akurat przy peronie.
    """
    line = [(0.0, 0.0), (100.0, 0.0)]
    sampled = B.resample_uniform(line, 10.0, [5.0])
    xs = [round(p[0], 6) for p, _ in sampled]
    assert 0.0 not in xs, xs
    assert 10.0 not in xs, xs
    assert 5.0 in xs and 20.0 in xs, xs
    assert xs[0] == 5.0, xs


def test_alignment_densify_does_not_duplicate_a_vertex_at_an_exact_step():
    """Segment długości dokładnie jednego kroku nie dostaje punktu pośredniego.

    Dodanie go zdublowałoby wierzchołek b: raz jako punkt pośredni, raz jako
    początek następnego segmentu. Statystyki odsunięcia liczą się PO punktach,
    więc duplikat cicho przeważyłby medianę.
    """
    assert B.densify([(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)], 10.0) == \
        [(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)]


def test_alignment_densify_splits_a_segment_longer_than_the_step():
    out = B.densify([(0.0, 0.0), (25.0, 0.0)], 10.0)
    assert out[0] == (0.0, 0.0) and out[-1] == (25.0, 0.0), out
    assert max(math.dist(a, b) for a, b in zip(out, out[1:])) <= 10.0 + 1e-9, out


def test_alignment_radius_of_collinear_points_is_infinite():
    assert B._radius((0.0, 0.0), (1.0, 0.0), (2.0, 0.0)) == float("inf")


def test_alignment_radius_matches_a_known_circle():
    """Trzy punkty na okręgu o promieniu 91,5 m — najciaśniejszy łuk sieci STIB."""
    radius = 91.5
    pts = [(radius * math.cos(a), radius * math.sin(a)) for a in (0.0, 0.4, 0.8)]
    assert abs(B._radius(*pts) - radius) < 1e-6, B._radius(*pts)


def test_alignment_pick_line_requires_both_code_and_variante_to_match():
    lines = [_line_row("1", 1), _line_row("1", 2), _line_row("5", 1)]
    assert B.pick_line(lines, "1", 2)["attributes"]["Variante"] == 2
    for code, variante in (("1", 3), ("2", 1), ("5", 2)):
        try:
            B.pick_line(lines, code, variante)
        except SystemExit as err:
            assert "brak polilinii" in str(err), err
        else:
            raise AssertionError(f"{code}/{variante} przeszło, a nie ma go w danych")


def test_alignment_pick_line_refuses_two_candidates():
    """Dwie polilinie na tej samej parze to niejednoznaczność, nie wybór.

    Bez tego warunku brany byłby po prostu pierwszy — a kolejność w shapefile
    nie jest niczym gwarantowana.
    """
    lines = [_line_row("1", 1), _line_row("1", 1)]
    try:
        B.pick_line(lines, "1", 1)
    except SystemExit as err:
        assert "2 polilinii" in str(err), err
    else:
        raise AssertionError("dwie polilinie przeszły jako jedna")


def test_alignment_pick_line_refuses_multipart_geometry():
    row = _line_row("1", 1)
    row["geometry"]["parts"] = [0, 4]
    try:
        B.pick_line([row], "1", 1)
    except SystemExit as err:
        assert "2 części" in str(err), err
    else:
        raise AssertionError("polilinia dwuczęściowa przeszła")


def _line_row(code, variante):
    return {"attributes": {"LineCode": code, "Variante": variante},
            "geometry": {"parts": [0], "points": [(0.0, 0.0), (100.0, 0.0)]}}


def test_alignment_package_bounds_matches_the_identifier_exactly():
    import tempfile
    network = {"build_packages": [{"id": "A", "from": "Beekkant", "to": "Merode",
                                   "stations": 12},
                                  {"id": "B", "from": "Merode", "to": "Stockel",
                                   "stations": 9}]}
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                         encoding="utf-8")
    json.dump(network, handle)
    handle.close()
    try:
        assert B.package_bounds(handle.name, "B")["to"] == "Stockel"
        try:
            B.package_bounds(handle.name, "C")
        except SystemExit as err:
            assert "pakiet C nie istnieje" in str(err), err
        else:
            raise AssertionError("nieistniejący pakiet C przeszedł")
    finally:
        os.unlink(handle.name)


def test_alignment_slice_starting_on_a_duplicated_vertex_does_not_divide_by_zero():
    """Ostre `<` w `c0 < start <= c1` to nie jest tylko zakres — to zabezpieczenie.

    Gdy oś ma zdublowany wierzchołek (a oś STIB ma), segment między kopiami ma
    `c1 - c0 == 0`. Nieostry warunek wpuszcza ten segment do interpolacji i cięcie
    dzieli przez zero. Znalezione różnicowo: mutacja `<` → `<=` przeżyła cały
    zestaw testów, a wywraca się na TYM wejściu.
    """
    line = [(0.0, 0.0), (50.0, 0.0), (50.0, 0.0), (100.0, 0.0)]
    assert [p for p, _ in B.slice_polyline(line, 50.0, 75.0)] == \
        [(50.0, 0.0), (75.0, 0.0)]
    assert [p for p, _ in B.slice_polyline(line, 50.0, 50.0)] == [(50.0, 0.0)]


def test_alignment_slice_ending_on_a_duplicated_vertex_does_not_divide_by_zero():
    """To samo od drugiej strony: ostre `<` w `c0 <= end < c1`."""
    line = [(0.0, 0.0), (50.0, 0.0), (50.0, 0.0), (100.0, 0.0)]
    assert [p for p, _ in B.slice_polyline(line, 0.0, 50.0)] == \
        [(0.0, 0.0), (50.0, 0.0)]
    assert [p for p, _ in B.slice_polyline(line, 25.0, 50.0)] == \
        [(25.0, 0.0), (50.0, 0.0)]


def test_alignment_point_at_the_very_end_returns_the_last_vertex_itself():
    """Na końcu osi ma wrócić TEN wierzchołek, nie jego przeliczenie.

    Bez skrótu `chainage >= chain[-1]` punkt idzie przez interpolację i wychodzi
    z błędem zaokrąglenia rzędu 3e-14 m. Fizycznie nieistotne — ale kotwice stacji
    porównuje się z końcem osi na równość, a nie z tolerancją, więc wynik ma być
    identyczny co do bitu.
    """
    line = [(0.0, 0.0), (30.0, 40.0), (60.0, 80.0)]
    assert B.point_at(line, B.polyline_length(line)) == line[-1]
    # Łamana, na której `cumulative` NARASTAJĄCO się myli: bez skrótu interpolacja
    # wraca (359.2019492051856, 450.22394968265843) zamiast wierzchołka.
    skew = [(-218.06927767326232, -354.32360754201943),
            (34.59096230010357, 109.81243525699688),
            (-181.38831888811347, -374.508487504023),
            (359.20194920518566, 450.2239496826585)]
    assert B.point_at(skew, B.polyline_length(skew)) == skew[-1]


def test_alignment_the_nanometre_guard_is_dominated_by_the_micrometre_dedup():
    """Próg 1e-9 przy domknięciu prawego końca nie ma jak zadziałać — i to jest wynik.

    Warunek `math.dist(out[-1][0], last) > 1e-9` decyduje wyłącznie o punktach
    leżących o mniej niż 1e-9 od poprzednika. Każdy taki punkt jest potem usuwany
    przez dedupikację, która sklaja wszystko bliżej niż **1e-6**. Próg nanometrowy
    jest więc martwy wobec mikrometrowego, który po nim następuje.

    Sprawdzone wykonaniem na ośmiu wejściach trafiających DOKŁADNIE w granicę
    (`end == chain[-1] - 1e-9` oraz łamane, których ostatni segment ma 1e-9)
    dla trzech mutacji naraz — zero różnic. Bez policzenia trafień w granicę
    „zero różnic" nic by nie znaczyło: losowa bateria w punkt równości nie trafia.
    """
    line = [(0.0, 0.0), (1.005e-9, 0.0)]
    assert [p for p, _ in B.slice_polyline(line, 0.0, 1.005e-9)] == [(0.0, 0.0)]
    for length in (1.0, 100.0, 6700.0):
        straight = [(0.0, 0.0), (length, 0.0)]
        at_edge = [p for p, _ in B.slice_polyline(straight, 0.0, length - 1e-9)]
        to_end = [p for p, _ in B.slice_polyline(straight, 0.0, length)]
        assert at_edge[0] == (0.0, 0.0) and to_end[0] == (0.0, 0.0)
        assert to_end[-1] == (length, 0.0), (length, to_end)

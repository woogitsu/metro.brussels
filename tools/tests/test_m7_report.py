#!/usr/bin/env python3
"""Testy pomiaru i bramki akceptacji bryły M7 (`tools/blender/m7_report.py`).

Powód powstania jest ten sam co przy `test_tunnel_manifest.py`: przemiatanie
mutacyjne z 03.09.2026 dało dla `m7_shell.py` 35 mutacji i 35 ocalałych — 100 %,
bo moduł importuje `bpy` i `test_all.py` nie umie go zaimportować. Cała bramka
— długość, szerokość, wysokość dachu, liczba członów, liczba i położenie otworów
drzwiowych, symetria obrotowa składu dwukierunkowego — leżała poza zasięgiem
jakiegokolwiek testu.

Bryła w testach jest **syntetyczna**, składana z `Layout` tak, żeby bramka ją
przepuściła, a potem psuta w JEDNYM miejscu naraz. Nie jest to zrzut prawdziwej
geometrii: bramka nie ogląda siatki, tylko wierzchołki i wymiary, więc zrzut
niczego by nie dodał poza megabajtem w repozytorium. To, że prawdziwy generator
przez tę bramkę przechodzi, sprawdza job `godot-first-run` na CI.
"""
import copy
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import m7_report as RP  # noqa: E402
from m7_layout import Layout  # noqa: E402


def _layout():
    return Layout(spec=None)


def _symmetric(layout, points):
    """Domyka zbiór na obrót 180° — bryła składu dwukierunkowego musi być na niego
    niezmiennicza, a bramka tego pilnuje."""
    # Współrzędne trzymam na 4 miejscach — dokładnie tylu używa kontrola symetrii.
    # Przy 6 miejscach podwójne zaokrąglenie (najpierw 6, potem 4 w bramce) rozjeżdża
    # kilka wierzchołków o jednostkę na ostatnim miejscu i atrapa oblewa własny test.
    out = set()
    for x, y, z in points:
        x, y, z = round(x, 4), round(y, 4), round(z, 4)
        out.add((x, y, z))
        out.add((round(layout.length - x, 4), -y if y else 0.0, z))
    return sorted(out)


def _body_points(layout):
    """Wierzchołki, które bramka umie zobaczyć: naroża otworów i obrys."""
    hw = layout.half_width
    points = []
    for door in layout.all_doors():
        y = door["side"] * hw
        for x in (door["x0"], door["x1"]):
            for z in (door["z0"], door["z1"]):
                points.append((round(x, 4), y, z))
    for x in (0.0, layout.length):
        for y in (hw, -hw):
            for z in (layout.body_bottom_z, layout.roof_z):
                points.append((x, y, z))
    # wypełniacz w osi pojazdu: bramka wymaga ponad 1000 wierzchołków, a te przy
    # y = 0 nie wpadają do pomiaru otworów (filtr |y| == half_width)
    for i in range(700):
        points.append((round(layout.length * i / 699.0, 4), 0.0,
                       round(layout.body_bottom_z
                             + (layout.roof_z - layout.body_bottom_z) * (i % 7) / 6.0, 4)))
    return _symmetric(layout, points)


def _records(layout):
    """Sześć członów i pięć przegubów; wierzchołki rozdzielone po X między człony."""
    points = _body_points(layout)
    span = layout.length / 6.0
    cars, joints = [], []
    for index in range(6):
        lo, hi = index * span, (index + 1) * span
        mine = [p for p in points if (lo <= p[0] < hi or (index == 5 and p[0] == layout.length))]
        cars.append({"name": f"M7_car_{index + 1}", "vertices": mine,
                     "faces": max(1, len(mine) // 2), "dimensions": (span, layout.width, 2.65)})
    for index in range(5):
        joints.append({"name": f"M7_articulation_{index + 1}", "vertices": [],
                       "faces": 0, "dimensions": (0.4, layout.width, 2.65)})
    joints[0]["vertices"] = []
    return cars, joints


def _run(layout=None, cars=None, joints=None):
    layout = layout or _layout()
    if cars is None:
        cars, joints = _records(layout)
    report = {}
    return RP.verify(layout, cars, joints, report), report


def test_m7_synthetic_body_passes_the_gate():
    """Punkt wyjścia dla wszystkich kontroli negatywnych niżej.

    Gdyby ten test padł, każdy `len(problems) == 1` poniżej przechodziłby
    z zupełnie innego powodu niż zamierzony.
    """
    problems, report = _run()
    assert problems == [], problems
    assert report["body"]["cars"] == 6, report["body"]
    assert report["rotational_symmetry"]["ok"] is True, report["rotational_symmetry"]


def test_m7_gate_catches_a_shortened_body():
    layout = _layout()
    cars, joints = _records(layout)
    cars[5]["vertices"] = [p for p in cars[5]["vertices"] if p[0] < layout.length - 0.01]
    problems, _ = _run(layout, cars, joints)
    assert any("długość" in p for p in problems), problems


def test_m7_gate_catches_a_body_that_does_not_start_at_the_origin():
    layout = _layout()
    cars, joints = _records(layout)
    cars = [dict(c, vertices=[(round(p[0] + 0.5, 4), p[1], p[2]) for p in c["vertices"]])
            for c in cars]
    problems, _ = _run(layout, cars, joints)
    assert any("origin/zasięg X" in p for p in problems), problems


def test_m7_gate_catches_a_roof_at_the_wrong_height():
    layout = _layout()
    cars, joints = _records(layout)
    cars[0]["vertices"] = cars[0]["vertices"] + [(1.0, 0.0, layout.roof_z + 0.02)]
    problems, _ = _run(layout, cars, joints)
    assert any("wysokość dachu" in p for p in problems), problems


def test_m7_gate_catches_a_missing_car():
    layout = _layout()
    cars, joints = _records(layout)
    joints.append(cars.pop())
    problems, _ = _run(layout, cars, joints)
    assert any("członów 5" in p for p in problems), problems


def test_m7_gate_catches_nan_and_infinity():
    for bad in (float("nan"), float("inf")):
        layout = _layout()
        cars, joints = _records(layout)
        cars[0]["vertices"] = cars[0]["vertices"] + [(1.0, 0.0, bad)]
        problems, _ = _run(layout, cars, joints)
        assert any("NaN/Inf" in p for p in problems), (bad, problems)


def test_m7_gate_catches_a_suspiciously_small_mesh():
    """Poniżej 1000 wierzchołków to nie jest bryła sześcioczłonowego składu.

    Bramka na liczbę wierzchołków łapie generator, który wykonał się bez błędu
    i wyprodukował prawie nic — przypadek z CLAUDE.md §5.
    """
    layout = _layout()
    cars, joints = _records(layout)
    for car in cars:
        car["vertices"] = car["vertices"][:80]
    problems, _ = _run(layout, cars, joints)
    assert any("podejrzana liczba wierzchołków" in p for p in problems), problems


def test_m7_vertex_count_bounds_are_open_at_the_named_values():
    assert RP.MIN_PLAUSIBLE_VERTICES == 1000
    assert RP.MAX_PLAUSIBLE_VERTICES == 500000


def test_m7_gate_catches_an_absurdly_scaled_object():
    layout = _layout()
    cars, joints = _records(layout)
    cars[2]["dimensions"] = (layout.length + 1.5, layout.width, 2.65)
    problems, _ = _run(layout, cars, joints)
    assert any("absurdalna skala" in p for p in problems), problems


def test_m7_gate_catches_an_object_collapsed_to_nothing():
    layout = _layout()
    cars, joints = _records(layout)
    joints[1]["dimensions"] = (0.0, 0.0, 0.0)
    problems, _ = _run(layout, cars, joints)
    assert any("absurdalna skala" in p for p in problems), problems


def test_m7_gate_catches_a_door_without_edges_in_the_geometry():
    """Otwór zaplanowany, ale nie wycięty — modyfikator boolean bywa cichy."""
    layout = _layout()
    cars, joints = _records(layout)
    door = layout.all_doors()[0]
    x0 = round(door["x0"], 4)
    for car in cars:
        car["vertices"] = [p for p in car["vertices"] if round(p[0], 4) != x0]
    problems, _ = _run(layout, cars, joints)
    assert any("nie ma krawędzi w geometrii" in p for p in problems), problems


def test_m7_gate_catches_a_door_cut_only_halfway_up():
    """Krawędzie boczne są, ale brakuje naroża — otwór urwany w pionie."""
    layout = _layout()
    cars, joints = _records(layout)
    door = layout.all_doors()[0]
    for car in cars:
        car["vertices"] = [p for p in car["vertices"]
                           if not (abs(p[2] - door["z1"]) <= RP.VERTEX_EPS
                                   and abs(abs(p[1]) - layout.half_width) <= RP.VERTEX_EPS
                                   and round(p[0], 4) in (round(door["x0"], 4),
                                                          round(door["x1"], 4)))]
    problems, _ = _run(layout, cars, joints)
    assert any("nie ma krawędzi w geometrii" in p for p in problems), problems


def test_m7_gate_catches_a_body_that_is_not_symmetric_under_a_half_turn():
    """Skład jest dwukierunkowy — bryła musi wyglądać tak samo z obu stron.

    Ten błąd jest niewidoczny na renderze, bo cieniowanie i tak jest niesymetryczne.
    """
    layout = _layout()
    cars, joints = _records(layout)
    cars[0]["vertices"] = cars[0]["vertices"] + [(3.0, layout.half_width, 2.0)]
    problems, report = _run(layout, cars, joints)
    assert any("nie jest symetryczna obrotowo" in p for p in problems), problems
    assert report["rotational_symmetry"]["mismatched"] == 1, report["rotational_symmetry"]


def test_m7_openings_are_counted_per_side_and_per_kind():
    layout = _layout()
    cars, joints = _records(layout)
    _problems, report = _run(layout, cars, joints)
    summary = report["opening_summary"]
    assert summary["double_per_side"] == layout.doors_per_side, summary
    assert summary["cab_total"] == layout.cab_doors, summary
    assert summary["double_total"] == 2 * layout.doors_per_side, summary
    assert summary["double_edges_found"] == summary["double_total"], summary
    assert summary["double_corners_found"] == summary["double_total"], summary


def test_m7_openings_are_measured_only_on_the_side_they_belong_to():
    """Wierzchołek po prawej burcie nie może zaliczyć otworu po lewej.

    Klucz pomiaru to (x, znak y) — bez znaku otwór wycięty tylko z jednej strony
    przechodziłby jako wycięty z obu.
    """
    layout = _layout()
    cars, joints = _records(layout)
    for car in cars:
        car["vertices"] = [p for p in car["vertices"]
                           if not (abs(p[1] - layout.half_width) <= RP.VERTEX_EPS)]
    _problems, report = _run(layout, cars, joints)
    right = [o for o in report["openings"] if o["side"] == 1]
    left = [o for o in report["openings"] if o["side"] == -1]
    assert right and not any(o["edges_found"] for o in right), right[:2]
    assert left and all(o["edges_found"] for o in left), left[:2]


def test_m7_measure_openings_ignores_vertices_off_the_body_side():
    """Filtr `|y| == half_width` odsiewa wnętrze; bez niego dach zaliczałby otwory."""
    layout = _layout()
    cars, joints = _records(layout)
    door = layout.all_doors()[0]
    inner = [(round(door["x0"], 4), 0.0, door["z0"]), (round(door["x1"], 4), 0.0, door["z1"])]
    cars[0]["vertices"] = cars[0]["vertices"] + inner
    measured = RP.measure_openings(layout, [{"name": "x", "vertices": inner, "faces": 1,
                                             "dimensions": (1.0, 1.0, 1.0)}])
    assert not any(o["edges_found"] for o in measured), measured[:2]


# --- x_stations -------------------------------------------------------------

def test_m7_x_stations_always_contain_both_ends():
    layout = _layout()
    stations = RP.x_stations(layout, 10.0, 20.0, taper_aware=False)
    assert stations[0] == 10.0 and stations[-1] == 20.0, stations


def test_m7_x_stations_are_sorted_and_unique():
    layout = _layout()
    stations = RP.x_stations(layout, 0.0, layout.length)
    assert stations == sorted(set(stations)), "podziały mają się nie powtarzać"


def test_m7_x_stations_respect_the_body_step():
    layout = _layout()
    stations = RP.x_stations(layout, 20.0, 40.0, taper_aware=False)
    gaps = [b - a for a, b in zip(stations, stations[1:])]
    assert max(gaps) <= RP.BODY_STEP_M + 1e-9, max(gaps)


def test_m7_x_stations_are_denser_inside_the_nose():
    """Przekrój zmienia się w dziobie, więc podział ma tam być gęstszy niż w pudle."""
    layout = _layout()
    from m7_layout import DESIGN_NOSE_LENGTH_M
    nose = RP.x_stations(layout, 0.0, DESIGN_NOSE_LENGTH_M)
    body = RP.x_stations(layout, 20.0, 20.0 + DESIGN_NOSE_LENGTH_M, taper_aware=False)
    assert len(nose) > len(body), (len(nose), len(body))
    gaps = [b - a for a, b in zip(nose, nose[1:])]
    assert max(gaps) <= RP.NOSE_STEP_M + 1e-9, max(gaps)


def test_m7_x_stations_include_a_nose_end_that_falls_exactly_on_the_boundary():
    """Koniec dziobu leżący DOKŁADNIE na granicy zakresu ma się w nim znaleźć.

    Warunek ma zapas 1e-9 właśnie po to; bez zapasu granica wypadałaby losowo,
    zależnie od tego, jak `layout.length - DESIGN_NOSE_LENGTH_M` się zaokrągli.
    """
    layout = _layout()
    from m7_layout import DESIGN_NOSE_LENGTH_M
    stations = RP.x_stations(layout, DESIGN_NOSE_LENGTH_M, 30.0)
    assert round(DESIGN_NOSE_LENGTH_M, 6) in stations, stations[:4]
    far = layout.length - DESIGN_NOSE_LENGTH_M
    stations = RP.x_stations(layout, 60.0, far)
    assert round(far, 6) in stations, stations[-4:]


# --- pudełko, NaN, punkty ---------------------------------------------------

def test_m7_bounds_are_the_extremes_of_every_axis():
    points = [(1.0, -2.0, 3.0), (-4.0, 5.0, -6.0), (0.0, 0.0, 0.0)]
    assert RP.bounds(points) == ((-4.0, -2.0, -6.0), (1.0, 5.0, 3.0))


def test_m7_all_points_keeps_input_order():
    records = [{"vertices": [(1.0, 0.0, 0.0)]}, {"vertices": [(2.0, 0.0, 0.0)]}]
    assert RP.all_points(records) == [(1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]


def test_m7_check_no_nan_looks_at_every_component():
    assert RP.check_no_nan([(0.0, 1.0, 2.0)])
    for index in range(3):
        bad = [0.0, 1.0, 2.0]
        bad[index] = float("nan")
        assert not RP.check_no_nan([tuple(bad)]), index
        bad[index] = float("-inf")
        assert not RP.check_no_nan([tuple(bad)]), index


# --- re-import GLB ----------------------------------------------------------

def _mesh(name, points):
    return {"name": name, "vertices": points, "faces": 1, "dimensions": (1.0, 1.0, 1.0)}


def test_m7_roundtrip_accepts_the_same_geometry_back():
    bbox = ((0.0, -1.35, 0.95), (94.0, 1.35, 3.6))
    records = [_mesh("a", [bbox[0], bbox[1]])]
    result = RP.roundtrip_result(records, 1, bbox)
    assert result["ok"] is True and result["max_delta_m"] == 0.0, result


def test_m7_roundtrip_rejects_a_missing_object():
    bbox = ((0.0, -1.35, 0.95), (94.0, 1.35, 3.6))
    records = [_mesh("a", [bbox[0], bbox[1]])]
    assert RP.roundtrip_result(records, 2, bbox)["ok"] is False


def test_m7_roundtrip_rejects_a_shifted_bounding_box_above_the_tolerance():
    bbox = ((0.0, -1.35, 0.95), (94.0, 1.35, 3.6))
    shifted = ((0.0, -1.35, 0.95), (94.0 + RP.TOLERANCE_M * 1.5, 1.35, 3.6))
    assert RP.roundtrip_result([_mesh("a", list(shifted))], 1, bbox)["ok"] is False


def test_m7_roundtrip_tolerance_is_closed_at_one_millimetre():
    bbox = ((0.0, -1.35, 0.95), (94.0, 1.35, 3.6))
    edge = ((0.0, -1.35, 0.95), (94.0 + RP.TOLERANCE_M, 1.35, 3.6))
    result = RP.roundtrip_result([_mesh("a", list(edge))], 1, bbox)
    assert result["max_delta_m"] == RP.TOLERANCE_M, result
    assert result["ok"] is True, result


# --- skrajnia ---------------------------------------------------------------

def test_m7_envelope_must_contain_the_body_in_width_and_height():
    body = ((0.0, -1.35, 0.95), (94.0, 1.35, 3.6))
    wide = ((0.0, -1.5, 0.8), (94.0, 1.5, 3.8))
    assert RP.envelope_problems(wide, body) == []


def test_m7_envelope_narrower_than_the_body_is_a_problem():
    body = ((0.0, -1.35, 0.95), (94.0, 1.35, 3.6))
    narrow = ((0.0, -1.2, 0.8), (94.0, 1.2, 3.8))
    assert RP.envelope_problems(narrow, body) == ["skrajnia nie obejmuje bryły w osi szerokość"]


def test_m7_envelope_lower_than_the_body_is_a_problem():
    body = ((0.0, -1.35, 0.95), (94.0, 1.35, 3.6))
    low = ((0.0, -1.5, 0.8), (94.0, 1.5, 3.5))
    assert RP.envelope_problems(low, body) == ["skrajnia nie obejmuje bryły w osi wysokość"]


def test_m7_envelope_flush_with_the_body_still_passes():
    """Skrajnia równa bryle co do mikrometra to styk, a nie przekroczenie."""
    body = ((0.0, -1.35, 0.95), (94.0, 1.35, 3.6))
    assert RP.envelope_problems(body, body) == []


def test_m7_envelope_is_not_checked_along_the_length():
    """Oś X celowo poza kontrolą: skrajnia jest przekrojem, nie kopertą składu."""
    body = ((0.0, -1.35, 0.95), (94.0, 1.35, 3.6))
    short = ((10.0, -1.5, 0.8), (20.0, 1.5, 3.8))
    assert RP.envelope_problems(short, body) == []


# --- progi: wartość RÓWNA progowi ------------------------------------------
#
# Wszystkie kontrole wymiarowe bramki stoją na `> TOLERANCE_M`, czyli odchyłka
# równa milimetrowi ma PRZEJŚĆ. Testu na granicy nie da się napisać naiwnie:
# `abs(94.001 - 94.0)` to 0.0009999999999976694, a nie 0.001 — czyli PONIŻEJ progu,
# więc taki test nigdy granicy nie dotyka. Różnica jest dokładna tylko wtedy, gdy
# jedna ze stron jest zerem. Dlatego atrapa niżej ma layout o wymiarach rzędu
# milimetra i bryłę zerowej wielkości: bramka ogląda RÓŻNICĘ, więc skala jest
# obojętna, a przy zerze granica jest reprezentowalna.


def _degenerate(**overrides):
    """Layout, w którym każda kontrola wymiarowa mierzy dokładnie `TOLERANCE_M`."""
    layout = _layout()
    layout.length = RP.TOLERANCE_M
    layout.width = RP.TOLERANCE_M
    layout.half_width = RP.TOLERANCE_M / 2.0
    layout.roof_z = RP.TOLERANCE_M
    layout.body_bottom_z = -RP.TOLERANCE_M
    # Drzwi wypadają z atrapy: ich położenia liczą się z długości pojazdu, a ta jest
    # tu milimetrowa. Bramka wymiarowa i tak ich nie ogląda — mierzy pudełko.
    layout.doors_per_side = 0
    layout.cab_doors = 0
    layout.all_doors = lambda: []
    for key, value in overrides.items():
        setattr(layout, key, value)
    point = (0.0, 0.0, 0.0)
    cars = [{"name": f"c{i}", "vertices": [point], "faces": 1,
             "dimensions": (0.5, 0.5, 0.5)} for i in range(layout.cars)]
    return layout, cars, []


def _messages(layout, cars, joints):
    return RP.verify(layout, cars, joints, {})


def test_m7_dimension_deviation_of_exactly_one_millimetre_passes():
    layout, cars, joints = _degenerate()
    problems = _messages(layout, cars, joints)
    for phrase in ("długość", "szerokość", "origin/zasięg X", "wysokość dachu",
                   "spód pudła"):
        assert not any(phrase in p for p in problems), (phrase, problems)


def test_m7_dimension_deviation_just_over_the_tolerance_is_reported():
    over = RP.TOLERANCE_M * 1.01
    for key, phrase in (("length", "długość"), ("width", "szerokość"),
                        ("roof_z", "wysokość dachu"), ("body_bottom_z", "spód pudła")):
        value = -over if key == "body_bottom_z" else over
        layout, cars, joints = _degenerate(**{key: value})
        problems = _messages(layout, cars, joints)
        assert any(phrase in p for p in problems), (key, problems)


def test_m7_vertex_count_exactly_at_the_bounds_is_rejected():
    """`1000 < n < 500000` jest OSTRE z obu stron: 1000 to nadal za mało."""
    for count in (RP.MIN_PLAUSIBLE_VERTICES, RP.MAX_PLAUSIBLE_VERTICES):
        layout, cars, joints = _degenerate()
        for car in cars[1:]:
            car["vertices"] = []
        cars[0]["vertices"] = [(0.0, 0.0, 0.0)] * count
        problems = _messages(layout, cars, joints)
        assert any("podejrzana liczba" in p for p in problems), (count, problems)


def test_m7_object_exactly_one_metre_longer_than_the_body_still_passes():
    """Zapas na obiekt jest `> length + 1 m` — równo metr ponad długość przechodzi."""
    layout, cars, joints = _degenerate()
    cars[0]["dimensions"] = (layout.length + RP.OVERSIZE_MARGIN_M, 0.5, 0.5)
    assert not any("absurdalna skala" in p for p in _messages(layout, cars, joints))
    cars[0]["dimensions"] = (layout.length + RP.OVERSIZE_MARGIN_M * 1.01, 0.5, 0.5)
    assert any("absurdalna skala" in p for p in _messages(layout, cars, joints))


def test_m7_object_thinner_than_a_millimetre_is_not_yet_absurd():
    """Kontrola łapie obiekt ZEROWY, nie po prostu cienki.

    Podniesienie progu do milimetra wyrzucałoby poszycie, które ma 3 mm.
    """
    layout, cars, joints = _degenerate()
    cars[0]["dimensions"] = (0.0005, 0.0005, 0.0005)
    assert not any("absurdalna skala" in p for p in _messages(layout, cars, joints))
    cars[0]["dimensions"] = (0.0, 0.0, 0.0)
    assert any("absurdalna skala" in p for p in _messages(layout, cars, joints))


def test_m7_a_vertex_exactly_one_epsilon_off_the_side_still_counts():
    """Filtr burty jest `> VERTEX_EPS` — wierzchołek dokładnie na epsilonie należy do burty."""
    layout = _layout()
    door = layout.all_doors()[0]
    y = layout.half_width + RP.VERTEX_EPS
    points = [(round(door["x0"], 4), y, door["z0"]), (round(door["x0"], 4), y, door["z1"]),
              (round(door["x1"], 4), y, door["z0"]), (round(door["x1"], 4), y, door["z1"])]
    measured = RP.measure_openings(layout, [{"name": "b", "vertices": points, "faces": 1,
                                             "dimensions": (1.0, 1.0, 1.0)}])
    first = [o for o in measured if o["center_x"] == door["center_x"] and o["side"] == 1][0]
    assert first["edges_found"] and first["corners_found"], first


def test_m7_corner_height_is_quantised_to_a_tenth_of_a_millimetre_first():
    """Pomiar zaokrągla `z` do 4 miejsc, czyli do 0,1 mm — DOKŁADNIE do progu VERTEX_EPS.

    To znaczy, że progu `abs(z - z0) <= VERTEX_EPS` nie da się dotknąć od dołu:
    najmniejsza niezerowa odchyłka, jaka przeżyje zaokrąglenie, jest już równa
    kwantowi i po zaokrągleniu wychodzi minimalnie NAD próg. Naroże odchylone
    o 0,1 mm nie zalicza się do otworu. Zapisuję to, bo wygląda jak tolerancja,
    a działa jak równość.
    """
    layout = _layout()
    door = layout.all_doors()[0]
    y = door["side"] * layout.half_width
    exact = [(round(door["x0"], 4), y, door["z0"]), (round(door["x1"], 4), y, door["z1"])]
    off = [(round(door["x0"], 4), y, door["z0"] - RP.VERTEX_EPS),
           (round(door["x1"], 4), y, door["z1"] + RP.VERTEX_EPS)]

    def corners(points):
        measured = RP.measure_openings(layout, [{"name": "b", "vertices": points, "faces": 1,
                                                 "dimensions": (1.0, 1.0, 1.0)}])
        return [o for o in measured if o["center_x"] == door["center_x"]
                and o["side"] == door["side"]][0]["corners_found"]

    assert corners(exact) is True
    assert corners(off) is False


def test_m7_side_of_a_vertex_is_decided_by_the_sign_of_y_not_by_a_metre():
    """Znak `y` rozstrzyga burtę — także dla pojazdu węższego niż dwa metry.

    Przy prawdziwym M7 (półszerokość 1,35 m) podniesienie progu z 0 na 1 nic nie
    zmienia, bo 1,35 > 1. Atrapa o półszerokości 0,5 m pokazuje, że to jest
    porównanie ZE ZNAKIEM, a nie z jakąkolwiek wartością.
    """
    layout = _layout()
    layout.half_width = 0.5
    door = layout.all_doors()[0]
    assert door["side"] == 1, door
    points = [(round(door["x0"], 4), 0.5, door["z0"]), (round(door["x0"], 4), 0.5, door["z1"]),
              (round(door["x1"], 4), 0.5, door["z0"]), (round(door["x1"], 4), 0.5, door["z1"])]
    measured = RP.measure_openings(layout, [{"name": "b", "vertices": points, "faces": 1,
                                             "dimensions": (1.0, 1.0, 1.0)}])
    right = [o for o in measured if o["center_x"] == door["center_x"] and o["side"] == 1][0]
    assert right["edges_found"], right


def test_m7_envelope_flush_to_the_micrometre_still_contains_the_body():
    """Zapas skrajni jest `+ 1e-6 <`, czyli styk co do mikrometra jeszcze przechodzi."""
    body = ((0.0, -1e-6, -1e-6), (1.0, 1e-6, 1e-6))
    flush = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
    assert RP.envelope_problems(flush, body) == []
    tighter = ((0.0, 0.0, 0.0), (1.0, -1e-9, 0.0))
    assert RP.envelope_problems(tighter, body) != []


def test_m7_body_offset_by_exactly_one_millimetre_from_the_origin_passes():
    """Kontrola początku układu ma dwie strony i obie stoją na tym samym progu.

    Bryła przesunięta o równo milimetr przechodzi; o milimetr z okładem — nie.
    """
    layout, cars, joints = _degenerate()
    layout.length = 0.0
    cars[0]["vertices"] = [(RP.TOLERANCE_M, 0.0, 0.0)]
    for car in cars[1:]:
        car["vertices"] = []
    assert not any("origin/zasięg X" in p for p in _messages(layout, cars, joints))
    cars[0]["vertices"] = [(RP.TOLERANCE_M * 1.01, 0.0, 0.0)]
    assert any("origin/zasięg X" in p for p in _messages(layout, cars, joints))

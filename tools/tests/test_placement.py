#!/usr/bin/env python3
"""Testy osadzenia pojazdu na osi trasy (T-220 x T-210). Bez Blendera i bez pytest."""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import clearance as CL  # noqa: E402
import placement as PL  # noqa: E402
import profiles as PR  # noqa: E402
import sweep as SW  # noqa: E402

BOX = PR.profile_points("box_double")


def _straight(length=600.0, step=10.0):
    return [(i * step, 0.0, 0.0) for i in range(int(length / step) + 1)]


def _arc(radius, span_deg=120.0, count=300):
    return [(radius * math.cos(math.radians(a)), radius * math.sin(math.radians(a)), 0.0)
            for a in (span_deg * i / count for i in range(count + 1))]


def test_placement_car_spans_cover_the_train_without_gaps():
    spans = PL.car_spans(94.0, 6)
    assert len(spans) == 6
    assert spans[0][0] == 0.0 and abs(spans[-1][1] - 94.0) < 1e-9
    for (_a, b), (c, _d) in zip(spans, spans[1:]):
        assert b == c


def test_placement_on_a_straight_track_keeps_every_body_collinear():
    points = _straight()
    stations = SW.chainages(points)
    places = PL.place_cars(points, None, stations, 100.0, 94.0, 6, 2.10)
    assert len(places) == 6
    for place in places:
        assert abs(place["forward"][0] - 1.0) < 1e-9
        assert abs(place["yaw_rad"]) < 1e-9
        assert abs(place["location"][1] + 2.10) < 1e-9, place["location"]


def test_placement_each_body_gets_its_own_chord_on_a_curve():
    """Sedno modelu przegubowego: sześć pudeł, sześć różnych cięciw, nie jedna bryła."""
    points = _arc(90.0)
    stations = SW.chainages(points)
    places = PL.place_cars(points, None, stations, 20.0, 94.0, 6, 0.0)
    yaws = [p["yaw_rad"] for p in places]
    assert len(set(round(y, 6) for y in yaws)) == 6, "wszystkie człony mają ten sam kąt"
    for a, b in zip(yaws, yaws[1:]):
        assert abs(b - a) > 1e-3, "kąt między sąsiednimi członami nie rośnie"


def test_placement_spans_handle_bodies_of_different_length():
    points = _straight()
    stations = SW.chainages(points)
    places = PL.place_spans(points, stations, 50.0, [(0.0, 15.117), (15.117, 16.217)], 0.0)
    assert abs(places[0]["chord_m"] - 15.117) < 1e-6
    assert abs(places[1]["chord_m"] - 1.100) < 1e-6


def test_placement_transform_puts_the_nose_at_the_start_chainage():
    points = _straight()
    stations = SW.chainages(points)
    place = PL.place_spans(points, stations, 100.0, [(0.0, 15.117)], 0.0)[0]
    nose = PL.transform_point(place, (0.0, 0.0, 0.0))
    assert abs(nose[0] - 100.0) < 1e-6, nose


def test_placement_distance_to_boundary_is_signed():
    assert abs(PL.distance_to_boundary(BOX, 2.10, 1.8) - 2.60) < 1e-9
    assert PL.distance_to_boundary(BOX, 5.0, 1.0) < 0.0
    assert abs(PL.distance_to_boundary(BOX, 5.0, 1.0) + 0.30) < 1e-9


def test_placement_worst_chainage_finds_the_tightest_curve():
    points = _straight(300.0) + [(300.0 + 90.0 * math.sin(math.radians(a)),
                                  90.0 - 90.0 * math.cos(math.radians(a)), 0.0)
                                 for a in range(1, 91)]
    station, radius = PL.worst_chainage(points, 15.0, 50.0)
    assert station is not None
    assert 80.0 < radius < 100.0, radius
    assert station > 250.0, station


def test_placement_mesh_measurement_agrees_with_the_chord_formula():
    """Ta sama liczba dwiema drogami: strzałka cięciwy i odległość punktu od obrysu.

    Rozjazd większy niż kilka milimetrów oznacza, że jedna z metod jest błędna —
    i właśnie po to obie istnieją.
    """
    radius = 90.0
    points = _arc(radius)
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    chord = 14.567
    offset = 2.10
    half_width = 1.35
    # Oba tory: na danym łuku pudło przesuwa się ku ścianie tylko na jednym z nich,
    # na drugim ucieka do środka otworu. Wiążący jest ten pierwszy.
    worst = min(
        PL.distance_to_boundary(BOX, *PL.local_offsets(
            PL.transform_point(place, (x, y, 1.03)), frames, stations)[1:])
        for sign in (-1.0, 1.0)
        for place in [PL.place_spans(points, stations, 40.0, [(0.0, chord)], sign * offset)[0]]
        for x in (chord * i / 20.0 for i in range(21))
        for y in (-half_width, half_width))
    static_wall = min(PL.distance_to_boundary(BOX, offset + dx, 1.03)
                      for dx in (-half_width, half_width))
    predicted = static_wall - CL.versine(chord, radius)
    assert abs(worst - predicted) < 0.02, (worst, predicted)


def test_placement_rejects_a_zero_length_body():
    points = _straight()
    stations = SW.chainages(points)
    try:
        PL.place_spans(points, stations, 10.0, [(5.0, 5.0)], 0.0)
    except ValueError as exc:
        assert "cięciwa" in str(exc)
    else:
        raise AssertionError("zerowa cięciwa powinna zostać odrzucona")


def _tube_along(direction, length=500.0, step=5.0, half_width=4.70, floor=-1.20, roof=4.70):
    """Rura o prostokątnym przekroju biegnąca w zadanym kierunku w płaszczyźnie XY."""
    dx, dy = direction
    nx, ny = -dy, dx
    points = []
    for i in range(int(length / step) + 1):
        cx, cy = dx * i * step, dy * i * step
        for side in (-half_width, half_width):
            for z in (floor, roof):
                points.append((cx + nx * side, cy + ny * side, z))
    return points


def test_placement_section_perpendicular_finds_the_full_height():
    for direction in ((1.0, 0.0), (0.0, 1.0), (0.6, 0.8), (-0.7071, 0.7071)):
        points = _tube_along(direction)
        origin = (direction[0] * 250.0, direction[1] * 250.0, 0.0)
        zmin, zmax, count = PL.section_vertical(points, origin, (direction[0], direction[1], 0.0), 1.0)
        assert abs(zmin + 1.20) < 1e-9 and abs(zmax - 4.70) < 1e-9, (direction, zmin, zmax)
        assert not PL.is_degenerate_section(zmin, zmax)
        assert count == 4, (direction, count)


def test_placement_constant_x_slab_degenerates_on_a_tube_across_x():
    """Defekt, który to naprawia: płat o stałym X na rurze biegnącej wzdłuż Y.

    Bierze WSZYSTKIE wierzchołki rury zamiast jednego przekroju, więc na zakrzywionym
    odcinku potrafi złapać sam strop. Płaszczyzna prostopadła do stycznej — nie.
    """
    points = _tube_along((0.0, 1.0))
    origin = (0.0, 250.0, 0.0)
    _zmin, _zmax, across = PL.section_vertical(points, origin, (1.0, 0.0, 0.0), 1.0)
    _zmin2, _zmax2, along = PL.section_vertical(points, origin, (0.0, 1.0, 0.0), 1.0)
    assert across > 10 * along, (across, along)
    assert along == 4


def test_placement_degenerate_section_is_recognised():
    roof_only = [(x, 0.0, 4.70) for x in range(0, 50)]
    zmin, zmax, count = PL.section_vertical(roof_only, (25.0, 0.0, 0.0), (0.0, 1.0, 0.0), 1.0)
    assert count == len(roof_only)
    assert PL.is_degenerate_section(zmin, zmax), (zmin, zmax)


def test_placement_section_rejects_a_zero_normal():
    try:
        PL.section_vertical([(0.0, 0.0, 0.0)], (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1.0)
    except ValueError as exc:
        assert "zerowym" in str(exc)
    else:
        raise AssertionError("zerowa normalna powinna zostać odrzucona")


def test_placement_section_falls_back_to_the_nearest_ring_when_nothing_is_in_range():
    points = _tube_along((1.0, 0.0), length=100.0, step=50.0)
    zmin, zmax, count = PL.section_vertical(points, (500.0, 0.0, 0.0), (1.0, 0.0, 0.0), 0.1)
    assert count == 4 and not PL.is_degenerate_section(zmin, zmax)


def test_placement_coverage_range_of_a_full_axis_is_the_whole_axis():
    axis = _straight(600.0, 10.0)
    frames = SW.rmf_frames(axis)
    stations = SW.chainages(axis)
    tube = [(x, y, z) for x in range(0, 601, 10) for y in (-4.7, 4.7) for z in (-1.2, 4.7)]
    low, high = PL.covered_chainage_range(tube, frames, stations)
    assert abs(low - 0.0) < 1e-6 and abs(high - 600.0) < 1e-6


def test_placement_coverage_range_of_a_chunk_is_only_that_chunk():
    """Sedno poprawki: ułamek 0,25 na chunku ma trafić w chunk, nie w początek osi."""
    axis = _straight(600.0, 10.0)
    frames = SW.rmf_frames(axis)
    stations = SW.chainages(axis)
    chunk = [(x, y, z) for x in range(300, 401, 10) for y in (-4.7, 4.7) for z in (-1.2, 4.7)]
    low, high = PL.covered_chainage_range(chunk, frames, stations)
    assert abs(low - 300.0) < 1e-6 and abs(high - 400.0) < 1e-6
    assert abs(PL.fraction_to_chainage(0.25, low, high) - 325.0) < 1e-6
    assert abs(PL.fraction_to_chainage(0.05, low, high) - 305.0) < 1e-6


def test_placement_fraction_is_clamped_to_the_covered_range():
    assert PL.fraction_to_chainage(-1.0, 100.0, 200.0) == 100.0
    assert PL.fraction_to_chainage(2.0, 100.0, 200.0) == 200.0


def test_placement_stable_section_widens_past_a_plateau():
    """Zmierzone na chunku pakietu A: tolerancje 1 m i 2 m dają tyle samo, 4 m więcej.

    Przerwanie na pierwszym braku przyrostu zatrzymywało się na zaniżonym stropie.
    """
    ring_near = [(0.0, y, z) for y in (-4.7, 4.7) for z in (-1.2, 4.3)]
    ring_far = [(3.0, y, z) for y in (-4.15, 4.15) for z in (4.7,)]
    points = ring_near + ring_far
    naive = PL.section_vertical(points, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 1.0)
    stable = PL.section_vertical_stable(points, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 1.0)
    assert abs(naive[1] - 4.30) < 1e-9, naive
    assert abs(stable[1] - 4.70) < 1e-9, stable


def test_placement_axis_window_frames_the_window_not_the_axis():
    points = _straight(6000.0, 10.0)
    window = PL.axis_window(points, 3695.0, 3740.0)
    assert math.isclose(window["length_m"], 45.0, abs_tol=1e-9)
    assert math.isclose(window["center"][0], 3717.5, abs_tol=1e-6)
    assert math.isclose(window["size"], 45.0, abs_tol=1e-6)


def test_placement_axis_window_keeps_the_points_inside_it():
    points = _straight(600.0, 10.0)
    window = PL.axis_window(points, 105.0, 145.0)
    xs = [p[0] for p in window["points"]]
    assert xs == sorted(xs)
    assert math.isclose(xs[0], 105.0, abs_tol=1e-6) and math.isclose(xs[-1], 145.0, abs_tol=1e-6)
    assert [round(x, 6) for x in xs[1:-1]] == [110.0, 120.0, 130.0, 140.0]


def test_placement_axis_window_on_a_curve_is_wider_than_it_is_long():
    points = _arc(300.0)
    stations = SW.chainages(points)
    window = PL.axis_window(points, 0.0, stations[-1])
    # Łuk 120 stopni zawraca, więc bbox okna jest szerszy niż jakikolwiek jego bok
    # liczony po cięciwie — kadr musi wynikać z bboxa, nie z długości łuku.
    assert window["size"] > 300.0
    assert math.isclose(window["length_m"], stations[-1], abs_tol=1e-9)


def test_placement_axis_window_rejects_a_window_outside_the_axis():
    points = _straight(600.0, 10.0)
    for bad in [(0.0, 0.0), (200.0, 100.0), (-1.0, 100.0), (100.0, 900.0)]:
        try:
            PL.axis_window(points, bad[0], bad[1])
        except ValueError:
            continue
        raise AssertionError(f"okno {bad} powinno zostać odrzucone")


def test_placement_axis_window_floors_the_size_at_one_metre():
    points = _straight(600.0, 10.0)
    assert PL.axis_window(points, 100.0, 100.2)["size"] == 1.0


# --- triaż mutacyjny: granice, które wyglądały na pokryte -----------------------
#
# Z przeglądu `tools/tests/mutation_sweep.py` na `placement.py`. Każdy test zabija
# konkretną mutację, wypisaną w komentarzu — i ta mutacja jest jego kontrolą negatywną.
# Klasyfikacja całości: `reports/mutation-triage-placement.md`.


def _bent_axis():
    """Prosta, ostry łuk, prosta — najgorsza krzywizna w znanym miejscu."""
    points = [(i * 10.0, 0.0, 0.0) for i in range(11)]
    points += [(100.0 + 40.0 * math.sin(math.radians(a)),
                40.0 - 40.0 * math.cos(math.radians(a)), 0.0)
               for a in range(10, 91, 10)]
    points += [(140.0, 40.0 + i * 10.0, 0.0) for i in range(1, 26)]
    return points


def test_placement_a_node_belongs_to_the_segment_before_it():
    """Mutacja: 30, drugi `<=` -> `<` — węzeł osi wpadałby do odcinka NASTĘPNEGO.

    Pozycja wychodzi ta sama, więc żaden test pozycji tego nie widzi. Różni się
    INDEKS odcinka — a z niego wołający liczy styczną (`station_kit.sweep_section`,
    `tunnel_sweep`). W węźle między dwoma odcinkami o różnych kierunkach dwie różne
    styczne znaczą dwie różne ramki, czyli profil obrócony wokół osi.

    Zmierzone na prostej 0/10/20 m: oryginał daje `(index 0, t 1.0)`, mutant
    `(index 1, t 0.0)`.

    **Konwencja jest tu ODWROTNA niż w blokach sygnalizacji i w chunkach**, gdzie
    granica należy do następnego (`docs/15-classic-signalling.md`). Test przypina stan
    faktyczny, a rozbieżność jest zapisana w `docs/24-clearance-profile-decisions.md`.
    """
    points = [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (20.0, 0.0, 0.0)]
    stations = SW.chainages(points)
    position, index, t = PL.frame_at(points, stations, 10.0)
    assert position == (10.0, 0.0, 0.0)
    assert (index, t) == (0, 1.0), (index, t)

    assert PL.frame_at(points, stations, 0.0)[1:] == (0, 0.0)
    assert PL.frame_at(points, stations, 20.0)[1:] == (1, 1.0)


def test_placement_a_window_over_the_whole_axis_is_accepted():
    """Mutacja: 53 `from_m < 0.0` -> `<= 0.0` — kadr całej osi byłby ODRZUCONY.

    Kadrowanie od zera to nie jest przypadek brzegowy, tylko domyślne wywołanie
    renderu kontrolnego dla całego pakietu. Mutant kończy je wyjątkiem „okno wychodzi
    poza oś", co jest nieprawdą: 0 m to początek osi, a nie punkt przed nią.
    """
    points = _straight()
    total = SW.chainages(points)[-1]
    window = PL.axis_window(points, 0.0, total)
    assert abs(window["length_m"] - total) < 1e-9
    assert window["from_m"] == 0.0

    for bad in ((-0.001, total), (0.0, total + 1.0)):
        try:
            PL.axis_window(points, *bad)
        except ValueError:
            continue
        raise AssertionError(f"okno {bad} poza osią zostało przyjęte")


def test_placement_a_station_exactly_at_the_guard_still_counts():
    """Mutacja: 140 `station < guard_m` -> `<=` — pomijałaby stację DOKŁADNIE na granicy.

    Strefa ochronna odsuwa wynik od końców osi, żeby cały skład się mieścił; odległość
    RÓWNA strefie już się mieści. Mutant przesuwa odpowiedź na następną stację i podaje
    inne miejsce jako najgorsze.

    Zmierzone na osi z łukiem: przy strefie ustawionej dokładnie na najgorszym
    kilometrażu oryginał zwraca 134,862 m, mutant 148,807 m — ten sam promień, inne
    miejsce w tunelu.
    """
    points = _bent_axis()
    worst_m, radius = PL.worst_chainage(points, 15.12, 1.0)
    assert worst_m is not None and radius < 50.0, (worst_m, radius)

    same_m, same_r = PL.worst_chainage(points, 15.12, worst_m)
    assert abs(same_m - worst_m) < 1e-9, (same_m, worst_m)
    assert abs(same_r - radius) < 1e-9


def test_placement_a_frame_exactly_at_the_window_edge_is_searched():
    """Mutacje: 169, oba `<=` -> `<` — ramka na krańcu okna wypadałaby z przeszukania.

    Awaria jest cicha i przez to najgorsza z całego tego zestawu: `local_offsets`
    startuje z `best = (0, 0, 0, inf)` i gdy żadna ramka nie przejdzie filtra, zwraca
    te ZERA jako offsety. Punkt oddalony o 2 m nad osią dostaje wtedy odpowiedź
    „leżysz dokładnie na osi w kilometrażu zero".

    Zmierzone przy oknie zawężonym do jednej ramki: oryginał `(50.0, 0.0, 2.0)`,
    mutant `(0.0, 0.0, 0.0)`.
    """
    points = _bent_axis()
    frames = SW.rmf_frames(SW.dedupe(points))
    stations = SW.chainages([f[0] for f in frames])
    origin = frames[5][0]
    probe = (origin[0], origin[1], origin[2] + 2.0)

    single = (stations[5], stations[5])
    chainage, right, up = PL.local_offsets(probe, frames, stations, single)
    assert abs(chainage - stations[5]) < 1e-6, (chainage, stations[5])
    assert abs(up - 2.0) < 1e-6, up
    assert abs(right) < 1e-6, right


def test_placement_a_section_exactly_at_the_minimum_is_not_degenerate():
    """Mutacja: 263 `<` -> `<=` — przekrój o wysokości RÓWNEJ minimum byłby odrzucony.

    Minimum znaczy „nie niższy niż", więc równość jeszcze się mieści. Kierunek błędu
    jest tu istotny: uznanie dobrego przekroju za zdegenerowany przerywa render, który
    powinien się udać, i wygląda jak usterka geometrii, a nie progu.
    """
    minimum = PL.MIN_SECTION_HEIGHT_M
    assert PL.is_degenerate_section(0.0, minimum) is False
    assert PL.is_degenerate_section(0.0, minimum * 0.999) is True
    assert PL.is_degenerate_section(0.0, minimum * 1.001) is False


def test_placement_circumradius_rejects_a_repeated_point_by_area_alone():
    """Kontrola po usunięciu MARTWEGO warunku `ab * bc * ca == 0.0` z `_circumradius`.

    Iloczyn boków zeruje się tylko wtedy, gdy dwa z trzech punktów się pokrywają —
    a wtedy trójkąt ma zerowe pole i łapie go już `area2 < 1e-12`. Ta sama martwa
    połowa stała w `clearance.circumradius` i została usunięta w #127; tutaj przetrwała,
    bo nikt nie sprawdził drugiego wystąpienia.

    Test pilnuje, że po usunięciu nadal odrzucane są WSZYSTKIE trzy przypadki, które
    tamten warunek miał rzekomo łapać.
    """
    assert PL._circumradius((0.0, 0.0), (0.0, 0.0), (2.0, 0.0)) is None
    assert PL._circumradius((0.0, 0.0), (1.0, 1.0), (0.0, 0.0)) is None
    assert PL._circumradius((0.0, 0.0), (1.0, 0.0), (2.0, 0.0)) is None

    radius = PL._circumradius((0.0, 0.0), (1.0, 1.0), (2.0, 0.0))
    assert radius is not None and abs(radius - 1.0) < 1e-9, radius

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

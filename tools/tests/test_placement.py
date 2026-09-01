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

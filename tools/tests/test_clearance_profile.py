#!/usr/bin/env python3
"""Testy profilu luzu wzdłuż osi i zamiatanej obwiedni. Bez Blendera i bez pytest."""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import clearance as CL  # noqa: E402
import clearance_profile as CP  # noqa: E402
import placement as PL  # noqa: E402
import profiles as PR  # noqa: E402
import sweep as SW  # noqa: E402

BOX = PR.profile_points("box_double")
PLANES = CP.halfplanes(BOX)


def _straight(length=400.0, step=5.0):
    return [(i * step, 0.0, 0.0) for i in range(int(length / step) + 1)]


def _arc(radius, span_deg=90.0, count=120):
    return [(radius * math.cos(math.radians(a)), radius * math.sin(math.radians(a)), 0.0)
            for a in (span_deg * i / count for i in range(count + 1))]


def _box_body(name, x0, x1, half_width=1.35, bottom=0.95, top=3.60, step=0.5):
    """Prostopadłościenna bryła zastępcza — tyle geometrii, ile potrzeba do pomiaru."""
    xs = [x0 + (x1 - x0) * i / max(1, int((x1 - x0) / step))
          for i in range(int((x1 - x0) / step) + 1)]
    vertices = [(x, y, z) for x in xs for y in (-half_width, 0.0, half_width)
                for z in (bottom, 0.5 * (bottom + top), top)]
    return {"name": name, "vertices": vertices, "span": (x0, x1)}


def _train(length=94.0, bodies=6):
    span = length / bodies
    return [_box_body(f"body_{i + 1}", i * span, (i + 1) * span) for i in range(bodies)]


# --- luz jako przekrój półpłaszczyzn -----------------------------------------

def test_clearance_profile_hull_orders_a_triangle_counter_clockwise():
    """Trzy punkty to już otoczka, ale KOLEJNOŚĆ ma znaczenie.

    Przegląd mutacyjny 02.09.2026: mutacja `len(pts) <= 2` -> `<= 3` przeżywała, bo
    nic nie sprawdzało trójkąta. Skrót zwróciłby wtedy punkty POSORTOWANE
    LEKSYKOGRAFICZNIE zamiast obiegu przeciwnego do zegara, a `halfplanes` chodzi po
    pierścieniu i liczy normalne z kolejnych krawędzi — przy złej kolejności wyszłyby
    normalne skierowane na zewnątrz i luz zmieniłby znak.
    """
    triangle = [(0.0, 0.0), (2.0, 0.0), (1.0, 1.0)]
    hull = CP.hull_2d(triangle)

    assert len(hull) == 3
    assert hull != sorted(set(triangle)), (
        "otoczka trójkąta wyszła w kolejności leksykograficznej, nie po obiegu")
    # Obieg przeciwny do zegara: pole ze wzoru sznurowadła jest DODATNIE.
    area2 = sum(a[0] * b[1] - b[0] * a[1]
                for a, b in zip(hull, hull[1:] + hull[:1]))
    assert area2 > 0.0, f"pole {area2} — obieg zgodny z zegarem"


def test_clearance_profile_halfplanes_accepts_a_triangle():
    # Trójkąt jest wypukłym obrysem i ma prawo przejść. Mutacje `count < 3` -> `<= 3`
    # oraz `3` -> `4` odrzucałyby go; nic tego nie sprawdzało.
    planes = CP.halfplanes(CP.hull_2d([(0.0, 0.0), (2.0, 0.0), (1.0, 1.0)]))
    assert len(planes) == 3

    # Kontrola negatywna: DWA punkty to nie obrys i mają zostać odrzucone,
    # więc rozluźnienie progu nie zamieniło się w brak progu.
    try:
        CP.halfplanes([(0.0, 0.0), (1.0, 1.0)])
    except ValueError:
        pass
    else:
        raise AssertionError("dwa punkty przeszły jako obrys profilu")


def test_clearance_profile_halfplanes_refuses_a_ring_with_zero_area():
    """Pierścień o zerowym polu nie jest obrysem — jest odcinkiem albo punktem.

    Decyzja właściciela z 04.09.2026, pozycja 12 w
    `docs/24-clearance-profile-decisions.md`: `halfplanes` ma go ODRZUCAĆ, tak samo
    jak odrzuca zerową krawędź. Przed tą decyzją liczył na nim dalej i zwracał
    półpłaszczyzny, w których luz każdego punktu jest niedodatni, a etykieta
    wiążącej krawędzi bierze się z orientacji policzonej ze `area2 == 0.0` —
    czyli z niczego.
    """
    for ring in ([(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)],
                 [(0.0, 0.0), (0.0, 1.0), (0.0, 2.0)],
                 [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)],
                 [(1.0, 1.0), (1.0, 1.0), (1.0, 1.0)],
                 [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 3.0)]):
        try:
            CP.halfplanes(ring)
        except ValueError as error:
            assert "zerowe pole" in str(error), (ring, str(error))
        else:
            raise AssertionError(f"przyjęty pierścień o zerowym polu: {ring}")


def test_clearance_profile_halfplanes_refuses_a_collinear_ring_that_rounds_off_zero():
    """DOKŁADNE `area2 == 0.0` przepuszczałoby prawie dwie trzecie wejść.

    To nie jest przypadek hipotetyczny i dlatego ma osobny test: dla trójki
    współliniowej o niecałkowitych współrzędnych suma wyznaczników nie wychodzi
    zerem, tylko rzędu 1e-15. Zmierzone 04.09.2026 na 200 000 losowych trójkach
    współliniowych: 63,46 % daje `area2 != 0.0`, największe |area2| to 2,183e-11.
    Strażnik porównuje więc z `CONVEXITY_EPS`, a nie z zerem, i ten test jest tym,
    co odróżnia jedną wersję od drugiej.
    """
    ring = [(0.1, 0.3), (1.7, 5.1), (3.3, 9.9)]
    area2 = 0.0
    for a, b in zip(ring, ring[1:] + ring[:1]):
        area2 += a[0] * b[1] - b[0] * a[1]
    assert area2 != 0.0, "to wejście przestało być tym, o co w tym teście chodzi"
    assert abs(area2) < CP.CONVEXITY_EPS, area2

    try:
        CP.halfplanes(ring)
    except ValueError as error:
        assert "zerowe pole" in str(error), str(error)
    else:
        raise AssertionError(f"przyjęty pierścień współliniowy o area2 = {area2!r}")


def test_clearance_profile_halfplanes_still_accepts_the_smallest_legitimate_ring():
    """Kontrola po DRUGIEJ stronie progu — bez niej strażnik mógłby odrzucać wszystko.

    Najmniejszy obrys, który ten zestaw testów każe przyjąć, to trójkąt 0,5 mm
    (`area2 = 2,5e-07`), czyli 2,4 rzędu POWYŻEJ progu. Prawdziwe profile z
    `profiles.py` leżą 10,8-11,3 rzędu powyżej. Zapas jest zmierzony z obu stron,
    a nie przyjęty na wiarę.
    """
    maly = [(0.0, 0.0), (5e-4, 0.0), (0.0, 5e-4)]
    assert len(CP.halfplanes(maly)) == 3

    import profiles
    for name in profiles.PROFILES:
        ring = [tuple(point) for point in profiles.profile_points(name)]
        planes = CP.halfplanes(ring)
        assert len(planes) == len(ring), name


def test_clearance_profile_halfplanes_refuses_a_ring_exactly_at_the_area_threshold():
    """Granica nowego progu jest OSIĄGALNA, więc `<=` kontra `<` to prawdziwa luka.

    Nowy strażnik wprowadził próg, a próg bez przybitej granicy jest dokładnie tym,
    na co narzeka `docs/24`. Zmierzone 04.09.2026: trójkąt o przyprostokątnych
    1e-5 i 1e-4 daje `area2` DOKŁADNIE `1e-09`, i tak samo cztery inne pary
    (1e-9 x 1, 1e-4 x 1e-5, 2e-5 x 5e-5, 1 x 1e-9).

    Wart uwagi jest sposób, w jaki to wyszło: 300 000 losowych obrysów o skali
    rozłożonej logarytmicznie trafiło w ten próg DOKŁADNIE **zero razy**. Samo
    próbkowanie podpowiedziałoby więc, że `<=` i `<` są nierozróżnialne — a nie są.
    W ten próg się nie wpada losowo, tylko się go konstruuje.

    Wybrana strona: na progu obrys jest już ODRZUCANY (`<=`), tak samo jak przy
    zerowej krawędzi niżej. 1e-5 m na 1e-4 m to 0,01 mm na 0,1 mm — nie jest to
    profil tunelu przy żadnym czytaniu.
    """
    dokladnie_na_progu = [(0.0, 0.0), (1e-5, 0.0), (0.0, 1e-4)]
    area2 = 0.0
    for a, b in zip(dokladnie_na_progu,
                    dokladnie_na_progu[1:] + dokladnie_na_progu[:1]):
        area2 += a[0] * b[1] - b[0] * a[1]
    assert abs(area2) == CP.CONVEXITY_EPS, (
        f"to wejście nie trafia już w próg dokładnie: {area2!r}")

    try:
        CP.halfplanes(dokladnie_na_progu)
    except ValueError as error:
        assert "zerowe pole" in str(error), str(error)
    else:
        raise AssertionError("obrys dokładnie na progu został przyjęty")

    # Druga strona granicy: o jeden bit powyżej progu obrys musi PRZEJŚĆ,
    # inaczej test przybijałby odmowę zamiast progu.
    import math
    tuz_powyzej = [(0.0, 0.0), (math.nextafter(1e-5, 1.0), 0.0), (0.0, 1e-4)]
    assert len(CP.halfplanes(tuz_powyzej)) == 3


def test_clearance_profile_halfplanes_refuses_a_zero_length_edge():
    """Zdublowany wierzchołek obrysu daje krawędź o zerowej długości.

    Bez strażnika `length <= 0.0` normalna dzieli się przez zero i zamiast czytelnej
    odmowy leci `ZeroDivisionError` z wnętrza pętli. Przegląd mutacyjny pokazał, że
    nic tego nie sprawdzało.
    """
    doubled = [(0.0, 0.0), (0.0, 0.0), (2.0, 0.0), (1.0, 1.0)]
    try:
        CP.halfplanes(doubled)
    except ValueError as error:
        assert "zerow" in str(error), str(error)
    else:
        raise AssertionError("obrys z zerową krawędzią przeszedł")


def test_clearance_profile_halfplane_clearance_matches_distance_to_boundary():
    """Sedno przyspieszenia: dla punktu wewnątrz obie drogi muszą dać tę samą liczbę."""
    for name in PR.PROFILES:
        ring = PR.profile_points(name)
        planes = CP.halfplanes(ring)
        x0, y0, x1, y1 = PR.bbox(name)
        worst = 0.0
        checked = 0
        for i in range(21):
            for j in range(21):
                x = x0 + (x1 - x0) * i / 20.0
                y = y0 + (y1 - y0) * j / 20.0
                reference = PL.distance_to_boundary(ring, x, y)
                if reference <= 0.0:
                    continue
                value, _label = CP.clearance_in_planes(planes, x, y)
                worst = max(worst, abs(value - reference))
                checked += 1
        assert checked > 50, (name, checked)
        assert worst < 1e-9, (name, worst)


def test_clearance_profile_halfplanes_reject_a_concave_ring():
    concave = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (2.0, 1.0), (0.0, 4.0)]
    try:
        CP.halfplanes(concave)
    except ValueError as exc:
        assert "wypukły" in str(exc)
    else:
        raise AssertionError("wklęsły obrys powinien zostać odrzucony")


def test_clearance_profile_labels_wall_roof_and_floor_apart():
    labels = {plane[3] for plane in PLANES}
    assert CP.WALL in labels and CP.ROOF in labels and CP.FLOOR in labels
    assert CP.CHAMFER in labels
    assert CP.clearance_in_planes(PLANES, 4.0, 1.0)[1] == CP.WALL
    assert CP.clearance_in_planes(PLANES, 0.0, 4.5)[1] == CP.ROOF
    assert CP.clearance_in_planes(PLANES, 0.0, -1.0)[1] == CP.FLOOR


# --- ramki i offsety ----------------------------------------------------------

def test_clearance_profile_offsets_match_placement():
    """Ramka wybrana lokalnie musi dać te same offsety, co `placement.local_offsets`."""
    points = _arc(120.0)
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    place = PL.place_spans(points, stations, 30.0, [(0.0, 15.0)], 2.10)[0]
    worst = 0.0
    for x in (0.0, 3.0, 7.5, 11.0, 15.0):
        for y in (-1.35, 0.0, 1.35):
            for z in (0.95, 3.60):
                world = PL.transform_point(place, (x, y, z))
                index = CP.nearest_frame(frames, stations, world, hint_m=30.0 + x)
                mine = CP.offsets_in_frame(frames[index], stations[index], world)
                reference = PL.local_offsets(world, frames, stations, (20.0, 60.0))
                worst = max(worst, max(abs(a - b) for a, b in zip(mine, reference)))
    assert worst < 1e-9, worst


def test_clearance_profile_band_coefficients_are_the_affine_expansion():
    points = _arc(120.0)
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    place = PL.place_spans(points, stations, 30.0, [(0.0, 15.0)], -2.10)[0]
    index = 12
    coefficients = CP.band_coefficients(place, frames[index], stations[index])
    for local in ((0.0, 1.35, 3.6), (7.5, -1.35, 0.95), (15.0, 0.0, 2.0)):
        world = PL.transform_point(place, local)
        expected = CP.offsets_in_frame(frames[index], stations[index], world)
        got = tuple(c[0] + c[1] * local[0] + c[2] * local[1] + c[3] * local[2]
                    for c in coefficients)
        assert max(abs(a - b) for a, b in zip(expected, got)) < 1e-9, (local, expected, got)


def test_clearance_profile_point_at_matches_frame_at():
    points = _arc(90.0)
    stations = SW.chainages(points)
    for chainage in (0.0, 12.3, 55.5, stations[-1]):
        a = CP.point_at(points, stations, chainage)
        b, _index, _t = PL.frame_at(points, stations, chainage)
        assert max(abs(a[i] - b[i]) for i in range(3)) < 1e-9, chainage


# --- kandydaci ----------------------------------------------------------------

def test_clearance_profile_hull_keeps_the_extremes_and_drops_the_inside():
    square = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.5, 0.5), (0.4, 0.6)]
    hull = CP.hull_2d(square)
    assert len(hull) == 4
    assert (0.5, 0.5) not in hull and (0.4, 0.6) not in hull


def test_clearance_profile_exact_bands_do_not_lose_the_minimum():
    """Redukcja kandydatów nie ma prawa podnieść zmierzonego minimum ani o mikrometr."""
    points = _arc(95.0)
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    bodies = _train()
    reduced = CP.reduce_bodies(bodies, CP.CANDIDATE_BUCKET_M)
    assert CP.candidate_count(reduced) < sum(len(b["vertices"]) for b in bodies)
    for start in (10.0, 25.0):
        for offset in (-2.10, 2.10):
            fast = CP.measure_position(points, frames, stations, PLANES, reduced, start, offset)
            slow = CP.measure_position_naive(points, frames, stations, BOX, bodies, start, offset)
            assert abs(fast["clearance_m"] - slow["clearance_m"]) < 1e-9, (start, offset, fast, slow)


def test_clearance_profile_straight_track_is_bound_by_the_roof():
    points = _straight()
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    reduced = CP.reduce_bodies(_train())
    record = CP.measure_position(points, frames, stations, PLANES, reduced, 100.0, 2.10)
    # 4,70 m stropu minus 3,60 m dachu; na prostej nie ma strzałki, więc wiąże wysokość
    assert abs(record["clearance_m"] - 1.10) < 1e-9, record
    assert record["bound_by"] == CP.ROOF


def test_clearance_profile_curve_pushes_the_body_towards_the_wall():
    points = _arc(95.0)
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    reduced = CP.reduce_bodies(_train())
    # Na danym łuku pudło idzie ku ścianie tylko na JEDNYM torze; na drugim ucieka
    # do środka otworu i wiążącą wielkością zostaje wysokość stropu.
    records = [CP.measure_position(points, frames, stations, PLANES, reduced, 20.0, offset)
               for offset in (-2.10, 2.10)]
    binding = min(records, key=lambda r: r["clearance_m"])
    straight = 4.70 - 2.10 - 1.35
    assert binding["clearance_m"] < straight, records
    assert binding["bound_by"] == CP.WALL, binding
    assert max(r["clearance_m"] for r in records) == 1.10


def test_clearance_profile_negative_clearance_is_reported_not_clamped():
    """Ujemny luz jest wynikiem do zaraportowania, nie do zamiecenia pod dywan."""
    points = _straight()
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    fat = [_box_body("fat", 0.0, 20.0, half_width=3.20)]
    reduced = CP.reduce_bodies(fat)
    record = CP.measure_position(points, frames, stations, PLANES, reduced, 50.0, 2.10)
    assert record["clearance_m"] < 0.0, record
    stats = CP.statistics([record])
    assert stats["negative_positions"] == 1
    assert stats["min_clearance_m"] < 0.0


# --- pokrycie osi i statystyki ------------------------------------------------

def test_clearance_profile_positions_cover_the_axis_end_to_end():
    positions = CP.scan_positions(1000.0, 94.0, 5.0)
    assert positions[0] == 0.0
    assert abs(positions[-1] - 906.0) < 1e-9
    for a, b in zip(positions, positions[1:]):
        assert b - a <= 5.0 + 1e-9


def test_clearance_profile_positions_keep_the_tail_when_step_does_not_divide():
    positions = CP.scan_positions(1000.0, 94.0, 7.0)
    assert abs(positions[-1] - 906.0) < 1e-9
    assert positions[-1] - positions[-2] <= 7.0 + 1e-9


def test_clearance_profile_coverage_gaps_finds_a_hole():
    records = [{"start_m": s, "clearance_m": 1.0} for s in (0.0, 5.0, 10.0, 30.0, 106.0)]
    problems = CP.coverage_gaps(records, 94.0, 200.0, 5.0)
    assert any("dziura" in p for p in problems), problems
    good = [{"start_m": float(s), "clearance_m": 1.0} for s in range(0, 106, 5)]
    good.append({"start_m": 106.0, "clearance_m": 1.0})
    assert CP.coverage_gaps(good, 94.0, 200.0, 5.0) == []


def test_clearance_profile_statistics_count_positions_below_thresholds():
    records = [{"start_m": float(i), "clearance_m": value, "object": "b", "bound_by": CP.WALL,
                "chainage_m": float(i), "lateral_m": 0.0, "vertical_m": 0.0, "chord_m": 15.0}
               for i, value in enumerate([1.10] * 90 + [0.95] * 5 + [0.80] * 4 + [-0.05])]
    stats = CP.statistics(records, thresholds=(1.000, 0.900, 0.000))
    assert stats["positions"] == 100
    assert stats["min_clearance_m"] == -0.05
    assert stats["below_threshold"]["1.000"] == 10
    assert stats["below_threshold"]["0.900"] == 5
    assert stats["below_threshold"]["0.000"] == 1
    assert stats["negative_positions"] == 1
    assert stats["median_clearance_m"] == 1.10


def test_clearance_profile_refinement_windows_bracket_the_dip():
    records = [{"start_m": float(i * 5), "clearance_m": 1.10} for i in range(20)]
    records[10]["clearance_m"] = 0.90
    windows = CP.refine_windows(records, 5.0)
    assert len(windows) == 1
    low, high = windows[0]
    assert low <= 50.0 - 5.0 + 1e-9 and high >= 50.0 + 5.0 - 1e-9


# --- miejsca krytyczne i stacje ----------------------------------------------

def _record(chainage, clearance, start=0.0):
    return {"start_m": start, "clearance_m": clearance, "object": "M7_car_1",
            "bound_by": CP.WALL, "chainage_m": chainage, "lateral_m": 3.8,
            "vertical_m": 1.03, "chord_m": 15.0}


STATIONS_DOC = [{"name": "Comte de Flandre|Graaf van Vlaanderen", "chainage_m": 2054.92},
                {"name": "Sainte-Catherine|Sint-Katelijne", "chainage_m": 2721.01}]


def test_clearance_profile_critical_places_merge_one_curve_into_one_entry():
    """Jeden ciasny łuk widziany z setek pozycji składu to JEDNO miejsce w tunelu."""
    records = [_record(2520.0 + 0.25 * i, 0.92, start=2400.0 + i) for i in range(40)]
    records.append(_record(4000.0, 0.93, start=3900.0))
    places = CP.critical_places(records, 0.95, STATIONS_DOC)
    assert len(places) == 2, places
    assert places[0]["positions"] == 40
    assert places[0]["nearest_station"]["name"].startswith("Sainte-Catherine")
    assert places[0]["between"] == {"after": "Comte de Flandre|Graaf van Vlaanderen",
                                    "before": "Sainte-Catherine|Sint-Katelijne"}


def test_clearance_profile_critical_places_are_empty_above_the_threshold():
    assert CP.critical_places([_record(2520.0, 1.10)], 0.95, STATIONS_DOC) == []


def test_clearance_profile_nearest_station_reports_the_distance():
    near = CP.nearest_station(STATIONS_DOC, 2721.01 + 200.0)
    assert near["name"].startswith("Sainte-Catherine")
    assert abs(near["distance_m"] - 200.0) < 0.05


# --- promienie i strzałka -----------------------------------------------------

def test_clearance_profile_min_radius_on_chord_recovers_the_arc():
    radius = 95.0
    points = _arc(radius, span_deg=120.0, count=400)
    stations = SW.chainages(points)
    _station, measured = CP.min_radius_on_chord(points, stations, 15.0, 20.0)
    assert abs(measured - radius) < 0.5, measured


def test_clearance_profile_chord_deviation_matches_the_versine_on_a_circle():
    """Na łuku okręgu zmierzone odchylenie i wzór na strzałkę muszą się zgodzić."""
    radius = 95.0
    chord = 15.0
    points = _arc(radius, span_deg=120.0, count=600)
    stations = SW.chainages(points)
    centre = stations[-1] / 2.0
    measured = CP.chord_deviation_m(points, stations, centre - chord / 2.0, centre + chord / 2.0)
    assert abs(measured - CL.versine(chord, radius)) < 0.002, (measured, CL.versine(chord, radius))


# --- zamiatana obwiednia ------------------------------------------------------

def _sweep_envelope(points, stations, frames, reduced, starts, offset, low, high):
    envelope = CP.SweptEnvelope(stations, low, high)
    samples = []
    for start in starts:
        def collector(chainage, lateral, vertical):
            envelope.add(chainage, lateral, vertical)
            samples.append((chainage, lateral, vertical))
        CP.measure_position(points, frames, stations, PLANES, reduced, start, offset,
                            collector=collector)
    return envelope, samples


def test_clearance_profile_support_polygon_circumscribes_the_points():
    directions = CP.support_directions(24)
    points = [(1.35, 0.95), (-1.35, 0.95), (-1.35, 3.60), (1.35, 3.60)]
    heights = [max(d[0] * p[0] + d[1] * p[1] for p in points) for d in directions]
    polygon = CP.support_polygon(directions, heights)
    for point in points:
        assert PL.distance_to_boundary(polygon, *point) >= -1e-9, point


def test_clearance_profile_swept_envelope_contains_the_train_in_every_position():
    points = _arc(95.0)
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    reduced = CP.reduce_bodies(_train())
    starts = [10.0 + 2.0 * i for i in range(10)]
    envelope, samples = _sweep_envelope(points, stations, frames, reduced, starts, 2.10,
                                        60.0, 120.0)
    rings = envelope.rings()
    assert len(rings) >= 5, len(rings)
    outside, checked = CP.envelope_contains(envelope, rings, samples)
    assert checked > 1000, checked
    assert outside == 0, outside


def test_clearance_profile_swept_envelope_is_wider_than_the_static_one():
    """To NIE jest `--envelope-out` z m7_shell.py: na łuku zamiatana bryła jest szersza."""
    points = _arc(95.0)
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    reduced = CP.reduce_bodies(_train())
    starts = [10.0 + 2.0 * i for i in range(12)]
    envelope, _samples = _sweep_envelope(points, stations, frames, reduced, starts, 2.10,
                                         60.0, 120.0)
    widths = []
    for _index, polygon in envelope.rings():
        lows = [p[0] for p in polygon]
        widths.append(max(lows) - min(lows))
    assert widths, "obwiednia nie ma ani jednego pierścienia"
    assert max(widths) > 2.70 + 0.05, max(widths)


def test_clearance_profile_swept_envelope_ignores_positions_outside_its_range():
    points = _straight()
    stations = SW.chainages(points)
    envelope = CP.SweptEnvelope(stations, 100.0, 200.0)
    envelope.add(50.0, 1.0, 1.0)
    assert envelope.rings_for(50.0) == ()
    assert envelope.rings() == []
    envelope.add(150.0, 1.0, 1.0)
    assert envelope.rings_for(150.0)


def test_clearance_profile_swept_mesh_is_closed_and_finite():
    points = _arc(95.0)
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    reduced = CP.reduce_bodies(_train())
    envelope, _samples = _sweep_envelope(points, stations, frames, reduced,
                                         [10.0 + 2.0 * i for i in range(10)], 2.10, 60.0, 120.0)
    rings = envelope.rings()
    mesh = CP.swept_mesh(frames, rings)
    columns = mesh["columns"]
    assert len(mesh["vertices"]) == columns * len(rings)
    assert len(mesh["faces"]) == columns * (len(rings) - 1) + 2
    for vertex in mesh["vertices"]:
        for value in vertex:
            assert not math.isnan(value) and not math.isinf(value)
    low, high = CP.mesh_bbox(mesh)
    assert high[2] - low[2] > 2.0, (low, high)
    assert high[0] - low[0] > 10.0


def test_clearance_profile_swept_mesh_rejects_a_single_ring():
    try:
        CP.swept_mesh([], [(0, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)])])
    except ValueError as exc:
        assert "2 pierścieni" in str(exc)
    else:
        raise AssertionError("jeden pierścień nie jest bryłą")


def test_clearance_profile_envelope_clearance_is_never_better_than_the_scan():
    """Obwiednia jest nadzbiorem, więc jej luz musi być mniejszy lub równy zmierzonemu."""
    points = _arc(95.0)
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    reduced = CP.reduce_bodies(_train())
    starts = [10.0 + 2.0 * i for i in range(12)]
    envelope, _samples = _sweep_envelope(points, stations, frames, reduced, starts, 2.10,
                                         60.0, 120.0)
    envelope_min, where = CP.envelope_clearance(envelope.rings(), PLANES)
    scan_min = min(CP.measure_position(points, frames, stations, PLANES, reduced, s,
                                       2.10)["clearance_m"] for s in starts)
    assert where is not None
    assert envelope_min <= scan_min + 1e-9, (envelope_min, scan_min)
    assert envelope_min > scan_min - 0.05, (envelope_min, scan_min)


# --- strażniki wejścia zdegenerowanego ---------------------------------------
#
# Klasa „strażnik zdegenerowany" z `reports/mutation-triage-clearance.md`: puste
# listy, zerowe kroki, jednoelementowe pierścienie. Każdy test poniżej trafia
# w JEDEN warunek i jest ZMIERZONY przeglądem mutacyjnym — nie „dotyka funkcji",
# tylko rozstrzyga próg. Lekcja z triażu `clearance.py`: test, który wygląda na
# pokrycie progu, może nie dotykać tego progu wcale.


def test_clearance_profile_hull_of_at_most_two_points_is_the_points_themselves():
    """Skrót `len(pts) <= 2` — wejście, na którym otoczki nie ma.

    Mutacja `<=` -> `<` jest tu **równoważna** i jest to ZMIERZONE, nie wyczytane
    z kodu: na 99 840 losowych wejściach o dokładnie dwóch różnych punktach
    oryginał i mutant dały ten sam wynik 99 840 razy, inny 0 razy. Dla dwóch
    punktów łańcuch monotoniczny zwraca `lower[:-1] + upper[:-1]`, czyli tę samą
    parę w tej samej kolejności co skrót. Test zostaje jako pokrycie samego
    zejścia do wejścia zdegenerowanego, nie jako zabójca mutacji.
    """
    assert CP.hull_2d([]) == []
    assert CP.hull_2d([(1.0, 2.0)]) == [(1.0, 2.0)]
    assert CP.hull_2d([(2.0, 0.0), (0.0, 1.0)]) == [(0.0, 1.0), (2.0, 0.0)]
    # Zdublowany punkt to jeden punkt, nie dwa.
    assert CP.hull_2d([(0.0, 0.0), (0.0, 0.0)]) == [(0.0, 0.0)]


def test_clearance_profile_positive_bucket_still_buckets_when_it_is_tiny():
    """`bucket_m <= 0.0` znaczy „pasma dokładne"; KAŻDA wartość dodatnia kubełkuje.

    Mutacja progu `0.0` -> `0.001` sprawia, że krok 1 mm przestaje być kubełkiem
    i zaczyna znaczyć „dokładnie" — cicha zmiana znaczenia parametru. Dwa
    wierzchołki 0,5 mm od siebie: przy kubełku 1 mm są JEDNYM pasmem, przy
    pasmach dokładnych dwoma.
    """
    vertices = [(0.0, -1.0, 0.0), (0.0, 1.0, 0.0),
                (0.0005, -1.0, 1.0), (0.0005, 1.0, 1.0)]
    bucketed = CP.candidate_bands(vertices, 0.001)
    assert len(bucketed) == 1, bucketed
    assert len(bucketed[0]["points"]) == 4, bucketed

    # Kontrola negatywna: zero nadal znaczy „dokładnie", więc te same wierzchołki
    # rozpadają się na dwa pasma.
    exact = CP.candidate_bands(vertices, 0.0)
    assert len(exact) == 2, exact


def test_clearance_profile_orientation_follows_the_sign_of_the_area_not_its_size():
    """Znak pola decyduje o kierunku normalnych — jego WIELKOŚĆ nie decyduje o niczym.

    Mutacja `area2 > 0.0` -> `> 0.001` odwraca orientację każdego obrysu o polu
    mniejszym niż 0,001, więc trójkąt 2 cm x 2 cm (`area2 = 4e-4`) dostaje
    normalne na zewnątrz i wypada z bramki wypukłości jako wklęsły.
    """
    small = [(0.0, 0.0), (0.02, 0.0), (0.0, 0.02)]
    planes = CP.halfplanes(small)
    assert len(planes) == 3
    # Środek ciężkości leży wewnątrz, więc luz musi być DODATNI.
    clearance, _label = CP.clearance_in_planes(planes, 0.005, 0.005)
    assert clearance > 0.0, (clearance, planes)


def test_clearance_profile_halfplanes_accept_a_half_millimetre_edge():
    """Strażnik `length <= 0.0` broni przed dzieleniem przez zero, nie przed krótkim.

    Mutacja progu `0.0` -> `0.001` odrzuca każdą krawędź krótszą niż milimetr,
    a obrys z takim odcinkiem jest poprawnym obrysem wypukłym. Wierzchołek 0,5 mm
    za poprzednim leży na tej samej prostej, więc wypukłość zostaje nienaruszona.
    """
    ring = [(0.0, 0.0), (1.0, 0.0), (1.0005, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
    planes = CP.halfplanes(ring)
    assert len(planes) == len(ring)
    # Punkt wewnątrz nadal ma dodatni luz — obrys nie rozjechał się na tej krawędzi.
    clearance, label = CP.clearance_in_planes(planes, 1.0, 0.4)
    assert clearance > 0.0, (clearance, label)


def test_clearance_profile_nearest_frame_ignores_a_hint_off_the_axis():
    """„Wynik nie zależy od trafności podpowiedzi" — z podpowiedzią 600 m za osią.

    Pętla rozszerza okno, dopóki nie obejmie choć jednej ramki; warunek `high > low`
    jest jedyną rzeczą, która ją do tego zmusza. Po mutacji na `>=` pętla wychodzi
    natychmiast, bo `bisect_left <= bisect_right` zawsze, i funkcja zwraca indeks
    WSTAWIENIA — tu 81 przy 81 ramkach, czyli indeks poza tablicą.
    """
    points = _straight()
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    index = CP.nearest_frame(frames, stations, (400.0, 0.0, 0.0),
                             window_m=1.0, hint_m=1000.0)
    assert index < len(frames), (index, len(frames))
    assert index == len(frames) - 1, index


def test_clearance_profile_nearest_frame_accepts_a_window_grown_to_the_limit():
    """Granica rozszerzania okna: przy rozpiętości DOKŁADNIE równej limitowi wolno szukać.

    Limit to `4 * (długość osi + 1)`. Oś [0; 1] daje limit 8,0; okno startowe 4,0
    z podpowiedzią 6,0 nie łapie nic, więc rozpiętość rośnie do 8,0 — dokładnie do
    limitu. Mutacja `>` -> `>=` odmawia w tym miejscu obsługi osi, która ramki MA.
    """
    points = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    index = CP.nearest_frame(frames, stations, (1.0, 0.0, 0.0),
                             window_m=4.0, hint_m=6.0)
    assert index == 1, index

    # Kontrola negatywna: oś bez ani jednej ramki nadal kończy się odmową.
    try:
        CP.nearest_frame([], [0.0, 1.0], (1.0, 0.0, 0.0), window_m=4.0, hint_m=1e9)
    except ValueError as exc:
        assert "ramki" in str(exc), str(exc)
    else:
        raise AssertionError("pusta lista ramek przeszła")


def test_clearance_profile_scan_positions_refuses_a_zero_step():
    """Zerowy krok: bez strażnika leci `ZeroDivisionError` z `floor(last / step)`.

    Mutacja `step_m <= 0.0` -> `< 0.0` przepuszcza dokładnie zero.
    """
    try:
        CP.scan_positions(1000.0, 94.0, 0.0)
    except ValueError as exc:
        assert "dodatni" in str(exc), str(exc)
    else:
        raise AssertionError("krok zerowy przeszedł")

    # Kontrola negatywna: krok ujemny też jest odmawiany.
    try:
        CP.scan_positions(1000.0, 94.0, -5.0)
    except ValueError:
        pass
    else:
        raise AssertionError("krok ujemny przeszedł")


def test_clearance_profile_scan_positions_accept_a_millimetre_step():
    """Strażnik kroku pilnuje ZNAKU, nie rzędu wielkości.

    Mutacja progu `0.0` -> `0.001` odrzuca krok milimetrowy, a doszlifowanie
    chodzi krokiem 0,25 m i nic nie zabrania zejść niżej.
    """
    positions = CP.scan_positions(95.0, 94.0, 0.001)
    assert len(positions) == 1001, len(positions)
    assert positions[0] == 0.0
    assert abs(positions[-1] - 1.0) < 1e-9, positions[-1]


def test_clearance_profile_scan_positions_refuse_a_train_as_long_as_the_axis():
    """Skład dokładnie tak długi jak oś: zakres skanu ma zerową długość.

    Test PRZYPINA obowiązujący kontrakt, a nie rozstrzyga go od nowa: komunikat
    strażnika mówi „nie mieści się", więc równość jest odmową. Mutacja
    `last <= 0.0` -> `< 0.0` zwracała w tym miejscu profil z jednej pozycji.
    Gdyby właściciel chciał, żeby równość była dopuszczalna, zmienia się strażnik
    i ten test razem z nim.
    """
    try:
        CP.scan_positions(94.0, 94.0, 5.0)
    except ValueError as exc:
        assert "nie mieści się" in str(exc), str(exc)
    else:
        raise AssertionError("skład równy długości osi przeszedł")


def test_clearance_profile_scan_positions_accept_half_a_millimetre_of_room():
    """Strażnik „nie mieści się" pilnuje ZNAKU zapasu, nie jego rzędu wielkości.

    Mutacja progu `0.0` -> `0.001` odmawia osi dłuższej od składu o 0,5 mm.
    Oryginał daje wtedy dwie pozycje: początek i dokładny koniec zakresu.
    """
    positions = CP.scan_positions(94.0005, 94.0, 5.0)
    assert positions[0] == 0.0
    assert len(positions) == 2, positions
    assert abs(positions[-1] - 0.0005) < 1e-9, positions[-1]


def test_clearance_profile_point_at_survives_a_duplicated_last_vertex():
    """Zerowe rozpięcie w `point_at` jest osiągalne WYŁĄCZNIE na końcu osi.

    Odwrotnie niż w `clearance._point_at`, gdzie duplikat musiał stać na POCZĄTKU:
    tam pętla zwracała przy pierwszym pasującym przedziale, tu indeks wychodzi
    z `bisect_right` i przycięcia do `len(points) - 2`. Dla duplikatu na początku
    albo w środku `bisect_right` przeskakuje nad nim i rozpięcie jest dodatnie;
    zerowe wychodzi dopiero wtedy, gdy przycięcie wskaże ostatnią, zdublowaną parę.
    Bez strażnika `span <= 0.0` leci tam `ZeroDivisionError`.
    """
    points = [(0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (10.0, 0.0, 0.0), (10.0, 0.0, 0.0)]
    stations = [0.0, 5.0, 10.0, 10.0]
    assert CP.point_at(points, stations, 10.0) == (10.0, 0.0, 0.0)

    # Duplikat na POCZĄTKU osi tego warunku nie uruchamia — zapisane, żeby nikt
    # nie „naprawiał" tego testu przenoszeniem duplikatu.
    start = [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (10.0, 0.0, 0.0)]
    assert CP.point_at(start, [0.0, 0.0, 5.0, 10.0], 0.0) == (0.0, 0.0, 0.0)


def test_clearance_profile_point_at_interpolates_inside_a_half_millimetre_span():
    """Strażnik zerowego rozpięcia nie ma prawa zjeść interpolacji w krótkim odcinku.

    Mutacja progu `0.0` -> `0.001` zwraca w odcinku 0,5 mm lewy koniec zamiast
    punktu w środku — 0,25 mm błędu w funkcji, którą `min_radius_on_chord` woła
    dwa razy na każdy pierścień osi.
    """
    points = [(0.0, 0.0, 0.0), (0.0005, 0.0, 0.0), (5.0, 0.0, 0.0)]
    stations = [0.0, 0.0005, 5.0]
    got = CP.point_at(points, stations, 0.00025)
    assert abs(got[0] - 0.00025) < 1e-12, got


def test_clearance_profile_support_directions_accept_exactly_three():
    """Komunikat mówi „co najmniej 3", więc trzy MUSZĄ przejść.

    Mutacje `count < 3` -> `<= 3` i `3` -> `4` odrzucały trzy kierunki; nic tego
    nie sprawdzało, bo wszystkie testy obwiedni chodzą po 24 albo 32 kierunkach.
    """
    directions = CP.support_directions(3)
    assert len(directions) == 3, directions
    for dx, dy in directions:
        assert abs(math.hypot(dx, dy) - 1.0) < 1e-12, (dx, dy)

    # Kontrola negatywna: dwa kierunki nie wyznaczają obrysu i nadal są odmawiane.
    try:
        CP.support_directions(2)
    except ValueError as exc:
        assert "3 kierunków" in str(exc), str(exc)
    else:
        raise AssertionError("dwa kierunki podparcia przeszły")


def test_clearance_profile_support_polygon_from_three_directions_is_a_triangle():
    """Trzy kierunki dają trzy wierzchołki — dokładnie na progu `len(out) < 3`.

    Mutacje `< 3` -> `<= 3` i `3` -> `4` odrzucały ten wynik jako zdegenerowany.
    """
    directions = CP.support_directions(3)
    points = [(1.35, 0.95), (-1.35, 0.95), (-1.35, 3.60), (1.35, 3.60)]
    heights = [max(d[0] * p[0] + d[1] * p[1] for p in points) for d in directions]
    polygon = CP.support_polygon(directions, heights)
    assert len(polygon) == 3, polygon
    for point in points:
        assert PL.distance_to_boundary(polygon, *point) >= -1e-9, point

    # Kontrola negatywna: dwa kierunki przeciwne dają wyznacznik zerowy, więc
    # z trzech prostych zostają dwa wierzchołki i odmowa musi zostać odmową.
    try:
        CP.support_polygon([(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0)], [1.0, 1.0, 1.0])
    except ValueError as exc:
        assert "3 wierzchołków" in str(exc), str(exc)
    else:
        raise AssertionError("obrys z dwóch wierzchołków przeszedł")


def test_clearance_profile_swept_mesh_from_exactly_two_rings():
    """Dwa pierścienie to najkrótsza rura, która jeszcze jest rurą.

    `test_..._swept_mesh_rejects_a_single_ring` pilnuje odmowy dla JEDNEGO
    pierścienia, ale nie odróżnia progu `< 2` od `<= 2` ani od `< 3` — przy jednym
    pierścieniu odmawiają wszystkie trzy. Rozstrzygają dopiero dokładnie dwa:
    osiem wierzchołków, cztery ściany boczne i dwie zaślepki.
    """
    points = _straight(20.0)
    frames = SW.rmf_frames(points)
    polygon = [(-1.0, 0.0), (1.0, 0.0), (1.0, 2.0), (-1.0, 2.0)]
    mesh = CP.swept_mesh(frames, [(0, polygon), (1, polygon)])
    assert mesh["rings"] == 2 and mesh["columns"] == 4
    assert len(mesh["vertices"]) == 8, len(mesh["vertices"])
    assert len(mesh["faces"]) == 4 + 2, mesh["faces"]
    low, high = CP.mesh_bbox(mesh)
    assert abs((high[0] - low[0]) - 5.0) < 1e-9, (low, high)

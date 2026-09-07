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


def test_clearance_profile_scan_positions_accept_a_train_as_long_as_the_axis():
    """Skład dokładnie tak długi jak oś ma JEDNĄ pozycję, nie zero.

    Poprzednia wersja tego testu przypinała odmowę i mówiła wprost: „gdyby właściciel
    chciał, żeby równość była dopuszczalna, zmienia się strażnik i ten test razem
    z nim". Właściciel tak zdecydował (pozycja 7 `docs/24`), więc test jest PRZEPISANY,
    nie dopisany obok.

    Powód decyzji jest zmierzalny i zmierzony: skład 93,999 m na osi 94,0 m dawał dwie
    pozycje `[0.0, 0.001]`, a skład 94,0 m — wyjątek. Nieciągłość w miejscu, w którym
    wynik jest dobrze określony (skład zajmuje dokładnie całą oś).
    """
    positions = CP.scan_positions(94.0, 94.0, 5.0)
    assert positions == [0.0], positions

    # Kontrola negatywna po DRUGIEJ stronie granicy: skład dłuższy od osi choćby
    # o milimetr nadal jest odmową. Bez tej połowy „poluzowałem strażnika" nie da się
    # odróżnić od „usunąłem strażnika".
    try:
        CP.scan_positions(94.0, 94.001, 5.0)
    except ValueError as exc:
        assert "nie mieści się" in str(exc), str(exc)
    else:
        raise AssertionError("skład dłuższy od osi przeszedł")

    # I ciągłość, o którą cała pozycja szła: 93,999 / 94,000 / 94,001 to teraz
    # dwie pozycje / jedna pozycja / odmowa, a nie dwie / odmowa / odmowa.
    assert len(CP.scan_positions(94.0, 93.999, 5.0)) == 2


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


def test_clearance_profile_a_clearance_exactly_at_the_threshold_is_reported():
    """Sedno decyzji właściciela: luz DOKŁADNIE na progu nie może zniknąć z raportu.

    `docs/24` pozycja 3 zmierzyła, że minimum na pakiecie A to 0,899948 m przy progu
    raportowania 0,900 m — różnica 52 µm. Gdyby minimum wypadło o te 52 µm wyżej,
    czyli dokładnie na progu, stary warunek `clearance_m < threshold_m` nie zgłosiłby
    NAJCIAŚNIEJSZEGO MIEJSCA NA CAŁYM PAKIECIE. Pasmo zgłasza je w obu przypadkach.
    """
    dokladnie = CP.critical_places([_record(2520.0, 0.900)], 0.900, STATIONS_DOC)
    assert len(dokladnie) == 1, dokladnie
    assert dokladnie[0]["at_threshold"] is True

    ponizej = CP.critical_places([_record(2520.0, 0.899948)], 0.900, STATIONS_DOC)
    assert len(ponizej) == 1, ponizej
    assert ponizej[0]["at_threshold"] is True, "52 µm pod progiem to nadal pasmo graniczne"

    glebiej = CP.critical_places([_record(2520.0, 0.850)], 0.900, STATIONS_DOC)
    assert len(glebiej) == 1
    assert glebiej[0]["at_threshold"] is False, "50 mm pod progiem to już nie pasmo"


def test_clearance_profile_the_threshold_band_is_two_sided():
    """„Dwustronny" znaczy dwustronny — także POWYŻEJ progu, i to jest cała różnica.

    Warunek jednostronny (`<=` zamiast `<`) łapałby wyłącznie równość co do bitu,
    czyli w praktyce nic. Kontrola negatywna po drugiej stronie pasma jest tu tym,
    co odróżnia tolerancję od zmiany operatora.
    """
    milimetr_nad = CP.critical_places([_record(2520.0, 0.901)], 0.900, STATIONS_DOC)
    assert len(milimetr_nad) == 1, "luz milimetr NAD progiem wypadł z raportu"
    assert milimetr_nad[0]["at_threshold"] is True

    poza_pasmem = CP.critical_places([_record(2520.0, 0.902)], 0.900, STATIONS_DOC)
    assert poza_pasmem == [], "pasmo objęło luz dwa milimetry nad progiem"

    # Symetria pasma, i to jest cała treść słowa „dwustronny": milimetr pod progiem
    # i milimetr nad nim muszą być traktowane jednakowo. Pierwsza wersja tej bramki
    # liczyła pasmo na floatach i `abs(0.899 - 0.900)` wychodziło
    # `0.0010000000000000009` — czyli WIĘCEJ niż tolerancja, więc milimetr pod progiem
    # z pasma wypadał, a pół milimetra nad nim wpadało. Granica rozstrzygała się
    # reprezentacją binarną, nie decyzją.
    assert CP.within_threshold_band(0.899, 0.900) is True
    assert CP.within_threshold_band(0.901, 0.900) is True
    assert CP.within_threshold_band(0.898, 0.900) is False
    assert CP.within_threshold_band(0.902, 0.900) is False


def test_clearance_profile_below_threshold_keeps_meaning_strictly_below():
    """Stary klucz nie zmienia znaczenia, bo czyta go `profile_vehicle.py` i bramka CI.

    Pasmo dochodzi jako OSOBNY klucz. Gdyby `below_threshold` zaczęło liczyć pasmo,
    liczba w raporcie zmieniłaby sens bez zmiany nazwy — a to jest dokładnie ten
    rodzaj cichego rozjazdu, którego ten moduł ma nie produkować.
    """
    records = [_record(100.0, 0.850), _record(200.0, 0.899),
               _record(300.0, 0.900), _record(400.0, 0.901)]
    stats = CP.statistics(records, thresholds=(0.900,))
    assert stats["below_threshold"]["0.900"] == 2, stats["below_threshold"]
    assert stats["at_threshold"]["0.900"] == 3, stats["at_threshold"]
    assert stats["threshold_tolerance_m"] == CP.THRESHOLD_TOLERANCE_M


def test_clearance_profile_tolerance_equals_the_resolution_the_module_records():
    """Tolerancja nie jest liczbą z powietrza — równa się rozdzielczości ZAPISU progów.

    `critical_places` zapisuje próg przez `round(threshold_m, 3)`, a `statistics`
    kluczuje po `f"{t:.3f}"`. Poniżej milimetra w wyjściu nie ma więc informacji,
    po której stronie progu leży wartość. Ten test przybija tę równość, żeby zmiana
    jednej strony bez drugiej nie przeszła po cichu.
    """
    source = open(os.path.join(ROOT, "tools", "blender", "clearance_profile.py"),
                  encoding="utf-8").read()
    assert 'round(threshold_m, 3)' in source, "zmieniła się rozdzielczość zapisu progu"
    assert 'f"{t:.3f}"' in source, "zmieniła się rozdzielczość kluczy statystyk"
    assert CP.THRESHOLD_TOLERANCE_M == 10 ** -3, CP.THRESHOLD_TOLERANCE_M
    assert CP.THRESHOLD_TOLERANCE_MM == 1, CP.THRESHOLD_TOLERANCE_MM
    assert CP._millimetres(0.9004) == 900 and CP._millimetres(0.9006) == 901


# --- remis przy minimum: czy WYBRANY INDEKS jedzie dalej ---------------------
#
# Klasa z `reports/mutation-triage-clearance.md`: dziewięć mutacji `<` -> `<=`
# (albo `>` -> `>=`) w wyborze minimum. Przy remisie obie gałęzie dają tę samą
# WARTOŚĆ i różnią się wybranym INDEKSEM, więc pytanie „czy to usterka" jest
# pytaniem, czy indeks jedzie dalej do wyjścia. Odpowiedź jest różna w różnych
# miejscach tego modułu i została ZMIERZONA, nie odczytana z kodu — pomiary stoją
# w docstringach niżej i w `reports/mutation-triage-clearance.md`.
#
# W remis się na ogół NIE WPADA losowo: 200 000 losowych punktów w profilu
# `box_double` trafiło w remis półpłaszczyzn DOKŁADNIE ZERO razy, a wystarczy
# kwadrat, żeby trafiać w 25 % przypadków. Każde wejście niżej jest więc
# SKONSTRUOWANE pod konkretny remis, a nie wylosowane.

def test_clearance_profile_a_tie_between_planes_picks_the_first_edge_in_ring_order():
    """Remis półpłaszczyzn zmienia ETYKIETĘ wiążącej krawędzi, a ta jedzie do raportu.

    Środek kwadratu jest równo odległy od wszystkich czterech krawędzi. Wartość luzu
    jest wtedy niezależna od wyboru, ale `bound_by` — nie: to ona odpowiada w raporcie
    na pytanie „co ogranicza skrajnię w tym miejscu", i wchodzi do
    `statistics()["bound_by_counts"]` oraz do każdego wpisu `critical_places`.

    Zmierzone: mutacja `value < best` -> `<=` zamienia `podłoga` na `ściana` przy
    identycznej wartości 1,0. Na 200 000 losowych punktów w kwadracie remis wypadł
    50 023 razy i etykieta różniła się we WSZYSTKICH 50 023; w profilu `box_double`
    remis nie wypadł ANI RAZU, więc samo próbkowanie orzekłoby tu równoważność.
    """
    square = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
    planes = CP.halfplanes(square)
    values = [nx * 0.0 + ny * 0.0 - c for nx, ny, c, _label in planes]
    assert values.count(min(values)) == 4, ("remis nie zaszedł", values)

    clearance, label = CP.clearance_in_planes(planes, 0.0, 0.0)
    assert clearance == 1.0, clearance
    assert label == planes[0][3] == CP.FLOOR, (label, planes[0][3])

    # Kontrola negatywna: bez remisu wygrywa krawędź NAJBLIŻSZA, nie pierwsza.
    blisko_stropu = CP.clearance_in_planes(planes, 0.0, 0.5)
    assert blisko_stropu == (0.5, CP.ROOF), blisko_stropu


def test_clearance_profile_a_tie_between_frames_keeps_the_earlier_frame():
    """Wierzchołek DOKŁADNIE w połowie między dwiema ramkami — wygrywa wcześniejsza.

    `nearest_frame` zwraca INDEKS, więc tu remis jest wprost wynikiem funkcji.
    Zmierzone: dla punktu (2,5; 0; 0) na osi o pierścieniach co 5 m odległość wzdłuż
    stycznej do ramki 0 i do ramki 1 wynosi 2,5 — równe CO DO BITU. Oryginał zwraca
    0, mutant `<=` zwraca 1. Na 50 000 losowych punktów remis wypadł 9 935 razy
    i indeks różnił się we wszystkich 9 935.
    """
    points = _straight()
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    midpoint = (2.5, 0.0, 0.0)

    do_zera = abs(SW.dot(SW.sub(midpoint, frames[0][0]), frames[0][1]))
    do_jedynki = abs(SW.dot(SW.sub(midpoint, frames[1][0]), frames[1][1]))
    assert do_zera == do_jedynki == 2.5, (do_zera, do_jedynki)

    assert CP.nearest_frame(frames, stations, midpoint, hint_m=2.5) == 0

    # Kontrola negatywna: o włos bliżej drugiej ramki i wybór ma się przesunąć.
    assert CP.nearest_frame(frames, stations, (2.6, 0.0, 0.0), hint_m=2.6) == 1
    assert CP.nearest_frame(frames, stations, (2.4, 0.0, 0.0), hint_m=2.4) == 0


def test_clearance_profile_a_tie_in_the_worst_candidate_keeps_the_first_vertex():
    """Symetryczna bryła na prostej: luz minimalny mają DZIESIĄTKI wierzchołków.

    Wartość minimum jest wtedy jedna, ale `chainage_m`, `lateral_m` i `object`
    opisują KONKRETNY punkt styku i trafiają do `statistics()["min_at"]` oraz do
    `critical_places`. Zmierzone: mutacja `clearance < best[...]` -> `<=` przesuwa
    zgłoszony punkt styku z chainage 100,0 na 115,0 i z lateral +1,35 na −1,35, przy
    luzie identycznym co do bitu (1,1 m). Raport wskazywałby wtedy inny koniec składu.
    """
    points = _straight()
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    reduced = CP.reduce_bodies([_box_body("b", 0.0, 15.0)])

    trafienia = []

    def collector(chainage, lateral, vertical):
        trafienia.append((chainage, lateral, vertical,
                          CP.clearance_in_planes(PLANES, lateral, vertical)[0]))

    record = CP.measure_position(points, frames, stations, PLANES, reduced, 100.0, 0.0,
                                 collector=collector)
    najmniejszy = min(t[3] for t in trafienia)
    assert record["clearance_m"] == najmniejszy
    assert sum(1 for t in trafienia if t[3] == najmniejszy) > 1, (
        "remis nie zaszedł — test nie sprawdza tego, co ma sprawdzać")

    assert record["chainage_m"] == 100.0, record["chainage_m"]
    assert record["lateral_m"] == 1.35, record["lateral_m"]


def test_clearance_profile_a_tie_in_the_naive_measurement_keeps_the_first_vertex():
    """Ta sama konwencja w przebiegu naiwnym — inaczej `--verify-full` porównywałby
    dwa różne punkty styku i zgłaszałby rozjazd tam, gdzie go nie ma.

    Zmierzone: mutacja `clearance < best[...]` -> `<=` w `measure_position_naive`
    przesuwa chainage z 100,0 na 115,0 i lateral z +1,35 na −1,35, przy tym samym
    luzie 1,1 m.
    """
    points = _straight()
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    record = CP.measure_position_naive(points, frames, stations, BOX,
                                       [_box_body("b", 0.0, 15.0)], 100.0, 0.0)
    assert record["chainage_m"] == 100.0, record["chainage_m"]
    assert record["lateral_m"] == 1.35, record["lateral_m"]

    zgodny = CP.measure_position(points, frames, stations, PLANES,
                                 CP.reduce_bodies([_box_body("b", 0.0, 15.0)]),
                                 100.0, 0.0)
    assert zgodny["chainage_m"] == record["chainage_m"]
    assert zgodny["lateral_m"] == record["lateral_m"]


def test_clearance_profile_a_tie_between_stations_names_the_earlier_one():
    """Punkt DOKŁADNIE w połowie między stacjami — raport ma podać jedną, nie losową.

    `nearest_station` wchodzi wprost w każdy wpis `critical_places`, więc remis
    zmienia NAZWĘ w raporcie. Zmierzone: mutacja `distance < best[1]` -> `<=`
    zamienia stację „A" na „B" przy identycznej odległości 100 m; na 50 000 losowych
    kilometraży remis wypadł 276 razy i nazwa różniła się we wszystkich 276.
    """
    doc = [{"name": "A", "chainage_m": 100.0}, {"name": "B", "chainage_m": 300.0}]
    remis = CP.nearest_station(doc, 200.0)
    assert remis["distance_m"] == 100.0, remis
    assert remis["name"] == "A", remis

    # Kontrola negatywna po obu stronach remisu.
    assert CP.nearest_station(doc, 199.0)["name"] == "A"
    assert CP.nearest_station(doc, 201.0)["name"] == "B"


def test_clearance_profile_a_tie_in_the_minimum_radius_keeps_the_first_chainage():
    """Oś o stałym promieniu: KAŻDY dopuszczalny kilometraż daje ten sam promień.

    Zygzak z odcinków (3, 4) ma długość odcinka DOKŁADNIE 5,0, więc kilometraże są
    całkowite i `point_at` na kilometrażu +/- 5 m trafia w węzeł bez interpolacji.
    Wszystkie pięć promieni wychodzi wtedy 3,125 CO DO BITU.

    Zmierzone: mutacja `radius < best[1]` -> `<=` przesuwa zgłoszony kilometraż
    z 5,0 na 25,0. Ta sama liczba promienia, inne MIEJSCE na trasie — a to właśnie
    to miejsce jedzie do raportu jako „najciaśniejszy łuk".
    """
    zigzag = [(0.0, 0.0, 0.0), (3.0, 4.0, 0.0), (6.0, 0.0, 0.0), (9.0, 4.0, 0.0),
              (12.0, 0.0, 0.0), (15.0, 4.0, 0.0), (18.0, 0.0, 0.0)]
    stations = SW.chainages(zigzag)
    assert stations == [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0], stations

    promienie = []
    for index, station in enumerate(stations):
        if station < 5.0 or station > 25.0:
            continue
        before = CP.point_at(zigzag, stations, station - 5.0)
        after = CP.point_at(zigzag, stations, station + 5.0)
        promienie.append(PL._circumradius(before[:2], zigzag[index][:2], after[:2]))
    assert promienie == [3.125] * 5, promienie

    assert CP.min_radius_on_chord(zigzag, stations, 10.0) == (5.0, 3.125)


def test_clearance_profile_a_tie_in_the_envelope_clearance_keeps_the_first_vertex():
    """Obrys symetryczny wobec profilu: dwa wierzchołki mają ten sam, najgorszy luz.

    `envelope_clearance` zwraca nie tylko liczbę, ale i `where` — pierścień i punkt,
    w którym obwiednia jest najciaśniejsza. Zmierzone: mutacja `value < best` -> `<=`
    zamienia `lateral_m` z +1,0 na −1,0 przy luzie identycznym co do bitu.
    """
    polygon = [(-1.0, 1.0), (1.0, 1.0), (1.0, 3.0), (-1.0, 3.0)]
    luzy = [CP.clearance_in_planes(PLANES, lateral, vertical)[0]
            for lateral, vertical in polygon]
    assert luzy.count(min(luzy)) == 2, ("remis nie zaszedł", luzy)

    best, where = CP.envelope_clearance([(0, polygon)], PLANES)
    assert best == min(luzy)
    assert where["lateral_m"] == 1.0, where
    assert where["ring"] == 0

    # Kontrola negatywna: obrys przesunięty w bok ma jedno, nie dwa najgorsze miejsca.
    przesuniety = [(x + 0.5, y) for x, y in polygon]
    _b, gdzie = CP.envelope_clearance([(0, przesuniety)], PLANES)
    assert gdzie["lateral_m"] == 1.5, gdzie


def test_clearance_profile_a_tie_between_frames_of_a_vertex_is_measured_equivalence():
    """Remis, który NIE zmienia wyjścia — i to jest zmierzone, nie założone.

    Wybór ramki dla pojedynczego wierzchołka (`along < closest` w `measure_position`)
    remisuje, gdy wierzchołek jest równo odległy od dwóch ramek wzdłuż stycznej.
    Trafień w ten remis jest DUŻO: 2 480 na osi prostej w 400 pozycjach, 854
    w przeszukaniu osi łamanych. Wyjście różni się jednak najwyżej o
    **8,88e-16 m** — dziesięć rzędów PONIŻEJ mikrometra, w którym `statistics`
    zapisuje minimum, i trzynaście poniżej milimetra progów.

    Powód jest algebraiczny i też zmierzony: na odcinku prostym `band_coefficients`
    dwóch sąsiednich ramek dają IDENTYCZNE chainage, lateral i vertical (różnica 0,0
    na 15 porównaniach), bo przesunięcie początku ramki wzdłuż stycznej znosi się
    z przyrostem kilometrażu. Ten test przybija właśnie tę własność — nie jest
    zabójcą mutacji i nie udaje, że nim jest.
    """
    points = _straight()
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    place = PL.place_spans(points, stations, 100.0, [(0.0, 15.0)], 0.0)[0]

    odniesienie = CP.band_coefficients(place, frames[20], stations[20])
    for index in (19, 20, 21):
        coefficients = CP.band_coefficients(place, frames[index], stations[index])
        for local in ((0.0, 1.35, 3.6), (7.5, -1.35, 0.95), (15.0, 0.0, 2.0)):
            mam = tuple(c[0] + c[1] * local[0] + c[2] * local[1] + c[3] * local[2]
                        for c in coefficients)
            chce = tuple(c[0] + c[1] * local[0] + c[2] * local[1] + c[3] * local[2]
                         for c in odniesienie)
            assert mam == chce, (index, local, mam, chce)


def test_clearance_profile_a_tie_in_the_envelope_height_is_a_plain_equivalence():
    """`if value > row[slot]: row[slot] = value` — przy remisie podstawia TO SAMO.

    Tu remisu nie trzeba szukać: przy `value == row[slot]` obie gałęzie kończą się
    tą samą liczbą w tym samym gnieździe, bo gałąź `>=` przypisuje wartość równą tej,
    która już tam stoi. Żaden indeks się nie wybiera, więc nie ma czego zgubić.
    Zmierzone: 40 001 remisów `value == row[slot]` na 200 000 losowych par, po
    4 000 próbkach `heights` i `rings()` identyczne, a próbka podana DWA RAZY daje
    ten sam słownik wysokości.
    """
    stations = SW.chainages(_straight(100.0, 5.0))

    raz = CP.SweptEnvelope(stations, 0.0, 100.0)
    raz.add(50.0, 1.0, 2.0)
    dwa = CP.SweptEnvelope(stations, 0.0, 100.0)
    dwa.add(50.0, 1.0, 2.0)
    dwa.add(50.0, 1.0, 2.0)
    assert raz.heights == dwa.heights, "powtórzona próbka zmieniła wysokości podparcia"
    assert dwa.samples == 2 and raz.samples == 1

    # Kontrola negatywna: próbka WIĘKSZA musi wysokość podnieść.
    dwa.add(50.0, 1.5, 2.0)
    assert dwa.heights != raz.heights


# --- tolerancje numeryczne: czy próg jest OSIĄGALNY --------------------------
#
# Raport triażu klasyfikował te jedenaście pozycji jako „równoważne w dziedzinie"
# BEZ POMIARU. Pomiar pokazał, że klasyfikacja była w części nieprawdziwa: pięć
# progów jest osiągalnych DOKŁADNIE, i to wejściem, które nie jest absurdalne —
# bo `coverage_gaps`, `support_polygon` i `envelope_contains` są funkcjami czystymi,
# którym próg podaje się wprost na wejściu.
#
# Ta klasa BYŁA też miejscem, w którym `docs/24` pozycja 6 się potwierdzała:
# `step + 1e-6` jest reprezentowalne dokładnie TYLKO przy podstawie zero. Właściciel
# rozstrzygnął tę pozycję na milimetry całkowite, więc trzy testy poniżej są PRZEPISANE,
# nie dopisane obok — i przypinają teraz własność ODWROTNĄ: granica `coverage_gaps`
# wypada w tym samym miejscu przy KAŻDEJ podstawie i właśnie to da się zmierzyć.

def test_clearance_profile_station_boundary_matches_the_half_open_block_rule():
    """Punkt na kilometrażu stacji trafia tam, gdzie trafiłby w bloku `[start, end)`.

    Pozycja 8 `docs/24` twierdziła, że te dwie konwencje są PRZECIWNE. Nie są, i to
    była moja pomyłka w odczycie `docs/15`. Ten test przypina zgodność, bo dokument
    poprawiony bez testu to znów zdanie, którego nic nie porównuje — a rozjechać może
    się każda ze stron osobno.

    Reguła bloku, `src/Sim/Signalling/Block.cs`:

        public bool Contains(double chainageM) => chainageM >= StartM && chainageM < EndM;

    Test nie czyta C# — odtwarza tę regułę wprost i żąda, żeby `between_stations`
    wskazywało ten sam przedział. Gdyby ktoś zmienił `Block.Contains` na domknięty
    z prawej, ten test tego NIE zauważy; to pilnuje `tests/Sim.Tests`. Tutaj pilnowana
    jest strona pythonowa i sama reguła zapisana jawnie.
    """
    stacje = [{"name": "A", "chainage_m": 0.0},
              {"name": "B", "chainage_m": 509.73},
              {"name": "C", "chainage_m": 1451.9}]

    def blok_zawierajacy(chainage):
        """Który odcinek międzystacyjny zawiera chainage przy konwencji [start, end)."""
        for i in range(len(stacje) - 1):
            start, end = stacje[i]["chainage_m"], stacje[i + 1]["chainage_m"]
            if chainage >= start and chainage < end:
                return stacje[i]["name"]
        return stacje[-1]["name"]

    for stacja in stacje:
        c = float(stacja["chainage_m"])
        para = CP.between_stations(stacje, c)
        # `after` to stacja, którą punkt ma ZA sobą, czyli początek jego przedziału.
        assert para["after"] == blok_zawierajacy(c), (c, para, blok_zawierajacy(c))

    # I kontrola negatywna: milimikron PRZED granicą należy już do przedziału
    # poprzedniego — po obu stronach jednakowo. Bez tej połowy test przechodziłby
    # także dla konwencji domkniętej obustronnie.
    for stacja in stacje[1:]:
        c = float(stacja["chainage_m"]) - 1e-9
        assert CP.between_stations(stacje, c)["after"] == blok_zawierajacy(c), c
    assert CP.between_stations(stacje, 509.73 - 1e-9)["after"] == "A"
    assert CP.between_stations(stacje, 509.73)["after"] == "B"


def test_clearance_profile_convexity_eps_sits_between_noise_and_the_real_profiles():
    """`CONVEXITY_EPS` ma zmierzony zapas z DWÓCH stron, i to jest jego uzasadnienie.

    Pozycja 11 `docs/24`: pytanie nie było o wartość, tylko o to, że nie wiadomo,
    skąd się wzięła. Zmierzone i przypięte tutaj, żeby uzasadnienie było wynikiem,
    a nie akapitem:

    Od góry — najmniejszy prawdziwy `|turn|` na trzech profilach `profiles.py`:
    `bore_single` 6,06e-02 (6,1e7 x EPS), `box_double` 3,025 (3,0e9 x), `station`
    4,64 (4,6e9 x).

    Od dołu — szum: obrys we współrzędnych lokalnych daje dryf DOKŁADNIE 0,0;
    przesunięty o 1000 m — 1,3e-12 (0,0013 x EPS); o 10^6 m — 1,3e-09 (1,33 x EPS).
    Lambert 72 dla Brukseli to ~1,5e5 m, czyli ~0,01 x EPS.
    """
    najmniejsze = {}
    for nazwa in ("box_double", "bore_single", "station"):
        ring = PR.profile_points(nazwa)
        n = len(ring)
        zakrety = []
        for i in range(n):
            ax, ay = ring[i]
            bx, by = ring[(i + 1) % n]
            cx, cy = ring[(i + 2) % n]
            zakrety.append((bx - ax) * (cy - by) - (by - ay) * (cx - bx))
        najmniejsze[nazwa] = min(abs(z) for z in zakrety if z != 0.0)

    # Od góry: każdy prawdziwy profil stoi co najmniej 10^6 razy nad progiem.
    for nazwa, wartosc in najmniejsze.items():
        assert wartosc / CP.CONVEXITY_EPS > 1e6, (nazwa, wartosc)
    assert abs(najmniejsze["bore_single"] - 0.0606026) < 1e-7, najmniejsze["bore_single"]

    # Od dołu: przesunięcie do skali Lamberta zostawia szum PONIŻEJ progu.
    ring = PR.profile_points("station")
    n = len(ring)

    def zakrety_po_przesunieciu(shift):
        out = []
        for i in range(n):
            ax, ay = ring[i][0] + shift, ring[i][1] + shift
            bx, by = ring[(i + 1) % n][0] + shift, ring[(i + 1) % n][1] + shift
            cx, cy = ring[(i + 2) % n][0] + shift, ring[(i + 2) % n][1] + shift
            out.append((bx - ax) * (cy - by) - (by - ay) * (cx - bx))
        return out

    bazowe = zakrety_po_przesunieciu(0.0)
    dryf_lambert = max(abs(a - b) for a, b in
                       zip(bazowe, zakrety_po_przesunieciu(1.5e5)))
    assert dryf_lambert < CP.CONVEXITY_EPS, dryf_lambert

    # Kontrola po drugiej stronie: przy 10^6 m szum PRZEKRACZA próg, więc próg nie
    # jest dowolnie mały — gdyby ta asercja padła, znaczyłoby to, że zapas od dołu
    # jest większy, niż mierzę, i akapit w dokumencie byłby przesadnie ostrożny.
    dryf_milion = max(abs(a - b) for a, b in
                      zip(bazowe, zakrety_po_przesunieciu(1e6)))
    assert dryf_milion > CP.CONVEXITY_EPS, dryf_milion


def test_clearance_profile_refine_band_is_not_a_reserve_over_the_measured_gain():
    """Pasmo 50 mm NIE jest zapasem nad zyskiem 3,194 mm — przeciwnie, jest blisko dna.

    Pozycja 10 `docs/24` mówiła, że pasmo jest „z zapasem, 15 razy większe od zysku".
    Zmierzone na pakiecie A, tor 1: przy 10 mm dołek 0,899948 m NIE zostaje znaleziony
    i raport pokazuje 0,900821 m, czyli o 0,873 mm za wysoko.

    Pomiaru na pakiecie nie da się powtórzyć w teście jednostkowym (potrzebuje Blendera
    i tunelu), więc test przypina to, co da się przypiąć bez silnika: że pasmo wybiera
    dołki, których jest WIĘCEJ niż samo minimum, i że zawężenie do 10 mm zmienia wybór.
    Gdyby ktoś zawęził stałą „bo jest zapas", ten test padnie razem z akapitem.
    """
    assert CP.DEFAULT_REFINE_BAND_M == 0.050

    # Rekordy odtwarzające rozkład z pakietu: jedno minimum i kilka pozycji nad nim
    # w odległościach, które 50 mm łapie, a 10 mm już nie.
    records = [{"start_m": 0.0, "clearance_m": 0.9000},
               {"start_m": 5.0, "clearance_m": 0.9200},
               {"start_m": 200.0, "clearance_m": 0.9450},
               {"start_m": 400.0, "clearance_m": 1.1000}]

    szerokie = CP.refine_windows(records, 5.0, band_m=0.050)
    waskie = CP.refine_windows(records, 5.0, band_m=0.010)
    assert len(szerokie) > len(waskie), (szerokie, waskie)
    assert len(waskie) == 1, waskie

    # 0,9450 wpada dopiero w pasmo 45 mm — czyli 50 mm bierze trzy dołki, 10 mm jeden.
    assert len(CP.refine_windows(records, 5.0, band_m=0.045)) == len(szerokie)


def test_clearance_profile_cluster_gap_follows_the_scan_step():
    """Odstęp grupowania jest KROTNOŚCIĄ kroku skanu, nie liczbą wpisaną z ręki.

    Pozycja 5 `docs/24`: poprzedni komentarz uzasadniał 25,0 m cięciwą najdłuższej
    bryły M7 (podaną jako 15,12 m; zmierzona to 15,1167 m). Pomiar na pakiecie A
    pokazał, że wielkość, od której ta stała naprawdę zależy, to GĘSTOŚĆ PRÓBKOWANIA:
    największy odstęp między sąsiednimi rekordami pod progiem WEWNĄTRZ jednego miejsca
    wyniósł 5,01 m — czyli krok skanu — a luki dzielące różne miejsca miały 844,5 m
    i 1524,6 m.

    Ten test pilnuje samego wyprowadzenia. Gdyby ktoś wpisał tu z powrotem stałą 25,0,
    `cluster_gap_m(2.0)` przestałoby zwracać 10,0 i test padnie — a to jest dokładnie
    ta usterka, którą pozycja 5 opisuje: opis nie jest wynikiem, więc nic go nie
    porównuje.
    """
    assert CP.CRITICAL_CLUSTER_GAP_M == CP.cluster_gap_m(CP.DEFAULT_STEP_M)
    assert CP.cluster_gap_m(5.0) == 25.0
    assert CP.cluster_gap_m(2.0) == 10.0
    assert CP.cluster_gap_m(25.0) == 125.0

    # Krok niedodatni jest odmową, tak samo jak w `scan_positions` — inaczej odstęp
    # zero scaliłby wszystko w jeden wpis i raport zgłosiłby jedno miejsce na trasie.
    for zly in (0.0, -5.0):
        try:
            CP.cluster_gap_m(zly)
        except ValueError as exc:
            assert "dodatni" in str(exc), str(exc)
        else:
            raise AssertionError(f"krok {zly} przeszedł")


def test_clearance_profile_cluster_gap_must_stay_above_the_scan_step():
    """Odstęp NIE MOŻE być równy krokowi — i to jest zmierzona przesłanka wyboru.

    Zmierzone na pakiecie A, tor 1, próg 1,000 m: przy odstępie 5,0 m trzy miejsca
    rozpadają się na PIĘĆ, bo odstępy 5,01 m przestają się mieścić. Przy 15,0985 m
    (cięciwa bryły), 15,667 m (cięciwa nominalna) i 25,0 m — trzy miejsca, identycznie.
    Krotność 5 daje więc pięciokrotny zapas nad krokiem, a nie „nieco więcej niż
    cięciwa pudła".

    Test odtwarza to na wejściu skonstruowanym, nie na pakiecie: dwa rekordy o odstępie
    chainage nieco większym od kroku. W taki próg się nie wpada losowo — trzeba go
    zbudować (ta sama lekcja co przy `CONVEXITY_EPS`, pozycja 12).
    """
    assert CP.CLUSTER_GAP_STEPS >= 2, CP.CLUSTER_GAP_STEPS

    krok = 5.0
    records = [{"chainage_m": 100.0, "clearance_m": 0.95, "start_m": 0.0,
                "object": "M7_car_6", "bound_by": "ściana"},
               {"chainage_m": 100.0 + krok + 0.01, "clearance_m": 0.96, "start_m": 5.0,
                "object": "M7_car_6", "bound_by": "ściana"}]

    # Przy odstępie równym krokowi te dwa rekordy to DWA miejsca — czyli rozpad.
    rozpad = CP.critical_places(records, 1.000, [], gap_m=krok)
    assert len(rozpad) == 2, rozpad

    # Przy wyprowadzonym odstępie — jedno, i tego pomiar wymaga.
    razem = CP.critical_places(records, 1.000, [], gap_m=CP.cluster_gap_m(krok))
    assert len(razem) == 1, razem
    assert razem[0]["positions"] == 2, razem


def test_clearance_profile_coverage_first_position_boundary_sits_below_half_a_millimetre():
    """Pierwsza pozycja: 0,4 mm przechodzi, 0,6 mm jest zgłaszane.

    Granica wypada poniżej połowy milimetra, bo `_millimetres` zaokrągla do
    najbliższego. Test celuje 0,1 mm po każdej stronie, a nie DOKŁADNIE w połowę —
    powód jest zmierzony i ma własny test poniżej
    (`..._exactly_half_a_millimetre_depends_on_parity`).
    """
    assert CP._millimetres(0.0004) == 0
    assert CP._millimetres(0.0006) == 1

    na_progu = [{"start_m": 0.0004, "clearance_m": 1.0},
                {"start_m": 5.0004, "clearance_m": 1.0}]
    assert CP.coverage_gaps(na_progu, 0.0, 5.0004, 5.0) == []

    # Kontrola negatywna: 0,2 mm dalej i pierwsza pozycja JEST zgłaszana.
    nad_progiem = [{"start_m": 0.0006, "clearance_m": 1.0},
                   {"start_m": 5.0006, "clearance_m": 1.0}]
    problemy = CP.coverage_gaps(nad_progiem, 0.0, 5.0006, 5.0)
    assert any("pierwsza pozycja" in p for p in problemy), problemy


def test_clearance_profile_coverage_last_position_no_longer_needs_a_zero_base():
    """Ostatnia pozycja: ta sama granica przy podstawie 0 i przy 6700 m.

    Poprzednia wersja tego testu MUSIAŁA kotwiczyć w zerze i mówiła to wprost:
    „różnica dwóch double równa DOKŁADNIE `fl(1e-6)` przy niezerowej podstawie nie
    wychodzi". Ta konieczność zniknęła razem z porównaniem floatów, i dokładnie to
    jest tu przypięte — bo gdyby wróciła, ten test byłby jedynym miejscem, które
    to zauważy.
    """
    assert 5.0 - (5.0 - 1e-6) != 1e-6          # stara pułapka nadal istnieje w floatach

    # Trzy oczekiwane końce zakresu: zero, mała podstawa i realny koniec pakietu A
    # (6686,739 m osi minus 94 m składu). Krok podany szeroko, żeby kontrola dziur
    # nie mieszała się do kontroli końca.
    for oczekiwane in (0.0, 5.0, 6592.739):
        blisko = [{"start_m": 0.0, "clearance_m": 1.0},
                  {"start_m": oczekiwane + 0.0004, "clearance_m": 1.0}]
        problemy = CP.coverage_gaps(blisko, 94.0, oczekiwane + 94.0, 10000.0)
        assert not [x for x in problemy if "ostatnia pozycja" in x], (oczekiwane, problemy)

        dalej = [{"start_m": 0.0, "clearance_m": 1.0},
                 {"start_m": oczekiwane + 0.0006, "clearance_m": 1.0}]
        problemy = CP.coverage_gaps(dalej, 94.0, oczekiwane + 94.0, 10000.0)
        assert [x for x in problemy if "ostatnia pozycja" in x], (oczekiwane, problemy)


def test_clearance_profile_coverage_gap_boundary_is_the_same_at_every_chainage():
    """Granica dziury wypada w TYM SAMYM miejscu przy każdej podstawie — to cała pozycja 6.

    Poprzednia wersja tego testu korzystała z pułapki, którą decyzja usunęła: przy
    `a = 0` różnica `b - a` była równa `step + 1e-6` co do bitu, przy `a = 5` już nie,
    a na 300 000 losowych par w równość trafiło 135 — wszystkie przy podstawie zero.

    Zmierzone po zmianie, ten sam warunek przy trzech podstawach:

        podstawa   przerwa 5,0004 m   przerwa 5,0006 m
             0,0   5000 mm, nie dziura   5001 mm, DZIURA
             5,0   5000 mm, nie dziura   5001 mm, DZIURA
          6700,0   5000 mm, nie dziura   5001 mm, DZIURA

    Nie ma już „strony granicy zależnej od kilometrażu" i nie ma losowego trafiania
    w próg: granicę się KONSTRUUJE, w jednym miejscu, dla każdej podstawy.
    """
    krok = 5.0
    for baza in (0.0, 5.0, 6700.0):
        styczne = [{"start_m": baza, "clearance_m": 1.0},
                   {"start_m": baza + krok + 0.0004, "clearance_m": 1.0}]
        problemy = CP.coverage_gaps(styczne, 0.0, baza + krok + 0.0004, krok)
        assert not [p for p in problemy if "dziura" in p], (baza, problemy)

        # Kontrola negatywna, ta sama podstawa: 0,1 mm dalej JEST dziurą.
        dziura = [{"start_m": baza, "clearance_m": 1.0},
                  {"start_m": baza + krok + 0.0006, "clearance_m": 1.0}]
        problemy = CP.coverage_gaps(dziura, 0.0, baza + krok + 0.0006, krok)
        assert [p for p in problemy if "dziura" in p], (baza, problemy)


def test_clearance_profile_coverage_exactly_half_a_millimetre_depends_on_parity():
    """DOKŁADNIE pół milimetra rozstrzyga się PARZYSTOŚCIĄ licznika, i to trzeba wiedzieć.

    Przejście na milimetry całkowite (decyzja właściciela, pozycja 6 `docs/24`) usuwa
    zależność granicy od kilometrażu — ale nie w jednym punkcie: `round()` w Pythonie
    zaokrągla połowę do liczby PARZYSTEJ, więc `x + 0,5 mm` raz wpada w ten sam
    milimetr, a raz w następny. Zmierzone:

        podstawa      mm      mm(+0,5 mm)   różnica   licznik
             0,0       0            0          0      parzysty
             5,0    5000         5000          0      parzysty
        1500,000 1500000      1500000          0      parzysty
        1500,001 1500001      1500002          1      NIEPARZYSTY
        6592,739 6592739      6592740          1      NIEPARZYSTY
        6592,740 6592740      6592740          0      parzysty

    Ten test istnieje, bo bez niego łatwo napisać w raporcie „granica jest teraz
    dokładna przy każdym kilometrażu" — co jest prawdą o 0,4 i 0,6 mm, a nieprawdą
    o 0,5 mm. Znalazł to MÓJ WŁASNY test poprzedniej wersji, który celował dokładnie
    w połowę i padł na końcu zakresu pakietu A (6592,739 m). Zapisuję ograniczenie,
    a nie tylko obchodzę je doborem liczb.

    Konsekwencja praktyczna jest żadna: chainage w `data/track/` jest zapisany
    z dokładnością do centymetra, więc różnica dokładnie pół milimetra nie powstaje
    z danych — powstaje z testu, który ją skonstruuje.
    """
    for podstawa, oczekiwana_roznica in ((0.0, 0), (5.0, 0), (1500.0, 0),
                                         (1500.001, 1), (6592.739, 1), (6592.740, 0)):
        licznik = CP._millimetres(podstawa)
        roznica = CP._millimetres(podstawa + 0.0005) - licznik
        assert roznica == oczekiwana_roznica, (podstawa, licznik, roznica)
        assert roznica == licznik % 2, (podstawa, licznik, roznica)

    # A 0,4 i 0,6 mm są jednoznaczne przy KAŻDEJ z tych podstaw — to jest ta część,
    # którą decyzja naprawdę kupiła, i dlatego pozostałe testy celują właśnie tam.
    for podstawa in (0.0, 5.0, 1500.0, 1500.001, 6592.739, 6592.740, 6700.0):
        licznik = CP._millimetres(podstawa)
        assert CP._millimetres(podstawa + 0.0004) - licznik == 0, podstawa
        assert CP._millimetres(podstawa + 0.0006) - licznik == 1, podstawa


def test_clearance_profile_support_polygon_skips_a_pair_exactly_at_the_determinant():
    """Wyznacznik DOKŁADNIE równy `1e-12` to para kierunków równoległych — pomijana.

    `support_polygon` przyjmuje kierunki od wołającego (`SweptEnvelope(directions=...)`),
    więc próg jest tu osiągalny wprost: `det((1, 0), (1, 1e-12)) == 1e-12` co do bitu.
    Bez pominięcia dzielenie przez wyznacznik rzędu 1e-12 daje wierzchołek oddalony
    o 1e12 jednostek i obrys przestaje być obrysem.

    Zmierzone: przy `det == 1e-12` oryginał wierzchołek LICZY (5 wierzchołków), bo
    porównanie jest ostre; mutant `<=` go pomija i zwraca 4. Tak samo przy
    `det == 1,005e-12` mutant progu (`1e-12` -> `1,01e-12`) pomija to, czego oryginał
    nie pomija. Żadne `support_directions(3..64)` nie produkuje takiego wyznacznika
    (0 trafień), więc ta bramka istnieje wyłącznie dla kierunków podanych z zewnątrz.
    """
    wysokosci = [2.0, 2.0, 3.0, 2.0, 1.0]

    na_progu = [(1.0, 0.0), (1.0, 1e-12), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)]
    det = na_progu[0][0] * na_progu[1][1] - na_progu[0][1] * na_progu[1][0]
    assert det == 1e-12, det
    assert len(CP.support_polygon(na_progu, wysokosci)) == 5, "próg pominął parę na progu"

    nad_progiem = [(1.0, 0.0), (1.0, 1.005e-12), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)]
    assert len(CP.support_polygon(nad_progiem, wysokosci)) == 5, (
        "para powyżej progu została pominięta")

    # Kontrola negatywna: wyznacznik PONIŻEJ progu musi zostać pominięty, inaczej
    # rozluźnienie porównania zamieniłoby się w brak porównania.
    pod_progiem = [(1.0, 0.0), (1.0, 9.9e-13), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)]
    assert len(CP.support_polygon(pod_progiem, wysokosci)) == 4, (
        "para kierunków równoległych przeszła jako wierzchołek")


def test_clearance_profile_envelope_contains_accepts_a_sample_exactly_at_the_tolerance():
    """Próbka DOKŁADNIE `tolerance_m` poza obrysem jeszcze się mieści.

    Próg jest osiągalny co do bitu, ale nie dla każdej tolerancji — i to jest ta sama
    obserwacja, co w `docs/24` pozycji 6. Zmierzone na kwadracie [-1; 1]:

        punkt (1 + 2**-20, 0) -> odległość -9.5367431640625e-07  == -2**-20  : True
        punkt (1 + 1e-6,   0) -> odległość -9.999999999177334e-07 == -1e-6  : False

    Potęga dwójki trafia w granicę dokładnie, `1e-6` nie trafia nigdy — na 200 000
    losowych punktów odległość wyszła równa `-1e-6` ZERO razy. Mutacja `<` -> `<=`
    liczy przy tolerancji `2**-20` obie próbki jako leżące poza obwiednią.
    """
    tolerancja = 2.0 ** -20
    kwadrat = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
    assert PL.distance_to_boundary(kwadrat, 1.0 + tolerancja, 0.0) == -tolerancja
    assert PL.distance_to_boundary(kwadrat, 1.0 + 1e-6, 0.0) != -1e-6

    stations = SW.chainages(_straight(50.0, 5.0))
    envelope = CP.SweptEnvelope(stations, 0.0, 50.0)
    rings = [(index, kwadrat) for index in range(len(stations))]

    poza, sprawdzone = CP.envelope_contains(envelope, rings, [(25.0, 1.0 + tolerancja, 0.0)],
                                            tolerance_m=tolerancja)
    assert sprawdzone == 2, sprawdzone
    assert poza == 0, "próbka dokładnie na tolerancji zgłoszona jako poza obwiednią"

    # Kontrola negatywna: dwa razy dalej i próbka MUSI wypaść poza.
    poza, sprawdzone = CP.envelope_contains(envelope, rings, [(25.0, 1.0 + 2.0 ** -19, 0.0)],
                                            tolerance_m=tolerancja)
    assert (poza, sprawdzone) == (2, 2), (poza, sprawdzone)


def test_clearance_profile_the_axis_tail_tolerance_is_measured_not_reachable():
    """`abs(out[-1] - last) > 1e-9` — próg nieosiągalny inaczej niż osią nanometrową.

    Zmierzone, a nie założone. Ogon jest różnicą `last` i `round(count * step, 6)`.
    Żeby wyszła DOKŁADNIE `fl(1e-9)`, `fl(1e-9)` musiałby być wielokrotnością odstępu
    double przy `out[-1]`, a nie jest:

        (0,5   + 1e-9) - 0,5   = 9.999999717180685e-10   != 1e-9
        (94,0  + 1e-9) - 94,0  = 1.0000036354540498e-09  != 1e-9
        (6700  + 1e-9) - 6700  = 1.000444171950221e-09   != 1e-9

    Zostaje `out[-1] == 0.0`, czyli `count == 0`, czyli `last < step` — i wtedy
    `last` sam musi być równy `fl(1e-9)`. Jedyne takie wejście to oś rzędu nanometra:
    `scan_positions(2e-9, 1e-9, 1.0)` daje `[0.0]`, a mutant `>=` `[0.0, 0.0]`.
    Na 300 000 losowych trójek (oś 200-7000 m, skład 15-94 m, krok 0,25-5 m) w próg
    trafiło ZERO. Ta mutacja zostaje więc jako równoważna w dziedzinie, a test pilnuje
    tego, po co próg stoi: żeby ogon osi był pokryty i NIE zdublowany.
    """
    assert (94.0 + 1e-9) - 94.0 != 1e-9
    assert (6700.0 + 1e-9) - 6700.0 != 1e-9

    dzieli = CP.scan_positions(1000.0, 94.0, 5.0)
    assert dzieli[-1] == 906.0 and dzieli[-2] == 905.0, dzieli[-3:]
    assert len(dzieli) == len(set(dzieli)), "ogon osi zdublowany"

    nie_dzieli = CP.scan_positions(1000.5, 94.0, 5.0)
    assert nie_dzieli[-1] == 906.5 and nie_dzieli[-2] == 905.0, nie_dzieli[-3:]
    assert len(nie_dzieli) == len(set(nie_dzieli))


def test_clearance_profile_the_zero_chord_tolerance_is_measured_equivalence():
    """`SW.norm(chord) < 1e-9` — próg trafialny, ale po obu stronach to samo zero.

    Zmierzone. Norma cięciwy wychodzi DOKŁADNIE `1e-9` na osi prostej (cięciwa od 0
    do 1e-9 daje wektor (1e-9, 0, 0)), i wtedy oryginał zwraca 0,0 przez strażnika,
    a mutant `<=` zwraca 0,0 licząc — ta sama liczba. Na łuku norma w próg nie trafia
    ani razu (0 na 200 000 par kilometraży), bo `frame_at` interpoluje.

    Ścieżka bez strażnika daje na cięciwie tego rzędu odchylenie 1,8e-15 m — czyli
    2 femtometry — przy cięciwie bryły M7 wynoszącej 15,12 m. Mutacja progu
    (`1e-9` -> `1,01e-9`) rozróżnia się właśnie tam i dlatego zostaje jako
    równoważna w dziedzinie. Test przybija samo zejście do zera i granicę cięciwy
    zerowej, bo TO jest powód, dla którego ten strażnik stoi.
    """
    points = _straight(50.0, 5.0)
    stations = SW.chainages(points)
    head, _i, _t = PL.frame_at(points, stations, 0.0)
    tail, _j, _u = PL.frame_at(points, stations, 1e-9)
    assert SW.norm(SW.sub(tail, head)) == 1e-9

    assert CP.chord_deviation_m(points, stations, 0.0, 1e-9) == 0.0
    assert CP.chord_deviation_m(points, stations, 12.0, 12.0) == 0.0, (
        "cięciwa zerowa musi zejść przez strażnika, a nie przez `unit` wektora zerowego")

    # Kontrola negatywna: na łuku prawdziwa cięciwa daje odchylenie NIEzerowe.
    arc = _arc(120.0)
    assert CP.chord_deviation_m(arc, SW.chainages(arc), 0.0, 15.12) > 0.02


# --- reszta ocalałych: pozycja po pozycji ------------------------------------

def test_clearance_profile_hull_drops_a_collinear_point_on_the_lower_chain():
    """Punkt DOKŁADNIE na krawędzi otoczki nie jest wierzchołkiem otoczki.

    `turn(...) <= 0.0` zdejmuje wierzchołek o zerowym zakręcie; mutacja `<` go
    ZOSTAWIA. Skutek nie jest kosmetyczny: `halfplanes` liczy normalną z każdej
    kolejnej krawędzi, więc współliniowy wierzchołek dokłada półpłaszczyznę
    o tej samej normalnej, a `candidate_bands` niesie wierzchołek, który nie może
    być ekstremalny w żadnym kierunku — czyli dokładnie to, co redukcja ma odsiać.

    Zmierzone: na 200 000 losowych zbiorów na siatce 4x4 trójka o zakręcie DOKŁADNIE
    zero wypadła 49 621 razy, a otoczka różniła się w 22 482. Dolny łańcuch rozstrzyga
    wejście współliniowe na DOLE — na tym samym wejściu mutacja górnego łańcucha
    (w. 155) nie zmienia niczego.
    """
    pts = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (1.0, 2.0)]
    assert (1.0 - 0.0) * (0.0 - 0.0) - (0.0 - 0.0) * (2.0 - 0.0) == 0.0
    assert CP.hull_2d(pts) == [(0.0, 0.0), (2.0, 0.0), (1.0, 2.0)]

    # Kontrola negatywna: wierzchołek o zakręcie DODATNIM ma zostać.
    wypukly = [(0.0, 0.0), (1.0, -0.5), (2.0, 0.0), (1.0, 2.0)]
    assert CP.hull_2d(wypukly) == [(0.0, 0.0), (1.0, -0.5), (2.0, 0.0), (1.0, 2.0)]


def test_clearance_profile_hull_keeps_a_lower_vertex_below_one_millimetre_of_turn():
    """Próg zdejmowania wierzchołka jest ZEREM, nie milimetrem — i to jest sprawdzane.

    Mutacja `turn(...) <= 0.0` -> `<= 0.001` spłaszczałaby otoczkę: zdejmowałaby
    wierzchołki o zakręcie dodatnim, ale mniejszym od 0,001. Zakręt to podwojone
    pole trójkąta, więc dla obrysu M7 w metrach 0,001 znaczy 0,5 mm^2 — a otoczka
    ma być otoczką ZBIORU, nie jego przybliżeniem.

    Zmierzone: wierzchołek (1; -0,00025) daje zakręt DOKŁADNIE 0,0005, oryginał go
    zostawia, mutant zdejmuje.
    """
    pts = [(0.0, 0.0), (1.0, -0.00025), (2.0, 0.0), (1.0, 2.0)]
    zakret = (1.0 - 0.0) * (0.0 - 0.0) - (-0.00025 - 0.0) * (2.0 - 0.0)
    assert zakret == 0.0005, zakret
    assert (1.0, -0.00025) in CP.hull_2d(pts), CP.hull_2d(pts)


def test_clearance_profile_hull_drops_a_collinear_point_on_the_upper_chain():
    """To samo dla łańcucha GÓRNEGO — dwa łańcuchy to dwie osobne bramki.

    Zmierzone: wejście współliniowe na GÓRZE zmienia otoczkę pod mutacją w. 155
    i NIE zmienia jej pod mutacją w. 150. Bez obu wejść jedna z dwóch bramek
    zostawałaby nietknięta, a wyglądałoby to na pokrycie.
    """
    pts = [(0.0, 2.0), (1.0, 2.0), (2.0, 2.0), (1.0, 0.0)]
    assert CP.hull_2d(pts) == [(0.0, 2.0), (1.0, 0.0), (2.0, 2.0)]

    gorny = [(0.0, 2.0), (1.0, 2.00025), (2.0, 2.0), (1.0, 0.0)]
    zakret = (1.0 - 2.0) * (2.0 - 2.0) - (2.00025 - 2.0) * (0.0 - 2.0)
    assert 0.0 < zakret < 0.001, zakret
    assert (1.0, 2.00025) in CP.hull_2d(gorny), CP.hull_2d(gorny)


def test_clearance_profile_touching_refine_windows_merge_into_one():
    """Dwa okna, których granice się DOKŁADNIE stykają, to jedno okno.

    Bez scalenia doszlifowanie policzyłoby pozycję granicy dwa razy — raz jako koniec
    pierwszego okna, raz jako początek drugiego — i `coverage_gaps` zobaczyłby
    zdublowaną pozycję. Zmierzone: dołki 8,0 m od siebie przy półoknie 4,0 m dają
    `0,0 + 4,0 == 8,0 - 4,0` co do bitu; oryginał zwraca jedno okno (-4,0; 12,0),
    mutant `<` dwa: (-4,0; 4,0) i (4,0; 12,0).
    """
    records = [{"start_m": 0.0, "clearance_m": 0.5},
               {"start_m": 8.0, "clearance_m": 0.5},
               {"start_m": 40.0, "clearance_m": 9.0}]
    assert 0.0 + 4.0 == 8.0 - 4.0
    assert CP.refine_windows(records, 5.0, half_window_m=4.0) == [(-4.0, 12.0)]

    # Kontrola negatywna: dołki dalej od siebie niż dwa półokna to DWA okna.
    rozlaczne = [{"start_m": 0.0, "clearance_m": 0.5},
                 {"start_m": 8.5, "clearance_m": 0.5},
                 {"start_m": 40.0, "clearance_m": 9.0}]
    assert CP.refine_windows(rozlaczne, 5.0, half_window_m=4.0) == [(-4.0, 4.0), (4.5, 12.5)]


def test_clearance_profile_zero_clearance_is_not_counted_as_negative():
    """`negative_positions` znaczy UJEMNY, a zero nie jest ujemne.

    Ta sama konwencja, którą `below_threshold` ma po decyzji z pozycji 3 `docs/24`:
    klucz nazywa się tak, jak liczy. Mutacja `v < 0.0` -> `<=` liczyłaby styk
    dokładnie na obrysie jako naruszenie, a mutacja progu (`0.0` -> `0.001`)
    liczyłaby jako naruszenie każdy luz poniżej milimetra.

    Zmierzone: luz 0,0 -> oryginał 0, mutant `<=` 1; luz 0,0005 -> oryginał 0,
    mutant 0,001 -> 1.
    """
    zero = CP.statistics([_record(100.0, 0.0), _record(200.0, 1.0)], thresholds=(0.0,))
    assert zero["negative_positions"] == 0, zero["negative_positions"]

    polmilimetra = CP.statistics([_record(100.0, 0.0005), _record(200.0, 1.0)],
                                 thresholds=(0.0,))
    assert polmilimetra["negative_positions"] == 0, polmilimetra["negative_positions"]

    # Kontrola negatywna: milimetr PONIŻEJ zera jest już naruszeniem.
    ujemny = CP.statistics([_record(100.0, -0.001), _record(200.0, 1.0)], thresholds=(0.0,))
    assert ujemny["negative_positions"] == 1, ujemny["negative_positions"]


def test_clearance_profile_min_radius_includes_the_chainage_exactly_at_half_chord():
    """Kilometraż DOKŁADNIE równy połowie cięciwy jeszcze się mierzy.

    Strażnik ma odrzucać kilometraże, dla których cięciwa nie mieści się na osi.
    Przy kilometrażu równym `half` mieści się dokładnie — `point_at(0)` jest końcem
    osi, nie ekstrapolacją. Zmierzone na zygzaku 3-4-5 (kilometraże całkowite):
    oryginał zwraca (5,0; 3,125), mutant `<=` pomija ten kilometraż i zwraca
    (10,0; 3,125), czyli inne MIEJSCE przy tej samej liczbie.
    """
    zigzag = [(0.0, 0.0, 0.0), (3.0, 4.0, 0.0), (6.0, 0.0, 0.0), (9.0, 4.0, 0.0),
              (12.0, 0.0, 0.0), (15.0, 4.0, 0.0), (18.0, 0.0, 0.0)]
    stations = SW.chainages(zigzag)
    assert stations[1] == 5.0 == 10.0 / 2.0
    assert CP.min_radius_on_chord(zigzag, stations, 10.0)[0] == 5.0

    # Kontrola negatywna: przy cięciwie 11 m połowa wynosi 5,5 m, więc kilometraż
    # 5,0 NIE mieści cięciwy i ma zostać pominięty — pierwszym mierzonym jest 10,0.
    assert CP.min_radius_on_chord(zigzag, stations, 11.0)[0] == 10.0


def test_clearance_profile_min_radius_includes_the_last_admissible_chainage():
    """Symetrycznie na drugim końcu: `total - half` jeszcze się mierzy.

    Oś z czterema odcinkami prostymi i dwoma załamaniami na końcu. Trzy pierwsze
    kilometraże dają promień `None` (punkty współliniowe), więc minimum leży na
    OSTATNIM dopuszczalnym kilometrażu i strażnik prawego końca jest jedyną rzeczą,
    która o nim decyduje. Zmierzone: oryginał (25,0; 3,125), mutant `>=`
    (20,0; 7,905694150420948) — inne miejsce I inna liczba.
    """
    points = [(0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (10.0, 0.0, 0.0), (15.0, 0.0, 0.0),
              (20.0, 0.0, 0.0), (24.0, 3.0, 0.0), (20.0, 6.0, 0.0)]
    stations = SW.chainages(points)
    assert stations == [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0], stations

    station, radius = CP.min_radius_on_chord(points, stations, 10.0)
    assert station == 25.0 == stations[-1] - 5.0, station
    assert radius == 3.125, radius


def test_clearance_profile_envelope_rings_include_both_range_ends():
    """Kilometraż DOKŁADNIE na granicy zakresu obwiedni wnosi się do pierścieni.

    `low_m` i `high_m` są granicami zakresu ZAMKNIĘTEGO — inaczej próbki z pierwszej
    i ostatniej mierzonej pozycji przepadałyby i obwiednia miałaby na szwach prążki
    niedomiaru, czyli byłaby MNIEJSZA od składu. Zmierzone na osi co 5 m z zakresem
    [10; 30]: przy chainage 10,0 oryginał daje (1, 2), mutant `<=` — nic; przy 30,0
    oryginał (5, 6), mutant `>=` — nic.
    """
    stations = SW.chainages(_straight(50.0, 5.0))
    envelope = CP.SweptEnvelope(stations, 10.0, 30.0)

    assert envelope.rings_for(10.0) == (1, 2), envelope.rings_for(10.0)
    assert envelope.rings_for(30.0) == (5, 6), envelope.rings_for(30.0)

    # Kontrola negatywna: o milimetr poza zakresem i próbka nie wnosi się nigdzie.
    assert envelope.rings_for(9.999) == ()
    assert envelope.rings_for(30.001) == ()


def test_clearance_profile_envelope_rings_include_the_first_and_last_ring_index():
    """Pierścień o indeksie `first` i o indeksie `last` należą do obwiedni.

    To osobna bramka niż zakres kilometrażu: `first` i `last` są przycięciem do
    ISTNIEJĄCYCH pierścieni osi, a łańcuch `self.first <= r <= self.last` nosi DWIE
    mutacje `<=` -> `<`. Zmierzone na zakresie [12; 28] (first=2, last=6): przy
    chainage 12,0 oryginał daje (2, 3), mutant lewej strony (3,); przy chainage 28,0
    oryginał (5, 6), mutant prawej strony (5,). Zgubiony pierścień to zgubiona
    ćwiartka obrysu na szwie.
    """
    stations = SW.chainages(_straight(50.0, 5.0))
    envelope = CP.SweptEnvelope(stations, 12.0, 28.0)
    assert (envelope.first, envelope.last) == (2, 6), (envelope.first, envelope.last)

    assert envelope.rings_for(12.0) == (2, 3), envelope.rings_for(12.0)
    assert envelope.rings_for(28.0) == (5, 6), envelope.rings_for(28.0)

    # Kontrola negatywna: pierścień PONIŻEJ `first` nadal się nie wnosi.
    waski = CP.SweptEnvelope(stations, 12.0, 13.0)
    assert (waski.first, waski.last) == (2, 3), (waski.first, waski.last)
    assert waski.rings_for(12.5) == (2, 3)
    assert waski.rings_for(12.0) == (2, 3)


def test_clearance_profile_the_hand_rolled_absolute_value_is_measured_equivalence():
    """`if along < 0.0: along = -along` — dwie mutacje, obie zmierzone jako równoważne.

    `<` -> `<=`: przy `along == 0.0` mutant podstawia `-0.0`. `-0.0 == 0.0` jest
    prawdą, a `-0.0 < 0.0` fałszem, więc porównanie `along < closest` zachowuje się
    identycznie, a `along` nigdzie dalej nie jedzie. Zmierzone: `along == 0.0`
    wypadło DOKŁADNIE 1 488 razy w 120 pozycjach na osi prostej i rekord nie
    różnił się ani razu.

    `0.0` -> `0.001`: mutant negowałby każdy `along` poniżej milimetra, a różnica
    wymaga DWÓCH kandydatów bliżej niż milimetr od swoich kilometraży. Kandydaci to
    sąsiednie pierścienie osi, czyli 5 m od siebie — zmierzone: 0 takich par na
    24 800 sprawdzonych wierzchołków. Na osi zdegenerowanej (łuk R = 0,01 m,
    pierścienie co 0,5 mm) różnica pojawia się i wynosi 2,47e-05 m, ale najmniejszy
    dopuszczalny promień osi to `LIMITS["min_radius_m"]` walidatora, czyli **90 m**,
    a pierścienie stoją co 5 m — więc oś zdegenerowana nie przejdzie walidatora.

    Zdanie jest przepisane, a nie dopisane obok (6.B25). Poprzednia wersja powoływała
    się na `MIN_RADIUS_M` „w tym repozytorium" równe 20 m — stałą z
    `tools/blender/clearance.py`, która od swojego pierwszego commita (#50) **nie była
    czytana przez żaden kod**, a tę samą nazwę nosił drugi próg, o innej wartości.
    Argument nie tylko powoływał się na liczbę martwą; powoływał się na **słabszą**,
    niż obowiązuje: 90 m tym bardziej wyklucza zdegenerowany łuk niż 20 m.

    Ten test przybija to, po co ta gałąź stoi: że wybierana jest ramka NAJBLIŻSZA
    wzdłuż stycznej, po obu stronach kilometrażu jednakowo.
    """
    assert -0.0 == 0.0 and not (-0.0 < 0.0)

    points = _arc(150.0)
    stations = SW.chainages(points)
    frames = SW.rmf_frames(points)
    place = PL.place_spans(points, stations, 30.0, [(0.0, 15.0)], 0.0)[0]
    for local_x in (0.0, 3.7, 7.5, 11.3, 15.0):
        world = PL.transform_point(place, (local_x, 0.0, 0.0))
        index = CP.nearest_frame(frames, stations, world, hint_m=30.0 + local_x)
        mine = CP.offsets_in_frame(frames[index], stations[index], world)
        blisko = abs(mine[0] - stations[index])
        for other in (index - 1, index + 1):
            if not 0 <= other < len(frames):
                continue
            dalej = CP.offsets_in_frame(frames[other], stations[other], world)
            assert blisko <= abs(dalej[0] - stations[other]) + 1e-12, (
                local_x, index, blisko, abs(dalej[0] - stations[other]))


def test_clearance_profile_convexity_threshold_refuses_at_the_boundary():
    """Zakręt DOKŁADNIE na progu jest odmową — decyzja właściciela, pozycja 13.

    `CONVEXITY_EPS` był w `halfplanes` użyty dwa razy, osiemnaście wierszy od siebie,
    z PRZECIWNYMI konwencjami na granicy: pole obrysu na progu odrzucało (pozycja 12,
    przybite w #197), a zakręt na progu przyjmował i nie był przybity niczym. Mutacja
    `<` -> `<=` przeżywała przegląd właśnie dlatego, że nikt nie powiedział, co ma się
    stać na progu — a nie dlatego, że była nieosiągalna.

    Wejście jest SKONSTRUOWANE, nie wylosowane, i to jest tu istotne: `area2` wynosi
    `12.000000002`, czyli jedenaście rzędów nad progiem, więc obrys jest obrysem,
    a jego najmniejszy zakręt równa się `-1e-9` CO DO BITU. W taki próg się nie wpada
    losowo.
    """
    ring = [(0.0, 0.0), (1.0, 0.0), (2.0, -1e-9), (3.0, 0.0), (3.0, 2.0), (0.0, 2.0)]

    area2 = 0.0
    for a, b in zip(ring, ring[1:] + ring[:1]):
        area2 += a[0] * b[1] - b[0] * a[1]
    assert abs(area2) > 1e9 * CP.CONVEXITY_EPS, (
        f"to wejście przestało być obrysem: area2 = {area2!r}")

    orientation = math.copysign(1.0, area2)
    count = len(ring)
    turns = [((ring[(i + 1) % count][0] - ring[i][0])
              * (ring[(i + 2) % count][1] - ring[(i + 1) % count][1])
              - (ring[(i + 1) % count][1] - ring[i][1])
              * (ring[(i + 2) % count][0] - ring[(i + 1) % count][0])) * orientation
             for i in range(count)]
    assert min(turns) == -CP.CONVEXITY_EPS, (
        f"najmniejszy zakręt nie trafia już w próg co do bitu: {min(turns)!r}")

    try:
        CP.halfplanes(ring)
    except ValueError as error:
        assert "nie jest wypukły" in str(error), str(error)
    else:
        raise AssertionError("obrys z zakrętem dokładnie na progu został przyjęty")


def test_clearance_profile_convexity_threshold_still_accepts_real_profiles():
    """Kontrola po DRUGIEJ stronie — bez niej zaostrzenie mogłoby odrzucać wszystko.

    Zmierzone przed zmianą: najmniejszy zakręt w `profiles.PROFILES` to 0,0606
    w `bore_single`, czyli **6e+07 razy** nad progiem; `box_double` ma 3,02,
    a `station` 4,64. Wszystkie dodatnie, więc zaostrzenie `<` na `<=` nie ma jak
    dotknąć prawdziwego obrysu — i ten test to trzyma, gdyby ktoś podniósł próg.
    """
    import profiles

    for name in profiles.PROFILES:
        ring = [tuple(point) for point in profiles.profile_points(name)]
        planes = CP.halfplanes(ring)
        assert len(planes) == len(ring), name

    # Szum zaokrąglenia POWYŻEJ pasma nadal wolno: obrys z zakrętem -1e-10 przechodzi,
    # bo dziesięć razy bliżej zera niż próg. Gdyby ta asercja padła, znaczyłoby to,
    # że zaostrzenie zjadło tolerancję na szum, a nie tylko jej granicę.
    lagodny = [(0.0, 0.0), (1.0, 0.0), (2.0, -1e-10), (3.0, 0.0), (3.0, 2.0), (0.0, 2.0)]
    assert len(CP.halfplanes(lagodny)) == 6

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

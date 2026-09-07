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
    assert result["kind"] == "MT"
    assert result["polygons"] == 2
    assert result["narrowest"][0]["name"] == "waski"
    assert result["narrowest"][0]["corridor_width_m"] < result["narrowest"][1]["corridor_width_m"]
    for row in result["narrowest"]:
        assert "bbox_min_width_m" in row and "area_m2" in row


def CRSLESS(x, y):
    """Punkty testowe podajemy w stopniach wokół Brukseli, żeby przeszły przez transformację."""
    return (4.35 + x / 70000.0, 50.85 + y / 111000.0)


def test_survey_separates_tunnels_from_station_chambers():
    """Ten sam kod ma odpowiadać na dwa różne pytania, zależnie od typu poligonu."""
    payload = {"features": [
        {"properties": {"type": "MT", "name_fr": "tunel"},
         "geometry": {"type": "Polygon", "coordinates": [
             [list(CRSLESS(x, y)) for x, y in _rect(9.0, 300.0)]]}},
        {"properties": {"type": "MS", "name_fr": "stacja"},
         "geometry": {"type": "Polygon", "coordinates": [
             [list(CRSLESS(x, y)) for x, y in _rect(16.0, 150.0)]]}},
    ]}
    tunnels = TW.survey(payload, "MT")
    stations = TW.survey(payload, "MS")
    assert tunnels["polygons"] == 1 and tunnels["narrowest"][0]["name"] == "tunel"
    assert stations["polygons"] == 1 and stations["narrowest"][0]["name"] == "stacja"
    assert stations["narrowest"][0]["corridor_width_m"] > tunnels["narrowest"][0]["corridor_width_m"]


# --- point_in_ring dokładnie na krawędzi ---------------------------------------

def test_tunnel_width_point_in_ring_on_a_horizontal_edge_does_not_divide_by_zero():
    """Punkt o `y` równym `y` krawędzi poziomej — jedyne wejście różnicujące `>` od `>=`.

    Test przecięć promienia w pionie opiera się na tym, że krawędź liczy się tylko
    wtedy, gdy jej końce leżą po PRZECIWNYCH stronach poziomu punktu. Przy `>=`
    krawędź pozioma leżąca dokładnie na tym poziomie zaczyna się liczyć, a wtedy
    `(y - y1) / (y2 - y1)` dzieli przez zero. Wysokość 4,7 m to połowa szerokości
    testowego prostokąta i jest liczbą dokładną po obu stronach porównania, bo
    obie biorą się z tego samego literału.
    """
    ring = _box(4.7)
    assert TW.point_in_ring((100.0, -4.7), ring) is True
    assert TW.point_in_ring((100.0, 4.7), ring) is False
    # kontrola negatywna: milimetr do środka i na zewnątrz zachowuje się normalnie
    assert TW.point_in_ring((100.0, -4.699), ring) is True
    assert TW.point_in_ring((100.0, -4.701), ring) is False


def test_tunnel_width_point_exactly_on_the_side_wall_counts_as_outside():
    """Punkt na ścianie bocznej ma być POZA poligonem — inaczej pomiar staje się dwuznaczny.

    `measure()` odrzuca punkty leżące w dwóch poligonach naraz. Gdyby granica liczyła
    się jako wnętrze, dwa stykające się poligony tuneli obejmowałyby wspólną ścianę
    i każdy punkt na styku wypadałby z pomiaru — albo, co gorsza, wpadał do złego.
    Prostokąt kończy się na `x = 600.0`, więc `x` punktu jest bitowo równe granicy.
    """
    ring = _box(4.7, length=600.0)
    assert TW.point_in_ring((600.0, 0.0), ring) is False
    # kontrola negatywna: centymetr do środka to już wnętrze
    assert TW.point_in_ring((599.99, 0.0), ring) is True


# --- ray_distance: wszystkie cztery progi, każdy na swojej granicy ---------------

def _ray_edge(u_at_hit, t_at_hit, apex=(0.0, 1000.0)):
    """Pierścień, dla którego promień z (0,0) w górę trafia dokładnie w `(t, u)`.

    Konstrukcja jest dobrana tak, że mianownik przecięcia wynosi **dokładnie 1.0**:
    kierunek to `(0, 1)`, a krawędź celu biegnie z `(x1, y)` do `(x1 - 1, y)`, czyli
    `ex = -1.0`, `ey = 0.0`, więc `dx*ey - dy*ex = 1.0`. Przy mianowniku równym
    jedności `t` wychodzi bitowo równe `y`, a `u` bitowo równe `x1` — bez żadnego
    zaokrąglenia po drodze. To jedyny sposób, żeby postawić `t` albo `u` DOKŁADNIE
    na progu; „prawie na progu" nie odróżnia `>` od `>=`.

    Wierzchołek `apex` domyka pierścień daleko od promienia: jego dwie krawędzie
    przecinają promień dopiero w `t = 1000`, czyli poza każdym używanym `maximum`.
    """
    return [(u_at_hit, t_at_hit), (u_at_hit - 1.0, t_at_hit), apex]


def test_tunnel_width_ray_rejects_a_hit_exactly_at_the_near_epsilon():
    """Trafienie dokładnie w `1e-6` od źródła to jeszcze „to samo miejsce", nie ściana.

    Epsilon odcina promień od ściany, na której sam stoi. Granica `t > 1e-6` różni się
    od `>=` wyłącznie dla `t` równego progowi co do bitu — i dokładnie tak jest tu
    zbudowany pierścień.
    """
    origin, direction = (0.0, 0.0), (0.0, 1.0)
    assert TW.ray_distance(origin, direction, _ray_edge(0.5, 1e-6)) is None
    # kontrola negatywna: pół procenta powyżej progu i trafienie już się liczy
    assert TW.ray_distance(origin, direction, _ray_edge(0.5, 1.005e-6)) == 1.005e-6
    # oraz normalna ściana 4,7 m dalej
    assert TW.ray_distance(origin, direction, _ray_edge(0.5, 4.7)) == 4.7


def test_tunnel_width_ray_accepts_u_exactly_at_both_ends_of_the_edge():
    """Trafienie dokładnie w koniec krawędzi liczy się — od tego są tolerancje `1e-9`.

    Poligony UrbIS są łamanymi, więc promień prostopadły do osi regularnie trafia
    w wierzchołek, a nie w środek krawędzi. Obie tolerancje są napisane przez `<=`
    i obie są tu postawione na wartości równej progowi co do bitu: `u` wychodzi
    bitowo równe `x1`, a `1.0 + 1e-9` w teście to ten sam literał co w module.
    """
    origin, direction = (0.0, 0.0), (0.0, 1.0)
    assert TW.ray_distance(origin, direction, _ray_edge(-1e-9, 4.0)) == 4.0
    assert TW.ray_distance(origin, direction, _ray_edge(1.0 + 1e-9, 4.0)) == 4.0
    # kontrola negatywna: dwa razy dalej za tolerancję i krawędzi już nie ma
    assert TW.ray_distance(origin, direction, _ray_edge(-2e-9, 4.0)) is None
    assert TW.ray_distance(origin, direction, _ray_edge(1.0 + 2e-9, 4.0)) is None


def test_tunnel_width_ray_rejects_a_hit_exactly_at_the_maximum():
    """Zasięg `maximum` jest wyłączny: ściana dokładnie na zasięgu nie jest widziana.

    `RAY_MAX_M = 80 m` odgradza pomiar tunelu od trafienia w drugi koniec komory
    stacyjnej. Granica `t < maximum` różni się od `<=` tylko dla równości i tylko
    ona mówi, po której stronie stoi ta ściana.
    """
    origin, direction = (0.0, 0.0), (0.0, 1.0)
    ring = _ray_edge(0.5, 4.0)
    assert TW.ray_distance(origin, direction, ring, maximum=4.0) is None
    # kontrola negatywna: zasięg większy o pół metra i ściana się pojawia
    assert TW.ray_distance(origin, direction, ring, maximum=4.5) == 4.0


def test_tunnel_width_ray_skips_an_edge_whose_denominator_is_exactly_degenerate():
    """Krawędź o mianowniku równym dokładnie `1e-12` jest jeszcze liczona, nie odrzucana.

    Strażnik `abs(denominator) < 1e-12` odsiewa krawędzie równoległe do promienia,
    dla których przecięcie nie istnieje albo ucieka w nieskończoność. Jego granica
    jest osiągalna dokładnie: przy kierunku `(1, 0)` mianownik wynosi `dx*ey`, czyli
    `1.0 * ey`, a `ey` krawędzi z `(10, 0)` do `(20, 1e-12)` jest bitowo równe
    literałowi `1e-12` (jedna strona odejmowania jest zerem — to jedyny przypadek,
    w którym różnica dwóch liczb jest dokładna). Źródło promienia stoi w kolumnie
    `x = 10`, więc krawędź pionowa w tej kolumnie daje `t = 0` i odpada na epsilonie
    bliskim; bez tego to ona byłaby najbliższym trafieniem i przykryła wynik.
    """
    ring = [(10.0, 0.0), (20.0, 1e-12), (20.0, -1000.0), (10.0, -1000.0)]
    assert (1e-12 - 0.0) == 1e-12
    origin, direction = (10.0, 5e-13), (1.0, 0.0)
    assert abs(TW.ray_distance(origin, direction, ring) - 5.0) < 1e-9
    # kontrola negatywna: krawędź naprawdę równoległa (ey = 0) jest pomijana i wynik
    # przeskakuje na ścianę pionową w x = 20
    parallel = [(10.0, 0.0), (20.0, 0.0), (20.0, -1000.0), (10.0, -1000.0)]
    assert abs(TW.ray_distance(origin, direction, parallel) - 10.0) < 1e-9


# --- corridor_width i bbox_min_width: progi zwyrodnień --------------------------

def test_survey_corridor_width_rejects_a_ring_with_zero_perimeter():
    """Pierścień zwinięty do punktu ma obwód równo zero i nie ma szerokości.

    Bez tego strażnika (`perimeter <= 0.0`) taki poligon dostaje szerokość `0.0`
    i wchodzi do statystyk sieci jako „najwęższy tunel", zawyżając wniosek o tym,
    jak wąskie tunele w ogóle występują. Obwód wychodzi bitowo równy zeru, bo
    wszystkie odległości są odległościami punktu od siebie.
    """
    degenerate = [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]
    assert TW.polygon_perimeter(degenerate) == 0.0
    assert TW.corridor_width(degenerate) is None
    # kontrola negatywna: normalny prostokąt dalej ma szerokość
    assert abs(TW.corridor_width(_rect(9.4, 400.0)) - 9.4) < 0.2


def test_survey_corridor_width_still_measures_a_sub_millimetre_ring():
    """Poligon mniejszy od milimetra to nadal poligon — próg zwyrodnienia stoi na zerze.

    Sprawdza, że granica odrzucania jest zerem, a nie „czymś małym": pierścień
    o obwodzie rzędu pół milimetra ma dostać liczbę, a nie `None`. Przesunięcie tego
    progu w górę wycina z przeglądu sieci wszystkie mikropoligony — i robi to cicho,
    bo `survey()` po prostu je pomija.
    """
    tiny = [(0.0, 0.0), (2e-4, 0.0), (1e-4, 1e-4)]
    assert 0.0 < TW.polygon_perimeter(tiny) < 1e-3
    width = TW.corridor_width(tiny)
    assert width is not None and 0.0 < width < 1e-3, width
    # kontrola negatywna: ten sam kształt zwinięty do punktu nadal odpada
    assert TW.corridor_width([(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]) is None


def test_survey_corridor_width_of_a_square_uses_the_quadratic_root():
    """Kwadrat to graniczny przypadek „wydłużonego korytarza": wyróżnik wynosi równo zero.

    Dla kwadratu o boku `s` mamy `A = s²`, `P = 4s`, więc `(P/2)² - 4A = 0` co do bitu
    (10 i 40 są dokładne, 400 - 400 = 0). Wtedy pierwiastek równania daje szerokość `s`,
    a gałąź awaryjna `2A/P` dałaby `s/2` — dwukrotnie mniej. To jest różnica między
    „tunel ma 10 m" a „tunel ma 5 m", więc granica `discriminant < 0.0` musi być
    ostra i musi stać na zerze.
    """
    square = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    area, perimeter = TW.polygon_area(square), TW.polygon_perimeter(square)
    assert area == 100.0 and perimeter == 40.0
    assert (perimeter / 2.0) ** 2 - 4.0 * area == 0.0
    assert TW.corridor_width(square) == 10.0
    # kontrola negatywna: koło ma wyróżnik ujemny i wtedy gałąź awaryjna jest w porządku
    circle = [(math.cos(i * 2 * math.pi / 24) * 10.0, math.sin(i * 2 * math.pi / 24) * 10.0)
              for i in range(24)]
    assert (TW.polygon_perimeter(circle) / 2.0) ** 2 - 4.0 * TW.polygon_area(circle) < 0.0
    assert abs(TW.corridor_width(circle)
               - 2.0 * TW.polygon_area(circle) / TW.polygon_perimeter(circle)) < 1e-12


def test_survey_bbox_min_width_uses_an_edge_exactly_at_the_length_floor():
    """Krawędź o długości równo `1e-9` jeszcze wyznacza kierunek pomiaru.

    Próg `length < 1e-9` chroni przed dzieleniem przez zero przy liczeniu normalnej.
    Jego granica jest osiągalna dokładnie, bo `math.hypot(1e-9, 0.0)` zwraca wartość
    bezwzględną drugiego argumentu, czyli bitowo `1e-9`. Pierścień złożony z dwóch
    punktów ma obie krawędzie na tym progu: gdy próg puszcza, wynik to `0.0`; gdy
    odrzuca — funkcja nie ma z czego liczyć i zwraca `None`.
    """
    assert math.hypot(1e-9, 0.0) == 1e-9
    on_the_floor = [(0.0, 0.0), (1e-9, 0.0)]
    assert TW.bbox_min_width(on_the_floor) == 0.0
    # kontrola negatywna: krawędź o połowę krótsza jest już poniżej progu
    assert TW.bbox_min_width([(0.0, 0.0), (5e-10, 0.0)]) is None
    # i normalny prostokąt nadal zwraca swój krótszy bok
    assert abs(TW.bbox_min_width(_rect(9.4, 200.0)) - 9.4) < 1e-6


def test_survey_polygon_rings_reads_a_multipolygon_not_only_a_polygon():
    """`MultiPolygon` niesie w UrbIS tunele rozdzielone stacją — nie wolno ich zgubić.

    Gałąź `Polygon` była sprawdzona przez testy sieciowe, gałąź `MultiPolygon` nie
    była w ogóle. Odwrócenie tego porównania zwraca pustą listę i cały obiekt znika
    z przeglądu bez żadnego komunikatu.
    """
    multi = {"type": "MultiPolygon", "coordinates": [
        [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]],
        [[[5.0, 5.0], [6.0, 5.0], [6.0, 6.0]]]]}
    rings = TW.polygon_rings(multi)
    assert len(rings) == 2 and rings[1][0] == [5.0, 5.0], rings
    # kontrola negatywna: Polygon dalej daje jeden pierścień, a nieznany typ — zero
    assert len(TW.polygon_rings({"type": "Polygon",
                                 "coordinates": [[[0.0, 0.0], [1.0, 0.0]]]})) == 1
    assert TW.polygon_rings({"type": "LineString", "coordinates": []}) == []


# --- progi doboru próbek -------------------------------------------------------

def test_tunnel_width_keeps_a_sample_exactly_at_the_station_halo():
    """Próbka dokładnie `halo` od stacji jest jeszcze szlakiem, nie komorą stacyjną.

    Istniejący test sprawdzał tylko `120.0 <= chainage <= 480.0`, czyli warunek
    prawdziwy zarówno dla `<`, jak i dla `<=`. Granicy dotyka wyłącznie próbka
    o kilometrażu równym `halo` co do bitu — a jest on dokładny, bo oś ma punkty
    co 20 m i kilometraż sumuje się z liczb całkowitych.
    """
    axis = _axis()
    rows = TW.measure(axis, [0.0, 600.0], [({"name_fr": "t"}, _box(4.7))], halo_m=120.0)
    kept = sorted(r["chainage_m"] for r in rows)
    assert kept[0] == 120.0 and kept[-1] == 480.0, kept
    # kontrola negatywna: halo większe o metr odcina tę próbkę i tylko ją
    tighter = TW.measure(axis, [0.0, 600.0], [({"name_fr": "t"}, _box(4.7))], halo_m=121.0)
    assert sorted(r["chainage_m"] for r in tighter) == kept[1:-1]


def test_tunnel_width_summary_keeps_a_sample_exactly_at_the_running_tunnel_limit():
    """Szerokość równa `RUNNING_TUNNEL_MAX_M` to jeszcze tunel szlakowy.

    Progiem odcina się węzły i rozjazdy. Istniejący test używał 8,8 m i 40 m, czyli
    wartości daleko po obu stronach; różnicę `<=` od `<` widać tylko na wartości
    równej progowi. Odcięcie o milimetr za wcześnie zabiera z próby najszersze
    tunele szlakowe i zaniża górny kraniec widełek, o które w tym pomiarze chodzi.
    """
    limit = TW.RUNNING_TUNNEL_MAX_M
    assert limit == 15.0
    at_limit = [{"chainage_m": 0.0, "width_m": limit,
                 "polygon_centre_offset_right_m": 0.0, "polygon": "szlak"}]
    summary = TW.summarise(at_limit)
    assert summary["status"] == "ok" and summary["samples"] == 1
    assert summary["max_m"] == limit
    # kontrola negatywna: centymetr powyżej progu i próbka odpada
    above = [{"chainage_m": 0.0, "width_m": limit + 0.01,
              "polygon_centre_offset_right_m": 0.0, "polygon": "wezel"}]
    assert TW.summarise(above)["samples"] == 0


# --- cały przebieg CLI ---------------------------------------------------------

_X0, _Y0 = 148000.0, 170000.0


def _cli_fixture(directory, half_width=4.7):
    """Oś 600 m i jeden prostokątny poligon MT wokół niej, wszystko lokalnie.

    Poligon jest zapisany w stopniach, tak jak przychodzi z OGC Features, i moduł
    sam przelicza go na Lambert 72. Szerokość 9,4 m to podwojone `half_width` i jest
    to liczba, którą przebieg ma wypisać.
    """
    import json
    import crs as CRS
    alignment = {"id": "TEST_A", "source_crs": "EPSG:31370",
                 "origin_source_crs": [_X0, _Y0],
                 "points": [[i * 20.0, 0.0] for i in range(31)],
                 "stations": [{"chainage_m": 0.0}, {"chainage_m": 600.0}]}
    alignment_path = os.path.join(directory, "TEST_A.json")
    with open(alignment_path, "w", encoding="utf-8") as handle:
        json.dump(alignment, handle)

    corners = [(_X0 - 50.0, _Y0 - half_width), (_X0 + 650.0, _Y0 - half_width),
               (_X0 + 650.0, _Y0 + half_width), (_X0 - 50.0, _Y0 + half_width)]
    ring = [list(CRS.lambert72_to_wgs84(x, y)) for x, y in corners]
    urbis = {"type": "FeatureCollection", "features": [
        {"properties": {"type": "MT", "name_fr": "tunel testowy"},
         "geometry": {"type": "Polygon", "coordinates": [ring + [ring[0]]]}}]}
    urbis_path = os.path.join(directory, "urbis.json")
    with open(urbis_path, "w", encoding="utf-8") as handle:
        json.dump(urbis, handle)
    return alignment_path, urbis_path


def test_tunnel_width_main_prints_the_measured_width_and_writes_it():
    """Przebieg CLI na lokalnym snapshocie: liczba na konsoli i ta sama liczba w pliku.

    `main()` nie miał żadnego testu, więc porównanie decydujące o tym, czy w ogóle
    wypisać wynik pomiaru, można było odwrócić — raport JSON zostawał poprawny,
    a operator dostawał samo ostrzeżenie o zastrzeżeniu i ani jednej liczby.
    Prostokąt o półszerokości 4,7 m daje 9,40 m w każdej z 19 próbek szlakowych
    (31 punktów osi minus po sześć w otoczeniu obu stacji).
    """
    import contextlib
    import io
    import json
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        alignment_path, urbis_path = _cli_fixture(directory)
        out = os.path.join(directory, "width.json")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = TW.main(["--alignment", alignment_path, "--out", out,
                            "--urbis-file", urbis_path])
        printed = buffer.getvalue()
        with open(out, encoding="utf-8") as handle:
            report = json.load(handle)

    assert code == 0
    assert report["status"] == "ok"
    assert report["polygons"] == 1
    assert report["summary"]["samples"] == 19, report["summary"]["samples"]
    assert report["summary"]["median_m"] == 9.4
    assert report["summary"]["stdev_m"] == 0.0
    assert "szerokość w planie: min 9.40 m" in printed, printed
    assert "mediana 9.40 m" in printed, printed
    # kontrola negatywna: węższy poligon daje inną liczbę w OBU miejscach naraz
    with tempfile.TemporaryDirectory() as directory:
        alignment_path, urbis_path = _cli_fixture(directory, half_width=3.04)
        out = os.path.join(directory, "width.json")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            TW.main(["--alignment", alignment_path, "--out", out,
                     "--urbis-file", urbis_path])
        narrow = buffer.getvalue()
        with open(out, encoding="utf-8") as handle:
            narrow_report = json.load(handle)
    assert narrow_report["summary"]["median_m"] == 6.08
    assert "mediana 6.08 m" in narrow, narrow

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

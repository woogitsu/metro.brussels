#!/usr/bin/env python3
"""Niezbieżność w `tools/track/crs.py` musi być słyszalna.

Dwie funkcje odwracały odwzorowanie Newtonem i po wyczerpaniu iteracji zwracały
ostatni iterat bez żadnego sygnału: `lambert72_to_wgs84` (dla `(1e9, 1e9)`
szerokość -46040° przy residuum 9,98e+08 m na składową) i `_authalic_to_geodetic`
(dla `beta = -90°` szerokość 270,355°). Ten plik pilnuje, że teraz podnoszą
`ValueError` z liczbami, a realne dane brukselskie nadal przechodzą.

Bez pytest — `test_all.py` sam odkrywa `test_*` w `tools/tests/test_*.py`.

Punkty odniesienia są **czytane z `data/track/*.json`**, a nie wymyślane: pakiety
trzymają oś w lokalnym układzie metrycznym, którego początek podaje
`origin_source_crs` w EPSG:31370, więc współrzędna Lamberta to suma tych dwóch.
"""
import glob
import json
import math
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import crs as CRS  # noqa: E402

TRACK_DIR = os.path.join(ROOT, "data", "track")
# Rzeczywisty wierzchołek osi INSPIRE (`TN.RailTransportNetwork.gml`, EPSG:3035,
# kolejność osi N,E już rozwinięta) — ten sam, którego używa `test_inspire_rail.py`.
INSPIRE_VERTEX = (3927587.80980263, 3095760.75491994)
# Kryterium pętli jest na SKŁADOWĄ (`abs(dx) < tol and abs(dy) < tol`), a
# `lambert_inverse_residual_m` mierzy odległość euklidesową, więc jej wynik może
# przekroczyć `tolerance_m` do sqrt(2) raza. 1e-5 m mieści ten zapas i nadal jest
# o dwa rzędy pod milimetrem.
SUBMILLIMETRE_M = 1e-5

RESIDUAL_IN_MESSAGE = re.compile(r"residuum (\S+) m")
STEP_IN_MESSAGE = re.compile(r"krok (\S+) rad")


def _package_points_in_lambert72():
    """Każdy wierzchołek każdego skomitowanego pakietu, przeliczony do EPSG:31370."""
    points = []
    for path in sorted(glob.glob(os.path.join(TRACK_DIR, "*.json"))):
        if path.endswith(".provenance.json"):
            continue
        with open(path, encoding="utf-8") as handle:
            document = json.load(handle)
        ox, oy = document["origin_source_crs"]
        points += [(p[0] + ox, p[1] + oy) for p in document["points"]]
    return points


# --- pozytyw: realna sieć nadal przechodzi ------------------------------------

def test_crs_convergence_real_packages_still_invert_below_a_millimetre():
    """Wszystkie 2308 wierzchołków pakietów A–F wracają z residuum < 1e-5 m.

    Bramka na wypadek, gdyby nowy `ValueError` okazał się zbyt czuły: gdyby
    kryterium było choć trochę ostrzejsze od warunku przerwania pętli, ten test
    poleciałby na pierwszym pakiecie.
    """
    points = _package_points_in_lambert72()
    assert len(points) > 2000, len(points)
    worst = 0.0
    for x, y in points:
        residual = CRS.lambert_inverse_residual_m(x, y)
        worst = max(worst, residual)
    assert worst < SUBMILLIMETRE_M, worst


def test_crs_convergence_inspire_vertex_still_reaches_lambert72():
    """Ścieżka EPSG:3035 -> EPSG:31370, której projekt realnie używa.

    `_authalic_to_geodetic` jest prywatna i wołana tylko przez `laea3035_to_wgs84`,
    więc jej wyjątek mógłby wywrócić import sieci INSPIRE. Nie wywraca: realny
    wierzchołek trafia w brukselski bbox.
    """
    x, y = CRS.laea3035_to_lambert72(*INSPIRE_VERTEX)
    assert 140000 < x < 165000 and 160000 < y < 180000, (x, y)


def test_crs_convergence_authalic_inversion_has_room_over_the_whole_network():
    """`beta` realnej sieci jest o ponad 30° od pasma, w którym Newton nie domyka.

    Zmierzone: osiem kroków przestaje schodzić pod 1e-14 rad dopiero od
    |beta| ≈ 85,1°, a oś brukselska ma `beta` w [50,67°, 50,78°]. Test liczy ten
    zapas z danych, żeby zmiana zasięgu sieci go zauważyła, a nie żeby wierzyć
    liczbie w komentarzu.
    """
    e, q_p, _beta_0, _r_q, _d = CRS._laea_constants()
    worst_beta = 0.0
    for x, y in _package_points_in_lambert72():
        lon, lat = CRS.lambert72_to_wgs84(x, y)
        beta = math.asin(CRS._laea_q(math.sin(math.radians(lat)), e) / q_p)
        # skoro nie rzuca, to iteracja domknęła się w ośmiu krokach
        CRS._authalic_to_geodetic(beta, e, q_p)
        worst_beta = max(worst_beta, abs(math.degrees(beta)))
    assert worst_beta < 55.0, worst_beta
    assert 85.0 - worst_beta > 30.0, worst_beta


# --- negatyw: niezbieżność mówi wprost ----------------------------------------

def test_crs_convergence_absurd_input_raises_with_the_residual_it_reached():
    """`(1e9, 1e9)` dawało lat = -46040,3° w milczeniu; teraz podnosi ValueError.

    Sprawdzana jest **liczba w komunikacie**, nie sam typ wyjątku: bez residuum
    wołający nie wie, czy chybił o mikrometr, czy o pół Ziemi. Odczytana liczba
    musi być rzędu odległości wejścia od Belgii (~1e9 m), a nie byle jaka.
    """
    try:
        CRS.lambert72_to_wgs84(1e9, 1e9)
    except ValueError as exc:
        match = RESIDUAL_IN_MESSAGE.search(str(exc))
        assert match, str(exc)
        residual = float(match.group(1))
        assert residual > 1e8, (residual, str(exc))
        assert "60 iteracjach" in str(exc), str(exc)
    else:
        raise AssertionError("lambert72_to_wgs84(1e9, 1e9) nie podniosło ValueError")


def test_crs_convergence_projection_pole_raises_instead_of_returning_lon_396():
    """Biegun odwzorowania (E_F, N_F + r_f) dawał lon = 395,8° przy residuum 2435 m."""
    try:
        CRS.lambert72_to_wgs84(CRS.E_F, 5400088.438)
    except ValueError as exc:
        residual = float(RESIDUAL_IN_MESSAGE.search(str(exc)).group(1))
        assert residual > 1000.0, (residual, str(exc))
    else:
        raise AssertionError("biegun odwzorowania nie podniósł ValueError")


def test_crs_convergence_authalic_south_pole_raises_instead_of_returning_270_deg():
    """`beta = -90°`: Newton dzieli przez `2*cos(phi)` i uciekał do phi = 270,355°.

    Krok w komunikacie musi być duży (6,2e-03 rad ≈ 39 km), bo to jest różnica
    między „nie domknąłem się o szum bitowy" a „poszedłem w las".
    """
    e, q_p, _beta_0, _r_q, _d = CRS._laea_constants()
    try:
        CRS._authalic_to_geodetic(math.radians(-90.0), e, q_p)
    except ValueError as exc:
        step = float(STEP_IN_MESSAGE.search(str(exc)).group(1))
        assert step > 1e-3, (step, str(exc))
        assert "8 iteracjach" in str(exc), str(exc)
    else:
        raise AssertionError("beta = -90 deg nie podniosło ValueError")


def test_crs_convergence_authalic_near_pole_raises_even_when_the_answer_looks_sane():
    """`beta = 89,99°` zwracało phi = 89,990044669° — wynik wiarygodny, iteracja nie.

    To najgorszy przypadek starego zachowania: liczba wyglądała dobrze, więc nikt
    by jej nie sprawdził, a kryterium zbieżności nie było spełnione. Nowy wyjątek
    nie ocenia wiarygodności wyniku, tylko raportuje, że kryterium nie zostało
    osiągnięte.
    """
    e, q_p, _beta_0, _r_q, _d = CRS._laea_constants()
    try:
        CRS._authalic_to_geodetic(math.radians(89.99), e, q_p)
    except ValueError as exc:
        step = float(STEP_IN_MESSAGE.search(str(exc)).group(1))
        assert step > 1e-14, (step, str(exc))
    else:
        raise AssertionError("beta = 89.99 deg nie podniosło ValueError")


# --- granica: residuum dokładnie na progu ---------------------------------------
#
# Decyzja, spójna z warunkiem przerwania pętli, którego ta zmiana nie ruszyła:
# kryterium jest OSTRE, więc residuum równe dokładnie `tolerance_m` NIE przechodzi.
# Przechodzi dopiero pierwszy float mniejszy od progu.

def test_crs_convergence_residual_exactly_at_zero_tolerance_fails():
    """Droga „jedna strona jest zerem" — jedyna, w której równość jest dokładna.

    Naiwny test progu (`abs((6700.0 + 0.01) - 6700.0)` = 0,010000000000218)
    NIGDY nie dotyka progu: różnica wychodzi tuż NAD nim, więc taki test
    przechodzi identycznie dla `<` i dla `<=` i nie bramkuje niczego. `1e-6` nie
    jest potęgą dwójki, więc skonstruowanie residuum równego mu co do bitu nie
    jest możliwe przez dodawanie.

    Tutaj residuum jest **dokładnie zerowe**: wejście to obraz ziarna iteracji
    `LAMBERT_INVERSE_SEED` przez tę samą funkcję w przód, więc `fx - x` to
    odejmowanie bit w bit identycznych floatów, czyli `0.0` bez zaokrąglenia.
    Przy `tolerance_m = 0.0` mamy `0.0 < 0.0` -> False -> ValueError, a przy
    `tolerance_m = nextafter(0.0, 1.0)` -> True -> zwrot. Ta para rozstrzyga
    `<` kontra `<=`.
    """
    x0, y0 = CRS.wgs84_to_lambert72(*CRS.LAMBERT_INVERSE_SEED)
    try:
        CRS.lambert72_to_wgs84(x0, y0, tolerance_m=0.0)
    except ValueError as exc:
        assert float(RESIDUAL_IN_MESSAGE.search(str(exc)).group(1)) == 0.0, str(exc)
    else:
        raise AssertionError("residuum == tolerance_m == 0.0 powinno być porażką")

    lon, lat = CRS.lambert72_to_wgs84(x0, y0, tolerance_m=math.nextafter(0.0, 1.0))
    assert (lon, lat) == CRS.LAMBERT_INVERSE_SEED, (lon, lat)


def test_crs_convergence_residual_exactly_at_a_nonzero_tolerance_fails():
    """Droga „próg odczytany z wnętrza funkcji" — dla progu różnego od zera.

    Konstruowanie residuum równego zadanej liczbie jest niewykonalne, więc idzie
    to odwrotnie: funkcja jest najpierw pytana o residuum, jakie faktycznie
    osiąga (`tolerance_m = 0.0`, `iterations = 1`, czyli dokładnie jeden krok
    Newtona od ziarna), a odczytana z komunikatu liczba staje się progiem.
    Komunikat zapisuje residuum przez `repr`, więc `float()` odtwarza je co do
    bitu — bez tego cała ta droga byłaby takim samym przybliżeniem jak naiwna.

    Wejście: Gare de l'Ouest, kotwica pakietu A, wprost z `data/track/L1_A.json`.
    """
    with open(os.path.join(TRACK_DIR, "L1_A.json"), encoding="utf-8") as handle:
        x, y = json.load(handle)["origin_source_crs"]

    try:
        CRS.lambert72_to_wgs84(x, y, tolerance_m=0.0, iterations=1)
        raise AssertionError("tolerance_m = 0.0 nie może być nigdy spełnione")
    except ValueError as exc:
        reached = float(RESIDUAL_IN_MESSAGE.search(str(exc)).group(1))
    assert reached > 0.0, reached

    # residuum == tolerance_m, bit w bit -> porażka
    try:
        CRS.lambert72_to_wgs84(x, y, tolerance_m=reached, iterations=1)
    except ValueError as exc:
        assert float(RESIDUAL_IN_MESSAGE.search(str(exc)).group(1)) == reached, str(exc)
    else:
        raise AssertionError(f"residuum == tolerance_m == {reached!r} powinno być porażką")

    # pierwszy float powyżej progu -> zwrot
    lon, lat = CRS.lambert72_to_wgs84(
        x, y, tolerance_m=math.nextafter(reached, math.inf), iterations=1)
    assert -180.0 < lon < 180.0 and -90.0 < lat < 90.0, (lon, lat)


def test_crs_convergence_authalic_step_exactly_at_tolerance_fails():
    """Ten sam próg, ta sama droga, po stronie `_authalic_to_geodetic`.

    `1e-14` też nie jest potęgą dwójki, więc próg znów jest **odczytywany
    z wnętrza funkcji**: jeden krok Newtona (`iterations = 1`, `tolerance_rad = 0.0`)
    zgłasza swoją długość przez `repr`, a ta liczba wraca jako `tolerance_rad`.
    Krok równy progowi co do bitu jest porażką, pierwszy float nad progiem
    przechodzi. Naiwna droga („weź 1e-14 i dodaj coś małego") dawałaby wartość
    tuż nad progiem i nie odróżniłaby `<` od `<=`.

    `beta` to szerokość autaliczna Gare de l'Ouest, policzona z realnego punktu.
    """
    e, q_p, _beta_0, _r_q, _d = CRS._laea_constants()
    lon, lat = CRS.lambert72_to_wgs84(*CRS.wgs84_to_lambert72(4.3517, 50.8466))
    beta = math.asin(CRS._laea_q(math.sin(math.radians(lat)), e) / q_p)

    try:
        CRS._authalic_to_geodetic(beta, e, q_p, tolerance_rad=0.0, iterations=1)
        raise AssertionError("tolerance_rad = 0.0 nie może być nigdy spełnione")
    except ValueError as exc:
        reached = float(STEP_IN_MESSAGE.search(str(exc)).group(1))
    assert reached > 0.0, reached

    try:
        CRS._authalic_to_geodetic(beta, e, q_p, tolerance_rad=reached, iterations=1)
    except ValueError as exc:
        assert float(STEP_IN_MESSAGE.search(str(exc)).group(1)) == reached, str(exc)
    else:
        raise AssertionError(f"krok == tolerance_rad == {reached!r} powinien być porażką")

    phi = CRS._authalic_to_geodetic(
        beta, e, q_p, tolerance_rad=math.nextafter(reached, math.inf), iterations=1)
    assert -math.pi / 2 < phi < math.pi / 2, phi


def test_crs_convergence_defaults_are_the_ones_the_module_had_before():
    """Naprawą jest sygnał, nie rozluźnienie kryterium.

    Gdyby ktoś „naprawił" niezbieżność, podnosząc tolerancję albo liczbę iteracji,
    ta bramka to pokaże. Wartości pochodzą z wersji sprzed zmiany.
    """
    import inspect
    lambert = inspect.signature(CRS.lambert72_to_wgs84).parameters
    assert lambert["tolerance_m"].default == 1e-6, lambert["tolerance_m"].default
    assert lambert["iterations"].default == 60, lambert["iterations"].default
    authalic = inspect.signature(CRS._authalic_to_geodetic).parameters
    assert authalic["tolerance_rad"].default == 1e-14, authalic["tolerance_rad"].default
    assert authalic["iterations"].default == 8, authalic["iterations"].default


# --- trzecia iteracja w tym pliku: ECEF -> geodezyjne -------------------------------

def _brussels_ecef(height_m, a=None, f=None):
    a = CRS.A_WGS if a is None else a
    f = CRS.F_WGS if f is None else f
    return CRS._geodetic_to_ecef(4.35, 50.85, a, f, height_m)


def test_crs_ecef_iteration_stops_on_a_measured_step_not_on_a_fixed_count():
    """Pętla kończyła się po dokładnie 12 obrotach, cokolwiek by z nich nie wyszło.

    Zmierzone 03.09.2026: dla wejścia 6000 km pod powierzchnią przyrost szerokości
    po 12. obrocie odpowiadał jeszcze 1,27e-07 m łuku, czyli iteracja była wtedy
    przerywana w locie. Warunku nikt nie sprawdzał, bo go nie było.
    """
    import inspect

    signature = inspect.signature(CRS._ecef_to_geodetic).parameters
    assert signature["tolerance_m"].default == 1e-9, signature["tolerance_m"].default
    assert signature["iterations"].default == 40, signature["iterations"].default

    deep = _brussels_ecef(-6_000_000.0)
    residual = CRS.ecef_to_geodetic_residual_m(*deep, CRS.A_WGS, CRS.F_WGS)
    assert residual < 1e-9, residual


def test_crs_ecef_round_trip_is_exact_for_everything_this_project_produces():
    for height in (0.0, 100.0, -50.0, 400_000.0):
        point = _brussels_ecef(height)
        residual = CRS.ecef_to_geodetic_residual_m(*point, CRS.A_WGS, CRS.F_WGS)
        assert residual < 1e-9, (height, residual)

        lon, lat, back = CRS._ecef_to_geodetic(*point, CRS.A_WGS, CRS.F_WGS)
        assert abs(lon - 4.35) < 1e-12, (height, lon)
        assert abs(lat - 50.85) < 1e-12, (height, lat)
        assert abs(back - height) < 1e-6, (height, back)


def test_crs_ecef_on_the_rotation_axis_is_an_answer_not_a_zero_division():
    """`x = y = 0` podnosiło `ZeroDivisionError` z wnętrza pętli.

    Zmierzone przed zmianą: na osi `p` jest zerem, więc `h` wychodzi równe `-n`,
    a następny krok dzieli przez `n + h`, czyli przez zero. Wyjątek spoza kontraktu
    modułu, nie mówiący nic o tym, co jest z wejściem nie tak — ta sama rodzina, co
    `struct.error` z niedokończonego PNG-a. Odpowiedź jest tu zresztą znana bez
    iterowania, bo punkt na osi ma szerokość +-90 stopni z definicji.
    """
    semi_minor = CRS.A_WGS * (1 - CRS.F_WGS)

    for sign in (1.0, -1.0):
        lon, lat, height = CRS._ecef_to_geodetic(0.0, 0.0, sign * semi_minor,
                                                 CRS.A_WGS, CRS.F_WGS)
        assert lon == 0.0, lon
        assert lat == sign * 90.0, lat
        assert abs(height) < 1e-6, height

    # Punkt na osi, ale wyżej: wysokość liczy się od bieguna, nie od równika.
    _lon, lat, height = CRS._ecef_to_geodetic(0.0, 0.0, semi_minor + 43_247.0,
                                              CRS.A_WGS, CRS.F_WGS)
    assert lat == 90.0, lat
    assert abs(height - 43_247.0) < 1e-3, height

    residual = CRS.ecef_to_geodetic_residual_m(0.0, 0.0, semi_minor,
                                               CRS.A_WGS, CRS.F_WGS)
    assert residual < 1e-9, residual


def test_crs_ecef_zero_axis_branch_is_reached_only_by_an_exact_zero():
    """Gałąź osi jest skrótem, nie obejściem: `p` różne od zera ma iść przez pętlę.

    Gdyby warunek był nieostry (`p < eps`), punkty leżące blisko osi — a takie
    projekt liczy, bo biegun odwzorowania Lamberta 72 ma `p` rzędu kilometrów —
    dostawałyby szerokość równą dokładnie 90 stopni zamiast policzonej.
    """
    semi_minor = CRS.A_WGS * (1 - CRS.F_WGS)
    _lon, lat, _h = CRS._ecef_to_geodetic(1e-3, 0.0, semi_minor, CRS.A_WGS, CRS.F_WGS)
    assert lat != 90.0, lat
    assert 89.0 < lat < 90.0, lat


def test_crs_ecef_residual_grows_towards_the_rotation_axis_and_that_is_recorded():
    """Kontrola do decyzji, która czeka na właściciela.

    Degradacja wzoru w stronę osi jest CIĄGŁA i nieograniczona, więc żadna
    tolerancja nie rozcina tu „szumu" od „śmiecia" w miejscu, które dałoby się
    obronić pomiarem. Test przybija sam kształt tej zależności, żeby przyszła
    decyzja o progu opierała się na liczbach, a nie na wrażeniu.
    """
    semi_minor = CRS.A_WGS * (1 - CRS.F_WGS)
    measured = [(p, CRS.ecef_to_geodetic_residual_m(p, 0.0, semi_minor,
                                                    CRS.A_WGS, CRS.F_WGS))
                for p in (1e6, 1e4, 1e2, 1.0, 1e-6)]

    for (_p_far, near_axis), (_p_near, farther) in zip(measured, measured[1:]):
        assert near_axis <= farther, measured

    assert measured[0][1] < 1e-8, measured[0]
    assert measured[-1][1] > 1.0, measured[-1]

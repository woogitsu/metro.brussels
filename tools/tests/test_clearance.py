#!/usr/bin/env python3
"""Testy skrajni M7 na łukach (T-210 / #14). Bez Blendera i bez pytest."""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import clearance as CL  # noqa: E402
import m7_layout  # noqa: E402
import placement as PL  # noqa: E402
import profiles as PR  # noqa: E402

ALIGNMENT = os.path.join(ROOT, "data", "track", "L1_A.json")


def _arc(radius, span_deg=90.0, count=200):
    return [(radius * math.cos(math.radians(a)), radius * math.sin(math.radians(a)), 0.0)
            for a in (span_deg * i / count for i in range(count + 1))]


def test_clearance_versine_matches_the_closed_form():
    # strzałka cięciwy ~ l^2 / 8R przy l << R
    assert abs(CL.versine(10.0, 1000.0) - 10.0 ** 2 / (8 * 1000.0)) < 1e-4
    # cięciwa równa średnicy: środek pudła wypada w środku okręgu
    assert abs(CL.versine(200.0, 100.0) - 100.0) < 1e-9
    assert CL.versine(10.0, None) == 0.0


def test_clearance_versine_refuses_a_non_positive_radius():
    """Odmowa dla promienia niedodatniego. Bez niej `math.sqrt` dostaje liczbę ujemną.

    Uwaga do przeglądu mutacyjnego: ten test NIE zabija mutacji progu `0.0 -> 0.001`.
    Żeby ją zabić, trzeba by promienia 0,5 mm, a taki nie jest łukiem toru w żadnym
    sensie. Ta mutacja jest RÓWNOWAŻNA w dziedzinie zadania i tak jest zapisana
    w `reports/mutation-sweep.md` — dopisywanie testu z absurdalnym wejściem tylko po
    to, żeby licznik ładnie wyglądał, byłoby dopasowywaniem testu do narzędzia.
    """
    assert CL.versine(10.0, 0.0) == 0.0
    assert CL.versine(10.0, -5.0) == 0.0
    assert CL.versine(10.0, 1000.0) > 0.0


def test_clearance_versine_saturates_exactly_at_the_half_chord():
    # Granica `half >= radius_m` jest NIEOBSERWOWALNA z zewnątrz: przy połowie cięciwy
    # równej promieniowi obie gałęzie zwracają `radius_m`. Test przypina zachowanie,
    # ale nie udaje, że łapie mutację — mutant `>=` -> `>` jest tu równoważny i tak
    # jest sklasyfikowany.
    assert CL.versine(20.0, 10.0) == 10.0
    assert abs(CL.versine(19.98, 10.0) - (10.0 - math.sqrt(10.0 ** 2 - 9.99 ** 2))) < 1e-12


def test_clearance_circumradius_threshold_separates_noise_from_an_arc():
    """Próg `area2 < 1e-12` rozdziela szum digitalizacji od łuku — i to po OBU stronach.

    Istniejący test podawał punkty DOKŁADNIE współliniowe (`area2` = 0), więc próg mógł
    mieć dowolną wartość i mutacja `1e-12 -> 1.01e-12` przeżywała. Tu obie strony są
    przypięte wejściem dobranym tak, żeby `area2` wypadło MIĘDZY jedną a drugą wartością.
    """
    def area2_of(y):
        return abs(1.0 * 0.0 - y * 2.0)

    # area2 = 1,004e-12: powyżej progu 1e-12, poniżej zmutowanego 1,01e-12.
    between = 5.02e-13
    assert 1e-12 < area2_of(between) < 1.01e-12, area2_of(between)
    radius = CL.circumradius((0.0, 0.0), (1.0, between), (2.0, 0.0))
    assert radius is not None, "trójka tuż nad progiem ma dać promień, nie None"
    assert radius > 1e11, f"promień {radius} — przy takiej trójce ma być absurdalnie duży"

    # A tuż pod progiem — odrzucona.
    below = 1e-13
    assert area2_of(below) < 1e-12
    assert CL.circumradius((0.0, 0.0), (1.0, below), (2.0, 0.0)) is None


def test_clearance_point_at_returns_both_ends_of_the_axis():
    """Krańce osi należą do dziedziny, a nie leżą poza nią.

    Mutacja `target < stations[0]` -> `<=` sprawia, że kilometraż RÓWNY początkowi osi
    dostaje `None` zamiast pierwszego punktu. Przy cięciwie zerowej albo stacji leżącej
    dokładnie na krańcu to nie jest przypadek teoretyczny.
    """
    points = [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (20.0, 0.0, 0.0)]
    stations = [0.0, 10.0, 20.0]

    assert CL._point_at(points, stations, 0.0) == (0.0, 0.0, 0.0)
    assert CL._point_at(points, stations, 20.0) == (20.0, 0.0, 0.0)
    assert CL._point_at(points, stations, 10.0) == (10.0, 0.0, 0.0), "węzeł wewnętrzny"
    assert CL._point_at(points, stations, 5.0) == (5.0, 0.0, 0.0), "interpolacja w środku"

    # Kontrola negatywna: POZA osią nadal `None`, więc rozszerzenie dziedziny
    # do krańców nie zamieniło się w brak dziedziny.
    assert CL._point_at(points, stations, -0.001) is None
    assert CL._point_at(points, stations, 20.001) is None


def test_clearance_point_at_survives_a_repeated_vertex():
    """Powtórzony wierzchołek osi daje odcinek o zerowej długości.

    Łamane z danych STIB potrafią nieść zdublowany punkt. Bez strażnika `span <= 0.0`
    interpolacja dzieli przez zero i cały przejazd po osi wywala się wyjątkiem zamiast
    zwrócić punkt. Przegląd mutacyjny 02.09.2026 pokazał, że nic tego nie sprawdzało.
    """
    points = [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (10.0, 0.0, 0.0), (20.0, 0.0, 0.0)]
    stations = [0.0, 10.0, 10.0, 20.0]

    assert CL._point_at(points, stations, 10.0) == (10.0, 0.0, 0.0)
    assert CL._point_at(points, stations, 15.0) == (15.0, 0.0, 0.0), "za duplikatem"
    assert CL._point_at(points, stations, 5.0) == (5.0, 0.0, 0.0), "przed duplikatem"

    # Duplikat na POCZĄTKU osi to jedyne miejsce, w którym strażnik `span <= 0.0`
    # jest w ogóle osiągalny: pętla zwraca przy PIERWSZYM pasującym przedziale, więc
    # zdublowany punkt w środku zawsze zostaje przykryty przez przedział poprzedni.
    # Pierwsza wersja tego testu miała duplikat w środku i mutacji nie zabijała.
    leading = [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (10.0, 0.0, 0.0)]
    assert CL._point_at(leading, [0.0, 0.0, 10.0], 0.0) == (0.0, 0.0, 0.0)


def test_clearance_circumradius_recovers_a_known_circle():
    points = [(100.0, 0.0), (0.0, 100.0), (-100.0, 0.0)]
    assert abs(CL.circumradius(*points) - 100.0) < 1e-6
    assert CL.circumradius((0.0, 0.0), (1.0, 0.0), (2.0, 0.0)) is None


def test_clearance_radius_is_measured_on_the_car_body_chord():
    """Trójka sąsiednich punktów daje promień szumu; cięciwa pudła daje promień łuku."""
    arc = _arc(150.0)
    measured = [r for _s, r in CL.radii_along(arc, 15.667) if r is not None]
    assert measured, "brak próbek promienia"
    assert abs(min(measured) - 150.0) < 1.0, min(measured)
    assert abs(max(measured) - 150.0) < 1.0, max(measured)


def test_clearance_straight_track_uses_the_whole_static_margin():
    straight = [(x, 0.0, 0.0) for x in range(0, 400, 10)]
    result = CL.evaluate(straight, "box_double", 15.667)
    assert result["versine_at_min_radius_m"] < 1e-6
    assert abs(result["margin_m"] - result["static_clearance_m"]) < 1e-6
    assert result["fits_on_curve"] is True


def test_clearance_tighter_curve_eats_the_margin():
    wide = CL.evaluate(_arc(400.0), "box_double", 15.667)
    tight = CL.evaluate(_arc(90.0), "box_double", 15.667)
    assert tight["versine_at_min_radius_m"] > wide["versine_at_min_radius_m"]
    assert tight["margin_m"] < wide["margin_m"]


def test_clearance_car_chord_comes_from_the_spec():
    spec = m7_layout.load_spec()
    assert abs(CL.car_chord_m(spec) - 94.0 / 6) < 1e-9
    assert spec["length_m"] == 94.0 and spec["cars"] == 6


def test_clearance_never_shrinks_the_train_to_make_it_fit():
    """Zapas liczymy inflacją skrajni pojazdu, nie zmianą jego szerokości."""
    spec = m7_layout.load_spec()
    assert PR.M7_WIDTH_M == spec["width_m"]
    assert PR.vehicle_gauge(0.0)[1][0] - PR.vehicle_gauge(0.0)[0][0] == spec["width_m"]


def test_clearance_committed_axis_fits_the_double_box_but_not_the_single_bore():
    """Znalezisko do utrwalenia: `bore_single` nie ma zapasu na łuki pakietu A.

    `box_double` przechodzi w obu wariantach promienia, `bore_single` przechodzi tylko
    po wygładzeniu osi. Ten test pilnuje, żeby poprawka nie poszła w stronę zwężenia
    M7: gdyby ktoś zmienił szerokość pojazdu, poleci `test_clearance_never_shrinks...`.
    """
    if not os.path.isfile(ALIGNMENT):
        return
    document = json.load(open(ALIGNMENT, encoding="utf-8"))
    points = [tuple(p) for p in document["points"]]
    chord = CL.car_chord_m(m7_layout.load_spec())
    box = CL.evaluate(points, "box_double", chord)
    bore = CL.evaluate(points, "bore_single", chord)
    assert box["fits_on_curve"] is True, box
    assert box["margin_m"] > 0.4, box["margin_m"]
    assert bore["fits_on_curve"] is False, bore
    assert -0.2 < bore["margin_m"] < 0.0, bore["margin_m"]
    assert box["min_radius_m"] == bore["min_radius_m"]


# --- wysokość styku a światło profilu ----------------------------------------

def test_clearance_box_double_narrows_with_height_at_the_chamfer():
    """Regresja: kontrola krzyżowa mierzyła ścianę na WPISANEJ NA STAŁE wysokości 1,0 m.

    `box_double` ma ścięte naroża stropu, więc światło zwęża się z wysokością. Minimum
    pakietu A wypada na 1,03 m i stała zgadzała się przypadkiem; minimum pakietu B
    wypada na ścięciu, na 3,60 m, i tam stała myli się o 149 mm.
    """
    ring = PR.profile_points("box_double")
    spec = m7_layout.load_spec()
    half = spec["width_m"] / 2.0

    def wall_at(height, track_offset=2.10):
        return min(PL.distance_to_boundary(ring, track_offset + dx, height)
                   for dx in (-half, half))

    low = wall_at(1.03)
    high = wall_at(3.60)
    assert abs(low - 1.25) < 1e-6, low
    assert abs(high - 1.10) < 1e-6, high
    # to jest dokładnie ten rozjazd, który wywrócił pakiet B
    assert abs(low - high) > 0.14, (low, high)


def test_clearance_contact_height_matters_for_every_track_offset():
    """Zwężenie nie zależy od tego, na którym torze stoi skład."""
    ring = PR.profile_points("box_double")
    spec = m7_layout.load_spec()
    half = spec["width_m"] / 2.0
    for offset in (-2.10, 2.10):
        low = min(PL.distance_to_boundary(ring, offset + dx, 1.03) for dx in (-half, half))
        high = min(PL.distance_to_boundary(ring, offset + dx, 3.60) for dx in (-half, half))
        assert high < low, (offset, low, high)


def test_clearance_versine_formula_is_conservative_for_an_off_centre_body():
    """Dlaczego kontrola wzoru jest KIERUNKOWA, a nie symetryczna.

    Strzałkę liczy się z promienia w środku składu. Bryła, w której wypada minimum,
    leży poza środkiem — tam oś jest łagodniejsza, więc wzór przeszacowuje wychylenie
    i **zaniża** luz. Zmierzone na trzech pakietach, oba tory: zachowawczy 6 z 6,
    z zapasem 1,2-13,3 mm.
    """
    chord = 14.5667
    tight, gentle = 85.94, 112.38          # promień w środku składu i na cięciwie bryły
    assert CL.versine(chord, tight) > CL.versine(chord, gentle)
    # luz przewidziany z ciaśniejszego promienia jest mniejszy, czyli bezpieczny
    static = 1.25
    assert static - CL.versine(chord, tight) < static - CL.versine(chord, gentle)

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

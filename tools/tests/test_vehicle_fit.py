#!/usr/bin/env python3
"""Testy `tools/blender/vehicle_fit.py` — decyzji osadzenia składu w tunelu.

Cztery bramki wydzielone z `place_vehicle.py`, gdzie przemiatanie mutacyjne
z 03.09.2026 dało 7 mutacji i 7 ocalałych. Sześć z nich to porównania z tego
modułu; siódma (`o.type == "MESH"`) wymaga prawdziwej sceny Blendera i została
w oryginale, gdzie ją weryfikuje CI.

**Progi są tu sprawdzane NA granicy, nie obok niej.** Każdy test granicy ma
w docstringu wypisane, którą drogą dotyka punktu równości i dlaczego naiwna
droga („wartość tuż nad progiem") nie bramkuje niczego: `abs((0.9 + 0.01) - 0.9)`
wynosi 0.010000000000000009, czyli NAD progiem, i taki test przechodzi
identycznie dla `<` i dla `<=`.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import profiles  # noqa: E402
import vehicle_fit as VF  # noqa: E402


def _curved_axis():
    """Łuk o malejącym promieniu — na prostej `worst_chainage` nie ma czego szukać."""
    import sweep as SW
    points = [(0.0, 0.0, 0.0), (60.0, 0.0, 0.0), (120.0, 6.0, 0.0),
              (170.0, 30.0, 0.0), (200.0, 70.0, 0.0), (210.0, 130.0, 0.0)]
    return SW.catmull_rom(points, 5.0)


# --- track_offset --------------------------------------------------------------


def test_vehicle_fit_track_index_zero_is_inside_the_range():
    """Tor 0 jest DOPUSZCZALNY — i to jest granica, której nie dotykał żaden test.

    Domyślny `--track` narzędzia to 1, więc każde dotychczasowe wywołanie mijało
    dolny koniec zakresu o jeden. Trzy mutacje przeżyły dokładnie na tym: `0 <= index`
    zamienione na `0 < index` i próg `0` podniesiony do `1` odrzucają tor 0, a próg
    górny w ogóle tego nie widzi.

    Granica jest tu CAŁKOWITA, więc trafia się w nią dokładnie i bez zabiegów —
    pułapka zmiennoprzecinkowa dotyczy progów luzu, nie indeksów listy.
    """
    offsets = profiles.PROFILES["box_double"]["track_offsets"]
    assert len(offsets) == 2, offsets
    assert VF.track_offset(offsets, 0) == offsets[0]
    assert VF.track_offset(offsets, 1) == offsets[1]


def test_vehicle_fit_track_index_past_the_last_is_refused():
    """Górna granica: ostatni tor przechodzi, pierwszy za nim odmawia.

    `len(offsets)` to pierwszy indeks POZA listą, więc para (len-1, len) stoi
    okrakiem na granicy `index < len(offsets)`. Mutacja na `<=` puściłaby
    `len(offsets)` i `offsets[index]` poleciałoby `IndexError` w środku pomiaru —
    albo, dla indeksu ujemnego, cicho wybrałoby tor liczony od końca.
    """
    offsets = [-2.10, 2.10]
    assert VF.track_offset(offsets, len(offsets) - 1) == 2.10

    for bad in (len(offsets), len(offsets) + 1, -1):
        try:
            VF.track_offset(offsets, bad)
        except ValueError as error:
            assert "2" in str(error) and str(bad) in str(error), (bad, str(error))
        else:
            raise AssertionError(f"tor {bad} przeszedł przy {len(offsets)} torach")


def test_vehicle_fit_track_refusal_carries_both_numbers():
    """Komunikat odmowy musi mieć ILE torów i KTÓRY żądano.

    `place_vehicle.py` dokleja do niego nazwę profilu i wypuszcza jako `SystemExit`,
    więc to jedyne, co zobaczy ktoś patrzący na log CI. Odmowa bez liczb kazałaby
    mu czytać `profiles.py`.
    """
    try:
        VF.track_offset([0.0], 7)
    except ValueError as error:
        assert str(error) == "ma 1 torów, żądano 7", str(error)
    else:
        raise AssertionError("tor 7 przeszedł na profilu jednotorowym")


# --- resolve_chainage ----------------------------------------------------------


def test_vehicle_fit_worst_chainage_is_computed_not_parsed():
    """Słowo `worst` jest liczone, nie parsowane jako liczba.

    Mutacja `==` -> `!=` odwraca obie gałęzie: dla „worst" poszłaby do
    `float("worst")`. Test sprawdza, że wynik NAPRAWDĘ pochodzi z szukania łuku —
    promień jest podany, a czoło leży pół składu przed środkiem.
    """
    points = _curved_axis()
    length = 94.0
    start, station, radius = VF.resolve_chainage("worst", points, length)

    assert radius is not None, "tryb najgorszego łuku ma zwrócić promień"
    assert radius > 0.0
    assert abs(station - (start + length / 2.0)) < 1e-9, (start, station)
    # Cały skład musi się mieścić na osi — `guard_m` w `worst_chainage` to długość
    # składu, więc środek nie może wypaść bliżej niż 94 m od któregokolwiek końca.
    assert start >= 0.0, start


def test_vehicle_fit_explicit_chainage_is_taken_literally():
    """Liczba w `--chainage` jest metrami czoła, a promienia wtedy NIE liczymy.

    Druga strona tej samej mutacji `==` -> `!=`: dla „120.0" mutant poszedłby
    szukać najgorszego łuku i zwrócił promień oraz zupełnie inne czoło.
    `None` w promieniu jest tu treścią raportu, nie brakiem danych — promień
    policzony w innym miejscu niż stoi skład byłby liczbą o niczym.
    """
    points = _curved_axis()
    start, station, radius = VF.resolve_chainage("120.0", points, 94.0)

    assert start == 120.0, start
    assert station == 120.0 + 47.0, station
    assert radius is None, radius


# --- clearance_tally -----------------------------------------------------------


def test_vehicle_fit_tally_reports_worst_and_per_body_minimum():
    """Globalne minimum i minimum każdego pudła to dwie różne liczby.

    Raport podaje oba: `min_clearance_m` z nazwą bryły oraz
    `per_object_min_clearance_m`. Test pilnuje, że nie są tą samą liczbą
    przepisaną dwa razy.
    """
    worst, per_object = VF.clearance_tally([
        ("pudlo_A", [(0.9012, 10.0, 1.1, 2.2), (0.8899, 12.0, 1.2, 2.3)]),
        ("pudlo_B", [(1.4000, 60.0, 0.1, 3.0)]),
    ])

    assert worst["clearance_m"] == 0.8899
    assert worst["object"] == "pudlo_A"
    assert worst["chainage_m"] == 12.0
    assert worst["lateral_m"] == 1.2
    assert worst["vertical_m"] == 2.3
    assert per_object == {"pudlo_A": 0.8899, "pudlo_B": 1.4}, per_object


def test_vehicle_fit_tally_tie_keeps_the_first_body():
    """GRANICA `<` kontra `<=`: remis luzu między dwoma pudłami.

    Ta mutacja jest obserwowalna WYŁĄCZNIE w punkcie dokładnej równości; dla
    luzu „o włos większego" obie wersje wybierają to samo pudło. Naiwny test
    remisu wpisałby drugą wartość z ręki albo policzył ją arytmetycznie i minąłby
    granicę: `0.8899 + 1e-9 - 1e-9` nie musi wrócić do `0.8899` bit w bit.

    Dlatego wartość remisu jest **odczytana z modułu**: pierwsze wywołanie zwraca
    zmierzony luz pudła A, a drugie podaje TĘ SAMĄ liczbę jako próbkę pudła B.
    Równość jest wtedy dokładna z definicji, bo to jeden i ten sam `float`.

    Remis nie jest tu obojętny: obok liczby zapisujemy nazwę bryły i chainage,
    więc `<=` przepisałoby raport na drugie pudło, nie zmieniając samej liczby.
    """
    first, _ = VF.clearance_tally([("pudlo_A", [(0.8899, 12.0, 1.2, 2.3)])])
    tie = first["clearance_m"]

    worst, per_object = VF.clearance_tally([
        ("pudlo_A", [(0.8899, 12.0, 1.2, 2.3)]),
        ("pudlo_B", [(tie, 80.0, -1.2, 2.9)]),
    ])

    assert worst["clearance_m"] == tie
    assert worst["object"] == "pudlo_A", "przy remisie wygrywa pierwsze pudło"
    assert worst["chainage_m"] == 12.0, worst
    # Remis widzą OBA pudła, więc minimum per bryła jest w obu takie samo.
    assert per_object == {"pudlo_A": tie, "pudlo_B": tie}, per_object


def test_vehicle_fit_tally_tie_inside_one_body_keeps_the_first_vertex():
    """Ten sam remis w środku jednego pudła — chainage nie ma prawa przeskoczyć.

    Granica dotknięta tą samą drogą: wartość bierzemy z wyniku modułu, a nie
    z klawiatury. Bez tego testu `<=` przy dwóch wierzchołkach o identycznym
    luzie przesuwałoby raportowany chainage na ostatni z nich.
    """
    first, _ = VF.clearance_tally([("pudlo_A", [(0.5, 5.0, 0.0, 1.0)])])
    tie = first["clearance_m"]

    worst, _ = VF.clearance_tally([
        ("pudlo_A", [(tie, 5.0, 0.0, 1.0), (tie, 25.0, 0.0, 3.0)]),
    ])
    assert worst["chainage_m"] == 5.0, worst


def test_vehicle_fit_tally_keeps_an_empty_body_infinite():
    """Pudło bez wierzchołków zostaje z nieskończonością, nie z zerem.

    Zachowanie przeniesione wiernie z `place_vehicle.py`. Pusta bryła w raporcie
    ma być widoczna jako `Infinity`; wpisanie tam zera podszyłoby ją pod styk
    ze ścianą, a wpisanie zapasu — pod bryłę zmierzoną.
    """
    worst, per_object = VF.clearance_tally([("pusta", []), ("pudlo_A", [(1.0, 0.0, 0.0, 0.0)])])
    assert per_object["pusta"] == float("inf")
    assert worst["object"] == "pudlo_A"


def test_vehicle_fit_tally_without_any_body_stays_neutral():
    """Brak brył to nieskończony luz i puste nazwy — nie wyjątek.

    `place_vehicle.py` odrzuca plik bez ani jednego mesha znacznie wcześniej
    (`import_glb`), więc ten stan jest nieosiągalny z CLI. Test przypina go
    mimo to, bo bramka `clearance_problem` czyta tę liczbę i musi z niej wyjść
    „przechodzi", a nie `TypeError`.
    """
    worst, per_object = VF.clearance_tally([])
    assert worst["clearance_m"] == float("inf")
    assert worst["object"] == ""
    assert per_object == {}
    assert VF.clearance_problem(worst["clearance_m"], 0.0) is None


# --- clearance_problem ---------------------------------------------------------


def test_vehicle_fit_clearance_exactly_at_the_threshold_passes():
    """GRANICA progu luzu: luz dokładnie równy progowi jeszcze przechodzi.

    Mutacja `<` -> `<=` jest widoczna WYŁĄCZNIE w punkcie równości. Naiwny test
    podaje luz „tuż nad progiem" i nie bramkuje niczego — dowód niżej w asercji:
    `abs((0.9 + 0.01) - 0.9)` nie wynosi 0.01, więc taka wartość leży nad
    granicą i przechodzi zarówno dla `<`, jak i dla `<=`.

    Równość dwóch `float` jest dokładna tylko wtedy, gdy obie strony to TA SAMA
    wartość, a nie wynik arytmetyki na niej. Stąd trzy drogi, każda inna:

    * próg 0,0 — domyślny próg narzędzia; zero jest dokładne bez zabiegów
      i to na nim rozstrzyga się styk pojazdu ze ścianą,
    * jedna zmienna podana po OBU stronach porównania,
    * próg 0,5 — potęga dwójki, reprezentowana dokładnie, więc `0.25 + 0.25`
      wraca do niej bit w bit i granicę można też złożyć arytmetycznie.
    """
    # 1. domyślny próg narzędzia: zero
    assert VF.clearance_problem(0.0, 0.0) is None

    # 2. ta sama wartość po obu stronach
    threshold = 0.8999
    assert VF.clearance_problem(threshold, threshold) is None

    # 3. potęga dwójki złożona z połówek — równość zachodzi bit w bit
    assert 0.25 + 0.25 == 0.5
    assert VF.clearance_problem(0.25 + 0.25, 0.5) is None

    # Kontrola negatywna drogi naiwnej: „tuż nad progiem" NIE stoi na granicy.
    assert abs((0.9 + 0.01) - 0.9) != 0.01
    assert VF.clearance_problem(0.9 + 0.01, 0.9) is None, (
        "wartość tuż nad progiem przechodzi w obu wariantach operatora — "
        "test napisany tak nie bramkuje niczego")


def test_vehicle_fit_clearance_below_the_threshold_is_refused():
    """Poniżej progu wychodzi gotowy komunikat z obiema liczbami.

    Najmniejszy krok w dół od granicy bierzemy z `math.nextafter`, a nie
    z odjęcia „małej liczby": dla progu 0,8999 odjęcie 1e-9 też by zadziałało,
    ale nextafter daje najbliższą reprezentowalną liczbę mniejszą od progu,
    czyli najostrzejszy możliwy test tej samej granicy z drugiej strony.
    """
    import math

    threshold = 0.8999
    below = math.nextafter(threshold, -math.inf)
    assert below < threshold and below != threshold

    problem = VF.clearance_problem(below, threshold)
    assert problem is not None, "luz pod progiem musi dać odmowę"
    assert "0.8999" in problem, problem
    assert "poniżej progu" in problem and "ścianę tunelu" in problem, problem

    # Ujemny luz przy domyślnym progu 0,0 — pojazd fizycznie w ścianie.
    negative = VF.clearance_problem(-0.0123, 0.0)
    assert negative is not None
    assert "-0.0123" in negative, negative
    assert "0.0000" in negative, negative

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

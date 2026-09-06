#!/usr/bin/env python3
"""Najciaśniejszy łuk na KAŻDEJ z sześciu osi — i to, czym pakiety B-F różnią się od A.

`reports/M7-curve-clearance.md` zmierzył metodę na jednym pakiecie. Ten moduł przypina
to, co wyszło po zastosowaniu jej do pozostałych pięciu, i pilnuje **wyłącznie różnic**:
liczba, która na wszystkich sześciu osiach wychodzi tak samo, nie potrzebuje tu testu,
bo strzeże jej już `tools/tests/test_clearance.py`.

Pomiary są datowane — 06.09.2026, `reports/promien-luku-szesc-osi.md` — i liczone
z osi w `data/track/`, nie przepisane z raportu: gdyby oś się zmieniła, ten moduł ma
zgasnąć, a nie milczeć. Widełki są dobrane tak, żeby przeżyć zaokrąglenie, a nie żeby
przeżyć zmianę osi.

CZEGO TEN MODUŁ NIE ROZSTRZYGA. Progu dopuszczalnego luzu nie ma w `data/` ani
w `docs/` — `reports/clearance-BE.md` §6 mówi to wprost — więc żaden test tutaj nie
sprawdza, czy zmierzony zapas jest „wystarczający". Sprawdzają wyłącznie znak
i wartość, bo to są pomiary, a nie oceny.
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import build_alignment as BA  # noqa: E402
import clearance as CL  # noqa: E402
import m7_layout  # noqa: E402
import sweep  # noqa: E402

#: Sześć osi pakietów A-F. Kolejność jest kolejnością z `docs/TASKS.md`, nie alfabetyczną.
AXES = ("L1_A", "L1_B", "L2_E", "L5_C", "L5_D", "L6_F")

#: Przedziały kilometrażu, na których OSM **nie widzi tunelu** — przepisane
#: z `reports/surface-vs-tunnel.md` §3, razem z zastrzeżeniem tamtego raportu:
#: punkty osi stoją co 7,6-22,4 m, więc granica przedziału jest znana z tą samą
#: dokładnością i nie wolno jej czytać co do metra. Pakiet B nie ma ani jednego
#: takiego przedziału i to też jest pomiar, a nie brak danych.
OUTSIDE_TUNNEL_M = {
    "L1_A": ((45.0, 135.0), (840.0, 840.0)),
    "L1_B": (),
    "L2_E": ((7762.0, 7867.0), (7897.0, 7927.0), (8556.0, 8616.0)),
    "L5_C": ((4937.0, 5386.0),),
    "L5_D": ((60.0, 539.0), (764.0, 1258.0), (1422.0, 1916.0), (2230.0, 3398.0)),
    "L6_F": ((60.0, 568.0), (763.0, 972.0), (3530.0, 3784.0)),
}

_CACHE = {}


def _chord():
    return CL.car_chord_m(m7_layout.load_spec())


def _points(name):
    if ("points", name) not in _CACHE:
        path = os.path.join(ROOT, "data", "track", f"{name}.json")
        with open(path, encoding="utf-8") as handle:
            document = json.load(handle)
        _CACHE[("points", name)] = [tuple(p) for p in document["points"]]
    return _CACHE[("points", name)]


def _evaluate(name, profile, variant):
    """`CL.evaluate` na osi skomitowanej (`pessimistic`) albo zagęszczonej (`optimistic`)."""
    key = ("eval", name, profile, variant)
    if key not in _CACHE:
        points = _points(name)
        if variant == "optimistic":
            points = sweep.catmull_rom(points, 5.0)
        _CACHE[key] = CL.evaluate(points, profile, _chord())
    return _CACHE[key]


def _scan(name, profile):
    key = ("scan", name, profile)
    if key not in _CACHE:
        _CACHE[key] = CL.scan(_points(name), profile, _chord())
    return _CACHE[key]


def _distance_to_surface(name, chainage_m):
    """Odległość kilometrażu od najbliższego odcinka POZA tunelem; 0 dla wnętrza odcinka."""
    spans = OUTSIDE_TUNNEL_M[name]
    if not spans:
        return math.inf
    return min(0.0 if low <= chainage_m <= high else min(abs(chainage_m - low),
                                                         abs(chainage_m - high))
               for low, high in spans)


# --- co jest wspólne: sześć osi w ogóle daje się zmierzyć ------------------------

def test_curve_radius_every_one_of_the_six_axes_yields_a_measured_arc():
    """Warunek wstępny dla wszystkiego niżej: każda oś ma łuk, kilometraż i próbki.

    Bez tego testu oś, która przestałaby dawać próbki, przeszłaby przez resztę modułu
    cicho — porównania „A jest ciaśniejsze niż B" są prawdziwe także wtedy, gdy jedna
    ze stron jest `None`, dopóki nikt nie sprawdzi, że nie jest.
    """
    for name in AXES:
        item = _evaluate(name, "box_double", "pessimistic")
        assert item["min_radius_m"] is not None, name
        assert 20.0 < item["min_radius_m"] < 500.0, (name, item["min_radius_m"])
        assert item["samples"] > 200, (name, item["samples"])
        length = sweep.chainages(_points(name))[-1]
        assert 0.0 <= item["min_radius_chainage_m"] <= length, (name, item)


# --- różnica 1: pakiet A jest najciaśniejszy z sześciu ---------------------------

def test_curve_radius_package_A_is_the_tightest_of_the_six():
    """Najciaśniejszy łuk sieci leży w pakiecie A — tym już zbudowanym, nie w nowych.

    To ta sama konkluzja co w `reports/clearance-BE.md` §1, ale osiągnięta inną drogą:
    tam mierzono luz siatką w Blenderze na trzech pakietach, tu promień czystym
    Pythonem na sześciu. Zgodność dwóch niezależnych dróg jest tu całą wartością.
    """
    radii = {name: _evaluate(name, "box_double", "pessimistic")["min_radius_m"]
             for name in AXES}
    assert min(radii, key=radii.get) == "L1_A", radii
    for name in AXES:
        if name != "L1_A":
            assert radii[name] > radii["L1_A"] + 1.0, (name, radii)
    # Najluźniejszy jest pakiet D i to jest druga strona tej samej różnicy.
    assert max(radii, key=radii.get) == "L5_D", radii
    assert radii["L5_D"] > 1.5 * radii["L1_A"], radii


# --- różnica 2: pakiet B ma najciaśniejszy łuk w pierwszej długości składu -------

def test_curve_radius_package_B_puts_its_tightest_arc_inside_one_train_length():
    """W pakiecie B najciaśniejszy łuk leży 30 m od początku osi, w pozostałych pięciu
    ponad kilometr od obu końców.

    Konsekwencja jest praktyczna, nie kosmetyczna: 94-metrowy skład ustawiony czołem
    na tym łuku wystaje **poza oś**, więc miary liczone na całym składzie
    (`profile_vehicle.py`, `refine_positions`) nie mają tam gdzie stanąć. Wzór na
    strzałkę cięciwy ma — i dlatego tę liczbę w ogóle da się podać.
    """
    spec = m7_layout.load_spec()
    train_length = float(spec["length_m"])
    at_start = {}
    for name in AXES:
        item = _evaluate(name, "box_double", "pessimistic")
        length = sweep.chainages(_points(name))[-1]
        station = item["min_radius_chainage_m"]
        at_start[name] = min(station, length - station)
    assert at_start["L1_B"] < train_length, at_start
    assert at_start["L1_B"] < 50.0, at_start["L1_B"]
    for name in AXES:
        if name != "L1_B":
            assert at_start[name] > 1000.0, (name, at_start)


# --- różnica 3: w D i F widełki wskazują DWA RÓŻNE łuki --------------------------

def test_curve_radius_variants_disagree_about_which_arc_is_tightest_in_D_and_F():
    """W pakietach D i F wariant pesymistyczny i optymistyczny wskazują inny łuk.

    W A, B, C i E oba warianty trafiają w ten sam wierzchołek co do decymetra, więc
    widełki są widełkami JEDNEJ liczby. W D rozjeżdżają się o 673 m, w F o 2976 m —
    tam „promień najmniejszego łuku" nie ma jednego adresu i raport, który podałby
    sam promień bez kilometrażu obu wariantów, mówiłby o dwóch różnych miejscach.
    """
    apart = {}
    for name in AXES:
        pessimistic = _evaluate(name, "box_double", "pessimistic")
        optimistic = _evaluate(name, "box_double", "optimistic")
        apart[name] = abs(pessimistic["min_radius_chainage_m"]
                          - optimistic["min_radius_chainage_m"])
    for name in ("L1_A", "L1_B", "L2_E", "L5_C"):
        assert apart[name] < 1.0, (name, apart)
    assert apart["L5_D"] > 500.0, apart
    assert apart["L6_F"] > 2000.0, apart


# --- różnica 4: `bore_single` dzieli sześć osi na dwie połowy --------------------

def test_curve_radius_bore_single_fails_on_three_axes_and_passes_on_three():
    """Znalezisko z pakietu A rozciąga się na C i E, ale NIE na B, D i F.

    `reports/M7-curve-clearance.md` §3 zapisał, że projektowy `bore_single` nie ma
    zapasu na łuki pakietu A. Po zastosowaniu do sześciu osi widać, że to nie jest
    własność jednego pakietu ani całej sieci: profil przechodzi dokładnie tam, gdzie
    najciaśniejszy łuk jest luźniejszy niż około 70 m.
    """
    margins = {name: _evaluate(name, "bore_single", "pessimistic")["margin_m"]
               for name in AXES}
    failing = sorted(name for name, value in margins.items() if value < 0.0)
    assert failing == ["L1_A", "L2_E", "L5_C"], margins
    for name in failing:
        assert -0.2 < margins[name] < 0.0, (name, margins[name])
    for name in ("L1_B", "L5_D", "L6_F"):
        assert 0.0 < margins[name] < 0.2, (name, margins[name])
    # Najgłębszy niedobór jest w A i jest ponad czterokrotnie głębszy niż w E.
    assert margins["L1_A"] < margins["L5_C"] < margins["L2_E"] < 0.0, margins
    assert margins["L1_A"] < 4.0 * margins["L2_E"], margins
    # `box_double` przechodzi na wszystkich sześciu — inaczej porównanie wyżej
    # mierzyłoby oś, a nie profil.
    for name in AXES:
        assert _evaluate(name, "box_double", "pessimistic")["fits_on_curve"] is True, name


# --- różnica 5: najciaśniejszy łuk pakietu D leży POZA tunelem -------------------

def test_curve_radius_tightest_arc_of_package_D_falls_outside_the_tunnel():
    """Oba warianty pakietu D wskazują łuk na odcinku, którego OSM nie widzi jako tunel.

    To ta sama klasa zastrzeżenia co uwaga o kilometrażu 8584,1 m w
    `reports/clearance-BE.md` §1: luz policzony wobec ściany, której tam nie ma, jest
    poprawną liczbą o modelu i bezużyteczną jako fakt o metrze. Różnica jest taka, że
    tam dotyczyła jednego dołka luzu, a tu **najciaśniejszego łuku całego pakietu**.

    Rozdzielenie jest ostre i to jest cała siła tego testu: w D oba warianty leżą
    w granicy dokładności przedziału, w pozostałych pięciu najbliższy odcinek poza
    tunelem jest o setki metrów dalej.
    """
    near = {}
    for name in AXES:
        near[name] = (
            _distance_to_surface(name, _evaluate(name, "box_double", "pessimistic")
                                 ["min_radius_chainage_m"]),
            _distance_to_surface(name, _evaluate(name, "box_double", "optimistic")
                                 ["min_radius_chainage_m"]),
        )
    assert max(near["L5_D"]) <= 25.0, near
    assert near["L5_D"][1] == 0.0, near["L5_D"]
    for name in AXES:
        if name != "L5_D":
            assert min(near[name]) > 300.0, (name, near)
    assert near["L1_B"] == (math.inf, math.inf), near["L1_B"]


# --- różnica 6: dwa pomiary promienia, jeden iloraz ------------------------------

def test_curve_radius_two_committed_measures_differ_by_the_digitisation_step():
    """`build_alignment.radius_stats` i `clearance.radii_along` mierzą DWIE różne rzeczy.

    Walidator osi wymaga promienia >= 90 m (`tools/tests/test_packages.py`) i wszystkie
    sześć osi ten warunek spełniają. Promień, który widzi pudło członu, jest jednak
    na każdej z nich prawie dwukrotnie mniejszy — bo pierwszy mierzy na trójce
    wierzchołków odległych o krok digitalizacji (~15 m), drugi na cięciwie pół pudła
    (~7,8 m). Iloraz jest więc ilorazem tych dwóch długości, a nie własnością toru:
    wychodzi ~1,91 na WSZYSTKICH sześciu osiach, mimo że same promienie różnią się
    o 60 %.

    Dlatego zdanie „walidator dopuszcza tylko łuki powyżej 90 m" nie jest zdaniem
    o skrajni i ten test istnieje po to, żeby nikt go tak nie przeczytał.
    """
    ratios = {}
    for name in AXES:
        triple = BA.radius_stats([(p[0], p[1]) for p in _points(name)])["min_m"]
        chord = _evaluate(name, "box_double", "pessimistic")["min_radius_m"]
        assert triple >= 90.0, (name, triple)
        assert chord < 90.0, (name, chord)
        ratios[name] = triple / chord
    assert max(ratios.values()) - min(ratios.values()) < 0.02, ratios
    for name, value in ratios.items():
        assert 1.85 < value < 1.95, (name, value)
    # Iloraz jest przewidziany przez same długości: krok digitalizacji do pół cięciwy.
    spec = m7_layout.load_spec()
    predicted = 15.0 / (float(spec["length_m"]) / int(spec["cars"]) / 2.0)
    assert abs(predicted - sum(ratios.values()) / len(ratios)) < 0.02, (predicted, ratios)


# --- różnica 7: żadna z sześciu prowieniencji nie nazywa promienia faktem --------

def test_curve_radius_is_never_claimed_as_a_construction_fact_by_provenance():
    """Sześć plików prowieniencji mówi to samo i to jest granica całego tego pomiaru.

    `CLAUDE.md` §4.1: czego nie da się potwierdzić, nie wstawia się jako liczby. Osie
    pochodzą z tras handlowych STIB, a nie z osi toru z pomiaru, więc każdy promień
    w raporcie jest własnością skomitowanej łamanej. Gdyby ktoś kiedyś podmienił oś
    na zmierzoną, to zdanie ma zniknąć z prowieniencji ŚWIADOMIE, a nie po cichu.
    """
    for name in AXES:
        path = os.path.join(ROOT, "data", "track", f"{name}.provenance.json")
        with open(path, encoding="utf-8") as handle:
            document = json.load(handle)
        claims = document["not_derived"]
        assert any("promieni" in line for line in claims), (name, claims)
        assert any("trasy handlowe" in line or "reprezentacją trasy" in line
                   for line in claims), (name, claims)


# --- skan punkt po punkcie ------------------------------------------------------

def test_curve_radius_point_scan_agrees_with_the_worst_arc_verdict():
    """Sprawdzenie punkt po punkcie nie może dać innego werdyktu niż najciaśniejszy łuk.

    `evaluate` liczy `fits_gauge` RAZ, w minimum promienia, i to wystarcza tylko wtedy,
    gdy zapas jest monotoniczny względem promienia. `scan` woła `fits_gauge` osobno
    w każdym punkcie, czyli tej monotoniczności nie zakłada. Zgodność obu dróg na
    sześciu osiach jest jej sprawdzeniem, a nie jej powtórzeniem.
    """
    for name in AXES:
        item = _evaluate(name, "box_double", "pessimistic")
        scanned = _scan(name, "box_double")
        assert scanned["samples"] == item["samples"], (name, scanned, item)
        assert scanned["fits_everywhere"] is item["fits_on_curve"], (name, scanned)
        assert abs(scanned["min_margin_m"] - item["margin_m"]) < 1e-3, (name, scanned)
        assert scanned["min_margin_chainage_m"] == item["min_radius_chainage_m"], name
        assert scanned["failing_samples"] == 0, (name, scanned)


def test_curve_radius_point_scan_names_where_bore_single_runs_out_of_room():
    """Werdykt „nie mieści się" dostaje adres: ile punktów i w jakich przedziałach.

    Sam znak zapasu mówi tylko, że gdzieś jest ciasno. Pakiet A ma 401 punktów i
    11 z nich bez skrajni w `bore_single`, w trzech rozłącznych miejscach — i to jest
    liczba, której `evaluate` nie umie podać, bo ogląda wyłącznie minimum.
    """
    scanned = _scan("L1_A", "bore_single")
    assert scanned["fits_everywhere"] is False, scanned
    assert scanned["failing_samples"] == 11, scanned
    assert scanned["worst_shortfall_m"] < -0.1, scanned
    spans = scanned["failing_spans_m"]
    assert len(spans) == 3, spans
    for low, high in spans:
        assert low <= high, spans
    # Najgłębszy punkt leży w pierwszym przedziale, tym pod Sainte-Catherine.
    assert spans[0][0] <= scanned["min_margin_chainage_m"] <= spans[0][1], (spans, scanned)
    # Ten sam skan na `box_double` tej samej osi nie ma ani jednego takiego punktu —
    # inaczej test mierzyłby oś, a nie profil.
    assert _scan("L1_A", "box_double")["failing_spans_m"] == [], "L1_A"


def _circle(radius, count=300):
    return [(radius * math.cos(math.radians(a)), radius * math.sin(math.radians(a)), 0.0)
            for a in (90.0 * i / count for i in range(count + 1))]


def test_curve_radius_scan_reports_a_shortfall_on_an_arc_tight_enough_to_cause_one():
    """Kierunek odwrotny na geometrii DOBRANEJ do progu, nie znalezionej w sieci.

    Wszystkie sześć osi mieści się w `box_double`, więc bez tego wejścia moduł nigdy
    nie zobaczyłby skanu, który coś odrzuca, i nie odróżniłby „nie ma niedoboru" od
    „nie umiem go zgłosić".

    Para promieni nie jest wzięta z powietrza: przy cięciwie 15,667 m strzałka zjada
    całe 1,078 m zapasu dokładnie przy R = 29,0 m, więc 25 m i 35 m stoją po dwóch
    stronach tej samej, policzonej granicy. Sama granica jest sprawdzona niżej —
    bez tego para mówiłaby „ciasno psuje, luźno nie", czyli nic ponad kierunek.
    """
    chord = _chord()
    static = 1.078
    critical = (chord / 2.0) ** 2 / (2.0 * static) + static / 2.0
    assert 28.0 < critical < 30.0, critical
    assert abs(CL.versine(chord, critical) - static) < 1e-9, critical

    scanned = CL.scan(_circle(25.0), "box_double", chord)
    assert scanned["fits_everywhere"] is False, scanned
    assert scanned["failing_samples"] > 100, scanned
    assert scanned["worst_shortfall_m"] < -0.1, scanned
    assert scanned["min_margin_m"] < 0.0, scanned

    easy = CL.scan(_circle(35.0), "box_double", chord)
    assert easy["fits_everywhere"] is True, easy
    assert easy["failing_spans_m"] == [], easy
    assert easy["min_margin_m"] > 0.0, easy
    assert easy["min_margin_m"] > scanned["min_margin_m"], (easy, scanned)


def test_curve_radius_scan_margin_follows_the_versine_not_the_train_width():
    """Zapas maleje dokładnie o strzałkę cięciwy — pojazd zostaje taki, jaki jest.

    Ta sama reguła co `test_clearance_never_shrinks_the_train_to_make_it_fit`, ale po
    stronie skanu: gdyby `scan` zaczął odejmować cokolwiek innego niż `versine`, sześć
    osi wyżej dalej mieściłoby się w `box_double` i nikt by tego nie zauważył.
    """
    chord = _chord()
    static = CL.margin_at("box_double", chord, 1e9, 0.0)[1]
    assert abs(static) < 1e-3, static
    for radius in (40.0, 60.0, 90.0, 150.0):
        needed, margin, _fits, _msg = CL.margin_at("box_double", chord, radius, 1.078)
        assert abs(needed - CL.versine(chord, radius)) < 1e-12, radius
        assert abs(margin - (1.078 - needed)) < 1e-12, radius
    # Ciaśniejszy łuk zjada więcej zapasu — monotonicznie.
    margins = [CL.margin_at("box_double", chord, r, 1.078)[1]
               for r in (40.0, 60.0, 90.0, 150.0)]
    assert margins == sorted(margins), margins


# --- sklejanie przedziałów ------------------------------------------------------

def test_curve_radius_span_merge_joins_neighbours_and_splits_a_real_gap():
    """Punkty osi dzieli do 22,4 m, więc próg sklejania musi być powyżej tego odstępu.

    Bez sklejania raport podawałby tyle „miejsc bez skrajni", ile jest wierzchołków
    w dołku — jedenaście zamiast trzech w pakiecie A. Próg musi jednak rozdzielać
    dwa naprawdę odległe dołki, inaczej sklei całą oś w jeden przedział.
    """
    assert CL.merge_spans([], 25.0) == []
    assert CL.merge_spans([100.0], 25.0) == [(100.0, 100.0)]
    assert CL.merge_spans([100.0, 115.0, 130.0], 25.0) == [(100.0, 130.0)]
    assert CL.merge_spans([100.0, 120.0, 400.0], 25.0) == [(100.0, 120.0), (400.0, 400.0)]
    # Odstęp WIĘKSZY od progu rozcina nawet trzy punkty stojące blisko siebie.
    assert CL.merge_spans([100.0, 130.0, 160.0], 25.0) == [(100.0, 100.0), (130.0, 130.0),
                                                           (160.0, 160.0)]
    # Kolejność wejścia nie ma znaczenia — sortowanie jest częścią umowy.
    assert CL.merge_spans([400.0, 120.0, 100.0], 25.0) == [(100.0, 120.0), (400.0, 400.0)]
    # Granica progu: odstęp DOKŁADNIE równy progowi jeszcze skleja, większy już nie.
    assert CL.merge_spans([0.0, 25.0], 25.0) == [(0.0, 25.0)]
    assert CL.merge_spans([0.0, 25.5], 25.0) == [(0.0, 0.0), (25.5, 25.5)]


def test_curve_radius_span_gap_is_above_the_largest_point_spacing_of_all_six_axes():
    """Próg sklejania nie jest okrągłą liczbą z sufitu — jest ponad największym odstępem.

    Zmierzone na sześciu osiach: największy odstęp między sąsiednimi wierzchołkami to
    22,4 m. Próg poniżej tej wartości rozcinałby jeden dołek na kilka „miejsc" tam,
    gdzie oś akurat jest rzadziej próbkowana.
    """
    widest = 0.0
    for name in AXES:
        stations = sweep.chainages(_points(name))
        widest = max(widest, max(b - a for a, b in zip(stations, stations[1:])))
    assert widest > 20.0, widest
    assert CL.SPAN_GAP_M > widest, (CL.SPAN_GAP_M, widest)
    assert CL.SPAN_GAP_M < 2.0 * widest, (CL.SPAN_GAP_M, widest)

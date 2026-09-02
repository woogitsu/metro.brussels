#!/usr/bin/env python3
"""Domyślne wartości narzędzi: przypięte do liczby, nie tylko do mechanizmu.

Audyt mutacyjny 02.09.2026 wykazał wspólny wzorzec: to są **domyślne wartości CLI**,
a każdy test podaje wartość jawnie w wywołaniu. Testy sprawdzają więc algorytm i nie
sprawdzają liczby, którą realnie dostaje pipeline. Zmierzone — wszystkie przechodziły
przez pełną suitę:

    NEAREST_MAX_M           60,0  ->  2000,0     klasyfikacja tunel/powierzchnia
    OSM_GRID_CELL_M         50,0  ->  5000,0     indeks przestrzenny snapshotu OSM
    DEFAULT_REFINE_BAND_M   0,050 ->  0,0        doszlifowanie luzu nigdy się nie odpala
    DEFAULT_REFINE_STEP_M   0,25  ->  2,50       j.w., 10x zgrubniej
    STATION_OFFSET_WARN_M   5,0   ->  500,0      ostrzeżenie „stacja daleko od osi"
    UNIFORM_STEP_M          15,0  ->  24,0       oś o 60 % rzadsza, wciąż pod limitem 25 m
    COLLISION_MAX_CHORD_M   25,0  ->  500,0      cięciwa bryły kolizyjnej
    COVERAGE_SAMPLES        2000  ->  5          zakres pokrycia osi z pięciu próbek
    PEAK_HOURS       (7,8,16,17)  ->  (2,3)      takt szczytu liczony dla godzin 2–3 w nocy
    DEFAULT_CONFLICT_M      9,40  ->  0,50       rury 3 m od siebie „bez kolizji"
    PARALLEL_M              30,0  ->  15,5
    CLEARANCE_M             0,30  ->  0,01       skrajnia mniejsza, więc łatwiej „pasuje"
    ALL_AXLES_BRAKED_...     1,0  ->  0,5        górny kres udziału osi hamowanych

Uzasadnienia poniżej są przepisane z komentarzy przy samych stałych — ten plik nie
wprowadza nowych twierdzeń o sieci, tylko odbiera możliwość zmiany liczby po cichu.
Tam, gdzie stała jest WYPROWADZONA z innej wielkości, przypięte jest wyprowadzenie,
a nie liczba: wtedy zmiana profilu pociąga za sobą próg, zamiast go rozjeżdżać.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for package in ("blender", "track", "physics"):
    sys.path.insert(0, os.path.join(ROOT, "tools", package))

import build_alignment as BA  # noqa: E402
import clearance_profile as CP  # noqa: E402
import lod as LOD  # noqa: E402
import network_chainage as NC  # noqa: E402
import placement  # noqa: E402
import profiles  # noqa: E402
import surface_sections as SS  # noqa: E402
import timetable as TT  # noqa: E402


def test_conflict_threshold_is_derived_from_the_tunnel_profile():
    """9,40 m to szerokość `box_double`, a nie okrągła liczba.

    Dwie osie bliżej niż to mają w modelu nachodzące na siebie rury. Przypinam
    WYPROWADZENIE, nie liczbę: przy zmianie profilu próg ma pojechać razem z nim,
    zamiast zostać w tyle.
    """
    width, _height = profiles.dimensions("box_double")
    assert NC.DEFAULT_CONFLICT_M == width, (NC.DEFAULT_CONFLICT_M, width)
    assert NC.PARALLEL_M == 30.0
    assert NC.PARALLEL_M > NC.DEFAULT_CONFLICT_M, "korytarz równoległy musi być szerszy niż konflikt"


def _flat_axis(offset_m, length_m=400.0, count=100):
    """Prosta pozioma oś w kształcie, jakiego oczekuje `network_chainage`."""
    points = [(length_m * i / count, offset_m) for i in range(count + 1)]
    return {
        "document": {
            "package": {"id": "T", "name": "pakiet T", "from": "A", "to": "B"},
            "stations": [],
            "vertical": {"status": "not_modelled"},
            "length_m": None,
        },
        "points": points,
        "chainages": NC.chainages(points),
    }


def test_conflict_detection_reacts_to_the_threshold_two_sided():
    """Sam próg, dwustronnie: 8 m od siebie to konflikt, 12 m już nie.

    Istniejące testy przekazują `NC.DEFAULT_CONFLICT_M` jako argument, więc razem
    z obniżonym progiem obniża się poprzeczka — mutacja 9,40 -> 0,50 przechodziła.
    Ten test podaje odległości jawnie, po obu stronach progu.
    """
    close = {"P": _flat_axis(0.0), "Q": _flat_axis(8.0)}
    apart = {"P": _flat_axis(0.0), "Q": _flat_axis(12.0)}

    near = NC.proximity(close, NC.DEFAULT_CONFLICT_M, NC.PARALLEL_M)
    far = NC.proximity(apart, NC.DEFAULT_CONFLICT_M, NC.PARALLEL_M)
    assert near and near[0]["conflict_points"] > 0, near
    assert far and far[0]["conflict_points"] == 0, far


def test_clearance_margin_is_pinned_and_two_sided():
    """Luz skrajni 0,30 m. Zmniejszenie go czyni test „mieści się w tunelu" trywialnym."""
    assert profiles.CLEARANCE_M == 0.30
    for name in profiles.PROFILES:
        assert profiles.fits_gauge(name)[0], name
    # Skrajnia szersza niż każdy profil nie ma prawa się zmieścić — inaczej
    # `fits_gauge` odpowiada „tak" niezależnie od argumentu.
    assert not profiles.fits_gauge("box_double", clearance=3.0)[0]


def test_tuning_defaults_are_pinned_to_their_stated_values():
    """Reszta domyślnych wartości, z uzasadnieniem przepisanym z komentarza przy stałej."""
    pinned = [
        # sonda dalej niż to od osi opisuje już inną linię, nie ten odcinek
        (SS, "NEAREST_MAX_M", 60.0),
        # komórka indeksu przestrzennego pełnego snapshotu Overpassa
        (SS, "OSM_GRID_CELL_M", 50.0),
        # doszlifowanie luzu wokół dołków: krok i pasmo wyboru dołków
        (CP, "DEFAULT_REFINE_STEP_M", 0.25),
        (CP, "DEFAULT_REFINE_BAND_M", 0.050),
        # krok zgrubny wybrany pomiarem: 5 m i 2 m dają to samo minimum 0,899948 m
        (CP, "DEFAULT_STEP_M", 5.0),
        # krok próbkowania osi; 15 m to jedyny, przy którym wszystkie sześć pakietów
        # mieści się w granicach walidatora (docs/21-measured-vs-assumed.md)
        (BA, "UNIFORM_STEP_M", 15.0),
        (BA, "STATION_OFFSET_WARN_M", 5.0),
        # bryła kolizyjna ma ostrzejszy limit strzałki niż LOD2
        (LOD, "COLLISION_MAX_CHORD_M", 25.0),
        (placement, "COVERAGE_SAMPLES", 2000),
    ]
    wrong = [f"{module.__name__}.{name}: {getattr(module, name)} != {expected}"
             for module, name, expected in pinned
             if getattr(module, name) != expected]
    assert not wrong, wrong

    # Okno POMIARU taktu szczytu, nie twierdzenie o tym, kiedy STIB ma szczyt.
    assert TT.PEAK_HOURS == (7, 8, 16, 17), TT.PEAK_HOURS


def test_collision_chord_is_tighter_than_the_coarsest_visual_lod():
    """Limit kolizji ma zostać OSTRZEJSZY niż najzgrubszy poziom obrazu.

    Komentarz przy stałej mówi wprost dlaczego: błąd kolizji nie jest kosmetyczny.
    Sagitta i inset bryły kolizyjnej są pilnowane osobno, cięciwa nie była.
    """
    coarsest = max(level["max_chord_m"] for level in LOD.LOD_LEVELS)
    assert coarsest > 0.0, LOD.LOD_LEVELS
    assert LOD.COLLISION_MAX_CHORD_M < coarsest, (LOD.COLLISION_MAX_CHORD_M, coarsest)

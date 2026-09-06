#!/usr/bin/env python3
"""Testy `tools/blender/material_specs.py` — modułu, który do 06.09.2026 nie miał
ŻADNEGO pokrycia: cztery bramki tego modułu siedziały wewnątrz `material_test_scene.py`,
tuż obok `import bpy`, a jedyny istniejący test tamtego pliku (`test_art_direction.py`)
czyta go jako TEKST — grepuje źródło, nie importuje go. Żadna z czterech funkcji
nigdy się nie wykonała pod żadnym testem, mimo że żadna z nich nie dotyka Blendera.

Moduł nie importuje `bpy` w ogóle (`tools/blender/material_specs.py` jest jego
własnym docstringiem to potwierdza), więc żadna atrapa tu nie jest potrzebna —
`import material_specs` działa w gołym Pythonie.

Wszystkie cztery są bramkami, nie pomocnikami: odpowiadają „czy wolno iść dalej",
i tak są tu testowane — po granicy, nie po przykładowej wartości.
"""
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import material_specs as MS  # noqa: E402


# --- artefact_is_missing -----------------------------------------------------


def test_missing_file_counts_as_missing():
    assert MS.artefact_is_missing("/nonexistent/path/for/test_material_specs.glb") is True


def test_file_exactly_at_the_threshold_is_still_missing():
    """Granica jest WŁĄCZNA: rozmiar RÓWNY progowi jest jeszcze śmieciem.

    `os.path.getsize(path) <= minimum_bytes` dotknięte DOKŁADNIE w punkcie
    równości — inaczej test nie odróżnia `<=` od `<`.
    """
    with tempfile.NamedTemporaryFile(delete=False) as handle:
        handle.write(b"x" * MS.MINIMUM_ARTEFACT_BYTES)
        path = handle.name
    try:
        assert os.path.getsize(path) == MS.MINIMUM_ARTEFACT_BYTES
        assert MS.artefact_is_missing(path) is True
    finally:
        os.remove(path)


def test_file_one_byte_over_the_threshold_is_not_missing():
    with tempfile.NamedTemporaryFile(delete=False) as handle:
        handle.write(b"x" * (MS.MINIMUM_ARTEFACT_BYTES + 1))
        path = handle.name
    try:
        assert MS.artefact_is_missing(path) is False
    finally:
        os.remove(path)


def test_missing_file_short_circuits_before_touching_its_size():
    """`or` jest tu konieczne, nie `and`. Gdy pliku nie ma, `os.path.getsize`
    wywraca się `FileNotFoundError` — mutacja `or` -> `and` zmusza Pythona do
    policzenia PRAWEJ strony nawet wtedy, gdy lewa już jest prawdziwa, i ta
    funkcja wywróciłaby się zamiast cicho zwrócić `True`.
    """
    path = "/nonexistent/path/for/short/circuit/check.glb"
    assert not os.path.exists(path)
    assert MS.artefact_is_missing(path) is True  # nie podnosi wyjątku


# --- is_transparent ------------------------------------------------------------


def test_fully_opaque_is_not_transparent():
    """Krycie DOKŁADNIE 1,0 jest NIEPRZEZROCZYSTE — granica wyłączna."""
    assert MS.is_transparent({"alpha": 1.0}) is False


def test_alpha_below_one_is_transparent():
    assert MS.is_transparent({"alpha": 0.5}) is True


def test_alpha_between_the_threshold_and_its_shifted_value_stays_opaque():
    """Odróżnia próg `1.0` od przesuniętego `1,01`: wartość MIĘDZY nimi.

    Przy oryginalnym progu 1,0 wartość 1,005 NIE jest mniejsza niż 1,0, więc
    materiał zostaje nieprzezroczysty. Mutacja stałej `1.0` -> `1.01` w
    porównaniu przesunęłaby próg tak, że ta sama wartość wypadłaby jako
    przezroczysta.
    """
    assert MS.is_transparent({"alpha": 1.005}) is False


def test_missing_alpha_key_defaults_to_fully_opaque():
    """Brak klucza `alpha` znaczy pełne krycie, nie przezroczystość.

    **Mutacja argumentu domyślnego `.get("alpha", 1.0)` -> `1.01` jest tu
    RÓWNOWAŻNA, i to jest sprawdzalne bez reszty kodu.** Domyślna wartość
    wchodzi do porównania `< 1.0` WYŁĄCZNIE wtedy, gdy klucza nie ma — a 1,0
    i 1,01 dają dokładnie ten sam wynik tego porównania (`False`, żadna z nich
    nie jest mniejsza niż 1,0). Nie ma żadnego wejścia z brakującym kluczem
    `alpha`, które odróżniłoby te dwie wartości domyślne od siebie; próbowałem
    obu granic (dokładnie 1,0 i tuż nad 1,0) i obie dają `False` po obu
    stronach mutacji. Różnica ujawniłaby się dopiero, gdyby razem z tym
    zmienił się też próg porównania — a to już osobna mutacja, zabita
    testem wyżej.
    """
    assert MS.is_transparent({}) is False
    assert MS.is_transparent({"id": "concrete"}) is False


# --- is_glass ----------------------------------------------------------------


def test_glass_id_matches_exactly():
    assert MS.is_glass({"id": "glass"}) is True


def test_glass_frosted_is_not_plain_glass():
    """Dopasowanie jest po CAŁYM identyfikatorze, nie po fragmencie."""
    assert MS.is_glass({"id": "glass_frosted"}) is False


def test_missing_id_is_not_glass():
    assert MS.is_glass({}) is False


# --- spec_id_problems ----------------------------------------------------------


def _specs(*ids):
    return [{"id": i} for i in ids]


def test_no_problems_when_all_ids_are_distinct_and_present():
    assert MS.spec_id_problems(_specs("concrete", "steel", "glass")) == []


def test_a_duplicate_id_is_named_in_the_message():
    problems = MS.spec_id_problems(_specs("concrete", "concrete", "steel"))
    assert len(problems) == 1
    assert problems[0].endswith("['concrete']"), problems


def test_an_id_seen_only_once_is_never_named_as_a_duplicate():
    """Granica `count(i) > 1` dotknięta wprost, obok id policzonego DWA razy.

    Ten jeden przypadek odróżnia dwie mutacje naraz: `>` -> `>=` dopisałby do
    listy także `steel` (policzony raz); prog `1` -> `2` wymazałby z niej
    `concrete` (policzony dwa razy, ale `2 > 2` jest fałszem).
    """
    problems = MS.spec_id_problems(_specs("concrete", "concrete", "steel"))
    assert problems[0].endswith("['concrete']"), problems


def test_repeated_empty_ids_trigger_the_duplicate_check_but_are_never_named():
    """Puste identyfikatory podnoszą sam TRIGGER (`len(ids) != len(set(ids))`
    liczy dwa puste stringi jak każdą inną parę), ale filtr `and i` w
    wierszu niżej nie pozwala pustemu identyfikatorowi trafić na listę
    NAZWANYCH powtórzeń — komunikat wychodzi z pustą listą, nie z `['']`.
    Mutacja `and` -> `or` wpuściłaby go tam, bo `count(i) > 1` samo w sobie
    już jest prawdą dla dwóch pustych wpisów.
    """
    problems = MS.spec_id_problems(_specs("", "", "steel"))
    duplicate_messages = [p for p in problems if "powtórzone" in p]
    assert len(duplicate_messages) == 1
    assert duplicate_messages[0].endswith(": []"), duplicate_messages


def test_missing_ids_are_counted_separately_from_duplicates():
    problems = MS.spec_id_problems(_specs("steel", "", ""))
    missing = [p for p in problems if "bez identyfikatora" in p]
    assert len(missing) == 1
    assert missing[0].startswith("2 "), missing

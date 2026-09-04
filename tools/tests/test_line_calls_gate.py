#!/usr/bin/env python3
"""Bramka zgodności przejazdu linią: scena Godota wobec rdzenia.

`tools/ci/assert_line_calls_match.py` porównuje dwa pliki zatrzymań. Bramka bez testów
jest w tym repozytorium bramką-atrapą, więc czysta funkcja `compare` ma je tutaj —
i to obie strony: musi milczeć na zgodnych wejściach i musi wołać na każdej różnicy,
którą deklaruje, że łapie.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "ci"))

import assert_line_calls_match as GATE  # noqa: E402


def _row(name="Beekkant", stop_id="8742", chainage="509.73", stopped="509.4267",
         error="-0.3033", arrival="45.975", departure="62.4833"):
    return {"name": name, "stop_id": stop_id, "chainage_m": chainage,
            "stopped_at_m": stopped, "stop_error_m": error,
            "arrival_s": arrival, "departure_s": departure}


def test_line_gate_is_silent_on_identical_calls():
    rows = [_row(), _row(name="Parc", stop_id="8022", chainage="4075.66")]
    assert GATE.compare(rows, [dict(r) for r in rows]) == []


def test_line_gate_catches_a_different_number_of_calls():
    problems = GATE.compare([_row()], [_row(), _row(name="Parc")])
    assert problems and "zatrzymań" in problems[0], problems


def test_line_gate_catches_a_millimetre_in_any_numeric_column():
    """Próg jest ZEROWY, więc milimetr musi wystarczyć — w KAŻDEJ kolumnie osobno.

    Bez pętli po kolumnach test sprawdzałby jedną z pięciu i mówił „ok" o pozostałych
    czterech. To ta sama usterka, co bramka porównująca listę z samą sobą.
    """
    for column in GATE.NUMERIC_COLUMNS:
        core = [_row()]
        scene = [dict(core[0])]
        scene[0][column] = repr(float(core[0][column]) + 0.001)
        problems = GATE.compare(core, scene)
        assert problems, f"{column}: różnica 1 mm przeszła"
        assert any(column in p for p in problems), (column, problems)


def test_line_gate_catches_a_swapped_station_name_and_id():
    for column, value in (("name", "Parc"), ("stop_id", "9999")):
        core = [_row()]
        scene = [dict(core[0])]
        scene[0][column] = value
        problems = GATE.compare(core, scene)
        assert problems and any(column in p for p in problems), (column, problems)


def test_line_gate_refuses_a_run_with_no_calls_at_all():
    """Zero zatrzymań po obu stronach jest ZGODNE i właśnie dlatego musi być błędem.

    Przebieg, który nie zatrzymał się nigdzie, przechodziłby porównanie kolumna
    w kolumnę — nie ma czego porównywać. To jest dokładnie kształt bramki, która
    mówi „ok", bo nic nie sprawdza.
    """
    problems = GATE.compare([], [])
    assert problems and "zero zatrzymań" in problems[0], problems


def test_line_gate_checks_the_expected_count_of_calls():
    """Pakiet A ma 12 stacji, czyli 11 wywołań — pierwsza jest punktem startowym.

    Bez tego argumentu bramka przepuściłaby przebieg, w którym oba przebiegi
    zatrzymały się na JEDNEJ stacji zgodnie i zakończyły się kodem zero.
    """
    rows = [_row(name=f"S{i}", stop_id=str(i)) for i in range(11)]
    assert GATE.compare(rows, [dict(r) for r in rows], expect_calls=11) == []

    problems = GATE.compare(rows[:1], [dict(rows[0])], expect_calls=11)
    assert problems and "oczekiwano 11" in problems[0], problems


def test_line_gate_is_wired_into_the_workflow_that_needs_it():
    """Bramka nie wołana z CI jest plikiem, nie bramką.

    Ta sama reguła co dla pozostałych bramek tego repozytorium: skrypt istnieje po to,
    żeby przebieg CI się na nim wywrócił, a nie żeby leżał w `tools/ci/`.
    """
    with open(os.path.join(ROOT, ".github", "workflows", "godot-first-run.yml"),
              encoding="utf-8") as handle:
        workflow = handle.read()
    assert "assert_line_calls_match.py" in workflow
    assert "--line --limit-kmh=70" in workflow, (
        "workflow nie podaje limitu jawnie — a bez tego scena bierze prędkość "
        "KONSTRUKCYJNĄ M7 (80 km/h) i przejazd nie zgadza się z rdzeniem")
    assert "--expect-calls 11" in workflow

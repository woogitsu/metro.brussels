#!/usr/bin/env python3
"""Audyt wymiarów: żaden parametr geometrii nie może istnieć bez wpisu w dokumencie.

Reguła 1 z `CLAUDE.md` mówi, żeby nie zgadywać danych o sieci. Egzekwowanie tego przez
dobre chęci nie działa — zmyślona głębokość stacji wygląda dokładnie tak samo jak
prawdziwa. Ten test pilnuje, żeby każda stała, na której stoi geometria, była wypisana
w `docs/21-measured-vs-assumed.md` razem ze statusem. Dopisanie parametru bez wpisu
wywraca testy, więc autor musi świadomie zadeklarować, czy to fakt, czy decyzja.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import m7_layout  # noqa: E402
import profiles  # noqa: E402
import station_components  # noqa: E402
import sweep  # noqa: E402

AUDIT = os.path.join(ROOT, "docs", "21-measured-vs-assumed.md")
STATUSES = ("spec", "observed", "design_assumption", "blocked")


def _audit_text():
    with open(AUDIT, encoding="utf-8") as handle:
        return handle.read()


def test_audit_document_exists_and_defines_every_status():
    text = _audit_text()
    for status in STATUSES:
        assert f"`{status}`" in text, status


def test_audit_covers_every_m7_design_constant():
    text = _audit_text()
    constants = [n for n in dir(m7_layout)
                 if n.startswith("DESIGN_") and n != "DESIGN_ASSUMPTIONS"]
    assert len(constants) >= 10, constants
    missing = [n for n in constants if n not in text]
    assert not missing, f"stałe bez wpisu w audycie: {missing}"


def test_audit_covers_every_m7_spec_key():
    text = _audit_text()
    spec = m7_layout.load_spec()
    numeric = {k: v for k, v in spec.items() if isinstance(v, (int, float))}
    missing = [k for k, v in numeric.items() if _format(v) not in text]
    assert not missing, f"wartości ze specyfikacji bez wpisu: {missing}"


def test_audit_covers_every_tunnel_profile_with_its_size():
    text = _audit_text()
    for name in profiles.PROFILES:
        assert f"`{name}`" in text, name
        width, height = profiles.dimensions(name)
        pair = f"{_dimension(width)} × {_dimension(height)} m"
        assert pair in text, f"{name}: brak wymiarów {pair} w audycie"


def test_audit_covers_every_sweep_constant():
    text = _audit_text()
    names = [n for n in dir(sweep)
             if n.startswith("DEFAULT_") or n in ("UV_METRES_PER_UNIT", "DEGENERATE_AREA_M2")]
    assert len(names) >= 6, names
    missing = [n for n in names if n not in text]
    assert not missing, f"stałe generatora bez wpisu: {missing}"


def test_audit_marks_profiles_as_design_not_measurement():
    """Profile są projektowe. Audyt musi to mówić wprost, a kod się z tym zgadzać."""
    text = _audit_text()
    for name, spec in profiles.PROFILES.items():
        assert spec["source_level"] == "design", name
    assert "Żaden nie jest pomiarem STIB" in text


def test_audit_records_the_measured_alternatives_that_were_not_applied():
    """Zmierzone alternatywy mają być wypisane RAZEM z powodem, dla którego nie weszły."""
    text = _audit_text()
    for marker in ("8,77", "3,294", "R-005"):
        assert marker in text, marker
    assert profiles.PROFILES["box_double"]["track_offsets"] == [-2.10, 2.10], \
        "rozstaw zmieniony w kodzie — audyt trzeba zaktualizować razem ze zmianą"
    width, _height = profiles.dimensions("box_double")
    assert abs(width - 9.40) < 1e-9, \
        "szerokość profilu zmieniona — audyt trzeba zaktualizować razem ze zmianą"


def test_audit_lists_what_is_blocked_and_by_what():
    text = _audit_text()
    for marker in ("T-112", "R-004", "R-005", "flat-preview"):
        assert marker in text, marker


def _row(text, name):
    """Wiersz tabeli audytu opisujący daną stałą, albo None."""
    for line in text.splitlines():
        if line.startswith("|") and f"`{name}`" in line.split("|")[1]:
            return [cell.strip() for cell in line.strip("|").split("|")]
    return None


def _documented_value(cell):
    """Druga kolumna wiersza jako liczba albo wartość logiczna.

    Dokument zapisuje liczby po polsku i z jednostką, w różnej liczbie miejsc
    po przecinku (`2,40 m`, `5,0 m`, `1e-06`), więc porównanie idzie po WARTOŚCI,
    a nie po napisie — inaczej test wywracałby się na formatowaniu zamiast
    na rozjeździe kodu z dokumentem.
    """
    raw = cell.replace("`", "").replace("\u00a0", " ").strip()
    if raw in ("True", "False"):
        return raw == "True"
    raw = raw.split(" ")[0].replace(",", ".")
    return float(raw)


def _assert_values_match(text, module, names):
    mismatched = []
    for name in names:
        row = _row(text, name)
        assert row is not None, f"brak wiersza dla {name} w audycie"
        assert len(row) >= 2, (name, row)
        expected = getattr(module, name)
        found = _documented_value(row[1])
        if isinstance(expected, bool) or isinstance(found, bool):
            if bool(expected) != bool(found):
                mismatched.append(f"{name}: kod {expected}, audyt {found}")
        elif abs(float(found) - float(expected)) > 1e-12:
            mismatched.append(f"{name}: kod {expected}, audyt {found}")
    assert not mismatched, mismatched


def test_audit_records_the_value_of_every_m7_design_constant():
    """Nie tylko NAZWA stałej ma być w dokumencie, ale jej WARTOŚĆ.

    Zmierzone 02.09.2026 audytem mutacyjnym: `DESIGN_NOSE_LENGTH_M` 2,40 -> 6,00,
    `DESIGN_SHELL_THICKNESS_M` 0,08 -> 0,50 i pięć innych przechodziło przez całą
    suitę, bo test szukał w dokumencie samej nazwy. Docstring tego pliku mówi
    wprost, po co on jest — „zmyślona głębokość stacji wygląda dokładnie tak samo
    jak prawdziwa" — a w tej postaci pozwalał kodowi i dokumentowi rozjechać się
    co do liczby. Dla profili tuneli było to zrobione dobrze od początku
    (`test_audit_covers_every_tunnel_profile_with_its_size`); asymetria była
    przypadkowa.
    """
    text = _audit_text()
    names = [n for n in dir(m7_layout)
             if n.startswith("DESIGN_") and n != "DESIGN_ASSUMPTIONS"]
    assert len(names) >= 10, names
    _assert_values_match(text, m7_layout, names)


def test_audit_records_the_value_of_every_sweep_constant():
    """To samo dla domyślnych wartości generatora tuneli.

    Te stałe są domyślnymi wartościami CLI, a każdy test podaje wartość jawnie
    w wywołaniu — więc testują algorytm, ale nie liczbę, którą realnie dostaje
    pipeline. Zmierzone: `DEFAULT_RING_STEP_M` 5,0 -> 50,0,
    `DEFAULT_STATION_HALO_M` 90,0 -> 5,0, `DEFAULT_MIN_CHUNK_M` 120 -> 1,
    `DEFAULT_MAX_CHUNK_M` 800 -> 80000, `UV_METRES_PER_UNIT` 4,0 -> 40,0 —
    wszystkie przechodziły.
    """
    text = _audit_text()
    names = [n for n in dir(sweep)
             if n.startswith("DEFAULT_") or n in ("UV_METRES_PER_UNIT", "DEGENERATE_AREA_M2")]
    assert len(names) >= 6, names
    _assert_values_match(text, sweep, names)


def _dimension(value):
    """Wymiary profili zapisujemy w dokumencie z dwoma miejscami, po polsku."""
    return f"{value:.2f}".replace(".", ",")


def _format(value):
    """Liczby w dokumencie są zapisane po polsku, z przecinkiem dziesiętnym."""
    if isinstance(value, float) and value != int(value):
        return f"{value}".replace(".", ",")
    return str(int(value)) if isinstance(value, float) else str(value)


def test_audit_covers_every_station_component_constant():
    """Stała projektowa bez wpisu w audycie jest liczbą, która udaje pomiar.

    T-212 dokłada siedemnaście takich stałych naraz — schody, winda, antresola,
    korytarz, portal — i żadna nie ma źródła. To jest dokładnie ta sytuacja, dla
    której audyt powstał: dużo liczb naraz, wszystkie brzmiące rozsądnie, żadna
    nie pochodząca ze STIB.
    """
    text = _audit_text()
    constants = [n for n in dir(station_components)
                 if n.startswith("DESIGN_") and n != "DESIGN_ASSUMPTIONS"]
    assert len(constants) >= 15, constants
    missing = [n for n in constants if f"`{n}`" not in text]
    assert not missing, f"stałe T-212 bez wpisu w audycie: {missing}"
    assert "design_assumption" in text

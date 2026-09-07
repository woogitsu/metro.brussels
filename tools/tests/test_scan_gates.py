#!/usr/bin/env python3
"""Testy bramek skanu luzu (`tools/blender/scan_gates.py`).

Powód powstania ten sam co przy `test_marker_gates.py` i `test_material_specs.py`:
trzy predykaty siedziały w `main()` z `profile_vehicle.py`, obok `import bpy`
na poziomie modułu, i przemiatanie mutacyjne liczyło je jako nieosiągalne, mimo
że żaden nie woła Blendera. `reports/bpy-extraction-round-3.md` mierzy dokładnie
te trzy miejsca.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import scan_gates as SG  # noqa: E402


# --- should_refine -----------------------------------------------------------

def test_refine_runs_for_a_positive_step():
    assert SG.should_refine(0.5) is True


def test_refine_is_off_at_exactly_zero():
    """Granica jest WYŁĄCZNA: `--refine-step 0` jest udokumentowaną drogą wyłączenia."""
    assert SG.should_refine(0.0) is False


def test_refine_is_off_below_zero():
    assert SG.should_refine(-1.0) is False


def test_a_tiny_positive_step_still_refines():
    """Odróżnia próg `> 0.0` od `> 0.001` — 0,0005 jest dodatnie, więc ma włączyć etap."""
    assert SG.should_refine(0.0005) is True


# --- should_verify -------------------------------------------------------------

def test_verify_runs_for_a_positive_count():
    assert SG.should_verify(3) is True


def test_verify_is_off_at_exactly_zero():
    """Granica jest WYŁĄCZNA: `--verify-full 0` wyłącza kosztowną kontrolę naiwną."""
    assert SG.should_verify(0) is False


def test_verify_is_off_below_zero():
    assert SG.should_verify(-1) is False


def test_count_of_exactly_one_still_verifies():
    """Odróżnia próg `> 0` od `> 1` — jedna pozycja kontrolna to już dodatnia liczba."""
    assert SG.should_verify(1) is True


# --- is_not_vehicle_tag --------------------------------------------------------

def test_vehicle_tag_is_excluded():
    assert SG.is_not_vehicle_tag("vehicle") is False


def test_tunnel_tag_is_kept():
    assert SG.is_not_vehicle_tag("tunnel") is True


def test_missing_tag_is_kept():
    """`obj.get(...)` na braku znacznika wraca `None` — to NIE jest pojazd."""
    assert SG.is_not_vehicle_tag(None) is True


def test_match_is_exact_not_a_prefix():
    """`"vehicle_debug"` zaczyna się tym samym słowem, ale nie jest pojazdem z `import_glb`."""
    assert SG.is_not_vehicle_tag("vehicle_debug") is True

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

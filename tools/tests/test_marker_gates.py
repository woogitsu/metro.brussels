#!/usr/bin/env python3
"""Testy `tools/blender/marker_gates.py` — modułu wyciągniętego spod `bpy`
w #276 (`reports/bpy-extraction-round-2.md`).

**Pomiar, nie przypuszczenie.** Wszystkie trzy funkcje tego modułu
`detail_markers.py` przypisuje pod STARE nazwy — `select_marks = MG.select_marks`
i tak dalej — więc to jest DOKŁADNIE ten sam obiekt funkcji, który
`tools/tests/test_detail_markers.py` woła jako `DM.select_marks`, `DM.side_sign`,
`DM.clearance_problems`. Pierwsze podejrzenie było, że próg `clearance_problems`
(`worst_gauge_m < 0.0` / `worst_wall_m < 0.0`) ma dziurę: żadne wywołanie w
`test_detail_markers.py` nie podaje wartości MIĘDZY `0.0` a `0.001`, więc
mutacja stałej `0.0` -> `0.001` wyglądała na nietkniętą. Pomiar (**przed**
dopisaniem czegokolwiek do tego pliku, `reports/mutation-triage-round-2-modules.md`
§2) pokazał, że to podejrzenie było błędne: `test_zero_clearance_is_still_allowed_
but_a_hair_below_is_not` wywołuje `DM.clearance_problems(0.0, 0.0, ...) == []` —
punkt DOKŁADNIE na granicy — a przesunięty próg `0.001` łapie już samo `0.0` jako
naruszenie i psuje to konkretne porównanie. Wszystkie dziewięć mutacji tego
modułu ginie dziś przez `test_detail_markers.py`, zero nowych zabić stąd.

Ten plik nie zamyka więc żadnej dziury — daje modułowi jeden test, który
importuje go PO NAZWIE (`import marker_gates as MG`), zamiast wyłącznie przez
alias w `detail_markers.py`. To jest cała jego rola.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import marker_gates as MG  # noqa: E402


def test_a_gauge_clearance_just_under_a_millimetre_is_not_a_problem():
    """Charakteryzacja progu, wywołana wprost na module, nie przez alias."""
    assert MG.clearance_problems(0.0005, 0.0, "box_double") == []


def test_a_wall_clearance_just_under_a_millimetre_is_not_a_problem():
    assert MG.clearance_problems(0.0, 0.0005, "box_double") == []


def test_select_marks_and_side_sign_are_the_same_objects_detail_markers_calls():
    """Kontrola, że alias w `detail_markers.py` naprawdę wskazuje NA TEN moduł —
    bez tego cały argument „to ten sam obiekt funkcji" byłby twierdzeniem bez
    dowodu.
    """
    sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))
    import types
    if "bpy" not in sys.modules:
        stub = types.ModuleType("bpy")
        stub.ops = types.SimpleNamespace()
        stub.data = types.SimpleNamespace(objects=[], meshes=None)
        stub.context = types.SimpleNamespace()
        sys.modules["bpy"] = stub
    import detail_markers as DM
    assert DM.select_marks is MG.select_marks
    assert DM.side_sign is MG.side_sign
    assert DM.clearance_problems is MG.clearance_problems

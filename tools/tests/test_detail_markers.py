#!/usr/bin/env python3
"""Testy `tools/blender/detail_markers.py` — modułu, który do 02.09.2026 nie miał
ŻADNEGO pokrycia: ani testu, ani wywołania w `tools/ci/`, ani w `.github/workflows/`.
Jedynym śladem po nim był raport `reports/T-011-detail-markers.md`.

To jest niebezpieczne akurat tutaj, bo moduł nosi **cztery jawne założenia
projektowe** (strona osi, odsunięcie, rzędna podstawy, przekrój słupka) i sam
deklaruje, że są „sprawdzane, nie tylko zadeklarowane".

Konwencja jak w `test_blender_cli.py`: atrapa `bpy` wpuszcza import, a testowane
są wyłącznie funkcje liczące bez silnika. Zamiatanie i eksport GLB weryfikuje
Blender w CI.
"""
import contextlib
import io as _io
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

if "bpy" not in sys.modules:
    _bpy = types.ModuleType("bpy")
    _bpy.ops = types.SimpleNamespace()
    _bpy.data = types.SimpleNamespace(objects=[], meshes=None)
    _bpy.context = types.SimpleNamespace()
    sys.modules["bpy"] = _bpy

import detail_markers as DM  # noqa: E402


def _marks(*chainages):
    return [{"chainage_m": float(c), "kind": "hectometre"} for c in chainages]


def test_the_three_kinds_have_three_distinct_heights():
    """Render kontrolny jest w SKALI SZARYCH — rodzaje muszą różnić się kształtem.

    Docstring modułu mówi to wprost: wysokości są różne, żeby rodzaje dało się
    rozróżnić na renderze BEZ koloru. Gdyby dwie się zrównały, znacznik hamowania
    wyglądałby na renderze identycznie jak hektometrowy i nikt by nie zauważył.
    """
    heights = DM.DEFAULT_HEIGHTS_M
    assert set(heights) == {"hectometre", "brake", "station"}, sorted(heights)
    assert len(set(heights.values())) == 3, heights
    assert all(h > 0.0 for h in heights.values()), heights


def test_station_sign_is_the_tallest_and_hectometre_the_shortest():
    """Porządek wysokości jest informacją, nie przypadkiem: tabliczka stacyjna ma
    być widoczna z najdalsza, słupek hektometrowy jest najniższy."""
    h = DM.DEFAULT_HEIGHTS_M
    assert h["station"] > h["brake"] > h["hectometre"], h


def test_marker_chord_is_short_but_never_zero():
    """`place_spans` odrzuca cięciwę zerowej długości, a długa cięciwa przestawia
    słupek ukośnie do osi zamiast stycznie."""
    assert 0.0 < DM.MARKER_CHORD_M <= 1.0, DM.MARKER_CHORD_M


def test_post_cross_section_is_a_rectangle_with_positive_sides():
    thick_m, wide_m = DM.DEFAULT_POST_M
    assert thick_m > 0.0 and wide_m > 0.0, DM.DEFAULT_POST_M
    assert thick_m < wide_m, "słupek ma być węższy wzdłuż osi niż w poprzek"


# --- okno kilometrażu ------------------------------------------------------------

def test_window_without_bounds_takes_every_mark():
    selected, low, high = DM.select_marks(_marks(0, 500, 5000), None, None)
    assert len(selected) == 3
    assert low == float("-inf") and high == float("inf")


def test_window_keeps_both_ends_inclusive():
    selected, _low, _high = DM.select_marks(_marks(100, 200, 300), 100.0, 300.0)
    assert [m["chainage_m"] for m in selected] == [100.0, 200.0, 300.0]


def test_window_drops_marks_outside_it():
    selected, _low, _high = DM.select_marks(_marks(0, 100, 200, 5000), 50.0, 250.0)
    assert [m["chainage_m"] for m in selected] == [100.0, 200.0]


def test_reversed_window_is_an_error_not_an_empty_list():
    """Odwrócone granice to pomyłka wołającego. Cicha pusta lista dałaby pustą scenę
    zapisaną jako poprawny GLB — dokładnie ten błąd, przed którym broni CLAUDE.md §5.
    """
    try:
        DM.select_marks(_marks(100), 300.0, 200.0)
    except SystemExit as exc:
        assert "puste" in str(exc), exc
    else:
        raise AssertionError("odwrócone okno przeszło")


def test_window_with_no_marks_inside_is_an_error():
    try:
        DM.select_marks(_marks(0, 100), 4000.0, 5000.0)
    except SystemExit as exc:
        assert "ani jednego znacznika" in str(exc), exc
    else:
        raise AssertionError("puste okno przeszło")


# --- domyślne wartości CLI, czyli to, co realnie dostaje pipeline ------------------

def _parse(*extra):
    saved = sys.argv
    sys.argv = ["detail_markers.py", "--", "--axis", "a", "--layout", "b",
                "--out", "c", *extra]
    try:
        with contextlib.redirect_stderr(_io.StringIO()):
            return DM.parse_args()
    finally:
        sys.argv = saved


def test_cli_defaults_are_the_declared_assumptions():
    """Te cztery liczby to ZAŁOŻENIA wypisywane przy każdym uruchomieniu. Każdy inny
    test podawał je jawnie w wywołaniu, więc domyślne nie były sprawdzane przez nic —
    a to one trafiają do pipeline'u."""
    args = _parse()
    assert args.side == "right"
    assert args.offset_m == 2.10
    assert args.foot_m == -0.10
    assert args.profile == "box_double"
    assert args.from_m is None and args.to_m is None


def test_cli_rejects_a_side_that_is_not_a_side():
    saved = sys.argv
    sys.argv = ["detail_markers.py", "--", "--axis", "a", "--layout", "b",
                "--out", "c", "--side", "gdzieś"]
    try:
        with contextlib.redirect_stderr(_io.StringIO()):
            DM.parse_args()
    except SystemExit:
        pass
    else:
        raise AssertionError("--side przyjął wartość spoza left/right")
    finally:
        sys.argv = saved

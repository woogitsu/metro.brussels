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
import math
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


# --- granice, dopisane 03.09.2026 po przemiataniu mutacyjnym ----------------
#
# Przemiatanie dało dla `detail_markers.py` 8 mutacji i 6 ocalałych. Jedna z nich
# leżała w `select_marks`, czyli w funkcji, którą ten plik już testował — ale żaden
# test nie dotykał jej GRANICY. Pozostałe siedziały w `main()`, za `bpy.ops`,
# i te zostały wyjęte na poziom modułu (`side_sign`, `clearance_problems`);
# nowego modułu nie trzeba, bo atrapa `bpy` i tak wpuszcza import.


def test_single_point_window_keeps_a_mark_standing_exactly_on_it():
    """Okno o zerowej szerokości jest poprawne, jeśli znacznik stoi dokładnie na nim.

    `low > high` kontra `low >= high` różnią się WYŁĄCZNIE w punkcie `low == high`,
    a istniejący `test_reversed_window_is_an_error_not_an_empty_list` podaje okno
    odwrócone, czyli mija tę granicę — i dlatego mutacja tam przeżyła.

    Granica jest tu dokładna bez żadnych zabiegów: ta sama liczba idzie jako oba
    końce okna, więc porównanie stoi na równości bit w bit. `--from-m 500
    --to-m 500` to realne wywołanie: wybiera hektometr stojący na 500 m.
    """
    marks = [{"chainage_m": 400.0, "kind": "hectometre"},
             {"chainage_m": 500.0, "kind": "hectometre"},
             {"chainage_m": 600.0, "kind": "hectometre"}]
    selected, low, high = DM.select_marks(marks, 500.0, 500.0)
    assert low == high == 500.0
    assert [m["chainage_m"] for m in selected] == [500.0], selected


def test_single_point_window_with_nothing_on_it_is_an_error():
    """Druga strona tej samej granicy: okno zerowej szerokości bez znacznika odmawia.

    Bez tego przypadku test wyżej sprawdzałby tylko, że okno zerowej szerokości
    czegoś nie odrzuca — a nie że odrzuca wtedy, gdy powinno.
    """
    marks = [{"chainage_m": 400.0, "kind": "hectometre"}]
    try:
        DM.select_marks(marks, 500.0, 500.0)
    except SystemExit as err:
        assert "nie ma ani jednego znacznika" in str(err), err
    else:
        raise AssertionError("puste okno jednopunktowe przeszło")


def test_side_sign_maps_the_word_to_the_sign():
    assert DM.side_sign("right") == 1.0
    assert DM.side_sign("left") == -1.0


def test_side_sign_refuses_anything_that_is_not_a_side():
    """Poprzedni kod odpowiadał „lewa" na KAŻDĄ wartość różną od „right".

    Strona osi jest jednym z czterech założeń projektowych tego modułu, a moduł
    sam deklaruje, że są „sprawdzane, nie tylko zadeklarowane". Cicha odpowiedź
    „lewa" na literówkę postawiłaby wszystkie słupki po drugiej stronie toru —
    geometria wyszłaby poprawna, więc żadna kontrola tego nie widzi.
    """
    for bad in ("Right", "RIGHT", "prawa", "", None):
        try:
            DM.side_sign(bad)
        except ValueError as err:
            assert "'right' albo 'left'" in str(err), (bad, err)
        else:
            raise AssertionError(f"side_sign({bad!r}) nie odmówiło")


def test_zero_clearance_is_still_allowed_but_a_hair_below_is_not():
    """Granica luzu dotknięta DOKŁADNIE: zero przechodzi, o jeden bit mniej nie.

    Zero jest tu granicą, a nie przypadkiem brzegowym — słupek stykający się ze
    skrajnią jeszcze się w niej nie znajduje. Dokładność bierze się stąd, że zero
    jest wpisane wprost, a nie policzone: `abs(0.0 - 0.0)` nie ma czego zaokrąglić.
    Naiwny test podający „tuż poniżej zera" jako `-0.01` nie odróżniłby `<` od `<=`.
    """
    assert DM.clearance_problems(0.0, 0.0, "box_double") == []

    below = math.nextafter(0.0, -math.inf)
    problems = DM.clearance_problems(below, 0.0, "box_double")
    assert any("skrajnię pojazdu" in p for p in problems), problems
    problems = DM.clearance_problems(0.0, below, "box_double")
    assert any("ścianę profilu" in p for p in problems), problems


def test_both_clearances_are_reported_and_named_separately():
    """Dwa różne luzy to dwa różne zarzuty i dwie różne podpowiedzi.

    Skrajnia pojazdu każe ZWIĘKSZYĆ odsunięcie, ściana tunelu ZMNIEJSZYĆ — więc
    zlanie ich w jeden komunikat kazałoby zgadywać, w którą stronę przesunąć słupek.
    """
    problems = DM.clearance_problems(-0.25, -0.5, "box_double")
    assert len(problems) == 2, problems
    assert "0.250" in problems[0] and "zwiększ --offset-m" in problems[0]
    assert "0.500" in problems[1] and "zmniejsz --offset-m" in problems[1]
    assert "box_double" in problems[1], "komunikat ma nazwać profil, którego dotyczy"


def test_clearance_problem_order_is_stable_because_it_becomes_an_error_message():
    assert DM.clearance_problems(-1.0, 0.0, "x")[0].startswith("słupek wchodzi")
    assert DM.clearance_problems(0.0, -1.0, "x")[0].startswith("słupek przebija")

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

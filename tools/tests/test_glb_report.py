#!/usr/bin/env python3
"""Testy werdyktu round-tripu GLB (`tools/blender/glb_report.py`).

Powód powstania ten sam co przy `test_tunnel_manifest.py`, `test_m7_report.py`
i `test_profile_scan.py`: przemiatanie mutacyjne z 03.09.2026 dało dla
`glb_roundtrip.py` 10 mutacji i 10 ocalałych — 100 %, i nie z braku testów,
tylko z braku drogi. Moduł importuje `bpy`, więc `test_all.py` nie umiał go
zaimportować, a poza zasięgiem leżała cała bramka odpowiadająca na pytanie,
czy wyeksportowany plik da się wczytać z powrotem.

Każdy test progu **dotyka granicy**, a nie okolic granicy. Dwie drogi, obie
wypisane w docstringach: albo jedna strona różnicy jest zerem (`abs(0.01-0.0)`
jest dokładnie `0.01`), albo wartość graniczna jest **odczytana z modułu**
(`vertex_ceiling`), zamiast wpisana z ręki. Naiwne `próg + 0.01` nie działa:
`abs((6700.0 + 0.01) - 6700.0)` to 0.010000000000218, czyli NAD progiem, więc
taki test przechodzi identycznie dla `>` i dla `>=` i nie bramkuje niczego.
"""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import glb_report as GR  # noqa: E402


def _expected(bbox=(10.0, 5.0, 3.0), vertices=100, faces=50):
    return {"bbox_size_m": list(bbox), "vertices": vertices, "faces": faces}


# --- składanie bboxa --------------------------------------------------------

def test_glb_bbox_spans_every_group_not_just_the_first():
    """Bbox jest wspólny dla wszystkich obiektów. Jeden obiekt = jeden chunk tunelu."""
    lo, hi = GR.bbox_from_corners([
        [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)],
        [(-5.0, 2.0, 0.5), (3.0, 9.0, 0.5)],
    ])
    assert lo == [-5.0, 0.0, 0.0], lo
    assert hi == [3.0, 9.0, 1.0], hi


def test_glb_bbox_of_nothing_is_infinite_not_zero():
    """Pusta scena musi wyjść jako `inf`, żeby `finite_bbox` ją złapała.

    Zero byłoby kłamstwem nie do odróżnienia od obiektu w początku układu.
    """
    lo, hi = GR.bbox_from_corners([])
    assert lo == [math.inf] * 3
    assert hi == [-math.inf] * 3
    assert GR.finite_bbox(lo, hi) is False


def test_glb_bbox_reads_all_three_axes():
    """Mutacja `range(3)` -> `range(2)` zostawiłaby Z nietknięte, czyli w `inf`."""
    lo, hi = GR.bbox_from_corners([[(1.0, 2.0, 3.0)]])
    assert lo == [1.0, 2.0, 3.0] and hi == [1.0, 2.0, 3.0]
    assert GR.bbox_size(lo, hi) == [0.0, 0.0, 0.0]


def test_glb_finite_bbox_rejects_nan_and_infinity_on_any_axis():
    assert GR.finite_bbox([0.0, 0.0, 0.0], [1.0, 1.0, 1.0]) is True
    for bad in (float("nan"), math.inf, -math.inf):
        assert GR.finite_bbox([0.0, 0.0, bad], [1.0, 1.0, 1.0]) is False, bad
        assert GR.finite_bbox([0.0, 0.0, 0.0], [bad, 1.0, 1.0]) is False, bad


def test_glb_bbox_size_subtracts_in_the_right_order():
    """Odwrócona różnica dałaby ujemny rozmiar, który potem porównuje się z metrykami."""
    assert GR.bbox_size([-2.0, 0.0, 1.0], [3.0, 4.0, 1.5]) == [5.0, 4.0, 0.5]


# --- puste wyjście ----------------------------------------------------------

def test_glb_empty_geometry_is_reported_for_either_count_at_zero():
    """`vertices == 0 or faces == 0` — mutacja `or` -> `and` przepuściłaby jedno z dwóch."""
    assert "geometria pusta po imporcie" in GR.roundtrip_problems(1, 0, 50, [], [1, 1, 1])
    assert "geometria pusta po imporcie" in GR.roundtrip_problems(1, 100, 0, [], [1, 1, 1])
    assert GR.roundtrip_problems(1, 1, 1, [], [1, 1, 1]) == []


def test_glb_one_vertex_and_one_face_is_not_empty():
    """Granica pustki: 0 to pustka, 1 to już nie. Odróżnia `== 0` od `<= 0` i `< 1`."""
    assert GR.roundtrip_problems(1, 1, 1, [], [1, 1, 1]) == []


# --- UV ---------------------------------------------------------------------

def test_glb_missing_uv_is_a_problem_unless_explicitly_allowed():
    """Skorupa M7 nie ma UV i ma prawo nie mieć; tunel ich wymaga."""
    problems = GR.roundtrip_problems(1, 10, 5, ["M7_shell"], [1, 1, 1])
    assert any("bez UV" in p and "M7_shell" in p for p in problems), problems
    assert GR.roundtrip_problems(1, 10, 5, ["M7_shell"], [1, 1, 1],
                                 allow_missing_uv=True) == []


def test_glb_empty_uv_list_is_not_a_missing_uv_complaint():
    """Pusta lista jest falsy i musi zostać ciszą, nie zarzutem o puste UV."""
    assert GR.roundtrip_problems(1, 10, 5, [], [1, 1, 1]) == []


# --- liczba obiektów --------------------------------------------------------

def test_glb_object_count_must_match_exactly_when_declared():
    assert GR.roundtrip_problems(12, 10, 5, [], [1, 1, 1], expect_objects=12) == []
    for actual in (11, 13):
        problems = GR.roundtrip_problems(actual, 10, 5, [], [1, 1, 1], expect_objects=12)
        assert any("oczekiwano 12" in p for p in problems), (actual, problems)


def test_glb_expecting_zero_objects_is_a_declaration_not_a_missing_value():
    """`expect_objects=0` jest falsy. Mutacja na `if expect_objects:` przemilczałaby je."""
    problems = GR.roundtrip_problems(1, 10, 5, [], [1, 1, 1], expect_objects=0)
    assert any("oczekiwano 0" in p for p in problems), problems


# --- próg bboxa: granica dotknięta dokładnie --------------------------------

def test_glb_bbox_drift_exactly_at_the_tolerance_passes():
    """Różnica jest DOKŁADNIE `TOLERANCE_M`, bo druga strona jest zerem.

    `abs(TOLERANCE_M - 0.0)` to bit w bit `TOLERANCE_M`, więc ten test odróżnia
    `delta > TOLERANCE_M` od `delta >= TOLERANCE_M`. Gdyby oczekiwany bbox miał
    tu jakąkolwiek inną wartość, odejmowanie wprowadziłoby błąd reprezentacji
    i granica przestałaby być granicą.
    """
    expected = _expected(bbox=(0.0, 0.0, 0.0), vertices=1, faces=1)
    size = [GR.TOLERANCE_M, 0.0, 0.0]
    assert abs(size[0] - expected["bbox_size_m"][0]) == GR.TOLERANCE_M
    assert GR.roundtrip_problems(1, 1, 1, [], size, expected=expected) == []


def test_glb_bbox_drift_just_above_the_tolerance_fails():
    expected = _expected(bbox=(0.0, 0.0, 0.0), vertices=1, faces=1)
    size = [math.nextafter(GR.TOLERANCE_M, math.inf), 0.0, 0.0]
    problems = GR.roundtrip_problems(1, 1, 1, [], size, expected=expected)
    assert any(p.startswith("bbox X rozjazd") for p in problems), problems


def test_glb_bbox_drift_is_checked_on_every_axis_and_named():
    """Mutacja zwężająca pętlę osi ukryłaby rozjazd w Y albo Z."""
    expected = _expected(bbox=(0.0, 0.0, 0.0), vertices=1, faces=1)
    for index, axis in enumerate("XYZ"):
        size = [0.0, 0.0, 0.0]
        size[index] = 1.0
        problems = GR.roundtrip_problems(1, 1, 1, [], size, expected=expected)
        assert any(p.startswith(f"bbox {axis} rozjazd") for p in problems), (axis, problems)


def test_glb_bbox_drift_is_absolute_not_signed():
    """Mesh MNIEJSZY od zgłoszonego jest równie zły jak większy."""
    expected = _expected(bbox=(10.0, 0.0, 0.0), vertices=1, faces=1)
    problems = GR.roundtrip_problems(1, 1, 1, [], [0.0, 0.0, 0.0], expected=expected)
    assert any(p.startswith("bbox X rozjazd") for p in problems), problems


# --- sufit wierzchołków: granica odczytana z modułu -------------------------

def test_glb_vertex_ceiling_is_reached_but_not_crossed():
    """Granica dotknięta DOKŁADNIE, i to wymagało wybrania liczby, nie zaokrąglenia.

    Liczba wierzchołków jest całkowita, a sufit to `expected * 1.1 * 4.0` — więc
    dla większości wartości sufit NIE JEST liczbą całkowitą i granicy nie da się
    trafić żadnym realnym wejściem. Dla `expected = 100` sufit wynosi
    440.00000000000006; `int()` z tego to 440, czyli PONIŻEJ granicy, i taki test
    przechodzi identycznie dla `>` i dla `>=`. Pierwsza wersja tego testu tak
    właśnie wyglądała i mutacja `>` -> `>=` ją przeżyła.

    `expected = 10` daje sufit dokładnie 44.0. Wtedy `vertices = 44` stoi na
    granicy bit w bit i test wreszcie odróżnia `>` od `>=`.
    """
    ceiling = GR.vertex_ceiling(10)
    assert ceiling == 44.0 and ceiling == int(ceiling), repr(ceiling)
    expected = _expected(vertices=10, faces=1)
    assert GR.roundtrip_problems(1, int(ceiling), 1, [], [10.0, 5.0, 3.0],
                                 expected=expected) == []
    problems = GR.roundtrip_problems(1, int(ceiling) + 1, 1, [], [10.0, 5.0, 3.0],
                                     expected=expected)
    assert any("wierzchołków 45" in p for p in problems), problems


def test_glb_vertex_ceiling_boundary_is_unreachable_for_most_counts():
    """Dlaczego ten próg jest tak trudny do przetestowania — zapisane, nie wywnioskowane.

    Sufit jest iloczynem z 1.1, które nie ma dokładnej reprezentacji binarnej.
    Ten test przypina, dla których liczb granica JEST całkowita, żeby następna
    osoba nie wybrała odruchowo 100 i nie napisała testu, który nie bramkuje.
    """
    assert GR.vertex_ceiling(0) == 4.0
    assert GR.vertex_ceiling(10) == 44.0
    assert GR.vertex_ceiling(20) == 88.0
    assert GR.vertex_ceiling(100) != 440.0, "gdyby to było 440.0, wybór 10 byłby zbędny"
    assert GR.vertex_ceiling(100) > 440.0


def test_glb_vertex_count_equal_to_the_generator_passes():
    """Dolna granica: tyle samo wierzchołków co zgłosił generator jest w porządku.

    Odróżnia `vertices < expected` od `vertices <= expected`.
    """
    expected = _expected(vertices=100, faces=1)
    assert GR.roundtrip_problems(1, 100, 1, [], [10.0, 5.0, 3.0], expected=expected) == []
    problems = GR.roundtrip_problems(1, 99, 1, [], [10.0, 5.0, 3.0], expected=expected)
    assert any("wierzchołków 99" in p for p in problems), problems


def test_glb_vertex_ceiling_never_drops_below_the_floor_for_tiny_meshes():
    """`max(1.0, ...)` istnieje dla meshy zerowych; sufit nie może zejść do zera."""
    assert GR.vertex_ceiling(0) == 1.0 * GR.VERTEX_CEILING_FACTOR
    assert GR.vertex_ceiling(0) > 0.0


def test_glb_vertex_ceiling_grows_with_the_declared_count():
    """Mutacja mnożnika albo tolerancji spłaszczyłaby sufit."""
    assert GR.vertex_ceiling(1000) > GR.vertex_ceiling(100)
    assert GR.vertex_ceiling(100) == max(1.0, 100 * (1.0 + GR.COUNT_TOLERANCE)) \
        * GR.VERTEX_CEILING_FACTOR


# --- ściany -----------------------------------------------------------------

def test_glb_face_count_may_grow_but_never_shrink():
    """Triangulacja przy eksporcie dodaje ściany; ubytek znaczy zgubioną geometrię."""
    expected = _expected(vertices=1, faces=50)
    assert GR.roundtrip_problems(1, 1, 50, [], [10.0, 5.0, 3.0], expected=expected) == []
    assert GR.roundtrip_problems(1, 1, 500, [], [10.0, 5.0, 3.0], expected=expected) == []
    problems = GR.roundtrip_problems(1, 1, 49, [], [10.0, 5.0, 3.0], expected=expected)
    assert any("ścian 49" in p for p in problems), problems


# --- brak metryk ------------------------------------------------------------

def test_glb_without_generator_metrics_only_the_local_checks_run():
    """Bez `expected` bramka nie ma z czym porównywać i nie wolno jej wymyślać zarzutu."""
    assert GR.roundtrip_problems(1, 10, 5, [], [999.0, 999.0, 999.0]) == []


def test_glb_problem_order_is_stable_because_it_becomes_an_error_message():
    expected = _expected(bbox=(0.0, 0.0, 0.0), vertices=100, faces=50)
    problems = GR.roundtrip_problems(3, 0, 0, ["a"], [1.0, 0.0, 0.0],
                                     expect_objects=12, expected=expected)
    assert problems[0] == "geometria pusta po imporcie"
    assert problems[1].startswith("obiekty bez UV")
    assert problems[2].startswith("obiektów 3")
    assert problems[3].startswith("bbox X rozjazd")

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

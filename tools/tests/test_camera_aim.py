#!/usr/bin/env python3
"""Testy celowania kamery kontrolnej (`tools/blender/camera_aim.py`).

Powód ten sam co przy poprzednich pięciu ekstrakcjach: przemiatanie mutacyjne
z 03.09.2026 dało dla `render_check.py` 8 mutacji i 8 ocalałych. Moduł importuje
`bpy` i `mathutils`, a decyzje leżały wewnątrz funkcji budujących kamery.

Poza zasięgiem był między innymi próg 0,995, który decyduje, czy przy kamerze
patrzącej prawie w pion wolno jeszcze użyć światowego „w górę" jako odniesienia.
Gdy pójdzie źle, ujęcie jest obrócone o przypadkowy kąt i **przechodzi** kontrolę
pustej klatki — tak samo jak ujęcie w płycie stropowej, opisane w docstringu
`local_vertical_mid`.
"""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import camera_aim as CA  # noqa: E402


# --- długość i degeneracja ---------------------------------------------------

def test_vector_length_is_exact_for_a_single_component():
    """`math.hypot(t, 0, 0)` daje `abs(t)` BIT W BIT — na tym stoi test granicy niżej."""
    assert CA.vector_length((CA.DEGENERATE_LENGTH, 0.0, 0.0)) == CA.DEGENERATE_LENGTH
    assert CA.vector_length((-3.0, 0.0, 0.0)) == 3.0
    assert CA.vector_length((3.0, 4.0, 0.0)) == 5.0


def test_degenerate_boundary_belongs_to_usable():
    """Wektor o długości DOKŁADNIE progu jest jeszcze użyteczny.

    Granica jest dotykalna bez błędu reprezentacji, bo bierze się z `hypot`
    jednej składowej. Podnoszenie do kwadratu i cofanie pierwiastkiem tej
    własności nie ma — a to jest jedyny sposób, żeby ten test odróżnił `<` od `<=`.
    """
    assert CA.is_degenerate((CA.DEGENERATE_LENGTH, 0.0, 0.0)) is False
    just_below = math.nextafter(CA.DEGENERATE_LENGTH, 0.0)
    assert CA.is_degenerate((just_below, 0.0, 0.0)) is True


def test_degenerate_recognises_the_zero_vector():
    assert CA.is_degenerate((0.0, 0.0, 0.0)) is True


def test_degenerate_threshold_is_pinned_and_far_below_any_real_tangent():
    """Mutacja progu `1e-9` -> `1.01e-9` nie ma zmienić odpowiedzi dla realnych stycznych.

    Styczne osi tunelu są wektorami jednostkowymi albo różnicami punktów
    o odstępach metrowych — nigdy nie są bliskie 1e-9. Ten test przypina samą
    liczbę, bo jej podniesienie w górę zaczęłoby odrzucać poprawne styczne.
    """
    assert CA.DEGENERATE_LENGTH == 1e-9
    assert CA.is_degenerate((1.0, 0.0, 0.0)) is False
    assert CA.is_degenerate((1e-6, 0.0, 0.0)) is False


def test_degenerate_uses_the_whole_vector_not_only_the_first_axis():
    """Styczna pionowa jest długa, choć jej X i Y są zerami."""
    assert CA.is_degenerate((0.0, 0.0, 1.0)) is False
    assert CA.is_degenerate((0.0, 1e-12, 0.0)) is True


# --- ile punktów osi ---------------------------------------------------------

def test_two_points_are_enough_and_one_is_not():
    """Granica całkowita, więc dokładna: odróżnia `>= 2` od `> 2` i `< 2` od `<= 2`."""
    assert CA.enough_centerline_points(2) is True
    assert CA.enough_centerline_points(1) is False
    assert CA.enough_centerline_points(0) is False


def test_more_points_stay_enough():
    assert CA.enough_centerline_points(3) is True
    assert CA.enough_centerline_points(447) is True, "tyle ma oś pakietu A"


def test_minimum_centerline_points_is_pinned():
    """Mutacja progu `2` -> `3` odrzuciłaby oś dwupunktową, która jest poprawna."""
    assert CA.MIN_CENTERLINE_POINTS == 2


# --- próg pionu --------------------------------------------------------------

def test_level_dot_boundary_belongs_to_usable():
    """Granica podana WPROST, bo wektora jednostkowego o Z równym 0,995 nie ma.

    Normalizacja wprowadza błąd reprezentacji, więc „kierunek na granicy" zbudowany
    z wektora wypadłby obok progu i nie odróżniłby `>` od `>=`. Dlatego predykat
    bierze gotowy iloczyn skalarny — wtedy granicę da się dotknąć bit w bit.
    """
    assert CA.needs_fallback_up(CA.LEVEL_DOT_LIMIT) is False
    assert CA.needs_fallback_up(math.nextafter(CA.LEVEL_DOT_LIMIT, 1.0)) is True


def test_looking_straight_down_needs_the_fallback():
    """|cos| = 1.0 to patrzenie w pion; mutacja progu `0.995` -> `1.00495` to przepuści."""
    assert CA.needs_fallback_up(1.0) is True
    assert CA.LEVEL_DOT_LIMIT < 1.0, "próg musi zostawiać pion po stronie zapasowego"


def test_looking_horizontally_keeps_world_up():
    assert CA.needs_fallback_up(0.0) is False


# --- wybór odniesienia pionu -------------------------------------------------

def test_up_reference_switches_only_near_the_vertical():
    assert CA.up_reference((1.0, 0.0, 0.0)) == (0.0, 0.0, 1.0)
    assert CA.up_reference((0.0, 1.0, 0.0)) == (0.0, 0.0, 1.0)
    assert CA.up_reference((0.0, 0.0, 1.0)) == (0.0, 1.0, 0.0)
    assert CA.up_reference((0.0, 0.0, -1.0)) == (0.0, 1.0, 0.0)


def test_up_reference_does_not_depend_on_the_length_of_the_direction():
    """Kierunek przychodzi jako różnica punktów, więc bywa długi na kilometry."""
    assert CA.up_reference((0.0, 0.0, 5000.0)) == (0.0, 1.0, 0.0)
    assert CA.up_reference((5000.0, 0.0, 0.0)) == (0.0, 0.0, 1.0)


def test_up_reference_of_a_zero_direction_falls_back_to_world_up():
    """Kierunek zerowy nie ma pionu; odpowiedź jest ta sama co dla poziomego."""
    assert CA.up_reference((0.0, 0.0, 0.0)) == (0.0, 0.0, 1.0)


def test_up_reference_at_exactly_the_degenerate_length_still_reads_the_direction():
    """Kierunek o długości DOKŁADNIE progu jest jeszcze kierunkiem, więc pion się liczy.

    To ta sama granica co w `is_degenerate` i musi zachowywać się tak samo —
    inaczej te dwie funkcje przestałyby mówić o tym samym. Kierunek pionowy
    o długości progu ma dać zapasowe odniesienie, bo `|cos|` wynosi tam 1,0;
    mutacja `<` -> `<=` zwróciłaby światowe „w górę" i ujęcie wyszłoby obrócone
    o przypadkowy kąt.

    Granica jest dotykalna bit w bit, bo `hypot` jednej składowej jest dokładny.
    """
    at_threshold = (0.0, 0.0, CA.DEGENERATE_LENGTH)
    assert CA.vector_length(at_threshold) == CA.DEGENERATE_LENGTH
    assert CA.is_degenerate(at_threshold) is False
    assert CA.up_reference(at_threshold) == (0.0, 1.0, 0.0)

    just_below = (0.0, 0.0, math.nextafter(CA.DEGENERATE_LENGTH, 0.0))
    assert CA.is_degenerate(just_below) is True
    assert CA.up_reference(just_below) == (0.0, 0.0, 1.0)


def test_up_reference_at_the_shallowest_angle_that_still_switches():
    """Trochę ponad 5,7° od pionu — po tej stronie progu wystarcza światowe „w górę"."""
    steep = (0.0, 0.05, 1.0)
    shallow = (0.0, 0.2, 1.0)
    assert CA.up_reference(steep) == (0.0, 1.0, 0.0)
    assert CA.up_reference(shallow) == (0.0, 0.0, 1.0)


# --- pozycja na osi ----------------------------------------------------------

def test_centerline_position_at_both_ends():
    assert CA.centerline_position(5, 0.0) == (0, 1, 0.0)
    lo, hi, t = CA.centerline_position(5, 1.0)
    assert (lo, hi) == (4, 4) and t == 0.0, "ułamek 1,0 nie może wyjść za oś"


def test_centerline_position_in_the_middle_of_a_segment():
    assert CA.centerline_position(5, 0.5) == (2, 3, 0.0)
    assert CA.centerline_position(3, 0.25) == (0, 1, 0.5)


def test_centerline_position_clamps_hi_on_a_two_point_axis():
    assert CA.centerline_position(2, 1.0) == (1, 1, 0.0)
    assert CA.centerline_position(2, 0.5) == (0, 1, 0.5)


def test_centerline_position_weight_stays_inside_the_unit_interval():
    for count in (2, 3, 447):
        for step in range(0, 21):
            _, _, t = CA.centerline_position(count, step / 20.0)
            assert 0.0 <= t < 1.0 or t == 0.0, (count, step, t)

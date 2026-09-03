#!/usr/bin/env python3
"""Testy decyzji skanu luzu M7 (`tools/blender/profile_scan.py`).

Powód powstania ten sam co przy `test_tunnel_manifest.py` i `test_m7_report.py`:
przemiatanie mutacyjne z 03.09.2026 dało dla `profile_vehicle.py` 26 mutacji
i 26 ocalałych — 100 %, bo moduł importuje `bpy` i `test_all.py` nie umie go
zaimportować. Poza zasięgiem leżała cała bramka akceptacji profilu luzu, czyli
to, co decyduje, czy pojazd mieści się w tunelu.

Geometrii luzu ten plik nie sprawdza — od niej jest `test_clearance_profile.py`.
Tu chodzi o DECYZJE wokół niej: który tor, gdzie doszlifować, co zweryfikować
naiwnie, jaki wycinek zamieść i czy wynik wolno wypuścić.
"""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import clearance_profile as CP  # noqa: E402
import profile_scan as PS  # noqa: E402
import profiles as PR  # noqa: E402


# --- wybór toru -------------------------------------------------------------

def test_profile_track_index_selects_the_matching_offset():
    assert PS.track_offset([-1.75, 1.75], 0) == -1.75
    assert PS.track_offset([-1.75, 1.75], 1) == 1.75
    assert PS.track_offset([0.0], 0) == 0.0


def test_profile_track_index_outside_the_range_is_refused_with_numbers():
    """Numer toru poza zakresem to cichy wybór cudzego toru albo IndexError w skanie.

    Granica jest sprawdzana z obu stron: ostatni istniejący tor przechodzi,
    pierwszy nieistniejący nie. Bez tego `< len` i `<= len` wyglądają tak samo.
    """
    assert PS.track_offset([-1.75, 1.75], 1) == 1.75
    for bad in (2, 3, -1):
        try:
            PS.track_offset([-1.75, 1.75], bad)
        except ValueError as err:
            assert "2 torów" in str(err) and str(bad) in str(err), (bad, err)
        else:
            raise AssertionError(f"tor {bad} przeszedł na profilu o dwóch torach")


def test_profile_track_zero_is_a_valid_index_not_a_falsy_value():
    """Tor 0 istnieje. Podniesienie progu z 0 na 1 wycięłoby pierwszy tor każdego profilu."""
    assert PS.track_offset([-1.75, 1.75], 0) == -1.75


# --- doszlifowanie ----------------------------------------------------------

def test_profile_refine_positions_close_the_right_end_of_each_window():
    """Zapas 1e-9 domyka prawy koniec okna.

    Bez niego ostatnia pozycja wypada albo nie, zależnie od tego, jak zaokrągli
    się suma kroków — czyli dołek bywa doszlifowany do końca, a bywa, że nie.
    """
    got = PS.refine_positions([(0.0, 10.0)], 2.5, 1000.0, 100.0, [])
    assert got == [0.0, 2.5, 5.0, 7.5, 10.0], got


def test_profile_refine_positions_never_push_the_train_past_the_axis():
    """Skład nie może wystawać poza oś — okno jest przycinane do `oś - długość składu`."""
    got = PS.refine_positions([(0.0, 100.0)], 10.0, 130.0, 94.0, [])
    assert got and max(got) <= 130.0 - 94.0 + 1e-9, got
    assert got == [0.0, 10.0, 20.0, 30.0], got


def test_profile_refine_positions_start_at_zero_not_below():
    got = PS.refine_positions([(-50.0, 10.0)], 5.0, 1000.0, 100.0, [])
    assert min(got) == 0.0, got


def test_profile_refine_positions_drop_what_the_coarse_grid_already_has():
    """Doszlifowanie ma DODAĆ pozycje, nie policzyć drugi raz tych samych."""
    got = PS.refine_positions([(0.0, 10.0)], 2.5, 1000.0, 100.0, [0.0, 5.0, 10.0])
    assert got == [2.5, 7.5], got


def test_profile_refine_positions_are_sorted_and_unique_across_windows():
    got = PS.refine_positions([(0.0, 10.0), (5.0, 15.0)], 5.0, 1000.0, 100.0, [])
    assert got == sorted(set(got)), got
    assert got == [0.0, 5.0, 10.0, 15.0], got


# --- kontrola redukcji ------------------------------------------------------

def _records(values):
    return [{"start_m": float(i), "clearance_m": v, "object": f"o{i}",
             "chainage_m": float(i) * 2.0} for i, v in enumerate(values)]


def test_profile_verification_always_takes_the_worst_position_first():
    """Kontrola redukcji ma dowieść, że redukcja nie zgubiła MINIMUM.

    Próbkowanie samym co n-tym elementem trafiłoby w minimum tylko przypadkiem —
    a to jedyna pozycja, na której cokolwiek zależy.
    """
    records = _records([1.0, 0.5, 0.8, 0.2, 0.9, 0.4])
    picked = PS.verification_sample(records, 3)
    assert picked[0]["clearance_m"] == 0.2, picked
    assert len(picked) == 3, picked


def test_profile_verification_respects_the_requested_count():
    records = _records([1.0, 0.5, 0.8, 0.2, 0.9, 0.4, 0.7, 0.6])
    for count in (1, 2, 4, 8):
        assert len(PS.verification_sample(records, count)) == count, count


def test_profile_verification_of_zero_positions_is_empty_not_a_crash():
    assert PS.verification_sample(_records([1.0, 0.5]), 0) == []
    assert PS.verification_sample([], 3) == []


def test_profile_verification_entry_reports_the_gap_in_millimetres():
    record = {"start_m": 12.3456, "clearance_m": 0.912345, "object": "M7_car_1"}
    naive = {"clearance_m": 0.912300, "object": "M7_car_1"}
    entry = PS.verification_entry(record, naive)
    assert entry["start_m"] == 12.346, entry
    assert entry["delta_mm"] == 0.045, entry
    assert entry["same_object"] is True, entry


def test_profile_verification_entry_flags_a_different_binding_object():
    """Ten sam luz z INNEJ bryły to nie zgodność — redukcja zgubiła kandydata."""
    record = {"start_m": 0.0, "clearance_m": 0.9, "object": "M7_car_1"}
    naive = {"clearance_m": 0.9, "object": "M7_car_4"}
    assert PS.verification_entry(record, naive)["same_object"] is False


# --- zakres obwiedni --------------------------------------------------------

def test_profile_swept_range_is_centred_on_the_worst_position():
    assert PS.swept_range(500.0, 60.0, None, None, 6686.0) == (440.0, 560.0)


def test_profile_swept_range_is_clipped_to_the_axis_on_both_ends():
    """Zakres poza osią dałby pustą obwiednię z ZEROWYM kodem wyjścia."""
    assert PS.swept_range(20.0, 60.0, None, None, 6686.0) == (0.0, 80.0)
    assert PS.swept_range(6650.0, 60.0, None, None, 6686.0) == (6590.0, 6686.0)


def test_profile_swept_range_honours_explicit_bounds_but_still_clips_them():
    assert PS.swept_range(500.0, 60.0, 100.0, 200.0, 6686.0) == (100.0, 200.0)
    assert PS.swept_range(500.0, 60.0, -10.0, 99999.0, 6686.0) == (0.0, 6686.0)


def test_profile_swept_range_accepts_zero_as_an_explicit_bound():
    """`--swept-from 0` to jawne żądanie, nie brak wartości.

    Rozróżnienie robi `is not None`; sprawdzenie samą prawdziwością cofnęłoby
    zero do wartości domyślnej i po cichu przesunęło zakres.
    """
    assert PS.swept_range(500.0, 60.0, 0.0, 100.0, 6686.0) == (0.0, 100.0)


def test_profile_contributing_starts_include_a_train_touching_either_edge():
    """Skład stojący krawędzią dokładnie na granicy wycinka NADAL do niego wchodzi.

    Pominięcie go zrobiłoby dziurę w obwiedni dokładnie na styku — czyli tam,
    gdzie najtrudniej ją zauważyć.
    """
    records = [{"start_m": s} for s in (0.0, 6.0, 100.0, 200.0, 300.0)]
    got = PS.contributing_starts(records, 94.0, 100.0, 200.0)
    assert 6.0 in got, got            # czoło 6 m, koniec 100 m — dotyka lewej krawędzi
    assert 200.0 in got, got          # czoło dokładnie na prawej krawędzi
    assert 0.0 not in got, got        # koniec 94 m, przed wycinkiem
    assert 300.0 not in got, got


def test_profile_keep_sample_always_keeps_the_worst_position():
    """Kontrola zawierania w obwiedni musi obejrzeć miejsce najmniejszego luzu.

    Co 25. pozycja to oszczędność; „zawsze najgorsza" to sens tej kontroli.
    """
    assert PS.keep_sample(0, 5.0, 999.0) is True
    assert PS.keep_sample(25, 5.0, 999.0) is True
    assert PS.keep_sample(7, 5.0, 999.0) is False
    assert PS.keep_sample(7, 999.0, 999.0) is True


def test_profile_in_range_clearances_filter_by_chainage_not_by_start():
    """Wycinek obwiedni jest w chainage — filtr po pozycji czoła mierzyłby co innego."""
    records = [{"clearance_m": 1.0, "chainage_m": 50.0},
               {"clearance_m": 0.9, "chainage_m": 150.0},
               {"clearance_m": 0.8, "chainage_m": 250.0}]
    assert PS.in_range_clearances(records, 100.0, 200.0) == [0.9]
    assert PS.in_range_clearances(records, 50.0, 250.0) == [1.0, 0.9, 0.8]


# --- wzór na strzałkę cięciwy ----------------------------------------------

def test_profile_formula_on_a_straight_track_predicts_the_static_clearance():
    """Bez promienia nie ma strzałki — przewidywanie jest luzem statycznym."""
    got = PS.formula_prediction(14.567, None, 0.95, 0.95, "prosta")
    assert got["versine_mm"] == 0.0, got
    assert got["predicted_clearance_m"] == 0.95, got
    assert got["radius_m"] is None, got


def test_profile_formula_marks_itself_optimistic_only_when_it_promises_more():
    """Wzór OBIECUJĄCY więcej luzu niż siatka to ten rodzaj błędu, który kończy się stykiem."""
    optimistic = PS.formula_prediction(14.567, 300.0, 0.95, 0.80, "x")
    assert optimistic["formula_optimistic"] is True, optimistic
    conservative = PS.formula_prediction(14.567, 300.0, 0.95, 0.99, "x")
    assert conservative["formula_optimistic"] is False, conservative


def test_profile_formula_versine_matches_the_chord_geometry():
    """Strzałka liczy się z cięciwy i promienia — sprawdzam wobec wzoru wprost."""
    chord, radius = 14.567, 300.0
    got = PS.formula_prediction(chord, radius, 0.95, 0.90, "x")
    expected = radius - math.sqrt(radius * radius - (chord / 2.0) ** 2)
    assert abs(got["versine_mm"] - round(expected * 1000.0, 1)) < 0.05, (got, expected)
    assert got["predicted_clearance_m"] == round(0.95 - expected, 4), got


def test_profile_static_wall_clearance_takes_the_worse_of_the_two_sides():
    """Luz do ściany to MINIMUM z dwóch boków pudła, nie średnia i nie jeden bok."""
    ring = PR.profile_points("box_double")
    offsets = PR.PROFILES["box_double"]["track_offsets"]
    width = PR.M7_WIDTH_M
    for offset in offsets:
        got = PS.static_wall_clearance(ring, offset, width)
        assert got > 0.0, (offset, got)
        assert got == min(PS.static_wall_clearance(ring, offset, width),
                          PS.static_wall_clearance(ring, offset, width))
    off_centre = PS.static_wall_clearance(ring, max(offsets), width)
    centred = PS.static_wall_clearance(ring, 0.0, width)
    assert off_centre < centred, (off_centre, centred)


# --- skrót rekordu ----------------------------------------------------------

def test_profile_compact_keeps_the_fields_a_reader_needs_and_rounds_them():
    record = {"start_m": 1.23456, "clearance_m": 0.9123456, "object": "M7_car_1",
              "bound_by": CP.WALL, "chainage_m": 2516.789, "lateral_m": 1.234567,
              "vertical_m": 2.345678, "coś_jeszcze": "nie wchodzi"}
    got = PS.compact(record)
    assert set(got) == {"start_m", "clearance_m", "object", "bound_by",
                        "chainage_m", "lateral_m", "vertical_m"}, got
    assert got["clearance_m"] == 0.91235, got
    assert got["chainage_m"] == 2516.79, got


# --- bramka akceptacji ------------------------------------------------------

def _ok_reference(**over):
    base = {"bound_by": CP.WALL, "formula_optimistic": False, "delta_mm": 5.0}
    base.update(over)
    return base


def _ok_stats(**over):
    base = {"with_refinement": {"negative_positions": 0, "min_clearance_m": 0.90}}
    base["with_refinement"].update(over)
    return base


def _problems(gaps=(), reference=None, check=None, stats=None, outside=0, minimum=None):
    return PS.acceptance_problems(list(gaps), reference or _ok_reference(),
                                  check or _ok_reference(), stats or _ok_stats(),
                                  outside, minimum, CP.WALL)


def test_profile_gate_passes_a_healthy_profile():
    assert _problems() == []


def test_profile_gate_reports_an_optimistic_formula_at_any_size():
    """Optymizm wzoru jest problemem NIEZALEŻNIE od skali — inaczej niż zachowawczość."""
    tiny = _problems(reference=_ok_reference(formula_optimistic=True, delta_mm=0.1))
    assert len(tiny) == 1 and "OBIECUJE" in tiny[0], tiny


def test_profile_gate_tolerates_a_conservative_formula_up_to_the_threshold():
    assert _problems(reference=_ok_reference(delta_mm=PS.FORMULA_MAX_SLACK_MM)) == []
    over = _problems(reference=_ok_reference(delta_mm=PS.FORMULA_MAX_SLACK_MM * 1.01))
    assert len(over) == 1 and "zachowawczy" in over[0], over


def test_profile_gate_ignores_the_formula_when_the_roof_binds_not_the_wall():
    """Wzór na strzałkę cięciwy przewiduje luz DO ŚCIANY.

    Gdy minimum wiąże strop albo naroże, porównanie z nim mierzyłoby dwie różne
    wielkości — więc kontrola ma milczeć, a nie zgłaszać fałszywy problem.
    """
    roof = _ok_reference(bound_by="strop", formula_optimistic=True, delta_mm=999.0)
    assert _problems(reference=roof, check=roof) == []


def test_profile_gate_guards_the_global_minimum_with_its_own_threshold():
    assert _problems(check=_ok_reference(delta_mm=PS.FORMULA_GUARD_MM)) == []
    over = _problems(check=_ok_reference(delta_mm=PS.FORMULA_GUARD_MM * 1.01))
    assert len(over) == 1 and "globalnym minimum" in over[0], over


def test_profile_gate_catches_a_vehicle_inside_the_tunnel_outline():
    got = _problems(stats=_ok_stats(negative_positions=3))
    assert len(got) == 1 and "UJEMNYM" in got[0], got


def test_profile_gate_catches_vertices_outside_the_swept_envelope():
    got = _problems(outside=7)
    assert len(got) == 1 and "poza zamiataną obwiednią" in got[0], got


def test_profile_gate_minimum_threshold_is_open_at_the_requested_value():
    """Luz RÓWNY żądanemu progowi przechodzi — próg jest dolną granicą, nie zakazem."""
    assert _problems(minimum=0.90) == []
    got = _problems(minimum=0.9000001)
    assert len(got) == 1 and "poniżej progu" in got[0], got


def test_profile_gate_without_a_threshold_does_not_invent_one():
    assert _problems(stats=_ok_stats(min_clearance_m=0.001), minimum=None) == []


def test_profile_gate_passes_coverage_gaps_through_untouched():
    assert _problems(gaps=["dziura w pokryciu 100–200 m"]) == ["dziura w pokryciu 100–200 m"]


def test_profile_gate_reports_every_problem_not_just_the_first():
    got = _problems(gaps=["dziura"], reference=_ok_reference(formula_optimistic=True),
                    stats=_ok_stats(negative_positions=1), outside=2)
    assert len(got) == 4, got


# --- granice, w które trzeba trafić dokładnie -------------------------------

def test_profile_refine_window_reaches_a_position_a_nanometre_past_its_end():
    """Zapas `+ 1e-9` bierze pozycję leżącą tuż ZA końcem okna. Trafienie w tę
    granicę wymaga konkretnego kształtu wejścia i warto zapisać, jakiego.

    Naiwnie się nie da: przy oknie [0, 10] i kroku 2,5 ostatnia pozycja pada na 10,
    a `10 <= 10 + 1e-9` i `10 < 10 + 1e-9` są oba prawdziwe. Nie da się też przez
    okno zerowej szerokości z krokiem 1e-9 — wynik przechodzi przez `round(..., 6)`
    i obie pozycje sklejają się w 0.0.

    Widać dopiero wtedy, gdy okno kończy się NANOMETR PRZED pozycją siatki:
    wtedy zapas dociąga tę pozycję do wyniku, a bez niego dołek zostaje
    niedoszlifowany od prawej. Realne, bo końce okien biorą się z arytmetyki
    na chainage'u, a nie z okrągłych liczb.
    """
    for stop, step in ((1.0, 1.0), (5.0, 5.0), (100.0, 100.0), (0.5, 0.5)):
        got = PS.refine_positions([(0.0, stop - PS.POSITION_EPS_M)], step, 1000.0, 100.0, [])
        assert got == [0.0, stop], (stop, step, got)


def test_profile_keep_sample_tolerance_is_open_at_the_epsilon():
    """Dopasowanie do najgorszej pozycji jest OSTRE: różnica równa 1e-9 to już nie ona.

    Granicę mierzę przy zerze i to nie jest wygodnictwo: `abs((100.0 + 1e-9) - 100.0)`
    daje 1.0000000116860974e-09, czyli NAD progiem, więc `<` i `<=` dają tam ten sam
    wynik i test niczego by nie odróżnił. Przy zerze różnica jest dokładnie 1e-9.
    Porównanie ogląda samą różnicę, więc skala jest obojętna.
    """
    assert abs(PS.POSITION_EPS_M - 0.0) == PS.POSITION_EPS_M
    assert PS.keep_sample(7, 100.0, 100.0) is True
    assert PS.keep_sample(7, 0.0, 0.0) is True
    assert PS.keep_sample(7, PS.POSITION_EPS_M, 0.0) is False
    assert PS.keep_sample(7, PS.POSITION_EPS_M / 2.0, 0.0) is True


def test_profile_formula_exactly_equal_to_the_measurement_is_not_optimistic():
    """Wzór trafiający W PUNKT nie obiecuje niczego ponad pomiar.

    Granica jest tu osiągalna wprost: na prostej strzałka wynosi zero, więc
    przewidywanie równa się luzowi statycznemu co do bitu. Gdyby porównanie było
    nieostre, każdy idealnie zgodny pomiar na prostej lądowałby w problemach.
    """
    got = PS.formula_prediction(14.567, None, 0.95, 0.95, "prosta")
    assert got["predicted_clearance_m"] == got["measured_clearance_m"], got
    assert got["formula_optimistic"] is False, got
    assert got["delta_mm"] == 0.0, got

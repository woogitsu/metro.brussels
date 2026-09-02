#!/usr/bin/env python3
"""Testy rozstawiania detali wzdłuż osi.

Ten moduł liczy wyłącznie kilometraże, więc testy sprawdzają **reguły miejsca**,
a nie wygląd. Wygląd nie jest tu testowany, bo go tu nie ma.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
sys.path.insert(0, os.path.join(ROOT, "tools", "physics"))

import braking as B  # noqa: E402
import detail_layout as D  # noqa: E402

CFG = B.params()


def _axis(length_m, stations):
    return {"id": "T", "length_m": length_m,
            "stations": [{"name": n, "chainage_m": c, "stop_id": f"P{i}"}
                         for i, (n, c) in enumerate(stations)]}


def _kinds(marks, kind):
    return [m for m in marks if m["kind"] == kind]


# --- hektometry ---------------------------------------------------------------

def test_layout_hectometres_start_at_zero_and_stop_at_the_axis_end():
    assert D.hectometre_marks(250.0) == [0.0, 100.0, 200.0]
    assert D.hectometre_marks(300.0) == [0.0, 100.0, 200.0, 300.0]


def test_layout_hectometre_exactly_on_the_end_is_kept():
    """Koniec osi to ostatnia stacja, więc taki hektometr i tak zniknie przy scaleniu —
    ale wypadnięcie go już tutaj ukryłoby, że oś kończy się okrągłą liczbą."""
    assert D.hectometre_marks(600.0)[-1] == 600.0


def test_layout_hectometre_step_must_be_positive():
    try:
        D.hectometre_marks(500.0, 0.0)
    except ValueError:
        return
    raise AssertionError("krok zerowy powinien zostać odrzucony")


def test_layout_denser_step_gives_proportionally_more_marks():
    assert len(D.hectometre_marks(1000.0, 50.0)) == 21
    assert len(D.hectometre_marks(1000.0, 100.0)) == 11


# --- pierwszeństwo w tym samym miejscu ----------------------------------------

def test_layout_station_wins_over_a_hectometre_at_the_same_place():
    """Stacja na okrągłym kilometrażu nie może dać dwóch słupków w jednym punkcie."""
    marks, _ = D.layout(_axis(600.0, [("A", 0.0), ("B", 300.0), ("C", 600.0)]))
    at_300 = [m for m in marks if abs(m["chainage_m"] - 300.0) < 0.5]
    assert len(at_300) == 1
    assert at_300[0]["kind"] == "station"


def test_layout_brake_point_wins_over_a_hectometre_but_loses_to_a_station():
    order = {"station": 0, "brake": 1, "hectometre": 2}
    marks, _ = D.layout(_axis(2000.0, [("A", 0.0), ("B", 1000.0), ("C", 2000.0)]),
                        speed_mps=20.0, decel_mps2=CFG["service"], jerk_mps3=CFG["jerk"])
    for a, b in zip(marks, marks[1:]):
        assert a["chainage_m"] < b["chainage_m"], (a, b)
    assert all(order[m["kind"]] is not None for m in marks)


def test_layout_marks_are_sorted_and_never_duplicated():
    marks, _ = D.layout(_axis(3000.0, [("A", 0.0), ("B", 1400.0), ("C", 3000.0)]),
                        speed_mps=20.0, decel_mps2=CFG["service"], jerk_mps3=CFG["jerk"])
    chainages = [m["chainage_m"] for m in marks]
    assert chainages == sorted(chainages)
    for a, b in zip(chainages, chainages[1:]):
        assert b - a > D.SAME_PLACE_M


# --- punkty hamowania ---------------------------------------------------------

def test_layout_braking_distance_matches_the_t311_closed_form():
    speed = 72.0 / 3.6
    got = D.braking_distance_m(speed, CFG["service"], CFG["jerk"])
    want = B.braking_distance_m(speed, 0.0, CFG["service"], CFG["jerk"])
    assert abs(got - want) < 1e-12


def test_layout_braking_below_the_plateau_falls_back_to_the_jerk_only_distance():
    """Przy małej prędkości cel wypada w trakcie narastania hamulca, więc zadane `b`
    nigdy nie zdąży zadziałać — droga nie zależy już od niego."""
    slow = 0.5
    assert CFG["service"] >= B.plateau_ceiling_mps2(slow, 0.0, CFG["jerk"])
    got = D.braking_distance_m(slow, CFG["service"], CFG["jerk"])
    assert abs(got - B.ramp_only_distance_m(slow, 0.0, CFG["jerk"])) < 1e-12


def test_layout_standstill_needs_no_braking_distance():
    assert D.braking_distance_m(0.0, CFG["service"], CFG["jerk"]) == 0.0


def test_layout_brake_point_sits_exactly_one_braking_distance_before_the_station():
    stations = [{"name": "A", "chainage_m": 0.0}, {"name": "B", "chainage_m": 1000.0}]
    marks, _ = D.braking_marks(stations, 20.0, CFG["service"], CFG["jerk"])
    assert len(marks) == 1
    assert abs(marks[0]["chainage_m"] + marks[0]["braking_distance_m"] - 1000.0) < 0.01


def test_layout_first_station_gets_no_brake_point():
    stations = [{"name": "A", "chainage_m": 0.0}, {"name": "B", "chainage_m": 900.0}]
    marks, _ = D.braking_marks(stations, 20.0, CFG["service"], CFG["jerk"])
    assert [m["for_station"] for m in marks] == ["B"]


def test_layout_brake_point_before_the_previous_station_is_skipped_with_a_reason():
    """Odcinek za krótki na tę prędkość. Przesunięcie punktu w prawo udawałoby, że
    da się ją osiągnąć — pominięcie z powodem mówi prawdę."""
    stations = [{"name": "A", "chainage_m": 0.0}, {"name": "B", "chainage_m": 150.0}]
    marks, skipped = D.braking_marks(stations, 20.0, CFG["service"], CFG["jerk"])
    assert marks == []
    assert len(skipped) == 1
    assert skipped[0]["station"] == "B"
    assert skipped[0]["would_be_at_m"] < 0.0
    assert "za krótki" in skipped[0]["reason"]


def test_layout_higher_speed_pushes_the_brake_point_further_back():
    stations = [{"name": "A", "chainage_m": 0.0}, {"name": "B", "chainage_m": 2000.0}]
    slow, _ = D.braking_marks(stations, 14.0, CFG["service"], CFG["jerk"])
    fast, _ = D.braking_marks(stations, 22.0, CFG["service"], CFG["jerk"])
    assert fast[0]["chainage_m"] < slow[0]["chainage_m"]


def test_layout_without_a_speed_there_are_no_brake_points_at_all():
    """Prędkość dopuszczalna na torze nie ma źródła (R-006), więc brak podanej
    prędkości musi znaczyć brak punktów, a nie cichy domyślny wybór."""
    marks, skipped = D.layout(_axis(2000.0, [("A", 0.0), ("B", 2000.0)]))
    assert _kinds(marks, "brake") == []
    assert skipped == []


# --- raport -------------------------------------------------------------------

def test_layout_survey_counts_every_kind_and_carries_its_assumptions():
    axis = _axis(2000.0, [("A", 0.0), ("B", 1000.0), ("C", 2000.0)])
    report = D.survey(axis, "T", speed_kmh=72.0, cfg=CFG)
    assert report["counts"]["station"] == 3
    assert report["brake_from_kmh"] == 72.0
    assert report["service_brake_mps2"] == CFG["service"]
    assert report["jerk_mps3"] == CFG["jerk"]
    assert report["braking_distance_m"] > 0.0


def test_layout_survey_without_speed_reports_none_not_zero():
    """Zero znaczyłoby „hamowanie na zerowej drodze", a nie „nie liczyliśmy"."""
    report = D.survey(_axis(500.0, [("A", 0.0), ("B", 500.0)]), "T", cfg=CFG)
    assert report["brake_from_kmh"] is None
    assert report["braking_distance_m"] is None
    assert report["service_brake_mps2"] is None


def test_layout_station_marks_carry_the_stop_id_for_joining_with_the_timetable():
    report = D.survey(_axis(900.0, [("A", 0.0), ("B", 900.0)]), "T", cfg=CFG)
    stations = _kinds(report["marks"], "station")
    assert [s["stop_id"] for s in stations] == ["P0", "P1"]


# --- prawdziwe osie -----------------------------------------------------------

def test_layout_every_package_axis_places_a_mark_on_every_station():
    import json, glob
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "track", "*.json"))):
        if path.endswith(".provenance.json"):
            continue
        with open(path, encoding="utf-8") as handle:
            axis = json.load(handle)
        if not isinstance(axis.get("package"), dict):
            continue
        report = D.survey(axis, axis["id"], speed_kmh=72.0, cfg=CFG)
        assert report["counts"]["station"] == len(axis["stations"]), axis["id"]
        last = max(m["chainage_m"] for m in report["marks"])
        assert last <= axis["length_m"] + D.SAME_PLACE_M, axis["id"]


# --- luz słupka przy torze ----------------------------------------------------

sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))
import placement as PL  # noqa: E402
from profiles import profile_points, vehicle_gauge  # noqa: E402

BOX = profile_points("box_double")
GAUGE = vehicle_gauge()


def test_marker_clearance_is_positive_for_the_committed_default():
    """Odsunięcie 2,10 m ze skryptu ma mieścić się między skrajnią a ścianą — i to jest
    jedyny powód, dla którego wolno je nazwać założeniem, a nie zgadywaniem."""
    for height in (0.60, 1.00, 1.60):
        to_gauge, to_wall = PL.marker_clearances(BOX, GAUGE, 2.10, 0.20, -0.10, height)
        assert to_gauge > 0.0, (height, to_gauge)
        assert to_wall > 0.0, (height, to_wall)


def test_marker_too_close_to_the_axis_fouls_the_vehicle_gauge():
    to_gauge, _ = PL.marker_clearances(BOX, GAUGE, 1.60, 0.20, -0.10, 1.60)
    assert to_gauge < 0.0


def test_marker_too_far_pierces_the_tunnel_wall():
    _to_gauge, to_wall = PL.marker_clearances(BOX, GAUGE, 4.70, 0.20, -0.10, 1.60)
    assert to_wall < 0.0


def test_marker_clearance_uses_the_near_edge_not_the_centre():
    """Liczenie od środka słupka zawyżałoby luz o pół szerokości i przepuściłoby
    bryłę, która realnie wchodzi w skrajnię."""
    narrow, _ = PL.marker_clearances(BOX, GAUGE, 2.10, 0.02, -0.10, 1.60)
    wide, _ = PL.marker_clearances(BOX, GAUGE, 2.10, 0.60, -0.10, 1.60)
    assert wide < narrow
    assert abs((narrow - wide) - (0.60 - 0.02) / 2.0) < 1e-9


def test_marker_gauge_narrows_with_height_so_a_low_post_may_stand_closer():
    """Skrajnia ma ścięte naroża, więc pół-rozstawienie do 1,0 m nie może być mniejsze
    niż do 3,9 m — i przy M7 jest wręcz większe."""
    low = PL.gauge_half_width_m(GAUGE, 1.00)
    high = PL.gauge_half_width_m(GAUGE, 3.90)
    assert low >= high


def test_marker_gauge_below_the_rail_head_has_no_points_and_says_so():
    try:
        PL.gauge_half_width_m(GAUGE, -5.0)
    except ValueError:
        return
    raise AssertionError("skrajnia bez punktów poniżej progu powinna dać ValueError")

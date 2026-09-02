#!/usr/bin/env python3
"""Testy koperty prędkości: rozkład kontra model fizyki M7.

Sprawdzają **własności modelu**, a nie wybrane liczby dla Brukseli. Liczba dla
konkretnego odcinka zależy od rozkładu, który się zmienia; własność „krótszy czas
wymaga wyższej prędkości" nie zmienia się nigdy i to ona pilnuje, żeby dolne
ograniczenie było dolnym ograniczeniem.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "physics"))

import braking as B  # noqa: E402
import schedule_envelope as SE  # noqa: E402

CFG = B.params()


def _model():
    return SE.Model(CFG["aw0_kg"], CFG)


def _segment(distance_m, scheduled_s, package="L1_A", from_stop="A", to_stop="B", line="1"):
    return {"package": package, "line": line, "direction_id": "0",
            "from_stop": from_stop, "to_stop": to_stop,
            "from_name": from_stop, "to_name": to_stop,
            "distance_m": distance_m, "median_s": scheduled_s}


# --- hamowanie ----------------------------------------------------------------

def test_envelope_brake_below_the_plateau_ignores_the_commanded_deceleration():
    """Przy małej prędkości cel wypada w trakcie narastania hamulca, więc zadane `b`
    nie zdąży zadziałać — dwie różne wartości `b` muszą dać tę samą drogę."""
    # Sufit plateau to sqrt(2*j*v); dla j = 0,75 hamulec służbowy 1,10 m/s² przestaje
    # być osiągalny dopiero poniżej 0,81 m/s. 1,0 m/s jeszcze PLATEAU osiąga.
    slow = 0.5
    low, _t = SE.brake_profile(slow, 1.10, CFG["jerk"])
    high, _t2 = SE.brake_profile(slow, 3.00, CFG["jerk"])
    assert abs(low - high) < 1e-12
    assert abs(low - B.ramp_only_distance_m(slow, 0.0, CFG["jerk"])) < 1e-12


def test_envelope_brake_above_the_plateau_uses_the_closed_form():
    fast = 80.0 / 3.6
    distance, time = SE.brake_profile(fast, CFG["service"], CFG["jerk"])
    assert abs(distance - B.braking_distance_m(fast, 0.0, CFG["service"], CFG["jerk"])) < 1e-12
    assert abs(time - B.braking_time_s(fast, 0.0, CFG["service"], CFG["jerk"])) < 1e-12


def test_envelope_standstill_brake_is_zero_not_a_negative_closed_form():
    assert SE.brake_profile(0.0, CFG["service"], CFG["jerk"]) == (0.0, 0.0)


# --- czas przejazdu -----------------------------------------------------------

def test_envelope_higher_ceiling_is_never_slower():
    """Monotoniczność jest warunkiem, żeby bisekcja po prędkości w ogóle miała sens."""
    model = _model()
    previous = None
    for speed in (30.0, 40.0, 50.0, 60.0, 70.0, 80.0):
        current = model.fastest_time_s(1200.0, speed)
        if previous is not None:
            assert current <= previous + 1e-9, (speed, current, previous)
        previous = current


def test_envelope_short_segment_never_reaches_the_ceiling():
    """Na krótkim odcinku profil jest trójkątem: podniesienie sufitu nic nie zmienia."""
    model = _model()
    short = 200.0
    assert abs(model.fastest_time_s(short, 60.0) - model.fastest_time_s(short, 100.0)) < 1e-6
    peak = model.peak_speed_kmh(short, 100.0)
    assert peak < 60.0
    _t_a, s_a = model.accel(peak)
    s_b, _t_b = model.brake(peak)
    assert abs(s_a + s_b - short) < 1.0


def test_envelope_long_segment_mean_speed_approaches_the_ceiling():
    model = _model()
    distance = 20000.0
    mean = 3.6 * distance / model.fastest_time_s(distance, 70.0)
    assert 60.0 < mean < 70.0


# --- dolne ograniczenie prędkości ---------------------------------------------

def test_envelope_minimum_top_speed_just_fits_the_schedule():
    """Znaleziona prędkość ma mieścić się w rozkładzie, a o włos niższa już nie."""
    model = _model()
    distance, scheduled = 900.0, 70.0
    speed = model.minimum_top_speed_kmh(distance, scheduled)
    assert speed is not None
    assert model.fastest_time_s(distance, speed) <= scheduled + 1e-6
    assert model.fastest_time_s(distance, speed - 1.0) > scheduled


def test_envelope_tighter_schedule_demands_a_higher_speed():
    model = _model()
    loose = model.minimum_top_speed_kmh(900.0, 90.0)
    tight = model.minimum_top_speed_kmh(900.0, 65.0)
    assert tight > loose


def test_envelope_impossible_schedule_returns_none_not_the_ceiling():
    """Rozkład, którego model nie dowozi, ma wyjść jako nierealizowalny. Zwrócenie
    sufitu przeszukiwania zamieniłoby błąd danych w fałszywy pomiar prędkości."""
    model = _model()
    assert model.minimum_top_speed_kmh(900.0, 5.0) is None


def test_envelope_generous_schedule_still_needs_a_positive_speed():
    model = _model()
    speed = model.minimum_top_speed_kmh(900.0, 600.0)
    assert speed is not None and speed > 0.0


# --- raport -------------------------------------------------------------------

def test_envelope_counts_a_shared_track_segment_once():
    """Pień 1/5 i pierścień 2/6 to ten sam tor obsługiwany przez dwie linie. Policzony
    dwa razy zawyżyłby liczbę odcinków i podwoił wagę pnia w statystyce."""
    timetable = {"segments": [_segment(900.0, 70.0, line="1"),
                              _segment(900.0, 70.0, line="5")]}
    report = SE.envelope(timetable, "AW0", CFG)
    assert report["segments"] == 1


def test_envelope_different_track_with_the_same_stops_on_another_package_is_separate():
    timetable = {"segments": [_segment(900.0, 70.0, package="L1_A"),
                              _segment(900.0, 70.0, package="L2_E")]}
    assert SE.envelope(timetable, "AW0", CFG)["segments"] == 2


def test_envelope_binding_segment_is_the_one_demanding_most_speed():
    timetable = {"segments": [_segment(900.0, 90.0, from_stop="wolny"),
                              _segment(900.0, 66.0, from_stop="szybki")]}
    report = SE.envelope(timetable, "AW0", CFG)
    assert report["binding_segment"]["from_name"] == "szybki"
    assert report["network_min_top_speed_kmh"] == report["binding_segment"]["min_top_speed_kmh"]
    for row in report["rows"]:
        assert row["min_top_speed_kmh"] <= report["network_min_top_speed_kmh"] + 1e-9


def test_envelope_reports_infeasible_segments_instead_of_dropping_them():
    timetable = {"segments": [_segment(900.0, 5.0, from_stop="niemozliwy"),
                              _segment(900.0, 70.0, from_stop="normalny")]}
    report = SE.envelope(timetable, "AW0", CFG)
    assert report["segments"] == 2 and report["infeasible"] == 1
    assert report["binding_segment"]["from_name"] == "normalny"


def test_envelope_ignores_segments_without_a_measured_distance():
    timetable = {"segments": [{"median_s": 70.0}, _segment(900.0, 70.0)]}
    assert SE.envelope(timetable, "AW0", CFG)["segments"] == 1


def test_envelope_loaded_train_needs_at_least_as_much_speed_as_the_empty_one():
    """AW2 rozpędza się wolniej, więc ten sam rozkład wymaga nie mniejszej prędkości."""
    timetable = {"segments": [_segment(900.0, 70.0)]}
    empty = SE.envelope(timetable, "AW0", CFG)["network_min_top_speed_kmh"]
    loaded = SE.envelope(timetable, "AW2", CFG)["network_min_top_speed_kmh"]
    assert loaded >= empty


def test_envelope_reserve_is_measured_against_the_unconstrained_run():
    timetable = {"segments": [_segment(900.0, 70.0)]}
    row = SE.envelope(timetable, "AW0", CFG)["rows"][0]
    assert abs(row["reserve_vs_unconstrained_s"]
               - (row["scheduled_s"] - row["unconstrained_time_s"])) < 0.01
    assert row["reserve_vs_unconstrained_s"] > 0.0


def test_envelope_carries_the_braking_parameters_it_actually_used():
    """Liczba bez wpisanych obok parametrów modelu jest nieodtwarzalna."""
    report = SE.envelope({"segments": [_segment(900.0, 70.0)]}, "AW0", CFG)
    assert report["service_brake_mps2"] == CFG["service"]
    assert report["jerk_mps3"] == CFG["jerk"]
    assert report["mass_kg"] == CFG["aw0_kg"]

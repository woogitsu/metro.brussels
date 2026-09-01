#!/usr/bin/env python3
"""Testy mapy kilometrażu sieci. Bez sieci i bez pytest — geometria budowana w locie."""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import network_chainage as NC  # noqa: E402


def _axis(points, package_id="X", from_station="A", to_station="B", stations=()):
    return {
        "document": {
            "package": {"id": package_id, "name": f"pakiet {package_id}",
                        "from": from_station, "to": to_station},
            "stations": [{"name": n, "chainage_m": c} for n, c in stations],
            "vertical": {"status": "not_modelled"},
            "length_m": None,
        },
        "points": points,
        "chainages": NC.chainages(points),
    }


def _line(x0, y0, x1, y1, count=100):
    return [(x0 + (x1 - x0) * i / count, y0 + (y1 - y0) * i / count) for i in range(count + 1)]


# --- kilometraż i odległości --------------------------------------------------

def test_network_chainages_sum_the_segments():
    values = NC.chainages([(0.0, 0.0), (3.0, 4.0), (3.0, 14.0)])
    assert values == [0.0, 5.0, 15.0]


def test_network_distance_to_axis_measures_the_perpendicular():
    axis = _line(0.0, 0.0, 100.0, 0.0)
    assert abs(NC.distance_to_axis((50.0, 7.0), axis) - 7.0) < 1e-9


def test_network_nearest_station_reports_a_signed_offset():
    document = {"stations": [{"name": "S1", "chainage_m": 100.0},
                             {"name": "S2", "chainage_m": 400.0}]}
    assert NC.nearest_station(document, 120.0) == {"name": "S1", "offset_m": 20.0}
    assert NC.nearest_station(document, 380.0) == {"name": "S2", "offset_m": -20.0}


def test_network_nearest_station_handles_an_axis_without_stations():
    assert NC.nearest_station({"stations": []}, 10.0) is None


# --- granice pakietów ---------------------------------------------------------

def test_network_endpoint_gaps_counts_each_pair_of_ends_once():
    """Regresja: pętla po wszystkich uporządkowanych parach liczyła każdą dziurę dwa razy."""
    axes = {"P": _axis(_line(0.0, 0.0, 500.0, 0.0)),
            "Q": _axis(_line(700.0, 0.0, 1200.0, 0.0))}
    gaps = NC.endpoint_gaps(axes, NC.DEFAULT_CONFLICT_M)
    pairs = {(g["from_axis"], g["from_side"], g["to_axis"], g["to_side"]) for g in gaps}
    assert len(pairs) == len(gaps), gaps
    closest = min(gaps, key=lambda g: g["chord_m"])
    assert abs(closest["chord_m"] - 200.0) < 0.05, closest


def test_network_endpoint_gaps_skips_pairs_further_than_two_kilometres():
    axes = {"P": _axis(_line(0.0, 0.0, 100.0, 0.0)),
            "Q": _axis(_line(50000.0, 0.0, 50100.0, 0.0))}
    assert NC.endpoint_gaps(axes, NC.DEFAULT_CONFLICT_M) == []


def test_network_endpoint_gaps_marks_a_shared_station():
    axes = {"P": _axis(_line(0.0, 0.0, 100.0, 0.0), to_station="WSPÓLNA"),
            "Q": _axis(_line(101.0, 0.0, 200.0, 0.0), from_station="WSPÓLNA")}
    shared = [g for g in NC.endpoint_gaps(axes, NC.DEFAULT_CONFLICT_M) if g["same_station"]]
    assert shared and shared[0]["chord_m"] < 2.0


# --- korytarze i kolizje ------------------------------------------------------

def test_network_proximity_finds_a_parallel_corridor_without_calling_it_a_conflict():
    """Dwie linie 15 m od siebie dzielą korytarz, ale rury 9,40 m się nie przenikają."""
    axes = {"P": _axis(_line(0.0, 0.0, 400.0, 0.0)),
            "Q": _axis(_line(0.0, 15.0, 400.0, 15.0))}
    rows = NC.proximity(axes, NC.DEFAULT_CONFLICT_M, NC.PARALLEL_M)
    assert len(rows) == 1
    assert rows[0]["conflict_points"] == 0
    assert rows[0]["corridor_length_a_m"] > 390.0
    assert abs(rows[0]["min_distance_m"] - 15.0) < 0.05


def test_network_proximity_reports_a_crossing_as_a_conflict():
    """Skrzyżowanie na Z = 0 to dwie rury przechodzące przez siebie."""
    axes = {"P": _axis(_line(-200.0, 0.0, 200.0, 0.0)),
            "Q": _axis(_line(0.0, -200.0, 0.0, 200.0))}
    rows = NC.proximity(axes, NC.DEFAULT_CONFLICT_M, NC.PARALLEL_M)
    assert rows[0]["conflict_points"] > 0
    assert rows[0]["min_distance_m"] < 1.0
    assert rows[0]["conflict_ranges_a_m"], rows[0]


def test_network_proximity_ignores_axes_that_never_come_close():
    axes = {"P": _axis(_line(0.0, 0.0, 400.0, 0.0)),
            "Q": _axis(_line(0.0, 5000.0, 400.0, 5000.0))}
    assert NC.proximity(axes, NC.DEFAULT_CONFLICT_M, NC.PARALLEL_M) == []


def test_network_proximity_conflict_carries_the_nearest_station():
    axes = {"P": _axis(_line(-200.0, 0.0, 200.0, 0.0),
                       stations=(("PERON", 200.0),)),
            "Q": _axis(_line(0.0, -200.0, 0.0, 200.0))}
    conflict = NC.proximity(axes, NC.DEFAULT_CONFLICT_M, NC.PARALLEL_M)[0]["conflicts"][0]
    assert conflict["nearest_station_a"]["name"] == "PERON"


# --- pokrycie -----------------------------------------------------------------

def test_network_coverage_reads_the_package_without_interpreting_it():
    axes = {"L9_Z": _axis(_line(0.0, 0.0, 300.0, 0.0), package_id="Z",
                          from_station="OD", to_station="DO",
                          stations=(("OD", 0.0), ("DO", 300.0)))}
    row = NC.coverage(axes)[0]
    assert row["line"] == "L9" and row["package"] == "Z"
    assert row["from_station"] == "OD" and row["to_station"] == "DO"
    assert abs(row["length_m"] - 300.0) < 1e-6
    assert row["stations"] == 2
    assert row["vertical_status"] == "not_modelled"

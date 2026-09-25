#!/usr/bin/env python3
"""Testy rozkładu bryły M7 (T-220). Bez Blendera i bez pytest.

Testują `m7_layout.py`, czyli całą matematykę, z której korzysta generator.
Kontrole samej wygenerowanej siatki (bbox 1 mm, otwory zmierzone w geometrii,
symetria obrotowa, re-import GLB) robi `m7_shell.py` w Blenderze i sprawdza je
`tools/ci/m7_shell_check.sh`.
"""
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import m7_layout as L  # noqa: E402
import profiles  # noqa: E402

TOLERANCE = 1e-9
SPEC_PATH = os.path.join(ROOT, "data", "vehicle", "m7-spec.json")


def _layout():
    return L.Layout()


# --- źródło wymiarów ----------------------------------------------------------

def test_m7_shell_uses_only_spec_values_from_registry():
    spec = L.load_spec()
    assert spec["length_m"] == 94.0
    assert spec["width_m"] == 2.7
    assert spec["floor_height_m"] == 1.03
    assert spec["cars"] == 6
    assert spec["double_doors_per_side"] == 18
    assert spec["single_cab_doors_total"] == 2
    assert spec["double_door_opening_width_m"] == 1.6
    assert spec["source_url"].startswith("https://stib.prezly.com/")


def test_m7_shell_refuses_non_spec_parameters():
    registry = json.load(open(SPEC_PATH, encoding="utf-8"))
    registry["parameters"]["length_m"]["status"] = "design_model"
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "spec.json")
        json.dump(registry, open(path, "w", encoding="utf-8"))
        try:
            L.load_spec(path)
        except ValueError as exc:
            assert "spec" in str(exc)
        else:
            raise AssertionError("wymiar bez statusu spec został przyjęty")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_m7_shell_dimensions_are_data_driven_not_hardcoded():
    registry = json.load(open(SPEC_PATH, encoding="utf-8"))
    registry["parameters"]["length_m"]["value"] = 90.0
    registry["parameters"]["double_doors_per_side"]["value"] = 12
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "spec.json")
        json.dump(registry, open(path, "w", encoding="utf-8"))
        layout = L.Layout(L.load_spec(path))
        assert layout.length == 90.0 and layout.doors_per_side == 12
        assert layout.doors_per_car == 2
        assert len(layout.double_doors()) == 24
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_m7_shell_every_design_constant_is_documented():
    constants = {name for name in dir(L) if name.startswith("DESIGN_") and name != "DESIGN_ASSUMPTIONS"}
    documented = {f"DESIGN_{key.upper()}" for key in L.DESIGN_ASSUMPTIONS}
    assert constants == documented, constants ^ documented
    for key, (_value, reason) in L.DESIGN_ASSUMPTIONS.items():
        assert len(reason) > 15, key


# --- podział wzdłużny ---------------------------------------------------------

def test_m7_shell_has_six_cars_and_five_articulations():
    layout = _layout()
    assert layout.cars == 6
    assert len(layout.articulation_spans()) == 5
    spans = [layout.car_body_span(i) for i in range(6)]
    assert abs(spans[0][0]) < TOLERANCE
    assert abs(spans[-1][1] - 94.0) < TOLERANCE


def test_m7_shell_car_bodies_and_articulations_tile_the_whole_length():
    layout = _layout()
    pieces = sorted([layout.car_body_span(i) for i in range(6)] + layout.articulation_spans())
    assert abs(pieces[0][0]) < TOLERANCE and abs(pieces[-1][1] - 94.0) < TOLERANCE
    for (_, end), (start, _) in zip(pieces, pieces[1:]):
        assert abs(start - end) < TOLERANCE, f"szczelina/nakładka przy {end}"


# --- drzwi --------------------------------------------------------------------

def test_m7_shell_has_eighteen_double_doors_per_side():
    layout = _layout()
    doors = layout.double_doors()
    assert len(doors) == 36
    for side in (1, -1):
        assert len([d for d in doors if d["side"] == side]) == 18
    for car in range(6):
        assert len([d for d in doors if d["car"] == car and d["side"] == 1]) == 3


def test_m7_shell_double_door_opening_is_exactly_spec_width():
    for door in _layout().double_doors():
        assert abs((door["x1"] - door["x0"]) - 1.6) < 1e-6


def test_m7_shell_has_two_single_cab_doors_on_opposite_sides():
    layout = _layout()
    cabs = layout.cab_doors_list()
    assert len(cabs) == 2
    assert {c["side"] for c in cabs} == {1, -1}
    assert abs((cabs[0]["center_x"] + cabs[1]["center_x"]) - layout.length) < 1e-6


def test_m7_shell_doors_do_not_overlap():
    layout = _layout()
    for side in (1, -1):
        spans = sorted((d["x0"], d["x1"]) for d in layout.all_doors() if d["side"] == side)
        for (_, end), (start, _) in zip(spans, spans[1:]):
            assert start > end, f"otwory nachodzą na siebie przy x={end}"


def test_m7_shell_doors_stay_inside_car_bodies():
    layout = _layout()
    for door in layout.all_doors():
        start, end = layout.car_body_span(door["car"])
        assert start <= door["x0"] and door["x1"] <= end, door


def test_m7_shell_doors_avoid_articulations_and_cabs():
    layout = _layout()
    joints = layout.articulation_spans()
    for door in layout.double_doors():
        for start, end in joints:
            assert door["x1"] <= start or door["x0"] >= end, f"drzwi w przegubie: {door}"
        assert door["x0"] >= L.DESIGN_CAB_LENGTH_M - 1e-9
        assert door["x1"] <= layout.length - L.DESIGN_CAB_LENGTH_M + 1e-9


def test_m7_shell_doors_are_regularly_spaced_inside_each_car():
    layout = _layout()
    for car in range(6):
        centers = sorted(d["center_x"] for d in layout.double_doors() if d["car"] == car and d["side"] == 1)
        gaps = [b - a for a, b in zip(centers, centers[1:])]
        assert max(gaps) - min(gaps) < 1e-5, f"człon {car}: nierówny rozstaw {gaps}"


def test_m7_window_dividers_clear_door_openings_and_match_both_directions():
    layout = _layout()
    spans = []
    for car in range(layout.cars):
        doors = sorted((d for d in layout.double_doors()
                        if d["car"] == car and d["side"] == 1),
                       key=lambda d: d["center_x"])
        dividers = layout.window_divider_spans(car)
        assert len(dividers) == len(doors) - 1, f"człon {car}: liczba słupków"
        for (start, end), before, after in zip(dividers, doors, doors[1:]):
            assert before["x1"] < start < end < after["x0"], f"człon {car}: słupek blokuje drzwi"
            assert abs(end - start - L.DESIGN_WINDOW_DIVIDER_WIDTH_M) < 1e-6, f"człon {car}: szerokość"
        spans.extend(dividers)
    mirrored = {(round(layout.length - end, 6), round(layout.length - start, 6))
                for start, end in spans}
    assert set(spans) == mirrored, "słupki nie są symetryczne po obrocie składu"


def test_m7_shell_door_layout_is_rotationally_symmetric():
    """Skład jest dwukierunkowy: rozkład musi przejść w siebie po obrocie 180°."""
    layout = _layout()
    doors = {(round(d["center_x"], 6), d["side"], d["kind"]) for d in layout.all_doors()}
    rotated = {(round(layout.length - x, 6), -side, kind) for x, side, kind in doors}
    assert doors == rotated, doors ^ rotated


def test_m7_shell_doors_start_at_source_backed_floor_height():
    layout = _layout()
    for door in layout.all_doors():
        assert abs(door["z0"] - 1.03) < 1e-9


# --- przekrój i skrajnia ------------------------------------------------------

def test_m7_shell_section_reaches_full_spec_width_between_noses():
    layout = _layout()
    y0, _, y1, _ = layout.section_extent(layout.length / 2)
    assert abs((y1 - y0) - 2.7) < 1e-9
    assert abs(y1 - 1.35) < 1e-9


def test_m7_shell_nose_tapers_and_never_exceeds_spec_width():
    layout = _layout()
    widest = 0.0
    for i in range(2001):
        x = layout.length * i / 2000
        y0, _, y1, z1 = layout.section_extent(x)
        widest = max(widest, y1 - y0)
        assert z1 <= L.DESIGN_TOTAL_HEIGHT_M + 1e-9
    assert abs(widest - 2.7) < 1e-9
    assert layout.section_extent(0.0)[2] < layout.section_extent(layout.length / 2)[2]


def test_m7_shell_bottom_is_one_shell_thickness_below_spec_floor():
    layout = _layout()
    assert abs(layout.body_bottom_z - (1.03 - L.DESIGN_SHELL_THICKNESS_M)) < 1e-9
    assert abs(layout.body_bottom_z + L.DESIGN_SHELL_THICKNESS_M - layout.floor_z) < 1e-9


def test_m7_shell_fits_vehicle_gauge():
    ok, message = _layout().fits_vehicle_gauge()
    assert ok, message


def test_m7_shell_fits_every_existing_tunnel_profile():
    report = _layout().fits_tunnel_profiles()
    assert set(report) == set(profiles.PROFILES)
    for name, entry in report.items():
        assert entry["ok"], f"{name}: {entry['message']}"
        assert entry["min_clearance_m"] > 0.0, name


def test_m7_shell_summary_reports_spec_and_assumptions_separately():
    summary = _layout().summary()
    assert summary["spec"]["length_m"] == 94.0
    assert "total_height_m" in summary["design_assumptions"]
    assert "length_m" not in summary["design_assumptions"]

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

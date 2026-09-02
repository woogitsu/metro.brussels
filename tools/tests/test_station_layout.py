#!/usr/bin/env python3
"""T-211: rozmieszczenie peronów — połowa, która nie ma decyzji projektowych.

Testy pilnują trzech rzeczy, z których każda była w tym repo osobnym błędem
w przeszłości:

1. wysokość peronu jest TĄ SAMĄ liczbą co wysokość podłogi M7, a nie jej kopią;
2. brakująca dana zostaje `None`, a nie zerem (T-011: `braking_distance_m`);
3. przycięcie do końca osi jest zgłaszane, a nie chowane (R-007: `CbtcTestSpan`).
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import profiles  # noqa: E402
import station_layout as SL  # noqa: E402

AXIS = os.path.join(ROOT, "data", "track", "L1_A.json")


def _axis():
    with open(AXIS, encoding="utf-8") as handle:
        return json.load(handle)


def _straight(stations, length_m=2000.0, step_m=20.0):
    count = int(length_m / step_m) + 1
    return {
        "id": "T",
        "points": [[i * step_m, 0.0, 0.0] for i in range(count)],
        "stations": [{"name": f"S{i}", "chainage_m": c} for i, c in enumerate(stations)],
    }


# --- wysokość: jedna liczba, nie dwie ------------------------------------------


def test_platform_height_is_the_m7_floor_height_from_the_registry():
    """R-007: STIB pisze, że podłoga M7 jest „à hauteur du quai".

    To nie są dwie wielkości, tylko jedna. Gdyby wysokość peronu była osobną stałą,
    dałoby się ją przestawić bez ruszania rejestru — i repo miałoby dwie prawdy.
    """
    height, status = SL.platform_height_m()
    with open(os.path.join(ROOT, "data", "vehicle", "m7-spec.json"), encoding="utf-8") as handle:
        floor = json.load(handle)["parameters"]["floor_height_m"]
    assert height == floor["value"] == 1.03, (height, floor)
    assert status == floor["status"] == "spec"


def test_layout_reports_the_height_with_its_status():
    report = SL.layout(_straight([500.0]), 94.0)
    assert report["platform_height_m"] == 1.03
    assert report["platform_height_status"] == "spec"
    assert report["platforms"][0]["height_m"] == 1.03


def test_profile_station_platform_height_is_not_used_as_the_source():
    """Profil `station` ma 1,05 m — to wysokość podłogi M6, nie M7.

    STIB: „Hauteur du plancher : 1m03 contre 1m05 pour les M6". Symulator jeździ M7
    po liniach 1 i 5, więc 1,05 m opisuje inny pojazd. Ten test nie zmienia profilu —
    pilnuje, żeby rozmieszczenie peronów brało liczbę z rejestru, a nie stamtąd.
    """
    assert profiles.PROFILES["station"]["platform_height_m"] == 1.05
    height, _status = SL.platform_height_m()
    assert height != profiles.PROFILES["station"]["platform_height_m"]


# --- długość: dolna granica z faktu --------------------------------------------


def test_platform_length_defaults_to_the_train_length_which_is_spec():
    assert SL.train_length_m() == 94.0
    report = SL.layout(_straight([500.0]), SL.train_length_m())
    assert report["platform_length_m"] == 94.0
    assert "R-007" in report["platform_length_basis"]


def test_platform_shorter_than_the_train_is_refused():
    """Peron krótszy od składu jest sprzeczny z ruchem — R-007 wyprowadza z tego granicę."""
    try:
        SL.layout(_straight([500.0]), 93.9)
    except SystemExit as error:
        assert "krótszy od składu" in str(error), error
    else:
        raise AssertionError("peron krótszy od składu przeszedł")

    # Dokładnie długość składu jest dozwolona; to jest granica, nie zakaz.
    assert SL.layout(_straight([500.0]), 94.0)["platforms"]


def test_footprint_bound_is_a_check_not_a_dimension():
    """Górna granica z obrysu stacji: peron dłuższy niż bryła jest na pewno błędny."""
    inside = SL.layout(_straight([500.0]), 94.0, footprint_m=109.1)
    assert inside["platforms"][0]["within_footprint"] is True

    outside = SL.layout(_straight([500.0]), 120.0, footprint_m=109.1)
    assert outside["platforms"][0]["within_footprint"] is False


# --- szczelina: brak źródła zostaje None ---------------------------------------


def test_platform_gap_has_no_default_and_stays_none():
    """R-007: szczeliny peron–pudło nie podaje żadne publiczne źródło.

    Zero znaczyłoby „peron dotyka pudła", a nie „nie wiem". Ten sam wzorzec, co
    `braking_distance_m` w T-011.
    """
    report = SL.layout(_straight([500.0]), 94.0)
    assert report["platform_gap_m"] is None
    platform = report["platforms"][0]
    assert platform["edge_offset_m"] is None
    assert platform["minimum_edge_offset_m"] is not None, (
        "dolna granica jest policzalna z geometrii i ma być podana")

    given = SL.layout(_straight([500.0]), 94.0, platform_gap_m=0.08)
    assert given["platforms"][0]["edge_offset_m"] == round(
        platform["minimum_edge_offset_m"] + 0.08, 4)


def test_minimum_edge_offset_is_half_width_plus_the_versine():
    """Na prostej odsunięcie to samo pół szerokości; na łuku rośnie o strzałkę."""
    straight = SL.layout(_straight([500.0]), 94.0)["platforms"][0]
    assert abs(straight["minimum_edge_offset_m"] - profiles.M7_WIDTH_M / 2.0) < 1e-6
    assert straight["versine_m"] == 0.0
    assert straight["min_radius_m"] is None

    curved = SL.layout(_axis(), 94.0)
    on_curve = [p for p in curved["platforms"] if p["min_radius_m"] is not None]
    assert on_curve, "pakiet A ma łuki — brak promienia znaczy, że pomiar nie działa"
    for platform in on_curve:
        assert platform["versine_m"] > 0.0, platform["name"]
        assert platform["minimum_edge_offset_m"] > profiles.M7_WIDTH_M / 2.0, platform["name"]


def test_profile_clearance_boundary_is_wider_than_the_geometric_minimum():
    """`platform_edge_x` z profilu to granica skrajni, nie krawędź peronu.

    Zmierzone: tory na ±2,10 m, krawędzie na ±4,05 m, czyli 1,95 m od toru — a to
    jest 1,35 (pół szerokości M7) + 2 × 0,30 (`CLEARANCE_M`). Szczelina peron–pudło
    wyszłaby **0,600 m**, czyli przepaść. Dolna granica z geometrii jest o połowę
    mniejsza i to ona jest punktem wyjścia dla peronu.
    """
    station = profiles.PROFILES["station"]
    track = max(station["track_offsets"])
    edge = min(e for e in station["platform_edge_x"] if e > track)
    profile_offset = edge - track
    assert abs(profile_offset - (profiles.M7_WIDTH_M / 2.0 + 2.0 * profiles.CLEARANCE_M)) < 1e-9
    assert abs(profile_offset - profiles.M7_WIDTH_M / 2.0 - 0.60) < 1e-9, profile_offset

    worst = max(p["minimum_edge_offset_m"] for p in SL.layout(_axis(), 94.0)["platforms"])
    assert worst < profile_offset, (worst, profile_offset)


# --- przycięcie do osi ----------------------------------------------------------


def test_clipping_at_the_axis_ends_is_reported_not_hidden():
    """Pierwsza i ostatnia stacja pakietu A leżą na końcach osi."""
    report = SL.layout(_axis(), 94.0)
    assert len(report["platforms"]) == 12

    first, last = report["platforms"][0], report["platforms"][-1]
    assert first["clipped_at_start"] is True, first
    assert first["from_m"] == 0.0
    assert last["clipped_at_end"] is True, last
    assert abs(last["to_m"] - report["axis_length_m"]) < 1e-6

    middle = report["platforms"][5]
    assert middle["clipped_at_start"] is False and middle["clipped_at_end"] is False
    assert abs(middle["length_m"] - 94.0) < 1e-6, (
        "peron w środku osi ma mieć pełną długość — inaczej przycięcie jest wszędzie")


def test_platform_is_centred_on_the_station_chainage():
    report = SL.layout(_straight([500.0, 900.0]), 94.0)
    for platform in report["platforms"]:
        centre = (platform["from_m"] + platform["to_m"]) / 2.0
        assert abs(centre - platform["station_chainage_m"]) < 1e-6, platform


def test_report_names_what_it_does_not_model():
    report = SL.layout(_axis(), 94.0)
    joined = " ".join(report["not_modelled"])
    assert "czopów skrętu" in joined, "brak zastrzeżenia o wychyleniu końców składu"
    assert "R-007" in joined, "brak zastrzeżenia o szczelinie bez źródła"

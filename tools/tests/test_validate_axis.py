#!/usr/bin/env python3
"""Testy walidatora osi w miejscach, które przepuszczał milczkiem.

Walidator miał na rzut ostatniej stacji tolerancję 50 m bez uzasadnienia. Przepuszczała
ona przekroczenia rzędu pół metra we wszystkich sześciu pakietach — i przepuściłaby też
stację leżącą 49 m poza osią, czyli błąd danych, a nie artefakt rzutowania. Te testy
przypinają regułę, która zastąpiła tę liczbę: **przekroczenie nie może być większe niż
ostatni odcinek łamanej**.
"""
import json
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import validate as V  # noqa: E402

#: Krok łamanej w osiach z T-210. Stały, żeby długość ostatniego odcinka była znana.
STEP_M = 15.0


def _axis(station_chainages, points=60, step=STEP_M, length_m=None):
    """Prosta oś wzdłuż osi X, z zadanymi kilometrażami stacji."""
    coords = [[i * step, 0.0, 0.0] for i in range(points)]
    total = (points - 1) * step
    return {
        "id": "T",
        "crs": "EPSG:31370",
        "length_m": total if length_m is None else length_m,
        "vertical": {"status": "not_modelled"},
        "points": coords,
        "stations": [
            {"name": f"S{i}", "chainage_m": c, "depth_m": 0.0}
            for i, c in enumerate(station_chainages)
        ],
    }


def _run(axis):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "axis.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(axis, handle)
        return V.validate(path)


def _has(messages, fragment):
    return any(fragment in m for m in messages)


# --- rzut ostatniej stacji za koniec osi --------------------------------------

def test_validate_station_exactly_on_the_end_raises_nothing():
    report = _run(_axis([0.0, 400.0, 885.0]))
    assert not report.err, report.err
    assert not _has(report.warn, "za końcem osi"), report.warn


def test_validate_small_overrun_is_a_warning_not_silence():
    """Pół metra jest nieszkodliwe, ale ma być widoczne: TrackAxis.PointAt obcina
    kilometraż do długości osi, więc symulacja i scena rozjeżdżają się po cichu."""
    report = _run(_axis([0.0, 400.0, 885.6]))
    assert not report.err, report.err
    assert _has(report.warn, "za końcem osi")
    assert _has(report.warn, "0.600 m")


def test_validate_overrun_longer_than_the_last_segment_is_an_error():
    """Rzut dalszy niż jeden odcinek łamanej nie jest artefaktem rzutowania,
    tylko stacją, która nie leży na tej osi."""
    report = _run(_axis([0.0, 400.0, 885.0 + STEP_M + 0.1]))
    assert _has(report.err, "wykracza poza oś"), report.err


def test_validate_old_fifty_metre_tolerance_would_have_passed_this():
    """Regresja z liczbą: stacja 40 m za końcem osi przechodziła poprzednią wersję."""
    report = _run(_axis([0.0, 400.0, 925.0]))
    assert _has(report.err, "wykracza poza oś"), report.err


def test_validate_tolerance_follows_the_actual_last_segment():
    """Tolerancja jest wyprowadzona, nie wpisana: przy gęstszej łamanej maleje razem
    z odcinkiem. Ta sama stacja, ten sam kilometraż, inny krok — inny werdykt."""
    # Krok 15 m: przekroczenie 6 m mieści się w ostatnim odcinku. Krok 5 m: nie mieści.
    # Odstęp stacji musi zostać w [250, 2200] m, więc gęstsza oś dostaje dwie stacje.
    coarse = _run(_axis([0.0, 400.0, 885.0 + 6.0]))
    fine = _run(_axis([0.0, (59 * 5.0) + 6.0], step=5.0))
    assert not coarse.err, coarse.err
    assert fine.err == [m for m in fine.err if "wykracza poza oś" in m], fine.err
    assert _has(fine.err, "wykracza poza oś"), fine.err


def test_validate_first_station_before_the_axis_is_caught_symmetrically():
    report = _run(_axis([-STEP_M - 0.1, 400.0, 885.0]))
    assert _has(report.err, "przed osią"), report.err


def test_validate_small_underrun_is_a_warning():
    report = _run(_axis([-0.4, 400.0, 885.0]))
    assert not report.err, report.err
    assert _has(report.warn, "przed początkiem osi")


# --- deklarowana długość kontra łamana ----------------------------------------

def test_validate_declared_length_matching_the_polyline_is_reported_in_millimetres():
    report = _run(_axis([0.0, 400.0, 885.0], length_m=885.004))
    assert not report.err, report.err
    assert _has(report.info, "length_m zgodne z łamaną")


def test_validate_declared_length_from_another_polyline_is_an_error():
    """Rozjazd większy niż zaokrąglenie zapisu znaczy, że length_m pochodzi z innej
    łamanej niż points — a wtedy wszystko, co liczy z tego pliku kilometraż, liczy go
    z czegoś innego niż geometria."""
    report = _run(_axis([0.0, 400.0, 885.0], length_m=900.0))
    assert _has(report.err, "nie zgadza się z łamaną"), report.err


def test_validate_axis_without_declared_length_still_validates():
    axis = _axis([0.0, 400.0, 885.0])
    del axis["length_m"]
    report = _run(axis)
    assert not report.err, report.err
    assert not _has(report.info, "length_m zgodne")


# --- prawdziwe osie -----------------------------------------------------------

def _package_axes():
    """Osie pakietów budowy, po `package`, a NIE po zawartości katalogu.

    `tools/track/make_test_track.py` zapisuje syntetyczne `TEST.json` i `BROKEN.json`
    prosto do `data/track/`, i robi to workflow `blender-smoke` przed uruchomieniem tej
    suity. Test liczący pliki w katalogu widział wtedy siedem osi zamiast sześciu i padał
    — co złapało CI, a lokalnie nie było widać. Kryterium jest więc **deklarowana
    przynależność do pakietu**, zgodna z `build_packages` w `lines.json`: syntetyczna oś
    pola `package` nie ma, a prawdziwa nie może go stracić po cichu.
    """
    with open(os.path.join(ROOT, "data", "network", "lines.json"), encoding="utf-8") as handle:
        declared = {p["id"] for p in json.load(handle)["build_packages"]}
    directory = os.path.join(ROOT, "data", "track")
    found = {}
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json") or name.endswith(".provenance.json"):
            continue
        path = os.path.join(directory, name)
        with open(path, encoding="utf-8") as handle:
            block = json.load(handle).get("package")
        # `package` w osi jest obiektem skopiowanym z lines.json, nie samym kodem litery.
        package = block.get("id") if isinstance(block, dict) else block
        if package in declared:
            assert package not in found, f"dwie osie dla pakietu {package}"
            found[package] = path
    missing = declared - set(found)
    assert not missing, f"brak osi dla pakietów: {sorted(missing)}"
    return found


def test_validate_every_package_axis_passes_without_errors():
    """Nowa reguła nie może zapalić się na tym, co już leży w repo — inaczej byłaby
    zaostrzeniem poprzeczki pod pozorem naprawy walidatora."""
    for package, path in sorted(_package_axes().items()):
        report = V.validate(path)
        assert not report.err, (package, report.err)


def test_validate_synthetic_axis_in_the_directory_does_not_disturb_the_check():
    """Regresja z nazwą: `blender-smoke` zapisuje TEST.json do data/track/ przed testami."""
    axes = _package_axes()
    assert all(not path.endswith(("TEST.json", "BROKEN.json")) for path in axes.values())


def test_validate_no_package_axis_overruns_its_own_end():
    """Odwrotność poprzedniej wersji tego testu, i to jest cała historia.

    Gdy powstawał, wszystkie sześć pakietów zgłaszało przekroczenie 0,25–0,64 m i test
    pilnował, żeby ta liczba nie zniknęła po cichu. Zniknęła jawnie: kilometraż stacji
    liczy się teraz na osi, która trafia do pliku, a nie na łamanej źródłowej. Test
    pilnuje więc dalej tej samej rzeczy, tylko z drugiej strony — powrót przekroczenia
    znaczyłby, że kilometraż znowu rozjechał się z geometrią.
    """
    over = [
        package for package, path in sorted(_package_axes().items())
        if _has(V.validate(path).warn, "za końcem osi")
    ]
    assert not over, f"pakiety z przekroczeniem: {over}"


def test_validate_last_station_lands_on_the_axis_end():
    """Ostatnia stacja jest końcem osi — oś jest cięta dokładnie w jej rzucie."""
    for package, path in sorted(_package_axes().items()):
        with open(path, encoding="utf-8") as handle:
            axis = json.load(handle)
        last = max(s["chainage_m"] for s in axis["stations"])
        gap = abs(axis["length_m"] - last)
        assert gap <= 0.01, f"{package}: ostatnia stacja {last:.2f} m, oś {axis['length_m']:.2f} m"


def test_validate_axes_keep_the_source_chainage_next_to_the_corrected_one():
    """Kilometraż na łamanej źródłowej nie znika — jest obok, żeby dało się zmierzyć,
    ile kosztuje przepróbkowanie osi, zamiast przyjmować to na wiarę."""
    for package, path in sorted(_package_axes().items()):
        with open(path, encoding="utf-8") as handle:
            stations = json.load(handle)["stations"]
        assert all("source_chainage_m" in s for s in stations), package
        drift = max(s["source_chainage_m"] - s["chainage_m"] for s in stations)
        assert drift >= 0.0, f"{package}: oś przepróbkowana wyszła DŁUŻSZA niż źródłowa"

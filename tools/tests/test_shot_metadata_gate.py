#!/usr/bin/env python3
"""Bramka metadanych zrzutu z Godota — testowana bez Godota.

Audyt mutacyjny `src/Game` (02.09.2026): 24 z 32 mutacji przeżyły, 75 % — najgorzej
z trzech warstw repo. Siedem z nich to jedna przyczyna: krok „Screenshots must not be
empty frames" woła `compare.py` **bez `--baseline`**, a `check_geometry` przy braku
baseline wychodzi na `new-baseline` zanim porówna cokolwiek. Metadane sceny nie były
porównywane z niczym.

`tools/ci/assert_shot_metadata.py` zamyka tę dziurę i te testy pilnują, żeby zamykał
ją nadal. Sam skrypt jest czystym Pythonem, więc testuje się bez silnika; przebieg
z prawdziwym Godotem robi CI.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(ROOT, "tools", "ci", "assert_shot_metadata.py")
AXIS = os.path.join(ROOT, "data", "track", "L1_A.json")
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "godot-first-run.yml")

sys.path.insert(0, os.path.join(ROOT, "tools", "ci"))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import assert_shot_metadata as G  # noqa: E402
import profiles  # noqa: E402


def _healthy():
    """Metadane zmierzone na prawdziwym przebiegu Godota 4.3 na pakiecie A."""
    return {
        "engine": "godot",
        "engine_version": "4.3-stable (official)",
        "manifest_version": "L1_A/flat-preview",
        "resolution": [1280, 720],
        "last_shot": {"view": "Cab", "chainage_m": 2000.068, "steps": 11872},
        "scene": {
            "bbox_min": [-4.4386, -1.2, -910.3813],
            "bbox_max": [5448.105, 4.7, 1076.5525],
            "size_m": [5452.5435, 5.9, 1986.9338],
            "mesh_objects": 12,
            "vertices": 48528,
            "faces": 16176,
            "chunks_loaded": 12,
            "chunks_declared": 12,
            "axis_length_m": 6686.739,
        },
    }


def _check(metadata, resolution=(1280, 720), view="cab", chainage_m=2000.0):
    return G.check(metadata, AXIS, list(resolution) if resolution else None, view, chainage_m)


def _run(metadata):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False)
        path = handle.name
    try:
        return subprocess.run(
            [sys.executable, SCRIPT, "--metadata", path, "--axis", AXIS,
             "--resolution", "1280x720", "--view", "cab", "--at-chainage", "2000"],
            capture_output=True, text=True)
    finally:
        os.unlink(path)


# --- prawda liczona niezależnie -------------------------------------------------


def test_axis_length_is_computed_here_not_read_from_the_metadata():
    """Długość osi musi pochodzić z drugiej implementacji, nie z pliku, który sprawdza.

    Scena raportuje 6686,739 m — długość po zagęszczeniu krzywą Catmull-Rom krokiem
    5 m, a nie 6686,35 m z pola `length_m`. Ten sam krok liczy tu Python, więc obie
    strony porównania są niezależne.
    """
    computed = G.axis_length_m(AXIS)
    assert abs(computed - 6686.739) < 1e-3, computed

    with open(AXIS, encoding="utf-8") as handle:
        declared = json.load(handle)["length_m"]
    assert abs(computed - declared) > 0.3, (
        "gdyby zagęszczenie nic nie zmieniało, ten test nie dowodziłby niezależności")
    assert G.RING_STEP_M == 5.0


def test_scene_bbox_of_the_axis_matches_the_engine_axis_swap():
    """`SceneAxis.ToScene` to (X, Z, −Y). Kotwica bezwzględna stoi na tej zamianie."""
    lo, hi = G.axis_scene_bbox(AXIS)
    healthy = _healthy()["scene"]
    for axis in range(3):
        assert healthy["bbox_min"][axis] <= lo[axis] + 1e-6, axis
        assert healthy["bbox_max"][axis] >= hi[axis] - 1e-6, axis


def test_healthy_metadata_passes():
    assert _check(_healthy()) == []
    result = _run(_healthy())
    assert result.returncode == 0, result.stderr
    assert "policzone niezależnie" in result.stdout, result.stdout


# --- każda z siedmiu mutacji, które przeżyły audyt -----------------------------


def _mutate(**scene_changes):
    metadata = _healthy()
    metadata["scene"].update(scene_changes)
    return metadata


def test_gate_catches_every_mutation_that_survived_the_audit():
    """Siedem mutacji z audytu plus dwie własne. Każda musi dać niepustą listę."""
    healthy = _healthy()
    shifted = _healthy()
    shifted["scene"]["bbox_min"] = [v + 1000.0 for v in healthy["scene"]["bbox_min"]]
    shifted["scene"]["bbox_max"] = [v + 1000.0 for v in healthy["scene"]["bbox_max"]]

    blown = _healthy()
    blown["scene"]["bbox_min"] = [v * 10.0 for v in healthy["scene"]["bbox_min"]]
    blown["scene"]["bbox_max"] = [v * 10.0 for v in healthy["scene"]["bbox_max"]]
    blown["scene"]["size_m"] = [b - a for a, b in
                                zip(blown["scene"]["bbox_min"], blown["scene"]["bbox_max"])]

    wrong_resolution = _healthy()
    wrong_resolution["resolution"] = [640, 480]

    wrong_shot = _healthy()
    wrong_shot["last_shot"] = {"view": "Cab", "chainage_m": 0.0, "steps": 0}

    wrong_view = _healthy()
    wrong_view["last_shot"] = dict(healthy["last_shot"], view="Chase")

    cases = {
        "M01 chunks_loaded +7": _mutate(chunks_loaded=19),
        "M02 mesh_objects 0": _mutate(mesh_objects=0),
        "M03 bbox +1000 m": shifted,
        "M04 vertices/faces 0": _mutate(vertices=0, faces=0),
        "M05 axis_length_m 0": _mutate(axis_length_m=0.0),
        "M06 resolution 640x480": wrong_resolution,
        "M07 last_shot wyzerowany": wrong_shot,
        "size_m zwinięte": _mutate(size_m=[0.0, 0.0, 0.0]),
        "bryła rozdmuchana 10x": blown,
        "widok inny niż żądany": wrong_view,
        "chunks_declared 0": _mutate(chunks_declared=0, chunks_loaded=0),
    }
    survivors = [name for name, metadata in cases.items() if not _check(metadata)]
    assert not survivors, survivors


def test_gate_refuses_metadata_without_a_scene_section():
    problems = _check({"resolution": [1280, 720], "last_shot": {}})
    assert problems and "sekcji" in problems[0], problems


def test_gate_exit_code_is_nonzero_and_says_what_is_wrong():
    result = _run(_mutate(chunks_loaded=19))
    assert result.returncode == 1, result
    assert "19" in result.stderr and "12" in result.stderr, result.stderr


# --- próg wystawania poza oś ---------------------------------------------------


def test_slack_tolerance_is_the_tunnel_cross_section_not_a_round_number():
    """Bryła może wystawać poza oś dokładnie o przekrój tunelu, nie o „coś".

    Zmierzone rozszerzenia na pakiecie A: 1,2–4,7 m przy profilu 9,40 × 5,90 m.
    Próg wzięty z `profiles.dimensions`, więc zmiana profilu pociąga go za sobą.
    """
    width, height = profiles.dimensions("box_double")
    assert max(width, height) == 9.4, (width, height)

    healthy = _healthy()
    # Wystawanie o pół przekroju jest w porządku…
    ok = _healthy()
    ok["scene"]["bbox_max"] = [v + 4.0 for v in healthy["scene"]["bbox_max"]]
    ok["scene"]["size_m"] = [b - a for a, b in
                             zip(ok["scene"]["bbox_min"], ok["scene"]["bbox_max"])]
    assert _check(ok) == [], _check(ok)

    # …a o dwa przekroje już nie.
    too_much = _healthy()
    too_much["scene"]["bbox_max"] = [v + 2.0 * max(width, height) for v in healthy["scene"]["bbox_max"]]
    too_much["scene"]["size_m"] = [b - a for a, b in
                                   zip(too_much["scene"]["bbox_min"], too_much["scene"]["bbox_max"])]
    assert _check(too_much), "bryła dwa razy szersza od tunelu przeszła"


# --- workflow woła tę bramkę ---------------------------------------------------


def test_workflow_actually_runs_the_metadata_gate():
    with open(WORKFLOW, encoding="utf-8") as handle:
        text = handle.read()
    steps = re.split(r"\n {6}- name: ", text)[1:]
    gate = [step for step in steps if step.startswith("Shot metadata must describe this scene")]
    assert len(gate) == 1, "krok bramki metadanych zniknął albo zmienił nazwę"

    body = gate[0]
    assert "tools/ci/assert_shot_metadata.py" in body
    assert "--axis data/track/L1_A.json" in body, "bramka musi dostać oś do policzenia prawdy"
    assert "--resolution 1280x720" in body
    # Krok musi stać PO zrzutach, bo inaczej nie ma czego czytać.
    assert text.index("Shot metadata must describe this scene") > text.index("--shot=")

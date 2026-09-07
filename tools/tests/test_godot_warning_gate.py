#!/usr/bin/env python3
"""Bramka na ostrzeżenia Godota — testowana bez Godota.

Bramka, która mówi „ok" także wtedy, gdy nic nie sprawdza, jest bezużyteczna
(`reports/T-310-physics.md` §6). Ta jest o tyle podatna na zgnicie, że jej cała
skuteczność siedzi w JEDNEJ liście dopuszczonych: pozycja dopisana za szeroko —
albo dopasowanie po fragmencie zamiast po całej treści — zamienia ją w worek bez dna
i nikt tego nie zauważy, bo krok nadal będzie zielony.

Wzorce ostrzeżeń w tych testach są WKLEJONE z prawdziwego przebiegu Godota 4.7.2 mono
na pakiecie A (04.09.2026): `--line --limit-kmh=70` przez `xvfb-run` z `opengl3`.
"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(ROOT, "tools", "ci", "assert_no_godot_warnings.py")
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "godot-first-run.yml")

sys.path.insert(0, os.path.join(ROOT, "tools", "ci"))

import assert_no_godot_warnings as G  # noqa: E402


COLINEAR = (
    "WARNING: Target and up vectors are colinear. This is not advised as it may cause "
    "unwanted rotation around local Z axis.\n"
    "     at: looking_at (core/math/basis.cpp:1045)\n"
    "     C# backtrace (most recent call first):\n"
    "         [3] void MetroBxl.Game.FirstRun.PlaceEverything() (src/Game/FirstRun.cs:831)\n"
)

VSYNC = (
    "WARNING: Could not set V-Sync mode, as changing V-Sync mode is not supported by "
    "the graphics driver.\n"
    "     at: set_vsync_mode (servers/display_server.cpp:112)\n"
)

AUDIO = (
    "ALSA lib confmisc.c:855:(parse_card) cannot find card '0'\n"
    "ALSA lib pcm.c:2721:(snd_pcm_open_noupdate) Unknown PCM default\n"
    "WARNING: All audio drivers failed, falling back to the dummy driver.\n"
    "     at: init_output_device (drivers/alsa/audio_driver_alsa.cpp:97)\n"
)

CLEAN = (
    "Godot Engine v4.7.2.stable.mono.official.ed1daf0bf - https://godotengine.org\n"
    "[PRZEJAZD] tryb=line widok=Cab scenariusz=package-a-first-run\n"
    "[PRZEJAZD] koniec: kroków=89958 t=749.650 s chainage=6686.0 m powód=stopped\n"
)


def _log(text):
    handle = tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8")
    handle.write(text)
    handle.close()
    return handle.name


def _run(text):
    path = _log(text)
    try:
        done = subprocess.run(["python3", SCRIPT, path], capture_output=True, text=True)
    finally:
        os.unlink(path)
    return done


# --- co bramka uznaje za ostrzeżenie -----------------------------------------

def test_a_clean_run_has_no_warnings():
    assert G.warnings(CLEAN) == []
    assert G.offending(CLEAN) == []


def test_the_scene_warning_is_caught():
    assert G.offending(CLEAN + COLINEAR) == [
        "Target and up vectors are colinear. This is not advised as it may cause "
        "unwanted rotation around local Z axis."
    ]


def test_ten_warnings_are_counted_as_ten():
    """Sygnatura maszynowa usterki: dziesięć na przebieg, nie „jakieś"."""
    assert len(G.offending(CLEAN + COLINEAR * 10)) == 10


def test_the_at_line_and_the_backtrace_are_not_warnings():
    """Wiersz `at:` i ślad stosu należą do TEGO SAMEGO ostrzeżenia, nie do nowych."""
    assert len(G.warnings(COLINEAR)) == 1


def test_alsa_chatter_is_not_a_godot_warning():
    """Wiersze biblioteki ALSA nie mają przedrostka `WARNING:` i bramka ich nie widzi.

    Dlatego NIE MA ich na liście dopuszczonych: lista opisuje ostrzeżenia silnika,
    a nie wszystko, co pojawia się na stderr.
    """
    alsa_only = "\n".join(line for line in AUDIO.splitlines() if line.startswith("ALSA"))
    assert G.warnings(alsa_only) == []


# --- lista dopuszczonych -----------------------------------------------------

def test_the_environment_warnings_pass():
    assert G.offending(CLEAN + VSYNC + AUDIO) == []
    assert len(G.warnings(CLEAN + VSYNC + AUDIO)) == 2


def test_the_list_is_short_and_every_entry_carries_a_reason():
    """Krótka i jawna — inaczej przestaje być listą, a zaczyna być wyciszeniem."""
    assert len(G.ALLOWED) <= 4, G.ALLOWED
    for message, why in G.ALLOWED:
        assert message and not message.startswith("WARNING"), message
        assert len(why) >= 40, (message, why)


def test_matching_is_on_the_whole_message_not_a_fragment():
    """Fragment dopuszczonego ostrzeżenia nie może przepuścić innego ostrzeżenia.

    Ta granica jest cała różnica między listą a workiem bez dna: przy dopasowaniu
    `in` wpis o V-Sync przepuściłby każde ostrzeżenie, które go cytuje — a Godot
    cytuje własne komunikaty w śladach stosu.
    """
    doubled = "WARNING: Could not set V-Sync mode, as changing V-Sync mode is not " \
              "supported by the graphics driver. And the camera looks nowhere.\n"
    assert G.offending(doubled), "dłuższa treść przeszła jako dopuszczona"

    shorter = "WARNING: Could not set V-Sync mode.\n"
    assert G.offending(shorter), "krótsza treść przeszła jako dopuszczona"


def test_an_entry_for_something_that_never_happens_does_not_open_the_gate():
    """Kontrola negatywna listy: wpis obok nie może uciszyć ostrzeżenia sceny.

    Mutacja `message == allowed` -> `True` (albo dopasowanie po pustym napisie)
    przechodzi każdy test wyżej i pada dopiero tutaj.
    """
    original = G.ALLOWED
    try:
        G.ALLOWED = original + (("Ostrzeżenie, którego nigdy nie było.", "wpis kontrolny"),)
        assert G.offending(CLEAN + COLINEAR + VSYNC), \
            "dopisanie pozycji obok uciszyło prawdziwe ostrzeżenie"
        assert G.reason("Ostrzeżenie, którego nigdy nie było.") == "wpis kontrolny"
    finally:
        G.ALLOWED = original


# --- kod wyjścia -------------------------------------------------------------

def test_the_script_fails_on_a_scene_warning():
    done = _run(CLEAN + VSYNC + COLINEAR)
    assert done.returncode == 1, done.stdout + done.stderr
    assert "colinear" in done.stderr


def test_the_script_passes_a_clean_run_with_environment_noise():
    done = _run(CLEAN + VSYNC + AUDIO)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "0 spoza listy, 2 środowiskowych" in done.stdout


def test_a_missing_log_is_a_failure_not_a_pass():
    """Bramka bez wejścia ma paść. Log, którego nie ma, to przebieg, którego nie widać."""
    done = subprocess.run(
        ["python3", SCRIPT, os.path.join(ROOT, "build", "nie-ma-takiego-pliku.log")],
        capture_output=True, text=True)
    assert done.returncode == 1
    assert "brak logu" in done.stderr


# --- czy CI naprawdę tę bramkę woła ------------------------------------------

def _scene_runs(text):
    """(numer wiersza, całe wywołanie) dla każdego uruchomienia sceny w workflow."""
    lines = text.splitlines()
    runs = []
    for index, line in enumerate(lines):
        if "--path src/Game" not in line or line.lstrip().startswith("#"):
            continue
        cursor = index
        while lines[cursor].rstrip().endswith("\\") and cursor + 1 < len(lines):
            cursor += 1
        runs.append((index, cursor, "\n".join(lines[index:cursor + 1])))
    return runs


def test_every_scene_run_in_ci_goes_through_the_gate():
    """Każde uruchomienie sceny zapisuje log i przepuszcza go przez bramkę.

    Bez tego testu bramka jest jednym `git revert` od zniknięcia z połowy kroków,
    a job zostałby zielony — czyli dokładnie stan sprzed 04.09.2026.
    """
    text = open(WORKFLOW, encoding="utf-8").read()
    runs = _scene_runs(text)
    assert len(runs) >= 8, f"workflow uruchamia scenę tylko {len(runs)} razy"

    lines = text.splitlines()
    without_log = []
    without_gate = []
    for start, end, block in runs:
        if "2>&1 | tee" not in block:
            without_log.append(start + 1)
            continue
        # Bramka ma stać W TYM SAMYM kroku, niedaleko za wywołaniem. Sześć wierszy
        # starczy na komentarz między nimi i nie sięga następnego wywołania sceny.
        window = "\n".join(lines[end + 1:end + 7])
        if "assert_no_godot_warnings.py" not in window:
            without_gate.append(start + 1)

    assert not without_log, f"wywołania sceny bez logu stderr, wiersze: {without_log}"
    assert not without_gate, f"wywołania sceny bez bramki ostrzeżeń, wiersze: {without_gate}"


def test_the_gate_checks_the_log_that_the_run_actually_wrote():
    """Bramka wołana na CUDZYM logu przechodzi i nie sprawdza nic.

    To jest najtańszy sposób, żeby ta bramka zgniła po cichu: skopiowany krok
    zostawia starą ścieżkę logu, a stary log jest czysty. Nazwy plików są tu
    pobierane z tego samego wywołania, w którym stoi `tee`.
    """
    text = open(WORKFLOW, encoding="utf-8").read()
    lines = text.splitlines()
    mismatched = []
    for _, end, block in _scene_runs(text):
        log = block.split("2>&1 | tee", 1)[1].split()[0].strip('"')
        window = "\n".join(lines[end + 1:end + 7])
        if log not in window:
            mismatched.append(log)

    assert not mismatched, f"bramka nie sprawdza logów, które te przebiegi zapisały: {mismatched}"

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

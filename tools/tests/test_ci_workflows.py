#!/usr/bin/env python3
"""Testy odporności workflow CI. Bez zewnętrznych zależności, bez parsera YAML.

Powód: 02.09.2026 krok instalacji Blendera zawiesił się trzy razy na trzech różnych
runnerach, za każdym razem przed uruchomieniem ciała testu. Te testy pilnują, żeby
poprawka nie wyparowała po cichu przy następnej edycji workflow.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOWS = os.path.join(ROOT, ".github", "workflows")
HELPER = os.path.join(ROOT, "tools", "ci", "apt_install.sh")


def _workflows():
    return sorted(f for f in os.listdir(WORKFLOWS) if f.endswith((".yml", ".yaml")))


def _text(name):
    return open(os.path.join(WORKFLOWS, name), encoding="utf-8").read()


def test_ci_no_workflow_calls_apt_get_directly():
    """Instalacja pakietów idzie przez helper, żeby limit czasu był w jednym miejscu."""
    offenders = [name for name in _workflows() if "apt-get" in _text(name)]
    assert not offenders, offenders


def _steps(text):
    """Kroki workflow jako osobne bloki tekstu.

    Świadomie przez podział, nie przez `re.findall` po wzorcu zaczynającym się od
    nowej linii: taki wzorzec zjada `\n` przed następnym krokiem i kolejne dopasowanie
    nie ma od czego zacząć. Pierwsza wersja tego testu przechodziła właśnie dlatego,
    że nie widziała ANI JEDNEGO kroku instalacji — sprawdzone przez usunięcie
    `timeout-minutes` i ponowne uruchomienie.
    """
    parts = re.split(r"\n {6}- name: ", text)
    return parts[1:]


def test_ci_every_package_install_step_has_a_step_timeout():
    """Krok instalacji ma własny timeout — inaczej zawieszone pobranie zjada cały job."""
    checked = 0
    for name in _workflows():
        for step in _steps(_text(name)):
            if "apt_install.sh" not in step:
                continue
            checked += 1
            assert "timeout-minutes:" in step, (name, step.splitlines()[0].strip())
    assert checked == 5, f"oczekiwano pięciu kroków instalacji, znaleziono {checked}"


def test_ci_apt_helper_is_executable_and_retries():
    assert os.access(HELPER, os.X_OK), "tools/ci/apt_install.sh musi być wykonywalny"
    body = open(HELPER, encoding="utf-8").read()
    assert "Acquire::http::Timeout" in body and "Acquire::https::Timeout" in body
    assert "ATTEMPTS" in body and "sleep" in body


def test_ci_apt_helper_limits_a_single_attempt_not_only_the_whole_step():
    """Limit na próbę, nie tylko na krok.

    Limit wyłącznie na kroku workflow zabija instalację w połowie pierwszego
    podejścia i powtórka nigdy nie dostaje szansy — zmierzone na `visual-regression`
    02.09.2026: krok padł po 10 min 13 s, wciąż w pierwszym `apt-get`.
    """
    body = open(HELPER, encoding="utf-8").read()
    assert "sudo timeout" in body, "sygnał ma trafić w apt-get, nie w sudo"
    assert "UPDATE_TIMEOUT_S" in body and "INSTALL_TIMEOUT_S" in body
    assert "124" in body, "kod 124 z `timeout` musi być rozpoznany jako nieudana próba"


def test_ci_step_timeout_leaves_room_for_every_attempt():
    """Backstop na kroku musi być dłuższy niż wszystkie próby razem z odstępami."""
    body = open(HELPER, encoding="utf-8").read()
    attempts = int(re.search(r"ATTEMPTS=\$\{APT_ATTEMPTS:-(\d+)\}", body).group(1))
    update_s = int(re.search(r"UPDATE_TIMEOUT_S=\$\{APT_UPDATE_TIMEOUT_S:-(\d+)\}", body).group(1))
    install_s = int(re.search(r"INSTALL_TIMEOUT_S=\$\{APT_INSTALL_TIMEOUT_S:-(\d+)\}", body).group(1))
    backoff = int(re.search(r"BACKOFF_S=\$\{APT_BACKOFF_S:-(\d+)\}", body).group(1))
    # dwa wywołania helpera na krok: `update` i `install`, każde z własnym budżetem
    worst_case_s = (attempts * (update_s + install_s)
                    + 2 * backoff * sum(range(1, attempts + 1)))
    for name in _workflows():
        for step in _steps(_text(name)):
            if "apt_install.sh" not in step:
                continue
            declared = int(re.search(r"timeout-minutes: (\d+)", step).group(1))
            assert declared * 60 >= worst_case_s, (name, declared * 60, worst_case_s)


def test_ci_apt_helper_refuses_an_empty_package_list():
    """Pusta lista pakietów to błąd wywołania, nie cicha instalacja niczego."""
    import subprocess
    result = subprocess.run(["bash", HELPER], capture_output=True, text=True)
    assert result.returncode == 2, result
    assert "użycie" in result.stderr


def test_ci_blender_workflows_still_install_blender():
    """Odporność nie może po cichu zgubić samego pakietu."""
    for name in ("blender-smoke.yml", "tunnel-alignment.yml", "m7-shell.yml",
                 "visual-regression.yml", "godot-first-run.yml"):
        text = _text(name)
        assert "apt_install.sh blender " in text, name
        assert "libegl1" in text and "python3-numpy" in text, name

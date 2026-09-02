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


def test_ci_apt_helper_lets_apt_handle_a_dead_socket():
    """Zerwane połączenie ma łapać apt, nie zewnętrzny stoper.

    `Acquire::*::Timeout` przerywa martwe gniazdo po 30 s, a `Acquire::Retries`
    powtarza sam plik. Zewnętrzny limit jest sufitem na proces, nie mechanizmem
    ponawiania — inaczej wyrzuca do kosza 190 MB pobrane w połowie.
    """
    body = open(HELPER, encoding="utf-8").read()
    assert "sudo timeout" in body, "sygnał ma trafić w apt-get, nie w sudo"
    assert "Acquire::Retries" in body
    assert "124" in body, "kod 124 z `timeout` musi być rozpoznany i opisany"


def test_ci_install_is_not_retried_from_scratch():
    """`install` NIE jest powtarzany od zera.

    Zmierzone 02.09.2026 na `first-run`: trzy próby po 240 s, każda z postępem,
    każda ubita i zaczynająca od nowa — 13 minut na nic. Powtarzany jest tylko
    `update`, bo jest tani (11,7 MB w 2 s).
    """
    body = open(HELPER, encoding="utf-8").read()
    assert "apt_update" in body and "UPDATE_ATTEMPTS" in body
    assert "INSTALL_ATTEMPTS" not in body, "install nie ma pętli prób"
    install_calls = [line for line in body.splitlines()
                     if line.startswith("apt_run") and "install" in line]
    assert len(install_calls) == 1, install_calls


def test_ci_step_budget_covers_a_slow_mirror():
    """Sufit musi pomieścić pobranie 190 MB z wolnego lustra.

    Zmierzona prędkość lustra Azure w złym momencie: ~150 kB/s, czyli ponad
    20 minut samego pobierania. Sufit poniżej tego zamienia wolne, ale postępujące
    pobranie w twardą awarię — dokładnie to zrobiła pierwsza wersja tej poprawki.
    """
    body = open(HELPER, encoding="utf-8").read()
    install_s = int(re.search(r"INSTALL_TIMEOUT_S=\$\{APT_INSTALL_TIMEOUT_S:-(\d+)\}", body).group(1))
    measured_s = 190 * 1024 / 150
    assert install_s >= measured_s, (install_s, measured_s)
    checked = 0
    for name in _workflows():
        text = _text(name)
        job_budget = int(re.search(r"(?m)^    timeout-minutes: (\d+)$", text).group(1))
        for step in _steps(text):
            if "apt_install.sh" not in step:
                continue
            checked += 1
            step_budget = int(re.search(r"timeout-minutes: (\d+)", step).group(1))
            assert step_budget * 60 >= install_s, (name, step_budget * 60, install_s)
            # po instalacji ma jeszcze zostać czas na samą pracę joba
            assert job_budget - step_budget >= 10, (name, job_budget, step_budget)
    assert checked == 5, f"oczekiwano pięciu kroków instalacji, znaleziono {checked}"


def test_ci_blender_workflows_still_install_blender():
    """Odporność nie może po cichu zgubić samego pakietu."""
    for name in ("blender-smoke.yml", "tunnel-alignment.yml", "m7-shell.yml",
                 "visual-regression.yml", "godot-first-run.yml"):
        text = _text(name)
        assert "apt_install.sh blender " in text, name
        assert "libegl1" in text and "python3-numpy" in text, name

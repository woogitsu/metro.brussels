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

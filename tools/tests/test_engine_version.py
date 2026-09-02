#!/usr/bin/env python3
"""Wersja silnika jest zapisana w trzech miejscach i muszą się zgadzać.

Powód: 02.09.2026 podniesienie Godota z 4.3 na 4.7.2 wymagało zmiany w trzech
niezależnych plikach. Rozjazd między nimi nie wywala budowy od razu — projekt
z `config/features` na starą wersję Godot otworzy i tylko ostrzeże, a workflow
pobierający inny binarny Godot niż ten, pod który zbudowano `Godot.NET.Sdk`,
zawiedzie dopiero w kroku uruchomienia sceny. Wtedy przyczyna jest daleko od skutku.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CSPROJ = os.path.join(ROOT, "src", "Game", "MetroBxl.Game.csproj")
PROJECT_GODOT = os.path.join(ROOT, "src", "Game", "project.godot")
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "godot-first-run.yml")


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def sdk_version(text):
    """Wersja `Godot.NET.Sdk` z atrybutu Sdk, np. `4.7.2`."""
    match = re.search(r'Sdk="Godot\.NET\.Sdk/([0-9]+\.[0-9]+(?:\.[0-9]+)?)"', text)
    return match.group(1) if match else None


def workflow_version(text):
    """Wartość `GODOT_VERSION`, np. `4.7.2-stable`."""
    match = re.search(r"^\s*GODOT_VERSION:\s*(\S+)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def feature_version(text):
    """Wersja z `config/features` w project.godot, np. `4.7`."""
    match = re.search(r'config/features=PackedStringArray\("([0-9]+\.[0-9]+)"', text)
    return match.group(1) if match else None


def minor(version):
    """`4.7.2-stable` i `4.7` sprowadzone do wspólnego `4.7`."""
    if version is None:
        return None
    match = re.match(r"([0-9]+\.[0-9]+)", version)
    return match.group(1) if match else None


def test_all_three_places_declare_a_version():
    assert sdk_version(_read(CSPROJ)) is not None, "brak wersji Godot.NET.Sdk w csproj"
    assert workflow_version(_read(WORKFLOW)) is not None, "brak GODOT_VERSION w workflow"
    assert feature_version(_read(PROJECT_GODOT)) is not None, "brak config/features"


def test_sdk_and_workflow_agree():
    sdk = sdk_version(_read(CSPROJ))
    flow = workflow_version(_read(WORKFLOW))
    assert flow.startswith(sdk + "-"), (
        f"Godot.NET.Sdk {sdk} wobec GODOT_VERSION {flow}: workflow pobrałby "
        "inny silnik niż ten, pod który zbudowano warstwę gry")


def test_project_features_agree_with_the_sdk():
    sdk = sdk_version(_read(CSPROJ))
    features = feature_version(_read(PROJECT_GODOT))
    assert features == minor(sdk), (
        f"config/features {features} wobec Godot.NET.Sdk {sdk}")


def test_workflow_version_carries_a_release_channel():
    # Samo `4.7.2` nie istnieje jako tag wydania — URL pobrania składa się
    # z `${GODOT_VERSION}` i pobrałby 404.
    flow = workflow_version(_read(WORKFLOW))
    assert re.match(r"^[0-9]+\.[0-9]+(\.[0-9]+)?-(stable|beta[0-9]+|rc[0-9]+)$", flow), flow


def test_parsers_do_not_accept_a_mismatch():
    # Kontrole negatywne. Bez nich testy wyżej przechodziłyby także wtedy, gdyby
    # parsery zwracały `None` na wszystkim — porównanie `None == None` jest prawdziwe.
    assert sdk_version('<Project Sdk="Microsoft.NET.Sdk">') is None
    assert workflow_version("  GODOT_VERSIONS: 4.7.2-stable\n") is None
    assert feature_version('config/features=PackedStringArray("C#")') is None

    # I że zgodność naprawdę jest sprawdzana, a nie zawsze prawdziwa.
    assert minor("4.7.2-stable") == "4.7"
    assert minor("4.3-stable") == "4.3"
    assert minor("4.7.2") != minor("4.3")

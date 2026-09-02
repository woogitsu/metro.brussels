#!/usr/bin/env python3
"""Runtime .NET jest zapisany w wielu miejscach i muszą się zgadzać.

Powód: migracja 8 -> 10 z 02.09.2026 dotknęła pięciu plików projektu i trzech
workflow. Rozjazd między `TargetFramework` a `dotnet-version` w `setup-dotnet`
nie daje czytelnego błędu — job instaluje SDK, po czym `dotnet build` przewraca
się na komunikat o brakującym targeting packu, który nie wskazuje na workflow.

Powód drugi: .NET 8 kończy wsparcie 10.11.2026. Test pilnuje też, żeby projekt
nie osunął się z powrotem na wersję po dacie końca wsparcia.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOWS = os.path.join(ROOT, ".github", "workflows")

PROJECTS = [
    os.path.join("src", "Sim", "Sim.csproj"),
    os.path.join("src", "Sim.Runner", "Sim.Runner.csproj"),
    os.path.join("src", "Game", "MetroBxl.Game.csproj"),
    os.path.join("tests", "Sim.Tests", "Sim.Tests.csproj"),
    os.path.join("tests", "Game.Tests", "Game.Tests.csproj"),
]

# .NET 8 kończy wsparcie 10.11.2026 (Microsoft, polityka wsparcia .NET Core).
# Wersje poniżej tej granicy są odrzucane, żeby powrót do nich wymagał
# zmiany testu, a nie przeoczenia w jednym csproj.
MINIMUM_SUPPORTED_MAJOR = 10


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def target_framework(text):
    """Wartość `<TargetFramework>`, np. `net10.0`."""
    match = re.search(r"<TargetFramework>\s*(net[0-9]+\.[0-9]+)\s*</TargetFramework>", text)
    return match.group(1) if match else None


def tfm_major(tfm):
    """`net10.0` -> 10."""
    if tfm is None:
        return None
    match = re.match(r"net([0-9]+)\.", tfm)
    return int(match.group(1)) if match else None


def setup_dotnet_versions(text):
    """Wszystkie `dotnet-version:` z workflow, np. ['10.0.x']."""
    return re.findall(r"^\s*dotnet-version:\s*'([^']+)'\s*$", text, re.MULTILINE)


def _workflows():
    return sorted(f for f in os.listdir(WORKFLOWS) if f.endswith((".yml", ".yaml")))


def test_every_project_declares_a_target_framework():
    for rel in PROJECTS:
        tfm = target_framework(_read(os.path.join(ROOT, rel)))
        assert tfm is not None, f"{rel} bez <TargetFramework>"


def test_all_projects_share_one_target_framework():
    # Rdzeń, runner, warstwa gry i oba projekty testowe referują się nawzajem.
    # Projekt na starszym TFM nie zbuduje się wobec nowszej referencji, a błąd
    # wskaże referencję, nie rozjazd.
    found = {rel: target_framework(_read(os.path.join(ROOT, rel))) for rel in PROJECTS}
    assert len(set(found.values())) == 1, found


def test_target_framework_is_still_supported():
    for rel in PROJECTS:
        major = tfm_major(target_framework(_read(os.path.join(ROOT, rel))))
        assert major >= MINIMUM_SUPPORTED_MAJOR, (
            f"{rel} celuje w .NET {major}; wsparcie .NET 8 kończy się 10.11.2026")


def test_workflows_install_the_same_major_as_the_projects():
    major = tfm_major(target_framework(_read(os.path.join(ROOT, PROJECTS[0]))))
    for name in _workflows():
        for version in setup_dotnet_versions(_read(os.path.join(WORKFLOWS, name))):
            assert version.startswith(f"{major}."), (
                f"{name}: setup-dotnet {version} wobec projektów net{major}.0")


def test_at_least_one_workflow_installs_dotnet():
    # Bez tego test wyżej przechodziłby także wtedy, gdyby `dotnet-version`
    # zniknął ze wszystkich workflow — pętla po pustej liście nic nie sprawdza.
    total = sum(len(setup_dotnet_versions(_read(os.path.join(WORKFLOWS, n))))
                for n in _workflows())
    assert total >= 3, f"tylko {total} kroków setup-dotnet; było ich trzy"


def test_parsers_reject_what_they_should():
    assert target_framework("<TargetFramework>netstandard2.0</TargetFramework>") is None
    assert target_framework("<TargetFrameworks>net10.0;net8.0</TargetFrameworks>") is None
    assert setup_dotnet_versions("  dotnet-version: 10.0.x\n") == [], "bez cudzysłowów"
    assert tfm_major("net10.0") == 10
    assert tfm_major("net8.0") == 8
    assert tfm_major("net8.0") < MINIMUM_SUPPORTED_MAJOR

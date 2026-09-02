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


def workflows_with_setup_dotnet():
    """Nazwy workflow, które w ogóle instalują SDK."""
    return [n for n in _workflows()
            if "actions/setup-dotnet" in _read(os.path.join(WORKFLOWS, n))]


def install_dir_step_index(text):
    """Numer linii, w której workflow ustawia `DOTNET_INSTALL_DIR`; inaczej None."""
    match = re.search(r"^\s*echo\s+\"DOTNET_INSTALL_DIR=.*>>\s*\"\$GITHUB_ENV\"",
                      text, re.MULTILINE)
    return match.start() if match else None


def setup_dotnet_index(text):
    match = re.search(r"^\s*uses:\s*actions/setup-dotnet@", text, re.MULTILINE)
    return match.start() if match else None


def test_every_setup_dotnet_gets_a_writable_install_dir():
    """CI 02.09.2026: `setup-dotnet` celował w /usr/share/dotnet i padał na prawach.

    Runner właściciela nie jest rootem, więc domyślny katalog SDK dawał serię
    `mkdir: Permission denied`. Na jednorazowej maszynie GitHuba to nie wychodziło,
    bo tam runner jest rootem — i dlatego bramka musi być tutaj, a nie w głowie.
    """
    for name in workflows_with_setup_dotnet():
        text = _read(os.path.join(WORKFLOWS, name))
        assert install_dir_step_index(text) is not None, (
            f"{name}: setup-dotnet bez DOTNET_INSTALL_DIR — poleci do /usr/share/dotnet")


def test_install_dir_is_set_before_setup_dotnet_runs():
    # Kolejność nie jest kosmetyczna: `setup-dotnet` czyta zmienną w momencie
    # uruchomienia, więc krok ustawiający ją PO nim nie zmienia niczego.
    for name in workflows_with_setup_dotnet():
        text = _read(os.path.join(WORKFLOWS, name))
        assert install_dir_step_index(text) < setup_dotnet_index(text), (
            f"{name}: DOTNET_INSTALL_DIR ustawiany po kroku setup-dotnet")


def without_comments(text):
    """Linie workflow bez komentarzy YAML i bez komentarzy powłoki.

    Pierwsza wersja tego testu szukała `RUNNER_TOOL_CACHE` w całym pliku i
    przechodziła, bo napis stoi też w KOMENTARZU tłumaczącym, po co ten katalog.
    Mutacja podmieniająca kod na `$HOME` przeżyła. Bramka czytająca komentarze
    sprawdza dokumentację, nie zachowanie.
    """
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))


def test_install_dir_comes_from_the_runner_tool_cache():
    # `RUNNER_TOOL_CACHE` wskazuje `_tool` — rodzeństwo workspace'u, którego
    # `git clean -ffdx` z `actions/checkout` nie dotyka. Katalog w workspace
    # znikałby przy każdym checkoucie, a w /usr — nie dałby się utworzyć.
    for name in workflows_with_setup_dotnet():
        code = without_comments(_read(os.path.join(WORKFLOWS, name)))
        assert "RUNNER_TOOL_CACHE" in code, (
            f"{name}: katalog SDK nie pochodzi z tool cache (komentarz się nie liczy)")
        assert 'echo "::error::katalog SDK' in code, (
            f"{name}: brak kontroli, że katalog nie leży w workspace ani w /usr")


def test_the_comment_stripper_actually_strips():
    # Kontrola negatywna do poprawki wyżej.
    assert "RUNNER_TOOL_CACHE" not in without_comments("      # RUNNER_TOOL_CACHE\n")
    assert "RUNNER_TOOL_CACHE" in without_comments('      cache="$RUNNER_TOOL_CACHE"\n')


def test_there_is_something_to_check():
    # Bez tego trzy testy wyżej przechodziłyby po pustej liście workflow.
    assert len(workflows_with_setup_dotnet()) >= 3, workflows_with_setup_dotnet()


def test_parsers_reject_what_they_should():
    assert target_framework("<TargetFramework>netstandard2.0</TargetFramework>") is None
    assert target_framework("<TargetFrameworks>net10.0;net8.0</TargetFrameworks>") is None
    assert setup_dotnet_versions("  dotnet-version: 10.0.x\n") == [], "bez cudzysłowów"
    assert tfm_major("net10.0") == 10
    assert tfm_major("net8.0") == 8
    assert tfm_major("net8.0") < MINIMUM_SUPPORTED_MAJOR

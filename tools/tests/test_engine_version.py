#!/usr/bin/env python3
"""Wersja silnika jest zapisana w czterech miejscach i muszą się zgadzać.

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

#: CZWARTE miejsce, dopisane 04.09.2026. Trzy pierwsze to kod i workflow, więc
#: pilnowały się nawzajem — a dokument, z którego człowiek stawia środowisko, stał
#: obok i nikt go nie sprawdzał. Zmierzone: po podniesieniu 4.3 -> 4.7.2 (`60ea54f`)
#: `docs/23-environment.md` przez trzy dni mówił „Godot 4.3-stable mono", podawał
#: `GODOT_VERSION=4.3-stable` i CYTOWAŁ z `project.godot` treść, której tam nie ma.
#: Cała suita świeciła zielono, bo dokument nie był dla niej jednym z „trzech miejsc".
#: Kto postawiłby środowisko z tego dokumentu, dostałby silnik, pod który warstwa
#: gry nie jest zbudowana — i dowiedziałby się o tym dopiero przy uruchomieniu sceny.
DOC = os.path.join(ROOT, "docs", "23-environment.md")


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


def doc_versions(text):
    """Wszystkie wersje Godota podane w dokumencie jako STAN AKTUALNY.

    Bierze wystąpienia postaci `4.7.2-stable`, `GODOT_VERSION=…`, `Godot 4.7`
    i nagłówek sekcji. NIE bierze wierszy, które dokument sam oznacza jako
    historyczne — ten projekt przepisuje reguły, a nie dopisuje obok, więc
    zdanie „poprzednio było 4.3" jest poprawną treścią, nie rozjazdem.
    """
    # Marker historyczny liczy się dla CAŁEGO AKAPITU, nie dla jednego wiersza.
    # Zmierzone przy pisaniu tej bramki: zdanie „Poprzednia wersja mówiła" stało
    # w wierszu 299, a wersja „4.3-stable" w 300 — parser wierszowy uznał ją za
    # aktualną i bramka padała na własnym wyjaśnieniu. Ta sama pułapka, co przy
    # bramkach grepujących po całym pliku razem z komentarzami.
    out = set()
    historyczny = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            historyczny = False
            continue
        if re.search(r"poprzedni|było|podawała|mówiła|dawn|do 0[0-9]\.0[0-9]\.20|wcześniej",
                     stripped, re.I):
            historyczny = True
        if historyczny:
            continue
        for match in re.finditer(r"\b([0-9]+\.[0-9]+(?:\.[0-9]+)?)-stable\b", stripped):
            out.add(match.group(1))
        for match in re.finditer(r"Godot[^0-9\n]{0,12}([0-9]+\.[0-9]+(?:\.[0-9]+)?)", stripped):
            out.add(match.group(1))
    return out


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


def test_the_document_declares_the_same_engine_version():
    """`docs/23-environment.md` jest instrukcją stawiania środowiska, więc jego
    wersja silnika musi zgadzać się z kodem. Dokument mówiący inną wersję niż
    `Godot.NET.Sdk` nie jest nieaktualny — jest instrukcją, która nie działa."""
    sdk = sdk_version(_read(CSPROJ))
    flow = workflow_version(_read(WORKFLOW))
    declared = doc_versions(_read(DOC))
    assert declared, "dokument nie podaje ani jednej wersji Godota"

    dozwolone = {sdk, flow, minor(sdk)}
    obce = sorted(v for v in declared if v not in dozwolone)
    assert not obce, (
        f"docs/23-environment.md podaje jako aktualne wersje Godota {obce}, "
        f"a kod jest na {sdk} (workflow {flow})")

    # CYTAT z `project.googot` sprawdzany OSOBNO, bo to on był pierwotnym błędem:
    # dokument podawał jako cytat treść, której w pliku nie ma. Kontrola negatywna
    # przy pisaniu tej bramki: podmiana `"4.7"` na `"4.5"` w cytacie NIE wywracała
    # asercji wyżej, bo w tym wierszu nie ma ani słowa „Godot", ani sufiksu
    # `-stable` — parser wersji go po prostu nie widział. Fałszywy cytat jest
    # gorszy od nieaktualnego zdania: czytający sprawdza go wzrokiem i wierzy.
    cytat = feature_version(_read(DOC))
    prawda = feature_version(_read(PROJECT_GODOT))
    assert cytat == prawda, (
        f"docs/23-environment.md cytuje z project.godot config/features "
        f"{cytat!r}, a w pliku jest {prawda!r}")


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

    # Parser dokumentu: bierze stan aktualny, pomija zdanie o stanie poprzednim.
    assert doc_versions("Godot 4.7.2-stable mono") == {"4.7.2"}
    assert doc_versions("poprzednio było Godot 4.3-stable") == set()
    assert doc_versions("do 02.09.2026 stał tu Godot 4.3-stable") == set()
    assert "4.3" in doc_versions("## 4. Godot 4.3-stable mono"), \
        "parser przestał widzieć wersję w nagłówku sekcji"

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

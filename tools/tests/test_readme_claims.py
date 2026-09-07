#!/usr/bin/env python3
"""README podaje liczby i wersje — ta bramka liczy je z repozytorium i porównuje.

Powód: na `e982bc0` README twierdził „41 plików" w `src/Sim/` (było 44), „Siedem
workflowów" (było 10) i „Godot 4.3 mono" w dwóch miejscach (`config/features`
mówi 4.7 od #121). Żadna bramka tego nie łapała, bo README był jedynym miejscem,
w którym te liczby stały — a liczba stojąca w jednym miejscu i nigdzie nie liczona
rozjeżdża się bezszelestnie.

Zasada tego modułu: **nie ma tu ani jednej oczekiwanej liczby**. Prawdę liczy
`os.walk` po `src/Sim/`, `glob` po `.github/workflows/` i `config/features`
z `src/Game/project.godot`; README jest stroną porównywaną, nigdy źródłem.
Wpisanie tu „44" byłoby drugą kopią tej samej wiedzy i rozjechałoby się dokładnie
tak samo jak pierwsza.

Bramka działa w obie strony:
  - README mówi mniej/inaczej niż repozytorium → pada (ktoś zepsuł README);
  - repozytorium rośnie, README stoi → pada (README nie dotrzymało kroku).
Druga strona jest tą, która się faktycznie rozjechała.

Kontrakt na README, od którego zależy parsowanie:
  - **pierwszy akapit sekcji `## CI`** jest listą workflowów i niczym innym: każdy
    token w grawisach w tym akapicie jest nazwą pliku workflow bez `.yml`, a przed
    słowem „workflowów" stoi ich liczba słownie. Zdania o runnerze, etykietach
    i o tym, który workflow nie jest bramką, należą do dalszych akapitów — inaczej
    `self-hosted` wjechałby na listę workflowów;
  - liczba plików rdzenia stoi jako „N plików `.cs`" / „N pliki `.cs`" w akapicie
    o `src/Sim/`. Jednostka jest jawna, bo „41 plików" nie dało się sprawdzić
    poleceniem: nie wiadomo było, czy liczy `.csproj`;
  - każda wzmianka wersji silnika ma postać „Godot X.Y" albo „Godot X.Y.Z".
"""
import glob
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
README = os.path.join(ROOT, "README.md")
SIM_DIR = os.path.join(ROOT, "src", "Sim")
WORKFLOW_DIR = os.path.join(ROOT, ".github", "workflows")
PROJECT_GODOT = os.path.join(ROOT, "src", "Game", "project.godot")

# Katalogi wyplute przez `dotnet build`. Leżą w .gitignore, ale `os.walk` ich nie
# zna, a policzone podniosłyby liczbę plików rdzenia po każdej lokalnej budowie.
BUILD_DIRS = {"bin", "obj"}

# Liczebniki, którymi README zapisuje liczbę workflowów. Prozą, nie cyfrą — więc
# bramka musi umieć je przeczytać. To słownik języka, nie kopia stanu repozytorium.
NUMERALS = {
    "jeden": 1, "dwa": 2, "trzy": 3, "cztery": 4, "pięć": 5, "sześć": 6,
    "siedem": 7, "osiem": 8, "dziewięć": 9, "dziesięć": 10, "jedenaście": 11,
    "dwanaście": 12, "trzynaście": 13, "czternaście": 14, "piętnaście": 15,
    "szesnaście": 16, "siedemnaście": 17, "osiemnaście": 18, "dziewiętnaście": 19,
    "dwadzieścia": 20,
}


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


# --- prawda z repozytorium -------------------------------------------------

def core_files():
    """Pliki `.cs` w `src/Sim/`, bez wyjścia budowy. Zwraca ścieżki relatywne."""
    found = []
    for base, dirs, names in os.walk(SIM_DIR):
        dirs[:] = [d for d in dirs if d not in BUILD_DIRS]
        for name in names:
            if name.endswith(".cs"):
                found.append(os.path.relpath(os.path.join(base, name), ROOT))
    return sorted(found)


def workflow_stems():
    """Nazwy plików `.github/workflows/*.yml` bez rozszerzenia."""
    paths = glob.glob(os.path.join(WORKFLOW_DIR, "*.yml"))
    return sorted(os.path.basename(p)[: -len(".yml")] for p in paths)


def project_godot_minor(text):
    """`4.7` z `config/features=PackedStringArray("4.7", ...)`."""
    match = re.search(r'config/features=PackedStringArray\("([0-9]+\.[0-9]+)"', text)
    return match.group(1) if match else None


# --- to, co twierdzi README ------------------------------------------------

def readme_core_file_count(text):
    """Liczba z „`src/Sim/`, N plików `.cs`". None, gdy README tego nie podaje."""
    match = re.search(r"`src/Sim/`,\s*([0-9]+)\s+plik\w*\s+`\.cs`", text)
    return int(match.group(1)) if match else None


def ci_list_paragraph(text):
    """Pierwszy akapit sekcji `## CI`. None, gdy sekcji nie ma."""
    match = re.search(r"^## CI\s*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if not match:
        return None
    paragraphs = [p for p in match.group(1).split("\n\n") if p.strip()]
    return paragraphs[0] if paragraphs else None


def readme_workflow_count(paragraph):
    """Liczebnik przed słowem „workflowów", np. „Dziesięć" -> 10."""
    match = re.search(r"(\w+)\s+workflow\w*", paragraph or "", re.UNICODE)
    if not match:
        return None
    return NUMERALS.get(match.group(1).lower())


def readme_workflow_names(paragraph):
    """Tokeny w grawisach z akapitu listy workflowów."""
    return sorted(set(re.findall(r"`([^`]+)`", paragraph or "")))


def readme_godot_versions(text):
    """Wszystkie wzmianki „Godot X.Y[.Z]" w README, w kolejności wystąpienia."""
    return re.findall(r"Godot\s+([0-9]+\.[0-9]+(?:\.[0-9]+)?)", text)


def minor(version):
    """`4.7.2` i `4.7` sprowadzone do wspólnego `4.7`."""
    match = re.match(r"([0-9]+\.[0-9]+)", version or "")
    return match.group(1) if match else None


# --- bramki ---------------------------------------------------------------

def test_readme_core_file_count_matches_repository():
    files = core_files()
    claimed = readme_core_file_count(_read(README))
    assert claimed is not None, (
        "README nie podaje liczby plików `.cs` w `src/Sim/` w formie „N plików `.cs``; "
        "bez jednostki tej liczby nie da się sprawdzić poleceniem")
    # Bramka nie przechodzi pusta: pusty `src/Sim/` znaczy zepsute liczenie,
    # a nie zgodę na dowolną liczbę w README.
    assert len(files) > 0, f"nie znaleziono ani jednego pliku .cs w {SIM_DIR}"
    assert claimed == len(files), (
        f"README mówi {claimed} plików `.cs` w src/Sim/, repozytorium ma "
        f"{len(files)}: {files}")


def test_readme_workflow_count_and_names_match_repository():
    stems = workflow_stems()
    assert len(stems) > 0, f"nie znaleziono ani jednego *.yml w {WORKFLOW_DIR}"

    paragraph = ci_list_paragraph(_read(README))
    assert paragraph is not None, "README nie ma sekcji `## CI`"

    claimed_count = readme_workflow_count(paragraph)
    assert claimed_count is not None, (
        "pierwszy akapit sekcji `## CI` nie podaje liczby workflowów słownie "
        f"przed słowem „workflowów”; akapit: {paragraph!r}")
    assert claimed_count == len(stems), (
        f"README mówi {claimed_count} workflowów, .github/workflows/ ma "
        f"{len(stems)}: {stems}")

    claimed_names = readme_workflow_names(paragraph)
    assert claimed_names == stems, (
        f"README wymienia {claimed_names}, repozytorium ma {stems}; "
        f"brakuje w README: {sorted(set(stems) - set(claimed_names))}, "
        f"nadmiar w README: {sorted(set(claimed_names) - set(stems))}")


def test_readme_godot_version_matches_project_godot():
    features = project_godot_minor(_read(PROJECT_GODOT))
    assert features is not None, "brak `config/features` w src/Game/project.godot"

    mentions = readme_godot_versions(_read(README))
    # Bramka nie przechodzi pusta: gdyby README przestał podawać wersję silnika,
    # pętla poniżej nie wykonałaby ani jednego obrotu i test byłby zielony
    # z powodu, który nie ma nic wspólnego ze zgodnością.
    assert len(mentions) > 0, "README nie podaje wersji Godota w formie „Godot X.Y”"
    checked = 0
    for version in mentions:
        assert minor(version) == features, (
            f"README mówi „Godot {version}”, src/Game/project.godot ma "
            f"config/features {features}")
        checked += 1
    assert checked == len(mentions)


def test_parsers_reject_a_mismatch():
    """Kontrole negatywne parserów.

    Bez nich testy wyżej przechodziłyby także wtedy, gdyby każdy parser zwracał
    `None` albo pustą listę na wszystkim: `None == None` jest prawdziwe, a pętla
    po pustej liście nie sprawdza niczego. Każda asercja `is not None` i każdy
    licznik wyżej ma tu swoją drugą stronę.
    """
    # Parsery nie widzą tego, czego nie ma.
    assert readme_core_file_count("`src/Sim/`, 41 plików, i tyle") is None
    assert project_godot_minor('config/features=PackedStringArray("C#")') is None
    assert readme_godot_versions("bez Godota, ale z Godotem") == []
    assert ci_list_paragraph("## Struktura\n\ncoś\n") is None
    assert readme_workflow_count("Siedemnaścioro workflowów") is None
    assert readme_workflow_names("") == []

    # I że parsery czytają to, co README naprawdę pisze.
    assert readme_core_file_count("`src/Sim/`, 44 pliki `.cs`, kompiluje się") == 44
    assert readme_core_file_count("`src/Sim/`, 7 plików `.cs`") == 7
    assert project_godot_minor('config/features=PackedStringArray("4.7", "C#")') == "4.7"
    assert readme_godot_versions("Godot 4.3 mono i Godot 4.7.2") == ["4.3", "4.7.2"]
    assert readme_workflow_count("Siedem workflowów, jeden na bramkę") == 7
    assert readme_workflow_count("Dziesięć workflowów") == 10
    assert readme_workflow_names("`a-b`, `c-d`.") == ["a-b", "c-d"]

    # I że zgodność wersji naprawdę jest sprawdzana, a nie zawsze prawdziwa.
    assert minor("4.7.2") == "4.7"
    assert minor("4.3") != minor("4.7")

    # Akapit listy workflowów to pierwszy akapit sekcji, nie cała sekcja —
    # inaczej `self-hosted` z akapitu o runnerze byłby nazwą workflow.
    sample = "## CI\n\n`a-b`, `c-d`.\n\nna etykiecie `self-hosted`.\n\n## Dalej\n"
    assert readme_workflow_names(ci_list_paragraph(sample)) == ["a-b", "c-d"]

    # Liczenie plików rdzenia pomija wyjście budowy.
    assert BUILD_DIRS == {"bin", "obj"}
    assert all("/obj/" not in p and "/bin/" not in p for p in core_files())

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

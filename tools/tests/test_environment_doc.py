#!/usr/bin/env python3
"""`docs/23-environment.md` mówi, GDZIE narzędzia leżą — i mówi to samo, co skrypty.

**Skąd ta bramka.** 6.D48, z mojej własnej pomyłki zmierzonej 08.09.2026. Sesja
sprawdziła obecność Blendera przez `command -v blender`, dostała puste wyjście
i zapisała w raporcie, że Blendera na maszynie nie ma — po czym pominęła częściowo
na tej podstawie dwie pozycje kolejki (6.C4 i 6.D24). `blender_install.sh`
uruchomiony później odpowiedział `5.2.1 już jest`, a data katalogu wskazywała
06.09.2026. Binarium leżało poza `PATH` przez dwa dni, bo TAK MA LEŻEĆ: katalog
musi przeżyć `git clean -ffdx` z `actions/checkout`. Brakowało wyłącznie zapisu,
gdzie go szukać — dokument mówił, jak instalować, i nie mówił, gdzie już jest.

**Czego ta bramka pilnuje.** Dwóch rzeczy, i obie są jednozdaniowe:

1. ścieżka katalogu cache stoi w dokumencie **i** w skrypcie, i jest to ta sama
   ścieżka. Podmiana katalogu w `tools/ci/blender_install.sh` bez podmiany
   w dokumencie wywraca tę bramkę — dokładnie tak, jak `test_engine_version.py`
   wywraca się na rozjeździe wersji Godota, i z tego samego powodu: dokument,
   z którego CZŁOWIEK stawia środowisko, jest jednym z pilnowanych miejsc, a nie
   prozą obok kodu;
2. dokument mówi **wprost**, że `command -v` nie odpowiada na pytanie o obecność.
   To jest treść, którą pominięcie kosztowało dwie pozycje, więc jej brak ma być
   awarią, a nie stylistyką.

**Czego NIE pilnuje, świadomie.** Nie pilnuje, że ścieżka cache stoi w kodzie
w jednym miejscu. Nie stoi: `${RUNNER_TOOL_CACHE:-$HOME/.cache/metro-tools}`
powtarza się w instalatorze Blendera i w trzech workflowach (zmierzone
08.09.2026 — pięć wystąpień w czterech plikach). Scalenie tego do jednego pliku,
tak jak wersja Blendera stoi w `blender-version.txt`, jest zmianą w kodzie CI
i leży poza zakresem 6.D48. Bramka za to **sprawdza, że te wystąpienia się
zgadzają** — rozjazd między nimi byłby gorszy niż samo powtórzenie.
"""
import glob
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOC = os.path.join(ROOT, "docs", "23-environment.md")
INSTALLER = os.path.join(ROOT, "tools", "ci", "blender_install.sh")
WORKFLOWS = os.path.join(ROOT, ".github", "workflows")

#: Podkatalogi, które CI zakłada w cache — po jednym na narzędzie. Nazwy nie są tu
#: wpisane jako oczekiwanie, tylko jako lista miejsc, z których się je CZYTA:
#: `metro-blender` z instalatora, dwa pozostałe z workflowów.
POD_KATALOGI_Z_KODU = ("metro-blender", "metro-godot", "metro-dotnet")


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def bez_komentarzy(text):
    """Wiersze bez komentarzy powłoki i YAML.

    Ta sama ostrożność, co w `test_dotnet_version.py::without_comments` i z tego
    samego zmierzonego powodu: `RUNNER_TOOL_CACHE` stoi w tych plikach także
    w komentarzu, który tłumaczy, po co ten katalog. Bramka czytająca komentarze
    sprawdzałaby dokumentację, nie zachowanie.
    """
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))


def fallback_cache(text):
    """Wartość domyślna z `${RUNNER_TOOL_CACHE:-<ścieżka>}`, np. `$HOME/.cache/metro-tools`.

    Zwraca `None`, gdy w kodzie nie ma tej konstrukcji — czyli gdy katalog przestał
    pochodzić z tool cache i mógłby wylądować w workspace.
    """
    match = re.search(r"\$\{RUNNER_TOOL_CACHE:-([^}]+)\}", bez_komentarzy(text))
    return match.group(1) if match else None


def wszystkie_fallbacki():
    """(plik, ścieżka) dla każdego pliku kodu, który liczy katalog cache."""
    found = []
    for path in [INSTALLER] + sorted(glob.glob(os.path.join(WORKFLOWS, "*.yml"))):
        cache = fallback_cache(_read(path))
        if cache is not None:
            found.append((os.path.relpath(path, ROOT), cache))
    return found


def podkatalog_instalatora(text):
    """Nazwa podkatalogu z wiersza `DIR="$CACHE/<nazwa>/$VERSION"` instalatora."""
    match = re.search(r'DIR="\$CACHE/([^/"]+)/', bez_komentarzy(text))
    return match.group(1) if match else None


def podkatalogi_workflowow():
    """Nazwy podkatalogów z wierszy `dir="$cache/<nazwa>..."` w workflowach."""
    names = set()
    for path in sorted(glob.glob(os.path.join(WORKFLOWS, "*.yml"))):
        for name in re.findall(r'dir="\$cache/([^/"]+)', bez_komentarzy(_read(path))):
            names.add(name)
    return names


# --- 1. dokument nazywa katalog, w którym narzędzia FAKTYCZNIE leżą -----------------

def test_the_document_names_the_cache_directory_the_installer_uses():
    """Ścieżka cache stoi w dokumencie i jest tą samą, którą liczy instalator.

    Kontrola negatywna (WYKONANA 08.09.2026): podmiana `metro-tools` na
    `metro-cache` w `tools/ci/blender_install.sh` bez zmiany w dokumencie
    wywraca ten test.
    """
    cache = fallback_cache(_read(INSTALLER))
    assert cache is not None, (
        "tools/ci/blender_install.sh nie liczy katalogu z ${RUNNER_TOOL_CACHE:-...} — "
        "Blender może wylądować w workspace i zniknąć przy checkoucie")
    doc = _read(DOC)
    assert cache in doc, (
        f"docs/23-environment.md nie podaje katalogu {cache}, w którym instalator "
        "kładzie Blendera — czytający nie ma jak sprawdzić, czy narzędzie już jest")
    assert "RUNNER_TOOL_CACHE" in doc, (
        "docs/23-environment.md nie nazywa zmiennej RUNNER_TOOL_CACHE, więc nie mówi, "
        "czym ten katalog nadpisać na runnerze")


def test_every_place_in_the_code_computes_the_same_cache_directory():
    """Instalator i workflowy muszą liczyć TĘ SAMĄ ścieżkę domyślną.

    Ścieżka jest powtórzona (patrz docstring modułu) i tego ta pozycja nie zmienia;
    ale rozjazd między kopiami dawałby dwa katalogi cache, z których jeden zawsze
    byłby pusty — czyli objaw nieodróżnialny od braku narzędzia.
    """
    found = wszystkie_fallbacki()
    assert len(found) >= 4, f"za mało miejsc liczących cache: {found}"
    unikalne = {cache for _, cache in found}
    assert len(unikalne) == 1, f"rozjazd ścieżek cache w kodzie: {found}"


def test_the_document_names_every_tool_subdirectory():
    """Trzy podkatalogi cache — Blender, Godot, .NET — stoją w dokumencie.

    Nazwy są CZYTANE z kodu, nie wpisane w test: `metro-blender` z instalatora,
    pozostałe z workflowów. Dopisanie czwartego narzędzia do CI bez wiersza
    w dokumencie wywraca ten test.
    """
    z_kodu = {podkatalog_instalatora(_read(INSTALLER))} | podkatalogi_workflowow()
    z_kodu.discard(None)
    assert set(POD_KATALOGI_Z_KODU) <= z_kodu, (
        f"kod nie zakłada już katalogów {sorted(set(POD_KATALOGI_Z_KODU) - z_kodu)} — "
        "jeżeli to zamierzone, poprawa idzie razem z dokumentem")
    doc = _read(DOC)
    brak = sorted(n for n in z_kodu if n not in doc)
    assert not brak, (
        f"docs/23-environment.md nie nazywa podkatalogów cache {brak}, "
        "a CI je zakłada — czytający szuka narzędzia nie tam, gdzie leży")


# --- 2. dokument mówi wprost, czego `command -v` NIE mówi ---------------------------

def test_the_document_says_command_v_does_not_answer_the_presence_question():
    """Zdanie o `command -v` jest treścią pozycji 6.D48, nie ozdobą.

    Kontrola negatywna (WYKONANA 08.09.2026): usunięcie akapitu „`command -v` nie
    odpowiada na pytanie…" z dokumentu wywraca ten test.
    """
    doc = _read(DOC)
    assert "command -v" in doc, "dokument nie wspomina `command -v` ani raz"
    # Samo wystąpienie napisu nie wystarczy — musi stać w zdaniu o TYM, że sonda
    # na obecność w PATH nie odpowiada na pytanie o obecność na maszynie.
    wzorzec = re.compile(
        r"`command -v`[^.\n]{0,80}nie (?:odpowiada|mówi|rozstrzyga)", re.IGNORECASE)
    assert wzorzec.search(doc), (
        "docs/23-environment.md nie mówi WPROST, że `command -v` nie odpowiada na "
        "pytanie o obecność narzędzia — a to jedno zdanie jest powodem tej pozycji")


def test_the_document_shows_how_to_find_the_binary_without_path():
    """Dokument podaje sondę, która działa BEZ dowiązania w `PATH`.

    Zdanie „narzędzia leżą tam i tam" bez polecenia, które je stamtąd wyciąga,
    zostawia czytającego z tym samym problemem, tylko lepiej opisanym.
    """
    doc = _read(DOC)
    assert "bash tools/ci/blender_install.sh" in doc, (
        "dokument nie pokazuje, że instalator Blendera jest własną sondą i wypisuje "
        "ścieżkę na stdout")
    assert re.search(r"-maxdepth 4[^\n]*-name blender", doc), (
        "dokument nie podaje sondy `find` dla Blendera z właściwą głębokością — "
        "binarium leży cztery poziomy pod korzeniem cache, a -maxdepth 3 daje pustkę")
    assert "DOTNET_ROOT" in doc and "$HOME/.dotnet" in doc, (
        "dokument nie mówi, gdzie leży SDK ani czym je wskazać, gdy nie ma go w PATH")


# --- 3. kontrole negatywne parserów ------------------------------------------------

def test_parsers_reject_what_they_should():
    # Bez tego trzy testy wyżej przechodziłyby także z parserem, który zwraca
    # `None` na wszystkim — a wtedy `brak` jest puste zawsze.
    assert fallback_cache('cache="${RUNNER_TOOL_CACHE:-$HOME/.cache/metro-tools}"') \
        == "$HOME/.cache/metro-tools"
    assert fallback_cache('cache="$HOME/.cache/metro-tools"') is None, "bez tool cache"
    assert fallback_cache('# cache="${RUNNER_TOOL_CACHE:-$HOME/.cache/x}"') is None, \
        "komentarz nie jest kodem"
    assert podkatalog_instalatora('DIR="$CACHE/metro-blender/$VERSION"') == "metro-blender"
    assert podkatalog_instalatora('DIR="$CACHE/$VERSION/x"') == "$VERSION", \
        "parser czyta pierwszy człon, jakikolwiek by był"
    assert podkatalog_instalatora('DIR="$CACHE/metro-blender"') is None, \
        "jeden czlon bez wersji w sciezce to nie ten wzorzec"
    assert podkatalog_instalatora('BIN="$DIR/blender"') is None


def test_the_comment_stripper_actually_strips():
    assert "RUNNER_TOOL_CACHE" not in bez_komentarzy("  # RUNNER_TOOL_CACHE\n")
    assert "RUNNER_TOOL_CACHE" in bez_komentarzy('  cache="$RUNNER_TOOL_CACHE"\n')


def test_there_is_something_to_check():
    # Bramka nad pustą listą plików przechodzi zawsze i nie mówi nic.
    assert os.path.isfile(DOC), DOC
    assert os.path.isfile(INSTALLER), INSTALLER
    assert len(sorted(glob.glob(os.path.join(WORKFLOWS, "*.yml")))) >= 3


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

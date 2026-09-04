#!/usr/bin/env python3
"""Dokumentacja XML i komentarze w `src/` — to, co da się sprawdzić mechanicznie.

Ta bramka powstała po trzech usterkach, których **żaden test nie widział**, bo
wszystkie stały w komentarzu, a nie w wyniku, który cokolwiek porównuje. Ta sama
rodzina co `test_axis_claims.py` i `test_t401_citation.py`.

Zmierzone na `888c41e`, wszystkie trzy przechodziły przez pełną suitę:

1. `TrackAxis.CoversChord` nosiła **dwa bloki `<summary>`** — odziedziczony opis
   `MaxDeviationFromSourceM` (o odległości od łamanej źródłowej) stał nad predykatem
   o zasięgu osi, a sama `MaxDeviationFromSourceM` została bez dokumentacji.
   Kompilator tego nie zgłasza: dwa `<summary>` w jednym bloku `///` są dla niego
   poprawnym XML-em.
2. `DesignAssumptions.StationStopWindowM` twierdziła, że **peron ma 94,0 m**, gdy
   decyzja właściciela z 04.09.2026 (T-212) to **95,0 m**. 94,0 m to długość składu
   M7 i dlatego ta liczba wygląda tu wiarygodnie — jest poprawna w kilkunastu innych
   miejscach repozytorium, tylko nie tam, gdzie mowa o peronie.
3. Ta sama dokumentacja mieszała podstawy procentu: „5,0 m to 5,3 % **połowy**
   peronu" — 5,3 % jest od CAŁEGO peronu, od połowy wychodzi dwa razy tyle.

Bramki niżej pilnują tych trzech rzeczy z osobna. Dwie ostatnie liczą procent
i długość peronu z ŹRÓDŁA (stała C# obok i `DESIGN_PLATFORM_LENGTH_M` z generatora),
a nie z liczby wpisanej w test — decyzja właściciela o innej długości peronu ma
zapalić tę bramkę, nie ominąć ją.

CZEGO TA BRAMKA NIE ROBI: nie sprawdza, czy dokumentacja mówi PRAWDĘ o tym, co robi
metoda — tego nie da się zrobić tanio. Wykrywa tylko dwa `<summary>` w jednym bloku
`///`, czyli ślad, który zostawia zarówno przeklejenie dokumentacji z metody na
metodę, jak i wstawienie nowej metody pod cudzy komentarz.
"""

import glob
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Projekty C#, w których stoi dokumentacja XML. `obj/` i `bin/` to wyjście budowy.
CSHARP_ROOTS = (
    os.path.join(ROOT, "src", "Sim"),
    os.path.join(ROOT, "src", "Sim.Runner"),
    os.path.join(ROOT, "src", "Game"),
)

ASSUMPTIONS = os.path.join(ROOT, "src", "Game", "DesignAssumptions.cs")
STATION_COMPONENTS = os.path.join(ROOT, "tools", "track", "station_components.py")

#: Podstawy procentu, które wolno nazwać w komentarzu, i ułamek długości peronu,
#: którym każda z nich jest. „peron" bez przymiotnika znaczy CAŁY peron.
PERCENT_BASES = (
    ("połowy peronu", 0.5),
    ("całego peronu", 1.0),
    ("peronu", 1.0),
)

#: Liczba w polskim zapisie, z jednostką „m" — tak stoją wymiary w komentarzach.
_METRES = r"(\d{1,3},\d{1,2})\s*m\b"

#: Twierdzenie o wymiarze peronu: słowo „peron*" i pierwsza długość w tym samym
#: zdaniu (`[^.]` nie przechodzi przez kropkę, więc sąsiednie zdanie nie wpada).
PLATFORM_CLAIM = re.compile(r"peron\w*[^.]{0,80}?" + _METRES)

#: Procent z jawnie nazwaną podstawą, np. „10,5 % połowy peronu".
PERCENT_CLAIM = re.compile(
    r"(\d{1,3},\d)\s*%\s*(" + "|".join(base for base, _ in PERCENT_BASES) + r")")


def cs_files():
    """Wszystkie pliki `.cs` projektów C#, bez wyjścia budowy."""
    found = []
    for root in CSHARP_ROOTS:
        for path in sorted(glob.glob(os.path.join(root, "**", "*.cs"), recursive=True)):
            parts = os.path.relpath(path, root).split(os.sep)
            if "obj" in parts or "bin" in parts:
                continue
            found.append(path)
    return found


def doc_runs(text):
    """Ciągłe bloki linii `///`. Zwraca `(numer pierwszej linii, treść bloku)`.

    Blok kończy się na pierwszej linii, która nie zaczyna się od `///` — dokładnie
    tak, jak kompilator wiąże dokumentację z następującym po niej składnikiem.
    """
    runs = []
    current = None
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("///"):
            if current is None:
                current = [number, []]
            current[1].append(stripped[3:].strip())
        elif current is not None:
            runs.append((current[0], " ".join(current[1])))
            current = None
    if current is not None:
        runs.append((current[0], " ".join(current[1])))
    return runs


def runs_with_two_summaries(text):
    """Bloki dokumentacji, w których `<summary>` występuje więcej niż raz."""
    return [(number, body) for number, body in doc_runs(text) if body.count("<summary>") > 1]


def _prose(path):
    """Treść pliku bez znaczników `///` i ze zwiniętymi białymi znakami."""
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    text = re.sub(r"^\s*///", " ", text, flags=re.M)
    return re.sub(r"\s+", " ", text)


def _platform_length_m():
    """`DESIGN_PLATFORM_LENGTH_M` z generatora stacji — jedyne źródło tej liczby."""
    with open(STATION_COMPONENTS, encoding="utf-8") as handle:
        match = re.search(r"^DESIGN_PLATFORM_LENGTH_M\s*=\s*([0-9.]+)", handle.read(), re.M)
    assert match, f"{STATION_COMPONENTS} nie podaje DESIGN_PLATFORM_LENGTH_M"
    return float(match.group(1))


def _stop_window_m():
    """`StationStopWindowM` z tego samego pliku, w którym stoi komentarz o procencie."""
    with open(ASSUMPTIONS, encoding="utf-8") as handle:
        match = re.search(
            r"const\s+double\s+StationStopWindowM\s*=\s*([0-9.]+)", handle.read())
    assert match, f"{ASSUMPTIONS} nie podaje StationStopWindowM"
    return float(match.group(1))


# --- dwa bloki <summary> na jednym składniku -----------------------------------

def test_no_documentation_block_carries_two_summaries():
    """Jeden składnik = jedno `<summary>`. Drugie znaczy dokumentację nie na miejscu.

    Defekt, który to zapala, wyglądał tak: pod opisem „największa odległość punktu
    zagęszczonej osi od łamanej źródłowej" stała metoda `CoversChord`, czyli predykat
    o zasięgu osi, a opisana metoda była dwadzieścia linii niżej — bez dokumentacji.
    """
    files = cs_files()
    assert len(files) > 40, f"przejrzano {len(files)} plików .cs — liczenie jest zepsute"
    doubled = []
    for path in files:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        for number, body in runs_with_two_summaries(text):
            doubled.append(f"{os.path.relpath(path, ROOT)}:{number}: {body[:70]}…")
    assert not doubled, (
        "bloki dokumentacji z dwoma <summary> — pierwszy opisuje najprawdopodobniej "
        f"inny składnik: {doubled}")


def test_the_two_summary_scanner_actually_sees_two_summaries():
    """Kontrola dodatnia skanera — bramka wyżej nie może przechodzić przez pustkę.

    Ten sam wzorzec, który stał w `TrackAxis.cs`: dwa bloki `<summary>` w jednym
    ciągu linii `///`. Bez tej kontroli literówka w `count("<summary>")` zamieniłaby
    bramkę w napis.
    """
    defect = (
        "    /// <summary>Pierwsza.</summary>\n"
        "    /// <summary>Druga.</summary>\n"
        "    public void M() { }\n"
    )
    assert runs_with_two_summaries(defect), "skaner nie widzi dwóch <summary> w jednym bloku"
    healthy = (
        "    /// <summary>Pierwsza.</summary>\n"
        "    public void A() { }\n"
        "\n"
        "    /// <summary>Druga.</summary>\n"
        "    public void B() { }\n"
    )
    assert not runs_with_two_summaries(healthy), "skaner myli dwie metody z jedną"


# --- liczby o peronie w DesignAssumptions.cs ----------------------------------

def test_platform_dimensions_in_design_assumptions_come_from_the_generator():
    """Każda długość peronu w `DesignAssumptions.cs` to `DESIGN_PLATFORM_LENGTH_M` albo jej połowa.

    Powód, dla którego bramka jest potrzebna: 94,0 m to długość składu M7 i występuje
    w repozytorium kilkanaście razy POPRAWNIE. Przy peronie była błędna i wyglądała
    identycznie. Test porównuje z generatorem, nie z liczbą wpisaną tutaj, więc
    decyzja właściciela o innej długości peronu zapali go, zamiast go ominąć.
    """
    length = _platform_length_m()
    allowed = {round(length, 3), round(length / 2.0, 3)}
    prose = _prose(ASSUMPTIONS)
    claims = [float(value.replace(",", ".")) for value in PLATFORM_CLAIM.findall(prose)]
    assert claims, (
        "w DesignAssumptions.cs nie ma ani jednego wymiaru peronu — albo zniknął opis "
        "górnego ograniczenia okna, albo wzorzec przestał go łapać")
    wrong = [value for value in claims if round(value, 3) not in allowed]
    assert not wrong, (
        f"długości peronu niezgodne z DESIGN_PLATFORM_LENGTH_M = {length} m "
        f"(dozwolone {sorted(allowed)}): {wrong}")


def test_percent_of_the_platform_is_computed_from_the_base_it_names():
    """Procent w komentarzu musi wynikać z podstawy, którą sam nazywa.

    Defekt: „5,0 m to 5,3 % połowy peronu" — 5,3 % jest od CAŁEGO peronu (5,0 / 95,0),
    od połowy wychodzi 10,5 % (5,0 / 47,5). Podstawy różnią się dwukrotnie, więc taki
    zapis myli czytelnika o czynnik 2 w wielkości, która pilnuje otwierania drzwi
    poza krawędzią peronu.
    """
    length = _platform_length_m()
    window = _stop_window_m()
    fractions = dict(PERCENT_BASES)
    prose = _prose(ASSUMPTIONS)
    found = PERCENT_CLAIM.findall(prose)
    assert found, (
        "w DesignAssumptions.cs nie ma procentu z nazwaną podstawą — okno zatrzymania "
        "opisywało swój udział w peronie, a wzorzec tego nie widzi")
    bad = []
    for claimed, base in found:
        base_m = length * fractions[base]
        expected = round(100.0 * window / base_m, 1)
        if abs(float(claimed.replace(",", ".")) - expected) > 0.05:
            bad.append(
                f"komentarz mówi {claimed} % {base}, a {window} m z {base_m} m "
                f"to {expected} %")
    assert not bad, f"procent nie zgadza się z nazwaną podstawą: {bad}"

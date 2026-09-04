#!/usr/bin/env python3
"""Dolne ograniczenie prędkości liniowej: osiem wystąpień, pięć plików, jedno źródło.

`reports/T-401-line-run.md` §4 wyprowadza dolne ograniczenie prędkości liniowej dla
sieci: najmniejszy limit, przy którym cały pakiet mieści się w rozkładzie z T-113,
policzony niezależnie w Pythonie i w C#. Dla sieci wiąże **maksimum kolumny C#** po
sześciu pakietach — dziś odcinek Beaulieu → Demey w L5_D.

TA LICZBA SIĘ RUSZA. #86 przeliczyło kilometraże stacji i ograniczenie spadło
z 58,75 km/h na 58,68 km/h. Pierwsza wartość została po tym w OŚMIU wystąpieniach
w pięciu plikach naraz:

- `reports/R-006-line-speed.md` — dwa zdania o stanie bieżącym (§4 i §7);
- `docs/TASKS.md` — dwa wiersze podsumowania T-401 i R-006;
- `src/Sim/Signalling/SignallingPlan.cs` — dwa napisy `basis`/`SignallingAssumption`;
- `tests/Sim.Tests/SignallingPlanTests.cs` — PRÓG ASERCJI `kmh >= 58.75`;
- `data/design/signalling/classic-2026.json` — pole `default_permitted_speed_kmh.basis`.

Nic tego nie łączyło z T-401. `Plik_planu_jest_dokladnie_tym_co_daje_regula_generowania`
pilnuje, że JSON w `data/` jest bajt w bajt tym, co wypisuje generator — i to jest
mocna kontrola, ale wiąże PLIK Z KODEM, a nie kod ze źródłem liczby. Oba mogły
cytować tę samą nieaktualną wartość i cały zestaw był zielony. Pozostałe siedem
wystąpień to napisy i literały, więc nie było wyniku, który cokolwiek porównuje.

Bramka nie trzyma DRUGIEJ KOPII tej liczby. Liczy ją z tabeli §4 raportu, więc
przeliczenie T-401 natychmiast żąda poprawienia cytatów, a nie odwrotnie. Zmierzone:
mutacja `58,68 -> 59,10` w wierszu L5_D tabeli wywraca skan cytatów i próg asercji.

O ZAPISIE DO `data/`. `CLAUDE.md` §4 pkt 6 mówi, że `data/` jest tylko do odczytu.
Ten jeden napis został tam jednak poprawiony, bo `classic-2026.json` NIE JEST danymi
o sieci: plik sam deklaruje w `$comment`, że powstał z reguły przez
`SignallingPlan.FromAxis`, `docs/15-classic-signalling.md` §4 mówi to samo, a przede
wszystkim `Plik_planu_jest_dokladnie_tym_co_daje_regula_generowania` **wywraca się**,
gdy plik przestaje być równy wyjściu generatora. Zmierzone: po poprawieniu napisu
w `SignallingPlan.cs` i przed poprawieniem pliku `dotnet test tests/Sim.Tests` dawał
`Failed: 2, Passed: 329` — ten test i `Wczytanie_i_zapis_planu_daja_ten_sam_plik`.
Zostawienie pliku byłoby więc nie poszanowaniem §4 pkt 6, tylko czerwonym zestawem.
"""

import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOURCE = os.path.join(ROOT, "reports", "T-401-line-run.md")
CSHARP_TEST = os.path.join(ROOT, "tests", "Sim.Tests", "SignallingPlanTests.cs")

#: Pakiety, na które T-401 §4 liczy ograniczenie. Nie po to, żeby trzymać drugą kopię
#: liczb, ale żeby tabela przeczytana pusto albo w połowie nie dała cichego maksimum.
PACKAGES = {"L1_A", "L1_B", "L2_E", "L5_C", "L5_D", "L6_F"}

#: Wiersz tabeli §4: `| L5_D | 57,64 | **58,68** | +1,04 | ... | ... |`
ROW = re.compile(
    r"^\|\s*(L\d_[A-F])\s*\|\s*([\d,]+)\s*\|\s*\*\*([\d,]+)\*\*\s*\|", re.M)

#: Prędkość CYTOWANA: liczba, po której stoi jednostka. Bez wymogu `km/h` wzorzec
#: łapałby daty — `docs/TASKS.md` ma w tym samym wierszu „notatki DH z 11.02.2008",
#: a `11.02` wygląda jak `58.68`. Kontrola negatywna na to jest w tym module.
SPEED = re.compile(r"(\d{2}[,.]\d{2})\s*km/h")

#: Słownictwo zdania HISTORYCZNEGO. Konwencja tego repozytorium każe zapisywać, co
#: mówiła poprzednia wersja tekstu, więc `58,75` w takim zdaniu jest POPRAWNĄ treścią,
#: nie dryfem. Pomijanie idzie z granulacją AKAPITU, nie wiersza: marker potrafi stać
#: w innym wierszu niż liczba (tak samo jak w `test_engine_version.py`).
#:
#: Markery mówią o POPRZEDNIEJ WERSJI TEGO ZDANIA, a nie o przeszłości w ogóle,
#: i to jest różnica zmierzona, nie stylistyczna. Pierwsza wersja tej listy miała
#: `sprzed`, `wtedy`, `było` i `wcześniej` — i wyłączała bramkę na wierszu
#: `docs/TASKS.md` z żywym cytatem, bo w tym samym wierszu stoi „notatki DH
#: z 11.02.2008 o sieci **sprzed** układu z 2009". To zdanie opisuje przeszłość
#: SIECI, nie przeszłość dokumentu, a bramka przez jedno słowo przestawała
#: pilnować cytatu. `przed #\d` wymaga numeru PR-a, więc w „sprzed układu" nie trafia.
HISTORICAL = re.compile(
    r"poprzedni|podawa|mówił|przed #\d|do #\d|stał[ao] (tu|w tym)|"
    r"[Dd]o \d{2}\.\d{2}\.20\d{2} sta", re.I)

#: Pliki, w których cytat może stać. `reports/T-401-line-run.md` jest ŹRÓDŁEM, więc
#: nie jest cytatem samego siebie. `build/` to wyjścia przebiegów, nie tekst
#: utrzymywany przez człowieka.
#:
#: `data/` jest w skanie, choć zgodność wygenerowanego JSON-a z generatorem pilnuje
#: już `Plik_planu_jest_dokladnie_tym_co_daje_regula_generowania` po stronie C#.
#: To nie jest nadmiar: tamten test wiąże PLIK Z KODEM, a nie kod z T-401, więc sam
#: przepuściłby oba na tej samej nieaktualnej liczbie. Skan tutaj mierzy drugi,
#: niezależny koniec tego łańcucha.
SCANNED = ("reports", "docs", "src", "tests", "data")
EXCLUDED = (os.path.join(ROOT, "reports", "T-401-line-run.md"),)


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def lower_bound_kmh():
    """Dolne ograniczenie dla SIECI: maksimum kolumny C# w tabeli §4 T-401."""
    rows = ROW.findall(_read(SOURCE))
    found = {package: float(csharp.replace(",", ".")) for package, _py, csharp in rows}
    assert set(found) == PACKAGES, sorted(found)
    return max(found.values())


def _units(path):
    """(etykieta, treść) — akapity dla Markdowna, wiersze dla kodu.

    Dla `.md` jednostką jest akapit, bo zdanie historyczne rozkłada się na kilka
    wierszy. Dla `.cs` jednostką jest wiersz: napisy są tam sklejane z wierszy
    i cytat mieści się w jednym, a akapit objąłby pół listy założeń razem z liczbami,
    które nie mają z tym cytatem nic wspólnego.
    """
    text = _read(path)
    label = os.path.relpath(path, ROOT)
    if path.endswith(".md"):
        offset = 1
        for chunk in text.split("\n\n"):
            # WIERSZ TABELI JEST WŁASNĄ JEDNOSTKĄ, nie częścią akapitu. Tabela nie
            # jest prozą: `docs/TASKS.md` ma tabelę, w której jeden wiersz cytuje
            # ograniczenie, a inne mówią o zupełnie innych sprawach. Sklejone w akapit
            # dawały jednostkę, którą marker z DOWOLNEGO wiersza wyłączał całą.
            lines = chunk.split("\n")
            if any(line.startswith("|") for line in lines):
                for index, line in enumerate(lines):
                    yield f"{label}:{offset + index}", line
            else:
                yield f"{label}:{offset}", chunk
            offset += chunk.count("\n") + 2
        return
    for number, line in enumerate(text.splitlines(), start=1):
        yield f"{label}:{number}", line


def _citations():
    """Jednostki, które cytują dolne ograniczenie z T-401, bez zdań historycznych."""
    for top in SCANNED:
        for folder, _dirs, files in os.walk(os.path.join(ROOT, top)):
            for name in sorted(files):
                if not name.endswith((".md", ".cs", ".json")):
                    continue
                path = os.path.join(folder, name)
                if path in EXCLUDED:
                    continue
                for label, unit in _units(path):
                    if "T-401" not in unit or "ogranicz" not in unit.lower():
                        continue
                    if HISTORICAL.search(unit):
                        continue
                    yield label, unit


def test_t401_lower_bound_comes_from_the_table_and_not_from_a_second_copy():
    """Bramka bez tego testu mogłaby czytać tabelę pusto i porównywać z niczym."""
    rows = ROW.findall(_read(SOURCE))
    assert len(rows) == len(PACKAGES), rows
    bound = lower_bound_kmh()
    binding = [package for package, _py, csharp in rows
               if float(csharp.replace(",", ".")) == bound]
    assert len(binding) == 1, binding
    assert 50.0 < bound < 80.0, bound


def test_every_citation_of_the_t401_lower_bound_carries_todays_number():
    """Napis z liczbą nie jest wynikiem, więc nic go dotąd nie porównywało.

    Mutacja, która przed tą bramką przechodziła całą suitę: przywrócenie `58,75 km/h`
    w którymkolwiek z pięciu miejsc. Tak właśnie #86 zostawiło je wszystkie.
    """
    bound = lower_bound_kmh()
    stale = []
    checked = 0
    for label, unit in _citations():
        for raw in SPEED.findall(unit):
            checked += 1
            value = float(raw.replace(",", "."))
            if abs(value - bound) > 1e-9:
                # Przecinek dziesiętny tylko w LICZBIE. Pierwsza wersja wołała
                # `.replace(".", ",")` na całym napisie i komunikat mówił
                # „docs/TASKS,md" — nazwa pliku, której nie da się otworzyć.
                expected = f"{bound:.2f}".replace(".", ",")
                stale.append(
                    f"{label}: cytuje {raw} km/h, T-401 §4 daje {expected} km/h")
    assert not stale, f"cytaty sprzed przeliczenia T-401: {stale}"
    assert checked >= 5, (
        f"bramka znalazła tylko {checked} cytowanych prędkości — dotąd było ich sześć, "
        "więc albo skan przestał czytać pliki, albo cytaty zniknęły niezauważone")


def test_the_csharp_threshold_tracks_the_t401_lower_bound():
    """Próg asercji to jedyne miejsce, w którym ta liczba coś ROZSTRZYGA.

    Cztery pozostałe są napisami dla czytającego. Ten jeden decyduje, czy zestaw
    `Sim.Tests` przejdzie — i był przybity do wartości sprzed #86. C# nie czyta
    raportu, więc zgodność musi pilnować bramka po stronie narzędzi.
    """
    source = _read(CSHARP_TEST)
    match = re.search(
        r"dolnego_ograniczenia_z_T_401.*?Assert\.IsTrue\(\s*kmh\s*>=\s*([\d.]+)",
        source, re.S)
    assert match, "nie znaleziono progu w SignallingPlanTests.cs"
    assert float(match.group(1)) == lower_bound_kmh(), (
        f"próg w asercji to {match.group(1)}, a T-401 §4 daje {lower_bound_kmh():.2f}")


def test_a_date_is_not_mistaken_for_a_speed():
    """`11.02.2008` w tym samym wierszu co cytat nie jest prędkością.

    Bez wymogu jednostki wzorzec łapałby `11.02` i bramka żądałaby „poprawienia"
    daty notatki prasowej z 2008 roku na dzisiejsze ograniczenie prędkości.
    """
    assert SPEED.findall("notatki DH z 11.02.2008 o sieci") == []
    assert SPEED.findall("Ograniczenie dolne z T-401: 58,68 km/h") == ["58,68"]


def test_a_historical_sentence_is_not_treated_as_drift():
    """Zdanie o poprzedniej wartości MA zostać w dokumencie i nie wywracać bramki."""
    assert HISTORICAL.search("Do 04.09.2026 stała w tym zdaniu wartość sprzed #86.")
    assert HISTORICAL.search("Wiersz był próbą przy ograniczeniu, jakie podawało T-401.")
    assert not HISTORICAL.search(
        "leży powyżej dolnego ograniczenia 58,68 km/h z T-401 i zostawia rezerwę")

    # Przeszłość SIECI nie jest przeszłością DOKUMENTU. Ten wiersz stoi dziś
    # w `docs/TASKS.md` i cytuje ograniczenie jako stan bieżący; słowo „sprzed"
    # dotyczy układu linii z 2009 roku, nie poprzedniej wersji zdania. Pierwsza
    # wersja listy markerów wyłączała na nim bramkę.
    assert not HISTORICAL.search(
        "72/50 km/h pochodzi z notatki DH z 11.02.2008 o sieci sprzed układu z 2009 "
        "— klasa `manufacturer_or_trade_press`. Ograniczenie dolne z T-401: 58,68 km/h")

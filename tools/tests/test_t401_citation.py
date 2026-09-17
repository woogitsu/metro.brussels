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
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

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
        for folder, _dirs, files in TW.walk(os.path.join(ROOT, top)):
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


#: CAŁY wiersz tabeli §4, wszystkie sześć pól — 6.D238 (16.09.2026).
#:
#: `ROW` wyżej bierze TRZY PIERWSZE pola i to wystarcza do maksimum, ale nie wiąże
#: wiersza z pakietem: **zamiana kolumny C# między dwoma pakietami zostawia maksimum
#: bez zmian**, więc dotąd przechodziła. Zmierzone 16.09.2026 podstawieniem
#: L5_D ↔ L6_F (58,68 ↔ 55,05): `python3 tools/tests/test_all.py test_t401_citation.py`
#: dał **5/5 przeszło**. Strony C# to nie ratuje i to też jest zmierzone, nie założone:
#: `grep -rn "T-401-line-run" --include=*.cs` daje dwa trafienia i **oba są
#: komentarzami** (`tests/Sim.Tests/LineRunTests.cs:18`,
#: `tests/Sim.Tests/SignallingPlanTests.cs:321`).
#: **Wzorzec NIE JEST zakotwiczony na końcu wiersza i to jest poprawka z pomiaru,
#: a nie wygoda (17.09.2026, 6.D238).** Pierwsza wersja kończyła się na `\|\s*$`,
#: czyli żądała, żeby kolumn było DOKŁADNIE sześć. Kontrola DODATNIA to obaliła:
#: dopisanie siódmej kolumny do wszystkich sześciu wierszy — praca POPRAWNA, którą
#: blok tej pozycji wymienia wprost („tabela ma kolumnę, którą kolejne przebiegi
#: dopisują") — oślepiało czytnik do ZERA wierszy i zapalało TRZY bramki, w tym
#: podłogę niżej. Przewidziane było ZIELONE, zmierzone 51/54. To jest 6.D27 w czystej
#: postaci: bramka, która pali się na pracy poprawnej, zostaje wyłączona, nie
#: naprawiona. Po zdjęciu kotwicy ta sama mutacja daje 54/54.
#:
#: Kolumn wymaganych jest sześć PIERWSZYCH, w tej kolejności; siódma i dalsze są
#: czytnikowi obojętne. Zawężenia po lewej stronie zostają: pakiet, dwie liczby
#: z pogrubioną drugą, różnica ze znakiem i dwa odcinki.
WIERSZ_PELNY = re.compile(
    r"^\|\s*(L\d_[A-F])\s*\|\s*([\d,]+)\s*\|\s*\*\*([\d,]+)\*\*\s*\|"
    r"\s*([+-][\d,]+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", re.M)

#: Zdanie §4, które NAZYWA wiersz wiążący — „rośnie z X km/h (Python, wiąże ODCINEK)
#: do Y km/h (C#, ten sam odcinek)". Jest to drugi, niezależny koniec tego samego
#: łańcucha: tabela mówi, ile, a to zdanie — KTÓRY odcinek.
ZDANIE_WIAZACE = re.compile(
    r"z \*\*([\d,]+) km/h\*\*\s*\(Python,\s*wiąże\s+([^)]+?)\)\s*"
    r"do\s*\*\*([\d,]+) km/h\*\*\s*\(C#", re.S)

#: Ile wierszy tabeli §4 czyta wiązanie arytmetyczne. Zmierzone 16.09.2026 na
#: `e420f14`: tabela ma **6 wierszy po 6 kolumn, czyli 36 komórek**, a **CYTOWANY
#: przez bramki jest DOKŁADNIE JEDEN wiersz z sześciu** — L5_D, i to wyłącznie przez
#: swoją wartość C# (58,68 km/h, jedenaście wystąpień w pięciu plikach). Pozostałe
#: pięć wierszy, czyli 30 z 36 komórek, nie było przed 6.D238 związane niczym.
#:
#: **Próg jest KW, a nie równością, i to jest wybór wymuszony przez 6.D108.** Raport
#: jest zapisem swojego dnia; równość na CAŁEJ tabeli zapalałaby się na dopisaniu
#: wiersza, czyli na pracy poprawnej (6.D27). Liczbę wierszy przybija zresztą już
#: `set(found) == PACKAGES` w `lower_bound_kmh`, więc druga równość nie dodałaby nic
#: prócz drugiego miejsca do poprawiania.
MIN_WIERSZY_Z_ARYTMETYKA = 6


def wiersze_pelne(tekst=None):
    """`[(pakiet, python, csharp, delta, odcinek_py, odcinek_cs)]` — tabela §4."""
    return WIERSZ_PELNY.findall(_read(SOURCE) if tekst is None else tekst)


def _na_liczbe(surowa):
    """Liczba z komórki tabeli: przecinek dziesiętny, opcjonalny znak."""
    return float(surowa.replace(",", "."))


def niespojne_arytmetycznie(tekst=None):
    """`[(pakiet, python, csharp, delta)]` dla wierszy, w których C# − Python ≠ Δ."""
    zle = []
    for pakiet, py, cs, delta, _op, _oc in wiersze_pelne(tekst):
        if round(_na_liczbe(cs) - _na_liczbe(py), 2) != round(_na_liczbe(delta), 2):
            zle.append((pakiet, py, cs, delta))
    return zle


def test_skan_widzi_zmierzona_liczbe_wierszy_tabeli_paragrafu_4():
    """Próg KW na sam SKAN — 6.D238.

    Wzorzec sześciopolowy jest dłuższy od `ROW` o trzy pola, więc łatwiej mu oślepnąć
    na przeformatowaniu tabeli. Zero wierszy znaczyłoby „nie ma niespójnych", czyli
    to samo co zielono — a to jest rodzina, którą projekt tropi od 6.D27.
    """
    wiersze = wiersze_pelne()
    assert len(wiersze) >= MIN_WIERSZY_Z_ARYTMETYKA, (
        "wzorzec sześciopolowy widzi %d wierszy tabeli §4 przy progu %d — "
        "16.09.2026 było ich 6 (36 komórek); spadek znaczy oślepły wzorzec, "
        "a nie skróconą tabelę" % (len(wiersze), MIN_WIERSZY_Z_ARYTMETYKA))
    assert len(wiersze) == len(ROW.findall(_read(SOURCE))), (
        "wzorzec sześciopolowy widzi %d wierszy, a trzypolowy %d — jeden z nich "
        "czyta tabelę w połowie"
        % (len(wiersze), len(ROW.findall(_read(SOURCE)))))


def test_kolumna_roznicy_zgadza_sie_z_arytmetyka_w_KAZDYM_wierszu():
    """Wiązanie, które łapie ZAMIANĘ KOLUMNY MIĘDZY PAKIETAMI — 6.D238.

    **Wiąże wiersz ze sobą samym, a nie tabelę z drugą kopią liczb**, i to jest cała
    różnica wobec `lower_bound_kmh`: maksimum kolumny jest niewrażliwe na przestawienie
    jej wartości między wierszami, a Δ nie jest. Dopisanie NOWEGO wiersza zostaje przy
    tym pracą poprawną — nowy wiersz musi tylko zgadzać się sam ze sobą (6.D108).

    Zmierzone 16.09.2026: dziś zgadza się wszystkie sześć wierszy; po zamianie
    kolumny C# między L5_D a L6_F dwa z nich przestają (L5_D: 55,05 − 57,64 = −2,59
    opisane jako +1,04; L6_F: 58,68 − 54,10 = +4,58 opisane jako +0,95).
    """
    zle = niespojne_arytmetycznie()
    assert zle == [], (
        "w tabeli §4 kolumna różnicy nie wychodzi z własnego wiersza: %s — "
        "tak wygląda kolumna przestawiona między pakietami" % zle)

    # KONTROLA PRZYRZĄDU: ta sama tabela z zamienioną kolumną MUSI dać czerwień.
    # Bez tego zdanie „zgadza się wszystkie sześć" jest prawdą także dla czytnika,
    # który nie widzi ani jednego wiersza.
    podmieniona = _read(SOURCE).replace(
        "| L5_D | 57,64 | **58,68** | +1,04 |",
        "| L5_D | 57,64 | **55,05** | +1,04 |", 1).replace(
        "| L6_F | 54,10 | **55,05** | +0,95 |",
        "| L6_F | 54,10 | **58,68** | +0,95 |", 1)
    assert podmieniona != _read(SOURCE), (
        "podstawienie kontrolne niczego nie zmieniło — wiersze tabeli §4 zmieniły "
        "kształt i kontrola przyrządu mierzy tekst, którego nie ma")
    zlapane = {p for p, _py, _cs, _d in niespojne_arytmetycznie(podmieniona)}
    assert zlapane == {"L5_D", "L6_F"}, (
        "zamiana kolumny C# między L5_D a L6_F złapana jako %s, a ma być jako "
        "oba pakiety naraz" % (sorted(zlapane) or "nic"))

    # Druga strona kontroli: wiersz DOPISANY i spójny sam ze sobą jest pracą poprawną
    # i zapalić się nie ma — inaczej bramka czerwieniałaby od kolejnego przebiegu.
    dopisany = _read(SOURCE).replace(
        "| L6_F | 54,10 | **55,05** | +0,95 | Bockstael → Stuyvenbergh | Bockstael → Stuyvenbergh |",
        "| L6_F | 54,10 | **55,05** | +0,95 | Bockstael → Stuyvenbergh | Bockstael → Stuyvenbergh |\n"
        "| L9_G | 50,00 | **51,25** | +1,25 | Nowy → Odcinek | Nowy → Odcinek |", 1)
    assert niespojne_arytmetycznie(dopisany) == [], (
        "wiersz DOPISANY i spójny sam ze sobą zapalił bramkę: %s — bramka "
        "zapalająca się na pracy poprawnej zostaje wyłączona, nie naprawiona (6.D27)"
        % niespojne_arytmetycznie(dopisany))


def test_wiersz_wiazacy_jest_TYM_ktory_nazywa_proza_paragrafu_4():
    """Drugi koniec łańcucha: nie WARTOŚĆ, tylko KTÓRY wiersz ją daje — 6.D238.

    Maksimum kolumny mówi ILE, a zdanie §4 („rośnie z 57,64 km/h (Python, wiąże
    Beaulieu → Demey) do 58,68 km/h") mówi KTÓRY odcinek. Po zamianie kolumny między
    pakietami maksimum stoi, a te dwa końce się rozjeżdżają — i dopiero to jest
    usterką widoczną dla bramki.
    """
    zdanie = ZDANIE_WIAZACE.search(_read(SOURCE))
    assert zdanie, (
        "w §4 nie ma zdania nazywającego wiersz wiążący — bez niego ta bramka "
        "porównuje maksimum z niczym")

    granica = lower_bound_kmh()
    wiazace = [w for w in wiersze_pelne() if _na_liczbe(w[2]) == granica]
    assert len(wiazace) == 1, wiazace
    pakiet, py, cs, _delta, _op, odcinek_cs = wiazace[0]

    assert _na_liczbe(zdanie.group(3)) == granica, (
        "zdanie §4 mówi o %s km/h, a maksimum kolumny C# daje %.2f"
        % (zdanie.group(3), granica))
    assert _na_liczbe(zdanie.group(1)) == _na_liczbe(py), (
        "zdanie §4 podaje stronę pythonową %s km/h, a wiersz wiążący (%s) ma %s — "
        "kolumna C# stoi przy innym pakiecie niż proza"
        % (zdanie.group(1), pakiet, py))
    assert zdanie.group(2).strip() == odcinek_cs.strip(), (
        "zdanie \u00a74 wi\u0105\u017ce odcinek \u201e%s\u201d, a wiersz o maksimum "
        "%s km/h (%s) wskazuje \u201e%s\u201d \u2014 po zamianie kolumny mi\u0119dzy "
        "pakietami wygl\u0105da to dok\u0142adnie tak"
        % (zdanie.group(2).strip(), cs, pakiet, odcinek_cs.strip()))


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

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

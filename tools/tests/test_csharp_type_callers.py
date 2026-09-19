#!/usr/bin/env python3
"""Typy publiczne `src/Sim/` bez wołającego w `src/` — i granica skanu PO NAZWIE.

**Odpowiedź na pierwsze pytanie 6.D234: przypadków jest DWANAŚCIE, nie jeden.**
Pozycja znała `CbtcTestArea` i żądała, żeby policzyć, ilu typów dotyczy to samo,
bo „bramka postawiona na jednej nazwie jest zapadką na nazwie". Zmierzone
19.09.2026 na `323bff5`, maską literałów POŻYCZONĄ z `test_dead_constants_csharp.py`:
w `src/Sim/` stoi 109 typów publicznych. Osiemdziesiąt cztery z nich woła po nazwie kod
spod `src/`. Dwanaście jest wołanych po nazwie wyłącznie spod `tests/` i te stoją
w `TYLKO_TESTY`. Trzynaście nie pada po nazwie nigdzie poza własnym plikiem i te stoją
w `NIEWOLANE_PO_NAZWIE`. Pełna tabela z nazwami:
`reports/6d234-typy-wolane-wylacznie-z-testow.md`.

**GRANICA PRZYRZĄDU JEST TU WAŻNIEJSZA OD LICZBY i dlatego stoi przed nią.**
Skan po nazwie odpowiada na pytanie „czy typ jest NAZYWANY", a nie „czy jest
UŻYWANY". W C# `var` i dekonstrukcja pozwalają użyć typu, nie pisząc jego nazwy:

* `BrakingRunResult` nie pada poza własnym plikiem ANI RAZU — a jest typem zwracanym
  `BrakingRun.ToStop` i `ToSpeed`, przy czym `BrakingRun` jest wołany
  z `src/Sim.Runner/Program.cs`. Wołający pisze `var run = …ToStop(80.0)`.
* `RegistryEntry` tak samo: typ zwracany `VehicleRegistry.Get`, a `VehicleRegistry`
  jest wołany z `src/Sim/Physics/VehicleModel.cs` i dwóch innych miejsc w `src/`.

Dlatego zbiór `NIEWOLANE_PO_NAZWIE` nazywa się **po nazwie**, a nie „martwe":
trzynaście z trzynastu to typy zwracane albo `record struct` konsumowane przez `var`,
i **ani jednego z nich ta bramka nie zgłasza jako martwego**. Zgłaszanie ich byłoby
bramką z 6.D27 — zapalającą się na kodzie poprawnym.

**WZORZEC TYPU MA DWA SŁOWA RODZAJU i pierwsza wersja tego nie wiedziała.**
`public readonly record struct X` niesie rodzaj `record struct`; wzorzec biorący
`record` za rodzaj czytał `struct` jako NAZWĘ typu. Zmierzony koszt tej pomyłki:
**71 typów zamiast 109, 10 „tylko testy" zamiast 12 i 2 „nigdzie" zamiast 13** —
czyli trzydzieści osiem typów niewidocznych dla skanu. Znalazła to kolumna sąsiadów,
w której jako nazwa typu wołanego z `src/` pojawił się `struct`; pilnuje tego dziś
`test_wzorzec_czyta_record_struct_jako_JEDEN_rodzaj`.
"""

import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_dead_constants_csharp as CS  # noqa: E402
import tree_walk as TW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Deklaracja typu publicznego. Rodzaj bywa DWUSŁOWNY (`record struct`, `record class`)
#: i to jest jedyny powód, dla którego ta alternatywa ma sześć gałęzi, a nie cztery.
TYP = re.compile(
    r"^\s*public\s+(?:(?:sealed|static|abstract|partial|readonly|ref)\s+)*"
    r"(record\s+struct|record\s+class|record|class|struct|enum|interface)"
    r"\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)

#: Typy publiczne `src/Sim/`, których nazwa pada poza własnym plikiem WYŁĄCZNIE
#: w plikach spod `tests/`. Dwanaście, zmierzone 19.09.2026 na `323bff5`.
#:
#: **Rozstrzygnięcie jest WSPÓLNE dla wszystkich dwunastu i brzmi: ZOSTAJĄ.** Pole
#: „Wyjście" 6.D234 dopuszcza je wprost — „zostaje, bo niesie wiedzę o sieci, i jest
#: to zapisane". Powód jest ten sam w każdym przypadku i dlatego stoi raz: to są typy
#: opisujące SIEĆ i JEJ REGUŁY (obszary testowe CBTC, tryby ochrony, trasa linii,
#: pola JSON-a danych), a nie kod pomocniczy testów. Usunięcie ich byłoby usunięciem
#: DANYCH, nie kodu, a dane w tym projekcie mają źródło (`CLAUDE.md` §4.1).
#: Podłączenie któregokolwiek do gry jest decyzją projektową i pozycja wyklucza je
#: wprost (§8).
#:
#: **Czego ten zbiór NIE twierdzi:** że typ jest niepotrzebny. Twierdzi wyłącznie,
#: że dziś żaden plik `src/` nie wymienia go z nazwy — i to jest fakt sprawdzalny,
#: inaczej niż „jest martwy", którego ten skan rozstrzygnąć nie może.
TYLKO_TESTY = frozenset({
    "CbtcTestArea", "CbtcTestStage", "DriveSegment", "JsonFields", "KcvFunction",
    "LineRoute", "LineTrain", "ProtectionMode", "ProtectionModeRegistry",
    "ProtectionModeStatus", "ProtectionModeStatusParser", "RouteGap",
})

#: Typy publiczne `src/Sim/`, których nazwa nie pada poza własnym plikiem NIGDZIE.
#:
#: **To NIE jest lista typów martwych** i nazwa zbioru mówi dlaczego: „po nazwie".
#: Jedenaście z trzynastu to `record struct`, a dwa pozostałe (`BrakingRunResult`,
#: `RegistryEntry`) są typami zwracanymi składników, których typ deklarujący JEST
#: wołany z `src/`. Wołający piszą `var`, więc nazwa nie pada — a typ jest używany.
NIEWOLANE_PO_NAZWIE = frozenset({
    "BrakingPoint", "BrakingReferenceRow", "BrakingRunResult", "CbtcDynamicTestSite",
    "CbtcTestSpan", "DoorInterlock", "RegistryEntry", "RouteStation",
    "RunRestartValues", "ServiceBlock", "ServicePeak", "SignallingAssumption",
    "StationApproach",
})

#: Ile typów publicznych ma `src/Sim/`. PODŁOGA, nie równość: nowy typ ma podnosić tę
#: liczbę razem z przypisaniem, a nie zapalać bramkę samym istnieniem.
MIN_TYPOW_PUBLICZNYCH = 109


def _pliki_cs(root=ROOT):
    """Wszystkie `.cs` pod `src/` i `tests/`, ścieżkami względem korzenia.

    Przejście przez `tree_walk.znajdz`, a nie przez `os.walk`: `bin/` i `obj/` stoją
    w `.gitignore`, więc odsiewa je ten sam filtr, co wszędzie indziej (6.D74, 6.D117).
    Własna lista katalogów builda byłaby DRUGĄ kopią tamtej wiedzy.
    """
    out = {}
    for pod in ("src", "tests"):
        for sciezka in TW.znajdz(os.path.join(root, pod), "*.cs", root):
            with open(sciezka, encoding="utf-8", errors="ignore") as uchwyt:
                klucz = os.path.relpath(sciezka, root).replace(os.sep, "/")
                out[klucz] = uchwyt.read()
    return out


def typy_publiczne(zrodla=None, root=ROOT):
    """`{nazwa: (rodzaj, plik)}` dla typów publicznych zadeklarowanych w `src/Sim/`."""
    zrodla = _pliki_cs(root) if zrodla is None else zrodla
    typy = {}
    for plik, tresc in sorted(zrodla.items()):
        if not plik.startswith("src/Sim/"):
            continue
        for rodzaj, nazwa in TYP.findall(tresc):
            typy.setdefault(nazwa, (rodzaj, plik))
    return typy


def rozklad_wolajacych(zrodla=None, root=ROOT):
    """`(wolane_z_src, tylko_testy, niewolane)` — trzy zbiory nazw.

    Maska literałów i komentarzy POŻYCZONA z `test_dead_constants_csharp.py`.
    Bez niej wzmianka w komentarzu liczyłaby się jako wołanie, a wtedy zbiór
    „tylko testy" mówiłby o prozie, nie o kodzie.
    """
    zrodla = _pliki_cs(root) if zrodla is None else zrodla
    maski = {p: CS.maska_z_dziurami(t) for p, t in zrodla.items()}
    z_src, tylko_testy, niewolane = set(), set(), set()
    for nazwa, (_rodzaj, wlasny) in typy_publiczne(zrodla, root).items():
        slowo = re.compile(r"\b%s\b" % re.escape(nazwa))
        gdzie = [p for p, m in maski.items() if p != wlasny and slowo.search(m)]
        if any(p.startswith("src/") for p in gdzie):
            z_src.add(nazwa)
        elif gdzie:
            tylko_testy.add(nazwa)
        else:
            niewolane.add(nazwa)
    return z_src, tylko_testy, niewolane


def test_przyrzad_widzi_typy_ktore_ma_widziec():
    """Bramka zielona na zerze trafień nic nie mierzy."""
    typy = typy_publiczne()
    assert len(typy) >= MIN_TYPOW_PUBLICZNYCH, (
        "typów publicznych w `src/Sim/` jest %d przy podłodze %d — skan przestał "
        "czytać drzewo albo rozbiór deklaracji się zawęził"
        % (len(typy), MIN_TYPOW_PUBLICZNYCH))


def test_wzorzec_czyta_record_struct_jako_JEDEN_rodzaj():
    """Kontrola przyrządu na PIERWSZĄ pomyłkę tej pozycji — 6.D234.

    `public readonly record struct X` ma rodzaj DWUSŁOWNY. Wzorzec biorący `record`
    za rodzaj czyta `struct` jako nazwę typu i gubi wszystkie takie deklaracje;
    zmierzony koszt: 71 typów zamiast 109.
    """
    probka = "\n".join((
        "public readonly record struct Kilometraz(double Metry);",
        "public record struct Peron(int Numer);",
        "public sealed record Tryb(string Nazwa);",
        "public sealed class Zwykla { }",
        "public enum Stan { A, B }",
    ))
    znalezione = dict((n, r) for r, n in TYP.findall(probka))
    assert znalezione == {
        "Kilometraz": "record struct",
        "Peron": "record struct",
        "Tryb": "record",
        "Zwykla": "class",
        "Stan": "enum",
    }, ("wzorzec przeczytał %s — `record struct` musi wyjść jako JEDEN rodzaj, "
        "inaczej nazwą typu robi się słowo `struct`" % znalezione)
    assert "struct" not in znalezione, (
        "wzorzec uznał słowo `struct` za nazwę typu — to jest dokładnie ta pomyłka, "
        "która urywała skanowi jedną trzecią typów drzewa; liczby w docstringu")


def test_kazdy_typ_bez_wolajacego_w_src_STOI_W_JEDNYM_ZE_ZBIOROW():
    """Połowa pola „Skończone, gdy" 6.D234: każdy ma mieć zapisane rozstrzygnięcie."""
    _z_src, tylko_testy, niewolane = rozklad_wolajacych()
    # Komunikat NAZYWA KLASĘ, do której typ trafił, i to jest treść, nie ozdoba:
    # bez tego kontrola âtyp wołany tylko z `tests/`" i kontrola âtyp nie wołany
    # nigdzie" dają komunikat NIEODRÓŻNIALNY, a to są dwa różne rozstrzygnięcia
    # i dwa różne zbiory. Zmierzone przy KN-1 i KN-2 tej pozycji.
    nieprzypisane = (
        [(n, "tylko testy") for n in sorted(tylko_testy - TYLKO_TESTY)]
        + [(n, "niewołany po nazwie") for n in sorted(niewolane - NIEWOLANE_PO_NAZWIE)])
    assert not nieprzypisane, (
        "te typy publiczne `src/Sim/` nie mają wołającego w `src/`, a nie stoją "
        "w żadnym z dwóch zbiorów tej bramki: %s — dopisz je razem z powodem "
        "w tym samym commicie, w którym powstały" % nieprzypisane)


def test_zaden_zbior_nie_wymienia_typu_ktory_MA_juz_wolajacego():
    """Druga strona: wpis, który się zestarzał, ma paść głośno."""
    z_src, tylko_testy, niewolane = rozklad_wolajacych()
    zestarzale = sorted((TYLKO_TESTY | NIEWOLANE_PO_NAZWIE) & z_src)
    assert not zestarzale, (
        "te typy są dziś wołane z `src/`, a stoją na liście typów bez wołającego: %s "
        "— zdejmij wpis, bo powód zniknął" % zestarzale)
    znikniete = sorted((TYLKO_TESTY | NIEWOLANE_PO_NAZWIE)
                       - (tylko_testy | niewolane | z_src))
    assert not znikniete, (
        "te nazwy stoją w zbiorach, a w drzewie takich typów publicznych NIE MA: %s"
        % znikniete)


def test_zbiory_sa_rozlaczne():
    """Typ nie może być naraz `tylko testy` i `niewołany`."""
    obie = sorted(TYLKO_TESTY & NIEWOLANE_PO_NAZWIE)
    assert not obie, ("te typy stoją w obu zbiorach: %s" % obie)


def test_wzmianka_w_komentarzu_i_w_literale_NIE_jest_wolaniem():
    """Kontrola maski — bez niej zbiór `tylko testy` mówiłby o prozie, nie o kodzie."""
    zrodla = {
        "src/Sim/Probka.cs": "public sealed class Probka { }",
        "src/Game/Uzywa.cs": "// Probka jest opisana w dokumencie\nvar s = \"Probka\";",
        "tests/Sim.Tests/Test.cs": "var p = new Probka();",
    }
    z_src, tylko_testy, niewolane = rozklad_wolajacych(zrodla)
    assert tylko_testy == {"Probka"}, (
        "wzmianka w komentarzu albo w literale została policzona jako wołanie — "
        "wyszło z_src=%s, tylko_testy=%s, niewolane=%s" % (z_src, tylko_testy, niewolane))


def test_typ_bez_wolajacego_NIGDZIE_trafia_do_drugiego_zbioru():
    """Kontrola przyrządu: pozycja mówi, że dziś takiego typu nie widzi nic."""
    zrodla = {
        "src/Sim/Samotny.cs": "public sealed class Samotny { }",
        "src/Game/Uzywa.cs": "var x = 1;",
    }
    _z_src, tylko_testy, niewolane = rozklad_wolajacych(zrodla)
    assert niewolane == {"Samotny"} and not tylko_testy, (
        "typ bez ani jednego wołającego nie trafił do zbioru `niewołane`: "
        "tylko_testy=%s, niewolane=%s" % (tylko_testy, niewolane))


def test_typ_wolany_z_src_NIE_trafia_do_zadnego_zbioru():
    """Trzecia gałąź, bez której dwie wyżej nie mówią, czego NIE łapią."""
    zrodla = {
        "src/Sim/Uzywany.cs": "public sealed class Uzywany { }",
        "src/Game/Uzywa.cs": "var u = new Uzywany();",
        "tests/Sim.Tests/Test.cs": "var u = new Uzywany();",
    }
    z_src, tylko_testy, niewolane = rozklad_wolajacych(zrodla)
    assert z_src == {"Uzywany"} and not tylko_testy and not niewolane, (
        "typ wołany z `src/` trafił na listę: tylko_testy=%s, niewolane=%s"
        % (tylko_testy, niewolane))


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

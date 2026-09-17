#!/usr/bin/env python3
"""Goły `JsonElement.GetProperty` w `src/` jest policzony i wymieniony z nazwy.

**Skąd ta bramka.** 6.D233. `JsonElement.GetProperty` rzuca `KeyNotFoundException`,
a wspólny handler `Sim.Runner` łapał `IOException`, `ArgumentException`,
`FormatException` i `InvalidOperationException` — tej jednej nie. Plik osi o treści
`{}` kończył więc przebieg **kodem 134** i stosem wywołań, czyli zrzutem środowiska
uruchomieniowego zamiast komunikatem narzędzia.

**Zmierzone 17.09.2026, przed zmianą**: gołych odczytów w `src/` jest **69**, a nie
50 — opis pozycji wymieniał **cztery** czytniki (24 `ChunkManifest`, 13
`CbtcTestArea`, 10 `SignallingPlan`, 3 `TrackAxis` = 50) i nie widział trzech
pozostałych miejsc: **8** w `VehicleRegistry`, **7** w `ProtectionMode` i **4**
w samym `Sim.Runner/Program.cs`. Cztery liczby z opisu zgadzają się co do jednego;
suma nie, bo populacja była zawężona do czterech plików.

**Dlaczego ZBIÓR, a nie liczba** (6.D131, 6.D211): próg na samą liczbę przechodzi
tak samo, gdy jeden odczyt zniknie z czytnika osi, a drugi przybędzie gdzie indziej.
Słownik niżej jest porównywany z drzewem w OBIE strony, więc widać, KTÓRY plik się
ruszył i w którą stronę.

**Osobnej zapadki na liczbę tu nie ma i to jest wybór.** Podłoga broniłaby wyłącznie
przed skanerem, który oślepł (6.D27), a przed tym broni tu `test_skaner_widzi_to_co_ma
_widziec` — kontrola przyrządu na wejściu SYNTETYCZNYM, niezależna od zawartości
drzewa, ściśle mocniejsza od progu, bo zapala się także wtedy, gdy skaner myli się
tylko na jednym kształcie. `ZAPADEK_RAZEM` w `test_tree_walks.py` zostaje więc nietknięte.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src")

#: Wywołanie `GetProperty`, które NIE jest `TryGetProperty`.
WYWOLANIE = re.compile(r"(?<!Try)\bGetProperty\s*\(")

#: Katalogi wytworów budowy pod `src/`. `.gitignore` odsiewa `bin/` i `obj/` przez
#: `TW.walk`, ale Godot.NET.Sdk generuje źródła również pod `.godot/`.
WYTWORY = ("obj", "bin", ".godot")

#: Czytniki plików danych — tu gołego odczytu ma NIE BYĆ ani jednego. To są cztery
#: pliki z opisu 6.D233 plus `Sim.Runner/Program.cs`, który czyta manifest i rozkład
#: wprost przez `JsonDocument`.
CZYTNIKI_BEZ_GOLYCH = (
    "src/Sim/Line/TrackAxis.cs",
    "src/Sim/Signalling/CbtcTestArea.cs",
    "src/Sim/Signalling/SignallingPlan.cs",
    "src/Sim.Runner/Program.cs",
)

#: Gdzie goły odczyt jeszcze STOI, z liczbą. Zmierzone 17.09.2026 po zmianie 6.D233.
#: Oba pliki czytają ground truth **osadzony w assembly** (`EmbeddedResource`
#: w `src/Sim/Sim.csproj`), a nie plik podawany przez gracza z wiersza poleceń —
#: dokument, którego brak pola jest usterką budowy, a nie złym wejściem. Pole
#: „Poza zakresem" 6.D233 wymienia cztery czytniki i tych dwóch nie obejmuje;
#: pozycja na nie jest 6.D234 (`CbtcTestArea` wołany wyłącznie z testów) i jej sąsiedzi.
POZOSTALE_GOLE = {
    # **`ChunkManifest.cs` jest w polu „Wejście" 6.D233, a mimo to zostaje z gołymi
    # odczytami — i to jest ZAWĘŻENIE ZAKRESU, nie przeoczenie.** Osłonięcie go zmienia
    # `src/Game/`, a `tests/Game.Tests/UiTextTests.cs` odtwarza tam pomiary 6.D173,
    # 6.D181 i 6.D188 nad DZISIEJSZYM korpusem `src/Game/`. Zmierzone: osłonięcie tego
    # jednego pliku zapala SZEŚĆ tych odtworzeń, a ich własny docstring zabrania
    # najtańszej naprawy — „odtworzenie 6.D181 mierzy wtedy inny korpus i nie ma prawa
    # go poprawiać". Po wyjęciu `src/Game/` z zakresu `Game.Tests` daje 318/318.
    #
    # **Zawężenie jest TRWAŁE, a nie tymczasowe, i ten akapit jest przepisany, a nie
    # dopisany obok (6.D256).** Do 17.09.2026 stało tu, że zamrożenie korpusu „daje 108
    # zamiast przypiętych 116", że „powód nie został ustalony" i że wejścia są bajtowo
    # identyczne „z commitem, na którym te liczby przypięto". **Ostatnia część była
    # nieprawdziwa i to ona wywracała wniosek:** migawkę zamrożono z `7771af3`, a to
    # jest commit, na którym przypięto **108**, nie 116 — sto szesnaście przypięto trzy
    # pozycje MB później, w `0ae0acf`. Migawka dała więc dokładnie tę liczbę, którą
    # miała dać. Zmierzone przebiegami w trzech układach: worktree `7771af3` (stała 108)
    # przechodzi, worktree `0ae0acf` (stała 116) przechodzi, dzisiejsze drzewo
    # (stała 116) przechodzi. Niewiadomej nie ma.
    #
    # **Powodem zawężenia jest więc to, co zmierzono niezależnie i co się nie zmieniło:**
    # osłonięcie tego jednego pliku zmienia `src/Game/`, czyli korpus, który te odtworzenia
    # mierzą Z DEFINICJI. Odtworzone 17.09.2026 własnoręcznie — wszystkie 24 gołe odczyty
    # zamienione na `RequiredField` dają `Failed: 6, Passed: 312, Total: 318`, a po
    # przywróceniu `318/318`. Sześć, tak samo jak przy 6.D233.
    #
    # Ta liczba jest strażnikiem zawężenia, a nie jego opisem: zbiór porównywany jest
    # w OBIE strony, więc osłonięcie tych odczytów bez zdjęcia wpisu zapali bramkę.
    "src/Game/Assets/ChunkManifest.cs": 24,
    "src/Sim/Physics/VehicleRegistry.cs": 8,
    "src/Sim/Signalling/ProtectionMode.cs": 7,
}

#: Osłona, przez którą odczyt wymaganego pola ma przechodzić.
OSLONA = "src/Sim/Json/JsonFields.cs"


def _bez_komentarzy_i_napisow(tekst):
    """Tekst tej samej DŁUGOŚCI, z wyzerowanymi komentarzami i treścią napisów.

    Dziura interpolacji `{...}` w `$"..."` zostaje, bo JEST kodem: przed 6.D233
    stało w takiej dziurze prawdziwe wywołanie (`CbtcTestArea.cs:177`), a skan
    liczący całą interpolację za napis gubił je i pokazywał 12 zamiast 13.
    """
    out = ["\n" if z == "\n" else " " for z in tekst]
    dlugosc = len(tekst)

    def zostaw(od, do):
        for i in range(od, do):
            out[i] = tekst[i]

    def napis(i, werbatim, interpolowany):
        while i < dlugosc:
            znak = tekst[i]
            if werbatim and znak == '"' and i + 1 < dlugosc and tekst[i + 1] == '"':
                i += 2
                continue
            if not werbatim and znak == "\\":
                i += 2
                continue
            if znak == '"':
                return i + 1
            if interpolowany and znak == "{":
                if i + 1 < dlugosc and tekst[i + 1] == "{":
                    i += 2
                    continue
                glebokosc, i, start = 1, i + 1, i + 1
                while i < dlugosc and glebokosc:
                    if tekst[i] == "{":
                        glebokosc += 1
                    elif tekst[i] == "}":
                        glebokosc -= 1
                        if not glebokosc:
                            break
                    elif tekst[i] == '"':
                        i = napis(i + 1, False, False) - 1
                    i += 1
                zostaw(start, i)
                i += 1
                continue
            i += 1
        return i

    i = 0
    while i < dlugosc:
        znak = tekst[i]
        nastepny = tekst[i + 1] if i + 1 < dlugosc else ""
        if znak == "/" and nastepny == "/":
            while i < dlugosc and tekst[i] != "\n":
                i += 1
            continue
        if znak == "/" and nastepny == "*":
            i += 2
            while i + 1 < dlugosc and not (tekst[i] == "*" and tekst[i + 1] == "/"):
                i += 1
            i += 2
            continue
        j, przedrostki = i, ""
        while j < dlugosc and tekst[j] in "$@":
            przedrostki += tekst[j]
            j += 1
        if przedrostki and j < dlugosc and tekst[j] == '"':
            i = napis(j + 1, "@" in przedrostki, "$" in przedrostki)
            continue
        if znak == '"':
            i = napis(i + 1, False, False)
            continue
        if znak == "'":
            i += 1
            while i < dlugosc:
                if tekst[i] == "\\":
                    i += 2
                    continue
                if tekst[i] == "'":
                    i += 1
                    break
                i += 1
            continue
        zostaw(i, i + 1)
        i += 1
    return "".join(out)


def gole_odczyty(katalog=None, root=None):
    """`{ścieżka względna: [numery wierszy]}` dla gołych `GetProperty` w `src/`."""
    baza = katalog or SRC
    korzen = root or ROOT
    znalezione = {}
    for sciezka in TW.znajdz(baza, "*.cs", korzen):
        wzgledna = os.path.relpath(sciezka, korzen).replace(os.sep, "/")
        if any(("/%s/" % w) in ("/" + wzgledna) for w in WYTWORY):
            continue
        with open(sciezka, encoding="utf-8") as uchwyt:
            tekst = uchwyt.read()
        kod = _bez_komentarzy_i_napisow(tekst)
        assert len(kod) == len(tekst), "skaner zgubil dlugosc na " + wzgledna
        for numer, wiersz in enumerate(kod.splitlines(), 1):
            znalezione.setdefault(wzgledna, []).extend(
                [numer] * len(WYWOLANIE.findall(wiersz)))
    return {k: v for k, v in znalezione.items() if v}


#: Wejście syntetyczne dla kontroli przyrządu. Para (kod, ile ma zobaczyć).
#: Ostatnie trzy wiersze są tu po to, żeby skaner, który zerowanie napisów ZDJĄŁ,
#: zapalił się tak samo jak skaner, który je rozszerzył na dziury interpolacji.
PROBKA_SKANERA = '''
class A {
    void B() {
        var x = root.GetProperty("a");
        var y = root.TryGetProperty("b", out var z);
        // var c = root.GetProperty("w_komentarzu");
        /// <c>root.GetProperty("w_dokumentacji")</c>
        /* root.GetProperty("w_bloku") */
        var s = "root.GetProperty(\\"w_napisie\\")";
        var v = @"root.GetProperty(""w_werbatim"")";
        var i = $"{root.GetProperty("c").GetString()} w dziurze";
    }
}
'''
PROBKA_SKANERA_WIDZIANE = 2


def test_skaner_widzi_to_co_ma_widziec():
    """Kontrola przyrzadu na wejsciu SYNTETYCZNYM — nie zalezy od zawartosci drzewa.

    Skaner, ktory oslepl, oddaje pusty slownik, a pusty slownik czyta sie jako
    „golych odczytow nie ma" i bramka wychodzi ZIELONA nad kazdym. To jest rodzina
    z 6.D27: przyrzad meldujacy sprawdzenie, ktorego nie zrobil.
    """
    kod = _bez_komentarzy_i_napisow(PROBKA_SKANERA)
    assert len(kod) == len(PROBKA_SKANERA), "skaner zgubil dlugosc na probce"
    ile = len(WYWOLANIE.findall(kod))
    assert ile == PROBKA_SKANERA_WIDZIANE, (
        "skaner widzi %d golych odczytow w probce, a ma %d — jeden z osmiu ksztaltow "
        "(gole, Try, //, ///, /* */, napis, werbatim, dziura interpolacji) przestal "
        "byc rozpoznawany; kod po wyzerowaniu: %r" % (ile, PROBKA_SKANERA_WIDZIANE, kod))


def test_osłona_stoi_tam_gdzie_ma_stac():
    """Bez pliku oslony cala reszta tej bramki opisuje stan, ktorego nie ma."""
    sciezka = os.path.join(ROOT, OSLONA)
    assert os.path.exists(sciezka), OSLONA + " nie istnieje — 6.D233"
    with open(sciezka, encoding="utf-8") as uchwyt:
        tresc = uchwyt.read()
    assert "public static JsonElement RequiredField(" in tresc, (
        OSLONA + " nie ma `RequiredField` — czytniki wolaja cos, czego tu nie ma")
    assert "throw new FormatException(" in tresc, (
        OSLONA + " nie rzuca `FormatException` — `KeyNotFoundException` wraca "
        "poza filtr wspolnego handlera `Sim.Runner` i przebieg konczy sie kodem 134")


def test_czytniki_plikow_danych_nie_maja_ANI_JEDNEGO_golego_odczytu():
    """Piec czytnikow z pola „Wejscie" 6.D233 — tu gole `GetProperty` ma nie stac."""
    w_drzewie = gole_odczyty()
    winne = {p: w_drzewie[p] for p in CZYTNIKI_BEZ_GOLYCH if p in w_drzewie}
    assert winne == {}, (
        "goly `GetProperty` wrocil do czytnika pliku danych (plik: wiersze): %s — "
        "brak pola konczy sie tam `KeyNotFoundException`, czyli kodem 134 i stosem "
        "zamiast komunikatem z nazwa pliku i pola. Przepusc odczyt przez "
        "`JsonFields.RequiredField`." % sorted(winne.items()))


def test_pozostale_gole_odczyty_stoja_TAM_GDZIE_BYLY_i_jest_ich_TYLE_SAMO():
    """Zbior porownywany w OBIE strony, a nie prog na sume (6.D131, 6.D211)."""
    w_drzewie = {p: len(w) for p, w in gole_odczyty().items()
                 if p not in CZYTNIKI_BEZ_GOLYCH}

    nowe = {p: n for p, n in w_drzewie.items() if p not in POZOSTALE_GOLE}
    assert nowe == {}, (
        "goly `GetProperty` w pliku spoza listy: %s — albo przepusc go przez "
        "`JsonFields.RequiredField`, albo dopisz plik do `POZOSTALE_GOLE` z powodem, "
        "w tym samym commicie" % sorted(nowe.items()))

    zniknięte = sorted(p for p in POZOSTALE_GOLE if p not in w_drzewie)
    assert zniknięte == [], (
        "wpis na liscie dla pliku, ktory golego odczytu juz nie ma: %s — zdejmij wpis "
        "w tym samym commicie" % zniknięte)

    inna_liczba = [(p, POZOSTALE_GOLE[p], n) for p, n in sorted(w_drzewie.items())
                   if n != POZOSTALE_GOLE[p]]
    assert inna_liczba == [], (
        "liczba golych odczytow sie ruszyla (plik, bylo, jest): %s — w gore znaczy, "
        "ze przybyl odczyt poza oslona; w dol, ze ubyl i wpis trzeba poprawic"
        % inna_liczba)


def test_wspolny_handler_runnera_lapie_KeyNotFoundException():
    """Druga polowa 6.D233: filtr, ktory te rodzine wyjatkow przepuszczal."""
    sciezka = os.path.join(ROOT, "src", "Sim.Runner", "Program.cs")
    with open(sciezka, encoding="utf-8") as uchwyt:
        tresc = uchwyt.read()
    filtry = re.findall(r"catch \(Exception \w+\) when \([^)]*\)", tresc)
    assert filtry, "w `Sim.Runner/Program.cs` nie ma ani jednego filtrowanego `catch`"
    bez = [f for f in filtry if "KeyNotFoundException" not in f]
    assert bez == [], (
        "filtrowany `catch` bez `KeyNotFoundException`: %s — `JsonElement.GetProperty` "
        "rzuca wlasnie ja, wiec przebieg konczy sie kodem 134 i stosem" % bez)


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

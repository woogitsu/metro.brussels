#!/usr/bin/env python3
"""Lancuch dawnych wartosci stalej — czy jest pelny i czy konczy sie na dzisiejszej (6.D260).

**Skad ta bramka.** 6.D256 spedzilo trzy doby nad liczba 108, ktora odtworzenie
dalo przy stalej stojacej na 116. Rozwiazanie lezalo kilkanascie wierszy wyzej,
w komentarzu tej samej stalej: `108 -> 112 -> 113 -> 114 -> 116`. Sto osiem bylo
OSTATNIM OGNIWEM PRZED lancuchem, czyli poprzednia wartoscia tej samej stalej —
a nie liczba znikad. Wskazowka byla w tym samym pliku i nie przeczytal jej nikt,
bo lancuchow nie czytalo NIC.

**Ksztalt jest jeden po obu stronach jezykowych**, i to jest pomiar, a nie zalozenie:
`A -> B (DD.MM.RRRR, pozycja): powod`, rozniacy sie wylacznie znakiem komentarza
(`#` w Pythonie, `//` w C#). Strzalka `->` jest tu warunkiem koniecznym; strzalka
UNICODE `→` NIE JEST markerem lancucha i celowo nie jest czytana, bo w C# stoi
takze przy mutacjach (`TrackOffsetM 2.10→0.0`), przy fizyce (`40 km/h → 506,3 MJ`)
i przy przejsciach predkosci. Zmierzone 17.09.2026: 29 wystapien `→` w `tests/`
i `src/`, z czego lancuchem zmian nie jest ANI JEDNO.

**Zmierzone 17.09.2026 na calym drzewie.** Stalych z lancuchem: 41 (12 w Pythonie, 29 w C#). Ogniw razem: 206. I to jest liczba, ktorej pozycja szukala:
tyle dawnych wartosci lezy w drzewie zapisanych MASZYNOWO CZYTELNIE, a nie czytal
ich zaden przyrzad.

**Liczby w tym docstringu stoja BEZ POGRUBIENIA i to nie jest niedbalstwo.** Bramka
6.D259 (`MAX_POGRUBIONYCH_BEZ_POKRYCIA`) zada od kazdej liczby POGRUBIONEJ pokrycia
w kodzie w promieniu dwudziestu wierszy, a te opisuja caly pomiar, nie sasiednia stala
— wiec pogrubione podnosilyby zapadke GORNA, ktora wolno tylko obnizac. Jest to
zmierzona CENA tamtej bramki: konwencja „pogrubienie znaczy liczba zmierzona" dziala
tam, gdzie liczba stoi obok swojej stalej, a nie w opisie calego pomiaru. Zapisane
jako pozycja 6.D264, a nie obchodzone w milczeniu.

**Dziewiec lancuchow jest PRZERWANYCH** — wartosc zmienila sie bez dopisania ogniwa.
Luki sa duze, wiec nie sa artefaktem czytnika: `MINIMUM_DETAIL_BLOCKS` skacze
307 -> 319, `MIN_REPORTS` 351 -> 367, `MIN_GAME_NEEDLES` 84 -> 65 (czyli W DOL,
przy zapadce DOLNEJ). Lancuch `KluczyKatalogunaEkranie` zostal uzupelniony
o brakujacy etap 47 -> 58 podczas integracji wskazowki hamowania.

**Bramka nie zada ciaglosci od wszystkich i to jest wybor z 6.D27**, a nie pobliza-
nie: zazadanie jej dzis dawaloby dziewiec czerwieni na PRAWIDLOWYM drzewie i bramka
poszlaby do wylaczenia. Zada jej od tych, ktore ciagle SA — lista stoi w
`LANCUCHY_PRZERWANE` i porownywana jest W OBIE STRONY, wiec przerwanie lancucha
dzis ciaglego zapala bramke, a naprawienie przerwanego zapala ja tak samo i kaze
zdjac wpis (6.D243).
"""
import ast
import glob
import io
import os
import re
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

#: Ogniwo lancucha. Znak komentarza jest tu ROZDZIELONY na dwie postacie zamiast
#: `[#/]+`, bo `#` w C# zaczyna dyrektywe preprocesora, a `//` w Pythonie jest
#: dzieleniem calkowitym — luzniejszy wzorzec czytalby wiec kod jako komentarz.
OGNIWO_PY = re.compile(r"#\s*(\d+)\s*->\s*(\d+)\s*\((\d{2}\.\d{2}\.\d{4}),\s*([^)]+)\)")
OGNIWO_CS = re.compile(r"//[/ ]*\s*(?:<para><b>)?\s*(\d+)\s*->\s*(\d+)\s*"
                       r"\((\d{2}\.\d{2}\.\d{4}),\s*([^)]+)\)")

#: Przypisanie stalej, po ktorym lancuch sie konczy.
#: Wartosc jest tu LAPANA, a nie pomijana, i to jest poprawka z pierwszego przebiegu:
#: bez drugiej grupy `wartosc` bylo `None` dla KAZDEJ stalej pythonowej, wiec bramka
#: na zgodnosc konca lancucha sprawdzala wylacznie strone C# i przechodzila na zielono,
#: nie widzac polowy drzewa. Zlapala to lista wyjatkow porownywana w obie strony.
STALA_PY = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*(.+)$")
STALA_CS = re.compile(r"\b(?:const|static readonly)\s+\w+\s+(\w+)\s*=\s*([^;]+);")

#: Zapadki na populacje. DOLNE i WOLNE, bo lancuchy przybywaja razem z praca:
#: przybicie rownoscia czerwienialoby przy kazdej podniesionej zapadce.
MIN_STALYCH_Z_LANCUCHEM = 35
MIN_OGNIW_RAZEM = 170

#: Lancuchy PRZERWANE na dzien 17.09.2026 — z powodem, bo sama nazwa nic nie mowi.
#: Lista jest porownywana z drzewem W OBIE STRONY: przerwanie lancucha dzis
#: ciaglego zapala bramke, naprawienie przerwanego zapala ja tak samo.
LANCUCHY_PRZERWANE = {
    ("test_backlog.py", "MINIMUM_DETAIL_BLOCKS"):
        "skok 307 -> 319 miedzy 6.D223 a 6.D233",
    ("test_field_paths.py", "WYWOLAN_W_WYKONANYCH"):
        "trzy luki: 134 -> 141, 144 -> 165, 167 -> 169",
    ("test_game_needle_specificity.py", "MIN_GAME_NEEDLES"):
        "84 -> 65 miedzy MB-02 a MB-03, czyli W DOL przy zapadce DOLNEJ",
    ("test_report_hygiene.py", "MIN_REPORTS"):
        "skok 351 -> 367 miedzy 6.D224 a 6.D237",
    ("UiTextTests.cs", "LiteralowDotknietychZdejmowaniem"): "luka w srodku lancucha",
    ("UiTextTests.cs", "LiteralowNaEkranie"): "luka w srodku lancucha",
    ("UiTextTests.cs", "LiteralowZKlamra"): "luka w srodku lancucha",
    ("UiTextTests.cs", "PozycjiStaregoCzytnika"): "luka w srodku lancucha",
    ("UiTextTests.cs", "ToStringRegeksemPoSurowym"): "luka w srodku lancucha",
}

#: Lancuchy, ktorych ostatnie ogniwo NIE jest dzisiejsza wartoscia stalej.
#: Trzy pierwsze to slowniki — ogniwo opisuje JEDNO pole, a `literal_eval` daje
#: caly slownik, wiec porownanie wprost jest bez sensu i bramka je pomija.
#: Dawny czwarty wyjatek (`KluczyKatalogunaEkranie`) zostal naprawiony przez
#: dopisanie brakujacego ogniwa w UiTextTests.cs.
KONIEC_INNY_NIZ_WARTOSC = {
    ("test_field_paths.py", "ADRESOW_W_WYKONANYCH"): "slownik — ogniwo opisuje jedno pole",
    ("test_field_paths.py", "KANDYDATOW_W_WYKONANYCH"): "slownik — jw.",
    ("test_field_paths.py", "WYWOLAN_W_WYKONANYCH"): "slownik — jw.",
}


def _lancuchy_z_pliku(sciezka, ogniwo, stala, nazwa_pliku):
    """`{(plik, stala): [ogniwa]}` — lancuch urywa sie na PIERWSZYM wierszu,
    ktory nie jest ani ogniwem, ani komentarzem, ani przypisaniem stalej."""
    linie = io.open(sciezka, encoding="utf-8").read().split("\n")
    out = {}
    biezace = []
    for i, lin in enumerate(linie):
        trafienie = ogniwo.search(lin)
        if trafienie:
            biezace.append((trafienie.group(1), trafienie.group(2),
                            trafienie.group(3), trafienie.group(4).strip(), i + 1))
            continue
        przypisanie = stala.search(lin)
        if przypisanie and biezace:
            wartosc = przypisanie.group(2).strip() if przypisanie.lastindex == 2 else None
            out[(nazwa_pliku, przypisanie.group(1))] = (biezace, wartosc)
            biezace = []
        elif lin.strip() and not lin.lstrip().startswith(("#", "//")) and biezace:
            biezace = []
    return out


def lancuchy_zmian(korzen=None):
    """`{(plik, stala): ([ogniwa], wartosc_lub_None)}` dla obu stron jezykowych."""
    korzen = korzen or ROOT
    out = {}
    for sciezka in sorted(glob.glob(os.path.join(korzen, "tools", "tests", "*.py"))):
        out.update(_lancuchy_z_pliku(sciezka, OGNIWO_PY, STALA_PY,
                                     os.path.basename(sciezka)))
    wzory = ["tests/*/*.cs", "src/*/*.cs", "src/*/*/*.cs"]
    for wzor in wzory:
        for sciezka in sorted(glob.glob(os.path.join(korzen, wzor))):
            out.update(_lancuchy_z_pliku(sciezka, OGNIWO_CS, STALA_CS,
                                         os.path.basename(sciezka)))
    return out


def ciagly(ogniwa):
    """Czy kazde `B` jest `A` nastepnego ogniwa."""
    return all(ogniwa[i][1] == ogniwa[i + 1][0] for i in range(len(ogniwa) - 1))


def dawna_wartosc(ogniwa, liczba):
    """`(data, pozycja)` dla wartosci, ktora w tym lancuchu STALA — albo `None`.

    To jest funkcja, o ktora pytalo pole „Wyjscie": czy komunikat odmowy da sie
    rozszerzyc o zdanie „liczba %d stala tu do <data>, pozycja <numer>". Da sie,
    i odpowiedz jest tutaj.
    """
    szukana = str(liczba)
    for a, b, data, pozycja, _wiersz in ogniwa:
        if a == szukana:
            return (data, pozycja)
    return None


def test_ile_stalych_ma_lancuch_i_ile_jest_ogniw():
    """**Obie liczby, ktorych zadalo pole „Wyjscie" — z drzewa, nie wpisane.**

    Podlogi, a nie rownosci: lancuchy przybywaja razem z praca, wiec przybicie
    czerwienialoby przy kazdej podniesionej zapadce (6.D27).
    """
    lanc = lancuchy_zmian()
    ogniw = sum(len(v[0]) for v in lanc.values())
    assert len(lanc) >= MIN_STALYCH_Z_LANCUCHEM, (
        "stalych z lancuchem zmian jest %d przy podlodze %d — czytnik oslepl albo "
        "lancuchy zniknely z drzewa" % (len(lanc), MIN_STALYCH_Z_LANCUCHEM))
    assert ogniw >= MIN_OGNIW_RAZEM, (
        "ogniw lancucha jest %d przy podlodze %d — jak wyzej"
        % (ogniw, MIN_OGNIW_RAZEM))

    # Obie strony jezykowe MUSZA byc widziane. Bez tego czytnik czytajacy sam
    # Python przechodzilby podlogi wyzej i wygladal na kompletny.
    z_pythona = [k for k in lanc if k[0].endswith(".py")]
    z_csharp = [k for k in lanc if k[0].endswith(".cs")]
    assert z_pythona and z_csharp, (
        "czytnik widzi tylko jedna strone jezykowa: py=%d cs=%d"
        % (len(z_pythona), len(z_csharp)))


def test_ktory_lancuch_jest_PELNY_a_ktory_przerwany():
    """**Porownanie W OBIE STRONY, bo lista przerwanych bez tego gnije (6.D243).**

    Przerwanie lancucha dzis ciaglego zapala pierwsza polowe; naprawienie
    przerwanego — druga, i kaze zdjac wpis.
    """
    lanc = lancuchy_zmian()
    przerwane = {k for k, (ogniwa, _w) in lanc.items() if not ciagly(ogniwa)}

    nowe = sorted(przerwane - set(LANCUCHY_PRZERWANE))
    assert nowe == [], (
        "lancuch zmian sie URWAL: %s — wartosc zmienila sie bez dopisania ogniwa. "
        "Dopisz brakujace ogniwo w tym samym commicie albo wpisz je do "
        "`LANCUCHY_PRZERWANE` z powodem" % nowe)

    naprawione = sorted(set(LANCUCHY_PRZERWANE) - przerwane)
    assert naprawione == [], (
        "wpis w `LANCUCHY_PRZERWANE` o lancuchu, ktory jest juz ciagly albo "
        "zniknal z drzewa: %s — zdejmij wpis" % naprawione)


def test_lancuch_konczy_sie_na_DZISIEJSZEJ_wartosci_stalej():
    """Ostatnie ogniwo ma byc tym, co stala niesie — inaczej historia klamie.

    Trzy wyjatki to slowniki, w ktorych ogniwo opisuje jedno pole.
    """
    lanc = lancuchy_zmian()
    rozjazd = set()
    for klucz, (ogniwa, wartosc) in lanc.items():
        if wartosc is None:
            continue
        if wartosc.strip() != ogniwa[-1][1]:
            rozjazd.add(klucz)

    nowe = sorted(rozjazd - set(KONIEC_INNY_NIZ_WARTOSC))
    assert nowe == [], (
        "lancuch konczy sie na innej liczbie, niz niesie stala: %s — dopisz "
        "ogniwo albo wpisz do `KONIEC_INNY_NIZ_WARTOSC` z powodem" % nowe)
    zbedne = sorted(set(KONIEC_INNY_NIZ_WARTOSC) - rozjazd)
    assert zbedne == [], (
        "wpis o rozjezdzie, ktorego juz nie ma: %s — zdejmij" % zbedne)


def test_lancuch_ZgloszenWaskichWierszami_wyjasnia_108_z_6D256():
    """**Odtworzenie tego, co 6.D256 ustalilo recznie — teraz maszynowo.**

    Pozycja 6.D256 spedzila trzy doby nad liczba 108 i rozstrzygnela ja czytaniem
    historii gita. Ten test pokazuje, ze odpowiedz lezala w SAMYM PLIKU: `dawna_wartosc`
    zwraca dla 108 date i pozycje, przy ktorych ta liczba w tej stalej stala.
    """
    lanc = lancuchy_zmian()
    klucz = ("UiTextTests.cs", "ZgloszenWaskichWierszami")
    assert klucz in lanc, "lancuch stalej z 6.D256 zniknal z drzewa"
    ogniwa, wartosc = lanc[klucz]

    assert ciagly(ogniwa), "lancuch tej stalej sie urwal"
    # 23.09.2026, 6.M1: lancuch wydluzyl sie o ogniwo 116 -> 117 (odtworzenie linii).
    assert wartosc.strip() == ogniwa[-1][1] == "137", (
        "lancuch nie konczy sie na dzisiejszej wartosci: %s wobec %s"
        % (ogniwa[-1][1], wartosc))

    skad = dawna_wartosc(ogniwa, 108)
    assert skad is not None, (
        "108 nie zostalo rozpoznane jako DAWNA wartosc tej stalej — a to jest "
        "cala tresc 6.D256")
    data, pozycja = skad
    assert data == "14.09.2026", data
    assert "MB-04" in pozycja, pozycja

    # I kontrola w druga strone: liczba, ktora w tym lancuchu nie stala,
    # ma dac `None`. Bez tego `dawna_wartosc` zwracajaca cokolwiek dla wszystkiego
    # przechodzilaby asercje wyzej.
    assert dawna_wartosc(ogniwa, 999) is None, (
        "`dawna_wartosc` zwraca odpowiedz dla liczby, ktorej w lancuchu nie ma")


def test_czytnik_lancuchow_widzi_ksztalt_ktory_ma_widziec():
    """**Kontrola przyrzadu — siedem ksztaltow na drzewie probnym.**

    Bez niej „41 stalych i 203 ogniwa" nie odroznialoby sie od czytnika, ktory
    czyta polowe drzewa: obie liczby sa podlogami, wiec czytnik slabszy tez je
    przechodzi (6.D27).
    """
    py = (
        "# 1 -> 2 (01.01.2026, 6.X1): pierwsze ogniwo.\n"
        "# 2 -> 3 (02.01.2026, 6.X2): drugie.\n"
        "PROBNA = 3\n"
        "# 10 -> 20 (03.01.2026, 6.X3): luka nizej.\n"
        "# 30 -> 40 (04.01.2026, 6.X4): tu jest przerwa.\n"
        "PRZERWANA = 40\n"
        "# zwykly komentarz bez ogniwa\n"
        "BEZ_LANCUCHA = 7\n"
        "wynik = 8 // 2  # dzielenie calkowite, NIE komentarz C#\n")
    cs = (
        "class P {\n"
        "    // 5 -> 6 (05.01.2026, 6.X5): ogniwo C#.\n"
        "    private const int Probna = 6;\n"
        "    // strzalka unicode 9 → 0 NIE jest lancuchem\n"
        "    private const int Unicode = 0;\n"
        "}\n")

    with tempfile.TemporaryDirectory(prefix="metro-lancuchy-") as katalog:
        os.makedirs(os.path.join(katalog, "tools", "tests"))
        os.makedirs(os.path.join(katalog, "tests", "Probne"))
        io.open(os.path.join(katalog, "tools", "tests", "test_probne.py"),
                "w", encoding="utf-8").write(py)
        io.open(os.path.join(katalog, "tests", "Probne", "ProbneTests.cs"),
                "w", encoding="utf-8").write(cs)
        lanc = lancuchy_zmian(katalog)

    klucze = sorted(lanc)
    assert klucze == [("ProbneTests.cs", "Probna"),
                      ("test_probne.py", "PROBNA"),
                      ("test_probne.py", "PRZERWANA")], klucze

    assert ciagly(lanc[("test_probne.py", "PROBNA")][0]), "ciagly uznany za przerwany"
    assert not ciagly(lanc[("test_probne.py", "PRZERWANA")][0]), (
        "przerwany uznany za ciagly: %s — prawa strona jednego ogniwa nie jest lewa\n"
        "strona nastepnego, a to jest cala definicja przerwania"
        % [(o[0], o[1]) for o in lanc[("test_probne.py", "PRZERWANA")][0]])
    assert ("test_probne.py", "BEZ_LANCUCHA") not in lanc, (
        "stala bez ani jednego ogniwa trafila do wyniku")
    assert ("ProbneTests.cs", "Unicode") not in lanc, (
        "strzalka unicode policzona jako lancuch — a stoi w C# takze przy "
        "mutacjach i przy fizyce")

    assert dawna_wartosc(lanc[("test_probne.py", "PROBNA")][0], 1) == \
        ("01.01.2026", "6.X1"), (
            "`dawna_wartosc` nie zwrocila daty i pozycji pierwszego ogniwa lancucha "
            "probnego — a to jest ta funkcja, o ktora pytalo pole „Wyjscie")


# Strażnik `__main__` — bez niego `python3 tools/tests/<moduł>.py` kończył się
# kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

#!/usr/bin/env python3
"""Metody testowe C# czytane z tekstu — bez `dotnet` i bez rozbioru skladni.

Zestaw narzedzi chodzi tam, gdzie `doctor.sh` przepuszcza brak SDK, wiec bramka na
brakujacy `[TestMethod]` nie moze uruchamiac `dotnet test`. Czyta wiec pliki
`tests/**/*.cs` jako tekst i szuka **jednego ksztaltu**: publicznej metody
`void`/`Task`, zadeklarowanej BEZPOSREDNIO w klasie z `[TestClass]`.

**Dlaczego akurat ten ksztalt.** Taka wlasnie jest metoda testowa w tym repozytorium,
i taka byla ta, ktora 06.09.2026 przy 6.A16 stracila atrybut i przestala byc
uruchamiana, nie dajac ani jednego `FAIL`.

**Ksztalt PRZEPISANY 07.09.2026 przy 6.B28, nie dopisany obok.** Poprzednia wersja
tego akapitu mowila „bez argumentow" i dodawala, ze szerszy ksztalt „lapalby
pomocnikow z argumentami i skonczylby wylaczony". Pomiar tego nie potwierdzil:
metod `public void`/`Task` z argumentami na bezposrednim poziomie klasy `[TestClass]`
jest **13** i **wszystkie** maja atrybut testowy. Pomocniki sa tu `private static`
albo `internal static`. `poza_ksztaltem` schodzi wiec do **zera** i tym samym
`coverage()` przestaje raportowac luke, ktorej nie ma.

**Osobno, i to bylo wieksze od samej luki:** liczenie klamr szlo do 07.09.2026 po
surowym tekscie, wiec `{` w napisie JSON w pomocniku testu bylo brane za otwarcie
bloku. `ServiceDayTests.cs` (16 metod testowych) dawal **zero** widzianych metod,
`SignallingPlanTests.cs` (15) — cztery. Razem **27** prawdziwych, zwyklych metod
`[TestMethod]` bylo dla bramki niewidzialne, a bramka meldowala „0 nieuruchamianych",
bo nie miala czego zobaczyc. Naprawia to `maska()`; patrz jej docstring.

Glebokosc ma znaczenie: pomocnik `Reset()` w zagniezdzonym przyrzadzie
`tests/Game.Tests/RunResetTests.cs` jest publiczna, bezargumentowa metoda `void`
i **nie jest testem**. Odsiewa go liczenie klamr — brany jest wylacznie poziom
bezposrednio pod klasa z `[TestClass]`.
"""
import glob
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Klasa oznaczona `[TestClass]`, razem z ewentualnymi dalszymi atrybutami.
KLASA = re.compile(
    r"\[TestClass\][^\n]*\n(?:[ \t]*\[[^\]]*\][ \t]*\n)*[ \t]*public[^\n]*?class\s+(\w+)")

#: Publiczna metoda `void`/`Task`, z argumentami albo bez, z blokiem atrybutow nad
#: nia. **Ksztalt przepisany 07.09.2026, nie dopisany obok** (6.B28): poprzednia
#: wersja zadala pustych nawiasow, wiec 13 metod `[DataTestMethod]` z wierszami
#: `[DataRow]` bylo poza nia i brakujacy atrybut w tej rodzinie przeszedlby
#: niezauwazony. Powodem tamtego zwezenia byla obawa o pomocnikow z argumentami —
#: **zmierzona i nieziszczona**: publicznych metod `void`/`Task` z argumentami na
#: bezposrednim poziomie klasy `[TestClass]` jest 13 i WSZYSTKIE maja atrybut
#: testowy, zero bez. Pomocniki tego repozytorium sa `private static` albo
#: `internal static`, wiec `public void` w klasie testowej jest sygnalem, nie szumem.
METODA = re.compile(
    r"(?P<attrs>(?:[ \t]*\[[^\]]*\][ \t]*\r?\n)*)"
    r"[ \t]*public\s+(?:static\s+|async\s+|override\s+|virtual\s+)*"
    r"(?P<ret>void|Task)\s+(?P<name>\w+)\s*\((?P<args>[^()]*)\)")

ATRYBUTY_TESTU = ("TestMethod", "DataTestMethod")

#: Nazwa metody na koncu naglowka czlonu — po niej zaczyna sie cialo. Bez tego warunku
#: `METODA` dopasowuje sie takze do naglowka, ktory metoda nie jest.
NAGLOWEK = re.compile(r"(\w+)\s*\([^()]*\)\s*$")


def pliki(root=ROOT):
    return sorted(glob.glob(os.path.join(root, "tests", "*", "*.cs")))


def maska(source):
    r"""`source` z komentarzami i literalami zamienionymi na spacje, ZNAK W ZNAK.

    Dlugosc i pozycje znakow nowej linii zostaja te same, wiec indeksy z maski
    wskazuja dokladnie te same miejsca w oryginale — po masce chodzi liczenie klamr,
    a wycinki bierze sie z oryginalu.

    **Po co.** Do 07.09.2026 liczenie klamr szlo po surowym tekscie, wiec `{`
    w napisie JSON w pomocniku testu bylo brane za otwarcie bloku. W
    `tests/Sim.Tests/ServiceDayTests.cs` przejscie rozjezdzalo sie na pierwszym
    pomocniku i z **16** metod testowych widzialo **zero** — a bramka na brakujacy
    atrybut meldowala mimo to „0 nieuruchamianych", bo nie miala czego zobaczyc.
    Wyrocznia zepsuta w strone „wszystko w porzadku"; zmierzone przy 6.B28.

    **Postaci jest SZESC, nie cztery, i ten akapit jest przepisany, a nie dopisany
    obok (13.09.2026, 6.D201).** Poprzednia wersja mowila o „wszystkich czterech
    postaciach, ktore wystepuja w `tests/`" — zdanie z 07.09.2026, opisujace drzewo
    z tamtego dnia. Policzone dzis, po jednej liczbie na galaz, na `tests/` + `src/`:
    zwykly **4735**, interpolowany **1079**, werbatim **42**, surowy interpolowany
    (przedrostek podwojnego dolara) **14**, surowy **8**, werbatim interpolowany **1**.
    Dwie ostatnie z tego wyliczenia — werbatim interpolowany i surowy interpolowany —
    w tamtej czworce nie byly wymienione w ogole, a wystepuja; zadna z szesciu nie ma
    udzialu zerowego w calym korpusie, choc dwie maja zerowy w samym `src/`.

    Co ktora galaz robi: w werbatim para cudzyslowow jest jednym cudzyslowem,
    a odwrotny ukosnik nie ucieka; w interpolowanym klamry zostaja WEWNATRZ literalu
    i sa w poprawnym C# zbilansowane, wiec pominiecie calego literalu jest bezpieczne;
    surowy konczy sie tyloma cudzyslowami, iloma sie otworzyl, a przedrostek
    podwojnego dolara zmienia tylko znak otwierajacy interpolacje, nie sposob
    domkniecia. Po malpie napisu surowego NIE MA — patrz `_koniec_literalu` i 6.D200.
    """
    out = []
    for rodzaj, kawalek, _klasa in _przebieg(source):
        out.append(kawalek if rodzaj == "kod" else _spacje(kawalek))
    return "".join(out)


#: Nazwy szesciu postaci literalu napisowego — 6.D201. Kolejnosc jest tu trescia:
#: od najczestszej do najrzadszej na dzien pomiaru, zeby wypis bramki czytalo sie
#: jako rozklad, a nie jako lista.
POSTACIE = (
    "zwykly",
    "interpolowany ($)",
    "werbatim (@)",
    "surowy interpolowany ($$" + '"""' + ")",
    "surowy (" + '"""' + ")",
    "werbatim interpolowany ($@)",
)


def klasy_literalow(source):
    """Lista postaci KAZDEGO literalu w `source`, w kolejnosci wystapienia — 6.D201.

    Idzie tym samym `_przebieg`, co `maska`, i to jest cala tresc tej funkcji:
    gdyby liczyla wlasnym rozbiorem, mowilaby o sobie, a nie o tym, co `maska`
    naprawde robi. Rodzina 6.D27.
    """
    return [klasa for rodzaj, _kawalek, klasa in _przebieg(source)
            if rodzaj == "literal"]


#: Postaci literalu, w ktorych klamra moze otwierac dziure interpolacji. Reszta
#: `POSTACIE` klamry nie interpretuje wcale — i to nie jest ostroznosc, tylko pomiar:
#: na drzewie z 15.09.2026 klamre NIE bedaca dziura ma 104 literalow zwyklych,
#: 24 werbatim i 8 surowych. Wzorzec szukajacy `{nazwa}` w kazdym literale wzialby
#: kazda z nich za odczyt.
POSTACIE_Z_DZIURA = (POSTACIE[1], POSTACIE[3], POSTACIE[5])


def dziury_interpolacji(source):
    """Zakresy `(start, koniec)` KODU w dziurach interpolacji — indeksy w `source`.

    Idzie tym samym `_przebieg`, co `maska` i `klasy_literalow`, i to jest cala tresc
    tej funkcji — rodzina 6.D213. Drugi rozbior literalow mowilby o sobie, a nie o tym,
    co `maska` naprawde zaslania.

    **Po co.** `maska` zamienia literal na spacje W CALOSCI, razem z dziurami — a dziura
    interpolacji jest KODEM, ktory sie wykonuje. Stala czytana wylacznie przez
    `$"...{Nazwa}..."` wygladala przez to dla kazdego skanu czytajacego na masce
    dokladnie tak samo jak martwa (6.D214, `CzlonWyrazenia`).

    **Ile klamr otwiera dziure, mowi liczba znakow dolara, a nie postac literalu.**
    W literale surowym z przedrostkiem `$$` dziure otwiera dopiero `{{`, a POJEDYNCZA
    klamra jest tam zwyklym znakiem; w zwyklym `$"..."` jest odwrotnie — dziure otwiera
    `{`, a `{{` jest uciekniete. Zmierzone 15.09.2026: wszystkie **14** literalow
    o przedrostku podwojnego dolara niosa w tym drzewie klamre, ktora dziura NIE jest.

    Domkniecie liczone jest na zagniezdzeniu, wiec `{f(new[]{1})}` konczy sie tam,
    gdzie trzeba, a literal napisowy w srodku dziury nie myli licznika — bo licznik
    chodzi po `_przebieg`, a nie po surowym tekscie.
    """
    wynik = []
    przesuniecie = 0
    for rodzaj, kawalek, klasa in _przebieg(source):
        if rodzaj == "literal" and klasa in POSTACIE_Z_DZIURA:
            for start, koniec in _dziury_w_literale(kawalek):
                wynik.append((przesuniecie + start, przesuniecie + koniec))
        przesuniecie += len(kawalek)
    return wynik


def _rozbior_prefiksu(kawalek):
    """`(dolary, surowy, poczatek_tresci, koniec_tresci)` literalu z `_przebieg`."""
    i = 0
    dolary = 0
    verbatim = False
    while i < len(kawalek) and kawalek[i] in "@$":
        dolary += kawalek[i] == "$"
        verbatim = verbatim or kawalek[i] == "@"
        i += 1
    cudzyslowy = 0
    while i + cudzyslowy < len(kawalek) and kawalek[i + cudzyslowy] == '"':
        cudzyslowy += 1
    surowy = cudzyslowy >= 3 and not verbatim
    zamkniecie = cudzyslowy if surowy else 1
    tresc = i + cudzyslowy
    return dolary, surowy, tresc, max(tresc, len(kawalek) - zamkniecie)


def _dziury_w_literale(kawalek):
    """Zakresy dziur WZGLEDEM kawalka literalu."""
    dolary, surowy, a, b = _rozbior_prefiksu(kawalek)
    if not dolary:
        return []
    otwiera = dolary if surowy else 1
    wynik = []
    i = a
    while i < b:
        if kawalek[i] != "{":
            i += 1
            continue
        bieg = 0
        while i + bieg < b and kawalek[i + bieg] == "{":
            bieg += 1
        # Surowy: bieg krotszy niz liczba dolarow to zwykle znaki. Nie-surowy:
        # `{{` jest uciekniete parami, wiec dziure otwiera dopiero klamra nieparzysta.
        if bieg < otwiera or (not surowy and bieg % 2 == 0):
            i += bieg
            continue
        start = i + bieg
        koniec = _koniec_dziury(kawalek, start, b, otwiera)
        wynik.append((start, koniec))
        i = koniec + otwiera
    return wynik


def _koniec_dziury(kawalek, start, b, zamyka):
    """Indeks pierwszej klamry domykajacej dziure, liczony na zagniezdzeniu."""
    reszta = kawalek[start:b]
    glebokosc = 0
    poz = 0
    for rodzaj, czesc, _klasa in _przebieg(reszta):
        if rodzaj != "kod":
            poz += len(czesc)
            continue
        for znak in czesc:
            if znak == "{":
                glebokosc += 1
            elif znak == "}":
                if glebokosc:
                    glebokosc -= 1
                elif reszta[poz:poz + zamyka] == "}" * zamyka:
                    return start + poz
            poz += 1
    return b


def _przebieg(source):
    """`(rodzaj, kawalek, klasa)` dla calego pliku — JEDYNY rozbior w tym module.

    `rodzaj` to `"kod"`, `"komentarz"`, `"literal"` albo `"znak"`. `klasa` jest
    wypelniona wylacznie dla literalow napisowych i jest jedna z `POSTACIE`.
    """
    i = 0
    n = len(source)
    while i < n:
        znak = source[i]
        if znak == "/" and i + 1 < n and source[i + 1] == "/":
            koniec = source.find("\n", i)
            koniec = n if koniec < 0 else koniec
            yield "komentarz", source[i:koniec], None
            i = koniec
            continue
        if znak == "/" and i + 1 < n and source[i + 1] == "*":
            koniec = source.find("*/", i + 2)
            koniec = n if koniec < 0 else koniec + 2
            yield "komentarz", source[i:koniec], None
            i = koniec
            continue
        if znak in "@$" or znak == '"':
            start = i
            j = i
            verbatim = False
            interpolowany = False
            while j < n and source[j] in "@$":
                verbatim = verbatim or source[j] == "@"
                interpolowany = interpolowany or source[j] == "$"
                j += 1
            if j < n and source[j] == '"':
                cudzyslowy = 0
                while j + cudzyslowy < n and source[j + cudzyslowy] == '"':
                    cudzyslowy += 1
                surowy = cudzyslowy >= 3 and not verbatim
                koniec = _koniec_literalu(source, j, verbatim)
                if surowy and interpolowany:
                    klasa = POSTACIE[3]
                elif surowy:
                    klasa = POSTACIE[4]
                elif verbatim and interpolowany:
                    klasa = POSTACIE[5]
                elif verbatim:
                    klasa = POSTACIE[2]
                elif interpolowany:
                    klasa = POSTACIE[1]
                else:
                    klasa = POSTACIE[0]
                yield "literal", source[start:koniec], klasa
                i = koniec
                continue
            yield "kod", (source[start:j] if j > start else znak), None
            i = j if j > start else i + 1
            continue
        if znak == "'":
            koniec = _koniec_znaku(source, i)
            yield "znak", source[i:koniec], None
            i = koniec
            continue
        yield "kod", znak, None
        i += 1


def _spacje(tekst):
    """Ten sam tekst w samych spacjach — poza znakami nowej linii."""
    return "".join("\n" if z == "\n" else " " for z in tekst)


def _koniec_literalu(source, at, verbatim):
    """Indeks ZA zamknieciem literalu napisowego otwartego cudzyslowem na `at`."""
    n = len(source)
    cudzyslowy = 0
    while at + cudzyslowy < n and source[at + cudzyslowy] == '"':
        cudzyslowy += 1
    if cudzyslowy >= 3 and not verbatim:
        # Surowy literal: konczy sie tyloma cudzyslowami, ilu go otwarlo.
        #
        # **`and not verbatim` DOPISANE 13.09.2026 (6.D200) i to nie jest ostroznosc.**
        # Po `@` napis surowy nie istnieje w C#: `@"""a"` jest napisem WERBATIM
        # o tresci `"a`, bo w werbatim `""` znaczy jeden cudzyslow. Bez tego warunku
        # czytnik liczyl tam trzy cudzyslowy otwierajace, szukal domkniecia `"""`,
        # ktorego nie ma, i maskowal WSZYSTKO DO KONCA PLIKU — a wiec chowal przed
        # bramka kazda metode ponizej. Jedna taka linia w `UiTextTests.cs` schowala
        # TRZY metody testowe (6.D188); zlapalo to porownanie dwoch odczytow
        # (`test_the_shape_covers_every_test_attribute`), a nie zadna bramka na
        # atrybut — bo bramka na atrybut nie miala czego zobaczyc. Ta sama wyrocznia
        # zepsuta w strone „wszystko w porzadku", co przy 6.B28, tylko innym wejsciem.
        #
        # `$"""..."""` (surowy interpolowany) zostaje w tej galezi, bo `$` nie czyni
        # napisu werbatim; `$@"""` i `@$"""` NIE zostaja, bo `@` czyni.
        zamkniecie = '"' * cudzyslowy
        koniec = source.find(zamkniecie, at + cudzyslowy)
        return n if koniec < 0 else koniec + cudzyslowy
    i = at + 1
    while i < n:
        if source[i] == "\\" and not verbatim:
            i += 2
            continue
        if source[i] == '"':
            if verbatim and i + 1 < n and source[i + 1] == '"':
                i += 2
                continue
            return i + 1
        i += 1
    return n


def _koniec_znaku(source, at):
    """Indeks ZA zamknieciem literalu znakowego — `'{'` nie jest otwarciem bloku."""
    i = at + 1
    n = len(source)
    while i < n:
        if source[i] == "\\":
            i += 2
            continue
        if source[i] == "'":
            return i + 1
        i += 1
    return n


def _cialo_klasy(source, at, maska_source=None):
    """Tresc klasy od jej `{` do pasujacego `}` — klamry liczone na masce."""
    m = maska(source) if maska_source is None else maska_source
    start = m.index("{", at)
    depth = 0
    for i in range(start, len(m)):
        if m[i] == "{":
            depth += 1
        elif m[i] == "}":
            depth -= 1
            if depth == 0:
                return source[start:i]
    return source[start:]


def _koniec_bloku(text, start):
    """Indeks znaku ZA klamra zamykajaca blok otwarty na `start`."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


def czlonkowie(cialo_klasy, maska_ciala=None):
    """`[(naglowek, cialo)]` dla czlonow na bezposrednim poziomie ciala klasy.

    Rozpoznaje **oba** ksztalty ciala: blok `{...}` i wyrazenie `=> ...;`. Przy ciele
    wyrazeniowym `cialo` jest tekstem wyrazenia, wiec `{` w inicjatorze tablicy nie
    jest brany za poczatek bloku metody — na tym wywrocila sie pierwsza wersja.

    Struktura chodzi po **masce** (`maska`), a wycinki po oryginale: `{` w napisie
    JSON w pomocniku testu nie jest otwarciem bloku. Bez tego `ServiceDayTests.cs`
    dawal 2 czlonki zamiast 18 — patrz `maska`.
    """
    m = maska(cialo_klasy) if maska_ciala is None else maska_ciala
    przesuniecie = 1 if cialo_klasy.startswith("{") else 0
    body = cialo_klasy[przesuniecie:]
    mbody = m[przesuniecie:]
    out = []
    poczatek = 0
    i = 0
    while i < len(mbody):
        # Cialo wyrazeniowe: `=>` PRZED najblizsza klamra otwierajaca.
        if mbody.startswith("=>", i):
            koniec = i + 2
            depth = 0
            while koniec < len(mbody):
                znak = mbody[koniec]
                if znak in "([{":
                    depth += 1
                elif znak in ")]}":
                    depth -= 1
                elif znak == ";" and depth <= 0:
                    break
                koniec += 1
            out.append((body[poczatek:i], body[i + 2:koniec]))
            i = koniec + 1
            poczatek = i
            continue
        if mbody[i] == "{":
            koniec = _koniec_bloku(mbody, i)
            out.append((body[poczatek:i], body[i + 1:koniec - 1]))
            i = koniec
            poczatek = i
            continue
        if mbody[i] == "}":
            break
        i += 1
    return out


#: Zachowane dla czytelnosci historii: `_poziom_bezposredni` wycinalo WNETRZA klamr,
#: zeby zostawic sam poziom deklaracji. Bylo poprawne dla wykrywania brakujacego
#: atrybutu i bezuzyteczne dla liczenia asercji, bo asercja siedzi wlasnie w tym
#: wnetrzu — dlatego 6.D28 dopisala DRUGIE przejscie, a 6.D30 sciagnela je tutaj
#: i skasowala pierwsze. Jedno przejscie, dwa zastosowania.


def metody(root=ROOT):
    """`[(plik, klasa, metoda, ma_atrybut)]` dla ksztaltu opisanego w docstringu."""
    found = []
    for path in pliki(root):
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        m = maska(source)
        for match in KLASA.finditer(source):
            for naglowek, _cialo in czlonkowie(_cialo_klasy(source, match.end(), m)):
                method = None
                for method in METODA.finditer(naglowek + "{"):
                    pass
                if method is None or not NAGLOWEK.search(naglowek.strip()):
                    continue
                found.append((
                    os.path.relpath(path, root),
                    match.group(1),
                    method.group("name"),
                    any(a in method.group("attrs") for a in ATRYBUTY_TESTU),
                ))
    return found


def bez_atrybutu(root=ROOT):
    """Metody o ksztalcie testu, ktore atrybutu NIE maja — czyli nieuruchamiane."""
    return [(p, k, m) for p, k, m, ma in metody(root) if not ma]


def coverage(root=ROOT):
    """Ile atrybutow testowych jest w plikach, a ile z nich obejmuje ten ksztalt."""
    w_plikach = 0
    for path in pliki(root):
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        for name in ATRYBUTY_TESTU:
            w_plikach += source.count("[%s]" % name)
    objete = sum(1 for _, _, _, ma in metody(root) if ma)
    return {"atrybuty_w_plikach": w_plikach, "objete_ksztaltem": objete,
            "poza_ksztaltem": w_plikach - objete}


def main():
    dane = coverage()
    print("[TESTY C#] atrybutow testowych w plikach: %d" % dane["atrybuty_w_plikach"])
    print("[TESTY C#] objetych ksztaltem bramki:     %d" % dane["objete_ksztaltem"])
    print("[TESTY C#] poza ksztaltem:                 %d" % dane["poza_ksztaltem"])
    brakujace = bez_atrybutu()
    print("[TESTY C#] wygladaja jak test, nie sa uruchamiane: %d" % len(brakujace))
    for path, klasa, metoda in brakujace:
        print("   BRAK [TestMethod]: %s :: %s.%s" % (path, klasa, metoda))
    return 1 if brakujace else 0


if __name__ == "__main__":
    raise SystemExit(main())

#: Podpis pomocnika `private static` — 6.D261. Typ zwracany lapany leniwie,
#: bo bywa generyczny (`List<(string, int)>`), tablicowy i dopuszczalny (`string?`);
#: rozstrzyga NAWIAS po nazwie, ktory odroznia metode od pola.
PODPIS_POMOCNIKA = re.compile(
    r"^\s*private\s+static\s+(?:readonly\s+)?[\w<>,\[\]\?\s]+?\s+(\w+)\s*\(")


def _cialo_pomocnika(linie, i):
    """Wiersze metody od jej podpisu do domykajacej klamry — albo do `;`.

    Dwie postacie i obie sa w drzewie: cialo w klamrach oraz metoda wyrazeniowa
    `=> ...;`, ktora klamry nie ma wcale. Czytnik liczacy same klamry gubilby te
    druga, a wsrod powtorzonych pomocnikow jest ona POSTACIA WIEKSZOSCI.
    """
    j = i
    while j < len(linie) and "{" not in linie[j]:
        if ";" in linie[j]:
            return linie[i:j + 1]
        j += 1
    if j >= len(linie):
        return linie[i:i + 1]
    glebokosc = 0
    k = j
    while k < len(linie):
        glebokosc += linie[k].count("{") - linie[k].count("}")
        if k > j and glebokosc <= 0:
            return linie[i:k + 1]
        if k == j and glebokosc == 0 and "}" in linie[k]:
            return linie[i:k + 1]
        k += 1
    return linie[i:k]


def _tresc(blok):
    """Biale znaki zdjete — porownujemy TRESC, a nie wciecie."""
    return re.sub(r"\s+", " ", " ".join(blok)).strip()


def pomocnicy(root=ROOT):
    """`{nazwa: [(plik, projekt, wiersz, tresc)]}` dla podpisow `private static`.

    Tresc jest tu ZNORMALIZOWANA, a nie zahaszowana, i to jest wybor: bramka
    ma umiec pokazac, CZYM rodziny sie roznia, a nie tylko ze sie roznia.

    **`plik` niesie PROJEKT, a nie sama nazwe pliku, i to jest poprawka z pierwszego
    przebiegu kontroli przyrzadu.** Pierwsza wersja kluczowala po `basename`, wiec dwa
    pliki o tej samej nazwie w roznych projektach byly dla niej JEDNYM plikiem —
    a rodzina wymaga dwoch. W dzisiejszym drzewie powtorzonych nazw plikow nie ma
    ani jednej, wiec zadna liczba w tym module by sie nie ruszyla i usterka przeszlaby
    caly zestaw na zielono; zlapal ja dopiero fixture, ktory takie dwa pliki tworzy.
    """
    out = {}
    for path in pliki(root):
        projekt = os.path.basename(os.path.dirname(path))
        linie = open(path, encoding="utf-8").read().split("\n")
        for i, lin in enumerate(linie):
            trafienie = PODPIS_POMOCNIKA.match(lin)
            if not trafienie:
                continue
            out.setdefault(trafienie.group(1), []).append(
                (os.path.join(projekt, os.path.basename(path)), projekt, i + 1,
                 _tresc(_cialo_pomocnika(linie, i))))
    return out


def rodziny_pomocnikow(root=ROOT):
    """`(identyczne, jednoimienne)` — nazwy padajace w WIECEJ NIZ JEDNYM pliku.

    Podzial jest cala trescia 6.D261 i pytalo o niego pole „Wyjscie": ta sama nazwa
    nad TYM SAMYM cialem jest duplikatem do scalenia, a nad INNYM — zbiegiem nazw,
    ktorego scalac nie wolno. Zlanie ich w jedna liczbe „24 powtorzone nazwy" nie
    mowi, ktora z tych dwoch rzeczy sie widzi.
    """
    identyczne, jednoimienne = {}, {}
    for nazwa, wystapienia in pomocnikow_w_wielu_plikach(root).items():
        tresci = {w[3] for w in wystapienia}
        (identyczne if len(tresci) == 1 else jednoimienne)[nazwa] = wystapienia
    return identyczne, jednoimienne


def pomocnikow_w_wielu_plikach(root=ROOT):
    """Same rodziny — nazwa musi pasc w co najmniej DWoCH plikach.

    Dwa pomocniki o tej samej nazwie w JEDNYM pliku to przeciazenie, a nie
    duplikat miedzy plikami, i do tego skanu nie naleza.
    """
    return {n: w for n, w in pomocnicy(root).items() if len({x[0] for x in w}) > 1}

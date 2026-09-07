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
    """`source` z komentarzami i literalami zamienionymi na spacje, ZNAK W ZNAK.

    Dlugosc i pozycje znakow nowej linii zostaja te same, wiec indeksy z maski
    wskazuja dokladnie te same miejsca w oryginale — po masce chodzi liczenie klamr,
    a wycinki bierze sie z oryginalu.

    **Po co.** Do 07.09.2026 liczenie klamr szlo po surowym tekscie, wiec `{`
    w napisie JSON w pomocniku testu bylo brane za otwarcie bloku. W
    `tests/Sim.Tests/ServiceDayTests.cs` przejscie rozjezdzalo sie na pierwszym
    pomocniku i z **16** metod testowych widzialo **zero** — a bramka na brakujacy
    atrybut meldowala mimo to „0 nieuruchamianych", bo nie miala czego zobaczyc.
    Wyrocznia zepsuta w strone „wszystko w porzadku"; zmierzone przy 6.B28.

    Obslugiwane sa wszystkie cztery postacie, ktore wystepuja w `tests/`: zwykly
    napis, `@"..."` (gdzie `""` jest cudzyslowem, a `\` nie ucieka), `$"..."`
    (klamry interpolacji zostaja WEWNATRZ literalu i sa w poprawnym C# zbilansowane,
    wiec pominiecie calego literalu jest bezpieczne) oraz surowy, otwierany trzema
    cudzyslowami.
    """
    out = []
    i = 0
    n = len(source)
    while i < n:
        znak = source[i]
        if znak == "/" and i + 1 < n and source[i + 1] == "/":
            koniec = source.find("\n", i)
            koniec = n if koniec < 0 else koniec
            out.append(_spacje(source[i:koniec]))
            i = koniec
            continue
        if znak == "/" and i + 1 < n and source[i + 1] == "*":
            koniec = source.find("*/", i + 2)
            koniec = n if koniec < 0 else koniec + 2
            out.append(_spacje(source[i:koniec]))
            i = koniec
            continue
        if znak in "@$" or znak == '"':
            start = i
            j = i
            verbatim = False
            while j < n and source[j] in "@$":
                verbatim = verbatim or source[j] == "@"
                j += 1
            if j < n and source[j] == '"':
                koniec = _koniec_literalu(source, j, verbatim)
                out.append(_spacje(source[start:koniec]))
                i = koniec
                continue
            out.append(source[start:j] if j > start else znak)
            i = j if j > start else i + 1
            continue
        if znak == "'":
            koniec = _koniec_znaku(source, i)
            out.append(_spacje(source[i:koniec]))
            i = koniec
            continue
        out.append(znak)
        i += 1
    return "".join(out)


def _spacje(tekst):
    """Ten sam tekst w samych spacjach — poza znakami nowej linii."""
    return "".join("\n" if z == "\n" else " " for z in tekst)


def _koniec_literalu(source, at, verbatim):
    """Indeks ZA zamknieciem literalu napisowego otwartego cudzyslowem na `at`."""
    n = len(source)
    cudzyslowy = 0
    while at + cudzyslowy < n and source[at + cudzyslowy] == '"':
        cudzyslowy += 1
    if cudzyslowy >= 3:
        # Surowy literal: konczy sie tyloma cudzyslowami, ilu go otwarlo.
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

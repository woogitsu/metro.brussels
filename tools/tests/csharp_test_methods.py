#!/usr/bin/env python3
"""Metody testowe C# czytane z tekstu — bez `dotnet` i bez rozbioru skladni.

Zestaw narzedzi chodzi tam, gdzie `doctor.sh` przepuszcza brak SDK, wiec bramka na
brakujacy `[TestMethod]` nie moze uruchamiac `dotnet test`. Czyta wiec pliki
`tests/**/*.cs` jako tekst i szuka **jednego, waskiego ksztaltu**: publicznej metody
`void`/`Task` bez argumentow, zadeklarowanej BEZPOSREDNIO w klasie z `[TestClass]`.

**Dlaczego akurat ten ksztalt.** Taka wlasnie jest metoda testowa w tym repozytorium,
i taka byla ta, ktora 06.09.2026 przy 6.A16 stracila atrybut i przestala byc
uruchamiana, nie dajac ani jednego `FAIL`. Ksztalt jest waski celowo: szerszy
(np. „kazda publiczna metoda") lapalby pomocnikow z argumentami i skonczylby
wylaczony, a bramka wylaczona nie jest bramka.

**Czego ten ksztalt NIE obejmuje, i to jest powiedziane, a nie ukryte.** Metod
z argumentami — czyli `[DataTestMethod]` z wierszami `[DataRow]`. Ich liczbe podaje
`coverage()`, zeby luka byla widoczna liczbowo, a nie tylko w komentarzu.

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

#: Publiczna metoda `void`/`Task` bez argumentow, z blokiem atrybutow nad nia.
METODA = re.compile(
    r"(?P<attrs>(?:[ \t]*\[[^\]]*\][ \t]*\r?\n)*)"
    r"[ \t]*public\s+(?:static\s+|async\s+|override\s+|virtual\s+)*"
    r"(?P<ret>void|Task)\s+(?P<name>\w+)\s*\(\s*\)")

ATRYBUTY_TESTU = ("TestMethod", "DataTestMethod")

#: Nazwa metody na koncu naglowka czlonu — po niej zaczyna sie cialo. Bez tego warunku
#: `METODA` dopasowuje sie takze do naglowka, ktory metoda nie jest.
NAGLOWEK = re.compile(r"(\w+)\s*\([^()]*\)\s*$")


def pliki(root=ROOT):
    return sorted(glob.glob(os.path.join(root, "tests", "*", "*.cs")))


def _cialo_klasy(source, at):
    """Tresc klasy od jej `{` do pasujacego `}` — po liczeniu klamr."""
    start = source.index("{", at)
    depth = 0
    for i in range(start, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
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


def czlonkowie(cialo_klasy):
    """`[(naglowek, cialo)]` dla czlonow na bezposrednim poziomie ciala klasy.

    Rozpoznaje **oba** ksztalty ciala: blok `{...}` i wyrazenie `=> ...;`. Przy ciele
    wyrazeniowym `cialo` jest tekstem wyrazenia, wiec `{` w inicjatorze tablicy nie
    jest brany za poczatek bloku metody — na tym wywrocila sie pierwsza wersja.
    """
    body = cialo_klasy[1:] if cialo_klasy.startswith("{") else cialo_klasy
    out = []
    buf = []
    i = 0
    while i < len(body):
        # Cialo wyrazeniowe: `=>` PRZED najblizsza klamra otwierajaca.
        if body.startswith("=>", i):
            koniec = i + 2
            depth = 0
            while koniec < len(body):
                znak = body[koniec]
                if znak in "([{":
                    depth += 1
                elif znak in ")]}":
                    depth -= 1
                elif znak == ";" and depth <= 0:
                    break
                koniec += 1
            out.append(("".join(buf), body[i + 2:koniec]))
            buf = []
            i = koniec + 1
            continue
        if body[i] == "{":
            koniec = _koniec_bloku(body, i)
            out.append(("".join(buf), body[i + 1:koniec - 1]))
            buf = []
            i = koniec
            continue
        if body[i] == "}":
            break
        buf.append(body[i])
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
        for match in KLASA.finditer(source):
            for naglowek, _cialo in czlonkowie(_cialo_klasy(source, match.end())):
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
    print("[TESTY C#] poza ksztaltem (z argumentami): %d" % dane["poza_ksztaltem"])
    brakujace = bez_atrybutu()
    print("[TESTY C#] wygladaja jak test, nie sa uruchamiane: %d" % len(brakujace))
    for path, klasa, metoda in brakujace:
        print("   BRAK [TestMethod]: %s :: %s.%s" % (path, klasa, metoda))
    return 1 if brakujace else 0


if __name__ == "__main__":
    raise SystemExit(main())

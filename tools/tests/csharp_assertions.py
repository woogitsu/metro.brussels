#!/usr/bin/env python3
"""Metody testowe C# i asercje obecne w ich tresci.

**Skad to narzedzie.** 6.D28. Zestaw Pythona ma `assertion_gate` od #139: test, ktory
przeszedl BEZ ani jednej asercji, jest tam awaria, nie sukcesem. Ta bramka zadzialala
07.09.2026 **dwa razy** — przy 6.D26, na moim wlasnym tescie, ktory po zawezeniu
zakresu skanowania przestal cokolwiek sprawdzac, i byla jedynym sladem, ze przestal.
Po stronie C# nie bylo nic: 2289 wywolan `Assert` w 124 plikach i zaden nadzor.

**Czego to narzedzie NIE mierzy, i to jest granica postawiona swiadomie.** Nie liczy
asercji WYKONANYCH, jak robi to `assertion_gate` przez instrumentacje AST. Liczy
asercje **obecne w tresci** metody, czyli to, co da sie przeczytac z tekstu. Test,
ktory ma asercje w galezi nigdy nie wchodzonej, przejdzie tu za asertujacy — to jest
slabsza wlasnosc niz po stronie Pythona i pole „Poza zakresem" pozycji 6.D28 mowi
o tym wprost.

**Cialo metody ma DWIE postacie i pierwsza wersja tego czytnika znala tylko jedna.**
Blok `{ ... }` oraz cialo wyrazeniowe `=> wyrazenie;`. Zmierzone: przy samych blokach
wychodzila **jedna** metoda „bez asercji" —
`Lista_funkcji_KCV_jest_dokladnie_ta_ktora_podaje_STIB` — ktora asertuje
`CollectionAssert.AreEqual` w ciele wyrazeniowym. Czytnik, ktory jednej z tych postaci
nie zna, nie zglasza braku asercji: zglasza **wlasna niewiedze** jako brak.

**Asercja to takze wywolanie pomocnika `Assert*`.** Zmierzone na tym drzewie: przy
samych wywolaniach `Assert.`/`StringAssert.`/`CollectionAssert.` wychodzilo **piec**
metod bez asercji, z czego cztery wolaja lokalny `AssertBits(...)`, ktory asertuje
w swoim ciele. Rozszerzenie na pomocnikow `Assert*` zbija to do jednej (tej z ciala
wyrazeniowego). Sprawdzone tez rozwiazywanie pomocnikow po CIELE, nie po nazwie —
i nie daje ani jednej metody wiecej, wiec zostaje regula prostsza.
"""
import glob
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csharp_test_methods as CTM  # noqa: E402

#: Wywolanie asercji MSTest wprost.
ASERCJA = re.compile(r"\b(?:Assert|StringAssert|CollectionAssert)\s*\.")
#: Wywolanie pomocnika, ktorego nazwa zaczyna sie od `Assert` — patrz docstring.
POMOCNIK = re.compile(r"\bAssert[A-Za-z0-9_]*\s*\(")
#: Nazwa metody na koncu naglowka czlonu — po niej zaczyna sie cialo.
NAGLOWEK = re.compile(r"(\w+)\s*\([^()]*\)\s*$")


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


def metody_testowe(root=ROOT):
    """`[(plik, klasa, metoda, ma_asercje)]` dla metod z atrybutem testowym."""
    found = []
    for path in CTM.pliki(root):
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        for klasa in CTM.KLASA.finditer(source):
            surowe = CTM._cialo_klasy(source, klasa.end())
            for naglowek, cialo in czlonkowie(surowe):
                match = None
                for match in CTM.METODA.finditer(naglowek + "{"):
                    pass
                if match is None:
                    continue
                if not NAGLOWEK.search(naglowek.strip()):
                    continue
                if not any(a in match.group("attrs") for a in CTM.ATRYBUTY_TESTU):
                    continue
                tresc = naglowek[match.end():] + cialo
                found.append((
                    os.path.relpath(path, root),
                    klasa.group(1),
                    match.group("name"),
                    bool(ASERCJA.search(tresc) or POMOCNIK.search(tresc)),
                ))
    return found


def bez_asercji(root=ROOT):
    return [(p, k, m) for p, k, m, ma in metody_testowe(root) if not ma]


def coverage(root=ROOT):
    dane = metody_testowe(root)
    return {"metody_testowe": len(dane),
            "z_asercja": sum(1 for *_x, ma in dane if ma),
            "bez_asercji": sum(1 for *_x, ma in dane if not ma)}


def main():
    dane = coverage()
    print("[ASERCJE C#] metod testowych:        %d" % dane["metody_testowe"])
    print("[ASERCJE C#] z asercja w tresci:     %d" % dane["z_asercja"])
    print("[ASERCJE C#] BEZ asercji w tresci:   %d" % dane["bez_asercji"])
    for plik, klasa, metoda in bez_asercji():
        print("BRAK ASERCJI: %s :: %s.%s" % (plik, klasa, metoda))
    return 1 if dane["bez_asercji"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

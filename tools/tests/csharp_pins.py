#!/usr/bin/env python3
"""Piny wpisane z ręki w testach C# — asercje, których oczekiwaną wartością jest literał.

**Skąd to narzędzie.** 6.D131. Pole „Skąd" pozycji zauważyło, że
`Wiersze_zlozone_z_katalogu_brzmia_co_do_znaku_tak_jak_przed_przenosinami` trzyma cały
wiersz pomocy jako napis wpisany z ręki — i że to jest JEDYNY powód, dla którego zmiana
nazwy klawisza cokolwiek zapala. Koszt takiego pinu rośnie liniowo z tabelą przypisań,
a rosnący koszt jest zwykle tym, co popycha do rozluźnienia pinu. Zanim to nastąpi,
warto wiedzieć, ile ich jest.

**Czytnik jest LEKSYKALNY, nie składniowy, i mówię to wprost.** Pole „Wyjście" pozycji
prosiło o liczbę „policzoną z drzewa składni". Drzewa składni C# w tym repozytorium nie
ma i mieć nie będzie: jedyną drogą byłby Roslyn, czyli nowa zależność — a tych projekt
nie dokłada (ta sama reguła, która w 6.D85 zabroniła walidatora JSON Schema). Zamiast
tego czytnik stoi na `csharp_test_methods.maska`, która zamienia komentarze i literały
na spacje ZNAK W ZNAK, więc `Assert.AreEqual` wewnątrz napisu albo komentarza nie jest
wywołaniem. To jest słabsza własność niż drzewo składni i jej granice są zmierzone:
czytnik nie wie, czy wywołanie stoi w metodzie testowej, czy w pomocniku, i nie rozwija
stałych (`Assert.AreEqual(OCZEKIWANY, x)` z `const string OCZEKIWANY` nie jest tu pinem,
choć nim jest).

**Sklejanie literałów jest konieczne, nie ozdobne.** Trzy z czterech pinów kategorii A
są zapisane jako `"…" + "…"` łamane przez kilka wierszy; czytnik biorący sam pierwszy
człon podawałby ich długość jako ułamek prawdziwej.
"""
import glob
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csharp_test_methods as CTM  # noqa: E402

#: Asercje, w których PIERWSZY argument jest wartością oczekiwaną. `Assert.IsTrue`
#: i `Assert.IsNotNull` pinem nie są: nie niosą oczekiwanej wartości, tylko warunek.
#:
#: **Wykluczenie `Assert.IsTrue` jest DEFINICYJNE, nie zmierzone — i mówię to wprost.**
#: KN-6 dopisała je do wzorca i zestaw przeszedł 5/5: `IsTrue` bierze `bool`, więc
#: literału napisowego jako pierwszego argumentu nie ma w drzewie ani jednego i mieć
#: nie może. Kontrola negatywna nie odróżni tu wzorca z `IsTrue` od wzorca bez niego
#: i żadna nie odróżni — różnica jest w typie, nie w danych.
ASERCJA = re.compile(
    r"\b(Assert\.AreEqual|StringAssert\.(?:Contains|StartsWith|EndsWith)"
    r"|CollectionAssert\.AreEqual)\s*\(")

#: Katalogi porównywane przez pozycję 6.D131.
KATALOGI = ("tests/Game.Tests", "tests/Sim.Tests")


def _tresc_literalu(zrodlo, i):
    """Sklejona treść literału zaczynającego się na `i`, razem z `+` przez wiersze."""
    czesci = []
    j = i
    while True:
        while j < len(zrodlo) and zrodlo[j] in "@$":
            j += 1
        if j >= len(zrodlo) or zrodlo[j] != '"':
            break
        k = j + 1
        while k < len(zrodlo):
            if zrodlo[k] == "\\":
                k += 2
                continue
            if zrodlo[k] == '"':
                break
            k += 1
        czesci.append(zrodlo[j + 1:k])
        j = k + 1
        while j < len(zrodlo) and zrodlo[j] in " \n\t\r":
            j += 1
        if j < len(zrodlo) and zrodlo[j] == "+":
            j += 1
            while j < len(zrodlo) and zrodlo[j] in " \n\t\r":
                j += 1
            continue
        break
    return "".join(czesci)


def piny(katalog, root=ROOT):
    """`[(plik, wiersz, rodzaj, tresc)]` dla asercji z literałem jako wartością oczekiwaną.

    Wywołania szukane w MASCE, a treść brana z ORYGINAŁU — maska ma te same indeksy,
    więc jedno przejście wystarcza na oba.
    """
    znalezione = []
    for sciezka in sorted(glob.glob(os.path.join(root, katalog, "*.cs"))):
        with open(sciezka, encoding="utf-8") as uchwyt:
            zrodlo = uchwyt.read()
        maska = CTM.maska(zrodlo)
        for dopasowanie in ASERCJA.finditer(maska):
            i = dopasowanie.end()
            # Białe znaki przeskakiwane po ORYGINALE, nie po masce: w masce literał
            # jest spacjami, więc pętla po masce przeszłaby przez niego na wylot
            # i nie zobaczyła ani jednego pinu. Zmierzone: 0 zamiast 44.
            while i < len(zrodlo) and zrodlo[i] in " \n\t\r":
                i += 1
            j = i
            while j < len(zrodlo) and zrodlo[j] in "@$":
                j += 1
            if j >= len(zrodlo) or zrodlo[j] != '"':
                continue
            znalezione.append((
                os.path.basename(sciezka),
                zrodlo[:dopasowanie.start()].count("\n") + 1,
                dopasowanie.group(1),
                _tresc_literalu(zrodlo, i),
            ))
    return znalezione


def per_plik(katalog, root=ROOT):
    """`{plik: ile}` — tylko pliki z co najmniej jednym pinem."""
    policzone = {}
    for plik, _wiersz, _rodzaj, _tresc in piny(katalog, root):
        policzone[plik] = policzone.get(plik, 0) + 1
    return policzone


def main():
    for katalog in KATALOGI:
        znalezione = piny(katalog)
        print(f"[PINY] {katalog}: {len(znalezione)}")
        for plik, ile in sorted(per_plik(katalog).items()):
            print(f"        {ile:4d}  {plik}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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


# --- 6.D141: piny LICZBOWE -------------------------------------------------------

#: Literał liczbowy C#: dziesiętny albo szesnastkowy, z opcjonalnym podkreśleniem
#: jako separatorem tysięcy (`248_900.0`), wykładnikiem (`1e-12`) i przyrostkiem
#: typu (`4L`, `1e-3f`, `2u`, `1.5m`).
LICZBA = re.compile(
    r"[-+]?(?:0[xX][0-9a-fA-F_]+"
    r"|\d[\d_]*\.?[\d_]*(?:[eE][-+]?\d+)?)"
    r"(?:[fFdDmMuUlL]{0,2})\b")

#: Czy literał jest zmiennoprzecinkowy: ma kropkę, wykładnik albo przyrostek `f`/`d`/`m`.
#: Rozróżnienie jest treścią, nie ozdobą — patrz `piny_liczbowe`.
ZMIENNOPRZECINKOWY = re.compile(r"[.eE]|[fFdDmM]$")

#: Asercja, która w ogóle MOŻE nieść tolerancję. `StringAssert` i `CollectionAssert`
#: trzeciego argumentu liczbowego nie przyjmują, więc pinu liczbowego nie tworzą.
ASERCJA_LICZBOWA = "Assert.AreEqual"


def argumenty(maska, start):
    """`[(poczatek, koniec)]` argumentów wywołania, którego `(` skończyło się na `start`.

    Cięcie idzie po MASCE, więc przecinek wewnątrz literału napisowego nie dzieli
    argumentów, a zagnieżdżone wywołanie (`Assert.AreEqual(f(a, b), c)`) liczy się
    jako jeden argument.
    """
    glebokosc = 1
    i = poczatek = start
    out = []
    while i < len(maska) and glebokosc > 0:
        znak = maska[i]
        if znak == "(":
            glebokosc += 1
        elif znak == ")":
            glebokosc -= 1
            if glebokosc == 0:
                out.append((poczatek, i))
                break
        elif znak == "," and glebokosc == 1:
            out.append((poczatek, i))
            poczatek = i + 1
        i += 1
    return out


def argumenty_z_nawiasami(maska, start):
    """Jak `argumenty`, ale głębokość liczy TAKŻE po `[` i `{` — 6.D145.

    **Po co osobna funkcja, a nie poprawka tamtej.** `argumenty` liczy wyłącznie
    nawiasy okrągłe, więc `CollectionAssert.AreEqual(new[] { "a", "b" }, x, "powód")`
    rozpada się jej na PIĘĆ argumentów zamiast trzech. Dla 6.D145, które pyta o to,
    czy OSTATNI argument jest komunikatem, jest to różnica rozstrzygająca.

    **Zmierzone 11.09.2026, i dlatego tamta zostaje nietknięta:** na 2593 wywołaniach
    asercji w obu katalogach testowych obie funkcje różnią się w **28** i wszystkie 28
    to `CollectionAssert.*`. Na `Assert.AreEqual` — jedynej rodzinie, którą czyta
    `piny_liczbowe` — różnicy nie ma ani jednej, a `piny` w ogóle nie tnie argumentów
    (patrzy na znak tuż za `(`). Liczby 6.D141 są więc tą poprawką NIETKNIĘTE
    i nie trzeba ich przeliczać.
    """
    glebokosc = 1
    i = poczatek = start
    out = []
    while i < len(maska) and glebokosc > 0:
        znak = maska[i]
        if znak in "([{":
            glebokosc += 1
        elif znak in ")]}":
            glebokosc -= 1
            if glebokosc == 0:
                out.append((poczatek, i))
                break
        elif znak == "," and glebokosc == 1:
            out.append((poczatek, i))
            poczatek = i + 1
        i += 1
    return out


def piny_liczbowe(katalog, root=ROOT):
    """`[(plik, wiersz, wartosc, tolerancja)]` — asercje z LICZBĄ jako wartością oczekiwaną.

    `tolerancja` to literał trzeciego argumentu, gdy jest liczbą, i `None`, gdy go nie
    ma albo gdy jest komunikatem. **To rozróżnienie jest całym powodem, dla którego
    ta funkcja jest osobna od `piny`**, i pole „Dlaczego" pozycji 6.D141 nazywa je
    wprost: pin z tolerancją mówi „wartość w paśmie", pin bez niej — „dokładnie ta
    liczba", a przy zmiennoprzecinkowej to dwa różne zdania o kodzie.

    **Zmierzone 11.09.2026** (`tests/Game.Tests` + `tests/Sim.Tests`, 627 pinów):

        całkowitych                   336, z tolerancją **0**
        zmiennoprzecinkowych          291, bez tolerancji **14**
        tolerancja zapisana jako 0,0  132

    Dwa wiersze z tej tabeli są wynikiem, a nie statystyką. Po pierwsze: tolerancja
    jest wyłącznie rzeczą zmiennoprzecinkową — ani jeden pin całkowity jej nie ma,
    i to jest zdanie o kodzie, nie o przypadku. Po drugie: **porównań dokładnych na
    liczbie zmiennoprzecinkowej jest 146, nie 14** — 132 z nich deklaruje to jawnie,
    pisząc `0.0` jako trzeci argument, a 14 przez przemilczenie. Sama liczba „14"
    byłaby więc dziesięciokrotnie zaniżona.
    """
    znalezione = []
    for sciezka in sorted(glob.glob(os.path.join(root, katalog, "*.cs"))):
        with open(sciezka, encoding="utf-8") as uchwyt:
            zrodlo = uchwyt.read()
        maska = CTM.maska(zrodlo)
        for dopasowanie in ASERCJA.finditer(maska):
            if dopasowanie.group(1) != ASERCJA_LICZBOWA:
                continue
            args = argumenty(maska, dopasowanie.end())
            if not args:
                continue
            wartosc = zrodlo[args[0][0]:args[0][1]].strip()
            if not LICZBA.fullmatch(wartosc):
                continue
            tolerancja = None
            if len(args) >= 3:
                trzeci = zrodlo[args[2][0]:args[2][1]].strip()
                if LICZBA.fullmatch(trzeci):
                    tolerancja = trzeci
            znalezione.append((
                os.path.basename(sciezka),
                zrodlo[:dopasowanie.start()].count("\n") + 1,
                wartosc,
                tolerancja,
            ))
    return znalezione


def zmiennoprzecinkowy(literal):
    """Czy literał liczbowy jest zmiennoprzecinkowy."""
    return bool(ZMIENNOPRZECINKOWY.search(literal))


def rozklad_liczbowych(katalog, root=ROOT):
    """`{...}` — cztery liczby, o które prosi pole „Wyjście" pozycji 6.D141."""
    znalezione = piny_liczbowe(katalog, root)
    zmienne = [w for w in znalezione if zmiennoprzecinkowy(w[2])]
    calkowite = [w for w in znalezione if not zmiennoprzecinkowy(w[2])]
    return {
        "razem": len(znalezione),
        "z_tolerancja": sum(1 for w in znalezione if w[3] is not None),
        "bez_tolerancji": sum(1 for w in znalezione if w[3] is None),
        "zmiennoprzecinkowe": len(zmienne),
        "zmiennoprzecinkowe_bez_tolerancji": sum(1 for w in zmienne if w[3] is None),
        "calkowite": len(calkowite),
        "calkowite_z_tolerancja": sum(1 for w in calkowite if w[3] is not None),
        "tolerancja_zero": sum(1 for w in znalezione if w[3] is not None
                               and float(w[3].rstrip("fFdDmMuUlL") or 0) == 0.0),
    }


def main():
    for katalog in KATALOGI:
        znalezione = piny(katalog)
        print(f"[PINY] {katalog}: {len(znalezione)} napisowych")
        for plik, ile in sorted(per_plik(katalog).items()):
            print(f"        {ile:4d}  {plik}")
        r = rozklad_liczbowych(katalog)
        print(f"[PINY] {katalog}: {r['razem']} liczbowych — "
              f"{r['z_tolerancja']} z tolerancja, {r['bez_tolerancji']} bez")
        print(f"        zmiennoprzecinkowych {r['zmiennoprzecinkowe']}, "
              f"z nich BEZ tolerancji {r['zmiennoprzecinkowe_bez_tolerancji']}")
        print(f"        calkowitych {r['calkowite']}, "
              f"z nich Z tolerancja {r['calkowite_z_tolerancja']} "
              "(Assert.AreEqual(int,int,double) nie ma przeciazenia)")
        # 6.D141: tolerancja 0,0 JEST porownaniem dokladnym — bez tego wiersza
        # licznik „bez tolerancji" mowi o czyms dziesieciokrotnie wezszym.
        print(f"        tolerancja zapisana jako 0,0: {r['tolerancja_zero']} — "
              f"porownan DOKLADNYCH razem: "
              f"{r['tolerancja_zero'] + r['zmiennoprzecinkowe_bez_tolerancji']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

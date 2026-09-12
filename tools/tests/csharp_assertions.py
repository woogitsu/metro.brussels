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

**Przejscie po ciele klasy stoi w `csharp_test_methods` i jest JEDNO (6.D30).**
6.D28 dopisala je tutaj, obok starszego `_poziom_bezposredni`, bo tamto wycinalo
wnetrza klamr — poprawnie dla wykrywania brakujacego atrybutu, bezuzytecznie dla
asercji, ktora siedzi wlasnie w tym wnetrzu. Dwa przejscia po tym samym drzewie
rozjezdzaja sie po cichu, wiec 6.D30 sciagnela nowsze do modulu nizszego i skasowala
starsze; oba zastosowania chodza teraz po tej samej strukturze, a test zgodnosci
zada **rownosci**, nie pasma.

**Cialo metody ma DWIE postacie i pierwsza wersja tego czytnika znala tylko jedna.**
Blok `{ ... }` oraz cialo wyrazeniowe `=> wyrazenie;`. Zmierzone: przy samych blokach
wychodzila **jedna** metoda „bez asercji" —
`Lista_funkcji_KCV_jest_dokladnie_ta_ktora_podaje_STIB` — ktora asertuje
`CollectionAssert.AreEqual` w ciele wyrazeniowym. Czytnik, ktory jednej z tych postaci
nie zna, nie zglasza braku asercji: zglasza **wlasna niewiedze** jako brak.

**Od 6.D145 modul odpowiada na DWA pytania, nie jedno, i warto je rozroznic.**
Starsze: czy metoda testowa ma w tresci JAKAKOLWIEK asercje (bramka od 6.D28).
Nowsze: czy pojedyncza asercja niesie KOMUNIKAT — to samo pytanie, ktore po stronie
Pythona zadaje `NIEME_ASERCJE`, tyle ze komunikat C# stoi jako OSTATNI argument
i nie ma wlasnej skladni. Zmierzone 11.09.2026: **1381 bez komunikatu, 1140 z nim,
72 nierozstrzygniete** na 2593 wywolaniach.

**Asercja to takze wywolanie pomocnika `Assert*`.** Zmierzone na tym drzewie: przy
samych wywolaniach `Assert.`/`StringAssert.`/`CollectionAssert.` wychodzilo **piec**
metod bez asercji, z czego cztery wolaja lokalny `AssertBits(...)`, ktory asertuje
w swoim ciele. Rozszerzenie na pomocnikow `Assert*` zbija to do jednej (tej z ciala
wyrazeniowego). Sprawdzone tez rozwiazywanie pomocnikow po CIELE, nie po nazwie —
i nie daje ani jednej metody wiecej, wiec zostaje regula prostsza.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csharp_pins as CP  # noqa: E402
import tree_walk as TW  # noqa: E402
import csharp_test_methods as CTM  # noqa: E402

#: Wywolanie asercji MSTest wprost.
ASERCJA = re.compile(r"\b(?:Assert|StringAssert|CollectionAssert)\s*\.")
#: Wywolanie pomocnika, ktorego nazwa zaczyna sie od `Assert` — patrz docstring.
POMOCNIK = re.compile(r"\bAssert[A-Za-z0-9_]*\s*\(")
#: Nazwa metody na koncu naglowka — jedno zrodlo, w module nizszym (6.D30).
NAGLOWEK = CTM.NAGLOWEK


def metody_testowe(root=ROOT):
    """`[(plik, klasa, metoda, ma_asercje)]` dla metod z atrybutem testowym."""
    found = []
    for path in CTM.pliki(root):
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        for klasa in CTM.KLASA.finditer(source):
            surowe = CTM._cialo_klasy(source, klasa.end())
            for naglowek, cialo in CTM.czlonkowie(surowe):
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


# --- 6.D145: KOMUNIKAT przy asercji C# -------------------------------------------

#: Ile argumentow kazda asercja MSTest ma OBOWIAZKOWO, czyli zanim zacznie sie miejsce
#: na komunikat. Tabela, nie regula: arnosc jest wlasnoscia API, a nie ksztaltu tekstu,
#: i zgadnieta byla by zgadnietym faktem. Zmierzone 11.09.2026 — wywolan spoza tej
#: tabeli w obu katalogach testowych jest ZERO, i pilnuje tego osobny test.
OBOWIAZKOWE_ARGUMENTY = {
    "Assert.AreEqual": 2, "Assert.AreNotEqual": 2,
    "Assert.AreSame": 2, "Assert.AreNotSame": 2,
    "Assert.IsTrue": 1, "Assert.IsFalse": 1, "Assert.IsNull": 1, "Assert.IsNotNull": 1,
    "Assert.IsInstanceOfType": 2, "Assert.Fail": 0, "Assert.Inconclusive": 0,
    "Assert.ThrowsException": 1,
    "StringAssert.Contains": 2, "StringAssert.StartsWith": 2, "StringAssert.EndsWith": 2,
    "StringAssert.Matches": 2, "StringAssert.DoesNotMatch": 2,
    "CollectionAssert.AreEqual": 2, "CollectionAssert.AreNotEqual": 2,
    "CollectionAssert.AreEquivalent": 2, "CollectionAssert.Contains": 2,
    "CollectionAssert.DoesNotContain": 2, "CollectionAssert.IsSubsetOf": 2,
    "CollectionAssert.AllItemsAreUnique": 1,
}

#: Jedyna rodzina, w ktorej argument NADMIAROWY moze nie byc komunikatem: przy DOKLADNIE
#: trzech argumentach trzeci jest albo `double delta`, albo `string message`. Wszedzie
#: indziej MSTest ma w tej pozycji wylacznie `string message` — wiec wyrazenie, ktore
#: sie kompiluje, jest tam napisem, i nie trzeba tego zgadywac.
RODZINA_Z_TOLERANCJA = ("Assert.AreEqual", "Assert.AreNotEqual")

#: Wywolanie asercji z nazwa i rodzina — `<T>` przeskakiwane, bo `ThrowsException<T>`.
WYWOLANIE = re.compile(
    r"\b(Assert|StringAssert|CollectionAssert)\.([A-Za-z]+)(?:<[^>()]*>)?\s*\(")

#: Poczatek literalu napisowego: zwykly, `@`-cytowany, interpolowany albo oba naraz.
LITERAL_NAPISOWY = re.compile(r'^[@$]*"')

#: Pierwszy argument, ktory NA PEWNO jest typu `string` — 6.D156.
#:
#: **Zawezenie SZCZELNE, i szczelnosc jest tu cala trescia.** Przeciazenie
#: `Assert.AreEqual(double, double, double)` zada, zeby OBA porownywane byly
#: zmiennoprzecinkowe. Napis do `double` nie konwertuje sie w C# nigdy — wiec gdy
#: pierwszy argument jest napisem, przeciazenie z tolerancja NIE MOZE sie zwiazac
#: i trzeci argument jest komunikatem. Nie jest to heurystyka: jest to wykluczenie.
#:
#: **Dlaczego konkatenacja WOLNO, a kropka NIE.** `"x" + y` jest napisem, bo w C#
#: `string + cokolwiek` daje napis. `"x".Length` napisem NIE JEST — daje `int`, ktory
#: do `double` konwertuje sie bez zarzutu, wiec przeciazenie z tolerancja wraca do gry.
#: Wzorzec przepuszcza wiec po literale wylacznie `+` albo koniec wyrazenia; kropka,
#: nawias kwadratowy i wszystko inne zostawiaja asercje NIEROZSTRZYGNIETA.
#:
#: **Wzorzec jest ZACHOWAWCZY z wyboru.** Czyta cialo literalu prosto, wiec na napisie
#: interpolowanym z zagniezdzonym cudzyslowem konca nie znajdzie i nie dopasuje sie —
#: czyli zostawi asercje w klasie „nie wiem". Falszywy BRAK zawezenia nie kosztuje nic;
#: falszywe zawezenie zamienialoby zadeklarowana niewiedze na ciche zgadywanie, czyli
#: dokladnie to, przed czym ostrzega pole „Dlaczego to nie jest dopisanie reguly".
PIERWSZY_ARGUMENT_NAPISOWY = re.compile(
    r'^[@$]*"(?:[^"\\]|\\.)*"\s*(?:\+.*)?$', re.S)

#: Zawezenie ODRZUCONE i powod, dla ktorego stoi tu zapisane, a nie milczy — 6.D156.
#:
#: Kuszace bylo zawezic takze po literale CALKOWITYM w pierwszym argumencie: przy
#: `Assert.AreEqual(0, x, cos)` wyglada to na komunikat. **Jest nieszczelne**: `int`
#: konwertuje sie do `double`, wiec `AreEqual(double, double, double)` zwiazac sie MOZE,
#: a o tym, ktore przeciazenie wybral kompilator, rozstrzyga typ TRZECIEGO argumentu —
#: czyli dokladnie to, czego czytnik nie wie. Zmierzone 12.09.2026: dotyczyloby to
#: **25** asercji, i wszystkie 25 zostaja NIEROZSTRZYGNIETE.
LITERAL_CALKOWITY_ODRZUCONY = re.compile(r"^-?\d+$")

BEZ_KOMUNIKATU = "bez"
Z_KOMUNIKATEM = "z"
NIEROZSTRZYGNIETE = "nierozstrzygniete"


def klasa_komunikatu(nazwa, argumenty, tresc):
    """Ktora z trzech klas — 6.D145. `argumenty` i `tresc` z tego samego zrodla.

    **Trzy klasy, nie dwie, i trzecia jest tu trescia, a nie porazka.** Komunikat C#
    stoi jako OSTATNI argument, nie jako drugi, i nie ma wlasnej skladni: rozpoznaje
    sie go po TYPIE, a typu identyfikatora nie da sie odczytac bez sprawdzacza typow,
    ktorego to repozytorium nie ma i miec nie bedzie (ta sama granica, co w 6.D141).
    Klasa `NIEROZSTRZYGNIETE` nazywa dokladnie to, czego czytnik nie wie — zamiast
    zgadnac i zameldowac pewnosc, ktorej nie ma.
    """
    wymagane = OBOWIAZKOWE_ARGUMENTY[nazwa]
    if len(argumenty) <= wymagane:
        return BEZ_KOMUNIKATU
    a, b = argumenty[-1]
    ostatni = tresc[a:b].strip()
    if LITERAL_NAPISOWY.match(ostatni):
        return Z_KOMUNIKATEM
    if nazwa in RODZINA_Z_TOLERANCJA and len(argumenty) == 3:
        if CP.LICZBA.match(ostatni):
            return BEZ_KOMUNIKATU
        # Zawezenie po PIERWSZYM argumencie — 6.D156. Napis wyklucza przeciazenie
        # z tolerancja SZCZELNIE; literal calkowity nie, i dlatego go tu nie ma.
        pierwszy_a, pierwszy_b = argumenty[0]
        if PIERWSZY_ARGUMENT_NAPISOWY.match(tresc[pierwszy_a:pierwszy_b].strip()):
            return Z_KOMUNIKATEM
        return NIEROZSTRZYGNIETE
    return Z_KOMUNIKATEM


def asercje(katalog, root=ROOT):
    """`[(plik, wiersz, nazwa, klasa)]` dla kazdego wywolania asercji w katalogu."""
    znalezione = []
    for sciezka in TW.znajdz(os.path.join(root, katalog), "*.cs", root):
        with open(sciezka, encoding="utf-8") as uchwyt:
            zrodlo = uchwyt.read()
        maska = CTM.maska(zrodlo)
        for dopasowanie in WYWOLANIE.finditer(maska):
            nazwa = "%s.%s" % (dopasowanie.group(1), dopasowanie.group(2))
            if nazwa not in OBOWIAZKOWE_ARGUMENTY:
                continue
            args = CP.argumenty_z_nawiasami(maska, dopasowanie.end())
            znalezione.append((
                os.path.basename(sciezka),
                zrodlo[:dopasowanie.start()].count("\n") + 1,
                nazwa,
                klasa_komunikatu(nazwa, args, zrodlo),
            ))
    return znalezione


def nazwy_spoza_tabeli(katalog, root=ROOT):
    """Nazwy asercji, ktorych `OBOWIAZKOWE_ARGUMENTY` nie zna — maja byc puste."""
    obce = set()
    for sciezka in TW.znajdz(os.path.join(root, katalog), "*.cs", root):
        with open(sciezka, encoding="utf-8") as uchwyt:
            maska = CTM.maska(uchwyt.read())
        for dopasowanie in WYWOLANIE.finditer(maska):
            nazwa = "%s.%s" % (dopasowanie.group(1), dopasowanie.group(2))
            if nazwa not in OBOWIAZKOWE_ARGUMENTY:
                obce.add(nazwa)
    return sorted(obce)


def bez_komunikatu_per_plik(katalog, root=ROOT):
    """`{plik: ile}` — tylko pliki z co najmniej jedna asercja bez komunikatu."""
    policzone = {}
    for plik, _w, _n, klasa in asercje(katalog, root):
        if klasa == BEZ_KOMUNIKATU:
            policzone[plik] = policzone.get(plik, 0) + 1
    return policzone


def rozklad_komunikatow(katalog, root=ROOT):
    """`{klasa: ile}` plus `razem` — trzy klasy sumuja sie do calosci."""
    dane = asercje(katalog, root)
    out = {BEZ_KOMUNIKATU: 0, Z_KOMUNIKATEM: 0, NIEROZSTRZYGNIETE: 0}
    for _p, _w, _n, klasa in dane:
        out[klasa] += 1
    out["razem"] = len(dane)
    return out


def main():
    dane = coverage()
    print("[ASERCJE C#] metod testowych:        %d" % dane["metody_testowe"])
    print("[ASERCJE C#] z asercja w tresci:     %d" % dane["z_asercja"])
    print("[ASERCJE C#] BEZ asercji w tresci:   %d" % dane["bez_asercji"])
    for plik, klasa, metoda in bez_asercji():
        print("BRAK ASERCJI: %s :: %s.%s" % (plik, klasa, metoda))

    # 6.D145: to samo pytanie o KOMUNIKAT, nie o obecnosc asercji. Trzy klasy,
    # bo trzecia nazywa to, czego czytnik bez sprawdzacza typow nie wie.
    razem = {BEZ_KOMUNIKATU: 0, Z_KOMUNIKATEM: 0, NIEROZSTRZYGNIETE: 0, "razem": 0}
    for katalog in CP.KATALOGI:
        rozklad = rozklad_komunikatow(katalog)
        print("[KOMUNIKATY C#] %-16s bez=%d z=%d nierozstrzygnietych=%d razem=%d"
              % (katalog, rozklad[BEZ_KOMUNIKATU], rozklad[Z_KOMUNIKATEM],
                 rozklad[NIEROZSTRZYGNIETE], rozklad["razem"]))
        for klucz, ile in rozklad.items():
            razem[klucz] += ile
    print("[KOMUNIKATY C#] RAZEM            bez=%d z=%d nierozstrzygnietych=%d razem=%d"
          % (razem[BEZ_KOMUNIKATU], razem[Z_KOMUNIKATEM],
             razem[NIEROZSTRZYGNIETE], razem["razem"]))

    return 1 if dane["bez_asercji"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

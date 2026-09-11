#!/usr/bin/env python3
"""Przejście po drzewie repozytorium z odsianiem katalogów pominiętych w `.gitignore`.

**Skąd ten moduł.** Zmierzone 09.09.2026 przy 6.D36: pierwszy skan tamtej pozycji,
liczony od korzenia, dał **6 i 12** wystąpień zamiast 1 i 2, bo wszedł do kopii drzewa
leżącej pod `.claude/`. Kopie niosły STARY kod, więc skan raportowałby usterkę już
naprawioną — a to jest ta sama rodzina, którą projekt tropi od 6.D27: przyrząd
meldujący sprawdzenie, którego nie zrobił.

**Dlaczego pozycja istnieje, choć dziś prawie nic nie pada.** Trzynaście z czternastu
wywołań `os.walk` w `tools/` startuje z NAZWANEGO podkatalogu (`tools`, `src`, `docs`,
`reports`, `data`), a kopie 6.D36 leżały pod `.claude/` — więc ochrona jest **uboczna
wobec nazewnictwa**, a nie zapisana. Zmierzone 10.09.2026 przez położenie kopii drzewa
pod `tools/build/kopia/` (`build/` jest w `.gitignore`, więc git jej nie widzi):
z piętnastu liczb raportowanych przez skany **jedna** urosła —
`test_dead_constants.definicje` **917 → 1511**. Jedna, a nie zero: „prawie nic"
znaczy tu „jedna liczba jest już dziś nieprawdziwa", a nie „zagrożenie jest hipotetyczne".

**Lista katalogów jest CZYTANA z `.gitignore`, a nie przepisana.** Druga kopia tej
samej wiedzy rozjechałaby się z pierwszą przy pierwszym wpisie dodanym do `.gitignore`
— dokładnie tak, jak `BUILD_DIRS` w `test_readme_claims.py`, który zna `bin` i `obj`,
a nie zna `build`, `renders` ani `.venv`.

**Czego ten moduł NIE robi.** Nie jest implementacją `.gitignore`. Bierze wyłącznie
wpisy **katalogowe** — wiersze zakończone ukośnikiem — bo tylko one mogą odciąć całą
gałąź przejścia. Wzorce plikowe (`*.pyc`, `*.blend1`) zostawia przejściu, bo ich
odsianie jest sprawą filtra po rozszerzeniu, a nie przycinania gałęzi. Nie zna też
gwiazdki w nazwie katalogu — dziś w `.gitignore` tego projektu takiego wpisu nie ma
i `test_tree_walks.py` sprawdza, że nadal nie ma, zamiast milczeć, gdy się pojawi.
"""
import fnmatch
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GITIGNORE = os.path.join(ROOT, ".gitignore")


def wzorce_katalogow(tekst):
    """`(nazwy, sciezki)` z treści `.gitignore`.

    `nazwy` to wpisy bez ukośnika w środku (`build/`), obowiązujące na KAŻDYM
    poziomie — tak samo, jak czyta je git. `sciezki` to wpisy zakotwiczone
    (`data/gtfs/`, `.claude/worktrees/`), liczone od korzenia repozytorium.
    """
    nazwy, sciezki = set(), set()
    for wiersz in tekst.splitlines():
        wpis = wiersz.strip()
        if not wpis or wpis.startswith("#") or wpis.startswith("!"):
            continue
        if not wpis.endswith("/"):
            continue
        wpis = wpis[:-1]
        if wpis.startswith("/"):
            sciezki.add(wpis[1:])
        elif "/" in wpis:
            sciezki.add(wpis)
        else:
            nazwy.add(wpis)
    return nazwy, sciezki


def _wzorce(root):
    sciezka = os.path.join(root, ".gitignore")
    if not os.path.isfile(sciezka):
        sciezka = GITIGNORE
    with open(sciezka, encoding="utf-8") as uchwyt:
        return wzorce_katalogow(uchwyt.read())


def pominiete(root=ROOT):
    """Zbiory `(nazwy, sciezki)` dla tego drzewa — do wypisania w raporcie i w testach."""
    return _wzorce(root)


def walk(top, root=ROOT):
    """`os.walk`, z którego wycięte są gałęzie pominięte w `.gitignore`.

    Podpis i wynik są takie same jak w `os.walk`, żeby podmiana w miejscu wołania
    była jednym słowem. Lista `dirs` jest przycinana W MIEJSCU (`dirs[:]`), bo tylko
    tak `os.walk` dowiaduje się, że w gałąź nie wchodzić.
    """
    nazwy, sciezki = _wzorce(root)
    for baza, katalogi, pliki in os.walk(top):
        wzgledna = os.path.relpath(baza, root).replace(os.sep, "/")
        przedrostek = "" if wzgledna == "." else wzgledna + "/"
        katalogi[:] = [k for k in katalogi
                       if k not in nazwy and przedrostek + k not in sciezki]
        yield baza, katalogi, pliki


def znajdz(top, wzorzec, root=ROOT):
    """Pliki pod `top` pasujące do `wzorzec`, bez gałęzi pominiętych w `.gitignore`.

    **Trzeci kształt przejścia po drzewie (6.D117).** 6.D74 zamknęło `os.walk`
    w `walk`, 6.D97 zdjęło kopie listy katalogów — a `glob.glob(…, recursive=True)`
    przechodził bokiem przez oba. Zmierzone 11.09.2026: **3** takie wywołania
    w `tools/`, każde z WŁASNĄ regułą odsiania (`.godot` w jednym, `obj`/`bin`
    w dwóch pozostałych, po jednej kopii na miejsce).

    Wynik jest posortowany i absolutny — tak jak `glob.glob` z absolutnym wzorcem,
    żeby podmiana w miejscu wołania nie zmieniała niczego poza samym odsianiem.
    """
    znalezione = []
    for baza, _katalogi, pliki in walk(top, root):
        znalezione += [os.path.join(baza, nazwa) for nazwa in pliki
                       if fnmatch.fnmatch(nazwa, wzorzec)]
    return sorted(znalezione)

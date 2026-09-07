#!/usr/bin/env python3
"""Przegląd mutacyjny bramek: psuje kod i sprawdza, czy testy to zauważą.

**Po co.** Audyt z 02.09.2026 znalazł cztery zielone bramki, które niczego nie
sprawdzały, i wszystkie cztery znalazła mutacja, nie czytanie kodu. W tej samej sesji
doszły dwie kolejne. Sześć na sześć prób — to nie jest wyjątek, to stan. Zielona bramka
bez pokrycia jest gorsza niż brak bramki, bo usypia.

**Czego to narzędzie NIE robi.** Nie mutuje testów. Mutuje **kod pod testem** i pyta,
czy zestaw testów to wyłapie. Mutacja, która przeżyje, znaczy jedno z dwojga: albo
w tym miejscu nie ma pokrycia, albo jest **mutantem równoważnym** — zmianą, której nie
da się zaobserwować. Jedno i drugie trzeba obejrzeć; narzędzie nie zgaduje, które to.

**Pięć klas mutacji.** Do 05.09.2026 były dwie — operatory porównań i stałe liczbowe
**stojące w porównaniach** — i `reports/mutation-sweep.md` sam wypisywał ten rozjazd
w tabeli „czego ten przebieg NIE pokrywa": pozycja 5.1 mówi „każdą kontrolę", a narzędzie
nie tykało przypisań, wywołań ani łączników logicznych. Dziś klasy są następujące:

| klasa | co robi | przykład |
|---|---|---|
| `operator` | operator porównania na sąsiedni | `a < b` -> `a <= b` |
| `prog` | stała liczbowa **w porównaniu** | `a < 1.5` -> `a < 1.515` |
| `logika` | łącznik logiczny na przeciwny | `a and b` -> `a or b` |
| `argument` | stała **w argumencie wywołania** | `round(x, 3)` -> `round(x, 4)` |
| `przypisanie` | zdjęta akumulacja z przypisania augmentowanego | `t += dt` -> `t = dt` |

`--operators` wybiera podzbiór; `--operators operator,prog` odtwarza stary zestaw
**co do identyfikatora**, więc porównanie „przed" i „po" jest sprawdzalne, a nie
opowiedziane.

**Ocalała, ale czy uruchomiona.** Przypisania i wywołania stoją często w kodzie,
którego żaden test nie wykonuje — w gałęzi `if __name__ == "__main__"`, w obsłudze
błędu, w wariancie CLI. Taka mutacja przeżywa **nie dlatego, że bramka nie bramkuje,
tylko dlatego, że nikt jej nie odpalił**, i policzona razem z prawdziwą dziurą kłamie
o pokryciu. Dlatego przebieg mierzy raz, przed mutowaniem, **które wiersze zestaw
testów naprawdę wykonuje** (`coverage_map`), i dzieli ocalałe na dwie kupki. Nie jest
to ta sama rzecz co „nierozstrzygnięte": tamto mówi o **wyroczni**, która nie doszła
do końca, to mówi o **mutancie**, do którego nie doszło wykonanie.

**Determinizm.** Mutacje powstają z AST w ustalonej kolejności (plik, wiersz, kolumna),
więc dwa przebiegi na tym samym drzewie dają tę samą listę i te same identyfikatory.

**`--only` dopasowuje PODCIĄG ścieżki, nie nazwę pliku — to jest zamierzone.**
Zdecydowane 06.09.2026 (6.D18, #301), pomiarem, nie gustem: `test_cli_lists_only_the_requested_class`
woła `--only tools/track/` i oczekuje mutacji z CAŁEGO katalogu naraz — dopasowanie
wyłącznie po nazwie pliku by to zablokowało, bo `tools/track/` nie jest nazwą żadnego
pliku. Cena podciągu: `--only sweep.py` łapie też `tunnel_sweep.py` (zmierzone przy
6.D15: 117 mutacji z `tools/blender/sweep.py` i 68 z `tools/blender/tunnel_sweep.py`
pod jedną etykietą). Cztery przebiegi sprzed tej decyzji (6.B6, 6.B7, 6.B8, 6.D5) wołały
`--only` basename'em, nie wiedząc, że złapały drugi moduł — ich raporty są **datowanymi
pomiarami** i się ich nie przelicza. Od 6.D18 przebieg z `--only` wypisuje, ZANIM
dotknie dziennika czy zmutuje choć jeden plik, ile modułów i ile mutacji złapał, z ich
nazwami — więc rozjazd jak przy 6.D15 jest widoczny w pierwszym wierszu wyjścia, także
dla `--list`, zamiast czekać na czyjeś porównanie liczb.
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures
import dataclasses
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Dziennik jest jednym plikiem dla wszystkich robotników, więc zapis idzie
# pod zamkiem. Bez niego dwa wiersze potrafią się przepleść i oba przepadają.
JOURNAL_LOCK = threading.Lock()

# Operator -> (napis w kodzie, wzorzec szukający go, napis po mutacji).
# Wzorce pilnują, żeby `<` nie trafił w `<=` ani w `<<`.
OPERATORS = {
    ast.Lt: ("<", r"<(?!=)", "<="),
    ast.LtE: ("<=", r"<=", "<"),
    ast.Gt: (">", r">(?!=)", ">="),
    ast.GtE: (">=", r">=", ">"),
    ast.Eq: ("==", r"==", "!="),
    ast.NotEq: ("!=", r"!=", "=="),
}

# Klasy mutacji w kolejności, w jakiej powstawały. Dwie pierwsze to cały zestaw
# sprzed 05.09.2026 — `--operators operator,prog` odtwarza tamten przebieg co do
# identyfikatora, więc różnica „przed/po" jest mierzalna, a nie deklarowana.
KINDS = ("operator", "prog", "logika", "argument", "przypisanie")
LEGACY_KINDS = ("operator", "prog")

# Token przypisania augmentowanego. Operatory dwuznakowe MUSZĄ być na liście jawnie.
# Wzorzec z samych jednoznakowych nie odpadłby z hukiem, tylko trafiłby w ogon: w `x **= y`
# dopasowałby drugą gwiazdkę i dał `x *= y` — mutację INNĄ niż opisana, za to poprawną
# składniowo, więc przechodzącą przez wszystkie strażniki parsowania.
AUG_TOKEN = re.compile(r"(\*\*|//|<<|>>|[-+*/%@&|^])=")


def mask_comments(span: str) -> str:
    """Ten sam napis z komentarzami zamienionymi na spacje.

    Między dwoma operandami wyrażenia może stać komentarz — legalnie, gdy całość
    jest w nawiasach:

        if (a       # tu and tam
                and b):

    Naiwne `re.search(r"\\band\\b", span)` trafiłoby w słowo z komentarza, splice
    rozwaliłby składnię, mutacja nie sparsowałaby się i **policzyłaby się jako
    zabita** — czyli w stronę zawyżania pokrycia. Maskowanie zachowuje długość
    napisu, więc indeksy pozostają te same.
    """
    out = []
    in_comment = False
    for char in span:
        if char == "\n":
            in_comment = False
            out.append(char)
        elif in_comment:
            out.append(" ")
        elif char == "#":
            in_comment = True
            out.append(" ")
        else:
            out.append(char)
    return "".join(out)


def shifted_number(value) -> str:
    """Sąsiednia wartość liczbowa: całkowita o jeden, zmiennoprzecinkowa o procent.

    Przesunięcie względne, żeby próg 0,001 i próg 1000 dostały zmianę tego samego
    rzędu co one same. Zero nie ma względnego sąsiedztwa, więc dostaje wartość wprost.
    """
    if isinstance(value, int):
        return repr(value + 1)
    return repr(value * 1.01 if value else 0.001)


@dataclasses.dataclass(frozen=True)
class Mutation:
    """Jedna zmiana: podmiana tekstu w jednym miejscu jednego pliku."""

    path: str          # ścieżka względem korzenia repo
    line: int          # 1-indeksowany wiersz, dla raportu
    start: int         # indeks znaku w pliku
    end: int
    was: str
    now: str
    kind: str          # "operator" albo "prog"

    @property
    def id(self) -> str:
        return f"{self.path}:{self.line}:{self.start}"

    def describe(self) -> str:
        return f"{self.path}:{self.line} {self.kind} `{self.was}` -> `{self.now}`"

    def apply(self, source: str) -> str:
        assert source[self.start:self.end] == self.was, (
            f"{self.id}: w pliku stoi {source[self.start:self.end]!r}, "
            f"oczekiwano {self.was!r}")
        return source[:self.start] + self.now + source[self.end:]


def line_offsets(source: str) -> list[int]:
    """Indeks pierwszego znaku każdego wiersza; wiersz 1 pod indeksem 1."""
    offsets = [0, 0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return offsets


def char_index(source: str, offsets: list[int], lineno: int, col_offset: int) -> int:
    """Pozycja AST (wiersz, offset BAJTOWY) na indeks znaku w pliku.

    `col_offset` w module `ast` liczy **bajty UTF-8**, nie znaki. W pliku z polskimi
    komentarzami te dwie liczby się rozjeżdżają, a splice pod złym indeksem rozwaliłby
    kod tak, że nie skompilowałby się i mutacja wyszłaby „zabita" bez sprawdzenia
    czegokolwiek.
    """
    start = offsets[lineno]
    end = offsets[lineno + 1] if lineno + 1 < len(offsets) else len(source)
    line = source[start:end]
    prefix = line.encode("utf-8")[:col_offset].decode("utf-8", errors="strict")
    return start + len(prefix)


def mutations_for(path: str, source: str, kinds=KINDS) -> list[Mutation]:
    """Mutacje dla jednego pliku, w ustalonej kolejności.

    `kinds` zawęża zestaw klas. Domyślnie wszystkie; `LEGACY_KINDS` daje dokładnie
    to, co narzędzie generowało przed 05.09.2026.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    offsets = line_offsets(source)
    rel = os.path.relpath(path, ROOT)
    found: list[Mutation] = []

    def between(left, right) -> tuple[int, str]:
        """Indeks początku i tekst szczeliny między dwoma węzłami."""
        start = char_index(source, offsets, left.end_lineno, left.end_col_offset)
        stop = char_index(source, offsets, right.lineno, right.col_offset)
        return start, source[start:stop]

    for node in ast.walk(tree):
        if isinstance(node, ast.BoolOp) and "logika" in kinds:
            was, now = ("and", "or") if isinstance(node.op, ast.And) else ("or", "and")
            for index in range(len(node.values) - 1):
                start, span = between(node.values[index], node.values[index + 1])
                match = re.search(rf"\b{was}\b", mask_comments(span))
                if match is None:
                    continue
                at = start + match.start()
                found.append(Mutation(
                    rel, source.count("\n", 0, at) + 1, at, at + len(was),
                    was, now, "logika"))
            continue

        if isinstance(node, ast.AugAssign) and "przypisanie" in kinds:
            start, span = between(node.target, node.value)
            match = AUG_TOKEN.search(mask_comments(span))
            if match is None:
                continue
            at = start + match.start()
            was = match.group(0)
            found.append(Mutation(
                rel, source.count("\n", 0, at) + 1, at, at + len(was),
                was, "=", "przypisanie"))
            continue

        if isinstance(node, ast.Call) and "argument" in kinds:
            for argument in [*node.args, *(kw.value for kw in node.keywords)]:
                if not isinstance(argument, ast.Constant):
                    continue
                value = argument.value
                at = char_index(source, offsets, argument.lineno, argument.col_offset)
                end = char_index(source, offsets,
                                 argument.end_lineno, argument.end_col_offset)
                text = source[at:end]
                if isinstance(value, bool):
                    # Zapis musi być dosłownym `True`/`False`; wszystko inne znaczy,
                    # że pozycje wskazują nie to, co myślimy, i lepiej pominąć.
                    if text not in ("True", "False"):
                        continue
                    replacement = "False" if value else "True"
                elif isinstance(value, (int, float)):
                    replacement = shifted_number(value)
                else:
                    continue
                if replacement == text:
                    continue
                found.append(Mutation(
                    rel, argument.lineno, at, end, text, replacement, "argument"))
            continue

        if not isinstance(node, ast.Compare):
            continue

        operands = [node.left, *node.comparators]
        # `if __name__ == "__main__"` NIE jest bramką, tylko konwencją modułu.
        # Zamiana na `!=` sprawia, że moduł uruchamia swoje CLI przy imporcie i zabija
        # cały zestaw — co narzędzie liczyło jako „test wykrył mutację". Na 996 mutacji
        # takich strażników było 35, z czego 27 zaliczono jako zabite. Zawyżały pokrycie
        # i nie mówiły nic o tym, czy jakakolwiek bramka bramkuje.
        if any(isinstance(x, ast.Name) and x.id == "__name__" for x in operands):
            continue
        for index, op in enumerate(node.ops if "operator" in kinds else ()):
            left, right = operands[index], operands[index + 1]
            spec = OPERATORS.get(type(op))
            if spec is None:
                continue
            was, pattern, now = spec

            span_start = char_index(source, offsets, left.end_lineno, left.end_col_offset)
            span_end = char_index(source, offsets, right.lineno, right.col_offset)
            span = source[span_start:span_end]
            match = re.search(pattern, span)
            if match is None:
                # Zapis, którego nie umiemy zlokalizować (np. nawiasy albo komentarz
                # w środku). Pomijamy, zamiast zgadywać pozycję.
                continue

            at = span_start + match.start()
            found.append(Mutation(
                rel, source.count("\n", 0, at) + 1, at, at + len(was), was, now, "operator"))

        for operand in operands if "prog" in kinds else ():
            if not isinstance(operand, ast.Constant):
                continue
            value = operand.value
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue

            at = char_index(source, offsets, operand.lineno, operand.col_offset)
            end = char_index(source, offsets, operand.end_lineno, operand.end_col_offset)
            text = source[at:end]
            replacement = shifted_number(value)
            if replacement == text:
                continue

            found.append(Mutation(
                rel, operand.lineno, at, end, text, replacement, "prog"))

    found.sort(key=lambda m: (m.path, m.start))
    return found


def targets() -> list[str]:
    """Moduły pod mutację: kod narzędzi, bez samych testów."""
    out = []
    for base, _dirs, files in os.walk(os.path.join(ROOT, "tools")):
        if os.sep + "tests" in base or "__pycache__" in base:
            continue
        for name in sorted(files):
            if name.endswith(".py"):
                out.append(os.path.join(base, name))
    return sorted(out)


def unreachable_modules(paths) -> dict[str, str]:
    """Moduły, których zestaw testów NIE MOŻE zaimportować, z powodem.

    Bez tego narzędzie kłamie w najbardziej mylący sposób, jaki umie. Mutacja w module,
    którego `tools/tests/test_all.py` nie potrafi wczytać, **nie ma jak zostać zabita** —
    żaden test nigdy nie wykona ani jednej jej linii. Narzędzie liczyło ją dotąd jako
    „ocalałą", czyli tak samo jak prawdziwą dziurę w pokryciu bramki.

    Zmierzone na tym repozytorium: **138 mutacji siedzi w siedmiu modułach z `import bpy`
    i 135 z nich przeżywa — 98 %**. Cała reszta, czysty Python, ma 66 %. Te 135 pozycji
    zawyżało „nieprzetestowane bramki" o jedną trzecią i kierowało triaż na moduły,
    w których żaden test nie pomoże, dopóki nie wyjdzie z nich matematyka.

    Pytanie jest zadawane WYKONANIEM, nie grepem po `import bpy`: liczy się to, czy
    import się udaje w tym środowisku, a nie która biblioteka go blokuje. Świeży runner
    bez Blendera i maszyna z Blenderem dadzą przez to różne odpowiedzi — i to jest
    poprawne, bo pytanie brzmi „czy TEN zestaw testów może to wykonać".
    """
    out = {}
    for path in sorted(set(paths)):
        module = os.path.splitext(os.path.basename(path))[0]
        probe = subprocess.run(
            [sys.executable, "-c", f"import {module}"],
            cwd=os.path.dirname(path), capture_output=True, text=True, timeout=120)
        if probe.returncode == 0:
            continue
        reason = (probe.stderr or "").strip().splitlines()
        out[path] = reason[-1] if reason else f"kod wyjścia {probe.returncode}"
    return out


#: Pamiec `collect` w OBREBIE PROCESU: (klasy, odciski wszystkich celow) -> mutacje.
#:
#: **Klucz niesie odciski, a nie sam zestaw klas, i to jest cala rzecz.** Testy tego
#: narzedzia ZMIENIAJA pliki celow w trakcie jednego procesu — robia to kontrole
#: negatywne 6.B32, 6.B39 i 6.B40 — wiec pamiec kluczowana samymi klasami
#: podstawialaby mutacje policzone dla INNEJ tresci. Bylaby to dokladnie ta usterka,
#: ktora 6.B32 zamykalo w dzienniku, tylko przeniesiona do pamieci procesu.
#:
#: **Ze klucz jest darmowy, jest ZMIERZONE**, a nie zalozone (07.09.2026, `665bd98`):
#: odczyt i sha256 wszystkich 63 celow zajmuje **0,0013 s**, a jedno `collect()` —
#: **0,224 s**. Klucz kosztuje 0,6 % tego, co oszczedza.
#:
#: Pamiec zwraca KOPIE listy, a nie ja sama: `Mutation` jest niezmienna, ale lista
#: nie, a wolajacy, ktory ja posortuje albo obetnie, zepsulby wynik nastepnemu.
_PAMIEC_COLLECT: dict[tuple, list] = {}


def collect(kinds=KINDS) -> list[Mutation]:
    """Mutacje wszystkich celow, policzone raz na (klasy, tresc) w tym procesie.

    Pomiar, ktory to uzasadnia (6.B38, 07.09.2026 na `665bd98`): modul
    `test_mutation_sweep.py` wola `collect()` **dziesiec razy**, po 0,224 s, czyli
    2,24 s z 17,34 s calego modulu. Zadne z tych wywolan nie potrzebuje swiezego
    przeliczenia — potrzebuje wyniku dla tresci, ktora w tej chwili lezy w drzewie,
    i wlasnie to jest kluczem pamieci.
    """
    klucz = (tuple(sorted(kinds)),
             tuple(sorted(odciski_przebiegu(
                 [os.path.relpath(c, ROOT) for c in targets()]).items())))
    zapamietane = _PAMIEC_COLLECT.get(klucz)
    if zapamietane is not None:
        return list(zapamietane)

    found: list[Mutation] = []
    for path in targets():
        with open(path, encoding="utf-8") as handle:
            found.extend(mutations_for(path, handle.read(), kinds))
    _PAMIEC_COLLECT[klucz] = found
    return list(found)


#: Dlugosc odcisku w dzienniku. Szesnascie znakow szesnastkowych to 64 bity — przy
#: 2346 mutacjach na przebieg szansa przypadkowej kolizji jest rzedu 10^-14, a wpis
#: dziennika zostaje czytelny. Pelne 64 znaki nie daja tu nic poza dlugoscia wiersza.
ODCISK_ZNAKOW = 16

#: Do ilu modulow raport wypisuje odciski PO JEDNYM, zamiast jednej liczby zbiorczej.
#:
#: Prog nie jest okragly z gustu, tylko WYPROWADZONY z pomiaru. Zmierzone 07.09.2026
#: na `5ae1b52`, po odsianiu prozy od komend (99 wzmianek o narzedziu w `reports/`
#: NIE jest wywolaniem — ta sama pulapka, ktora 6.A31 nazwalo dla sciezek `bin/`):
#: prawdziwych wywolan jest **66**, a **54 z nich** obejmuje DOKLADNIE JEDEN modul.
#: Bez `--only` chodzi **7** wywolan i te obejmuja wszystkie 63 cele.
#:
#: Zalozenie pozycji 6.B42 — „jezeli triaz chodzi po jednym module naraz, tabela jest
#: darmowa" — jest wiec POTWIERDZONE: w 82 % wywolan tabela ma jeden wiersz. Prog 8
#: przepuszcza kazdy zmierzony przebieg triazowy (najszerszy z zawezeniem to `sweep.py`
#: z dwoma modulami) i odsiewa te 7 pelnych, gdzie tabela zajelaby 63 wiersze.
MAX_ODCISKOW_W_RAPORCIE = 8


def odcisk_tresci(path: str) -> str:
    """SHA-256 pliku, z ktorego POLICZONO mutacje — pierwsze `ODCISK_ZNAKOW` znakow.

    **Po co, skoro wpis niesie juz `commit` (6.B19).** Bo commit nie odroznia dwoch
    przebiegow na TYM SAMYM commicie. Przy niezacommitowanej zmianie — a dokladnie
    na to jest `--dirty` — `git rev-parse --short HEAD` daje w obu przebiegach te sama
    wartosc, a tresc mutowanego pliku juz nie. Odmowa z 6.B19 tego przypadku NIE WIDZI
    i wznowienie podstawia wynik policzony dla innej tresci pod dzisiejsza mutacje,
    po cichu. 6.B19 nazwala to wprost jako to, czego nie lapie.

    **Czytane z DRZEWA ROBOCZEGO, nie z drzewa robotnika — i to jest cala rzecz.**
    `collect` liczy mutacje z drzewa roboczego (`open(path)` wzgledem `ROOT`), a
    `check_one` stosuje je na kopii `git worktree add --detach HEAD`. Te dwa zrodla sa
    tym samym plikiem dopoki drzewo jest czyste, i roznymi plikami przy `--dirty`.
    Odcisk liczony w `check_one` z kopii robotnika mialby wiec wartosc commita: bylby
    slepy dokladnie na przypadek, dla ktorego powstal.

    **Koszt, ZMIERZONY, nie zalozony.** SHA-256 raz na kazda z 2346 mutacji pelnego
    przegladu: **0,045 s**, przy przebiegu 534-600 s (6.B36) — 0,008 %. Odcisk liczony
    raz na PLIK (63 moduly) jest jeszcze tanszy, i tak jest tu zrobione. Pole „Wyjscie"
    pozycji 6.B32 kazalo wybrac miedzy tym a `git status --porcelain` (0,015 s raz na
    przebieg) na podstawie pomiaru: tansza opcja mowi tylko „drzewo brudne", a nie CO
    w nim jest, i przy tej roznicy kosztu nie ma powodu jej brac.
    """
    with open(os.path.join(ROOT, path), "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:ODCISK_ZNAKOW]


def odciski_przebiegu(paths) -> dict[str, str]:
    """Odcisk kazdego pliku przebiegu, liczony RAZ — nie raz na mutacje."""
    return {path: odcisk_tresci(path) for path in sorted(set(paths))}


def brudne_wyjasnienie(paths, dirty_flag: bool) -> str:
    """Jedno zdanie o PRAWDZIWEJ przyczynie rozjazdu odciskow, gdy nia jest brudne drzewo.

    **Zmierzone przy 6.B32, na wlasnej poprawce.** Odmowa odciskow stoi w `main` PRZED
    `dirty_sources`, bo musi dzialac takze dla `--list` (tamta odmowa jest za galezia
    `--list`). Skutek: przy brudnym drzewie BEZ `--dirty` czytajacy dostaje komunikat
    o DZIENNIKU, choc prawdziwym problemem jest jego wlasna niezacommitowana zmiana —
    a jasniejszy komunikat `dirty_sources` nie dochodzi do glosu wcale.

    Przestawienie kolejnosci nie jest rozwiazaniem: zdjeloby odmowe odciskow z drogi
    `--list`, czyli z jedynej taniej drogi, ktora ja sprawdza. Zamiast tego komunikat
    NAZYWA druga mozliwa przyczyne — i robi to tylko wtedy, gdy ona faktycznie zachodzi,
    bo zdanie dopisywane zawsze byloby szumem przy dzienniku z innego drzewa.
    """
    if dirty_flag:
        return ""
    brudne = dirty_sources(paths)
    if not brudne:
        return ""
    return ("\n  UWAGA: te pliki maja niezacommitowane zmiany, i to jest prawdopodobna "
            "przyczyna rozjazdu odciskow:\n"
            + "".join(f"    {path}\n" for path in brudne)
            + "  Zacommituj je albo uruchom z --dirty, jesli wiesz, ze robisz co innego.")


# --- które wiersze zestaw testów w ogóle wykonuje ----------------------------------


# Wstrzykiwane do KAŻDEGO procesu Pythona przebiegu przez `sitecustomize` na
# `PYTHONPATH` — tak samo, jak robi to `coverage.py`, i z tego samego powodu:
# `tools/tests/test_all.py` część testów wykonuje w podprocesach (`sys.executable`
# z argparse, bramki CI). Licznik tylko w procesie głównym uznałby wiersze pokryte
# wyłącznie przez podproces za niewykonane — a to fałsz w najgorszą stronę: kazałby
# uznać prawdziwą dziurę w pokryciu za „martwy kod, nie ma czego łatać".
TRACER = '''\
import atexit, json, os, sys, threading

_root = os.environ.get("METRO_COVER_ROOT") or ""
_out = os.environ.get("METRO_COVER_OUT") or ""
if _root and _out:
    _hits = {}

    def _local(frame, event, arg):
        if event == "line":
            _hits.setdefault(frame.f_code.co_filename, set()).add(frame.f_lineno)
        return _local

    def _global(frame, event, arg):
        # Zwrócenie None dla plików spoza `tools/` wyłącza śledzenie wierszy w całej
        # bibliotece standardowej. Bez tego przebieg puchnie kilkunastokrotnie.
        if event != "call":
            return None
        name = frame.f_code.co_filename
        if name.startswith(_root):
            _hits.setdefault(name, set()).add(frame.f_lineno)
            return _local
        return None

    def _dump():
        try:
            os.makedirs(_out, exist_ok=True)
            with open(os.path.join(_out, "%d.json" % os.getpid()), "w") as handle:
                json.dump({k: sorted(v) for k, v in _hits.items()}, handle)
        except Exception:
            pass

    atexit.register(_dump)
    threading.settrace(_global)
    sys.settrace(_global)
'''


#: Treść, którą dostaje `test_mutation_sweep.py` w drzewie roboczym. Moduł zostaje
#: na swoim miejscu, ale nie ma w nim ani jednego testu.
OWN_TESTS_STUB = '''"""Zaślepka: testy narzędzia mutacyjnego, zdjęte na czas przeglądu.

Prawdziwa treść jest w repozytorium; tutaj jej nie ma, bo mierzy narzędzie,
a nie kod pod testem. Plik ZOSTAJE, bo jego ścieżkę wymieniają raporty.

**Zaślepka musi być PEŁNOPRAWNYM modułem testowym (6.B35), nie samym docstringiem.**
Do 07.09.2026 była samym docstringiem — i od scalenia 6.D25 wywracała każdy przegląd
mutacyjny, zanim ten zdążył policzyć pierwszą mutację: bramka
`test_module_entrypoints.py` żąda od każdego `test_*.py` strażnika `__main__`
delegującego do `test_all`, więc kalibracja wyroczni widziała zestaw jako padający
w czystym drzewie i przerywała kodem 2. Stąd jeden test niżej i strażnik na końcu:
`test_all.main(<plik>)` odmawia przy zerze testów, a `assertion_gate` przy teście bez
asercji, więc pełnoprawny moduł to docstring, test i strażnik — wszystkie trzy.
"""


def test_this_file_is_the_stub_not_the_real_tests():
    """Jedyny test zaślepki: mówi, czym ten plik jest.

    Nie jest to test narzędzia — narzędzia się tu nie mierzy, bo to ono jest tym,
    co mierzy. Jest to test TOŻSAMOŚCI pliku: czytający drzewo robocze przeglądu
    (a także `test_all.py`, który je przebiega) ma dostać jednoznaczną odpowiedź,
    że prawdziwe testy zostały zdjęte świadomie, a nie zginęły.
    """
    assert __doc__ is not None, "zaślepka bez docstringu nie mówi, czym jest"
    assert "Zaślepka" in __doc__, "docstring nie nazywa tego pliku zaślepką"


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
'''


def neutralise_own_tests(root: str) -> str | None:
    """Zdejmuje testy narzędzia z drzewa `root`, NIE kasując pliku.

    **Dlaczego nie `os.remove`.** Do 05.09.2026 ta funkcja plik kasowała, i to
    działało dopóty, dopóki nikt nie patrzył na drzewo jako całość. `809e6f1` dodał
    bramkę `test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie`, która
    sprawdza, czy każda ścieżka wymieniona w `reports/` rozwiązuje się w drzewie —
    a `reports/mutation-drift.md` i `reports/mutation-sweep.md` wymieniają właśnie
    `tools/tests/test_mutation_sweep.py`, cztery razy. Od tamtego commita zestaw padał
    w KAŻDYM drzewie roboczym, bez żadnej mutacji, więc każda mutacja była zapisywana
    jako ZABITA. Pomiar z 05.09.2026 na `8c3f752`: `m7_report.py` dał „31/31 zabitych,
    0 ocalałych", podczas gdy ręczne wstawienie mutacji z wiersza 46 zostawia zestaw
    zielonym — mutacja przeżywa.

    Narzędzie skłamało w tę samą stronę co przy OOM w wersji z 02.09.2026: zawyżyło
    pokrycie. Zaślepka zdejmuje testy tak samo skutecznie, a ścieżkę zostawia.
    """
    own = os.path.join(root, "tools", "tests", "test_mutation_sweep.py")
    if not os.path.isfile(own):
        return None
    with open(own, "w", encoding="utf-8") as handle:
        handle.write(OWN_TESTS_STUB)
    return own


def add_worktree(path: str) -> None:
    """Kopia `HEAD` w podanym miejscu, bez testów samego narzędzia.

    Testy `test_mutation_sweep.py` mierzą narzędzie, nie kod pod testem, a przy tym
    dominują czas przebiegu. Muszą znikać TAK SAMO w drzewie robotnika i w drzewie
    sondy pokrycia — inaczej sonda zaliczyłaby jako „wykonane" wiersze, których
    prawdziwy przebieg mutacji już nie dotyka.
    """
    subprocess.run(["git", "worktree", "add", "--detach", "--quiet", path, "HEAD"],
                   cwd=ROOT, check=True, capture_output=True)
    neutralise_own_tests(path)


def coverage_map(out_dir: str, timeout: int) -> dict[str, set[int]] | None:
    """Wiersze modułów `tools/`, które zestaw testów NAPRAWDĘ wykonuje.

    **Po co.** Mutacja przypisania albo argumentu wywołania trafia często w kod,
    do którego wykonanie nigdy nie dochodzi: gałąź `if __name__ == "__main__"`,
    obsługa błędu, wariant CLI. Taka mutacja przeżywa, bo nikt jej nie odpalił —
    i policzona razem z mutacją, która przeżyła MIMO odpalenia, zamienia raport
    o pokryciu w raport o niczym. Ta sonda rozdziela te dwie rzeczy pomiarem.

    **Czego NIE mierzy.** Wykonanie WIERSZA, nie wykonanie zmutowanego podwyrażenia.
    W `a and b` wiersz bywa wykonany, a `b` nigdy nie policzone. „Wykonana" jest więc
    ograniczeniem z góry, a „niewykonana" — twarde: skoro wiersz nie ruszył ani razu,
    mutant nie miał jak zostać zaobserwowany. Nierówność idzie w bezpieczną stronę:
    zawyża liczbę prawdziwych dziur, nie zaniża.

    Zwraca `None`, gdy przebieg sondy nie doszedł do końca — wtedy przebieg mutacji
    idzie dalej, a raport mówi „niezmierzone" zamiast zgadywać.
    """
    worktree = os.path.join(out_dir, "wtcov")
    site = os.path.join(out_dir, "cov")
    hits = os.path.join(out_dir, "hits")
    os.makedirs(site, exist_ok=True)
    os.makedirs(hits, exist_ok=True)
    with open(os.path.join(site, "sitecustomize.py"), "w", encoding="utf-8") as handle:
        handle.write(TRACER)

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([site] + ([env["PYTHONPATH"]]
                                                  if env.get("PYTHONPATH") else []))
    env["METRO_COVER_ROOT"] = os.path.join(worktree, "tools") + os.sep
    env["METRO_COVER_OUT"] = hits

    add_worktree(worktree)
    try:
        done = subprocess.run(
            [sys.executable, os.path.join(worktree, "tools", "tests", "test_all.py")],
            cwd=worktree, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return None
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", worktree],
                       cwd=ROOT, capture_output=True)

    if SUMMARY.search(done.stdout) is None:
        return None

    out: dict[str, set[int]] = {}
    for name in sorted(os.listdir(hits)):
        try:
            with open(os.path.join(hits, name), encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        for path, lines in data.items():
            out.setdefault(os.path.relpath(path, worktree), set()).update(lines)
    return out


#: Wersja kształtu zapamiętanej mapy pokrycia. Plik o innej wersji jest ODRZUCANY,
#: nie czytany „na tyle, na ile się da": mapa przeczytana źle daje etykietę
#: „nieodpalona" mutacji, która się odpaliła — czyli kłamstwo w stronę „jest dziura
#: w bramce", i to takie, którego nic w wyniku nie zdradza.
POKRYCIE_WERSJA = 1


def pokrycie_w_celach(mapa: dict[str, set[int]]) -> dict[str, set[int]]:
    """Mapa pokrycia obcięta do plików, które są CELAMI mutacji.

    **Po co obcinać, skoro nadmiar nie przeszkadza.** Przeszkadza dwojako, i oba
    powody są ZMIERZONE, nie przewidziane (07.09.2026, `reports/pamiec-pokrycia.md`):

    1. **Mapa bez obcięcia nie jest stabilna między przebiegami na TYM SAMYM
       commicie.** Dwie sondy z tego samego drzewa dały 162 klucze każda i te same
       25 732 wiersze, ale **różne zbiory kluczy**: różnica to piaskownice, które
       zestaw zakłada sam — `tools/tests/test_dwa_<losowe>/test_dwa_testy.py`
       i `tools/tests/test_pusty_<losowe>/test_bez_zadnego_testu.py` (bramka 6.D25).
       Losowy przyrostek zmienia się co przebieg. W ANI JEDNYM module wspólnym dla
       obu map zbiory wierszy się nie różniły — niestabilne były wyłącznie te
       efemeryczne ścieżki. Bez obcięcia każdy test porównujący mapę zapamiętaną
       z policzoną od nowa byłby więc chwiejny, i to nie z winy pokrycia.
    2. **Nadmiar jest większy od treści.** Z 162 kluczy celami mutacji jest **57**
       (celów jest 63, sześciu zestaw nie uruchamia wcale), a z 25 732 wierszy
       w celach leży **7 582**. Sto pięć kluczy to `tools/tests/` — zestaw
       obserwujący sam siebie.

    **Obcięcie nie zmienia ani jednego werdyktu**, bo `was_executed` pyta wyłącznie
    o `mutation.path`, a ten jest zawsze celem. To jest jedyny czytnik tej mapy.
    """
    cele = {os.path.relpath(path, ROOT) for path in targets()}
    return {path: lines for path, lines in mapa.items() if path in cele}


def sciezka_pokrycia(commit: str) -> str:
    """Gdzie stoi zapamiętana mapa dla tego commita.

    Obok dziennika, w katalogu tymczasowym — nie w repozytorium: mapa jest
    pochodną drzewa, nie jego treścią, a `git clean -ffdx` z checkoutu CI i tak by
    ją zdjął przy każdym przebiegu (`docs/CLAUDE.md`, punkt o narzędziach poza
    workspace). Commit w nazwie z tego samego powodu, z którego ma go
    `default_journal`: dwie rewizje mierzą co innego.
    """
    return os.path.join(tempfile.gettempdir(), f"metro-pokrycie-{commit}.json")


def zapisz_pokrycie(path: str, commit: str, mapa: dict[str, set[int]]) -> None:
    """Mapa na dysk, z commitem WEWNĄTRZ pliku, nie tylko w nazwie.

    Nazwa da się zmienić jednym `mv`, a wtedy mapa z innego drzewa weszłaby jako
    swoja. Ta sama zasada, którą 6.B19 postawiła dla wpisu dziennika i 6.B32 dla
    odcisku treści: dowód pochodzenia jedzie razem z danymi.
    """
    dane = {
        "wersja": POKRYCIE_WERSJA,
        "commit": commit,
        "pokrycie": {plik: sorted(wiersze) for plik, wiersze in sorted(mapa.items())},
    }
    tymczasowy = path + ".czesciowy"
    with open(tymczasowy, "w", encoding="utf-8") as handle:
        json.dump(dane, handle)
    # Podmiana atomowa: przebieg ubity w połowie zapisu nie zostawia pliku, który
    # da się przeczytać do połowy. `read_journal` radzi sobie z uciętym wierszem,
    # bo dziennik jest linia-na-wpis; mapa jest jednym obiektem JSON i ucięta
    # byłaby nieczytelna — albo, gorzej, czytelna i niepełna.
    os.replace(tymczasowy, path)


def wczytaj_pokrycie(path: str, commit: str) -> dict[str, set[int]] | None:
    """Zapamiętana mapa dla TEGO commita albo `None`.

    Odrzuca — nie naprawia — plik z innego commita, z inną wersją kształtu i plik
    nieczytelny. Powód jest ten sam, dla którego 6.B19 odrzuca wpis dziennika
    z innego drzewa: mapa z innego kodu przypisze etykietę „nieodpalona" mutacji,
    która się odpaliła, i nic w wyniku tego nie zdradzi.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            dane = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(dane, dict):
        return None
    if dane.get("wersja") != POKRYCIE_WERSJA:
        return None
    if dane.get("commit") != commit:
        return None
    pokrycie = dane.get("pokrycie")
    if not isinstance(pokrycie, dict):
        return None
    return {plik: set(wiersze) for plik, wiersze in pokrycie.items()}


def was_executed(coverage, mutation: Mutation) -> bool | None:
    """Czy wiersz tej mutacji wykonał się w przebiegu bez mutacji."""
    if coverage is None:
        return None
    return mutation.line in coverage.get(mutation.path, ())


# --- uruchamianie -----------------------------------------------------------------


# Zestaw kończy się linią „  N/M przeszło". Jej BRAK znaczy, że przebieg nie doszedł
# do końca — a to co innego niż „testy wykryły mutację".
SUMMARY = re.compile(r"^\s*(\d+)/(\d+) przeszło\s*$", re.MULTILINE)


def run_suite(worktree: str, timeout: int) -> tuple[bool | None, list[str], int | None]:
    """Zestaw testów w podanym drzewie.

    Zwraca `(werdykt, nazwy tych, co padły)`, gdzie werdykt to `True` (przeszedł,
    czyli mutacja PRZEŻYŁA), `False` (testy ją złapały) albo **`None` —
    nierozstrzygnięte**.

    Trzeci stan nie jest ozdobnikiem. Pierwszy przebieg tego narzędzia (02.09.2026)
    leciał, gdy kontener dławił się pamięcią; `test_all.py` bywał ubijany przez OOM,
    zwracał kod różny od zera i był czytany jako „test wykrył mutację". Kontrola
    wykazała, że **16 z 20 tak zaliczonych zabić** to w rzeczywistości mutacje ocalałe.
    Narzędzie do mierzenia pokrycia ZAWYŻAŁO pokrycie — kłamało w tę stronę, w którą
    najłatwiej uwierzyć.

    Dowodem, że przebieg doszedł do końca, jest linia podsumowania. Bez niej wynik
    jest nieznany i tak trafia do raportu, zamiast udawać zabicie.
    """
    try:
        done = subprocess.run(
            [sys.executable, os.path.join(worktree, "tools", "tests", "test_all.py")],
            cwd=worktree, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, ["<przekroczony czas>"], None

    summary = SUMMARY.search(done.stdout)
    if summary is None:
        # Zestaw nie wypisał podsumowania. Zapisujemy KOD WYJŚCIA, bo to jedyna rzecz,
        # która odróżnia przyczyny: ujemny kod albo 137/143 znaczy zabicie sygnałem
        # (najczęściej OOM), czyli coś, co z mutacją nie ma związku.
        #
        # Pierwsza wersja zapisywała tu ostatnią linię stderr jako „powód" i było to
        # mylące: zestaw NORMALNIE wypisuje na stderr błędy argparse z testów, które
        # sprawdzają, czy narzędzia odrzucają złe argumenty. Ostatnia linia stderr
        # opisywała więc test negatywny, a nie awarię.
        # Kod ujemny albo 137/143 znaczy zabicie sygnałem — najczęściej OOM. To jedyna
        # przyczyna, która NIE mówi nic o mutacji, więc tylko ona daje „nierozstrzygnięte".
        #
        # Każdy inny kod jest skutkiem mutacji i liczy się jako WYKRYCIE. Kod 2 to
        # `SystemExit` z argparse, które wychodzi poza `test_all.py`: zmutowany moduł
        # woła `parse_args()` w miejscu, w którym nie powinien, a zestaw ginie podczas
        # odkrywania testów. Sprawdzone na trzech mutacjach po dwa przebiegi — kod 2
        # za każdym razem. W CI taki przebieg jest czerwony, czyli mutacja jest złapana.
        if done.returncode < 0 or done.returncode in (137, 143):
            return None, [f"<zabity sygnałem, kod {done.returncode}>"], done.returncode
        return False, [f"<zestaw zginął przed podsumowaniem, kod {done.returncode}>"], done.returncode

    failed = re.findall(r"^\s*FAIL (\S+)", done.stdout, re.MULTILINE)
    passed, total = int(summary.group(1)), int(summary.group(2))
    if passed == total and done.returncode == 0:
        return True, failed, done.returncode
    return False, failed, done.returncode


def baseline_problem(worktree: str, timeout: int, run=run_suite) -> str | None:
    """Czy drzewo BEZ mutacji przechodzi zestaw. `None` znaczy „tak".

    **Po co osobny przebieg.** Wyrocznia tego narzędzia brzmi „zestaw padł, czyli
    mutacja została wykryta". Zdanie jest prawdziwe wyłącznie wtedy, gdy zestaw
    NIE PADA bez mutacji. Gdy przestaje, narzędzie melduje 100 % zabić i nie ma
    w wyniku niczego, co by to zdradziło: sto procent wygląda jak sukces.

    Zdarzyło się to dwa razy z dwóch różnych przyczyn — 02.09.2026 zestaw ubijał OOM,
    05.09.2026 drzewo robocze łamała własna przygotowawcza kasacja pliku (patrz
    `neutralise_own_tests`). Za pierwszym razem obroną był kod wyjścia, za drugim
    nie było żadnej. Ta funkcja jest obroną niezależną od przyczyny: mierzy dokładnie
    to założenie, na którym stoi każdy wiersz dziennika.

    Kosztuje jeden przebieg zestawu na cały przegląd — przy 31 mutacjach 3 %, przy
    600 poniżej dwóch promili.
    """
    passed, failed, code = run(worktree, timeout)
    if passed is True:
        return None
    if passed is None:
        return (f"zestaw w czystym drzewie nie doszedł do podsumowania (kod {code}): "
                f"{failed}")
    return (f"zestaw PADA w czystym drzewie, bez żadnej mutacji (kod {code}): {failed} "
            "— dopóki tak jest, każda mutacja zostanie zapisana jako zabita, "
            "a przegląd nie mierzy niczego")


def check_one(worktree: str, mutation: Mutation, timeout: int, commit: str,
              executed: bool | None = None, odcisk: str | None = None) -> dict:
    """Jedna mutacja w jednym drzewie roboczym, z przywróceniem pliku.

    `commit` idzie do wpisu dziennika obok `id`, bo `id` sam w sobie NIE mówi,
    z jakiego drzewa pochodzi — to `plik:wiersz:przesunięcie bajtowe`, a dwie różne
    mutacje z dwóch różnych drzew mogą wypaść pod tym samym przesunięciem (6.B19).
    Bez tego pola wznowienie z dziennika zapisanego na innym commicie podstawiłoby
    cudzy wynik pod dzisiejszą mutację po cichu.
    """
    path = os.path.join(worktree, mutation.path)
    with open(path, encoding="utf-8") as handle:
        original = handle.read()

    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(mutation.apply(original))
        passed, failed, code = run_suite(worktree, timeout)
    finally:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(original)

    return {
        "id": mutation.id,
        "commit": commit,
        # 6.B32: odcisk tresci pliku, z ktorego POLICZONO te mutacje. `commit` nie
        # odroznia dwoch przebiegow na tym samym commicie, a `--dirty` jest po to,
        # zeby takie przebiegi robic.
        "odcisk": odcisk,
        "rozstrzygniete": passed is not None,
        "kod": code,
        "opis": mutation.describe(),
        "plik": mutation.path,
        "wiersz": mutation.line,
        "rodzaj": mutation.kind,
        "bylo": mutation.was,
        "jest": mutation.now,
        # `True`/`False` z sondy pokrycia, `None` gdy sonda nie doszła do skutku.
        # Ocalała z `False` przeżyła, bo nikt jej nie uruchomił — to NIE jest to samo
        # co dziura w bramce i raport nie ma prawa liczyć tego razem.
        "wykonana": executed,
        "przezyla": bool(passed),
        "padly": failed[:5],
        "ile_padlo": len(failed),
    }


def worker(slot: int, chunk: list[Mutation], timeout: int, out_dir: str,
           journal: str, commit: str, coverage=None, odciski=None) -> int:
    """Jeden robotnik na własnym drzewie roboczym git.

    Wynik KAŻDEJ mutacji leci od razu do dziennika, wiersz po wierszu. Pierwsza wersja
    zapisywała dopiero po całej porcji — i gdy przebieg padł po siedemdziesięciu
    minutach, nie zostało ani jedno z ponad sześciuset sprawdzeń. Przebieg trwający
    godzinę musi znosić śmierć procesu, bo jej doświadczy.
    """
    # Testy SAMEGO narzędzia lecą z drzewa roboczego (`add_worktree`). Mierzą
    # narzędzie, nie kod pod testem, a przy tym dominują czas:
    # `test_every_mutation_still_parses` parsuje wszystkie mutacje w KAŻDYM z setek
    # przebiegów. Zostawione podniosły koszt przeglądu z 66 do 120 minut, nie mówiąc
    # przy tym nic o pokryciu bramek.
    worktree = os.path.join(out_dir, f"wt{slot}")
    add_worktree(worktree)

    done = 0
    try:
        for mutation in chunk:
            entry = check_one(worktree, mutation, timeout, commit,
                              was_executed(coverage, mutation),
                              (odciski or {}).get(mutation.path))
            with JOURNAL_LOCK:
                with open(journal, "a", encoding="utf-8") as handle:
                    handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
            done += 1
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", worktree],
                       cwd=ROOT, capture_output=True)
    return done


def odcisk_przebiegu(odciski: dict) -> str:
    """Jeden odcisk CALEGO przebiegu, zlozony z odciskow jego plikow.

    Osobna funkcja, a nie wyrazenie w `default_journal`, bo tej wartosci pyta sie
    dwoch rozmowcow: nazwa dziennika (6.B40) i — po scaleniu — naglowek raportu
    (6.B42). Dwa niezalezne skladania tej samej listy rozjechalyby sie po cichu,
    i to jest ta sama zasada, dla ktorej `przyczyna_pustego_zbioru` jest jedna
    (6.B28, 6.B41).

    Pusty przebieg ma odcisk pusty, nie odcisk pustego napisu: nazwa dziennika dla
    zbioru bez plikow nie ma czego odrozniac, a `sha256("")` jest wartoscia, ktora
    wygladalaby jak zmierzona.
    """
    if not odciski:
        return ""
    material = "|".join(f"{path}:{odcisk}" for path, odcisk in sorted(odciski.items()))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:ODCISK_ZNAKOW]


def default_journal(commit: str, kinds: tuple, only: str,
                    odcisk: str = "") -> str:
    """Domyślna ścieżka dziennika — JEDNA NA PRZEBIEG, nie jedna na maszynę.

    **Co było nie tak.** Do 06.09.2026 domyślną ścieżką było
    `tempfile.gettempdir()/metro-mutacje.jsonl` — ta sama dla wszystkiego, co się
    na tej maszynie uruchomi. A wynik przebiegu czytany jest z CAŁEGO dziennika
    (`sweep`, wiersz z `read_journal`), więc dwa przeglądy naraz nie tyle sobie
    przeszkadzały, co **mieszały wyniki**: raport przebiegu na jednym module
    dostawał sekcję modułu, którego ten przebieg w ogóle nie dotykał.

    Zmierzone 06.09.2026 wykonaną kontrolą: dziennik z jednym wpisem obcego modułu
    daje raport zawierający `### tools/track/detail_layout.py — 1`, choć przebieg
    dotyczył wyłącznie `lod_paths.py`. Znalezione przy 6.B14, gdzie dwa agenty
    liczyły równolegle na jednej maszynie.

    **Dlaczego nazwa zawiera właśnie to.** Commit, klasy operatorów, zawężenie
    `--only` i — od 6.B40 — **odcisk treści przebiegu** to cztery rzeczy, które
    rozstrzygają, CZEGO przebieg dotyczy. Dwa przebiegi różniące się którąkolwiek
    z nich mierzą co innego i nie mają prawa dzielić pliku; dwa przebiegi zgodne we
    wszystkich czterech to ten sam pomiar, więc wznowienie ma je znaleźć.

    **Czwarty składnik jest tu dlatego, że trzy przestały wystarczać** — i to nie
    domysł, a skutek 6.B32. Odcisk treści wszedł wtedy do WPISU dziennika i odmowa
    zaczęła poprawnie odrzucać cudzą treść; nazwa pliku pozostała jednak funkcją
    trzech rzeczy, więc dwa przebiegi na tym samym commicie i różnej treści
    **dzieliły ścieżkę** i drugi z nich kończył się odmową zamiast pomiaru.
    Zmierzone 07.09.2026 przy 6.B32::

        czyste: /tmp/metro-mutacje-58804969c2a4.jsonl
        brudne: /tmp/metro-mutacje-58804969c2a4.jsonl     <- ta sama nazwa
        odcisk: 4e495be9c4159f96                          <- inna tresc

    Docstring obiecywał wtedy „trzy rzeczy, które rozstrzygają, CZEGO przebieg
    dotyczy", a rozstrzygały już cztery. Ta rozbieżność między obietnicą funkcji
    i jej działaniem była właściwą treścią pozycji 6.B40 — odmowa z 6.B32 działa
    i zostaje niezależnie od nazwy.

    **Czego to NIE zmienia.** Wznowienie na treści niezmienionej trafia w ten sam
    plik, bo odcisk jest wtedy ten sam; przebieg po zacommitowaniu zmiany nadal nie
    znajdzie dziennika sprzed commita, bo różni się już samym commitem.
    """
    znacznik = hashlib.sha256(
        "|".join([commit, ",".join(sorted(kinds)), only or "", odcisk]).encode("utf-8")
    ).hexdigest()[:12]
    return os.path.join(tempfile.gettempdir(), f"metro-mutacje-{znacznik}.jsonl")


def read_journal(path: str) -> list[dict]:
    """Wyniki z dziennika; wiersz ucięty w połowie zapisu jest pomijany."""
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def sweep(mutations: list[Mutation], workers: int, timeout: int, out_dir: str,
          journal: str, commit: str, coverage=None, odciski=None) -> list[dict]:
    os.makedirs(out_dir, exist_ok=True)
    chunks: list[list[Mutation]] = [[] for _ in range(workers)]
    for index, mutation in enumerate(mutations):
        chunks[index % workers].append(mutation)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, slot, chunk, timeout, out_dir, journal, commit,
                               coverage, odciski)
                   for slot, chunk in enumerate(chunks) if chunk]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    results = read_journal(journal)
    results.sort(key=lambda r: (r["plik"], r["wiersz"]))
    return results


def naglowek_odciskow(odciski: dict) -> list[str]:
    """Wiersze naglowka raportu, ktore mowia, Z JAKIEJ TRESCI powstaly liczby.

    **Po co, skoro naglowek podaje commit (6.D3).** Bo commit nie odroznia dwoch
    przebiegow na tym samym commicie — to jest dokladnie to, co zmierzylo 6.B32
    dla dziennika, a nastepnie 6.B40 dla nazwy pliku. Raport z przebiegu `--dirty`
    byl do 07.09.2026 nieodroznialny od raportu z drzewa czystego, choc liczby
    dotyczyly innej tresci.

    **Jeden odcisk zbiorczy ORAZ tabela, a nie jedno z dwojga** — i to rozstrzygnal
    pomiar, nie wygoda. Odcisk zbiorczy jest krotki i zawsze obecny, ale nie mowi,
    ktory modul sie roznil; tabela mowi, ale przy 63 celach zajmuje ekran. Zmierzone
    07.09.2026: **54 z 66** wywolan w `reports/` obejmuje jeden modul, wiec tabela
    kosztuje w nich JEDEN wiersz. Powyzej `MAX_ODCISKOW_W_RAPORCIE` zostaje sam
    odcisk zbiorczy i zdanie o tym, ile modulow pominieto — nie milczenie.

    Odcisk zbiorczy bierze `odcisk_przebiegu` (6.B40), a nie wlasne skladanie tej
    samej listy: dwa czytniki jednej rzeczy rozjezdzaja sie po cichu (6.B28).
    """
    if not odciski:
        return ["**Odcisk treści przebiegu:** brak — przebieg nie objął ani jednego pliku"]

    zbiorczy = odcisk_przebiegu(odciski)
    out = [f"**Odcisk treści przebiegu:** `{zbiorczy}` "
           f"({len(odciski)} moduł(ów))"]
    if len(odciski) <= MAX_ODCISKOW_W_RAPORCIE:
        out += ["", "| moduł | odcisk treści |", "|---|---|"]
        out += [f"| `{path}` | `{odcisk}` |" for path, odcisk in sorted(odciski.items())]
    else:
        out += ["",
                f"Odciski poszczególnych modułów pominięte: przebieg objął "
                f"{len(odciski)} modułów, a tabela wypisuje je do "
                f"{MAX_ODCISKOW_W_RAPORCIE}. Odcisk zbiorczy wyżej zależy od "
                f"każdego z nich, więc zmiana dowolnego jest w nim widoczna — "
                f"nie widać tylko, KTÓREGO."]
    return out


def report(results: list[dict], commit: str, odciski: dict | None = None) -> str:
    # Starsze dzienniki nie mają pola `rozstrzygniete`; brak pola traktujemy jako
    # „rozstrzygnięte", żeby raport z nich nadal się składał.
    unknown = [r for r in results if not r.get("rozstrzygniete", True)]
    decided = [r for r in results if r.get("rozstrzygniete", True)]
    survived = [r for r in decided if r["przezyla"]]
    killed = len(decided) - len(survived)

    # Trzy kupki ocalałych, bo to trzy różne zdania o kodzie. Starsze dzienniki nie
    # mają pola `wykonana` — brak pola to „niezmierzone", nie „wykonana".
    hot = [r for r in survived if r.get("wykonana") is True]
    cold = [r for r in survived if r.get("wykonana") is False]
    untested = [r for r in survived if r.get("wykonana") is None]
    ran = killed + len(hot)

    # Nierozstrzygnięta z PRZEKROCZONEGO CZASU i nierozstrzygnięta z zabicia sygnałem
    # to dwa różne zdania. Pierwsza mówi o mutancie: zestaw się zapętlił, czyli zmiana
    # jest obserwowalna, tylko nie w postaci, którą ta wyrocznia umie odczytać. Druga
    # mówi o maszynie — OOM, ubity proces — i o mutancie nie mówi nic. Podane jedną
    # liczbą wyglądają tak samo i obie czyta się jako awarię narzędzia.
    timeouts = [r for r in unknown
                if any("czas" in str(x) for x in r.get("padly", []))]
    killed_off = [r for r in unknown if r not in timeouts]

    by_kind: dict[str, list[int]] = {}
    for entry in decided:
        row = by_kind.setdefault(entry.get("rodzaj", "?"), [0, 0, 0, 0])
        row[0] += 1
        if not entry["przezyla"]:
            row[1] += 1
        elif entry.get("wykonana") is False:
            row[3] += 1
        else:
            row[2] += 1

    lines = [
        "# Przegląd mutacyjny bramek",
        "",
        f"**Snapshot na commicie:** `{commit}`",
        "",
        *naglowek_odciskow(odciski or {}),
        "",
        "Narzędzie: `tools/tests/mutation_sweep.py`. Mutowany jest **kod pod testem**,",
        "nie testy. Mutacja, która przeżyła, znaczy jedno z dwojga: brak pokrycia albo",
        "mutant równoważny — zmiana, której nie da się zaobserwować. Narzędzie nie zgaduje,",
        "które to; każdą trzeba obejrzeć.",
        "",
        "## Wynik",
        "",
        "| | |",
        "|---|---|",
        f"| mutacji | {len(results)} |",
        f"| rozstrzygniętych | {len(decided)} |",
        f"| zabitych | {killed} |",
        f"| **ocalałych mimo wykonania** | **{len(hot)}** |",
        f"| ocalałych nieuruchomionych | {len(cold)} |",
        f"| ocalałych o niezmierzonym wykonaniu | {len(untested)} |",
        f"| **nierozstrzygniętych** | **{len(unknown)}** |",
        f"| — z przekroczonego czasu | {len(timeouts)} |",
        f"| — z awarii poza mutacją | {len(killed_off)} |",
        ("| pokrycie (z rozstrzygniętych) | "
         f"{killed / len(decided) * 100:.1f} % |") if decided else "| pokrycie | — |",
        (f"| **pokrycie kodu wykonanego** | **{killed / ran * 100:.1f} %** |")
        if ran else "| pokrycie kodu wykonanego | — |",
        "",
        "**Nierozstrzygnięta** znaczy, że przebieg testów nie doszedł do końca —",
        "zapętlony, ubity, bez pamięci. Taki wynik NIE liczy się jako zabicie.",
        "Pierwsza wersja tego narzędzia liczyła go właśnie tak i przez to zawyżała",
        'pokrycie: kontrola wykazała, że 16 z 20 „zabić” z przebiegu pod presją pamięci',
        "to w rzeczywistości mutacje ocalałe.",
        "",
        "Rozbicie nierozstrzygniętych na dwa wiersze nie jest ozdobą. **Przekroczony",
        "czas** znaczy, że zestaw się zapętlił — czyli mutant JEST obserwowalny, tylko",
        "nie w postaci, którą ta wyrocznia umie odczytać, bo jej dowodem jest linia",
        "podsumowania, a pętla nieskończona jej nie wypisze. **Awaria poza mutacją**",
        "(sygnał, OOM) nie mówi o mutancie nic. Podane jedną liczbą czyta się je tak samo",
        "i obie wyglądają na awarię narzędzia.",
        "",
        "**Nieuruchomiona** to co innego. Mutacja siedzi w wierszu, którego zestaw testów",
        "nie wykonuje ani razu — w gałęzi `if __name__ == \"__main__\"`, w obsłudze błędu,",
        "w wariancie CLI. Przeżyła nie dlatego, że bramka nie bramkuje, tylko dlatego,",
        "że nikt jej nie odpalił. Wpisanie jej do jednego worka z ocalałą **mimo**",
        "wykonania zamienia raport o pokryciu w raport o rozmiarze repozytorium.",
        "Pomiar robi jeden przebieg zestawu z licznikiem wierszy przed mutowaniem",
        "(`coverage_map`); mierzy wykonanie WIERSZA, więc „nieuruchomiona\" jest twarda,",
        "a „wykonana\" jest ograniczeniem z góry.",
        "",
        "## Per klasa mutacji",
        "",
        "| klasa | rozstrzygniętych | zabitych | ocalałych bez nieuruchomionych "
        "| nieuruchomionych |",
        "|---|---:|---:|---:|---:|",
    ]
    for kind in sorted(by_kind):
        total, dead, alive, frozen = by_kind[kind]
        lines.append(f"| `{kind}` | {total} | {dead} | {alive} | {frozen} |")
    lines.append("")

    if unknown:
        lines += ["## Nierozstrzygnięte, z powodem", "",
                  "| mutacja | powód | kod wyjścia |", "|---|---|---|"]
        for entry in unknown:
            why = (entry.get("padly") or ["<bez powodu w dzienniku>"])[0]
            lines.append(f"| {entry.get('opis', entry.get('id', '?'))} | {why} "
                         f"| {entry.get('kod')} |")
        lines.append("")

    if not survived:
        lines += ["Żadna mutacja nie przeżyła.", ""]
        return "\n".join(lines)

    lines += [
        "## Jak czytać ocalałe",
        "",
        "Ocalała mutacja **nie jest** automatycznie usterką. Trzeba ją zakwalifikować",
        "do jednej z czterech klas; pierwszą narzędzie rozstrzyga pomiarem, trzy",
        "pozostałe zostają czytającemu:",
        "",
        "| klasa | co znaczy | co z tym zrobić |",
        "|---|---|---|",
        "| **kod nieuruchomiony** | wiersz nie wykonał się ani razu — mierzone, "
        "nie zgadywane | osobna sekcja niżej; nie liczy się do pokrycia kodu wykonanego |",
        "| **realna dziura** | zmiana zmienia zachowanie, które ktoś kiedyś zobaczy, "
        "a żaden test tego nie sprawdza | dopisać test z kontrolą negatywną |",
        "| **mutant równoważny** | zmiany nie da się zaobserwować (np. tolerancja "
        "`1e-12` przesunięta o procent) | zapisać jako równoważną, nie „naprawiać” |",
        "| **remis bez znaczenia** | `<` kontra `<=` przy wyborze minimum: przy remisie "
        "obie gałęzie dają tę samą wartość | jak wyżej, chyba że liczy się INDEKS |",
        "",
        "Rozróżnienie wymaga przeczytania kodu. Wpisanie mutanta równoważnego jako",
        "usterki zawyża znalezisko dokładnie tak samo, jak liczenie zepsutego przebiegu",
        "jako zabicia zawyżało pokrycie.",
        "",
        "**Kolejność triażu:** od pliku o najwyższym UDZIALE ocalałych, nie od pliku",
        "o największej ich liczbie. Wysoki udział znaczy, że testy tego modułu sprawdzają",
        "co innego, niż deklarują; duża liczba przy niskim udziale znaczy tylko, że moduł",
        "jest duży.",
        "",
    ]

    for title, bucket, note in (
        ("Ocalałe MIMO wykonania, per plik", hot,
         "Wiersz wykonał się w przebiegu bez mutacji, a mutacja i tak przeżyła. "
         "To tutaj są dziury w bramkach."),
        ("Ocalałe, których żaden test nie uruchomił", cold,
         "Wiersz nie wykonał się ani razu. Testu nie da się tu „dopisać do bramki” — "
         "trzeba najpierw doprowadzić wykonanie do tego kodu albo uznać go za martwy."),
        ("Ocalałe o niezmierzonym wykonaniu", untested,
         "Sonda pokrycia nie doszła do skutku albo dziennik jest starszy niż ona. "
         "Nie wiadomo, do której z dwóch grup wyżej należą."),
    ):
        if not bucket:
            continue
        by_file: dict[str, list[dict]] = {}
        for entry in bucket:
            by_file.setdefault(entry["plik"], []).append(entry)
        lines += [f"## {title} — {len(bucket)}", "", note, ""]
        for path in sorted(by_file):
            lines += [f"### `{path}` — {len(by_file[path])}", "",
                      "| wiersz | rodzaj | było | jest |", "|---|---|---|---|"]
            for entry in by_file[path]:
                lines.append(f"| {entry['wiersz']} | {entry['rodzaj']} | "
                             f"`{entry['bylo']}` | `{entry['jest']}` |")
            lines.append("")

    return "\n".join(lines)


def dirty_sources(paths) -> list[str]:
    """Które z podanych plików różnią się między drzewem roboczym a `HEAD`.

    Istnieje po to, żeby przebieg przerwał się w pierwszej sekundzie, a nie w piętnastej
    minucie. Mutacje powstają z pliku w DRZEWIE ROBOCZYM — z jego przesunięciami bajtowymi
    — a wykonywane są w kopii z `HEAD` (`run_worker`). Gdy plik jest zmieniony i
    niezacommitowany, te dwa źródła to dwa różne pliki i mutacja trafia w inne miejsce,
    niż myśli.

    Zdarzyło się przy triażu `lod.py`: dopisany komentarz przesunął ofsety i przebieg padł
    po 88 mutacjach na `AssertionError` mówiącym, że „w pliku stoi 'ł', oczekiwano '<'".
    Strażnik wklejki zadziałał — nikt nie policzył złych wyników — ale kosztowało to
    piętnaście minut maszyny i minutę zastanawiania się, skąd tam polska litera.

    Pyta o KONKRETNE mutowane pliki, a nie o czystość całego repozytorium: dopisywanie
    testów w tej samej sesji jest normalne i nie ma powodu, żeby blokowało przegląd.
    """
    wanted = sorted(set(paths))
    if not wanted:
        return []
    changed = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--"] + wanted,
        cwd=ROOT, capture_output=True, text=True)
    if changed.returncode != 0:
        return []
    return [line for line in changed.stdout.splitlines() if line]


#: Kod wyjścia przebiegu, którego zbiór mutacji opróżniło WZNOWIENIE. Zero, i to jest
#: cały ładunek 6.B41: przebieg zrobił wszystko, o co go proszono, a skrypt CI puszczający
#: przegląd w pętli do skutku czyta kod wyjścia jako „gotowe"/„awaria" i z kodu 1 nie ma
#: jak wyczytać, że liczyć już nie ma czego, bo wszystko jest policzone.
KOD_WZNOWIENIE_KOMPLETNE = 0

#: Kod wyjścia pozostałych przyczyn pustego zbioru — BEZ ZMIAN względem 07.09.2026.
#: `--only` pasujące do niczego jest usterką wywołania (6.B39 stoi wprost na tym, że to
#: kod 1), `--limit`, który nie przepuścił niczego, tak samo, a filtr nieosiągalnych,
#: który odsiał wszystko, znaczy „nie ma czego mierzyć" — i to nie jest w porządku.
KOD_NIC_DO_LICZENIA = 1


def przyczyna_pustego_zbioru(zebrane, po_wznowieniu, po_limicie, po_filtrze,
                             only: str = "", journal: str = "",
                             limit: int = 0,
                             dopasowane_pliki: int | None = None) -> tuple[str, int]:
    """Nazywa RZECZYWISTĄ przyczynę pustego zbioru mutacji i daje jej kod wyjścia.

    **Po co (6.B41).** Do 07.09.2026 `main` miał na pusty zbiór dwie gałęzie i żadna
    nie pytała, CO go opróżniło. Zmierzone przy 6.B32, drugim przebiegiem na czystym
    drzewie::

        [MUTACJE] wznowienie z /tmp/b32/dziennik.jsonl: 2 z 2 już policzonych
        brak mutacji do sprawdzenia po odfiltrowaniu nieosiągalnych
        kod=1

    Filtr nieosiągalnych nie odsiał wtedy NICZEGO — zbiór był pusty, bo wznowienie
    policzyło wszystko. Komunikat nazywał przyczynę, która nie zachodziła, a kod 1
    mówił „awaria" o przebiegu, który skończył całą robotę.

    **Dlaczego komunikat i kod wychodzą z jednego miejsca.** Bo to jedna odpowiedź na
    jedno pytanie. Rozdzielenie ich dałoby dwa czytniki tych samych liczników, a dwa
    czytniki jednej rzeczy rozjeżdżają się po cichu — to była usterka 6.B28.

    **Kolejność pytań jest kolejnością etapów zawężania w `main`**, i to nie jest
    kosmetyka: przy zbiorze opróżnionym przez wznowienie każdy późniejszy licznik też
    jest zerem, więc pytanie zadane w złej kolejności wskazałoby złą przyczynę —
    dokładnie tak, jak robiła to gałąź `if not found:` z komunikatem o filtrze.

    Argumenty to rozmiar zbioru PO kolejnych etapach; `None` znaczy „ten etap jeszcze
    nie chodził na tej drodze" i nigdy nie jest przyczyną.
    """
    if zebrane == 0:
        if only and dopasowane_pliki:
            return (f"brak mutacji do sprawdzenia: --only {only!r} dopasowało "
                    f"{dopasowane_pliki} plik(ów) docelowych, ale żaden nie dał ani "
                    "jednej mutacji w podanych klasach — zawężenie trafiło, klasy nie",
                    KOD_NIC_DO_LICZENIA)
        if only:
            return (f"brak mutacji do sprawdzenia: --only {only!r} nie dopasowało "
                    "ani jednego pliku", KOD_NIC_DO_LICZENIA)
        return ("brak mutacji do sprawdzenia: żaden plik docelowy nie dał ani jednej "
                "mutacji w podanych klasach", KOD_NIC_DO_LICZENIA)
    if po_wznowieniu == 0:
        return (f"brak mutacji do sprawdzenia: wznowienie z {journal} zastało wszystkie "
                f"{zebrane} już policzone — przebieg zrobił wszystko, o co go proszono",
                KOD_WZNOWIENIE_KOMPLETNE)
    if po_limicie == 0:
        return (f"brak mutacji do sprawdzenia: --limit {limit} nie przepuścił ani jednej "
                f"z {po_wznowieniu}", KOD_NIC_DO_LICZENIA)
    if po_filtrze == 0:
        return (f"brak mutacji do sprawdzenia po odfiltrowaniu nieosiągalnych: filtr "
                f"odsiał wszystkie {po_limicie}", KOD_NIC_DO_LICZENIA)
    raise ValueError(
        "przyczyna_pustego_zbioru wołana przy NIEPUSTYM zbiorze: "
        f"zebrane={zebrane}, po_wznowieniu={po_wznowieniu}, po_limicie={po_limicie}, "
        f"po_filtrze={po_filtrze}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--limit", type=int, default=0,
                        help="tylko pierwsze N mutacji; 0 = wszystkie")
    parser.add_argument("--only", default="",
                        help="mutuj wyłącznie pliki, których ścieżka zawiera ten PODCIĄG "
                             "(nie: nazwę pliku) — `sweep.py` łapie też `tunnel_sweep.py`; "
                             "przebieg wypisuje, ile modułów złapał, zanim ruszy dalej")
    parser.add_argument("--operators", default=",".join(KINDS),
                        help="klasy mutacji po przecinku, z " + ", ".join(KINDS) +
                             f". `{','.join(LEGACY_KINDS)}` odtwarza zestaw sprzed "
                             "05.09.2026 co do identyfikatora")
    parser.add_argument("--no-coverage", action="store_true",
                        help="nie mierz, które wiersze zestaw testów wykonuje. Ocalałe "
                             "trafią wtedy do kupki „niezmierzone”, bo bez tego pomiaru "
                             "nie wiadomo, czy przeżyły mimo wykonania, czy dlatego, "
                             "że nikt ich nie uruchomił")
    parser.add_argument("--journal", default="",
                        help="dziennik JSONL: każdy wynik dopisywany od razu. Wznowienie "
                             "pomija to, co już w nim jest. Bez tego przerwany przebieg "
                             "traci wszystko")
    parser.add_argument("--json", default="", help="zapisz surowe wyniki tutaj")
    parser.add_argument("--out", default="", help="zapisz raport markdown tutaj")
    parser.add_argument("--list", action="store_true", help="wypisz mutacje i wyjdź")
    parser.add_argument("--include-unreachable", action="store_true",
                        help="mutuj także moduły, których zestaw testów nie potrafi "
                             "zaimportować. Ich mutacje policzą się jako ocalałe, choć "
                             "nie mają jak zostać zabite — patrz `unreachable_modules`")
    parser.add_argument("--dirty", action="store_true",
                        help="nie przerywaj, gdy mutowane pliki mają niezacommitowane "
                             "zmiany. Wyniki będą wtedy liczone dla innego pliku niż ten "
                             "w drzewie roboczym")
    args = parser.parse_args()

    kinds = tuple(part for part in args.operators.split(",") if part)
    unknown_kinds = [k for k in kinds if k not in KINDS]
    if unknown_kinds or not kinds:
        parser.error(f"nieznane klasy mutacji: {unknown_kinds or ['(pusto)']}; "
                     f"dozwolone: {', '.join(KINDS)}")

    # 6.D37: `--only ""` to ZLE WYWOLANIE, nie puste zawezenie — i do 07.09.2026
    # przechodzilo w milczeniu. Pusty napis jest falszywy dla `if args.only`, wiec
    # nie wchodzil ani filtr, ani wypis „dopasowalo N plikow", ani odmowa z 6.B39:
    # przebieg robil PELNY przeglad (2346 mutacji zamiast 2 dla typowego triazu
    # jednego modulu, czyli 1173x wiecej pracy) i wygladal przy tym na zawezony,
    # bo wolajacy o zawezenie prosil.
    #
    # Ze to nie jest przypadek teoretyczny, mowi pomiar 07.09.2026: w `reports/`
    # stoja DWIE petle podstawiajace zmienna do `--only`. Ich zachowanie sie ROZNI
    # i tylko jedna wymaga tej odmowy:
    #   `--only "$m"`  (mutation-drift.md:455)         -> `--only ""`, kod 0, pelny
    #                                                     przeglad w milczeniu
    #   `--only $f`    (mutation-triage-fizyka.md:173) -> argument znika, a argparse
    #                                                     JUZ odmawia: `expected one
    #                                                     argument`, kod 2
    # Druga postac jest wiec chroniona od zawsze, pierwsza nie byla przez nic.
    #
    # Kod 2, nie 1: to nie „nie ma czego liczyc" (`KOD_NIC_DO_LICZENIA`, gdzie zbior
    # jest pusty z powodu, ktory przebieg umie nazwac), a bledne wywolanie — i taki
    # sam kod daje argparse dla drugiej postaci tej samej pomylki. Jedna pomylka,
    # jeden kod, niezaleznie od tego, czy cudzyslow ocalal.
    if "--only" in sys.argv and not args.only:
        parser.error(
            "--only '' nie jest zawężeniem: pusty wzorzec przepuszcza WSZYSTKIE "
            f"{len(targets())} plików docelowych, czyli robi pełny przegląd. "
            "Jeżeli chodziło o przebieg bez zawężenia — nie podawaj --only wcale; "
            "jeżeli wzorzec bierze się z podstawienia zmiennej, sprawdź, czy nie "
            "jest pusta.")

    # Commit policzony TUTAJ, a nie tuż przed raportem: nazwa domyślnego dziennika
    # go zawiera, bo przebiegi z różnych drzew mierzą co innego.
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()

    found = collect(kinds)

    # `--only` zawęża PRZED czytaniem dziennika, a nie po. Powód jest jeden: bez
    # znajomości zbioru plików tego przebiegu nie da się sprawdzić, czy dziennik
    # niesie cudze wyniki — a właśnie to sprawdzenie jest niżej. Dla przebiegu bez
    # `--only` kolejność niczego nie zmienia, bo zbiorem jest wtedy wszystko.
    if args.only:
        found = [m for m in found if args.only in m.path]
    pliki_przebiegu = sorted({m.path for m in found})

    # 6.B39: pliki DOCELOWE dopasowane przez `--only`, liczone niezaleznie od tego, czy
    # dały mutację. Bez tego licznika nie da się odróżnić dwóch przyczyn pustego zbioru,
    # a wcześniej komunikat mówił „nie dopasowało ani jednego pliku" także wtedy, gdy
    # dopasował — zmierzone 07.09.2026: `--only tools/blender/camera_aim.py
    # --operators prog` dopasowuje DOKŁADNIE JEDEN cel i daje zero mutacji, bo ten plik
    # nie ma ani jednego progu. Modułów bez mutacji danej klasy jest dziś od 2
    # (`operator`) do 36 (`przypisanie`) na 63 cele, więc to nie jest przypadek
    # teoretyczny. Licznik idzie do `przyczyna_pustego_zbioru`, a nie do drugiej
    # gałęzi: dwa czytniki jednej rzeczy rozjeżdżają się po cichu (6.B28).
    dopasowane_cele = ([os.path.relpath(c, ROOT) for c in targets()
                        if args.only in os.path.relpath(c, ROOT)]
                       if args.only else [])

    # `--only` dopasowuje PODCIĄG ścieżki, nie nazwę pliku — to jest zamierzone:
    # `--only tools/track/` musi łapać cały katalog naraz (patrz
    # `test_cli_lists_only_the_requested_class`), a dopasowanie tylko po nazwie
    # pliku by to zablokowało. Cena podciągu jest jednak taka, że `sweep.py`
    # łapie też `tunnel_sweep.py` — zmierzone przy 6.D15 (#301): 117 mutacji
    # z `tools/blender/sweep.py` i 68 z `tools/blender/tunnel_sweep.py` pod
    # jedną etykietą `--only sweep.py`. Cztery przebiegi (6.B6, 6.B7, 6.B8, 6.D5)
    # wołały `--only` basename'em bez wiedzy, że złapały drugi moduł. Dlatego
    # ten komunikat nazywa złapane moduły PRZED czytaniem dziennika i PRZED
    # jakąkolwiek mutacją — nawet dla `--list` — więc rozjazd jest widoczny
    # w pierwszym wierszu wyjścia, a nie odkrywany przez porównanie liczb.
    if args.only:
        # Dwie liczby, nie jedna: ile CELÓW zawężenie dopasowało i z ilu z nich
        # wyszła choć jedna mutacja. Do 07.09.2026 stała tu tylko druga, więc
        # zawężenie trafione w plik bez mutacji wyglądało identycznie jak literówka
        # w ścieżce — oba dawały „0 moduł(ów)".
        print(f"[MUTACJE] --only {args.only!r} dopasowało {len(dopasowane_cele)} "
              f"plik(ów) docelowych i złapało {len(found)} mutacji "
              f"z {len(pliki_przebiegu)} moduł(ów): {', '.join(pliki_przebiegu)}")

    # Rozmiar zbioru, o KTÓRY POPROSZONO, zapamiętany przed pierwszym zawężeniem.
    # `przyczyna_pustego_zbioru` porównuje z nim liczniki kolejnych etapów, bo bez
    # punktu wyjścia „zero po wznowieniu" nie da się odróżnić od „zero od początku".
    zebrane = len(found)

    # Odciski liczone TUTAJ: zbior plikow przebiegu jest juz znany, a dziennika jeszcze
    # nie czytano — czyli dokladnie w miejscu, w ktorym odmowa nizej ma czym porownywac.
    # Raz na plik, nie raz na mutacje (6.B32).
    odciski = odciski_przebiegu(pliki_przebiegu)

    journal = args.journal or default_journal(
        commit, kinds, args.only, odcisk_przebiegu(odciski))
    done = read_journal(journal)

    obce = [entry for entry in done if entry.get("plik") not in pliki_przebiegu]
    if obce:
        skad = sorted({entry.get("plik", "?") for entry in obce})
        print(f"[MUTACJE] PRZERWANE — dziennik {journal} niesie {len(obce)} wpisów "
              f"spoza tego przebiegu, z plików: {', '.join(skad)}.\n"
              "  Wynik przebiegu czytany jest Z CAŁEGO dziennika, więc te wpisy "
              "trafiłyby do raportu jako wynik TEGO pomiaru.\n"
              "  Podaj własny --journal albo skasuj tamten plik.", file=sys.stderr)
        return 2

    # 6.B19: identyfikator mutacji (plik:wiersz:przesunięcie bajtowe) NIE mówi, z jakiego
    # drzewa pochodzi. Dwie różne mutacje z dwóch różnych commitów mogą wypaść pod tym
    # samym przesunięciem, więc samo dopasowanie po `id` (niżej) by je pomyliło. Wpis
    # bez pola `commit` jest starszy niż ta poprawka i nie da się go zweryfikować —
    # liczy się jako obcy z tego samego powodu, dla którego wpis bez pola `plik` liczy
    # się jako obcy wyżej: milcząca zgoda wpuściłaby cudzy wynik pod dzisiejszą mutację.
    inny_commit = [entry for entry in done if entry.get("commit") != commit]
    if inny_commit:
        skad = sorted({str(entry.get("commit")) for entry in inny_commit})
        print(f"[MUTACJE] PRZERWANE — dziennik {journal} niesie {len(inny_commit)} "
              f"wpisów z innego drzewa: commit {', '.join(skad)}, a ten przebieg liczy "
              f"na {commit!r}.\n"
              "  Identyfikator mutacji (plik:wiersz:przesunięcie bajtowe) nie niesie "
              "commita, więc wznowienie mogłoby po cichu podstawić wynik zapisany dla "
              "innego kodu pod dzisiejszą mutację.\n"
              "  Podaj własny --journal na inną ścieżkę albo skasuj tamten plik.",
              file=sys.stderr)
        return 2

    # 6.B32: `commit` nie odroznia dwoch przebiegow na TYM SAMYM commicie. Przy
    # niezacommitowanej zmianie — a `--dirty` jest po to, zeby takie przebiegi robic —
    # `git rev-parse --short HEAD` daje w obu te sama wartosc, a tresc mutowanego pliku
    # juz nie. Odmowa z 6.B19 tego przypadku NIE WIDZI; 6.B19 nazwala to wprost jako to,
    # czego nie lapie.
    #
    # Wpis BEZ pola `odcisk` jest starszy niz ta poprawka i nie da sie go zweryfikowac —
    # liczy sie jako obcy z tego samego powodu, dla ktorego wpis bez pola `commit` liczyl
    # sie jako obcy przy 6.B19: milczaca zgoda wpuscilaby cudzy wynik pod dzisiejsza
    # mutacje. Odmowa nazywa PLIK, a nie tylko fakt, bo przy `--only` na katalog rozjazd
    # dotyczy zwykle jednego modulu z kilkunastu.
    inna_tresc = [
        entry for entry in done
        if entry.get("odcisk") != odciski.get(entry.get("plik"))
    ]
    if inna_tresc:
        skad = sorted({
            f"{entry.get('plik')} (dziennik {entry.get('odcisk')}, "
            f"drzewo {odciski.get(entry.get('plik'))})"
            for entry in inna_tresc
        })
        print(f"[MUTACJE] PRZERWANE — dziennik {journal} niesie {len(inna_tresc)} "
              "wpisow policzonych na INNEJ TRESCI pliku niz ta w drzewie roboczym, "
              f"przy tym samym commicie {commit!r}:\n"
              + "".join(f"    {wiersz}\n" for wiersz in skad)
              + "  Identyfikator mutacji (plik:wiersz:przesuniecie bajtowe) nie niesie "
                "tresci, a `commit` nie odroznia dwoch przebiegow na tym samym commicie "
                "— wznowienie podstawiloby wynik policzony dla innego kodu pod dzisiejsza "
                "mutacje.\n"
                "  Podaj wlasny --journal na inna sciezke albo skasuj tamten plik."
              + brudne_wyjasnienie(pliki_przebiegu, args.dirty),
              file=sys.stderr)
        return 2

    if done:
        # Wznowienie liczy tylko to, czego jeszcze nie ma — WYŁĄCZNIE dla mutacji o tym
        # samym identyfikatorze. Samo dopasowanie po `id` nie odróżnia drzew — o to dba
        # odmowa wyżej: gdy do tego miejsca dojdzie, każdy wpis w `done` jest z TEGO
        # samego commita, więc zmiana kodu MIĘDZY przebiegami na tym samym commicie
        # (drzewo z `--dirty`) jest jedynym przypadkiem, którego to dopasowanie już
        # nie chroni — a ten jest poza zakresem 6.B19.
        seen = {entry["id"] for entry in done}
        found = [m for m in found if m.id not in seen]
        print(f"[MUTACJE] wznowienie z {journal}: {zebrane - len(found)} z {zebrane} "
              "już policzonych")
    po_wznowieniu = len(found)

    if args.limit:
        found = found[:args.limit]
    po_limicie = len(found)

    if args.list:
        # 6.B39: do 07.09.2026 ta gałąź wychodziła ZEREM także przy zbiorze pustym,
        # bo odmowa `brak mutacji do sprawdzenia` stoi ZA nią. Zmierzone:
        # `--only tools/nie-ma-takiego-pliku.py --list` dawało `razem: 0` i kod 0,
        # czyli przebieg CI z literówką w zawężeniu dostawał zielone zero.
        # Odmowa idzie przez `przyczyna_pustego_zbioru` — ten sam przyrząd, co droga
        # bez `--list` — więc obie nie mogą podać różnych przyczyn tego samego stanu.
        # Zawężenie BEZ trafień i przebieg bez `--only` to osobne sprawy: ta pozycja
        # dotyczy `--only`, a pusty zbiór bez zawężenia zostaje poza jej zakresem.
        if args.only and not found:
            komunikat, kod = przyczyna_pustego_zbioru(
                len(found), None, None, None, only=args.only, journal=journal,
                limit=args.limit, dopasowane_pliki=len(dopasowane_cele))
            print(komunikat, file=sys.stderr)
            return kod
        for mutation in found:
            print(mutation.describe())
        print(f"razem: {len(found)}")
        return 0

    # 6.B41: warunek jest gołe `not found`, a nie `not found and not done`. Tamten
    # drugi członek był mechanizmem usterki: przy zbiorze opróżnionym przez WZNOWIENIE
    # (`done` niepuste) gałąź milczała, a odmowę wypisywała dopiero gałąź za filtrem
    # nieosiągalnych — nazywając przyczynę, która nie zachodziła. Tu jest też jedyne
    # miejsce, w którym przebieg bez roboty może wyjść ZEREM.
    if not found:
        komunikat, kod = przyczyna_pustego_zbioru(
            zebrane, po_wznowieniu, po_limicie, None,
            only=args.only, journal=journal, limit=args.limit,
            dopasowane_pliki=len(dopasowane_cele))
        print(komunikat, file=sys.stderr)
        return kod

    dirty = dirty_sources(m.path for m in found)
    if dirty and not args.dirty:
        print("[MUTACJE] przerwane: mutowane pliki mają niezacommitowane zmiany:",
              file=sys.stderr)
        for path in dirty:
            print(f"    {path}", file=sys.stderr)
        print(
            "\n  Mutacje są liczone z DRZEWA ROBOCZEGO, a robotnicy pracują na kopii\n"
            "  `git worktree add --detach HEAD`. Gdy te dwa źródła się różnią, przesunięcia\n"
            "  bajtowe mutacji nie pasują do pliku, na którym mają być wykonane. Strażnik\n"
            "  wklejki to wyłapie, ale dopiero po kilkunastu minutach liczenia i w postaci\n"
            "  AssertionError o nieoczywistej treści.\n\n"
            "  Zacommituj zmiany albo uruchom z --dirty, jeśli wiesz, że robisz co innego.",
            file=sys.stderr)
        return 2

    unreachable = unreachable_modules(m.path for m in found)
    if unreachable:
        blocked = [m for m in found if m.path in unreachable]
        print(f"[MUTACJE] {len(blocked)} mutacji w {len(unreachable)} modułach, których "
              "zestaw testów nie potrafi zaimportować — nie mają jak zostać zabite:",
              file=sys.stderr)
        for path, reason in unreachable.items():
            count = sum(1 for m in blocked if m.path == path)
            print(f"    {path} ({count}): {reason[:80]}", file=sys.stderr)
        if not args.include_unreachable:
            found = [m for m in found if m.path not in unreachable]
            print("[MUTACJE] pominięte; --include-unreachable liczy je razem z resztą",
                  file=sys.stderr)

    if not found:
        komunikat, kod = przyczyna_pustego_zbioru(
            zebrane, po_wznowieniu, po_limicie, len(found),
            only=args.only, journal=journal, limit=args.limit)
        print(komunikat, file=sys.stderr)
        return kod

    print(f"[MUTACJE] {len(found)} mutacji do policzenia, {args.workers} robotników, "
          f"commit {commit}, klasy {','.join(kinds)}, dziennik {journal}")

    with tempfile.TemporaryDirectory(prefix="metro-mutacje-") as work:
        # Kalibracja wyroczni PRZED pomiarem. Bez niej „zabitych 31/31" znaczy
        # dokładnie tyle samo, co „zestaw pada zawsze" — i wygląda lepiej.
        print("[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji")
        base = os.path.join(work, "wtbase")
        add_worktree(base)
        try:
            problem = baseline_problem(base, args.timeout)
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", base],
                           cwd=ROOT, capture_output=True)
        if problem is not None:
            print(f"[MUTACJE] PRZERWANE — {problem}", file=sys.stderr)
            return 2
        print("[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”")

        coverage = None
        if not args.no_coverage:
            # Sonda liczy wiersze, więc chodzi kilka razy wolniej od zwykłego
            # przebiegu zestawu. Własny, hojniejszy limit, żeby nie wywracała się
            # o `--timeout` dobrany do przebiegu bez licznika.
            # 6.B36: mapa pokrycia NIE zalezy od mutowanego modulu. `coverage_map`
            # nie bierze zadnego argumentu o module — jeden przebieg zestawu
            # z licznikiem wierszy w kopii `HEAD`, sledzone jest cale `tools/`.
            # Wolno ja wiec policzyc RAZ na commit i zapamietac miedzy przebiegami.
            #
            # ZMIERZONE, nie zalozone (`reports/pamiec-pokrycia.md`): zestaw bez
            # sondy 54,49 s, z sonda 332,57 s i 331,92 s w dwoch przebiegach na tym
            # samym drzewie — narzut instrumentacji to okolo 278 s, czyli sonda
            # kosztuje 6,1 raza tyle, co goly zestaw.
            #
            # Klucz to COMMIT, nie odcisk tresci z 6.B32, i to jest roznica warta
            # nazwania: sonda czyta kopie `git worktree add --detach HEAD`, wiec
            # jej wynik zalezy od HEAD i tylko od HEAD. Mutacje przeciwnie — liczy
            # je `collect` z DRZEWA ROBOCZEGO, dlatego tam kluczem musi byc tresc.
            # Dwa klucze do dwoch roznych rzeczy, kazdy zmierzony.
            plik_pokrycia = sciezka_pokrycia(commit)
            coverage = wczytaj_pokrycie(plik_pokrycia, commit)
            if coverage is not None:
                print(f"[MUTACJE] sonda pokrycia: mapa z pamieci {plik_pokrycia} "
                      f"({len(coverage)} modulow) — commit {commit} bez zmian")
            else:
                print("[MUTACJE] sonda pokrycia: jeden przebieg zestawu z licznikiem wierszy")
                surowa = coverage_map(work, args.timeout * 4)
                if surowa is not None:
                    coverage = pokrycie_w_celach(surowa)
                    zapisz_pokrycie(plik_pokrycia, commit, coverage)
                    print(f"[MUTACJE] mapa zapamietana w {plik_pokrycia}: "
                          f"{len(coverage)} modulow z {len(surowa)} sledzonych")
            if coverage is None:
                print("[MUTACJE] sonda pokrycia nie doszła do końca — ocalałe będą "
                      "policzone jako niezmierzone", file=sys.stderr)
            else:
                hit = sum(1 for m in found if was_executed(coverage, m))
                print(f"[MUTACJE] wykonywanych wierszy dotyczy {hit} z {len(found)} "
                      f"mutacji; pozostałe {len(found) - hit} siedzą w kodzie, którego "
                      "zestaw nie uruchamia")

        results = sweep(found, args.workers, args.timeout, work, journal, commit,
                        coverage, odciski)

    decided = [r for r in results if r.get("rozstrzygniete", True)]
    survived = [r for r in decided if r["przezyla"]]
    cold = [r for r in survived if r.get("wykonana") is False]
    unknown = len(results) - len(decided)
    print(f"[MUTACJE] rozstrzygniętych {len(decided)}/{len(results)}, "
          f"zabitych {len(decided) - len(survived)}, ocalałych {len(survived)} "
          f"(w tym {len(cold)} nieuruchomionych), "
          f"nierozstrzygniętych {unknown}")
    for entry in survived:
        mark = {True: "OCALAŁA ", False: "NIEURUCH."}.get(entry.get("wykonana"), "OCALAŁA?")
        print(f"  {mark} {entry['opis']}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(results, handle, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(report(results, commit, odciski))
        print(f"[MUTACJE] raport -> {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

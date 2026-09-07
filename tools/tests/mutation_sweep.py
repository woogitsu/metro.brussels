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
import json
import hashlib
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


def collect(kinds=KINDS) -> list[Mutation]:
    found: list[Mutation] = []
    for path in targets():
        with open(path, encoding="utf-8") as handle:
            found.extend(mutations_for(path, handle.read(), kinds))
    return found


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
              executed: bool | None = None) -> dict:
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
           journal: str, commit: str, coverage=None) -> int:
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
                              was_executed(coverage, mutation))
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


def default_journal(commit: str, kinds: tuple, only: str) -> str:
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

    **Dlaczego nazwa zawiera właśnie to.** Commit, klasy operatorów i zawężenie
    `--only` to trzy rzeczy, które rozstrzygają, CZEGO przebieg dotyczy. Dwa
    przebiegi różniące się którąkolwiek z nich mierzą co innego i nie mają prawa
    dzielić pliku; dwa przebiegi zgodne we wszystkich trzech to ten sam pomiar,
    więc wznowienie ma je znaleźć.
    """
    znacznik = hashlib.sha256(
        "|".join([commit, ",".join(sorted(kinds)), only or ""]).encode("utf-8")
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
          journal: str, commit: str, coverage=None) -> list[dict]:
    os.makedirs(out_dir, exist_ok=True)
    chunks: list[list[Mutation]] = [[] for _ in range(workers)]
    for index, mutation in enumerate(mutations):
        chunks[index % workers].append(mutation)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, slot, chunk, timeout, out_dir, journal, commit, coverage)
                   for slot, chunk in enumerate(chunks) if chunk]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    results = read_journal(journal)
    results.sort(key=lambda r: (r["plik"], r["wiersz"]))
    return results


def report(results: list[dict], commit: str) -> str:
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
        print(f"[MUTACJE] --only {args.only!r} złapało {len(found)} mutacji "
              f"z {len(pliki_przebiegu)} moduł(ów): {', '.join(pliki_przebiegu)}")

    journal = args.journal or default_journal(commit, kinds, args.only)
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

    if done:
        # Wznowienie liczy tylko to, czego jeszcze nie ma — WYŁĄCZNIE dla mutacji o tym
        # samym identyfikatorze. Samo dopasowanie po `id` nie odróżnia drzew — o to dba
        # odmowa wyżej: gdy do tego miejsca dojdzie, każdy wpis w `done` jest z TEGO
        # samego commita, więc zmiana kodu MIĘDZY przebiegami na tym samym commicie
        # (drzewo z `--dirty`) jest jedynym przypadkiem, którego to dopasowanie już
        # nie chroni — a ten jest poza zakresem 6.B19.
        seen = {entry["id"] for entry in done}
        before = len(found)
        found = [m for m in found if m.id not in seen]
        print(f"[MUTACJE] wznowienie z {journal}: {before - len(found)} z {before} "
              "już policzonych")

    if args.limit:
        found = found[:args.limit]

    if args.list:
        for mutation in found:
            print(mutation.describe())
        print(f"razem: {len(found)}")
        return 0

    if not found and not done:
        print("brak mutacji do sprawdzenia", file=sys.stderr)
        return 1

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
        print("brak mutacji do sprawdzenia po odfiltrowaniu nieosiągalnych", file=sys.stderr)
        return 1

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
            print("[MUTACJE] sonda pokrycia: jeden przebieg zestawu z licznikiem wierszy")
            coverage = coverage_map(work, args.timeout * 4)
            if coverage is None:
                print("[MUTACJE] sonda pokrycia nie doszła do końca — ocalałe będą "
                      "policzone jako niezmierzone", file=sys.stderr)
            else:
                hit = sum(1 for m in found if was_executed(coverage, m))
                print(f"[MUTACJE] wykonywanych wierszy dotyczy {hit} z {len(found)} "
                      f"mutacji; pozostałe {len(found) - hit} siedzą w kodzie, którego "
                      "zestaw nie uruchamia")

        results = sweep(found, args.workers, args.timeout, work, journal, commit, coverage)

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
            handle.write(report(results, commit))
        print(f"[MUTACJE] raport -> {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

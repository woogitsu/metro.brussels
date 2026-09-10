#!/usr/bin/env python3
"""Bramka: test, który przeszedł, musiał wykonać co najmniej jedną asercję.

Powód jest zmierzony, nie wymyślony. W zamkniętym PR #139 stały dwa testy zaczynające
się od

    path = os.path.join(ROOT, "build", "t400", "chunks", "L1_A-chunks.json")
    if not os.path.isfile(path):
        return

`python-tests.yml` nie ma kroku, który buduje `build/`, a `actions/checkout` robi
`git clean -ffdx`. W CI ten plik nie istniał NIGDY, więc oba testy kończyły się na
drugiej linii, wypisywały `ok` i podnosiły licznik `przeszło`. Odtworzone 05.09.2026:
dwa `PASS`, zero asercji. Kontrole negatywne z opisu tamtego PR-a działały wyłącznie
u autora, bo miał w drzewie zaległe `build/`.

Test, który milczy, wygląda w logu dokładnie tak samo jak test, który sprawdził.
Ten moduł usuwa tę dwuznaczność dwoma narzędziami:

* **licznik asercji** — moduły testowe są ładowane przez transformację AST, która
  przed każdą asercją wstawia wywołanie licznika. Runner czyta licznik po każdym
  teście; zero przy werdykcie „przeszedł" to awaria, nie sukces;
* **jawne pominięcie** — `skip("powód")` podnosi `Skipped`, runner wypisuje `SKIP`
  z powodem i **nie liczy** takiego testu jako zaliczonego. Test, który naprawdę
  potrzebuje Blendera albo artefaktu z `build/`, ma prawo się pominąć — ale musi
  to powiedzieć, a nie udać, że sprawdził.

Co liczy się jako asercja:

1. `assert ...` — wykonanie samej instrukcji;
2. wejście w `except ...:` należące do `try`, którego ścieżka „bez wyjątku" kończy się
   `raise AssertionError(...)` (w `else:` albo w dalszych instrukcjach tego samego
   bloku). To jest idiom „coś miało paść i padło", używany w tym repo bez `assert`:

       try:
           SW.stream_window(100.0, -1.0)
       except ValueError:
           return
       raise AssertionError("ujemny zasięg streamowania został przyjęty")

   Bez punktu 2 bramka kazałaby dziesięciu poprawnym testom dopisać sztuczny `assert`.

Instrumentacja jest robiona przez AST, a nie przez `sys.settrace`, bo koszt ma
znaczenie: `mutation_sweep.py` uruchamia cały zestaw raz na mutację, setki razy pod
rząd. Zmierzone na tym drzewie 05.09.2026 — zestaw goły 38,8 s, pod `sys.settrace`
z wczesnym wyjściem 66,7 s (+72 %), z instrumentacją AST bez mierzalnej różnicy.
"""
import ast
import os
import sys
import types

#: Nazwa, pod którą licznik trafia do globali instrumentowanego modułu. Podkreślniki
#: po obu stronach, żeby nie kolidowała z niczym, co test mógłby chcieć nazwać sam.
BUMP = "__metro_assertion_bump__"

_HITS = [0]
_SITES = [0]


class Skipped(Exception):
    """Test świadomie pominięty. Runner nie liczy go jako zaliczonego."""


def skip(reason):
    """Pomiń bieżący test z podanym powodem.

    Powód jest obowiązkowy i trafia do logu. `skip("")` nie ma sensu: pominięcie bez
    powodu jest tym samym cichym `return`, przed którym ta bramka stoi.
    """
    reason = str(reason).strip()
    if not reason:
        raise ValueError("pominięcie testu wymaga powodu")
    raise Skipped(reason)


def bump():
    """Wołane przez kod wstawiony do instrumentowanych modułów."""
    _HITS[0] += 1


def reset():
    """Wyzeruj licznik przed pojedynczym testem."""
    _HITS[0] = 0


def hits():
    """Ile asercji wykonano od ostatniego `reset()`."""
    return _HITS[0]


def sites():
    """Ile miejsc asercji wstawiono łącznie podczas ładowania modułów."""
    return _SITES[0]


def _is_assertion_raise(stmt):
    """Czy instrukcja to `raise AssertionError(...)`?"""
    if not isinstance(stmt, ast.Raise):
        return False
    exc = stmt.exc
    if isinstance(exc, ast.Call):
        name = getattr(exc.func, "id", None) or getattr(exc.func, "attr", None)
    elif isinstance(exc, ast.Name):
        name = exc.id
    else:
        name = None
    return name == "AssertionError"


def _bump_call(reference):
    """Instrukcja `__metro_assertion_bump__()` z lokalizacją węzła odniesienia.

    Lokalizacja jest kopiowana celowo: wstawiony węzeł ma numer wiersza asercji,
    więc `compile` nie przesuwa numerów w tracebackach.
    """
    call = ast.Call(func=ast.Name(id=BUMP, ctx=ast.Load()), args=[], keywords=[])
    node = ast.Expr(value=call)
    return ast.fix_missing_locations(ast.copy_location(node, reference))


def _mark_except_guards(tree):
    """Krok 1: `except`, po którym „brak wyjątku" znaczy `raise AssertionError`.

    Robiony PRZED krokiem 2, bo patrzy na sąsiedztwo instrukcji w bloku. Wstawia
    wyłącznie do ciał `except`, więc bloki zewnętrzne pozostają nieruszone i indeksy
    sąsiadów są prawdziwe przez cały przebieg.
    """
    marked = 0
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if not isinstance(block, list):
                continue
            for index, stmt in enumerate(block):
                if not isinstance(stmt, ast.Try):
                    continue
                after = stmt.orelse + block[index + 1:]
                if not any(_is_assertion_raise(s) for s in after):
                    continue
                for handler in stmt.handlers:
                    if handler.body:
                        handler.body.insert(0, _bump_call(handler.body[0]))
                        marked += 1
    return marked


class _AssertCounter(ast.NodeTransformer):
    """Krok 2: przed każdym `assert` wstaw wywołanie licznika."""

    def __init__(self):
        self.marked = 0

    def visit_Assert(self, node):
        self.generic_visit(node)
        self.marked += 1
        return [_bump_call(node), node]


def instrument(source, path):
    """Zwróć `(drzewo, liczba miejsc)` dla źródła modułu testowego."""
    tree = ast.parse(source, path)
    marked = _mark_except_guards(tree)
    counter = _AssertCounter()
    tree = counter.visit(tree)
    ast.fix_missing_locations(tree)
    return tree, marked + counter.marked


def load_instrumented(path, name):
    """Załaduj moduł testowy z licznikiem asercji wstrzykniętym w AST.

    Zastępuje `spec_from_file_location` + `exec_module`: tamta para kompiluje z pliku
    i nie zostawia miejsca na transformację. Moduł ląduje w `sys.modules`, żeby
    zachowywał się jak normalnie zaimportowany.
    """
    with open(path, encoding="utf-8") as handle:
        source = handle.read()
    tree, marked = instrument(source, path)
    _SITES[0] += marked
    # `optimize=0` JAWNIE, a nie z trybu interpretera — 6.D71. Licznik sprawdzeń
    # wstawia przekształcenie drzewa, a nie sama asercja, więc pod `python3 -O`
    # kompilator zdejmuje `assert`, a wstrzyknięte wywołanie licznika ZOSTAJE.
    # Zmierzone 09.09.2026 na module z jedną asercją, która ma padać:
    #
    #     bez -O:  padła: ta asercja MA padać   sprawdzeń: 1
    #     z  -O:   PRZESZŁA (asercja zdjęta)    sprawdzeń: 1
    #
    # Czyli wyrocznia meldowała sprawdzenie, którego nie było — ta sama rodzina co
    # 6.D65, tylko utajona, bo dziś żadne wywołanie w repozytorium nie ustawia
    # `PYTHONOPTIMIZE` ani nie woła interpretera z `-O`. Jawna wartość zdejmuje
    # zależność od tego, jak ktoś kiedyś uruchomi zestaw.
    code = compile(tree, path, "exec", dont_inherit=True, optimize=0)
    module = types.ModuleType(name)
    module.__file__ = path
    module.__dict__[BUMP] = bump
    sys.modules[name] = module
    exec(code, module.__dict__)
    return module


def verdict(outcome, checks):
    """Werdykt dla jednego testu: `("ok"|"skip"|"fail", komunikat)`.

    `outcome` to `None` (test wrócił normalnie), instancja `Skipped` albo dowolny inny
    wyjątek. `checks` to `hits()` zmierzone dla tego testu.
    """
    if isinstance(outcome, Skipped):
        return "skip", str(outcome)
    if outcome is not None:
        return "fail", f"{outcome}"
    if checks == 0:
        return "fail", (
            "przeszedł bez wykonania ani jednej asercji — cichy skip zamiast testu. "
            f"Jeśli pominięcie jest zamierzone, powiedz to wprost: "
            f"`{__name__}.skip(\"powód\")`"
        )
    return "ok", ""


def suite_verdict(total_tests, total_checks):
    """Kontrola samej bramki: czy w ogóle miała na co patrzeć.

    Bramka, która przestała widzieć asercje — bo ładowanie modułów obeszło
    `load_instrumented`, bo transformacja przestała trafiać w `assert`, bo zestaw
    testów zniknął — musi paść, a nie przechodzić na pustym zbiorze. To jest ten sam
    błąd, który łapie u testów, tylko o poziom wyżej.
    """
    if total_tests <= 0:
        return "nie odkryto ani jednego testu — bramka nie ma na co patrzeć"
    if sites() <= 0:
        return "instrumentacja nie znalazła ani jednego miejsca asercji"
    if total_checks <= 0:
        return "cały zestaw nie wykonał ani jednej asercji"
    return ""


def paths():
    """Pliki `tools/tests/test_*.py`, posortowane. Jedno miejsce dla runnera i testów."""
    import glob
    here = os.path.dirname(os.path.abspath(__file__))
    return sorted(glob.glob(os.path.join(here, "test_*.py")))

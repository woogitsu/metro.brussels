#!/usr/bin/env python3
"""Testy narzędzia przeglądu mutacyjnego.

Narzędzie do znajdowania niesprawdzonych bramek, samo niesprawdzone, byłoby żartem.
Testy pilnują trzech rzeczy, z których każda ma tryb cichej awarii:

1. **Pozycja splice'u.** `ast` liczy kolumny w BAJTACH UTF-8, nie w znakach. W pliku
   z polskimi komentarzami naiwny indeks trafia obok, mutacja rozwala składnię,
   przebieg pada — i mutacja zostaje policzona jako „zabita", nie sprawdziwszy niczego.
   To najgorszy możliwy błąd tego narzędzia: **zawyża pokrycie**.
2. **Determinizm.** Dwa przebiegi na tym samym drzewie muszą dać tę samą listę,
   inaczej raport nie da się porównać z poprzednim.
3. **Zakres.** Narzędzie mutuje kod pod testem, nigdy testów. Mutowanie testów
   pokazywałoby, że testy sprawdzają same siebie.
"""
import ast
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mutation_sweep as sweep  # noqa: E402

ROOT = sweep.ROOT


def _mutations(source, path="tools/x.py"):
    return sweep.mutations_for(os.path.join(ROOT, path), source)


# --- pozycja splice'u -------------------------------------------------------------


def test_operator_is_replaced_at_the_right_place():
    source = "def f(a):\n    return a < 3\n"
    found = _mutations(source)
    ops = [m for m in found if m.kind == "operator"]
    assert len(ops) == 1, [m.describe() for m in ops]
    assert ops[0].apply(source) == "def f(a):\n    return a <= 3\n"


def test_polish_comment_does_not_shift_the_splice():
    # TO JEST TEN TEST. `col_offset` w `ast` liczy bajty UTF-8; „ł", „ż" i „ę" zajmują
    # po dwa. Bez konwersji bajty->znaki splice trafia o kilka pozycji w lewo.
    source = "def f(a):\n    # próg łuku, żeby ględzić: ćwierć\n    return a < 3\n"
    ops = [m for m in _mutations(source) if m.kind == "operator"]
    assert len(ops) == 1
    mutated = ops[0].apply(source)
    assert mutated.endswith("return a <= 3\n"), repr(mutated[-40:])
    ast.parse(mutated)


def test_polish_text_before_the_operator_in_the_same_line():
    # Wariant trudniejszy: znaki wielobajtowe stoją w TYM SAMYM wierszu, przed
    # operatorem, więc przesunięcie kumuluje się dokładnie tam, gdzie tniemy.
    source = 'def f(a):\n    return len("żółć ćma ęk") < 3\n'
    ops = [m for m in _mutations(source) if m.kind == "operator"]
    assert len(ops) == 1
    mutated = ops[0].apply(source)
    assert '< 3' not in mutated and '<= 3' in mutated
    ast.parse(mutated)


def test_threshold_is_replaced_at_the_right_place():
    # Sprawdzana jest WŁASNOŚĆ, nie wklejona liczba. Pierwsza wersja tego testu miała
    # wpisane ręcznie `1.515`, a `1.5 * 1.01` daje `1.5150000000000001` — i kusiło,
    # żeby wkleić to, co wyszło. Wklejenie wyniku zamieniłoby test w echo kodu:
    # przechodziłby dla każdej wartości, którą kod akurat zwróci.
    source = "def f(a):\n    return a < 1.5\n"
    thresholds = [m for m in _mutations(source) if m.kind == "prog"]
    assert len(thresholds) == 1

    mutated = thresholds[0].apply(source)
    assert mutated.startswith("def f(a):\n    return a < ")
    moved = float(mutated.rsplit("< ", 1)[1])
    assert moved != 1.5, "próg się nie ruszył"
    assert abs(moved / 1.5 - 1.01) < 1e-12, f"przesunięcie {moved / 1.5:.6f} zamiast 1,01"
    # Liczba musi wrócić do pliku BEZ straty precyzji — zaokrąglony zapis
    # zmieniłby wartość progu i mutacja mierzyłaby co innego, niż deklaruje.
    assert repr(moved) in mutated


def test_zero_threshold_gets_a_value_not_a_scaling():
    # Zero nie ma sąsiedztwa względnego: 0.0 * 1.01 to nadal 0.0, czyli mutacja,
    # która nic nie zmienia i zawsze „przeżywa". Bez tej gałęzi raport pokazywałby
    # dziesiątki fałszywych ocalałych.
    source = "def f(a):\n    return a > 0.0\n"
    thresholds = [m for m in _mutations(source) if m.kind == "prog"]
    assert len(thresholds) == 1
    assert thresholds[0].now != thresholds[0].was
    assert float(thresholds[0].now) != 0.0


def test_integer_threshold_moves_by_one():
    source = "def f(a):\n    return a >= 3\n"
    thresholds = [m for m in _mutations(source) if m.kind == "prog"]
    assert [t.now for t in thresholds] == ["4"]


# --- łączniki logiczne ------------------------------------------------------------


def test_and_becomes_or():
    source = "def f(a, b):\n    return a and b\n"
    found = [m for m in _mutations(source) if m.kind == "logika"]
    assert len(found) == 1, [m.describe() for m in found]
    assert found[0].apply(source) == "def f(a, b):\n    return a or b\n"


def test_or_becomes_and():
    source = "def f(a, b):\n    return a or b\n"
    found = [m for m in _mutations(source) if m.kind == "logika"]
    assert len(found) == 1
    assert found[0].apply(source) == "def f(a, b):\n    return a and b\n"


def test_three_operands_give_two_connectors():
    # `a and b and c` to JEDEN węzeł `BoolOp` z trzema wartościami. Naiwna
    # implementacja „jeden węzeł, jedna mutacja" zgubiłaby drugi łącznik i cicho
    # zmniejszyła zakres przeglądu.
    source = "def f(a, b, c):\n    return a and b and c\n"
    found = [m for m in _mutations(source) if m.kind == "logika"]
    assert len(found) == 2, [m.describe() for m in found]
    assert sorted(m.start for m in found) == [m.start for m in found]
    for mutation in found:
        assert mutation.apply(source).count(" or ") == 1


def test_connector_after_a_comment_is_not_taken_from_the_comment():
    # Komentarz WEWNĄTRZ wyrażenia jest legalny, gdy całość stoi w nawiasach.
    # Bez maskowania komentarzy `re.search` trafiłby w słowo „and" z komentarza,
    # splice rozwaliłby składnię, a mutacja, która się nie parsuje, liczy się jako
    # zabita — czyli błąd w stronę ZAWYŻANIA pokrycia.
    source = "def f(a, b):\n    return (a  # tu and tam\n            and b)\n"
    found = [m for m in _mutations(source) if m.kind == "logika"]
    assert len(found) == 1, [m.describe() for m in found]
    mutated = found[0].apply(source)
    assert "# tu and tam" in mutated, mutated
    assert "or b" in mutated, mutated
    ast.parse(mutated)


def test_mask_comments_keeps_the_length():
    # Maskowanie służy wyłącznie do szukania; indeks trafienia wraca na oryginalny
    # napis. Zmiana długości przesunęłaby splice.
    span = "  # and\n  and "
    masked = sweep.mask_comments(span)
    assert len(masked) == len(span)
    assert masked.count("\n") == span.count("\n")
    assert masked.strip() == "and"


# --- przypisania augmentowane -----------------------------------------------------


def test_augmented_assignment_loses_its_accumulation():
    source = "def f(dt):\n    t = 0.0\n    t += dt\n    return t\n"
    found = [m for m in _mutations(source) if m.kind == "przypisanie"]
    assert len(found) == 1, [m.describe() for m in found]
    assert found[0].apply(source) == "def f(dt):\n    t = 0.0\n    t = dt\n    return t\n"


def test_two_character_augmented_operator_is_replaced_whole():
    # `**=`, `//=` i `>>=` mają po trzy znaki. Wzorzec zbudowany z samych operatorów
    # jednoznakowych trafiłby w OGON tokenu: z `x **= y` zrobiłby `x *= y` — mutację
    # inną niż deklarowana, za to poprawną składniowo, więc niewidoczną dla wszystkich
    # strażników parsowania.
    for op in ("**=", "//=", ">>=", "|="):
        source = f"def f(x, y):\n    x {op} y\n    return x\n"
        found = [m for m in _mutations(source) if m.kind == "przypisanie"]
        assert [m.was for m in found] == [op], (op, [m.describe() for m in found])
        assert found[0].apply(source) == f"def f(x, y):\n    x = y\n    return x\n"


def test_augmented_assignment_to_a_subscript():
    source = "def f(d, k):\n    d[k] += 1\n"
    found = [m for m in _mutations(source) if m.kind == "przypisanie"]
    assert len(found) == 1, [m.describe() for m in found]
    assert found[0].apply(source) == "def f(d, k):\n    d[k] = 1\n"


# --- argumenty wywołań ------------------------------------------------------------


def test_call_argument_number_is_moved():
    source = "def f(x):\n    return round(x, 3)\n"
    found = [m for m in _mutations(source) if m.kind == "argument"]
    assert [(m.was, m.now) for m in found] == [("3", "4")], [m.describe() for m in found]


def test_call_keyword_argument_is_mutated_too():
    # Tolerancje jadą w tym repozytorium prawie zawsze jako argument nazwany
    # (`abs_tol=`, `rel_tol=`). Pominięcie `keywords` wycięłoby z przeglądu
    # dokładnie te liczby, dla których przegląd powstał.
    source = "def f(a, b):\n    return isclose(a, b, abs_tol=1e-09)\n"
    found = [m for m in _mutations(source) if m.kind == "argument"]
    assert len(found) == 1, [m.describe() for m in found]
    assert float(found[0].now) != 1e-09
    assert abs(float(found[0].now) / 1e-09 - 1.01) < 1e-12


def test_boolean_call_argument_is_flipped_not_incremented():
    # `True` jest podklasą `int`; bez osobnej gałęzi wyszłoby `2` — zapis, który
    # w miejscu flagi zachowuje się jak `True` i mutacja byłaby równoważna z definicji.
    source = "def f(p):\n    return open(p, closefd=True)\n"
    found = [m for m in _mutations(source) if m.kind == "argument"]
    assert [(m.was, m.now) for m in found] == [("True", "False")]


def test_string_call_argument_is_left_alone():
    # Podmiana napisu daje albo natychmiastowy wyjątek, albo mutanta o niczym.
    # Ani jedno, ani drugie nie mówi nic o bramkach.
    source = "def f():\n    return open('plik.json', 'r')\n"
    assert [m for m in _mutations(source) if m.kind == "argument"] == []


def test_a_comparison_constant_is_not_also_counted_as_an_argument():
    # Kontrola negatywna do rozdziału klas: `3` w `f(x) < 3` jest progiem porównania
    # i nie ma prawa pojawić się drugi raz jako argument. Podwójne liczenie zawyżyłoby
    # przyrost, którego to zadanie ma dowieść.
    source = "def f(x):\n    return g(x) < 3\n"
    found = _mutations(source)
    assert sorted(m.kind for m in found) == ["operator", "prog"], \
        [m.describe() for m in found]


def test_negative_literal_argument_is_skipped():
    # `f(-1)` to `UnaryOp(USub, Constant(1))`, nie `Constant(-1)`. Splice na samej
    # jedynce dałby `f(-2)`, czyli mutację o innym znaczeniu niż opisana.
    source = "def f():\n    return g(-1)\n"
    assert [m for m in _mutations(source) if m.kind == "argument"] == []


# --- stary zestaw operatorów jest odtwarzalny -------------------------------------


def test_legacy_kinds_are_a_subset_of_the_new_run():
    """Kontrola regresji na całym repozytorium.

    Dopisanie trzech klas mutacji nie może przesunąć ANI JEDNEGO identyfikatora
    ze starego zestawu — inaczej porównanie „przed/po" byłoby porównaniem dwóch
    różnych rzeczy, a wznowienie z dziennika przypisałoby stary wynik nowej mutacji.
    """
    legacy = [(m.id, m.was, m.now) for m in sweep.collect(sweep.LEGACY_KINDS)]
    from_full = [(m.id, m.was, m.now) for m in sweep.collect()
                 if m.kind in sweep.LEGACY_KINDS]
    assert legacy == from_full, (len(legacy), len(from_full))
    assert len(legacy) > 500, len(legacy)


def test_the_new_kinds_add_mutations_rather_than_replace_them():
    legacy = sweep.collect(sweep.LEGACY_KINDS)
    full = sweep.collect()
    assert len(full) > len(legacy), (len(full), len(legacy))
    assert set(m.id for m in legacy) < set(m.id for m in full)


def test_unknown_operator_class_is_rejected_by_the_cli():
    done = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
         "--operators", "kolor", "--list"],
        capture_output=True, text=True)
    assert done.returncode == 2, done.stdout[-400:]
    assert "kolor" in done.stderr, done.stderr[-400:]


def test_cli_lists_only_the_requested_class():
    done = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
         "--operators", "przypisanie", "--only", "tools/track/", "--list",
         "--journal", os.path.join(tempfile.gettempdir(), "metro-mutacje-nieistniejacy.jsonl")],
        capture_output=True, text=True)
    assert done.returncode == 0, done.stderr[-400:]
    body = [line for line in done.stdout.splitlines() if line.startswith("tools/")]
    assert body, done.stdout[-400:]
    assert all(" przypisanie " in line for line in body), body[:5]


def test_only_is_a_substring_match_by_design_and_says_how_many_modules_it_caught():
    """6.D18: `--only` dopasowuje PODCIĄG ścieżki, nie nazwę pliku — zdecydowane,
    bo `test_cli_lists_only_the_requested_class` (wyżej) już opiera się na tym, że
    `--only tools/track/` łapie cały katalog naraz. Cena podciągu, zmierzona przy
    6.D15: `--only sweep.py` łapie też `tunnel_sweep.py`. Od 6.D18 przebieg musi to
    NAZWAĆ w pierwszym wierszu wyjścia, zanim tknie dziennik albo jedną mutację —
    nawet dla samego `--list`.
    """
    done = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
         "--only", "sweep.py", "--list",
         "--journal", os.path.join(tempfile.gettempdir(),
                                    "metro-mutacje-nieistniejacy-6d18.jsonl")],
        capture_output=True, text=True)
    assert done.returncode == 0, done.stderr[-400:]
    lines = done.stdout.splitlines()
    assert lines, done.stdout[-400:]
    pierwszy = lines[0]
    assert pierwszy.startswith("[MUTACJE] --only"), pierwszy
    assert "sweep.py" in pierwszy, pierwszy
    assert "2 moduł" in pierwszy, pierwszy
    assert "tools/blender/sweep.py" in pierwszy, pierwszy
    assert "tools/blender/tunnel_sweep.py" in pierwszy, pierwszy
    # Pojedynczy plik: dalej nazwany, ale liczba modułów to 1, nie 2.
    solo = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
         "--only", "tools/blender/sweep.py", "--list",
         "--journal", os.path.join(tempfile.gettempdir(),
                                    "metro-mutacje-nieistniejacy-6d18b.jsonl")],
        capture_output=True, text=True)
    assert solo.returncode == 0, solo.stderr[-400:]
    pierwszy_solo = solo.stdout.splitlines()[0]
    assert "1 moduł" in pierwszy_solo, pierwszy_solo
    assert "tunnel_sweep.py" not in pierwszy_solo, pierwszy_solo


# --- ocalała, ale czy w ogóle uruchomiona -----------------------------------------


def test_was_executed_is_unknown_without_a_measurement():
    """Brak pomiaru musi dawać `None`, a nie `False`.

    `False` znaczy „wiersz się nie wykonał" i zdejmuje mutację z licznika pokrycia.
    Zwrócenie go, gdy sondy w ogóle nie było, wypisałoby całe repozytorium jako
    martwy kod i pokazało pokrycie 100 % z pustego mianownika.
    """
    mutation = sweep.Mutation("tools/a.py", 7, 0, 1, "<", "<=", "operator")
    assert sweep.was_executed(None, mutation) is None
    assert sweep.was_executed({"tools/a.py": {7}}, mutation) is True
    assert sweep.was_executed({"tools/a.py": {8}}, mutation) is False
    assert sweep.was_executed({}, mutation) is False


def test_tracer_records_the_lines_that_ran_and_only_those():
    """Licznik wierszy z `TRACER`, sprawdzony wykonaniem, w tym w PODPROCESIE.

    Podproces jest tu sednem: `test_all.py` część bramek uruchamia przez
    `sys.executable`. Licznik działający tylko w procesie głównym uznałby wiersze
    pokryte wyłącznie przez podproces za niewykonane — a to fałsz w najgorszą stronę,
    bo kazałby uznać prawdziwą dziurę w pokryciu za martwy kod.
    """
    import json
    with tempfile.TemporaryDirectory() as tmp:
        site = os.path.join(tmp, "site")
        hits = os.path.join(tmp, "hits")
        tools = os.path.join(tmp, "tools")
        os.makedirs(site)
        os.makedirs(tools)
        with open(os.path.join(site, "sitecustomize.py"), "w", encoding="utf-8") as handle:
            handle.write(sweep.TRACER)
        modul = os.path.join(tools, "modul.py")
        with open(modul, "w", encoding="utf-8") as handle:
            handle.write("def wolany():\n"
                         "    return 1\n"
                         "\n"
                         "def nigdy():\n"
                         "    return 2\n")
        runner = os.path.join(tmp, "runner.py")
        with open(runner, "w", encoding="utf-8") as handle:
            handle.write("import subprocess, sys, os\n"
                         "sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))\n"
                         "import modul\n"
                         "subprocess.run([sys.executable, '-c',\n"
                         " \"import sys, os; sys.path.insert(0, os.path.join(os.environ['DIR'], 'tools'));\"\n"
                         " \"import modul; modul.wolany()\"], check=True)\n")

        env = dict(os.environ)
        env["PYTHONPATH"] = site
        env["METRO_COVER_ROOT"] = tools + os.sep
        env["METRO_COVER_OUT"] = hits
        env["DIR"] = tmp
        done = subprocess.run([sys.executable, runner], env=env,
                              capture_output=True, text=True)
        assert done.returncode == 0, done.stderr[-400:]

        seen = set()
        files = sorted(os.listdir(hits))
        assert len(files) >= 2, f"licznik nie zapisał podprocesu: {files}"
        for name in files:
            with open(os.path.join(hits, name), encoding="utf-8") as handle:
                for path, rows in json.load(handle).items():
                    if os.path.basename(path) == "modul.py":
                        seen.update(rows)
        assert 2 in seen, f"ciało `wolany` nie zostało policzone: {sorted(seen)}"
        assert 5 not in seen, f"ciało `nigdy` policzone, choć nikt go nie wołał: {sorted(seen)}"


# --- co jest mutowane, a co nie ---------------------------------------------------


def test_boolean_is_not_treated_as_a_number():
    # `True` jest w Pythonie podklasą `int`. Bez jawnego wykluczenia zostałoby
    # zmutowane na `2`, co jest bez sensu i zaśmieca raport.
    source = "def f(a):\n    return a == True\n"
    assert [m.kind for m in _mutations(source)] == ["operator"]


def test_only_comparison_operators_we_can_locate():
    # `in` i `is` nie są na liście: ich mutacje wymagałyby wstawienia słowa `not`
    # w miejsce, którego pozycji `ast` nie podaje. Lepiej pominąć niż zgadywać.
    source = "def f(a, b):\n    return a in b\n"
    assert _mutations(source) == []


def test_main_guard_is_not_a_gate():
    # `if __name__ == "__main__"` to konwencja, nie bramka. Zmutowany na `!=` uruchamia
    # CLI modułu przy imporcie i zabija cały zestaw — narzędzie liczyło to jako
    # „test wykrył mutację", czyli ZAWYŻAŁO pokrycie. Na 996 mutacji takich strażników
    # było 35, w tym 27 policzonych jako zabite.
    source = 'def f():\n    return 1\n\n\nif __name__ == "__main__":\n    f()\n'
    assert _mutations(source) == []


def test_a_comparison_next_to_the_guard_is_still_mutated():
    # Kontrola negatywna: pominięcie ma dotyczyć WYŁĄCZNIE strażnika, a nie całego
    # pliku, który go zawiera.
    source = ('def f(a):\n    return a < 3\n\n\n'
              'if __name__ == "__main__":\n    f(1)\n')
    found = _mutations(source)
    at_gate = [m for m in found if m.line == 2]
    assert len(at_gate) == 2, [m.describe() for m in found]
    assert not [m for m in found if m.line == 5], [m.describe() for m in found]
    # Wywołanie w ciele strażnika mutowane JEST — to kod, nie konwencja. Tego, że
    # żaden test go nie wykona, nie rozstrzyga generator mutacji, tylko sonda pokrycia.
    assert [m.describe() for m in found if m.line == 6] == [
        "tools/x.py:6 argument `1` -> `2`"]


def test_plain_assignment_is_not_mutated():
    # Zwykłe `a = 3` nie ma czego zabrać: podmiana wartości byłaby mutacją stałej,
    # a tej narzędzie robi wyłącznie tam, gdzie stała czymś steruje — w porównaniu
    # albo w argumencie wywołania.
    source = "def f():\n    a = 3\n    return a\n"
    assert _mutations(source) == []


def test_tests_are_never_targets():
    # Mutowanie testów pokazywałoby, że testy sprawdzają same siebie.
    for path in sweep.targets():
        assert os.sep + "tests" + os.sep not in path, path
        assert "__pycache__" not in path, path


def test_targets_cover_the_real_tools():
    paths = {os.path.relpath(p, ROOT) for p in sweep.targets()}
    for expected in ("tools/blender/profiles.py", "tools/track/validate.py",
                     "tools/visual/compare.py"):
        assert expected in paths, expected


# --- determinizm i tożsamość ------------------------------------------------------


def test_two_passes_give_the_same_list():
    first = [m.id for m in sweep.collect()]
    second = [m.id for m in sweep.collect()]
    assert first == second


def test_identifiers_are_unique():
    ids = [m.id for m in sweep.collect()]
    assert len(ids) == len(set(ids)), "dwie mutacje o tym samym identyfikatorze"


def test_every_mutation_lands_on_what_it_expects():
    # `apply` asertuje, że w pliku stoi dokładnie to, co mutacja zamierza podmienić.
    # Gdyby pozycje były policzone źle, asercja padnie tutaj, a nie w środku przebiegu
    # trwającego godzinę.
    #
    # Licznik obrotów i asercja na jego wartość NIE są ozdobą. Cała treść tego testu
    # siedzi w pętli; gdyby `collect()` przestało zwracać cokolwiek, pętla nie
    # wykonałaby się ani razu, a test wypisałby `ok` tak samo jak dziś.
    # Zmierzone bramką asercji 05.09.2026: przed tą poprawką test przechodził,
    # wykonując zero własnych asercji.
    cache = {}
    checked = 0
    for mutation in sweep.collect():
        path = os.path.join(ROOT, mutation.path)
        if path not in cache:
            with open(path, encoding="utf-8") as handle:
                cache[path] = handle.read()
        mutation.apply(cache[path])
        checked += 1
    assert checked > 500, f"sprawdzono tylko {checked} mutacji"


def test_every_mutation_still_parses():
    # Mutacja, która nie parsuje, wywala przebieg i liczy się jako zabita — czyli
    # ZAWYŻA pokrycie. To najkosztowniejsza możliwa cicha awaria tego narzędzia.
    # Licznik obrotów jak wyżej i z tego samego powodu.
    cache = {}
    checked = 0
    for mutation in sweep.collect():
        path = os.path.join(ROOT, mutation.path)
        if path not in cache:
            with open(path, encoding="utf-8") as handle:
                cache[path] = handle.read()
        ast.parse(mutation.apply(cache[path]))
        checked += 1
    assert checked > 500, f"sparsowano tylko {checked} mutacji"


def test_there_is_something_to_sweep():
    # Bez tego cztery testy wyżej przechodziłyby po pustej liście.
    found = sweep.collect()
    assert len(found) > 500, f"tylko {len(found)} mutacji — generator przestał generować"
    kinds = {m.kind for m in found}
    assert kinds == set(sweep.KINDS), kinds
    # Każda klasa musi mieć w tym repozytorium co najmniej po kilkanaście sztuk.
    # Klasa, która nigdzie nie trafia, jest kodem martwym udającym pokrycie.
    counts = {kind: sum(1 for m in found if m.kind == kind) for kind in sweep.KINDS}
    assert all(n > 10 for n in counts.values()), counts


# --- raport -----------------------------------------------------------------------


def test_report_names_the_survivors():
    results = [
        {"plik": "tools/a.py", "wiersz": 7, "rodzaj": "prog", "bylo": "0.0",
         "jest": "0.001", "przezyla": True, "opis": "", "id": "a", "padly": [], "ile_padlo": 0},
        {"plik": "tools/a.py", "wiersz": 9, "rodzaj": "operator", "bylo": "<",
         "jest": "<=", "przezyla": False, "opis": "", "id": "b", "padly": ["t"], "ile_padlo": 1},
    ]
    text = sweep.report(results, "abc1234")
    assert "abc1234" in text
    assert "tools/a.py" in text
    assert "| 7 |" in text, "ocalała nie trafiła do tabeli"
    assert "| 9 |" not in text, "zabita mutacja nie ma czego szukać w tabeli ocalałych"


def _entry(line, przezyla, wykonana, rodzaj="argument"):
    return {"plik": "tools/a.py", "wiersz": line, "rodzaj": rodzaj, "bylo": "1",
            "jest": "2", "przezyla": przezyla, "wykonana": wykonana, "opis": "",
            "id": f"a{line}", "padly": [], "ile_padlo": 0}


def test_report_does_not_mix_survivors_that_never_ran_with_real_holes():
    """Sedno rozszerzenia zestawu operatorów.

    Mutacja przypisania albo argumentu wywołania trafia często w kod, do którego
    wykonanie nigdy nie dochodzi. Taka ocalała nie mówi nic o bramkach. Policzona
    razem z ocalałą, która przeżyła MIMO wykonania, zamienia raport o pokryciu
    w raport o rozmiarze repozytorium — i to w stronę zaniżania pokrycia, czyli
    kierującą triaż na kod, w którym nie ma czego naprawiać.
    """
    text = sweep.report([_entry(7, True, True), _entry(9, True, False),
                         _entry(11, False, True)], "abc1234")
    assert "| **ocalałych mimo wykonania** | **1** |" in text, text
    assert "| ocalałych nieuruchomionych | 1 |" in text, text
    # Zabita (1) na wykonane (zabita + ocalała mimo wykonania = 2) to 50 %,
    # a nie 33 %, które wyszłyby z wrzucenia nieuruchomionej do jednego worka.
    assert "| **pokrycie kodu wykonanego** | **50.0 %** |" in text, text
    assert "| pokrycie (z rozstrzygniętych) | 33.3 % |" in text, text
    assert "Ocalałe MIMO wykonania" in text and "żaden test nie uruchomił" in text


def test_report_counts_a_journal_without_the_measurement_as_unmeasured():
    """Dziennik sprzed sondy pokrycia nie może udawać, że wszystko się wykonało.

    Brak pola `wykonana` to „nie wiem", a nie „tak" — inaczej wznowiony stary
    przebieg wyglądałby na zmierzony i wpisywałby martwy kod do dziur w bramkach.
    """
    stary = _entry(7, True, None)
    del stary["wykonana"]
    text = sweep.report([stary], "abc1234")
    assert "| ocalałych o niezmierzonym wykonaniu | 1 |" in text, text
    assert "| **ocalałych mimo wykonania** | **0** |" in text, text


def test_report_separates_a_hanging_mutant_from_a_broken_machine():
    """Dwa różne zdania, dziś liczone jedną liczbą „nierozstrzygnięte".

    Przekroczony czas znaczy, że zestaw się ZAPĘTLIŁ — mutant jest obserwowalny,
    tylko nie przez tę wyrocznię, bo jej dowodem jest linia podsumowania.
    Zabicie sygnałem (OOM) nie mówi o mutancie nic. Sklejone w jedną liczbę
    czyta się jedno i drugie jako awarię narzędzia i triaż idzie w złą stronę.
    """
    wisi = {"plik": "tools/a.py", "wiersz": 5, "rodzaj": "przypisanie", "bylo": "+=",
            "jest": "=", "przezyla": False, "rozstrzygniete": False, "kod": None,
            "opis": "tools/a.py:5 przypisanie", "id": "a5",
            "padly": ["<przekroczony czas>"], "ile_padlo": 1}
    oom = {"plik": "tools/a.py", "wiersz": 9, "rodzaj": "operator", "bylo": "<",
           "jest": "<=", "przezyla": False, "rozstrzygniete": False, "kod": -9,
           "opis": "tools/a.py:9 operator", "id": "a9",
           "padly": ["<zabity sygnałem, kod -9>"], "ile_padlo": 1}
    text = sweep.report([wisi, oom], "abc1234")
    assert "| **nierozstrzygniętych** | **2** |" in text, text
    assert "| — z przekroczonego czasu | 1 |" in text, text
    assert "| — z awarii poza mutacją | 1 |" in text, text
    assert "<przekroczony czas>" in text and "<zabity sygnałem, kod -9>" in text


def test_report_breaks_the_survivors_down_by_mutation_class():
    """Przyrost ocalałych ma być rozbity na klasy, nie podany jedną liczbą.

    Bez rozbicia nie widać, czy nowe klasy cokolwiek wnoszą, czy tylko puchną.
    """
    text = sweep.report([_entry(7, True, True, "logika"),
                         _entry(9, False, True, "operator"),
                         _entry(11, True, False, "przypisanie")], "abc1234")
    assert "| `logika` | 1 | 0 | 1 | 0 |" in text, text
    assert "| `operator` | 1 | 1 | 0 | 0 |" in text, text
    assert "| `przypisanie` | 1 | 0 | 0 | 1 |" in text, text


def test_report_says_so_when_nothing_survived():
    results = [{"plik": "tools/a.py", "wiersz": 9, "rodzaj": "operator", "bylo": "<",
                "jest": "<=", "przezyla": False, "opis": "", "id": "b",
                "padly": ["t"], "ile_padlo": 1}]
    text = sweep.report(results, "abc1234")
    assert "Żadna mutacja nie przeżyła" in text


# --- strażnik brudnego drzewa -------------------------------------------------

def _git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True, check=True)


def _repo_with_one_file(tmp, name="tools/blender/x.py", body="a = 1\n"):
    _git(tmp, "init", "--quiet")
    _git(tmp, "config", "user.email", "t@t")
    _git(tmp, "config", "user.name", "t")
    path = os.path.join(tmp, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)
    _git(tmp, "add", "-A")
    _git(tmp, "commit", "--quiet", "-m", "start")
    return path


def test_dirty_sources_sees_a_modified_file():
    """Mutacje są liczone z drzewa roboczego, a wykonywane na kopii `HEAD`.

    Gdy te dwa źródła się różnią, przesunięcia bajtowe mutacji nie pasują do pliku
    i przebieg pada po kilkunastu minutach na strażniku wklejki. Ten strażnik ma
    przerwać w pierwszej sekundzie.
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = _repo_with_one_file(tmp)
        original = sweep.ROOT
        try:
            sweep.ROOT = tmp
            assert sweep.dirty_sources(["tools/blender/x.py"]) == []
            with open(path, "a", encoding="utf-8") as handle:
                handle.write("# dopisek\n")
            assert sweep.dirty_sources(["tools/blender/x.py"]) == ["tools/blender/x.py"]
        finally:
            sweep.ROOT = original


def test_dirty_sources_ignores_files_it_was_not_asked_about():
    """Kontrola negatywna do testu wyżej.

    Strażnik, który pyta o czystość CAŁEGO repozytorium, blokowałby przegląd za każdym
    razem, gdy w tej samej sesji dopisuje się testy — a to jest normalny tryb pracy
    i nie ma z mutacjami nic wspólnego. Zmieniony plik obok nie może niczego wstrzymać.
    """
    with tempfile.TemporaryDirectory() as tmp:
        _repo_with_one_file(tmp)
        other = os.path.join(tmp, "tools", "tests", "test_x.py")
        os.makedirs(os.path.dirname(other), exist_ok=True)
        with open(other, "w", encoding="utf-8") as handle:
            handle.write("# nowy test\n")
        _git(tmp, "add", "-A")
        _git(tmp, "commit", "--quiet", "-m", "test")
        with open(other, "a", encoding="utf-8") as handle:
            handle.write("# zmiana w teście\n")

        original = sweep.ROOT
        try:
            sweep.ROOT = tmp
            assert sweep.dirty_sources(["tools/blender/x.py"]) == []
            assert sweep.dirty_sources(["tools/tests/test_x.py"]) == ["tools/tests/test_x.py"]
        finally:
            sweep.ROOT = original


def test_dirty_sources_of_nothing_is_empty_without_calling_git():
    """Pusta lista plików nie może wołać `git diff` bez ścieżek — to zwróciłoby
    KAŻDĄ zmianę w repozytorium i strażnik blokowałby wszystko."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _repo_with_one_file(tmp)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("# brudno\n")
        original = sweep.ROOT
        try:
            sweep.ROOT = tmp
            assert sweep.dirty_sources([]) == []
        finally:
            sweep.ROOT = original


# --- moduły nieosiągalne dla zestawu testów -----------------------------------

def test_unreachable_modules_names_a_module_the_suite_cannot_import():
    """Mutacja w module, którego zestaw NIE MOŻE wczytać, nie ma jak zostać zabita.

    Narzędzie liczyło ją dotąd jako „ocalałą" — czyli tak samo jak prawdziwą dziurę
    w pokryciu bramki. Zmierzone na tym repozytorium: **148 z 961 mutacji (15 %) siedzi
    w dziewięciu modułach z `import bpy`**, a w częściowym przebiegu przeżywało tam
    98 % wobec 66 % w czystym Pythonie. Te pozycje zawyżały „nieprzetestowane bramki"
    i kierowały triaż na moduły, w których żaden test nie pomoże, dopóki nie wyjdzie
    z nich matematyka.

    Pytanie jest zadawane WYKONANIEM, nie grepem po nazwie biblioteki: liczy się to,
    czy import się udaje, a nie co go blokuje.
    """
    with tempfile.TemporaryDirectory() as tmp:
        good = os.path.join(tmp, "dobry.py")
        bad = os.path.join(tmp, "zly.py")
        with open(good, "w", encoding="utf-8") as handle:
            handle.write("VALUE = 1\n")
        with open(bad, "w", encoding="utf-8") as handle:
            handle.write("import biblioteka_ktorej_nie_ma\n")

        result = sweep.unreachable_modules([good, bad])
        assert set(result) == {bad}, result
        assert "biblioteka_ktorej_nie_ma" in result[bad], result[bad]


def test_unreachable_modules_reports_the_reason_not_just_the_fact():
    """Sam fakt „nie da się zaimportować" nie mówi, czy to brak Blendera, czy literówka.

    Powód jest ostatnią linią `stderr` podprocesu, czyli tym, co Python sam uznał za
    podsumowanie błędu. Bez niego czytający raportu nie wie, czy ma doinstalować
    zależność, czy naprawić moduł.
    """
    with tempfile.TemporaryDirectory() as tmp:
        broken = os.path.join(tmp, "skladnia.py")
        with open(broken, "w", encoding="utf-8") as handle:
            handle.write("def f(:\n")
        result = sweep.unreachable_modules([broken])
        assert set(result) == {broken}
        assert "SyntaxError" in result[broken], result[broken]


def test_unreachable_modules_sees_a_sibling_import_as_reachable():
    """Kontrola negatywna: moduł wołający sąsiada z tego samego katalogu jest OSIĄGALNY.

    Bez uruchamiania sondy z katalogu modułu każdy plik `tools/blender/*.py`, który
    importuje `sweep` albo `profiles`, wyszedłby nieosiągalny — i narzędzie wycięłoby
    z przeglądu prawie całą geometrię, czyli dokładnie to, co ma mierzyć.
    """
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "sasiad.py"), "w", encoding="utf-8") as handle:
            handle.write("VALUE = 2\n")
        user = os.path.join(tmp, "user.py")
        with open(user, "w", encoding="utf-8") as handle:
            handle.write("import sasiad\nVALUE = sasiad.VALUE\n")
        assert sweep.unreachable_modules([user]) == {}


def test_unreachable_modules_of_nothing_is_empty():
    assert sweep.unreachable_modules([]) == {}


def test_every_real_target_except_the_blender_entry_points_is_reachable():
    """Sonda nie może wycinać modułów, które da się przetestować.

    Zmierzone: 9 z 44 modułów `tools/` jest nieosiągalnych i wszystkie dziewięć to
    wejścia Blenderowe. Gdyby sonda zaczęła zgłaszać cokolwiek innego, przegląd
    po cichu zmniejszyłby swój zakres — a liczba „ocalałych" spadłaby, wyglądając
    na poprawę pokrycia.
    """
    unreachable = sweep.unreachable_modules(sweep.targets())
    assert unreachable, "sonda nie znalazła nic — na tej maszynie bpy jest dostępne?"
    for path, reason in unreachable.items():
        assert "bpy" in reason, f"{path}: nieoczekiwany powód {reason}"
    assert len(unreachable) < len(sweep.targets()) // 2, len(unreachable)


# --- dryf pokrycia mutacyjnego po triażu (6.D5) ------------------------------------
#
# PO CO TA BRAMKA. `reports/mutation-drift.md` zestawia dla każdego modułu z raportem
# triażu liczbę ocalałych z dnia triażu i liczbę zmierzoną dziś. Obie strony tego
# zestawienia starzeją się w ten sam sposób, w jaki zestarzały się liczby, które ten
# raport w ogóle opisuje: ktoś dopisuje do modułu porównanie, liczba mutacji rośnie,
# a tabela w raporcie zostaje na wczoraj i **czyta się jak stan bieżący**. Dokładnie
# tak `tools/ci/assert_shot_metadata.py` doszedł z 33 mutacji do 65 (`a643f05` i
# `2c916de`), a `tools/track/crs.py` z 8 do 14 (`d419437` i `16726cd`).
#
# CZEGO TA BRAMKA NIE ROBI, ŚWIADOMIE. Nie sprawdza liczby OCALAŁYCH — jej pomiar to
# jeden pełny przebieg zestawu testów na mutację: 686 mutacji razy zestaw, który sam
# w sobie chodzi 45 s, czyli ponad trzy godziny przy czterech robotnikach. Tego nie
# da się postawić w bramce chodzącej przy każdym commicie i próba skończyłaby się
# wyłączeniem bramki, nie
# skróceniem przebiegu. Sprawdzana jest liczba MUTACJI, bo liczy się ją z AST w ułamku
# sekundy — a to ona jest mianownikiem i to jej zmiana jest pierwszym objawem dryfu:
# w obu znanych przypadkach ocalałe przybyły razem z mutacjami, nie osobno.
#
# Innymi słowy: bramka nie mówi „pokrycie jest nadal takie", tylko „moduł, dla którego
# ten raport podał liczby, od tamtego pomiaru nie urósł o ani jedno porównanie".
# Gdy urośnie, raport trzeba przeliczyć — i o tym mówi komunikat.

DRIFT_REPORT = os.path.join(ROOT, "reports", "mutation-drift.md")

#: Wiersz tabeli modułów: ścieżka w grawisach, dalej kolumny oddzielone `|`.
DRIFT_ROW = re.compile(r"^\|\s*`(tools/[^`]+\.py)`\s*\|")

#: Raporty triażu objęte pozycją 6.D5. Lista jest ZAMROŻONA i to jest wybór, nie
#: przeoczenie: gdyby test wyliczał ją z `glob`, nowy raport triażu — na przykład ten,
#: który kiedyś powstanie dla `tools/blender/clearance_profile.py` — wywracałby bramkę
#: w cudzym PR-ze, zamiast dopisywać się do audytu wtedy, gdy ktoś ten audyt liczy.
#: Test niżej pilnuje tylko tego, że każdy z tych dwunastu plików nadal istnieje.
TRIAGE_REPORTS = (
    "mutation-triage-alignment.md",
    "mutation-triage-clearance.md",
    "mutation-triage-fizyka.md",
    "mutation-triage-inspire-rail.md",
    "mutation-triage-lod.md",
    "mutation-triage-parametry.md",
    "mutation-triage-placement.md",
    "mutation-triage-png-metadata.md",
    "mutation-triage-surface-width.md",
    "mutation-triage-validate.md",
    "mutation-triage-wczytywanie.md",
    "mutation-triage-wizualna.md",
)


#: Ile kolumn ma wiersz tabeli modułów. Liczba stoi tu, bo bez niej detektor łapie
#: KAŻDY wiersz zaczynający się od ścieżki w grawisach — a raport ma drugą tabelę,
#: czterokolumnową, o tych samych ścieżkach w pierwszej kolumnie. Zmierzone przy
#: kontroli negatywnej nr 2: bez tego warunku `_drift_table` zwracał dla siedmiu
#: modułów wiersze tamtej tabeli i test padał `IndexError`, zamiast czegokolwiek
#: sprawdzić. Test padający z IndexError jest bramką tak samo zepsutą jak zielona.
DRIFT_COLUMNS = 8


def _drift_table(text):
    """Wiersze tabeli modułów jako `{ścieżka: [kolumny]}`, bez pogrubień."""
    rows = {}
    for line in text.splitlines():
        if not DRIFT_ROW.match(line):
            continue
        cells = [c.strip().replace("*", "") for c in line.strip().strip("|").split("|")]
        if len(cells) != DRIFT_COLUMNS:
            continue
        rows[cells[0].strip("`")] = cells[1:]
    return rows


def _drift_text():
    with open(DRIFT_REPORT, encoding="utf-8") as handle:
        return handle.read()


def test_drift_report_exists_and_has_a_row_per_module():
    """Tabela ma wiersz dla każdego modułu z dwunastu raportów triażu.

    Liczba 28 nie jest okrągła i taka ma być: dwanaście raportów opisuje dwadzieścia
    osiem modułów, bo siedem z nich (fizyka, parametry, wczytywanie, png-metadata,
    surface-width, validate, wizualna) bierze po kilka plików naraz.
    """
    rows = _drift_table(_drift_text())
    assert len(rows) == 28, f"wierszy modułów: {len(rows)}, oczekiwano 28"
    for path in rows:
        assert os.path.isfile(os.path.join(ROOT, path)), path


def test_drift_report_mutation_count_is_the_one_the_tool_gives_today():
    """Kolumna „mutacji dziś" ma się zgadzać z tym, co narzędzie liczy Z DRZEWA.

    To jest cała bramka. Liczba ocalałych jest w raporcie z przebiegu i zostaje
    w nim jako pomiar z datą; liczba mutacji jest sprawdzalna tu i teraz, więc jest
    sprawdzana — i to ona pęka pierwsza, gdy ktoś dopisze do modułu porównanie.

    **Liczone ZESTAWEM STARYM (`LEGACY_KINDS`), i to jest treść, nie wygoda.** Audyt
    porównuje dzisiejsze liczby z liczbami z raportów triażu, a te powstały wszystkie
    przed 05.09.2026, czyli zestawem `operator, prog`. Policzenie kolumny „dziś"
    zestawem pełnym dałoby porównanie DWÓCH RÓŻNYCH RZECZY pod jednym nagłówkiem —
    dokładnie tę rodzinę usterek, którą audyt tropi. Zmierzone przy scaleniu #258:
    ta sama bramka liczona zestawem pełnym pokazuje rozjazd we **wszystkich 28**
    modułach (np. `crs.py` 14 wobec 29), choć w drzewie nie zmienił się ani jeden
    z nich — zmieniło się narzędzie.

    Przeliczenie audytu zestawem pełnym jest osobnym zadaniem i osobnym przebiegiem
    (1940 mutacji osiągalnych wobec 985), a nie poprawką w tym teście.
    """
    rows = _drift_table(_drift_text())
    wrong = []
    for path, cells in rows.items():
        with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
            found = len(sweep.mutations_for(
                os.path.join(ROOT, path), handle.read(), kinds=sweep.LEGACY_KINDS))
        written = int(cells[5])
        if written != found:
            wrong.append(f"{path}: raport mówi {written}, narzędzie liczy {found}")
    assert not wrong, (
        "reports/mutation-drift.md rozjechał się z drzewem — przelicz audyt "
        f"dla tych modułów: {wrong}")


def test_drift_report_attributes_every_difference():
    """Każda różnica ma powód: commit w grawisach albo jawne „nie przypisano".

    „Prawdopodobnie z powodu X" jest zakazane przez samą pozycję 6.D5. Test pilnuje
    kształtu, którego nie da się spełnić domysłem: SHA albo przyznanie się.
    """
    sha = re.compile(r"`[0-9a-f]{7,40}`")
    bez_powodu = []
    for path, cells in _drift_table(_drift_text()).items():
        delta, why = cells[3], cells[6]
        if delta in ("0", "—"):
            continue
        if not sha.search(why) and "nie przypisano" not in why:
            bez_powodu.append(f"{path}: {why!r}")
    assert not bez_powodu, f"różnice bez commita i bez przyznania się: {bez_powodu}"


def test_drift_report_pins_the_two_cases_the_task_names():
    """Dwa przypadki z treści 6.D5 stoją w tabeli z liczbami po obu stronach.

    6.D5 nazywa je wprost: `tools/track/crs.py` **6** ocalałych po triażu
    (`reports/mutation-triage-wczytywanie.md`) i `tools/ci/assert_shot_metadata.py`
    **2** (`reports/mutation-triage-png-metadata.md`). Te dwie liczby są historyczne
    i nie wolno ich „odświeżyć": raport ma pokazywać rozjazd, a rozjazd znika, gdy
    ktoś przepisze stronę „przed" na dzisiejszą wartość. To najłatwiejszy sposób,
    w jaki ten audyt mógłby skłamać, i dlatego jest zabramkowany.

    **Nie jest tu przypięta dzisiejsza liczba ocalałych** — ani 4, ani 32. Jej pomiar
    kosztuje pełny przebieg zestawu na mutację, więc bramka nie umiałaby sprawdzić
    nowej wartości, a przypięta stara robiłaby się czerwona po każdym dopisanym
    teście, czyli po każdej DOBREJ zmianie. Sprawdzane jest to, co sprawdzalne:
    obie liczby stoją, różnią się od siebie, a powód różnicy nosi commit.
    """
    rows = _drift_table(_drift_text())
    sha = re.compile(r"`[0-9a-f]{7,40}`")
    for path, po_triazu in (("tools/track/crs.py", "6"),
                            ("tools/ci/assert_shot_metadata.py", "2")):
        cells = rows[path]
        assert cells[1] == po_triazu, f"{path}: liczba z raportu triażu to {cells[1]}"
        assert int(cells[2]) != int(po_triazu), (
            f"{path}: obie liczby są równe — rozjazd zniknął z tabeli?")
        assert sha.search(cells[6]), f"{path}: różnica bez commita: {cells[6]!r}"


def test_drift_report_names_every_triage_report_it_audits():
    """Dwanaście raportów wejściowych istnieje i każdy jest w audycie zacytowany."""
    text = _drift_text()
    for name in TRIAGE_REPORTS:
        assert os.path.isfile(os.path.join(ROOT, "reports", name)), name
        assert name[len("mutation-triage-"):-len(".md")] in text, name
    assert len(TRIAGE_REPORTS) == 12


def test_the_drift_table_detector_is_not_matching_prose():
    """Kontrola detektora: bez niej cztery testy wyżej byłyby zielone na pustej tabeli.

    Trzy wiersze, z których tylko pierwszy jest wierszem tabeli modułów. Gdyby
    wyrażenie łapało zdanie z prozy albo nagłówek sekcji, „28 wierszy" dałoby się
    uzyskać bez ani jednej zmierzonej liczby.
    """
    text = (
        "| `tools/track/crs.py` | wczytywanie | 6 | 8 | +2 | 8 | 14 | `d419437` |\n"
        "Moduł `tools/track/crs.py` urósł o sześć mutacji.\n"
        "### `tools/track/crs.py` — 6 -> 8\n"
        "| `tools/track/crs.py` | `d419437` | 5 | 3 |\n")
    rows = _drift_table(text)
    assert list(rows) == ["tools/track/crs.py"], rows
    assert rows["tools/track/crs.py"][5] == "14", rows["tools/track/crs.py"]
    # Ostatni wiersz to druga tabela raportu, o czterech kolumnach i o tej samej
    # ścieżce. Gdyby wszedł, nadpisałby wiersz właściwy — i tak było, dopóki nie
    # doszedł warunek na liczbę kolumn.
    assert len(rows["tools/track/crs.py"]) == DRIFT_COLUMNS - 1, rows


# --- wyrocznia: drzewo robocze musi być zielone BEZ mutacji ----------------------

#: DLACZEGO TE DWA TESTY ISTNIEJĄ.
#:
#: Całe narzędzie stoi na jednym zdaniu: „zestaw padł, czyli mutacja została wykryta".
#: Zdanie jest prawdziwe tylko wtedy, gdy zestaw nie pada BEZ mutacji. Gdy przestaje,
#: narzędzie melduje 100 % zabić — a sto procent wygląda jak sukces, nie jak awaria.
#: Zdarzyło się to dwa razy: OOM (02.09.2026) i własna kasacja pliku przygotowująca
#: drzewo (05.09.2026, opis w `neutralise_own_tests`). Pierwszy raz kosztował 16 z 20
#: fałszywych zabić, drugi — cały wynik `m7_report.py`: „31/31 zabitych" przy dziewięciu
#: mutacjach, które ręcznie wstawione zestaw przepuszcza.


def test_przygotowanie_drzewa_zdejmuje_testy_narzedzia_nie_kasujac_pliku():
    """Zaślepka zamiast `os.remove`: ścieżka zostaje, testów nie ma.

    Kasacja pliku była poprawna dopóty, dopóki żadna bramka nie patrzyła na drzewo
    jako całość. `test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie`
    właśnie tak patrzy, a cztery miejsca w `reports/` wymieniają ten plik z nazwy.
    """
    with tempfile.TemporaryDirectory() as root:
        tests = os.path.join(root, "tools", "tests")
        os.makedirs(tests)
        own = os.path.join(tests, "test_mutation_sweep.py")
        with open(own, "w", encoding="utf-8") as handle:
            handle.write("def test_cokolwiek():\n    assert True\n")
        inny = os.path.join(tests, "test_all.py")
        with open(inny, "w", encoding="utf-8") as handle:
            handle.write("def test_inny():\n    assert True\n")

        zwrot = sweep.neutralise_own_tests(root)

        assert zwrot == own, zwrot
        # 1. Plik ZOSTAJE — to jest cała różnica wobec wersji, która go kasowała.
        assert os.path.isfile(own), "przygotowanie skasowało plik, który raporty cytują"
        # 2. Ale nie ma w nim ani jednego testu — inaczej zaślepka nie robi swojego.
        tresc = open(own, encoding="utf-8").read()
        assert "def test_" not in tresc, tresc
        assert ast.parse(tresc).body and isinstance(
            ast.parse(tresc).body[0], ast.Expr), "zaślepka ma być samym docstringiem"
        # 3. Żaden inny plik nie jest ruszony.
        assert open(inny, encoding="utf-8").read() == "def test_inny():\n    assert True\n"


def test_ten_plik_jest_wymieniony_w_raportach_wiec_nie_wolno_go_kasowac():
    """Powód zaślepki, zmierzony na drzewie, a nie przepisany z pamięci.

    Gdyby żaden raport tej ścieżki nie wymieniał, zaślepka byłaby ostrożnością bez
    przyczyny i ten test by o tym powiedział — zamiast pozwolić jej trwać jako
    obrzędowi po nieaktualnym zdarzeniu.
    """
    igla = "`tools/tests/test_mutation_sweep.py`"
    trafienia = []
    katalog = os.path.join(ROOT, "reports")
    for name in sorted(os.listdir(katalog)):
        if not name.endswith(".md"):
            continue
        if igla in open(os.path.join(katalog, name), encoding="utf-8").read():
            trafienia.append(name)
    assert trafienia, (
        "żaden raport nie wymienia już tego pliku — zaślepka straciła powód, "
        "sprawdź, czy zamiast niej nie wystarczy kasacja")


def test_przeglad_odmawia_pomiaru_gdy_czyste_drzewo_nie_jest_zielone():
    """`baseline_problem` mówi „nie" dokładnie w tych trzech przypadkach, w których ma.

    Kontrola negatywna jest tu WBUDOWANA: pierwszy przypadek to drzewo zielone i on
    musi dać `None`. Bez niego funkcja zwracająca zawsze komunikat przechodziłaby
    trzy czwarte tego testu i zatrzymałaby każdy przegląd świata.
    """
    zielone = sweep.baseline_problem("/nieistotne", 1, run=lambda *_: (True, [], 0))
    assert zielone is None, zielone

    czerwone = sweep.baseline_problem(
        "/nieistotne", 1,
        run=lambda *_: (False, ["test_kazda_sciezka_wymieniona_w_raporcie:"], 1))
    assert czerwone is not None
    assert "PADA w czystym drzewie" in czerwone, czerwone
    assert "test_kazda_sciezka_wymieniona_w_raporcie:" in czerwone, czerwone

    nieznane = sweep.baseline_problem(
        "/nieistotne", 1, run=lambda *_: (None, ["<zabity sygnałem, kod -9>"], -9))
    assert nieznane is not None
    assert "nie doszedł do podsumowania" in nieznane, nieznane


def test_domyslny_dziennik_jest_jeden_na_przebieg_a_nie_jeden_na_maszyne():
    """Do 06.09.2026 domyślną ścieżką była jedna nazwa dla całej maszyny.

    To nie było „dwa przebiegi sobie przeszkadzają", tylko **mieszanie wyników**:
    `sweep` czyta wynik z CAŁEGO dziennika, więc raport przebiegu na jednym module
    dostawał sekcję modułu, którego ten przebieg nie dotykał. Zmierzone wykonaną
    kontrolą — patrz `test_obcy_wpis_w_dzienniku_trafia_do_raportu_jesli_go_nie_odsiac`.

    Nazwa zależy od trzech rzeczy, które rozstrzygają, CZEGO przebieg dotyczy:
    commita, klas operatorów i zawężenia `--only`.
    """
    baza = sweep.default_journal("abc1234", ("operator", "prog"), "lod_paths.py")
    assert baza != sweep.default_journal("abc1234", ("operator", "prog"), "scan_gates.py")
    assert baza != sweep.default_journal("abc1234", ("operator", "prog", "logika"), "lod_paths.py")
    assert baza != sweep.default_journal("ffff999", ("operator", "prog"), "lod_paths.py")

    # KONTROLA NEGATYWNA WBUDOWANA: gdyby nazwa zależała od czegoś jeszcze —
    # choćby od kolejności klas albo od czasu — wznowienie nigdy by swojego
    # dziennika nie znalazło i „jeden na przebieg" znaczyłoby „nowy za każdym razem".
    assert baza == sweep.default_journal("abc1234", ("prog", "operator"), "lod_paths.py")
    assert baza == sweep.default_journal("abc1234", ("operator", "prog"), "lod_paths.py")


def test_obcy_wpis_w_dzienniku_trafia_do_raportu_jesli_go_nie_odsiac():
    """Dowód, że problem jest realny, a nie teoretyczny — i po co jest odmowa.

    Ten test opisuje zachowanie `read_journal` + `report`, czyli dokładnie tę drogę,
    którą idzie `sweep`. Gdyby kiedyś ktoś uznał odmowę za nadgorliwość, ten test
    pokazuje, co się dzieje bez niej.
    """
    def wpis(plik, wiersz):
        return {"id": f"{plik}:{wiersz}:100", "plik": plik, "wiersz": wiersz,
                "rozstrzygniete": True, "przezyla": True, "wykonana": True,
                "opis": "wpis", "rodzaj": "operator", "bylo": "<", "jest": "<=",
                "padly": [], "ile_padlo": 0, "kod": 0}

    with tempfile.TemporaryDirectory() as tmp:
        dziennik = os.path.join(tmp, "wspolny.jsonl")
        with open(dziennik, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(wpis("tools/blender/lod_paths.py", 10)) + "\n")
            handle.write(json.dumps(wpis("tools/track/detail_layout.py", 5)) + "\n")

        wyniki = sweep.read_journal(dziennik)
        assert len(wyniki) == 2, wyniki
        tekst = sweep.report(wyniki, "test")
        assert "tools/track/detail_layout.py" in tekst, (
            "raport przebiegu na lod_paths.py nie wymienia obcego modułu — jeśli to "
            "się zmieniło, odmowa z `main` może być już niepotrzebna i trzeba to "
            "sprawdzić, a nie zakładać")


def test_odmowa_patrzy_na_plik_wpisu_a_nie_na_jego_tresc():
    """Kryterium „obcy" to plik spoza zbioru przebiegu — nic więcej.

    Wpis o tym samym pliku, choćby z innego commita, obcym NIE jest: to jest
    wznowienie i ma działać. Wpis o innym pliku obcym JEST, nawet gdy wygląda
    poprawnie pod każdym innym względem.
    """
    pliki = {"tools/blender/lod_paths.py"}
    swoj = {"plik": "tools/blender/lod_paths.py"}
    obcy = {"plik": "tools/track/detail_layout.py"}
    bez_pola = {}

    assert swoj.get("plik") in pliki
    assert obcy.get("plik") not in pliki
    # Wpis bez pola `plik` liczy się jako obcy — nie da się go przypisać do przebiegu,
    # a milcząca zgoda wpuściłaby do raportu coś, czego nikt nie umie nazwać.
    assert bez_pola.get("plik") not in pliki

# --- 6.B19: wpis dziennika niesie commit, wznowienie z obcego drzewa jest odmówione --


def test_check_one_records_the_commit_it_ran_on():
    """Wpis dziennika musi nieść `commit`, obok `id` — to jest samo ładunek 6.B19.

    `id` to `plik:wiersz:przesunięcie bajtowe` i sam w sobie NIE mówi, z jakiego
    drzewa pochodzi — dwie różne mutacje z dwóch różnych commitów mogą wypaść pod
    tym samym przesunięciem. Bez pola `commit` w samym wpisie nie ma jak tego
    rozstrzygnąć później, choćby dziennik czytać ręcznie.
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "a.py")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("x = 1\n")
        mutation = sweep.Mutation("a.py", 1, 4, 5, "1", "2", "prog")

        original_run_suite = sweep.run_suite
        sweep.run_suite = lambda *_a, **_kw: (False, [], 0)  # zestaw "złapał" mutację
        try:
            entry = sweep.check_one(tmp, mutation, 5, "abcdef1")
        finally:
            sweep.run_suite = original_run_suite

        assert entry["commit"] == "abcdef1", entry
        assert entry["id"] == mutation.id, entry


def _dziennik_z_wpisem(sciezka, commit):
    return {
        "id": "tools/blender/lod_paths.py:28:0", "commit": commit,
        "plik": "tools/blender/lod_paths.py", "wiersz": 28,
        "rozstrzygniete": True, "przezyla": False, "wykonana": True,
        "opis": "wpis testowy", "rodzaj": "operator", "bylo": "==", "jest": "!=",
        "padly": ["jakis_test"], "ile_padlo": 1, "kod": 1,
    }


def test_resume_refuses_a_journal_written_on_another_tree():
    """Pokaz wprost: dziennik zapisany na jednym drzewie, wznowienie próbowane na
    drugim (6.B19) — narzędzie ma ODMÓWIĆ, nie policzyć cudzy wynik jako swój.

    `--only` zawęża do jednego modułu, żeby dowód był tani: bez mutowania choćby
    jednej linii i bez `collect()` po całym repozytorium.
    """
    with tempfile.TemporaryDirectory() as tmp:
        journal = os.path.join(tmp, "dziennik.jsonl")
        with open(journal, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(_dziennik_z_wpisem(
                "tools/blender/lod_paths.py", "0000000")) + "\n")

        done = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
             "--only", "tools/blender/lod_paths.py", "--journal", journal, "--list"],
            capture_output=True, text=True)

        assert done.returncode == 2, (done.stdout, done.stderr)
        assert "innego drzewa" in done.stderr, done.stderr
        assert "0000000" in done.stderr, done.stderr


def test_resume_still_works_when_the_journal_is_from_the_same_tree():
    """Kontrola pozytywna do testu wyżej — obowiązkowa, bo strażnik, który odrzuca
    wszystko bez wyjątku, przeszedłby połowę tego zadania i nazywałby się gotowy.

    Dziennik zapisany na TYM SAMYM commicie, co uruchomienie, ma dalej wznawiać.
    """
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        journal = os.path.join(tmp, "dziennik.jsonl")
        with open(journal, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(_dziennik_z_wpisem(
                "tools/blender/lod_paths.py", commit)) + "\n")

        done = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
             "--only", "tools/blender/lod_paths.py", "--journal", journal, "--list"],
            capture_output=True, text=True)

        assert done.returncode == 0, (done.stdout, done.stderr)
        assert "wznowienie z" in done.stdout, done.stdout
        assert "innego drzewa" not in done.stderr, done.stderr


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

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
import os
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
    assert len(found) == 2, [m.describe() for m in found]
    assert all(m.line == 2 for m in found), [m.describe() for m in found]


def test_assignment_is_not_a_comparison():
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
    cache = {}
    for mutation in sweep.collect():
        path = os.path.join(ROOT, mutation.path)
        if path not in cache:
            with open(path, encoding="utf-8") as handle:
                cache[path] = handle.read()
        mutation.apply(cache[path])


def test_every_mutation_still_parses():
    # Mutacja, która nie parsuje, wywala przebieg i liczy się jako zabita — czyli
    # ZAWYŻA pokrycie. To najkosztowniejsza możliwa cicha awaria tego narzędzia.
    cache = {}
    for mutation in sweep.collect():
        path = os.path.join(ROOT, mutation.path)
        if path not in cache:
            with open(path, encoding="utf-8") as handle:
                cache[path] = handle.read()
        ast.parse(mutation.apply(cache[path]))


def test_there_is_something_to_sweep():
    # Bez tego cztery testy wyżej przechodziłyby po pustej liście.
    found = sweep.collect()
    assert len(found) > 500, f"tylko {len(found)} mutacji — generator przestał generować"
    kinds = {m.kind for m in found}
    assert kinds == {"operator", "prog"}, kinds


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

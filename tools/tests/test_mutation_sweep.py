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
import contextlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mutation_sweep as sweep  # noqa: E402


def _dziennik_testu(etykieta):
    """Sciezka dziennika, ktorej nie dzieli z nami ZADEN inny przebieg — 6.D172.

    Nazwy tych dziennikow byly do 12.09.2026 wpisane z reki i STALE. Obrona, ktora
    mialy dac, jest opisana w docstringu `_sweep_cli`: przebieg z dziennikiem
    domyslnym czytalby plik zostawiony przez czyjs poprzedni pomiar i moglby na nim
    odmowic (6.B19), czyli test padalby od stanu maszyny, nie od kodu. Rozumowanie
    bylo trafne, a obrona objela wylacznie przebiegi KOLEJNE — nie rownolegle.

    Zmierzone 12.09.2026 na `tunnel-alignment` w PR #553: macierz startuje trzy
    joby w odstepie sekundy NA TEJ SAMEJ maszynie (CLAUDE.md §9), wiec dziela `/tmp`.
    L1_A 10:50:55Z i L1_B 10:50:56Z chodzily obok siebie szesc minut; L1_B padl na
    `[MUTACJE] PRZERWANE — dziennik /tmp/metro-mutacje-6b39-nieistniejacy.jsonl
    trzyma inny przebieg.` Odmowa zadzialala POPRAWNIE — wadliwa byla stala nazwa.

    Odtworzone celowo, a nie wywnioskowane z czasow: dwa rownolegle przebiegi
    `mutation_sweep.py` na jedna sciezke daja odmowe **6 razy na 6**, gdy roznia sie
    trescia (`--only camera_aim.py` kontra `--only lod_paths.py`), i **0 razy na 2**,
    gdy tresc jest ta sama. To drugie jest poprawne i wymagane przez
    `test_ta_sama_tresc_trafia_w_ten_sam_dziennik`: ta sama tresc MA trafiac w ten
    sam dziennik. Kolizja nie potrzebuje wiec pecha co do milisekundy — wystarcza
    dwa rownolegle procesy o roznej tresci, a modul wola `_sweep_6b39` dziewiec razy
    z roznymi argumentami.

    PID, a nie licznik ani znacznik czasu: ma byc stala w obrebie procesu (inaczej
    wznowienie w tym samym tescie zgubiloby plik) i rozna miedzy procesami, ktore
    moga chodzic naraz. Dwa joby na jednej maszynie to dwa procesy.
    """
    return os.path.join(tempfile.gettempdir(),
                        "metro-mutacje-%s-%d.jsonl" % (etykieta, os.getpid()))

ROOT = sweep.ROOT


#: 6.D90: pliki celów, na których kontrole tego modułu wolno zmieniać treść.
#: Kopia, nie oryginał — powód w `_cele_na_boku` niżej.
CEL_KONTROLNY = os.path.join("tools", "blender", "lod_paths.py")


@contextlib.contextmanager
def _cele_na_boku(cel=CEL_KONTROLNY, z_gitem=False):
    """Drzewo celów na kopii, z `sweep.ROOT` przestawionym na czas kontroli.

    **Po co, zmierzone 10.09.2026 przy 6.D90.** Trzy kontrole tego modułu — 6.B32
    i dwie z 6.B38 — zmieniały treść `tools/blender/lod_paths.py` W DRZEWIE GŁÓWNYM
    i przywracały ją w `finally`. Sonda `git status --porcelain` odpytywana co 50 ms
    przez cały przebieg zestawu (2158 testów) złapała `M tools/blender/lod_paths.py`
    w **11 próbkach**, czyli przez około pół sekundy plik był w drzewie zmieniony.
    Nikt tej zmiany nie popełnił i nikt jej nie zobaczy po fakcie, bo przywrócenie
    działa — ale równoległa kontrola czystości w tym oknie widzi naruszenie reguły 6.

    **Dlaczego kopia, a nie znacznik.** Pole „Wyjście" pozycji 6.D90 daje znacznik
    jako wariant awaryjny, „jeśli kopia jest niewykonalna". Jest wykonalna: wszystkie
    trzy kontrole czytają plik przez `sweep.ROOT` (`odcisk_tresci`, `targets`,
    `collect`), więc przestawienie tej jednej zmiennej kieruje je na kopię, nie
    zmieniając ani jednej asercji o zachowaniu narzędzia.

    **Czego to NIE zmienia:** `_biezacy_commit()` czyta `ROOT` tego modułu testowego,
    a nie `sweep.ROOT`, więc zdanie „HEAD stoi w miejscu" nadal dotyczy prawdziwego
    repozytorium — i tak ma być, bo to jest połowa tezy 6.B32.
    """
    zrodlo = os.path.join(ROOT, cel)
    with tempfile.TemporaryDirectory(prefix="metro-cele-") as bok:
        kopia = os.path.join(bok, cel)
        os.makedirs(os.path.dirname(kopia))
        shutil.copyfile(zrodlo, kopia)
        if z_gitem:
            # Kontrola 6.B32 o brudnym drzewie pyta `git diff --name-only HEAD`,
            # wiec kopia bez repozytorium nie odpowiedzialaby na jej pytanie wcale.
            # Repozytorium syntetyczne odpowiada, a prawdziwe zostaje czyste.
            for polecenie in (("init", "--quiet"),
                              ("config", "user.email", "test@example.invalid"),
                              ("config", "user.name", "test"),
                              ("add", "-A"),
                              ("commit", "--quiet", "-m", "baza")):
                gotowe = _git_w(bok, *polecenie)
                assert gotowe.returncode == 0, (polecenie, gotowe.stderr[-200:])
        zastane = sweep.ROOT
        sweep.ROOT = bok
        try:
            yield kopia
        finally:
            sweep.ROOT = zastane


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
         "--journal", _dziennik_testu("nieistniejacy")],
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
         "--journal", _dziennik_testu("nieistniejacy-6d18")],
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
         "--journal", _dziennik_testu("nieistniejacy-6d18b")],
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
    #
    # **Od 6.D204 na wyniku tej bramki stoi jeszcze jedno zdanie — i dolnego ostrza
    # mimo to NIE dostała, bo pomiar pokazał, że byłoby czwartym zdaniem o tym samym.**
    # Zdanie brzmi: mapy dwóch przebiegów tego samego commita różnią się czterema
    # kluczami katalogów próbnych, a nie szkodzi to nikomu **wyłącznie dlatego**, że te
    # katalogi leżą pod `tools/tests/` — tam, gdzie `was_executed` nigdy nie zagląda.
    # Pętla po PUSTEJ liście celów przechodzi bez ani jednego sprawdzenia i
    # „potwierdziłaby" to zerem (6.D27), więc ostrze wygląda na potrzebne.
    #
    # Zmierzone 14.09.2026 zawężeniem `targets()`, trzy razy, przy 71 celach w drzewie
    # i bazie 133/133: do 3 celów — **113/133**, czyli 20 testów tego modułu czerwonych;
    # do 55 — **131/133**, czyli 2; do 24 dobranych tak, by zachowały wszystkie trzy pliki
    # przypięte z NAZWY w `test_targets_cover_the_real_tools` — **129/133**, czyli 4.
    # Zawężenia, które zapala WYŁĄCZNIE ostrze na liczbie, nie udało się zbudować:
    # niezależnie od niego zapalają się `..._cover_the_real_tools` (zbiór nazw, nie
    # liczba — 6.D131), `test_zaden_cel_mutacji_nie_lezy_poza_kodem_narzedzi`
    # (`len(cele) > 20`, postawione dokładnie na tę pułapkę) i testy `--only`.
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


#: Piec modulow WYCIAGNIETYCH spod `bpy` w 6.B9 (#276) i 6.B13 (#284), zeby dalo sie
#: je testowac jednostkowo. Kazdy nadal WSPOMINA `bpy` — w funkcji, nie w ciele modulu
#: — wiec tekstowy `grep` liczy ich razem z wejsciami Blenderowymi: 15 wobec 10.
#:
#: **Lista jest utrzymywana recznie i to jest decyzja, nie zaniedbanie.** Rownosc
#: „nieosiagalne == importujace bpy w ciele modulu" NIE broni tych pieciu, i to jest
#: ZMIERZONE, nie zalozone: dopisanie `import bpy` na poziomie modulu do
#: `lod_paths.py` dodaje go do OBU zbiorow naraz, wiec rownosc zostaje spelniona,
#: a stary prog (11 < 31) tez przechodzi. Regres wraca wiec po cichu przez oba
#: strazniki i tylko lista imienna go zatrzymuje.
MODULY_WYCIAGNIETE_SPOD_BPY = (
    "tools/blender/lod_paths.py",
    "tools/blender/marker_gates.py",
    "tools/blender/scan_gates.py",
    "tools/blender/station_sections.py",
    "tools/blender/vehicle_fit.py",
)


def _bpy_na_poziomie_modulu(path):
    """Czy modul importuje `bpy` w SWOIM CIELE, a nie wewnatrz funkcji.

    Rozroznienie jest cala trescia tej pomocniczej: `import bpy` schowany w funkcji
    nie przeszkadza zaimportowac modulu, wiec sonda go nie odrzuca. Tekstowy `grep`
    za `import bpy` daje dzis **15** modulow, a nieosiagalnych jest **10** —
    piec roznicy to dokladnie moduly wyciagniete spod `bpy` w 6.B9 i 6.B13
    (`lod_paths.py`, `marker_gates.py`, `scan_gates.py`, `station_sections.py`,
    `vehicle_fit.py`). Bramka na `grep` zglaszalaby wiec pieciu poprawnych.
    """
    drzewo = ast.parse(open(os.path.join(ROOT, path), encoding="utf-8").read())
    for wezel in drzewo.body:
        if isinstance(wezel, ast.Import):
            if any(a.name.split(".")[0] == "bpy" for a in wezel.names):
                return True
        elif isinstance(wezel, ast.ImportFrom):
            if (wezel.module or "").split(".")[0] == "bpy":
                return True
    return False


def test_every_real_target_except_the_blender_entry_points_is_reachable():
    """Sonda nie moze wycinac modulow, ktore da sie przetestowac — i to jest
    WYPROWADZONE z drzewa, nie wpisane liczba.

    **Docstring przepisany 07.09.2026 (6.B45), a poprzednia wersja NIE byla
    nieprawdziwa — byla pomiarem bez daty.** Mowila „Zmierzone: 9 z 44 modulow
    `tools/` jest nieosiagalnych" i na dzien wpisania zgadzala sie co do sztuki.
    Sprawdzone na commicie, ktory ja wprowadzil::

        ff99d13 (03.09.2026)  celow 44   nieosiagalnych  9
        6bbbf37 (04.09.2026)  celow 55   nieosiagalnych 10
        d9d8709 (07.09.2026)  celow 63   nieosiagalnych 10

    Czyli w cztery dni celow przybylo dziewietnascie, a nieosiagalnych — jeden.
    Liczba w docstringu zestarzala sie po cichu, bo asercja stala na PROGU
    (`< len(targets()) // 2`, czyli 10 < 31): przechodzi przy 9, przy 10 i przy 30.

    **Co jest tu przybite od dzis.** Zbior nieosiagalnych rowna sie DOKLADNIE
    zbiorowi modulow importujacych `bpy` na poziomie modulu — zmierzone 07.09.2026:
    10 = 10, zbiory identyczne. Rownosc nie wymaga utrzymywania zadnej liczby, bo
    rosnie razem z drzewem, i lapie sonde odrzucajaca modul, ktory `bpy` w ciele nie
    importuje, oraz odwrotnie.

    **Czego rownosc NIE lapie, i to jest zmierzone, nie zalozone.** Pierwsza wersja
    tego docstringu twierdzila, ze rownosc broni pieciu modulow wyciagnietych spod
    `bpy` w 6.B9 i 6.B13. Kontrola pokazala, ze nie: `import bpy` dopisany na poziomie
    modulu do `lod_paths.py` wchodzi do OBU zbiorow naraz, wiec rownosc zostaje
    spelniona, a prog (11 < 31) tez przechodzi. Regres przeszedlby przez oba
    strazniki, i dlatego tych pieciu broni osobna asercja na liscie imiennej
    (`MODULY_WYCIAGNIETE_SPOD_BPY`) — utrzymywanej recznie, bo wyprowadzic jej
    z drzewa nie da sie: „modul, ktory kiedys importowal bpy i przestal" nie jest
    wlasnoscia dzisiejszego drzewa.
    """
    unreachable = sweep.unreachable_modules(sweep.targets())
    assert unreachable, "sonda nie znalazla nic — na tej maszynie bpy jest dostepne?"
    for path, reason in unreachable.items():
        assert "bpy" in reason, f"{path}: nieoczekiwany powod {reason}"

    # Klucze `unreachable` sa TAKIE, jak podana lista — `sweep.targets()` zwraca
    # sciezki bezwzgledne. Normalizuje OBIE strony, bo porownanie sciezki bezwzglednej
    # ze wzgledna daje zbiory rozlaczne przy identycznej tresci: ten sam blad zlapal
    # mnie dzis przy 6.B39 (`targets()` wobec `Mutation.path`) i jest wart komentarza,
    # a nie tylko poprawki.
    cele = [os.path.relpath(c, ROOT) for c in sweep.targets()]
    nieosiagalne = {os.path.relpath(k, ROOT) if os.path.isabs(k) else k
                    for k in unreachable}
    z_bpy = {p for p in cele if _bpy_na_poziomie_modulu(p)}
    assert nieosiagalne == z_bpy, (
        "sonda odrzuca inny zbior niz moduly importujace `bpy` w swoim ciele; "
        f"tylko sonda: {sorted(nieosiagalne - z_bpy)}, "
        f"tylko import: {sorted(z_bpy - nieosiagalne)}")


    # **Piec modulow z 6.B9 i 6.B13 musi zostac OSIAGALNE.** Rownosc wyzej tego nie
    # pilnuje i sprawdzilem to kontrola: `import bpy` dopisany na poziomie modulu do
    # `lod_paths.py` wchodzi do OBU zbiorow naraz, wiec rownosc zostaje prawdziwa,
    # a prog (11 < 31) tez przechodzi — regres przeszedlby przez oba strazniki.
    wrocily = sorted(set(MODULY_WYCIAGNIETE_SPOD_BPY) & nieosiagalne)
    assert not wrocily, (
        "modul wyciagniety spod `bpy` w 6.B9/6.B13 znow importuje go w swoim ciele "
        f"i przestal byc testowalny: {wrocily}")

    # Prog zostaje, i nie jest po zmianie zbedny: rownosc wyzej jest spelniona takze
    # wtedy, gdy OBA zbiory sa puste, wiec sama nie odroznia „sonda widzi tyle, ile
    # ma" od „bpy jest na tej maszynie dostepne i nie ma czego odrzucac".
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
        # 2. Ale nie ma w nim PRAWDZIWYCH testów — inaczej zaślepka nie robi swojego.
        #
        # **Asercja przepisana 07.09.2026 przy 6.B35, nie dopisana obok.** Poprzednia
        # wersja żądała, żeby zaślepka nie miała ANI JEDNEJ funkcji `test_` i była
        # „samym docstringiem" — i to właśnie ona przybijała usterkę: moduł testowy
        # bez strażnika `__main__` i bez ani jednego testu nie spełnia reguł, których
        # bramka `test_module_entrypoints.py` (6.D25) żąda od każdego `test_*.py`,
        # więc od jej scalenia kalibracja wyroczni widziała zestaw jako padający
        # w KAŻDYM czystym drzewie i przerywała przegląd kodem 2.
        #
        # Intencja zostaje ta sama: prawdziwej treści testów narzędzia w zaślepce
        # nie ma. Zmienia się to, co z tego wynika dla KSZTAŁTU pliku — zaślepka jest
        # dziś pełnoprawnym modułem z jednym testem tożsamości, a pilnuje tego
        # `test_the_stub_is_a_full_test_module_not_just_a_docstring`.
        tresc = open(own, encoding="utf-8").read()
        assert "def test_cokolwiek(" not in tresc, (
            "zaślepka niesie prawdziwy test z drzewa: " + tresc)
        wlasne = [w.name for w in ast.parse(tresc).body
                  if isinstance(w, ast.FunctionDef) and w.name.startswith("test_")]
        assert wlasne == ["test_this_file_is_the_stub_not_the_real_tests"], (
            "zaślepka ma nieść DOKŁADNIE jeden test — swojej tożsamości: " + repr(wlasne))
        assert isinstance(ast.parse(tresc).body[0], ast.Expr), (
            "zaślepka bez docstringu nie mówi, czym jest")
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

    **Przepisane 10.09.2026 (6.D106), a nie dopisane obok.** Od tej pozycji nazwa
    niesie też element unikatowy dla PROCESU, więc stabilna jest **w obrębie jednego
    przebiegu**, a nie między przebiegami — i to jest cała treść tego testu, bo
    `sweep` woła `default_journal` raz, a kod poniżej dwa razy. Wznowienia po
    domyślnej nazwie już nie ma; idzie ono przez jawne `--journal`. Dwa przebiegi
    o tych samych czterech członach mierzą to samo, ale dopisywały do JEDNEGO pliku
    i każdy czytał wynik z całego — więc oba raporty liczyły każdą mutację dwa razy.
    """
    baza = sweep.default_journal("abc1234", ("operator", "prog"), "lod_paths.py")
    assert baza != sweep.default_journal("abc1234", ("operator", "prog"), "scan_gates.py")
    assert baza != sweep.default_journal("abc1234", ("operator", "prog", "logika"), "lod_paths.py")
    assert baza != sweep.default_journal("ffff999", ("operator", "prog"), "lod_paths.py")

    # KONTROLA NEGATYWNA WBUDOWANA: kolejność klas nie ma prawa zmieniać nazwy,
    # a dwa wywołania W TYM SAMYM PROCESIE muszą dać ten sam plik — inaczej `sweep`
    # zapisywałby gdzie indziej, niż czyta. Element procesu jest liczony RAZ przy
    # imporcie właśnie po to; gdyby liczył się przy każdym wywołaniu, te dwa wiersze
    # padłyby i „jeden na przebieg" znaczyłoby „nowy za każdym wywołaniem".
    assert baza == sweep.default_journal("abc1234", ("prog", "operator"), "lod_paths.py")
    assert baza == sweep.default_journal("abc1234", ("operator", "prog"), "lod_paths.py")


def _sciezka_z_innego_procesu(wyrazenie):
    """Wartość wyrażenia policzona w OSOBNYM procesie Pythona.

    Element procesu jest liczony przy imporcie modułu, więc różnicy między
    przebiegami nie da się zobaczyć inaczej niż uruchamiając drugi proces.
    Podproces, a nie `importlib.reload`: przeładowanie w tym samym procesie
    dałoby nowy znacznik, ale nie dowiodłoby niczego o dwóch przebiegach.
    """
    kod = ("import sys; sys.path.insert(0, %r)\n"
           "import mutation_sweep as sweep\n"
           "print(%s)\n" % (os.path.dirname(os.path.abspath(sweep.__file__)),
                             wyrazenie))
    wynik = subprocess.run([sys.executable, "-c", kod],
                           capture_output=True, text=True)
    assert wynik.returncode == 0, wynik.stderr
    return wynik.stdout.strip()


def _trzymaj_zamek(sciezka):
    """Podproces, który bierze zamek na `sciezka` i trzyma go, aż go ubijemy."""
    proces = subprocess.Popen(
        [sys.executable, "-c",
         "import sys, time\n"
         "sys.path.insert(0, %r)\n"
         "import mutation_sweep as sweep\n"
         "stan, uchwyt = sweep.zajmij_dziennik(%r)\n"
         "print(stan, flush=True)\n"
         "time.sleep(120)\n"
         % (os.path.dirname(os.path.abspath(sweep.__file__)), sciezka)],
        stdout=subprocess.PIPE, text=True)
    stan = proces.stdout.readline().strip()
    assert stan == "wziety", (
        "podproces nie wzial zamka na start: %r — reszta testu mierzylaby co innego"
        % stan)
    return proces


def test_dwa_przebiegi_tego_samego_commita_dostaja_TEN_SAM_dziennik_i_drugi_ODMAWIA():
    """Nazwa wraca do czterech członów, a rozdziela ZAMEK — 6.D123.

    **Przepisany, a nie dopisany obok.** Do 11.09.2026 ten test żądał, żeby dwa
    procesy dostały ŚCIEŻKI RÓŻNE: 6.D106 rozdzielało przebiegi nazwą, bo dwa
    przeglądy o tych samych czterech członach dopisywały do jednego pliku, a
    `read_journal` powtórzeń nie odsiewa — oba raporty liczyły każdą mutację dwa razy.
    Ceną było zdjęcie wznowienia po nazwie domyślnej.

    6.D123 rozdziela je zamkiem, więc **ta sama ścieżka jest teraz WARUNKIEM**, a nie
    usterką: bez niej wznowienie nie miałoby czego znaleźć. Ochroną jest odmowa.
    """
    wyrazenie = ("sweep.default_journal('abc1234', ('operator', 'prog'), "
                 "'lod_paths.py')")
    pierwszy = _sciezka_z_innego_procesu(wyrazenie)
    drugi = _sciezka_z_innego_procesu(wyrazenie)
    assert pierwszy == drugi, (
        "dwa procesy dostaly ROZNE sciezki dziennika (%s, %s) — wznowienie po nazwie "
        "domyslnej znowu nie ma czego znalezc" % (pierwszy, drugi))
    assert os.path.basename(pierwszy).startswith("metro-mutacje-"), pierwszy

    # …a rozdziela je zamek. Mierzone na WLASNEJ sciezce, zeby nie dotknac dziennika,
    # ktory moze akurat lezec w `/tmp` po prawdziwym przebiegu.
    with tempfile.TemporaryDirectory() as katalog:
        sciezka = os.path.join(katalog, "dziennik.jsonl")
        trzyma = _trzymaj_zamek(sciezka)
        try:
            stan, uchwyt = sweep.zajmij_dziennik(sciezka)
            assert stan == "zajety", (
                "drugi przebieg wzial zamek trzymany przez pierwszy (%r) — dwa "
                "przebiegi znowu dopisuja do jednego dziennika" % stan)
            assert uchwyt is None, uchwyt
        finally:
            trzyma.kill()
            trzyma.wait()


def test_zamek_zwalnia_sie_po_SIGKILL_wlasciciela():
    """Pomiar, ktory rozstrzygnal 6.D123 — i bez ktorego zamek byl zakladem.

    Pole „Skonczone, gdy" tej pozycji zada tego wprost: zamek po procesie ubitym
    `SIGKILL` nie moze blokowac nastepnego przebiegu na stale. `SIGKILL` nie da sie
    obsluzyc, wiec zaden kod sprzatajacy sie nie wykona — zwolnienie musi przyjsc
    od jadra, ktore zamyka opisy plikow martwego procesu.

    **Mierzone, a nie wyczytane z dokumentacji.** Gdyby ten test kiedys zaczal padac
    — inny system plikow, `flock` emulowany po sieci — bedzie to znaczylo, ze warunek
    pozycji przestal zachodzic na tej maszynie, a nie ze test jest zepsuty. Wtedy
    nazwa dziennika ma wrocic do postaci unikatowej (`zamek=False`), ktora jest
    zachowana i przetestowana obok.
    """
    with tempfile.TemporaryDirectory() as katalog:
        sciezka = os.path.join(katalog, "dziennik.jsonl")
        trzyma = _trzymaj_zamek(sciezka)

        stan_przy_zywym, _ = sweep.zajmij_dziennik(sciezka)
        assert stan_przy_zywym == "zajety", (
            "zamek nie dziala nawet przy ZYWYM wlascicielu (%r) — nizej mierzylibysmy "
            "nie to, co trzeba" % stan_przy_zywym)

        trzyma.send_signal(signal.SIGKILL)
        trzyma.wait()

        stan_po, uchwyt = sweep.zajmij_dziennik(sciezka)
        try:
            assert stan_po == "wziety", (
                "zamek po `SIGKILL` wlasciciela nadal odmawia (%r) — na tej maszynie "
                "zostalby osierocony i blokowal kazdy nastepny przebieg; warunek "
                "6.D123 nie zachodzi i nazwa dziennika ma wrocic do unikatowej"
                % stan_po)
        finally:
            if uchwyt is not None:
                uchwyt.close()

        # Plik dziennika ZOSTAJE — i to jest powod, dla ktorego zamek idzie na niego,
        # a nie na osobny `.lock`: osobny plik bylby drugim smieciem bez zysku.
        assert os.path.isfile(sciezka), sciezka


def test_bez_flock_nazwa_dziennika_wraca_do_unikatowej():
    """Gałąź bez zamka jest WYKONYWANA, a nie tylko napisana.

    `fcntl` jest POSIX-owy i na Windowsie go nie ma. Bez parametru `zamek` ta gałąź
    byłaby kodem, którego nikt nigdy nie uruchomił — a taki kod jest w tym projekcie
    tym samym, co komentarz obiecujący zachowanie.
    """
    argumenty = ("abc1234", ("operator",), "x.py", "")
    z_zamkiem = sweep.default_journal(*argumenty, zamek=True)
    bez_zamka = sweep.default_journal(*argumenty, zamek=False)

    assert z_zamkiem != bez_zamka, (z_zamkiem, bez_zamka)
    assert os.path.basename(bez_zamka).endswith(
        f"-{sweep.PROCES_ZNACZNIK}.jsonl"), bez_zamka
    assert not os.path.basename(z_zamkiem).endswith(
        f"-{sweep.PROCES_ZNACZNIK}.jsonl"), z_zamkiem
    # Człon treści zostaje wspólny w obu: mówi człowiekowi w `/tmp`, czego plik dotyczy.
    assert os.path.basename(bez_zamka).startswith(
        os.path.basename(z_zamkiem)[:-len(".jsonl")]), (z_zamkiem, bez_zamka)

    # I że domyślna gałąź na TEJ maszynie idzie przez zamek — inaczej cała reszta
    # tej pozycji byłaby wyłączona i nikt by tego nie zobaczył.
    assert sweep.ZAMEK_DOSTEPNY is True
    assert sweep.default_journal(*argumenty) == z_zamkiem

    stan, uchwyt = sweep.zajmij_dziennik(bez_zamka, dostepny=False)
    assert (stan, uchwyt) == ("bez_zamka", None), (stan, uchwyt)
    assert not os.path.exists(bez_zamka), (
        "gałąź bez zamka utworzyła plik — a nie ma po co, skoro niczego nie trzyma")


def test_zajety_i_bez_zamka_to_DWIE_rozne_odpowiedzi():
    """Zlanie ich w `None` dałoby przebieg, który po cichu dzieli plik z innym.

    „Nie ma czym zamykać" puszcza przebieg dalej (nazwa jest wtedy unikatowa),
    „ktoś inny trzyma" jest ODMOWĄ. Jedna wartość na oba znaczyłaby, że maszyna bez
    `fcntl` dostaje zachowanie maszyny z zajętym dziennikiem albo odwrotnie — a to
    druga z tych pomyłek jest usterką z 6.D106, tylko wróconą tylnymi drzwiami.
    """
    with tempfile.TemporaryDirectory() as katalog:
        sciezka = os.path.join(katalog, "dziennik.jsonl")
        trzyma = _trzymaj_zamek(sciezka)
        try:
            zajety, _ = sweep.zajmij_dziennik(sciezka)
            bez, _ = sweep.zajmij_dziennik(sciezka, dostepny=False)
        finally:
            trzyma.kill()
            trzyma.wait()
    assert zajety == "zajety" and bez == "bez_zamka", (zajety, bez)
    assert zajety != bez


def test_zamek_stoi_przed_pierwszym_ZAPISEM_do_dziennika():
    """Granica jest zapis, nie odczyt — i to jest wynik kontroli, ktora wyszla ZIELONA.

    **Czego ten test NIE pilnuje i dlaczego.** Pierwszy komentarz przy zamku mowil
    „przed pierwszym CZYTANIEM, pozniej byloby za pozno". KN-6 przeniosla wywolanie
    za `read_journal` i dala **125/125**: zmiana niczego nie psuje, bo `read_journal`
    nic nie zapisuje. Gdy dwa przebiegi czytaja pusty dziennik naraz, zamek i tak
    przepuszcza jeden, a drugiemu odmawia, zanim ktorykolwiek dopisze wiersz.
    Twierdzenie bylo nieprawdziwe, wiec zostalo poprawione, a nie przybite.

    **Co ma znaczenie naprawde.** Zamek musi stac przed `sweep`, bo to `sweep`
    dopisuje wiersze. Zamek wziety po nim zostawia okno, w ktorym oba przebiegi maja
    juz wpisy w jednym pliku — usterke z 6.D106. Kolejnosc liczona z AST, bo komentarz
    cytujacy nazwe funkcji wygladalby przy szukaniu napisu tak samo jak wywolanie.
    """
    import ast as _ast

    drzewo = _ast.parse(open(sweep.__file__, encoding="utf-8").read())
    glowna = next(w for w in drzewo.body
                  if isinstance(w, _ast.FunctionDef) and w.name == "main")

    def wiersze(nazwa):
        return [w.lineno for w in _ast.walk(glowna)
                if isinstance(w, _ast.Call)
                and getattr(w.func, "id", getattr(w.func, "attr", None)) == nazwa]

    zamki = wiersze("zajmij_dziennik")
    sweepy = wiersze("sweep")
    assert zamki, "`main` nie wola `zajmij_dziennik` ani razu"
    assert sweepy, (
        "`main` nie wola `sweep` — ten test przestal mierzyc to, co mowi")
    assert min(zamki) < min(sweepy), (
        "zamek brany w wierszu %d, a `sweep` wola sie juz w %d — pierwszy dopis idzie "
        "do dziennika, ktorego nikt nie trzyma" % (min(zamki), min(sweepy)))


def test_uchwyt_zamka_jest_MODULOWY_bo_flock_zyje_z_otwartym_opisem():
    """Zmienna lokalna zwolniłaby zamek natychmiast po sprawdzeniu — zmierzone.

    **To nie jest przewidywanie.** Pierwsza próba tej pozycji wołała
    `zajmij_dziennik` dwa razy pod rząd, nie trzymając wyniku pierwszego wywołania,
    i **oba razy dostała `"wziety"`** — bo uchwyt pierwszego był już zebrany przez
    GC, a `flock` znika razem z zamknięciem opisu pliku. Wyglądało to dokładnie jak
    zamek, który nie działa.

    Stąd `_UCHWYT_ZAMKA` na poziomie modułu i stąd ten test: sprawdza, że `main`
    przypisuje uchwyt do czegoś, co przeżyje wyjście z funkcji.
    """
    with tempfile.TemporaryDirectory() as katalog:
        sciezka = os.path.join(katalog, "dziennik.jsonl")
        stan_a, uchwyt_a = sweep.zajmij_dziennik(sciezka)
        assert stan_a == "wziety", stan_a
        stan_b, _ = sweep.zajmij_dziennik(sciezka)
        assert stan_b == "zajety", (
            "drugi zamek w TYM SAMYM procesie przeszedl przy trzymanym pierwszym — "
            "`flock` przestal wiazac opisy plikow")
        uchwyt_a.close()
        stan_c, uchwyt_c = sweep.zajmij_dziennik(sciezka)
        assert stan_c == "wziety", (
            "po zamknieciu uchwytu zamek nadal odmawia — nie zwalnia sie wcale")
        uchwyt_c.close()

    zrodlo = open(sweep.__file__, encoding="utf-8").read()
    assert "global _UCHWYT_ZAMKA" in zrodlo, (
        "`main` nie przypisuje uchwytu do zmiennej modulowej — zamek zwolni sie "
        "przy pierwszym zbieraniu smieci, a przebieg bedzie myslal, ze go trzyma")
    assert "stan_zamka, _UCHWYT_ZAMKA = zajmij_dziennik(journal)" in zrodlo, zrodlo[:0]


#: Dwie mapy pokrycia RÓŻNIĄCE SIĘ jednym kluczem — najmniejsze wejście, na którym
#: mechanizm wspólnej nazwy pośredniej w ogóle ma co zepsuć. Treść jest tu istotna:
#: gdyby oba napisy były identyczne, przeplot dwóch strumieni nie zmieniłby ANI JEDNEGO
#: bajtu i plik wyszedłby czytelny — co jest całym wyjaśnieniem, dlaczego 6.D106 nie
#: odtworzyło zepsucia w pięciu próbach (6.D191).
#:
#: **Mapa A jest DUŻO większa od B i to też jest treścią, a nie wygodą.** Pierwsza wersja
#: tego wejścia miała obie mapy tej samej długości — i wyszła ZIELONA, bo obie zaczynają
#: się tym samym prefiksem (`{"wersja": 1, "commit": …`), a dłuższy pisarz nadpisał
#: krótszego co do bajtu. Zepsucie wymaga, żeby pisarz, który jest DALEJ, dopisywał za
#: końcem tego, co zapisał drugi: wtedy między nimi zostaje dziura wypełniona zerami.
MAPA_PISARZA_A = {"wersja": 1, "commit": "abc1234",
                  "pokrycie": {"tools/a%02d.py" % i: [1, 2, 3] for i in range(20)}}
MAPA_PISARZA_B = {"wersja": 1, "commit": "abc1234", "pokrycie": {"tools/b.py": [9]}}


def _dwaj_pisarze(posredni_a, posredni_b, cel):
    """Dwaj pisarze mapy pokrycia, przeplecieni DETERMINISTYCZNIE. Zwraca `(stan, replace)`.

    **Bez zegara, bez bariery i bez drugiego procesu — i to jest cała wartość tego
    wejścia.** Dwa procesy dają przeplot, w który trzeba TRAFIĆ, więc jego nietrafienie
    nie znaczy nic (dokładnie błąd, który 6.D191 znalazło w pomiarze 6.D106). Dwa uchwyty
    na jednej ścieżce, otwarte w `"w"`, mają dokładnie to, co ma para procesów: **własne,
    niezależne offsety i obcięcie przy otwarciu**. Przeplot jest tu więc wymuszony,
    a nie wylosowany, i wychodzi ten sam, ilekroć się go uruchomi.

    `posredni_a == posredni_b` odtwarza nazwę sprzed 10.09.2026; różne — dzisiejszą.
    """
    napis_a = json.dumps(MAPA_PISARZA_A)
    napis_b = json.dumps(MAPA_PISARZA_B)
    OGON = 16                      # ile A ma jeszcze do napisania, gdy wchodzi B
    assert len(napis_a) - OGON > len(napis_b), (
        "pisarz A nie jest DALEJ niż koniec pisarza B (%d-%d vs %d) — wtedy nie ma "
        "dziury i wejście przestaje ćwiczyć mechanizm, który ma ćwiczyć"
        % (len(napis_a), OGON, len(napis_b)))

    # Pisarz A jest prawie gotowy: zapisał wszystko poza ogonem.
    uchwyt_a = open(posredni_a, "w", encoding="utf-8")
    uchwyt_a.write(napis_a[:-OGON])
    uchwyt_a.flush()
    # Pisarz B wchodzi w środku jego pracy: `open(..., "w")` OBCINA plik do zera,
    # a pisarz A nadal stoi na swoim starym, DALEKIM offsecie.
    uchwyt_b = open(posredni_b, "w", encoding="utf-8")
    uchwyt_b.write(napis_b)
    uchwyt_b.flush()
    # A dopisuje ogon — od SWOJEGO offsetu, czyli daleko za końcem tego, co zapisał B.
    # Przy osobnych nazwach obie części sklejają się w poprawny JSON i to właśnie
    # odróżnia jeden wariant od drugiego: pisarze robią w obu DOKŁADNIE TO SAMO.
    uchwyt_a.write(napis_a[-OGON:])
    uchwyt_a.flush()
    uchwyt_a.close()
    uchwyt_b.close()

    stan = {}
    for kto, sciezka in (("A", posredni_a), ("B", posredni_b)):
        surowy = open(sciezka, "rb").read()
        try:
            json.loads(surowy.decode("utf-8"))
            stan[kto] = "czytelny"
        except (ValueError, UnicodeDecodeError):
            stan[kto] = "nieczytelny"

    zamiany = []
    for sciezka in (posredni_a, posredni_b):
        try:
            os.replace(sciezka, cel)
            zamiany.append("przeszla")
        except FileNotFoundError:
            zamiany.append("brak_pliku")
    return stan, zamiany


def test_wspolna_nazwa_posrednia_psuje_mape_NA_WEJSCIU_SYNTETYCZNYM():
    """ROZSTRZYGNIĘCIE 6.D191: zjawisko jest MOŻLIWE i odtwarza się za pierwszym razem.

    **Ten test jest przepisaniem dawnego zdania, a nie dopiskiem obok.** Do 13.09.2026
    stało tu i w `zapisz_pokrycie`, że unikatowa nazwa pośrednia jest ubezpieczeniem od
    zjawiska, którego „nie udało się odtworzyć w pięciu próbach". **Pomiar to obalił i
    pokazał, że tamte pięć prób mierzyło nie tę zmienną:** oba procesy pisały TĘ SAMĄ
    mapę, więc przeplot dwóch strumieni nie zmieniał ani jednego bajtu. Zmienną nie jest
    szerokość okna, tylko RÓŻNICA TREŚCI — i dlatego wejście niżej ma dwie różne mapy.

    Okno zresztą było szerokie, nie wąskie: sam zapis mapy ~50 MB trwa ~2,4 s (zmierzone),
    więc pięć prób z barierą startu trafiło w nie pięć razy na pięć i nic nie zobaczyło.

    **Druga połowa, przeoczona zupełnie**: przy wspólnej nazwie drugi `os.replace` nie ma
    czego przenieść, bo pierwszy już przeniósł. To nie jest rzadkie — to jest ZAWSZE, i to
    niezależnie od treści. Stara nazwa wywracała więc przebieg w stu procentach wypadków,
    a patrzono wyłącznie na plik docelowy. Liczby: `reports/6d191-nie-ta-zmienna.md`.
    """
    with tempfile.TemporaryDirectory() as katalog:
        cel = os.path.join(katalog, "pokrycie.json")

        # STARA nazwa: jedna dla obu pisarzy.
        wspolna = cel + ".czesciowy"
        stan, zamiany = _dwaj_pisarze(wspolna, wspolna, cel)
        assert stan["A"] == "nieczytelny", (
            "wspólna nazwa pośrednia dała plik CZYTELNY — wtedy zdanie o przeplocie "
            "dwóch strumieni o niezależnych offsetach przestaje mieć przedmiot: %s" % stan)
        assert zamiany == ["przeszla", "brak_pliku"], (
            "drugi `os.replace` przy wspólnej nazwie powinien nie mieć czego przenieść, "
            "a dał %s — to jest ta połowa usterki, która zachodzi ZAWSZE" % zamiany)

    with tempfile.TemporaryDirectory() as katalog:
        cel = os.path.join(katalog, "pokrycie.json")

        # DZISIEJSZA nazwa: element procesu rozdziela pisarzy. Dwa różne znaczniki
        # zamiast dwóch procesów, bo `PROCES_ZNACZNIK` liczy się raz przy imporcie;
        # że dwa procesy naprawdę dostają różne, mierzy test niżej.
        stan, zamiany = _dwaj_pisarze(cel + ".czesciowy-aaaaaaaa",
                                      cel + ".czesciowy-bbbbbbbb", cel)
        assert stan == {"A": "czytelny", "B": "czytelny"}, (
            "przy OSOBNYCH nazwach pośrednich któryś plik wyszedł nieczytelny: %s — "
            "wtedy dzisiejszy mechanizm nie chroni przed tym, przed czym ma chronić" % stan)
        assert zamiany == ["przeszla", "przeszla"], (
            "przy osobnych nazwach oba `os.replace` mają przejść, a dały %s" % zamiany)


def test_plik_posredni_mapy_pokrycia_jest_wlasny_dla_procesu():
    """Mapa pokrycia: plik POŚREDNI unikatowy, DOCELOWY wspólny — dwie decyzje.

    **Pośredni jest własny i od 6.D191 wiadomo, że to NAPRAWA, a nie ubezpieczenie** —
    i to rozróżnienie jest tu treścią. Dwa procesy pisały do jednego `<cel>.czesciowy`,
    obcinając go sobie przy otwarciu; zjawisko odtwarza dziś wejście syntetyczne
    w `test_wspolna_nazwa_posrednia_psuje_mape_NA_WEJSCIU_SYNTETYCZNYM`, za pierwszym
    razem i bez zegara. Ten test odpowiada za drugą połowę argumentu: że dwa PROCESY
    naprawdę dostają różne nazwy, bo tamten model używa dwóch napisów.

    **Docelowy zostaje wspólny** i to też jest zmierzone, a nie przeoczone: mapa
    kosztuje JEDEN PEŁNY PRZEBIEG ZESTAWU z licznikiem wierszy
    (`coverage_map(work, timeout * 4)`), a jest pamięcią podręczną dla commita.
    Uczynienie jej unikatową kasowałoby tę pamięć przy każdym przebiegu. Dzielenie
    jest bezpieczne, bo sweep ODMAWIA na brudnym drzewie (`dirty_sources`, kod 2),
    więc jeden commit znaczy jedno drzewo i jedną mapę.
    """
    cel = "sweep.sciezka_pokrycia('abc1234')"
    assert _sciezka_z_innego_procesu(cel) == _sciezka_z_innego_procesu(cel), (
        "plik DOCELOWY mapy różni się między procesami — pamięć podręczna commita "
        "przestała działać i każdy przebieg liczy mapę od nowa")

    posredni = "sweep.sciezka_pokrycia('abc1234') + '.czesciowy-' + sweep.PROCES_ZNACZNIK"
    pierwszy = _sciezka_z_innego_procesu(posredni)
    drugi = _sciezka_z_innego_procesu(posredni)
    assert pierwszy != drugi, (
        "plik POŚREDNI jest ten sam w dwóch procesach: %s" % pierwszy)
    assert pierwszy.startswith(_sciezka_z_innego_procesu(cel) + ".czesciowy-"), pierwszy

    # I że kod NAPRAWDĘ używa tej nazwy, a nie tylko test ją składa.
    zrodlo = open(sweep.__file__, encoding="utf-8").read()
    assert 'f"{path}.czesciowy-{PROCES_ZNACZNIK}"' in zrodlo, (
        "`zapisz_pokrycie` nie składa nazwy pliku pośredniego ze znacznika procesu")
    # Szukane jest PRZYPISANIE, a nie sam napis: komentarz przy tej podmianie cytuje
    # dawną postać `path + ".czesciowy"`, żeby powiedzieć, co było nie tak, i cytat
    # nie jest powrotem usterki. Pierwsza wersja tej asercji szukała samego napisu
    # i zapaliła się na własnym komentarzu.
    assert 'tymczasowy = path + ".czesciowy"' not in zrodlo, (
        "stała nazwa pliku pośredniego wróciła do `mutation_sweep.py` jako "
        "przypisanie, a nie cytat")


def test_znacznik_procesu_nie_jest_samym_pidem():
    """PID sam nie wystarcza i to nie jest ostrożność na zapas.

    W kontenerach numery procesów zaczynają się od małych liczb i powtarzają się
    między maszynami tej samej puli — a pula dzieli `/tmp`. Znacznik miesza więc
    PID z czasem w nanosekundach.
    """
    assert sweep.PROCES_ZNACZNIK != str(os.getpid()), sweep.PROCES_ZNACZNIK
    assert len(sweep.PROCES_ZNACZNIK) == sweep.PROCES_ZNACZNIK_ZNAKOW, (
        sweep.PROCES_ZNACZNIK)
    assert re.fullmatch(r"[0-9a-f]+", sweep.PROCES_ZNACZNIK), sweep.PROCES_ZNACZNIK


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


#: Dwie tresci TEJ SAMEJ DLUGOSCI. Rowna dlugosc jest tu warunkiem, nie ozdoba:
#: CPython uznaje `.pyc` za wazny po parze `(mtime w sekundach, rozmiar)`, wiec
#: mutacja krotsza albo dluzsza unieważnia bajtkod sama z siebie i pulapki nie ma.
BAZA_LAB = 'F0_N = "248900.0"\n'
MUTACJA_LAB = 'F0_N = "251389.0"\n'


def _laboratorium_bajtkodu(katalog):
    """`mod.py` i `use.py`, ktory go importuje — najmniejsza scena pulapki 6.D102."""
    assert len(BAZA_LAB) == len(MUTACJA_LAB), (len(BAZA_LAB), len(MUTACJA_LAB))
    with open(os.path.join(katalog, "mod.py"), "w", encoding="utf-8") as uchwyt:
        uchwyt.write(BAZA_LAB)
    with open(os.path.join(katalog, "use.py"), "w", encoding="utf-8") as uchwyt:
        uchwyt.write("import mod\nprint(mod.F0_N)\n")


def _co_sie_wykonalo(katalog):
    """Wartosc, ktora NAPRAWDE zobaczyl import — a nie ta, ktora lezy w pliku."""
    wynik = subprocess.run([sys.executable, "use.py"], cwd=katalog,
                           capture_output=True, text=True)
    assert wynik.returncode == 0, wynik.stderr
    return wynik.stdout.strip()


def _zastaw_pulapke(katalog):
    """Podmienia tresc `mod.py` NIE ruszajac pary `(mtime, rozmiar)`.

    Czas ustawiany jest jawnie przez `os.utime`, a nie brany z zegara, i to jest
    to samo rozstrzygniecie co w `test_bytecode_staleness._zapisz`: warunek pulapki
    ma zachodzic ZAWSZE, a nie wtedy, gdy dwa zapisy trafia w te sama sekunde.
    Zmierzone 11.09.2026 na 200 przebiegach wersji zegarowej: 5 razy nie trafily.
    """
    sciezka = os.path.join(katalog, "mod.py")
    zegar = os.stat(sciezka).st_mtime
    with open(sciezka, "w", encoding="utf-8") as uchwyt:
        uchwyt.write(MUTACJA_LAB)
    os.utime(sciezka, (zegar, zegar))
    return sciezka


def test_detektor_starego_bajtkodu_widzi_oba_stany():
    """`bajtkod_przykrywa_zrodlo` na wejsciu syntetycznym, w obie strony.

    Bez drugiej strony reguła „zawsze `True`" spelnia pierwsza idealnie — a to jest
    dokladnie ten ksztalt bledu, ktory projekt tropi od 6.D27.
    """
    with tempfile.TemporaryDirectory() as katalog:
        sciezka = os.path.join(katalog, "mod.py")

        # Bajtkodu nie ma wcale.
        assert sweep.bajtkod_przykrywa_zrodlo(sciezka) is False, (
            "detektor widzi bajtkod tam, gdzie zadnego nie ma")

        _laboratorium_bajtkodu(katalog)
        assert _co_sie_wykonalo(katalog) == "248900.0"

        # Pulapka zastawiona: tresc inna, para `(mtime, rozmiar)` ta sama.
        _zastaw_pulapke(katalog)
        assert sweep.bajtkod_przykrywa_zrodlo(sciezka) is True, (
            "detektor nie widzi waznego `.pyc` przy zmienionej tresci — czyli nie "
            "widzi pulapki, dla ktorej powstal")
        assert _co_sie_wykonalo(katalog) == "248900.0", (
            "pulapka nie zadzialala na tej maszynie — wtedy to pomiar z 6.D102 "
            "trzeba przeliczyc, a nie ten test wylaczyc")

        # Ta sama tresc, ale czas zapisu inny: bajtkod przestaje przykrywac.
        pozniej = os.stat(sciezka).st_mtime + 10
        os.utime(sciezka, (pozniej, pozniej))
        assert sweep.bajtkod_przykrywa_zrodlo(sciezka) is False, (
            "detektor uznaje `.pyc` za wazny mimo innego czasu zrodla")


def test_usuniecie_bajtkodu_ODWRACA_pulapke():
    """Kontrola negatywna z pola „Skonczone, gdy" 6.D113 — obie strony w jednym tescie.

    Ta sama scena, ta sama mutacja, jedyna roznica to wywolanie `usun_bajtkod`.
    BEZ niego import wykonuje stara wartosc — czyli sweep zapisalby „PRZEZYLA"
    o mutacji, ktorej nie uruchomil. Z nim wykonuje sie to, co lezy w pliku.
    """
    with tempfile.TemporaryDirectory() as katalog:
        _laboratorium_bajtkodu(katalog)
        _co_sie_wykonalo(katalog)
        sciezka = _zastaw_pulapke(katalog)

        bez_czyszczenia = _co_sie_wykonalo(katalog)
        assert bez_czyszczenia == "248900.0", (
            "bez czyszczenia mutacja byla widoczna (%r) — scena nie odtwarza "
            "pulapki i reszta tego testu nie mierzylaby niczego" % bez_czyszczenia)

        assert sweep.usun_bajtkod(sciezka) is True, "nie bylo czego kasowac"
        z_czyszczeniem = _co_sie_wykonalo(katalog)
        assert z_czyszczeniem == "251389.0", (
            "po skasowaniu `.pyc` import nadal wykonuje stara wartosc (%r)"
            % z_czyszczeniem)

        # Drugie kasowanie nie ma czego skasowac i mowi to wprost, zamiast udawac.
        assert sweep.usun_bajtkod(os.path.join(katalog, "nie-ma.py")) is False


def test_check_one_pyta_o_bajtkod_ZANIM_go_skasuje():
    """Kolejnosc jest tresc: po skasowaniu `.pyc` nie ma juz czego zmierzyc.

    Gdyby `check_one` kasowal najpierw, pole `stary_bajtkod` bylo by ZAWSZE `False`
    i meldowaloby pomiar, ktorego nie zrobiono — 6.D27 w najczystszej postaci.
    """
    kolejnosc = []
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "a.py"), "w", encoding="utf-8") as uchwyt:
            uchwyt.write("x = 1\n")
        mutacja = sweep.Mutation("a.py", 1, 4, 5, "1", "2", "prog")

        zastane = (sweep.run_suite, sweep.bajtkod_przykrywa_zrodlo, sweep.usun_bajtkod)
        sweep.run_suite = lambda *_a, **_kw: (True, [], 0)
        sweep.bajtkod_przykrywa_zrodlo = lambda _p: kolejnosc.append("pytanie") or True
        sweep.usun_bajtkod = lambda _p: kolejnosc.append("kasowanie") or True
        try:
            wpis = sweep.check_one(tmp, mutacja, 5, "abcdef1")
        finally:
            (sweep.run_suite, sweep.bajtkod_przykrywa_zrodlo,
             sweep.usun_bajtkod) = zastane

    assert kolejnosc == ["pytanie", "kasowanie"], kolejnosc
    assert wpis["stary_bajtkod"] is True, wpis


def _docstringi(drzewo):
    """Węzły napisów, które są docstringami — moduł, klasa, funkcja."""
    out = set()
    for wezel in ast.walk(drzewo):
        if not isinstance(wezel, (ast.Module, ast.ClassDef,
                                  ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        ciało = getattr(wezel, "body", None)
        if not ciało:
            continue
        pierwszy = ciało[0]
        if (isinstance(pierwszy, ast.Expr) and isinstance(pierwszy.value, ast.Constant)
                and isinstance(pierwszy.value.value, str)):
            out.add(pierwszy.value)
    return out


#: Dziennik mieszany: dwa wpisy sprzed 6.D113 (bez pola), jeden zmierzony z wynikiem
#: `False` i jeden z wynikiem `True`. Cztery wpisy, TRZY stany.
DZIENNIK_MIESZANY = [
    {"opis": "sprzed 6.D113, pierwszy"},
    {"opis": "sprzed 6.D113, drugi"},
    {"opis": "zmierzony, czysto", "stary_bajtkod": False},
    {"opis": "zmierzony, pod bajtkodem", "stary_bajtkod": True},
]


def test_licznik_starego_bajtkodu_ma_TRZY_stany_a_nie_dwa():
    """6.D132: „nie zmierzono" nie jest tym samym, co „zmierzono i nie było".

    `dict.get` zwraca dla brakującego pola `None`, a `None` jest fałszywe — więc
    do 11.09.2026 wpis sprzed 6.D113 wpadał do tej samej kupki, co wpis zmierzony
    z wynikiem `False`, i nie zostawiał po sobie żadnego śladu.
    """
    podzial = sweep.podzial_starego_bajtkodu(DZIENNIK_MIESZANY)

    assert [w["opis"] for w in podzial[True]] == ["zmierzony, pod bajtkodem"], podzial[True]
    assert [w["opis"] for w in podzial[False]] == ["zmierzony, czysto"], podzial[False]
    assert [w["opis"] for w in podzial[sweep.NIEZMIERZONY]] == [
        "sprzed 6.D113, pierwszy", "sprzed 6.D113, drugi"], podzial[sweep.NIEZMIERZONY]

    # Reguła sprzed poprawki, wykonana tutaj, żeby różnica była POKAZANA, a nie
    # opowiedziana: `get` bez trzeciego stanu daje tę samą liczbę co dziś, ale
    # z innego zbioru — i o dwóch wpisach nie mówi nic.
    stara_regula = [w for w in DZIENNIK_MIESZANY if w.get("stary_bajtkod")]
    assert len(stara_regula) == len(podzial[True]) == 1, stara_regula
    assert len(DZIENNIK_MIESZANY) - len(stara_regula) == 3, (
        "stara reguła dzieliła cztery wpisy na 1 i 3, nie rozróżniając w tej trójce "
        "dwóch niezmierzonych od jednego zmierzonego")


def test_wartosc_null_w_polu_liczy_sie_jako_NIEZMIERZONA():
    """Ręcznie poprawiony dziennik może nieść `null`, a pomiaru za nim nie ma.

    `None` nie jest ani `True`, ani `False`; zaliczenie go do „zmierzono, nie było"
    byłoby dokładnie tym, co ta pozycja naprawia, tylko innym wejściem.
    """
    assert sweep.stan_starego_bajtkodu({"stary_bajtkod": None}) == sweep.NIEZMIERZONY, (
        "`null` w polu policzony jako pomiar — a pomiaru za nim nie ma")
    assert sweep.stan_starego_bajtkodu({}) == sweep.NIEZMIERZONY, (
        "wpis BEZ pola policzony jako pomiar — to jest cała usterka 6.D132")
    assert sweep.stan_starego_bajtkodu({"stary_bajtkod": False}) is False, (
        "zmierzone `False` przestało być odróżnialne od braku pomiaru")
    assert sweep.stan_starego_bajtkodu({"stary_bajtkod": True}) is True, (
        "zmierzone `True` przestało być rozpoznawane")


def test_wypis_podaje_MIANOWNIK_i_nazywa_wpisy_bez_pomiaru():
    """Wypis ma mówić „0 z 1", a nie samo „0" — bo samo „0" milczy o reszcie."""
    wiersze = sweep.wiersze_starego_bajtkodu(DZIENNIK_MIESZANY)
    razem = "\n".join(wiersze)

    assert "1 z 2 ZMIERZONYCH" in razem, (
        "wypis nie podaje mianownika: %r" % razem)
    assert "wpisów BEZ tego pomiaru: 2 z 4" in razem, (
        "wypis nie mówi, ilu wpisów licznik nie dotyczy: %r" % razem)
    assert "BEZ POMIARU   sprzed 6.D113, pierwszy" in razem, (
        "wypis nie nazywa wpisów bez pomiaru z osobna: %r" % razem)
    assert "STARY BAJTKOD zmierzony, pod bajtkodem" in razem, (
        "wypis zgubił wiersz z 6.D113: %r" % razem)


def test_wiersz_o_niezmierzonych_stoi_TAKZE_gdy_jest_ich_zero():
    """Ta sama zasada, którą 6.D113 zapisało dla wiersza wyżej.

    Milczenie o zerze jest nieodróżnialne od braku pomiaru. Drugi powód jest nowy:
    bez tego wiersza mianownik `z N zmierzonych` nie ma z czym się różnić.
    """
    czysty = [{"opis": "a", "stary_bajtkod": False},
              {"opis": "b", "stary_bajtkod": False}]
    wiersze = sweep.wiersze_starego_bajtkodu(czysty)
    razem = "\n".join(wiersze)

    assert "0 z 2 ZMIERZONYCH" in razem, razem
    assert "wpisów BEZ tego pomiaru: 0 z 2" in razem, (
        "przy zerze niezmierzonych wypis milczy — a milczenie znaczy to samo, co "
        "brak pomiaru: %r" % razem)
    assert "BEZ POMIARU" not in razem, (
        "przy zerze niezmierzonych nie ma czego wymieniać z osobna: %r" % razem)


def test_pusty_dziennik_nie_dzieli_przez_zero_i_mowi_ze_jest_pusty():
    """Zero wpisów to stan osiągalny (`--limit 0` po wznowieniu) i ma się nie wywrócić."""
    wiersze = sweep.wiersze_starego_bajtkodu([])
    razem = "\n".join(wiersze)
    assert "0 z 0 ZMIERZONYCH" in razem, razem
    assert "wpisów BEZ tego pomiaru: 0 z 0" in razem, razem


def test_main_wypisuje_licznik_PRZEZ_wspolna_funkcje_a_nie_po_swojemu():
    """Jeden czytnik tej reguły, nie dwa (6.B28).

    Gdyby `main` składał ten wypis u siebie, testy wyżej mierzyłyby funkcję, której
    przebieg nie woła — czyli byłyby bramką meldującą sprawdzenie, którego nie zrobiła.
    """
    zrodlo = open(os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
                  encoding="utf-8").read()
    drzewo = ast.parse(zrodlo)
    main = [w for w in ast.walk(drzewo)
            if isinstance(w, ast.FunctionDef) and w.name == "main"]
    assert len(main) == 1, "w module jest %d funkcji `main`" % len(main)

    wolane = {w.func.id for w in ast.walk(main[0])
              if isinstance(w, ast.Call) and isinstance(w.func, ast.Name)}
    assert "wiersze_starego_bajtkodu" in wolane, (
        "`main` nie woła `wiersze_starego_bajtkodu` — wypis powstaje gdzie indziej "
        "i testy tej funkcji nie mówią o tym, co widzi użytkownik")

    # Liczone z DRZEWA, nie z tekstu: docstring `wiersze_starego_bajtkodu` cytuje to
    # zdanie dwa razy — brzmienie dawne i dzisiejsze — i cytat nie jest kopią reguły.
    # Odsianie po samych komentarzach `#` tych dwóch wystąpień nie widzi.
    wystapienia = 0
    for wezel in ast.walk(drzewo):
        if not isinstance(wezel, ast.Constant) or not isinstance(wezel.value, str):
            continue
        if wezel in _docstringi(drzewo):
            continue
        if "starym bajtkodem" in wezel.value:
            wystapienia += 1
    assert wystapienia == 1, (
        "zdanie licznika stoi w kodzie (poza docstringami) %d razy — ma stać raz, "
        "w `wiersze_starego_bajtkodu`" % wystapienia)


def test_check_one_zostawia_katalog_bez_bajtkodu_zmutowanego_pliku():
    """Bez atrap: po przebiegu `.pyc` zmutowanego pliku ma nie lezec w drzewie."""
    with tempfile.TemporaryDirectory() as tmp:
        _laboratorium_bajtkodu(tmp)
        _co_sie_wykonalo(tmp)
        cache = __import__("importlib.util", fromlist=["util"]).cache_from_source(
            os.path.join(tmp, "mod.py"))
        assert os.path.isfile(cache), "scena nie ma bajtkodu, wiec nie ma czego kasowac"

        mutacja = sweep.Mutation("mod.py", 1, 8, 16, "248900.0", "251389.0", "prog")
        zastane = sweep.run_suite
        sweep.run_suite = lambda *_a, **_kw: (True, [], 0)
        try:
            sweep.check_one(tmp, mutacja, 5, "abcdef1")
        finally:
            sweep.run_suite = zastane

        assert not os.path.isfile(cache), (
            "`.pyc` zmutowanego pliku przetrwal przebieg — nastepna mutacja o tej "
            "samej dlugosci moze pojsc na nim")


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


#: Wartownik: `None` jako odcisk znaczy „wpis BEZ tego pola" (dziennik starszy niz
#: 6.B32), a brak argumentu — „policz prawdziwy odcisk dzisiejszego drzewa".
_BRAK = object()


def _dziennik_z_wpisem(sciezka, commit, odcisk=_BRAK):
    """Wpis dziennika POPRAWNY na dzisiejszym drzewie, o ile nie zepsuje sie pola.

    **Pole `odcisk` domyslnie prawdziwe, nie stale (6.B32).** Kazdy test tej rodziny
    psuje DOKLADNIE JEDNO pole — commit albo odcisk — a reszta wpisu ma byc dzisiejsza.
    Wpis ze stalym odciskiem sprawialby, ze testy 6.B19 wywracalyby sie na odmowie
    6.B32 i przestalyby mierzyc to, co mierza z nazwy. Zdarzylo sie to przy pisaniu
    6.B32: `test_resume_still_works_when_the_journal_is_from_the_same_tree` padl
    z komunikatem o INNEJ TRESCI, a mierzy zgodnosc commita.
    """
    if odcisk is _BRAK:
        odcisk = sweep.odcisk_tresci(sciezka)
    wpis = {
        "id": "tools/blender/lod_paths.py:28:0", "commit": commit,
        "plik": "tools/blender/lod_paths.py", "wiersz": 28,
        "rozstrzygniete": True, "przezyla": False, "wykonana": True,
        "opis": "wpis testowy", "rodzaj": "operator", "bylo": "==", "jest": "!=",
        "padly": ["jakis_test"], "ile_padlo": 1, "kod": 1,
    }
    if odcisk is not None:
        wpis["odcisk"] = odcisk
    return wpis


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


def test_the_stub_is_a_full_test_module_not_just_a_docstring():
    """Zaslepka narzedzia musi spelniac te same reguly, co kazdy modul testowy (6.B35).

    **Sprawdzane TYM SAMYM przyrzadem, ktory ja odrzucil.** Bramka
    `test_module_entrypoints.py` zada od kazdego `test_*.py` wykonywalnego strazniku
    `__main__` i delegacji do `test_all` — ale widzi tylko pliki LEZACE w drzewie,
    a zaslepka powstaje dopiero w drzewie roboczym przegladu. Od scalenia 6.D25 do
    07.09.2026 nikt wiec nie sprawdzal, ze tresc, ktora narzedzie tam wpisuje, te
    reguly spelnia — i nie spelniala: byla samym docstringiem, wiec kalibracja
    wyroczni widziala zestaw jako padajacy w KAZDYM czystym drzewie i przerywala
    przeglad kodem 2, zanim policzyl pierwsza mutacje.

    Ten test zamyka luke, w ktorej ta usterka mogla zyc: zaslepka jest tu czytana
    tak samo, jak bramka czyta prawdziwy modul, wiec nie da sie jej znowu zepsuc
    w sposob niewidoczny dla zestawu.
    """
    import test_module_entrypoints as WEJSCIA

    zrodlo = sweep.OWN_TESTS_STUB
    assert WEJSCIA.ma_straznik(zrodlo), (
        "zaslepka bez wykonywalnego strazniku `__main__` — kalibracja wyroczni "
        "zobaczy zestaw jako padajacy i przerwie przeglad kodem 2")
    assert WEJSCIA.DELEGACJA in zrodlo, (
        "zaslepka nie deleguje do wspolnego przebiegacza (" + WEJSCIA.DELEGACJA
        + "), a bramka 6.D25 tego zada od kazdego modulu testowego")
    drzewo = ast.parse(zrodlo)
    testy = [w.name for w in drzewo.body
             if isinstance(w, ast.FunctionDef) and w.name.startswith("test_")]
    assert testy, (
        "zaslepka bez ani jednej funkcji `test_` — `test_all.main(<plik>)` odmawia "
        "przy zerze testow, wiec straznik sam nie wystarcza")
    for wezel in drzewo.body:
        if isinstance(wezel, ast.FunctionDef) and wezel.name in testy:
            asercje = [w for w in ast.walk(wezel) if isinstance(w, ast.Assert)]
            assert asercje, (
                "test `" + wezel.name + "` w zaslepce nie ma ani jednej asercji — "
                "`assertion_gate` liczy taki test jako PORAZKE od #139")


# --- czy narzedzie w ogole dochodzi do konca WLASNA droga (6.B37) --------------


def _sweep_cli(*argumenty, journal_tag):
    """`mutation_sweep.py` uruchomiony jako PROCES, tak jak wola go czlowiek i CI.

    Dziennik na sciezke, ktorej nie ma: przebieg z domyslnym dziennikiem czytalby
    plik zostawiony przez czyjs poprzedni pomiar i moglby na nim odmowic (6.B19),
    czyli test padalby od stanu maszyny, nie od kodu.
    """
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
         *argumenty, "--journal",
         _dziennik_testu("brak-" + journal_tag)],
        capture_output=True, text=True, timeout=300)


def test_the_cli_lists_mutations_as_a_process_and_exits_zero():
    """6.B37: droga CLI konczy sie kodem 0 I podaje liczbe zlapanych mutacji.

    **Zalozenie pozycji 6.B37 jest w jednej trzeciej NIEPRAWDZIWE, i to jest
    zmierzone.** Pozycja mowi „zaden test nie uruchamia narzedzia jego wlasna droga
    (`main()`)". Pomiar na `origin/main` (przejscie po `ast`, funkcje wolajace
    `subprocess.run` na `mutation_sweep.py`) daje **piec** takich testow:
    `test_unknown_operator_class_is_rejected_by_the_cli`,
    `test_cli_lists_only_the_requested_class`,
    `test_only_is_a_substring_match_by_design_and_says_how_many_modules_it_caught`,
    `test_resume_refuses_a_journal_written_on_another_tree`,
    `test_resume_still_works_when_the_journal_is_from_the_same_tree`.
    Kod wyjscia drogi CLI byl wiec pilnowany; kontrola KN-3a (`--list` wraca 3)
    wywraca cztery testy, z ktorych trzy sa starsze od tej pozycji.

    Czego NIE bylo, zmierzone kontrola KN-3b (usuniety `print(f"razem: ...")`):
    **wiersza z liczba**. Stare testy filtruja wypis po przedrostku `tools/`, wiec
    podsumowania nie ogladaja wcale — KN-3b wywraca WYLACZNIE ten test. Do tego
    dochodzi porownanie dwoch niezaleznych licznikow tej samej rzeczy: liczby
    z naglowka `--only` i liczby wypisanych mutacji.

    **Usterki 6.B35 ten test nie lapie, i to tez jest zmierzone, nie zalozone.**
    `--list` wraca kodem 0 takze z zaslepka bez straznika, bo wychodzi z `main()`
    PRZED `add_worktree` i przed kalibracja wyroczni. Pomiar 07.09.2026, z trescia
    zaslepki podmieniona w drzewie na sam docstring:

        [MUTACJE] --only 'tools/blender/lod_paths.py' zlapalo 2 mutacji z 1 modul(ow)
        razem: 2
        kod: 0

    Prawdziwa luka po 6.B35 jest wiec NIE w kodzie wyjscia CLI, a w **drodze
    przygotowania drzewa**, ktorej zadna z piatki nie dotyka. Zajmuje sie nia
    `test_a_fresh_worktree_runs_the_stub_as_a_real_module` nizej i tylko ona
    spelnia pole „Skonczone, gdy" tej pozycji.
    """
    done = _sweep_cli("--only", "tools/blender/lod_paths.py", "--list",
                      journal_tag="6b37-list")
    assert done.returncode == 0, (
        "CLI narzedzia mutacyjnego nie dochodzi do konca wlasna droga (kod "
        + str(done.returncode) + "):\n" + done.stderr[-600:])
    linie = done.stdout.splitlines()
    naglowek = [w for w in linie if w.startswith("[MUTACJE] --only")]
    assert len(naglowek) == 1, done.stdout[-600:]
    razem = [w for w in linie if w.startswith("razem: ")]
    assert len(razem) == 1, (
        "wypis bez wiersza z liczba zlapanych mutacji: " + done.stdout[-600:])
    ile = int(razem[0].split(":")[1])
    # Liczba z wiersza podsumowania ma sie zgadzac z liczba wypisanych mutacji
    # ORAZ z liczba, ktora naglowek `--only` podal przed dotknieciem dziennika.
    # Dwa niezalezne liczniki tej samej rzeczy — rozjazd znaczy, ze filtr `--only`
    # dziala inaczej niz wypis.
    opisy = [w for w in linie if w.startswith("tools/")]
    assert ile == len(opisy), (str(ile), len(opisy), done.stdout[-600:])
    assert ile > 0, "przebieg nie zlapal ani jednej mutacji: " + done.stdout[-600:]
    assert str(ile) + " mutacji" in naglowek[0], (naglowek[0], ile)


def _stub_w_drzewie(zaslepka=None):
    """Prawdziwe `git worktree` przygotowane `add_worktree`, uruchomione wprost.

    Zwraca `(kod, liczba_testow, wypis)`. `zaslepka` podmienia `OWN_TESTS_STUB`
    na czas wywolania — sluzy kontroli przyrzadu, nie produkcji.
    """
    import test_module_entrypoints as WEJSCIA

    oryginal = sweep.OWN_TESTS_STUB
    # `git worktree remove` MUSI pojsc przed sprzatnieciem katalogu, inaczej git
    # zostaje z wpisem wskazujacym w nicosc i psuje kazdy nastepny przebieg
    # w tym repozytorium — dlatego `finally` jest wewnatrz `with`, nie odwrotnie.
    with tempfile.TemporaryDirectory(prefix="metro-6b37-") as katalog:
        drzewo = os.path.join(katalog, "w")
        try:
            if zaslepka is not None:
                sweep.OWN_TESTS_STUB = zaslepka
            sweep.add_worktree(drzewo)
            done = subprocess.run(
                [sys.executable, os.path.join("tools", "tests", "test_mutation_sweep.py")],
                cwd=drzewo, capture_output=True, text=True, timeout=300)
            return done.returncode, WEJSCIA._liczba_testow(done.stdout), done.stdout
        finally:
            sweep.OWN_TESTS_STUB = oryginal
            subprocess.run(["git", "worktree", "remove", "--force", drzewo],
                           cwd=ROOT, capture_output=True)


def test_a_fresh_worktree_runs_the_stub_as_a_real_module():
    """6.B37: usterka 6.B35 lapana w PRAWDZIWYM drzewie roboczym, nie na napisie.

    `test_the_stub_is_a_full_test_module_not_just_a_docstring` czyta `OWN_TESTS_STUB`
    jako napis. Ten test przechodzi cala droge przygotowania — `git worktree add`,
    `neutralise_own_tests`, uruchomienie modulu WPROST — czyli dokladnie to, co robi
    robotnik przegladu, i to na pliku LEZACYM w drzewie.

    **Kod wyjscia tu nie wystarcza, i to jest zmierzone.** Zaslepka bez straznika
    daje w drzewie kod **0** i PUSTY wypis, bo modul bez `__main__` uruchomiony
    wprost nie wykonuje niczego — to ta sama usterka, ktorej 6.D25 dala bramke.
    Rozstrzyga wiec LICZBA wykonanych testow, czytana tym samym `_liczba_testow`,
    ktorym czyta ja bramka 6.D25.
    """
    kod, ile, wypis = _stub_w_drzewie()
    assert kod == 0, "zaslepka w swiezym drzewie nie przechodzi (kod " + str(kod) + "):\n" + wypis[-600:]
    assert ile == 1, (
        "zaslepka w swiezym drzewie nie zameldowala DOKLADNIE jednego wykonanego "
        "testu (" + repr(ile) + ") — kalibracja wyroczni zobaczy zestaw jako "
        "padajacy i przerwie przeglad kodem 2:\n" + wypis[-600:])


def test_the_worktree_probe_can_tell_a_guardless_stub_apart():
    """Kontrola przyrzadu z testu wyzej — WYKONANA, nie opisana.

    Bramka, ktora swieci sie tak samo na tresci poprawnej i zepsutej, nie mierzy
    niczego. Tu podmieniana jest DOKLADNIE tresc, ktora usterka 6.B35 miala:
    sam docstring, bez straznika i bez testu. Przyrzad ma wtedy pokazac brak
    liczby testow, mimo kodu wyjscia 0.
    """
    kod, ile, wypis = _stub_w_drzewie(
        '"""Zaslepka: testy narzedzia mutacyjnego, zdjete na czas przegladu."""\n')
    assert kod == 0, (
        "spodziewany byl wlasnie kod 0 — o to cala rzecz: modul bez straznika "
        "NIE zdradza sie kodem wyjscia (kod " + str(kod) + ")")
    assert ile is None, (
        "przyrzad zameldowal " + repr(ile) + " wykonanych testow dla zaslepki "
        "bez straznika, czyli nie odroznia jej od poprawnej")
    assert wypis.strip() == "", (
        "modul bez straznika mial nie wypisac niczego: " + repr(wypis[-300:]))



# --- dziennik odroznia dwa przebiegi na TYM SAMYM commicie (6.B32) ---------------


def _sweep_z_dziennikiem(journal, *dodatkowe):
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
         "--only", "tools/blender/lod_paths.py", "--journal", journal, "--list",
         *dodatkowe],
        capture_output=True, text=True, timeout=300)


def _biezacy_commit():
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()


def test_resume_refuses_a_journal_written_on_other_content_of_the_same_commit():
    """Sedno 6.B32, i to jest przypadek, ktorego odmowa z 6.B19 NIE WIDZI.

    6.B19 dopisala do wpisu `commit` i odmawia, gdy dziennik niesie inny commit. Przy
    niezacommitowanej zmianie — a `--dirty` jest po to, zeby takie przebiegi robic —
    commit jest w obu przebiegach TEN SAM, a tresc mutowanego pliku juz nie. 6.B19
    nazwala to wprost jako to, czego nie lapie.

    Wpis ma wiec commit DZISIEJSZY (zeby odmowa z 6.B19 nie zadzialala i nie zaslonila
    pomiaru) i odcisk cudzy. Odmowa ma nazwac PLIK i OBA odciski, bo przy `--only` na
    katalog rozjazd dotyczy zwykle jednego modulu z kilkunastu.
    """
    with tempfile.TemporaryDirectory() as tmp:
        journal = os.path.join(tmp, "dziennik.jsonl")
        with open(journal, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(_dziennik_z_wpisem(
                "tools/blender/lod_paths.py", _biezacy_commit(),
                odcisk="0123456789abcdef")) + "\n")

        done = _sweep_z_dziennikiem(journal)

        assert done.returncode == 2, (done.stdout, done.stderr)
        assert "INNEJ TRESCI" in done.stderr, done.stderr
        assert "0123456789abcdef" in done.stderr, done.stderr
        assert "tools/blender/lod_paths.py" in done.stderr, done.stderr
        # Odmowa 6.B19 NIE zadzialala: commit sie zgadza, wiec komunikat o innym
        # drzewie nie ma prawa sie tu pojawic. Bez tej asercji test przechodzilby
        # takze wtedy, gdyby lapala go tamta odmowa — i mierzylby cudza prace.
        assert "innego drzewa" not in done.stderr, done.stderr


def test_resume_refuses_a_journal_entry_without_the_content_fingerprint():
    """Wpis BEZ pola `odcisk` jest starszy niz 6.B32 i nie da sie go zweryfikowac.

    Ta sama zasada, ktora 6.B19 postawila dla wpisu bez pola `commit`: milczaca zgoda
    wpuscilaby cudzy wynik pod dzisiejsza mutacje. Dziennik z przed tej poprawki jest
    wiec obcy — i lepiej, zeby narzedzie odmowilo, niz zeby policzylo go jako swoj.
    """
    with tempfile.TemporaryDirectory() as tmp:
        journal = os.path.join(tmp, "dziennik.jsonl")
        with open(journal, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(_dziennik_z_wpisem(
                "tools/blender/lod_paths.py", _biezacy_commit(), odcisk=None)) + "\n")

        done = _sweep_z_dziennikiem(journal)

        assert done.returncode == 2, (done.stdout, done.stderr)
        assert "INNEJ TRESCI" in done.stderr, done.stderr
        assert "None" in done.stderr, (
            "odmowa nie pokazuje, ze wpis nie ma odcisku wcale: " + done.stderr)


def test_resume_still_works_when_the_content_matches():
    """Kontrola drugiego kierunku, i to ONA jest tu wazniejsza od odmow wyzej.

    Straznik, ktory odrzuca kazdy dziennik, przeszedlby polowe tego zadania i nazywalby
    sie gotowy. Wpis z dzisiejszym commitem I dzisiejszym odciskiem ma dalej wznawiac.
    """
    with tempfile.TemporaryDirectory() as tmp:
        journal = os.path.join(tmp, "dziennik.jsonl")
        with open(journal, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(_dziennik_z_wpisem(
                "tools/blender/lod_paths.py", _biezacy_commit())) + "\n")

        done = _sweep_z_dziennikiem(journal)

        assert done.returncode == 0, (done.stdout, done.stderr)
        assert "PRZERWANE" not in done.stderr, done.stderr
        assert "wznowienie" in done.stdout, done.stdout


def test_the_fingerprint_reads_the_working_tree_not_the_worker_copy():
    """**Odcisk MUSI byc liczony z drzewa roboczego** — i to jest cala rzecz 6.B32.

    `collect` liczy mutacje z drzewa roboczego (`open(path)` wzgledem `ROOT`), a
    `check_one` stosuje je na kopii `git worktree add --detach HEAD`. Te dwa zrodla sa
    tym samym plikiem dopoki drzewo jest czyste, i ROZNYMI plikami przy `--dirty`.
    Odcisk liczony z kopii robotnika mialby wiec wartosc commita: bylby slepy dokladnie
    na przypadek, dla ktorego powstal.

    Test mierzy to bez zakladania drzewa roboczego: `odcisk_tresci` czyta plik pod
    `ROOT`, wiec zmiana pliku w drzewie roboczym MUSI zmienic odcisk, mimo ze `HEAD`
    stoi w miejscu.
    """
    plik = CEL_KONTROLNY
    commit_przed = _biezacy_commit()
    # 6.D90: zmiana idzie na KOPIE, nie na plik w drzewie glownym. Teza testu tego
    # nie rusza — `odcisk_tresci` czyta plik wzgledem `sweep.ROOT`, wiec kopia jest
    # dla niego dokladnie tym samym „drzewem roboczym", o ktore chodzi 6.B32.
    with _cele_na_boku() as kopia:
        with open(kopia, encoding="utf-8") as uchwyt:
            oryginal = uchwyt.read()
        przed = sweep.odcisk_tresci(plik)
        try:
            with open(kopia, "w", encoding="utf-8") as uchwyt:
                uchwyt.write(oryginal + "\n# 6.B32: zmiana bez commita\n")
            po = sweep.odcisk_tresci(plik)
        finally:
            with open(kopia, "w", encoding="utf-8") as uchwyt:
                uchwyt.write(oryginal)

        assert sweep.odcisk_tresci(plik) == przed, "przywrocenie pliku sie nie udalo"
    assert po != przed, (
        "odcisk nie zmienil sie po zmianie pliku w drzewie roboczym — czytnik siega "
        "gdzie indziej niz `collect`")
    assert _biezacy_commit() == commit_przed, (
        "commit sie zmienil, wiec test nie mierzy tego, co obiecuje")


def test_the_fingerprint_is_computed_once_per_file_not_once_per_mutation():
    """Koszt: raz na PLIK, nie raz na mutacje — i to jest asercja o kodzie, nie o czasie.

    Czas mierzy sie osobno (0,045 s na 2346 mutacji, raport §2) i nie da sie z niego
    zrobic bramki: prog czasowy na tak malej liczbie jest szumem. To, co da sie przybic,
    to KSZTALT — `odciski_przebiegu` zwraca slownik po plikach, a `main` wola go raz.
    """
    pliki = ["tools/blender/lod_paths.py", "tools/blender/lod_paths.py",
             "tools/track/build_alignment.py"]
    odciski = sweep.odciski_przebiegu(pliki)

    assert set(odciski) == set(pliki), odciski
    assert len(odciski) == 2, (
        "powtorzona sciezka policzona dwa razy: " + repr(odciski))
    for path, wartosc in odciski.items():
        assert len(wartosc) == sweep.ODCISK_ZNAKOW, (path, wartosc)
        assert wartosc == sweep.odcisk_tresci(path), path

    # **Asercja PRZEKIEROWANA 07.09.2026 przy 6.B38, nie oslabiona.** Stala tu
    # liczba WYSTAPIEN napisu `odciski_przebiegu(` w pliku i zadanie „dokladnie 2"
    # (definicja + jedno wolanie). Byl to PROXY, i to slaby w obie strony: przechodzil
    # takze wtedy, gdyby to jedno wolanie stalo WEWNATRZ petli po mutacjach — czyli
    # przy dokladnie tej usterce, przed ktora mial bronic — a zapalal sie przy
    # dolozeniu drugiego, poprawnego rozmowcy (pamiec `collect`, 6.B38).
    #
    # Nowa asercja mierzy ZACHOWANIE i jest MOCNIEJSZA: liczy prawdziwe wywolania
    # `odcisk_tresci` i zada, zeby na jedno `collect()` bylo ich tyle, ile CELOW —
    # nie tyle, ile mutacji. Wolanie w petli po mutacjach dalo by 2346 zamiast 63
    # i pada natychmiast, czego licznik tekstowy nie widzial.
    prawdziwy = sweep.odcisk_tresci
    wywolania = []
    sweep.odcisk_tresci = lambda path: (wywolania.append(path), prawdziwy(path))[1]
    try:
            sweep.collect()
    finally:
        sweep.odcisk_tresci = prawdziwy

    celow = len(sweep.targets())
    assert len(wywolania) == celow, (
        f"odcisk liczony {len(wywolania)} razy na {celow} celow — ma byc raz na PLIK, "
        f"nie raz na mutacje (tych jest dziś ponad 2000)")
    assert len(set(wywolania)) == celow, (
        "ten sam plik odciskany wiecej niz raz: "
        + repr([x for x in wywolania if wywolania.count(x) > 1][:3]))



def test_the_fingerprint_refusal_names_the_dirty_tree_when_that_is_the_cause():
    """Znalezisko na WLASNEJ poprawce: odmowa odciskow zaslaniala jasniejszy komunikat.

    Odmowa odciskow stoi w `main` PRZED `dirty_sources`, bo musi dzialac takze dla
    `--list` — tamta odmowa jest za galezia `--list`. Skutek, zmierzony: przy brudnym
    drzewie BEZ `--dirty` czytajacy dostawal komunikat o DZIENNIKU, choc prawdziwym
    problemem byla jego wlasna niezacommitowana zmiana, a jasniejszy komunikat
    `dirty_sources` nie dochodzil do glosu wcale.

    Przestawienie kolejnosci nie jest rozwiazaniem: zdjeloby odmowe odciskow z drogi
    `--list`, czyli z jedynej taniej drogi, ktora ja sprawdza. Komunikat NAZYWA wiec
    druga mozliwa przyczyne — i tylko wtedy, gdy ona faktycznie zachodzi.
    """
    plik = CEL_KONTROLNY.replace(os.sep, "/")
    # 6.D90: caly ten test chodzi po repozytorium SYNTETYCZNYM. `dirty_sources` pyta
    # `git diff --name-only HEAD` z `cwd=sweep.ROOT`, wiec kopia z wlasnym `.git`
    # odpowiada na to pytanie tak samo, a drzewo glowne zostaje czyste przez cale
    # okno — co dla tego akurat testu jest ta sama rzecz, ktora on sprawdza.
    with _cele_na_boku(z_gitem=True) as kopia:
        # 1. brudne drzewo bez `--dirty` -> zdanie jest, i wymienia plik z nazwy.
        zdanie = sweep.brudne_wyjasnienie([plik], dirty_flag=False)
        with open(kopia, encoding="utf-8") as uchwyt:
            oryginal = uchwyt.read()
        try:
            with open(kopia, "w", encoding="utf-8") as uchwyt:
                uchwyt.write(oryginal + "\n# 6.B32: zmiana bez commita\n")
            brudne = sweep.brudne_wyjasnienie([plik], dirty_flag=False)
            # 2. z `--dirty` przebieg jest ZAMIERZONY, wiec zdania nie ma — inaczej
            #    komunikat radzilby zacommitowac to, co ktos swiadomie zostawil.
            z_dirty = sweep.brudne_wyjasnienie([plik], dirty_flag=True)
        finally:
            with open(kopia, "w", encoding="utf-8") as uchwyt:
                uchwyt.write(oryginal)
        po_przywroceniu = sweep.brudne_wyjasnienie([plik], dirty_flag=False)

    assert "niezacommitowane zmiany" in brudne, brudne
    assert plik in brudne, brudne
    assert "--dirty" in brudne, brudne
    assert z_dirty == "", (
        "przy --dirty komunikat radzi zacommitowac zmiane, ktora ktos zostawil "
        "swiadomie: " + z_dirty)
    # 3. drzewo czyste -> zdania nie ma; bez tego kierunku zdanie dopisywane zawsze
    #    byloby szumem przy dzienniku z innego drzewa.
    assert zdanie == "", (
        "zdanie o brudnym drzewie dopisane przy drzewie czystym: " + zdanie)
    assert po_przywroceniu == "", "przywrocenie pliku sie nie udalo"


# --- mapa pokrycia liczona RAZ na commit i zapamietana (6.B36) -------------------


# --- 6.D204: czy mapa pokrycia jest pamiecia podreczna DZIALAJACA -------------------
#
# **TAK, i sprawdzaja to DWA testy nizej — nowej bramki ta pozycja NIE dolozyla, bo
# dolozyc nie bylo czego.** Zapisane, zeby nie zostalo napisane po raz trzeci.
#
# Pozycja postawila teze, ze mapa niesie cztery klucze katalogow probnych po cudzym
# przebiegu i przez to moze byc pamiecia bezuzyteczna. Nie niesie i nie ma jak: miedzy
# `coverage_map` a `zapisz_pokrycie` stoi `pokrycie_w_celach`. Teza opisuje WEJSCIE
# obciecia, a mowi o jego wyjsciu. Zmierzone 14.09.2026 na `8e9f830`:
#
#     SUROWA  (wyjscie `coverage_map`)   201 kluczy, 36 475 wierszy, 4 efemeryczne
#     OBCIETA (to, co idzie na dysk)      64 klucze,   8 711 wierszy, 0 efemerycznych
#     celow 71, z tego 7 zestaw nie uruchamia wcale; sciezek z mutacja 70, zadna
#     nie lezy pod `tools/tests/`, wiec przeciecie z kluczami efemerycznymi wynosi 0
#
# „Efemeryczne" znaczy tu KLUCZ, KTOREGO NIE MA NA DYSKU, a nie klucz o przedrostku
# piaskownicy. Roznica nie jest slowna: `tempfile` dobiera przyrostek z alfabetu
# z podkreslnikiem (`test_wiele__vlngc3k`), wiec sito po przedrostku gubi czesc
# piaskownic i przy pierwszym przebiegu sondy dalo ZERO zamiast czterech.
#
# **Droga zapis → odczyt → tozsamosc jest juz obstawiona, i to jest ZMIERZONE, nie
# przeczytane.** Napisalem byl trzecia bramke na te sama droge, zanim kontrola
# negatywna pokazala, ze dwie ponizej zapalaja sie na tych samych mutacjach:
# zapis gubiacy jeden klucz → `..._survives_a_round_trip` czerwony; odczyt przyjmujacy
# cudzy commit → `..._from_another_commit_is_refused` czerwony. Trzecia bramka byla wiec
# trzecim zdaniem o tym samym i zostala usunieta, a nie zostawiona „na wszelki wypadek".
# Pytanie to zadano zreszta juz raz, 07.09.2026, szesc dni przed wpisaniem pozycji —
# odpowiedzia bylo napisanie `pokrycie_w_celach` (`reports/pamiec-pokrycia.md`).


def test_the_remembered_map_survives_a_round_trip():
    """Zapis i odczyt nie gubia ani jednego wiersza.

    Zbiory nie sa serializowalne do JSON, wiec zapis idzie przez sortowane listy —
    a to jest dokladnie miejsce, w ktorym mapa mogla by po cichu stracic wiersz.
    """
    mapa = {
        "tools/blender/lod_paths.py": {1, 2, 28, 300},
        "tools/track/crs.py": {7},
    }
    with tempfile.TemporaryDirectory() as tmp:
        plik = os.path.join(tmp, "pokrycie.json")
        sweep.zapisz_pokrycie(plik, "aaaaaaa", mapa)

        assert sweep.wczytaj_pokrycie(plik, "aaaaaaa") == mapa
        # Wartosci maja byc ZBIORAMI po odczycie, nie listami: `was_executed` pyta
        # `mutation.line in coverage.get(path, ())`, a `in` na liscie jest liniowe
        # i przy 7582 wierszach robi z tego pytania petle.
        for wiersze in sweep.wczytaj_pokrycie(plik, "aaaaaaa").values():
            assert isinstance(wiersze, set), type(wiersze)


def test_a_remembered_map_from_another_commit_is_refused():
    """Kontrola negatywna, ktorej zadalo pole „Skonczone, gdy" pozycji 6.B36.

    Mapa z innego kodu przypisze etykiete „nieodpalona" mutacji, ktora sie odpalila —
    czyli klamstwo w strone „jest dziura w bramce", i to takie, ktorego nic w wyniku
    nie zdradza. Odrzucenie, nie proba naprawy.

    Commit siedzi WEWNATRZ pliku, nie tylko w nazwie: nazwe da sie zmienic jednym
    `mv`, a wtedy mapa z innego drzewa weszlaby jako swoja. Ta sama zasada, ktora
    6.B19 postawila dla wpisu dziennika i 6.B32 dla odcisku tresci — dowod
    pochodzenia jedzie razem z danymi. Ten test przenosi plik POD NAZWE innego
    commita wlasnie po to, zeby sprawdzic, ze nazwa nie wystarcza.
    """
    mapa = {"tools/blender/lod_paths.py": {28}}
    with tempfile.TemporaryDirectory() as tmp:
        swoj = sweep.sciezka_pokrycia("aaaaaaa").replace(tempfile.gettempdir(), tmp)
        sweep.zapisz_pokrycie(swoj, "aaaaaaa", mapa)

        assert sweep.wczytaj_pokrycie(swoj, "bbbbbbb") is None, (
            "mapa z innego commita zostala przyjeta")

        # Przeniesiona pod nazwe innego commita nadal jest odrzucana, bo commit
        # stoi w tresci.
        cudzy = sweep.sciezka_pokrycia("bbbbbbb").replace(tempfile.gettempdir(), tmp)
        os.replace(swoj, cudzy)
        assert sweep.wczytaj_pokrycie(cudzy, "bbbbbbb") is None, (
            "wystarczylo zmienic NAZWE pliku, zeby cudza mapa weszla jako swoja")
        # ...a pod swoim commitem dalej dziala, wiec odrzucenie nie jest odrzucaniem
        # wszystkiego.
        assert sweep.wczytaj_pokrycie(cudzy, "aaaaaaa") == mapa


def test_a_broken_or_older_remembered_map_is_refused_not_repaired():
    """Plik nieczytelny i plik o innym KSZTALCIE ida tam samo, co plik z innego drzewa.

    Mapa przeczytana „na tyle, na ile sie da" jest gorsza od braku mapy: brak daje
    etykiete „niezmierzone", ktora narzedzie mowi wprost, a mapa niepelna daje
    „nieodpalona" bez zadnego zastrzezenia.
    """
    with tempfile.TemporaryDirectory() as tmp:
        plik = os.path.join(tmp, "pokrycie.json")

        assert sweep.wczytaj_pokrycie(plik, "aaaaaaa") is None, "plik, ktorego nie ma"

        with open(plik, "w", encoding="utf-8") as handle:
            handle.write("{ to nie jest json")
        assert sweep.wczytaj_pokrycie(plik, "aaaaaaa") is None, "plik nieczytelny"

        with open(plik, "w", encoding="utf-8") as handle:
            json.dump({"wersja": sweep.POKRYCIE_WERSJA + 1, "commit": "aaaaaaa",
                       "pokrycie": {}}, handle)
        assert sweep.wczytaj_pokrycie(plik, "aaaaaaa") is None, "inna wersja ksztaltu"

        with open(plik, "w", encoding="utf-8") as handle:
            json.dump(["nie", "slownik"], handle)
        assert sweep.wczytaj_pokrycie(plik, "aaaaaaa") is None, "nie slownik"

        with open(plik, "w", encoding="utf-8") as handle:
            json.dump({"wersja": sweep.POKRYCIE_WERSJA, "commit": "aaaaaaa",
                       "pokrycie": "nie slownik"}, handle)
        assert sweep.wczytaj_pokrycie(plik, "aaaaaaa") is None, "pokrycie nie slownikiem"


def test_the_write_is_atomic_and_leaves_no_half_file():
    """Przebieg ubity w polowie zapisu nie zostawia mapy czytelnej i niepelnej.

    Dziennik jest linia-na-wpis i `read_journal` radzi sobie z ucietym wierszem.
    Mapa jest JEDNYM obiektem JSON: ucieta byla by nieczytelna — albo, gorzej,
    czytelna i niepelna. Dlatego zapis idzie przez plik tymczasowy i `os.replace`.
    """
    with tempfile.TemporaryDirectory() as tmp:
        plik = os.path.join(tmp, "pokrycie.json")
        sweep.zapisz_pokrycie(plik, "aaaaaaa", {"tools/track/crs.py": {1}})

        assert os.path.exists(plik)
        assert not os.path.exists(plik + ".czesciowy"), (
            "plik tymczasowy zostal po zapisie")
        # `os.replace` musi stac w kodzie: bez niego zapis jest zwyklym `open(w)`,
        # a ten obcina plik NA MIEJSCU i tworzy dokladnie stan polowiczny.
        zrodlo = open(os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
                      encoding="utf-8").read()
        at = zrodlo.index("def zapisz_pokrycie(")
        cialo = zrodlo[at:zrodlo.index("\ndef ", at + 10)]
        assert "os.replace(" in cialo, "zapis mapy nie jest atomowy"


def test_the_map_is_trimmed_to_mutation_targets():
    """Obciecie do celow mutacji — bo bez niego mapa nie jest stabilna miedzy przebiegami.

    **Zmierzone 07.09.2026, i to jest powod istnienia `pokrycie_w_celach`.** Dwie
    sondy z TEGO SAMEGO drzewa daly 162 klucze kazda i te same 25 732 wiersze, ale
    ROZNE zbiory kluczy: roznica to piaskownice, ktore zestaw zaklada sam —
    `tools/tests/test_dwa_<losowe>/...` i `tools/tests/test_pusty_<losowe>/...`
    (bramka 6.D25). Losowy przyrostek zmienia sie co przebieg. W ani jednym module
    wspolnym dla obu map zbiory wierszy sie NIE roznily.

    Obciecie nie zmienia zadnego werdyktu, bo `was_executed` pyta wylacznie
    o `mutation.path`, a ten jest zawsze celem — i to jest jedyny czytnik tej mapy.
    """
    surowa = {
        "tools/blender/lod_paths.py": {28},
        "tools/tests/test_all.py": {1, 2, 3},
        "tools/tests/test_dwa_4ydu68u1/test_dwa_testy.py": {1},
        "tools/tests/test_pusty_xfz551js/test_bez_zadnego_testu.py": {1},
    }
    obcieta = sweep.pokrycie_w_celach(surowa)

    assert "tools/blender/lod_paths.py" in obcieta, obcieta
    assert obcieta["tools/blender/lod_paths.py"] == {28}
    for klucz in surowa:
        if klucz.startswith("tools/tests/"):
            assert klucz not in obcieta, (
                "efemeryczna albo testowa sciezka zostala w mapie: " + klucz)

    # Kontrola przyrzadu: obciecie ma zostawiac CZESC, a nie wszystko wyrzucac.
    # Bez tej asercji `pokrycie_w_celach` zwracajace pusty slownik przeszlo by
    # wszystkie asercje wyzej.
    assert len(obcieta) == 1, obcieta
    # I ma czytac cele z `targets()`, a nie z listy wpisanej z pamieci.
    cele = {os.path.relpath(p, ROOT) for p in sweep.targets()}
    assert "tools/blender/lod_paths.py" in cele, "lod_paths.py przestal byc celem"
    assert not any(c.startswith("tools/tests/") for c in cele), (
        "cel mutacji lezy pod tools/tests/ — obciecie zaczelo by gubic prawdziwy modul")


# --- przyczyna pustego zbioru mutacji (6.B41) ---------------------------------------
#
# PO CO TA RODZINA. Do 07.09.2026 `main` mial na pusty zbior dwie galezie i zadna nie
# pytala, CO go oproznilo. Zmierzone przy 6.B32, drugim przebiegiem na czystym drzewie:
# `wznowienie z ...: 2 z 2 juz policzonych`, a potem `brak mutacji do sprawdzenia po
# odfiltrowaniu nieosiagalnych` i kod 1 — komunikat o przyczynie, ktora nie zachodzila,
# i kod „awaria" o przebiegu, ktory zrobil cala robote. Dla skryptu CI puszczajacego
# przeglad w petli do skutku to roznica miedzy „gotowe" i „awaria".
#
# CZEGO TE TESTY PILNUJA, a czego nie da sie zobaczyc po samym komunikacie: KOLEJNOSCI
# pytan. Przy zbiorze oproznionym przez wznowienie kazdy pozniejszy licznik tez jest
# zerem, wiec przyrzad pytajacy o filtr przed wznowieniem odpowiadalby „filtr" na kazdy
# taki przebieg — i wygladalby na dzialajacy, dopoki nikt nie wznowi kompletnego
# dziennika. Dwa pierwsze testy ida wiec po LICZNIKACH, a nie po napisie.


def _dziennik_kompletny(plik):
    """Wpisy dziennika dla WSZYSTKICH dzisiejszych mutacji jednego pliku.

    Buduje je z `mutations_for`, a nie z listy wpisanej z reki: identyfikator mutacji
    to `plik:wiersz:przesuniecie bajtowe`, wiec wpis wpisany na stale przestalby
    pasowac przy pierwszym dopisanym komentarzu w mutowanym pliku — i test „wznowienie
    zastalo wszystko policzone" cicho zmienilby sie w test „wznowienie zastalo czesc".
    """
    pelna = os.path.join(ROOT, plik)
    with open(pelna, encoding="utf-8") as uchwyt:
        mutacje = sweep.mutations_for(pelna, uchwyt.read())
    assert mutacje, f"{plik} nie ma dzisiaj ani jednej mutacji"
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.strip()
    odcisk = sweep.odcisk_tresci(plik)
    return [{
        "id": mutacja.id, "commit": commit, "odcisk": odcisk, "plik": mutacja.path,
        "wiersz": mutacja.line, "rozstrzygniete": True, "przezyla": False,
        "wykonana": True, "opis": mutacja.describe(), "rodzaj": mutacja.kind,
        "bylo": mutacja.was, "jest": mutacja.now, "padly": ["jakis_test"],
        "ile_padlo": 1, "kod": 1,
    } for mutacja in mutacje]


def test_pusty_zbior_po_wznowieniu_nie_klamie_o_filtrze_nieosiagalnych():
    """Sama usterka 6.B41, zadana licznikami: wznowienie wyprzedza filtr.

    Przy zbiorze oproznionym przez wznowienie liczniki PO limicie i PO filtrze tez sa
    zerami — dokladnie tak wygladalo drzewo, na ktorym padl pomiar z 6.B32. Przyrzad
    ma odpowiedziec „wznowienie", nie „filtr", i dac kod ZERO, bo przebieg zrobil
    wszystko, o co go proszono.
    """
    komunikat, kod = sweep.przyczyna_pustego_zbioru(
        2, 0, 0, 0, only="tools/blender/lod_paths.py",
        journal="/tmp/b41/d.jsonl", limit=0)

    assert kod == 0, (kod, komunikat)
    assert "wznowienie" in komunikat, komunikat
    assert "/tmp/b41/d.jsonl" in komunikat, komunikat
    assert "2" in komunikat, komunikat
    assert "nieosiagalnych" not in komunikat.replace("ą", "a"), (
        "komunikat nazywa filtr nieosiagalnych, ktory niczego nie odsial: " + komunikat)


def test_pusty_zbior_z_filtru_nieosiagalnych_dalej_mowi_o_filtrze():
    """Kontrola pozytywna do testu wyzej — obowiazkowa.

    Przyrzad, ktory na kazdy pusty zbior odpowiada „wznowienie", przeszedlby polowe
    tej pozycji i nazywalby sie gotowy. Gdy wznowienie NIE odsialo niczego (licznik po
    wznowieniu rowny zebranemu), a zero przyszlo dopiero po filtrze, przyczyna jest
    filtr — i kod zostaje 1, bo nie ma czego mierzyc.
    """
    komunikat, kod = sweep.przyczyna_pustego_zbioru(
        14, 14, 14, 0, only="tools/blender/glb_roundtrip.py", journal="/tmp/b41/d.jsonl")

    assert kod == 1, (kod, komunikat)
    assert "nieosiągalnych" in komunikat, komunikat
    assert "14" in komunikat, komunikat
    assert "wznowienie" not in komunikat, komunikat


def test_pusty_zbior_z_only_nazywa_only_a_nie_wznowienie():
    """Zbior pusty OD POCZATKU: `--only` nie dopasowalo pliku.

    Kod zostaje 1 i to jest swiadome: 6.B39 stoi wprost na tym, ze `--only` pasujace
    do niczego jest usterka wywolania. Komunikat ma podac WZORZEC, bo jedynym sygnalem
    w wypisie jest dzis `0 modul(ow)` z pusta lista nazw.
    """
    komunikat, kod = sweep.przyczyna_pustego_zbioru(
        0, None, None, None, only="tools/nie-ma-takiego-pliku.py",
        journal="/tmp/b41/d.jsonl")

    assert kod == 1, (kod, komunikat)
    assert "--only" in komunikat, komunikat
    assert "tools/nie-ma-takiego-pliku.py" in komunikat, komunikat
    assert "wznowienie" not in komunikat, komunikat

    bez_only, kod_bez = sweep.przyczyna_pustego_zbioru(0, None, None, None)
    assert kod_bez == 1, (kod_bez, bez_only)
    assert "--only" not in bez_only, (
        "przebieg BEZ --only oskarza --only o pusty zbior: " + bez_only)


def test_pusty_zbior_z_limitu_nazywa_limit():
    """Trzecia mozliwa przyczyna, wymieniona w polu „Wyjscie" pozycji 6.B41.

    `--limit` opróznia niepusty zbior tylko wartoscia ujemna (`found[:-1]` na zbiorze
    jednoelementowym), ale przyrzad ma nazywac przyczyne, a nie zgadywac, ktora jest
    prawdopodobna — i wlasnie dlatego pytanie o limit stoi PO wznowieniu, a nie przed.
    """
    komunikat, kod = sweep.przyczyna_pustego_zbioru(1, 1, 0, None, limit=-1)

    assert kod == 1, (kod, komunikat)
    assert "--limit" in komunikat, komunikat
    assert "-1" in komunikat, komunikat
    assert "wznowienie" not in komunikat, komunikat


def test_przyczyna_pustego_zbioru_odmawia_przy_niepustym_zbiorze():
    """Kontrakt przyrzadu: wolany tylko przy PUSTYM zbiorze.

    Cicha odpowiedz przy niepustym zbiorze byla by najgorsza forma awarii, jaka ten
    przyrzad umie: przebieg z robota do wykonania dostalby komunikat „brak mutacji"
    i wyszedl bez policzenia niczego. Wyjatek jest tu widoczny.
    """
    try:
        sweep.przyczyna_pustego_zbioru(14, 14, 14, 14)
    except ValueError as blad:
        assert "NIEPUSTYM" in str(blad), str(blad)
    else:
        raise AssertionError("przyrzad odpowiedzial przyczyna dla niepustego zbioru")


def test_wznowienie_ktore_policzylo_wszystko_konczy_sie_zerem():
    """Ta sama rzecz, ale DROGA NARZEDZIA (`main`), bo tam usterka mieszkala.

    Dziennik niesie wszystkie dzisiejsze mutacje modulu, wiec wznowienie oprozni zbior
    do zera. Bieg jest tani mimo braku `--list`: galaz pustego zbioru stoi PRZED
    `dirty_sources`, przed sonda nieosiagalnosci i przed kalibracja wyroczni, wiec ani
    jedno `git worktree add` ani jeden przebieg zestawu tu nie chodzi.
    """
    plik = "tools/blender/lod_paths.py"
    with tempfile.TemporaryDirectory() as tmp:
        journal = os.path.join(tmp, "dziennik.jsonl")
        with open(journal, "w", encoding="utf-8") as uchwyt:
            for wpis in _dziennik_kompletny(plik):
                uchwyt.write(json.dumps(wpis) + "\n")

        done = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
             "--only", plik, "--journal", journal, "--workers", "2", "--no-coverage"],
            capture_output=True, text=True)

    assert done.returncode == 0, (done.returncode, done.stdout, done.stderr)
    assert "już policzonych" in done.stdout, done.stdout
    assert "wznowienie" in done.stderr, done.stderr
    assert "nieosiągalnych" not in done.stderr, done.stderr
    # Kalibracja wyroczni to jeden pelny przebieg zestawu — gdyby galaz stanela za nia,
    # ten test kosztowalby minute i ta asercja to pokaze, zanim ktos zmierzy czas.
    assert "kalibracja" not in done.stdout, done.stdout


def test_filtr_nieosiagalnych_ktory_odsial_wszystko_konczy_sie_jedynka():
    """Kontrola pozytywna droga narzedzia: przyczyna „filtr" ma zostac przy kodzie 1.

    `glb_roundtrip.py` to wejscie Blenderowe — zestaw testow go nie zaimportuje, wiec
    filtr odsiewa WSZYSTKIE jego mutacje. Dziennik jest pusty, wiec wznowienie nie ma
    tu nic do rzeczy i przyczyna moze byc tylko jedna.
    """
    plik = "tools/blender/glb_roundtrip.py"
    with tempfile.TemporaryDirectory() as tmp:
        done = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
             "--only", plik, "--journal", os.path.join(tmp, "pusty.jsonl"),
             "--workers", "2", "--no-coverage"],
            capture_output=True, text=True)

    assert done.returncode == 1, (done.returncode, done.stdout, done.stderr)
    assert "po odfiltrowaniu nieosiągalnych" in done.stderr, done.stderr
    assert "wznowienie" not in done.stderr, done.stderr
    assert "kalibracja" not in done.stdout, done.stdout


# --- 6.B39: pusty zbior na drodze `--list` -----------------------------------------

def _sweep_6b39(*argv):
    """Narzedzie wolane jego wlasna droga (`main()`), nie przez import."""
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
         *argv, "--journal",
         _dziennik_testu("6b39-nieistniejacy")],
        capture_output=True, text=True)


def test_only_bez_trafien_z_lista_nie_konczy_sie_zerem():
    """6.B39: `--list` wychodzila ZEREM takze przy zbiorze pustym.

    Odmowa `brak mutacji do sprawdzenia` stoi ZA galezia `--list`, wiec wypisu nie
    dotyczyla wcale. Zmierzone 07.09.2026 na `b019436`::

        $ mutation_sweep.py --only tools/nie-ma-takiego-pliku.py --list
        razem: 0
        kod: 0

    Przebieg CI, ktory przez literowke zawezil `--only`, dostawal zielone zero
    i wyglad poprawnego przebiegu, ktory po prostu nie mial co robic.
    """
    done = _sweep_6b39("--only", "tools/nie-ma-takiego-pliku.py", "--list")

    assert done.returncode != 0, (done.returncode, done.stdout[-400:])
    assert "tools/nie-ma-takiego-pliku.py" in done.stderr, done.stderr[-400:]
    assert "nie dopasowało ani jednego pliku" in done.stderr, done.stderr[-400:]
    assert "razem: 0" not in done.stdout, done.stdout[-400:]


def test_zawezenie_trafione_w_plik_bez_mutacji_nie_mowi_ze_nie_trafilo():
    """Druga przyczyna pustego zbioru, i do 07.09.2026 komunikat o niej KLAMAL.

    `--only tools/blender/camera_aim.py --operators prog` dopasowuje DOKLADNIE JEDEN
    plik docelowy i daje zero mutacji, bo ten plik nie ma ani jednego progu. Komunikat
    mowil wtedy `nie dopasowało ani jednego pliku` — zdanie nieprawdziwe, bo dopasowal
    dokladnie jeden. To ta sama rodzina usterki co 6.B41: gałąź nazywajaca przyczyne,
    ktora nie zachodzi.

    Ze to nie przypadek teoretyczny, mowi pomiar z 07.09.2026: modulow bez ani jednej
    mutacji danej klasy jest od **2** (`operator`) do **36** (`przypisanie`) na **63**
    cele. Sam licznik mutacji tego nie odroznia, bo `pliki_przebiegu` wyprowadza sie
    ze zbioru mutacji — zero mutacji znaczy tam zawsze zero modulow.
    """
    done = _sweep_6b39("--only", "tools/blender/camera_aim.py",
                      "--operators", "prog", "--list")

    assert done.returncode != 0, (done.returncode, done.stdout[-400:])
    assert "dopasowało 1 plik" in done.stderr, done.stderr[-400:]
    assert "nie dopasowało ani jednego pliku" not in done.stderr, done.stderr[-400:]


def test_obie_drogi_podaja_te_sama_przyczyne_tego_samego_stanu():
    """Wlasnosc, po ktora przyrzad jest JEDEN: `--list` i przebieg pelny nie moga
    sie roznic w opisie tego samego stanu.

    Do 07.09.2026 roznily sie maksymalnie: jedna wychodzila kodem 0 bez slowa,
    druga kodem 1 z komunikatem. Rozdzielenie ich dalo by dwa czytniki tych samych
    licznikow, a dwa czytniki jednej rzeczy rozjezdzaja sie po cichu (6.B28).
    """
    z_lista = _sweep_6b39("--only", "tools/blender/camera_aim.py",
                         "--operators", "prog", "--list")
    bez_listy = _sweep_6b39("--only", "tools/blender/camera_aim.py",
                           "--operators", "prog")

    assert z_lista.returncode == bez_listy.returncode, (
        z_lista.returncode, bez_listy.returncode)
    assert z_lista.stderr.strip() == bez_listy.stderr.strip(), (
        z_lista.stderr, bez_listy.stderr)


def test_only_z_trafieniami_nadal_konczy_sie_zerem():
    """Kontrola ujemna z pola „Skonczone, gdy" pozycji, WYKONANA w zestawie.

    Odmowa zbudowana zbyt szeroko wywrocilaby cala droge `--list`, a testy odmowy
    zostalyby wtedy zielone. Trzy ksztalty zawezenia: katalog, podciag lapiacy dwa
    moduly (6.D18) i jeden plik.
    """
    # `tools/track/` ma 23 cele od 11.09.2026 (bylo 22 od 10.09.2026, 21 od 09.09.2026,
    # 20 od 07.09.2026, a wczesniej 19): doszly `tools/track/vertical_profile.py`
    # z 6.B44, `tools/track/osm_tile_cache.py` z 6.D62, `tools/track/stop_names.py`
    # z 6.D111 i `tools/track/apply_vertical.py` z 6.D120.
    # Ta liczba MIERZY drzewo, wiec rosnie razem z nim — nie jest progiem
    # i nie wolno jej zamienic na nierownosc, bo wtedy przestalaby odroznic
    # "zawezenie trafilo w katalog" od "zawezenie trafilo w cokolwiek".
    for wzorzec, ile_celow in (("tools/track/", 23), ("sweep.py", 2),
                               ("tools/blender/lod_paths.py", 1)):
        done = _sweep_6b39("--only", wzorzec, "--list")

        assert done.returncode == 0, (wzorzec, done.returncode, done.stderr[-300:])
        assert f"dopasowało {ile_celow} plik" in done.stdout, (wzorzec, done.stdout[:200])
        assert "razem: 0" not in done.stdout, (wzorzec, done.stdout[-200:])


def test_przyczyna_odroznia_zawezenie_nietrafione_od_trafionego_bez_mutacji():
    """Sam przyrzad, bez procesu: dwie przyczyny, dwa zdania, ten sam kod.

    Test na FUNKCJI, obok trzech na procesie, i to nie jest powtorzenie: proces
    dowodzi, ze `main` woła przyrzad w obu galeziach, a to dowodzi, ze przyrzad
    odroznia stany, ktorych `main` sam nie odrozni — bo `zebrane` jest w obu zerem.
    """
    nietrafione, kod_a = sweep.przyczyna_pustego_zbioru(
        0, None, None, None, only="zmyslony", dopasowane_pliki=0)
    trafione, kod_b = sweep.przyczyna_pustego_zbioru(
        0, None, None, None, only="zmyslony", dopasowane_pliki=3)

    assert kod_a == kod_b == sweep.KOD_NIC_DO_LICZENIA, (kod_a, kod_b)
    assert nietrafione != trafione
    assert "nie dopasowało ani jednego pliku" in nietrafione, nietrafione
    assert "dopasowało 3 plik" in trafione, trafione


# --- 6.B40: odcisk tresci przebiegu w nazwie dziennika ----------------------------

def test_dwie_tresci_na_tym_samym_commicie_maja_rozne_dzienniki():
    """6.B40: nazwa byla funkcja TRZECH rzeczy, a rozstrzygaly juz cztery.

    Po 6.B32 wpis dziennika niesie odcisk tresci i odmowa poprawnie odrzuca cudza
    tresc — ale nazwa pliku zostala funkcja commita, klas operatorow i `--only`,
    wiec dwa przebiegi na tym samym commicie i roznej tresci DZIELILY sciezke
    i drugi z nich konczyl sie odmowa zamiast pomiaru. Zmierzone 07.09.2026::

        czyste: /tmp/metro-mutacje-58804969c2a4.jsonl
        brudne: /tmp/metro-mutacje-58804969c2a4.jsonl     <- ta sama nazwa

    Docstring obiecywal wtedy „trzy rzeczy, ktore rozstrzygaja, CZEGO przebieg
    dotyczy" — i to ta rozbieznosc miedzy obietnica i dzialaniem byla trescia
    pozycji, nie sama odmowa (ona dziala i zostaje).
    """
    argumenty = ("abc1234", ("operator", "prog"), "lod_paths.py")

    czyste = sweep.default_journal(*argumenty, "fcb923b7000e0dca")
    brudne = sweep.default_journal(*argumenty, "4657e1519785c683")

    assert czyste != brudne, czyste


def test_ta_sama_tresc_trafia_w_ten_sam_dziennik():
    """Kontrola ujemna: wznowienie na tresci NIEZMIENIONEJ nie moze zgubic pliku.

    To jest polowa, ktora poprawka musiala zachowac. Nazwa zmieniajaca sie przy
    kazdym wywolaniu — a nie przy kazdej zmianie tresci — zamienilaby wznowienie
    w fikcje, i pole „Wyjscie" pozycji zadalo sprawdzenia dokladnie tego.
    """
    argumenty = ("abc1234", ("operator", "prog"), "lod_paths.py")

    pierwszy = sweep.default_journal(*argumenty, "fcb923b7000e0dca")
    drugi = sweep.default_journal(*argumenty, "fcb923b7000e0dca")

    assert pierwszy == drugi, (pierwszy, drugi)


def test_odcisk_przebiegu_sklada_PARY_a_nie_kolejnosc_i_nie_same_wartosci():
    """Odcisk przebiegu zalezy od PAR plik→odcisk: nie od kolejnosci i nie od
    samych wartosci.

    **Pierwsza wersja tego testu nie lapala polowy tego, co obiecuje, i pokazala to
    moja wlasna kontrola negatywna.** Test uzywal par `{x: aaaa, y: bbbb}` wobec
    `{x: aaaa, y: cccc}`, wiec odcisk liczony z SAMYCH WARTOSCI (bez nazw plikow)
    tez je odroznial — KN-2 przechodzila 99/99. Do zlapania tej mutacji potrzebne sa
    dwa slowniki o tym samym multizbiorze wartosci i innym przypisaniu; odcisk
    z wartosci uzna je za rowne, poprawny nie moze.

    To ta sama klasa usterki, ktora ta sesja tropila caly dzien: asercja prawdziwa,
    ale nie rozstrzygajaca (6.A32, 6.A29).
    """
    a = sweep.odcisk_przebiegu({"x.py": "aaaa", "y.py": "bbbb"})
    b = sweep.odcisk_przebiegu({"y.py": "bbbb", "x.py": "aaaa"})
    przestawione = sweep.odcisk_przebiegu({"x.py": "bbbb", "y.py": "aaaa"})
    inna_wartosc = sweep.odcisk_przebiegu({"x.py": "aaaa", "y.py": "cccc"})

    # kolejnosc wstawiania nie ma znaczenia
    assert a == b, (a, b)
    # ale przypisanie odciskow do NAZW ma — i to jest czlon, ktorego brakowalo
    assert a != przestawione, (a, przestawione)
    assert a != inna_wartosc, (a, inna_wartosc)


def test_pusty_przebieg_ma_odcisk_PUSTY_a_nie_odcisk_pustego_napisu():
    """`sha256("")` jest wartoscia, ktora WYGLADALABY jak zmierzona.

    Przebieg bez ani jednego pliku nie ma czego odrozniac, wiec odcisk jest pusty
    i nazwa dziennika wraca do trzech skladnikow. Gdyby zamiast tego wchodzil tam
    odcisk pustego napisu, czytajacy nazwy nie mialby jak odroznic „przebieg bez
    plikow" od „przebieg, ktorego pliki maja akurat taki odcisk".
    """
    assert sweep.odcisk_przebiegu({}) == ""

    trzy = sweep.default_journal("abc1234", ("operator",), "x.py")
    cztery_z_pustym = sweep.default_journal("abc1234", ("operator",), "x.py", "")

    assert trzy == cztery_z_pustym, (trzy, cztery_z_pustym)


# --- 6.B42: odciski w naglowku raportu -------------------------------------------

def _wynik(rodzaj="operator", przezyla=False):
    return {"id": "x.py:1:0", "plik": "x.py", "opis": "x", "rodzaj": rodzaj,
            "przezyla": przezyla, "rozstrzygniete": True, "wykonana": True,
            "padly": []}


def test_naglowek_raportu_niesie_odcisk_tresci_a_nie_tylko_commit():
    """6.B42: commit nie odroznia dwoch przebiegow na tym samym commicie.

    To jest to samo zdanie, ktore zmierzylo 6.B32 dla WPISU dziennika i 6.B40 dla
    NAZWY pliku. Raport z przebiegu `--dirty` byl do 07.09.2026 nieodroznialny od
    raportu z drzewa czystego, choc liczby dotyczyly innej tresci — a 6.D3 postawilo
    bramke wlasnie na to, zeby kazdy `reports/*.md` mowil, na czym powstaly jego
    liczby. Commit podawal; tresci nie.
    """
    odciski = {"tools/blender/lod_paths.py": "fcb923b7000e0dca"}

    tekst = sweep.report([_wynik()], "5ae1b52", odciski)

    assert "**Odcisk treści przebiegu:**" in tekst, tekst[:400]
    assert sweep.odcisk_przebiegu(odciski) in tekst, tekst[:400]
    assert "fcb923b7000e0dca" in tekst, tekst[:400]


def test_dwie_tresci_daja_ROZNE_naglowki_przy_tym_samym_commicie():
    """Wlasnosc z pola „Skonczone, gdy": raport ma byc ODROZNIALNY.

    Bez tej asercji test wyzej przechodzilby takze wtedy, gdyby odcisk byl stala —
    obecnosc napisu w raporcie nie jest tym samym, co jego zaleznosc od tresci
    (6.A32, 6.A29).
    """
    czysty = sweep.report([_wynik()], "5ae1b52", {"a.py": "fcb923b7000e0dca"})
    brudny = sweep.report([_wynik()], "5ae1b52", {"a.py": "634df59defe0ec2a"})

    assert czysty != brudny
    naglowek = lambda t: [l for l in t.splitlines() if "Odcisk" in l][0]
    assert naglowek(czysty) != naglowek(brudny), naglowek(czysty)


def test_powyzej_progu_tabela_ustepuje_ZDANIU_a_nie_milczeniu():
    """Przy 63 celach tabela zajmuje ekran, wiec powyzej progu jej nie ma —
    ale nie ma jej JAWNIE, z liczba pominietych modulow.

    Prog jest wyprowadzony z pomiaru: 54 z 66 wywolan w `reports/` obejmuje jeden
    modul, wiec w 82 % tabela ma jeden wiersz. Milczenie zamiast zdania zamienialoby
    raport szerokiego przebiegu w raport, ktory NIE MOWI, ze czegos nie mowi.
    """
    duzo = {f"m{i}.py": f"{i:016x}" for i in range(sweep.MAX_ODCISKOW_W_RAPORCIE + 1)}

    tekst = sweep.report([_wynik()], "5ae1b52", duzo)

    assert sweep.odcisk_przebiegu(duzo) in tekst, tekst[:400]
    assert "| moduł | odcisk treści |" not in tekst, tekst[:600]
    assert str(len(duzo)) in tekst, tekst[:600]
    assert "pominięte" in tekst, tekst[:600]


def test_na_progu_tabela_JESZCZE_jest():
    """Granica nalezy do tabeli, nie do zdania — i to jest przybite, zeby prog
    dal sie przesunac tylko swiadomie.

    Para z testem wyzej: bez niej `<=` i `<` byly by nieodroznialne, a to jest
    dokladnie ta klasa remisu na granicy, ktora `docs/24-clearance-profile-decisions.md`
    rozstrzyga po jednej pozycji naraz.
    """
    rowno = {f"m{i}.py": f"{i:016x}" for i in range(sweep.MAX_ODCISKOW_W_RAPORCIE)}

    tekst = sweep.report([_wynik()], "5ae1b52", rowno)

    assert "| moduł | odcisk treści |" in tekst, tekst[:600]
    assert "pominięte" not in tekst, tekst[:600]


def test_przebieg_bez_plikow_mowi_BRAK_a_nie_odcisk_niczego():
    """`sha256("")` wygladalby jak zmierzony. Ta sama zasada co w `odcisk_przebiegu`
    (6.B40) i ten sam powod: wartosc, ktorej nikt nie policzyl, nie ma prawa
    wygladac jak policzona.
    """
    tekst = sweep.report([_wynik()], "5ae1b52", {})

    assert "brak" in tekst.split("Narzędzie:")[0], tekst[:400]
    assert "| moduł | odcisk treści |" not in tekst, tekst[:600]


# --- 6.B38: pamiec `collect` w obrebie procesu ------------------------------------

def test_pamiec_collect_zwraca_to_samo_i_nie_liczy_dwa_razy():
    """6.B38: modul wolal `collect()` DZIESIEC razy po 0,224 s.

    Zmierzone 07.09.2026 na `665bd98`, czyli PRZED ta pamiecia: 2,24 s z 17,34 s
    calego modulu szlo na dziesiec przeliczen tej samej listy.

    **Ta liczba opisuje drzewo, ktorego ten test juz nie ma** — i dlatego stoi tu
    z commitem, a nie w czasie terazniejszym (6.B46). Zmierzone 07.09.2026 na
    `f684e40`, z ta pamiecia: wywolan w module jest dwadziescia, a swiezych
    przeliczen cztery. Trzy z tych czterech sa nieuniknione, wiec to nie jest
    ubytek pamieci, tylko jej skutek.
    """

    kluczy = len(sweep._PAMIEC_COLLECT)
    pierwsze = sweep.collect()
    drugie = sweep.collect()

    assert [m.id for m in pierwsze] == [m.id for m in drugie]
    # DELTA, nie stan absolutny: inne testy tego modulu tez zapelniaja pamiec, a ten
    # test nie ma prawa ich przeliczen wyrzucac — czyszczenie calej pamieci kosztowaloby
    # 0,224 s kazdemu, kto po nim wola `collect()`, czyli zjadloby oszczednosc 6.B38.
    assert len(sweep._PAMIEC_COLLECT) - kluczy <= 1, (
        f"dwa wywolania dolozyly {len(sweep._PAMIEC_COLLECT) - kluczy} kluczy")


def test_pamiec_collect_zwraca_KOPIE_a_nie_te_sama_liste():
    """Wolajacy, ktory posortuje albo obetnie wynik, nie moze zepsuc nastepnemu.

    `Mutation` jest niezmienna, ale lista nie — a `collect()` jest w tym module
    wolane z **dwudziestu** miejsc (zmierzone 07.09.2026 na `f684e40` przejsciem po
    module z owinietym `collect()`; przy 6.B38, na `665bd98`, bylo ich dziesiec),
    z ktorych czesc robi z wynikiem swoje.
    """
    pierwsze = sweep.collect()
    pierwsze.clear()

    drugie = sweep.collect()

    assert len(drugie) > 500, len(drugie)


def _z_dopiskiem(cel, dopisek):
    """Wykonaj `collect()` z dopiskiem w pliku celu i przywroc plik.

    6.D90: `cel` jest KOPIA z `_cele_na_boku`, a nie plikiem w drzewie glownym.
    Sama funkcja tego nie wymusza — wymusza to wolajacy, i pilnuje bramka
    `test_zadna_kontrola_nie_pisze_do_pliku_sledzonego_w_drzewie`.
    """
    zastane = open(cel, encoding="utf-8").read()
    try:
        with open(cel, "a", encoding="utf-8") as handle:
            handle.write(dopisek)
        return sweep.collect()
    finally:
        with open(cel, "w", encoding="utf-8") as handle:
            handle.write(zastane)


def test_pamiec_collect_UNIEWAZNIA_SIE_gdy_tresc_celu_sie_zmieni():
    """**Najwazniejszy test tej pozycji**, bo bez niego pamiec jest usterka.

    Testy tego narzedzia ZMIENIAJA pliki celow w trakcie jednego procesu — robia to
    kontrole negatywne 6.B32, 6.B39 i 6.B40. Pamiec kluczowana samymi klasami
    podstawialaby wtedy mutacje policzone dla INNEJ tresci, czyli dokladnie te
    usterke, ktora 6.B32 zamykalo w dzienniku, tylko przeniesiona do pamieci procesu.

    Ze klucz z odciskami jest darmowy, jest zmierzone: odczyt i sha256 wszystkich
    63 celow zajmuje 0,0013 s przy 0,224 s na jedno `collect()`.
    """
    with _cele_na_boku() as cel:  # 6.D90: kopia, nie plik w drzewie glownym
        przed = sweep.collect()
        kluczy = len(sweep._PAMIEC_COLLECT)

        po = _z_dopiskiem(cel, "\n\ndef _f38(a):\n    return a >= 1\n")

        assert len(sweep._PAMIEC_COLLECT) == kluczy + 1, (
            "zmiana tresci celu NIE uniewaznila pamieci — mutacje policzone dla innej "
            "tresci wrocilyby jako wynik biezacego przebiegu")
        assert len(po) > len(przed), (len(po), len(przed))
        assert [m.id for m in sweep.collect()] == [m.id for m in przed], (
            "po przywroceniu tresci pamiec nie wrocila do klucza pierwszego przebiegu")


def test_pamiec_uniewaznia_sie_takze_przy_zmianie_BEZ_ani_jednej_mutacji():
    """Zmiana tresci, ktora nie dodaje ani jednej mutacji, TEZ musi uniewazniac.

    **To nie jest przypadek wymyslony — na nim padla pierwsza wersja testu wyzej.**
    Dopisek `DODANE = 1` zmienia plik i jego odcisk, ale `mutations_for` daje z niego
    ZERO mutacji (zmierzone: 0), wiec lista mutacji jest identyczna. Asercja
    „inna tresc znaczy inna lista" jest wiec NIEPRAWDZIWA jako zdanie ogolne, i test
    poprawilem wedlug pomiaru, nie pomiar wedlug testu (wzorzec 6.A28).

    Wlasciwa wlasnoscia jest **uniewaznienie klucza**, a roznica list to tylko jej
    skutek — i to tylko wtedy, gdy zmiana jest mutowalna. Ten test przybija te
    pierwsza, bo bez niego pamiec, ktora ignoruje zmiany „nieciekawe", przechodzilaby
    caly zestaw.
    """
    with _cele_na_boku() as cel:  # 6.D90: kopia, nie plik w drzewie glownym
        przed = sweep.collect()
        kluczy = len(sweep._PAMIEC_COLLECT)

        po = _z_dopiskiem(cel, "\nDODANE_PRZEZ_TEST_6B38 = 1\n")

        assert len(sweep._PAMIEC_COLLECT) == kluczy + 1, (
            "zmiana tresci bez nowych mutacji NIE uniewaznila pamieci")
        assert [m.id for m in po] == [m.id for m in przed], (
            "dopisek bez mutacji zmienil liste — zmienil sie pomiar, nie test")


# --- 6.D37: puste zawezenie ------------------------------------------------------

def test_only_z_pustym_wzorcem_jest_odmowa_a_nie_pelny_przeglad():
    """6.D37: `--only ""` przechodzilo w milczeniu i robilo PELNY przeglad.

    Pusty napis jest falszywy dla `if args.only`, wiec nie wchodzil ani filtr, ani
    wypis „dopasowalo N plikow", ani odmowa z 6.B39. Zmierzone 07.09.2026:
    **2346 mutacji zamiast 2** dla typowego triazu jednego modulu, czyli **1173x**
    wiecej pracy — i przebieg wygladal przy tym na zawezony, bo wolajacy o zawezenie
    prosil. Ta sama rodzina co 6.B39, odwrocona: tam zbior byl pusty, tu jest pelny.
    """
    done = _sweep_6b39("--only", "", "--list")

    assert done.returncode != 0, (done.returncode, done.stdout[-300:])
    assert "--only" in done.stderr, done.stderr[-400:]
    assert "razem: 2346" not in done.stdout, done.stdout[-200:]


def test_przebieg_BEZ_only_zostaje_niezmieniony():
    """Kontrola ujemna z pola „Skonczone, gdy": odmowa nie moze objac przebiegu,
    ktory o zawezenie nie prosil.

    Odmowa kluczuje po `"--only" in sys.argv`, a NIE po samej falszywosci
    `args.only` — bo obie sytuacje daja pusty napis, a tylko jedna jest pomylka.
    Bez tego testu odmowa zbudowana na falszywosci przeszlaby test wyzej i zablokowala
    kazdy przebieg pelny, czyli droge, ktora `reports/` wola siedem razy.
    """
    done = _sweep_6b39("--list")

    assert done.returncode == 0, (done.returncode, done.stderr[-300:])
    assert "razem:" in done.stdout, done.stdout[-200:]


def test_dwie_postacie_tej_samej_pomylki_daja_ten_sam_kod():
    """Podstawienie pustej zmiennej ma DWIE postacie i tylko jedna byla chroniona.

    Zmierzone 07.09.2026 na dwoch prawdziwych petlach w `reports/`::

        --only "$m"   (mutation-drift.md:455)          -> --only ''
        --only $f     (mutation-triage-fizyka.md:173)  -> argument znika

    Druga postac argparse odmawia od zawsze (`expected one argument`, kod 2);
    pierwsza nie byla chroniona przez nic. Po 6.D37 obie daja **ten sam kod**, bo
    jedna pomylka nie ma prawa dawac dwoch roznych odpowiedzi zaleznie od tego, czy
    cudzyslow ocalal.
    """
    w_cudzyslowie = _sweep_6b39("--only", "", "--list")
    bez_cudzyslowu = _sweep_6b39("--only", "--workers", "4", "--list")

    assert w_cudzyslowie.returncode == bez_cudzyslowu.returncode == 2, (
        w_cudzyslowie.returncode, bez_cudzyslowu.returncode)




# --- 6.D90: okno mutacji a czystość drzewa głównego -------------------------------
#
# Pozycja weszła do kolejki z tezą, że narzędzie mutuje pliki w `data/` W MIEJSCU.
# Pomiar 10.09.2026 tezę OBALIŁ i te trzy bramki pilnują tego, co pomiar zastał,
# a nie tego, co wpis zapowiadał:
#
#   * `targets()` chodzi wyłącznie po `tools/` i bierze wyłącznie `.py`, więc żaden
#     plik z `data/` nie ma jak zostać wybrany do mutacji;
#   * `check_one` otwiera do zapisu `os.path.join(worktree, ...)`, a `worktree` jest
#     kopią z `git worktree add --detach` stojącą w katalogu tymczasowym, nie w repo;
#   * przez cały przebieg (kalibracja wyroczni + trzy mutacje, 512 s) `git status
#     --porcelain` w drzewie głównym, odpytywany co 50 ms, zwrócił pustkę 100 %
#     próbek — także dla samego `data/`.
#
# Skoro teza jest fałszywa, wartością tej pozycji jest UTRWALENIE stanu: gdyby ktoś
# rozszerzył `targets()` o dane albo zmutował w drzewie wołającego, dziś nie
# zapaliłoby się nic. Trzecia bramka jest kontrolą PRZYRZĄDU: ten sam obserwator,
# skierowany na drzewo, które NAPRAWDĘ się brudzi, brud widzi — bez niej „pusto
# w trakcie okna" znaczyłoby tyle samo, co „obserwator nic nie umie zobaczyć".


def _git_w(katalog, *args):
    """Nazwa z przyrostkiem, bo `_git` w tym module JUŻ JEST i ma inną sygnaturę.

    Pierwsza wersja tych bramek nazwała pomocnika `_git` i przesłoniła tamten —
    trzy testy `dirty_sources` padły od razu na `missing keyword-only argument`.
    Wypisane, bo to ten sam kształt, o który chodzi w całej tej sekcji: przyrząd,
    który po cichu podmienia inny przyrząd.
    """
    return subprocess.run(["git", *args], cwd=katalog, capture_output=True, text=True)


def _stan_roboczy(katalog, sciezka=None):
    """`git status --porcelain`, opcjonalnie zawężony do jednej ścieżki."""
    polecenie = ["status", "--porcelain"]
    if sciezka is not None:
        polecenie += ["--", sciezka]
    gotowe = _git_w(katalog, *polecenie)
    assert gotowe.returncode == 0, gotowe.stderr[-300:]
    return gotowe.stdout


def test_zaden_cel_mutacji_nie_lezy_poza_kodem_narzedzi():
    """Plik z `data/` nie ma jak trafić pod mutację, bo `targets()` tam nie zagląda.

    To jest pierwsza z dwóch niezależnych przyczyn, dla których teza pozycji 6.D90
    okazała się fałszywa: nawet gdyby mutacja szła w drzewie wołającego, nie miałaby
    czego zmutować w `data/`. Asercja na niepustość stoi tu, a nie w komentarzu,
    bo pętla po pustej liście przechodzi każdą regułę, jaką się w nią wpisze.
    """
    cele = sweep.targets()
    assert len(cele) > 20, f"celów {len(cele)} — `targets()` przestało cokolwiek widzieć"

    tools = os.path.join(ROOT, "tools") + os.sep
    dane = os.path.join(ROOT, "data") + os.sep
    for path in cele:
        assert path.startswith(tools), path
        assert not path.startswith(dane), path
        assert path.endswith(".py"), path


def test_okno_mutacji_nie_rusza_drzewa_glownego_W_TRAKCIE_a_nie_po():
    """Pomiar W TRAKCIE okna, bo po jego zamknięciu plik jest już przywrócony.

    Pole „Skończone, gdy" pozycji żąda dokładnie tego rozróżnienia: sprawdzenie po
    przebiegu nie odróżnia narzędzia, które niczego nie tknęło, od narzędzia, które
    tknęło i posprzątało. Obserwator siedzi więc w atrapie `run_suite`, czyli jest
    wołany DOKŁADNIE wtedy, gdy mutacja stoi zastosowana.

    Porównanie idzie do stanu SPRZED okna, a nie do pustki: gałąź robocza może mieć
    legalnie zmieniony plik w `data/` (na przykład czyjąś kontrolę negatywną w toku),
    a ta bramka pyta wyłącznie o to, czy okno mutacji coś do tego stanu DOŁOŻYŁO.
    """
    przed = _stan_roboczy(ROOT, "data")
    widziane = {}

    with tempfile.TemporaryDirectory() as udawane_drzewo:
        plik = os.path.join(udawane_drzewo, "a.py")
        with open(plik, "w", encoding="utf-8") as uchwyt:
            uchwyt.write("x = 1\n")
        mutacja = sweep.Mutation("a.py", 1, 4, 5, "1", "2", "prog")

        def _atrapa(*_a, **_kw):
            with open(plik, encoding="utf-8") as uchwyt:
                widziane["kopia"] = uchwyt.read()
            widziane["data"] = _stan_roboczy(ROOT, "data")
            return (False, [], 0)

        prawdziwe = sweep.run_suite
        sweep.run_suite = _atrapa
        try:
            sweep.check_one(udawane_drzewo, mutacja, 5, "abcdef1")
        finally:
            sweep.run_suite = prawdziwe

        with open(plik, encoding="utf-8") as uchwyt:
            po = uchwyt.read()

    # Okno NAPRAWDĘ było otwarte — bez tego zdania cała reszta mówiłaby tylko tyle,
    # że atrapa się wykonała.
    assert widziane["kopia"] == "x = 2\n", widziane.get("kopia")
    assert po == "x = 1\n", po
    assert widziane["data"] == przed, (
        "w trakcie otwartego okna mutacji `data/` w drzewie głównym zmieniło stan:\n"
        f"przed: {przed!r}\nw trakcie: {widziane['data']!r}")


def test_obserwator_okna_widzi_brud_tam_gdzie_brud_jest():
    """Kontrola PRZYRZĄDU, nie narzędzia: pusty wynik ma znaczyć „czysto", nie „ślepy".

    Bramka wyżej twierdzi, że w trakcie okna `git status` drzewa głównego nie drgnął.
    Zdanie to jest warte tyle, ile obserwator, który je wypowiada — a obserwator
    wołający `git status` na drzewie, którego narzędzie nie tyka, zwróci pustkę
    także wtedy, gdy przestanie cokolwiek mierzyć.

    Ta bramka kieruje TEN SAM obserwator na repozytorium syntetyczne, w którym plik
    `data/os.json` jest mutowany naprawdę, i żąda, żeby zobaczył zmianę w trakcie
    okna oraz jej brak po zamknięciu. Prawdziwe `data/` pozostaje nietknięte —
    reguła 6 konstytucji obowiązuje także testy tej pozycji.
    """
    with tempfile.TemporaryDirectory() as repo:
        os.makedirs(os.path.join(repo, "data"))
        cel = os.path.join(repo, "data", "os.json")
        with open(cel, "w", encoding="utf-8") as uchwyt:
            uchwyt.write('{"x": 1}\n')
        for polecenie in (("init", "--quiet"),
                          ("config", "user.email", "test@example.invalid"),
                          ("config", "user.name", "test"),
                          ("add", "-A"),
                          ("commit", "--quiet", "-m", "baza")):
            gotowe = _git_w(repo, *polecenie)
            assert gotowe.returncode == 0, (polecenie, gotowe.stderr[-200:])
        assert _stan_roboczy(repo, "data") == "", "repozytorium syntetyczne startuje brudne"

        mutacja = sweep.Mutation(os.path.join("data", "os.json"), 1, 6, 7, "1", "2", "prog")
        widziane = {}

        def _atrapa(*_a, **_kw):
            widziane["w_trakcie"] = _stan_roboczy(repo, "data")
            return (False, [], 0)

        prawdziwe = sweep.run_suite
        sweep.run_suite = _atrapa
        try:
            sweep.check_one(repo, mutacja, 5, "abcdef1")
        finally:
            sweep.run_suite = prawdziwe

        assert widziane["w_trakcie"].strip().endswith("data/os.json"), (
            "obserwator nie zobaczył brudu w drzewie, które NAPRAWDĘ się brudzi — "
            f"czyli pustka w bramce wyżej niczego nie dowodzi: {widziane['w_trakcie']!r}")
        assert _stan_roboczy(repo, "data") == "", (
            "po zamknięciu okna plik nie wrócił do stanu z HEAD")


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

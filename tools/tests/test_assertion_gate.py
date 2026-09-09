#!/usr/bin/env python3
"""Testy bramki asercji z `assertion_gate.py`.

Bramka pilnuje, żeby test, który przeszedł, wykonał co najmniej jedną asercję.
Te testy pilnują samej bramki — w obie strony:

* że **łapie** cichy skip w kształcie tego z zamkniętego PR #139
  (`if not os.path.isfile(...): return` na artefakcie, którego CI nie buduje);
* że **nie rusza** testu pominiętego jawnie przez `skip("powód")`;
* że **pada na pustym zbiorze**, zamiast przechodzić, gdy przestaje mieć na co patrzeć.

Bez ostatniego punktu bramka byłaby dokładnie tą usterką, którą tropi: zielona,
bo nic nie sprawdziła.
"""
import ast
import atexit
import os
import shutil
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "tests"))
import assertion_gate as AG  # noqa: E402

TEST_ALL = os.path.join(ROOT, "tools", "tests", "test_all.py")
_UNIQUE = [0]
_SANDBOX = tempfile.mkdtemp(prefix="assertion-gate-probe-")
atexit.register(shutil.rmtree, _SANDBOX, True)


def _load(source):
    """Załaduj źródło jako instrumentowany moduł i zwróć go."""
    _UNIQUE[0] += 1
    name = f"assertion_gate_probe_{_UNIQUE[0]}"
    path = os.path.join(_SANDBOX, name + ".py")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(source)
    return AG.load_instrumented(path, name)


def _run(fn):
    """Uruchom test tak, jak robi to runner, i zwróć `(stan, komunikat, asercje)`."""
    AG.reset()
    outcome = None
    try:
        fn()
    except Exception as error:
        outcome = error
    checks = AG.hits()
    state, message = AG.verdict(outcome, checks)
    return state, message, checks


# --- licznik: co się liczy jako asercja ------------------------------------------


def test_gate_counts_a_plain_assert():
    module = _load("def test_x():\n    assert 1 == 1\n")
    state, _message, checks = _run(module.test_x)
    assert state == "ok", state
    assert checks == 1, checks


def test_gate_counts_every_pass_through_an_assert_in_a_loop():
    """Trzy obroty pętli to trzy asercje, nie jedna."""
    module = _load("def test_x():\n    for i in range(3):\n        assert i >= 0\n")
    _state, _message, checks = _run(module.test_x)
    assert checks == 3, checks


def test_gate_counts_the_except_guard_with_a_raise_after_the_try():
    """Idiom bez `assert`, używany w tym repo dziesięć razy.

    `try: coś_co_ma_paść()` / `except ValueError: return` / `raise AssertionError(...)`
    jest pełnoprawnym sprawdzeniem. Bez tego punktu bramka kazałaby dopisać do tych
    testów sztuczny `assert`, żeby przestały być czerwone.
    """
    module = _load(
        "def test_x():\n"
        "    try:\n"
        "        raise ValueError('tak ma być')\n"
        "    except ValueError:\n"
        "        return\n"
        "    raise AssertionError('nie padło')\n")
    state, _message, checks = _run(module.test_x)
    assert state == "ok", state
    assert checks == 1, checks


def test_gate_counts_the_except_guard_with_a_raise_in_the_else():
    module = _load(
        "def test_x():\n"
        "    try:\n"
        "        raise ValueError('tak ma być')\n"
        "    except ValueError:\n"
        "        pass\n"
        "    else:\n"
        "        raise AssertionError('nie padło')\n")
    state, _message, checks = _run(module.test_x)
    assert state == "ok", state
    assert checks == 1, checks


def test_gate_does_not_count_a_try_except_that_only_swallows():
    """`try/except: pass` bez `raise AssertionError` NIE jest sprawdzeniem.

    To kontrola przeciwna do dwóch powyższych: gdyby liczyło się każde wejście
    w `except`, wystarczyłoby połknąć wyjątek, żeby test wyglądał na sprawdzający.
    """
    module = _load(
        "def test_x():\n"
        "    try:\n"
        "        raise ValueError('połknięte')\n"
        "    except ValueError:\n"
        "        pass\n")
    state, message, checks = _run(module.test_x)
    assert checks == 0, checks
    assert state == "fail", state
    assert "bez wykonania ani jednej asercji" in message, message


# --- usterka: cichy skip ----------------------------------------------------------


def test_gate_catches_the_pr139_shape_of_a_silent_skip():
    """Dokładny kształt z PR #139: wyjście na nieistniejącym artefakcie z `build/`.

    ŚCIEŻKA NIE MOŻE WSKAZYWAĆ NA PRAWDZIWY `build/` — i to jest cała historia tego
    testu. Pierwsza wersja brała dosłownie `build/t400/chunks/L1_A-chunks.json`, czyli
    plik, który generatory tego repozytorium naprawdę tworzą. W CI przechodziła, bo
    `actions/checkout` robi `git clean -ffdx`. Na maszynie, na której ktoś uruchomił
    `blender_smoke.sh`, plik ISTNIEJE, ciało atrapy się wykonuje, bramka liczy jedną
    asercję zamiast zera i test pada:

        FAIL test_gate_catches_the_pr139_shape_of_a_silent_skip: 1

    Zmierzone 05.09.2026, na czystym `main`, u kogoś z zabudowanym `build/`.

    Bramka na testy zależne od artefaktów była więc sama zależna od artefaktu —
    dokładnie ta usterka, którą łapie, o jeden poziom wyżej. Ścieżka idzie teraz do
    katalogu tymczasowego, który na pewno nie istnieje; kształt kodu atrapy zostaje
    ten sam co w #139, bo o kształt tu chodzi, a nie o konkretny plik.
    """
    nieistniejacy = os.path.join(
        tempfile.gettempdir(), "mbxl-bramka-asercji-nie-ma-takiego-pliku", "chunks.json")
    assert not os.path.exists(nieistniejacy), (
        'ścieżka udająca brakujący artefakt jednak istnieje, '
        f'więc test mierzyłby co innego niż cichy skip: {nieistniejacy}')

    module = _load(
        "import os\n"
        "def test_x():\n"
        f"    path = {nieistniejacy!r}\n"
        "    if not os.path.isfile(path):\n"
        "        return\n"
        "    assert os.path.getsize(path) > 0\n")
    state, message, checks = _run(module.test_x)
    assert checks == 0, checks
    assert state == "fail", state
    assert "cichy skip" in message, message


def test_gate_catches_the_silent_skip_even_when_the_artefact_is_there():
    """Kontrola przeciwna: ten sam kształt, ale plik ISTNIEJE.

    Wtedy ciało się wykonuje, asercja pada w liczniku i bramka NIE ma prawa zgłosić
    cichego skipu — bo go nie było. Bez tego testu poprzedni przechodziłby także wtedy,
    gdyby bramka zaczęła zgłaszać cichy skip na sam WIDOK `os.path.isfile`, nie patrząc,
    czy ciało się wykonało.
    """
    with tempfile.TemporaryDirectory() as katalog:
        istniejacy = os.path.join(katalog, "chunks.json")
        with open(istniejacy, "w", encoding="utf-8") as uchwyt:
            uchwyt.write("{}\n")

        module = _load(
            "import os\n"
            "def test_x():\n"
            f"    path = {istniejacy!r}\n"
            "    if not os.path.isfile(path):\n"
            "        return\n"
            "    assert os.path.getsize(path) > 0\n")
        state, _message, checks = _run(module.test_x)

    assert checks == 1, f"ciało się wykonało, więc asercja musi być policzona: {checks}"
    assert state == "ok", state


def test_gate_catches_a_loop_over_an_empty_set():
    """Asercje wyłącznie w środku pętli po zbiorze, który bywa pusty."""
    module = _load("def test_x():\n    for item in []:\n        assert item\n")
    state, _message, checks = _run(module.test_x)
    assert checks == 0, checks
    assert state == "fail", state


def test_gate_catches_a_test_whose_exception_was_swallowed_whole():
    module = _load(
        "def test_x():\n"
        "    try:\n"
        "        assert False, 'to miało paść'\n"
        "    except Exception:\n"
        "        return\n")
    state, _message, checks = _run(module.test_x)
    # Asercja WYKONAŁA się i padła, a test i tak przeszedł. Licznik ją widzi, więc
    # bramka tego przypadku nie łapie — i tak ma być: to inna usterka niż cichy skip,
    # a bramka, która próbuje łapać wszystko, kłamie o tym, co mierzy.
    assert checks == 1, checks
    assert state == "ok", state


# --- poprawne pominięcie ----------------------------------------------------------


def test_gate_leaves_an_explicit_skip_alone():
    module = _load(
        "import assertion_gate as AG\n"
        "def test_x():\n"
        "    AG.skip('brak Blendera na tej maszynie')\n"
        "    assert False\n")
    state, message, checks = _run(module.test_x)
    assert state == "skip", state
    assert message == "brak Blendera na tej maszynie", message
    assert checks == 0, checks


def test_gate_skip_demands_a_reason():
    """Pominięcie bez powodu to ten sam cichy `return`, przed którym bramka stoi."""
    for empty in ("", "   "):
        try:
            AG.skip(empty)
        except ValueError:
            continue
        raise AssertionError(f"pominięcie bez powodu przeszło: {empty!r}")


def test_gate_skip_is_not_a_failure_and_not_a_pass():
    state, _message, _checks = _run(lambda: AG.skip("powód"))
    assert state == "skip", state
    assert state != "ok" and state != "fail"


# --- bramka bez niczego do oglądania ----------------------------------------------


def test_gate_fails_when_there_are_no_tests_at_all():
    assert AG.suite_verdict(0, 12345), "pusty zestaw przeszedł przez bramkę"


def test_gate_fails_when_the_whole_suite_executed_no_assertion():
    assert AG.suite_verdict(1493, 0), "zestaw bez ani jednej asercji przeszedł"


def test_gate_fails_when_instrumentation_stopped_finding_assertions():
    """`sites()` to liczba miejsc, w które bramka wstrzyknęła licznik.

    Zero znaczy, że transformacja przestała trafiać w `assert` — na przykład dlatego,
    że ładowanie modułów obeszło `load_instrumented`. Wtedy każdy test miałby zero
    asercji, więc bramka musi się zgłosić SAMA, zanim zaleje log fałszywymi awariami.
    """
    saved = AG._SITES[0]
    try:
        AG._SITES[0] = 0
        assert AG.suite_verdict(1493, 100), "bramka bez miejsc asercji przeszła"
    finally:
        AG._SITES[0] = saved
    assert AG.suite_verdict(1493, 100) == "", AG.suite_verdict(1493, 100)


def test_gate_instrumented_this_suite_for_real():
    """Kontrola pozytywna do trzech powyższych: na tym drzewie miejsca ISTNIEJĄ.

    **Rozdzielona na dwie asercje przy 6.D25, i to nie jest kosmetyka.** Poprzednia
    wersja brzmiała `AG.sites() > 3000` — a `AG.sites()` liczy miejsca załadowane
    W TYM przebiegu, nie miejsca na drzewie. Dopóki jedynym sposobem uruchomienia był
    cały zestaw, obie liczby były tą samą liczbą. Od 6.D25 moduł można uruchomić sam
    i wtedy `sites()` daje 161 — próg 3000 czynił z tego awarię, choć instrumentacja
    działała bez zarzutu. Test mówiłby wtedy „bramka nie instrumentuje", mierząc
    w istocie „ten przebieg objął mniej modułów".

    Rozdzielenie pilnuje obu rzeczy osobno i **mocniej** niż jedna asercja: że
    instrumentacja tego przebiegu w ogóle zadziałała, i że drzewo ma ponad 3000 miejsc
    — to drugie liczone wprost z plików, więc niezależne od tego, ile modułów wczytał
    akurat ten przebieg.
    """
    assert AG.sites() > 0, (
        "instrumentacja tego przebiegu nie znalazła ani jednego miejsca asercji")
    na_drzewie = 0
    for path in AG.paths():
        with open(path, encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        na_drzewie += sum(1 for node in ast.walk(tree) if isinstance(node, ast.Assert))
    assert na_drzewie > 3000, na_drzewie


# --- instrumentacja nie psuje modułu ----------------------------------------------


def test_gate_keeps_line_numbers_so_tracebacks_still_point_at_the_assert():
    """Wstawiony licznik ma numer wiersza asercji, więc `compile` nic nie przesuwa.

    Gdyby przesuwał, każdy komunikat awarii wskazywałby nie ten wiersz, a to jest
    cena, której ta bramka nie ma prawa nakładać.
    """
    module = _load("def test_x():\n\n\n    assert False, 'tutaj'\n")
    try:
        module.test_x()
    except AssertionError:
        line = sys.exc_info()[2].tb_next.tb_lineno
        assert line == 4, line
    else:
        raise AssertionError("asercja nie padła")


def test_gate_instrumented_module_keeps_its_file_and_name():
    module = _load("import os\nHERE = os.path.dirname(os.path.abspath(__file__))\n")
    assert module.__file__.endswith(".py"), module.__file__
    assert module.HERE and os.path.isdir(module.HERE), module.HERE
    assert sys.modules[module.__name__] is module


def test_gate_instrument_counts_sites_it_actually_injected():
    source = ("def test_a():\n    assert 1\n    assert 2\n"
              "def test_b():\n"
              "    try:\n        pass\n    except ValueError:\n        return\n"
              "    raise AssertionError('x')\n")
    _tree, marked = AG.instrument(source, "<probe>")
    assert marked == 3, marked


# --- runner naprawdę używa bramki --------------------------------------------------


#: Wywolania, ktore runner MUSI wykonywac, zapisane jako nazwy z drzewa skladni.
#: Bez `AG.load_instrumented` moduly ida bez licznika; bez `AG.verdict` bramka nie
#: rozstrzyga o tescie; bez `AG.suite_verdict` nikt nie pyta, czy bramka miala na co
#: patrzec.
WYMAGANE_WOLANIA = ("AG.load_instrumented", "AG.verdict", "AG.suite_verdict")

#: Sposoby zaladowania modulu, ktore OMIJAJA licznik asercji. Lista jest po
#: nazwach z drzewa skladni, nie po napisach w pliku — patrz docstring bramki nizej.
ZAKAZANE_LADOWANIA = ("exec", "eval", "__import__", "importlib.import_module",
                      "importlib.util.spec_from_file_location", "spec_from_file_location",
                      "importlib.machinery.SourceFileLoader", "runpy.run_path")


def _wolania(drzewo):
    """Nazwy wszystkich wywolan w drzewie, jako napisy w postaci `a.b.c`."""
    nazwy = []
    for wezel in ast.walk(drzewo):
        if isinstance(wezel, ast.Call):
            try:
                nazwy.append(ast.unparse(wezel.func))
            except Exception:
                continue
    return nazwy


def _funkcja(drzewo, nazwa):
    for wezel in ast.walk(drzewo):
        if isinstance(wezel, (ast.FunctionDef, ast.AsyncFunctionDef)) and wezel.name == nazwa:
            return wezel
    return None


def test_gate_runner_loads_every_test_module_through_the_counter():
    """Bramka jest warta tyle, ile jej uzycie w `test_all.py` — sprawdzane po AST.

    **6.D76, i ta bramka byla zepsuta w OBIE strony naraz.** Poprzednia wersja
    robila cztery dopasowania `napis in tresc_pliku`, i to dawalo dwa przeciwne
    skutki z jednej przyczyny. Zmierzone 09.09.2026:

    Strona pierwsza — FALSZYWY ALARM na poprawnej tresci. Pilnowane wywolania byly
    zapisane bez spacji po przecinku, wiec pierwsze narzedzie stylu je przepisuje:

        ORYGINAL   PASS 'AG.load_instrumented(path,name)'
        PEP8       FAIL 'AG.load_instrumented(path,name)'

    Semantyka identyczna, `ast.parse` przechodzi, a bramka czerwona. Bramka, ktora
    pada na poprawnej tresci, zostaje wylaczona przez pierwszego zirytowanego
    czlowieka — rodzina 6.D27.

    Strona druga — CISZA na rzeczywistym obejsciu, i ta jest grozniejsza. Podmiana
    ladowania modulow na `exec(compile(...))`, BEZ ani jednego wystapienia zakazanej
    nazwy, przechodzila wszystkie cztery asercje na zielono przy modulach idacych
    bez licznika. Jedyna bramka pilnujaca, ze asercje sa liczone, przechodzila na
    runnerze, ktory ich nie liczyl — rodzina 6.D65.

    **Dlaczego AST, a nie lepszy napis.** Dopasowanie tekstowe nie odroznia kodu od
    komentarza ani od napisu, i zalezy od formatowania. Drzewo skladni nie widzi ani
    spacji, ani komentarzy — a zakaz jest wyrazony POZYTYWNIE: w funkcji odkrywania
    zaden sposob zaladowania modulu poza `AG.*` nie jest dopuszczony. Zakaz jednej
    nazwy laapal jedno obejscie; warunek pozytywny laapie kazde.
    """
    with open(TEST_ALL, encoding="utf-8") as handle:
        source = handle.read()
    drzewo = ast.parse(source)

    wolania = _wolania(drzewo)
    brakujace = [nazwa for nazwa in WYMAGANE_WOLANIA if nazwa not in wolania]
    assert not brakujace, (
        "runner nie wola bramki: " + repr(brakujace) + " — bez tych wywolan moduly "
        "ida bez licznika asercji, a zestaw meldowalby sprawdzenia, ktorych nie zrobil")

    odkrywanie = _funkcja(drzewo, "_discover")
    assert odkrywanie is not None, (
        "nie znalazlem funkcji odkrywania modulow w `test_all.py` — milczenie tej "
        "bramki nie moze znaczyc „nie ma obejscia\", gdy nie ma czego sprawdzic")

    w_odkrywaniu = _wolania(odkrywanie)
    obejscia = [nazwa for nazwa in w_odkrywaniu if nazwa in ZAKAZANE_LADOWANIA]
    assert not obejscia, (
        "odkrywanie modulow laduje je omijajac licznik: " + repr(obejscia))

    # WARUNEK POZYTYWNY, i to on laapie obejscie nienazwane na liscie: modul wchodzi
    # do zestawu WYLACZNIE przez bramke. Gdyby ktos dopisal trzeci sposob ladowania,
    # ta asercja go nazwie, nie znajac jego nazwy z gory.
    assert "AG.load_instrumented" in w_odkrywaniu, (
        "funkcja odkrywania nie wola `AG.load_instrumented` — moduly wchodza do "
        "zestawu inna droga niz przez licznik asercji")


def test_gate_runner_counts_skipped_tests_outside_the_passed_total():
    """`SKIP` nie może po cichu poprawiać statystyki `przeszło`."""
    with open(TEST_ALL, encoding="utf-8") as handle:
        source = handle.read()
    assert "{passed}/{len(tests)-len(skipped)} przeszło" in source, source[-800:]


def test_gate_paths_cover_this_file_and_test_all():
    found = {os.path.basename(p) for p in AG.paths()}
    assert "test_all.py" in found, sorted(found)[:5]
    assert "test_assertion_gate.py" in found, sorted(found)[:5]
    assert len(found) > 50, len(found)


# --- 6.D19: import nieudany musi być widoczny dla grepa, nie tylko dla kodu wyjścia -


def test_gate_a_broken_import_produces_a_grep_visible_fail_line_and_keeps_the_summary():
    """Moduł, który się nie importuje, nie może być niewidzialny dla `grep FAIL`.

    Zmierzone 06.09.2026 przy 6.D15 (#301): moduł z błędem składni w `tools/tests/`
    kończył `test_all.py` kodem 1 (poprawnie) — ale bez ani jednego wiersza `FAIL`
    i bez wiersza `N/M przeszło`. Sesja sprawdzająca zieloność przez
    `grep -cE '^\\s*FAIL'` dostawała zero i widziała zielono.

    Test podmienia `AG.paths()` (ta sama współdzielona funkcja modułu, którą woła
    `_discover()` w `test_all.py`) na dwa pliki w piaskownicy — jeden zepsuty, jeden
    poprawny — i uruchamia prawdziwe `main()` z `test_all.py` w tym samym procesie,
    bez dotykania prawdziwego `tools/tests/`. Podmiana jest cofana w `finally`
    niezależnie od wyniku, bo inaczej kolejne testy w tym samym przebiegu (np.
    `test_gate_paths_cover_this_file_and_test_all`) dostałyby okrojoną listę ścieżek.
    """
    import contextlib
    import io
    import re

    broken = os.path.join(_SANDBOX, "test_d19_broken_import_probe.py")
    with open(broken, "w", encoding="utf-8") as handle:
        handle.write("def test_broken(:\n    assert True\n")
    good = os.path.join(_SANDBOX, "test_d19_good_probe.py")
    with open(good, "w", encoding="utf-8") as handle:
        handle.write("def test_probe_ok():\n    assert True\n")

    test_all = AG.load_instrumented(TEST_ALL, "test_all_d19_probe")
    original_paths = AG.paths
    AG.paths = lambda: [broken, good]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = test_all.main()
    finally:
        AG.paths = original_paths

    output = buf.getvalue()
    assert code == 1, (code, output[-2000:])
    fail_lines = re.findall(r"^\s*FAIL.*$", output, re.MULTILINE)
    assert any("test_d19_broken_import_probe" in line for line in fail_lines), (
        "żaden wiersz FAIL nie nazywa modułu z błędem składni", fail_lines, output[-2000:])
    assert re.search(r"^\s*\d+/\d+ przeszło\s*$", output, re.MULTILINE), (
        "brak wiersza „N/M przeszło\" — mutation_sweep.py czyta z tego procesu "
        "dokładnie tę linię (6.D11)", output[-2000:])
    # Kontrola negatywna wbudowana: moduł POPRAWNY nie może zniknąć z powodu tego,
    # że jego sąsiad w tej samej podmianie padł na imporcie.
    assert "  ok   test_probe_ok" in output, output[-2000:]

def test_modul_wychodzacy_z_procesu_PRZY_IMPORCIE_jest_FAILEM_IMPORTU():
    """6.D65: drugie drzwi, ktore 6.D54 zostawilo otwarte.

    `SystemExit` NIE dziedziczy z `Exception`, wiec `except Exception` w petli
    importu go nie lapal — wychodzil z petli, z `main()` i z procesu, z kodem
    z wyjatku. Przy `sys.exit(0)` tym kodem bylo zero, a zestaw nie wypisywal ani
    jednego wiersza. Zmierzone 09.09.2026 na sondzie z jednym padajacym testem:
    bez galezi `kod 0 / 0 bajtow / 0 FAIL-i`, z galezia `kod 1 / 150120 bajtow /
    1 FAIL`.

    Ten test NIE tworzy pliku w `tools/tests/` — podstawia sam loader, bo mierzona
    jest galaz `except`, a nie odkrywanie plikow. Plik-sonda w katalogu skanowanym
    zapalilby przy okazji dwie inne bramki (o strazniku `__main__`), czyli mierzylby
    trzy rzeczy naraz.
    """
    import test_all as TA

    oryginalny = TA.AG.load_instrumented
    try:
        def wychodzi(_path, _name):
            raise SystemExit(0)

        TA.AG.load_instrumented = wychodzi
        tests, module_of, import_failures = TA._discover("test_assertion_gate.py")
    finally:
        TA.AG.load_instrumented = oryginalny

    assert tests == [], tests
    assert module_of == [], module_of
    assert len(import_failures) == 1, import_failures
    nazwa, blad = import_failures[0]
    assert nazwa == "test_assertion_gate", nazwa
    assert isinstance(blad, TA.WyjscieZImportu), type(blad).__name__
    assert "PRZY IMPORCIE" in str(blad), str(blad)
    assert "sys.exit(0)" in str(blad), str(blad)

    # STRUKTURALNY POWOD, dla ktorego ta galaz musi istniec osobno. Bez tej asercji
    # ktos moglby ja usunac w przekonaniu, ze `except Exception` wystarczy.
    assert not issubclass(SystemExit, Exception), (
        "SystemExit przestal byc poza Exception — ta galaz i jej powod trzeba wtedy "
        "przeczytac od nowa, a nie usunac")


def test_modul_z_bledem_skladni_nadal_jest_FAILEM_IMPORTU():
    """Kontrola, ze poprawka 6.D65 nie zabrala starej sciezki.

    **Czego ten test NIE pilnuje, i to jest poprawka do wlasnego uzasadnienia.**
    Pierwsza wersja tego docstringa mowila, ze galaz `SystemExit` musi stac PRZED
    `except Exception`, bo inaczej blad skladni przestanie byc raportowany. To
    NIEPRAWDA i zostalo zmierzone: po odwroceniu kolejnosci obu galezi modul
    przechodzi `25/25`. Kolejnosc jest nieistotna dokladnie z tego powodu, ktory
    czyni cala usterke 6.D65 mozliwa — `SystemExit` nie jest podklasa `Exception`,
    wiec zadna z tych galezi nie przechwytuje drugiej. Pilnuje tego asercja
    strukturalna w tescie wyzej, nie kolejnosc zapisu.

    Pilnowana jest wiec jedna rzecz: blad skladni nadal trafia do niepowodzen
    importu i NIE jest przekierowany do galezi 6.D65. Bez tego poprawka moglaby
    po cichu zamienic „modul sie nie kompiluje" na „modul wyszedl z procesu",
    czyli podstawic zla rade pod prawdziwy blad.
    """
    import test_all as TA

    oryginalny = TA.AG.load_instrumented
    try:
        def sypie(_path, _name):
            raise SyntaxError("celowo zly modul")

        TA.AG.load_instrumented = sypie
        tests, _module_of, import_failures = TA._discover("test_assertion_gate.py")
    finally:
        TA.AG.load_instrumented = oryginalny

    assert tests == [], tests
    assert len(import_failures) == 1, import_failures
    _nazwa, blad = import_failures[0]
    assert isinstance(blad, SyntaxError), type(blad).__name__
    assert not isinstance(blad, TA.WyjscieZImportu), "blad skladni trafil w zla galaz"


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

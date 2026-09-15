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
import re
import shutil
import subprocess
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


# --- 6.D127: asercje, które zgłaszają się bez ani jednego słowa -----------------

#: Katalog skanowany. Ten sam, którego dotyczy pole „Wejście" pozycji 6.D127.
KATALOG_TESTOW = os.path.join(ROOT, "tools", "tests")

#: **Zmierzone 11.09.2026 na `e0543cd`:** w `tools/tests/` stoi **6264** asercji,
#: z czego **3887** niesie komunikat, a **2377** nie niesie żadnego — w **103**
#: modułach ze 121.
#:
#: **Dlaczego lista jest PER MODUŁ, a nie per asercja.** Zamknięta lista 2377 pozycji
#: byłaby dłuższa od kodu, który opisuje, i rozjeżdżałaby się przy każdym przesunięciu
#: wiersza. Moduł jest najmniejszą jednostką, którą da się wymienić z nazwy i która
#: nie zmienia się od zmiany numeru wiersza.
#:
#: **Zapadka działa w OBIE strony i to jest treść pola „Skończone, gdy".** W górę:
#: dopisanie asercji bez komunikatu zapala bramkę, bo liczba przestaje się zgadzać.
#: W dół: dopisanie komunikatu też ją zapala — i to jest zamierzone, bo inaczej wpis
#: zostawałby zawyżony i zwalniał moduł z pilnowania tylu asercji, ile zdążył
#: naprawić. Obniżenie wpisu w tym samym commicie jest całym kosztem tej reguły.
#:
#: **Moduł spoza tej listy ma mieć ZERO.** Nowy plik testowy zaczyna z komunikatami
#: przy każdej asercji; dopisanie go tutaj jest świadomym cofnięciem i wymaga zdania
#: w commicie.
#:
#: **Czego ta bramka NIE robi:** nie poprawia dzisiejszych 2377 asercji. Pole „Poza
#: zakresem" pozycji 6.D127 mówi o tym wprost — to praca liniowa w ich liczbie
#: i osobna pozycja. Ta lista ma tylko móc **maleć**.
NIEME_ASERCJE = {
    "test_alignment.py": 77,
    "test_all.py": 68,
    "test_architecture_doc.py": 3,
    "test_art_direction.py": 15,
    "test_assertion_gate.py": 2,
    "test_audio_rights.py": 25,
    "test_backlog.py": 13,
    "test_backlog_commands.py": 3,
    "test_bin_path_framework.py": 15,
    "test_blender_cli.py": 17,
    "test_braking.py": 13,
    "test_camera_aim.py": 39,
    "test_capture_plan.py": 39,
    "test_chunks.py": 65,
    "test_ci_workflows.py": 64,
    "test_clearance.py": 30,
    "test_crosscheck_alignment.py": 37,
    "test_crs.py": 1,
    "test_crs_convergence.py": 1,
    "test_curve_radius_axes.py": 8,
    "test_data_freshness.py": 17,
    "test_dead_constants.py": 1,
    "test_dead_constants_csharp.py": 1,
    "test_detail_layout.py": 59,
    "test_detail_markers.py": 17,
    "test_dimension_audit.py": 17,
    "test_docs_ci_claims.py": 33,
    "test_doctor_queue_claim.py": 1,
    "test_dotnet_version.py": 13,
    "test_engine_version.py": 11,
    "test_environment_doc.py": 6,
    "test_fetchers.py": 18,
    "test_field_paths.py": 50,
    "test_game_needle_specificity.py": 4,
    "test_glb_report.py": 33,
    "test_godot_warning_gate.py": 13,
    "test_gtfs_stops.py": 40,
    "test_hexdigest_truncation.py": 1,
    "test_inspire_rail.py": 102,
    "test_line_calls_gate.py": 4,
    "test_line_trace_gate.py": 12,
    "test_linecore_budget_gate.py": 10,
    "test_lod.py": 81,
    "test_lod_paths.py": 7,
    "test_m7_cab.py": 1,
    "test_m7_report.py": 22,
    "test_m7_shell.py": 38,
    "test_make_test_track.py": 10,
    "test_manifest_write_policy.py": 6,
    "test_marker_gates.py": 5,
    "test_material_specs.py": 18,
    "test_mutation_sweep.py": 76,
    "test_needle_specificity.py": 3,
    "test_network_chainage.py": 20,
    "test_next_task.py": 1,
    "test_osm_api_fallback.py": 22,
    "test_osm_tile_cache.py": 13,
    "test_packages.py": 30,
    "test_parameter_boundaries.py": 44,
    "test_placement.py": 45,
    "test_platform_dimensions.py": 11,
    "test_platform_length_in_pipeline.py": 1,
    "test_png_pixels.py": 2,
    "test_pr_template.py": 16,
    "test_profile_scan.py": 33,
    "test_provenance_retrieved_at_claim.py": 2,
    "test_readme_claims.py": 22,
    "test_reference_snapshot.py": 1,
    "test_render_engine.py": 6,
    "test_report_claims.py": 15,
    "test_report_hygiene.py": 28,
    "test_rights_matrix.py": 3,
    "test_run_mode_claims.py": 7,
    "test_scan_gates.py": 12,
    "test_schedule_envelope.py": 32,
    "test_shot_metadata_gate.py": 15,
    "test_sim_untested_members.py": 2,
    "test_snapshot_source.py": 16,
    "test_station_components.py": 6,
    "test_station_kit.py": 19,
    "test_station_layout.py": 23,
    "test_station_sections.py": 8,
    "test_stations.py": 22,
    "test_stop_names.py": 1,
    "test_streaming_fixture.py": 1,
    "test_suite_runtime_budget.py": 6,
    "test_surface_sections.py": 84,
    "test_sweep.py": 57,
    "test_t401_citation.py": 6,
    "test_timetable.py": 75,
    "test_timing_record.py": 4,
    "test_tree_walks.py": 3,
    "test_tuning_constants.py": 3,
    "test_tunnel_manifest.py": 42,
    "test_tunnel_width.py": 73,
    "test_validate_axis.py": 9,
    "test_vehicle_fit.py": 23,
    "test_vertical_profile.py": 4,
    "test_visual.py": 92,
    "test_visual_gates.py": 14,
    "test_visual_identical_pixels.py": 9,
    "test_xml_doc_blocks.py": 6,
}

#: Suma z listy wyżej, LICZONA, nie wpisana. Wpisana ręcznie rozjechałaby się przy
#: pierwszym obniżonym wpisie — czyli dokładnie wtedy, gdy ktoś tę listę poprawia.
NIEMYCH_RAZEM = sum(NIEME_ASERCJE.values())


def _moduly_testowe(katalog=None):
    """Ścieżki `<katalog>/*.py`, tą samą drogą co reszta skanów drzewa.

    Argument jest po to, żeby kontrole tej bramki mogły puścić JĄ SAMĄ po drzewie
    probnym, zamiast składać u siebie drugi skan tego samego kształtu (6.B28).
    Domyślnie `KATALOG_TESTOW`, czyli to, co bramka mierzy naprawdę.
    """
    import tree_walk as TW

    baza_skanu = KATALOG_TESTOW if katalog is None else katalog
    korzen = ROOT if katalog is None else katalog
    znalezione = []
    for baza, _katalogi, pliki in TW.walk(baza_skanu, korzen):
        znalezione += [os.path.join(baza, n) for n in pliki if n.endswith(".py")]
    return sorted(znalezione)


def komunikat_nic_nie_mowi(msg):
    """Czy ten węzeł komunikatu jest obecny, ale pusty — 6.D144.

    **Dopisane po kontroli negatywnej KN-2, która wyszła ZIELONA.** Do 6.D144 licznik
    pytał wyłącznie o `msg is None`, więc `assert x, ""` przechodził jako asercja
    Z powodem. Moduł dałoby się zbić do zera samym dopisaniem przecinka i pary
    cudzysłowów, a bramka zameldowałaby sprawdzenie, którego nie zrobiła — dokładnie
    ta rodzina, którą projekt tropi od 6.D27, tym razem w przyrządzie, na którym
    stoi cała pozycja 6.D144.

    Zamknięcie tej dziury **nie ruszyło ani jednej liczby**: zmierzone 11.09.2026 na
    całym `tools/tests/` — asercji z komunikatem nic nie mówiącym było **zero**.
    Bramka pilnuje więc czegoś, czego dziś nikt nie robi, i o to chodzi.

    Czego to NIE łapie i nie może: komunikatu, który powtarza warunek zamiast podawać
    powód. `assert a == b, "a != b"` przejdzie tu tak samo jak zdanie o przyczynie —
    rozróżnienie wymaga semantyki, a nie kształtu. Granica jest tu wypisana, żeby
    zielona bramka nie czytała się jako „każdy komunikat coś mówi".
    """
    if isinstance(msg, ast.Constant):
        if msg.value is None:
            return True
        if isinstance(msg.value, str):
            return not msg.value.strip()
        return msg.value is False or msg.value == 0
    if isinstance(msg, ast.JoinedStr):
        return not msg.values
    return False


def asercje_bez_komunikatu(zrodlo):
    """Ile `assert` w tym źródle nie niesie POWODU.

    Liczone z DRZEWA SKŁADNI, nie grepem: `assert x, "powód"` i `assert x` różnią
    się obecnością pola `msg`, a nie obecnością przecinka — `assert (a, b)` ma
    przecinek i komunikatu nie ma (jest zawsze prawdziwy, bo krotka).

    Brakiem powodu jest też komunikat OBECNY, ale pusty — patrz
    `komunikat_nic_nie_mowi` i kontrola KN-2 z 6.D144.
    """
    try:
        drzewo = ast.parse(zrodlo)
    except SyntaxError:
        return None
    return sum(1 for w in ast.walk(drzewo)
               if isinstance(w, ast.Assert)
               and (w.msg is None or komunikat_nic_nie_mowi(w.msg)))


def nieme_w_drzewie(katalog=None):
    """`{nazwa modułu: ile}` — tylko moduły, w których jest co najmniej jedna."""
    policzone = {}
    for sciezka in _moduly_testowe(katalog):
        with open(sciezka, encoding="utf-8") as uchwyt:
            ile = asercje_bez_komunikatu(uchwyt.read())
        if ile:
            policzone[os.path.basename(sciezka)] = ile
    return policzone


def _zapisz(katalog, nazwa, tresc):
    """Plik w drzewie probnym; zwraca ścieżkę."""
    sciezka = os.path.join(katalog, nazwa)
    with open(sciezka, "w", encoding="utf-8") as uchwyt:
        uchwyt.write(tresc)
    return sciezka


def moduly_zaslepione(katalog=None):
    """Moduły, które w TYM drzewie są zaślepką przeglądu mutacyjnego, nie sobą.

    **Skąd ten wyjątek, 11.09.2026.** Przegląd mutacyjny pracuje na kopii
    `git worktree add --detach HEAD`, w której `neutralise_own_tests` podmienia
    `tools/tests/test_mutation_sweep.py` na zaślepkę — plik ZOSTAJE, bo jego ścieżkę
    wymieniają raporty, ale treści już nie ma. Zaślepka nie ma ani jednej asercji bez
    komunikatu, więc zapadka widziała wpis dla modułu, „który zniknął z drzewa",
    i żądała jego zdjęcia. Skutek nie jest czerwonym testem: `baseline_problem` czyta
    to jako „zestaw PADA w czystym drzewie" i **przerywa przegląd przed pierwszą
    mutacją**. Zmierzone na `6d9c5dc`: zestaw w drzewie roboczym daje **2189/2190,
    kod 1**, a `mutation_sweep.py --only lod_paths` kończy kodem 2 i nie liczy nic.

    Wyjątek NIE jest zgodą na moduł bez komunikatów: dotyczy pliku, który sam przegląd
    podłożył, rozpoznanego po CAŁEJ treści przez `mutation_sweep.czy_zaslepka`, i tylko
    w tym drzewie, w którym leży. W drzewie repozytorium zbiór jest **pusty** i test
    niżej tego pilnuje — inaczej wyjątek zwalniałby moduł z bramki na co dzień.
    """
    import mutation_sweep as MS

    zaslepione = set()
    for sciezka in _moduly_testowe(katalog):
        with open(sciezka, encoding="utf-8") as uchwyt:
            if MS.czy_zaslepka(uchwyt.read()):
                zaslepione.add(os.path.basename(sciezka))
    return zaslepione


def test_lista_asercji_bez_komunikatu_moze_tylko_malec():
    """Zapadka z obu stron na liczbie asercji bez komunikatu — 6.D127.

    **Po co.** Czerwień bez zdania każe czytać KOD zamiast komunikatu, a w CI czyta
    się wypis, nie kod. Zmierzone dwa razy: KN-3 przy 6.D117 dała
    `FAIL test_generated_files_are_excluded_from_the_count:` — dwukropek i nic dalej;
    to samo zauważono przy 6.D106. Przy przebiegu, w którym pada kilkanaście testów
    naraz, asercja bez komunikatu jest nieodróżnialna od asercji, której nikt nie
    napisał.
    """
    import mutation_sweep as MS

    w_drzewie = nieme_w_drzewie()
    zaslepione = moduly_zaslepione()
    # **Szerokość wyjątku sprawdzana TUTAJ, a nie tylko w osobnym teście, i zrobiła
    # to kontrola KN-3, która wyszła ZIELONA.** Osobny test woła `moduly_zaslepione()`
    # po swojemu, więc rozlanie wyjątku W TYM MIEJSCU było dla niego niewidzialne:
    # podstawienie `set(NIEME_ASERCJE)` opróżnia `w_drzewie` ze wszystkiego, co lista
    # pilnuje, a suma dostaje te same 2377 z drugiego składnika — zapadka staje się
    # PUSTA i zostaje zielona. Asercja niżej jest jedyną, która to łapie.
    assert zaslepione <= {MS.WLASNE_TESTY[-1]}, (
        "wyjątek użyty przez zapadkę objął moduł, którego przegląd nie podmienia: "
        "%s — zapadka zwolniona z pilnowania modułu zostaje zielona i o niczym nie "
        "mówi" % sorted(zaslepione - {MS.WLASNE_TESTY[-1]}))
    # Moduł podmieniony na zaślepkę nie jest sobą, więc nie jest mierzony — ani
    # w tę stronę, że „ubyło", ani w tę, że „zniknął". Jego wpis z listy wchodzi
    # do sumy osobno, niżej, bo inaczej suma mówiłaby o drzewie o jeden moduł
    # mniejszym, nie zdradzając tego ani słowem.
    w_drzewie = {n: ile for n, ile in w_drzewie.items() if n not in zaslepione}

    nowe = {n: ile for n, ile in w_drzewie.items() if n not in NIEME_ASERCJE}
    assert nowe == {}, (
        "moduł spoza listy ma asercje bez komunikatu: %s — nowy plik testowy "
        "zaczyna z komunikatem przy każdej asercji" % sorted(nowe.items()))

    znikniete = {n: ile for n, ile in NIEME_ASERCJE.items()
                 if n not in w_drzewie and n not in zaslepione}
    assert znikniete == {}, (
        "wpis na liście dla modułu, który już nie ma ani jednej takiej asercji "
        "(albo zniknął z drzewa): %s — zdejmij wpis w tym samym commicie"
        % sorted(znikniete))

    wzroslo = [(n, NIEME_ASERCJE[n], ile) for n, ile in sorted(w_drzewie.items())
               if ile > NIEME_ASERCJE.get(n, 0)]
    assert wzroslo == [], (
        "asercji bez komunikatu PRZYBYŁO (moduł, było, jest): %s — nowa asercja "
        "ma nieść powód" % wzroslo)

    zmalalo = [(n, NIEME_ASERCJE[n], ile) for n, ile in sorted(w_drzewie.items())
               if ile < NIEME_ASERCJE.get(n, 0)]
    assert zmalalo == [], (
        "asercji bez komunikatu UBYŁO (moduł, było, jest): %s — obniż wpis w tym "
        "samym commicie, inaczej lista zwalnia moduł z pilnowania tylu asercji, "
        "ile zdążył naprawić" % zmalalo)

    # Bramka nie przechodzi pusta: pusty skan znaczy zepsute liczenie, a nie zgodę.
    assert len(_moduly_testowe()) > 100, (
        "skan widzi %d modułów — liczenie jest zepsute, a nie drzewo puste"
        % len(_moduly_testowe()))
    # Asercje modułów zaślepionych są POLICZONE Z LISTY, a nie pominięte: suma ma
    # dotyczyć tego samego zbioru modułów, o którym mówi zapadka. Gdy zaślepki nie
    # ma — a w drzewie repozytorium nie ma — składnik jest zerem i nic się nie zmienia.
    zaslepione_z_listy = sum(NIEME_ASERCJE[n] for n in zaslepione if n in NIEME_ASERCJE)
    # **2255 -> 2254 (13.09.2026, MB-01).** `test_shot_metadata_gate.py` zszedł z 16
    # na 15: asercja porównująca pozycje `--chunk-manifest` i `--manifest` w jednym
    # pliku była NIEMA, a zastąpiła ją para asercji Z KOMUNIKATEM (przepis generacji
    # wyprowadził się z workflowa do `tools/dev/prepare-playable.sh`). Zapadka „może
    # tylko maleć" działa więc tak, jak ma: wpis obniżony w tym samym commicie.
    assert NIEMYCH_RAZEM == sum(w_drzewie.values()) + zaslepione_z_listy == 2254, (
        "suma z listy %d, suma z drzewa %d (+ %d z %d modułów zaślepionych: %s), "
        "pomiar z 11.09.2026 mówił 2377, po 6.D135 jest 2376, po 6.D138 — 2372, "
        "po 6.D144 — 2255, bo `test_clearance_profile.py` zszedł ze 117 na ZERO "
        "i wypadł z listy, a po MB-01 — 2254"
        % (NIEMYCH_RAZEM, sum(w_drzewie.values()), zaslepione_z_listy,
           len(zaslepione), sorted(zaslepione) or "—"))


def test_licznik_odroznia_assert_z_powodem_od_assert_bez():
    """Kontrola przyrządu: różnica `assert x` kontra `assert x, "powód"` — na wejściu
    syntetycznym, bo na drzewie obie wersje dają tę samą zieleń.

    Trzeci przypadek jest tu najważniejszy i nie jest hipotetyczny: `assert (a, b)`
    MA przecinek, a komunikatu nie ma — jest krotką, czyli zawsze prawdziwy. Grep po
    przecinku policzyłby go jako asercję z powodem i przepuścił test, który nie
    sprawdza NICZEGO.
    """
    assert asercje_bez_komunikatu("assert x\n") == 1, "goły `assert` nie został policzony"
    assert asercje_bez_komunikatu('assert x, "powod"\n') == 0, (
        "asercja Z komunikatem policzona jako niema")
    assert asercje_bez_komunikatu("assert (a, b)\n") == 1, (
        "`assert (a, b)` policzone jako asercja z komunikatem — a to krotka, "
        "czyli asercja zawsze prawdziwa")
    assert asercje_bez_komunikatu("assert x\nassert y, 'p'\nassert z\n") == 2, (
        "licznik nie rozdziela trzech asercji w jednym źródle")
    assert asercje_bez_komunikatu("x = 1\n") == 0, (
        "źródło bez ani jednej asercji dało wynik niezerowy")
    assert asercje_bez_komunikatu("def f(:\n") is None, (
        "plik z błędem składni ma dać None, a nie zero — zero czytałoby się "
        "jako „sprawdzone i czysto\u201d")

    # Komunikat OBECNY, ale pusty — dopisane po kontroli KN-2 z 6.D144, która
    # wyszła zielona. Bez tych pięciu wierszy moduł dałoby się zbić do zera samym
    # dopisaniem przecinka i pary cudzysłowów.
    for pusty in ('assert x, ""\n', "assert x, '   '\n", "assert x, None\n",
                  "assert x, 0\n", "assert x, False\n", 'assert x, f""\n'):
        assert asercje_bez_komunikatu(pusty) == 1, (
            "komunikat, który nic nie mówi, policzony jako powód: %r" % pusty)
    assert asercje_bez_komunikatu('assert x, "0"\n') == 0, (
        "napis „0” JEST treścią — bramka ma odsiewać puste, a nie fałszywe")
    assert asercje_bez_komunikatu("assert x, f'{y}'\n") == 0, (
        "f-string z dziurą niesie treść i ma być liczony jako powód")

    # I że skan naprawdę czyta pliki z drzewa, a nie tylko umie parsować napisy.
    wlasny = os.path.join(KATALOG_TESTOW, "test_assertion_gate.py")
    assert wlasny in _moduly_testowe(), "skan nie widzi nawet siebie"


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
    # KATALOG PRYWATNY, NIE STAŁA NAZWA W `/tmp` — 6.D84.
    #
    # Poprzednia wersja brała `tempfile.gettempdir()` + stałą nazwę i tylko ZAKŁADAŁA,
    # że nikt jej nie zajął. Zmierzone 09.09.2026 i odtworzone 10.09.2026: po
    # utworzeniu pliku pod tą nazwą moduł schodzi z **27/27 na 26/27**, a pada nie
    # ten test, który coś mierzy, tylko jego strażnik. Fałszywy alarm zależny od
    # OBCEGO stanu jest w tym projekcie osobną kategorią (6.D27): bramkę, która pada
    # nie ze swojego powodu, ktoś w końcu wyłączy.
    #
    # Katalog jest tworzony przez `TemporaryDirectory`, a ścieżka wskazuje jego
    # NIEUTWORZONE dziecko — więc nieistnienie jest tu SKONSTRUOWANE. Asercja mimo to
    # zostaje, bo skonstruowany warunek i tak trzeba udowodnić: ten sam wzorzec, co
    # w 6.D57. Po tej zmianie test sprawdza dwie rzeczy zamiast jednej.
    with tempfile.TemporaryDirectory(prefix="mbxl-bramka-asercji-") as katalog:
        nieistniejacy = os.path.join(katalog, "nie-ma-takiego-katalogu", "chunks.json")
        # DWIE rzeczy, nie jedna. Sama nieobecność ścieżki jest prawdziwa także dla
        # literówki w nazwie zmiennej albo dla katalogu, którego nigdy nie utworzono —
        # a wtedy test przechodzi, nie mierząc niczego. Ten wiersz przybija, że
        # ścieżka leży W ISTNIEJĄCYM katalogu prywatnym, czyli że brak dotyczy
        # dziecka, a nie całej gałęzi.
        assert os.path.isdir(katalog), (
            f'katalog prywatny nie powstał: {katalog} — nieobecność ścieżki niżej '
            'nie znaczyłaby wtedy nic')
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
def test_asercje_zyja_takze_pod_wylaczonymi_asercjami_interpretera():
    """Moduł testowy kompiluje się z `optimize=0`, a nie z trybu interpretera (6.D71).

    **Skąd.** Licznik sprawdzeń wstawia przekształcenie drzewa, a nie sama asercja.
    Pod `python3 -O` kompilator zdejmuje `assert`, a wstrzyknięte wywołanie licznika
    zostaje — więc wyrocznia meldowała sprawdzenie, którego nie było. Zmierzone
    09.09.2026 na module z jedną asercją, która MA padać:

        bez -O:  padła: ta asercja MA padać   sprawdzeń: 1
        z  -O:   PRZESZŁA (asercja zdjęta)    sprawdzeń: 1

    To ta sama rodzina co 6.D65, tylko utajona: dziś nic w repozytorium nie ustawia
    `PYTHONOPTIMIZE` ani nie woła interpretera z `-O`, więc scenariusz nie ma drogi
    wywołania — ale wyrocznia zieloności nie ma prawa zależeć od tego, jak ktoś
    kiedyś uruchomi zestaw.

    Test odpala **OSOBNY interpreter z `-O`**, bo trybu własnego procesu nie da się
    zmienić w locie: `sys.flags.optimize` jest tylko do odczytu, a testowanie tego
    przez podmianę `compile` sprawdzałoby atrapę, nie zachowanie.
    """
    import subprocess
    import textwrap

    program = textwrap.dedent(f'''
        import os, sys, tempfile
        sys.path.insert(0, {os.path.join(ROOT, "tools", "tests")!r})
        import assertion_gate as AG
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "test_sonda.py")
            open(p, "w", encoding="utf-8").write(
                "def test_pada():\\n    assert False, 'ma padać'\\n")
            modul = AG.load_instrumented(p, "test_sonda")
            przed = AG.hits()
            try:
                modul.test_pada()
                print("PRZESZLA", AG.hits() - przed, sys.flags.optimize)
            except AssertionError:
                print("PADLA", AG.hits() - przed, sys.flags.optimize)
    ''')

    for flagi, opis in (([], "bez -O"), (["-O"], "z -O")):
        done = subprocess.run([sys.executable] + flagi + ["-c", program],
                              capture_output=True, text=True, timeout=120)
        assert done.returncode == 0, (opis, done.stderr[-400:])
        wynik = done.stdout.split()
        assert wynik[0] == "PADLA", (
            f"{opis}: asercja, która ma padać, {wynik[0]} — kompilacja modułu testowego "
            "dziedziczy tryb interpretera zamiast `optimize=0`")
        assert wynik[1] == "1", (opis, "licznik sprawdzeń zgubił trafienie", done.stdout)
    # Kontrola przyrządu: drugi przebieg MA iść z `-O`, inaczej test dwa razy sprawdza
    # to samo i milczy o jedynym scenariuszu, dla którego powstał.
    done = subprocess.run([sys.executable, "-O", "-c", program],
                          capture_output=True, text=True, timeout=120)
    assert done.stdout.split()[2] == "1", (
        "podproces z `-O` nie ma włączonej optymalizacji — test sprawdza dwa razy "
        f"ten sam tryb: {done.stdout!r}")


def test_kompilacja_modulu_testowego_zada_optimize_wprost():
    """Wartość jest w kodzie JAWNIE, nie domyślnie — inaczej wróci po cichu.

    Poprzedni test złapałby regres, ale dopiero na podprocesie; ta bramka mówi to
    samo o źródle i tłumaczy, czego szukać, gdy tamten się zapali.
    """
    zrodlo = open(os.path.join(ROOT, "tools", "tests", "assertion_gate.py"),
                  encoding="utf-8").read()
    kod = "\n".join(l for l in zrodlo.splitlines() if not l.lstrip().startswith("#"))
    assert "optimize=0" in kod, (
        "`compile` modułu testowego nie podaje `optimize`, więc tryb dziedziczy się "
        "z interpretera i pod `-O` asercje znikają spod licznika")
    assert "dont_inherit=True" in kod, (
        "`compile` bez `dont_inherit` dziedziczy flagi __future__ i tryb z wołającego")


def test_wyjatek_nie_obejmuje_zadnego_modulu_poza_wlasnymi_testami_przegladu():
    """Wyjątek ma być wyjątkiem, a nie furtką — i to jest zdanie prawdziwe w OBU drzewach.

    **Ten test jest przepisany, a nie dopisany obok, i zrobił to pomiar.** Pierwsza
    wersja żądała zbioru PUSTEGO, „bo zaślepka ma prawo istnieć wyłącznie w drzewie
    roboczym przeglądu". Zdanie jest prawdziwe, a bramka z niego zrobiona — nie:
    zestaw w drzewie roboczym z zaślepką dał **2193/2194, kod 1**, czyli dokładnie
    ten sam skutek, przed którym wyjątek miał bronić (`baseline_problem` przerywa
    przegląd). Bramka nie umie odróżnić repozytorium od jego kopii roboczej, bo
    treść pliku wygląda w obu tak samo.

    Dzisiejsza wersja pilnuje tego, co da się sprawdzić z samej treści: wyjątek
    obejmuje **wyłącznie** moduł, który przegląd sam podmienia. Za „zaślepka nie
    została zacommitowana" odpowiada osobny test, pytający o to, o co trzeba —
    o zawartość HEAD, a nie dysku.
    """
    import mutation_sweep as MS

    wolno = {MS.WLASNE_TESTY[-1]}
    zaslepione = moduly_zaslepione()
    assert zaslepione <= wolno, (
        "wyjątek objął moduł, którego przegląd nie podmienia: %s — wolno mu "
        "obejmować tylko %s" % (sorted(zaslepione - wolno), sorted(wolno)))


def test_zaslepka_nie_jest_tym_co_stoi_w_HEAD():
    """Zaślepka w drzewie roboczym jest w porządku; zaślepka w HEAD to utrata testów.

    Pytanie stawiane jest gitowi, a nie dyskowi, bo tylko ono rozróżnia oba
    przypadki: w kopii roboczej przeglądu na dysku leży zaślepka, a w HEAD prawdziwe
    testy — i to jest stan poprawny, którego poprzednia wersja poprzedniego testu
    nie umiała odróżnić od awarii.
    """
    import mutation_sweep as MS

    sciezka = "/".join(MS.WLASNE_TESTY)
    wynik = subprocess.run(["git", "show", f"HEAD:{sciezka}"],
                           cwd=ROOT, capture_output=True, text=True)
    assert wynik.returncode == 0, (
        "`git show HEAD:%s` skończyło kodem %d — bez odpowiedzi gita ta bramka nie "
        "wie, czy zaślepka jest zacommitowana, więc milczy tylko wtedy, gdy WIE; "
        "stderr: %s" % (sciezka, wynik.returncode, wynik.stderr.strip()[:200]))
    assert not MS.czy_zaslepka(wynik.stdout), (
        "w HEAD pod %s stoi zaślepka przeglądu — prawdziwe testy narzędzia zostały "
        "zacommitowane jako zdjęte" % sciezka)


def test_zaslepka_w_drzewie_probnym_jest_rozpoznana_a_podobna_do_niej_nie():
    """Kontrola przyrządu na drzewie probnym, obie strony w jednym teście.

    Rozpoznanie idzie przez `mutation_sweep.czy_zaslepka`, czyli przez CAŁĄ treść.
    Drugi plik różni się od zaślepki **jedną literą** i ma być policzony normalnie —
    inaczej wyjątek zwalniałby z bramki każdy plik, który zaczyna się tak samo.
    """
    import mutation_sweep as MS

    with tempfile.TemporaryDirectory(prefix="metro-zaslepka-") as katalog:
        _zapisz(katalog, "test_prawdziwy.py", "assert 1\nassert 2\n")
        _zapisz(katalog, "test_mutation_sweep.py", MS.OWN_TESTS_STUB)
        _zapisz(katalog, "test_prawie_zaslepka.py", MS.OWN_TESTS_STUB + "assert 1\n")

        zaslepione = moduly_zaslepione(katalog)
        assert zaslepione == {"test_mutation_sweep.py"}, (
            "rozpoznane jako zaślepki: %s — miał być dokładnie jeden plik, ten "
            "podłożony przez przegląd" % sorted(zaslepione))

        w_drzewie = nieme_w_drzewie(katalog)
        assert w_drzewie == {"test_prawdziwy.py": 2, "test_prawie_zaslepka.py": 1}, (
            "licznik na drzewie probnym dał %s — plik różniący się od zaślepki jedną "
            "asercją ma być policzony normalnie" % sorted(w_drzewie.items()))


def test_bez_wyjatku_zapadka_zapalilaby_sie_na_drzewie_roboczym_przegladu():
    """Pomiar, który ten wyjątek uzasadnia — na drzewie probnym, nie na opowieści.

    Po lewej stronie stoi warunek SPRZED poprawki (`n not in w_drzewie`), po prawej
    dzisiejszy. Test nie mierzy kodu bramki, tylko RÓŻNICĘ, którą wyjątek robi:
    bez niego moduł zaślepiony jest „modułem, który zniknął z drzewa", a to w drzewie
    roboczym przeglądu znaczy `baseline_problem` → przerwanie przed pierwszą mutacją.
    """
    import mutation_sweep as MS

    with tempfile.TemporaryDirectory(prefix="metro-zaslepka-") as katalog:
        _zapisz(katalog, "test_prawdziwy.py", "assert 1\nassert 2\n")
        _zapisz(katalog, "test_mutation_sweep.py", MS.OWN_TESTS_STUB)

        lista = {"test_prawdziwy.py": 2, "test_mutation_sweep.py": 7}
        w_drzewie = nieme_w_drzewie(katalog)
        zaslepione = moduly_zaslepione(katalog)

        bez_wyjatku = {n: ile for n, ile in lista.items() if n not in w_drzewie}
        assert bez_wyjatku == {"test_mutation_sweep.py": 7}, (
            "warunek sprzed poprawki miał zgłosić zaślepiony moduł, a zgłosił %s"
            % sorted(bez_wyjatku.items()))

        z_wyjatkiem = {n: ile for n, ile in lista.items()
                       if n not in w_drzewie and n not in zaslepione}
        assert z_wyjatkiem == {}, (
            "dzisiejszy warunek nadal coś zgłasza: %s" % sorted(z_wyjatkiem.items()))

        # Drugi składnik sumy — ten sam rachunek, co w zapadce, wykonany tutaj,
        # bo na drzewie repozytorium jest ZEREM i nie ćwiczy go nic. Bez tych trzech
        # wierszy składnik byłby ubezpieczeniem, o którym wiadomo tylko tyle, że się
        # kompiluje (ta sama lekcja co maska w 6.D131).
        zaslepione_z_listy = sum(lista[n] for n in zaslepione if n in lista)
        assert zaslepione_z_listy == 7, (
            "z listy doliczono %d, a zaślepiony moduł ma tam wpis 7"
            % zaslepione_z_listy)
        assert sum(w_drzewie.values()) + zaslepione_z_listy == sum(lista.values()), (
            "suma drzewa %d + %d z listy nie schodzi się z sumą listy %d — zapadka "
            "mówiłaby wtedy o drzewie o jeden moduł mniejszym, nie zdradzając tego"
            % (sum(w_drzewie.values()), zaslepione_z_listy, sum(lista.values())))


def test_obie_bramki_czytaja_nazwe_wlasnych_testow_z_jednego_miejsca():
    """`WLASNE_TESTY` ma być JEDYNYM zapisem tej nazwy po stronie przeglądu.

    Gdyby `neutralise_own_tests` składała ścieżkę u siebie, a wyjątek wpisywał nazwę
    u siebie, przemianowanie modułu rozjechałoby je po cichu — i objawiłoby się
    dopiero przerwanym przeglądem, czyli tam, gdzie nikt nie szuka (6.B28).
    """
    import mutation_sweep as MS

    assert MS.WLASNE_TESTY[-1] == "test_mutation_sweep.py", MS.WLASNE_TESTY
    zrodlo = open(os.path.join(ROOT, "tools", "tests", "mutation_sweep.py"),
                  encoding="utf-8").read()
    kod = "\n".join(l for l in zrodlo.splitlines()
                    if not l.lstrip().startswith("#") and not l.lstrip().startswith("#:"))
    wprost = kod.count('"test_mutation_sweep.py"')
    assert wprost == 1, (
        "nazwa własnych testów stoi w kodzie `mutation_sweep.py` %d razy — ma stać "
        "raz, w `WLASNE_TESTY`, a reszta ma ją czytać stamtąd" % wprost)


# --- 6.D161: zdania „ubezpieczenie", i ile z nich ma pod sobą wejście --------------
#
# **Skąd ta sekcja.** 6.D147, 6.D148 i 6.D149 — trzy pozycje pod rząd — miały kontrolę
# negatywną, która wyszła ZIELONA z tego samego powodu: mechanizm jest poprawny, ale
# żadne dzisiejsze wejście z drzewa nie odróżnia go od jego braku. Ile takich zdań stoi
# w drzewie i ile z nich ma pod sobą wejście syntetyczne, nie policzył nikt.
#
# **GRANICA TEGO POMIARU, powiedziana wprost, bo jest jego najważniejszą częścią.**
# Wzorzec niżej znajduje zdania, które się do tego PRZYZNAJĄ — słowem „ubezpieczenie",
# „zmierzona konieczność" albo „kontrola wyszła ZIELONA". Rodziny to NIE wyczerpuje
# i zmierzyłem, że nie: pole „Dlaczego" pozycji 6.D161 wymienia jako jej członków
# `SUROWY` i `argumenty_z_nawiasami`, a **żadne z nich nie niesie ani jednego z tych
# słów**. Pierwsze uzasadnia się kosztem skanu i szczelnością odsiania, drugie podaje
# pomiar („różnicy nie ma ani jednej") bez nazwania go ubezpieczeniem. Liczba niżej
# jest więc liczbą zdań JAWNYCH, a nie liczbą mechanizmów bez pokrycia — tej drugiej
# z tekstu wyprowadzić się nie da i ten komentarz stoi zamiast niej.

#: Miejsce, od którego zaczyna się własna sekcja 6.D161 tego pliku. Wszystko od tego
#: napisu w dół jest ze skanu WYCIĘTE — powód w `zdania_rodziny`. Napis wskazuje
#: NAGŁÓWEK sekcji, a nie pierwszą stałą pod nim: nagłówek też wymienia słowa wzorca,
#: więc cięcie niżej zostawiało jedno trafienie o sobie samym (19 zamiast 18).
ZNACZNIK_WLASNEJ_SEKCJI = "# --- 6.D161: zdania "

#: Zdanie przyznające się do rodziny. Trzy sformułowania, wszystkie z pola „Wejście"
#: pozycji 6.D161.
RODZINA_UBEZPIECZENIA = re.compile(
    r"ubezpieczeni\w*"
    r"|nie\s+zmierzon\w+\s+konieczno\w+"
    r"|zmierzon\w+\s+konieczno\w+"
    r"|wysz(?:ł|l)a\s+ZIELONA"
    r"|wysz(?:ł|l)a\s+zielona",
    re.IGNORECASE)

#: Ile zdań rodziny stoi w `tools/tests/`. Zapadka RÓWNOŚCIOWA, nie minimum:
#: dopisanie zdania ma zmusić do rozstrzygnięcia, czy niesie pokrycie, a nie
#: przejść samo.
ZDAN_RODZINY_RAZEM = 24

#: **Wszystkie zdania rodziny, przeczytane po kolei, w DWÓCH workach** —
#: `(plik, zakres) -> powód`. **Liczby w tym zdaniu NIE MA i to jest wybór po pomiarze
#: (6.D191).** Stało tu „wszystkie osiemnaście", zmierzone 13.09.2026 przy 6.D161 —
#: i było nieprawdą już nazajutrz, gdy 6.D165 dopisało dziewiętnaste zdanie, a 6.D191
#: dwudzieste i dwudzieste pierwsze. **Nie złapała tego żadna bramka i złapać nie mogła:**
#: `test_prose_counts.py` porównuje z drzewem liczby stojące w prozie OBOK zapadki, a ta
#: stała nazywa się `ZDAN_RODZINY_RAZEM` i jest tuż wyżej — tylko że liczba w prozie stała
#: SŁOWNIE, a tamta bramka czyta cyfry. Liczba jest więc zdjęta zamiast poprawiona: stoi
#: w stałej, i jedna kopia wystarczy (6.B28).
#:
#: Podział jest ręczny i to jest wybór z pomiaru, nie
#: lenistwo: automat szukający markera wejścia syntetycznego w obejmującej definicji
#: dał **cztery trafienia fałszywe na dwanaście**, wszystkie tam, gdzie zakresem jest
#: moduł albo funkcja na czterysta wierszy, a marker leżał 179 do 437 wierszy od
#: zdania. Liczba wyprowadzona z takiego automatu byłaby dokładnie tym „cichym
#: sitem", którego ta pozycja szuka — więc liczby nie ma, jest lista.
Z_WEJSCIEM_SYNTETYCZNYM = {
    ("tools/tests/test_assertion_gate.py",
     "test_licznik_odroznia_assert_z_powodem_od_assert_bez"):
        "kontrola przyrządu na wejściu zbudowanym na tę okazję, a nie na drzewie",
    ("tools/tests/test_assertion_gate.py",
     "test_bez_wyjatku_zapadka_zapalilaby_sie_na_drzewie_roboczym_przegladu"):
        "drzewo próbne w katalogu tymczasowym, budowane na tę jedną gałąź",
    ("tools/tests/test_ci_workflows.py", "_cialo_z_tekstu"):
        "docstring mówi wprost, że mechanizm jest przybity wejściem syntetycznym "
        "w kontroli przyrządu niżej, i tak jest",
    ("tools/tests/test_csharp_pins.py",
     "test_maska_odsiewa_wywolania_z_komentarzy_i_napisow"):
        "przechodzi przez `piny()` na drzewie próbnym, więc zdjęcie maski je wywraca",
    ("tools/tests/test_csharp_pins.py",
     "test_czytnik_liczbowy_tnie_argumenty_po_MASCE_a_nie_po_przecinkach"):
        "wejście syntetyczne poprawione właśnie po zielonej kontroli, i to jest "
        "w docstringu powiedziane",
    ("tools/tests/test_mass_copies.py", "(moduł)"):
        "cały moduł mierzy na drzewie próbnym, a nie na repozytorium — zbiory nazw "
        "są tam mniejsze i o to chodzi",
    ("tools/tests/test_osm_api_fallback.py",
     "test_czytelnik_rejestru_ODMAWIA_gdy_wpisow_OSM_jest_wiecej_niz_jeden"):
        "rejestr z dwoma wpisami zbudowany w katalogu tymczasowym — w drzewie "
        "jest jeden, więc gałęzi nie ćwiczyłoby nic",
    ("tools/tests/test_provenance_classes.py",
     "test_the_geometry_readers_are_parsing_and_not_returning_a_constant"):
        "wejście syntetyczne, wymienione w docstringu dwa razy, plus kontrola przyrządu",
    ("tools/tests/test_tree_writes.py", "test_skan_widzi_ksztalt_ktory_ma_widziec"):
        "czwarty kształt dopisany po zielonej kontroli, razem z wejściem syntetycznym",
    # --- PRZENIESIONE Z DRUGIEGO WORKA PRZY 6.D191, 13.09.2026 --------------------
    # Oba zdania mówiły, że osobna nazwa pliku pośredniego jest ubezpieczeniem od
    # zjawiska, którego „nie udało się odtworzyć w pięciu próbach". Zmierzone i obalone:
    # tamte pięć prób pisało DWA RAZY TĘ SAMĄ mapę, a identycznych bajtów nie ma czego
    # przepleść. Przy mapach różnych zepsucie wychodzi 12 razy na 20.
    ("tools/tests/mutation_sweep.py", "zapisz_pokrycie"):
        "wejście syntetyczne DOROBIONE przy 6.D191, po obaleniu zdania o zjawisku "
        "nieodtworzonym — mechanizm jest naprawą usterki powtarzalnej, nie ubezpieczeniem",
    ("tools/tests/test_mutation_sweep.py",
     "test_plik_posredni_mapy_pokrycia_jest_wlasny_dla_procesu"):
        "to samo od strony testu: zjawisko odtwarza dziś wejście syntetyczne obok, "
        "a ten test odpowiada za drugą połowę argumentu — że dwa PROCESY biorą różne nazwy",
    ("tools/tests/test_mutation_sweep.py",
     "test_wspolna_nazwa_posrednia_psuje_mape_NA_WEJSCIU_SYNTETYCZNYM"):
        "SAMO wejście syntetyczne: dwa uchwyty na jednej ścieżce, przeplot wymuszony "
        "a nie wylosowany, więc zapala się za pierwszym razem i bez zegara",
    ("tools/tests/test_mutation_sweep.py", "(moduł)"):
        "komentarz przy `MAPA_PISARZA_A` o tym, że PIERWSZA wersja tego wejścia wyszła "
        "zielona na mapach równej długości — warunek dziury jest dziś asercją w kodzie",
    ("tools/tests/test_ci_workflows.py",
     "test_kazda_wartosc_retencji_ma_POWOD_albo_ZAPISANA_GRANICE"):
        "DOPISANE 13.09.2026 przy 6.D194: komentarz o tym, że przy 6.D193 ta sama "
        "kontrola wyszła ZIELONA dwa razy — tutaj licznik obrotów pętli stał od "
        "początku i KN-5 zapala się natychmiast, więc lekcja jest przeniesiona, "
        "a nie powtórzona",
    ("tools/tests/test_suite_runtime_budget.py",
     "test_ile_ksztaltow_zapisu_pomiaru_niesie_drzewo"):
        "DOPISANE 13.09.2026 przy 6.D193: zdanie o tym, że KN-5b wyszła ZIELONA, bo "
        "równość pilnowała słownika, a podstawienie oślepiało pętlę — dziś obie drogi "
        "zamyka jawny licznik obrotów, a kontrola przyrządu na pięciu kształtach stoi "
        "w osobnym teście obok",
}

#: Drugi worek. **Powody NIE są jednym powodem i to jest główny wynik 6.D161:**
#: zielona kontrola ma w tym drzewie kilka różnych losów, a pole „Wyjście" tamtej pozycji
#: zakładało dwa (deklaracja albo wejście syntetyczne).
#:
#: **Losów było pięć, a od 6.D191 jest ich CZTERY, i to zdanie jest przepisane, a nie
#: dopisane obok.** Zniknął los „ubezpieczenie przyjęte świadomie" — oba jego zdania
#: (mapa pokrycia, `zapisz_pokrycie` i jego test) przeszły do pierwszego worka, bo
#: zjawisko, od którego rzekomo ubezpieczały, **zostało odtworzone**. Ubyło więc losu,
#: a nie tylko wpisów: dziś w tym worku nie ma ANI JEDNEGO zdania, które mówiłoby
#: „zjawiska nie odtworzono". Pozostałe cztery to: twierdzenie poprawione, mechanizm
#: dołożony bez możliwego wejścia, pokrycie inne niż syntetyczne, mechanizm nieprzyjęty.
BEZ_WEJSCIA_SYNTETYCZNEGO = {
    ("tools/tests/test_csharp_test_methods.py",
     "test_ktora_galaz_jest_BEZCZYNNA_i_gdzie"):
        "DOPISANE 13.09.2026 przy 6.D201. Wejścia syntetycznego mieć NIE MOŻE, bo "
        "twierdzenie jest o DRZEWIE: „żadna z sześciu gałęzi nie ma udziału zerowego”. "
        "Przyrządem są tu stałe `ROZKLAD_POSTACI`, a sprawdza je test OBOK "
        "(`test_rozklad_SZESCIU_postaci_literalu_zgadza_sie_z_drzewem`) — i to jego "
        "ćwiczą KN-1 (literał werbatim dopisany do `src/`) oraz KN-4b (siódma nazwa "
        "w `POSTACIE`). Ten test czyta wyłącznie liczby już zweryfikowane, więc "
        "własnego wejścia nie ma czego zbudować",
    ("tools/tests/test_conflict_markers.py",
     "test_gita_o_liste_plikow_pyta_DOKLADNIE_tyle_modulow_ile_wymieniono"):
        "DOPISANE 13.09.2026 przy 6.D165, i ta bramka je z\u0142apa\u0142a nazajutrz po "
        "powstaniu: warto\u015b\u0107 wartowni chroni\u0105cej przed podw\u00f3jnym wypisem nie da si\u0119 "
        "sprawdzi\u0107 przy wywo\u0142aniu z jednym nazwanym modu\u0142em, bo `_discover` nie "
        "\u0142aduje wtedy `test_all.py` drugi raz — KN-5 tamtej pozycji wysz\u0142a zielona, "
        "wi\u0119c asercji na liczb\u0119 wyst\u0105pie\u0144 NIE MA zamiast udawanej",
    ("tools/tests/mutation_sweep.py", "main"):
        "TWIERDZENIE POPRAWIONE: dawne zdanie o granicy zamka było nieprawdziwe; "
        "mechanizm pilnuje kolejności czytanej z AST, a nie wejścia zbudowanego",
    ("tools/tests/test_mutation_sweep.py",
     "test_zamek_stoi_przed_pierwszym_ZAPISEM_do_dziennika"):
        "ta sama poprawka twierdzenia od strony testu — docstring mówi wprost "
        "„zostało poprawione, a nie przybite”",
    ("tools/tests/test_assertion_gate.py", "komunikat_nic_nie_mowi"):
        "mechanizm DOŁOŻONY po zielonej kontroli, ale wejścia nie ma i mieć nie może: "
        "asercji z pustym komunikatem jest w drzewie ZERO, co sam docstring podaje",
    ("tools/tests/test_assertion_gate.py",
     "test_lista_asercji_bez_komunikatu_moze_tylko_malec"):
        "pokrycie dołożone ASERCJĄ w tym samym miejscu, a nie wejściem syntetycznym",
    ("tools/tests/test_bytecode_staleness.py", "(moduł)"):
        "wzorzec ZAWĘŻONY po zielonej kontroli (kotwica końca wiersza), ale czyta "
        "wyłącznie prawdziwy workflow — napisu próbnego z dawnym przedrostkiem "
        "nie dostaje nigdy",
    ("tools/tests/test_tree_writes.py", "_pisze_przez_parametr"):
        "kształt DOŁOŻONY przez kontrolę; ćwiczy go skan prawdziwego drzewa, "
        "nie wejście zbudowane na tę okazję",
    ("tools/tests/test_tree_walks.py", "(moduł)"):
        "MECHANIZMU NIE PRZYJĘTO: zielona kontrola pokazała, że osobna zapadka na "
        "liczbę nie zapala się nigdy sama, więc jej nie ma — lista nazw jest "
        "ściśle mocniejsza",
}

#: Ile stoi bez wejścia syntetycznego. Przybite osobno od długości słownika, żeby
#: skreślenie wpisu nie przeszło po cichu.
#:
#: **Z dziesięciu na osiem, 13.09.2026 (6.D191).** Dwa zdania o mapie pokrycia wyszły
#: z tego worka nie dlatego, że ktoś je przeredagował, tylko dlatego, że zjawisko, od
#: którego rzekomo ubezpieczały, **zostało odtworzone**: pięć prób z 6.D106 pisało dwa
#: razy tę samą mapę i mierzyło nie tę zmienną. Liczby: `reports/6d191-nie-ta-zmienna.md`.
ZDAN_BEZ_POKRYCIA = 9


def _moduly_do_skanu_rodziny():
    """Ścieżki modułów `.py` pod `tools/tests/`, przez wspólny filtr drzewa.

    Osobna od `_moduly_testowe` wyżej, bo tamta przyjmuje katalog i służy przeglądowi
    mutacyjnemu; zlanie ich w jedną nazwę przesłoniło tamtą i wywróciło cztery testy.
    """
    import tree_walk
    katalog = os.path.join(ROOT, "tools", "tests")
    return sorted(os.path.join(base, nazwa)
                  for base, _kat, pliki in tree_walk.walk(katalog)
                  for nazwa in pliki if nazwa.endswith(".py"))


def zdania_rodziny(sciezki=None):
    """`[(plik, zakres, wiersz)]` — zdania przyznające się do rodziny 6.D161.

    Zakres to nazwa najwęższej obejmującej definicji albo `(moduł)`. Jedno zdanie
    bywa rozbite na dwa wiersze, więc para `(plik, zakres)` liczy się RAZ — inaczej
    liczba mówiłaby o zawijaniu tekstu, a nie o zdaniach.
    """
    out, widziane = [], set()
    for sciezka in (sciezki if sciezki is not None
                    else _moduly_do_skanu_rodziny()):
        with open(sciezka, encoding="utf-8") as uchwyt:
            zrodlo = uchwyt.read()
        if os.path.abspath(sciezka) == os.path.abspath(__file__):
            # WŁASNA SEKCJA JEST WYCIĘTA, i to nie jest wyjątek dla wygody: ona
            # WYMIENIA słowa, które wzorzec rozpoznaje, więc bramka skanująca samą
            # siebie zapalałaby się na własnej dokumentacji i zostałaby wyłączona,
            # nie poprawiona. Ta sama konstrukcja co `granica` w bramce marginesu
            # z `test_suite_runtime_budget.py`. Zmierzone: bez tego wycięcia wzorzec
            # znajduje tu CZTERY zdania o sobie samym (22 zamiast 18).
            zrodlo = zrodlo[:zrodlo.index(ZNACZNIK_WLASNEJ_SEKCJI)]
        try:
            drzewo = ast.parse(zrodlo)
        except SyntaxError:
            continue
        zakresy = [(w.lineno, getattr(w, "end_lineno", w.lineno), w.name)
                   for w in ast.walk(drzewo)
                   if isinstance(w, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        wzgledna = os.path.relpath(sciezka, ROOT)
        for numer, wiersz in enumerate(zrodlo.splitlines(), 1):
            if not RODZINA_UBEZPIECZENIA.search(wiersz):
                continue
            obejmujace = sorted([z for z in zakresy if z[0] <= numer <= z[1]],
                                key=lambda z: z[1] - z[0])
            zakres = obejmujace[0][2] if obejmujace else "(moduł)"
            if (wzgledna, zakres) in widziane:
                continue
            widziane.add((wzgledna, zakres))
            out.append((wzgledna, zakres, numer))
    return out


def test_rodzina_ubezpieczenia_jest_POLICZONA_a_nie_opowiedziana():
    """6.D161: obie liczby wyprowadzone ze źródeł, i KAŻDE zdanie w jednym z worków.

    **Wynik pozycji 6.D161, z dnia pomiaru (13.09.2026, `ca9c595`):** zdań jawnych
    osiemnaście, z wejściem syntetycznym dziewięć, bez niego dziewięć. **Liczby są tu
    podane JAKO POMIAR Z DNIA, a nie jako stan drzewa, i to jest poprawka z 6.D191** —
    do niej stały w czasie teraźniejszym i były nieprawdziwe od 6.D165, czyli od
    następnego dnia. Stan bieżący niosą `ZDAN_RODZINY_RAZEM` i `ZDAN_BEZ_POKRYCIA`,
    i to one są porównywane z drzewem niżej.

    **Co z tamtego pomiaru zostaje prawdą bezterminowo:** worek bez pokrycia rozpada się
    na WIELE różnych losów zielonej kontroli, nie na jeden — pole „Wyjście" 6.D161
    zakładało podział binarny, a drzewo go nie ma. Losów było wtedy pięć; 6.D191 zdjęło
    jeden z nich w całości (patrz komentarz przy `BEZ_WEJSCIA_SYNTETYCZNEGO`).

    **Dlaczego worki są RĘCZNE.** Automat szukający markera wejścia syntetycznego
    w obejmującej definicji dał cztery trafienia fałszywe na dwanaście — liczby
    z takiego automatu nie podaję, bo byłaby tym cichym sitem, którego ta pozycja
    szuka. Zamiast liczby stoi lista, a ten test pilnuje, żeby była PEŁNA.

    **Czego ta bramka NIE łapie, świadomie i z pomiarem:** mechanizmu, który do
    rodziny należy, a w prozie się do niej nie przyznaje. Dwa takie wymienia sama
    pozycja (`SUROWY` i `argumenty_z_nawiasami`) i sprawdziłem oba — żaden nie niesie
    ani jednego ze słów wzorca. Szersze kryterium („nie odróżnia") daje w `tools/tests/`
    grubo ponad setkę trafień, w ogromnej większości o czymś innym, więc bramka na nim
    świeciłaby na poprawnym tekście i zostałaby wyłączona, nie poprawiona.
    """
    zdania = zdania_rodziny()
    assert len(zdania) == ZDAN_RODZINY_RAZEM, (
        "zdań rodziny jest %d, a zapadka stoi na %d — podnieś ją w tym samym "
        "commicie, w którym dopisujesz zdanie" % (len(zdania), ZDAN_RODZINY_RAZEM))

    znalezione = {(plik, zakres) for plik, zakres, _n in zdania}
    sklasyfikowane = set(Z_WEJSCIEM_SYNTETYCZNYM) | set(BEZ_WEJSCIA_SYNTETYCZNEGO)

    # SEDNO: podzial ma byc ZUPELNY i ROZLACZNY. Bez pierwszej polowy zdanie dopisane
    # dzis przechodziloby nieprzeczytane; bez drugiej to samo zdanie moglo by stac
    # w obu workach naraz i obie liczby byłyby prawdziwe osobno, a razem nieprawdziwe.
    niesklasyfikowane = znalezione - sklasyfikowane
    assert not niesklasyfikowane, (
        "zdanie rodziny, którego nikt nie przeczytał i nie przypisał do worka: %s — "
        "rozstrzygnij, czy ma pod sobą wejście syntetyczne, i dopisz do jednej "
        "z dwóch list" % sorted(niesklasyfikowane))

    zbedne = sklasyfikowane - znalezione
    assert not zbedne, (
        "lista wymienia zdanie, którego wzorzec już nie znajduje: %s — zdanie "
        "zniknęło albo zmieniło słowa, a lista została z wczorajszą prawdą"
        % sorted(zbedne))

    obie_naraz = set(Z_WEJSCIEM_SYNTETYCZNYM) & set(BEZ_WEJSCIA_SYNTETYCZNEGO)
    assert not obie_naraz, ("zdanie w obu workach naraz: %s" % sorted(obie_naraz))

    assert len(BEZ_WEJSCIA_SYNTETYCZNEGO) == ZDAN_BEZ_POKRYCIA, (
        "bez pokrycia wymieniono %d zdań przy zapadce %d"
        % (len(BEZ_WEJSCIA_SYNTETYCZNEGO), ZDAN_BEZ_POKRYCIA))
    assert (len(Z_WEJSCIEM_SYNTETYCZNYM) + ZDAN_BEZ_POKRYCIA
            == ZDAN_RODZINY_RAZEM), (
        "worki nie sumują się do całości: %d + %d != %d"
        % (len(Z_WEJSCIEM_SYNTETYCZNYM), ZDAN_BEZ_POKRYCIA, ZDAN_RODZINY_RAZEM))

    # I ze kazdy wpis niesie POWOD, a nie sama nazwe — bez tego lista bylaby
    # wyliczeniem, z ktorego nie widac, czym te przypadki sie roznia.
    for worek in (Z_WEJSCIEM_SYNTETYCZNYM, BEZ_WEJSCIA_SYNTETYCZNEGO):
        for klucz, powod in worek.items():
            assert len(powod) > 40, (klucz, powod)


def test_wzorzec_rodziny_lapie_zdanie_ktore_ma_lapac_i_nie_bierze_sasiedztwa():
    """Kontrola przyrządu na WEJŚCIU SYNTETYCZNYM — bo na drzewie nie widać granicy.

    Bez tej kontroli test wyżej byłby zielony także wtedy, gdyby wzorzec przestał
    cokolwiek znajdować: zapadka porównywałaby zero z zerem po pierwszym podniesieniu.
    """
    probny = os.path.join(_SANDBOX, "rodzina_probna.py")
    with open(probny, "w", encoding="utf-8") as uchwyt:
        uchwyt.write(
            '"""Moduł próbny."""\n'
            'def z_deklaracja():\n'
            '    """To jest UBEZPIECZENIE, nie zmierzona konieczność."""\n'
            '    return 1\n'
            'def bez_deklaracji():\n'
            '    """Zwykły test, który o niczym takim nie mówi."""\n'
            '    return 2\n'
            'def sasiad():\n'
            '    """Kontrola wyszła na czerwono, czyli mechanizm coś zmienia."""\n'
            '    return 3\n')
    znalezione = zdania_rodziny([probny])
    zakresy = [zakres for _p, zakres, _n in znalezione]
    assert zakresy == ["z_deklaracja"], (
        "wzorzec ma wziąć dokładnie jedną z trzech funkcji drzewa próbnego, "
        "a wziął: %s" % zakresy)



# --- 6.D195: bramka na NAPIS w źródle zamiast na ZACHOWANIE ---------------------------
#
# **Skąd.** Przy 6.D165 bramka szukająca napisu w źródle dała się wyłączyć DWA RAZY POD
# RZĄD bez ani jednego czerwonego testu. Czerwoną dało dopiero uruchomienie przebiegu
# w podprocesie i szukanie napisu w jego WYJŚCIU. Pozycja 6.D195 pytała, ile jeszcze
# takich bramek stoi w drzewie.
#
# **Skala jest odwrotna, niż zakładała pozycja.** Asercji kształtu `"literał" in coś`
# jest w `tools/tests/` **849**, ale **560 (66 %) stoi już na ZACHOWANIU** — na wyjściu
# wywołania albo procesu. Na źródle `.py` stoi **31**, czyli 3,7 %. Rodzina `.py` nie
# jest przy tym największa: bramki na `.cs` i `.sh` to 65, na YAML-u CI 69.
#
# **Dlaczego LISTA, a nie liczba — zmierzone, nie przyjęte.** Proste kryterium
# („w obejmującej funkcji pada `.py` albo `getsource`") daje **158** trafień: **136
# fałszywych i 9 przeoczeń**, czyli trafia 22 z 31. Automat na tej liczbie byłby
# dokładnie tym cichym sitem, którego ten projekt unika — więc liczby nie ma, jest lista.
# Ta sama droga, co przy `Z_WEJSCIEM_SYNTETYCZNYM` z 6.D161.

#: Wszystkie asercje kształtu `literał napisowy in/not in coś` pod `tools/tests/`.
#: Zapadka RÓWNOŚCIOWA i MECHANICZNA — liczba wychodzi z `ast`, bez jednego osądu.
#: Jest strażnikiem listy niżej: nowa bramka tego kształtu rusza tę liczbę, więc nie
#: da się dopisać trzydziestej drugiej po cichu.
#:
#: **855 -> 870 (13.09.2026, MB-01), z powodem.** Doszło piętnaście asercji, wszystkie
#: na plikach NIE-`.py`, więc do listy `NA_ZRODLE_PY` nie należy ani jedna. Trzynaście
#: w nowym `test_playable_scripts.py`: czytają `tools/dev/prepare-playable.sh`,
#: `tools/dev/play.sh` i YAML workflowa, czyli rodziny, które ten sam pomiar liczy
#: osobno (65 na `.cs` i `.sh`, 69 na YAML-u CI). Dwie w `test_shot_metadata_gate.py`,
#: w `test_workflow_actually_runs_the_metadata_gate`: `"bash tools/dev/prepare-playable.sh"
#: in text` (YAML) i `"--chunk-manifest" in handle.read()` (`.sh`). Ta druga para jest
#: **przepisana, a nie dopisana obok** — zastąpiła porównanie pozycji dwóch napisów
#: w jednym pliku, bo przepis generacji wyprowadził się z workflowa do skryptu
#: i `--chunk-manifest` w YAML-u już nie stoi.
#:
#: **852 -> 855 (13.09.2026, MB-00), z powodem.** Doszły trzy asercje w bramce pasma M
#: w `test_backlog.py`: `"- **%s:**" % pole not in tresc` (komplet sześciu pól),
#: `"docs/PLAYABILITY.md" in konstytucja` i `"pasmo M" in konstytucja`. Do listy
#: `NA_ZRODLE_PY` NIE należą, bo nie czytają źródła `.py` — czytają **dokumenty**
#: (`docs/TASKS.md` i `CLAUDE.md`), a te są dla tej bramki zachowaniem, nie kodem:
#: reguła zapisana w konstytucji i nieodwzorowana w drzewie jest dokładnie tym, co
#: 6.D109 zmierzyło jako „życzenie zapisane w dokumencie".
#:
#: **850 -> 852 (13.09.2026, 6.D201), z powodem.** Doszły dwie asercje
#: w `test_csharp_test_methods.py`, obie w `test_klasy_literalow_i_maska_ida_TYM_SAMYM_przebiegiem`:
#: `assert "zwykly" not in zamaskowane` i `assert "var a =" in zamaskowane`. Do listy
#: `NA_ZRODLE_PY` NIE należą, bo nie czytają żadnego źródła — `zamaskowane` jest
#: WYNIKIEM WYWOŁANIA `maska()` na wejściu syntetycznym z tego samego testu. Stoją więc
#: na ZACHOWANIU, i to na zachowaniu najostrzej postawionym: jedna pyta, czy literał
#: ZNIKA, druga — czy kod ZOSTAJE. Bez tej pary „maska działa" znaczyłoby „coś zwróciła".
#:
#: **849 -> 850 (13.09.2026, 6.D200), z powodem.** Doszła jedna asercja
#: w `test_csharp_test_methods.py`: `assert "{}" in oczekiwana`. Do listy `NA_ZRODLE_PY`
#: NIE należy, bo nie czyta żadnego źródła — `oczekiwana` jest literałem z tabeli
#: `POSTACIE_LITERALU` w tym samym module. Stoi na ZACHOWANIU własnego testu: pilnuje,
#: żeby oczekiwana maska NIOSŁA KLAMRY, bo maska bez klamr przeszłaby także u czytnika,
#: który połyka resztę pliku — czyli jest to strażnik wyroczni, a nie odczyt tekstu.
#: **872 -> 878, z powodem.** Sześć asercji doszło razem z progiem na czasie CPU
#: w `test_suite_runtime_budget.py`. Wszystkie sześć stoi na NAPISIE i tak ma być: pięć
#: czyta KOMUNIKAT `werdykt` (`"SUFIT INFORMACYJNY" in komunikat`, `"CPU/sciana" in
#: komunikat`, `f"{sciana:.3f}" in komunikat`), a jedna — TEKST KROKU CI
#: (`"SUITE_CPU_BUDGET_S" in step`), tak samo jak sąsiadujące z nią bramki na workflow.
#: Komunikat werdyktu JEST wyjściem tej funkcji, a nie jej opisem — jedzie do logu joba
#: i to z niego `tools/ci/timing_record.py` składa wpisy `POMIARY`, więc asercja na jego
#: treść jest asercją na zachowanie, tylko wyrażoną literałem.
#: **878 -> 880 (14.09.2026, 6.D206), z powodem.** Doszły dwie asercje
#: w `test_suite_runtime_budget.py`, obie w
#: `test_przyrzad_6D206_WIDZI_date_dopisana_do_komentarza`:
#: `"POMIARY_BRAKOW" in nazwy` i `"POMIARY_BRAKOW" not in z_data`. Stoją na NAPISIE
#: z konieczności i to jest ich treść: populacja, którą 6.D206 mierzy, JEST zbiorem
#: nazw stałych, a pytanie „czy `POMIARY_BRAKOW` do niej wchodzi" nie ma innej postaci
#: niż literał z tą nazwą. Do listy `NA_ZRODLE_PY` nie należą — `nazwy` i `z_data` są
#: wynikiem skanu drzewa, a nie odczytem pliku.
#: **880 -> 881 (14.09.2026, 6.D207), z powodem.** Doszła jedna asercja
#: w `test_prose_counts.py`, w `test_sito_jest_SLEPE_na_przypadek_dla_ktorego_powstalo`:
#: `"od 6.D193 jest to SPRAWDZANE" in doc`. Stoi na NAPISIE i tak ma być — pilnuje,
#: że docstring, w którym 6.D193 zamieniło deklarację niesprawdzaną na sprawdzaną,
#: nadal to mówi. Gdyby deklaracja wróciła bez skanu pod spodem, wróciłaby usterka,
#: od której 6.D207 wyszło, a ta bramka jest jedynym miejscem, które to zauważy.
#: Do listy `NA_ZRODLE_PY` nie należy: `doc` jest docstringiem wyjętym przez `ast`,
#: a nie tekstem pliku.
#: **881 -> 883 (15.09.2026, 6.D222), z powodem.** Doszły dwie asercje
#: w `test_ci_workflows.py`: `"with" in str(blad)` w
#: `test_loader_scisly_WIDZI_duplikat_ktorego_safe_load_NIE_widzi` i
#: `"tabulator we wcieciu" not in przeszlo` w
#: `test_ile_ksztaltow_PyYAML_przepuszcza_a_ile_odrzuca`. Obie stoją na NAPISIE
#: Z KONIECZNOŚCI i to jest ich treść: pierwsza pyta, czy KOMUNIKAT loadera nazywa
#: klucz — komunikat bez nazwy nie mówi, gdzie szukać, więc jego treść jest tu
#: zachowaniem, nie opisem; druga pyta o członkostwo w zbiorze nazw próbek, a nazwa
#: próbki nie ma innej postaci niż literał. Do listy `NA_ZRODLE_PY` nie należą:
#: `blad` jest wyjątkiem PyYAML-a, a `przeszlo` wynikiem pętli po próbkach
#: syntetycznych — żadne z nich nie jest odczytem pliku.
ASERCJI_NAPISOWYCH_RAZEM = 883

#: **Kotwica wpisu to `(plik, funkcja, operator, literał)`, a NIE numer wiersza.**
#: Numer przesuwa się przy każdej edycji pliku i lista rozjechałaby się sama z siebie.
#: Zmierzone: sama trójka bez operatora jest niejednoznaczna dla dwóch wpisów
#: (`test_field_paths.py`, ten sam literał pod `in` i pod `not in`), a z operatorem —
#: jednoznaczna dla wszystkich. **Granica, wypisana:** w całych 849 asercjach zostaje
#: 10 kotwic niejednoznacznych (21 asercji); żadna nie jest na tej liście, ale gdyby
#: kiedyś była, trzeba dołożyć licznik wystąpień.
NA_ZRODLE_PY = {
    ('tools/tests/test_assertion_gate.py',
     'test_gate_runner_counts_skipped_tests_outside_the_passed_total',
     'in', '{passed}/{len(tests)-len(skipped)} przeszło'):
        ('KOSZTOWNA',
         "literał to TEKST f-stringa z `test_all.py`, który w wyjściu nigdy nie występuje w tej postaci; wiersz powstaje w `main()`, czyli po przebiegu całego modułu"),
    ('tools/tests/test_assertion_gate.py',
     'test_kompilacja_modulu_testowego_zada_optimize_wprost',
     'in', 'optimize=0'):
        ('KOSZTOWNA',
         "`optimize=0` jest rozróżnialne WYŁĄCZNIE pod `-O`; pod zwykłym interpreterem `optimize=-1` daje ten sam bajtkod, więc trzeba podprocesu"),
    ('tools/tests/test_assertion_gate.py',
     'test_kompilacja_modulu_testowego_zada_optimize_wprost',
     'in', 'dont_inherit=True'):
        ('KOSZTOWNA',
         "to samo dla `dont_inherit=True`: dziedziczenie flag widać dopiero w procesie uruchomionym w innym trybie"),
    ('tools/tests/test_camera_aim.py',
     'test_wypis_okna_nazywa_kamery_i_proporcje',
     'in', '[OKNO] zaweza kamery: '):
        ('KOSZTOWNA',
         "to prawdziwy `print` z `render_check.py`, ale moduł ma `import bpy` w wierszu 16, a wypis stoi w gałęzi kadrowania — potrzeba Blendera"),
    ('tools/tests/test_camera_aim.py',
     'test_wypis_okna_nazywa_kamery_i_proporcje',
     'in', 'CA.KAMERY_POD_OKNEM'):
        ('STRUKTURALNA',
         "pilnuje, że nazwy kamer POCHODZĄ z `CA.KAMERY_POD_OKNEM`, a nie są drugą kopią; lista wpisana na sztywno dałaby identyczny wypis"),
    ('tools/tests/test_camera_aim.py',
     'test_wypis_okna_nazywa_kamery_i_proporcje',
     'in', 'CA.proporcje_okna('):
        ('KOSZTOWNA',
         "obecność wiersza `[OKNO] proporcje okna` jest zachowaniem, ale za `import bpy`"),
    ('tools/tests/test_clearance_profile.py',
     'test_clearance_profile_tolerance_equals_the_resolution_the_module_records',
     'in', 'round(threshold_m, 3)'):
        ('WYKONALNA',
         "`critical_places` jest czystym Pythonem, wołanym w tym samym pliku kilkanaście razy — zaokrąglenie widać w zwróconym `threshold_m`"),
    ('tools/tests/test_clearance_profile.py',
     'test_clearance_profile_tolerance_equals_the_resolution_the_module_records',
     'in', 'f"{t:.3f}"'):
        ('WYKONALNA',
         "format klucza widać w `statistics(...)['below_threshold'].keys()`; test obok już asertuje klucz `0.900`"),
    ('tools/tests/test_conflict_markers.py',
     'test_gita_o_liste_plikow_pyta_DOKLADNIE_tyle_modulow_ile_wymieniono',
     'not in', 'ls-files'):
        ('STRUKTURALNA',
         "z założenia czuła także na komentarz („nawet jeśli tylko w komentarzu”) — mówi o kształcie, nie o wyniku; wersją zachowaniową jest podproces wyżej"),
    ('tools/tests/test_constant_names.py',
     'test_the_package_limits_are_read_from_the_validator_not_copied',
     'in', 'VALIDATOR = V.LIMITS'):
        ('STRUKTURALNA',
         "pilnuje jednego źródła progów; kopia o tych samych liczbach zachowuje się identycznie i o to właśnie chodzi"),
    ('tools/tests/test_crs_convergence.py',
     'test_crs_ecef_threshold_is_the_declared_accuracy_of_the_datum_not_a_tuned_number',
     'in', 'IGN-Bel 1m'):
        ('WYKONALNA',
         "napis stoi w komunikacie `ValueError` i w `__doc__` modułu; `crs.py` to czysty stdlib, wołany w tym pliku bez żadnego środowiska"),
    ('tools/tests/test_dotnet_version.py',
     'test_lista_sdk_ma_tyle_wierszy_ile_jest_sdk',
     'in', 'f"{w} [/atrapa/sdk]\\n"'):
        ('WYKONALNA',
         "pomocnik z TEGO SAMEGO pliku zwraca złożony napis w `{'LISTA': …}` — literał jest wartością do odczytania, nie tekstem"),
    ('tools/tests/test_dotnet_version.py',
     'test_lista_sdk_ma_tyle_wierszy_ile_jest_sdk',
     'not in', 'f"{w} [/atrapa/sdk]\\\\n"'):
        ('WYKONALNA',
         "negatyw tego samego: ukośnik z literą `n` widać w zwróconym `LISTA` bez czytania źródła"),
    ('tools/tests/test_field_paths.py',
     'test_pole_weryfikacji_6d74_wskazuje_modul_z_bramka_o_ktorej_mowi',
     'in', 'def test_no_tool_walks_the_tree_without_the_shared_filter'):
        ('WYKONALNA',
         "nazwa funkcji jest atrybutem modułu, a moduł importuje się bez efektów ubocznych — robi to `_discover` w każdym przebiegu"),
    ('tools/tests/test_field_paths.py',
     'test_pole_weryfikacji_6d74_wskazuje_modul_z_bramka_o_ktorej_mowi',
     'in', 'tools/blender/scan_gates.py'):
        ('WYKONALNA',
         "adres występuje w tamtym module TYLKO w docstringu; to, co moduł naprawdę testuje, widać po `SG.__file__`"),
    ('tools/tests/test_field_paths.py',
     'test_pole_weryfikacji_6d74_wskazuje_modul_z_bramka_o_ktorej_mowi',
     'not in', 'def test_no_tool_walks_the_tree_without_the_shared_filter'):
        ('WYKONALNA',
         "negatyw dla dawnego adresu: po imporcie tamtego modułu brak tej bramki widać "
         "przez `hasattr`, a napis w źródle przepuściłby ją stojącą w komentarzu"),
    ('tools/tests/test_manifest_write_policy.py',
     'test_both_fetchers_go_through_the_shared_helper',
     'in', 'write_manifest_if_changed'):
        ('STRUKTURALNA',
         "docstring mówi wprost „dwie kopie tej samej reguły rozjechałyby się”; wierna reimplementacja dałaby dziś identyczne zachowanie"),
    ('tools/tests/test_manifest_write_policy.py',
     'test_both_fetchers_go_through_the_shared_helper',
     'not in', 'handle.write(P.canonical_json(manifest))'):
        ('WYKONALNA',
         "zakaz zapisu bezwarunkowego jest mierzalny w procesie: dwa przebiegi `--offline` i porównanie `st_mtime_ns` manifestu"),
    ('tools/tests/test_manifest_write_policy.py',
     'test_both_fetchers_say_when_they_did_not_write',
     'in', 'bez zmian'):
        ('WYKONALNA',
         "`bez zmian` to realny wypis `main()` osiągalny w trybie `--offline`, bez sieci i bez podprocesu"),
    ('tools/tests/test_mass_copies.py',
     'test_kazda_z_dwoch_kopii_liczby_naprawde_lezy_tam_gdzie_mowi_opis',
     'in', '"AW0":170000.0'):
        ('STRUKTURALNA',
         "żąda, żeby moduł NIÓSŁ literał, czyli był drugą niezależną drogą wobec rejestru; wartość z importu byłaby ta sama także wtedy, gdyby zaczął czytać rejestr"),
    ('tools/tests/test_mutation_sweep.py',
     'test_przygotowanie_drzewa_zdejmuje_testy_narzedzia_nie_kasujac_pliku',
     'not in', 'def test_cokolwiek('):
        ('NIE_Z_TEJ_RODZINY',
         "czytany plik NIE JEST modułem repozytorium, tylko plikiem w katalogu tymczasowym wytworzonym przez `sweep.neutralise_own_tests` dwa wiersze wyżej — asercja stoi już na wyniku wywołania"),
    ('tools/tests/test_mutation_sweep.py',
     'test_main_wypisuje_licznik_PRZEZ_wspolna_funkcje_a_nie_po_swojemu',
     'in', 'wiersze_starego_bajtkodu'):
        ('STRUKTURALNA_AST',
         "nie szuka napisu: zbiór `wolane` powstaje z `ast.walk(main[0])`; wypis złożony w `main` u siebie dawałby to samo wyjście"),
    ('tools/tests/test_mutation_sweep.py',
     'test_the_write_is_atomic_and_leaves_no_half_file',
     'in', 'os.replace('):
        ('STRUKTURALNA',
         "pilnuje atomowości zapisu; stan połowiczny powstaje tylko przy ubiciu procesu, a skutek końcowy obu kształtów jest identyczny"),
    ('tools/tests/test_readme_claims.py',
     'test_the_absence_measurements_are_not_all_reading_the_same_thing',
     'not in', 'bpy'):
        ('STRUKTURALNA_AST',
         "nie szuka napisu: zbiór `importy` z `ast.parse`; wersja przez `sys.modules` została ZMIERZONA jako fałszywa, bo inne moduły wstawiają atrapy `bpy`"),
    ('tools/tests/test_schedule_envelope.py',
     'test_odwzorowanie_wariantu_na_parametr_ma_jedno_zrodlo_i_odrzuca_obce',
     'in', 'choices=("AW0", "AW2")'):
        ('WYKONALNA',
         "`parse_args` buduje parser czystym `argparse`, bez wejścia i wyjścia — zbiór `choices` da się odczytać z `parser._actions`"),
    ('tools/tests/test_schedule_envelope.py',
     'test_odwzorowanie_wariantu_na_parametr_ma_jedno_zrodlo_i_odrzuca_obce',
     'in', 'choices=sorted(PARAMETR_MASY)'):
        ('WYKONALNA',
         "`parse_args` buduje parser czystym `argparse`, bez wejścia i wyjścia — zbiór `choices` da się odczytać z `parser._actions`"),
    ('tools/tests/test_tree_walks.py',
     'test_klasa_POZA_SKANEM_mowi_o_granicy_przyrzadu_a_nie_o_zapadce',
     'in', 'for field, floor in MIN_PATHS.items()'):
        ('STRUKTURALNA',
         "pilnuje porównania przez zmienną pętli, czyli tego, czego skan z definicji nie widzi; wynik zachowaniowy stoi już wiersz wyżej"),
    ('tools/tests/test_visual_identical_pixels.py',
     'test_capture_blender_wpisuje_sume_pikseli_obok_sumy_pliku',
     'in', 'record["sha256"] = sha256(path)'):
        ('KOSZTOWNA',
         "wpis do manifestu powstaje w `main()` modułu z `import bpy` — tylko po renderze"),
    ('tools/tests/test_visual_identical_pixels.py',
     'test_capture_blender_wpisuje_sume_pikseli_obok_sumy_pliku',
     'in', 'record["idat_sha256"] = idat_sha256(path)'):
        ('KOSZTOWNA',
         "to samo dla drugiej sumy — obie liczby są zachowaniem, ale wyłącznie przez Blendera"),
    ('tools/tests/test_visual_identical_pixels.py',
     'test_narzedzie_sumy_pikseli_jest_wolane_a_nie_przepisane',
     'in', 'png_pixels_sha256'):
        ('STRUKTURALNA',
         "żąda IMPORTU wspólnej funkcji; wierna kopia dawałaby tę samą sumę, a wynik jest już porównany osobno"),
    ('tools/tests/test_visual_identical_pixels.py',
     'test_narzedzie_sumy_pikseli_jest_wolane_a_nie_przepisane',
     'not in', 'def idat_sha256(path):\n    digest'):
        ('STRUKTURALNA',
         "negatyw tego samego: zakaz przepisanej implementacji — czysto kształtowy, bo kopia i wywołanie zwracają tę samą sumę"),
}


#: Rozkład klas, zmierzony 13.09.2026 czytaniem każdej z osobna — asercji, jej otoczenia
#: i modułu, którego źródło jest czytane.
#:
#: **WYKONALNA** — zachowanie da się wywołać tanio: moduł ten napis wypisuje, zwraca go
#: z funkcji, albo wartość da się odczytać importem zamiast czytaniem tekstu.
#: **STRUKTURALNA** — bramka pilnuje KSZTAŁTU kodu, nie zachowania („moduł X woła
#: pomocnika Y", „nie ma importu Z"). Tego przez wywołanie nie widać z definicji: dwa
#: różne kształty dają to samo zachowanie i **o to właśnie chodzi**.
#: **KOSZTOWNA** — zachowanie istnieje, ale wymaga Blendera, podprocesu w innym trybie
#: interpretera albo pełnego przebiegu.
#: **STRUKTURALNA_AST** — osobno, bo to NIE JEST szukanie napisu: prawa strona jest
#: zbiorem zbudowanym z `ast`, a nie tekstem. Trzecia droga, której pozycja nie
#: przewidywała, a drzewo już jej używa.
#: **NIE_Z_TEJ_RODZINY** — wpis, który do listy trafił omyłkowo i zostaje na niej
#: z zapisanym powodem, żeby następny pomiar go nie policzył drugi raz.
KLAS_W_LISCIE = {
    "WYKONALNA": 12,
    "STRUKTURALNA": 9,
    "STRUKTURALNA_AST": 2,
    "KOSZTOWNA": 7,
    "NIE_Z_TEJ_RODZINY": 1,
}

#: **Koszt zamiany „napis → przebieg w podprocesie", zmierzony, bo pozycja żądała liczby
#: z pomiaru, a nie z zasady.** Trzy próby wywołania `test_all.py test_lod_paths.py`
#: w podprocesie: 0,090 / 0,087 / 0,085 s, średnio **0,087 s**.
#:
#: Zapas do progu czasu ściany wynosi 150,0 − 116,404 = **33,596 s**, czyli takich zamian
#: mieści się **386**, a wszystkie 12 wykonalnych kosztowałoby **1,0 s** — 3 % zapasu.
#: Ograniczenie, o którym mówi pozycja, więc ISTNIEJE, ale nie wiąże.
#:
#: **ZASTRZEŻENIE, które sam stawiam przeciwko tej liczbie:** 0,087 s zmierzyłem
#: w KONTENERZE, a próg jest skalibrowany na RUNNERZE. Dokładanie kosztu z jednej maszyny
#: do zapasu z drugiej jest dokładnie tym mieszaniem, przed którym 6.D135 i 6.D149
#: postawiły podłogę mierzalności. Wniosek przeżywa to wyłącznie dlatego, że zapas jest
#: **trzydziestokrotny** wobec kosztu wszystkich dwunastu — przy zapasie ciasnym liczby
#: trzeba by zmierzyć na runnerze.
KOSZT_PODPROCESU_S = 0.087


def czlony_napisowe(wezel):
    """Człony `literał napisowy in/not in coś` w jednej asercji. `[(operator, literał)]`.

    Rozkłada `and`/`or` i `not`, bo asercja z dwoma członami pilnuje dwóch rzeczy i liczy
    się dwa razy — inaczej liczba mówiłaby o składni, a nie o tym, ile jest pilnowane.
    """
    czlony, stos = [], [wezel.test]
    while stos:
        x = stos.pop()
        if isinstance(x, ast.BoolOp):
            stos.extend(x.values)
        elif isinstance(x, ast.UnaryOp) and isinstance(x.op, ast.Not):
            stos.append(x.operand)
        else:
            czlony.append(x)
    out = []
    for x in czlony:
        if (isinstance(x, ast.Compare) and len(x.ops) == 1
                and isinstance(x.ops[0], (ast.In, ast.NotIn))
                and isinstance(x.left, ast.Constant)
                and isinstance(x.left.value, str)
                and not isinstance(x.comparators[0], ast.Constant)):
            out.append(("not in" if isinstance(x.ops[0], ast.NotIn) else "in",
                        x.left.value))
    return out


def asercje_napisowe():
    """`[(plik, funkcja, operator, literał)]` — wszystkie pod `tools/tests/`.

    Przez `tree_walk.walk`, bo to jedyne przejście honorujące `.gitignore`.
    """
    import tree_walk as tw

    katalog = os.path.join(ROOT, "tools", "tests")
    out = []
    for baza, _kat, pliki in tw.walk(katalog):
        for plik in sorted(pliki):
            if not plik.endswith(".py"):
                continue
            sciezka = os.path.join(baza, plik)
            with open(sciezka, encoding="utf-8") as uchwyt:
                try:
                    drzewo = ast.parse(uchwyt.read())
                except SyntaxError:
                    continue
            wzgledna = os.path.relpath(sciezka, ROOT).replace(os.sep, "/")
            for funkcja in (n for n in ast.walk(drzewo)
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
                for wezel in ast.walk(funkcja):
                    if not isinstance(wezel, ast.Assert):
                        continue
                    for operator, literal in czlony_napisowe(wezel):
                        out.append((wzgledna, funkcja.name, operator, literal))
    return out


def test_czytnik_asercji_napisowych_WIDZI_to_co_ma_widziec():
    """Kontrola PRZYRZĄDU: bez niej liczba 849 nie znaczy nic (rodzina 6.D159).

    Czytnik, który nie rozkłada `and`, policzyłby asercję o dwóch członach raz — i nikt
    by tego nie zobaczył, bo wynikiem jest liczba, a nie lista. Wejście jest zbudowane
    na tę okazję i wymienia wprost, co ma być widziane, a co ma milczeć.
    """
    widziane = {
        'assert "a" in x': [("in", "a")],
        'assert "a" not in x': [("not in", "a")],
        'assert "a" in x and "b" not in y': [("in", "a"), ("not in", "b")],
        'assert not ("a" in x)': [("in", "a")],
        'assert "a" in f(z), "powod"': [("in", "a")],
    }
    for zrodlo, spodziewane in sorted(widziane.items()):
        wezel = ast.parse(zrodlo).body[0]
        dostane = czlony_napisowe(wezel)
        assert sorted(dostane) == sorted(spodziewane), (
            "czytnik na %r dał %s zamiast %s — asercja o dwóch członach policzona raz "
            "znika w liczbie bez śladu" % (zrodlo, dostane, spodziewane))

    for milczy in ('assert "a" in "abc"',        # prawa strona też literałem
                   'assert x in y',              # lewa nie jest literałem
                   'assert "a" == x',            # nie `in`
                   'assert 5 in x'):             # literał, ale nie napisowy
        assert czlony_napisowe(ast.parse(milczy).body[0]) == [], (
            "czytnik zapalił się na %r — wtedy 849 opisuje co innego, niż mówi" % milczy)


def test_ile_bramek_stoi_na_NAPISIE_a_nie_na_ZACHOWANIU():
    """ODPOWIEDŹ 6.D195: 849 asercji tego kształtu, 31 na źródle `.py`, 12 wykonalnych.

    **Liczba 849 jest strażnikiem listy, a nie ozdobą.** Lista niżej jest ręczna, bo
    automat na niej myli się w obie strony (136 fałszywych trafień i 9 przeoczeń na 31).
    Gdyby stała sama, trzydziesta druga bramka na źródle weszłaby po cichu — tego pilnuje
    właśnie równość na 849.
    """
    wszystkie = asercje_napisowe()
    assert len(wszystkie) == ASERCJI_NAPISOWYCH_RAZEM, (
        "asercji kształtu `literał in coś` jest %d przy zapadce %d — jeśli doszła, "
        "rozstrzygnij, czy stoi na NAPISIE czy na ZACHOWANIU, i dopisz do listy albo "
        "podnieś liczbę z powodem" % (len(wszystkie), ASERCJI_NAPISOWYCH_RAZEM))

    import collections
    rozklad = collections.Counter(k for k, _p in NA_ZRODLE_PY.values())
    assert dict(rozklad) == KLAS_W_LISCIE, (
        "rozkład klas na liście to %s, a zmierzony 13.09.2026 był %s"
        % (dict(rozklad), KLAS_W_LISCIE))
    assert sum(KLAS_W_LISCIE.values()) == len(NA_ZRODLE_PY), (
        "klasy sumują się do %d przy %d wpisach — któraś liczba opisuje co innego, "
        "niż mówi" % (sum(KLAS_W_LISCIE.values()), len(NA_ZRODLE_PY)))

    # KAŻDY wpis listy ma się w drzewie ZNALEŹĆ, i to jest ta połowa, bez której lista
    # opisywałaby wczorajsze drzewo. Kotwica bez numeru wiersza, bo numer się przesuwa.
    obecne = set(wszystkie)
    sprawdzonych = 0
    for kotwica, (klasa, powod) in sorted(NA_ZRODLE_PY.items()):
        assert kotwica in obecne, (
            "wpis listy 6.D195 wskazuje asercję, której w drzewie już nie ma: %r — "
            "albo bramkę zamieniono na zachowanie (wtedy zdejmij wpis i obniż klasę), "
            "albo przepisano literał" % (kotwica,))
        assert klasa in KLAS_W_LISCIE, (kotwica, klasa)
        assert len(powod) > 60, (
            "powód przy %r ma %d znaków — za mało, żeby powiedzieć, DLACZEGO ta bramka "
            "stoi na napisie" % (kotwica, len(powod)))
        sprawdzonych += 1

    assert sprawdzonych == len(NA_ZRODLE_PY), (
        "pętla listy wykonała %d obrotów przy %d wpisach — pusta pętla przechodzi każdą "
        "asercję w środku (zmierzone przy 6.D193)"
        % (sprawdzonych, len(NA_ZRODLE_PY)))


def test_zamiana_wszystkich_WYKONALNYCH_miesci_sie_w_progu_czasu():
    """ODPOWIEDŹ 6.D195 na pytanie o KOSZT — wykonana, a nie opowiedziana.

    Pozycja żądała, żeby liczba możliwych zamian wyszła **z pomiaru, nie z zasady**.
    Wyszła: 0,087 s na zamianę wobec zapasu do progu, czyli mieści się ich kilkaset przy
    dwunastu kandydatach. **Ta bramka wykonuje tę nierówność**, zamiast ją cytować —
    inaczej `KOSZT_PODPROCESU_S` byłby liczbą, której nikt nie czyta, a zdanie „koszt się
    mieści" zestarzałoby się cicho przy pierwszym podniesieniu progu albo maksimum.

    **Granica tej liczby stoi przy samej stałej i jest ważniejsza od niej:** koszt
    zmierzono w kontenerze, a próg jest skalibrowany na runnerze. Nierówność niżej ma
    więc **dziesięciokrotny margines żądany wprost**, żeby nie rozstrzygała o niczym
    w zakresie, w którym mieszanie maszyn mogłoby zmienić wynik.
    """
    import test_suite_runtime_budget as B

    zapas = B.SUITE_RUNTIME_BUDGET_S - B.MEASURED_MAX_WALL_S
    assert zapas > 0, (
        "zapas do progu jest niedodatni (%.3f s) — wtedy zdanie o koszcie zamian nie ma "
        "o czym mówić, a próg trzeba przeliczyć przed tą pozycją" % zapas)

    wykonalnych = sum(1 for klasa, _p in NA_ZRODLE_PY.values() if klasa == "WYKONALNA")
    assert wykonalnych == KLAS_W_LISCIE["WYKONALNA"], (wykonalnych, KLAS_W_LISCIE)

    koszt_wszystkich = wykonalnych * KOSZT_PODPROCESU_S
    assert koszt_wszystkich * 10 < zapas, (
        "zamiana wszystkich %d wykonalnych kosztowałaby %.3f s przy zapasie %.3f s — "
        "margines zszedł poniżej dziesięciokrotnego, a koszt zmierzono w KONTENERZE przy "
        "progu skalibrowanym na RUNNERZE. W tym zakresie liczby przestają być "
        "porównywalne (6.D135, 6.D149) i trzeba je zmierzyć na runnerze"
        % (wykonalnych, koszt_wszystkich, zapas))


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

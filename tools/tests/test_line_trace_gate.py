# -*- coding: utf-8 -*-
"""Testy bramki wzorcowego śladu (6.D1).

Bramka porównuje ślad przejazdu z wzorcem dwuczęściowym: suma SHA-256 wykrywa
rozjazd, próbka co 100 wierszy go lokalizuje. Te testy sprawdzają obie części
osobno, na sfabrykowanych plikach — **bez uruchamiania rdzenia**.

DLACZEGO BEZ .NET. `tools/tests/` chodzi na maszynie, na której `doctor.sh`
przepuszcza brak SDK jako „pomijam". Bramka, której test wymagałby `dotnet`,
byłaby bramką nietestowaną wszędzie tam, gdzie zestaw narzędzi jest jedynym,
co się uruchamia — a to jest większość przebiegów. Dlatego `check()` przyjmuje
wersję runtime jako parametr.
"""

import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ci"))

import assert_line_trace as G  # noqa: E402

RUNTIME = "10.0.11"


def _slad(rows):
    """Ślad o `rows` wierszach danych, każdy rozpoznawalny po numerze."""
    lines = ["t_s,chainage_m,speed_mps,brake_mps2,throttle,brake,door"]
    for i in range(rows):
        lines.append("%d,%d.5,0,0,1,0,Closed" % (i, i))
    return "\n".join(lines) + "\n"


def _drzewo(tmp, rows, psuj=None):
    """Katalog wzorca + katalog świeżych śladów dla jednej osi `L5_D`."""
    golden = os.path.join(tmp, "golden")
    traces = os.path.join(tmp, "trace")
    os.makedirs(traces)
    with open(os.path.join(traces, "L5_D.csv"), "w", encoding="utf-8") as out:
        out.write(_slad(rows))
    G.update(golden, traces, ["L5_D"], {"limit_kmh": "72", "exchange_s": "20"})
    with open(os.path.join(golden, G.MANIFEST_NAME), encoding="utf-8") as handle:
        manifest = json.load(handle)
    manifest["srodowisko"]["runtime"] = RUNTIME
    with open(os.path.join(golden, G.MANIFEST_NAME), "w", encoding="utf-8") as out:
        json.dump(manifest, out, ensure_ascii=False, indent=2, sort_keys=True)
    if psuj is not None:
        path = os.path.join(traces, "L5_D.csv")
        lines = open(path, encoding="utf-8").read().splitlines()
        lines[psuj] = lines[psuj].replace(",1,0,Closed", ",0,1,Closed")
        with open(path, "w", encoding="utf-8") as out:
            out.write("\n".join(lines) + "\n")
    return golden, traces


def test_probka_bierze_naglowek_i_co_ktory_wiersz_danych():
    lines = _slad(250).splitlines()
    sample = G.sample_lines(lines, step=100)
    # nagłówek + wiersze danych 1, 101, 201 -> numery w pliku 1, 2, 102, 202
    assert [row for row, _ in sample] == [1, 2, 102, 202], sample


def test_numer_wiersza_z_probki_wskazuje_ten_sam_wiersz_co_sed():
    # KONTROLA POZYTYWNA numeracji: gdyby próbka liczyła od zera albo pomijała
    # nagłówek, przedział w komunikacie bramki wskazywałby nie ten wiersz, co
    # edytor — i śledztwo zaczynałoby się od złego miejsca.
    lines = _slad(250).splitlines()
    for row, text in G.sample_lines(lines, step=100):
        assert lines[row - 1] == text, (row, text, lines[row - 1])


def test_probka_pustego_pliku_jest_pusta_a_nie_wywala_sie():
    assert G.sample_lines([], step=100) == []


def test_slad_zgodny_co_do_bajtu_nie_daje_zadnego_problemu():
    with tempfile.TemporaryDirectory() as tmp:
        golden, traces = _drzewo(tmp, 250)
        assert G.check(golden, traces, runtime=RUNTIME) == []


def test_zmiana_jednego_pola_w_probkowanym_wierszu_daje_numer_wiersza():
    with tempfile.TemporaryDirectory() as tmp:
        # wiersz 102 pliku = indeks 101, i JEST w próbce (krok 100)
        golden, traces = _drzewo(tmp, 250, psuj=101)
        problems = G.check(golden, traces, runtime=RUNTIME)
        assert len(problems) == 1, problems
        assert "wierszy 3..102" in problems[0], problems[0]


def test_zmiana_miedzy_wierszami_probki_jest_wykryta_i_nazwana_wprost():
    with tempfile.TemporaryDirectory() as tmp:
        # indeks 50 = wiersz 51 pliku, MIĘDZY próbkami 2 i 102
        golden, traces = _drzewo(tmp, 250, psuj=50)
        problems = G.check(golden, traces, runtime=RUNTIME)
        assert len(problems) == 1, problems
        # suma SHA-256 wykrywa, próbka nie lokalizuje — i bramka to MÓWI,
        # zamiast udawać, że zna numer wiersza
        assert "MIĘDZY" in problems[0], problems[0]
        assert "compare" in problems[0], problems[0]


def test_krotszy_slad_jest_rozjazdem_a_nie_cichym_przejsciem():
    with tempfile.TemporaryDirectory() as tmp:
        golden, traces = _drzewo(tmp, 250)
        path = os.path.join(traces, "L5_D.csv")
        lines = open(path, encoding="utf-8").read().splitlines()[:120]
        with open(path, "w", encoding="utf-8") as out:
            out.write("\n".join(lines) + "\n")
        problems = G.check(golden, traces, runtime=RUNTIME)
        assert len(problems) == 1, problems
        assert "KRÓTSZY" in problems[0], problems[0]


def test_brak_swiezego_sladu_nie_jest_sukcesem():
    # Bramka, która przy braku pliku mówi „zgadza się", jest gorsza niż jej brak.
    with tempfile.TemporaryDirectory() as tmp:
        golden, traces = _drzewo(tmp, 250)
        os.remove(os.path.join(traces, "L5_D.csv"))
        problems = G.check(golden, traces, runtime=RUNTIME)
        assert len(problems) == 1 and "brak świeżego śladu" in problems[0], problems


def test_inna_rodzina_runtime_jest_problemem():
    with tempfile.TemporaryDirectory() as tmp:
        golden, traces = _drzewo(tmp, 250)
        problems = G.check(golden, traces, runtime="8.0.11")
        assert any("rodzina" in p for p in problems), problems


def test_inna_latka_runtime_przy_zgodnym_sladzie_NIE_jest_problemem():
    # Workflow pina `dotnet-version: '10.0.x'`, czyli łatkę puszcza. Bramka
    # żądająca zgodności co do łatki świeciłaby przy pierwszej aktualizacji
    # runtime i mówiłaby „regres rdzenia" o czymś, co regresem nie jest.
    with tempfile.TemporaryDirectory() as tmp:
        golden, traces = _drzewo(tmp, 250)
        assert G.check(golden, traces, runtime="10.0.99") == []


def test_inna_latka_runtime_przy_ROZJECHANYM_sladzie_jest_dopisana_jako_uwaga():
    # Odwrotna strona tej samej decyzji: gdy ślad się rozjedzie, różnica łatki jest
    # pierwszą rzeczą, o której trzeba wiedzieć, zamiast szukać zmiany w rdzeniu.
    with tempfile.TemporaryDirectory() as tmp:
        golden, traces = _drzewo(tmp, 250, psuj=101)
        problems = G.check(golden, traces, runtime="10.0.99")
        assert any("inna łatka" in p for p in problems), problems


def test_rodzina_ucina_latke_a_nie_wersje_glowna():
    assert G.family("10.0.11") == "10.0"
    assert G.family("8.0.11") == "8.0"
    assert G.family("10.1.0") == "10.1"
    assert G.family("?") == "?"


def test_nieodczytana_wersja_runtime_nie_udaje_rozjazdu_rodziny():
    # KONTROLA NEGATYWNA WYKONANA 06.09.2026: pierwsza wersja narzędzia wstawiała
    # w miejsce wersji komunikat błędu, więc brak `dotnet` w PATH zgłaszał się jako
    # „rozjazd RODZINY środowiska" — zdanie formalnie prawdziwe i mylące co do
    # przyczyny. Ten test pilnuje, żeby powód był nazwany po imieniu.
    with tempfile.TemporaryDirectory() as tmp:
        golden, traces = _drzewo(tmp, 250)
        problems = G.check(golden, traces, runtime=G.UNKNOWN_RUNTIME)
        assert len(problems) == 1, problems
        assert "brak narzędzia" in problems[0], problems[0]
        assert "rodzina" not in problems[0], problems[0]


def test_suma_liczy_zawartosc_pliku_a_nie_jego_nazwe():
    with tempfile.TemporaryDirectory() as tmp:
        a = os.path.join(tmp, "a.csv")
        b = os.path.join(tmp, "b.csv")
        for path in (a, b):
            with open(path, "w", encoding="utf-8") as out:
                out.write(_slad(10))
        assert G.sha256_of(a) == G.sha256_of(b)
        assert G.sha256_of(a) == hashlib.sha256(_slad(10).encode()).hexdigest()


def test_manifest_wzorca_w_repozytorium_ma_szesc_osi_i_wersje_runtime():
    here = os.path.dirname(__file__)
    golden = os.path.join(here, "..", "..", "tests", "data", "golden-trace")
    with open(os.path.join(golden, G.MANIFEST_NAME), encoding="utf-8") as handle:
        manifest = json.load(handle)
    assert sorted(manifest["osie"]) == ["L1_A", "L1_B", "L2_E", "L5_C", "L5_D", "L6_F"]
    assert manifest["srodowisko"]["runtime"] != G.UNKNOWN_RUNTIME
    assert manifest["krok_probki"] == G.SAMPLE_STEP
    for axis, opis in manifest["osie"].items():
        probka = os.path.join(golden, axis + ".csv")
        assert os.path.isfile(probka), probka
        assert len(open(probka, encoding="utf-8").read().splitlines()) == \
            opis["wiersze_probki"], axis


def test_wzorzec_w_repozytorium_miesci_sie_w_limicie_z_konstytucji():
    # `CLAUDE.md` §4.8: nic > 10 MB. To jest cała przyczyna, dla której wzorcem
    # jest suma i próbka, a nie pełny plik — więc niech to pilnuje test, a nie
    # pamięć autora.
    here = os.path.dirname(__file__)
    golden = os.path.join(here, "..", "..", "tests", "data", "golden-trace")
    for name in os.listdir(golden):
        rozmiar = os.path.getsize(os.path.join(golden, name))
        assert rozmiar < 10 * 1024 * 1024, (name, rozmiar)

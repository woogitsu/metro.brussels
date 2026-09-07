#!/usr/bin/env python3
"""Bramka kosztu kroku `LineCore.Step` sprawdza to, co obiecuje — i nie da sie oszukac.

**Dlaczego ten modul istnieje osobno od samej bramki.** `tools/ci/assert_linecore_budget.py`
chodzi w CI i potrzebuje `dotnet`, zeby cokolwiek zmierzyc. Zestaw narzedzi chodzi tam,
gdzie `doctor.sh` przepuszcza brak SDK, wiec testy nie moga uruchamiac `budget`. Rozbior
wyjscia, prog i warunki werdyktu da sie jednak sprawdzic bez ani jednego przejazdu —
i to jest cala zawartosc tego pliku.

**Czego pilnuje najmocniej.** Nie liczby mikrosekund, tylko tego, ze pomiar dotyczy
DZIEWIECIU skladow. 6.A12 (#308) zmierzyla, ze `budget --trains 32` melduje `N_max = 1`,
kiedy okno jest krotsze niz jeden odstep — kolumna µs/krok ma wtedy wartosc, tylko
opisuje inny przejazd. Bramka czytajaca sama liczbe mikrosekund przechodzilaby na
zielono z pomiarem jednego skladu.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "ci"))

import assert_linecore_budget as gate  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "sim-tests.yml")

#: Wiersz pomiaru w ksztalcie, jaki daje `Sim.Runner budget` — dziewiec skladow
#: na planie, koszt kroku z zapasem do progu.
ZIELONY = (
    "[BUDŻET] N_zgł;N_max;N_śr;czeka_śr;mediana_kroków_s;min;max;rozstęp_%;µs_krok;CPU/ścienny;%budżetu\n"
    "[BUDŻET] 32;9;5.08;0.98;265081;223360;268544;17.0;3.772;1.01;0.05\n"
)


def _config():
    return gate.load_config()


def _gate_step(workflow):
    """Blok `run:` kroku, ktory wola bramke — bez kroku kontroli negatywnej."""
    at = workflow.index("- name: Core step cost at nine trains is under budget")
    end = workflow.index("- name: Core step gate can actually go red", at)
    return workflow[at:end]


def test_the_threshold_lives_in_one_place_and_the_step_does_not_compare_anything():
    """Prog w YAML-u i prog w pliku to dwie liczby, ktore rozjada sie przy pierwszej
    zmianie. Krok CI ma WOLAC skrypt, a nie porownywac samodzielnie.

    Sprawdzany jest sam krok bramki, nie caly plik: krok kontroli negatywnej NIZEJ
    zawiera zmyslone liczby pomiaru i to jest w porzadku — one wlasnie maja byc
    literalami, bo udaja wyjscie `budget`.
    """
    config = _config()
    with open(WORKFLOW, encoding="utf-8") as handle:
        workflow = handle.read()
    assert "tools/ci/assert_linecore_budget.py" in workflow, (
        "workflow nie wola bramki kosztu kroku")
    krok = _gate_step(workflow)
    assert "tools/ci/assert_linecore_budget.py" in krok, krok
    for liczba in (repr(config["microseconds_per_step_max"]),
                   str(config["scenario"]["steps"]),
                   str(config["scenario"]["headway_s"])):
        assert liczba not in krok, (
            "liczba %s stoi wpisana w kroku CI — ma byc TYLKO w "
            "tools/ci/linecore-step-budget.json" % liczba)
    for porownanie in ("bc ", "awk ", "-gt ", "-lt ", "expr "):
        assert porownanie not in krok, (
            "krok porownuje cos sam (%r) zamiast zdac sie na skrypt" % porownanie)


def test_a_green_measurement_passes():
    ok, problems = gate.verdict(_config(), ZIELONY)
    assert ok, problems


def test_a_slow_step_is_refused():
    wolny = ZIELONY.replace(";3.772;1.01;0.05", ";9.091;1.00;0.11")
    ok, problems = gate.verdict(_config(), wolny)
    assert not ok
    assert any("prog" in p for p in problems), problems


def test_one_train_reported_as_nine_is_refused():
    """Sedno bramki. Pomiar jednego skladu ma TE SAMA kolumne µs/krok i miesci sie
    w progu z ogromnym zapasem — odrzucenie musi wynikac z obsady, nie z czasu."""
    jeden = ZIELONY.replace("32;9;5.08;0.98;", "32;1;1.00;0.00;")
    ok, problems = gate.verdict(_config(), jeden)
    assert not ok
    assert any("skladow" in p or "składów" in p for p in problems), problems
    assert not any("prog" in p and "us" in p for p in problems), (
        "odrzucenie ma wynikac z obsady, a nie z przekroczonego czasu: %s" % problems)


def test_an_empty_output_is_refused_instead_of_passing_quietly():
    ok, problems = gate.verdict(_config(), "nic tu nie ma\n")
    assert not ok
    assert problems


def test_more_than_one_measurement_row_is_refused():
    """Prog dotyczy jednej obsady. Dwa wiersze znacza, ze ktos zmienil scenariusz
    na drabinke N i bramka porownywalaby prog ze srednia z czegos innego."""
    dwa = ZIELONY + "[BUDŻET] 8;8;5.12;0.36;242813;224687;248859;10.0;4.118;0.99;0.05\n"
    ok, problems = gate.verdict(_config(), dwa)
    assert not ok
    assert any("JEDEN" in p for p in problems), problems


def test_the_command_is_built_from_the_config_not_from_memory():
    config = _config()
    argv = gate.command(config)
    for name, key in (("--headway-s", "headway_s"), ("--steps", "steps"),
                      ("--trains", "trains_declared"), ("--turnback-s", "turnback_s")):
        assert name in argv, name
        assert argv[argv.index(name) + 1] == str(config["scenario"][key]), name


def test_the_config_names_its_basis_and_the_expected_occupancy():
    config = _config()
    assert config["trains_on_line_expected"] == 9, (
        "prog opisuje dziewiec skladow — inna liczba wymaga nowego pomiaru, "
        "nie podmiany stalej")
    assert config["basis"].startswith("reports/"), config["basis"]
    assert os.path.isfile(os.path.join(ROOT, config["basis"])), (
        "plik progu odsyla do raportu, ktorego nie ma: " + config["basis"])


def test_the_gate_says_which_run_it_measures():
    """Bramka ma mowic, ktory wariant przejazdu mierzy, a nie milczaco mierzyc jeden.

    **Test przepisany, nie dopisany obok.** Do 6.A18 sprawdzal, ze w zrodle bramki stoi
    tekst "--coast-from-m" i "6.A18" — czyli ze zdanie ZOSTALO NAPISANE. Zdanie napisane
    raz i wpisane na sztywno starzeje sie po cichu; ta wersja sprawdza, ze zdanie zgadza
    sie z tym, co bramka NAPRAWDE uruchamia, bo obie strony czytaja `coast_from_m`.
    """
    config = _config()
    assert "coast_from_m" in config["scenario"], (
        "scenariusz nie wypowiada sie o wybiegu, wiec zdanie o nim nie ma z czego wynikac")
    zdanie = gate.coasting(config)
    if config["scenario"]["coast_from_m"] is None:
        assert "BEZ wybiegu" in zdanie, zdanie
    else:
        assert "Z WYBIEGIEM" in zdanie, zdanie
        assert str(config["scenario"]["coast_from_m"]) in zdanie, zdanie


def test_the_sentence_about_coasting_follows_the_scenario_both_ways():
    """Oba kierunki na kopii scenariusza — bo tego wlasnie nie sprawdzal test na tekst.

    Wpisanie liczby do scenariusza ma zmienic ZDANIE i WYWOLANIE naraz; brak wybiegu ma
    usunac opcje z wywolania. Rozjazd ktoregokolwiek z tych dwoch znaczy, ze bramka mowi
    o innym przejezdzie, niz mierzy.
    """
    config = _config()
    bez = json.loads(json.dumps(config))
    bez["scenario"]["coast_from_m"] = None
    assert "BEZ wybiegu" in gate.coasting(bez)
    assert "--coast-from-m" not in gate.command(bez)

    z_wybiegiem = json.loads(json.dumps(config))
    z_wybiegiem["scenario"]["coast_from_m"] = 250
    zdanie = gate.coasting(z_wybiegiem)
    assert "Z WYBIEGIEM" in zdanie and "250" in zdanie, zdanie
    argv = gate.command(z_wybiegiem)
    assert "--coast-from-m" in argv, argv
    assert argv[argv.index("--coast-from-m") + 1] == "250", argv


def test_the_measured_scenario_still_runs_without_coasting():
    """Prog 8,0 us zmierzono 06.09.2026 na przejezdzie BEZ wybiegu, a wybieg zmienia
    przejazd, nie tylko jego koszt (N_sr 6.69 bez, 6.40 przy 120 m — zmierzone przy
    6.A18). Wlaczenie wybiegu w scenariuszu bez nowego pomiaru porownywaloby wynik
    z progiem wzietym z innego przejazdu, wiec `null` jest tu warunkiem waznosci progu,
    a nie zaniedbaniem."""
    assert _config()["scenario"]["coast_from_m"] is None, (
        "scenariusz wlaczyl wybieg — prog w tym samym pliku musi wtedy pochodzic "
        "z pomiaru Z WYBIEGIEM, razem z nowym raportem")

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

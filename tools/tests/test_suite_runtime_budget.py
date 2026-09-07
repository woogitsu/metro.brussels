#!/usr/bin/env python3
"""6.D11: próg czasu ściany dla `python3 tools/tests/test_all.py` w CI.

**Dlaczego próg NIE siedzi w `test_all.py`.** Kod wyjścia tamtego pliku czyta
`tools/tests/mutation_sweep.py` (`run_suite`, regex `SUMMARY`): mutacja jest uznana
za PRZEŻYTĄ dokładnie wtedy, gdy linia `N/M przeszło` mówi `N == M` **i** kod wyjścia
jest zerowy. Gdyby `main()` w `test_all.py` zwracał 1 również przy przekroczeniu
czasu, zwykłe spowolnienie współdzielonej maszyny — a ta jest współdzielona, patrz
niżej — zamieniłoby się w falę fałszywych „zabić" mutacyjnych, tej samej rodziny co
`reports/wyrocznia-mutacyjna-falszywe-zabicia.md`, tylko odwróconej: nie fałszywe
przeżycie, tylko fałszywa śmierć. Bramka czasu żyje więc w kroku CI (`.github/
workflows/python-tests.yml`), PO zakończeniu procesu — `test_all.py` sam wypisuje
tylko czas, nie ocenia go.

**Skąd próg.** Zmierzone 06.09.2026 na commicie `045730bd639c771d59b6d3b876c4d390d85f16ad`,
cztery przebiegi CAŁEGO procesu `python3 tools/tests/test_all.py` z rzędu, bez ŻADNEJ
zmiany kodu i przy stałych 1709 testach: **66,20 / 68,45 / 68,96 / 77,04 s**
(`time.perf_counter()` od uruchomienia procesu do jego zakończenia, mierzone z
zewnątrz — nie licznik wewnętrzny `test_all.py`, który liczy tylko samą pętlę testów
i wypada o ok. 1-2 s niżej, bo pomija import i odkrywanie modułów). Maszyna jest
KONTENEREM DZIELONYM z innymi sesjami agenta — `ps aux` w trakcie pomiaru pokazywał
równoległy `dotnet build` i proces Godota z sąsiedniego katalogu roboczego — stąd
rozrzut 10,84 s na średniej 70,16 s (15,45 % względem średniej, 16,37 % względem
najniższego pomiaru) przy tym samym kodzie i tej samej liczbie testów. Pełna tabela
per moduł: `reports/test-all-runtime-gate.md`.

**Skąd mnożnik.** `SUITE_RUNTIME_BUDGET_S` to NIE najwyższy zmierzony czas — to
najwyższy zmierzony czas razy margines, bo próg ma przeżyć DWIE rzeczy, których ta
sesja nie zmierzyła: (1) maszyna właściciela (`woogitsu`, `CLAUDE.md` §9) chodzi
gdzie indziej, z nieznaną tej sesji prędkością i własnym wzorcem obciążenia; (2)
zestaw rośnie z każdym zadaniem — w tej sesji o kilkadziesiąt testów dziennie — a
próg dostrojony tuż nad dzisiejszym maksimum wymagałby przeliczania co kilka dni,
czyli przestałby być bramką, a stałby się rytuałem. Margines jest x2 nad najwyższym
zmierzonym przebiegiem, zaokrąglony w DÓŁ do czytelnej liczby (150,0 zamiast
154,08) — bramka i tak porównuje go jako liczbę zmiennoprzecinkową, więc czytelność
nic nie kosztuje.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "python-tests.yml")

#: Najwyższy z czterech przebiegów opisanych w docstringu modułu. Stała osobna od
#: `SUITE_RUNTIME_BUDGET_S`, żeby dało się sprawdzić SAM margines (test niżej), a nie
#: tylko to, że próg jest jakąś liczbą dodatnią.
MEASURED_MAX_WALL_S = 77.04

#: Próg bramki CI. Czytany z TEGO pliku przez krok „Run tool tests" w
#: `python-tests.yml` (`python3 -c "... import test_suite_runtime_budget ..."`) —
#: jedno miejsce prawdy, nie liczba wpisana w YAML z ręki.
SUITE_RUNTIME_BUDGET_S = 150.0


def over_budget(elapsed_s, budget_s=SUITE_RUNTIME_BUDGET_S):
    """Czy zmierzony czas ściany przekracza próg. Równość progu NIE jest przekroczeniem —

    ta sama konwencja, co gdzie indziej w tym repo dla granic włącznie (np.
    `PARALLEL_M jest granicą włącznie` w `test_report_claims.py`).
    """
    return elapsed_s > budget_s


def _workflow_text():
    with open(WORKFLOW, encoding="utf-8") as handle:
        return handle.read()


def test_budget_constant_is_a_sane_positive_number():
    assert isinstance(SUITE_RUNTIME_BUDGET_S, float)
    assert 30.0 < SUITE_RUNTIME_BUDGET_S < 900.0, SUITE_RUNTIME_BUDGET_S


def test_budget_stays_above_the_measured_maximum_with_a_real_margin():
    """Bramka na samą bramkę.

    Bez tego testu ktoś mógłby obniżyć `SUITE_RUNTIME_BUDGET_S` poniżej
    `MEASURED_MAX_WALL_S` bez żadnego ostrzeżenia — a próg niższy niż to, co
    już zostało zmierzone na spokojnej maszynie, zapala się na czerwono od
    samego sąsiedztwa na runnerze, bez żadnego regresu w kodzie.
    """
    assert SUITE_RUNTIME_BUDGET_S > MEASURED_MAX_WALL_S, (
        SUITE_RUNTIME_BUDGET_S, MEASURED_MAX_WALL_S)
    margin = SUITE_RUNTIME_BUDGET_S / MEASURED_MAX_WALL_S
    # Udokumentowany mnożnik to x2 zaokrąglone w dół; test żąda tylko, żeby margines
    # NIE stopniał do czegoś ciasnego przy przyszłej edycji — próg 1.2 zostawia dużo
    # miejsca poniżej rzeczywistych ok. 1.95, a mimo to łapie „obniżono do 78".
    assert margin > 1.2, margin


def test_over_budget_boundary_is_strict_greater_than():
    assert over_budget(SUITE_RUNTIME_BUDGET_S) is False
    assert over_budget(SUITE_RUNTIME_BUDGET_S - 0.001) is False
    assert over_budget(SUITE_RUNTIME_BUDGET_S + 0.001) is True


def test_over_budget_default_argument_tracks_the_shared_constant():
    """Wersja bez podanego `budget_s` musi patrzeć na TĘ SAMĄ stałą, nie na kopię."""
    assert over_budget(SUITE_RUNTIME_BUDGET_S + 1.0) is True
    assert over_budget(SUITE_RUNTIME_BUDGET_S - 1.0) is False


def test_ci_gate_step_reads_this_files_constant_not_a_second_copy():
    """Krok YAML musi czytać `SUITE_RUNTIME_BUDGET_S` STĄD, nie nosić drugiej liczby.

    Dwa źródła progu rozjeżdżają się bezszelestnie przy pierwszej edycji jednego
    z nich — dokładnie klasa usterki, którą `test_report_claims.py` łapie dla
    stałych cytowanych w `reports/`. YAML nie jest raportem, więc tamta bramka
    go nie widzi; ten test jest jej odpowiednikiem dla workflow.
    """
    text = _workflow_text()
    assert "tools/tests/test_suite_runtime_budget.py" in text, text
    assert "SUITE_RUNTIME_BUDGET_S" in text, text
    # Żaden inny fragment kroku nie wpisuje progu jako gołej liczby przypisanej do
    # zmiennej „budget" z ręki — to złapałoby drugą, ukrytą kopię wartości.
    assert not re.search(r"budget\s*=\s*[\"']?\d", text, re.IGNORECASE), text


def test_ci_gate_step_is_a_comparison_that_can_exit_non_zero():
    """Krok o tej nazwie musi umieć wywalić joba, nie tylko wypisać liczby.

    Ta sama klasa kontroli, co `test_ci_reference_parity_step_is_a_gate_not_a_print`
    w `test_ci_workflows.py` (zarezerwowanym dla innej pozycji) — napisana tu, żeby
    nie dotykać cudzego pliku.
    """
    text = _workflow_text()
    step_start = text.index("Run tool tests")
    step = text[step_start:text.index("\n      - name:", step_start)]
    assert "SUITE_RUNTIME_BUDGET_S" in step, step
    assert re.search(r"exit\s+1\b", step), step
    assert "set -euo pipefail" in step, (
        "bez tego krok kontynuowałby po awarii test_all.py aż do własnego "
        "porownania czasu i mógłby zameldować sukces mimo nieudanych testów")

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

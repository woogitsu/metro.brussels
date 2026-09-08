#!/usr/bin/env python3
"""Test, który wychodzi z procesu, jest FAIL-em testu — nie werdyktem o zestawie.

**SKĄD TA BRAMKA — 6.D54, zmierzone 08.09.2026.** Pętla po testach w `test_all.py`
łapała `except Exception`, a `SystemExit` dziedziczy z `BaseException`, nie
z `Exception`. Wychodził więc z pętli ORAZ z `main()`, a Python kończył proces kodem
z wyjątku — przy `sys.exit(0)` **zerowym**. Sonda z trzema testami, w której drugi
woła `sys.exit(0)`, dawała jeden wiersz `ok`, **ani jednego** wiersza `N/M przeszło`
ani `RAZEM`, i **kod 0**. Sonda nazwana `test_aaa_…` (czyli pierwsza w sortowaniu
modułów) urywała przebieg po **jednym** wykonanym teście z 2041 odkrytych; nazwana
`test_zzz_…` — po 2039. Kod 0 był niezmienny w obu wypadkach, liczba utraconych
testów nie.

To nie była usterka kosmetyczna: kod wyjścia tego zestawu jest **wyrocznią zieloności
całego projektu** (`CLAUDE.md` §5), a `mutation_sweep.py` czyta z przebiegu wyłącznie
wiersz `N/M przeszło` i kod wyjścia, uznając mutację za PRZEŻYTĄ dokładnie wtedy, gdy
oba mówią „ok". Brak wiersza podsumowania przy kodzie 0 dawał więc obu czytającym
odpowiedź „zielono" o przebiegu, który się nie odbył.

**Kłamstwo było jednostronne w WERDYKCIE, ale nie w SKUTKU**, i to rozróżnienie jest
powodem, dla którego ta bramka ma sześć testów, a nie jeden: `sys.exit(1)` dawał kod 1,
czyli czerwono — ale zestaw równie dobrze się nie wykonał, bez podsumowania. Naprawa
samego kodu wyjścia załatwiłaby połowę, więc obok przechwytu `SystemExit` stoi
w `main()` osobny FAIL zestawu na „wykonano mniej, niż odkryto", i on też jest tu
sprawdzony — w obie strony, bo zapadka, która zapala się zawsze, nie jest zapadką.

**DLACZEGO PODPROCES, A NIE `main()` W TYM SAMYM PROCESIE — to jest pomiar, nie
ostrożność.** Pierwsza wersja tej bramki użyła idiomu bramki 6.D15
z `test_assertion_gate.py`: podmiana `AG.paths()` na piaskownicę i `main()` wołane
wprost. Puszczona na kodzie SPRZED poprawki dała **zero wierszy wyjścia i kod 2** —
bo `SystemExit` sondy uciekał z `main()`, uciekał z funkcji testowej i kończył proces
samej bramki. Zmierzone osobną sondą, czym ten kod 2 był:

    $ python3 hipoteza.py          # in-process, sonda woła sys.exit(0)
    kod procesu bramki: 0
    # i ani jednego wiersza wypisu — `print` po `main()` nie wykonał się wcale

Kod 2 brał się **wyłącznie z kolejności alfabetycznej**: pierwszy w kolejce był test
z `sys.exit(2)`. Gdyby pierwszy był ten z `sys.exit(0)`, bramka in-process byłaby
**ZIELONA nad usterką, którą ma łapać** — czyli dokładnie tą samą usterką o poziom
wyżej. Podproces tego nie może powtórzyć: wyjście z procesu sondy nie ma jak dosięgnąć
procesu bramki, a czytany jest ten sam kod wyjścia, którego żąda `CLAUDE.md` §5.

**Dlaczego bramka, a nie tylko poprawka.** Zmiana jest jednym słowem w jednej linii
(`except Exception` -> osobne `except SystemExit`). Słowo wraca przy pierwszym
refaktorze pętli, a wraca **cicho**: przebieg z takim błędem wygląda jak przebieg
krótszy, nie jak przebieg zepsuty.
"""
import atexit
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEST_ALL = os.path.join(ROOT, "tools", "tests", "test_all.py")
_SANDBOX = tempfile.mkdtemp(prefix="runner-process-exit-probe-")
atexit.register(shutil.rmtree, _SANDBOX, True)
_UNIQUE = [0]

#: Wiersz podsumowania, który czyta `mutation_sweep.py` (`SUMMARY` w tamtym pliku).
#: Wzorzec jest tu przepisany, a nie zaimportowany, świadomie: gdyby tamten się
#: zmienił, ta bramka ma paść i pokazać rozjazd, a nie podążyć za zmianą po cichu.
PRZESZLO = re.compile(r"^\s*(\d+)/(\d+) przeszło\s*$", re.MULTILINE)

TRZY_TESTY = """\
import sys


def test_aaa_pierwszy():
    assert 1 == 1


def test_bbb_{co}():
    assert True
    {akcja}


def test_ccc_trzeci():
    assert 2 == 2
"""


def _przebieg(akcja, co):
    """Uruchom `test_all.py` na jednej sondzie W PODPROCESIE. Zwraca `(kod, wypis)`.

    `test_all.py <ścieżka>` zawęża odkrywanie do jednego modułu (`only`, 6.D25),
    a `_only_path` przyjmuje ścieżkę spoza `tools/tests/`, więc piaskownica wchodzi
    bez dotykania prawdziwego katalogu testów. Podproces jest tu warunkiem
    poprawności bramki, nie wygodą — powód stoi w docstringu modułu.
    """
    _UNIQUE[0] += 1
    sciezka = os.path.join(_SANDBOX, f"test_sonda_{co}_{_UNIQUE[0]}.py")
    with open(sciezka, "w", encoding="utf-8") as uchwyt:
        uchwyt.write(TRZY_TESTY.format(co=co, akcja=akcja))
    gotowe = subprocess.run([sys.executable, TEST_ALL, sciezka],
                            capture_output=True, text=True, cwd=ROOT, timeout=120)
    return gotowe.returncode, gotowe.stdout + gotowe.stderr


def test_wyjscie_z_procesu_przez_sys_exit_ZERO_daje_kod_niezerowy():
    """Rdzeń 6.D54: `sys.exit(0)` w teście nie może dać zielonego zestawu.

    Przed poprawką ten przebieg dawał **kod 0** i nie wypisywał ani wiersza
    `N/M przeszło`, ani `RAZEM`. Asercje niżej pilnują wszystkich trzech rzeczy
    naraz, bo każda z nich osobno dałaby się spełnić bez naprawienia usterki:
    kod niezerowy bez podsumowania nadal ukrywałby, ile testów się wykonało,
    a podsumowanie bez FAIL-a nie nazywałoby winnego.
    """
    kod, wypis = _przebieg("sys.exit(0)", "wychodzi_zero")
    assert kod != 0, f"sys.exit(0) w teście dał kod {kod} — wyrocznia mówi zielono\n{wypis}"
    assert PRZESZLO.search(wypis), f"brak wiersza `N/M przeszło`:\n{wypis}"
    assert "RAZEM" in wypis, f"brak wiersza `RAZEM`:\n{wypis}"
    assert re.search(r"^\s*FAIL test_bbb_wychodzi_zero", wypis, re.MULTILINE), (
        f"FAIL nie wskazuje testu, który zawołał sys.exit:\n{wypis}")


def test_komunikat_FAIL_podaje_KOD_z_ktorym_test_chcial_wyjsc():
    """Sam fakt wyjścia nie wystarczy — kod mówi, czego szukać.

    `sys.exit(0)` to zwykle `--help` albo pomyłkowe `main()` narzędzia, a `sys.exit(2)`
    to `argparse` odrzucający argument. Bez tej liczby w komunikacie czytający widzi
    „test wyszedł z procesu" i nie wie, która z tych dwóch dróg go tam zaprowadziła.
    """
    _, wypis = _przebieg("sys.exit(2)", "wychodzi_dwa")
    assert "sys.exit(2)" in wypis, f"komunikat nie podaje kodu wyjścia:\n{wypis}"


def test_sys_exit_JEDEN_i_sys_exit_ZERO_daja_TEN_SAM_werdykt():
    """Jednostronność kłamstwa musi zniknąć, a nie zmienić stronę.

    Przed poprawką `sys.exit(1)` dawał kod 1 (czerwono), a `sys.exit(0)` kod 0
    (zielono) — mimo że w obu wypadkach zestaw się nie wykonał. Gdyby poprawka
    zrównała je „w drugą stronę", oba dawałyby zielono i ta bramka by tego nie
    zobaczyła, patrząc tylko na równość. Dlatego sprawdzana jest równość **i**
    niezerowość obu.
    """
    kod_zero, wypis_zero = _przebieg("sys.exit(0)", "rowne_zero")
    kod_jeden, wypis_jeden = _przebieg("sys.exit(1)", "rowne_jeden")
    assert kod_zero == kod_jeden, (
        f"sys.exit(0) dało {kod_zero}, a sys.exit(1) dało {kod_jeden} — werdykt zależy "
        f"od kodu, z którym test chciał wyjść\n{wypis_zero}\n{wypis_jeden}")
    assert kod_zero != 0, f"oba kody są zerowe — kłamstwo zmieniło stronę\n{wypis_zero}"


def test_test_STOJACY_PO_wyjsciu_z_procesu_nadal_sie_wykonuje():
    """Wyjście z procesu jest usterką JEDNEGO testu, nie końcem przebiegu.

    To jest asercja, która odróżnia poprawkę wykonaną od poprawki pozornej: kod
    niezerowy dałoby się uzyskać, przerywając przebieg na winnym teście — i wtedy
    reszta zestawu wciąż by się nie wykonała, tylko czerwono zamiast zielono. Sonda ma
    trzeci test PO winnym i on musi mieć werdykt.
    """
    kod, wypis = _przebieg("sys.exit(0)", "nie_przerywa")
    assert re.search(r"^\s*ok\s+test_ccc_trzeci", wypis, re.MULTILINE), (
        f"test po wyjściu z procesu nie wykonał się — pętla stanęła\n{wypis}")
    przeszlo = PRZESZLO.search(wypis)
    assert przeszlo.group(2) == "3", (
        f"mianownik podsumowania to {przeszlo.group(2)}, a odkryto 3 testy\n{wypis}")
    assert kod != 0, kod


def test_zapadka_na_niewykonane_testy_MILCZY_gdy_wszystkie_doszly_do_werdyktu():
    """Zapadka, która zapala się zawsze, nie jest zapadką — druga strona pary.

    `FAIL <zestaw>` ma się pokazywać wtedy i tylko wtedy, gdy któryś odkryty test
    nie doszedł do werdyktu. Przebieg z `sys.exit(0)` w środku ma wszystkie trzy
    testy rozliczone (winny jako FAIL, dwa pozostałe jako ok), więc ten wiersz
    stać tam NIE może — inaczej niósłby zero informacji.
    """
    _, wypis = _przebieg("sys.exit(0)", "cisza_zapadki")
    assert "<zestaw>" not in wypis, (
        f"FAIL <zestaw> zapalił się, choć wszystkie odkryte testy doszły do werdyktu:"
        f"\n{wypis}")
    assert "<przebieg>" not in wypis, (
        f"FAIL <przebieg> zapalił się bez przerwania przebiegu:\n{wypis}")


def test_przebieg_PRZERWANY_wypisuje_podsumowanie_i_liczbe_bez_werdyktu():
    """`KeyboardInterrupt` dalej przerywa, ale nie wynosi sterowania z `main()`.

    Gdyby wynosił, nie wypisałoby się podsumowanie i kod procesu wziąłby się
    z wyjątku — czyli dokładnie ta usterka, tylko innym wyjątkiem. Pętla staje,
    podsumowanie leci, kod jest niezerowy, a osobny FAIL nazywa, ile testów nie
    doszło do werdyktu.

    Komunikat mówi **„nie doszło do werdyktu"**, a nie „nie wykonało się wcale":
    test, który rzucił `KeyboardInterrupt`, zaczął się i zginął w połowie, więc
    zdanie o niewykonaniu byłoby o nim nieprawdziwe.
    """
    kod, wypis = _przebieg("raise KeyboardInterrupt()", "przerywa")
    assert kod != 0, f"przerwany przebieg dał kod {kod}\n{wypis}"
    assert PRZESZLO.search(wypis), f"przerwany przebieg nie wypisał podsumowania:\n{wypis}"
    assert "RAZEM" in wypis, f"przerwany przebieg nie wypisał `RAZEM`:\n{wypis}"
    assert "FAIL <przebieg>: przerwany przez KeyboardInterrupt" in wypis, (
        f"nie widać, co przerwało przebieg:\n{wypis}")
    assert re.search(r"FAIL <zestaw>: wykonano 1 z 3 odkrytych testów", wypis), (
        f"FAIL zestawu nie podaje, ile testów doszło do werdyktu:\n{wypis}")


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

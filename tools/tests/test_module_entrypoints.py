#!/usr/bin/env python3
"""Modul testowy uruchomiony WPROST naprawde uruchamia swoje testy.

**Skad ta bramka.** 6.D25, ze znaleziska przy 6.A18 — na mojej wlasnej kontroli
negatywnej. Opcja zostala zdjeta z tabeli, bramka uruchomiona przez
`python3 tools/tests/test_runner_options.py`, wynik: `kod: 0`. Odczytalem to jako
„bramka sie nie zapala". Nieprawda: modul nie mial straznika `__main__`, wiec
uruchomiony wprost wykonal same definicje, ZERO testow, i skonczyl sie zerem —
nieodroznialnie od przebiegu, w ktorym wszystko przeszlo.

**Czego ta bramka pilnuje NAPRAWDE.** Nie obecnosci straznika. Tego, ze droga
pojedynczego modulu jest TA SAMA droga, co calego zestawu: `test_all.main(__file__)`,
czyli z licznikiem asercji i z odmowa przy zerze testow (`AG.suite_verdict`). Wlasna
petla po `globals()` w kazdym module byla by 91 kopiami przebiegacza — a jedna z nich
juz istniala, w `test_reference_snapshot.py`, i miala dokladnie te usterke, przed
ktora ta pozycja broni: zero funkcji `test_` dawalo wypis „co do bitu" i kod 0.

**Straznik czytany przez `ast`, nie grepem — i to nie jest ostroznosc na zapas.**
Zmierzone 06.09.2026: `grep -l '__main__' tools/tests/test_*.py` dawal **5** trafien,
a wykonywalnych straznikow bylo **2**. Trzy pozostale to slowo `__main__` w prozie
docstringow i w danych testowych `test_mutation_sweep.py`. Pomiar grepem wszedl do
raportu 6.A18 jako „84 z 89 modulow" i byl zanizony; prawdziwa liczba to 89 z 91.
Bramka na obecnosc tekstu bylaby tu wiec tym samym rodzajem przyrzadu, ktorego ta
pozycja dotyczy.
"""
import ast
import glob
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTY = os.path.join(ROOT, "tools", "tests")
#: Wywolanie, ktore ma stac w strazniku KAZDEGO modulu procz `test_all.py`. Jeden
#: przebiegacz, nie 91 kopii — kopia rozjezdza sie po cichu i to jest zmierzone,
#: nie przewidywane (`test_reference_snapshot.py` przed 6.D25).
DELEGACJA = "test_all.main(__file__)"


def moduly():
    return sorted(glob.glob(os.path.join(TESTY, "test_*.py")))


def ma_straznik(zrodlo):
    """Czy modul ma WYKONYWALNY `if __name__ == "__main__"` na poziomie modulu.

    Przez `ast`, wiec slowo `__main__` w docstringu, w komentarzu i w napisie
    z danymi testowymi nie liczy sie jako straznik.
    """
    for wezel in ast.parse(zrodlo).body:
        if not isinstance(wezel, ast.If):
            continue
        warunek = wezel.test
        if (isinstance(warunek, ast.Compare)
                and isinstance(warunek.left, ast.Name)
                and warunek.left.id == "__name__"
                and any(isinstance(k, ast.Constant) and k.value == "__main__"
                        for k in warunek.comparators)):
            return True
    return False


def _zrodlo(path):
    with open(path, encoding="utf-8") as uchwyt:
        return uchwyt.read()


def _uruchom(argumenty, cwd=ROOT):
    return subprocess.run([sys.executable] + argumenty, cwd=cwd,
                          capture_output=True, text=True, timeout=300)


def _napisz(sciezka, cialo):
    """Modul-piaskownica z tym samym straznikiem, co prawdziwe moduly zestawu.

    `sys.path` dopisany wprost, bo plik lezy w podkatalogu `tools/tests/`, a nie
    obok `test_all.py`.
    """
    with open(sciezka, "w", encoding="utf-8") as uchwyt:
        uchwyt.write(
            '"""Modul piaskownicy bramki 6.D25."""\n'
            + cialo
            + '\n\nif __name__ == "__main__":\n'
              '    import os, sys\n'
              '    sys.path.insert(0, os.path.join(\n'
              '        os.path.dirname(os.path.abspath(__file__)), ".."))\n'
              '    import test_all\n'
              '    raise SystemExit(test_all.main(__file__))\n')


def _liczba_testow(wypis):
    """Liczba z wiersza `RAZEM ... , N testów, ...`; `None`, gdy wiersza nie ma."""
    for linia in wypis.splitlines():
        if linia.strip().startswith("RAZEM "):
            for czlon in linia.split(","):
                czlon = czlon.strip()
                if czlon.endswith("testów"):
                    return int(czlon.split()[0])
    return None


def test_every_test_module_can_be_run_directly():
    bez = [os.path.relpath(p, ROOT) for p in moduly() if not ma_straznik(_zrodlo(p))]
    assert not bez, (
        "modul testowy bez straznika `__main__` — uruchomiony wprost skonczy sie "
        "kodem 0, nie wykonawszy ani jednego testu: " + ", ".join(bez))


def test_every_module_delegates_to_the_one_runner():
    """Straznik ma WOLAC wspolny przebiegacz, a nie miec wlasna petle.

    `test_all.py` jest jedynym wyjatkiem: on tym przebiegaczem JEST.
    """
    wlasne = []
    for path in moduly():
        if os.path.basename(path) == "test_all.py":
            continue
        if DELEGACJA not in _zrodlo(path):
            wlasne.append(os.path.relpath(path, ROOT))
    assert not wlasne, (
        "straznik nie deleguje do wspolnego przebiegacza (" + DELEGACJA + "): "
        + ", ".join(wlasne) + " — wlasna petla po globals() nie liczy asercji "
        "i nie odmawia przy zerze testow")


def test_a_word_in_a_docstring_is_not_mistaken_for_a_guard():
    """Kontrola przyrzadu, a nie kodu — powod bramki jest w docstringu modulu.

    Grep dawal 5 trafien tam, gdzie straznikow bylo 2. Ten test pilnuje, ze
    `ma_straznik` czyta strukture: modul, ktory ma `__main__` WYLACZNIE w prozie
    i w napisie, nie jest uznany za uruchamialny.
    """
    udawany = (
        '"""Docstring, ktory mowi o if __name__ == "__main__" i nic wiecej."""\n'
        'WZORZEC = \'if __name__ == "__main__":\'\n'
        '# komentarz o __main__\n'
        'def test_x():\n    assert True\n'
    )
    assert not ma_straznik(udawany), "proza uznana za straznik"
    prawdziwy = udawany + '\nif __name__ == "__main__":\n    pass\n'
    assert ma_straznik(prawdziwy), "prawdziwy straznik nierozpoznany"


def test_running_one_module_reports_how_many_tests_it_ran():
    """Kod 0 sam w sobie niczego nie dowodzi — o to poszlo w 6.A18.

    Przebieg musi POWIEDZIEC, ile testow wykonal, inaczej „przeszlo" i „nie bylo
    czego uruchomic" wygladaja tak samo.
    """
    with tempfile.TemporaryDirectory(dir=TESTY, prefix="test_dwa_") as katalog:
        # Modul piaskownicy, a NIE ten plik: uruchomienie samego siebie w podprocesie
        # jest rekursja bez dna — zmierzone, 300 s do timeoutu przy pierwszej wersji
        # tego testu.
        dwa = os.path.join(katalog, "test_dwa_testy.py")
        _napisz(dwa, "def test_a():\n    assert True\n\n\n"
                     "def test_b():\n    assert 1 + 1 == 2\n")
        wynik = _uruchom([os.path.relpath(dwa, ROOT)])
    assert wynik.returncode == 0, wynik.stdout + wynik.stderr
    ile = _liczba_testow(wynik.stdout)
    assert ile is not None, "przebieg pojedynczego modulu nie podal liczby testow"
    assert ile == 2, wynik.stdout


def test_dwa_moduly_URUCHAMIAJA_SIE_OBA_a_nie_pierwszy_z_nich():
    """6.D114: drugi i dalszy argument byl odrzucany BEZ SLOWA.

    Do 11.09.2026 galaz `__main__` konczyla sie na `main(sys.argv[1])`, wiec
    `test_all.py a.py b.py` dawalo wynik `a.py` i **kod zero** — wynik, ktory
    WYGLADA jak wynik tego, o co sie prosilo. Tak sie o tym dowiedzialem przy
    6.D101: wywolalem zestaw z czterema modulami i wzialem wynik jednego za wynik
    czterech.

    Pomiar jest tu po LICZBIE TESTOW, a nie po kodzie wyjscia, i to jest treść:
    oba wywolania koncza sie zerem, bo oba moduly przechodza. Rozroznia je dopiero
    mianownik — 2 wobec 5. Kod wyjscia nie odroznil by cichego pominiecia od
    poprawnego przebiegu i dlatego nie jest tu wyrocznia.
    """
    with tempfile.TemporaryDirectory(dir=TESTY, prefix="test_wiele_") as katalog:
        pierwszy = os.path.join(katalog, "test_pierwszy_modul.py")
        drugi = os.path.join(katalog, "test_drugi_modul.py")
        _napisz(pierwszy, "def test_a():\n    assert True\n\n\n"
                          "def test_b():\n    assert 1 + 1 == 2\n")
        _napisz(drugi, "def test_c():\n    assert True\n\n\n"
                       "def test_d():\n    assert True\n\n\n"
                       "def test_e():\n    assert True\n")

        sam = _uruchom(["tools/tests/test_all.py", os.path.relpath(pierwszy, ROOT)])
        oba = _uruchom(["tools/tests/test_all.py", os.path.relpath(pierwszy, ROOT),
                        os.path.relpath(drugi, ROOT)])

    assert sam.returncode == 0, sam.stdout + sam.stderr
    assert oba.returncode == 0, oba.stdout + oba.stderr
    assert _liczba_testow(sam.stdout) == 2, sam.stdout
    assert _liczba_testow(oba.stdout) == 5, (
        "wywolanie z dwoma modulami wykonalo %r testow zamiast 5 — drugi argument "
        "zostal pominiety po cichu:\n%s" % (_liczba_testow(oba.stdout), oba.stdout))
    assert "test_drugi_modul" in oba.stdout, (
        "w wypisie nie ma sladu drugiego modulu:\n" + oba.stdout)


def test_ten_sam_modul_dwa_razy_jest_ODMOWA_a_nie_podwojnym_przebiegiem():
    """Powtorzenie zawyzyloby mianownik `N/M przeszlo`, ktory czyta wyrocznia.

    `mutation_sweep.run_suite` czyta z przebiegu WYLACZNIE ten wiersz i kod wyjscia.
    Policzenie tego samego modulu dwa razy jest wiec bledem tego samego rodzaju co
    ciche pominiecie argumentu, tylko w druga strone — i tak samo nie zostawia sladu.
    """
    with tempfile.TemporaryDirectory(dir=TESTY, prefix="test_powtorka_") as katalog:
        modul = os.path.join(katalog, "test_powtorzony.py")
        _napisz(modul, "def test_a():\n    assert True\n")
        wzgledna = os.path.relpath(modul, ROOT)
        wynik = _uruchom(["tools/tests/test_all.py", wzgledna, wzgledna])

    assert wynik.returncode != 0, (
        "ten sam modul dwa razy skonczyl sie kodem 0:\n" + wynik.stdout + wynik.stderr)
    assert "modul podany dwa razy" in (wynik.stdout + wynik.stderr), (
        wynik.stdout + wynik.stderr)


def test_nieznany_modul_na_DRUGIM_miejscu_tez_jest_odmowa():
    """Odmowa nie moze zalezec od POZYCJI argumentu.

    Bez tego testu wystarczyloby sprawdzac wylacznie `argv[1]` — i literowka
    w drugiej nazwie znow byla by cichym pominieciem, tyle ze po poprawce.

    **Pierwszym argumentem jest modul PIASKOWNICY, a nie ten plik, i to nie jest
    ozdoba.** Pierwsza wersja podawala tu `test_module_entrypoints.py`: przy dzialajacym
    kodzie odmowa przychodzi przed uruchomieniem czegokolwiek, wiec bylo szybko — ale
    kontrola negatywna KN-1 (galaz `__main__` bierze znow jeden argument) zamieniala to
    w uruchomienie TEGO pliku w podprocesie, ktory uruchamia kolejne podprocesy. Ta sama
    rekursja, przed ktora ostrzega komentarz w tescie o liczbie testow, tylko widoczna
    dopiero pod mutacja.
    """
    with tempfile.TemporaryDirectory(dir=TESTY, prefix="test_drugi_zly_") as katalog:
        pierwszy = os.path.join(katalog, "test_poprawny_modul.py")
        _napisz(pierwszy, "def test_a():\n    assert True\n")
        wynik = _uruchom(["tools/tests/test_all.py", os.path.relpath(pierwszy, ROOT),
                          "test_nie_ma_takiego_modulu"])
    assert wynik.returncode != 0, wynik.stdout + wynik.stderr
    assert "nie ma takiego modulu testowego" in (wynik.stdout + wynik.stderr), (
        wynik.stdout + wynik.stderr)


def test_a_module_with_no_tests_is_refused_not_passed():
    """Sedno pozycji, sprawdzone WYKONANIEM, nie odczytaniem kodu.

    Modul bez ani jednego testu, uruchomiony wprost, ma sie skonczyc kodem roznym
    od zera. Przed 6.D25 konczyl sie zerem — i to bylo nieodroznialne od sukcesu.
    """
    with tempfile.TemporaryDirectory(dir=TESTY, prefix="test_pusty_") as katalog:
        pusty = os.path.join(katalog, "test_bez_zadnego_testu.py")
        _napisz(pusty, "def pomocnik():\n    return 1\n")
        wynik = _uruchom([os.path.relpath(pusty, ROOT)])
    assert wynik.returncode != 0, (
        "modul bez testow skonczyl sie kodem 0: " + wynik.stdout + wynik.stderr)
    assert "nie odkryto ani jednego testu" in wynik.stdout, wynik.stdout


def test_an_unknown_module_name_is_refused(): 
    """Literowka w nazwie modulu ma byc odmowa, nie pustym przebiegiem — inaczej
    `test_all.py test_runer_options` konczyloby sie zerem, nie uruchomiwszy nic."""
    wynik = _uruchom(["tools/tests/test_all.py", "test_nie_ma_takiego_modulu"])
    assert wynik.returncode != 0, wynik.stdout + wynik.stderr
    assert "nie ma takiego modulu testowego" in (wynik.stdout + wynik.stderr), (
        wynik.stdout + wynik.stderr)


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

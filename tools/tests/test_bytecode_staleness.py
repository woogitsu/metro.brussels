#!/usr/bin/env python3
"""Kontrola negatywna na module Pythona a bajtkod, ktory zostal po poprzednim przebiegu.

**Po co ten modul istnieje.** 6.D86 (10.09.2026) zglosilo dwa razy `F0_N: 251389.0`
— wartosc z POPRZEDNIEJ mutacji — mimo ze `md5sum -c` na zrodle dawal `OK`. Zrodlo
bylo przywrocone naprawde; wykonal sie stary `.pyc`. CPython uznaje bajtkod za wazny
po parze `(mtime zrodla w SEKUNDACH, rozmiar w bajtach)`, a mutacja podmieniajaca
napis o tej samej dlugosci i przywrocona w tej samej sekundzie nie rusza ani jednego
z tych dwoch pol.

**Dlaczego to nie jest incydent jednej pozycji.** Przyrzad potwierdzajacy przywrocenie
oglada plik `.py`, a import idzie z `.pyc`. Kontrola sumy MD5 nie widzi wiec tego, co
sie naprawde wykonalo — i to jest ta sama rodzina usterki, ktora projekt tropi od 6.D27:
przyrzad meldujacy sprawdzenie, ktorego nie zrobil.

**Pulapka dziala w OBIE strony, i druga jest grozniejsza.** Zmierzone 10.09.2026:

  (a) mutacja WIDOCZNA, przywrocenie NIE   -> kontrola zglasza wynik z mutacji, ktorej
      juz nie ma. Tak wygladalo 6.D86: czerwone, ale nie z tego powodu, co trzeba.
  (b) mutacja NIEWIDOCZNA                  -> kontrola wychodzi ZIELONA i czyta sie
      jako „bramka tego nie lapie". Falszywy wniosek w druga strone, i bez zadnego
      sladu, ze cos poszlo nie tak.

**Dlaczego bramka odtwarza pulapke, a nie sprawdza napisu w dokumencie.** Napis
w dokumencie mowi, ze pulapka istnieje; ta bramka to MIERZY. Gdyby CPython kiedys
przeszedl na bajtkod z suma zrodla (PEP 552, tryb `CHECKED_HASH`) domyslnie, pierwszy
test zapali sie na zielonej maszynie — i to bedzie sygnal, ze zdanie w `CLAUDE.md` §5
i w `docs/06-worked-example.md` przestalo byc prawda, a nie ze bramka jest zepsuta.

**Czego ta bramka NIE robi.** Nie czysci `__pycache__` w przebiegu zestawu i nie
kaze tego robic `test_all.py`. Zmierzone 10.09.2026 na trzech parach przebiegow:
zimny 126.27 / 125.65 / 127.47 s, cieply 127.17 / 127.49 / 125.25 s — czyli cache
bajtkodu nie daje tu ZADNEGO mierzalnego zysku, bo moduly testowe i tak kompiluja
sie ze zrodla przez `assertion_gate.load_instrumented`. Mimo to czyszczenie w kazdym
przebiegu byloby wylaczeniem cache'a na stale takze w CI, a to pole „Poza zakresem"
pozycji 6.D102 wyklucza wprost. W CI pulapki zreszta nie ma: `actions/checkout` robi
`git clean -ffdx`, a `__pycache__` jest w `.gitignore`, wiec kazdy przebieg CI zaczyna
zimno. Jest to zagrozenie LOKALNE, dla agenta i dla wlasciciela.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Para napisow tej samej dlugosci — dokladnie ta, na ktorej pulapka wyszla w 6.D86.
ORYGINAL = '248900.0'
MUTACJA = '251389.0'

#: Polecenie, ktore ma stac w OBU dokumentach opisujacych petle weryfikacji.
#: Nie chodzi o jego brzmienie co do znaku, tylko o to, ze procedura tam jest —
#: dlatego dopasowanie idzie po dwoch czlonach, a nie po calym wierszu.
PROCEDURA_CZLONY = ("__pycache__", "-exec rm -rf")

#: Dokumenty, w ktorych procedura ma stac. Raport nie wystarcza: pole „Skonczone,
#: gdy" pozycji 6.D102 zada, zeby procedura stala w DOKUMENCIE.
DOKUMENTY = ("CLAUDE.md", os.path.join("docs", "06-worked-example.md"))


def _laboratorium(katalog):
    """Modul `mod.py` i skrypt `use.py`, ktory go importuje i wypisuje stala."""
    with open(os.path.join(katalog, "mod.py"), "w", encoding="utf-8") as handle:
        handle.write('F0_N = "%s"\n' % ORYGINAL)
    with open(os.path.join(katalog, "use.py"), "w", encoding="utf-8") as handle:
        handle.write("import mod\nprint(mod.F0_N)\n")


def _zapisz(katalog, wartosc):
    with open(os.path.join(katalog, "mod.py"), "w", encoding="utf-8") as handle:
        handle.write('F0_N = "%s"\n' % wartosc)


def _bieg(katalog, bez_bajtkodu=False):
    """Wynik importu — czyli to, co NAPRAWDE sie wykonalo."""
    env = dict(os.environ)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    if bez_bajtkodu:
        env["PYTHONDONTWRITEBYTECODE"] = "1"
    wynik = subprocess.run([sys.executable, "use.py"], cwd=katalog,
                           capture_output=True, text=True, env=env)
    assert wynik.returncode == 0, (
        "laboratorium nie wystartowalo: %s" % (wynik.stderr.strip() or "brak stderr"))
    return wynik.stdout.strip()


def _czysc(katalog):
    shutil.rmtree(os.path.join(katalog, "__pycache__"), ignore_errors=True)


def _sekwencja(bez_bajtkodu_wszedzie=False, bez_bajtkodu_na_kontroli=False,
               czysc_przed_mutacja=False):
    """Baza, potem mutacja W TEJ SAMEJ SEKUNDZIE. Zwraca `(baza, mutacja)`.

    Bez `sleep`: caly sens pulapki polega na tym, ze obie operacje mieszcza sie
    w jednej sekundzie zegara, a na tej maszynie mieszcza sie w kilkunastu
    milisekundach. Test, ktory by tu czekal, mierzylby cos innego.

    **Dwa rozne `bez_bajtkodu` i to jest cala tresc rozstrzygniecia.**
    `bez_bajtkodu_wszedzie` ustawia zmienna od poczatku, wiec `.pyc` nie powstaje
    NIGDY i pulapki nie ma — ale to nie opisuje zycia, w ktorym zestaw chodzil
    juz wczesniej normalnie. `bez_bajtkodu_na_kontroli` ustawia ja dopiero na
    przebieg po mutacji, czyli tak, jak zrobilby ktos, kto o zmiennej uslyszal
    i uznal ja za procedure. Pierwsza wersja tej bramki mierzyla tylko pierwszy
    wariant i przez to zaprzeczala pomiarowi z 6.D102 — zmierzone 10.09.2026.
    """
    with tempfile.TemporaryDirectory() as katalog:
        _laboratorium(katalog)
        baza = _bieg(katalog, bez_bajtkodu_wszedzie)
        if czysc_przed_mutacja:
            _czysc(katalog)
        _zapisz(katalog, MUTACJA)
        return baza, _bieg(katalog, bez_bajtkodu_wszedzie or bez_bajtkodu_na_kontroli)


def test_stary_bajtkod_potrafi_ukryc_mutacje():
    """Bez procedury mutacja jest NIEWIDOCZNA — kontrola wyszlaby zielona."""
    baza, mutacja = _sekwencja()
    assert baza == ORYGINAL, (
        "przebieg bazowy nie pokazal wartosci wyjsciowej: %r" % baza)
    assert mutacja == ORYGINAL, (
        "mutacja o tej samej dlugosci, wpisana w tej samej sekundzie, zostala "
        "ZAUWAZONA (%r) — pulapka z 6.D86 przestala istniec na tej maszynie, "
        "wiec zdanie o niej w CLAUDE.md §5 i w docs/06-worked-example.md trzeba "
        "przeliczyc, a nie wylaczyc ten test" % mutacja)


def test_czyszczenie_pycache_pokazuje_prawdziwy_wynik():
    """Ta sama sekwencja z czyszczeniem `__pycache__` daje wynik prawdziwy."""
    baza, mutacja = _sekwencja(czysc_przed_mutacja=True)
    assert baza == ORYGINAL, baza
    assert mutacja == MUTACJA, (
        "po wyczyszczeniu bajtkodu mutacja nadal jest niewidoczna (%r) — "
        "procedura z dokumentow nie dziala" % mutacja)


def test_sam_PYTHONDONTWRITEBYTECODE_nie_wystarcza():
    """Zmienna zabrania PISAC bajtkod, nie CZYTAC — a pulapke robi czytanie.

    To jest rozstrzygniecie, ktorego zada pole „Wyjscie" pozycji 6.D102: czy
    wystarczy zmienna, czy trzeba czyscic katalog. Zmierzone: **nie wystarcza**,
    bo `.pyc` z wczesniejszego, zwyklego przebiegu juz lezy i jest wazny wedlug
    pary `(mtime, rozmiar)` — a zmienna nie zabrania go przeczytac.
    """
    baza, mutacja = _sekwencja(bez_bajtkodu_na_kontroli=True)
    assert baza == ORYGINAL, baza
    assert mutacja == ORYGINAL, (
        "PYTHONDONTWRITEBYTECODE=1 na samej kontroli wystarczylo (%r) — pomiar "
        "z 6.D102 mowi, ze nie wystarcza, wiec albo maszyna sie zmienila, albo "
        "zmienil sie CPython" % mutacja)


def test_ta_sama_zmienna_USTAWIONA_OD_POCZATKU_dziala_i_dlatego_mysli_sie_ze_wystarcza():
    """Druga polowa tego samego rozstrzygniecia — i powod, dla ktorego mysli sie inaczej.

    Ze zmienna ustawiona od pierwszego przebiegu `.pyc` nie powstaje nigdy i mutacja
    jest widoczna. Stad bierze sie przekonanie, ze zmienna „zalatwia sprawe": pomiar
    zrobiony w czystym katalogu je potwierdza. Nie zalatwia — wystarczy JEDEN wczesniejszy
    zwykly przebieg (albo zestaw uruchomiony godzine temu), zeby pulapka wrocila.
    Dlatego procedura w dokumentach kaze CZYSCIC KATALOG, a nie ustawiac zmienna.
    """
    baza, mutacja = _sekwencja(bez_bajtkodu_wszedzie=True)
    assert baza == ORYGINAL, baza
    assert mutacja == MUTACJA, (
        "zmienna ustawiona od poczatku nie pokazala mutacji (%r) — wtedy cale "
        "rozroznienie z testu wyzej opisuje cos innego, niz mowi" % mutacja)


def test_procedura_stoi_w_dokumentach_a_nie_tylko_w_raporcie():
    """Oba dokumenty petli weryfikacji niosa polecenie czyszczace.

    Raport opisuje pomiar z jednego dnia; procedura ma stac tam, gdzie sie po nia
    siega przed zadaniem. Dopasowanie po dwoch czlonach, a nie po calym wierszu —
    inaczej bramka pilnowalaby formatowania, a nie tresci.
    """
    for wzgledna in DOKUMENTY:
        with open(os.path.join(ROOT, wzgledna), encoding="utf-8") as handle:
            tresc = handle.read()
        for czlon in PROCEDURA_CZLONY:
            assert czlon in tresc, (
                "%s nie niesie procedury kontroli negatywnej na module Pythona — "
                "brakuje czlonu %r" % (wzgledna, czlon))


def test_dokumenty_mowia_ktora_zmienna_NIE_wystarcza():
    """W dokumencie stoi takze to, co NIE dziala — bo to jest polowa procedury.

    Sama komenda czyszczaca bez tego zdania zaprasza do zamiany jej na zmienna
    srodowiskowa, ktora wyglada taniej i nie dziala. Ta para (co robic, czego nie
    robic) jest tresci a, nie ozdoba.
    """
    for wzgledna in DOKUMENTY:
        with open(os.path.join(ROOT, wzgledna), encoding="utf-8") as handle:
            tresc = handle.read()
        assert re.search(r"PYTHONDONTWRITEBYTECODE", tresc), (
            "%s nie mowi, ze PYTHONDONTWRITEBYTECODE nie wystarcza" % wzgledna)


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

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

**Co sie zmienilo 11.09.2026 (6.D122) — ten akapit jest PRZEPISANY, nie dopisany
obok.** Do tego dnia stalo tu, ze ta bramka „nie czysci `__pycache__` w przebiegu
zestawu i nie kaze tego robic `test_all.py`", z powodem: pole „Poza zakresem" pozycji
6.D102 wykluczalo wylaczanie cache'a w CI. To juz nieprawda — `test_all.py` czysci
`__pycache__` pod `tools/` sam, PRZED wlasnymi importami narzedzi, i mowi o tym
wierszem `[BAJTKOD]`.

Powod zmiany jest ten sam pomiar, ktory wtedy uzasadnial wstrzymanie sie: zimny
126.27 / 125.65 / 127.47 s wobec cieplego 127.17 / 127.49 / 125.25 s, czyli cache
bajtkodu nie daje ZADNEGO mierzalnego zysku, bo moduly testowe kompiluja sie ze
zrodla przez `assertion_gate.load_instrumented`. Skoro zysk jest zerem, zakaz
z „Poza zakresem" chronil wtedy przed kosztem, ktorego nie ma. W CI pulapki i tak
nie bylo (`actions/checkout` robi `git clean -ffdx`), wiec czyszczenie jest tam
operacja na pustym katalogu.

Czego to NIE znosi: procedura reczna zostaje w `CLAUDE.md` §5 i w
`docs/06-worked-example.md` jako DRUGA LINIA, bo pulapka dotyczy takze przebiegow,
ktore nie ida przez `test_all.py` — wlasnego `python3 -c`, importu w konsoli,
skryptu w `tools/`. Pilnuje tego `test_procedura_stoi_w_dokumentach_a_nie_tylko_w_raporcie`.

**Zagrozenie jest LOKALNE, dla agenta i dla wlasciciela** — to zdanie zostaje bez
zmian i jest powodem, dla ktorego obrona ma byc w narzedziu, a nie w pamieci.
"""

import ast
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize

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


def _zapisz(katalog, wartosc, mtime=None):
    """Zapisuje `mod.py`; `mtime` USTAWIA czas modyfikacji zamiast brać zegar.

    **Po co ustawiać czas, skoro pulapka bierze sie z zegara.** Bo pulapka bierze
    sie z PARY `(mtime w sekundach, rozmiar)`, a „ten sam czas" wychodzi z zegara
    tylko wtedy, gdy oba zapisy trafia w te sama sekunde — i to jest los, nie
    warunek. Zmierzone 11.09.2026 na 200 przebiegach tej sekwencji bez obciazenia:
    **5 razy** zapis mutacji wypadl w innej sekundzie niz zapis bazy, i za kazdym
    z tych 5 razy mutacja byla WIDOCZNA, czyli test padal. Przy obciazeniu jest
    gorzej: przeglad mutacyjny przerywal na kalibracji, bo w drzewie roboczym
    `test_stary_bajtkod_potrafi_ukryc_mutacje` padalo przy czterech zestawach naraz.

    Ustawienie czasu nie zamienia wiec pomiaru na zalozenie — odtwarza DOKLADNIE
    ten warunek, ktorego pulapka wymaga, zamiast czekac, az wypadnie sam. To, co
    test mierzy, zostaje to samo: czy CPython przy tej parze siegnie po stary
    bajtkod.
    """
    sciezka = os.path.join(katalog, "mod.py")
    with open(sciezka, "w", encoding="utf-8") as handle:
        handle.write('F0_N = "%s"\n' % wartosc)
    if mtime is not None:
        os.utime(sciezka, (mtime, mtime))


def _mtime(katalog):
    return os.stat(os.path.join(katalog, "mod.py")).st_mtime


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
        zegar = _mtime(katalog)
        baza = _bieg(katalog, bez_bajtkodu_wszedzie)
        if czysc_przed_mutacja:
            _czysc(katalog)
        # Czas zapisu mutacji USTAWIONY na czas zapisu bazy — patrz `_zapisz`.
        # Bez tego warunek pulapki zachodzil losowo (zmierzone: 195 razy na 200).
        _zapisz(katalog, MUTACJA, mtime=zegar)
        return baza, _bieg(katalog, bez_bajtkodu_wszedzie or bez_bajtkodu_na_kontroli)


def test_sekwencja_USTAWIA_czas_zamiast_liczyc_na_zegar():
    """Warunek pulapki ma zachodzic ZAWSZE, a nie wtedy, gdy zegar sprzyja.

    **Bez tego testu poprawka jest niewidoczna dla zestawu.** Cofniecie `_zapisz`
    do brania czasu z zegara nie zapala niczego w zwyklym przebiegu — bo w 195
    przebiegach na 200 zegar sprzyja. Zmierzone 11.09.2026: wersja zegarowa dala
    **5 porazek na 200**, wersja z `os.utime` — **0 na 200**. Test pyta wiec o to,
    co odroznia obie wersje: czy zapis mutacji dostal czas USTAWIONY.

    To ta sama rodzina co 6.D27: przebieg zielony nie odroznia procedury, ktora
    dziala, od procedury, ktorej zadzialanie jest losowe.
    """
    zapisy = []
    zastane = globals()["_zapisz"]

    def podglad(katalog, wartosc, mtime=None):
        zapisy.append(mtime)
        return zastane(katalog, wartosc, mtime)

    globals()["_zapisz"] = podglad
    try:
        baza, mutacja = _sekwencja()
    finally:
        globals()["_zapisz"] = zastane

    assert baza == ORYGINAL and mutacja == ORYGINAL, (baza, mutacja)
    assert zapisy and zapisy[-1] is not None, (
        "zapis mutacji wzial czas z zegara zamiast go ustawic — warunek pulapki "
        "zachodzi wtedy losowo: %r" % (zapisy,))


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


# --- 6.D122: obrona po stronie NARZEDZIA, nie po stronie pamieci ----------------

def _laboratorium_pod_tools(katalog):
    """Ten sam lab, ale `mod.py` lezy pod `tools/` — tam, gdzie zestaw czysci.

    Polozenie jest tu TRESCIA, a nie dekoracja: `_wyczysc_bajtkod` chodzi wylacznie
    po `tools/`, wiec lab w korzeniu katalogu tymczasowego mierzylby, ze funkcja
    NIC nie robi, i wygladalby identycznie jak lab, w ktorym pulapki nie ma.
    """
    gdzie = os.path.join(katalog, "tools", "track")
    os.makedirs(gdzie)
    with open(os.path.join(gdzie, "mod.py"), "w", encoding="utf-8") as handle:
        handle.write('F0_N = "%s"\n' % ORYGINAL)
    with open(os.path.join(katalog, "use.py"), "w", encoding="utf-8") as handle:
        handle.write("import sys, os\n"
                     "sys.path.insert(0, os.path.join(os.path.dirname(__file__), "
                     "'tools', 'track'))\n"
                     "import mod\nprint(mod.F0_N)\n")


def _sciezka_mod(katalog):
    return os.path.join(katalog, "tools", "track", "mod.py")


def _sekwencja_w_drzewie(czysc_zestawem=False):
    """Baza, potem mutacja w tej samej sekundzie — z czyszczeniem ZESTAWU albo bez.

    Czysci **ta sama funkcja**, ktora wola `test_all.py` przy starcie, a nie jej
    kopia ani `shutil.rmtree` napisane tutaj. Kopia przechodzilaby dalej, gdyby
    tamta przestala dzialac, i bramka meldowalaby sprawdzenie, ktorego nie zrobila.
    """
    import tree_walk as TW

    with tempfile.TemporaryDirectory() as katalog:
        _laboratorium_pod_tools(katalog)
        zegar = os.stat(_sciezka_mod(katalog)).st_mtime
        baza = _bieg(katalog)
        usuniete = TW.wyczysc_bajtkod(katalog) if czysc_zestawem else (0, 0)
        with open(_sciezka_mod(katalog), "w", encoding="utf-8") as handle:
            handle.write('F0_N = "%s"\n' % MUTACJA)
        os.utime(_sciezka_mod(katalog), (zegar, zegar))
        return baza, _bieg(katalog), usuniete


def test_ta_sama_sekwencja_BEZ_czyszczenia_zestawu_ukrywa_mutacje():
    """Kontrola przyrzadu dla testu nizej: w tym labie pulapka NAPRAWDE zachodzi.

    Bez tego testu zielony wynik testu nizej nie odrozniałby „zestaw wyczyscil
    bajtkod" od „w tym labie bajtkodu nigdy nie bylo". Ta sama rodzina co 6.D27.
    """
    baza, mutacja, usuniete = _sekwencja_w_drzewie(czysc_zestawem=False)
    assert baza == ORYGINAL, baza
    assert usuniete == (0, 0), usuniete
    assert mutacja == ORYGINAL, (
        "mutacja w labie pod `tools/` zostala zauwazona BEZ czyszczenia (%r) — "
        "pulapka w tym labie nie zachodzi, wiec test nizej nie mierzy tego, "
        "co mowi" % mutacja)


def test_zestaw_czysci_bajtkod_sam():
    """Ta sama sekwencja, ale czysci funkcja zestawu — mutacja jest WIDOCZNA.

    To jest pole „Skonczone, gdy" pozycji 6.D122 zmierzone wprost: mutacja o tej
    samej dlugosci, wpisana w tej samej sekundzie, widoczna BEZ recznej procedury.
    """
    baza, mutacja, usuniete = _sekwencja_w_drzewie(czysc_zestawem=True)
    assert baza == ORYGINAL, baza
    assert usuniete[0] >= 1 and usuniete[1] >= 1, (
        "funkcja zestawu nie znalazla ani jednego `__pycache__` pod `tools/` "
        "(%r) — czysci nie tam, gdzie pulapka mieszka" % (usuniete,))
    assert mutacja == MUTACJA, (
        "po czyszczeniu funkcja zestawu mutacja nadal jest niewidoczna (%r) — "
        "`tree_walk.wyczysc_bajtkod` nie broni przed pulapka z 6.D102" % mutacja)


def test_czyszczenie_zestawu_nie_rusza_niczego_poza_tools():
    """Pole „Poza zakresem" 6.D122 zmierzone: kasowane jest `tools/` i nic wiecej."""
    import tree_walk as TW

    with tempfile.TemporaryDirectory() as katalog:
        w_tools = os.path.join(katalog, "tools", "track", "__pycache__")
        poza = os.path.join(katalog, "build", "__pycache__")
        zwykly = os.path.join(katalog, "tools", "track", "zwykly")
        for gdzie in (w_tools, poza, zwykly):
            os.makedirs(gdzie)
            with open(os.path.join(gdzie, "mod.cpython-0.pyc"), "wb") as handle:
                handle.write(b"x")

        katalogi, pliki = TW.wyczysc_bajtkod(katalog)

        assert not os.path.exists(w_tools), "`__pycache__` pod `tools/` przetrwal"
        assert os.path.isdir(poza), "skasowano `__pycache__` SPOZA `tools/`"
        assert os.path.isdir(zwykly), "skasowano katalog, ktory nie jest `__pycache__`"
        assert (katalogi, pliki) == (1, 1), (katalogi, pliki)


def test_czyszczenie_stoi_PRZED_importami_narzedzi():
    """Kolejnosc w zrodle `test_all.py`: czyszczenie, dopiero potem `import profiles`.

    **To jest cala roznica miedzy obrona a wypisem o obronie.** Wywolanie przeniesione
    do `main()` zostawia zestaw zielony i wiersz `[BAJTKOD]` na swoim miejscu, a mimo
    to nie chroni niczego: `import profiles, validate, reference …` wykonuje sie przy
    IMPORCIE `test_all`, czyli wczesniej, wiec stary bajtkod narzedzi jest juz
    wczytany. Zaden inny test tego nie zobaczy, bo wynik przebiegu jest identyczny.

    Liczone z AST, nie z kolejnosci napisow: komentarz albo tekst w dokumentacji
    modulu wygladalby przy wyszukiwaniu napisu tak samo jak wywolanie.
    """
    import ast

    zrodlo = os.path.join(ROOT, "tools", "tests", "test_all.py")
    with open(zrodlo, encoding="utf-8") as handle:
        drzewo = ast.parse(handle.read())

    wywolania = [w.lineno for w in ast.walk(drzewo)
                 if isinstance(w, ast.Call)
                 and getattr(w.func, "attr", getattr(w.func, "id", None))
                 == "wyczysc_bajtkod"]
    assert wywolania, "`test_all.py` nie wola `wyczysc_bajtkod` ani razu"

    narzedzia = {"profiles", "validate", "reference", "make_test_track",
                 "provenance", "assertion_gate"}
    importy = [w.lineno for w in drzewo.body if isinstance(w, ast.Import)
               and any(a.name.split(".")[0] in narzedzia for a in w.names)]
    assert importy, (
        "nie znalazlem importow narzedzi na najwyzszym poziomie `test_all.py` — "
        "ten test przestal mierzyc to, co mowi")

    assert min(wywolania) < min(importy), (
        "`wyczysc_bajtkod` wolane w wierszu %d, a pierwszy import narzedzia stoi "
        "w %d — czyszczenie jest SPOZNIONE i wiersz `[BAJTKOD]` mowi o obronie, "
        "ktora nic nie zmienila" % (min(wywolania), min(importy)))


def test_zestaw_MOWI_ze_wyczyscil():
    """Wiersz `[BAJTKOD]` ma stac na stdout kazdego przebiegu — pole „Wyjscie".

    Czyszczenie ciche byloby zmiana, ktorej nikt nie zauwazy przy czytaniu wyjscia,
    a procedura reczna w dokumentach zostalaby jedyna widoczna obrona.
    """
    with tempfile.TemporaryDirectory() as katalog:
        # Modul PIASKOWNICY, a nie ten plik — i to nie jest ostroznosc, tylko
        # poprawka bledu popelnionego tutaj 11.09.2026. Pierwsza wersja podawala
        # `test_bytecode_staleness.py`, czyli modul, W KTORYM stoi ten test:
        # podproces uruchamial go od nowa, on odpalal kolejny podproces i tak bez
        # konca. Ta sama pomylka co w 6.D114, tylko z drugiej strony.
        sciezka = os.path.join(katalog, "test_piaskownica_bajtkodu.py")
        with open(sciezka, "w", encoding="utf-8") as handle:
            handle.write("def test_nic():\n    assert True\n")
        wynik = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "tests", "test_all.py"),
             sciezka],
            cwd=ROOT, capture_output=True, text=True)

    assert wynik.returncode == 0, (
        "przebieg piaskownicy nie wyszedl zielony: %s" % wynik.stdout[-400:])
    assert "[BAJTKOD]" in wynik.stdout, (
        "przebieg zestawu nie powiedzial, ze wyczyscil bajtkod; stdout zaczyna sie "
        "od: %r" % wynik.stdout[:200])
    assert "[BAJTKOD]" not in wynik.stderr, (
        "wiersz informacyjny poszedl na stderr — `test_runner_streams.py` zada "
        "stdout dla informacji")
    # Raz w TYM przebiegu — ale to NIE jest sprawdzenie wartowni na `sys`, i to
    # zdanie jest tu dlatego, ze pierwsza wersja tak je opisywala. Zmierzone
    # 11.09.2026 kontrola KN-4: zdjecie wartowni daje **12/12**, czyli zielono.
    # Powod: przebieg z jednym modulem nie laduje `test_all.py` po raz drugi —
    # `_discover` chodzi wylacznie po sciezkach z `only` — wiec wypis i tak pada
    # raz, z wartownia czy bez. Wartowni pilnuje test nizej, ladujac modul drugi
    # raz naprawde.
    assert wynik.stdout.count("[BAJTKOD]") == 1, (
        "wiersz `[BAJTKOD]` pada %d razy w przebiegu jednego modulu"
        % wynik.stdout.count("[BAJTKOD]"))


def test_wartownia_nie_pozwala_wyczyscic_dwa_razy_w_jednym_przebiegu():
    """Drugie zaladowanie `test_all.py` w tym samym procesie ma MILCZEC.

    **Po co osobny test.** W pelnym przebiegu `_discover` laduje `test_all.py`
    ponownie, pod nazwa `test_all__mierzony`, zeby jego wlasne testy tez szly przez
    licznik asercji. Bez wartowni na `sys` czyszczenie odpalaloby sie wtedy DRUGI
    RAZ, w srodku przebiegu, kasujac bajtkod, ktory wlasnie powstal — i mowiac
    o tym drugim wierszem `[BAJTKOD]`.

    **Dlaczego nie da sie tego zmierzyc przebiegiem jednego modulu.** Bo wtedy
    `_discover` drugiego zaladowania nie robi. Zmierzone 11.09.2026 (KN-4): asercja
    na liczbe wystapien wiersza w takim przebiegu jest zielona takze BEZ wartowni.
    Ten test laduje modul drugi raz sam, ta sama droga co `_discover`.
    """
    import contextlib
    import io as _io

    import assertion_gate as AG

    assert getattr(sys, "_metro_bajtkod_wyczyszczony", None) is not None, (
        "ten proces nie przeszedl jeszcze przez czyszczenie — test mierzylby "
        "PIERWSZE zaladowanie, nie drugie")

    bufor = _io.StringIO()
    with contextlib.redirect_stdout(bufor):
        AG.load_instrumented(os.path.join(ROOT, "tools", "tests", "test_all.py"),
                             "test_all__wartownia_probna")
    assert "[BAJTKOD]" not in bufor.getvalue(), (
        "drugie zaladowanie `test_all.py` w tym samym procesie znowu wyczyscilo "
        "bajtkod i powiedzialo o tym: %r" % bufor.getvalue()[:200])


# --- 6.D136: skąd w CI bierze się bajtkod, którego zestaw nie zastał pustym ---------

#: Workflow, w którym stoi krok tworzący bajtkod i krok zestawu.
WORKFLOW_ZESTAWU = os.path.join(ROOT, ".github", "workflows", "python-tests.yml")

#: Krok, który bajtkod TWORZY. Samej nazwy nie wystarczy pilnować — treść polecenia
#: czyta `CEL_KOMPILACJI` niżej, bo nazwa kroku przeżyłaby zmianę tego, co kompiluje.
KROK_KOMPILACJI = "Compile Python tools"

#: Wzorzec wyciągający CEL kompilacji z workflowa. **Dopasowanie musi sięgać końca
#: wiersza i to jest poprawka po kontroli, która wyszła ZIELONA** (KN-3): sprawdzanie
#: `POLECENIE_KOMPILACJI in tekst` przepuszczało `… -q tools/tests`, bo dawne polecenie
#: jest jego PRZEDROSTKIEM. Zawężenie celu z `tools` na `tools/tests` zmieniłoby liczbę
#: plików z 201 na 130, a bramka milczałaby.
CEL_KOMPILACJI = re.compile(r"run:\s*python3 -m compileall -q (\S+)\s*$", re.M)

#: Krok, który bajtkod ZASTAJE i kasuje (6.D122).
KROK_ZESTAWU = "Run tool tests"

#: **Zmierzone 11.09.2026 z logu joba `tools` przebiegu PR #530 i odtworzone lokalnie
#: na czystym drzewie.** CI wypisywało wtedy `[BAJTKOD] wyczyszczono 7 kat. __pycache__
#: (201 plikow) pod tools/`; `python3 -m compileall -q tools` po `find … -name
#: __pycache__ -prune -exec rm -rf` dawało **dokładnie te same liczby**.
#:
#: **201 → 202 przy 6.D138**, bo doszedł moduł `test_mass_copies.py`. Bramka niżej
#: zapaliła się na tej jedynce sama, w pierwszym przebiegu po dopisaniu pliku, i to
#: jest dowód, że mierzy drzewo, a nie własny komentarz. Rozkład dzisiejszy:
#: `tools/tests` **140**, `tools/blender` 29, `tools/track` 23, `tools/ci` 9,
#: `tools/visual` 5, `tools/physics` 3, `tools/data` 2.
#:
#: **Rozklad modulow po katalogach — 6.D263, i to jest zapadka na ZDANIE, nie na sume.**
#:
#: Suma (`MODULOW_W_CALYM_DRZEWIE`) byla przybita od 6.D255 i przez to KAZDY przyrost
#: lapala. Rozkladu nie pilnowalo nic — a zdanie o nim stoi w dwoch miejscach
#: (komentarz wyzej i `docs/06-worked-example.md`). Zmierzone 18.09.2026: OBA byly
#: nieprawdziwe, kazde inaczej. Komentarz mowil o `tools/tests` **136** przy 139
#: w drzewie; dokument mowil **138**, a liczbe te wpisalem przy 6.D260 przez
#: PODNIESIENIE poprzedniej o jeden, zamiast przez policzenie.
#:
#: Rownosc per katalog, a nie podloga: katalogow jest siedem i nie przybywa ich
#: co pozycje, wiec rownosc nie czerwienieje na pracy poprawnej — a to wlasnie
#: przyrost W JEDNYM katalogu przy niezmienionej sumie jest zdarzeniem, ktorego
#: suma nie widzi.
ROZKLAD_MODULOW = {
    # 139 -> 140 (18.09.2026, 6.D277): doszedl `test_digit_boundaries.py`.
    "tools/tests": 140,
    "tools/blender": 29,
    "tools/track": 23,
    "tools/ci": 9,
    "tools/visual": 5,
    "tools/physics": 3,
    "tools/data": 2,
}

#:
#: **136 -> 139 (18.09.2026, 6.D263): liczba byla NIEPRAWDZIWA i znalazlo ja sito
#: prozy z 6.D259.** Szesc pozostalych liczb tego zdania jest poprawnych co do
#: jednej — i zadna z nich nie jest POGRUBIONA. Sito oglada wylacznie pogrubione,
#: wiec zglosilo dokladnie te jedna, ktora sie zestarzala. Jest to najkrotszy
#: dowod, ze konwencja „pogrubienie znaczy liczba zmierzona" niesie tresc,
#: a nie ozdobe.
#:
#: **Po co ta liczba stoi tutaj.** Zdanie w `docs/06-worked-example.md` mówiło do
#: 11.09.2026, że „każdy przebieg CI zaczyna zimno". Pierwsza połowa uzasadnienia
#: (`git clean -ffdx`, `.gitignore`) jest prawdziwa, druga nie: bajtkod powstaje
#: PÓŹNIEJ, w nazwanym kroku tego samego joba. Liczba jest tu po to, żeby poprawione
#: zdanie miało czym się zestarzeć widocznie.
BAJTKOD_PO_COMPILEALL_KATALOGI = 7
#: 207 -> 208 (17.09.2026, 6.D233): doszedl `tools/tests/test_json_required.py`.
#: 208 -> 209 (17.09.2026, 6.D255): doszedl `tools/tests/test_message_claims.py`.
#: 209 -> 210 (17.09.2026, 6.D260): doszedl `tools/tests/test_value_chains.py`.
# 210 -> 211 (18.09.2026, 6.D277): doszedl `test_digit_boundaries.py`.
BAJTKOD_PO_COMPILEALL_PLIKI = 211


def _workflow_zestawu():
    with open(WORKFLOW_ZESTAWU, encoding="utf-8") as uchwyt:
        return uchwyt.read()


def test_krok_kompilacji_stoi_w_workflow_PRZED_zestawem():
    """Kolejność jest treścią: to ona tłumaczy, czemu zestaw nie zastaje pustki.

    Gdyby `compileall` stał PO zestawie, wypis `[BAJTKOD] wyczyszczono …` mówiłby
    o zerze i zdanie w dokumencie byłoby prawdziwe w dawnym brzmieniu. Test czyta
    pozycje obu kroków, a nie samą ich obecność.
    """
    tekst = _workflow_zestawu()
    assert KROK_KOMPILACJI in tekst, (
        "w `python-tests.yml` nie ma kroku %r — zdanie w `docs/06-worked-example.md` "
        "o tym, skąd bierze się bajtkod w CI, przestało mieć przedmiot" % KROK_KOMPILACJI)
    cele = CEL_KOMPILACJI.findall(tekst)
    assert cele == ["tools"], (
        "krok %r kompiluje %s zamiast całego `tools` — zawężenie celu zmienia liczbę "
        "plików bajtkodu, o której mówi dokument, i robi to po cichu"
        % (KROK_KOMPILACJI, cele or "nic"))
    assert tekst.index(KROK_KOMPILACJI) < tekst.index(KROK_ZESTAWU), (
        "krok kompilacji stoi PO zestawie — wtedy zestaw zastaje katalog pusty "
        "i dokument ma mówić co innego")


def test_compileall_na_czystym_drzewie_daje_liczby_z_logu_CI():
    """Liczby z CI odtworzone lokalnie, a nie przepisane z logu.

    Kopia `tools/` w katalogu tymczasowym, żeby nie ruszać bajtkodu drzewa roboczego
    w trakcie przebiegu zestawu — ten sam powód, dla którego 6.D90 przeniosło zapisy
    na kopię.
    """
    with tempfile.TemporaryDirectory(prefix="metro-compileall-") as katalog:
        # Cel brany Z WORKFLOWA, nie wpisany tu drugi raz: inaczej test mierzyłby
        # własne wyobrażenie o tym, co CI kompiluje (6.B28).
        z_workflowa = CEL_KOMPILACJI.findall(_workflow_zestawu())
        assert z_workflowa == ["tools"], (
            "workflow kompiluje %s, a ten test odtwarza liczby dla `tools` — "
            "liczby z logu CI przestaly opisywac to samo" % (z_workflowa or "nic"))
        cel = os.path.join(katalog, z_workflowa[0])
        shutil.copytree(os.path.join(ROOT, z_workflowa[0]), cel,
                        ignore=shutil.ignore_patterns("__pycache__"))
        wynik = subprocess.run([sys.executable, "-m", "compileall", "-q", cel],
                               capture_output=True, text=True)
        assert wynik.returncode in (0, 1), (
            "compileall skonczyl kodem %d: %s" % (wynik.returncode, wynik.stderr[:300]))

        # Liczenie idzie przez `tree_walk.policz_bajtkod`, a nie przez własne
        # `os.walk`: przedmiotem liczenia JEST katalog pominięty w `.gitignore`,
        # więc `TW.walk` odsiewałby dokładnie to, czego szukamy (zmierzone: 0 i 0),
        # a zapadkę `MAX_WOLNO_WPROST` wolno wyłącznie obniżać. Ten sam wybór, co
        # przy `wyczysc_bajtkod` w 6.D122.
        import tree_walk as TW

        katalogi, pliki = TW.policz_bajtkod(katalog, z_workflowa[0])

    assert (katalogi, pliki) == (BAJTKOD_PO_COMPILEALL_KATALOGI,
                                 BAJTKOD_PO_COMPILEALL_PLIKI), (
        "compileall na kopii `tools/` dal %d katalogow i %d plikow, a pomiar "
        "z 11.09.2026 (i log CI) mowil %d i %d — zdanie w `docs/06-worked-example.md` "
        "o tym, skad bierze sie bajtkod w CI, trzeba przeliczyc"
        % (katalogi, pliki, BAJTKOD_PO_COMPILEALL_KATALOGI, BAJTKOD_PO_COMPILEALL_PLIKI))


def test_dokument_nie_twierdzi_ze_CI_zaczyna_z_pustym_katalogiem():
    """Zdanie obalone pomiarem nie ma prawa wrócić — 6.D136.

    Bramka czyta akapit o CI w `docs/06-worked-example.md` i żąda dwóch rzeczy naraz:
    żeby nie było w nim dawnego twierdzenia, i żeby były liczby, które je zastąpiły.
    Sam zakaz przepuściłby akapit skasowany, a sam wymóg liczb — akapit mówiący
    jedno i drugie.
    """
    with open(os.path.join(ROOT, "docs", "06-worked-example.md"),
              encoding="utf-8") as uchwyt:
        tekst = uchwyt.read()

    plaski = " ".join(tekst.split())
    assert "każdy przebieg CI zaczyna zimno. **To jest" not in plaski, (
        "dawne brzmienie wrocilo do dokumentu jako TWIERDZENIE — log przebiegu je obala")
    assert KROK_KOMPILACJI in tekst, (
        "dokument nie nazywa kroku, ktory bajtkod tworzy — a to jest cala tresc 6.D136")
    assert str(BAJTKOD_PO_COMPILEALL_PLIKI) in tekst, (
        "dokument nie podaje liczby plikow (%d), wiec nie ma czym sie zestarzec "
        "widocznie" % BAJTKOD_PO_COMPILEALL_PLIKI)


# --- 6.D147: nieprawidlowe sekwencje ucieczki w zrodlach `tools/` ----------------

#: Wszystko, co po `\` jest w napisie Pythona SEKWENCJA PRAWIDLOWA. Reszta jest
#: zapowiedzia bledu: CPython mowi „such sequences will not work in the future".
PRAWIDLOWE_PO_UKOSNIKU = "\n\\'\"abfnrtvxNuU01234567"

#: Prefiksy literalu, po ktorych ucieczki nie ma — `r`, `rb`, `Rb`, `br`…
SUROWY = re.compile(r"^[a-zA-Z]*[rR][a-zA-Z]*['\"]")

#: Ile takich sekwencji ma byc w `tools/`. **Zero, przybite w OBIE strony.**
#:
#: **Zmierzone 12.09.2026 (6.D147): przed poprawka CZTERY, a nie trzy.** Wpis pozycji
#: mowil o trzech — `csharp_test_methods.py`, `test_conflict_markers.py`
#: i `test_next_task.py` — bo tyle stalo w logu CI przy 6.D136. Czwarta,
#: `test_dimension_audit.py`, **doszla pozniej i dolozylem ja ja sam przy 6.D139**
#: (`4358ab5`, dobe wczesniej). Nie zauwazyl tego nikt i nic: dlatego ta bramka
#: istnieje, a jej liczba jest przybita z obu stron, nie progiem.
MAX_SEKWENCJI_UCIECZKI = 0

#: Dolne ostrze na SAM SKAN: zepsuty czytnik daje zero sekwencji i zielono, czyli
#: czyta sie jak czystosc. Zmierzone 12.09.2026: **202** moduly pod `tools/`, skan
#: trwa 3,1 s. Prog stoi nizej, zeby nie ruszac go przy kazdym nowym narzedziu —
#: ale wysoko na tyle, zeby zawezenie skanu do jednego katalogu go zapalilo
#: (kontrola KN-5b: `tools/ci` to 9 modulow).
MINIMUM_MODULOW_SKANOWANYCH = 100


def _po_ukosnikach(fragment):
    """Znaki stojace zaraz po `\\` w tekscie literalu, z pominieciem par `\\\\`."""
    out = []
    i = 0
    while i < len(fragment) - 1:
        if fragment[i] == "\\":
            if fragment[i + 1] == "\\":
                i += 2
                continue
            out.append(fragment[i + 1])
            i += 2
            continue
        i += 1
    return out


def _sekwencje_w_zrodle(zrodlo):
    r"""`[(wiersz, sekwencja)]` — zle ucieczki w JEDNYM zrodle, czytane z TOKENOW.

    **Czytane z `tokenize`, a nie z `ast.get_source_segment`, i to jest wybor
    ZMIERZONY (14.09.2026, MB-04).** Poprzednia wersja chodzila po `ast`, brala dla
    kazdego `ast.Constant` fragment zrodla i odsiewala literaly surowe po prefiksie
    W TYM FRAGMENCIE. Do 3.11 czesci f-stringa dziedziczyly pozycje CALEGO literalu,
    wiec fragment zawieral `rf"` i odsianie dzialalo. Od 3.12 (PEP 701) kazdy kawalek
    tekstu f-stringa ma WLASNE `lineno/col_offset`, wskazujace sam tekst BEZ prefiksu
    — `SUROWY` przestawal trafiac, a bramka meldowala poprawne literaly `rf"..."`
    jako zle sekwencje.

    **Zmierzone na TYM drzewie, czterema interpreterami:**

        3.11.15     0 trafien   kod 0
        3.12.3      5 trafien   kod 1   ← wszystkie FALSZYWE
        3.13.12     5 trafien   kod 1
        3.14.0rc2   5 trafien   kod 1

    Runner CI ma 3.14.4, a to drzewo mialo 3.11.15 — i **ta roznica jest cala
    przyczyna, dla ktorej bramka byla zielona u mnie i czerwona w CI**. Zgloszone
    piec sekwencji to literaly `rf"..."` w `tools/tests/test_player_package.py`;
    sa POPRAWNE i nie wolno ich „naprawiac".

    **Dlaczego tokenizer, a nie latanie `ast`.** Tokenizer podaje prefiks tam, gdzie
    on w zrodle naprawde stoi, i robi to tak samo na obu epokach — **bez ani jednego
    rozgalezienia po `sys.version_info`**: do 3.11 caly f-string to jeden `STRING`
    z prefiksem, od 3.12 to `FSTRING_START` (niosacy `rf"`), `FSTRING_MIDDLE` (sam
    tekst) i `FSTRING_END`, a nazwy tych tokenow po prostu nie padaja na 3.11.
    Galaz nietestowana na danej wersji cicho by nie dzialala — tego wlasnie unikamy.

    **Wariant „badac caly `JoinedStr` raz" zostal odrzucony POMIAREM, nie argumentem.**
    Zaimplementowany i uruchomiony: na dzisiejszym drzewie daje zero trafien, ale
    wnosi NOWA klase falszywego alarmu dokladnie na tych wersjach, dla ktorych robimy
    poprawke — od 3.12 ukosnik jest legalny w polu podstawienia, wiec skan po calym
    fragmencie czyta KOD podstawienia jak tekst napisu i zapala sie na
    `f"{re.sub(r'\d', '', s)}"`. Ta wersja daje tam zero.
    """
    out = []
    # Jeden wpis na KAZDY otwarty f-string; `[-1]` mowi, wewnatrz ktorego stoi
    # biezacy `FSTRING_MIDDLE`. Stos, a nie flaga: od 3.12 f-string wolno zagniezdzic
    # w polu podstawienia innego, a w `rf"{f'\w'}"` zewnetrzny jest surowy, a
    # wewnetrzny NIE.
    surowy_stos = []
    for token in tokenize.generate_tokens(io.StringIO(zrodlo).readline):
        nazwa = tokenize.tok_name[token.type]
        if nazwa == "FSTRING_START":
            surowy_stos.append(bool(SUROWY.match(token.string)))
            continue
        if nazwa == "FSTRING_END":
            if surowy_stos:
                surowy_stos.pop()
            continue
        if nazwa == "FSTRING_MIDDLE":
            if surowy_stos and surowy_stos[-1]:
                continue
        elif nazwa == "STRING":
            if SUROWY.match(token.string):
                continue
        else:
            continue
        # Odsianie po ZRODLE tokenu, nie po wartosci literalu. Scislejsze niz dawne
        # i nie potrzebuje juz dowodu szczelnosci: token niesie tekst tak, jak stoi
        # w pliku, wiec brak ukosnika w tokenie znaczy brak ukosnika w zrodle.
        if "\\" not in token.string:
            continue
        for znak in _po_ukosnikach(token.string):
            if znak not in PRAWIDLOWE_PO_UKOSNIKU:
                out.append((token.start[0], "\\" + znak))
    return out


def sekwencje_ucieczki(korzen=None):
    r"""`[(plik, wiersz, sekwencja)]` dla kazdej NIEPRAWIDLOWEJ ucieczki w `tools/`.

    **Czytane ze ZRODLA, nie z ostrzezen interpretera, i to jest wybor zmierzony.**
    CPython zglasza te sekwencje jako `DeprecationWarning` do 3.11 wlacznie,
    a od 3.12 jako `SyntaxWarning`. Bramka oparta o klase ostrzezenia milczalaby
    na jednej z tych wersji — zmierzone 12.09.2026: na Pythonie 3.11.15 tego
    kontenera `python3 -W error::SyntaxWarning -m compileall -q tools` daje kod 0
    i ani jednego wiersza, przy CZTERECH sekwencjach w drzewie.

    **Drugie ograniczenie interpretera, wazniejsze:** CPython zglasza tylko PIERWSZA
    zla sekwencje w danym literale. W drzewie sprzed tej pozycji byly cztery
    ostrzezenia, ale **dziewiec** wystapien — `test_next_task.py` mial sam cztery
    (`\|`, `\.`, `\d`). Skan po zrodle widzi wszystkie.

    **`ast.parse` zostaje, ale juz WYLACZNIE jako przyrzad kontrolny.** Czytnikiem
    jest `_sekwencje_w_zrodle` (tokenizer); `ast.parse` odpowiada tu na inne pytanie
    — czy modul w ogole sie parsuje. Sam `tokenize` tego nie umie, bo jest
    leksykalny i `def f(:` przechodzi przez niego bez sprzeciwu, a wylapywanie
    modulow nieparsowalnych jest polowa tej bramki (KN-1 z 6.D147).
    """
    import tree_walk as TW

    korzen = os.path.join(ROOT, "tools") if korzen is None else korzen
    # `TW.znajdz`, a nie `os.walk`: odsianie `.gitignore` stoi w jednym miejscu,
    # a `__pycache__` odpada razem z nim — wlasna kopia tej listy rozjechalaby sie
    # przy nastepnym wpisie (6.D74, 6.D97, 6.D117).
    sciezki = TW.znajdz(korzen, "*.py", korzen)
    znalezione = []
    nieparsowalne = []
    for sciezka in sciezki:
        with open(sciezka, encoding="utf-8") as uchwyt:
            zrodlo = uchwyt.read()
        try:
            ast.parse(zrodlo)
        except SyntaxError as blad:
            # NIE `continue` po cichu. Zmierzone przy kontroli KN-1 tej pozycji:
            # plik, ktory sie nie parsuje, wypadal ze skanu bez sladu, a bramka
            # nizej meldowala „zero sekwencji" na drzewie, ktorego w calosci nie
            # przeczytala — rodzina 6.D27, tym razem w przyrzadzie tej pozycji.
            nieparsowalne.append((os.path.relpath(sciezka, korzen), str(blad)))
            continue
        try:
            trafienia = _sekwencje_w_zrodle(zrodlo)
        except (tokenize.TokenError, SyntaxError) as blad:
            nieparsowalne.append((os.path.relpath(sciezka, korzen), str(blad)))
            continue
        for wiersz, sekwencja in trafienia:
            znalezione.append((os.path.relpath(sciezka, korzen), wiersz, sekwencja))
    return znalezione, len(sciezki), nieparsowalne


def test_zrodla_tools_nie_niosa_ani_jednej_zlej_sekwencji_ucieczki():
    """Zapowiedz bledu nie ma prawa dojsc po cichu — 6.D147.

    Cztery poprawione tu docstringi dostaly prefiks `r`, i **zmierzono, ze wartosc
    zadnego z nich sie przez to nie zmienila** (dlugosc i tresc identyczne co do
    znaku). Obawa z pola „Dlaczego" tej pozycji — ze surowy napis zmieni sposob,
    w jaki czyta go bramka roszczen — jest wiec dla TYCH czterech nieprawdziwa:
    zadna z nich nie niesie ucieczki PRAWIDLOWEJ, ktora `r` by unieszkodliwilo.
    """
    znalezione, moduly, nieparsowalne = sekwencje_ucieczki()

    assert nieparsowalne == [], (
        "modul pod `tools/` sie NIE PARSUJE, wiec skan go pominal — zero sekwencji "
        "nizej byloby wtedy zdaniem o drzewie, ktorego bramka nie przeczytala "
        "w calosci: %s" % nieparsowalne)
    assert moduly >= MINIMUM_MODULOW_SKANOWANYCH, (
        "skan widzi %d modulow pod `tools/` przy progu %d — zero sekwencji nizej "
        "znaczyloby wtedy \u201eczytnik nie czyta\u201d, a nie \u201edrzewo czyste\u201d"
        % (moduly, MINIMUM_MODULOW_SKANOWANYCH))

    assert len(znalezione) == MAX_SEKWENCJI_UCIECZKI, (
        "nieprawidlowych sekwencji ucieczki jest %d, a zapadka stoi na %d: %s — "
        "napis z taka sekwencja przestanie sie kompilowac w przyszlym CPythonie, "
        "wiec dopisz `r` przed literalem albo zdubluj ukosnik"
        % (len(znalezione), MAX_SEKWENCJI_UCIECZKI, znalezione))


def test_czytnik_sekwencji_widzi_to_co_ma_i_nie_widzi_tego_czego_nie_ma():
    """Kontrola przyrzadu na drzewie probnym — 6.D147.

    Na drzewie repozytorium czytnik poprawny i czytnik zepsuty daja dzis TE SAMA
    zielen (zero sekwencji), wiec rozroznia je wylacznie wejscie syntetyczne.
    """
    with tempfile.TemporaryDirectory() as katalog:
        with open(os.path.join(katalog, "zly.py"), "w", encoding="utf-8") as uchwyt:
            uchwyt.write('x = "a \\| b"\ny = """c \\` d"""\n')
        with open(os.path.join(katalog, "dobry.py"), "w", encoding="utf-8") as uchwyt:
            uchwyt.write('x = r"a \\| b"\ny = "c \\n d"\nz = "e \\\\ f"\n')

        znalezione, moduly, nieparsowalne = sekwencje_ucieczki(katalog)
        assert moduly == 2, moduly
        assert nieparsowalne == [], nieparsowalne
        assert sorted(s for _p, _w, s in znalezione) == ["\\`", "\\|"], (
            "czytnik widzi %s, a ma widziec dokladnie dwie zle sekwencje z `zly.py`"
            % znalezione)
        # Po basename, bo sciezki drzewa probnego sa wzgledem `ROOT` repozytorium
        # i wychodza jako `../../tmp/…`; pytanie brzmi, KTORY plik, a nie gdzie lezy.
        assert {os.path.basename(p) for p, _w, _s in znalezione} == {"zly.py"}, (
            "czytnik zglasza plik, ktory ZADNEJ zlej sekwencji nie ma: %s" % znalezione)

    # I ze `\\\\` naprawde jest parą, a nie dwoma osobnymi ucieczkami — bez tego
    # kazdy zdublowany ukosnik w drzewie bylby falszywym alarmem.
    assert _po_ukosnikach(r'"a \\ b"') == [], _po_ukosnikach(r'"a \\ b"')
    assert _po_ukosnikach(r'"a \\\| b"') == ["|"], _po_ukosnikach(r'"a \\\| b"')

    # I ze plik NIEPARSOWALNY jest zglaszany, a nie przemilczany. Bez tej polowy
    # „zero sekwencji" bylo by prawda takze o drzewie, ktorego nie da sie wczytac.
    with tempfile.TemporaryDirectory() as katalog:
        with open(os.path.join(katalog, "polamany.py"), "w", encoding="utf-8") as uchwyt:
            uchwyt.write("def f(:\n    pass\n")
        znalezione, moduly, nieparsowalne = sekwencje_ucieczki(katalog)
        assert moduly == 1 and znalezione == [], (moduly, znalezione)
        assert [p for p, _b in nieparsowalne] == ["polamany.py"], nieparsowalne


#: Jedyny katalog najwyzszego poziomu, w ktorym stoi Python — 6.D159.
#:
#: **Przeslanka 6.D159 jest NIEPRAWDZIWA i to jest glowny wynik tej pozycji.** Pole
#: „Dlaczego to nie jest poszerzenie sciezki" mowilo, ze `tests/` i `src/` „nios\u0105
#: Pythona o innym przeznaczeniu (pomocniki testow C#, narzedzia sceny)". Zmierzone
#: 13.09.2026: **nie nios\u0105 ani jednego pliku `.py`**. Caly Python tego repozytorium
#: — co do jednego modulu — stoi pod `tools/`.
KATALOG_Z_PYTHONEM = "tools"

#: Ile modulow `.py` ma CALE drzewo, a nie tylko `tools/` — 6.D159.
#:
#: Rowna sie `BAJTKOD_PO_COMPILEALL_PLIKI` i to nie jest zbieg okolicznosci: skoro
#: caly Python stoi pod `tools/`, to `compileall -q tools` kompiluje CALOSC, a skan
#: sekwencji czyta CALOSC. Gdy te dwie liczby sie rozejda, znaczy to, ze gdzies
#: pojawil sie modul poza zasiegiem obu.
#: 207 -> 208 (17.09.2026, 6.D233): doszedl `tools/tests/test_json_required.py`.
#: 208 -> 209 (17.09.2026, 6.D255): doszedl `tools/tests/test_message_claims.py`.
#: 209 -> 210 (17.09.2026, 6.D260): doszedl `tools/tests/test_value_chains.py`.
# 210 -> 211 (18.09.2026, 6.D277): ten sam modul, ta sama jedynka.
MODULOW_W_CALYM_DRZEWIE = 211


def moduly_calego_drzewa(korzen=None):
    """`[sciezka wzgledna]` dla kazdego `.py` pod `korzen` — 6.D159.

    Tym SAMYM czytnikiem, ktorego uzywa `sekwencje_ucieczki`. Dwa czytniki
    rozjechalyby sie przy pierwszym wpisie do `.gitignore`, a zdanie „skan obejmuje
    cale drzewo" bylo by wtedy porownaniem dwoch roznych drzew.

    `korzen` jest parametrem, bo bez niego bramka polozenia nizej jest BEZCZYNNA —
    patrz `test_czytnik_drzewa_WIDZI_modul_poza_tools_gdy_taki_jest`.
    """
    import tree_walk as TW

    korzen = ROOT if korzen is None else korzen
    return sorted(os.path.relpath(s, korzen)
                  for s in TW.znajdz(korzen, "*.py", korzen))


def moduly_poza_katalogiem_z_pythonem(korzen=None):
    """`[sciezka wzgledna]` dla modulow stojacych POZA `tools/` — 6.D159."""
    return [s for s in moduly_calego_drzewa(korzen)
            if s.split(os.sep)[0] != KATALOG_Z_PYTHONEM]


def test_caly_Python_drzewa_stoi_pod_tools():
    """**GLOWNY WYNIK 6.D159: poza `tools/` nie ma ani jednego modulu.**

    Pozycja pytala, ile zlych sekwencji ucieczki stoi poza `tools/`, i zakladala, ze
    `tests/` oraz `src/` nios\u0105 Pythona. **Nie nios\u0105.** Odpowiedz „zero" jest wiec
    prawdziwa, ale NIE dlatego, ze tamtejszy Python jest czysty — tylko dlatego, ze
    tamtejszego Pythona nie ma. Te dwie odpowiedzi wygladaja tak samo w liczbie
    i roznia sie wszystkim innym: pierwsza mowi „sprawdzone", druga „nie ma czego
    sprawdzac, a gdy sie pojawi, nikt sie nie dowie".

    **Dlatego ta bramka pilnuje POLOZENIA, a nie liczby.** Pierwszy modul dopisany
    poza `tools/` wypada jednoczesnie z tej bramki, ze skanu sekwencji i z kroku
    `compileall -q tools` w CI — i ta asercja jest jedynym miejscem, ktore o tym
    powie.
    """
    wszystkie = moduly_calego_drzewa()
    assert len(wszystkie) == MODULOW_W_CALYM_DRZEWIE, (
        "modulow .py w drzewie jest %d, a pomiar z 13.09.2026 dal %d"
        % (len(wszystkie), MODULOW_W_CALYM_DRZEWIE))

    poza = moduly_poza_katalogiem_z_pythonem()
    assert not poza, (
        "modul .py stoi poza `%s/`: %s — wypada przez to ze skanu sekwencji "
        "ucieczki ORAZ z kroku `compileall -q %s` w CI, i zadna inna bramka tego "
        "nie zglosi" % (KATALOG_Z_PYTHONEM, poza, KATALOG_Z_PYTHONEM))


def test_czytnik_drzewa_WIDZI_modul_poza_tools_gdy_taki_jest():
    """Kontrola, ze bramka polozenia NIE jest tautologia — 6.D159.

    **Zmierzone, a nie przewidziane.** Pierwsza wersja tej pozycji nie miala tego
    testu i kontrola negatywna KN-1 wyszla przez to ZIELONA: zawezenie czytnika
    drzewa do samego `tools/` nie zmienialo niczego, bo caly Python i tak tam stoi.
    Bramka „poza `tools/` nie ma modulu" byla wtedy prawdziwa z pustego zbioru
    i przechodzilaby tak samo przy czytniku, ktory poza `tools/` nie patrzy wcale.

    Drzewo tych dwoch przypadkow nie rozdziela i rozdzielic nie moze — dopoki caly
    Python stoi pod `tools/`, oba daja te sama liczbe. Rozdziela je dopiero wejscie
    SYNTETYCZNE: drzewo tymczasowe, w ktorym modul poza `tools/` JEST.
    """
    with tempfile.TemporaryDirectory(prefix="metro-6d159-drzewo-") as katalog:
        os.makedirs(os.path.join(katalog, "tools", "tests"))
        os.makedirs(os.path.join(katalog, "tests"))
        for wzgledna in (os.path.join("tools", "tests", "w_srodku.py"),
                         os.path.join("tests", "na_zewnatrz.py")):
            with open(os.path.join(katalog, wzgledna), "w", encoding="utf-8") as u:
                u.write("X = 1\n")

        wszystkie = moduly_calego_drzewa(katalog)
        assert len(wszystkie) == 2, (
            "czytnik drzewa widzi %d modulow zamiast dwoch — wejscie syntetyczne "
            "nie opisuje tego, co mialo opisac: %s" % (len(wszystkie), wszystkie))
        poza = moduly_poza_katalogiem_z_pythonem(katalog)
        assert poza == [os.path.join("tests", "na_zewnatrz.py")], (
            "czytnik drzewa NIE widzi modulu poza `%s/`: %s — wtedy bramka "
            "polozenia jest zielona z pustego zbioru i nie zglosi pierwszego "
            "modulu dopisanego poza zasiegiem" % (KATALOG_Z_PYTHONEM, poza))


def test_skan_sekwencji_czyta_KAZDY_modul_drzewa_a_nie_tylko_swoj_katalog():
    """Zasieg bramki rowna sie calosci drzewa — 6.D159.

    Bez tego zdania „skan czyta 203 moduly" i „drzewo ma 203 moduly" sa dwoma
    niezaleznymi liczbami, ktore moga sie rozjechac po cichu. Tu stoi porownanie.
    """
    _znalezione, przeskanowanych, _nieparsowalne = sekwencje_ucieczki()
    assert przeskanowanych == MODULOW_W_CALYM_DRZEWIE, (
        "skan sekwencji czyta %d modulow, a drzewo ma ich %d — zasieg bramki "
        "przestal byc calym drzewem" % (przeskanowanych, MODULOW_W_CALYM_DRZEWIE))
    assert przeskanowanych == BAJTKOD_PO_COMPILEALL_PLIKI, (
        "skan sekwencji czyta %d modulow, a `compileall -q %s` kompiluje %d — "
        "jedno z dwoch przestalo obejmowac calosc"
        % (przeskanowanych, KATALOG_Z_PYTHONEM, BAJTKOD_PO_COMPILEALL_PLIKI))


def test_skan_ZNAJDUJE_zla_sekwencje_poza_tools_gdy_taka_jest():
    """Kontrola, ze zero z poprzedniej bramki jest zerem DRZEWA — 6.D159.

    Zdanie „poza `tools/` nie ma zlych sekwencji" jest dzis prawdziwe z powodu
    pustego zbioru. Gdyby skan byl slepy poza wlasnym katalogiem, brzmialoby tak
    samo — i dlatego stoi tu wejscie SYNTETYCZNE: katalog tymczasowy, ktory `tools/`
    nie jest, z jednym modulem niosacym `\\d`.

    Bez tej kontroli poszerzenie zasiegu bramki w przyszlosci mogloby nie zmienic
    niczego i nikt by tego nie zauwazyl.
    """
    with tempfile.TemporaryDirectory(prefix="metro-6d159-") as katalog:
        sciezka = os.path.join(katalog, "przyklad.py")
        with open(sciezka, "w", encoding="utf-8") as uchwyt:
            uchwyt.write('WZORZEC = "\\d+"\n')

        znalezione, przeskanowanych, nieparsowalne = sekwencje_ucieczki(katalog)
        assert przeskanowanych == 1, (
            "skan nie zobaczyl pliku w katalogu spoza `tools/` — wtedy zero "
            "z bramki polozenia jest zerem CZYTNIKA, a nie drzewa")
        assert not nieparsowalne, (
            "wejscie syntetyczne przestalo sie parsowac: %s" % nieparsowalne)
        assert [s for _p, _w, s in znalezione] == ["\\d"], (
            "skan nie znalazl `\\\\d` w katalogu spoza `tools/`: %s" % znalezione)



def rozklad_modulow(korzen=None):
    """`{katalog: ile plikow .py}` — POZYCZONYM czytnikiem, nie wlasnym globem.

    Pierwsza wersja wolala `glob.glob(..., recursive=True)` i zlapala to bramka
    `test_zaden_rekurencyjny_glob_nie_omija_wspolnego_odsiania`: wlasny glob omija
    odsianie z `.gitignore`, wiec liczylby pliki, ktorych suma nie liczy — dwie
    bramki mowilyby o dwoch roznych drzewach. Tu uzywany jest `moduly_calego_drzewa`,
    czyli dokladnie ten czytnik, ktory daje sume.
    """
    out = {}
    for sciezka in moduly_calego_drzewa(korzen):
        katalog = os.path.dirname(sciezka).replace(os.sep, "/")
        if katalog:
            out[katalog] = out.get(katalog, 0) + 1
    return out


def test_rozklad_modulow_po_katalogach_zgadza_sie_z_drzewem():
    """**Zapadka na ZDANIE o rozkladzie, nie tylko na sume — 6.D263.**

    Suma lapie kazdy przyrost, ale nie widzi PRZESUNIECIA: plik przeniesiony
    z `tools/track/` do `tools/tests/` zostawia sume bez zmian, a oba zdania
    o rozkladzie czyni nieprawdziwymi. Zmierzone 18.09.2026: oba i tak juz byly
    nieprawdziwe, kazde inna liczba.
    """
    w_drzewie = rozklad_modulow()
    assert w_drzewie == ROZKLAD_MODULOW, (
        "rozklad modulow po katalogach rozjechal sie ze zdaniem: w drzewie %s, "
        "w stalej %s — popraw OBA zdania (komentarz wyzej i `docs/06-worked-example.md`), "
        "bo mowia o tej samej rzeczy"
        % (sorted(w_drzewie.items()), sorted(ROZKLAD_MODULOW.items())))

    # Suma rozkladu MUSI byc ta sama liczba, ktora pilnuje zapadka sumy — inaczej
    # dwie bramki mowilyby o dwoch roznych drzewach.
    assert sum(ROZKLAD_MODULOW.values()) == MODULOW_W_CALYM_DRZEWIE, (
        "suma rozkladu to %d, a zapadka sumy stoi na %d"
        % (sum(ROZKLAD_MODULOW.values()), MODULOW_W_CALYM_DRZEWIE))


def test_oba_zdania_o_rozkladzie_niosa_TE_SAME_liczby():
    """Komentarz i `docs/06-worked-example.md` mowia o tym samym — niech mowia zgodnie.

    Bez tego testu jedno z dwoch zdan moze sie zestarzec w milczeniu, i **dokladnie
    tak sie stalo**: przez dobe stalo 136 w jednym i 138 w drugim, przy 139 w drzewie.
    """
    dokument = open(os.path.join(ROOT, "docs", "06-worked-example.md"),
                    encoding="utf-8").read()
    zrodlo = open(os.path.join(ROOT, "tools", "tests",
                               "test_bytecode_staleness.py"), encoding="utf-8").read()
    for katalog, ile in sorted(ROZKLAD_MODULOW.items()):
        wzor = re.compile(r"`%s`\s*\**\s*%d\b" % (re.escape(katalog), ile))
        assert wzor.search(dokument), (
            "`docs/06-worked-example.md` nie niesie pary %s = %d" % (katalog, ile))
        assert wzor.search(zrodlo), (
            "komentarz w tym module nie niesie pary %s = %d" % (katalog, ile))

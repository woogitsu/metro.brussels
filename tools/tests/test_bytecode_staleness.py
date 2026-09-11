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
#: na czystym drzewie.** CI wypisuje `[BAJTKOD] wyczyszczono 7 kat. __pycache__
#: (201 plikow) pod tools/`; `python3 -m compileall -q tools` po `find … -name
#: __pycache__ -prune -exec rm -rf` daje **dokładnie te same liczby**, z rozkładem
#: `tools/tests` 130, `tools/blender` 29, `tools/track` 23, `tools/ci` 9,
#: `tools/visual` 5, `tools/physics` 3, `tools/data` 2.
#:
#: **Po co ta liczba stoi tutaj.** Zdanie w `docs/06-worked-example.md` mówiło do
#: 11.09.2026, że „każdy przebieg CI zaczyna zimno". Pierwsza połowa uzasadnienia
#: (`git clean -ffdx`, `.gitignore`) jest prawdziwa, druga nie: bajtkod powstaje
#: PÓŹNIEJ, w nazwanym kroku tego samego joba. Liczba jest tu po to, żeby poprawione
#: zdanie miało czym się zestarzeć widocznie.
BAJTKOD_PO_COMPILEALL_KATALOGI = 7
BAJTKOD_PO_COMPILEALL_PLIKI = 201


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

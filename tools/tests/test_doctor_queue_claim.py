#!/usr/bin/env python3
"""`doctor.sh` mówi o kolejce to, co w niej stoi — a nie zdanie stałe.

**Skąd ta bramka (6.D95).** Do 10.09.2026 `doctor.sh` wypisywał obok policzonej
liczby napis STAŁY: „Kolejka faz 5 i 6 ma $queue_count pozycji do wzięcia, żadna nie
wymaga decyzji właściciela." Liczba pochodziła z pliku, zdanie o zbiorze — z niczego.
W tej samej policzonej kolejce stała **6.D53**, której pole „Zależy od" brzmi
dosłownie „decyzji właściciela o zapisie do `data/network/sources.json`".

To ta sama rodzina co 6.D27: przyrząd melduje sprawdzenie, którego nie zrobił.
Szkoda nie jest teoretyczna — `CLAUDE.md` §2 każe czytać doctora przed KAŻDYM
zadaniem, więc agent brał pierwszą pozycję w przekonaniu, że jest odblokowana,
i zatrzymywał się w połowie na cudzej decyzji.

**Czego te bramki NIE robią:** nie ruszają `open_items` (pole „Poza zakresem"
wyklucza to wprost) ani kolejności brania pozycji. Podział na dwie kupki bierze
wynik `open_items` i czyta pola „Zależy od".
"""
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_backlog as TB  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOCTOR = os.path.join(ROOT, "doctor.sh")
TASKS = os.path.join(ROOT, "docs", "TASKS.md")

#: Zdanie, którego w `doctor.sh` być nie może: twierdzenie o zbiorze wypowiadane
#: bez zajrzenia do zbioru. Zostaje w kodzie jako gałąź dla przypadku, w którym
#: NAPRAWDĘ nikt nie czeka — ale wtedy jest wynikiem pomiaru, nie napisem stałym.
ZDANIE_BEZWARUNKOWE = "pozycji do wzięcia, żadna nie wymaga decyzji właściciela"

#: Do 10.09.2026 stała tu kotwica `KOTWICA_ZABLOKOWANA = "6.D53"` — pozycja, o której
#: wiadomo było, że czeka na właściciela. **Padła zgodnie z przeznaczeniem**: decyzja
#: z 10.09.2026 odblokowała 6.D53, a wraz z nią 6.D108, i kolejka nie ma dziś ANI
#: JEDNEJ pozycji czekającej na właściciela. Kotwica na numerze nie da się już
#: postawić, bo nie ma czego zakotwiczyć — i to jest stan poprawny, nie luka.
#:
#: Rolę kotwicy przejmuje **wejście syntetyczne**: `test_dopisanie_pozycji_zaleznej_
#: od_wlasciciela_zmienia_wypis` dopisuje pozycję z taką zależnością i sprawdza, że
#: doctor ją nazywa. Werdykt na dzisiejszej kolejce jest odtąd sterowany STANEM: gdy
#: nikt nie czeka, zdanie bezwarunkowe jest PRAWDĄ i ma stać; gdy ktoś czeka, ma
#: zniknąć i ustąpić nazwom.


def _tresc_zadan():
    with open(TASKS, encoding="utf-8") as uchwyt:
        return uchwyt.read()


def _doctor_w_kopii(tresc_zadan):
    """`doctor.sh` puszczony na drzewie, w którym `docs/TASKS.md` jest podmieniony.

    **Dlaczego symlinki, a nie kopia repozytorium.** Doctor sprawdza kilkanaście
    ścieżek i przy braku którejkolwiek kończy przed blokiem, w którym stoi zdanie
    o kolejce — kopia częściowa nie odpowiedziałaby więc na pytanie tego testu.
    Drzewo z symlinkami do wszystkiego POZA `docs/` (a w `docs/` do wszystkiego poza
    `TASKS.md`) daje doctorowi komplet, a podmienia dokładnie jeden plik.

    **Atrapa `dotnet` jest konieczna**, bo w kontenerze tej sesji SDK nie stoi
    w `PATH`, doctor melduje wtedy pozycję do naprawienia i **nie dochodzi** do bloku
    z kolejką. Ta sama technika co w `test_dotnet_version._run_doctor`.
    """
    with tempfile.TemporaryDirectory() as tmp:
        drzewo = os.path.join(tmp, "repo")
        os.makedirs(drzewo)
        for nazwa in os.listdir(ROOT):
            if nazwa == "docs":
                continue
            os.symlink(os.path.join(ROOT, nazwa), os.path.join(drzewo, nazwa))
        docs = os.path.join(drzewo, "docs")
        os.makedirs(docs)
        for nazwa in os.listdir(os.path.join(ROOT, "docs")):
            if nazwa == "TASKS.md":
                continue
            os.symlink(os.path.join(ROOT, "docs", nazwa), os.path.join(docs, nazwa))
        with open(os.path.join(docs, "TASKS.md"), "w", encoding="utf-8") as uchwyt:
            uchwyt.write(tresc_zadan)

        atrapa = os.path.join(tmp, "bin", "dotnet")
        os.makedirs(os.path.dirname(atrapa))
        with open(atrapa, "w", encoding="utf-8") as uchwyt:
            uchwyt.write('#!/bin/sh\nif [ "$1" = "--version" ]; then echo "99.1.2"; '
                         "exit 0; fi\nexit 1\n")
        os.chmod(atrapa, 0o755)
        dom = os.path.join(tmp, "home")
        os.makedirs(dom)

        srodowisko = dict(os.environ, DOTNET_BIN=atrapa, HOME=dom, LC_ALL="C")
        gotowe = subprocess.run(["bash", DOCTOR, "--no-tests"], cwd=drzewo,
                                env=srodowisko, capture_output=True, text=True,
                                timeout=180)
        return gotowe.stdout + gotowe.stderr


def test_doctor_mowi_o_kolejce_to_co_w_niej_stoi():
    """Wypis na DZISIEJSZEJ kolejce zgadza się z tym, co znajduje czytnik pól.

    **Werdykt sterowany STANEM, nie kotwicą na numerze** (10.09.2026). Poprzednia
    wersja żądała, żeby wypis wymieniał 6.D53, i padła w chwili, w której decyzja
    właściciela ją odblokowała — czyli dokładnie wtedy, kiedy miała paść. Dziś
    kolejka nie ma ani jednej pozycji czekającej na właściciela, więc zdanie
    bezwarunkowe jest PRAWDĄ i ma stać; gdy pojawi się pierwsza taka pozycja, ma
    zniknąć i ustąpić nazwom. Obie strony są tu sprawdzone, więc test nie przechodzi
    dlatego, że lista zrobiła się pusta.
    """
    tresc = _tresc_zadan()
    wypis = _doctor_w_kopii(tresc)
    assert "Kolejka faz 5 i 6" in wypis, (
        "doctor nie doszedł do bloku o kolejce — bez tego reszta testu nic nie mierzy:\n"
        + wypis[-600:])
    czekaja = TB.czeka_na_wlasciciela(tresc)

    if czekaja:
        assert ZDANIE_BEZWARUNKOWE not in wypis, (
            "doctor twierdzi o CAŁYM zbiorze, że nikt nie czeka na decyzję "
            "właściciela; czytnik pól znajduje dziś: " + ", ".join(czekaja))
        for numer in czekaja:
            assert numer in wypis, (
                f"{numer} czeka na decyzję właściciela, a wypis jej nie nazywa:\n"
                + wypis[-600:])
        # LICZBY W WYPISIE MAJĄ SIĘ ZGADZAĆ Z NAZWANĄ LISTĄ. Ta asercja doszła po
        # tym, jak kontrola negatywna KN-5 (doctor liczy wolne pozycje jako WSZYSTKIE
        # otwarte) przeszła przez trzy pozostałe bramki: wypis mówił wtedy „13
        # pozycji, z czego 13 do wzięcia od ręki" i w następnym wierszu wymieniał
        # 6.D53 jako zablokowaną. Zdanie sprzeczne samo ze sobą, i żadna bramka go
        # nie widziała. Stoi w tej gałęzi, bo doctor drukuje dwie liczby TYLKO tu —
        # przy pustym zbiorze wiersz ma jedną i o czym innym.
        liczby = re.search(r"ma (\d+) pozycji, z czego (\d+) do wzięcia", wypis)
        assert liczby, (
            "nie da się odczytać dwóch liczb z wiersza o kolejce:\n" + wypis[-600:])
        wszystkie, wolne = int(liczby.group(1)), int(liczby.group(2))
        assert wszystkie - wolne == len(czekaja), (
            f"doctor mówi {wszystkie} pozycji i {wolne} do wzięcia, czyli "
            f"{wszystkie - wolne} zablokowanych, a wymienia {len(czekaja)}: {czekaja}")
    else:
        assert ZDANIE_BEZWARUNKOWE in wypis, (
            "nikt nie czeka na decyzję właściciela, a doctor tego nie mówi — "
            "zdanie o pustym zbiorze też jest zdaniem o zbiorze:\n" + wypis[-600:])
        # Jedna liczba, i ma się zgadzać z policzoną kolejką: gałąź pusta drukuje
        # „ma N pozycji do wzięcia", bez rozbicia, bo rozbijać nie ma czego.
        liczba = re.search(r"ma (\d+) pozycji do wzięcia", wypis)
        assert liczba, (
            "nie da się odczytać liczby z wiersza o kolejce:\n" + wypis[-600:])
        assert int(liczba.group(1)) == len(TB.open_items(tresc)), (
            f"doctor mówi {liczba.group(1)} pozycji do wzięcia, a otwartych jest "
            f"{len(TB.open_items(tresc))}")


#: Pole „Zależy od", które mówi o decyzji właściciela — do zdjęcia w kontroli niżej.
#: Wzorzec, a nie treść jednej pozycji: zależności takich bywa w kolejce więcej niż
#: jedna, a kontrola ma mierzyć „ani jednej", nie „bez tej konkretnej".
POLE_WLASCICIELA = re.compile(
    r"- \*\*Zależy od:\*\*[^\n]*właściciel[^\n]*(?:\n  [^\n-][^\n]*)*")


def test_dopisanie_pozycji_zaleznej_od_wlasciciela_zmienia_wypis():
    """Kontrola z pola „Skończone, gdy": pozycja SYNTETYCZNA, nie zmiana w drzewie.

    Dwie strony, bo tylko razem coś znaczą: kolejka bez ani jednej pozycji zależnej
    od właściciela ma dawać zdanie „żadna nie wymaga", a dopisanie takiej pozycji ma
    je zmienić i wymienić numer. Bez pierwszej strony bramka przechodziłaby także dla
    doctora, który wypisuje ostrzeżenie ZAWSZE.
    """
    tresc = _tresc_zadan()

    # Strona pierwsza: zdejmujemy WSZYSTKIE zależności od właściciela, jakie ma dziś
    # kolejka, i sprawdzamy, że doctor to widzi.
    #
    # **Wszystkie, a nie jedną wpisaną z nazwy** (10.09.2026). Do tego dnia stała tu
    # dosłowna treść pola 6.D53 jako „jedynej zależności, jaką ma dziś kolejka" — i to
    # przestało być prawdą w chwili, w której druga pozycja (6.D108) została odłożona
    # na decyzję właściciela. Kontrola padła wtedy z listą `['6.D108']`, czyli mówiła
    # o stanie kolejki sprzed zmiany. Zdejmowanie po WZORCU nie starzeje się przy
    # trzeciej takiej pozycji.
    bez_zaleznosci = POLE_WLASCICIELA.sub("- **Zależy od:** brak.", tresc)
    assert bez_zaleznosci != tresc, (
        "nie znaleziono ani jednego pola zależności od właściciela do zdjęcia — "
        "kolejka albo wzorzec się zmieniły i ta kontrola przestała mierzyć to, "
        "co obiecuje")
    assert TB.czeka_na_wlasciciela(bez_zaleznosci) == [], \
        TB.czeka_na_wlasciciela(bez_zaleznosci)
    wypis_bez = _doctor_w_kopii(bez_zaleznosci)
    assert ZDANIE_BEZWARUNKOWE in wypis_bez, (
        "kolejka bez ani jednej pozycji zależnej od właściciela, a doctor i tak "
        "ostrzega — ostrzeżenie wypisywane zawsze nie niesie informacji:\n"
        + wypis_bez[-600:])

    # Strona druga: dopisujemy pozycję SYNTETYCZNĄ z taką zależnością.
    syntetyczna = bez_zaleznosci.replace(
        "##### 6.D95 ·",
        "##### 6.Z1 · Pozycja syntetyczna kontroli 6.D95\n\n"
        "- **Skąd:** kontrola negatywna.\n"
        "- **Wejście:** nic.\n"
        "- **Wyjście:** nic.\n"
        "- **Weryfikacja:** nic.\n"
        "- **Skończone, gdy:** nigdy.\n"
        "- **Poza zakresem:** wszystko.\n"
        "- **Zależy od:** decyzji właściciela o czymkolwiek.\n\n"
        "##### 6.D95 ·", 1)
    syntetyczna = syntetyczna.replace(
        "| 6.D95 |", "| 6.Z1 | **Pozycja syntetyczna** | kontrola | S |\n| 6.D95 |", 1)
    assert TB.czeka_na_wlasciciela(syntetyczna) == ["6.Z1"], (
        "pozycja syntetyczna nie weszła do kolejki albo nie została rozpoznana: "
        + repr(TB.czeka_na_wlasciciela(syntetyczna)))

    wypis_z = _doctor_w_kopii(syntetyczna)
    assert ZDANIE_BEZWARUNKOWE not in wypis_z, (
        "kolejka ma pozycję 6.Z1 zależną od decyzji właściciela, a doctor twierdzi "
        "o całym zbiorze, że nikt nie czeka:\n" + wypis_z[-600:])
    assert "6.Z1" in wypis_z, (
        "dopisana pozycja zależna od decyzji właściciela nie zmieniła wypisu:\n"
        + wypis_z[-600:])


def test_podzial_kolejki_zgadza_sie_z_polami_zaleznosci():
    """Dwie kupki sumują się do całości i żadna nie jest liczona dwa razy."""
    tresc = _tresc_zadan()
    otwarte = TB.open_items(tresc)
    czekaja = TB.czeka_na_wlasciciela(tresc)
    wolne = TB.do_wziecia(tresc)

    assert set(czekaja) | set(wolne) == set(otwarte), (czekaja, wolne, otwarte)
    assert not (set(czekaja) & set(wolne)), (czekaja, wolne)
    assert len(czekaja) + len(wolne) == len(otwarte)

    # Kotwicy na numerze tu nie ma i to jest wybór: 10.09.2026 kolejka przestała mieć
    # ANI JEDNĄ pozycję czekającą na właściciela, więc każda taka kotwica byłaby
    # zdaniem o stanie, który się zmienił. Że podział UMIE rozdzielić kupki, mierzy
    # `test_czytnik_blokad_rozroznia_oba_ksztalty_na_kolejce_syntetycznej`
    # w `test_backlog.py` — na wejściu syntetycznym, więc niezależnie od tego, czy
    # dziś ktoś czeka.
    assert wolne, "kolejka nie ma ani jednej pozycji do wzięcia — to nie jest podział"


def test_czytnik_pola_zaleznosci_rozroznia_trzy_ksztalty():
    """Kontrola PRZYRZĄDU na wejściu syntetycznym: numer, właściciel, brak pola.

    Bez niej „6.D53 jest na liście" znaczyłoby tyle samo, co „funkcja zwraca cokolwiek".
    """
    numer = "##### 6.X1 · a\n- **Zależy od:** 6.D73.\n"
    wlasciciel = "##### 6.X2 · b\n- **Zależy od:** decyzji właściciela o czymś.\n"
    bez_pola = "##### 6.X3 · c\n- **Skąd:** nic.\n"

    assert TB.pole_zaleznosci(numer) == "6.D73.", TB.pole_zaleznosci(numer)
    assert TB.SLOWO_WLASCICIELA not in TB.pole_zaleznosci(numer).lower(), (
        "pole wskazujące na INNĄ POZYCJĘ zostało wzięte za decyzję właściciela: "
        + TB.pole_zaleznosci(numer))
    assert TB.SLOWO_WLASCICIELA in TB.pole_zaleznosci(wlasciciel).lower(), (
        "pole mówiące o decyzji właściciela nie zostało rozpoznane — czytnik albo "
        f"słowo szukane są zepsute: {TB.pole_zaleznosci(wlasciciel)!r} wobec "
        f"szukanego {TB.SLOWO_WLASCICIELA!r}")
    assert TB.pole_zaleznosci(bez_pola) == "", (
        "brak pola „Zależy od” ma dawać pusty napis, a nie treść sąsiedniego pola: "
        + repr(TB.pole_zaleznosci(bez_pola)))

    wieloliniowe = ("##### 6.X4 · d\n- **Zależy od:** decyzji\n  właściciela,\n"
                    "  rozbitej na dwa wiersze.\n- **Inne:** nie to.\n")
    assert TB.pole_zaleznosci(wieloliniowe) == "decyzji właściciela, rozbitej na dwa wiersze.", (
        "czytnik gubi drugą linię złamanego pola — a pole „Zależy od” bywa łamane: "
        + repr(TB.pole_zaleznosci(wieloliniowe)))


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

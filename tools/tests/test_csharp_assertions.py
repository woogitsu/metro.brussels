#!/usr/bin/env python3
"""Bramka: kazda metoda testowa C# ma w tresci asercje.

Powod, granice i pomiary — w docstringu `tools/tests/csharp_assertions.py`.
Ten modul sprawdza dwie rzeczy osobno: **drzewo** (zero metod bez asercji) i **czytnik**
(czy widzi oba ksztalty ciala, pomocnika `Assert*`, i czy zglasza brak, gdy brak jest).

**Od 6.D145 dochodzi trzecia**: zapadka na asercje bez KOMUNIKATU, per plik, w obie
strony — odpowiednik `NIEME_ASERCJE` po stronie Pythona. Klasyfikacja ma trzy klasy,
bo komunikat C# rozpoznaje sie po TYPIE ostatniego argumentu, a typu identyfikatora
nie widac bez sprawdzacza typow; klasa `NIEROZSTRZYGNIETE` nazywa te niewiedze zamiast
ja chowac. Powody i pomiary: `reports/6d145-komunikaty-asercji-csharp.md`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csharp_assertions as CA  # noqa: E402
import csharp_test_methods as CTM  # noqa: E402

#: Ile metod testowych bramka ma WIDZIEC, zeby pomiar byl pomiarem. Bez tego progu
#: literowka w czytniku dalaby zero metod, zero brakow i zielona bramke — ta sama
#: pulapka, ktora zamyka `MINIMUM_CLAIMS` w `test_report_claims.py` i prog deklaracji
#: w `test_dead_constants_csharp.py`.
#:
#: **Liczba przepisana 07.09.2026 przy 6.B28, razem ze sprostowaniem.** Poprzednia
#: wersja mowila „zmierzone 07.09.2026: **674**" i stawiala prog na 600. Tamte 674
#: byly liczone przejsciem, ktore liczylo klamry w literalach napisowych i gubilo
#: przez to **27 prawdziwych metod** (`ServiceDayTests.cs` w calosci), a do tego
#: pomijalo 13 metod `[DataTestMethod]` z argumentami. Po obu poprawkach z 6.B28
#: metod testowych jest **719** — tyle, ile atrybutow testowych w plikach. Prog 600
#: przechodzil rowniez wtedy, gdy czytnik gubil te 27; prog, ktory nie zauwaza utraty
#: jednej metody z dwudziestu piu, nie mierzy tego, co obiecuje mierzyc.
MINIMUM_METOD = 700


def test_the_gate_sees_the_test_methods_it_is_supposed_to_see():
    ile = CA.coverage()["metody_testowe"]
    assert ile >= MINIMUM_METOD, (
        "czytnik widzi %d metod testowych przy progu %d — przestal pasowac do ksztaltu, "
        "w jakim to repozytorium pisze testy C#" % (ile, MINIMUM_METOD))


def test_every_csharp_test_method_has_an_assertion_in_its_body():
    braki = CA.bez_asercji()
    assert not braki, (
        "metoda testowa C# bez ani jednej asercji w tresci: "
        + "; ".join("%s :: %s.%s" % b for b in braki)
        + ". Test bez asercji przechodzi zawsze — po stronie Pythona jest to awaria "
          "od #139, a po stronie C# nie bylo nic (6.D28)")


def _klasa(cialo):
    return ("using Microsoft.VisualStudio.TestTools.UnitTesting;\n\n"
            "[TestClass]\npublic class Przyklad\n{\n" + cialo + "}\n")


def _czytaj(cialo, tmp_path=None):
    """Uruchom czytnik na jednej syntetycznej klasie w katalogu tymczasowym."""
    import tempfile
    with tempfile.TemporaryDirectory() as katalog:
        podkatalog = os.path.join(katalog, "tests", "Przyklad.Tests")
        os.makedirs(podkatalog)
        with open(os.path.join(podkatalog, "PrzykladTests.cs"), "w",
                  encoding="utf-8") as uchwyt:
            uchwyt.write(_klasa(cialo))
        return CA.metody_testowe(katalog)


def test_the_reader_sees_both_shapes_of_a_method_body():
    """Blok `{ ... }` i cialo wyrazeniowe `=> ...;`.

    Ta para nie jest ostroznoscia na zapas. Pierwsza wersja czytnika znala tylko blok
    i zglosila `Lista_funkcji_KCV_jest_dokladnie_ta_ktora_podaje_STIB` jako metode bez
    asercji — a ona asertuje `CollectionAssert.AreEqual` w ciele wyrazeniowym.
    Czytnik, ktory jednej postaci nie zna, zglasza **wlasna niewiedze** jako brak.
    """
    dane = _czytaj(
        "    [TestMethod]\n"
        "    public void Blokiem()\n"
        "    {\n        Assert.IsTrue(true);\n    }\n\n"
        "    [TestMethod]\n"
        "    public void Wyrazeniem() =>\n"
        "        CollectionAssert.AreEqual(new[] { 1, 2 }, new[] { 1, 2 });\n")
    nazwy = {m: ma for _p, _k, m, ma in dane}
    assert nazwy == {"Blokiem": True, "Wyrazeniem": True}, nazwy


def test_a_helper_whose_name_starts_with_assert_counts_as_an_assertion():
    """Zmierzone: cztery metody w `BrakingTests` asertuja przez lokalny `AssertBits`.
    Bez tej reguly bramka zglaszalaby je jako braki, czyli swiecilaby na poprawnym
    kodzie — a taka bramka zostaje wylaczona, nie poprawiona (6.D27)."""
    dane = _czytaj(
        "    [TestMethod]\n"
        "    public void PrzezPomocnika()\n"
        "    {\n        AssertBits(1.0, 1.0);\n    }\n\n"
        "    private static void AssertBits(double a, double b)\n"
        "    {\n        Assert.AreEqual(a, b);\n    }\n")
    nazwy = {m: ma for _p, _k, m, ma in dane}
    assert nazwy == {"PrzezPomocnika": True}, nazwy


def test_a_test_method_without_any_assertion_is_reported():
    """Kontrola pozytywna detektora, wykonywana przy KAZDYM przebiegu.

    Bez niej bramka wyzej byla by zielona takze wtedy, gdyby czytnik uznawal za
    asertujaca kazda metode — czyli gdyby przestal cokolwiek rozrozniac. Drzewo ma
    dzis zero brakow, wiec sama zielona bramka tego nie odrozni.
    """
    dane = _czytaj(
        "    [TestMethod]\n"
        "    public void NicNieSprawdza()\n"
        "    {\n        var x = 1 + 1;\n        _ = x;\n    }\n")
    assert [(m, ma) for _p, _k, m, ma in dane] == [("NicNieSprawdza", False)], dane


def test_a_method_without_a_test_attribute_is_not_counted():
    """Pomocnik nie jest testem i nie ma obowiazku asertowac."""
    dane = _czytaj(
        "    private static void Reset()\n"
        "    {\n        var x = 1;\n        _ = x;\n    }\n")
    assert dane == [], dane


def test_both_readers_agree_exactly_on_how_many_methods_carry_a_test_attribute():
    """Dwa zastosowania, JEDNO przejscie — wiec rownosc, nie pasmo.

    **Ten test jest przepisany, a nie dopisany obok (6.D30).** Wersja z 6.D28 zadala
    `nowy - stary <= 20`, i to pasmo bylo **fudge'em**: postawilem je, bo majac dwa
    osobne przejscia po ciele klasy nie moglem postawic rownosci, a nie bo 20 cokolwiek
    znaczylo. Zmierzone wtedy na drzewie: roznica wynosila **0** — pasmo nie opisywalo
    zadnego prawdziwego rozjazdu, tylko moja niepewnosc co do wlasnego kodu.

    6.D30 sciagnela przejscie do `csharp_test_methods` i skasowala starsze, wiec oba
    czytniki chodza po tej samej strukturze i roznica **musi** byc zerem. Gdyby ktos
    dopisal drugie przejscie z powrotem, ten test upadnie na pierwszej metodzie, ktorej
    jedno widzi, a drugie nie — czego pasmo 20 przepuszczaloby dwadziescia razy.
    """
    stary = sum(1 for _p, _k, _m, ma in CTM.metody() if ma)
    nowy = CA.coverage()["metody_testowe"]
    assert nowy == stary, (
        "czytniki podaja rozne liczby metod z atrybutem: %d vs %d — a od 6.D30 chodza "
        "po TYM SAMYM przejsciu, wiec roznica znaczy, ze ktos dopisal drugie" % (nowy, stary))


def test_there_is_only_one_traversal_of_a_class_body():
    """Sedno 6.D30, sprawdzone na kodzie, a nie na liczbach.

    Rownosc wyzej byla by prawdziwa takze przy dwoch przejsciach, ktore akurat zgadzaja
    sie na dzisiejszym drzewie — tak wlasnie bylo przy 6.D28. Ten test patrzy na to, co
    tamten test przepuszcza: `czlonkowie` ma byc zdefiniowane w JEDNYM module, a drugi
    ma je wolac, nie kopiowac.
    """
    with open(CA.__file__, encoding="utf-8") as uchwyt:
        asercje = uchwyt.read()
    with open(CTM.__file__, encoding="utf-8") as uchwyt:
        metody = uchwyt.read()
    assert "def czlonkowie(" in metody, (
        "przejscie zniknelo z modulu nizszego — a to on jest jego miejscem")
    assert "def czlonkowie(" not in asercje, (
        "drugie przejscie wrocilo do csharp_assertions.py; 6.D30 sciagnela je do "
        "csharp_test_methods wlasnie po to, zeby bylo jedno")
    assert "CTM.czlonkowie(" in asercje, (
        "csharp_assertions nie wola wspolnego przejscia")
    # DEFINICJA, nie sama nazwa — i to nie jest ustepstwo dla wygody. Pierwsza wersja
    # tego testu zabraniala nazwy w calym pliku i zapalila sie na komentarzu, ktory
    # WYJASNIA, dlaczego starsze przejscie zniknelo. Wzmianka nie jest powrotem; ta sama
    # roznica, ktora 6.D27 postawilo miedzy twierdzeniem a odsylaczem.
    assert "def _poziom_bezposredni(" not in metody, (
        "starsze przejscie wrocilo — mialo wycinac wnetrza klamr, wiec asercji nie "
        "widzi, a jego definicja znaczy, ze znowu sa dwa")
    assert "def _poziom_bezposredni(" not in asercje, (
        "starsze przejscie wrocilo, tym razem do csharp_assertions.py")


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw.

# --- asercja rozstrzygajaca, nie tylko prawdziwa (6.A29) -------------------------

#: Testy odmowy komorki z 6.A24 i to, co KAZDY z nich musi asercjonowac, zeby
#: odrozniac komunikat 6.A24 od dowolnej innej odmowy `compare`.
#:
#: **Skad ta bramka.** Zmierzone kontrola KN-1 pozycji 6.A25: przy `compare` z zerowa
#: liczba czlonow pozycyjnych piec testow `compare` padlo, a
#: `Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy` ZOSTAL ZIELONY — jego trzy
#: asercje (kod 1, tresc zawiera sciezke zepsutego pliku, tresc nie zawiera dobrego)
#: spelnia dowolna odmowa nazywajaca pierwsza sciezke z wiersza polecen. Asercja
#: prawdziwa, ale nie rozstrzygajaca.
#:
#: Pomiar z 07.09.2026: z czterech testow rodziny 6.A24 asercje rozstrzygajaca mialy
#: TRZY — ten jeden nie. Poprawka dotyczy wiec jednego testu, nie czterech, i to jest
#: odpowiedz na pytanie z pola „Wyjscie" pozycji 6.A29.
ASERCJE_ODMOWY_KOMORKI = {
    "Zepsuta_komorka_nazywa_plik_wiersz_i_kolumne": ("wiersz ", "kolumna ", "step"),
    "Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy": (
        "wiersz ", "kolumna ", "chainage_m"),
    "Numer_i_nazwa_kolumny_ida_z_pozycji_w_wierszu": (
        "wiersz ", "kolumna ", "speed_mps"),
}

#: Test drugiego kierunku tej samej rodziny: dwa poprawne pliki koncza sie kodem 0.
#: Tresci odmowy nie asercjonuje, bo odmowy nie ma — i to jest poprawne, dlatego
#: stoi osobno, a nie w slowniku wyzej. Wypisany, zeby jego zniknięcie bylo widoczne.
TEST_DRUGIEGO_KIERUNKU = "Dwa_poprawne_pliki_nadal_przechodza"


def _cialo_metody(zrodlo, nazwa):
    at = zrodlo.index("public void " + nazwa + "(")
    return zrodlo[at:zrodlo.index("\n    }", at)]


def test_every_cell_refusal_test_asserts_what_only_that_message_carries():
    """Asercja ma ROZSTRZYGAC, nie tylko byc prawdziwa.

    Numer wiersza, numer kolumny i nazwa kolumny sa tym, co 6.A24 wprowadzila do
    komunikatu i czego nie ma zadna inna odmowa runnera. Test sprawdzajacy wylacznie
    kod wyjscia i nazwe pliku przechodzi takze wtedy, gdy odmowa mowi o czym innym —
    zmierzone, nie przewidziane.
    """
    sciezka = os.path.join(CTM.ROOT, "tests", "Sim.Tests", "RunnerCommandTests.cs")
    with open(sciezka, encoding="utf-8") as uchwyt:
        zrodlo = uchwyt.read()

    braki = []
    for nazwa, czesci in ASERCJE_ODMOWY_KOMORKI.items():
        cialo = _cialo_metody(zrodlo, nazwa)
        for czesc in czesci:
            if czesc not in cialo:
                braki.append((nazwa, czesc))
    assert braki == [], (
        "test odmowy komorki nie asercjonuje czesci komunikatu, ktora odroznia go od "
        "kazdej innej odmowy `compare` — przechodzilby takze dla odmowy o czym innym "
        "(6.A29, zmierzone kontrola KN-1 pozycji 6.A25): " + repr(braki))

    # Test drugiego kierunku ISTNIEJE i ma zostac. Bez tej asercji bramka wyzej
    # byłaby zielona takze wtedy, gdyby ktos usunal jedyny test sprawdzajacy, ze
    # dwa poprawne pliki nadal przechodza — a wtedy odmowa zbudowana zbyt szeroko
    # nie mialaby czego wywrocic.
    assert "public void " + TEST_DRUGIEGO_KIERUNKU + "(" in zrodlo, (
        "zniknal test drugiego kierunku rodziny 6.A24: " + TEST_DRUGIEGO_KIERUNKU)
    drugi = _cialo_metody(zrodlo, TEST_DRUGIEGO_KIERUNKU)
    assert "Assert.AreEqual(0," in drugi, (
        TEST_DRUGIEGO_KIERUNKU + " przestal zadac kodu 0")


def test_the_reader_of_test_bodies_is_not_matching_the_whole_file():
    """Kontrola przyrzadu z testu wyzej — WYKONANA, nie opisana.

    `_cialo_metody` wycina od naglowka metody do pierwszego `\\n    }`. Gdyby wycinal
    za duzo (do konca pliku), bramka wyzej bylaby zielona zawsze, bo `wiersz `,
    `kolumna ` i nazwy kolumn wystepuja w plikach gdzie indziej. Ten test mierzy, ze
    wycinek jest WEZSZY od pliku i ze nie niesie nazwy nastepnej metody.
    """
    sciezka = os.path.join(CTM.ROOT, "tests", "Sim.Tests", "RunnerCommandTests.cs")
    with open(sciezka, encoding="utf-8") as uchwyt:
        zrodlo = uchwyt.read()

    cialo = _cialo_metody(zrodlo, "Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy")
    assert len(cialo) < len(zrodlo) / 10, (
        "wycinek ciala metody ma %d znakow przy pliku %d — czytnik bierze za duzo"
        % (len(cialo), len(zrodlo)))
    assert "Numer_i_nazwa_kolumny_ida_z_pozycji_w_wierszu" not in cialo, (
        "wycinek siega do nastepnej metody: " + cialo[-200:])
    assert "speed_mps" not in cialo, (
        "wycinek niesie nazwe kolumny z INNEGO testu, wiec bramka wyzej mogłaby "
        "zaliczyc cudza asercje jako swoja")


# --- 6.D145: asercje C# BEZ KOMUNIKATU ------------------------------------------

#: Asercje bez komunikatu, per plik. **Zmierzone 11.09.2026: 1381 w 49 plikach**,
#: na 2593 wywolaniach asercji w obu katalogach testowych.
#:
#: Zapadka jest w OBIE strony, tak samo jak `NIEME_ASERCJE` po stronie Pythona: wpis
#: wolno obnizyc, podniesc nie wolno, a plik spoza listy ma miec zero. Dopisywanie
#: komunikatow do asercji C# stoi w polu „Poza zakresem" pozycji 6.D145 — ta lista
#: ma je najpierw POLICZYC.
BEZ_KOMUNIKATU = {
    "BrakingPropertyTests.cs": 1,
    "BrakingTests.cs": 63,
    "CabProtectionTests.cs": 18,
    "ChaseCameraAimTests.cs": 45,
    "ChunkManifestTests.cs": 13,
    "ClassicSignallingScenarioTests.cs": 1,
    "DesignAssumptionsTests.cs": 2,
    "DesignModelAuditTests.cs": 9,
    "DeterminismTests.cs": 2,
    "DoorCycleTests.cs": 31,
    "DriverActionsTests.cs": 1,
    "DriverNotchTests.cs": 21,
    "EmergencyBrakeTests.cs": 3,
    "EnergyAccountTests.cs": 23,
    "EnergyAndProfileTests.cs": 22,
    "FixedBlockTests.cs": 68,
    "InputLogTests.cs": 62,
    "LineBudgetTests.cs": 31,
    "LineCoreTests.cs": 44,
    "LineDriveTests.cs": 21,
    "LineRouteTests.cs": 14,
    "LineRunTests.cs": 28,
    "MovementAuthorityTests.cs": 30,
    "PlatformFitTests.cs": 13,
    "ProtectionModeTests.cs": 43,
    "ProvenanceSidecarTests.cs": 4,
    "ReferenceParityTests.cs": 8,
    "RouteDispatcherTests.cs": 24,
    "RunHeaderTests.cs": 11,
    "RunPlanTests.cs": 107,
    "RunResetTests.cs": 40,
    "RunnerCommandTests.cs": 126,
    "ScenarioDriveTests.cs": 35,
    "SceneAxisTests.cs": 10,
    "ServiceDayTests.cs": 31,
    "SignallingHudTests.cs": 15,
    "SignallingPlanTests.cs": 23,
    "SpeedProfileTests.cs": 29,
    "StationServiceTests.cs": 53,
    "StepAccumulatorTests.cs": 17,
    "StreamingPlanTests.cs": 30,
    "TelemetryTrackTests.cs": 33,
    "TrackAxisTests.cs": 41,
    "TractionAndResistanceTests.cs": 16,
    "TrainControllerTests.cs": 23,
    "TrainProtectionTests.cs": 41,
    "TrainViewLayoutTests.cs": 14,
    "UiTextTests.cs": 13,
    "ValidationTests.cs": 28,
}

#: Suma z listy wyzej, LICZONA, nie wpisana — z tego samego powodu, co po stronie
#: Pythona: wpisana recznie rozjechalaby sie przy pierwszym obnizonym wpisie.
BEZ_KOMUNIKATU_RAZEM = sum(BEZ_KOMUNIKATU.values())

#: Pozostale dwie klasy i calosc. **Trzy klasy sumuja sie do `ASERCJI_RAZEM`** i to
#: jest tu trescia: asercja, ktorej czytnik nie umie zaklasyfikowac, ma byc POLICZONA
#: jako nierozstrzygnieta, a nie wpasc miedzy klasy.
Z_KOMUNIKATEM_RAZEM = 1162
NIEROZSTRZYGNIETYCH = 72
ASERCJI_RAZEM = 2615


def _rozklad():
    """Rozklad zsumowany po obu katalogach testowych."""
    out = {CA.BEZ_KOMUNIKATU: 0, CA.Z_KOMUNIKATEM: 0, CA.NIEROZSTRZYGNIETE: 0, "razem": 0}
    for katalog in CA.CP.KATALOGI:
        for klucz, ile in CA.rozklad_komunikatow(katalog).items():
            out[klucz] += ile
    return out


def test_lista_asercji_C_bez_komunikatu_moze_tylko_malec():
    """Zapadka z obu stron, per plik — 6.D145.

    Bramka nie przechodzi pusta: pusty skan znaczy zepsute liczenie, a nie czyste
    drzewo. Ten sam powod i ten sam ksztalt, co `MINIMUM_METOD` wyzej.
    """
    w_drzewie = {}
    for katalog in CA.CP.KATALOGI:
        w_drzewie.update(CA.bez_komunikatu_per_plik(katalog))

    urosly = sorted((p, ile, BEZ_KOMUNIKATU[p]) for p, ile in w_drzewie.items()
                    if p in BEZ_KOMUNIKATU and ile > BEZ_KOMUNIKATU[p])
    assert not urosly, (
        "asercji bez komunikatu przybylo (plik, w drzewie, w zapadce): "
        + repr(urosly) + " — zapadka wolno obnizac, nie podnosic")

    spoza = sorted((p, ile) for p, ile in w_drzewie.items() if p not in BEZ_KOMUNIKATU)
    assert not spoza, (
        "plik spoza listy ma asercje bez komunikatu: " + repr(spoza)
        + " — nowy plik testowy C# zaczyna z komunikatem przy kazdej asercji")

    znikly = sorted(p for p in BEZ_KOMUNIKATU if p not in w_drzewie)
    assert not znikly, (
        "plik z listy nie ma juz ani jednej asercji bez komunikatu: " + repr(znikly)
        + " — zdejmij wpis w tym samym commicie, w ktorym dopisujesz komunikaty")

    spadly = sorted((p, w_drzewie[p], BEZ_KOMUNIKATU[p]) for p in BEZ_KOMUNIKATU
                    if p in w_drzewie and w_drzewie[p] < BEZ_KOMUNIKATU[p])
    assert not spadly, (
        "wpis stoi wyzej niz drzewo (plik, w drzewie, w zapadce): " + repr(spadly)
        + " — obniz go w tym samym commicie")


def test_trzy_klasy_sumuja_sie_do_calosci_i_zadna_nie_gubi_sie_po_cichu():
    """Suma jest tu trescia: asercja niezaklasyfikowana ma byc WIDOCZNA — 6.D145.

    Gdyby czytnik po cichu gubil wywolania, ktorych nie rozumie, zapadka na same
    „bez komunikatu" spadalaby razem z jego niewiedza i czytalaby sie jako postep.
    """
    r = _rozklad()
    assert r["razem"] == ASERCJI_RAZEM, (
        "wywolan asercji jest %d, a pomiar z 11.09.2026 dal %d"
        % (r["razem"], ASERCJI_RAZEM))
    assert r[CA.BEZ_KOMUNIKATU] == BEZ_KOMUNIKATU_RAZEM, (
        "suma z drzewa %d, suma z listy %d"
        % (r[CA.BEZ_KOMUNIKATU], BEZ_KOMUNIKATU_RAZEM))
    assert r[CA.Z_KOMUNIKATEM] == Z_KOMUNIKATEM_RAZEM, (
        "asercji Z komunikatem jest %d zamiast %d"
        % (r[CA.Z_KOMUNIKATEM], Z_KOMUNIKATEM_RAZEM))
    assert r[CA.NIEROZSTRZYGNIETE] == NIEROZSTRZYGNIETYCH, (
        "asercji nierozstrzygnietych jest %d zamiast %d — klasa, ktorej czytnik nie "
        "umie rozstrzygnac, ma byc policzona, a nie schowana"
        % (r[CA.NIEROZSTRZYGNIETE], NIEROZSTRZYGNIETYCH))
    assert (BEZ_KOMUNIKATU_RAZEM + Z_KOMUNIKATEM_RAZEM + NIEROZSTRZYGNIETYCH
            == ASERCJI_RAZEM), (
        "trzy klasy nie sumuja sie do calosci: %d + %d + %d != %d"
        % (BEZ_KOMUNIKATU_RAZEM, Z_KOMUNIKATEM_RAZEM, NIEROZSTRZYGNIETYCH,
           ASERCJI_RAZEM))


def test_tabela_arnosci_zna_kazda_asercje_z_drzewa():
    """Nazwa spoza tabeli przechodzilaby przez czytnik NIEPOLICZONA — 6.D145."""
    for katalog in CA.CP.KATALOGI:
        obce = CA.nazwy_spoza_tabeli(katalog)
        assert obce == [], (
            "w " + katalog + " stoi asercja, ktorej `OBOWIAZKOWE_ARGUMENTY` nie zna: "
            + repr(obce) + " — dopisz jej arnosc, bo inaczej czytnik ja POMIJA, "
            "a zapadka spada razem z jego niewiedza")


def _klasa_wejscia(kod, nazwa="Assert.AreEqual"):
    """Klasa asercji z wejscia syntetycznego — jedna droga dla wszystkich kontrol."""
    maska = CTM.maska(kod)
    dopasowanie = CA.WYWOLANIE.search(maska)
    args = CA.CP.argumenty_z_nawiasami(maska, dopasowanie.end())
    return CA.klasa_komunikatu(nazwa, args, kod)


def test_tolerancja_jako_trzeci_argument_NIE_jest_komunikatem():
    """Pole „Skonczone, gdy" 6.D145 zada tego wprost — na wejsciu syntetycznym.

    Na drzewie obie wersje czytnika daja te sama zielen: `Assert.AreEqual(a, b, 1e-9)`
    i `Assert.AreEqual(a, b, "powod")` roznia sie TYPEM trzeciego argumentu, a nie
    liczba przecinkow. Czytnik liczacy przecinki zaliczylby tolerancje jako komunikat
    i zapadka spadlaby o 265 pozycji bez ani jednego dopisanego zdania.
    """
    assert _klasa_wejscia('Assert.AreEqual(1.0, x, 1e-9);') == CA.BEZ_KOMUNIKATU, (
        "tolerancja jako trzeci argument policzona jako komunikat")
    assert _klasa_wejscia('Assert.AreEqual(1.0, x, 0.0);') == CA.BEZ_KOMUNIKATU, (
        "tolerancja zapisana jako `0.0` policzona jako komunikat — a takich w drzewie "
        "jest najwiecej (6.D141)")
    assert _klasa_wejscia('Assert.AreEqual(1.0, x, 1e-9, "powod");') == CA.Z_KOMUNIKATEM, (
        "czwarty argument JEST komunikatem, gdy trzeci jest tolerancja")
    assert _klasa_wejscia('Assert.AreEqual(1.0, x, "powod");') == CA.Z_KOMUNIKATEM, (
        "trzeci argument bedacy literalem napisowym jest komunikatem")
    assert _klasa_wejscia('Assert.AreEqual(1.0, x);') == CA.BEZ_KOMUNIKATU, (
        "dwa argumenty to sama asercja, bez miejsca na komunikat")
    assert _klasa_wejscia('Assert.AreEqual(1.0, x, tol);') == CA.NIEROZSTRZYGNIETE, (
        "wyrazenie w pozycji tolerancji jest NIEROZSTRZYGNIETE — `tol` moze byc "
        "liczba albo napisem, a typu bez sprawdzacza typow nie widac")

    # Wszedzie POZA rodzina `AreEqual` MSTest ma w tej pozycji wylacznie `string`,
    # wiec wyrazenie, ktore sie kompiluje, jest tam komunikatem — i nie zgadujemy.
    assert _klasa_wejscia('Assert.IsTrue(x, opis);', "Assert.IsTrue") == CA.Z_KOMUNIKATEM, (
        "`Assert.IsTrue(x, opis)` ma jedyne przeciazenie z `string message` — "
        "nierozstrzygniete byloby tu nadmiarowa ostroznoscia")
    assert _klasa_wejscia('Assert.IsTrue(x);', "Assert.IsTrue") == CA.BEZ_KOMUNIKATU, (
        "jeden argument to sama asercja")
    assert _klasa_wejscia('Assert.Fail("powod");', "Assert.Fail") == CA.Z_KOMUNIKATEM, (
        "`Assert.Fail` nie ma argumentow obowiazkowych, wiec pierwszy JEST komunikatem")


def test_literal_kolekcji_nie_rozbija_argumentow_na_przecinkach():
    """Ciecie po samych nawiasach okraglych psuloby ten ksztalt — 6.D145.

    `CollectionAssert.AreEqual(new[] { "a", "b" }, x, "powod")` ma trzy argumenty,
    a nie piec. Zmierzone: na drzewie roznica miedzy cieciem po nawiasach okraglych
    a po wszystkich dotyczy **28** wywolan i wszystkie sa `CollectionAssert.*`.
    """
    kod = 'CollectionAssert.AreEqual(new[] { "a", "b" }, x, "powod");'
    maska = CTM.maska(kod)
    dopasowanie = CA.WYWOLANIE.search(maska)
    po_wszystkich = CA.CP.argumenty_z_nawiasami(maska, dopasowanie.end())
    po_okraglych = CA.CP.argumenty(maska, dopasowanie.end())

    assert len(po_wszystkich) == 3, (
        "literal kolekcji rozbil argumenty: %d zamiast 3" % len(po_wszystkich))
    assert len(po_okraglych) == 4, (
        "kontrola przyrzadu: ciecie po samych nawiasach okraglych ma dac 4 (przecinek "
        "w klamrach dzieli je na `new[] { \"a\"` i `\"b\" }`) — jesli daje %d, obie "
        "funkcje robia to samo i jedna z nich jest zbedna" % len(po_okraglych))
    assert CA.klasa_komunikatu("CollectionAssert.AreEqual", po_wszystkich,
                               kod) == CA.Z_KOMUNIKATEM, (
        "komunikat za literalem kolekcji przestal byc widoczny")


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

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
    # 44 -> 43 (14.09.2026, MB-07): zapadka SCHODZI, bo trzy testy przypinające zator
    # zostały przepisane i jedna asercja bez komunikatu z nich zniknęła. Ta lista może
    # tylko maleć i to jest jej cała treść — wpis podniesiony byłby cichym przyzwoleniem
    # na asercję, która nie mówi, co jest nie tak.
    "LineCoreTests.cs": 43,
    # 21 -> 29 (24.09.2026): końcowy postój Merode i ślad po ograniczeniu osi.
    # 29 -> 23 (24.09.2026): sze?? nowych asercji postoju dosta?o opisy.
    "LineDriveTests.cs": 23,
    "LineRouteTests.cs": 14,
    "LineRunTests.cs": 28,
    "MovementAuthorityTests.cs": 30,
    "PlatformFitTests.cs": 13,
    "ProtectionModeTests.cs": 43,
    "ProvenanceSidecarTests.cs": 4,
    "ReferenceParityTests.cs": 8,
    "RouteDispatcherTests.cs": 24,
    "RunHeaderTests.cs": 11,
    "RunPlanTests.cs": 109,
    "RunResetTests.cs": 40,
    "RunnerCommandTests.cs": 126,
    "ScenarioDriveTests.cs": 35,
    # 10 -> 11 (24.09.2026): oprawa nie wykracza za zmierzoną scenerię.
    "SceneAxisTests.cs": 11,
    "ServiceDayTests.cs": 31,
    "SignallingHudTests.cs": 21,
    "SignallingPlanTests.cs": 23,
    "SpeedProfileTests.cs": 29,
    "StationServiceTests.cs": 53,
    "StepAccumulatorTests.cs": 17,
    "StreamingPlanTests.cs": 30,
    "TelemetryTrackTests.cs": 33,
    # Koniec osi: sześć dokładnych porównań stanu bez opisów w nowym teście.
    "TrackEndStopTests.cs": 6,
    "TrackAxisTests.cs": 41,
    "TractionAndResistanceTests.cs": 16,
    "TrainControllerTests.cs": 23,
    "TrainProtectionTests.cs": 41,
    "TrainViewLayoutTests.cs": 14,
    "UiTextTests.cs": 12,
    "ValidationTests.cs": 28,
}

#: Suma z listy wyzej, LICZONA, nie wpisana — z tego samego powodu, co po stronie
#: Pythona: wpisana recznie rozjechalaby sie przy pierwszym obnizonym wpisie.
BEZ_KOMUNIKATU_RAZEM = sum(BEZ_KOMUNIKATU.values())

#: Pozostale dwie klasy i calosc. **Trzy klasy sumuja sie do `ASERCJI_RAZEM`** i to
#: jest tu trescia: asercja, ktorej czytnik nie umie zaklasyfikowac, ma byc POLICZONA
#: jako nierozstrzygnieta, a nie wpasc miedzy klasy.
#:
#: **1307 -> 1419 i 2756 -> 2868 (13.09.2026, MB-02), z powodem.** Doszly 112 asercji
#: w `TrainingSessionTests.cs` (17 testow), `RunSummaryTests.cs` (6 testow)
#: i `TrainingWiringTests.cs` (5 testow),
#: **wszystkie z komunikatem**: `BEZ_KOMUNIKATU_RAZEM` nie drgnelo ani o jeden, bo
#: dwa nowe pliki nie maja w tabeli wyzej wpisu i miec go nie moga — nowy plik testowy
#: C# zaczyna z komunikatem przy kazdej asercji. Ta bramka zapalila sie pierwsza
#: w tym commicie, na 43 asercjach bez powodu, i wszystkie 43 dostaly powod.
#: `NIEROZSTRZYGNIETYCH` bez zmian: czytnik zaklasyfikowal kazda z 112.
#:
#: **1419 -> 1433 i 2868 -> 2882 (14.09.2026, MB-03).** Czternascie asercji
#: w `TractionBlockTests.cs` (4 metody), wszystkie Z KOMUNIKATEM —
#: `BEZ_KOMUNIKATU_RAZEM` znow nie drgnelo.
#:
#: **1438 -> 1453 i 2887 -> 2902 (14.09.2026, MB-05).** Pietnascie asercji
#: w `CabPlacementTests.cs` (6 metod), wszystkie Z KOMUNIKATEM —
#: `BEZ_KOMUNIKATU_RAZEM` znow nie drgnelo, `NIEROZSTRZYGNIETYCH` tez nie.
#: Trzy z tych metod czytaja ZRODLO, a nie licza — i to nie jest wybor stylu:
#: trzy kontrole negatywne na trzech metodach arytmetycznych tego samego pliku
#: wyszly ZIELONE, bo mutacje siedza w wezlach Godota, ktorych `dotnet test`
#: nie powola.
#:
#: **1453 -> 1475 i 2902 -> 2924 (14.09.2026, audyt bramki MB-05).** Dwadziescia dwie
#: asercje, wszystkie Z KOMUNIKATEM — `BEZ_KOMUNIKATU_RAZEM` i `NIEROZSTRZYGNIETYCH`
#: znow nie drgnely. Powod jest pomiarem, nie rozbudowa: bramka leksykalna dolozona
#: wyzej byla TAUTOLOGICZNA. Zmierzone na starym kodzie — cztery mutacje dajace te
#: sama usterke 0,700 m (`_train.LengthM` -> `_cabView.LengthM`; `+ 0.7` w argumencie
#: wywolania; `+ 0.7` w ciele `CabView.PlaceAt`; cale wywolanie owiniete w `if`)
#: przechodzily **292/292 kazda**. Tautologia byla przy tym w JEDNEJ metodzie, a nie
#: w calym pliku, i ta roznica jest tu trescia, a nie niuansem: podmiana bryl kabiny
#: na `(-999, -998)` dawala bez filtra `290/292` (dwie inne metody ja lapaly), ale
#: `--filter Ta_sama_wspolrzedna_X_daje_ten_sam_kilometraz_w_obu_zbiorach` dawal
#: `1/1 przeszlo` — ta metoda liczyla OBIE strony rownosci tym samym wyrazeniem na
#: tych samych brylach. Po przepisaniu kazda z czterech mutacji daje jedna czerwien,
#: ta sama tautologia pod tym samym filtrem `1 failed`, a bez filtra cztery. Cztery
#: nowe metody testowe (6 -> 10) i piny na CALA liste argumentow zamiast na token
#: w niej — `Contains("trainLength")` bylo prawda takze dla
#: `chainage - trainLength + 0.7`.
#:
#: **1475 -> 1513 i 2924 -> 2962 (14.09.2026, MB-06).** Ten wpis stoi OBOK wpisu
#: wyzej, a nie zamiast niego: MB-06 i audyt bramki MB-05 to dwie rozlaczne zmiany,
#: ktore spotkaly sie dopiero przy scalaniu, i obie liczby sa PRZELICZONE na wspolnym
#: drzewie, a nie zsumowane w glowie. Dwadziescia siedem asercji w `ControlOwnerTests.cs`
#: (11 metod), wszystkie Z KOMUNIKATEM — ale nie od razu: bramka
#: `test_lista_asercji_C_bez_komunikatu_moze_tylko_malec` zapalila sie na PIECIU
#: asercjach tego pliku bez komunikatu, w tym dwoch `Assert.ThrowsException`, ktore
#: latwo przeoczyc, bo komunikat jest w nich argumentem DRUGIM po lambdzie. Dopisane,
#: a nie wpisane na liste wyjatkow. Do tego jedenascie asercji poprawki dziury
#: w ochronie: cztery testy galezi postoju, ktorych ta pozycja najpierw NIE miala
#: (i dlatego wpuscila komende czlowieka do kontrolera z pominieciem ochrony), plus
#: dwa straznik dolozone tam, gdzie audyt znalazl tozsamosci. `BEZ_KOMUNIKATU_RAZEM`
#: i `NIEROZSTRZYGNIETYCH` znow nie drgnely.
#: **2962 -> 2963 (14.09.2026, MB-07).** Bilans trzech przepisanych testów
#: `LineCoreTests.cs`, które przypinały ZATOR: asercji przybyło o jedną netto,
#: a `Z_KOMUNIKATEM_RAZEM` nie drgnęło, bo wszystkie mają komunikat.
#: **1519/2966 -> ?/? (14.09.2026, MB-08) — i obie liczby są PRZELICZONE na drzewie
#: PO scaleniu audytu MB-06 (#605), a nie zsumowane z dwóch gałęzi.** Gałąź MB-08
#: wyszła z `0ae0acf`, gdzie stało 1519/2966; audyt MB-06 podniósł te same stałe
#: niezależnie, do 1521/2968. Zsumowanie przyrostów dałoby liczbę, której nie ma
#: w żadnym drzewie — to jest dokładnie ten rozjazd, przed którym ostrzega wpis audytu
#: wyżej, i dlatego wartości niżej pochodzą z przebiegu na scalonym drzewie.
#:
#: Sto dwadzieścia pięć asercji MB-08 w trzech nowych plikach testowych
#: (`ManualDoorsTests`, `ManualDoorsOnLineTests`, `DoorPromptTests`) i w bramce
#: leksykalnej `HandleTrainKeysGateTests` — **wszystkie z komunikatem**,
#: `BEZ_KOMUNIKATU_RAZEM` i `NIEROZSTRZYGNIETYCH` nie drgnęły. Ale nie od razu:
#: `test_lista_asercji_C_bez_komunikatu_moze_tylko_malec` zapaliła się na **54**
#: asercjach bez komunikatu (4 + 15 + 35) i komunikaty zostały DOPISANE, a pliki nie
#: trafiły na listę wyjątków. Ta sama pomyłka co przy MB-06, o rząd wielkości większa,
#: i z tego samego powodu: pisząc nowy plik testowy łatwo przyjąć, że komunikat jest
#: potrzebny tylko tam, gdzie asercja „może być niejasna".
#: **1646 -> 1652 (14.09.2026, 6.D210)** — te same sześć asercji, co przy
#: `ASERCJI_RAZEM` niżej. Wszystkie z komunikatem od pierwszego przebiegu: przy
#: MB-08 ta sama bramka złapała 54 asercje bez komunikatu i lekcja weszła.
#: **1652 -> 1667 (14.09.2026, 6.D211)** — te same piętnaście asercji, co przy
#: `ASERCJI_RAZEM` niżej, wszystkie z komunikatem.
#: **1667 -> 1675 (15.09.2026, 6.D212)** — te same osiem asercji, co przy
#: `ASERCJI_RAZEM` niżej, wszystkie z komunikatem.
#: **1675 -> 1682 (15.09.2026, 6.D213)** — te same siedem asercji, co przy
#: `ASERCJI_RAZEM` niżej, wszystkie z komunikatem.
#: **1682 -> 1690 (15.09.2026, 6.D214)** — te same osiem asercji, co przy
#: `ASERCJI_RAZEM` niżej, wszystkie z komunikatem.
#: **1690 -> 1696 (15.09.2026, 6.D215)** — szesc z siedmiu nowych asercji ma
#: komunikat; siodma sklada go ze zbioru, ktory porownuje.
#: **1708 -> 1723 (15.09.2026, 6.D224)** — te same pietnascie asercji, co przy
#: `ASERCJI_RAZEM` nizej, wszystkie z komunikatem.
#: **1723 -> 1732 (17.09.2026, 6.D231)** — te same dziewiec asercji, co przy
#: `ASERCJI_RAZEM` nizej, wszystkie z komunikatem.
#: **1732 -> 1741 (17.09.2026, 6.D229)** — dziewiec asercji bramki
#: `tests/Sim.Tests/BrokenJsonRefusalTests.cs`, wszystkie z komunikatem, wiec obie
#: stale rusza sie o tyle samo.
# 1756 -> 1743 (17.09.2026, 6.D257): te same TRZYNASCIE asercji co przy `ASERCJI_RAZEM`
# — wszystkie mialy komunikat (`"nie znaleziono korzenia repozytorium"` albo
# `"Test uruchomiony poza drzewem repozytorium."`), wiec ubywaja z obu liczb naraz.
# Przeliczone z drzewa.
# 1743 -> 1750 (17.09.2026, 6.D260): SIEDEM asercji z komunikatem dokladanych przez
# kontrole przyrzadu czytnika lancuchow w `UiTextTests.cs`. Wszystkie SIEDEM ma
# komunikat, wiec obie zapadki — ta i `ASERCJI_RAZEM` — rosna o tyle samo.
# 1750 -> 1770 (22.09.2026, 6.M2): DWADZIESCIA asercji `StopWindowParityTests.cs`,
# wszystkie z komunikatem — obie zapadki rosna o tyle samo.
# 1770 -> 1787 (22.09.2026, 6.D235): SIEDEMNASCIE asercji, wszystkie z komunikatem.
# 1787 -> 1792 (23.09.2026, 6.D365): te same PIEC asercji, wszystkie z komunikatem; ZMIERZONE.
# 1792 -> 1829 (23.09.2026, 6.M1): TRZYDZIESCI SIEDEM asercji z komunikatem —
# `LineReplayTests.cs` i nowy test `RunPlanTests.cs` oraz dwie asercje, ktore
# dostaly komunikat. Przeliczone z drzewa.
# 1829 -> 1842 (23.09.2026, 6.M3): TRZYNASCIE asercji, wszystkie z komunikatem.
# 1842 -> 1850 (23.09.2026, 6.D357): OSIEM asercji `BrokenJsonRefusalTests.cs`,
# wszystkie z komunikatem — obie zapadki rosna o tyle samo; ZMIERZONE.
# 1850 -> 1865 (23.09.2026, 6.D356): PIETNASCIE asercji `BrokenJsonRefusalTests.cs`,
# wszystkie z komunikatem — obie zapadki rosna o tyle samo; ZMIERZONE.
# 1865 -> 1874 (23.09.2026, tunel): dziewiec nowych asercji z komunikatem.
# 1874 -> 1886 (24.09.2026, door-prompt-service): dwanascie asercji w
# `DoorPromptTests.cs` i `HudLayoutTests.cs`, kazda z komunikatem; ZMIERZONE.
# 1886 -> 1896 (24.09.2026, braking cue): dziesiec asercji wskazowki hamowania.
# 1896 -> 1901 (24.09.2026, PR #771): piec asercji krawedzi peronu z komunikatem.
# 1901 -> 1903 (24.09.2026, kamera): dwie kontrole koncow osi.
# 1903 -> 1915 (24.09.2026, dwustopniowe cue): dwanascie asercji z komunikatem.
# 1915 -> 1920 (24.09.2026, S): piec kontroli natychmiastowego wygaszenia.
# 1920 -> 1925 (24.09.2026, oznaczenia stacji): piec asercji pelnej nazwy
# i polozenia znacznikow, wszystkie z komunikatem; zmierzone z drzewa.
# 1925 -> 1939 (24.09.2026, pamiec cue): czternascie asercji testow fazy.
# 1939 -> 1947 (24.09.2026, autopilot E): osiem asercji z komunikatem.
# 1947 -> 1950 (24.09.2026, HUD 800x600): trzy asercje zachowania pozycji.
# 1950 -> 1966 (24.09.2026, wybór składu i HUD): 17 nowych kontroli N/T,
# jedna mniej po scaleniu dwóch sprawdzeń pełnego wiersza pozycji.
# 1966 -> 1973 (24.09.2026, interaktywne R): siedem kontroli zakończenia,
# wszystkie z komunikatem.
# 1973 -> 1977 (24.09.2026, automat bez sygnalizacji): cztery asercje
# strażnika BrakingCue, każda z komunikatem.
# 1977 -> 1978 (24.09.2026, widok chase 800x600): jedna asercja zawijania View.
# 1978 -> 1982 (24.09.2026, krótki HUD chase): cztery granice z opisem.
# 1982 -> 1995 (24.09.2026, tablice na dojeździe i pomoc linii):
# trzynaście kontroli z komunikatami; trzy nowe komunikaty dopisano przy scaleniu.
# 1995 -> 1997 (24.09.2026, mocowania tablic): obie asercje opisują sens błędu.
# 1997 -> 2010 (24.09.2026, wejście składu od wskazanej stacji):
# trzynaście nowych asercji opisuje także blokadę drugiego składu i dojazd.
# 2010 -> 2025 (24.09.2026, T-320): osiem asercji planu wejść i siedem
# kontroli ciągłości obiegów ma komunikaty.
# 2025 -> 2035 (24.09.2026, T-320): dziesięć kontroli bramki wjazdu.
# 2035 -> 2040 (24.09.2026, T-320): pięć kontroli chronologii obiegu.
# 2040 -> 2049 (24.09.2026, T-320): dziewięć asercji wykrywania pominiętych kursów.
# 2049 -> 2054 (24.09.2026, T-320): walidacja dnia służby i godziny po północy.
# 2054 -> 2063 (24.09.2026, koniec osi linii): dziewięć opisanych kontroli
# postoju Merode i opraw scenerii.
# 2063 -> 2077 (24.09.2026, dwa wjazdy rozkładowe): czternaście kontroli
# ma teraz jawne komunikaty, także sześć porównań początkowo bez opisu.
# Po integracji dyspozytora i hamowania: 2133 opisane asercje, zmierzone w drzewie.
# 2077 -> 2144 (24.09.2026, integracja dyspozytora, test granicy, hamowanie i metadane).
# Równoległy pomiar gałęzi obserwacji:
# 2144 -> 2173 (24.09.2026, nowe testy sceny i adaptera rozkladu).
# 2173 -> 2179 (24.09.2026, krok wjazdu i pozycja kabiny).
# 2179 -> 2198 (25.09.2026, obserwacja czynnych składów): dziewiętnaście
# asercji w dwóch testach ma jawne komunikaty; klasy bez opisu nie rosną.
# Równoległy pomiar gałęzi podglądu łącznika:
# Równoległa gałąź miała pomiary 2144 → 2148 i 2148 → 2183.
# 2198 -> 2202 (25.09.2026, integracja obserwacji i podglądu łącznika).
# 2202 -> 2206 (25.09.2026, nastawnik): cztery asercje przejścia przez neutral.
# 2206 -> 2209 (25.09.2026, tablice stacyjne): trzy kontrole z komunikatami.
# 2209 -> 2216 (25.09.2026, asercje odcisku i drugiego składu z komunikatami).
# 2216 -> 2220 (25.09.2026, odcisk taktu pytań nastawni).
# 2220 -> 2223 (25.09.2026, AZERTY): trzy asercje pary W/Z mają komunikaty.
# 2223 -> 2232 (25.09.2026, T-400 ATP): wszystkie dziewięć nowych asercji ma komunikat.
# 2232 -> 2233 (25.09.2026, T-400 platform): mapowanie widoku z komunikatem.
# 2233 -> 2240 (25.09.2026, T-400 platform): siedem kontroli obrysu z komunikatem.
# 2240 -> 2247 (25.09.2026, T-400 stop target): all seven new assertions explain the failure.
# 2247 -> 2250 (25.09.2026, T-400 stop target): three active-track placement checks.
# 2250 -> 2258 (25.09.2026, T-400 outcome): lifecycle assertions explain each transition.
# 2258 -> 2263 (25.09.2026, T-400 outcome): cab cue lifecycle assertions.
# 2263 -> 2265 (25.09.2026, liczność przypisań HUD i tablicy STOP).
# 2265 -> 2268 (26.09.2026, trzy asercje FirstRunSceneContractTests).
# 2268 -> 2276 (26.09.2026, osiem asercji kompletności chunków).
# 2276 -> 2284 (26.09.2026, osiem komunikatów w teście wykończeń stacji).
Z_KOMUNIKATEM_RAZEM = 2284
NIEROZSTRZYGNIETYCH = 69
#: **3093 -> 3099 (14.09.2026, 6.D210).** Sześć asercji nowego pliku
#: `tests/Sim.Tests/DefaultArmAuditTests.cs` — bramki na ramionach domyślnych
#: switchy `src/Sim/`. Wszystkie z komunikatem, więc `Z_KOMUNIKATEM_RAZEM` rośnie
#: o tyle samo, a `BEZ_KOMUNIKATU_RAZEM` i `NIEROZSTRZYGNIETYCH` nie drgają.
#: **3099 -> 3114 (14.09.2026, 6.D211).** Piętnaście asercji bramki na POŁYKANYCH
#: członach ramion domyślnych, dopisanej do `tests/Sim.Tests/DefaultArmAuditTests.cs`:
#: osiem w bramce drzewa, cztery w kontroli przyrządu na wejściu syntetycznym,
#: trzy w pomocnikach czytających korpus metody. Wszystkie z komunikatem, więc
#: `Z_KOMUNIKATEM_RAZEM` rośnie o tyle samo, a `BEZ_KOMUNIKATU_RAZEM`
#: i `NIEROZSTRZYGNIETYCH` nie drgają.
#: **3114 -> 3122 (15.09.2026, 6.D212).** Osiem asercji kontroli przyrządu
#: czytnika wyliczeń w `tests/Game.Tests/UiTextTests.cs`: cztery żądają, żeby czytnik
#: MASKUJĄCY nie dał się nabrać na `enum` w komentarzu ani w literale, i cztery — żeby
#: czytnik SUROWY dał się nabrać na trzech próbkach, a na czwartej nie. Bez tej drugiej
#: czwórki zieleń mówiłaby tyle, co czytnik, który ją wypisał: rozjazd w drzewie wynosi
#: dziś ZERO. Wszystkie z komunikatem, `BEZ_KOMUNIKATU_RAZEM` i `NIEROZSTRZYGNIETYCH`
#: nie drgają.
#: **3122 -> 3129 (15.09.2026, 6.D213).** Siedem asercji bramki na `.ToString()`
#: w RDZENIU, w `tests/Game.Tests/UiTextTests.cs`: cztery w bramce drzewa (podłoga
#: na liczbę plików, podłoga na liczbę wywołań, zbiór nazw dwuznacznych, zero
#: wywołań na wyliczeniu) i trzy w kontroli przyrządu — po jednej na każde
#: z trzech podstawień, w tym na to, przy którym sito jest ŚLEPE. Wszystkie
#: z komunikatem; `BEZ_KOMUNIKATU_RAZEM` i `NIEROZSTRZYGNIETYCH` nie drgają.
#: **3129 -> 3137 (15.09.2026, 6.D214).** Osiem asercji bramki na zgłoszeniach
#: URWANYCH i jej kontroli przyrządu: dwie w bramce drzewa (podłoga na liczbę
#: zgłoszeń, zero zgłoszeń z kropką na brzegu) i sześć w kontroli — po parze na
#: indeksator, nawias okrągły i nawiasy ZAGNIEŻDŻONE, czyli na granicę, która
#: zostaje. Wszystkie z komunikatem.
#: **3137 -> 3143 (15.09.2026, 6.D215).** Szesc asercji bramki na galezi
#: surowy-czy-werbatim: dwie w petli po czterech postaciach (tresc literalu
#: i kod po masce), jedna na liczbe obrotow petli, jedna na ZBIOR przedrostkow
#: i dwie w bramce o jednym miejscu warunku.
#: **3143 -> 3155 (15.09.2026, 6.D217).** Dwanascie asercji bramki na DRODZE BLEDU
#: w `tests/Game.Tests/UiTextTests.cs`: piec w bramce jezyka (kontrola przyrzadu
#: „lista zawiera `Abort`", liczba wolajacych, liczba wypisow poza `Abort`, jezyk
#: kazdego komunikatu, podloga na liczbe komunikatow ze slowami), cztery w bramce
#: rozdzielajacej zrodla tekstu obcego od wlasnego (liczba dziur obcych, ZBIOR
#: wytworcow, obecnosc kazdego zrodla wlasnego, suma obu list) i trzy w bramce
#: o wytworcy komunikatu bez wlasnych slow (liczba wolajacych `RunPlan.Refusal`,
#: podloga na literaly `[ARGUMENT]`, jezyk kazdego). Wszystkie z komunikatem;
#: `BEZ_KOMUNIKATU_RAZEM` i `NIEROZSTRZYGNIETYCH` nie drgaja.
#: **3155 -> 3170 (15.09.2026, 6.D224).** Pietnascie asercji bramki na DRUGIEJ
#: slepej plamce sita rdzenia, w `tests/Game.Tests/UiTextTests.cs`: jedenascie
#: w bramce drzewa (podloga na liczbe plikow, rownosc „surowo == po masce",
#: niezerowa liczba slow `var`, a dalej po cztery na kazdy wpis wykazu — liczba pol,
#: obecnosc pliku, obecnosc typu w zbiorze wyliczen i DOKLADNIE JEDNO trafienie
#: wzorca deklaracji — plus zbior czytelny wzorcem, liczba NAKLADANIA sie obu plamek,
#: zbior pozycji poza pierwsza plamka i zero wywolan `.ToString()`) oraz cztery
#: w kontroli przyrzadu: sito SLEPE na typ wnioskowany, sito WIDZACE ten sam kod
#: z typem jawnym, czytnik rozpoznajacy `var nazwa = Wyliczenie.Czlon` i granica,
#: na ktorej ten czytnik milczy, bo inicjalizatorem jest wywolanie. Wszystkie
#: z komunikatem; `BEZ_KOMUNIKATU_RAZEM` i `NIEROZSTRZYGNIETYCH` nie drgaja.
#: **3170 -> 3179 (17.09.2026, 6.D231).** Dziewiec asercji kontroli przyrzadu
#: czytnika korpusu w `tests/Sim.Tests/DefaultArmAuditTests.cs`: piec na ODMOWIE
#: metodzie WYRAZENIOWEJ (straz `deklaracji == 1` nadal SPELNIONA, zwrot `null`,
#: powod niepusty, powod NAZYWA ksztalt ciala, powod nie niesie cudzej tresci)
#: i cztery na kontroli DODATNIEJ, czyli na sasiadce KLAMROWEJ, ktorej korpus
#: czytnik podstawial pod tamto pytanie: jedna deklaracja, brak powodu odmowy,
#: zwrot niepusty i tresc WLASNA. Bez tej czworki bramka zapalalaby sie tak samo
#: na kodzie poprawnym (6.D27). Wszystkie z komunikatem, wiec
#: `Z_KOMUNIKATEM_RAZEM` rosnie o tyle samo, a `BEZ_KOMUNIKATU_RAZEM`
#: i `NIEROZSTRZYGNIETYCH` nie drgaja.
#: **3179 -> 3188 (17.09.2026, 6.D229).** Dziewiec asercji bramki na odmowie przy
#: ZEPSUTEJ SKLADNI JSON-a: cztery po parach loader x ksztalt (oczekiwany
#: `FormatException`, zgodnosc z filtrem `Sim.Runner:247`, zgodnosc z filtrem
#: `FirstRun:1034`, PODLOGA na liczbe przejrzanych par), cztery na jezyku odmowy
#: i jedna na tym, ze powod parsera zostaje jako `InnerException`.
#: **Liczba jest PRZELICZONA z drzewa po scaleniu, a nie zlozona z dwoch stron:**
#: galaz 6.D229 mierzyla baze 3170 i dawala 3179, a `main` po 6.D231 mial ROWNIEZ
#: 3179 — obie strony podawaly TE SAMA liczbe o ROZNYCH zbiorach asercji, czyli
#: dokladnie ten uklad, ktory przy `MIN_REPORTS` opisano jako czyste scalenie
#: o blednej sumie. Drzewo scalone ma 3188.
#: 3203 -> 3190 (17.09.2026, 6.D257): TRZYNASCIE asercji znika razem z DZIEWIETNASTOMA
#: wlasnymi petlami szukania korzenia, zastapionymi jednym pomocnikiem
#: `tests/Shared/KorzenRepozytorium.cs`. Cztery to `Assert.IsNotNull(katalog, …)`
#: z kopii na markerze `MetroBxl.sln`, reszta to `Assert.Inconclusive(…)` z kopii na
#: markerze `CLAUDE.md`. Pomocnik NIE wola `Assert` — brak korzenia nie jest
#: niespelnionym oczekiwaniem testu, tylko niemozliwym do przeprowadzenia przebiegiem,
#: a plik bez zaleznosci od frameworka wchodzi do obu projektow tak samo. Ubytek jest
#: wiec TRESCIA tej pozycji, nie kosztem. **Liczba kopii ZMIERZONA, nie wzieta z opisu:
#: pozycja mowila o CZTERECH, w drzewie stalo DZIEWIETNASCIE.** Przeliczone z drzewa.
# 3190 -> 3197 (17.09.2026, 6.D260): SIEDEM asercji dokladanych przez kontrole
# przyrzadu `Czytnik_lancucha_odpowiada_o_TEJ_stalej_i_tylko_o_dawnych_wartosciach`
# w `UiTextTests.cs` — trzy postaci odpowiedzi i trzy przypadki, w ktorych czytnik
# ma milczec (dzisiejsza wartosc, liczba spoza lancucha, cudza stala).
# 3197 -> 3217 (22.09.2026, 6.M2): DWADZIESCIA asercji `StopWindowParityTests.cs`,
# kazda z komunikatem. Przeliczone z drzewa.
# 3217 -> 3234 (22.09.2026, 6.D235): SIEDEMNASCIE asercji `FileReadGuardTests.cs`
# i `BadFileTests.cs`. Przeliczone z drzewa.
# 3234 -> 3239 (23.09.2026, 6.D365): PIEC asercji testow kultury — jedna w
# `TrainingSessionTests.cs` (przecinek pl-PL) i cztery w `DoorCycleTests.cs`; ZMIERZONE.
# 3239 -> 3275 (23.09.2026, 6.M1): TRZYDZIESCI SZESC asercji — `LineReplayTests.cs`
# i nowy test `RunPlanTests.cs`, minus jedna zdjeta z `ReplayRefusesASecondSourceOfCommand`.
# Przeliczone z drzewa.
# 3275 -> 3288 (23.09.2026, 6.M3): TRZYNASCIE asercji trzech testow okna drzwi
# w `StopWindowParityTests.cs`. Przeliczone z drzewa.
# 3288 -> 3296 (23.09.2026, 6.D357): OSIEM asercji `BrokenJsonRefusalTests.cs` —
# szesc w petli po 10 parach loader x ksztalt (wyjatek, zero slow parsera, obecnosc
# pozycji, wiersz, bajt, podloga na liczbe par) i dwie w kontroli pozycji z edytora;
# ZMIERZONE.
# 3296 -> 3311 (23.09.2026, 6.D356): PIETNASCIE asercji `BrokenJsonRefusalTests.cs`
# na odmowie CLI przy dokumencie innego KSZTALTU — trzy ksztalty przez
# `Program.Main`, kontrola w druga strone na wlasnych wyjatkach rdzenia i wiersz
# wspolnego handlera. Kazda z komunikatem; ZMIERZONE.
# 3311 -> 3320 (23.09.2026, tunel): dziewiec asercji testow nowej sceny tunelu.
# 3320 -> 3332 (24.09.2026, door-prompt-service): te same dwanascie asercji
# nowych testow komunikatu postoju i ukladu HUD; ZMIERZONE.
# 3332 -> 3342 (24.09.2026, braking cue): dziesiec asercji `BrakingCueTests`.
# 3342 -> 3347 (24.09.2026, PR #771): piec asercji `StationEdgeVisibilityTests`.
# 3347 -> 3349 (24.09.2026, kamera): dwie asercje ciaglosci i kierunku.
# 3349 -> 3361 (24.09.2026, dwustopniowe cue): te same dwanascie asercji.
# 3361 -> 3366 (24.09.2026, S): piec kontroli natychmiastowego wygaszenia.
# 3366 -> 3371 (24.09.2026, oznaczenia stacji): piec asercji nowych testow.
# 3371 -> 3385 (24.09.2026, pamiec cue): te same czternascie asercji.
# 3385 -> 3393 (24.09.2026, autopilot E): te same osiem asercji.
# 3393 -> 3396 (24.09.2026, HUD 800x600): te same trzy asercje.
# 3396 -> 3412 (24.09.2026, wybór składu i HUD): te same 16 netto.
# 3412 -> 3419 (24.09.2026, interaktywne R): te same siedem kontroli.
# 3419 -> 3423 (24.09.2026, automat bez sygnalizacji): te same cztery.
# 3423 -> 3424 (24.09.2026, widok chase 800x600): ta sama asercja.
# 3424 -> 3428 (24.09.2026, krótki HUD chase): cztery stany granicy.
# 3428 -> 3441 (24.09.2026, integracja tablic i pomocy linii):
# te same trzynaście kontroli z komunikatami.
# 3441 -> 3447 (24.09.2026, stan składu po zjeździe): sześć asercji.
# 3447 -> 3449 (24.09.2026, mocowania tablic): dwie asercje długości wsporników.
# 3449 -> 3462 (24.09.2026, wejście składu od wskazanej stacji).
# 3462 -> 3477 (24.09.2026, T-320): plan wejść i ciągłość obiegów.
# 3477 -> 3487 (24.09.2026, T-320): dziesięć kontroli bramki wjazdu.
# 3487 -> 3492 (24.09.2026, T-320): pięć kontroli chronologii obiegu.
# 3492 -> 3501 (24.09.2026, T-320): dziewięć kontroli bramki z planem.
# 3501 -> 3506 (24.09.2026, T-320): dzień służby i zapis 25:00.
# 3506 -> 3512 (24.09.2026, koniec osi): sześć kontroli stanu granicznego.
# 3512 -> 3530 (24.09.2026, koniec osi linii): końcowy postój i oprawy scenerii;
# po dziewięć asercji z komunikatem i bez komunikatu.
# 3530 -> 3544 (24.09.2026, dwa wjazdy rozkładowe): czternaście kontroli
# integracji LineEntrySchedule/LineEntryGate z planem blokowym L1_A. Wszystkie
# mają komunikat; zapadka BEZ_KOMUNIKATU pozostaje surowa.
# Po integracji dyspozytora i hamowania: 3595 wywolan, zmierzone w drzewie.
# 3544 -> 3606 (24.09.2026, testy dyspozytora, hamowania i scenerii).
# Równoległy pomiar gałęzi obserwacji:
# 3606 -> 3635 (24.09.2026, scena i adapter odtwarzania rozkladu).
# 3635 -> 3641 (24.09.2026, te same testy).
# 3641 -> 3660 (25.09.2026, obserwacja czynnych składów): zmierzone w drzewie.
# Równoległy pomiar gałęzi podglądu łącznika:
# Równoległa gałąź miała pomiary 3606 → 3610 i 3610 → 3645.
# 3660 -> 3664 (25.09.2026, integracja obserwacji i podglądu łącznika).
# 3664 -> 3668 (25.09.2026, nastawnik): cztery asercje przejścia przez neutral.
# 3668 -> 3671 (25.09.2026, tablice stacyjne): trzy kontrole skrajni i stropu.
# 3671 -> 3678 (25.09.2026, powtarzalność odcisku i drugi skład).
# 3678 -> 3682 (25.09.2026, stan nastawni o różnych terminach pytań).
# 3682 -> 3685 (25.09.2026, AZERTY): trzy asercje nowego testu mapy.
# 3685 -> 3694 (25.09.2026, T-400 ATP): dziewięć asercji testu trzech składów.
# 3694 -> 3695 (25.09.2026, T-400 platform): jawna kontrola mapowania widoku.
# 3695 -> 3702 (25.09.2026, T-400 platform): siedem kontroli rzeczywistego obrysu peronu.
# 3702 -> 3709 (25.09.2026, T-400 stop target): seven clearance and endpoint assertions.
# 3709 -> 3712 (25.09.2026, T-400 stop target): three active-track placement assertions.
# 3712 -> 3720 (25.09.2026, T-400 outcome): eight lifecycle assertions.
# 3720 -> 3725 (25.09.2026, T-400 outcome): five in-cab cue assertions.
# 3725 -> 3727 (25.09.2026, jawne granice aktualizacji etykiet HUD i STOP).
# 3727 -> 3730 (25.09.2026, trzy asercje planu r?cznego po integracji T-400).
# 3730 -> 3733 (26.09.2026, FirstRunSceneContractTests: trzy asercje kontraktu sceny).
# 3733 -> 3741 (26.09.2026, osiem asercji kompletności chunków).
# 3741 -> 3749 (26.09.2026, osiem asercji ról wykończeń zestawu dostępu stacji).
ASERCJI_RAZEM = 3749


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


#: Ile asercji zawezil literal napisowy w PIERWSZYM argumencie — 6.D156.
ZAWEZONYCH_PIERWSZYM_NAPISEM = 4

#: Ilu zawezenie po literale CALKOWITYM dotyczyloby, gdyby je przyjac — 6.D156.
#: Stoi tu, bo liczba odrzuconego zawezenia jest TRESCIA rozstrzygniecia: 26 to nie
#: „kilka", tylko szesciokrotnosc tego, co przyjeto, i mimo to nie wchodzi.
ODRZUCONYCH_PIERWSZYM_CALKOWITYM = 26


def _pierwsze_argumenty_nierozstrzygnietych():
    """`[tekst pierwszego argumentu]` dla kazdej asercji klasy NIEROZSTRZYGNIETE."""
    out = []
    for katalog in CA.CP.KATALOGI:
        for sciezka in CA.TW.znajdz(os.path.join(CA.ROOT, katalog), "*.cs", CA.ROOT):
            with open(sciezka, encoding="utf-8") as uchwyt:
                zrodlo = uchwyt.read()
            maska = CA.CTM.maska(zrodlo)
            for dopasowanie in CA.WYWOLANIE.finditer(maska):
                nazwa = "%s.%s" % (dopasowanie.group(1), dopasowanie.group(2))
                if nazwa not in CA.OBOWIAZKOWE_ARGUMENTY:
                    continue
                args = CA.CP.argumenty_z_nawiasami(maska, dopasowanie.end())
                if CA.klasa_komunikatu(nazwa, args, zrodlo) != CA.NIEROZSTRZYGNIETE:
                    continue
                poczatek, koniec = args[0]
                out.append(zrodlo[poczatek:koniec].strip())
    return out


def test_zawezenie_po_pierwszym_argumencie_jest_SZCZELNE_a_nie_heurystyka():
    """6.D156 — na wejsciu SYNTETYCZNYM, bo drzewo nie rozdziela tych przypadkow.

    Pole „Dlaczego to nie jest dopisanie reguly" ostrzega, ze zastosowanie obu
    zawezen „zamienialoby zadeklarowana niewiedze na cicha heurystyke". Te trzy
    asercje pokazuja granice miedzy zawezeniem, ktore WYKLUCZA przeciazenie,
    a takim, ktore je tylko czyni malo prawdopodobnym.
    """
    # SZCZELNE: napis do `double` nie konwertuje sie nigdy, wiec przeciazenie
    # z tolerancja zwiazac sie NIE MOZE i trzeci argument jest komunikatem.
    assert _klasa_wejscia('Assert.AreEqual("abc", x, opis);') == CA.Z_KOMUNIKATEM, (
        "literal napisowy w PIERWSZYM argumencie przestal wykluczac tolerancje")
    assert _klasa_wejscia('Assert.AreEqual("abc" + d, x, opis);') == CA.Z_KOMUNIKATEM, (
        "konkatenacja po literale przestala byc napisem — w C# `string + cokolwiek` "
        "daje napis, wiec to zawezenie jest tak samo szczelne")

    # NIESZCZELNE i dlatego ODRZUCONE: `int` konwertuje sie do `double`.
    assert _klasa_wejscia('Assert.AreEqual(0, x, opis);') == CA.NIEROZSTRZYGNIETE, (
        "literal CALKOWITY w pierwszym argumencie zawezil asercje — a nie moze, bo "
        "`int` konwertuje sie do `double` i przeciazenie z tolerancja wraca do gry")

    # NIESZCZELNE z drugiego powodu: kropka po literale zmienia typ wyrazenia.
    assert _klasa_wejscia('Assert.AreEqual("abc".Length, x, opis);') == (
        CA.NIEROZSTRZYGNIETE), (
        "`\"abc\".Length` zostalo uznane za napis — jest `int`em, wiec konwertuje sie "
        "do `double` i zawezenie przestaje byc wykluczeniem")

    # Kontrola, ze zawezenie nie zjadlo rozpoznawania TOLERANCJI, o co pole
    # „Weryfikacja" pozycji prosi wprost.
    assert _klasa_wejscia('Assert.AreEqual(1.0, x, 1e-9);') == CA.BEZ_KOMUNIKATU, (
        "tolerancja jako trzeci argument policzona jako komunikat")


def test_zawezenie_dotyka_czterech_asercji_a_odrzucone_dotknieloby_dwudziestu_pieciu():
    """6.D156 — obie liczby z DRZEWA, obie przybite, bo obie sa trescia.

    Bez drugiej liczby rozstrzygniecie „przyjmujemy szczelne, odrzucamy nieszczelne"
    czytaloby sie jak wybor bez kosztu. Koszt jest: odrzucone zawezenie zabralo by
    z klasy „nie wiem" SZESC RAZY wiecej pozycji niz przyjete.
    """
    pierwsze = _pierwsze_argumenty_nierozstrzygnietych()
    assert len(pierwsze) == NIEROZSTRZYGNIETYCH, (
        "nierozstrzygnietych jest %d, a zapadka stoi na %d"
        % (len(pierwsze), NIEROZSTRZYGNIETYCH))

    # Po zawezeniu ANI JEDNA nierozstrzygnieta nie ma juz napisu w pierwszym
    # argumencie — inaczej zawezenie sie nie zastosowalo tam, gdzie mialo.
    zostaly_napisy = [p for p in pierwsze if CA.PIERWSZY_ARGUMENT_NAPISOWY.match(p)]
    assert not zostaly_napisy, (
        "zawezenie nie zastosowalo sie do: %s" % zostaly_napisy)

    calkowite = [p for p in pierwsze if CA.LITERAL_CALKOWITY_ODRZUCONY.match(p)]
    assert len(calkowite) == ODRZUCONYCH_PIERWSZYM_CALKOWITYM, (
        "literalow calkowitych w pierwszym argumencie jest %d, a pomiar z 12.09.2026 "
        "dal %d — liczba ODRZUCONEGO zawezenia zmienila sie i rozstrzygniecie 6.D156 "
        "opisuje inny koszt" % (len(calkowite), ODRZUCONYCH_PIERWSZYM_CALKOWITYM))


def test_zawezenie_naprawde_cos_zabralo_z_klasy_nie_wiem():
    """Kontrola, ze `PIERWSZY_ARGUMENT_NAPISOWY` nie jest bezczynny — 6.D156.

    Bez niej dwie bramki wyzej przechodzilyby tak samo, gdyby wzorzec nie lapal
    NICZEGO: „zadna nierozstrzygnieta nie ma napisu" jest wtedy prawda z niczego.
    Ta sama pulapka, co przy bezczynnym wyjatku z 6.D142.
    """
    bez_zawezenia = 0
    for katalog in CA.CP.KATALOGI:
        for sciezka in CA.TW.znajdz(os.path.join(CA.ROOT, katalog), "*.cs", CA.ROOT):
            with open(sciezka, encoding="utf-8") as uchwyt:
                zrodlo = uchwyt.read()
            maska = CA.CTM.maska(zrodlo)
            for dopasowanie in CA.WYWOLANIE.finditer(maska):
                nazwa = "%s.%s" % (dopasowanie.group(1), dopasowanie.group(2))
                if nazwa not in CA.RODZINA_Z_TOLERANCJA:
                    continue
                args = CA.CP.argumenty_z_nawiasami(maska, dopasowanie.end())
                if len(args) != 3:
                    continue
                poczatek, koniec = args[-1]
                if CA.LITERAL_NAPISOWY.match(zrodlo[poczatek:koniec].strip()):
                    continue
                if CA.CP.LICZBA.match(zrodlo[poczatek:koniec].strip()):
                    continue
                pierwszy_a, pierwszy_b = args[0]
                if CA.PIERWSZY_ARGUMENT_NAPISOWY.match(
                        zrodlo[pierwszy_a:pierwszy_b].strip()):
                    bez_zawezenia += 1

    assert bez_zawezenia == ZAWEZONYCH_PIERWSZYM_NAPISEM, (
        "zawezenie zabralo z klasy „nie wiem” %d pozycji, a pomiar "
        "%d — jesli ZERO, wzorzec przestal lapac cokolwiek i obie bramki wyzej sa "
        "zielone z niczego" % (bez_zawezenia, ZAWEZONYCH_PIERWSZYM_NAPISEM))

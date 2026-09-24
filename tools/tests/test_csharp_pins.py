#!/usr/bin/env python3
"""Piny wpisane z ręki w testach warstwy gry — policzone i skategoryzowane (6.D131).

Pozycja jest POMIAREM: nie zdejmuje ani nie przepisuje żadnego pinu (wprost w polu
„Poza zakresem"), tylko mówi, ile ich jest, które są niezbędne i czy którykolwiek da
się przybić inaczej.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csharp_pins as CP  # noqa: E402

#: Piny warstwy gry per plik. Zmierzone 11.09.2026 na `dfc7543`: 44 w ośmiu plikach;
#: **45 od 6.D142**, które dopisało `Assert.AreEqual("E c", BezJednostek("Esc"))`,
#: i **47 od 6.D155**, które dopisało `BezJednostek("akmb") == "a b"` (mechanizm:
#: podstawiana jest SPACJA, więc pary liter utworzyć nie umie) oraz resztkę `"a"`
#: z wiersza prędkości HUD-u. Oba są kategorii C — wynik JEDNEJ przemiany napisu.
#: Zapadka działa w obie strony, jak przy asercjach bez komunikatu z 6.D127: w górę
#: mówi „doszedł pin, skategoryzuj go", w dół — „pin zniknął, zdejmij go z tabeli".
PINY_GRY = {
    "ChaseCameraAimTests.cs": 3,
    # MB-05: jeden pin w `CabPlacementTests.cs` — brzmienie warunku widocznosci kabiny
    # (`view == ViewKind.Cab`). KATEGORIA C: wartosc liczona w JEDNYM miejscu, czyli
    # w `FirstRun.ApplyView`. Trzy liczby tego pliku nie sa pinami napisowymi i stoja
    # w `ROZKLAD_LICZBOWYCH` (218 -> 221).
    #
    # 1 -> 6 (14.09.2026, audyt bramki MB-05). Ten wpis jest PRZEPISANY, a nie dopisany
    # obok: piec nowych pinow to nie rozbudowa, tylko zamiana asercji, ktore pytaly
    # o PISOWNIE, na asercje pytajace o TRESC. Stare `Contains("trainLength")` bylo
    # prawda rowniez dla `chainage - trainLength + 0.7` (zmierzone: 292/292), wiec
    # w miejsce dwoch `Contains` weszly porownania dokladne calej listy argumentow:
    # `_sceneAxis, TrainLayout.RearOfTrain(chainage, trainLength)`, `_train.LengthM`,
    # `_sceneAxis, chainage`, `TrainLayout.PlaceWithRear(axis, _bodies, rearChainageM)`
    # i pin kontroli przyrzadu. Wszystkie KATEGORII C — kazda wartosc stoi w JEDNYM
    # miejscu zrodla, o ktore bramka pyta.
    "CabPlacementTests.cs": 6,
    "ChunkManifestTests.cs": 3,
    # MB-08: dwa piny w `DoorPromptTests.cs` — wyjscie awaryjne ramienia
    # domyslnego (`"99"`) i nazwa czlonu `None`, ktory NIE jest odmowa.
    # Oba KATEGORII C: wartosc stoi w JEDNYM miejscu zrodla, w `DoorPrompt.Reason`.
    # Trzeci pin sprawdza caly wiersz fazy recznej, zamiast niejednoznacznej igly DRZWI.
    "DoorPromptTests.cs": 3,
    "HudLayoutTests.cs": 1,
    # Dwa dokładne warianty pozycji, oba wyniki pojedynczego formatera (C).
    "HudPositionTests.cs": 2,
    "RunHeaderTests.cs": 1,
    "RunPlanTests.cs": 30,
    "RunResetTests.cs": 2,
    "SignallingHudTests.cs": 2,
    "StationWayfindingTests.cs": 2,
    "TelemetryTrackTests.cs": 1,
    # MB-03: cztery piny w `TractionBlockTests.cs` — trzy brzmienia wiersza blokady
    # i jedno przy dwóch blokadach naraz. Wszystkie cztery to KATEGORIA C: kazdy jest
    # wynikiem JEDNEJ przemiany napisu (`TractionBlock.Line` na wpisie katalogu),
    # a nie wynikiem zlozonym z kilku zrodel ani wejsciem syntetycznym.
    "TractionBlockTests.cs": 5,
    # 8 -> 9 (14.09.2026, MB-07): pin na wiersz pomocy dla składu PRZEJĘTEGO
    # (`HelpWhenTheDriverHasTaken`). Kategoria C — napis składa się w JEDNYM miejscu,
    # w `DriverActions.BuildDriverHasTakenHelp`, i bramka pyta o jego treść.
    # 9 -> 12 (15.09.2026, 6.D214): trzy piny bramki na zgloszeniach URWANYCH —
    # pelne wyrazenie z indeksatorem, zgloszenie starego czytnika i wyrazenie
    # po wyniku metody. Kategoria C: kazda z tych wartosci jest tresc JEDNEGO
    # miejsca w drzewie, a nie liczba miejsc.
    "UiTextTests.cs": 12,
}

#: Ile pinów stoi w `tests/Sim.Tests` — liczba PORÓWNAWCZA, o którą prosiło pole
#: „Wejście". Rdzeń ma ich 74 przy 36 plikach, gra 47 przy 16: na plik wypada
#: **2,06** wobec **2,94**, więc gra pinuje GĘŚCIEJ, mimo że ma mniej testów.
#:
#: **74 -> 76 (13.09.2026, MB-02):** dwa piny w `TrainingSessionTests.cs`
#: (`"Pierwsza"` jako nazwa celu z osi i `"s1"` jako identyfikator stacji miniętej).
#: Proporcja praktycznie się nie rusza — 37 plików rdzenia daje **2,05**, a gra
#: zostaje na **2,94** przy 16 plikach, bo `RunSummaryTests.cs` nie wnosi ani jednego
#: pinu NAPISOWEGO: cały jego tekst przychodzi z katalogu `UiText`, a nie z literałów
#: w teście. To nie jest przypadek, tylko skutek tego, że panel wyniku nie składa
#: żadnego napisu u siebie.
# 76 -> 75 (14.09.2026, MB-07): zniknął pin napisowy z przepisanego
# `Drugi_sklad_zatrzymuje_sie_przed_blokiem_zajetym_przez_pierwszy` — asercja
# `AreEqual("step-budget", reason)` przypinała ZATOR jako wynik oczekiwany. Test pyta
# dziś o `"arrived"`, ale przez zmienną, nie przez literał w tym miejscu.
# 75 -> 77 (23.09.2026, 6.D365): dwa piny `AreEqual(",", …)` w `DoorCycleTests.cs`
# i `TrainingSessionTests.cs` — straz, ze pl-PL naprawde ma przecinek; ZMIERZONE.
# 77 -> 78 (23.09.2026, 6.D356): pin napisowy `"BŁĄD: " + Program.WrongJsonShapeText`
# w `BrokenJsonRefusalTests.cs` — wiersz wspolnego handlera `Sim.Runner` przy
# dokumencie innego ksztaltu, porownany w calosci; ZMIERZONE.
# 78 -> 81 (24.09.2026, T-320): data, kurs i identyfikator obiegu.
# 81 -> 85 (24.09.2026, T-320): cztery kursy w dwóch przejściach obiegu.
# 85 -> 86 (24.09.2026, T-320): pierwszy trip_id po remisie w planie.
# 86 -> 87 (24.09.2026, koniec osi linii): nazwa postoju Merode w LineDriveTests.
PINY_RDZENIA = 87

#: Kategorie, po jednej pozycji na pin — zamknięte i sumujące się do liczby wyżej.
#:
#: **Podział jest ZAPISANY, a nie wyprowadzony regułą, i to jest wynik pomiaru.**
#: Próbowałem reguły po kształcie literału („zawiera interpunkt albo dwie spacje pod
#: rząd = wynik złożony"). Myli się na dwóch z czterech: **przepuszcza**
#: `UiTextTests.cs:700`, czyli wiersz o hamulcu awaryjnym, który jest złożony,
#: a rozdzielony pojedynczymi spacjami, i **łapie** `UiTextTests.cs:770`, który
#: pinem wyjścia nie jest wcale — to WEJŚCIE syntetyczne kontroli `BezDziur`.
#: Reguła myląca się w połowie przypadków jest gorsza niż wypisana tabela, bo
#: zmyśla kategorię tam, gdzie nikt nie patrzy.
#:
#: A — pin na wynik ZŁOŻONY z kilku źródeł. Niezbędny: wartość liczona z katalogu
#:     byłaby porównaniem katalogu z samym sobą. Pole „Skończone, gdy" pozycji 6.D99
#:     żądało wypisu tych samych wierszy wprost i to jest ta sama decyzja.
#: B — WEJŚCIE syntetyczne kontroli przyrządu. Nie jest pinem na wyjście programu;
#:     literał jest tu daną testu i inaczej zapisać się go nie da.
#: C — pin na wartość liczoną w JEDNYM miejscu: nazwa trybu, ścieżka, identyfikator
#:     albo wynik jednej przemiany napisu (`BezJednostek("Esc") == "E c"` z 6.D142 —
#:     zdanie o kategorii dopisane razem z pinem, żeby nie rozszerzyć jej po cichu).
#:
#: **Kotwica to (plik, WIERSZ), wiec kazda wstawka wyzej w pliku ja przesuwa** — i to
#: nie jest wada tabeli, tylko jej koszt, ktory trzeba placic w tym samym commicie.
#: MB-02 przesunelo piec kotwic w `UiTextTests.cs` o TRZY wiersze (1150/1156/1161 ->
#: 1153/1159/1164 oraz 1230/1231 -> 1233/1234); tresc pinow nie zmienila sie ani o znak,
#: co sprawdzone porownaniem trzywierszowych blokow ze starym plikiem.
#:
#: MB-04 przesunelo te same piec kotwic o KOLEJNE TRZY wiersze (-> 1156/1162/1167 oraz
#: 1236/1237). Powod jest jeden i stoi WYZEJ od nich: trzywierszowy komentarz z powodem
#: przy `LiteralowWZasieguBramki` (509 -> 521). Tresc pinow znowu nie zmienila sie ani
#: o znak — sprawdzone `diff`em blokow z `git show HEAD:` wobec drzewa, a nie oceną.
#:
#: MB-05 przesunelo je o TRZECIE trzy wiersze, a potem — poprawka `--cab` w tym samym
#: commicie — o SZOSTY, CZTERY wiersze (MB-07): koncowe polozenie to 1168/1177/1193 oraz
#: 1240/1241. Drugi ruch zrobil JEDNOWIERSZOWY komentarz przy `LiteralowWZasieguBramki`
#: (529 -> 530), czyli nawet jedna linijka powyzej kotwicy ja przesuwa.
#: Powod pierwszego ruchu byl ten sam co przy MB-04 i w tym samym miejscu (521 -> 529). Tresc znowu bez zmiany
#: o znak, znowu sprawdzona `diff`em. **Trzy razy z rzedu ta sama kotwica przesunela
#: sie o ten sam komentarz i to jest znak, a nie zbieg**: kotwica po numerze wiersza
#: placi ten koszt przy KAZDEJ edycji powyzej siebie. Zamiana jej na kotwice po TRESCI
#: jest pozycja do kolejki, nie robota do zrobienia po drodze przy aktywnym kamieniu
#: milowym (CLAUDE.md §8).
KATEGORIE = {
    "A": {
        # SZÓSTY ruch tych kotwic w ciągu doby (MB-07, 14.09.2026) — tym razem
        # o cztery wiersze, przez komentarz z powodem przy `LiteralowWZasieguBramki`.
        # Kotwica po NUMERZE WIERSZA płaci ten koszt przy każdej edycji powyżej siebie;
        # zamiana jej na kotwicę po TREŚCI jest pozycją w kolejce, a nie robotą po
        # drodze przy aktywnym kamieniu milowym (CLAUDE.md §8).
        # SIÓDMY ruch tych kotwic (MB-08, 14.09.2026): 1168/1177/1193 -> 1176/1189/1199.
        # Tym razem przesunęły je DWIE rzeczy naraz — komentarz z powodem przy
        # `LiteralowWZasieguBramki` (jak sześć razy wcześniej) ORAZ dopisane do pinów
        # nowe człony wiersza pomocy (`D otwórz drzwi`, `F zamknij drzwi`), czyli po raz
        # pierwszy zmieniła się także TREŚĆ dwóch z nich. Sprawdzone wypisem skanera,
        # a nie liczeniem wierszy z ręki.
        # OSMY ruch tych kotwic (6.D229, 17.09.2026): 1265/1278/1296 -> 1269/1282/1300
        # i 1365/1366 -> 1369/1370. Powod jest TEN SAM, co szesc z siedmiu razy wyzej —
        # komentarz z powodem przy `LiteralowWZasieguBramki`, tym razem o cztery wiersze.
        # TRESC pinow nie drgnela; przesunal sie wylacznie numer wiersza. Sprawdzone
        # wypisem skanera, a nie liczeniem wierszy z reki.
        # DZIEWIATY ruch tych kotwic (6.D235, 22.09.2026): 1269/1282/1300 -> 1272/1285/1303
        # i 1369/1370 -> 1372/1373. Powod ten sam — komentarz z powodem przy
        # `LiteralowWZasieguBramki`, tym razem o trzy wiersze. TRESC pinow nie drgnela.
        # Przeliczone roznica plikow (difflib), a nie liczeniem wierszy z reki.
        # DZIESIATY ruch tych kotwic (6.M1, 23.09.2026): 1272/1285/1303 -> 1273/1286/1304
        # i 1372/1373 -> 1373/1374. Powod ten sam — komentarz z powodem przy
        # `LiteralowWZasieguBramki`, tym razem o jeden wiersz. TRESC pinow nie drgnela.
        # Przeliczone roznica plikow (difflib).
        # Dodatkowe ogniwo pomiaru korpusu przesuwa kotwice o kolejny wiersz.
        # 24.09.2026: komentarz o scenerii Merode przesunął kotwice o wiersz.
        # Dodatkowy komentarz o wyróżnieniu celu przesuwa kotwice o wiersz.
        # Komentarz o końcu toru przesuwa kotwice o kolejny wiersz.
        # Dwa komentarze o lampach scenerii przesunęły te same piny o dwa wiersze.
        ("UiTextTests.cs", 1289), ("UiTextTests.cs", 1302), ("UiTextTests.cs", 1320),
        ("SignallingHudTests.cs", 39),
    },
    "B": {
        ("UiTextTests.cs", 1389), ("UiTextTests.cs", 1390),
    },
}

#: Ile pinów wpada do kategorii C — reszta, liczona, nie wpisana.
# 41 -> 46 (14.09.2026, MB-03): piec pinow `TractionBlockTests.cs` — cztery brzmienia
# wiersza blokady i jedno brzmienie wariantu `hud.speed.no-limit`.
# 46 -> 47 (14.09.2026, MB-05): jeden pin `CabPlacementTests.cs` — brzmienie warunku
# widocznosci kabiny (`view == ViewKind.Cab`). Kategoria C, bo jest to wartosc liczona
# w JEDNYM miejscu: `FirstRun.ApplyView` ma ten warunek raz i bramka pyta o jego tresc.
# 47 -> 52 (14.09.2026, audyt bramki MB-05): piec pinow `CabPlacementTests.cs`
# w miejsce dwoch asercji `Contains`, ktore pytaly o pisownie tokenu, a nie o tresc
# wyrazenia. Kategoria C, bo kazda z tych wartosci stoi w JEDNYM miejscu zrodla.
# 52 -> 53 (14.09.2026, MB-07): pin wiersza pomocy dla składu przejętego.
# 53 -> 55 (14.09.2026, MB-08): dwa piny `DoorPromptTests.cs`.
# 55 -> 58 (15.09.2026, 6.D214): trzy piny `UiTextTests.cs` opisane wyzej.
# 58 -> 59 (24.09.2026, braking cue): pin w teście wskazówki hamowania.
# 59 -> 60 (24.09.2026, integracja): dokladny wiersz fazy DoorPromptTests.
# 60 -> 59 (24.09.2026, cue): dwa syntetyczne piny UiTextTests zajmuja teraz
# osobne wiersze 1378/1379, wiec oba sa jawnie w kategorii B.
# 59 -> 61 (24.09.2026, tablice stacji): dwie pelne nazwy w StationWayfindingTests.
# 61 -> 62 (24.09.2026, HUD 800x600): jednoliniowy kilometraż przy widocznej stacji.
# 62 -> 63 (24.09.2026, HUD bez wiersza stacji): pełny wiersz pozycji.
# 63 -> 66 (24.09.2026, krótki HUD chase): trzy dokładne brzmienia
# wskazówki przy różnych pozycjach względem granicy. Kategoria C,
# bo tekst powstaje w jednym formatterze ChaseAvailability.HudHint.
# 66 -> 67 (24.09.2026, test końca planu): wynik `LineCore.Run` jest jednym źródłem.
LICZBA_C = 67


def test_ile_pinow_stoi_w_testach_warstwy_gry():
    """Liczba z drzewa, zapadka w obie strony — 6.D131."""
    zmierzone = CP.per_plik("tests/Game.Tests")

    assert zmierzone == PINY_GRY, (
        "piny warstwy gry rozjechały się z tabelą (zmierzone / zapisane): %s / %s "
        "— doszedł pin do skategoryzowania albo zniknął pin do zdjęcia"
        % (sorted(zmierzone.items()), sorted(PINY_GRY.items())))

    # 61 -> 64 (15.09.2026, 6.D214): trzy piny `UiTextTests.cs` bramki na
    # zgloszeniach URWANYCH.
    # 64 -> 65 (24.09.2026, integracja): pin caly wiersz fazy.
    # 65 -> 67 (24.09.2026, tablice stacji): dwie pelne nazwy.
    # 67 -> 69 (24.09.2026, HUD 800x600): dwa dokładne warianty pozycji.
    assert sum(zmierzone.values()) == 73, (
        "pinów warstwy gry jest %d, a pomiar z 14.09.2026 dał 61 "
        "(47 po 6.D155, 45 przed nim; +5 przy MB-03, +1 przy MB-05, "
        "+5 przy audycie bramki MB-05, +2 przy MB-08 — `DoorPromptTests`)"
        % sum(zmierzone.values()))

    ile_rdzenia = len(CP.piny("tests/Sim.Tests"))
    assert ile_rdzenia == PINY_RDZENIA, (
        "pinów rdzenia jest %d przy zapisanych %d — liczba porównawcza wymaga "
        "przeliczenia" % (ile_rdzenia, PINY_RDZENIA))


def test_kazdy_pin_ma_kategorie_i_suma_sie_zgadza():
    """Pole „Skończone, gdy": każdy pin ma przypisaną kategorię — 6.D131."""
    wszystkie = {(plik, wiersz) for plik, wiersz, _r, _t
                 in CP.piny("tests/Game.Tests")}
    nazwane = KATEGORIE["A"] | KATEGORIE["B"]

    assert nazwane <= wszystkie, (
        "kategoria wskazuje pin, którego w drzewie nie ma: %s"
        % sorted(nazwane - wszystkie))
    assert not (KATEGORIE["A"] & KATEGORIE["B"]), (
        "pin wpisany do dwóch kategorii naraz: %s"
        % sorted(KATEGORIE["A"] & KATEGORIE["B"]))
    assert len(wszystkie - nazwane) == LICZBA_C, (
        "do kategorii C wpada %d pinów przy zapisanych %d"
        % (len(wszystkie - nazwane), LICZBA_C))
    # 52 -> 53 (14.09.2026, MB-05): pin `CabPlacementTests.cs` w kategorii C.
    # KOMUNIKAT MOWI DZIS TE SAMA LICZBE CO ASERCJA, i to jest poprawka przy okazji,
    # ktora NIE jest przy okazji: stalo tu „nie sumują się do 47" przy warunku na 52,
    # czyli komunikat bledu podawal liczbe o piec mniejsza od tej, ktorej bramka
    # pilnowala. Kto by na niego trafil, szukalby rozbieznosci, ktorej nie ma.
    assert len(KATEGORIE["A"]) + len(KATEGORIE["B"]) + LICZBA_C == 73, (
        "kategorie nie sumują się do 73: A=%d, B=%d, C=%d"
        % (len(KATEGORIE["A"]), len(KATEGORIE["B"]), LICZBA_C))


def test_regula_po_ksztalcie_literalu_myli_sie_i_dlatego_jej_nie_ma():
    """Kontrola rozstrzygnięcia: podział jest zapisany, bo reguła się MYLI.

    Bez tego testu zdanie „reguły nie da się napisać" byłoby opinią. Tutaj jest
    wykonane: reguła „interpunkt albo dwie spacje pod rząd" przepuszcza jeden pin
    kategorii A i łapie jeden z kategorii B.
    """
    import re as _re

    regula = _re.compile(r"·|  ")
    tresci = {(plik, wiersz): tresc
              for plik, wiersz, _r, tresc in CP.piny("tests/Game.Tests")}

    przepuszczone = [p for p in sorted(KATEGORIE["A"])
                     if not regula.search(tresci[p])]
    zlapane_z_b = [p for p in sorted(KATEGORIE["B"]) if regula.search(tresci[p])]

    assert przepuszczone == [("UiTextTests.cs", 1320)], (
        "reguła po kształcie przestała przepuszczać wiersz o hamulcu awaryjnym — "
        "rozstrzygnięcie 6.D131 wymaga przeliczenia: %s" % przepuszczone)
    assert zlapane_z_b == [("UiTextTests.cs", 1390)], (
        "reguła po kształcie przestała łapić wejście syntetyczne: %s" % zlapane_z_b)


def test_czytnik_widzi_pin_takze_wtedy_gdy_literal_jest_sklejony():
    """Kontrola przyrządu: `"…" + "…"` przez kilka wierszy to JEDEN pin.

    Trzy z czterech pinów kategorii A są tak zapisane. Czytnik biorący sam pierwszy
    człon podawałby ich długość jako ułamek prawdziwej — a długość jest jedyną
    rzeczą, po której widać, że pin trzyma CAŁY wiersz, a nie jego początek.
    """
    tresci = {(plik, wiersz): tresc
              for plik, wiersz, _r, tresc in CP.piny("tests/Game.Tests")}

    assert len(tresci[("UiTextTests.cs", 1289)]) == 122, (
        "sklejanie literałów przestało działać: %d znaków"
        % len(tresci[("UiTextTests.cs", 1289)]))
    assert len(tresci[("UiTextTests.cs", 1320)]) == 98, (
        len(tresci[("UiTextTests.cs", 1320)]))
    assert len(tresci[("SignallingHudTests.cs", 39)]) == 84, (
        len(tresci[("SignallingHudTests.cs", 39)]))

    # Kontrola w drugą stronę: krótki pin ma zostać krótki, inaczej sklejanie
    # zjadałoby sąsiednie argumenty.
    assert tresci[("ChunkManifestTests.cs", 57)] == "L1_A", (
        tresci[("ChunkManifestTests.cs", 57)])


def test_maska_odsiewa_wywolania_z_komentarzy_i_napisow(tmp=None):
    """Kontrola przyrządu: `Assert.AreEqual` w napisie nie jest wywołaniem.

    **Maska jest dziś UBEZPIECZENIEM, a nie zmierzoną koniecznością — i to jest
    wynik kontroli negatywnej, nie przypuszczenie.** KN-4 zastąpiła
    `CTM.maska(zrodlo)` samym źródłem i zestaw przeszedł **5/5**: w całym
    `tests/Game.Tests` nie ma dziś ani jednego `Assert.AreEqual("` wewnątrz
    komentarza albo napisu, więc na tym drzewie maska nie zmienia ani jednej liczby.

    Pierwsza wersja tego testu składała maskę SAMA i przez to nie pilnowała
    `piny()` wcale — była zielona niezależnie od tego, czy czytnik maski używa.
    Dziś przechodzi przez `piny()` na drzewie probnym, więc zdjęcie maski z czytnika
    ją wywraca.
    """
    import shutil
    import tempfile

    katalog = tmp or tempfile.mkdtemp(prefix="piny-probne-")
    try:
        gdzie = os.path.join(katalog, "tests", "Game.Tests")
        os.makedirs(gdzie, exist_ok=True)
        with open(os.path.join(gdzie, "Probka.cs"), "w", encoding="utf-8") as uchwyt:
            uchwyt.write(
                'class X {\n'
                '    // Assert.AreEqual("w komentarzu", x);\n'
                '    void A() { var s = "Assert.AreEqual(\\"w napisie\\", y)"; }\n'
                '    void B() { Assert.AreEqual("prawdziwy", z); }\n'
                '}\n')

        znalezione = CP.piny("tests/Game.Tests", root=katalog)
        tresci = [tresc for _p, _w, _r, tresc in znalezione]
        assert tresci == ["prawdziwy"], (
            "czytnik policzył wywołanie z komentarza albo z napisu: %s" % tresci)

        # Kontrola w drugą stronę: próbka NAPRAWDĘ niesie trzy wystąpienia, więc
        # zieleń wyżej znaczy „dwa odsiane", a nie „nie było czego odsiewać".
        with open(os.path.join(gdzie, "Probka.cs"), encoding="utf-8") as uchwyt:
            surowe = [m.group(1) for m in CP.ASERCJA.finditer(uchwyt.read())]
        assert len(surowe) == 3, (
            "próbka przestała zawierać trzy wystąpienia — ten test mierzyłby nic: %s"
            % surowe)
    finally:
        if tmp is None:
            shutil.rmtree(katalog, ignore_errors=True)


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw.
# --- 6.D141: piny LICZBOWE ------------------------------------------------------

#: **Zmierzone 11.09.2026** na `888a190`. Pinów liczbowych jest **627** — pięć razy
#: więcej niż napisowych (118, z 6.D131) — i dlatego mają **własny licznik, a nie
#: wpis w `KATEGORIE`**. To jest rozstrzygnięcie, o które prosiło pole „Wyjście":
#: tabela z jednym wierszem na pin ma sens przy 44 pozycjach, a przy 627 byłaby
#: dłuższa od kodu, który opisuje, i rozjeżdżałaby się przy każdej zmianie liczby.
#:
#: Podział na tolerancję jest za to treścią i on zostaje wypisany:
ROZKLAD_LICZBOWYCH = {
    "tests/Game.Tests": {
        # 215 -> 216 (13.09.2026, MB-02): `TrainingWiringTests.cs` przybija jedna
        # liczbe — `DesignAssumptions.TrainingTargets == 2`.
        # 216 -> 218 (14.09.2026, MB-03): dwie liczby siatki w `TractionBlockTests.cs`
        # (21 par i 20 par z blokada). `calkowite_z_tolerancja` zostaje ZEREM.
        # 218 -> 221 (14.09.2026, MB-05): trzy liczby w `CabPlacementTests.cs` —
        # dwie liczby wywolan (`_cabView.PlaceAt` i `_cabView.Visible` maja stac
        # DOKLADNIE raz) i jeden pin polozenia. `calkowite_z_tolerancja` zostaje ZEREM.
        # 221 -> 229 (14.09.2026, audyt bramki MB-05): osiem liczb, ktore
        # WYKONUJA arytmetyke, a nie czytaja zrodlo. Powod jest pomiarem:
        # `Ta_sama_wspolrzedna_X_daje_ten_sam_kilometraz_w_obu_zbiorach` liczyla
        # OBIE strony rownosci tym samym wyrazeniem na tych samych brylach, wiec
        # podmiana bryl kabiny na `(-999, -998)` dawala `1/1 przeszlo`. Teraz
        # porownywane sa DWA plany (skorupy i kabiny) i trzeci, zly — stad 1906,0 m,
        # 0,35 m za czolem, 0,700 m roznicy i zgodnosc z `RearChainageM(Skorupa())`.
        # `calkowite_z_tolerancja` zostaje ZEREM.
        # 229 -> 232 (14.09.2026, MB-08): trzy liczby CALKOWITE w `DoorPromptTests.cs`
        # — piec powodow odmowy, piec roznych zdan i piec faz ruchu skrzydel. Zadna
        # nie jest tolerancja, wiec `z_tolerancja` i `tolerancja_zero` stoja w miejscu,
        # a `calkowite_z_tolerancja` zostaje ZEREM.
        # 232 -> 233 (15.09.2026, 6.D213): JEDEN pin liczbowy bramki na `.ToString()`
        # w rdzeniu — `Assert.AreEqual(0, naWyliczeniu.Count, …)`, czyli „na wartości
        # wyliczenia nie stoi ANI JEDNO". CAŁKOWITY i BEZ TOLERANCJI, bo jest liczbą
        # miejsc w kodzie; `calkowite_z_tolerancja` zostaje ZEREM. Podłogi tej bramki
        # do liczby nie wchodzą — stoją jako `>=`, a nie jako pin równościowy.
        # 233 -> 234 (15.09.2026, 6.D214): JEDEN pin liczbowy — `Assert.AreEqual(0,
        # urwane.Count, …)`, czyli „zgloszen urwanych nie ma ANI JEDNEGO". CALKOWITY
        # i BEZ TOLERANCJI; podloga `MinimumZgloszenToString` do liczby nie wchodzi,
        # bo stoi jako `>=`.
        # 234 -> 235 (15.09.2026, 6.D215): JEDEN pin liczbowy — "warunek stoi
        # w JEDNYM miejscu". CALKOWITY i BEZ TOLERANCJI: to liczba miejsc w kodzie.
        # 235 -> 237 (15.09.2026, 6.D217): DWA piny liczbowe — „dziur z tekstem
        # OBCYM jest 9" i „wolajacych `RunPlan.Refusal` jest 26". Oba sa zdaniem
        # o drodze bledu, a nie progiem: pierwszy mowi, ile razy silnik dopisuje
        # sie do komunikatu, drugi — ilu wytworcow ma jedyne wywolanie `Abort`
        # bez wlasnego literalu. Oba calkowite i bez tolerancji.
        # 237 -> 240 (15.09.2026, 6.D224): TRZY piny liczbowe bramki na DRUGIEJ
        # slepej plamce sita rdzenia — „wpis wykazu ma CZTERY pola", „wzorzec
        # deklaracji trafia w plik DOKLADNIE RAZ" i „`.ToString()` na `var`-ze
        # o typie wyliczeniowym nie stoi ANI RAZ". Wszystkie CALKOWITE i BEZ
        # TOLERANCJI, bo kazdy jest liczba miejsc w kodzie. Liczba NAKLADANIA sie
        # obu plamek do rozkladu NIE WCHODZI i to jest tresc, a nie przeoczenie:
        # stoi jako stala `NakladaniePlamek`, wiec w asercji nie ma literalu.
        # Podloga na liczbe slow `var` tez nie wchodzi — zostala ZDJETA, bo
        # zmierzono, ze zapala sie na kodzie poprawnym (6.D27): zamiana jednego
        # `var` na typ jawny daje 535 przy pinie 536.
        # 240 -> 246 (22.09.2026, 6.D235): SZESC pinow calkowitych bez tolerancji
        # w `FileReadGuardTests.cs` i `BadFileTests.cs`. Przeliczone z drzewa.
        # 246 -> 249: trzy piny pozycji widoku kabiny, kazdy float z tolerancja.
        # 249 -> 250 (24.09.2026, door-prompt-service): jeden pin liczby
        # wierszy komunikatu HUD; calkowity bez tolerancji. ZMIERZONE.
        # 250 -> 251 (24.09.2026, braking cue): dystans z tolerancja.
        # 251 -> 252 (24.09.2026, kamera): pin kierunku z tolerancja.
        # 252 -> 255: trzy pomiary polozenia tablic z tolerancja.
        # 255 -> 256: krok pojawienia sie PREP w replay, calkowity bez tolerancji.
        # 256 -> 257: pin pelnego hamulca z tolerancja po przejeciu przez gracza.
        # 257 -> 260 (24.09.2026, dwie tablice): trzy polozenia z tolerancja.
        # 260 -> 262 (24.09.2026, mocowania tablic): dwie długości z tolerancją.
        "razem": 262, "z_tolerancja": 117, "bez_tolerancji": 145,
        "zmiennoprzecinkowe": 123, "zmiennoprzecinkowe_bez_tolerancji": 6,
        "calkowite": 139, "calkowite_z_tolerancja": 0, "tolerancja_zero": 18,
    },
    "tests/Sim.Tests": {
        # 441 -> 454 (13.09.2026, MB-02): trzynaście pinów liczbowych
        # w `TrainingSessionTests.cs`. `calkowite_z_tolerancja` zostaje ZEREM, a to
        # jest tu jedyna liczba, która niesie zdanie, a nie stan drzewa.
        # 458 -> 460 (14.09.2026, MB-06): dwa piny liczbowe `ControlOwnerTests.cs` —
        # liczba komend widzianych przez ochronę w jednym kroku (1) i prędkość zerowa
        # po dwudziestu sekundach pełnego hamulca. `calkowite_z_tolerancja` zostaje ZEREM.
        # 460 -> 462 (14.09.2026, MB-06, poprawka dziury w ochronie): dwa piny
        # w testach galezi postoju — liczba komend widzianych przez ochrone w kroku
        # postoju (1) i zerowy nastawnik, ktory ochrona dostaje JUZ po filtrze drzwi.
        # 462 -> 461 (14.09.2026, MB-07) i ta liczba idzie W DÓŁ, co jest tu POPRAWNE.
        # Trzy testy `LineCoreTests.cs` przypinały ZATOR (skład, który dojechał, zostawał
        # na peronie na zawsze) i zostały przepisane, bo właściciel rozstrzygnął
        # 14.09.2026, że skład schodzi z planu. Zniknął pin `AreEqual(0.0, …SpeedMps, 0.0)`
        # — „drugi skład przed zajętym blokiem nadal jedzie" — bo zmierzone jest, że
        # w oknie pomiarowym skład PEŁZNIE 0,008539847973193317 m/s, więc asercja o zerze
        # opisywałaby inny stan niż ten, o który test pyta. Stąd `tolerancja_zero` 114 -> 113.
        # 461 -> 463 (14.09.2026, audyt MB-06): dwa piny testu werdyktu ochrony —
        # liczba wierszy śladu (240) i liczba poleceń omijających ochronę (0). Oba
        # CAŁKOWITE i BEZ TOLERANCJI, bo są liczbami zdarzeń, nie miarą fizyczną.
        # 463 -> ? (14.09.2026, MB-08): dziesięć pinów liczbowych w testach drzwi —
        # `ManualDoorsTests` (liczby kroków cyklu ręcznego: 1021, 1020, długości faz)
        # i `ManualDoorsOnLineTests` (nietknięty kilometraż przy otwartych drzwiach).
        # SZEŚĆ z nich ma tolerancję ZAPISANĄ JAKO 0.0, bo pytanie brzmi tam „ani jeden
        # bit", a nie „w przybliżeniu". `calkowite_z_tolerancja` zostaje ZEREM.
        # WSZYSTKIE liczby niżej są PRZELICZONE na drzewie po scaleniu obu gałęzi.
        # 473 -> 474 (14.09.2026, 6.D210): JEDEN pin liczbowy nowego pliku
        # `DefaultArmAuditTests.cs` — podłoga `MinimumSwitches` porównywana z liczbą
        # znalezionych switchy. CAŁKOWITY i BEZ TOLERANCJI, bo jest liczbą miejsc
        # w kodzie, nie miarą fizyczną; `calkowite_z_tolerancja` zostaje ZEREM.
        # 474 -> 477 (14.09.2026, 6.D211): TRZY piny liczbowe bramki na połykanych
        # członach — raz „deklaracji metody jest DOKŁADNIE jedna" i dwa razy „switchy
        # po tym wyliczeniu jest DOKŁADNIE jeden" (w bramce drzewa i w pomocniku,
        # którego woła także kontrola przyrządu). Wszystkie CAŁKOWITE i BEZ TOLERANCJI,
        # bo są liczbami miejsc w kodzie; `calkowite_z_tolerancja` zostaje ZEREM.
        # Pin `PolykaneCzlony.Length == sprawdzonych` do tej liczby NIE wchodzi: obie
        # strony są wyrażeniami, a nie literałem.
        # 477 -> 479 (17.09.2026, 6.D231): DWA piny liczbowe kontroli przyrzadu
        # czytnika korpusu — dwa razy „deklaracji jest DOKLADNIE jedna", raz przy
        # metodzie wyrazeniowej (straz ma byc SPELNIONA, bo na tym polegala usterka)
        # i raz przy jej klamrowej sasiadce w kontroli DODATNIEJ. Oba CALKOWITE
        # i BEZ TOLERANCJI, bo sa liczbami miejsc w kodzie, nie miara fizyczna;
        # `calkowite_z_tolerancja` zostaje ZEREM.
        # 479 -> 480 (17.09.2026, 6.D229): JEDEN pin liczbowy bramki
        # `BrokenJsonRefusalTests.cs` — podloga na liczbe przejrzanych par
        # loader x ksztalt. CALKOWITY i BEZ TOLERANCJI, bo jest liczba przebiegow
        # petli, nie miara fizyczna. Przeliczone z drzewa po scaleniu.
        # 481 -> 488 (22.09.2026, 6.M2): SIEDEM pinow calkowitych bez tolerancji
        # w `StopWindowParityTests.cs` (liczby wywolan, liczba minietych, liczba
        # krokow postoju). Przeliczone z drzewa.
# 488 -> 493 (23.09.2026, 6.M1): PIĘĆ pinów `LineReplayTests.cs` — cztery
# całkowite bez tolerancji (liczby zdarzeń, poleceń drzwi, zdarzeń jednego kroku,
# zdarzeń kroku obok) i jeden zmiennoprzecinkowy z tolerancją 0.0 (skład stoi).
# Przeliczone z drzewa.
        # 493 -> 496 (23.09.2026, 6.M3): TRZY piny calkowite bez tolerancji w testach
        # okna drzwi (liczby wywolan i krokow z otwartymi drzwiami). Przeliczone z drzewa.
        # 496 -> 498 (23.09.2026, 6.D357): DWA piny `BrokenJsonRefusalTests.cs` —
        # zero slow wspolnych z tekstem parsera i podloga 10 par loader x ksztalt
        # w nowej bramce. Oba CALKOWITE i BEZ TOLERANCJI, bo sa liczbami, nie miara
        # fizyczna; `calkowite_z_tolerancja` zostaje ZEREM. ZMIERZONE.
        # 498 -> 501 (23.09.2026, 6.D356): TRZY piny calkowite bez tolerancji
        # w `BrokenJsonRefusalTests.cs` — dwa razy kod wyjscia 1 i podloga na liczbe
        # przejrzanych ksztaltow. Przeliczone z drzewa; ZMIERZONE.
        # 501 -> 505 (24.09.2026): three station/step pins and one
        # chainage pin with exact 0.0 tolerance for mid-axis admission.
        # 505 -> 508 (24.09.2026, T-320): plan wejść i dwie granice obiegu.
        # 508 -> 512 (24.09.2026, T-320): kroki, stacja i liczba składów.
        # 512 -> 513 (24.09.2026, T-320): liczba przejść obiegu.
        # 513 -> 515 (24.09.2026, T-320): niezmieniony krok i dwa kursy planu.
        # 515 -> 517 (24.09.2026, koniec osi): odległość i zerowa prędkość.
        # 517 -> 523 (24.09.2026, LineDrive): granica Merode, prędkość, ślad i bilans.
        "razem": 523, "z_tolerancja": 191, "bez_tolerancji": 332,
        "zmiennoprzecinkowe": 206, "zmiennoprzecinkowe_bez_tolerancji": 15,
        "calkowite": 317, "calkowite_z_tolerancja": 0, "tolerancja_zero": 121,
    },
}

#: **Dwa wnioski, które nie są statystyką.**
#:
#: `calkowite_z_tolerancja` wynosi **zero w obu katalogach** — tolerancja jest wyłącznie
#: rzeczą zmiennoprzecinkową. Nie jest to przypadek ani zwyczaj: `Assert.AreEqual(int,
#: int, double)` nie ma przeciążenia, więc pin całkowity z tolerancją nie skompilowałby
#: się. Zapadka z obu stron na tej zerowej liczbie pilnuje, żeby zdanie zostało prawdziwe.
#:
#: **Porównań DOKŁADNYCH na liczbie zmiennoprzecinkowej jest 160, nie 21.** Dwadzieścia
#: jeden nie ma trzeciego argumentu wcale, a **139 podaje tolerancję `0.0`** — czyli deklaruje
#: dokładność jawnie. Sama liczba „21" byłaby znacznie zaniżona i to jest
#: dokładnie ten kształt, który projekt tropi od 6.D27: licznik mówiący o czymś węższym,
#: niż sugeruje jego nazwa.
# 146 -> 145 (14.09.2026, MB-07): zniknal `AreEqual(0.0, …SpeedMps, 0.0)`
# z przepisanego testu zatoru — powod przy `ROZKLAD_LICZBOWYCH["tests/Sim.Tests"]`.
# 145 -> 151 (14.09.2026, MB-08): sześć porównań z tolerancją 0.0 w testach
# drzwi; `zmiennoprzecinkowe_bez_tolerancji` stoi w miejscu na ośmiu.
# 151 -> 152 (23.09.2026, 6.M1): jedno porównanie z tolerancją 0.0 w `LineReplayTests.cs`.
# 152 -> 153 (24.09.2026, next station after mid-axis entry).
# 153 -> 155 (24.09.2026, koniec osi): dwa dokładne porównania prędkości.
# 155 -> 160 (24.09.2026, LineDrive): pięć dokładnych porównań bez tolerancji.
DOKLADNE_ZMIENNOPRZECINKOWE = 160


def test_ile_pinow_liczbowych_i_jak_sie_dziela():
    """Cztery liczby na katalog, wszystkie z drzewa."""
    for katalog, oczekiwany in ROZKLAD_LICZBOWYCH.items():
        zmierzony = CP.rozklad_liczbowych(katalog)
        assert zmierzony == oczekiwany, (
            "rozkład pinów liczbowych w %s zmienił się: %s zamiast %s"
            % (katalog, zmierzony, oczekiwany))


def test_pin_calkowity_NIGDY_nie_ma_tolerancji_i_to_nie_jest_zwyczaj():
    """Zapadka z obu stron na zerze — `Assert.AreEqual(int, int, double)` nie istnieje.

    Gdyby ta liczba przestała być zerem, znaczyłoby to albo że czytnik bierze za
    tolerancję coś, co nią nie jest, albo że ktoś pinuje liczbę całkowitą przez
    przeciążenie zmiennoprzecinkowe — i jedno, i drugie trzeba obejrzeć.
    """
    razem = sum(CP.rozklad_liczbowych(k)["calkowite_z_tolerancja"]
                for k in ROZKLAD_LICZBOWYCH)
    assert razem == 0, (
        "pin całkowity z tolerancją: %d — `Assert.AreEqual(int, int, double)` nie ma "
        "przeciążenia, więc albo czytnik się myli, albo ktoś przeszedł na `double`"
        % razem)


def test_dokladnych_porownan_zmiennoprzecinkowych_jest_160_a_nie_21():
    """**Sedno 6.D141: tolerancja `0.0` JEST porównaniem dokładnym.**

    Licznik „bez tolerancji" mówi o dwudziestu jeden asercjach, a dokładnych porównań na
    liczbie zmiennoprzecinkowej jest znacznie więcej — bo 139 podają tolerancję
    zapisaną jako `0.0`. Test liczy jedno i drugie, żeby ta różnica stała w kodzie,
    a nie tylko w raporcie.
    """
    bez = sum(CP.rozklad_liczbowych(k)["zmiennoprzecinkowe_bez_tolerancji"]
              for k in ROZKLAD_LICZBOWYCH)
    zero = sum(CP.rozklad_liczbowych(k)["tolerancja_zero"] for k in ROZKLAD_LICZBOWYCH)

    assert bez == 21, ("zmiennoprzecinkowych bez tolerancji: %d, pomiar mówił 21" % bez)
    # 132 -> 131 (14.09.2026, MB-07): patrz `ROZKLAD_LICZBOWYCH["tests/Sim.Tests"]`.
    # 131 -> 137 (14.09.2026, MB-08): sześć porównań z tolerancją 0.0 w nowych testach
    # drzwi — wszystkie tam, gdzie pytanie brzmi „ani jeden bit": nietknięty nastawnik,
    # nietknięty hamulec i nieruszony kilometraż przy otwierających się drzwiach.
    # 137 -> 138 (23.09.2026, 6.M1): jedno porównanie z tolerancją 0.0 w
    # `LineReplayTests.cs` — skład ma STAĆ przed otwarciem drzwi, ani jednego bitu ruchu.
    assert zero == 139, ("tolerancji zapisanych jako 0.0: %d, pomiar mówił 139" % zero)
    assert bez + zero == DOKLADNE_ZMIENNOPRZECINKOWE, (
        "porównań dokładnych jest %d, a stała mówi %d" % (bez + zero,
                                                          DOKLADNE_ZMIENNOPRZECINKOWE))


def test_pin_Z_TOLERANCJA_i_BEZ_daja_dwa_rozne_wpisy_na_wejsciu_syntetycznym():
    """Pole „Skończone, gdy" — pokazane na drzewie probnym, nie na dzisiejszym kodzie.

    Cztery asercje o tej samej wartości oczekiwanej, różniące się wyłącznie trzecim
    argumentem. Czytnik ma dać cztery wpisy i dwie różne tolerancje — `None` tam,
    gdzie trzeciego argumentu nie ma albo jest komunikatem.
    """
    import tempfile

    zrodlo = (
        "public class T {\n"
        "  public void A() {\n"
        "    Assert.AreEqual(1.5, x);\n"
        "    Assert.AreEqual(1.5, x, 1e-9);\n"
        '    Assert.AreEqual(1.5, x, "komunikat, nie tolerancja");\n'
        "    Assert.AreEqual(1.5, x, 0.0);\n"
        "    Assert.AreEqual(4L, y);\n"
        '    Assert.AreEqual("napis", z);\n'
        "  }\n"
        "}\n")

    with tempfile.TemporaryDirectory(prefix="metro-piny-") as katalog:
        with open(os.path.join(katalog, "Probne.cs"), "w", encoding="utf-8") as uchwyt:
            uchwyt.write(zrodlo)
        znalezione = CP.piny_liczbowe("", katalog)
        # Czytnik napisowy wołany W TYM SAMYM bloku `with`: poza nim katalog już
        # nie istnieje i `glob` zwraca pustą listę, czyli test mierzyłby brak plików
        # zamiast braku pinów. Zmierzone tutaj, w pierwszym przebiegu.
        napisowe = CP.piny("", katalog)

    tolerancje = [w[3] for w in znalezione]
    wartosci = [w[2] for w in znalezione]
    assert wartosci == ["1.5", "1.5", "1.5", "1.5", "4L"], wartosci
    assert tolerancje == [None, "1e-9", None, "0.0", None], (
        "czytnik nie odróżnia tolerancji od komunikatu ani od jej braku: %s" % tolerancje)

    # Pin NAPISOWY nie wchodzi do liczbowych, a liczbowy nie wchodzi do napisowych —
    # inaczej obie liczby mówiłyby o tym samym zbiorze.
    assert all(not w[2].startswith('"') for w in znalezione), znalezione
    assert [w[3] for w in napisowe] == ["napis"], (
        "czytnik napisowy zobaczył co innego niż jeden napis: %s" % napisowe)


def test_czytnik_liczbowy_tnie_argumenty_po_MASCE_a_nie_po_przecinkach():
    """Przecinek w literale napisowym i w zagnieżdżonym wywołaniu nie dzieli argumentów.

    Bez maski `Assert.AreEqual(1.5, f(a, b), 1e-9)` miałoby CZTERY argumenty i trzecim
    byłoby `b`, czyli tolerancją zostałaby nazwa zmiennej. Wejście syntetyczne, bo na
    dzisiejszym drzewie obie drogi dają to samo.
    """
    import tempfile

    # **Przecinek musi stać na GŁĘBOKOŚCI 1, żeby cokolwiek rozstrzygać** — i to jest
    # poprawka po kontroli, która wyszła ZIELONA. Pierwsza wersja tego wejścia miała
    # `g("x, y")`, czyli napis WEWNĄTRZ zagnieżdżonego wywołania: tam przecinek jest
    # na głębokości 2 i licznik nawiasów radzi sobie bez maski. KN-2 (cięcie po
    # oryginale) przeszła wtedy 10/10.
    zrodlo = (
        "public class T {\n"
        "  public void A() {\n"
        "    Assert.AreEqual(1.5, f(a, b), 1e-9);\n"
        '    Assert.AreEqual(2.5, "x, y".Length, 1e-3);\n'
        "  }\n"
        "}\n")

    with tempfile.TemporaryDirectory(prefix="metro-piny-") as katalog:
        with open(os.path.join(katalog, "Probne.cs"), "w", encoding="utf-8") as uchwyt:
            uchwyt.write(zrodlo)
        znalezione = CP.piny_liczbowe("", katalog)

    assert [(w[2], w[3]) for w in znalezione] == [("1.5", "1e-9"), ("2.5", "1e-3")], (
        "cięcie argumentów pomyliło zagnieżdżone wywołanie albo przecinek w napisie "
        "stojącym na głębokości 1: %s" % znalezione)


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

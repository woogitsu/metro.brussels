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

#: Piny warstwy gry per plik. **Zmierzone 11.09.2026 na `dfc7543`: 44 w ośmiu plikach.**
#: Zapadka działa w obie strony, jak przy asercjach bez komunikatu z 6.D127: w górę
#: mówi „doszedł pin, skategoryzuj go", w dół — „pin zniknął, zdejmij go z tabeli".
PINY_GRY = {
    "ChunkManifestTests.cs": 3,
    "HudLayoutTests.cs": 1,
    "RunHeaderTests.cs": 1,
    "RunPlanTests.cs": 30,
    "RunResetTests.cs": 2,
    "SignallingHudTests.cs": 1,
    "TelemetryTrackTests.cs": 1,
    "UiTextTests.cs": 5,
}

#: Ile pinów stoi w `tests/Sim.Tests` — liczba PORÓWNAWCZA, o którą prosiło pole
#: „Wejście". Rdzeń ma ich 74 przy 36 plikach, gra 44 przy 16: na plik wypada
#: **2,06** wobec **2,75**, więc gra pinuje GĘŚCIEJ, mimo że ma mniej testów.
PINY_RDZENIA = 74

#: Kategorie, po jednej pozycji na pin — zamknięte i sumujące się do liczby wyżej.
#:
#: **Podział jest ZAPISANY, a nie wyprowadzony regułą, i to jest wynik pomiaru.**
#: Próbowałem reguły po kształcie literału („zawiera interpunkt albo dwie spacje pod
#: rząd = wynik złożony"). Myli się na dwóch z czterech: **przepuszcza**
#: `UiTextTests.cs:501`, czyli wiersz o hamulcu awaryjnym, który jest złożony,
#: a rozdzielony pojedynczymi spacjami, i **łapie** `UiTextTests.cs:571`, który
#: pinem wyjścia nie jest wcale — to WEJŚCIE syntetyczne kontroli `BezDziur`.
#: Reguła myląca się w połowie przypadków jest gorsza niż wypisana tabela, bo
#: zmyśla kategorię tam, gdzie nikt nie patrzy.
#:
#: A — pin na wynik ZŁOŻONY z kilku źródeł. Niezbędny: wartość liczona z katalogu
#:     byłaby porównaniem katalogu z samym sobą. Pole „Skończone, gdy" pozycji 6.D99
#:     żądało wypisu tych samych wierszy wprost i to jest ta sama decyzja.
#: B — WEJŚCIE syntetyczne kontroli przyrządu. Nie jest pinem na wyjście programu;
#:     literał jest tu daną testu i inaczej zapisać się go nie da.
#: C — pin na wartość liczoną w JEDNYM miejscu: nazwa trybu, ścieżka, identyfikator.
KATEGORIE = {
    "A": {
        ("UiTextTests.cs", 490), ("UiTextTests.cs", 496), ("UiTextTests.cs", 501),
        ("SignallingHudTests.cs", 37),
    },
    "B": {
        ("UiTextTests.cs", 570), ("UiTextTests.cs", 571),
    },
}

#: Ile pinów wpada do kategorii C — reszta, liczona, nie wpisana.
LICZBA_C = 38


def test_ile_pinow_stoi_w_testach_warstwy_gry():
    """Liczba z drzewa, zapadka w obie strony — 6.D131."""
    zmierzone = CP.per_plik("tests/Game.Tests")

    assert zmierzone == PINY_GRY, (
        "piny warstwy gry rozjechały się z tabelą (zmierzone / zapisane): %s / %s "
        "— doszedł pin do skategoryzowania albo zniknął pin do zdjęcia"
        % (sorted(zmierzone.items()), sorted(PINY_GRY.items())))

    assert sum(zmierzone.values()) == 44, (
        "pinów warstwy gry jest %d, a pomiar z 11.09.2026 dał 44"
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
    assert len(KATEGORIE["A"]) + len(KATEGORIE["B"]) + LICZBA_C == 44, (
        "kategorie nie sumują się do 44: A=%d, B=%d, C=%d"
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

    assert przepuszczone == [("UiTextTests.cs", 501)], (
        "reguła po kształcie przestała przepuszczać wiersz o hamulcu awaryjnym — "
        "rozstrzygnięcie 6.D131 wymaga przeliczenia: %s" % przepuszczone)
    assert zlapane_z_b == [("UiTextTests.cs", 571)], (
        "reguła po kształcie przestała łapić wejście syntetyczne: %s" % zlapane_z_b)


def test_czytnik_widzi_pin_takze_wtedy_gdy_literal_jest_sklejony():
    """Kontrola przyrządu: `"…" + "…"` przez kilka wierszy to JEDEN pin.

    Trzy z czterech pinów kategorii A są tak zapisane. Czytnik biorący sam pierwszy
    człon podawałby ich długość jako ułamek prawdziwej — a długość jest jedyną
    rzeczą, po której widać, że pin trzyma CAŁY wiersz, a nie jego początek.
    """
    tresci = {(plik, wiersz): tresc
              for plik, wiersz, _r, tresc in CP.piny("tests/Game.Tests")}

    assert len(tresci[("UiTextTests.cs", 490)]) == 122, (
        "sklejanie literałów przestało działać: %d znaków"
        % len(tresci[("UiTextTests.cs", 490)]))
    assert len(tresci[("UiTextTests.cs", 501)]) == 98, (
        len(tresci[("UiTextTests.cs", 501)]))
    assert len(tresci[("SignallingHudTests.cs", 37)]) == 84, (
        len(tresci[("SignallingHudTests.cs", 37)]))

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
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

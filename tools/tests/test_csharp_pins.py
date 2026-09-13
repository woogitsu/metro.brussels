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
    "ChunkManifestTests.cs": 3,
    "HudLayoutTests.cs": 1,
    "RunHeaderTests.cs": 1,
    "RunPlanTests.cs": 30,
    "RunResetTests.cs": 2,
    "SignallingHudTests.cs": 1,
    "TelemetryTrackTests.cs": 1,
    "UiTextTests.cs": 8,
}

#: Ile pinów stoi w `tests/Sim.Tests` — liczba PORÓWNAWCZA, o którą prosiło pole
#: „Wejście". Rdzeń ma ich 74 przy 36 plikach, gra 47 przy 16: na plik wypada
#: **2,06** wobec **2,94**, więc gra pinuje GĘŚCIEJ, mimo że ma mniej testów.
PINY_RDZENIA = 74

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
KATEGORIE = {
    "A": {
        ("UiTextTests.cs", 1150), ("UiTextTests.cs", 1156), ("UiTextTests.cs", 1161),
        ("SignallingHudTests.cs", 37),
    },
    "B": {
        ("UiTextTests.cs", 1230), ("UiTextTests.cs", 1231),
    },
}

#: Ile pinów wpada do kategorii C — reszta, liczona, nie wpisana.
LICZBA_C = 41


def test_ile_pinow_stoi_w_testach_warstwy_gry():
    """Liczba z drzewa, zapadka w obie strony — 6.D131."""
    zmierzone = CP.per_plik("tests/Game.Tests")

    assert zmierzone == PINY_GRY, (
        "piny warstwy gry rozjechały się z tabelą (zmierzone / zapisane): %s / %s "
        "— doszedł pin do skategoryzowania albo zniknął pin do zdjęcia"
        % (sorted(zmierzone.items()), sorted(PINY_GRY.items())))

    assert sum(zmierzone.values()) == 47, (
        "pinów warstwy gry jest %d, a pomiar z 12.09.2026 dał 47 (45 przed 6.D155)"
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
    assert len(KATEGORIE["A"]) + len(KATEGORIE["B"]) + LICZBA_C == 47, (
        "kategorie nie sumują się do 47: A=%d, B=%d, C=%d"
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

    assert przepuszczone == [("UiTextTests.cs", 1161)], (
        "reguła po kształcie przestała przepuszczać wiersz o hamulcu awaryjnym — "
        "rozstrzygnięcie 6.D131 wymaga przeliczenia: %s" % przepuszczone)
    assert zlapane_z_b == [("UiTextTests.cs", 1231)], (
        "reguła po kształcie przestała łapić wejście syntetyczne: %s" % zlapane_z_b)


def test_czytnik_widzi_pin_takze_wtedy_gdy_literal_jest_sklejony():
    """Kontrola przyrządu: `"…" + "…"` przez kilka wierszy to JEDEN pin.

    Trzy z czterech pinów kategorii A są tak zapisane. Czytnik biorący sam pierwszy
    człon podawałby ich długość jako ułamek prawdziwej — a długość jest jedyną
    rzeczą, po której widać, że pin trzyma CAŁY wiersz, a nie jego początek.
    """
    tresci = {(plik, wiersz): tresc
              for plik, wiersz, _r, tresc in CP.piny("tests/Game.Tests")}

    assert len(tresci[("UiTextTests.cs", 1150)]) == 122, (
        "sklejanie literałów przestało działać: %d znaków"
        % len(tresci[("UiTextTests.cs", 1150)]))
    assert len(tresci[("UiTextTests.cs", 1161)]) == 98, (
        len(tresci[("UiTextTests.cs", 1161)]))
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
        "razem": 207, "z_tolerancja": 98, "bez_tolerancji": 109,
        "zmiennoprzecinkowe": 104, "zmiennoprzecinkowe_bez_tolerancji": 6,
        "calkowite": 103, "calkowite_z_tolerancja": 0, "tolerancja_zero": 18,
    },
    "tests/Sim.Tests": {
        "razem": 441, "z_tolerancja": 179, "bez_tolerancji": 262,
        "zmiennoprzecinkowe": 187, "zmiennoprzecinkowe_bez_tolerancji": 8,
        "calkowite": 254, "calkowite_z_tolerancja": 0, "tolerancja_zero": 114,
    },
}

#: **Dwa wnioski, które nie są statystyką.**
#:
#: `calkowite_z_tolerancja` wynosi **zero w obu katalogach** — tolerancja jest wyłącznie
#: rzeczą zmiennoprzecinkową. Nie jest to przypadek ani zwyczaj: `Assert.AreEqual(int,
#: int, double)` nie ma przeciążenia, więc pin całkowity z tolerancją nie skompilowałby
#: się. Zapadka z obu stron na tej zerowej liczbie pilnuje, żeby zdanie zostało prawdziwe.
#:
#: **Porównań DOKŁADNYCH na liczbie zmiennoprzecinkowej jest 146, nie 14.** Czternaście
#: nie ma trzeciego argumentu wcale, a **132 podaje tolerancję `0.0`** — czyli deklaruje
#: dokładność jawnie. Sama liczba „14" byłaby dziesięciokrotnie zaniżona i to jest
#: dokładnie ten kształt, który projekt tropi od 6.D27: licznik mówiący o czymś węższym,
#: niż sugeruje jego nazwa.
DOKLADNE_ZMIENNOPRZECINKOWE = 146


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


def test_dokladnych_porownan_zmiennoprzecinkowych_jest_146_a_nie_14():
    """**Sedno 6.D141: tolerancja `0.0` JEST porównaniem dokładnym.**

    Licznik „bez tolerancji" mówi o czternastu asercjach, a dokładnych porównań na
    liczbie zmiennoprzecinkowej jest dziesięć razy więcej — bo 132 podają tolerancję
    zapisaną jako `0.0`. Test liczy jedno i drugie, żeby ta różnica stała w kodzie,
    a nie tylko w raporcie.
    """
    bez = sum(CP.rozklad_liczbowych(k)["zmiennoprzecinkowe_bez_tolerancji"]
              for k in ROZKLAD_LICZBOWYCH)
    zero = sum(CP.rozklad_liczbowych(k)["tolerancja_zero"] for k in ROZKLAD_LICZBOWYCH)

    assert bez == 14, ("zmiennoprzecinkowych bez tolerancji: %d, pomiar mówił 14" % bez)
    assert zero == 132, ("tolerancji zapisanych jako 0.0: %d, pomiar mówił 132" % zero)
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

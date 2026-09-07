#!/usr/bin/env python3
"""Test oczekujacy wyjatku moze polec, gdy wyjatku nie ma (6.B33).

**Wzorzec, o ktory chodzi.** Ten projekt sprawdza odmowy tak:

    try { Cos(); } catch (FormatException error) { StringAssert.Contains(...); return; }
    Assert.Fail("zapis bez liczby krokow zostal przyjety - ...");

Cala wyrocznia siedzi w `Assert.Fail` **za** blokiem `try`/`catch`. Gdy kod przestanie
rzucac, wykonanie dochodzi do tego wiersza i test pada. Bez niego test przechodzi
w milczeniu — asercje w `catch` nie wykonuja sie wcale, bo `catch` nie jest wchodzony.

**Stan zmierzony 07.09.2026:** dwanascie metod testowych uzywa tego wzorca i WSZYSTKIE
dwanascie maja `Assert.Fail` na wlasciwym miejscu. Ta bramka nie naprawia wiec niczego
— pilnuje, zeby trzynasta bez niego nie przeszla w milczeniu. To ta sama klasa co
6.B27, gdzie objawem brakujacego `[TestMethod]` byla wylacznie liczba testow.

**Uwaga o pulapce, na ktora wpadl moj wlasny dorazny detektor**, i dlatego stoi tu
napisana, a nie zapomniana: pierwsza wersja szukala `Assert.Fail` **wewnatrz** bloku
`try` i zglosila wszystkie dwanascie jako usterke. Zero z nich nia bylo. Bramka
zbudowana na tym odruchu zapalilaby sie na dwunastu poprawnych testach i zostalaby
wylaczona, nie naprawiona — nauczka 6.D27.

**Czego bramka NIE lapie, i to jest zmierzone, nie zalozone.** `try`/`finally` BEZ
`catch` (dziesiec wystapien w drzewie, wszystkie to sprzatanie plikow tymczasowych)
nie jest tym wzorcem: wyjatek tam nie ginie, leci dalej i wywala test glosno.
`catch`, ktory rzuca ponownie (`throw;`), tez nie — wyjatek nie jest pochloniety.
Bramka kluczuje wiec na `catch` POCHLANIAJACYM wyjatek, nie na obecnosci `try`.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csharp_test_methods as CTM  # noqa: E402

#: Ile wystapien wzorca bramka ma widziec co najmniej. ZMIERZONE 07.09.2026: **12**.
#: Prog istnieje z tego samego powodu, co przy 6.B29, 6.B31, 6.D27 i 6.A14: bramka
#: szukajaca wzorca, ktory przez literowke nie pasuje do niczego, melduje zero
#: znalezisk i swieci na zielono. Podnosi sie razem z przybyciem wystapien.
MINIMUM_WYSTAPIEN = 12

TRY = re.compile(r"\btry\b")
KLAUZULA = re.compile(r"\s*(catch|finally)\b[^{]*\{", re.S)


def _metody_testowe(root=CTM.ROOT):
    """`[(plik, klasa, metoda, cialo)]` dla metod z atrybutem testowym."""
    out = []
    for path in CTM.pliki(root):
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        maska_zrodla = CTM.maska(source)
        for klasa in CTM.KLASA.finditer(source):
            cialo_klasy = CTM._cialo_klasy(source, klasa.end(), maska_zrodla)
            for naglowek, cialo in CTM.czlonkowie(cialo_klasy):
                match = None
                for match in CTM.METODA.finditer(naglowek + "{"):
                    pass
                if match is None or not CTM.NAGLOWEK.search(naglowek.strip()):
                    continue
                if not any(a in match.group("attrs") for a in CTM.ATRYBUTY_TESTU):
                    continue
                out.append((os.path.relpath(path, root), klasa.group(1),
                            match.group("name"), cialo))
    return out


def wystapienia(cialo):
    """`[(pochlania, tekst_za_calym_try)]` dla kazdego `try` w ciele metody.

    Klamry liczone na masce (`CTM.maska`), zeby `{` w napisie nie konczylo bloku —
    bez tego przejscie gubi sie dokladnie tak, jak gubila sie bramka 6.B27 przed 6.B28.
    """
    maska = CTM.maska(cialo)
    out = []
    for start_try in TRY.finditer(maska):
        try:
            otwarcie = maska.index("{", start_try.end())
        except ValueError:
            continue
        indeks = CTM._koniec_bloku(maska, otwarcie)
        pochlania = False
        while True:
            klauzula = KLAUZULA.match(maska[indeks:])
            if not klauzula:
                break
            otwarcie_klauzuli = maska.index("{", indeks)
            koniec = CTM._koniec_bloku(maska, otwarcie_klauzuli)
            if (klauzula.group(1) == "catch"
                    and "throw" not in maska[otwarcie_klauzuli:koniec]):
                pochlania = True
            indeks = koniec
        out.append((pochlania, cialo[indeks:]))
    return out


def offenders(root=CTM.ROOT):
    """Metody z `catch` pochlaniajacym wyjatek i BEZ asercji za calym `try`."""
    zle = []
    for plik, klasa, metoda, cialo in _metody_testowe(root):
        for pochlania, po in wystapienia(cialo):
            # `Assert.Fail` szukane na MASCE, nie w surowym tekscie — inaczej
            # zakomentowane wywolanie (albo wzmianka w napisie) liczy sie jako
            # asercja. Znalezione WLASNA kontrola negatywna: KN-1 podmienil
            # prawdziwe `Assert.Fail(...)` na komentarz „// Assert.Fail zdjety"
            # i bramka zostala zielona, bo podciag nadal byl w pliku. To ta sama
            # usterka, ktora 6.B34 opisuje dla bramki martwych stalych — tylko ze
            # tutaj daje FALSZYWY NEGATYW w bramce pisanej wlasnie po to, zeby
            # falszywych negatywow nie bylo.
            if pochlania and "Assert.Fail" not in CTM.maska(po):
                zle.append((plik, klasa, metoda))
    return zle


def ile_wystapien(root=CTM.ROOT):
    """Ile razy wzorzec „catch pochlaniajacy wyjatek" wystepuje w metodach testowych."""
    ile = 0
    for _plik, _klasa, _metoda, cialo in _metody_testowe(root):
        ile += sum(1 for pochlania, _po in wystapienia(cialo) if pochlania)
    return ile


def _zapisz(katalog, zrodlo):
    os.makedirs(os.path.join(katalog, "tests", "Udawane"), exist_ok=True)
    with open(os.path.join(katalog, "tests", "Udawane", "W.cs"), "w",
              encoding="utf-8") as handle:
        handle.write(zrodlo)


def _klasa(cialo):
    return ("using Microsoft.VisualStudio.TestTools.UnitTesting;\n"
            "namespace X;\n[TestClass]\npublic sealed class Wstrzykniete\n{\n"
            + cialo + "}\n")


def test_every_expected_exception_test_can_fail_when_nothing_throws():
    """Zadna metoda z pochlaniajacym `catch` nie stoi bez asercji za `try`."""
    zle = offenders()
    assert zle == [], (
        "test oczekujacy wyjatku przejdzie w milczeniu, gdy wyjatek nie zostanie "
        "rzucony — brakuje `Assert.Fail` za blokiem try/catch: "
        + ", ".join("%s :: %s.%s" % x for x in zle))


def test_the_gate_sees_the_pattern_it_is_supposed_to_see():
    """Prog na liczbe wystapien — literowka we wzorcu ma dawac FAIL, nie zero."""
    ile = ile_wystapien()
    assert ile >= MINIMUM_WYSTAPIEN, (
        "wzorzec rozpoznany %d razy przy progu %d — albo testy oczekujace wyjatku "
        "ubyly, albo przejscie po ciele metody przestalo pasowac; jedno i drugie "
        "trzeba zobaczyc, a nie przegapic" % (ile, MINIMUM_WYSTAPIEN))


def test_a_try_finally_without_catch_is_not_the_pattern():
    """Sprzatanie plikow tymczasowych to NIE oczekiwany wyjatek.

    W drzewie jest dziesiec takich blokow (`finally { File.Delete(...) }`). Wyjatek
    tam nie ginie — leci dalej i wywala test glosno — wiec zadanie od nich
    `Assert.Fail` byloby bramka zapalajaca sie na poprawnym kodzie.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as katalog:
        _zapisz(katalog, _klasa(
            "    [TestMethod]\n"
            "    public void Sprzatanie()\n"
            "    {\n"
            "        try\n"
            "        {\n"
            "            Assert.IsTrue(true);\n"
            "        }\n"
            "        finally\n"
            "        {\n"
            "            System.IO.File.Delete(\"/tmp/nie-ma.txt\");\n"
            "        }\n"
            "    }\n"))
        assert offenders(katalog) == [], (
            "try/finally bez catch wziete za wzorzec oczekiwanego wyjatku")
        assert ile_wystapien(katalog) == 0, (
            "try/finally bez catch policzone jako wystapienie wzorca")


def test_a_rethrowing_catch_is_not_the_pattern():
    """`catch { ...; throw; }` nie pochlania wyjatku, wiec nie jest tym wzorcem."""
    import tempfile

    with tempfile.TemporaryDirectory() as katalog:
        _zapisz(katalog, _klasa(
            "    [TestMethod]\n"
            "    public void Rzuca_ponownie()\n"
            "    {\n"
            "        try\n"
            "        {\n"
            "            Assert.IsTrue(true);\n"
            "        }\n"
            "        catch (System.Exception)\n"
            "        {\n"
            "            throw;\n"
            "        }\n"
            "    }\n"))
        assert offenders(katalog) == [], "catch z `throw;` wziety za pochlaniajacy"
        assert ile_wystapien(katalog) == 0, "catch z `throw;` policzony jako wzorzec"


def test_the_detector_lights_up_on_a_test_without_assert_fail():
    """Kontrola dodatnia jako TEST, nie jako zdanie w docstringu (wzorzec 6.B24)."""
    import tempfile

    with tempfile.TemporaryDirectory() as katalog:
        _zapisz(katalog, _klasa(
            "    [TestMethod]\n"
            "    public void Bez_Assert_Fail()\n"
            "    {\n"
            "        try\n"
            "        {\n"
            "            Cos();\n"
            "        }\n"
            "        catch (System.FormatException)\n"
            "        {\n"
            "            Assert.IsTrue(true);\n"
            "            return;\n"
            "        }\n"
            "    }\n"
            "\n"
            "    [TestMethod]\n"
            "    public void Z_Assert_Fail()\n"
            "    {\n"
            "        try\n"
            "        {\n"
            "            Cos();\n"
            "        }\n"
            "        catch (System.FormatException)\n"
            "        {\n"
            "            Assert.IsTrue(true);\n"
            "            return;\n"
            "        }\n"
            "\n"
            "        Assert.Fail(\"nie rzucil\");\n"
            "    }\n"))
        zle = offenders(katalog)
        assert [m for _, _, m in zle] == ["Bez_Assert_Fail"], (
            "detektor nie zobaczyl testu bez `Assert.Fail` albo zglosil takze ten "
            "poprawny: " + repr(zle))
        assert ile_wystapien(katalog) == 2, (
            "oba wystapienia wzorca maja byc policzone, nie tylko zle")


def test_a_commented_out_assert_fail_does_not_count():
    """Zakomentowane `Assert.Fail` nie jest asercja — i to jest wynik kontroli.

    Ten test istnieje, bo **moja wlasna kontrola negatywna go wymusila**: KN-1
    podmienil prawdziwe `Assert.Fail(...)` w `InputLogTests.cs` na komentarz
    zawierajacy te nazwe, a bramka zostala ZIELONA — szukala podciagu w surowym
    tekscie. Bramka pisana po to, zeby lapac cichy falszywy negatyw, sama miala
    falszywy negatyw. Dziś `Assert.Fail` szukane jest na masce (`CTM.maska`).
    """
    import tempfile

    with tempfile.TemporaryDirectory() as katalog:
        _zapisz(katalog, _klasa(
            "    [TestMethod]\n"
            "    public void Zakomentowany_Assert_Fail()\n"
            "    {\n"
            "        try\n"
            "        {\n"
            "            Cos();\n"
            "        }\n"
            "        catch (System.FormatException)\n"
            "        {\n"
            "            Assert.IsTrue(true);\n"
            "            return;\n"
            "        }\n"
            "\n"
            "        // Assert.Fail(\"zdjete przy jakiejs poprawce\");\n"
            "    }\n"))
        zle = offenders(katalog)
        assert [m for _, _, m in zle] == ["Zakomentowany_Assert_Fail"], (
            "zakomentowane Assert.Fail policzone jako asercja: " + repr(zle))


def test_the_detector_is_not_fooled_by_a_brace_in_a_string():
    """Klamra w napisie nie konczy bloku — inaczej `catch` wypadnie poza pomiar.

    Ta sama usterka, ktora do 6.B28 sprawiala, ze bramka 6.B27 nie widziala 27 metod;
    tutaj sprawdzana wprost, bo `Assert.Fail` niesie zwykle komunikat z cudzyslowami.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as katalog:
        _zapisz(katalog, _klasa(
            "    [TestMethod]\n"
            "    public void Klamra_w_napisie()\n"
            "    {\n"
            "        try\n"
            "        {\n"
            "            Cos(\"}\");\n"
            "        }\n"
            "        catch (System.FormatException)\n"
            "        {\n"
            "            Assert.IsTrue(true);\n"
            "            return;\n"
            "        }\n"
            "    }\n"))
        zle = offenders(katalog)
        assert [m for _, _, m in zle] == ["Klamra_w_napisie"], (
            "klamra w napisie zgubila blok catch: " + repr(zle))


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

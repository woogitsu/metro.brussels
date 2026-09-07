#!/usr/bin/env python3
"""Bramka: kazda metoda testowa C# ma w tresci asercje.

Powod, granice i pomiary — w docstringu `tools/tests/csharp_assertions.py`.
Ten modul sprawdza dwie rzeczy osobno: **drzewo** (zero metod bez asercji) i **czytnik**
(czy widzi oba ksztalty ciala, pomocnika `Assert*`, i czy zglasza brak, gdy brak jest).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csharp_assertions as CA  # noqa: E402
import csharp_test_methods as CTM  # noqa: E402

#: Ile metod testowych bramka ma WIDZIEC, zeby pomiar byl pomiarem. Bez tego progu
#: literowka w czytniku dalaby zero metod, zero brakow i zielona bramke — ta sama
#: pulapka, ktora zamyka `MINIMUM_CLAIMS` w `test_report_claims.py` i prog deklaracji
#: w `test_dead_constants_csharp.py`. Zmierzone 07.09.2026: **674**.
MINIMUM_METOD = 600


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
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

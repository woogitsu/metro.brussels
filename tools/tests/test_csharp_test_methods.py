#!/usr/bin/env python3
"""Bramka: metoda, ktora wyglada jak test C#, jest uruchamiana.

**Skad.** 06.09.2026 przy 6.A16, na moim wlasnym commicie: przepisujac komentarz nad
testem, atrybut `[TestMethod]` zostal wyciety razem z nim. Metoda zostala w pliku,
miala asercje, wygladala jak test — i nie byla uruchamiana. Zestaw C# przeszedl
**545/545 mimo obecnego bledu**; objawem nie byl zaden `FAIL`, tylko liczba testow
o jeden mniejsza i mutacja, ktora nie miala czego wywrocic.

Zestaw Pythona ma na to `assertion_gate` od #139 — test bez ani jednej asercji liczy
sie tam jako PORAZKA. Po stronie C# nie bylo nic.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csharp_test_methods as czytnik  # noqa: E402


def test_no_method_looks_like_a_test_and_is_not_run():
    brakujace = czytnik.bez_atrybutu()
    assert not brakujace, (
        "metody o ksztalcie testu bez [TestMethod] — nie sa uruchamiane: "
        + ", ".join("%s :: %s.%s" % x for x in brakujace))


def test_the_reader_actually_sees_the_tests():
    """Bramka na pustym zbiorze przechodzi zawsze. Ten test pilnuje, ze czytnik
    naprawde cos widzi — inaczej pierwszy zepsuty regex zamienilby ja w ozdobe."""
    dane = czytnik.coverage()
    assert dane["objete_ksztaltem"] > 100, dane
    assert dane["atrybuty_w_plikach"] >= dane["objete_ksztaltem"], dane


def test_the_gap_is_named_not_hidden():
    """Ksztalt bramki nie obejmuje metod Z ARGUMENTAMI, czyli `[DataTestMethod]`
    z wierszami `[DataRow]`. Luka ma byc WIDOCZNA LICZBOWO, a nie tylko opisana
    w komentarzu — inaczej za rok nikt nie bedzie wiedzial, jak duza jest."""
    dane = czytnik.coverage()
    assert dane["poza_ksztaltem"] == (
        dane["atrybuty_w_plikach"] - dane["objete_ksztaltem"]), dane
    assert dane["poza_ksztaltem"] >= 0, dane


def test_a_nested_helper_is_not_mistaken_for_a_test():
    """`Reset()` w zagniezdzonym przyrzadzie `RunResetTests` jest publiczna,
    bezargumentowa metoda `void` i NIE jest testem. Gdyby bramka liczyla glebokosc
    zle, zglaszalaby go przy kazdym przebiegu i skonczylaby wylaczona."""
    nazwy = [m for _, _, m, _ in czytnik.metody()]
    assert "Reset" not in nazwy, (
        "pomocnik z zagniezdzonej klasy wziety za metode testowa")


def test_the_shape_is_recognised_on_an_injected_class(tmp=None):
    """Kontrola wstrzykiwana: dwie metody, jedna z atrybutem, jedna bez."""
    import tempfile

    zrodlo = (
        "using Microsoft.VisualStudio.TestTools.UnitTesting;\n"
        "namespace X;\n"
        "[TestClass]\n"
        "public sealed class Wstrzykniete\n"
        "{\n"
        "    [TestMethod]\n"
        "    public void Uruchamiany()\n"
        "    {\n"
        "        Assert.IsTrue(true);\n"
        "    }\n"
        "\n"
        "    /// <summary>Stracil atrybut.</summary>\n"
        "    public void Nieuruchamiany()\n"
        "    {\n"
        "        Assert.IsTrue(true);\n"
        "    }\n"
        "}\n"
    )
    with tempfile.TemporaryDirectory() as katalog:
        os.makedirs(os.path.join(katalog, "tests", "Udawane"))
        with open(os.path.join(katalog, "tests", "Udawane", "W.cs"), "w",
                  encoding="utf-8") as handle:
            handle.write(zrodlo)
        znalezione = czytnik.metody(katalog)
        assert len(znalezione) == 2, znalezione
        brak = czytnik.bez_atrybutu(katalog)
        assert [m for _, _, m in brak] == ["Nieuruchamiany"], brak

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

#: Ile metod testowych czytnik ma widziec co najmniej. ZMIERZONE 07.09.2026 po
#: naprawie liczenia klamr (6.B28): **719**, czyli wszystkie atrybuty testowe
#: w `tests/`. Prog stoi tu, bo poprzedni (`> 100`) byl spelniony rowniez wtedy,
#: gdy czytnik gubil 27 prawdziwych metod na napisach z klamrami — i wlasnie dlatego
#: nikt tego nie zauwazyl przez dobe. Podnosi sie razem z przybyciem testow.
MINIMUM_WIDZIANYCH = 700


def test_no_method_looks_like_a_test_and_is_not_run():
    brakujace = czytnik.bez_atrybutu()
    assert not brakujace, (
        "metody o ksztalcie testu bez [TestMethod] — nie sa uruchamiane: "
        + ", ".join("%s :: %s.%s" % x for x in brakujace))


def test_the_reader_actually_sees_the_tests():
    """Bramka na pustym zbiorze przechodzi zawsze, a na PRAWIE pustym — prawie zawsze.

    **Prog przepisany 07.09.2026, nie dopisany obok.** Poprzednia wersja zadala
    `> 100` i byla spelniona takze wtedy, gdy czytnik gubil 27 prawdziwych metod
    na napisach z klamrami (6.B28). Prog, ktory przechodzi przy dwoch trzecich
    zgubionego zbioru, nie mierzy niczego.
    """
    dane = czytnik.coverage()
    assert dane["objete_ksztaltem"] >= MINIMUM_WIDZIANYCH, (
        "czytnik widzi %d metod przy progu %d — albo testy ubyly, albo przejscie "
        "po ciele klasy znow sie rozjezdza" % (dane["objete_ksztaltem"],
                                               MINIMUM_WIDZIANYCH))
    assert dane["atrybuty_w_plikach"] >= dane["objete_ksztaltem"], dane


def test_the_shape_covers_every_test_attribute():
    """Ksztalt obejmuje KAZDY atrybut testowy w plikach — luka jest zerem (6.B28).

    Do 07.09.2026 ksztalt zadal pustych nawiasow, wiec 13 metod `[DataTestMethod]`
    zostawalo poza nim; test w tym miejscu sprawdzal wtedy jedynie, ze luka jest
    **nazwana liczbowo**. Dziś jest zamknieta, wiec test zada zera — inaczej
    „nazwana luka" zostalaby na zawsze jako stan docelowy.
    """
    dane = czytnik.coverage()
    assert dane["poza_ksztaltem"] == (
        dane["atrybuty_w_plikach"] - dane["objete_ksztaltem"]), dane
    assert dane["poza_ksztaltem"] == 0, (
        "%d atrybutow testowych jest poza ksztaltem bramki — metoda, ktora straci "
        "atrybut w tej rodzinie, nie zostanie zauwazona: %s"
        % (dane["poza_ksztaltem"], dane))


def test_a_data_test_method_without_its_attribute_is_named():
    """Kontrola wstrzykiwana dla rodziny, ktora 6.B28 wciagnela w ksztalt.

    Metoda z `[DataRow]`, ale bez `[DataTestMethod]`, jest tak samo nieuruchamiana
    jak metoda bez `[TestMethod]` — i ma byc zgloszona Z IMIENIA, bo to jedyny
    slad, jaki dostaje czytajacy.
    """
    import tempfile

    zrodlo = (
        "using Microsoft.VisualStudio.TestTools.UnitTesting;\n"
        "namespace X;\n"
        "[TestClass]\n"
        "public sealed class Wiersze\n"
        "{\n"
        "    [DataTestMethod]\n"
        "    [DataRow(1.0)]\n"
        "    public void Uruchamiany(double x)\n"
        "    {\n"
        "        Assert.IsTrue(x > 0.0);\n"
        "    }\n"
        "\n"
        "    [DataRow(1.0)]\n"
        "    public void Stracil_DataTestMethod(double x)\n"
        "    {\n"
        "        Assert.IsTrue(x > 0.0);\n"
        "    }\n"
        "}\n"
    )
    with tempfile.TemporaryDirectory() as katalog:
        os.makedirs(os.path.join(katalog, "tests", "Udawane"))
        with open(os.path.join(katalog, "tests", "Udawane", "W.cs"), "w",
                  encoding="utf-8") as handle:
            handle.write(zrodlo)
        brak = czytnik.bez_atrybutu(katalog)
        assert [m for _, _, m in brak] == ["Stracil_DataTestMethod"], brak


def test_a_brace_inside_a_string_is_not_a_block():
    """Sedno 6.B28: `{` i `}` w napisie nie sa klamrami bloku.

    Klasa nizej ma pomocnika blokowego, ktorego cialo zawiera napis z **niesparowana**
    klamra zamykajaca — to jest ksztalt, na ktorym przejscie rozjezdzalo sie naprawde:
    `ServiceDayTests.cs` (16 metod testowych) dawal ZERO widzianych metod,
    `SignallingPlanTests.cs` (15) — cztery. Bez maski walk konczy blok pomocnika na
    klamrze STOJACEJ W NAPISIE, a prawdziwa klamre zamykajaca metody bierze za koniec
    ciala klasy i przestaje szukac; wszystko za pomocnikiem staje sie niewidzialne.

    **Pierwsza wersja tego testu przechodzila rowniez BEZ maski** — pomocnicy byli
    wyrazeniowi (`=> "..."`), a tam klamry w napisie trafialy do licznika nawiasow,
    ktory i tak konczyl na `;`, wiec kontrola negatywna nie miala czego wywrocic.
    Test opisywal wtedy wlasna niewiedze jako brak usterki. Przepisany na ksztalt
    blokowy, ktory KN-1 topi.

    Dalsze trzy pomocniki biora pozostale postacie napisu wystepujace w `tests/`:
    `@"..."`, `$"..."` i surowa otwierana trzema cudzyslowami.
    """
    import tempfile

    trzy = '"' * 3
    zrodlo = (
        "using Microsoft.VisualStudio.TestTools.UnitTesting;\n"
        "namespace X;\n"
        "[TestClass]\n"
        "public sealed class Klamrowe\n"
        "{\n"
        "    private static string Niesparowana()\n"
        "    {\n"
        '        return "}";\n'
        "    }\n"
        "\n"
        '    private static string Verbatim() => @"{""a"": 1}";\n'
        '    private static string Interpolowany(int x) => $"{{a: {x}}}";\n'
        "    private static string Surowy()\n"
        "    {\n"
        # Tresc `"}` jest wybrana POMIAREM, nie dla ozdoby: przy zdjetej obsludze
        # literalu surowego (KN-3) cudzyslowy paruja sie tak, ze ta klamra ląduje
        # w pozycji kodu i topi test stojacy nizej. Trzy inne tresci, w tym pelny
        # JSON, przechodza w obu wariantach — czyli nie mierzylyby niczego.
        "        return " + trzy + "\n"
        '        "}\n'
        "        " + trzy + ";\n"
        "    }\n"
        "\n"
        "    [TestMethod]\n"
        "    public void Za_pomocnikami_z_klamrami()\n"
        "    {\n"
        "        Assert.IsNotNull(Niesparowana());\n"
        "    }\n"
        "\n"
        "    public void Stracil_atrybut_za_pomocnikami()\n"
        "    {\n"
        "        Assert.IsNotNull(Surowy());\n"
        "    }\n"
        "}\n"
    )
    with tempfile.TemporaryDirectory() as katalog:
        os.makedirs(os.path.join(katalog, "tests", "Udawane"))
        with open(os.path.join(katalog, "tests", "Udawane", "W.cs"), "w",
                  encoding="utf-8") as handle:
            handle.write(zrodlo)
        nazwy = [m for _, _, m, _ in czytnik.metody(katalog)]
        assert "Za_pomocnikami_z_klamrami" in nazwy, (
            "test stojacy ZA pomocnikiem z klamra w napisie jest niewidzialny — "
            "przejscie po ciele klasy liczy klamry w literalach: " + repr(nazwy))
        assert "Stracil_atrybut_za_pomocnikami" in nazwy, (
            "metoda bez atrybutu za pomocnikami jest niewidzialna: " + repr(nazwy))
        brak = czytnik.bez_atrybutu(katalog)
        assert [m for _, _, m in brak] == ["Stracil_atrybut_za_pomocnikami"], brak


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

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

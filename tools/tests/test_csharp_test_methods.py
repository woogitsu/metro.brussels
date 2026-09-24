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
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csharp_test_methods as czytnik  # noqa: E402

#: Korzen repozytorium — 6.D226 czyta oba pliki tabeli ze ZRODLA.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

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

#: Zapisow `@"""` (werbatim otwarty cudzyslowem uciekanym) w `tests/` i `src/`.
#: ZMIERZONE 13.09.2026 przy 6.D200 czytnikiem, ktory te pozycje naprawia: **jeden**,
#: i stoi w KOMENTARZU (`tests/Game.Tests/UiTextTests.cs`, akapit opisujacy te wlasnie
#: usterke). Zywych wystapien jest **zero**, bo obejscie z 6.D188 przepisalo tamten
#: wzorzec na zwykly napis z uciekanymi cudzyslowami.
#:
#: **Dlatego ta liczba NIE jest dowodem naprawy i nie moze nim byc.** Korpus tej
#: galezi nie cwiczy — gdyby czytnik zostal zepsuty z powrotem, liczba sie nie ruszy.
#: Dowodem jest kontrola na wejsciu SYNTETYCZNYM nizej, na OBU galeziach naraz;
#: liczba mowi tylko, ile razy drzewo moze na te galaz trafic. Rodzina 6.D159.
ZAPISOW_WERBATIM_POTROJNYCH = 1

#: Cztery postacie, ktorych rozroznienie jest trescia 6.D200, z oczekiwana maska.
#: Stoja RAZEM w jednej krotce, bo pozycja zadala kontroli na OBIE galezie „w jednym
#: tescie": osobne testy przeszlyby, gdyby czytnik obie postacie mylil w te sama
#: strone, a wtedy nie byloby wiadomo, ktora galaz dziala.
POSTACIE_LITERALU = (
    # (zapis, maska, co to jest w C#)
    ('x = @"""a"; {}', "x =       ; {}", "werbatim o tresci `\"a` — NIE surowy"),
    ('x = @"a"""; {}', "x =       ; {}", "werbatim o tresci `a\"`"),
    ('x = """a"""; {}', "x =        ; {}", "surowy, otwarty trzema cudzyslowami"),
    ('x = $@"""a"; {}', "x =        ; {}", "werbatim interpolowany — NIE surowy"),
)


#: Tabela po stronie C# — 6.D226. Nazwa pliku i nazwa tablicy, obie sprawdzane.
TABELA_CSHARP = ("tests/Game.Tests/UiTextTests.cs", "PostacieLiteralu")

#: Ucieczki zwyklego literalu C#. Tabela jest MALA i to jest wybor: dekoder ma
#: obsluzyc dokladnie to, co w tej tabeli stoi, a na wszystkim innym PASC GLOSNO
#: (`KeyError`), a nie oddac napis przepuszczony bez zmiany. Dekoder milczacy
#: o nieznanej ucieczce mowilby o sobie, a nie o pliku.
UCIECZKI_CSHARP = {'"': '"', "\\": "\\", "n": "\n", "t": "\t", "r": "\r", "0": "\0"}


def _odkoduj_zwykly_literal_csharp(kawalek):
    """Tresc zwyklego literalu C# (`"..."`) — ucieczki rozwiniete.

    **Dekoder jest PRZYBITY DO KOMPILATORA, nie do wyobrazenia (6.D226).** Zmierzone
    16.09.2026: `dotnet test` zmuszony asercja do wypisania czterech wartosci
    `PostacieLiteralu[i].Zapis` oddal je znak w znak tak, jak zwraca je ten dekoder
    na tym samym pliku — wlacznie z postacia werbatim o potrojnym cudzyslowie.
    Bez tego porownania dekoder bylby drugim czytnikiem tabeli, a nie jej odczytem.
    """
    assert kawalek.startswith('"'), kawalek
    i, out = 1, []
    while i < len(kawalek):
        if kawalek[i] == "\\":
            out.append(UCIECZKI_CSHARP[kawalek[i + 1]])
            i += 2
            continue
        if kawalek[i] == '"':
            return "".join(out)
        out.append(kawalek[i])
        i += 1
    raise AssertionError("literal bez domkniecia: " + kawalek)


def _sam_literal(tekst):
    """Sam literal napisowy z `... = <literal>; ...`, albo None.

    **Porownywany jest SAM LITERAL, a nie caly zapis, i to jest rozstrzygniecie
    6.D226 oparte na pomiarze trzech stopni.** Zmierzone 16.09.2026:
    (A) tekst zapisu BEZ odkodowania — rozjazd **4/4**, na samym escapowaniu, bo ten
        sam cudzyslow pisze sie inaczej w Pythonie i w C#;
    (B) tresc po odkodowaniu, CALY `Zapis` — rozjazd **4/4**, na rusztowaniu
        (`x = ` wobec `var x = `, `{}` wobec `var y = 1;`);
    (C) sam literal (od `= ` do domykajacego `;`) — **zbiory ROWNE co do znaku**.
    Porownanie calych zapisow byloby wiec bramka swiecaca na kodzie POPRAWNYM, czyli
    bramka do wylaczenia, nie do utrzymania (6.D27).

    Odsiew niebedacych literalem idzie przez `klasy_literalow`, a nie przez wlasne
    pytanie o pierwszy znak: kolumna `PoMasce` tabeli C# ma ksztalt
    `var x =       ; var y = 1;`, wiec wycinek miedzy `= ` a `;` jest tam pusty
    i bez tego odsiewu wszedlby do zbioru jako piaty element.
    """
    i = tekst.find("= ")
    if i < 0:
        return None
    j = tekst.find(";", i)
    if j < 0:
        return None
    wycinek = tekst[i + 2:j]
    kawalki = [(rodzaj, kawalek) for rodzaj, kawalek, _ in czytnik._przebieg(wycinek)]
    literaly = [kawalek for rodzaj, kawalek in kawalki if rodzaj == "literal"]
    if len(literaly) != 1 or literaly[0] != wycinek:
        return None
    return wycinek


#: **GRANICA NAZWANA, a nie przemilczana (6.D226).** Literal niosacy SREDNIK w tresci
#: zostalby uciety po obu stronach TAK SAMO, wiec rozjazd za srednikiem bylby dla tej
#: bramki niewidoczny. Sita na to swiadomie NIE MA: jedyne tanie (parzystosc
#: cudzyslowow) zapala sie na literale POPRAWNYM z uciekanym cudzyslowem, czyli
#: bylaby to bramka z 6.D27. Dzis zadna z czterech postaci srednika nie niesie.
ZAPADKA_ZAPISOW = 4


def zapisy_python():
    """Same literaly z `POSTACIE_LITERALU`, czytane ZE ZRODLA, nie z importu.

    Ze zrodla, bo pytanie brzmi „co stoi w pliku", a nie „co widzi ten proces" —
    ta sama roznica, ktora 6.D131 nazwalo przy masce skladanej w tescie.
    """
    import ast as _ast
    tekst = open(os.path.join(ROOT, "tools", "tests",
                              "test_csharp_test_methods.py"), encoding="utf-8").read()
    blok = tekst[tekst.index("POSTACIE_LITERALU = ("):]
    blok = blok[:blok.index("\n)\n") + 3]
    wynik = []
    for element in _ast.parse(blok).body[0].value.elts:
        literal = _sam_literal(_ast.literal_eval(element.elts[0]))
        if literal:
            wynik.append(literal)
    return wynik


def zapisy_csharp(zrodlo=None):
    """Same literaly z tablicy `PostacieLiteralu` po stronie C#.

    **Czytnik POZYCZONY (6.D213):** literaly bierze `czytnik._przebieg`, ten sam,
    ktorym chodzi `maska`. Ma to skutek, ktory warto nazwac: wiersz tabeli zakomentowany
    — blokowo albo przez `//` — jest wtedy KOMENTARZEM, a nie wierszem, **za darmo**
    i bez ani jednej wlasnej reguly. Zmierzone: `maska` jest tu zlym narzedziem, bo
    zaslania literaly W CALOSCI i czytnik na masce widzi ZERO wierszy tabeli.
    """
    if zrodlo is None:
        with open(os.path.join(ROOT, TABELA_CSHARP[0]), encoding="utf-8") as uchwyt:
            zrodlo = uchwyt.read()
    blok = zrodlo[zrodlo.index(TABELA_CSHARP[1] + " ="):]
    blok = blok[:blok.index("};") + 2]
    wynik = []
    for rodzaj, kawalek, _klasa in czytnik._przebieg(blok):
        if rodzaj != "literal" or not kawalek.startswith('"'):
            continue
        literal = _sam_literal(_odkoduj_zwykly_literal_csharp(kawalek))
        if literal:
            wynik.append(literal)
    return wynik


def test_zbior_zapisow_literalu_jest_TEN_SAM_po_obu_stronach():
    """6.D226: dwie listy tych samych czterech zapisow i nic nie pilnowalo zgodnosci.

    **Oczekiwania MUSZA byc osobne** — `maska` zwraca kod, `Literaly` tresc — ale
    **zapisy maja byc te same**, bo pytanie jest to samo: ktore cztery ksztalty
    rozstrzygaja o galezi „surowy czy werbatim".

    **ASYMETRIA, dla ktorej ta bramka istnieje, jest ZMIERZONA (16.09.2026).**
    Skreslenie jednej z czterech postaci **po stronie C#** zapala od 6.D215
    (`dotnet test tests/Game.Tests` -> `Failed: 1, Passed: 317`, na asercji zbioru
    przedrostkow). To samo skreslenie **po stronie Pythona** — czyli w liscie, ktora
    jest ZRODLEM — dawalo `python3 tools/tests/test_all.py` -> **2497/2497 przeszlo**,
    zero czerwieni. Lista bedaca zrodlem byla chroniona SLABIEJ niz jej kopia.
    """
    py = zapisy_python()
    cs = zapisy_csharp()
    assert len(py) == ZAPADKA_ZAPISOW and len(cs) == ZAPADKA_ZAPISOW, (
        "zapisow jest %d po stronie Pythona i %d po stronie C# przy zapadce %d — "
        "czytnik przestal widziec wiersze tabeli albo tabela sie zwezila"
        % (len(py), len(cs), ZAPADKA_ZAPISOW))
    assert set(py) == set(cs), (
        "ZBIORY zapisow literalu rozjechaly sie miedzy %s a %s:\n"
        "  tylko w Pythonie: %s\n  tylko w C#: %s\n"
        "kazdy zapis odpowiada innej galezi czytnika, wiec skreslenie jednego po "
        "JEDNEJ stronie zdejmuje te galaz spod pomiaru po tej stronie i tylko po niej"
        % ("tools/tests/test_csharp_test_methods.py", TABELA_CSHARP[0],
           sorted(set(py) - set(cs)), sorted(set(cs) - set(py))))


def test_czytnik_zapisow_WIDZI_rozjazd_na_wejsciu_wlasnym():
    """Kontrola PRZYRZADU: zbior rozjazdow jest z zalozenia pusty (rodzina 6.D159).

    Wejscie jest **CELOWO inne** niz tabela w drzewie — inaczej ta kontrola stalaby
    sie trzecia kopia tej samej czworki, a pytanie brzmi o czytnik, nie o tabele.

    **Pulapka w wejsciu to KOMENTARZ BLOKOWY MIEDZY wierszami tabeli**, i to jest
    ksztalt, ktory naprawde cos mierzy: czytnik naiwny (regeks po `("`) wzialby
    zakomentowany wiersz za wiersz tabeli. Czytnik pozyczony z `_przebieg` odsiewa
    go za darmo — i ten test pilnuje, ze nadal odsiewa.
    """
    probna = (
        '    private static readonly (string Zapis, string Tresc)[] PostacieLiteralu =\n'
        '    {\n'
        '        ("var a = @\\"alfa\\"; var b = 1;", "alfa"),\n'
        '        /* ("var a = @\\"beta\\"; var b = 1;", "beta"), */\n'
        '        ("var a = $@\\"gama\\"; var b = 1;", "gama"),\n'
        '        // ("var a = @\\"delta\\"; var b = 1;", "delta"),\n'
        '    };\n')
    widziane = zapisy_csharp(probna)
    assert widziane == ['@"alfa"', '$@"gama"'], (
        "czytnik zapisow widzi %s — wiersz zakomentowany BLOKOWO albo przez `//` "
        "nie jest wierszem tabeli, a czytnik naiwny bierze oba" % (widziane,))

    rozjazd = probna.replace('$@\\"gama\\"', '@\\"gama\\"')
    assert zapisy_csharp(rozjazd) != widziane, (
        "podmiana przedrostka `$@` na `@` nie zmienila odczytu — czytnik nie czyta "
        "przedrostka, wiec porownanie zbiorow bylo by zielone nad rozjazdem")


def test_maska_ROZROZNIA_werbatim_od_surowego_na_obu_galeziach():
    # **6.D200: potrojny cudzyslow po `@` to NIE jest napis surowy, a pomylenie tego
    # polyka plik.** Do 13.09.2026 `_koniec_literalu` brala kazde trzy cudzyslowy za
    # otwarcie napisu surowego, nie patrzac na `@` przed nimi. W C# po `@` napisu
    # surowego nie ma: taki zapis jest werbatim, bo w werbatim para cudzyslowow znaczy
    # jeden cudzyslow. Czytnik szukal wiec domkniecia potrojnym cudzyslowem, ktorego
    # w pliku nie ma, i maskowal WSZYSTKO DO KONCA PLIKU — chowajac przed bramka kazda
    # metode ponizej.
    #
    # Jedna taka linia w `UiTextTests.cs` schowala TRZY metody testowe (6.D188).
    # Zlapalo to porownanie dwoch odczytow, a nie bramka na atrybut: bramka na atrybut
    # meldowala „0 nieuruchamianych", bo nie miala czego zobaczyc. Ta sama wyrocznia
    # zepsuta w strone „wszystko w porzadku", co przy 6.B28.
    #
    # **Cztery postacie sprawdzane sa RAZEM**, bo kazda osobno przeszlaby u czytnika,
    # ktory myli je w te sama strone.
    sprawdzonych = 0
    for zapis, oczekiwana, opis in POSTACIE_LITERALU:
        assert czytnik.maska(zapis) == oczekiwana, (
            "maska(%r) = %r, a ma byc %r — %s"
            % (zapis, czytnik.maska(zapis), oczekiwana, opis))
        sprawdzonych += 1
    assert sprawdzonych == len(POSTACIE_LITERALU), (
        "petla po postaciach wykonala sie %d razy zamiast %d — wtedy asercje wyzej "
        "nie porownuja wszystkiego (rodzina 6.D193)" % (sprawdzonych, len(POSTACIE_LITERALU)))

    # I DRUGA STRONA, bez ktorej cztery rownosci wyzej nie mowia nic o AWARII:
    # klamry maja ZOSTAC. Czytnik sprzed naprawy zwracal dla pierwszej postaci
    # maske bez `{}` — i to wlasnie po tym znika reszta pliku.
    for zapis, oczekiwana, _ in POSTACIE_LITERALU:
        assert "{}" in oczekiwana, (
            "oczekiwana maska %r nie ma klamr — wtedy ten test przeszedlby takze "
            "u czytnika, ktory polyka reszte pliku" % oczekiwana)


def test_ile_zapisow_WERBATIM_POTROJNYCH_ma_drzewo():
    # **Liczba mowi o KORPUSIE, nie o naprawie — i to stoi napisane.**
    # Zapisow werbatim z potrojnym cudzyslowem jest w `tests/` i `src/` dokladnie
    # jeden i stoi w KOMENTARZU. Galaz naprawiona przez 6.D200 nie jest wiec przez
    # drzewo cwiczona ani razu; dowodem naprawy jest wylacznie kontrola syntetyczna
    # wyzej. Ta liczba pilnuje czego innego: gdyby ktos wprowadzil taki zapis do KODU,
    # ma to zostac zauwazone — bo kazdy inny czytnik w tym drzewie (`maska`
    # z `UiTextTests.cs`, `Literaly`, `KodLeksykalnie`) ma te sama galaz i nie kazdy
    # zostal naprawiony.
    import re as _re
    import tree_walk

    # `tree_walk.znajdz`, a nie `glob(recursive=True)` — 6.D117. Rekurencyjny glob
    # przechodzi bokiem obok wspolnego odsiania z `.gitignore` i kazde jego wywolanie
    # nosi WLASNA kopie reguly (`.godot`, `obj`, `bin`). Tu doszlaby czwarta.
    pliki_cs = tree_walk.znajdz("tests", "*.cs", root=czytnik.ROOT)
    pliki_cs += tree_walk.znajdz("src", "*.cs", root=czytnik.ROOT)
    pliki_cs = sorted(pliki_cs)

    assert len(pliki_cs) > 100, (
        "przeskanowano %d plikow `.cs` — korpus sie zwezil i liczba nizej opisuje "
        "co innego niz w dniu pomiaru" % len(pliki_cs))

    trafienia = []
    for sciezka in pliki_cs:
        with open(sciezka, encoding="utf-8") as handle:
            zrodlo = handle.read()
        for dopasowanie in _re.finditer(r'@\$?"{3,}|\$@"{3,}', zrodlo):
            trafienia.append("%s:%d" % (
                os.path.basename(sciezka), zrodlo[:dopasowanie.start()].count("\n") + 1))

    assert len(trafienia) == ZAPISOW_WERBATIM_POTROJNYCH, (
        "zapisow `@\"\"\"` jest %d, a zmierzono %d: %s. Jesli PRZYBYLO — sprawdz, czy "
        "stoi w kodzie czy w komentarzu, i czy czytnik, ktory ten plik czyta, ma "
        "naprawe z 6.D200" % (len(trafienia), ZAPISOW_WERBATIM_POTROJNYCH,
                              ", ".join(trafienia)))


#: Rozklad literalow napisowych po SZESCIU postaciach `maska()`. ZMIERZONE
#: 13.09.2026 (6.D201) tym samym `_przebieg`, ktory maskuje — nie drugim czytnikiem.
#:
#: **Docstring `maska()` mowil o CZTERECH postaciach „wystepujacych w tests/" i to
#: zdanie bylo NIEPELNE, a nie nieaktualne.** Dwie postacie, ktorych nie wymienialo,
#: wystepuja: werbatim interpolowany (1 raz) i surowy interpolowany z przedrostkiem
#: podwojnego dolara (14 razy). Ta druga jest liczniejsza od surowego bez przedrostka.
ROZKLAD_POSTACI = {
    "tests": {
        # 3555 -> 3734 i 655 -> 665 (13.09.2026, MB-02): `TrainingSessionTests.cs`
        # i `RunSummaryTests.cs`. Cztery pozostale postacie bez zmian.
        # 3799 -> 3853 i 667 -> 674 (14.09.2026, MB-03): `TractionBlockTests.cs`.
        # Liczby ZMIERZONE przyrzadem, nie wyprowadzone z liczby metod — pierwsza
        # proba wpisana „z glowy" dala 3862/676 i bramka ja odrzucila.
        # 3871 -> 3912, 674 -> 675, 50 -> 54 i 7 -> 8 (14.09.2026, MB-05):
        # `CabPlacementTests.cs`. **Tu drgnely CZTERY postacie, a nie dwie jak zwykle**,
        # i to jest tresc, a nie cztery liczby: bramka leksykalna tego pliku czyta
        # zrodlo wyrazeniami regularnymi, wiec niesie werbatim (`@"..."`, +4) i jeden
        # literal surowy — postacie, ktorych testy arytmetyczne nie uzywaja wcale.
        # 3912 -> 3996 i 54 -> 55 (14.09.2026, audyt bramki MB-05):
        # `CabPlacementTests.cs` przepisany z 6 metod na 10, z czytnikiem zrodla
        # (`TylkoKod`, `Wywolania`, `Glebokosc`, `ZnakPrzed`), ktory ma wlasna
        # kontrole negatywna na literalach surowych. `interpolowany ($)` nie drgnal.
        # 3996 -> 4075 i 675 -> 685 (14.09.2026, MB-06): `ControlOwnerTests.cs`
        # (w tym cztery testy galezi postoju i dwa straznik z poprawki dziury
        # w ochronie). Ten wpis stoi OBOK poprzedniego, a nie zamiast niego — obie
        # zmiany sa rozlaczne i spotkaly sie dopiero przy scalaniu, a liczby sa
        # PRZELICZONE na wspolnym drzewie, nie zsumowane w glowie. `werbatim (@)`
        # nie drgnal przy MB-06, bo `ControlOwnerTests.cs` nie czyta zrodla
        # wyrazeniami regularnymi: pyta rdzen o zachowanie, a rdzen da sie zawolac
        # bez silnika.
        # 4093 -> 4102 i 691 -> 692 (14.09.2026, audyt MB-06): literały nowego testu.
        # MB-08 dokłada trzy pliki testowe i bramkę leksykalną. Postać
        # `werbatim interpolowany ($@)` rośnie z jednego na cztery i to jest treść,
        # a nie szum: `HandleTrainKeysGateTests` składa wzorce `Regex` z nazwy klawisza,
        # więc potrzebuje `$@"..."` — gałąź, która do dziś miała w `tests/` JEDNO
        # wystąpienie. Wszystkie liczby PRZELICZONE po scaleniu obu gałęzi.
        # 4242 -> 4258, 717 -> 725 i 56 -> 62 (14.09.2026, 6.D210): literały nowego
        # pliku `DefaultArmAuditTests.cs`. Werbatim rośnie o sześć, bo próbki
        # syntetyczne klasyfikatora są zapisane jako `@"..."` z `\n` w środku —
        # kontrola przyrządu potrzebuje kodu C# jako DANYCH, a nie jako kodu.
        # 4258 -> 4318, 725 -> 739 i 62 -> 64 (14.09.2026, 6.D211): literały bramki
        # na połykanych członach, dopisanej do tego samego pliku. Werbatim rośnie
        # o DWA i tylko o dwa — oba to wzorce `Regex` w `KorpusMetody`, gdzie ukośnik
        # wsteczny jest treścią; próbki syntetyczne tej bramki są zwykłymi napisami
        # z `\n`, bo składają się z kilku kawałków przez `+`, a werbatim nie znosi
        # sklejania z sekwencjami ucieczki w jednym wyrażeniu.
        # 4318 -> 4345 i 64 -> 66 (15.09.2026, 6.D212): literały kontroli przyrządu
        # czytnika wyliczeń i maski. Postać interpolowana NIE DRGA i to jest treść:
        # komunikaty tej kontroli nazywają próbkę słowami, a nie wstawiają jej wartości,
        # bo próbka jest stała i wypisanie jej niczego nie dopowiada. Werbatim rośnie
        # o dwa — oba to wzorce `Regex` czytnika surowego, gdzie ukośnik jest treścią.
        # 4345 -> 4384, 739 -> 744 i 66 -> 67 (15.09.2026, 6.D213): literały bramki
        # na `.ToString()` w rdzeniu i jej kontroli przyrządu. Werbatim rośnie o JEDEN
        # — wzorzec `Regex` deklaracji zmiennej, gdzie ukośnik jest treścią.
        # 4384 -> 4406, 744 -> 747, 67 -> 68 i 4 -> 6 (15.09.2026, 6.D214): literały
        # bramki na zgłoszeniach urwanych. Postać `werbatim interpolowany ($@)` rośnie
        # z czterech na SZEŚĆ i to jest treść: oba wzorce `.ToString()` składają się dziś
        # z `CzlonWyrazenia` przez interpolację, a ukośnik w nich jest treścią — czyli
        # jedyna postać, która daje i jedno, i drugie.
        # 4406 -> 4438, 747 -> 754 i 68 -> 70 (15.09.2026, 6.D215): literaly bramki
        # na galezi surowy-czy-werbatim. Postac `surowy (""")` NIE DRGA i to jest tresc:
        # cztery probki tej bramki opisuja literaly surowe i werbatim, ale opisuja je
        # jako DANE w napisach zwyklych, a nie zapisuja w tych postaciach — inaczej
        # probka byla by tym, co mierzy.
        # 4511 -> 4562, 769 -> 783, 76 -> 88 i 6 -> 7 (15.09.2026, 6.D224): literaly
        # bramki na DRUGIEJ slepej plamce sita rdzenia. Werbatim rosnie o DWANASCIE
        # i to jest tresc: dziesiec z nich to wpisy wykazu
        # `VarOTypieWyliczeniowymWRdzeniu`, gdzie czwartym polem jest WZORZEC
        # deklaracji, a ukosnik wsteczny w nim jest trescia; dwa pozostale to wzorce
        # `Regex` czytnika (`\bvar\b` i `var nazwa = Wyliczenie.Czlon`). Postac
        # `werbatim interpolowany ($@)` rosnie o JEDEN — wzorzec `.ToString()`
        # skladany z nazwy zmiennej przez `Regex.Escape`, czyli jedyne miejsce,
        # ktore potrzebuje i ukosnika jako tresci, i wstawienia wartosci.
        # 4562 -> 4583 i 783 -> 789 (17.09.2026, 6.D231): literaly czytnika korpusu
        # odmawiajacego metodzie wyrazeniowej i jego kontroli przyrzadu. WERBATIM
        # NIE DRGA i to jest tresc: probka syntetyczna tej kontroli jest sklejana
        # z szesciu kawalkow przez `+` i niesie `\n`, a werbatim nie znosi sekwencji
        # ucieczki; jedyny wzorzec `Regex` tego czytnika stal w pliku juz wczesniej
        # i policzony jest od 6.D211. Postac interpolowana rosnie o SZESC — tyle
        # komunikatow tej okolicy wstawia zmierzona wartosc zamiast ja opisywac.
        # 4583 -> 4602 i 789 -> 792 (17.09.2026, 6.D229): literaly bramki
        # `BrokenJsonRefusalTests.cs` — nazwy loaderow i ksztaltow wejscia w dwoch
        # wykazach, fragmenty komunikatu odmowy i teksty asercji. Trzy interpolowane
        # to komunikaty par loader x ksztalt, ktore MUSZA nazwac pare, inaczej FAIL
        # nie mowi ktora. Cztery pozostale postacie nie drgnely. Przeliczone z drzewa.
        # 4602 -> 4641 (17.09.2026, 6.D233): literaly bramki `test_json_required`
        # i `RequiredFieldTests.cs`. Postac interpolowana NIE drga: komunikaty tej
        # okolicy wstawiaja nazwe pola przez argument osłony, a nie przez interpolacje.
        # 4641 -> 4609 i 792 -> 794 (17.09.2026, 6.D257): DZIEWIETNASCIE wlasnych petli
        # szukania korzenia zastapionych JEDNYM pomocnikiem
        # `tests/Shared/KorzenRepozytorium.cs`.
        # **Liczba kopii jest ZMIERZONA, a nie wzieta z opisu pozycji: pozycja mowila
        # o CZTERECH, a w drzewie stalo ICH DZIEWIETNASCIE** — cztery na markerze
        # `MetroBxl.sln` i PIETNASCIE na `CLAUDE.md`, w ksztalcie wielowierszowym,
        # ktorego pierwsza wersja bramki nie widziala.
        # Zwyklych UBYWA trzydziesci dwa: kazda kopia niosla marker i komunikat odmowy,
        # a pomocnik trzyma marker w JEDNEJ stalej. Interpolowanych PRZYBYWAJA dwa —
        # komunikat odmowy pomocnika nazywa marker i katalog startu, czego zadna
        # z kopii nie robila. Przeliczone z drzewa, nie zsumowane.
        # 4609 -> 4627, 794 -> 797 i 88 -> 92 (17.09.2026, 6.D260): `LancuchZmian.cs`
        # w `tests/Shared/` i kontrola przyrzadu w `UiTextTests.cs`. Werbatim rosnie
        # o CZTERY, bo wzorce lancucha zapisane sa jako `@"..."` — literal werbatim
        # jest dla wyrazenia regularnego jedyna postacia, w ktorej `\d` nie wymaga
        # podwajania ukosnika. Przeliczone z drzewa, nie zsumowane.
        # 4627 -> 4643 i 797 -> 802 (22.09.2026, 6.M2): `StopWindowParityTests.cs`.
        # Przeliczone z drzewa, nie zsumowane.
        # 4643 -> 4720, 802 -> 812 i 92 -> 95 (22.09.2026, 6.D235): `FileReadGuardTests.cs`
        # (tekst wzorcowy przyrzadu, trzy wzorce werbatim) i `BadFileTests.cs` (osiem
        # zlych ksztaltow). Przeliczone z drzewa, nie zsumowane.
        # 4720 -> 4730 i 95 -> 96 (23.09.2026, 6.D365): testy kultury w `DoorCycleTests.cs`
        # i `TrainingSessionTests.cs`, wzorzec czasu postoju jako `@"..."`; ZMIERZONE.
        # 4730 -> 4732 (23.09.2026, 6.D368): dwie postacie w tescie sciezki `a=b.csv`.
        # 4732 -> 4788 i 812 -> 819 (23.09.2026, 6.M1): `LineReplayTests.cs` (zapisy
        # wejsc w tekscie, komunikaty asercji) i nowy test `RunPlanTests.cs`.
        # Przeliczone z drzewa.
        # 4788 -> 4800 i 819 -> 820 (23.09.2026, 6.M3): testy okna drzwi
        # w `StopWindowParityTests.cs`. Przeliczone z drzewa.
        # 4800 -> 4807, 820 -> 826 i 96 -> 98 (23.09.2026, 6.D357): dwie nowe metody
        # `BrokenJsonRefusalTests.cs` — komunikaty asercji, ksztalt wielowierszowy
        # i DWA wzorce werbatim (slowo z lacznikiem, pozycja „w wierszu …, bajt …");
        # ZMIERZONE.
        # 4807 -> 4843, 826 -> 836, 98 -> 99 i 7 -> 8 (23.09.2026, 6.D356):
        # `BrokenJsonRefusalTests.cs` — komunikaty asercji, argumenty `line`, wzorzec
        # slowa `@"..."` i dopasowanie slowa zakazanego `$@"..."`. ZMIERZONE.
        # 4843 -> 4851 i 836 -> 837 (23.09.2026): testy nowej sceny i komunikaty.
        # 4851 -> 4875 i 99 -> 100 (24.09.2026, door-prompt-service):
        # literały tekstowe i komunikaty asercji nowych testow postoju; ZMIERZONE.
        # 4875 -> 4886 (24.09.2026, braking cue): testy warunku przejecia i hamulca.
        # 4886 -> 4892 (24.09.2026, PR #771): nazwy siatek i komunikat asercji.
        # 4892 -> 4901 i 838 -> 840 (24.09.2026, kamera): testy ciaglosci.
        # 4901 -> 4904 (24.09.2026, integracja): scisle porownania w DoorPromptTests.
        # 4904 -> 4915 i 840 -> 842 (24.09.2026, dwustopniowe cue): testy obu faz.
        # 4915 -> 4920 (24.09.2026, S): cztery literały i komunikat asercji.
        # 4920 -> 4929 (24.09.2026, oznaczenia stacji): pelna nazwa i
        # komunikaty pieciu asercji testow znacznikow; zmierzone czytnikiem.
        # 4929 -> 4957 i 842 -> 843 (24.09.2026, pamiec cue): test przejazdu i zakresu pamieci.
        # 4957 -> 4970 (24.09.2026, autopilot E): osiem asercji i ich komunikaty.
        # 4970 -> 4977 (24.09.2026, HUD 800x600): dwa testy pozycji i ich komunikaty.
        # 4977 -> 5000, 843 -> 844 (24.09.2026, wybór składu i HUD): testy N/T,
        # komunikaty asercji oraz pełny wiersz pozycji; przeliczone czytnikiem.
        # 5000 -> 5021 (24.09.2026, interaktywne R): test kolejności guardów
        # i diagnostyki błędu, przeliczone czytnikiem testów.
        # 5021 -> 5030 (24.09.2026, automat bez sygnalizacji): trzy igły
        # strażnika, trzy komunikaty asercji i pozostałe literały testu.
        # 5030 -> 5031, werbatim 100 -> 101 (24.09.2026, chase 800x600):
        # komunikat asercji oraz wzorzec węzła View.
        # 5031 -> 5038 (24.09.2026, krótki HUD chase): teksty i komunikaty testu.
        "zwykly": 5045,
        "interpolowany ($)": 847,
        "werbatim (@)": 101,
        "surowy interpolowany ($$\"\"\")": 13,
        # 8 -> 10 (23.09.2026): dwie probki sceny w testach.
        "surowy (\"\"\")": 10,
        "werbatim interpolowany ($@)": 8,
    },
    "src": {
        # 1223 -> 1264 i 446 -> 456 (13.09.2026, MB-02): `TrainingSession.cs`,
        # `TrainingResult.cs` i `RunSummary.cs`. Cztery postacie o liczbie 0 albo 1
        # NIE DRGNELY i to jest tu trescia, a nie dwie liczby, ktore urosly: caly
        # przyrost poszedl w dwie postacie, ktore `src/` juz mial.
        # 1265 -> 1281 i 460 -> 459 (14.09.2026, MB-03): `TractionBlock.cs`
        # i cztery wpisy katalogu; postac interpolowana SPADLA o jeden, bo wiersz
        # predkosci przestal byc interpolowany w ciele `Hud.Update`.
        # 1284 -> 1293 i 459 -> 462 (14.09.2026, MB-04): `FirstRun.AssetsRoot`,
        # `FirstRun.DomyslnyZapisWejsc` i wiersz `[ZAPISY]`. Cztery pozostale
        # postacie nie drgnely. Liczby ZMIERZONE `czytnik.klasy_literalow`, czyli
        # przyrzadem tej bramki — nie przepisane z jej komunikatu o bledzie.
        # 1293 -> 1298 i 462 -> 465 (14.09.2026, MB-05): `CabView.cs` i wpiecie
        # kabiny w `FirstRun`. Cztery pozostale postacie znowu nie drgnely, tak samo
        # jak przy MB-02 — caly przyrost idzie w dwie postacie, ktore `src/` juz ma.
        # 1298 -> 1299 (14.09.2026, MB-05, poprawka `--cab`): jeden napis w
        # `RunPlan.KnownArguments`. `interpolowany` nie drgnelo.
        # 465 -> 467 (14.09.2026, MB-06): dwa komunikaty odmowy w `LineCore` —
        # „nie przejeto sterowania" i „nie ma skladu o identyfikatorze". `zwykly` NIE
        # DRGNELO i to jest tresc: `ControlOwner.cs` jest typem bez ani jednego napisu.
        # 1299 -> 1300 i 467 -> 468 (14.09.2026, MB-06, poprawka dziury w ochronie):
        # komunikat odmowy `TakeControl` przed wjazdem na plan.
        # 1300 -> 1308 i 468 -> 473 (14.09.2026, MB-07): literały drugiego składu
        # w `RunPlan` (nazwy argumentów, komunikaty odmowy zakresu) i w `FirstRun`
        # (nazwy węzłów widoków, odmowa przy zerze brył widoku pochodnego) oraz
        # w `LineCore` (nic nowego napisowego — stąd przyrost tylko po stronie gry).
        # 1323 -> 1377 i 478 -> 480 (14.09.2026, MB-08). Przyrost `zwykly` jest tu
        # NIETYPOWO duzy i ma jeden powod: `DoorPrompt` i `UiText` niosa dziewiec
        # nowych kluczy katalogu, a `DoorControl.cs` — piec zdan odmowy i komplet
        # opisow czlonow; do tego dochodza klawisze `D`/`F` i szablony wiersza stacji.
        # `interpolowany` rusza sie o DWA, bo jedynymi nowymi napisami skladanymi sa
        # komunikaty odmowy konstruktora i wypis `ToString` postoju.
        # Cztery pozostale postacie znowu nie drgnely.
        # 1377 -> 1384 i 480 -> 481 (17.09.2026, 6.D229). Siedem nowych `zwykly` to
        # SIEDEM ARGUMENTOW `what` przekazanych do `JsonText.Parse` — po jednym na
        # kazde miejsce parsowania pliku uzytkownika ("plan sygnalizacji", "os trasy",
        # "doba sluzby", "definicja strefy testowej CBTC", "rozklad" i DWA RAZY
        # "manifest chunkow": w `ChunkManifest.cs` i w `Sim.Runner/Program.cs`.
        # `interpolowany` rusza sie o JEDEN, bo skladany napis jest tu jeden: wiersz
        # odmowy w `JsonText.Parse`. Cztery pozostale postacie nie drgnely.
        # 1384 -> 1409 i 481 -> 489 (17.09.2026, 6.D233): literaly osłony
        # `JsonFields.RequiredField` i jej wołań — każdy odczyt wymaganego pola
        # niesie dziś NAZWĘ pola i opis właściciela, bo bez nich komunikat odmowy
        # nie mówi, czego brakuje. Przeliczone z drzewa.
        # 1409 -> 1450 (23.09.2026, 6.M1): kody i komunikaty zdarzen linii w
        # `InputLog`, `LineSession`, pola sidecara i odmowy `replay --line` w `Sim.Runner`,
        # nowa odmowa w `RunPlan`. Przeliczone z drzewa, nie zsumowane.
        # 1450 -> 1452 (23.09.2026, 6.D356): DWA literaly polskiego opisu dokumentu
        # innego ksztaltu, `Program.WrongJsonShapeText` w `Sim.Runner`. ZMIERZONE.
        # 1452 -> 1456 (23.09.2026): cztery literaly kodu nowej sceny.
        # 1456 -> 1460 (24.09.2026, braking cue): wskazowka w obu trybach.
        # 1460 -> 1464 (24.09.2026, dwustopniowe cue): cztery nowe literały HUD.
        # 1464 -> 1465 i 514 -> 515 (24.09.2026, oznaczenia stacji):
        # sciezka GLB i odmowa braku; zmierzone czytnikiem po obu katalogach.
        # 1465 -> 1468 (24.09.2026, HUD 800x600): klucz i dwa warianty pozycji.
        "zwykly": 1470,
        # 489 -> 494 (22.09.2026, 6.D235): piec komunikatow `Abort` dla pliku ZLEGO
        # w `FirstRun.cs`. Przeliczone z drzewa, nie zsumowane.
        # 494 -> 513 (23.09.2026, 6.M1): komunikaty odmow i wiersze zapisu zdarzen
        # linii (`InputLog`), wiersz `[ODTWORZENIE]` linii w `Sim.Runner`. Przeliczone.
        # 513 -> 514 (23.09.2026, 6.D357): wiersz odmowy `JsonText.Parse` przestal
        # doklejac `error.Message` i ma DWIE postacie — z pozycja z liczb parsera
        # i bez niej, gdy parser jej nie podal; jedna byla, sa dwie. ZMIERZONE.
        # 515 -> 516 (24.09.2026, interaktywne R): błąd przeładowania sceny.
        # 516 -> 518 (24.09.2026, krótki HUD chase): dystans i granica.
        "interpolowany ($)": 519,
        "werbatim (@)": 0,
        "surowy interpolowany ($$\"\"\")": 1,
        "surowy (\"\"\")": 1,
        "werbatim interpolowany ($@)": 0,
    },
}

#: Galezie o udziale ZEROWYM — i to jest polowa pytania 6.D201, wiec stoi osobno.
#: **W calym korpusie nie ma ani jednej.** W samym `src/` sa DWIE: werbatim i werbatim
#: interpolowany. Rdzen i warstwa gry nie pisza wyrazen regularnych, a to jedyne
#: miejsce, gdzie werbatim jest w tym drzewie uzywany — wszystkie 42 wystapienia
#: z `tests/` to wzorce `Regex`.
BEZ_UDZIALU_W_SRC = ("werbatim (@)", "werbatim interpolowany ($@)")


def test_rozklad_SZESCIU_postaci_literalu_zgadza_sie_z_drzewem():
    # **Cztery liczby zadane przez pole „Wyjscie" 6.D201 sa tu SZEŚCIOMA i to jest
    # odpowiedz, a nie rozszerzenie zakresu:** postaci, ktore `maska` rozroznia,
    # jest szesc, wiec cztery liczby opisalyby cztery z nich i przemilczaly dwie.
    #
    # Liczone `czytnik.klasy_literalow`, czyli tym samym `_przebieg`, ktorym chodzi
    # `maska` — bramka liczaca wlasnym rozbiorem mowilaby o sobie (rodzina 6.D27).
    import collections
    import tree_walk

    sprawdzonych = 0
    for korzen, oczekiwany in sorted(ROZKLAD_POSTACI.items()):
        licznik = collections.Counter()
        pliki_cs = tree_walk.znajdz(korzen, "*.cs", root=czytnik.ROOT)
        assert len(pliki_cs) > 20, (
            "pod `%s/` widac %d plikow `.cs` — korpus sie zwezil i liczby nizej "
            "opisuja co innego niz w dniu pomiaru" % (korzen, len(pliki_cs)))
        for sciezka in pliki_cs:
            with open(sciezka, encoding="utf-8") as handle:
                licznik.update(czytnik.klasy_literalow(handle.read()))
        widziane = {postac: licznik.get(postac, 0) for postac in czytnik.POSTACIE}
        assert widziane == oczekiwany, (
            "rozklad postaci pod `%s/` to %s, a zmierzono %s"
            % (korzen, widziane, oczekiwany))
        sprawdzonych += 1

    assert sprawdzonych == len(ROZKLAD_POSTACI), (
        "petla po korzeniach wykonala sie %d razy zamiast %d — wtedy rownosci wyzej "
        "nie porownuja wszystkiego (rodzina 6.D193)"
        % (sprawdzonych, len(ROZKLAD_POSTACI)))

    # KONTROLA PRZYRZADU: kazda z szesciu postaci MA nazwe w `POSTACIE` i kazda
    # nazwa z `POSTACIE` stoi w obu rozkladach. Bez tego dopisanie siodmej galezi
    # do `_przebieg` przeszloby cicho, bo `licznik.get(..., 0)` jej nie zobaczy.
    for korzen, oczekiwany in ROZKLAD_POSTACI.items():
        assert sorted(oczekiwany) == sorted(czytnik.POSTACIE), (
            "rozklad pod `%s/` wymienia %s, a `POSTACIE` — %s; siodma galaz "
            "policzylaby sie jako zero i nikt by jej nie zobaczyl"
            % (korzen, sorted(oczekiwany), sorted(czytnik.POSTACIE)))


def test_ktora_galaz_jest_BEZCZYNNA_i_gdzie():
    # **Galaz o udziale zerowym ma byc WIDOCZNA, nie domniemana** — ta sama zasada,
    # ktora 6.D186 zastosowalo do markera `RootElement` (0 z 18) i 6.D187 do ukosnika
    # w domknieciu wzorca. Tam wyszlo to na jaw dopiero przez kontrole negatywna,
    # ktora wyszla ZIELONA; tutaj jest policzone wprost i przybite.
    #
    # **Odpowiedz: w calym korpusie ZERA nie ma ani razu**, wiec zadnej galezi nie
    # ma po co usuwac — a pole „Poza zakresem" i tak tego zabrania. W samym `src/`
    # zera sa DWA i obydwa na werbatim, bo werbatim sluzy w tym drzewie wylacznie
    # do wzorcow `Regex`, a te stoja w testach.
    puste_w_src = tuple(sorted(
        postac for postac, ile in ROZKLAD_POSTACI["src"].items() if ile == 0))
    assert puste_w_src == tuple(sorted(BEZ_UDZIALU_W_SRC)), (
        "galezie bez udzialu w `src/` to dzis %s, a wpisano %s"
        % (puste_w_src, tuple(sorted(BEZ_UDZIALU_W_SRC))))

    for postac in czytnik.POSTACIE:
        razem = (ROZKLAD_POSTACI["tests"][postac] + ROZKLAD_POSTACI["src"][postac])
        assert razem > 0, (
            "postac `%s` ma udzial ZEROWY w calym korpusie — wtedy jej galaz w "
            "`_przebieg` jest bezczynna i to ma stac napisane, a nie byc domniemane "
            "(6.D201). Galezi mimo to NIE USUWAJ: zero dzis nie znaczy zero jutro, "
            "a galaz usunieta jest galezia, ktorej nikt nie przywroci przy pierwszym "
            "nowym literale" % postac)


def test_klasy_literalow_i_maska_ida_TYM_SAMYM_przebiegiem():
    # Bez tego oba czytniki moglyby sie rozejsc po cichu, a wtedy rozklad wyzej
    # opisywalby jeden rozbior, a maskowanie robilby drugi — dokladnie ta rozbieznosc,
    # ktora 6.D27 nazywa „bramka mierzy cos innego, niz twierdzi".
    zrodlo = ('var a = "zwykly"; var b = $"interp {x}"; var c = @"werb\\at";\n'
              '// komentarz z "napisem"\n'
              'var d = $@"werb interp {y}";\n')
    klasy = czytnik.klasy_literalow(zrodlo)
    assert klasy == ["zwykly", "interpolowany ($)", "werbatim (@)",
                     "werbatim interpolowany ($@)"], klasy

    # Komentarz NIE wnosi literalu — cztery, nie piec.
    assert len(klasy) == 4, klasy

    # I ta sama tresc po masce: literaly znikaja, kod zostaje, dlugosc sie nie zmienia.
    zamaskowane = czytnik.maska(zrodlo)
    assert len(zamaskowane) == len(zrodlo), (len(zamaskowane), len(zrodlo))
    assert "zwykly" not in zamaskowane, zamaskowane
    assert "var a =" in zamaskowane, zamaskowane


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.

#: Kształt, po którym test szuka korzenia repozytorium przez KATALOG `.git` — 6.D253.
#: Wzorzec stoi na SUROWYM źródle, a nie na masce, i to jest wymóg, nie skrót:
#: `maska()` zamienia literały na spacje, a `".git"` JEST literałem, więc po masce
#: tego kształtu nie da się zobaczyć w ogóle.
KORZEN_PO_GIT = re.compile(r'Directory\.Exists\(\s*[^)]*"\.git"')


def _bez_komentarza(wiersz):
    """Wiersz z uciętym komentarzem `//` — żeby proza o usterce jej nie udawała."""
    i = wiersz.find("//")
    return wiersz if i < 0 else wiersz[:i]


def korzen_po_katalogu_git():
    """`[(plik, numer, wiersz)]` — miejsca szukające korzenia po KATALOGU `.git`."""
    out = []
    for sciezka in czytnik.pliki():
        with open(sciezka, encoding="utf-8") as uchwyt:
            tresc = uchwyt.read()
        for numer, wiersz in enumerate(tresc.split("\n"), 1):
            if KORZEN_PO_GIT.search(_bez_komentarza(wiersz)):
                out.append((os.path.basename(sciezka), numer, wiersz.strip()))
    return out


def test_zaden_test_nie_szuka_korzenia_repozytorium_po_KATALOGU_git():
    """W worktree `.git` jest PLIKIEM, więc `Directory.Exists` nie znajdzie go nigdy.

    **Zmierzone 17.09.2026, nie wywnioskowane z dokumentacji gita.** Dwa pliki
    (`TractionBlockTests.cs`, `TrainingWiringTests.cs`) szukały tak korzenia i w worktree
    padało przez to **siedem** testów `Game.Tests`, przy zerze w głównym katalogu
    roboczym. Rozkład jest zmierzony osobno, cofnięciem po jednym miejscu naraz:
    `TrainingWiringTests` odpowiada za **pięć**, `TractionBlockTests` za **dwa**.

    **Dlaczego to bramka, a nie tylko poprawka.** `CLAUDE.md` §5 wymienia jako
    weryfikację kodu `test_all.py` i `dotnet test tests/Sim.Tests` — `Game.Tests` w tej
    pętli **nie stoi**. Czerwień, na którą nikt nie patrzy, stoi dowolnie długo, a agenci
    tego projektu pracują w worktree z instrukcji, czyli dokładnie w układzie, w którym
    ta usterka się objawia.

    Wzór poprawny jest w tym samym katalogu: `HandleTrainKeysGateTests` szuka korzenia
    przez `File.Exists` na `MetroBxl.sln` — plik, który jest treścią repozytorium
    i plikiem w OBU układach.
    """
    winne = korzen_po_katalogu_git()
    assert winne == [], (
        "test szuka korzenia repozytorium po KATALOGU `.git`, a w worktree `.git` jest "
        "PLIKIEM — pętla dojdzie wtedy do korzenia systemu plików i test padnie na "
        "maszynie agenta, zostając zielony u autora: %s. Wzór: `File.Exists` na "
        "`MetroBxl.sln`, jak w `HandleTrainKeysGateTests`." % winne)


def test_bramka_na_korzen_widzi_ksztalt_ktory_ma_widziec():
    """Kontrola przyrządu: pusty wynik wyżej ma znaczyć „nie ma", a nie „nie patrzę".

    Bez tego testu literówka we wzorcu dałaby zero winnych i zieleń — nieodróżnialne
    od stanu poprawnego (6.D27 w drugą stronę).
    """
    zle = 'var katalog = Directory.GetCurrentDirectory();\n' \
          'while (katalog is not null && !Directory.Exists(Path.Combine(katalog, ".git")))'
    assert KORZEN_PO_GIT.search(zle) is not None, (
        "wzorzec nie widzi kształtu, dla którego powstał — bramka wyżej mierzyłaby "
        "wtedy milczenie")

    dobre = 'while (katalog is not null && !File.Exists(Path.Combine(katalog, "MetroBxl.sln")))'
    assert KORZEN_PO_GIT.search(dobre) is None, (
        "wzorzec zapala się na wzorze POPRAWNYM — taka bramka zostaje wyłączona, "
        "nie naprawiona (6.D27)")

    w_komentarzu = '// dawniej: Directory.Exists(Path.Combine(katalog, ".git"))'
    assert KORZEN_PO_GIT.search(_bez_komentarza(w_komentarzu)) is None, (
        "wzorzec liczy PROZĘ o usterce jako usterkę — wtedy nie da się o niej napisać "
        "w komentarzu bez zapalenia bramki")

#: Kształt WŁASNEJ pętli szukania korzenia: wspinaczka w górę drzewa katalogów,
#: sterowana `File.Exists`/`Directory.Exists`. Bramka wyżej pilnuje MARKERA
#: (`.git` kontra `MetroBxl.sln`); ta pilnuje LICZBY KOPII — bo kopia z poprawnym
#: markerem przechodziłaby tamtą bez słowa, a to jest dokładnie ten kształt długu,
#: który 6.D253 zostawiło po sobie.
#:
#: **Czyta BLOK, a nie wiersz, i to jest wymóg, nie ostrożność.** Pierwsza wersja tej
#: bramki żądała `File.Exists` w TYM SAMYM wierszu co `while` i przez to nie widziała
#: PIĘTNASTU kopii kształtu `while (directory is not null) { if (File.Exists(…)) … }`
#: — a przechodziła na zielono, twierdząc „dokładnie jedno miejsce". Zmierzone przy
#: 6.D257: cztery kopie, o których mówił opis pozycji, plus piętnaście, o których
#: nie mówił nikt, przy DWÓCH różnych markerach (`MetroBxl.sln` i `CLAUDE.md`).
WHILE = re.compile(r"\bwhile\s*\(")
ISTNIENIE = re.compile(r"(?:File|Directory)\.Exists\(")

#: Ile wierszy po `while` czytać w poszukiwaniu sprawdzenia istnienia. Osiem —
#: tyle zajmuje najdłuższa z piętnastu znalezionych kopii (nagłówek, klamra,
#: `if`, klamra, `return`, klamra, pusty wiersz, krok w górę).
OKNO_PETLI = 8

#: Gdzie ta JEDNA pętla wolno stać. Pomocnik jest LINKOWANY do obu projektów
#: testowych, więc jedna kopia obsługuje `Game.Tests` i `Sim.Tests` naraz —
#: trzeci projekt byłby nową zależnością obu, a plik źródłowy nią nie jest.
JEDYNA_PETLA_KORZENIA = "KorzenRepozytorium.cs"


def _petla_w_bloku(linie, i):
    """Czy `while` w wierszu `i` sprawdza ISTNIENIE pliku w swoim oknie."""
    okno = "\n".join(_bez_komentarza(w) for w in linie[i:i + OKNO_PETLI])
    return ISTNIENIE.search(okno) is not None


def wlasne_petle_korzenia():
    """`[(plik, numer, wiersz)]` — każda WŁASNA wspinaczka po drzewie katalogów."""
    out = []
    for sciezka in czytnik.pliki():
        with open(sciezka, encoding="utf-8") as uchwyt:
            linie = uchwyt.read().split("\n")
        for i, wiersz in enumerate(linie):
            if WHILE.search(_bez_komentarza(wiersz)) and _petla_w_bloku(linie, i):
                out.append((os.path.basename(sciezka), i + 1, wiersz.strip()))
    return out


def test_korzenia_repozytorium_szuka_DOKLADNIE_JEDNO_miejsce():
    """**Bramka z 6.D253 pilnuje markera, a nie liczby kopii — i to jest luka (6.D257).**

    Przed tą pozycją cztery pliki testowe szukały korzenia czterema własnymi pętlami,
    różniącymi się punktem startu (`AppContext.BaseDirectory` kontra
    `Directory.GetCurrentDirectory()`) i typem uchwytu (`string` kontra `DirectoryInfo`).
    Marker ujednoliciła 6.D253; procedury nie ujednolicił nikt, bo nie pilnowała jej
    żadna bramka: **piąta kopia z poprawnym markerem przechodziła bez słowa.**

    Ta bramka mówi „jedna", a nie „nie więcej niż cztery": równość jest tańsza
    i mocniejsza, bo pomocnik jest LINKOWANY do obu projektów i nie ma powodu, dla
    którego druga kopia miałaby powstać.
    """
    widziane = wlasne_petle_korzenia()

    poza = sorted(x for x in widziane if x[0] != JEDYNA_PETLA_KORZENIA)
    assert poza == [], (
        "własna pętla szukania korzenia poza `%s`: %s — pożycz pomocnika "
        "(`KorzenRepozytorium.Plik(...)` albo `.Tresc(...)`) zamiast pisać piątą "
        "kopię; marker poprawny nie wystarcza, bo kopii pilnuje liczba, nie kształt"
        % (JEDYNA_PETLA_KORZENIA, poza))

    assert len(widziane) == 1, (
        "pętli szukania korzenia jest %d, a ma być DOKŁADNIE jedna: %s"
        % (len(widziane), widziane))


def test_bramka_na_liczbe_petli_widzi_ksztalt_ktory_ma_widziec():
    """Kontrola PRZYRZĄDU — bez niej literówka we wzorcu dałaby zero pętli i zieleń,
    czyli stan NIEODRÓŻNIALNY od drzewa z jedną pętlą (6.D27).

    Cztery kształty osobno, bo cztery stały w drzewie przed tą pozycją: uchwyt
    `string` z `GetParent`, uchwyt `DirectoryInfo` z `Parent`, marker `.git`
    i ten sam kod w komentarzu.
    """
    jednowierszowa = ['while (katalog is not null '
                      '&& !File.Exists(Path.Combine(katalog, "MetroBxl.sln")))', "{", "}"]
    przez_uchwyt = ['while (katalog is not null '
                    '&& !File.Exists(Path.Combine(katalog.FullName, "MetroBxl.sln")))',
                    "{", "}"]
    po_gicie = ['while (katalog is not null '
                '&& !Directory.Exists(Path.Combine(katalog, ".git")))', "{", "}"]
    # **Kształt, którego pierwsza wersja tej bramki NIE WIDZIAŁA** — a stał w drzewie
    # w piętnastu kopiach. Sprawdzenie istnienia jest trzy wiersze niżej niż `while`.
    wielowierszowa = [
        "while (directory is not null)",
        "{",
        '    if (File.Exists(Path.Combine(directory.FullName, "CLAUDE.md")))',
        "    {",
        "        return directory.FullName;",
        "    }",
        "",
        "    directory = directory.Parent;",
    ]

    for ksztalt in (jednowierszowa, przez_uchwyt, po_gicie, wielowierszowa):
        assert WHILE.search(_bez_komentarza(ksztalt[0])) is not None \
            and _petla_w_bloku(ksztalt, 0), (
                "czytnik nie widzi własnej pętli: %r" % ksztalt[0])

    w_komentarzu = ["        // while (directory is not null) — dawny wzór",
                    "        // if (File.Exists(x)) return y;"]
    assert not (WHILE.search(_bez_komentarza(w_komentarzu[0]))
                and _petla_w_bloku(w_komentarzu, 0)), (
        "czytnik zapalił się na PROZIE o dawnym wzorze — wtedy nie da się o tej "
        "usterce napisać w komentarzu, a ten plik robi to w kilku miejscach")

    wolanie = ['var kod = KorzenRepozytorium.Tresc("src", "Game", "FirstRun.cs");']
    assert WHILE.search(_bez_komentarza(wolanie[0])) is None, (
        "czytnik zapalił się na WOŁANIU pomocnika, czyli na tym, co ta bramka "
        "ma promować: %r" % wolanie[0])

    # Pętla BEZ sprawdzania istnienia pliku NIE jest szukaniem korzenia.
    obca = ["while (i < n)", "{", "    suma += tab[i];", "}"]
    assert not _petla_w_bloku(obca, 0), (
        "czytnik zapalił się na zwykłej pętli — wtedy każdy `while` w testach "
        "byłby kopią szukania korzenia: %r" % obca)

if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

# --- 6.D261: powtorzona nazwa pomocnika — duplikat czy zbieg nazw ---------------

#: **Dwadziescia jeden nazw `private static` pada w wiecej niz jednym pliku,
#: i to sa DWIE rozne rzeczy, a nie jedna.** Ten akapit jest PRZEPISANY 18.09.2026
#: przy 6.D265, a nie dopisany obok: pomiar 6.D261 z 17.09.2026 dal 24 nazwy przy
#: 237 podpisach i dziesiec rodzin identycznych, i to juz nieprawda — trzy z tamtych
#: rodzin byly opakowaniami, ktore ta pozycja zdjela. Dzis: 67 plikow, 222 podpisy.
#:
#: * **7 rodzin IDENTYCZNYCH** — ta sama nazwa nad tym samym cialem po normalizacji
#:   bialych znakow, kazda po DWIE kopie. 6.D261 liczylo tu dziesiec, bo TRZY byly
#:   jednowierszowymi DELEGACJAMI do `KorzenRepozytorium` (`RepositoryRoot` x9,
#:   `RepoRoot` x3, `FindRepositoryRoot` x3), zostawionymi przez 6.D257: tamta
#:   pozycja zdjela PETLE, a nie OPAKOWANIA, i jest to roznica, ktorej nie nazwala.
#:   6.D265 zdjelo pietnascie definicji i przepisalo 58 wywolan w pietnastu
#:   plikach — piecdziesiat trzy na `KorzenRepozytorium.Sciezka` i piec na
#:   `.SciezkaAlboNull`, bo `FindRepositoryRoot` zwracalo `string?`.
#: * **14 rodzin JEDNOIMIENNYCH** — ta sama nazwa nad ROZNYM cialem, i ta liczba
#:   sie NIE ruszyla: zadna z trzech zdjetych nazw nie stala nad innym cialem.
#:   Najliczniejsze: `Settings` x7 w czterech postaciach, `Level` x7 w trzech,
#:   `Plan` x6 w czterech. Scalenie ich byloby bledem, a nie sprzataniem.
#:
#: **Odpowiedz 6.D261 na pytanie „ktora z pozostalych zasluguje na wspolny plik"
#: brzmi: ZADNA** — i zostaje w mocy, bo 6.D265 nie ruszylo ani jednej z nich.
#: Wszystkie siedem ma po DWIE kopie, wszystkie sa jednowierszowe (48–163 znaki
#: tresci), a SZESC z siedmiu stoi w obrebie JEDNEGO projektu. Wspolny plik kosztuje
#: wpis `Compile Include` w kazdym `.csproj`, ktory go bierze; dla jednowierszowca
#: uzywanego dwa razy w tym samym projekcie jest to koszt wiekszy niz oszczednosc.
#: Jedyna rodzina miedzyprojektowa (`Notch`) jest zarazem najkrotsza z siodemki.
#:
#: **Granica rodziny lezy przy DWOCH kopiach, nie przy jednej**, i jest to zmierzone
#: kontrola przyrzadu 6.D265 na drzewie probnym, a nie wywnioskowane z definicji:
#: przywrocenie JEDNEJ kopii `RepoRoot` daje nadal siedem, dwoch i trzech — osiem.
#: Rodzina to nazwa w WIECEJ NIZ JEDNYM pliku, wiec przedostatnia kopia zabiera
#: z rejestru takze ostatnia. Zdanie „zostawienie jednego opakowania da osiem"
#: z pola „Weryfikacja" tej pozycji jest wiec prawdziwe dla RODZINY, a falszywe
#: dla KOPII — i dopiero pomiar to rozdzielil.
RODZIN_IDENTYCZNYCH = 7
RODZIN_JEDNOIMIENNYCH = 14

#: Podloga na liczbe podpisow — WOLNA, bo pomocnikow przybywa razem z testami.
MIN_PODPISOW_POMOCNIKA = 200


def test_ile_rodzin_pomocnikow_jest_DUPLIKATEM_a_ile_ZBIEGIEM_NAZW():
    """**Obie liczby, ktorych zadalo pole „Wyjscie" — rownosciami, nie progiem.**

    Rownosc jest tu wyborem: dopisanie DWUDZIESTEJ PIATEJ powtorzonej nazwy zmienia
    jedna z tych dwoch liczb bez wzgledu na to, do ktorej kupki wpadnie — a prog
    zlapalby tylko jedna ze stron. Podloga na liczbe podpisow stoi obok, zeby
    czytnik oslepiony do zera nie przeszedl obu rownosci przez zejscie do (0, 0).
    """
    podpisow = sum(len(w) for w in czytnik.pomocnicy().values())
    assert podpisow >= MIN_PODPISOW_POMOCNIKA, (
        "podpisow `private static` pod `tests/` jest %d przy podlodze %d — czytnik "
        "oslepl albo pomocnicy zniknęli, a wtedy obie rownosci nizej przechodza "
        "zejsciem do zera" % (podpisow, MIN_PODPISOW_POMOCNIKA))

    identyczne, jednoimienne = czytnik.rodziny_pomocnikow()
    assert (len(identyczne), len(jednoimienne)) == (RODZIN_IDENTYCZNYCH,
                                                    RODZIN_JEDNOIMIENNYCH), (
        "rodzin identycznych %d i jednoimiennych %d, a pomiar 17.09.2026 dal %d i %d. "
        "Identyczne: %s. Jednoimienne: %s. Rodzina IDENTYCZNA to ta sama nazwa nad TYM "
        "SAMYM cialem — kandydat do scalenia; JEDNOIMIENNA to ta sama nazwa nad INNYM "
        "cialem i scalac jej NIE WOLNO"
        % (len(identyczne), len(jednoimienne), RODZIN_IDENTYCZNYCH,
           RODZIN_JEDNOIMIENNYCH, sorted(identyczne), sorted(jednoimienne)))


def test_czytnik_rodzin_odroznia_TO_SAMO_CIALO_od_TEJ_SAMEJ_NAZWY():
    """**Kontrola przyrzadu do 6.D261 — piec ksztaltow na drzewie probnym.**

    Zadanie zadalo jej wprost: dwie metody o tej samej nazwie i ROZNYCH cialach maja
    zostac policzone jako rodzina „ta sama nazwa, inna tresc", a nie jako duplikat.
    Bez tego liczby (10, 14) nie odroznialyby sie od czytnika, ktory kazda powtorzona
    nazwe wrzuca do jednej kupki — a taki tez daje sume 24.

    Sprawdzane sa naraz: rozroznienie cial, obojetnosc na WCIECIE (tresc, nie zapis),
    pominiecie nazwy padajacej w JEDNYM pliku (przeciazenie, nie duplikat) oraz
    metoda WYRAZENIOWA `=> ...;`, ktora klamry nie ma — a jest postacia wiekszosci
    powtorzonych pomocnikow w tym drzewie.
    """
    a = ("class A {\n"
         "    private static int Ten() { return 1; }\n"
         "    private static int Inny() { return 1; }\n"
         "    private static int Wyrazeniowy() => 7;\n"
         "    private static int WJednymPliku() { return 2; }\n"
         "    private static int WJednymPliku(int x) { return x; }\n"
         "}\n")
    b = ("class B {\n"
         "    private static int Ten() {   return 1;   }\n"
         "    private static int Inny() { return 999; }\n"
         "    private static int Wyrazeniowy() => 7;\n"
         "}\n")

    with tempfile.TemporaryDirectory(prefix="metro-pomocnicy-") as katalog:
        for projekt, tresc in (("Alfa.Tests", a), ("Beta.Tests", b)):
            os.makedirs(os.path.join(katalog, "tests", projekt))
            with open(os.path.join(katalog, "tests", projekt, "T.cs"), "w",
                      encoding="utf-8") as uchwyt:
                uchwyt.write(tresc)
        identyczne, jednoimienne = czytnik.rodziny_pomocnikow(katalog)

    assert sorted(identyczne) == ["Ten", "Wyrazeniowy"], (
        "identyczne dalo %s — `Ten` rozni sie tylko WCIECIEM, a `Wyrazeniowy` jest "
        "metoda bez klamry; obie maja byc duplikatem" % sorted(identyczne))
    assert sorted(jednoimienne) == ["Inny"], (
        "jednoimienne dalo %s — `Inny` ma to samo imie nad ROZNYM cialem i nie jest "
        "duplikatem" % sorted(jednoimienne))
    assert "WJednymPliku" not in identyczne and "WJednymPliku" not in jednoimienne, (
        "przeciazenie w JEDNYM pliku policzone jako rodzina miedzy plikami")


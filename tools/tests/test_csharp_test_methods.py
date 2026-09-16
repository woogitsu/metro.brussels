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
        "zwykly": 4562,
        "interpolowany ($)": 783,
        "werbatim (@)": 88,
        "surowy interpolowany ($$\"\"\")": 13,
        "surowy (\"\"\")": 8,
        "werbatim interpolowany ($@)": 7,
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
        "zwykly": 1377,
        "interpolowany ($)": 480,
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
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

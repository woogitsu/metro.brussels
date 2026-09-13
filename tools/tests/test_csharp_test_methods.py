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
        "zwykly": 3555,
        "interpolowany ($)": 655,
        "werbatim (@)": 50,
        "surowy interpolowany ($$\"\"\")": 13,
        "surowy (\"\"\")": 7,
        "werbatim interpolowany ($@)": 1,
    },
    "src": {
        "zwykly": 1223,
        "interpolowany ($)": 446,
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

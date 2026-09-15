#!/usr/bin/env python3
"""Stala C#, ktorej nikt nie czyta, jest zglaszana albo uzasadniona.

**Skad ta bramka.** 6.B31. `test_dead_constants.py` z 6.B29 obchodzi `tools/` i `src/`,
ale filtruje pliki po `.py` — a `src/` jest w tym repozytorium przede wszystkim C#.
6.B29 samo wypisalo ten brak, ale **nazwalo go katalogiem `godot/`, ktory tu nie
istnieje**: `ls -d */` daje `data docs reports src tests tools`, a scena lezy
w `src/Game/`. Brak byl realny i jest brakiem **jezyka**, nie katalogu — i ten wpis
jest tu dlatego, ze pozycja kolejki powtorzyla te pomylke po raporcie.

**Konwencja nazw jest inna niz po stronie Pythona, i to tez byl blad we wpisie.**
Wpis 6.B31 mowil o stalych „o nazwie wielkimi literami"; C# w tym repozytorium pisze
je **PascalCase** (`CabEyeHeightM`, `PlanLimitKmh`), wiec kryterium na WIELKIE litery
nie zlapaloby ani jednej. Bramka nie filtruje po kroju nazwy wcale — bierze kazda
deklaracje `const` i `static readonly`.

**Kierunek pomylki jest wybrany swiadomie.** Odczyt liczony jest jako wystapienie
identyfikatora poza wierszem deklaracji, wiec stala o nazwie zbiegajacej sie z nazwa
metody albo zmiennej gdzie indziej wyjdzie jako ZYWA, choc martwa. To jest falszywy
negatyw i tansza pomylka niz odwrotna: falszywy pozytyw kazalby usunac cos, co dziala,
a bramka swiecaca na poprawnym kodzie zostaje wylaczona, nie poprawiona (6.D27).

**Sprawdzone jest tez to, czego `ast` nie ma po stronie C#**: `.tscn`, `.gd`, `*.sh`
i `.github/` — bo scena Godota i skrypty CI moga czytac stala po nazwie, a wtedy nie
jest martwa. Zmierzone 07.09.2026: zero takich odczytow, ale warunek zostaje, bo jego
brak zamienilby jedno zapytanie w bledna diagnoze.

Zmierzone 07.09.2026: 124 pliki `.cs`, **234** deklaracje, **194** roznych nazw,
**jedna** nieczytana — `StationChainagesM`, prywatne pole w `RunHeaderTests`, ktore
zostalo usuniete w tym samym commicie, a nie wpisane na liste wyjatkow. Lista startuje
**pusta** i to jest mocniejsze niz start z wyjatkiem.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csharp_test_methods as CTM  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DRZEWA = ("src", "tests")
#: Gdzie jeszcze moze stac ODCZYT stalej — patrz docstring modulu.
POZA_CSHARP = ((os.path.join(ROOT, "src"), (".tscn", ".gd")),
               (os.path.join(ROOT, "tools"), (".sh",)),
               (os.path.join(ROOT, ".github"), (".yml", ".yaml")))

#: Deklaracja `const` albo `static readonly` z inicjatorem w tym samym wierszu.
#: Zmierzone 07.09.2026: **wszystkie 234** deklaracje w tym drzewie maja taki ksztalt —
#: ani jedna nie konczy sie srednikiem bez `=`, ani jedna nie przenosi `=` do
#: nastepnego wiersza. Gdyby ktos taka dopisal, bramka jej NIE zobaczy; osobny test
#: pilnuje wiec, ze liczba widzianych deklaracji nie spada pod zmierzony prog.
DEKLARACJA = re.compile(
    r"^\s*(?:public|private|internal|protected)?\s*(?:static\s+readonly|const)\s+"
    r"[A-Za-z0-9_<>.,\[\]?]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", re.M)

#: Ile deklaracji bramka ma widziec, zeby pomiar byl pomiarem. Bez tego progu literowka
#: w `DEKLARACJA` dalaby zero deklaracji, zero martwych i zielona bramke — ta sama
#: pulapka, ktora `MINIMUM_CLAIMS` zamyka w `test_report_claims.py`. Zmierzone: 234.
MINIMUM_DEKLARACJI = 200

#: Stale nieczytane, uznane po obejrzeniu: nazwa -> (plik, powod).
#:
#: **Pusto, i to jest wynik pomiaru, a nie zalozenie — po raz drugi.** Do 15.09.2026
#: bylo tu pusto, bo jedyna nieczytana stala tego drzewa (`StationChainagesM`) zostala
#: USUNIETA, bo byla prywatnym polem testu. Przy 6.D214 doszedl wpis `CzlonWyrazenia`,
#: ktory nie byl o stalej, tylko **o skanerze**: stala byla czytana dwa razy, ale
#: wylacznie przez interpolacje napisu, a skan czytal na masce, ktora literal zaslania
#: W CALOSCI — razem z dziura, czyli razem z kodem, ktory sie wykonuje.
#:
#: **Ten akapit jest przepisany, a nie dopisany obok (15.09.2026, 6.D225): wpis znika,
#: bo znika powod, dla ktorego istnial.** `martwe()` czyta od dzis `maska_z_dziurami`,
#: wiec stala czytana wylacznie przez `$"...{Nazwa}..."` nie jest juz nieczytana —
#: i lista wraca do pustej. Wyjatek na liscie opisywalby granice skanera jako wlasciwosc
#: STALEJ, a to jest dokladnie ta pomylka, ktora 6.D27 kaze wylaczac, a nie hodowac.
UZASADNIONE = {}


def _pliki(root, rozszerzenia, drzewa=DRZEWA):
    for drzewo in drzewa:
        # 6.D97: bez własnego odsiewania `bin`/`obj` — stoją w `.gitignore`, więc
        # `TW.walk` już ich nie oddaje. Warunek na `os.sep + "obj"` był przy tym
        # szerszy, niż wyglądał: łapał każdy katalog KOŃCZĄCY się na `obj`.
        for katalog, _pod, pliki in TW.walk(os.path.join(root, drzewo), root):
            for plik in pliki:
                if plik.endswith(rozszerzenia):
                    yield os.path.join(katalog, plik)


def _tresc_csharp(root=ROOT):
    tresc = {}
    for sciezka in _pliki(root, (".cs",)):
        with open(sciezka, encoding="utf-8", errors="replace") as uchwyt:
            tresc[os.path.relpath(sciezka, root)] = uchwyt.read()
    return tresc


def deklaracje(tresc=None, root=ROOT):
    """Nazwa -> lista plikow, w ktorych jest deklarowana."""
    tresc = _tresc_csharp(root) if tresc is None else tresc
    znalezione = {}
    for sciezka, zawartosc in tresc.items():
        for match in DEKLARACJA.finditer(zawartosc):
            znalezione.setdefault(match.group(1), []).append(sciezka)
    return znalezione


def _tresc_poza_csharp(root=ROOT):
    kawalki = []
    for katalog, rozszerzenia in POZA_CSHARP:
        if not os.path.isdir(katalog):
            continue
        for gdzie, _pod, pliki in TW.walk(katalog):
            for plik in pliki:
                if plik.endswith(rozszerzenia):
                    with open(os.path.join(gdzie, plik), encoding="utf-8",
                              errors="replace") as uchwyt:
                        kawalki.append(uchwyt.read())
    return "\n".join(kawalki)


#: Identyfikator w kodzie — do policzenia odczytow JEDNYM przejsciem po pliku.
IDENTYFIKATOR = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _odczyty(tresc):
    """Licznik identyfikatorow spoza wierszy deklaracji, jednym przejsciem.

    **Ksztalt wymuszony pomiarem, nie estetyka.** Pierwsza wersja szla po KAZDEJ
    nazwie osobno przez wszystkie wiersze — 194 nazwy razy 124 pliki — i modul mierzyl
    **20,7 s**, czyli tyle, ile 6.B30 wlasnie zdjelo z calego zestawu. Jedno przejscie
    z licznikiem daje ten sam wynik w ulamku tego czasu.
    """
    import collections
    licznik = collections.Counter()
    for zawartosc in tresc.values():
        for wiersz in zawartosc.splitlines():
            deklaracja = DEKLARACJA.match(wiersz)
            nazwa_deklarowana = deklaracja.group(1) if deklaracja else None
            for identyfikator in IDENTYFIKATOR.findall(wiersz):
                # Wiersz deklaracji nie jest odczytem TEJ nazwy — inaczej kazda stala
                # czytalaby sie sama i bramka nie zglosilaby nigdy niczego. Pozostale
                # identyfikatory z tego wiersza (typ, wartosci) licza sie normalnie.
                if identyfikator == nazwa_deklarowana:
                    continue
                licznik[identyfikator] += 1
    return licznik


def maska_z_dziurami(source):
    """`CTM.maska`, ale DZIURY INTERPOLACJI zostaja widoczne jako kod — 6.D225.

    Znak w znak tej samej dlugosci co `source`, tak samo jak `maska`. Tresc kazdej
    dziury przepuszczona jest przez `maska` jeszcze raz, bo dziura jest kodem C#
    i moze niesc wlasny literal (`{slownik["klucz"]}`) albo komentarz — a nazwa
    w napisie nie jest odczytem takze wtedy, gdy napis stoi w dziurze.

    Oba czytniki sa **pozyczone** (`CTM.maska`, `CTM.dziury_interpolacji`), a nie
    przepisane: drugi rozbior mowilby o sobie, a nie o tym, co skan naprawde widzi
    (6.D213).
    """
    bufor = list(CTM.maska(source))
    for start, koniec in CTM.dziury_interpolacji(source):
        bufor[start:koniec] = list(CTM.maska(source[start:koniec]))
    return "".join(bufor)


def martwe(root=ROOT):
    """Nazwa -> pliki deklaracji, dla stalych nieczytanych NIGDZIE.

    **Odczyty liczone na MASCE, nie w surowym tekscie (6.B34).** `CTM.maska` zamienia
    komentarze i literaly napisowe na spacje znak w znak, wiec wzmianka o stalej
    w komentarzu albo w napisie NIE liczy sie jako jej odczyt. Do 07.09.2026 liczyla
    sie — i szczegolnie klopotliwy byl przypadek komentarza WYJASNIAJACEGO usuniecie
    stalej, ktory utrzymywal ja w stanie „zywa" na zawsze; ten projekt takie komentarze
    pisze regularnie, bo reguly i zdania sie tu przepisuje, nie dopisuje obok.

    6.B31 wybrala tamten kierunek pomylki SWIADOMIE: falszywy negatyw (martwa stala
    uznana za zywa) byl tanszy niz bramka zapalajaca sie na poprawnym kodzie,
    a alternatywa wymagala wlasnego rozbioru literalow. Od 6.B28 `maska()` juz
    istnieje, wiec koszt zniknal razem z powodem.

    **Zmierzone: na dzisiejszym drzewie zmiana nie przesuwa ani jednej stalej** —
    martwych jest zero i przed maska, i po niej. Wartosc tej poprawki jest wiec
    wylacznie zapobiegawcza i dowodzi jej kontrola dodatnia na wstrzykniętym wejsciu,
    nie zmiana liczby.

    **Maska ma od 15.09.2026 (6.D225) DZIURE NA DZIURY INTERPOLACJI, i to zdanie jest
    przepisane, a nie dopisane obok.** Do tego dnia stalo tu, ze odczyty liczy `maska`;
    to juz nieprawda — liczy je `maska_z_dziurami`. Powod jest zmierzony: `maska`
    zaslania literal W CALOSCI, a dziura interpolacji NIE jest trescia napisu, tylko
    kodem, ktory sie wykonuje. Stala czytana wylacznie przez `$"...{Nazwa}..."`
    wygladala przez to dokladnie tak samo jak martwa, a komunikat bramki zachecal do
    jej usuniecia. Na drzewie z 15.09.2026 zmiana przesuwa **jedna** stala
    (`CzlonWyrazenia`, 6.D214): martwych **1 -> 0**.

    **Ile klamr otwiera dziure, mowi liczba dolarow** — patrz `CTM.dziury_interpolacji`.
    Wzorzec szukajacy `{nazwa}` w kazdym literale byl sprawdzony i ODRZUCONY: na tym
    drzewie daje odczyt dla **16 nazw**, dla ktorych odczytu nie ma (`case`, `if`,
    `return`, `var`, `void` z fragmentow C# cytowanych w napisach zwyklych, i dalej).
    Zadna z tej szesnastki nie jest dzis zadeklarowana jako stala, wiec werdyktu by
    nie zmienil — ale kazda z nich to stala, ktorej bramka BY NIE ZGLOSILA, gdyby
    kiedys taka nazwe dostala.
    """
    tresc = _tresc_csharp(root)
    znalezione = deklaracje(tresc, root)
    odczyty = _odczyty({k: maska_z_dziurami(v) for k, v in tresc.items()})
    poza = _tresc_poza_csharp(root)
    wynik = {}
    for nazwa, gdzie in znalezione.items():
        if odczyty[nazwa]:
            continue
        if re.search(r"\b" + re.escape(nazwa) + r"\b", poza):
            continue
        wynik[nazwa] = sorted(gdzie)
    return wynik


def test_the_gate_sees_the_declarations_it_is_supposed_to_see():
    """Prog na liczbe deklaracji. Literowka we wzorcu dalaby zero martwych i zielono."""
    ile = sum(len(v) for v in deklaracje().values())
    assert ile >= MINIMUM_DEKLARACJI, (
        "bramka widzi %d deklaracji przy progu %d — wzorzec przestal pasowac do "
        "ksztaltu, w jakim to repozytorium pisze stale C#" % (ile, MINIMUM_DEKLARACJI))


def test_every_unread_csharp_constant_is_justified():
    znalezione = martwe()
    nieuzasadnione = sorted(set(znalezione) - set(UZASADNIONE))
    assert not nieuzasadnione, (
        "stala C#, ktorej nic w src/ ani tests/ nie czyta, bez wpisu w UZASADNIONE: "
        + "; ".join("%s (%s)" % (n, ", ".join(znalezione[n])) for n in nieuzasadnione)
        + ". Albo jest do usuniecia, albo ma zostac i nalezy powiedziec dlaczego "
          "jednym zdaniem w tym samym commicie")


def test_no_justification_outlives_the_constant_it_describes():
    """Drugi kierunek: wpis bez martwej stalej opisuje stan miniony."""
    znalezione = martwe()
    martwe_wpisy = sorted(set(UZASADNIONE) - set(znalezione))
    assert not martwe_wpisy, (
        "UZASADNIONE opisuje stale, ktore znikly albo znowu sa czytane: "
        + ", ".join(martwe_wpisy))


def _wstrzyknij(katalog, zrodlo):
    """Drzewo `<katalog>/src/Atrapa.cs` z podanym zrodlem — dla kontrol wstrzykiwanych."""
    os.makedirs(os.path.join(katalog, "src"), exist_ok=True)
    os.makedirs(os.path.join(katalog, "tests"), exist_ok=True)
    with open(os.path.join(katalog, "src", "Atrapa.cs"), "w", encoding="utf-8") as uchwyt:
        uchwyt.write(zrodlo)


def test_a_mention_in_a_comment_is_not_a_read():
    """Sedno 6.B34: komentarz WYJASNIAJACY usuniecie stalej nie trzyma jej przy zyciu.

    Do 07.09.2026 trzymal: `_odczyty` liczylo identyfikatory w surowym tekscie, wiec
    wzmianka w komentarzu dawala jeden odczyt i stala wygladala na zywa NA ZAWSZE.
    Ten projekt takie komentarze pisze regularnie, wiec mechanizm nie byl teoretyczny.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as katalog:
        _wstrzyknij(katalog, "\n".join([
            "public static class Atrapa",
            "{",
            "    private const int ZmyslonaStala = 7;",
            "",
            "    // ZmyslonaStala zostala zdjeta z uzycia; komentarz zostal, zeby",
            "    // wiadomo bylo, dlaczego.",
            "    public static int Nic() => 0;",
            "}",
            "",
        ]))
        znalezione = martwe(katalog)
        assert "ZmyslonaStala" in znalezione, (
            "stala wymieniona WYLACZNIE w komentarzu uznana za czytana: "
            + repr(znalezione))


def test_a_mention_in_a_string_is_not_a_read():
    """To samo dla literalu napisowego — nazwa w napisie nie jest wywolaniem."""
    import tempfile

    with tempfile.TemporaryDirectory() as katalog:
        _wstrzyknij(katalog, "\n".join([
            "public static class Atrapa",
            "{",
            "    private const int ZmyslonaStala = 7;",
            "",
            '    public static string Opis() => "ZmyslonaStala jest tu tylko wymieniona";',
            "}",
            "",
        ]))
        znalezione = martwe(katalog)
        assert "ZmyslonaStala" in znalezione, (
            "stala wymieniona WYLACZNIE w napisie uznana za czytana: "
            + repr(znalezione))


def test_a_real_read_still_counts():
    """Kontrola drugiego kierunku: prawdziwy odczyt nadal trzyma stala przy zyciu.

    Bez tego testu trzy poprzednie byly by zielone rowniez dla maski zbyt szerokiej,
    ktora zamienia na spacje cos wiecej niz komentarze i literaly — a wtedy bramka
    zglaszalaby jako martwe stale, ktore sa czytane, i skonczylaby wylaczona.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as katalog:
        _wstrzyknij(katalog, "\n".join([
            "public static class Atrapa",
            "{",
            "    private const int ZmyslonaStala = 7;",
            "",
            "    public static int Dwa() => ZmyslonaStala * 2;",
            "}",
            "",
        ]))
        assert martwe(katalog) == {}, (
            "prawdziwy odczyt nie policzony — maska zdejmuje wiecej niz komentarze "
            "i literaly: " + repr(martwe(katalog)))


def test_a_declaration_line_is_not_counted_as_a_read():
    """Kontrola przyrzadu, nie drzewa. Gdyby wiersz deklaracji liczyl sie jako odczyt,
    KAZDA stala czytalaby sie sama i bramka nie zglosilaby NIGDY niczego — zielona
    z tego samego powodu, z ktorego zielone bylo `python3 <modul>.py` przed 6.D25."""
    wiersz = "    private const double PlanLimitKmh = 72.0;"
    assert DEKLARACJA.match(wiersz), wiersz
    assert DEKLARACJA.match(wiersz).group(1) == "PlanLimitKmh"
    assert not DEKLARACJA.match("        var x = PlanLimitKmh * 2.0;"), (
        "odczyt uznany za deklaracje")


def test_the_pattern_reads_the_shapes_this_repository_actually_uses():
    """Cztery ksztalty stad, a nie z podrecznika C#."""
    for wiersz, nazwa in (
            ("    public const double CabEyeHeightM = 2.20;", "CabEyeHeightM"),
            ("    private const int BadArgumentValue = 9;", "BadArgumentValue"),
            ("    private static readonly double[] Chainages = { 0.0, 600.0 };", "Chainages"),
            ("    internal static readonly IReadOnlyList<string> Names = new[] { \"a\" };",
             "Names")):
        match = DEKLARACJA.match(wiersz)
        assert match, wiersz
        assert match.group(1) == nazwa, (wiersz, match.group(1))
    # PascalCase, nie WIELKIE_LITERY — kryterium na wielkie litery nie zlapaloby
    # w tym repozytorium ani jednej stalej C#.
    assert all(not n.isupper() for n in list(deklaracje())[:20]), list(deklaracje())[:5]


#: Pietnascie probek na wszystkie szesc postaci literalu — 6.D225. Kazda niesie
#: nazwe wlasna, wiec „widziana" i „niewidziana" rozstrzyga sie po nazwie, a nie po
#: liczbie trafien. Cztery ostatnie to nie postacie, tylko GRANICE: specyfikator
#: formatu, wyrownanie, literal w dziurze i komentarz otaczajacy.
#: Trzy cudzyslowy skladane, a nie wpisane — inaczej zamknelyby docstring modulu.
Q = '"' * 3

PROBKI_DZIUR = (
    ('var a = $"x{Alfa}y";', ("Alfa",), "interpolowany"),
    ('var a = $@"x{Beta}y";', ("Beta",), "werbatim interpolowany"),
    ('var a = @$"x{Gama}y";', ("Gama",), "werbatim interpolowany, malpa pierwsza"),
    ('var a = $"x{{Delta}}y";', (), "podwojna klamra jest uciekniete, nie dziura"),
    ('var a = $$' + Q + 'x{Epsilon}y' + Q + ';', (),
     "surowy z dwoma dolarami: POJEDYNCZA klamra to zwykly znak"),
    ('var a = $$' + Q + 'x{{Zeta}}y' + Q + ';', ("Zeta",),
     "surowy z dwoma dolarami: dziure otwiera dopiero podwojna klamra"),
    ('var a = $' + Q + 'x{Eta}y' + Q + ';', ("Eta",),
     "surowy z jednym dolarem: dziure otwiera pojedyncza klamra"),
    ('var a = "x{Theta}y";', (), "bez dolara nie ma dziury w ogole"),
    ('var a = @"x{Jota}y";', (), "werbatim bez dolara tez nie"),
    ('var a = ' + Q + 'x{Kappa}y' + Q + ';', (), "surowy bez dolara tez nie"),
    ('var a = $"{Lambda:yyyy}";', ("Lambda", "yyyy"),
     "GRANICA: specyfikator formatu wchodzi jako identyfikator — patrz docstring"),
    ('var a = $"{My,5}";', ("My",), "wyrownanie"),
    ('var a = $$' + Q + '{{slownik["Ni"]}}' + Q + ';', (),
     "napis W DZIURZE nie jest odczytem — tresc dziury idzie przez maske drugi raz"),
    ('var a = $"{slownik["Ksi"]}";', ("Ksi",),
     "GRANICA ODZIEDZICZONA: cudzyslow w dziurze literalu NIE-surowego urywa literal "
     "juz w `_przebieg` — patrz docstring"),
    ('// $"{Omikron}"', (), "dziura w komentarzu nie jest kodem"),
)


def test_dziura_interpolacji_jest_kodem_a_reszta_literalu_nie():
    """Kontrola PRZYRZADU na wejsciu wlasnym: szesc postaci literalu i cztery granice.

    Zbior rozjazdow jest tu z zalozenia pusty, wiec bez tego testu poszerzenie skanu
    o dziure bylo by twierdzeniem bez dowodu (rodzina 6.D159). Wejscie jest CELOWO
    inne niz cokolwiek w drzewie — probka czytajaca drzewo mowilaby o drzewie,
    a pytanie jest o czytnik.

    **GRANICA NAZWANA, a nie przemilczana: specyfikator formatu wchodzi jako odczyt.**
    W `$"{Lambda:yyyy}"` czesc za dwukropkiem nie jest kodem, a czytnik oddaje z niej
    `yyyy`. Odciecie jej bylo rozwazone i ODRZUCONE, bo pomylka szlaby wtedy w DROZSZA
    strone: uciety fragment to identyfikator mniej, czyli stala moglaby wyjsc na martwa,
    choc jest czytana — a bramka zapalajaca sie na poprawnym kodzie zostaje wylaczona,
    nie poprawiona (6.D27). Zmierzona cena tej granicy na drzewie z 15.09.2026:
    specyfikatory daja **16 roznych** tokenow (`F0`-`F9`, `E3`, `E6`, `R`, `D4`, `P0`,
    `yyyy`, `MM`, `dd`, `e`) i **ani jeden** z nich nie jest zadeklarowany jako stala,
    wiec dzis nie trzyma przy zyciu niczego.

    **GRANICA ODZIEDZICZONA po `maska`, i ta jest STARSZA niz 6.D225.** W literale
    NIE-surowym cudzyslow domyka literal takze wtedy, gdy stoi w dziurze
    (`$"{slownik["Ksi"]}"`, legalne od C# 11) — `_przebieg` urywa tam literal i reszta
    wiersza idzie u niego jako KOD. Dziury liczone sa juz na tak urwanym kawalku, wiec
    ta pomylka jest dziedziczona, a nie wniesiona: przed 6.D225 `maska` oddawala z tej
    probki dokladnie to samo `Ksi`. Kierunek jest tanszy z dwoch (wiecej identyfikatorow
    widzianych, czyli falszywy negatyw bramki), ale nie jest zerowy: zmierzone
    15.09.2026, w `src/` i `tests/` jest **55** takich literalow, prawie wszystkie
    z `string.Join("...")` w dziurze. Poprawka nalezy do `_przebieg`, nie do tego skanu,
    i jest wpisana do kolejki osobno.
    """
    for zapis, oczekiwane, opis in PROBKI_DZIUR:
        widziane = set(IDENTYFIKATOR.findall(maska_z_dziurami(zapis))) - {"var", "a", "slownik"}
        assert widziane == set(oczekiwane), (
            "%s: z %r czytnik widzi %s, a ma widziec %s"
            % (opis, zapis, sorted(widziane), sorted(oczekiwane)))
        assert len(maska_z_dziurami(zapis)) == len(zapis), (
            "maska_z_dziurami zmienila dlugosc na %r — indeksy przestaly wskazywac "
            "te same miejsca co w oryginale" % (zapis,))


def test_probki_pokrywaja_KAZDA_z_szesciu_postaci_literalu():
    """Bez tego `PROBKI_DZIUR` moglyby sie zwezic do czterech postaci i nikt by nie
    zauwazyl — dokladnie ta pomylka, ktora 6.D201 znalazlo w docstringu `maska`."""
    widziane = set()
    for zapis, _oczekiwane, _opis in PROBKI_DZIUR:
        widziane.update(CTM.klasy_literalow(zapis))
    brakujace = sorted(set(CTM.POSTACIE) - widziane)
    assert not brakujace, (
        "PROBKI_DZIUR nie niosa ani jednego literalu postaci: " + ", ".join(brakujace))


def test_stala_czytana_WYLACZNIE_przez_interpolacje_nie_jest_zglaszana():
    """Sedno 6.D225, kontrola DODATNIA na wstrzyknietym drzewie.

    Do 15.09.2026 ta stala byla zglaszana jako martwa — i to nie jest teza, tylko
    zdarzenie: `CzlonWyrazenia` w `tests/Game.Tests/UiTextTests.cs` zapalilo bramke
    przy 6.D214 i musialo dostac wpis w `UZASADNIONE`.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as katalog:
        _wstrzyknij(katalog, "\n".join([
            "public static class Atrapa",
            "{",
            "    private const string CzlonProbki225 = \"czlon\";",
            "",
            '    public static string Opis() => $@"wzorzec {CzlonProbki225} konczy zdanie";',
            "}",
            "",
        ]))
        znalezione = martwe(katalog)
        assert "CzlonProbki225" not in znalezione, (
            "stala czytana wylacznie przez interpolacje nadal zglaszana jako martwa: "
            + repr(znalezione))


def test_stala_naprawde_martwa_jest_zglaszana_NADAL():
    """Drugi brzeg tego samego przebiegu: poszerzenie skanu nie moze go oslepic.

    Bez tego testu `maska_z_dziurami` oddajaca caly literal jako kod przeszlaby
    kontrole wyzej na zielono — i bramka przestalaby zglaszac cokolwiek.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as katalog:
        _wstrzyknij(katalog, "\n".join([
            "public static class Atrapa",
            "{",
            "    private const string MartwaProbka225 = \"nic\";",
            "",
            '    public static string Opis() => "MartwaProbka225 stoi tu tylko w napisie";',
            "}",
            "",
        ]))
        znalezione = martwe(katalog)
        assert "MartwaProbka225" in znalezione, (
            "stala wymieniona wylacznie w NAPISIE (nie w dziurze) uznana za czytana — "
            "poszerzenie skanu zdjelo maske z calego literalu: " + repr(znalezione))


def test_klamra_w_literale_NIE_interpolowanym_nie_jest_odczytem():
    """Granica, dla ktorej ten skan liczy dolary, a nie szuka `{nazwa}`.

    Napis zwykly niosacy `{Nazwa}` (na przyklad wzorzec formatu albo fragment JSON-a)
    nie jest odczytem. Zmierzone 15.09.2026: taka klamre niesie **104** literalow
    zwyklych, **24** werbatim i **8** surowych tego drzewa — wzorzec `{nazwa}` bez
    liczenia dolarow wzialby kazdy z nich za odczyt.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as katalog:
        _wstrzyknij(katalog, "\n".join([
            "public static class Atrapa",
            "{",
            "    private const string PoleProbki225 = \"pole\";",
            "",
            '    public static string Wzorzec() => "{PoleProbki225} nie jest dziura";',
            "}",
            "",
        ]))
        znalezione = martwe(katalog)
        assert "PoleProbki225" in znalezione, (
            "klamra w literale BEZ dolara policzona jako dziura — bramka przestalaby "
            "zglaszac stale naprawde martwe: " + repr(znalezione))


#: Ile dziur interpolacji ma widziec skan, zeby pomiar byl pomiarem. Ta sama pulapka,
#: co przy `MINIMUM_DEKLARACJI`: literowka w `dziury_interpolacji` dalaby zero dziur,
#: zero odzyskanych odczytow i zielona bramke — bo dzis zadna stala nie wyszlaby przez
#: to na martwa. Zapadka DOLNA, klasa WOLNA. Zmierzone 15.09.2026: **2116**
#: (2037 w postaci `$`, 69 w surowej interpolowanej, 10 w werbatim interpolowanej).
MINIMUM_DZIUR = 1800


def test_the_gate_sees_the_interpolation_holes_it_is_supposed_to_see():
    """Prog na liczbe dziur — bez niego oslepiony czytnik dziur jest dzis ZIELONY."""
    ile = sum(len(CTM.dziury_interpolacji(z)) for z in _tresc_csharp().values())
    assert ile >= MINIMUM_DZIUR, (
        "skan widzi %d dziur interpolacji przy progu %d — `dziury_interpolacji` "
        "przestalo pasowac do ksztaltu, w jakim to repozytorium pisze interpolacje"
        % (ile, MINIMUM_DZIUR))


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

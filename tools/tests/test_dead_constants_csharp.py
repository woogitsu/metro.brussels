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
#: Do 15.09.2026 **pusto**, i to bylo wynikiem pomiaru, nie zalozeniem: jedyna nieczytana
#: stala tego drzewa (`StationChainagesM`) zostala USUNIETA, bo byla prywatnym polem testu.
#:
#: **Pierwszy wpis doszedl przy 6.D214 i jest o SKANERZE, nie o stalej.** `CzlonWyrazenia`
#: jest czytana dwa razy — w obu wzorcach `.ToString()` — ale WYLACZNIE przez interpolacje
#: napisu (`$@"...{CzlonWyrazenia}..."`), a skan szuka nazwy jako osobnego slowa w kodzie.
#: Stala zyje, bramka jej nie widzi; usuniecie zlamaloby oba czytniki. Ile jeszcze stalych
#: C# jest czytanych wylacznie tak, nie policzyl nikt — wpisane jako 6.D225.
UZASADNIONE = {
    "CzlonWyrazenia": (
        "tests/Game.Tests/UiTextTests.cs",
        "czytana dwa razy, ale wylacznie przez interpolacje napisu w obu wzorcach "
        "`.ToString()`; skan szuka nazwy jako osobnego slowa i interpolacji nie widzi "
        "(6.D214, granica skanera zapisana jako 6.D225)"),
}


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
    """
    tresc = _tresc_csharp(root)
    znalezione = deklaracje(tresc, root)
    odczyty = _odczyty({k: CTM.maska(v) for k, v in tresc.items()})
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


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

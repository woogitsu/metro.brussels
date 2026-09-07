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
#: **Pusto** — i to jest wynik pomiaru, nie zalozenie. Jedyna nieczytana stala tego
#: drzewa (`StationChainagesM`) zostala USUNIETA, bo byla prywatnym polem testu, nikt
#: jej nie czytal i nie nalezala do zadnego udokumentowanego zbioru — inaczej niz
#: `LOCATION_STATION` po stronie Pythona, ktore spisuje wyliczenie GTFS.
UZASADNIONE = {}


def _pliki(root, rozszerzenia, drzewa=DRZEWA):
    for drzewo in drzewa:
        for katalog, _pod, pliki in os.walk(os.path.join(root, drzewo)):
            if os.sep + "obj" in katalog or os.sep + "bin" in katalog:
                continue
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
        for gdzie, _pod, pliki in os.walk(katalog):
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
    """Nazwa -> pliki deklaracji, dla stalych nieczytanych NIGDZIE."""
    tresc = _tresc_csharp(root)
    znalezione = deklaracje(tresc, root)
    odczyty = _odczyty(tresc)
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

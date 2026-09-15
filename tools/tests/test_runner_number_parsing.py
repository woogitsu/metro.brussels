#!/usr/bin/env python3
"""Wartosc nieliczbowa opcji odmawia komunikatem nazywajacym siebie (6.A14).

**Stan wyjsciowy.** Do 07.09.2026 kazda liczbowa opcja `Sim.Runner` szla wprost
w `double.Parse` / `long.Parse` / `int.Parse`, wiec `--limit-kmh abc` konczylo sie
komunikatem platformy .NET:

    BLAD: The input string 'abc' was not in a correct format.

Komunikat nie mowil ANI ktorej opcji dotyczy, ANI ktorego polecenia — a byl jedynym
sladem, jaki dostawal czytajacy. 6.D20 poprawila komunikat o BRAKU opcji; ten o zlej
WARTOSCI zostal wtedy nietkniety i to bylo swiadome.

**Dlaczego to jest bramka, a nie tylko testy C#.** Testy C# sprawdzaja komunikat
kilku opcji po jednej. Ta bramka czyta `Program.cs` jako TEKST i pilnuje, ze wartosc
opcji nie trafi w goly `Parse` w miejscu, ktorego nikt jeszcze nie otestowal — bo
nowa opcja dopisana golym `double.Parse` nie zlamie zadnego istniejacego testu.
Ujednolicenie, ktorego nikt nie pilnuje, rozjezdza sie przy pierwszej nowej opcji.

**Czego bramka NIE zabrania.** Rozbioru tresci PLIKU. `Compare` czyta komorki CSV
i tam komunikat nazywajacy opcje bylby nieprawda — zla komorka nie jest zla opcja.
To jedyny wpis w `USPRAWIEDLIWIENIA` i jest kluczowany METODA, nie numerem wiersza:
numer starzeje sie przy pierwszej wstawce (nauczka z 6.A20, gdzie klucz po nazwie
zmiennej pokazal to samo).

**Prog na liczbe miejsc rozbioru** stoi tu z tego samego powodu, co przy 6.B29,
6.B31 i 6.D27: bramka szukajaca wzorca, ktory przez literowke nie pasuje do niczego,
melduje zero znalezisk i swieci na zielono. Prog zamienia taka literowke w FAIL.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROGRAM = os.path.join(ROOT, "src", "Sim.Runner", "Program.cs")

#: Typy liczbowe, ktorych `Parse` bez `Try` nie mowi nic o opcji.
TYPY = ("double", "float", "decimal", "long", "int", "short", "uint", "ulong", "byte")

GOLY_PARSE = re.compile(r"\b(?:" + "|".join(TYPY) + r")\.Parse\s*\(")
TRY_PARSE = re.compile(r"\b(?:" + "|".join(TYPY) + r")\.TryParse\s*\(")

#: Deklaracja metody na poziomie klasy — do przypisania znaleziska do METODY.
DEKLARACJA = re.compile(
    r"^\s{4}(?:\[[^\]]*\]\s*)?(?:private|public|internal|protected)\s+"
    r"(?:static\s+)?(?:async\s+)?[\w<>?\[\],\s]+?\s+(\w+)\s*(?:\(|=>)")

#: Metody, ktorym goly `Parse` przysluguje, i POWOD kazdej. Powod jest czescia
#: wpisu, bo lista wymowek bez powodow rosnie sama.
#:
#: **Pusto od 07.09.2026, i wpis zdjety, a nie zostawiony na zapas.** Jedynym wpisem
#: byl `Compare` z powodem „rozbior komorek CSV, nie wartosci opcji — komunikat
#: nazywajacy opcje bylby tu nieprawda". Powod byl prawdziwy i nadal jest: zla komorka
#: nie jest zla opcja. Ale 6.A24 pokazala, ze nie wynika z niego prawo do KOMUNIKATU
#: PLATFORMY — wynika z niego tylko inny naglowek. `Compare` rozbiera dziś komorki
#: przez `Cell`, ktory nazywa plik, wiersz i kolumne, wiec golego `Parse` nie ma
#: w `Program.cs` ani jednego. Test zgodnosci w obie strony sam tego zazadal.
USPRAWIEDLIWIENIA = {}

#: Ile miejsc rozbioru liczby ma byc w `Program.cs` co najmniej.
#:
#: **Liczba przepisana 07.09.2026 przy 6.A24, i jako jedyna w tym repozytorium ZESZLA
#: w dol — dlatego stoi tu powod, a nie sama cyfra.** Poprzednia wersja mowila 6 i byla
#: prawdziwa: 2 gole `Parse` (komorki CSV w `Compare`) + 4 przez `TryParse`
#: (`NumberValue`, `LongValue`, `IntValue`, `ParseClock`). 6.A24 zamienila te DWA gole
#: wywolania na JEDEN wspolny pomocnik `Cell` z `TryParse`, wiec miejsc jest teraz
#: 0 + 5 = **5**. Spadek nie jest tu zluzowaniem bramki: gole `Parse` znikly z pliku
#: calkiem, co pilnuje osobny test, a ten prog pilnuje wylacznie tego, zeby literowka
#: we wzorcu nie dawala zera znalezisk i zielono.
#:
#: Przy DOPISANIU miejsca rosnie w tym samym commicie. Przy zamianie miejsca na inne
#: przelicza sie razem z pomiarem, tak jak tutaj — a nie zostaje na zapas, bo prog
#: wyzszy od stanu faktycznego padlby przy pierwszym przebiegu.
MINIMUM_MIEJSC = 5

#: Pomocnikow, ktore maja byc JEDYNA droga wartosci opcji do liczby: trzy.
#: (Ksztalt zdania zmieniony 15.09.2026 przy 6.D218: liczebnik stoi PO etykiecie,
#: wiec `WZORZEC_POMOCNIKOW` nie wymusza juz formy `pomocniki` — poprawnej po 3,
#: ale bledniej po kazdej liczbie spoza 2-4.)
POMOCNIKI = ("NumberValue", "LongValue", "IntValue")

#: Fragmenty komunikatu — bez polskich znakow diakrytycznych tam, gdzie to mozliwe,
#: zeby wzorzec nie zalezal od kodowania pliku testu.
KOMUNIKAT = "nie rozumie warto"
KONCOWKA = "nie jest liczb"


def _source():
    with open(PROGRAM, encoding="utf-8") as handle:
        return handle.read()


def _kod_bez_komentarzy(source):
    """`Program.cs` bez wierszy komentarza — wzmianka nie jest komunikatem.

    Dopisane przy 6.A24: docstring pomocnika `NieJestLiczba` WYJASNIA tresc
    komunikatu, wiec licznik pisarzy szukajacy zdania w surowym tekscie widzial
    dwoch tam, gdzie jest jeden. Bramka zapalajaca sie na poprawnym tekscie zostaje
    wylaczona, nie naprawiona (6.D27) — to ten sam warunek, ktory ma
    `test_runner_options.py`, i z tego samego powodu.
    """
    return "\n".join(
        line for line in source.splitlines()
        if not line.strip().startswith("//") and not line.strip().startswith("///"))


def metoda_dla_wiersza(lines, index):
    """Nazwa metody, w ktorej lezy wiersz `index` — najblizsza deklaracja przed nim."""
    for back in range(index, -1, -1):
        match = DEKLARACJA.match(lines[back])
        if match:
            return match.group(1)
    return "<poza metoda>"


def gole_parse(source):
    """Pary (metoda, tresc wiersza) dla kazdego golego `Parse` w kodzie.

    Wiersze komentarza i dokumentacji sa pomijane — `<c>double.Parse(text, Inv)</c>`
    w docstringu pomocnika OPISUJE to, co pomocnik zastapil, i zapalenie sie na nim
    byloby bramka swiecaca na poprawnym tekscie. Taka bramke sie wylacza, nie naprawia
    (nauczka z 6.D27 i 6.D30).
    """
    znaleziska = []
    lines = source.splitlines()
    for index, line in enumerate(lines):
        goly = line.strip()
        if goly.startswith("///") or goly.startswith("//"):
            continue
        for _ in GOLY_PARSE.finditer(line):
            znaleziska.append((metoda_dla_wiersza(lines, index), line.strip()))
    return znaleziska


def miejsca_rozbioru(source):
    """Ile razy `Program.cs` w ogole zamienia tekst na liczbe — gole plus `TryParse`."""
    kod = [
        line for line in source.splitlines()
        if not line.strip().startswith("///") and not line.strip().startswith("//")
    ]
    tekst = "\n".join(kod)
    return len(GOLY_PARSE.findall(tekst)) + len(TRY_PARSE.findall(tekst))


def test_no_option_value_reaches_a_bare_parse():
    """Zadna wartosc opcji nie idzie w goly `Parse` — poza usprawiedliwionymi."""
    znaleziska = gole_parse(_source())
    obce = [(m, l) for m, l in znaleziska if m not in USPRAWIEDLIWIENIA]
    assert obce == [], (
        "goly Parse poza lista usprawiedliwien — wartosc opcji odmowi komunikatem "
        "platformy .NET, ktory nie nazwie ani opcji, ani polecenia (6.A14). "
        "Uzyj NumberValue/LongValue/IntValue. Znaleziska: " + repr(obce))


def test_the_allow_list_is_exact_in_both_directions():
    """Kazde usprawiedliwienie ma tyle wystapien, ile obiecuje — i ani jednego wiecej.

    Kontrola w OBIE strony: wpis, ktory przestal byc potrzebny, tez jest bledem —
    inaczej lista wymowek zostaje po poprawce i przepuszcza nastepny goly Parse
    w tej samej metodzie.
    """
    znaleziska = gole_parse(_source())
    # Asercja BEZWARUNKOWA, nie petla po wpisach: przy pustej liscie petla nie
    # wykonalaby ani jednej asercji i test bylby cichym skipem — co przy 6.A24
    # zlapal `assertion_gate` (#139), gdy lista opustoszala. Zbior metod z golym
    # `Parse` ma byc DOKLADNIE zbiorem kluczy listy, w obie strony naraz.
    z_golym = sorted({m for m, _ in znaleziska})
    assert z_golym == sorted(USPRAWIEDLIWIENIA), (
        "metody z golym Parse: " + repr(z_golym) + ", a lista usprawiedliwien mowi "
        + repr(sorted(USPRAWIEDLIWIENIA)) + " — wpis bez znaleziska opisuje stan "
        "miniony i przepusci nastepny goly Parse w tej samej metodzie")
    for metoda, (ile, powod) in USPRAWIEDLIWIENIA.items():
        rzeczywiste = [l for m, l in znaleziska if m == metoda]
        assert len(rzeczywiste) == ile, (
            "usprawiedliwienie dla " + metoda + " obiecuje " + str(ile)
            + " wystapien golego Parse, a jest " + str(len(rzeczywiste))
            + ". Powod wpisu: " + powod + ". Wiersze: " + repr(rzeczywiste))
        assert powod.strip(), "wpis " + metoda + " nie ma powodu"


def test_parse_site_count_is_above_the_floor():
    """Prog na liczbe miejsc rozbioru — literowka we wzorcu ma dawac FAIL, nie zero."""
    ile = miejsca_rozbioru(_source())
    assert ile >= MINIMUM_MIEJSC, (
        "miejsc rozbioru liczby jest " + str(ile) + " przy progu "
        + str(MINIMUM_MIEJSC) + " — albo wzorzec przestal pasowac, albo rozbior "
        "przeniosl sie gdzie indziej; jedno i drugie trzeba zobaczyc, a nie przegapic")


def test_one_writer_of_the_message():
    """`NotANumber` jest jedynym pisarzem tresci — trzy pomocniki go WOLAJA."""
    source = _source()
    kod = _kod_bez_komentarzy(source)
    assert kod.count("private static string NotANumber(") == 1, (
        "NotANumber ma byc zadeklarowany dokladnie raz")
    assert kod.count(KOMUNIKAT) == 1, (
        "tresc komunikatu o nieliczbowej wartosci stoi w " + str(kod.count(KOMUNIKAT))
        + " miejscach zamiast w jednym — dwoch pisarzy rozjedzie sie przy pierwszej "
        "poprawce, dokladnie jak przy 6.A20")
    assert kod.count(KONCOWKA) == 1, (
        "koncowka komunikatu stoi w " + str(kod.count(KONCOWKA)) + " miejscach zamiast "
        "w jednym. Od 6.A24 sa DWA naglowki (opcja i komorka pliku) i to jest wlasciwe "
        "— zla komorka nie jest zla opcja — ale zdanie o tym, ze wartosc nie jest "
        "liczba, ma jednego pisarza: `NieJestLiczba`")
    assert kod.count("private static string NieJestLiczba(") == 1, (
        "wspolna koncowka ma byc zadeklarowana dokladnie raz")
    for pomocnik in POMOCNIKI:
        assert "private static " in source and pomocnik + "(" in source, (
            "brak pomocnika " + pomocnik)
        cialo = source.split(pomocnik + "(string command, string name, string text)")[-1][:400]
        assert "NotANumber(command, name, text)" in cialo, (
            pomocnik + " nie wola NotANumber — tresc komunikatu ma jednego pisarza")


def test_no_helper_hardcodes_the_command_name():
    """Nazwa polecenia bierze sie z `args[0]`, nie z nowej zaszytej stalej (6.D20)."""
    source = _source()
    assert source.count("private static string Command(string[] args)") == 1, (
        "Command(args) ma byc jednym zrodlem nazwy polecenia")
    poczatek = source.index("private static string NotANumber(")
    naglowek = source[poczatek:poczatek + 300]
    assert "{command}" in naglowek, "NotANumber ma brac nazwe polecenia z argumentu"
    for polecenie in ("line", "budget", "replay", "drive", "compare", "service-day"):
        assert '"' + polecenie + ' nie rozumie' not in source, (
            "tresc komunikatu ma zaszyta nazwe polecenia " + polecenie
            + " — to ten sam blad, ktory 6.D20 wyjela z RequiredNumber")


def test_detector_lights_up_on_injected_bare_parse():
    """Kontrola dodatnia jako TEST, nie jako zdanie w docstringu (wzorzec 6.B24)."""
    wstrzykniete = "\n".join([
        "public static class Atrapa",
        "{",
        "    private static int Zmyslone(string[] args)",
        "    {",
        '        var x = double.Parse(Option(args, "--zmyslona"), Inv);',
        "        return 0;",
        "    }",
        "}",
    ])
    znaleziska = gole_parse(wstrzykniete)
    assert [m for m, _ in znaleziska] == ["Zmyslone"], (
        "detektor nie zobaczyl golego Parse we wstrzyknietym kodzie albo przypisal "
        "go do zlej metody: " + repr(znaleziska))


def test_detector_stays_quiet_on_the_helper_shape():
    """...i milczy na ksztalcie, ktory jest poprawka — inaczej mierzylby cokolwiek."""
    wstrzykniete = "\n".join([
        "public static class Atrapa",
        "{",
        "    private static double Poprawne(string command, string name, string text)",
        "    {",
        "        if (!double.TryParse(text, NumberStyles.Float, Inv, out var value))",
        "        {",
        "            throw new ArgumentException(NotANumber(command, name, text));",
        "        }",
        "",
        "        return value;",
        "    }",
        "}",
    ])
    assert gole_parse(wstrzykniete) == [], (
        "detektor zapalil sie na TryParse — `TryParse` zawiera `Parse` jako podciag "
        "i wzorzec bez granicy slowa lapalby wlasna poprawke")


def test_detector_ignores_documentation_lines():
    """Wzmianka w docstringu nie jest wywolaniem — inaczej bramka swieci na tekscie."""
    wstrzykniete = "\n".join([
        "public static class Atrapa",
        "{",
        "    /// <summary>Zbior postaci ten sam, co mial <c>double.Parse(text, Inv)</c>.</summary>",
        "    private static double Poprawne(string command, string name, string text)",
        "    {",
        "        // dawniej: int.Parse(text, Inv)",
        "        return 0.0;",
        "    }",
        "}",
    ])
    assert gole_parse(wstrzykniete) == [], (
        "detektor zapalil sie na komentarzu — bramka zapalajaca sie na poprawnym "
        "tekscie zostaje wylaczona, nie naprawiona")


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

#!/usr/bin/env python3
"""Swoistość igły `StringAssert.Contains` wobec ZAMKNIĘTEJ rodziny komunikatów runnera.

**Po co ta bramka istnieje.** `reports/audyt-asercji.md` §7 nazwał ten pomiar
**rozstrzygającym** i świadomie go nie wykonał: „czy igła asercji występuje w INNYM
komunikacie tego samego programu". 6.A32 zamknęło się bez bramki, bo przyrząd liczący
*kształt* asercji łapał 0 z 4 znanych przypadków dnia; wniosek tamtej pozycji brzmiał,
że rozstrzyga **swoistość igły**, a to jest zdanie o kodzie produkcyjnym, nie o tekście
testu. `StringAssert.Contains(err, "line")` przechodzi przy odmowie o czymkolwiek — i to
jest dosłownie usterka 6.A29, tylko widziana od strony igły, a nie od strony testu.

**Dlaczego to jest wykonalne, choć 6.A32 nie było.** Rodzina komunikatów jest
**zamknięta**: literały `src/Sim.Runner/Program.cs` da się wyliczyć z jednego pliku,
więc pytanie „ile komunikatów zawiera tę igłę" ma odpowiedź liczbową, a nie
heurystykę. 6.A32 pytało o kształt asercji w całym zestawie, gdzie żadnej zamkniętej
rodziny nie ma.

**Czym jest KOMUNIKAT w tej bramce, i to jest decyzja, nie szczegół.** Komunikat to
**maksymalna grupa literałów zszytych `+`** — bo w C# jedno zdanie odmowy stoi
regularnie w trzech literałach obok siebie i policzenie ich jako trzech komunikatów
zmyśliłoby niejednoznaczność, której nie ma. Grupa jest brana pod warunkiem, że jest
**wielowyrazowa**: literał jednowyrazowy w tym pliku to nazwa opcji z tabeli, nagłówek
CSV albo klucz słownika, a nie zdanie do czytania. Dziury interpolacji zostają w treści
w postaci źródłowej (`{command}`), bo to jest tekst, który w pliku NAPRAWDĘ stoi.

**CZEGO TA BRAMKA NIE ROBI, ŚWIADOMIE — i dlaczego ma trzeci szczebel.** Nie rozwiązuje
interpolacji. Komunikat `$"{command} nie rozumie wartości {name}: "` daje przy różnych
argumentach różne zdania i statyczny czytnik nie wie których; igła `line nie rozumie
wartości --limit-kmh` nie pasuje więc do ŻADNEGO literału, choć runner dokładnie to
wypisuje. Igieł bez ani jednego dopasowania jest dziś **33 z 68** i bramka ich nie
zgłasza, bo nie ma o nich nic prawdziwego do powiedzenia. Ma natomiast **zapadkę na ich
liczbę** (`MAX_UNMATCHED_NEEDLES`) — bez niej najtańszym sposobem uciszenia szczebla 1
byłoby przepisanie igły na tekst, którego w literałach nie ma wcale, czyli zamiana
niejednoznaczności na niewidzialność.

**Trzy szczeble, bo trzy różne rzeczy.**

1. Igła zawarta w WIĘCEJ NIŻ JEDNYM komunikacie — zgłoszenie. Naprawia się
   **w teście** (wzmocnienie igły), nie w programie: treść komunikatów `Program.cs`
   jest poza zakresem pozycji 6.A33.
2. Igła niejednoznaczna Z DOBREGO POWODU — wpis na liście `JUSTIFICATIONS` z powodem
   podanym zdaniem. Asercja o nazwie polecenia albo opcji MA pasować do wielu
   komunikatów, bo nazwa opcji stoi i w wypisie pomocy, i w każdej odmowie o niej.
   Lista jest **zamknięta zapadką z obu stron** (wzorzec 6.A31), bo wpis tańszy od
   wzmocnienia igły rośnie po cichu.
3. Igła bez ani jednego dopasowania — poza zakresem werdyktu, ale POD ZAPADKĄ; patrz
   akapit wyżej.

**KONTROLE — każda WYKONANA, wypisane w `reports/swoistosc-igly.md`:**

  KD (dodatnia)  osłabienie igły `axis wymaga --axis` do `--axis` wywraca dokładnie
                 szczebel 1 tej bramki i nic więcej.
                 Pilnuje tego `test_a_weakened_needle_lights_up_the_first_rung`.
  KU (ujemna)    igła jednoznaczna NIE jest zgłaszana, a mutacja warunku `> 1`
                 na `>= 1` PRZENOSI zbiór zgłoszeń — czyli „nie zgłasza" jest
                 rozróżnieniem, nie pustym zbiorem.
                 Pilnuje tego `test_a_specific_needle_is_never_reported`.
  KP (przyrząd)  dopisanie do `Program.cs` drugiego komunikatu z istniejącą igłą
                 PODNOSI jej licznik, więc bramka czyta plik, a nie tabelę wpisaną
                 z pamięci. Pilnuje tego `test_the_verdict_follows_the_program_file`.
  KW (wzorzec)   wzorzec zepsuty daje ZERO komunikatów i ZERO igieł, a wtedy cały
                 moduł świeci zielono. Pilnują tego progi `MIN_MESSAGES`
                 i `MIN_NEEDLES`.
"""

import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csharp_test_methods as CTM  # noqa: E402

#: Plik, z którego bierze się ZAMKNIĘTA rodzina komunikatów.
PROGRAM = os.path.join("src", "Sim.Runner", "Program.cs")

#: Plik z igłami. Testy runnera, bo o nich mówi pomiar 6.A32 i pozycja 6.A33;
#: `tests/Game.Tests` ma osobną rodzinę (`RunPlan`) i osobną pozycję — 6.D34.
TESTS = os.path.join("tests", "Sim.Tests", "RunnerCommandTests.cs")

#: Asercja, której drugi argument jest igłą.
ASSERTION = "StringAssert.Contains"

#: Igły niejednoznaczne Z POWODEM. Klucz to treść igły — nie numer wiersza, bo numer
#: przesuwa każdy commit dopisujący cokolwiek wyżej, a bramka zapalająca się na tekście
#: poprawnym zostaje wyłączona, nie naprawiona (6.D27).
JUSTIFICATIONS = {
    "line":
        "Sedno 6.D20, przeniesione tu z nazwy: `RequiredNumber` mówiło `line` także "
        "wtedy, gdy uruchomiono `budget`, więc test `Line_z_nieliczbowym_limitem_...` "
        "asertuje NAZWĘ WOŁANEGO POLECENIA, a nie treść jednej odmowy. Nazwa polecenia "
        "stoi w wypisie pomocy i w odmowie `line wymaga --axis`, i tak ma być; "
        "wzmocnienie igły do `line nie rozumie wartości --limit-kmh` odebrałoby testowi "
        "to, co mierzy z nazwy, i wpadłoby na szczebel 3, bo tego zdania nie ma "
        "w żadnym literale — składa je interpolacja.",
    "budget":
        "Ta sama para co wyżej, druga połowa kontroli 6.D20: "
        "`Budget_z_nieliczbowym_limitem_nazywa_budget_a_nie_line` istnieje po to, żeby "
        "poprawka zaszywająca nową sztywną nazwę nie przeszła. Igła jest nazwą "
        "polecenia, a nazwa polecenia jest w tym pliku w siedmiu komunikatach — "
        "to własność `Program.cs`, nie słabość testu.",
    "--limit-kmh":
        "Nazwa opcji w trzech różnych testach (nieliczbowa wartość w `line`, "
        "w `budget`, powtórzona opcja). Każdy z nich stawia ją OBOK igły swoistej "
        "(`abc`, `więcej niż raz`), a sama nazwa opcji stoi i w wypisie pomocy, "
        "i w dwóch odmowach `replay` — asercja o nazwie opcji MA pasować do wielu "
        "komunikatów, bo inaczej nie byłaby asercją o nazwie opcji.",
    "--trains":
        "Dwa testy, dwie różne role, obie o NAZWIE opcji: "
        "`Odmowa_wymienia_opcje_tego_polecenia_a_nie_wszystkich` żąda, żeby lista "
        "znanych nazw była listą TEGO polecenia, a `Trains_cytuje_zly_czlon...` — żeby "
        "odmowa nazwała opcję, której członu nie zrozumiała. Obie treści są składane "
        "z listy w czasie wykonania, więc igła swoista nie istnieje.",
    "--at":
        "To samo w drugą stronę i to jest cała treść testu "
        "`Odmowa_wymienia_opcje_tego_polecenia_a_nie_wszystkich`: `--at` MA być "
        "w odmowie `service-day`, a `--trains` NIE ma być w niej jako opcja znana. "
        "Igła jest nazwą opcji i pasuje do wypisu pomocy oraz do odmowy o `--atp`, "
        "bo `--at` jest jej przedrostkiem.",
    "--steps":
        "Nazwa opcji w `Budget_z_nieliczbowa_liczba_krokow_nazywa_steps`. Komunikat, "
        "który ten test naprawdę oglądа, jest składany interpolacją "
        "(`{command} nie rozumie wartości {name}`), więc oba dopasowania — wypis pomocy "
        "i odmowa o BRAKU opcji — dotyczą komunikatów innych niż mierzony. Wzmocnienie "
        "igły w tym miejscu jest niewykonalne bez zmiany treści komunikatu, a to jest "
        "pole „Poza zakresem\" pozycji 6.A33.",
    "step":
        "Nazwa KOLUMNY telemetrii, nie opcji: test "
        "`Zepsuta_komorka_nazywa_plik_wiersz_i_kolumne` żąda, żeby odmowa o komórce "
        "nazwała kolumnę po imieniu. Nazwa kolumny stoi w nagłówku CSV, w wypisie "
        "pomocy (`--sample-every`… i `kroków`) oraz w komunikatach `[BUDŻET]` — a igła "
        "stoi w tym teście obok czterech innych (`wiersz 3`, `kolumna 1`, `abc`, "
        "ścieżka pliku), które razem wskazują jeden komunikat.",
}

#: Zapadka na listę wyżej, z OBU stron. Bez dolnego ostrza zapadka stałaby wyżej niż
#: lista i przyjmowałaby nowe wpisy bez śladu w diffie — dokładnie to zamknęło 6.A31.
#:
#: **Nazwa nie jest `MAX_JUSTIFICATIONS`, choć wzorzec jest ten sam, i to nie jest
#: przypadek.** `test_bin_path_framework.py` nosi stałą o tej nazwie i o innej wartości
#: (14), a `test_constant_names.py` żąda, żeby jedna nazwa przy dwóch wartościach albo
#: była poprawiona, albo uzasadniona wpisem w SWOJEJ liście. Tu nazwa jest po prostu
#: za ogólna: to nie jest „maksimum usprawiedliwień w ogóle", tylko maksimum
#: usprawiedliwionych IGIEŁ, więc poprawiam nazwę, a nie dopisuję wyjątku do cudzej
#: bramki (`CLAUDE.md` §4.10).
MAX_JUSTIFIED_NEEDLES = 7

#: Zapadka na igły bez ani jednego dopasowania (szczebel 3). Zmierzone 07.09.2026:
#: **33 z 68**. Rośnie tylko przez przepisanie igły na tekst, którego w literałach nie
#: ma — czyli przez zamianę niejednoznaczności na niewidzialność — i dlatego jest
#: zapadką, a nie wypisem.
MAX_UNMATCHED_NEEDLES = 33

#: Progi KW. Literówka we wzorcu daje zero dopasowań i cały moduł zielony; te dwie
#: liczby są jedynym powodem, dla którego taka literówka jest widoczna. Zmierzone
#: 07.09.2026 na `2ffb0b0`: **97** wielowyrazowych grup literałów w `Program.cs`
#: i **68** różnych igieł w 85 wywołaniach `StringAssert.Contains` (dwa wywołania mają
#: igłę w zmiennej, nie w literale, i te nie są mierzalne z tekstu).
MIN_MESSAGES = 97
MIN_NEEDLES = 68

#: Igła, na której stoją kontrole dodatnia i przyrządu. Musi być SWOISTA (dokładnie
#: jeden komunikat) i musi stać w teście — obie kontrole mówią to wprost w komunikacie
#: awarii, bo bez tego zniknięcie próbki wyglądałoby jak zepsuta bramka.
PROBKA = "axis wymaga --axis"


def _read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
        return handle.read()


def _spany(source):
    """`[(start, koniec)]` literałów napisowych — te same prymitywy, co `CTM.maska`.

    Jeden czytnik C# (6.D30): granice literału liczy `CTM._koniec_literalu`, więc maska
    i ta lista nie mogą się rozjechać. Pilnuje tego
    `test_the_literal_spans_agree_with_the_mask`.
    """
    out = []
    i = 0
    n = len(source)
    while i < n:
        znak = source[i]
        if znak == "/" and i + 1 < n and source[i + 1] == "/":
            koniec = source.find("\n", i)
            i = n if koniec < 0 else koniec
            continue
        if znak == "/" and i + 1 < n and source[i + 1] == "*":
            koniec = source.find("*/", i + 2)
            i = n if koniec < 0 else koniec + 2
            continue
        if znak in "@$" or znak == '"':
            start = i
            j = i
            verbatim = False
            while j < n and source[j] in "@$":
                verbatim = verbatim or source[j] == "@"
                j += 1
            if j < n and source[j] == '"':
                koniec = CTM._koniec_literalu(source, j, verbatim)
                out.append((start, koniec))
                i = koniec
                continue
            i = j if j > start else i + 1
            continue
        if znak == "'":
            i = CTM._koniec_znaku(source, i)
            continue
        i += 1
    return out


def tresc_literalu(raw):
    """Tekst literału bez przedrostków i cudzysłowów, z rozwiniętymi ucieczkami.

    Dziury interpolacji ZOSTAJĄ w postaci źródłowej (`{command}`) — to jest tekst,
    który w pliku naprawdę stoi, a bramka mówi o tekście pliku, nie o wykonaniu.
    """
    j = 0
    verbatim = False
    while j < len(raw) and raw[j] in "@$":
        verbatim = verbatim or raw[j] == "@"
        j += 1
    body = raw[j:]
    cudzyslowy = 0
    while cudzyslowy < len(body) and body[cudzyslowy] == '"':
        cudzyslowy += 1
    if cudzyslowy >= 3:
        zamkniecie = '"' * cudzyslowy
        return body[cudzyslowy:-cudzyslowy] if body.endswith(zamkniecie) else body[cudzyslowy:]
    body = body[1:-1] if len(body) > 1 and body.endswith('"') else body[1:]
    if verbatim:
        return body.replace('""', '"')
    return (body.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "")
            .replace('\\"', '"').replace("\\\\", "\\"))


def _numer_wiersza(source, at):
    return source.count("\n", 0, at) + 1


def komunikaty(source):
    """`[(wiersz, tekst)]` — maksymalne grupy literałów zszytych `+`, wielowyrazowe.

    Zszycie idzie po MASCE: między końcem jednego literału a początkiem następnego
    wolno stać wyłącznie białym znakom i plusom (komentarz maska zamienia na spacje).
    Bez zszycia jedno zdanie odmowy stojące w trzech literałach byłoby trzema
    komunikatami i bramka zmyśliłaby niejednoznaczność, której nie ma.
    """
    maska = CTM.maska(source)
    grupy = []
    poprzedni = None
    for start, koniec in _spany(source):
        if grupy and poprzedni is not None and set(maska[poprzedni:start]) <= set(" \t\r\n+"):
            grupy[-1][1].append(tresc_literalu(source[start:koniec]))
        else:
            grupy.append((start, [tresc_literalu(source[start:koniec])]))
        poprzedni = koniec
    out = []
    for start, czesci in grupy:
        tekst = "".join(czesci)
        if len(tekst.split()) > 1:
            out.append((_numer_wiersza(source, start), tekst))
    return out


def igly(source):
    """`{igła: [wiersze testu]}` dla `StringAssert.Contains(cokolwiek, "igła")`.

    Argumenty cięte po MASCE i po nawiasach, nie regexem na jednym wierszu: jedno
    wywołanie w tym pliku jest rozbite na dwa wiersze i wzorzec wierszowy je gubi.
    Wywołanie, którego druga pozycja nie jest JEDNYM literałem (igła w zmiennej),
    jest pomijane — z tekstu nie da się powiedzieć, jaki to napis.
    """
    maska = CTM.maska(source)
    out = {}
    for wywolanie in re.finditer(re.escape(ASSERTION) + r"\s*\(", maska):
        start = wywolanie.end() - 1
        glebokosc = 0
        koniec = None
        for i in range(start, len(maska)):
            if maska[i] == "(":
                glebokosc += 1
            elif maska[i] == ")":
                glebokosc -= 1
                if glebokosc == 0:
                    koniec = i
                    break
        if koniec is None:
            continue
        granice = []
        glebokosc = 0
        ostatni = start + 1
        for i in range(start + 1, koniec):
            znak = maska[i]
            if znak in "([{":
                glebokosc += 1
            elif znak in ")]}":
                glebokosc -= 1
            elif znak == "," and glebokosc == 0:
                granice.append((ostatni, i))
                ostatni = i + 1
        granice.append((ostatni, koniec))
        if len(granice) < 2:
            continue
        od, do = granice[1]
        surowy = source[od:do].strip()
        spany = _spany(surowy)
        if len(spany) != 1 or spany[0] != (0, len(surowy)):
            continue
        igla = tresc_literalu(surowy)
        out.setdefault(igla, []).append(_numer_wiersza(source, od))
    return out


def licznik(program=None, testy=None, prog=1):
    """`{igła: ile komunikatów ją zawiera}`. `prog` służy WYŁĄCZNIE mutacji w KU."""
    program = _read(PROGRAM) if program is None else program
    testy = _read(TESTS) if testy is None else testy
    wiadomosci = [tekst for _wiersz, tekst in komunikaty(program)]
    return {igla: sum(1 for tekst in wiadomosci if igla in tekst)
            for igla in igly(testy)}


def zgloszenia(program=None, testy=None, prog=1):
    """Igły przekraczające `prog` dopasowań, BEZ wpisu na liście usprawiedliwień."""
    trafienia = licznik(program, testy)
    return sorted(igla for igla, ile in trafienia.items()
                  if ile > prog and igla not in JUSTIFICATIONS)


def bez_dopasowania(program=None, testy=None):
    trafienia = licznik(program, testy)
    return sorted(igla for igla, ile in trafienia.items() if ile == 0)


# --------------------------------------------------------------------------- testy


def test_the_message_family_and_the_needles_are_both_read_from_the_files():
    """Próg KW: zepsuty wzorzec daje zero i cały moduł świeci zielono.

    To jest najczęstszy sposób, w jaki bramka kłamie w stronę „wszystko w porządku",
    i jedyny powód, dla którego ten test stoi osobno od pozostałych.
    """
    wiadomosci = komunikaty(_read(PROGRAM))
    igielki = igly(_read(TESTS))
    assert len(wiadomosci) >= MIN_MESSAGES, (
        "wzorzec złapał %d wielowyrazowych komunikatów, a 07.09.2026 było ich %d — "
        "spadek znaczy zepsuty czytnik, nie posprzątany plik"
        % (len(wiadomosci), MIN_MESSAGES))
    assert len(igielki) >= MIN_NEEDLES, (
        "wzorzec złapał %d różnych igieł, a 07.09.2026 było ich %d"
        % (len(igielki), MIN_NEEDLES))
    assert all(wiersz > 0 for wiersz, _tekst in wiadomosci)


def test_every_needle_matches_at_most_one_message_or_is_justified():
    """Szczebel 1 i 2 razem: zgłoszenie albo wpis z powodem, trzeciej drogi nie ma."""
    trafienia = licznik()
    bad = ["%r w %d komunikatach (test w wierszach %s)"
           % (igla, trafienia[igla], igly(_read(TESTS))[igla])
           for igla in zgloszenia()]
    assert bad == [], (
        "igła asercji pasuje do więcej niż jednego komunikatu `Program.cs` i nie ma "
        "wpisu z powodem — wzmocnij ją w teście albo wpisz na listę: %s" % bad)


def test_a_specific_needle_is_never_reported():
    """KU: bramka łapiąca igłę POPRAWNĄ zostałaby wyłączona w tym samym tygodniu.

    Nie wystarczy, że nic się nie zgłasza — trzeba pokazać, że igły jednoznaczne
    W PLIKU SĄ, że żadna z nich nie trafia do zgłoszeń, i że przesunięcie warunku
    `> 1` na `>= 1` PRZENOSI zbiór zgłoszeń. Bez ostatniego członu ten test
    przechodziłby także wtedy, gdyby wzorzec nie łapał niczego.
    """
    trafienia = licznik()
    jednoznaczne = {igla for igla, ile in trafienia.items() if ile == 1}
    assert len(jednoznaczne) >= 20, sorted(jednoznaczne)
    assert not jednoznaczne & set(zgloszenia())
    przy_jedynce = set(zgloszenia(prog=1))
    przy_zerze = set(zgloszenia(prog=0))
    assert przy_zerze > przy_jedynce, (sorted(przy_jedynce), sorted(przy_zerze))
    assert jednoznaczne <= przy_zerze, sorted(jednoznaczne - przy_zerze)


def test_the_verdict_follows_the_program_file():
    """KP: dopisanie DRUGIEGO komunikatu z istniejącą igłą podnosi jej licznik.

    Bez tego testu „bramka czytająca `Program.cs`" byłaby nieodróżnialna od tabeli
    liczb wpisanej z pamięci: obie dają dziś ten sam werdykt.
    """
    program = _read(PROGRAM)
    igla = PROBKA
    przed = licznik(program=program)
    assert przed.get(igla) == 1, (
        "igła-przyrząd %r nie stoi już w teście albo nie jest swoista (licznik %r) — "
        "kontrola przyrządu straciła punkt odniesienia" % (igla, przed.get(igla)))
    dopisany = program + '\n// osłona: Console.Error.WriteLine("axis wymaga --axis, drugi raz");\n'
    # Komentarz maska zamienia na spacje, więc dopisek MUSI być kodem, nie komentarzem —
    # i to samo w sobie jest kontrolą tego, że bramka nie liczy komentarzy.
    assert licznik(program=dopisany)[igla] == 1, "bramka policzyła literał z komentarza"
    kod = program + '\nstatic class Oslona { const string X = "axis wymaga --axis, drugi raz"; }\n'
    po = licznik(program=kod)
    assert po[igla] == 2, po[igla]
    assert igla in zgloszenia(program=kod), "podniesiony licznik nie trafił do zgłoszeń"


def test_a_weakened_needle_lights_up_the_first_rung():
    """KD: osłabienie igły swoistej do wieloznacznej wywraca szczebel 1.

    Na wejściu wstrzykniętym, bo bramka ma dziś szczebel 1 pusty i sam jego zielony
    kolor nie dowodzi niczego (ta sama zasada, co przy 6.A31).
    """
    testy = _read(TESTS)
    assert PROBKA in testy, (
        "igła-przyrząd %r zniknęła z %s — kontrola dodatnia nie ma czego osłabiać"
        % (PROBKA, TESTS.replace(os.sep, "/")))
    oslabione = testy.replace('"%s"' % PROBKA, '"--axis"')
    assert oslabione != testy, PROBKA
    assert zgloszenia(testy=testy) == [], (
        "szczebel 1 zapalony JUŻ przed osłabieniem: %s — kontrola dodatnia nie "
        "pokazuje wtedy niczego" % zgloszenia(testy=testy))
    assert "--axis" in zgloszenia(testy=oslabione), zgloszenia(testy=oslabione)


def test_the_needle_reader_tells_a_literal_from_a_variable():
    """Granica czytnika igieł, w obie strony, na wejściu syntetycznym.

    Bez tego `igly` mogłaby zwracać pusty słownik na wszystkim — a wtedy bramka
    byłaby zielona zawsze, i to jest najczęstszy sposób, w jaki kłamie w stronę
    „w porządku".
    """
    probka = "\n".join([
        'class T {',
        '  void A() {',
        '    StringAssert.Contains(result.StdErr, "swoista igła");',
        '    StringAssert.Contains(result.StdErr, zmienna);',
        '    StringAssert.Contains(',
        '        result.StdErr, "igła z dwóch wierszy");',
        '    StringAssert.Contains(wynik.StdOut, "z, przecinkiem");',
        '  }',
        '}',
    ])
    znalezione = igly(probka)
    assert set(znalezione) == {"swoista igła", "igła z dwóch wierszy", "z, przecinkiem"}, znalezione
    assert znalezione["igła z dwóch wierszy"] == [6], znalezione


def test_the_message_reader_stitches_concatenations_and_drops_one_word_literals():
    """Granica czytnika komunikatów, na wejściu syntetycznym.

    Dwa rozstrzygnięcia naraz: zdanie zszyte z trzech literałów jest JEDNYM
    komunikatem (inaczej bramka zmyśla niejednoznaczność), a literał jednowyrazowy
    komunikatem nie jest (inaczej każda nazwa opcji z tabeli jest komunikatem).
    """
    probka = "\n".join([
        'class P {',
        '  static string[] Tabela = new[] { "--axis", "--limit-kmh" };',
        '  static void M() {',
        '    Console.Error.WriteLine("odmowa w trzech "',
        '        + "czesciach, jedno "',
        '        + "zdanie");',
        '    Console.Out.WriteLine("drugie zdanie osobno");',
        '  }',
        '}',
    ])
    teksty = [tekst for _wiersz, tekst in komunikaty(probka)]
    assert "odmowa w trzech czesciach, jedno zdanie" in teksty, teksty
    assert "drugie zdanie osobno" in teksty, teksty
    assert "--axis" not in teksty and "--limit-kmh" not in teksty, teksty
    assert len(teksty) == 2, teksty


def test_the_literal_spans_agree_with_the_mask():
    """Jeden czytnik C#: każdy literał `_spany` jest w masce zamazany, znak w znak.

    Dwa przejścia po tym samym drzewie rozjeżdżają się po cichu (6.D30) — a maska
    i lista literałów to dokładnie dwa spojrzenia na jedną strukturę.
    """
    source = _read(PROGRAM)
    maska = CTM.maska(source)
    assert len(maska) == len(source)
    spany = _spany(source)
    assert len(spany) > 200, len(spany)
    for start, koniec in spany:
        wycinek = maska[start:koniec]
        assert set(wycinek) <= {" ", "\n"}, (start, koniec, repr(wycinek[:40]))


def test_every_justification_still_describes_an_ambiguous_needle():
    """Usprawiedliwienie nie może przeżyć igły, którą opisuje.

    Wpis, którego nie ma czego usprawiedliwiać, jest dziurą w bramce ubraną w prozę —
    ta sama zasada, którą 6.D29 postawiło dla listy wyjątków raportów, 6.B34 dla
    martwych stałych i 6.A31 dla ścieżek `bin/`.
    """
    trafienia = licznik()
    martwe = sorted(igla for igla in JUSTIFICATIONS if trafienia.get(igla, 0) <= 1)
    assert martwe == [], (
        "usprawiedliwienie igły, która niejednoznaczna już nie jest: %s" % martwe)
    puste = sorted(igla for igla, powod in JUSTIFICATIONS.items()
                   if len(powod.strip()) < 40)
    assert puste == [], "usprawiedliwienie bez powodu podanego zdaniem: %s" % puste


def test_the_justification_list_stays_closed():
    """Zapadka z obu stron: wpis tańszy od wzmocnienia igły rośnie po cichu."""
    assert len(JUSTIFICATIONS) <= MAX_JUSTIFIED_NEEDLES, (
        "lista usprawiedliwień urosła do %d przy zapadce %d — igła ma zostać wzmocniona "
        "w teście, a nie dostać miejsce na liście"
        % (len(JUSTIFICATIONS), MAX_JUSTIFIED_NEEDLES))
    assert MAX_JUSTIFIED_NEEDLES <= len(JUSTIFICATIONS), (
        "zapadka %d stoi wyżej niż lista (%d) — obniż ją do stanu faktycznego"
        % (MAX_JUSTIFIED_NEEDLES, len(JUSTIFICATIONS)))


def test_needles_without_a_single_match_stay_under_a_ratchet():
    """Szczebel 3: zamiana niejednoznaczności na niewidzialność musi być widoczna.

    Igła przepisana na tekst, którego w literałach nie ma wcale, ucisza szczebel 1
    i nie zgłasza się nigdzie — chyba że jej liczba stoi pod zapadką. Wtedy trzeba
    ją podnieść w tym samym commicie, czyli w diffie.
    """
    bez = bez_dopasowania()
    assert len(bez) <= MAX_UNMATCHED_NEEDLES, (
        "igieł bez ani jednego dopasowania jest %d przy zapadce %d: %s"
        % (len(bez), MAX_UNMATCHED_NEEDLES, bez))
    assert MAX_UNMATCHED_NEEDLES <= len(bez), (
        "zapadka %d stoi wyżej niż stan faktyczny (%d) — obniż ją"
        % (MAX_UNMATCHED_NEEDLES, len(bez)))


def main():
    """Inwentarz do wklejenia w raport: wszystkie igły z licznikiem i wyrokiem."""
    program = _read(PROGRAM)
    testy = _read(TESTS)
    wiadomosci = komunikaty(program)
    igielki = igly(testy)
    trafienia = licznik(program, testy)
    print("komunikatow wielowyrazowych w %s: %d"
          % (PROGRAM.replace(os.sep, "/"), len(wiadomosci)))
    print("igiel roznych w %s: %d (w %d wywolaniach %s z literalem)"
          % (TESTS.replace(os.sep, "/"), len(igielki),
             sum(len(v) for v in igielki.values()), ASSERTION))
    print()
    for igla in sorted(trafienia, key=lambda i: (-trafienia[i], i)):
        ile = trafienia[igla]
        wyrok = ("ZGLOSZONA" if igla in zgloszenia(program, testy)
                 else "usprawiedliwiona" if ile > 1
                 else "bez dopasowania" if ile == 0 else "swoista")
        print("  %-17s %2d  %-40r  test l. %s"
              % (wyrok, ile, igla, igly(testy)[igla]))
    print()
    print("  swoistych (dokladnie 1 komunikat): %d"
          % len([1 for ile in trafienia.values() if ile == 1]))
    print("  niejednoznacznych (>1):            %d"
          % len([1 for ile in trafienia.values() if ile > 1]))
    print("    z tego usprawiedliwionych:       %d (zapadka %d)"
          % (len(JUSTIFICATIONS), MAX_JUSTIFIED_NEEDLES))
    print("    z tego ZGLOSZONYCH:              %d" % len(zgloszenia(program, testy)))
    print("  bez ani jednego dopasowania:       %d (zapadka %d)"
          % (len(bez_dopasowania(program, testy)), MAX_UNMATCHED_NEEDLES))
    for igla in zgloszenia(program, testy):
        print("    ZGLOSZONA: %r w %d komunikatach" % (igla, trafienia[igla]))
    return 0


if __name__ == "__main__":
    if "--inwentarz" in sys.argv:
        raise SystemExit(main())
    import test_all

    raise SystemExit(test_all.main(__file__))

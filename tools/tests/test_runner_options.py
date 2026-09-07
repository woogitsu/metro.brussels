#!/usr/bin/env python3
"""Tabela znanych opcji `Sim.Runner` zgadza sie z tym, co polecenia naprawde czytaja.

**Skad ta bramka.** 6.D15 (#301) uruchomilo komende z pola „Weryfikacja" pozycji 6.A6:
`line ... --coast-from-m X`. Opcji `--coast-from-m` nie ma nigdzie w `src/`, `X` nie
jest liczba — a proces konczyl sie **kodem 0**. Dwa przejazdy, z ta opcja i bez niej,
daly pliki identyczne co do bajtu. 6.A11 dopisala odmowe; ta bramka pilnuje, zeby
odmowa nie rozjechala sie z kodem.

**Dlaczego bramka po stronie Pythona.** Tabela `KnownOptions` w `Program.cs` jest recznie
wypisana i to jest jej zaleta: komunikat odmowy ma wymieniac opcje TEGO polecenia,
a nie wszystkie, jakie runner zna. Recznie wypisana tabela ma jednak dokladnie jedna
wade — starzeje sie po cichu. Opcja dopisana do polecenia bez dopisania jej tutaj
przechodzilaby wszystkie testy C#: kod czyta ja przez `Option`, a odmowa nigdy nie
dochodzi do glosu, bo nikt tej opcji nie poda w tescie.

Ten modul czyta wiec `Program.cs` jako TEKST i wyprowadza zbior nazw z wywolan
`Option`, `RequiredNumber`, `OptionalNumber` i `Array.IndexOf` w ciele kazdego
polecenia — po czym porownuje go z tabela. Dwa niezalezne odczyty tego samego pliku;
rozjazd jednego z nich zapala bramke.

**Czego ta bramka NIE robi.** Nie uruchamia `dotnet` i nie moze go potrzebowac: zestaw
narzedzi chodzi tam, gdzie `doctor.sh` przepuszcza brak SDK. Nie sprawdza, czy opcja
robi to, co obiecuje jej nazwa — to jest praca testow C#.
"""
import os
import re
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROGRAM = os.path.join(ROOT, "src", "Sim.Runner", "Program.cs")

#: Nazwa metody C# obslugujacej polecenie -> nazwa polecenia w wierszu polecen.
#: Bierze sie z rozdzielacza `args[0] switch` i jest tu wypisana, bo rozdzielacz
#: mapuje jedno na drugie i tego odwzorowania nie da sie wyprowadzic z samej nazwy
#: metody (`line` -> `LineCommand`, `service-day` -> `ServiceDayCommand`).
HANDLERS = {
    "Drive": "drive",
    "Replay": "replay",
    "Compare": "compare",
    "Axis": "axis",
    "Parity": "parity",
    "Braking": "braking",
    "LineCommand": "line",
    "Budget": "budget",
    "ServiceDayCommand": "service-day",
}


def _source():
    with open(PROGRAM, encoding="utf-8") as handle:
        return handle.read()


def dispatcher_commands(source):
    """Nazwy polecen wprost z rozdzielacza `args[0] switch` w `Main`."""
    at = source.index("return args[0] switch")
    end = source.index("_ =>", at)
    return set(re.findall(r'"([a-z-]+)"\s*=>', source[at:end]))


def declared_table(source):
    """`KnownOptions` z `Program.cs` -> {polecenie: (wartosciowe, flagi)}."""
    at = source.index("KnownOptions =")
    # +1, zeby ostatni wpis mial swoj konczacy znak nowej linii: bez tego wyrazenie
    # nizej nie dopasowuje wpisu stojacego tuz przed klamra zamykajaca slownik.
    end = source.index("\n        };", at)
    body = source[at:end + 1]
    table = {}
    for match in re.finditer(r'\["([a-z-]+)"\]\s*=\s*\((.*?)\),\n', body, re.S):
        command, pair = match.group(1), match.group(2)
        halves = re.findall(r'new\[\]\s*\{(.*?)\}|Array\.Empty<string>\(\)', pair, re.S)
        parsed = []
        for half in halves:
            parsed.append(set(re.findall(r'"(--[a-z0-9-]+)"', half)))
        while len(parsed) < 2:
            parsed.append(set())
        table[command] = (parsed[0], parsed[1])
    return table


def read_by_code(source):
    """Nazwy opcji, ktore CIALO kazdego polecenia naprawde czyta."""
    positions = []
    for method in HANDLERS:
        match = re.search(r"\n    private static int " + method + r"\(", source)
        if match:
            positions.append((match.start(), method))
    positions.sort()
    found = {}
    for index, (start, method) in enumerate(positions):
        end = positions[index + 1][0] if index + 1 < len(positions) else len(source)
        body = source[start:end]
        values = set(re.findall(r'Option\(args,\s*"(--[a-z0-9-]+)"', body))
        values |= set(re.findall(
            r'(?:Required|Optional)Number\(args,\s*"(--[a-z0-9-]+)"', body))
        flags = set(re.findall(r'Array\.IndexOf\(args,\s*"(--[a-z0-9-]+)"', body))
        found[HANDLERS[method]] = (values, flags)
    return found


def test_the_table_covers_every_command_the_dispatcher_knows():
    source = _source()
    assert dispatcher_commands(source) == set(declared_table(source)), (
        "rozdzielacz i tabela znanych opcji wymieniaja rozne polecenia: "
        f"{sorted(dispatcher_commands(source))} vs {sorted(declared_table(source))}")


def test_every_option_the_code_reads_is_in_the_table():
    source = _source()
    table = declared_table(source)
    for command, (values, flags) in read_by_code(source).items():
        declared_values, declared_flags = table[command]
        assert values <= declared_values, (
            f"polecenie {command} czyta opcje spoza tabeli: "
            f"{sorted(values - declared_values)} — dopisz je do KnownOptions, "
            "inaczej odmowa odrzuci opcje, ktora dziala")
        assert flags <= declared_flags, (
            f"polecenie {command} czyta flagi spoza tabeli: "
            f"{sorted(flags - declared_flags)}")


def test_the_table_does_not_declare_options_nobody_reads():
    """Drugi kierunek. Nazwa w tabeli, ktorej kod nie czyta, jest gorsza niz jej brak:
    odmowa przepuszcza taka opcje, a polecenie i tak jej nie uzyje — czyli literowka
    znowu przechodzi w milczeniu."""
    source = _source()
    read = read_by_code(source)
    for command, (values, flags) in declared_table(source).items():
        code_values, code_flags = read[command]
        assert values <= code_values, (
            f"tabela deklaruje dla {command} opcje, ktorych kod nie czyta: "
            f"{sorted(values - code_values)}")
        assert flags <= code_flags, (
            f"tabela deklaruje dla {command} flagi, ktorych kod nie czyta: "
            f"{sorted(flags - code_flags)}")


def test_the_refusal_is_actually_wired_into_main():
    """Tabela bez wywolania jest dekoracja. Sprawdzane jest jedno: `Main` wola
    odmowe PRZED rozdzielaczem, bo po nim polecenie zdazyloby juz przeczytac
    argumenty i wykonac prace."""
    source = _source()
    call = source.index("RejectUnknownOptions(args[0], args);")
    switch = source.index("return args[0] switch")
    assert call < switch, "odmowa wolana po rozdzielaczu — polecenie zdazy zadzialac"


def test_the_refusal_skips_positional_arguments():
    """`compare` bierze dwie sciezki pozycyjnie. Odmowa zbudowana na „wszystko, czego
    nie znam" wywrocilaby to polecenie w calosci, wiec sprawdzenie ogranicza sie do
    czlonow zaczynajacych sie od minusa — i ten warunek ma stac w kodzie.

    **Test przepisany, a nie dopisany obok (6.A15.)** Do tej pozycji zadal literalnie
    `StartsWith("--"`, bo odmowa z 6.A11 patrzyla wylacznie na dwa minusy. 6.A11 SAMA
    wypisala te dziure: `-zmyslona 7` konczylo sie kodem 0. Warunek jest teraz na
    JEDNYM minusie, wiec literalna asercja przestala opisywac kod — a **intencja jest
    ta sama i to ona jest sprawdzana**: sciezki polecenia `compare` nie zaczynaja sie
    od minusa, wiec nadal przechodza nietknięte.
    """
    source = _source()
    at = source.index("private static void RejectUnknownOptions")
    body = source[at:source.index("\n    private static int Unknown", at)]
    assert 'StartsWith("-", StringComparison.Ordinal)' in body, (
        "odmowa nie odsiewa argumentow pozycyjnych")
    assert 'token == "-"' in body, (
        "goly minus jest konwencja standardowego wejscia, nie literowka: odmowa nie ma "
        "prawa go zglaszac")
    assert "known.Flags" in body and "known.Values" in body, (
        "odmowa nie rozroznia flagi od opcji z wartoscia — flaga zjadlaby nastepny czlon")


def _kod_bez_komentarzy(source):
    """`Program.cs` bez wierszy komentarza — wzmianka w komentarzu nie jest komunikatem.

    Bez tego bramka nizej zapalalaby sie na akapicie, ktory WYJASNIA odrzucona postac,
    czyli na poprawnym tekscie. Bramka zapalajaca sie na poprawnym tekscie zostaje
    wylaczona, nie naprawiona (nauczka 6.D27 i 6.D30).
    """
    return "\n".join(
        line for line in source.splitlines()
        if not line.strip().startswith("//") and not line.strip().startswith("///"))


def test_the_refusal_splits_a_token_on_the_equals_sign():
    """Postac `--opcja=wartosc` ma dostac komunikat o POSTACI, nie o nieznanej opcji.

    Sedno 6.A22: `--limit-kmh=72` konczylo sie zdaniem „nie zna opcji --limit-kmh=72",
    ktore jest sprzeczne z tabela — `--limit-kmh` w niej stoi. Wartosc odmowy z 6.A11
    lezy w tym, ze czytajacy jej wierzy; komunikat mowiacy nieprawde o zawartosci
    tabeli uczy czytac go z zastrzezeniem i wtedy przestaje dzialac takze tam, gdzie
    mial racje.
    """
    source = _source()
    at = source.index("private static void RejectUnknownOptions")
    body = source[at:source.index("\n    /// <summary>\n    /// Tresc odmowy", at)]
    assert "IndexOf('=', StringComparison.Ordinal)" in body, (
        "odmowa nie rozbiera czlonu na przedrostek i wartosc")
    assert "nie przyjmuje postaci" in body, (
        "brak komunikatu nazywajacego POSTAC")
    assert body.count("nie przyjmuje postaci") == 2, (
        "komunikat o postaci ma dwie wersje — dla opcji z wartoscia i dla FLAGI, "
        "ktora wartosci nie bierze; rada podana fladze musi byc inna, bo `--atp 1` "
        "zostawiloby `1` czlonem pozycyjnym, ktorego odmowa nie widzi")
    assert "known.Flags, prefix" in body, (
        "odmowa nie sprawdza, czy przedrostek jest FLAGA")


def test_there_is_one_writer_of_the_unknown_option_message():
    """Tresc odmowy nieznanej opcji ma jednego pisarza, choc wolaja ja dwa miejsca.

    Od 6.A22 odmowa wychodzi z dwoch miejsc — czlon bez rownosci i przedrostek czlonu
    z rownoscia. Dwoch pisarzy tej samej tresci rozjezdza sie przy pierwszej poprawce;
    ta sama zasada, ktora przy 6.A20 wydzielila `Provenance`, a przy 6.A14
    `NotANumber`.
    """
    source = _source()
    kod = _kod_bez_komentarzy(source)
    assert kod.count("private static string Nieznana(") == 1, (
        "pomocnik tresci odmowy ma byc zadeklarowany dokladnie raz")
    assert kod.count("nie zna opcji") == 1, (
        "tresc odmowy nieznanej opcji stoi w %d miejscach zamiast w jednym"
        % kod.count("nie zna opcji"))
    assert source.count("Nieznana(command,") == 2, (
        "pomocnik ma byc wolany z DWOCH miejsc — czlonu bez rownosci i przedrostka "
        "czlonu z rownoscia; jedno wywolanie znaczy, ze jedna z drog zniknela")


def test_no_message_writes_a_known_option_in_the_equals_form():
    """Zaden komunikat runnera nie radzi postaci, ktora runner sam odrzuca.

    Znalezione WLASNYM sondowaniem 6.A22, nie wpisem: `replay --limit-kmh={ceiling}
    nie jest dodatnia predkoscia` bylo pisane z rownoscia, czyli w postaci, ktora
    od tej pozycji konczy sie odmowa. Komunikat radzacy komende niedzialajaca jest
    ta sama usterka co ta pozycja, przesunieta o jedno miejsce.
    """
    source = _source()
    kod = _kod_bez_komentarzy(source)
    table = declared_table(source)
    winne = []
    for command, (values, flags) in table.items():
        for option in sorted(values | flags):
            if option + "=" in kod:
                winne.append((command, option))
    assert winne == [], (
        "komunikat albo kod pisze znana opcje w postaci z rownoscia, ktorej runner "
        "nie przyjmuje: " + repr(sorted(set(winne))))

def test_the_refusal_catches_a_repeated_value_option_but_not_a_repeated_flag():
    """Powtorzona opcja z wartoscia jest odmowa; powtorzona FLAGA nie (6.A23).

    `Option` bierze PIERWSZE wystapienie, wiec do 6.A23 druga wartosc znikala bez
    slowa — a od 6.A20 nastawy ida rowniez do plikow z `--out`, czyli ta sama luka
    byla w artefakcie, ktory przezywa proces. Flaga to inna sprawa i jest to pole
    „Poza zakresem" tamtej pozycji: `--atp --atp` znaczy to samo, co `--atp`, wiec
    nie ginie zadna wartosc. Bramka pilnuje OBU polowek, bo przesuniecie tej granicy
    ma byc widoczne, a nie ciche.
    """
    source = _source()
    at = source.index("private static void RejectUnknownOptions")
    body = source[at:source.index("\n    private static int Unknown", at)]
    assert "new HashSet<string>(StringComparer.Ordinal)" in body, (
        "odmowa nie pamieta, ktore opcje juz byly w tym wierszu polecen")
    assert body.count("seen.Add(token)") == 1, (
        "zbior widzianych opcji ma byc dotykany dokladnie w JEDNYM miejscu — "
        "w galezi opcji z wartoscia, nie w galezi flagi")
    galaz_flagi = body[body.index("Array.IndexOf(known.Flags, token)"):]
    assert "seen" not in galaz_flagi, (
        "galaz flagi dotyka zbioru widzianych opcji — powtorzona flaga zaczelaby "
        "byc odmowa, a to jest poza zakresem 6.A23")
    assert "wiecej niz raz".replace("wiecej", "więcej").replace("niz", "niż") in body, (
        "brak komunikatu o powtorzeniu")


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.

# --- ile czlonow pozycyjnych bierze polecenie (6.A25) ---------------------------


def declared_positional(source):
    """Trzecie pole `KnownOptions` -> {polecenie: liczba czlonow pozycyjnych}.

    Osobny czytnik od `declared_table`, i to jest zamierzone: tamten wyprowadza ZBIORY
    nazw i jego wyrazenie regularne szuka `new[] {...}` albo `Array.Empty<string>()`,
    wiec liczby by nie zobaczylo. Doklejanie trzeciego pola do tamtego czytnika
    zmusiloby go do zwracania trojki wszedzie, gdzie dzis zwraca pare — a wtedy
    poprawka w jednym z dwoch pomiarow psulaby drugi.
    """
    at = source.index("KnownOptions =")
    end = source.index("\n        };", at)
    body = source[at:end + 1]
    found = {}
    for match in re.finditer(r'\["([a-z-]+)"\]\s*=\s*\((.*?)\),\n', body, re.S):
        command, krotka = match.group(1), match.group(2)
        ogon = re.search(r",\s*(\d+)\s*$", krotka)
        assert ogon, (
            f"wpis {command!r} w KnownOptions nie ma liczby czlonow pozycyjnych "
            "jako trzeciego pola: " + krotka[-60:])
        found[command] = int(ogon.group(1))
    return found


def positional_by_code(source):
    """Ile czlonow pozycyjnych CIALO kazdego polecenia naprawde czyta.

    Miara: najwyzszy indeks `args[N]` dla N >= 1 w ciele metody. `args[0]` to nazwa
    polecenia, a nie czlon pozycyjny, wiec sie nie liczy. Brak jakiegokolwiek odczytu
    znaczy zero.

    Komentarze zdjete: `Program.cs` MOWI o `args[1]` i `args[2]` w prozie przy
    `RejectUnknownOptions` i w dokumentacji `Command`, a bramka zapalajaca sie na
    tekscie, ktory tylko wyjasnia mechanizm, zostaje wylaczona, nie naprawiona
    (nauczka 6.D27 i 6.D30).
    """
    kod = _kod_bez_komentarzy(source)
    positions = []
    for method in HANDLERS:
        match = re.search(r"\n    private static int " + method + r"\(", kod)
        if match:
            positions.append((match.start(), method))
    positions.sort()
    found = {}
    for index, (start, method) in enumerate(positions):
        end = positions[index + 1][0] if index + 1 < len(positions) else len(kod)
        indeksy = [int(n) for n in re.findall(r"\bargs\[(\d+)\]", kod[start:end])]
        found[HANDLERS[method]] = max([n for n in indeksy if n >= 1], default=0)
    return found


def test_the_positional_count_matches_what_each_command_reads():
    """Liczba w tabeli ma byc POMIAREM z kodu, nie czyjas pamiecia.

    Sedno 6.A25: do 07.09.2026 czlon pozycyjny nie byl liczony wcale, wiec
    `budget ... --atp 1` konczylo sie kodem 0 z wypisem nieodroznialnym od
    `budget ... --atp` — wartosc po fladze jest czlonem pozycyjnym. Odmowa stoi teraz
    na liczbie przy poleceniu, a liczba recznie wypisana starzeje sie po cichu
    dokladnie tak samo, jak starzala sie tabela nazw (powod tego modulu).
    """
    source = _source()
    assert declared_positional(source) == positional_by_code(source), (
        "tabela i kod nie zgadzaja sie co do liczby czlonow pozycyjnych: "
        f"tabela {declared_positional(source)} vs kod {positional_by_code(source)}")


def test_only_compare_takes_positional_members_and_it_takes_two():
    """Pomiar, o ktory prosilo pole „Wyjscie" 6.A25 — wprost i jedna liczba.

    Pozycja zadala rozstrzygniecia POMIAREM, ile polecen bierze dzis choc jeden czlon
    pozycyjny, bo od tego zalezalo, czy wystarcza jedna liczba przy poleceniu, czy
    trzeba nowego rozbioru. Wyszlo: JEDNO polecenie, dwa czlony. Dlatego jedna liczba
    wystarcza — i ten test przybija tamto rozstrzygniecie, zeby trzecie polecenie
    z czlonem pozycyjnym nie doszlo w milczeniu.
    """
    source = _source()
    z_czlonami = {k: v for k, v in positional_by_code(source).items() if v > 0}
    assert z_czlonami == {"compare": 2}, (
        "czlony pozycyjne czyta dzis inny zestaw polecen niz przy 6.A25 "
        f"({z_czlonami}) — sprawdz, czy jedna liczba przy poleceniu nadal wystarcza")


def test_the_refusal_counts_positional_members_against_the_table():
    """Odmowa ma czytac `known.Positional`, a nie mieć wlasnej stalej.

    Kontrola przyrzadu, nie kodu: liczba w tabeli bez odczytu w odmowie byla by
    dokumentacja, a `test_the_positional_count_matches_what_each_command_reads`
    wyzej nadal by przechodzil. Bramka porownujaca dwa martwe pola zgadza sie
    zawsze — to usterka 6.D30.
    """
    kod = _kod_bez_komentarzy(_source())
    at = kod.index("private static void RejectUnknownOptions")
    body = kod[at:kod.index("private static string Nieznana", at)]
    assert "known.Positional" in body, (
        "odmowa nie czyta liczby czlonow pozycyjnych z tabeli")
    assert "człon pozycyjny" in body, (
        "odmowa nie nazywa czlonu pozycyjnego po imieniu")


# --- pomiar, na ktorym stoi decyzja 6.A22, jest pilnowany (6.A26) ----------------

#: Postac `--opcja=wartosc`. Sam przedrostek z rownoscia, bez wartosci — bo `--out=`
#: z pusta wartoscia jest ta sama postacia i ma sie liczyc.
POSTAC_Z_ROWNOSCIA = re.compile(r"--[a-z0-9][a-z0-9-]*=")

#: Komenda wolajaca `Sim.Runner`. Dwie postaci, obie ZMIERZONE w drzewie
#: (`git grep`): `dotnet run --project src/Sim.Runner` (89 trafien) i wolanie DLL
#: wprost (4 trafienia, w tym trzy sciezki `bin/Release/...`).
WOLANIE_RUNNERA = re.compile(
    r"dotnet run\s+--project\s+src/Sim\.Runner|MetroBxl\.Sim\.Runner\.dll")

#: Komenda wolajaca SCENE Godota. Scena postaci z rownoscia WYMAGA — taki jest jej
#: `RunPlan`, przybity testami w `tests/Game.Tests` — wiec bramka, ktora by ja
#: zglaszala, zostalaby wylaczona w tym samym tygodniu. Dlatego scena jest wykrywana
#: PIERWSZA i wygrywa z wykryciem runnera: wiersz niosacy oba markery jest proza
#: o dwoch polowach projektu, nie komenda runnera.
WOLANIE_SCENY = re.compile(r"GODOT_BIN|--path\s+src/Game")

#: Rozszerzenia plikow, ktore moga niesc komende. Binarne i zasoby odsiane, zeby
#: bramka nie zalezala od tego, co `git ls-files` wypisze po dodaniu nowego formatu.
ROZSZERZENIA = (".yml", ".yaml", ".md", ".sh", ".py", ".cs", ".txt", ".json")

#: Komendy runnera w postaci z rownoscia, ktore MAJA tam stac, z powodem przy kazdej.
#: Klucz to (sciezka, fragment komendy) — nie numer wiersza, bo numer przesuwa kazdy
#: commit dopisujacy cokolwiek wyzej w pliku, a wtedy bramka zapalalaby sie na tekscie
#: poprawnym i zostalaby wylaczona (nauczka 6.D27).
USPRAWIEDLIWIENIA = {
    ("docs/TASKS.md", "line --axis data/track/L1_A.json"):
        "pole `Weryfikacja` pozycji 6.A22 — komenda, ktorej CALYM sensem jest "
        "pokazanie odmowy dla postaci z rownoscia. Gdyby ja przepisac na dwa czlony, "
        "pozycja przestalaby weryfikowac to, co zrobila.",
}


def _sklej_kontynuacje(tekst):
    """Wiersze polaczone znakiem `\\` na koncu -> jeden wiersz logiczny.

    Bez tego klasyfikacja jest nieprawdziwa w te sama strone, w ktora klamie kazdy
    zly przyrzad tej sesji — w strone „wszystko w porzadku". Komenda CI lamana na
    trzy wiersze niesie `dotnet run --project src/Sim.Runner` w pierwszym, a
    `--limit-kmh=72` w drugim; liczone osobno, drugi wiersz nie ma zadnego markera
    i wpada do prozy.

    Zwraca listy `(numer pierwszego wiersza, tresc)`.
    """
    out, buf, start = [], "", None
    for numer, linia in enumerate(tekst.splitlines(), 1):
        if start is None:
            start = numer
        goly = linia.rstrip()
        if goly.endswith("\\"):
            buf += goly[:-1] + " "
            continue
        out.append((start, buf + goly))
        buf, start = "", None
    if buf:
        out.append((start or 1, buf))
    return out


def _pliki_repozytorium():
    wypis = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout
    return [p for p in wypis.split("\n") if p.endswith(ROZSZERZENIA)]


def klasyfikacja_rownosci():
    """Kazde wystapienie postaci `--opcja=` podzielone po WOLANYM programie.

    Zwraca `(liczby, komendy_runnera)`, gdzie `liczby` to
    `{"razem", "runner", "scena", "proza"}`, a `komendy_runnera` to lista
    `(sciezka, numer wiersza, tresc)`.
    """
    liczby = {"razem": 0, "runner": 0, "scena": 0, "proza": 0}
    komendy = []
    for sciezka in _pliki_repozytorium():
        pelna = os.path.join(ROOT, sciezka)
        try:
            with open(pelna, encoding="utf-8") as uchwyt:
                tekst = uchwyt.read()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        for numer, wiersz in _sklej_kontynuacje(tekst):
            ile = len(POSTAC_Z_ROWNOSCIA.findall(wiersz))
            if not ile:
                continue
            liczby["razem"] += ile
            if WOLANIE_SCENY.search(wiersz):
                liczby["scena"] += ile
            elif WOLANIE_RUNNERA.search(wiersz):
                liczby["runner"] += ile
                komendy.append((sciezka, numer, wiersz.strip()))
            else:
                liczby["proza"] += ile
    return liczby, komendy


#: Prog na LACZNA liczbe wystapien. Bez niego literowka we wzorcu daje zero komend
#: runnera i zielono — dokladnie ten sposob, w ktory bramka klamie w strone „wszystko
#: w porzadku"; kontrola KN-B to wykonala.
#:
#: Zmierzone 07.09.2026, trzy razy, kazdy raz na nazwanym drzewie:
#:   409 / 1 / 99 / 309   `main` przed 6.A25 i przed ta bramka
#:   419 / 1 / 99 / 319   ta galaz przed przestawieniem na `main` z 6.A25
#:   426 / 1 / 100 / 325  ta galaz po przestawieniu — stan do scalenia
#: Caly przyrost jest rozliczony po plikach: +1 w `docs/TASKS.md` (wiersze 6.A25
#: i 6.A26), +5 w `reports/pomiar-rownosci.md`, +11 w TYM pliku (klasyfikator i jego
#: kontrole, 4 -> 15). Bramka, ktora liczy takze siebie, ma to powiedziec wprost —
#: inaczej pierwszy commit dopisujacy do niej test wygladalby jak wzrost liczby
#: komend w repozytorium.
#:
#: Prog stoi nizej niz pomiar, bo proza rosnie i maleje razem z raportami; ma lapac
#: zejscie do zera, nie wahanie o kilkadziesiat.
MINIMUM_WYSTAPIEN_ROWNOSCI = 250


def test_no_runner_command_in_the_repository_uses_the_equals_form():
    """Pomiar, na ktorym stoi decyzja 6.A22, jest PILNOWANY, a nie zapisany raz.

    **To jest sprostowanie do wlasnego raportu.** §10 `reports/postac-z-rownosciem.md`
    napisal, ze gdyby komenda CI zaczela tej postaci uzywac wobec runnera, „bramka
    z §5 pokaze to jako FAIL, zamiast czekac na czyjes oko". Nieprawda: bramka z §5
    (`test_no_message_writes_a_known_option_in_the_equals_form`) czyta WYLACZNIE
    `src/Sim.Runner/Program.cs`. Komenda w `.github/workflows/*.yml` albo w `docs/`
    byla poza jej zasiegiem.

    6.A22 odrzucila postac `--opcja=wartosc` na podstawie pomiaru — decyzja jest dobra
    dokladnie tak dlugo, jak dlugo pomiar jest prawdziwy. Ta bramka mierzy go po
    kazdym commicie.
    """
    liczby, komendy = klasyfikacja_rownosci()
    nieuzasadnione = [
        (p, nr, w) for p, nr, w in komendy
        if not any(p == plik and fragment in w
                   for plik, fragment in USPRAWIEDLIWIENIA)
    ]
    assert nieuzasadnione == [], (
        "komenda `Sim.Runner` w postaci `--opcja=wartość`, ktorej runner od 6.A22 "
        "nie przyjmuje — konczy sie kodem 1:\n"
        + "\n".join(f"    {p}:{nr}  {w[:140]}" for p, nr, w in nieuzasadnione))


def test_the_equals_form_count_has_not_collapsed_to_nothing():
    """Prog na laczna liczbe — inaczej literowka we wzorcu daje zielono.

    Bramka wyzej jest zielona takze wtedy, gdy `POSTAC_Z_ROWNOSCIA` przestanie
    cokolwiek lapac: zero komend runnera to zero. Ten test odbiera jej te droge
    do falszywej zgody.
    """
    liczby, _ = klasyfikacja_rownosci()
    assert liczby["razem"] >= MINIMUM_WYSTAPIEN_ROWNOSCI, (
        f"postac z rownoscia wystepuje {liczby['razem']} razy przy progu "
        f"{MINIMUM_WYSTAPIEN_ROWNOSCI} — wzorzec albo lista plikow przestaly lapac "
        "to, co lapaly 07.09.2026 (426 wystapien na drzewie do scalenia)")
    assert liczby["scena"] > 0, (
        "ani jedna komenda SCENY nie uzywa postaci z rownoscia, a scena jej WYMAGA "
        "(`RunPlan`, 27 testow w tests/Game.Tests) — wykrywanie sceny jest zepsute, "
        f"a wtedy jej komendy poleca do kubelka runnera. Liczby: {liczby}")
    assert liczby["razem"] == liczby["runner"] + liczby["scena"] + liczby["proza"], (
        f"kubelki nie sumuja sie do calosci: {liczby}")


def test_the_gate_catches_a_runner_command_written_in_the_equals_form():
    """Kontrola DODATNIA na wstrzykniętym wejsciu, z plikiem i numerem wiersza.

    Bramka odmawiajaca zawsze i bramka nieodmawiajaca nigdy wygladaja identycznie na
    czystym drzewie. Ten test sprawdza, ze klasyfikator NAPRAWDE lapie komende
    runnera — i ze lapie ja takze wtedy, gdy jest zlamana na trzy wiersze znakiem
    `\\`, bo tak wyglada kazda komenda w `docs/` i w workflowach.
    """
    komenda = ("dotnet run --project src/Sim.Runner -c Release -- line \\\n"
               "    --axis data/track/L1_A.json \\\n"
               "    --limit-kmh=72 --exchange-s 20\n")
    wiersze = _sklej_kontynuacje("pierwszy wiersz bez niczego\n" + komenda)
    trafione = [(nr, w) for nr, w in wiersze
                if POSTAC_Z_ROWNOSCIA.search(w) and WOLANIE_RUNNERA.search(w)
                and not WOLANIE_SCENY.search(w)]
    assert len(trafione) == 1, (
        "klasyfikator nie widzi wstrzykniętej komendy runnera jako jednego wiersza "
        f"logicznego: {wiersze}")
    nr, _ = trafione[0]
    assert nr == 2, (
        "numer wiersza ma wskazywac PIERWSZY wiersz komendy, nie ten z rownoscia — "
        f"dostal {nr}")

    # Ta sama komenda BEZ rownosci nie jest zgloszeniem.
    czysta = komenda.replace("--limit-kmh=72", "--limit-kmh 72")
    assert not [w for _, w in _sklej_kontynuacje(czysta)
                if POSTAC_Z_ROWNOSCIA.search(w)], (
        "klasyfikator zglasza komende runnera bez postaci z rownoscia")


def test_no_scene_command_is_reported_as_a_runner_command():
    """Kontrola UJEMNA: ani jedna z komend sceny nie jest zglaszana.

    Scena postaci z rownoscia WYMAGA. Bramka lapiaca scene bylaby wylaczona w tym
    samym tygodniu, w ktorym powstala — i dlatego wykrycie sceny wygrywa z wykryciem
    runnera, takze dla wiersza niosacego oba markery.
    """
    _, komendy = klasyfikacja_rownosci()
    ze_scena = [(p, nr) for p, nr, w in komendy if WOLANIE_SCENY.search(w)]
    assert ze_scena == [], (
        "komenda sceny trafila do kubelka runnera: " + repr(ze_scena))

    wzor_sceny = ('"$GODOT_BIN" --headless --path src/Game -- --line '
                  '--limit-kmh=70 --calls=3')
    assert POSTAC_Z_ROWNOSCIA.search(wzor_sceny), "wzorzec kontrolny nie ma rownosci"
    assert WOLANIE_SCENY.search(wzor_sceny), "wykrywanie sceny nie widzi wzorca"


def test_a_line_naming_both_programs_counts_as_scene_not_runner():
    """Pierwszenstwo sceny nad runnerem — pilnowane NA WEJSCIU, nie w komentarzu.

    **Rzecz warta powiedzenia wprost, bo mowi, ile ten test jest wart.** Kontrola
    negatywna KN-D (przestawienie kolejnosci tak, ze runner sprawdzany jest pierwszy)
    zostawia zestaw ZIELONY: w dzisiejszym drzewie nie ma ani jednego wiersza, ktory
    niesie oba markery, wiec kolejnosc nie ma na czym zadzialac. Regula jest wiec
    zabezpieczeniem na przyszlosc, nie wnioskiem z pomiaru — a regula opisana samym
    komentarzem nie jest pilnowana wcale.

    Wiersz niosacy oba markery jest proza o dwoch polowach projektu (albo krokiem CI,
    ktory wola jedno i drugie), a nie komenda runnera. Zaklasyfikowanie go do runnera
    daloby FAIL na tekscie poprawnym — a bramka zapalajaca sie na poprawnym tekscie
    zostaje wylaczona, nie naprawiona (6.D27, 6.D30).
    """
    oba = ('scena `"$GODOT_BIN" --headless --path src/Game -- --limit-kmh=70` '
           'wymaga rownosci, a `dotnet run --project src/Sim.Runner -- line '
           '--limit-kmh 70` jej nie przyjmuje')
    assert WOLANIE_SCENY.search(oba), "wykrywanie sceny nie widzi tego wiersza"
    assert WOLANIE_RUNNERA.search(oba), "wykrywanie runnera nie widzi tego wiersza"
    assert POSTAC_Z_ROWNOSCIA.search(oba), "wiersz kontrolny nie ma rownosci"

    # Ta sama gałąź decyzyjna, co w `klasyfikacja_rownosci`, na jednym wierszu:
    # scena sprawdzana PIERWSZA, wiec kubelkiem jest scena.
    kubelek = ("scena" if WOLANIE_SCENY.search(oba)
               else "runner" if WOLANIE_RUNNERA.search(oba) else "proza")
    assert kubelek == "scena", (
        "wiersz niosacy oba markery poszedl do kubelka " + kubelek
        + " — pierwszenstwo sceny jest zdjete")


def test_every_justification_still_describes_a_command_that_exists():
    """Usprawiedliwienie nie moze przezyc komendy, ktora opisuje.

    Wpis, ktorego nie ma czego usprawiedliwiac, jest dziura w bramce ubrana w proze —
    ta sama zasada, ktora 6.D29 postawilo dla listy wyjatkow raportow i 6.B34 dla
    usprawiedliwien martwych stalych.
    """
    _, komendy = klasyfikacja_rownosci()
    martwe = [klucz for klucz in USPRAWIEDLIWIENIA
              if not any(p == klucz[0] and klucz[1] in w for p, _, w in komendy)]
    assert martwe == [], (
        "usprawiedliwienie bez komendy, ktora opisuje: " + repr(martwe))
    puste = [k for k, v in USPRAWIEDLIWIENIA.items() if len(v.strip()) < 40]
    assert puste == [], (
        "usprawiedliwienie bez powodu podanego zdaniem: " + repr(puste))


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

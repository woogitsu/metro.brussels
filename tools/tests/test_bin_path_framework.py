#!/usr/bin/env python3
"""Ścieżka `bin/…/netX.Y/` cytowana w `reports/` i w `docs/` a `TargetFramework`.

**Po co ta bramka istnieje.** `tools/tests/test_report_hygiene.py` pilnuje, czy każda
ścieżka WYMIENIONA w raporcie rozwiązuje się w drzewie. Ścieżka do katalogu, który
powstaje dopiero przy budowaniu, nie rozwiązuje się w drzewie NIGDY — ani ta poprawna,
ani ta z martwym `netX.Y` — więc tamta bramka jej nie ogląda i oglądać nie może.
Nikt jej nie sprawdzał. Zmierzone 07.09.2026 przy 6.A26: `reports/T-311-braking.md:257`
i `reports/T-400-first-run.md:235` niosą `net8.0`, a `<TargetFramework>` we wszystkich
pięciu plikach projektu to `net10.0` od migracji z 02.09.2026 (`ba93903`).

**Dlaczego to nie jest kosmetyka.** Pole „Weryfikacja" pozycji z `docs/TASKS.md` jest
obietnicą, że podaną komendę da się wpisać do terminala — tak samo jak w
`tools/tests/backlog_commands.py`. Komenda `dotnet src/Sim.Runner/bin/Release/net8.0/…`
kończy się dziś `Could not execute because the specified command or file was not found`,
i to jest awaria, której nie widać w żadnym teście: katalog `net8.0` nie istnieje, bo
`dotnet build` produkuje `net10.0`. Ta bramka wyprowadza `netX.Y` Z PLIKU PROJEKTU
i porównuje z każdą cytowaną ścieżką `bin/`.

**Trzy szczeble, bo trzy różne rzeczy.**

1. Ścieżka niezgodna w polu „Weryfikacja" `docs/TASKS.md` — **twardy błąd, bez
   usprawiedliwienia**. To jest komenda, którą ktoś wpisze.
2. Ścieżka niezgodna w wierszu, który JEST komendą (pierwszy token to wołany program) —
   **twardy błąd, bez usprawiedliwienia**, gdziekolwiek stoi. Tu wyrok jest ten sam
   nawet w prozie: komenda w raporcie jest przepisem, nie pomiarem.
3. Ścieżka niezgodna w prozie albo w CYTACIE WYJŚCIA `dotnet build` — pomiar z datą.
   Tych się nie przelicza (`CLAUDE.md` §4, `docs/04-conventions.md`); dostają
   usprawiedliwienie z powodem podanym zdaniem i adnotację w samym raporcie.

**Znalezisko o pomiarze z 6.A26, wpisane tu wprost.** Tamten pomiar nazwał dwa
wystąpienia „komendami"; nie są nimi. `reports/T-311-braking.md:257` i
`reports/T-400-first-run.md:235` to wiersze postaci `Sim.Runner -> …dll` z CYTOWANEGO
WYJŚCIA `dotnet build`, a nie wołania. Jedyna prawdziwa komenda z ścieżką `bin/`
w całym drzewie stoi w `reports/linecore-budget.md:91` i jest ZGODNA (`net10.0`).
Szczebel 2 jest więc dziś pusty — i dokładnie dlatego ma kontrolę dodatnią na wejściu
wstrzykniętym, a nie „przechodzi, bo nic nie ma".

**CZEGO TA BRAMKA NIE ROBI, ŚWIADOMIE.** Nie uruchamia komend i nie sprawdza, czy
działają — to jest bramka na spójność ścieżki z plikiem projektu, nie na wykonanie
(pole „Poza zakresem" pozycji 6.A31). Nie ogląda też wystąpień `netX.Y` BEZ segmentu
`bin/`: wiersz `… - MetroBxl.Sim.Tests.dll (net8.0)` jest cytatem wyjścia `dotnet test`
o tym, na czym testy WTEDY chodziły, a nie ścieżką do katalogu; takich wierszy jest
w `reports/` kilkanaście i zgłaszanie ich zamieniłoby bramkę w szum. Granicę pilnuje
`test_a_framework_without_a_bin_segment_is_out_of_scope`.

**KONTROLE — każda WYKONANA, wypisane w `reports/ramka-w-sciezce.md`:**

  KD (dodatnia)  ścieżka `net8.0` wstrzyknięta w prawdziwy plik jest zgłoszona
                 z plikiem i numerem wiersza, na obu twardych szczeblach osobno.
  KU (ujemna)    ani jedna ze ścieżek `net10.0` w drzewie nie jest zgłoszona —
                 bramka łapiąca ścieżkę POPRAWNĄ zostałaby wyłączona w tym samym
                 tygodniu (6.D27). Pilnuje tego `test_a_matching_directory_is_never_reported`.
  KP (przyrząd)  `TargetFramework` podmieniony na `net8.0` PRZENOSI zbiór zgłoszeń
                 na ścieżki `net10.0` — bez tego „bramka" byłaby stałą wpisaną
                 z pamięci. Pilnuje tego `test_the_verdict_follows_the_project_file`.
  KW (wzorzec)   wzorzec zepsuty daje ZERO dopasowań i wszystko zielone — to jest
                 najczęstszy sposób, w jaki bramka kłamie w stronę „w porządku".
                 Pilnuje tego próg `MIN_PATHS_IN_TREE`.
"""

import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Plik projektu, z którego bramka WYPROWADZA `netX.Y`. Runner, bo to jego katalog
#: `bin/` cytują komendy w raportach; `test_dotnet_version.py` osobno pilnuje, że
#: wszystkie pięć plików projektu mają jedną wartość, więc wybór jednego nie jest
#: tu założeniem na wiarę.
PROJECT = os.path.join("src", "Sim.Runner", "Sim.Runner.csproj")

#: Katalogi przeglądane. Pole „Wyjście" pozycji 6.A31 mówi `reports/` i `docs/`.
SCANNED = ("reports", "docs")

#: Ścieżka z segmentem `bin/`, po którym gdzieś dalej stoi `netX.Y`, po którym stoi
#: kolejny segment. Wymaganie separatora PO wersji odcina wiersze postaci
#: `MetroBxl.Sim.Tests.dll (net8.0)` — te są cytatem wyjścia `dotnet test`, nie ścieżką.
PATH = re.compile(
    r"(?P<prefix>[A-Za-z0-9._+/-]*bin/(?:[A-Za-z0-9._+-]+/)*?net(?P<version>\d+\.\d+))(?=/)")

#: Nagłówek pola, którego treść jest obietnicą wykonalnej komendy — w brzmieniu
#: z `docs/TASK-TEMPLATE.md`, tak samo jak w `backlog_commands.FIELD`.
VERIFICATION_MARKER = "- **Weryfikacja:**"

#: Programy, których obecność na początku wiersza czyni z niego WOŁANIE, a nie cytat
#: wyjścia. Lista jest zamknięta i celowo krótka: rozpoznanie ma być składniowe
#: i głupie, bo wyrok „czy to komenda" nie może zależeć od domysłu.
PROGRAMS = ("dotnet", "bash", "sh", "python3", "python", "git", "blender", "godot", "make")

#: Usprawiedliwienia szczebla 3: pomiar z datą, którego się NIE przelicza. Klucz to
#: **(ścieżka pliku, przedrostek ścieżki `bin/`)**, nie numer wiersza — numer przesuwa
#: każdy commit dopisujący cokolwiek wyżej, a bramka zapalająca się na tekście
#: poprawnym zostaje wyłączona, nie naprawiona (6.D27, 6.A26).
JUSTIFICATIONS = {
    ("reports/T-310-physics.md", "src/Sim/bin/Release/net8.0"):
        "Cytat wyjścia `dotnet build` z 31.08.2026, dnia pomiaru T-310; wtedy wszystkie "
        "projekty celowały w net8.0 i ten wiersz był prawdziwy. Adnotacji nie dostaje, "
        "bo plik nie stoi w polu „Wejście\" pozycji 6.A31 (CLAUDE.md §4.10).",
    ("reports/T-310-physics.md", "tests/Sim.Tests/bin/Release/net8.0"):
        "Ten sam cytat wyjścia `dotnet build` z 31.08.2026, wiersz projektu testowego. "
        "Powód identyczny jak dla wiersza rdzenia wyżej.",
    ("reports/T-311-braking.md", "src/Sim/bin/Release/net8.0"):
        "Cytat wyjścia `dotnet build` z dnia pomiaru T-311, §5.1. Raport ma adnotację "
        "dopisaną przy 6.A31; liczb i cytatu nie przeliczono, bo mają datę.",
    ("reports/T-311-braking.md", "src/Sim.Runner/bin/Release/net8.0"):
        "Wiersz runnera z tego samego cytatu `dotnet build`, §5.1 — to jedno z dwóch "
        "wystąpień, które 6.A26 nazwało „komendą\"; komendą nie jest. Raport ma adnotację.",
    ("reports/T-311-braking.md", "tests/Sim.Tests/bin/Release/net8.0"):
        "Wiersz projektu testowego z tego samego cytatu `dotnet build`, §5.1. Powód "
        "identyczny jak dla dwóch wierszy wyżej; raport ma adnotację.",
    ("reports/T-400-first-run.md", "src/Sim/bin/Release/net8.0"):
        "Cytat wyjścia `dotnet build` z dnia pomiaru T-400. Raport ma adnotację dopisaną "
        "przy 6.A31; cytatu nie przeliczono, bo jego wartością jest to, co wyszło wtedy.",
    ("reports/T-400-first-run.md", "src/Sim.Runner/bin/Release/net8.0"):
        "Wiersz runnera z tego samego cytatu `dotnet build` — drugie z dwóch wystąpień "
        "wskazanych przez 6.A26. Raport ma adnotację.",
    ("reports/T-400-first-run.md", "tests/Sim.Tests/bin/Release/net8.0"):
        "Wiersz projektu testowego z tego samego cytatu `dotnet build`. Powód identyczny "
        "jak dla dwóch wierszy wyżej; raport ma adnotację.",
    ("reports/pomiar-rownosci.md", "Sim.Runner/bin/Release/net8.0"):
        "§9 raportu 6.A26 CYTUJE dwie ścieżki net8.0 z T-311 i T-400 jako znalezisko "
        "zostawione nietknięte. Poprawienie ich tutaj skasowałoby zapis o tym, co "
        "znaleziono — a pozycja 6.A31 wzięła się właśnie z tego zapisu.",
    ("reports/ramka-w-sciezce.md", "src/Sim/bin/Release/net8.0"):
        "Raport tej pozycji CYTUJE wyjście własnej bramki, a bramka wypisuje ścieżki, "
        "które zgłasza. Bramka, która liczy także siebie, ma to powiedzieć wprost — "
        "zasada z 6.A26; alternatywą byłby raport bez wklejonego wyjścia.",
    ("reports/ramka-w-sciezce.md", "src/Sim.Runner/bin/Release/net8.0"):
        "Ta sama przyczyna: wiersz runnera w cytowanym wyjściu bramki oraz w cytatach "
        "kontroli dodatniej. Wyjścia weryfikacji nie wolno streszczać (CLAUDE.md §5).",
    ("reports/ramka-w-sciezce.md", "tests/Sim.Tests/bin/Release/net8.0"):
        "Ta sama przyczyna: wiersz projektu testowego w cytowanym wyjściu bramki. "
        "Trzy przedrostki, bo bramka zgłasza dziś trzy różne katalogi `bin/`.",
    ("reports/ramka-w-sciezce.md", "Sim.Runner/bin/Release/net8.0"):
        "Przedrostek w postaci skróconej, w jakiej cytuje go §9 raportu 6.A26 i wiersz "
        "6.A31 w `docs/TASKS.md`; raport 6.A31 przepisuje ten cytat, żeby pokazać, "
        "skąd pozycja się wzięła.",
    ("docs/TASKS.md", "Sim.Runner/bin/Release/net8.0"):
        "Wiersze 6.A26 i 6.A31 w tabeli fazy 6 oraz pole „Skąd\" bloku 6.A31 CYTUJĄ "
        "zmierzoną ścieżkę jako treść znaleziska. To jest opis usterki, nie komenda; "
        "podmiana na net10.0 skasowałaby zdanie o tym, co zmierzono 07.09.2026.",
}

#: Zapadka na listę wyżej. Bez niej usprawiedliwienie jest tańszym wyjściem niż
#: adnotacja i lista rośnie po cichu — dokładnie to, co 6.D29 zamknęło
#: `MAX_COMMIT_EXCEPTIONS` w `test_report_hygiene.py`.
MAX_JUSTIFICATIONS = 14

#: Próg na łączną liczbę dopasowań wzorca. Literówka we wzorcu daje ZERO dopasowań
#: i cały moduł zielony; ten próg jest jedynym powodem, dla którego taka literówka
#: jest widoczna. Zmierzone 07.09.2026 na drzewie idącym do scalenia (baza `aa64156`
#: plus ten commit): **29** ścieżek `bin/…/netX.Y/` w `reports/` i `docs/`, w 8 plikach,
#: z tego 22 niezgodne z `net10.0`. Na samej bazie było ich 19 w 7 plikach — różnicę
#: wnosi ten commit i mówi to wprost, bo bramka liczy także własny raport (6.A26).
# 29 -> 30 (14.09.2026, MB-08): ścieżka dopisana przez `HandleTrainKeysGateTests`,
# która szuka korzenia repozytorium po `MetroBxl.sln` i czyta `src/Game/FirstRun.cs`.
# 30 -> 31 (25.09.2026, #26): odtwarzalne polecenie Sim.Runner w raporcie
# `t400-performance-baseline-1080p.md` dopisało jedną ścieżkę bin/net10.0.
MIN_PATHS_IN_TREE = 31
# 8 -> 9 (14.09.2026, MB-08): `HandleTrainKeysGateTests.cs` — dziewiąty plik,
# który składa ścieżkę do drzewa. Ta zapadka idzie w parze z `MIN_PATHS_IN_TREE`
# i obie ruszają się razem, bo nowa bramka leksykalna czyta źródło `src/Game/`.
# 9 -> 10 (25.09.2026, #26): nowy raport jest dziesiątym plikiem ze ścieżką.
MIN_FILES_WITH_PATHS = 10


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def target_framework(text=None):
    """`netX.Y` z `<TargetFramework>` pliku projektu — WYPROWADZONE, nie wpisane."""
    if text is None:
        text = _read(os.path.join(ROOT, PROJECT))
    match = re.search(r"<TargetFramework>\s*(net[0-9]+\.[0-9]+)\s*</TargetFramework>", text)
    return match.group(1) if match else None


def is_command(line):
    """Czy wiersz JEST wołaniem programu, a nie cytatem jego wyjścia.

    Rozpoznanie składniowe: zdjęty znak zachęty `$ `, zdjęty wcięcie, pierwszy token
    z zamkniętej listy `PROGRAMS`. Wiersz `Sim.Runner -> src/…/MetroBxl.Sim.Runner.dll`
    komendą nie jest, i to jest cała różnica między szczeblem 2 i 3.
    """
    stripped = line.strip()
    if stripped.startswith("$ "):
        stripped = stripped[2:].strip()
    stripped = stripped.lstrip("`")
    token = re.match(r"([A-Za-z0-9_.+-]+)", stripped)
    return bool(token) and token.group(1) in PROGRAMS


def verification_lines(text):
    """Numery wierszy (od 1), które należą do pola „Weryfikacja" jakiegoś bloku.

    Cięcie takie samo jak w `backlog_commands.verification_field`: pole kończy się na
    następnym punkcie listy `- **…:**` albo na nagłówku. Numery, nie treść, bo bramka
    ma wskazać plik i wiersz.
    """
    inside = False
    out = set()
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith(VERIFICATION_MARKER):
            inside = True
        elif line.startswith("- **") or line.startswith("#"):
            inside = False
        if inside:
            out.add(number)
    return out


def scan(root=None, tfm=None):
    """Wszystkie ścieżki `bin/…/netX.Y/` z `reports/` i `docs/`.

    Zwraca listę słowników: `path` (ścieżka pliku względem korzenia), `line`, `prefix`,
    `version`, `stale` (czy `netX.Y` rozjeżdża się z plikiem projektu), `verification`
    (czy wiersz stoi w polu „Weryfikacja"), `command` (czy wiersz jest wołaniem),
    `text`. `tfm` podany jawnie służy WYŁĄCZNIE kontroli przyrządu.
    """
    root = ROOT if root is None else root
    tfm = target_framework() if tfm is None else tfm
    found = []
    for base in SCANNED:
        for dirpath, _, files in TW.walk(os.path.join(root, base), root):
            for name in sorted(files):
                if not name.endswith(".md"):
                    continue
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, root).replace(os.sep, "/")
                text = _read(full)
                fields = verification_lines(text) if rel == "docs/TASKS.md" else set()
                for number, line in enumerate(text.splitlines(), 1):
                    for match in PATH.finditer(line):
                        found.append({
                            "path": rel,
                            "line": number,
                            "prefix": match.group("prefix"),
                            "version": "net" + match.group("version"),
                            "stale": ("net" + match.group("version")) != tfm,
                            "verification": number in fields,
                            "command": is_command(line),
                            "text": line.strip(),
                        })
    return sorted(found, key=lambda hit: (hit["path"], hit["line"]))


def stale(hits=None):
    """Tylko te wystąpienia, których `netX.Y` rozjeżdża się z plikiem projektu."""
    return [hit for hit in (scan() if hits is None else hits) if hit["stale"]]


def _where(hit):
    return "%s:%d %s (%s)" % (hit["path"], hit["line"], hit["prefix"], hit["version"])


def unjustified(hits=None):
    """Zgłoszenia szczebla 3 bez wpisu na liście usprawiedliwień."""
    return [hit for hit in stale(hits)
            if (hit["path"], hit["prefix"]) not in JUSTIFICATIONS]


# --------------------------------------------------------------------------- testy


def test_the_project_file_still_declares_a_target_framework():
    """Bez tego bramka nie ma z czym porównywać i musi paść, a nie przejść."""
    tfm = target_framework()
    assert tfm is not None, PROJECT + " bez <TargetFramework> — bramka nie ma odniesienia"
    assert re.fullmatch(r"net\d+\.\d+", tfm), tfm


def test_the_scan_sees_the_measured_number_of_paths():
    """Próg KW: zepsuty wzorzec daje zero dopasowań i cały moduł świeci zielono.

    To jest najczęstszy sposób, w jaki bramka kłamie w stronę „wszystko w porządku",
    i jedyny powód, dla którego ten test istnieje osobno od pozostałych.
    """
    hits = scan()
    assert len(hits) >= MIN_PATHS_IN_TREE, (
        "wzorzec złapał %d ścieżek `bin/…/netX.Y/`, a 07.09.2026 było ich %d — "
        "spadek znaczy zepsuty wzorzec, nie posprzątane drzewo"
        % (len(hits), MIN_PATHS_IN_TREE))
    files = {hit["path"] for hit in hits}
    assert len(files) >= MIN_FILES_WITH_PATHS, sorted(files)

    # STRAŻNIK, dodany 12.09.2026 (6.D167). Dwie asercje wyżej są NOŚNE: padają,
    # gdy kurczy się drzewo. Nie padają, gdy ktoś obniży samą stałą — a obniżenie
    # stałej jest dokładnie tym, co człowiek robi odruchowo, gdy bramka zapali się
    # po skasowaniu jednej ścieżki. Do 12.09.2026 rejestr `test_tree_walks.py`
    # klasyfikował obie zapadki jako WOLNE, czyli ruch w zakazaną stronę nie
    # zapalał niczego, a stały DOKŁADNIE na stanie drzewa: 29 i 8.
    #
    # To ta sama usterka, którą 6.D45 zmierzyło na `MIN_REPORTS`, tylko w drugą
    # stronę — tam zapadka stała sto pozycji za drzewem i nie mierzyła nic, tu stoi
    # równo i nie broni się przed cofnięciem.
    #
    # KOSZT PRZYBICIA ZMIERZONY, NIE OSZACOWANY: populacja `bin/…/netX.Y/`
    # w `reports/` i `docs/` nie zmieniła się ANI RAZU w 59 przejściach historii
    # tych katalogów (jedna jedyna wartość w całym oknie). Równość kosztuje więc
    # zero — inaczej niż przy 6.D153, gdzie ten sam pomiar przybicie ODRADZAŁ
    # (29 zmian na 39 przejściach) i gdzie przybity został zbiór, a nie liczba.
    #
    # Kształt wyrażenia po prawej jest TREŚCIĄ, a nie stylem: klasyfikator
    # `klasa_zapadki` uznaje strażnika za przybijającego dopiero wtedy, gdy mierzy
    # TĘ SAMĄ populację co próg, porównując `ast.dump` obu stron. `len(hits)`
    # i `len(files)` muszą tu więc stać znak w znak tak, jak stoją wyżej.
    assert MIN_PATHS_IN_TREE >= len(hits), (
        "`MIN_PATHS_IN_TREE` = %d stoi PONIŻEJ drzewa (%d ścieżek) — zapadkę "
        "obniżono zamiast przeliczyć, a próg poniżej stanu nie mierzy już niczego"
        % (MIN_PATHS_IN_TREE, len(hits)))
    assert MIN_FILES_WITH_PATHS >= len(files), (
        "`MIN_FILES_WITH_PATHS` = %d stoi PONIŻEJ drzewa (%d plików) — jak wyżej"
        % (MIN_FILES_WITH_PATHS, len(files)))


def test_no_verification_field_cites_a_stale_framework_directory():
    """Szczebel 1: pole „Weryfikacja" jest obietnicą wykonalnej komendy.

    Ścieżki tu nie wolno usprawiedliwić — katalog `bin/Release/net8.0` nie istnieje,
    więc komenda kończy się awarią u każdego, kto ją wpisze.
    """
    bad = [_where(hit) for hit in stale() if hit["verification"]]
    assert bad == [], (
        "pole „Weryfikacja\" cytuje katalog, którego budowanie nie tworzy (%s): %s"
        % (target_framework(), bad))


def test_no_command_cites_a_stale_framework_directory():
    """Szczebel 2: wiersz, który JEST wołaniem, gdziekolwiek stoi.

    Komenda w prozie raportu jest przepisem do powtórzenia, nie cytatem wyjścia —
    dlatego nie dostaje usprawiedliwienia razem z cytatami.
    """
    bad = [_where(hit) for hit in stale() if hit["command"]]
    assert bad == [], (
        "komenda woła katalog, którego budowanie nie tworzy (%s): %s"
        % (target_framework(), bad))


def test_every_stale_path_in_prose_is_justified():
    """Szczebel 3: pomiar z datą wolno zostawić, ale nie po cichu."""
    bad = [_where(hit) for hit in unjustified()]
    assert bad == [], (
        "ścieżka z martwym `netX.Y` bez usprawiedliwienia i bez adnotacji: %s" % bad)


def test_a_matching_directory_is_never_reported():
    """KU: bramka łapiąca ścieżkę POPRAWNĄ zostałaby wyłączona w tym samym tygodniu.

    Nie wystarczy, że nic się nie zgłasza — trzeba pokazać, że ścieżki zgodne
    W DRZEWIE SĄ i że żadna z nich nie trafia do zgłoszeń. Inaczej ten test
    przechodziłby też wtedy, gdyby wzorzec nie łapał niczego.
    """
    hits = scan()
    tfm = target_framework()
    matching = [hit for hit in hits if hit["version"] == tfm]
    assert len(matching) >= 4, [_where(hit) for hit in matching]
    assert [_where(hit) for hit in matching if hit["stale"]] == []
    reported = {_where(hit) for hit in stale(hits)}
    assert not reported & {_where(hit) for hit in matching}


def test_the_verdict_follows_the_project_file():
    """KP: podmiana `TargetFramework` PRZENOSI zbiór zgłoszeń.

    Bez tego testu „bramka wyprowadzająca `netX.Y` z pliku projektu" byłaby
    nieodróżnialna od stałej `net10.0` wpisanej z pamięci: obie dają dziś ten sam
    zbiór zgłoszeń.
    """
    real = target_framework()
    assert real == "net10.0", real
    at_10 = {(hit["path"], hit["line"]) for hit in scan() if hit["stale"]}
    at_8 = {(hit["path"], hit["line"]) for hit in scan(tfm="net8.0") if hit["stale"]}
    assert at_10, "przy net10.0 bramka nie zgłasza niczego — nie ma czego porównywać"
    assert at_8, "przy net8.0 bramka nie zgłasza niczego — porównanie jest atrapą"
    assert at_10 != at_8, "zbiór zgłoszeń nie zależy od TargetFramework"
    assert not (at_10 & at_8), sorted(at_10 & at_8)


def test_a_framework_without_a_bin_segment_is_out_of_scope():
    """Granica wzorca, w obie strony, na wejściu syntetycznym.

    Wiersz `… - MetroBxl.Sim.Tests.dll (net8.0)` jest cytatem wyjścia `dotnet test`
    o tym, na czym testy WTEDY chodziły. Zgłaszanie go zamieniłoby bramkę w szum —
    takich wierszy jest w `reports/` kilkanaście.
    """
    assert PATH.search("Total: 77 - MetroBxl.Sim.Tests.dll (net8.0)") is None
    assert PATH.search("podniesienie projektów na `net10.0`") is None
    assert PATH.search("src/Sim/bin/Release/net8.0") is None       # bez segmentu PO wersji
    match = PATH.search("  Sim -> src/Sim/bin/Release/net8.0/MetroBxl.Sim.dll")
    assert match is not None
    assert match.group("prefix") == "src/Sim/bin/Release/net8.0"
    assert match.group("version") == "8.0"
    skrot = PATH.search("reports/T-311-braking.md:257    Sim.Runner/bin/Release/net8.0/…")
    assert skrot is not None and skrot.group("prefix") == "Sim.Runner/bin/Release/net8.0"


def test_a_command_is_told_apart_from_quoted_build_output():
    """Rozróżnienie szczebli 2 i 3 na wejściu syntetycznym.

    Bez tego testu `is_command` mogłaby zwracać `False` na wszystkim — a wtedy
    szczebel 2 byłby pusty zawsze i przechodziłby, także dla komendy z martwą ścieżką.
    """
    assert is_command("dotnet src/Sim.Runner/bin/Release/net8.0/MetroBxl.Sim.Runner.dll budget")
    assert is_command("$ dotnet build MetroBxl.sln --configuration Release")
    assert is_command("  python3 tools/tests/test_all.py")
    assert not is_command("  Sim.Runner -> src/Sim.Runner/bin/Release/net8.0/MetroBxl.Sim.Runner.dll")
    assert not is_command("reports/T-311-braking.md:257    Sim.Runner/bin/Release/net8.0/…")
    assert not is_command("Passed!  - Failed: 0, Passed: 173")


def test_the_verification_field_is_cut_the_same_way_as_in_backlog_commands():
    """Pole „Weryfikacja" musi być rozpoznawane, inaczej szczebel 1 jest atrapą.

    Kontrola na wejściu syntetycznym, bo w dzisiejszym drzewie szczebel 1 jest pusty
    i sam jego zielony kolor nie dowodzi niczego.
    """
    probka = "\n".join([
        "##### 9.Z1 · próbka",
        "- **Wejście:** nic",
        "- **Weryfikacja:**",
        "  ```bash",
        "  dotnet src/Sim.Runner/bin/Release/net8.0/MetroBxl.Sim.Runner.dll",
        "  ```",
        "- **Poza zakresem:** nic",
        "  dotnet src/Sim.Runner/bin/Release/net8.0/MetroBxl.Sim.Runner.dll",
    ])
    lines = verification_lines(probka)
    assert 5 in lines, sorted(lines)
    assert 8 not in lines, sorted(lines)
    assert 2 not in lines, sorted(lines)


def test_every_justification_still_describes_a_path_that_exists():
    """Usprawiedliwienie nie może przeżyć ścieżki, którą opisuje.

    Wpis, którego nie ma czego usprawiedliwiać, jest dziurą w bramce ubraną w prozę —
    ta sama zasada, którą 6.D29 postawiło dla listy wyjątków raportów, 6.B34 dla
    usprawiedliwień martwych stałych i 6.A26 dla komend runnera.
    """
    hits = stale()
    zywe = {(hit["path"], hit["prefix"]) for hit in hits}
    martwe = sorted(key for key in JUSTIFICATIONS if key not in zywe)
    assert martwe == [], (
        "usprawiedliwienie bez ścieżki, którą opisuje: %s" % martwe)
    puste = sorted(key for key, powod in JUSTIFICATIONS.items()
                   if len(powod.strip()) < 40)
    assert puste == [], (
        "usprawiedliwienie bez powodu podanego zdaniem: %s" % puste)


def test_the_justification_list_stays_closed():
    """Zapadka: lista rosnąca po cichu robi z usprawiedliwienia tańsze wyjście."""
    assert len(JUSTIFICATIONS) <= MAX_JUSTIFICATIONS, (
        "lista usprawiedliwień urosła do %d przy zapadce %d — pomiar z datą ma dostać "
        "adnotację, a nie miejsce na liście" % (len(JUSTIFICATIONS), MAX_JUSTIFICATIONS))
    assert MAX_JUSTIFICATIONS <= len(JUSTIFICATIONS), (
        "zapadka %d stoi wyżej niż lista (%d) — obniż ją do stanu faktycznego"
        % (MAX_JUSTIFICATIONS, len(JUSTIFICATIONS)))


def main():
    """Inwentarz do wklejenia w raport: wszystkie ścieżki z wyrokiem."""
    hits = scan()
    tfm = target_framework()
    print("TargetFramework z %s: %s" % (PROJECT.replace(os.sep, "/"), tfm))
    print()
    for hit in hits:
        szczebel = ("WERYFIKACJA" if hit["verification"]
                    else "KOMENDA" if hit["command"] else "proza/cytat")
        print("  %-7s %-34s %-6s %-12s %s"
              % ("ZGLOSZONA" if hit["stale"] else "zgodna",
                 hit["path"] + ":" + str(hit["line"]),
                 hit["version"], szczebel, hit["prefix"]))
    zgloszone = [hit for hit in hits if hit["stale"]]
    print()
    print("  wszystkich sciezek `bin/…/netX.Y/`: %d w %d plikach"
          % (len(hits), len({hit["path"] for hit in hits})))
    print("  zgodnych z %s: %d" % (tfm, len(hits) - len(zgloszone)))
    print("  ZGLOSZONYCH (niezgodnych): %d" % len(zgloszone))
    print("    z tego w polu „Weryfikacja\": %d"
          % len([hit for hit in zgloszone if hit["verification"]]))
    print("    z tego w wierszu, ktory JEST komenda: %d"
          % len([hit for hit in zgloszone if hit["command"]]))
    print("    z tego w prozie albo w cytacie wyjscia: %d"
          % len([hit for hit in zgloszone
                 if not hit["verification"] and not hit["command"]]))
    print("  usprawiedliwien na liscie: %d (zapadka %d)"
          % (len(JUSTIFICATIONS), MAX_JUSTIFICATIONS))
    print("  BEZ usprawiedliwienia: %d" % len(unjustified(hits)))
    for hit in unjustified(hits):
        print("    " + _where(hit))
    return 0


if __name__ == "__main__":
    import sys

    if "--inwentarz" in sys.argv:
        raise SystemExit(main())
    import test_all
    raise SystemExit(test_all.main(__file__))

#!/usr/bin/env python3
"""Ścieżka wymieniona w polu bloku `docs/TASKS.md` a plik, który w drzewie jest.

**Po co ta bramka istnieje.** `tools/tests/test_report_hygiene.py` pilnuje tego samego
dla `reports/`: ścieżka w grawisach albo się rozwiązuje, albo nie, i rozstrzyga to
system plików, a nie druga lista w teście. Dla bloków kolejki nie pilnował tego nikt,
a blok jest gorszym miejscem na złą ścieżkę niż raport: raport opisuje przeszłość,
a pole „Wejście" jest ADRESEM, pod który idzie następny agent. Zmierzone 07.09.2026
na `2ffb0b0` przez wszystkie 111 bloków:

    Wejście       442 ścieżek     1 nieistniejąca     1 usterka
    Wyjście        45 ścieżek     2 nieistniejące     0 usterek
    Weryfikacja   191 ścieżek     4 nieistniejące     2 usterki
    RAZEM         678

Usterek jest **trzy** i każda wysyła czytającego w puste miejsce:

  * **6.B5**, pole „Wejście": `tools/track/profile_scan.py` — plik leży
    w `tools/blender/profile_scan.py`.
  * **6.A30**, pole „Weryfikacja": `data/keys/L1_A-manual.json` — katalogu `data/keys`
    nie ma w drzewie WCALE; zapisy wejść leżą w `tests/data/`, a `--keys` wołają
    z `tests/data/manual-keys.log` wszystkie trzy bramki w
    `.github/workflows/godot-first-run.yml`.
  * **6.D35**, pole „Wejście": `tests/Sim.Tests/MetroBxl.Sim.Tests.csproj` — plik
    nazywa się `Sim.Tests.csproj`, a `MetroBxl.Sim.Tests` jest wartością
    `<AssemblyName>` i `<RootNamespace>` w tym pliku. Ta trzecia NIE była w pomiarze
    z bloku 6.D32 (tamten liczył 101 bloków i 387/40/149 ścieżek) i jest tu wpisana
    dlatego, że przeliczenie na świeżym `main` ją znalazło — szczebel 1 niżej nie
    dopuszcza wyjątku, więc nie było jak jej obejść.

**DLACZEGO TO NIE JEST BRAMKA „KAŻDA ŚCIEŻKA MUSI ISTNIEĆ".** Cztery z siedmiu
nieistniejących ścieżek są POPRAWNE, każda z innego powodu, i to one wyznaczają
kształt bramki. Bramka bez tego rozróżnienia zgłasza cztery poprawne pozycje na trzy
usterki i zostaje wyłączona w tym samym tygodniu (6.D27) — a wyłączona bramka jest
gorsza niż żadna, bo zostawia po sobie przekonanie, że coś było sprawdzane.

  (a) plik, który pozycja ma WYTWORZYĆ, w polu „Wyjście" — `tools/track/vertical_profile.py`
      (6.B44) i `tools/tests/test_test_track_fixture.py` (6.B8);
  (b) ten sam plik w KOMENDZIE, KTÓRA GO TWORZY — 6.B44 w polu „Weryfikacja";
  (c) ścieżka CELOWO nieistniejąca, bo o nią w teście chodzi —
      `tools/nie-ma-takiego-pliku.py` (6.B39).

**Trzy szczeble, bo trzy różne rzeczy.**

1. Pole „Wejście" — **twardy błąd, BEZ WYJĄTKU MOŻLIWEGO DO DOPISANIA PO CICHU**.
   To jest adres, pod który ktoś pójdzie. Wyjątku dla tego pola nie ma nie przez
   przeoczenie: `test_the_exception_list_stays_closed` sprawdza wprost, że żaden klucz
   `EXCEPTIONS` nie dotyczy pola „Wejście", więc dopisanie się tam jest widoczną
   zmianą asercji, nie jedną linijką w słowniku.
2. Pole „Weryfikacja" — nieistnienie przyjmowane TYLKO wtedy, gdy ten sam plik stoi
   w polu „Wyjście" TEGO SAMEGO bloku (rodzaj b) albo ma wpis na liście wyjątków
   z powodem (rodzaj c). „Tego samego bloku" jest istotne i sprawdzone na wejściu
   syntetycznym: plik z „Wyjścia" bloku X nie usprawiedliwia komendy w bloku Y.
3. Pole „Wyjście" — nieistnienie jest tu stanem NORMALNYM (rodzaj a). Reguła jest ta
   sama co dla szczebla 2 i dlatego dla tego pola wypada tożsamościowo; ma to jednak
   dwa mierzone skutki, więc nie jest pustym przebiegiem: liczy się do progu KW
   i **karmi szczebel 2** — zbiór „Wyjścia" bloku jest jedynym, co odróżnia 6.B44
   od 6.A30, bo obie ścieżki nie istnieją identycznie.

**CZEGO TA BRAMKA NIE ROBI, ŚWIADOMIE.**

* Nie sprawdza, czy komenda z pola „Weryfikacja" DZIAŁA — to jest 6.D33 i osobny
  pomiar (pole „Poza zakresem" pozycji 6.D32).
* Nie ogląda pól „Skąd" ani „Zależy od". Tam plik bywa cytowany jako historia
  („`reports/X.md` §3 podaje"), a nie jako wejście; objęcie ich zamieniłoby bramkę
  w zakaz cytowania czegokolwiek usuniętego. Granicę pilnuje
  `test_the_scan_reads_only_the_three_fields_that_promise_a_file`.
* Nie wymaga, żeby ODHACZONA pozycja miała już plik ze swojego „Wyjścia". Ta reguła
  wyglądałaby mocniej, a jest zmierzona jako fałszywy alarm: 6.B8 jest „ZROBIONE — i to
  nie w tej pozycji, tylko w 5.8", a plik `tools/tests/test_test_track_fixture.py`
  pod tą nazwą nie powstał nigdy. Jedyne dziś zgłoszenie tej reguły byłoby więc
  zgłoszeniem tekstu poprawnego.

**TRZECI KSZTAŁT: NAZWA MODUŁU (6.D101, 10.09.2026).** Pole „Weryfikacja" wołało
cztery moduły, których w drzewie nie ma — `test_physics_reference.py` (6.D86),
`test_glossary.py` (6.D89), `test_all_self.py` (6.D102) i `test_scan_gates.py`
(6.D74, który istnieje, ale testuje co innego). **Żadnego nie zgłosiła bramka**;
każdy znalazł ktoś, kto poszedł pod adres. `PATH_TOKEN` ich nie widzi z definicji:
żąda ukośnika, a nazwa modułu stoi po `test_all.py` jako goły argument.

Trzy rzeczy w tym kształcie są zmierzone, a nie przyjęte:

* **Czytany jest wyłącznie PIERWSZY argument**, bo `test_all.py` kończy się na
  `main(sys.argv[1]) if len(sys.argv)>1 else main()` — drugiego nie czyta nikt.
* **Rozstrzyga `test_all._only_path`, nie druga reguła zapisana tutaj.** Stąd nazwa
  bez rozszerzenia (`test_all.py test_report_claims`) jest poprawna: `_only_path`
  dokłada `.py` samo. Własna reguła rozjechałaby się z zestawem po cichu.
* **Nie każdy token po `test_all.py` jest nazwą.** W dzisiejszym pliku stoją tam
  także `|` (cały zestaw w potoku) i nazwy z ogonem `;` z łańcucha `cmd; cmd`.

Czwarty przypadek — `test_scan_gates.py` — jest **poza zasięgiem** i to jest wybór:
plik istnieje, a „czy moduł zawiera bramkę, o której pole mówi" to pytanie o TREŚĆ,
wykluczone wprost w polu „Poza zakresem" pozycji 6.D101.

**KONTROLE — każda WYKONANA, wypisane w `reports/sciezki-w-polach-blokow.md`:**

  KD (dodatnia)  literówka wstawiona w pole „Wejście" jednego bloku wywraca DOKŁADNIE
                 tę bramkę i nazywa blok oraz ścieżkę. Pilnuje tego na stałe
                 `test_the_three_kinds_of_exception_are_told_apart_on_synthetic_input`.
  KU (ujemna)    cztery poprawne ścieżki NIE są zgłaszane, a zdjęcie rozróżnienia pól
                 PRZENOSI zbiór zgłoszeń — na drzewie przed poprawką z 3 na 7, po
                 poprawce z 0 na 4. Bez tej pary „wyjątki" mogłyby milczeć, bo nic ich
                 nie dotyczy. Pilnuje tego `test_removing_the_field_distinction_moves_the_reported_set`.
  KW (wzorzec)   wzorzec zepsuty daje ZERO dopasowań i wszystko zielone — najczęstszy
                 sposób, w jaki bramka kłamie w stronę „w porządku". Pilnują tego progi
                 `MIN_PATHS` (per pole, nie łącznie: literówka w cięciu JEDNEGO pola
                 nie schowałaby się wtedy za dwoma pozostałymi).
  KP (pułapka)   alternatywa rozszerzeń w złej kolejności dopasowuje `.cs` do
                 PRZEDROSTKA `.csproj` i `.csv`, a `.json` do `.jsonl`, dając tokeny,
                 z których żaden nie istnieje. Zmierzone: taki wzorzec zgłasza trzy
                 nieistniejące „ścieżki" na drzewie bez ani jednej usterki tego rodzaju.
                 Pilnuje tego `test_the_extension_alternation_is_ordered_longest_first`.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backlog_commands as bc  # noqa: E402
import test_backlog as tb  # noqa: E402
import tree_walk as tw  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TASKS = os.path.join(ROOT, "docs", "TASKS.md")

#: Trzy pola, których treść OBIECUJE plik. Nazwy w brzmieniu z `docs/TASK-TEMPLATE.md`
#: i z `test_backlog.REQUIRED_FIELDS` — to samo cięcie dokumentu, więc bramka nie
#: trzyma drugiej listy tego, jak wygląda blok.
FIELDS = ("Wejście", "Wyjście", "Weryfikacja")

#: Pole, którego zbiór ścieżek USPRAWIEDLIWIA nieistnienie w pozostałych polach
#: tego samego bloku.
OUTPUT_FIELD = "Wyjście"

#: Pole bez prawa do wyjątku. Osobna stała, bo na niej stoi asercja w
#: `test_the_exception_list_stays_closed`, a nie tylko zdanie w docstringu.
HARD_FIELD = "Wejście"

#: Ścieżka repozytoryjna: token z UKOŚNIKIEM i ze znanym rozszerzeniem.
#:
#: KOLEJNOŚĆ ALTERNATYWY JEST OD NAJDŁUŻSZEGO I TO NIE JEST KOSMETYKA. `cs` postawione
#: przed `csproj` i `csv` dopasowuje się do ich PRZEDROSTKA, a `json` przed `jsonl` do
#: przedrostka `jsonl`; wynikiem są tokeny `tests/Sim.Tests/Sim.Tests.cs`,
#: `data/network/station-depths.cs` i `reports/x.json` — ani jeden nie istnieje, więc
#: zły wzorzec produkuje zgłoszenia z niczego. Domknięcie `(?![A-Za-z0-9])` robi to
#: samo drugą drogą i jest tu OBOK kolejności, nie zamiast niej: samo domknięcie
#: wystarcza tylko dlatego, że silnik `re` cofa się po alternatywie, a poleganie na
#: nawrotach jest poleganiem na szczególe implementacji. Zmierzone —
#: `test_the_extension_alternation_is_ordered_longest_first`.
#:
#: WIODĄCA KROPKA JEST DOZWOLONA, bo `.github/workflows/*.yml` to prawdziwe wejście
#: piętnastu wystąpień w dziesięciu blokach. Wzorzec `reports/` (6.D3) jej nie
#: dopuszcza i przez to tamtych ścieżek nie oglądał wcale.
#:
#: Glob (`.github/workflows/*.yml`, `tools/tests/test_*.py`) odpada sam: ostatni
#: segment musi zaczynać się od znaku słowa, a `*` nim nie jest. To jest wybór —
#: glob nie jest plikiem i „nie istnieje" nie jest o nim zdaniem prawdziwym.
PATH_TOKEN = re.compile(
    r'(?<![A-Za-z0-9_./-])'
    r'(\.?[A-Za-z0-9_][A-Za-z0-9_./+-]*'
    r'/[A-Za-z0-9_][A-Za-z0-9_.+-]*'
    r'\.(?:geojson|csproj|jsonl|yaml|json|tscn|glb|yml|txt|png|csv|zip|log|sh|md|py|cs))'
    r'(?![A-Za-z0-9])')

#: Przedrostki, których nie ma po co sprawdzać — te same co w
#: `test_report_hygiene.IGNORED_PREFIXES`: wytwory przebiegu (reguła 8 zabrania ich
#: komitować, więc ich BRAK jest stanem poprawnym), ścieżki Godota, katalogi
#: tymczasowe i adresy.
IGNORED_PREFIXES = ("build/", "renders/", "res://", "/tmp/", "http://", "https://",
                    "/opt/", "/usr/", "~/")

#: Progi KW, PER POLE. Zmierzone 07.09.2026 na `2ffb0b0`: 442 / 45 / 191. Próg stoi
#: niżej, żeby nie trzeba go było ruszać przy każdym nowym bloku, ale osobno dla
#: każdego pola — jeden łączny próg (678) przeżyłby literówkę w cięciu pola „Wyjście",
#: bo jego 45 ścieżek to 6 % sumy.
MIN_PATHS = {"Wejście": 420, "Wyjście": 40, "Weryfikacja": 180}

#: Próg KW dla trzeciego kształtu, na blokach WSZYSTKICH. Zmierzone 10.09.2026:
#: **66** nazw (30 różnych), wszystkie w polu „Weryfikacja"; na `c724001`, czyli
#: w dniu, w którym pozycja 6.D101 powstała, było ich **60** i stąd ta liczba jako
#: próg — poniżej dzisiejszego stanu, żeby nie ruszać go przy każdym nowym bloku.
#:
#: Progu na blokach OTWARTYCH tu nie ma, i to jest ten sam wybór, co przy katalogach:
#: kolejka maleje z każdą scaloną pozycją, więc taki próg czerwieniałby od SPRZĄTANIA.
MIN_MODULE_NAMES = 60

#: JAWNE WYJĄTKI (rodzaj c): ścieżka, o której NIEISTNIENIE w teście chodzi. Klucz to
#: `(numer bloku, pole, ścieżka)` — nie numer wiersza, bo wiersz przesuwa każdy commit
#: dopisujący cokolwiek wyżej, a bramka zapalająca się na tekście poprawnym zostaje
#: wyłączona, nie naprawiona (6.D27, 6.A31).
#:
#: Pola „Wejście" na tej liście być nie może i pilnuje tego asercja, nie zdanie.
EXCEPTIONS = {
    ("6.B39", "Weryfikacja", "tools/nie-ma-takiego-pliku.py"):
        "Ścieżka jest CELOWO nieistniejąca: pozycja 6.B39 mierzy kod wyjścia "
        "`mutation_sweep.py --only` przy zerze trafień, a `--only` na module, którego "
        "nie ma, jest najkrótszym sposobem wymuszenia zera. Plik o tej nazwie nie "
        "powstanie nigdy i nie ma powstać — gdyby powstał, komenda z pola przestałaby "
        "mierzyć to, po co ją tam wpisano.",
}

#: Zapadka na listę wyżej. Wolno ją tylko OBNIŻAĆ. Bez niej wyjątek jest tańszym
#: wyjściem niż poprawka ścieżki i lista rośnie w jedną stronę z definicji —
#: dokładnie to, co 6.D29 zamknęło `MAX_COMMIT_EXCEPTIONS` w `test_report_hygiene.py`,
#: a 6.A31 `MAX_JUSTIFICATIONS`.
MAX_EXCEPTIONS = 1


def _tasks():
    with open(TASKS, encoding="utf-8") as handle:
        return handle.read()


def field_body(body, field):
    """Treść pola bloku albo `None`, gdy pola nie ma.

    Cięcie DOKŁADNIE takie, jak w `test_backlog.missing_fields` i
    `backlog_commands.verification_field`: pole kończy się na następnym punkcie listy
    `- **…:**`. Zgodność z tym drugim jest sprawdzana testem, a nie założona —
    `test_the_field_is_cut_the_same_way_as_in_backlog_commands`.
    """
    marker = "- **%s:**" % field
    at = body.find(marker)
    if at < 0:
        return None
    rest = body[at + len(marker):]
    nxt = re.search(r"\n- \*\*", rest)
    return rest if nxt is None else rest[:nxt.start()]


def paths_in(text):
    """Ścieżki repozytoryjne z treści, w kolejności wystąpienia, z powtórzeniami."""
    out = []
    for token in PATH_TOKEN.findall(text or ""):
        if "/" not in token or token.startswith(IGNORED_PREFIXES):
            continue
        out.append(token)
    return out


def scan(text=None, root=None):
    """Wszystkie ścieżki z trzech pól każdego bloku `docs/TASKS.md`.

    Zwraca listę słowników: `number`, `field`, `path`, `exists`, `in_own_output`
    (czy ten sam plik stoi w polu „Wyjście" TEGO SAMEGO bloku). Powtórzenia zostają,
    bo próg KW liczy wystąpienia; werdykty niżej idą po unikatach.
    """
    root = ROOT if root is None else root
    blocks = tb.detail_sections(_tasks() if text is None else text)
    found = []
    for number in sorted(blocks):
        body = blocks[number]
        produced = set(paths_in(field_body(body, OUTPUT_FIELD) or ""))
        for field in FIELDS:
            content = field_body(body, field)
            if content is None:
                continue
            for path in paths_in(content):
                found.append({
                    "number": number,
                    "field": field,
                    "path": path,
                    "exists": os.path.exists(os.path.join(root, path)),
                    "in_own_output": path in produced,
                })
    return found


def _key(hit):
    return (hit["number"], hit["field"], hit["path"])


def accepted(hit, distinguish=True):
    """Czy nieistnienie tej ścieżki jest stanem POPRAWNYM.

    `distinguish=False` zdejmuje rozróżnienie pól i jest jedynym powodem, dla którego
    ten argument istnieje: bez niego nie da się pokazać, że wyjątki cokolwiek MIERZĄ,
    a nie tylko milczą, bo nic ich nie dotyczy.
    """
    if not distinguish:
        return False
    if hit["field"] == HARD_FIELD:
        return False
    return hit["in_own_output"] or _key(hit) in EXCEPTIONS


def reported(hits=None, distinguish=True):
    """Unikalne `(numer, pole, ścieżka)`, które bramka ZGŁASZA."""
    hits = scan() if hits is None else hits
    return sorted({_key(hit) for hit in hits
                   if not hit["exists"] and not accepted(hit, distinguish)})


def _where(key):
    return '%s „%s": %s' % (key[0], key[1], key[2])


# --------------------------------------------------------------------------- testy


# --- 6.D73: katalog i nazwa opcji, czyli dwa kształty, których skan ścieżek nie widzi ---
#
# **Poprawka do pola „Wejście" tej pozycji, i jest to ta sama usterka, o której ona
# jest.** Wpis 6.D73 wskazuje `tools/tests/test_backlog.py` jako miejsce, gdzie stoi
# „skan pól i wyjątki ścieżek". Skan przeprowadził się do TEGO pliku przy 6.D32
# (#388), więc pole nazywa adres, pod którym tej rzeczy nie ma — dokładnie to, co
# pozycja tropi, tyle że w niej samej.
#
# Dlaczego dwa NOWE kształty, a nie rozszerzenie `PATH_TOKEN`. Ścieżka pliku ma
# rozszerzenie i to ono odróżnia ją od prozy; katalog rozszerzenia nie ma, a nazwa
# opcji nie jest ścieżką w ogóle. Wciągnięcie ich do jednego wzorca zamieniłoby go
# w łapacz słów ze znakiem `/` albo `-`.

#: Katalog w treści pola: **co najmniej dwa** segmenty i ukośnik na końcu. Oba warunki
#: są zmierzone, nie ostrożnościowe. Jeden segment łapie `CPU/` ze zwrotu „stosunek
#: CPU/ściana" i `bin/`, `obj/` z opisu wytworów budowania — 8 z 11 zgłoszeń pierwszej
#: wersji. Ukośnik na końcu jest jedyną rzeczą, która w prozie odróżnia katalog od
#: nazwy własnej. Wykluczenie `$` odsiewa `$DOTNET_ROOT/host/fxr/`, czyli ścieżkę
#: zbudowaną ze zmiennej — o niej „nie istnieje" nie jest zdaniem prawdziwym.
DIR_TOKEN = re.compile(
    r'(?<![A-Za-z0-9_./$-])((?:\.?[A-Za-z0-9_][A-Za-z0-9_.+-]*/){2,})(?![A-Za-z0-9_.])')

#: Wywołanie WŁASNEGO narzędzia pythonowego w bloku kodu.
PY_TOOL_CALL = re.compile(r"python3\s+(tools/[A-Za-z0-9_./-]+\.py)")

#: Wywołanie sceny Godota; argumenty sceny stoją za `--path src/Game`.
SCENE_CALL = "--path src/Game"

#: Wywołanie zestawu z nazwą modułu — trzeci kształt „pole nazywa coś, czego nie ma"
#: (6.D101). Nazwa modułu stoi po `test_all.py` jako GOŁY ARGUMENT, bez ukośnika,
#: więc `PATH_TOKEN` jej nie widzi z definicji: tamten wzorzec ukośnika żąda.
#:
#: **Brane są WSZYSTKIE argumenty wywołania, nie tylko pierwszy — i ten akapit jest
#: PRZEPISANY, a nie dopisany obok (16.09.2026, 6.D237).** Do tego dnia stało tu, że
#: „brany jest WYŁĄCZNIE pierwszy argument", z uzasadnieniem, że `test_all.py` kończy
#: się na `main(sys.argv[1]) if len(sys.argv)>1 else main()`, więc drugiego argumentu
#: nie czyta nikt. **To już nieprawda i nie było prawdą od 11.09.2026**: komentarz
#: powstał w 6.D101 (10.09.2026), a strażnik `__main__` zmieniono w 6.D114 na
#: `main(sys.argv[1:]) if len(sys.argv)>1 else main()`. Zmierzone 16.09.2026 —
#: `python3 tools/tests/test_all.py test_crs.py test_lod.py` daje **82/82 przeszło**
#: i **2 modułów**, czyli obie nazwy zostają wykonane.
#:
#: **Wzorzec bierze OGON wywołania, a nie jeden token, i rozbiera go PREFIKSOWO** —
#: token po tokenie, aż do pierwszego, który nazwą modułu nie jest. Postać „wszystkie
#: tokeny z ogona" (bez zatrzymania) jest o jedną literę krótsza i **zmierzenie
#: pokazało, że jest zła**: 16.09.2026 na `docs/TASKS.md` dawała **8 fałszywych
#: zgłoszeń** na wszystkich blokach (`grep`, `RAZEM`, `done` z potoku w 6.D26, `echo`
#: z `; echo "kod: $?"` w 6.D44/45/63, `dotnet` i `test` z `&& dotnet test` w 6.D234),
#: a bez filtru `MODULE_ARGUMENT` — **17**. Postać prefiksowa daje **0**. To jest ta
#: sama rodzina co 6.D27: bramka zapalająca się na poleceniu POPRAWNYM zostaje
#: wyłączona, nie naprawiona.
#:
#: **Ogon kończy też token z średnikiem** i to nie jest kosmetyka: `test_x.py;` jest
#: nazwą modułu po odcięciu średnika (tak czyta ją `MODULE_ARGUMENT` od 6.D101), ale
#: średnik jest końcem POLECENIA — bez zatrzymania na nim `echo` z `; echo "kod: $?"`
#: wchodzi jako nazwa modułu. Trzy takie wiersze stoją dziś w `docs/TASKS.md`.
MODULE_CALL = re.compile(r"test_all\.py((?:\s+\S+)*)")

#: Kształt, jaki musi mieć argument, żeby BYĆ nazwą modułu. Zmierzone na dzisiejszym
#: `docs/TASKS.md`: po `test_all.py` stoi też `|` (wywołanie całego zestawu w potoku)
#: oraz nazwy z ogonem `;` (`test_ci_workflows.py;` w łańcuchu `cmd; cmd`). Pierwsze
#: nazwą modułu nie jest i nie ma być nią nazwane; drugie jest nią po odcięciu
#: średnika. Przekierowanie (`2>&1`) i opcja (`--x`) odpadają tym samym wzorcem, bo
#: token bierze się w całości i dopiero potem sprawdza — a nie odwrotnie.
MODULE_ARGUMENT = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")

#: Opcje, o których argparse wie bez `add_argument`.
ARGPARSE_BUILTINS = ("--help",)


def _code_lines(text):
    """Wiersze z bloków ogrodzonych — czyli POLECENIA, a nie proza o nich.

    Bez tego zawężenia skan opcji zgłaszał `--follow` ze zdania
    „`git log --follow` jako narzędzie": nazwa opcji stała tam w prozie, obok nazwy
    pliku, i została przypisana do niego. Zmierzone przy pierwszej wersji tej bramki.
    """
    out, inside = [], False
    for line in (text or "").splitlines():
        if line.strip().startswith("```"):
            inside = not inside
            continue
        if inside:
            out.append(line)
    return out


def _argparse_options(relative):
    """Nazwy opcji, które narzędzie NAPRAWDĘ parsuje — z drzewa składni, nie z grepa.

    Grep po napisie `--nazwa` łapie też komentarze i teksty pomocy, czyli miejsca,
    w których opcja jest OPISANA, a nie zadeklarowana — a właśnie ta różnica jest
    treścią tej bramki.
    """
    import ast

    try:
        tree = ast.parse(open(os.path.join(ROOT, relative), encoding="utf-8").read())
    except (OSError, SyntaxError):
        return None
    names = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) \
                        and arg.value.startswith("-"):
                    names.add(arg.value)
    return names


def _scene_arguments():
    """`KnownArguments` ze sceny — ta sama lista, którą czyta `test_ci_workflows.py`."""
    source = open(os.path.join(ROOT, "src", "Game", "RunPlan.cs"), encoding="utf-8").read()
    block = re.search(r"KnownArguments\s*=\s*\{(.*?)\};", source, re.S)
    return set(re.findall(r'"([a-z-]+)"', block.group(1))) if block else set()


def _open_blocks():
    """Bloki pozycji, które są jeszcze DO WZIĘCIA.

    Zapis pozycji wykonanej jest historią: jej „Weryfikacja" cytuje polecenie, którym
    coś zmierzono, a narzędzie mogło się od tamtej pory zmienić — i przepisanie tego
    cytatu sfałszowałoby pomiar. Ta sama zasada, co przy markerach historycznych
    w `test_docs_ci_claims.py` i przy datowanych liczbach w raportach.

    **Rozstrzygnięcie 6.D126 (11.09.2026): zapis NIEAKTUALNY zostaje, zapis FAŁSZYWY
    wolno poprawić — i to jest różnica, której powyższe zdanie nie robiło.**

    Uzasadnienie wyłączenia bloków wykonanych mówi o poleceniu, które **było
    prawdziwe w dniu pomiaru** i zestarzało się razem z narzędziem. Przepisanie go
    faktycznie sfałszowałoby pomiar: czytający zobaczyłby polecenie, którym nikt
    niczego nie mierzył. Ten powód **nie obejmuje** zapisu, który prawdziwy nie był
    nigdy — adresu modułu, w którym opisywanej bramki nie było ani w dniu pomiaru,
    ani później. Tam przepisanie niczego nie fałszuje, a zostawienie każe dokumentowi
    twierdzić nieprawdę.

    **Zmierzone 11.09.2026 na `2d251b7`.** Blok 6.D74 wołał w polu „Weryfikacja"
    `test_scan_gates.py` jako miejsce bramki o przejściach po drzewie. Bramka mieszka
    w `test_tree_walks.py`; `test_scan_gates.py` w drzewie **jest** i testuje trzy
    predykaty skanu luzu z `tools/blender/scan_gates.py`. `missing_modules` tego nie
    widzi z dwóch niezależnych powodów naraz: moduł istnieje (więc `_only_path` go
    przyjmuje), a blok jest wykonany (więc skan i tak by go nie czytał).

    **Warunki poprawki, wszystkie trzy naraz** — inaczej „fałszywy" stanie się furtką
    do przepisywania historii:

      1. zapis jest fałszywy, a nie przestarzały: rzeczy, o której mówi, nie było pod
         tym adresem także w dniu, w którym pole powstało;
      2. poprawka niesie adnotację `**Poprawione <data> …:**` z tym, co stało wcześniej,
         i z powodem — czyli dawny zapis zostaje czytelny obok nowego;
      3. adnotacja mówi, gdzie stoi ta reguła, żeby następny nie rozstrzygał od nowa.

    Konwencja adnotacji nie jest tu wymyślona: projekt użył jej **cztery razy**
    10.09.2026 (bloki 6.D73, 6.D74, 6.D86, 6.D89), za każdym razem ad hoc i bez
    zapisanej reguły. Trzy z tych czterech dotyczyły modułu, którego w drzewie NIE MA;
    jedna — 6.D101 o sobie samej — modułu, który jest, i to ta jedna pokazuje, czego
    bramka adresów nie złapie nigdy. Kształtu adnotacji pilnuje
    `test_kazda_poprawka_zapisu_wykonanego_niesie_date_i_powod`.
    """
    tasks = _tasks()
    otwarte = set(tb.open_items(tasks))
    return {n: b for n, b in tb.detail_sections(tasks).items() if n in otwarte}


def _all_blocks():
    """Wszystkie bloki, także wykonane — do kotwic na zamrożonych przypadkach."""
    return tb.detail_sections(_tasks())


def directories_in(text):
    """Katalogi wymienione w treści pola, bez przedrostków pomijanych."""
    return [d for d in DIR_TOKEN.findall(text or "")
            if not d.startswith(IGNORED_PREFIXES)]


def unknown_options(blocks=None):
    """`(numer, pole, narzędzie, opcja)` dla opcji, których narzędzie nie parsuje."""
    found = []
    scene = _scene_arguments()
    for number, body in (blocks if blocks is not None else _open_blocks()).items():
        for field in FIELDS:
            for line in _code_lines(field_body(body, field)):
                call = PY_TOOL_CALL.search(line)
                if call and os.path.isfile(os.path.join(ROOT, call.group(1))):
                    known = _argparse_options(call.group(1))
                    if known is not None:
                        rest = line[call.end():].split("|")[0].split("&&")[0]
                        for option in re.findall(r"(?<![\w-])(--[a-z][a-z0-9-]*)", rest):
                            if option not in known and option not in ARGPARSE_BUILTINS:
                                found.append((number, field, call.group(1), option))
                if SCENE_CALL in line:
                    rest = line.split(SCENE_CALL, 1)[1]
                    for option in re.findall(r"(?<!-)--([a-z][a-z0-9-]*)", rest):
                        if option not in scene:
                            found.append((number, field, "src/Game/RunPlan.cs",
                                          "--" + option))
    return found


def _rozbior_ogona(ogon):
    """Nazwy modulu z ogona JEDNEGO wywolania `test_all.py`, po kolei — 6.D237.

    **Jedyny rozbior ogona w tym module i to jest wymog, a nie porzadek (6.D213).**
    Do 17.09.2026 ta sama petla stala DWA RAZY: tu i w `nazwy_z_dalszego_argumentu`.
    Kopie nie rozjechaly sie tresciowo, ale rozjechaly sie w tym, co WIDZA bramki:
    kontrola negatywna oslepiajaca `module_names` (`return out` na wejsciu) zapalila
    DWANASCIE testow, a podloga `MIN_NAZW_Z_DALSZEGO_ARGUMENTU` — ktora istnieje
    dokladnie po to, zeby lapac zwezenie tego rozbioru — ZOSTALA ZIELONA, bo czytala
    wlasna kopie. Podloga pilnujaca czytnika, ktorego nie uzywa, jest napisem.

    Zatrzymanie jest PREFIKSOWE: token po tokenie, az do pierwszego, ktory nazwa
    modulu nie jest, oraz wlacznie z tym, ktory niesie srednik (`test_x.py;` konczy
    polecenie). Powod liczbowo stoi przy `MODULE_CALL`.
    """
    out = []
    for surowy in ogon.split():
        token = surowy.rstrip(";")
        if not MODULE_ARGUMENT.match(token):
            break
        out.append(token)
        if token != surowy:
            break
    return out


def module_names(text):
    """Nazwy modułów wołanych przez `test_all.py` w blokach ogrodzonych treści.

    Płotek, a nie cała treść pola: w prozie ta sama nazwa bywa CYTOWANA („bramkę
    trzyma `test_backlog.py`"), a cytat nie jest wywołaniem. To samo zawężenie, co
    przy skanie opcji, i z tego samego zmierzonego powodu.

    **Argumentów jest tyle, ile stoi w wierszu — 6.D237 (16.09.2026).** Rozbiór jest
    PREFIKSOWY: token po tokenie, aż do pierwszego, który nazwą modułu nie jest, oraz
    włącznie z tym, który niesie średnik (`test_x.py;` kończy polecenie). Powód
    liczbowo: postać bez zatrzymania dawała na `docs/TASKS.md` osiem fałszywych
    zgłoszeń, ta — zero. Pełny wywód przy `MODULE_CALL`.
    """
    out = []
    for line in _code_lines(text):
        for call in MODULE_CALL.finditer(line):
            out.extend(_rozbior_ogona(call.group(1)))
    return out


def missing_modules(blocks=None):
    """`(numer, pole, nazwa)` dla nazw modułów, których `test_all.py` nie zna.

    Rozstrzyga `test_all._only_path`, a nie druga reguła zapisana tutaj. Drugi
    czytnik tej samej rzeczy rozjechałby się po cichu — a rozjazd akurat TEJ pary
    znaczyłby, że bramka przyjmuje nazwę, której zestaw odmówi, albo odwrotnie.
    Stąd też akceptacja nazwy BEZ rozszerzenia: `test_all.py test_report_claims`
    jest poprawnym wywołaniem, bo `_only_path` dokłada `.py` samo.
    """
    import test_all

    found = []
    for number, body in (blocks if blocks is not None else _open_blocks()).items():
        for field in FIELDS:
            for name in module_names(field_body(body, field)):
                try:
                    test_all._only_path(name)
                except ValueError:
                    found.append((number, field, name))
    return found


def missing_directories(blocks=None):
    """`(numer, pole, katalog)` dla katalogów, których w drzewie nie ma."""
    found = []
    for number, body in (blocks if blocks is not None else _open_blocks()).items():
        for field in FIELDS:
            for directory in directories_in(field_body(body, field)):
                if not os.path.isdir(os.path.join(ROOT, directory.rstrip("/"))):
                    found.append((number, field, directory))
    return found


def test_no_open_field_names_a_directory_that_is_not_in_the_tree():
    """Katalog w polu zadania jest sprawdzany jak plik — 6.D73.

    **Skąd.** Pole „Wyjście" pozycji 6.A21 wskazywało `tools/ci/golden/`, katalogu
    o tej nazwie w drzewie nie ma, a polecenie z pola kończyło się
    `fatal: ambiguous argument 'tools/ci/golden/'` — wzorce śladu leżą
    w `tests/data/golden-trace/`. Skan ścieżek tego nie widział, bo jego wzorzec żąda
    ROZSZERZENIA na ostatnim segmencie, a katalog go nie ma.
    """
    bad = missing_directories()
    assert bad == [], "pole zadania nazywa katalog, którego w drzewie nie ma: %s" % bad
    # Pusta lista jest zielona także wtedy, gdy wzorzec przestał cokolwiek łapać —
    # więc przyrząd jest przybity do ZAMROŻONEGO przypadku, a nie do progu liczbowego.
    # Progu po liczbie katalogów w otwartych blokach tu nie ma świadomie: kolejka
    # maleje z każdą scaloną pozycją, więc taki próg czerwieniałby od SPRZĄTANIA.
    # Blok 6.A21 jest wykonany, jego zapis jest historyczny (pole „Poza zakresem"
    # pozycji 6.D73) i dlatego nadaje się na kotwicę: `tools/ci/golden/` stoi tam
    # nieruchomo, TRZY razy (raz w „Wejściu", dwa razy w „Weryfikacji"), i nie ma go
    # w drzewie.
    kotwica = missing_directories({"6.A21": _all_blocks()["6.A21"]})
    assert [d for _n, _f, d in kotwica] == ["tools/ci/golden/"] * 3, (
        "wzorzec katalogu przestał widzieć zamrożony przypadek 6.A21: %s" % kotwica)


def test_no_open_field_calls_an_option_the_tool_does_not_parse():
    """Nazwa opcji w polu jest zestawiana z opcjami, które narzędzie NAPRAWDĘ parsuje.

    **Skąd.** Pole „Weryfikacja" pozycji 6.B43 wołało scenę z `--at-m=96` i `--out=…`,
    a scena zna `--at-chainage` i nie zna żadnego z tych dwóch. Nazwa opcji nie jest
    ścieżką, więc skan ścieżek nie miał jej jak zobaczyć — trzeci kształt tego samego
    wzorca „pole nazywa coś niewykonalnego".
    """
    bad = unknown_options()
    assert bad == [], "pole zadania woła opcję, której narzędzie nie parsuje: %s" % bad
    # Kotwica na zamrożonym bloku, z tego samego powodu co wyżej. 6.B43 jest wykonane,
    # a jego pole „Weryfikacja" woła dwie opcje, których scena nie zna — obie muszą tu
    # wyjść, inaczej cisza w otwartych blokach nic nie znaczy.
    kotwica = [o for _n, _f, _t, o in unknown_options({"6.B43": _all_blocks()["6.B43"]})]
    assert kotwica == ["--at-m", "--out"], (
        "wzorzec opcji przestał widzieć zamrożony przypadek 6.B43: %s" % kotwica)
    # Drugi kierunek tej samej kotwicy: opcje, które scena ZNA, nie mogą się tam
    # pojawić. Bez tego „widzi dwie" byłoby prawdą także dla skanu zgłaszającego
    # wszystko, co zaczyna się od dwóch myślników.
    assert "--shot" not in kotwica and "--view" not in kotwica


def test_zadne_pole_nie_wola_modulu_spoza_drzewa():
    """Nazwa modułu po `test_all.py` jest sprawdzana na istnienie — 6.D101.

    **Zakres rozszerzony 11.09.2026 (6.D146) z bloków OTWARTYCH na WSZYSTKIE, i ten
    akapit jest dopisany do zdania, które zostaje.** Poprzednia wersja czytała tylko
    bloki otwarte i nazywała się `test_no_open_field_…`; blok wykonany wypadał jej
    z pola widzenia w chwili odhaczenia. Dwa z pięciu zapisów poprawionych w tym
    drzewie (6.D86 i 6.D89) były dokładnie tego kształtu — nazwa modułu, którego nie
    ma — i oba znalazł człowiek, już PO odhaczeniu bloku, kiedy ta bramka przestała
    na nie patrzeć.

    Rozszerzenie kosztuje dziś **zero**: zmierzone 11.09.2026 na 216 blokach
    wykonanych — 92 wywołania modułu w polu „Weryfikacja", z czego nieistniejących
    **ani jednego**. Bramka pilnuje więc czegoś, czego dziś nie ma, i o to chodzi.

    **Skąd.** Cztery pola „Weryfikacja" wołały moduły, których w drzewie nie ma:
    `test_physics_reference.py` (6.D86), `test_glossary.py` (6.D89),
    `test_all_self.py` (6.D102) — i `test_scan_gates.py` (6.D74), który ISTNIEJE,
    ale testuje co innego. Żadnego nie zgłosiła bramka; wszystkie cztery znalazł
    ktoś, kto poszedł pod adres. Skan ścieżek ich nie widzi, bo `PATH_TOKEN` żąda
    ukośnika, a nazwa modułu stoi jako goły argument.

    **Czwarty przypadek jest poza zasięgiem tej bramki i to jest wybór, nie luka.**
    `test_scan_gates.py` w drzewie jest; „czy moduł zawiera bramkę, o której pole
    mówi" to pytanie o TREŚĆ, a pole „Poza zakresem" tej pozycji wyklucza je wprost.
    """
    bad = missing_modules(_all_blocks())
    assert bad == [], (
        "pole zadania woła moduł, którego `test_all.py` nie zna: %s" % bad)

    # Cisza wyżej znaczy coś dopiero z kotwicami na ZAMROŻONYCH kształtach, bo
    # wszystkie cztery zmierzone przypadki zostały poprawione przy swoich pozycjach
    # i w drzewie nie ma dziś ani jednej złej nazwy do złapania.
    #
    # Kotwica 1: nazwa BEZ rozszerzenia. `test_all.py` dokłada `.py` samo, więc
    # `test_report_claims` jest wywołaniem poprawnym — i musi być WIDZIANE jako
    # nazwa, inaczej bramka milczy o całej tej klasie zapisu.
    assert module_names(_all_blocks()["6.D27"]) == ["test_report_claims"], (
        "skan przestał widzieć nazwę BEZ rozszerzenia w zamrożonym bloku 6.D27 — "
        "widzi tam: %s" % module_names(_all_blocks()["6.D27"]))

    # Kotwica 2: nazwa z ogonem `;` z łańcucha `cmd; cmd`, oraz `|` w tym samym
    # bloku, które nazwą modułu NIE jest. Bez drugiej połowy „widzi jedną" byłoby
    # prawdą także dla skanu biorącego każdy token po `test_all.py`.
    assert module_names(_all_blocks()["6.D44"]) == ["test_ci_workflows.py"], (
        "skan przestał widzieć nazwę z ogonem `;` w zamrożonym bloku 6.D44 — "
        "widzi tam: %s" % module_names(_all_blocks()["6.D44"]))
    assert module_names(_all_blocks()["6.D26"]) == ["test_suite_runtime_budget"], (
        "blok 6.D26 ma po `test_all.py` i nazwę modułu, i `|`; skan ma widzieć "
        "wyłącznie tę pierwszą, a widzi: %s" % module_names(_all_blocks()["6.D26"]))


# --- 6.D146: adresy w blokach WYKONANYCH -----------------------------------------

#: Bloki wykonane i wywołania modułu w ich polu „Weryfikacja". Zmierzone 11.09.2026:
#: **216** bloków wykonanych z 228, **92** wywołania w **90** blokach, wszystkie
#: modułów ISTNIEJĄCYCH. Progi KW, nie równości: liczba bloków rośnie z każdą
#: domkniętą pozycją, ale zepsuty czytnik daje zero i zielono.
MIN_BLOKOW_WYKONANYCH = 200
MIN_WYWOLAN_W_WYKONANYCH = 80

#: Kandydaci na zły adres wg reguły z pola „Wyjście" 6.D146 — nazwa modułu wołanego
#: w „Weryfikacji" NIE pada w prozie bloku. **Przeczytane po kolei 11.09.2026 i ani
#: jeden nie okazał się złym adresem.** Wpisane tutaj, żeby wiadomo było, które
#: sprawdzono, a nie żeby stanowiły zapadkę — patrz
#: `test_kandydaci_na_zly_adres_sa_przeczytani_i_zapisani`.
#:
#: Powód, dla którego każdy przeszedł, jest w większości ten sam: proza nazywa bramkę
#: PO TYM, CO ROBI („bramka liczy przyspieszenie rozruchu z modelu"), a nie po nazwie
#: pliku. Dwa przypadki — 6.D86 i 6.D89 — stoją tu wręcz dlatego, że ich adres ZOSTAŁ
#: JUŻ POPRAWIONY, a poprawiona nazwa w starej prozie siłą rzeczy nie pada.
SPRAWDZONE_RECZNIE = {
    ("6.D36", "test_mutation_sweep.py"): "trzy obcięcia hexdigest, o które blok pyta, leżą w `mutation_sweep.py`",
    ("6.D86", "test_reference_snapshot.py"): "adres POPRAWIONY 10.09.2026; stara proza nie zna nowej nazwy",
    ("6.D89", "test_provenance_classes.py"): "adres POPRAWIONY 10.09.2026; jak wyżej",
    ("6.D90", "test_mutation_sweep.py"): "blok jest o `mutation_sweep.py` brudzącym `data/`",
    ("6.D91", "test_validate_axis.py"): "blok jest o kontroli osi; moduł testuje `validate_axis.py`",
    ("6.D119", "test_dimension_audit.py"): "pole „Oczekiwane\" opisuje audyt `DESIGN_*` wobec `docs/21`",
    ("6.D120", "test_vertical_profile.py"): "blok jest o cząstkowym profilu pionowym, a moduł trzyma bramkę na czytnik tego profilu",
    ("6.D127", "test_assertion_gate.py"): "pole „Oczekiwane\" ŻĄDA, żeby bramka stanęła w module mierzącym asercje",
    ("6.D136", "test_bytecode_staleness.py"): "moduł powstał w tej pozycji i nie mógł paść w prozie napisanej wcześniej",
    ("6.D145", "test_csharp_assertions.py"): "moduł rozszerzony W TEJ pozycji",
}


def bloki_wykonane():
    """Bloki, które NIE są w kolejce — czyli te, których skan pól nie czyta."""
    otwarte = set(_open_blocks())
    return {n: b for n, b in _all_blocks().items() if n not in otwarte}


def proza_bloku(body):
    """Treść bloku bez bloków ogrodzonych — nazwa w płotku nie jest jej wzmianką."""
    return re.sub(r"```.*?```", " ", body, flags=re.S)


def adresy_w_wykonanych():
    """`[(numer, nazwa)]` — wywołania modułu w „Weryfikacji" bloków wykonanych."""
    out = []
    for numer, body in sorted(bloki_wykonane().items()):
        for nazwa in module_names(field_body(body, "Weryfikacja")):
            out.append((numer, nazwa))
    return out


def kandydaci_zlego_adresu():
    """`[(numer, nazwa)]` — nazwa wołana w „Weryfikacji", której proza nie wymienia.

    **To jest reguła z pola „Wyjście" 6.D146, wykonana — a nie przyjęta.** Pomiar
    z 11.09.2026 mówi, ile jest warta: dziesięciu kandydatów, zero złych adresów.
    Druga reguła, równie prawdopodobna (czy moduł NIESIE numer bloku), daje dziewięciu
    kandydatów, z czego wspólny jest **jeden**. Dwie reguły zgodne w jednym przypadku
    na dziewiętnaście nie mierzą tej samej rzeczy — i żadna nie mierzy adresu.
    """
    out = []
    for numer, body in sorted(bloki_wykonane().items()):
        proza = proza_bloku(body)
        for nazwa in sorted(set(module_names(field_body(body, "Weryfikacja")))):
            rdzen = nazwa[:-3] if nazwa.endswith(".py") else nazwa
            if rdzen not in proza:
                out.append((numer, nazwa))
    return out


def test_skan_blokow_wykonanych_widzi_to_co_zmierzono():
    """Progi KW — bez nich zepsuty czytnik daje zero kandydatów i zielono.

    Zero kandydatów czyta się jako „adresy są w porządku", a znaczy wtedy „czytnik
    nie widzi niczego". To ta sama rodzina, którą projekt tropi od 6.D27, i dlatego
    próg stoi na SAMYM SKANIE, nie na wyniku.
    """
    wykonane = bloki_wykonane()
    assert len(wykonane) >= MIN_BLOKOW_WYKONANYCH, (
        "bloków wykonanych jest %d przy progu %d — cięcie na otwarte i wykonane "
        "przestało działać, bo bloków tylko przybywa"
        % (len(wykonane), MIN_BLOKOW_WYKONANYCH))

    adresy = adresy_w_wykonanych()
    assert len(adresy) >= MIN_WYWOLAN_W_WYKONANYCH, (
        "skan widzi %d wywołań modułu w polach „Weryfikacja” bloków wykonanych "
        "przy progu %d — 11.09.2026 było ich 92"
        % (len(adresy), MIN_WYWOLAN_W_WYKONANYCH))

    # Kandydatów jest MNIEJ niż wywołań i WIĘCEJ niż nic — reguła, która zgłasza
    # wszystko albo nic, nie jest regułą i nie warto o niej pisać zdania.
    kandydaci = kandydaci_zlego_adresu()
    assert 0 < len(kandydaci) < len(adresy), (
        "reguła prozy zgłasza %d kandydatów na %d wywołań — przy zerze albo przy "
        "komplecie nie odsiewa niczego" % (len(kandydaci), len(adresy)))


def test_kandydaci_na_zly_adres_sa_przeczytani_i_zapisani():
    """Każdy kandydat z 11.09.2026 ma zapisany wynik CZYTANIA — 6.D146.

    **Lista nie jest zapadką i to jest wybór.** Kandydat pojawia się za każdym razem,
    gdy proza nazywa bramkę po tym, co robi, zamiast po nazwie pliku — czyli często
    i bez związku z usterką. Zapadka na tej liczbie byłaby podatkiem od każdego
    nowego bloku, płaconym za sygnał o zmierzonej precyzji **zero**.
    Zapisane jest więc co innego: KTÓRE dziesięć przeczytano i z jakim wynikiem.

    Test pilnuje, żeby ten zapis nie zaczął opisywać bloków, których nie ma —
    a nie żeby lista kandydatów stała w miejscu.
    """
    wszystkie = _all_blocks()
    obce = sorted(n for n, _m in SPRAWDZONE_RECZNIE if n not in wszystkie)
    assert obce == [], (
        "zapis czytania wskazuje blok, którego w `docs/TASKS.md` nie ma: %s" % obce)

    bez_powodu = sorted(k for k, v in SPRAWDZONE_RECZNIE.items() if len(v) < 30)
    assert bez_powodu == [], (
        "wpis bez powodu — zapis ma mówić, DLACZEGO adres uznano za poprawny: %s"
        % bez_powodu)

    assert len(SPRAWDZONE_RECZNIE) == 10, (
        "przeczytanych jest %d, a pomiar z 11.09.2026 dał dziesięciu kandydatów; "
        "dopisanie wpisu wymaga przeczytania bloku, nie tylko dopisania wiersza"
        % len(SPRAWDZONE_RECZNIE))


def test_regula_prozy_nie_jest_tym_samym_co_regula_numeru():
    """Dwie reguły, jeden wspólny kandydat na dziewiętnaście — 6.D146.

    To jest rozstrzygnięcie pozycji, wykonane zamiast opisane: gdyby obie reguły
    mierzyły „zły adres", zgadzałyby się. Zgadzają się w jednym przypadku, więc
    mierzą coś innego — swoje własne konwencje pisania, a nie adres.
    """
    import io as _io

    proza = set(kandydaci_zlego_adresu())
    numer = set()
    for para in adresy_w_wykonanych():
        blok, nazwa = para
        sciezka = os.path.join(ROOT, "tools", "tests",
                               nazwa if nazwa.endswith(".py") else nazwa + ".py")
        if not os.path.isfile(sciezka):
            continue
        with _io.open(sciezka, encoding="utf-8") as uchwyt:
            if blok not in uchwyt.read():
                numer.add(para)

    assert proza and numer, (
        "jedna z reguł nie zgłasza nic — porównanie niżej mierzyłoby wtedy milczenie: "
        "proza %d, numer %d" % (len(proza), len(numer)))
    assert len(proza & numer) * 3 < len(proza | numer), (
        "reguły zaczęły się zgadzać (wspólnych %d na %d) — jeśli to zmiana świadoma, "
        "rozstrzygnięcie 6.D146 trzeba przeczytać jeszcze raz"
        % (len(proza & numer), len(proza | numer)))


def test_the_scan_sees_the_measured_number_of_module_names():
    """Próg KW dla trzeciego kształtu: zepsuty wzorzec daje zero i zielone wszystko."""
    seen = [name
            for body in _all_blocks().values()
            for field in FIELDS
            for name in module_names(field_body(body, field))]
    assert len(seen) >= MIN_MODULE_NAMES, (
        "wzorzec złapał %d nazw modułów, a 10.09.2026 było ich 66 (60 w dniu, "
        "w którym pozycja powstała) — spadek znaczy zepsuty wzorzec albo zepsute "
        "cięcie pola, nie posprzątane bloki" % len(seen))


def test_the_three_measured_module_names_light_the_gate_when_put_back():
    """Trzy nieistniejące nazwy, każda wstawiona z powrotem do bloku OTWARTEGO.

    Tego żąda pole „Skończone, gdy". Wszystkie trzy leżą dziś w blokach poprawionych,
    więc dzisiejsze drzewo o nich milczy — a to milczenie znaczy coś dopiero wtedy,
    gdy każda z nich, podłożona jako pole otwartego bloku, je przerywa.
    """
    plotek = "\n\n  ```bash\n  python3 tools/tests/test_all.py %s\n  ```\n"
    for nazwa in ("test_physics_reference.py", "test_glossary.py", "test_all_self.py"):
        zapalone = _zapala("Weryfikacja", plotek % nazwa)
        assert zapalone == ["moduł"], (
            "%s: zapalone kształty %s, spodziewany wyłącznie „moduł”"
            % (nazwa, zapalone or "żaden"))

    # Kierunek przeciwny — nic z poniższych zapalić się nie ma.
    for poprawne in (
        "test_backlog.py",          # moduł, który jest
        "test_report_claims",       # ten sam bez rozszerzenia — `_only_path` dokłada
    ):
        assert _zapala("Weryfikacja", plotek % poprawne) == [], (
            "poprawne wywołanie `%s` zapaliło bramkę: %s"
            % (poprawne, _zapala("Weryfikacja", plotek % poprawne)))

    # Argument, który nazwą modułu nie jest: potok, przekierowanie i opcja.
    for nie_nazwa in ("| tail -3", "2>&1 | tail -3", "--nie-ma-takiej"):
        assert module_names(plotek % nie_nazwa) == [], (
            "`%s` nie jest nazwą modułu, a skan czyta ją jako: %s"
            % (nie_nazwa, module_names(plotek % nie_nazwa)))

    # I PROZA — z pełnym wywołaniem w środku, bo tylko taka odróżnia zawężenie do
    # płotków od jego braku. Pierwsza wersja tej kontroli stawiała tu zdanie bez
    # `test_all.py` i była zielona TAKŻE po zdjęciu zawężenia (zmierzone jako KN-5):
    # pilnowała więc czegoś, czego nie sprawdzała.
    #
    # Zdanie jest BEZ grawisów i to też jest zmierzone: w wersji z grawisami
    # kontrola była zielona po zdjęciu zawężenia (KN-5), bo `(\\S+)` bierze wtedy
    # `test_nie_ma_takiego.py\u0060,` razem z grawisem i przecinkiem, a taki token
    # odrzuca `MODULE_ARGUMENT`. Cichła więc z INNEGO powodu niż ten, którego
    # miała pilnować — i pilnowała czegoś, czego nie sprawdzała.
    zdanie = ("- **Weryfikacja:** dawniej trzeba było uruchomić "
              "python3 tools/tests/test_all.py test_nie_ma_takiego.py i porównać\n")
    assert missing_modules({"6.D999": zdanie}) == [], (
        "cytat wywołania w prozie został wzięty za wywołanie: %s"
        % missing_modules({"6.D999": zdanie}))

    # Ta sama nazwa W PŁOTKU zapala — inaczej wiersz wyżej byłby prawdą także dla
    # skanu, który nie widzi niczego.
    assert missing_modules({"6.D999": _mutacja("Weryfikacja",
                                               plotek % "test_nie_ma_takiego.py")}), (
        "ta sama nazwa w płotku też jest cicha — skan nie widzi nic")


def test_the_module_shape_reads_the_name_the_way_the_runner_does():
    """Kontrola przyrządu: werdykt rozstrzyga `test_all._only_path`, nie druga reguła.

    Gdyby bramka trzymała własną regułę rozwiązywania nazw, mogłaby przyjąć nazwę,
    której zestaw odmówi — albo zgłosić nazwę, którą zestaw przyjmuje. Oba kierunki
    są tu sprawdzone na tym samym module.
    """
    import test_all

    assert test_all._only_path("test_backlog").endswith("test_backlog.py")
    assert test_all._only_path("test_backlog.py").endswith("test_backlog.py")
    try:
        test_all._only_path("test_nie_ma_takiego")
    except ValueError:
        pass
    else:
        raise AssertionError("`_only_path` przyjął moduł, którego nie ma")


# --- 6.D237: argument DRUGI i dalszy, czyli ogon wywolania ------------------------

#: Ile nazw modulu przychodzi z DALSZEGO niz pierwszy argumentu `test_all.py`, na
#: blokach WSZYSTKICH. Zmierzone 16.09.2026 na `e420f14`: **19** — szesnascie w polach
#: „Weryfikacja" blokow WYKONANYCH (6.D138, 6.D144, 6.D151, 6.D162, 6.D163, 6.D192,
#: 6.D193, 6.D194, 6.D203, 6.D204, 6.D205, 6.D206, 6.D207, 6.D209, 6.D216, 6.D218)
#: i trzy w blokach, ktore 16.09.2026 byly jeszcze OTWARTE (6.D228 dwa, 6.D230 jeden).
#: **Na dzis wszystkie dziewietnascie stoi w blokach WYKONANYCH** — scalenie #644
#: i #646 przeniosla tamte trzy; POPULACJA SIE NIE ZMIENILA, bo prog liczy sie na
#: blokach WSZYSTKICH i to jest wlasnie powod, dla ktorego tak jest liczony.
#: Prog stoi NIZEJ, na 15, zeby nie ruszac go przy kazdej scalonej pozycji.
#:
#: **Prog jest KW, a nie rownoscia, i liczony na blokach WSZYSTKICH** — te same dwa
#: wybory, co przy `MIN_MODULE_NAMES` i z tych samych powodow: bloki wykonane sa
#: zamrozone, wiec liczba na nich tylko rosnie, a na blokach otwartych malalaby od
#: SPRZATANIA kolejki. Broni przed jedna rzecza i tylko przed nia: cichym powrotem
#: `MODULE_CALL` do postaci jednoargumentowej, po ktorym ta liczba spada do ZERA,
#: a zero czyta sie jako „takich wywolan nie ma" (6.D27).
MIN_NAZW_Z_DALSZEGO_ARGUMENTU = 15


def nazwy_z_dalszego_argumentu(blocks=None):
    """`[(numer, pole, nazwa)]` dla nazw stojacych na DRUGIM i dalszym miejscu."""
    out = []
    for numer, body in (blocks if blocks is not None else _all_blocks()).items():
        for pole in FIELDS:
            for line in _code_lines(field_body(body, pole) or ""):
                for call in MODULE_CALL.finditer(line):
                    for token in _rozbior_ogona(call.group(1))[1:]:
                        out.append((numer, pole, token))
    return out


def test_skan_widzi_zmierzona_liczbe_nazw_z_DALSZEGO_argumentu():
    """Prog KW na sam SKAN, nie na jego werdykt — 6.D237.

    Bez niego powrot `MODULE_CALL` do jednego argumentu daje tu zero, a zero czyta
    sie jako „wywolan wieloargumentowych nie ma" — czyli dokladnie jako zdanie,
    ktore ta pozycja OBALILA pomiarem (`test_all.py test_crs.py test_lod.py` daje
    82/82 przeszlo i 2 modulow).
    """
    widziane = nazwy_z_dalszego_argumentu()
    assert len(widziane) >= MIN_NAZW_Z_DALSZEGO_ARGUMENTU, (
        "skan widzi %d nazw modulu na drugim i dalszym miejscu wywolania przy progu "
        "%d — 16.09.2026 bylo ich 19; spadek znaczy zwezony `MODULE_CALL` albo "
        "zepsute ciecie pola, a nie posprzatane bloki"
        % (len(widziane), MIN_NAZW_Z_DALSZEGO_ARGUMENTU))


def test_literowka_na_DRUGIM_miejscu_wywolania_zapala_bramke():
    """Kontrola przyrzadu na wejsciu syntetycznym — 6.D237, wg reguly 6.D159.

    **Dziura jest REALNA, ale PUSTA i to jest zmierzone.** Nazw modulu BEZ
    rozszerzenia, stojacych na drugim lub dalszym miejscu, jest dzis w `docs/TASKS.md`
    **zero** — na 19 wystapien dalszego argumentu wszystkie 19 konczy sie na `.py`.
    Nazwe Z rozszerzeniem lapie od 6.D187 skan golych nazw, niezaleznie od pozycji;
    bez rozszerzenia nie lapie jej nic i to jest ta polowa, ktora ta pozycja zamyka.
    Bramka o pustym zbiorze nie odrozniaja „nie ma czego lapac" od „nie lapie", wiec
    rozstrzyga PODSTAWIENIE, a nie cisza drzewa.
    """
    plotek = "\n\n  ```bash\n  python3 tools/tests/test_all.py %s\n  ```\n"

    # Ksztalt, dla ktorego ta pozycja powstala: literowka BEZ rozszerzenia, na drugim
    # miejscu. Do 16.09.2026 przechodzila bez sladu przez CALY zestaw.
    assert _zapala("Weryfikacja", plotek % "test_crs.py test_nie_ma_takiego") == [
        "moduł"], (
        "literowka bez rozszerzenia na DRUGIM miejscu nie zapala niczego — to jest "
        "dokladnie stan sprzed 6.D237: %s"
        % _zapala("Weryfikacja", plotek % "test_crs.py test_nie_ma_takiego"))

    # Trzecie miejsce tez, bo „drugie" nie ma byc przypadkiem wzorca liczacego do dwoch.
    assert missing_modules({"6.D999": _mutacja(
        "Weryfikacja", plotek % "test_crs.py test_lod.py test_nie_ma_takiego")}) == [
        ("6.D999", "Weryfikacja", "test_nie_ma_takiego")], (
        "literowka na TRZECIM miejscu nie zostala zgloszona albo zgloszono cos "
        "innego: %s" % missing_modules({"6.D999": _mutacja(
            "Weryfikacja", plotek % "test_crs.py test_lod.py test_nie_ma_takiego")}))

    # Kierunek przeciwny — poprawne wywolanie dwoch i trzech modulow milczy.
    for poprawne in ("test_crs.py test_lod.py",
                     "test_crs.py test_lod.py test_backlog.py",
                     "test_crs.py test_report_claims"):
        assert _zapala("Weryfikacja", plotek % poprawne) == [], (
            "poprawne wywolanie `%s` zapalilo bramke: %s"
            % (poprawne, _zapala("Weryfikacja", plotek % poprawne)))


def test_ogon_wywolania_KONCZY_SIE_na_pierwszym_tokenie_ktory_nazwa_nie_jest():
    """Trzy POPRAWNE polecenia, na ktorych postac naiwna zapalalaby sie falszywie.

    **Postac naiwna nie jest tu strachem na wrobla, tylko zmierzona alternatywa.**
    Ogon czytany do konca wiersza, bez zatrzymania, dawal 16.09.2026 na `docs/TASKS.md`
    **osiem** falszywych zgloszen (bez filtru `MODULE_ARGUMENT` — **siedemnascie**),
    postac prefiksowa — **zero**. Wszystkie osiem stoi w poleceniach POPRAWNYCH, wiec
    bramka z ta postacia zostalaby wylaczona, a nie naprawiona (6.D27).

    Trzy wiersze nizej sa przepisane z `docs/TASKS.md` co do znaku: potok (6.D26),
    srednik (6.D44, 6.D45, 6.D63) i `&&` (6.D234).
    """
    wiersze = {
        "for i in 1 2 3; do python3 tools/tests/test_all.py | grep RAZEM; done":
            [],
        "python3 tools/tests/test_all.py test_ci_workflows.py; echo \"kod: $?\"":
            ["test_ci_workflows.py"],
        "python3 tools/tests/test_all.py && dotnet test tests/Sim.Tests":
            [],
    }
    for wiersz, oczekiwane in wiersze.items():
        plotek = "\n\n  ```bash\n  %s\n  ```\n" % wiersz
        assert module_names(plotek) == oczekiwane, (
            "ogon wiersza `%s` przeczytany jako %s, a nazwami modulu sa %s — "
            "rozbior przestal sie zatrzymywac na tokenie, ktory nazwa nie jest"
            % (wiersz, module_names(plotek), oczekiwane))
        assert _zapala("Weryfikacja", plotek) == [], (
            "poprawne polecenie `%s` zapalilo bramke: %s"
            % (wiersz, _zapala("Weryfikacja", plotek)))


def test_the_two_new_shapes_catch_the_measured_cases_and_leave_the_prose_alone():
    """Kontrola negatywna dla obu kształtów, WYKONANA na zmierzonych przypadkach.

    Cztery zdania prozy niżej to te, na których pierwsze wersje obu wzorców się
    wywracały. Każde zostało zmierzone, nie wymyślone.
    """
    # KATALOG — zmierzony przypadek 6.A21 wstawiony do bloku otwartego.
    blok = {"6.D999": "- **Wyjście:** wzorce w `tools/ci/golden/`\n"}
    assert missing_directories(blok) == [("6.D999", "Wyjście", "tools/ci/golden/")]
    assert missing_directories({"6.D999": "- **Wyjście:** `tools/blender/`\n"}) == []
    # …a proza z ukośnikiem katalogiem nie jest.
    assert directories_in("stosunek CPU/ściana") == []
    assert directories_in("`bin/` i `obj/` to wytwory budowania") == []
    assert directories_in("`$DOTNET_ROOT/host/fxr/` po instalacji") == []
    assert directories_in("wzorce w `tools/ci/golden/`") == ["tools/ci/golden/"]

    # OPCJA — zmierzony przypadek 6.B43 wstawiony do bloku otwartego.
    scena = {"6.D999": '- **Weryfikacja:**\n\n  ```bash\n'
                       '  $GODOT_BIN --path src/Game -- --shot --view=chase '
                       '--at-m=96 --out=build/chase-96.png\n  ```\n'}
    nieznane = [o for _n, _f, _t, o in unknown_options(scena)]
    assert nieznane == ["--at-m", "--out"], nieznane
    # `--shot` i `--view` scena ZNA, więc nie mogą się tu pojawić — bez tej asercji
    # „łapie dwie" byłoby prawdą także dla bramki zgłaszającej wszystko.
    assert "--shot" not in nieznane and "--view" not in nieznane

    narzedzie = {"6.D999": '- **Weryfikacja:**\n\n  ```bash\n'
                           '  python3 tools/tests/mutation_sweep.py --only x --nie-ma-takiej\n'
                           '  ```\n'}
    assert [o for _n, _f, _t, o in unknown_options(narzedzie)] == ["--nie-ma-takiej"]
    # PROZA: wywołanie narzędzia WPLECIONE W ZDANIE nie jest komendą do wykonania.
    # Kształt nie jest wymyślony — pole „Wyjście" bloku 6.A26 niesie dziś `--path
    # src/Game` w środku zdania. Zmierzone na całym `docs/TASKS.md`: **200** wystąpień
    # wywołania narzędzia w polach, z tego **199** w blokach ogrodzonych i **1** w
    # prozie, właśnie to. Nazwa opcji jest tu DOPISANA do prawdziwego zdania, bo samo
    # zdanie 6.A26 żadnej za sobą nie ma — i dlatego zdjęcie ogrodzenia z dzisiejszej
    # treści nie zmienia ani jednego zgłoszenia (kontrola negatywna KN-2, opisana
    # w `reports/6d73-katalog-i-opcja-w-polu.md`). Ogrodzenie pilnuje KSZTAŁTU, który
    # w drzewie jest, a nie trafienia, którego dziś nie ma.
    proza = {"6.D999": "- **Wyjście:** odmawia, gdy w komendzie `--path src/Game` "
                       "stanie `--nie-ma-takiej`, i wypisuje powód\n"}
    assert unknown_options(proza) == []
    # OPCJA OPISANA A NIEZADEKLAROWANA — powód, dla którego lista opcji idzie
    # z drzewa składni, a nie z grepa po napisie `--nazwa`. Zmierzone na 15 narzędziach
    # wołanych dziś z pól: w **pięciu** grep widzi więcej niż argparse, bo łapie
    # komentarze, teksty pomocy i flagi CUDZYCH poleceń (`--quiet` gita w
    # `mutation_sweep.py`). `--metrics` stoi w treści `assert_shot_metadata.py`,
    # a `add_argument` go nie dostaje — więc wariant grepowy przyjmuje tę komendę
    # w milczeniu, a ten wiersz go czerwieni (kontrola negatywna KN-3).
    opisana = {"6.D999": '- **Weryfikacja:**\n\n  ```bash\n'
                         '  python3 tools/ci/assert_shot_metadata.py --metrics x\n  ```\n'}
    assert [o for _n, _f, _t, o in unknown_options(opisana)] == ["--metrics"]

    # …a ta sama treść w bloku ogrodzonym jest już komendą i zgłoszenie daje.
    komenda = {"6.D999": '- **Wyjście:**\n\n  ```bash\n'
                         '  $GODOT_BIN --path src/Game -- --nie-ma-takiej\n  ```\n'}
    assert [o for _n, _f, _t, o in unknown_options(komenda)] == ["--nie-ma-takiej"]


SZESC_PRZYPADKOW = (
    # (nazwa, pole, treść pola, kształt, który ma się zapalić)
    ("6.D59 · ścieżka z wiodącą kropką", "Wejście",
     "`.github/workflows/nie-ma-takiego.yml`", "ścieżka"),
    ("6.A21 · katalog w polu „Wejście\u201d", "Wejście",
     "`tools/ci/golden/` (wzorce śladu)", "katalog"),
    ("6.A21 · ten sam katalog w komendzie", "Weryfikacja",
     "\n\n  ```bash\n  git diff --stat tools/ci/golden/\n  ```\n", "katalog"),
    ("6.B43 · `--at-m`", "Weryfikacja",
     "\n\n  ```bash\n  $GODOT_BIN --path src/Game -- --shot --at-m=96\n  ```\n",
     "opcja"),
    ("6.B43 · `--out`", "Weryfikacja",
     "\n\n  ```bash\n  $GODOT_BIN --path src/Game -- --shot --out=build/x.png\n  ```\n",
     "opcja"),
    ("6.D64 · moduł w złym katalogu", "Wejście",
     "`tools/track/provenance.py` (pisarz nastaw)", "ścieżka"),
)


def _mutacja(field, content):
    """Blok otwarty o numerze `6.D999`, z jednym polem wypełnionym mutacją."""
    return "##### 6.D999 · Blok wstawiony na czas kontroli\n\n- **%s:** %s\n" % (
        field, content)


def _zapala(field, content):
    """Które kształty zapala ta mutacja: `ścieżka`, `katalog`, `opcja`."""
    tekst = _mutacja(field, content)
    blocks = {"6.D999": tekst}
    zapalone = []
    if reported(scan(tekst)):
        zapalone.append("ścieżka")
    if missing_directories(blocks):
        zapalone.append("katalog")
    if unknown_options(blocks):
        zapalone.append("opcja")
    if missing_modules(blocks):
        zapalone.append("moduł")
    return zapalone


def test_each_of_the_six_measured_cases_lights_a_gate_when_put_back():
    """Sześć przypadków z pola „Skąd" pozycji 6.D73, każdy wstawiony z powrotem.

    **Dlaczego mutacja, a nie pomiar dzisiejszego drzewa.** Wszystkie sześć leży
    w blokach WYKONANYCH, a ich poprawianie pozycja 6.D73 wyklucza wprost w polu
    „Poza zakresem" („ich zapis jest historyczny"). Dwie bramki wyżej chodzą więc po
    blokach OTWARTYCH i na dzisiejszej kolejce milczą — a ta cisza znaczy coś dopiero
    wtedy, gdy każdy z sześciu, podłożony jako pole otwartego bloku, ją przerywa.

    **Trzy kształty, a nie jeden**, i podział jest treścią: dwa z sześciu łapie skan
    ścieżek, który istniał wcześniej (i to jest zmierzony wynik — 6.D59 poprawiło
    `PATH_TOKEN` także tutaj, więc wiodąca kropka wchodzi), a cztery nie miały
    czym zostać złapane do dziś.
    """
    zmierzone = {}
    for nazwa, field, content, oczekiwany in SZESC_PRZYPADKOW:
        zapalone = _zapala(field, content)
        zmierzone[nazwa] = zapalone
        assert oczekiwany in zapalone, (
            '%s: mutacja nie zapaliła kształtu „%s” — zapalone: %s'
            % (nazwa, oczekiwany, zapalone or "żaden"))
    # Rozkład na kształty jest przybity, a nie tylko „coś się zapaliło": bramka
    # zgłaszająca wszystko przeszłaby pętlę wyżej i nie przeszłaby tego wiersza.
    assert [len(v) for v in zmierzone.values()] == [1, 1, 1, 1, 1, 1], zmierzone
    # I kierunek przeciwny: poprawne pola tych samych sześciu bloków są ciche.
    assert _zapala("Wejście", "`.github/workflows/godot-first-run.yml`") == []
    assert _zapala("Wejście", "`tests/data/golden-trace/` (wzorce śladu)") == []
    assert _zapala("Wejście", "`tools/data/provenance.py` (pisarz nastaw)") == []
    assert _zapala(
        "Weryfikacja",
        "\n\n  ```bash\n  $GODOT_BIN --path src/Game -- --shot=build/x.png "
        "--at-chainage=96\n  ```\n") == []


def test_the_scan_sees_the_measured_number_of_paths_in_every_field():
    """Próg KW: zepsuty wzorzec albo zepsute cięcie pola dają zero i zielone wszystko.

    Progi są PER POLE, bo pole „Wyjście" to 45 ścieżek na 678 — jeden łączny próg
    przeżyłby literówkę w jego cięciu i nie drgnąłby.
    """
    hits = scan()
    for field, floor in MIN_PATHS.items():
        seen = len([hit for hit in hits if hit["field"] == field])
        assert seen >= floor, (
            'wzorzec złapał %d ścieżek w polu „%s", a 07.09.2026 było ich %d — '
            'spadek znaczy zepsuty wzorzec albo zepsute cięcie pola, '
            'nie posprzątane bloki' % (seen, field, floor))
    blocks = tb.detail_sections(_tasks())
    assert len(blocks) >= tb.MINIMUM_DETAIL_BLOCKS, (
        "bramka przeszła %d bloków przy zapadce %d — skan przestał czytać plik"
        % (len(blocks), tb.MINIMUM_DETAIL_BLOCKS))


def test_no_input_field_names_a_file_outside_the_tree():
    """Szczebel 1: pole „Wejście" jest ADRESEM, pod który idzie następny agent.

    Wyjątku dla tego pola nie ma i nie da się go dopisać po cichu —
    `test_the_exception_list_stays_closed` sprawdza to na kluczach `EXCEPTIONS`.
    """
    bad = [_where(key) for key in reported() if key[1] == HARD_FIELD]
    assert bad == [], (
        'pole „Wejście" nazywa plik, którego w drzewie nie ma: %s' % bad)


def test_no_verification_field_names_a_file_outside_the_tree_and_outside_its_own_output():
    """Szczebel 2: komenda wolno wymienić plik nieistniejący tylko wtedy, gdy go TWORZY.

    Rozróżnienie idzie po polu „Wyjście" TEGO SAMEGO bloku (6.B44) albo po wpisie
    na liście wyjątków z powodem (6.B39). Ścieżka `data/keys/L1_A-manual.json` z 6.A30
    nie spełniała ani jednego z tych dwóch warunków i to jest cała różnica.
    """
    bad = [_where(key) for key in reported() if key[1] == "Weryfikacja"]
    assert bad == [], (
        'pole „Weryfikacja" woła plik, którego nie ma i którego pozycja nie tworzy: %s'
        % bad)


def test_the_same_block_output_rule_is_the_one_actually_carrying_the_exceptions():
    """Szczebel 3 nie jest pustym przebiegiem — reguła „z własnego Wyjścia" JEST używana.

    Bez tej asercji cała konstrukcja mogłaby stać na liście wyjątków, a reguła
    z „Wyjścia" bloku byłaby martwym kodem, którego nikt by nie zauważył.
    """
    hits = scan()
    carried = sorted({_key(hit) for hit in hits
                      if not hit["exists"] and hit["field"] != HARD_FIELD
                      and hit["in_own_output"]})

    # Reguła jest ŻYWA, gdy jej ZDJĘCIE zmienia zbiór zgłoszeń. To dowód, który nie
    # zależy od liczby usprawiedliwionych ścieżek — a zależeć nie może, bo ta liczba
    # SPADA za każdym razem, gdy ktoś wykona pozycję i obiecany plik powstanie.
    #
    # **Asercja jest PRZEPISANA, a nie poluzowana — 07.09.2026.** Poprzednia wersja
    # żądała `len(carried) >= 3` i uzasadniała to pomiarem z tego samego dnia. Próg
    # zapalił się przy 6.B44, bo `tools/track/vertical_profile.py` i
    # `tools/tests/test_vertical_profile.py` PRZESTAŁY być wyjątkami — powstały.
    # Próg, który wymaga, żeby pozycje NIE były wykonywane, mierzy kolejkę, nie regułę.
    # Nowa asercja sprawdza WIĘCEJ: nie tylko że reguła kogoś usprawiedliwia, ale że
    # bez niej zbiór zgłoszeń faktycznie rośnie o dokładnie te ścieżki.
    assert carried, (
        "reguła „plik z własnego Wyjścia\" nie usprawiedliwia dziś ANI JEDNEJ ścieżki "
        "— jest martwym kodem")
    bez_reguly = sorted({_key(hit) for hit in hits
                         if not hit["exists"] and _key(hit) not in EXCEPTIONS})
    z_regula = reported(hits)
    dolozone = sorted(set(bez_reguly) - set(z_regula))
    assert dolozone, (
        "zdjęcie reguły nie dołożyło ani jednego zgłoszenia, choć usprawiedliwia %d "
        "ścieżek — jedna z tych dwóch rzeczy jest policzona źle: %s"
        % (len(carried), carried))
    poza_regula = [k for k in dolozone if k not in carried]
    assert not poza_regula, (
        "zdjęcie reguły dołożyło ścieżki, których ona nie usprawiedliwia: %s" % poza_regula)
    for key in carried:
        assert key not in EXCEPTIONS, (
            "%s jest usprawiedliwiona regułą z „Wyjścia\" i JESZCZE stoi na liście "
            "wyjątków — wpis jest zbędny" % _where(key))


def test_removing_the_field_distinction_moves_the_reported_set():
    """KU: bez tego testu „wyjątki" mogłyby milczeć, bo nic ich nie dotyczy.

    Zdjęcie rozróżnienia pól musi PRZENIEŚĆ zbiór zgłoszeń, i to jest jedyny dowód,
    że rozróżnienie cokolwiek mierzy. Zmierzone 07.09.2026: na drzewie PRZED poprawką
    trzech ścieżek 3 -> 7, na drzewie po poprawce 0 -> 4.

    Liczba 4 NIE jest tu wpisana jako asercja i to jest wybór: `tools/track/vertical_profile.py`
    (6.B44) i `tools/tests/test_test_track_fixture.py` (6.B8) mają kiedyś powstać, a
    wtedy zbiór luźny zejdzie do 2 i bramka na dokładnej liczbie zapaliłaby się za
    WYKONANĄ pracę — dokładnie to, co 6.D27 nazwało powodem wyłączania bramek. Liczby
    per rodzaj wyjątku pilnuje test na wejściu syntetycznym niżej.
    """
    hits = scan()
    strict = reported(hits, distinguish=True)
    loose = reported(hits, distinguish=False)
    assert strict == [], [_where(key) for key in strict]
    assert loose, (
        "bez rozróżnienia pól bramka też nie zgłasza niczego — nie ma czego "
        "porównywać, więc wyjątki nie są mierzone, tylko zadeklarowane")
    assert set(strict) < set(loose), (sorted(strict), sorted(loose))
    # Każde zgłoszenie zbioru luźnego jest ścieżką POPRAWNĄ — to jest kontrola
    # ujemna wprost: bramka rozróżniająca pola nie zgłasza żadnej z nich.
    for key in loose:
        assert key[1] != HARD_FIELD, (
            "%s jest w polu „Wejście\" i zostałaby zgłoszona także przez bramkę "
            "rozróżniającą — zbiór luźny miał zawierać wyłącznie ścieżki poprawne"
            % _where(key))


def test_the_three_kinds_of_exception_are_told_apart_on_synthetic_input():
    """KD i granice reguły — na blokach napisanych tutaj, bez dotykania `docs/TASKS.md`.

    Sześć przypadków, bo sześć różnych rzeczy musi wyjść osobno. Na dzisiejszym drzewie
    bramka zgłasza ZERO, więc sam jej zielony kolor nie dowodzi niczego: gdyby
    `reported()` zwracało pustą listę zawsze, wszystkie testy wyżej też byłyby zielone.

    **Atrapa jest PRZEPISANA, a nie dopisana obok — 07.09.2026.** Pierwsza wersja
    używała `tools/track/vertical_profile.py` jako przykładu pliku nieistniejącego,
    a ten plik był **obiecany w polu „Wyjście" pozycji 6.B44** — czyli atrapa zależała
    od tego, że pozycja z kolejki NIE została wykonana. Gdy 6.B44 powstało, asercja
    granicy reguły (przypadek 4) zaczęła padać, choć bramka działa poprawnie. Nazwa
    `ATRAPA_ktorej_nie_bedzie.py` nie jest niczyim wyjściem i nikt jej nie stworzy,
    więc próbka mierzy regułę, a nie stan kolejki.
    """
    probka = "\n".join([
        "##### 9.Z1 · literówka w polu Wejście",
        "- **Wejście:** `tools/track/profile_scan.py`",
        "- **Wyjście:** nic",
        "- **Weryfikacja:** nic",
        "",
        "##### 9.Z2 · plik do wytworzenia i komenda, która go tworzy",
        "- **Wejście:** `tools/tests/test_all.py`",
        "- **Wyjście:** `tools/track/ATRAPA_ktorej_nie_bedzie.py`",
        "- **Weryfikacja:**",
        "  ```bash",
        "  python3 tools/track/ATRAPA_ktorej_nie_bedzie.py --out build/x.json",
        "  ```",
        "",
        "##### 9.Z3 · komenda woła plik, którego nikt tu nie tworzy",
        "- **Wejście:** `tools/tests/test_all.py`",
        "- **Wyjście:** nic",
        "- **Weryfikacja:** `python3 tools/track/ATRAPA_ktorej_nie_bedzie.py`",
        "",
        "##### 9.Z4 · ten sam plik, ale z wpisem na liście wyjątków",
        "- **Wejście:** `tools/tests/test_all.py`",
        "- **Wyjście:** nic",
        "- **Weryfikacja:** `python3 tools/nie-ma-takiego-pliku.py`",
    ])
    hits = scan(text=probka)
    keys = {_key(hit) for hit in hits}

    # 1. KD: literówka w polu „Wejście" jest zgłoszona, z blokiem i ze ścieżką.
    zgloszone = reported(hits)
    assert ("9.Z1", "Wejście", "tools/track/profile_scan.py") in zgloszone, zgloszone
    assert _where(("9.Z1", "Wejście", "tools/track/profile_scan.py")) == (
        '9.Z1 „Wejście": tools/track/profile_scan.py')

    # 2. rodzaj (a): plik z pola „Wyjście" nie jest zgłoszony.
    assert ("9.Z2", "Wyjście", "tools/track/ATRAPA_ktorej_nie_bedzie.py") in keys
    assert ("9.Z2", "Wyjście", "tools/track/ATRAPA_ktorej_nie_bedzie.py") not in zgloszone

    # 3. rodzaj (b): ten sam plik w komendzie, KTÓRA GO TWORZY — nie jest zgłoszony.
    assert ("9.Z2", "Weryfikacja", "tools/track/ATRAPA_ktorej_nie_bedzie.py") not in zgloszone

    # 4. GRANICA reguły „tego samego bloku": ta sama ścieżka w komendzie bloku, który
    #    jej NIE deklaruje jako wyjścia, JEST zgłoszona. Bez tej asercji reguła
    #    mogłaby patrzeć na „Wyjścia" wszystkich bloków naraz i nikt by nie zauważył.
    assert ("9.Z3", "Weryfikacja", "tools/track/ATRAPA_ktorej_nie_bedzie.py") in zgloszone

    # 5. rodzaj (c): wpis na liście wyjątków zdejmuje zgłoszenie — pod warunkiem, że
    #    klucz zgadza się co do bloku i pola. Tu blok jest inny (9.Z4, nie 6.B39),
    #    więc wyjątek NIE działa: wyjątek jest na wystąpienie, nie na nazwę pliku.
    assert ("9.Z4", "Weryfikacja", "tools/nie-ma-takiego-pliku.py") in zgloszone
    z_wyjatkiem = {("9.Z4", "Weryfikacja", "tools/nie-ma-takiego-pliku.py"): "x" * 41}
    ratowane = [hit for hit in hits
                if _key(hit) == ("9.Z4", "Weryfikacja", "tools/nie-ma-takiego-pliku.py")]
    assert len(ratowane) == 1
    globalny = EXCEPTIONS
    try:
        globals()["EXCEPTIONS"] = z_wyjatkiem
        assert ("9.Z4", "Weryfikacja", "tools/nie-ma-takiego-pliku.py") not in reported(hits)
        # 6. …i to samo podstawienie NIE ratuje pola „Wejście": szczebel 1 nie ma
        #    wyjątków, więc wpis na jego wystąpienie jest bezsilny.
        globals()["EXCEPTIONS"] = {
            ("9.Z1", "Wejście", "tools/track/profile_scan.py"): "x" * 41}
        assert ("9.Z1", "Wejście", "tools/track/profile_scan.py") in reported(hits)
    finally:
        globals()["EXCEPTIONS"] = globalny
    assert EXCEPTIONS is globalny


def test_the_extension_alternation_is_ordered_longest_first():
    """KP: alternatywa w złej kolejności produkuje zgłoszenia z niczego.

    To jest pułapka, w którą wpadł pomiar poprzedzający tę bramkę, i dlatego ma
    kontrolę w obie strony: że dobry wzorzec bierze token do końca, i że zły wzorzec
    NAPRAWDĘ go ucina — inaczej „poprawka kolejności" byłaby twierdzeniem o niczym.
    """
    def found(line):
        return paths_in(line)

    # 1. Rozszerzenia będące przedrostkiem innych — token musi wejść CAŁY.
    assert found("`tests/Sim.Tests/Sim.Tests.csproj`") == ["tests/Sim.Tests/Sim.Tests.csproj"]
    assert found("`data/network/station-depths.csv`") == ["data/network/station-depths.csv"]
    assert found("`build/x/y.jsonl` i `reports/a.jsonl`") == ["reports/a.jsonl"]
    assert found("`src/Sim/Train/LineDrive.cs`") == ["src/Sim/Train/LineDrive.cs"]

    # 2. DOWÓD, że pułapka istnieje: alternatywa z `cs` i `json` przed dłuższymi,
    #    bez domknięcia, ucina token w środku i daje ścieżkę, której nie ma.
    zly = re.compile(r'([A-Za-z0-9_][A-Za-z0-9_./+-]*/[A-Za-z0-9_][A-Za-z0-9_.+-]*'
                     r'\.(?:py|cs|md|json|csv|csproj|jsonl))')
    assert zly.findall("tests/Sim.Tests/Sim.Tests.csproj") == ["tests/Sim.Tests/Sim.Tests.cs"]
    assert zly.findall("data/network/station-depths.csv") == ["data/network/station-depths.cs"]
    assert zly.findall("reports/a.jsonl") == ["reports/a.json"]
    for ucięty in ("tests/Sim.Tests/Sim.Tests.cs", "data/network/station-depths.cs",
                   "reports/a.json"):
        assert not os.path.exists(os.path.join(ROOT, ucięty)), ucięty

    # 3. Domknięcie działa też bez kolejności — ale jest OBOK niej, nie zamiast:
    #    poleganie na nawrotach silnika `re` jest poleganiem na szczególe implementacji.
    domkniety = re.compile(r'([A-Za-z0-9_][A-Za-z0-9_./+-]*/[A-Za-z0-9_][A-Za-z0-9_.+-]*'
                           r'\.(?:py|cs|md|json|csv|csproj|jsonl))(?![A-Za-z0-9])')
    assert domkniety.findall("tests/Sim.Tests/Sim.Tests.csproj") == [
        "tests/Sim.Tests/Sim.Tests.csproj"]


def test_the_pattern_does_not_take_prose_for_a_path():
    """Granica wzorca w drugą stronę: bramka, która łapie prozę, zamienia się w szum."""
    def found(line):
        return paths_in(line)

    # 1. Kwalifikowana nazwa w kodzie NIE jest ścieżką — brak ukośnika.
    assert found("`sweep.max_deviation`, `lod.lod_plan`, `Mutation.id`") == []
    # 2. Katalog z kropką w nazwie NIE jest plikiem: `tests/Sim.Tests`, `src/Sim.Runner`.
    assert found("`tests/Sim.Tests/` i `src/Sim.Runner/`") == []
    # 3. Wytwór przebiegu nie jest brakiem — reguła 8 zabrania go komitować.
    assert found("artefakt `build/t400/scene-line.log` i `renders/L1_A_iso.png`") == []
    # 4. Odsyłacz bez rozszerzenia nie jest ścieżką pliku.
    assert found("patrz `docs/24` i `tools/ci`") == []
    # 5. Glob nie jest plikiem — „nie istnieje" nie jest o nim zdaniem prawdziwym.
    assert found("`.github/workflows/*.yml` i `tools/tests/test_*.py`") == []
    # 6. …a prawdziwa ścieżka z wiodącą kropką JEST łapana, inaczej punkt 5 byłby
    #    wymówką dla całego katalogu `.github/`.
    assert found("`.github/workflows/python-tests.yml`") == [
        ".github/workflows/python-tests.yml"]
    # 7. Adres nie jest ścieżką repozytoryjną.
    assert found("`https://data.stib-mivb.be/x/y.json`") == []


def test_the_scan_reads_only_the_three_fields_that_promise_a_file():
    """Granica zakresu: „Skąd" i „Zależy od" są POZA bramką i to jest wybór.

    Tam plik bywa cytowany jako historia („`reports/X.md` §3 podaje"), a nie jako
    wejście. Objęcie tych pól zamieniłoby bramkę w zakaz cytowania czegokolwiek
    usuniętego — a `docs/TASKS.md` jest też zapisem, co kiedy zmierzono.
    """
    probka = "\n".join([
        "##### 9.Z9 · próbka",
        "- **Skąd:** `reports/nie-ma-mnie.md` §3 podaje",
        "- **Wejście:** `tools/tests/test_all.py`",
        "- **Wyjście:** nic",
        "- **Weryfikacja:** nic",
        "- **Zależy od:** `tools/tez-mnie-nie-ma.py`",
    ])
    hits = scan(text=probka)
    assert {hit["field"] for hit in hits} == {"Wejście"}, hits
    assert [hit["path"] for hit in hits] == ["tools/tests/test_all.py"]
    assert reported(hits) == []
    # …a wzorzec te dwie ścieżki ZNAJDUJE — pominięcie jest decyzją o zakresie,
    # nie skutkiem tego, że wzorzec ich nie widzi.
    assert paths_in("- **Skąd:** `reports/nie-ma-mnie.md` §3") == ["reports/nie-ma-mnie.md"]


def test_the_field_is_cut_the_same_way_as_in_backlog_commands():
    """To samo cięcie pola, co w `backlog_commands` i `test_backlog` — nie druga reguła.

    Gdyby cięcia się rozjechały, ta bramka oglądałaby inny fragment bloku niż bramka
    na komendy, a obie twierdziłyby, że czytają pole „Weryfikacja".
    """
    probka = "\n".join([
        "##### 9.Z8 · próbka",
        "- **Wejście:** `tools/tests/test_all.py`",
        "- **Weryfikacja:**",
        "  ```bash",
        "  python3 tools/tests/test_backlog.py",
        "  ```",
        "- **Poza zakresem:** `tools/tests/test_report_hygiene.py`",
    ])
    blocks = tb.detail_sections(probka)
    body = blocks["9.Z8"]
    assert field_body(body, "Weryfikacja") == bc.verification_field(body)
    # Pole „Poza zakresem" stoi ZA cięciem, więc jego ścieżka nie wchodzi do skanu.
    hits = scan(text=probka)
    assert [(hit["field"], hit["path"]) for hit in hits] == [
        ("Wejście", "tools/tests/test_all.py"),
        ("Weryfikacja", "tools/tests/test_backlog.py"),
    ], hits
    # …i to samo dla pól, które w bloku po prostu nie stoją: `None`, nie pusty napis.
    assert field_body(body, "Wyjście") is None
    assert field_body("", "Wejście") is None


#: Adnotacja, którą niesie poprawka pola w bloku JUŻ WYKONANYM — 6.D126.
#: Grupy: data i powód (reszta nagłówka), a treść uzasadnienia stoi po dwukropku.
POPRAWKA = re.compile(r"\*\*Poprawione\s+(\d{2}\.\d{2}\.\d{4})([^:*]*):\*\*")

#: Ile znaków uzasadnienia musi stać za adnotacją. Adnotacja bez powodu jest tańsza
#: od poprawki z powodem i rośnie z tego samego powodu, co lista wyjątków bez
#: zapadki — a tutaj kosztem jest przepisany zapis historyczny.
MINIMUM_POWODU = 120

#: Ile takich poprawek jest dziś. Zapadka w GÓRĘ nie ma sensu (poprawek ma być
#: mało), w DÓŁ też nie (zdjęcie adnotacji jest cichym przepisaniem historii),
#: więc liczba jest **przybita równością** i zmiana jej wymaga zdania w commicie.
#: Zmierzone 11.09.2026: cztery z 10.09.2026 (6.D73, 6.D74, 6.D86, 6.D89) plus
#: piąta z tej pozycji, w tym samym bloku 6.D74, w innym polu.
#: **5 → 6 (11.09.2026, przy 6.D133).** Szósta: blok 6.D133, pole
#: „Weryfikacja”, wołające `test_scan_gates.py` zamiast `test_tree_walks.py`.
#: Ten sam kształt, co poprawka piąta — pole opisywało bramkę prozą poprawnie,
#: a komenda wskazywała moduł o podobnej nazwie i innej treści.
POPRAWEK_W_DRZEWIE = 6


def poprawki_zapisow(blocks=None):
    """`[(numer, data, powod)]` dla adnotacji `**Poprawione …:**` w blokach."""
    zrodlo = blocks if blocks is not None else _all_blocks()
    found = []
    for number, body in zrodlo.items():
        for match in POPRAWKA.finditer(body):
            ogon = body[match.end():]
            koniec = ogon.find("\n- **")
            found.append((number, match.group(1),
                          ogon if koniec < 0 else ogon[:koniec]))
    return found


def test_kazda_poprawka_zapisu_wykonanego_niesie_date_i_powod():
    """Poprawka w bloku wykonanym ma być WIDOCZNA, a nie cicha — 6.D126.

    Rozstrzygnięcie „zapis fałszywy wolno poprawić" stoi w docstringu `_open_blocks`
    i ma trzy warunki. Ten test pilnuje dwóch z nich, bo są sprawdzalne z tekstu:
    adnotacja niesie datę i niesie powód. Trzeciego — że zapis był fałszywy, a nie
    przestarzały — sprawdzić się nie da bez czytania historii, i mówię to wprost,
    zamiast udawać, że bramka obejmuje całą regułę.

    **Liczba jest przybita RÓWNOŚCIĄ, nie progiem.** W górę próg nie ma sensu, bo
    poprawek ma być mało; w dół też nie, bo zdjęcie adnotacji jest dokładnie tym
    cichym przepisaniem historii, przed którym ta reguła broni.
    """
    poprawki = poprawki_zapisow()
    assert len(poprawki) == POPRAWEK_W_DRZEWIE, (
        "poprawek zapisów wykonanych jest %d przy zapadce %d — dopisanie albo "
        "zdjęcie adnotacji wymaga zdania w commicie: %s"
        % (len(poprawki), POPRAWEK_W_DRZEWIE, [(n, d) for n, d, _p in poprawki]))

    krotkie = [(n, d, len(p)) for n, d, p in poprawki if len(p) < MINIMUM_POWODU]
    assert krotkie == [], (
        "adnotacja bez powodu — poprawka zapisu wykonanego ma mówić, co stało "
        "wcześniej i dlaczego wolno było to zmienić: %s" % krotkie)

    # Kontrola przyrządu: wzorzec czyta DATĘ, a nie cokolwiek. Bez tego adnotacja
    # bez daty byłaby niewidzialna i liczba wyżej milczałaby o jej zniknięciu.
    assert poprawki_zapisow({"X": "**Poprawione przy wykonaniu:** " + "x" * 200}) == [], (
        "adnotacja BEZ daty została policzona jako poprawna")
    syntetyczna = poprawki_zapisow(
        {"X": "**Poprawione 01.01.2026 przy czymś:** " + "y" * 200})
    assert [(n, d) for n, d, _p in syntetyczna] == [("X", "01.01.2026")], syntetyczna
    assert len(syntetyczna[0][2]) >= MINIMUM_POWODU, len(syntetyczna[0][2])

    # …i że KRÓTKA adnotacja naprawdę wpada do `krotkie`, a nie tylko mogłaby.
    krotka = poprawki_zapisow({"X": "**Poprawione 01.01.2026 przy czymś:** bo tak"})
    assert len(krotka[0][2]) < MINIMUM_POWODU, krotka


def test_pole_weryfikacji_6d74_wskazuje_modul_z_bramka_o_ktorej_mowi():
    """Konkretny przypadek, który tę pozycję wywołał — przybity, nie opisany.

    Bramka adresów nie zobaczy go nigdy: `test_scan_gates.py` w drzewie JEST, więc
    `_only_path` go przyjmuje, a blok 6.D74 jest wykonany, więc skan go nie czyta.
    Ten test pyta wprost o to, o co tamta bramka pytać nie może — o TREŚĆ modułu,
    i tylko dla tego jednego bloku, bo przeglądanie pozostałych jest w polu „Poza
    zakresem" pozycji 6.D126.
    """
    blok = _all_blocks()["6.D74"]
    nazwy = module_names(field_body(blok, "Weryfikacja"))
    assert nazwy == ["test_tree_walks.py"], (
        "pole „Weryfikacja” bloku 6.D74 woła %s, a bramka o przejściach po drzewie "
        "mieszka w `test_tree_walks.py`" % nazwy)

    # I że wskazany moduł NAPRAWDĘ trzyma tę bramkę — inaczej asercja wyżej
    # pilnowałaby samej nazwy, a nie tego, co pod nią stoi.
    import test_all
    zrodlo = open(test_all._only_path(nazwy[0]), encoding="utf-8").read()
    assert "def test_no_tool_walks_the_tree_without_the_shared_filter" in zrodlo, (
        "moduł z pola 6.D74 nie zawiera bramki o przejściach po drzewie")

    # Kontrola przyrządu: dawny adres istnieje i testuje CO INNEGO — to jest powód,
    # dla którego `missing_modules` tego nie łapało.
    dawny = open(test_all._only_path("test_scan_gates.py"), encoding="utf-8").read()
    assert "tools/blender/scan_gates.py" in dawny, (
        "`test_scan_gates.py` przestał testować skan luzu — powód zapisany "
        "w adnotacji przy 6.D74 wymaga przeliczenia")
    assert "def test_no_tool_walks_the_tree_without_the_shared_filter" not in dawny


def test_the_exception_list_does_not_rot():
    """Wyjątek, który przestał być potrzebny, musi z listy ZNIKNĄĆ.

    Trzy warunki, każdy zamyka inną drogę zgnicia: powód podany zdaniem, wystąpienie
    nadal w pliku (blok, pole i ścieżka co do znaku), a ścieżka nadal nieistniejąca.
    """
    hits = scan()
    wystapienia = {_key(hit): hit for hit in hits}
    for key, reason in EXCEPTIONS.items():
        assert len(reason) > 40, "wyjątek na %s bez powodu: %r" % (_where(key), reason)
        assert key in wystapienia, (
            "wyjątek na %s — takiego wystąpienia w `docs/TASKS.md` nie ma" % _where(key))
        assert not wystapienia[key]["exists"], (
            "%s już istnieje — zdejmij ją z listy wyjątków" % _where(key))
        # Obietnica własnego usunięcia jest zakazana z tego samego powodu, co
        # w `test_report_hygiene.test_lista_wyjatkow_nie_gnije`: bramka nie umie
        # sprawdzić, czy obietnica została dotrzymana.
        obietnice = ("po scaleniu", "do zdjęcia", "w locie", "tymczasow",
                     "na razie", "docelowo")
        znalezione = [f for f in obietnice if f in reason.lower()]
        assert not znalezione, (
            "wyjątek na %s uzasadnia się obietnicą %s — powód musi opisywać stan "
            "trwały" % (_where(key), znalezione))


def test_the_exception_list_stays_closed():
    """Zapadka — i STRUKTURALNY zakaz wyjątku dla pola „Wejście".

    Zdanie w docstringu, że pole „Wejście" wyjątku nie ma, jest tylko zdaniem. Ta
    asercja robi z niego regułę: wpis na to pole wywraca bramkę, więc nie da się go
    dopisać po cichu jedną linijką w słowniku.
    """
    assert len(EXCEPTIONS) <= MAX_EXCEPTIONS, (
        "lista wyjątków urosła do %d przy zapadce %d — zła ścieżka ma dostać poprawkę, "
        "a nie miejsce na liście: %s"
        % (len(EXCEPTIONS), MAX_EXCEPTIONS,
           [_where(key) for key in sorted(EXCEPTIONS)[MAX_EXCEPTIONS:]]))
    assert MAX_EXCEPTIONS == len(EXCEPTIONS), (
        "zapadka %d stoi wyżej niż lista (%d) — obniż ją do stanu faktycznego"
        % (MAX_EXCEPTIONS, len(EXCEPTIONS)))
    twarde = [_where(key) for key in EXCEPTIONS if key[1] == HARD_FIELD]
    assert twarde == [], (
        'wyjątek dla pola „Wejście": %s — to pole jest adresem, pod który idzie '
        'następny agent, i wyjątku nie ma' % twarde)
    for key in EXCEPTIONS:
        assert key[1] in FIELDS, key
        assert len(key) == 3, key


def main():
    """Inwentarz do wklejenia w raport: liczby per pole i każda ścieżka z wyrokiem."""
    hits = scan()
    print("bloków szczegółów: %d (zapadka %d)"
          % (len(tb.detail_sections(_tasks())), tb.MINIMUM_DETAIL_BLOCKS))
    print()
    for field in FIELDS:
        wszystkie = [hit for hit in hits if hit["field"] == field]
        brak = {_key(hit) for hit in wszystkie if not hit["exists"]}
        zgl = [key for key in reported(hits) if key[1] == field]
        print("  %-12s %4d ścieżek  %d nieistniejących  %d zgłoszonych  (próg %d)"
              % (field, len(wszystkie), len(brak), len(zgl), MIN_PATHS[field]))
    print("  %-12s %4d" % ("RAZEM", len(hits)))
    print()
    print("  nieistniejące, z wyrokiem:")
    for key in sorted({_key(hit) for hit in hits if not hit["exists"]}):
        hit = [h for h in hits if _key(h) == key][0]
        if key[1] == "Wejście":
            wyrok = "ZGŁOSZONA (szczebel 1, bez wyjątku)"
        elif key[1] == OUTPUT_FIELD:
            wyrok = "przyjęta: plik do wytworzenia (rodzaj a)"
        elif hit["in_own_output"]:
            wyrok = "przyjęta: komenda, która go tworzy (rodzaj b)"
        elif key in EXCEPTIONS:
            wyrok = "przyjęta: wyjątek z powodem (rodzaj c)"
        else:
            wyrok = "ZGŁOSZONA (szczebel 2)"
        print("    %-58s %s" % (_where(key), wyrok))
    print()
    print("  ZGŁOSZONYCH z rozróżnieniem pól:      %d" % len(reported(hits)))
    print("  ZGŁOSZONYCH bez rozróżnienia pól:     %d"
          % len(reported(hits, distinguish=False)))
    print("  wyjątków na liście: %d (zapadka %d)" % (len(EXCEPTIONS), MAX_EXCEPTIONS))
    for key in reported(hits):
        print("    " + _where(key))
    return 0


if __name__ == "__main__":
    if "--inwentarz" in sys.argv:
        raise SystemExit(main())
    import test_all
    raise SystemExit(test_all.main(__file__))


#: Zly adres wypisany w adnotacji poprawki — 6.D157.
#:
#: Adnotacje maja jeden ksztalt: „pole wskazywalo/wolalo `X`", gdzie `X` jest adresem
#: BLEDNYM, a reszta zdania nazywa ten wlasciwy. Bez tego rozroznienia licznik modulow
#: liczylby razem adres zly i poprawny — a to sa dwie rozne rzeczy w jednym zdaniu.
ZLY_ADRES_Z_POPRAWKI = re.compile(
    r"pole (?:wskazywało|wołało) `([A-Za-z0-9_./-]+\.py)`")

#: Ile razy kazdy modul padl jako ZLY adres — wyprowadzone z drzewa, przybite tu.
ZLE_ADRESY = {
    "test_scan_gates.py": 3,
    "test_backlog.py": 1,
    "test_physics_reference.py": 1,
    "test_glossary.py": 1,
}

#: Ile z szesciu zlych adresow niesie UKOSNIK, czyli w ogole trafia pod `PATH_TOKEN`.
ZLYCH_ADRESOW_ZE_SCIEZKA = 2

#: Ile z nich wskazuje plik, ktory w drzewie ISTNIEJE — 6.D157.
ZLYCH_ADRESOW_ISTNIEJACYCH = 4


def zle_adresy_z_poprawek():
    """`[(numer, data, zly_adres)]` — po jednym na kazda adnotacje poprawki."""
    out = []
    for numer, data, powod in poprawki_zapisow():
        trafienia = ZLY_ADRES_Z_POPRAWKI.findall(" ".join(powod.split()))
        out.append((numer, data, trafienia))
    return out


def test_kazda_poprawka_nazywa_DOKLADNIE_jeden_zly_adres():
    """Kontrola PRZYRZADU, zanim cokolwiek z niego policzymy — 6.D157.

    Gdyby wzorzec chybil choc jednej adnotacji, licznik nizej bylby mniejszy i nikt
    by sie nie dowiedzial — bo mniejszy licznik wyglada dokladnie tak samo jak
    mniejsza liczba pomylek. Ta bramka mowi, ze skan widzi KAZDA z szesciu.
    """
    znalezione = zle_adresy_z_poprawek()
    assert len(znalezione) == POPRAWEK_W_DRZEWIE, (
        "adnotacji poprawek jest %d, a zapadka stoi na %d"
        % (len(znalezione), POPRAWEK_W_DRZEWIE))
    puste = [(n, d) for n, d, t in znalezione if len(t) != 1]
    assert not puste, (
        "adnotacja bez DOKLADNIE jednego zlego adresu: %s — wzorzec rozjechal sie "
        "z ksztaltem zdania i licznik ponizej liczy mniej, niz jest" % puste)


def test_ktory_modul_padl_jako_zly_adres_wiecej_niz_raz():
    """Pole „Wyjscie" 6.D157 zada listy z liczba przy kazdym — z DRZEWA, nie wpisanej.

    **WYNIK: powtarza sie DOKLADNIE JEDEN modul — `test_scan_gates.py` — i pada
    TRZY razy, a nie dwa.** Wpis pozycji mowil o dwoch blokach (6.D74 i 6.D133);
    blok 6.D74 byl poprawiany DWUKROTNIE, 10.09 i 11.09, i obie poprawki nazywaja
    ten sam zly adres. Trzy na szesc to POLOWA wszystkich poprawek w drzewie.
    """
    licznik = {}
    for _numer, _data, trafienia in zle_adresy_z_poprawek():
        nazwa = os.path.basename(trafienia[0])
        licznik[nazwa] = licznik.get(nazwa, 0) + 1

    assert licznik == ZLE_ADRESY, (
        "rozklad zlych adresow to %s, a pomiar z 12.09.2026 dal %s"
        % (sorted(licznik.items()), sorted(ZLE_ADRESY.items())))
    powtarzajace = sorted(n for n, ile in licznik.items() if ile > 1)
    assert powtarzajace == ["test_scan_gates.py"], (
        "powtarzajacych sie zlych adresow jest %s — odpowiedz 6.D157 „powtarza sie "
        "dokladnie jeden” przestala byc prawdziwa" % powtarzajace)


def test_bramka_istnienia_nie_mogla_zlapac_ani_jednej_z_tych_szesciu():
    """Dlaczego powtorzenie nie wymaga wyjasnienia — 6.D157.

    **To jest odpowiedz na pytanie „regula czy zbieg okolicznosci".** Zaden z szesciu
    zlych adresow nie mogl zostac zlapany, i to z DWOCH roznych powodow:

    * **cztery** stoja BEZ katalogu, a `PATH_TOKEN` zada ukosnika — wiec bramka
      w ogole na nie nie patrzy;
    * **dwa**, ktore ukosnik maja, wskazuja pliki, ktore w drzewie ISTNIEJA — wiec
      bramka patrzy i przepuszcza, bo sprawdza ISTNIENIE, a nie PRZEDMIOT.

    Adres, ktory przechodzi za kazdym razem, mozna wpisac za kazdym razem. Powtorzenie
    nie jest wiec wlasnoscia tego modulu, tylko KLASY: tylko adres istniejacy da sie
    powtorzyc, bo wymyslony i tak nie zostanie zlapany, ale i nie zostanie wpisany
    drugi raz przez kogos, kto go wlasnie poprawil.
    """
    ze_sciezka = 0
    istniejace = 0
    for _numer, _data, trafienia in zle_adresy_z_poprawek():
        adres = trafienia[0]
        if "/" in adres:
            ze_sciezka += 1
            assert PATH_TOKEN.search(adres), (
                "adres `%s` ma ukosnik, a `PATH_TOKEN` go nie widzi — podzial na "
                "„bramka patrzy” i „nie patrzy” przestal byc prawdziwy" % adres)
        else:
            assert not PATH_TOKEN.search(adres), (
                "adres `%s` bez katalogu zostal zlapany przez `PATH_TOKEN` — wtedy "
                "cztery z szesciu NIE sa poza zasiegiem bramki i ten test mowi "
                "nieprawde" % adres)
        if _istnieje_w_drzewie(os.path.basename(adres)):
            istniejace += 1

    assert ze_sciezka == ZLYCH_ADRESOW_ZE_SCIEZKA, (
        "zlych adresow z ukosnikiem jest %d, a pomiar dal %d"
        % (ze_sciezka, ZLYCH_ADRESOW_ZE_SCIEZKA))
    assert istniejace == ZLYCH_ADRESOW_ISTNIEJACYCH, (
        "zlych adresow wskazujacych ISTNIEJACY plik jest %d, a pomiar dal %d — "
        "jesli spadlo, ktorys modul zniknal i zdanie „bramka przepuszcza, bo plik "
        "istnieje” opisuje inny stan" % (istniejace, ZLYCH_ADRESOW_ISTNIEJACYCH))


def _istnieje_w_drzewie(nazwa):
    """Czy plik o tej nazwie stoi gdziekolwiek w drzewie — 6.D157.

    Przez `tree_walk.znajdz`, a nie `os.walk`: wspolny filtr odsiewa galezie
    pominiete w `.gitignore`, a wlasne przejscie po drzewie ma w tym repozytorium
    swoja bramke (6.D74, 6.D97, 6.D117) — i zlapala ta funkcje, gdy pierwsza wersja
    wolala `os.walk` wprost.
    """
    return bool(tw.znajdz(ROOT, nazwa, ROOT))


#: Ile ADRESOW (`PATH_TOKEN`) stoi w blokach wykonanych, per pole — 6.D158.
#:
#: Zmierzone 13.09.2026. Rozklad jest tu trescia, a nie ozdoba: pole „Wejscie" niesie
#: adresow WIECEJ NIZ POZOSTALE DWA RAZEM, a regula kandydatow z 6.D146 nie moze
#: siegnac do niego ani jednym — patrz `test_zero_wywolan_poza_Weryfikacja_jest_STRUKTURALNE`.
#:
#: **Te liczby rosna przy KAZDYM domknieciu pozycji i to nie jest usterka.** Domkniecie
#: przenosi WLASNY blok pozycji do zbioru wykonanych, razem z adresami, ktore ten blok
#: cytuje — wiec pomiar zmienia sie przez to, ze zostal zapisany. Przy 6.D158 bylo
#: 849/63/364 (241 blokow), zaraz po jego domknieciu 851/63/365 (242), a po domknieciu
#: 6.D159 — 853/63/366 (243).
#:
#: **Nastepne domkniecie podniesie je znowu i trzeba to zrobic TYM SAMYM commitem**,
#: tak jak kazda inna zapadke tego projektu. Ulamek z
#: `test_jaka_czesc_adresow_obejrzala_regula_kandydatow_6D146` jest odporny na ten
#: ruch z wyboru — stoi w przedziale, nie w rownosci — i po dwoch domknieciach nadal
#: pokazuje te sama jedna trzynasta.
# 931 -> 935 (14.09.2026, 6.D203): cztery adresy dopisane w wierszu domknięcia
# tej pozycji — `test_prose_counts.py`, `test_runner_number_parsing.py`,
# `test_backlog.py` i sam raport. „Weryfikacja" rośnie o jeden (383 -> 384),
# a „Wyjście" nie drga — blok sześciu pól pozycji nie był ruszany, zmienił
# się WIERSZ TABELI, a skan czyta oba.
# 935 -> 938 (14.09.2026, 6.D204): trzy adresy z pola „Wejście" WŁASNEGO bloku
# tej pozycji, ktory domkniecie przenioslo do wykonanych — `tools/tests/mutation_sweep.py`,
# `tools/tests/test_module_entrypoints.py` i `reports/6d191-nie-ta-zmienna.md`.
# „Weryfikacja" rosnie o jeden (384 -> 385) za `tools/tests/test_all.py` z plotka tego
# bloku, „Wyjscie" nie drga — to pole nie cytuje ani jednego adresu.
# 938 -> 942 (14.09.2026, 6.D205): cztery adresy z pola „Wejście" WLASNEGO bloku
# tej pozycji — `test_suite_runtime_budget.py`, `test_timing_record.py`,
# `tests/data/ci-logs/README.md` i `reports/6d190-…`. „Weryfikacja" rosnie o jeden
# (385 -> 386) za `tools/tests/test_all.py` z plotka tego bloku, „Wyjscie" nie drga.
# 942 -> 945 (14.09.2026, 6.D206): trzy adresy z pola „Wejście" WLASNEGO bloku tej
# pozycji — `test_suite_runtime_budget.py`, `test_readme_claims.py` i `reports/6d193-…`.
# „Weryfikacja" rosnie o jeden (386 -> 387) za `tools/tests/test_all.py` z plotka tego
# bloku. Liczba jest PRZELICZONA na drzewie po scaleniu #610, a nie zsumowana z dwoch
# galezi: obie pozycje domknieto tego samego dnia i obie dokladaly do tej samej puli.
# 945 -> 949 (14.09.2026, 6.D207): cztery adresy z pola „Wejście" WLASNEGO bloku tej
# pozycji — `test_report_claims.py`, `test_prose_counts.py`,
# `test_suite_runtime_budget.py` i `reports/6d193-…`. „Weryfikacja" rosnie o jeden
# (387 -> 388) za `tools/tests/test_all.py` z plotka tego bloku, „Wyjscie" nie drga.
# Przeliczone na drzewie po scaleniu #611, a nie zsumowane z dwoch galezi.
# 949 -> 952 (14.09.2026, 6.D208): trzy adresy z pola „Wejście" WLASNEGO bloku tej
# pozycji — `docs/TASKS.md`, `test_backlog.py` i `reports/6d196-…`. „Weryfikacja"
# rosnie o jeden (388 -> 389) za `tools/tests/test_all.py` z plotka tego bloku.
# Przeliczone na drzewie po scaleniu #612.
# 952 -> 955 (14.09.2026, 6.D209): trzy adresy z pola „Wejście" WLASNEGO bloku tej
# pozycji — `test_report_claims.py`, `test_backlog.py` i `reports/6d196-…`.
# „Weryfikacja" rosnie o jeden (389 -> 390) za `tools/tests/test_all.py` z plotka.
# Przeliczone na drzewie po scaleniu #613.
# 955 -> 958 (14.09.2026, 6.D210): trzy adresy z pola „Wejście" WLASNEGO bloku tej
# pozycji — `src/Game/FirstRun.cs`, `tests/Game.Tests/UiTextTests.cs` i `reports/6d197-…`.
# „Weryfikacja" NIE DRGA i to jest treść, a nie brak: płotek tej pozycji woła
# `dotnet test tests/Sim.Tests`, a nie `tools/tests/test_all.py`, więc nie niesie ani
# adresu, ani wywołania modułu. Przeliczone na drzewie po scaleniu #614.
# 958 -> 964 (14.09.2026, 6.D211): SZEŚĆ adresów z pola „Wejście" WŁASNEGO bloku tej
# pozycji — `FixedBlockSystem.cs`, `SignallingEvent.cs`, `LineCore.cs`, `CabProtection.cs`,
# `TrainProtection.cs` i `reports/6d197-…`. Najwięcej, ile ta zapadka podniosła się przy
# jednym domknięciu; siódma pozycja pola — `tests/Sim.Tests/` — do liczby NIE weszła, bo
# jest katalogiem, a `PATH_TOKEN` czyta pliki. „Weryfikacja" nie drga z tego samego powodu
# co przy 6.D210: płotek woła `dotnet test tests/Sim.Tests`, nie `tools/tests/test_all.py`.
# Przeliczone na drzewie po scaleniu #615.
# 964 -> 967 (15.09.2026, 6.D212): trzy adresy z pola „Wejście" WŁASNEGO bloku tej
# pozycji — `tests/Game.Tests/UiTextTests.cs`, `tools/tests/csharp_test_methods.py`
# i `reports/6d197-…`. „Weryfikacja" rośnie o jeden (390 -> 391), bo płotek tej pozycji
# woła `tools/tests/test_all.py` — inaczej niż przy 6.D210 i 6.D211, gdzie wołał
# `dotnet test`. Przeliczone na drzewie po scaleniu #616.
# 967 -> 971 (15.09.2026, 6.D222): CZTERY adresy z pola „Wejście" WŁASNEGO bloku tej
# pozycji — `prune-merged-branches.yml`, `test_ci_workflows.py`, `docs/04-conventions.md`
# i `reports/6d211-…`. „Weryfikacja" rośnie o jeden (391 -> 392) za
# `tools/tests/test_all.py` z płotka tego bloku.
# 971 -> 973 (15.09.2026, 6.D213): DWA adresy z pola „Wejście" WŁASNEGO bloku tej
# pozycji — `tests/Game.Tests/UiTextTests.cs` i `reports/6d199-…`. Pozostałe pozycje
# tego pola to katalogi (`src/Sim/**/*.cs`, `tests/Sim.Tests/`), a `PATH_TOKEN` czyta
# pliki. „Weryfikacja" NIE DRGA: płotek tej pozycji woła `dotnet test`, nie `test_all.py`.
# 973 -> 976 (15.09.2026, 6.D214): TRZY adresy z pola „Wejście" WŁASNEGO bloku tej
# pozycji — `tests/Game.Tests/UiTextTests.cs`, `src/Game/FirstRun.cs` i `reports/6d199-…`.
# „Weryfikacja" rośnie o jeden (392 -> 393) za `tools/tests/test_csharp_test_methods.py`
# z płotka tego bloku.
# 976 -> 980 (15.09.2026, 6.D215): CZTERY adresy z pola „Wejście" WLASNEGO bloku tej
# pozycji — `csharp_test_methods.py`, `UiTextTests.cs`, `test_csharp_test_methods.py`
# i `reports/6d200-…`. „Weryfikacja" rosnie o jeden (393 -> 394) za
# `tools/tests/test_all.py` z plotka tego bloku.
# 980 -> 983 (15.09.2026, 6.D216): TRZY adresy z pol „Wejscie" DWOCH wlasnych blokow
# tej pozycji — `test_report_claims.py` i `reports/6d210-…` w 6.D227,
# `src/Sim/Train/DriverKeys.cs` tamze; pozostale pozycje obu pol to katalogi
# (`reports/*.md`) albo powtorzenia, a `PATH_TOKEN` liczy kazdy adres raz.
# „Weryfikacja" rosnie o jeden (394 -> 395) za `tools/tests/test_report_claims.py`
# z plotka bloku 6.D227.
# 983 -> 986 (15.09.2026, 6.D217): TRZY adresy z pola „Wejscie" wlasnego bloku 6.D229 —
# `src/Sim/Train/InputLog.cs`, `src/Sim.Runner/Program.cs` i `reports/obsada-planu.md`;
# reszta pola powtarza adresy juz liczone gdzie indziej, a `PATH_TOKEN` liczy kazdy raz.
# „Weryfikacja" NIE DRGA: plotek tego bloku wola `dotnet test`, nie `test_all.py`.
# 986 -> 989 (15.09.2026, 6.D218): TRZY adresy z pola „Wejscie" WLASNEGO bloku tej
# pozycji — `tools/tests/test_prose_counts.py`, `tools/tests/test_tree_walks.py`
# i `reports/6d206-…`; czwarty adres tego pola (`docs/TASKS.md`) byl juz liczony.
# „Weryfikacja" rosnie o jeden (395 -> 396) za `tools/tests/test_all.py` z plotka
# tego bloku.
# 989 -> 991 (15.09.2026, 6.D219): DWA adresy z pola „Wejscie" wlasnego bloku 6.D230 —
# `tools/tests/test_backlog.py` i `reports/6d219-…`; reszta pola byla juz liczona.
# „Weryfikacja" rosnie o jeden (396 -> 397) za `tools/tests/test_backlog.py`
# z plotka tego bloku.
# 991 -> 993 (15.09.2026, 6.D220): DWA adresy z pola „Wejscie" wlasnego bloku 6.D231 —
# `tests/Sim.Tests/DefaultArmAuditTests.cs` i `reports/6d220-…`; pozostale adresy tego
# pola byly juz liczone. „Weryfikacja" NIE DRGA: plotek tego bloku wola `dotnet test`.
# 993 -> 997 (15.09.2026, 6.D221): CZTERY adresy z pola „Wejscie" WLASNEGO bloku
# tej pozycji — `tools/tests/test_field_paths.py`, `tests/Sim.Tests/DefaultArmAuditTests.cs`,
# `docs/TASKS.md` i `reports/6d211-…`. Tym razem NIE jest to blok pozycji obcej
# dopisany przy okazji: 6.D221 zostalo w tym samym commicie ODHACZONE, wiec jego
# wlasny blok wszedl do `bloki_wykonane()` w calosci. Rozjazd wyliczony diffem
# `adresy_pola_w_wykonanych` przed edycja i po niej, nie odjeciem liczb.
# „Weryfikacja" rosnie o jeden (397 -> 398) za `tools/tests/test_all.py` z plotka
# tego bloku, a `WYWOLAN_W_WYKONANYCH` NIE DRGA: plotek wola zestaw BEZ nazwy
# modulu, a `MODULE_CALL` liczy wylacznie `test_all.py <modul>`.
# 997 -> 1003 (15.09.2026, 6.D223): SZESC adresow z pola „Wejscie" WLASNEGO bloku
# tej pozycji — `reports/6d212-…`, `test_camera_aim.py`, `test_clearance_profile.py`,
# `test_dimension_audit.py`, `test_environment_doc.py` i `test_stations.py`; siodma
# pozycja tego pola (`tools/tests/*.py`) jest wzorcem, a `PATH_TOKEN` czyta pliki.
# Ten sam mechanizm co przy 6.D221 i tak samo wyliczony — DIFFEM
# `adresy_pola_w_wykonanych` przed edycja i po niej: 6.D223 zostalo w tym commicie
# ODHACZONE, wiec jego wlasny blok wszedl do `bloki_wykonane()` w calosci.
# „Weryfikacja" rosnie o jeden (398 -> 399) za `tools/tests/test_all.py` z plotka
# tego bloku, a `WYWOLAN_W_WYKONANYCH` NIE DRGA z tego samego powodu co wtedy:
# plotek wola zestaw BEZ nazwy modulu.
# 1003 -> 1005 (15.09.2026, 6.D224): DWA adresy z pola „Wejscie" WLASNEGO bloku tej
# pozycji — `tests/Game.Tests/UiTextTests.cs` i `reports/6d213-…`; pozostale pozycje
# tego pola byly juz liczone albo sa wzorcami (`src/Sim/**/*.cs`), a `PATH_TOKEN`
# czyta pliki. Ten sam mechanizm co przy 6.D221 i 6.D223 i tak samo wyliczony —
# DIFFEM `adresy_pola_w_wykonanych` przed edycja i po niej. „Weryfikacja" NIE DRGA:
# plotek tego bloku wola `dotnet test`, nie `test_all.py`.
# 6.D240: 1005/63/399 -> 1011/63/400. Policzone DIFFEM list, nie odejmowaniem:
# siedem adresów z WŁASNEGO bloku 6.D240, który wszedł do `bloki_wykonane()` w chwili
# odhaczenia wiersza — sześć w polu „Wejście” (akcja sondująca, workflow, dwa zestawy
# apt, dwa moduły testowe) i `test_all.py` w „Weryfikacji”.
# 6.D241: 1011/63/400 -> 1013/64/401. Policzone DIFFEM list, nie odejmowaniem:
# cztery adresy z WŁASNEGO bloku 6.D241, który wszedł do `bloki_wykonane()` w chwili
# odhaczenia wiersza — `tools/tests/test_all.py` i `tools/ci/blender_smoke.sh`
# w polu „Wejście”, `tools/tests/test_doctor_test_log.py` w „Wyjściu” (to pole drga
# tu pierwszy raz od 6.D224 i dlatego jest wypisane osobno) oraz `tools/tests/test_all.py`
# w „Weryfikacji”.
# 6.D247: 1011/63/400 -> 1013/63/401. Policzone DIFFEM list, nie odejmowaniem:
# trzy adresy z WŁASNEGO bloku 6.D247 — `tools/tests/test_suite_runtime_budget.py`
# i `.github/workflows/python-tests.yml` w polu „Wejście”, `tools/tests/test_all.py`
# w „Weryfikacji”.
# 6.D226: 1011/63/400 -> 1015/63/401. Policzone DIFFEM list: pięć adresów z WŁASNEGO
# bloku 6.D226, który wszedł do `bloki_wykonane()` w chwili odhaczenia wiersza —
# cztery w polu „Wejście” (dwa raporty i dwa pliki tabeli) i `test_all.py` w „Weryfikacji”.
# 6.D243: 1011/63/400 -> 1014/63/401. Policzone DIFFEM list, nie odejmowaniem:
# cztery adresy z WŁASNEGO bloku 6.D243 — trzy w polu „Wejście”
# (`.github/workflows/godot-first-run.yml`, `tools/ci/apt-packages/blender.txt`,
# `tools/tests/test_ci_workflows.py`) i `tools/tests/test_all.py` w „Weryfikacji”.
# SCALENIE 6.D241 + 6.D243: 1016/64/402. **PRZELICZONE NA DRZEWIE PO SCALENIU,
# a nie zsumowane z dwóch gałęzi** — i to nie jest ostrożność: 6.D243 sama dawała
# 1014/63/401, 6.D241 sama 1013/64/401, a drzewo scalone ma 1016/64/402. Ani jedna
# z tych dwóch liczb nie jest tu prawdziwa, bo oba bloki weszły do `bloki_wykonane()`
# naraz i oba cytują `tools/tests/test_all.py` w „Weryfikacji”.
# 6.D242: 1011/63/400 -> 1015/63/401. Policzone DIFFEM list, nie odejmowaniem:
# pięć adresów z WŁASNEGO bloku 6.D242, który wszedł do `bloki_wykonane()` w chwili
# odhaczenia wiersza — cztery w polu „Wejście” (`tools/ci/blender_install.sh`,
# `.github/actions/probe-tools/action.yml`, `tools/ci/apt-packages/blender.txt`,
# `tools/tests/test_ci_workflows.py`) i `tools/tests/test_all.py` w „Weryfikacji”.
# „Wyjście” NIE DRGA: pole wymienia nazwy stałych i funkcji, nie ścieżki.
# 1005/63/399 -> 1013/63/401 po scaleniu 6.D225 i 6.D240. Liczba jest PRZELICZONA
# Z DRZEWA po scaleniu, a nie wzięta z żadnej z dwóch gałęzi: 6.D225 samo dawało
# 1007/63/400, 6.D240 samo 1011/63/400, a scalone drzewo ma OBA bloki i daje
# 1013/63/401. Wzięcie którejkolwiek strony konfliktu byłoby tu liczbą fałszywą,
# a zsumowanie przyrostów (+2 i +6) dałoby 1013 przypadkiem, bo pola „Weryfikacja”
# nakładają się na `test_all.py`. Policzone DIFFEM list, nie odejmowaniem.
# PO SCALENIU 6.D225 z `main`: obie galezie podnosily te zapadke niezaleznie
# i ZADNA Z DWOCH LICZB nie jest prawdziwa dla drzewa scalonego. Liczba nizej jest
# PRZELICZONA DIFFEM Z DRZEWA po scaleniu; sumowanie przyrostow byloby tu bledem,
# bo pola „Weryfikacja" obu blokow wolaja `test_all.py`, czyli ten sam adres.
# 1028/64/406 -> 1033/65/407 (16.09.2026, 6.D228). Przyrost NIE pochodzi z nowych
# adresow: blok 6.D228 dostal adnotacje ZROBIONE, wiec PRZESZEDL z populacji blokow
# OTWARTYCH do WYKONANYCH razem ze swoimi polami. Zmierzone PODSTAWIENIEM, nie
# odejmowaniem: po zdjeciu samego napisu ZROBIONE z wiersza czytnik daje z powrotem
# 1028/64/406 i 141 wywolan, czyli dokladnie stare zapadki. Te cztery liczby rusza
# odtad KAZDA adnotacja ZROBIONE, a nie tylko dopisany adres — i to jest wlasciwosc
# populacji „bloki wykonane", nie usterka.
# 1033/65/407 -> 1038/65/408 i 142 -> 143 (16.09.2026, 6.D239): adnotacja ZROBIONE na
# wierszu 6.D239 przeniosla jego blok z populacji OTWARTYCH do WYKONANYCH razem z polami,
# dokladnie tak, jak opisuje komentarz z 6.D228 wyzej. Pole „Wyjscie" nie drgnelo, bo ten
# blok nie nazywa w nim zadnej sciezki. Przeliczone z drzewa, nie odejmowaniem.
# 1038/65/408 -> 1040/65/409 i 143 -> 144 (16.09.2026, 6.D236): ta sama przyczyna co
# przy 6.D228 i 6.D239 wyzej — adnotacja ZROBIONE przenosi blok pozycji z populacji
# OTWARTYCH do WYKONANYCH razem z jego polami. Trzeci raz tego samego dnia, wiec nie
# jest to niespodzianka, tylko WLASCIWOSC populacji „bloki wykonane": rusza ja KAZDE
# domkniecie pozycji. Przeliczone z drzewa.
# 1038/65/408 -> 1042/65/409 i 143 -> 144 (16.09.2026, 6.D230): adnotacja ZROBIONE
# przeniosla blok tej pozycji do populacji WYKONANYCH. Czwarty raz tego samego dnia.
# Obie strony tego konfliktu podnosily TE SAMA zapadke z TEGO SAMEGO powodu, do
# ROZNYCH wartosci (1040 i 1042) — bo kazda widziala tylko SWOJE domkniecie.
# Drzewo scalone niesie OBIE adnotacje, wiec zadna ze stron nie jest poprawna.
# Wartosc nizej PRZELICZONA z drzewa po scaleniu.
# 1044/65/410 -> 1047/65/411 (17.09.2026, 6.D237): PIATY raz ta sama przyczyna —
# adnotacja ZROBIONE przenosi blok pozycji z populacji OTWARTYCH do WYKONANYCH razem
# z jego polami. Przeliczone z drzewa.
# 1047/65/411 -> 1052/65/412 (17.09.2026, 6.D238): SZOSTY raz ta sama przyczyna —
# adnotacja ZROBIONE przenosi blok pozycji do populacji WYKONANYCH. Przeliczone z drzewa.
# 1052/65/412 -> 1056/65/412 (17.09.2026, 6.D231): SIODMY raz ta sama przyczyna —
# adnotacja ZROBIONE przenosi blok pozycji do populacji WYKONANYCH. Pole „Weryfikacja"
# NIE drgnelo, bo plotek tego bloku wola te same adresy, co juz w niej stoja.
# 1056/65/412 -> 1058/65/413 (17.09.2026, 6.D232): OSMY raz ta sama przyczyna —
# adnotacja ZROBIONE przenosi blok pozycji do populacji WYKONANYCH. Cztery NOWE bloki
# (6.D252-6.D255) tej liczby NIE ruszaja, bo sa OTWARTE; licza sie do `MIN_PATHS`.
# 1058/65/413 -> 1064/65/413 (17.09.2026, 6.D229): DZIEWIATY raz ta sama przyczyna —
# adnotacja ZROBIONE przenosi blok pozycji do populacji WYKONANYCH. Pole „Weryfikacja"
# nie drgnelo, bo plotek tego bloku wola adresy juz w niej stojace.
# 1064/65/413 -> 1070/65/414 (17.09.2026, 6.D233): DZIESIATY raz ta sama przyczyna —
# adnotacja ZROBIONE przenosi blok pozycji do populacji WYKONANYCH razem z polami.
# 1070/65/414 -> 1072/65/414 (17.09.2026, 6.D252): JEDENASTY raz ta sama przyczyna.
# „Wejście" 1072 -> 1075 (17.09.2026, 6.D253): TRZY adresy z pola „Wejście"
# WLASNEGO bloku tej pozycji, ktory adnotacja ZROBIONE przeniosla do wykonanych —
# `tests/Game.Tests/TractionBlockTests.cs`, `tests/Game.Tests/TrainingWiringTests.cs`
# i `tests/Game.Tests/HandleTrainKeysGateTests.cs`. „Weryfikacja" NIE DRGA i to jest
# tresc, a nie brak: plotek tej pozycji wola `~/.dotnet/dotnet test tests/Game.Tests`,
# a nie `tools/tests/test_all.py`, wiec nie niesie ani adresu, ani wywolania modulu —
# ten sam ksztalt co przy 6.D210. „Wyjscie" nie drga, bo to pole nie cytuje ani jednego
# adresu. Blok 6.D257, dopisany tym samym commitem, do tych liczb NIE wchodzi: jest
# pozycja OTWARTA, a skan czyta wylacznie bloki wykonanych. Liczby PRZELICZONE
# czytnikiem `adresy_pola_w_wykonanych` na pliku PO edycji, nie zsumowane.
# 1075 -> 1077 i „Weryfikacja" 414 -> 415 (17.09.2026, 6.D254): adresy z pol WLASNEGO
# bloku tej pozycji, ktory adnotacja ZROBIONE przeniosla do wykonanych. Tym razem
# „Weryfikacja" DRGA, inaczej niz przy 6.D253, i to jest tresc: plotek tej pozycji wola
# `python3 tools/tests/test_all.py test_tree_walks.py`, czyli niesie i ADRES, i WYWOLANIE
# modulu — a plotek 6.D253 wolal `dotnet test`, ktory nie niesie zadnego z dwojga.
# Blok 6.D258, dopisany tym samym commitem, do tych liczb NIE wchodzi: jest pozycja
# OTWARTA, a skan czyta wylacznie bloki wykonanych. Liczby PRZELICZONE czytnikami
# `adresy_pola_w_wykonanych` i `wywolania_pola_w_wykonanych` na pliku PO edycji.
# 1077 -> 1080 i „Weryfikacja" 415 -> 416 (17.09.2026, 6.D255): adresy z pol WLASNEGO
# bloku tej pozycji, ktory adnotacja ZROBIONE przeniosla do wykonanych. Blok 6.D259,
# dopisany tym samym commitem, do tych liczb NIE wchodzi: jest pozycja OTWARTA.
# Liczby PRZELICZONE czytnikami na pliku PO edycji, nie zsumowane.
# 1080 -> 1087 i „Weryfikacja" 416 -> 419 (17.09.2026, 6.D256 + 6.D257): adresy z pol
# WLASNYCH blokow OBU pozycji, ktore adnotacje ZROBIONE przeniosly do wykonanych.
# PRZELICZONE CZYTNIKIEM po scaleniu #658, a nie zsumowane: kazda galaz podnosila
# te liczby o swoj wlasny blok. Bloki 6.D260 i 6.D261 do tych liczb NIE wchodza:
# obie pozycje sa OTWARTE. `WYWOLAN` nie drga (169): plotek 6.D256 wola
# `~/.dotnet/dotnet test`, ktory niesie ADRES, ale nie jest wywolaniem modulu.
# 1087 -> 1092 i „Weryfikacja" 419 -> 421 (17.09.2026, 6.D258): adresy z pol
# WLASNEGO bloku tej pozycji, ktory adnotacja ZROBIONE przeniosla do wykonanych.
# Blok 6.D262, dopisany tym samym commitem, do tych liczb NIE wchodzi: pozycja OTWARTA.
ADRESOW_W_WYKONANYCH = {"Wejście": 1092, "Wyjście": 65, "Weryfikacja": 421}

#: Ile WYWOLAN modulu (`test_all.py X` w plotku) stoi tam, per pole — 6.D158.
# 120 -> 121 (14.09.2026, 6.D203): jedno wywołanie modułu więcej w polu
# „Weryfikacja" — `test_backlog.prog_z_dokumentu` z wiersza domknięcia.
# 121 -> 122 (14.09.2026, 6.D204): jedno wywolanie modulu wiecej —
# `test_module_entrypoints.py` z plotka „Weryfikacji" bloku tej pozycji.
# 122 -> 123 (14.09.2026, 6.D205): jedno wywolanie modulu wiecej —
# `test_timing_record.py` z plotka „Weryfikacji" bloku tej pozycji.
# 123 -> 124 (14.09.2026, 6.D206): jedno wywolanie modulu wiecej —
# `test_readme_claims.py` z plotka „Weryfikacji" bloku tej pozycji. Przeliczone na
# drzewie po scaleniu #610.
# 124 -> 125 (14.09.2026, 6.D207): jedno wywolanie modulu wiecej —
# `test_prose_counts.py` z plotka „Weryfikacji" bloku tej pozycji. Przeliczone na
# drzewie po scaleniu #611.
# 125 -> 126 (14.09.2026, 6.D208): jedno wywolanie modulu wiecej —
# `test_backlog.py` z plotka „Weryfikacji" bloku tej pozycji. Przeliczone na drzewie
# po scaleniu #612.
# 126 -> 127 (14.09.2026, 6.D209): jedno wywolanie modulu wiecej —
# `test_backlog.py` z plotka „Weryfikacji" bloku tej pozycji. Przeliczone na drzewie
# po scaleniu #613.
# 127 -> 128 (15.09.2026, 6.D212): jedno wywolanie modulu wiecej —
# `test_csharp_test_methods.py` z plotka „Weryfikacji" bloku tej pozycji.
# Zera w dwoch pozostalych polach nie drgaja i to jest STRUKTURALNE, nie przypadkowe:
# patrz `test_zero_wywolan_poza_Weryfikacja_jest_STRUKTURALNE`.
# 128 -> 129 (15.09.2026, 6.D222): jedno wywolanie modulu wiecej —
# `test_ci_workflows.py` z plotka „Weryfikacji" bloku tej pozycji.
# 129 -> 130 (15.09.2026, 6.D214): jedno wywolanie modulu wiecej —
# `test_csharp_test_methods.py` z plotka „Weryfikacji" bloku tej pozycji.
# 130 -> 131 (15.09.2026, 6.D215): jedno wywolanie modulu wiecej —
# `test_csharp_test_methods.py` z plotka „Weryfikacji" bloku tej pozycji.
# 131 -> 132 (15.09.2026, 6.D216): jedno wywolanie modulu wiecej —
# `test_report_claims.py` z plotka „Weryfikacji" bloku 6.D227.
# 132 -> 133 (15.09.2026, 6.D218): jedno wywolanie modulu wiecej —
# `test_prose_counts.py` z plotka „Weryfikacji" bloku tej pozycji.
# 133 -> 134 (15.09.2026, 6.D219): jedno wywolanie modulu wiecej —
# `test_backlog.py` z plotka „Weryfikacji" bloku 6.D230.
# 6.D240: „Weryfikacja” 134 -> 135. Policzone DIFFEM listy: doszło JEDNO wywołanie,
# `test_all.py test_ci_workflows.py` z własnego bloku 6.D240.
# 6.D241: „Weryfikacja” 135 -> 136. Policzone DIFFEM listy: doszło JEDNO wywołanie,
# `test_all.py test_doctor_test_log.py` z własnego bloku 6.D241.
# 6.D247: „Weryfikacja” 135 -> 136. Policzone DIFFEM listy: doszło JEDNO wywołanie,
# `test_all.py test_suite_runtime_budget.py` z własnego bloku 6.D247.
# 6.D226: „Weryfikacja” 135 -> 136. DIFFEM listy: doszło JEDNO wywołanie,
# `test_all.py test_csharp_test_methods.py` z własnego bloku 6.D226.
# 6.D243: „Weryfikacja” 135 -> 136. Policzone DIFFEM listy: doszło JEDNO wywołanie,
# `test_all.py test_ci_workflows.py` z własnego bloku 6.D243.
# SCALENIE 6.D241 + 6.D243: „Weryfikacja” 137. Przeliczone na drzewie po scaleniu:
# każdy z dwóch bloków niesie jedno wywołanie modułu w płotku „Weryfikacji”.
# 6.D242: „Weryfikacja” 135 -> 136. Policzone DIFFEM listy: doszło JEDNO wywołanie,
# `test_all.py test_ci_workflows.py` z własnego bloku 6.D242.
# „Weryfikacja” 134 -> 136 po scaleniu 6.D225 i 6.D240: dwa wywołania modułu, po
# jednym z własnego bloku każdej pozycji (`test_all.py test_dead_constants_csharp.py`
# i `test_all.py test_ci_workflows.py`). Każda gałąź osobno dawała 135; liczba jest
# przeliczona z drzewa po scaleniu.
# PO SCALENIU: 136 -> 137, przeliczone Z DRZEWA scalonego, nie zlozone z dwoch
# galezi — kazda dawala 136 wobec ROZNYCH zbiorow blokow i zadna nie opisuje drzewa,
# ktore powstalo. Zsumowanie przyrostow (+2 i +2) dalo by 138, czyli o jeden za duzo:
# pola „Weryfikacja" obu galezi wolaja `test_all.py`, wiec jeden adres jest WSPOLNY.
# 141 -> 142 (16.09.2026, 6.D228): z tego samego powodu co `ADRESOW_W_WYKONANYCH`
# wyzej — blok 6.D228 przeszedl do populacji WYKONANYCH ze swoim plotkiem
# „Weryfikacja". Podstawienie: bez napisu ZROBIONE czytnik daje z powrotem 141.
# 142 -> 144 (16.09.2026, 6.D239 i 6.D236) i 144 -> 145 PO SCALENIU (6.D230):
# ta sama przyczyna co przy `ADRESOW_W_WYKONANYCH` wyzej i ten sam blad byl tu
# mozliwy — kazda strona konfliktu widziala TYLKO swoje domkniecie i kazda dawala
# 144. Drzewo scalone niesie OBIE adnotacje. Wartosc PRZELICZONA Z DRZEWA po
# scaleniu, nie zsumowana z przyrostow galezi.
# 6.D237 (17.09.2026): „Weryfikacja” 145 -> 164. To JEDYNY skok tej liczby, który
# nie jest przybyciem bloku: `MODULE_CALL` czyta od dziś WSZYSTKIE argumenty
# wywołania, a nie pierwszy, więc te same wiersze oddają o DZIEWIĘTNAŚCIE nazw
# więcej. Policzone PODSTAWIENIEM wzorca, nie odjęciem: ten sam czytnik nad tym
# samym drzewem, raz z dawną postacią jednoargumentową i raz z dzisiejszą, daje
# 145 i 164, `DOSZLO 19`, `UBYLO []`. Dziewiętnaście wywołań dwuargumentowych stoi
# w „Weryfikacji” bloków 6.D138, 6.D144, 6.D151, 6.D162, 6.D163, 6.D192, 6.D193,
# 6.D194, 6.D203, 6.D204, 6.D205, 6.D206, 6.D207, 6.D209, 6.D216, 6.D218, 6.D228
# (dwa) i 6.D230.
#
# **Liczba jest o TRZY większa niż w pomiarze tej pozycji z 16.09.2026 (156 przy
# bazie 140) i nie jest to rozbieżność pomiaru.** Tamten pomiar stał na drzewie,
# w którym 6.D228 i 6.D230 były blokami OTWARTYMI, a ich trzy wywołania dwu-
# argumentowe liczyły się do populacji „wszystkie bloki", nie do „wykonane".
# Scalenie #644 i #646 przeniosło oba bloki do WYKONANYCH razem z ich płotkami —
# ta sama mechanika, którą opisuje komentarz 6.D228 wyżej, tu widoczna po raz piąty.
# Wartość jest PRZELICZONA na dzisiejszym drzewie, a nie przepisana z pomiaru.
#
# Zera w dwóch pozostałych polach NIE DRGAJĄ mimo poszerzenia — patrz
# `test_zero_wywolan_poza_Weryfikacja_jest_STRUKTURALNE`.
# 164 -> 165 (17.09.2026): adnotacja ZROBIONE na wierszu tej pozycji, ta sama
# przyczyna co przy `ADRESOW_W_WYKONANYCH` wyzej. Wywolanie w plotku jest
# JEDNOargumentowe, wiec `nazwy_z_dalszego_argumentu` nie drga i zostaje 19.
# 165 -> 166 (17.09.2026, 6.D238): jak wyzej, jedno wywolanie JEDNOargumentowe
# z plotka „Weryfikacji" tego bloku.
# 166 -> 167 (17.09.2026, 6.D232): jedno wywolanie JEDNOargumentowe z plotka
# „Weryfikacji" bloku tej pozycji, ta sama przyczyna co przy adresach wyzej.
# 169 -> 170 (17.09.2026, 6.D258): jedno wywolanie modulu wiecej —
# `test_tree_walks.py` z plotka „Weryfikacji" bloku tej pozycji.
WYWOLAN_W_WYKONANYCH = {"Wejście": 0, "Wyjście": 0, "Weryfikacja": 170}

#: Ilu kandydatow zlego adresu daje regula prozy, per pole — 6.D158.
# 12 -> 13 (14.09.2026, 6.D204): trzynastym kandydatem jest `test_mutation_sweep.py`
# z plotka „Weryfikacji" bloku tej pozycji — nazwa modulu bez sciezki, ktorej proza
# bloku nie wymienia. Ten sam ksztalt co dwanascie poprzednich (6.D36 i 6.D90 daja go
# na tym samym module), a nie zly adres: plik istnieje i zestaw go uruchamia.
# 13 -> 14 (15.09.2026, 6.D214): czternastym kandydatem jest
# `test_csharp_test_methods.py` z plotka „Weryfikacji" bloku tej pozycji — nazwa
# modulu bez sciezki, ktorej proza bloku nie wymienia. Ten sam ksztalt co
# trzynascie poprzednich, a nie zly adres: plik istnieje i zestaw go uruchamia.
# 14 -> 17 (16.09.2026, 6.D237): trzej nowi kandydaci wchodzą nie z nowego bloku,
# tylko z poszerzenia `MODULE_CALL` na WSZYSTKIE argumenty — `test_timing_record.py`
# z 6.D162 i 6.D194 oraz `test_suite_runtime_budget.py` z 6.D192, każdy stojący na
# DRUGIM miejscu wywołania. Policzone DIFFEM listy: `UBYLO []`. Żaden nie jest złym
# adresem — wszystkie trzy moduły są w drzewie i zestaw je uruchamia; to ten sam
# kształt, co czternaście poprzednich (proza bloku nazywa bramkę po tym, co robi).
KANDYDATOW_W_WYKONANYCH = {"Wejście": 0, "Wyjście": 0, "Weryfikacja": 17}


def adresy_pola_w_wykonanych(pole):
    """`[(numer, sciezka)]` — adresy `PATH_TOKEN` w danym polu blokow wykonanych."""
    out = []
    for numer, body in sorted(bloki_wykonane().items()):
        for trafienie in PATH_TOKEN.finditer(field_body(body, pole)):
            out.append((numer, trafienie.group(1)))
    return out


def wywolania_pola_w_wykonanych(pole):
    """`[(numer, nazwa)]` — wywolania modulu w danym polu blokow wykonanych."""
    out = []
    for numer, body in sorted(bloki_wykonane().items()):
        for nazwa in module_names(field_body(body, pole)):
            out.append((numer, nazwa))
    return out


def kandydaci_pola_w_wykonanych(pole):
    """`[(numer, nazwa)]` — kandydaci zlego adresu regula prozy, w danym polu."""
    out = []
    for numer, body in sorted(bloki_wykonane().items()):
        proza = proza_bloku(body)
        for nazwa in sorted(set(module_names(field_body(body, pole)))):
            rdzen = nazwa[:-3] if nazwa.endswith(".py") else nazwa
            if rdzen not in proza:
                out.append((numer, nazwa))
    return out


def test_ile_adresow_stoi_w_kazdym_z_trzech_pol_blokow_wykonanych():
    """Pole „Wyjscie" 6.D158 zada trzech liczb per pole — z DRZEWA, nie wpisanych."""
    for pole in FIELDS:
        adresy = adresy_pola_w_wykonanych(pole)
        assert len(adresy) == ADRESOW_W_WYKONANYCH[pole], (
            "adresow w polu „%s” jest %d, a pomiar z 12.09.2026 dal %d"
            % (pole, len(adresy), ADRESOW_W_WYKONANYCH[pole]))

        wywolania = wywolania_pola_w_wykonanych(pole)
        assert len(wywolania) == WYWOLAN_W_WYKONANYCH[pole], (
            "wywolan modulu w polu „%s” jest %d, a pomiar dal %d"
            % (pole, len(wywolania), WYWOLAN_W_WYKONANYCH[pole]))

        kandydaci = kandydaci_pola_w_wykonanych(pole)
        assert len(kandydaci) == KANDYDATOW_W_WYKONANYCH[pole], (
            "kandydatow zlego adresu w polu „%s” jest %d, a pomiar dal %d"
            % (pole, len(kandydaci), KANDYDATOW_W_WYKONANYCH[pole]))


def test_jaka_czesc_adresow_obejrzala_regula_kandydatow_6D146():
    """**Pole „Skonczone, gdy" 6.D158 zada UŁAMKA, a nie slowa.**

    Odpowiedz: **101 z 1276, czyli niecale osiem procent.** Pozycja pytala, „czy 92
    to calosc adresow w blokach wykonanych, czy jedna trzecia" — nie jest ani jednym,
    ani drugim. Jest okolo JEDNEJ TRZYNASTEJ; liczac same adresy `.py`, jedna siodma.

    Nie jest to zarzut wobec 6.D146, ktore mierzylo dokladnie to, o co pytalo jego
    wlasne pole „Wyjscie". Jest to liczba, ktorej tamta pozycja nie miala — i bez
    ktorej zdanie „dziesieciu kandydatow da sie przeczytac recznie" brzmi jak zdanie
    o calosci, a jest zdaniem o jednej trzynastej.
    """
    razem = sum(len(adresy_pola_w_wykonanych(p)) for p in FIELDS)
    obejrzane = len(wywolania_pola_w_wykonanych("Weryfikacja"))
    assert razem == sum(ADRESOW_W_WYKONANYCH.values()), (
        "adresow w blokach wykonanych jest %d, a suma rozkladu daje %d"
        % (razem, sum(ADRESOW_W_WYKONANYCH.values())))
    # Ulamek PRZYBITY Z OBU STRON, a nie rownoscia: rownosc na 101/1276 zapalalaby
    # sie przy kazdym dopisanym bloku, a zdanie, ktore ta pozycja stawia, brzmi
    # „okolo jednej trzynastej", nie „dokladnie 101 z 1276". Same liczby stoja
    # przybite rownoscia w `ADRESOW_W_WYKONANYCH` i `WYWOLAN_W_WYKONANYCH`.
    assert obejrzane * 20 > razem, (
        "regula kandydatow obejmuje %d z %d adresow, czyli MNIEJ niz jedna "
        "dwudziesta — zdanie 6.D158 o „jednej trzynastej” opisuje inny stan"
        % (obejrzane, razem))
    assert obejrzane * 8 < razem, (
        "regula kandydatow obejmuje %d z %d adresow, czyli WIECEJ niz jedna osma — "
        "jak wyzej, tylko z drugiej strony" % (obejrzane, razem))


def test_zero_wywolan_poza_Weryfikacja_jest_STRUKTURALNE():
    """**Zero w „Wejsciu" i „Wyjsciu" to nie jest odkrycie o pokryciu — 6.D158.**

    `MODULE_CALL` szuka `test_all.py <modul>` W PLOTKU, czyli WYWOLANIA. Polecenia
    stoja w „Weryfikacji" i tylko tam; „Wejscie" i „Wyjscie" niosą SCIEZKI, a nie
    komendy. Zero jest wiec wlasnoscia PYTANIA, a nie drzewa — i bez tego zdania
    czytaloby sie je jako „w tych polach nie ma adresow", co jest nieprawda: stoi
    ich tam **912**, wiecej niz w „Weryfikacji".

    **Wniosek, ktory z tego plynie, jest o BRAMCE, a nie o liczbie:** rozszerzenie
    reguly kandydatow na pozostale pola nie polega na podaniu jej innej nazwy pola.
    Tam nie ma wywolan do znalezienia — potrzebna byloby REGULA INNEGO KSZTALTU.
    Klasa, ktora 6.D157 wskazalo jako powtarzajaca sie (adres ISTNIEJACY, ale nie ten),
    jest wiec poza zasiegiem wszedzie poza „Weryfikacja".

    Kontrola na wejsciu SYNTETYCZNYM, bo drzewo tych dwoch przypadkow nie rozdziela:
    pole ze sciezka i bez wywolania wyglada w drzewie tak samo jak pole, ktorego
    czytnik nie umie przeczytac.
    """
    ze_sciezka = "- **Wejście:** `tools/tests/test_backlog.py`, `docs/TASKS.md`."
    assert module_names(ze_sciezka) == [], (
        "czytnik wywolan znalazl wywolanie w polu, ktore niesie samą ŚCIEŻKĘ — "
        "wtedy zero w „Wejściu” nie jest strukturalne, tylko przypadkowe")
    assert [m.group(1) for m in PATH_TOKEN.finditer(ze_sciezka)] == [
        "tools/tests/test_backlog.py", "docs/TASKS.md"], (
        "czytnik adresow przestal widziec sciezki w tym samym tekscie — wtedy "
        "porownanie „sciezki sa, wywolan nie ma” nie ma jednej ze stron")

    z_wywolaniem = (
        "- **Weryfikacja:**\n  ```bash\n"
        "  python3 tools/tests/test_all.py test_backlog.py\n  ```")
    assert module_names(z_wywolaniem) == ["test_backlog.py"], (
        "czytnik wywolan przestal widziec wywolanie w plotku — wtedy zero wyzej "
        "jest zerem czytnika, a nie zerem drzewa: %s" % module_names(z_wywolaniem))


# --- 6.D187: gola nazwa pliku, czyli ksztalt, ktorego PATH_TOKEN nie widzi ---------
#
# Pozycja pyta o DWIE LICZBY POLICZONE PRZED zmiana wzorca i o rozstrzygniecie, czy
# poszerzenie da sie zrobic bez listy wyjatkow. Oba stoja nizej, wyprowadzone z drzewa.

#: Alternatywa rozszerzen WYCIETA Z `PATH_TOKEN`, a nie przepisana obok.
#:
#: Druga lista tych samych rozszerzen rozjechalaby sie po cichu z pierwsza, a rozjazd
#: akurat TEJ pary znaczylby, ze jeden ksztalt widzi plik, ktorego drugi nie widzi —
#: czyli dokladnie ten rodzaj roznicy, ktory ta pozycja mierzy. Ze wyciecie naprawde
#: bierze sie ze wzorca, a nie z przypadkowo zgodnego napisu, pilnuje asercja nizej.
ROZSZERZENIA_Z_PATH_TOKEN = re.search(
    r"\\\.\(\?:([a-z|]+)\)", PATH_TOKEN.pattern).group(1)

#: Gola nazwa pliku: JEDEN segment ze znanym rozszerzeniem, bez ukosnika po zadnej
#: stronie. Domkniecie `(?![A-Za-z0-9/])` odsiewa poczatek sciezki (`docs/TASKS.md`
#: nie ma dac `docs`… ani `TASKS.md`), a poprzednik `(?<![A-Za-z0-9_./-])` — ogon
#: sciezki.
BARE_TOKEN = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"([A-Za-z0-9_][A-Za-z0-9_.+-]*\.(?:" + ROZSZERZENIA_Z_PATH_TOKEN + r"))"
    r"(?![A-Za-z0-9/])")

#: PIERWSZA LICZBA POZYCJI — progi KW, nie rownosci, i to jest wybor. `docs/` rosnie
#: z kazda domknieta pozycja, wiec rownosc czerwienialaby od pisania dokumentacji;
#: prog laduje literowke we wzorcu, ktora daje zero, a zero przechodzi „nic nie
#: znaleziono" bez ani jednego sprawdzenia. Zmierzone 13.09.2026: **1331** wystapien
#: golej nazwy w `docs/*.md`, w **276** roznych nazwach.
#:
#: Progu na LICZBE ROZNYCH nazw tu nie ma i to jest wynik pomiaru, nie przeoczenie.
#: Napisalem go najpierw (`MIN_GOLYCH_ROZNYCH = 250`), po czym okazal sie scisle
#: slabszy od rownosci `GOLYCH_BEZ_ODPOWIEDNIKA` nizej: ta liczy sie ZE ZBIORU
#: roznych nazw, wiec zapadniecie sie tego zbioru rusza ja pierwsze. Trzecia wolna
#: zapadka mowiaca to samo slabiej kosztuje wpis w `test_tree_walks.ZAPADKI`
#: i nie daje nic.
MIN_GOLYCH_W_DOKUMENTACH = 1200

#: DRUGA LICZBA POZYCJI — ile z tych roznych nazw NIE MA odpowiednika w drzewie.
#: Rownosc, nie prog: to jest liczba, o ktora pozycja pyta, i kazdy jej ruch ma byc
#: przeczytany. Zmierzone 13.09.2026: **32**.
#:
#: **32 -> 35 (13.09.2026, MB-01), przeczytane po kolei.** Doszly `L1_A.glb`,
#: `M7_shell.glb` i `L1_A-platforms.glb`, wszystkie trzy z wiersza MB-01
#: w `docs/TASKS.md`, gdzie stoja przy ZMIERZONYCH rozmiarach wyjscia skryptu
#: `tools/dev/prepare-playable.sh`. Nowej rodziny nie zakladaja: to druga z czterech
#: juz wymienionych nizej — wytwory przebiegu, ktorych regula 8 zabrania komitowac.
#: Ich obecnosc w drzewie byloby usterka, a NIEobecnosc usterka nie jest.
#: **35 -> 36 (15.09.2026, 6.D221), przeczytane po kolei — a raczej po jednej.**
#: Doszla `plik.cs` z wiersza 6.D221 w `docs/TASKS.md`, gdzie stoi w ksztalcie
#: ``` `plik.cs` (`Nazwa`) ``` jako ZAPIS KONWENCJI pola „Wejscie", a nie jako adres:
#: nazwa opisuje tam wzorzec, ktorym sito przechodzilo po 153 parach. Nowej rodziny
#: nie zaklada — to PIERWSZA z czterech wymienionych nizej, nazwy zastepcze prozy,
#: ta sama co `PLIK.json`, `AXIS.csv` i `a.py`. Plik o tej nazwie w drzewie byloby
#: usterka, bo zdanie mowi o KSZTALCIE nazwy, a nie o pliku.
GOLYCH_BEZ_ODPOWIEDNIKA = 36

#: To samo, ale WYLACZNIE w trzech polach skanowanych — czyli tam, gdzie poszerzony
#: `PATH_TOKEN` naprawde by zapalal. Zmierzone 13.09.2026: **244** wystapienia,
#: **88** roznych nazw, **10** wystapien bez odpowiednika w drzewie.
MIN_GOLYCH_W_POLACH = 200
GOLYCH_W_POLACH_BEZ_ODPOWIEDNIKA = 10

#: Wystapienia bez odpowiednika w polach skanowanych, z powodem — i ANI JEDEN nie
#: jest usterka. To jest ROZSTRZYGNIECIE pozycji, zapisane jako lista, a nie zdanie.
#:
#: Klucz to `(numer, pole, nazwa)`, tak samo jak w `EXCEPTIONS` wyzej i z tego samego
#: powodu: numer wiersza przesuwa kazdy commit dopisujacy cokolwiek wyzej.
NIEISTNIEJACE_W_POLACH = {
    ("6.B1", "Weryfikacja", "AXIS.json"):
        "nazwa zastepcza w szablonie polecenia `--out AXIS.json`; wielkie litery sa "
        "tu konwencja oznaczajaca „podstaw swoja nazwe”, a nie nazwa pliku",
    ("6.B2", "Weryfikacja", "AXIS.json"):
        "ten sam szablon polecenia, co w 6.B1, i ta sama nazwa zastepcza",
    ("6.D1", "Wejście", "PLIK.csv"):
        "nazwa zastepcza wejscia narzedzia; plik o tej nazwie nie powstanie nigdy",
    ("6.D1", "Weryfikacja", "AXIS.csv"):
        "nazwa zastepcza wyjscia w szablonie polecenia tego samego bloku",
    ("6.D1", "Weryfikacja", "AXIS.json"):
        "druga nazwa zastepcza w tym samym szablonie, obok `AXIS.csv`",
    ("6.D59", "Wyjście", "plik.md"):
        "nazwa zastepcza w opisie KSZTALTU wyjscia, a nie adres konkretnego pliku",
    ("6.D86", "Weryfikacja", "test_physics_reference.py"):
        "CYTAT WLASNEJ POPRAWKI: adnotacja „Poprawione 10.09.2026 przy wykonaniu” "
        "przytacza zla nazwe po to, zeby powiedziec, ze ja poprawiono",
    ("6.D89", "Weryfikacja", "test_glossary.py"):
        "CYTAT WLASNEJ POPRAWKI, tak samo jak wyzej: adnotacja z 10.09.2026 "
        "przytacza zla nazwe, zeby zapisac, czym ja zastapiono",
}


def gole_nazwy_w_dokumentach(root=None):
    """`[(plik, nazwa)]` — gole nazwy plikow ze wszystkich `docs/*.md`."""
    root = ROOT if root is None else root
    katalog = os.path.join(root, "docs")
    out = []
    for nazwa_pliku in sorted(os.listdir(katalog)):
        if not nazwa_pliku.endswith(".md"):
            continue
        with open(os.path.join(katalog, nazwa_pliku), encoding="utf-8") as handle:
            tresc = handle.read()
        for trafienie in BARE_TOKEN.finditer(tresc):
            out.append((nazwa_pliku, trafienie.group(1)))
    return out


def _nazwy_plikow_w_drzewie(root=None):
    """Zbior NAZW WLASNYCH plikow sledzonych — bez katalogow."""
    root = ROOT if root is None else root
    return {os.path.basename(p) for p in tw.znajdz(root, "*")}


def gole_nazwy_w_polach(blocks=None):
    """`[(numer, pole, nazwa)]` — gole nazwy w trzech polach skanowanych."""
    out = []
    zrodlo = _all_blocks() if blocks is None else blocks
    for numer, body in zrodlo.items():
        for pole in FIELDS:
            tresc = field_body(body, pole)
            if tresc is None:
                continue
            for trafienie in BARE_TOKEN.finditer(tresc):
                out.append((numer, pole, trafienie.group(1)))
    return out


def test_wzorzec_golej_nazwy_dzieli_rozszerzenia_z_PATH_TOKEN():
    """Jedna lista rozszerzen, nie dwie — 6.D187.

    Wyciecie jest z `PATH_TOKEN.pattern`, wiec dopisanie rozszerzenia do wzorca
    sciezek wchodzi do wzorca golych nazw SAMO. Bez tego byly by dwie listy i ta
    druga starzalaby sie po cichu.

    Kontrola na wejsciu syntetycznym, bo drzewo tych dwoch stron nie rozdziela:
    `PATH_TOKEN` ma widziec sciezke i NIE widziec golej nazwy, `BARE_TOKEN`
    odwrotnie. Gdyby ktorys widzial oba, obie liczby pozycji mierzylyby to samo.
    """
    assert "csproj" in ROZSZERZENIA_Z_PATH_TOKEN and "geojson" in ROZSZERZENIA_Z_PATH_TOKEN, (
        "wyciecie alternatywy z `PATH_TOKEN` nie dalo znanych rozszerzen: %r"
        % ROZSZERZENIA_Z_PATH_TOKEN)
    assert ROZSZERZENIA_Z_PATH_TOKEN in PATH_TOKEN.pattern, (
        "napis z rozszerzeniami nie pochodzi ze wzorca sciezek — wtedy sa dwie listy")

    probka = "plik `docs/TASKS.md`, a obok goly `reference.py` w prozie"
    assert [m.group(1) for m in PATH_TOKEN.finditer(probka)] == ["docs/TASKS.md"], (
        "wzorzec sciezek zaczal widziec gola nazwe albo przestal widziec sciezke: %s"
        % [m.group(1) for m in PATH_TOKEN.finditer(probka)])
    assert [m.group(1) for m in BARE_TOKEN.finditer(probka)] == ["reference.py"], (
        "wzorzec golej nazwy widzi co innego niz gola nazwe: %s"
        % [m.group(1) for m in BARE_TOKEN.finditer(probka)])

    # UKOSNIK W DOMKNIECIU JEST BEZCZYNNY NA DZISIEJSZYM DRZEWIE i to jest zmierzone,
    # a nie domniemane: zdjecie go z `(?![A-Za-z0-9/])` nie ruszylo zadnej z liczb tej
    # sekcji (KN-1). Powod jest strukturalny — ogon sciezki odcina juz POPRZEDNIK
    # `(?<![A-Za-z0-9_./-])`, a nazwa z rozszerzeniem stojaca jako PIERWSZY segment
    # sciezki w tym repozytorium nie pada ani razu.
    #
    # Nie jest to powod, zeby domkniecie zdjac — jest powodem, zeby jego bezczynnosc
    # byla WIDOCZNA. Ta sama decyzja, co przy `RootElement` w 6.D186. Probka jest
    # syntetyczna, bo drzewo tej roznicy nie rozdziela.
    z_ukosnikiem = "sciezka reference.py/dalej w prozie"
    assert [m.group(1) for m in BARE_TOKEN.finditer(z_ukosnikiem)] == [], (
        "gola nazwa zostala zlapana, choc stoi jako PIERWSZY segment sciezki — "
        "domkniecie `(?![A-Za-z0-9/])` przestalo dzialac: %s"
        % [m.group(1) for m in BARE_TOKEN.finditer(z_ukosnikiem)])


def test_ile_golych_nazw_stoi_w_docs_i_ile_z_nich_nie_ma_odpowiednika():
    """PIERWSZA I DRUGA LICZBA POZYCJI, policzone PRZED zmiana wzorca — 6.D187.

    Pole „Wyjscie” zada dwoch liczb: ile golych nazw plikow stoi w skanowanych
    dokumentach i ile z nich wskazuje cos, czego w drzewie nie ma. Zmierzone
    13.09.2026: **1331** wystapien w **276** roznych nazwach, z czego **32** bez
    odpowiednika. Po MB-01 tego samego dnia — **35**; skad te trzy, stoi przy
    `GOLYCH_BEZ_ODPOWIEDNIKA`.

    **Trzydziesci dwie nazwy to nie trzydziesci dwie usterki** i to jest tresc tej
    bramki. Rozkladaja sie na cztery rodziny, z ktorych zadna nie jest bledem:
    nazwy zastepcze prozy (`PLIK.json`, `AXIS.csv`, `a.py`, `d1.csv`, `new.json`),
    wytwory przebiegu, ktorych regula 8 zabrania komitowac (`GODOT_metadata.json`,
    `inspect.png`, `czas-modulow.json`, a od MB-01 takze trzy pliki `.glb`
    pakietu A), wytwory budowania (`Sim.AssemblyInfo.cs`,
    `v10.0.AssemblyAttributes.cs`, `runtimeconfig.json`) i pliki CUDZE
    (`dotnet-install.sh`, `SHA512-SUMS.txt`, `stops.txt` z GTFS-a STIB).
    """
    wystapienia = gole_nazwy_w_dokumentach()
    rozne = {n for _p, n in wystapienia}
    assert len(wystapienia) >= MIN_GOLYCH_W_DOKUMENTACH, (
        "golych nazw w `docs/*.md` jest %d przy progu %d — wzorzec przestal "
        "dopasowywac i zero czytaloby sie jako czysty dokument"
        % (len(wystapienia), MIN_GOLYCH_W_DOKUMENTACH))
    w_drzewie = _nazwy_plikow_w_drzewie()
    brak = sorted(n for n in rozne if n not in w_drzewie)
    assert len(brak) == GOLYCH_BEZ_ODPOWIEDNIKA, (
        "golych nazw bez odpowiednika w drzewie jest %d, a pomiar 6.D187 dal %d: %s"
        % (len(brak), GOLYCH_BEZ_ODPOWIEDNIKA, brak))


def test_w_polach_skanowanych_nie_istnieje_osiem_i_ANI_JEDNA_nie_jest_usterka():
    """ROZSTRZYGNIECIE POZYCJI: nie poszerzamy, i to jest zmierzone — 6.D187.

    Poszerzony `PATH_TOKEN` zapalalby sie wylacznie w trzech polach skanowanych.
    Tam golych nazw jest **244** w **88** roznych, a bez odpowiednika w drzewie —
    **10 wystapien w 8 miejscach**. Przeczytane po kolei: **szesc to nazwy zastepcze
    w szablonach polecen**, a **dwa to CYTATY WLASNEJ POPRAWKI** — adnotacje
    „Poprawione 10.09.2026 przy wykonaniu” przytaczaja zla nazwe po to, zeby
    powiedziec, ze ja poprawiono.

    **Dzisiejszy urobek poszerzenia to zero usterek przy osmiu wyjatkach**, a dwa
    z tych wyjatkow musialyby wyciszyc zdanie, ktore dokumentuje NAPRAWE tej samej
    usterki, o ktorej pozycja jest.

    **Klasa usterek z 6.D157 jest juz lapana, tylko czym innym** — patrz
    `test_ta_klasa_usterek_jest_juz_lapana_regula_INNEGO_ksztaltu`.
    """
    wystapienia = gole_nazwy_w_polach()
    assert len(wystapienia) >= MIN_GOLYCH_W_POLACH, (
        "golych nazw w trzech polach jest %d przy progu %d — zero przeszloby "
        "„nic do poszerzania” bez ani jednego sprawdzenia"
        % (len(wystapienia), MIN_GOLYCH_W_POLACH))

    w_drzewie = _nazwy_plikow_w_drzewie()
    brak = [x for x in wystapienia if x[2] not in w_drzewie]
    assert len(brak) == GOLYCH_W_POLACH_BEZ_ODPOWIEDNIKA, (
        "wystapien bez odpowiednika jest %d, a pomiar 6.D187 dal %d: %s"
        % (len(brak), GOLYCH_W_POLACH_BEZ_ODPOWIEDNIKA, sorted(set(brak))))
    assert sorted(set(brak)) == sorted(NIEISTNIEJACE_W_POLACH), (
        "poszerzony wzorzec zapalilby sie dzis gdzie indziej niz w pomiarze 6.D187: "
        "%s" % sorted(set(brak)))

    bez_powodu = sorted(k for k, v in NIEISTNIEJACE_W_POLACH.items() if len(v) < 20)
    assert not bez_powodu, (
        "wpis bez powodu zapisanego zdaniem: %s — lista, ktorej wpisy nie niosa "
        "powodu, jest lista wyjatkow, a nie pomiarem" % bez_powodu)


def test_w_polach_blokow_OTWARTYCH_nie_ma_ANI_JEDNEJ_golej_nazwy_bez_odpowiednika():
    """Druga polowa rozstrzygniecia — 6.D187.

    Pola blokow OTWARTYCH sa obietnica o przyszlosci, a pola blokow wykonanych —
    zapisem tego, co bylo. Poszerzenie bramki mialoby sens przede wszystkim dla tych
    pierwszych. Zmierzone 13.09.2026: **12 wystapien golej nazwy w 7 roznych,
    ani jedno bez odpowiednika w drzewie**.

    Progu na liczbe wystapien tu NIE MA i to ten sam wybor, co przy `MIN_MODULE_NAMES`:
    kolejka maleje z kazda scalona pozycja, wiec prog czerwienialby od SPRZATANIA.
    Zamiast niego stoi kotwica na wzorcu — ta sama probka, co w bramce wyzej.
    """
    w_drzewie = _nazwy_plikow_w_drzewie()
    brak = [x for x in gole_nazwy_w_polach(_open_blocks())
            if x[2] not in w_drzewie]
    assert brak == [], (
        "pole bloku OTWARTEGO niesie gola nazwe pliku, ktorego w drzewie nie ma: %s"
        % brak)

    probka = "- **Wejście:** `reference.py` i `docs/TASKS.md`."
    assert [m.group(1) for m in BARE_TOKEN.finditer(probka)] == ["reference.py"], (
        "cisza wyzej jest cisza CZYTNIKA, a nie drzewa — wzorzec przestal widziec "
        "gola nazwe w polu")


def test_kontrola_na_wejsciu_syntetycznym_istniejaca_i_wymyslona_daja_INNE_werdykty():
    """Zadanie pola „Weryfikacja” pozycji, wprost — 6.D187.

    Drzewo tych dwoch przypadkow dzis nie rozdziela w polach blokow otwartych: tam
    golych nazw bez odpowiednika jest ZERO, wiec „bramka milczy” bylo by prawda tak
    samo dla czytnika zepsutego.
    """
    w_drzewie = _nazwy_plikow_w_drzewie()
    istniejaca = "- **Wejście:** `test_field_paths.py` opisuje ten ksztalt."
    wymyslona = "- **Wejście:** `test_nie_ma_takiego_modulu.py` opisuje ten ksztalt."

    zlapana_i = [m.group(1) for m in BARE_TOKEN.finditer(istniejaca)]
    zlapana_w = [m.group(1) for m in BARE_TOKEN.finditer(wymyslona)]
    assert zlapana_i == ["test_field_paths.py"], zlapana_i
    assert zlapana_w == ["test_nie_ma_takiego_modulu.py"], zlapana_w

    assert zlapana_i[0] in w_drzewie, (
        "nazwa istniejaca nie zostala uznana za istniejaca — wtedy werdykt jest "
        "zawsze ten sam i rozdzielenie nic nie znaczy")
    assert zlapana_w[0] not in w_drzewie, (
        "nazwa wymyslona zostala uznana za istniejaca — jak wyzej, druga strona")


def test_ta_klasa_usterek_jest_juz_lapana_regula_INNEGO_ksztaltu():
    """DLACZEGO nie poszerzamy: klasa z 6.D157 ma juz swoja bramke — 6.D187.

    Trzy z czterech zlych adresow 6.D157 — `test_physics_reference.py` (6.D86),
    `test_glossary.py` (6.D89), `test_all_self.py` (6.D102) — stalo jako GOLY
    ARGUMENT `test_all.py`, czyli w ksztalcie, ktory `MODULE_CALL` czyta od 6.D101.
    Czwarty (`test_scan_gates.py`, 6.D74) istnieje i jest poza zasiegiem z wlasnego
    pola „Poza zakresem”.

    Kontrola DODATNIA na wejsciu syntetycznym, bo w drzewie nie ma dzis ani jednej
    takiej nazwy do zlapania — wszystkie cztery poprawiono przy ich pozycjach.
    Odtworzony jest tekst pola 6.D86 SPRZED poprawki.

    **Wniosek pozycji:** poszerzenie `PATH_TOKEN` nie dodaje pokrycia tej klasie,
    a dokłada osiem wyjatkow. Regula INNEGO KSZTALTU — ta, ktora czyta wywolanie,
    a nie napis o ksztalcie pliku — jest tu i szczelniejsza, i tansza.
    """
    przed_poprawka = (
        "- **Weryfikacja:**\n  ```bash\n"
        "  python3 tools/tests/test_all.py test_physics_reference.py\n  ```\n"
        "  Oczekiwane: zestaw zielony.\n")
    assert missing_modules({"6.D86-SPRZED": przed_poprawka}) == [
        ("6.D86-SPRZED", "Weryfikacja", "test_physics_reference.py")], (
        "regula wywolan nie lapie nazwy, ktora 6.D157 wymienia jako zly adres — "
        "wtedy zdanie „ta klasa jest juz lapana” jest nieprawda: %s"
        % missing_modules({"6.D86-SPRZED": przed_poprawka}))

    # Druga strona: ta sama nazwa w PROZIE wywolaniem nie jest i lapana byc nie ma.
    w_prozie = "- **Weryfikacja:** pole wolalo `test_physics_reference.py`, a modulu nie ma."
    assert missing_modules({"6.D86-PROZA": w_prozie}) == [], (
        "regula wywolan zglasza CYTAT nazwy w prozie — wtedy zapalilaby sie na "
        "adnotacji, ktora dokumentuje wlasna poprawke")


# --- 6.D189: regula „zly, choc istnieje" dla pola niosacego SCIEZKE ----------------
#
# Pozycja pyta, czy dla pola ze SCIEZKA (a nie z poleceniem) da sie postawic regule
# zly-ale-istniejacy BEZ czytania tresci modulu — z precyzja zmierzona na drzewie,
# a jesli sie nie da, to z zapisana granica. Odpowiedz brzmi: NIE DA SIE, i nizej
# stoi, czym to zmierzono.

#: Oba znane przypadki klasy „adres ISTNIEJE, ale wskazuje co innego" — 6.D157 §3.
#:
#: **Oba stoja w polu „Wejscie" i oba sa JUZ POPRAWIONE.** Dzisiejsze drzewo ma wiec
#: w tych dwoch polach ZERO pozytywow, a precyzja kazdej reguly liczona na nim wynosi
#: `0/N` z konstrukcji — nie dlatego, ze regula jest zla, tylko dlatego, ze nie ma
#: czego trafic. Jedyny sprawdzian, jaki zostaje, to KONTROLA DODATNIA na tekscie
#: odtworzonym SPRZED poprawki; ta sama droga, co przy 6.D187.
ZNANE_POZYTYWY = {
    "6.D73": ("`tools/tests/test_backlog.py` (skan pól i wyjątki ścieżek),\n"
              "  `docs/TASKS.md`, `docs/TASK-TEMPLATE.md`.",
              "tools/tests/test_backlog.py"),
    "6.D74": ("moduły w `tools/tests/test_scan_gates.py` wołające `os.walk`, "
              "`.gitignore`.",
              "tools/tests/test_scan_gates.py"),
}

#: Ile z dwoch znanych pozytywow lapie kazda z dwoch form reguly prozy — 6.D189.
TRAFIEN_FORMA_A = 0
TRAFIEN_FORMA_B = 1

#: Pola niosace SCIEZKE, a nie polecenie.
POLA_SCIEZKOWE = ("Wejście", "Wyjście")


def _rdzen(sciezka):
    """Nazwa pliku bez katalogu i bez rozszerzenia."""
    return os.path.splitext(os.path.basename(sciezka))[0]


def kandydaci_sciezkowi(pole, z_polem):
    """`[(numer, sciezka)]` — kandydaci reguly prozy w polu niosacym sciezke.

    `z_polem=True` to regula W POSTACI, W JAKIEJ STOI dla „Weryfikacji": proza bloku
    liczona w calosci. `z_polem=False` to jedyna nasuwajaca sie poprawka: proza BEZ
    tego pola.
    """
    out = []
    for numer, body in sorted(bloki_wykonane().items()):
        tresc = field_body(body, pole)
        if tresc is None:
            continue
        proza = proza_bloku(body if z_polem else body.replace(tresc, " "))
        for sciezka in sorted(set(paths_in(tresc))):
            if _rdzen(sciezka) not in proza:
                out.append((numer, sciezka))
    return out


def adresy_rozne_w_polu(pole):
    """Ile ROZNYCH adresow stoi w danym polu blokow wykonanych, licząc per blok."""
    ile = 0
    for _numer, body in sorted(bloki_wykonane().items()):
        tresc = field_body(body, pole)
        if tresc is not None:
            ile += len(set(paths_in(tresc)))
    return ile


def test_regula_prozy_W_POSTACI_W_JAKIEJ_STOI_nie_zglasza_dla_pol_sciezkowych():
    """Forma A jest STRUKTURALNIE pusta — i to jest polowa odpowiedzi 6.D189.

    Regula kandydatow porownuje nazwe z PROZA bloku. Dla „Weryfikacji" ma to sens:
    nazwa stoi tam w PLOTKU, a `proza_bloku` plotki wycina, wiec porownywane sa dwie
    rozne rzeczy. W polu niosacym SCIEZKE adres stoi w samej prozie — jest wiec
    SWOIM WLASNYM SWIADKIEM i regula nie moze zglosic niczego.

    Nie jest to prog ostroznosciowy, tylko zmierzony zero: na 894 roznych adresach
    „Wejscia" i 63 „Wyjscia" kandydatow jest **ZERO**. Prog KW na SAM SKAN stoi obok,
    bo zero da sie dostac takze z zepsutego czytnika (6.D27).
    """
    for pole in POLA_SCIEZKOWE:
        adresy = adresy_rozne_w_polu(pole)
        assert adresy >= 50, (
            "w polu „%s” bloków wykonanych widać %d adresów — skan przestał czytać, "
            "a zero kandydatów byłoby wtedy zerem czytnika, nie drzewa"
            % (pole, adresy))
        kandydaci = kandydaci_sciezkowi(pole, z_polem=True)
        assert kandydaci == [], (
            "reguła prozy W POSTACI, W JAKIEJ STOI, zgłosiła coś w polu „%s”: %s — "
            "wtedy adres przestał być swoim własnym świadkiem i cały wywód 6.D189 "
            "opisuje inne drzewo" % (pole, kandydaci))


def test_jedyna_nasuwajaca_sie_poprawka_zglasza_WIEKSZOSC_korpusu():
    """Forma B: proza BEZ pola. Druga polowa odpowiedzi 6.D189.

    Zdjecie pola z prozy naprawia tautologie i natychmiast daje regule, ktora zglasza
    **wiekszosc wszystkich adresow**. Zmierzone 13.09.2026: 570 z 894 w „Wejsciu"
    (64 %) i 23 z 63 w „Wyjsciu" (37 %).

    **Liczby stoja w komunikacie, a asercja pyta o PROPORCJE** i to jest wybor:
    obie rosna z kazda domknieta pozycja, wiec rownosc czerwienialaby od pracy,
    a prog trzeba by rejestrowac jako kolejna wolna zapadke. Tresc pomiaru jest
    proporcja — „regula zglasza wiekszosc" — i ona sie nie zmienia od dopisania bloku.
    """
    wejscie = adresy_rozne_w_polu("Wejście")
    kandydaci = kandydaci_sciezkowi("Wejście", z_polem=False)
    assert len(kandydaci) * 2 > wejscie, (
        "reguła prozy bez pola zgłasza %d z %d adresów „Wejścia” — mniej niż połowę, "
        "a pomiar 6.D189 dał większość (570 z 894). Jeśli udział spadł, jej koszt "
        "trzeba przeliczyć od nowa" % (len(kandydaci), wejscie))
    assert len(kandydaci) < wejscie, (
        "reguła zgłasza WSZYSTKIE %d adresów — wtedy nie jest regułą, tylko "
        "przepisaniem korpusu" % wejscie)


def test_kontrola_DODATNIA_na_tekscie_odtworzonym_SPRZED_poprawki():
    """Ani jedna, ani druga forma nie nadaje sie na bramke — 6.D189.

    **Dzisiejsze drzewo ma zero pozytywow**, bo oba znane przypadki poprawiono. Precyzja
    liczona na nim wynosi `0/N` z konstrukcji i nie mowi o regule nic. Sprawdzian idzie
    wiec na tekscie odtworzonym SPRZED poprawki — ta sama droga, co kontrola dodatnia
    przy 6.D187.

    Wynik: **forma A lapie 0 z 2**, forma B — **1 z 2**.

    **Dlaczego forma B nie lapie 6.D74, jest wazniejsze niz to, ze nie lapie.** Blok
    niesie DRUGA adnotacje poprawki, w polu „Weryfikacja", i ta adnotacja CYTUJE ten
    sam zly adres. Nazwa stoi wiec w prozie — wstawiona tam przez ZAPIS NAPRAWY.
    Jest to ten sam wzorzec, co przy 6.D187, tylko odwrocony: tam adnotacja o poprawce
    KAZALA regule zapalic sie na zapisie naprawy, tu KAZE jej zamilknac na adresie.
    Wspolna przyczyna: adnotacja jest proza o zlym adresie, a kazda regula czytajaca
    proze sie o nia potyka.

    **ROZSTRZYGNIECIE POZYCJI:** dla pola niosacego sciezke reguly zly-ale-istniejacy
    postawic sie NIE DA bez czytania tresci modulu. Forma A nie zglasza nigdy; forma B
    zglasza wiekszosc korpusu i mimo to gubi polowe znanych pozytywow. Regula
    rozstrzygajaca musialaby porownac adres z TYM, CO NAZYWA — czyli przeczytac modul,
    co wyklucza pole „Poza zakresem" tej pozycji i 6.D101.
    """
    wykonane = bloki_wykonane()
    trafien = {"A": 0, "B": 0}
    for numer, (sprzed, zly) in sorted(ZNANE_POZYTYWY.items()):
        body = wykonane[numer]
        pole_dzis = field_body(body, "Wejście")
        assert pole_dzis is not None, numer

        # Podstawienie MUSI byc widoczne: zly adres ma stac w odtworzonym tekscie,
        # a dzisiejszy — nie. Bez tego odtworzenie bylo by cichym no-opem, na czym
        # to samo podstawienie potknelo sie raz przy pisaniu tej bramki.
        assert zly in sprzed, (
            "odtworzony tekst pola %s nie niesie złego adresu `%s` — kontrola "
            "dodatnia mierzyłaby wtedy tekst dzisiejszy" % (numer, zly))
        # Samo „zły adres stoi w odtworzeniu" NIE WYSTARCZA i pokazała to KN-2:
        # dzisiejsze pole też go niesie — w adnotacji poprawki — więc podstawienie
        # `sprzed = pole_dzis` przechodziło tamtą asercję i całą bramkę, mierząc
        # tekst DZISIEJSZY pod nazwą „sprzed". Odtworzenie musi się od dzisiejszego
        # RÓŻNIĆ i nie może nieść adnotacji, której wtedy jeszcze nie było.
        assert sprzed != pole_dzis, (
            "odtworzenie pola %s jest identyczne z tekstem dzisiejszym — kontrola "
            "dodatnia nie mierzy wtedy stanu sprzed poprawki" % numer)
        assert "**Poprawione" not in sprzed, (
            "odtworzenie pola %s niesie adnotację poprawki, której przed poprawką "
            "być nie mogło" % numer)
        # Porownanie idzie do pola BEZ ADNOTACJI poprawki i to nie jest wygoda:
        # adnotacja CYTUJE zly adres, zeby powiedziec, ze go poprawiono, wiec
        # w polu dzisiejszym on stoi — pierwsza wersja tej asercji wywrocila sie
        # na 6.D73 dokladnie z tego powodu. Ten sam cytat jest zreszta przyczyna,
        # dla ktorej forma B gubi 6.D74; tam stoi w polu obok.
        at = pole_dzis.find("**Poprawione")
        pole_bez_adnotacji = pole_dzis if at < 0 else pole_dzis[:at]
        assert zly not in pole_bez_adnotacji, (
            "zły adres `%s` wrócił do dzisiejszego pola %s poza adnotacją poprawki"
            % (zly, numer))

        reszta = proza_bloku(body.replace(pole_dzis, " "))
        formy = {"A": proza_bloku(sprzed + reszta), "B": reszta}
        for forma, proza in formy.items():
            zgloszone = [s for s in sorted(set(paths_in(sprzed)))
                         if _rdzen(s) not in proza]
            if zly in zgloszone:
                trafien[forma] += 1

    assert trafien["A"] == TRAFIEN_FORMA_A, (
        "forma A łapie dziś %d z %d znanych pozytywów, a pomiar dał %d"
        % (trafien["A"], len(ZNANE_POZYTYWY), TRAFIEN_FORMA_A))
    assert trafien["B"] == TRAFIEN_FORMA_B, (
        "forma B łapie dziś %d z %d znanych pozytywów, a pomiar dał %d"
        % (trafien["B"], len(ZNANE_POZYTYWY), TRAFIEN_FORMA_B))

    # POWOD chybienia formy B na 6.D74 — zapisany jako asercja, nie jako zdanie.
    body74 = wykonane["6.D74"]
    poza_wejsciem = proza_bloku(body74.replace(field_body(body74, "Wejście"), " "))
    assert "test_scan_gates" in poza_wejsciem, (
        "w bloku 6.D74 poza polem „Wejście” nie ma już nazwy `test_scan_gates` — "
        "wtedy powód, dla którego forma B go nie łapie, jest inny niż zmierzony")

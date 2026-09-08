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

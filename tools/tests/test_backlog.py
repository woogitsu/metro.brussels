#!/usr/bin/env python3
"""Zapas pracy, którego nie da się przeoczyć między sesjami.

`docs/TASKS.md` niesie regułę: agent nigdy nie ma mniej niż 24 godziny pracy przed
sobą, a uzupełnienie zapasu jest zadaniem samo w sobie. Reguła zapisana w dokumencie
i nigdzie niesprawdzana jest życzeniem — ten test robi z niej bramkę.

Powód nie jest wydajnościowy. Agent, który skończył kolejkę, ma do wyboru stanąć albo
wymyślić sobie zadanie na miejscu. Drugie jest gorsze: zadanie wymyślone w pośpiechu
omija format z sekcji 6 `CLAUDE.md` i ląduje w kodzie, którego nikt nie prosił o zmianę.

Do 05.09.2026 ten plik liczył WYŁĄCZNIE, ile pozycji stoi w kolejce — nigdy, czy
pozycja jest zadaniem. Zmierzone tego dnia: wycięcie z `docs/TASKS.md` całej sekcji
`#### Szczegóły ośmiu pozycji dopisanych 04.09.2026`, **15 802 znaki** z sześcioma
polami dla ośmiu pozycji, przechodziło **1467/1467** testów. Licznik widział 33 wiersze
tabel tak samo przed wycięciem, jak po nim, bo wiersz tabeli zostaje wierszem tabeli
niezależnie od tego, czy gdziekolwiek w pliku stoi opis, jak to zadanie wykonać.

Stąd druga połowa tego pliku: `detail_sections` czyta bloki `##### <numer> · …`
i sprawdza sześć pól z `docs/TASK-TEMPLATE.md`. Numery liczone do zapasu i numery
udokumentowane to **dwie różne liczby** — pierwsza mówi, ile pozycji ktoś wpisał,
druga, ile z nich da się wziąć bez dopytywania właściciela.

Pozycja ODHACZONA jest z tego wymagania wyłączona **jawnie**, a nie przez przeoczenie:
domknięte numery stoją w tabeli `#### Domknięte i zdjęte z kolejki`, której kolumny to
`| # | co było | gdzie zostało zrobione |`. Tam nie ma sześciu pól i nie ma ich mieć —
odpowiednikiem „Wyniku" z `docs/TASK-TEMPLATE.md` jest trzecia kolumna, a `ready_items`
i tak wyklucza te numery z licznika. Wymaganie sześciu pól obowiązuje dokładnie te
pozycje, które licznik zapasu liczy.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TASKS = os.path.join(ROOT, "docs", "TASKS.md")

# Próg z `docs/TASKS.md`. Przy 20-45 minutach na zadanie z pełną weryfikacją
# dwanaście pozycji to dolna granica doby pracy — a część pozycji to generatory,
# więc realny zapas jest większy.
MINIMUM_READY_ITEMS = 12

# Zadania, które mają być KOLEJKĄ. Sekcja „Czego agent nie ruszy bez decyzji"
# celowo NIE jest tu wymieniona: jej pozycje czekają na właściciela i nie są pracą,
# po którą agent może sięgnąć.
QUEUE_PREFIXES = ("5.", "6.")

#: Nagłówek tabeli kolejki. Służy do jednego: sprawdzenia, że wycinanie sekcji
#: domknięć nie zabrało ze sobą tabeli, z której ta sekcja pochodzi.
QUEUE_TABLE_HEADER = "| # | zadanie |"

#: Sześć pól z `CLAUDE.md` §6 i `docs/TASK-TEMPLATE.md`, dokładnie w tym brzmieniu,
#: w jakim stoją w `docs/TASKS.md`: `- **Wejście:** …`.
REQUIRED_FIELDS = (
    "Wejście",
    "Wyjście",
    "Weryfikacja",
    "Skończone, gdy",
    "Poza zakresem",
    "Zależy od",
)

#: Ile pozycji kolejki ma DZIŚ komplet sześciu pól. Zmierzone 05.09.2026 na `b41c158`:
#: 8 z 33. To jest zapadka, nie cel — wolno ją tylko podnosić. Celem jest
#: `MINIMUM_READY_ITEMS`, czyli tyle udokumentowanych pozycji, ile licznik zapasu
#: uznaje za dobę pracy; brakujące cztery są **znaleziskiem do zgłoszenia**, nie
#: zaproszeniem do wymyślenia treści (`CLAUDE.md` §8 zabrania brać zadanie wymyślone
#: na miejscu, a dopisanie sobie „Weryfikacji" do cudzej pozycji jest tym samym).
MINIMUM_DOCUMENTED_ITEMS = 8

#: Zdanie, które musi stać w `docs/TASKS.md`, dopóki zapadka nie dojdzie do progu.
#: Gdy ktoś podniesie `MINIMUM_DOCUMENTED_ITEMS` do `MINIMUM_READY_ITEMS`, ma je
#: usunąć — inaczej plan niesie nieprawdę o samym sobie.
SHORTFALL_MARKER = "**Zapas udokumentowany:**"


def _tasks():
    with open(TASKS, encoding="utf-8") as handle:
        return handle.read()


def queue_items(text):
    """Numery pozycji kolejki, np. ['5.1', '6.A1'] — wiersze tabel `| 5.x |` i `| 6.x |`."""
    found = []
    for line in text.splitlines():
        match = re.match(r"^\|\s*(\d+\.[A-Za-z]?\d+)\s*\|", line)
        if match and match.group(1).startswith(QUEUE_PREFIXES):
            found.append(match.group(1))
    return found


def _section(text, heading, stop_prefixes):
    """Treść sekcji od `heading` do pierwszego kolejnego nagłówka z `stop_prefixes`."""
    start = text.find(heading)
    if start < 0:
        return ""
    rest = text[start + len(heading):]
    ends = [rest.find(prefix) for prefix in stop_prefixes]
    ends = [e for e in ends if e >= 0]
    return rest if not ends else rest[:min(ends)]


def blocked_section(text):
    """Treść sekcji „Czego agent nie ruszy bez decyzji"."""
    return _section(text, "### Czego agent nie ruszy bez decyzji", ["\n### "])


def closed_section(text):
    """Treść sekcji „Domknięte i zdjęte z kolejki".

    Zatrzymuje się na nagłówku CZWARTEGO poziomu też, nie tylko trzeciego: sekcja
    domknięć jest `####` i stoi wewnątrz fazy 5, więc szukanie samego `\n### `
    wciągnęłoby resztę fazy razem z jej tabelą pozycji — czyli wykluczyłoby
    z licznika dokładnie tę kolejkę, której ma pilnować.
    """
    return _section(text, "#### Domknięte i zdjęte z kolejki", ["\n### ", "\n#### "])


def ready_items(text):
    """Pozycje kolejki, które są PRACĄ: bez zablokowanych i bez domkniętych."""
    excluded = set(queue_items(blocked_section(text))) | set(queue_items(closed_section(text)))
    return [item for item in queue_items(text) if item not in excluded]


def detail_sections(text):
    """Bloki `##### <numer> · tytuł` → treść, np. {'6.A8': '##### 6.A8 · …\n- …'}.

    Blok kończy się na PIERWSZYM kolejnym nagłówku dowolnego poziomu, nie tylko
    piątego: sekcja szczegółów jest ostatnia w fazie 6 i sąsiaduje z `### Czego agent
    nie ruszy bez decyzji`, więc szukanie samego `\n##### ` wciągnęłoby do ostatniej
    pozycji całą listę decyzji właściciela — i „Zależy od" znalazłoby się tam, gdzie
    go nie ma.
    """
    lines = text.splitlines()
    heads = [(i, m.group(1)) for i, line in enumerate(lines)
             for m in [re.match(r"^#####\s+(\d+\.[A-Za-z]?\d+)\s*·", line)] if m]
    sections = {}
    for position, (start, number) in enumerate(heads):
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if lines[j].startswith("#"):
                end = j
                break
        sections[number] = "\n".join(lines[start:end])
    return sections


def missing_fields(body):
    """Których z sześciu pól brakuje w bloku — pusta lista znaczy komplet.

    Pole musi mieć TREŚĆ, nie tylko nagłówek. `- **Weryfikacja:**` bez niczego dalej
    jest dokładnie tym, przed czym `CLAUDE.md` §6 ostrzega: polem odhaczonym zamiast
    wypełnionego.
    """
    missing = []
    for field in REQUIRED_FIELDS:
        marker = "- **%s:**" % field
        at = body.find(marker)
        if at < 0:
            missing.append(field)
            continue
        rest = body[at + len(marker):]
        nxt = re.search(r"\n- \*\*", rest)
        if not (rest if nxt is None else rest[:nxt.start()]).strip():
            missing.append(field)
    return missing


def documented_items(text):
    """Pozycje liczone do zapasu, które mają komplet sześciu pól z `CLAUDE.md` §6."""
    sections = detail_sections(text)
    return [item for item in ready_items(text)
            if item in sections and not missing_fields(sections[item])]


def test_tasks_file_exists():
    assert os.path.isfile(TASKS), TASKS


def test_the_reserve_rule_is_written_down():
    text = _tasks()
    assert "### Reguła zapasu" in text, "reguła zapasu zniknęła z planu"
    assert "24 godzin" in text or "24 godziny" in text, "reguła bez liczby godzin"


def test_the_queue_holds_at_least_a_day_of_work():
    items = ready_items(_tasks())
    assert len(items) >= MINIMUM_READY_ITEMS, (
        f"kolejka ma {len(items)} pozycji przy progu {MINIMUM_READY_ITEMS}; "
        "pierwszym zadaniem jest uzupełnienie fazy 6, nie zatrzymanie się")


def test_queue_numbers_are_unique():
    # Dwie pozycje o tym samym numerze to jedna pozycja policzona dwa razy —
    # zapas wyglądałby na większy, niż jest.
    items = queue_items(_tasks())
    assert len(items) == len(set(items)), (
        f"powtórzone numery: {[i for i in set(items) if items.count(i) > 1]}")


def test_every_queue_item_says_why_it_needs_no_decision():
    # Pozycja bez tej kolumny to pozycja, której nikt nie sprawdził pod kątem tego,
    # czy naprawdę da się ją zrobić bez właściciela. Taka trafia do kolejki i blokuje
    # ją dopiero wtedy, gdy agent po nią sięgnie.
    text = _tasks()
    for line in text.splitlines():
        if re.match(r"^\|\s*\d+\.[A-Za-z]?\d+\s*\|", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            assert len(cells) >= 3, f"pozycja bez kolumny uzasadnienia: {line[:60]}"
            assert cells[2], f"puste uzasadnienie: {line[:60]}"


def test_blocked_work_is_not_counted_as_queue():
    # Kontrola negatywna do progu. Gdyby licznik zaglądał również do sekcji
    # „Czego agent nie ruszy bez decyzji", zapas rósłby o zadania, których
    # agent z definicji nie może wykonać — i bramka byłaby zielona przy pustej kolejce.
    blocked = blocked_section(_tasks())
    assert blocked, "sekcja o decyzjach właściciela zniknęła"
    assert not queue_items(blocked), (
        "pozycje z sekcji decyzji właściciela wpadają do licznika kolejki")


def test_closed_work_is_not_counted_as_queue():
    """Domknięcie pozycji ma zapas OBNIŻAĆ, a nie podnosić.

    Wiersz `| 6.C1 | ... |` wygląda dla parsera identycznie niezależnie od tego,
    w której tabeli stoi. Bez tego wykluczenia przeniesienie pozycji do sekcji
    domknięć zostawiało ją w liczniku — zmierzone 04.09.2026 przy zamykaniu 5.5,
    6.C1 i 6.C2: licznik pokazywał 28 przy 25 pozycjach realnych, czyli dokładnie
    tyle, ile przed domknięciem czegokolwiek.
    """
    text = _tasks()
    closed = closed_section(text)
    assert closed, "sekcja domknięć zniknęła z planu"

    numbers = queue_items(closed)
    assert numbers, "sekcja domknięć nie wymienia ani jednego numeru"

    ready = ready_items(text)
    for number in numbers:
        assert number not in ready, f"{number} jest domknięte, a nadal liczy się do zapasu"
    assert len(ready) < len(queue_items(text)), (
        "wykluczenie niczego nie odejmuje — licznik liczy domknięte razem z gotowymi")


def test_the_closed_section_stands_below_the_queue_it_is_carved_out_of():
    """Wycinanie sekcji domknięć nie może zabrać ze sobą tabeli kolejki.

    Dziś nie zabiera — ale NIE dzięki liście nagłówków zamykających, tylko dzięki
    POŁOŻENIU: sekcja `#### Domknięte` stoi pod tabelą fazy 5, więc poniżej niej
    nie ma już ani jednego wiersza `| 5.x |`. Pierwsza wersja tego testu twierdziła,
    że pilnuje listy nagłówków, i była fałszywa: usunięcie `"\n#### "` z `closed_section`
    NIE wywracało jej ani razu, bo nie było czego pochłonąć. Zmierzone, nie wyczytane.

    Ten test pilnuje więc tego, co naprawdę trzyma licznik w ryzach. Gdyby sekcja
    domknięć trafiła NAD tabelę, wycinanie zabrałoby całą kolejkę fazy 5 i próg
    spełniałby się na samej fazie 6 — czyli bramka byłaby zielona przy zapasie
    mniejszym, niż pokazuje.
    """
    text = _tasks()
    assert "#### Domknięte i zdjęte z kolejki" in text, "sekcja domknięć zniknęła z planu"

    # Wprost: wycięty blok nie ma prawa zawierać NAGŁÓWKA tabeli kolejki. Gdyby
    # sekcja domknięć stała nad tabelą, wycinanie zabrałoby nagłówek i wszystkie
    # wiersze pod nim — i to jest jedyny objaw, który widać z samego pliku.
    carved = closed_section(text)
    assert QUEUE_TABLE_HEADER not in carved, (
        "sekcja domknięć stoi NAD tabelą kolejki i wycinanie zabiera ją razem z sobą")

    # I skutek tego położenia: każda niedomknięta pozycja 5.x zostaje w zapasie.
    closed_numbers = set(queue_items(carved))
    ready = ready_items(text)
    phase_five = [i for i in queue_items(text)
                  if i.startswith("5.") and i not in closed_numbers]
    assert phase_five, "faza 5 nie ma ani jednej niedomkniętej pozycji"
    for item in phase_five:
        assert item in ready, f"{item} z fazy 5 wypadło z zapasu"


def test_the_parser_actually_parses():
    # Kontrole negatywne samego licznika. Bez nich testy wyżej przechodziłyby także
    # wtedy, gdyby `queue_items` zwracał pustą listę na wszystkim albo łapał co popadnie.
    assert queue_items("| 5.1 | coś | bo tak |") == ["5.1"]
    assert queue_items("| 6.A1 | coś | bo tak |") == ["6.A1"]
    assert queue_items("| 6.B12 | coś | bo tak |") == ["6.B12"]
    assert queue_items("| # | zadanie | dlaczego |") == [], "nagłówek tabeli nie jest pozycją"
    assert queue_items("| 4.1 | stara faza |") == [], "faza spoza kolejki nie liczy się"
    assert queue_items("tekst 5.1 w zdaniu") == [], "wzmianka w prozie nie jest pozycją"
    assert queue_items("|---|---|---|") == [], "separator tabeli nie jest pozycją"


def test_the_threshold_is_not_trivially_satisfied():
    # Próg, który spełnia się sam, nie jest progiem. Ten test pada, gdyby ktoś
    # obniżył `MINIMUM_READY_ITEMS` do wartości, przy której bramka nigdy nie zaświeci.
    assert MINIMUM_READY_ITEMS >= 12, (
        "próg poniżej dwunastu pozycji przestaje odpowiadać dobie pracy")


# ---------------------------------------------------------------------------
# Format pozycji, a nie tylko jej liczba.
# ---------------------------------------------------------------------------


def test_the_detail_scan_actually_finds_something():
    """Bramka bez przedmiotu ma PAŚĆ, nie przechodzić na pustym zbiorze.

    To jest ta sama pułapka, którą ten plik już raz złapał przy sekcji domknięć,
    tylko o poziom wyżej. Gdyby ktoś zmienił poziom nagłówka `#####` na `####`,
    przeniósł szczegóły do osobnego pliku albo wyciął całą sekcję — `detail_sections`
    zwróciłoby `{}`, a test „każdy blok ma sześć pól" byłby zielony, bo nie miałby
    czego sprawdzić. Zmierzone 05.09.2026: wycięcie 15 802 znaków tej sekcji
    przechodziło 1467/1467.
    """
    sections = detail_sections(_tasks())
    assert len(sections) >= MINIMUM_DOCUMENTED_ITEMS, (
        f"skan znalazł {len(sections)} bloków szczegółów przy zapadce "
        f"{MINIMUM_DOCUMENTED_ITEMS}; albo sekcja z sześcioma polami zniknęła "
        "lub zmieniła kształt nagłówka i bramka przestała mieć na co patrzeć, "
        "albo ktoś podniósł zapadkę bez dopisania bloków")


def test_every_detail_block_carries_all_six_fields():
    # Blok, który ma nagłówek i trzy pola, jest gorszy niż brak bloku: wygląda
    # na wypełniony i przechodzi wzrokiem. Sześć pól albo żadnego.
    for number, body in sorted(detail_sections(_tasks()).items()):
        missing = missing_fields(body)
        assert not missing, f"{number} bez pól: {', '.join(missing)}"


def test_no_detail_block_describes_a_number_that_left_the_tables():
    # Odwrotna strona tego samego rozjazdu: opis został, wiersz zniknął.
    # Taki blok wygląda jak zadanie do wzięcia, a nie ma go w żadnej kolejce.
    text = _tasks()
    numbers = set(queue_items(text))
    for number in sorted(detail_sections(text)):
        assert number in numbers, (
            f"blok szczegółów {number} nie ma wiersza w żadnej tabeli")


def test_the_documented_reserve_does_not_regress():
    """Zapadka na liczbie pozycji, które naprawdę da się wziąć.

    `MINIMUM_READY_ITEMS` mówi, ile pozycji ktoś WPISAŁ. Ta liczba mówi, ile z nich
    niesie sześć pól, czyli ile agent może wziąć bez dopytywania właściciela.
    Zmierzone 05.09.2026 na `b41c158`: **8 z 33**. Wolno tylko podnosić — a podnosi
    się ją, dopisując pola tam, gdzie da się je ODCZYTAĆ z `docs/`, `reports/`
    i `data/`, nie zmyślając ich.
    """
    text = _tasks()
    documented = documented_items(text)
    assert len(documented) >= MINIMUM_DOCUMENTED_ITEMS, (
        f"pozycji z kompletem sześciu pól jest {len(documented)} "
        f"przy zapadce {MINIMUM_DOCUMENTED_ITEMS}: "
        f"{sorted(set(ready_items(text)) - set(documented))} są bez kompletu")


def test_the_documented_shortfall_is_written_down_while_it_lasts():
    """Różnica między zapadką a progiem nie ma prawa zniknąć po cichu.

    Dziś zapadka stoi na 8, a próg zapasu na 12 — cztery pozycje kolejki są
    wierszem tabeli bez opisu, jak je wykonać. Dopóki tak jest, `docs/TASKS.md`
    ma to mówić wprost. Gdy ktoś doprowadzi zapadkę do progu, ma ten akapit
    usunąć: plan, który po domknięciu luki nadal ją opisuje, jest tak samo
    nieprawdziwy jak plan, który jej nigdy nie opisał.
    """
    text = _tasks()
    if MINIMUM_DOCUMENTED_ITEMS < MINIMUM_READY_ITEMS:
        assert SHORTFALL_MARKER in text, (
            "zapas udokumentowany jest poniżej progu, a plan o tym milczy")
    else:
        assert SHORTFALL_MARKER not in text, (
            "zapadka doszła do progu, a plan nadal opisuje lukę")


def test_the_ratchet_cannot_be_set_above_what_it_guards():
    # Zapadka wyższa od progu zapasu byłaby wymaganiem bez pokrycia w regule:
    # `docs/TASKS.md` żąda dwunastu pozycji, nie dwudziestu udokumentowanych.
    assert 0 < MINIMUM_DOCUMENTED_ITEMS <= MINIMUM_READY_ITEMS, (
        "zapadka udokumentowanych stoi poza przedziałem (0, próg zapasu]")


def test_closed_items_are_exempt_from_the_six_fields_on_purpose():
    """Rozstrzygnięcie wprost: pozycja ODHACZONA nie ma sześciu pól i nie ma ich mieć.

    `docs/TASK-TEMPLATE.md` daje pozycji niezrobionej sześć pól, a zrobionej dokłada
    „Wynik". W tabelach 5.x/6.x odpowiednikiem „Wyniku" jest trzecia kolumna tabeli
    domknięć — `| # | co było | gdzie zostało zrobione |`. Wymaganie kompletu
    dotyczy więc dokładnie `ready_items`, i ten test pilnuje, żeby to zwolnienie
    było ŻYWE: gdyby wszystkie domknięte numery miały nagle bloki szczegółów,
    zwolnienie byłoby martwym zapisem i nikt by nie zauważył, że przestało cokolwiek
    znaczyć.
    """
    text = _tasks()
    closed = queue_items(closed_section(text))
    assert closed, "sekcja domknięć nie wymienia ani jednego numeru"

    sections = detail_sections(text)
    without = [n for n in closed if n not in sections]
    assert without, (
        "każdy domknięty numer ma blok szczegółów — zwolnienie z sześciu pól "
        "przestało cokolwiek zwalniać")

    documented = set(documented_items(text))
    for number in closed:
        assert number not in documented, (
            f"{number} jest domknięte, a liczy się do zapasu udokumentowanego")

    # I to, co domknięta pozycja mieć MUSI zamiast sześciu pól: wskazanie, gdzie
    # została zrobiona. Pusta trzecia kolumna zamieniłaby tabelę domknięć
    # w listę numerów bez śladu po pracy.
    for line in closed_section(text).splitlines():
        if re.match(r"^\|\s*\d+\.[A-Za-z]?\d+\s*\|", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            assert len(cells) >= 3 and cells[2], (
                f"domknięta pozycja bez wskazania, gdzie ją zrobiono: {line[:60]}")


def test_the_field_parser_actually_parses():
    # Kontrole negatywne samego czytnika pól. Bez nich testy wyżej przechodziłyby
    # także wtedy, gdyby `missing_fields` zwracał pustą listę na wszystkim.
    complete = "\n".join("- **%s:** treść." % f for f in REQUIRED_FIELDS)
    assert missing_fields(complete) == []
    assert missing_fields("") == list(REQUIRED_FIELDS), "pusty blok ma być bez pól"
    assert missing_fields(complete.replace("- **Wyjście:** treść.", "")) == ["Wyjście"]
    assert missing_fields(complete.replace("- **Weryfikacja:** treść.",
                                           "- **Weryfikacja:**")) == ["Weryfikacja"], \
        "sam nagłówek pola bez treści nie jest polem"
    assert missing_fields("Wejście: bez pogrubienia") == list(REQUIRED_FIELDS), \
        "wzmianka w prozie nie jest polem"

    # I czytnik bloków.
    sample = ("##### 6.Z9 · tytuł\n- **Wejście:** a\n"
              "### inny nagłówek\n- **Wyjście:** nie moje\n")
    parsed = detail_sections(sample)
    assert list(parsed) == ["6.Z9"], parsed
    assert "nie moje" not in parsed["6.Z9"], "blok przelewa się przez nagłówek"
    assert detail_sections("#### 6.Z9 · zły poziom") == {}, \
        "nagłówek innego poziomu nie jest blokiem szczegółów"
    assert detail_sections("##### T-010 · nie numer kolejki") == {}


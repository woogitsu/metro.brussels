#!/usr/bin/env python3
"""Zapas pracy, którego nie da się przeoczyć między sesjami.

`docs/TASKS.md` niesie regułę: agent nigdy nie ma mniej niż 24 godziny pracy przed
sobą, a uzupełnienie zapasu jest zadaniem samo w sobie. Reguła zapisana w dokumencie
i nigdzie niesprawdzana jest życzeniem — ten test robi z niej bramkę.

Powód nie jest wydajnościowy. Agent, który skończył kolejkę, ma do wyboru stanąć albo
wymyślić sobie zadanie na miejscu. Drugie jest gorsze: zadanie wymyślone w pośpiechu
omija format z sekcji 6 `CLAUDE.md` i ląduje w kodzie, którego nikt nie prosił o zmianę.
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

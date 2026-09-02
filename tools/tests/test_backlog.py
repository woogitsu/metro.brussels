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


def blocked_section(text):
    """Treść sekcji „Czego agent nie ruszy bez decyzji"."""
    start = text.find("### Czego agent nie ruszy bez decyzji")
    if start < 0:
        return ""
    rest = text[start + 1:]
    end = rest.find("\n### ")
    return rest if end < 0 else rest[:end]


def test_tasks_file_exists():
    assert os.path.isfile(TASKS), TASKS


def test_the_reserve_rule_is_written_down():
    text = _tasks()
    assert "### Reguła zapasu" in text, "reguła zapasu zniknęła z planu"
    assert "24 godzin" in text or "24 godziny" in text, "reguła bez liczby godzin"


def test_the_queue_holds_at_least_a_day_of_work():
    items = queue_items(_tasks())
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

#!/usr/bin/env python3
"""Zadanie, które `doctor.sh` podaje nowej sesji, nie może już leżeć w `main`.

Zmierzone 05.09.2026 na `e413bb1`. `doctor.sh` kończył się wierszem

    Baza projektu jest gotowa. Następne zadanie: T-212 · Pierwsza stacja typowa — **ODBLOKOWANE**

a T-212 było scalone **04.09.2026** jako #137 (`fe14d72`), i od tamtej pory doszły
jeszcze #223 (peron w scenie Godota) i #225 (95,0 m dociera do pipeline'u). Pierwszą
rzeczą, jaką widziała każda nowa sesja po `bash doctor.sh`, było więc polecenie
zrobienia pracy, która już leży w `main`.

Sam `doctor.sh` nic tu nie zawinił i nie ma czego w nim poprawiać: komentarz nad tym
kawałkiem mówi wprost, że nazwa zadania jest czytana z rozpiski właśnie po to, żeby
nie zastygła — „wpisane na sztywno przestaje być prawdą pierwszego dnia po zrobieniu
tego zadania". Czyta więc prawdziwy plik, a plik kłamał. Bramka musi stać po stronie
pliku.

Co ta bramka sprawdza — i czego NIE sprawdza
--------------------------------------------
Sprawdza **dokładnie ten zbiór wpisów, który `doctor.sh` może wymienić**: niezahaczone
`### [ ]` bez `ZABLOKOWANE` i bez `CZŁOWIEK`. Dla każdego z nich pyta, czy w repozytorium
leży ślad wykonania. Ślady są dwa i są niezależne:

1. **pole „Wynik”** w treści wpisu — `docs/TASK-TEMPLATE.md` dokłada je do wpisu
   odhaczonego, a `tools/tests/test_backlog.py` używa tej samej miary dla pozycji
   kolejki (`DONE_ONLY_FIELD`);
2. **raport `reports/<numer>*.md`** — `CLAUDE.md` §5 i §7 każą kończyć zadanie
   weryfikacją i raportem, więc istniejący raport zadania jest śladem, że zadanie
   zostało wykonane. To ten ślad złapałby T-212: `reports/T-212-station.md` leży
   w `main` od #137, a wpis stał `[ ]` przez kolejne dwanaście scaleń.

NIE sprawdza wpisów odrzucanych przez `doctor.sh` (`ZABLOKOWANE`, `CZŁOWIEK`), bo tam
raport nie musi znaczyć wykonania: zadanie właściciela potrafi mieć raport z rozpoznania,
a `doctor.sh` i tak nigdy takiego wpisu nie wymieni. Bramka o zasięgu szerszym niż usterka
zapalałaby się na czymś, czego usterka nie dotyczy — i skończyłaby wyłączona.

Wybór wpisu NIE jest tu przepisany z `doctor.sh` ręcznie. Test **wycina z `doctor.sh`
jego własne podstawienie** `next_task=$(…)` i uruchamia je bashem na podanym katalogu,
a potem porównuje wynik z czytnikiem w tym pliku. Kopia reguły rozjechałaby się z
oryginałem przy pierwszej zmianie doctora i bramka pilnowałaby wtedy nie tego wpisu,
który sesja naprawdę zobaczy.
"""
import io
import os
import re
import subprocess
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TASKS = os.path.join(ROOT, "docs", "TASKS.md")
DOCTOR = os.path.join(ROOT, "doctor.sh")
REPORTS = os.path.join(ROOT, "reports")

#: Podstawienie z `doctor.sh`, w którym mieszka wybór następnego zadania. Nazwa zmiennej
#: jest jedyną rzeczą, którą ten plik o doctorze zakłada.
DOCTOR_SELECTION = re.compile(r"next_task=\$\((.*?)\)\n", re.S)

#: Pole, które `docs/TASK-TEMPLATE.md` dokłada do wpisu ZROBIONEGO. Ta sama miara,
#: co `DONE_ONLY_FIELD` w `tools/tests/test_backlog.py`.
DONE_FIELD = "- **Wynik:**"

#: Numer zadania w nagłówku wpisu: `T-212`, `R-007`. Po nim nazywają się raporty.
TASK_NUMBER = re.compile(r"\b([TR]-\d{3})\b")


def _read(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def doctor_selection_command():
    """Treść podstawienia `next_task=$(…)` wycięta z `doctor.sh`."""
    match = DOCTOR_SELECTION.search(_read(DOCTOR))
    return None if match is None else match.group(1)


def run_doctor_selection(workdir):
    """Wynik podstawienia z doctora, puszczonego bashem w `workdir`."""
    command = doctor_selection_command()
    script = "%s\nprintf '%%s' \"$next_task\"\n" % ("next_task=$(%s)" % command)
    done = subprocess.run(["bash", "-c", script], cwd=workdir,
                          capture_output=True, text=True)
    return done.stdout.strip()


def selectable_entries(text):
    """Wpisy, które `doctor.sh` może wymienić: `### [ ]`, bez ZABLOKOWANE i CZŁOWIEK.

    Zwraca listę `(nagłówek_bez_prefiksu, treść_wpisu)` w kolejności z pliku — pierwszy
    element to ten, który doctor pokaże.
    """
    lines = text.splitlines()
    found = []
    for index, line in enumerate(lines):
        if not line.startswith("### [ ] "):
            continue
        if "ZABLOKOWANE" in line or "CZŁOWIEK" in line:
            continue
        end = len(lines)
        for ahead in range(index + 1, len(lines)):
            if lines[ahead].startswith("#"):
                end = ahead
                break
        found.append((line[len("### [ ] "):], "\n".join(lines[index:end])))
    return found


def reports_for(number):
    """Raporty `reports/<numer>*.md` — ślad, że zadanie zostało wykonane."""
    if not os.path.isdir(REPORTS):
        return []
    return sorted(name for name in os.listdir(REPORTS)
                  if name.startswith(number) and name.endswith(".md"))


def delivery_marks(heading, body, reports_lookup=reports_for):
    """Ślady wykonania znalezione przy wpisie — pusta lista znaczy „jeszcze nie zrobione”."""
    marks = []
    if DONE_FIELD in body:
        marks.append("wpis ma pole „Wynik”, które szablon dokłada do zadania ZROBIONEGO")
    for number in dict.fromkeys(TASK_NUMBER.findall(heading)):
        for report in reports_lookup(number):
            marks.append("w repozytorium leży reports/%s" % report)
    return marks


# ---------------------------------------------------------------------------
# Bramka
# ---------------------------------------------------------------------------


def test_the_selection_is_taken_from_doctor_itself_and_not_retyped():
    """Czytnik w tym pliku ma dawać to samo, co podstawienie z `doctor.sh`.

    Kontrola jest zrobiona na **syntetycznej** rozpisce, a nie na prawdziwej, i to jest
    celowe: gdyby stała tylko na `docs/TASKS.md`, po tej właśnie poprawce porównywałaby
    pustkę z pustką i nie miałaby czego wykryć.
    """
    command = doctor_selection_command()
    assert command is not None, (
        "nie znalazłem podstawienia `next_task=$(…)` w doctor.sh — bramka straciła "
        "przedmiot; jeśli doctor przestał wybierać zadanie z rozpiski, ten plik "
        "trzeba przepisać, a nie usunąć")
    assert "docs/TASKS.md" in command, "doctor czyta następne zadanie z innego pliku"

    synthetic = (
        "# Rozpiska\n\n"
        "### [x] T-001 · zrobione\n- treść\n\n"
        "### [ ] T-002 · zablokowane — **ZABLOKOWANE**\n- treść\n\n"
        "### [ ] **[CZŁOWIEK]** T-003 · nie dla agenta\n- treść\n\n"
        "### [ ] T-004 · pierwsze do wzięcia\n- treść\n\n"
        "### [ ] T-005 · drugie do wzięcia\n- treść\n")

    with tempfile.TemporaryDirectory() as workdir:
        os.mkdir(os.path.join(workdir, "docs"))
        with io.open(os.path.join(workdir, "docs", "TASKS.md"), "w",
                     encoding="utf-8") as handle:
            handle.write(synthetic)
        from_doctor = run_doctor_selection(workdir)

    assert from_doctor == "T-004 · pierwsze do wzięcia", from_doctor

    mine = selectable_entries(synthetic)
    assert [heading for heading, _ in mine] == [
        "T-004 · pierwsze do wzięcia", "T-005 · drugie do wzięcia"], mine
    assert mine[0][0] == from_doctor, (
        "czytnik tej bramki i doctor wskazują różne zadania: %r vs %r"
        % (mine[0][0], from_doctor))


def test_the_delivery_marks_have_a_desygnat_on_this_tree():
    """Miara „ślad wykonania” ma coś znaczyć DZIŚ, a nie tylko w opisie.

    Gdyby `reports/` przestało nosić nazwy zadań, drugi ślad byłby martwą literą
    i bramka zwężałaby się po cichu do samego pola „Wynik”.
    """
    assert reports_for("T-212"), (
        "reports/T-212*.md zniknęło — ślad, na którym stoi ta bramka, stracił desygnat")
    assert reports_for("T-311"), "reports/T-311*.md zniknęło"
    assert not reports_for("T-999"), "czytnik raportów łapie numery, których nie ma"

    tasks = _read(TASKS)
    assert "### [x] T-212 " in tasks, (
        "wpis T-212 nie jest odhaczony, a jego raport leży w reports/ — to jest "
        "dokładnie ta usterka, dla której ten plik powstał")


def test_no_task_doctor_can_name_is_already_delivered():
    """Sedno bramki: żaden wpis do wzięcia nie może nosić śladu wykonania."""
    entries = selectable_entries(_read(TASKS))
    guilty = []
    for heading, body in entries:
        marks = delivery_marks(heading, body)
        if marks:
            guilty.append("%s — %s" % (heading, "; ".join(marks)))
    assert not guilty, (
        "doctor.sh wysłałby nową sesję do pracy, która leży w main: "
        + " | ".join(guilty)
        + " — wpis ma zostać odhaczony i dostać pole „Wynik”, a nie stać w kolejce")


def test_the_reader_of_delivery_marks_actually_reads():
    # Kontrole negatywne samego czytnika. Bez nich test wyżej przechodziłby także
    # wtedy, gdyby `delivery_marks` zwracało pustą listę na wszystkim — a dziś
    # przechodzi na zbiorze, w którym po poprawce nie ma ani jednego wpisu.
    empty = lambda number: []
    assert delivery_marks("T-500 · świeże", "- **Wejście:** x", empty) == []
    assert delivery_marks("T-500 · zrobione", "- **Wynik:** 12 brył", empty), \
        "pole „Wynik” nie jest rozpoznawane jako ślad wykonania"
    assert delivery_marks("T-500 · z raportem", "- **Wejście:** x",
                          lambda number: ["T-500-cos.md"] if number == "T-500" else []), \
        "raport zadania nie jest rozpoznawany jako ślad wykonania"
    assert delivery_marks("bez numeru", "- **Wejście:** x",
                          lambda number: ["cokolwiek.md"]) == [], \
        "nagłówek bez numeru zadania nie ma po czym szukać raportu"

    # I czytnik wpisów.
    sample = ("### [ ] T-010 · do wzięcia\n- treść\n"
              "### [x] T-011 · zrobione\n- treść\n"
              "### [ ] T-012 · **ZABLOKOWANE**\n- treść\n"
              "### [ ] **[CZŁOWIEK]** T-013 · nie dla agenta\n- treść\n")
    picked = [heading for heading, _ in selectable_entries(sample)]
    assert picked == ["T-010 · do wzięcia"], picked
    assert selectable_entries("")[:] == [], "pusty plik nie ma wpisów"
    body = selectable_entries(sample)[0][1]
    assert "T-011" not in body, "treść wpisu przelewa się przez następny nagłówek"


# --- kolejka faz 5 i 6, gdy nie ma odblokowanego zadania z numerem -------------------
#
# `CLAUDE.md` §8 mówi wprost: „Zatrzymanie się z powodu pustej kolejki nie jest poprawnym
# wynikiem […] agent bierze następną pozycję z fazy 5 lub 6". Do 05.09.2026 doctor w tej
# sytuacji odsyłał do tabeli „Co blokuje co", czyli do miejsca, które mówi, CZEGO NIE DA
# SIĘ zrobić — dokładnie odwrotnie niż konstytucja.
#
# Gałąź nigdy się nie wykonywała, bo zawsze istniał jakiś wpis `### [ ]`. Zobaczyliśmy ją
# dopiero po odhaczeniu T-212 (#240). Nie była martwym kodem — była kodem, którego nikt
# nie widział, bo poprzedzał go stan nieaktualny.

#: Podstawienie z `doctor.sh`, w którym mieszka wybór pozycji kolejki.
DOCTOR_QUEUE = re.compile(r"queue_item=\$\((.*?)\)\n", re.S)

def doctor_queue_command():
    """Treść podstawienia `queue_item=$(…)` wycięta z `doctor.sh`."""
    match = DOCTOR_QUEUE.search(_read(DOCTOR))
    return None if match is None else match.group(1)


def run_doctor_queue(workdir):
    """Wynik podstawienia kolejki, puszczonego bashem w `workdir`."""
    command = doctor_queue_command()
    script = "%s\nprintf '%%s' \"$queue_item\"\n" % ("queue_item=$(%s)" % command)
    done = subprocess.run(["bash", "-c", script], cwd=workdir,
                          capture_output=True, text=True)
    return done.stdout.strip()


def test_doctor_points_at_the_queue_and_the_rule_is_not_retyped():
    r"""Wybór pozycji kolejki jest WYCIĘTY z doctora i uruchomiony, nie przepisany.

    Bramka na napis nie odróżniłaby kodu wykonywanego od komentarza — repozytorium
    odrzuciło tę formę osobno w #200.

    **BRAMKA PRZEKIEROWANA 09.09.2026, i sprawdza teraz WIĘCEJ.** Poprzednia wersja
    porównywała wybór doctora z PIERWSZYM wierszem tabeli faz 5 i 6, dopasowanym
    wzorcem `^\| ([56]\.\d+) \|` — czyli z drugą kopią reguły „co jest pozycją
    kolejki". Kopia rozjechała się z oryginałem i bramka tego nie widziała, bo
    porównywała jedną kopię z drugą: wzorzec łapał **8 wierszy i ani jednej pozycji
    otwartej** (wszystkie 34 otwarte mają w numerze literę), a więc pierwszym
    „zadaniem" był wiersz z adnotacją ZROBIONE. Teraz porównanie idzie z
    `test_backlog.open_items`, czyli z tym samym czytnikiem, którym mierzy się zapas,
    i dochodzi asercja, że wybór **nie nosi adnotacji ZROBIONE**.
    """
    import test_backlog

    command = doctor_queue_command()
    assert command is not None, (
        "nie znalazłem podstawienia `queue_item=$(…)` w doctor.sh — bramka straciła "
        "przedmiot i przestałaby cokolwiek sprawdzać")

    tekst = _read(TASKS)
    otwarte = test_backlog.open_items(tekst)
    assert otwarte, "w docs/TASKS.md nie ma ani jednej OTWARTEJ pozycji kolejki"

    wybrane = run_doctor_queue(ROOT)
    numer = otwarte[0]
    assert wybrane.startswith(numer), (
        f"doctor wskazuje {wybrane!r}, a pierwsza OTWARTA pozycja kolejki to {numer}")

    wiersz = test_backlog.queue_row(tekst, numer) or ""
    assert test_backlog.DONE_ROW_MARKER not in wiersz, (
        f"doctor wskazuje {numer}, a jej wiersz nosi {test_backlog.DONE_ROW_MARKER} — "
        "sesja dostałaby polecenie zrobienia pracy, która już leży w main")
    tytul = re.match(r"\| \S+ \| \*\*([^*]+)\*\*", wiersz)
    assert tytul is not None, f"wiersz pozycji {numer} nie ma pogrubionego tytułu: {wiersz[:120]!r}"
    assert tytul.group(1).strip() in wybrane, (
        f"doctor nie podaje tytułu pozycji {numer}: {wybrane!r}")


def test_doctor_says_the_queue_is_empty_instead_of_going_silent():
    """Pusta kolejka ma dać PUSTY wynik podstawienia, a nie pierwszy lepszy wiersz.

    Kontrola przeciwna do poprzedniego testu: bez niej podstawienie mogłoby łapać
    dowolny wiersz tabeli i zawsze coś zwracać, co wyglądałoby jak działająca bramka.
    """
    with tempfile.TemporaryDirectory() as katalog:
        docs = os.path.join(katalog, "docs")
        os.makedirs(docs)
        with io.open(os.path.join(docs, "TASKS.md"), "w", encoding="utf-8") as uchwyt:
            uchwyt.write(
                "# Rozpiska bez kolejki\n\n"
                "| # | co | dlaczego |\n"
                "|---|---|---|\n"
                "| T-999 | **Zadanie spoza kolejki** — nie ma numeru fazy | powód |\n")

        assert run_doctor_queue(katalog) == "", (
            "doctor wskazał pozycję kolejki, choć w rozpisce nie ma ani jednego wiersza "
            "faz 5 i 6 — podstawienie łapie za szeroko")

#: Podstawienie z `doctor.sh`, w którym mieszka LICZBA pozycji kolejki (6.D50).
DOCTOR_COUNT = re.compile(r"queue_count=\$\((.*?)\)\n", re.S)

#: Akapit, do którego trafia człowiek idący za komunikatem doctora. Kotwica jest jego
#: pierwszym zdaniem; region kończy się pierwszą pustą linią, bo dalej stoi już WYWÓD
#: o dawnych literach tej reguły i on liczby cytować MUSI.
AKAPIT_KOTWICA = "**Jeśli trafiłeś do tej tabeli z `doctor.sh`**"

#: „31 pozycji", „**36** pozycje", „12 pozycjami" — literał liczby pozycji w prozie.
LITERAL_POZYCJI = re.compile(r"\d+\s*\**\s*pozycj", re.I)


def doctor_count_command():
    """Treść podstawienia `queue_count=$(…)` wycięta z `doctor.sh`."""
    match = DOCTOR_COUNT.search(_read(DOCTOR))
    return None if match is None else match.group(1)


def run_doctor_count(workdir):
    """Wynik podstawienia liczby pozycji, puszczonego bashem w `workdir`."""
    command = doctor_count_command()
    script = "%s\nprintf '%%s' \"$queue_count\"\n" % ("queue_count=$(%s)" % command)
    done = subprocess.run(["bash", "-c", script], cwd=workdir,
                          capture_output=True, text=True)
    return done.stdout.strip()


def _akapit_kolejki(text):
    """Akapit z kotwicą, do pierwszej pustej linii. `None`, gdy kotwicy nie ma."""
    start = text.find(AKAPIT_KOTWICA)
    if start < 0:
        return None
    koniec = text.find("\n\n", start)
    return text[start:koniec if koniec > 0 else len(text)]


def test_doctor_liczy_pozycje_kolejki_sam_zamiast_przepisywac_liczbe():
    """Liczba pozycji ma być LICZONA przy uruchomieniu, nie wpisana z ręki (6.D50).

    Kontrola jest dwuczęściowa i druga część jest tą, która ma znaczenie: to samo
    podstawienie puszczone na ROZPISCE ZE ZMIENIONĄ LICZBĄ POZYCJI musi dać INNĄ
    liczbę. Sama zgodność z `open_items` na tym drzewie przeszłaby także wtedy, gdyby
    ktoś wpisał dzisiejsze `36` na sztywno — i to jest dokładnie usterka, którą 6.D50
    zamyka po stronie prozy.
    """
    command = doctor_count_command()
    assert command is not None, (
        "nie znalazłem podstawienia `queue_count=$(…)` w doctor.sh — bramka straciła "
        "przedmiot i przestałaby cokolwiek sprawdzać")

    import test_backlog as B
    tekst = _read(TASKS)
    dzis = len(B.open_items(tekst))
    assert run_doctor_count(ROOT) == str(dzis), (
        f"doctor podaje {run_doctor_count(ROOT)!r}, a open_items daje {dzis}")

    pozycje = B.open_items(tekst)
    assert pozycje, "kolejka jest pusta — nie ma czego odejmować w kontroli"
    wiersz = B.queue_row(tekst, pozycje[0])
    zmieniony = tekst.replace(wiersz, wiersz.replace("| ", "| **ZROBIONE w kontroli.** ", 2), 1)
    oczekiwane = len(B.open_items(zmieniony))
    assert oczekiwane != dzis, (
        "kontrola nie zmieniła liczby pozycji — mutacja rozpiski chybiła i test "
        "nie sprawdziłby niczego")

    with tempfile.TemporaryDirectory() as katalog:
        os.makedirs(os.path.join(katalog, "docs"))
        os.makedirs(os.path.join(katalog, "tools", "tests"))
        with io.open(os.path.join(katalog, "docs", "TASKS.md"), "w", encoding="utf-8") as uchwyt:
            uchwyt.write(zmieniony)
        with io.open(os.path.join(katalog, "tools", "tests", "test_backlog.py"), "w",
                     encoding="utf-8") as uchwyt:
            uchwyt.write(_read(os.path.join(ROOT, "tools", "tests", "test_backlog.py")))
        assert run_doctor_count(katalog) == str(oczekiwane), (
            f"na rozpisce z jedną pozycją mniej doctor podał "
            f"{run_doctor_count(katalog)!r}, a powinien {oczekiwane} — liczba nie jest "
            "liczona, tylko przepisana")


def test_akapit_kolejki_nie_odzyskuje_literalu_liczby_pozycji():
    """Akapit dla człowieka z doctora nie podaje liczby pozycji — podaje ją doctor.

    Zmierzone przy 6.D50 na czterdziestu ostatnich commitach dotykających
    `docs/TASKS.md`: licznik zmienił wartość w **27** z nich, a **7** z tych
    czterdziestu to wciągnięcia `main` do równoległej gałęzi. Literał w prozie starzeje
    się więc przy dwóch commitach na trzy i daje konflikt semantyczny przy co szóstym.

    Detektor jest tu sprawdzany na własnym przedmiocie, żeby bramka nie była pusta:
    zdanie, które akapit NOSIŁ do 09.09.2026, musi zostać złapane.
    """
    assert LITERAL_POZYCJI.search("fazy 5 i 6 trzymają\n31 pozycji, z których żadna"), (
        "detektor nie łapie zdania, które ten akapit naprawdę nosił — bramka pusta")
    assert not LITERAL_POZYCJI.search("fazy 5 i 6 trzymają pozycje, z których żadna"), (
        "detektor łapie zdanie BEZ liczby — zapaliłby się na poprawnej prozie")

    akapit = _akapit_kolejki(_read(TASKS))
    assert akapit is not None, (
        f"nie znalazłem akapitu po kotwicy {AKAPIT_KOTWICA!r} w docs/TASKS.md — "
        "bramka straciła przedmiot i milczy zamiast pilnować")
    trafienie = LITERAL_POZYCJI.search(akapit)
    assert trafienie is None, (
        f"akapit kolejki znowu podaje liczbę pozycji ({trafienie.group(0)!r}) — "
        "ta liczba starzeje się przy dwóch commitach na trzy; podaje ją doctor.sh")


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

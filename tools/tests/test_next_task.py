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

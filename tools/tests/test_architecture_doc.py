#!/usr/bin/env python3
"""Drzewo modułów w `docs/01-architecture.md` kontra prawdziwe drzewo `src/`.

`docs/01` jest dokumentem, od którego zaczyna czytanie ktokolwiek nowy w projekcie:
`CLAUDE.md` §3 odsyła do niego po podział na moduły. Jego blok ```text był
NIEAKTUALNY i nic tego nie łapało — bramki CI oglądają kod i YAML, a nie prozę.

Zmierzone 04.09.2026 na `98b2769`:

- `src/Sim/Passengers/` — w dokumencie był, w repozytorium NIE ISTNIAŁ;
- `src/Game/Views/` (Cab, Platform, Dispatcher) i `src/Game/Audio/` — to samo;
- `src/Sim/Signalling/` — 8 plików `.cs`, w dokumencie NIE BYŁO;
- `src/Sim.Runner/` — cały projekt CLI, w dokumencie NIE BYŁO;
- `src/Game/Assets/`, `Scenes/`, `UI/`, `World/` — istnieją, nie były wymienione.

Bramka nie trzyma DRUGIEJ KOPII drzewa. Czyta je z dysku i porównuje z dokumentem
w OBIE strony, bo jedna strona nie wystarcza: sam zakaz katalogów-widm nie zmusza
dokumentu, żeby dotrzymywał kroku nowym katalogom, a właśnie to się tu rozjechało.

DLACZEGO JEDEN KATALOG W JEDNYM WIERSZU. Poprzedni zapis ściskał kilka katalogów
w wiersz (`Views/Cab, Platform, Dispatcher`, `Input/, Audio/, UI/`). Takiego wiersza
nie da się porównać maszynowo bez zgadywania, gdzie kończy się nazwa, a zaczyna
opis — i dokładnie w tym zapisie dryf przeżył. Zmiana formatu jest częścią bramki,
nie jej ozdobą.
"""

import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOC = os.path.join(ROOT, "docs", "01-architecture.md")
SRC = os.path.join(ROOT, "src")

#: Katalogi, które są wynikiem builda albo stanem edytora, a nie modułem projektu.
#: **6.D97: bez `bin` i `obj`.** Te dwa stoją w `.gitignore`, więc odsiewa je już
#: `TW.walk` — trzymanie ich tutaj było DRUGĄ, uboższą kopią tamtej listy (nie zna
#: `build`, `renders`, `.venv`) i rozjechałoby się przy pierwszym nowym wpisie.
#: `.vs` i `node_modules` w `.gitignore` NIE stoją i dlatego zostają: odsiewa je
#: reguła tego dokumentu, nie reguła repozytorium.
ARTEFAKTY = {".vs", "node_modules"}

#: Wiersz drzewa: wcięcie, nazwa katalogu z ukośnikiem, opcjonalny opis.
WIERSZ = re.compile(r"^(\s*)([A-Za-z][\w.]*)/(?:\s{2,}(.*))?$")


def _doc():
    with open(DOC, encoding="utf-8") as handle:
        return handle.read()


def tree_block():
    """Zawartość pierwszego bloku ```text w dokumencie."""
    match = re.search(r"```text\n(.*?)```", _doc(), re.S)
    assert match, "w docs/01-architecture.md nie ma bloku ```text z drzewem"
    return match.group(1)


def documented_paths():
    """Ścieżki wypisane w dokumencie, względem `src/`, np. `Sim/Physics`.

    Wcięcie decyduje o zagnieżdżeniu, więc `Physics/` pod `Sim/` daje `Sim/Physics`.
    """
    stos = []
    out = set()
    for line in tree_block().split("\n"):
        if not line.strip() or line.strip() == "src/":
            continue
        match = WIERSZ.match(line)
        if not match:
            continue
        wciecie, nazwa, _opis = match.groups()
        poziom = len(wciecie)
        while stos and stos[-1][0] >= poziom:
            stos.pop()
        sciezka = "/".join([czlon for _lvl, czlon in stos] + [nazwa])
        out.add(sciezka)
        stos.append((poziom, nazwa))
    return out


def real_paths():
    """Katalogi pod `src/` z dysku, bez artefaktów builda."""
    out = set()
    for folder, dirs, _files in TW.walk(SRC):
        dirs[:] = [d for d in dirs if d not in ARTEFAKTY and not d.startswith(".")]
        rel = os.path.relpath(folder, SRC)
        if rel != ".":
            out.add(rel.replace(os.sep, "/"))
    return out


def test_architecture_doc_lists_no_directory_that_does_not_exist():
    """Katalog-widmo w dokumencie to gorzej niż brak dokumentu.

    Ktoś nowy szuka `src/Sim/Passengers/`, nie znajduje i nie wie, czy patrzy w złe
    miejsce, czy dokument kłamie. Zmierzone: przed 04.09.2026 dokument wymieniał
    trzy takie katalogi (`Sim/Passengers`, `Game/Views`, `Game/Audio`).
    """
    widma = sorted(documented_paths() - real_paths())
    assert not widma, f"docs/01 wymienia katalogi, których nie ma w src/: {widma}"


def test_architecture_doc_lists_every_directory_that_exists():
    """KIERUNEK ODWROTNY, i to ten, który się tutaj rozjechał.

    Bez tego bramka pilnuje tylko, żeby nikt nie dopisał widma — a nie tego, żeby
    dokument dotrzymywał kroku repozytorium. Zmierzone: `src/Sim/Signalling/`
    z ośmioma plikami i cały `src/Sim.Runner/` istniały, nie będąc wymienione.
    """
    brakujace = sorted(real_paths() - documented_paths())
    assert not brakujace, f"docs/01 nie wymienia katalogów z src/: {brakujace}"


def test_architecture_doc_tree_is_not_read_empty():
    """Pusta pętla przechodzi zielona z powodu, który nie ma nic wspólnego ze zgodnością."""
    udokumentowane = documented_paths()
    prawdziwe = real_paths()
    assert len(udokumentowane) >= 8, sorted(udokumentowane)
    assert len(prawdziwe) >= 8, sorted(prawdziwe)


def test_architecture_doc_build_artefacts_are_not_demanded():
    """`bin/` i `obj/` po lokalnym `dotnet build` nie są modułami architektury.

    Kontrola po drugiej stronie odsiewu: bez niej ktoś mógłby usunąć `ARTEFAKTY`
    i bramka zaczęłaby żądać wpisania katalogów builda do dokumentu — na maszynie,
    na której ktoś zbudował projekt, i tylko tam.
    """
    assert not {p for p in real_paths() if p.split("/")[-1] in ARTEFAKTY}
    # 6.D97: te dwa wiersze są teraz JEDYNĄ kontrolą na `bin`/`obj` po tej stronie
    # i to jest wzmocnienie, nie osłabienie — pytają o WYNIK (czego nie ma w liście
    # ścieżek), a nie o zawartość zbioru, który je odsiewa.
    assert "Sim/bin" not in real_paths()
    assert "Sim/obj" not in real_paths()

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

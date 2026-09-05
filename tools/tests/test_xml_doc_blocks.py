#!/usr/bin/env python3
"""Jedna składowa dokumentacji XML: jeden składnik. Bramka przeciw osieroconym blokom.

Gdy składnik znika albo dostaje nową nazwę, jego blok `///` zostaje w pliku i przykleja
się do NASTĘPNEGO składnika. Powstaje wtedy dwa razy `<summary>` nad jedną metodą:
pierwszy opisuje coś innego, drugi to prawda. Kompilator tego nie widzi — projekt nie
ustawia `GenerateDocumentationFile`, więc CS1571 („zduplikowany znacznik") nigdy nie
pada, a `dotnet build` przechodzi z zerem ostrzeżeń. Nie widzi tego też żaden test,
bo tekst w komentarzu nie jest wynikiem, który cokolwiek porównuje — ta sama rodzina,
co nieaktualne twierdzenia o osi z `test_axis_claims.py`.

Zmierzone 04.09.2026, przed tą bramką, na `888c41e`:

    src/Sim/Line/TrackAxis.cs:185   CoversChord nosił summary MaxDeviationFromSourceM
    src/Sim/Line/LineCore.cs:285    TurnbackEnabled nosił summary Finished
    src/Sim/Train/LineRun.cs:119    TracePoint nosił summary i cztery <param> metody Run
    src/Game/FirstRun.cs:99         AxisManifestToleranceM nosił summary kodów wyjścia

Cztery sztuki w czterech plikach, wszystkie przechodziły przez całą suitę i przez
`dotnet build` bez jednego ostrzeżenia.

CZEGO TA BRAMKA NIE ROBI: nie sprawdza, czy treść bloku opisuje ten składnik, pod
którym stoi — tego maszyna nie oceni. Łapie wyłącznie sytuację mechaniczną: dwa
`<summary>` w jednym ciągu linii `///`. To wystarczyło na wszystkie cztery powyżej.
"""
import glob
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Katalogi z kodem C#, w których dokumentacja XML jest jedynym opisem założeń.
SCANNED_ROOTS = (
    os.path.join(ROOT, "src", "Sim"),
    os.path.join(ROOT, "src", "Game"),
)


def _sources():
    paths = []
    for root in SCANNED_ROOTS:
        paths += glob.glob(os.path.join(root, "**", "*.cs"), recursive=True)
    return sorted(p for p in paths if os.sep + "obj" + os.sep not in p
                  and os.sep + "bin" + os.sep not in p)


def _doc_runs(path):
    """Spójne ciągi linii `///` jako (numer pierwszej linii, lista linii)."""
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    runs = []
    run = []
    start = 0
    for number, line in enumerate(lines, 1):
        if line.strip().startswith("///"):
            if not run:
                start = number
            run.append(line)
            continue
        if run:
            runs.append((start, run))
            run = []
    if run:
        runs.append((start, run))
    return runs


def test_xml_doc_scan_actually_reads_the_sources():
    """Bramka, która nic nie czyta, przechodzi zawsze — więc czytanie też jest sprawdzane."""
    sources = _sources()
    assert len(sources) >= 20, f"za mało plików do skanu: {len(sources)}"
    documented = [p for p in sources if _doc_runs(p)]
    assert len(documented) >= 20, f"za mało plików z dokumentacją XML: {len(documented)}"


def test_no_member_carries_two_summary_blocks():
    offenders = []
    for path in _sources():
        for start, run in _doc_runs(path):
            count = sum(line.count("<summary>") for line in run)
            if count > 1:
                offenders.append(
                    f"{os.path.relpath(path, ROOT)}:{start} — {count} bloków <summary> "
                    f"na jednym składniku")
    assert not offenders, offenders


def test_every_summary_is_closed_in_its_own_block():
    """Blok osierocony bywa też blokiem urwanym; to ten sam koszt skanu."""
    offenders = []
    for path in _sources():
        for start, run in _doc_runs(path):
            text = "\n".join(run)
            if text.count("<summary>") != text.count("</summary>"):
                offenders.append(
                    f"{os.path.relpath(path, ROOT)}:{start} — "
                    f"{text.count('<summary>')} otwarć, {text.count('</summary>')} zamknięć")
    assert not offenders, offenders

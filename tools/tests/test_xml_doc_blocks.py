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

6.B21: bramka sprawdzała dziś wyłącznie prawdziwe `src/`, które jest aktualnie
czyste — czyli przechodziła, ale bez dowodu, że umie zaświecić (dokładnie stan,
przed którym ostrzega `CLAUDE.md` §5). Dwie funkcje `test_no_member_carries_two_
summary_blocks` i `test_every_summary_is_closed_in_its_own_block` zostały tu
rozłożone na wywołanie zwykłej funkcji (`_duplicate_summary_offenders`,
`_unclosed_summary_offenders`) branej na liście ścieżek — ta sama funkcja jedzie
teraz zarówno po prawdziwym `_sources()`, jak i po pliku `.cs` wstrzykniętym w
katalogu tymczasowym niżej. Kontrola negatywna woła DOKŁADNIE tę funkcję, którą
wołają testy bramki, więc dowodzi zaświecenia mechanizmu, a nie osobnej kopii
liczącej to samo.
"""
import glob
import os
import tempfile

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


def _duplicate_summary_offenders(paths):
    """Ta sama pętla dla prawdziwego skanu i dla kontroli negatywnej niżej."""
    offenders = []
    for path in paths:
        for start, run in _doc_runs(path):
            count = sum(line.count("<summary>") for line in run)
            if count > 1:
                offenders.append(
                    f"{os.path.relpath(path, ROOT) if ROOT in path else path}:{start} — "
                    f"{count} bloków <summary> na jednym składniku")
    return offenders


def _unclosed_summary_offenders(paths):
    """Blok osierocony bywa też blokiem urwanym; to ten sam koszt skanu."""
    offenders = []
    for path in paths:
        for start, run in _doc_runs(path):
            text = "\n".join(run)
            if text.count("<summary>") != text.count("</summary>"):
                offenders.append(
                    f"{os.path.relpath(path, ROOT) if ROOT in path else path}:{start} — "
                    f"{text.count('<summary>')} otwarć, {text.count('</summary>')} zamknięć")
    return offenders


def test_no_member_carries_two_summary_blocks():
    assert not _duplicate_summary_offenders(_sources())


def test_every_summary_is_closed_in_its_own_block():
    assert not _unclosed_summary_offenders(_sources())


# --- kontrola negatywna (6.B21): dowód, że bramka umie zaświecić ------------------
#
# Powyższe dwa testy jadą po prawdziwym `src/`, które jest dziś czyste — same z
# siebie nie dowodzą, że licznik `<summary>`/`</summary>` w ogóle potrafi zapalić
# którykolwiek z offenderów. Poniżej: plik `.cs` budowany w katalogu tymczasowym
# (nie w `src/`, poza zakresem 6.B21), jeden wariant zdublowany, jeden czysty —
# oba przez tę samą `_doc_runs` i te same funkcje offenderów co bramka wyżej.

_CLEAN_MEMBER_CS = """namespace Metro.Sim.Line
{
    /// <summary>Zwraca odległość stycznej cięciwy od źródłowej osi.</summary>
    /// <param name="chordM">Długość cięciwy w metrach.</param>
    public double CoversChord(double chordM)
    {
        return chordM;
    }
}
"""

_DUPLICATED_SUMMARY_MEMBER_CS = """namespace Metro.Sim.Line
{
    /// <summary>Maksymalne odchylenie od źródłowej osi w metrach.</summary>
    /// <summary>Zwraca odległość stycznej cięciwy od źródłowej osi.</summary>
    /// <param name="chordM">Długość cięciwy w metrach.</param>
    public double CoversChord(double chordM)
    {
        return chordM;
    }
}
"""

_UNCLOSED_SUMMARY_MEMBER_CS = """namespace Metro.Sim.Line
{
    /// <summary>Zwraca odległość stycznej cięciwy od źródłowej osi.
    /// <param name="chordM">Długość cięciwy w metrach.</param>
    public double CoversChord(double chordM)
    {
        return chordM;
    }
}
"""


def _write_temp_cs(tmp_dir, name, text):
    path = os.path.join(tmp_dir, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


def test_a_duplicated_summary_block_lights_up_the_duplicate_gate():
    """Wstrzyknięty w katalogu tymczasowym plik z dwoma <summary> na CoversChord
    ZAPALA `_duplicate_summary_offenders` — dokładnie ten sam offender, jaki
    znalazły cztery prawdziwe pliki opisane w docstringu modułu 04.09.2026."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = _write_temp_cs(tmp_dir, "Duplicated.cs", _DUPLICATED_SUMMARY_MEMBER_CS)
        offenders = _duplicate_summary_offenders([path])
        assert len(offenders) == 1, offenders
        assert "Duplicated.cs:3" in offenders[0], offenders[0]
        assert "2 bloków <summary>" in offenders[0], offenders[0]
        # ten sam plik NIE zapala kontroli „urwany blok" — oba <summary> są domknięte.
        assert not _unclosed_summary_offenders([path])


def test_an_unclosed_summary_block_lights_up_the_unclosed_gate():
    """Wariant urwany (bez `</summary>`) to osobna usterka z tego samego docstringu
    („blok osierocony bywa też blokiem urwanym") — musi zapalać SWOJĄ bramkę."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = _write_temp_cs(tmp_dir, "Unclosed.cs", _UNCLOSED_SUMMARY_MEMBER_CS)
        offenders = _unclosed_summary_offenders([path])
        assert len(offenders) == 1, offenders
        assert "1 otwarć, 0 zamknięć" in offenders[0], offenders[0]
        # jedno <summary>, więc kontrola duplikatu na tym samym pliku milczy.
        assert not _duplicate_summary_offenders([path])


def test_a_clean_synthetic_file_lights_up_neither_gate():
    """Kontrola w drugą stronę: ten sam mechanizm na POPRAWNYM pliku (jeden
    <summary>, domknięty) ma milczeć — inaczej powyższe dwa testy dowodziłyby
    tylko tego, że bramka zapala się zawsze, niezależnie od treści pliku."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = _write_temp_cs(tmp_dir, "Clean.cs", _CLEAN_MEMBER_CS)
        assert not _duplicate_summary_offenders([path])
        assert not _unclosed_summary_offenders([path])

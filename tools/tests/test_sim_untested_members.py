#!/usr/bin/env python3
"""Licznik składników `src/Sim` bez testu — bez plików generowanych przez `dotnet build`.

Zmierzone 06.09.2026 przy 6.D15 (#301): wiersz powłoki z bloku `##### 6.A8` —
jedyne miejsce, gdzie ten licznik dotąd żył — to pętla po `find src/Sim -name '*.cs'`.
Na czystym drzewie wypisuje zero wierszy `BRAK TESTU`. Na drzewie **po**
`dotnet build src/Sim` (Debug albo Release) wypisuje cztery, i to zawsze te same
cztery, bo `dotnet` generuje je przy każdym budowaniu:

    src/Sim/obj/Debug/net10.0/Sim.AssemblyInfo.cs
    src/Sim/obj/Debug/net10.0/.NETCoreApp,Version=v10.0.AssemblyAttributes.cs
    src/Sim/obj/Release/net10.0/Sim.AssemblyInfo.cs
    src/Sim/obj/Release/net10.0/.NETCoreApp,Version=v10.0.AssemblyAttributes.cs

Żaden z tych czterech plików nie ma nazwanego typu do przetestowania — to plik
wygenerowany przez SDK, bez `namespace Metro.*` i bez logiki. Blok 6.A8 obiecywał
„po zadaniu ma wypisać zero wierszy"; ta obietnica jest dziś nie do spełnienia na
ŻADNYM drzewie, które ktokolwiek zbudował — a `.gitignore` już wyklucza `obj/`
i `bin/` z commitów, więc te pliki nie są nawet danymi wejściowymi projektu.

Ta bramka liczy to samo, co robił wiersz powłoki z 6.A8 — składnik `src/Sim/**/*.cs`
bez pliku, który zawiera jego nazwę jako całe słowo gdziekolwiek pod `tests/` —
ale pomija `obj/` i `bin/` PRZED liczeniem, więc wynik nie zależy od tego, czy
drzewo było budowane. Precedens bramki chodzącej po `src/` bez wołania `dotnet`:
`tools/tests/test_xml_doc_blocks.py`.

CZEGO TA BRAMKA NIE ROBI: nie sprawdza, że test faktycznie ĆWICZY dany typ —
tylko że jego nazwa pada w jakimś pliku pod `tests/`. To ten sam próg, którego
używał wiersz z 6.A8; podniesienie progu (np. sprawdzenie wywołania, a nie tylko
wzmianki) jest poza zakresem tej pozycji.
"""
import glob
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

SIM_ROOT = os.path.join(ROOT, "src", "Sim")
TESTS_ROOT = os.path.join(ROOT, "tests")

#: Składniki, o których zmierzono, że legalnie nie mają testu nazywającego je
#: po nazwie pliku — z powodem, nie z pustą listą "bo tak wyszło". Pusta dziś:
#: pomiar na czystym drzewie (patrz test_gate_is_clean_on_a_real_checkout)
#: pokazuje zero prawdziwych plików `src/Sim` bez testu.
KNOWN_EXCEPTIONS = {}


def _is_generated(path):
    """`obj/` i `bin/` — dokładnie to, co pomija `.gitignore` w korzeniu repo."""
    parts = path.split(os.sep)
    return "obj" in parts or "bin" in parts


def _all_sim_cs_files():
    """Wszystko pod `src/Sim/**/*.cs`, WŁĄCZNIE z `obj/`/`bin/` — do pomiaru „przed"."""
    return sorted(glob.glob(os.path.join(SIM_ROOT, "**", "*.cs"), recursive=True))


def _sim_sources():
    """To samo, ale bez gałęzi pominiętych w `.gitignore` — wejście właściwej bramki.

    **6.D117: odsianie idzie przez `tree_walk`, nie przez `_is_generated`.** Wynik
    ten sam co do pliku: **53 pliki** przed i po (zmierzone 11.09.2026, przy 54
    z `_all_sim_cs_files`). `_is_generated` zostaje, bo nazywa się w komunikacie
    bramki „przed" i pole „Poza zakresem" 6.D117 wyklucza zmianę `_all_sim_cs_files`.
    """
    return TW.znajdz(SIM_ROOT, "*.cs")


def _test_corpus_text():
    """Treść każdego pliku pod `tests/` w jednym ciągu na plik — jak `grep -rlw` po katalogu."""
    texts = []
    for dirpath, _dirnames, filenames in TW.walk(TESTS_ROOT):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            try:
                with open(path, encoding="utf-8") as handle:
                    texts.append(handle.read())
            except (UnicodeDecodeError, OSError):
                continue
    return texts


def _has_whole_word(texts, word):
    """Odpowiednik `grep -rlw "$n" tests/` — granice słowa, nie samo `in`."""
    import re
    pattern = re.compile(r"\b" + re.escape(word) + r"\b")
    return any(pattern.search(text) for text in texts)


def _untested_members(paths, texts):
    """Ta sama funkcja dla prawdziwego skanu i dla kontroli negatywnej niżej."""
    offenders = []
    for path in paths:
        name = os.path.splitext(os.path.basename(path))[0]
        if name in KNOWN_EXCEPTIONS:
            continue
        if not _has_whole_word(texts, name):
            rel = os.path.relpath(path, ROOT) if ROOT in path else path
            offenders.append(f"BRAK TESTU: {rel}")
    return offenders


def test_generated_files_are_excluded_from_the_count():
    """Bramka, która nie odróżnia `obj/`/`bin/` od prawdziwych źródeł, nie jest
    tą, którą prosi 6.B23 — sprawdzamy to na pomiarze, nie na deklaracji."""
    all_files = _all_sim_cs_files()
    sources = _sim_sources()
    assert len(all_files) >= len(sources)
    for path in sources:
        assert not _is_generated(path), path


def test_sim_scan_actually_reads_the_sources():
    """Bramka, która nic nie czyta, przechodzi zawsze — więc czytanie też jest sprawdzane."""
    sources = _sim_sources()
    assert len(sources) >= 40, f"za mało plików do skanu: {len(sources)}"
    texts = _test_corpus_text()
    assert len(texts) >= 20, f"za mało plików pod tests/ do przeszukania: {len(texts)}"


def test_no_real_sim_member_is_missing_from_tests():
    """Właściwa bramka 6.B23: każdy składnik `src/Sim` (bez `obj/`/`bin/`) ma
    plik pod `tests/`, który wzmiankuje go po nazwie."""
    sources = _sim_sources()
    texts = _test_corpus_text()
    offenders = _untested_members(sources, texts)
    assert not offenders, "\n" + "\n".join(offenders)


# --- kontrola negatywna: dowód, że bramka umie zaświecić --------------------------
#
# Powyższy test jedzie po prawdziwym `src/Sim`, które jest dziś czyste — sam z siebie
# nie dowodzi, że `_untested_members` w ogóle potrafi zapalić offendera. Poniżej:
# nazwa składnika, która NIE pada w żadnym pliku pod `tests/` (sprawdzone wyżej przez
# `_has_whole_word` na prawdziwym korpusie), użyta jako ścieżka syntetyczna — przez
# TĘ SAMĄ `_untested_members`, którą woła test bramki powyżej.

_NEGATIVE_CONTROL_BASENAME = "NieistniejacySkladnikBezTestu6B23"


def test_a_member_absent_from_the_test_corpus_lights_up_the_gate():
    """Składnik dopisany do `src/Sim` bez testu MUSI zapalić bramkę — to jest
    kontrola negatywna, której 6.B23 żąda wprost."""
    texts = _test_corpus_text()
    # Warunek wstępny: nazwa kontrolna naprawdę nie pada w prawdziwym korpusie testów —
    # inaczej test poniżej dowodziłby zapalenia z niewłaściwego powodu.
    assert not _has_whole_word(texts, _NEGATIVE_CONTROL_BASENAME)

    fake_path = os.path.join(SIM_ROOT, "Physics", _NEGATIVE_CONTROL_BASENAME + ".cs")
    offenders = _untested_members([fake_path], texts)
    assert len(offenders) == 1, offenders
    assert _NEGATIVE_CONTROL_BASENAME in offenders[0], offenders[0]


def test_a_member_present_in_the_test_corpus_does_not_light_up_the_gate():
    """Kontrola w drugą stronę: składnik, który realnie ma test (np. `LineCore`,
    obecne w `tests/Sim.Tests/LineCoreTests.cs`), NIE zapala bramki — inaczej
    powyższy test dowodziłby tylko, że bramka zapala się zawsze."""
    texts = _test_corpus_text()
    real_path = os.path.join(SIM_ROOT, "Line", "LineCore.cs")
    assert os.path.exists(real_path), "pomiar zakłada plik, który dziś istnieje"
    offenders = _untested_members([real_path], texts)
    assert not offenders, offenders


def test_generated_obj_files_would_have_lit_up_the_gate_before_the_exclusion():
    """Dowód na SEDNO zadania: dokładnie te cztery pliki, które generuje
    `dotnet build`, nie mają swojej nazwy w `tests/` — czyli bez pominięcia
    `obj/`/`bin/` bramka kłamałaby na każdym zbudowanym drzewie, tak jak kłamał
    wiersz powłoki z 6.A8."""
    texts = _test_corpus_text()
    generated_names = ["Sim.AssemblyInfo", ".NETCoreApp,Version=v10.0.AssemblyAttributes"]
    for name in generated_names:
        assert not _has_whole_word(texts, name), name

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

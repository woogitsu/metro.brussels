#!/usr/bin/env python3
"""Twierdzenia o geometrii osi kontra `data/track/*.json`.

#86 (`4a03982`, 02.09.2026) przeliczyło kilometraże stacji na osi, która trafia do
pliku, i **zlikwidowało sytuację**, którą trzy miejsca w kodzie opisywały jako
bieżącą: „skrajna stacja wypada o ułamek metra za końcem osi". Zmierzone na
`e41178f`, wszystkie sześć pakietów:

    pakiet     length_m  ostatnia stacja   nadwyżka  stacje za końcem osi
    L1_A        6686.35          6686.35      0.000  0
    L1_B        5083.23          5083.23      0.000  0
    L2_E        9020.77          9020.77      0.000  0
    L5_C        5386.41          5386.41      0.000  0
    L5_D        3847.23          3847.23      0.000  0
    L6_F        4456.66          4456.66      0.000  0

Nieaktualne twierdzenie zostało w `src/Sim/Signalling/SignallingPlan.cs`,
w `tools/blender/sweep.py` i w komentarzu `tools/tests/test_chunks.py`, razem
z liczbą 6686,99 m. Żaden test tego nie widział, bo liczba stała w KOMENTARZU
i w dokumentacji XML — nie w wyniku, który cokolwiek porównuje. To ta sama rodzina,
co dolne ograniczenie z T-401 (`test_t401_citation.py`).

CZEGO TA BRAMKA NIE ROBI: nie każe usunąć przycinania ani rozszerzania planu za oś.
Zmierzone, że jedno i drugie jest nadal potrzebne — plan pakietu A sięga 47,00 m za
koniec osi, bo blok peronowy jest wyśrodkowany na stacji, a ostatnia stacja leży
dokładnie na końcu osi (47,00 m to połowa 94-metrowego składu M7). Zmieniła się
PRZESŁANKA, nie wniosek, i bramka pilnuje właśnie przesłanki.
"""

import glob
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TRACK = os.path.join(ROOT, "data", "track")

#: Pliki, w których twierdzenie o osi może stać jako stan bieżący.
SCANNED = (
    os.path.join(ROOT, "src", "Sim", "Signalling", "SignallingPlan.cs"),
    os.path.join(ROOT, "tools", "blender", "sweep.py"),
    os.path.join(ROOT, "tools", "tests", "test_chunks.py"),
    os.path.join(ROOT, "docs", "15-classic-signalling.md"),
)

#: Zdanie historyczne wolno zostawić — konwencja tego repozytorium każe zapisywać,
#: co mówiła poprzednia wersja tekstu. Markery mówią o POPRZEDNIEJ WERSJI TEGO
#: ZDANIA, nie o przeszłości w ogóle: `sprzed` czy `wcześniej` wyłączałyby bramkę
#: na zdaniach o przeszłości SIECI. Ta sama lekcja, co w `test_t401_citation.py`.
HISTORICAL = re.compile(r"[Dd]o #\d+|poprzedni|mówił|był[ao]? —|była —|Do \d{2}\.\d{2}\.20", re.I)


def axes():
    for path in sorted(glob.glob(os.path.join(TRACK, "L*.json"))):
        if ".provenance" in path:
            continue
        with open(path, encoding="utf-8") as handle:
            yield os.path.basename(path)[:-5], json.load(handle)


def test_no_station_lies_beyond_the_end_of_its_axis():
    """Fakt, na którym stoi cała reszta tej bramki — mierzony, nie zakładany."""
    checked = 0
    beyond = []
    for name, document in axes():
        checked += 1
        length = document["length_m"]
        for station in document["stations"]:
            if station["chainage_m"] > length:
                beyond.append(f"{name}: {station['name']} {station['chainage_m']} > {length}")
    assert checked == 6, f"przejrzano {checked} osi zamiast sześciu"
    assert not beyond, f"stacje za końcem osi: {beyond}"


def test_the_last_station_sits_exactly_at_the_end_of_its_axis():
    """Przypadek graniczny jest dziś REGUŁĄ i to jest powód, dla którego obrony zostają.

    Gdyby ostatnia stacja przestała leżeć na końcu osi, uzasadnienia w
    `SignallingPlan.cs` i `sweep.py` przestałyby opisywać rzeczywistość — a to jest
    dokładnie ten rodzaj cichego rozjazdu, który #86 zostawiło po sobie na dwa dni.
    """
    for name, document in axes():
        last = max(station["chainage_m"] for station in document["stations"])
        assert abs(last - document["length_m"]) < 0.005, (
            f"{name}: ostatnia stacja {last} m, koniec osi {document['length_m']} m")


def test_no_file_claims_as_current_that_a_station_is_beyond_the_axis():
    """Twierdzenie w KOMENTARZU nie jest wynikiem, więc nic go dotąd nie porównywało.

    Skan idzie po akapitach (`.md`, docstringi) i wierszach (kod), a zdania jawnie
    historyczne pomija. Mutacja, która przed tą bramką przechodziła cały zestaw:
    przywrócenie „skrajna stacja potrafi wypaść za końcem osi (Merode: 6686,99 m)"
    jako stanu bieżącego.
    """
    stale = []
    checked = 0
    for path in SCANNED:
        assert os.path.isfile(path), path
        text = open(path, encoding="utf-8").read()
        for chunk in text.split("\n\n"):
            if "6686,99" not in chunk and "6686.99" not in chunk:
                continue
            checked += 1
            if HISTORICAL.search(chunk):
                continue
            stale.append(f"{os.path.relpath(path, ROOT)}: {chunk.strip()[:110]}")
    assert not stale, f"twierdzenia o kilometrażu sprzed #86 podane jako bieżące: {stale}"
    assert checked >= 3, (
        f"skan znalazł tylko {checked} wzmianek 6686,99 — dotąd były w trzech plikach, "
        "więc albo pętla przestała czytać, albo wzmianki zniknęły niezauważone")

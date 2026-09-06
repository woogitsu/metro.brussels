#!/usr/bin/env python3
"""Pythonowa połowa bramki zgodności predykatu streamowania.

Predykat okna, plan LOD i plan kolizji są w tym repozytorium napisane DWA razy:

  * wzorcowo w Pythonie — `tools/blender/sweep.py` i `tools/blender/lod.py`,
    liczone przy generowaniu geometrii i pilnujące spójności manifestu,
  * wykonawczo w C# — `src/Game/Assets/StreamingPlan.cs`, liczone w czasie jazdy.

Testy pisane osobno dla każdej strony sprawdzają tylko, czy dana strona zgadza się
sama ze sobą. Rozjazd między nimi nie wywala niczego: robi dziurę w tunelu na jednym
szwie przy jednym kierunku jazdy, i to wszystko.

Dlatego obie strony są przybite do jednej tablicy oczekiwań w
`tests/Game.Tests/fixtures/L1_A-streaming-plans.json`, policzonej raz przez
`tools/tests/make_streaming_fixture.py`. Ten plik pilnuje połowy pythonowej,
`tests/Game.Tests/StreamingPlanTests.cs` — połowy C#. Żadna strona nie woła drugiej.

Wzorzec jest ze skróconego, ale PRAWDZIWEGO manifestu L1_A. Skrócenie polega na
zdjęciu pól nieodtwarzalnych między przebiegami (`sha256`, `bytes`, bboxy); zakresy
chainage zostają dokładnie takie, jakie wyszły z generatora, i to jest cały sens:
próbki leżą na szwach co do bitu.
"""

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import lod as LD  # noqa: E402
import sweep as SW  # noqa: E402

FIXTURES = os.path.join(ROOT, "tests", "Game.Tests", "fixtures")
MANIFEST = os.path.join(FIXTURES, "L1_A-chunks.json")
PLANS = os.path.join(FIXTURES, "L1_A-streaming-plans.json")


def _manifest():
    with open(MANIFEST, encoding="utf-8") as handle:
        return json.load(handle)


def _plans():
    with open(PLANS, encoding="utf-8") as handle:
        return json.load(handle)


def test_streaming_fixture_files_are_present_and_not_empty():
    manifest, plans = _manifest(), _plans()
    assert len(manifest["chunks"]) == 12, len(manifest["chunks"])
    assert len(plans) == 138, len(plans)


def test_python_reference_still_produces_every_row_of_the_fixture():
    """Właściwa bramka: cała tablica, oba kierunki, 138 wierszy."""
    manifest = _manifest()
    thresholds = LD.manifest_thresholds(manifest)
    for row in _plans():
        chainage, heading = row["chainage_m"], row["heading"]
        where = f"chainage {chainage!r}, kierunek {heading!r}"

        low, high = SW.stream_window(chainage, heading=heading)
        assert low == row["window_low_m"], (where, low, row["window_low_m"])
        assert high == row["window_high_m"], (where, high, row["window_high_m"])

        resident = [c["id"] for c in SW.chunks_for_train(manifest, chainage, heading=heading)]
        assert resident == row["resident"], (where, resident, row["resident"])

        plan = LD.lod_plan(manifest, chainage, heading=heading, thresholds=thresholds)
        assert plan == {e["id"]: e["level"] for e in row["lod"]}, (where, plan)

        collision = LD.collision_plan(manifest, chainage, heading=heading)
        assert collision == row["collision"], (where, collision, row["collision"])


def test_a_planted_mismatch_in_the_fixture_actually_fails_the_comparison():
    """Kontrola negatywna do testu wyżej: dowód, że porównanie umie zaświecić.

    6.B15: bez tego `test_python_reference_still_produces_every_row_of_the_fixture`
    mógłby przechodzić zielono nawet wtedy, gdyby porównanie samo z siebie było
    bezzębne (np. gdyby ktoś kiedyś zamienił `assert resident == row["resident"]` na
    coś, co po cichu nie porównuje list punkt po punkcie) — akapit wyżej w tym
    module ostrzega wprost: „rozjazd między nimi nie wywala niczego”. Ten test
    psuje JEDNO pole JEDNEGO wiersza w PAMIĘCI (plik na dysku zostaje nietknięty)
    i sprawdza, że dokładnie ta sama pętla, która stoi w teście wyżej, tę usterkę
    łapie.
    """
    manifest = _manifest()
    plans = _plans()
    row = dict(plans[0])
    chainage, heading = row["chainage_m"], row["heading"]

    real_resident = [c["id"] for c in SW.chunks_for_train(manifest, chainage, heading=heading)]
    assert real_resident == row["resident"], (
        "wiersz 0 ma się zgadzać PRZED psuciem — inaczej test niżej nie mierzy nic")

    # Psucie: dopisanie chunku, którego pociąg w tym punkcie naprawdę nie ma na
    # pokładzie. Plik `L1_A-streaming-plans.json` na dysku nie jest ruszany.
    row["resident"] = real_resident + ["ŻADEN_TAKI_CHUNK"]

    resident = [c["id"] for c in SW.chunks_for_train(manifest, chainage, heading=heading)]
    try:
        assert resident == row["resident"], (chainage, heading, resident, row["resident"])
        zapalila_sie = False
    except AssertionError:
        zapalila_sie = True
    assert zapalila_sie, (
        "porównanie NIE złapało dopisanego chunku — pętla z testu wyżej jest bezzębna")


def test_the_fixture_samples_sit_exactly_on_the_seams():
    """Bez tego wzorzec sprawdzałby wnętrza chunków i nigdy granicy (§5.1)."""
    manifest = _manifest()
    seams = set()
    for chunk in manifest["chunks"]:
        seams.add(float(chunk["start_m"]))
        seams.add(float(chunk["end_m"]))

    sampled = {row["chainage_m"] for row in _plans()}
    hit = seams & sampled
    assert len(hit) == 13, sorted(seams - sampled)

    # I że te szwy naprawdę są ułamkowe — na okrągłych liczbach równość byłaby
    # przypadkiem, a nie dowodem, że wzorzec bierze wartości z manifestu.
    fractional = [s for s in hit if abs(s - round(s)) > 1e-9]
    assert len(fractional) >= 11, sorted(hit)


def test_a_train_exactly_on_a_seam_keeps_both_chunks_resident():
    manifest = _manifest()
    chunks = manifest["chunks"]
    for index in range(1, len(chunks)):
        seam = float(chunks[index]["start_m"])
        assert seam == float(chunks[index - 1]["end_m"]), index
        resident = [c["id"] for c in SW.chunks_in_range(manifest, seam, seam)]
        assert resident == [chunks[index - 1]["id"], chunks[index]["id"]], (seam, resident)


def test_the_trimmed_fixture_manifest_still_passes_the_consistency_checks():
    """Skrócenie nie może zrobić z manifestu czegoś, czego generator by nie wypuścił."""
    manifest = _manifest()
    problems = SW.manifest_problems(manifest)
    assert problems == [], problems


def test_the_fixture_carries_the_window_and_radius_from_the_design_documents():
    streaming = _manifest()["streaming"]
    assert streaming["default_ahead_m"] == 600.0, streaming
    assert streaming["default_behind_m"] == 300.0, streaming
    assert streaming["collision_radius_m"] == LD.COLLISION_RADIUS_M, streaming


def test_the_fixture_thresholds_match_the_lod_levels_header():
    manifest = _manifest()
    thresholds = LD.manifest_thresholds(manifest)
    assert thresholds == [158.0, 404.4], thresholds
    assert [l["level"] for l in manifest["lod_levels"]] == [0, 1, 2]


def test_the_csharp_side_reads_the_same_two_fixture_files():
    """Gdyby C# czytało inny plik, obie połowy przechodziłyby, nie porównując nic.

    Nie uruchamia .NET-a — sprawdza tylko, że nazwy plików w teście C# to te same
    nazwy, które ten moduł tu wczytał.
    """
    path = os.path.join(ROOT, "tests", "Game.Tests", "StreamingPlanTests.cs")
    with open(path, encoding="utf-8") as handle:
        source = handle.read()
    for name in (os.path.basename(MANIFEST), os.path.basename(PLANS)):
        assert f'FixturePath("{name}")' in source, name

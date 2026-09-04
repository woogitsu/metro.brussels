#!/usr/bin/env python3
"""Skrócony manifest i tablica oczekiwanych planów streamowania — dla obu stron.

Dlaczego to istnieje. Predykat okna, plan LOD i plan kolizji są napisane dwa razy:
w Pythonie (`tools/blender/sweep.py`, `tools/blender/lod.py`) jako implementacja
wzorcowa i w C# (`src/Game/Assets/StreamingPlan.cs`) jako to, co naprawdę wykona
scena. Dwie implementacje tego samego predykatu rozjeżdżają się cicho: pierwsza
rozbieżność nie wywala żadnego testu, tylko robi dziurę w tunelu na jednym szwie
przy jednym kierunku jazdy.

Ten skrypt liczy tablicę oczekiwań RAZ, z implementacji pythonowej, i zapisuje ją
do repozytorium. Potem:

  * `tools/tests/test_streaming_fixture.py` sprawdza, że Python nadal daje tę tablicę,
  * `tests/Game.Tests/StreamingPlanTests.cs` sprawdza, że C# daje tę samą tablicę.

Żadna ze stron nie woła drugiej w trakcie testu, a mimo to obie są przybite do tego
samego wyniku. Rozjazd którejkolwiek psuje jej własną bramkę.

Wejście to prawdziwy manifest z `tunnel_sweep.py`, nie wymyślony JSON: chainage szwów
ma wtedy tyle miejsc po przecinku, ile ma naprawdę, a to jest istotne — próbki leżą
DOKŁADNIE na szwach, żeby przypadek „pociąg na granicy dwóch chunków" był sprawdzony
równością, a nie w jej pobliżu.

Użycie (wymaga Blendera tylko do wyprodukowania manifestu wejściowego):

    blender --background --python tools/blender/tunnel_sweep.py -- \
        --centerline data/track/L1_A.json --profile box_double \
        --out build/L1_A.glb --chunk-dir build/chunks/L1_A
    python3 tools/tests/make_streaming_fixture.py \
        build/chunks/L1_A/tunnel_flat_preview-chunks.json
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "blender"))

import sweep as SW  # noqa: E402
import lod as LD  # noqa: E402

FIXTURE_DIR = os.path.join(os.path.dirname(ROOT), "tests", "Game.Tests", "fixtures")
MANIFEST_OUT = os.path.join(FIXTURE_DIR, "L1_A-chunks.json")
PLANS_OUT = os.path.join(FIXTURE_DIR, "L1_A-streaming-plans.json")

# Szew jest tu wartością DOKŁADNĄ, wziętą z manifestu, a nie liczbą wpisaną z ręki.
# Bez tego próbka „na granicy" nigdy nie trafiłaby w granicę: `1754.15` wpisane ręcznie
# mija szew 1754.152651 o cztery milimetry i sprawdza zwykły punkt w środku chunka.
SEAM_OFFSETS_M = (-1.0, 0.0, 1.0)
HEADINGS = (1.0, -1.0)


def trimmed_manifest(manifest):
    """Manifest bez pól nieodtwarzalnych między przebiegami — i tylko bez nich.

    Używa `sweep.deterministic_view`, czyli tej samej funkcji, którą projekt liczy
    porównania dwóch przebiegów. Zdejmuje dokładnie `sweep.VOLATILE_CHUNK_KEYS`
    (`sha256`, `bytes`), także w zagnieżdżonych wpisach `lods` i `collision`.

    Wcześniejsza wersja tego skryptu wycinała ręcznie „pola, których predykat nie
    czyta". To był błąd: razem z nimi wypadało `length_m`, przez co
    `sweep.manifest_problems` nie miało czego sprawdzać i wywalało się na
    `KeyError: 'length_m'`. Wzorzec, którego nie da się przepuścić przez kontrolę
    spójności manifestu, może po cichu zgnić w dziurę albo zakładkę na szwie i nic
    tego nie zauważy. Zostaje więc pełny manifest minus bajty.
    """
    return SW.deterministic_view(manifest)


def sample_chainages(manifest):
    """Próbki chainage: siatka co 250 m plus każdy szew dokładnie i po metrze z obu stron."""
    length = float(manifest["axis_length_m"])
    samples = set()

    # poza osią z obu stron — okno ma tam dawać pustą albo skrajną listę, nie wyjątek
    samples.update((-500.0, -1.0, 0.0))
    value = 0.0
    while value <= length + 500.0:
        samples.add(round(value, 6))
        value += 250.0
    samples.add(round(length, 6))

    for chunk in manifest["chunks"]:
        for edge in (float(chunk["start_m"]), float(chunk["end_m"])):
            for offset in SEAM_OFFSETS_M:
                samples.add(round(edge + offset, 6))

    return sorted(samples)


def build_plans(manifest):
    thresholds = LD.manifest_thresholds(manifest)
    rows = []
    for chainage in sample_chainages(manifest):
        for heading in HEADINGS:
            resident = SW.chunks_for_train(manifest, chainage, heading=heading)
            low, high = SW.stream_window(chainage, heading=heading)
            plan = LD.lod_plan(manifest, chainage, heading=heading, thresholds=thresholds)
            rows.append({
                "chainage_m": chainage,
                "heading": heading,
                "window_low_m": low,
                "window_high_m": high,
                "resident": [c["id"] for c in resident],
                "lod": [{"id": c["id"], "level": plan[c["id"]]} for c in resident],
                "collision": LD.collision_plan(manifest, chainage, heading=heading),
            })
    return rows


def main(argv):
    if len(argv) != 2:
        raise SystemExit(f"użycie: {argv[0]} <manifest-chunks.json>")

    with open(argv[1], encoding="utf-8") as handle:
        manifest = json.load(handle)

    problems = SW.manifest_problems(manifest) + LD.lod_problems(manifest)
    if problems:
        raise SystemExit("BŁĄD: manifest wejściowy niespójny — " + "; ".join(problems))

    small = trimmed_manifest(manifest)

    # Skrócenie nie może zmienić ani jednej decyzji predykatu. Gdyby zmieniło, cała
    # tablica byłaby liczona z innego manifestu niż ten, który trafia do repozytorium.
    full_rows = build_plans(manifest)
    small_rows = build_plans(small)
    if full_rows != small_rows:
        raise SystemExit("BŁĄD: skrócony manifest daje inne plany niż pełny")

    os.makedirs(FIXTURE_DIR, exist_ok=True)
    for path, payload in ((MANIFEST_OUT, small), (PLANS_OUT, small_rows)):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=1, sort_keys=True)
            handle.write("\n")

    residents = sorted({len(r["resident"]) for r in small_rows})
    print(f"[WZORZEC] manifest={MANIFEST_OUT} ({os.path.getsize(MANIFEST_OUT)} B)")
    print(f"[WZORZEC] plany={PLANS_OUT} ({os.path.getsize(PLANS_OUT)} B)")
    print(f"[WZORZEC] wierszy={len(small_rows)} chunkow={len(small['chunks'])} "
          f"progi_lod={LD.manifest_thresholds(small)}")
    print(f"[WZORZEC] rezydentnych chunkow na wiersz: {residents[0]}..{residents[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

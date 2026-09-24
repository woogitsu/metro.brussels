#!/usr/bin/env bash
# MB-01 · Przygotowanie zasobów pakietu A do grywalnego treningu.
#
# **DLACZEGO TEN SKRYPT ISTNIEJE, A NIE POWIELA PRZEPISU.** Do 13.09.2026 przepis
# generacji stał wyłącznie w kroku `Generate package A geometry` workflowa
# `godot-first-run.yml`. Człowiek, który chciał uruchomić trening u siebie, musiał
# wkleić stamtąd **cztery wywołania generatorów** z pięcioma jawnymi parametrami.
# Pierwsza literówka dawała scenę bez peronu albo perony o metr krótsze od decyzji
# właściciela — i wyglądało to jak stan repozytorium, a nie jak pomyłka przepisywania.
#
# **PIĘĆ PARAMETRÓW, ALE TRZY RODZINY — zmierzone w argparse 13.09.2026, a nie odczytane
# z tego skryptu.** Ten akapit jest POPRAWKĄ własnej pierwszej wersji, która mówiła
# „pięć parametrów, z których żaden nie ma wartości domyślnej, a pominięcie żadnego nie
# kończy się błędem": nieprawdą były OBIE połowy.
#   * DWA pominięte dają scenę, która wygląda poprawnie i nią nie jest — i te dwa są
#     powodem, dla którego ten skrypt istnieje. `--platform-length-m design`:
#     `default=None`, a `resolve_platform_length_m(None)` oddaje **94,0 m** jako dolną
#     granicę R-007, z nazwanym powodem i bez ani jednego ostrzeżenia (decyzja
#     właściciela T-212 to 95,0 m). `--component platform --component edge`:
#     `action="append"` bez domyślnej, a pomocy argparse'a stoi „Bez tego budowane są
#     wszystkie" — czyli schody i antresola do 8,30 m pod stropem `box_double` na 4,70 m.
#   * JEDEN pominięty kończy się GŁOŚNO: `--platform-gap-m` jest `required=True`
#     (`tools/blender/station_kit.py:76`), argparse przerywa i Blender wychodzi
#     **kodem 2** — zmierzone, nie przyjęte. Do rodziny cichej ten parametr NIE należy.
#   * JEDEN nie zmienia dziś nic: `--profile` ma `default="box_double"`
#     (`tools/blender/tunnel_sweep.py:51`), czyli DOKŁADNIE tę wartość, którą przepis
#     podaje. Jawny zapis jest tu przypięciem na wypadek zmiany domyślnej, a nie obroną
#     przed ciszą — i tak też jest opisany w bramce.
#
# **Przepis stoi teraz w JEDNYM miejscu — tutaj — a workflow ten skrypt WOŁA.**
# Pilnuje tego `tools/tests/test_playable_scripts.py`: jeśli przepis wróci do YAML-a
# albo rozejdzie się na dwa miejsca, bramka zapala. Bez niej „współdzielenie" byłoby
# zdaniem w dokumencie, a nie własnością drzewa.
#
# Chunki i skorupa M7 nie są w repozytorium (`CLAUDE.md` reguła 8). Powstają tu i teraz,
# więc trening zawsze wczytuje świeżo wygenerowaną geometrię, a nie kopię sprzed miesięcy.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# Blender jest przypięty po wersji i leży POZA workspace (`tools/ci/blender_install.sh`),
# więc woła się go przez `BLENDER_BIN`, a nie przez goły `blender` z PATH. Na maszynie,
# która kiedykolwiek dostała Blendera z apt, w PATH stoi 4.0.2, czyli LEGACY EEVEE —
# a baseline projektu jest z EEVEE Next i te dwie generacje nie są porównywalne.
BLENDER_EXE="${BLENDER_BIN:-blender}"

if ! command -v "$BLENDER_EXE" >/dev/null 2>&1 && [ ! -x "$BLENDER_EXE" ]; then
    echo "[PRZYGOTOWANIE] nie ma Blendera: '$BLENDER_EXE'." >&2
    echo "[PRZYGOTOWANIE] ustaw BLENDER_BIN albo zainstaluj przypiętą wersję:" >&2
    echo "[PRZYGOTOWANIE]   bash tools/ci/blender_install.sh" >&2
    echo "[PRZYGOTOWANIE] wersja i suma: tools/ci/blender-version.txt" >&2
    exit 3
fi

OUT="${1:-build/t400}"
mkdir -p "$OUT/chunks"

echo "[PRZYGOTOWANIE] tunel pakietu A -> $OUT/L1_A.glb"
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/tunnel_sweep.py -- \
    --centerline data/track/L1_A.json --profile box_double --name L1_A \
    --out "$OUT/L1_A.glb" --metrics "$OUT/L1_A-metrics.json" \
    --chunk-dir "$OUT/chunks" --chunk-manifest "$OUT/chunks/L1_A-chunks.json"

echo "[PRZYGOTOWANIE] tory i detale tunelu -> $OUT/chunks"
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/track_detail.py -- \
    --centerline data/track/L1_A.json --manifest "$OUT/chunks/L1_A-chunks.json" \
    --out-dir "$OUT/chunks"

echo "[PRZYGOTOWANIE] skorupa M7 -> $OUT/M7_shell.glb"
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/m7_shell.py -- \
    --out "$OUT/M7_shell.glb" --envelope-out "$OUT/M7_envelope.glb" \
    --report "$OUT/M7_shell.json"

# Kabina kanoniczna — OBIE, czołowa i ogonowa (MB-05). Scena stawia je tą samą
# arytmetyką co skorupę i wybiera widokiem, a nie plikiem: gdyby generator oddawał
# tylko jedną, kabina zależałaby od kierunku jazdy, a plik z jednym końcem wyglądałby
# przy zmianie kierunku dokładnie jak kabina, która zniknęła.
#
# Układ jest KANONICZNY i nie jest kabiną M7 — generator powtarza to zdanie w raporcie
# obok geometrii, a scena w wierszu `[KABINA]` logu przejazdu.
echo "[PRZYGOTOWANIE] kabina kanoniczna -> $OUT/M7_cab.glb"
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/m7_cab_build.py -- \
    --out "$OUT/M7_cab.glb" --report "$OUT/M7_cab.json"

# Perony. Dwa kroki, bo taki jest podział T-211: kilometraże i dolna granica odsunięcia
# krawędzi liczą się czystym Pythonem, a bryły powstają w Blenderze.
#
# `--platform-gap-m` NIE ma wartości domyślnej (R-007: szczeliny peron–pudło nie podaje
# żadne publiczne źródło), więc stoi tu jawnie i jest to ta sama liczba co
# w `tools/ci/station_details.sh`.
#
# Budowane są WYŁĄCZNIE `platform` i `edge`. Reszta zespołu stacji — schody, winda,
# antresola, korytarz, portal — sięga od 1,03 m do 8,30 m nad główką szyny, a strop
# profilu `box_double`, którym zamiatany jest tunel pakietu A, stoi na 4,70 m. Te bryły
# przebijałyby więc strop i kończyły się w nim, bo komora stacyjna (profil `station`,
# strop 5,30 m) nie jest jeszcze wstawiana w przebieg tunelu.
#
# `--platform-length-m design` bierze DECYZJĘ WŁAŚCICIELA (95,0 m, T-212)
# ze `station_components.DESIGN_PLATFORM_LENGTH_M`, zamiast przepisywać tu liczbę po raz
# drugi. Bez tego słowa generator brał wartość domyślną, czyli dolną granicę z R-007
# (94,0 m = długość składu), i scena dostawała perony o metr krótsze niż decyzja.
echo "[PRZYGOTOWANIE] rozkład peronów -> $OUT/L1_A-platforms.json"
python3 tools/track/station_layout.py --axis data/track/L1_A.json \
    --out "$OUT/L1_A-platforms.json" --platform-length-m design

echo "[PRZYGOTOWANIE] bryły peronów -> $OUT/L1_A-platforms.glb"
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/station_kit.py -- \
    --axis data/track/L1_A.json --layout "$OUT/L1_A-platforms.json" \
    --platform-gap-m 0.08 --component platform --component edge \
    --out "$OUT/L1_A-platforms.glb" \
    --metrics "$OUT/L1_A-platforms-metrics.json"

echo "[PRZYGOTOWANIE] neutralna tablica stacji -> $OUT/L1_A-station-board.glb"
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/station_board.py -- \
    --out "$OUT/L1_A-station-board.glb"

ls -la "$OUT" "$OUT/chunks" | sed -n '1,20p'
echo "[PRZYGOTOWANIE] gotowe. Trening: bash tools/dev/play.sh"

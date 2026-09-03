#!/usr/bin/env bash
# T-211 etap 2 i T-011: perony stacyjne i słupki przydrożne.
#
# DLACZEGO TA BRAMKA POWSTAJE. Do 03.09.2026 ani `station_kit.py`, ani
# `detail_markers.py` nie były wołane z ŻADNEGO workflow ani skryptu w `tools/ci`
# — sprawdzone grepem. Oba generują geometrię, oba noszą jawne stałe projektowe
# i oba miały wyłącznie pokrycie testami jednostkowymi przez atrapę `bpy`, czyli
# takie, które nigdy nie dotyka Blendera. Ich bramki odmowy (`--only-station`
# z literówką, okno bez znaczników, słupek w skrajni) nie były sprawdzane nigdy
# i nigdzie — a to są dokładnie te ścieżki, których atrapa nie umie wykonać.
#
# Skrypt jest jeden na dwa generatory, bo dzielą wejście: oba biorą tę samą oś
# pakietu i oba potrzebują layoutu policzonego wcześniej czystym Pythonem.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Blender jest przypięty po wersji i leży POZA workspace (`tools/ci/blender_install.sh`),
# więc woła się go przez `BLENDER_BIN`, a nie przez goły `blender` z PATH. Na maszynie,
# która kiedykolwiek dostała Blendera z apt, w PATH stoi 4.0.2, czyli LEGACY EEVEE —
# a baseline projektu jest z EEVEE Next i te dwie generacje nie są porównywalne.
BLENDER_EXE="${BLENDER_BIN:-blender}"
cd "$ROOT"

OUT="build/t211details"
mkdir -p "$OUT/renders" build renders
REPORT="$OUT/report.txt"
: > "$REPORT"
exec > >(tee -a "$REPORT") 2>&1
SECONDS=0

AXIS="data/track/L1_A.json"
GAP_M="0.08"          # R-007: szczeliny peron–pudło nie podaje żadne źródło, więc jawnie
WINDOW_FROM="400"
WINDOW_TO="700"

fail() {
  echo "BŁĄD: $*" >&2
  exit 1
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "BŁĄD: wymagane polecenie '$1' nie jest dostępne w PATH" >&2
    return 127
  fi
}

# Odmowa MUSI podać powód, inaczej nie jest bramką, tylko awarią. Ta funkcja
# sprawdza trzy rzeczy naraz: że polecenie padło, że NIE zostawiło pliku
# wyjściowego, i że w logu stoi konkretna diagnoza — nie dowolny traceback.
expect_refusal() {
  local label="$1" glb="$2" log="$3" pattern="$4"
  shift 4
  rm -f "$glb"
  if "$@" >"$log" 2>&1; then
    fail "$label: polecenie NIE padło, a miało odmówić"
  fi
  test ! -e "$glb" || fail "$label: odmowa zostawiła plik wyjściowy $glb"
  grep -Eq "$pattern" "$log" || fail "$label: w logu nie ma diagnozy /$pattern/"
  echo "[NEGATYW] $label — OK: $(grep -Eom1 "$pattern" "$log")"
  tail -n 4 "$log" || true
}

echo "T-211 etap 2 (perony) + T-011 (słupki)"
echo "============================================================"
date -u '+UTC: %Y-%m-%dT%H:%M:%SZ'
echo "commit: ${GITHUB_SHA:-local}"
require_command python3 || exit $?
require_command "$BLENDER_EXE" || exit $?
"$BLENDER_EXE" --version | sed -n '1,2p'
test -f "$AXIS" || fail "brak osi wejściowej $AXIS"

echo
echo "[PERONY 1/4] layout z osi — czysty Python, bez Blendera"
python3 tools/track/station_layout.py --axis "$AXIS" --out "$OUT/platforms.json"
python3 - "$OUT/platforms.json" <<'PY'
import json, sys
layout = json.load(open(sys.argv[1], encoding="utf-8"))
platforms = layout["platforms"]
if len(platforms) != 12:
    raise SystemExit(f"BŁĄD: pakiet A ma 12 stacji, layout podaje {len(platforms)}")
for platform in platforms:
    if platform["to_m"] <= platform["from_m"]:
        raise SystemExit(f"BŁĄD: peron {platform['name']} ma niedodatnią długość")
    if not platform["minimum_edge_offset_m"] > 0.0:
        raise SystemExit(f"BŁĄD: peron {platform['name']} ma niedodatnie minimalne odsunięcie")
print(f"[PERONY] {len(platforms)} peronów, odsunięcia "
      f"{min(p['minimum_edge_offset_m'] for p in platforms):.4f}"
      f"–{max(p['minimum_edge_offset_m'] for p in platforms):.4f} m")
PY

echo
echo "[PERONY 2/4] bryły w Blenderze"
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/station_kit.py -- \
  --axis "$AXIS" --layout "$OUT/platforms.json" --platform-gap-m "$GAP_M" \
  --out "$OUT/platforms.glb" --metrics "$OUT/platforms-metrics.json"
test -s "$OUT/platforms.glb" || fail "station_kit.py nie zostawił GLB"

echo
echo "[PERONY 3/4] round-trip GLB przez wydzielony werdykt"
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/glb_roundtrip.py -- \
  --in "$OUT/platforms.glb" --allow-missing-uv --out "$OUT/platforms-roundtrip.json"

echo
echo "[PERONY 4/4] bramka --only-station, pozytyw i negatyw"
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/station_kit.py -- \
  --axis "$AXIS" --layout "$OUT/platforms.json" --platform-gap-m "$GAP_M" \
  --only-station Schuman --out "$OUT/only-schuman.glb"
test -s "$OUT/only-schuman.glb" || fail "--only-station Schuman nie zostawił GLB"
python3 - "$OUT/platforms-metrics.json" "$OUT/only-schuman.glb" "$OUT/platforms.glb" <<'PY'
import os, sys
whole = os.path.getsize(sys.argv[3])
one = os.path.getsize(sys.argv[2])
# Jedna stacja MUSI dać mniej geometrii niż dwanaście. Bez tego porównania
# `--only-station` mógłby po cichu budować wszystko i nikt by nie zauważył.
if one >= whole:
    raise SystemExit(f"BŁĄD: jedna stacja ({one} B) nie jest mniejsza od dwunastu ({whole} B)")
print(f"[PERONY] jedna stacja {one} B < dwanaście {whole} B")
PY
expect_refusal "--only-station z literówką" "$OUT/only-typo.glb" "$OUT/only-typo.log" \
  "nie zbudowano ani jednej bryły" \
  "$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/station_kit.py -- \
  --axis "$AXIS" --layout "$OUT/platforms.json" --platform-gap-m "$GAP_M" \
  --only-station schuman --out "$OUT/only-typo.glb"
expect_refusal "brak --platform-gap-m" "$OUT/no-gap.glb" "$OUT/no-gap.log" \
  "platform-gap-m|required" \
  "$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/station_kit.py -- \
  --axis "$AXIS" --layout "$OUT/platforms.json" --out "$OUT/no-gap.glb"

echo
echo "[SŁUPKI 1/3] layout detali — czysty Python"
python3 tools/track/detail_layout.py --axis "$AXIS" --out "$OUT/details.json" --brake-from-kmh 72

echo
echo "[SŁUPKI 2/3] słupki w oknie ${WINDOW_FROM}–${WINDOW_TO} m"
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/detail_markers.py -- \
  --axis "$AXIS" --layout "$OUT/details.json" \
  --from-m "$WINDOW_FROM" --to-m "$WINDOW_TO" --out "$OUT/details.glb"
test -s "$OUT/details.glb" || fail "detail_markers.py nie zostawił GLB"

echo
echo "[SŁUPKI 3/3] cztery odmowy: dwie granice okna i dwie bramki luzu"
expect_refusal "odwrócone okno" "$OUT/neg-window.glb" "$OUT/neg-window.log" \
  "okno .* jest puste" \
  "$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/detail_markers.py -- \
  --axis "$AXIS" --layout "$OUT/details.json" --from-m "$WINDOW_TO" --to-m "$WINDOW_FROM" \
  --out "$OUT/neg-window.glb"
expect_refusal "okno bez znaczników" "$OUT/neg-empty.glb" "$OUT/neg-empty.log" \
  "nie ma ani jednego znacznika" \
  "$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/detail_markers.py -- \
  --axis "$AXIS" --layout "$OUT/details.json" --from-m 6686.5 --to-m 6686.6 \
  --out "$OUT/neg-empty.glb"
expect_refusal "słupek w skrajni pojazdu" "$OUT/neg-gauge.glb" "$OUT/neg-gauge.log" \
  "wchodzi w skrajnię pojazdu o [0-9.]+ m" \
  "$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/detail_markers.py -- \
  --axis "$AXIS" --layout "$OUT/details.json" --from-m "$WINDOW_FROM" --to-m "$WINDOW_TO" \
  --offset-m 1.5 --out "$OUT/neg-gauge.glb"
expect_refusal "słupek przebija ścianę" "$OUT/neg-wall.glb" "$OUT/neg-wall.log" \
  "przebija ścianę profilu [a-z_]+ o [0-9.]+ m" \
  "$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/detail_markers.py -- \
  --axis "$AXIS" --layout "$OUT/details.json" --from-m "$WINDOW_FROM" --to-m "$WINDOW_TO" \
  --offset-m 9.0 --out "$OUT/neg-wall.glb"

echo
echo "[ZRZUTY] rendery kontrolne"
# Peron jednej stacji, nie dwunastu: kadr obejmujący 6,7 km sprowadza płytę do
# ułamka piksela i klatka wychodzi poniżej podłogi obrazowej. Zmierzone, nie
# przewidziane — to samo znalezisko, co przy słupkach niżej.
"$BLENDER_EXE" --background --python tools/blender/render_check.py -- \
  --in "$OUT/only-schuman.glb" --out "$OUT/renders/PERON"

echo
echo "[VERIFY] Python tool suite"
python3 tools/tests/test_all.py

echo
echo "============================================================"
echo "[RESULT] T-211 etap 2 + T-011 zakończone w ${SECONDS}s"
echo "[RESULT] OGLĘDZINY RENDERÓW SĄ NADAL WYMAGANE:"
for f in "$OUT"/renders/PERON_*.png; do
  test -e "$f" || continue
  echo "[RESULT]   $f ($(stat -c%s "$f") B)"
done
echo "[RESULT] metryka automatyczna nie zastępuje obejrzenia PNG (CLAUDE.md §5)"
echo "[RESULT] UWAGA: słupki 0,12 x 0,20 m NIE mają tu renderu i to jest świadome —"
echo "[RESULT] render_check.py kadruje bbox całego GLB, więc słupek wychodzi poniżej"
echo "[RESULT] podłogi obrazowej. Sensowny zrzut wymaga kamery kadrującej jeden słupek."

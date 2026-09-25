#!/usr/bin/env bash
# Lokalny baseline T-400. Xvfb trzyma okno poza ekranem użytkownika.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

GODOT_EXE="${GODOT_BIN:-$(bash tools/ci/godot_install.sh)}"
BLENDER_EXE="${BLENDER_BIN:-$(bash tools/ci/blender_install.sh)}"
ASSETS="$ROOT/build/t400"
OUT="$ROOT/build/perf/scene-1080p"
mkdir -p "$OUT"

if [ ! -f "$ASSETS/chunks/L1_A-chunks.json" ]; then
    BLENDER_BIN="$BLENDER_EXE" bash tools/dev/prepare-playable.sh "$ASSETS" >"$OUT/prepare.log" 2>&1
fi

dotnet build src/Game/MetroBxl.Game.csproj -c Debug --nologo >"$OUT/build.log" 2>&1

for repeat in 1 2 3; do
    log="$OUT/run-$repeat.log"
    /usr/bin/time -f '%M' -o "$OUT/run-$repeat.max-rss-kb" \
        xvfb-run -a "$GODOT_EXE" --audio-driver Dummy \
        --rendering-driver opengl3 --resolution 1920x1080 \
        --path src/Game --script "$ROOT/tools/perf/scene_1080p.gd" -- \
        "--assets=$ASSETS" >"$log" 2>&1
    python3 - "$log" <<'PY'
import json
from pathlib import Path
import sys

log = Path(sys.argv[1])
text = log.read_text(encoding="utf-8")
lines = [line.removeprefix("[PERF] ") for line in text.splitlines()
         if line.startswith("[PERF] ")]
if len(lines) != 1 or "SCRIPT ERROR:" in text or "ERROR:" in text:
    raise SystemExit(f"{log}: brak pojedynczego pomiaru albo błąd Godota")
result = json.loads(lines[0])
if (result["resolution"] != [1920, 1080] or result["draw_calls"]["median"] <= 0
        or result["scene_steps"] <= 0):
    raise SystemExit(f"{log}: zła rozdzielczość, pusta klatka albo brak kroków sceny")
print(f"{log}: {result['frames']} klatek, mediana {result['frame_ms']['median']:.3f} ms, "
      f"draw calls {result['draw_calls']['median']:.0f}, "
      f"krok sceny {result['scene_step_us']['median']:.3f} µs")
PY
done

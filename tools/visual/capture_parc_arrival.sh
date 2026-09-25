#!/usr/bin/env bash
# Record one continuous, deterministic line run under Xvfb. Keep raw frames out of Git.
set -euo pipefail

source_dir="${GAME_SOURCE:?set GAME_SOURCE to a checkout of the source commit}"
godot_bin="${GODOT_BIN:?set GODOT_BIN to the pinned Godot 4.7.2 Mono binary}"
export BLENDER_BIN="${BLENDER_BIN:?set BLENDER_BIN to the pinned Blender binary}"
expected=1afb4d6235b5811699f5221cac58e47e8ac5957f
actual="$(git -C "$source_dir" rev-parse HEAD)"
if [[ "$actual" != "$expected" ]]; then
  echo "Expected source $expected, got $actual" >&2
  exit 1
fi

cd "$source_dir"
bash tools/dev/prepare-playable.sh build/t400
dotnet build src/Game/MetroBxl.Game.csproj --configuration Debug --nologo
out="$PWD/build/t400/parc-movie/hd"
mkdir -p "$out"
xvfb-run -a "$godot_bin" --rendering-driver opengl3 --resolution 1280x720 \
  --write-movie "$out/arrival.png" --quit-after 1835 --path src/Game -- \
  --line --limit-kmh=70 --view=outside --steps-per-frame=30 \
  --calls="$out/calls.csv" > "$out/arrival.log" 2>&1
count="$(find "$out" -maxdepth 1 -name 'arrival????????.png' | wc -l)"
test "$count" -eq 1835 || { echo "Expected 1835 PNG frames, got $count" >&2; exit 1; }
echo "$out"

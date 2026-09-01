#!/usr/bin/env bash
# T-012: pipeline kontroli wizualnej na GitHub-hosted Linux (ubuntu-latest).
# Dowodzi: determinizm renderu, wykrywanie regresji, odrzucanie pustej klatki
# i to, że brak baseline nie prowadzi do cichego nadpisania.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

OUT="build/t012visual"
mkdir -p "$OUT" build renders data/track
REPORT="$OUT/report.txt"
: > "$REPORT"
exec > >(tee -a "$REPORT") 2>&1
SECONDS=0

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

echo "T-012 kontrola wizualna — pipeline Blender"
echo "============================================================"
date -u '+UTC: %Y-%m-%dT%H:%M:%SZ'
echo "repo: $ROOT"
echo "commit: ${GITHUB_SHA:-local}"

echo
echo "[ENV] runner"
uname -a
if [ -r /etc/os-release ]; then cat /etc/os-release; fi
require_command python3 || exit $?
require_command blender || exit $?
python3 --version
blender --version | head -n 3

echo
echo "[VERIFY] testy narzędzi (w tym testy pipeline'u wizualnego)"
python3 tools/tests/test_all.py

echo
echo "[SETUP] deterministyczna geometria testowa"
python3 tools/track/make_test_track.py --out data/track/TEST.json
blender --background --python-exit-code 7 --python tools/blender/tunnel_sweep.py -- \
  --centerline data/track/TEST.json --profile box_double --out build/TEST.glb >"$OUT/tunnel.log" 2>&1 \
  || { cat "$OUT/tunnel.log"; fail "generowanie tunelu testowego nie powiodło się"; }
grep -E '^\[RAPORT\]' "$OUT/tunnel.log"

capture() {
  local outdir="$1"; shift
  blender --background --python-exit-code 7 --python tools/visual/capture_blender.py -- \
    --in build/TEST.glb --set infrastructure --prefix VIS_TUNNEL --out "$outdir" \
    --centerline data/track/TEST.json "$@" >"$OUT/capture_$(basename "$outdir").log" 2>&1 \
    || { tail -n 40 "$OUT/capture_$(basename "$outdir").log"; fail "capture do $outdir nie powiódł się"; }
  grep -E '^\[(RENDER|SKIP|RAPORT|TEST-SHIFT)\]' "$OUT/capture_$(basename "$outdir").log"
}

echo
echo "[CAPTURE] przebieg A (kandydat na baseline)"
rm -rf renders/ci_a renders/ci_b renders/ci_shift
capture renders/ci_a

echo
echo "[CAPTURE] przebieg B (ten sam wejściowy GLB, te same kamery)"
capture renders/ci_b

echo
echo "[TEST 1/5] brak baseline musi dać status new-baseline, nie pass"
if python3 tools/visual/compare.py --set infrastructure --current renders/ci_b --prefix VIS_TUNNEL \
    --out "$OUT/no-baseline.json" >"$OUT/no-baseline.log" 2>&1; then
  cat "$OUT/no-baseline.log"
  fail "brak baseline został potraktowany jako sukces"
fi
grep -c 'new-baseline' "$OUT/no-baseline.log" >/dev/null || fail "brak statusu new-baseline"
tail -n 3 "$OUT/no-baseline.log"
test ! -d visual-baseline || fail "baseline powstał bez jawnego zatwierdzenia"

echo
echo "[TEST 2/5] determinizm: przebieg B względem przebiegu A musi przejść"
python3 tools/visual/compare.py --set infrastructure --current renders/ci_b --prefix VIS_TUNNEL \
  --baseline renders/ci_a --diff-dir "$OUT/diff-determinism" \
  --out "$OUT/determinism.json" --markdown "$OUT/determinism.md" \
  || fail "dwa identyczne przebiegi renderu nie są zgodne"

echo
echo "[TEST 3/5] pusta/czarna klatka musi zostać odrzucona"
mkdir -p renders/ci_black
cp renders/ci_b/VIS_TUNNEL_metadata.json renders/ci_black/
python3 - <<'PY'
import json, os, sys
sys.path.insert(0, os.path.join("tools", "visual"))
import pngio
meta = json.load(open("renders/ci_b/VIS_TUNNEL_metadata.json", encoding="utf-8"))
w, h = meta["resolution"]
for camera in meta["cameras"]:
    pngio.write_gray(os.path.join("renders/ci_black", os.path.basename(camera["file"])), w, h, [0.0] * (w * h))
print(f"[SETUP] wygenerowano {len(meta['cameras'])} czarnych klatek {w}x{h}")
PY
if python3 tools/visual/compare.py --set infrastructure --current renders/ci_black --prefix VIS_TUNNEL \
    --baseline renders/ci_a --out "$OUT/black.json" >"$OUT/black.log" 2>&1; then
  cat "$OUT/black.log"
  fail "czarna klatka przeszła kontrolę"
fi
grep -q 'obraz pusty/jednorodny' "$OUT/black.log" || { cat "$OUT/black.log"; fail "brak diagnostyki pustej klatki"; }
tail -n 4 "$OUT/black.log"

echo
echo "[TEST 4/5] zmieniona rozdzielczość musi zostać odrzucona"
mkdir -p renders/ci_size
cp renders/ci_b/VIS_TUNNEL_metadata.json renders/ci_size/
python3 - <<'PY'
import json, os, sys
sys.path.insert(0, os.path.join("tools", "visual"))
import pngio
meta = json.load(open("renders/ci_b/VIS_TUNNEL_metadata.json", encoding="utf-8"))
w, h = [v // 2 for v in meta["resolution"]]
for camera in meta["cameras"]:
    gray = [0.3 + 0.4 * ((x // 8 + y // 8) % 2) for y in range(h) for x in range(w)]
    pngio.write_gray(os.path.join("renders/ci_size", os.path.basename(camera["file"])), w, h, gray)
print(f"[SETUP] wygenerowano klatki w złej rozdzielczości {w}x{h}")
PY
if python3 tools/visual/compare.py --set infrastructure --current renders/ci_size --prefix VIS_TUNNEL \
    --baseline renders/ci_a --out "$OUT/size.json" >"$OUT/size.log" 2>&1; then
  cat "$OUT/size.log"
  fail "zła rozdzielczość przeszła kontrolę"
fi
grep -q 'rozdzielczość' "$OUT/size.log" || { cat "$OUT/size.log"; fail "brak diagnostyki rozdzielczości"; }
tail -n 4 "$OUT/size.log"

echo
echo "[TEST 5/5] sztucznie przesunięta geometria musi przekroczyć próg"
capture renders/ci_shift --test-shift 0,0,1.5
if python3 tools/visual/compare.py --set infrastructure --current renders/ci_shift --prefix VIS_TUNNEL \
    --baseline renders/ci_a --diff-dir "$OUT/diff-regression" \
    --out "$OUT/regression.json" --markdown "$OUT/regression.md" >"$OUT/regression.log" 2>&1; then
  cat "$OUT/regression.log"
  fail "przesunięta geometria nie została wykryta jako regresja"
fi
cat "$OUT/regression.log"
for suffix in before current diff; do
  test -s "$OUT/diff-regression/VIS_TUNNEL_section_${suffix}.png" \
    || fail "brak artefaktu ${suffix} przy regresji"
done

echo
echo "[ARTEFAKTY] kopiowanie renderów do artefaktu CI"
mkdir -p "$OUT/renders"
cp renders/ci_a/*.png renders/ci_a/*.json "$OUT/renders/" 2>/dev/null || true
python3 - <<'PY'
import json, os
for name in ("determinism", "regression"):
    path = os.path.join("build/t012visual", f"{name}.json")
    if not os.path.isfile(path):
        continue
    data = json.load(open(path, encoding="utf-8"))
    print(f"[WYNIK] {name}: {data['status']} {data['summary']}")
PY

echo
echo "============================================================"
echo "[RESULT] T-012 pipeline wizualny przeszedł w ${SECONDS}s"
echo "[RESULT] manual visual gate NADAL WYMAGANY dla:"
for f in "$OUT"/renders/VIS_TUNNEL_*.png; do echo "[RESULT]   $f"; done
echo "[RESULT] metryka automatyczna nie zastępuje obejrzenia PNG (CLAUDE.md §5)"

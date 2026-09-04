#!/usr/bin/env bash
# Bramka T-902: neutralny baseline materiałowy.
#
# `docs/03-legal.md` zabrania liverii, logo i wystroju STIB/MIVB. Ta bramka nie
# sprawdza, czy scena „ładnie wygląda" — od oceny estetycznej agent ma się trzymać
# z daleka (CLAUDE.md §8). Sprawdza rzeczy rozstrzygalne: że zestaw materiałów
# powstał ze skryptu i z pliku konfiguracyjnego, że renderują się trzy kadry i że
# żaden z nich nie jest pustą ani jednolitą klatką.
#
# Kontrola negatywna jest tu obowiązkowa, bo skrypt kończący się bez błędu potrafi
# wyprodukować pustą scenę (CLAUDE.md §5). Każda odmowa jest sprawdzana na TRZECH
# warunkach naraz: polecenie padło, NIE zostawiło pliku wyjściowego, a w logu stoi
# konkretna diagnoza.
set -euo pipefail

BLENDER_EXE="${BLENDER_BIN:-blender}"
CONFIG="data/design/visual-style.json"
OUT="build/style/materials.glb"
RENDER_PREFIX="renders/style"
LOG_DIR="build/style/logs"

fail() { echo "BŁĄD: $*" >&2; exit 1; }

mkdir -p "$(dirname "$OUT")" "$LOG_DIR" renders

echo "[T-902] Blender: $("$BLENDER_EXE" --version 2>/dev/null | sed -n '1p')"

rm -f "$OUT" "${RENDER_PREFIX}"_*.png

"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/material_test_scene.py -- \
  --config "$CONFIG" --out "$OUT" --renders "$RENDER_PREFIX" | tee "$LOG_DIR/run.log"

test -s "$OUT" || fail "generator nie zostawił $OUT"
for view in iso side close; do
  test -s "${RENDER_PREFIX}_${view}.png" || fail "brak renderu ${RENDER_PREFIX}_${view}.png"
done

# Raport generatora NIE jest weryfikacją generatora: to ta sama strona umowy.
# Liczba materiałów jest więc porównywana z DWIEMA stronami — z plikiem
# konfiguracyjnym i z wyeksportowanym GLB, którego węzły czytamy niezależnie,
# bez Blendera. Preset dopisany do konfiguracji, a nieobecny w scenie, przechodził
# przez `grep -q "material_presets="` tak samo dobrze jak preset zbudowany.
CONFIG="$CONFIG" OUT="$OUT" LOG="$LOG_DIR/run.log" python3 - <<'PY'
import json, os, re, struct, sys

config = json.load(open(os.environ["CONFIG"], encoding="utf-8"))
declared = [m["id"] for m in config["material_presets"]]

log = open(os.environ["LOG"], encoding="utf-8").read()
match = re.search(r"material_presets=(\d+) mesh_objects=(\d+)", log)
if not match:
    raise SystemExit("BŁĄD: raport nie podaje liczby materiałów ani brył")
reported, meshes = int(match.group(1)), int(match.group(2))

blob = open(os.environ["OUT"], "rb").read()
if blob[:4] != b"glTF":
    raise SystemExit("BŁĄD: %s nie jest plikiem GLB" % os.environ["OUT"])
offset, document = 12, None
while offset < len(blob):
    length, kind = struct.unpack("<II", blob[offset:offset + 8])
    if kind == 0x4E4F534A:  # 'JSON'
        document = json.loads(blob[offset + 8:offset + 8 + length].decode("utf-8"))
        break
    offset += 8 + length + ((4 - length % 4) % 4)
if document is None:
    raise SystemExit("BŁĄD: GLB nie ma chunku JSON")

names = [node.get("name", "") for node in document.get("nodes", [])]
swatches = [n for n in names if n.startswith("swatch_")]

problems = []
if reported != len(declared):
    problems.append("raport mówi %d materiałów, konfiguracja ma %d" % (reported, len(declared)))
if meshes != len(declared) + 1:
    problems.append("brył jest %d, a %d materiałów + podłoga to %d"
                    % (meshes, len(declared), len(declared) + 1))
missing = [i for i in declared if not any(n.endswith("_" + i) for n in swatches)]
if missing:
    problems.append("presety bez bryły w GLB: " + ", ".join(missing))
extra = len(swatches) - len(declared)
if extra:
    problems.append("w GLB jest %+d brył swatch_ ponad liczbę presetów" % extra)

if problems:
    for line in problems:
        print("BŁĄD: " + line, file=sys.stderr)
    raise SystemExit(1)

print("[ZGODNOŚĆ] %d presetów z konfiguracji ma po jednej bryle w GLB, "
      "raport generatora podaje tę samą liczbę" % len(declared))
PY


# Trzy kadry to nie trzy pliki: pusta klatka też jest plikiem. Progi są te same,
# co dla renderów Blenderowych z T-012, i mierzone tym samym narzędziem.
python3 - <<'PY'
import sys, os
sys.path.insert(0, os.path.join("tools", "visual"))
import pngio

problems = []
for view in ("iso", "side", "close"):
    path = f"renders/style_{view}.png"
    image = pngio.read_gray(path)
    values = image.gray
    lo, hi = min(values), max(values)
    mean = sum(values) / len(values)
    spread = hi - lo
    print(f"[KLATKA] {path} {image.width}x{image.height} "
          f"min={lo:.4f} max={hi:.4f} śr={mean:.4f} rozpiętość={spread:.4f}")
    # Klatka bez geometrii jest jednolita: rozpiętość schodzi wtedy do zera.
    if spread < 0.20:
        problems.append(f"{path}: rozpiętość {spread:.4f} < 0.20 — klatka jednolita")
    if mean < 0.02:
        problems.append(f"{path}: średnia {mean:.4f} — klatka praktycznie czarna")

if problems:
    for line in problems:
        print("BŁĄD: " + line, file=sys.stderr)
    raise SystemExit(1)
PY

echo "[T-902] wszystkie kontrole przeszły"

# --- kontrole negatywne -------------------------------------------------------
expect_refusal() {
  local label="$1" artefact="$2" log="$3" pattern="$4"
  shift 4
  rm -f "$artefact"
  if "$@" >"$log" 2>&1; then
    fail "$label: polecenie NIE padło, a miało odmówić"
  fi
  test ! -e "$artefact" || fail "$label: odmowa zostawiła plik $artefact"
  grep -Eq "$pattern" "$log" || fail "$label: w logu nie ma diagnozy /$pattern/"
  # `grep -o` wypisuje KAŻDE trafienie w linii, a `-m1` ogranicza liczbę linii,
  # nie trafień: „FileNotFoundError: [Errno 2] No such file or directory" daje dwa.
  # `sed -n '1p'` bierze pierwsze i nie wywołuje SIGPIPE, inaczej niż `head`.
  echo "[NEGATYW] $label — OK: $(grep -Eo "$pattern" "$log" | sed -n '1p')"
}

expect_refusal "brak pliku konfiguracji" "build/style/nieistotny.glb" \
  "$LOG_DIR/nc_config.log" "No such file|FileNotFoundError|nie istnieje" \
  "$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/material_test_scene.py -- \
    --config data/design/nie-ma-takiego-pliku.json --out build/style/nieistotny.glb --renders build/style/nc

expect_refusal "brak wymaganego argumentu" "build/style/bezargu.glb" \
  "$LOG_DIR/nc_args.log" "required|wymagan" \
  "$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/material_test_scene.py -- \
    --out build/style/bezargu.glb --renders build/style/nc

# Trzy odmowy generatora, których poprzednia wersja tej bramki (cztery `test -s`
# na plikach wyjściowych) nie mogła wykonać ani razu, bo każda potrzebuje
# uruchomionego Blendera z WCZYTANĄ konfiguracją. Konfiguracje są mutowane
# ze zdrowego pliku, żeby odmowa nie padła z zupełnie innego powodu niż mierzony —
# ręcznie napisany JSON łatwo psuje się gdzie indziej.
mutate() {
  CONFIG="$CONFIG" DEST="$2" python3 - "$1" <<'PY'
import json, os, sys

document = json.load(open(os.environ["CONFIG"], encoding="utf-8"))
kind = sys.argv[1]
if kind == "empty":
    document["material_presets"] = []
elif kind == "duplicate":
    document["material_presets"].append(dict(document["material_presets"][0]))
elif kind == "no_close":
    document["material_presets"] = [m for m in document["material_presets"]
                                    if m["id"] != "brushed_metal"]
else:
    raise SystemExit("nieznana mutacja: " + kind)
json.dump(document, open(os.environ["DEST"], "w", encoding="utf-8"), ensure_ascii=False)
PY
}

mutate empty "$LOG_DIR/cfg_empty.json"
expect_refusal "pusta lista materiałów" "build/style/pusty.glb" \
  "$LOG_DIR/nc_empty.log" "material_presets jest puste" \
  "$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/material_test_scene.py -- \
    --config "$LOG_DIR/cfg_empty.json" --out build/style/pusty.glb --renders build/style/nc

mutate duplicate "$LOG_DIR/cfg_dup.json"
expect_refusal "powtórzony identyfikator materiału" "build/style/dup.glb" \
  "$LOG_DIR/nc_dup.log" "niepuste i unikalne" \
  "$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/material_test_scene.py -- \
    --config "$LOG_DIR/cfg_dup.json" --out build/style/dup.glb --renders build/style/nc

# Ta odmowa pada PO zbudowaniu sceny i jest jedyną, która sprawdza, że kamera
# `close` ma na co patrzeć. Bez niej usunięcie `brushed_metal` z konfiguracji dałoby
# kadr wycelowany w środek pustego miejsca — i klatkę, która przeszłaby przez
# kontrolę rozpiętości, bo w tle nadal stoją pozostałe bryły.
mutate no_close "$LOG_DIR/cfg_noclose.json"
expect_refusal "brak materiału dla kamery close" "build/style/noclose.glb" \
  "$LOG_DIR/nc_noclose.log" "wymaganych przez kamerę close" \
  "$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/material_test_scene.py -- \
    --config "$LOG_DIR/cfg_noclose.json" --out build/style/noclose.glb --renders build/style/nc

# Odtworzenie właściwego wyjścia po kontrolach negatywnych — artefakt joba ma
# zawierać wynik przebiegu, a nie to, co zostało po ostatniej odmowie.
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/material_test_scene.py -- \
  --config "$CONFIG" --out "$OUT" --renders "$RENDER_PREFIX" >"$LOG_DIR/rerun.log" 2>&1
test -s "$OUT" || fail "odtworzenie po kontrolach negatywnych nie dało $OUT"

echo "[T-902] bramka zakończona, $(du -sh build/style renders 2>/dev/null | tr '\n' ' ')"

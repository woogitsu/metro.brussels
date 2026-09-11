#!/usr/bin/env bash
# T-220: generowanie i weryfikacja proceduralnej bryły M7 na GitHub-hosted Linux.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Blender jest przypięty po wersji i leży POZA workspace (`tools/ci/blender_install.sh`),
# więc woła się go przez `BLENDER_BIN`, a nie przez goły `blender` z PATH. To nie jest
# ozdoba: na maszynie, która kiedykolwiek miała `apt-get install blender`, w PATH stoi
# 4.0.2, czyli LEGACY EEVEE — a baseline projektu jest z EEVEE Next i te dwie generacje
# nie są porównywalne (`tools/visual/capture_plan.py`, `EEVEE_NEXT_SINCE`). Fallback na
# PATH zostaje, żeby uruchomienie z ręki na maszynie z jednym Blenderem dalej działało.
# Ta sama konwencja co `GODOT_BIN`.
BLENDER_EXE="${BLENDER_BIN:-blender}"
cd "$ROOT"

OUT="build/t220"
mkdir -p "$OUT" build renders
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

echo "T-220 proceduralna bryła M7"
echo "============================================================"
date -u '+UTC: %Y-%m-%dT%H:%M:%SZ'
echo "commit: ${GITHUB_SHA:-local}"

echo
echo "[ENV] runner"
uname -a
require_command python3 || exit $?
require_command "$BLENDER_EXE" || exit $?
python3 --version
"$BLENDER_EXE" --version | sed -n '1,3p'

echo
echo "[VERIFY] testy narzędzi"
python3 tools/tests/test_all.py

echo
echo "[GENERATE] bryła M7 ze skryptu"
rm -f build/M7_shell.glb build/M7_envelope.glb build/M7_shell.json
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/m7_shell.py -- \
  --out build/M7_shell.glb --envelope-out build/M7_envelope.glb --report build/M7_shell.json \
  >"$OUT/generate.log" 2>&1 || { tail -n 40 "$OUT/generate.log"; fail "generator M7 nie powiódł się"; }
grep -E '^\[RAPORT\]' "$OUT/generate.log"
cp build/M7_shell.json "$OUT/M7_shell.json"

echo
echo "[VERIFY] twarde kontrole geometryczne z raportu generatora"
python3 - <<'PY'
import json, sys

report = json.load(open("build/M7_shell.json", encoding="utf-8"))
spec = report["spec_values"]
body = report["body"]
problems = []


def close(actual, expected, tolerance, label):
    if abs(actual - expected) > tolerance:
        problems.append(f"{label}: {actual!r} != {expected!r} (tol {tolerance})")
    else:
        print(f"[OK] {label}: {actual:.6f} (oczekiwane {expected}, tol {tolerance})")


close(body["size_m"][0], spec["length_m"], 0.001, "długość bbox")
close(body["size_m"][1], spec["width_m"], 0.001, "szerokość bbox")
close(body["bbox_min"][0], 0.0, 0.001, "origin X")
close(body["bbox_max"][0], spec["length_m"], 0.001, "koniec X")
close(body["bbox_min"][2], spec["floor_height_m"] - report["design_assumptions"]["shell_thickness_m"]["value"],
      0.001, "spód pudła")

if body["cars"] != spec["cars"]:
    problems.append(f"człony: {body['cars']} != {spec['cars']}")
else:
    print(f"[OK] człony: {body['cars']}")

openings = report["opening_summary"]
if openings["double_per_side"] != spec["double_doors_per_side"]:
    problems.append(f"drzwi podwójne/stronę: {openings['double_per_side']}")
else:
    print(f"[OK] drzwi podwójne na stronę: {openings['double_per_side']}")
if openings["cab_total"] != spec["single_cab_doors_total"]:
    problems.append(f"drzwi kabinowe: {openings['cab_total']}")
else:
    print(f"[OK] drzwi kabinowe: {openings['cab_total']}")
if openings["double_edges_found"] != openings["double_total"]:
    problems.append("nie wszystkie otwory mają krawędzie w geometrii")
else:
    print(f"[OK] otwory z krawędziami w siatce: {openings['double_edges_found']}/{openings['double_total']}")

for opening in report["openings"]:
    if opening["kind"] != "double":
        continue
    if abs(opening["measured_width_m"] - spec["double_door_opening_width_m"]) > 0.001:
        problems.append(f"otwór x={opening['center_x']}: {opening['measured_width_m']}")
print(f"[OK] każdy otwór podwójny zmierzony w geometrii = {spec['double_door_opening_width_m']} m")

if not report["gauge"]["vehicle_gauge_ok"]:
    problems.append(f"skrajnia pojazdu: {report['gauge']['vehicle_gauge_message']}")
for name, entry in report["gauge"]["tunnel_profiles"].items():
    if not entry["ok"]:
        problems.append(f"profil {name}: {entry['message']}")
    else:
        print(f"[OK] skrajnia w profilu {name}, luz {entry['min_clearance_m']:.2f} m")

if not report["rotational_symmetry"]["ok"]:
    problems.append(f"symetria obrotowa: {report['rotational_symmetry']['mismatched']} wierzchołków")
else:
    print(f"[OK] symetria obrotowa 180°: {report['rotational_symmetry']['vertices']} wierzchołków")

if not report["roundtrip"]["ok"]:
    problems.append(f"re-import GLB: {report['roundtrip']}")
else:
    print(f"[OK] eksport i re-import GLB, max_delta={report['roundtrip']['max_delta_m']} m")

if not 1000 < body["vertices"] < 500000:
    problems.append(f"liczba wierzchołków: {body['vertices']}")
else:
    print(f"[OK] wierzchołki={body['vertices']} ściany={body['faces']}")

if problems:
    for problem in problems:
        print(f"BŁĄD: {problem}", file=sys.stderr)
    raise SystemExit(1)
print("[OK] wszystkie kontrole raportu przeszły")
PY

echo
echo "[VERIFY] GLB istnieje i ma poprawny magic/header"
python3 - <<'PY'
import os
for path in ("build/M7_shell.glb", "build/M7_envelope.glb"):
    size = os.path.getsize(path)
    with open(path, "rb") as handle:
        magic = handle.read(4)
    if magic != b"glTF":
        raise SystemExit(f"BŁĄD: {path} ma zły magic {magic!r}")
    if size <= 1024:
        raise SystemExit(f"BŁĄD: {path} jest podejrzanie mały: {size} B")
    print(f"[OK] {path}: {size} B, magic glTF")
PY

echo
echo "[NEGATIVE] wymiar bez statusu spec musi zatrzymać generator"
python3 - <<'PY'
import json
registry = json.load(open("data/vehicle/m7-spec.json", encoding="utf-8"))
registry["parameters"]["length_m"]["status"] = "design_model"
json.dump(registry, open("build/t220/broken-spec.json", "w", encoding="utf-8"), ensure_ascii=False)
print("[SETUP] rejestr z length_m oznaczonym jako design_model")
PY
if "$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/m7_shell.py -- \
    --spec build/t220/broken-spec.json --out build/t220/should-not-exist.glb \
    --envelope-out build/t220/should-not-exist-env.glb --report build/t220/broken.json \
    >"$OUT/negative-spec.log" 2>&1; then
  fail "generator przyjął wymiar bez statusu spec"
fi
grep -q 'nie ma statusu spec' "$OUT/negative-spec.log" || { tail -n 20 "$OUT/negative-spec.log"; fail "brak czytelnej diagnostyki"; }
test ! -e build/t220/should-not-exist.glb || fail "powstał GLB mimo odrzuconego wymiaru"
tail -n 3 "$OUT/negative-spec.log"

echo
echo "[RENDER] canonical zestaw kamer T-012 dla pojazdu"
DOOR_ANCHOR="$(cd tools/blender && python3 -c "
import sys
sys.path.insert(0, '.')
from m7_layout import Layout
layout = Layout()
door = [d for d in layout.double_doors() if d['side'] == 1][0]
print(f\"{door['center_x']},{layout.half_width},{(door['z0'] + door['z1']) / 2}\")")"
echo "kotwica drzwi: $DOOR_ANCHOR"
rm -rf renders/m7
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/visual/capture_blender.py -- \
  --in build/M7_shell.glb --set vehicle --prefix M7_shell --out renders/m7 \
  --anchor "door=$DOOR_ANCHOR" >"$OUT/capture.log" 2>&1 \
  || { tail -n 40 "$OUT/capture.log"; fail "render kontrolny nie powiódł się"; }
grep -E '^\[(RENDER|SKIP|RAPORT)\]' "$OUT/capture.log"

echo
echo "[VERIFY] sanity renderów (brak baseline jest tu świadomy)"
python3 tools/visual/compare.py --set vehicle --current renders/m7 --prefix M7_shell \
  --allow-new-baseline --out "$OUT/visual.json" --markdown "$OUT/visual.md" \
  || fail "rendery M7 nie przeszły kontroli sanity"

echo
echo "[VERIFY] szerokość otworu drzwiowego zmierzona NA RENDERZE"
python3 - <<'PY'
import json, math, os, sys
sys.path.insert(0, os.path.join("tools", "visual"))
import pngio

meta = json.load(open("renders/m7/M7_shell_metadata.json", encoding="utf-8"))
camera = next(c for c in meta["cameras"] if c["id"] == "door")
image = pngio.read_gray("renders/m7/M7_shell_door.png")
frame_w = 2 * camera["distance_m"] * math.tan(math.radians(camera["fov_x_deg"]) / 2)
metres_per_pixel = frame_w / image.width

row = image.gray[(image.height // 2) * image.width:(image.height // 2 + 1) * image.width]
threshold = min(row) + 0.25 * (max(row) - min(row))
dark = [i for i, value in enumerate(row) if value < threshold]
if not dark:
    raise SystemExit("BŁĄD: na renderze drzwi nie widać otworu")
measured = (max(dark) - min(dark) + 1) * metres_per_pixel
spec = json.load(open("build/M7_shell.json", encoding="utf-8"))["spec_values"]["double_door_opening_width_m"]
print(f"[OK] kadr {frame_w:.4f} m, {metres_per_pixel * 1000:.4f} mm/px")
print(f"[OK] otwór na renderze: {max(dark) - min(dark) + 1} px = {measured:.4f} m (spec {spec} m)")
if abs(measured - spec) > 2 * metres_per_pixel:
    raise SystemExit(f"BŁĄD: zmierzony otwór {measured:.4f} m odbiega od {spec} m o więcej niż 2 px")
PY

echo
echo "[VERIFY] symetria sylwetki na renderze czoła"
python3 - <<'PY'
import json, os, sys
sys.path.insert(0, os.path.join("tools", "visual"))
import pngio

image = pngio.read_gray("renders/m7/M7_shell_front.png")
histogram = [0] * 256
for value in image.gray:
    histogram[min(255, int(value * 255))] += 1
background = histogram.index(max(histogram)) / 255.0
mask = [1 if abs(v - background) > 0.02 else 0 for v in image.gray]
rows = []
for y in range(image.height):
    row = mask[y * image.width:(y + 1) * image.width]
    if any(row):
        xs = [i for i, m in enumerate(row) if m]
        rows.append((min(xs), max(xs)))
meta = json.load(open("renders/m7/M7_shell_metadata.json", encoding="utf-8"))
camera = next(c for c in meta["cameras"] if c["id"] == "front")
metres_per_pixel = camera["frame_w_m"] / image.width
width_m = max(b - a + 1 for a, b in rows) * metres_per_pixel
height_m = len(rows) * metres_per_pixel
widest = max(b - a + 1 for a, b in rows)
# Jednopikselowe krawędzie antyaliasingu wpadają w próg maski tylko po stronie
# oświetlonej, więc liczymy symetrię na wierszach niosących realną sylwetkę.
solid = [(a, b) for a, b in rows if (b - a + 1) >= 0.5 * widest]
offset_px = max(abs((a + b) / 2 - (image.width - 1) / 2) for a, b in solid)
spec = json.load(open("build/M7_shell.json", encoding="utf-8"))["spec_values"]
print(f"[OK] sylwetka czoła: {width_m:.3f} x {height_m:.3f} m przy {metres_per_pixel * 1000:.3f} mm/px")
if abs(width_m - spec["width_m"]) > 3 * metres_per_pixel:
    raise SystemExit(f"BŁĄD: sylwetka czoła {width_m:.4f} m != spec {spec['width_m']} m")
if offset_px > 1.0:
    raise SystemExit(f"BŁĄD: sylwetka czoła niesymetryczna, odchylenie {offset_px:.1f} px")
print(f"[OK] odchylenie środka sylwetki od osi kadru: {offset_px:.1f} px "
      f"({len(solid)}/{len(rows)} wierszy, reszta to krawędzie antyaliasingu)")
PY

echo
echo "[TOPOLOGIA] dwa eksporty tej samej bryły muszą dać tę samą topologię"
# Eksporter glTF NIE jest powtarzalny: dla identycznego wejścia (2334 wierzchołki,
# 1862 ściany, wymiary zgodne co do 6 miejsc) plik waha się o 4 % rozmiaru, a liczba
# wierzchołków po re-imporcie o ok. 1 % — bo rozszczepienie na szwach UV i normalnych
# nie ma ustalonej kolejności. Liczba ŚCIAN natomiast nie waha się wcale, więc to ona
# jest niezmiennikiem nadającym się na kontrolę regresji topologii.
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/m7_shell.py -- \
  --out "$OUT/M7_repeat.glb" --envelope-out "$OUT/M7_repeat_env.glb" \
  --report "$OUT/M7_repeat.json" --skip-roundtrip >/dev/null
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/glb_roundtrip.py -- \
  --in build/M7_shell.glb --allow-missing-uv --out "$OUT/topology_a.json" >/dev/null
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/glb_roundtrip.py -- \
  --in "$OUT/M7_repeat.glb" --allow-missing-uv --out "$OUT/topology_b.json" >/dev/null
python3 - "$OUT/topology_a.json" "$OUT/topology_b.json" <<'TOPOPY'
import json, sys

VERTEX_TOLERANCE = 0.05
a = json.load(open(sys.argv[1], encoding="utf-8"))
b = json.load(open(sys.argv[2], encoding="utf-8"))
print(f"[TOPOLOGIA] przebieg A: obiekty={a['objects']} sciany={a['faces']} wierzcholki={a['vertices']} bajty={a['bytes']}")
print(f"[TOPOLOGIA] przebieg B: obiekty={b['objects']} sciany={b['faces']} wierzcholki={b['vertices']} bajty={b['bytes']}")
if a["objects"] != b["objects"]:
    raise SystemExit(f"BŁĄD: liczba obiektow {a['objects']} != {b['objects']}")
if a["faces"] != b["faces"]:
    raise SystemExit(f"BŁĄD: topologia niestabilna — scian {a['faces']} != {b['faces']}")
spread = abs(a["vertices"] - b["vertices"]) / max(1, a["vertices"])
print(f"[TOPOLOGIA] rozrzut wierzcholkow {spread*100:.2f} % (dopuszczalne {VERTEX_TOLERANCE*100:.0f} %), "
      f"bajtow {abs(a['bytes']-b['bytes'])/max(1,a['bytes'])*100:.2f} % — bajty nie sa kontrolowane")
if spread > VERTEX_TOLERANCE:
    raise SystemExit(f"BŁĄD: rozrzut wierzcholkow {spread*100:.2f} % przekracza {VERTEX_TOLERANCE*100:.0f} %")
for axis, x, y in zip("XYZ", a["bbox_size_m"], b["bbox_size_m"]):
    if abs(x - y) > 1e-6:
        raise SystemExit(f"BŁĄD: bbox {axis} rozjazd {abs(x-y)} m")
print("[TOPOLOGIA] OK — scian tyle samo, bbox identyczny, wierzcholki w tolerancji")
TOPOPY
rm -f "$OUT/M7_repeat.glb" "$OUT/M7_repeat_env.glb"

echo
echo "[GENERATE] kabina kanoniczna (6.D119)"
rm -f build/M7_cab.glb build/M7_cab.json
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/m7_cab_build.py -- \
  --out build/M7_cab.glb --report build/M7_cab.json \
  >"$OUT/cab.log" 2>&1 || { tail -n 40 "$OUT/cab.log"; fail "generator kabiny nie powiódł się"; }
grep -E '^\[KABINA\]' "$OUT/cab.log"
cp build/M7_cab.json "$OUT/M7_cab.json"

echo
echo "[VERIFY] kabina: bryły w skorupie, zdanie o układzie kanonicznym, GLB"
python3 - <<'CABPY'
import json
import os
import sys

sys.path.insert(0, os.path.join("tools", "blender"))
import m7_cab
import m7_layout

report = json.load(open("build/M7_cab.json", encoding="utf-8"))
problems = []

if not report.get("not_modelled"):
    problems.append("raport kabiny nie mówi, czego układ NIE odwzorowuje")
elif "design_assumption" not in " ".join(report["not_modelled"]):
    problems.append("raport kabiny nie nazywa swoich wymiarow zalozeniami")
else:
    print(f"[OK] raport niesie {len(report['not_modelled'])} zdan o tym, czego nie ma")

oczekiwane = 2 * 8
if len(report["solids"]) != oczekiwane:
    problems.append(f"bryl kabiny: {len(report['solids'])} != {oczekiwane}")
else:
    print(f"[OK] bryl kabiny: {len(report['solids'])} (dwie kabiny po osiem)")

# Zawieranie liczone TUTAJ, a nie przepisane z raportu: raport jest wyjsciem tego
# samego kodu, wiec jego wlasna deklaracja o zawieraniu nie bylaby dowodem.
layout = m7_layout.Layout()
poza = []
for solid in report["solids"]:
    for x in (solid["x_from_m"], solid["x_to_m"]):
        ys = [p[0] for p in layout.section(x)]
        zs = [p[1] for p in layout.section(x)]
        for y in (solid["y_from_m"], solid["y_to_m"]):
            for z in (solid["z_from_m"], solid["z_to_m"]):
                if not (min(ys) - 1e-6 <= y <= max(ys) + 1e-6):
                    poza.append((solid["name"], "y", y))
                if not (min(zs) - 1e-6 <= z <= max(zs) + 1e-6):
                    poza.append((solid["name"], "z", z))
if poza:
    problems.append(f"bryla kabiny poza obrysem przekroju: {poza[:3]}")
else:
    print("[OK] kazda bryla kabiny miesci sie w obrysie przekroju pudla")

size = os.path.getsize("build/M7_cab.glb")
with open("build/M7_cab.glb", "rb") as handle:
    magic = handle.read(4)
if magic != b"glTF":
    problems.append(f"build/M7_cab.glb ma zly magic {magic!r}")
elif size <= 1024:
    problems.append(f"build/M7_cab.glb jest podejrzanie maly: {size} B")
else:
    print(f"[OK] build/M7_cab.glb: {size} B, magic glTF")

if problems:
    for problem in problems:
        print(f"BŁĄD: {problem}", file=sys.stderr)
    raise SystemExit(1)
print("[OK] wszystkie kontrole kabiny przeszly")
CABPY

echo
echo "[NEGATIVE] generator kabiny bez ani jednej bryły musi odmówić"
if "$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/m7_cab_build.py -- \
    --end 9 --out build/t220/cab-should-not-exist.glb --report build/t220/cab-broken.json \
    >"$OUT/cab-negative.log" 2>&1; then
  fail "generator kabiny przyjął numer końca spoza zbioru"
fi
test ! -e build/t220/cab-should-not-exist.glb || fail "powstał GLB mimo odrzuconego argumentu"
tail -n 3 "$OUT/cab-negative.log"

echo
echo "[RENDER] cztery klatki kontrolne kabiny (CLAUDE.md §5)"
rm -f renders/M7_cab_front_*.png
"$BLENDER_EXE" --background --python-exit-code 7 --python tools/blender/m7_cab_build.py -- \
  --end 0 --out build/M7_cab_front.glb --report build/t220/M7_cab_front.json \
  >>"$OUT/cab.log" 2>&1 || { tail -n 20 "$OUT/cab.log"; fail "generator jednej kabiny nie powiódł się"; }
"$BLENDER_EXE" --background --python tools/blender/render_check.py -- \
  --in build/M7_cab_front.glb --out renders/M7_cab_front \
  >"$OUT/cab-render.log" 2>&1 || { tail -n 40 "$OUT/cab-render.log"; fail "render kabiny nie powiódł się"; }
grep -E '^\[(RENDER|NORMALNE)\]' "$OUT/cab-render.log"
for klatka in iso side normals inside; do
  test -s "renders/M7_cab_front_$klatka.png" || fail "brak klatki renders/M7_cab_front_$klatka.png"
done

echo
echo "[ARTEFAKTY] kopiowanie do artefaktu CI"
mkdir -p "$OUT/renders"
cp renders/m7/*.png renders/m7/*.json "$OUT/renders/" 2>/dev/null || true
cp renders/M7_cab_front_*.png "$OUT/renders/" 2>/dev/null || true

echo
echo "============================================================"
echo "[RESULT] T-220 zakończone w ${SECONDS}s"
echo "[RESULT] manual visual gate NADAL WYMAGANY dla:"
for f in "$OUT"/renders/M7_shell_*.png "$OUT"/renders/M7_cab_front_*.png; do echo "[RESULT]   $f"; done
echo "[RESULT] metryka automatyczna nie zastępuje obejrzenia PNG (CLAUDE.md §5)"

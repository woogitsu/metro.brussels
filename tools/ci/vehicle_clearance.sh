#!/usr/bin/env bash
# Osadzenie M7 w tunelu pakietu A i POMIAR luzu na siatce, plus rendery kontrolne.
# `reports/M7-curve-clearance.md` liczy ten sam luz ze wzoru na strzałkę cięciwy —
# dwie niezależne drogi do jednej liczby, żeby jedna sprawdzała drugą.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

OUT="build/t220clearance"
RENDERS="$OUT/renders"
mkdir -p "$OUT" "$RENDERS"
REPORT="$OUT/report.txt"
: > "$REPORT"
exec > >(tee -a "$REPORT") 2>&1
SECONDS=0

AXIS="data/track/L1_A.json"
PROFILE="box_double"
BLENDER=(blender --background --python-exit-code 7 --python)

fail() { echo "BŁĄD: $*" >&2; exit 1; }

echo "Skrajnia M7 w tunelu pakietu A — pomiar na siatce"
echo "============================================================"
blender --version | head -n 1
test -s "$AXIS" || fail "brak osi $AXIS"

echo
echo "[BUILD] tunel i pojazd"
"${BLENDER[@]}" tools/blender/tunnel_sweep.py -- \
  --centerline "$AXIS" --profile "$PROFILE" --name L1_A \
  --out "$OUT/L1_A.glb" --metrics "$OUT/L1_A-metrics.json" >/dev/null
"${BLENDER[@]}" tools/blender/m7_shell.py -- \
  --out "$OUT/M7_shell.glb" --envelope-out "$OUT/M7_envelope.glb" \
  --report "$OUT/M7_shell.json" >/dev/null
test -s "$OUT/L1_A.glb" || fail "tunel nie powstał"
test -s "$OUT/M7_shell.glb" || fail "pojazd nie powstał"

echo
echo "[POMIAR] oba tory na najciaśniejszym łuku"
for TRACK in 0 1; do
  "${BLENDER[@]}" tools/blender/place_vehicle.py -- \
    --tunnel "$OUT/L1_A.glb" --vehicle "$OUT/M7_shell.glb" --centerline "$AXIS" \
    --profile "$PROFILE" --track "$TRACK" \
    --out "$OUT/L1_A_with_M7_t$TRACK.glb" --report "$OUT/m7_t$TRACK.json" \
    --min-clearance-m 0.0 | grep -E '^\[OSADZENIE\]'
done

echo
echo "[NEGATYWNY] próg luzu musi wywrócić przebieg, gdy nie jest spełniony"
if "${BLENDER[@]}" tools/blender/place_vehicle.py -- \
  --tunnel "$OUT/L1_A.glb" --vehicle "$OUT/M7_shell.glb" --centerline "$AXIS" \
  --profile "$PROFILE" --track 1 --min-clearance-m 5.0 \
  --out "$OUT/negative.glb" >"$OUT/negative.log" 2>&1; then
  fail "próg 5 m luzu przeszedł, choć tunel ma 9,40 m szerokości"
fi
grep -q "poniżej progu" "$OUT/negative.log" || fail "brak czytelnej diagnostyki progu luzu"
tail -n 2 "$OUT/negative.log"

echo
echo "[KONTROLA] pomiar na siatce wobec wzoru na strzałkę cięciwy"
python3 - "$OUT/m7_t0.json" "$OUT/m7_t1.json" <<'CHECKPY'
import json, os, sys
sys.path.insert(0, os.path.join("tools", "blender"))
import clearance as CL, m7_layout, placement as PL, profiles

spec = m7_layout.load_spec()
chord = CL.car_chord_m(spec)
worst = None
for path in sys.argv[1:]:
    m = json.load(open(path, encoding="utf-8"))
    if m["min_clearance_m"] <= 0.0:
        raise SystemExit(f"BŁĄD: {path} raportuje luz {m['min_clearance_m']} m — pojazd w ścianie")
    worst = m if worst is None or m["min_clearance_m"] < worst["min_clearance_m"] else worst
    print(f"[KONTROLA] {os.path.basename(path)}: tor {m['track_index']} "
          f"({m['track_offset_m']:+.2f} m), luz {m['min_clearance_m']:+.4f} m "
          f"na {m['min_clearance_at']['object']}")

# Strzałka cięciwy pudła w promieniu ze sceny; ten sam wzór co w raporcie skrajni,
# ale na RZECZYWISTEJ cięciwie pudła, w którym wypadło minimum. Nominalny podział
# 94/6 daje cięciwę 15,667 m zamiast 14,567 m i przewiduje luz mniejszy o 52 mm —
# zachowawczo, ale wtedy kontrola mierzyłaby własną niespójność, nie zgodność metod.
radius = worst["radius_at_centre_m"]
body_chord = worst.get("min_clearance_chord_m") or chord
versine = CL.versine(body_chord, radius)
ring = profiles.profile_points(worst["profile"])
# Luz statyczny do ŚCIANY na danym torze — inna wielkość niż profiles.min_clearance,
# które inflatuje skrajnię symetrycznie i bywa wiązane przez ścięcie naroża stropu.
static_wall = min(PL.distance_to_boundary(ring, worst["track_offset_m"] + dx, 1.0)
                  for dx in (-spec["width_m"] / 2.0, spec["width_m"] / 2.0))
predicted = static_wall - versine
print(f"[KONTROLA] promień {radius} m, cięciwa nominalna {chord:.3f} m, "
      f"rzeczywista {body_chord:.3f} m -> strzałka {versine*1000:.1f} mm")
print(f"[KONTROLA] luz statyczny do ściany {static_wall:.4f} m, przewidziany {predicted:.4f} m, "
      f"zmierzony {worst['min_clearance_m']:.4f} m")
delta = abs(predicted - worst["min_clearance_m"])
print(f"[KONTROLA] rozjazd wzoru i siatki: {delta*1000:.1f} mm")
if delta > 0.01:
    raise SystemExit(f"BŁĄD: wzór i pomiar na siatce rozjeżdżają się o {delta*1000:.1f} mm — "
                     "jedna z tych dwóch dróg jest błędna")
CHECKPY

echo
echo "[RENDER] zestaw clearance w najgorszym punkcie"
ANCHORS="$(python3 - "$OUT/m7_t1.json" <<'ANCHORPY'
import json, os, sys
sys.path.insert(0, os.path.join("tools", "blender"))
import placement as PL, sweep as SW

report = json.load(open(sys.argv[1], encoding="utf-8"))
document = json.load(open(os.path.join("data", "track", "L1_A.json"), encoding="utf-8"))
points = SW.catmull_rom([tuple(float(c) for c in p) for p in document["points"]],
                        report["ring_step_m"])
stations = SW.chainages(points)
gap = report["min_clearance_at"]["chainage_m"]
nose = report["start_chainage_m"]


def at(chainage, z=1.75):
    position, _index, _t = PL.frame_at(points, stations, chainage)
    return f"{position[0]:.3f},{position[1]:.3f},{z:.3f}"


print(f"--anchor gap_eye={at(gap)} --anchor gap_target={at(gap + 10.0)} "
      f"--anchor approach_eye={at(nose - 32.0)} --anchor approach_target={at(nose - 2.0)}")
ANCHORPY
)"
"${BLENDER[@]}" tools/visual/capture_blender.py -- \
  --in "$OUT/L1_A_with_M7_t1.glb" --set clearance --prefix M7_GAP --out "$RENDERS" \
  --centerline "$AXIS" $ANCHORS

echo
echo "[KONTROLA] renderów nie wolno uznać za puste ani jednolite"
python3 tools/visual/compare.py --set clearance --current "$RENDERS" --prefix M7_GAP \
  --out "$OUT/render-sanity.json" --markdown "$OUT/render-sanity.md" --allow-new-baseline

python3 - "$OUT/render-sanity.json" <<'SANITYPY'
import json, sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
manifest = json.load(open("tools/visual/cameras.json", encoding="utf-8"))
expected = {c["id"] for c in manifest["scene_sets"]["clearance"]["cameras"]}
bad = []
for image in report["images"]:
    checks, metrics = image["checks"], image["metrics"]
    ok = checks.get("exists") and checks.get("dimension") and checks.get("not_empty")
    print(f"[RENDER] {image['camera']}: ink={metrics['ink_fraction']} std={metrics['luma_std']} "
          f"poziomy={metrics['distinct_levels']} -> {'OK' if ok else 'ODRZUCONY'}")
    if not ok:
        bad.append(image["camera"])
missing = expected - {i["camera"] for i in report["images"]}
if missing:
    raise SystemExit(f"BŁĄD: brak renderów: {sorted(missing)}")
if bad:
    raise SystemExit("BŁĄD: puste lub jednolite rendery: " + ", ".join(bad))
SANITYPY

echo
echo "[VERIFY] zestaw testów Pythona"
python3 tools/tests/test_all.py

echo
echo "============================================================"
echo "[RESULT] pomiar skrajni zakończony w ${SECONDS}s"
echo "[RESULT] OGLĘDZINY RENDERÓW SĄ NADAL WYMAGANE:"
for f in "$RENDERS"/M7_GAP_*.png; do
  echo "  - $f ($(stat -c%s "$f") B)"
done

#!/usr/bin/env bash
# T-210: tunel pakietu A z rzeczywistej osi — generacja, kontrola geometrii,
# round-trip GLB i render kontrolny na GitHub-hosted Linux (ubuntu-latest).
# Wszystkie artefakty lądują w build/t210 i są wgrywane także przy porażce.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

OUT="build/t210"
RENDERS="$OUT/renders"
mkdir -p "$OUT" "$RENDERS"
REPORT="$OUT/report.txt"
: > "$REPORT"
exec > >(tee -a "$REPORT") 2>&1
SECONDS=0

AXIS="data/track/L1_A.json"
BLENDER=(blender --background --python-exit-code 7 --python)

fail() {
  echo "BŁĄD: $*" >&2
  exit 1
}

echo "T-210 tunel pakietu A — pipeline geometryczny"
echo "============================================================"
blender --version | head -n 1
python3 --version
test -s "$AXIS" || fail "brak osi $AXIS"

echo
echo "[GENERATE] wariant renderowy (zagęszczenie 5 m)"
"${BLENDER[@]}" tools/blender/tunnel_sweep.py -- \
  --centerline "$AXIS" --profile box_double --name L1_A \
  --out "$OUT/L1_A.glb" --metrics "$OUT/L1_A-metrics.json"

echo
echo "[GENERATE] wariant wierny łamanej źródłowej (--ring-step 0)"
"${BLENDER[@]}" tools/blender/tunnel_sweep.py -- \
  --centerline "$AXIS" --profile box_double --name L1_A --ring-step 0 \
  --out "$OUT/L1_A-faithful.glb" --metrics "$OUT/L1_A-faithful-metrics.json"

echo
echo "[NEGATIVE] wariant production musi zostać odrzucony bez profilu pionowego"
if "${BLENDER[@]}" tools/blender/tunnel_sweep.py -- \
  --centerline "$AXIS" --profile box_double --variant production \
  --out "$OUT/negative-production.glb" >"$OUT/negative-production.log" 2>&1; then
  fail "wariant production przeszedł mimo braku profilu pionowego (T-112)"
fi
test ! -e "$OUT/negative-production.glb" || fail "odrzucony wariant zostawił plik GLB"
grep -q "wariant production niedozwolony" "$OUT/negative-production.log" \
  || fail "brak czytelnej diagnostyki dla wariantu production"
tail -n 3 "$OUT/negative-production.log"

echo
echo "[CHECK] metryki generatora"
python3 - "$OUT/L1_A-metrics.json" "$OUT/L1_A-faithful-metrics.json" <<'PY'
import json, sys

MAX_GAP_M = 0.001
for path in sys.argv[1:]:
    m = json.load(open(path, encoding="utf-8"))
    problems = []
    if m["variant"] != "flat-preview" or m["production_ready"]:
        problems.append("wariant musi być flat-preview dopóki T-112 jest zablokowane")
    if m["chunk_max_gap_m"] > MAX_GAP_M:
        problems.append(f"szczelina {m['chunk_max_gap_m']*1000:.3f} mm")
    if m["stations_split"]:
        problems.append(f"szew na stacji: {m['stations_split']}")
    for key in ("outward_faces", "degenerate_faces", "non_finite_vertices"):
        if m[key]:
            problems.append(f"{key}={m[key]}")
    if abs(m["chunk_length_sum_m"] - m["axis_length_m"]) > 0.01:
        problems.append("suma chunków != chainage")
    if m["frame_twist_deg"] > 5.0:
        problems.append(f"skręt ramki {m['frame_twist_deg']}")
    low, high = m["uv_metres_per_unit"]
    if not 0.8 * 4.0 < low <= high < 1.2 * 4.0:
        problems.append(f"gęstość UV {low}..{high} m/jednostkę")
    span = max(m["bbox_size_m"][0], m["bbox_size_m"][1])
    if not m["profile_size_m"][0] < span <= m["axis_length_m"]:
        problems.append(f"bbox {span} m nie pasuje do osi {m['axis_length_m']} m")
    if abs(m["bbox_size_m"][2] - m["profile_size_m"][1]) > 1e-6:
        problems.append("wysokość bboxa != wysokość profilu")
    print(f"[METRYKI] {path}: chunki={m['chunks']} szczelina={m['chunk_max_gap_m']*1000:.3f} mm "
          f"os={m['axis_length_m']} m wygladzenie={m['smoothing_max_deviation_m']} m "
          f"trojkaty={m['triangles']}")
    if problems:
        raise SystemExit("BŁĄD: " + "; ".join(problems))
print("[METRYKI] OK")
PY

echo
echo "[DETERMINISM] drugi przebieg musi dać te same metryki"
"${BLENDER[@]}" tools/blender/tunnel_sweep.py -- \
  --centerline "$AXIS" --profile box_double --name L1_A \
  --out "$OUT/L1_A-repeat.glb" --metrics "$OUT/L1_A-repeat-metrics.json" >/dev/null
# Bajty GLB nie są odtwarzalne (eksporter glTF nie gwarantuje kolejności bufora),
# ale metryki geometryczne muszą się zgadzać co do znaku.
python3 - "$OUT/L1_A-metrics.json" "$OUT/L1_A-repeat-metrics.json" <<'DETPY'
import json, sys
a = json.load(open(sys.argv[1], encoding="utf-8"))
b = json.load(open(sys.argv[2], encoding="utf-8"))
for key in sorted(set(a) | set(b)):
    if key == "glb_bytes":
        continue
    if a.get(key) != b.get(key):
        raise SystemExit(f"BŁĄD: niedeterminizm w {key}: {a.get(key)} != {b.get(key)}")
print("[DETERMINISM] metryki identyczne w obu przebiegach")
DETPY
rm -f "$OUT/L1_A-repeat.glb"

echo
echo "[ROUNDTRIP] ponowny import wyeksportowanych GLB"
CHUNKS="$(python3 -c "import json;print(json.load(open('$OUT/L1_A-metrics.json'))['chunks'])")"
"${BLENDER[@]}" tools/blender/glb_roundtrip.py -- \
  --in "$OUT/L1_A.glb" --expect-objects "$CHUNKS" \
  --expect-metrics "$OUT/L1_A-metrics.json" --out "$OUT/roundtrip.json"
"${BLENDER[@]}" tools/blender/glb_roundtrip.py -- \
  --in "$OUT/L1_A-faithful.glb" --expect-metrics "$OUT/L1_A-faithful-metrics.json" \
  --out "$OUT/roundtrip-faithful.json"

echo
echo "[RENDER] zestaw alignment"
"${BLENDER[@]}" tools/visual/capture_blender.py -- \
  --in "$OUT/L1_A.glb" --set alignment --prefix L1_A --out "$RENDERS" \
  --centerline "$AXIS" --wire-cameras axis05,axis25,axis50,axis75,section

echo
echo "[CHECK] renderów nie wolno uznać za puste ani jednolite"
python3 tools/visual/compare.py --set alignment --current "$RENDERS" --prefix L1_A \
  --out "$OUT/render-sanity.json" --markdown "$OUT/render-sanity.md" --allow-new-baseline

python3 - "$OUT/render-sanity.json" <<'PY'
import json, sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
bad = []
for image in report["images"]:
    checks, metrics = image["checks"], image["metrics"]
    ok = checks.get("exists") and checks.get("dimension") and checks.get("not_empty")
    print(f"[RENDER] {image['camera']}: {metrics['width']}x{metrics['height']} "
          f"ink={metrics['ink_fraction']} std={metrics['luma_std']} "
          f"poziomy={metrics['distinct_levels']} -> {'OK' if ok else 'ODRZUCONY'}")
    if not ok:
        bad.append(image["camera"])
expected = {"plan", "section", "axis05", "axis25", "axis50", "axis75"}
missing = expected - {i["camera"] for i in report["images"]}
if missing:
    raise SystemExit(f"BŁĄD: brak renderów: {sorted(missing)}")
if bad:
    raise SystemExit("BŁĄD: puste/jednolite lub uszkodzone rendery: " + ", ".join(bad))
PY

echo
echo "[VERIFY] zestaw testów Pythona"
python3 tools/tests/test_all.py

echo
echo "============================================================"
echo "[RESULT] T-210 zakończone w ${SECONDS}s"
echo "[RESULT] OGLĘDZINY RENDERÓW SĄ NADAL WYMAGANE:"
for f in "$RENDERS"/L1_A_*.png; do
  echo "  - $f ($(stat -c%s "$f") B)"
done

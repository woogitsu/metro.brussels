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
echo "[CHUNKI] eksport per chunk i manifest streamingowy"
# Chunki jako osobne obiekty w jednym GLB nie dają streamowania — Godot i tak wczytuje
# całe 6,7 km. Ten blok sprawdza to, na czym opiera się streaming: pokrycie osi bez
# dziur, integralność każdego pliku i sensowność predykatu okna.
CHUNKS_A="$OUT/chunks"
CHUNKS_B="$OUT/chunks-repeat"
MANIFEST_A="$CHUNKS_A/L1_A-chunks.json"
MANIFEST_B="$CHUNKS_B/L1_A-chunks.json"
rm -rf "$CHUNKS_A" "$CHUNKS_B"
"${BLENDER[@]}" tools/blender/tunnel_sweep.py -- \
  --centerline "$AXIS" --profile box_double --name L1_A \
  --out "$OUT/L1_A-chunked.glb" --metrics "$OUT/L1_A-chunked-metrics.json" \
  --chunk-dir "$CHUNKS_A" --chunk-manifest "$MANIFEST_A" | grep -E '^\[CHUNKI\]'

echo
echo "[CHUNKI] spójność manifestu, pliki, sumy kontrolne i predykat okna"
python3 - "$MANIFEST_A" "$CHUNKS_A" "$OUT/L1_A-chunked-metrics.json" "$AXIS" <<'CHUNKPY'
import hashlib, json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.join("tools", "blender"))
import sweep as SW

manifest_path, chunk_dir, metrics_path, axis_path = sys.argv[1:5]
manifest = json.load(open(manifest_path, encoding="utf-8"))
metrics = json.load(open(metrics_path, encoding="utf-8"))
axis = json.load(open(axis_path, encoding="utf-8"))
problems = []


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def check_files(manifest, directory):
    """Istnienie, magic GLB i sha256 każdego pliku chunka."""
    bad = []
    for chunk in manifest["chunks"]:
        path = os.path.join(directory, chunk["file"])
        if not os.path.isfile(path):
            bad.append(f"{chunk['id']}: brak pliku {path}")
            continue
        with open(path, "rb") as handle:
            magic = handle.read(4)
        if magic != b"glTF":
            bad.append(f"{chunk['id']}: zły magic {magic!r}")
        if os.path.getsize(path) != chunk["bytes"]:
            bad.append(f"{chunk['id']}: rozmiar {os.path.getsize(path)} != {chunk['bytes']}")
        if sha256(path) != chunk["sha256"]:
            bad.append(f"{chunk['id']}: sha256 nie zgadza się z manifestem")
    return bad


problems += SW.manifest_problems(manifest)
problems += check_files(manifest, chunk_dir)

if manifest["variant"] != "flat-preview" or manifest["production_ready"]:
    problems.append("manifest musi być flat-preview dopóki T-112 jest zablokowane")
if manifest["chunk_count"] != metrics["chunks"]:
    problems.append("liczba chunków w manifeście != metryki generatora")
for key in ("vertices", "faces", "triangles"):
    if manifest["totals"][key] != metrics[key]:
        problems.append(f"totals.{key} != metryki generatora")
if abs(manifest["axis_length_m"] - metrics["axis_length_m"]) > 1e-9:
    problems.append("axis_length_m w manifeście != metryki generatora")
if metrics["stations_split"]:
    problems.append(f"szew chunka przecina stację: {metrics['stations_split']}")

# Każda stacja z osi ma się znaleźć w dokładnie jednym chunku i wewnątrz jego zakresu.
declared = [s["name"] for s in axis["stations"]]
placed = [(s["name"], s["chainage_m"], c) for c in manifest["chunks"] for s in c["stations"]]
if sorted(n for n, _c, _k in placed) != sorted(declared):
    problems.append("stacje w manifeście nie pokrywają się ze stacjami osi")
axis_end = manifest["chunks"][-1]["end_m"]
for name, chainage, chunk in placed:
    # Chainage stacji pochodzi z łamanej źródłowej, koniec osi z zagęszczonej — Merode
    # wypada o 0,25 m za końcem, więc porównanie idzie po przyciętej wartości.
    value = min(max(chainage, 0.0), axis_end)
    if not chunk["start_m"] - 1e-6 <= value <= chunk["end_m"] + 1e-6:
        problems.append(f"stacja {name} poza zakresem chunka {chunk['id']}")

# Predykat okna: przejazd całej osi co 25 m. Chunk pod pociągiem nigdy nie może
# wypaść z planu, a okno musi być pokryte bez dziur.
loaded, peak, total_loads = [], 0, 0
step, chainage = 25.0, 0.0
while chainage <= manifest["axis_length_m"] + step:
    plan = SW.streaming_plan(manifest, chainage, loaded)
    loaded = plan["keep"] + plan["load"]
    total_loads += len(plan["load"])
    peak = max(peak, len(loaded))
    under = [c["id"] for c in manifest["chunks"] if c["start_m"] <= chainage <= c["end_m"]]
    if not set(under) <= set(loaded):
        problems.append(f"chainage {chainage}: chunk pod pociągiem nie jest wczytany")
    picked = SW.chunks_for_train(manifest, chainage)
    for previous, current in zip(picked, picked[1:]):
        if abs(current["start_m"] - previous["end_m"]) > 1e-6:
            problems.append(f"chainage {chainage}: dziura w oknie streamowania")
    chainage += step
if peak >= manifest["chunk_count"]:
    problems.append(f"okno {SW.DEFAULT_STREAM_BEHIND_M}+{SW.DEFAULT_STREAM_AHEAD_M} m "
                    f"trzyma {peak} z {manifest['chunk_count']} chunków — to nie jest streaming")

# NEGATYW: uszkodzony bajt w pliku chunka musi zostać wykryty. Kontrola, która
# przechodzi tylko na poprawnym wejściu, nie dowodzi niczego (docs/06-worked-example).
scratch = tempfile.mkdtemp()
try:
    for chunk in manifest["chunks"]:
        shutil.copy2(os.path.join(chunk_dir, chunk["file"]), scratch)
    victim = os.path.join(scratch, manifest["chunks"][0]["file"])
    with open(victim, "r+b") as handle:
        handle.seek(os.path.getsize(victim) - 1)
        last = handle.read(1)
        handle.seek(os.path.getsize(victim) - 1)
        handle.write(bytes([last[0] ^ 0xFF]))
    detected = check_files(manifest, scratch)
    if not any("sha256" in d for d in detected):
        problems.append("NEGATYW: przekręcony bajt w chunku nie został wykryty")
    else:
        print(f"[CHUNKI] negatyw OK — {detected[0]}")
finally:
    shutil.rmtree(scratch, ignore_errors=True)

size = sum(c["bytes"] for c in manifest["chunks"])
print(f"[CHUNKI] chunki={manifest['chunk_count']} suma={manifest['chunk_length_sum_m']} m "
      f"os={manifest['axis_length_m']} m stacje={manifest['station_count']} "
      f"pliki={size} B")
print(f"[CHUNKI] okno {SW.DEFAULT_STREAM_BEHIND_M}+{SW.DEFAULT_STREAM_AHEAD_M} m: "
      f"maks. {peak} chunków naraz, {total_loads} wczytań na całym przejeździe "
      f"(bez streamowania: {manifest['chunk_count']} naraz)")
if problems:
    raise SystemExit("BŁĄD: " + "; ".join(problems))
print("[CHUNKI] manifest OK")
CHUNKPY

echo
echo "[CHUNKI] round-trip każdego chunka w Blenderze"
python3 - "$MANIFEST_A" "$CHUNKS_A" <<'EXPECTPY'
import json, os, sys
manifest = json.load(open(sys.argv[1], encoding="utf-8"))
for chunk in manifest["chunks"]:
    path = os.path.join(sys.argv[2], f"expect-{chunk['id']}.json")
    json.dump({"bbox_size_m": chunk["bbox_size_m"], "vertices": chunk["vertices"],
               "faces": chunk["faces"]}, open(path, "w", encoding="utf-8"))
print(f"[CHUNKI] oczekiwania dla {len(manifest['chunks'])} chunków zapisane")
EXPECTPY
for expect in "$CHUNKS_A"/expect-*.json; do
  chunk_id="$(basename "$expect" .json)"; chunk_id="${chunk_id#expect-}"
  "${BLENDER[@]}" tools/blender/glb_roundtrip.py -- \
    --in "$CHUNKS_A/$chunk_id.glb" --expect-objects 1 --expect-metrics "$expect" \
    --out "$CHUNKS_A/roundtrip-$chunk_id.json" | sed "s/^/  $chunk_id /"
done

echo
echo "[CHUNKI] determinizm: drugi przebieg, identyczny manifest poza sha256 plików"
"${BLENDER[@]}" tools/blender/tunnel_sweep.py -- \
  --centerline "$AXIS" --profile box_double --name L1_A \
  --out "$OUT/L1_A-chunked-repeat.glb" --chunk-dir "$CHUNKS_B" \
  --chunk-manifest "$MANIFEST_B" >/dev/null
python3 - "$MANIFEST_A" "$MANIFEST_B" <<'DETPY'
import json, os, sys
sys.path.insert(0, os.path.join("tools", "blender"))
import sweep as SW
a = json.load(open(sys.argv[1], encoding="utf-8"))
b = json.load(open(sys.argv[2], encoding="utf-8"))
# Bajty GLB NIE są odtwarzalne — eksporter glTF nie gwarantuje kolejności bufora
# (ustalone w PR #44). Odtwarzalna jest geometria, i to sprawdza geometry_sha256.
view_a, view_b = SW.deterministic_view(a), SW.deterministic_view(b)
if view_a != view_b:
    for key in sorted(set(view_a) | set(view_b)):
        if view_a.get(key) != view_b.get(key):
            print(f"[CHUNKI] rozjazd w {key}")
    raise SystemExit("BŁĄD: manifest nie jest deterministyczny poza sha256 plików")
same_geometry = sum(1 for x, y in zip(a["chunks"], b["chunks"])
                    if x["geometry_sha256"] == y["geometry_sha256"])
same_bytes = sum(1 for x, y in zip(a["chunks"], b["chunks"]) if x["sha256"] == y["sha256"])
if same_geometry != len(a["chunks"]):
    raise SystemExit(f"BŁĄD: geometria nieodtwarzalna w {len(a['chunks']) - same_geometry} chunkach")
print(f"[CHUNKI] geometria identyczna w {same_geometry}/{len(a['chunks'])} chunkach; "
      f"bajty GLB identyczne w {same_bytes}/{len(a['chunks'])} (nie jest to wymagane)")
DETPY
rm -rf "$CHUNKS_B" "$OUT/L1_A-chunked-repeat.glb"

echo
echo "[CHUNKI] render pojedynczego chunka — czy fragment rury jest zamknięty i ciągły"
# Kotwice kamer liczą się z UŁAMKÓW osi podanej w --centerline. Podanie tu pełnej osi
# postawiłoby kamerę wnętrza kilka kilometrów od chunka, więc render dostaje wycinek
# osi odpowiadający zakresowi chainage tego chunka.
CHUNK_ID="$(python3 -c "import json;print(json.load(open('$MANIFEST_A'))['chunks'][5]['id'])")"
ANCHORS_FILE="$CHUNKS_A/$CHUNK_ID-anchors.txt"
python3 - "$MANIFEST_A" "$AXIS" "$CHUNKS_A/$CHUNK_ID-axis.json" "$CHUNK_ID" \
         "$ANCHORS_FILE" box_double <<'AXISPY'
import json, os, sys
sys.path.insert(0, os.path.join("tools", "blender"))
import profiles as PR
import sweep as SW

manifest_path, axis_path, axis_out, chunk_id, anchors_out, profile = sys.argv[1:7]
manifest = json.load(open(manifest_path, encoding="utf-8"))
axis = json.load(open(axis_path, encoding="utf-8"))
chunk = next(c for c in manifest["chunks"] if c["id"] == chunk_id)
dense = SW.catmull_rom([tuple(p) for p in axis["points"]], SW.DEFAULT_RING_STEP_M)
station = SW.chainages(dense)
inside = [p for p, s in zip(dense, station)
          if chunk["start_m"] - 1e-6 <= s <= chunk["end_m"] + 1e-6]
if len(inside) < 2:
    raise SystemExit("BŁĄD: wycinek osi chunka ma mniej niż 2 punkty")
json.dump({"id": chunk["id"], "points": [list(p) for p in inside]},
          open(axis_out, "w", encoding="utf-8"))

# Kotwice kamer liczymy sami zamiast zdawać się na `local_vertical_mid`: ono wybiera
# przekrój po stałym X, a na chunku biegnącym prawie równolegle do X taki plaster
# łapie samą płytę stropu i stawia kamerę w ścianie. Tutaj wysokość oka bierze się
# wprost ze środka profilu, a kierunek patrzenia z osi chunka.
_, y_low, _, y_high = PR.bbox(profile)
eye_z = 0.5 * (y_low + y_high)
local = SW.chainages(inside)
length = local[-1]


def at(distance):
    distance = min(max(distance, 0.0), length)
    for (a, b), (sa, sb) in zip(zip(inside, inside[1:]), zip(local, local[1:])):
        if sa <= distance <= sb and sb > sa:
            t = (distance - sa) / (sb - sa)
            return SW.add(a, SW.scale(SW.sub(b, a), t))
    return inside[-1]


AHEAD_M = 25.0
lines = []
for tag, fraction in (("axis05", 0.05), ("axis25", 0.25), ("axis50", 0.5),
                      ("axis75", 0.75), ("inside", 0.05), ("section", 0.5)):
    eye = at(length * fraction)
    target = at(length * fraction + AHEAD_M)
    lines.append(f"{tag}_eye={eye[0]:.4f},{eye[1]:.4f},{eye_z:.4f}")
    lines.append(f"{tag}_target={target[0]:.4f},{target[1]:.4f},{eye_z:.4f}")
open(anchors_out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(f"[CHUNKI] os chunka {chunk['id']}: {len(inside)} punktow, "
      f"{chunk['start_m']:.1f}..{chunk['end_m']:.1f} m, oko na z={eye_z:.2f} m")
AXISPY
ANCHOR_ARGS=()
while read -r line; do ANCHOR_ARGS+=(--anchor "$line"); done < "$ANCHORS_FILE"
"${BLENDER[@]}" tools/visual/capture_blender.py -- \
  --in "$CHUNKS_A/$CHUNK_ID.glb" --set alignment --prefix CHUNK \
  --out "$RENDERS/chunk" --centerline "$CHUNKS_A/$CHUNK_ID-axis.json" \
  --wire-cameras axis05,axis25,axis50,axis75,section "${ANCHOR_ARGS[@]}" \
  | grep -E '^\[(RENDER|SKIP)\]'
python3 tools/visual/compare.py --set alignment --current "$RENDERS/chunk" \
  --prefix CHUNK --out "$OUT/chunk-render-sanity.json" --allow-new-baseline
python3 - "$OUT/chunk-render-sanity.json" <<'PY'
import json, sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
bad = []
for image in report["images"]:
    checks, metrics = image["checks"], image["metrics"]
    ok = checks.get("exists") and checks.get("dimension") and checks.get("not_empty")
    print(f"[CHUNKI] render {image['camera']}: ink={metrics['ink_fraction']} "
          f"std={metrics['luma_std']} poziomy={metrics['distinct_levels']} "
          f"-> {'OK' if ok else 'ODRZUCONY'}")
    if not ok:
        bad.append(image["camera"])
expected = {"plan", "section", "axis05", "axis25", "axis50", "axis75"}
missing = expected - {i["camera"] for i in report["images"]}
if missing:
    raise SystemExit(f"BŁĄD: brak renderów chunka: {sorted(missing)}")
if bad:
    raise SystemExit("BŁĄD: puste/jednolite rendery chunka: " + ", ".join(bad))
PY

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
# Lista kamer bierze się z manifestu, nie z literału: dopisanie kamery do zestawu
# ma automatycznie rozszerzać kontrolę, a nie po cichu zostawiać ją niesprawdzoną.
manifest = json.load(open("tools/visual/cameras.json", encoding="utf-8"))
expected = {c["id"] for c in manifest["scene_sets"]["alignment"]["cameras"]}
missing = expected - {i["camera"] for i in report["images"]}
if missing:
    raise SystemExit(f"BŁĄD: brak renderów: {sorted(missing)}")
if bad:
    raise SystemExit("BŁĄD: puste/jednolite lub uszkodzone rendery: " + ", ".join(bad))
PY

echo
echo "[SKRAJNIA] M7 na rzeczywistych łukach pakietu A"
python3 tools/blender/clearance.py --alignment "$AXIS" --profile box_double \
  --out "$OUT/clearance-box_double.json"
# `bore_single` nie jest używany na pakiecie A, ale ma udokumentowany brak zapasu
# na łukach tej ostrości — raportujemy, nie wywracamy na tym pipeline'u tunelu.
python3 tools/blender/clearance.py --alignment "$AXIS" --profile bore_single \
  --out "$OUT/clearance-bore_single.json" --report-only

echo
echo "[SZEROKOŚĆ] szerokość tunelu w planie wg oficjalnych poligonów UrbIS"
# Informacyjnie: narzędzie zapisuje niedostępność źródła jako wynik i kończy zerem,
# więc niedostępny data.mobility.brussels nie wywraca pipeline'u geometrii.
python3 tools/track/tunnel_width.py --alignment "$AXIS" --out "$OUT/L1_A-tunnel-width.json"

echo
echo "[VERIFY] zestaw testów Pythona"
python3 tools/tests/test_all.py

echo
echo "============================================================"
echo "[RESULT] T-210 zakończone w ${SECONDS}s"
echo "[RESULT] OGLĘDZINY RENDERÓW SĄ NADAL WYMAGANE:"
for f in "$RENDERS"/L1_A_*.png "$RENDERS"/chunk/CHUNK_*.png; do
  echo "  - $f ($(stat -c%s "$f") B)"
done
echo "[RESULT] manifest streamingowy: $MANIFEST_A ($(python3 -c "import json;print(json.load(open('$MANIFEST_A'))['chunk_count'])") chunków)"

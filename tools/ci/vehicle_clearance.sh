#!/usr/bin/env bash
# Osadzenie M7 w tunelu pakietu i POMIAR luzu na siatce, plus rendery kontrolne.
# `reports/M7-curve-clearance.md` liczy ten sam luz ze wzoru na strzałkę cięciwy —
# dwie niezależne drogi do jednej liczby, żeby jedna sprawdzała drugą.
#
# Druga połowa skryptu przesuwa skład wzdłuż CAŁEJ osi (`profile_vehicle.py`) i pyta
# o to, czego pomiar w jednym punkcie nie powie: czy zmierzony dołek jest odosobniony
# i gdzie jeszcze robi się ciasno. Wynik: `reports/M7-clearance-profile.md`.
#
#     bash tools/ci/vehicle_clearance.sh [ID_OSI]
#
# ID_OSI to nazwa pliku z `data/track/` bez rozszerzenia (domyślnie L1_A). Pakiet A
# nie jest tu w niczym wyróżniony — tak samo jak w `tunnel_alignment.sh`, parametr
# istnieje po to, żeby ta sama poprzeczka dała się postawić każdemu pakietowi.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

NAME="${1:-L1_A}"
# AXIS jest eksportowana, bo czytają ją także wtrącone bloki `python3 - <<'PY'`,
# do których nie da się podać ścieżki inaczej niż przez środowisko albo argv.
export AXIS="data/track/$NAME.json"
OUT="build/t220clearance/$NAME"
RENDERS="$OUT/renders"
mkdir -p "$OUT" "$RENDERS"
REPORT="$OUT/report.txt"
: > "$REPORT"
exec > >(tee -a "$REPORT") 2>&1
SECONDS=0

PROFILE="box_double"
BLENDER=(blender --background --python-exit-code 7 --python)

fail() { echo "BŁĄD: $*" >&2; exit 1; }

echo "Skrajnia M7 w tunelu pakietu $NAME — pomiar na siatce i profil wzdłuż osi"
echo "============================================================"
blender --version | head -n 1
test -s "$AXIS" || fail "brak osi $AXIS"

echo
echo "[BUILD] tunel i pojazd"
"${BLENDER[@]}" tools/blender/tunnel_sweep.py -- \
  --centerline "$AXIS" --profile "$PROFILE" --name "$NAME" \
  --out "$OUT/$NAME.glb" --metrics "$OUT/$NAME-metrics.json" >/dev/null
"${BLENDER[@]}" tools/blender/m7_shell.py -- \
  --out "$OUT/M7_shell.glb" --envelope-out "$OUT/M7_envelope.glb" \
  --report "$OUT/M7_shell.json" >/dev/null
test -s "$OUT/$NAME.glb" || fail "tunel nie powstał"
test -s "$OUT/M7_shell.glb" || fail "pojazd nie powstał"

echo
echo "[POMIAR] oba tory na najciaśniejszym łuku"
for TRACK in 0 1; do
  "${BLENDER[@]}" tools/blender/place_vehicle.py -- \
    --tunnel "$OUT/$NAME.glb" --vehicle "$OUT/M7_shell.glb" --centerline "$AXIS" \
    --profile "$PROFILE" --track "$TRACK" \
    --out "$OUT/${NAME}_with_M7_t$TRACK.glb" --report "$OUT/m7_t$TRACK.json" \
    --min-clearance-m 0.0 | grep -E '^\[OSADZENIE\]'
done

echo
echo "[NEGATYWNY] próg luzu musi wywrócić przebieg, gdy nie jest spełniony"
if "${BLENDER[@]}" tools/blender/place_vehicle.py -- \
  --tunnel "$OUT/$NAME.glb" --vehicle "$OUT/M7_shell.glb" --centerline "$AXIS" \
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

# Zmierzony rozrzut wzoru wobec siatki to 1,2-13,3 mm na trzech pakietach; próg jest
# ustawiony z zapasem nad tym, a wciąż daleko pod 148,8 mm, którym objawiał się błąd
# wpisanej na stałe wysokości styku.
FORMULA_MAX_SLACK_M = 0.05

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
#
# WYSOKOŚĆ, na której mierzymy odległość do ściany, musi być tą, na której wypadło
# minimum — nie stałą. Profil `box_double` ma ścięte naroża stropu, więc światło
# zwęża się z wysokością: na 1,03 m jest 1,250 m, a na 3,60 m już 1,100 m. Wpisana
# na stałe wysokość 1,0 m zgadzała się z pakietem A PRZYPADKIEM (jego minimum leży
# na 1,03 m) i rozjeżdżała się o 148,8 mm na pakiecie B, gdzie minimum wypada na
# ścięciu naroża, na 3,60 m.
contact_height = float(worst["min_clearance_at"]["vertical_m"])
static_wall = min(PL.distance_to_boundary(ring, worst["track_offset_m"] + dx, contact_height)
                  for dx in (-spec["width_m"] / 2.0, spec["width_m"] / 2.0))
predicted = static_wall - versine
print(f"[KONTROLA] promień {radius} m, cięciwa nominalna {chord:.3f} m, "
      f"rzeczywista {body_chord:.3f} m -> strzałka {versine*1000:.1f} mm")
print(f"[KONTROLA] wysokość styku {contact_height:.3f} m, luz statyczny {static_wall:.4f} m, "
      f"przewidziany {predicted:.4f} m, zmierzony {worst['min_clearance_m']:.4f} m")
# Kontrola jest KIERUNKOWA, nie symetryczna, i to nie jest złagodzenie progu.
# Strzałka liczy się z promienia w ŚRODKU SKŁADU, a bryła, w której wypada minimum,
# leży poza środkiem — tam oś jest łagodniejsza, więc wzór przeszacowuje wychylenie
# i zaniża luz. Zmierzone na trzech pakietach, oba tory: wzór jest zachowawczy
# w 6 z 6 przypadków, z zapasem 1,2-13,3 mm. Symetryczny próg +-10 mm był
# skalibrowany na samym pakiecie A i pakiet E przekraczał go o 3,3 mm, mimo że
# błądził w bezpieczną stronę.
#
# Próba poprawienia wzoru promieniem na cięciwie samej bryły pogarsza sprawę
# (pakiet A: rozjazd rośnie z 3,9 do 69,0 mm), więc to nie jest kwestia doboru
# promienia. `clearance_profile.py` mówi to samo, podając trzy warianty wzoru
# i etykietując każdy jako optymistyczny albo zachowawczy zamiast wybierać jeden.
slack = worst["min_clearance_m"] - predicted
print(f"[KONTROLA] wzór wobec siatki: zapas {slack*1000:+.1f} mm "
      f"({'zachowawczy' if slack >= 0 else 'OPTYMISTYCZNY'})")
if slack < -1e-9:
    raise SystemExit(f"BŁĄD: wzór OBIECUJE {(-slack)*1000:.1f} mm więcej luzu, niż mierzy "
                     "siatka — kontrola skrajni nie może błądzić w tę stronę")
if slack > FORMULA_MAX_SLACK_M:
    raise SystemExit(f"BŁĄD: wzór jest zachowawczy o {slack*1000:.1f} mm, ponad próg "
                     f"{FORMULA_MAX_SLACK_M*1000:.0f} mm — to już nie jest ta sama wielkość "
                     "mierzona dwiema drogami")
CHECKPY

echo
echo "[RENDER] zestaw clearance w najgorszym punkcie"
ANCHORS="$(python3 - "$OUT/m7_t1.json" <<'ANCHORPY'
import json, os, sys
sys.path.insert(0, os.path.join("tools", "blender"))
import placement as PL, sweep as SW

report = json.load(open(sys.argv[1], encoding="utf-8"))
document = json.load(open(os.environ["AXIS"], encoding="utf-8"))
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
  --in "$OUT/${NAME}_with_M7_t1.glb" --set clearance --prefix M7_GAP --out "$RENDERS" \
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
echo "============================================================"
echo "[PROFIL] luz wzdłuż CAŁEJ osi, oba tory, plus zamiatana obwiednia"
# Oba tory idą równolegle: pomiar jednego nie zależy od drugiego, a każdy to ~30 s
# skanu w czystym Pythonie. Logi lecą do plików i są wypisywane po kolei, bo dwa
# strumienie w jednym terminalu przeplotłyby się w nieczytelną kaszę.
PROFILE_PID=()
for TRACK in 0 1; do
  "${BLENDER[@]}" tools/blender/profile_vehicle.py -- \
    --vehicle "$OUT/M7_shell.glb" --centerline "$AXIS" --profile "$PROFILE" \
    --tunnel "$OUT/$NAME.glb" --track "$TRACK" \
    --out "$OUT/profile_t$TRACK.json" \
    --swept-out "$OUT/M7_swept_t$TRACK.glb" \
    --swept-scene-out "$OUT/${NAME}_with_swept_t$TRACK.glb" \
    >"$OUT/profile_t$TRACK.log" 2>&1 &
  PROFILE_PID[TRACK]=$!
done
PROFILE_STATUS=0
for TRACK in 0 1; do
  wait "${PROFILE_PID[TRACK]}" || PROFILE_STATUS=1
done
for TRACK in 0 1; do
  grep -E '^(\[PROFIL\]|\[KONTROLA\]|\[OBWIEDNIA\]|BŁĄD)' "$OUT/profile_t$TRACK.log" || true
done
[ "$PROFILE_STATUS" -eq 0 ] || fail "profil luzu zgłosił problem — patrz $OUT/profile_t*.log"

echo
echo "[DETERMINIZM] dwa przebiegi tego samego kodu muszą dać identyczny raport"
# Na siatce zgrubnej (krok 25 m), bo determinizm nie zależy od gęstości siatki,
# a dwa pełne przebiegi to minuta CI za tę samą informację. Ścieżka kodu jest ta sama:
# skan, doszlifowanie, obwiednia, kontrola redukcji.
for RUN in a b; do
  "${BLENDER[@]}" tools/blender/profile_vehicle.py -- \
    --vehicle "$OUT/M7_shell.glb" --centerline "$AXIS" --profile "$PROFILE" --track 1 \
    --step 25 --swept-half-range 60 --verify-full 1 \
    --out "$OUT/determinism_$RUN.json" --swept-out "$OUT/determinism_$RUN.glb" \
    >"$OUT/determinism_$RUN.log" 2>&1
done
python3 - "$OUT/determinism_a.json" "$OUT/determinism_b.json" <<'DETPY'
import json, sys

# Klucze zależne od zegara i od nazwy pliku wyjściowego; reszta raportu ma być
# powtarzalna co do bitu.
VOLATILE_TOP = ("timing_s",)
VOLATILE_SWEPT = ("glb", "glb_bytes", "scene_glb", "scene_glb_bytes", "seconds")


def view(path):
    report = json.load(open(path, encoding="utf-8"))
    for key in VOLATILE_TOP:
        report.pop(key, None)
    for key in VOLATILE_SWEPT:
        report.get("swept_envelope", {}).pop(key, None)
    report.get("refinement", {}).pop("seconds", None)
    return report


first, second = view(sys.argv[1]), view(sys.argv[2])
if json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True):
    print(f"[DETERMINIZM] {len(first['profile'])} pozycji, raporty identyczne")
else:
    changed = [k for k in sorted(set(first) | set(second))
               if json.dumps(first.get(k), sort_keys=True) != json.dumps(second.get(k), sort_keys=True)]
    raise SystemExit(f"BŁĄD: drugi przebieg dał inny raport; różnią się klucze: {changed}")
DETPY

echo
echo "[KONTROLA] profil: pokrycie osi, znak luzu, zgodność z place_vehicle, obwiednia"
python3 - "$OUT/profile_t0.json" "$OUT/profile_t1.json" "$OUT/m7_t0.json" "$OUT/m7_t1.json" <<'PROFILECHECK'
import json, sys

TOOL_AGREEMENT_MM = 0.5
# Ten sam próg i ta sama zasada co w bloku [KONTROLA] wyżej: wzór na strzałkę liczy
# się z promienia w środku składu, a bryła z minimum leży poza środkiem, więc wzór
# jest z natury zachowawczy. `clearance_profile.py` liczy już znak tej różnicy jako
# `formula_optimistic` — guard poniżej po prostu przestaje go ignorować.
FORMULA_MAX_SLACK_MM = 50.0
problems = []
for track in (0, 1):
    profile = json.load(open(sys.argv[1 + track], encoding="utf-8"))
    single = json.load(open(sys.argv[3 + track], encoding="utf-8"))
    stats = profile["statistics"]
    refined = stats["with_refinement"]
    print(f"[KONTROLA] tor {track} ({profile['track_offset_m']:+.2f} m): "
          f"{stats['positions']} pozycji na siatce {profile['step_m']} m + "
          f"{profile['refinement']['positions']} doszlifowanych, minimum "
          f"{refined['min_clearance_m']:+.4f} m na {refined['min_at']['object']} "
          f"(chainage {refined['min_at']['chainage_m']} m, wiąże {refined['min_at']['bound_by']}), "
          f"P05 {stats['p05_clearance_m']:.4f} m, mediana {stats['median_clearance_m']:.4f} m")

    if profile["coverage_problems"]:
        problems += [f"tor {track}: {p}" for p in profile["coverage_problems"]]
    # Ujemny luz JEST wynikiem do zaraportowania — dlatego jest wypisywany, a nie
    # przemilczany; ale CI ma się wtedy wywalić, żeby nikt tego nie przegapił.
    if refined["negative_positions"]:
        problems.append(f"tor {track}: {refined['negative_positions']} pozycji z ujemnym luzem")

    for item in profile["reduction_check"]:
        if item["delta_mm"] > 1e-3:
            problems.append(f"tor {track}: redukcja kandydatów gubi {item['delta_mm']} mm "
                            f"w pozycji {item['start_m']} m")
    print(f"[KONTROLA] tor {track}: redukcja {profile['candidate_vertices']} z "
          f"{profile['source_vertices']} wierzchołków, rozjazd wobec pełnego przebiegu "
          f"{max(i['delta_mm'] for i in profile['reduction_check']):.4f} mm")

    # Zgodność dwóch niezależnych implementacji tego samego pomiaru: profil w pozycji
    # odniesienia wobec place_vehicle.py, który mierzy dokładnie tę pozycję.
    reference = profile["crosscheck"]["reference_measurement"]
    delta = abs(reference["clearance_m"] - single["min_clearance_m"]) * 1000.0
    print(f"[KONTROLA] tor {track}: pozycja odniesienia — profil {reference['clearance_m']:.4f} m, "
          f"place_vehicle {single['min_clearance_m']:.4f} m, rozjazd {delta:.3f} mm")
    if delta > TOOL_AGREEMENT_MM:
        problems.append(f"tor {track}: profil i place_vehicle rozjeżdżają się o {delta:.3f} mm")

    at_reference = profile["crosscheck"]["at_reference"]
    if at_reference["bound_by"] == "ściana":
        if at_reference["formula_optimistic"]:
            problems.append(f"tor {track}: wzór w pozycji odniesienia OBIECUJE "
                            f"{at_reference['delta_mm']} mm więcej luzu, niż mierzy siatka")
        elif at_reference["delta_mm"] > FORMULA_MAX_SLACK_MM:
            problems.append(f"tor {track}: wzór w pozycji odniesienia jest zachowawczy o "
                            f"{at_reference['delta_mm']} mm, ponad próg {FORMULA_MAX_SLACK_MM:.0f} mm")
    print(f"[KONTROLA] tor {track}: wzór na strzałkę w pozycji odniesienia — przewidziany "
          f"{at_reference['predicted_clearance_m']:.4f} m wobec "
          f"{at_reference['measured_clearance_m']:.4f} m, rozjazd {at_reference['delta_mm']} mm "
          f"({'OPTYMISTYCZNY' if at_reference['formula_optimistic'] else 'zachowawczy'})")
    for variant in profile["crosscheck"]["at_minimum"]["variants"]:
        print(f"[KONTROLA] tor {track}: w minimum, {variant['variant']} (R {variant['radius_m']} m) "
              f"-> {variant['predicted_clearance_m']:.4f} m, rozjazd {variant['delta_mm']} mm "
              f"({'optymistyczny' if variant['formula_optimistic'] else 'zachowawczy'})")

    swept = profile["swept_envelope"]
    print(f"[KONTROLA] tor {track}: obwiednia {swept['from_chainage_m']}..{swept['to_chainage_m']} m, "
          f"{swept['rings']} pierścieni, bbox {swept['bbox_size_m']} m, luz "
          f"{swept['min_clearance_m']:+.4f} m wobec {swept['scan_min_in_range_m']} m ze skanu, "
          f"wierzchołków poza obwiednią {swept['vertices_outside_envelope']}/{swept['vertices_checked']}")
    if swept["vertices_outside_envelope"]:
        problems.append(f"tor {track}: obwiednia nie zawiera składu w każdej pozycji")
    if swept["min_clearance_m"] > swept["scan_min_in_range_m"] + 1e-9:
        problems.append(f"tor {track}: obwiednia ma większy luz niż skan — nie jest nadzbiorem")
    if min(swept["bbox_size_m"]) <= 0.0 or swept["bbox_size_m"][2] < 2.0:
        problems.append(f"tor {track}: bbox obwiedni {swept['bbox_size_m']} m jest bez sensu")
    if swept["is_static_envelope"]:
        problems.append(f"tor {track}: obwiednia zgłasza się jako statyczna")

    for place in profile["critical_places"]:
        if place["threshold_m"] != profile["thresholds_m"][1]:
            continue
        station = place["nearest_station"]
        print(f"[KRYTYCZNE] tor {track}: luz {place['min_clearance_m']:.4f} m w chainage "
              f"{place['chainage_m']} m ({place['bound_by']}, {place['object']}) — "
              f"{station['distance_m']:+.0f} m od {station['name']}, między "
              f"{place['between']['after']} i {place['between']['before']}")

if problems:
    raise SystemExit("BŁĄD: " + "; ".join(problems))
print("[KONTROLA] profil, obwiednia i zgodność narzędzi: OK")
PROFILECHECK

echo
echo "[ROUNDTRIP] zamiatana obwiednia musi się wczytać z powrotem z tym samym bboxem"
for TRACK in 0 1; do
  python3 - "$OUT/profile_t$TRACK.json" "$OUT/swept_metrics_t$TRACK.json" <<'METRICSPY'
import json, sys
swept = json.load(open(sys.argv[1], encoding="utf-8"))["swept_envelope"]
json.dump({"bbox_size_m": swept["bbox_size_m"], "vertices": swept["vertices"],
           "faces": swept["faces"]}, open(sys.argv[2], "w", encoding="utf-8"))
METRICSPY
  "${BLENDER[@]}" tools/blender/glb_roundtrip.py -- --in "$OUT/M7_swept_t$TRACK.glb" \
    --expect-objects 1 --expect-metrics "$OUT/swept_metrics_t$TRACK.json" \
    --out "$OUT/swept_roundtrip_t$TRACK.json" | grep -E '^\[ROUNDTRIP\]'
done

echo
echo "[RENDER] przekrój w NAJGORSZYM punkcie profilu i zamiatana obwiednia w tunelu"
WORST_START="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1],encoding='utf-8'))['statistics']['with_refinement']['min_at']['start_m'])" "$OUT/profile_t1.json")"
echo "[RENDER] czoło składu na chainage $WORST_START m (tor 1)"
"${BLENDER[@]}" tools/blender/place_vehicle.py -- \
  --tunnel "$OUT/$NAME.glb" --vehicle "$OUT/M7_shell.glb" --centerline "$AXIS" \
  --profile "$PROFILE" --track 1 --chainage "$WORST_START" \
  --out "$OUT/${NAME}_with_M7_worst.glb" --report "$OUT/m7_worst.json" \
  --min-clearance-m 0.0 | grep -E '^\[OSADZENIE\] ZMIERZONY'

python3 - "$OUT/profile_t1.json" "$OUT/m7_worst.json" <<'WORSTPY'
import json, sys
profile = json.load(open(sys.argv[1], encoding="utf-8"))
single = json.load(open(sys.argv[2], encoding="utf-8"))
expected = profile["statistics"]["with_refinement"]["min_clearance_m"]
delta = abs(expected - single["min_clearance_m"]) * 1000.0
print(f"[KONTROLA] w globalnym minimum: profil {expected:.4f} m, place_vehicle "
      f"{single['min_clearance_m']:.4f} m, rozjazd {delta:.3f} mm")
if delta > 0.5:
    raise SystemExit(f"BŁĄD: dwie implementacje pomiaru rozjeżdżają się o {delta:.3f} mm "
                     "w punkcie, w którym luz jest najmniejszy")
WORSTPY

ANCHORS="$(python3 - "$OUT/profile_t1.json" <<'ANCHORPY'
import json, os, sys
sys.path.insert(0, os.path.join("tools", "blender"))
import placement as PL, sweep as SW

report = json.load(open(sys.argv[1], encoding="utf-8"))
document = json.load(open(os.environ["AXIS"], encoding="utf-8"))
points = SW.catmull_rom([tuple(float(c) for c in p) for p in document["points"]],
                        report["ring_step_m"])
stations = SW.chainages(points)
best = report["statistics"]["with_refinement"]["min_at"]
gap = best["chainage_m"]
nose = best["start_m"]


def at(chainage, z=1.75):
    position, _index, _t = PL.frame_at(points, stations, chainage)
    return f"{position[0]:.3f},{position[1]:.3f},{z:.3f}"


print(f"--anchor gap_eye={at(gap)} --anchor gap_target={at(gap + 10.0)} "
      f"--anchor approach_eye={at(nose - 32.0)} --anchor approach_target={at(nose - 2.0)}")
ANCHORPY
)"
"${BLENDER[@]}" tools/visual/capture_blender.py -- \
  --in "$OUT/${NAME}_with_M7_worst.glb" --set clearance --prefix M7_WORST --out "$RENDERS" \
  --centerline "$AXIS" $ANCHORS >/dev/null

# Obwiednia potrzebuje INNEJ kotwicy `approach` niż pojazd. Zamiatana bryła jest
# szersza od pudła i ciągnie się 300 m, więc oko postawione na osi wpada w nią i widać
# jednolitą płaszczyznę zamiast tunelu. Oko idzie 3 m w bok, na sąsiedni tor, i patrzy
# ukośnie na obwiednię — wtedy w kadrze jest i wnętrze tunelu, i bok zamiatanej bryły.
SWEPT_ANCHORS="$(python3 - "$OUT/profile_t1.json" <<'SWEPTANCHORPY'
import json, os, sys
sys.path.insert(0, os.path.join("tools", "blender"))
import clearance_profile as CP, placement as PL, sweep as SW

report = json.load(open(sys.argv[1], encoding="utf-8"))
document = json.load(open(os.environ["AXIS"], encoding="utf-8"))
points = SW.catmull_rom([tuple(float(c) for c in p) for p in document["points"]],
                        report["ring_step_m"])
stations = SW.chainages(points)
frames = SW.rmf_frames(points)
gap = report["statistics"]["with_refinement"]["min_at"]["chainage_m"]


def at(chainage, lateral=0.0, z=1.75):
    position, _index, _t = PL.frame_at(points, stations, chainage)
    right = frames[CP.nearest_frame(frames, stations, position, hint_m=chainage)][2]
    return (f"{position[0] + right[0] * lateral:.3f},"
            f"{position[1] + right[1] * lateral:.3f},{z:.3f}")


print(f"--anchor gap_eye={at(gap)} --anchor gap_target={at(gap + 10.0)} "
      f"--anchor approach_eye={at(gap - 40.0, -3.0)} "
      f"--anchor approach_target={at(gap + 5.0, 1.0)}")
SWEPTANCHORPY
)"
"${BLENDER[@]}" tools/visual/capture_blender.py -- \
  --in "$OUT/${NAME}_with_swept_t1.glb" --set clearance --prefix M7_SWEPT --out "$RENDERS" \
  --centerline "$AXIS" $SWEPT_ANCHORS >/dev/null

for PREFIX in M7_WORST M7_SWEPT; do
  python3 tools/visual/compare.py --set clearance --current "$RENDERS" --prefix "$PREFIX" \
    --out "$OUT/render-sanity-$PREFIX.json" --markdown "$OUT/render-sanity-$PREFIX.md" \
    --allow-new-baseline >/dev/null
  python3 - "$OUT/render-sanity-$PREFIX.json" "$PREFIX" <<'SANITY2PY'
import json, sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
manifest = json.load(open("tools/visual/cameras.json", encoding="utf-8"))
expected = {c["id"] for c in manifest["scene_sets"]["clearance"]["cameras"]}
bad = []
for image in report["images"]:
    checks, metrics = image["checks"], image["metrics"]
    ok = checks.get("exists") and checks.get("dimension") and checks.get("not_empty")
    print(f"[RENDER] {sys.argv[2]}/{image['camera']}: ink={metrics['ink_fraction']} "
          f"std={metrics['luma_std']} poziomy={metrics['distinct_levels']} "
          f"-> {'OK' if ok else 'ODRZUCONY'}")
    if not ok:
        bad.append(image["camera"])
missing = expected - {i["camera"] for i in report["images"]}
if missing:
    raise SystemExit(f"BŁĄD: brak renderów {sys.argv[2]}: {sorted(missing)}")
if bad:
    raise SystemExit(f"BŁĄD: puste lub jednolite rendery {sys.argv[2]}: " + ", ".join(bad))
SANITY2PY
done

echo
echo "[VERIFY] zestaw testów Pythona"
python3 tools/tests/test_all.py

echo
echo "============================================================"
echo "[RESULT] pomiar skrajni zakończony w ${SECONDS}s"
echo "[RESULT] OGLĘDZINY RENDERÓW SĄ NADAL WYMAGANE:"
for f in "$RENDERS"/M7_GAP_*.png "$RENDERS"/M7_WORST_*.png "$RENDERS"/M7_SWEPT_*.png; do
  echo "  - $f ($(stat -c%s "$f") B)"
done

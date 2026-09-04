"""Profil luzu M7 wzdłuż CAŁEJ osi + zamiatana obwiednia składu. Headless.

    blender --background --python tools/blender/profile_vehicle.py -- \
        --vehicle build/M7_shell.glb --centerline data/track/L1_A.json \
        --profile box_double --track 1 --out build/profile_t1.json \
        --swept-out build/M7_swept_t1.glb --tunnel build/L1_A.glb \
        --swept-scene-out build/L1_A_with_swept_t1.glb

`place_vehicle.py` mierzy luz w JEDNYM punkcie — automatycznie wybranym najciaśniejszym
łuku. To narzędzie przesuwa skład wzdłuż całej trasy i odpowiada na pytanie, którego
tamto nie zadaje: czy zmierzony dołek jest odosobniony, i gdzie jeszcze robi się ciasno.

Matematyka siedzi w `clearance_profile.py` (czysty Python, testowalny bez Blendera).
Tu zostaje tylko to, co wymaga bpy: wczytanie wierzchołków pojazdu z GLB, zbudowanie
siatki zamiatanej obwiedni i eksport.

Zamiatana obwiednia to NIE jest `--envelope-out` z `m7_shell.py`. Tamta jest statyczną
skrajnią prostego składu; ta jest objętością, którą skład zajmuje przejeżdżając łuk.
"""
import argparse
import json
import os
import sys
import time

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clearance as CL  # noqa: E402
import clearance_profile as CP  # noqa: E402
import m7_layout  # noqa: E402
import placement as PL  # noqa: E402
import profile_scan as PS  # noqa: E402
import profiles  # noqa: E402
import sweep as SW  # noqa: E402

DEFAULT_RING_STEP_M = 5.0
UV_METRES_PER_UNIT = 4.0
# Zgodność wzoru na strzałkę cięciwy z pomiarem na siatce w POZYCJI ODNIESIENIA jest
# KIERUNKOWA, nie symetryczna, i to nie jest złagodzenie progu. Strzałkę liczy się
# z promienia w środku składu, a bryła, w której wypada minimum, leży poza środkiem —
# tam oś jest łagodniejsza, więc wzór przeszacowuje wychylenie i ZANIŻA luz. Zmierzone
# na pakietach A, B i E, oba tory: wzór jest zachowawczy w 6 z 6 przypadków, z zapasem
# 1,2-13,3 mm. Symetryczny próg +-10 mm był skalibrowany na samym pakiecie A i pakiet E
# przekraczał go o 2,8 mm, mimo że błądził w bezpieczną stronę.
#
# Wzór OPTYMISTYCZNY — obiecujący więcej luzu, niż mierzy siatka — jest błędem zawsze,
# niezależnie od wielkości; kontrola skrajni nie może błądzić w tę stronę.

# W globalnym minimum wzór ma prawo być gorszy, bo oś nie jest tam łukiem okręgu.
# Ta wartość nie jest oceną dokładności, tylko bezpiecznikiem na regresję: rozjazd
# powyżej 100 mm oznaczałby, że rozjechał się model, a nie krzywizna osi.



def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Profil luzu wzdłuż osi i zamiatana obwiednia")
    parser.add_argument("--vehicle", required=True)
    parser.add_argument("--centerline", required=True)
    parser.add_argument("--tunnel", help="GLB tunelu — tylko do sceny z obwiednią")
    parser.add_argument("--profile", default="box_double", choices=list(profiles.PROFILES))
    parser.add_argument("--track", type=int, default=1)
    parser.add_argument("--ring-step", type=float, default=DEFAULT_RING_STEP_M)
    parser.add_argument("--step", type=float, default=CP.DEFAULT_STEP_M,
                        help="krok przesuwania składu wzdłuż osi")
    parser.add_argument("--refine-step", type=float, default=CP.DEFAULT_REFINE_STEP_M,
                        help="krok doszlifowania wokół dołków; 0 wyłącza")
    parser.add_argument("--bucket", type=float, default=CP.CANDIDATE_BUCKET_M)
    parser.add_argument("--verify-full", type=int, default=3,
                        help="ile pozycji przeliczyć naiwnie, po wszystkich wierzchołkach")
    parser.add_argument("--swept-half-range", type=float, default=CP.DEFAULT_SWEPT_HALF_RANGE_M)
    parser.add_argument("--swept-from", type=float, help="początek zakresu obwiedni w chainage")
    parser.add_argument("--swept-to", type=float, help="koniec zakresu obwiedni w chainage")
    parser.add_argument("--swept-out", help="GLB samej zamiatanej obwiedni")
    parser.add_argument("--swept-scene-out", help="GLB obwiedni razem z tunelem")
    parser.add_argument("--out", required=True, help="JSON z profilem i statystykami")
    parser.add_argument("--min-clearance-m", type=float, default=None,
                        help="poniżej tej wartości narzędzie kończy błędem PO zapisie raportu")
    return parser.parse_args(argv)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def import_glb(path, tag):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    added = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if not added:
        raise SystemExit(f"BŁĄD: {path} nie wniósł ani jednego mesha")
    for obj in added:
        obj["metro_source"] = tag
    return added


def read_bodies(objects):
    """Bryły pojazdu jako czyste krotki — dalej liczy już `clearance_profile`, bez bpy."""
    bodies = []
    for obj in objects:
        matrix = obj.matrix_world
        vertices = [tuple(matrix @ v.co) for v in obj.data.vertices]
        bodies.append({"name": obj.name, "vertices": vertices,
                       "span": (min(v[0] for v in vertices), max(v[0] for v in vertices))})
    bodies.sort(key=lambda b: b["span"][0])
    return bodies


def build_envelope_object(mesh, name="M7_swept_envelope"):
    """Siatka zamiatanej obwiedni w Blenderze, z UV — bez UV round-trip ją odrzuca."""
    data = bpy.data.meshes.new(name)
    data.from_pydata([tuple(v) for v in mesh["vertices"]], [], [tuple(f) for f in mesh["faces"]])
    data.validate()
    data.update()
    uv = data.uv_layers.new(name="UVMap")
    columns = mesh["columns"]
    for loop_index, loop in enumerate(data.loops):
        vertex = loop.vertex_index
        uv.data[loop_index].uv = ((vertex % columns) / float(columns),
                                  (vertex // columns) * 1.0 / UV_METRES_PER_UNIT)
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    return obj


def export(objects, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True)
    return os.path.getsize(path)


def scan(points, frames, stations, planes, reduced, positions, track_offset, collector=None):
    return [CP.measure_position(points, frames, stations, planes, reduced, start, track_offset,
                                collector=collector)
            for start in positions]


def main():
    args = parse_args()
    started = time.time()
    clear_scene()

    with open(args.centerline, encoding="utf-8") as handle:
        document = json.load(handle)
    points = SW.catmull_rom([tuple(float(c) for c in p) for p in document["points"]],
                            args.ring_step)
    frames = SW.rmf_frames(points)
    stations = SW.chainages(points)
    axis_length = stations[-1]

    offsets = profiles.PROFILES[args.profile].get("track_offsets", [0.0])
    try:
        track_offset = PS.track_offset(offsets, args.track)
    except ValueError as err:
        raise SystemExit(f"BŁĄD: profil {args.profile} {err}")
    ring = profiles.profile_points(args.profile)
    planes = CP.halfplanes(ring)

    vehicle = import_glb(args.vehicle, "vehicle")
    bodies = read_bodies(vehicle)
    train_length = max(b["span"][1] for b in bodies) - min(b["span"][0] for b in bodies)
    reduced = CP.reduce_bodies(bodies, args.bucket)

    positions = CP.scan_positions(axis_length, train_length, args.step)
    print(f"[PROFIL] oś {axis_length:.1f} m, skład {train_length:.3f} m w {len(bodies)} bryłach")
    print(f"[PROFIL] tor {args.track} ({track_offset:+.2f} m), profil {args.profile}, "
          f"krok {args.step} m -> {len(positions)} pozycji")
    print(f"[PROFIL] kandydaci {CP.candidate_count(reduced)} z "
          f"{sum(len(b['vertices']) for b in bodies)} wierzchołków, "
          f"{sum(len(b['bands']) for b in reduced)} pasm X")

    t0 = time.time()
    records = scan(points, frames, stations, planes, reduced, positions, track_offset)
    scan_seconds = time.time() - t0
    print(f"[PROFIL] skan zgrubny: {scan_seconds:.2f} s "
          f"({1000.0 * scan_seconds / len(positions):.2f} ms na pozycję)")

    coarse_min = min(r["clearance_m"] for r in records)
    refined = {"step_m": args.refine_step, "windows": 0, "positions": 0,
               "min_before_m": round(coarse_min, 6), "min_after_m": round(coarse_min, 6),
               "gain_mm": 0.0, "seconds": 0.0}
    if args.refine_step > 0.0:
        windows = CP.refine_windows(records, args.step)
        extra = PS.refine_positions(windows, args.refine_step, axis_length,
                                    train_length, positions)
        t0 = time.time()
        more = scan(points, frames, stations, planes, reduced, extra, track_offset)
        refined["seconds"] = round(time.time() - t0, 2)
        records.extend(more)
        records.sort(key=lambda r: r["start_m"])
        refined["windows"] = len(windows)
        refined["positions"] = len(extra)
        refined["min_after_m"] = round(min(r["clearance_m"] for r in records), 6)
        refined["gain_mm"] = round(max(0.0, coarse_min - refined["min_after_m"]) * 1000.0, 3)
        print(f"[PROFIL] doszlifowanie krokiem {args.refine_step} m: {len(windows)} okien, "
              f"{len(extra)} pozycji, minimum spadło o {refined['gain_mm']:.3f} mm "
              f"({refined['seconds']:.2f} s)")

    # Percentyle liczą się WYŁĄCZNIE na siatce równomiernej. Doszlifowanie zagęszcza
    # próbki tylko w dołkach, więc wrzucone do jednego worka przesunęłoby P05 i medianę
    # w stronę dołków i statystyka opisywałaby rozkład próbek, nie rozkład luzu.
    coarse = set(positions)
    grid_records = [r for r in records if r["start_m"] in coarse]
    stats = CP.statistics(grid_records)
    stats["grid"] = f"równomierna, krok {args.step} m"
    everything = CP.statistics(records)
    stats["with_refinement"] = {
        "positions": everything["positions"],
        "min_clearance_m": everything["min_clearance_m"],
        "min_at": everything["min_at"],
        "negative_positions": everything["negative_positions"],
    }
    gaps = CP.coverage_gaps(grid_records, train_length, axis_length, args.step)

    # Dowód, że redukcje nie gubią minimum: te same pozycje liczone naiwnie,
    # po WSZYSTKICH wierzchołkach i przez placement.distance_to_boundary.
    verification = []
    if args.verify_full > 0:
        t0 = time.time()
        for record in PS.verification_sample(records, args.verify_full):
            naive = CP.measure_position_naive(points, frames, stations, ring, bodies,
                                              record["start_m"], track_offset)
            verification.append(PS.verification_entry(record, naive))
        print(f"[PROFIL] kontrola redukcji na {len(verification)} pozycjach "
              f"({time.time() - t0:.2f} s):")
        for item in verification:
            print(f"[PROFIL]   czoło {item['start_m']:8.2f} m: redukcja {item['reduced_m']:.6f} m, "
                  f"pełny przebieg {item['full_m']:.6f} m, rozjazd {item['delta_mm']:.4f} mm")

    worst = min(records, key=lambda r: r["clearance_m"])
    spec_width = profiles.M7_WIDTH_M

    # Pozycja odniesienia: dokładnie ta, którą wybiera `place_vehicle.py` — skład
    # wyśrodkowany na najmniejszym promieniu. Pomiar w tym punkcie musi się zgadzać
    # z tamtym narzędziem co do dziesiątych milimetra, inaczej dwie implementacje
    # tego samego pomiaru rozjechały się i profil nie jest porównywalny z #55.
    reference_station, reference_radius = PL.worst_chainage(points, train_length / 6.0,
                                                            train_length)
    reference_start = reference_station - train_length / 2.0
    reference = CP.measure_position(points, frames, stations, planes, reduced,
                                    reference_start, track_offset)
    static_wall = PS.static_wall_clearance(ring, track_offset, spec_width)
    # Wariant ODNIESIENIA jest przepisany 1:1 z tools/ci/vehicle_clearance.sh: rzeczywista
    # cięciwa bryły, w której wypadło minimum, razy promień w ŚRODKU składu. Ma wyjść
    # ten sam rozjazd co w #55, inaczej nowe narzędzie liczy coś innego niż stare.
    check_reference = PS.formula_prediction(reference["chord_m"], reference_radius, static_wall,
                                         reference["clearance_m"], "pozycja odniesienia")
    check_reference["start_m"] = round(reference_start, 3)
    check_reference["centre_chainage_m"] = round(reference_station, 2)
    check_reference["object"] = reference["object"]
    check_reference["bound_by"] = reference["bound_by"]

    # W globalnym minimum wzór dostaje trzy różne promienie — bo „promień" nie jest
    # jedną liczbą, tylko zależy od tego, gdzie i na jakiej cięciwie się go mierzy.
    worst_chord = worst["chord_m"]
    nominal_chord = CL.car_chord_m(m7_layout.load_spec())
    local_radius = CP.body_radius_m(points, stations, worst_chord,
                                    0.5 * (worst["body_from_m"] + worst["body_to_m"]))
    _station_real, min_radius_real = CP.min_radius_on_chord(points, stations, worst_chord,
                                                            train_length)
    _station_nom, min_radius_nominal = CP.min_radius_on_chord(points, stations, nominal_chord,
                                                              train_length)
    variants = [
        PS.formula_prediction(worst_chord, local_radius, static_wall, worst["clearance_m"],
                           "promień lokalny w środku bryły"),
        PS.formula_prediction(worst_chord, min_radius_real, static_wall, worst["clearance_m"],
                           "najmniejszy promień osi na cięciwie rzeczywistej"),
        PS.formula_prediction(nominal_chord, min_radius_nominal, static_wall, worst["clearance_m"],
                           "najmniejszy promień osi na cięciwie nominalnej 94/6"),
    ]
    check = dict(variants[1])
    check["start_m"] = round(worst["start_m"], 3)
    check["object"] = worst["object"]
    check["bound_by"] = worst["bound_by"]
    check["local_radius_m"] = round(local_radius, 2) if local_radius else None
    check["axis_deviation_mm"] = round(1000.0 * CP.chord_deviation_m(
        points, stations, worst["body_from_m"], worst["body_to_m"]), 1)
    check["variants"] = variants

    print(f"[KONTROLA] pozycja odniesienia (jak place_vehicle): czoło {reference_start:.2f} m, "
          f"luz {reference['clearance_m']:.4f} m na {reference['object']}, "
          f"wiąże {reference['bound_by']}")
    print(f"[KONTROLA] odniesienie: cięciwa {check_reference['chord_m']:.3f} m, promień "
          f"{check_reference['radius_m']} m -> strzałka {check_reference['versine_mm']:.1f} mm, "
          f"luz statyczny do ściany {static_wall:.4f} m, przewidziany "
          f"{check_reference['predicted_clearance_m']:.4f} m, "
          f"rozjazd {check_reference['delta_mm']:.1f} mm")
    print(f"[KONTROLA] najgorsza pozycja: czoło {worst['start_m']:.2f} m, luz "
          f"{worst['clearance_m']:.4f} m na {worst['object']}, wiąże {worst['bound_by']}, "
          f"rzeczywiste odchylenie osi od cięciwy {check['axis_deviation_mm']:.1f} mm")
    for variant in variants:
        print(f"[KONTROLA]   {variant['variant']}: cięciwa {variant['chord_m']:.3f} m, "
              f"R {variant['radius_m']} m, strzałka {variant['versine_mm']:.1f} mm, "
              f"przewidziany {variant['predicted_clearance_m']:.4f} m, rozjazd "
              f"{variant['delta_mm']:.1f} mm "
              f"({'wzór optymistyczny' if variant['formula_optimistic'] else 'wzór zachowawczy'})")

    # --- zamiatana obwiednia ---------------------------------------------------
    centre = worst["chainage_m"]
    low, high = PS.swept_range(centre, args.swept_half_range, args.swept_from,
                               args.swept_to, axis_length)
    envelope = CP.SweptEnvelope(stations, low, high)
    contributing = PS.contributing_starts(records, train_length, low, high)
    t0 = time.time()
    samples = []
    for index, start in enumerate(contributing):
        keep = PS.keep_sample(index, start, worst["start_m"])
        collected = []

        def collector(chainage, lateral, vertical, _sink=collected, _keep=keep):
            envelope.add(chainage, lateral, vertical)
            if _keep:
                _sink.append((chainage, lateral, vertical))

        CP.measure_position(points, frames, stations, planes, reduced, start, track_offset,
                            collector=collector)
        samples.extend(collected)
    rings = envelope.rings()
    swept_seconds = time.time() - t0
    mesh = CP.swept_mesh(frames, rings)
    bbox_min, bbox_max = CP.mesh_bbox(mesh)
    env_clearance, env_where = CP.envelope_clearance(rings, planes)
    outside, checked = CP.envelope_contains(envelope, rings, samples)
    in_range = PS.in_range_clearances(records, low, high)
    swept = {
        "from_chainage_m": round(low, 2),
        "to_chainage_m": round(high, 2),
        "length_m": round(high - low, 2),
        "positions": len(contributing),
        "rings": len(rings),
        "directions": len(envelope.directions),
        "vertices": len(mesh["vertices"]),
        "faces": len(mesh["faces"]),
        "bbox_min_m": [round(v, 4) for v in bbox_min],
        "bbox_max_m": [round(v, 4) for v in bbox_max],
        "bbox_size_m": [round(bbox_max[i] - bbox_min[i], 4) for i in range(3)],
        "min_clearance_m": round(env_clearance, 6),
        "min_clearance_at": env_where,
        "scan_min_in_range_m": round(min(in_range), 6) if in_range else None,
        "vertices_outside_envelope": outside,
        "vertices_checked": checked,
        "seconds": round(swept_seconds, 2),
        "is_static_envelope": False,
        "note": ("przekrój półpłaszczyzn podparcia: obwiednia jest nadzbiorem objętości "
                 "zajętej przez skład, bo do testu kolizji niedomiar byłby niebezpieczny"),
    }
    print(f"[OBWIEDNIA] zakres {low:.1f}..{high:.1f} m ({high - low:.0f} m), "
          f"{len(contributing)} pozycji składu, {len(rings)} pierścieni x "
          f"{len(envelope.directions)} kierunków")
    print(f"[OBWIEDNIA] bbox {swept['bbox_size_m']} m, luz obwiedni "
          f"{env_clearance:+.4f} m wobec {swept['scan_min_in_range_m']} m ze skanu")
    print(f"[OBWIEDNIA] wierzchołki pojazdu poza obwiednią: {outside} z {checked}")

    if args.swept_out or args.swept_scene_out:
        obj = build_envelope_object(mesh)
        if args.swept_out:
            swept["glb_bytes"] = export([obj], args.swept_out)
            swept["glb"] = args.swept_out
            print(f"[OBWIEDNIA] plik={args.swept_out} ({swept['glb_bytes']} B)")
        if args.swept_scene_out:
            if args.tunnel:
                import_glb(args.tunnel, "tunnel")
            everything = [o for o in bpy.data.objects
                          if o.type == "MESH" and o.get("metro_source") != "vehicle"]
            swept["scene_glb_bytes"] = export(everything, args.swept_scene_out)
            swept["scene_glb"] = args.swept_scene_out
            print(f"[OBWIEDNIA] scena={args.swept_scene_out} "
                  f"({swept['scene_glb_bytes']} B, {len(everything)} obiektów)")

    thresholds = list(CP.DEFAULT_THRESHOLDS_M)
    critical = []
    for threshold in thresholds:
        critical.extend(CP.critical_places(records, threshold, document.get("stations", [])))

    report = {
        "tool": "tools/blender/profile_vehicle.py",
        "blender_version": bpy.app.version_string,
        "alignment": document.get("id", ""),
        "profile": args.profile,
        "track_index": args.track,
        "track_offset_m": track_offset,
        "ring_step_m": args.ring_step,
        "step_m": args.step,
        "axis_length_m": round(axis_length, 3),
        "train_length_m": round(train_length, 4),
        "bodies": [b["name"] for b in bodies],
        "source_vertices": sum(len(b["vertices"]) for b in bodies),
        "candidate_vertices": CP.candidate_count(reduced),
        "candidate_bands": sum(len(b["bands"]) for b in reduced),
        "candidate_bucket_m": args.bucket,
        "design_assumptions": {
            "step_m": args.step,
            "refine_step_m": args.refine_step,
            "candidate_bucket_m": args.bucket,
            "frame_window_m": CP.FRAME_WINDOW_M,
            "support_directions": CP.SWEPT_DIRECTIONS,
            "swept_half_range_m": args.swept_half_range,
            "thresholds_m": thresholds,
        },
        "thresholds_m": thresholds,
        "statistics": stats,
        "refinement": refined,
        "coverage_problems": gaps,
        "reduction_check": verification,
        "crosscheck": {
            "at_minimum": check,
            "at_reference": check_reference,
            "reference_measurement": PS.compact(reference),
            "formula_max_slack_mm": PS.FORMULA_MAX_SLACK_MM,
            "formula_guard_at_minimum_mm": PS.FORMULA_GUARD_MM,
            "note": ("wzór na strzałkę cięciwy zakłada łuk okręgu; w pozycji odniesienia "
                     "oś jest do niego bliska i zgodność jest milimetrowa, w globalnym "
                     "minimum krzywizna zmienia się wewnątrz bryły i wzór jest optymistyczny"),
        },
        "swept_envelope": swept,
        "critical_places": critical,
        "profile": [PS.compact(r) for r in records],
        "timing_s": {"scan": round(scan_seconds, 2), "refine": refined["seconds"],
                     "swept": round(swept_seconds, 2),
                     "total": round(time.time() - started, 2)},
        "not_modelled": [
            "zwis czopów skrętu — brak rozstawu w m7-spec.json",
            "przechyłka, ugięcie zawieszenia, tolerancje toru i budowlane tunelu",
            "profil pionowy — T-112 zablokowane, cała scena leży na Z = 0",
            "rozjazdy, odcinki przejściowe i krzywe przejściowe",
        ],
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"[PROFIL] minimum {stats['with_refinement']['min_clearance_m']:+.4f} m "
          f"(z doszlifowaniem), na siatce równomiernej: min {stats['min_clearance_m']:.4f} m, "
          f"P05 {stats['p05_clearance_m']:.4f} m, mediana {stats['median_clearance_m']:.4f} m, "
          f"maks {stats['max_clearance_m']:.4f} m")
    for threshold, count in stats["below_threshold"].items():
        print(f"[PROFIL] pozycji poniżej {threshold} m: {count} z {stats['positions']}")
    for place in critical:
        station = place["nearest_station"]
        print(f"[PROFIL] < {place['threshold_m']:.3f} m: chainage {place['chainage_m']:.1f} m "
              f"({place['positions']} pozycji, min {place['min_clearance_m']:.4f} m, "
              f"{place['bound_by']}) — {station['name']} {station['distance_m']:+.0f} m")
    print(f"[PROFIL] raport={args.out} ({os.path.getsize(args.out)} B), "
          f"czas {report['timing_s']['total']:.1f} s")

    problems = PS.acceptance_problems(gaps, check_reference, check, stats,
                                      outside, args.min_clearance_m, CP.WALL)
    if problems:
        raise SystemExit("BŁĄD: " + "; ".join(problems))


if __name__ == "__main__":
    main()

"""Osadza skład M7 w wygenerowanym tunelu na rzeczywistej osi i MIERZY luz. Headless.

    blender --background --python tools/blender/place_vehicle.py -- \
        --tunnel build/L1_A.glb --vehicle build/M7_shell.glb \
        --centerline data/track/L1_A.json --profile box_double \
        --out build/L1_A_with_M7.glb --report build/L1_A_with_M7.json

`reports/M7-curve-clearance.md` liczy luz **ze wzoru** na strzałkę cięciwy. To narzędzie
liczy go **na siatce**: każdy wierzchołek pojazdu dostaje offsety względem lokalnej ramki
osi i odległość do obrysu profilu. Dwie niezależne drogi do tej samej liczby — jeżeli się
rozjadą, jedna z nich jest błędna i trzeba to zobaczyć, a nie uśrednić.

Skład jest przegubowy, więc każde pudło i każdy mieszek stoi na **własnej cięciwie**.
Ustawienie całych 94 m jako jednej bryły dałoby geometrię, której na torze nie ma.

Same DECYZJE — który tor, gdzie postawić czoło, który wierzchołek jest najgorszy
i czy wynik wolno wypuścić — siedzą w `vehicle_fit.py`. Nie dlatego, że tego
modułu nie da się zaimportować bez Blendera: atrapa `bpy` w
`tools/tests/test_blender_cli.py` importuje go bez przeszkód. Dlatego, że stały
wewnątrz `main()`, za `bpy.ops.object.select_all` i `bpy.ops.import_scene.gltf`,
czyli za granicą, której atrapa nie przekroczy. Tutaj zostaje to, co dotyka
scenki: import GLB, macierze pudeł, chodzenie po siatce i eksport.
"""
import argparse
import json
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement as PL  # noqa: E402
import profiles  # noqa: E402
import sweep as SW  # noqa: E402
import vehicle_fit as VF  # noqa: E402

DEFAULT_RING_STEP_M = 5.0


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Osadzenie M7 w tunelu i pomiar luzu")
    parser.add_argument("--tunnel", required=True)
    parser.add_argument("--vehicle", required=True)
    parser.add_argument("--centerline", required=True)
    parser.add_argument("--profile", default="box_double", choices=list(profiles.PROFILES))
    parser.add_argument("--track", type=int, default=1,
                        help="indeks toru w track_offsets profilu")
    parser.add_argument("--chainage", default="worst",
                        help="chainage czoła składu w metrach albo 'worst'")
    parser.add_argument("--ring-step", type=float, default=DEFAULT_RING_STEP_M)
    parser.add_argument("--out", required=True)
    parser.add_argument("--report")
    parser.add_argument("--min-clearance-m", type=float, default=0.0,
                        help="poniżej tej wartości narzędzie kończy błędem")
    return parser.parse_args(argv)


def load_axis(path, ring_step):
    with open(path, encoding="utf-8") as handle:
        document = json.load(handle)
    points = SW.catmull_rom([tuple(float(c) for c in p) for p in document["points"]], ring_step)
    return document, points, SW.rmf_frames(points), SW.chainages(points)


def import_glb(path, tag):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    added = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if not added:
        raise SystemExit(f"BŁĄD: {path} nie wniósł ani jednego mesha")
    for obj in added:
        obj["metro_source"] = tag
    return added


def local_span(obj):
    xs = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return min(v.x for v in xs), max(v.x for v in xs)


def main():
    args = parse_args()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    document, points, frames, stations = load_axis(args.centerline, args.ring_step)
    offsets = profiles.PROFILES[args.profile].get("track_offsets", [0.0])
    try:
        track_offset = VF.track_offset(offsets, args.track)
    except ValueError as error:
        raise SystemExit(f"BŁĄD: profil {args.profile} {error}")

    tunnel = import_glb(args.tunnel, "tunnel")
    vehicle = import_glb(args.vehicle, "vehicle")
    spans = {obj.name: local_span(obj) for obj in vehicle}
    train_length = max(b for _a, b in spans.values()) - min(a for a, _b in spans.values())

    start, station, radius = VF.resolve_chainage(args.chainage, points, train_length)

    chords = {name: round(b - a, 4) for name, (a, b) in spans.items()}
    order = sorted(vehicle, key=lambda o: spans[o.name][0])
    placements = PL.place_spans(points, stations, start,
                                [spans[o.name] for o in order], track_offset)
    for obj, place in zip(order, placements):
        forward = Vector(place["forward"])
        right = Vector(place["right"])
        up = Vector(place["up"])
        # kolumny bazy: X pojazdu -> styczna, Y pojazdu -> lewo, Z pojazdu -> pion
        basis = Matrix((forward, -right, up)).transposed().to_4x4()
        shift = Matrix.Translation(Vector((-place["local_centre_x_m"], 0.0, 0.0)))
        obj.matrix_world = Matrix.Translation(Vector(place["location"])) @ basis @ shift

    bpy.context.view_layer.update()
    window = (start - 40.0, start + train_length + 40.0)
    ring = profiles.profile_points(args.profile)

    def measured(obj):
        """Luz w każdym wierzchołku bryły — jedyny fragment, który dotyka siatki."""
        for vertex in obj.data.vertices:
            world = obj.matrix_world @ vertex.co
            chainage, lateral, vertical = PL.local_offsets(
                (world.x, world.y, world.z), frames, stations, window)
            yield PL.distance_to_boundary(ring, lateral, vertical), chainage, lateral, vertical

    worst, per_object = VF.clearance_tally((obj.name, measured(obj)) for obj in vehicle)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=args.out, export_format="GLB", use_selection=True)

    report = {
        "alignment": document.get("id", ""),
        "profile": args.profile,
        "track_index": args.track,
        "track_offset_m": track_offset,
        "ring_step_m": args.ring_step,
        "train_length_m": round(train_length, 4),
        "bodies": len(vehicle),
        "start_chainage_m": round(start, 2),
        "centre_chainage_m": round(station, 2),
        "radius_at_centre_m": round(radius, 2) if radius else None,
        "min_clearance_m": round(worst["clearance_m"], 4),
        "min_clearance_at": {"object": worst["object"],
                             "chainage_m": round(worst["chainage_m"], 2),
                             "lateral_m": round(worst["lateral_m"], 4),
                             "vertical_m": round(worst["vertical_m"], 4)},
        "per_object_min_clearance_m": per_object,
        # Rzeczywista cięciwa pudła, nie nominalny podział 94/6: model analityczny
        # w reports/M7-curve-clearance.md używa dłuższej cięciwy nominalnej i przez to
        # jest zachowawczy o kilkadziesiąt milimetrów. Kontrola krzyżowa musi
        # porównywać tę samą wielkość, inaczej mierzy własną niespójność.
        "per_object_chord_m": chords,
        "min_clearance_chord_m": chords.get(worst["object"]),
        "static_clearance_m": profiles.min_clearance(args.profile),
        "glb_bytes": os.path.getsize(args.out),
        "not_modelled": [
            "zwis czopów skrętu — brak rozstawu w m7-spec.json",
            "przechyłka, ugięcie zawieszenia, tolerancje toru",
        ],
    }
    if args.report:
        os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
        with open(args.report, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")

    print(f"[OSADZENIE] tunel={args.tunnel} pojazd={args.vehicle}")
    print(f"[OSADZENIE] skład {train_length:.3f} m w {len(vehicle)} bryłach, tor {args.track} "
          f"(offset {track_offset:+.2f} m)")
    print(f"[OSADZENIE] czoło na chainage {start:.1f} m, środek {station:.1f} m, "
          f"promień w środku {report['radius_at_centre_m']} m")
    print(f"[OSADZENIE] ZMIERZONY minimalny luz: {worst['clearance_m']:.4f} m "
          f"({worst['object']}, chainage {worst['chainage_m']:.1f} m, "
          f"bok {worst['lateral_m']:+.3f} m, wysokość {worst['vertical_m']:.3f} m)")
    print(f"[OSADZENIE] statyczny luz profilu (na prostej): {report['static_clearance_m']:.3f} m")
    for name in sorted(per_object):
        print(f"[OSADZENIE]   {per_object[name]:+.4f} m  {name}")
    print(f"[OSADZENIE] plik={args.out} ({report['glb_bytes']} B)")

    problem = VF.clearance_problem(worst["clearance_m"], args.min_clearance_m)
    if problem:
        raise SystemExit(f"BŁĄD: {problem}")


if __name__ == "__main__":
    main()

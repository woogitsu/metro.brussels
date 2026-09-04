"""Znaczniki wzdłuż osi: hektometry, tabliczki stacyjne, punkty hamowania. Headless.

    blender --background --python tools/blender/detail_markers.py -- \
        --axis data/track/L1_A.json --layout build/L1_A-details.json \
        --profile box_double --out build/L1_A-markers.glb

**Gdzie kończy się dane, a zaczyna założenie.** Kilometraże liczy
`tools/track/detail_layout.py` — wyłącznie z osi i z solvera hamowania, bez ani jednej
decyzji projektowej. Tutaj zostaje to, czego z danych wyprowadzić się nie da: rozmiar
słupka, jego strona i odsunięcie od osi. Te cztery liczby są **jawnymi założeniami**,
wypisywanymi przy każdym uruchomieniu, i nie mają nic wspólnego z wyglądem docelowym —
znacznik jest celowo schematyczny, bo kierunek artystyczny to T-902.

**Założenia są sprawdzane, nie tylko zadeklarowane.** Słupek postawiony byle gdzie
albo wchodzi w skrajnię pojazdu, albo przebija ścianę tunelu. Skrypt liczy oba luzy
i **odmawia zapisu**, gdy któryś wyjdzie ujemny. To jest cała różnica między
„dobrałem ładny odstęp" a „odstęp mieści się między skrajnią a ścianą, i oto o ile".
"""
import argparse
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement as PL  # noqa: E402
import sweep as SW  # noqa: E402
from profiles import profile_points, vehicle_gauge  # noqa: E402

#: Rozpiętość cięciwy, na której stoi słupek. Krótka, żeby znacznik stał stycznie
#: do osi, ale niezerowa — `place_spans` odrzuca cięciwę zerowej długości.
MARKER_CHORD_M = 0.40

#: Wysokość słupka według rodzaju. Trzy różne, żeby rodzaje dało się rozróżnić na
#: renderze BEZ koloru — render kontrolny jest w skali szarości.
DEFAULT_HEIGHTS_M = {"hectometre": 0.60, "brake": 1.00, "station": 1.60}

#: Przekrój słupka: wzdłuż osi x poprzek. Schematyczny.
DEFAULT_POST_M = (0.12, 0.20)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Znaczniki wzdłuż osi")
    parser.add_argument("--axis", required=True)
    parser.add_argument("--layout", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--profile", default="box_double")
    parser.add_argument("--metrics")
    parser.add_argument("--side", choices=("left", "right"), default="right",
                        help="strona osi. ZAŁOŻENIE: brak źródła na stronę oznakowania STIB")
    parser.add_argument("--offset-m", type=float, default=2.10,
                        help="odsunięcie od osi. ZAŁOŻENIE, ale sprawdzane: musi zmieścić "
                             "się między skrajnią pojazdu a ścianą tunelu")
    parser.add_argument("--foot-m", type=float, default=-0.10,
                        help="rzędna podstawy słupka względem osi")
    parser.add_argument("--from-m", type=float, help="początek okna kilometrażu")
    parser.add_argument("--to-m", type=float, help="koniec okna kilometrażu")
    return parser.parse_args(argv)


def select_marks(marks, from_m, to_m):
    """Znaczniki mieszczące się w oknie kilometrażu. Puste okno jest błędem, nie zerem.

    **Po co osobna funkcja.** Wybór okna siedział w `main()` razem z `bpy`, więc nie
    dawał się dotknąć testem — a decyduje o tym, czy render kontrolny w ogóle coś
    pokaże. Bez okna kadr obejmuje 5,4 km i każdy słupek ma 0,03 piksela; scena
    wychodzi pusta, mimo że geometria jest. Zmierzone, nie przewidziane: pierwszy
    przebieg dał dokładnie taki pusty render.

    Puste okno kończy się `SystemExit`, a nie pustą listą, bo skrypt bez ani jednego
    znacznika wyprodukowałby pustą scenę i zapisał ją jako poprawny GLB.
    """
    low = from_m if from_m is not None else float("-inf")
    high = to_m if to_m is not None else float("inf")
    if low > high:
        raise SystemExit(f"BŁĄD: okno {low}–{high} m jest puste")
    selected = [m for m in marks if low <= m["chainage_m"] <= high]
    if not selected:
        raise SystemExit(f"BŁĄD: w oknie {low}–{high} m nie ma ani jednego znacznika")
    return selected, low, high


def side_sign(side):
    """'right' -> +1, 'left' -> -1. Odmawia zamiast zgadywać.

    Wyjęte z `main()` na poziom modułu, bo tam siedziało za `bpy.ops` i żaden test
    nie mógł tego dotknąć — przemiatanie mutacyjne z 03.09.2026 pokazało tu mutację
    ocalałą. Strona osi jest JEDNYM Z CZTERECH założeń projektowych tego modułu
    i sam docstring modułu obiecuje, że są „sprawdzane, nie tylko zadeklarowane".

    Poprzednia wersja, `1.0 if side == "right" else -1.0`, odpowiadała „lewa"
    na KAŻDĄ wartość różną od „right", literówkę włącznie. `argparse` ma tu
    `choices`, więc na drodze z CLI to nie zdarzy się — ale ta funkcja jest
    wołana także z testów i z innych narzędzi, a cicha odpowiedź „lewa"
    postawiłaby wszystkie słupki po drugiej stronie toru.
    """
    if side == "right":
        return 1.0
    if side == "left":
        return -1.0
    raise ValueError(f"strona osi musi być 'right' albo 'left', nie {side!r}")


def clearance_problems(worst_gauge_m, worst_wall_m, profile_name):
    """Lista zarzutów wobec zmierzonych luzów. Pusta lista = słupki wolno wypuścić.

    Dwie bramki tego modułu, wyjęte z `main()` razem, bo odpowiadają na to samo
    pytanie i mają wspólną granicę: luz DOKŁADNIE zerowy jest jeszcze dopuszczony,
    ujemny nie. Zero jest tu granicą, a nie przypadkiem brzegowym — słupek stykający
    się ze skrajnią jeszcze się w niej nie znajduje.

    Kolejność zarzutów jest ustalona, bo trafia do komunikatu błędu.
    """
    problems = []
    if worst_gauge_m < 0.0:
        problems.append(f"słupek wchodzi w skrajnię pojazdu o {-worst_gauge_m:.3f} m — "
                        "zwiększ --offset-m")
    if worst_wall_m < 0.0:
        problems.append(f"słupek przebija ścianę profilu {profile_name} o "
                        f"{-worst_wall_m:.3f} m — zmniejsz --offset-m")
    return problems


def post_mesh(name, placement, lateral_m, foot_m, height_m, thick_m, wide_m):
    """Prostopadłościan stojący stycznie do osi, odsunięty w bok o `lateral_m`."""
    corners = []
    for dx in (-thick_m / 2.0, thick_m / 2.0):
        for dy in (lateral_m - wide_m / 2.0, lateral_m + wide_m / 2.0):
            for dz in (foot_m, foot_m + height_m):
                corners.append(PL.transform_point(placement, (dx + placement["local_centre_x_m"],
                                                              dy, dz)))
    # kolejność wierzchołków: (dx, dy, dz) w pętli wyżej -> indeksy 0..7
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 2, 6, 4),
             (1, 5, 7, 3), (0, 4, 5, 1), (2, 3, 7, 6)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(c) for c in corners], [], [list(f) for f in faces])
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    args = parse_args()
    root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    with open(args.axis if os.path.isabs(args.axis) else os.path.join(root, args.axis),
              encoding="utf-8") as handle:
        axis = json.load(handle)
    with open(args.layout if os.path.isabs(args.layout) else os.path.join(root, args.layout),
              encoding="utf-8") as handle:
        layout = json.load(handle)

    points = [tuple(p) for p in axis["points"]]
    stations = SW.chainages(points)
    profile = profile_points(args.profile)
    gauge = vehicle_gauge()
    sign = side_sign(args.side)
    thick_m, wide_m = DEFAULT_POST_M

    for name in list(bpy.data.objects):
        bpy.data.objects.remove(name, do_unlink=True)

    # Okno kilometrażu. Bez niego render kontrolny kadruje 5,4 km i każdy słupek ma
    # 0,03 piksela — scena wychodzi pusta, mimo że geometria jest. Zmierzone, nie
    # przewidziane: pierwszy przebieg dał dokładnie taki pusty render.
    selected, low, high = select_marks(layout["marks"], args.from_m, args.to_m)

    worst_gauge, worst_wall = float("inf"), float("inf")
    objects, counts = [], {}
    for index, mark in enumerate(selected):
        height = DEFAULT_HEIGHTS_M[mark["kind"]]
        to_gauge, to_wall = PL.marker_clearances(profile, gauge, args.offset_m,
                                                 wide_m, args.foot_m, height)
        worst_gauge = min(worst_gauge, to_gauge)
        worst_wall = min(worst_wall, to_wall)
        centre = mark["chainage_m"]
        span_from = max(0.0, min(stations[-1] - MARKER_CHORD_M, centre - MARKER_CHORD_M / 2.0))
        placements = PL.place_spans(points, stations, span_from,
                                    [(0.0, MARKER_CHORD_M)], 0.0)
        objects.append(post_mesh(f"MARK_{mark['kind']}_{index:04d}", placements[0],
                                 sign * args.offset_m, args.foot_m, height, thick_m, wide_m))
        counts[mark["kind"]] = counts.get(mark["kind"], 0) + 1

    window = ("cała oś" if args.from_m is None and args.to_m is None
              else f"okno {low:.0f}-{high:.0f} m z {len(layout['marks'])} znaczników")
    print(f"[ZNACZNIKI] {axis['id']}: {len(objects)} słupków ({window}) — "
          + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print(f"[ZAŁOŻENIE] strona={args.side} odsunięcie={args.offset_m:.2f} m "
          f"podstawa={args.foot_m:+.2f} m przekrój={thick_m:.2f}x{wide_m:.2f} m")
    print("[ZAŁOŻENIE] wysokości: " + ", ".join(f"{k} {v:.2f} m"
                                                for k, v in sorted(DEFAULT_HEIGHTS_M.items())))
    print(f"[LUZ] do skrajni pojazdu: {worst_gauge:+.3f} m")
    print(f"[LUZ] do ściany tunelu {args.profile}: {worst_wall:+.3f} m")

    problems = clearance_problems(worst_gauge, worst_wall, args.profile)
    if problems:
        raise SystemExit("BŁĄD: " + "; ".join(problems))

    out = args.out if os.path.isabs(args.out) else os.path.join(root, args.out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True)
    print(f"[ZNACZNIKI] zapisano {args.out} ({os.path.getsize(out)} B)")

    if args.metrics:
        metrics = {
            "axis_id": axis["id"], "profile": args.profile, "markers": len(objects),
            "window_from_m": args.from_m, "window_to_m": args.to_m,
            "counts": counts, "side": args.side, "offset_m": args.offset_m,
            "foot_m": args.foot_m, "post_m": list(DEFAULT_POST_M),
            "heights_m": DEFAULT_HEIGHTS_M,
            "clearance_to_gauge_m": round(worst_gauge, 4),
            "clearance_to_wall_m": round(worst_wall, 4),
        }
        mpath = args.metrics if os.path.isabs(args.metrics) else os.path.join(root, args.metrics)
        os.makedirs(os.path.dirname(mpath) or ".", exist_ok=True)
        with open(mpath, "w", encoding="utf-8") as handle:
            json.dump(metrics, handle, ensure_ascii=False, indent=1, sort_keys=True)
            handle.write("\n")
        print(f"[ZNACZNIKI] metryki {args.metrics}")


if __name__ == "__main__":
    main()

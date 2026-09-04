#!/usr/bin/env python3
"""Bryły peronu i komory stacyjnej, zamiatane wzdłuż osi z layoutu T-211.

    blender --background --python tools/blender/station_kit.py -- \
        --axis data/track/L1_A.json --layout build/L1_A-platforms.json \
        --platform-gap-m 0.08 --out build/L1_A-platforms.glb

Druga połowa T-211. Pierwsza (`tools/track/station_layout.py`) policzyła kilometraże
i **dolną granicę odsunięcia krawędzi** — pół szerokości M7 plus strzałkę cięciwy członu
na lokalnym promieniu. Tu z tego powstają bryły.

Podział taki sam, jak w T-011: tamten plik nie ma ani jednej decyzji projektowej,
ten ma **trzy stałe projektowe** — wypisywane przy każdym uruchomieniu:

1. `DESIGN_WALL_SETBACK_M` — o tyle peron cofa się od ściany komory;
2. `DESIGN_EDGE_STRIP_M` — szerokość pasa ostrzegawczego przy krawędzi;
3. `DESIGN_SOLID_FROM_RAIL_HEAD` — peron jest bryłą pełną od poziomu główki szyny
   w górę, bo wymiarów pustki technicznej nie ma w żadnym źródle.

Czwarta liczba, **szczelina peron–pudło**, nie jest stałą tego pliku, tylko
`--platform-gap-m` **bez wartości domyślnej**: R-007 ustalił, że nie podaje jej żadne
publiczne źródło, więc narzędzie bez niej nie buduje. To jest różnica między
„przyjęliśmy" a „nie wiemy i wołający musi powiedzieć".

Wysokość peronu NIE jest tu założeniem: to `floor_height_m` z rejestru M7, bo STIB
pisze, że podłoga M7 jest „à hauteur du quai" (R-007). Czytana z layoutu, żeby nie
było trzeciej kopii tej liczby.
"""
import argparse
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import placement as PL  # noqa: E402
import profiles  # noqa: E402
import sweep as SW  # noqa: E402

#: ZAŁOŻENIE 2. O tyle peron cofa się od ściany komory, żeby nie wchodzić w nią siatką.
DESIGN_WALL_SETBACK_M = 0.10

#: ZAŁOŻENIE 3. Pas ostrzegawczy przy krawędzi — osobna bryła, żeby dało się go
#: sprawdzić i pomalować niezależnie od płyty.
DESIGN_EDGE_STRIP_M = 0.60

#: ZAŁOŻENIE 4. Peron jest pełny od główki szyny w górę.
DESIGN_SOLID_FROM_RAIL_HEAD = True

DESIGN_ASSUMPTIONS = {
    "DESIGN_WALL_SETBACK_M": DESIGN_WALL_SETBACK_M,
    "DESIGN_EDGE_STRIP_M": DESIGN_EDGE_STRIP_M,
    "DESIGN_SOLID_FROM_RAIL_HEAD": DESIGN_SOLID_FROM_RAIL_HEAD,
}


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Bryły peronów wzdłuż osi")
    parser.add_argument("--axis", required=True)
    parser.add_argument("--layout", required=True, help="wyjście tools/track/station_layout.py")
    parser.add_argument("--profile", default="station", choices=list(profiles.PROFILES))
    parser.add_argument("--platform-gap-m", type=float, required=True,
                        help="szczelina peron–pudło; BEZ WARTOŚCI DOMYŚLNEJ (R-007: brak źródła)")
    parser.add_argument("--ring-step-m", type=float, default=SW.DEFAULT_RING_STEP_M)
    parser.add_argument("--out", required=True)
    parser.add_argument("--metrics")
    parser.add_argument("--only-station", help="zbuduj tylko ten peron, po nazwie")
    return parser.parse_args(argv)


def wall_offset_m(profile_name):
    """Odległość ściany komory od osi trasy, z profilu.

    Przez `profile_points`, a nie przez `PROFILES[...]["points"]`: klucza `points`
    nie mają profile okrągłe (`bore_single` opisuje się promieniem i środkiem),
    a `--profile` przyjmuje KAŻDY profil z rejestru. Pierwsza wersja czytała klucz
    wprost i wywracała się na `bore_single` z gołym `KeyError: 'points'` —
    zamiatanie nie zaczynało się w ogóle, więc żaden render tego nie pokazywał.
    """
    return max(abs(x) for x, _z in profiles.profile_points(profile_name))


def slab_sections(gap_m, minimum_offset_m, wall_m, height_m, track_offset_m, side):
    """Przekrój płyty i pasa ostrzegawczego po jednej stronie, w metrach lokalnych.

    Zwraca dwie listy `(y, z)`: płyta i pas. `side` to +1 albo -1.
    """
    inner = track_offset_m + side * (minimum_offset_m + gap_m)
    outer = side * (wall_m - DESIGN_WALL_SETBACK_M)
    if side > 0:
        assert outer > inner, (inner, outer)
        strip_far = min(outer, inner + DESIGN_EDGE_STRIP_M)
    else:
        assert outer < inner, (inner, outer)
        strip_far = max(outer, inner - DESIGN_EDGE_STRIP_M)

    slab = [(inner, 0.0), (outer, 0.0), (outer, height_m), (inner, height_m)]
    strip = [(inner, height_m), (strip_far, height_m),
             (strip_far, height_m + 0.001), (inner, height_m + 0.001)]
    return slab, strip


def selected_platforms(platforms, only_station):
    """Perony do zbudowania. `only_station` puste albo `None` znaczy WSZYSTKIE.

    Wyjęte z `main()` na poziom modułu, bo tam siedziało za `bpy.ops` i żaden test
    nie mógł tego dotknąć — przemiatanie mutacyjne z 03.09.2026 pokazało tu mutację
    ocalałą. Sam filtr nie potrzebuje Blendera i jest bramką: `--only-station`
    z literówką ma dać PUSTĄ listę, a nie po cichu zbudować wszystko.

    Nazwa musi zgadzać się dokładnie. Dopasowanie po fragmencie byłoby gorsze niż
    brak filtru: „Arts" trafiałoby w „Arts-Loi" i w każdą inną stację z tym słowem.
    """
    if not only_station:
        return list(platforms)
    return [p for p in platforms if p["name"] == only_station]


def side_tag(side):
    """'R' dla strony dodatniej, 'L' dla ujemnej — to trafia do NAZWY bryły.

    Też wyjęte z `main()`. Pomyłka tutaj nie wywraca niczego: bryły powstają
    poprawne, tylko z zamienionymi nazwami, więc wszystkie kontrole geometryczne
    przechodzą, a peron prawy nazywa się lewym. Taki błąd wychodzi dopiero wtedy,
    gdy ktoś w scenie szuka peronu po nazwie.

    Zero nie jest stroną i nie ma tu cichej odpowiedzi: wołający podaje +1 albo -1.
    """
    if side > 0:
        return "R"
    if side < 0:
        return "L"
    raise ValueError("strona peronu musi być dodatnia albo ujemna, nie zero")


def sweep_section(points, stations, from_m, to_m, section, step_m):
    """Zamiata przekrój `(y, z)` wzdłuż odcinka osi. Zwraca (wierzchołki, ściany)."""
    ring_at = []
    cursor = from_m
    while cursor < to_m - 1e-9:
        ring_at.append(cursor)
        cursor += step_m
    ring_at.append(to_m)

    verts = []
    for chainage in ring_at:
        position, index, _t = PL.frame_at(points, stations, chainage)
        forward = SW.unit(SW.sub(points[min(index + 1, len(points) - 1)], points[index])) \
            if index + 1 < len(points) else (1.0, 0.0, 0.0)
        right = SW.unit(SW.cross(forward, SW.UP_WORLD))
        up = SW.unit(SW.cross(right, forward))
        for y, z in section:
            verts.append(SW.add(position,
                                SW.add(SW.scale(right, y), SW.scale(up, z))))

    faces = []
    width = len(section)
    for ring in range(len(ring_at) - 1):
        base = ring * width
        nxt = base + width
        for i in range(width):
            j = (i + 1) % width
            faces.append((base + i, base + j, nxt + j, nxt + i))
    # Denka, żeby bryła była zamknięta — inaczej render `_inside` pokazuje wnętrze.
    faces.append(tuple(range(width - 1, -1, -1)))
    faces.append(tuple(range(len(verts) - width, len(verts))))
    return verts, faces


def build_mesh(name, verts, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(v) for v in verts], [], [list(f) for f in faces])
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def main():
    args = parse_args()

    def resolve(path):
        return path if os.path.isabs(path) else os.path.join(ROOT, path)

    with open(resolve(args.axis), encoding="utf-8") as handle:
        axis = json.load(handle)
    with open(resolve(args.layout), encoding="utf-8") as handle:
        layout = json.load(handle)

    points = SW.catmull_rom([tuple(float(c) for c in p) for p in axis["points"]],
                            args.ring_step_m)
    stations = SW.chainages(points)
    wall_m = wall_offset_m(args.profile)
    height_m = layout["platform_height_m"]
    track_offsets = profiles.PROFILES[args.profile]["track_offsets"]

    print(f"[PERON] profil {args.profile}: ściana {wall_m:.2f} m od osi, "
          f"tory {track_offsets}, wysokość peronu {height_m:.2f} m "
          f"({layout['platform_height_status']})")
    print(f"[PERON] szczelina peron–pudło {args.platform_gap_m:.3f} m — "
          "wartość podana jawnie, bo R-007 nie znalazł źródła")
    print(f"[PERON] założenia projektowe ({len(DESIGN_ASSUMPTIONS)}): "
          + ", ".join(f"{k}={v}" for k, v in DESIGN_ASSUMPTIONS.items()))

    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    built = []
    for platform in selected_platforms(layout["platforms"], args.only_station):
        minimum = platform["minimum_edge_offset_m"]
        safe = "".join(c if c.isalnum() else "_" for c in (platform["name"] or "x"))[:24]
        for side, track in ((1.0, max(track_offsets)), (-1.0, min(track_offsets))):
            slab, strip = slab_sections(args.platform_gap_m, minimum, wall_m, height_m,
                                        track, side)
            tag = side_tag(side)
            for kind, section in (("slab", slab), ("edge", strip)):
                verts, faces = sweep_section(points, stations, platform["from_m"],
                                             platform["to_m"], section, args.ring_step_m)
                built.append(build_mesh(f"{safe}_{tag}_{kind}", verts, faces))
        print(f"[PERON] {platform['name']}: {platform['from_m']:.1f}–{platform['to_m']:.1f} m, "
              f"krawędź {minimum + args.platform_gap_m:.4f} m od toru "
              f"(minimum {minimum:.4f} + szczelina {args.platform_gap_m:.3f})")

    if not built:
        raise SystemExit("BŁĄD: nie zbudowano ani jednej bryły — sprawdź --only-station")

    out = resolve(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in built:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = built[0]
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format="GLB")

    vertices = sum(len(o.data.vertices) for o in built)
    faces = sum(len(o.data.polygons) for o in built)
    print(f"[PERON] {len(built)} brył, {vertices} wierzchołków, {faces} ścian -> {out}")

    if args.metrics:
        metrics_path = resolve(args.metrics)
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        with open(metrics_path, "w", encoding="utf-8") as handle:
            json.dump({
                "axis_id": layout["axis_id"],
                "profile": args.profile,
                "platform_gap_m": args.platform_gap_m,
                "platform_height_m": height_m,
                "platform_height_status": layout["platform_height_status"],
                "wall_offset_m": wall_m,
                "objects": len(built),
                "vertices": vertices,
                "faces": faces,
                "design_assumptions": DESIGN_ASSUMPTIONS,
                "not_modelled": layout["not_modelled"],
            }, handle, ensure_ascii=False, indent=1)
            handle.write("\n")
        print(f"[RAPORT] {metrics_path}")


if __name__ == "__main__":
    main()

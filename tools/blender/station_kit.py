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

sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import placement as PL  # noqa: E402
import profiles  # noqa: E402
import station_components as SC  # noqa: E402
import station_sections as SS  # noqa: E402
import sweep as SW  # noqa: E402

# Przekroje i wybór peronów mieszkają w `station_sections`, module BEZ `bpy`.
# Tutaj zostają pod starymi nazwami, bo woła je `main()` i wołały je zawsze —
# ekstrakcja nie ma prawa zmienić ani jednej nazwy, którą widzi reszta pliku.
straight_prism = SS.straight_prism
wall_offset_m = SS.wall_offset_m
slab_sections = SS.slab_sections
selected_platforms = SS.selected_platforms
side_tag = SS.side_tag
sweep_section = SS.sweep_section

# Założenia projektowe 2–4 mieszkają w `station_sections` razem z funkcjami, które
# z nich korzystają. Tu są tylko przepisane pod stare nazwy, bo woła je `main()`
# i wypisuje raport — jedna definicja, dwa miejsca odczytu.
DESIGN_WALL_SETBACK_M = SS.DESIGN_WALL_SETBACK_M
DESIGN_EDGE_STRIP_M = SS.DESIGN_EDGE_STRIP_M
DESIGN_SOLID_FROM_RAIL_HEAD = SS.DESIGN_SOLID_FROM_RAIL_HEAD
DESIGN_ASSUMPTIONS = SS.DESIGN_ASSUMPTIONS

#: Peron i pas ostrzegawczy są z T-211; reszta z T-212 i z `station_components`.
ALL_COMPONENTS = ("platform", "edge") + SC.COMPONENTS


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
    parser.add_argument("--component", action="append", choices=list(ALL_COMPONENTS),
                        help="element do zbudowania; można podać wiele razy. "
                             "Bez tego budowane są wszystkie")
    parser.add_argument("--access-side", type=int, default=1, choices=(1, -1),
                        help="strona osi, po której stoi zespół dostępu")
    args = parser.parse_args(argv)
    args.component = tuple(args.component) if args.component else ALL_COMPONENTS
    return args














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

    ceiling_m = max(z for _x, z in profiles.profile_points(args.profile))
    level = SC.levels(height_m, ceiling_m)
    print(f"[STACJA] poziomy: peron {level['platform_top_m']:.2f} m, strop komory "
          f"{level['chamber_ceiling_m']:.2f} m (w świetle {level['chamber_clear_m']:.2f} m), "
          f"antresola {level['mezzanine_floor_m']:.2f}–{level['mezzanine_ceiling_m']:.2f} m, "
          f"wznoszenie schodów {level['stair_rise_m']:.2f} m")
    print(f"[STACJA] elementy: {', '.join(args.component)}")
    print(f"[STACJA] peron: decyzja właściciela {SC.DESIGN_PLATFORM_LENGTH_M:.1f} m "
          f"(skład M7 94,0 m + 1,0 m zapasu), kontrola R-007: obrys stacji "
          f"{SC.TIGHTEST_STATION_FOOTPRINT_M:.1f} m (Parc)")
    print(f"[STACJA] założenia projektowe T-212 ({len(SC.DESIGN_ASSUMPTIONS)}): "
          + ", ".join(f"{k}={v}" for k, v in SC.DESIGN_ASSUMPTIONS.items()))
    for line in SC.NOT_MODELLED:
        print(f"[STACJA] nie modelowane: {line}")

    built = []
    per_kind = {}
    for platform in selected_platforms(layout["platforms"], args.only_station):
        minimum = platform["minimum_edge_offset_m"]
        safe = "".join(c if c.isalnum() else "_" for c in (platform["name"] or "x"))[:24]
        for side, track in ((1.0, max(track_offsets)), (-1.0, min(track_offsets))):
            slab, strip = slab_sections(args.platform_gap_m, minimum, wall_m, height_m,
                                        track, side)
            tag = side_tag(side)
            for kind, section in (("platform", slab), ("edge", strip)):
                if kind not in args.component:
                    continue
                verts, faces = sweep_section(points, stations, platform["from_m"],
                                             platform["to_m"], section, args.ring_step_m)
                built.append(build_mesh(f"{safe}_{tag}_{kind}", verts, faces))
                per_kind[kind] = per_kind.get(kind, 0) + 1
        print(f"[PERON] {platform['name']}: {platform['from_m']:.1f}–{platform['to_m']:.1f} m, "
              f"krawędź {minimum + args.platform_gap_m:.4f} m od toru "
              f"(minimum {minimum:.4f} + szczelina {args.platform_gap_m:.3f})")

        wanted = tuple(c for c in args.component if c in SC.COMPONENTS)
        if not wanted:
            continue
        # Kontrola z R-007 §5 pkt 3, wykonywana, a nie opisana: peron dłuższy niż
        # najciaśniejszy obrys stacji pakietu A jest na pewno błędny, a zespół dostępu
        # postawiony na takim peronie byłby błędny razem z nim. Generator staje.
        if not SC.platform_fits_the_station(platform["length_m"]):
            raise SystemExit(
                f"BŁĄD: peron {platform['name']} ma {platform['length_m']:.1f} m, "
                f"a najciaśniejszy obrys stacji pakietu A to "
                f"{SC.TIGHTEST_STATION_FOOTPRINT_M:.1f} m (Parc, R-007) — peron dłuższy "
                "niż obrys stacji jest na pewno błędny")
        if platform["length_m"] < SC.DESIGN_MEZZANINE_LENGTH_M + SC.DESIGN_ACCESS_SETBACK_M:
            print(f"[STACJA] {platform['name']}: peron {platform['length_m']:.1f} m jest "
                  f"krótszy niż zespół dostępu "
                  f"({SC.DESIGN_MEZZANINE_LENGTH_M + SC.DESIGN_ACCESS_SETBACK_M:.1f} m) "
                  "— pomijam; peron przycięty do końca osi nie jest stacją typową")
            continue
        for solid in SC.station_solids(platform, level, wall_m, wanted, args.access_side):
            if solid["follows_axis"]:
                verts, faces = sweep_section(points, stations, solid["at_m"],
                                             solid["at_m"] + solid["length_m"],
                                             solid["section"], args.ring_step_m)
            else:
                verts, faces = straight_prism(points, stations, solid["at_m"],
                                              solid["length_m"], solid["section"])
            built.append(build_mesh(f"{safe}_{solid['name']}", verts, faces))
            per_kind[solid["kind"]] = per_kind.get(solid["kind"], 0) + 1

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
    print("[STACJA] brył per element: "
          + ", ".join(f"{k}={v}" for k, v in sorted(per_kind.items())))

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
                "components": list(args.component),
                "objects_per_component": per_kind,
                "access_side": args.access_side,
                "levels": level,
                "design_assumptions": DESIGN_ASSUMPTIONS,
                "design_assumptions_t212": SC.DESIGN_ASSUMPTIONS,
                "not_modelled": list(layout["not_modelled"]) + list(SC.NOT_MODELLED),
            }, handle, ensure_ascii=False, indent=1)
            handle.write("\n")
        print(f"[RAPORT] {metrics_path}")


if __name__ == "__main__":
    main()

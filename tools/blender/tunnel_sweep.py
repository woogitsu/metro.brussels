"""Generuje geometrię tunelu przez zamiatanie profilu wzdłuż osi trasy. Uruchamianie headless.

    blender --background --python tools/blender/tunnel_sweep.py -- \
        --centerline data/track/L1_A.json --profile box_double --out build/L1_A.glb

Cała matematyka siedzi w `sweep.py` i `lod.py`, a manifest, wybór wariantu i bramka
akceptacji w `tunnel_manifest.py` — wszystko czysty Python, testowalny bez Blendera.
Tutaj zostaje budowa siatek bpy, materiał, eksport i wypisanie raportu. Oś jest dzielona na chunki,
których szwy nigdy nie wypadają w obrębie stacji — to warunek późniejszego
streamowania w Godot (T-210, wymaganie 4).

`--chunk-dir` dokłada eksport per chunk plus manifest streamingowy. Chunki jako
osobne obiekty w JEDNYM pliku GLB nie dają streamowania — Godot i tak wczytuje
całe 6,7 km naraz; osobne pliki i indeks chainage dają. Pojedynczy GLB z `--out`
zostaje bez zmian, bo jest wejściem renderów kontrolnych i baseline'u T-012.

Razem z chunkami powstają trzy poziomy szczegółowości (`{id}.glb`, `{id}_lod1.glb`,
`{id}_lod2.glb`) i osobna bryła kolizyjna (`{id}_col.glb`). Manifest mówił dotąd
tylko, CO wczytać; teraz mówi też, w jakiej rozdzielczości i czym testować kolizje,
razem ze ZMIERZONYM błędem każdego poziomu. Matematyka jest w `lod.py`, decyzje
i pomiary w `reports/L1_A-lod.md`.

Dopóki profil pionowy nie ma źródła (T-112 zablokowane brakiem publicznych rzędnych
główki szyny), wynik jest wariantem `flat-preview` i jest tak nazwany w scenie,
w metrykach i w raporcie. `--variant production` jest wtedy odrzucany.
"""
import argparse
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lod as LD  # noqa: E402
import sweep as SW  # noqa: E402
import tunnel_manifest as TM  # noqa: E402
from profiles import PROFILES, profile_points, dimensions, fits_gauge, vehicle_gauge  # noqa: E402


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Zamiatanie profilu tunelu wzdłuż osi")
    parser.add_argument("--centerline", required=True)
    parser.add_argument("--profile", default="box_double", choices=list(PROFILES))
    parser.add_argument("--out", required=True)
    parser.add_argument("--name", default="tunnel")
    parser.add_argument("--ring-step", type=float, default=SW.DEFAULT_RING_STEP_M,
                        help="odstęp pierścieni w metrach; 0 = wierne trzymanie łamanej źródłowej")
    parser.add_argument("--max-chunk-m", type=float, default=SW.DEFAULT_MAX_CHUNK_M)
    parser.add_argument("--station-halo-m", type=float, default=SW.DEFAULT_STATION_HALO_M)
    parser.add_argument("--variant", default="auto", choices=("auto", "flat-preview", "production"))
    parser.add_argument("--metrics", help="ścieżka na metryki JSON")
    parser.add_argument("--chunk-dir",
                        help="katalog na osobny GLB dla każdego chunka plus manifest "
                             "streamingowy; bez tej opcji powstaje tylko pojedynczy --out")
    parser.add_argument("--chunk-manifest",
                        help="ścieżka manifestu streamingowego; domyślnie "
                             "<chunk-dir>/<name>-chunks.json")
    return parser.parse_args(argv)


def export_selected(objects, path):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True)


def drop_object(obj):
    """Usuwa obiekt LOD-a/kolizji ze scenki po eksporcie.

    LOD-y i kolizja NIE mogą trafić do pojedynczego `--out`: to jest wejście renderów
    kontrolnych i baseline'u T-012, a dwie siatki w tym samym miejscu dałyby na
    renderze artefakty z-fightingu. Pojedynczy GLB jest eksportowany przed tym blokiem,
    ale scena zostaje czysta także dlatego, żeby nikt nie dołożył kroku po drodze.
    """
    mesh = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)


def lod_entries(chunk, chunk_id, name_prefix, base_object, chunk_dir, frames, station_m,
                profile, material, uv_scale):
    """Trzy poziomy szczegółowości chunka, każdy w osobnym pliku, z ZMIERZONYM błędem.

    LOD 0 jest tożsamy z siatką bazową i nie jest eksportowany drugi raz — dzieli
    plik z `chunk["file"]`. Pozostałe poziomy to ten sam zestaw ramek z wyrzuconymi
    pierścieniami, więc pierwszy i ostatni pierścień jest wspólny z LOD 0 i szew
    zostaje szczelny także po przełączeniu poziomu.
    """
    first, last = chunk["first_ring"], chunk["last_ring"]
    base_volume = LD.tube_volume_m3(LD.rings_of(frames, profile, chunk["ring_indices"]))
    base_size = [round(v, 4) for v in TM.chunk_size(chunk)]
    entries, meshes = [], []
    for params in LD.LOD_LEVELS:
        level = params["level"]
        if level == 0:
            mesh, path = chunk, os.path.join(chunk_dir, f"{chunk_id}.glb")
        else:
            mesh = LD.lod_chunk(frames, station_m, profile, first, last, level, uv_scale)
            path = os.path.join(chunk_dir, f"{chunk_id}_lod{level}.glb")
            obj = build_object(mesh, level, chunk_id, material,
                               mesh_name=f"{chunk_id}_lod{level}")
            export_selected([obj], path)
            drop_object(obj)
        stats = LD.deviation_stats(frames, profile, station_m, first, last,
                                   mesh["ring_indices"])
        volume = LD.tube_volume_m3(LD.rings_of(frames, profile, mesh["ring_indices"]))
        record = TM.geometry_record(mesh, path)
        record.update({
            "level": level,
            "max_chord_m": params["max_chord_m"],
            "max_sagitta_m": params["max_sagitta_m"],
            "max_deviation_m": round(stats["max_m"], 6),
            "p95_deviation_m": round(stats["p95_m"], 6),
            "median_deviation_m": round(stats["median_m"], 6),
            "mean_deviation_m": round(stats["mean_m"], 6),
            "volume_m3": round(volume, 3),
            "volume_delta_pct": round(100.0 * (volume - base_volume) / base_volume, 4),
            # Rozdzielone znakiem: bbox rzadszego poziomu ma prawo się SKURCZYĆ
            # (wypadł pierścień, który był skrajny), ale nie ma prawa urosnąć —
            # urośnięcie znaczyłoby, że interpolacja wyniosła powierzchnię poza LOD 0.
            "bbox_growth_m": round(max(record["bbox_size_m"][i] - base_size[i]
                                       for i in range(3)), 6),
            "bbox_shrink_m": round(max(base_size[i] - record["bbox_size_m"][i]
                                       for i in range(3)), 6),
            "triangle_share_pct": round(100.0 * len(mesh["faces"]) / len(chunk["faces"]), 2),
        })
        entries.append(record)
        meshes.append(mesh)
    return entries, meshes


def collision_entry(chunk, chunk_id, chunk_dir, frames, station_m, profile, material,
                    uv_scale, track_offsets):
    """Bryła kolizyjna chunka w osobnym pliku, z pomiarem zapasu do ściany i do skrajni.

    Osobny plik, a nie nazwany obiekt w GLB LOD-a, bo kolizja jest JEDNA na chunk,
    a LOD-ów jest trzy: w pliku LOD-a musiałaby albo istnieć trzy razy (marnotrawstwo
    i ryzyko rozjazdu wersji), albo tylko w LOD 0 — a wtedy rezydencja fizyki zależałaby
    od decyzji o rozdzielczości obrazu. Uzasadnienie w `reports/L1_A-lod.md` §4.
    """
    first, last = chunk["first_ring"], chunk["last_ring"]
    solid = LD.collision_solid(frames, station_m, profile, first, last, uv_scale=uv_scale)
    hull = solid["profile"]
    path = os.path.join(chunk_dir, f"{chunk_id}_col.glb")
    obj = build_object(solid, 0, chunk_id, material, mesh_name=f"{chunk_id}_col")
    export_selected([obj], path)
    drop_object(obj)
    columns = len(hull) + 1
    closed, boundary, expected = LD.transversally_closed(solid, columns)
    base_volume = LD.tube_volume_m3(LD.rings_of(frames, profile, chunk["ring_indices"]))
    volume = LD.tube_volume_m3(LD.rings_of(frames, hull, solid["ring_indices"]))
    record = TM.geometry_record(solid, path)
    record.update({
        "role": "wnętrze tunelu — przestrzeń, w której może się poruszać pociąg",
        "derived_from_profile": "box_double",
        "inset_m": solid["inset_m"],
        "max_chord_m": solid["max_chord_m"],
        "max_sagitta_m": solid["max_sagitta_m"],
        "cross_section_m2": round(LD.polygon_area_m2(hull), 4),
        "transversally_closed": bool(closed),
        "boundary_edges": boundary,
        "boundary_edges_expected": expected,
        "end_caps": False,
        "volume_m3": round(volume, 3),
        "volume_share_pct": round(100.0 * volume / base_volume, 3),
        "wall_margin_m": round(LD.wall_margin_m(frames, profile, hull, station_m,
                                                first, last, solid["ring_indices"]), 6),
        "gauge_margin_m": round(LD.gauge_margin_m(hull, vehicle_gauge(), track_offsets), 6),
        "triangle_share_pct": round(100.0 * len(solid["faces"]) / len(chunk["faces"]), 2),
        "normals": "do wnętrza, jak w siatce wizualnej",
        "outward_faces": SW.outward_faces(solid, frames, columns),
        "degenerate_faces": len(SW.degenerate_faces(solid)),
    })
    return record, solid


def chunk_records(chunks, objects, stations, station_slots, name, chunk_dir, frames,
                  station_m, profile, material, uv_scale, track_offsets):
    """Eksportuje każdy chunk do własnych plików i opisuje go wpisem manifestu.

    Nazwy plików są funkcją nazwy wariantu i indeksu chunka, więc są stabilne między
    przebiegami — Godot może je trzymać w ścieżkach scen. Pola schematu 1 (`file`,
    `vertices`, `triangles`, `sha256`) nadal opisują LOD 0, więc `chunks_for_train`
    i `manifest_problems` działają bez zmiany; LOD-y i kolizja dochodzą obok.
    """
    records, lod_meshes, collision_meshes = [], [], []
    for index, (chunk, obj) in enumerate(zip(chunks, objects)):
        chunk_id = f"{name}_c{index:02d}"
        path = os.path.join(chunk_dir, f"{chunk_id}.glb")
        export_selected([obj], path)
        lods, meshes = lod_entries(chunk, chunk_id, name, obj, chunk_dir, frames,
                                   station_m, profile, material, uv_scale)
        collision, solid = collision_entry(chunk, chunk_id, chunk_dir, frames, station_m,
                                           profile, material, uv_scale, track_offsets)
        lod_meshes.append(meshes)
        collision_meshes.append(solid)
        record = TM.geometry_record(chunk, path)
        record.update({
            "id": chunk_id,
            "index": index,
            "length_m": SW.manifest_span(chunk["start_m"], chunk["end_m"])[2],
            "stations": [{"name": stations[s]["name"],
                          "chainage_m": round(float(stations[s]["chainage_m"]), 3)}
                         for s in station_slots[index]],
            "lods": lods,
            "collision": collision,
        })
        records.append(record)
    return records, lod_meshes, collision_meshes


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def load_centerline(path):
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        points = data["points"]
        # Stacje wracają jako rekordy, nie same chainage: manifest streamingowy musi
        # umieć powiedzieć, KTÓRA stacja leży w którym chunku, a nie tylko ile ich jest.
        stations = [{"name": s.get("name") or f"stop{i:02d}",
                     "chainage_m": float(s["chainage_m"])}
                    for i, s in enumerate(data.get("stations", []))]
        vertical = (data.get("vertical") or {}).get("status", "not_modelled")
        identifier = data.get("id", "")
    else:
        points, stations, vertical, identifier = data, [], "not_modelled", ""
    return [tuple(float(c) for c in p) for p in points], stations, vertical, identifier


def build_object(chunk, index, name, material, mesh_name=None):
    # Nazwa obiektu jest tym, co Godot zobaczy w zaimportowanej scenie, więc LOD-y
    # i kolizja dostają nazwę mówiącą, czym są, a nie kolejny „_chunkNN".
    mesh = bpy.data.meshes.new(mesh_name or f"{name}_chunk{index:02d}")
    mesh.from_pydata([tuple(v) for v in chunk["vertices"]], [], [list(f) for f in chunk["faces"]])
    mesh.update()
    layer = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        layer.data[loop.index].uv = chunk["uvs"][loop.vertex_index]
    obj = bpy.data.objects.new(mesh.name, mesh)
    obj.data.materials.append(material)
    bpy.context.collection.objects.link(obj)
    # Świadomie BEZ remove_doubles i bez recalc_face_normals: kolumna szwu jest
    # zdublowana celowo (inaczej UV zawija się na ostatnim czworokącie), a nawinięcie
    # ścian jest policzone w `sweep` i sprawdzone przez `sweep.outward_faces` —
    # przeliczenie normalnych przez Blendera odwróciłoby je na zewnątrz rury.
    return obj


def neutral_material(name="tunnel_neutral"):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = (0.55, 0.55, 0.55, 1.0)
        principled.inputs["Roughness"].default_value = 0.85
    return material


def main():
    args = parse_args()
    clear_scene()
    points, stations, vertical, identifier = load_centerline(args.centerline)
    if not TM.enough_points(points):
        raise SystemExit("BŁĄD: oś trasy musi mieć co najmniej 2 punkty")
    ok, message = fits_gauge(args.profile)
    if not ok:
        raise SystemExit(f"BŁĄD: profil {args.profile} nie mieści skrajni M7 — {message}")

    try:
        plan = TM.variant_plan(args.variant, vertical, args.name)
    except ValueError as err:
        raise SystemExit(f"BŁĄD: {err}")
    variant, name = plan["variant"], plan["scene_name"]

    profile = profile_points(args.profile)
    station_m = [s["chainage_m"] for s in stations]
    result = SW.sweep(points, profile, args.ring_step, station_m, args.max_chunk_m,
                      args.station_halo_m)
    chunks, frames, columns = result["chunks"], result["frames"], result["columns"]

    material = neutral_material()
    objects = [build_object(chunk, i, name, material) for i, chunk in enumerate(chunks)]

    gaps = [SW.chunk_gap_m(a, b, columns) for a, b in zip(chunks, chunks[1:])]
    stretch = [SW.uv_stretch(c, columns) for c in chunks]
    lo, hi = SW.bounding_box(chunks)
    metrics = {
        "id": identifier or name,
        "variant": variant,
        "production_ready": plan["production_ready"],
        "profile": args.profile,
        "profile_size_m": list(dimensions(args.profile)),
        "axis_length_m": round(result["axis_length_m"], 3),
        "source_length_m": round(result["source_length_m"], 3),
        "source_points": result["source_points"],
        "ring_points": result["ring_points"],
        "ring_step_m": args.ring_step,
        "smoothing_max_deviation_m": round(result["max_deviation_m"], 4),
        "frame_twist_deg": round(result["twist_deg"], 6),
        "chunks": len(chunks),
        "chunk_lengths_m": [round(c["length_m"], 2) for c in chunks],
        "chunk_length_sum_m": round(sum(c["length_m"] for c in chunks), 3),
        "chunk_max_gap_m": round(max(gaps), 6) if gaps else 0.0,
        "stations_split": SW.splits_station(result["chunk_bounds"], station_m, args.station_halo_m),
        "vertices": sum(len(c["vertices"]) for c in chunks),
        "faces": sum(len(c["faces"]) for c in chunks),
        "triangles": sum(len(c["faces"]) for c in chunks) * 2,
        "outward_faces": sum(SW.outward_faces(c, frames, columns) for c in chunks),
        "degenerate_faces": sum(len(SW.degenerate_faces(c)) for c in chunks),
        "non_finite_vertices": SW.non_finite(chunks),
        "uv_metres_per_unit": [round(min(s[0] for s in stretch), 4),
                               round(max(s[1] for s in stretch), 4)],
        "bbox_min_m": [round(v, 3) for v in lo],
        "bbox_max_m": [round(v, 3) for v in hi],
        "bbox_size_m": [round(hi[i] - lo[i], 3) for i in range(3)],
    }

    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    export_selected(objects, args.out)
    metrics["glb_bytes"] = os.path.getsize(args.out)

    manifest = None
    if args.chunk_dir:
        os.makedirs(args.chunk_dir, exist_ok=True)
        slots = SW.stations_by_chunk(result["chunk_bounds"], station_m)
        records, lod_meshes, collision_meshes = chunk_records(
            chunks, objects, stations, slots, name, args.chunk_dir, frames,
            result["station_m"], profile, material, SW.UV_METRES_PER_UNIT,
            PROFILES[args.profile].get("track_offsets", [0.0]))
        lod_header = TM.lod_levels_header(records)
        metrics.update(TM.lod_metrics(records, lod_meshes, collision_meshes, frames,
                                   columns, len(profile) + 1))
        manifest_path = args.chunk_manifest or os.path.join(args.chunk_dir, f"{name}-chunks.json")
        manifest = {
            "schema_version": SW.CHUNK_MANIFEST_SCHEMA_VERSION,
            "generator": "tools/blender/tunnel_sweep.py",
            "id": metrics["id"],
            "name": name,
            "variant": variant,
            "production_ready": metrics["production_ready"],
            "profile": args.profile,
            "profile_size_m": metrics["profile_size_m"],
            "units": "m",
            "up_axis": "Z",
            "axis_length_m": metrics["axis_length_m"],
            "chunk_count": len(records),
            "chunk_length_sum_m": metrics["chunk_length_sum_m"],
            "station_count": len(stations),
            "totals": {"vertices": metrics["vertices"], "faces": metrics["faces"],
                       "triangles": metrics["triangles"]},
            "bbox_min_m": metrics["bbox_min_m"],
            "bbox_max_m": metrics["bbox_max_m"],
            # ZAŁOŻENIE PROJEKTOWE, nie dana o sieci: okno z docs/01-architecture.md.
            # Manifest je tylko zapisuje — predykat przyjmuje dowolne wartości, bo
            # budżet pamięci jest decyzją silnika, nie faktem o metrze brukselskim.
            "streaming": {
                "default_ahead_m": SW.DEFAULT_STREAM_AHEAD_M,
                "default_behind_m": SW.DEFAULT_STREAM_BEHIND_M,
                "source": "docs/01-architecture.md — okno 600 m przed składem, 300 m za nim",
                "status": "design_assumption",
                "predicate": "tools/blender/sweep.py: chunks_for_train / streaming_plan",
                "volatile_keys": list(SW.VOLATILE_CHUNK_KEYS),
                "lod_predicate": "tools/blender/lod.py: lod_plan",
                "collision_predicate": "tools/blender/lod.py: collision_plan",
                "collision_radius_m": LD.COLLISION_RADIUS_M,
                "collision_radius_status": "design_assumption",
                "collision_radius_source": "długość składu M7 94,0 m (data/vehicle/m7-spec.json) "
                                           "z zapasem po obu stronach",
            },
            "lod_levels": lod_header,
            "chunks": records,
        }
        problems = SW.manifest_problems(manifest) + LD.lod_problems(manifest)
        if problems:
            raise SystemExit("BŁĄD: manifest niespójny — " + "; ".join(problems))
        os.makedirs(os.path.dirname(manifest_path) or ".", exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        # do metryk trafiają tylko nazwy plików, nie ścieżki: metryki są porównywane
        # między przebiegami i nie mogą zależeć od katalogu wyjściowego
        metrics["chunk_files"] = [r["file"] for r in records]

    if args.metrics:
        os.makedirs(os.path.dirname(args.metrics) or ".", exist_ok=True)
        with open(args.metrics, "w", encoding="utf-8") as handle:
            json.dump(metrics, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")

    print(f"[RAPORT] plik={args.out} wariant={variant}")
    print(f"[RAPORT] profil={args.profile} ({metrics['profile_size_m'][0]:.2f} x "
          f"{metrics['profile_size_m'][1]:.2f} m) punkty_osi={metrics['source_points']} "
          f"pierscienie={metrics['ring_points']}")
    print(f"[RAPORT] dlugosc_osi={metrics['axis_length_m']:.2f} m "
          f"(zrodlo {metrics['source_length_m']:.2f} m, wygladzenie "
          f"{metrics['smoothing_max_deviation_m']:.4f} m)")
    print(f"[RAPORT] chunki={metrics['chunks']} suma={metrics['chunk_length_sum_m']:.3f} m "
          f"max_szczelina={metrics['chunk_max_gap_m']*1000:.3f} mm "
          f"stacje_przeciete={len(metrics['stations_split'])}")
    print(f"[RAPORT] wierzcholki={metrics['vertices']} sciany={metrics['faces']} "
          f"trojkaty={metrics['triangles']}")
    print(f"[RAPORT] normalne_na_zewnatrz={metrics['outward_faces']} "
          f"zdegenerowane={metrics['degenerate_faces']} "
          f"nieskonczone={metrics['non_finite_vertices']} "
          f"skret_ramki={metrics['frame_twist_deg']:.4f} st.")
    print(f"[RAPORT] UV m/jednostke: {metrics['uv_metres_per_unit'][0]:.3f} .. "
          f"{metrics['uv_metres_per_unit'][1]:.3f}")
    print(f"[RAPORT] bbox_m: X={metrics['bbox_size_m'][0]:.1f} Y={metrics['bbox_size_m'][1]:.1f} "
          f"Z={metrics['bbox_size_m'][2]:.1f}")
    if manifest:
        print(f"[CHUNKI] katalog={args.chunk_dir} manifest={manifest_path} "
              f"pliki={manifest['chunk_count']} "
              f"bajty={sum(r['bytes'] for r in manifest['chunks'])}")
        for record in manifest["chunks"]:
            names = ", ".join(s["name"] for s in record["stations"]) or "-"
            print(f"[CHUNKI] {record['id']} {record['start_m']:8.2f}..{record['end_m']:8.2f} m "
                  f"({record['length_m']:6.2f} m) trojkaty={record['triangles']:5d} "
                  f"bajty={record['bytes']:7d} stacje: {names}")
        for entry in manifest["lod_levels"]:
            print(f"[LOD] poziom {entry['level']}: cieciwa<={entry['max_chord_m']:.0f} m "
                  f"strzalka<={entry['max_sagitta_m']:.2f} m -> trojkaty={entry['triangles']:5d} "
                  f"({entry['triangle_share_pct']:5.1f}%) blad_max={entry['max_deviation_m']:.4f} m "
                  f"mediana={entry['median_deviation_m']:.4f} m "
                  f"prog={entry['switch_distance_m']:.0f} m")
        print(f"[LOD] szczelina na szwie: max {metrics['lod_max_gap_any_m']*1000:.3f} mm "
              f"po wszystkich parach poziomow {sorted(metrics['lod_max_gap_m'])}")
        print(f"[KOLIZJA] trojkaty={metrics['collision_triangles']} "
              f"({100.0*metrics['collision_triangles']/metrics['triangles']:.1f}% siatki "
              f"wizualnej) zamknieta_poprzecznie={metrics['collision_closed']} "
              f"szczelina={metrics['collision_max_gap_m']*1000:.3f} mm")
        print(f"[KOLIZJA] zapas do sciany min {metrics['collision_min_wall_margin_m']:.4f} m, "
              f"zapas do skrajni M7 min {metrics['collision_min_gauge_margin_m']:.4f} m, "
              f"objetosc {sum(c['collision']['volume_m3'] for c in manifest['chunks']):.1f} m3 "
              f"({manifest['chunks'][0]['collision']['volume_share_pct']:.1f}% swiatla tunelu)")

    problems = TM.geometry_problems(metrics, manifest)
    if problems:
        raise SystemExit("BŁĄD: " + "; ".join(problems))
    print("[RAPORT] kontrole geometryczne: OK")


if __name__ == "__main__":
    main()

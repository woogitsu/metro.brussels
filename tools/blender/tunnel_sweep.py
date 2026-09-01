"""Generuje geometrię tunelu przez zamiatanie profilu wzdłuż osi trasy. Uruchamianie headless.

    blender --background --python tools/blender/tunnel_sweep.py -- \
        --centerline data/track/L1_A.json --profile box_double --out build/L1_A.glb

Cała matematyka siedzi w `sweep.py` (czysty Python, testowalny bez Blendera); tutaj
zostaje budowa siatek bpy, materiał, eksport i raport. Oś jest dzielona na chunki,
których szwy nigdy nie wypadają w obrębie stacji — to warunek późniejszego
streamowania w Godot (T-210, wymaganie 4).

`--chunk-dir` dokłada eksport per chunk plus manifest streamingowy. Chunki jako
osobne obiekty w JEDNYM pliku GLB nie dają streamowania — Godot i tak wczytuje
całe 6,7 km naraz; osobne pliki i indeks chainage dają. Pojedynczy GLB z `--out`
zostaje bez zmian, bo jest wejściem renderów kontrolnych i baseline'u T-012.

Dopóki profil pionowy nie ma źródła (T-112 zablokowane brakiem publicznych rzędnych
główki szyny), wynik jest wariantem `flat-preview` i jest tak nazwany w scenie,
w metrykach i w raporcie. `--variant production` jest wtedy odrzucany.
"""
import argparse
import hashlib
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweep as SW  # noqa: E402
from profiles import PROFILES, profile_points, dimensions, fits_gauge  # noqa: E402

MAX_GAP_M = 0.001
MAX_TWIST_DEG = 5.0


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


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def export_selected(objects, path):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True)


def chunk_records(chunks, objects, stations, station_slots, name, chunk_dir):
    """Eksportuje każdy chunk do własnego GLB i opisuje go wpisem manifestu.

    Nazwy plików są funkcją nazwy wariantu i indeksu chunka, więc są stabilne między
    przebiegami — Godot może je trzymać w ścieżkach scen. Liczniki wierzchołków
    i trójkątów pochodzą z generatora, nie z GLB: eksporter glTF rozszczepia
    wierzchołki na szwach UV, więc liczba w pliku jest większa i nie sumuje się
    do metryk. `geometry_sha256` odpowiada na pytanie „czy siatka się zmieniła"
    wtedy, gdy `sha256` pliku i tak nie jest odtwarzalny.
    """
    records = []
    for index, (chunk, obj) in enumerate(zip(chunks, objects)):
        chunk_id = f"{name}_c{index:02d}"
        path = os.path.join(chunk_dir, f"{chunk_id}.glb")
        export_selected([obj], path)
        lo, hi = SW.bounding_box([chunk])
        records.append({
            "id": chunk_id,
            "index": index,
            "file": os.path.basename(path),
            "start_m": round(chunk["start_m"], 6),
            "end_m": round(chunk["end_m"], 6),
            "length_m": round(chunk["length_m"], 6),
            "rings": chunk["last_ring"] - chunk["first_ring"] + 1,
            "bbox_min_m": [round(v, 4) for v in lo],
            "bbox_max_m": [round(v, 4) for v in hi],
            "bbox_size_m": [round(hi[i] - lo[i], 4) for i in range(3)],
            "vertices": len(chunk["vertices"]),
            "faces": len(chunk["faces"]),
            "triangles": len(chunk["faces"]) * 2,
            "geometry_sha256": SW.chunk_geometry_sha256(chunk),
            "sha256": sha256_file(path),
            "bytes": os.path.getsize(path),
            "stations": [{"name": stations[s]["name"],
                          "chainage_m": round(float(stations[s]["chainage_m"]), 3)}
                         for s in station_slots[index]],
        })
    return records


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


def build_object(chunk, index, name, material):
    mesh = bpy.data.meshes.new(f"{name}_chunk{index:02d}")
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
    if len(points) < 2:
        raise SystemExit("BŁĄD: oś trasy musi mieć co najmniej 2 punkty")
    ok, message = fits_gauge(args.profile)
    if not ok:
        raise SystemExit(f"BŁĄD: profil {args.profile} nie mieści skrajni M7 — {message}")

    variant = args.variant
    if variant == "auto":
        variant = "production" if vertical == "modelled" else "flat-preview"
    if variant == "production" and vertical != "modelled":
        raise SystemExit("BŁĄD: oś nie ma profilu pionowego (T-112), wariant production niedozwolony")
    name = args.name if variant == "production" else f"{args.name}_flat_preview"

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
        "production_ready": variant == "production",
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
        records = chunk_records(chunks, objects, stations, slots, name, args.chunk_dir)
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
            },
            "chunks": records,
        }
        problems = SW.manifest_problems(manifest)
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

    problems = []
    if metrics["vertices"] == 0 or metrics["faces"] == 0:
        problems.append("geometria pusta")
    if metrics["chunk_max_gap_m"] > MAX_GAP_M:
        problems.append(f"szczelina na szwie {metrics['chunk_max_gap_m']*1000:.3f} mm > 1 mm")
    if metrics["stations_split"]:
        problems.append(f"szew chunka przecina stację: {metrics['stations_split']}")
    if metrics["outward_faces"]:
        problems.append(f"{metrics['outward_faces']} ścian z normalną na zewnątrz")
    if metrics["degenerate_faces"]:
        problems.append(f"{metrics['degenerate_faces']} zdegenerowanych ścian")
    if metrics["non_finite_vertices"]:
        problems.append(f"{metrics['non_finite_vertices']} wierzchołków NaN/Inf")
    if metrics["frame_twist_deg"] > MAX_TWIST_DEG:
        problems.append(f"skręt ramki {metrics['frame_twist_deg']:.2f} st.")
    if abs(metrics["chunk_length_sum_m"] - metrics["axis_length_m"]) > 0.01:
        problems.append("suma długości chunków nie zgadza się z chainage")
    if problems:
        raise SystemExit("BŁĄD: " + "; ".join(problems))
    print("[RAPORT] kontrole geometryczne: OK")


if __name__ == "__main__":
    main()

"""Manifest i bramka akceptacji generatora tunelu — czysty Python, bez Blendera.

Wydzielone z `tunnel_sweep.py`, który importuje `bpy` i przez to nie daje się
zaimportować w `tools/tests/test_all.py`. Funkcje mieszkały tam obok kodu bpy,
więc żaden test nie mógł ich dotknąć: przemiatanie mutacji z 03.09.2026 pokazało
35 mutacji w `tunnel_sweep.py` i 35 ocalałych — 100 %, bo nie istniała droga,
którą test mógłby je zabić.

Tu są tylko rzeczy, które biorą na wejściu słowniki i listy: opis siatki chunka,
nagłówek poziomów LOD, metryki zbiorcze, wybór wariantu i **lista problemów
geometrycznych**, na której generator kończy pracę błędem. `tunnel_sweep.py`
zostaje z budową siatek bpy, materiałem i eksportem.

Matematyka siatek jest w `sweep.py` i `lod.py`; ten moduł ich używa, ale sam
niczego nie liczy geometrycznie — składa i ocenia.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lod as LD  # noqa: E402
import sweep as SW  # noqa: E402

MAX_GAP_M = 0.001
MAX_TWIST_DEG = 5.0
MIN_AXIS_POINTS = 2
CHUNK_LENGTH_TOLERANCE_M = 0.01


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def geometry_record(chunk, path):
    """Wspólny opis dowolnej siatki chunka: LOD-a, kolizji i siatki bazowej.

    Liczniki wierzchołków i trójkątów pochodzą z generatora, nie z GLB: eksporter
    glTF rozszczepia wierzchołki na szwach UV, więc liczba w pliku jest większa
    i nie sumuje się do metryk. `geometry_sha256` odpowiada na pytanie „czy siatka
    się zmieniła" wtedy, gdy `sha256` pliku i tak nie jest odtwarzalny.
    """
    lo, hi = SW.bounding_box([chunk])
    start_m, end_m, _length_m = SW.manifest_span(chunk["start_m"], chunk["end_m"])
    return {
        "file": os.path.basename(path),
        "start_m": start_m,
        "end_m": end_m,
        "rings": len(chunk["ring_indices"]),
        "vertices": len(chunk["vertices"]),
        "faces": len(chunk["faces"]),
        "triangles": len(chunk["faces"]) * 2,
        "bbox_min_m": [round(v, 4) for v in lo],
        "bbox_max_m": [round(v, 4) for v in hi],
        "bbox_size_m": [round(hi[i] - lo[i], 4) for i in range(3)],
        "geometry_sha256": SW.chunk_geometry_sha256(chunk),
        "sha256": sha256_file(path),
        "bytes": os.path.getsize(path),
    }

def chunk_size(chunk):
    lo, hi = SW.bounding_box([chunk])
    return [hi[i] - lo[i] for i in range(3)]


def lod_levels_header(records):
    """Nagłówek manifestu: co robi każdy poziom, ile kosztuje i od jakiej odległości wolno.

    Próg odległości NIE jest zgadnięty i NIE jest specyfikacją: liczy się ze
    ZMIERZONEGO na tym pakiecie największego odchylenia poziomu i z jawnego budżetu
    błędu ekranowego (`lod.switch_distance_m`). Docelowe progi mają wyjść z pomiaru
    wydajności na rzeczywistym sprzęcie w T-400 — do tego czasu wpis jest oznaczony
    `design_assumption`, tak jak okno streamowania.
    """
    out = []
    for params in LD.LOD_LEVELS:
        level = params["level"]
        entries = [l for chunk in records for l in chunk["lods"] if l["level"] == level]
        worst = max(e["max_deviation_m"] for e in entries)
        triangles = sum(e["triangles"] for e in entries)
        base = sum(l["triangles"] for chunk in records for l in chunk["lods"]
                   if l["level"] == 0)
        out.append({
            "level": level,
            "max_chord_m": params["max_chord_m"],
            "max_sagitta_m": params["max_sagitta_m"],
            "purpose": params["purpose"],
            "triangles": triangles,
            "triangle_share_pct": round(100.0 * triangles / base, 2),
            "max_deviation_m": round(worst, 6),
            "median_deviation_m": round(
                sorted(e["median_deviation_m"] for e in entries)[len(entries) // 2], 6),
            "switch_distance_m": round(LD.switch_distance_m(worst), 1),
            "switch_distance_source":
                "poziom bazowy — obowiązuje wszędzie poniżej progu LOD 1" if level == 0 else
                f"odległość, na której zmierzone odchylenie {worst:.4f} m schodzi poniżej "
                f"{LD.PIXEL_BUDGET_TOLERANCE_PX:.0f} px przy {LD.PIXEL_BUDGET_WIDTH_PX} px "
                f"i obiektywie {LD.PIXEL_BUDGET_LENS_MM:.0f} mm na matrycy "
                f"{LD.PIXEL_BUDGET_SENSOR_MM:.0f} mm",
            "status": "design_assumption",
        })
    return out


def lod_metrics(records, lod_meshes, collision_meshes, frames, columns, collision_columns):
    """Metryki generatora dla LOD-ów i kolizji, z kontrolą szwów W KAŻDYM poziomie.

    Szew jest sprawdzany osobno w każdym poziomie ORAZ między różnymi poziomami
    sąsiednich chunków: streaming ma prawo trzymać chunk `n` w LOD 0 i chunk `n+1`
    w LOD 2, więc dziura mogłaby się otworzyć dokładnie na tej parze.
    """
    levels = [p["level"] for p in LD.LOD_LEVELS]
    gaps = {}
    for low in levels:
        for high in levels:
            worst = 0.0
            for previous, current in zip(lod_meshes, lod_meshes[1:]):
                worst = max(worst, SW.chunk_gap_m(previous[low], current[high], columns))
            gaps[f"{low}->{high}"] = round(worst, 9)
    collision_gap = 0.0
    for previous, current in zip(collision_meshes, collision_meshes[1:]):
        collision_gap = max(collision_gap,
                            SW.chunk_gap_m(previous, current, collision_columns))
    return {
        "lod_level_ids": levels,
        "lod_max_bbox_growth_m": round(max(l["bbox_growth_m"] for chunk in records
                                           for l in chunk["lods"]), 6),
        "lod_max_bbox_shrink_m": round(max(l["bbox_shrink_m"] for chunk in records
                                           for l in chunk["lods"]), 6),
        "lod_triangles": {str(level): sum(l["triangles"] for chunk in records
                                          for l in chunk["lods"] if l["level"] == level)
                          for level in levels},
        "lod_max_deviation_m": {str(level): round(max(l["max_deviation_m"] for chunk in records
                                                      for l in chunk["lods"]
                                                      if l["level"] == level), 6)
                                for level in levels},
        "lod_outward_faces": sum(SW.outward_faces(mesh, frames, columns)
                                 for meshes in lod_meshes for mesh in meshes),
        "lod_degenerate_faces": sum(len(SW.degenerate_faces(mesh))
                                    for meshes in lod_meshes for mesh in meshes),
        "lod_non_finite_vertices": SW.non_finite([m for ms in lod_meshes for m in ms]),
        "lod_max_gap_m": {key: value for key, value in sorted(gaps.items())},
        "lod_max_gap_any_m": round(max(gaps.values()), 9),
        "collision_triangles": sum(c["collision"]["triangles"] for c in records),
        "collision_max_gap_m": round(collision_gap, 9),
        "collision_outward_faces": sum(c["collision"]["outward_faces"] for c in records),
        "collision_degenerate_faces": sum(c["collision"]["degenerate_faces"] for c in records),
        "collision_non_finite_vertices": SW.non_finite(collision_meshes),
        "collision_min_wall_margin_m": round(min(c["collision"]["wall_margin_m"]
                                                 for c in records), 6),
        "collision_min_gauge_margin_m": round(min(c["collision"]["gauge_margin_m"]
                                                  for c in records), 6),
        "collision_closed": all(c["collision"]["transversally_closed"] for c in records),
    }




def enough_points(points):
    """Czy oś w ogóle da się zamiatać.

    Jeden punkt nie wyznacza kierunku, zero punktów nie wyznacza niczego —
    `sweep` dostałby wtedy pustą listę ramek i wyprodukował pustą scenę
    z zerowym kodem wyjścia. To jest dokładnie ten przypadek, przed którym
    ostrzega CLAUDE.md §5.
    """
    return len(points) >= MIN_AXIS_POINTS


def variant_plan(requested, vertical, name):
    """Wariant wyniku, jego status produkcyjny i nazwa sceny — jedna decyzja.

    Dopóki oś nie ma modelowanego profilu pionowego (T-112 zablokowane brakiem
    publicznych rzędnych główki szyny), wynik jest `flat-preview` i **nosi to
    w nazwie**: scena, metryki i raport mają mówić jednym głosem, żeby płaska
    zajawka nigdy nie trafiła nikomu do rąk jako geometria docelowa.

    `production` na osi bez profilu pionowego jest odrzucane, a nie po cichu
    obniżane — jawne żądanie zasługuje na jawną odmowę.
    """
    if requested == "auto":
        requested = "production" if vertical == "modelled" else "flat-preview"
    if requested == "production" and vertical != "modelled":
        raise ValueError(
            "oś nie ma profilu pionowego (T-112), wariant production niedozwolony")
    return {
        "variant": requested,
        "production_ready": requested == "production",
        "scene_name": name if requested == "production" else f"{name}_flat_preview",
    }


def geometry_problems(metrics, manifest):
    """Lista powodów, dla których tego wyniku NIE wolno wypuścić. Pusta = przeszedł.

    Bramka akceptacji generatora. Rozdzielona na dwie części, bo kontrole LOD-ów
    i bryły kolizyjnej mają sens tylko wtedy, gdy `--chunk-dir` w ogóle je
    wyprodukował; kontrole siatki bazowej obowiązują zawsze.
    """
    problems = []
    if manifest:
        if metrics["lod_outward_faces"]:
            problems.append(f"{metrics['lod_outward_faces']} ścian LOD-a z normalną na zewnątrz")
        if metrics["lod_degenerate_faces"] or metrics["lod_non_finite_vertices"]:
            problems.append("LOD ma ściany zdegenerowane albo wierzchołki NaN/Inf")
        if metrics["lod_max_gap_any_m"] > MAX_GAP_M:
            problems.append(f"szczelina między LOD-ami {metrics['lod_max_gap_any_m']*1000:.3f} mm")
        if metrics["collision_max_gap_m"] > MAX_GAP_M:
            problems.append(f"szczelina kolizji {metrics['collision_max_gap_m']*1000:.3f} mm")
        if metrics["collision_outward_faces"] or metrics["collision_degenerate_faces"] \
                or metrics["collision_non_finite_vertices"]:
            problems.append("bryła kolizyjna ma złe normalne, degeneracje albo NaN/Inf")
        if not metrics["collision_closed"]:
            problems.append("bryła kolizyjna nie jest zamknięta poprzecznie")
        if metrics["collision_min_wall_margin_m"] < 0.0:
            problems.append("bryła kolizyjna wystaje poza światło tunelu")
        if metrics["collision_min_gauge_margin_m"] <= 0.0:
            problems.append("bryła kolizyjna nie mieści skrajni M7")
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
    if abs(metrics["chunk_length_sum_m"] - metrics["axis_length_m"]) > CHUNK_LENGTH_TOLERANCE_M:
        problems.append("suma długości chunków nie zgadza się z chainage")
    return problems

#!/usr/bin/env python3
"""Buduje oś poziomą pakietu A (Gare de l'Ouest – Merode) z geometrii STIB.

    python3 tools/track/build_alignment.py --package A --out data/track/L1_A.json

Reguła źródeł z `docs/07-open-data-research.md`:

1. bazowy przebieg pochodzi z **oficjalnego STIB** (`ACTU_LIGNES_BRUTES`);
2. kotwice stacyjne z `ACTU_STOPS` tego samego datasetu, w kolejności `StopOrder`;
3. rozbieżności wobec innych źródeł są **liczone i raportowane**, nigdy uśredniane.

Oś jest wyłącznie **pozioma**. Współrzędna Z jest zerowym placeholderem, żeby plik
przechodził walidator; profil pionowy należy do T-112 i jest dziś zablokowany
brakiem publicznych rzędnych (patrz raport T-901).
"""
import argparse
import json
import math
import os
import sys
import unicodedata
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import provenance as P  # noqa: E402
import shapefile as S  # noqa: E402

ARCHIVE_PREFIX = "2603_STIB_MIVB_Network/"
LINES_LAYER = "ACTU_LIGNES_BRUTES"
STOPS_LAYER = "ACTU_STOPS"
SOURCE_CRS = "EPSG:31370"
UNIFORM_STEP_M = 15.0
STATION_OFFSET_WARN_M = 5.0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Oś pozioma pakietu budowy z geometrii STIB")
    parser.add_argument("--package", default="A", help="identyfikator pakietu z lines.json")
    parser.add_argument("--line-code", default="001m", help="LineCode w shapefile STIB")
    parser.add_argument("--variante", type=int, default=1)
    parser.add_argument("--shapes", default=os.path.join("data", "raw", "stib_shapefiles.zip"))
    parser.add_argument("--out", default=os.path.join("data", "track", "L1_A.json"))
    parser.add_argument("--provenance", help="domyślnie <out> z sufiksem .provenance.json")
    parser.add_argument("--manifest", default=os.path.join("data", "network", "shapes-manifest.json"))
    parser.add_argument("--network", default=os.path.join("data", "network", "lines.json"))
    parser.add_argument("--step", type=float, default=UNIFORM_STEP_M,
                        help="krok równomiernego próbkowania osi w metrach")
    parser.add_argument("--svg", help="opcjonalny podgląd 2D w SVG")
    return parser.parse_args(argv)


# --- geometria ----------------------------------------------------------------

def polyline_length(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def cumulative(points):
    out = [0.0]
    for a, b in zip(points, points[1:]):
        out.append(out[-1] + math.dist(a, b))
    return out


def project_on_polyline(points, target):
    """Zwraca (chainage, odległość_od_osi, indeks_segmentu) dla najbliższego rzutu."""
    best = (0.0, float("inf"), 0)
    chain = cumulative(points)
    for index, (a, b) in enumerate(zip(points, points[1:])):
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        seg = dx * dx + dy * dy
        if seg <= 0.0:
            continue
        t = ((target[0] - ax) * dx + (target[1] - ay) * dy) / seg
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        px, py = ax + t * dx, ay + t * dy
        offset = math.dist((px, py), target)
        if offset < best[1]:
            best = (chain[index] + t * math.sqrt(seg), offset, index)
    return best


def slice_polyline(points, start_chainage, end_chainage):
    """Wycina fragment polilinii między dwoma kilometrażami, z interpolacją końców."""
    chain = cumulative(points)
    out = []
    for index in range(len(points) - 1):
        c0, c1 = chain[index], chain[index + 1]
        if c1 < start_chainage or c0 > end_chainage:
            continue
        a, b = points[index], points[index + 1]
        if c0 < start_chainage <= c1:
            out.append((_lerp(a, b, (start_chainage - c0) / (c1 - c0)), "interpolated_cut"))
        if start_chainage <= c0 <= end_chainage:
            out.append((a, f"source_vertex:{index}"))
        if c0 <= end_chainage < c1:
            out.append((_lerp(a, b, (end_chainage - c0) / (c1 - c0)), "interpolated_cut"))
    if not out or math.dist(out[-1][0], points[-1]) > 1e-9:
        pass
    deduped = []
    for point, origin in out:
        if deduped and math.dist(deduped[-1][0], point) < 1e-6:
            continue
        deduped.append((point, origin))
    return deduped


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def point_at(points, chainage):
    """Punkt na polilinii w zadanym kilometrażu."""
    chain = cumulative(points)
    if chainage <= 0:
        return points[0]
    if chainage >= chain[-1]:
        return points[-1]
    for index in range(len(points) - 1):
        if chain[index] <= chainage <= chain[index + 1]:
            span = chain[index + 1] - chain[index]
            if span <= 0:
                return points[index]
            return _lerp(points[index], points[index + 1], (chainage - chain[index]) / span)
    return points[-1]


def resample_uniform(points, step, anchors_chainage):
    """Próbkuje oś równomiernie i wymusza dokładne trafienie w kotwice stacyjne.

    Wierzchołki źródłowe mają odstępy od 0,42 m, przez co trzy kolejne punkty
    opisują promień rzędu metrów — to szum digitalizacji trasy, nie łuk toru.
    Równomierne próbkowanie jest **jawną transformacją**; odchyłka od źródła jest
    mierzona i raportowana, a nie ukrywana.
    """
    total = cumulative(points)[-1]
    anchor_marks = sorted(round(c, 6) for c in anchors_chainage)
    count = max(2, int(math.ceil(total / step)))
    candidates = [round(min(total, i * total / count), 6) for i in range(count + 1)]
    # próbka bliżej niż pół kroku od kotwicy tworzyłaby duplikat; kotwica ma pierwszeństwo
    keep = [c for c in candidates
            if all(abs(c - a) > step / 2.0 for a in anchor_marks)]
    ordered = sorted(set(keep) | set(anchor_marks))
    return [(point_at(points, c), "station_anchor" if round(c, 6) in
             {round(a, 6) for a in anchors_chainage} else "resampled_uniform")
            for c in ordered]


def max_deviation(sampled, source):
    """Największe odsunięcie próbkowanej osi od polilinii źródłowej."""
    return max(project_on_polyline(source, point)[1] for point in sampled)


def radius_stats(points):
    radii = []
    for i in range(1, len(points) - 1):
        radii.append(_radius(points[i - 1], points[i], points[i + 1]))
    finite = sorted(r for r in radii if r != float("inf"))
    if not finite:
        return {"min_m": None, "p05_m": None, "median_m": None}
    return {"min_m": round(finite[0], 1),
            "p05_m": round(finite[int(0.05 * (len(finite) - 1))], 1),
            "median_m": round(finite[len(finite) // 2], 1)}


def _radius(a, b, c):
    (x1, y1), (x2, y2), (x3, y3) = a, b, c
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        return float("inf")
    ux = ((x1 ** 2 + y1 ** 2) * (y2 - y3) + (x2 ** 2 + y2 ** 2) * (y3 - y1) +
          (x3 ** 2 + y3 ** 2) * (y1 - y2)) / d
    uy = ((x1 ** 2 + y1 ** 2) * (x3 - x2) + (x2 ** 2 + y2 ** 2) * (x1 - x3) +
          (x3 ** 2 + y3 ** 2) * (x2 - x1)) / d
    return math.dist((ux, uy), (x1, y1))


# --- wejście ------------------------------------------------------------------

def load_layers(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        prefix = ARCHIVE_PREFIX if any(n.startswith(ARCHIVE_PREFIX) for n in names) else ""
        lines = S.read_pair(archive.read(f"{prefix}{LINES_LAYER}.shp"),
                            archive.read(f"{prefix}{LINES_LAYER}.dbf"))
        stops = S.read_pair(archive.read(f"{prefix}{STOPS_LAYER}.shp"),
                            archive.read(f"{prefix}{STOPS_LAYER}.dbf"))
        prj = S.read_prj(archive.read(f"{prefix}{LINES_LAYER}.prj").decode("utf-8"))
    return lines, stops, prj


def pick_line(lines, line_code, variante):
    matches = [r for r in lines
               if str(r["attributes"].get("LineCode")) == line_code
               and r["attributes"].get("Variante") == variante]
    if not matches:
        raise SystemExit(f"BŁĄD: brak polilinii LineCode={line_code} Variante={variante}")
    if len(matches) > 1:
        raise SystemExit(f"BŁĄD: {len(matches)} polilinii dla {line_code}/{variante}; oczekiwano jednej")
    geometry = matches[0]["geometry"]
    if len(geometry["parts"]) != 1:
        raise SystemExit(f"BŁĄD: polilinia ma {len(geometry['parts'])} części; oczekiwano jednej")
    return matches[0]


def package_bounds(network_path, package_id):
    with open(network_path, encoding="utf-8") as handle:
        network = json.load(handle)
    package = next((p for p in network["build_packages"] if p["id"] == package_id), None)
    if package is None:
        raise SystemExit(f"BŁĄD: pakiet {package_id} nie istnieje w lines.json")
    return package


def normalise(name):
    text = unicodedata.normalize("NFKD", str(name))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper().replace("'", "'").replace("-", " ").replace(".", "")
    return " ".join(text.split())


def pick_stops(stops, line_code, variante, first_name, last_name):
    rows = [r["attributes"] for r in stops
            if str(r["attributes"].get("LineCode")) == line_code
            and r["attributes"].get("Variante") == variante]
    if not rows:
        raise SystemExit(f"BŁĄD: brak przystanków dla {line_code}/{variante}")
    directions = sorted({r.get("LineDir") for r in rows})
    chosen = None
    for direction in directions:
        ordered = sorted([r for r in rows if r.get("LineDir") == direction],
                         key=lambda r: r["StopOrder"])
        names = [normalise(r["Descr_fr"]) for r in ordered]
        if normalise(first_name) in names and normalise(last_name) in names:
            start = names.index(normalise(first_name))
            end = names.index(normalise(last_name))
            if start < end:
                chosen = ordered[start:end + 1]
                break
            # wariant powrotny: ta sama trasa w odwrotnej kolejności StopOrder
            chosen = list(reversed(ordered[end:start + 1]))
            break
    if chosen is None:
        raise SystemExit(f"BŁĄD: nie znaleziono odcinka {first_name} -> {last_name} "
                         f"w kierunkach {directions}")
    return chosen


# --- budowa -------------------------------------------------------------------

def build(args):
    shapes_path = args.shapes if os.path.isabs(args.shapes) else os.path.join(ROOT, args.shapes)
    if not os.path.isfile(shapes_path):
        raise SystemExit(f"BŁĄD: brak {shapes_path}; uruchom tools/track/fetch_stib_shapes.py")
    network_path = args.network if os.path.isabs(args.network) else os.path.join(ROOT, args.network)

    lines, stops, prj = load_layers(shapes_path)
    if prj["name"] != "Belge_Lambert_1972":
        raise SystemExit(f"BŁĄD: nieoczekiwany CRS źródła: {prj['name']}")
    package = package_bounds(network_path, args.package)
    record = pick_line(lines, args.line_code, args.variante)
    points = record["geometry"]["points"]
    station_rows = pick_stops(stops, args.line_code, args.variante, package["from"], package["to"])
    if len(station_rows) != package["stations"]:
        raise SystemExit(f"BŁĄD: pakiet {args.package} deklaruje {package['stations']} stacji, "
                         f"dane STIB dają {len(station_rows)}")

    anchors = []
    for row in station_rows:
        target = (float(row["Coord_X"]), float(row["Coord_Y"]))
        chainage, offset, segment = project_on_polyline(points, target)
        anchors.append({"row": row, "chainage": chainage, "offset": offset, "segment": segment,
                        "source_point": target})
    if [a["chainage"] for a in anchors] != sorted(a["chainage"] for a in anchors):
        raise SystemExit("BŁĄD: rzuty stacji nie są monotoniczne wzdłuż osi")

    start, end = anchors[0]["chainage"], anchors[-1]["chainage"]
    sliced = [p for p, _ in slice_polyline(points, start, end)]
    anchor_local = [a["chainage"] - start for a in anchors]
    resampled = resample_uniform(sliced, args.step, anchor_local)
    deviation = max_deviation([p for p, _ in resampled], sliced)
    radii_source = radius_stats(sliced)
    radii_final = radius_stats([p for p, _ in resampled])

    origin = resampled[0][0]
    local = [((p[0] - origin[0], p[1] - origin[1]), tag) for p, tag in resampled]
    chain_local = cumulative([p for p, _ in local])

    out_points = [[round(p[0], 3), round(p[1], 3), 0.0] for p, _ in local]
    point_sources = [{"index": i, "origin": tag, "source_class": "derived",
                      "derived_from": "official_stib"}
                     for i, (_p, tag) in enumerate(local)]

    with open(network_path, encoding="utf-8") as handle:
        network_doc = json.load(handle)
    canonical = {}
    for line in network_doc["lines"]:
        for stop in line["stops"]:
            canonical[normalise(stop.split("|")[0])] = stop

    stations = []
    for anchor in anchors:
        row = anchor["row"]
        key = normalise(row["Descr_fr"])
        if key not in canonical:
            raise SystemExit(f"BŁĄD: stacja STIB '{row['Descr_fr']}' nie ma odpowiednika "
                             f"w data/network/lines.json — rozbieżność wymaga decyzji")
        stations.append({
            "name": canonical[key],
            "name_fr": _display_name(row["Descr_fr"]),
            "name_nl": _display_name(row["Descr_nl"]),
            "stop_id": row["Stop_id"],
            "stop_order": row["StopOrder"],
            "chainage_m": round(anchor["chainage"] - start, 2),
            "offset_from_axis_m": round(anchor["offset"], 3),
            "source_class": "official_stib",
            "depth_m": None,
            "interpolated": False,
        })

    document = {
        "$comment": "Oś pozioma pakietu A z oficjalnej geometrii STIB. Generowane przez "
                    "tools/track/build_alignment.py — nie edytować ręcznie.",
        "id": f"L1_{args.package}",
        "schema_version": 1,
        "crs": f"lokalny układ metryczny; origin = kotwica {package['from']} w {SOURCE_CRS}",
        "source_crs": SOURCE_CRS,
        "origin_source_crs": [round(origin[0], 3), round(origin[1], 3)],
        "vertical": {
            "status": "not_modelled",
            "note": "Z = 0 to placeholder. Profil pionowy należy do T-112 i jest zablokowany "
                    "brakiem publicznych rzędnych główki szyny (raport T-901).",
        },
        "package": {"id": package["id"], "name": package["name"],
                    "from": package["from"], "to": package["to"],
                    "declared_stations": package["stations"]},
        "length_m": round(chain_local[-1], 2),
        "points": out_points,
        "stations": stations,
        "speed_limits": [],
    }
    gaps = [math.dist(a, b) for a, b in zip([p for p, _ in local], [p for p, _ in local][1:])]
    stats = {
        "source_vertices_in_slice": len(sliced),
        "output_points": len(local),
        "station_anchor_points": sum(1 for s in point_sources if s["origin"] == "station_anchor"),
        "max_point_gap_m": round(max(gaps), 3),
        "min_point_gap_m": round(min(gaps), 3),
        "resample_step_m": args.step,
        "resample_max_deviation_m": round(deviation, 3),
        "radius_source_polyline": radii_source,
        "radius_after_resample": radii_final,
        "station_offset_max_m": round(max(a["offset"] for a in anchors), 3),
        "station_offset_median_m": round(sorted(a["offset"] for a in anchors)[len(anchors) // 2], 3),
        "trunk_length_m": round(chain_local[-1], 2),
        "source_slice_length_m": round(polyline_length(sliced), 2),
    }
    return document, point_sources, stats, anchors, record, points, lines, stops, prj


def _display_name(value):
    text = " ".join(str(value).split())
    return text.title().replace("'", "'") if text.isupper() else text


# --- kontrola krzyżowa --------------------------------------------------------

def crosscheck_internal(lines, stops, base_code, variante, package, base_points, start, end):
    """Porównanie z drugą linią pnia i z drugim wariantem tej samej linii — oba STIB."""
    base_slice = [p for p, _ in slice_polyline(base_points, start, end)]
    results = []
    for code, var in (("001m", 2), ("005m", 1), ("005m", 2)):
        if code == base_code and var == variante:
            continue
        try:
            other = pick_line(lines, code, var)
            other_stops = pick_stops(stops, code, var, package["from"], package["to"])
        except SystemExit as exc:
            results.append({"line_code": code, "variante": var, "status": "niedostępne", "reason": str(exc)})
            continue
        other_points = other["geometry"]["points"]
        first = project_on_polyline(other_points, (float(other_stops[0]["Coord_X"]),
                                                   float(other_stops[0]["Coord_Y"])))[0]
        last = project_on_polyline(other_points, (float(other_stops[-1]["Coord_X"]),
                                                 float(other_stops[-1]["Coord_Y"])))[0]
        # wariant powrotny biegnie w przeciwną stronę, więc kilometraże trzeba uporządkować
        low, high = (first, last) if first <= last else (last, first)
        other_slice = [p for p, _ in slice_polyline(other_points, low, high)]
        if not other_slice:
            results.append({"line_code": code, "variante": var, "status": "pusty wycinek",
                            "reason": f"kilometraże {low:.1f}..{high:.1f} nie dały punktów"})
            continue
        deviations = sorted(project_on_polyline(other_slice, point)[1] for point in base_slice)
        results.append({
            "line_code": code, "variante": var, "status": "ok",
            "length_m": round(polyline_length(other_slice), 2),
            "points": len(other_slice),
            "deviation_median_m": round(deviations[len(deviations) // 2], 3),
            "deviation_p95_m": round(deviations[int(0.95 * (len(deviations) - 1))], 3),
            "deviation_max_m": round(deviations[-1], 3),
        })
    return results


def write_svg(path, document, anchors, origin, extra_layers=None):
    """Prosty podgląd 2D: oś, kotwice stacyjne i warstwy kontrolne."""
    points = [(p[0], p[1]) for p in document["points"]]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    for layer in (extra_layers or {}).values():
        xs.extend(p[0] for p in layer)
        ys.extend(p[1] for p in layer)
    pad = 80.0
    min_x, max_x, min_y, max_y = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    width, height = 1400, 700
    scale = min(width / (max_x - min_x), height / (max_y - min_y))

    def to_px(point):
        return ((point[0] - min_x) * scale, height - (point[1] - min_y) * scale)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#12161c"/>']
    colours = {"stib_005m_v1": "#f6a90b", "stib_001m_v2": "#7a7f88", "urbis_metro": "#2f6f4f"}
    for name, layer in (extra_layers or {}).items():
        path_data = " ".join(("M" if i == 0 else "L") + f"{to_px(p)[0]:.1f},{to_px(p)[1]:.1f}"
                             for i, p in enumerate(layer))
        parts.append(f'<path d="{path_data}" fill="none" stroke="{colours.get(name, "#888")}" '
                     f'stroke-width="1.4" stroke-dasharray="5,4" opacity="0.9"/>')
    axis = " ".join(("M" if i == 0 else "L") + f"{to_px(p)[0]:.1f},{to_px(p)[1]:.1f}"
                    for i, p in enumerate(points))
    parts.append(f'<path d="{axis}" fill="none" stroke="#b02d8c" stroke-width="2.6"/>')
    for station in document["stations"]:
        index = min(range(len(document["points"])),
                    key=lambda i: abs(_chainage_at(document["points"], i) - station["chainage_m"]))
        px, py = to_px(points[index])
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="#ffffff"/>')
        parts.append(f'<text x="{px + 7:.1f}" y="{py - 7:.1f}" fill="#dfe3e8" '
                     f'font-family="monospace" font-size="11">{station["name"]}</text>')
    legend = [("oś STIB 001m v1 (bazowa)", "#b02d8c")] + \
             [(name, colours.get(name, "#888")) for name in (extra_layers or {})]
    for i, (label, colour) in enumerate(legend):
        parts.append(f'<rect x="16" y="{16 + i * 18}" width="22" height="4" fill="{colour}"/>')
        parts.append(f'<text x="46" y="{23 + i * 18}" fill="#dfe3e8" font-family="monospace" '
                     f'font-size="12">{label}</text>')
    parts.append(f'<text x="16" y="{height - 16}" fill="#8b929c" font-family="monospace" '
                 f'font-size="12">{document["id"]}: {document["length_m"]:.0f} m, '
                 f'{len(document["stations"])} stacji, origin {origin}</text>')
    parts.append("</svg>")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(parts) + "\n")


def _chainage_at(points, index):
    total = 0.0
    for i in range(index):
        total += math.dist(points[i][:2], points[i + 1][:2])
    return total


def main(argv=None):
    args = parse_args(argv)
    document, point_sources, stats, anchors, record, full_points, lines, stops, prj = build(args)

    package = package_bounds(args.network if os.path.isabs(args.network)
                             else os.path.join(ROOT, args.network), args.package)
    start, end = anchors[0]["chainage"], anchors[-1]["chainage"]
    crosscheck = crosscheck_internal(lines, stops, args.line_code, args.variante,
                                     package, full_points, start, end)

    out_path = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    prov_path = args.provenance or out_path.replace(".json", ".provenance.json")
    manifest_path = args.manifest if os.path.isabs(args.manifest) else os.path.join(ROOT, args.manifest)

    feed = {}
    if os.path.isfile(manifest_path):
        with open(manifest_path, encoding="utf-8") as handle:
            manifest = json.load(handle)
        feed = {"source_id": manifest.get("source_id"),
                "content_sha256": manifest.get("content_sha256"),
                "retrieved_at": manifest.get("retrieved_at"),
                "dataset_validity": manifest.get("dataset_validity")}
    document["source"] = feed

    provenance = {
        "$comment": "Provenance osi pakietu A. Każdy punkt ma klasę źródła; rozbieżności "
                    "między źródłami są raportowane, nie uśredniane.",
        "alignment_id": document["id"],
        "generator": "tools/track/build_alignment.py",
        "parser_version": "alignment/v1",
        "source": feed,
        "source_dataset": f"STIB/MIVB shape-files, {LINES_LAYER} + {STOPS_LAYER}",
        "source_crs": SOURCE_CRS,
        "source_prj": prj,
        "selection": {"line_code": args.line_code, "variante": args.variante,
                      "package": args.package, "line_dir": anchors[0]["row"].get("LineDir")},
        "transformations": [
            {"step": "project_stations", "note": "rzut prostopadły kotwic stacyjnych na polilinię"},
            {"step": "slice", "note": "wycięcie między pierwszą a ostatnią kotwicą, końce interpolowane"},
            {"step": "resample_uniform", "step_m": args.step,
             "max_deviation_m": stats["resample_max_deviation_m"],
             "note": "równomierne próbkowanie osi; wierzchołki źródłowe mają odstępy od 0,42 m "
                     "i generują pozorne promienie rzędu metrów, co jest szumem digitalizacji "
                     "trasy, a nie łukiem toru"},
            {"step": "translate_origin", "origin_source_crs": document["origin_source_crs"],
             "note": "przesunięcie do lokalnego układu metrycznego, bez obrotu i skalowania"},
        ],
        "statistics": stats,
        "points": point_sources,
        "crosscheck": crosscheck,
        "not_derived": [
            "profil pionowy i głębokości — brak publicznych rzędnych (T-901)",
            "układ tor-po-torze — dataset zawiera trasy handlowe, nie osie torów",
            "geometria rozjazdów, w tym węzeł Beekkant",
            "promienie łuków jako fakt konstrukcyjny — polilinia jest reprezentacją trasy",
        ],
    }

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as handle:
        handle.write(P.canonical_json(document))
    with open(prov_path, "wb") as handle:
        handle.write(P.canonical_json(provenance))

    print(f"[RAPORT] pakiet {package['id']} ({package['name']}): {package['from']} -> {package['to']}")
    print(f"[RAPORT] źródło: {LINES_LAYER} {args.line_code} var {args.variante}, CRS {prj['name']}")
    print(f"[RAPORT] długość osi: {document['length_m']:.2f} m")
    print(f"[RAPORT] punktów: {len(document['points'])} "
          f"(wierzchołków źródłowych w wycinku: {stats['source_vertices_in_slice']})")
    print(f"[RAPORT] odstęp punktów: {stats['min_point_gap_m']:.2f}..{stats['max_point_gap_m']:.2f} m, "
          f"krok {stats['resample_step_m']:.1f} m")
    print(f"[RAPORT] odchyłka próbkowania od źródła: maks. {stats['resample_max_deviation_m']:.3f} m")
    print(f"[RAPORT] promień: źródło min {stats['radius_source_polyline']['min_m']} m / "
          f"P05 {stats['radius_source_polyline']['p05_m']} m, "
          f"po próbkowaniu min {stats['radius_after_resample']['min_m']} m / "
          f"P05 {stats['radius_after_resample']['p05_m']} m")
    print(f"[RAPORT] stacje: {len(document['stations'])}, "
          f"odsunięcie kotwic od osi: mediana {stats['station_offset_median_m']:.3f} m, "
          f"maks. {stats['station_offset_max_m']:.3f} m")
    for station in document["stations"]:
        print(f"[STACJA] {station['chainage_m']:>8.1f} m  {station['name']:<22} "
              f"offset={station['offset_from_axis_m']:.2f} m")
    for entry in crosscheck:
        if entry["status"] != "ok":
            print(f"[KONTROLA] {entry['line_code']} v{entry['variante']}: {entry['status']}")
            continue
        print(f"[KONTROLA] {entry['line_code']} v{entry['variante']}: "
              f"dł. {entry['length_m']:.1f} m, odchyłka mediana {entry['deviation_median_m']:.2f} m, "
              f"P95 {entry['deviation_p95_m']:.2f} m, maks. {entry['deviation_max_m']:.2f} m")
    if stats["station_offset_max_m"] > STATION_OFFSET_WARN_M:
        print(f"[UWAGA] kotwica stacyjna oddalona o {stats['station_offset_max_m']:.2f} m od osi")
    print(f"[RAPORT] {out_path}")
    print(f"[RAPORT] {prov_path}")

    if args.svg:
        svg_path = args.svg if os.path.isabs(args.svg) else os.path.join(ROOT, args.svg)
        extra = {}
        for entry in crosscheck:
            if entry["status"] != "ok" or entry["line_code"] != "005m" or entry["variante"] != 1:
                continue
            other = pick_line(lines, "005m", 1)["geometry"]["points"]
            other_stops = pick_stops(stops, "005m", 1, package["from"], package["to"])
            first = project_on_polyline(other, (float(other_stops[0]["Coord_X"]),
                                                float(other_stops[0]["Coord_Y"])))[0]
            last = project_on_polyline(other, (float(other_stops[-1]["Coord_X"]),
                                               float(other_stops[-1]["Coord_Y"])))[0]
            origin = document["origin_source_crs"]
            extra["stib_005m_v1"] = [(p[0] - origin[0], p[1] - origin[1])
                                     for p, _ in slice_polyline(other, first, last)]
        write_svg(svg_path, document, anchors, document["origin_source_crs"], extra)
        print(f"[RAPORT] {svg_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

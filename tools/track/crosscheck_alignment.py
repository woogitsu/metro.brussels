#!/usr/bin/env python3
"""Porównuje gotową oś z niezależnymi źródłami: UrbIS/Brussels Mobility i OSM.

    python3 tools/track/crosscheck_alignment.py --alignment data/track/L1_A.json \
        --out build/L1_A-crosscheck.json

Rozbieżności są **liczone i zapisywane**, nigdy uśredniane ani „poprawiane".
Niedostępność źródła jest wynikiem, a nie powodem do pominięcia kontroli: zapisujemy
kod HTTP i komunikat, żeby raport mówił, czego nie dało się sprawdzić i dlaczego.

UrbIS `Metro` to **poligony** tuneli (MT) i stacji (MS), a nie oś toru, więc jedyną
sensowną miarą jest, jaka część osi mieści się w tych poligonach.
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import crs as CRS  # noqa: E402
import provenance as P  # noqa: E402

URBIS_URL = ("https://data.mobility.brussels/geoserver/ogc/features/v1/collections/"
             "bm_public_transport%3AMetro/items?limit=10000&f=application/json")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSM_COVERAGE_RADIUS_M = 50.0
# Bbox zapytania Overpassa liczony jest z **samej osi**, a nie wpisany na stałe:
# stały bbox pnia (50.835,4.310,50.855,4.400) nie obejmuje ani Stockel, ani Erasme,
# ani Roi Baudouin, więc dla pakietów B–F dawałby ciche zero pokrycia.
OVERPASS_BBOX_MARGIN_M = 300.0
OVERPASS_TEMPLATE = """[out:json][timeout:60];
(
  way["railway"="subway"](%.5f,%.5f,%.5f,%.5f);
);
out geom;
"""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Kontrola krzyżowa osi wobec UrbIS i OSM")
    parser.add_argument("--alignment", default=os.path.join("data", "track", "L1_A.json"))
    parser.add_argument("--out", default=os.path.join("build", "L1_A-crosscheck.json"))
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--skip-osm", action="store_true")
    parser.add_argument("--osm-file", help="lokalny snapshot OSM zamiast zapytania sieciowego "
                                           "(Overpass albo tools/track/fetch_osm_routes.py)")
    parser.add_argument("--urbis-file", help="lokalny snapshot warstwy UrbIS Metro")
    parser.add_argument("--skip-urbis", action="store_true")
    return parser.parse_args(argv)


def load_alignment(path):
    with open(path, encoding="utf-8") as handle:
        document = json.load(handle)
    origin = document["origin_source_crs"]
    points = [(p[0] + origin[0], p[1] + origin[1]) for p in document["points"]]
    return document, points


def point_in_ring(point, ring):
    inside = False
    x, y = point
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y):
            xin = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < xin:
                inside = not inside
    return inside


def polygon_rings(geometry):
    kind = geometry.get("type")
    if kind == "Polygon":
        return [geometry["coordinates"][0]]
    if kind == "MultiPolygon":
        return [poly[0] for poly in geometry["coordinates"]]
    return []


def chainage_ranges(points, flags):
    """Przedziały kilometrażu, na których flaga jest prawdziwa.

    Sama liczba trafionych punktów nie mówi generatorowi tunelu, **gdzie** ma
    przestać budować rurę; przedziały mówią.
    """
    chain = [0.0]
    for a, b in zip(points, points[1:]):
        chain.append(chain[-1] + math.dist(a, b))
    ranges = []
    start = None
    for index, flag in enumerate(flags):
        if flag and start is None:
            start = chain[index]
        elif not flag and start is not None:
            ranges.append([round(start, 1), round(chain[index - 1], 1)])
            start = None
    if start is not None:
        ranges.append([round(start, 1), round(chain[-1], 1)])
    return ranges


def crosscheck_urbis(points, timeout, local_file=None):
    if local_file:
        with open(local_file, "rb") as handle:
            content = handle.read()
        final_url = f"file:{os.path.basename(local_file)}"
    else:
        try:
            content, final_url, _headers = P.fetch_url(URBIS_URL, expected_format="json",
                                                       timeout=timeout)
        except Exception as exc:
            return {"status": "niedostępne", "reason": str(exc), "url": P.sanitize_url(URBIS_URL)}
    payload = json.loads(content.decode("utf-8"))
    features = payload.get("features", [])
    rings = {"MT": [], "MS": []}
    for feature in features:
        properties = feature.get("properties") or {}
        kind = properties.get("type")
        if kind in rings:
            for ring in polygon_rings(feature.get("geometry") or {}):
                rings[kind].append({
                    "ring": [CRS.wgs84_to_lambert72(x, y) for x, y, *_ in ring],
                    "niveau": str(properties.get("niveau")),
                    "name": properties.get("name_fr") or properties.get("name_nl"),
                })

    counts = {"MT": 0, "MS": 0, "outside": 0}
    # `niveau` jest jedynym polem w tym datasecie, które w ogóle mówi coś o poziomie
    # względem terenu, a `sources.json` zapisuje wprost, że **wymaga interpretacji**.
    # Liczymy je, bo 12 z 87 poligonów tuneli ma `0` i pokrywa się z odcinkami znanymi
    # z biegu po powierzchni — ale wniosku „to jest naziemne" tu nie stawiamy.
    niveau_hits = {}
    named_niveau0 = {}
    niveau0_flags = []
    for point in points:
        hit = next((r for r in rings["MT"] if point_in_ring(point, r["ring"])), None)
        kind = "MT"
        if hit is None:
            hit = next((r for r in rings["MS"] if point_in_ring(point, r["ring"])), None)
            kind = "MS"
        if hit is None:
            counts["outside"] += 1
            niveau0_flags.append(False)
            continue
        counts[kind] += 1
        key = f"{kind}/niveau={hit['niveau']}"
        niveau_hits[key] = niveau_hits.get(key, 0) + 1
        niveau0_flags.append(hit["niveau"] == "0")
        if hit["niveau"] == "0":
            named_niveau0[hit["name"]] = named_niveau0.get(hit["name"], 0) + 1
    total = max(1, len(points))
    niveau0 = sum(v for k, v in niveau_hits.items() if k.endswith("niveau=0"))
    return {
        "status": "ok",
        "url": P.sanitize_url(final_url),
        "features": len(features),
        "polygons": {k: len(v) for k, v in rings.items()},
        "points_checked": len(points),
        "inside_tunnel_pct": round(100.0 * counts["MT"] / total, 1),
        "inside_station_pct": round(100.0 * counts["MS"] / total, 1),
        "outside_pct": round(100.0 * counts["outside"] / total, 1),
        "by_niveau": dict(sorted(niveau_hits.items())),
        "niveau0_points": niveau0,
        "niveau0_pct": round(100.0 * niveau0 / total, 1),
        "niveau0_polygons": dict(sorted(named_niveau0.items())),
        "niveau0_chainage_ranges_m": chainage_ranges(points, niveau0_flags),
        "note": "UrbIS Metro to poligony tuneli i stacji, nie oś toru; miarą jest pokrycie, "
                "nie odchyłka liniowa. Znaczenie pola 'niveau' nie jest potwierdzone przez "
                "dataset — liczba punktów w poligonach z niveau=0 jest wejściem dla R-005, "
                "nie stwierdzeniem, że odcinek biegnie po powierzchni.",
    }


def overpass_query(points, margin_m=OVERPASS_BBOX_MARGIN_M):
    """Zapytanie Overpassa z bboxem policzonym z osi, w WGS84."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    corners = [(min(xs) - margin_m, min(ys) - margin_m), (max(xs) + margin_m, max(ys) + margin_m)]
    lonlat = [CRS.lambert72_to_wgs84(x, y) for x, y in corners]
    return OVERPASS_TEMPLATE % (lonlat[0][1], lonlat[0][0], lonlat[1][1], lonlat[1][0])


def crosscheck_osm(points, timeout, local_file=None):
    query = overpass_query(points)
    if local_file:
        with open(local_file, "rb") as handle:
            content = handle.read()
        payload = json.loads(content.decode("utf-8"))
        return _osm_metrics(points, payload, {
            "status": "ok",
            "source": "snapshot lokalny",
            "file": os.path.basename(local_file),
            "file_sha256": P.sha256_bytes(content),
            "osm_timestamp": (payload.get("osm3s") or {}).get("timestamp_osm_base"),
            "routes": payload.get("routes"),
            "attribution": "© OpenStreetMap contributors, ODbL 1.0",
        })
    try:
        content, final_url, _headers = P.fetch_url(
            OVERPASS_URL + "?data=" + _quote(query), expected_format="json", timeout=timeout)
    except Exception as exc:
        return {"status": "niedostępne", "reason": str(exc), "url": P.sanitize_url(OVERPASS_URL),
                "query_sha256": P.sha256_bytes(query.encode("utf-8"))}
    payload = json.loads(content.decode("utf-8"))
    return _osm_metrics(points, payload, {
        "status": "ok",
        "source": "overpass",
        "url": P.sanitize_url(final_url),
        "osm_timestamp": (payload.get("osm3s") or {}).get("timestamp_osm_base"),
        "attribution": "© OpenStreetMap contributors, ODbL 1.0",
    })


def _lambert_segments(ways):
    return [[CRS.wgs84_to_lambert72(node["lon"], node["lat"]) for node in way["geometry"]]
            for way in ways]


def _coverage_and_deviation(points, segments):
    """Pokrycie i odchyłka to **dwie różne wielkości** i nie wolno ich mieszać.

    Pokrycie mówi, na jakiej części osi drugie źródło w ogóle coś ma. Odchyłka jest
    liczona **tylko** na pokrytym odcinku — punkty bez pokrycia dawałyby setki metrów
    i zamazywały wynik.
    """
    deviations = sorted(min(_distance_to_polyline(point, seg) for seg in segments)
                        for point in points)
    covered = [d for d in deviations if d <= OSM_COVERAGE_RADIUS_M]
    result = {"points_checked": len(points),
              "coverage_radius_m": OSM_COVERAGE_RADIUS_M,
              "coverage_pct": round(100.0 * len(covered) / max(1, len(points)), 1)}
    if not covered:
        return result
    result.update({"deviation_median_m": round(covered[len(covered) // 2], 2),
                   "deviation_p95_m": round(covered[int(0.95 * (len(covered) - 1))], 2),
                   "deviation_max_m": round(covered[-1], 2)})
    return result


def _osm_metrics(points, payload, base):
    ways = [e for e in payload.get("elements", []) if e.get("type") == "way" and e.get("geometry")]
    segments = _lambert_segments(ways)
    if not segments:
        return dict(base, status="brak danych", ways=0)
    overall = _coverage_and_deviation(points, segments)
    if "deviation_median_m" not in overall:
        return dict(base, status="brak pokrycia", ways=len(ways), **overall)
    # Snapshot z `fetch_osm_routes.py` zna przynależność way'a do relacji kierunkowej,
    # więc da się policzyć odchyłkę osobno dla każdego toru. Ekstrakt bboxowy tego nie
    # ma — i właśnie dlatego mieszał cztery linie w jedną statystykę (raport pakietu A).
    per_relation = {}
    for way, segment in zip(ways, segments):
        for relation in way.get("route_relations", []):
            per_relation.setdefault(relation, []).append(segment)
    directions = []
    for relation in sorted(per_relation):
        entry = {"relation": relation}
        for route in payload.get("routes") or []:
            if route.get("id") == relation:
                entry["name"] = route.get("name")
        entry.update(_coverage_and_deviation(points, per_relation[relation]))
        entry["ways"] = len(per_relation[relation])
        directions.append(entry)
    return dict(base, **{
        "query_sha256": P.sha256_bytes(overpass_query(points).encode("utf-8")),
        "ways": len(ways),
        "nodes": sum(len(s) for s in segments),
        "per_relation": directions,
        "note": "OSM mapuje tory pojedynczo, więc odchyłka od osi trasy handlowej odpowiada "
                "mniej więcej połowie rozstawu torów i nie jest błędem żadnego ze źródeł.",
    }, **overall)


def _quote(text):
    from urllib.parse import quote
    return quote(text, safe="")


def _distance_to_polyline(point, polyline):
    best = float("inf")
    for a, b in zip(polyline, polyline[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        seg = dx * dx + dy * dy
        if seg <= 0:
            best = min(best, math.dist(point, a))
            continue
        t = ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / seg
        t = 0.0 if t < 0 else (1.0 if t > 1.0 else t)
        best = min(best, math.dist(point, (a[0] + t * dx, a[1] + t * dy)))
    return best


def main(argv=None):
    args = parse_args(argv)
    path = args.alignment if os.path.isabs(args.alignment) else os.path.join(ROOT, args.alignment)
    document, points = load_alignment(path)

    report = {"alignment_id": document["id"], "checked_at": P.utc_now_iso(),
              "source_crs": document["source_crs"], "points": len(points)}
    report["urbis"] = ({"status": "pominięte"} if args.skip_urbis
                       else crosscheck_urbis(points, args.timeout, args.urbis_file))
    report["osm"] = ({"status": "pominięte"} if args.skip_osm
                     else crosscheck_osm(points, args.timeout, args.osm_file))

    out = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "wb") as handle:
        handle.write(P.canonical_json(report))

    for name in ("urbis", "osm"):
        entry = report[name]
        if entry["status"] != "ok":
            print(f"[KONTROLA] {name}: {entry['status']}"
                  + (f" — {entry.get('reason', '')}" if entry.get("reason") else ""))
            continue
        if name == "urbis":
            print(f"[KONTROLA] urbis: tunel {entry['inside_tunnel_pct']}%, "
                  f"stacja {entry['inside_station_pct']}%, poza {entry['outside_pct']}% "
                  f"({entry['features']} obiektów)")
            print(f"[KONTROLA] urbis niveau: {entry['by_niveau']}; "
                  f"niveau=0 na {entry['niveau0_points']} punktach ({entry['niveau0_pct']}%)")
            for polygon, hits in entry["niveau0_polygons"].items():
                print(f"[NIVEAU0] {hits:>4} punktów w poligonie: {polygon}")
            for low, high in entry["niveau0_chainage_ranges_m"]:
                print(f"[NIVEAU0] kilometraż {low:.1f}–{high:.1f} m ({high - low:.1f} m)")
        else:
            print(f"[KONTROLA] osm: {entry['ways']} way, pokrycie {entry['coverage_pct']}% "
                  f"(promień {entry['coverage_radius_m']:.0f} m), odchyłka na pokrytym odcinku: "
                  f"mediana {entry['deviation_median_m']} m, P95 {entry['deviation_p95_m']} m, "
                  f"maks. {entry['deviation_max_m']} m")
            for direction in entry.get("per_relation", []):
                print(f"[KIERUNEK] {direction['relation']} {direction.get('name', '')}: "
                      f"{direction['ways']} way, pokrycie {direction['coverage_pct']}%, "
                      f"mediana {direction.get('deviation_median_m')} m, "
                      f"P95 {direction.get('deviation_p95_m')} m, "
                      f"maks. {direction.get('deviation_max_m')} m")
    print(f"[RAPORT] {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

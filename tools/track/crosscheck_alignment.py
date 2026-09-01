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
OVERPASS_QUERY = """[out:json][timeout:60];
(
  way["railway"="subway"](50.835,4.310,50.855,4.400);
);
out geom;
"""


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Kontrola krzyżowa osi wobec UrbIS i OSM")
    parser.add_argument("--alignment", default=os.path.join("data", "track", "L1_A.json"))
    parser.add_argument("--out", default=os.path.join("build", "L1_A-crosscheck.json"))
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--skip-osm", action="store_true")
    parser.add_argument("--osm-file", help="lokalna odpowiedź Overpass JSON zamiast zapytania sieciowego")
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


def crosscheck_urbis(points, timeout):
    try:
        content, final_url, _headers = P.fetch_url(URBIS_URL, expected_format="json", timeout=timeout)
    except Exception as exc:
        return {"status": "niedostępne", "reason": str(exc), "url": P.sanitize_url(URBIS_URL)}
    payload = json.loads(content.decode("utf-8"))
    features = payload.get("features", [])
    rings = {"MT": [], "MS": []}
    for feature in features:
        kind = (feature.get("properties") or {}).get("type")
        if kind in rings:
            for ring in polygon_rings(feature.get("geometry") or {}):
                rings[kind].append([CRS.wgs84_to_lambert72(x, y) for x, y, *_ in ring])

    counts = {"MT": 0, "MS": 0, "outside": 0}
    for point in points:
        if any(point_in_ring(point, ring) for ring in rings["MT"]):
            counts["MT"] += 1
        elif any(point_in_ring(point, ring) for ring in rings["MS"]):
            counts["MS"] += 1
        else:
            counts["outside"] += 1
    total = max(1, len(points))
    return {
        "status": "ok",
        "url": P.sanitize_url(final_url),
        "features": len(features),
        "polygons": {k: len(v) for k, v in rings.items()},
        "points_checked": len(points),
        "inside_tunnel_pct": round(100.0 * counts["MT"] / total, 1),
        "inside_station_pct": round(100.0 * counts["MS"] / total, 1),
        "outside_pct": round(100.0 * counts["outside"] / total, 1),
        "note": "UrbIS Metro to poligony tuneli i stacji, nie oś toru; miarą jest pokrycie, "
                "nie odchyłka liniowa.",
    }


def crosscheck_osm(points, timeout, local_file=None):
    if local_file:
        with open(local_file, "rb") as handle:
            content = handle.read()
        payload = json.loads(content.decode("utf-8"))
        return _osm_metrics(points, payload, {
            "status": "ok",
            "source": "snapshot lokalny",
            "file_sha256": P.sha256_bytes(content),
            "osm_timestamp": (payload.get("osm3s") or {}).get("timestamp_osm_base"),
            "attribution": "© OpenStreetMap contributors, ODbL 1.0",
        })
    try:
        content, final_url, _headers = P.fetch_url(
            OVERPASS_URL + "?data=" + _quote(OVERPASS_QUERY), expected_format="json", timeout=timeout)
    except Exception as exc:
        return {"status": "niedostępne", "reason": str(exc), "url": P.sanitize_url(OVERPASS_URL),
                "query_sha256": P.sha256_bytes(OVERPASS_QUERY.encode("utf-8"))}
    payload = json.loads(content.decode("utf-8"))
    return _osm_metrics(points, payload, {
        "status": "ok",
        "source": "overpass",
        "url": P.sanitize_url(final_url),
        "osm_timestamp": (payload.get("osm3s") or {}).get("timestamp_osm_base"),
        "attribution": "© OpenStreetMap contributors, ODbL 1.0",
    })


def _osm_metrics(points, payload, base):
    ways = [e for e in payload.get("elements", []) if e.get("type") == "way" and e.get("geometry")]
    segments = []
    for way in ways:
        segments.append([CRS.wgs84_to_lambert72(node["lon"], node["lat"]) for node in way["geometry"]])
    if not segments:
        return dict(base, status="brak danych", ways=0)
    all_deviations = sorted(min(_distance_to_polyline(point, seg) for seg in segments)
                            for point in points)
    # Ekstrakt OSM pokrywa tylko część pnia; punkty bez pokrycia dawałyby setki metrów
    # i zamazywały realną odchyłkę, więc pokrycie i odchyłka są raportowane osobno.
    covered = [d for d in all_deviations if d <= OSM_COVERAGE_RADIUS_M]
    if not covered:
        return dict(base, status="brak pokrycia", ways=len(ways),
                    coverage_pct=0.0, coverage_radius_m=OSM_COVERAGE_RADIUS_M)
    return dict(base, **{
        "query_sha256": P.sha256_bytes(OVERPASS_QUERY.encode("utf-8")),
        "ways": len(ways),
        "points_checked": len(points),
        "coverage_radius_m": OSM_COVERAGE_RADIUS_M,
        "coverage_pct": round(100.0 * len(covered) / len(points), 1),
        "deviation_median_m": round(covered[len(covered) // 2], 2),
        "deviation_p95_m": round(covered[int(0.95 * (len(covered) - 1))], 2),
        "deviation_max_m": round(covered[-1], 2),
        "note": "OSM mapuje tory pojedynczo, więc odchyłka od osi trasy handlowej odpowiada "
                "mniej więcej połowie rozstawu torów i nie jest błędem żadnego ze źródeł.",
    })


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
                       else crosscheck_urbis(points, args.timeout))
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
        else:
            print(f"[KONTROLA] osm: {entry['ways']} way, pokrycie {entry['coverage_pct']}% "
                  f"(promień {entry['coverage_radius_m']:.0f} m), odchyłka na pokrytym odcinku: "
                  f"mediana {entry['deviation_median_m']} m, P95 {entry['deviation_p95_m']} m, "
                  f"maks. {entry['deviation_max_m']} m")
    print(f"[RAPORT] {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

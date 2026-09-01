#!/usr/bin/env python3
"""Mierzy szerokość tunelu w planie z oficjalnych poligonów UrbIS wzdłuż gotowej osi.

    python3 tools/track/tunnel_width.py --alignment data/track/L1_A.json \
        --out build/L1_A-tunnel-width.json

Źródło: `brussels_mobility_metro` (Paradigm / Brussels Mobility, CC0) — obiekty `MT`
to **poligony tuneli w planie**, nie oś toru i nie przekrój. Rejestr źródeł mówi wprost:
„Obiekty MS/MT nie są automatycznie osią toru ani niweletą".

Dlatego wynik **nie upoważnia** do zmiany `profiles.py` z `design` na `observed`:
dataset nie mówi, czy poligon jest światłem tunelu, czy obrysem konstrukcji z murami.
Wynik jest widełkami do skonfrontowania z R-005 (#17), nie pomiarem światła tunelu.

Niedostępność źródła jest wynikiem, a nie powodem do pominięcia kontroli.
"""
import argparse
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import crs as CRS  # noqa: E402
import provenance as P  # noqa: E402
import sweep as SW  # noqa: E402

URBIS_URL = ("https://data.mobility.brussels/geoserver/ogc/features/v1/collections/"
             "bm_public_transport%3AMetro/items?limit=10000&f=application/json")
SOURCE_ID = "brussels_mobility_metro"
# Poza tym promieniem od stacji poligon opisuje komorę stacyjną, a nie tunel szlakowy.
STATION_HALO_M = 120.0
# Powyżej tej szerokości to węzeł, rozjazd albo ukośne trafienie w zakręcie poligonu.
RUNNING_TUNNEL_MAX_M = 15.0
RAY_MAX_M = 80.0


def point_in_ring(point, ring):
    x, y = point
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def ray_distance(origin, direction, ring, maximum=RAY_MAX_M):
    """Odległość do najbliższego przecięcia półprostej z pierścieniem."""
    best = None
    ox, oy = origin
    dx, dy = direction
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        ex, ey = x2 - x1, y2 - y1
        denominator = dx * ey - dy * ex
        if abs(denominator) < 1e-12:
            continue
        t = ((x1 - ox) * ey - (y1 - oy) * ex) / denominator
        u = ((x1 - ox) * dy - (y1 - oy) * dx) / denominator
        if t > 1e-6 and -1e-9 <= u <= 1.0 + 1e-9 and t < maximum:
            best = t if best is None else min(best, t)
    return best


def polygon_area(ring):
    total = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def polygon_perimeter(ring):
    return sum(math.dist(a, b) for a, b in zip(ring, ring[1:] + ring[:1]))


def corridor_width(ring):
    """Szerokość wydłużonego poligonu, odporna na krzywiznę.

    Wydłużony korytarz o szerokości `w` i długości `L` ma pole `A = w·L` i obwód
    `P = 2(w + L)`. Traktując to jako układ równań, `w` i `L` są pierwiastkami
    `t² − (P/2)·t + A = 0`, więc szerokość wychodzi **dokładnie** dla prostokąta
    i z małym błędem dla korytarza zakrzywionego.

    Prostsze `2A/P` daje `w·L/(w+L)`, czyli zaniża o czynnik `1/(1 + w/L)` — dla tunelu
    9,4 m na 400 m to 2 %, czyli 22 cm. Przy pytaniu „czy ten tunel jest jednotorowy"
    to jest różnica, która zmienia odpowiedź.

    Najmniejszy wymiar prostokąta otaczającego **nie nadaje się** do tego pytania:
    dla zakrzywionego korytarza mierzy zasięg, nie szerokość, i zawyża wielokrotnie
    (Pétillon–Hankar: 7,5 m korytarza wobec 25,1 m bboxa). Oba są raportowane, bo ich
    rozbieżność mierzy krzywiznę poligonu.
    """
    perimeter = polygon_perimeter(ring)
    area = polygon_area(ring)
    if perimeter <= 0.0:
        return None
    half = perimeter / 2.0
    discriminant = half * half - 4.0 * area
    if discriminant < 0.0:
        # Kształt nie jest wydłużony — dla takiego poligonu „szerokość korytarza"
        # nie ma sensu; zwracamy przybliżenie zamiast udawać dokładność.
        return 2.0 * area / perimeter
    return (half - math.sqrt(discriminant)) / 2.0


def bbox_min_width(ring):
    """Najmniejszy wymiar prostokąta otaczającego o dowolnej orientacji (rotating calipers)."""
    best = None
    count = len(ring)
    for index in range(count):
        ax, ay = ring[index]
        bx, by = ring[(index + 1) % count]
        ex, ey = bx - ax, by - ay
        length = math.hypot(ex, ey)
        if length < 1e-9:
            continue
        nx, ny = -ey / length, ex / length
        projection = [(x - ax) * nx + (y - ay) * ny for x, y in ring]
        span = max(projection) - min(projection)
        best = span if best is None else min(best, span)
    return best


def survey(payload):
    """Szerokość każdego poligonu tunelu w sieci, dwoma estymatorami.

    Odpowiada na pytanie, którego pomiar wzdłuż jednej osi nie obejmuje: czy w sieci
    STIB w ogóle występują tunele w skali jednotorowej, czy `bore_single` z `profiles.py`
    modeluje coś, czego nie ma.
    """
    rows = []
    for properties, ring in load_polygons(payload, "MT"):
        width = corridor_width(ring)
        if width is None:
            continue
        rows.append({
            "name": properties.get("name_fr", ""),
            "corridor_width_m": round(width, 2),
            "bbox_min_width_m": round(bbox_min_width(ring) or 0.0, 2),
            "area_m2": round(polygon_area(ring), 1),
            "perimeter_m": round(polygon_perimeter(ring), 1),
        })
    rows.sort(key=lambda r: r["corridor_width_m"])
    widths = [r["corridor_width_m"] for r in rows]
    return {
        "polygons": len(rows),
        "min_m": widths[0] if widths else None,
        "p05_m": widths[int(0.05 * (len(widths) - 1))] if widths else None,
        "median_m": round(statistics.median(widths), 2) if widths else None,
        "p95_m": widths[int(0.95 * (len(widths) - 1))] if widths else None,
        "max_m": widths[-1] if widths else None,
        "narrowest": rows[:8],
        "note": "corridor_width_m rozwiązuje A=w·L, P=2(w+L) i jest dokładne dla prostokąta. bbox_min_width_m "
                "zawyża dla zakrzywionych korytarzy i nie nadaje się do wnioskowania "
                "o braku wąskich tuneli.",
    }


def polygon_rings(geometry):
    kind = geometry.get("type")
    if kind == "Polygon":
        return [geometry["coordinates"][0]]
    if kind == "MultiPolygon":
        return [poly[0] for poly in geometry["coordinates"]]
    return []


def load_polygons(payload, wanted="MT"):
    out = []
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        if properties.get("type") != wanted:
            continue
        for ring in polygon_rings(feature.get("geometry") or {}):
            out.append((properties, [CRS.wgs84_to_lambert72(x, y) for x, y, *_ in ring]))
    return out


def measure(points, station_chainages, polygons, halo_m=STATION_HALO_M):
    """Szerokość poligonu prostopadle do osi w każdym punkcie poza obrębem stacji."""
    frames = SW.rmf_frames(points)
    stations = SW.chainages(points)
    rows = []
    for station, frame in zip(stations, frames):
        if station_chainages and min(abs(station - s) for s in station_chainages) < halo_m:
            continue
        position = (frame[0][0], frame[0][1])
        right = frame[2]
        length = math.hypot(right[0], right[1])
        if length < 1e-9:
            continue
        unit = (right[0] / length, right[1] / length)
        hosts = [(pr, ring) for pr, ring in polygons if point_in_ring(position, ring)]
        if len(hosts) != 1:  # poza poligonem albo w nakładce dwóch — pomiar niejednoznaczny
            continue
        properties, ring = hosts[0]
        left = ray_distance(position, (-unit[0], -unit[1]), ring)
        right_hit = ray_distance(position, unit, ring)
        if left is None or right_hit is None:
            continue
        # Znak liczony wzdłuż wektora „prawo" ramki (`cross(styczna, pion)`), więc
        # wartość ujemna oznacza, że środek poligonu leży po lewej stronie osi.
        rows.append({
            "chainage_m": round(station, 1),
            "width_m": round(left + right_hit, 3),
            "polygon_centre_offset_right_m": round((right_hit - left) / 2.0, 3),
            "polygon": properties.get("name_fr", ""),
        })
    return rows


def summarise(rows, maximum=RUNNING_TUNNEL_MAX_M):
    running = [r for r in rows if r["width_m"] <= maximum]
    widths = sorted(r["width_m"] for r in running)
    if not widths:
        return {"status": "brak pomiarów szlakowych", "samples": 0, "samples_all": len(rows)}
    return {
        "status": "ok",
        "samples_all": len(rows),
        "samples": len(widths),
        "running_tunnel_max_m": maximum,
        "min_m": widths[0],
        "p05_m": widths[int(0.05 * (len(widths) - 1))],
        "median_m": round(statistics.median(widths), 3),
        "p95_m": widths[int(0.95 * (len(widths) - 1))],
        "max_m": widths[-1],
        "stdev_m": round(statistics.pstdev(widths), 3),
        "per_polygon": {name: round(statistics.median(
            [r["width_m"] for r in running if r["polygon"] == name]), 3)
            for name in sorted({r["polygon"] for r in running})},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Szerokość tunelu w planie wg UrbIS")
    parser.add_argument("--alignment", default=os.path.join("data", "track", "L1_A.json"))
    parser.add_argument("--out", default=os.path.join("build", "tunnel-width.json"))
    parser.add_argument("--urbis-file", help="lokalna odpowiedź OGC Features zamiast sieci")
    parser.add_argument("--survey", action="store_true",
                        help="dodatkowo: szerokość KAŻDEGO poligonu tunelu w sieci, nie tylko wzdłuż osi")
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args(argv)

    path = args.alignment if os.path.isabs(args.alignment) else os.path.join(ROOT, args.alignment)
    with open(path, encoding="utf-8") as handle:
        document = json.load(handle)
    origin = document["origin_source_crs"]
    points = [(p[0] + origin[0], p[1] + origin[1], 0.0) for p in document["points"]]
    stops = [float(s["chainage_m"]) for s in document.get("stations", [])]

    report = {"alignment": document.get("id", ""), "source_id": SOURCE_ID,
              "checked_at": P.utc_now_iso(), "source_crs": document.get("source_crs"),
              "caveat": "Poligon MT jest obrysem tunelu w planie, nie światłem przekroju. "
                        "Wynik nie upoważnia do zmiany profilu z design na observed."}
    if args.urbis_file:
        with open(args.urbis_file, "rb") as handle:
            content = handle.read()
        report["source"] = {"kind": "snapshot lokalny", "sha256": P.sha256_bytes(content)}
    else:
        try:
            content, final_url, _headers = P.fetch_url(URBIS_URL, expected_format="json",
                                                       timeout=args.timeout)
        except Exception as exc:
            report["status"] = "niedostępne"
            report["reason"] = str(exc)
            report["url"] = P.sanitize_url(URBIS_URL)
            _write(args.out, report)
            print(f"[SZEROKOŚĆ] źródło niedostępne: {exc}")
            return 0
        report["source"] = {"kind": "ogc features", "url": P.sanitize_url(final_url),
                            "sha256": P.sha256_bytes(content)}

    payload = json.loads(content.decode("utf-8"))
    # Endpoint wstawia `timeStamp` odpowiedzi, więc sha256 surowych bajtów zmienia się
    # przy każdym pobraniu i nie identyfikuje wersji danych. Liczymy więc drugi hash,
    # wyłącznie z samych obiektów — ten jest stabilny między pobraniami.
    report["source"]["features_sha256"] = P.sha256_bytes(
        P.canonical_json(payload.get("features", [])))
    report["source"]["response_timestamp"] = payload.get("timeStamp")
    report["source"]["features_total"] = payload.get("numberMatched")
    polygons = load_polygons(payload, "MT")
    if args.survey:
        report["survey"] = survey(payload)
        item = report["survey"]
        print(f"[SIEĆ] {item['polygons']} poligonów tuneli: min {item['min_m']} m, "
              f"P05 {item['p05_m']} m, mediana {item['median_m']} m, "
              f"P95 {item['p95_m']} m, maks. {item['max_m']} m")
        for row in item["narrowest"][:5]:
            print(f"[SIEĆ]   {row['corridor_width_m']:5.2f} m "
                  f"(bbox {row['bbox_min_width_m']:5.2f} m)  {row['name']}")
    rows = measure(points, stops, polygons)
    summary = summarise(rows)
    report["status"] = summary["status"]
    report["polygons"] = len(polygons)
    report["summary"] = summary
    report["samples"] = rows
    _write(args.out, report)

    print(f"[SZEROKOŚĆ] poligonów MT={len(polygons)} próbek szlakowych={summary.get('samples', 0)} "
          f"(z {summary.get('samples_all', 0)} wszystkich)")
    if summary["status"] == "ok":
        print(f"[SZEROKOŚĆ] szerokość w planie: min {summary['min_m']:.2f} m, "
              f"P05 {summary['p05_m']:.2f} m, mediana {summary['median_m']:.2f} m, "
              f"P95 {summary['p95_m']:.2f} m, maks. {summary['max_m']:.2f} m "
              f"(odch.std {summary['stdev_m']:.2f} m)")
        for name, value in summary["per_polygon"].items():
            print(f"[SZEROKOŚĆ]   {value:5.2f} m  {name}")
    print(f"[SZEROKOŚĆ] {report['caveat']}")
    print(f"[RAPORT] {args.out}")
    return 0


def _write(path, report):
    target = path if os.path.isabs(path) else os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "wb") as handle:
        handle.write(P.canonical_json(report))


if __name__ == "__main__":
    sys.exit(main())

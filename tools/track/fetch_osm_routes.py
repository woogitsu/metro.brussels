#!/usr/bin/env python3
"""Pobiera relacje tras metra z OpenStreetMap i zapisuje snapshot do kontroli krzyżowej.

    python3 tools/track/fetch_osm_routes.py --alignment data/track/L2_E.json \
        --out build/osm/L2_E.json

Dlaczego API OSM, a nie Overpass: `overpass-api.de` jest z tego środowiska
nieosiągalny (`Connection reset by peer`), co jest udokumentowane już w
`reports/L1_A-crosscheck.md`. Zwykłe API OSM (`api.openstreetmap.org`) odpowiada,
a relacja trasy daje **lepszy materiał** niż zapytanie bboxowe: ekstrakt po bboxie
miesza wszystkie linie biegnące obok siebie, przez co „rozstaw torów" policzony
z takiej chmury wychodzi 11 m zamiast 3,9 m (ta sama pułapka opisana w raporcie
pakietu A).

Wyszukiwanie relacji idzie **z danych, nie z pamięci**: punkt pierwszej stacji osi
jest przeliczany do WGS84, mały wycinek `/api/0.6/map` daje lokalne way'e
`railway=subway`, a ich relacje macierzyste — trasy `route=subway` operatora
STIB/MIVB. Zostają tylko te z `ref` zgodnym z linią osi.

Snapshot ma kształt odpowiedzi Overpass (`elements` z `geometry`), żeby
`crosscheck_alignment.py --osm-file` czytał go bez rozgałęzień, plus dodatkowe
pole `route_relations` na każdym way'u, które pozwala policzyć odchyłkę osobno
dla każdego kierunku.

Licencja danych: © OpenStreetMap contributors, ODbL 1.0.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import crs as CRS  # noqa: E402
import provenance as P  # noqa: E402

API = "https://api.openstreetmap.org/api/0.6/"
SOURCE_ID = "openstreetmap"
PARSER_VERSION = "osm-routes/v1"
# Wycinek wokół stacji startowej. 0,0012 stopnia to ~130 m w poprzek i ~85 m wzdłuż
# południka — dość, żeby trafić w tunel pod stacją, i mało, żeby /map nie zwrócił
# całej dzielnicy. Wartość robocza, nie parametr źródła.
SEED_HALF_DEG = 0.0012
MAX_SEED_WAYS = 8


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Snapshot relacji tras metra z OSM")
    parser.add_argument("--alignment", required=True, help="oś, dla której szukamy trasy OSM")
    parser.add_argument("--out", help="domyślnie build/osm/<id osi>.json")
    parser.add_argument("--route-ref", help="ref linii w OSM; domyślnie z id osi (L2_E -> 2)")
    parser.add_argument("--relation", type=int, action="append",
                        help="pomiń wyszukiwanie i weź wprost tę relację (można podać wiele razy)")
    parser.add_argument("--timeout", type=float, default=90.0)
    return parser.parse_args(argv)


def api_get(path, timeout):
    content, final_url, _headers = P.fetch_url(API + path, expected_format="json", timeout=timeout)
    return json.loads(content.decode("utf-8")), final_url


def route_ref_from_id(alignment_id):
    """`L2_E` -> `2`. Numer linii, nie identyfikator pakietu."""
    head = alignment_id.split("_")[0]
    return head[1:].lstrip("0") or head[1:]


def seed_bbox(x, y, half=SEED_HALF_DEG):
    lon, lat = CRS.lambert72_to_wgs84(x, y)
    return (lon - half, lat - half, lon + half, lat + half), (lon, lat)


def discover_relations(bbox, route_ref, timeout, log=print):
    """Trasy `route=subway` o zadanym `ref`, znalezione przez lokalny wycinek mapy."""
    payload, url = api_get("map.json?bbox=%.6f,%.6f,%.6f,%.6f" % bbox, timeout)
    ways = [e for e in payload.get("elements", [])
            if e.get("type") == "way" and (e.get("tags") or {}).get("railway") == "subway"]
    log(f"[OSM] wycinek {url.split('bbox=')[-1]}: {len(ways)} way railway=subway")
    found = {}
    for way in ways[:MAX_SEED_WAYS]:
        parents, _ = api_get(f"way/{way['id']}/relations.json", timeout)
        for element in parents.get("elements", []):
            tags = element.get("tags") or {}
            if tags.get("type") != "route" or tags.get("route") != "subway":
                continue
            if route_ref is not None and str(tags.get("ref")) != str(route_ref):
                continue
            found[element["id"]] = {"id": element["id"], "ref": tags.get("ref"),
                                    "name": tags.get("name"), "operator": tags.get("operator"),
                                    "from": tags.get("from"), "to": tags.get("to")}
    return [found[k] for k in sorted(found)]


def fetch_relation_ways(relation_id, timeout):
    """Way'e relacji z geometrią — kształt zgodny z `out geom` Overpassa."""
    payload, _url = api_get(f"relation/{relation_id}/full.json", timeout)
    nodes = {e["id"]: (e["lon"], e["lat"]) for e in payload["elements"] if e["type"] == "node"}
    ways = []
    for element in payload["elements"]:
        if element.get("type") != "way":
            continue
        geometry = [{"lon": nodes[n][0], "lat": nodes[n][1]}
                    for n in element.get("nodes", []) if n in nodes]
        if len(geometry) < 2:
            continue
        # `version` i `timestamp` way'a ZOSTAJĄ w wyniku — 6.D64, i z tego samego
        # powodu, co w `parse_osm_map_xml` drogi zapasowej: bez nich nie ma z czego
        # wyprowadzić NICZEGO o stanie bazy OSM, a pole `timestamp_osm_base` niosło
        # do 09.09.2026 czas pobrania. Zmierzone przed poprawką: 162 way'e, z tego
        # **zero** z `timestamp`, a pole „stan bazy" pokazywało godzinę przebiegu.
        ways.append({"type": "way", "id": element["id"], "tags": element.get("tags") or {},
                     "geometry": geometry, "route_relations": [relation_id],
                     "version": element.get("version"),
                     "timestamp": element.get("timestamp")})
    return ways


def merge_ways(groups):
    """Way należący do dwóch kierunków ma jeden wpis i dwie relacje."""
    merged = {}
    for way in groups:
        existing = merged.get(way["id"])
        if existing is None:
            merged[way["id"]] = way
            continue
        for relation in way["route_relations"]:
            if relation not in existing["route_relations"]:
                existing["route_relations"].append(relation)
    return [merged[k] for k in sorted(merged)]


def main(argv=None):
    args = parse_args(argv)
    path = args.alignment if os.path.isabs(args.alignment) else os.path.join(ROOT, args.alignment)
    with open(path, encoding="utf-8") as handle:
        document = json.load(handle)
    origin = document["origin_source_crs"]
    first = document["points"][0]
    bbox, seed_lonlat = seed_bbox(origin[0] + first[0], origin[1] + first[1])
    route_ref = args.route_ref or route_ref_from_id(document["id"])

    try:
        if args.relation:
            routes = []
            for relation_id in args.relation:
                payload, _ = api_get(f"relation/{relation_id}.json", args.timeout)
                tags = payload["elements"][0].get("tags") or {}
                routes.append({"id": relation_id, "ref": tags.get("ref"), "name": tags.get("name"),
                               "operator": tags.get("operator"), "from": tags.get("from"),
                               "to": tags.get("to")})
        else:
            routes = discover_relations(bbox, route_ref, args.timeout)
        if not routes:
            raise RuntimeError(f"nie znaleziono relacji route=subway ref={route_ref} "
                               f"w wycinku wokół {seed_lonlat}")
        ways = merge_ways([w for route in routes
                           for w in fetch_relation_ways(route["id"], args.timeout)])
    except Exception as exc:  # niedostępność źródła jest wynikiem, nie powodem do milczenia
        report = {"alignment_id": document["id"], "status": "niedostępne", "reason": str(exc),
                  "route_ref": route_ref, "api": P.sanitize_url(API),
                  "checked_at": P.utc_now_iso()}
        _write(args, document, report)
        print(f"[OSM] niedostępne: {exc}")
        return 0

    # `osm3s.timestamp_osm_base` NIE JEST tu wypełniane i to jest cała treść 6.D64.
    # Pole znaczy **stan bazy OSM** i podaje je wyłącznie Overpass; `/api/0.6` nie
    # podaje go wcale. Do 09.09.2026 stał tu `P.utc_now_iso()`, czyli **czas
    # pobrania pod nazwą stanu bazy** — zmierzone: `2026-09-09T22:02:01Z` na
    # przebiegu, którego way'e pochodziły z edycji sprzed miesięcy. Czytelnik
    # (`crosscheck_alignment.py`) bierze to pole wprost, więc raport cytowałby
    # godzinę przebiegu jako stan danych i nic by go nie zatrzymało.
    #
    # Zamiast zmyślenia stoją tu DWIE liczby pod własnymi nazwami: czas pobrania
    # i **dolna granica** stanu bazy, czyli najświeższa edycja wśród pobranych way'ów.
    # Granica nie jest stanem bazy i tak się nazywa — way nietknięty od roku nie mówi
    # nic o tym, co baza wie dzisiaj.
    snapshot = {
        "version": 0.6,
        "generator": "tools/track/fetch_osm_routes.py",
        "parser_version": PARSER_VERSION,
        "retrieved_at": P.utc_now_iso(),
        "way_timestamp_max": max((w["timestamp"] for w in ways if w.get("timestamp")),
                                 default=None),
        "attribution": "© OpenStreetMap contributors, ODbL 1.0",
        "alignment_id": document["id"],
        "route_ref": route_ref,
        "seed_lonlat": [round(seed_lonlat[0], 7), round(seed_lonlat[1], 7)],
        "routes": routes,
        "elements": ways,
    }
    out = _write(args, document, snapshot)
    print(f"[OSM] relacje: " + ", ".join(f"{r['id']} ({r['name']})" for r in routes))
    print(f"[OSM] way'ów: {len(ways)}, węzłów: {sum(len(w['geometry']) for w in ways)}")
    print(f"[RAPORT] {out}")
    return 0


def _write(args, document, payload):
    out = args.out or os.path.join("build", "osm", f"{document['id']}.json")
    out = out if os.path.isabs(out) else os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    content = P.canonical_json(payload)
    with open(out, "wb") as handle:
        handle.write(content)
    manifest = P.build_manifest(
        source_id=SOURCE_ID,
        requested_url=API,
        final_url=API,
        content=content,
        retrieved_at=P.utc_now_iso(),
        data_format="json",
        parser_version=PARSER_VERSION,
        query_text=f"relacje route=subway ref={payload.get('route_ref')} przez /api/0.6",
        transformations=["osm_relation_full", "node_ids_to_geometry"],
        input_sources=[SOURCE_ID],
    )
    with open(out.replace(".json", ".manifest.json"), "wb") as handle:
        handle.write(P.canonical_json(manifest))
    return out


if __name__ == "__main__":
    sys.exit(main())

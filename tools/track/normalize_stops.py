#!/usr/bin/env python3
"""Normalizuje stacje metra z feedu GTFS STIB/MIVB do `data/network/stops.json`.

    python3 tools/track/normalize_stops.py --gtfs data/gtfs/stib_gtfs.zip \
        --out data/network/stops.json

Zasady, które ten moduł realizuje wprost:

- rekord `stops.txt` **nie jest** stacją; stacje powstają z `location_type`
  i `parent_station`, a zbiór punktów metra z `routes` -> `trips` -> `stop_times`;
- nie ma tu żadnej listy nazw stacji; liczba stacji wychodzi z danych i jeżeli
  nie zgadza się z `docs/00-network-data.md`, jest **raportowana**, nie naprawiana;
- nazwy zostają w oryginale FR/NL, bez tłumaczenia na polski;
- rekordy bez współrzędnych i osierocone `parent_station` są odrzucane z podaniem
  przyczyny, a nie po cichu pomijane;
- wynik jest sortowany deterministycznie, więc ten sam feed daje bajtowo ten sam JSON.
"""
import argparse
import csv
import io
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
import provenance as P  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
METRO_ROUTE_TYPE = "1"
LOCATION_STOP = "0"
LOCATION_STATION = "1"
LOCATION_ENTRANCE = "2"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Normalizacja stacji metra z GTFS STIB/MIVB")
    parser.add_argument("--gtfs", default=os.path.join("data", "gtfs", "stib_gtfs.zip"))
    parser.add_argument("--out", default=os.path.join("data", "network", "stops.json"))
    parser.add_argument("--manifest", default=os.path.join("data", "network", "gtfs-manifest.json"),
                        help="manifest z fetch_gtfs.py; jego sha256 trafia do wyniku")
    parser.add_argument("--network", default=os.path.join("data", "network", "lines.json"),
                        help="tylko do porównania liczby stacji; nie jest używany do korekty")
    parser.add_argument("--report", help="opcjonalny raport JSON z odrzuconymi rekordami")
    return parser.parse_args(argv)


def read_table(archive, name):
    if name not in archive.namelist():
        return []
    with archive.open(name) as handle:
        return list(csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig", newline="")))


def build_translations(rows):
    """GTFS Translations STIB łączy się po `field_value`, nie po `record_id`."""
    out = {}
    for row in rows:
        if row.get("table_name") != "stops" or row.get("field_name") != "stop_name":
            continue
        value = row.get("field_value")
        language = (row.get("language") or "").lower()
        if not value or not language:
            continue
        out.setdefault(value, {})[language] = row.get("translation", "")
    return out


def _coords(row, reject, kind):
    lat, lon = row.get("stop_lat", ""), row.get("stop_lon", "")
    try:
        if lat == "" or lon == "":
            raise ValueError("puste współrzędne")
        return round(float(lat), 6), round(float(lon), 6)
    except ValueError as exc:
        reject.append({"stop_id": row.get("stop_id"), "kind": kind,
                       "reason": f"brak lub błędne współrzędne: {exc}"})
        return None, None


def normalize(archive):
    routes = read_table(archive, "routes.txt")
    trips = read_table(archive, "trips.txt")
    stop_times = read_table(archive, "stop_times.txt")
    stops_rows = read_table(archive, "stops.txt")
    translations = build_translations(read_table(archive, "translations.txt"))

    metro_routes = {r["route_id"]: r for r in routes if r.get("route_type") == METRO_ROUTE_TYPE}
    if not metro_routes:
        raise SystemExit("BŁĄD: feed nie zawiera żadnej trasy o route_type=1 (metro)")
    trip_to_route = {t["trip_id"]: t["route_id"] for t in trips if t.get("route_id") in metro_routes}

    stop_routes = {}
    for row in stop_times:
        route_id = trip_to_route.get(row.get("trip_id"))
        if route_id is None:
            continue
        stop_routes.setdefault(row["stop_id"], set()).add(metro_routes[route_id]["route_short_name"])

    stops = {row["stop_id"]: row for row in stops_rows}
    rejected = []

    # osierocone parent_station wykrywamy na całym pliku, nie tylko na metrze
    for row in stops_rows:
        parent = row.get("parent_station") or ""
        if parent and parent not in stops:
            rejected.append({"stop_id": row["stop_id"], "kind": "orphan_parent",
                             "reason": f"parent_station={parent} nie istnieje w stops.txt"})

    entrances = {}
    for row in stops_rows:
        if (row.get("location_type") or LOCATION_STOP) != LOCATION_ENTRANCE:
            continue
        parent = row.get("parent_station") or ""
        if not parent:
            continue
        lat, lon = _coords(row, rejected, "entrance")
        if lat is None:
            continue
        entrances.setdefault(parent, []).append({"stop_id": row["stop_id"], "name": row.get("stop_name", ""),
                                                 "lat": lat, "lon": lon})

    stations = {}
    orphan_platforms = []
    orphan_ids = set()
    for stop_id in sorted(stop_routes):
        row = stops.get(stop_id)
        if row is None:
            rejected.append({"stop_id": stop_id, "kind": "platform",
                             "reason": "stop_id z stop_times.txt nie istnieje w stops.txt"})
            continue
        lat, lon = _coords(row, rejected, "platform")
        if lat is None:
            continue
        parent = row.get("parent_station") or ""
        if parent and parent in stops:
            station_id = parent
        else:
            station_id = stop_id
            orphan_ids.add(stop_id)
            orphan_platforms.append({"stop_id": stop_id, "name": row.get("stop_name", ""),
                                     "reason": "peron metra bez parent_station; potraktowany jako własna stacja"})
        entry = stations.setdefault(station_id, {"platforms": [], "routes": set()})
        entry["platforms"].append({"stop_id": stop_id, "name": row.get("stop_name", ""),
                                   "lat": lat, "lon": lon,
                                   "routes": sorted(stop_routes[stop_id], key=_route_key)})
        entry["routes"].update(stop_routes[stop_id])

    out = []
    for station_id in sorted(stations, key=_id_key):
        entry = stations[station_id]
        container = stops.get(station_id, {})
        name = container.get("stop_name", "")
        lat, lon = _coords(container, rejected, "station") if container.get("stop_lat") else (None, None)
        if lat is None:
            # stacja bez własnego kontenera: kotwiczymy na średniej peronów i jawnie to znaczymy
            lat = round(sum(p["lat"] for p in entry["platforms"]) / len(entry["platforms"]), 6)
            lon = round(sum(p["lon"] for p in entry["platforms"]) / len(entry["platforms"]), 6)
            anchor = "platform_mean"
        elif station_id in orphan_ids:
            anchor = "orphan_platform"
        else:
            anchor = "gtfs_station_container"
        names = translations.get(name, {})
        entry_out = {
            "station_id": station_id,
            "name": name,
            "name_fr": names.get("fr", name),
            "name_nl": names.get("nl", ""),
            "lat": lat,
            "lon": lon,
            "anchor": anchor,
            "location_type": container.get("location_type", "") or LOCATION_STOP,
            "routes": sorted(entry["routes"], key=_route_key),
            "platforms": sorted(entry["platforms"], key=lambda p: _id_key(p["stop_id"])),
            "entrances": sorted(entrances.get(station_id, []), key=lambda e: _id_key(e["stop_id"])),
        }
        if station_id in orphan_ids:
            entry_out["anomaly"] = ("rekord bez parent_station w feedzie STIB; nie scalam automatycznie "
                                    "z kontenerem o tej samej nazwie, bo wymagałoby to decyzji poza danymi")
        out.append(entry_out)

    summary = {
        "metro_routes": sorted(({"route_id": r["route_id"],
                                 "short_name": r["route_short_name"],
                                 "long_name": r.get("route_long_name", "")}
                                for r in metro_routes.values()),
                               key=lambda r: _route_key(r["short_name"])),
        "metro_platform_records": sum(len(s["platforms"]) for s in out),
        "metro_stations": len(out),
        "metro_station_containers": len(out) - len(orphan_ids),
        "unique_station_names": len({s["name"] for s in out}),
        "entrance_records": sum(len(s["entrances"]) for s in out),
        "rejected_records": len(rejected),
        "orphan_platforms": orphan_platforms,
    }
    return out, summary, rejected


def _route_key(value):
    return (0, int(value)) if str(value).isdigit() else (1, str(value))


def _id_key(value):
    return (0, int(value)) if str(value).isdigit() else (1, str(value))


def main(argv=None):
    args = parse_args(argv)
    gtfs = args.gtfs if os.path.isabs(args.gtfs) else os.path.join(ROOT, args.gtfs)
    out_path = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    if not os.path.isfile(gtfs):
        raise SystemExit(f"BŁĄD: brak feedu {gtfs}; uruchom najpierw tools/track/fetch_gtfs.py")
    if not zipfile.is_zipfile(gtfs):
        raise SystemExit(f"BŁĄD: {gtfs} nie jest archiwum ZIP")

    with zipfile.ZipFile(gtfs) as archive:
        broken = archive.testzip()
        if broken is not None:
            raise SystemExit(f"BŁĄD: uszkodzony wpis w archiwum: {broken}")
        stations, summary, rejected = normalize(archive)

    manifest_path = args.manifest if os.path.isabs(args.manifest) else os.path.join(ROOT, args.manifest)
    feed = {}
    if os.path.isfile(manifest_path):
        with open(manifest_path, encoding="utf-8") as handle:
            manifest = json.load(handle)
        feed = {"source_id": manifest.get("source_id"),
                "content_sha256": manifest.get("content_sha256"),
                "retrieved_at": manifest.get("retrieved_at"),
                "feed_version": (manifest.get("gtfs", {}).get("feed_info") or {}).get("feed_version")}

    document = {
        "$comment": "Stacje metra wyprowadzone z feedu GTFS STIB/MIVB. Generowane przez "
                    "tools/track/normalize_stops.py — nie edytować ręcznie.",
        "schema_version": 1,
        "generator": "tools/track/normalize_stops.py",
        "parser_version": "gtfs-stops/v1",
        "feed": feed,
        "summary": summary,
        "stations": stations,
    }

    network_path = args.network if os.path.isabs(args.network) else os.path.join(ROOT, args.network)
    if os.path.isfile(network_path):
        with open(network_path, encoding="utf-8") as handle:
            declared = json.load(handle).get("network", {}).get("metro_stations")
        if declared is not None:
            document["summary"]["declared_metro_stations"] = declared
            document["summary"]["matches_declared"] = declared == summary["metro_stations"]

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as handle:
        handle.write(P.canonical_json(document))

    print(f"[RAPORT] linie metra: {[r['short_name'] for r in summary['metro_routes']]}")
    print(f"[RAPORT] rekordy peronowe metra: {summary['metro_platform_records']}")
    print(f"[RAPORT] stacje metra wyprowadzone z danych: {summary['metro_stations']}")
    print(f"[RAPORT] unikalne nazwy stacji: {summary['unique_station_names']}")
    print(f"[RAPORT] rekordy wejść: {summary['entrance_records']}")
    print(f"[RAPORT] rekordy odrzucone: {summary['rejected_records']}")
    for item in rejected[:10]:
        print(f"[ODRZUCONO] {item['kind']} {item['stop_id']}: {item['reason']}")
    if len(rejected) > 10:
        print(f"[ODRZUCONO] ... i {len(rejected) - 10} więcej (użyj --report)")
    for item in summary["orphan_platforms"]:
        print(f"[WYJĄTEK] {item['stop_id']} {item['name']}: {item['reason']}")
    if "declared_metro_stations" in summary and not summary["matches_declared"]:
        print(f"[ROZBIEŻNOŚĆ] docs/00-network-data.md deklaruje "
              f"{summary['declared_metro_stations']} stacji, dane dają {summary['metro_stations']} wpisów "
              f"({summary['metro_station_containers']} kontenerów + {len(summary['orphan_platforms'])} bez parent_station), "
              f"{summary['unique_station_names']} unikalnych nazw. "
              f"Nie koryguję — wymaga rozstrzygnięcia drugim źródłem.")
    print(f"[RAPORT] {out_path}")

    if args.report:
        report_path = args.report if os.path.isabs(args.report) else os.path.join(ROOT, args.report)
        os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
        with open(report_path, "wb") as handle:
            handle.write(P.canonical_json({"summary": summary, "rejected": rejected}))
        print(f"[RAPORT] {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

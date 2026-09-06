#!/usr/bin/env python3
"""Pobiera feed GTFS STIB/MIVB do ignorowanego `data/gtfs/` i zapisuje provenance.

    python3 tools/track/fetch_gtfs.py --out data/gtfs/stib_gtfs.zip

Surowy ZIP **nie trafia do repo** (`.gitignore`: `data/gtfs/`). Do repo idzie
wyłącznie mały manifest provenance.

Kanał dystrybucji: Belgian Mobility Open Data (BMC). Dawny portal Opendatasoft
`data.stib-mivb.brussels` nie istnieje — każda ścieżka zwraca 302 na
`data.belgianmobility.io`, więc dawne identyfikatory datasetów
(`gtfs-files-production`, `stop-details-production`) nie są już serwowane.

Atrybucja wymagana przez warunki BMC: `Source: STIB-MIVB - Open Data - <data>`.
Limity anonimowe: 100 żądań/dobę i 10/minutę; przekroczenie daje HTTP 429.
"""
import argparse
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
import provenance as P  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DEFAULT_SOURCE_ID = "stib_gtfs"
REQUIRED_MEMBERS = ("agency.txt", "routes.txt", "stops.txt", "stop_times.txt", "trips.txt")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Pobranie feedu GTFS STIB/MIVB z provenance")
    parser.add_argument("--out", default=os.path.join("data", "gtfs", "stib_gtfs.zip"),
                        help="ścieżka docelowa ZIP-a (katalog musi być gitignored)")
    parser.add_argument("--manifest", default=os.path.join("data", "network", "gtfs-manifest.json"),
                        help="mały manifest provenance commitowany do repo")
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID,
                        help="identyfikator w data/network/sources.json")
    parser.add_argument("--registry", default=os.path.join(ROOT, "data", "network", "sources.json"))
    parser.add_argument("--url", help="nadpisanie download_url z rejestru")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--offline", action="store_true",
                        help="nie pobieraj; policz manifest dla istniejącego pliku --out")
    return parser.parse_args(argv)


def inspect_zip(path):
    """Sprawdza kompletność archiwum i wyciąga zakres dat feedu."""
    if not zipfile.is_zipfile(path):
        raise SystemExit(f"BŁĄD: {path} nie jest archiwum ZIP")
    with zipfile.ZipFile(path) as archive:
        broken = archive.testzip()
        if broken is not None:
            raise SystemExit(f"BŁĄD: uszkodzony wpis w archiwum: {broken}")
        names = set(archive.namelist())
        missing = [m for m in REQUIRED_MEMBERS if m not in names]
        if missing:
            raise SystemExit(f"BŁĄD: niekompletny GTFS, brak: {', '.join(missing)}")
        info = {"members": sorted(names)}
        if "feed_info.txt" in names:
            rows = _read_csv(archive, "feed_info.txt")
            if rows:
                first = rows[0]
                info["feed_info"] = {k: first.get(k, "") for k in
                                     ("feed_publisher_name", "feed_version", "feed_start_date", "feed_end_date")}
        if "calendar.txt" in names:
            rows = _read_csv(archive, "calendar.txt")
            starts = [r["start_date"] for r in rows if r.get("start_date")]
            ends = [r["end_date"] for r in rows if r.get("end_date")]
            if starts and ends:
                info["calendar_range"] = {"start_date": min(starts), "end_date": max(ends), "services": len(rows)}
        info["member_counts"] = {name: _count_rows(archive, name)
                                 for name in sorted(names) if name.endswith(".txt")}
    return info


def _read_csv(archive, name):
    import csv
    import io
    with archive.open(name) as handle:
        text = io.TextIOWrapper(handle, encoding="utf-8-sig", newline="")
        return list(csv.DictReader(text))


def _count_rows(archive, name):
    with archive.open(name) as handle:
        return max(0, sum(1 for _ in handle) - 1)


def main(argv=None):
    args = parse_args(argv)
    out = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    manifest_path = args.manifest if os.path.isabs(args.manifest) else os.path.join(ROOT, args.manifest)

    registry = P.load_source_registry(args.registry)
    if args.source_id not in registry:
        raise SystemExit(f"BŁĄD: brak źródła {args.source_id} w {args.registry}")
    source = registry[args.source_id]
    url = args.url or source.get("download_url")
    if not url:
        raise SystemExit(f"BŁĄD: źródło {args.source_id} nie ma download_url; podaj --url")

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    if args.offline:
        if not os.path.isfile(out):
            raise SystemExit(f"BŁĄD: tryb --offline, a plik {out} nie istnieje")
        with open(out, "rb") as handle:
            content = handle.read()
        final_url = url
        retrieved_at = P.utc_now_iso()
        print(f"[OFFLINE] używam istniejącego {out} ({len(content)} B)")
    else:
        try:
            content, final_url, _headers = P.fetch_url(url, expected_format="zip", timeout=args.timeout)
        except Exception as exc:
            raise SystemExit(f"BŁĄD: pobranie {P.sanitize_url(url)} nie powiodło się: {exc}")
        retrieved_at = P.utc_now_iso()
        with open(out, "wb") as handle:
            handle.write(content)
        print(f"[POBRANO] {P.sanitize_url(final_url)} -> {out} ({len(content)} B)")

    details = inspect_zip(out)
    manifest = P.build_manifest(
        source_id=args.source_id,
        requested_url=url,
        final_url=final_url,
        content=content,
        retrieved_at=retrieved_at,
        data_format="zip",
        parser_version="gtfs-fetch/v1",
    )
    manifest["gtfs"] = details
    manifest["attribution"] = source.get("attribution")
    # 6.D23, wariant C wybrany przez wlasciciela 06.09.2026: manifest jest nadpisywany
    # TYLKO przy zmianie `content_sha256`. Bez tego `retrieved_at` zmienial plik w `data/`
    # przy kazdym uruchomieniu, takze w `--offline` (zmierzone przy 6.D12, #295).
    # Komunikat nizej nie jest ozdoba: to on zastepuje sygnal, ktory dawal `git diff`.
    stan = P.write_manifest_if_changed(manifest_path, manifest)

    counts = details["member_counts"]
    print(f"[RAPORT] sha256={manifest['content_sha256']}")
    print(f"[RAPORT] rozmiar={manifest['size_bytes']} B, pobrano={retrieved_at}")
    if "feed_info" in details:
        feed = details["feed_info"]
        print(f"[RAPORT] feed_version={feed.get('feed_version')} "
              f"zakres={feed.get('feed_start_date')}..{feed.get('feed_end_date')}")
    if "calendar_range" in details:
        cal = details["calendar_range"]
        print(f"[RAPORT] calendar={cal['start_date']}..{cal['end_date']} services={cal['services']}")
    for name in ("stops.txt", "routes.txt", "trips.txt", "stop_times.txt", "shapes.txt"):
        if name in counts:
            print(f"[RAPORT] {name}: {counts[name]} rekordów")
    if stan == "bez zmian":
        print("[RAPORT] manifest bez zmian: content_sha256 ten sam, plik nietkniety")
    else:
        print(f"[RAPORT] manifest {stan}")
    print(f"[RAPORT] manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

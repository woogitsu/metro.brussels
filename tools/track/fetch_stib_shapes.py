#!/usr/bin/env python3
"""Pobiera shapefile'y sieci STIB/MIVB do ignorowanego `data/raw/` i zapisuje provenance.

    python3 tools/track/fetch_stib_shapes.py --out data/raw/stib_shapefiles.zip

Dawny dataset Opendatasoft `shapefiles-production` nie istnieje — portal
`data.stib-mivb.brussels` zwraca 302 na `data.belgianmobility.io`. Aktualny,
anonimowy endpoint jest w `data/network/sources.json` pod `stib_shapefiles`.

Archiwum deklaruje własne okno ważności w polach `Date_debut`/`Date_fin`; jest ono
zapisywane w manifeście, bo bywa **wcześniejsze niż data pobrania**.
"""
import argparse
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import provenance as P  # noqa: E402
import shapefile as S  # noqa: E402

DEFAULT_SOURCE_ID = "stib_shapefiles"
PREFIX = "2603_STIB_MIVB_Network/"
REQUIRED = ("ACTU_LIGNES_BRUTES.shp", "ACTU_LIGNES_BRUTES.dbf", "ACTU_LIGNES_BRUTES.prj",
            "ACTU_STOPS.shp", "ACTU_STOPS.dbf")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Pobranie shapefile'ów sieci STIB/MIVB")
    parser.add_argument("--out", default=os.path.join("data", "raw", "stib_shapefiles.zip"))
    parser.add_argument("--manifest", default=os.path.join("data", "network", "shapes-manifest.json"))
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--registry", default=os.path.join(ROOT, "data", "network", "sources.json"))
    parser.add_argument("--url")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--offline", action="store_true")
    return parser.parse_args(argv)


def inspect_archive(path):
    if not zipfile.is_zipfile(path):
        raise SystemExit(f"BŁĄD: {path} nie jest archiwum ZIP")
    with zipfile.ZipFile(path) as archive:
        broken = archive.testzip()
        if broken is not None:
            raise SystemExit(f"BŁĄD: uszkodzony wpis w archiwum: {broken}")
        names = archive.namelist()
        prefix = PREFIX if any(n.startswith(PREFIX) for n in names) else ""
        missing = [m for m in REQUIRED if f"{prefix}{m}" not in names]
        if missing:
            raise SystemExit(f"BŁĄD: niekompletne archiwum, brak: {', '.join(missing)}")
        lines = S.read_pair(archive.read(f"{prefix}ACTU_LIGNES_BRUTES.shp"),
                            archive.read(f"{prefix}ACTU_LIGNES_BRUTES.dbf"))
        stops = S.read_pair(archive.read(f"{prefix}ACTU_STOPS.shp"),
                            archive.read(f"{prefix}ACTU_STOPS.dbf"))
        prj = S.read_prj(archive.read(f"{prefix}ACTU_LIGNES_BRUTES.prj").decode("utf-8"))
    metro = [r["attributes"] for r in lines if str(r["attributes"].get("LineCode", "")).endswith("m")]
    starts = sorted({r["Date_debut"] for r in metro if r.get("Date_debut")})
    ends = sorted({r["Date_fin"] for r in metro if r.get("Date_fin")})
    return {
        "members": len(names),
        "line_records": len(lines),
        "stop_records": len(stops),
        "metro_line_records": len(metro),
        "metro_line_codes": sorted({r["LineCode"] for r in metro}),
        "prj": prj,
        "dataset_validity": {"date_debut": starts, "date_fin": ends},
    }


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
        final_url, retrieved_at = url, P.utc_now_iso()
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

    details = inspect_archive(out)
    manifest = P.build_manifest(source_id=args.source_id, requested_url=url, final_url=final_url,
                                content=content, retrieved_at=retrieved_at, data_format="zip",
                                parser_version="stib-shapes/v1", crs="EPSG:31370")
    manifest["shapefiles"] = details
    manifest["dataset_validity"] = details["dataset_validity"]
    manifest["attribution"] = source.get("attribution")
    os.makedirs(os.path.dirname(manifest_path) or ".", exist_ok=True)
    with open(manifest_path, "wb") as handle:
        handle.write(P.canonical_json(manifest))

    print(f"[RAPORT] sha256={manifest['content_sha256']}")
    print(f"[RAPORT] linie={details['line_records']} przystanki={details['stop_records']}")
    print(f"[RAPORT] metro: {details['metro_line_records']} rekordów {details['metro_line_codes']}")
    print(f"[RAPORT] CRS źródła: {details['prj']['name']}")
    validity = details["dataset_validity"]
    print(f"[RAPORT] okno ważności datasetu: {validity['date_debut']} .. {validity['date_fin']}")
    print(f"[RAPORT] manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Snapshot a source into an auditable provenance manifest, or diff two manifests."""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

from provenance import (  # noqa: E402
    build_manifest,
    canonical_json,
    diff_manifests,
    fetch_url,
    load_source_registry,
)


def _source_metadata(row: dict) -> dict:
    return {
        key: row.get(key)
        for key in ("publisher", "dataset", "license", "license_status", "checked_at")
        if key in row
    }


def snapshot(args: argparse.Namespace) -> int:
    registry = load_source_registry(args.registry)
    if args.source_id not in registry:
        raise SystemExit(f"unknown source_id: {args.source_id}")
    source = registry[args.source_id]
    url = args.url or source.get("download_url") or source.get("url")
    if not url:
        raise SystemExit("source has no usable URL; provide --url explicitly")

    data, final_url, headers = fetch_url(url, expected_format=args.format, timeout=args.timeout)
    manifest = build_manifest(
        source_id=args.source_id,
        requested_url=url,
        final_url=final_url,
        content=data,
        dataset_version=args.dataset_version,
        etag=headers.get("ETag"),
        last_modified=headers.get("Last-Modified"),
        mime_type=headers.get("Content-Type"),
        data_format=args.format,
        crs=args.crs,
        parser_version=args.parser_version,
        source_metadata=_source_metadata(source),
        query_text=args.query,
    )
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "wb") as handle:
        handle.write(canonical_json(manifest))
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def compare(args: argparse.Namespace) -> int:
    with open(args.old, encoding="utf-8") as handle:
        old = json.load(handle)
    with open(args.new, encoding="utf-8") as handle:
        new = json.load(handle)
    report = diff_manifests(old, new)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if report["status"] == "changed" and args.fail_on_change else 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("snapshot", help="download and write one provenance manifest")
    s.add_argument("source_id")
    s.add_argument("--url")
    s.add_argument("--format", required=True)
    s.add_argument("--output", required=True)
    s.add_argument("--registry", default=os.path.join(ROOT, "data", "network", "sources.json"))
    s.add_argument("--dataset-version")
    s.add_argument("--crs")
    s.add_argument("--parser-version", default="raw/v1")
    s.add_argument("--query", help="OSM/other query text; only its SHA-256 is stored")
    s.add_argument("--timeout", type=float, default=30.0)
    s.set_defaults(func=snapshot)

    d = sub.add_parser("diff", help="compare two provenance manifests")
    d.add_argument("old")
    d.add_argument("new")
    d.add_argument("--fail-on-change", action="store_true")
    d.set_defaults(func=compare)
    return p


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

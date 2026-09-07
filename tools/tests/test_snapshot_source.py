#!/usr/bin/env python3
"""Testy `tools/data/snapshot_source.py` — modułu, który do 02.09.2026 nie miał żadnych.

Audyt mutacyjny: 21 z 21 mutantów przeżyło, bo nie importował go ani jeden test,
ani jeden workflow. To narzędzie zapisuje manifesty proweniencji, które trafiają
do repo — czyli decyduje o tym, co repo twierdzi o pochodzeniu swoich danych.

Testy nie ruszają sieci poza pętlą zwrotną: `snapshot` jest sprawdzany na lokalnym
serwerze HTTP, tak samo jak `fetch_url` w `test_all.py`.
"""
import argparse
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import snapshot_source as S  # noqa: E402


def _registry(rows):
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump({"sources": rows}, handle, ensure_ascii=False)
    handle.close()
    return handle.name


def _write(data):
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(data, handle, ensure_ascii=False)
    handle.close()
    return handle.name


# --- parser CLI ----------------------------------------------------------------


def test_snapshot_source_parser_requires_a_subcommand():
    """Bez podkomendy narzędzie ma się zatrzymać, a nie wybrać domyślną."""
    try:
        S.parser().parse_args([])
    except SystemExit:
        pass
    else:
        raise AssertionError("brak podkomendy przeszedł")


def test_snapshot_source_parser_defaults_are_pinned():
    """Domyślne wartości CLI to jedyne, co realnie dostaje pipeline.

    `--format` i `--output` są wymagane świadomie: format decyduje o kontroli
    magic bytes w `validate_payload`, a bez ścieżki manifest nie miałby gdzie
    powstać. Gdyby któryś przestał być wymagany, narzędzie zapisywałoby manifest
    z niezweryfikowaną treścią.
    """
    args = S.parser().parse_args(
        ["snapshot", "stib_gtfs", "--format", "zip", "--output", "/tmp/x.json"])
    assert args.command == "snapshot"
    assert args.parser_version == "raw/v1", args.parser_version
    assert args.timeout == 30.0, args.timeout
    assert args.registry.endswith(os.path.join("data", "network", "sources.json")), args.registry
    assert args.url is None and args.crs is None and args.query is None
    assert args.func is S.snapshot

    for missing in (["snapshot", "stib_gtfs", "--output", "/tmp/x.json"],
                    ["snapshot", "stib_gtfs", "--format", "zip"]):
        try:
            S.parser().parse_args(missing)
        except SystemExit:
            continue
        raise AssertionError(f"brakujący argument przeszedł: {missing}")


def test_snapshot_source_diff_defaults_to_not_failing_on_change():
    """`--fail-on-change` musi być decyzją wołającego, nie stanem domyślnym."""
    args = S.parser().parse_args(["diff", "a.json", "b.json"])
    assert args.fail_on_change is False
    assert args.func is S.compare
    assert S.parser().parse_args(["diff", "a.json", "b.json", "--fail-on-change"]).fail_on_change


# --- metadane źródła -----------------------------------------------------------


def test_snapshot_source_copies_only_the_five_declared_source_fields():
    """Do manifestu wchodzi biała lista pól, a nie cały wiersz rejestru.

    To nie jest kosmetyka: manifesty są commitowane, więc gdyby przepisywany był
    cały wiersz, każde pole dopisane kiedyś do `sources.json` — także takie
    z tokenem albo adresem wewnętrznym — wjeżdżałoby do repo razem z nim.
    """
    row = {
        "publisher": "STIB", "dataset": "GTFS", "license": "CC-BY",
        "license_status": "compatible", "checked_at": "2026-08-31",
        "download_url": "https://example.test/a.zip",
        "internal_note": "TAJNE", "auth_token": "sekret",
    }
    meta = S._source_metadata(row)

    assert meta == {
        "publisher": "STIB", "dataset": "GTFS", "license": "CC-BY",
        "license_status": "compatible", "checked_at": "2026-08-31",
    }, meta
    assert "TAJNE" not in json.dumps(meta) and "sekret" not in json.dumps(meta)


def test_snapshot_source_metadata_skips_fields_the_row_does_not_have():
    """Brakujące pole ma zniknąć, a nie wejść jako None — inaczej manifest kłamie."""
    meta = S._source_metadata({"publisher": "STIB"})
    assert meta == {"publisher": "STIB"}, meta
    assert "license" not in meta


# --- bramki przed pobraniem ----------------------------------------------------


def _snapshot_args(**overrides):
    args = dict(source_id="brak", url=None, format="json", output="/tmp/nieuzywane.json",
                registry=None, dataset_version=None, crs=None, parser_version="raw/v1",
                query=None, timeout=2.0)
    args.update(overrides)
    return argparse.Namespace(**args)


def test_snapshot_source_unknown_source_id_stops_before_downloading():
    registry = _registry([{"id": "stib_gtfs", "url": "https://example.test/a.zip"}])
    try:
        S.snapshot(_snapshot_args(source_id="nie_ma_takiego", registry=registry))
    except SystemExit as error:
        assert "nie_ma_takiego" in str(error), error
    else:
        raise AssertionError("nieznany source_id przeszedł")
    finally:
        os.unlink(registry)


def test_snapshot_source_without_any_url_refuses_instead_of_guessing():
    """Źródło bez URL-a nie dostaje adresu domyślnego ani zgadniętego."""
    registry = _registry([{"id": "bez_url", "publisher": "STIB"}])
    try:
        S.snapshot(_snapshot_args(source_id="bez_url", registry=registry))
    except SystemExit as error:
        assert "URL" in str(error), error
    else:
        raise AssertionError("źródło bez URL-a przeszło")
    finally:
        os.unlink(registry)


# --- pełny przebieg na pętli zwrotnej ------------------------------------------


def test_snapshot_source_writes_a_manifest_that_matches_the_payload():
    """Manifest ma opisywać to, co realnie przyszło z sieci."""
    payload = b'{"ok":true}'

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("ETag", '"abc"')
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    registry = _registry([{"id": "lokalne", "publisher": "STIB", "dataset": "test",
                           "license": "CC-BY", "license_status": "compatible",
                           "checked_at": "2026-08-31",
                           "url": f"http://127.0.0.1:{server.server_port}/a.json",
                           "internal_note": "TAJNE"}])
    out = os.path.join(tempfile.mkdtemp(), "manifest.json")
    try:
        code = S.snapshot(_snapshot_args(
            source_id="lokalne", registry=registry, output=out,
            query="[out:json];way[railway=subway];out;"))
        assert code == 0, code

        with open(out, encoding="utf-8") as handle:
            manifest = json.load(handle)

        import hashlib
        assert manifest["content_sha256"] == hashlib.sha256(payload).hexdigest()
        assert manifest["size_bytes"] == len(payload)
        assert manifest["source_id"] == "lokalne"
        assert manifest["format"] == "json"
        # Zapytanie jest hashowane, nie zapisywane — i nic z wiersza rejestru poza
        # białą listą nie wjeżdża do pliku, który idzie do repo.
        assert len(manifest["query_sha256"]) == 64 and "query" not in manifest
        assert "TAJNE" not in json.dumps(manifest)
        assert manifest["source_metadata"]["publisher"] == "STIB"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        os.unlink(registry)


# --- porównanie manifestów -----------------------------------------------------


def _manifest(content):
    import provenance as P
    return P.build_manifest(
        source_id="stib_gtfs", requested_url="https://example.test/a.json",
        final_url="https://example.test/a.json", content=content,
        retrieved_at="2026-09-01T00:00:00Z", data_format="json")


def test_snapshot_source_diff_returns_two_only_when_asked_to_fail():
    """Kod wyjścia 2 jest bramką CI — musi zależeć od zmiany I od flagi."""
    old = _write(_manifest(b'{"x":1}'))
    new = _write(_manifest(b'{"x":2}'))
    same = _write(_manifest(b'{"x":1}'))
    try:
        changed = argparse.Namespace(old=old, new=new, fail_on_change=True)
        assert S.compare(changed) == 2

        quiet = argparse.Namespace(old=old, new=new, fail_on_change=False)
        assert S.compare(quiet) == 0, "bez flagi zmiana ma być raportem, nie błędem"

        unchanged = argparse.Namespace(old=old, new=same, fail_on_change=True)
        assert S.compare(unchanged) == 0, "identyczna treść nie może wywracać CI"
    finally:
        for path in (old, new, same):
            os.unlink(path)

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

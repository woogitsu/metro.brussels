#!/usr/bin/env python3
"""Manifest proweniencji jest nadpisywany TYLKO przy zmianie tresci zrodla.

**Skad ta bramka.** 6.D12 (#295) zmierzyla, ze `retrieved_at` zmienia sie przy KAZDYM
uruchomieniu fetchera — takze w trybie `--offline`, gdzie nic nie jest pobierane —
wiec plik w `data/` rozjezdzal sie z repozytorium bez zmiany tresci zrodla, a
`CLAUDE.md` §4.6 mowi, ze `data/` jest tylko do odczytu. 6.D16 (#311) poprawila zdanie
w dokumencie, ktore dla dwoch miejsc bylo nieprawda. Wlasciciel wybral 06.09.2026
wariant **C** z `reports/zapisy-do-data.md` §3: zmieniaja sie NARZEDZIA, nie regula.

**Kryterium jest waskie i to jest cala jego tresc.** Nadpisanie zalezy WYLACZNIE od
`content_sha256`, a nie od calego `diff_manifests`. Pytanie, czy zmiana innych pol przy
niezmienionej tresci tez ma nadpisywac plik, wariant C dopiero otwiera — i nalezy do
wlasciciela. Test `test_a_changed_side_field_alone_does_not_rewrite` przybija ten waski
zakres, zeby nikt nie rozszerzyl go po cichu przy okazji czegos innego.
"""
import json
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import provenance as P  # noqa: E402

FETCHERY = ("tools/track/fetch_gtfs.py", "tools/track/fetch_stib_shapes.py")


def _manifest(sha="a" * 64, **extra):
    base = {"content_sha256": sha, "source_id": "test", "retrieved_at": "2026-09-06T00:00:00Z"}
    base.update(extra)
    return base


def test_a_missing_file_is_created():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "m.json")
        assert P.write_manifest_if_changed(path, _manifest()) == "utworzony"
        assert os.path.isfile(path)


def test_the_same_content_leaves_the_file_untouched():
    """Nie chodzi o to, ze plik ma te sama tresc — ma NIE ZOSTAC DOTKNIETY.
    Zapis identycznych bajtow tez zmienia czas modyfikacji i tez wyglada w narzedziach
    jak praca, ktorej nie bylo."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "m.json")
        P.write_manifest_if_changed(path, _manifest())
        przed = os.stat(path)
        stan = P.write_manifest_if_changed(path, _manifest(retrieved_at="2026-09-06T23:59:59Z"))
        po = os.stat(path)
        assert stan == "bez zmian", stan
        assert (przed.st_mtime_ns, przed.st_size) == (po.st_mtime_ns, po.st_size)
        assert json.load(open(path, encoding="utf-8"))["retrieved_at"] == "2026-09-06T00:00:00Z"


def test_changed_content_rewrites():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "m.json")
        P.write_manifest_if_changed(path, _manifest())
        assert P.write_manifest_if_changed(path, _manifest(sha="b" * 64)) == "zmieniony"
        assert json.load(open(path, encoding="utf-8"))["content_sha256"] == "b" * 64


def test_a_changed_side_field_alone_does_not_rewrite():
    """Waski zakres wariantu C, przybity celowo. `dataset_validity` jest w `tracked`
    `diff_manifests`, wiec `status` bylby `changed` — ale `source_changed` nie, i to
    ono rozstrzyga. Rozszerzenie tego kryterium jest decyzja wlasciciela."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "m.json")
        P.write_manifest_if_changed(path, _manifest(dataset_version="1"))
        stan = P.write_manifest_if_changed(path, _manifest(dataset_version="2"))
        assert stan == "bez zmian", stan


def test_both_fetchers_go_through_the_shared_helper():
    """Dwie kopie tej samej reguly rozjechalyby sie przy pierwszej zmianie."""
    for nazwa in FETCHERY:
        with open(os.path.join(ROOT, nazwa), encoding="utf-8") as handle:
            zrodlo = handle.read()
        assert "write_manifest_if_changed" in zrodlo, nazwa
        assert "handle.write(P.canonical_json(manifest))" not in zrodlo, (
            nazwa + " nadal zapisuje manifest bezwarunkowo")


def test_both_fetchers_say_when_they_did_not_write():
    """Wariant C zabiera sygnal, ktory dawal `git diff`. Komunikat go zastepuje —
    bez niego przebieg bez zmian jest nieodroznialny od przebiegu, ktorego nie bylo."""
    for nazwa in FETCHERY:
        with open(os.path.join(ROOT, nazwa), encoding="utf-8") as handle:
            zrodlo = handle.read()
        assert "bez zmian" in zrodlo, nazwa

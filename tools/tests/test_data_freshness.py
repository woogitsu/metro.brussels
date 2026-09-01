#!/usr/bin/env python3
"""Testy kontroli świeżości danych. Bez sieci, bez pytest, bez zależności od dzisiejszej daty."""
import datetime
import json
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import data_freshness as DF  # noqa: E402

TODAY = datetime.date(2026, 9, 1)


def _write(directory, name, payload):
    os.makedirs(os.path.join(directory, "data"), exist_ok=True)
    path = os.path.join(directory, "data", name)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return path


def test_freshness_parses_both_date_formats():
    assert DF.parse_date("28/08/2026") == datetime.date(2026, 8, 28)
    assert DF.parse_date("2026-09-01T10:48:05Z") == datetime.date(2026, 9, 1)
    assert DF.parse_date("2026-09-01") == datetime.date(2026, 9, 1)
    assert DF.parse_date("") is None
    assert DF.parse_date("31/02/2026") is None
    assert DF.parse_date(None) is None


def test_freshness_finds_a_window_nested_in_dataset_validity():
    """Klucze okna siedzą o poziom głębiej, w słowniku `dataset_validity`."""
    document = {"source": {"dataset_validity": {"date_debut": ["02/03/2026"],
                                                "date_fin": ["28/08/2026"]}}}
    found = DF.collect(document)
    assert found, "okno ważności nieznalezione"
    _where, start, end = found[0]
    assert start == datetime.date(2026, 3, 2) and end == datetime.date(2026, 8, 28)


def test_freshness_marks_expired_and_counts_days():
    with tempfile.TemporaryDirectory() as directory:
        _write(directory, "a.json", {"source": {"dataset_validity": {"date_fin": ["28/08/2026"]},
                                                "retrieved_at": "2026-09-01T10:00:00Z"}})
        rows = DF.audit(DF.data_files(directory), TODAY)
    assert len(rows) == 1
    assert rows[0]["status"] == "przeterminowane"
    assert rows[0]["days_left"] == -4
    assert rows[0]["retrieved_after_expiry"] is True


def test_freshness_flags_the_window_that_closes_soon():
    with tempfile.TemporaryDirectory() as directory:
        _write(directory, "a.json", {"validity": {"valid_to": "2026-09-20"}})
        rows = DF.audit(DF.data_files(directory), TODAY)
    assert rows[0]["status"] == "kończy się" and rows[0]["days_left"] == 19


def test_freshness_leaves_current_data_alone():
    with tempfile.TemporaryDirectory() as directory:
        _write(directory, "a.json", {"validity": {"valid_to": "2027-01-01"}})
        rows = DF.audit(DF.data_files(directory), TODAY)
    assert rows[0]["status"] == "aktualne" and rows[0]["retrieved_after_expiry"] is False


def test_freshness_ignores_schema_files():
    with tempfile.TemporaryDirectory() as directory:
        _write(directory, "x.schema.json", {"validity": {"valid_to": "2020-01-01"}})
        assert DF.data_files(directory) == []


def test_freshness_deduplicates_the_same_window_repeated_in_one_file():
    """Manifest powtarza to samo okno w dwóch miejscach; raport ma je pokazać raz."""
    with tempfile.TemporaryDirectory() as directory:
        window = {"date_debut": ["02/03/2026"], "date_fin": ["28/08/2026"]}
        _write(directory, "a.json", {"dataset_validity": window,
                                     "shapefiles": {"dataset_validity": window}})
        rows = DF.audit(DF.data_files(directory), TODAY)
    assert len(rows) == 1, rows


def test_freshness_strict_mode_fails_only_on_expired():
    with tempfile.TemporaryDirectory() as directory:
        _write(directory, "a.json", {"validity": {"valid_to": "2020-01-01"}})
        try:
            DF.main(["--root", directory, "--today", "2026-09-01", "--strict"])
        except SystemExit as exc:
            assert "okien ważności" in str(exc)
        else:
            raise AssertionError("--strict powinno odrzucić przeterminowane dane")
        assert DF.main(["--root", directory, "--today", "2026-09-01"]) == 0


def test_freshness_committed_axis_declares_its_window():
    """Oś nie może po cichu stracić informacji o oknie ważności źródła."""
    path = os.path.join(ROOT, "data", "track", "L1_A.json")
    if not os.path.isfile(path):
        return
    document = json.load(open(path, encoding="utf-8"))
    windows = DF.collect(document)
    assert windows, "skomitowana oś nie deklaruje okna ważności źródła"
    assert DF.retrieved_at(document) is not None

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


def test_freshness_baseline_accepts_only_the_exact_known_expiry():
    with tempfile.TemporaryDirectory() as directory:
        path = _write(directory, "old.json", {"validity": {"valid_to": "2026-08-28"},
                                               "retrieved_at": "2026-09-01"})
        baseline = os.path.join(directory, "baseline.json")
        with open(baseline, "w", encoding="utf-8") as handle:
            json.dump({"windows": [{"file": "data/old.json", "valid_to": "2026-08-28",
                                    "retrieved_at": "2026-09-01"}]}, handle)
        args = ["--root", directory, "--today", "2026-09-25", "--strict",
                "--baseline", baseline]
        assert DF.main(args) == 0, "dokładnie znane okno ma przejść etap przejściowy"

        _write(directory, "new.json", {"validity": {"valid_to": "2026-09-01"}})
        try:
            DF.main(args)
        except SystemExit as exc:
            assert "nowych przeterminowanych okien ważności: 1" in str(exc), (
                "nowe wygasłe okno ma być nazwane w błędzie")
        else:
            raise AssertionError("nowe wygasłe okno musi zatrzymać CI")

        os.remove(os.path.join(directory, "data", "new.json"))
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"validity": {"valid_to": "2027-08-28"}}, handle)
        try:
            DF.main(args)
        except SystemExit as exc:
            assert "nieaktualnych wyjątków: 1" in str(exc), (
                "po odświeżeniu źródła lista wyjątków ma wymagać czyszczenia")
        else:
            raise AssertionError("po odświeżeniu źródła wyjątek trzeba usunąć")


def test_freshness_committed_baseline_matches_only_legacy_windows():
    baseline = os.path.join(ROOT, "tools", "track", "freshness-baseline.json")
    today = datetime.date(2026, 9, 25)
    rows = DF.audit(DF.data_files(ROOT), today)
    expired = {(r["file"], r["valid_to"], r["retrieved_at"])
               for r in rows if r["status"] == "przeterminowane"}
    assert len(expired) == 13, "liczba znanych wygasłych okien wymaga przeglądu"
    assert DF.known_expired(baseline) == expired, "baseline musi być zamknięta w obie strony"


def test_freshness_baseline_rejects_unknown_fields():
    with tempfile.TemporaryDirectory() as directory:
        baseline = os.path.join(directory, "baseline.json")
        with open(baseline, "w", encoding="utf-8") as handle:
            json.dump({"windows": [{"file": "data/old.json", "valid_to": "2026-08-28",
                                    "retrieved_at": "2026-09-01", "ignored": True}]}, handle)
        try:
            DF.known_expired(baseline)
        except ValueError as exc:
            assert str(exc).startswith("baseline row"), "błąd ma wskazywać wadliwy wiersz"
        else:
            raise AssertionError("dodatkowe pola nie mogą być cicho ignorowane")


def test_freshness_committed_axis_declares_its_window():
    """Oś nie może po cichu stracić informacji o oknie ważności źródła."""
    path = os.path.join(ROOT, "data", "track", "L1_A.json")
    if not os.path.isfile(path):
        return
    document = json.load(open(path, encoding="utf-8"))
    windows = DF.collect(document)
    assert windows, "skomitowana oś nie deklaruje okna ważności źródła"
    assert DF.retrieved_at(document) is not None

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

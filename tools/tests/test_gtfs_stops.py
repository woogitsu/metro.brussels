#!/usr/bin/env python3
"""Testy importera GTFS i normalizacji stacji metra (T-110). Bez sieci i bez pytest.

Feed testowy jest budowany w locie, więc testy nie zależą ani od internetu, ani od
14 MB archiwum STIB. Artefakt z prawdziwego feedu jest sprawdzany osobno, ale tylko
wtedy, gdy jest obecny w repo.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import fetch_gtfs  # noqa: E402
import normalize_stops as N  # noqa: E402
import provenance as P  # noqa: E402

STOPS_JSON = os.path.join(ROOT, "data", "network", "stops.json")
MANIFEST_JSON = os.path.join(ROOT, "data", "network", "gtfs-manifest.json")


def _csv(rows):
    if not rows:
        return ""
    header = list(rows[0].keys())
    out = io.StringIO()
    out.write(",".join(header) + "\n")
    for row in rows:
        out.write(",".join(str(row.get(k, "")) for k in header) + "\n")
    return out.getvalue()


def _feed(extra_stops=None, routes=None, stop_times=None, trips=None, translations=None):
    """Minimalny, ale realistyczny feed: 1 linia metra, 1 autobusowa."""
    routes = routes if routes is not None else [
        {"route_id": "M1", "route_short_name": "1", "route_long_name": "A - B", "route_type": "1"},
        {"route_id": "B99", "route_short_name": "99", "route_long_name": "BUS", "route_type": "3"},
    ]
    trips = trips if trips is not None else [
        {"trip_id": "t1", "route_id": "M1"}, {"trip_id": "t2", "route_id": "B99"}]
    stop_times = stop_times if stop_times is not None else [
        {"trip_id": "t1", "stop_id": "p1", "stop_sequence": "1"},
        {"trip_id": "t1", "stop_id": "p2", "stop_sequence": "2"},
        {"trip_id": "t2", "stop_id": "bus1", "stop_sequence": "1"},
    ]
    stops = [
        {"stop_id": "S1", "stop_name": "ALFA", "stop_lat": "50.85", "stop_lon": "4.35",
         "location_type": "1", "parent_station": ""},
        {"stop_id": "p1", "stop_name": "ALFA", "stop_lat": "50.8501", "stop_lon": "4.3501",
         "location_type": "0", "parent_station": "S1"},
        {"stop_id": "p2", "stop_name": "ALFA", "stop_lat": "50.8502", "stop_lon": "4.3502",
         "location_type": "0", "parent_station": "S1"},
        {"stop_id": "e1", "stop_name": "1 - Rue Test", "stop_lat": "50.8503", "stop_lon": "4.3503",
         "location_type": "2", "parent_station": "S1"},
        {"stop_id": "bus1", "stop_name": "BUS STOP", "stop_lat": "50.86", "stop_lon": "4.36",
         "location_type": "0", "parent_station": ""},
    ]
    stops.extend(extra_stops or [])
    translations = translations if translations is not None else [
        {"table_name": "stops", "field_name": "stop_name", "language": "fr",
         "translation": "Alfa", "field_value": "ALFA"},
        {"table_name": "stops", "field_name": "stop_name", "language": "nl",
         "translation": "Alfa NL", "field_value": "ALFA"},
    ]
    return {"agency.txt": _csv([{"agency_id": "1", "agency_name": "TEST"}]),
            "routes.txt": _csv(routes),
            "trips.txt": _csv(trips),
            "stop_times.txt": _csv(stop_times),
            "stops.txt": _csv(stops),
            "translations.txt": _csv(translations)}


def _zip(members, path):
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return path


def _normalize(members):
    tmp = tempfile.mkdtemp()
    try:
        path = _zip(members, os.path.join(tmp, "feed.zip"))
        with zipfile.ZipFile(path) as archive:
            return N.normalize(archive)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- normalizacja -------------------------------------------------------------

def test_gtfs_only_metro_routes_are_used():
    stations, summary, _ = _normalize(_feed())
    assert summary["metro_stations"] == 1
    assert [r["short_name"] for r in summary["metro_routes"]] == ["1"]
    assert all(s["name"] != "BUS STOP" for s in stations)


def test_gtfs_platforms_group_into_one_station():
    stations, summary, _ = _normalize(_feed())
    assert summary["metro_platform_records"] == 2
    assert len(stations[0]["platforms"]) == 2
    assert stations[0]["station_id"] == "S1"
    assert stations[0]["anchor"] == "gtfs_station_container"


def test_gtfs_station_count_follows_data_not_expectation():
    """Dodanie stacji w feedzie musi zmienić wynik — brak zaszytej listy nazw."""
    extra = [
        {"stop_id": "S2", "stop_name": "BETA", "stop_lat": "50.87", "stop_lon": "4.37",
         "location_type": "1", "parent_station": ""},
        {"stop_id": "p3", "stop_name": "BETA", "stop_lat": "50.8701", "stop_lon": "4.3701",
         "location_type": "0", "parent_station": "S2"},
    ]
    members = _feed(extra_stops=extra,
                    stop_times=[{"trip_id": "t1", "stop_id": "p1", "stop_sequence": "1"},
                                {"trip_id": "t1", "stop_id": "p3", "stop_sequence": "2"}])
    _stations, summary, _ = _normalize(members)
    assert summary["metro_stations"] == 2


def test_gtfs_translations_join_by_field_value():
    stations, _summary, _ = _normalize(_feed())
    assert stations[0]["name"] == "ALFA"
    assert stations[0]["name_fr"] == "Alfa"
    assert stations[0]["name_nl"] == "Alfa NL"


def test_gtfs_entrances_are_attached_to_station():
    stations, summary, _ = _normalize(_feed())
    assert summary["entrance_records"] == 1
    assert stations[0]["entrances"][0]["stop_id"] == "e1"


def test_gtfs_missing_coordinates_are_rejected_with_reason():
    extra = [{"stop_id": "p9", "stop_name": "ALFA", "stop_lat": "", "stop_lon": "",
              "location_type": "0", "parent_station": "S1"}]
    members = _feed(extra_stops=extra,
                    stop_times=[{"trip_id": "t1", "stop_id": "p1", "stop_sequence": "1"},
                                {"trip_id": "t1", "stop_id": "p9", "stop_sequence": "2"}])
    _stations, summary, rejected = _normalize(members)
    assert summary["rejected_records"] == 1
    assert rejected[0]["stop_id"] == "p9" and "współrzędne" in rejected[0]["reason"]


def test_gtfs_orphan_parent_station_is_reported():
    extra = [{"stop_id": "p8", "stop_name": "GAMMA", "stop_lat": "50.88", "stop_lon": "4.38",
              "location_type": "0", "parent_station": "NIE_ISTNIEJE"}]
    _stations, summary, rejected = _normalize(_feed(extra_stops=extra))
    assert any(r["kind"] == "orphan_parent" and r["stop_id"] == "p8" for r in rejected), rejected
    assert summary["rejected_records"] >= 1


def test_gtfs_platform_without_parent_becomes_flagged_station():
    extra = [{"stop_id": "p7", "stop_name": "DELTA", "stop_lat": "50.89", "stop_lon": "4.39",
              "location_type": "0", "parent_station": ""}]
    members = _feed(extra_stops=extra,
                    stop_times=[{"trip_id": "t1", "stop_id": "p1", "stop_sequence": "1"},
                                {"trip_id": "t1", "stop_id": "p7", "stop_sequence": "2"}])
    stations, summary, _ = _normalize(members)
    flagged = [s for s in stations if s["station_id"] == "p7"]
    assert flagged and flagged[0]["anchor"] == "orphan_platform"
    assert "anomaly" in flagged[0]
    assert summary["orphan_platforms"][0]["stop_id"] == "p7"
    assert summary["metro_station_containers"] == summary["metro_stations"] - 1


def test_gtfs_feed_without_metro_fails_loudly():
    members = _feed(routes=[{"route_id": "B99", "route_short_name": "99",
                             "route_long_name": "BUS", "route_type": "3"}])
    try:
        _normalize(members)
    except SystemExit as exc:
        assert "route_type=1" in str(exc)
    else:
        raise AssertionError("feed bez metra powinien zatrzymać normalizację")


def test_gtfs_output_is_byte_deterministic():
    first = P.canonical_json({"stations": _normalize(_feed())[0]})
    second = P.canonical_json({"stations": _normalize(_feed())[0]})
    assert first == second


# --- pobieranie i kontrola archiwum -------------------------------------------

def test_gtfs_incomplete_archive_is_rejected():
    tmp = tempfile.mkdtemp()
    try:
        path = _zip({"agency.txt": "agency_id\n1\n"}, os.path.join(tmp, "bad.zip"))
        try:
            fetch_gtfs.inspect_zip(path)
        except SystemExit as exc:
            assert "niekompletny GTFS" in str(exc)
        else:
            raise AssertionError("niekompletne archiwum powinno zostać odrzucone")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_gtfs_non_zip_is_rejected():
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "notzip.zip")
        with open(path, "wb") as handle:
            handle.write(b"<html>not a zip</html>")
        try:
            fetch_gtfs.inspect_zip(path)
        except SystemExit as exc:
            assert "ZIP" in str(exc)
        else:
            raise AssertionError("plik nie-ZIP powinien zostać odrzucony")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_gtfs_inspect_reports_feed_range():
    members = _feed()
    members["feed_info.txt"] = _csv([{"feed_publisher_name": "TEST", "feed_version": "v1",
                                      "feed_start_date": "20260831", "feed_end_date": "20260927"}])
    members["calendar.txt"] = _csv([{"service_id": "s1", "start_date": "20260831", "end_date": "20260927"}])
    tmp = tempfile.mkdtemp()
    try:
        info = fetch_gtfs.inspect_zip(_zip(members, os.path.join(tmp, "ok.zip")))
        assert info["feed_info"]["feed_version"] == "v1"
        assert info["calendar_range"] == {"start_date": "20260831", "end_date": "20260927", "services": 1}
        assert info["member_counts"]["stops.txt"] == 5
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- artefakt z prawdziwego feedu, jeżeli jest w repo --------------------------

def test_gtfs_committed_stops_json_is_consistent():
    if not os.path.isfile(STOPS_JSON):
        return
    doc = json.load(open(STOPS_JSON, encoding="utf-8"))
    summary = doc["summary"]
    assert doc["generator"] == "tools/track/normalize_stops.py"
    assert summary["metro_stations"] == len(doc["stations"])
    assert summary["metro_platform_records"] == sum(len(s["platforms"]) for s in doc["stations"])
    assert {r["short_name"] for r in summary["metro_routes"]} == {"1", "2", "5", "6"}
    for station in doc["stations"]:
        assert station["name"], station
        assert station["routes"], station
        assert 50.7 < station["lat"] < 51.0 and 4.2 < station["lon"] < 4.5, station
        for platform in station["platforms"]:
            assert platform["routes"], platform


def test_gtfs_committed_stops_json_keeps_original_names():
    if not os.path.isfile(STOPS_JSON):
        return
    doc = json.load(open(STOPS_JSON, encoding="utf-8"))
    names = {s["name_fr"] for s in doc["stations"]} | {s["name_nl"] for s in doc["stations"]}
    assert "Weststation" in names, "nazwy NL muszą zostać zachowane"
    assert not any("Stacja" in n for n in names), "nazwy nie mogą być tłumaczone na polski"


def test_gtfs_committed_manifest_has_provenance_and_no_secrets():
    if not os.path.isfile(MANIFEST_JSON):
        return
    manifest = json.load(open(MANIFEST_JSON, encoding="utf-8"))
    assert len(manifest["content_sha256"]) == 64
    assert manifest["source_id"] == "stib_gtfs"
    assert manifest["final_url"].startswith("https://")
    blob = json.dumps(manifest).lower()
    for secret in ("authorization", "subscription-key", "bearer ", "apikey", "api_key"):
        assert secret not in blob, secret


# --- main(): porównanie z deklaracją i skrót listy odrzuconych -------------------
#
# Przegląd mutacyjny z 03.09.2026 zostawił w tym module trzy ocalałe mutacje i
# wszystkie trzy siedzą w `main()`, poza `normalize()`. Testy wyżej wołają wyłącznie
# `normalize()`, więc cała warstwa raportowania — ta, która ma KRZYCZEĆ, gdy dane
# nie zgadzają się z `docs/00-network-data.md` — nie była dotknięta niczym.


def _run_main(members, declared, extra_argv=()):
    """`main()` na feedzie z pamięci, z podstawioną deklaracją liczby stacji.

    Zwraca `(dokument wynikowy, wypisany tekst)`. Nie dotyka `data/` — wszystkie
    trzy ścieżki (feed, wynik, sieć) idą do katalogu tymczasowego, a `--manifest`
    celowo wskazuje plik nieistniejący, żeby wynik nie zależał od stanu repo.
    """
    import contextlib
    tmp = tempfile.mkdtemp()
    try:
        gtfs = _zip(members, os.path.join(tmp, "feed.zip"))
        network = os.path.join(tmp, "lines.json")
        with open(network, "w", encoding="utf-8") as handle:
            json.dump({"network": {"metro_stations": declared}}, handle)
        out = os.path.join(tmp, "stops.json")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            N.main(["--gtfs", gtfs, "--out", out, "--network", network,
                    "--manifest", os.path.join(tmp, "brak-manifestu.json"), *extra_argv])
        with open(out, encoding="utf-8") as handle:
            return json.load(handle), buffer.getvalue()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_gtfs_declared_count_agreeing_with_the_data_is_not_reported_as_a_discrepancy():
    """`matches_declared` steruje jedynym ostrzeżeniem, jakie ten moduł ma wypisać.

    Zasada modułu brzmi: liczba stacji wychodzi z danych, a rozbieżność z
    `docs/00-network-data.md` jest RAPORTOWANA, nie naprawiana. Odwrócenie tego
    porównania zamienia raport w jego przeciwieństwo — narzędzie milczy dokładnie
    wtedy, gdy dane rozjechały się z dokumentacją, i alarmuje, gdy wszystko gra.
    Objaw jest niewidoczny w pliku wyjściowym: stacje są te same, zmienia się tylko
    jedno pole i jedna linia na wyjściu.

    Feed testowy daje jedną stację metra, więc obie strony granicy da się pokazać
    na tym samym feedzie: deklaracja 1 ma się zgadzać, deklaracja 2 nie.
    """
    document, printed = _run_main(_feed(), declared=1)
    assert document["summary"]["metro_stations"] == 1
    assert document["summary"]["declared_metro_stations"] == 1
    assert document["summary"]["matches_declared"] is True
    assert "[ROZBIEŻNOŚĆ]" not in printed, printed

    document, printed = _run_main(_feed(), declared=2)
    assert document["summary"]["matches_declared"] is False
    assert "[ROZBIEŻNOŚĆ]" in printed, printed
    assert "deklaruje 2 stacji" in printed, printed


def _orphans(count):
    """`count` peronów wskazujących na nieistniejącą stację — tyle samo odrzuceń."""
    return [{"stop_id": f"x{i}", "stop_name": f"SIEROTA {i}",
             "stop_lat": "50.9", "stop_lon": "4.4",
             "location_type": "0", "parent_station": "NIE_ISTNIEJE"}
            for i in range(count)]


def test_gtfs_rejected_list_is_cut_at_ten_and_says_how_many_are_left():
    """Wypisywanych jest pierwszych dziesięć odrzuceń; reszta ma być POLICZONA.

    Ta linia jest jedynym miejscem, z którego czytający dowiaduje się, że lista na
    ekranie jest ucięta i że pełna leży w `--report`. Bez niej dziesiąte odrzucenie
    wygląda jak ostatnie.

    Granica całkowitoliczbowa, więc trafiona wprost i z obu stron: przy DOKŁADNIE
    dziesięciu odrzuceniach dopisku ma nie być (`>= 10` wypisałoby „i 0 więcej"),
    przy jedenastu ma być i ma mówić „1" (`> 11` przemilczałoby to jedno).
    """
    document, printed = _run_main(_feed(extra_stops=_orphans(10)), declared=1)
    assert document["summary"]["rejected_records"] == 10
    assert printed.count("[ODRZUCONO]") == 10, printed
    assert "więcej" not in printed, printed

    document, printed = _run_main(_feed(extra_stops=_orphans(11)), declared=1)
    assert document["summary"]["rejected_records"] == 11
    assert "[ODRZUCONO] ... i 1 więcej" in printed, printed
    assert printed.count("[ODRZUCONO]") == 11, printed

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

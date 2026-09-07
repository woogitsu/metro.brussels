#!/usr/bin/env python3
"""Testy proweniencji rejestru stacji pakietu A (R-004). Bez sieci, bez pytest.

Rejestr `data/stations/package-a.json` jest zbiorem faktów, nie modelem. Te testy
pilnują trzech rzeczy, których nie widać gołym okiem w 250 kB JSON-a:

1. każdy fakt ma źródło albo jawnie mówi, że go nie ma;
2. nic, czego źródła nie potwierdzają, nie dostało wartości domyślnej —
   w szczególności żadnej głębokości, wysokości peronu ani wymiaru pomieszczenia;
3. stan docelowy przebudowy nigdy nie udaje stanu na 2026-08-31.

Testy czytają też `data/schema/station-registry.schema.json`, ale nie walidują nim
dokumentu: repo nie ma zależności `jsonschema`, więc te same niezmienniki są
sprawdzane wprost, a schemat jest kontrolowany osobno pod kątem deklaracji.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REGISTRY = os.path.join(ROOT, "data", "stations", "package-a.json")
SCHEMA = os.path.join(ROOT, "data", "schema", "station-registry.schema.json")
SOURCES = os.path.join(ROOT, "data", "network", "sources.json")
STOPS = os.path.join(ROOT, "data", "network", "stops.json")

AS_OF = "2026-08-31"
PACKAGE_A = {
    "GARE_DE_L_OUEST", "BEEKKANT", "ETANGS_NOIRS", "COMTE_DE_FLANDRE", "SAINTE_CATHERINE",
    "DE_BROUCKERE", "GARE_CENTRALE", "PARC", "ARTS_LOI", "MAELBEEK", "SCHUMAN", "MERODE",
}
# Stacje, dla których STIB nie udostępnia dziś tekstowego opisu planu dzielnicowego.
NO_VERBAL = {"DE_BROUCKERE", "ETANGS_NOIRS", "SAINTE_CATHERINE", "SCHUMAN"}
# Stacje, które muszą mieć rozdzielony stan 2026-08-31 i stan przyszły.
TIME_SPLIT = {"BEEKKANT", "GARE_CENTRALE", "PARC", "MAELBEEK"}
STATUSES = {"source_backed", "indicative", "conflict", "unknown"}
WORKS_STATES = {"stable", "under_construction", "planned_change", None}
# Fakt o zmiennym stanie stacji; source_backed wymaga tu `as_of`.
STATEFUL_KEYS = {"works_state", "fixed_stairs", "escalator", "lift", "metro_lines",
                 "step_free_street_to_platform", "lift_at_listed_exits",
                 "lift_count_station", "escalator_count_station"}
# Nazwy, pod którymi mogłaby się przemycić zmyślona geometria.
GEOMETRY_WORDS = ("depth", "height", "length", "width", "area", "glebokosc", "wysokosc")


def _load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _registry():
    return _load(REGISTRY)


def _source_ids():
    return {row["id"] for row in _load(SOURCES)["sources"]}


def _walk_facts(node, path="$"):
    """Zwraca (ścieżka, fakt) dla każdego słownika, który wygląda jak koperta faktu."""
    if isinstance(node, dict):
        if "status" in node and "source_ids" in node:
            yield path, node
        for key, value in node.items():
            yield from _walk_facts(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk_facts(value, f"{path}[{i}]")


def _stations():
    return {s["station_id"]: s for s in _registry()["stations"]}


def _exit_facts(exit_record):
    return {k: v for k, v in exit_record.items()
            if k in ("exit_label", "position", "street", "fixed_stairs", "escalator", "lift")}


def test_package_a_registry_holds_exactly_twelve_stations():
    reg = _registry()
    ids = [s["station_id"] for s in reg["stations"]]
    assert reg["package"] == "A" and reg["as_of"] == AS_OF, (reg["package"], reg["as_of"])
    assert len(ids) == 12, len(ids)
    assert len(set(ids)) == 12, "zduplikowany station_id"
    assert set(ids) == PACKAGE_A, set(ids) ^ PACKAGE_A


def test_every_station_declares_as_of_and_works_state():
    for sid, station in _stations().items():
        assert station["as_of"] == AS_OF, (sid, station["as_of"])
        works = station["works_state"]
        assert works["value"] in WORKS_STATES, (sid, works["value"])
        if works["status"] == "unknown":
            assert works["value"] is None, sid
        else:
            assert works["as_of"] == AS_OF, sid


def test_every_fact_envelope_is_well_formed():
    for path, fact in _walk_facts(_registry()):
        assert fact["status"] in STATUSES, (path, fact["status"])
        if fact["status"] == "unknown":
            assert fact.get("value") is None, path
            assert fact["source_ids"] == [], path
            assert fact.get("reason"), f"{path}: unknown bez uzasadnienia"
        elif fact["status"] == "conflict":
            assert fact.get("value") is None, path
            assert fact.get("conflict_id"), path
            assert len(fact.get("candidates", [])) >= 2, path
            assert len(fact["source_ids"]) >= 2, path
        else:
            assert fact["source_ids"], f"{path}: {fact['status']} bez źródła"


def test_facts_about_changing_state_carry_as_of():
    """Wyposażenie stacji i stan robót zmieniają się w czasie, więc potwierdzony fakt
    o nich bez daty jest bezużyteczny dla wariantu historycznego."""
    checked = 0
    for path, fact in _walk_facts(_registry()):
        leaf = path.rsplit(".", 1)[-1]
        if leaf in STATEFUL_KEYS and fact["status"] in ("source_backed", "indicative"):
            assert fact.get("as_of") == AS_OF, f"{path}: fakt o zmiennym stanie bez as_of"
            checked += 1
    assert checked >= 100, checked


def test_every_source_id_in_registry_is_registered_in_sources_json():
    known = _source_ids()
    reg = _registry()
    used = set()
    for _, fact in _walk_facts(reg):
        used.update(fact["source_ids"])
        for cand in fact.get("candidates", []):
            used.add(cand["source_id"])
    for station in reg["stations"]:
        for ex in station["exits"]:
            used.update(rec["source_id"] for rec in ex["source_records"])
        for group in ("temporary_elements", "future_changes"):
            for item in station[group]:
                used.update(item["source_ids"])
    for conflict in reg["conflicts"]:
        used.update(conflict["source_ids"])
    missing = used - known
    assert not missing, sorted(missing)
    assert "stib_district_plan_verbal" in used and "stib_gtfs" in used


def test_r004_sources_have_required_audit_fields():
    by_id = {row["id"]: row for row in _load(SOURCES)["sources"]}
    ids = {"stib_district_plans", "stib_district_plan_verbal", "stib_prm_access",
           "stib_works_gare_centrale", "stib_traffic_gare_centrale_bus_stops",
           "stib_works_maelbeek", "stib_works_beekkant", "stib_traffic_beekkant_bus87",
           "stib_works_parc", "stib_commercial_spaces", "metro_bxl_issue_16_note"}
    required = {"id", "class", "publisher", "url", "role", "license", "update_frequency",
                "access", "as_of", "checked_at", "limitations"}
    for sid in ids:
        assert sid in by_id, sid
        row = by_id[sid]
        missing = required - set(row)
        assert not missing, (sid, sorted(missing))
        assert isinstance(row["role"], list) and row["role"], sid
        assert isinstance(row["access"], dict) and row["access"], sid
        assert row["url"].startswith("https://"), sid
    assert by_id["metro_bxl_issue_16_note"]["class"] == "secondary_reference"


def test_every_exit_element_has_a_source_or_is_unknown():
    total = 0
    for sid, station in _stations().items():
        assert station["exits"], sid
        assert station["exit_count"]["value"] == len(station["exits"]), sid
        for ex in station["exits"]:
            total += 1
            assert ex["source_records"], ex["exit_id"]
            for key, fact in _exit_facts(ex).items():
                assert fact["status"] in STATUSES, (ex["exit_id"], key)
                if fact["status"] != "unknown":
                    assert fact["source_ids"], (ex["exit_id"], key)
    assert total == 54, total


def test_exit_and_station_ids_are_unique():
    seen = set()
    for station in _registry()["stations"]:
        for ex in station["exits"]:
            assert ex["exit_id"] not in seen, ex["exit_id"]
            assert ex["exit_id"].startswith(station["station_id"] + "_"), ex["exit_id"]
            seen.add(ex["exit_id"])


def test_duplicate_exit_labels_are_kept_not_deduplicated():
    """Sainte-Catherine ma pięć rekordów „1”, Gare Centrale dwa „3”. Scalenie ich po
    numerze skasowałoby realne wyjścia, więc rejestr musi je zachować."""
    stations = _stations()
    labels = [e["exit_label"]["value"] for e in stations["SAINTE_CATHERINE"]["exits"]]
    assert labels.count("1") == 5, labels
    gc = [e["exit_label"]["value"] for e in stations["GARE_CENTRALE"]["exits"]]
    assert gc.count("3") == 2, gc
    ids = {e["exit_id"] for e in stations["SAINTE_CATHERINE"]["exits"]}
    assert len(ids) == 5, ids


def test_no_guessed_geometry_anywhere_in_the_registry():
    for sid, station in _stations().items():
        gaps = station["geometry_not_in_this_registry"]
        assert gaps, sid
        for key, fact in gaps.items():
            assert fact["status"] == "unknown", (sid, key)
            assert fact["value"] is None, (sid, key)
            assert fact.get("reason"), (sid, key)
    for path, fact in _walk_facts(_registry()):
        leaf = path.rsplit(".", 1)[-1].lower()
        if any(word in leaf for word in GEOMETRY_WORDS):
            assert not isinstance(fact.get("value"), (int, float)), path


def test_platform_configuration_is_never_invented():
    for sid, station in _stations().items():
        cfg = station["platform_configuration"]
        assert cfg["status"] == "unknown" or cfg["value"] in ("island", "side", "interchange"), sid
        if cfg["status"] == "unknown":
            assert cfg.get("reason"), sid


def test_stations_under_works_split_historical_and_future_state():
    for sid in TIME_SPLIT:
        station = _stations()[sid]
        assert station["works_state"]["status"] != "unknown", sid
        assert station["works_state"]["as_of"] == AS_OF, sid
        assert station["future_changes"], f"{sid}: brak zapisanych zmian przyszłych"
        variants = station["variants"]
        hist = variants["historical_2026_08_31"]
        assert hist["as_of"] == AS_OF, sid
        assert hist["includes_future_elements"] is False, sid
        assert variants["future_completed"]["active_at_2026_08_31"] is False, sid
        assert variants["future_completed"]["elements"], sid
        future = {f["element"] for f in station["future_changes"]}
        assert set(variants["future_completed"]["elements"]) == future, sid
        assert not (set(hist["temporary_elements"]) & future), f"{sid}: element przyszły w wariancie historycznym"


def test_future_elements_are_never_active_at_the_historical_as_of():
    for sid, station in _stations().items():
        for change in station["future_changes"]:
            assert change["exists_at_2026_08_31"] is False, (sid, change["element"])
            assert change["source_ids"], (sid, change["element"])
            date = change.get("earliest_known_date")
            assert date is None or date > AS_OF[:len(date)], (sid, change["element"], date)
        for temp in station["temporary_elements"]:
            assert temp["as_of"] == AS_OF, (sid, temp["element"])
            assert temp["source_ids"], (sid, temp["element"])


def test_stations_without_verbal_description_do_not_invent_equipment():
    for sid in NO_VERBAL:
        station = _stations()[sid]
        for ex in station["exits"]:
            for key in ("fixed_stairs", "escalator", "lift"):
                assert ex[key]["status"] == "unknown", (sid, ex["exit_id"], key)
        assert station["accessibility"]["lift_at_listed_exits"]["status"] == "unknown", sid


def test_conflicting_sources_are_recorded_instead_of_overwritten():
    reg = _registry()
    declared = {c["conflict_id"]: c for c in reg["conflicts"]}
    assert len(declared) == len(reg["conflicts"]), "zduplikowany conflict_id"
    assert declared, "rejestr bez sekcji konfliktów"
    referenced = set()
    for _, fact in _walk_facts(reg):
        if fact["status"] == "conflict":
            referenced.add(fact["conflict_id"])
    unknown = referenced - set(declared)
    assert not unknown, sorted(unknown)
    for cid, conflict in declared.items():
        assert conflict["description"] and conflict["resolution"], cid
        assert conflict["kind"] in {"street_assignment", "numbering", "coverage", "scope",
                                    "unverified_claim"}, cid
        assert conflict["source_ids"], cid
        if conflict["kind"] == "street_assignment":
            assert len(conflict["source_ids"]) >= 2, cid
    # Sprzeczność ulic Arts-Loi i Gare de l'Ouest musi być widoczna przy samych wyjściach.
    assert "C-ARTS_LOI-STREET-1" in referenced
    assert "C-GARE_DE_L_OUEST-STREET-1" in referenced


def test_unverified_claim_about_missing_descriptions_is_not_promoted_to_fact():
    reg = _registry()
    claim = [c for c in reg["conflicts"] if c["kind"] == "unverified_claim"]
    assert claim, "brak zapisu o niepotwierdzonych listach wyjść"
    assert "metro_bxl_issue_16_note" in claim[0]["source_ids"]
    for _, fact in _walk_facts(reg):
        if fact["status"] in ("source_backed", "indicative"):
            assert "metro_bxl_issue_16_note" not in fact["source_ids"], \
                "notatka badawcza awansowała do faktu"


def test_entrance_positions_come_from_the_committed_gtfs_snapshot():
    """Każda współrzędna wejścia w rejestrze musi istnieć w data/network/stops.json."""
    by_name = {s["name"]: s for s in _load(STOPS)["stations"]}
    gtfs_points = {(e["lat"], e["lon"]) for st in by_name.values() for e in st["entrances"]}
    checked = 0
    for sid, station in _stations().items():
        for ex in station["exits"]:
            pos = ex["position"]
            if pos["status"] == "unknown":
                continue
            assert pos["source_ids"] == ["stib_gtfs"], (sid, ex["exit_id"])
            assert (pos["lat"], pos["lon"]) in gtfs_points, (sid, ex["exit_id"])
            checked += 1
    assert checked == 47, checked


def test_metro_lines_match_the_committed_gtfs_snapshot():
    by_id = {s["station_id"]: s for s in _load(STOPS)["stations"]}
    for sid, station in _stations().items():
        gtfs = by_id[station["gtfs_station_id"]]
        assert station["metro_lines"]["value"] == gtfs["routes"], sid
        assert station["gtfs_platform_records"]["value"] == len(gtfs["platforms"]), sid
        assert station["position"]["lat"] == gtfs["lat"], sid
        assert station["position"]["lon"] == gtfs["lon"], sid


def test_parc_equipment_counts_do_not_come_from_the_exit_list():
    """Opis wyjść zna jedno wyjście Parc; projekt STIB podaje 4 windy i 7 schodów
    ruchomych. Liczby stacyjne muszą mieć źródło projektowe, nie listę wyjść."""
    parc = _stations()["PARC"]
    assert len(parc["exits"]) == 1, len(parc["exits"])
    acc = parc["accessibility"]
    assert acc["lift_count_station"]["value"] == 4
    assert acc["escalator_count_station"]["value"] == 7
    assert acc["lift_count_station"]["source_ids"] == ["stib_works_parc"]
    assert acc["escalator_count_station"]["source_ids"] == ["stib_works_parc"]
    assert acc["step_free_street_to_platform"]["value"] is True
    assert acc["step_free_street_to_platform"]["as_of"] == AS_OF
    ids = {c["conflict_id"] for c in _registry()["conflicts"]}
    assert "C-PARC-EXITS-VS-EQUIPMENT" in ids


def test_gare_centrale_is_not_recorded_as_accessible_at_the_historical_as_of():
    gc = _stations()["GARE_CENTRALE"]
    assert gc["works_state"]["value"] == "under_construction"
    step_free = gc["accessibility"]["step_free_street_to_platform"]
    assert step_free["value"] is False and step_free["as_of"] == AS_OF
    assert step_free["source_ids"] == ["stib_works_gare_centrale"]
    assert gc["temporary_elements"], "brak listy elementów tymczasowych"
    assert gc["railway_interchange"]["status"] == "source_backed"


def test_access_graph_never_claims_a_confirmed_way_to_the_platform():
    for sid, station in _stations().items():
        graph = station["access_graph"]
        assert graph["completeness"] == "partial", sid
        to_platform = [e for e in graph["edges"] if e["to"] == "platform_level"]
        assert to_platform, sid
        for edge in to_platform:
            assert edge["status"] == "unknown", (sid, edge)
        street_nodes = [n for n in graph["nodes"] if n["level"] == "street"]
        assert len(street_nodes) == len(station["exits"]), sid


def test_station_registry_schema_declares_the_invariants():
    schema = _load(SCHEMA)
    assert schema["$id"].endswith("station-registry.schema.json")
    required = set(schema["required"])
    assert {"registry_version", "package", "as_of", "checked_at", "conflicts", "stations"} <= required
    defs = schema["$defs"]
    assert set(defs["fact"]["properties"]["status"]["enum"]) == STATUSES
    assert defs["future_change"]["properties"]["exists_at_2026_08_31"]["const"] is False
    geometry = defs["station"]["properties"]["geometry_not_in_this_registry"]
    assert geometry["additionalProperties"]["allOf"][1]["properties"]["status"]["const"] == "unknown"
    station_required = set(defs["station"]["required"])
    assert {"as_of", "works_state", "exits", "future_changes", "variants",
            "geometry_not_in_this_registry"} <= station_required

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

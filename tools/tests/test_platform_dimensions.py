#!/usr/bin/env python3
"""R-007: wymiary peronu i głębokości z EIE — to, co research ustalił, przypięte testem.

Raport sam z siebie niczego nie pilnuje. Te testy stoją nad trzema ustaleniami,
z których każde da się po cichu zepsuć edycją danych:

1. wysokość peronu 1,03 m jest tą SAMĄ liczbą co wysokość podłogi M7 z rejestru —
   nie kopią, tylko tożsamością, bo cały wniosek stoi na zdaniu STIB
   „le plancher des M7 sera 100 % plat, à hauteur du quai";
2. długość peronu zostaje `unknown`, a ograniczenie 94,0 m ≤ L ≤ obrys stacji jest
   ograniczeniem, nie wymiarem;
3. głębokości z EIE noszą przy sobie oba przekształcenia, którym podlegały.
"""
import csv
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "physics"))

REPORT = os.path.join(ROOT, "reports", "R-007-platform-dimensions.md")
DEPTHS = os.path.join(ROOT, "data", "network", "station-depths.csv")

#: Głębokości peronu podane przez EIE, w metrach poniżej powierzchni.
EIE_PLATFORM_DEPTHS_M = {"De Brouckère": 11.0, "Arts-Loi": 11.0, "Parc": 19.0}

#: Najciaśniejsze górne ograniczenie długości peronu w pakiecie A (obrys stacji Parc).
TIGHTEST_STATION_FOOTPRINT_M = 109.1


def _json(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as handle:
        return json.load(handle)


def _depth_rows():
    with open(DEPTHS, encoding="utf-8") as handle:
        lines = [line for line in handle if not line.startswith("#")]
    rows = list(csv.DictReader(lines))
    assert rows, "plik głębokości jest pusty"
    return rows


def _sources():
    return {source["id"]: source for source in _json("data", "network", "sources.json")["sources"]}


# --- wysokość peronu -----------------------------------------------------------


def test_platform_height_is_the_same_number_as_the_m7_floor_height():
    """Wysokość peronu NIE jest osobną liczbą — jest wysokością podłogi M7.

    Cały wniosek stoi na jednym zdaniu STIB: podłoga M7 jest „à hauteur du quai".
    Gdyby ktoś wpisał wysokość peronu jako osobną stałą, dałoby się ją przestawić
    bez ruszania rejestru — i repo miałoby dwie prawdy o tej samej wielkości.
    """
    spec = _json("data", "vehicle", "m7-spec.json")
    floor = spec["parameters"]["floor_height_m"]
    assert floor["value"] == 1.03, floor
    assert floor["status"] == "spec", floor
    assert floor["source_id"], "wysokość podłogi bez źródła nie może nieść wysokości peronu"


def test_platform_height_sources_are_registered_and_official():
    """Dwie niezależne publikacje STIB, obie klasy `official_stib`."""
    sources = _sources()
    for source_id in ("stib_m7_press_kit_2020_07_13", "stib_m7_press_kit_2021_05_26"):
        source = sources[source_id]
        assert source["class"] == "official_stib", source_id
        assert "platform_height_inference" in source["role"], source_id
        # Zastrzeżenie musi jechać razem z liczbą: STIB nie mówi, względem czego mierzy.
        assert "NIE deklaruje" in source["limitations"], source_id


def test_report_keeps_the_caveat_next_to_the_number():
    """Raport nie może zgubić zastrzeżenia — bez niego 1,03 m wygląda na pomiar."""
    with open(REPORT, encoding="utf-8") as handle:
        text = handle.read()
    assert "à hauteur du quai" in text
    assert "konwencja\nbranżowa, nie zdanie STIB" in text or "konwencja branżowa" in text
    # Pułapka OSM: 0,76 m to perony SNCB, nie metro.
    assert "0.76" in text and "SNCB" in text


# --- długość peronu ------------------------------------------------------------


def test_platform_length_stays_unknown_in_the_station_registry():
    """Ograniczenie to nie jest wymiar. `platform_length` ma zostać puste."""
    stations = _json("data", "stations", "package-a.json")["stations"]
    assert len(stations) == 12, len(stations)
    for station in stations:
        assert station.get("platform_length") is None, station["station_id"]
        assert station.get("platform_height_above_rail") is None, station["station_id"]


def test_platform_length_lower_bound_is_the_train_not_the_osm_measurement():
    """Dolne ograniczenie = długość składu M7, fakt STIB — a nie 94,76 m z OSM.

    Różnica jest klasy źródła, nie wielkości: 94,0 m to `spec` od operatora,
    94,76 m to pomiar obrysów założonych przez dwóch mapowiczów w 2016–2017.
    """
    spec = _json("data", "vehicle", "m7-spec.json")
    length = spec["parameters"]["length_m"]
    assert length["value"] == 94.0, length
    assert length["status"] == "spec", length
    assert length["value"] < TIGHTEST_STATION_FOOTPRINT_M, (
        "dolne ograniczenie przekroczyło najciaśniejsze górne — jedno z nich jest błędne")


def test_osm_measurement_is_recorded_as_weaker_evidence_not_as_the_value():
    """Raport ma mówić, DLACZEGO nie bierzemy 94,76 m, a nie tylko że nie bierzemy."""
    with open(REPORT, encoding="utf-8") as handle:
        text = handle.read()
    assert "94,76" in text
    assert "PONIŻEJ długości składu" in text, "brak dowodu na błąd obrysu OSM"
    assert "knowledge" in text, "brak proweniencji odstającego pomiaru Schuman"


def test_station_footprint_source_says_it_is_only_an_upper_bound():
    source = _sources()["urbis_metro_station_polygons"]
    assert source["class"] == "official_brussels_region"
    assert source["license"] == "CC0"
    assert "GÓRNE ograniczenie" in source["limitations"]
    # Wyjątek musi być zapisany, bo tam ograniczenie nie obowiązuje.
    assert "Gare de l'Ouest" in source["limitations"]
    assert "content_sha256" not in source, (
        "suma kontrolna tej warstwy była znana tylko w skróconej postaci — "
        "dopisanie brakujących znaków byłoby wymyśleniem")


# --- głębokości z EIE ----------------------------------------------------------


def test_eie_depths_carry_both_conversions_they_went_through():
    """Wartość bez notatki o przekształceniach jest wartością, która kłamie.

    Źródło podaje głębokość PERONU poniżej powierzchni, a kolumna chce rzędnej
    GŁÓWKI SZYNY. Różnica to dokładnie wysokość peronu. Do tego źródło mówi
    „environ" w zdaniu porównawczym, a nie w tabeli pomiarowej.
    """
    floor = _json("data", "vehicle", "m7-spec.json")["parameters"]["floor_height_m"]["value"]
    rows = {row["station_fr"]: row for row in _depth_rows()}

    for station, platform_depth in EIE_PLATFORM_DEPTHS_M.items():
        row = rows[station]
        assert row["confidence"] == "estimated", (station, row["confidence"])

        expected = -(platform_depth + floor)
        actual = float(row["depth_m"])
        assert abs(actual - expected) <= 0.5, (station, actual, expected)
        assert actual < 0.0, f"{station}: rzędna główki szyny ma być ujemna"
        # Zaokrąglenie do precyzji źródła: jedno miejsce po przecinku, nie dwa.
        assert row["depth_m"] == f"{actual:.1f}", row["depth_m"]

        for marker in ("metro3_eie_livre3_colignon", "environ", "PERONU", "glowki szyny", "1,03"):
            assert marker in row["note"], (station, marker)


def test_schuman_stays_empty_because_two_official_sources_disagree():
    """Rejestr nie wybiera zwycięzcy — a 15 m to jedna strona znanego konfliktu."""
    row = {r["station_fr"]: r for r in _depth_rows()}["Schuman"]
    assert row["depth_m"] == "", row
    assert row["confidence"] == "unknown", row
    assert "17,42" in row["note"], "notatka musi nazywać drugą stronę konfliktu"
    assert "nie wybiera" in row["note"]


def test_stations_the_eie_does_not_mention_stay_untouched():
    """EIE wymienia pięć stacji, z czego cztery są w pakiecie A. Reszta zostaje pusta."""
    named = set(EIE_PLATFORM_DEPTHS_M) | {"Schuman"}
    for row in _depth_rows():
        if row["station_fr"] in named:
            continue
        assert row["depth_m"] == "", row["station_fr"]
        assert row["confidence"] == "unknown", row["station_fr"]
        assert "metro3" not in row["note"], (
            f"{row['station_fr']}: EIE nie wymienia tej stacji, a notatka się na nie powołuje")


def test_eie_source_is_registered_with_its_limitations():
    source = _sources()["metro3_eie_livre3_colignon"]
    assert source["class"] == "official_brussels_region"
    assert len(source["content_sha256"]) == 64
    for marker in ("PRZYK", "environ", "PERONU", "17,42"):
        assert marker in source["limitations"], marker

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))

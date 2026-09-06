#!/usr/bin/env python3
"""Testy osi pakietów B–F (T-111 c.d.). Bez sieci, bez pytest, bez archiwum STIB.

Wybór linii i wariantu, dopasowanie nazw stacji i domknięcie wycinka są testowane
na danych budowanych w locie. Skomitowane osie `data/track/L*_[B-F].json` są
sprawdzane tylko wtedy, gdy istnieją — tak samo jak `test_alignment.py` traktuje
pakiet A.
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import build_alignment as B  # noqa: E402
import crosscheck_alignment as X  # noqa: E402
import crs as CRS  # noqa: E402
import validate as V  # noqa: E402

NETWORK = os.path.join(ROOT, "data", "network", "lines.json")
# id osi -> (pakiet, linia w lines.json)
PACKAGE_FILES = {"L1_A": ("A", "L1"), "L1_B": ("B", "L1"), "L5_C": ("C", "L5"),
                 "L5_D": ("D", "L5"), "L2_E": ("E", "L2"), "L6_F": ("F", "L6")}
#: Granice CZYTANE z `tools/track/validate.py`, nie przepisane z niego. Do 6.B25 stały
#: tu trzy liczby wpisane z ręki pod komentarzem „Granice z tools/track/validate.py";
#: komentarz mówił, skąd są, i nic nie pilnowało, żeby nadal stamtąd były. Kopia progu
#: walidatora rozjeżdża się w jedną stronę po cichu: oś, która przestaje spełniać
#: prawdziwy próg, przechodzi tutaj, bo tutejszy został przy starej wartości.
#: Nazwa `MIN_RADIUS_M` znika przy okazji — była w repozytorium zajęta drugi raz,
#: przy innej wartości (20,0 w `tools/blender/clearance.py`, stała martwa od #50).
VALIDATOR = V.LIMITS


def _network():
    with open(NETWORK, encoding="utf-8") as handle:
        return json.load(handle)


def _axis(name):
    path = os.path.join(ROOT, "data", "track", f"{name}.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _provenance(name):
    path = os.path.join(ROOT, "data", "track", f"{name}.provenance.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _fake_layers():
    """Dwie linie: 100m z wariantami w obie strony i 200m, która pakietu nie zawiera."""
    line = [(0.0, 0.0), (1000.0, 0.0), (2000.0, 0.0), (3000.0, 0.0)]
    lines = [
        {"geometry": {"parts": [0], "points": line}, "attributes": {"LineCode": "100m", "Variante": 1}},
        {"geometry": {"parts": [0], "points": list(reversed(line))},
         "attributes": {"LineCode": "100m", "Variante": 2}},
        {"geometry": {"parts": [0], "points": line}, "attributes": {"LineCode": "200m", "Variante": 1}},
    ]
    names = ["ALPHA", "BETA", "GAMMA", "DELTA"]
    stops = []
    for order, (name, x) in enumerate(zip(names, [0.0, 1000.0, 2000.0, 3000.0]), start=1):
        stops.append({"attributes": {"LineCode": "100m", "Variante": 1, "LineDir": "F",
                                     "StopOrder": order, "Stop_id": f"1{order}",
                                     "Descr_fr": name, "Descr_nl": name,
                                     "Alpha_fr": name.title(), "Alpha_nl": name.title(),
                                     "Coord_X": x, "Coord_Y": 0.0, "Mode": "M"}})
    for order, (name, x) in enumerate(zip(reversed(names), [3000.0, 2000.0, 1000.0, 0.0]), start=1):
        stops.append({"attributes": {"LineCode": "100m", "Variante": 2, "LineDir": "V",
                                     "StopOrder": order, "Stop_id": f"2{order}",
                                     "Descr_fr": name, "Descr_nl": name,
                                     "Alpha_fr": name.title(), "Alpha_nl": name.title(),
                                     "Coord_X": x, "Coord_Y": 0.0, "Mode": "M"}})
    stops.append({"attributes": {"LineCode": "200m", "Variante": 1, "LineDir": "F",
                                 "StopOrder": 1, "Stop_id": "31", "Descr_fr": "ALPHA",
                                 "Descr_nl": "ALPHA", "Alpha_fr": "Alpha", "Alpha_nl": "Alpha",
                                 "Coord_X": 0.0, "Coord_Y": 0.0, "Mode": "M"}})
    return lines, stops


# --- wybór linii i wariantu ----------------------------------------------------

def test_packages_resolve_source_keeps_only_forward_variant():
    lines, stops = _fake_layers()
    package = {"id": "X", "from": "Alpha", "to": "Gamma", "stations": 3}
    candidates = B.resolve_source(lines, stops, package)
    assert [(c["line_code"], c["variante"]) for c in candidates] == [("100m", 1)], candidates
    assert candidates[0]["line_dir"] == "F"


def test_packages_resolve_source_uses_reverse_variant_when_package_runs_that_way():
    lines, stops = _fake_layers()
    package = {"id": "X", "from": "Delta", "to": "Beta", "stations": 3}
    candidates = B.resolve_source(lines, stops, package)
    assert [(c["line_code"], c["variante"]) for c in candidates] == [("100m", 2)], candidates


def test_packages_resolve_source_rejects_wrong_station_count():
    lines, stops = _fake_layers()
    package = {"id": "X", "from": "Alpha", "to": "Gamma", "stations": 4}
    try:
        B.resolve_source(lines, stops, package)
    except SystemExit as exc:
        assert "żadna metrowa trasa" in str(exc)
    else:
        raise AssertionError("niezgodna liczba stacji powinna odrzucić kandydata")


def test_packages_select_candidate_breaks_tie_by_lowest_line_code():
    candidates = [{"line_code": "005m", "variante": 1}, {"line_code": "001m", "variante": 1}]
    assert B.select_candidate(candidates)["line_code"] == "001m"
    assert B.select_candidate(candidates, line_code="005m")["line_code"] == "005m"


def test_packages_select_candidate_rejects_forced_non_candidate():
    try:
        B.select_candidate([{"line_code": "001m", "variante": 1}], line_code="002m")
    except SystemExit as exc:
        assert "nie jest kandydatem" in str(exc)
    else:
        raise AssertionError("wymuszona linia spoza kandydatów powinna być błędem")


def test_packages_alignment_id_uses_line_number_not_package_letter():
    assert B.alignment_id("001m", "A") == "L1_A"
    assert B.alignment_id("002m", "E") == "L2_E"
    assert B.alignment_id("006m", "F") == "L6_F"


def test_packages_metro_line_codes_come_from_mode_field():
    _lines, stops = _fake_layers()
    stops.append({"attributes": {"LineCode": "071b", "Variante": 1, "Mode": "B", "StopOrder": 1,
                                 "Descr_fr": "X", "Descr_nl": "X", "Coord_X": 0.0, "Coord_Y": 0.0}})
    assert B.metro_line_codes(stops) == ["100m", "200m"]


# --- dopasowanie nazw ----------------------------------------------------------

def test_packages_stop_aliases_cover_abbreviation_and_second_language():
    row = {"Descr_fr": "JOSEPH.-CHARLOTTE", "Descr_nl": "JOSEPH.-CHARLOTTE",
           "Alpha_fr": "Joséphine-Charlotte", "Alpha_nl": "Joséphine-Charlotte"}
    assert B.normalise("Joséphine-Charlotte") in B.stop_aliases(row)
    row = {"Descr_fr": "CRAINHEM", "Descr_nl": "KRAAINEM",
           "Alpha_fr": "Crainhem", "Alpha_nl": "Kraainem"}
    aliases = B.stop_aliases(row)
    assert B.normalise("Kraainem") in aliases and B.normalise("Crainhem") in aliases


def test_packages_canonical_index_covers_both_halves_of_bilingual_name():
    index = B.canonical_station_index(_network())
    assert index[B.normalise("Kraainem")] == index[B.normalise("Crainhem")]
    assert index[B.normalise("Zwarte Vijvers")] == index[B.normalise("Étangs Noirs")]


def test_packages_every_committed_station_name_exists_in_lines_json():
    index = B.canonical_station_index(_network())
    for name in PACKAGE_FILES:
        document = _axis(name)
        if document is None:
            continue
        for station in document["stations"]:
            assert B.normalise(station["name"].split("|")[0]) in index, station["name"]


# --- geometria wycinka ---------------------------------------------------------

def test_packages_slice_keeps_last_vertex_when_cut_is_at_polyline_end():
    line = [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0), (286.8, 0.0)]
    sliced = B.slice_polyline(line, 50.0, 286.8)
    assert sliced[-1] == (286.8, 0.0), sliced[-1]
    assert abs(B.polyline_length(sliced) - 236.8) < 1e-6


def test_packages_slice_at_end_does_not_duplicate_last_vertex():
    line = [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]
    sliced = B.slice_polyline(line, 0.0, 200.0)
    assert len(sliced) == len(set(sliced)) == 3


def test_packages_resample_at_line_end_has_no_zero_gap():
    line = [(0.0, 0.0), (500.0, 0.0), (586.8, 0.0)]
    sliced = B.slice_polyline(line, 0.0, 586.8)
    sampled = [p for p, _ in B.resample_uniform(sliced, 15.0, [0.0, 586.8])]
    gaps = [math.dist(a, b) for a, b in zip(sampled, sampled[1:])]
    assert min(gaps) > VALIDATOR["min_point_gap_m"], min(gaps)


def test_packages_densify_keeps_vertices_and_respects_step():
    line = [(0.0, 0.0), (100.0, 0.0), (100.0, 30.0)]
    dense = B.densify(line, 10.0)
    assert (0.0, 0.0) in dense and (100.0, 0.0) in dense and (100.0, 30.0) in dense
    gaps = [math.dist(a, b) for a, b in zip(dense, dense[1:])]
    assert max(gaps) <= 10.0 + 1e-9, max(gaps)


def test_packages_source_offset_sees_corner_cutting_that_deviation_misses():
    corner = [(0.0, 0.0), (50.0, 20.0), (100.0, 0.0)]
    axis = [(0.0, 0.0), (100.0, 0.0)]
    # Oba punkty osi leżą na źródle, więc miara „oś -> źródło" pokazuje zero,
    # mimo że cięciwa ścina 20-metrowy wierzchołek.
    assert B.max_deviation(axis, corner) < 1e-9
    stats = B.source_offset_stats(axis, corner)
    assert stats["max_m"] > 19.0, stats
    assert B.source_offset_stats(axis, [(0.0, 0.0), (50.0, 0.0), (100.0, 0.0)])["max_m"] < 1e-6


# --- CRS -----------------------------------------------------------------------

def test_packages_lambert_inverse_round_trips_over_the_network_bbox():
    for x in (142800.0, 147300.0, 156800.0):
        for y in (166800.0, 171000.0, 176300.0):
            assert CRS.lambert_inverse_residual_m(x, y) < 0.001, (x, y)


def test_packages_lambert_inverse_matches_known_forward_point():
    lon, lat = CRS.lambert72_to_wgs84(*CRS.wgs84_to_lambert72(4.3517, 50.8466))
    assert abs(lon - 4.3517) < 1e-7 and abs(lat - 50.8466) < 1e-7


# --- kontrola krzyżowa ---------------------------------------------------------

def test_packages_overpass_bbox_follows_the_axis_not_a_fixed_trunk():
    east = X.overpass_query([(156700.0, 170100.0), (156800.0, 170200.0)])
    west = X.overpass_query([(142800.0, 167100.0), (142900.0, 167300.0)])
    assert east != west
    numbers = [float(v) for v in east.split("(")[-1].split(")")[0].split(",")]
    assert 50.7 < numbers[0] < numbers[2] < 51.0 and 4.4 < numbers[1] < numbers[3] < 4.6, numbers


def test_packages_coverage_and_deviation_are_separate_numbers():
    points = [(0.0, 0.0), (10.0, 0.0), (1000.0, 0.0)]
    segments = [[(0.0, 2.0), (10.0, 2.0)]]
    result = X._coverage_and_deviation(points, segments)
    assert result["coverage_pct"] == round(200.0 / 3, 1)
    assert abs(result["deviation_max_m"] - 2.0) < 1e-6


def test_packages_deviation_median_and_p95_are_computed_not_zero():
    """Mediana i p95 odchyłki muszą być POLICZONE, nie zerem wpisanym na sztywno.

    Zmierzone 02.09.2026 audytem mutacyjnym: podmiana obu na `0.0` przechodziła
    przez całą suitę, bo jedyny test, który ich dotykał, asertował
    `deviation_median_m is not None`. Kontrola krzyżowa z OSM — jedyna rzecz
    w repo, która mówi „nasza oś zgadza się z drugim źródłem" — raportowałaby
    wtedy idealną zgodność dla dowolnej osi, a `provenance.json` niósłby to
    dalej jako fakt.

    Fikstura: dziesięć punktów o znanych, różnych odchyłkach 1…10 m.
    """
    offsets = [float(i) for i in range(1, 11)]
    points = [(100.0 * i, offset) for i, offset in enumerate(offsets)]
    segments = [[(-1000.0, 0.0), (10000.0, 0.0)]]
    result = X._coverage_and_deviation(points, segments)

    assert result["coverage_pct"] == 100.0, result
    # covered = [1..10]; mediana to element o indeksie 10//2 = 5, czyli 6,0 m,
    # p95 to indeks int(0.95*9) = 8, czyli 9,0 m.
    assert result["deviation_median_m"] == 6.0, result
    assert result["deviation_p95_m"] == 9.0, result
    assert result["deviation_max_m"] == 10.0, result


def test_packages_coverage_radius_is_pinned_and_two_sided():
    """Promień pokrycia 50 m to próg, a nie ozdoba.

    Mutacja 50 → 900 przechodziła: istniejąca fikstura używa odchyłek 2 m i 1000 m,
    więc przechodzi dla każdej wartości między ~2 a ~990. To ta sama „okrągła liczba
    z sufitu", co tolerancja 50 m, którą walidator osi już stracił.
    """
    assert X.OSM_COVERAGE_RADIUS_M == 50.0

    segments = [[(-1000.0, 0.0), (10000.0, 0.0)]]
    just_inside = X._coverage_and_deviation([(0.0, X.OSM_COVERAGE_RADIUS_M - 0.5)], segments)
    assert just_inside["coverage_pct"] == 100.0, just_inside
    just_outside = X._coverage_and_deviation([(0.0, X.OSM_COVERAGE_RADIUS_M + 0.5)], segments)
    assert just_outside["coverage_pct"] == 0.0, just_outside
    assert "deviation_median_m" not in just_outside, \
        "punkt poza promieniem nie ma prawa wejść do odchyłki"


def test_packages_chainage_ranges_group_consecutive_flags():
    points = [(x, 0.0) for x in (0.0, 10.0, 20.0, 30.0, 40.0)]
    ranges = X.chainage_ranges(points, [False, True, True, False, True])
    assert ranges == [[10.0, 20.0], [40.0, 40.0]], ranges


# --- skomitowane osie ----------------------------------------------------------

def test_packages_committed_axes_match_declared_packages():
    network = _network()
    packages = {p["id"]: p for p in network["build_packages"]}
    for name, (package_id, _line) in PACKAGE_FILES.items():
        document = _axis(name)
        if document is None:
            continue
        package = packages[package_id]
        assert document["id"] == name
        assert document["package"]["from"] == package["from"]
        assert document["package"]["to"] == package["to"]
        assert len(document["stations"]) == package["stations"], name
        assert document["stations"][0]["chainage_m"] == 0.0
        chainages = [s["chainage_m"] for s in document["stations"]]
        assert chainages == sorted(chainages), name
        assert abs(chainages[-1] - document["length_m"]) < 1.0, name


def test_packages_committed_axes_are_horizontal_only():
    for name in PACKAGE_FILES:
        document = _axis(name)
        if document is None:
            continue
        assert document["vertical"]["status"] == "not_modelled", name
        assert all(point[2] == 0.0 for point in document["points"]), name
        assert all(station["depth_m"] is None for station in document["stations"]), name


def test_packages_committed_axes_have_finite_points_and_sane_gaps():
    for name in PACKAGE_FILES:
        document = _axis(name)
        if document is None:
            continue
        points = [(p[0], p[1]) for p in document["points"]]
        for x, y in points:
            assert math.isfinite(x) and math.isfinite(y), name
        gaps = [math.dist(a, b) for a, b in zip(points, points[1:])]
        assert min(gaps) > VALIDATOR["min_point_gap_m"], (name, min(gaps))
        assert max(gaps) < VALIDATOR["max_point_gap_m"], (name, max(gaps))


def test_packages_committed_axes_keep_radius_above_validator_limit():
    for name in PACKAGE_FILES:
        document = _axis(name)
        if document is None:
            continue
        radii = B.radius_stats([(p[0], p[1]) for p in document["points"]])
        assert radii["min_m"] >= VALIDATOR["min_radius_m"], (name, radii)


def test_packages_committed_station_order_follows_lines_json():
    network = _network()
    for name, (_package_id, line_id) in PACKAGE_FILES.items():
        document = _axis(name)
        if document is None:
            continue
        line = next(l for l in network["lines"] if l["id"] == line_id)
        names = [s["name"] for s in document["stations"]]
        forward = [s for s in line["stops"] if s in names]
        assert names in (forward, list(reversed(forward))), (name, names)


def test_packages_committed_provenance_marks_every_point_as_derived():
    for name in PACKAGE_FILES:
        provenance = _provenance(name)
        document = _axis(name)
        if provenance is None or document is None:
            continue
        assert len(provenance["points"]) == len(document["points"]), name
        assert {p["source_class"] for p in provenance["points"]} == {"derived"}, name
        assert provenance["source_crs"] == "EPSG:31370", name
        assert provenance["statistics"]["resample_max_deviation_m"] < 0.01, name
        assert provenance["statistics"]["resample_step_m"] == 15.0, name


def test_packages_committed_provenance_records_source_selection():
    for name in PACKAGE_FILES:
        provenance = _provenance(name)
        if provenance is None or "candidates" not in provenance["selection"]:
            continue  # pakiet A powstał przed wprowadzeniem listy kandydatów
        selection = provenance["selection"]
        chosen = (selection["line_code"], selection["variante"])
        assert chosen in [(c["line_code"], c["variante"]) for c in selection["candidates"]], name
        assert provenance["crosscheck"], name


def test_packages_committed_axes_have_unique_ids_and_files():
    seen = {}
    for name in PACKAGE_FILES:
        document = _axis(name)
        if document is None:
            continue
        assert document["id"] not in seen, document["id"]
        seen[document["id"]] = name


def test_packages_ring_package_e_is_an_open_slice_without_simonis():
    document = _axis("L2_E")
    if document is None:
        return
    names = [s["name"] for s in document["stations"]]
    assert names[0] == "Elisabeth" and names[-1] == "Beekkant"
    # Wybór jawny: pakiet E nie domyka pierścienia i nie dotyka Simonis ani Osseghem.
    assert "Simonis" not in names and "Osseghem|Ossegem" not in names
    first = document["points"][0]
    last = document["points"][-1]
    assert math.dist((first[0], first[1]), (last[0], last[1])) > 1000.0

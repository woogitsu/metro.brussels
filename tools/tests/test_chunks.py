#!/usr/bin/env python3
"""Testy manifestu streamingowego i predykatu okna (T-210, eksport per chunk).

Bez Blendera i bez pytest. Manifest jest tu budowany z ręki, żeby dało się go
celowo zepsuć — kontrola, która przechodzi tylko na poprawnym wejściu, nie dowodzi
niczego. Geometria idzie przez `sweep.sweep`, więc hash liczy się na prawdziwej
siatce, a nie na atrapie.
"""
import copy
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import profiles as PR  # noqa: E402
import sweep as SW  # noqa: E402

ALIGNMENT = os.path.join(ROOT, "data", "track", "L1_A.json")
BOX = PR.profile_points("box_double")


def _s_curve(count=60, amplitude=40.0, length=600.0):
    return [(length * i / count, amplitude * math.sin(2 * math.pi * i / count), 0.0)
            for i in range(count + 1)]


def _chunk(index, start, end, stations=()):
    return {
        "id": f"T_c{index:02d}",
        "index": index,
        "file": f"T_c{index:02d}.glb",
        "start_m": start,
        "end_m": end,
        "length_m": end - start,
        "rings": 10,
        "bbox_min_m": [start, -5.0, -1.2],
        "bbox_max_m": [end, 5.0, 4.7],
        "bbox_size_m": [end - start, 10.0, 5.9],
        "vertices": 100,
        "faces": 80,
        "triangles": 160,
        "geometry_sha256": "0" * 64,
        "sha256": "1" * 64,
        "bytes": 1024,
        "stations": [{"name": n, "chainage_m": c} for n, c in stations],
    }


def _manifest(edges=(0.0, 400.0, 900.0, 1500.0)):
    """Poprawny manifest o czterech krawędziach, czyli trzech stykających się chunkach."""
    spans = list(zip(edges, edges[1:]))
    stations = [("A", 200.0), ("B", 650.0), ("C", 1200.0)]
    chunks = []
    for index, (start, end) in enumerate(spans):
        inside = [(n, c) for n, c in stations if start <= c < end]
        chunks.append(_chunk(index, start, end, inside))
    return {
        "schema_version": SW.CHUNK_MANIFEST_SCHEMA_VERSION,
        "id": "T",
        "variant": "flat-preview",
        "axis_length_m": edges[-1],
        "chunk_count": len(chunks),
        "chunk_length_sum_m": edges[-1] - edges[0],
        "station_count": len(stations),
        "totals": {"vertices": 100 * len(chunks), "faces": 80 * len(chunks),
                   "triangles": 160 * len(chunks)},
        "chunks": chunks,
    }


def _ids(records):
    return [r["id"] for r in records]


# --- przypisanie stacji do chunków --------------------------------------------

def test_chunk_every_station_lands_in_exactly_one_chunk():
    stops = [0.0, 500.0, 1400.0, 3000.0, 5000.0]
    bounds = SW.chunk_boundaries(5000.0, stops, max_chunk_m=800.0)
    slots = SW.stations_by_chunk(bounds, stops)
    assigned = [i for slot in slots for i in slot]
    assert sorted(assigned) == list(range(len(stops))), assigned
    assert len(assigned) == len(set(assigned)), "stacja przypisana do dwóch chunków"


def test_chunk_station_beyond_the_axis_end_is_clamped_not_dropped():
    # Merode ma chainage 6686,99 m przy osi 6686,74 m — stacja spoza końca osi nie
    # może zniknąć z manifestu, bo Godot nie zobaczyłby peronu ostatniej stacji.
    bounds = [(0.0, 500.0), (500.0, 1000.0)]
    slots = SW.stations_by_chunk(bounds, [0.0, 1000.64])
    assert slots == [[0], [1]], slots


def test_chunk_stations_match_the_boundaries_on_the_real_axis():
    if not os.path.isfile(ALIGNMENT):
        return
    document = json.load(open(ALIGNMENT, encoding="utf-8"))
    stops = [s["chainage_m"] for s in document["stations"]]
    points = [tuple(p) for p in document["points"]]
    result = SW.sweep(points, BOX, 5.0, stops)
    slots = SW.stations_by_chunk(result["chunk_bounds"], stops)
    assert sum(len(s) for s in slots) == len(stops)
    assert all(len(s) >= 1 for s in slots), "chunk bez stacji przy podziale po stacjach"
    for slot, (start, end) in zip(slots, result["chunk_bounds"]):
        for index in slot:
            value = min(max(stops[index], 0.0), result["axis_length_m"])
            assert start - 1e-9 <= value <= end + 1e-9, (index, start, end)


# --- okno streamowania --------------------------------------------------------

def test_chunk_window_radius_is_symmetric():
    assert SW.stream_window(1000.0, 500.0) == (500.0, 1500.0)


def test_chunk_window_defaults_come_from_the_architecture_document():
    low, high = SW.stream_window(1000.0)
    assert (low, high) == (1000.0 - SW.DEFAULT_STREAM_BEHIND_M,
                           1000.0 + SW.DEFAULT_STREAM_AHEAD_M)
    assert SW.DEFAULT_STREAM_AHEAD_M > SW.DEFAULT_STREAM_BEHIND_M


def test_chunk_window_follows_the_direction_of_travel():
    forward = SW.stream_window(1000.0, ahead_m=600.0, behind_m=300.0, heading=1.0)
    backward = SW.stream_window(1000.0, ahead_m=600.0, behind_m=300.0, heading=-1.0)
    assert forward == (700.0, 1600.0)
    assert backward == (400.0, 1300.0)


def test_chunk_window_rejects_a_negative_range():
    try:
        SW.stream_window(100.0, -1.0)
    except ValueError:
        return
    raise AssertionError("ujemny zasięg streamowania został przyjęty")


def test_chunk_selection_covers_the_whole_requested_window():
    manifest = _manifest()
    for chainage in (0.0, 120.0, 400.0, 899.0, 1500.0):
        low, high = SW.stream_window(chainage, 250.0)
        picked = SW.chunks_for_train(manifest, chainage, 250.0)
        assert picked, chainage
        want_low = max(low, 0.0)
        want_high = min(high, manifest["axis_length_m"])
        assert picked[0]["start_m"] <= want_low
        assert picked[-1]["end_m"] >= want_high


def test_chunk_selection_is_a_contiguous_run_without_holes():
    manifest = _manifest()
    picked = SW.chunks_for_train(manifest, 700.0, 400.0)
    assert len(picked) >= 2
    for previous, current in zip(picked, picked[1:]):
        assert previous["end_m"] == current["start_m"]


def test_chunk_selection_on_a_seam_returns_both_neighbours():
    manifest = _manifest()
    # zasięg 0 m i pociąg dokładnie na szwie: brakujący chunk to dziura w tunelu,
    # nadmiarowy to tylko pamięć — więc szew ma zwrócić oba
    assert _ids(SW.chunks_for_train(manifest, 400.0, 0.0)) == ["T_c00", "T_c01"]


def test_chunk_selection_at_the_axis_ends_does_not_run_off_the_manifest():
    manifest = _manifest()
    assert _ids(SW.chunks_for_train(manifest, 0.0, 100.0)) == ["T_c00"]
    assert _ids(SW.chunks_for_train(manifest, 1500.0, 100.0)) == ["T_c02"]
    assert _ids(SW.chunks_for_train(manifest, -5000.0, 10.0)) == []
    assert _ids(SW.chunks_for_train(manifest, 99000.0, 10.0)) == []


def test_chunk_selection_grows_with_the_range():
    manifest = _manifest()
    narrow = _ids(SW.chunks_for_train(manifest, 700.0, 50.0))
    wide = _ids(SW.chunks_for_train(manifest, 700.0, 5000.0))
    assert narrow == ["T_c01"]
    assert wide == ["T_c00", "T_c01", "T_c02"]


# --- plan streamowania --------------------------------------------------------

def test_chunk_streaming_plan_splits_into_load_keep_free():
    manifest = _manifest()
    plan = SW.streaming_plan(manifest, 1200.0, ["T_c00", "T_c01"], radius_m=100.0)
    assert plan["load"] == ["T_c02"]
    assert plan["keep"] == []
    assert plan["free"] == ["T_c00", "T_c01"]


def test_chunk_streaming_plan_keeps_what_is_already_loaded():
    manifest = _manifest()
    needed = _ids(SW.chunks_for_train(manifest, 700.0, 400.0))
    plan = SW.streaming_plan(manifest, 700.0, needed, radius_m=400.0)
    assert plan["load"] == [] and plan["free"] == [] and plan["keep"] == needed


def test_chunk_streaming_plan_walks_the_axis_without_ever_dropping_the_train():
    """Przejazd co 25 m: chunk pod pociągiem nigdy nie może być zwolniony."""
    manifest = _manifest()
    loaded = []
    for step in range(0, 61):
        chainage = step * 25.0
        plan = SW.streaming_plan(manifest, chainage, loaded, radius_m=300.0)
        loaded = plan["keep"] + plan["load"]
        under = [c["id"] for c in manifest["chunks"]
                 if c["start_m"] <= chainage <= c["end_m"]]
        assert set(under) <= set(loaded), (chainage, under, loaded)


# --- kontrola manifestu -------------------------------------------------------

def test_chunk_manifest_problems_accepts_a_consistent_manifest():
    assert SW.manifest_problems(_manifest()) == []


def test_chunk_manifest_span_is_consistent_after_rounding():
    """Regresja: pięć z siedemnastu chunków pakietu E wywracało kontrolę manifestu.

    Zaokrąglanie długości niezależnie od końców rozjeżdża się z ich różnicą o pełne
    1e-6, czyli dokładnie o tolerancję szwu w `manifest_problems`. Liczby poniżej to
    surowe granice chunków `L2_E_flat_preview_c08` i `..._c12`, wprost z
    `chunk_boundaries` na osi pakietu E — jeden przypadek w górę, drugi w dół.
    Pakiet A nie trafił w ten przypadek ani razu, więc błąd przeszedł niezauważony.
    """
    for start_raw, end_raw, naive in ((4465.6121470499465, 5005.090002543426, 539.477855),
                                      (6383.717986769654, 6953.151306430391, 569.43332)):
        start, end, length = SW.manifest_span(start_raw, end_raw)
        assert round(end_raw - start_raw, 6) == naive, "przypadek przestał być brzegowy"
        assert length != naive, "zaokrąglenie osobno i z końców dało to samo"
        assert abs((end - start) - length) <= 1e-9


def test_chunk_manifest_problems_accepts_the_package_e_boundary_case():
    """Ta sama para liczb wstawiona w manifest nie może być zgłoszona jako błąd."""
    manifest = _manifest()
    start, end, length = SW.manifest_span(4465.6121470499465, 5005.090002543426)
    first, middle, last = manifest["chunks"]
    first["start_m"], first["end_m"] = 0.0, start
    first["length_m"] = round(start, 6)
    middle["start_m"], middle["end_m"], middle["length_m"] = start, end, length
    last["start_m"] = end
    last["end_m"] = end + 400.0
    last["length_m"] = round(last["end_m"] - end, 6)
    manifest["chunk_length_sum_m"] = sum(c["length_m"] for c in manifest["chunks"])
    manifest["axis_length_m"] = last["end_m"]
    assert SW.manifest_problems(manifest) == []


def test_chunk_manifest_problems_catches_a_length_rounded_on_its_own():
    """Kontrola musi nadal łapać długość, która nie zgadza się z końcami."""
    manifest = _manifest()
    manifest["chunks"][1]["length_m"] = round(manifest["chunks"][1]["length_m"] + 1e-5, 6)
    assert any("length_m" in p for p in SW.manifest_problems(manifest))


def test_chunk_manifest_problems_detects_a_hole_between_chunks():
    manifest = _manifest()
    manifest["chunks"][1]["start_m"] += 0.5
    manifest["chunks"][1]["length_m"] -= 0.5
    manifest["chunk_length_sum_m"] -= 0.5
    problems = SW.manifest_problems(manifest)
    assert any("dziura" in p for p in problems), problems


def test_chunk_manifest_problems_detects_an_overlap_between_chunks():
    manifest = _manifest()
    manifest["chunks"][1]["start_m"] -= 0.5
    manifest["chunks"][1]["length_m"] += 0.5
    manifest["chunk_length_sum_m"] += 0.5
    problems = SW.manifest_problems(manifest)
    assert any("zakładka" in p for p in problems), problems


def test_chunk_manifest_problems_detects_a_length_sum_that_misses_the_axis():
    manifest = _manifest()
    manifest["axis_length_m"] += 3.0
    problems = SW.manifest_problems(manifest)
    assert any("suma długości" in p for p in problems), problems


def test_chunk_manifest_problems_detects_counters_that_do_not_add_up():
    manifest = _manifest()
    manifest["totals"]["triangles"] += 2
    problems = SW.manifest_problems(manifest)
    assert any("totals.triangles" in p for p in problems), problems


def test_chunk_manifest_problems_detects_duplicate_ids_and_files():
    manifest = _manifest()
    manifest["chunks"][1]["id"] = manifest["chunks"][0]["id"]
    manifest["chunks"][1]["file"] = manifest["chunks"][0]["file"]
    problems = SW.manifest_problems(manifest)
    assert any("powtórzone id" in p for p in problems), problems
    assert any("powtórzone nazwy plików" in p for p in problems), problems


def test_chunk_manifest_problems_detects_empty_geometry():
    manifest = _manifest()
    manifest["chunks"][2]["vertices"] = 0
    manifest["totals"]["vertices"] -= 100
    problems = SW.manifest_problems(manifest)
    assert any("pusta geometria" in p for p in problems), problems


def test_chunk_manifest_problems_detects_a_lost_station():
    manifest = _manifest()
    manifest["chunks"][0]["stations"] = []
    problems = SW.manifest_problems(manifest)
    assert any("stacje w chunkach" in p for p in problems), problems


def test_chunk_manifest_problems_rejects_an_empty_manifest():
    assert SW.manifest_problems({"axis_length_m": 10.0, "chunks": []})


# --- determinizm --------------------------------------------------------------

def test_chunk_geometry_hash_is_stable_across_runs():
    a = SW.sweep(_s_curve(), BOX, 5.0, [0.0, 300.0, 600.0], max_chunk_m=200.0)
    b = SW.sweep(_s_curve(), BOX, 5.0, [0.0, 300.0, 600.0], max_chunk_m=200.0)
    assert [SW.chunk_geometry_sha256(c) for c in a["chunks"]] == \
           [SW.chunk_geometry_sha256(c) for c in b["chunks"]]


def test_chunk_geometry_hash_reacts_to_a_moved_vertex():
    result = SW.sweep(_s_curve(), BOX, 5.0, [0.0, 600.0])
    chunk = result["chunks"][0]
    before = SW.chunk_geometry_sha256(chunk)
    moved = dict(chunk)
    moved["vertices"] = [chunk["vertices"][0]] + list(chunk["vertices"][1:])
    moved["vertices"][1] = SW.add(moved["vertices"][1], (0.0, 0.0, 0.001))
    assert SW.chunk_geometry_sha256(moved) != before


def test_chunk_geometry_hash_ignores_the_glb_bytes():
    """Odcisk geometrii nie może zależeć od pól opisujących plik — po to istnieje."""
    result = SW.sweep(_s_curve(), BOX, 5.0, [0.0, 600.0])
    chunk = dict(result["chunks"][0])
    before = SW.chunk_geometry_sha256(chunk)
    chunk["sha256"] = "deadbeef"
    chunk["bytes"] = 12345
    assert SW.chunk_geometry_sha256(chunk) == before


def test_chunk_deterministic_view_drops_only_the_file_dependent_keys():
    manifest = _manifest()
    manifest["glb_bytes"] = 999
    view = SW.deterministic_view(manifest)
    assert "glb_bytes" not in view
    for chunk in view["chunks"]:
        assert "sha256" not in chunk and "bytes" not in chunk
        assert chunk["geometry_sha256"] and chunk["triangles"] and chunk["file"]
    assert manifest["chunks"][0]["sha256"], "deterministic_view nie może psuć oryginału"


def test_chunk_deterministic_view_still_sees_a_geometry_change():
    a = _manifest()
    b = copy.deepcopy(a)
    b["chunks"][0]["sha256"] = "f" * 64
    b["chunks"][0]["bytes"] = 4096
    assert SW.deterministic_view(a) == SW.deterministic_view(b)
    b["chunks"][0]["geometry_sha256"] = "e" * 64
    assert SW.deterministic_view(a) != SW.deterministic_view(b)


# --- triaż mutacyjny: granice cięcia i kontroli manifestu -----------------------
#
# Z przeglądu `tools/tests/mutation_sweep.py` na `sweep.py`. Każdy test zabija
# konkretną mutację, wypisaną w komentarzu — i ta mutacja jest jego kontrolą
# negatywną. Klasyfikacja całości: `reports/mutation-triage-sweep.md`.
#
# TOLERANCJA JEST POTĘGĄ DWÓJKI. `1e-6` nie jest reprezentowalne dokładnie przy
# 400,0 / 900,0 / 1500,0 m — `abs((400.0 + 1e-6) - 400.0)` wychodzi mniej niż `1e-6`,
# więc test „przesuwam dokładnie o tolerancję" nigdy nie dotykałby granicy i mutacja
# `>` -> `>=` przeżywałaby mimo testu napisanego wprost pod nią. Ta sama pułapka
# przeszła niezauważona w `test_lod.py` (patrz `reports/mutation-triage-lod.md`),
# dlatego każdy test poniżej sprawdza swoje założenie wprost, zamiast je zakładać.

EXACT_TOL = 2.0 ** -20


def test_chunk_a_span_exactly_at_the_cap_is_not_split():
    """Odcinek RÓWNY limitowi nie jest dzielony. Limit znaczy „nie dłuższy niż".

    **Mutacja 219 `<=` -> `<` jest równoważna i ten test tego nie zmienia.**
    Napisałem go w przekonaniu, że ją zabije; nie zabija — sprawdzone wykonaniem,
    mutant daje 730/730. Powód: przy równości `pieces = ceil((b - a) / max_chunk_m)`
    wychodzi 1, więc `range(1, 1)` jest puste i pętla i tak nic nie dokłada. `continue`
    w tym wierszu jest optymalizacją, nie bramką.

    Test zostaje, bo przypina zachowanie, które jest umową („nie dłuższy niż"), i
    złapie każdą zmianę, która tę umowę naprawdę złamie — na przykład przejście na
    `floor` albo dzielenie z zapasem. Ale nie udaję, że zabija mutację.
    """
    assert SW._split_long([], 400.0, 400.0, [], 10.0) == []
    assert SW._split_long([], 400.1, 400.0, [], 10.0) != []


def test_chunk_a_cut_exactly_one_halo_from_a_station_is_left_alone():
    """Mutacja: 234 `>=` -> `>` — cięcie DOKŁADNIE o halo od peronu byłoby odsuwane.

    Halo znaczy „bliżej niż tyle nie wolno", więc odległość równa halo jest już
    dopuszczalna. Mutacja odsuwałaby takie cięcie bez potrzeby, a odsunięcie może
    się nie udać i wtedy chunk w ogóle nie zostaje podzielony.
    """
    assert SW._push_out_of_stations(150.0, [100.0], 50.0, 0.0, 1000.0) == 150.0
    assert SW._push_out_of_stations(149.9, [100.0], 50.0, 0.0, 1000.0) == 50.0


def test_chunk_a_piece_exactly_at_the_minimum_length_is_kept():
    """Mutacja: 247 `>=` -> `>` — kawałek RÓWNY minimum byłby wyrzucony.

    Minimum znaczy „nie krótszy niż", więc równość jest dopuszczalna. Wyrzucenie
    takiego cięcia scala dwa chunki w jeden dłuższy niż `max_chunk_m` — czyli łamie
    drugi limit, żeby uszanować pierwszy.
    """
    assert SW._drop_short([100.0], 300.0, 100.0) == [100.0]
    assert SW._drop_short([99.999], 300.0, 100.0) == []


def test_chunk_a_station_exactly_on_a_seam_goes_to_the_chunk_that_starts_there():
    """Mutacja: 528 `<` -> `<=` — stacja na szwie wpadałaby do chunka POPRZEDNIEGO.

    Konwencja jest półotwarta, `[start, end)`, ta sama co w blokach sygnalizacji:
    kilometraż równy granicy należy do chunka NASTĘPNEGO. Bez tego peron leżałby
    w chunku, który się na nim kończy, i halo stacji straciłoby sens.
    """
    assert SW.stations_by_chunk([(0.0, 400.0), (400.0, 900.0)], [400.0]) == [[], [0]]
    assert SW.stations_by_chunk([(0.0, 400.0), (400.0, 900.0)], [399.999]) == [[0], []]


def test_chunk_window_with_no_heading_looks_forward():
    """Mutacja: 571 `>=` -> `>` — `heading == 0.0` odwracałoby okno.

    Zero to „kierunek nieznany", a nie „do tyłu": skład stojący na peronie ma zerową
    prędkość i musi mieć wczytane to, co PRZED nim, bo za chwilę tam pojedzie.
    """
    assert SW.stream_window(500.0, ahead_m=100.0, behind_m=50.0, heading=0.0) == (450.0, 600.0)
    assert SW.stream_window(500.0, ahead_m=100.0, behind_m=50.0, heading=-1.0) == (400.0, 550.0)


# --- kontrola manifestu: granice tolerancji ------------------------------------

def test_chunk_manifest_problems_detects_a_span_of_exactly_zero():
    """Mutacja: 683 `<= 0.0` -> `< 0.0` — chunk o zerowej długości przechodziłby.

    Chunk, który zaczyna się i kończy w tym samym miejscu, nie ma geometrii ani szwu.
    Zero jest tu złamaniem, nie granicą dopuszczalną.
    """
    manifest = _manifest()
    manifest["chunks"][1]["end_m"] = manifest["chunks"][1]["start_m"]
    problems = SW.manifest_problems(manifest)
    assert any("zakres chainage nie rośnie" in p for p in problems), problems


def test_chunk_manifest_problems_detects_geometry_that_is_exactly_empty():
    """Mutacje: 687 `<= 0` -> `< 0` (dwie) i `0` -> `1` (dwie).

    Zero wierzchołków albo zero trójkątów to pusty plik. Mutacja w drugą stronę
    (`<= 1`) zgłaszałaby jako pustą siatkę o jednym trójkącie, która pusta nie jest,
    więc test sprawdza obie strony granicy.
    """
    for field in ("vertices", "triangles"):
        manifest = _manifest()
        manifest["chunks"][1][field] = 0
        assert any("pusta geometria" in p for p in SW.manifest_problems(manifest)), field

    manifest = _manifest()
    for chunk in manifest["chunks"]:
        chunk["vertices"], chunk["triangles"], chunk["faces"] = 1, 1, 1
    manifest["totals"] = {"vertices": 3, "faces": 3, "triangles": 3}
    assert not any("pusta geometria" in p for p in SW.manifest_problems(manifest))


def test_chunk_manifest_problems_detects_a_bbox_collapsed_to_a_point():
    """Mutacja: 690 `<= 0.0` -> `0.001` — bbox zwinięty do punktu.

    `max(size) <= 0.0` łapie chunk, którego pudełko ma zerowy rozmiar we WSZYSTKICH
    trzech osiach naraz — czyli siatkę zwiniętą do punktu. To jest dokładnie ten
    obraz, którego szuka render `_iso` z `CLAUDE.md`, tylko widziany w liczbach.
    """
    manifest = _manifest()
    chunk = manifest["chunks"][1]
    chunk["bbox_min_m"] = [10.0, 0.0, 0.0]
    chunk["bbox_max_m"] = [10.0, 0.0, 0.0]
    chunk["bbox_size_m"] = [0.0, 0.0, 0.0]
    assert any("bbox zwinięty" in p for p in SW.manifest_problems(manifest))

    chunk["bbox_max_m"] = [10.0, 0.0, 1e-6]
    assert not any("bbox zwinięty" in p for p in SW.manifest_problems(manifest))


def test_chunk_manifest_tolerances_accept_a_shift_of_exactly_the_tolerance():
    """Mutacje: 678, 685, 695 i 700 `>` -> `>=`.

    Cztery tolerancje — koniec ostatniego chunka wobec osi, `length_m` wobec różnicy
    końców, szew między chunkami i suma długości — i wszystkie znaczą to samo:
    „do tyle wolno". Przesunięcie RÓWNE tolerancji jeszcze się mieści, większe już nie.

    Każdy przypadek sprawdza najpierw, że różnica faktycznie WYSZŁA równa tolerancji.
    Bez tego sprawdzenia test wygląda na kontrolę granicy, a granicy nie dotyka —
    dokładnie tak przeżyły dwie mutacje w `test_lod.py`.
    """
    # 685: length_m rozjechane z różnicą końców dokładnie o tolerancję szwu
    manifest = _manifest()
    chunk = manifest["chunks"][1]
    span = chunk["end_m"] - chunk["start_m"]
    chunk["length_m"] = span + EXACT_TOL
    assert abs(span - chunk["length_m"]) == EXACT_TOL
    assert not any("length_m" in p for p in SW.manifest_problems(manifest, seam_tolerance_m=EXACT_TOL))
    chunk["length_m"] = span + EXACT_TOL * 2.0
    assert any("length_m" in p for p in SW.manifest_problems(manifest, seam_tolerance_m=EXACT_TOL))

    # 695: szew między chunkami dokładnie o tolerancję
    manifest = _manifest()
    first, second = manifest["chunks"][0], manifest["chunks"][1]
    second["start_m"] = first["end_m"] + EXACT_TOL
    second["length_m"] = second["end_m"] - second["start_m"]
    assert abs(second["start_m"] - first["end_m"]) == EXACT_TOL
    problems = SW.manifest_problems(manifest, seam_tolerance_m=EXACT_TOL,
                                    length_tolerance_m=1e-3)
    assert not any("dziura" in p or "zakładka" in p for p in problems), problems
    second["start_m"] = first["end_m"] + EXACT_TOL * 2.0
    second["length_m"] = second["end_m"] - second["start_m"]
    problems = SW.manifest_problems(manifest, seam_tolerance_m=EXACT_TOL,
                                    length_tolerance_m=1e-3)
    assert any("dziura" in p for p in problems), problems

    # 678 i 700: koniec ostatniego chunka i suma długości wobec osi
    manifest = _manifest()
    axis = manifest["axis_length_m"]
    manifest["axis_length_m"] = axis + EXACT_TOL
    assert abs(manifest["chunks"][-1]["end_m"] - manifest["axis_length_m"]) == EXACT_TOL
    problems = SW.manifest_problems(manifest, length_tolerance_m=EXACT_TOL)
    assert not any("ostatni chunk" in p or "suma długości" in p for p in problems), problems
    manifest["axis_length_m"] = axis + EXACT_TOL * 2.0
    problems = SW.manifest_problems(manifest, length_tolerance_m=EXACT_TOL)
    assert any("ostatni chunk" in p for p in problems), problems
    assert any("suma długości" in p for p in problems), problems


def test_chunk_a_shifted_cut_may_land_exactly_one_halo_from_another_station():
    """Mutacja: 237 `>=` -> `>` — odsunięte cięcie odrzucane przez własne halo.

    Cięcie odsuwane spod peronu ląduje z definicji DOKŁADNIE o halo od niego. Warunek
    „nie bliżej niż halo od żadnej stacji" musi więc dopuszczać równość, bo inaczej
    odrzuca każdy kandydat, który sam wyprodukował — i `_push_out_of_stations` zwraca
    `None`, czyli „nie da się przeciąć", dla przypadku, w którym da się doskonale.

    Zmierzone: przy stacjach 100 i 200 m, halo 50 m i kandydacie 120 m oryginał oddaje
    50,0 m, a mutant `None`. Drugi przypadek pilnuje, że wybór jest ograniczony
    krańcami odcinka: przy `low = 60` pierwsza możliwość odpada i wychodzi 150,0 m.
    """
    assert SW._push_out_of_stations(120.0, [100.0, 200.0], 50.0, 0.0, 1000.0) == 50.0
    assert SW._push_out_of_stations(120.0, [100.0, 200.0], 50.0, 60.0, 1000.0) == 150.0

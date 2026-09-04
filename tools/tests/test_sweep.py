#!/usr/bin/env python3
"""Testy geometrii zamiatania tunelu (T-210). Bez Blendera i bez pytest.

Cała matematyka `tools/blender/sweep.py` jest sprawdzana na figurach liczonych
w locie; gotowa oś `data/track/L1_A.json` jest używana tylko wtedy, gdy jest
obecna w repo, żeby testy nie zależały od artefaktu.
"""
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
    """Łuk S — krzywizna zmienia znak, czyli miejsce, w którym ramka Freneta wywraca się."""
    return [(length * i / count, amplitude * math.sin(2 * math.pi * i / count), 0.0)
            for i in range(count + 1)]


def _helix(count=80, radius=50.0, pitch=30.0, turns=1.5):
    return [(radius * math.cos(2 * math.pi * turns * i / count),
             radius * math.sin(2 * math.pi * turns * i / count),
             pitch * turns * i / count) for i in range(count + 1)]


# --- ramki --------------------------------------------------------------------

def test_sweep_frames_do_not_flip_on_inflection():
    frames = SW.rmf_frames(_s_curve())
    assert SW.frame_twist_deg(frames) < 1e-6, SW.frame_twist_deg(frames)
    for (_p, _t, r1, _s1), (_q, _u, r2, _s2) in zip(frames, frames[1:]):
        assert SW.dot(r1, r2) > 0.99, "ramka wywróciła się między sąsiednimi punktami"


def test_sweep_frames_stay_continuous_on_a_helix():
    frames = SW.rmf_frames(_helix())
    for (_p, t, r, s), (_q, t2, r2, s2) in zip(frames, frames[1:]):
        assert SW.dot(r, r2) > 0.9 and SW.dot(s, s2) > 0.9
    for _p, t, r, s in frames:
        assert abs(SW.dot(t, r)) < 1e-9 and abs(SW.dot(t, s)) < 1e-9
        assert abs(SW.norm(r) - 1.0) < 1e-9 and abs(SW.norm(s) - 1.0) < 1e-9


def test_sweep_frames_are_deterministic():
    assert SW.rmf_frames(_s_curve()) == SW.rmf_frames(_s_curve())


# --- zagęszczanie osi ---------------------------------------------------------

def test_sweep_smoothing_passes_through_every_source_point():
    source = _s_curve(count=12)
    dense = SW.catmull_rom(source, 5.0)
    for point in source:
        assert min(SW.norm(SW.sub(point, d)) for d in dense) < 1e-9, point


def test_sweep_zero_step_keeps_the_source_polyline():
    source = _s_curve(count=12)
    assert SW.catmull_rom(source, 0.0) == SW.dedupe(source)
    assert SW.max_deviation(SW.catmull_rom(source, 0.0), source) < 1e-9


def test_sweep_smoothing_deviation_is_bounded_and_reported():
    source = _s_curve(count=12)
    dense = SW.catmull_rom(source, 2.0)
    assert len(dense) > 4 * len(source)
    # wybrzuszenie poza cięciwę jest nieuniknione i MA być mierzone, nie ukrywane
    assert 0.0 < SW.max_deviation(dense, source) < 5.0


# --- podział na chunki --------------------------------------------------------

def test_sweep_chunk_boundaries_never_land_inside_a_station():
    stops = [0.0, 500.0, 1400.0, 3000.0, 3100.0, 5000.0]
    bounds = SW.chunk_boundaries(5000.0, stops, max_chunk_m=400.0)
    assert SW.splits_station(bounds, stops) == []


def test_sweep_chunk_boundaries_respect_the_length_cap():
    stops = [0.0, 2500.0, 5000.0]
    bounds = SW.chunk_boundaries(5000.0, stops, max_chunk_m=600.0)
    assert max(b - a for a, b in bounds) <= 600.0 + 1e-6


def test_sweep_chunk_lengths_sum_to_the_axis_length():
    stops = [0.0, 900.0, 2600.0, 4000.0]
    bounds = SW.chunk_boundaries(4000.0, stops)
    assert abs(sum(b - a for a, b in bounds) - 4000.0) < 1e-9
    assert bounds[0][0] == 0.0 and bounds[-1][1] == 4000.0
    for (_a, b), (c, _d) in zip(bounds, bounds[1:]):
        assert b == c, "granice chunków muszą się stykać, nie zachodzić"


# --- siatka -------------------------------------------------------------------

def test_sweep_mesh_has_no_gap_between_chunks():
    result = SW.sweep(_s_curve(), BOX, 5.0, [0.0, 200.0, 400.0, 600.0], max_chunk_m=150.0)
    chunks, columns = result["chunks"], result["columns"]
    assert len(chunks) >= 3
    for a, b in zip(chunks, chunks[1:]):
        assert SW.chunk_gap_m(a, b, columns) <= 0.001


def test_sweep_normals_point_into_the_bore():
    result = SW.sweep(_s_curve(), BOX, 5.0, [0.0, 600.0])
    outward = sum(SW.outward_faces(c, result["frames"], result["columns"])
                  for c in result["chunks"])
    assert outward == 0, f"{outward} ścian z normalną na zewnątrz"


def test_sweep_mesh_has_no_degenerate_or_non_finite_geometry():
    result = SW.sweep(_helix(), BOX, 4.0, [0.0, 100.0])
    assert SW.non_finite(result["chunks"]) == 0
    assert sum(len(SW.degenerate_faces(c)) for c in result["chunks"]) == 0


def test_sweep_seam_column_is_duplicated_so_uv_does_not_wrap():
    result = SW.sweep(_s_curve(), BOX, 10.0, [0.0, 600.0])
    columns = result["columns"]
    assert columns == len(BOX) + 1
    chunk = result["chunks"][0]
    assert chunk["vertices"][0] == chunk["vertices"][columns - 1]
    assert chunk["uvs"][0][0] == 0.0
    perimeter = SW.profile_arc(BOX)[-1]
    assert abs(chunk["uvs"][columns - 1][0] - perimeter / SW.UV_METRES_PER_UNIT) < 1e-9


def test_sweep_uv_density_is_uniform_along_the_axis():
    result = SW.sweep(_s_curve(), BOX, 5.0, [0.0, 300.0, 600.0], max_chunk_m=200.0)
    columns = result["columns"]
    for chunk in result["chunks"]:
        low, high = SW.uv_stretch(chunk, columns)
        assert 0.8 * SW.UV_METRES_PER_UNIT < low <= high < 1.2 * SW.UV_METRES_PER_UNIT


def test_sweep_uv_v_is_continuous_across_a_chunk_seam():
    result = SW.sweep(_s_curve(), BOX, 5.0, [0.0, 300.0, 600.0], max_chunk_m=200.0)
    columns = result["columns"]
    for a, b in zip(result["chunks"], result["chunks"][1:]):
        assert abs(a["uvs"][-columns][1] - b["uvs"][0][1]) < 1e-9


def test_sweep_profile_cross_section_keeps_its_size():
    result = SW.sweep(_s_curve(), BOX, 5.0, [0.0, 600.0])
    width, height = PR.dimensions("box_double")
    chunk = result["chunks"][0]
    columns = result["columns"]
    ring = chunk["vertices"][:columns]
    frame = result["frames"][chunk["first_ring"]]
    lateral = [SW.dot(SW.sub(v, frame[0]), frame[2]) for v in ring]
    vertical = [SW.dot(SW.sub(v, frame[0]), frame[3]) for v in ring]
    assert abs((max(lateral) - min(lateral)) - width) < 1e-6
    assert abs((max(vertical) - min(vertical)) - height) < 1e-6


# --- gotowa oś ----------------------------------------------------------------

def test_sweep_committed_axis_produces_a_sane_tunnel():
    if not os.path.isfile(ALIGNMENT):
        return
    document = json.load(open(ALIGNMENT, encoding="utf-8"))
    points = [tuple(p) for p in document["points"]]
    stops = [s["chainage_m"] for s in document["stations"]]
    result = SW.sweep(points, BOX, 5.0, stops)
    assert abs(result["axis_length_m"] - document["length_m"]) < 5.0
    assert abs(sum(c["length_m"] for c in result["chunks"]) - result["axis_length_m"]) < 0.01
    assert SW.splits_station(result["chunk_bounds"], stops) == []
    assert result["twist_deg"] < 5.0
    lo, hi = SW.bounding_box(result["chunks"])
    width, height = PR.dimensions("box_double")
    span = max(hi[i] - lo[i] for i in range(2))
    # bbox nie może być ani punktem, ani dłuższy niż sama oś
    assert width < span <= result["axis_length_m"]
    assert abs((hi[2] - lo[2]) - height) < 1e-6


# --- triaż mutacyjny: granice prymitywów geometrycznych -------------------------
#
# Z przeglądu `tools/tests/mutation_sweep.py` na `sweep.py`: 39 ocalałych mutacji.
# Każdy test poniżej zabija konkretną, wypisaną w komentarzu — i ta mutacja jest jego
# kontrolą negatywną. Klasyfikacja całości: `reports/mutation-triage-sweep.md`.


def test_sweep_zero_vector_has_no_direction():
    """Mutacja: 54 `<= 0.0` -> `< 0.0` — wektor zerowy dzieliłby przez zero."""
    try:
        SW.unit((0.0, 0.0, 0.0))
    except ValueError:
        pass
    else:
        raise AssertionError("wektor zerowy dostał kierunek")
    assert SW.unit((3.0, 0.0, 0.0)) == (1.0, 0.0, 0.0)


def test_sweep_three_points_are_enough_to_smooth():
    """Mutacja: 92 `len(points) < 3` -> `< 4` — trzy punkty wracałyby bez zmian.

    Trzy punkty to najkrótsza łamana, która ma w ogóle załamanie, więc jest to
    najmniejszy przypadek, w którym wygładzanie ma sens. Odrzucenie go byłoby ciche:
    oś wróciłaby kanciasta i nikt by się nie dowiedział.
    """
    source = [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (20.0, 1.0, 0.0)]
    smoothed = SW.catmull_rom(source, 2.0)
    assert len(smoothed) > len(source), len(smoothed)
    assert SW.catmull_rom(source[:2], 2.0) == source[:2], "dwa punkty nie mają czego wygładzać"


def test_sweep_point_to_polyline_survives_a_segment_of_zero_length():
    """Mutacja: 126 `<= 0.0` -> `< 0.0` — dzielenie przez zero na zdublowanym punkcie.

    `dedupe` istnieje właśnie dlatego, że surowe dane zawierają powtórzone wierzchołki.
    Gdy taki odcinek mimo wszystko tu trafi, ma wyjść odległość od punktu.
    """
    assert SW.point_to_polyline((0.0, 3.0, 0.0),
                                [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]) == 3.0


def test_sweep_two_points_are_enough_for_frames():
    """Mutacje: 157 `< 2` -> `<= 2` i `2` -> `3` — dwupunktowa oś byłaby odrzucona.

    Prosty odcinek jest legalną osią i najkrótszą, jaka daje rurę. Odmowa dla niego
    wywróciłaby każdy chunk zbudowany z dwóch pierścieni.
    """
    frames = SW.rmf_frames([(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)])
    assert len(frames) == 2
    try:
        SW.rmf_frames([(0.0, 0.0, 0.0)])
    except ValueError:
        pass
    else:
        raise AssertionError("oś z jednego punktu dostała ramki")


def test_sweep_a_vertical_axis_still_gets_a_frame():
    """Oś pionowa ma styczną równoległą do „góry" świata.

    Iloczyn wektorowy stycznej i pionu jest wtedy zerem, więc bez tej gałęzi
    `unit` dostaje wektor zerowy i całość leci wyjątkiem. Szyb windy albo pochylnia
    o dużym spadku to nie jest przypadek hipotetyczny.

    **Ten test nie zabija żadnej mutacji z przeglądu i tak ma być.** Obie mutacje
    wiersza 161 — `< 1e-9` na `<= 1e-9` oraz próg na `1,01e-9` — są nieobserwowalne:
    rozróżnia je wyłącznie norma wypadająca DOKŁADNIE na progu. Sprawdzone
    wykonaniem: mutant `<=` daje 730/730. Test zostaje jako regresja na samą gałąź,
    bo jej usunięcie wywraca oś pionową natychmiast — ale nie udaję, że coś zabija.
    """
    frames = SW.rmf_frames([(0.0, 0.0, 0.0), (0.0, 0.0, 10.0)])
    right = frames[0][2]
    assert abs(SW.norm(right) - 1.0) < 1e-12, right
    assert abs(SW.dot(right, (0.0, 0.0, 1.0))) < 1e-12, "prawo nie jest prostopadłe do osi"


def test_sweep_ring_indices_must_be_at_least_two_and_increasing():
    """Mutacja: 298 `< 2` -> `<= 2` — chunk z jednego pierścienia przechodziłby dalej."""
    frames = SW.rmf_frames(SW.dedupe(_s_curve()))
    station_m = SW.chainages([f[0] for f in frames])
    for bad in ([3], [3, 3], [5, 2]):
        try:
            SW.build_chunk_from_rings(frames, station_m, BOX, bad)
        except ValueError:
            continue
        raise AssertionError(f"zestaw pierścieni {bad} został przyjęty")
    assert SW.build_chunk_from_rings(frames, station_m, BOX, [0, 1])["vertices"]


def test_sweep_uv_stretch_ignores_rows_with_no_uv_span():
    """Zerowy krok UV nie może wejść do stosunku metrów na jednostkę tekstury.

    Dwa pierścienie o tym samym `v` dają `duv == 0`; policzenie dla nich stosunku
    byłoby dzieleniem przez zero, a wpisanie tam zera zaniżyłoby minimum i kontrola
    rozciągnięcia tekstury przestałaby cokolwiek znaczyć.

    **Mutacji wiersza 410 ten test nie zabija.** `> 1e-9` na `>= 1e-9` rozróżnia
    wyłącznie krok UV równy progowi co do bitu; sprawdzone wykonaniem — mutant daje
    730/730. Zabija natomiast usunięcie samego strażnika, bo wtedy leci dzielenie
    przez zero, i to jest to, co ten test pilnuje.
    """
    frames = SW.rmf_frames(SW.dedupe(_s_curve()))
    station_m = SW.chainages([f[0] for f in frames])
    chunk = SW.build_chunk(frames, station_m, BOX, 0, 20)
    columns = len(BOX) + 1
    low, high = SW.uv_stretch(chunk, columns)
    assert low > 0.0 and high > 0.0, (low, high)
    assert high / low < 1.05, (low, high)

    flat = {"vertices": list(chunk["vertices"]), "uvs": [(u, 0.0) for u, _v in chunk["uvs"]]}
    assert SW.uv_stretch(flat, columns) == (0.0, 0.0), "brak rozpiętości UV ma dać zera"


def test_sweep_strictly_increasing_removes_a_repeated_tail():
    """Mutacja: 487 `>=` -> `>` — powtórzony indeks na końcu zostawałby w wyniku.

    Zduplikowany pierścień na szwie znaczy czworokąt o zerowej wysokości, czyli
    ścianę bez pola — `degenerate_faces` zgłosiłoby to później, ale dopiero po
    zbudowaniu siatki.
    """
    assert SW._strictly_increasing([0, 3, 3], 3) == [0, 3]
    assert SW._strictly_increasing([0, 0, 0], 5) == [0, 1, 5]
    assert SW._strictly_increasing([0, 2, 4], 4) == [0, 2, 4]
